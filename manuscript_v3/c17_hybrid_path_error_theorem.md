# C17 hybrid conditional-path error theorem target

**Document status:** `UNPROVED`  
**Claim status:** `NO_C17_PROMOTION_AUTHORIZED`  
**Execution status:** `NOT_EXECUTABLE`  
**Route:** `NARROW_THEORY_AND_TWO_DOMAIN_BENCHMARK`  
**Scope:** one fixed admitted observation/task/context tuple and the ideal
continuous-time capped hybrid laws defined below  
**Last specification audit:** 2026-08-28

This document formalizes C17 only. It fixes the statement that would have to
be proved, the assumptions that cannot be hidden, the two permissible routes
from density-ratio estimation to path error, and the code quantities that do
or do not exist. It is not a proof, a proof audit, an empirical result, a
sampler admission, an end-to-end reliability decomposition, or a novelty
promotion.

The controlling manuscript documents remain
[`executable_method_spec.md`](executable_method_spec.md),
[`novelty_audit_matrix.md`](novelty_audit_matrix.md), and
[`execution_preregistration.md`](execution_preregistration.md). If a later
method freeze changes the state space, generator, observation law, residual
class, initializer, or numerical path construction, this statement is stale
and must be superseded before any C17 proof or experiment.

## 1. Object and orientation

Fix one task \(m\), context \(z\), and admitted observation \(a\) on the
positive dominated observation branch. Fix a reverse horizon \(u\in[0,S]\).
Let

\[
\Gamma_{\le N}=\bigsqcup_{n=0}^{N}\Gamma_n
\]

be the capped typed finite-counting state, with each continuous stratum
represented in its declared physical coordinates and with permutation and
multiplicity semantics inherited from the method specification. Write

- \(\rho_0^\phi\) for the candidate-base initial law at reverse time zero
  (the selected method uses \(\Pi_N\));
- \(\bar a_u(y)=\bar\sigma_u(y)\bar\sigma_u(y)^{\mathsf T}\) and
  \(\bar b_u^\phi(y)\) for the within-stratum covariance and drift of the
  candidate base;
- \(\bar q_u^{\phi,J}(y,dy')\) for the base off-diagonal jump kernel of family
  \(J\in\{+, -, R\}\), denoting birth, death, and replacement; and
- \(g_m(a\mid y,z)\) for the positive terminal observation density.

The exact candidate-base information function is

\[
h_u(y)=
\mathbb E_\phi[g_m(a\mid Y_S,z)\mid Y_u=y,z],
\qquad
(\partial_u+\bar{\mathcal L}_u^\phi)h_u=0,
\qquad
h_S=g_m(a\mid\cdot,z).
\]

The analytic preconditioner \(\widetilde h\) is positive and terminal matched,
but is not assumed harmonic for the capped base. Define the exact residual and
the learned residual by

\[
h_u=\widetilde h_u e^{r_u^*},
\qquad
\widehat h_u=\widetilde h_u e^{r_{\theta,u}},
\qquad
e_u:=r_{\theta,u}-r_u^*
=\log\frac{\widehat h_u}{h_u}.
\]

The clean-hold boundary requires \(r_S^*=r_{\theta,S}=0\), hence
\(h_S=\widehat h_S=g_m(a\mid\cdot,z)\). A state-independent additive gauge in
\(e_u\) changes neither the controlled local characteristics nor the
normalized initial law.

For \(k\in\{h,\widehat h\}\), define the ideal controlled characteristics

\[
\bar b_u^k
=\bar b_u^\phi+\bar a_u\nabla\log k_u,
\qquad
\bar q_u^{k,J}(y,dy')
=\bar q_u^{\phi,J}(y,dy')\frac{k_u(y')}{k_u(y)},
\]

and the normalized initial tilt

\[
Z_k=\int_{\Gamma_{\le N}} k_0(y)\rho_0^\phi(dy),
\qquad
\rho_0^k(dy)=\frac{k_0(y)}{Z_k}\rho_0^\phi(dy).
\]

Let \(P^h\) and \(P^{\widehat h}\) be the corresponding ideal path laws on
\(D([0,S],\Gamma_{\le N})\). The frozen divergence orientation is

\[
\boxed{\mathrm{KL}(P^h\,\|\,P^{\widehat h})},
\]

target first and plug-in law second. Reversing the arguments changes the
occupation law, initializer term, and jump Bregman orientation; it is not a
cosmetic rewrite.

If \(\mu_u^\phi\) is the candidate-base marginal generated from
\(\rho_0^\phi\), harmonicity gives the exact target occupancy

\[
\mu_u^h(dy)=\frac{h_u(y)}{Z_h}\mu_u^\phi(dy).
\]

This orientation is deliberate: a known-law oracle can integrate the error
against the exact target occupancy without solving the arbitrary neural
plug-in Fokker--Planck equation. The reverse KL would instead require the
plug-in occupancy.

## 2. Assumptions required by the target statement

No item in this section may be replaced by “standard regularity conditions”
in a promoted theorem.

### A1. State and measurable structure

The capped quotient state is standard Borel. Every active continuous stratum
has a declared smooth coordinate chart and tangent gradient. Collision or
quotient boundaries must either have zero entropy/local-time contribution or
use exactly the same boundary/reflection mechanism under both laws with a
proved cancellation in their likelihood ratio. Any noncancelling boundary
term is outside Theorem C17.1 and requires a restated identity that displays
it explicitly. Atomic coordinates are discrete and are never differentiated.

### A2. Well-posed candidate base

The time-inhomogeneous martingale problem for
\(\bar{\mathcal L}^\phi\) is well posed and nonexplosive from
\(\rho_0^\phi\). Its jump kernel is the disjoint sum of the declared birth,
death, and replacement kernels, including the exact occurrence multiplicity,
destination-fiber, and cap indicators. Simultaneous jumps have probability
zero.

### A3. Positive finite information functions

For the fixed \((a,m,z)\), \(h_u(y)\), \(\widetilde h_u(y)\), and
\(\widehat h_u(y)\) are measurable, strictly positive, and finite on every
state that can be occupied. The normalizers satisfy
\(0<Z_h,Z_{\widehat h}<\infty\). Positivity is a substantive common-support
assumption; it is not supplied by clipping.

### A4. Terminal and clean-hold compatibility

The exact and plug-in functions have the same terminal density. On the frozen
reverse clean hold, both controlled generators are the zero generator, so
their transition is the static identity transition, and the two residuals are
zero. If either boundary condition changes, the theorem must be restated.

### A5. Within-stratum differentiability

On each active continuous stratum, \(\log h\),
\(\log\widehat h\), and \(e\) have predictable gradients sufficient for the
stochastic integrals below. The integrated quadratic form

\[
\int_0^S\nabla e_u(Y_u)^{\mathsf T}\bar a_u(Y_u)
\nabla e_u(Y_u)\,du
\]

is finite under \(P^h\).

### A6. Shared diffusion and degenerate directions

Both laws use exactly the same covariance
\(\bar a=\bar\sigma\bar\sigma^{\mathsf T}\). Their drift difference is
\(\bar a\nabla e\), hence lies in the Cameron--Martin range of
\(\bar\sigma\). If \(\bar a\) is degenerate, the proof must use this range
condition (or the appropriate pseudoinverse statement); uniform ellipticity
must not be silently assumed.

### A7. Common jump support

For every family \(J\) and every predictable source,

\[
\frac{d\bar q_u^{\widehat h,J}}
{d\bar q_u^{h,J}}(y,y')
=\exp\{e_u(y')-e_u(y)\}
\]

on the common support. Every structural-zero base edge is zero under both
laws. The log ratio and the Bregman integrals are finite on occupied edges. A
plug-in law that removes a target-positive edge on a source/time set with
positive \(P^h\) compensator mass gives infinite divergence and is outside the
finite conclusion. Algebraic positivity at an unreachable state is not by
itself enough.

### A8. Finite compensators

The three controlled total exit rates are predictable and integrable under
\(P^h\). In particular,

\[
\sum_J\mathbb E_{P^h}\int_0^S\int
\bar q_u^{h,J}(Y_{u-},dy')
\Phi\!\left(e_u(y')-e_u(Y_{u-})\right)du<\infty,
\]

where \(\Phi(t)=e^t-1-t\).

### A9. True change-of-measure martingale

The continuous stochastic exponential and the marked-jump likelihood ratio,
including the initial density ratio, define a true uniformly integrable
martingale rather than only a local martingale. A promoted proof must give
checkable Novikov/Kazamaki-type and jump-compensator conditions, or a bounded
localization argument with justified limit passage.

### A10. Path-law uniqueness

The controlled martingale problems for \(h\) and \(\widehat h\) are unique in
law. The characteristics above therefore identify \(P^h\) and
\(P^{\widehat h}\), not merely two candidate weak solutions.

### A11. Exact-law, not numerical-path, comparison

The statement compares ideal continuous-time laws. Split-step integration,
rounded envelopes, finite-resolution clocks, initializer rejection/SIR, and
operational-surrogate jump targets are different objects. Their errors belong
to a separate numerical or implementation theorem, not to the identity below.

### A12. Conditioning and base scope

The exact target is conditional only relative to the frozen candidate base.
Equality to the conditional reversal of the data-forward law additionally
requires the correct learned base and reverse initial law. C17 does not prove
that broader statement.

## 3. The exact C17 path identity to be proved

### Theorem target C17.1 (oriented hybrid path relative entropy)

Under A1--A12, the following identity is the exact target:

\[
\boxed{
\begin{aligned}
\mathrm{KL}(P^h\,\|\,P^{\widehat h})
={}&\mathcal K_0(e)+\mathcal K_C(e)
+\mathcal K_+(e)+\mathcal K_-(e)+\mathcal K_R(e),\\[2mm]
\mathcal K_0(e)
={}&\mathrm{KL}(\rho_0^h\,\|\,\rho_0^{\widehat h})\\
={}&\log\frac{Z_{\widehat h}}{Z_h}
-\mathbb E_{\rho_0^h}[e_0(Y_0)]\\
={}&\log\mathbb E_{\rho_0^h}[e^{e_0(Y_0)}]
-\mathbb E_{\rho_0^h}[e_0(Y_0)],\\
\mathcal K_C(e)
={}&\frac12\mathbb E_{P^h}\int_0^S
\left\|\bar a_u(Y_u)^{1/2}\nabla e_u(Y_u)\right\|^2du,\\
\mathcal K_J(e)
={}&\mathbb E_{P^h}\int_0^S\int
\bar q_u^{h,J}(Y_{u-},dy')
\Phi\!\left(e_u(y')-e_u(Y_{u-})\right)du,
\quad J\in\{+,-,R\},\\
\Phi(t)={}&e^t-1-t.
\end{aligned}}
\]

Every displayed component is nonnegative, although the two terms in the
second expression for \(\mathcal K_0\) need not be. Birth, death, and
replacement are separate terms: “jump error” is not an allowed certificate
unless its record contains the exact family partition and proves that their
sum equals the displayed quantity.

The kernels in that partition are kernels on the unlabeled counting state.
Occurrence-labelled proposal routes that reach the same unlabeled destination
must first be aggregated, with source multiplicity, transposed reference
flux, destination-fiber Radon--Nikodym/Jacobian factors, and cap indicators
already present in \(\bar q^{h,J}\). The \(h\)-ratio cannot repair a malformed
base kernel.

The jump orientation follows from

\[
\bar q^{\widehat h,J}=\bar q^{h,J}e^{\Delta e},
\qquad
\bar q^{h,J}\log\frac{\bar q^{h,J}}
{\bar q^{\widehat h,J}}
-\bar q^{h,J}+\bar q^{\widehat h,J}
=\bar q^{h,J}\Phi(\Delta e).
\]

The continuous orientation follows from
\(\bar b^{\widehat h}-\bar b^h=\bar a\nabla e\). These algebraic checks do
not constitute a proof of the path-space identity; A1--A10 still have to be
discharged.

If Theorem C17.1 is proved, Pinsker and data processing would give only

\[
\|P^h-P^{\widehat h}\|_{\mathrm{TV}}
\le\sqrt{\tfrac12\mathrm{KL}(P^h\|P^{\widehat h})},
\]

and the analogous upper bound for any measurable endpoint or statistic. It
would not give reverse KL, equality of endpoint laws, calibration, utility,
or a numerical-sampler guarantee.

## 4. Joint/product NCE and the mandatory bridge fork

Let \(J\) be the declared same-context joint law of
\((u,Y_u,A,m,z)\) and \(M\) the corresponding product law obtained from an
independent second terminal simulation at the same \((u,m,z)\). With equal
class priors, the Bayes logit is

\[
\ell^*=\log h_u(Y_u)-\log p_{A,m}^{\phi,\lambda}(A\mid z).
\]

The proposed logit is

\[
\ell_{\theta,\psi}
=\log\widetilde h_u(Y_u)+r_{\theta,u}(Y_u)+c_\psi(A,m,z),
\]

so that

\[
\ell_{\theta,\psi}-\ell^*
=e_u(Y_u)+\eta_\psi(A,m,z),
\qquad
\eta_\psi:=c_\psi+\log p_{A,m}^{\phi,\lambda}.
\]

The nuisance has no process-time or state input. The path law is invariant to
state-independent gauges, but a classifier risk is not. A valid analysis must
therefore fix a normalization or explicitly quotient the nuisance/gauge; it
may not identify \(e\) from the logit error by assertion.

Write the equal-prior population logistic risk as

\[
\mathcal R(\ell)=\tfrac12\mathbb E_J\log(1+e^{-\ell})
+\tfrac12\mathbb E_M\log(1+e^{\ell}).
\]

If both the Bayes and fitted logits lie in a frozen bounded interval, the
joint/product measures have declared common support, and the model projection
error is separately retained, logistic curvature can yield a value-level
bound of the form

\[
\|e^\circ\|^2_{L^2(\mu_{\mathrm{train}})}
\le
C_{\mathrm{log}}
\left(\Delta_{\mathrm{NCE}}+\varepsilon_{\mathrm{projection}}
+\varepsilon_{\mathrm{nuisance}}\right),
\]

where \(e^\circ\) is a declared state-centered representative and every
measure and constant is frozen. This is still a value bound. It does not
control \(\nabla e\), legal-edge increments, initializer KL, or a shift from
the training measure to the \(P^h\) occupation measure.

It is also an average over the declared observation/context law. C17 fixes a
particular admitted \((a,m,z)\). For a continuous observation, that slice can
have zero probability under the average training law, so an ordinary
Radon--Nikodym comparison of the averaged measures does not control it. Fork A
must therefore prove a regular conditional/per-observation risk statement or
a uniform disintegration/regularity theorem that transfers the average bound
to the exact fixed observation and context. An assertion that the observed
slice is merely "in support" is insufficient.

Exactly one of the following two forks must be completed.

### Fork A: prove coercivity and measure transport

This route must prove all of:

1. a conditional/per-observation or uniform-disintegration bound transferring
   the averaged NCE risk to the exact fixed \((a,m,z)\) theorem slice;
2. a finite transport constant from the resulting fixed-slice training
   measure to the target
   occupation measure, with no unreported zero-density region;
3. a frozen edge-amplitude bound sufficient to turn
   \(\Phi(\Delta e)\) into a controlled quadratic edge term;
4. an inverse regularity/coercivity inequality on the actual error class,
   not on an unrelated Sobolev closure; and
5. a separate initializer inequality.

One admissible target shape is

\[
\mathcal K_C(e)+\sum_J\mathcal K_J(e)
\le C_{\mathrm{coer}}
\|e^\circ\|^2_{L^2(\mu_{\mathrm{train}})}
+\varepsilon_{\mathrm{derivative/edge}}
+\varepsilon_{\mathrm{transport}},
\]

followed by the value-risk bound and an explicit bound on
\(\mathcal K_0\). The direction is intentionally difficult: ordinary
Poincare inequalities control values by derivatives, not derivatives by
values. A reverse inequality is false on a general smooth or neural function
class. It needs restrictive finite-dimensional, band-limited, spectral,
inverse-estimate, or independently certified derivative/edge structure with
finite reported constants.

### Fork B: certify the path quantities directly

This route may retain NCE as value-estimation evidence, but the C17 path bound
must come from separate simultaneous certificates

\[
\mathcal K_0\le U_0,
\quad
\mathcal K_C\le U_C,
\quad
\mathcal K_+\le U_+,
\quad
\mathcal K_-\le U_-,
\quad
\mathcal K_R\le U_R.
\]

Each certificate must use the \(P^h\) occupation law or a proved dominating
measure with exact Radon--Nikodym factors. Every legal edit family must be
covered; sampled proposals require fixed proposal laws, unnormalized weights,
and a nonvacuous simultaneous uncertainty rule. A global architecture ceiling
without an error-to-\(r^*\) certificate is not sufficient. Under a proved
simultaneous event, Theorem C17.1 would then give

\[
\mathrm{KL}(P^h\|P^{\widehat h})
\le U_0+U_C+U_++U_-+U_R.
\]

Fork B is not a disguised coercivity claim and must not report the NCE loss as
the source of its derivative or edge bounds.

## 5. Cap/reference placement and the no-double-counting rule

The cap and reference defects are scientifically relevant, but their location
is constrained by algebra. For any fixed positive preconditioner,

\[
\log\frac{\widehat h}{h}
=\log\frac{\widetilde h e^{r_\theta}}
{\widetilde h e^{r^*}}
=r_\theta-r^*=e.
\]

Therefore neither the harmonic defect

\[
\mathfrak d_u^\phi
=\frac{(\partial_u+\bar{\mathcal L}_u^\phi)
\widetilde h_u}{\widetilde h_u}
\]

nor its blocked-birth cap component is an additional summand in Theorem
C17.1. The defect can enter C17 only through one proved, nonoverlapping route:

1. **Residual-PDE stability:** use the exact residual equation and a proved
   stability/regularity estimate to bound the size or approximability of
   \(r^*\), then count the resulting projection term once inside \(e\).
2. **Projection decomposition:** prove that the chosen residual class has a
   defect-dependent approximation error, then place that term once in the
   NCE/coercivity or direct-certificate fork.
3. **Intermediate-law comparison:** define every intermediate law and prove a
   valid composition inequality in its actual orientation. KL has no triangle
   inequality; a sum of pairwise KL values is not valid without an additional
   theorem.

If the implemented guide differs from the guide used to define \(r^*\), the
actual error is

\[
e_{\mathrm{actual}}=\log\widehat h_{\mathrm{implemented}}-\log h.
\]

Splitting it into guide and residual pieces introduces continuous cross terms
and nonlinear jump Bregman terms. Those pieces cannot be added as independent
KL errors without a proved inequality. Base-model, terminal-reference,
association-kernel misspecification, numerical integration, and finite-RNG
errors belong to C18 or another theorem; C17 does not absorb them.

## 6. Estimable certificate contract

The word “estimable” below means tied to a declared finite computation or a
statistical procedure with a frozen error statement. It does not mean that
the current repository already supplies the estimate.

| Quantity | Exact/certified route | Required record | Current boundary |
|---|---|---|---|
| \(\mathcal K_0\) | Exact support enumeration, a direct KL/log-mgf enclosure, or the correctly oriented combination of an upper bound on \(Z_{\widehat h}\), a lower bound on \(Z_h\), and a lower bound on \(\mathbb E_{\rho_0^h}[e_0]\) | Base initial law, support, \(h_0\), \(\widehat h_0\), normalizers, target expectation, bound directions, orientation, numerical enclosure | Finite atomic tools exist; a general mixed exact \(h_0\) and real-domain certificate do not. |
| \(\mathcal K_C\) | Exact occupation integration in a known law, or target-occupation sampling plus a simultaneous upper confidence rule for \(\|\bar a^{1/2}\nabla e\|^2\) | Time law, target occupation law, gradient definition, covariance, quadrature/MC error | The learned residual has coordinate derivatives, but the unknown \(\nabla r^*\) and general \(P^h\) occupation law are unavailable. |
| \(\mathcal K_+\) | Enumerate all births in a finite oracle or use a frozen dominating birth proposal with exact unnormalized factors | Every cap/source/destination factor, proposal, sample count, family uncertainty bound | Analytic guide birth/cap proposals exist; target error increments involving \(r^*\) do not. |
| \(\mathcal K_-\) | Enumerate every occurrence-weighted death edge | Multiplicity, source occupation, target rate, \(\Delta e\), Bregman term | Operational edge composition exists only in narrower successful/totalized targets; no general C17 certificate exists. |
| \(\mathcal K_R\) | Enumerate or importance-sample every source/destination replacement fiber with exact RN factors | Source multiplicity, type balance, destination fiber, target rate, \(\Delta e\), uncertainty | Same limitation as death, with additional continuous destination integration. |
| NCE value risk | Held-out same-context joint/product population or a frozen estimator with concentration | Joint/product construction, time/context law, nuisance class, projection error, support and bounded-logit checks | A finite population oracle exists; the declared general trainer and nuisance branch are not implemented. |
| Coercivity/transport | Analytic constants or machine-checked finite matrices on the exact error class and measures | Constants, spectra/inverse estimates, density-ratio bounds, edge-amplitude bound, failure conditions | No such theorem or certificate exists. |
| Cap/reference diagnostic | Exact enumeration in finite fixtures or unnormalized proposals with a simultaneous error rule | Guide value/derivative error, isolated cap term, base mismatch, proposal and uncertainty records | Partial analytic routines exist; the complete Section 6.3 diagnostic and nonvacuous high-probability rule remain open. |

Self-normalized proposal weights are not accepted for the population
quantities in this table. A Monte Carlo point estimate without a prespecified
simultaneous upper bound cannot be inserted into a theorem. A finite known-law
success is a falsification gate, not evidence that the same certificate holds
on PhysioNet or Retail.

### Nonvacuity rule

A C17 numerical conclusion is nonvacuous only if its upper bound is finite,
strictly below the frozen null/reference tolerance, and computed without an
unknown exact residual, an arbitrary global envelope, or a post-result choice
of measure, grid, proposal, or confidence level. The exact threshold remains
an unresolved preregistration field.

## 7. Proof roadmap and proof obligations

The following is a roadmap, not a proof.

1. Construct the capped hybrid martingale problem on the quotient state and
   prove nonexplosion and uniqueness for the base and both controlled laws.
2. Prove the initial density ratio and the displayed formula for
   \(\mathcal K_0\).
3. Localize the continuous and jump likelihood ratios and prove their
   stochastic exponentials are true martingales.
4. Apply continuous Girsanov on each active stratum, including the degenerate
   covariance/range case and any chart-boundary terms.
5. Apply the marked-point-process compensator change separately to birth,
   death, and replacement, preserving multiplicity and continuous
   destination measures.
6. Take the \(P^h\) expectation of the log likelihood ratio, justify limit
   passage, and recover the five nonnegative terms in Theorem C17.1.
7. Verify gauge invariance, the clean-hold boundary, and structural-zero
   preservation.
8. Prove the logistic-risk curvature statement under the exact joint/product
   measures and isolate the observation-only nuisance and bounded-class
   projection error.
9. Complete either Fork A, including measure transport and an honest inverse
   inequality, or Fork B, including all five simultaneous certificates.
10. Prove the selected cap/reference placement without a KL triangle or
    duplicated defect term.
11. Instantiate every term on the frozen finite and mixed known-law gates,
    then conduct a fresh proof/code audit against the symbol map below.

No C17 claim may be promoted after only steps 1--7: that would be a classical
change-of-measure identity without the estimator-specific executable bridge
required by the novelty matrix.

## 8. Counterexamples and required falsification cases

1. **Value error does not control gradient error.** On a one-dimensional
   stratum, \(e_n(x)=n^{-1}\sin(nx)\) has value \(L^2\) error tending to zero
   while its gradient energy stays of constant order. Logistic excess can
   vanish while \(\mathcal K_C\) does not.
2. **Value error does not uniformly control edge error.** On graph families
   with increasing top eigenvalue, small vertex \(L^2\) error can retain large
   edge energy. Any finite-state reverse inequality must expose its spectral
   constant and cannot be transferred dimension-free.
3. **Nuisance is not a path control.** Adding an observation-only constant to
   a logit can change classifier risk while leaving every drift, jump ratio,
   and normalized initializer unchanged. Conversely, a state-dependent error
   cannot be assigned to the nuisance.
4. **Initial error is not a local-generator error.** Two tilts can agree in
   all post-initial local characteristics yet induce different normalized
   initial laws. Omitting \(\mathcal K_0\) then understates path divergence.
5. **Support loss makes KL infinite.** If a target-positive legal edge or
   initial state receives zero plug-in mass on a set with positive target
   initial or compensator mass, finite gradient or surviving-edge errors do
   not repair absolute continuity.
6. **Cap defect is not an invariant additive error.** Changing
   \(\widetilde h\) and compensating \(r^*\) can leave \(h\) and the actual
   target-versus-plug-in error unchanged while changing the displayed
   harmonic defect. Adding that defect to path KL would depend on an arbitrary
   factorization.
7. **KL has no triangle inequality.** Small or bounded divergences through a
   guide-only intermediate law do not justify their unproved sum as a bound
   on \(\mathrm{KL}(P^h\|P^{\widehat h})\).
8. **Orientation matters.** Substituting \(P^{\widehat h}\) occupation and
   \(\Phi(-\Delta e)\) computes the reverse orientation, not Theorem C17.1.
9. **Ideal equality does not certify a numerical sampler.** Even when
   \(e=0\) and the ideal path KL vanishes, time discretization, rounded
   envelopes, finite-resolution initialization, or RNG refusal can change the
   returned algorithmic law.
10. **Oracle scope does not transfer.** Exact finite-state or cap-one
    CTMC--OU behavior does not prove the general capped mixed-state identity,
    the real-domain transport constant, or neural approximation quality.
11. **Average NCE risk does not control a fixed continuous observation.** An
    error may concentrate in an arbitrarily small neighborhood of one
    admitted observation while its joint/product average risk tends to zero.
    C17's fixed-observation conclusion therefore needs conditional or uniform
    observation regularity, not only average-risk convergence.

The proof package must turn these into executable unit or theorem-oracle
tests where the required objects exist. A counterexample that the code cannot
represent remains a mathematical boundary case and must still be retained.

## 9. Code-to-symbol interface and current gaps

This table is descriptive of the live tree inspected for this specification.
It does not promote a partial component to the ideal law in Theorem C17.1.

| Mathematical object | Live interface | What it supplies | What it does not supply for C17 |
|---|---|---|---|
| Capped state and \(\rho_0^\phi=\Pi_N\) | `heterodiff.theory.configuration_reference.CappedPoissonConfigurationReference` | Typed capped reference representation and scoped sampling | Exact conditional \(h\), target initial tilt, or a path-KL certificate |
| Base hybrid characteristics | `heterodiff.processes.reversible_hybrid_reference.ReversibleHybridReference` | Forward reference rates and event-driven reference paths | The general learned conditional path law or C17 change-of-measure proof |
| Base reversal/objective oracles | `heterodiff.theory.reverse_energy_objective` | Finite jump-flux Bregman and Gaussian relative-score identities | A continuous marked-configuration path theorem |
| Terminal \(g_m\) and association law | `heterodiff.theory.association_observation.evaluate_association_observation` and `association_log_density_coordinate_gradients` | Normalized retained/overflow association values and coordinate derivatives in the admitted family | Real-domain task admission or exact \(h_u\) away from the terminal time |
| \(\widetilde h\), guide gradients, guide edit ratios, cap term | `heterodiff.theory.association_preconditioner.AnalyticAssociationPreconditioner.evaluate`, `.coordinate_gradients`, `.edit_log_ratio`, `.cap_boundary_defect`, and `.estimate_cap_boundary_from_proposal` | Declared conjugate auxiliary guide, restriction, derivative/edit interfaces, and isolated cap diagnostic | Exact capped information \(h\), \(r^*\), complete Section 6.3 uncertainty, or an additive path-error term |
| Learned \(r_\theta\) | `heterodiff.models.configuration_residual_torch.configuration_residual`, `configuration_residual_state_pair_difference`, and `configuration_residual_coordinate_gradients` | Bounded residual values, same-condition differences, and physical-coordinate derivatives for a certified checkpoint | The joint/product trainer, nuisance estimator, training success, \(r^*\), or error certificates relative to \(r^*\) |
| Finite joint/product risk | `heterodiff.theory.finite_bridge_population.equal_prior_logistic_risk_per_time` and `population_equal_prior_logistic_risk` | Exact finite population-risk oracle | General mixed trainer, projection/transport constants, or derivative/edge coercivity |
| Finite initializer and time-inhomogeneous jump path KL | `heterodiff.theory.finite_bridge_path_control.conditional_initial_law` and `tilted_path_kl` | Finite-state initializer and jump-only path-KL gate | Continuous-gradient term, general mixed quotient-state proof, or rigorous enclosure; its numerical ODE error is outside the returned path-KL value |
| Time-homogeneous finite CTMC KL | `heterodiff.theory.path_kl.ctmc_path_kl` | Classical finite-state jump-compensator oracle | Learned mixed path law, diffusion term, NCE bridge, or rigorous arithmetic certificate; the implementation uses binary64 matrix exponentials without interval enclosure |
| Finite association bridge | `heterodiff.theory.finite_atomic_association_bridge.FiniteAtomicAssociationBridgeOracle` | A1-scale exact association/conditioning oracle | Representative mixed or real-domain conclusion |
| Concurrent factorized CTMC--OU diagnostic | `heterodiff.evaluation.mixed_ctmc_ou_known_law_oracle.build_mixed_ctmc_ou_known_law_oracle` | A small two-type capped counting CTMC times an independent scalar OU, with positive factorized terminal likelihood, finite information/initial tilt, discrete jump tilts, continuous conditioned drift, and a Poisson-tail uniformization certificate | Association marginalization, occurrence-attached continuous marks, a learned residual, the C17 path-KL decomposition, cap-defect cancellation, a general mixed oracle, or closure of R2/C17; its own scope is `FINITE_FACTORIZED_MIXED_CTMC_OU_DIAGNOSTIC` and all claim effects are false |
| Historically named analytic successful edge composer | `heterodiff.models.configuration_potential_composer_torch` is named by the method documents but its source module is absent from the live tree | No current importable quantity | It cannot be a C17 dependency unless its source, tests, semantics, and identity are restored; the totalized operational composer below is not a substitute |
| Totalized operational edge composition | `heterodiff.models.configuration_totalized_jump_potential_composer_torch` | A separately defined operational-surrogate jump target | The analytic \(h\)/\(\widehat h\) target in this theorem |
| Reference candidate preflight | `heterodiff.processes.plugin_bridge_sampler.ProcessValidReferenceJumpComposer` | Reference intensity and one normalized process-valid edit candidate | Controlled clock, full ideal generator, drift integration, or full path sampler |

The method specification names
`heterodiff.theory.mixed_hybrid_oracle`,
`heterodiff.theory.mixed_hybrid_conditional_oracle`, and
`heterodiff.theory.mixed_hybrid_conditional_sampler`, but corresponding source
files are not present in the live `src/heterodiff/theory` tree inspected on
2026-08-28. Their documented historical evidence cannot serve as a current
importable C17 dependency until the source, tests, and exact identities are
restored and hash-bound.

No live module currently implements all of the following together:

- the general same-context joint/product trainer and nuisance branch;
- the exact unknown residual \(r^*\) or its derivative/edge certificates;
- a proved NCE-to-hybrid-Dirichlet coercivity/transport bridge;
- the complete defect diagnostic with a nonvacuous simultaneous uncertainty
  rule;
- the ideal learned continuous-plus-all-jump path law; and
- a general mixed path-KL/TV evaluator including the initial tilt.

## 10. Precise impossibility findings at this snapshot

1. **A distribution-free NCE-to-path theorem is impossible.** Value-level
   logistic excess cannot upper-bound continuous gradients or all graph-edge
   differences on the declared unrestricted smooth/neural class. Fork A must
   impose and verify a restrictive inverse estimate; otherwise only Fork B is
   defensible.
2. **The exact real-domain C17 terms are not currently observable.** They
   depend on \(h\), \(r^*\), and the \(P^h\) occupation law, none of which is
   available for the two real tasks. Existing architecture ceilings are not
   errors relative to \(r^*\).
3. **The general ideal plug-in path is not currently executable.** The live
   implementation inventory is partial and contains operational-surrogate and
   finite-resolution components with explicit nonclaims. It cannot be used as
   if it sampled \(P^{\widehat h}\).
4. **The complete cap/reference stability route is absent.** The analytic cap
   identity and partial proposal routines exist, but no proved residual-PDE
   stability estimate or complete high-probability defect certificate places
   them into a C17 bound.
5. **A finite oracle pass cannot close the theorem.** Finite-state path-KL and
   population-risk routines are necessary falsification tools, but they omit
   the general continuous-stratum proof, real-domain measure shift, and
   approximation error.

These are blockers, not requests to weaken the claim. If they remain at
submission time, C17 must stay unproved and be removed as a promoted theorem.

## 11. Promotion and failure rule

C17 remains `UNPROVED` until one immutable packet contains:

1. a final theorem statement whose symbols match the frozen executable method;
2. a complete proof of Theorem C17.1 under explicit, checked A1--A12;
3. a completed Fork A or Fork B with finite nonvacuous constants or bounds;
4. exact finite and mixed known-law instantiations covering initialization,
   continuous drift, birth, death, replacement, endpoint, and path law;
5. the code-to-symbol and estimand-to-artifact crosswalk;
6. all counterexample and boundary tests;
7. a fresh ordinary proof/code audit; and
8. a preregistered numerical threshold met without changing the claim,
   measure, proposal, comparator, or domain.

Failure of the coercivity bridge does not authorize silently dropping the
gradient or edit terms. Failure to estimate \(r^*\) does not authorize using a
global residual range as a surrogate error. Failure of the cap decomposition
does not authorize adding the defect twice. A null or negative result is a
valid terminal outcome.

Until all eight items exist, the exact allowed conclusion is:

> **C17 is a mathematically specified but unproved target. The general
> estimator-to-hybrid-path guarantee is unavailable, no manuscript claim is
> promoted, and no confirmatory execution is authorized by this document.**
