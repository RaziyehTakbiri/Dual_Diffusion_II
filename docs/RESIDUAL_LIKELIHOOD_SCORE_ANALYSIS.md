# Residual likelihood and score: target, gauge and capacity analysis

Date: 2026-09-13. Status: local mathematical diagnosis, not a model amendment.
No optimizer update, endpoint sampling, model change or real-data access was
performed for this analysis. Existing experiment records and acceptance rules
are unchanged. Numerical evaluations below use the independently derived
cap-one reference formulas; they are not interval-certified arithmetic.

The main finding is a concrete representational limitation: the current
benchmark residual has amplitude at most `0.25*(1-u)`. That bound is too small
to represent the exact capped-reference likelihood correction, even after
allowing an arbitrary observation-only normalization. Linear rather than cubic
decay fixes the generic order of vanishing, but does not establish a sufficient
coefficient. This does not by itself attribute observed endpoint errors to one
cause, or identify the exact numerical-grid training target with the reference
target.

## 1. What the classifier is learning

Fix static context z and the frozen common-grid BASE path law P^Delta. Let
U be uniform on the eight admitted nodes 0,1/8,...,7/8. For a complete endpoint
observation A, let g^lambda(a|x) denote its density relative to the project's
observation reference measure lambda, including the empty and overflow atoms.
Define

\[
h_i^\Delta(x,a)=E_{P^\Delta}[g^\lambda(a|X_1)\mid X_{u_i}=x,z],\qquad
m^\Delta(a)=E_{P^\Delta}[g^\lambda(a|X_1)\mid z].
\]

The joint example is (U,X_U^(1),A^(1)); its product counterpart is
(U,X_U^(1),A^(2)) from an independent complete second path. Both therefore
have the same time and state marginal. Their density ratio is h_i^Delta/m^Delta.
Sharing the first state between the two examples changes the covariance of a
Monte Carlo gradient, not this population density ratio.

With balanced classes and the actual unit weights, the implemented risk is

\[
R(f)=\tfrac12 E_J\log(1+e^{-f})+\tfrac12 E_P\log(1+e^f).
\]

At a point with joint/product densities j,p>0, differentiating gives the
unique optimal logit f*=log(j/p). Thus

\[
f_i^*(x,a)=\log h_i^\Delta(x,a)-\log m^\Delta(a). \tag{1}
\]

The marginal m^Delta is independent of i because every node belongs to the
same endpoint experiment. The observation-only nuisance is therefore the
right kind of function for this normalizer. This argument relies on the
common-grid construction, not on the former query-refined population.

Equation (1) is the target of the population objective, not a claim that
32 stochastic updates recover it. The actual experiment uses 64 joint/product
pairs per fitted model, covers all generated observation forms, and evaluates
a particular selected-key observation afterward. It does not train only at
that fixed observation.

Source crosswalk: `CommonGridDeviceFactorizedBasePopulation.sample_pair` and
`common_grid_train_conditional_step` in
[the common-grid implementation](../src/heterodiff/experiments/factorized_common_grid_pipeline.py);
`DeviceFactorizedConditionalModel.paired_loss` in
[the device learner](../src/heterodiff/experiments/factorized_device_training.py).

## 2. G+R, DIR and the nuisance normalization

Write the physical log-likelihood approximation as b_m+r_m and the classifier
as f_m=b_m+r_m+n_eta(a,z). The baselines are

\[
b_{\rm G+R}=\log\widetilde h_{\rm uncapped}^\lambda(u,x,a),\qquad
b_{\rm DIR}=\log g^\lambda(a|x). \tag{2}
\]

G+R uses the remaining jump/continuous clocks. DIR uses the same association
implementation at zero clocks: it is an observation-likelihood baseline, not
an initially zero physical potential. Both methods aim at the same target.

For either baseline define the canonical grid residual

\[
d_{m,i}^\Delta(x,a)=\log h_i^\Delta(x,a)-b_m(u_i,x,a).
\]

In an unrestricted class, r=d^Delta+c(a,z),
n=-log(m^Delta)-c(a,z) yields the same Bayes logit. This observation-only
gauge cancels from coordinate derivatives, jump-rate ratios and normalized
initial laws. The code correctly excludes the nuisance from the physical
potential and from residual-only initialization rejection.

Consequently, comparing a raw classifier logit directly with log h is wrong.
Comparing residual values in an arbitrarily selected gauge can also be wrong.
The diagnostically distinct quantities are:

| Quantity | Correct comparison |
| --- | --- |
| Classifier calibration | b+r+n against log h_grid-log m_grid |
| State-relative physical potential | differences of b+r between two states against differences of log h |
| Likelihood score on a selected continuous fiber | state-coordinate derivative of b+r against derivative of log h |
| Nuisance in the canonical gauge | n against -log m_grid, explicitly noting gauge non-identifiability |
| Reference/algorithm discrepancy | h_grid and its derivatives against h_capped, before discussing learning error |

The independent continuous-fiber modules return raw observation densities
relative to coordinate Lebesgue measure. For the selected singleton a=(d*,y),
the project's reference density is

\[
\lambda(a)=e^{-1}\rho\varphi_1(y),\qquad
\rho=393217/524288=0.7500019073486328,
\]

where varphi_v is the centered normal density of variance v. Converting raw
h to the project's convention subtracts log lambda(a). In (1) the factor
cancels between h and m; it also cancels from residual differences and state
derivatives. In raw-density notation the canonical nuisance is
log lambda(a)-log m_raw(a), not simply -log m_raw(a).

At the terminal node both baselines equal g and the residual is zero. If the
Bayes equality is required continuously up to that node, this fixes the
canonical gauge c=0. The actual finite training roster excludes the terminal
node, so it does not itself identify that boundary normalization. Allowing a
separate c(u,a) is physically harmless for likelihood ratios, but it is a
larger gauge freedom than the implemented observation-only nuisance offers.

## 3. A gauge-independent amplitude obstruction

The fixture in [the original benchmark](../src/heterodiff/experiments/mixed_continuous_conditional_benchmark.py)
sets `value_bound=0.25`, horizon=1 and clean hold=0. The shared conditioner
returns B*tanh(raw/B), and the linear gate is applied exactly once. Therefore
for every parameter setting and permitted state/observation,

\[
|r_m(u,x,a)|\le B(1-u),\qquad B=1/4. \tag{3}
\]

This bound follows from the forward expression, not from a numerical estimate
of trained weights. In particular,

\[
|r_m(u,x,a)-r_m(u,x',a)|\le 2B(1-u). \tag{4}
\]

**Finite-query obstruction.** Fix u,a and a finite state set S. Let d(x) be
the desired residual correction in any fixed gauge, and let
osc_S(d)=max_S d-min_S d. For every candidate satisfying (3), even after the
best state-independent shift c,

\[
\inf_c\max_{x\in S}|r(x)-d(x)-c|
\ge \tfrac12[\operatorname{osc}_S(d)-2B(1-u)]_+. \tag{5}
\]

Proof: choose states achieving the two extrema of d. Their candidate
contrast has magnitude at most 2B(1-u). The difference of the two errors
therefore has magnitude at least osc_S(d)-2B(1-u). At least one error has
half that magnitude. The constant c cancels. This proof even permits a
different optimal gauge at every time, so an observation-only nuisance cannot
evade it.

For a common observation-only gauge across several times, a further necessary
condition is that the intervals

\[
[-B(1-u)-d(u,x),\ B(1-u)-d(u,x)]
\]

have a nonempty intersection over all queried states and times. Neither this
condition nor (4) is sufficient for representation by the particular neural
network. They are necessary capacity checks only.

### 3.1 Finite-query evaluations for the exact capped reference

Here the desired corrections are
d_GR=log h_capped-log h_uncapped and d_DIR=log h_capped-log g.
The query set is EMPTY, OTHER and one selected-key occurrence with coordinate
x=-3+0.3k, k=0,...,20. The following values come only from the independent
capped and uncapped formulas; there are no fitted weights or samples in them.
This 21-coordinate analytic witness roster is separate from the five-coordinate
neural-probe roster fixed in [the diagnostic protocol](RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md).
Neither roster is substituted for the other. The last two columns are (5), in
log-likelihood units.

| Scenario (theta,y) | u | Allowed contrast | Required G+R contrast | Required DIR contrast | G+R error lower bound | DIR error lower bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| (0.8,0.7) | 0 | 0.50000 | 0.47393 | 3.43231 | 0 | 1.46616 |
| (0.8,0.7) | 0.5 | 0.25000 | 0.64984 | 2.76061 | 0.19992 | 1.25530 |
| (0.8,0.7) | 0.875 | 0.06250 | 0.42076 | 1.19343 | 0.17913 | 0.56547 |
| (2.5,1.4) | 0 | 0.50000 | 0.74837 | 4.09046 | 0.12418 | 1.79523 |
| (2.5,1.4) | 0.5 | 0.25000 | 1.05259 | 3.53103 | 0.40130 | 1.64051 |
| (2.5,1.4) | 0.875 | 0.06250 | 0.97847 | 1.80465 | 0.45798 | 0.87107 |

Across all eight active nodes, G+R violates (4) at seven nodes in the first
scenario and every node in the second. DIR violates it at every node in both.
This finite set supplies witnesses, not an estimated global maximum or an
endpoint discrepancy bound. To represent even these finite contrasts, B would
have to be at least 1.68304/3.91387 for G+R in the two scenarios, and
4.77373/7.21858 for DIR, permitting a separate best gauge at each time. These
are necessary lower bounds, not proposed replacement hyperparameters.

### 3.2 Exact near-terminal witness on a jump-connected state pair

Set tau=1-u and fix the rates, noise and contamination used in the benchmark.
Let

\[
c=0.1e^{-1}\rho\varphi_1(y),\qquad
\kappa=\frac{0.9\theta\rho}{4}\varphi_{1.25}(y).
\]

Starting empty, a selected-key birth followed by retention has first-order
likelihood 2*kappa*tau, under both capped and uncapped reference processes.
Starting with OTHER under cap one, the old occurrence must first die before
a selected-key birth, so the clean selected-observation contribution is
O(tau^2). Under uncapped propagation, an immigrant can arrive immediately;
the old OTHER occurrence must additionally fail to be retained. Its retention
failure has leading probability 1/2, leaving kappa*tau. Thus

\[
\begin{array}{ll}
h_{\rm capped}(E)=c+2\kappa\tau+O(\tau^2),&
\widetilde h_{\rm uncapped}(E)=c+2\kappa\tau+O(\tau^2),\\
h_{\rm capped}(O)=c+O(\tau^2),&
\widetilde h_{\rm uncapped}(O)=c+\kappa\tau+O(\tau^2).
\end{array}
\]

Since g(E)=g(O)=c, taking logarithms proves

\[
d_{\rm GR}(O)-d_{\rm GR}(E)=-\frac\kappa c\tau+O(\tau^2),\qquad
d_{\rm DIR}(E)-d_{\rm DIR}(O)=\frac{2\kappa}c\tau+O(\tau^2). \tag{6}
\]

The coefficient kappa/c equals
2.25*e*theta/sqrt(1.25)*exp(0.1*y^2): 4.59613 in the first scenario and
16.63733 in the second. The allowed coefficient in (4) is only 0.5.
Consequently no parameter choice in the current amplitude-bounded class can
represent the exact reference correction for all times sufficiently near the
terminal boundary. This witness uses a pair connected by the death/birth
mechanism and is independent of observation normalization. It also explains
why correcting cubic to linear decay did not alone establish realizability.
The finite numerical-grid target must still be evaluated on its actual nodes;
(6) is not silently transferred to that target.

## 4. Why low paired loss need not mean a good conditional score

For the unrestricted classifier, let M=(J+P)/2 and eta=j/(j+p). Directly
expanding the cross entropy gives

\[
R(f)-R(f^*)=E_M\operatorname{KL}
 (\operatorname{Bern}(\eta)\Vert\operatorname{Bern}(\sigma(f))). \tag{7}
\]

This controls an average classification-probability error, not a state
derivative. Uniformly small logit perturbations can have large derivatives:
for example epsilon*tanh(k*x) has amplitude at most epsilon but derivative
epsilon*k at zero. The absence of a derivative consequence is mathematical;
no claim that this particular experiment realizes that example is needed.
The model has no certified parameter-norm or derivative bound closing this
gap. Its amplitude cap alone cannot provide one.

Moreover, nuisance calibration can lower (7) without changing any physical
score or jump ratio. Errors at rare observations or states can contribute
little to an average validation loss. Coverage will be measured from the actual
64 training pairs and 32 held-out pairs per fit, using the unchanged sampler
and the fixed y +/- 0.5 interval (one observation-noise standard deviation)
declared in [the diagnostic protocol](RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md).
That descriptive tally must not be replaced by an exact-reference expectation
or by a differently selected proximity window. The fixed observation y itself
has zero mass in a continuous channel.

The observation encoder processes every byte but is a learned compressed,
non-injective representation. The atan-based coordinate encoding approaches
its tail limits, and the output tanh plus gate can attenuate learning
gradients. These are plausible additional approximation/optimization issues,
not measured causes of the reported residual gap. Parameter counts alone do
not establish approximation quality over all keys and continuous fibers.

An important negative control is OTHER. In this exact cap-one selected-key
experiment, the target likelihood is constant in an OTHER event's coordinate,
even if that OTHER event has a continuous fiber. Its likelihood score is
therefore zero. A learned nonzero OTHER score is spurious for this target.
The nuisance's derivative with respect to the latent state is zero; gradients
with respect to the observation coordinate are a different quantity.

Finally, the likelihood score is not the full marginal posterior score:
the latter adds the unconditional marginal score. The sampler uses reference
drift -x/2 plus the likelihood-potential gradient in this zero-BASE experiment.
Coordinate score errors and state log-potential contrasts are relevant to its
local drift and jump rates, but are not by themselves an endpoint-error bound.

## 5. Separate the exact reference and numerical training laws

Zero BASE does not eliminate Heun discretization. With a half-step length
h=1/16 and unit OU rate, the actual Heun update in exact real arithmetic is

\[
x' = A x+\sqrt Q Z,\quad
A=1-h/2+h^2/8=0.96923828125,\quad
Q=h(1-h/4)^2=0.0605621337890625. \tag{8}
\]

This differs from the exact OU kernel. Its standalone stationary variance
Q/(1-A^2)=0.9997520456 is not one. Therefore the continuous-time reference
evidence is not automatically the numerical-grid evidence, despite a
stationary reference initial law and unchanged category dynamics.

For this zero-BASE cap-one experiment, an independent numerical-grid target
can be calculated without endpoint simulation. Let P=exp(Delta*Q_cat),
Delta=1/8, S=exp(-Delta) and T f(x)=E[f(A*x+sqrt(Q)*Z)]. For backward
likelihood components h_i(E), h_i(O), h_i(C,x), define

\[
B_i=E_{Z\sim N(0,1)}[(T h_{i+1}(C,\cdot))(Z)].
\]

The exact ideal numerical-kernel recursion is

\[
\begin{aligned}
h_i(s)&=P_{sE}h_{i+1}(E)+P_{sO}h_{i+1}(O)+P_{sC}B_i,
&&s\in\{E,O\},\\
h_i(C,x)&=P_{CE}h_{i+1}(E)+P_{CO}h_{i+1}(O)
 +(P_{CC}-S)B_i+S(T^2h_{i+1}(C,\cdot))(x).
\end{aligned} \tag{9}
\]

Proof: a surviving initial C occurrence receives both Heun halves. If it dies
and a C occurrence is present after the middle jump substep, that last birth
has an independent standard-normal mark and receives only the second half.
The E/O starts likewise use a reset mark whenever their destination is C.
With zero BASE, jump acceptance implements the constant cap-one reference
CTMC; virtual thinning events do not change this ideal transition law. The
augmented memory generator can evaluate P_CC-S without subtractive cancellation.

Start (9) with h_L(E)=h_L(O)=c and
h_L(C,x)=c+0.45*varphi_0.25(y-x). Gaussian expectation preserves a constant
plus a Gaussian likelihood in x. Thus (9) gives the grid likelihood and its
analytic coordinate derivatives; integration of h_0 against the same original
capped prior gives m_grid. This argument concerns ideal random draws and real
arithmetic, not bitwise floating-point law or conditioning on resource success.
The independent [grid-target implementation](../src/heterodiff/evaluation/continuous_fiber_grid_target.py)
is now available with [focused tests](../tests/unit/test_continuous_fiber_grid_target.py).
Its recurrence, forward marginal and Gaussian initializer have received a
separate source/algebra review. Direct forward-mixture and backward-recursion
evidence evaluations agree within 7e-18 for both fixed scenarios; this check
does not certify interval arithmetic or the finite-RNG sampling law.

## 6. What the next diagnostic should and should not conclude

For each original fixed seed/method, replay the saved training-prefix settings
and verify the final parameter digest before comparing step 0/8/16/32 values.
No endpoint top-ups or favorable checkpoint selection are needed. Compare all
eight training nodes; report the terminal identity separately. Stage midpoints
remain a distinct interpolation/algorithmic question.

Report classifier calibration against (1), state-centered potential error,
selected-fiber score error, OTHER spurious score, amplitude saturation and
the necessary capacity witness, with capped and numerical-grid targets kept
separate. The known observation marginal lets nuisance/gauge effects be
distinguished from physical errors. A falling validation loss alone cannot
substitute for these comparisons.

No amplitude increase, observation reweighting, score-loss addition, epoch
extension or architecture change is selected here. Any such remedy changes
the hypothesis class or experiment and needs a prospective comparison. The
analysis establishes one real capacity obstruction and a precise diagnostic
target; it does not assert that removing that obstruction alone will recover
the conditional law, improve endpoint error, or establish a paper-level
advantage for either method.
