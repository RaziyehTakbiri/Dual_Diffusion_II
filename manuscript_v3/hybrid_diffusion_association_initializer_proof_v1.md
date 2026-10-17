# Association guide and cap-conditioned initializer: proof appendix

Date: 2026-09-13  
Status: complete derivations for the specified ideal reference laws, with an
implementation crosswalk. These are structural results, not a claim of a
learned-posterior guarantee, numerical exactness or novelty.

This appendix completes claim S5 of the
[scientific claim ledger](hybrid_diffusion_claims_and_proof_plan_v1.md).
The [scientific core](hybrid_diffusion_scientific_core_v1.md) specifies the
training target and learned model. The conclusions below distinguish three
different laws that must not be conflated:

1. An uncapped independent birth/death–OU reference propagated from a fixed
   current configuration: this defines the analytic guide.
2. A capped **initial prior**, subsequently propagated by that uncapped
   reference: this defines the analytic initializer's posterior.
3. The capped birth/death–OU reference throughout the path: its propagated
   likelihood generally differs from the analytic guide.

None of these is automatically the learned BASE law or the smoothed training
target Q0. The new [conditional-law contract](hybrid_diffusion_conditional_law_contract_v2.md)
addresses those further approximation questions.

## 1. Assumptions, notation and reference measures

Fix a context. Let D be countable, rho(d)>0 and sum_d rho(d)=1.
Each key d has a fiber of dimension k(d) in {0,1}; write

\[
E=\bigsqcup_{d\in D}\{d\}\times\mathbb R^{k(d)},\qquad
\nu(d,dr)=\rho(d)\phi_{k(d)}(dr).
\]

Phi_1 is standard Gaussian probability and phi_0 is a point mass. A state is
a finite counting measure, so equal events retain occurrence multiplicity.
All calculations use temporary occurrence labels before passing to the
counting measure. N,M are finite nonnegative integers, theta,delta,sigma>0,
p=1/2, and 0<epsilon<1. No positive lower bound on rho over all D is assumed.

Let Pi_infinity=PPP(theta nu). With

\[
c_N=\Pr\{\operatorname{Pois}(\theta)\le N\}
=e^{-\theta}Z_N(\theta),\qquad
Z_N(\theta)=\sum_{n=0}^{N}\theta^n/n!,
\]

define Pi_N=Pi_infinity conditioned on count<=N. Equivalently,
Pi_N has count probabilities p_N(n)=theta^n/(n! Z_N(theta)) and, given n,
n iid nu marks passed to their counting measure.

The observation reference is lambda=(C_M)_#PPP(nu), where C_M preserves
counts<=M and maps larger counts to one atom dagger. In particular,

\[
\lambda_\dagger=\Pr\{\operatorname{Pois}(1)>M\}>0.
\]

Retained-empty and overflow are distinct observations. The observation
kernel keeps each terminal occurrence independently with probability p,
preserves its key, and adds N(0,sigma^2) noise to each retained continuous
coordinate. The complete kernel is the **whole-observation** mixture

\[
K_\epsilon=(1-\epsilon)K_{\rm clean}+\epsilon\lambda.
\tag{1}
\]

Thus its lambda-density is g_epsilon=(1-epsilon)g_clean+epsilon.

All posterior formulas below specify the regular conditional version obtained
from the displayed Gaussian/atomic density formulas. On continuous observation
fibers, conditioning on a single value is understood through that version,
not as division by a positive point probability. Its evidence is positive for
every legal fixed observation because epsilon>0.

For the remaining interval, let J,C>=0 be finite integrated jump and
continuous clocks. Set beta=theta delta and

\[
A=e^{-\delta J},\quad c=e^{-C/2},\quad
D=pA,\quad K=p\theta(1-A),\quad
v=\sigma^2+1-c^2.
\tag{2}
\]

Here D is a probability and K a Poisson mean, not a key set or kernel.
Finite clocks give A,c>0; J=0 gives A=1 and K=0. Infinite-clock limits can
be derived separately but are not required or silently substituted by the
implementation.

The uncapped reference has immigrant births at rate beta times its jump
clock, per-occurrence deaths at rate delta times that clock, and independent
OU fibers with generator (-r partial_r+partial_r^2)/2 times the continuous
clock. Its ingredients are independent. These assumptions, together with
(1), define the probability experiment used below.

## 2. Lemma: the propagated occurrence experiment

Let x=sum_(i=1)^n delta_(d_i,r_i) be a fixed initial configuration; atomic
fibers omit r_i. Under the uncapped reference and the clean observation
channel:

- Each initial occurrence independently contributes at most one observation,
  with probability D. Conditional on contributing, its key is d_i and its
  continuous coordinate has law N(c r_i,v).
- Independently, future immigrants contribute a Poisson observation process
  with mean K and normalized mark law bar_nu, whose nu-density is

\[
\bar q(d,a)=
\begin{cases}
1,&k(d)=0,\\
\phi_{\sqrt{1+\sigma^2}}(a)/\phi_1(a),&k(d)=1.
\end{cases}
\tag{3}
\]

**Proof.** An initial occurrence survives all remaining death exposure with
probability exp(-delta J)=A. Detection multiplies this by p. Given survival,
OU evolution has mean c r_i and variance 1-c^2. Independent observation noise
adds sigma^2. Its key cannot change before death.

Using integrated jump time t, an immigrant born at t survives to J with
probability exp(-delta(J-t)). Thinning the Poisson immigration process gives
terminal immigrant mean

\[
\int_0^J\beta e^{-\delta(J-t)}dt
=\theta(1-A).
\]

Each immigrant is born with law nu; OU preserves its Gaussian fiber law and
does not alter its key. Detection and observation noise therefore give mean
K and mark law (3). The integral of bar_q against nu is one: sum rho=1,
and each continuous Gaussian density integrates to one. Immigration is
independent of initial-occurrence evolution, completing the proof. QED.

This is an independent-occurrence representation of the **uncapped**
process. Suppressing births at count N invalidates that independence and is
not accomplished merely by evaluating the formula at n<=N.

## 3. Theorem: normalized occurrence-level association formula

For a retained observation a=sum_(j=1)^k delta_(o_j), k<=M, define

\[
q_i(o_j)=
\begin{cases}
\mathbf1_{\{d_j=d_i\}}/\rho(d_i),&k(d_i)=0,\\
\displaystyle\frac{\mathbf1_{\{d_j=d_i\}}}{\rho(d_i)}
\frac{\phi_{\sqrt v}(a_j-c r_i)}{\phi_1(a_j)},&k(d_i)=1.
\end{cases}
\tag{4}
\]

An incompatible key has factor zero. A partial matching H is a collection
of pairs (i,j) using each source index and each observation index at most
once. Let I(H),O(H) be its used source and observation indices. Then

\[
\widetilde h_{\rm clean}(J,C;x,a)
=e^{1-K}\sum_H
 \prod_{(i,j)\in H}Dq_i(o_j)
 \prod_{i\notin I(H)}(1-D)
 \prod_{j\notin O(H)}K\bar q(o_j).
\tag{5}
\]

At overflow,

\[
\widetilde h_{\rm clean}(J,C;x,\dagger)
=\frac{\Pr\{\operatorname{Bin}(n,D)+\operatorname{Pois}(K)>M\}}
       {\lambda_\dagger},
\tag{6}
\]

with independent count terms. The complete guide is

\[
\widetilde h_\epsilon
=\epsilon+(1-\epsilon)\widetilde h_{\rm clean}.
\tag{7}
\]

It is the lambda-density of a normalized probability kernel and is at
least epsilon. It equals the conditional expectation of g_epsilon at the
uncapped reference endpoint.

**Proof of the quotient factors.** Before collapsing overflow, write a
symmetric test function F of k observation coordinates. The observation
configuration expectation on the k-occurrence component can be expressed as

\[
\frac1{k!}\int F(o_1,\ldots,o_k)\,j_k(o_1,\ldots,o_k)
\,\nu^{\otimes k}(do).
\]

Fix a subset I of b detected initial sources. Their Bernoulli probability
is D^b(1-D)^(n-b). The Poisson immigrants supply k-b observations with
Janossy factor exp(-K)K^(k-b). To express their superposition symmetrically,
assign the b distinct source occurrences injectively to the k observation
positions. These assignments are exactly the size-b partial matchings.
There are k!/(k-b)! assignments; dividing by k! recovers the immigrant
count factor 1/(k-b)!, with no missing or additional factor. Integrating
the source q_i and immigrant bar_q factors gives their normalized mark
laws. Summing b, source subsets and k reconstructs the probability experiment
of Section 2.

The unit-Poisson reference has Janossy density exp(-1), so dividing j_k by
exp(-1) yields (5). Both measures use the same 1/k! quotient, which cancels
in the RN ratio. This argument holds with atoms: it is an identity of
pushforward measures, not a distinct-points argument. For example, a purely
atomic observation multiplicity m_o has the same quotient multiplicity
factor 1/m_o! on both sides. Equal-valued sources and observations must
still occupy separate labeled slots in the matching sum.

The pre-collapse count is the sum in (6). Collapsing all counts>M therefore
gives (6), while retained components are unchanged. Summing their probabilities
and the overflow probability gives one. Applying the mixture (1) gives (7)
and its lower bound. The endpoint conditional-expectation statement follows
from composing the reference transition and K_epsilon. QED.

**Factorization and exact dynamic programming.** An edge in (5) can join
only equal complete keys. Consequently the matching polynomial factors over
exact-key groups. For one group, process source occurrences one at a time
and index a dynamic-programming table by the subset of assigned observation
occurrences. A source either contributes (1-D), leaving the subset unchanged,
or contributes Dq_i(o_j) to one unassigned index. After all sources, multiply
K bar_q for every remaining observation. The global exp(1-K) appears once.
Induction on the processed source count proves that each matching is included
once. Duplicates are never merged into a single assignment index.

**Boundary checks.**

- At J=C=0, K=0, D=p and c=1. Every retained observation must match a
  different source, so (5) becomes the terminal injection formula
  exp(1)p^k(1-p)^(n-k) sum_injections product q_i(o_j).
- For a retained empty observation, (5)=exp(1-K)(1-D)^n.
- For an empty source, (5)=exp(1-K) product_j K bar_q(o_j). This is zero
  for nonempty retained a when K=0, but (7) remains epsilon.
- At J=0 and M>=N, clean overflow is impossible for a source with n<=N,
  and its complete guide value is exactly epsilon.
- Zero-dimensional occurrences have no derivative coordinate. They remain
  ordinary occurrences in both the count and matching calculations.

## 4. Corollary: differentiable guide, scores and finite bounds

For a fixed retained observation define

\[
B_j=
\begin{cases}
1/\rho(d_j),&k(d_j)=0,\\
e^{a_j^2/2}/[\rho(d_j)\sigma],&k(d_j)=1,
\end{cases}
\qquad
B_a=e\,k!\prod_{j=1}^{k}B_j.
\tag{8}
\]

For overflow put B_dagger=1/lambda_dagger. For all finite latent counts,
including uncapped counts,

\[
0\le g_{\rm clean}(a\mid x)\le B_a,\qquad
\epsilon\le\widetilde h_\epsilon(J,C;x,a)
\le\epsilon+(1-\epsilon)B_a.
\tag{9}
\]

**Proof.** A terminal continuous Gaussian likelihood is at most
1/(sqrt(2pi)sigma); dividing by rho(d_j)phi_1(a_j) gives B_j.
The atomic bound follows directly. For a k-occurrence retained observation,
the terminal injection formula is therefore bounded by

\[
e(n)_k p^k(1-p)^{n-k}\prod_jB_j
=e\,k!\Pr\{\operatorname{Bin}(n,p)=k\}\prod_jB_j\le B_a.
\]

The case k>n is zero. An overflow probability is at most one. Conditional
expectation under the reference transition and (7) give (9). QED.

For fixed source keys, (5) is a finite sum of Gaussian functions of the
continuous source coordinates, plus structurally zero terms. It is smooth;
(7)>0 makes its logarithm smooth. No differentiation of rho or of key
equality is intended.

One can make the derivative calculation explicit. Normalize the positive
terms of (7), treating its epsilon term as a separate component. For a
matching component H set

\[
S_i(H)=\mathbf1_{\{i\ {\rm matched}\}}\,
 \frac{c(a_{j(i)}-cr_i)}v
\]

on continuous source occurrence i, and set S_i=0 for the contamination
component. Expectation under these normalized component weights gives

\[
\partial_{r_i}\log\widetilde h_\epsilon=\mathbb E[S_i],\qquad
\partial_{r_i}\partial_{r_\ell}\log\widetilde h_\epsilon
=-\mathbf1_{\{i=\ell\}}\frac{c^2}{v}\Pr\{i\ {\rm matched}\}
+\operatorname{Cov}(S_i,S_\ell).
\tag{10}
\]

This is the ordinary derivative-of-log-sum identity, applied to the finite
sum. It justifies the guide's within-fiber gradient and Hessian without an
exchange of an unbounded semigroup derivative and expectation. Overflow
depends only on count, so its coordinate derivatives vanish. Constants in
(8) are finite **for the fixed observation**, not uniformly over all
countably many keys or unbounded coordinates.

## 5. Theorem: retained-observation reference posterior

First let the current prior be Pi_infinity and suppose the observation is
retained and clean. Put t=p theta and m=theta(1-pA). Its evidence relative
to the retained part of lambda is

\[
m_{{\rm clean},\infty}(a)
=e^{1-t}t^k\prod_{j=1}^{k}\bar q(o_j).
\tag{11}
\]

The current-state posterior has the following construction:

1. Independently for each of the k observed **occurrences**, select it as
   having a current ancestor with probability A.
2. An ancestor copies the complete observed key. For a continuous anchor a_j,
   draw its current coordinate independently as

\[
R_j\mid a_j,\ {\rm ancestor}
\sim N\left(\frac{ca_j}{1+\sigma^2},
            \frac{v}{1+\sigma^2}\right).
\tag{12}
\]

   An atomic ancestor is exactly its observed atom.
3. Independently add a PPP(m nu) population of current occurrences that
   generate no retained terminal observation.
4. Forget temporary labels, preserving duplicate occurrences.

Thus the current count has law

\[
H_a=B+U,\qquad B\sim\operatorname{Bin}(k,A),\quad
U\sim\operatorname{Pois}(m),\quad B\perp U.
\tag{13}
\]

**Proof.** Split the initial Poisson process into current occurrences that
survive and are detected, and those that produce no observation. Poisson
thinning gives their means theta pA and theta(1-pA), independently.
The event of producing no observation is mark-independent, so the missed
population retains mark law nu.

Detected current ancestors and detected future immigrants are independent
Poisson observation processes with means p theta A and p theta(1-A).
Both have the same mark law bar_nu, because the Gaussian reference is
stationary. Their superposition is PPP(t bar_nu). Its RN density against
unit PPP(nu) gives (11). Conditional on each superposed observation occurrence,
its independent source label is current-ancestor with probability
(p theta A)/(p theta)=A. This remains true for coincident atoms: an
occurrence's latent source label is not determined by its observed value.

For a continuous ancestor, before observation R~N(0,1) and
a=cR+Z with independent Z~N(0,v). Their covariance is c and
Var(a)=c^2+v=1+sigma^2. Completing the square in
phi_1(R)phi_sqrt(v)(a-cR) gives (12). The variance is positive because
sigma>0. Conditional independence across ancestor occurrences follows from
the marked Poisson splitting construction. Its remaining independent current
population is the missed process already identified. This proves the
construction and (13). QED.

### 5.1 Conditioning the current prior on its total count

Let

\[
c_a=\Pr\{B+U\le N\}
=\sum_{b=0}^{\min(k,N)}
 {k\choose b}A^b(1-A)^{k-b}
 \Pr\{\operatorname{Pois}(m)\le N-b\}.
\tag{14}
\]

Zero-probability endpoint terms have their probability-law meanings, including
0^0=1 in a binomial mass. The clean evidence for Pi_N is

\[
m_{{\rm clean},N}(a)
=m_{{\rm clean},\infty}(a)c_a/c_N.
\tag{15}
\]

When c_a>0, its clean posterior is exactly the law in Section 5 conditioned
on B+U<=N. A non-rejection construction samples b with weights

\[
\Pr\{B=b\}\Pr\{U\le N-b\},\quad 0\le b\le\min(k,N),
\tag{16}
\]

then samples U conditional on U<=N-b, chooses uniformly a b-subset of the
k observation **indices**, and draws the corresponding marks from (12),
plus U independent nu marks.

**Proof.** Conditioning the prior is conditioning the joint probability
experiment on the event E={current count<=N}, which has probability c_N.
Bayes' formula gives

\[
\Pr(da\mid E)=\Pr(da)\Pr(E\mid a)/c_N.
\]

Section 5 identifies Pr(E|a)=c_a and the conditional current-state law, proving
(15) and the total-count restriction. The binomial ancestry indicators are
exchangeable, so their selected subset is uniform given b. Conditioning on
B+U<=N changes only the pair of counts and this subset-size distribution;
given b and U, the key and Gaussian mark draws remain as above. The elementary
factorization of the conditioned joint count mass yields (16). QED.

The two counts must **not** be clipped or separately conditioned on <=N.
Their sum is the prior event. For example, J=0 gives A=1, so all k anchors
must have current ancestors and c_a=Pr{Pois(theta(1-p))<=N-k}; if k>N
then c_a=0 and the clean branch is genuinely impossible. No posterior
conditioned on that impossible clean branch is asserted.

### 5.2 Whole-observation contamination

For every retained a, including a with c_a=0,

\[
m_{\epsilon,N}(a)=\epsilon+(1-\epsilon)m_{{\rm clean},N}(a)>0,
\tag{17}
\]

and

\[
\frac{\Pi_N(dx)\widetilde h_\epsilon(J,C;x,a)}
     {m_{\epsilon,N}(a)}
=(1-w_a)\Pi_N(dx)+w_a\,\Pi_N^{\,{\rm clean},a}(dx),
\qquad
w_a=\frac{(1-\epsilon)m_{{\rm clean},N}(a)}{m_{\epsilon,N}(a)}.
\tag{18}
\]

When c_a=0, interpret w_a=0 and do not construct the impossible component.

**Proof.** The contamination branch draws a from lambda independently of
the current state; its evidence density is one and its conditional state
law remains Pi_N. Integrating (7) gives (17), and ordinary mixture Bayes
weights give (18). QED.

For a retained empty observation, B=0, so the clean posterior count is
Pois(theta(1-pA)) conditioned on <=N. Formula (18) still mixes this with
Pi_N; it is not generally just a reference draw.

## 6. Theorem: overflow-observation reference posterior

Let T_n=Pr{Bin(n,D)+Pois(K)>M}. Since overflow depends only on the generated
observation count, the complete posterior current-count weights are

\[
w_n^\dagger \ \propto\
p_N(n)\left[\epsilon+(1-\epsilon)\frac{T_n}{\lambda_\dagger}\right],
\quad n=0,\ldots,N.
\tag{19}
\]

Given n, the current n marks remain iid nu. These formulas define a
normalized posterior because all bracketed terms are at least epsilon.

**Proof.** Conditional on initial count n, the observation-count law from
Section 2 is independent of initial marks: survival, detection and immigration
rates do not depend on keys or coordinates. Its overflow likelihood is
T_n/lambda_dagger. The prior conditional mark law therefore cancels unchanged
in Bayes' formula, giving (19). Finite n and positive epsilon give a positive
finite normalizer. QED.

The count likelihood can be computed with a finite recursion. Set
r_j^(0)=Pr{Pois(K)=j}, j=0,...,M, and T_0=Pr{Pois(K)>M}. For n>=0,

\[
r_0^{(n+1)}=(1-D)r_0^{(n)},\quad
r_j^{(n+1)}=(1-D)r_j^{(n)}+D r_{j-1}^{(n)}\ (1\le j\le M),\quad
T_{n+1}=T_n+D r_M^{(n)}.
\tag{20}
\]

Adding one independent Bernoulli(D) gives each identity; only a transition
from M to M+1 increases the tail. This is a proof of the recursion, not an
assumption that a numerically tiny tail is representable. At J=0 with M>=N,
all T_n are zero and (19) reduces exactly to p_N. An overflow observation in
that case comes entirely from the contamination channel.

## 7. Theorem: residual-only conditional initialization

Let a fixed method choose

\[
b_{\rm G+R}(x,a)=\widetilde h_\epsilon(J_0,C_0;x,a),\qquad
b_{\rm DIR}(x,a)=\widetilde h_\epsilon(0,0;x,a)=g_\epsilon(a\mid x),
\tag{21}
\]

where (J_0,C_0) are the remaining schedule clocks at reverse time zero.
For a measurable residual R_0(x,a) with -B<=R_0<=B<infinity, define

\[
q_b(dx)=\frac{\Pi_N(dx)b(x,a)}{\int b\,d\Pi_N},\qquad
q_{\rm init}(dx)
=\frac{\Pi_N(dx)b(x,a)e^{R_0(x,a)}}
       {\int b(x,a)e^{R_0(x,a)}\Pi_N(dx)}.
\tag{22}
\]

An iid proposal from q_b followed by acceptance probability
exp(R_0(x,a)-B) samples q_init on acceptance. Its single-trial acceptance
probability is a_b=e^(-B) E_qb[e^R0], lying in [exp(-2B),1].

**Proof.** Multiplying the proposal measure by its acceptance probability
gives q_b(dx)exp(R_0-B), proportional to the numerator of q_init. Normalizing
this measure proves the accepted law. The two-sided bound on R_0 gives the
acceptance bound. With ideal iid trials, probability of no acceptance in
T trials is (1-a_b)^T <=(1-exp(-2B))^T. Summing the geometric first-acceptance
probabilities also shows that the returned state, conditional on success
within T, has law q_init. QED.

This theorem concerns ideal proposal/acceptance draws. State-dependent
finite-arithmetic, metadata-size or work-limit refusals can introduce
additional failure events. Conditioning on their absence is not silently
certified to preserve (22); the program must report refusal rather than
substitute a fallback law.

**Why only the residual is rejected.** Sections 5–6 already sample the
analytic factor b. Rejecting again on b would incorrectly square it.
The BASE potential is absent because the candidate BASE simulation starts
from Pi_N, not from Pi_N exp(V_phi(0,.)); adding it would change that initial
law. An observation-only nuisance c(a,z) cancels from a normalized density
over x, so it is absent as well.

The implemented residual is a_R(0) times a bounded conditioner, with
a_R(0)=1 for the declared cubic gate. Throughout the clean hold the residual
gate and the remaining reference clocks are zero, so both analytic baselines
reduce to g_epsilon. That boundary identity does **not** prove cubic approach
of the desired residual to zero, nor exact representability of a learned
likelihood.

If b exp(R_0) happened to equal the conditional endpoint likelihood of the
chosen BASE process up to a state-independent factor, (22) would be that
process's exact conditional initial law. Neither logistic finite-sample
training nor this rejection proof establishes that premise or the law of
the subsequent approximate conditioned path.

## 8. A quantitative capped/uncapped reference distinction

Let P^N and P^infinity be the capped and uncapped reference laws on the
remaining interval, started at the same state x with |x|<=N. Let
h_N(x,a)=E_x^N[g_epsilon(a|X_terminal)] and
h_infinity(x,a)=tilde_h_epsilon(J,C;x,a).

Couple their immigration proposals, occurrence deaths and OU randomness
until the first immigrant proposal at a time when the capped state has
count N. Before that proposal the two processes coincide. Write q_x for
the probability of at least one such blocking proposal. Then

\[
\operatorname{TV}(P_x^N,P_x^\infty)\le q_x
\le\min\left\{1,\,
 \beta\int_{\rm interval}\gamma_J(t)
            \Pr_x^N\{|X_t|=N\}\,dt\right\}.
\tag{23}
\]

TV denotes sup_B |P(B)-Q(B)|. It is a path-law statement on the common
uncapped configuration path space, into which capped paths embed.

**Proof.** Use a rate beta gamma_J(t) Poisson process of proposed births
for the capped process, accepting only below N. This leaves its stated
generator unchanged. Mark its proposals with iid nu births; use the same
marks and the same per-occurrence clocks/noises for the uncapped process
until a blocked proposal. Thus disagreement requires a blocked proposal.
The probability of at least one is bounded by its expected count. Predictable
Poisson compensation gives the integral on the right of (23). Finite
integrated clocks make this expectation finite. The coupling inequality
then proves the TV claim. QED.

A simple bound not involving the boundary occupation is min(1,beta J).
For a more informative starting-state calculation, the capped count process
has the finite generator in integrated jump time

\[
Q_{n,n+1}=\beta\mathbf1_{\{n<N\}},\quad
Q_{n,n-1}=\delta n,\quad
Q_{n,n}=-\beta\mathbf1_{\{n<N\}}-\delta n.
\tag{24}
\]

Hence the occupation term is
beta integral_0^J [exp(tQ)]_(|x|,N) dt, independently of C and the marks.
This can be evaluated by finite linear algebra; it is a reference
calculation, not learned-sampler validation.

Averaging over the common initial prior Pi_N gives

\[
\bar q=\int q_x\Pi_N(dx)
\le\min\{1,\beta J p_N(N)\}.
\tag{25}
\]

Indeed Pi_N is invariant for the capped reference, so its boundary
probability at every time is p_N(N). For N=0 this gives min(1,beta J),
not a spurious zero defect: the uncapped process can still admit births.

For every fixed retained or overflow observation, (9) and the same coupling
give

\[
|h_N(x,a)-h_\infty(x,a)|
\le (1-\epsilon)B_a\,q_x.
\tag{26}
\]

To see this, the common epsilon term cancels, and the clean likelihood
lies in [0,B_a]. Its difference is zero on coupled equal endpoints and
has magnitude at most B_a otherwise. The bound is zero when J=0 even if
C>0, since only birth suppression distinguishes the two reference laws.

Finally define the two initial posteriors

\[
\pi_N^a(dx)=\Pi_N(dx)h_N(x,a)/m_N(a),\qquad
\tilde\pi_N^a(dx)=\Pi_N(dx)h_\infty(x,a)/\tilde m_N(a).
\]

Both evidences are at least epsilon. Integrating (26) and normalizing gives

\[
|m_N(a)-\tilde m_N(a)|\le(1-\epsilon)B_a\bar q,\qquad
\operatorname{TV}(\pi_N^a,\tilde\pi_N^a)
\le\min\left\{1,\frac{(1-\epsilon)B_a\bar q}{\epsilon}\right\}.
\tag{27}
\]

For completeness, for positive f,g and their prior integrals m_f,m_g,

\[
\frac12\int\left|\frac f{m_f}-\frac g{m_g}\right|d\Pi
\le\frac{\int|f-g|\,d\Pi}{m_f},
\]

by adding/subtracting g/m_f and using
|m_f-m_g|<=integral|f-g|. Apply f=h_N and m_f>=epsilon to obtain (27).

This is a rigorous but potentially **vacuous** bound. A rare observed key,
large magnitude, small epsilon or large boundary occupation can make its
right side one. It does not establish a useful approximation regime for
the real domains. Nor does it bound derivatives of h, learned-model error,
or numerical conditional-path error. Those require separate assumptions
and analysis.

As an independent check, capped stationarity implies the exact capped
reference evidence m_N(a) is independent of the remaining clocks. For
retained clean a it equals (15) evaluated with A=1, not generally (15)
at the positive remaining clocks. The latter is the evidence for a capped
initial prior propagated **uncapped**. This provides a concrete way to
detect accidental conflation of the two laws.

### 8.1 A hand-computable cap-defect example

Take a mathematical one-atom reference nu=delta_e, theta=delta=1, N=1,
M>=1, p=1/2 and J=log(2). Continuous clocks are irrelevant for this atomic
carrier. This is a diagnostic specialization of the theorem, not a replacement
for either full-support domain grammar. Then A=1/2, D=1/4 and K=1/4.
For one retained observed atom, the two **clean** guide values at current
counts zero and one are

\[
(h_\infty^{\rm clean}(0),h_\infty^{\rm clean}(1))
=e^{3/4}(1/4,7/16).
\]

The capped count generator is Q=[[-1,1],[1,-1]], with transition probability
P_(0,1)(J)=(1-exp(-2J))/2=3/8 and P_(1,1)(J)=5/8.
The terminal one-observation clean likelihood is e/2 when the terminal count
is one and zero otherwise. Thus

\[
(h_N^{\rm clean}(0),h_N^{\rm clean}(1))
=e(3/16,5/16).
\]

Since Pi_1 gives each initial count probability 1/2, the clean-observation
posterior probability of current count one is 7/11 under the uncapped-future
guide and 5/8 under the capped reference. These are different despite using
the same capped initial prior. For the actual positive-epsilon channel,
replace each clean value h by epsilon+(1-epsilon)h before normalizing; the
same distinction persists. This example does not set epsilon=0 in the model:
it displays its clean mixture component separately for transparent arithmetic.

## 9. Algorithm-to-proof crosswalk and remaining claims

The [independent continuous-fiber diagnostic](../docs/CONTINUOUS_FIBER_GUIDE_INITIALIZATION_DIAGNOSTIC.md)
now makes the cap distinction computable for an occurrence-attached OU submodel.
It derives the uncapped Bernoulli/Poisson likelihood without calling this guide,
normalizes both initial Gaussian-mixture laws under the same Pi_N, and computes
their mixed-state TV by one-dimensional quadrature. This is a known-initial-law
diagnostic, not an empirical terminal TV estimate or a general learned-law bound.

| Implementation | Mathematical statement | Qualification |
|---|---|---|
| FactorizedSmoothOracle._clocks | (2), survival/OU convolution | Finite-clock floating-point evaluation may refuse unrepresentable values. |
| clean_observation_log_density and FactorizedAssociationGuide.log_value | (5)–(7), per-key subset recursion | Exact finite polynomial in ideal arithmetic; bounded-size log-domain implementation. |
| Guide coordinate autograd | (10) | Atomic fibers are excluded; finite derivative tests do not establish global floating-point error bounds. |
| upper_log_bound | (8)–(9) | Fixed-observation envelope, not a uniform observation-space certificate. |
| sample_reference_posterior, retained branch | (14)–(18), Gaussian marks (12) | Conditions the total count once; copies selected anchor keys without prior-key rejection. |
| _overflow_count_logs | (19)–(20) | Mark law remains nu because only counts are conditioned. |
| conditional_initializer | (21)–(22) | G+R uses remaining clocks; DIR uses zero clocks; rejection is residual-only. |
| ExactFactorizedReference.sample_forward | Capped generator and (24) | Different from the propagated independent-reference guide. |
| LearnedFactorizedSampler | Approximate tilted learned path | Not certified by this appendix; the initializer theorem alone is insufficient. |

The source files are
[association guide](../src/heterodiff/theory/factorized_association_guide_torch.py),
[smooth oracle](../src/heterodiff/theory/factorized_smooth_amendment.py),
[hybrid sampler](../src/heterodiff/processes/factorized_hybrid_sampler.py),
[conditional learner](../src/heterodiff/experiments/factorized_conditional_training.py)
and [device learner](../src/heterodiff/experiments/factorized_device_training.py).
The historical mathematical amendment's statement that the retained posterior
was "not implemented" describes its earlier state; the construction now
exists in the guide module. Its historical text need not be silently
reinterpreted to claim the implementation existed at that date.

**Completed here:** occurrence-level normalized association formula; exact
retained/empty/overflow reference posterior; correct total-count conditioning;
residual-only initializer law; a quantitative capped-reference defect bound.

**Not completed by these results:** global learned posterior recovery;
uniform-in-observation guarantees; score/gradient approximation from logistic
risk; cubic-gated realizability; finite-RNG exactness; general large-cap
computational efficiency; real-data scientific superiority. The retired C17
path theorem remains retired.
