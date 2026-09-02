# C17 Fork-B direct-certificate contract

**Status:** `PARTIAL_CONTRACT_NOT_A_PROOF`  
**C17 claim status:** `UNPROVED`  
**R2-HYBRID status:** `NOT_RUN`  
**Claim promotion:** `NONE`  
**Confirmatory execution authorized:** no

This document fixes the next scientific step after the C17 theorem target. It
selects the direct-certificate route (Fork B): measure the initializer,
continuous-gradient, and every legal jump-family error instead of assuming
that value-level classifier loss controls them. It does not weaken or replace
[`c17_hybrid_path_error_theorem.md`](c17_hybrid_path_error_theorem.md).

The first implementation is deliberately a small factorized CTMC--OU
falsification fixture. A successful fixture is necessary evidence that the
formulas and orientations have been implemented coherently; it is not a
certificate for a learned model, an association model, PhysioNet, Retail, or
the full heterogeneous process.

## 1. Frozen direction and quantities

The only forward direction used for the C17 target is

\[
\operatorname{KL}(P^h\,\|\,P^{\widehat h}),
\qquad
e=\log(\widehat h/h).
\]

For identical covariance, terminal likelihood, boundary mechanism, and jump
support, the direct quantities are

\[
\begin{aligned}
K_0 &= \operatorname{KL}(\rho_0^h\,\|\,\rho_0^{\widehat h}),\\
K_C &= \frac12\,\mathbb E_{P^h}\int_0^T
       \nabla e_t^{\mathsf T}a_t\nabla e_t\,dt,\\
K_J &= \mathbb E_{P^h}\int_0^T\int
       q_t^{h,J}(Y_{t-},dy')\,
       \Phi(e_t(y')-e_t(Y_{t-}))\,dt,
       \quad J\in\{+, -, R\},\\
\Phi(v)&=\exp(v)-1-v.
\end{aligned}
\]

The required decomposition is

\[
K_{\mathrm{path}}=K_0+K_C+K_++K_-+K_R.
\]

The expectation and occupation law are those of the exact conditioned law
\(P^h\), not the plug-in law. The reverse orientation is a diagnostic only; it
must use plug-in occupation and cannot be substituted into the forward bound.

## 2. Factorized falsification fixture

The local fixture uses the existing six-state, two-type capped counting CTMC
with nonempty birth, death, and replacement families, independently multiplied
by a scalar OU process. Its residual perturbation has the form

\[
e(t,i,x)=(1-t/T)\{s c_i+\beta x+\gamma\}.
\]

This form is chosen because it supplies exact structural controls:

- `e(T,i,x)=0`, so exact and plug-in potentials share the terminal law;
- the OU gradient is `beta * (1 - t/T)`;
- every jump increment is
  `s * (1 - t/T) * (c_destination - c_source)`;
- the gauge `gamma` cancels from normalized initialization, gradients, and
  jump increments; and
- the target initial OU law tilted by `exp(beta*x)` remains Gaussian with an
  analytic initializer KL.

The discrete terms must use aggregate rates on the unlabeled counting state.
Occurrence-labelled paths to the same destination may not be counted as
independent edges. Birth, death, and replacement must remain separate in the
record even when their sum is also reported.

## 3. Required independent checks

The fixture is acceptable only if all of the following hold:

1. the terminal residual is exactly zero for every state and coordinate;
2. zero non-gauge perturbation gives zero initializer, dynamic, and total KL;
3. changing only the gauge leaves every path-law quantity unchanged;
4. the nonzero fixture gives positive initializer, OU, birth, death, and
   replacement contributions;
5. the five components sum to the reported forward total;
6. a separately evaluated finite time-inhomogeneous CTMC path-KL routine agrees
   with the discrete initializer plus the three jump components;
7. a fixed-order calculation using direct Poisson-rate divergence agrees with
   the adaptive `q^h Phi(Delta e)` calculation;
8. forward and reverse orientations are distinct on the nonzero asymmetric
   fixture and are never mixed;
9. the OU term uses `diffusion**2`, the correct direct clock, and the factor
   `1/2`; and
10. malformed types, nonfinite values, excessive log tilts, and unusable
    numerical controls fail closed.

Endpoint agreement alone is not a path-law check. The implementation must
exercise initializer and holding/jump-rate contributions.

## 4. Numerical qualification

The change-of-measure identity and the closed-form OU/initializer expressions
are mathematical identities for the stated ideal fixture. Binary64 matrix
exponentials, adaptive quadrature, fixed Gauss--Legendre quadrature, and ODE
integration are numerical evaluations. Their library error estimates and
cross-method agreement are not interval enclosures.

Every result must therefore distinguish:

- `mathematical_identity_exact`;
- `floating_evaluation_performed`;
- `interval_certified` (false at this checkpoint);
- `adaptive_error_estimate_is_rigorous_bound` (false); and
- `applied_to_gate_or_claim_decision` (false).

No tolerance may silently turn this diagnostic into an R2 or C17 pass.

## 5. Shared guide and cap defect

When both exact and plug-in potentials use the same positive guide,

\[
h=\widetilde h\exp(r^*),\qquad
\widehat h=\widetilde h\exp(r_\theta),
\]

the path error is `e = r_theta - r_star`; the shared guide cancels. The guide's
harmonic or blocked-birth cap defect is not an additional path-KL summand.

The factorized fixture does not implement the full association guide or its
cap defect. It must report `cap_defect_cancellation_exercised=false`. A later
fixture may exercise that algebra explicitly, but it still may not add the
defect to `K_path` without a separate proved stability or projection result.

## 6. What is still required for a real Fork-B certificate

The factorized fixture leaves the actual hard quantities unresolved. Before
C17 can be promoted, a learned-method certificate must provide, under the
exact admitted observation and context:

- an error reference for `r_star`, not merely bounds on `r_theta`;
- the exact target occupation law or a proved dominating measure;
- simultaneous upper bounds for the continuous gradient and every legal
  birth, death, and replacement error;
- source multiplicities, destination mark-fiber measures, type/Radon--Nikodym
  factors, cap indicators, and structural zeros from the true aggregate
  kernel;
- an initializer bound with correctly oriented normalizer and expectation
  bounds;
- a fixed-observation rather than merely observation-averaged statement;
- finite, prespecified uncertainty and numerical-error controls; and
- a nonvacuous total bound below the preregistered scientific threshold.

If any term contains an unknown norm of `r_star`, an arbitrary global
envelope, a post-result grid/proposal choice, or an unreported observation or
occupation change of measure, the certificate fails.

## 7. Exact checkpoint conclusion

Passing the local implementation permits only this statement:

> The directed initializer, continuous-gradient, and three jump-family
> components have been instantiated consistently on one finite factorized
> CTMC--OU falsification fixture, with independent floating-point
> cross-checks. The general C17 theorem remains unproved, R2-HYBRID remains
> unrun, no manuscript claim is promoted, and confirmatory execution remains
> unauthorized.

