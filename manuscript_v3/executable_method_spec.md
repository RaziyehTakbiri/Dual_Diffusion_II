# Executable Route-A Method Specification

**Status:** `[INTERNALLY AUDITED MATHEMATICAL CANDIDATE / PARTIALLY IMPLEMENTED]`  
**Created:** 2026-08-03  
**Last updated:** 2026-08-20  
**Scope:** the first code-ready probability contract for Manuscript v3.  
**Non-claim:** this document does not establish novelty, a theorem, numerical
performance, real-domain task admission, or submission readiness.

This specification closes the prose-level ambiguities identified in the
Manuscript-v3 audit. It selects one capped reference process, one exact
population objective for its reversal, one normalized unordered-association
family, one guide restriction and cap-defect convention, and one conditional
initializer/simulator contract. Numerical schedules, domain semantics, and
decision thresholds remain in
`execution_preregistration.md`.

## 1. Decisions fixed by this candidate

The first implementation SHALL use all of the following:

1. a capped finite-counting configuration, never a learned slot-labelled
   state;
2. a normalized capped-Poisson configuration reference with a reversible
   birth/death/replacement/OU corruption;
3. one permutation-invariant scalar base energy whose gradient and edge
   differences define the continuous and jump reversal corrections;
4. a relative score-matching plus jump-flux population loss whose minimizer is
   the exact reversal energy up to its harmless time/context gauge;
5. a normalized at-most-one-anchor-per-event observation kernel with type
   confusion, dominated mark noise, misses, Poisson clutter, and an explicit
   overflow observation;
6. exact marginalization of occurrence-to-anchor association, including orbit
   factors for repeated identical atoms;
7. an unbounded independent analytic association guide restricted to capped
   states, called an **analytic preconditioner**, not an exact capped
   information function;
8. an explicit harmonic defect whose cap-boundary term is measured rather than
   hidden;
9. joint-versus-product density-ratio training from the candidate base process
   once implemented and admitted, with a separate observation-only nuisance;
10. exact conditional initialization when enumerable or certified rejection
    is possible, and fixed-budget self-normalized importance resampling
    otherwise; and
11. a numerical split-step conditional sampler with mandatory refinement
    diagnostics. No rate or likelihood may be silently clipped.

The clean structural-zero observation law and the positive dominated mixture
remain distinct. The positive branch is the bridge selected for the first
implementation. A
structural-zero bridge is a separate theorem and implementation gate.

## 2. Native state and normalized reference

### 2.1 Transformed typed event space

For each executable stratum \(d\in\mathcal D\), all atomless physical-time and
mark coordinates are mapped by a declared bijection to
\(r\in\mathbb R^{k_d}\). Atomic time coordinates are included in the discrete
stratum label. The transformed event space and state space are

\[
\mathcal E
=\coprod_{d\in\mathcal D}\bigl(\{d\}\times\mathbb R^{k_d}\bigr),
\qquad
\Gamma_{\le N}^{\mathrm{count}}(\mathcal E).
\]

Every physical support transform and inverse is part of the domain manifest.
The implementation may temporarily label occurrences to simulate a path, but
the model input, scalar energy, likelihood, rates, and saved state are
permutation invariant. Repeated identical atoms are legal in the counting
branch.

### 2.2 One-event and configuration references

Freeze positive type weights \(w_d\), \(\sum_d w_d=1\), and let
\(\varphi_d\) be standard Gaussian probability on
\(\mathbb R^{k_d}\). Define

\[
\nu(de)=\sum_{d\in\mathcal D}w_d\,\delta_d(dd)\varphi_d(dr).
\]

For activity \(\vartheta>0\), define the normalized capped-Poisson reference

\[
\Pi_N(dx)
=\frac1{Z_N(\vartheta)}
\sum_{n=0}^{N}\frac{\vartheta^n}{n!}
(\Sigma_n)_\#\nu^{\otimes n}(dx),
\qquad
Z_N(\vartheta)=\sum_{n=0}^{N}\frac{\vartheta^n}{n!},
\]

where \(\Sigma_n(e_{1:n})=\sum_i\delta_{e_i}\). The pushforward, rather than
an ordered tuple density, is authoritative. For an atomic count vector
\(m\), it contributes the orbit factor \(n!/\prod_j m_j!\); combined with the
exterior \(1/n!\), this leaves the required inverse multiplicity factorials.

## 3. Reversible capped forward corruption

### 3.1 Reference dynamics

Let \(s\in[0,S]\) be forward noising time. Freeze nonnegative schedules
\(\gamma_C(s)\) and \(\gamma_J(s)\), constants \(\beta,\delta>0\) satisfying
\(\beta/\delta=\vartheta\), and type-change rates
\(\kappa_{dd'}\ge0\) satisfying

\[
w_d\kappa_{dd'}=w_{d'}\kappa_{d'd},\qquad d\ne d'.
\]

The implemented parameterization makes these identities structural rather
than post-hoc checks. It accepts \(\delta\), derives
\(\beta=\vartheta\delta\), accepts sparse symmetric positive reference fluxes
\(c_{dd'}=c_{d'd}\), and sets

\[
\kappa_{dd'}=\frac{c_{dd'}}{w_d},
\qquad
\kappa_{d'd}=\frac{c_{dd'}}{w_{d'}}.
\]

The implementation and evidence boundary are recorded in the
reversible-forward-process code audit.

To avoid an untrained endpoint extrapolation, freeze a clean-hold time
\(s_{\mathrm{hold}}>0\) and require

\[
\gamma_C(s)=\gamma_J(s)=0\quad\text{for }0\le s\le s_{\mathrm{hold}},
\]

with both schedules strictly positive on the active interval
\((s_{\mathrm{hold}},S]\). Hence \(P_s=P_0\) throughout the clean hold. In reverse
time, the generator is identically zero on
\([S-s_{\mathrm{hold}},S]\), so that final segment is exactly the identity and
does not query an unconstrained energy.

The forward generator \(\mathcal L_s^0\) contains:

\[
\begin{aligned}
(\mathcal L_s^{C}f)(x)
={}&\gamma_C(s)\int x(de)
\left[-\tfrac12r_e^\top\nabla_e f(x)
+\tfrac12\Delta_e f(x)\right],\\
(\mathcal L_s^{+}f)(x)
={}&\gamma_J(s)\mathbf1_{\{|x|<N\}}\beta
\int\bigl[f(x+\delta_v)-f(x)\bigr]\nu(dv),\\
(\mathcal L_s^{-}f)(x)
={}&\gamma_J(s)\delta
\int x(de)\bigl[f(x-\delta_e)-f(x)\bigr],\\
(\mathcal L_s^{R}f)(x)
={}&\gamma_J(s)\int x(de)
\sum_{d'\ne d(e)}\kappa_{d(e)d'}
\int\bigl[f(x-\delta_e+\delta_{(d',r')})-f(x)\bigr]
\varphi_{d'}(dr').
\end{aligned}
\]

Thus
\(\mathcal L_s^0=\mathcal L_s^C+\mathcal L_s^++\mathcal L_s^-+
\mathcal L_s^R\). Births stop exactly at \(N\). Death and replacement are
integrated against \(x(de)\), so repeated occurrences receive the correct
multiplicity. Type replacement drops the source fiber and creates destination
coordinates from its declared reference; no padded ambient coordinate is
used.

Each component is reversible with respect to \(\Pi_N\). In particular, the
capped Mecke identity and \(\beta/\delta=\vartheta\) give birth/death detailed
balance, and the displayed \(w\)-balance gives the correct source/destination
fiber factors for replacement. This reference-factor construction is frozen;
a learned bridge multiplier cannot repair a different kernel.

### 3.2 Exact forward simulation

The forward simulator SHALL be event driven.

- Between jumps, an extant transformed coordinate follows the exact OU update

  \[
  r_{s_1}=e^{-G_C/2}r_{s_0}+\sqrt{1-e^{-G_C}}\,\epsilon,
  \qquad G_C=\int_{s_0}^{s_1}\gamma_C(v)dv,
  \quad\epsilon\sim\mathcal N(0,I).
  \]

- While the counting state is fixed, its unscaled total jump rate is

  \[
  \Lambda^0(x)=
  \beta\mathbf1_{\{|x|<N\}}+\delta|x|
  +\int x(de)\sum_{d'\ne d(e)}\kappa_{d(e)d'},
  \]

  where the counting-measure integral includes repeated occurrences. The
  time-\(s\) rate is
  \(\Lambda_s^0(x)=\gamma_J(s)\Lambda^0(x)\). Jump time is sampled in the
  integrated clock \(G_J(s)=\int_0^s\gamma_J(v)dv\).
- A birth draws \(v\sim\nu\); a death selects an occurrence with its declared
  per-occurrence rate; replacement selects a source occurrence and destination
  type by \(\kappa\), then draws the new destination coordinates from
  \(\varphi_{d'}\).

Occurrence identifiers used to maintain a path are deleted before model
evaluation. Permuting them with the same random variates must leave the
canonical path law unchanged.

The first implementation uses the declared zero hold followed by positive
piecewise-constant \(\gamma_C\) and \(\gamma_J\) schedules on a frozen grid.
At an interior knot, the public point value is left-continuous, while a
waiting-time search beginning exactly at that knot visits the segment on its
right. The isolated-point convention does not affect either integral.
Given current time \(s_0\), state
\(x\), and \(E\sim\operatorname{Exp}(1)\), the next jump solves

\[
\Lambda^0(x)\,[G_J(s_1)-G_J(s_0)]=E.
\]

The public `continuous_integral` and `jump_integral` values are stable binary64
views: segment products are evaluated in binary64, and multi-term intervals
are combined by one flat `math.fsum` over the selected full and partial terms.
The OU transition uses this stable rounded continuous clock in its closed-form
coefficients.

Waiting-time decisions deliberately do not use the rounded public jump-clock
total. Inversion interprets each supplied binary64 endpoint, schedule rate,
base exit rate, and sampled hazard as its exact binary rational. Segment
duration is the exact rational difference of its endpoints; segment hazards
and residual subtraction are compared exactly. Equality therefore places a
jump at a breakpoint or at the horizon, whereas strict excess over the exact
remaining segment sum means that no further jump occurs. A rounded relation
such as `base_rate * jump_integral(...) == E` is not an equality certificate.
An interior exact rational event time is converted to binary64 once. If a
strictly positive interior time cannot be represented strictly between the
cursor and the next breakpoint, the simulator refuses rather than collapsing
it to either boundary.

Thus “exact forward simulation” means event-driven simulation without time
discretization or a numerical root tolerance for the piecewise process
declared by the admitted binary64 inputs and finite random draws. It does not
claim arbitrary-precision OU arithmetic or an ideal real-valued random source.

The terminal law \(P_S\) approaches \(\Pi_N\) but need not equal it at finite
\(S\). The exact reversed forward process starts from \(P_S\). The candidate
reverse generator in Section 8 is instead specified to start from
\(\rho_0^\phi=\Pi_N\). It therefore has the exact reversal path law only when
\(P_S=\Pi_N\); otherwise the initial-law discrepancy is a separately measured
terminal-reference error.

## 4. Exact reversal target and unconditional base model

### 4.1 Relative density energy

Let \(P_s(dx\mid z)\) be the noised data law and assume, for trained times,

\[
f_s(x\mid z)=\frac{dP_s(\cdot\mid z)}{d\Pi_N}(x)>0.
\]

The exact relative energy is
\(V_s^*(x,z)=\log f_s(x\mid z)\), identified up to an additive function of
\((s,z)\). Let \(q_s^0(x,dy)\) denote the off-diagonal jump kernel in
\(\mathcal L_s^0\), and define the reverse-time reference notation

\[
\bar{\mathcal L}^{0,N}_u:=\mathcal L^0_{S-u},
\qquad
\bar q_u^0:=q_{S-u}^0,
\qquad s=S-u.
\]

Because \(\mathcal L_s^0\) is \(\Pi_N\)-reversible, the following are the
exact **local characteristics** of the reversed forward law:

\[
\bar b_u^*(e,x,z)
=-\tfrac12\gamma_C(s)r_e
+\gamma_C(s)\nabla_eV_s^*(x,z),
\]

and, for every valid off-diagonal reference edge,

\[
\bar q_u^*(x,dy\mid z)
=q_s^0(x,dy)\exp\{V_s^*(y,z)-V_s^*(x,z)\}.
\]

The exact reversed **path law** additionally starts from \(P_S\). The candidate
base is defined to use one permutation-invariant differentiable scalar
\(V_\phi(s,x,z)\) in these two formulas and starts from
\(\rho_0^\phi=\Pi_N\). This enforces cycle consistency and
the required common correction across birth, death, replacement, and
continuous motion. It is standard reversal machinery, not the candidate
novelty.

### 4.2 Population loss

Sample \(X_0\) from data, simulate the exact forward corruption to a time
\(s\sim\omega\), and write \(X_s=x\). The time law \(\omega\) must have a
strictly positive density on its frozen training interval.

For the Gaussian one-event reference, the continuous relative score-matching
loss is

\[
\mathcal L_C(\phi)
=\mathbb E\sum_{e\in X_s}\gamma_C(s)
\left[
\tfrac12\|\nabla_eV_\phi\|^2
+\Delta_eV_\phi-r_e^\top\nabla_eV_\phi
\right].
\]

The divergence term may use an unbiased Hutchinson estimator with a frozen
probe distribution and probe count. This identity requires bijective
Euclidean support transforms, sufficient tail decay, and no omitted quotient
boundary term. Collision strata of the atomless reference have measure zero;
atomic coordinates are represented discretely rather than differentiated. A
non-bijective or finite-boundary transform is not admitted by this objective.
Its population excess is

\[
\mathcal L_C(V)-\mathcal L_C(V^*)
=\frac12\mathbb E_{s,X_s}
\sum_{e\in X_s}\gamma_C(s)
\|\nabla_e(V-V^*)\|^2.
\]

For \(\Delta_\phi(s,x,y)=V_\phi(s,y,z)-V_\phi(s,x,z)\), the jump-flux loss,
up to a parameter-independent constant, is

\[
\boxed{
\mathcal L_J(\phi)
=\mathbb E_{s,X_s}
\int q_s^0(X_s,dy)
\left[e^{\Delta_\phi(s,X_s,y)}
+\Delta_\phi(s,X_s,y)\right].
}
\]

This is the Poisson cross-entropy for the reverse jump measure after using
reference detailed balance. The positive sign of the linear term comes from
transposing the realized reverse-jump flux through the symmetric
\(\Pi_N(dx)q_s^0(x,dy)\) edge measure. If \(E=V-V^*\), its excess is

\[
\mathcal L_J(V)-\mathcal L_J(V^*)
=\mathbb E_{s,X_s}
\int \bar q_{S-s}^*(X_s,dy)
\left[e^{E(s,y,z)-E(s,X_s,z)}-1
-E(s,y,z)+E(s,X_s,z)\right]\ge0.
\]

Therefore its population minimizer is \(V_s^*=\log f_s\) up to the shared
gauge when the reference edge graph is connected and the model class contains
\(V^*\). A trajectory loss using realized reversed jumps instead has the form
\(\int q^0e^{\Delta V}du-\sum_j\Delta V_j\); that form and the displayed
marginal-flux form must not be mixed term by term.

For continuous birth or replacement destinations, let
\(\Lambda_s^0(x)=q_s^0(x,\Gamma_{\le N}\setminus\{x\})\) and, when this is
positive, let
\(Q_s^0(dy\mid x)=q_s^0(x,dy)/\Lambda_s^0(x)\). With
\(Y\sim Q_s^0(\cdot\mid x)\),

\[
\Lambda_s^0(x)
\left[e^{\Delta_\phi(s,x,Y)}+\Delta_\phi(s,x,Y)\right]
\]

is an unbiased one-proposal estimator. The proposal count, family
stratification, and any alternative proposal density are frozen. If an
alternative proposal \(R\) is used, the exact factor \(dq_s^0/dR\) is
mandatory; self-normalized weights are forbidden in this population loss.

The unconditional objective is

\[
\mathcal L_{\mathrm{base}}=\mathcal L_C+\lambda_J\mathcal L_J,
\qquad \lambda_J>0.
\]

A positive \(\lambda_J\) changes conditioning of the optimization but not the
common population minimizer. The declared expectation over \(s\sim\omega\)
needs no \(1/\omega(s)\) factor; such a factor is required only if estimating
an integral against a different target time measure. All exponentials are
evaluated in log-safe arithmetic. A bound/certificate on edge differences is required before a
checkpoint can be exposed to a simulator; clipping an edge difference changes
the fitted generator and is not allowed.

The finite/Gaussian theorem-to-code layer for these identities is implemented
in `heterodiff.theory.reverse_energy_objective` and governed by the
third incremental code audit. Its
finite generator inputs must already carry the direct forward-time schedule;
its alternative-proposal interface retains every named unnormalized factor.
Cancellation-sensitive Gaussian and jump expressions use checked binary64,
exact binary-rational, or high-precision fallback paths without clipping. This
is a NumPy objective/reversal oracle, not the bounded neural scalar,
Hutchinson/autodiff training path, checkpoint certificate, production proposal
composer, or reverse trajectory model.

### 4.3 First executable scalar class and rate certificate

The first implementation does not leave regularity to an unconstrained neural
network. It uses

\[
V_\phi(s,x,z)=B_V\tanh\!\left(F_\phi(s,x,z)/B_V\right),
\qquad B_V>0,
\]

where \(F_\phi\) is a permutation-invariant \(C^2\) DeepSets scalar. Each
type-valid coordinate is processed by a type-specific smooth bounded event
encoder, occurrences are sum-pooled with multiplicity, and a smooth bounded
context/time encoder and readout produce the scalar. All hidden activations are
\(\tanh\); input and context transforms, layer spectral-norm ceilings, width,
and depth are frozen. This preserves exact ties and repeated atoms because no
slot index enters the network. Attention models are later capacity controls,
not the first correctness implementation.

Consequently,

\[
|V_\phi|\le B_V,
\qquad
|V_\phi(s,y,z)-V_\phi(s,x,z)|\le2B_V,
\]

and the learned base jump intensity is dominated by
\(e^{2B_V}q_s^0\). The frozen spectral bounds also supply finite constants for
the first two coordinate derivatives. Together with the linear OU drift this
gives a real-arithmetic nonexplosion argument for the candidate base on the
capped state space; it is not binary64 interval verification or sampler
admission. These are architectural restrictions, not runtime clipping. The model
therefore estimates the bounded-class risk projection if \(V^*\) lies outside
the class.

The correctness implementation is
`heterodiff.models.configuration_energy_torch`. It fixes a CPU-binary64,
typed-ragged DeepSets graph; stable \(\operatorname{atan2}\) input transforms
with a custom backward and scale interval \([2^{-256},2^{256}]\);
deterministic multiplicity-preserving pooling; exact/Hutchinson Laplacians;
the continuous and jump objectives; and an owned snapshot certificate. For
one represented checkpoint, outward arithmetic propagates all frozen layer
norms through the complete flattened physical-coordinate Jacobian and
Hessian, including cross-occurrence readout curvature and the outer bounded
\(\tanh\). The record binds the reference-process key, architecture, scales,
state bytes, runtime version, and procedural method/training/data/selection
digests. It also derives value, edge-increment, multiplier, reference-exit,
physical-coordinate derivative, and Laplacian bounds, plus a binary64
operational threshold for each supplied rate. That threshold is not an
interval enclosure of the exact real expression or a production aggregate of
separately rounded learned edges; the real-arithmetic learned-rate consequence
is retained only as the symbolic inequality \(q^\phi\le q^0e^{2B_V}\).

This certificate assumes a trusted, unmodified Python/PyTorch runtime. It is
not runtime-tamper attestation, checkpoint authentication, a safe persistence
format, evidence that a trained checkpoint equals \(V^*\), or sampler
admission. In particular, this layer does not establish that a caller-supplied
positive reference rate corresponds to a valid edit; the production
process-edge composer must supply and bind that fact before simulation.

Training times have a density that is strictly positive on the full active
interval \((s_{\mathrm{hold}},S]\). The endpoint \(s=s_{\mathrm{hold}}\) has zero
sampling mass, and the generator is zero below it. The method-freeze review
must verify strict positivity of \(f_s\), the integration-by-parts tails, and
finite loss moments at every active \(s\). The value of \(B_V\) and every derivative ceiling
remain numerical preregistration fields; until they are frozen, no checkpoint
is sampler-admissible.

## 5. Normalized unordered-association observation

### 5.1 Observation reference and overflow

For task \(m\), choose an observed-event probability reference
\(\eta_m\) on a typed observation space \(\mathcal O_m\). Let
\(\Lambda_m^\infty=\operatorname{PPP}(\eta_m)\) be the unit-rate Poisson
configuration probability. Collapse every configuration with cardinality
above \(M_m\) to one outcome \(\dagger\):

\[
C_{M_m}(a)=
\begin{cases}
a,&|a|\le M_m,\\
\dagger,&|a|>M_m,
\end{cases}
\qquad
\lambda_m=(C_{M_m})_\#\Lambda_m^\infty.
\]

Thus \(\lambda_m\) is normalized and has positive overflow mass

\[
\lambda_m(\dagger)
=1-e^{-1}\sum_{k=0}^{M_m}\frac1{k!}.
\]

If \(a=\sum_r\ell_r\delta_{o_r}\) lies in a finite atomic stratum, then

\[
\lambda_m(\{a\})
=e^{-1}\prod_r\frac{\eta_m(\{o_r\})^{\ell_r}}{\ell_r!}.
\]

This fixes the symmetrization and duplicate-atom convention.

### 5.2 Detection, noise, and clutter

Temporarily expand

\[
y=\sum_{i=1}^{J}m_i\delta_{e_i}
\]

into an occurrence set \(I_y\). An occurrence \(e\):

- is detected independently with probability \(p_D(e,z,m)\in[0,1]\);
- if detected, emits exactly one observed event with density
  \(q_m(o\mid e,z)\) relative to \(\eta_m\), with
  \(\int q_m(o\mid e,z)\eta_m(do)=1\); and
- otherwise emits no observation.

The first implementation freezes these as eventwise factors conditional on
\((z,m)\); configuration-dependent detection or noise would invalidate the
independent analytic propagation in Section 6 and is outside this freeze.
If \(o=(t,x)\) and
\(\eta_m(do)=\sum_t\omega_t\delta_t(dt)\eta_t(dx)\), the
executable type-confusion/noise factor is

\[
q_m((t,x)\mid e,z)
=\frac{\Pi_m(t\mid e,z)}{\omega_t}
\ell_{m,t}(x\mid e,z),
\]

where \(\Pi_m\) is row stochastic and \(\ell_{m,t}\) is a normalized density
relative to \(\eta_t\). The division by \(\omega_t\) is mandatory.

For the analytic-guide branch, this family is narrowed further. Detection is
type/context dependent, \(p_D(e,z,m)=p_D(d(e),z,m)\), and type confusion is
independent of the continuous latent coordinate,
\(\Pi_m(t\mid e,z)=\Pi_m(t\mid d(e),z)\). Atomless observed
coordinates use a declared affine Gaussian channel in standardized charts,

\[
x=A_{m,t,d}r+b_{m,t,d}(z)+\varepsilon,
\qquad \varepsilon\sim\mathcal N(0,\Sigma_{m,t,d}),
\qquad \Sigma_{m,t,d}\succ0,
\]

and \(\ell_{m,t}\) is its Radon--Nikodym density relative to the declared
Gaussian \(\eta_t\). Atomic fibers use finite stochastic matrices. This makes
the one-occurrence propagation in Section 6 a finite mixture of Gaussian and
categorical calculations. A nonconjugate observation channel may use the
normalized likelihood in Section 5, but then its guide is an approximation
with separate value, gradient, and edge-ratio gates; it is not called
analytic.

Independent clutter is a Poisson process with intensity
\(\kappa_m(o\mid z)\eta_m(do)\) and finite total

\[
K_m(z)=\int\kappa_m(o\mid z)\eta_m(do)<\infty.
\]

### 5.3 Labelled and quotient likelihoods

For a retained observation \(a=\sum_{j=1}^{k}\delta_{o_j}\), let
\(\mathfrak M(a,y)\) contain every partial injection from a subset of the
temporary observation occurrences to \(I_y\). Matched observations are
signals, unmatched observations are clutter, and unmatched latent occurrences
are misses. The clean density relative to \(\lambda_m\) is

\[
\boxed{
\begin{aligned}
g_m^{\mathrm{clean}}(a\mid y,z)
={}&e^{1-K_m(z)}
\sum_{\mu\in\mathfrak M(a,y)}
\prod_{j\in\operatorname{dom}\mu}
\left[p_D(e_{\mu(j)},z,m)q_m(o_j\mid e_{\mu(j)},z)\right]\\
&\times
\prod_{i\in I_y\setminus\operatorname{im}\mu}
[1-p_D(e_i,z,m)]
\prod_{j\notin\operatorname{dom}\mu}\kappa_m(o_j\mid z).
\end{aligned}
}
\]

Only \((z,m)\) are suppressed inside repeated factors below. No additional
\(k!\) appears under the unit-Poisson configuration reference.

For an implementation that stores only distinct atoms, write

\[
a=\sum_{r=1}^{R}\ell_r\delta_{o_r},
\qquad y=\sum_{i=1}^{J}m_i\delta_{e_i}.
\]

An association class is an integer matrix \(H=(h_{ri})\). Set

\[
d_i=\sum_rh_{ri}\le m_i,
\qquad c_r=\ell_r-\sum_ih_{ri}\ge0.
\]

Its exact orbit coefficient is

\[
\boxed{
\Omega(H)=
\frac{\displaystyle
\prod_r\ell_r!\prod_im_i!}
{\displaystyle
\prod_rc_r!\prod_i(m_i-d_i)!\prod_{r,i}h_{ri}!}.
}
\]

Therefore the quotient implementation is

\[
\boxed{
\begin{aligned}
g_m^{\mathrm{clean}}(a\mid y,z)
={}&e^{1-K_m(z)}\sum_H\Omega(H)
\prod_i p_i^{d_i}(1-p_i)^{m_i-d_i}\\
&\times\prod_{r,i}q_m(o_r\mid e_i,z)^{h_{ri}}
\prod_r\kappa_m(o_r\mid z)^{c_r}.
\end{aligned}
}
\]

where \(p_i=p_D(e_i,z,m)\).

The labelled-injection and quotient formulas are exactly equivalent. A code
path may use either, but deduplicating occurrence copies without \(\Omega(H)\)
is invalid.

### 5.4 Overflow and positivity

Let \(D_y\) be the sum of the independent occurrence-detection Bernoulli
variables and let \(C\sim\operatorname{Poisson}(K_m(z))\). The clean overflow
density is

\[
g_m^{\mathrm{clean}}(\dagger\mid y,z)
=\frac{\Pr(D_y+C>M_m\mid y,z)}{\lambda_m(\dagger)}.
\]

No retained row is renormalized. Structural zeros remain exact. For a
scientifically justified full-support outlier branch \(R_{0,m}\), define

\[
K_{m,\epsilon}=(1-\epsilon_m)K_m^{\mathrm{clean}}
+\epsilon_mR_{0,m}.
\]

The first controlled implementation uses \(R_{0,m}=\lambda_m\), giving

\[
g_{m,\epsilon}=(1-\epsilon_m)g_m^{\mathrm{clean}}+\epsilon_m
\ge\epsilon_m.
\]

This mixture is authorized for a known-law fixture. It is not authorized for a
real domain until the outlier mechanism and \(\epsilon_m\) are justified
without reference to method performance.

### 5.5 Exact dynamic program and refusal boundary

For \(n=|y|\), enumerate temporary latent occurrences by \(i=1,\ldots,n\)
and retained observation occurrences by \(j=1,\ldots,k\). One exact
log-semiring dynamic program processes observations and stores a table over
matched-source subsets. In ordinary arithmetic,

\[
D_0(\varnothing)=1,
\]

\[
D_j(S)
=\kappa_m(o_j\mid z)D_{j-1}(S)
+\sum_{i\in S}p_iq_m(o_j\mid e_i,z)
D_{j-1}(S\setminus\{i\}).
\]

The retained clean density is

\[
g_m^{\mathrm{clean}}(a\mid y,z)
=e^{1-K_m(z)}
\sum_{S\subseteq I_y}D_k(S)
\prod_{i\notin S}(1-p_i).
\]

The transposed recurrence processes latent occurrences and stores used
observation subsets. The implementation chooses the smaller subset axis, for
time \(O(nk2^{\min(n,k)})\) and memory
\(O(2^{\min(n,k)})\), and uses log-sum-exp with exact \(-\infty\) structural
zeros. Automatic differentiation through this recurrence supplies the value,
continuous gradient, and edit-edge evaluations. Temporary occurrence order is
canonicalized, and the quotient formula in Section 5.3 is retained as an
independent duplicate/orbit oracle.

The overflow probability uses the coefficient recursion for
\(\prod_i[(1-p_i)+p_it]\), followed by a Poisson-tail convolution. Both
algorithms are exact up to floating-point arithmetic. A frozen memory/time
switch controls admission. The first implementation **refuses** an input above
that switch; it does not silently substitute a heuristic. Any scalable
approximation is a later, separately named algorithm whose log-value,
gradient, every edge-ratio, positivity, and tail errors must pass independent
gates before a representative-cardinality claim is allowed.

## 6. Analytic preconditioner and explicit cap defect

### 6.1 Unbounded auxiliary computation

Let \(\bar{\mathcal L}^{0,\infty}_u\) be the unbounded independent
immigration/death/type-replacement/linear-Gaussian **reverse-time reference**
process obtained from \(\bar{\mathcal L}^{0,N}_u\) by removing the cap. Thus
its schedules are evaluated at forward time \(S-u\); in particular its
immigration rate is
\(\widetilde\beta_u=\gamma_J(S-u)\beta\). It is an auxiliary computational
model, not the candidate base law.

For one current occurrence \(e\), let
\(S_{u,S}(e,de')\) be its sub-Markov transition under this auxiliary process
to a surviving terminal event.
This kernel is explicit for the selected reference. Define

\[
A_J(u,t)=\int_u^t\gamma_J(S-v)\,dv,
\qquad
A_C(u,t)=\int_u^t\gamma_C(S-v)\,dv,
\qquad
\alpha_{u,t}=e^{-A_C(u,t)/2},
\]

and let \(Q\) be the type generator with off-diagonal entries
\(Q_{dd'}=\kappa_{dd'}\) and
\(Q_{dd}=-\sum_{d'\ne d}\kappa_{dd'}\). With
\(\kappa_d^{\mathrm{out}}=\sum_{d'\ne d}\kappa_{dd'}\), for
\(e=(d,r)\),

\[
\begin{aligned}
S_{u,S}((d,r),\{d'\}\times dr')
={}&e^{-\delta A_J(u,S)}
\Bigl[
\mathbf1_{\{d'=d\}}e^{-\kappa_d^{\mathrm{out}}A_J(u,S)}
\mathcal N\!\left(
dr';\alpha_{u,S}r,(1-\alpha_{u,S}^2)I
\right)\\
&+\left(
[e^{A_J(u,S)Q}]_{dd'}
-\mathbf1_{\{d'=d\}}e^{-\kappa_d^{\mathrm{out}}A_J(u,S)}
\right)\varphi_{d'}(dr')
\Bigr].
\end{aligned}
\]

The first term is survival with no type replacement; after the first
replacement the coordinate is refreshed from the destination reference and
remains reference-distributed. The displayed coefficients are nonnegative and
sum to the survival probability.
Define its effective detected-anchor density and miss probability by

\[
\widetilde p_{u,m}(o\mid e)
=\int S_{u,S}(e,de')p_D(e',z,m)q_m(o\mid e',z),
\]

\[
\widetilde u_{u,m}(e)
=1-\int\widetilde p_{u,m}(o\mid e)\eta_m(do).
\]

Because \(\nu\) is invariant for the uncapped reference, future immigrants
that survive to \(S\) form a Poisson process with mean

\[
\Lambda_{\mathrm{imm}}(u)
=\int_u^S\gamma_J(S-t)\beta
e^{-\delta A_J(t,S)}\,dt.
\]

They contribute the Poisson anchor intensity

\[
\kappa_{\mathrm{imm},u,m}(o)
=\Lambda_{\mathrm{imm}}(u)
\int\nu(de')p_D(e',z,m)q_m(o\mid e',z).
\]

Its anchor-count mean and the total clutter-plus-immigrant quantities are

\[
K_{\mathrm{imm}}^A(u)
=\int\kappa_{\mathrm{imm},u,m}(o)\eta_m(do)
=\Lambda_{\mathrm{imm}}(u)\int\nu(de')p_D(e',z,m),
\]

\[
\kappa_{\mathrm{tot},u,m}=\kappa_m+\kappa_{\mathrm{imm},u,m},
\qquad
K_{\mathrm{tot},u,m}=K_m+K_{\mathrm{imm}}^A(u).
\]

Replacing \(p_Dq\), miss, and clutter in Section 5 by
\(\widetilde p\), \(\widetilde u\), and
\(\kappa_{\mathrm{tot},u,m}\) gives a closed clean-association computation
for \(\widetilde h_{u,m}^{\infty,\mathrm{clean}}\). Its retained likelihood
uses the exponential \(e^{1-K_{\mathrm{tot},u,m}}\), not
\(e^{1-K_m}\). Finite categorical transitions use matrix
exponentials; linear-Gaussian coordinates use exact Gaussian propagation.
Any low-rank or truncated association approximation is a separate object with
separate value, gradient, and edge-ratio errors.

For overflow, let independent

\[
B_i\sim\operatorname{Bernoulli}\!\left(
\int\widetilde p_{u,m}(o\mid e_i)\eta_m(do)
\right),
\qquad
P\sim\operatorname{Poisson}(K_{\mathrm{tot},u,m}).
\]

The propagated clean overflow **density**, including the collapsed-reference
divisor, is

\[
\widetilde h_{u,m}^{\infty,\mathrm{clean}}(y;\dagger,z)
=\frac{\Pr(\sum_{i\in I_y}B_i+P>M_m)}{\lambda_m(\dagger)}.
\]

The numerator is evaluated by the Poisson-binomial recursion followed by a
Poisson-tail convolution. For the admitted \(R_{0,m}=\lambda_m\) mixture, set

\[
\widetilde h_{u,m}^{\infty,\epsilon}
=(1-\epsilon_m)\widetilde h_{u,m}^{\infty,\mathrm{clean}}
+\epsilon_m.
\]

All harmonic-defect, residual-learning, initialization, and sampling formulas
below use the admitted positive \(\epsilon_m\)-mixture exclusively. The clean
structural-zero guide is retained only for observation-law and diagnostic
calculations. Accordingly, \(\widetilde h_u^\infty\) below denotes the positive
branch. At \(u=S\), future immigration vanishes and

\[
\widetilde h_S^\infty(y;a,z)=g_m(a\mid y,z)
\]

for retained observations and the collapsed overflow atom.

### 6.2 Restriction, not an exact capped bridge

The preconditioner on the target state is the literal restriction

\[
\widetilde h_u(y;a,z)
=\widetilde h_u^\infty(y;a,z),
\qquad |y|\le N.
\]

No renormalization or conditioning on remaining below \(N\) is applied. This
restriction is a positive terminal-matched function, but it is not called an
exact information function for the capped base.

Let \(\bar{\mathcal L}_u^\phi\) be the candidate base generator and define
the measurable harmonic defect

\[
\boxed{
\mathfrak d_u^\phi(y;a,z)
=\frac{(\partial_u+\bar{\mathcal L}_u^\phi)
\widetilde h_u(y;a,z)}{\widetilde h_u(y;a,z)}.
}
\]

Using the reverse-time capped reference \(\bar{\mathcal L}^{0,N}_u\) defined
in Section 4.1,

\[
\mathfrak d_u^\phi
=\frac{(\bar{\mathcal L}_u^\phi-\bar{\mathcal L}^{0,N}_u)
\widetilde h_u}{\widetilde h_u}
+\frac{(\bar{\mathcal L}^{0,N}_u-
\bar{\mathcal L}^{0,\infty}_u)
\widetilde h_u^\infty}{\widetilde h_u}.
\]

The second term is zero away from the cap when the auxiliary and reference
local characteristics agree. Define the birth operator omitted at the cap by

\[
B_u^\partial f(y)
=\mathbf1_{\{|y|=N\}}\gamma_J(S-u)\beta
\int[f(y+\delta_v)-f(y)]\nu(dv).
\]

Then

\[
(\partial_u+\bar{\mathcal L}^{0,N}_u)\widetilde h_u
=-B_u^\partial\widetilde h_u^\infty,
\]

and its blocked-birth contribution is

\[
\boxed{
\mathfrak d_u^{\mathrm{cap}}(y;a,z)
=-\mathbf1_{\{|y|=N\}}\gamma_J(S-u)\beta
\int\left[
\frac{\widetilde h_u^\infty(y+\delta_v;a,z)}
{\widetilde h_u(y;a,z)}-1
\right]\nu(dv).
}
\]

This is the required cap-boundary flux correction. It is reported separately
from base-energy mismatch. The method does not claim the uncapped guide and
capped target share a generator.

As a sign oracle, if \(\bar h^N\) is the exact capped-reference information
function and \(\bar P^N\) its propagator, then

\[
\bar h_u^N-\widetilde h_u
=-\int_u^S\bar P_{u,t}^N
B_t^\partial\widetilde h_t^\infty\,dt.
\]

For \(h_u^\phi=\widetilde h_u e^{r_u^*}\), the exact residual satisfies

\[
\partial_ur_u^*
+\frac{\bar{\mathcal L}_u^\phi(\widetilde h_ue^{r_u^*})}
{\widetilde h_ue^{r_u^*}}
-\frac{\bar{\mathcal L}_u^\phi\widetilde h_u}{\widetilde h_u}
+\mathfrak d_u^\phi=0,
\qquad r_S^*=0.
\]

This displayed equation is a target identity. A perturbation or finite-sample
bound based on it remains `[THEOREM-TARGET]`.

### 6.3 Executable defect diagnostic

In finite fixtures, every term in \(\mathfrak d\) is evaluated by enumeration.
In mixed configurations, automatic differentiation through the analytic
recurrence supplies \(\partial_u\widetilde h\), its coordinate gradients, and
its coordinate Laplacians; a frozen Hutchinson rule may replace the exact
Laplacian. Birth and replacement integrals under
\(\bar{\mathcal L}_u^\phi\), and the displayed cap integral under \(\nu\), use
independent unnormalized proposal averages with the exact base-kernel
Radon--Nikodym factors. The proposal family, count, random stream, and
standard-error calculation are frozen.

Reports separate (i) analytic-guide value/derivative error, (ii) cap-boundary
defect, (iii) learned-base/reference mismatch, and (iv) Monte Carlo numerical
error. No theorem may use this diagnostic until the preregistration supplies a
nonvacuous high-probability error rule; a self-normalized proposal average is
not admissible here.

## 7. Learned conditional potential

### 7.1 Joint/product population

Once implemented and admitted, use the candidate base process, not data-forward
pairs. First draw task and context \((m,z)\) from the frozen training law and
draw
\(u\sim q(du\mid m,z)\), where \(q\) has a strictly positive density on the
entire open interval \((0,S)\). Then:

1. draw \(Y_0^{(1)}\sim\Pi_N\) and simulate
   \(\bar{\mathcal L}_u^\phi\) to \((Y_u^{(1)},Y_S^{(1)})\);
2. draw \(A^{(1)}\sim K_m(\cdot\mid Y_S^{(1)},z)\) to form a joint pair; and
3. independently draw and simulate \(Y_0^{(2)}\sim\Pi_N\), then draw
   \(A^{(2)}\sim K_m(\cdot\mid Y_S^{(2)},z)\), to form the product pair
   \((Y_u^{(1)},A^{(2)})\).

The two trajectories share only \((m,z,u)\). This construction remains valid
for unique or continuous contexts because it repeats stochastic simulations
at the same context. Batch permutation is allowed only inside genuinely
identical context groups and otherwise is invalid. The task, context, time,
and class laws are stored; any alternative sampling law carries its exact
unnormalized Radon--Nikodym factor.

The equal-prior risk is the one in Manuscript v3. Over unrestricted measurable
logits on the common support, its Bayes optimum is

\[
\ell^*(u,y,a,m,z)=\log h_{u,m}^\phi(y;a,z)
-\log p_{A,m}^{\phi,\lambda}(a\mid z).
\]

The candidate logit is

\[
u_{\mathrm b}=S-s_{\mathrm{hold}},
\qquad
a_R(u)=\left(\max\left\{1-\frac{u}{u_{\mathrm b}},0\right\}\right)^3.
\]

The multiplier \(a_R\) is \(C^2\), equals one at \(u=0\), and is identically
zero throughout the reverse clean hold, where the exact residual is zero. Then

\[
\ell_{\theta,\psi}
=\log\widetilde h_{u,m}
+a_R(u)\mathcal C_{B_R}(F_\theta(u,y,a,m,z))
+c_\psi(a,m,z),
\]

where
\(\mathcal C_{B_R}(t)=B_R\tanh(t/B_R)\) is part of the model class, not a
runtime clip. The checkpoint-thirteen residual primitive uses a
permutation-invariant \(C^2\) DeepSets \(F_\theta\) with frozen spectral-norm,
first-derivative, and second-derivative ceilings, matching the smooth
event/context conventions of Section 4.3. The joint/product classifier loss
and nuisance branch are not yet implemented. Concretely, checkpoint thirteen
parameterizes the already bounded residual factor as

\[
\mathcal C_{B_R}(F_\theta(u,y,a,m,z))
=G_\theta(S-u,y,E(a,m,z)),
\]

where
\(G_\theta(s,y,c)=B_R\tanh(F_\theta^{\mathrm{core}}(s,y,c)/B_R)\) is the
backbone output. The network consumes the process-owned direct time \(s=S-u\)
and a fixed finite-dimensional conditioner \(E(a,m,z)\); the residual wrapper
does not apply a second saturation. Its operational gate is evaluated
equivalently as

\[
a_R(S-s)=
\left(\frac{\max\{s-s_{\mathrm{hold}},0\}}
{S-s_{\mathrm{hold}}}\right)^3.
\]

The residual contract binds the observation schema, task schema,
conditioner-adapter digest, residual role, process, and architecture; the
residual certificate additionally binds the core checkpoint and certificate.
The adapter digest is a procedural identity: the current tensor
API cannot authenticate at runtime that a supplied context vector was
actually produced by that adapter. A native permutation-invariant
variable-cardinality observation encoder therefore remains a separate
conditioning checkpoint.

The checkpoint-thirteen certificate covers the value, same-condition
state-pair difference, and the full flattened physical-latent-coordinate
gradient, Hessian operator norm, and Laplacian within each fixed continuous
configuration stratum. It does not certify time, observation, task, or
context derivatives, smoothness across discrete edits, a small binary64
forward error, density-ratio recovery, training success, or sampler
admission. The mathematical gate is \(C^2\); its derivative witnesses use the
exact rational difference of the represented endpoint times. The operational
binary64 gate is separately range-checked and clean-hold rows return canonical
positive zero without a neural forward call.

The nuisance \(c_\psi\) cannot receive \(u\) or \(y\). The bounded class learns
a risk projection unless it contains the Bayes logit. The plug-in physical
potential is

\[
\widehat h_{u,m}^{\phi,\theta}
=\widetilde h_{u,m}
\exp\{a_R(u)\mathcal C_{B_R}(F_\theta)\}.
\]

The nuisance is excluded. If training samples use the declared joint/product
and time/context laws, no importance correction is present. Any different
sampler must store the exact Radon--Nikodym weight; self-normalized training
weights are not allowed.

### 7.2 One combined conditional generator

Let \(s=S-u\) and define

\[
\Psi_{u,m}^{\phi,\theta}(y;a,z)
=V_\phi(s,y,z)+\log\widehat h_{u,m}^{\phi,\theta}(y;a,z).
\]

The executable plug-in generator is

\[
\bar b_{u,m}^{\phi,\theta,a}(e,y,z)
=-\tfrac12\gamma_C(s)r_e
+\gamma_C(s)\nabla_e\Psi_{u,m}^{\phi,\theta}(y;a,z),
\]

\[
\bar q_{u,m}^{\phi,\theta,a}(y,dy'\mid z)
=q_s^0(y,dy')
\exp\{\Psi_{u,m}^{\phi,\theta}(y';a,z)
-\Psi_{u,m}^{\phi,\theta}(y;a,z)\}.
\]

Thus the same total scalar modifies continuous motion and every valid edit
edge. Invalid reference edges remain zero. If \(\widehat h=h^\phi\), the
plug-in process equals the exact conditional bridge of the candidate base,
regardless of whether \(V_\phi=V^*\). Equality to the conditional reversal of
the forward data law additionally requires \(V_\phi=V^*\) and the correct
initial law \(P_S\), or the special case \(P_S=\Pi_N\).

Checkpoint fourteen implements the successful, jump-edge-only composition for
one already sampled `ProcessValidReferenceJump`. For its source \(y\),
destination \(y'\), reverse time \(u\), direct time \(s=S-u\), separately
declared base context \(z_B\), and residual conditioner \(c_R\), it recomputes

\[
b^{\mathrm{op}}=V_\phi(s,y',z_B)-V_\phi(s,y,z_B),
\qquad
g^{\mathrm{op}}=
\operatorname{RN}\!\left(\ell_m^{\mathrm{op}}(u,y')
-\ell_m^{\mathrm{op}}(u,y)\right),
\]

\[
r^{\mathrm{op}}=R_\theta(S-s,y',c_R)-R_\theta(S-s,y,c_R),
\]

from the live certified base, fixed-observation range-gated guide, and distinct
certified residual. The represented combined increment is frozen as

\[
\Delta\Psi^{\mathrm{op}}
=\operatorname{RN}_{1}\!\left(
b^{\mathrm{op}}+g^{\mathrm{op}}+r^{\mathrm{op}}
\right),
\]

where \(\operatorname{RN}_{1}\) means: interpret the three returned binary64
values as exact rationals, add them exactly, and round the sum to binary64
once. Exact cancellation returns canonical positive zero. This is deliberately
not sequential binary64 addition.

Let \(D_V^{\mathrm{math}},D_V^{\mathrm{op}}\) be the base certificate's
mathematical and one-step-slack operational edge witnesses; let
\(D_h^{\mathrm{math}}\ge\log(H_m/\epsilon_m)\) be the analytic
certificate's directed oscillation witness and let
\(D_h^{\mathrm{op}}=W_m\); finally, let
\(D_R^{\mathrm{math}}\) and \(D_R^{\mathrm{op}}\) be the residual's global
same-condition edge witnesses. With the residual helper's separate outward
gate witnesses \(a_{R,+}^{\mathrm{math}}(s)\) and
\(a_{R,+}^{\mathrm{op}}(s)\), checkpoint fourteen constructs

\[
D_{\Psi}^{\mathrm{math}}(s)
=\operatorname{rd}_{\uparrow}\!\left(
D_V^{\mathrm{math}}+D_h^{\mathrm{math}}
+a_{R,+}^{\mathrm{math}}(s)D_R^{\mathrm{math}}
\right),
\]

\[
D_{\Psi}^{\mathrm{op}}(s)
=\operatorname{rd}_{\uparrow}\!\left(
D_V^{\mathrm{op}}+D_h^{\mathrm{op}}
+\max\{a_{R,+}^{\mathrm{math}}(s),a_{R,+}^{\mathrm{op}}(s)\}
D_R^{\mathrm{op}}
\right),
\qquad
D_{\Psi}^{\mathrm{used}}(s)=
\max\{D_{\Psi}^{\mathrm{math}}(s),D_{\Psi}^{\mathrm{op}}(s)\}.
\]

Every nonnegative sum and product in these witnesses is evaluated from exact
rationals and rounded outward. The successful record checks each represented
component against its own operational bound and checks
\(|\Delta\Psi^{\mathrm{op}}|\le D_\Psi^{\mathrm{op}}(s)\). It binds the
candidate, edit kind, both endpoints, reflected times, fixed guide outcome,
distinct context schemas, checkpoints, residual role, provenance, and live
model state. Base and residual neural states must occupy disjoint physical
storage, including view and offset overlaps.

This checkpoint is partial in the literal sense: the guide may refuse a
finite point outside its represented range gate, and the composer propagates
that refusal without projection or fallback. The record is therefore a
successful log-space edge witness, not an absolute-potential evaluator, a
rate-space envelope, a controlled total exit, a waiting-time or acceptance
decision, a drift certificate, an initializer, a path, or sampler admission.
The base context is schema- and dimension-bound; the residual context is
additionally adapter-digest-bound. The runtime origin of neither supplied
vector is authenticated, so both origins remain procedural.

### 7.3 Physical-potential envelope

For every sampler-admitted fixed \((a,m,z)\), the analytic routine must certify

\[
\epsilon_m\le \widetilde h_{u,m}(y;a,z)\le H_m(a,z)<\infty
\quad\text{for all }u\in[0,S],\ |y|\le N.
\]

The lower bound is supplied by the admitted positive mixture; the upper bound
is computed from the cap and statewise-bounded likelihoods for the fixed
anchors and clutter. Concretely, for a retained observation
\(a=(o_1,\ldots,o_k)\), let

\[
U_{jd}
=\frac{p_d\pi_{d,t_j}}{\omega_{t_j}}
\exp\!\left\{\frac{\|x_j\|^2}{2}\right\}
\det(\Sigma_{d,t_j})^{-1/2},
\qquad A_j=\max_d U_{jd},
\]

with the Gaussian factor replaced by one on a zero-dimensional stratum. A
certified covariance lower bound may conservatively replace the determinant.
If \(\kappa_j\) bounds physical clutter at \(o_j\) and \(\vartheta\) is the
reference activity, set \(C_j=\kappa_j+\vartheta A_j\). The cap-aware
injection polynomial is

\[
\mathcal P_N(a)
=\sum_{\substack{D\subseteq\{1,\ldots,k\}\\|D|\le N}}
(N)_{|D|}
\prod_{j\in D}A_j
\prod_{j\notin D}C_j.
\]

Dropping miss factors and using \(e^{1-K_{\rm tot}}\le e\) gives the global
real-arithmetic certificate

\[
H_m(a,z)=\epsilon_m+(1-\epsilon_m)e\mathcal P_N(a).
\]

For overflow, the numerator is at most one, so

\[
H_m(\dagger,z)
=\epsilon_m+\frac{1-\epsilon_m}{\lambda_m(\dagger)}.
\]

The executable conjugate guide now issues these bounds with exact-rational
Gershgorin covariance witnesses, directed log arithmetic, full flattened
\(\nabla\log\widetilde h\) and
\(\nabla^2\log\widetilde h\) bounds, canonical observation binding, and
fail-closed resource limits. This is a **model-level real-arithmetic
certificate** under the declared normalized probability-simplex and Markov
kernel semantics.

The represented bridge deliberately uses a coarser, successful-evaluation
contract because a small uniform floating-point error bound is unavailable on
unbounded Gaussian coordinates. Let

\[
L_m=-\operatorname{rd}_{\uparrow}
  \log(1/\epsilon_m),
\qquad
U_m=C_m^{\log,+},
\qquad
W_m=\operatorname{rd}_{\uparrow}(U_m-L_m),
\]

where \(C_m^{\log,+}\) is the checkpoint-eleven directed log upper
witness. The reciprocal logarithm and endpoint subtraction are evaluated from
exact rationals represented by the binary64 inputs and rounded in the
displayed directions. For a canonical capped state and represented reverse
time, the operational bridge calls the existing restricted evaluator and
accepts its raw log value \(r\) only when the returned record has the same model,
observation, time, and state, \(r\) is an exact finite binary64 value, and

\[
L_m\le r\le U_m.
\]

An accepted value is preserved bit for bit; there is no tolerance, clipping,
projection, or fallback. Since both the exact model value and the admitted
represented value lie in the same interval,

\[
\lvert r-\log\widetilde h_{u,m}(y;a,z)\rvert\le W_m.
\]

For two admitted endpoints, correctly rounded binary64 subtraction also gives
the direct represented edit envelope

\[
\left|\operatorname{RN}(r'-r)\right|\le W_m.
\]

This direct range argument avoids adding a separate pointwise-error allowance
when bounding the magnitude of an edit assembled from two admitted outputs.
For an evaluator outside this gate with an independently proved pointwise
bound
\(\lvert\log h^{\rm op}-\log h\rvert\le\eta_h\), the generic edit envelope
obtained by the triangle inequality is
\(\log(H_m/\epsilon_m)+2\eta_h\). The present result is a coarse uniform
discrepancy bound over **successful** range-gated point evaluations, not a
small forward-error analysis or a total evaluator over unbounded coordinate
charts. It admits the represented scalar jump-guide value and edit
contribution only. It does not certify coordinate derivatives, continuous
drift, residual composition, a controlled clock, sampler liveness, or a path
sampler. All sealing and provenance guarantees in this operational layer
assume a trusted, unmodified Python runtime.

Checkpoint fifteen adds a separate **jump-only operational surrogate** that
totalizes exactly the preceding typed point failures. Let

\[
\mu_m=\frac{\iota(L_m)+\iota(U_m)}{2},
\qquad
m_m=\operatorname{RN}(\mu_m),
\]

where \(\iota\) maps a finite binary64 value to its exact rational and the
midpoint is rounded to binary64 once, with exact zero canonicalized positive.
The totalized point function preserves a successful range-gated raw value
bitwise; it returns the fixed \(m_m\) only for a typed preconditioner numerical
failure or typed represented-range failure. Invalid inputs, resource refusal,
foreign or stale provenance, live-binding mismatch, and untyped structural
failures remain refusals. Before certification, a fixed-outcome preflight
checks worst-case point-evaluation resources over the full capped finite-
binary64 state domain and every reverse time; that work witness is replayed on
every live call.

The global and fallback-specific point witnesses are

\[
W_m=\operatorname{rd}_{\uparrow}
\bigl(\iota(U_m)-\iota(L_m)\bigr),
\qquad
B_m^{\mathrm{fb}}=\operatorname{rd}_{\uparrow}
\max\{\iota(m_m)-\iota(L_m),\iota(U_m)-\iota(m_m)\}.
\]

Every legal edit is formed from two evaluations of the same operational point
function. The record stores the exact rational endpoint coboundary

\[
\Delta_{\mathbb Q}\ell_m^{\mathrm{op}}(x,y)
=\iota(\ell_m^{\mathrm{op}}(y))
-\iota(\ell_m^{\mathrm{op}}(x))
\]

and rounds that exact difference once for its binary64 `log_ratio`. Its
magnitude is at most \(W_m\); its discrepancy from the exact analytic edit is
bounded by the outward sum of its endpoint witnesses and hence by \(2W_m\).
The exact rational operational differences telescope and reverse exactly.
Independently rounded binary64 edge values need not close a cycle exactly.

This construction defines a new operational target whenever fallback occurs.
It supplies no equality with the analytic guide, conditional posterior, or
Doob bridge and no coordinate derivatives, continuous drift, rate envelope,
clock, randomness, path, or sampler admission. The checkpoint-fourteen
composer still consumes the successful-only range gate and has not been
migrated to this surrogate.

Checkpoint sixteen separately resolves checkpoint thirteen's strictly active
binary64 cubic-gate refusal for **jump-only operational use**. It leaves the
checkpoint-thirteen evaluator unchanged. Let \(h=s_{\mathrm{hold}}\), let
\(\iota\) map each finite binary64 input to its exact rational value, and define

\[
a_{R,\mathbb Q}(s)=
\begin{cases}
0, & s\le h,\\[2mm]
\left(
\dfrac{\iota(s)-\iota(h)}{\iota(S)-\iota(h)}
\right)^3, & s>h.
\end{cases}
\]

Write \(G_{64}(y,c_R)\) for the represented output of the bounded residual
core materialized privately from the certified checkpoint. The operational
point function is branch-defined:

\[
r_{64}^{\mathrm{op}}(s,y;c_R)=
\begin{cases}
r_{64}^{(13)}(s,y;c_R),
& \text{if checkpoint thirteen returns successfully},\\[1mm]
\operatorname{RN}\!\left(
a_{R,\mathbb Q}(s)\,\iota(G_{64}(y,c_R))
\right),
& \text{only if checkpoint thirteen raises its exact typed}\\[-1mm]
& \quad\text{active tiny-gate resolution error}.
\end{cases}
\]

The second branch is admitted only when \(s>h\) and the legacy staged gate is
finite, nonnegative, and smaller than the minimum normal binary64 value. Its
exact rational product is rounded once to nearest-even binary64, and exact zero
is canonicalized positive. Every successful checkpoint-thirteen point value is
therefore preserved bit for bit. On the rescaled branch, the outward point
witness is

\[
B_R^{\mathrm{op}}(s)=
\operatorname{rd}_{\uparrow}
\left(a_{R,\mathbb Q}(s)\,\iota(B_R)\right),
\]

and the record stores the exact rational one-round error. The implementation
also enforces
\(\lvert G_{64}\rvert\le B_R\) structurally. It limits every exact numerator
and denominator to 8,192 bits; exceeding that implementation resource bound is
a refusal rather than an approximation.

For same-time, same-condition endpoints, checkpoint sixteen stores

\[
\Delta_{\mathbb Q}r^{\mathrm{op}}(x,y)
=\iota(r_{64}^{\mathrm{op}}(s,y;c_R))
-\iota(r_{64}^{\mathrm{op}}(s,x;c_R))
\]

and rounds this exact endpoint difference once for the binary64 operational
edge. The exact rational endpoint differences reverse and telescope exactly;
independently rounded binary64 edges need not close cycles. Both endpoint
values are structurally bounded by \(B_R\), rescaled-branch endpoints also
obey \(B_R^{\mathrm{op}}(s)\), and the represented edge retains the global
\(2B_R\) witness. Point and difference constructors independently derive the
only admissible branch from the recorded direct time; a digest-recomputed
tiny-gate record cannot be relabelled as a preserved success.

Custody is deliberately stronger than a before/after hash alone. Each supplied
single-row batch is validated, copied into a detached canonical snapshot, and
accepted only when the original-before, snapshot, and original-after streaming
digests agree. Evaluation uses an unexposed model materialized from the
checkpoint with storage disjoint from both the caller model and checkpoint
snapshot, while the caller's bound live model and the private model are both
revalidated against the same residual certificate. The runtime digest binds
round-to-nearest-even binary64 and gradual underflow probes, including consumed
subnormal operands in Python and CPU `torch.float64`; a changed arithmetic mode
is refused before and after evaluation.

This is an operational surrogate on the exact-rescaling branch because
\(G_{64}\) is a represented neural-core value, not an exact real-arithmetic
network evaluation. The checkpoint certifies no small neural forward error,
time or coordinate derivative, continuous drift, exponentiated rate, rate
envelope, clock, RNG, path, or sampler admission. Invalid inputs, resource or
custody failures, core failures, generic arithmetic failures, and subclasses
of the dedicated gate error still propagate. The checkpoint-fourteen composer
does not consume this point function and remains unchanged. Checkpoint
seventeen supplies a separate target-explicit operational composer.

Checkpoint seventeen selects exactly one **jump-only operational-surrogate
target**. For reverse time \(u\), direct time \(s=S-u\), fixed guide
observation, base context \(c_{\mathrm{base}}\), and residual context
\(c_{\mathrm{resid}}\), it defines

\[
\Phi_{\mathbb Q}^{\mathrm{op}}(u,x)
=\iota\!\left(V_{64}(S-u,x,c_{\mathrm{base}})\right)
+\iota\!\left(
G_{64}^{\mathrm{totalized}}
(u,x;\text{fixed observation})
\right)
+\iota\!\left(
R_{64}^{\mathrm{totalized}}(S-u,x,c_{\mathrm{resid}})
\right).
\]

Here each component is the finite represented point value returned by its
certified owner, and \(\iota\) lifts that binary64 value to its exact rational.
The factory requires the exported target-policy string exactly; it refuses to
infer an analytic, conditional, posterior, or Doob target from the components.
For one active process-valid birth, death, or replacement candidate
\(x\to y\), the exact composed edge is

\[
\begin{aligned}
\Delta_{\mathbb Q}\Phi^{\mathrm{op}}(x,y)
&=\Phi_{\mathbb Q}^{\mathrm{op}}(u,y)
-\Phi_{\mathbb Q}^{\mathrm{op}}(u,x)\\
&=\Delta_{\mathbb Q}V_{64}
+\Delta_{\mathbb Q}G_{64}^{\mathrm{totalized}}
+\Delta_{\mathbb Q}R_{64}^{\mathrm{totalized}},\\
\Delta_{64}\Phi^{\mathrm{op}}(x,y)
&=\operatorname{RN}_{64}\!\left(
\Delta_{\mathbb Q}\Phi^{\mathrm{op}}(x,y)
\right).
\end{aligned}
\]

The implementation recomputes all six endpoint point values. It ignores the
three separately rounded component edges when forming the aggregate, sums the
exact endpoint fractions, and rounds only the final aggregate to nearest-even
binary64, with exact zero canonicalized positive. Exact rational reversal and
cycle telescoping follow from the common point potential; independently
rounded binary64 aggregate edges are not certified to close cycles. Every
exact numerator and denominator is capped at 8,192 bits, and overflow of this
work limit is a refusal rather than an approximation.

Let \(B_V^{\mathrm{pt}}\), \(B_G^{\mathrm{op}}\), and
\(B_R^{\mathrm{pt}}\) be the certified global represented point-magnitude
witnesses, and let \(D_V^{\mathrm{edge}}\),
\(D_G^{\mathrm{op}}\), and \(D_R^{\mathrm{edge}}\) be the corresponding
global represented edge witnesses. Checkpoint seventeen stores outward-rounded
sums

\[
B_\Phi^{\mathrm{op}}
=\operatorname{rd}_{\uparrow}
\left(B_V^{\mathrm{pt}}+B_G^{\mathrm{op}}+B_R^{\mathrm{pt}}\right),
\qquad
D_\Phi^{\mathrm{op}}
=\operatorname{rd}_{\uparrow}
\left(D_V^{\mathrm{edge}}+D_G^{\mathrm{op}}+D_R^{\mathrm{edge}}\right).
\]

These are operational magnitude bounds only. They are not an aggregate
analytic-target discrepancy certificate, a small neural-forward-error bound,
or an exponentiated domination result.

The certificate transitively binds the process, schedule/horizon, candidate
identity, fixed guide outcome, both context schemas, both totalizer
certificates, base and residual checkpoints and provenance, runtimes, and a
composition-role digest. The base is evaluated through an unexposed model
materialized from its certified checkpoint, while the caller-supplied live
base remains bound for custody checks. External base, private base, external
residual, and private residual model state storage must be pairwise disjoint,
including overlapping views. Candidate configurations and contexts are copied
and streaming-digested; original-before, snapshot, and original-after identity
is checked, and the live component graph and binary64 nearest-even/gradual-
underflow environment are revalidated before and after composition. No
component exception is caught or converted into another fallback.

This checkpoint is an operational log-space composer, not a claim that
\(\Phi_{\mathbb Q}^{\mathrm{op}}\) is the exact analytic, conditional,
posterior, or Doob target. It preserves neither checkpoint fourteen's combined
bits nor a rounded-edge cycle identity. It performs no aggregate
exponentiation and constructs no rate-space envelope, controlled total exit,
clock, waiting-time or acceptance RNG, coordinate derivative, continuous
drift, initializer, path, or sampler admission.

Checkpoint eighteen separately exponentiates that explicit operational edge.
Let

\[
\nu_{S-u}^0(x,\mathrm dy)
=\frac{Q_{S-u}^0(x,\mathrm dy)}{\Lambda_{S-u}^0(x)}
\]

be the process-owned normalized reference candidate law when
\(\Lambda_{S-u}^0(x)>0\). The operational-surrogate candidate-measure
integrand is

\[
I_{\mathbb Q}^{\mathrm{op}}(u,x,y)
=\Lambda_{S-u}^0(x)
\exp\!\left\{\Delta_{\mathbb Q}\Phi^{\mathrm{op}}(u;x,y)\right\},
\]

so that

\[
Q_u^{\mathrm{op}}(x,\mathrm dy)
=I_{\mathbb Q}^{\mathrm{op}}(u,x,y)\,
\nu_{S-u}^0(x,\mathrm dy).
\]

The exponent is checkpoint seventeen's exact reduced rational edge, not its
rounded binary64 display. Both that edge and the represented reference exit
are dyadic. Checkpoint eighteen converts them to exact terminating Decimals,
encloses the exponential with adjacent correctly rounded Decimal values,
multiplies the reference exit directly with floor/ceiling contexts, and then
converts outward to binary64. Direct product construction avoids requiring a
finite standalone binary64 exponential. The adaptive precision schedule is
\(192,384,768,1536\); 384 is a schedule milestone, not an unconditionally
executed independent audit. A candidate succeeds only when both Decimal
interval endpoints select one correctly rounded finite normal binary64 rate.
Subnormal, zero-rounded, overflowing, work-limit, nonnested, or unresolved
active products are refused.

For checkpoint seventeen's represented global edge bound
\(D_\Phi^{\mathrm{op}}\), a no-RNG intensity preflight constructs

\[
E_{\mathbb Q}^{\mathrm{op}}(u,x)
=\operatorname{rd}_{\uparrow}
\left[
\Lambda_{S-u}^0(x)
\exp\!\left\{\iota(D_\Phi^{\mathrm{op}})\right\}
\right].
\]

Since the normalized candidate law has unit mass,

\[
\lambda_{\mathbb Q}^{\mathrm{op}}(u,x)
=\int I_{\mathbb Q}^{\mathrm{op}}(u,x,y)\,
\nu_{S-u}^0(x,\mathrm dy)
\le E_{\mathbb Q}^{\mathrm{op}}(u,x).
\]

The same construction with the process-bound maximum reference exit gives a
global envelope. When the authenticated reference exit is exactly zero, the
controlled exit is exactly zero and no candidate edge is evaluated. Otherwise
the envelope is an upper bound, not an exact total exit. Envelope construction
invokes no route draw or random bits, and the candidate record is evaluated
only after a mandatory source/time/owner-matched envelope is supplied.

This checkpoint is specific to the exported operational-surrogate target. It
does not establish an analytic, conditional, posterior, Doob, or stationary
target; detailed balance of independently rounded rates; full candidate-rate
totality; route-draw admission; a waiting or acceptance decision; coordinate
derivatives or drift; initialization; a path; or a sampler. Future acceptance
must use the actual represented ratio
\(I_{\mathbb Q}^{\mathrm{op}}/E_{\mathbb Q}^{\mathrm{op}}\), not a simplified
exponential that assumes the outward envelope equals its real-arithmetic
antecedent.

Checkpoint nineteen adds one **successful-return local** operational thinning
sequence for the same explicit surrogate. Write \(I_{64}^{\mathrm{op}}\) for a
successful checkpoint-eighteen represented candidate integrand and
\(E_{64}^{\mathrm{op}}\) for its authenticated represented local envelope. For
a caller-supplied local clock interval \([a,b]\), let \(r=b-a\). Under the
declared ideal-prefix mapping, successive raw 64-bit words \(w_j\) from an exact
NumPy Philox generator define

\[
K_n=\sum_{j=1}^{n}w_j2^{64(n-j)},
\qquad
U\in\left[
\frac{K_n}{2^{64n}},
\frac{K_n+1}{2^{64n}}
\right),
\]

and the ideal waiting time is

\[
\tau(U)=\frac{-\log U}{E_{64}^{\mathrm{op}}}.
\]

Directed Decimal intervals enclose both \(\tau\) and \(a+\tau\) at the same
192/384/768/1536 precision schedule. The ideal-real eligibility rule is
inclusive, \(\tau\le r\); local exhaustion is certified only when the directed
lower waiting bound is strictly greater than \(r\). A returned hit is stricter:
the waiting interval and the absolute-time interval must each have a unique
round-to-nearest-even binary64 image, and the public timestamp must satisfy

\[
a<t_{64}^{\mathrm{proposal}}<b.
\]

Thus exact real equality at \(b\), or an interior ideal time whose represented
timestamp collapses to either boundary, is refused rather than returned,
clipped, or relabelled as local exhaustion. `proposal_time` is the authoritative
local operational-clock timestamp. It does not replace the separately recorded
midpoint-frozen reverse/direct generative times used by the reference intensity,
potential, and route.

Only after a returned clock hit may the same Philox stream enter the
process-owned normalized-reference route draw. Checkpoint nineteen inherits
that composer's binary64 CDF, uniform-integer, and finite standard-normal
semantics; it does not upgrade the route to a variable-random-bit exact
categorical or Gaussian law. For a fully replayed candidate, acceptance uses
the exact reduced rational quotient

\[
p_{\mathrm{acc}}^{64}
=\frac{I_{64}^{\mathrm{op}}}{E_{64}^{\mathrm{op}}}
=\frac{n}{d}\in(0,1].
\]

The Bernoulli decision concatenates complete Philox raw words, retains the
required high bits, discards fixed padding, and uses denominator rejection; it
never divides the rates in binary64 or substitutes the simplified exponential.
Conditional on the declared uniform-word model and a resolved bounded trial,
its acceptance probability is exactly \(n/d\). Ambiguity after 64 waiting words
or exhaustion of 128 denominator-rejection trials is a resource refusal, not a
timeout, rejection, or acceptance. No independence, physical-randomness, or
cryptographic property of Philox is proved.
The same mutable Philox stream continues across waiting, route, and acceptance,
with before/after state replay. This is a sequential local-stream contract, not
the run/step/occurrence/proposal counter-key contract required by Section 8.2.

This checkpoint does not loop after rejection, advance the local clock,
recompute the intensity or envelope after an accepted edit, enforce a proposal
ceiling, construct lineage, integrate continuous drift, initialize a state, or
return a path. It neither computes the exact active controlled total exit nor
proves all-route rate totality or liveness. Its focused operational route
evidence is all-atomic; a continuous-destination operational fixture and the
complete sampler remain separate obligations.

Checkpoint twenty adds a distinct **bounded successful-return coordination
layer** around checkpoint nineteen without changing checkpoint nineteen's
historical contract. Fix one represented local interval \([a,b]\), one frozen
reverse/direct generative time, immutable contexts, and a proposal cap
\(B\in\{0,\ldots,64\}\). Let \(x_k\), \(a_k\), \(J_k\), and \(E_k\) denote the
state, represented local-clock cursor, process-owned reference-intensity
record, and checkpoint-eighteen envelope before completed proposal \(k\). A
checkpoint-nineteen hit and decision give \(t_k\), candidate \(y_k\), and
\(A_k\in\{0,1\}\). The authoritative recurrence is

\[
a_{k+1}=t_k,
\qquad
x_{k+1}=
\begin{cases}
x_k, & A_k=0,\\
y_k, & A_k=1.
\end{cases}
\]

On rejection, \(J_{k+1}\) and \(E_{k+1}\) are the exact same runtime objects as
\(J_k\) and \(E_k\); only the represented cursor advances. On acceptance, the
destination is immediately passed to the process-owned deterministic
intensity preflight at the same frozen reverse time, and the resulting fresh
intensity is immediately passed to checkpoint eighteen's no-RNG envelope
preflight:

\[
J_{k+1}
=\operatorname{PreflightIntensity}(x_{k+1},u_{\mathrm{frozen}}),
\qquad
E_{k+1}=\operatorname{PreflightEnvelope}(J_{k+1}).
\]

Every accepted intensity/envelope pair is identity-distinct from the initial
pair and every earlier accepted epoch. Thus a semantic \(A\to B\to A\) return
cannot reinstall the earlier \(A\) parent objects.

This refresh occurs even after the last permitted accepted proposal. The next
loop-top action first recognizes a deterministic structural-zero or
zero-duration hold. Structural zero has precedence if both apply. Otherwise,
if \(k=B\) and the local state remains active, the entire call raises the typed
proposal-cap refusal before another waiting draw. Hence \(B=0\) admits a
no-RNG deterministic terminal hold but refuses an active interval before RNG.
An active checkpoint-nineteen waiting draw whose certified wait exceeds the
right endpoint returns `right_endpoint_exhausted`; it is not counted as a
proposal. A successful `OperationalLocalThinningResult` is returned only with
a terminal checkpoint-nineteen waiting record certifying interval exhaustion.
There is no successful budget-truncated result.

One mutable exact NumPy Philox object continues through every wait, inherited
route, potential/rate evaluation, Bernoulli, and subsequent iteration. The
potential/rate computations and accepted-state refresh must leave that supplied
stream unchanged. A child numerical/resource refusal or active proposal-cap
refusal aborts the aggregate call and retains all bits already consumed; there
is no clone, rollback, timeout, rejection relabelling, or partial result.

This checkpoint coordinates successful operational records only. Repeated
renewals start from rounded binary64 proposal timestamps, and the inherited
categorical, integer, and Gaussian route remains finite-resolution. Therefore
the layer does not certify an exact real-time Poisson/CTMC or unconditional
frozen-jump law, unconditional local completion, exact route sampling,
continuous-destination operational evidence, the analytic/conditional/
posterior/Doob target, exact active total exit, rounded detailed balance or
stationarity, counter-keyed streams, lineage, drift, initialization, a path,
Strang integration, liveness, or the full sampler. Focused route evidence is
still all-atomic.

Checkpoint twenty-one adds a separate **same-runtime route-evidence
successor** without changing the frozen checkpoint-nineteen or checkpoint-
twenty schemas. Around one delegated post-clock route draw it retains the
complete canonical NumPy Philox state before and after the draw. Offline
validation reconstructs a fresh local Philox generator from the pre-state,
calls the frozen process-owned candidate composer exactly once, and requires
both the replayed candidate digest and every post-state field to agree. The
evidence preserves the labelled source occurrence, source multiplicity,
endpoint types and dimensions, exact binary64 coordinate tuples, and the
recomputed represented analytic route factors. Fixed evidence covers a
continuous birth and both 2D-to-3D and 3D-to-2D reset replacements; death is
retained as a non-continuous route without hidden resampling.

This is concrete finite-resolution operational custody, not an ideal route-law
proof. NumPy's categorical, integer, and standard-normal outputs remain
finite-resolution; the evidence records no bounded raw normal-word trace and
does not establish an analytic Lebesgue output law, continuous-destination
distribution recovery, Test 29, all-route totality, liveness, or a path.

Checkpoint twenty-two adds an **ordered bounded-loop route-evidence overlay**
without changing checkpoints nineteen, twenty, or twenty-one. It captures the
complete canonical Philox snapshots \(G_{\mathrm{in}}\) and
\(G_{\mathrm{out}}\) around one black-box checkpoint-twenty call. Starting
from a fresh local reconstruction of \(G_{\mathrm{in}}\), validation replays,
for each completed proposal \(k\),

\[
G_k^{\mathrm{wait,in}}
\xrightarrow{\;\text{recorded waiting raw64 prefix}\;}
G_k^{\mathrm{route,in}}
\xrightarrow{\;\text{checkpoint-21 route replay}\;}
G_k^{\mathrm{accept,in}}
\xrightarrow{\;\text{recorded Bernoulli raw64 prefix}\;}
G_{k+1}^{\mathrm{wait,in}}.
\]

After the last completed proposal it also replays the checkpoint-nineteen
terminal waiting prefix. The final reconstructed snapshot must equal
\(G_{\mathrm{out}}\) field by field. Exactly one checkpoint-twenty-one evidence
record is positionally bound to each checkpoint-twenty iteration's waiting,
intensity, envelope, route, candidate, source, destination, decision, and RNG
fields. Rejection-parent reuse, accepted-state intensity/envelope refresh,
terminal classification, proposal-cap refusal, and clock recurrence remain
checkpoint-twenty semantics rather than being reimplemented here.

Creation and offline validation perform the reconstruction on fresh local
Philox objects. Offline validation accepts no caller RNG. If the additive
overlay fails after the black-box loop has succeeded, it raises and returns no
partial composite result; the caller bits already consumed by checkpoint
twenty are not rolled back. The route objects in the overlay are replay
objects, not the original Python route instances or snapshots captured at the
original route-call sites.

This is a bounded, successful-return, same-runtime transcript-custody result.
It does not bound NumPy's internal normal raw-word consumption, upgrade the
finite-resolution route to an exact categorical/integer/Gaussian or analytic
Lebesgue law, establish Test 29 distribution recovery, provide unconditional
completion or liveness, preserve an analytic/conditional/posterior/Doob
target, or construct counter-keyed lineage, drift, initialization, a path,
Strang integration, or the full sampler.

Checkpoint twenty-three adds a separate **direct counter-key namespace and
persistent-lineage sidecar** without changing checkpoints nineteen through
twenty-two. It binds to one exact live checkpoint-twenty-two owner. For an
admitted run identifier \(r\), domain \(d\), step index \(s\), occurrence serial
\(\ell\), and proposal index \(p\), its address is

\[
K(r,d)=(r,\delta(d)),
\qquad
C(s,\ell,p)=(0,s,\ell,p),
\]

where \(K\) is passed directly as the NumPy Philox key and \(C\) directly as
the initial counter. No component is hashed, truncated, XORed, folded, or
converted to a scalar seed. The fixed domains are

| Domain | \(\delta(d)\) | Admissible subject coordinates |
|---|---:|---|
| jump proposal | 1 | \(\ell=0\), \(0\le p<64\) |
| terminal wait | 2 | \(\ell=0\), \(0\le p\le64\) |
| initializer | 3 | \(1\le\ell\le2^{64}-1\), \(p=0\) |
| Brownian left half-step | 4 | \(1\le\ell\le2^{64}-1\), \(p=0\) |
| Brownian right half-step | 5 | \(1\le\ell\le2^{64}-1\), \(p=0\) |

All displayed address limbs lie in the exact uint64 range. Within this fixed
schema, equality of the complete key and counter implies equality of the
domain, run, step, occurrence, and proposal components, so the admitted address
map is injective. This is a namespace statement, not a statistical-independence
or collision-resistance theorem. Reissuing the same address intentionally
reconstructs the same stream, and the module has no global run-ID or one-shot
issuance registry.

Every issued receipt stores the complete checkpoint-twenty-one canonical
Philox snapshot at that direct address: the four-word buffer is zero, its
position is four, and the cached uint32 fields are zero. Validation reconstructs
a fresh local generator and requires the complete snapshot digest to agree.
This is same-runtime reconstruction only. A receipt is initially unused and
explicitly records that checkpoint twenty-two did not consume it. The
initializer and Brownian factories reserve addresses but draw no initializer or
Brownian random variable.

For a canonical unlabelled model configuration

\[
x=(e_0,\ldots,e_{n-1}),
\]

the lineage sidecar is an ordered tuple

\[
L=((\lambda_0,e_0),\ldots,(\lambda_{n-1},e_{n-1})),
\qquad
\pi(L)=(e_0,\ldots,e_{n-1})=x.
\]

Bootstrap assigns

\[
\operatorname{serial}(\lambda_i)=i+1,
\qquad
\operatorname{origin}(\lambda_i)
=(\mathrm{initial},\mathrm{initialization\_index},i).
\]

Thus equal-valued duplicate events at distinct canonical tuple positions have
distinct identifiers. This is an arbitrary labelled lift of the unlabelled
model state; identifiers never enter a potential, guide, reference kernel,
rate, candidate proposal, or other model projection.

For completed parent proposal \(k\), the deterministic sidecar transition is

| Parent outcome | Exact destruction | Fresh creation | Post-state rule |
|---|---|---|---|
| rejected birth, death, or replacement | none | none | reuse the exact pre-state object |
| accepted birth | none | `birth(step_index, k)` | append the destination and stable-sort only by `event.model_key()` |
| accepted death | identifier at the exact parent `source_occurrence_index` | none | retire that identifier and stable-sort the survivors |
| accepted replacement | identifier at the exact parent `source_occurrence_index` | `replacement(step_index, k)` | retire the source, append the destination, and stable-sort only by `event.model_key()` |

An accepted birth or replacement takes the current `next_serial` and then
increments it. Survivors retain exact object identity. Retired identifiers are
appended to a persistent ledger and cannot be reused within that exact custody
chain. Initial serials are contiguous from one, all live and retired serials
remain unique and below `next_serial`, edit origins are unique and strictly
increase lexicographically in serial order, and every replacement origin must
have a feasible earlier retired source. The operational bounds are

\[
|L_{\mathrm{live}}|\le100000,
\qquad
|L_{\mathrm{live}}|+|L_{\mathrm{retired}}|\le100064,
\qquad
\sum_{e\in\pi(L)}\dim(e)\le4000000.
\]

The scalar `next_serial` validator reserves \(2^{64}\) as an exhausted
one-past-last sentinel. The simultaneous contiguous-ledger and 100064-identifier
bounds are tighter, so no valid operational chain in this checkpoint reaches
that sentinel. Independent bootstraps and deliberate forks must use a fresh
`run_id`. The retired ledger detects reuse only along the exact continued state
chain and does not police deliberate forks from an older state. The
`initialization_index` is provenance, not an occurrence-address limb.

Annotation first fully revalidates the supplied checkpoint-twenty-two result.
It then binds one lineage transition to each exact parent iteration and its
positionally corresponding checkpoint-twenty-one route-evidence record. The
terminal waiting record creates no transition and reuses the exact final
lineage-state object. Offline lineage validation accepts and advances no
caller-owned RNG and consumes no checkpoint-twenty-three receipt. Its
transitive checkpoint-twenty-two validation may advance fresh local replay
generators while deterministically reconstructing the recorded parent chain.

This checkpoint therefore certifies a standalone address/reconstruction
contract and a post-hoc lineage prerequisite only. It does not make checkpoint
twenty-two proposal-keyed, prove that its parent consumed a contract stream,
prevent duplicate address use or global run-ID reuse, consume occurrence,
initializer, or Brownian streams, certify coarse/fine Brownian coupling,
statistical independence or physical randomness, implement continuous drift or
initialization, construct a path or Strang step, establish an exact frozen-jump
or real-time Poisson/CTMC law, preserve an analytic/conditional/posterior/Doob
target, prove liveness, or admit the full sampler.

Checkpoint twenty-four adds a separate **bounded counter-keyed operational-
epoch loop** without changing checkpoints nineteen through twenty-three. The
successor owns one new direct domain,

~~~text
operational_epoch
~~~

with fixed tag 6. It does not extend or mutate checkpoint twenty-three's frozen
five-domain mapping. For exact uint64 run identifier \(r\), step index \(j\),
and completed-proposal count \(p<64\), the active-epoch address is

\[
K_{r}^{E}=(r,6),
\qquad
C_{j,p}^{E}=(0,j,0,p).
\]

No address limb is hashed, truncated, XORed, folded, or converted to a scalar
seed. Tag 6 is disjoint from checkpoint twenty-three's tags 1--5. Within the
fixed schema, equality of complete tag-6 keys and counters implies equality of
the run, step, and epoch coordinates. As before, that representation statement
does not imply independence, physical randomness, cryptographic collision
resistance, global run-ID uniqueness, or one-shot address use.

At every active loop boundary, \(p\) is the number of already completed
candidate proposals. The successor constructs and records the tag-6 receipt,
reconstructs one fresh local same-runtime Philox generator at its unused
initial state, and passes that exact generator to the frozen checkpoint-
nineteen sequence. Its within-epoch chronology is

\[
G_{j,p}^{E,0}
\xrightarrow{\;\mathrm{wait}\;}
\begin{cases}
G_{j,p}^{E,\mathrm{term}},
  & \text{right endpoint exhausted},\\
G_{j,p}^{E,\mathrm{route}}
\xrightarrow{\;\mathrm{route}\;}
G_{j,p}^{E,\mathrm{accept}}
\xrightarrow{\;\mathrm{Bernoulli}\;}
G_{j,p}^{E,1},
  & \text{candidate due}.
\end{cases}
\]

The wait, route, and represented-ratio acceptance therefore retain checkpoint
nineteen's one-stream continuity. If the active wait exhausts the right
endpoint, that same tag-6 stream is the stochastic terminal epoch; it is not
redrawn, relabelled, or replaced by a checkpoint-twenty-three `terminal_wait`
stream. It creates no proposal, route witness, or lineage transition. Every
actual proposal occurs in one uniquely indexed active epoch, but not every
active epoch produces a proposal.

A structural-zero or zero-duration hold known at loop preflight is different.
Structural zero retains checkpoint twenty's precedence when both apply. The
successor binds the frozen checkpoint-twenty-three `terminal_wait` receipt at
completed-proposal coordinate \(p\), invokes only the deterministic no-word
checkpoint-nineteen hold, and requires the reconstructed generator to remain
at the receipt's exact unused initial state. The immutable receipt's historical
`parent_execution_used_this_stream=False` field is not changed. The checkpoint-
twenty-four result separately records the zero-word terminal binding. No
random-word-consuming tag-2 terminal-wait execution is certified.

The successful transcript shapes are therefore

\[
(E_0,P_0),\ldots,(E_{n-1},P_{n-1}),E_n^{\mathrm{stochastic\ terminal}}
\]

or

\[
(E_0,P_0),\ldots,(E_{n-1},P_{n-1}),T_n^{\mathrm{deterministic\ hold}}.
\]

Here each \(P_k\) is a completed proposal and \(T_n\) consumes zero words.
The zero-proposal deterministic result consists only of \(T_0\). A stochastic
terminal transcript has one more tag-6 epoch than proposals. At an active loop
boundary with \(p=B\), where the exact caller-supplied proposal budget obeys
\(0\le B\le64\), the operation refuses before issuing or advancing another
active-epoch stream. A deterministic terminal hold is checked first and may
succeed at \(p=B\). Budget exhaustion never returns a truncated transcript.

Every candidate epoch binds one exact checkpoint-twenty iteration, one
checkpoint-twenty-one route-evidence record, and one checkpoint-twenty-three
lineage transition. Rejection advances the represented cursor while reusing
the exact state, intensity, envelope, and lineage-state objects. Acceptance
uses the candidate destination, immediately constructs fresh intensity and
envelope parents at the unchanged frozen generative time, and applies exact
indexed destruction, fresh creation where applicable, stable model-key-only
ordering, and the retired-ID ledger. A terminal epoch creates no lineage
transition and reuses the exact final lineage state. These ordered algorithmic
records are not a physical or lineage-aware path admission.

The sealed validation boundary is deliberately deeper than digest equality.
Domain and coordinate tags are exact non-Boolean integers. Stored base and
residual contexts are exact tuples of canonical binary64 values with
role-specific digests, and every proposal must match the result's ordered
proposal, iteration, route-evidence, and lineage-transition digest sequences.
Before nested reconstruction or hashing, bounded exact-type preflights cover
candidate source/destination configurations and events, waiting/acceptance raw
words, and live-plus-retired lineage records. Validation then invokes the
frozen deep validators for the supplied wait, checkpoint-twenty iteration, and
checkpoint-twenty-one evidence; requires exact parent certificate and record
objects where custody is identity-based; and requires each unlabelled model-
projection event to be the exact event object held by its lineage occurrence.

There is no Philox carry between epochs:

\[
G_{j,p+1}^{E,0}
:=\operatorname{DirectPhilox}(r,6,j,p+1),
\qquad
\text{without using }G_{j,p}^{E,1}.
\]

Each address has one authoritative generative execution in the returned
record. Checkpoint nineteen's shadow checks, checkpoint twenty-one's route
replay, and offline validation may reconstruct and advance local copies at the
same address. Thus the checkpoint does not claim only one physical evaluation
or globally exclusive consumption of an address. It accepts no caller RNG and
returns no partial result on failure, but this is caller-RNG isolation rather
than a rollback guarantee for arbitrary nested side effects or a global
one-shot stream registry.

Checkpoint twenty-four leaves checkpoint twenty-two's historical sequential
caller-stream execution unchanged and consumes none of checkpoint twenty-
three's legacy tag-1 `jump_proposal` receipts. It certifies only bounded,
successful-return, same-runtime operational-epoch-keyed execution for the
explicit operational surrogate. It does not establish an exact categorical,
integer, Gaussian, real-time Poisson/CTMC, or unconditional frozen-jump law;
unconditional completion or liveness; analytic/conditional/posterior/Doob
target preservation; exact active-total-exit computation; all-route totality;
rounded detailed balance or stationarity; occurrence, initializer, or Brownian
stream consumption; Brownian coupling; drift, initialization, a path, a Strang
step, or the full sampler.

Checkpoint twenty-five adds a separate **bootstrap initializer-stream prefix-
custody successor** without changing checkpoints twenty-three or twenty-four.
It binds one exact live checkpoint-twenty-four owner and that owner's exact
checkpoint-twenty-three lineage owner. Its complete scope is recorded in the
checkpoint-twenty-five audit.

The admitted input is an already existing bootstrap-form lineage state

\[
L_0=((\lambda_1,e_1),\ldots,(\lambda_n,e_n)),
\qquad 0\le n\le64,
\]

with no retired identifiers, `next_serial = n + 1`, initial origins only,
serial \(i+1\) at zero-based position \(i\), matching initialization
provenance, and identity—not merely equality—between each lineage event and
its unlabelled model projection. The initializer step is fixed to zero. For
run ID \(r\) and positive positional serial \(\ell\), the consumed checkpoint-
twenty-three tag-3 receipt has

\[
K_r^I=(r,3),
\qquad
C_\ell^I=(0,0,\ell,0).
\]

`initialization_index` remains provenance and is not an address limb. Equal-
valued duplicate events at different bootstrap positions have different
serials and therefore different counters.

The caller supplies one exact tuple \(w=(w_1,\ldots,w_n)\) satisfying

\[
1\le w_i\le4096,
\qquad
\sum_i w_i\le65536.
\]

Every entry must be an exact non-Boolean Python integer. The complete plan is
preflighted before the first receipt is issued. The empty bootstrap with plan
`()` is the only successful zero-word case. For each live occurrence, the
owner reconstructs a fresh local Philox generator at the exact receipt,
records its initial snapshot, consumes exactly `w_i` values from
`bit_generator.random_raw`, records the final snapshot, and replays the prefix
in the same runtime. Every stored word is an exact Python integer in
\([0,2^{64}-1]\). Recorded execution requires the key and upper counter limbs
to remain unchanged.

The aggregate result binds one record per live occurrence in positional order,
the exact input/final lineage-state object, the complete count and digest
tuples, and exact state/model identity. Validation snapshots the result, state,
nested records, and parent occurrences before replay and compares them again
after every record has been replayed. `consume` likewise compares the returned
state and occurrences to their pre-child baselines. Locally re-digested equal
clones, same-digest alien parent objects, and mutations of an earlier record
during a later replay are refused. Neither consumption nor replay accepts or
advances a caller RNG.

The `raw64` words are deliberately uninterpreted. This checkpoint defines no
cardinality, event type, coordinate, uniform, categorical, integer, Gaussian,
enumeration, rejection, resampling, SIR, reference, tilted, or conditional
initializer output. It certifies occurrence-local tag-3 prefix custody, not an
initializer law or initializer admissibility. Reissuing the same address
deliberately replays the same prefix; no one-shot use, independence, physical-
randomness, portability, or cryptographic claim follows.

A general initializer must choose global structure before final occurrence
serials exist. It therefore requires a future collision-disjoint **global
initializer control domain** with frozen stage/attempt/particle coordinates,
work caps, finite-resolution transforms, branch/failure chronology, and a
mapping from accepted global structure to positional lineage IDs. The exact
tag and counter layout of that future domain are not selected here. Per-
occurrence tag-3 payload prefixes cannot be used circularly to choose their own
cardinality or subjects.

Accordingly, Test 28 remains **OPEN**, Test 29 is unchanged and open, and Test
30 remains **PENDING**. `R2-HYBRID` remains **NOT RUN**. No claim or empirical
result is promoted.

The frozen checkpoint-twenty-five source and focused-test SHA-256 values are,
respectively,
`1a6d6f2434285fc0918ea9d3e7fbd80cbacce55c16c5af56d35033317195e942`
and
`aba48d39acb4a4a3c76a214c18dda00c3ddf139f1c9960827838480788129f66`.
The focused suite passed 61/61 in 393.02 seconds. The unchanged direct
checkpoint-twenty-four parent suite passed 46/46, with zero skipped/failed, in
749.21 seconds of pytest time (750.06 seconds external wall time); the unchanged
direct checkpoint-twenty-three parent suite passed 54/54, with zero skipped/
failed, in 1,042.33 seconds of pytest time (1,043.18 seconds external wall time).
The final nonduplicative five-suite inherited regression passed 200/200, with
zero skipped/failed, in 1,564.54 seconds of pytest time (1,565.54 seconds
external wall time); all ten pre/post source and test hashes matched and no
files changed. The independent disposition is **PASS WITH EXPLICIT SCOPE
LIMITS**, P0=P1=P2=0.

Checkpoint twenty-six adds the separate **global initializer-control
namespace successor** anticipated by checkpoint twenty-five, without changing
the tag-3 occurrence-prefix contract or any earlier execution. It binds the
exact checkpoint-twenty-five owner and its exact transitive checkpoint-twenty-
four and checkpoint-twenty-three owners. Its complete scope is recorded in the
checkpoint-twenty-six audit.

For exact uint64 run ID \(r\), initialization index \(i\), serialized stage
coordinate \(g\), and attempt coordinate \(a\), the direct Philox address is

\[
K_r^G=(r,7),
\qquad
C_{i,g,a}^G=(0,i,g,a).
\]

The literal tag 7 and domain name `global_initializer_control` are required to
be distinct from the exact parent tags 1--6. No hash, folding, scalar seed, or
future occurrence serial enters this construction. The parent ownership is a
transitive certification chain only, so the address can be constructed before
cardinality, events, and lineage identifiers exist.
“Collision-disjoint” here means separation of the direct domain/address tuples;
it does not guarantee unequal emitted words or statistical independence.
`control_role_sha256` is certificate metadata rather than an address
coordinate, so another certified role does not select another prefix.

The caller supplies one exact tuple

\[
P=((g_1,a_1,w_1),\ldots,(g_n,a_n,w_n))
\]

with at most 64 entries, strictly increasing address pairs
\((g_1,a_1)<\cdots<(g_n,a_n)\), exact positive Python-integer counts
\(1\le w_j\le4096\), and aggregate count at most 65,536. The entire plan is
preflighted before the first plan-addressed tag-7 control stream or record is
constructed. Plan `()` is a zero-word namespace no-op that creates no such
stream or record and consumes no plan-addressed word; it is not an empty
configuration or zero-cardinality draw.

For each entry, the owner constructs a fresh local Philox generator at the
direct address, records its exact initial snapshot, consumes exactly \(w_j\)
`raw64` words, records its exact final snapshot, and requires the key and upper
counter limbs to remain unchanged. Every stream, record, and aggregate result
is replayed from its canonical pre-state in the same runtime. Within a supplied
transcript, declared nested identity relations and validation-window
mutation/substitution custody are enforced, and no caller RNG is accepted or
advanced. This is not pre-call provenance: without an issuance registry, a
fully self-consistent value-equal transcript clone prepared before validation,
retaining the exact local certificate and recomputed digests, is not excluded.

The plan order is canonical serialization only. `stage_index` and
`attempt_index` have no stage, retry, branch, failure, abandonment, or adaptive-
chronology semantics. Reissuing an address deliberately replays its prefix; a
longer request overlaps and extends the same prefix and is not an append or
fresh continuation. The checkpoint provides no durable issuance registry,
global run-ID uniqueness, initialization-index uniqueness, one-shot use, or
independence claim.

The words remain uninterpreted. This checkpoint defines no cardinality, event
type, coordinate, configuration, uniform, categorical, integer, Gaussian,
enumeration, rejection, resampling, SIR, reference, tilted, or conditional
initializer output. It does not map an accepted configuration to positional
lineage identifiers or coordinate subsequent tag-3 occurrence payloads.
Although tag 7 includes `initialization_index`, checkpoint twenty-five's tag-3
address does not; tag-3 cross-initialization separation under a reused run ID
is therefore not certified.

Accordingly, Test 28 remains **OPEN**, Test 29 is unchanged and open, and Test
30 remains **PENDING**. `R2-HYBRID` remains **NOT RUN**. The focused suite
passed 45/45 in 323.22 seconds (323.90 seconds external wall time), and the
fresh exact checkpoint-twenty-five parent suite passed 61/61, with zero
skipped/failed, in 389.42 seconds of pytest time (390.14 seconds external wall
time). The final nonduplicative five-suite inherited regression passed 200/200,
with zero skipped/failed, in 1,707.20 seconds of pytest time (1,708.48 seconds
external wall time); all ten pre/post source and test hashes matched and no
files changed. The independent disposition is **PASS WITH EXPLICIT SCOPE
LIMITS**, P0=P1=P2=0. No claim or empirical result is promoted.

Checkpoint twenty-seven adds the **fixed initializer-protocol allocation
successor** over the exact checkpoint-twenty-six owner. Its complete scope is
recorded in the
checkpoint-twenty-seven audit.
The exact strategy tuple and stage-role map are

\[
(\mathtt{enumeration},\mathtt{rejection},\mathtt{sir},\mathtt{reference})
\]

and

\[
\begin{aligned}
0&\leftrightarrow\mathtt{enumeration\_selection},&
1&\leftrightarrow\mathtt{rejection\_attempt},\\
2&\leftrightarrow\mathtt{sir\_particle},&
3&\leftrightarrow\mathtt{sir\_resample},\\
4&\leftrightarrow\mathtt{reference\_candidate}.&&
\end{aligned}
\]

For a fixed positive block tuple
\(W=(w_0,\ldots,w_{B-1})\), every outer work item \(a\) and block \(b\)
uses the injective parent attempt coordinate \(aB+b\). With selection-prefix
count \(s\), the four canonical plans are

\[
\begin{aligned}
P_{\rm enum}&=((0,0,s)),\\
P_{\rm rej}&=((1,aB+b,w_b))_{a,b},\\
P_{\rm SIR}&=((2,jB+b,w_b))_{j,b}\mathbin{\|}((3,0,s)),\\
P_{\rm ref}&=((4,b,w_b))_b.
\end{aligned}
\]

Enumeration requires literal budget one, \(W=()\), and positive \(s\).
Rejection requires a positive fixed attempt budget, nonempty \(W\), and
\(s=0\). SIR requires a positive fixed particle budget, nonempty \(W\), and
positive \(s\); its stage-3 prefix follows every particle block. Reference
requires literal budget one, nonempty \(W\), and \(s=0\). All requests satisfy

\[
|P|\le64,
\qquad 1\le w(P_k)\le4096,
\qquad \sum_k w(P_k)\le65536.
\]

The 64-rejection-attempt and 63-SIR-particle constants are absolute
single-block maxima. Multiblock work items reach the 64-record cap sooner.
Every request is fully preflighted and every parent prefix is materialized
before semantic resolution. Each result binds exact work-item/block indices,
plan position, chronological index, parent record, raw-word tuple, parent
result, and parent plan. The parent plan must be identical, not merely equal.
Validation replays the complete parent result in the same runtime. No caller
or second RNG is accepted.

This checkpoint assigns allocation roles only. It takes no branch and defines
no support enumeration/normalization, rejection predicate or outcome, SIR
weights or resampling law, branch-free reference output law, finite-resolution
transform, cardinality/type/coordinate/configuration generation, accepted-
configuration lineage mapping, or tag-3 coordination. Test 28 remains
**OPEN**, Test 29 remains open and unchanged, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. The hash-stable focused suite passed 76/76 in
197.19 seconds, and independent final reviews report P0=P1=P2=0. No claim or
empirical result is promoted.

Checkpoint twenty-eight adds the **finite-resolution reference-strategy
transformer** over the exact checkpoint-twenty-seven owner. Its complete scope
is recorded in the
checkpoint-twenty-eight audit.
It derives a sealed manifest from the exact process-owned capped-Poisson
reference. For cap \(N\le64\), ordered types \(d\in\mathcal D\), type
dimensions \(k_d\), and \(D=\max_d k_d\), it requests the fixed-word-budget,
no-retry
reference capsule with exact length

\[
L=1+N+ND.
\]

Offset zero is the count word, offsets \(1,\ldots,N\) are contiguous type
words, and the remaining \(N\times D\) words are row-major coordinate slots.
The exact parent plan is the canonical greedy partition of
\(L\le65{,}536\) into blocks of at most 4,096 words. Every raw slot's type and
all \(D\) coordinates, including inactive slots and dimension padding, are
transformed before the count word is decoded. Only then is the leading raw-
slot prefix selected. Stable canonicalization uses `(event.model_key(),
raw_slot_index)` and records both directions of the selected/raw-slot map.

Let \(\bar a\) and \(\bar\rho_d\) be the exact rational values of the reference's
binary64 activity and positive type weights. The manifest records

\[
p_n^C=
\frac{\bar a^n/n!}{\sum_{m=0}^{N}\bar a^m/m!},
\qquad
p_d^T=\frac{\bar\rho_d}{\sum_e\bar\rho_e}.
\]

For either exact target table \(p=(p_i)_{i=0}^{K-1}\), let \(R=2^{64}\).
The positive Hamilton rule reserves one word per category and distributes the
remaining \(R-K\) words by largest remainder, with table-position tie breaking:

\[
h_i=1+\lfloor(R-K)p_i\rfloor
 +\mathbf 1\{i\text{ receives a remainder seat}\},
\qquad q_i=\frac{h_i}{R}.
\]

Thus every positive category remains represented and \(\sum_i h_i=R\). The
manifest records each exact quota/cumulative table and the reduced exact
target-to-dyadic TV, \(\frac12\sum_i|p_i-q_i|\).

For coordinate word \(w\), the runtime-specific transform is

\[
j=w\mathbin{\texttt{>>}}11,
\quad r=\min(j,2^{53}-1-j),
\quad u_r=\frac{2r+1}{2^{54}},
\]

followed by lower-tail SciPy `ndtri` and exact sign reflection. The midpoint is
strictly inside \((0,1/2)\); the output must be finite, nonzero, normal
binary64. Under a uniform uint64 word, the finite coordinate codebook law is

\[
\Gamma_{\mathrm{rt}}
=2^{-53}\sum_{j=0}^{2^{53}-1}\delta_{z(j)}.
\]

The lower eleven raw bits are ignored, but their words and offsets remain in
the exact parent transcript.

The strongest distributional statement is explicitly counterfactual. If all
\(L\) words were mutually independent and uniform on the uint64 domain, then

\[
\nu_{\mathrm{fin}}(d,\mathrm d r)
=q_d^T\Gamma_{\mathrm{rt}}^{\otimes k_d}(\mathrm d r),
\qquad
Q_{\mathrm{fin}}
=\sum_{n=0}^{N}q_n^C
  (\Sigma_n)_\#(\nu_{\mathrm{fin}}^{\otimes n}),
\]

where \(\Sigma_n\) is canonical stable sorting. For canonical finite-support
\(x\), with \(m_e\) copies of each distinct event \(e\),

\[
Q_{\mathrm{fin}}\{x\}
=q_{|x|}^C\frac{|x|!}{\prod_e m_e!}
  \prod_{e\in x}\nu_{\mathrm{fin}}\{e\}.
\]

Actual Philox words are deterministic procedural values only: this checkpoint
certifies no uniformity, independence, physical randomness, or empirical
sampling claim. The finite coordinate marginal and a Gaussian have TV one.
Whenever a positive-dimensional configuration sector has positive mass under
both laws, their conditional laws on that sector are mutually singular.
Unconditional full-configuration TV is **not generally one**, because empty
and zero-dimensional configurations can overlap. If all
types have positive dimension, then

\[
\operatorname{TV}(Q_{\mathrm{fin}},P_{\mathrm{ref}})
=1-\min(q_0,p_0).
\]

No quantitative weak or Wasserstein bound is certified. Exact-rational work
is preflighted at 131,072 bits per integer and 16,777,216 aggregate bits;
large ratio integers use canonical hexadecimal digest projections rather than
unbounded decimal conversion.

This checkpoint implements no enumeration, rejection, or SIR semantics and no
conditional, tilted, posterior, or accepted initializer law. It supplies no
accepted-configuration lineage mapping or tag-3 coordination. Test 28 remains
**OPEN** because the cumulative stack has only scoped all-atomic enumeration
and finite-rejection precursors; a complete general initializer law, SIR
semantics, conditional/tilted initializer admission and its benchmark beyond
the completed fixed-grid diagnostic, and accepted-configuration lineage/tag-3
coordination remain absent. Test 29 remains open and unchanged, Test 30
remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. The source and tests
are frozen at
`69a05b843b32b542e6a3d291d7fa55e3d79fbde46bc394cc010637ce18f2bde4`
and
`8df4e6078e948a17f6ba2fb7fe8c82f8a05201fa73b3be8ac48911d48f1ec026`.
The focused suite passed 58/58 in 259.68 seconds of pytest time (260.30
seconds external wall time), and a fresh exact checkpoint-twenty-seven parent
regression passed 76/76 in 214.96 seconds of pytest time (215.54 seconds
external wall time). Independent final reviews report P0=P1=P2=0. No claim or
confirmatory or model-quality result is promoted.

Checkpoint twenty-nine adds the **one-shot finite reference-transform
engineering diagnostic** over the exact checkpoint-twenty-eight owners. Its
[sealed preregistration](plugin_bridge_counter_keyed_reference_initializer_diagnostic_preregistration.md)
froze two deterministic address grids of 16,384 rows, five exact discrepancy
families, counterfactual product-uniform envelopes, all implementation and
runtime identities, and a no-search/no-exclusion/no-retry decision rule before
any production word was read. The sole attempt ended with terminal status
`PASS`; its detailed
execution audit
has disposition **PASS WITH EXPLICIT SCOPE LIMITS**. Independent standard-
library-only scientific recomputation and a separate custody audit each report
P0=P1=P2=0.

The exact permitted result sentence is:

> On the frozen deterministic address grid, all prespecified empirical
> discrepancies fell within the preregistered envelopes derived under the
> hypothetical product-uniform reference model.

This checkpoint supplies only nonconfirmatory engineering evidence. It
certifies no Philox uniformity, independence, randomness, or unseen-address
behavior; no \(Q_{\mathrm{fin}}\) sampling law; no continuous capped-Poisson or
Gaussian reference law; no conditional or tilted initialization; no general
initializer admission; and no sampler correctness. No Gaussian TV experiment
was run because the finite codebook and continuous Gaussian fiber have TV one
analytically on a positive-dimensional realized type. Formal Test 28 remains
**OPEN**, Formal Test 29 remains **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No claim or confirmatory result slot is
promoted.

The following paragraphs resume the intended **analytic-method design**. They
state obligations for the analytic target and a future sampling layer; they
are not consequences of checkpoints eighteen through thirty-nine. In
particular,
\(\Psi_{u,m}^{\phi,\theta}\) below must not be identified with
\(\Phi_{\mathbb Q}^{\mathrm{op}}\) without a separate target-preservation
theorem. Checkpoint eighteen certifies only the latter's operational-surrogate
rate domination, and checkpoint nineteen certifies only the scoped local
wait/route/represented-ratio sequence built on that domination. Checkpoint
twenty certifies only bounded successful-return coordination of those local
records with fail-closed cap semantics. Checkpoint twenty-one certifies only
same-runtime replay custody for concrete route records. Checkpoint twenty-two
certifies only their ordered integration into one returned bounded-loop RNG
transcript. Checkpoint twenty-three certifies only the standalone direct
namespace and deterministic post-hoc lineage overlay just defined; it does not
alter or re-execute that transcript with per-proposal keys.
Checkpoint twenty-four certifies only its new tag-6 operational-epoch execution
and integrated finite-resolution custody. It does not alter checkpoint twenty-
two, consume checkpoint twenty-three's tag-1 proposal receipts, or implement
the remaining analytic-method sampler obligations.
Checkpoint twenty-five certifies only bounded bootstrap tag-3 raw-prefix
custody. It does not supply the global initializer-control domain or transform
those words into any initializer output law.
Checkpoint twenty-six certifies only the addressable tag-7 namespace and
bounded raw-prefix custody. It does not supply global-control semantics,
initializer transforms, tag-3 coordination, or any initializer output law.
Checkpoint twenty-seven certifies only fixed strategy/stage allocation,
multiblock work-item coordinates, complete prefix materialization, and parent
replay. It does not interpret a word or supply any initializer output law.
Checkpoint twenty-eight certifies only one bounded reference-strategy finite
transform and its hypothetical product-uniform pushforward. It does not admit
a general conditional initializer or alter any path-law obligation.
Checkpoint twenty-nine evaluates only that fixed transform on its frozen grid;
its counterfactual-envelope pass does not alter analytic-target, initializer-
admission, or path-law obligations.
Checkpoint thirty certifies only the deterministic guide-plus-residual
time-zero operational log factor over the selected \(\Pi_N\) base, with exact
represented-value addition and one final binary64 rounding. It excludes the
base energy and observation-only nuisance and supplies no exponentiation,
normalization, enumeration, selection, RNG, initialized configuration, or
path-law result.
Checkpoint thirty-one certifies only exact bounded all-atomic support
enumeration, represented-parameter base coefficients, their completeness
normalizer witness, and one replay-validated checkpoint-thirty point per
state. It supplies no normalized mass, factor exponentiation, tilted
normalization, selection, RNG, initializer-protocol binding, continuous
codebook, initialized configuration, or path-law result.
Checkpoint thirty-two certifies only deterministic preparation of a positive
finite-resolution approximation to the all-atomic operational tilted law and
lookup from one explicit uint64 word. It does not acquire or certify that
word, bind checkpoint twenty-seven stage 0, admit an initializer, cover mixed
or continuous support, or alter any path-law obligation.
Checkpoint thirty-three certifies only the exact binding of one checkpoint-
twenty-seven enumeration-stage tag-7 word to one caller-supplied, replayed
checkpoint-thirty-two preparation and selector. Its distributional shorthand
is counterfactual: for fixed preparation \(p\), replace the deterministic live
word by an abstract \(U\sim\operatorname{Unif}\{0,\ldots,2^{64}-1\}\), not by
reinterpreting the live word as random. Then the fixed lookup \(f_p(U)\) has
the existing dyadic law \(Q_p\). It does not certify a live word law, sample
the ideal operational law exactly, admit an initializer, cover mixed or
continuous support, or alter any path-law obligation.
Checkpoint thirty-four internally fixes checkpoint-thirty-one enumeration and
checkpoint-thirty-two preparation before exposing its two-integer live
construction call. It certifies a valid bounded all-atomic configuration as an
initial state and exact same-address deterministic replay. Its only positive
output/pushforward-law statement is the same abstract replacement theorem
\(f_p(U)\sim Q_p\). At a fixed live address both the checkpoint-thirty-three
word and the constructed configuration are deterministic point masses.
Consequently it does not certify a live initializer distribution or initializer
admission; its historical module name does not change that disposition.
Checkpoint thirty-five composes checkpoint twenty-eight's complete finite
reference capsule at fixed initialization index zero with the reverse-time-
zero reference intensity, checkpoint twenty-three bootstrap lineage, and
checkpoint twenty-five occurrence-local tag-3 prefixes. Its public live call
is only `initialize(run_id)`, and a repeated fixed-run call is deterministic
replay rather than a fresh draw. For a fixed manifest \(m\), complete capsule
budget \(L_m\), and deterministic CP28 transform \(F_m\), only the separate
counterfactual substitution

\[
U=(U_0,\ldots,U_{L_m-1}),\qquad
U_\ell\overset{\mathrm{iid}}{\sim}
\operatorname{Unif}\{0,\ldots,2^{64}-1\}
\]

gives \(F_m(U)\sim Q_{\mathrm{fin},m}\). This statement covers only the
configuration component, not the live tag-7 words, tag-3 transcript, lineage,
or complete returned record. With exact count/type discrepancies \(\delta_N\)
and \(\delta_A\), its structural projection satisfies only the upper bound

\[
\operatorname{TV}_{\mathrm{struct}}
\le\min\!\left\{1,\delta_N+
\sum_{n=0}^{N}p_N(n)\left[1-(1-\delta_A)^n\right]\right\},
\]

not an equality. Conditional on a common positive-probability structural cell
with positive active coordinate dimension, the finite CP28 codebook and the
analytic Gaussian fiber have TV one. Canonical position \(j\) maps to bootstrap
serial \(j+1\), and its tag-3 prefix has length \(\max(1,d_j)\). The tag-3
counter is \((0,0,j+1,0)\); because it omits initialization index, this fixed-
zero construction establishes no cross-initialization disjointness. The
checkpoint closes lineage/tag-3 coordination only for this finite reference
constructor. It supplies no live randomness law, Gaussian/capped-Poisson law,
conditional/tilted/rejection/SIR/general initializer admission, Brownian
coupling, path, or sampler result.

Checkpoint thirty-six binds checkpoint twenty-eight's finite proposal transform
and checkpoint thirty's deterministic point score inside checkpoint twenty-
seven's fixed rejection stage. Fix an attempt budget \(A\), let \(B\) be CP28's
reference-block count, and let \(L\) be its complete proposal-word count. Each
attempt has the exact CP28 layout followed by one reserved one-word block, so
the parent materializes \(A(B+1)\) records and \(A(L+1)\) words. The fixed
resource rule is

\[
A\le\min\!\left\{
64,
\left\lfloor\frac{64}{B+1}\right\rfloor,
\left\lfloor\frac{65536}{L+1}\right\rfloor
\right\}.
\]

CP36 materializes and validates every CP28 slot's transformed fields before
count decode, then constructs and validates the final activity-bearing slot
records and the exact duplicate-stable canonical candidate. It obtains CP30's
exact represented rational score \(q\) and records the reduced exact witness
\(q-U\le0\) for the frozen global rational upper bound \(U\). For attempt
\(a\), block \(b\), and separate word offset \(o\), the live address is key
`(run_id, 7)`, counter
`(0, initialization_index, 1, a*(B+1)+b)`, offset \(o\). The final block
\(b=B\) is retained but uninterpreted.

The sole probabilistic statement is conditional on a separate abstract iid-
uniform uint64 variable for every distinct full logical coordinate. It
totalizes the deterministic abstract operation into
`Success(abstract preparation batch)` disjoint-unioned with `Failure`, because
materialization or scoring can fail, and gives only

\[
\operatorname{TV}(F_{\#}\nu,F_{\#}U)
\le\operatorname{TV}(\nu,U).
\]

Any source-plus-algorithm triangle ledger requires a separately proved source
approximation. CP36 supplies no failure probability, no law conditional on
success, and no live Philox uniformity, independence, or randomness. It makes
no decision, acceptance, exponentiation, selection, success/exhaustion,
initializer-law or admission, lineage/tag-3, Brownian, drift, path, liveness,
or sampler claim.

Checkpoint thirty-seven consumes only a successfully validated CP36 batch. For
each exact dyadic gap \(\delta_a=q_a-U\le0\), it certifies

\[
D=2^{64},\qquad K_a=\left\lfloor D e^{\delta_a}\right\rfloor,
\qquad A_a=\mathbf 1\{w_a<K_a\}.
\]

All \(K_a\) values are constructed before the first word-to-quota comparison.
Threshold construction may inspect each already materialized reserved word for
exact type and uint64 range, but the word does not determine its quota and is
not decision-compared until the complete threshold tuple exists. Decisions
then form a prefix ending at the first acceptance; that attempt's exact CP36
configuration is selected. If every attempt rejects, the result is bounded
`exhausted`. Validation or numerical-certification failure raises and returns
no result rather than exhaustion. A suffix after early selection remains
materialized by CP36 but has no CP37 decision records.

The exact quota branches are \(K=D\) at \(\delta=0\), \(K=0\) for
\(\delta\le-64\), \(K=D-1\) for \(-D^{-1}<\delta<0\), and an adaptive
192/384/768/1536/3072-digit Decimal enclosure otherwise. They certify

\[
0\le e^{\delta_a}-K_a/D<D^{-1}.
\]

For fixed proposal/score data excluding the realized words and a separate
abstract iid-uniform uint64 family, \(p_a=K_a/D\) gives

\[
\Pr(J=j)=p_j\prod_{i<j}(1-p_i),\qquad
\Pr(\mathrm{Exhausted})=\prod_i(1-p_i).
\]

For the corresponding fixed-data comparison between independent-coordinate
ideal and dyadic Bernoulli sequences, a common-uniform coupling gives a strict
\(A/D\) total-variation bound between their finite outcome laws.
These formulas do not condition on the complete CP36 record, which contains the
realized words, and are not a live Philox law, exact ideal-rejection theorem,
success-conditional CP36 law, normalized tilted initializer, admission rule,
lineage/tag-3 mapping, path, or sampler claim. The fixed-address live operation
is deterministic replay.

Checkpoint thirty-eight calls CP37 once and materializes the complete exact
counterfactual law conditional on the direct word-free projection

\[
B=\bigl((j,x_j,\delta_j,K_j)\bigr)_{j=0}^{A-1}.
\]

This projection includes each canonical candidate, exact score gap, and
conservative quota while excluding every reserved decision word, decision,
realized outcome, and parent digest that indirectly binds those words. Under a
separate abstract iid-uniform uint64 family independent of \(B\), with
\(p_j=K_j/2^{64}\), CP38 records

\[
\alpha_j
=p_j\prod_{i<j}(1-p_i),\qquad
e_B=\prod_{i=0}^{A-1}(1-p_i),\qquad
\sum_j\alpha_j+e_B=1.
\]

It stably aggregates structurally equal configurations as

\[
m_B(x)=\sum_{j:x_j=x}\alpha_j,\qquad
Z_B=\sum_xm_B(x)=1-e_B.
\]

The selected-configuration law \(m_B(x)/Z_B\) is defined exactly when
\(Z_B>0\). If every quota is zero, then \(Z_B=0\), exhaustion has mass one,
and all optional selected-conditioned probability values are absent, while
the corresponding definition flags remain present and false.

Separately, independent continuous common uniforms couple the ideal
\(e^{\delta_j}\) and dyadic \(p_j\) Bernoulli sequences. Data processing
through the first-selected-configuration-or-exhaustion map gives the strict
augmented comparison

\[
\operatorname{TV}\!\left(
  \mathcal L_B(X_{\mathrm{dyadic}}\sqcup E),
  \mathcal L_B(X_{\mathrm{ideal}}\sqcup E)
\right)<\frac{A}{2^{64}}.
\]

This fixed-\(B\) bound is unconditioned over selection versus exhaustion and is
not directly reused unchanged by CP38 after conditioning on selection. CP38
supplies no live Philox law, CP36 failure or successful-batch distribution,
generic initializer admission, or normalized analytic target. Its live result
is deterministic replay. A
selected configuration is certified only as structurally valid for one
operational initial state. Lineage/tag-3 attachment remains absent because the
current namespace does not distinguish every initialization index under one
run. The direct projection digest is explicitly framed and streamed under the
64-attempt, 64-event-per-configuration, and 65,536-coordinate-per-event caps.

Checkpoint thirty-nine invokes the exact CP38 `resolve` once at run \(r\) and
initialization index \(i\). Bounded exhaustion remains a valid no-state result.
If CP38 instead selects exact CP37 attempt \(a\) and exact canonical
configuration

\[
x=(e_0,\ldots,e_{n-1}),
\]

CP39 retains the configuration by object identity and the attempt index by
exact integer value, then queries the process-owned reference intensity at
reverse time zero,

\[
I_0(x)
=\operatorname{PreflightReferenceIntensity}(x,\text{reverse\_time}=0),
\]

and asks the exact CP23 owner to construct positional bootstrap lineage.
Canonical position \(j\) maps to serial \(s_j=j+1\), origin initialization
\(i\), and origin position \(j\). Structurally equal duplicate events remain
distinct occurrences. The selected attempt is the actual CP37 attempt, not a
CP38 duplicate-aggregation representative or ordinal.

For checkpoint-twenty-eight manifest dimension \(d_j\), CP39 assigns the
positive local word count and direct tag-3 address

\[
N_j=\max(1,d_j),\qquad
\operatorname{key}=(r,3),\qquad
\operatorname{counter}=(0,i,s_j,a+1).
\]

The initialization index, positional lineage serial, and positive selected-
attempt suffix are direct unhashed address limbs. The layout is injective over
the declared \((i,s_j,a)\) tuple and is disjoint from valid legacy tag-3
initializer addresses whose final counter limb is zero. This is only a local
address-layout claim. It gives no global run-ID uniqueness, address one-shot
use, cross-bootstrap merge safety, lineage-fork prevention, or statistical
independence. CP39 uses its own address and stream DTOs; it neither forges a
CP23 address DTO nor invokes CP25 initializer-stream consumption.

Each occurrence stream binds its exact address, initial and final Philox
snapshots, exactly \(N_j\) raw64 words, no upper-counter carry, and same-runtime
deterministic replay. The words are uninterpreted shape metadata. They do not
generate, alter, decode, or semantically explain the already selected event or
its coordinates.

A selected empty configuration remains selected: it retains the exact empty
configuration, reverse-time-zero intensity, and a present empty lineage state,
with no local stream. Exhaustion instead retains no selected attempt,
configuration, intensity, lineage, address, stream, occurrence, or prefix. Its
branch invokes no selected-branch composer preflight, CP23 bootstrap, or CP39
result address/stream/occurrence construction. Certification and live-binding
Philox probes are separate procedural checks and may still execute. Parent
failure is not relabeled as exhaustion.

Validation does not call CP38 `resolve`, CP23 bootstrap, or CP39 child
constructors. It does replay-validate the stored CP38 parent, recompute the
deterministic composer preflight through intensity validation, validate stored
lineage without bootstrapping, and replay every stored selected-branch stream.
The resource limits are 64 occurrence records, 4,096 raw64 words per
occurrence, and 65,536 raw64 words in aggregate.

Same-address behavior is deterministic replay, not a fresh draw. CP39 supplies
no Philox law, randomness or independence theorem, cryptographic guarantee,
cross-runtime portability guarantee, tag-3 payload semantics, coordinate-
generation law, live
initializer distribution, generic initializer admission, selected-conditioned
reuse of CP38's ideal/dyadic comparison, normalized global tilted law, Brownian
consumption, continuous drift, path, liveness, or sampler. Its final
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

Checkpoint forty accepts one exact checkpoint-thirty-nine owner and invokes
its `coordinate(r,i)` operation exactly once. From the embedded checkpoint-
thirty-eight direct word-free successful batch

\[
B=\bigl((j,x_j,\delta_j,K_j)\bigr)_{j=0}^{A-1},
\qquad D=2^{64},\qquad p_j=K_j/D,
\]

it names the exact finite-resolution augmented target

\[
Q_B^{\mathrm{aug}}
=\sum_xm_B(x)\delta_x+e_B\delta_{\bot_E},
\quad
m_B(x)=\sum_{j:x_j=x}p_j\prod_{k<j}(1-p_k),
\quad
e_B=\prod_j(1-p_j).
\]

This target always normalizes. With \(Z_B=1-e_B\), the selected-state target

\[
Q_B^{\mathrm{sel}}(x)=\frac{m_B(x)}{Z_B}
\]

is defined if and only if \(Z_B>0\). At \(Z_B=0\), exhaustion has mass one and
the selected-conditioned target is undefined. Its optional probability and
comparison-bound values are absent and its definition, strictness, and
nonvacuity flags are false; fixed comparison/proof metadata remains present.

For ideal attempt probabilities \(r_j=e^{\delta_j}\), conservative quotas give
\(p_j\le r_j\), so ideal selection mass \(Z_B^\star\ge Z_B\). Conditioning
stability and checkpoint thirty-eight's strict augmented comparison yield

\[
\operatorname{TV}(P_B^{\mathrm{sel}},Q_B^{\mathrm{sel}})
\le
\frac{2\operatorname{TV}(P_B^{\mathrm{aug}},Q_B^{\mathrm{aug}})}
     {\min(Z_B^\star,Z_B)}
<\frac{2A}{D Z_B}
\qquad (Z_B>0).
\]

The exact rational \(2A/(DZ_B)\) is recorded as a strict upper bound. Its
clipping (min\{1,2A/(DZ_B)\}) is recorded only as a non-strict display
bound, nonvacuous exactly when the raw rational is strictly below one. At
equality the raw strict theorem remains informative even though the clipped
non-strict display is vacuous.

If CP39 selects, including selected-empty, checkpoint forty retains the exact
configuration, intensity, lineage, and occurrence payloads by identity and
admits the state only through this declared fixed-\(B\) downstream structural
boundary. The checkpoint-thirty-eight selected configuration ordinal chooses
the target mass row, but that row is a mass witness only: its stable duplicate
representative never replaces the actual selected CP39 object. If CP39 is
exhausted, the finite-resolution target remains present but every state,
intensity, lineage, occurrence, and stream field is absent. Parent,
validation, or construction failure returns no checkpoint-forty record and is
never relabelled as exhaustion.

The target is conditional on one successfully materialized checkpoint-thirty-
six batch and checkpoint thirty-eight's separate abstract iid decision-word
premise. The live fixed-address result is deterministic replay, not a draw from
the target. Checkpoint forty supplies no live or unconditional initializer law,
checkpoint-thirty-six failure law, exact ideal rejection, normalized global
tilt, all-strategy general initializer, tag-3 payload or coordinate semantics,
Brownian consumption, drift, path, liveness, or sampler. Its focused suite
passed 45/45, inherited exact-hash CP39 parent evidence remains applicable,
and its disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

Together with Sections 4.3 and 7.1,

\[
\operatorname{osc}_{y}\Psi_{u,m}^{\phi,\theta}
\le D_\Psi(a,m,z)
:=2B_V+\log\!\frac{H_m(a,z)}{\epsilon_m}+2B_R.
\]

Hence every tilted jump kernel has finite total rate bounded by

\[
\bar q_{u,m}^{\phi,\theta,a}
\bigl(y,\Gamma_{\le N}\setminus\{y\}\bigr)
\le e^{D_\Psi(a,m,z)}\Lambda_{S-u}^0(y).
\]

That display is a real-arithmetic domination statement. The executable
waiting clock uses an outward-rounded operational value

\[
E_\Psi^{\mathrm{op}}(u,y;a,m,z)
\ge e^{D_\Psi(a,m,z)}\Lambda_{S-u}^0(y),
\]

computed by a staged certified routine. For a reference-kernel proposal
\(Y\), define the actual represented tilted integrand

\[
I_\Psi^{\mathrm{op}}(u,y,Y)
=\Lambda_{S-u}^0(y)
\exp\{\Psi_{u,m}^{\phi,\theta}(Y;a,z)
-\Psi_{u,m}^{\phi,\theta}(y;a,z)\}.
\]

The implementation acceptance probability is the checked ratio

\[
p_{\mathrm{acc}}
=I_\Psi^{\mathrm{op}}/E_\Psi^{\mathrm{op}}\in(0,1].
\]

It must not be replaced by
\(\exp\{\Psi(Y)-\Psi(y)-D_\Psi\}\) unless the implementation has separately
proved exact equality between the operational envelope and the corresponding
real-arithmetic product. Outward rounding can make that equality false.
Checkpoint nineteen supplies a separately audited variable-word exact
Bernoulli only for checkpoint eighteen's represented operational-surrogate
quotient and successful local custody chain. A future analytic or full sampler
must bind its own matching represented quotient to that construction or refuse
probabilities below its frozen RNG resolution; one ordinary 53-bit uniform draw
is not an exact Bernoulli for every positive binary64 probability.

The same certificate supplies the continuous-destination rejection envelope
used in Section 8.2. Sampler admission requires finite first and second
coordinate-derivative certificates for all three physical components:
\(V_\phi\), \(\log\widetilde h\), and
\(a_R(u)\mathcal C_{B_R}(F_\theta)\). These make the controlled drift locally
Lipschitz with linear growth. Failure to construct any one of these
certificates blocks the sample; it is never repaired by clipping a potential
or rate.

## 8. Conditional initializer and numerical sampler

### 8.1 Initial tilt

For a general candidate base initial law \(\rho_0^\phi\), the plug-in
conditional initial law is

\[
\widehat\rho_0^a(dy)
=\frac{\rho_0^\phi(dy)\widehat h_{0,m}^{\phi,\theta}(y;a,z)}
{\int\rho_0^\phi(dv)\widehat h_{0,m}^{\phi,\theta}(v;a,z)},
\qquad \rho_0^\phi=\Pi_N
\quad\text{in the selected implementation}.
\]

Checkpoint thirty freezes only the selected implementation's deterministic
time-zero **operational point factor**. Let \(\iota(v)\) denote the exact
rational represented by a finite binary64 value. For canonical configuration
\(x\), explicit residual context \(c\), reverse time \(u=0\), and direct time
\(s=S\), write
\(L_{\mathrm{init}}^{\mathrm{op}}\equiv
\log\widehat h_0^{\mathrm{op}}\) for the log-factor identifier. This notation
does not construct the exponentiated factor. The composer computes

\[
L_{\mathrm{init},\mathbb Q}^{\mathrm{op}}(x;c)
=\iota\!\left(G_{64}^{\mathrm{totalized}}(0,x)\right)
+\iota\!\left(R_{64}^{\mathrm{totalized}}(S,x,c)\right),
\qquad
L_{\mathrm{init},64}^{\mathrm{op}}(x;c)
=\operatorname{RN}_{64}\!\left(
L_{\mathrm{init},\mathbb Q}^{\mathrm{op}}(x;c)\right),
\]

where \(\operatorname{RN}_{64}\) is round to nearest, ties to even. The two
represented component values are lifted with exact `Fraction` arithmetic,
summed exactly, and rounded only once at the aggregate. The returned record
also carries the outward interval

\[
\left[
\operatorname{rd}_{\downarrow}(\ell_G-B_R),
\operatorname{rd}_{\uparrow}(u_G+B_R)
\right].
\]

The learned base energy \(V_\phi(S,x)\) is excluded: the selected base law is
already \(\Pi_N\), so this extra operational log factor contains only the
totalized guide and residual. A separate observation-only nuisance input is
also excluded. The residual context \(c\) remains explicit, and its
conditioning-adapter origin is not authenticated. These are target/API facts,
not a causal nuisance-isolation result. The process-local owner identities in
the certificate are procedural custody witnesses; its hashes are not
cross-run semantic-reproducibility identifiers or cryptographic attestations.

Checkpoint thirty does not itself exponentiate or normalize the point factor,
enumerate a support, select a state, consume randomness, return an initialized
configuration, or establish the analytic conditional/posterior target.

Checkpoint thirty-one implements the next dependency only on a bounded
**all-atomic** process-owned reference. Let the reference type identifiers
\((d_1,\ldots,d_K)\) be increasing and define the exact represented parameters

\[
a=\iota(\vartheta_{64}),\qquad
r_j=\iota(w_{d_j,64}),\qquad
R=\sum_{k=1}^K r_k,\qquad
p_j=\frac{r_j}{R}.
\]

For the canonical count-vector support

\[
\mathcal M_{K,N}=\{m\in\mathbb N_0^K:|m|\le N\},
\]

ordered by increasing cardinality and then lexicographically, the enumerator
stores the exact unnormalized represented-parameter coefficient

\[
b_{\mathbb Q}(m)
=a^{|m|}\prod_{j=1}^K\frac{p_j^{m_j}}{m_j!}.
\]

There is no additional \(|m|!\) factor. The exact renormalization
\(p_j=r_j/R\), rather than the unnormalized stored weights or separately
rounded intensities, is part of the implemented law. The implementation
checks

\[
b_{\mathbb Q}(m+e_j)
=b_{\mathbb Q}(m)\frac{a p_j}{m_j+1},\qquad
\sum_{|m|=n}b_{\mathbb Q}(m)=\frac{a^n}{n!},
\]

and

\[
\sum_{m\in\mathcal M_{K,N}}b_{\mathbb Q}(m)
=Z_N(a):=\sum_{n=0}^N\frac{a^n}{n!}.
\]

The result stores \(Z_N(a)\) only as a completeness witness; it does not
materialize the normalized masses \(b_{\mathbb Q}(m)/Z_N(a)\). One
checkpoint-thirty point evaluation is attached to and replay-validated for
every state only after the complete support and exact coefficients pass
preflight.

The admitted boundary is \(1\le K\le64\), \(0\le N\le255\),
\(\binom{N+K}{K}\le256\) states,
\(K\binom{N+K}{K+1}\le32{,}640\) emitted occurrences, at most 8,192 bits for
each exact numerator or denominator, and at most 8,388,608 under the defined
aggregate exact-rational bit witness, which counts each conceptual rational in
the frozen formula once rather than bounding Python memory. Every reference
dimension must be zero; any mixed or continuous
reference is refused in full, even when \(N=0\). Checkpoint twenty-eight's
finite coordinate codebook is not admitted because it is singular with
respect to a positive-dimensional continuous Gaussian reference.

Checkpoint thirty-one still does not exponentiate the point factor, combine
it into tilted weights, normalize a tilted law, select a state, perform
rejection or SIR, consume RNG, bind checkpoint twenty-seven stage 0, return an
initialized configuration, or establish the analytic conditional/posterior
target. Thus it does not implement the displayed law
\(\widehat\rho_0^a\), and Test 28 remains **OPEN**. A later selector must
either label a dyadic approximation explicitly or use a separately certified
variable-bit construction for a generally non-dyadic target.

Checkpoint thirty-two implements the labelled dyadic alternative only for a
successful checkpoint-thirty-one all-atomic result. For its exact coefficient
\(b_i\) and checkpoint-thirty exact represented-component sum \(q_i\), define

\[
P_i=\frac{b_i e^{q_i}}{\sum_k b_k e^{q_k}}.
\]

With \(q_\star=\max_iq_i\), adaptive directed Decimal intervals enclose
\(b_i e^{q_i-q_\star}\) at precisions 192, 384, 768, and 1536. Exact interval
normalization gives \(L_i\le P_i\le U_i\). Exact midpoint weights define a
positive rational proxy \(\widetilde P\), with

\[
\varepsilon_{\mathrm{ip}}
=\frac12\sum_i
\max\{\widetilde P_i-L_i,U_i-\widetilde P_i\}
\le2^{-96}.
\]

For \(M\le256\) states and \(D=2^{64}\), one quota is reserved per state and
Hamilton apportionment distributes the remaining \(D-M\) units according to
\(\widetilde P\), with exact fractional remainders and canonical ordinal ties.
This gives \(Q_i=h_i/D>0\), \(\sum_i h_i=D\), and the exact certificate

\[
\operatorname{TV}(P,Q)
\le\varepsilon_{\mathrm{ip}}
+\operatorname{TV}(\widetilde P,Q)
\le2^{-48}.
\]

An explicit exact Python integer \(w\in[0,2^{64})\) selects the unique
half-open cumulative quota interval. The checkpoint uses exact \(q_i\), not
checkpoint thirty's rounded display float. It caps centered-log magnitude at
10,000, each exact integer at 131,072 bits, and the defined aggregate rational
witness at 16,777,216 bits. Excessive exact work, nonnested enclosures, or
unresolved precision fails closed.

This checkpoint neither materializes exact transcendental masses nor samples
the ideal \(P\) exactly. It treats \(w\) as explicit data and certifies no RNG,
uniformity, independence, physical randomness, or checkpoint-twenty-seven
binding. Therefore it still does not implement an admitted
\(\widehat\rho_0^a\) initializer, and Test 28 remains **OPEN**.

Checkpoint thirty-three supplies the separate protocol binding only for the
same resource-admitted all-atomic preparation. For exact unsigned run \(r\) and
initialization index \(i\), its complete checkpoint-twenty-seven request uses
the enumeration strategy, literal budget one, empty work-item block tuple, and
selection-word count one. Thus its exact plan and direct tag-7 address are

\[
P_{33}=((0,0,1),),
\qquad
K_r^G=(r,7),
\qquad
C_{i,0,0}^G=(0,i,0,0).
\]

The bridge validates the caller-supplied checkpoint-thirty-two preparation
before allocation, requires shared reference-composer, guide, and residual
ancestry across both parents, validates the sole checkpoint-twenty-seven entry,
and forwards its exact word \(w\) unchanged to the checkpoint-thirty-two
selector. It retains exact parent-result, entry, address, raw-word-tuple,
preparation, selection, selected-row, count-vector, and configuration custody.
It accepts no caller RNG, creates no second RNG or namespace, and has no retry
or fallback. The inherited parent does materialize one local Philox word, so
this is not a no-RNG checkpoint.

For a fixed checkpoint-thirty-two preparation \(p\), let \(f_p\) denote its
deterministic half-open quota lookup. Introduce a separate abstract replacement
word

\[
U\sim\operatorname{Unif}\{0,\ldots,2^{64}-1\}.
\]

Here \(U\) is explicitly not identified with the live checkpoint-thirty-three
Philox word source; their realized uint64 values may coincide.
Only under this counterfactual replacement does the selected configuration
have the exact finite-resolution law

\[
\Pr(f_p(U)=x_j)=Q_{p,j}=\frac{h_j}{2^{64}}.
\]

Separately and without the abstract-\(U\) premise, the fixed preparation
inherits

\[
\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}.
\]

At fixed live run and initialization indices the checkpoint-thirty-three word
is a deterministic function of the complete Philox address, and the live
output is therefore a point mass. The TV bound above is between the ideal
operational law and its dyadic approximation; it is not a
bound from the live point mass to \(Q_p\). The checkpoint does not certify
actual Philox uniformity, independence, or physical randomness; exact ideal-
law sampling; global one-shot address use; or an analytic conditional/posterior
target. The positive protocol-binding field is limited to this one-word
bridge. The separate initializer-admission fields remain false,
mixed/continuous support and the other three strategies remain absent, and
Test 28 remains **OPEN**.

Checkpoint thirty-four turns that fixed bridge into a factory-owned bounded
all-atomic **configuration constructor**. Certification canonically fixes the
residual context, materializes the complete checkpoint-thirty-one enumeration
and checkpoint-thirty-two dyadic preparation exactly once each, performs their
initial direct validations, and retains exact checkpoint-thirty-three,
selector, enumerator, preparation, hypothesis, and certificate custody. Later
custody checks may revalidate the fixed objects but do not rematerialize them.
The live public operation accepts only \((r,i)\). Each successful live
construction consumes exactly the one inherited stage-0 parent word and
permits no per-call context, preparation, RNG, explicit word, retry, fallback,
added namespace, or rollback.

For the factory-owned fixed preparation \(p\), its only positive
output/pushforward-law theorem remains

\[
U\sim\operatorname{Unif}\{0,\ldots,2^{64}-1\}
\quad\Longrightarrow\quad
f_p(U)\sim Q_p,
\]

where \(U\) is an abstract ideal source and is not identified with the live
checkpoint-thirty-three word source; their realized uint64 values may coincide.
A fixed live address \(((r,7),(0,i,0,0))\) deterministically
replays the same word and the same valid all-atomic configuration; it is not a
fresh draw. Thus checkpoint thirty-four certifies construction of a
configuration valid as an initial state, but not a live output law, live
initializer distribution, initializer admission, generality, actual RNG law,
mixed/continuous support, another strategy, lineage/tag-3 coordination,
Brownian coupling, drift, path, liveness, or sampler admission. The historical
`atomic_admission` module name promotes none of those claims. Formal Tests 28
and 29 remain **OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains
**NOT RUN**.

#### Checkpoint 39: selected-result positional initializer contract

Following the checkpoint-thirty-eight fixed-\(B\) law specified in Section
7.3, the checkpoint-thirty-nine contract for this subsection is exactly the
bounded construction-time map defined there. It calls CP38
`resolve(run_id, initialization_index)` once; exhaustion is a valid no-state
result with no selected-branch composer preflight, CP23 bootstrap, or CP39
child construction. Selection retains the exact CP38 configuration and exact
CP37 attempt, evaluates reverse-time-zero reference intensity, and maps
canonical position \(j\) to CP23 bootstrap serial \(j+1\) with origin
initialization index \(i\). Its CP39-local tag-3 address is key \((r,3)\),
counter \((0,i,j+1,a+1)\), and its uninterpreted prefix length is
\(\max(1,d_j)\), subject to 64 occurrence records, 4,096 words per occurrence,
and 65,536 aggregate words. A selected empty configuration retains its
intensity and present empty lineage with zero streams. Validation does not
rerun CP38 resolution, CP23 bootstrap, or CP39 child construction; composer
validation recomputes preflight and every stored stream replays
deterministically.

This contract uses CP39-local DTOs without forging a CP23 address DTO or
invoking CP25 consumption. Its positive attempt suffix is disjoint only from
valid legacy suffix-zero tag-3 addresses. It establishes no live law,
randomness, independence, payload or coordinate semantics, generic initializer
admission, selected-conditioned TV reuse, normalized global tilt, global or
one-shot/cross-bootstrap/merge/fork address safety, Brownian motion, drift,
path, liveness, sampler, cryptographic guarantee, or cross-runtime portability
guarantee. Its final disposition is **PASS WITH EXPLICIT SCOPE LIMITS**;
Formal Tests 28 and 29 remain **OPEN**, Test 30 remains
**PENDING**, and `R2-HYBRID` remains **NOT RUN**.

#### Checkpoint 40: finite-resolution rejection-target admission contract

The checkpoint-forty contract names checkpoint thirty-eight's exact augmented
dyadic law conditional on its direct word-free successful batch as the
operational finite-resolution rejection target. The target contains the
exhaustion atom and always normalizes. Its selected-state law is defined only
for positive \(Z_B\). At \(Z_B=0\), optional selected-conditioned probability
and raw/clipped numeric-bound values are absent, the corresponding definition,
strictness, and nonvacuity flags remain present and false, and fixed
comparison/proof metadata remains present.

For \(Z_B>0\), the exact raw strict ideal/dyadic selected-state upper bound is
\(2A/(2^{64}Z_B)\); the separately reported clipped value is non-strict and is
nonvacuous exactly when the raw value is below one. This scaling follows from
conditioning stability and the ideal-selection-mass ordering, not from direct
reuse of checkpoint thirty-eight's unconditioned augmented bound.

The sole live operation accepts run and initialization indices. It calls CP39
once. Selection retains the exact CP39 state and custody objects and uses the
parent's configuration ordinal only to bind a target mass row. Selected-empty
is admitted as a present structural initial state. Exhaustion retains the
target but no state. Operational failure produces no checkpoint-forty record.
Validation calls no parent coordinate/resolve, bootstrap, stream consumer, or
target/result constructor.

This is a narrow fixed-successful-batch structural state/no-state boundary. It
is not a live output law, unconditional checkpoint-thirty-six batch law, exact
ideal rejection, global normalized tilted law, SIR result, all-strategy general
initializer admission, path, or sampler. Formal Tests 28 and 29 remain
**OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**.

#### Checkpoint 41: conditional failure-aware abstract source law

Checkpoint forty-one defines an exactly normalized symbolic mixture over
preparation failure, quota-certification failure, exhaustion, and configuration
atoms under a separate product-uniform \(V/W\) source. Its premise that the
totalized live predecision map factors through \(V\) is explicit and unproved.
It materializes no fiber or numeric mass and establishes no live source or
initializer law.

#### Checkpoint 42: staged predecision reference evaluator

For fixed valid request indices \(r,j\), checkpoint forty-two implements the
partial executable operational map and subsequent decision stage

\[
G^{42}_{r,j}:D^M\rightharpoonup
\{F_{37}\}\mathbin{\dot\cup}\mathcal R,
\qquad
H^{42}:\operatorname{im}(G^{42}_{r,j})\times D^A
\longrightarrow\{F_{37},E\}\mathbin{\dot\cup}\mathcal X.
\]

The executable \(G^{42}\) signature receives only the frozen CP41
proposal/scoring tuple \(V\). On calls whose direct CP28/CP30 stages do not
refuse, its source-audited staging transforms and scores all \(A\) attempts
before quota construction and returns `ready` only after the complete quota
tuple exists. The public schema retains preparation-failure tag \(F_{36}\)
only for alignment with CP41; it is reserved, non-executable, and outside the
image of \(G^{42}\). CP28/CP30 exceptions remain operational refusals. Only an
exact CP37 quota-certification error after valid
nonpositive-dyadic-gap preflight is represented as \(F_{37}\), without a
partial row tuple.

For a ready result, \(H\) validates the complete \(W\in[D]^A\) tuple before
its first comparison and then applies the exact half-open predicate
\(w_i<K_i\) in first-success order. A modeled \(F_{37}\) passes through
without retaining or comparing \(W\), after public validation and replay of
its parent predecision record.

This construction makes decision-word noninterference executable for CP42's
own staged evaluator. Its sealed parity witness covers only one supplied
successful CP37 result. Its parity comparison is limited to the CP36/CP37
predecision/threshold projection. For custody, the witness retains and
digest-binds the full supplied CP37 result, including decision records/words
and outcome, but contains no CP42 applied-\(H^{42}\) record and asserts no
\(W\)/outcome or failure-fiber parity. CP42 does not
prove universal equivalence to live CP36/CP37 behavior, cover an executable
\(F_{36}\) branch, or discharge CP41's factorization hypothesis. The focused
run, additive boundary supplement, exact CP41 regression, static gates, and
final independent review are complete. The supplement's \(F_{37}\) case is
profiler-injected exact-exception branch evidence, not evidence that an
unchanged valid parent naturally reaches that failure. Its \(K=0\) and
\(K=2^{64}\) cases validate the pure \(H^{42}\) constructor, not public-owner
\(G^{42}/H^{42}\) endpoint integration.

#### Checkpoint 43: supplied-word reference-factorization closure

Fix valid request indices \(r,j\) and one exact certified CP42 owner/runtime.
Let \(D=2^{64}\), \([D]=\{0,\ldots,D-1\}\), and use CP41's exact ordered
partition \(V\in[D]^M\), \(W\in[D]^A\). Under the declared exact typed-error
and trusted-runtime construction contract, checkpoint forty-three defines

\[
G^{43}_{r,j}:[D]^M\longrightarrow
\{F_{36},F_{37}\}\mathbin{\dot\cup}\mathcal R,
\]
\[
H^{43}_{\mathrm{sem}}:\operatorname{im}(G^{43}_{r,j})\times[D]^A
\longrightarrow
\{F_{36},F_{37},E\}\mathbin{\dot\cup}\mathcal X,
\qquad
T^{43}_{r,j}(V,W)
=H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right).
\]

Without that contract, unexpected operational exceptions remain refusals and
the executable \(G^{43}\) is not claimed total. `evaluate_predecision`
implements the \(V\)-only \(G^{43}\) and has no decision-word argument. It
maps only exact instances of the declared CP28
`PluginBridgeCounterKeyedReferenceInitializerError` and CP30
`ConfigurationInitialTiltError` classes to \(F_{36}\); subclasses and every
other exception remain refusals. It retains CP42's exact modeled quota-
certification failure as \(F_{37}\), and otherwise returns the complete ready
result.

The mathematical \(H^{43}_{\mathrm{sem}}\) denotes the private semantic
`_apply_trusted`
kernel operating on a trusted internally produced \(G^{43}\) record. For
\(F_{36}\) or \(F_{37}\), it returns the same failure atom without inspecting,
validating, retaining, hashing, or comparing \(W\). For a ready record, it
preflights the complete exact \(W\) tuple before its first half-open
\(w_a<K_a\) comparison and then returns first selection or exhaustion.
`evaluate_and_apply` evaluates one \(G^{43}\) followed by one semantic
\(H^{43}_{\mathrm{sem}}\), so it directly realizes the displayed CP43 composite.

The separately invoked public replay facade `apply_decision_words` is not the
replay-free semantic \(H^{43}_{\mathrm{sem}}\). It first replays
\(G^{43}\) and requires the replayed digest to equal the supplied sealed
predecision record. Consequently, public \(F_{36}/F_{37}\) pass-through holds
only for deterministic, replay-stable failures. If a previously observed
failure is transient or replays to a different result, the replay facade refuses
before accessing the supplied decision-word object.

The certificate statements are deliberately narrow:
`complete_g_before_semantic_h_certified=True`,
`semantic_h43_failure_passthrough_without_w_access_certified=True`, and
`semantic_h43_full_w_preflight_before_comparison_certified=True` refer only to
the private semantic kernel. In contrast,
`public_h_replays_g_for_custody_disclosed=True`,
`separately_invoked_public_h_replay_free=False`, and
`transient_failure_public_h_passthrough_certified=False` delimit the public
replay facade. The construction-level flags are
`cp43_defined_reference_factorization_discharged_by_construction=True`,
`abstract_product_uniform_corollary_recorded_under_explicit_premises=True`,
and `construction_contract_enforced=True`. Under one fixed owner/runtime,
deterministic replay-stable total \(G^{43}\), and abstract independent product-
uniform supplied \(V,W\), the \(F_{36}\), \(F_{37}\), and ready fibers are
\(V\)-measurable and the conditional semantic kernel uses \(W\) only after
\(G^{43}\). This is a conditional finite supplied-word corollary, not a live
Philox uniformity, independence, randomness, source, or initializer law.

CP43 also binds an exact-text reviewed arithmetic argument and its domain-
separated digest. The argument uses exact binary64 dyadics with denominator
exponent at most 1074, a conservative CP30-gap numerator bound below
\(2^{2100}\), and an exact-decimal coefficient bound of at most 1383 digits,
below CP37's 16384-digit limit. Together with the inherited finite,
nonpositive-gap contract and checked terminal boundaries, the review excludes
the identified nonadaptive quota-error routes under the trusted runtime. Only
the 3072-digit adaptive floor-separation ambiguity remains unresolved. Exact
text and digest binding prevents the reviewed statement from being silently
substituted, but the statement is a reviewed mathematical argument plus
boundary tests, not a machine-checked proof. Neither a natural valid-parent
\(F_{37}\) witness nor an impossibility theorem is claimed;
`natural_f37_reachability_resolved=False`,
`natural_f37_failure_exhibited=False`, and
`natural_f37_impossibility_proved=False`.

The `closure_runtime_sha256` value fingerprints the declared semantic text,
selected CP42/CP43 Python code objects, and the interpreter/platform tuple.
Validation separately rechecks exact dependency identities and recomputes that
selected fingerprint. This is procedural same-runtime drift detection, not
authentication that the loaded process originated from frozen audited source
bytes, not a complete fingerprint of every transitive callback, and not
portable or cryptographic custody. Accordingly,
`construction_contract_enforced=True` intentionally coexists with
`loaded_code_integrity_certified=False`.

The certificate correspondingly retains
`universal_live_checkpoint36_37_failure_equivalence_certified=False`,
`checkpoint41_live_parent_factorization_discharged=False`,
`live_philox_source_law_certified=False`,
`live_uniformity_independence_or_randomness_certified=False`,
`scientific_claim_promoted=False`, `model_quality_claim_promoted=False`, and
`generality_claim_promoted=False`.

CP43 does not certify replay-free public \(H\), transient-failure public pass-
through, universal equivalence to live CP36/CP37 success or failure behavior,
discharge of CP41's live-parent factorization premise, whole-record
equivalence, a live Philox/source law, numeric fibers or masses, an initializer
distribution, general admission, a path, a sampler, scientific validity,
model quality, or framework generality.

#### Checkpoint 44: one-allocation factorized execution adapter

Fix one exact certified CP43 owner, its exact transitive CP37/CP36/CP27
ancestry, a valid request \(r,j\), inherited attempt budget \(A\), proposal-
word count \(M\), and \(D=2^{64}\). CP44 defines a new operational path that
begins with one adapter-level call to the exact CP27 `allocate` API for the
complete attempt-interleaved CP36 rejection layout. That count is an API-call
statement, not a physical single-read or replay-free source statement: CP27's
inherited allocation implementation performs its own deterministic internal
validation replay before it returns a complete validated capsule.

On successful source acquisition, chronological flattening gives

\[
Z\in[D]^{M+A}.
\]

CP44 independently reconstructs the CP36 proposal/decision layout and requires
the exact CP43 partition identities

\[
\operatorname{split}_{43}(Z)=(V,W),
\qquad V\in[D]^M,
\qquad W\in[D]^A,
\qquad
\operatorname{join}_{43}(V,W)=Z.
\]

It then calls CP43 `evaluate_and_apply` exactly once, with no second source
allocation, extra source word, caller/global RNG, retry, fallback, or rollback.
Let \(\pi\) be the canonical projection containing semantic status, comparison
count, selected-attempt index, and selected-configuration digest. For every
valid request whose call actually returns a CP44 result after one allocation
returns a complete capsule and all final structural/custody checks pass, the
executable contract is

\[
\pi\!\left(T^{44}_{r,j}(Z)\right)
=\pi\!\left(T^{43}_{r,j}(V,W)\right)
=\pi\!\left(
H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right)
\right).
\]

This is pointwise equality by construction after canonical semantic
projection, not Python-record equality. CP44 additionally retains the CP27
capsule, its entries and words, the \(V/W\) partition, source-boundary custody,
and a CP44 record digest.

Source acquisition and the initial capsule checks precede the CP43 semantic
map. An exact CP27 allocation exception propagates unchanged without a CP44
result; malformed-source, failed-preflight, and split/join refusals likewise
occur before the combined call. Repeated dependency, owner, and source-custody
checks can instead refuse after CP43 has evaluated but before CP44 returns a
result. Neither chronology produces a CP44 result, neither refusal is
\(F_{36}\) or \(F_{37}\), and CP44 assigns no probability to either class.
Only after a complete valid capsule exists can the one CP43 combined call
produce its exact post-source `preparation_failure`,
`quota_certification_failure`, `selected`, or `exhausted` status. If CP43
returns \(F_{36}\) or \(F_{37}\), CP44 may retain \(W\) as complete-capsule
boundary evidence; this does not assert that CP43's semantic failure branch
interpreted \(W\).

The separate CP44 public `validate_result` operation is structural and
nonreplaying in the operational sense. It checks exact record types, ancestry,
source-tree custody, flattening, partition identities, canonical projection,
and digests, but invokes no new CP27 allocation, CP36 `prepare`, CP37 `decide`,
CP43 \(G\), CP43 semantic \(H\), or CP43 combined evaluation. It may traverse,
hash, and deterministically reconstruct structural facts. It intentionally
does not call CP43's public applied-decision validator, because that facade
would replay \(G^{43}\).

CP44 fingerprints its selected Python code objects with explicit marshal
version 2 after a recursive exact constant-domain check. This removes false
digest drift from live reference topology while retaining sensitivity to
selected code changes. The mechanism is CP44-only procedural custody; it does
not modify CP43 or establish arbitrary-instrumentation ancestry stability,
portable attestation, or loaded-code integrity.

The new route is

\[
\text{CP27 full capsule}
\longrightarrow \operatorname{split}_{43}
\longrightarrow T^{43}_{r,j}.
\]

It bypasses CP36 `prepare` and CP37 `decide`. It therefore does not establish
their preparation-record, decision-record, failure-path, chronology, or whole-
record equivalence, and it neither discharges nor theorem-level supersedes
CP41's original live-parent factorization premise.

For one fixed certified owner/runtime, first assume that \(G^{43}_{r,j}\) is
deterministic, replay-stable, and total under CP43's declared typed-error
contract. Define the abstract successful-source semantic map

\[
S^{44}_{r,j}(Z)=T^{43}_{r,j}(\operatorname{split}_{43}(Z)).
\]

Only under that premise and the separate abstract full-word premise

\[
Z\sim\operatorname{Unif}\!\left([D]^{M+A}\right)
\]

with product measure on the exact distinct CP36-derived coordinates does the
coordinate split imply product-uniform \(V\), product-uniform \(W\), and
\(V\perp W\). Under both premises, the CP43 \(G\)-fibers yield the CP41-form
symbolic \(S^{44}\) pushforward

\[
Q_{44}(F_{36})=\phi_{36},\qquad
Q_{44}(F_{37})=\phi_{37},\qquad
Q_{44}(E)=\sum_B\lambda_B e_B,\qquad
Q_{44}(x)=\sum_B\lambda_B m_B(x).
\]

No operational source/refusal mass, fiber, or other mass is numerically
materialized. This corollary supplies no unconditional adapter law, live
CP27/Philox uniformity, independence, freshness, randomness, allocation-
success, source, or initializer law. Natural \(F_{37}\) reachability and the
terminal 3,072-digit adaptive floor-separation question remain unresolved;
the answer only determines whether the symbolic \(F_{37}\) fiber is empty and
does not affect the pointwise split-and-compose identity. CP44 admits no global
initializer, path, liveness, or sampler and promotes no scientific validity,
model quality, cross-domain evidence, framework generality, or manuscript
claim.

Final CP44 execution evidence is frozen in the linked standalone audit. The
frozen source contains `1829` lines and has SHA-256
`42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d`;
the `829`-line focused test has SHA-256
`e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.
The final no-cache, warnings-as-errors run collected **26** cases and returned
**26/26 passed** in **50165.86** seconds of pytest time and **50166.38** seconds
external wall time; pre/post source and test hashes were unchanged. There were
no failures, errors, skips, xfails, xpasses, or warnings.

Black, pyflakes, flake8 `E9,F63,F7,F82`, Python 3.9.13 and locked Python 3.11.5
syntax compilation, ASCII screening, exact collection, and the exact 16-symbol
export/signature check passed. Eighteen formatter-stable, identifier-dominated
lines exceeded 88 columns and were individually reviewed. All six exact
contract blocks occur once and byte-match the frozen source. Independent CP44
source and test audits found `P0=P1=P2=0`.

No parent suite was freshly rerun for CP44. Exact-hash inherited evidence
remains the historical CP43 **62/62 passed** record
(**12949.69/12950.26** seconds pytest/wall), CP42 primary **29/29 passed**
record (**3409.31/3409.78** seconds), and CP42 supplement **5/5 passed** record
(**1205.53/1205.98** seconds). The untouched venue-neutral Markdown and TeX
manuscripts retain SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.
The CP44 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. This freezes only
the scoped engineering record and promotes no live source, numeric-mass,
initializer/path/sampler, scientific, model-quality, cross-domain, generality,
C-row, R-slot, or manuscript claim.

#### Checkpoint 45: fixed-address source-support obstruction

Fix the exact CP44 owner and runtime, write D = 2^64, and let L be the
complete CP44 capsule length. For one exact request that returns capsule z,
inherited same-runtime deterministic replay defines the canonical live source
law as the point mass delta_z. Its exact distance from the abstract product-
uniform capsule law U_L is

```text
TV(delta_z, U_L) = 1 - D^(-L).
```

This is a returned-fixed-request statement, not an allocation-success or
unconditional adapter law.

The general CP45 contract considers a deterministic partial map from the
successful subset of at most k free uint64 coordinates into L-word capsules.
Under any request law with positive success probability, the conditional-
success pushforward q_success has support at most D^k. Hence

```text
TV(q_success, U_L) >= 1 - D^(k-L) when L > k.
```

For L <= k, the certified universal support-only lower bound is zero.
Conditioning cannot enlarge support, so the theorem requires no independence
between success and value. All external entropy-bearing coordinates must be
counted in k. The executable record accepts every exact nonnegative integer k,
stores symbolic exponent information, and uses signed-hex integer
canonicalization so hashing is independent of Python's decimal digit limit.

The bound is not transported through CP43's semantic map. Total-variation data
processing is an upper bound after a map, and a constant map is an exact
counterexample to any universal output lower bound. CP45 accordingly certifies
no semantic-output discrepancy, numeric outcome mass, or live product-uniform
law.

Certification binds exact CP44 and transitive CP36/CP27/CP26 ancestry and
inherits CP44's guarded CP43 coordinate partition. Sealed certificate and
bound records, exact owner identities, local theorem/digest helpers, parent
callbacks, guard aliases, and construction tokens fail closed under the
tested replacement attacks. Bound construction and validation invoke no CP27
allocation and no CP43/CP44 semantics. Caller/global RNG states are unchanged,
but inherited validation may execute a deterministic local Philox runtime
probe; zero transitive RNG calls, loaded-code integrity, portability, and
cryptographic authentication are explicitly not certified.

Final source-independent, static, hostile-audit, and full focused evidence is
recorded in the linked
[CP45 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md)
after an authoritative 20/20 warnings-as-errors pass in `19448.25 s`
(`5:24:08`). The source/test hashes and post-run static gates remained
unchanged, the final independent severity count is `P0=P1=P2=0`, and the
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. CP45 supplies no refusal
probability, natural \(F_{37}\) resolution, live V/W independence, physical
randomness,
freshness, initializer/path/sampler admission, empirical/model-quality result,
cross-domain generality, C-row, R-slot, or manuscript claim.

#### Checkpoint 46: explicit fixed and external source-model contract

Checkpoint forty-six binds one exact CP45 owner and separates two source
descriptors that must not be conflated. Let \(D=2^{64}\), let \(L\) be the
complete CP44 capsule length, and inherit CP45's certified \(L>2\).

The **fixed-request replay model** contains one exact pair
\((r,j)\in[D]^2\). The request is deterministic, not sampled. Conditional on a
named event \(\mathcal A\) having positive mass, its symbolic capsule law is a
point mass and

\[
\nu_{\mathcal A}=\delta_{z(r,j)},
\qquad
\operatorname{TV}(\nu_{\mathcal A},U_L)=1-D^{-L}.
\]

The descriptor neither executes the request nor materializes \(z(r,j)\).
Deterministic replay does not certify cross-call freshness or nondegenerate
independence; degenerate constant-factor independence is not promoted into
either claim.

The distinct **external finite request-law model** accepts a canonical finite
exact-rational PMF \(\mu\) over the two uint64 request coordinates. It is a
declaration, not a sampler or evidence that a caller realizes \(\mu\). If
\(s=\lvert\operatorname{supp}\mu\rvert\) and \(F\) is any deterministic
partial request-to-\(L\)-word-capsule map, then for every named conditioning
event \(\mathcal A\) with positive \(\mu\)-mass,

\[
\bigl\lvert\operatorname{supp}\bigl(F_\#
  \mu(\,\cdot\mid\mathcal A)\bigr)\bigr\rvert\le s,
\qquad
\operatorname{TV}\!\left(F_\#\mu(\,\cdot\mid\mathcal A),U_L\right)
\ge 1-\frac{s}{D^L}.
\]

No success/value-independence premise is needed: conditioning can change
weights and induce dependence but cannot enlarge support. The
complete-validated-capsule acquisition event and the CP44 returned-result
event are separate public identifiers. Positive event mass is a theorem
premise and is explicitly not certified; therefore CP46 instantiates no
conditional capsule law and supplies no numeric acquisition, return, or
refusal probability.

The executable declaration surface is resource-capped at 4,096 atoms. This is
not the analytic request-surface limit. The current two-coordinate domain has
at most \(D^2\) requests, and \(D^2<D^L\) because \(L>2\); hence no request law
on the current surface can have a deterministic positive-event pushforward
equal to \(U_L\). More generally, request support at least \(D^L\) is necessary
but not sufficient. Under a realized \(\mu\), deterministic \(F\), and positive
\(\mathcal A\), exact product uniformity holds if and only if every output
fiber has conditional mass

\[
\mu\!\left(F^{-1}(z)\mid\mathcal A\right)=D^{-L}
\quad\text{for every }z\in[D]^L.
\]

CP46 records this exact weighted-fiber criterion but certifies neither an
external-law realization nor weighted-fiber balance. Its source-TV statements
do not imply a semantic-output lower bound: TV data processing is an upper
bound, and a constant semantic map can erase all source discrepancy.

Ordinary model construction and validation produce sealed cached descriptors
and do not invoke the CP45 owner's live-binding method. Explicit
`revalidate_live_ancestry` remains separately available. Cached certificate
validation and explicit revalidation may inherit CP45's disclosed
deterministic local Philox ancestry probe, so an ordinary returned model
records `live_checkpoint45_ancestry_revalidated_for_this_model=False`.

The standalone
[CP46 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md)
records the complete evidence boundary. The frozen source and focused test
paths are
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
and
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`.
Their SHA-256 values are, respectively,
`8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`
and `04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`.
The authoritative focused run returned **24/24 passed** in **4765.71
seconds** of pytest time and **4766.28 seconds** real time, partitioned into 15
source-independent fast cases and nine owner-bound cases. Exact finite checks
enumerated 1,848 positive partial-map/law cases and 10,000
derived-coordinate/map compositions. Static gates passed, and final
independent audits report `P0=P1=P2=0`.

The CP46 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It certifies no
external request-law realization or sampling, live request uniformity or
coordinate independence, full-capsule product uniformity, nondegenerate V/W
independence, event positivity or unconditional source/output law, physical
randomness, cross-call freshness, semantic-output TV lower bound, loaded-code
integrity, portability, cryptographic authentication,
initializer/path/sampler admission, empirical or model-quality result,
cross-domain generality, C-row, R-slot, or manuscript claim.

#### Checkpoint 47: external full-capsule execution adapter

Checkpoint forty-seven binds one exact CP46 owner and its transitive CP45,
CP44, and CP43 ancestry to a caller-supplied full-capsule provider. For one
preflighted request, the provider receives exactly

```text
(source_instance_sha256, draw_index, L)
```

and, if it returns, must return an exact built-in tuple of length \(L\) whose
entries are exact built-in integers in \([0,D)\), \(D=2^{64}\). No coercion,
retry, fallback, truncation, padding, or adapter RNG is permitted. The return
interface is exactly \([D]^L\), has cardinality \(D^L\), and is ingested by the
identity bijection before CP43's certified split
\(Z\leftrightarrow(V,W)\) and one combined evaluation.

This is an interface-capacity statement, not a realized source-law statement.
If one successfully returned provider capsule has product-uniform law \(U_L\),
then the certified coordinate split yields independent product-uniform \(V\)
and \(W\). IID conclusions across calls additionally require externally IID
provider draws on distinct draw identifiers. Moreover, the law conditional on
an adapter result agrees with the provider law only under provider/downstream
totality or the corresponding value-independence condition. A provider or
downstream failure whose occurrence depends on the capsule value can bias the
returned-result conditional law.

The exact built-in `run_id`, `initialization_index`, and `draw_index` are
preflighted before state change. Under one owner lock, CP47 assigns one new
immutable retirement-row tuple and its hash-chain tuple before invoking the
provider. A duplicate draw identifier refuses before the provider; each
execution invokes the provider at most once and exactly once if it reaches the
provider boundary. Ordinary provider exceptions, malformed returns, and
downstream refusal do not roll back an API-mediated completed retirement.
Equal capsule values under distinct draw identifiers are legal. The guarantee
is bounded and local to one owner lifetime: it is not global, persistent,
cross-process, restart-safe, cryptographic, or evidence that distinct draw
identifiers have distinct or independent values. Concurrent or reentrant
semantic safety beyond the atomic duplicate reservation is not certified, and
a provider that obtains an ambient owner reference and mutates private state
through same-process introspection is outside the procedural guarantee.

Certification performs one explicit CP46 live revalidation. Ordinary execute,
result-validation, and ledger operations use the cached ancestry boundary.
Successful execution performs the exact CP43 split/join checks and combined
semantic evaluation; it makes no CP27 allocation and does not call CP44
`execute`, CP36 `prepare`, or CP37 `decide`. Sealed provider receipts, results,
and ledger snapshots bind the exact returned words, owner identity, retirement
ordinal and chain, certificate ancestry, and structural semantic custody.
Result and ledger validation are nonreplaying: they invoke neither the
provider nor CP43 semantic work.

The standalone
[CP47 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md)
records the complete evidence boundary. Frozen source and focused-test paths
are
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
and
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`.
Their SHA-256 values are, respectively,
`2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`
and `46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`.
The authoritative warnings-as-errors run returned **31/31 passed** in
**7763.03 seconds** (`2:09:23`) of pytest active duration: 22 fast cases and
nine owner-bound cases. The external timer recorded real `30735.62` seconds,
including a long host-suspension interval, with user `7141.85` and sys `545.25`
seconds. The post-run fast partition passed 22/22 in `1.17` seconds; Black,
syntax compilation, pyflakes, and flake8 `E9,F63,F7,F82` passed; and final
independent audits report `P0=P1=P2=0`.

The CP47 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It certifies no
provider totality, success mass, product-uniform or IID realization, physical
randomness, value freshness, global uniqueness, adaptive retry law,
unconditional returned-result law, semantic-output TV lower bound, concurrent
semantic execution, hostile private-state tamper resilience, loaded-code
attestation, runtime portability, cryptography, initializer/path/sampler
admission, empirical or model-quality result, cross-domain generality, C-row,
R-slot, or manuscript claim.

#### Checkpoint 48: byte-source full-capsule execution

Checkpoint forty-eight constructs one private CP47 complete-word provider over
the exact CP46--CP43 ancestry and exposes exactly two byte-source profiles:
`system-os-urandom-operational` and
`external-exact-byte-block-unverified`. At a reached private provider boundary,
the direct backend receives exactly

```text
(source_instance_sha256, draw_index, 8L)
```

and is invoked once. In the external profile this is the exact caller-supplied
callable. In the system profile it is the fixed internal wrapper, which makes
one call to the cached ordinary `os.urandom(8L)` Python API. If the direct
backend call returns, CP48 requires exact built-in `bytes` of length \(8L\).
Backend exceptions propagate by identity. There is no coercion, retry,
filtering, fallback, padding, truncation, or replacement-source call. Every
exact byte content is accepted by the codec; later CP47 or CP43 refusal remains
possible, so codec acceptance is not CP48 totality.

Let \(D=2^{64}\). For
\(x\in\{0,\ldots,255\}^{8L}\), CP48 implements the fixed manual big-endian map

\[
 B(x)_\ell=\sum_{b=0}^{7}x_{8\ell+b}2^{8(7-b)},
 \qquad \ell=0,\ldots,L-1.
\]

The implemented encoder is its exact inverse, so
\(B:\{0,\ldots,255\}^{8L}\to[D]^L\) is a bijection. Hence a bijective
pushforward preserves total variation. In particular, write
\(U_{\mathrm{byte},8L}:=\operatorname{Unif}(\{0,\ldots,255\}^{8L})\) for the
jointly uniform complete byte-block law and \(U_L\) for the product-uniform
uint64 word law. Then

\[
 \operatorname{TV}(B_\#\mu,U_L)
 =\operatorname{TV}(\mu,U_{\mathrm{byte},8L}).
\]

Thus an exactly jointly uniform complete byte block maps to product-uniform
words. Uniform one-byte marginals alone do not imply this joint law. IID word
capsules across distinct draw identifiers require backend blocks that are
jointly product uniform across calls, or sequentially uniform conditional on
the complete prior history.

Those byte-law premises do not by themselves establish a returned-result law.
Writing \(Z=B(X)\) for the decoded capsule, let \(R_{48}\) be the complete
event that CP48 returns after all backend, CP47, custody, and final structural
checks. A uniform returned capsule requires
\(\Pr(R_{48})>0\) and complete CP48 success likelihood
\(\Pr(R_{48}\mid Z=z)\) constant over capsule values \(z\); complete totality is
sufficient. A returned sequence analogously requires positive joint return-
event mass and the corresponding joint success condition over the full capsule
vector. Separate one-call marginal uniformity or success conditions do not
establish returned-sequence IID.

CP47 remains the sole draw-retirement and semantic-execution authority. CP48
creates no second retirement ledger and does not roll CP47 retirement back.
Once CP47 has retired a draw, a backend exception, malformed byte return, or
downstream refusal does not restore it, and a duplicate draw identifier is
refused by CP47 before another backend boundary. Successful CP48 results retain
the exact originating bytes, the exact decoded words, their byte-for-byte round
trip, and the exact CP47 result. Result validation is structural and replays
neither the backend nor CP47/CP43 semantics. Empty thread-local and acquisition
maps after failure cleanup establish only ordinary private-reference cleanup,
not secure memory erasure.

The controlled same-draw race is deliberately a zero-result test. The
retirement-winning execution is held inside its sole backend boundary until the
competing execution is refused by CP47 as already retired; release then produces
the designated backend-marker failure. This establishes exactly one direct
backend invocation, one marker failure, one duplicate refusal, and ordinary
private-reference cleanup on that exercised path. The separate synchronous
same-thread, same-draw callback-reentry case establishes only that CP47
retirement rejects the nested execution before a second backend boundary while
the outer execution can complete. Neither test certifies general thread,
different-draw, reentrant, scheduler, asynchronous-task, or hostile-callback
safety, and the zero-result race supplies no positive return-event mass.

The system profile certifies only the cached ordinary Python `os.urandom` API
binding and direct call site. It does not certify the operating system's law,
independence, totality, physical entropy, internal retry behavior, syscall
count, cryptographic security, authentication, freshness, or reproducibility.
The external profile analogously certifies exact callable identity and
invocation shape, not behavior or law. CP48 additionally certifies no backend
totality or success probability, byte-block uniformity, cross-call IID,
distinct values from distinct identifiers, global/cross-owner/cross-process/
fork/restart uniqueness, backend internals, loaded-code integrity, portability,
hostile same-process tamper resilience, realization of CP46's declared request
law, unconditional returned-result law, or semantic-output TV lower bound. The
bijective source-space TV identity does not yield a lower bound after CP43's
potentially many-to-one semantic map. CP48 admits no initializer, path, or
sampler and promotes no scientific, model-quality, cross-domain, generality,
novelty, empirical, C-row, R-slot, or manuscript claim.

The standalone
[CP48 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md)
records the complete evidence boundary. Frozen source and focused-test paths
are
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
and
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`.
The source contains 2,025 lines and 82,973 bytes, with SHA-256
`7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd`;
the test contains 1,692 lines and 62,124 bytes, with SHA-256
`2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282`.
The authoritative no-cache, warnings-as-errors run passed **37/37** tests in
**15191.58 seconds** of pytest time, partitioned into 28 source-independent fast
cases and nine owner-bound cases; fixture setup took **15048.01 seconds**.
External timing was `15192.11` seconds real, `13929.09` user, and `1211.79`
system. The unchanged pinned pair then passed the exact 28/28 fast partition in
`2.16` seconds. Static gates passed, and final independent reviews report
`P0=P1=P2=0`. One retained P3 note records asynchronous-task safety as an
explicit nonclaim, not an unlocked guarantee. The CP48 disposition is **PASS
WITH EXPLICIT SCOPE LIMITS**. The venue-neutral Markdown and TeX manuscript
hashes remain unchanged.

#### Checkpoint 49: assumption-gated full-source law admission

Checkpoint forty-nine adds one nonexecuting, assumption-gated law-admission
contract above the exact CP48 owner and its CP47--CP43 ancestry. Its sole v1
declaration is an explicitly unverified external mathematical assumption,
never an operational attestation. For each individually fixed request
\((r,j,d)=(\texttt{run_id},\texttt{initialization_index},\texttt{draw_index})\)
and fixed pre-operation state, the antecedent assumes a fresh draw, available
retirement capacity, and passing preboundary guards; almost-sure return of one
exact \(8L\)-byte block by the bound backend; an unconditional jointly uniform
law for that complete block; complete post-boundary success for every exact
block; and fixed-runtime deterministic, replay-stable, typed-total CP43/CP42
object semantics. Duplicate-draw, capacity, and other preboundary refusals are
outside this kernel and are not totalized by choosing the declaration.

Let \(C:\{0,\ldots,255\}^{8L}\to[D]^L\) be CP48's certified byte/word
bijection, let \(B\sim\mu\), and define the pointwise enriched semantic map

\[
 T_{\mathrm{obj}}(w)=
 (\mathrm{status},\mathrm{comparison\ count},
   \mathrm{selected\ attempt\ index},
   \mathrm{canonical\ bit\mbox{-}exact\ CP42\ configuration\ value\ or\ None}).
\]

The status coordinate preserves `preparation_failure`,
`quota_certification_failure`, `selected`, and `exhausted` as distinct values.
Replacing only the last coordinate by the canonical configuration SHA-256
yields CP44's canonical projection of the CP43 applied decision. A selected
CP49 result separately retains the actual nested CP42 configuration object by
identity for custody; runtime object identity is not part of the probability
space. Under exactly the declared antecedent,

\[
 \operatorname{Law}(T_{\mathrm{obj}}(C(B)))
   =(T_{\mathrm{obj}}\circ C)_{\#}\mu,
 \qquad
 \operatorname{TV}((T_{\mathrm{obj}}\circ C)_{\#}\mu,
                    (T_{\mathrm{obj}})_{\#}U_L)
 \leq \operatorname{TV}(\mu,U_{\mathrm{byte},8L}).
\]

This is a one-request, premise-qualified pushforward and data-processing
statement, not a verified backend law. If \(R\) is instead a nontotal complete
return event, write \(s(b)=\Pr(R\mid B=b)\) and
\(Z=\sum_b\mu(b)s(b)>0\). Then the returned word law is

\[
 \Pr(C(B)=w\mid R)
 =\frac{\mu(C^{-1}(w))s(C^{-1}(w))}{Z}.
\]

For uniform \(\mu\), a returned law uniform on the complete word domain holds
if and only if \(s\) is positive and constant there. Separate one-call or
marginal premises do not establish a returned-sequence IID law. Such a result
requires either a joint product-uniform full-vector source law or each new
block conditionally uniform given the complete prior and adaptive history,
for distinct pre-admissible requests, together with positive joint return mass
and value-independent joint complete success. Adaptive stopping and retry
remain outside CP49.

`describe` performs no source or semantic work. Certification,
`admit_returned_result`, and ordinary result validation are structural and
nonreplaying: they do not acquire bytes or call CP43/CP42 semantics. The
separate explicit live-ancestry operation may replay CP48 ancestry validation,
but it still never acquires source bytes or executes the semantic map. The
internal certificate field `passed=True` records consistency with this narrow
contract; it is neither a test-result field nor an attestation that any
mathematical premise holds in operation.

The owner-bound evidence includes a concrete selected custody witness over the
same exact one-attempt ancestry: all proposal and decision words are zero, the
first certified quota is positive, and decision word \(W_0=0\) selects attempt
zero after one comparison. CP49 retains the exact nested CP42 configuration
object and thereby identifies both one nonempty enriched semantic-atom fiber
and its coarser nonempty configuration-value fiber. Only under the declared
abstract uniform and total-semantics assumptions, one exhibited preimage gives
those fibers and the selection event reference mass at least \(2^{-64L}\),
and defines the selected-conditioned reference law. The concrete result is
structural custody evidence, not operational source-law evidence or initializer
admission.

The standalone
[CP49 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md)
records the complete evidence boundary. Frozen source and focused-test paths
are
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
and
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`.
The source contains 1,913 lines and 84,530 bytes, with SHA-256
`7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39`;
the test contains 1,765 lines and 70,075 bytes, with SHA-256
`a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a`.
The authoritative no-cache, warnings-as-errors suite passed **28/28** tests in
`25354.31` seconds (`7:02:34`) of pytest time: 21 source-independent cases and
seven cases sharing the genuine owner-bound fixture. Shared fixture setup took
`17897.94` seconds. `/usr/bin/time -p` recorded real `25366.40`, user
`23535.81`, and sys `1681.97` seconds. JUnit records 28 tests with zero errors,
failures, or skips; shell and pytest exits are zero; and pre/post source and
test hashes are stable. The unchanged pair then passed the independent fast
partition **21/21**, with seven owner-bound cases deselected, in `2.04` seconds
of pytest time; external timing was real `2.62`, user `1.67`, and sys `0.45`
seconds. Black, locked-runtime syntax compilation, pyflakes, and flake8
`E9,F63,F7,F82` passed, and independent source, hostile-test, and claim-scope
audits report `P0=P1=P2=0`.

Evidence provenance is deliberately narrow. The pinned
[status record](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/status.env)
and
[JUnit record](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/junit.xml)
are authoritative for the first completed success; only lines 1--30 of the
pinned
[authoritative log](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/authoritative.log)
belong to that run and support the reported runtime details. An unintended
automatic repeat begins at line 31, was
[stopped](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/UNINTENDED_REPEAT_STOPPED),
and is excluded from all evidence and counts.

CP49 certifies no backend, operating-system, or callback law; totality or
operational realization; unconditional returned-result law; sequence IID or
adaptive-query/retry law; duplicate/capacity/preboundary totalization; global
uniqueness; physical-randomness, entropy, cryptographic, or authentication
property; loaded-code integrity or runtime portability; semantic-output TV
lower bound; CP41-premise discharge or universal CP36/CP37 equivalence; CP40
result, fixed-batch target, or live/general initializer admission; exact ideal
rejection or a globally normalized analytic tilt; intensity, lineage, tag-3
payload, Brownian, path, or sampler; Formal Test 28 closure; scientific or
model-quality result;
cross-domain generality; C-row; R-slot; or manuscript claim. Formal Tests 28
and 29 remain **OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains
**NOT RUN**.
The CP49 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. The venue-neutral
Markdown and TeX manuscript hashes remain unchanged.

The remaining analytic-method initialization design, not the CP39--CP49 software
contract, follows this order:

1. exact enumeration for finite known-law gates;
2. exact rejection sampling for the **plug-in tilted law** when
   \(M_h=H_m(a,z)e^{B_R}\) is certified: propose
   \(Y\sim\Pi_N\) and accept with probability \(\widehat h_0(Y)/M_h\);
   otherwise
3. fixed-budget sampling-importance-resampling: draw \(J_{\rm SIR}\) iid states from
   \(\Pi_N\), compute log weights
   \(\log\widetilde h_0+\mathcal C_{B_R}(F_\theta)\), normalize by
   log-sum-exp, and perform one categorical resample.

Sampling from \(\Pi_N\) first draws
\(n\) with probability \(\vartheta^n/(n!Z_N)\), then draws \(n\) iid events
from \(\nu\) and canonicalizes the counting configuration. In the current
finite-RNG implementation, both categorical draws must pass the frozen
resolution check: every realized CDF bin is at least
\(\max(2^{-40},32K\epsilon_{64})\) and agrees with its declared probability
within the checked increment tolerance. A valid log law that fails this
operational gate is refused; it is not silently sampled from a clipped,
renormalized, or unreachable-support approximation. A future
variable-random-bit sampler requires a separate exactness/resource audit.
Rejection attempts use independent proposals; exceeding the frozen attempt
ceiling fails the run instead of falling back to a biased sample. Separate
requested conditional outputs use independent rejection streams or
independent SIR particle clouds.

The observation-only nuisance cancels and is never used as a particle weight.
The particle count, resampling method, random stream, ESS warning, and failure
rule are frozen. A low ESS is not repaired by drawing more particles after
seeing a result. Known-law experiments report initializer TV/KL error; real
experiments report ESS and sensitivity across preregistered particle budgets.

### 8.2 Reverse/plugin simulation

Finite known-law gates use exact CTMC simulation or certified thinning. The
mixed and real-domain process uses the following Strang split on a grid aligned
with every schedule breakpoint. For a step \([u_j,u_j+h]\):

Any step contained in the final reverse clean hold
\([S-s_{\mathrm{hold}},S]\) copies the state exactly and consumes no model or
random-number evaluation. Every active step follows:

1. Advance extant coordinates through a half-step \(h/2\) with the additive-
   noise stochastic Heun method. The predictor and corrector evaluate the
   drift at the half-step endpoints and share the same Brownian increment.
2. Freeze continuous coordinates and generative time at
   \(u_j+h/2\). For the full jump substep of operational length \(h\), pass
   the canonical state to the process-owned deterministic reference-intensity
   preflight. This supplies
   \(\Lambda_{S-u_j-h/2}^0(y)\) without consuming RNG and refuses any
   unresolved family, birth-type, replacement-source, or reachable
   replacement-destination categorical law before a waiting-time draw. Construct
   the certified outward-rounded rate
   \(E_\Psi^{\mathrm{op}}(u_j+h/2,y;a,m,z)\), use it as the proposal clock,
   and then draw the candidate edit, including a birth or replacement
   destination, from the normalized reference kernel
   \(q_{S-u_j-h/2}^0/\Lambda_{S-u_j-h/2}^0\). Accept it with probability

   \[
   \frac{
   \Lambda_{S-u_j-h/2}^0(y)
   \exp\{\Psi(y')-\Psi(y)\}
   }{
   E_\Psi^{\mathrm{op}}(u_j+h/2,y;a,m,z)
   }.
   \]

   After every accepted edit, recompute the reference rate and continue;
   rejected candidates leave the state unchanged. This is certified thinning
   and is exact for the frozen jump subproblem, including its continuous
   destinations. It does not require evaluating a tilted destination
   normalizer.
3. Advance the post-jump coordinates through the second stochastic-Heun
   half-step.

The deterministic no-RNG reference-intensity preflight described above is
implemented, as is the separate target-explicit operational guide/residual
log-space composition certificate. Checkpoint eighteen additionally implements
exact-edge aggregate exponentiation, a correctly rounded successful-candidate
integrand, and no-RNG instantaneous/global upper envelopes for that explicit
operational target. It does not compute the active controlled total exit,
admit the route draw, draw a waiting time, make an acceptance decision, or
consume random bits. Checkpoint nineteen separately supplies one
successful-return local wait/route/accept sequence for that operational target.
It treats the `proposal_time` field as the authoritative local-clock
timestamp, retains the inherited finite-resolution route law, and draws the
exact represented \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\) Bernoulli while
continuing one mutable Philox stream. It does not repeat after rejection,
recompute after acceptance, validate a continuous-destination operational route
fixture, or provide counter-keyed streams, lineage, a jump-substep path, or the
full sampler. Checkpoint twenty now wraps that primitive in a bounded
successful-return loop. It advances the represented cursor after every
completed proposal, reuses the exact state/intensity/envelope objects after a
rejection, and immediately rebuilds the intensity and envelope after an
acceptance at the same frozen generative time. The 0--64 proposal budget is a
refusal cap: a result is returned only after a structural-zero, zero-duration,
or active right-endpoint terminal waiting record, and an active cap hit raises
before another wait. This supplies no unconditional completion or exact
frozen-jump/path law. Its operational route evidence remains all-atomic, and it
does not add continuous-destination evidence, counter-keyed streams, lineage,
drift/Strang integration, initialization, or the full sampler.

Checkpoints twenty-one and twenty-two add same-runtime route replay and its
ordered integration across a successfully returned sequential loop. Checkpoint
twenty-three adds initially unused direct namespace receipts and a post-hoc
lineage sidecar. Checkpoint twenty-four separately executes the bounded local
jump operation through direct tag-6 operational epochs, integrates route and
lineage custody for every candidate epoch, and accepts no caller RNG. It still
does not consume a lineage-specific occurrence stream, a legacy tag-1 proposal
receipt, a random-word tag-2 terminal stream, an initializer stream, or a
Brownian stream. Checkpoint twenty-five subsequently consumes only one bounded
uninterpreted tag-3 `raw64` prefix per already existing bootstrap occurrence,
at fixed step zero, without changing the state or accepting a caller RNG. It
does not define the global control choices or any initializer output law.
Checkpoint twenty-six adds the direct tag-7 pre-cardinality namespace and
bounded raw-prefix replay, but not stage/attempt allocation, adaptive branch
chronology, exact output transforms, a general initializer law, accepted-
configuration lineage mapping, or tag-3 payload coordination. Checkpoint
twenty-seven then adds fixed strategy/stage roles and canonical multiblock
work-item allocation, but no decision, transform, output, configuration,
lineage, or payload semantics. Checkpoint twenty-eight transforms only the
fixed reference capsule into a finite canonical configuration and defines its
law only under hypothetical product-uniform words. It supplies no
enumeration/rejection/SIR semantics, general conditional initializer
admission or benchmark beyond the completed fixed-grid reference-transform
diagnostic, lineage, or payload semantics. Checkpoint twenty-nine evaluates
only prespecified discrepancies of that fixed transform on two frozen grids
and supplies one-shot custody; it creates no new initializer semantics.
Checkpoint thirty adds only the deterministic time-zero point factor and also
creates no exponentiated/normalized law, support enumeration, initializer
selection, or path semantics. Checkpoint thirty-one adds exact bounded
all-atomic support and base-coefficient enumeration, but no normalized mass,
exponentiated/normalized tilt, selection, RNG, initializer-protocol binding,
continuous codebook, lineage mapping, or path semantics. Checkpoint
thirty-two adds a positive dyadic approximation and selection from one
explicit word only; it neither binds nor certifies an initializer word and
adds no mixed/continuous, lineage, payload, or path semantics. Checkpoint
thirty-three binds that sole all-atomic enumeration word to the exact
checkpoint-twenty-seven stage-0 allocation and forwards it unchanged to the
checkpoint-thirty-two selector. For fixed preparation, only replacing the live
word by an abstract uniform \(U\) yields the dyadic law; the fixed-address live
word and output remain deterministic. It does not certify the Philox word law,
sample the ideal law exactly, admit an initializer, add another strategy, or
add mixed/continuous, lineage, payload, Brownian, or path semantics. Checkpoint
thirty-four moves enumeration and preparation into one fixed factory and
exposes only deterministic one-address construction of a valid all-atomic
initial configuration. That constructor does not turn the abstract replacement
theorem into a live distribution or admit an initializer.
Checkpoint thirty-five adds only the fixed-index finite reference
configuration-to-bootstrap-lineage and dimension-shaped tag-3 prefix
coordination just stated; it does not add semantic payload, cross-
initialization address disjointness, a live initializer law, or a path.
Checkpoint thirty-six adds only complete fixed-budget rejection-stage proposal
transformation and point scoring. Its one reserved word per attempt is
uninterpreted; it performs no exponentiation, decision, acceptance, selection,
success/exhaustion handling, initializer admission, lineage/tag-3 coordination,
or path operation.
Checkpoint thirty-seven adds only the exact conservative finite-resolution
quota, all-thresholds-before-comparison chronology, and first-selected-or-
exhausted decision layer over CP36. Its product probabilities use fixed
proposal/score data and a separate abstract iid word family. Separately, a
fixed-data common-uniform coupling of independent-coordinate ideal and dyadic
Bernoulli sequences gives the \(<A/2^{64}\) ideal-outcome comparison. It does
not certify the live word law, exact
ideal rejection, CP36 failure/success-conditioned laws, initializer admission,
lineage/tag-3 coordination, or a path.
Checkpoint thirty-eight adds only the exact fixed-\(B\) counterfactual mass
partition, stable duplicate aggregation, the \(Z_B>0\) selected-law boundary,
and the strict augmented \(<A/2^{64}\) ideal/dyadic comparison from a separate
common-uniform coupling. It does not make the deterministic live result
random, provide a CP36 failure or successful-batch law, permit
selected-conditioned reuse of that TV bound, admit a generic initializer, or
repair the initialization-index gap in lineage/tag-3 addressing.
Checkpoint thirty-nine adds only construction-time coordination of one exact
CP38 selected result with reverse-time-zero intensity, CP23 positional
bootstrap lineage, and CP39-local prefixes whose address includes
initialization index, lineage serial, and selected-attempt suffix. It
distinguishes selected-empty from exhaustion and closes initialization-index
separation only for this bounded selected fixed-batch mapping. It does not
interpret tag-3 payloads, generate coordinates, provide global/one-shot/cross-
bootstrap/merge/fork guarantees, establish a live initializer law or generic
admission, consume Brownian words, or construct a path.
Checkpoint forty adds only the normalized fixed-\(B\) finite-resolution target,
the \(Z_B>0\) selected-state target and scaled ideal/dyadic comparison, and a
narrow structural state/no-state boundary over the exact CP39 result. It does
not establish a live or unconditional initializer law, CP36 success/failure
law, exact ideal rejection, global normalized tilt, all-strategy admission,
semantic tag-3 payloads, Brownian consumption, or a path.
Thus the following semantic initializer, occurrence/Brownian, and split-step
statements remain analytic-method obligations rather than consequences of
checkpoints twenty-four through forty.

The schedule is constant inside each integration step. Counter-based random
streams are keyed by run, step, occurrence identifier, and proposal index.
Under step halving, coarse Brownian increments are sums of the corresponding
fine increments for every surviving lineage; new occurrences receive their
declared independent streams. The full split-step path is numerical even
though the frozen jump subproblem is exact.

The step schedule is fixed before confirmatory execution. Every run records
potential ranges, total rates, rejected/non-finite evaluations, jump counts,
cap contacts, and support inversions. Any non-finite value, undeclared zero,
or missing rate envelope is a failure, not a clipping event. A step-halving
study must pass frozen endpoint, path, and edit-family tolerances before real
results are admissible.

### 8.3 Terminal-reference diagnostic

For every finite known-law fixture, report exact
\(\operatorname{TV}(P_S,\Pi_N)\) and both directed KL divergences when finite.
For a real domain, compare held-out forward-terminal samples to iid
\(\Pi_N\) samples using one preregistered two-sample classifier with a disjoint
test split, plus count, type, and transformed-coordinate diagnostics by frozen
stratum. These are sample-based discrepancy diagnostics, not certified TV
bounds. Their sample counts, uncertainty procedure, and failure threshold are
frozen before base training; failing the terminal gate blocks use of
\(\rho_0^\phi=\Pi_N\) and requires a separately validated terminal-tilt
initializer.

Checkpoint twenty-nine is not the terminal-reference diagnostic required by
this subsection. It tests five finite-transform discrepancies only on a frozen
deterministic tag-7/stage-4 address grid, against envelopes derived under a
hypothetical product-uniform word model. It contains no held-out forward-
terminal sample, iid \(\Pi_N\) comparator, real-domain split, terminal-tilt
decision, or model-quality result.

## 9. Existing implementation and missing interfaces

| Contract | Existing reusable implementation | Status for this specification |
|---|---|---|
| Immutable typed counting configuration | `heterodiff.events.configuration` | Reused; transformed-coordinate and cap wrapper implemented in `heterodiff.theory.configuration_reference`. |
| Finite capped factorial reference and multiplicity | `heterodiff.theory.finite_atomic_counting` | Exact atomic oracle only. |
| Finite association plus positive mixture | `heterodiff.theory.finite_atomic_association_bridge` and `heterodiff.theory.finite_atomic_overflow_observation` | Reuse as A1 oracle. |
| Uncapped association guide | `heterodiff.theory.finite_atomic_reference_guide` | Reuse as finite cap-defect control. |
| Exact joint/product population | `heterodiff.theory.finite_bridge_population` | Reuse as density-ratio oracle. |
| Potential tilt, initializer, path KL, exact thinning | `heterodiff.theory.finite_bridge_path_control` | Reuse for finite gates. |
| Continuous unordered anchors | `heterodiff.theory.gaussian_particle_bridge` | Reuse for continuous association checks. |
| Learned bounded residual | `heterodiff.models.finite_association_residual_torch` | A1-only architecture and certificate. |
| General boundary-gated conditional residual | `heterodiff.models.configuration_residual_torch` | **Implemented and incrementally audited for a fixed finite-dimensional declared conditioner. It reuses an independently certified bounded typed-DeepSets backbone under a distinct residual contract, evaluates only active direct-time rows, and certifies global value/state-pair and physical-coordinate derivative bounds. The conditioner adapter is procedurally digest-bound but its tensor origin is not runtime-authenticated; time/conditioner derivatives, the joint/product trainer and nuisance, a controlled clock, and sampler admission remain pending. Its jump-edge output is consumed by the separate successful composition checkpoint.** |
| General \(\Pi_N\) reference | `heterodiff.theory.configuration_reference` | **Implemented and incrementally audited; full method freeze remains open.** |
| Exact reversible hybrid forward sampler | `heterodiff.processes.reversible_hybrid_reference` | **Implemented and incrementally audited for the forward reference only; full method freeze remains open.** |
| Reference-relative reverse targets and NumPy population-objective oracles | `heterodiff.theory.reverse_energy_objective` | **Implemented and incrementally audited; Tests 7--10 are closed only in theorem/oracle scope.** |
| Bounded permutation-invariant neural scalar, Hutchinson/autodiff training path, and checkpoint certificate | `heterodiff.models.configuration_energy_torch` | **Implemented and incrementally audited in the declared neural-unit scope. Tests 11--12 retain whole-method obligations; this does not authorize training or sampling.** |
| General continuous/mixed association kernel with orbit API | `heterodiff.theory.association_observation` | **Implemented and incrementally audited for the exact endpoint-observation oracle; representative-scale approximation remains open.** |
| Analytic mixed guide, global model-level range/regularity certificate, and harmonic/cap defect | `heterodiff.theory.association_preconditioner` | **Implemented and incrementally audited for the declared conjugate exact-oracle guide, isolated cap term, and fixed-observation real-arithmetic range/edit/coordinate certificate under normalized probability-simplex and Markov-kernel semantics. A small floating-point forward-error analysis, operational sampler admission, and the complete Section 6.3 diagnostic remain open.** |
| Successful-only represented association-guide value and edit gate | `heterodiff.theory.association_operational_guide` | **Implemented and incrementally audited for a fixed observation. It preserves an exact finite raw binary64 log guide only inside directed model bounds, supplies a coarse range-derived discrepancy bound and direct represented edit envelope, and otherwise refuses. It is not total over unbounded coordinates and certifies no coordinate derivative, continuous drift, residual, controlled clock, liveness, or sampler.** |
| Totalized operational-surrogate association jump guide | `heterodiff.theory.association_totalized_jump_guide` | **Implemented and incrementally audited for one fixed observation over the resource-admitted full capped finite-binary64 point domain. It preserves successful raw values and maps only typed numerical/range point failures to the exact-rational interval midpoint rounded once. Legal edits are exact rational operational endpoint coboundaries with \(W_m\), fallback-specific, and outward \(2W_m\) witnesses. It defines a new jump-only operational target, not the analytic conditional/posterior or Doob bridge, and supplies no derivatives, drift, rate envelope, clock, RNG, path, or sampler admission.** |
| Totalized operational-surrogate conditional jump residual | `heterodiff.models.configuration_totalized_jump_residual_torch` | **Implemented and incrementally audited for detached single-row point values and same-time/same-condition endpoint differences. It preserves every successful checkpoint-thirteen point bitwise and maps only the exact typed active tiny-cubic-gate refusal to an exact-rational gate times the represented checkpoint-private bounded core, rounded once. Exact rational operational endpoint differences telescope; rounded binary64 edges need not. It is not the exact real neural residual or conditional/posterior target and supplies no derivative, drift, rate envelope, clock, RNG, path, or sampler admission.** |
| Target-explicit totalized operational jump-potential composition | `heterodiff.models.configuration_totalized_jump_potential_composer_torch` | **Implemented and incrementally audited for one active process-valid birth, death, or replacement candidate. It selects the exported operational-surrogate point target, recomputes checkpoint-private base and both totalized component endpoints, adds exact represented endpoint differences as rationals, and rounds the aggregate once. Its global bounds are operational magnitude witnesses only. It is not an analytic, conditional, posterior, or Doob target and performs no exponentiation, rate-envelope or total-exit construction, clock/RNG decision, derivative/drift computation, initialization, path construction, or sampler admission.** |
| Totalized operational jump-rate envelope | `heterodiff.models.configuration_totalized_jump_rate_envelope_torch` | **Implemented and incrementally audited for checkpoint seventeen's explicit operational-surrogate target. It exponentiates the exact rational edge by adaptive directed Decimal direct-product arithmetic, returns a correctly rounded finite normal candidate integrand on success, and constructs no-RNG instantaneous/global controlled-total-exit upper bounds. Structural zero is exact. It does not compute the active total exit, admit a candidate route draw, preserve rounded detailed balance, or implement waiting/acceptance RNG, derivatives/drift, initialization, paths, or a sampler.** |
| Successful-return local operational thinning | `heterodiff.processes.plugin_bridge_operational_thinning` | **Implemented and incrementally audited for one local wait/route/accept sequence under checkpoint eighteen's envelope. It applies inclusive ideal-real endpoint eligibility with strict represented-interior return or refusal, retains the inherited finite-resolution route, and draws an exact Bernoulli for the represented \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\) quotient while continuing one Philox stream. The returned `proposal_time` is the authoritative local-clock timestamp. A repeated loop, continuous-destination operational fixture, counter-keyed streams, lineage, drift/Strang integration, initialization, path, liveness theorem, and full sampler remain pending.** |
| Bounded successful-return local thinning coordination | `heterodiff.processes.plugin_bridge_operational_thinning_loop` | **Implemented as checkpoint twenty and mapped in its separate incremental audit. It repeats checkpoint nineteen at one fixed generative time, advances the represented cursor after every proposal, reuses the exact parents after rejection, and immediately refreshes the accepted-state intensity and envelope. Results require a terminal structural-zero or right-endpoint waiting record; active exhaustion of the exact caller-supplied proposal budget \(B\), with \(0\le B\le64\), is a refusal before another wait. It uses one sequential Philox stream and returns no budget-truncated transcript. It is not an exact real-time Poisson/CTMC or unconditional frozen-jump law, exact route sampler, continuous-destination operational evidence, counter-keyed/lineage contract, path, drift/Strang step, initializer, liveness theorem, or full sampler.** |
| Same-runtime continuous-route replay evidence | `heterodiff.processes.plugin_bridge_continuous_route_evidence` | **Implemented as checkpoint twenty-one and mapped in its separate incremental audit. It retains reconstructable canonical pre/post Philox states around one delegated checkpoint-nineteen route, replays the frozen process-owned composer on a fresh local generator, and requires the candidate digest and exact post-state to agree. Record-specific evidence covers continuous birth and both directions of a genuine unequal positive-dimensional reset replacement. It is not an exact categorical/integer/Gaussian law, a bounded normal-word trace, Test-29 distribution recovery, liveness, a path, or the full sampler.** |
| Ordered bounded-loop route-evidence integration | `heterodiff.processes.plugin_bridge_operational_thinning_loop_route_evidence` | **Implemented as checkpoint twenty-two and mapped in its separate incremental audit. It runs checkpoint twenty as a black box, captures exact loop-entry/exit Philox snapshots, reconstructs every waiting, route, acceptance, and terminal prefix on a local stream, and binds one checkpoint-twenty-one route witness to each completed proposal. It inherits checkpoint twenty's rejection, refresh, terminal, and cap semantics. A post-loop overlay failure is fail-closed but does not roll back caller randomness already consumed by the parent. It is not an ideal route law, unconditional completion or liveness theorem, analytic-target result, counter-keyed/lineage contract, path, or full sampler.** |
| Direct Philox namespaces and post-hoc persistent lineage | `heterodiff.processes.plugin_bridge_counter_keyed_lineage_contract` | **Implemented as checkpoint twenty-three and mapped in its separate incremental audit. It issues initially unused same-runtime NumPy Philox receipts with direct key `(run_id, domain_tag)` and counter `(0, step_index, occurrence_serial, proposal_index)`, and deterministically annotates one fully revalidated checkpoint-twenty-two result with a duplicate-safe positional lineage sidecar. It preserves exact indexed destruction, survivor identity, stable model-key-only ordering, fresh monotone creation, rejection/terminal state identity, and a bounded retired-ID ledger. It does not make checkpoint twenty-two proposal-keyed, certify consumption of any receipt, enforce global run-ID or one-shot-address uniqueness, consume or couple Brownian streams, implement drift or initialization, construct a path, or admit the full sampler.** |
| Counter-keyed operational-epoch loop | `heterodiff.processes.plugin_bridge_counter_keyed_operational_epoch_loop` | **Implemented as checkpoint twenty-four and mapped in its separate incremental audit. Every active loop boundary uses one direct tag-6 stream with key `(run_id, 6)` and counter `(0, step_index, 0, completed_proposals)` continuously through wait and, if due, route and represented-ratio acceptance. Candidate epochs bind checkpoint-twenty iteration, checkpoint-twenty-one route evidence, and checkpoint-twenty-three lineage transition records. Active right-endpoint exhaustion remains on tag 6; deterministic holds bind a tag-2 receipt and consume zero words. It accepts no caller RNG. It does not consume legacy tag-1 proposal receipts, random words from tag 2, occurrence/initializer/Brownian streams, or admit an exact jump law, path, drift/Strang step, liveness theorem, or full sampler.** |
| Bootstrap tag-3 initializer-stream prefix custody | `heterodiff.processes.plugin_bridge_counter_keyed_initializer_stream_consumption` | **Implemented as checkpoint twenty-five and mapped in its separate incremental audit. It binds the exact checkpoint-twenty-four and checkpoint-twenty-three owners, admits only an existing no-retirement positional bootstrap with at most 64 live occurrences, fixes step zero, and consumes one exact positive tag-3 `raw64` prefix per serial with 4,096-word per-occurrence and 65,536-word aggregate caps. Exact pre/post snapshots, no upper carry, same-runtime replay, no caller RNG, and exact unchanged input-state identity are enforced. The words are uninterpreted: no cardinality, event, coordinate, categorical, Gaussian, rejection, SIR, reference, tilted, or conditional initializer law is implemented. A separate global initializer control domain, general initializer, Brownian coupling, drift, path, and full sampler remain pending.** |
| Pre-cardinality tag-7 global initializer-control prefix custody | `heterodiff.processes.plugin_bridge_counter_keyed_global_initializer_control` | **Implemented as checkpoint twenty-six and mapped in its separate incremental audit. It binds the exact checkpoint-twenty-five owner and transitive checkpoint-twenty-four/twenty-three ancestry, then consumes one bounded uninterpreted `raw64` prefix per entry of a strictly lexicographic canonical plan. The direct address is key `(run_id, 7)`, counter `(0, initialization_index, stage_index, attempt_index)`; caps are 64 records, 4,096 words per stream, and 65,536 words in aggregate. Exact pre/post snapshots, no upper carry, same-runtime replay, empty-plan no-op, no caller RNG, declared nested identity relations, and validation-window mutation custody are enforced; a self-consistent pre-call transcript clone is not excluded. Stage/attempt and branch/retry semantics, output transforms, a general initializer law, accepted-configuration lineage mapping, tag-3 payload coordination, Brownian coupling, drift, path, and full sampler remain pending.** |
| Fixed-budget tag-7 initializer-protocol allocation | `heterodiff.processes.plugin_bridge_counter_keyed_initializer_protocol` | **Implemented as checkpoint twenty-seven and mapped in its separate incremental audit. It binds the exact checkpoint-twenty-six owner, freezes enumeration/rejection/SIR/reference stages 0--4, maps fixed multiblock work items injectively by `outer_index * block_count + block_index`, materializes the complete bounded parent plan, and binds exact chronology, parent-plan identity, raw-word identity, and same-runtime replay without a caller RNG. It performs no support normalization, rejection decision/outcome, SIR weighting/resampling, reference transform, configuration generation, initializer output law, lineage mapping, or tag-3 coordination.** |
| Finite-resolution fixed reference-strategy transformer | `heterodiff.processes.plugin_bridge_counter_keyed_reference_initializer` | **Implemented as checkpoint twenty-eight and mapped in its separate incremental audit. It binds the exact checkpoint-twenty-seven owner and reference ancestry; records exact binary64-induced count/type targets, positive dyadic Hamilton quotas and exact TV errors; consumes the fixed (1+N+ND) layout; transforms all slot/padding coordinates before count decoding; and returns a duplicate-stable canonical configuration. Its exact finite law is defined only under hypothetical product-uniform uint64 words. Actual Philox output is deterministic procedural evidence, not certified uniformity, independence, randomness, or equality to the continuous capped-Poisson/Gaussian reference. It implements no enumeration/rejection/SIR, conditional or tilted initializer, lineage/tag-3 coordination, path, or sampler admission.** |
| Frozen-grid reference-transform diagnostic and one-shot custody | `heterodiff.processes.plugin_bridge_counter_keyed_reference_initializer_diagnostic`, `heterodiff.artifacts.reference_initializer_diagnostic_artifact`, `heterodiff.experiments.reference_initializer_diagnostic_production`, and the independent verifier | **Implemented and executed as checkpoint twenty-nine. One sole attempt evaluated five prespecified exact discrepancies on two 16,384-row deterministic grids; all fell within envelopes frozen under the hypothetical product-uniform model. This is nonconfirmatory engineering evidence with terminal `PASS` and audit disposition PASS WITH EXPLICIT SCOPE LIMITS. It is evaluation/custody tooling, not an initializer or sampler dependency, and certifies no Philox law, actual finite pushforward law, continuous reference, general initializer admission, or scientific result.** |
| Time-zero operational initial-log-factor point composer | `heterodiff.models.configuration_initial_tilt_composer_torch` | **Implemented as checkpoint thirty and mapped in its incremental code audit. It binds the selected \(\Pi_N\) base, totalized guide at reverse time zero, and totalized residual at direct time \(S\); excludes \(V_\phi(S,x)\) and a separate observation-only nuisance; adds the two represented binary64 values exactly as rationals; and rounds the aggregate once. Its outward interval, process-local custody, replay, and resource contract are deterministic point evidence only. It performs no exponentiation, normalization, support enumeration, rejection, SIR, categorical selection, RNG consumption, initialization, path construction, or sampler admission, and it does not establish the analytic conditional/posterior target.** |
| Exact bounded all-atomic initial-tilt support enumeration | `heterodiff.models.configuration_initial_tilt_atomic_enumerator_torch` | **Implemented as checkpoint thirty-one and mapped in its incremental code audit. It exact-renormalizes the represented raw type weights, enumerates every resource-admitted atomic count vector in cardinality-then-lexicographic order, stores the exact unnormalized coefficient \(a^{\lvert m\rvert}\prod_jp_j^{m_j}/m_j!\), verifies local/cardinality/global completeness identities, and attaches one replay-validated checkpoint-thirty point to every state. It refuses every positive-dimensional reference and performs no normalized-mass materialization, point-factor exponentiation, tilted normalization, selection, rejection, SIR, RNG, initializer-protocol binding, continuous-codebook construction, path construction, or sampler admission.** |
| Finite-resolution all-atomic operational tilted-law preparation and explicit-word selection | `heterodiff.models.configuration_initial_tilt_atomic_selector_torch` | **Implemented as checkpoint thirty-two and mapped in its incremental code audit. It combines checkpoint-thirty-one exact base coefficients with checkpoint-thirty exact represented-component log factors, constructs adaptive directed weight and normalized-mass enclosures, normalizes a positive exact-rational midpoint proxy, forms positive \(2^{64}\) Hamilton quotas with ordinal ties, certifies ideal-to-dyadic TV at most \(2^{-48}\), and performs exact half-open lookup from one explicit uint64 word. It does not acquire or certify the word, bind checkpoint twenty-seven stage 0, sample the ideal transcendental law exactly, admit an initializer, cover mixed/continuous support, or construct a path or sampler.** |
| Counter-keyed one-word all-atomic selection binding | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_atomic_selection` | **Implemented as checkpoint thirty-three and mapped in its incremental code audit. It binds the exact checkpoint-twenty-seven enumeration request with budget one, empty work-item blocks, one selection word, plan \(((0,0,1),)\), key \((r,7)\), and counter \((0,i,0,0)\); validates shared checkpoint-thirty-two ancestry before allocation; and forwards the sole parent word unchanged to the exact selector. For fixed preparation \(p\), replacing the live word source by an abstract \(U\sim\operatorname{Unif}(\mathrm{uint64})\) gives \(f_p(U)\sim Q_p\); separately, that fixed preparation inherits \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\). The two word sources are not identified, though their uint64 values may coincide. The live fixed-address word and output are deterministic point masses. It does not certify an actual Philox law, sample \(P_{\mathrm{operational},p}\) exactly, establish global one-shot use, admit an initializer, cover mixed/continuous support or other strategies, or construct a path or sampler.** |
| Fixed all-atomic initial-configuration constructor and counterfactual ideal-word theorem | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_atomic_admission` | **Implemented as checkpoint thirty-four and mapped in its incremental code audit. Its factory owns canonical context, complete checkpoint-thirty-one enumeration, checkpoint-thirty-two preparation, and exact checkpoint-thirty-three ancestry before exposing `initialize(run_id, initialization_index)` plus result validation. Each successful live construction consumes exactly one inherited stage-0 word and returns a valid all-atomic initial configuration, with no per-call context/preparation/RNG/word, added namespace, retry, fallback, or rollback. For fixed preparation \(p\), an abstract ideal \(U\sim\operatorname{Unif}(\mathrm{uint64})\), explicitly not identified with the live word source, satisfies \(f_p(U)\sim Q_p\); separately, that fixed preparation inherits \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\). The two word sources may produce equal uint64 values. At a fixed live address the word and output are deterministic point masses. It therefore certifies a configuration constructor, not a live initializer distribution or initializer admission; the historical module name does not promote admission. It supplies no actual RNG law, global address uniqueness, mixed/continuous support, other strategy, lineage/tag-3 coordination, path, or sampler.** |
| Fixed-index finite mixed reference constructor with bootstrap lineage and tag-3 prefix custody | `heterodiff.processes.plugin_bridge_counter_keyed_mixed_reference_constructor` | **Implemented as checkpoint thirty-five and mapped in its incremental code audit. It composes the complete CP28 tag-7 finite transform at index zero, reverse-time-zero reference intensity, CP23 bootstrap lineage, and CP25 prefixes of length \(\max(1,d_j)\), behind `initialize(run_id)`. Only abstract iid-uniform substitution for the complete CP28 capsule yields configuration law \(Q_{\mathrm{fin}}\); live replay is deterministic. The structural-TV formula is an exact-rational upper bound and positive-dimensional codebook/Gaussian fiber TV is conditionally one. Tag-3 addresses omit initialization index, so cross-initialization disjointness is not established. Focused evidence is 64/64 in 998.81 seconds; the no-cache direct-parent regression is 173/173 with no failures, skips, xfails, xpasses, or warnings in 1251.19 seconds. The disposition is PASS WITH EXPLICIT SCOPE LIMITS; no initializer admission, path, or sampler is claimed.** |
| Fixed-budget initial-tilt rejection proposal-and-score preparation | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_preparation` | **Implemented as checkpoint thirty-six and mapped in its incremental code audit. It asks CP27 to materialize the complete rejection-stage-1 prefix, applies the exact CP28 proposal transform for every attempt, retains one reserved uninterpreted word per attempt, and records CP30's exact represented score \(q\) and reduced rational witness \(q-U\le0\). Addresses use key `(run_id, 7)`, counter `(0, initialization_index, 1, a*(B+1)+b)`, and a separate word offset. Its only distributional theorem uses a separate abstract iid-uniform uint64 family over distinct coordinates and a failure-augmented total map; it supplies no live word law, failure probability, or success-conditional law. The focused suite passed 115/115 and the no-cache direct-parent regression passed 171/171; the disposition is PASS WITH EXPLICIT SCOPE LIMITS. It performs no exponentiation, decision, acceptance, selection, initializer admission, lineage/tag-3 coordination, path, or sampler operation.** |
| Conservative finite-resolution initial-tilt rejection decision | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_decision` | **Implemented as checkpoint thirty-seven and mapped in its incremental code audit. It certifies \(K_a=\lfloor2^{64}e^{q_a-U}\rfloor\) for every CP36 attempt before any word-to-quota comparison, then applies the exact predicate \(w_a<K_a\) in prefix order and returns the first selected CP36 configuration or bounded exhaustion. Word type/range may be preflighted during threshold construction; later words remain materialized but decision-uninterpreted after early selection. For fixed proposal/score data and separate abstract iid-uniform words, it records the exact first-index/exhaustion product law. Separately, a fixed-data common-uniform coupling of independent-coordinate ideal and dyadic Bernoulli sequences gives the strict \(A/2^{64}\) ideal-outcome TV bound. The focused suite passed 44/44 and the no-cache CP36 regression passed 115/115; the disposition is PASS WITH EXPLICIT SCOPE LIMITS. It certifies no live Philox law, exact ideal rejection, failure probability, success-conditional law, normalized tilted initializer, admission, lineage/tag-3 coordination, path, or sampler.** |
| Exact counterfactual finite-batch rejection law and structural selected-state boundary | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law` | **Implemented as checkpoint thirty-eight and mapped in its incremental code audit. Conditional on the direct word-free \(B\) of CP36 candidates/gaps and CP37 quotas, a separate abstract iid-uniform uint64 family gives the complete exact first-success/exhaustion mass partition. Structurally equal configurations are aggregated, and the selected-configuration law is defined only when \(Z_B>0\); all-zero quotas give exhaustion mass one and no conditioned law. A separate common-uniform ideal/dyadic comparison gives strict augmented TV \(<A/2^{64}\) before selection conditioning and is not directly reused unchanged by CP38 afterward. The live result is deterministic replay. Selection certifies structural initial-state validity only; generic admission remains false. Lineage/tag-3 attachment is deferred because the current namespace omits general initialization-index separation. The no-cache, warnings-as-errors focused suite passed 45/45 and the no-cache CP37 regression passed 44/44; the disposition is PASS WITH EXPLICIT SCOPE LIMITS.** |
| Selected rejection-state positional lineage and initialization-indexed local tag-3 coordination | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_coordination` | **Implemented as checkpoint thirty-nine and mapped in its incremental code audit. It invokes exact CP38 `resolve` once. Selection retains the exact CP38 configuration and CP37 attempt, queries reverse-time-zero reference intensity, maps canonical position \(j\) to CP23 bootstrap serial \(j+1\), and consumes \(\max(1,d_j)\) uninterpreted words at key `(run_id, 3)` and counter `(0, initialization_index, j+1, selected_attempt_index+1)`, under caps of 64 occurrence records, 4,096 words per occurrence, and 65,536 words in aggregate. Selected-empty retains intensity and empty lineage with no stream; exhaustion is exact no-state with no selected-branch child construction. Positive suffixes are disjoint only from valid legacy suffix-zero tag-3 addresses. Same-address replay is deterministic. The focused suite passed 65/65 and the CP38 parent regression passed 45/45; the disposition is PASS WITH EXPLICIT SCOPE LIMITS. No live law, payload/coordinate semantics, global/one-shot/cross-bootstrap/merge/fork guarantee, cryptographic or cross-runtime-portability guarantee, generic initializer admission, Brownian/path, or sampler claim follows.** |
| Fixed-batch finite-resolution rejection target and structural state admission | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_admission` | **Implemented as checkpoint forty and mapped in its incremental code audit. It accepts one exact CP39 owner, calls `coordinate` once, materializes the always-normalized augmented dyadic target conditional on CP38's direct word-free successful batch, defines the selected-state target only for positive \(Z_B\), and records the raw strict \(2A/(2^{64}Z_B)\) comparison plus its separately labelled clipped non-strict display. Selection, including selected-empty, preserves the exact CP39 state and admits it only under this declared target; exhaustion retains the target and no state. The target row is selected by ordinal but never substitutes its duplicate representative for the actual state. Source and tests are frozen, the focused suite passed 45/45, and inherited exact-hash CP39 parent evidence remains applicable; the disposition is PASS WITH EXPLICIT SCOPE LIMITS. No live/unconditional law, CP36 failure law, exact ideal rejection, global normalized tilt, all-strategy general initializer, semantic tag-3 payload, Brownian/path, or sampler claim follows.** |
| Failure-aware abstract product-uniform rejection source law | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law` | **Implemented as checkpoint forty-one and mapped in its [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md). It is exactly an abstract product-uniform failure-aware source law conditional on an explicit unproved factorization hypothesis. It partitions CP36 words into proposal/scoring \(V\) and reserved-decision \(W\), distinguishes preparation failure, quota failure, exhaustion, and configurations, and symbolically defines their exactly normalized mixture. It records the \(\rho=0\) identity, strict \(\rho A/2^{64}\) augmented comparison, and positive-\(S_Q\) factor-one conditioned bound. No fiber or numeric mass is materialized; no CP36--CP40 operational call is made; and no live Philox/source/initializer law, exact ideal rejection, global analytic normalization, general admission, path, or sampler claim follows. The no-cache, warnings-as-errors focused suite passed 28/28; the disposition is PASS WITH EXPLICIT SCOPE LIMITS.** |
| Successful-only certified base/guide/residual jump-log composition | `heterodiff.models.configuration_potential_composer_torch` | **Implemented and incrementally audited for one active, already sampled process-valid reference candidate. It recomputes all three increments from the same endpoints, uses direct time for the base/residual and reverse time for the guide, performs an exact-rational single-round represented sum, and supplies separate time-specific mathematical and operational aggregate log bounds. It is partial with the range-gated guide and does not exponentiate, construct a rate-space envelope or total exit, draw waiting/acceptance randomness, certify drift, or admit a sampler.** |
| Process-owned reference intensity, normalized edit composer, and certified base-energy candidate projection | `heterodiff.processes.plugin_bridge_sampler` | **Implemented and incrementally audited for a deterministic no-RNG reference-clock preflight and one sampled reference candidate. It does not construct the controlled clock, integrate the learned exit rate, draw a waiting time, or admit a reverse path sampler.** |
| Mixed CTMC--OU known-law oracle with a type-changing edge | `heterodiff.theory.mixed_hybrid_oracle` and `heterodiff.theory.mixed_hybrid_conditional_oracle` | **Implemented and incrementally audited only for cap one, exactly two positive unequal-dimensional Gaussian types, and a positive two-way replacement edge. The forward law, backward information/Doob controls, and a separate cap-two multiplicity companion are exact-oracle evidence; this is not a general-cap conditional RNG/path sampler.** |
| Exact compact conditional-path oracle | `heterodiff.theory.mixed_hybrid_conditional_sampler` | **Implemented and incrementally audited only for the preceding cap-one/two-type Gaussian known law. It samples the right-end conditional marginal, runs the exact forward reference path, and reverses endpoints/times/edits with finite-resolution refusals. It is not the learned/general plug-in split-step sampler.** |
| Staged decision-word-free rejection predecision reference semantics | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization` | **Implemented as checkpoint forty-two and mapped in its [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md). It binds the exact CP41 owner, hypothesis object, \(V/W\) coordinate partition, and transitive CP36/CP37 ancestry. Its partial executable \(G^{42}_{r,j}:D^M\rightharpoonup\{F_{37}\}\mathbin{\dot\cup}\mathcal R\) accepts proposal/scoring words only. On calls whose direct CP28/CP30 stages do not refuse, it scores every attempt before quota construction and returns a complete ready-row tuple or modeled quota-certification failure. A separate \(H^{42}\) fully preflights \(W\) before its first ready-row comparison and applies exact first-success/exhaustion semantics. Preparation failure is retained in the public schema but reserved, non-executable, and outside \(G^{42}\)'s image. The sealed witness retains and digest-binds the full supplied successful CP37 result for custody, including its decision records/words and outcome; the parity comparison is limited to the predecision/threshold projection, the witness contains no CP42 applied-\(H^{42}\) record, and it asserts no \(W\)/outcome or failure-fiber parity. CP42 does not prove universal live CP36/CP37 failure equivalence, discharge CP41's factorization hypothesis, establish a live source/initializer law, materialize numeric fibers or masses, or admit a path or sampler. Focused execution, the additive supplement, CP41 regression, static gates, and final independent review are complete; the disposition is PASS WITH EXPLICIT SCOPE LIMITS.** |
| Supplied-word initial-rejection reference-factorization closure | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure` | **Implemented as checkpoint forty-three and mapped in its [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md). For one fixed certified owner/runtime and CP41's exact \(V/W\) partition, it defines \(G^{43}_{r,j}\), the private semantic `_apply_trusted` kernel \(H^{43}_{\mathrm{sem}}\), and the combined \(T^{43}_{r,j}(V,W)=H^{43}_{\mathrm{sem}}(G^{43}_{r,j}(V),W)\). Only the exact declared CP28/CP30 exception classes become \(F_{36}\); CP42's exact \(F_{37}\) is retained. Semantic \(H^{43}_{\mathrm{sem}}\) passes failures without \(W\) access and fully preflights \(W\) on ready rows. Public `apply_decision_words` is the replay facade and replays \(G^{43}\) for custody, so public failure pass-through requires deterministic replay stability. The exact-text, digest-bound reviewed F37 argument leaves the 3072-digit adaptive floor-separation route and natural F37 reachability unresolved. `construction_contract_enforced=True` does not override `loaded_code_integrity_certified=False`. CP43 closes only its defined supplied-word reference construction under explicit premises; it does not prove live CP36/CP37 factorization, discharge CP41's live-parent premise, establish a Philox/source law, materialize numeric masses, or admit an initializer, path, or sampler. Frozen execution and audit evidence is recorded below; disposition: PASS WITH EXPLICIT SCOPE LIMITS.** |
| One-allocation factorized initial-rejection execution adapter | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter` | **Checkpoint forty-four binds one exact CP43 owner and transitive CP37/CP36/CP27 ancestry. For one valid request it makes one adapter-level CP27 `allocate` call for the complete interleaved rejection capsule; the inherited CP27 API still performs its own deterministic internal validation replay. It flattens \(Z\), verifies the exact CP36-derived and CP43 split/join partition \(Z\leftrightarrow(V,W)\), and calls CP43 `evaluate_and_apply` once. On calls that return after final custody, the CP44 and CP43 canonical semantic projections agree by construction. Pre- and post-combined refusals produce no CP44 result and are neither \(F_{36}\) nor \(F_{37}\). Public CP44 validation is structural and invokes no allocation, CP43 \(G/H\), CP36 `prepare`, or CP37 `decide`. The CP41-form pushforward applies only to an abstract semantic map under fixed-runtime deterministic replay-stable total \(G^{43}\) and product-uniform \(Z\). CP44 bypasses but does not prove equivalence to the legacy CP36/CP37 route and does not discharge CP41's original premise. Natural \(F_{37}\) reachability remains unresolved; no live Philox law, unconditional adapter law, numeric source/refusal/fiber mass, initializer/path/sampler admission, or scientific/model/generality claim follows. Frozen focused, static, exact-string, and independent-audit evidence is recorded below; CP43/CP42 execution records are inherited by exact hash and were not freshly rerun. Disposition: PASS WITH EXPLICIT SCOPE LIMITS.** |
| Fixed-address source-support obstruction | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction` | **Checkpoint forty-five binds exact CP44 and transitive CP36/CP27/CP26 ancestry and records the negative live-source boundary. A returned fixed request has point-mass source TV `1-D^(-L)` from product uniform. A deterministic successful capsule map driven by at most k free uint64 coordinates has conditional-success source TV at least `1-D^(k-L)` when L>k, without success/value independence. This gives no output-TV lower bound, because a constant semantic map erases the discrepancy. CP45 allocates no source, executes no CP43/CP44 semantics, and leaves caller/global RNG state unchanged while disclosing the inherited deterministic local Philox ancestry probe. It establishes no live uniformity/independence, refusal probability, unconditional law, randomness, initializer/path/sampler admission, or scientific/model/generality claim. Its frozen 20/20 focused pass, unchanged post-run hashes/static gates, and independent `P0=P1=P2=0` review support PASS WITH EXPLICIT SCOPE LIMITS.** |
| Explicit fixed-request and external finite request-law source models | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract` | **Checkpoint forty-six binds exact CP45 ancestry and separates deterministic fixed-request replay from a declarative finite exact-rational PMF over the two uint64 request coordinates. Given a positive named event, the fixed source has exact TV `1-D^(-L)` and external support s yields capsule support at most s and TV at least `1-s/D^L`. Acquisition and returned-result events are distinct; positivity is required but unproved. The 4,096-atom declaration cap is separate from the analytic `D^2` surface theorem, and inherited `L>2` excludes product-uniform complete capsules on that surface. Support at least `D^L` is necessary but insufficient; exact uniformity is equivalent to conditional mass `D^(-L)` on every output fiber. CP46 certifies neither external-law realization nor fiber balance, and no output-TV lower bound follows. Ordinary models are cached descriptors with optional separate live-ancestry revalidation. Frozen 24/24 evidence, exact enumerations, static gates, hashes, and independent `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS; no event probability, unconditional law, randomness/freshness/independence, initializer/path/sampler, or scientific/model/generality claim follows.** |
| External full-capsule execution adapter | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter` | **Checkpoint forty-seven binds exact CP46--CP43 ancestry to one direct provider callback returning an exact tuple of L uint64 words. The interface has exactly `D^L` possible returns and identity ingestion is bijective, but provider product uniformity, IID draws, totality, and value-independent success remain external premises. One bounded owner-lifetime draw identifier is atomically retired before the at-most-once provider call; duplicate identifiers refuse before the provider, failures do not roll back an API-mediated retirement, and equal values under distinct identifiers are legal. Successful execution uses CP43 split/join and one combined evaluation with no CP27 allocation or CP44/CP36/CP37 execution; validation is structural and nonreplaying. Frozen 31/31 evidence, post-run fast/static gates, hashes, and independent `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS. No live law, randomness, IID/freshness, global uniqueness, concurrent semantic-safety, adaptive-retry, output-TV, initializer/path/sampler, or scientific/model/generality claim follows.** |
| Exact byte-source full-capsule execution | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution` | **Checkpoint forty-eight constructs a private CP47 provider over exact CP46--CP43 ancestry and exposes only the `system-os-urandom-operational` and `external-exact-byte-block-unverified` profiles. A reached boundary makes one direct three-argument backend call for exact built-in bytes of length `8L`, with no coercion, retry, filter, fallback, or replacement. The fixed manual big-endian byte/word map is bijective and preserves source-space TV; jointly uniform complete blocks map to product-uniform words, whereas byte marginals do not suffice. A returned law additionally requires positive complete return mass and value-independent complete CP48 success, and sequence IID requires the corresponding joint premises. CP47 remains the sole retirement/semantic authority; successful results retain exact raw bytes, words, and CP47 custody. The system profile certifies only one cached ordinary `os.urandom` Python-API call site and no OS law, entropy, syscall, or cryptographic property. Frozen 37/37 evidence, post-run 28/28 fast/static gates, hashes, and independent `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS; a retained P3 note keeps asynchronous-task safety explicitly uncertified. No backend law/totality, general concurrency/reentry/async safety, unconditional returned-result law, output-TV, initializer/path/sampler, or scientific/model/generality claim follows.** |
| Assumption-gated full-source law admission | `heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission` | **Checkpoint forty-nine binds one exact CP48 owner and exact CP47--CP43 ancestry to the sole explicitly unverified external assumption declaration. For each individually fixed request and fixed pre-operation state, its pointwise object-semantic pushforward and TV data-processing statement requires fresh-draw/capacity/preboundary admissibility, almost-sure exact-block return, unconditional joint full-block uniformity, all-block post-boundary complete success, and fixed-runtime deterministic replay-stable typed-total CP43/CP42 semantics. The enriched tuple preserves four statuses and the canonical bit-exact CP42 value; a selected record separately retains the exact runtime object by identity. Nontotal return reweights by the complete success likelihood, and marginal one-call premises do not imply sequence IID or adaptive laws. Describe, certification, admission, and ordinary validation acquire no bytes and execute no semantics; explicit live ancestry revalidation may replay ancestry only. A real all-zero one-attempt selected custody witness proves a nonempty enriched and configuration fiber only under the abstract premises. Frozen 28/28 evidence, an independent 21/21 fast pass, static gates, stable hashes, and independent `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS. No backend/OS/callback law, totality, operational realization, unconditional returned law, sequence/adaptive law, refusal totalization, global uniqueness, legacy equivalence or premise discharge, initializer/path/sampler, Test-28 closure, scientific/model/generality, or manuscript claim follows.** |
| General plug-in split-step sampler | `heterodiff.processes.plugin_bridge_sampler` | **The scoped implementation chain now extends through CP49: CP39's selected-state coordination, CP40's fixed-batch target, CP41's conditional abstract source ledger, CP42's staged predecision evaluator, CP43's supplied-word factorization closure, CP44's one-allocation adapter, CP45's fixed-address/support obstruction, CP46's explicit fixed-versus-declared-external source descriptors, CP47's external full-capsule execution adapter, CP48's exact byte-source boundary, and CP49's assumption-gated pointwise semantic-law admission are implemented within their stated boundaries. CP39--CP49 are each PASS WITH EXPLICIT SCOPE LIMITS. CP47's frozen 31/31 record closes only the exact provider interface, identity ingestion, local retirement, and execution custody; CP48's frozen 37/37 record adds only the two operational byte-source bindings, manual bijection, and exact byte/word custody; CP49's frozen 28/28 record adds only a theorem owner under an explicitly unverified external premise and structural admission of returned CP48 records. None realizes a product-uniform/IID backend law or an unconditional returned-result law. CP44 still does not discharge CP41's live-parent premise or prove universal live CP36/CP37 equivalence. Ideal continuous-route recovery, unconditional completion, an exact frozen-jump law, semantic SIR or exact ideal rejection, a live/global initializer source law, numeric CP36/CP37 failure masses, adaptive source chronology, general initializer admission, semantic tag-3 payloads, global address guarantees, Brownian coupling, paths, drift integration, and the complete sampler remain pending.** |

The implementation inventory now contains forty-nine separately mapped
checkpoints. CP49 is frozen at its assumption-gated full-source-law admission
boundary, with focused, independent-fast, static, and independent-audit
evidence complete. The inventory is:

1. `src/heterodiff/theory/configuration_reference.py` (**implemented; see the
   incremental code audit**);
2. `src/heterodiff/processes/reversible_hybrid_reference.py` (**implemented;
   see the
   incremental code audit**);
3. `src/heterodiff/theory/reverse_energy_objective.py` (**implemented; see the
   incremental code audit**);
4. `src/heterodiff/theory/association_observation.py` (**implemented; see the
   incremental code audit**);
5. `src/heterodiff/theory/association_preconditioner.py` (**implemented; see
   the incremental code audit**);
6. `src/heterodiff/models/configuration_energy_torch.py` (**implemented; see
   the incremental code audit**);
7. `src/heterodiff/processes/plugin_bridge_sampler.py` (**first dependency
   slice implemented; see the
   incremental code audit; the complete
   conditional sampler remains pending**); and
8. `src/heterodiff/theory/mixed_hybrid_oracle.py` and
   `src/heterodiff/theory/mixed_hybrid_conditional_oracle.py` (**implemented
   in the scoped cap-one/two-type known-law setting; see the
   incremental code audit; a separate
   cap-two test checks multiplicity, while the general learned conditional
   path sampler remains pending**); and
9. `src/heterodiff/theory/mixed_hybrid_conditional_sampler.py` (**implemented
   only as an exact compact path-space reversal sampler for dependency 8; see
   the incremental code audit;
   the learned/general split-step sampler remains pending**); and
10. `src/heterodiff/processes/plugin_bridge_sampler.py` (**extended with the
    deterministic no-RNG reference-intensity preflight required before a
    future waiting-time draw; see the
    incremental code audit; the
    controlled envelope, waiting/acceptance RNG, and path sampler remain
    pending**); and
11. `src/heterodiff/theory/association_preconditioner.py` (**extended with a
    sealed fixed-observation analytic guide range and coordinate-regularity
    certificate; see the
    incremental code audit.
    It certifies the real-arithmetic conjugate guide under normalized
    probability-simplex and Markov-kernel semantics, not the represented
    pointwise evaluator or operational sampler**); and
12. `src/heterodiff/theory/association_operational_guide.py` (**implements a
    sealed fixed-observation, successful-only range gate for represented
    point values and legal jump edits; see the
    incremental code audit. It preserves
    admitted raw log values bitwise and refuses nonfinite, foreign, stale, or
    out-of-range results. Its coarse interval certificate is not a small
    forward-error analysis, a coordinate-derivative certificate, a liveness
    theorem, or operational sampler admission**); and
13. `src/heterodiff/models/configuration_residual_torch.py` (**implements the
    distinct general typed conditional-residual value, same-condition
    state-pair difference, physical-coordinate derivative interfaces, cubic
    clean-hold gate, and residual-role checkpoint certificate; see the
    incremental code audit. Its
    fixed-vector conditioner remains externally prepared and only
    procedurally digest-bound, and the module does not implement the
    joint/product population, nuisance logit, combined physical potential,
    controlled clock, or sampler**); and
14. `src/heterodiff/models/configuration_potential_composer_torch.py`
    (**implements the provenance-bound successful log-space composition of
    the certified base edge, range-gated guide edit, and certified residual
    edge for one active process-valid candidate; see the
    incremental code audit.
    It returns a one-round represented sum and separate time-specific
    mathematical/operational aggregate log witnesses, but no exponentiated
    rate envelope, total exit, waiting/acceptance decision, drift, path, or
    sampler**); and
15. `src/heterodiff/theory/association_totalized_jump_guide.py`
    (**implements the fixed-observation totalized operational-surrogate point
    and jump-edit layer; see the
    incremental code audit. It preserves
    successful range-gated raw values, maps only typed numerical/range point
    failures to one certified midpoint after a full capped-domain resource
    preflight, and stores exact-rational operational endpoint differences. It
    does not preserve the analytic target or supply derivatives, drift, a
    rate-space envelope, clock, randomness, path, or sampler**); and
16. `src/heterodiff/models/configuration_totalized_jump_residual_torch.py`
    (**implements the detached, checkpoint-private, jump-only residual point
    and same-condition endpoint-difference layer; see the
    incremental code audit. It
    preserves every successful checkpoint-thirteen point bitwise and maps only
    the exact typed active tiny-gate refusal to the exact-rational cubic gate
    times the represented bounded-core value, rounded once. It does not claim
    the exact real neural residual or conditional/posterior target and supplies
    no derivatives, drift, rate-space envelope, clock, randomness, path, or
    sampler**); and
17. `src/heterodiff/models/configuration_totalized_jump_potential_composer_torch.py`
    (**implements the target-explicit operational-surrogate point/edge composer
    for one active process-valid birth, death, or replacement candidate; see
    the
    incremental code audit.
    It evaluates a checkpoint-private base and the two certified totalizers,
    composes their exact represented endpoint fractions, and rounds the
    aggregate once. It supplies no exponentiation, rate envelope, total exit,
    clock, RNG, derivative/drift, initializer, path, or sampler**); and
18. `src/heterodiff/models/configuration_totalized_jump_rate_envelope_torch.py`
    (**implements certified rate-space exponentiation for checkpoint
    seventeen's explicit operational-surrogate edge and no-RNG instantaneous
    and global controlled-total-exit upper bounds; see the
    incremental code audit. It
    uses the exact rational edge rather than the trace-only rounded edge,
    returns a correctly rounded finite normal candidate integrand on success,
    and treats structural-zero reference intensity exactly. It does not
    compute the active total exit, authorize a route draw, preserve rounded
    detailed balance, or supply waiting/acceptance randomness,
    derivatives/drift, initialization, paths, or a sampler**); and
19. `src/heterodiff/processes/plugin_bridge_operational_thinning.py`
    (**implements one successful-return local operational wait/route/accept
    sequence; see the
    incremental code audit.
    It resolves the ideal-prefix inverse-exponential clock with inclusive real
    endpoint eligibility and strict represented-interior return, continues one
    Philox stream through the inherited finite-resolution route, and samples
    the exact represented \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\)
    Bernoulli. It supplies no repeated loop, continuous-destination operational
    fixture, counter-keyed lineage, drift/Strang integration, initialization,
    path, liveness theorem, or full sampler**); and
20. `src/heterodiff/processes/plugin_bridge_operational_thinning_loop.py`
    (**implements bounded successful-return coordination of checkpoint
    nineteen; see the
    incremental code audit.
    Rejections advance the represented cursor and reuse the exact parents;
    acceptances immediately refresh the process-owned intensity and operational
    envelope at the fixed generative time. A result requires a terminal
    structural-zero or right-endpoint waiting record. The exact 0--64 proposal
    budget is a refusal cap, so an active cap hit returns no truncated result
    and consumes no speculative next wait. It supplies no exact real-time
    Poisson/CTMC or unconditional frozen-jump law, exact route law, continuous-
    destination operational evidence, counter-keyed stream, lineage,
    drift/Strang integration, initialization, path, liveness theorem, or full
    sampler**); and
21. `src/heterodiff/processes/plugin_bridge_continuous_route_evidence.py`
    (**implements reconstructable same-runtime evidence around one delegated
    checkpoint-nineteen route; see the
    incremental code audit.
    It replays the frozen process-owned composer from the exact pre-route
    Philox snapshot and requires the candidate digest and exact post-state to
    agree. Record-specific fixtures cover continuous birth and both directions
    of a genuine unequal-dimensional positive-fibre reset. It supplies no
    exact categorical/integer/Gaussian law, bounded normal-word trace,
    distribution recovery, liveness, path, or full sampler**); and
22. `src/heterodiff/processes/plugin_bridge_operational_thinning_loop_route_evidence.py`
    (**implements an additive route-evidence overlay for one successfully
    returned checkpoint-twenty loop; see the
    incremental code audit.
    It captures exact loop-entry/exit Philox snapshots, reconstructs every
    checkpoint-nineteen waiting and acceptance raw-word prefix, inserts and
    validates one checkpoint-twenty-one route witness per completed proposal,
    replays the terminal waiting prefix, and requires the exact full-loop exit
    snapshot. It supplies no ideal route law, unconditional completion,
    liveness, analytic-target preservation, counter-keyed lineage, drift,
    initialization, path, or full sampler**); and
23. `src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py`
    (**implements direct, unhashed, injective-within-schema NumPy Philox address
    receipts and a deterministic persistent-lineage overlay on one fully
    revalidated checkpoint-twenty-two result; see the
    incremental code audit.
    Its positional bootstrap distinguishes equal-valued duplicates; accepted
    edits preserve exact source/survivor custody, allocate fresh monotone IDs,
    retain retired IDs, and stable-sort only by the event model key; rejection
    and terminal custody reuse the exact lineage state. It does not make the
    parent execution proposal-keyed, consume any issued receipt, enforce global
    run-ID or duplicate-address uniqueness, consume or couple Brownian streams,
    implement drift or initialization, construct a path or Strang step, or
    admit the full sampler**); and
24. `src/heterodiff/processes/plugin_bridge_counter_keyed_operational_epoch_loop.py`
    (**implements the bounded counter-keyed operational-epoch successor; see
    the
    incremental code audit.
    It owns direct tag-6 epoch addresses, uses one reconstructed local stream
    continuously through each active wait/route/accept sequence, integrates
    exact checkpoint-twenty iteration, checkpoint-twenty-one route-evidence,
    and checkpoint-twenty-three lineage-transition records for every proposal,
    and accepts no caller RNG. Active stochastic exhaustion remains on tag 6;
    deterministic holds bind a tag-2 receipt with zero word consumption. It
    consumes neither legacy tag-1 proposal receipts nor occurrence,
    initializer, or Brownian streams and supplies no exact jump law, path,
    drift/Strang step, liveness theorem, or full sampler**); and
25. `src/heterodiff/processes/plugin_bridge_counter_keyed_initializer_stream_consumption.py`
    (**implements bounded bootstrap-only tag-3 raw-prefix custody; see the
    incremental code audit.
    It binds the exact checkpoint-twenty-four and checkpoint-twenty-three
    owners, preflights at most 64 positional initial occurrences and their
    complete positive count plan, fixes step zero, and consumes at most 4,096
    raw words per occurrence and 65,536 in aggregate. It preserves the exact
    lineage-state object, accepts no caller RNG, and retains same-runtime
    pre/post snapshot replay with no upper carry. It defines no initializer
    output law; a separate global control domain, general initializer,
    Brownian coupling, drift, path, and full sampler remain pending**); and
26. `src/heterodiff/processes/plugin_bridge_counter_keyed_global_initializer_control.py`
    (**implements the bounded law-neutral pre-cardinality tag-7 control
    namespace; see the
    incremental code audit.
    It binds exact checkpoint-twenty-five/twenty-four/twenty-three ancestry,
    preflights a strictly lexicographic plan of at most 64 stage/attempt
    addresses, and consumes at most 4,096 `raw64` words per stream and 65,536
    in aggregate at key `(run_id, 7)`, counter `(0, initialization_index,
    stage_index, attempt_index)`. It accepts no caller RNG and retains exact
    same-runtime pre/post replay with no upper carry. It defines no stage,
    attempt, branch, retry, output-transform, initializer-law, lineage-mapping,
    or tag-3 coordination semantics; Brownian coupling, drift, path, and full
    sampler remain pending**); and
27. `src/heterodiff/processes/plugin_bridge_counter_keyed_initializer_protocol.py`
    (**implements fixed, nonadaptive strategy-specific allocation over the
    exact checkpoint-twenty-six owner; see the
    incremental code audit.
    It freezes stages 0--4 for enumeration, rejection, SIR, and a branch-free
    reference candidate; uses injective multiblock work-item coordinates;
    materializes the complete bounded parent plan; and retains exact plan,
    entry, raw-word, and replay custody without a caller RNG. It takes no
    branch and defines no output transform, initializer law, configuration,
    lineage mapping, tag-3 coordination, Brownian coupling, drift, path, or
    full sampler**); and
28. `src/heterodiff/processes/plugin_bridge_counter_keyed_reference_initializer.py`
    (**implements the fixed-word-budget, no-retry finite transformer for only
    the
    exact checkpoint-twenty-seven reference strategy; see the
    incremental code audit.
    It derives an exact manifest from the frozen capped-Poisson ancestry,
    consumes the canonical (1+N+ND) parent layout, applies positive uint64
    Hamilton quotas to count/type categories, transforms every slot and
    coordinate-padding word before decoding cardinality, and returns a
    duplicate-stable canonical configuration. Its distributional statement is
    only the explicit finite pushforward under hypothetical product-uniform
    words. It certifies no actual Philox randomness, exact continuous
    reference law, other initializer strategy, conditional/tilted initializer,
    lineage/tag-3 coordination, Brownian coupling, drift, path, or full
    sampler**); and
29. Checkpoint-29 diagnostic and custody tooling:
    `src/heterodiff/processes/plugin_bridge_counter_keyed_reference_initializer_diagnostic.py`,
    `src/heterodiff/processes/plugin_bridge_counter_keyed_reference_initializer_diagnostic_fixtures.py`,
    `src/heterodiff/artifacts/reference_initializer_diagnostic_artifact.py`,
    `src/heterodiff/experiments/reference_initializer_diagnostic_production.py`,
    `src/heterodiff/artifacts/reference_initializer_diagnostic_artifact_verifier.py`,
    and `research/tools/run_reference_initializer_diagnostic.py`
    (**implements the preregistered finite-grid diagnostic, immutable artifact
    encoding, one-shot STARTED-v2/terminal-v2 execution custody, and independent
    verification summarized in the
    execution audit.
    It is evaluation and custody tooling, not an initializer or sampler
    dependency, and it promotes no scientific claim**); and
30. `src/heterodiff/models/configuration_initial_tilt_composer_torch.py`
    (**implements the deterministic time-zero operational point-factor
    prerequisite for the selected \(\Pi_N\) base; see the
    incremental code audit.
    It evaluates the totalized guide at reverse time zero and the totalized
    residual at direct time \(S\), lifts their represented binary64 values to
    exact rationals, sums them, and rounds once. The learned base energy and a
    separate observation-only nuisance are excluded. It supplies a replayable
    outward point interval under process-local procedural custody, but no
    exponentiation, normalization, support enumeration, rejection, SIR,
    selection, RNG, initialized configuration, lineage mapping, tag-3 payload
    coordination, path, or sampler admission**); and
31. `src/heterodiff/models/configuration_initial_tilt_atomic_enumerator_torch.py`
    (**implements exact complete enumeration only for a resource-admitted
    all-atomic process reference; see the
    incremental code audit.
    It exact-renormalizes represented raw type weights, emits count vectors by
    cardinality then lexicographic order, stores exact unnormalized
    multiplicity-corrected base coefficients and their completeness
    normalizer, and attaches one replay-validated checkpoint-thirty point to
    every state. It refuses positive-dimensional types and supplies no
    normalized masses, point-factor exponentiation, tilted normalization,
    selection, rejection, SIR, RNG, checkpoint-twenty-seven binding,
    initialized configuration, continuous codebook, lineage mapping, tag-3
    coordination, path, or sampler admission**); and
32. `src/heterodiff/models/configuration_initial_tilt_atomic_selector_torch.py`
    (**implements deterministic preparation of the bounded all-atomic
    operational tilted law and exact selection from one explicit uint64 word;
    see the
    incremental code audit.
    It constructs directed exponential and normalized-mass intervals,
    exact-normalizes a positive rational proxy, forms positive Hamilton quotas
    over \(2^{64}\), and records rigorous ideal-to-proxy and ideal-to-dyadic TV
    bounds. It does not source or certify the word, bind checkpoint twenty-seven
    stage 0, sample the ideal transcendental law exactly, admit an initializer,
    support mixed/continuous states, coordinate lineage/tag-3 payloads, or
    construct a path or sampler**); and
33. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_atomic_selection.py`
    (**implements the exact checkpoint-twenty-seven stage-0 word binding for the
    checkpoint-thirty-two all-atomic selector; see the
    incremental code audit.
    It validates the supplied preparation before allocation, requires exact
    shared reference-composer, guide, and residual ancestry, requests only
    enumeration with budget one, empty work-item blocks, and one selection word,
    retains exact plan/address/raw-word custody, and forwards the sole word
    unchanged. For fixed preparation \(p\), its law statement replaces the
    live word source by an abstract uniform uint64 \(U\), explicitly not
    identified with the live checkpoint-thirty-three word source, though their
    uint64 values may coincide, so that \(f_p(U)\sim Q_p\). Separately, the
    fixed preparation inherits
    \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\). The live
    fixed-address word and output are deterministic point masses. It does not
    certify actual Philox uniformity, independence, randomness, or global
    one-shot use; sample \(P_{\mathrm{operational},p}\) exactly; admit an initializer; support
    mixed/continuous states or other strategies; coordinate lineage/tag-3
    payloads; or construct a path or sampler**); and
34. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_atomic_admission.py`
    (**implements the fixed all-atomic initial-configuration constructor and
    counterfactual ideal-word theorem; see the
    incremental code audit.
    Its factory canonically fixes context, complete checkpoint-thirty-one
    enumeration, checkpoint-thirty-two preparation, and exact checkpoint-
    thirty-three ancestry. The live call accepts only run and initialization
    indices. Each successful live construction consumes exactly one inherited
    stage-0 parent word and returns a configuration valid as an initial state
    with deterministic same-address replay. For fixed preparation \(p\), only
    an abstract ideal replacement
    \(U\sim\operatorname{Unif}(\mathrm{uint64})\), not identified with the
    live word source, gives
    \(f_p(U)\sim Q_p\); the live fixed-address output is a point mass. It
    certifies no live initializer distribution or admission, actual RNG law,
    global address uniqueness, mixed/continuous support, other strategy,
    lineage/tag-3 coordination, path, or sampler. Its historical module name
    promotes no admission claim**); and
35. `src/heterodiff/processes/plugin_bridge_counter_keyed_mixed_reference_constructor.py`
    (**implements the fixed-index finite reference construction, bootstrap-
    lineage, and dimension-shaped tag-3-prefix coordination checkpoint; see
    the incremental code audit.
    Its complete-capsule law is counterfactual and configuration-only, its
    structural-TV expression is an upper bound, and its codebook/Gaussian
    fiber TV-one statement is conditional. It certifies no live initializer
    law, cross-initialization tag-3 disjointness, path, or sampler**); and
36. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_preparation.py`
    (**implements fixed-budget rejection-stage-1 proposal transformation and
    point-score preparation; see the
    incremental code audit.
    Every attempt uses the exact CP28 proposal layout plus one reserved
    uninterpreted word and records CP30's exact represented \(q\), global exact
    \(U\), and reduced rational witness \(q-U\le0\). Its conditional abstract
    theorem assumes distinct-coordinate iid-uniform uint64 words and uses a
    total success-batch/failure codomain. It supplies no live word law, failure
    probability, success-conditional law, exponentiation, decision,
    acceptance, selection, initializer admission, lineage/tag-3 coordination,
    path, or sampler**); and
37. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_decision.py`
    (**implements conservative finite-resolution rejection decisions over the
    exact CP36 owner and batch; see the
    incremental code audit.
    It builds every exact quota before any word-to-quota comparison, evaluates
    the inherited words only through the first acceptance or full bounded
    exhaustion, and retains the selected CP36 configuration by identity and
    digest. Its fixed-data product law requires separate abstract iid-uniform
    words. Separately, a common-uniform coupling of independent-coordinate
    ideal and dyadic Bernoulli sequences gives the strict \(A/2^{64}\)
    ideal-outcome comparison. It supplies no
    live word law, exact ideal rejection, failure probability, success-
    conditional law, initializer admission, lineage/tag-3 coordination, path,
    or sampler**); and
38. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law.py`
    (**implements the exact counterfactual fixed-batch dyadic law over one
    CP37 result; see the
    incremental code audit.
    Its direct \(B\) excludes words, decisions, outcome, and word-binding
    parent digests; exact first-success/exhaustion masses are stably aggregated
    across duplicate configurations; and the selected law exists only for
    \(Z_B>0\). A separate common-uniform comparison gives strict augmented TV
    \(<A/2^{64}\) without success-conditioned reuse. It supplies no live law,
    CP36 failure/successful-batch law, generic initializer admission,
    initialization-index-safe lineage/tag-3 coordination, path, or sampler.
    Its no-cache focused and CP37 regression suites passed 45/45 and 44/44,
    respectively; the disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
39. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_coordination.py`
    (**implements construction-time coordination over one exact CP38 result;
    see the
    incremental code audit.
    Selection retains the exact CP38 configuration and CP37 attempt, queries
    reverse-time-zero intensity, maps position \(j\) to CP23 bootstrap serial
    \(j+1\), and consumes \(\max(1,d_j)\) CP39-local uninterpreted words at
    key `(run_id, 3)` and counter
    `(0, initialization_index, j+1, selected_attempt_index+1)`. Selected-empty
    retains intensity and empty lineage with no stream; exhaustion is an exact
    no-state result without selected-branch child construction. The positive
    suffix is disjoint only from valid legacy suffix-zero tag-3 addresses. It
    supplies no live law, payload/coordinate semantics, global/one-shot/cross-
    bootstrap/merge/fork guarantee, cryptographic or cross-runtime-portability
    guarantee, generic admission, Brownian/path, or sampler.
    Final disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
40. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_admission.py`
    (**implements the exact finite-resolution fixed-\(B\) rejection target,
    selected-conditioned comparison, and narrow structural state/no-state
    boundary over one exact CP39 result; see the
    incremental code audit.
    It calls CP39 once; preserves the actual selected state rather than a
    duplicate-aggregation representative; admits selected-empty; and retains
    the target but no state on exhaustion. The raw strict comparison is
    \(2A/(2^{64}Z_B)\), while the clipped display is non-strict. At \(Z_B=0\),
    optional probability and numeric-bound values are absent, the corresponding
    flags remain present and false, and fixed comparison/proof metadata remains
    present. It supplies no live/unconditional initializer law, CP36 failure
    law, exact ideal rejection, global normalized tilt, all-strategy general
    initializer, semantic tag-3 payload,
    Brownian/path, or sampler. Source and tests are frozen and 45 focused tests
    passed; inherited exact-hash CP39 parent evidence remains applicable, and
    the final disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
41. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law.py`
    (**defines an abstract product-uniform failure-aware source law conditional
    on an explicit unproved factorization hypothesis; see the
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md).
    It partitions the complete CP36 abstract word template into proposal/
    scoring \(V\) and reserved-decision \(W\); distinguishes \(F_{36}\)
    preparation failure, \(F_{37}\) quota failure, exhaustion, and
    configuration atoms; and records an exact symbolic normalized mixture.
    The \(\rho=0\) laws agree; for positive \(\rho\), augmented TV is strictly
    below \(\rho A/2^{64}\); and when \(S_Q>0\), the selected comparison uses
    the factor-one bound through the augmented-law TV distance divided by
    \(\max(S_P,S_Q)\). No dyadic selected
    law or comparison bound is defined when \(S_Q=0\). No fiber or numeric
    mass is materialized, and no CP36--CP40 operational call is made. It
    supplies no
    proof of factorization, live Philox/source/initializer law, exact ideal
    rejection, global analytic normalization, general admission, Brownian/
    path, or sampler claim. The no-cache, warnings-as-errors focused suite
    passed 28/28; the disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
42. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization.py`
    (**implements the bounded partial staged CP41-bound reference semantics
    \(G^{42}_{r,j}(V)\) followed by \(H^{42}(G,W)\); see the
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md).
    It binds the exact \(V/W\) partition and CP36/CP37 ancestry. On calls whose
    direct CP28/CP30 stages do not refuse, it transforms and scores all attempts
    before quota construction and returns `ready` only with a complete quota
    tuple. It fully preflights \(W\) before a ready-result comparison and
    deterministically replays both stages. The sealed witness retains and
    digest-binds the full supplied successful CP37 result for custody,
    including its decision records/words and outcome. Its parity comparison is
    limited to the predecision/threshold projection; it contains no CP42
    applied-\(H^{42}\) record and asserts no \(W\)/outcome or failure-fiber
    parity. \(F_{36}\) remains reserved and outside the
    executable image, and the
    checkpoint proves neither universal live-failure equivalence nor CP41's
    factorization premise. It supplies no live Philox/source/initializer law,
    numeric source masses, exact ideal rejection, general admission, path, or
    sampler. Focused execution, the additive boundary supplement, CP41
    regression, static gates, and final independent review are complete; the
    disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
43. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure.py`
    (**constructs the CP43-defined supplied-word reference factorization; see
    the [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md).
    It binds one exact CP42 owner and CP41 \(V/W\) partition. Its public
    `evaluate_predecision` is the \(V\)-only \(G^{43}\); the private
    `_apply_trusted` is \(H^{43}_{\mathrm{sem}}\); and `evaluate_and_apply`
    performs one \(G^{43}\) followed by one \(H^{43}_{\mathrm{sem}}\). Only the exact
    declared CP28/CP30 errors become \(F_{36}\), and CP42's exact \(F_{37}\) is
    retained. \(H^{43}_{\mathrm{sem}}\) passes failures without \(W\) access and
    fully preflights ready \(W\) before comparison. The public replay facade
    `apply_decision_words` replays \(G^{43}\) for custody, so public
    failure pass-through requires deterministic replay stability. The exact-
    text, digest-bound reviewed F37 argument leaves the 3072-digit adaptive
    floor-separation route unresolved. The selected runtime fingerprint is
    procedural, and `loaded_code_integrity_certified=False`. The narrow flags
    are
    `cp43_defined_reference_factorization_discharged_by_construction=True`,
    `abstract_product_uniform_corollary_recorded_under_explicit_premises=True`,
    and `construction_contract_enforced=True`. This closes no live
    CP36/CP37 factorization, CP41 live-parent premise, Philox/source law,
    numeric mass, initializer, path, sampler, or scientific claim. Its
    disposition is PASS WITH EXPLICIT SCOPE LIMITS**); and
44. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter.py`
    (**defines the CP44 one-allocation factorized execution route; see the
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_code_audit.md).
    It binds one exact CP43 owner and transitive CP37/CP36/CP27 ancestry,
    invokes the exact CP27 `allocate` API once per valid request, and explicitly
    retains the inherited allocation API's internal deterministic validation
    replay. On a call that returns after acquiring a complete capsule \(Z\) and
    passing final custody, it verifies CP36 layout and CP43 split/join custody
    for \(Z\leftrightarrow(V,W)\), invokes CP43's combined operation once, and
    constructs a result whose canonical semantic projection equals that CP43
    result's projection. Pre- and post-combined refusals produce no result and
    are neither \(F_{36}\) nor \(F_{37}\). Its public result validator is
    structural and replays no
    allocation, CP43 \(G/H\), CP36 `prepare`, or CP37 `decide`. The CP41-form
    mixture applies only to an abstract semantic map under fixed-runtime,
    deterministic, replay-stable total \(G^{43}\) and product-uniform \(Z\).
    This new route bypasses rather than proves equivalence to legacy
    CP36/CP37 and does not discharge CP41's live-parent premise. Natural
    \(F_{37}\) reachability, a live Philox/source law, numeric fibers or masses,
    initializer/path/sampler admission, and scientific, model-quality, or
    generality evidence remain absent or unresolved**); and
45. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction.py`
    (**records the exact CP45 source-only obstruction; see the
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md).
    For a fixed returned request it gives
    `TV(delta_z,U_L)=1-D^(-L)`. For a deterministic partial successful capsule
    map driven by at most k free uint64 coordinates it gives conditional-
    success support at most `D^k` and source TV at least `1-D^(k-L)` when
    L>k, with no success/value-independence premise. It makes no source
    allocation or CP43/CP44 semantic call and gives no output-TV lower bound,
    live product-uniform law, initializer, path, sampler, or scientific claim.
    Its authoritative warnings-as-errors suite passed 20/20 in `19448.25 s`;
    unchanged post-run hashes/static gates and independent `P0=P1=P2=0`
    review support PASS WITH EXPLICIT SCOPE LIMITS**); and
46. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
    (**implements the CP46 fixed-versus-external source descriptor boundary;
    see the linked
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md).
    It binds exact CP45 ancestry, exposes deterministic fixed-request replay
    and canonical finite exact-rational request-law declarations, and records
    only positive-event source support and TV consequences. It distinguishes
    acquisition from returned-result conditioning, proves neither event's
    positivity, separates the 4,096-atom declaration cap from the analytic
    two-uint64-coordinate capacity theorem, and records the exact weighted-
    fiber criterion. It realizes no external law, samples no request, and
    establishes no semantic-output TV lower bound, randomness, freshness,
    nondegenerate independence, initializer, path, sampler, or scientific
    claim. Frozen 24/24 evidence, exact enumerations, static gates, hashes,
    and independent `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE
    LIMITS**); and
47. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
    (**implements the CP47 external full-capsule execution boundary; see the
    linked
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md).
    It binds exact CP46--CP43 ancestry and one direct provider callback, requires
    an exact L-word uint64 tuple, ingests it by identity, retires one bounded
    owner-local draw identifier before the at-most-once provider call, and
    passes the split capsule through CP43's combined semantics. Interface
    cardinality `D^L` is not a realized product-uniform or IID law; provider
    and downstream value-dependent failure can bias the returned-result law.
    The retirement contract is neither global nor persistent and gives no
    concurrent semantic-safety or adaptive-retry guarantee. Frozen 31/31
    evidence, post-run fast/static gates, hashes, and independent
    `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS. No live source
    law, randomness, output-TV, initializer, path, sampler, scientific, model-
    quality, generality, or manuscript claim follows**); and
48. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
    (**implements the CP48 byte-source full-capsule execution boundary; see the
    linked
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md).
    It constructs a private CP47 provider over exact CP46--CP43 ancestry,
    exposes only the system operational and exact external unverified byte-
    source profiles, requires one exact `8L`-byte direct backend return at each
    reached boundary, and decodes it with a fixed manual big-endian bijection.
    Joint full-block uniformity, not byte marginals, is the premise for product-
    uniform words; a returned law also requires positive return mass and value-
    independent complete CP48 success, with corresponding joint premises for
    returned-sequence IID. CP47 remains the sole retirement and semantic
    authority. The system profile certifies one cached ordinary `os.urandom`
    Python-API call site only. Frozen 37/37 evidence, post-run 28/28 fast/static
    gates, hashes, and independent `P0=P1=P2=0` audits support PASS WITH
    EXPLICIT SCOPE LIMITS; a retained P3 note keeps asynchronous-task safety an
    explicit nonclaim. No backend or OS law, entropy, totality, general
    concurrency/reentry/async safety, unconditional returned-result law,
    output-TV, initializer, path, sampler, scientific, model-quality,
    generality, or manuscript claim follows**); and
49. `src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
    (**implements the CP49 nonexecuting, assumption-gated full-source law
    admission boundary; see the linked
    [incremental code audit](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md).
    It binds one exact CP48 owner and CP47--CP43 ancestry to a sealed declaration
    whose probability premises remain expressly unverified. For every
    individually fixed request and fixed pre-operation state, the declared
    premises give the pointwise enriched CP43/CP42 object-semantic pushforward
    and its TV data-processing upper bound. The tuple preserves preparation
    failure, quota-certification failure, selection, and exhaustion, retaining
    the canonical bit-exact CP42 configuration value on selection; the result
    separately retains the exact runtime object by identity. Complete-return
    conditioning and sequence/history caveats remain explicit. Description,
    certification, admission, and ordinary validation are source-free and
    semantic-nonreplaying; explicit live revalidation may replay ancestry but
    never bytes or semantic execution. A selected one-attempt all-zero witness
    establishes nonempty enriched/configuration fibers and the
    premise-qualified \(2^{-64L}\) reference-mass lower bound, not an
    operational law or initializer. Frozen 28/28 evidence, an unchanged 21/21
    fast partition, static gates, stable hashes, and independent
    `P0=P1=P2=0` audits support PASS WITH EXPLICIT SCOPE LIMITS. It certifies no
    backend law or totality, operational realization, unconditional returned
    law, sequence/adaptive law, refusal totalization, global uniqueness,
    CP41-premise discharge or universal legacy equivalence, initializer, path,
    sampler, Test-28 closure, scientific/model/generality, or manuscript
    claim**).

Names of remaining unimplemented interfaces may change before their code
freeze. Previously frozen names or artifacts may change only through a new
audit. Checkpoint thirty-eight's mapped surface, checkpoint thirty-nine's
frozen source/test surface, checkpoint forty's evidence-bound frozen
source/test surface, and checkpoint forty-one's evidence-bound frozen
source/test surface may change only through a new audit. Checkpoint forty-two's
source and recovered 29-test primary focused-suite identities are fixed. Its
separately identified additive boundary supplement and overall evidence record
are final and evidence-bound. These artifacts may change only through a new
audit. Checkpoint forty-three's frozen source and focused-test SHA-256 values
are `12977ea4c38c8f5cb595d823e129f0f9dd8e0cadb1a151247d3278464c64fd64` and
`5f8372c4e80e5539e08444170f687af36b755998e6e96ffbdbe57331178f9944`.
The complete execution and audit evidence below is evidence-bound under the
CP43 audit. Checkpoint forty-four's frozen source and focused-test SHA-256
values are
`42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d` and
`e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.
Its complete focused, static, exact-string, and independent-audit evidence is
evidence-bound under the CP44 audit; CP43/CP42 execution records cited there
are inherited by exact hash and were not freshly rerun for CP44. Any CP44
source or focused-test change requires a new audit. Checkpoint forty-five's
frozen source and focused-test SHA-256 values are
`5c430ed18d8c14fd5359858b8a686c521c8cb61f5389b977b4c1f8fdc192bad5` and
`53701f0c59634fe6be32d730e39b16e066cfa9d8879094e7c876e235742f9553`.
Its complete focused, static, and independent-audit record is evidence-bound
under the CP45 audit; any CP45 source or focused-test change requires a new
audit. Checkpoint forty-six's frozen source and focused-test SHA-256 values
are `8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`
and `04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`.
Its complete focused, static, exact-enumeration, and independent-audit record
is evidence-bound under the standalone
[CP46 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md);
any CP46 source or focused-test change requires a new audit. Checkpoint forty-
seven's frozen source and focused-test SHA-256 values are
`2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`
and `46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`.
Its complete focused, static, runtime-fingerprint-regression, and independent-
audit record is evidence-bound under the standalone
[CP47 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md);
any CP47 source or focused-test change requires a new audit. Checkpoint forty-
eight's frozen source and focused-test SHA-256 values are
`7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd`
and `2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282`.
Its complete focused, post-run fast, static, codec, success-conditioning,
retirement-boundary, failure-cleanup, and independent-audit record is evidence-
bound under the standalone
[CP48 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md);
any CP48 source or focused-test change requires a new audit. Checkpoint forty-
nine's frozen source and focused-test SHA-256 values are
`7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39`
and `a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a`.
Its complete focused, independent-fast, static, pointwise-law,
return-conditioning, selected-fiber, nonreplay, and independent-audit record
is evidence-bound under the standalone
[CP49 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md);
any CP49 source or focused-test change requires a new audit. The dependency
order may not be reversed: the mixed
oracle must exist before a real-domain trainer can be authorized. Checkpoint
twenty-nine's diagnostic/custody tooling is an evidence layer, not a dependency
of the initializer or sampler. Checkpoint thirty is a deterministic point-
factor dependency only, not an admitted initializer or sampler. Checkpoint
thirty-one is an all-atomic support/coefficient dependency only, not an
admitted initializer or sampler.
Checkpoint thirty-two is an explicit-word all-atomic finite-resolution
selection dependency only, not an admitted initializer or sampler.
Checkpoint thirty-three is an exact one-word all-atomic protocol-binding
dependency only, not an admitted initializer or sampler.
Checkpoint thirty-four is a fixed all-atomic configuration-constructor
dependency only, not a live initializer distribution, admitted initializer,
or sampler.
Checkpoint thirty-five is a fixed-index finite reference construction,
bootstrap-lineage, and tag-3-prefix coordination dependency only, not a live
initializer distribution, admitted general initializer, path, or sampler.
Checkpoint thirty-six is a fixed-budget rejection-stage proposal-and-score
preparation dependency only, not an acceptance decision, selected output,
failure analysis, live initializer distribution, admitted initializer, path,
or sampler.
Checkpoint thirty-seven is a conservative finite-resolution decision
dependency only, not an exact ideal-rejection or live-source law, CP36 failure
analysis, normalized tilted initializer, admitted initializer, selected-state
lineage/tag-3 coordinator, path, or sampler.
Checkpoint thirty-eight is a fixed-\(B\) counterfactual mass-law and structural
selected-state dependency only, not a live source/success law, selected-
conditioned ideal/dyadic guarantee, generic initializer admission,
initialization-index-safe lineage/tag-3 coordinator, path, or sampler.
Checkpoint thirty-nine is a selected-result construction-time positional-
lineage and local tag-3-prefix dependency only, not a live initializer/source
law, payload or coordinate generator, global address allocator, generic
admission object, selected-conditioned ideal/dyadic guarantee, path, or
sampler. Its final disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
Checkpoint forty is a fixed-successful-batch finite-resolution target and
structural state/no-state boundary only, not a live or unconditional
initializer distribution, CP36 failure law, exact ideal rejection, normalized
global tilt, all-strategy general initializer, payload or coordinate generator,
path, or sampler. Its focused suite passed 45/45, inherited exact-hash CP39
parent evidence remains applicable, and its disposition is **PASS WITH EXPLICIT
SCOPE LIMITS**.
Checkpoint forty-one is a symbolic failure-aware abstract source-law ledger
conditional on an explicit unproved factorization hypothesis only. It
materializes no numeric source/failure/selection mass and supplies no live
Philox/source/initializer law, exact ideal rejection, global analytic
normalization, general admission, path, or sampler. Its focused suite passed
**28/28** under no-cache, warnings-as-errors conditions; its disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**. Its final independent documentation
audits report **P0=P1=P2=0**.
Checkpoint forty-two is only a bounded partial staged reference evaluator for
the frozen CP41 coordinate partition. On its nonrefusing direct-dependency
domain, its input signature establishes decision-word noninterference for its
own \(G^{42}\), not for the totalized live CP36/CP37 map. It neither supplies
an executable preparation-failure branch nor
proves live failure equivalence, and therefore does not discharge CP41's
factorization hypothesis or establish a live/global initializer source law.
Checkpoint forty-three closes only its own supplied-word reference composite
under its typed construction contract. Its private \(H^{43}_{\mathrm{sem}}\) and
public replay facade are distinct: the latter passes a failure through only
after deterministic stable replay of \(G^{43}\), and otherwise refuses before
touching \(W\). Its reviewed arithmetic text does not resolve natural
\(F_{37}\) reachability, and its selected runtime fingerprint does not certify
loaded-code integrity. It does not prove universal live CP36/CP37
factorization, discharge CP41's premise, or establish a live source,
initializer, path, sampler, or scientific claim.

## 10. Mandatory theorem-to-code tests

### 10.1 Reference and forward process

1. \(\Pi_N\) normalizes and reproduces atomic multiplicity factorials.
2. Birth/death and type-replacement detailed-balance residuals vanish.
3. The generator annihilates constants, has finite total rates, enforces the
   cap, and is permutation invariant.
4. The forward and reverse clean holds are exact identities; segmentwise
   integrated-clock inversion satisfies the sampled exponential hazard and
   handles a horizon with no further jump.
5. Event-driven forward frequencies match finite matrix exponentials and exact
   OU moments on every piecewise-constant schedule segment.
6. Relabelling occurrence identifiers leaves canonical path statistics
   unchanged.

### 10.2 Reverse objective

7. On every enumerable finite fixture, \(V^*=\log(dP_s/d\Pi_N)\) reconstructs
   the exact reversed generator.
8. The analytic gradient and nonnegative population excess of the jump-flux
   loss vanish at \(V^*\) and not at a sign-reversed energy.
9. The continuous score-matching excess equals the squared relative-score
   error on a nonstationary Gaussian/OU fixture.
10. Exact integral and importance-proposal estimates agree under deliberately
   nonuniform time, occurrence, edge-family, and destination proposals; weights
   include every source/destination reference factor.
11. On hostile inputs, the snapshot-bound analytic certificate dominates
    \(|V|\), every valid learned-base edge increment, the full
    physical-coordinate gradient and Hessian of \(V\) (and its derived
    Laplacian), \(e^{\Delta V}\), and, under the frozen production edge
    enumeration and summation law, the resulting total learned-exit rate
    relative to the bound reference process.
12. Adding a time/context-only gauge changes neither drift, rates, nor loss
    gradients on state-dependent parameters.

### 10.3 Observation and guide

13. Clean rows and positive-mixture rows normalize under \(\lambda_m\).
14. The exact subset dynamic program, labelled injections, and quotient
    \((H,\Omega(H))\) computation agree, including simultaneous signal/clutter
    duplicates.
15. Latent and observed duplicate permutations change no likelihood or
    derivative.
16. Detection counts convolved with Poisson clutter reproduce retained and
    overflow mass before and after the positive mixture.
17. Type-confusion rows and every atomic/Gaussian mark-noise fiber integrate to
    one.
18. Structural zeros remain exact before, and only before, an admitted
    full-support mixture.
19. The explicit one-occurrence sub-Markov kernel and future-immigrant Poisson
    intensity match finite simulation and quadrature.
20. The clean, positive-mixture, retained, and overflow preconditioners equal
    their terminal densities at \(u=S\).
21. Uncapped enumeration matches analytic propagation; restriction performs no
    cap conditioning.
22. The blocked-birth defect and Duhamel sign identity equal a finite generator
    calculation at every cap state.
23. Exact and proposal-based defect calculations agree within their frozen
    uncertainty rule, with cap, base-mismatch, derivative, and Monte Carlo
    components reported separately.
24. Guide log-value, continuous-gradient, and every edit-edge ratio error are tested
    separately.

### 10.4 Conditional learner and sampler

25. The conditional time law has full interval support; joint/product sampling
    uses independent same-context trajectories, including unique continuous
    contexts, and recovers the finite Bayes logit.
26. The nuisance has no computational path from \(u\) or \(y\) and cancels in
    all ratios and initial weights.
27. Exact \(h\), guide-plus-exact-residual, and the combined scalar reconstruct
    identical drift, all edit rates, initializer, and endpoint law.
28. Enumeration and certified rejection normalize the plug-in initializer;
    SIR converges to it as its preregistered independent-particle sequence
    grows.
29. Certified thinning reproduces exact tilted total rates, edit-family
    probabilities, and continuous destination distributions on quadrature
    fixtures.
30. Coupled step halving converges on the mixed oracle for continuous paths, edit
    counts, and endpoint conditional law.
31. Exact known-law and sample-based real-domain terminal-reference diagnostics
    trigger their declared pass/failure decisions.
32. No support, cap, multiplicity, overflow, non-finite, missing-envelope, or silent-clipping
    violation occurs.

### 10.5 Incremental implementation checkpoint

As of 2026-08-20, forty-nine incremental implementation and engineering-
evidence checkpoints are implemented and separately mapped. Final execution
evidence is complete through checkpoint forty-nine; CP43, CP44, CP45, CP46,
CP47, CP48, and CP49 evidence is recorded below, each with disposition **PASS
WITH EXPLICIT SCOPE LIMITS**.
For checkpoint thirty-four, frozen source SHA-256
`e8e7dee2a1773fbc836b920c4289a1c1b555698f2f07e5c62d3b3ffb2ee423a1`
and focused-test SHA-256
`98a864e9119f6c78b33c1380bf7e7904b70f9ffbfd76edaccb06db8703a742c3`
identify the audited pair. The focused suite passed 65/65 in 1186.81 seconds;
the inherited checkpoint-31 through checkpoint-34 regression passed 226/226 in
3178.43 seconds; and independent source, test, and mathematical-scope audits
report **P0=P1=P2=0**. These are scoped software results for a fixed
all-atomic configuration constructor and an abstract ideal-word theorem, not
an actual-RNG law, live initializer distribution or admission, live or
empirical distributional evidence, scientific evidence, model-quality
evidence, or generality evidence. Formal
Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**, Test 30 remains
**PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim or result slot is
promoted.

For checkpoint thirty-five, frozen source SHA-256
`f8d20a73e5fe0bd728182636c7235532433ec477e130dce4cc026e967869b768`
and focused-test SHA-256
`8a633c1033ad6c4dde25ee5e174e3ed9592cb8eb9320835bcc1d9f90cb11acde`
identify the reviewed pair. The focused suite passed 64/64 with warnings-as-
errors in 998.81 seconds. The no-cache direct-parent CP23/CP25/CP28 regression
passed 173/173 with 0 failed/errors/skips/xfail/xpass and no warnings, under
warnings-as-errors in 1251.19 seconds (0:20:51); all involved hashes remained
unchanged. The disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. Formal Tests
28 and 29 remain
**OPEN**, Test 30 remains **PENDING**, `R2-HYBRID` remains **NOT RUN**, and no
claim or result slot is promoted.

For checkpoint thirty-six, frozen source SHA-256
`fd87881c04801510e74edde8676583d7068b387c3e091adeba8732f6b6ce4b59`
and focused-test SHA-256
`8a7469dc18ab47c3b2dde1a3a8eeeb86c7764709a511b1b2ed105dd081d1ceeb`
identify the audited pair. The focused suite collected 115 tests and passed
115/115 with 0 failed, 0 skipped, and no warnings under warnings-as-errors in
1455.63 seconds (0:24:15) of pytest time and 1456.13 seconds external wall
time. The no-cache direct-parent regression passed 171/171 with 0 failed, 0
skipped, and no warnings under warnings-as-errors in 485.58 seconds (0:08:05)
of pytest time and 486.19 seconds external wall time. The disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**. These are scoped software results for
fixed-budget proposal-and-score preparation, not acceptance, rejection
success/exhaustion, a failure bound, a success-conditional or live word law,
initializer admission, path, or sampler evidence. Formal Tests 28 and 29
remain **OPEN**, Test 30 remains **PENDING**, `R2-HYBRID` remains **NOT RUN**,
and no claim or result slot is promoted. The venue-neutral TeX manuscript is
unchanged.

For checkpoint thirty-seven, frozen source SHA-256
`acbe2bd14305560360ec40595314a19a66f37ceec22d4e22321c05f14d050fed`
and focused-test SHA-256
`ea255cc36ee17c20b355e237fd5a87de89bd9458ef42f5b850124b14f6b49f91`
identify the audited pair. The focused suite passed 44/44 with no reported
failure, skip, or warning in 423.78 seconds (0:07:03) of pytest time and 424.30
seconds external wall time; the log SHA-256 is
`b83af9ebf878c198916d5b5e6737478dfcfa80e53f64bc26f75b236d21058579`.
The no-cache CP36 direct-parent regression passed 115/115 with no reported
failure, skip, or warning in 1777.84 seconds (0:29:37) of pytest time and
1778.76 seconds external wall time; the log SHA-256 is
`3c9266f00e96da99850d343ccc137bf1a09bd68546852486391abad9bba744d4`.
The disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. These are scoped
software results for the conservative dyadic quota and first-selected-or-
exhausted decision layer under its exact API contracts, not a live Philox law,
exact ideal rejection, failure probability, law conditional on CP36 success,
normalized tilted initializer or admission, lineage/tag-3 coordination, path,
or sampler evidence. Formal Tests 28 and 29 remain **OPEN**, Test 30 remains
**PENDING**, `R2-HYBRID` remains **NOT RUN**, and no claim or result slot is
promoted. The venue-neutral TeX manuscript is unchanged.

For checkpoint thirty-eight, the direct word-free fixed-batch projection,
exact first-success/exhaustion partition, duplicate-configuration aggregation,
\(Z_B>0\) selected-law boundary, strict unconditioned augmented
\(<A/2^{64}\) common-uniform comparison, structural selected-state validity,
deterministic-live/non-live-law boundary, and initialization-index lineage/tag-3
gap are mapped in the linked incremental audit. The source/test SHA-256
identities are
`5614c0f79dc318d2a19b920d1a787056f153cbf4dc2b7b4da2bd0cd65592b627`
and
`97d4752b00e119a9ff8011e38500ff2de2efa2738791244fbca3d15680188184`.
The no-cache, warnings-as-errors focused suite passed 45/45 in 681.48 seconds,
and the no-cache, warnings-as-errors CP37 regression passed 44/44 in 428.82
seconds. Static gates and the independent source audit passed; the disposition
is **PASS WITH EXPLICIT SCOPE LIMITS**. Formal Tests 28 and 29 remain **OPEN**,
Test 30 remains **PENDING**, `R2-HYBRID` remains
**NOT RUN**, and no claim, initializer admission, evidence row, or result slot
is promoted. The venue-neutral TeX manuscript is unchanged.

For checkpoint thirty-nine, one exact CP38 resolution, selected-configuration
object identity and exact selected-attempt index, reverse-time-zero intensity,
CP23 positional bootstrap lineage, initialization-indexed and attempt-
separated local tag-3 addresses, dimension-shaped uninterpreted prefixes,
selected-empty/exhausted separation, same-runtime stream replay, and the
explicit local-only address boundary are mapped in the linked incremental
audit. The frozen source SHA-256 is
`d9851ab3a0ab68e8d748db497c386264f26e42e4131cd679c4282a4a609a65ac`;
the focused-test SHA-256 is
`4d7c0c763b874717a47697c160670e9d68343ae780c77bffe861cb50eb8673da`.
The no-cache, warnings-as-errors focused suite passed 65/65 in 2,983.10
seconds of pytest time and 2,983.75 seconds of external wall time.
The direct-parent CP38 source/test SHA-256 identities are
`5614c0f79dc318d2a19b920d1a787056f153cbf4dc2b7b4da2bd0cd65592b627`
and
`97d4752b00e119a9ff8011e38500ff2de2efa2738791244fbca3d15680188184`;
its no-cache, warnings-as-errors regression passed 45/45 in 789.66 seconds of
pytest time and 790.13 seconds of external wall time. Static gates and the
independent final source, hostile-test, and documentation reviews returned
**P0=P1=P2=0**. CP39 is **PASS WITH EXPLICIT SCOPE LIMITS**. Formal Tests 28
and 29 remain **OPEN**, Test 30
remains **PENDING**, `R2-HYBRID` remains **NOT RUN**, and no claim, initializer
admission, evidence row, or result slot is promoted. The venue-neutral TeX
manuscript is unchanged.

For checkpoint forty, the exact augmented and selected finite-resolution
targets, \(Z_B=0\) definition boundary, raw strict
\(2A/(2^{64}Z_B)\) comparison, clipped non-strict display convention,
selected/selected-empty structural admission, exhausted no-state result,
target-row ordinal versus selected-object identity, one-parent-coordinate
chronology, validation-without-construction rule, and comprehensive surface
hardening are mapped in the linked incremental audit. Frozen source SHA-256 is
`1d92574611498aeed62cd16bb232ef22f95b365b689b5351219e0539e0e6b115`;
focused-test SHA-256 is
`30b5f93413b8c5448d85a1b7f768da5b394143d363061db418f5847272c80305`.
The focused suite contains 45 collected tests. Its final result is
**45/45 passed** in **3908.56** seconds of pytest time and **3909.19** seconds
external wall time.
The frozen CP39 direct-parent source/test identities are
`d9851ab3a0ab68e8d748db497c386264f26e42e4131cd679c4282a4a609a65ac`
and
`4d7c0c763b874717a47697c160670e9d68343ae780c77bffe861cb50eb8673da`;
an inherited no-cache, warnings-as-errors regression of that exact frozen pair
passed **65/65** in **2983.10** seconds of pytest time and **2983.75** seconds
external wall time. CP39 was not freshly rerun for CP40. Static gates passed,
and independent final read-only source, hostile-test, and documentation audits
returned **P0=P1=P2=0**. The read-only audits do not substitute for execution.
The CP40 focused execution passed, and the unchanged CP39 pair is covered by
inherited exact-hash regression evidence. CP40 is **PASS WITH EXPLICIT SCOPE
LIMITS**. Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**,
`R2-HYBRID` remains **NOT RUN**, and no C-row, R-slot,
nonconfirmatory-evidence row, novelty decision, scientific/model-quality
result, generality statement, or manuscript conclusion is promoted. The
venue-neutral TeX manuscript is unchanged.

For checkpoint forty-one, the linked audit maps exactly an **abstract
product-uniform failure-aware source law conditional on an explicit unproved
factorization hypothesis**. The symbolic map separates \(F_{36}\) preparation
failure, \(F_{37}\) quota failure, exhaustion, and configuration atoms. It
records exact normalization, the \(\rho=0\) identity, strict
\(\rho A/2^{64}\) and universal \(A/2^{64}\) augmented bounds, and, only for
\(S_Q>0\), the factor-one selected comparison, with
\(\Delta=\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})\),

\[
\operatorname{TV}(P^{\mathrm{sel}},Q^{\mathrm{sel}})
\le\frac{\Delta}{\max(S_P,S_Q)}
=\frac{\Delta}{S_P}
\le\frac{\Delta}{S_Q}
<\frac{\rho A}{2^{64}S_Q}
\le\frac{A}{2^{64}S_Q}.
\]

No dyadic selected law or comparison bound is defined when \(S_Q=0\). No
numeric fiber, failure, batch, state, exhaustion, selection,
or conditioned-bound value is materialized. No live Philox/source/initializer
law follows. CP41 consumes no source-law \(V/W\) coordinate and no
caller/global RNG, and performs no CP36--CP40 operational call. Transitive
certification/live-binding may execute CP39's local fixed Philox runtime probe
of three raw words for procedural custody; that is not a live source draw,
result, or fiber enumeration.

Checkpoint-41 source SHA-256 is
`79827f05b1a157dfaaed53146a17a7f9e006170c36bf6823510a87d338abe254`;
focused-test SHA-256 is
`36e445057613dff7ea5d0606fa4c7924886549b57f94b58c4b3850c51678fcc3`.
The no-cache, warnings-as-errors focused run collected **28** tests and passed
**28/28** in **759.21** seconds of pytest time and **759.70** seconds external
wall time. Static gates were clean under Black, pyflakes,
Python 3.9 byte-compilation, ASCII, and the at-most-88-column check.
The final independent source/test re-audit reports **P0=P1=P2=0**.
The final independent documentation audits also report **P0=P1=P2=0**.

Inherited CP40 source/test identities are
`1d92574611498aeed62cd16bb232ef22f95b365b689b5351219e0539e0e6b115`
and
`30b5f93413b8c5448d85a1b7f768da5b394143d363061db418f5847272c80305`.
That pair passed **45/45** in **3908.56** seconds of pytest time and
**3909.19** seconds external wall time and was not freshly rerun for CP41.
The CP41 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. Formal Tests 28
and 29 remain
**OPEN**, Test 30 remains **PENDING**, `R2-HYBRID` remains **NOT RUN**, and no
C-row, R-slot, evidence row, novelty decision, scientific/model-quality
result, generality statement, or manuscript conclusion is promoted. The
venue-neutral TeX manuscript is unchanged.

For checkpoint forty-two, the linked audit maps the exact CP41-bound staged
\(G_{r,j}(V)\)/\(H(G,W)\) reference semantics and its explicit nonclaim
boundary. Frozen source SHA-256 is
`a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`.
The recovered 29-test focused-file SHA-256 is
`8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`;
any additive boundary supplement is identified and timed separately.

The final no-cache, warnings-as-errors focused result is
**29/29 passed** in **3599.47** seconds of pytest time
and **3600.09** seconds external wall time. The fresh exact-hash
CP41 regression result is **28/28 passed** in
**805.41** seconds of pytest time and
**806.05** seconds external wall time. The additive
boundary supplement has SHA-256
`d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe` and result
**5/5 passed** in
**1273.25** seconds of pytest time and
**1274.44** seconds external wall time.
Static gates are **PASS (Black, pyflakes, Python 3.9 byte-compilation, ASCII, <=88 columns, and 5-test collection)**, and the independent audit is
**PASS (independent audit: P0=P1=P2=0)**.

The supplement's \(F_{37}\) case is profiler-injected exact-exception branch
evidence, not evidence that an unchanged valid parent naturally reaches that
failure. Its \(K=0\) and \(K=2^{64}\) cases validate the pure \(H^{42}\)
constructor, not public-owner \(G^{42}/H^{42}\) endpoint integration. The
CP42 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot,
nonconfirmatory-evidence row, novelty decision, scientific/model-quality
result, generality statement, initializer admission, or manuscript conclusion
is promoted. The venue-neutral TeX manuscript is unchanged.

For checkpoint forty-three, the linked audit maps the CP42-bound supplied-word
reference composite and its exact claim boundary. Frozen CP43 source SHA-256 is
`12977ea4c38c8f5cb595d823e129f0f9dd8e0cadb1a151247d3278464c64fd64`, and
frozen focused-test SHA-256 is
`5f8372c4e80e5539e08444170f687af36b755998e6e96ffbdbe57331178f9944`. The
final no-cache, warnings-as-errors focused run collected **62** tests and
returned **62/62 passed** in **12949.69** seconds of pytest time and
**12950.26** seconds external wall time.

The frozen regression identities are CP42 source
`a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`, CP42
primary test
`8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`, and CP42
additive-supplement test
`d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`. The
primary regression returned **29/29 passed** in **3409.31** seconds of pytest
time and **3409.78** seconds external wall time. The additive-supplement
regression returned **5/5 passed** in **1205.53** seconds of pytest time and
**1205.98** seconds external wall time. Their pre/post hash status is
`PASS (pre/post exact CP42 source and test hashes unchanged)`.

Static gates are **PASS (Black, pyflakes, Python 3.9 byte-compilation, ASCII,
and 62-test collection); line-length audit has five reviewed exceptions**,
with details `Black left both files unchanged; exactly five lines exceeded 88
columns (source 56, 1683, 1705, and 1712; test 780), all identifier or
qualified-name lines`. The final independent audit is **PASS WITH ONE EXPLICIT
P2 SCOPE LIMIT**, with details `P0=0, P1=0; P2=1: only one live CP37 outcome has
a full parity witness, while the opposite outcome is covered only by synthetic
semantic-H tests; no universal live-equivalence claim is made`. The CP43
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. These are scoped software-
engineering results and do not alter the open scientific statuses below.

The CP43 theorem is the constructed composite using private semantic
`_apply_trusted`, not the separately callable public replay facade. Public
failure pass-through requires deterministic, replay-stable \(G^{43}\); a
transient mismatch is refused before the decision-word object is accessed.
The renamed
`semantic_h43_failure_passthrough_without_w_access_certified` and
`semantic_h43_full_w_preflight_before_comparison_certified` fields certify
only private \(H^{43}_{\mathrm{sem}}\); they do not contradict
`separately_invoked_public_h_replay_free=False` or
`transient_failure_public_h_passthrough_certified=False`. The certificate also
records
`cp43_defined_reference_factorization_discharged_by_construction=True`,
`abstract_product_uniform_corollary_recorded_under_explicit_premises=True`,
and `construction_contract_enforced=True` for the corresponding narrow
claims. Its exact-text, digest-bound reviewed F37 argument excludes the
identified nonadaptive routes but leaves the 3072-digit adaptive floor-
separation route and natural valid-parent \(F_{37}\) reachability unresolved.
Its selected same-runtime fingerprint does not authenticate loaded source;
`loaded_code_integrity_certified=False`.

For checkpoint forty-four, the linked audit maps the one-allocation factorized
execution adapter and its returned-result-only claim boundary. Frozen CP44
source SHA-256 is
`42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d`, and
frozen focused-test SHA-256 is
`e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.
The source and test contain `1829` and `829` lines, respectively, and the test
collects exactly **26** cases. The final no-cache, warnings-as-errors run
returned **26/26 passed** in **50165.86** seconds of pytest time and
**50166.38** seconds external wall time. There were no failures, errors, skips,
xfails, xpasses, or warnings, and the source/test hashes were unchanged.

Static gates are **PASS** under Black, pyflakes, flake8
`E9,F63,F7,F82`, Python 3.9.13 and locked Python 3.11.5 syntax compilation,
ASCII screening, exact 26-case collection, the exact 16-symbol
export/signature check, and all six once-only exact contract-block
comparisons. Eighteen formatter-stable, identifier-dominated lines longer than
88 columns were individually reviewed. The independent CP44 source/test audit
reports **P0=P1=P2=0**.

No parent suite was freshly rerun for CP44. Exact-hash inherited evidence is
the historical CP43 **62/62 passed** record
(**12949.69/12950.26** seconds pytest/wall), CP42 primary **29/29 passed**
record (**3409.31/3409.78** seconds), and CP42 supplement **5/5 passed** record
(**1205.53/1205.98** seconds). The venue-neutral Markdown and TeX manuscripts
were untouched and retain SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.
The CP44 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. This is scoped
software-engineering evidence only; it promotes no live-source, numeric-mass,
initializer/path/sampler, scientific, model-quality, cross-domain, generality,
or manuscript claim.

For checkpoint forty-five, the linked audit maps the fixed-address source-
support obstruction and its source-only claim boundary. Frozen CP45 source
SHA-256 is
`5c430ed18d8c14fd5359858b8a686c521c8cb61f5389b977b4c1f8fdc192bad5`, and
frozen focused-test SHA-256 is
`53701f0c59634fe6be32d730e39b16e066cfa9d8879094e7c876e235742f9553`.
The source and test contain `1019` and `1009` lines and `44871` and `37063`
bytes, respectively; the test collects exactly **20** unique cases. The final
no-cache, warnings-as-errors run returned **20/20 passed** in **19448.25**
seconds (`5:24:08`) of pytest time. `/usr/bin/time -p` recorded **19448.78**
seconds wall, **18123.18** seconds user, and **1248.91** seconds system time.
There were no failures, errors, skips, xfails, xpasses, or warnings, and the
source/test hashes were unchanged.

Post-run static gates are **PASS** under Black, pyflakes, flake8
`E9,F63,F7,F82`, Python 3.9.13 and locked Python 3.11.5 syntax compilation,
ASCII/AST screening, exact 20-case collection, and the exact 15-symbol export
surface. The source-independent exact-enumeration subset passed **9/9**. The
independent CP45 source/test review reports **P0=P1=P2=0**. The untouched
venue-neutral Markdown and TeX manuscripts retain SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.

The CP45 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. This scoped
negative source-law result supplies no live product-uniform or independent
source, success/refusal probability, unconditional CP44 law, semantic-output
lower bound, natural \(F_{37}\) resolution, initializer/path/sampler admission,
scientific/model-quality result, cross-domain generality, or manuscript claim.

For checkpoint forty-six, the standalone
[CP46 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md)
maps the explicit fixed-request and declared external finite request-law
descriptors and their conditional source-only boundary. The frozen source is
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
with SHA-256
`8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`;
the frozen focused test is
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
with SHA-256
`04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`.
The authoritative run returned **24/24 passed** in **4765.71 seconds** of
pytest time and **4766.28 seconds** real time: 15 source-independent fast
cases and nine owner-bound cases. Exact enumeration covered 1,848 positive
partial-map/law cases and 10,000 derived-coordinate/map compositions. Static
gates passed, and final independent reviews report **P0=P1=P2=0**.

The CP46 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It adds no
external-law realization or sampler, event-positivity or unconditional-law
claim, live uniformity/independence/randomness/freshness, weighted-fiber
balance, semantic-output TV lower bound, initializer/path/sampler admission,
scientific/model-quality result, cross-domain generality, or manuscript
claim.

For checkpoint forty-seven, the standalone
[CP47 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md)
maps the direct external L-word provider interface, identity ingestion, bounded
owner-local retirement ledger, and exact CP46--CP43 execution custody. Frozen
source SHA-256 is
`2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`,
and frozen focused-test SHA-256 is
`46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`.
The source/test contain `2512`/`1446` lines and `108814`/`52122` bytes. The
authoritative no-cache warnings-as-errors run returned **31/31 passed** in
**7763.03 seconds** (`2:09:23`) of pytest active duration: 22 fast cases and
nine owner-bound cases. `/usr/bin/time -p` recorded real `30735.62` seconds,
including a long host-suspension interval, user `7141.85`, and sys `545.25`
seconds. Post-run 22/22 fast evidence passed in `1.17` seconds; Black, syntax
compilation, pyflakes, and flake8 `E9,F63,F7,F82` passed; final independent
reviews report **P0=P1=P2=0**.

The CP47 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It adds no
provider-law realization, totality/success-mass guarantee, live product-
uniformity or IID, physical randomness, cross-call value freshness, global or
persistent uniqueness, concurrent semantic-safety or adaptive-retry contract,
unconditional returned-result law, output-TV lower bound,
initializer/path/sampler admission, scientific/model-quality result, cross-
domain generality, or manuscript claim.

For checkpoint forty-eight, the standalone
[CP48 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md)
maps the two exact operational profiles, direct exact-byte backend boundary,
manual big-endian byte/word bijection, CP47 delegation, and successful-result
custody. Frozen source SHA-256 is
`7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd`,
and frozen focused-test SHA-256 is
`2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282`.
The source/test contain `2025`/`1692` lines and `82973`/`62124` bytes. The
authoritative no-cache warnings-as-errors run returned **37/37 passed** in
`15191.58` seconds of pytest active duration: 28 source-independent fast cases
and nine owner-bound cases. Shared owner-fixture setup consumed `15048.01`
seconds. `/usr/bin/time -p` recorded real `15192.11`, user `13929.09`, and sys
`1211.79` seconds. The post-run fast partition passed **28/28** in `2.16`
seconds; Black, locked-runtime syntax compilation, pyflakes, and flake8
`E9,F63,F7,F82` passed; and three independent final strict audits report
**P0=P1=P2=0**. A retained P3 note deliberately leaves asynchronous
`CALL`-to-`STORE` interruption outside the certificate.

The CP48 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It certifies no
backend or operating-system source law, totality, success mass, product-
uniformity, IID behavior, entropy provenance, physical randomness,
cryptographic security, authentication, freshness, global uniqueness,
general concurrency/reentry/asynchronous safety, unconditional returned-result
law, semantic-output TV lower bound, initializer/path/sampler admission,
scientific/model-quality result, cross-domain generality, or manuscript claim.

For checkpoint forty-nine, the standalone
[CP49 audit](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md)
maps the sealed external assumption declaration, the pointwise enriched
CP43/CP42 object-semantic pushforward, return-conditioning and sequence
caveats, selected-fiber custody, and structural nonexecution/nonreplay. Frozen
source SHA-256 is
`7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39`,
and frozen focused-test SHA-256 is
`a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a`.
The source/test contain `1913`/`1765` lines and `84530`/`70075` bytes. The
authoritative no-cache warnings-as-errors run returned **28/28 passed** in
`25354.31` seconds (`7:02:34`) of pytest active duration: 21
source-independent cases and seven owner-bound cases. Shared owner-fixture
setup consumed `17897.94` seconds. `/usr/bin/time -p` recorded real
`25366.40`, user `23535.81`, and sys `1681.97` seconds. JUnit records zero
errors, failures, and skips; shell and pytest exits are zero; and source/test
hashes remained stable. The unchanged pair then passed the independent fast
partition **21/21**, with seven deselected, in `2.04` seconds; external timing
was real `2.62`, user `1.67`, and sys `0.45` seconds. Black, locked-runtime
syntax compilation, pyflakes, and flake8 `E9,F63,F7,F82` passed; independent
source, hostile-test, and claim-scope audits report **P0=P1=P2=0**.

The first-success snapshot's `status.env` and `junit.xml` are authoritative.
Only lines 1--30 of its `authoritative.log` support the first run's timing;
the unintended automatic-repeat suffix beginning at line 31 was stopped and
is excluded. The CP49 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. It
certifies no operational premise, backend/OS/callback law, totality,
unconditional returned law, sequence IID/adaptive law, preboundary refusal
totalization, global uniqueness, CP41-premise discharge or universal legacy
equivalence, initializer/path/sampler, Formal Test 28 closure,
scientific/model-quality result, generality, or manuscript claim.

Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot,
nonconfirmatory-evidence row, novelty decision, scientific/model-quality
result, generality statement, initializer admission, or manuscript conclusion
is promoted. The venue-neutral TeX manuscript is unchanged.

- Test 1 is implemented for the transformed mixed-dimensional reference,
  including the finite-atomic orbit/factorial projection.
- Test 2 has balanced-rate construction and direct all-atomic two-way flux and
  reverse-generator evidence. The eighth layer adds cap-one mixed
  birth/death/type-replacement detailed balance, and a separate cap-two
  companion checks the \(1/2!\) reference mass and the two indistinguishable
  occurrence routes at the `AA` state. Arbitrary-cap mixed balance remains a
  whole-method obligation.
- Test 3 has cap, occurrence-multiplicity, finite-rate, atomic
  constant-generator, resource, and permutation checks. The scoped mixed
  oracle adds nonnegative no-clipping transition construction, signed row
  residuals, explicit dense-work and Hessian-allocation limits, and fail-closed
  unresolved-clock behavior. Its conditional branch additionally refuses
  non-normal positive generator/transition entries and non-diagonal Gaussian
  precisions outside a dimension-scaled binary64 condition limit. These are
  operational oracle boundaries, not restrictions on the abstract law, and
  are not a substitute for the eventual whole-method generator audit.
- Test 4 has an exact forward clean hold, exact binary-rational waiting-time
  decisions, and explicit breakpoint/horizon behavior. The eighth layer adds
  a backward-information oracle with public reverse time
  \(u\mapsto s=S-u\), an exact terminal identity throughout the reflected
  clean hold, and zero Doob controls there. The ninth layer adds an exact
  compact known-law path RNG by conditional right-end sampling, exact forward
  reference simulation, and deterministic reversal. It preserves the final
  reverse hold exactly, but it is not the learned/general sampler. The tenth
  layer independently returns an exact zero reference-candidate intensity
  throughout the hold without evaluating an inactive base-rate decomposition
  or consuming RNG; this is not a controlled waiting-time implementation. The
  thirteenth layer independently returns a canonical positive-zero residual
  throughout the same direct-time hold, retains exact-zero first and second
  coordinate derivative graphs for both state-pair endpoints, and refuses a
  positive operational gate that becomes subnormal or underflows. It does not
  construct the combined reverse path. The fourteenth layer accepts only an
  already sampled active positive-rate candidate; a clean-hold or zero-exit
  intensity therefore yields no composable candidate rather than a fabricated
  zero-edit record. The fifteenth layer separately totalizes a typed guide
  numerical failure one unit in the last place inside the active interval,
  without pruning support. The sixteenth layer leaves checkpoint thirteen's
  strict failure intact but supplies a separate jump-only value at that
  strictly active subnormal/underflow gate by exact rational rescaling of the
  represented checkpoint-private bounded core. It does not create a residual
  derivative or continuous-path value. The seventeenth layer composes those
  operational guide and residual values with the checkpoint-private base for
  an active candidate at the same time; it still does not create a hold edit,
  continuous derivative, clock, or path. The eighteenth layer converts the
  authenticated zero reference exit into an exact zero controlled exit and
  otherwise constructs a no-RNG upper envelope before any route draw. It does
  not draw a waiting time or candidate. The nineteenth layer consumes that
  local envelope in a separate successful-return primitive. It treats
  \(\tau\le b-a\) as ideal-real hit eligibility, certifies exhaustion only by
  strict real excess, and returns only a uniquely rounded binary64
  `proposal_time` strictly inside \((a,b)\); real right-end equality and
  represented boundary collapse are refusals. Structural-zero and zero-length
  local intervals consume no random word. This is not a repeated clock or
  learned/general path. The twentieth layer coordinates repeated represented
  clocks only within a caller-bounded successful-return transcript. Its loop-
  top structural-zero/zero-duration terminal check precedes the proposal cap;
  an active cap hit refuses before another waiting draw. It is not an exact
  real-time renewal, CTMC, or learned/general path law.
- Test 5 now has the scoped type-changing mixed CTMC--OU gate: its certified
  three-state kernel and analytic untouched/fresh-coordinate decomposition
  agree with an independent matrix exponential and with 6,000 seeded
  event-driven paths, including discrete transition frequencies and OU
  moments. This is one frozen cap-one schedule fixture, not exhaustive
  schedule, scale, or production-sampler evidence.
- Test 6 has same-stream equality of canonical path results under input
  permutation.
- Test 7 is substantively closed for enumerable finite fixtures, including
  independent reversal matrices, randomized reversible chains, direct-time
  schedule orientation, and tiny-edge support. The eighth layer additionally
  supplies exact reference-relative mixed forward density ratios, derivatives,
  and edit multipliers in its declared nonstationary law, but no learned or
  general-cap reverse path.
- Test 8 is substantively closed for the finite theorem layer through
  independent loss/gradient/Hessian controls, wrong-sign sentinels, stable
  nonnegative excess, and the connected-graph gauge nullspace.
- Test 9 is substantively closed for the Gaussian theorem layer through a
  correlated nonstationary OU fixture and squared relative-score excess.
- Test 10 is closed for structured importance arithmetic/oracle scope and is
  now integrated with the exact normalized reference proposal. The composer
  retains duplicate occurrence routes, continuous Gaussian destination log
  densities, and every reference/proposal factor. The tenth layer adds the
  independent process-owned no-RNG value
  \(\Lambda_s^0(x)=\gamma_J(s)\Lambda^0(x)\) and makes the route draw consume
  and revalidate that record; external time and state densities remain
  explicit caller inputs. Arbitrary alternative production proposals are not
  implemented.
- Test 11 has substantive sixth-layer evidence for the declared bounded
  neural/checkpoint scope: an owned snapshot certificate globally bounds
  \(|V|\), arbitrary paired-configuration increments, the full flattened
  physical-coordinate gradient and Hessian, the derived Laplacian,
  \(e^{\Delta V}\), a binary64 operational guard for each supplied rate, and
  the symbolic real-arithmetic learned-rate consequence relative to the bound
  reference process. Hostile tests cover multiplicity, empty/atomic states,
  extreme finite inputs, exact module-graph/dispatch/registry custody,
  tensor/storage/autograd isolation, resource preflight, binary64 range loss,
  checkpoint mutation, and staged rate rounding. The
  seventh layer now proves this relationship for one process-created
  normalized reference candidate and its recomputed
  \(\gamma_J(s)\Lambda^0(x)\). The tenth layer separates that reference clock
  into a deterministic preflight before route RNG and checks every reachable
  normalized-reference categorical law. The whole-method gate remains partial
  because the tilted value is a sampled candidate-measure integrand, not an
  integrated learned total exit. Checkpoint seventeen adds an operational
  binary64 edge aggregation and global magnitude witness. Checkpoint eighteen
  exponentiates the exact rational edge, correctly rounds every successful
  finite normal candidate integrand, and constructs no-RNG instantaneous and
  global upper envelopes. It does not compute the active learned total exit or
  admit waiting/acceptance RNG; no trained checkpoint or numerical experiment
  freeze exists, and the certificate is not sampler admission. The
  thirteenth layer separately inherits these global value, state-pair,
  flattened physical-coordinate gradient/Hessian, and Laplacian bounds for a
  cubic-gated conditional residual. It does not certify time or conditioner
  derivatives or aggregate the residual with the base and guide.
- Test 12 has substantive sixth-layer evidence for the declared output-gauge
  and autodiff scope: time/context-only gauges preserve coordinate gradients;
  symbolic gauges preserve edge differences, certified rates, continuous and
  jump losses, and model-parameter gradients; even a maximum finite gauge
  cancels before subtraction; and live state/parameter-dependent gauge graphs
  are rejected. The whole-method gate remains partial because the reverse
  drift and sampler interfaces do not yet exist, and semantic provenance of a
  caller-detached gauge remains a procedural assertion.
- Test 13 is substantively closed for the declared bound-row oracle through
  independent finite atomic enumeration and continuous Gaussian quadrature,
  including overflow and the fixed positive reference mixture.
- Test 14 is substantively closed for exact small-instance scope through
  labelled occurrence, subset-DP, and quotient-orbit agreement, including
  simultaneous signal/clutter duplicates. This is not a scaling result.
- Test 15 has canonical source/observation permutation, duplicate occurrence,
  value, and source-coordinate gradient evidence in the declared channel
  family.
- Test 16 has independent Bernoulli-detection/Poisson-clutter retained and
  overflow checks before and after positive mixing.
- Test 17 has atomic/type-confusion and correlated affine-Gaussian fiber
  normalization checks against the observation reference.
- Test 18 preserves exact clean structural zeros and restores support only via
  the bound row's fixed reference mixture. Real-domain authorization of that
  mixture remains pending.
- Test 19 is substantively closed for the selected conjugate reference through
  independent augmented-CTMC exponential and uniformization calculations,
  Gaussian quadrature, immigrant-intensity identities, and seeded finite-
  simulation checks. This is not a nonconjugate guide result.
- Test 20 is closed for retained and overflow terminal rows and the complete
  reverse clean-hold interval, including the fixed positive mixture.
- Test 21 is substantively closed in exact finite/enumerable scope: a larger
  uncapped count generator matches analytic propagation, and two distinct caps
  give the same literal restricted values without cap conditioning.
- Test 22 is substantively closed on every state of the finite two-type cap
  fixture through both the generator identity and independently quadratured
  Duhamel sign calculation.
- Test 23 is partial. Exact and replayable unnormalized proposal cap estimates,
  standard errors, and provenance separation are implemented, but no
  production cap-defect proposal family/count or nonvacuous high-probability
  uncertainty rule is frozen, and the other Section 6.3 defect components
  remain separate future modules.
- Test 24 is substantively closed only for the exact-oracle scope through
  independent guide values, continuous finite differences/closed calculus, and
  exhaustive birth, death, and replacement ratios on a small finite fixture.
  The eleventh layer additionally certifies a fixed retained or overflow
  observation's real-arithmetic guide range, every capped edit oscillation,
  and full flattened log-guide gradient/Hessian bounds over all reverse times
  and coordinate charts under normalized probability-simplex and
  Markov-kernel semantics. It uses a cap-aware injection polynomial,
  exact-rational covariance witnesses, and directed log arithmetic. It is not
  evidence for a scalable association approximation or a floating-point
  enclosure of the pointwise evaluator. The twelfth layer adds a separate
  represented-value contract: every successfully admitted raw binary64 point
  value lies in the directed model interval and therefore differs from the
  exact model log guide by at most that interval's outward-rounded width; any
  represented legal edit assembled from two such values has magnitude at most
  the same width. This is a coarse successful-only range theorem, not a small
  arithmetic-error analysis or a total evaluator over unbounded coordinates.
  The fifteenth layer adds qualified full-capped-domain fallback coverage for
  the two declared typed point-failure classes after a factory resource
  preflight. It defines an operational
  surrogate rather than preserving the analytic guide; its point discrepancy
  is bounded by \(W_m\), its midpoint branch has a sharper endpoint-radius
  witness, and its analytic-edit discrepancy is at most \(2W_m\).
- Tests 25--26 remain pending because the learned conditional population,
  loss, and nuisance-isolation interfaces do not exist. The thirteenth layer
  is only the residual architecture/evaluation/certificate precursor.
- Test 27 has an eighth-layer exact-oracle precursor. A bounded positive
  Gaussian terminal potential produces analytic backward information,
  log-score/Hessian/Laplacian, reflected drift correction, integrated
  birth/death/replacement controls, invariant-normalized initializer, and
  terminal endpoint law; independent quadrature, finite differences, and the
  backward equation check those objects. The thirteenth layer supplies a
  distinct learned-residual primitive. The fourteenth now recomputes and
  composes the certified base, successful represented guide, and residual
  jump-edge increments for one process-valid candidate. It does not construct
  the combined continuous score/drift, initializer, or endpoint law, so the
  whole gate remains partial.
- Test 28 remains **OPEN**. It has an exact normalized conditional-initializer distribution record
  and endpoint record in the same scoped oracle. The ninth layer samples these
  three-state/two-Gaussian-mixture laws with the frozen categorical-resolution
  gate and checked Cholesky map. Mixed/continuous support handling, rejection
  RNG, the SIR sequence, and its frozen acceptance rule remain pending.
  Checkpoint twenty-
  five consumes bounded per-existing-occurrence tag-3 `raw64` prefixes only;
  it supplies neither a global initializer-control domain nor any output law
  and therefore does not close this test. Checkpoint twenty-six supplies the
  separate tag-7 address domain and bounded raw-prefix custody, but no stage/
  retry semantics, branch chronology, finite-resolution output transform,
  initializer distribution, accepted-configuration lineage mapping, or tag-3
  payload coordination. Checkpoint twenty-seven supplies fixed stages and
  canonical multiblock prefix allocation for enumeration, bounded rejection,
  SIR, and a branch-free reference candidate. It executes and validates none
  of those strategies' transforms, decisions, or output laws and creates no
  configuration or lineage mapping. Checkpoint twenty-eight now implements
  only the fixed reference strategy's (1+N+ND) finite transformer. It
  records exact binary64-induced targets, positive dyadic quotas and their TV
  errors, transforms every raw slot before count decoding, and returns a
  duplicate-stable canonical configuration. Its exact law assumes
  hypothetical product-uniform words; actual Philox output remains
  deterministic procedural evidence. Checkpoint twenty-nine then ran its sole
  preregistered 16,384-row-per-fixture deterministic-grid diagnostic. On the
  frozen deterministic address grid, all prespecified empirical discrepancies
  fell within the preregistered envelopes derived under the hypothetical
  product-uniform reference model. This supplies no Philox or sampling-law
  certificate. Checkpoint thirty adds the target-explicit deterministic point
  value
  \(G_{64}^{\mathrm{totalized}}(0,x)
  +R_{64}^{\mathrm{totalized}}(S,x,c)\) over base \(\Pi_N\), with exact
  represented-value addition and one final rounding. It deliberately excludes
  \(V_\phi(S,x)\) and a separate observation-only nuisance, but it neither
  exponentiates nor normalizes the factor and does not enumerate or select a
  state. Checkpoint thirty-one now enumerates every bounded resource-admitted
  all-atomic count vector, records its exact represented-parameter
  multiplicity-corrected base coefficient and the \(Z_N(a)\) completeness
  witness, and attaches one replay-validated checkpoint-thirty point to every
  state. It materializes no normalized mass or tilted weight, refuses every
  positive-dimensional reference, and performs no selection, rejection, SIR,
  RNG, or checkpoint-twenty-seven protocol binding. Checkpoint thirty-two
  applies directed exponentiation to the exact all-atomic factors, encloses the
  normalized ideal masses, constructs an exact positive rational proxy and a
  positive 64-bit Hamilton law with a certified TV bound, and selects from
  that dyadic law using one explicit word. It does not sample the ideal law
  exactly, consume RNG, bind checkpoint twenty-seven's stage-0 protocol, or
  admit an initializer. Checkpoint thirty-three binds exactly that one word to
  checkpoint twenty-seven's enumeration stage 0, validates the supplied
  checkpoint-thirty-two preparation before allocation, and forwards the
  parent's sole Philox word unchanged. For fixed preparation \(p\), replacing
  that live word source by an abstract \(U\sim\operatorname{Unif}(\mathrm{uint64})\),
  explicitly not identified with the live word source, gives the checkpoint-
  thirty-two dyadic law \(Q_p\). Separately, the fixed preparation inherits the
  \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\) bound. The
  live fixed-address word and output are deterministic point masses. It does
  not certify
  actual Philox uniformity, independence, or randomness, exact
  \(P_{\mathrm{operational},p}\) sampling,
  or global address one-shot use, and its protocol-bound flag is not initializer
  admission. Mixed/continuous support, a general conditional/tilted
  initializer and its benchmark beyond the fixed-grid diagnostic, lineage
  mapping, and tag-3 payload coordination remain absent. Test 28 therefore
  remains open.
  Checkpoint thirty-four then fixes the context, complete enumeration, and
  dyadic preparation inside one constructor factory and exposes only run and
  initialization indices. A successful live call returns a configuration valid
  as an all-atomic initial state and consumes exactly one inherited stage-0
  word, with no per-call context/preparation/RNG/word, retry, fallback, added
  namespace, or rollback. It retains the same abstract replacement theorem,
  but the fixed-address live result remains deterministic and no live
  initializer distribution is admitted. General, mixed/continuous,
  rejection/SIR/reference, lineage/tag-3, Brownian, drift, path, liveness, and
  sampler claims remain false. The historical module name does not promote
  initializer admission, and Test 28 remains open.
  Checkpoint thirty-five adds the fixed-index CP28 reference configuration's
  bootstrap lineage and dimension-shaped tag-3 prefixes. Its live output is
  still deterministic, its complete-capsule theorem is counterfactual and
  configuration-only, and no conditional/tilted or general initializer is
  admitted. Test 28 remains open.
  Checkpoint thirty-six prepares every fixed rejection-stage proposal and its
  CP30 point score, but the reserved word is uninterpreted and no acceptance,
  selection, returned initializer, live output law, or admission exists. Its
  failure-augmented abstract-word theorem supplies neither a failure bound nor
  a law conditional on success. Test 28 remains open.
  Checkpoint thirty-seven then implements only the conservative finite-
  resolution decision over that prepared batch. Every quota is certified
  before the first word-to-quota comparison, and the result is the first
  selected CP36 configuration or bounded exhaustion. Its product law uses
  fixed data and abstract iid words; its separate \(<A/2^{64}\) ideal-outcome
  TV comparison uses independent-coordinate ideal/dyadic Bernoulli sequences
  under a common-uniform coupling. Neither certifies the live words, exact
  ideal rejection, a normalized tilted initializer,
  selected-state lineage/tag-3 coordination, or initializer admission. Test 28
  therefore remains open.
  Checkpoint thirty-eight materializes the complete counterfactual fixed-\(B\)
  dyadic batch law and certifies a selected configuration only as structurally
  valid for one operational initial state. The live result remains
  deterministic, generic `initializer_admissible` is false, the augmented TV
  comparison is not directly reused unchanged by CP38 after selection
  conditioning, and no
  initialization-index-safe lineage/tag-3 output exists. Test 28 therefore
  remains open.
  Checkpoint thirty-nine attaches reverse-time-zero intensity, CP23 positional
  bootstrap lineage, and initialization-indexed local tag-3 prefixes to the
  exact CP38 selected configuration and attempt. Its prefixes are
  uninterpreted, the live result remains deterministic, and
  `initializer_admissible` remains false. It supplies neither a live
  initializer law nor generic admission, so Test 28 remains open.
  Checkpoint forty adds an exact normalized finite-resolution target
  conditional on one direct word-free successful batch and admits the exact
  selected CP39 state only through that narrow structural boundary. It also
  supplies the correctly selection-mass-scaled ideal/dyadic comparison. It does
  not provide a live source law, CP36 successful-batch/failure law, exact ideal
  rejection, global plug-in tilted normalization, SIR convergence, or
  all-strategy general admission. Test 28 therefore remains **OPEN**.
  Checkpoint forty-one adds only the conditional abstract product-uniform
  failure-aware mixture over CP36/CP37 predecision outcomes. Its factorization
  premise is explicitly unproved; no numeric failure or selection mass, live
  source/initializer law, exact ideal rejection, global analytic
  normalization, SIR result, or all-strategy admission follows. Test 28
  therefore remains **OPEN**.
  Checkpoint forty-two makes the \(V\)-only staging constructive only for its
  bounded reference evaluator. Because universal live equivalence and CP41's
  factorization premise remain unproved, it supplies no live
  initializer/source law or admission. Test 28 remains **OPEN**.
  Checkpoint forty-three closes only its CP43-defined supplied-word reference
  composite under explicit typed-totality and abstract-source premises. It
  does not identify that composite with the live CP36/CP37 map, discharge
  CP41's live-parent factorization premise, materialize numeric fibers or
  masses, or establish a live source, initializer law, or admission rule. Test
  28 remains **OPEN**.
  Checkpoint forty-four acquires one complete CP27 capsule and routes its exact
  split through that CP43 composite, but its returned-result-conditional
  construction proves neither a live source law nor an unconditional adapter
  or initializer law. Test 28 remains **OPEN**.
  Checkpoint forty-five proves instead that the fixed returned-request live
  source is a point mass and that at most k free uint64 coordinates impose the
  stated conditional-success support obstruction. It introduces no positive
  live source or initializer law, so Test 28 remains **OPEN**.
  Checkpoint forty-six adds cached fixed/external source descriptors but
  realizes and samples no external request law, proves no conditioning-event
  positivity, and admits no initializer. Test 28 remains **OPEN**.
  Checkpoint forty-seven accepts one externally supplied full capsule, but
  certifies neither the provider law nor an initializer law or admission.
  Test 28 remains **OPEN**.
  Checkpoint forty-eight obtains an exact complete byte block and delegates
  its bijective word image to checkpoint forty-seven, but certifies no
  backend or operating-system source law, complete-success conditioning law,
  initializer law, or admission. Test 28 remains **OPEN**.
  Checkpoint forty-nine records the desired one-request enriched semantic law
  only under an explicitly unverified backend/full-block/complete-success and
  typed-total-semantics premise. Its concrete selected result is custody and
  nonempty-fiber evidence under that premise, not operational source-law or
  initializer admission. Test 28 remains **OPEN**.
- Test 29 has multiple distinct precursors. The seventh layer supplies a
  process-owned draw from \(q_s^0/\Lambda_s^0\), a certified sampled
  base-energy integrand \(\gamma_J(s)\Lambda^0(x)e^{\Delta V}\), and an
  outward envelope ratio. The eighth layer independently supplies exact
  conditional total family rates and reset-destination Gaussian mixtures for
  its known law. The ninth layer supplies exact known-law conditional paths
  and induced reset marks by time reversal. The tenth layer supplies the
  deterministic state-dependent reference candidate intensity before RNG and
  preflights all reachable normalized-reference routes. The eleventh layer
  supplies the real-arithmetic guide contribution
  \(\log(H_m/\epsilon_m)\). The twelfth admits a represented scalar guide
  value and direct edit envelope only when both point evaluations pass the
  directed range gate; it provides neither totality nor liveness on unbounded
  coordinate charts. The thirteenth supplies a separately certified residual
  value and same-condition state-pair difference, with the global residual
  log-oscillation bound (2B_R) and time-specific directed gate witnesses.
  The fourteenth composes all three represented jump-log contributions on the
  same revalidated candidate and returns separate outward-rounded
  mathematical and operational aggregate log witnesses. It deliberately does
  not exponentiate that witness, construct a rate-space controlled envelope
  or total learned exit, establish guide liveness, implement finite-resolution-
  safe waiting and acceptance decisions, or simulate the frozen learned
  conditional jump subproblem. The fifteenth supplies a separately certified
  totalized surrogate guide edit over the resource-admitted capped domain, and
  the sixteenth analogously supplies a checkpoint-private operational residual
  point/edit at the exact typed active tiny-gate failure. The seventeenth
  selects their explicit common operational point target, composes both with
  the checkpoint-private base for all three edit families, and rounds the
  exact rational aggregate once. The eighteenth exponentiates that exact edge,
  records a correctly rounded successful-candidate integrand and its outward
  interval, and constructs no-RNG instantaneous/global controlled-total-exit
  upper bounds. It still does not compute the active total exit, admit the
  route draw, or make a waiting/acceptance decision. The nineteenth adds one
  successful-return local wait, one inherited finite-resolution route, and an
  exact variable-word Bernoulli for the actual represented quotient
  \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\), with `proposal_time` as the
  authoritative local-clock timestamp and one continued Philox stream. Its
  focused route evidence is all-atomic. The twentieth adds bounded rejection-
  clock continuation, exact rejected-parent reuse, mandatory accepted-state
  intensity/envelope refresh, terminal interval-exhaustion custody, and cap
  refusal before a speculative wait. It does not supply continuous-destination
  operational evidence, unconditional completion, an exact frozen-jump law,
  counter-keyed lineage, or a conditional path.
  The twenty-first adds record-specific same-runtime replay evidence for
  continuous birth and both 2D-to-3D and 3D-to-2D reset replacements. It
  retains exact pre/post Philox snapshots, labelled occurrences, exact
  binary64 coordinates, dimensions, multiplicities, and represented analytic
  factors. It does not supply an exact categorical/integer/Gaussian law,
  bounded normal-word trace, Test-29 distribution recovery, unconditional
  completion, counter-keyed lineage, or a conditional path.
  The twenty-second integrates one such route witness at every completed
  proposal of a successfully returned bounded checkpoint-twenty loop. It
  replays the complete entry-to-exit waiting/route/acceptance stream,
  including the terminal waiting prefix, and binds the ordered witnesses to
  the parent iterations. This strengthens finite-resolution route custody for
  the bounded-loop precursor but still does not establish the ideal route or
  frozen-jump distribution required by Test 29.
  The twenty-third supplies a direct per-domain address namespace and a
  deterministic lineage annotation of that validated bounded-loop result. It
  does not cause the parent to consume those addresses or upgrade the jump law,
  so Test 29 remains open.
  The twenty-fourth instead runs a distinct bounded local loop through direct
  tag-6 operational epochs. Every candidate epoch integrates one exact loop
  iteration, route witness, and lineage transition; an active stochastic
  terminal remains on tag 6. This closes keyed finite-resolution execution
  custody only. It does not upgrade the route or rounded clock to their ideal
  laws or establish unconditional completion, so Test 29 remains open.
  The twenty-fifth adds only bootstrap initializer-prefix custody and does not
  alter the jump route, waiting, acceptance, rounded clock, or frozen-jump law.
  The twenty-sixth adds only global initializer-control prefix custody and also
  leaves those jump-law objects unchanged. The twenty-seventh adds only fixed
  initializer-protocol allocation and likewise changes no wait, route,
  acceptance, controlled-exit, or frozen-jump law. The twenty-eighth transforms
  only the reference initialization capsule and also changes none of those
  jump-law objects. The twenty-ninth only evaluates that transform's frozen-
  grid discrepancies and likewise changes no wait, route, acceptance,
  controlled-exit, or frozen-jump law. Checkpoint thirty evaluates only a
  deterministic time-zero log factor and likewise changes no wait, route,
  acceptance, controlled-exit, destination, or frozen-jump law. Checkpoint
  thirty-one only enumerates static all-atomic initial-support coefficients
  and attached point records; it also changes none of those jump-law objects.
  Checkpoint thirty-two normalizes and selects only that static all-atomic
  initial support; it likewise changes no wait, route, acceptance,
  controlled-exit, destination, or frozen-jump law.
  Checkpoint thirty-three only binds that static selection to one tag-7
  stage-0 word; it also changes none of those jump-law objects.
  Checkpoint thirty-four only fixes and exposes the resulting all-atomic
  configuration-construction capability; it likewise changes none of those
  jump-law objects.
  Checkpoint thirty-five only coordinates one finite initial configuration
  with bootstrap lineage and tag-3 prefixes; it likewise changes none of those
  jump-law objects.
  Checkpoint thirty-six only prepares finite initial proposals and their
  deterministic point scores from tag-7 stage-1 words; it makes no jump wait,
  route, acceptance, destination, or frozen-jump-law change.
  Checkpoint thirty-seven only interprets the reserved initial-rejection words
  through its finite conservative quotas; it likewise changes no jump wait,
  route, destination, controlled exit, or frozen-jump law.
  Checkpoint thirty-eight only annotates that fixed initial decision batch with
  counterfactual masses and structural selected-state validity; it likewise
  changes no jump wait, route, destination, controlled exit, or frozen-jump
  law.
  Checkpoint thirty-nine only coordinates that selected initial state with
  intensity, positional lineage, and local tag-3 prefixes; it also changes no
  jump wait, route, destination, controlled exit, or frozen-jump law.
  Checkpoint forty only annotates that coordinated initial result with its
  fixed-batch target and structural state/no-state boundary; it likewise
  changes no jump wait, route, acceptance, destination, controlled exit, or
  frozen-jump law.
  Checkpoint forty-one is a descriptive abstract source-law ledger and calls no
  CP36--CP40 operational method; it likewise changes no jump wait, route,
  acceptance, destination, controlled exit, or frozen-jump law.
  Checkpoint forty-two evaluates only the bounded initial-rejection
  predecision/decision reference semantics and likewise performs no jump wait,
  route, destination, controlled-exit, or frozen-jump-law operation.
  Checkpoint forty-three only composes the supplied-word initial-rejection
  reference semantics and adds typed reference failures and custody checks. It
  likewise performs no jump wait, route, acceptance, destination, controlled-
  exit, or frozen-jump-law operation.
  Checkpoint forty-four adds source-capsule custody and one CP43 combined call,
  but performs no jump wait, route, acceptance, destination, controlled-exit,
  or frozen-jump-law operation.
  Checkpoint forty-five is operation-free at the source/semantic layer and
  only records a source-support theorem; it likewise performs no jump wait,
  route, acceptance, destination, controlled-exit, or frozen-jump-law
  operation.
  Checkpoint forty-six is likewise descriptor-only at the source/semantic
  layer and performs none of those jump-law operations.
  Checkpoint forty-seven transports one supplied initial-rejection capsule
  through CP43 and likewise performs no jump wait, route, acceptance,
  destination, controlled-exit, or frozen-jump-law operation.
  Checkpoint forty-eight changes only the byte-source acquisition boundary and
  delegates the decoded capsule to checkpoint forty-seven. It likewise
  performs no jump wait, route, acceptance, destination, controlled-exit, or
  frozen-jump-law operation.
  Checkpoint forty-nine is nonexecuting with respect to source acquisition and
  CP43/CP42 semantics. It only describes and structurally admits the
  premise-qualified semantic reference law and likewise performs none of
  those jump-law operations. Test 29 therefore remains **OPEN**.
- Test 30 remains pending: checkpoint twenty-three supplies positional
  persistent-lineage and left/right Brownian address reservations only. There
  is no consumed Brownian stream, additive coarse/fine coupling,
  lineage-aware split-step conditional path, or coupled step-halving
  implementation. Checkpoint twenty-four consumes only tag-6 operational
  epochs and zero-word deterministic tag-2 terminal bindings; it does not
  change this disposition. Checkpoint twenty-five consumes only tag-3
  initializer prefixes for an already existing bootstrap; it consumes no
  Brownian stream and likewise does not change this disposition. Checkpoint
  twenty-six consumes only tag-7 control prefixes and also leaves Test 30
  unchanged. Checkpoint twenty-seven reuses only those tag-7 control prefixes;
  it consumes no Brownian stream and leaves Test 30 unchanged. Checkpoint
  twenty-eight also consumes only those tag-7 reference-strategy words, not a
  tag-4 or tag-5 Brownian stream, and leaves Test 30 unchanged. Checkpoint
  twenty-nine only assesses the retained tag-7/stage-4 words; it consumes or
  assesses no Brownian stream and also leaves Test 30 unchanged.
  Checkpoint thirty consumes no RNG or Brownian stream and constructs no path,
  so it also leaves Test 30 unchanged. Checkpoint thirty-one likewise consumes
  no RNG or Brownian stream and constructs no path, so it leaves Test 30
  unchanged. Checkpoint thirty-two accepts an explicit word as data, consumes
  no RNG or Brownian stream, and constructs no path, so it also leaves Test 30
  unchanged. Checkpoint thirty-three causes its checkpoint-twenty-seven parent
  to materialize one tag-7 initializer-control word, but consumes no tag-4 or
  tag-5 Brownian stream and constructs no path, so it likewise leaves Test 30
  unchanged.
  Checkpoint thirty-four uses that same single inherited tag-7 word for a fixed
  all-atomic configuration and consumes no Brownian stream or path state, so it
  also leaves Test 30 unchanged.
  Checkpoint thirty-five consumes only tag-7 reference and tag-3 initializer-
  prefix words, no tag-4/tag-5 Brownian stream or path state, and therefore
  also leaves Test 30 unchanged.
  Checkpoint thirty-six materializes only tag-7 stage-1 proposal and reserved
  words, consumes no tag-4/tag-5 Brownian stream, and constructs no path state,
  so it also leaves Test 30 unchanged.
  Checkpoint thirty-seven reuses only those already materialized tag-7 words,
  consumes no tag-4/tag-5 Brownian stream, and constructs no path state, so it
  likewise leaves Test 30 unchanged.
  Checkpoint thirty-eight adds no word or RNG operation, consumes no
  tag-4/tag-5 Brownian stream, and constructs no path state, so it likewise
  leaves Test 30 unchanged.
  Checkpoint thirty-nine consumes only CP39-local tag-3 initializer prefixes,
  no tag-4/tag-5 Brownian stream or path state, and therefore also leaves Test
  30 unchanged.
  Checkpoint forty adds no RNG or word consumption, consumes no tag-4/tag-5
  Brownian stream, and constructs no path state, so Test 30 remains pending.
  Checkpoint forty-one consumes no source-law \(V/W\) coordinate, no
  tag-4/tag-5 Brownian stream, and no caller/global RNG. It performs no
  CP36--CP40 operational call. Transitive certification/live-binding may
  execute CP39's local fixed Philox runtime probe of three raw words for
  procedural custody. That probe is not a live source draw, result, or fiber
  enumeration, and it consumes no tag-4/tag-5 Brownian or source-law
  coordinate. CP41 constructs no path state, so Test 30 remains pending.
  Checkpoint forty-two accepts explicit \(V/W\) tuples as reference-evaluator
  inputs, invokes no RNG, consumes no tag-4/tag-5 Brownian stream, and
  constructs no path state. Test 30 remains **PENDING**.
  Checkpoint forty-three also accepts explicit supplied words, invokes no live
  RNG or Brownian consumer, and constructs no path state. Its selected runtime
  fingerprint and public replay checks are procedural custody, not source-law
  or coupled-path execution. Test 30 remains **PENDING**.
  Checkpoint forty-four consumes no tag-4/tag-5 Brownian stream and constructs
  no path state; its CP27 allocation and CP43 execution remain confined to the
  initial-rejection capsule. Test 30 remains **PENDING**.
  Checkpoint forty-five allocates no source, consumes no tag-4/tag-5 Brownian
  stream, and constructs no path state. Its inherited deterministic local
  Philox ancestry probe is procedural custody, not source-law or path
  execution. Test 30 remains **PENDING**.
  Checkpoint forty-six also allocates no source and consumes no Brownian
  stream. Its cached descriptors and optional ancestry revalidation
  construct no path state, so Test 30 remains **PENDING**.
  Checkpoint forty-seven obtains only externally supplied initial-rejection
  words, consumes no tag-4/tag-5 Brownian stream, and constructs no path
  state. Test 30 remains **PENDING**.
  Checkpoint forty-eight acquires only the exact byte block for that same
  initial-rejection capsule. Its byte/word transform and CP47 delegation
  consume no tag-4/tag-5 Brownian stream and construct no path state. Test 30
  remains **PENDING**.
  Checkpoint forty-nine acquires no byte or word, consumes no Brownian stream,
  and constructs no path state. Its optional live-ancestry revalidation
  remains semantic- and source-nonexecuting. Test 30 remains **PENDING**.
- Test 31 has the exact analytic forward terminal-reference TV for the scoped
  nonstationary mixture. It has no frozen pass/failure threshold and supplies
  no sample-based real-domain diagnostic.
- Test 32 combines seventh-layer process/checkpoint/provenance checks with
  eighth-layer support, cap-one type-changing, cap-two multiplicity,
  no-clipping, transition-certificate, extreme-coordinate, underflow/overflow,
  unresolved-clock, record-forgery, work-limit, and immutable-output checks.
  The ninth adds scoped marginal/path resolution, reflection-boundary,
  zero-clock identity, resource, nested-provenance, and 3,000-path joint-law
  checks. The tenth adds no-RNG clean-hold/structural-zero separation, active
  binary64 rate refusal, schedule-breakpoint collision detection, nested
  categorical preflight, exact-key/signed-zero provenance, intensity-tamper
  rejection, and mixed-dimensional stream-identity checks. The eleventh adds
  canonical fixed-observation binding, exact Poisson-overflow and covariance
  witnesses, retained value/edit/regularity domination, resource refusal,
  non-Gershgorin covariance refusal, record tamper rejection, large plain-key
  handling, and explicit model-level/non-operational scope. The twelfth adds
  directed endpoint/width checks, structural-zero represented error,
  exhaustive atomic values and all edit families, continuous and overflow
  values, one-ULP out-of-range refusal, nonfinite/no-fallback behavior, exact
  point/edge provenance, one-shot iterable handling, sealing, live-certificate
  reconstruction, sampler-boundary rejection, and the explicit absence of an
  RNG, derivative, or sampling surface. The thirteenth adds direct-time
  one-ULP boundaries, mathematical/operational gate separation, active-gate
  underflow refusal, active-row isolation, physical-coordinate derivative and
  Laplacian scaling, source/destination clean-hold Hessian graphs, hidden-leaf
  hook and model-ancestry refusal, residual-role/schema/provenance cross-pair
  rejection, live mutation detection, and explicit no-sampler/no-time-
  derivative scope. The fourteenth adds same-candidate source/destination,
  edit-kind, reverse/direct-time, context-schema, outcome, checkpoint,
  provenance, and live-state custody; exact-rational one-round summation;
  independent component and aggregate-bound oracles; all three edit families;
  duplicate routes; unequal-dimensional replacement; retained/overflow
  outcomes; one-ULP, signed-zero, subnormal, overflow, out-of-range,
  mid-flight-mutation, record-forgery, and shared/view/offset-storage refusal;
  and the explicit absence of exponentiation, RNG, drift, or sampler surfaces.
  The fifteenth adds typed numerical/range fallback, a full capped-domain
  resource preflight, exact midpoint and \(W_m\)/fallback/\(2W_m\) checks,
  exact-rational operational coboundaries, one-ULP active-time liveness,
  streaming state digests, runtime/resource replay, hostile non-fallback
  exception checks, and explicit surrogate-target/no-derivative/no-rate/no-RNG
  scope. The sixteenth adds bitwise preservation of successful residual
  points, both strictly active staged-gate underflow modes, exact-rational
  gate/core multiplication and endpoint coboundaries, one-round and outward
  witnesses, private checkpoint-model evaluation, detached batch snapshots,
  DAZ/FTZ and rounding-mode refusal, streaming digests, custody/tamper replay,
  narrow exception handling, and explicit no-derivative/no-rate/no-RNG scope.
  The seventeenth adds mandatory explicit target-policy selection, exact
  endpoint-fraction composition and one final rounding for all three edit
  families, transitive component/runtime/context/candidate custody, external-
  plus-private base custody, pairwise base/residual storage separation,
  replay/tamper/cross-owner refusal, and the explicit absence of exponentiation,
  rate, clock, RNG, drift, initializer, path, and sampler APIs. The eighteenth
  adds exact-edge/direct-product exponentiation, 192--1536 adaptive interval
  resolution, hard midpoint and underflow/overflow boundaries, no-RNG
  structural-zero and finite-atomic domination checks, parent-snapshot/live-
  custody attacks, and explicit refusal of route, waiting, acceptance, drift,
  path, and sampler admission. The nineteenth adds ideal-prefix MSB-order and
  directed-clock witnesses, inclusive ideal endpoint/strict represented-
  interior behavior, Philox state continuity across the inherited route and
  exact represented-ratio Bernoulli, bounded-work refusals, parent replay, and
  record/owner/stream tamper checks. It explicitly makes no counter-key,
  continuous-route, loop, lineage, path, liveness, or full-sampler claim.
  The twentieth adds contiguous iteration/state/time/RNG chains, exact
  rejection-parent identity, accepted-state refresh replay, structural-zero
  stop precedence, terminal-wait custody, no-RNG active cap refusal, and
  aggregate record/owner/context/tamper checks. Its evidence remains all-atomic
  and it explicitly makes no exact-route, continuous-destination,
  unconditional-completion, exact frozen-jump, counter-key, lineage, path,
  liveness, or full-sampler claim.
  The twenty-first adds exact pre/post Philox snapshot reconstruction,
  same-runtime candidate/post-state replay, genuine unequal-dimensional
  continuous resets in both directions, death-without-resampling, exact
  coordinate/factor/type/occurrence custody, and rejection of the known
  re-digested candidate and post-state attacks. It explicitly makes no ideal
  categorical/integer/Gaussian, bounded-normal-word, distribution-recovery,
  liveness, path, or full-sampler claim.
  The twenty-second adds exact loop-entry/exit snapshots, replay of every
  waiting and acceptance raw-word prefix plus the terminal waiting prefix,
  one positionally bound checkpoint-twenty-one witness per completed proposal,
  count/classification/digest attacks, cross-transcript splices, offline-RNG
  isolation, and explicit nontransactional failure after a successful parent
  loop. It makes no ideal-route, unconditional-completion, liveness, target,
  lineage, path, or full-sampler claim.
  The twenty-third adds exact direct-address limbs and domain bounds,
  same-runtime empty-state reconstruction, duplicate-safe positional bootstrap,
  accepted/rejected birth/death/replacement lineage algebra, exact object
  custody, serial/chronology/ledger and live-coordinate bounds, parent-result
  revalidation, hostile re-digested record and cross-owner/run/step refusal,
  and explicit negative flags for every unimplemented stream-consumption,
  coupling, target, liveness, path, and sampler claim.
  The twenty-fourth adds direct tag-6 address and empty-state reconstruction,
  active-epoch wait/route/accept continuity, stochastic-versus-deterministic
  terminal-domain separation, no-carry epoch isolation, exact candidate-epoch
  iteration/route/lineage binding, caller-RNG isolation, proposal-cap refusal,
  exact tag integers, canonical context/per-proposal digest custody, bounded
  pre-hash candidate/event/lineage resources, deep supplied wait/iteration/
  evidence validation, exact parent-certificate objects, event-identity
  projection custody, and hostile address, transcript, owner, replay, and
  claim-flag checks. It explicitly leaves legacy tag-1 proposal receipts,
  random-word tag-2 terminal execution, occurrence/initializer/Brownian
  streams, target, liveness, path, and sampler claims false.
  The twenty-fifth adds the exact bootstrap gate; tag-3, step-zero address and
  prefix replay; 64-record, 4,096-word per-occurrence, and 65,536-word aggregate
  preflights; canonical raw-word and step types; unchanged input-state and
  event identity; no-caller-RNG behavior; exact parent/certificate custody;
  global pre-loop replay baselines; and hostile redigested, cross-owner,
  mutation, sealing, and output-law-claim checks. It explicitly certifies only
  uninterpreted bootstrap prefix custody, leaving the global initializer-
  control domain, output law, Brownian, target, liveness, path, and sampler
  claims false.
  The twenty-sixth adds direct tag-7 address and parent-domain separation,
  initialization/stage/attempt coordinate custody, canonical-plan and
  aggregate preflight, empty-plan no-op, maximum-prefix replay, no upper carry,
  no-caller-RNG behavior, declared nested identity relations, validation-window
  mutation custody, same-digest alien-parent refusal, sealing, and explicit
  negative flags for every
  unimplemented stage/branch/output/lineage/tag-3/Brownian/target/path/sampler
  claim. It certifies the namespace and bounded prefix custody only.
  The twenty-seventh adds the exact four-strategy tuple, stages and roles
  0--4, multiblock work-item flattening, fixed-budget/resource preflight,
  complete parent-prefix materialization, canonical chronology, exact parent-
  plan and raw-word identity, owner-baseline mutation custody, deterministic
  reissue, sealed construction, and hostile type/length/plan/role/flag checks.
  It explicitly leaves every branch, transform, initializer-law,
  configuration, lineage, tag-3, Brownian, target, path, liveness, and sampler
  claim false.
  The twenty-eighth adds exact ancestry-derived count/type target ratios,
  positive Hamilton quota and exact-TV records, the fixed (1+N+ND) word-role
  partition, a symmetric top-53 midpoint normal-quantile codebook, complete
  inactive/padding transformation before cardinality decoding, stable
  duplicate maps, exact parent/result replay, large-rational work bounds,
  hostile nested-type/equality preflight, sealing, and no-caller-RNG behavior.
  It certifies only a finite configuration transform and the law induced under
  hypothetical product-uniform words. Exact continuous-reference, actual-
  Philox, other-strategy, conditional/tilted-initializer, lineage, tag-3,
  Brownian, target, path, liveness, and sampler claims remain false.
  The twenty-ninth adds a sealed no-search/no-exclusion/no-retry plan, two
  complete ordered raw corpora, four public checkpoint-twenty-eight anchors,
  exact rational statistics and upward-rounded thresholds, immutable candidate
  manifests, STARTED-v2 and terminal-v2 claim-file identity binding, one-shot
  attempt custody, and independent replay. All five comparisons passed, and
  both post-run audits report P0=P1=P2=0. Its negative flags remain false for
  actual Philox uniformity/independence/randomness, the actual finite
  pushforward law, the continuous reference law, initializer admission, and
  Test-28 closure.
  The thirtieth adds mandatory target-policy and selected-\(\Pi_N\)-base
  binding; exact guide-state equality; reverse-zero/direct-horizon custody;
  exclusion of base energy and a separate observation-only nuisance; exact
  rational component addition with one final rounding; outward point and
  rounding-error witnesses; normal, halfway, subnormal, signed-zero, and
  overflow arithmetic oracles; typed-guide-fallback and untyped-failure
  behavior; one-pass many-type adaptation; bounded configuration, context,
  integer, and runtime-identity resources; process-local owner snapshots and
  replay; external/private residual storage separation; no-RNG sentinels;
  sealing; and hostile record, state, certificate, owner, process, horizon,
  context, runtime, and cross-owner refusal. It explicitly leaves
  loaded-code and conditioning-adapter-origin authentication, the analytic
  conditional/posterior identity, exponentiation, normalization, support
  enumeration, rejection, SIR, selection, initialization, path, and sampler
  claims false.
  The thirty-first adds exhaustive resource-bounded all-atomic enumeration,
  exact coefficient and completeness identities, point-record replay, bounded
  preflight, and hostile mutation/substitution refusal. The thirty-second adds
  adaptive directed exponential and normalized-mass intervals, exact proxy
  and Hamilton arithmetic, independent TV witnesses, half-open endpoint probes
  for every interval in the tested tables, exact replay/custody checks, and
  no-RNG sentinels. The thirty-third adds exact checkpoint-twenty-seven owner
  binding; the literal \(((0,0,1),)\) parent plan; direct key \((r,7)\) and
  counter \((0,i,0,0)\); validation-before-allocation; shared composer, guide,
  and residual ancestry; unchanged sole-word forwarding; exact parent/result
  custody; owner-baseline mutation refusal; and hostile plan, address, word,
  ancestry, certificate, and claim-flag checks. These claims remain limited to
  deterministic all-atomic support, explicit-word dyadic selection, and that
  one-word protocol binding. For fixed preparation its distributional statement
  uses an abstract uniform replacement source \(U\), not identified with the
  deterministic live word source, though their uint64 values may coincide;
  they do not certify the Philox law, admit an
  initializer, or provide a learned/general conditional path.
  The thirty-fourth adds factory-owned context, enumeration, and preparation;
  a two-integer live constructor API; complete exact parent and callback
  chronology/custody; one inherited parent word per successful construction;
  deterministic same-address replay; and explicit positive certification that
  the resulting all-atomic configuration is valid as an initial state. Its
  only positive output/pushforward-law theorem is \(f_p(U)\sim Q_p\) for an
  abstract ideal
  \(U\sim\operatorname{Unif}(\mathrm{uint64})\), explicitly not identified with
  the live word source, though their uint64 values may coincide. The live
  fixed-address output is a point mass, and the separate
  inherited TV witness is
  \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\), not a
  point-mass-to-\(Q_p\) bound. Actual RNG-law, live initializer distribution,
  initializer admission, generality, mixed/continuous, other-strategy,
  lineage/tag-3, Brownian, drift, path, liveness, and sampler claims remain
  false.
  The thirty-fifth adds fixed-run construction, reverse-time-zero intensity,
  bootstrap-lineage, dimension-shaped tag-3-prefix, address, mapping, and
  custody checks. Its 64/64 focused pass and 173/173 direct-parent regression
  remain scoped deterministic software evidence; no live law, initializer
  admission, Brownian/path, or sampler claim follows.
  The thirty-sixth adds fixed-budget rejection-stage proposal transformation,
  CP30 point scoring, exact \(q-U\le0\) witnesses, reserved-word custody, and a
  conditional failure-augmented abstract pushforward. Its focused 115/115 pass
  and no-cache 171/171 direct-parent regression are scoped software evidence
  and supply no
  decision, acceptance, initializer admission, Brownian/path, or sampler claim.
  The thirty-seventh adds exact-quota branches, adaptive Decimal enclosure,
  threshold-before-decision chronology, exact half-open boundary comparisons,
  first-selected/exhausted result matrices, replay validation, and hostile
  custody checks. Its focused 44/44 pass and no-cache CP36 115/115 regression
  are scoped software evidence and supply no live source law, exact ideal
  rejection, initializer admission, Brownian/path, or sampler claim.
  The thirty-eighth adds exact fixed-\(B\) mass partitioning, duplicate
  aggregation, the all-zero/positive-selection definition boundary, streamed
  projection custody, and strict augmented ideal/dyadic theorem flags. Its
  no-cache focused and parent-regression suites passed 45/45 and 44/44,
  respectively, and static gates plus the independent source audit passed; no
  live source law, selected-
  conditioned ideal/dyadic guarantee, generic initializer admission,
  Brownian/path, or sampler claim follows.
  The thirty-ninth test matrix adds exact CP38 result/configuration identity,
  exact CP37 selected-attempt-index provenance, reverse-time-zero intensity,
  duplicate-safe positional lineage, direct
  address injectivity and legacy-suffix disjointness, dimension-shaped prefix
  replay, selected-empty/exhausted separation, validation chronology, resource
  refusal, and hostile ancestry/callback/route-state custody. Its frozen
  focused and direct-parent suites passed 65/65 and 45/45, respectively, and
  its independent final reviews returned **P0=P1=P2=0**; its disposition is
  **PASS WITH EXPLICIT SCOPE LIMITS**. No live law, semantic payload,
  coordinate generation,
  generic admission, Brownian/path, or sampler claim follows.
  The fortieth test matrix adds exact augmented normalization, positive/zero
  selection definitions, duplicate aggregation, raw strict and clipped non-
  strict conditioned-comparison arithmetic, word-free-law versus custody
  digests, exact selected-object/target-row-ordinal separation, selected-empty
  admission, exhausted target-with-no-state behavior, one-parent chronology,
  validation without construction, exact resource refusal, and hostile
  ancestry/callback/owner/public-private-surface custody. Forty-five focused
  tests passed; inherited exact-hash CP39 direct-parent evidence remains
  applicable. The disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. No live/
  unconditional law, global tilt, all-strategy admission, Brownian/path, or
  sampler claim follows.
  The whole-method
  test remains pending because no learned/general conditional path is
  simulated.

Accordingly, the forward-process portions of Tests 2--6 have executable
evidence, and the cap-one/two-type mixed parts of Tests 2--5 now have the
additional scoped evidence just listed. Arbitrary-cap and whole-method forms
remain partial. Tests 7--10 have executable theorem/oracle evidence in the
scopes stated above. Tests 11--12 now have the scoped sixth-, seventh-, tenth-,
eleventh-, twelfth-, thirteenth-, fourteenth-, fifteenth-, sixteenth-,
seventeenth-, and eighteenth-layer
evidence
just listed but remain partial as whole-method gates. The
eighth layer closes the absence of a type-changing mixed known-law control
only in its declared cap-one scope. The ninth adds the exact compact known-law path
comparator in that same scope; neither replaces a general production
conditional simulator.

Tests 13--18 now also have executable evidence in the exact endpoint-
observation scope stated above. The fifth layer supplies the scoped Test
19--22 and 24 evidence just listed, while the eleventh strengthens the
model-level range/regularity part of Test 24 and the twelfth adds the
successful-only represented-value part; Test 23 remains partial. The eighth
and ninth layers supply the scoped Test 27--29, 31, and 32 precursors above;
the tenth adds the reference-clock precursor for Tests 29 and 32, the
eleventh adds the model-level guide-range precursor, and the twelfth adds its
successful-only represented jump-value successor. The thirteenth adds the
separate residual value/state-pair and physical-coordinate certificate
precursor for Tests 27, 29, and 32, and the fourteenth adds the successful
same-candidate log-space composition precursor for Tests 27, 29, and 32. The
fifteenth adds the operational-surrogate guide-totalization precursor for
Tests 24, 29, and 32, without changing the analytic target or the successful-
only composer. The sixteenth adds the operational-surrogate residual tiny-gate
precursor for Tests 29 and 32, likewise without changing checkpoint thirteen
or the successful-only composer. The seventeenth adds the explicit
operational-target and compatible log-space composition precursor for Tests 29
and 32 while leaving checkpoint fourteen unchanged. The eighteenth adds the
operational-surrogate rate-space domination precursor for Tests 29 and 32,
without promoting the route, clock, acceptance, or sampler. The nineteenth adds
the successful-return local operational-clock precursor for Test 4 and the
scoped wait/route/represented-ratio and custody precursors for Tests 29 and 32.
It does not promote the loop, continuous-destination operational evidence,
counter-keyed lineage, path, liveness, or sampler. The twentieth adds bounded
successful-return coordination and fail-closed proposal-cap precursors for
Tests 4, 29, and 32. It does not promote continuous-destination operational
evidence, unconditional completion, an exact frozen-jump law, counter-keyed
lineage, path, liveness, or sampler.
The twenty-first adds the record-specific continuous-destination custody
precursor for Tests 29 and 32: exact endpoint dimensions and float tuples,
represented route factors, and same-runtime Philox replay. It does not promote
the finite-output route to the analytic route law and therefore does not close
Test 29's distributional recovery requirement.
The twenty-second adds the ordered bounded-loop custody precursor for Tests 29
and 32: one route-evidence record per completed proposal, exact waiting and
acceptance raw-word-prefix replay, terminal-prefix replay, and exact full-loop
entry/exit binding. It still does not promote the finite-output route to an
ideal law or prove unconditional completion, so Test 29 remains open.
The twenty-third adds a prerequisite for Tests 29, 30, and 32: a direct
run/domain/step/occurrence/proposal address schema and a deterministic
persistent-lineage projection over a validated bounded-loop result. Because the
parent still uses its sequential stream and no Brownian address is consumed or
coupled, Test 29 remains open and Test 30 remains pending.
The twenty-fourth adds the bounded operational-epoch-keyed execution precursor
for Tests 29 and 32. It consumes direct tag-6 active epochs with integrated
route and lineage custody, but leaves the legacy tag-1 namespace unused and
consumes no initializer, occurrence, or Brownian stream. The finite-resolution
route, bounded success condition, and absent Brownian coupling keep Test 29
open and Test 30 pending.
The thirtieth adds the deterministic initial guide-plus-residual point-factor
precursor for Tests 28 and 32. It binds the selected \(\Pi_N\) base and one
canonical state/context evaluation, but creates no normalized initializer and
consumes no RNG. It therefore leaves Test 28 open, Test 29 open, and Test 30
pending.
The thirty-first adds the exact bounded all-atomic support/coefficient
precursor for Tests 1, 28, and 32. It verifies the represented-parameter local,
cardinality, and global base-coefficient identities and attaches one validated
checkpoint-thirty point per state, but creates no normalized or selected
initializer and consumes no RNG. It therefore also leaves Test 28 open, Test
29 open, and Test 30 pending.
The thirty-second adds the deterministic all-atomic finite-resolution
operational tilted-law precursor for Tests 28 and 32. It encloses the ideal
normalized masses, certifies a positive dyadic approximation, and interprets
one explicit uint64 word, but does not obtain or certify that word, bind the
initializer protocol, admit an initializer, or cover mixed/continuous support.
It therefore also leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-third adds the exact one-word all-atomic protocol-binding precursor
for Tests 28 and 32. It obtains the checkpoint-twenty-seven enumeration-stage
word and forwards it unchanged, but does not certify the word law, sample the
ideal law exactly, admit an initializer, or cover mixed/continuous support.
It therefore also leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-fourth adds a fixed all-atomic configuration-construction precursor
for Tests 28 and 32. It owns support enumeration and dyadic preparation before
any live call; each successful live construction returns a valid initial
configuration. Its live fixed-address output is deterministic, while its sole
positive output/pushforward-law theorem uses an abstract uniform replacement
source and its separate inherited TV witness compares the ideal operational
law with the dyadic law. It therefore does not establish the live initializer
distribution or admission required by Test 28 and likewise leaves Test 28
open, Test 29 open, and Test 30 pending.
The thirty-fifth adds a fixed-index finite reference construction-to-bootstrap-
lineage and tag-3-prefix precursor for Tests 28 and 32. The live result remains
deterministic and no general initializer law is admitted; it therefore also
leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-sixth adds fixed-budget rejection proposal-and-score preparation as
a precursor for Tests 28 and 32. Its reserved words are uninterpreted, its
total abstract map includes failure, and it supplies no live output law,
acceptance, selection, initializer admission, path, or sampler. It therefore
also leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-seventh adds the conservative finite-resolution rejection decision
as a precursor for Tests 28 and 32. It selects the first finite-rule acceptance
or records bounded exhaustion, but its probability theorem uses separate
abstract iid words and its finite law is not the ideal normalized tilted law.
It supplies no live word law, CP36 failure analysis, initializer admission,
selected-configuration lineage/tag-3 coordination, path, or sampler. It
therefore also leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-eighth adds the direct-word-free fixed-batch law as a further
precursor for Tests 28 and 32. It aggregates duplicate configurations and
defines the selected law only when selection mass is positive, but it supplies
no live law, generic initializer admission, selected-conditioned ideal/dyadic
bound, initialization-index-safe lineage/tag-3 coordination, path, or sampler.
It therefore also leaves Test 28 open, Test 29 open, and Test 30 pending.
The thirty-ninth adds exact selected-result intensity, positional-lineage, and
initialization-indexed local tag-3-prefix coordination as a further precursor
for Tests 28 and 32. Selected-empty remains a present state and exhaustion
remains no-state, but the words are uninterpreted, no live initializer law or
generic admission exists, and no tag-4/tag-5 Brownian stream or path is
constructed. It therefore also leaves Test 28 open, Test 29 open, and Test 30
pending; its final software evidence is bound and its disposition is **PASS
WITH EXPLICIT SCOPE LIMITS**.
The fortieth adds the fixed-\(B\) augmented and selected finite-resolution
targets, the selected-conditioned comparison with explicit \(Z_B\) dependence,
and the narrow structural state/no-state boundary as a further precursor for
Tests 28 and 32. It does not provide a live source law, CP36 success/failure
law, exact ideal rejection, SIR convergence, global normalized plug-in target,
or all-strategy admission. Test 28 therefore remains open; Test 29 remains
open; Test 30 remains pending. Its software disposition is **PASS WITH EXPLICIT
SCOPE LIMITS**.
The forty-first adds only the conditional abstract product-uniform
failure-aware source ledger. It separates preparation failure, quota failure,
exhaustion, and configuration atoms and proves exact symbolic normalization
and its stated conditional bounds, but its factorization premise is explicit
and unproved. It materializes no numeric fibers or masses and establishes no
live source or initializer law. Test 28 therefore remains open; Test 29 remains
open; Test 30 remains pending. Its software disposition is **PASS WITH
EXPLICIT SCOPE LIMITS**.
The forty-second adds only the bounded partial \(V\)-only predecision
reference evaluator on the nonrefusing CP28/CP30 domain and separate fully
preflighted \(H^{42}\). Its finite supplied witness retains and digest-binds
the full successful CP37 result for custody, including decision records/words
and outcome; only the parity comparison is limited to the CP36/CP37
predecision/threshold projection. It contains no CP42 applied-\(H^{42}\)
record and asserts no \(W\)/outcome or failure-fiber parity. It does not prove
universal live CP36/CP37 equivalence or discharge CP41's premise.
Test 28 therefore remains open; Test 29 remains open; Test 30 remains pending.
Its disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
The forty-third constructs only its own supplied-word reference composite
\(T^{43}_{r,j}(V,W)=H^{43}_{\mathrm{sem}}(G^{43}_{r,j}(V),W)\) under the
declared contract. Here \(H^{43}_{\mathrm{sem}}\) is the private
`_apply_trusted` kernel; the public replay facade
`apply_decision_words` first replays \(G^{43}\) for custody and passes a
failure through only when replay is deterministic and stable. The narrow
construction and abstract-product flags do not establish live CP36/CP37
factorization or discharge CP41's premise. The exact-text reviewed F37
argument leaves adaptive floor separation and natural reachability unresolved,
and the runtime fingerprint does not certify loaded-code integrity. Test 28
therefore remains open; Test 29 remains open; Test 30 remains pending. Its
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
The forty-fourth adds a one-adapter-allocation route from a
complete CP27 capsule through exact CP43 split/join and one combined
evaluation. Its pointwise projection claim applies only to calls that return a
CP44 result after final custody checks. Pre-combined and post-combined refusals
produce no result and remain outside \(F_{36}/F_{37}\); the abstract symbolic
mixture also requires fixed-runtime deterministic replay-stable total
\(G^{43}\) and product-uniform \(Z\). Its frozen 26/26 focused result, static
gates, exact-string checks, and independent `P0=P1=P2=0` audit support a
disposition of **PASS WITH EXPLICIT SCOPE LIMITS**. CP43 and CP42 execution
records are inherited by exact hash and were not freshly rerun for CP44. This
does not promote a live source, legacy-route equivalence, numeric-mass,
scientific, model-quality, generality, or manuscript claim.
The forty-fifth records only the fixed-address point-mass identity and the
bounded-free-coordinate conditional-success source-support obstruction. The
source theorem does not descend to an output-TV lower bound. Its frozen 20/20
focused pass, unchanged post-run hashes and static gates, and independent
`P0=P1=P2=0` audit support a disposition of **PASS WITH EXPLICIT SCOPE
LIMITS**. It promotes no positive live source, initializer/path/sampler,
scientific, model-quality, generality, or manuscript claim.
The forty-sixth separates deterministic fixed-request replay from a declared
finite exact-rational external law on the two uint64 request coordinates. Its
point-mass identity, positive-event support bound, analytic \(D^2\)-surface
obstruction for \(L>2\), and weighted-fiber criterion are source-descriptor
statements only. Ordinary models use cached ancestry; live revalidation is
separate, event positivity and external-law realization are unproved, and no
output-TV lower bound follows. Its frozen 24/24 focused result, static gates,
exact enumerations, hashes, and independent `P0=P1=P2=0` audits support a
disposition of **PASS WITH EXPLICIT SCOPE LIMITS**. It promotes no live
randomness/independence/freshness, initializer/path/sampler, scientific,
model-quality, generality, or manuscript claim.
The forty-seventh adds only the exact external full-capsule provider interface,
identity ingestion, bounded owner-local draw retirement, and CP43 execution
custody. Interface capacity \(D^L\) is not a product-uniform or IID provider
law; returned-result conditioning additionally depends on provider/downstream
success. Its frozen 31/31 focused result, post-run 22/22 fast gate, static
gates, hashes, runtime-fingerprint regressions, and independent
`P0=P1=P2=0` audits support a disposition of **PASS WITH EXPLICIT SCOPE
LIMITS**. It promotes no live source law, randomness, global uniqueness,
concurrent semantic-safety, adaptive retry, output-TV, initializer/path/sampler,
scientific, model-quality, generality, or manuscript claim.
The forty-eighth adds only the `system-os-urandom-operational` and
`external-exact-byte-block-unverified` byte-source bindings, one reached direct
backend call for exact built-in bytes of length \(8L\), the fixed manual
big-endian byte/word bijection, CP47 delegation, and successful-result custody.
The bijection preserves source-space TV, but a returned law and returned IID
sequence still require the stated positive complete-success and joint source-
law premises. Its frozen 37/37 focused result, post-run 28/28 fast gate, static
gates, hashes, and independent `P0=P1=P2=0` audits support a disposition of
**PASS WITH EXPLICIT SCOPE LIMITS**. The retained P3 asynchronous-interruption
note remains a nonclaim. CP48 promotes no backend or operating-system law,
totality, randomness, general concurrency/reentry/asynchronous safety,
unconditional result law, output-TV, initializer/path/sampler, scientific,
model-quality, generality, or manuscript claim.
The forty-ninth adds only a sealed unverified external premise, a pointwise
enriched CP43/CP42 object-semantic pushforward and data-processing statement,
complete-return and sequence caveats, structural nonexecution/nonreplay, and a
real selected custody/fiber witness whose probability consequence remains
assumption-only. Its frozen 28/28 result, independent 21/21 fast gate, static
gates, stable hashes, and independent `P0=P1=P2=0` audits support a
disposition of **PASS WITH EXPLICIT SCOPE LIMITS**. CP49 promotes no
operational source law or totality, unconditional returned law, sequence IID
or adaptive law, refusal totalization, global uniqueness, premise discharge
or universal legacy equivalence, initializer/path/sampler, Test-28 closure,
scientific, model-quality, generality, or manuscript claim.
Tests 25--26
and 30 remain unimplemented. None of these checkpoints admits a real
observation task, authorizes the learned conditional sampler, or establishes
representative-cardinality scaling.

## 11. Freeze decision and genuine blockers

This document does not yet close `METHOD-FREEZE/BASE-LAW`. The transformed
capped-Poisson reference, reversible forward reference process, NumPy
reverse-objective theorem/oracle, exact endpoint association-observation row,
conjugate analytic preconditioner, bounded neural/checkpoint layer, and
process-owned normalized reference-candidate composer, followed by the scoped
mixed CTMC--OU known-law oracle and its exact compact time-reversal path
sampler, and followed by the deterministic no-RNG extension of the reference
composer, the model-level analytic guide range/regularity extension, and the
successful-only represented guide value/edit gate, followed by the distinct
  general conditional-residual layer and the successful log-space
  base/guide/residual edge composer, and followed by the totalized operational-
  surrogate jump guide and the separately totalized operational-surrogate
  conditional jump residual, and finally the target-explicit totalized
  operational jump-potential composer and its separate exact-edge rate-space
  envelope, successful-return local operational thinning layer, and bounded
  local coordination successor, followed by single-route replay evidence and
  its ordered bounded-loop integration, and then the direct Philox namespace
  and post-hoc persistent-lineage prerequisite, followed by the direct tag-6
  operational-epoch loop with integrated route and lineage custody, followed
  by the tag-3 bootstrap-prefix, tag-7 global-control-prefix, fixed initializer-
  protocol allocation, finite reference-strategy transformer, and its frozen-
  grid diagnostic/custody layer, followed by the deterministic time-zero
  guide-plus-residual operational point-factor composer and its exact bounded
  all-atomic support/coefficient enumerator and explicit-word finite-resolution
  operational tilted-law selector and its exact stage-0 one-word protocol
  binding, followed by the fixed all-atomic initial-configuration constructor
  and fixed-index finite-reference bootstrap-lineage/tag-3-prefix constructor,
  and then fixed-budget rejection-stage proposal-and-score preparation followed
  by conservative finite-resolution first-selection-or-exhaustion decisions
  and the exact fixed-\(B\) counterfactual batch-law/structural-state layer,
  followed by selected-result reverse-time-zero intensity, CP23 positional
  lineage, and initialization-indexed local tag-3-prefix coordination, followed
  by the fixed-\(B\) finite-resolution target, selected-conditioned comparison,
  and narrow structural state/no-state boundary, followed by the conditional
  abstract product-uniform failure-aware source ledger, followed by the bounded
  staged \(V\)-only predecision evaluator and separate fully preflighted
  \(H^{42}\), and followed by CP43's supplied-word composite with private
  \(H^{43}_{\mathrm{sem}}\) and a distinct public replay facade, followed by
  CP44's one-allocation factorized execution adapter from a complete CP27
  capsule through the CP43 combined map, and followed by CP45's operation-free
  fixed-address and bounded-free-coordinate source-support obstruction, and
  then by CP46's cached fixed-request and declared finite external-law source
  descriptors with conditional support/TV and weighted-fiber boundaries, and
  then by CP47's direct external full-capsule interface, identity ingestion,
  bounded owner-local draw retirement, and CP43 execution custody, and then by
  CP48's two exact operational byte-source bindings, direct exact-byte backend
  boundary, manual big-endian bijection, CP47 delegation, and exact successful-
  result custody, and then by CP49's sealed external assumption declaration,
  pointwise enriched CP43/CP42 object-semantic pushforward, complete-return and
  sequence caveats, selected-result fiber custody, and nonexecuting structural
  admission above the exact CP48 ancestry,
  are now
  implemented and incrementally mapped as forty-nine
  checkpoints. Checkpoints thirty-eight through forty-one have disposition
  **PASS WITH EXPLICIT SCOPE LIMITS**. Checkpoint forty-two also has disposition
  **PASS WITH EXPLICIT SCOPE LIMITS**. Checkpoint forty-three has disposition
  **PASS WITH EXPLICIT SCOPE LIMITS**; checkpoint forty-four also has
  disposition **PASS WITH EXPLICIT SCOPE LIMITS**, with its frozen focused,
  static, exact-string, and independent-audit evidence recorded above and its
  CP43/CP42 execution records inherited by exact hash rather than freshly
  rerun. Checkpoint forty-five also has disposition **PASS WITH EXPLICIT SCOPE
  LIMITS**, with its frozen 20/20 focused result, post-run static gates,
  unchanged hashes, and independent `P0=P1=P2=0` review recorded above.
  Checkpoint forty-six also has disposition **PASS WITH EXPLICIT SCOPE
  LIMITS**, with its frozen 24/24 focused result, exact enumerations, static
  gates, hashes, and independent `P0=P1=P2=0` audits recorded above.
  Checkpoint forty-seven also has disposition **PASS WITH EXPLICIT SCOPE
  LIMITS**, with its frozen 31/31 focused result, post-run fast/static gates,
  runtime-fingerprint regression, hashes, and independent `P0=P1=P2=0` audits
  recorded above.
  Checkpoint forty-eight also has disposition **PASS WITH EXPLICIT SCOPE
  LIMITS**, with its frozen 37/37 focused result, post-run 28/28 fast/static
  gates, hashes, and independent `P0=P1=P2=0` audits recorded above. Its
  retained P3 asynchronous-interruption note remains an explicit nonclaim.
  Checkpoint forty-nine also has disposition **PASS WITH EXPLICIT SCOPE
  LIMITS**, with its frozen 28/28 focused result, independent 21/21 fast gate,
  static gates, hashes, explicit first-success/repeat evidence boundary, and
  independent `P0=P1=P2=0` audits recorded above. Its theorem remains
  assumption-only and closes none of the operational or whole-method claims.
The third audit code-matches the reference-relative reverse formulas and
population objectives; the fourth
code-matches the normalized retained/overflow law, exact association and orbit
calculations, typed atomic/Gaussian channels, positive mixture, and coordinate
gradients; the fifth code-matches reverse-to-terminal propagation, literal cap
restriction, the isolated cap flux, and exact-oracle guide derivatives and
edit ratios. The sixth code-matches the bounded invariant neural scalar,
snapshot-bound global analytic certificate, exact/Hutchinson coordinate
derivatives, training objectives, output-gauge controls, and certified rate
envelopes for supplied rates. The seventh code-matches reverse-to-direct time
orientation, process-valid labelled birth/death/replacement proposals, exact
normalized proposal factors, continuous destination log densities, and the
certified sampled base-energy integrand. It deliberately does not call that
integrand an integrated learned total exit and does not make an RNG-resolved
acceptance decision. The eighth code-matches the cap-one two-type generator and
reference, nonnegative uniformization certificate, exact nonstationary forward
law and derivatives, untouched-versus-edited OU transition decomposition,
analytic TV, bounded Gaussian terminal potential, backward information
equation, Doob drift and edit controls, reset law, and invariant-normalized
conditional marginals, with complete-log positive mass arithmetic and
fail-closed derivative scaling. It also includes a separate cap-two factorial
and occurrence-route companion, but no arbitrary-cap oracle or conditional
path RNG. The ninth code-matches finite-resolution-checked scoped marginal
sampling, exact forward-reference simulation, deterministic compact-path
reversal, strict float64 timestamp/boundary refusal, and nested provenance and
resource validation. It supplies no general learned initializer, thinning
loop, lineage-aware split step, or dense Brownian path. The tenth code-matches
the process-owned state-dependent reference intensity before RNG, exact
clean-hold and active structural-zero representations, route-resolution
preflight, time-reflection breakpoint refusal, and sealed-record revalidation.
It does not multiply by a guide/residual envelope, draw a waiting time, or
make an acceptance decision. The eleventh code-matches the fixed-observation
real-arithmetic guide lower/upper range, edit oscillation, and full flattened
log-guide gradient/Hessian bounds under normalized probability-simplex and
Markov-kernel semantics. It is sealed, deterministic, and fail-closed, but it
does not enclose the floating-point error of the pointwise guide evaluator and
therefore does not authorize operational thinning by itself. The twelfth
code-matches the directed represented interval, exact finite in-range
admission without tolerance or projection, bitwise raw-value preservation,
the coarse successful-evaluation discrepancy theorem, and the direct
represented jump-edit envelope. It refuses foreign, stale, nonfinite,
out-of-range, over-cap, or numerically failed evaluations. It supplies no
coordinate derivative, continuous drift, residual, controlled clock,
sampler-liveness theorem, or path sampler. The thirteenth code-matches the
direct-time cubic residual gate, active-row-only neural evaluation, canonical
clean-hold zero, same-condition state-pair subtraction, inherited global
value/oscillation and full flattened physical-coordinate
gradient/Hessian/Laplacian bounds, exact mathematical gate-derivative
witnesses, directed operational gate bounds, and residual-specific
schema/provenance/checkpoint custody. It assumes a procedurally frozen
finite-vector conditioner whose tensor origin is not runtime-authenticated;
it certifies no residual time/conditioner derivative, small forward error,
training result, combined potential, controlled clock, or sampler. The
fourteenth code-matches one active process-valid candidate's three separately
recomputed jump-log increments, their exact-rational one-round represented
sum, separate time-specific mathematical and operational aggregate bounds,
and cross-component process/time/state/context/outcome/checkpoint/provenance
custody. It rejects shared or physically overlapping base/residual model
storage and revalidates live components before and after evaluation. Its
successful record constructor is a structural check; authoritative
  `validate_evaluation` additionally recomputes the residual time gate and all
  three increments from live owners. It certifies no guide totality, small
  forward error, exponentiated rate envelope, total exit, waiting/acceptance
  law, continuous drift, or sampler. The fifteenth code-matches the
  factory-preflighted full-capped-domain operational point totalizer. It
  preserves a successful guide value bitwise, maps only typed numerical/range
  point failures to the exact-rational interval midpoint rounded once, and
  forms legal edits as exact rational endpoint coboundaries with global
  \(W_m\), fallback-specific, and \(2W_m\) discrepancy witnesses. Its runtime-
  specific streaming-digest records are replayable but not portable or BLAS-
  authenticated. Binary64 edit values are independently rounded and have no
  exact cycle-closure claim. It defines a jump-only operational surrogate,
  not the analytic conditional/posterior or Doob target, and supplies no
  coordinate derivatives, drift, rate envelope, clock, RNG, path, or sampler.
  The checkpoint-fourteen composer has not been migrated to it. The sixteenth
  code-matches the separate jump-only resolution of checkpoint thirteen's
  exact typed active tiny-cubic-gate failure. It preserves successful residual
  points bitwise; otherwise it multiplies the exact rational gate by the
  represented bounded-core value from a private checkpoint-materialized model
  and rounds once. Its detached canonical batch snapshots, before/snapshot/
  after streaming digests, private/public model custody, consumed-subnormal
  DAZ/FTZ probes, exact endpoint coboundaries, structural point/edge bounds,
  and narrow exception policy are fail-closed under the declared trusted
  runtime. It is an operational surrogate on the rescaling branch, not an
  exact real neural residual or conditional/posterior identity, and supplies
  no derivatives, drift, rate envelope, clock, RNG, path, or sampler. The
  checkpoint-fourteen composer has not been migrated to either totalizer.
  The seventeenth code-matches a separate explicit operational point target
  that combines the checkpoint-private base, fixed-observation totalized
  guide, and totalized residual for one active process-valid candidate. It
  recomputes all six endpoint values, composes exact represented endpoint
  fractions, ignores the component-rounded edges for aggregation, and rounds
  the final sum once. Its transitive certificate binds candidate/process,
  contexts, totalizer and checkpoint provenance, runtime, and external/private
  base and residual custody with pairwise disjoint model storage. This is an
  operational-surrogate log increment only, not an analytic, conditional,
  posterior, or Doob target; it supplies no exponentiation, rate envelope,
  total exit, clock, RNG, derivative/drift, initializer, path, or sampler. The
  eighteenth code-matches the separate rate-space successor for precisely that
  operational target. It exponentiates the exact rational edge by adaptive
  directed Decimal direct-product arithmetic, correctly rounds a successful
  finite normal candidate integrand, and constructs no-RNG instantaneous and
  global controlled-total-exit upper bounds. Structural zero is exact. It does
  not compute the active total exit, preserve rounded detailed balance or an
  exact stationary target, admit a route draw, make waiting/acceptance RNG
  decisions, or supply derivatives, drift, initialization, paths, or a
  sampler. The nineteenth code-matches the separate successful-return local
  successor. It resolves an ideal Philox-prefix inverse-exponential wait under
  inclusive real endpoint eligibility, refuses equality or represented
  collapse at a local boundary, delegates one inherited finite-resolution
  process-owned route, and samples the exact reduced rational represented
  candidate/envelope Bernoulli. Its authoritative `proposal_time` and
  before/after stream states bind one sequential Philox session, not a
  counter-keyed lineage. It supplies no repeated proposal loop, accepted-state
  recomputation, continuous-destination operational fixture, drift/Strang
  integration, initialization, path, liveness theorem, or full sampler.
  The twentieth code-matches bounded repeated coordination of those local
  operations. It advances by the authoritative represented proposal timestamp,
  preserves exact parent identity after rejection, immediately refreshes the
  accepted-state intensity and envelope at the fixed generative time, and
  returns only with a terminal interval-exhaustion waiting record. Its 0--64
  proposal count is a refusal cap: a still-active state at the cap raises
  before another wait, while a deterministic structural-zero/zero-duration
  hold is checked first. The sequential Philox state, contexts, parents,
  children, transitions, terminal record, and owner bindings are replayed. It
  supplies no exact real-time Poisson/CTMC or unconditional frozen-jump law,
  exact route law, continuous-destination operational evidence, counter-keyed
  lineage, drift/Strang integration, initialization, path, liveness theorem,
  or full sampler.
  The twenty-first code-matches a separate successor for post-hoc route
  custody. It retains reconstructable canonical Philox states, replays the
  frozen route composer locally, and validates concrete continuous birth and
  unequal-dimensional replacement records. It supplies no exact ideal route
  law, bounded standard-normal word trace, distribution recovery,
  counter-keyed lineage, drift, initialization, path, liveness theorem, or
  full sampler.
  The twenty-second code-matches the additive bounded-loop route-evidence
  overlay. It treats checkpoint twenty as a black box, reconstructs the full
  entry-to-exit sequential Philox transcript, and binds one checkpoint-
  twenty-one witness to every completed proposal. It inherits rather than
  redefines rejection, accepted-state refresh, terminal, and cap semantics.
  It supplies no original-call route-object identity, bounded normal-word
  trace, ideal route or frozen-jump law, unconditional completion, target
  preservation, counter-keyed lineage, drift, initialization, path, liveness
  theorem, or full sampler.
  The twenty-third code-matches the additive direct-address and lineage-sidecar
  contract. It binds to the exact checkpoint-twenty-two owner, constructs
  initially unused Philox states directly from the fixed run/domain key and
  zero/step/occurrence/proposal counter, and validates same-runtime
  reconstruction. Separately, it revalidates a returned parent transcript and
  applies positional duplicate-safe bootstrap, exact indexed destruction,
  fresh monotone creation, stable model-key-only ordering, exact rejection and
  terminal state reuse, and a bounded live-plus-retired custody ledger. It does
  not make checkpoint twenty-two keyed, consume any namespace receipt, enforce
  global run-ID uniqueness or deliberate-fork prevention, consume or couple
  Brownian streams, implement drift or initialization, construct a path or
  Strang step, prove an exact jump law or liveness, or admit the full sampler.
  The twenty-fourth code-matches the distinct counter-keyed operational-epoch
  loop. It owns tag 6 without modifying checkpoint twenty-three, reconstructs
  one direct local stream per active epoch, preserves within-epoch checkpoint-
  nineteen continuity, binds exact iteration/route/lineage records for every
  proposal, and separates active tag-6 stochastic exhaustion from zero-word
  tag-2 deterministic holds. It has no caller-RNG parameter or cross-epoch
  state carry. Its final hardening requires exact tag integers, exact canonical
  contexts and ordered proposal digests, bounded pre-hash nested resources,
  deep iteration/evidence/wait validation, exact parent certificate objects,
  and event-identity projection custody. It does not consume legacy tag-1
  proposal receipts or random tag-2 terminal words, prove one-shot use or
  independence, upgrade the finite-resolution route or rounded clock, consume
  occurrence/initializer/Brownian streams, implement drift or initialization,
  construct a path or Strang step, prove an exact jump law or liveness, or
  admit the full sampler.
  The twenty-fifth code-matches the distinct bounded bootstrap-only
  initializer-stream prefix-custody layer. It binds the exact checkpoint-
  twenty-four and checkpoint-twenty-three owners, admits only an already
  existing no-retirement positional bootstrap with at most 64 live
  occurrences, fixes the address to key \((\mathtt{run\_id},3)\), counter
  \((0,0,\mathtt{serial},0)\), and step zero, and consumes one positive
  `raw64` prefix per serial with 4,096-word per-occurrence and 65,536-word
  aggregate caps. It preserves exact input-state/model identity, accepts no
  caller RNG, and replays exact pre/post snapshots without upper carry. These
  raw words are deliberately uninterpreted: the checkpoint certifies prefix
  custody, not an initializer/output law. Because cardinality and occurrence
  serials do not exist before bootstrap, a general initializer requires a
  separate global initializer-control domain. It supplies no general
  initializer, occurrence semantics beyond those narrow prefixes, Brownian
  consumption or coupling, drift, path, liveness theorem, or full sampler.
  The twenty-sixth code-matches the separate law-neutral pre-cardinality
  control namespace. It binds exact checkpoint-twenty-five/twenty-four/twenty-
  three ancestry, reserves direct tag 7, and consumes bounded raw prefixes at
  key \((\mathtt{run\_id},7)\), counter
  \((0,\mathtt{initialization\_index},\mathtt{stage\_index},
  \mathtt{attempt\_index})\) for one canonical lexicographic plan. It enforces
  complete resource preflight, empty-plan no-op, exact pre/post replay, no
  upper carry, no caller RNG, declared nested identity relations, and
  validation-window mutation custody. It assigns no
  stage/attempt or branch/retry semantics, defines no output transform or
  initializer law, and supplies no accepted-configuration lineage mapping or
  tag-3 payload coordination. Brownian coupling, drift, path, liveness, and
  the full sampler remain open.
  The twenty-seventh code-matches the fixed initializer-protocol allocation
  successor. It binds the exact checkpoint-twenty-six owner, freezes four
  strategies and stages/roles 0--4, maps multiblock work-item coordinates
  injectively, materializes every fixed-budget parent prefix, and retains
  exact chronology, parent-plan/raw-word identity, same-runtime replay, owner
  baselines, and no-caller-RNG custody. It takes no branch and defines no
  enumeration/rejection/SIR/reference transform or output law, configuration,
  lineage mapping, or tag-3 coordination. Brownian, drift, path, liveness, and
  full-sampler claims remain false.
  The twenty-eighth code-matches the fixed reference strategy's ancestry-
  derived finite manifest and transformer. It records exact binary64-induced
  count/type ratios, positive dyadic quotas and their exact TV, consumes the
  canonical (1+N+ND) layout, transforms all raw slots and padding before
  cardinality decoding, and produces a stable duplicate-safe canonical
  configuration with complete parent replay. Its law is only the finite
  pushforward under hypothetical product-uniform words. It certifies no actual
  Philox randomness, exact Gaussian/capped-Poisson law, weak/Wasserstein bound,
  other initializer strategy, conditional/tilted initializer, initializer
  admission, lineage/tag-3 coordination, Brownian coupling, drift, path,
  liveness, or sampler.
  The twenty-ninth code-matches the preregistered one-shot diagnostic and its
  artifact/custody boundary. It binds exact checkpoint-twenty-eight owners,
  two 16,384-row deterministic grids, five exact statistics and frozen
  counterfactual envelopes, four end-to-end anchors, complete raw corpora, an
  independent verifier receipt, and STARTED-v2/terminal-v2 one-shot records.
  Its exact terminal is `PASS`, but its permitted inference is only that the
  prespecified discrepancies on the frozen grid fell within those envelopes.
  It certifies no Philox or continuous-reference law, general initializer,
  conditional/tilted initializer, path, sampler, model-quality result, or
  generality result.
  The thirtieth code-matches the selected \(\rho_0^\phi=\Pi_N\) initial point
  factor at reverse time zero/direct time \(S\). It evaluates only the
  totalized guide and residual, excludes \(V_\phi(S,x)\) and a separate
  observation-only nuisance, adds the represented binary64 component values
  exactly as rationals, rounds the aggregate once, and records outward point
  and rounding-error witnesses with process-local replay custody. It does not
  exponentiate or normalize that value, enumerate a support, select a state,
  consume RNG, return an initialized configuration, establish an analytic
  conditional/posterior target, or construct a path or sampler.
  The thirty-first code-matches exact complete support enumeration for the
  bounded all-atomic represented-parameter reference. It exact-renormalizes
  the stored type weights, emits cardinality-then-lexicographic count vectors,
  verifies the local multiplicity recurrence, all \(a^n/n!\) subtotals, and
  the \(Z_N(a)\) coefficient sum, and attaches one replay-validated
  checkpoint-thirty point to every state under explicit state, occurrence, and
  rational-bit caps. It stores no normalized mass, refuses every
  positive-dimensional type, and performs no point-factor exponentiation,
  tilted normalization, selection, RNG, initializer-protocol binding,
  initialized output, continuous-codebook construction, path, or sampler.
  The thirty-second code-matches the all-atomic ideal operational weights
  \(b_i e^{q_i}\), directed normalized-mass enclosures, exact midpoint-proxy
  normalization, positive \(2^{64}\) Hamilton quotas, rigorous
  ideal-to-dyadic TV control, and half-open lookup from one explicit uint64
  word. It neither sources nor certifies that word, binds checkpoint
  twenty-seven stage 0, samples the ideal transcendental law exactly, admits an
  initializer, supports mixed/continuous states, or constructs a path or
  sampler.
  The thirty-third code-matches the exact one-word all-atomic protocol bridge.
  It validates the checkpoint-thirty-two preparation before allocation,
  requires shared reference-composer, guide, and residual ancestry, invokes
  the exact checkpoint-twenty-seven owner with enumeration, budget one, empty
  work-item blocks, one selection word, and plan \(((0,0,1),)\), and retains
  key \((r,7)\), counter \((0,i,0,0)\), and unchanged raw-word custody through
  the selector result. For fixed preparation \(p\), its finite-law statement
  replaces the live word source by an abstract uniform \(U\), explicitly not
  identified with the deterministic fixed-address live word source, though
  their uint64 values may coincide. Separately, the fixed preparation inherits
  only \(\operatorname{TV}(P_{\mathrm{operational},p},Q_p)\le2^{-48}\). It does
  not certify actual Philox uniformity, independence, randomness, or global
  one-shot use; sample \(P_{\mathrm{operational},p}\) exactly; admit a general,
  mixed, or continuous
  initializer; implement another strategy; or construct a path or sampler.
  The thirty-fourth code-matches a factory-owned fixed all-atomic initial-
  configuration constructor. It freezes canonical context, complete support,
  dyadic preparation, and exact parent ancestry, then consumes one inherited
  word per successful two-index live call. Same-address live replay is
  deterministic; only abstract \(U\) has pushforward \(Q_p\). It certifies a
  configuration valid as an initial state, not a live initializer
  distribution or initializer admission, and promotes no actual-RNG,
  generality, mixed/continuous, path, or sampler claim.
  The thirty-fifth code-matches the fixed-index CP28-to-intensity-to-CP23-to-
  CP25 construction path, exact bootstrap and tag-3 mappings, counterfactual
  complete-capsule theorem, structural-TV upper bound, and conditional fiber-
  TV statement. It does not certify a live initializer law, tag-3 cross-index
  disjointness, general admission, path, or sampler.
  The thirty-sixth code-matches the fixed-budget CP27 rejection-stage-1 plan,
  exact CP28 proposal layout and all-slots-before-count transform, one reserved
  uninterpreted word per attempt, CP30 point score, reduced exact
  \(q-U\le0\) witness, full logical address coordinates, and conditional
  failure-augmented abstract pushforward. It does not certify a live word law,
  failure probability, success-conditional law, decision, acceptance,
  selection, initializer admission, lineage/tag-3 coordination, path, or
  sampler.
  The thirty-seventh code-matches exact conservative
  \(\lfloor2^{64}e^{q-U}\rfloor\) quota certification, the analytic terminal
  branches and adaptive Decimal enclosure, threshold-before-comparison
  chronology, exact inherited-word half-open decisions, first-selected or
  bounded-exhaustion results, and the fixed-data abstract-iid product law.
  Separately, the independent-coordinate ideal/dyadic Bernoulli comparison
  under common-uniform coupling has strict \(A/2^{64}\) finite-outcome error.
  It does not certify a live
  source law, CP36 failure probability or success-conditional law, exact ideal
  rejection, normalized tilted initializer or admission, lineage/tag-3
  coordination, path, or sampler.
  The thirty-eighth code-matches the direct word-free \(B\) projection, exact
  first-success/exhaustion partition, stable duplicate-configuration
  aggregation, \(Z_B>0\) selected-law boundary, all-zero total exhaustion,
  streamed projection digest, selected structural initial-state validity, and
  strict augmented \(<A/2^{64}\) common-uniform comparison. It does not certify
  a live law, CP36 failure or successful-batch distribution, success-
  conditioned reuse of the TV bound, generic initializer admission,
  initialization-index-safe lineage/tag-3 coordination, path, or sampler.
  Its no-cache focused and CP37 regression suites passed 45/45 and 44/44,
  respectively; the disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
  The thirty-ninth code-matches one exact checkpoint-thirty-eight
  `resolve(run_id, initialization_index)` call, preserves the selected
  configuration and its exact checkpoint-thirty-seven attempt rather than an
  aggregate representative, evaluates the reverse-time-zero reference
  intensity, and maps canonical position \(j\) to checkpoint-twenty-three
  bootstrap serial \(j+1\) with origin initialization index \(i\). Its tag-3
  coordination address is exactly key \((r,3)\), counter
  \((0,i,j+1,a+1)\), with prefix length \(\max(1,d_j)\), and the result stores
  the replayable positional lineage and bounded word plan under the
  64-record, 4,096-word-per-occurrence, and 65,536-word-aggregate caps. It
  uses CP39-local DTOs without forging a checkpoint-twenty-three address DTO or
  invoking checkpoint-twenty-five consumption. Exhaustion creates
  no selected-branch child; a selected empty configuration retains its
  intensity and present empty lineage with zero streams. Validation performs
  no checkpoint-thirty-eight resolution, checkpoint-twenty-three bootstrap,
  or checkpoint-thirty-nine child construction, while composer validation
  recomputes preflight and stored streams replay. It does not interpret tag-3
  payloads, generate coordinates, establish a live word law or independence,
  admit a generic initializer, reuse selected-conditioned TV, construct a
  normalized global tilt, Brownian motion, drift, path, liveness, or sampler,
  establish global, one-shot, cross-bootstrap, merge, or fork address safety,
  or provide a cryptographic or cross-runtime-portability guarantee. Its
  source, focused tests, and direct-parent regression are frozen, and its final
  disposition is **PASS WITH EXPLICIT SCOPE LIMITS**; no scientific result
  claim is promoted here.
  The fortieth code-matches one exact checkpoint-thirty-nine
  `coordinate(run_id, initialization_index)` call, the exact checkpoint-thirty-
  eight duplicate-aggregated augmented target with exhaustion atom, the
  positive-\(Z_B\) selected target, and the conditioning-stability comparison.
  It records raw strict upper \(2A/(2^{64}Z_B)\), separately labels the clipped
  display non-strict, and, at \(Z_B=0\), leaves optional probability and
  numeric-bound values absent while the corresponding flags remain present and
  false and fixed comparison/proof metadata remains present. On selection it
  preserves the exact CP39 configuration, intensity, lineage, and occurrence
  payloads and binds the target row by parent ordinal without
  substituting its representative. Selected-empty is admitted; exhaustion
  retains the target but no state. Validation performs no parent coordinate or
  child construction. It does not certify a live/unconditional initializer
  law, CP36 failure law, exact ideal rejection, normalized global tilt,
  all-strategy general admission, semantic tag-3 payload, Brownian motion,
  drift, path, liveness, or sampler. Its source and test hashes are frozen and
  all 45 focused tests passed; inherited exact-hash CP39 direct-parent evidence
  remains applicable. Its disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
  No scientific result claim is promoted here.
  The forty-first code-matches CP41's explicit product-uniform \(V/W\)
  hypothesis, the four-way symbolic law over preparation failure, quota
  failure, exhaustion, and configurations, its exact normalization, the
  \(\rho=0\) branch, the strict augmented comparison, and the positive-
  \(S_Q\) factor-one conditioning inequality. It invokes no CP36--CP40
  operation and consumes no source coordinate or caller/global RNG. It does
  not prove the factorization premise, materialize any fiber or numeric mass,
  establish a live Philox/source/initializer law, or admit a path or sampler.
  Its frozen focused suite passed 28/28, and its disposition is **PASS WITH
  EXPLICIT SCOPE LIMITS**. No scientific result claim is promoted here.
  The forty-second code-matches a bounded staged reference evaluator bound to
  that exact CP41 hypothesis and ancestry. Partial executable
  \(G^{42}_{r,j}:D^M\rightharpoonup
  \{F_{37}\}\mathbin{\dot\cup}\mathcal R\) accepts no reserved decision-word
  argument. On calls whose direct CP28/CP30 stages do not refuse, it constructs
  a ready value only after all attempts have been transformed, scored, and
  quota-certified. It reserves \(F_{36}\) outside its image while mapping only
  the exact CP37 quota exception to \(F_{37}\). Separate \(H^{42}\) preflights
  the complete \(W\) tuple before its
  first half-open comparison and returns first selection or exhaustion. The
  sealed witness retains and digest-binds the full supplied successful CP37
  result for custody, including decision records/words and outcome. Its parity
  comparison covers only the predecision/threshold projection; it contains no
  CP42 applied-\(H^{42}\) record and asserts no \(W\)/outcome or
  failure-fiber parity. CP42 invokes no CP36--CP40
  operation and consumes no RNG. It establishes neither universal live
  CP36/CP37 failure equivalence nor CP41's factorization premise, a live source
  or initializer law, numeric fibers or masses, general admission, path, or
  sampler. Its final focused, supplemental, regression, and independent-audit
  evidence is recorded above; its disposition is
  **PASS WITH EXPLICIT SCOPE LIMITS**.
  No scientific result claim is promoted here.
  The forty-third code-matches the CP43-defined supplied-word composite
  \(T^{43}_{r,j}(V,W)=H^{43}_{\mathrm{sem}}(G^{43}_{r,j}(V),W)\) for one exact certified
  owner/runtime and coordinate partition. Public `evaluate_predecision` is the
  \(V\)-only \(G^{43}\); private `_apply_trusted` is
  \(H^{43}_{\mathrm{sem}}\); and
  `evaluate_and_apply` performs one of each. Only the exact declared CP28/CP30
  exception classes become \(F_{36}\), while CP42's exact \(F_{37}\) is
  retained. \(H^{43}_{\mathrm{sem}}\) passes either failure without \(W\) access and
  preflights all ready \(W\) before comparison. The public replay facade
  `apply_decision_words` replays \(G^{43}\) for custody, so public failure
  pass-through requires deterministic, stable replay and a transient mismatch
  is refused before \(W\) access. The certificate records only the
  correspondingly narrow construction and abstract-product corollary flags.
  Its exact-text, digest-bound reviewed F37 arithmetic argument is not a
  machine proof and leaves the 3072-digit adaptive floor-separation route and
  natural F37 reachability unresolved. Its selected runtime fingerprint is
  procedural custody, with `loaded_code_integrity_certified=False`. CP43 does
  not establish universal live CP36/CP37 equivalence, discharge CP41's live-
  parent factorization premise, provide a live source or initializer law,
  materialize numeric masses, or admit a path or sampler. Its focused,
  regression, static-gate, and independent-audit evidence is frozen above; its
  disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. No
  scientific result claim is promoted here.
  The forty-fourth code-matches a one-adapter-allocation route from
  one complete CP27 rejection capsule through exact CP43 split/join and one
  combined evaluation. Its pointwise semantic-projection statement applies
  only when CP44 actually returns a result after final custody checks; both
  pre-combined and post-combined refusals instead produce no result and remain
  outside \(F_{36}/F_{37}\). Its abstract CP41-form mixture additionally assumes
  CP43's fixed-runtime, deterministic, replay-stable total \(G^{43}\) under the
  declared typed-error contract and a product-uniform full capsule. Its frozen
  26/26 focused result, static gates, exact-string checks, and independent
  `P0=P1=P2=0` audit support **PASS WITH EXPLICIT SCOPE LIMITS**; CP43/CP42
  execution evidence is inherited by exact hash and was not freshly rerun.
  No live source, legacy-route, numeric-mass, scientific, model-quality,
  generality, or manuscript claim is promoted.
  The forty-fifth code-matches the fixed-address point-mass identity and the
  at-most-k-free-coordinate conditional-success source-support obstruction.
  It is operation-free with respect to source allocation and CP43/CP44
  semantics, and a constant map witnesses why no output-TV lower bound
  follows. Its frozen 20/20 focused result, unchanged post-run hashes/static
  gates, and independent `P0=P1=P2=0` audit support **PASS WITH EXPLICIT SCOPE
  LIMITS**. No positive live source, initializer, path, sampler, scientific,
  model-quality, generality, or manuscript claim is promoted.
  The forty-sixth code-matches only the fixed-versus-declared-external source-
  model contract over the two uint64 request coordinates. Its point-mass
  identity, positive-event support bound, analytic \(D^2\)-surface obstruction
  for \(L>2\), and exact weighted-fiber criterion do not realize an external
  law, prove event positivity or fiber balance, or yield an output-TV lower
  bound. Ordinary models are cached descriptors and live revalidation is
  separate. Its frozen 24/24 focused result, exact enumerations, unchanged
  hashes/static gates, and independent `P0=P1=P2=0` audits support **PASS WITH
  EXPLICIT SCOPE LIMITS**. No live randomness, independence, freshness,
  initializer, path, sampler, scientific, model-quality, generality, or
  manuscript claim is promoted.
  The forty-seventh code-matches only the direct exact-L-word provider
  interface, identity ingestion, bounded owner-lifetime retirement ledger, and
  exact CP46--CP43 custody. Product uniformity, IID, totality, and value-
  independent success remain external premises; the local retirement contract
  is neither global nor persistent and gives no concurrent semantic-safety or
  adaptive-retry guarantee. Its frozen 31/31 focused result, post-run 22/22
  fast gate, hashes/static gates, runtime-fingerprint regression, and
  independent `P0=P1=P2=0` audits support **PASS WITH EXPLICIT SCOPE LIMITS**.
  No live law, randomness, output-TV, initializer, path, sampler, scientific,
  model-quality, generality, or manuscript claim is promoted.
  The forty-eighth code-matches only the two named operational byte-source
  profiles, one reached direct backend call with
  `(source_instance_sha256, draw_index, 8L)`, exact built-in-byte shape, the
  manual big-endian bijection, direct CP47 delegation, and exact successful-
  result byte/word/CP47 custody. The identity
  \(\operatorname{TV}(B_\#\mu,U_L)
  =\operatorname{TV}(\mu,U_{\mathrm{byte},8L})\), where
  \(U_{\mathrm{byte},8L}=\operatorname{Unif}(\{0,\ldots,255\}^{8L})\), is a
  source-space statement: product-uniform words require joint uniformity of
  the complete byte block, and returned-result and returned-sequence laws
  additionally require the stated positive complete-success and joint
  value-independent-success premises. CP47 remains the sole retirement and
  semantic authority. The deliberately zero-result same-draw race and the
  exact same-thread same-draw reentry fixture certify only their exercised
  retirement/refusal and ordinary-cleanup paths, not general concurrency,
  reentry, scheduler, asynchronous, or hostile-callback safety. The system
  profile certifies only one cached ordinary Python `os.urandom` API call site;
  the external profile certifies only exact callable binding and shape.
  Its frozen 37/37 focused result, post-run 28/28 fast gate, hashes/static
  gates, and independent `P0=P1=P2=0` audits support **PASS WITH EXPLICIT
  SCOPE LIMITS**; the retained P3 asynchronous `CALL`-to-`STORE` interruption
  remains a nonclaim. No backend totality, source law, IID behavior, entropy,
  cryptographic property, unconditional returned law, semantic-output TV,
  initializer, path, sampler, scientific, model-quality, generality, or
  manuscript claim is promoted.
  The forty-ninth code-matches only the sealed CP48-bound assumption
  declaration; the four-status pointwise tuple
  \(T_{\mathrm{obj}}\); its premise-qualified pushforward and TV
  data-processing statement; complete-return reweighting; joint/history
  sequence caveats; exact selected CP42 object custody and nonempty-fiber
  witness; and source-free, semantic-nonreplaying description, admission, and
  validation. Explicit live revalidation may replay ancestry only. Its frozen
  28/28 focused result, independent 21/21 fast gate, hashes/static gates, and
  independent `P0=P1=P2=0` audits support **PASS WITH EXPLICIT SCOPE LIMITS**.
  The actual all-zero selected witness does not attest the declared backend
  law, and the internal `passed=True` flag is contract consistency only. No
  operational realization, source law or totality, unconditional returned or
  sequence/adaptive law, refusal totalization, global uniqueness, premise
  discharge or universal legacy equivalence, initializer, path, sampler,
  Test-28 closure, scientific, model-quality, generality, or manuscript claim
  is promoted.
  Tests 11--12, 23, 27--29, and 31--32 therefore retain the whole-method
limitations stated above; Tests 25--26 and 30 remain pending. Unconditional
completion beyond the bounded fail-closed coordination layer, ideal
continuous-destination distribution recovery, an exact frozen-jump law, counter-
keyed execution beyond the scoped operational-epoch, checkpoint-twenty-five
bootstrap-prefix, checkpoint-thirty-nine selected-rejection-prefix, law-neutral
global-control, and fixed-protocol contracts, legacy tag-1 proposal-
  receipt and random-word tag-2 terminal consumption, semantic SIR decisions,
  adaptive branch/failure/source chronology, remaining initializer strategies,
  general
  conditional/tilted initializer admission and its empirical benchmark beyond
  the completed fixed-grid diagnostic,
  selected-state coordination beyond checkpoint thirty-nine's fixed-batch
  positional-bootstrap scope, semantic tag-3 payload interpretation and
  coordinate-generation semantics, global/cross-bootstrap/merge/fork/one-shot
  address guarantees, exact ideal rejection, a live/global initializer source
  law, a CP36 successful-batch/failure law, proof of CP41's factorization
  premise, universal equivalence between the CP43 supplied-word reference
  composite and live CP36/CP37 success and failure behavior, resolution of
  natural \(F_{37}\) reachability or impossibility, or
  all-strategy general admission,
occurrence semantics beyond the scoped prefixes, Brownian stream
consumption and coarse/fine coupling,
continuous drift, lineage-aware path and sampler contracts, and the
complete Section 6.3 diagnostic remain document-level
rather than end-to-end code evidence.

Closure still requires:

- analytic-target-preserving evaluation if that alternative is retained, an
  active controlled-total-exit evaluator if required by the final algorithm,
  unconditional completion/resource semantics beyond the bounded proposal
  cap, ideal continuous-destination distribution recovery, an exact frozen-
  jump law if claimed, keyed execution beyond the operational-epoch,
  checkpoint-twenty-five bootstrap-prefix, checkpoint-thirty-nine selected-
  rejection-prefix, and law-neutral global-control scopes, legacy tag-1
  proposal and random-word tag-2 terminal consumption, semantic SIR decisions,
  adaptive branch/failure/source semantics, remaining initializer strategies,
  an exact ideal-rejection alternative, a live/global initializer source law,
  a CP36 successful-batch/failure law, proof of CP41's factorization premise,
  universal equivalence between the CP43 supplied-word reference composite and
  live CP36/CP37 success and failure behavior, resolution of natural
  \(F_{37}\) reachability or impossibility, and a
  general conditional/tilted initializer admission rule and its empirical
  benchmark, selected-state coordination beyond checkpoint thirty-nine's
  fixed-batch positional-bootstrap scope, semantic tag-3 payload
  interpretation and coordinate-generation semantics, global/cross-bootstrap/
  merge/fork/one-shot address guarantees, occurrence semantics beyond the
  scoped prefixes,
  and Brownian stream consumption, plus the unfinished
  Section 6.3 diagnostic and
  conditioning contracts in Sections 7--8, the learned initializer and
  Brownian coarse/fine coupling, continuous drift, lineage-aware path sampler,
  and the native-to-transformed domain-manifest
  adapters deferred from Section 2;
- fresh independent code-and-equation audits after each of those remaining
  implementations;
- learned/sampled recovery against the scoped mixed CTMC--OU known law, any
  general-cap/general-type oracle extension on which a framework claim relies,
  the whole-method remainder of Tests 11--12, Test 23, Tests 25--32, and
  whole-method integration of the already scoped Tests 1--22 and 24;
- frozen numerical schedules, proposal counts, energy/rate certificates,
  initializer particles, and integration steps;
- a frozen refusal threshold for exact association and, before any scaling or
  real-domain claim, a separately validated production approximation; and
- real-domain task contracts for \((p_D,q_m,\kappa_m,M_m,\lambda_m)\), including
  a scientifically justified positivity route.

The following remain outside this candidate:

- exact atomless anchors;
- many-to-one aggregation, one-to-many splitting, or noninjective observation
  semantics;
- configuration-dependent detection/emission laws and nonconjugate channels,
  except as separately validated guide approximations;
- a structural-zero \(h\)-transform on the moving support \(\{h>0\}\);
- unbounded latent cardinality;
- a claim that the analytic preconditioner is novel; and
- any empirical or generality claim.

If two real domains cannot justify the frozen observation family, the common
association headline is retired even if the controlled known-law gates pass.
