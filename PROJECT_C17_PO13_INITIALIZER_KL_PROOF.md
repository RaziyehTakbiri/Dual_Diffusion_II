# C17 Gate-A Fork-B route narrowing and PO13 initializer-KL proof

**Package state:** `C17_GATE_A_ROUTE_NARROWED_NO_GO_PO13_PROVED_C17_UNPROVED`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Selected route:** `FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES`  
**Proof-obligation effect:** `PO13_DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS`  
**Gate-A effect after independent audit:** C17 item eligible to check as
`ROUTE_NARROWED_PREOUTCOME_NO_GO`, not as theorem viability  
**Scientific effect:** zero

## 1. Authority and stopped scope

The normalized visible authority for this additive local proof package is
exactly:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

The normalized UTF-8 text is 207 bytes and has SHA-256
`44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a`.
Raw transport bytes, trailing HTML-space transport content, the conversation
envelope, account identity, and a cryptographic user signature are not bound.
The sentence authorizes continued bounded local project work during the
user's absence. It does not authorize external contact, browsing, data
access, entropy, runtime approval, training, a scientific execution, a formal
test result, claim promotion, submission, or tracker edits.

This package adds only the following four files:

1. `PROJECT_C17_PO13_INITIALIZER_KL_PROOF.md`;
2. `research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json`;
3. `research/diagnostics/manuscript_v3_c17_po13_initializer_kl_proof_v1.py`;
4. `tests/unit/test_manuscript_v3_c17_po13_initializer_kl_proof_v1.py`.

The machine record binds the predecessor Fork-B register and the exact local
theorem/code snapshot used here. The validator is read-only. Its deterministic
two-state witness is a qualification aid, not a scientific run and not the
proof. No existing source, manuscript, ledger, timetable, or tracker is
modified.

## 2. Exact theorem and hypotheses

Let \((E,\mathcal E)\) be a measurable space, let \(\rho\) be a probability
measure, and let \(h,\widehat h:E\to(0,\infty)\) be measurable. Assume

\[
0<Z_h:=\int h\,d\rho<\infty,
\qquad
0<Z_{\widehat h}:=\int \widehat h\,d\rho<\infty.
\tag{13.1}
\]

Define the exact-target and plug-in initial laws

\[
dP_0=\frac{h}{Z_h}\,d\rho,
\qquad
dQ_0=\frac{\widehat h}{Z_{\widehat h}}\,d\rho,
\qquad
e=\log\frac{\widehat h}{h}.
\tag{13.2}
\]

Strict positivity makes \(P_0\) and \(Q_0\) equivalent. No finite state
space, density relative to Lebesgue measure, bounded residual, or real-domain
instantiation is assumed.

### Theorem PO13.1 (initializer density ratio and oriented KL)

Under (13.1)--(13.2),

\[
\frac{dP_0}{dQ_0}
=\frac{Z_{\widehat h}}{Z_h}e^{-e},
\qquad
\mathbb E_{P_0}[e^e]
=\frac{Z_{\widehat h}}{Z_h},
\tag{13.3}
\]

and, with extended values allowed,

\[
\boxed{
\operatorname{KL}(P_0\Vert Q_0)
=\log\frac{Z_{\widehat h}}{Z_h}-\mathbb E_{P_0}[e]
=\log\mathbb E_{P_0}[e^e]-\mathbb E_{P_0}[e].
}
\tag{13.4}
\]

Here \(\mathbb E_{P_0}[e]\in[-\infty,\infty)\) is well defined: (13.3)
implies \(\mathbb E_{P_0}[e^+]<\infty\). Thus no \(\infty-\infty\)
ambiguity occurs. The initializer KL is finite exactly when
\(\mathbb E_{P_0}[e^-]<\infty\).

If it is finite, it is nonnegative and equals zero exactly when \(e\) is
constant \(P_0\)-almost surely, equivalently when \(P_0=Q_0\). For every
constant \(c\), replacing \(e\) by \(e+c\) leaves (13.4) unchanged.

### Corollary PO13.2 (certified oscillation bound)

If a separately justified certificate establishes
\(m\le e\le M\), \(P_0\)-almost surely, then Hoeffding's lemma applied under
\(P_0\) gives

\[
\operatorname{KL}(P_0\Vert Q_0)
=\log\mathbb E_{P_0}[e^{e-\mathbb E e}]
\le\frac{(M-m)^2}{8}.
\tag{13.5}
\]

The range \(M-m\) is gauge invariant. Equation (13.5) is a valid future
route to \(U_0\) only when the range is certified for the *actual error*
\(e=r_\theta-r^*\) on the exact target initial law. A range for
\(r_\theta\) alone, an architecture ceiling, or an unknown bound involving
\(r^*\) is not such a certificate. No range, threshold, or numerical
\(U_0\) is supplied by this package.

## 3. Proof

By strict positivity and (13.2), both tilted laws have the same null sets as
\(\rho\). Their Radon--Nikodym quotient is

\[
\frac{dP_0}{dQ_0}
=\frac{h/Z_h}{\widehat h/Z_{\widehat h}}
=\frac{Z_{\widehat h}}{Z_h}\frac{h}{\widehat h}
=\frac{Z_{\widehat h}}{Z_h}e^{-e},
\]

which proves the first part of (13.3). Direct integration gives

\[
\mathbb E_{P_0}[e^e]
=\int\frac{\widehat h}{h}\frac{h}{Z_h}\,d\rho
=\frac{Z_{\widehat h}}{Z_h},
\]

which is positive and finite. Since \(x^+\le e^x\) for all real \(x\),
\(e^+\) is \(P_0\)-integrable. Taking the \(P_0\)-expectation of the log
of the density quotient is therefore well defined in \([0,\infty]\) and
yields (13.4). If \(e^-\) is not integrable, the result is \(+\infty\); if
it is integrable, the expression is finite.

For the finite case, Jensen's inequality gives

\[
\log\mathbb E_{P_0}[e^e]\ge\mathbb E_{P_0}[e].
\]

Strict convexity of the exponential makes equality equivalent to \(e\) being
constant \(P_0\)-almost surely. In that case (13.3) makes the density ratio
one; conversely equality of the laws makes the density ratio one and forces
\(e\) to be constant almost surely. Adding \(c\) adds \(c\) to both terms
in (13.4), so they cancel. Finally, applying Hoeffding's lemma to the centered
variable \(e-\mathbb E e\), whose range length is \(M-m\), proves (13.5).
This completes PO13's initializer derivation and orientation under its stated
objects.

## 4. Orientation is substantive

The reverse initializer divergence is

\[
\operatorname{KL}(Q_0\Vert P_0)
=\log\mathbb E_{Q_0}[e^{-e}]+\mathbb E_{Q_0}[e],
\tag{13.6}
\]

which changes both the occupation measure and the log-mgf sign. It is not a
rewrite of (13.4).

An exact two-state witness makes the distinction explicit. Take base weights
\((1/2,1/2)\), exact tilt \(h=(2,1)\), and plug-in tilt
\(\widehat h=(1,3)\). Then

\[
P_0=(2/3,1/3),\qquad Q_0=(1/4,3/4),\qquad
e=(-\log2,\log3),
\]

and

\[
\begin{aligned}
\operatorname{KL}(P_0\Vert Q_0)
&=\tfrac23\log\tfrac83+\tfrac13\log\tfrac49,\\
\operatorname{KL}(Q_0\Vert P_0)
&=\tfrac14\log\tfrac38+\tfrac34\log\tfrac94.
\end{aligned}
\tag{13.7}
\]

These values are positive and unequal. The machine record stores only exact
rational weights and symbolic log-ratio factors; ordinary decimal evaluation
in the hostile suite is merely an orientation check.

## 5. Decisive obstructions: dynamic-only control is insufficient

Put the two initial laws from (13.7) on a two-state process with zero
generator, so every path is constant. The map taking an initial state to its
constant path is a measurable bijection onto the support of both path laws.
Relative entropy is therefore preserved by that map:

\[
\operatorname{KL}(P_{\mathrm{path}}\Vert Q_{\mathrm{path}})
=\operatorname{KL}(P_0\Vert Q_0)>0.
\tag{13.8}
\]

All continuous-gradient and jump-compensator terms are exactly zero. Thus no
certificate covering only \(K_C,K_+,K_-,K_R\) can bound the complete path KL;
\(K_0\) is logically indispensable. This obstruction is exact and does not
depend on floating evaluation.

The witness is not a clean-hold violation: it is a standalone path-law
counterexample to *omitting* the initializer term, not an instantiation of the
full terminal-matched C17 bridge.

### Theorem PO13.5 (smooth terminal-matched unbounded obstruction)

The preceding finite witness can be strengthened to a smooth family that
satisfies terminal matching and has unbounded initializer KL while every
dynamic component remains zero.

For any integer \(n\ge2\), take \(E=[0,1]\) with uniform base initial law,
horizon \(T>0\), zero base drift, zero covariance, and no jumps. Let the
terminal likelihood and exact information function be

\[
g_n(x)=h_{n,t}(x)=e^{nx},\qquad 0\le t\le T.
\tag{13.9}
\]

This \(h_n\) is positive, finite, smooth, and harmonic for the zero generator.
Choose a smooth \(\alpha:[0,T]\to[0,1]\) with \(\alpha(0)=0\) and
\(\alpha=1\) throughout the declared clean-hold interval (including at
\(T\)). Use the common guide \(\widetilde h_n=h_n\), so \(r_n^*=0\), and
define

\[
\widehat h_{n,t}(x)
=e^{\alpha(t)nx}
=\widetilde h_{n,t}(x)
  e^{(\alpha(t)-1)nx}.
\tag{13.10}
\]

Thus \(r_{\theta,n}=r_n^*=0\) throughout the clean hold and
\(\widehat h_{n,T}=h_{n,T}=g_n\): the plug-in is terminal matched. Both
controlled local generators are the zero generator. They have the same
degenerate covariance, there are no legal jump edges or compensators, and
their path laws are the unique constant-path laws induced by their normalized
initial distributions.

At time zero, \(\widehat h_{n,0}=1\), hence the plug-in initial law is uniform,
whereas the exact target has density

\[
p_n(x)=\frac{ne^{nx}}{e^n-1}.
\tag{13.11}
\]

Direct integration gives

\[
\begin{aligned}
K_{0,n}
&=\operatorname{KL}(p_n\Vert\operatorname{Unif}[0,1])\\
&=\frac{n e^n}{e^n-1}-1
  -\log\frac{e^n-1}{n}\\
&>\log n-1.
\end{aligned}
\tag{13.12}
\]

The strict lower bound follows from
\(e^n/(e^n-1)>1\) and
\(\log((e^n-1)/n)<n-\log n\). Consequently
\(K_{0,n}\to\infty\), while for every \(n\)

\[
K_{C,n}=K_{+,n}=K_{-,n}=K_{R,n}=0.
\tag{13.13}
\]

This proves that terminal matching, exact agreement of all post-initial local
characteristics, and even zero dynamic error do not provide any finite
uniform control of the full path KL. A separate initializer certificate is
not merely conservative bookkeeping; it is mathematically necessary. The
construction uses no dataset, learned checkpoint, numerical solver, or
floating approximation.

## 6. Shared-guide lemma and its strict limit

If one positive guide is used on both sides,

\[
h=\widetilde h e^{r^*},\qquad
\widehat h=\widetilde h e^{r_\theta},
\]

then pointwise

\[
e=\log(\widehat h/h)=r_\theta-r^*.
\tag{13.14}
\]

Consequently (13.4) depends on the shared guide only through the actual error
and cannot accept a guide harmonic/cap defect as a second initializer-KL
summand. This proves a narrow algebraic cancellation lemma. It does **not**
discharge PO16: the project still lacks a selected, proved, nonoverlapping
cap/reference stability or projection route that certifies the actual error.

## 7. Gate-A route-narrowing decision

The Gate-A timetable permits either demonstrated C17 viability **or** a route
narrowed before outcomes. The current evidence supports the second branch
only. This package freezes the following stopped decision:

> `REAL_DOMAIN_C17_PROMOTION_UNDER_CURRENT_FORK_B_OBSERVABILITY = NO_GO`.
> C17 remains an unproved theorem target. Only a conditional mathematical
> theorem and finite/mixed known-law falsification route survives. C17 may not
> be counted as a real-domain contribution, model-quality guarantee, or
> execution premise.

This is not a claim that Fork B is impossible in every future project. It is
a fail-closed decision for this project's present evidence: the exact target
occupation or a proved dominating law, the actual error relative to \(r^*\),
all five finite nonvacuous bounds, and a simultaneous event are absent. The
smooth family above also rules out the tempting fallback of certifying only
the four dynamic terms.

Real-domain C17 promotion may be reconsidered only if a new, pre-outcome,
independently audited packet satisfies **all** of the following conditions:

1. `S1_PATH_IDENTITY`: PO14 is completely proved with all required A1--A12
   hypotheses and exact target-first orientation, including A11's ideal-law
   versus numerical/operational separation and A12's candidate-base
   conditioning scope.
2. `S2_INITIALIZER`: the exact target initial law or an admitted dominating
   law with exact Radon--Nikodym factors is bound, and a finite nonvacuous
   \(U_0\) controls the actual \(e_0=r_{\theta,0}-r_0^*\).
3. `S3_CONTINUOUS`: the target continuous occupation or exact domination is
   bound, and a finite \(U_C\) controls the actual covariance-weighted
   gradient error, including degenerate directions.
4. `S4_BIRTH`, `S5_DEATH`, and `S6_REPLACEMENT`: each aggregate unlabeled
   legal family has exhaustive support, multiplicity/fiber factors, target
   compensator or exact domination, actual-error edge increments, and its own
   finite upper bound.
5. `S7_SIMULTANEITY`: one prespecified simultaneous event covers
   \(U_0,U_C,U_+,U_-,U_R\), including numerical and proposal error without
   self-normalized substitution or post-result tuning.
6. `S8_NONVACUITY`: the total threshold and failure rule are frozen before
   outcomes and the certified sum is strictly below that threshold.
7. `S9_FALSIFICATION_AND_AUDIT`: finite and mixed known-law gates cover all
   five components, hostile orientation/support cases pass, and a fresh
   proof/code audit binds the exact implementation.

The conditions are conjunctive. Partial satisfaction does not reopen the
route. A later packet must supersede this decision explicitly; tracker prose,
an NCE value, a residual architecture range, a finite point estimate, or a
known-law pass alone cannot do so.

After independent mathematical and exact-byte audit, the eligible Gate-A
predicate is

`GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO=true`.

Checking the corresponding timetable item would mean only that the route was
narrowed before outcomes. It must not be worded as “C17 viable,” “C17 proved,”
or “Fork B certified.”

## 8. Proof/code crosswalk

| Mathematical object | Local code surface | Evidentiary use |
|---|---|---|
| Normalized initial tilt | `conditional_initial_law` in `finite_bridge_path_control.py` | Finite binary64 implementation witness; not the general proof |
| Directed initial KL | `_initial_kl` used by `ctmc_path_kl` in `path_kl.py` | Finite binary64 orientation witness; private helper, not a public certificate |
| Exact proof | this document, Theorem PO13.1 | General measurable-space derivation conditional on positive finite normalizers |
| Exact two-state witness | rational record in the machine artifact | Falsifies orientation interchange and dynamic-only omission |
| Future `U0` route | Corollary PO13.2 | Conditional range theorem only; no actual-error range is present |

The source snapshot is hash-bound and its required symbols are checked by AST
without importing project science. Neither finite implementation uses formal
arithmetic, and neither supplies a real-domain \(U_0\).

## 9. Exact effects and remaining work

After independent exact-byte and mathematical audit, this package is eligible
to establish exactly two project-control predicates:

- `C17_PO13_INITIALIZER_KL_DERIVATION_AND_ORIENTATION_PROVED=true`; and
- `GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO=true`.

The eligible proof-register update is:

- `PO13_INITIALIZER_KL_DERIVATION_AND_ORIENTATION`:
  `DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS`;
- real-domain verification of A3: still false;
- finite nonvacuous `U0`: still null;
- `PO01`--`PO12` and `PO14`--`PO18`: still open;
- all A1--A12 domain assumptions: still open;
- B01 and F001--F006: still open/null;
- Gate A's C17 viability-or-narrowing item: eligible to check only as
  `ROUTE_NARROWED_PREOUTCOME_NO_GO` after independent audit;
- C17 theorem and manuscript claim: still unproved/unpromoted.

The package closes 0 of 172 preregistration fields, 0 of 12 blockers, 0 formal
tests, and 0 scientific results. It authorizes no runtime or scientific
execution. PO13 is a mathematical proof-register obligation, not one of the
172 preregistration fields.

The next C17 action is therefore not ordinary implementation. It is either
(i) production of the complete S1--S9 supersession packet before outcomes, or
(ii) retention of C17 only as an unproved specification/known-law
falsification route while the real-domain contribution is rescoped. No
intermediate state reopens real-domain promotion.
