# Mixed neural conditional learner: opt-in common-path contract v3

Date: 2026-09-13

Status: selected opt-in successor for local implementation and known-law
validation. This is a scientific model/algorithm contract, not a claim of
posterior recovery, scientific convergence, production readiness or GPU speedup.

The [finite-grid contract v2](hybrid_diffusion_conditional_law_contract_v2.md)
resolved the target, classifier and normalized-twist definitions for an
enumerable atomic experiment. This v3 carries the common-path and linear-gate
choices into the actual mixed-domain neural learner, while preserving the
distinction between that learner's numerical population and its approximate
conditional sampler. It does **not** transfer the finite-state exact transition
formula to a hybrid kernel whose transition density is unavailable.

## 1. Selected change and compatibility boundary

The successor is opt-in through
[factorized_common_grid_pipeline.py](../src/heterodiff/experiments/factorized_common_grid_pipeline.py):

- CommonGridDeviceFactorizedBasePopulation freezes one BASE, reference,
  context and trajectory grid.
- common_grid_train_conditional_step trains the existing mixed neural
  conditioner on paired observations from that common trajectory construction.
- common_grid_sample_conditional uses the selected linear residual gate,
  analytic reference-posterior initializer and existing hybrid numerical sampler.

The existing CPU conditional model gains the explicit policy
LINEAR_ACTIVE_TIME_V1; LEGACY_CUBIC_V1 remains its default.
DeviceFactorizedConditionalModel.from_cpu copies the selected policy.
Frozen physical snapshots retain that policy. Existing legacy population and
training entrypoints retain their query-refinement and continuous-time sampling
conventions; they are not silently redirected into the successor.

Tensor shapes, parameter names and ordinary legacy state-dictionary keys need
not change merely to select a different scalar gate. This makes explicit
weight transfer possible, but does not make the two models equivalent.
The gate is scientific metadata, not a trainable tensor: copying old weights
into a linear-gated constructor is an acknowledged warm start whose physical
function changes away from the gate endpoints.

Legacy checkpoint checks must not label such a linear-gated object as a
legacy checkpoint. The successor exposes a snapshot binding with its grid,
time measure, BASE identity and numerical policies. That record is useful for
reproducibility; it is **not** a completed resumable successor-checkpoint format.
No historical CPU/GPU receipt or installed release is reclassified by this
contract.

## 2. One numerical BASE path law

Fix a task/static context z, mixed configuration carrier Gamma_N, reference
Pi_N, reference observation channel K_epsilon, frozen neural BASE parameters
phi and an explicit grid

\[
0=u_0<u_1<\cdots<u_L=S.
\]

Let H=S-s_hold>0 be the beginning of the terminal clean hold; H must be a
grid point. The existing sampler evolves active intervals before H and
copies the state on held intervals at or after H.

The idealized numerical construction with this frozen grid, coefficients and
random-draw laws defines a single BASE path law P_phi^Delta. Its initial law
is Pi_N, not Pi_N tilted by the BASE energy. In the implementation, the
constructor uses DeviceFactorizedPhysicalPotential with
BASE_GRAPH_FP64_SHARED_V1: BASE activations, coordinate derivatives and shared
gradient accumulation use the selected FP64 policy, while the existing
parameter/input-encoding conventions remain as specified by that policy.
The conditional neural graph is not thereby promoted to entirely FP64.

Every queried training state is selected from a completed path on this same
grid. A query time must already be an admitted grid node. It does not cause
time insertion, trajectory refinement, partial re-simulation or interpolation
of a training state.

For an identical run seed and record identifier, queries at different admitted
nodes reconstruct the same two complete BASE paths and the same endpoint
observations; only the selected state index changes. Query time is absent
from their path/observation random-stream identities. Distinct trajectory
branches have independently keyed streams. Deterministic replay is a useful
implementation check, not a proof that finite pseudorandom numbers are ideal
independent draws.

Changing BASE weights, reference, context, grid or the bound numerical policy
creates a different declared population. The sampler can check an explicitly
supplied expected_population_law_id before drawing; when omitted, the returned
binding documents the selected population but does not establish equivalence
to some earlier training run.

### 2.1 Refusals are not silently normalized away

The formal path law presumes the declared transitions and random draws can be
completed. Actual code has numerical and work-limit refusals. It must stop and
report a refusal, not redraw a difficult path, truncate the scientific cap,
replace a tail event, or count an incomplete path as a successful observation.

Conditioning on completion of a state-dependent resource-limited computation
is not automatically the same statistical law as the unrestricted numerical
construction. This contract does not assert otherwise. A failed bounded run
is failed evidence, not a hidden change to the model's support or an accepted
sample from a fallback law.

## 3. The selected training-time measure

The admitted time set is the active **left macro-grid** roster

\[
I_\Delta=\{u_i:u_i<H\},\qquad q_\Delta(u_i)=1/|I_\Delta|.
\tag{1}
\]

It includes reverse time zero, so the conditional likelihood used by the
initializer is trained rather than left entirely to temporal extrapolation.
It excludes H, later held nodes and S: in the hold the state no longer evolves,
the analytic likelihood is the terminal observation likelihood, and the
selected residual is zero.

Equation (1) is uniform over a finite list of nodes. It is not uniform in
continuous physical time and is not a duration-weighted quadrature rule on a
nonuniform grid. Refining the grid changes both the numerical population and
this explicitly declared training measure; that is a new experiment.

A default training update samples a node from (1) independently of its two
trajectory branches. Unit class-conditional sampling weights are then correct
for the declared population risk. An explicitly supplied admitted time selects
a separate fixed-node diagnostic, not an alternative implementation of the
full q_Delta objective.

For each row, generate two complete independent BASE paths X^(1),X^(2) and
their observations A^(1),A^(2) from K_epsilon at time S. At U~q_Delta form

\[
(U,X_U^{(1)},A^{(1)})\quad\text{and}\quad
(U,X_U^{(1)},A^{(2)}).
\tag{2}
\]

Whole observations, including duplicate occurrences, empty observations and
overflow, are replaced in the product example. Static context remains fixed.

Let g(a|x) be the general model's lambda-density observation likelihood.
Define

\[
h_i^\Delta(x,a)=\mathbb E_{P_\phi^\Delta}
 [g(a|X_S)\mid X_{u_i}=x,z],\qquad
m^\Delta(a)=\mathbb E_{P_\phi^\Delta}[g(a|X_S)\mid z].
\tag{3}
\]

Because all times belong to one endpoint experiment, m^Delta does not depend
on i. Balanced joint/product logistic classification therefore has the Bayes
logit

\[
\ell_i^*(x,a)=\log h_i^\Delta(x,a)-\log m^\Delta(a)
\tag{4}
\]

on the paired population's support. The observation-only nuisance can represent
the same normalizing offset at every training node. Its value and a
state-independent component of the residual are not separately identified
just by their sum.

The actual update is a finite Monte Carlo gradient step on this declared risk,
unlike the finite atomic benchmark's full-population sums. Finite samples,
restricted representation and finite optimization remain sources of error.

## 4. Linear remaining-active-time residual

For u in [0,S], define

\[
a_{\rm lin}(u)=\frac{\max(S-u-s_{\rm hold},0)}{S-s_{\rm hold}}
             =\frac{\max(H-u,0)}H.
\tag{5}
\]

The successor's physical likelihood approximation is

\[
\begin{aligned}
\log\widehat h_{\rm G+R}(u,x,a)
 &=\log\widetilde h_{\rm uncapped}(J(u),C(u);x,a)
   +a_{\rm lin}(u)R_\theta(u,x,a),\\
\log\widehat h_{\rm DIR}(u,x,a)
 &=\log g(a|x)+a_{\rm lin}(u)R_\theta(u,x,a).
\end{aligned}
\tag{6}
\]

Both retain the same bounded mixed neural conditioner, event/observation
encoders and observation-only nuisance structure. The classifier is
log hat_h+c_eta(a,z); the physical potential excludes c_eta.

The gate is evaluated once using the declared binary64 physical time, not an
independent rounded neural-time surrogate. At u=0 it equals one; at and
throughout the hold it is zero. The analytic G+R clocks also vanish in the
hold, so both physical likelihoods reduce to g there.

Contract v2 exhibits a finite-generator counterexample in which the required
log-likelihood correction is O(H-u), not O((H-u)^3). Equation (5) removes
that generic cubic representability obstruction. It does not prove that the
fixed conditioner bound, feature representation or optimizer recovers the
needed correction on this countable/unbounded mixed carrier. In particular,
the finite-generator quotient bound in v2 is not a global theorem for every
reference key and continuous coordinate.

This changes the model's hypothesis class prospectively. It is not merely
a floating-point stabilization or a reinterpretation of a legacy trained model.

## 5. The actual conditional sampler remains approximate

The physical potential is

\[
V_\phi(S-u,x,z)+\log\widehat h_\theta(u,x,a,z),
\tag{7}
\]

with the existing hold extension for the BASE. The initial proposal is the
analytic capped-initial-prior reference posterior, with remaining clocks for
G+R and zero clocks for DIR. Bounded residual-only rejection gives

\[
\widehat\pi_0(dx)\propto\Pi_N(dx)\widehat h_\theta(0,x,a).
\tag{8}
\]

The [initializer appendix](hybrid_diffusion_association_initializer_proof_v1.md)
proves that ideal proposal/acceptance law. The BASE potential and nuisance
are not inserted into (8).

Subsequent transitions are still those of LearnedFactorizedSampler:
Strang-style continuous/jump/continuous splitting, additive-noise Heun
coordinate updates, and midpoint-frozen tilted jump rates. The code does not
evaluate the numerical BASE transition density K_i^Delta or normalize
K_i^Delta(x,dy)hat_h_{i+1}(y) into an exact discrete transition row.

Consequently even exact values of h_i^Delta at training nodes would not by
themselves make (7)'s numerical transitions the conditioned numerical law.
The finite atomic benchmark's exact Doob identity and normalized-row
implementation must not be assigned to this sampler.

### 5.1 Off-training stage evaluations

Training observations occur at macro-grid nodes. The real sampler also asks
the physical potential for values and coordinate derivatives at Heun stages
and jump midpoints. The neural time representation supplies values between
training nodes, but that interpolation is not independently qualified by
the finite-node classification objective.

At a splitting midpoint, the state before the jump substep and the state
after it are distinct algorithmic stages. They should not both be called a
sample from the same physical-time state distribution without an explicit
augmented-stage law. Repeatedly adding midpoints to the macro grid changes
the algorithm and generates new stage midpoints; it does not automatically
remove this issue.

Reported scope therefore retains both
continuous_time_conditional_recovery_claimed=False and
exact_numerical_doob_transform_claimed=False, with stage-time interpolation
separately unqualified. These are descriptions of the scientific approximation,
not new administrative steps.

## 6. Independent continuous-fiber validation model

The next known-law validation uses an actual continuous event coordinate,
not a scalar added independently to a counting process. It fixes a selected
continuous complete key d_* with reference mass rho=nu{key=d_*}, keeps the
original full-support reference on all keys, and takes scientific count cap
N=1. For the reference/zero-BASE process, the count/key state can be lumped into

\[
E=\text{empty},\qquad C=\text{one event with key }d_*,
\qquad O=\text{one event with any other key}.
\]

The independent implementation is
[continuous_fiber_conditional_benchmark.py](../src/heterodiff/evaluation/continuous_fiber_conditional_benchmark.py).
Its array order is EMPTY,OTHER,CONTINUOUS (E,O,C); the matrix displayed below
uses the explicitly labeled order E,C,O. Implementations must map by those
labels rather than copy the displayed entries into a different array order.
This is not the older Cartesian counting-process-times-OU diagnostic.

With effective active death rate delta, birth rate beta=theta delta, and
row order E,C,O, the finite generator is

\[
Q=
\begin{pmatrix}
-\beta&\beta\rho&\beta(1-\rho)\\
\delta&-\delta&0\\
\delta&0&-\delta
\end{pmatrix}.
\tag{9}
\]

This lumping is valid because reference births use fixed key probabilities,
deaths are per-occurrence with key-independent rate, and OU evolution never
changes keys. It need not remain valid for a nonzero learned BASE that gives
different rates to different keys or coordinates.

Each continuous reference fiber follows

\[
dZ=-\tfrac c2Z\,dt+\sqrt c\,dW,
\tag{10}
\]

matching the sampler's continuous_rate convention. Thus contraction over
active duration tau is a=exp(-c tau/2) and conditional variance is 1-a^2.
A birth has a standard-normal continuous coordinate. Reference stationarity
means its coordinate remains standard normal at every later time if its
ancestry has been reset by a birth.

The selected control uses theta=0.8, delta=c=1, count cap one, clean observation
noise sigma=0.5 and whole-observation contamination epsilon=0.1. The actual
rho is obtained from the constructed full-support reference and reported,
not rounded to an assumed value such as 0.75. Horizon, hold, grids,
observation coordinate and sample/update counts belong in each diagnostic's
explicit run specification.

### 6.1 A closed-form propagated retained-observation likelihood

Take an observation consisting of one key d_* occurrence and coordinate y, with M=1.
Its reference lambda has Lebesgue density

\[
\lambda_y=e^{-1}\rho\phi_1(y).
\]

The clean channel still adds independent N(0,sigma^2) observation noise.
Only the **contamination** branch draws directly from lambda; it is not
passed through the clean observation-noise channel a second time.

Let P(tau)=exp(tau Q), s=exp(-delta tau),
v=sigma^2+1-a^2, and F(y)=phi_sqrt(1+sigma^2)(y).
For an initial C event with coordinate z, the absolute observation density is

\[
h_{\rm abs}(\tau,C,z;y)
=\epsilon\lambda_y+(1-\epsilon)p
 \left[s\,\phi_{\sqrt v}(y-az)
       +(P_{CC}(\tau)-s)F(y)\right],\qquad p=1/2.
\tag{11}
\]

For x=E,O,

\[
h_{\rm abs}(\tau,x;y)
=\epsilon\lambda_y+(1-\epsilon)p P_{xC}(\tau)F(y).
\tag{12}
\]

**Proof.** Starting in C, the original occurrence survives throughout with
probability s. On this event its coordinate evolves from z by (10), and
observation noise gives the first Gaussian in (11). On paths ending in C
after the original occurrence has died, a new C birth supplies a stationary
Gaussian mark; their total probability is P_CC-s. Initial E/O can end in C
only after such a birth. Multiplying by detection probability p and adding
the whole-observation contamination proves (11)–(12). QED.

A numerically stable implementation may compute the nonnegative reset mass
P_CC-s using a finite CTMC augmented with the original-ancestry indicator,
rather than subtract two close positive numbers. That is an independent
evaluation of the same probability experiment.

The neural guide convention is the lambda-density h_RN=h_abs/lambda_y.
At fixed y, this conversion changes log h by a state/time-independent constant:
normalized conditional laws, score derivatives and jump likelihood ratios
are unchanged. The convention must still be explicit when comparing guide
values, classifier logits, normalization constants or physical upper bounds.

### 6.2 Coordinate derivatives and an independently normalized target

Write (11) as A+B G(z), where A>=epsilon lambda_y, B=(1-epsilon)p s,
G(z)=phi_sqrt(v)(y-az), w=B G/(A+B G), and k=a(y-az)/v.
Then

\[
\partial_z\log h=w k,\qquad
\partial_z^2\log h=-w a^2/v+w(1-w)k^2.
\tag{13}
\]

These derivatives can be checked by differentiating the finite Gaussian
mixture, independently of neural autograd and the association implementation.
On O the likelihood is coordinate-independent; a continuous OTHER event has
a zero derivative in its actual one-dimensional fiber, while an atomic OTHER
event has no derivative coordinate.

For the selected stationary prior,

\[
\pi_E=\frac1{1+\theta},\quad
\pi_C=\frac{\theta\rho}{1+\theta},\quad
\pi_O=\frac{\theta(1-\rho)}{1+\theta},
\]

with standard-normal continuous coordinates. Its endpoint evidence is

\[
m_{\rm abs}(y)=\epsilon\lambda_y+
 (1-\epsilon)p\pi_C F(y).
\tag{14}
\]

The endpoint posterior is obtained by multiplying each prior component by
the terminal likelihood and normalizing by (14). The initial conditional
posterior similarly multiplies by (11)–(12). Its C-coordinate part is a finite
mixture of the prior N(0,1) and

\[
N\!\left(\frac{ay}{1+\sigma^2},
         1-\frac{a^2}{1+\sigma^2}\right),
\tag{15}
\]

because completing the square in phi_1(z)phi_sqrt(v)(y-az) gives (15) and
normalizer F(y). Thus independent normalization, exact moments and direct
sampling of the oracle's initial and endpoint conditional laws are possible
without the learned sampler.

O is an aggregate for calculation, not an invented replacement event.
When materializing an O draw for the actual sampler, draw the original key
and its correct fiber from the reference restricted to key!=d_*.
Collapsing every OTHER event into one artificial atomic key would validate a
different carrier. Empty and overflow observation cases likewise retain their
actual channel meanings; in the N=1,M=1 capped process clean overflow is
impossible, so overflow arises only from the contamination component.

## 7. What the separate validation controls measure

The controls must not conflate the following laws:

| Object | Meaning |
|---|---|
| P_ref | Exact continuous-time capped reference/zero-BASE process of (9)–(10). |
| P_0^Delta | Actual common-grid zero-neural-BASE numerical population; Heun OU updates generally differ from exact OU. |
| h_ref | Independent analytic likelihood (11)–(12) for P_ref. |
| h_0^Delta | Bayes likelihood of P_0^Delta; not automatically equal to h_ref. |
| hat_h_theta | Learned G+R or DIR approximation from common-grid neural training pairs. |
| hat_P_theta^Delta | Actual coefficient-tilted hybrid conditional sampler with its declared initializer. |

An **oracle-likelihood physical control**, initialized from the oracle's exact
conditional initial law, uses h_ref and its analytic derivatives in the real
sampler. Its departure from the independent conditional endpoint target
measures numerical coefficient/splitting error and finite-sampling uncertainty
without a learned residual or approximate guide initializer.

An **actual neural conditional control** freezes a shared zero BASE, trains
G+R and DIR under the common-grid construction, and uses their actual analytic
guide/residual initialization and physical sampling. Its departure from the
independent continuous reference posterior combines BASE discretization,
likelihood-estimation error, initializer error, off-grid interpolation and
conditional numerical-sampler error. It must not be attributed solely to
conditional learning or solely to the guide.

Even at zero BASE, the actual OU step is Heun rather than exact exponential
OU propagation. Therefore the independent continuous posterior is not silently
declared the exact Bayes target of the neural training population.
A derivation of the complete numerical hybrid kernel would be a further result.

A **small end-to-end optimizer smoke test** may update BASE as well as the
conditioner to verify connection of real modules. Once the BASE has changed,
(9)–(15) generally no longer describe its posterior. Such a test establishes
execution and bounded numerical behavior, not known-law posterior recovery.

Grid comparisons should keep the declared continuous target fixed, report
initializer choice and sample counts, and distinguish sampling variability
from discretization trends. No monotone grid improvement, method superiority,
or statistical confidence is inferred from a single small draw.

## 8. What this successor completes

The [multi-seed follow-up protocol](../docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md)
adds exact-h/exact-initial, exact-h/guide-initial, guide-only and zero-clock
controls on one grid. Its [independent initialization derivation](../docs/CONTINUOUS_FIBER_GUIDE_INITIALIZATION_DIAGNOSTIC.md)
quantifies one of Section 7's approximation sources without fitting a neural
model. Differences between those numerical control laws are not added as though
they formed an exact decomposition of terminal TV. The separately reported
finite-indicator uncertainty is conditional on the fitted seed roster.

The implementation step can complete common-path pairing, an explicit
discrete training-time measure including initialization, a copied/bound linear
gate, compatibility checks against legacy checkpoint interpretation, and a
bounded local connection to the real mixed neural model and sampler.

The independent occurrence-attached continuous oracle adds a testable
conditional target and analytic score control beyond the purely atomic
benchmark. Successful checks remain local evidence; the approximation
questions in Section 7 must remain visible in reporting.

Full neural convergence, conditional posterior recovery on real domains,
global Sobolev control from logistic risk, a resumable successor release,
production/GPU qualification and a paper-level empirical superiority claim
are not supplied by this contract. The retired C17 theorem remains retired.
