# C17 cap-defect cancellation contract

**Status:** `PARTIAL_CAP_CANCELLATION_CHECKPOINT_NOT_A_PROOF`  
**Scope:** `FINITE_CAP3_GUIDE_RESTRICTED_TO_CAP2_MIXED_CTMC_OU_FIXTURE`  
**Claim promotion:** `NONE`  
**R2-HYBRID:** `NOT_RUN`  
**Confirmatory execution authorized:** no

## 1. Purpose

This checkpoint tests one narrow algebraic obligation in the proposed C17
argument: a nonzero blocked-birth defect of an auxiliary uncapped-or-larger-cap
guide must not be added as a second path-error term after the exact and plug-in
laws have both been factorized through that same guide.

The checkpoint extends the six-state cap-two counting component of
`mixed_ctmc_ou_known_law_oracle.py`. It does not create a trained residual,
restore a missing mixed conditional oracle, or promote the finite fixture to a
general marked-configuration theorem.

## 2. Frozen cap-two target and cap-three auxiliary guide

The target state space is

\[
\mathcal X_2=\{(n_\alpha,n_\beta)\in\mathbb N^2:
n_\alpha+n_\beta\le 2\},
\]

with horizon `T=0.8`, birth rates `(0.7, 0.4)`, per-occurrence death
rates `(0.5, 0.3)`, and row-source/column-destination replacement rates

\[
\begin{pmatrix}0&0.2\\0.35&0\end{pmatrix}.
\]

The exact target information is

\[
h_i(t)=[\exp((T-t)Q^{(2)})g^{(2)}]_i,
\]

where

\[
g(n_\alpha,n_\beta)
=1+0.75n_\alpha+0.4n_\beta+0.2n_\alpha n_\beta.
\]

The auxiliary guide uses the same rates and likelihood formula on
`X_3`, the cap-three space:

\[
\widetilde h_j(t)
=[\exp((T-t)Q^{(3)})g^{(3)}]_j.
\]

It is evaluated on `X_2` by the exact state-vector inclusion. The cap-three
guide is an algebraic auxiliary object only; this checkpoint does not call it
an exact guide for the cap-two target.

## 3. Blocked-birth defect identity

For a cap-two state `i`, let `B(i)` be its cap-three birth destinations that
are absent from the cap-two generator. The required identity is

\[
\frac{(\partial_t+Q^{(2)})\widetilde h_i(t)}
     {\widetilde h_i(t)}
=-
\sum_{j\in B(i)}Q^{(3),+}_{ij}
\left(\frac{\widetilde h_j(t)}{\widetilde h_i(t)}-1\right).
\tag{CAP.1}
\]

It must hold at every evaluated time and cap-two state. Both sides must be
zero below the cap. At least one cap-boundary value must be nonzero, otherwise
the fixture has not exercised the obstruction.

The implementation obtains `partial_t tilde_h = -Q3 tilde_h`; no finite
difference is permitted in the primary identity. Matrix exponentials and all
reported residuals remain ordinary binary64/SciPy calculations, not interval
enclosures.

## 4. Shared-guide factorization

For the exact cap-two information and the restricted guide define

\[
r^*(t,i)=\log h_i(t)-\log\widetilde h_i(t).
\]

Let the terminal-matched plug-in error from the existing Fork-B fixture be

\[
e(t,i,x)=(1-t/T)(s c_i+\beta x+\gamma),
\]

and define

\[
r_\theta(t,i,x)=r^*(t,i)+e(t,i,x).
\]

Then

\[
\log\frac{\widetilde h_i(t)e^{r_\theta(t,i,x)}}
               {\widetilde h_i(t)e^{r^*(t,i)}}
=e(t,i,x).
\tag{CAP.2}
\]

The guide and its nonzero defect cancel before any initializer, diffusion, or
jump Bregman term is formed. The cancellation must be checked for a fixed grid
of times, every cap-two state, and multiple continuous coordinates.

## 5. Path-error invariance

The forward orientation remains

\[
\mathrm{KL}(P^h\Vert P^{\widehat h}).
\]

The cap-factorized checkpoint must reproduce, without adding a defect term,
the existing five-component Fork-B decomposition:

\[
K_0+K_C+K_++K_-+K_R.
\]

Required equalities are:

- the normalized initializer error is unchanged;
- the OU spatial-gradient error is unchanged;
- every legal birth, death, and replacement increment of `e` is unchanged;
- the separately reported `K_+`, `K_-`, and `K_R` values are unchanged;
- the total is exactly the sum of those five quantities within the declared
  binary64 comparison tolerance;
- no cap-defect scalar is included in that sum.

The shared guide may affect `r*` and `r_theta` separately. It cannot affect
their difference, its spatial gradient, or its legal-edge differences.

## 6. Hostile checks

The focused tests must reject or detect:

1. using a cap-two guide in place of the frozen cap-three guide;
2. a state-order mismatch between `X_2` and `X_3`;
3. omission of either blocked birth type at a cap-boundary state;
4. a sign reversal in (CAP.1);
5. insertion of the defect into any path-KL component or total;
6. unequal guides in the exact and plug-in factorizations;
7. a nonterminal plug-in error at `t=T`;
8. a changed initializer, OU, birth, death, or replacement quantity;
9. mutation or writeability of returned arrays; and
10. boolean, nonfinite, out-of-range, or excessive-grid inputs.

## 7. Numerical and scientific boundary

Passing this checkpoint establishes only that, on the declared finite
factorized fixture:

- the larger-cap auxiliary guide has a nonzero blocked-birth defect;
- the primary defect identity is numerically reproduced;
- the common-guide factorization cancels that defect from
  `log(hhat/h)=r_theta-r*`; and
- the previously recorded five path-error quantities are unchanged.

It does **not** establish:

- an interval-certified matrix exponential or path integral;
- a trained or selected residual checkpoint;
- an error certificate relative to a learned residual's unknown `r*`;
- unordered association marginalization;
- occurrence-attached heterogeneous marks;
- a mixed conditional sampler or whole-method path law;
- the general C17 theorem or a coercivity bridge;
- completion of R2-HYBRID;
- confirmatory or production execution authority; or
- any manuscript claim promotion.

The next scientific checkpoint after this one remains the construction of an
exact mixed marked conditional oracle and a legitimate trained residual
checkpoint under the frozen execution preregistration. Only then can the same
initializer, gradient, and every-legal-edge errors be evaluated against
`r*` rather than a test-owned perturbation.
