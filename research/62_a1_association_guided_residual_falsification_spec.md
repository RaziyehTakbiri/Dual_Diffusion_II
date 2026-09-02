# A1 Association-Guided Residual Falsification Specification

**Status:** frozen base plus audited implementation-custody amendments; production-order and target-runtime HOLD; no learner run  
**Freeze date:** 2026-07-31  
**Parent:** `61_a1_association_preconditioned_residual_audit.md`  
**Decision scope:** finite known-law estimator falsification only

## 1. Question and claim boundary

This gate asks one narrow question:

> Does an exactly normalized association-aware reference guide make one shared
> scalar bridge potential materially easier to learn than a rigorously matched
> direct scalar potential on a finite capped process?

The proposed potential is

\[
h_t^\theta(x;a)=\bar h_t(x;a)\exp r_\theta(t,x,a),
\]

where `bar h` is the analytic information function of an uncapped independent
immigration--death--replacement reference process and `r_theta` is one scalar
residual used for every target birth, death, and replacement edge.

A pass supports only a finite known-law CPU statement about inductive bias,
sample efficiency, and conditional-path accuracy. It does not support
scalability, real-data performance, cross-domain transfer, unbounded
cardinality, a general mixed discrete/continuous framework, a new permanent
algorithm, or submission readiness. No learner metric may enter the
manuscript as a result before this frozen gate is executed and independently
audited.

## 2. Primary finite universe

### 2.1 State and observation alphabets

Use three latent types and three anchor types. The target state space is

\[
\mathcal X_3=\{q\in\mathbb N^3:|q|\le 3\},
\qquad |\mathcal X_3|=20.
\]

The finite observation alphabet retains every count vector through total
cardinality three and adds a distinct overflow outcome:

\[
\mathcal A_3=
\{c\in\mathbb N^3:|c|\le3\}\cup\{\mathsf{overflow}\},
\qquad |\mathcal A_3|=21.
\]

Count vectors are ordered by total cardinality and then lexicographically.
Overflow is last. Freeze the horizon `T=1`. Decision evaluation uses
`t_j=j/32`, `j=0,...,32`; `j=32` is a boundary check and supplies no gradient.

### 2.2 Capped target process

Freeze birth rates

\[
\beta=(0.38,0.30,0.24),
\]

per-occurrence death rates

\[
\delta=(0.28,0.34,0.25),
\]

and the row-source, column-destination replacement matrix

\[
R=
\begin{pmatrix}
0&0.16&0.07\\
0.11&0&0.15\\
0.09&0.13&0
\end{pmatrix}.
\]

For `q in X_3`,

\[
Q(q,q+e_s)=\beta_s\mathbf 1_{\{|q|<3\}},
\]

\[
Q(q,q-e_s)=q_s\delta_s,
\qquad
Q(q,q-e_s+e_z)=q_sR_{sz}\quad(s\ne z),
\]

and the diagonal is the negative row sum. All three edit families must be
active. The target/reference dynamical discrepancy in this primary mechanism
fixture is exactly the blocking of immigration at the target cap.

The initial law is the capped factorial reference

\[
\pi_0(q)=\frac{1}{Z_\vartheta}
\prod_{s=1}^3\frac{\vartheta_s^{q_s}}{q_s!},
\qquad \vartheta=(0.65,0.50,0.40),
\]

with

\[
Z_\vartheta=\sum_{n=0}^3\frac{1.55^n}{n!}
=4.371895833333333.
\]

The cap has initial mass `0.14196263063`; it is not a negligible boundary.

### 2.3 Terminal association law

Freeze detection probabilities

\[
d=(0.72,0.63,0.68)
\]

and row-source confusion matrix

\[
C=
\begin{pmatrix}
0.62&0.25&0.13\\
0.22&0.58&0.20\\
0.18&0.27&0.55
\end{pmatrix}.
\]

The source-to-anchor emission masses, with sources as rows, are

\[
D=\operatorname{diag}(d)C
=
\begin{pmatrix}
0.4464&0.1800&0.0936\\
0.1386&0.3654&0.1260\\
0.1224&0.1836&0.3740
\end{pmatrix},
\]

and the miss vector is `u=1-d=(0.28,0.37,0.32)`. Independent Poisson
observation clutter has rates

\[
\nu_{\rm obs}=(0.10,0.08,0.12).
\]

For retained `c`, the clean probability is the coefficient of `z^c` in

\[
G(z\mid q)=
\exp\!\left(\sum_g\nu_{{\rm obs},g}(z_g-1)\right)
\prod_s\left(u_s+\sum_gD_{sg}z_g\right)^{q_s}.
\]

Equivalently, it is the occurrence-level partial-matching partition including
the Poisson exponential and `1/prod_g c_g!`. Overflow is the unconditioned
tail

\[
K_{\rm assoc}(\mathsf{overflow}\mid q)
=1-\sum_{|c|\le3}K_{\rm assoc}(c\mid q).
\]

No row is conditioned on retained cardinality.

Use the uniform normalized finite reference

\[
\lambda_A(a)=1/21
\]

and whole-observation contamination `epsilon=0.08`:

\[
K_\epsilon(a\mid q)
=0.92K_{\rm assoc}(a\mid q)+0.08\lambda_A(a),
\qquad
g_a(q)=K_\epsilon(a\mid q)/\lambda_A(a)\ge0.08.
\]

Contamination is applied once to the complete observation, never once per
occurrence.

### 2.4 Frozen association and nontriviality witnesses

The anchor-by-source emission matrix `p=D^T` has

\[
\det(p)=0.0423190656\ne0,
\]

so ordinary rank and nonnegative rank are both exactly three. For
`q=(1,1,1)` and `c=(1,1,1)`, all six complete-association terms must be
present and sum to

\[
\operatorname{per}(p)=0.090006360192.
\]

The identity assignment supplies only `67.78%` of this permanent. An
eventwise or maximum-matching shortcut is therefore invalid.

Before any learner run, an implementation-separated calculation must recover:

| Fixture quantity | Frozen value or condition |
|---|---:|
| minimum clean overflow probability | `0.0002658111900217808` |
| maximum clean overflow probability | `0.11343860759109892` |
| contaminated density range | `[0.08122134255134471, 14.39260802357079]` |
| maximum retained `abs(r*_0)` | `0.28651014165` |
| maximum overall `abs(r*_0)` | `0.99836959565` |
| joint-weighted mean `abs(r*_0)` | at least `0.05` |
| exact joint overflow probability at `t=0` | at most `0.05` |
| retained share of joint-weighted `abs(r*_0)` | at least `60%` |

Failure by more than `1e-8` for the determinant, permanent, immigrant means,
or residual maxima invalidates the fixture before training.

## 3. Analytic uncapped reference guide

The reference process lives on `N^3`, never blocks immigration, and otherwise
uses exactly `beta`, `delta`, and `R` above. Its one-occurrence subgenerator is

\[
A=
\begin{pmatrix}
-0.51&0.16&0.07\\
0.11&-0.60&0.15\\
0.09&0.13&-0.47
\end{pmatrix}.
\]

For remaining time `tau=1-t`, let `S_tau=exp(tau A)`. Current-source terminal
anchor masses and miss probabilities are

\[
\bar D_\tau=S_\tau D,
\qquad
\bar u_\tau=1-\bar D_\tau\mathbf1.
\]

Future immigrant terminal-type means and their detected anchor intensities are

\[
m_\tau=\int_0^\tau\beta e^{vA}\,dv,
\qquad
\nu_{\rm imm,\tau}=m_\tau D.
\]

The integral must use a block exponential or linear solve, not an explicit
matrix inverse. Total analytic clutter is

\[
\bar\nu_\tau=\nu_{\rm obs}+\nu_{\rm imm,\tau}.
\]

The clean guide probability is the retained coefficient, or overflow
complement, of

\[
\bar G_\tau(z\mid q)=
\exp\!\left(\sum_g\bar\nu_{\tau,g}(z_g-1)\right)
\prod_s\left(
\bar u_\tau(s)+\sum_g\bar D_{\tau,sg}z_g
\right)^{q_s}.
\]

The decision guide is

\[
\bar h_t(q;a)=0.92\,
\frac{\bar K_{{\rm assoc},1-t}(a\mid q)}{\lambda_A(a)}+0.08.
\]

At `tau=1`, an independent implementation must recover

\[
m_1\approx(0.31898446,0.25993776,0.21914375),
\]

\[
\nu_{\rm imm,1}\approx(0.20524523,0.19263325,0.14456887).
\]

At the terminal boundary `S_0=I`, `m_0=0`, and the guide equals the exact
terminal density, including overflow and contamination.

The exact target information and residual are

\[
h_t^\star=e^{(1-t)Q}g,
\qquad
r_t^\star=\log h_t^\star-\log\bar h_t,
\qquad r_1^\star=0.
\]

No finite-generator-norm Duhamel claim is made between this capped target and
the unbounded reference.

## 4. Frozen splits

### 4.1 Pair split

For retained low-cardinality pairs `|x|<=2`, `|a|<=2`, define

\[
H(x,a)=
(3x_1+5x_2+7x_3+11a_1+13a_2+17a_3
+19|x||a|)\bmod5.
\]

- training pairs `P_tr`: `H in {0,1,2}` (61 pairs);
- validation pairs `P_val`: `H=3` (19 pairs);
- in-domain test pairs `P_test`: `H=4` (20 pairs).

The split implementation must verify that every low-cardinality state and
observation occurs individually in the training set. These counts and the
coverage assertion are frozen pre-training tests.

### 4.2 Time split

- training times `T_tr`: even `j=0,2,...,30` (16 times);
- validation times `T_val`: `j mod 4 = 1` (8 times);
- testing times `T_test`: `j mod 4 = 3` (8 times);
- `j=32`: exact boundary verification only.

The interpolation masks are exactly

\[
M_{\rm train}=T_{\rm tr}\times P_{\rm tr},
\quad
M_{\rm val}=T_{\rm val}\times P_{\rm val},
\quad
M_{\rm joint}=T_{\rm test}\times P_{\rm test},
\]

\[
M_{\rm time}=T_{\rm test}\times P_{\rm tr},
\qquad
M_{\rm pair}=T_{\rm tr}\times P_{\rm test}.
\]

At `T_test`, define four mutually exclusive OOD pair strata:

\[
P_{\rm latent3}=\{|x|=3,\ |a|\le2\},
\]

\[
P_{\rm anchor3}=\{|x|\le2,\ |a|=3\},
\]

\[
P_{\rm both3}=\{|x|=3,\ |a|=3\},
\qquad
P_{\rm overflow}=\mathcal X_3\times\{\mathsf{overflow}\}.
\]

No OOD aggregate may substitute for the `M_joint` in-domain decision.

For any finite mask `M`, define its exact normalized excess BCE as

\[
E_M(\ell)=
\frac{
\sum_{(t,x,a)\in M}\frac12[
J_t(x,a)\operatorname{softplus}(-\ell_t(x,a))+
R_t(x,a)\operatorname{softplus}(\ell_t(x,a))]
-\mathcal L_M(\ell^\star)}
{\sum_{(t,x,a)\in M}\frac12[J_t(x,a)+R_t(x,a)]}.
\]

The same formula and physical masses apply to every interpolation and OOD
stratum. The balanced OOD score is the arithmetic mean of the four stratum
scores; each stratum remains a separate hard diagnostic.

Masked population BCE retains the original pointwise joint/product ratio. In
the sampled lane, the executable importance weighting is fixed in Section 6.

## 5. Matched learner contract

### 5.1 Common inputs and architecture

Both primary learners receive the exact terminal classifier logit

\[
b_T(x,a)=\log g_a(x)-\log z_A(a),
\]

where the denominator is explicitly the observation **density**

\[
z_A(a)=\frac{p_A^{\rm mass}(a)}{\lambda_A(a)}
=\sum_x\pi_T(x)g_a(x)
=\sum_x\pi_0(x)h_0^\star(x;a).
\]

The physical risk tables remain ordinary masses:

\[
J_t(x,a)=\pi_t(x)\lambda_A(a)h_t^\star(x;a),
\qquad
R_t(x,a)=\pi_t(x)p_A^{\rm mass}(a).
\]

Thus `ell*=log h*-log z_A`. PMF and density conventions are never
interchanged, and the product-positive optimum is exactly zero.

use one checkpoint for every observation, and receive the identical
21-dimensional feature vector:

1. `t`, `1-t`, `sin(pi*t)`, and `cos(pi*t)`;
2. three latent counts divided by three and latent total divided by three;
3. three anchor counts divided by three, anchor total divided by three, and an
   overflow indicator (all count coordinates are zero for overflow);
4. the six same-index and cyclic latent--anchor products;
5. latent total times anchor total; and
6. a constant.

The six cross-products are `(x1*a1,x2*a2,x3*a3,x1*a2,x2*a3,x3*a1)` after both
count vectors have been divided by three, so every product is divided by nine.
The total-count product is likewise divided by nine. This explicit ordering
and scaling, rather than an informal feature count, is authoritative.

Both correction networks are `21 -> 32 -> 32 -> 1` with SiLU activations,
binary64 parameters, and identical initial tensors for every paired seed. Let

\[
\mathcal C_B(u)=B\tanh(u/B),\qquad B=2048.
\]

This near-identity common safety map has unit derivative at zero. A
positivity/rate envelope gives `sup|c_D|<375` and `sup|c_R|<1035`: the target
density ratio is bounded by its frozen `[m,M]` range and target exit rate
`2.12`, while the reference guide is bounded by contamination, density at
most `0.92*21+0.08`, and reference event rate at most `2.72`. Hence neither
oracle target is structurally clipped. The learner equations are

\[
\ell_{\rm direct}=b_T+(1-t)\mathcal C_B(F_\phi),
\]

\[
\ell_{\rm G+R}
=\log\bar h_t-\log z_A+(1-t)\mathcal C_B(F_\theta).
\]

Before any path calculation, each fitted checkpoint receives a continuous
certificate. Using `|SiLU'|<=1.1`, define the outward upper row-sum norm

\[
U_\infty(W)=\max_i
\operatorname{nextafter}\!\left(
\operatorname{float}\!\left[
\sum_j\operatorname{Fraction}(
|W_{ij}|.\operatorname{as\_integer\_ratio}())
\right],+\infty\right),
\]

where the sum is exact over the binary64 values. Thus floating evaluation
cannot underestimate the declared bound. The ordinary
21 inputs use `L_x=pi`. For the guide-input control,

\[
|v'_{22}|\le
2.72(19.4/0.08-1)/4<165,
\]

from the frozen reference event-rate and positive-density envelopes, and its
certificate uses `L_x=165`. Thus the implemented bound is

\[
L_F=(1.1)^2U_\infty(W_3)U_\infty(W_2)U_\infty(W_1)L_x.
\]

For `c(t)=(1-t)C_B(F(t))`, `|c'(t)|<=B+L_F`. Evaluate every
state--observation pair on the uniform `1/4096` certificate grid and require

\[
\max_{\rm grid}|c|+(B+L_F)/(2\cdot4096)\le20.
\]

The implemented check evaluates an immutable parameter snapshot at all
`4097 x 20 x 21` grid points in fixed time chunks of 128. It uses
`nextafter(pi,+infinity)` for the ordinary input bound and an outward-rounded
grid maximum. This is an **operational binary64 continuous-time safety
certificate** for the declared evaluator, not an interval enclosure or a
real-arithmetic theorem for an ideal MLP: the binary64 forward passes on the
grid have no separate interval/forward-error enclosure. Consequently every
potential call must also check finiteness and strict
`|log h_t(x;a)|<24` before exponentiation; checked edge log tilts must remain
below 48. A formal real-arithmetic statement requires a later interval or
forward-error analysis and is not claimed by this experiment.

Failure of either the snapshot certificate or any runtime physical-log check
places the complete gate on HOLD before exponentiating rates; it may not
select an earlier or replacement checkpoint. The exact terminal table is
common fixed information and is not counted as trainable capacity.

Production evaluation is bound once to an owned immutable snapshot. Its
full-classifier SHA-256 identity covers method and composition rule, actual
fixture/population/terminal contents, correct/cyclic/no-guide identity,
architecture, parameter snapshot, certificate witness and grid feature,
canonical configuration, frozen execution environment, and decision-bearing
source/specification files. Expensive snapshot and guide-grid hashes are
checked at each top-level result boundary, not at every scalar adaptive-solver
callback. Arbitrary callback evaluators are explicitly test-only and cannot
produce learned evidence.

The primary models have identical parameter counts, initial tensors, data,
updates, terminal rule, and numerical precision. Analytic-guide evaluation
time and memory count toward the proposed method.

### 5.2 Stronger direct and identification controls

The stronger direct control is exactly `21 -> 40 -> 40 -> 1`, receives the
same sampled streams, and uses 4,500 updates with the otherwise identical
schedule. Its parameter count, multiply-add count, wall time, and peak memory
are reported. No post-hoc wall-clock matching or unnamed capacity doubling is
allowed. A correct-guide win that disappears here is a STOP.

Additional identification controls are:

- guide alone (`r=0`);
- the guide supplied as a twenty-second input feature without an additive
  skip, using `22 -> 32 -> 32 -> 1` and otherwise identical training;
- a mismatched guide formed by the fixed cyclic permutation
  `(beta_1,beta_2,beta_3)->(beta_2,beta_3,beta_1)` while the target and terminal
  law stay unchanged;
- a full-population observation-specific affine-count/eventwise learner,
  reported as an oracle capacity diagnostic only;
- oracle-supervised separate birth, death, and replacement corrections,
  reported only as a diagnostic upper bound because they are neither one
  coherent scalar potential nor trained by the proposed objective;
- an exact potential with the ordinary, untilted initial law;
- the unconditional process;
- an oracle-only product-positive algebra control on the full
  `33 x 20 x 21` reporting domain: set `J=R` cellwise, compute the declared
  pointwise optimal logit `log J-log R`, and require its maximum absolute
  value to be at most `1e-9`; this control takes no optimizer step, is not a
  learned negative control, and cannot determine PASS or STOP; and
- exact residual supervision as an oracle-only upper bound.

The guide-input feature and its output equation are

\[
v_{22}=(\log\bar h_t-\log z_A)/4,
\qquad
\ell_{\rm input}=b_T+(1-t)\mathcal C_B(F(t,x,a,v_{22})).
\]

The mismatched model has the identical 21-input architecture, initialization,
samples, batches, and schedule as the proposal, but uses

\[
\ell_{\rm mismatch}=\log\bar h_t^{\rm cyc}-\log z_A
+(1-t)\mathcal C_B(F),
\]

where the cyclic immigration permutation was fixed above. Separately for each
co-primary, require correct/mismatched paired geometric-mean AULC ratio
`<=0.90` and correct/input ratio `<=0.95`. In each comparison, at least 7 of 8
paired seed ratios must be strictly below the corresponding margin; the same
seven seeds need not serve the two different controls. Otherwise the additive
preconditioning mechanism is not identified. Oracle-supervised eventwise and
separate-family diagnostics cannot determine PASS or STOP.

## 6. Training protocol

There are two lanes:

1. exact masked-population BCE, used only for capacity and optimization
   diagnosis; and
2. sampled BCE, used for the decision-bearing sample-efficiency claim.

The exact lane has no sample budget and no checkpoint-selection role. For
each of the eight frozen seeds, its full-batch objective is

\[
\mathcal R_{\rm exact}=\frac1{2|T_{\rm tr}|}
\sum_{j\in T_{\rm tr}}\sum_{(x,a)\in P_{\rm tr}}
\left[J_{t_j}(x,a)\operatorname{softplus}(-\ell)
+R_{t_j}(x,a)\operatorname{softplus}(\ell)\right].
\]

This is exactly the expectation of the sampled objective below, including
the unnormalized masked class masses. The equal-width direct and G+R models
use fresh copies of the same seed-specific initial tensors, the same AdamW
hyperparameters and learning-rate sequence, and 3,000 full-batch updates; the
fixed stronger direct diagnostic uses 4,500. The final update is reported,
with exact train/validation/test excess BCE and gradient/optimization traces.
No exact-lane value may select a sampled checkpoint, alter a hyperparameter,
or enter a material-win criterion. Other identification controls remain in
the sampled lane unless explicitly labelled oracle-only.

Sample budgets are nested:

\[
N\in\{512,4096,32768\},
\]

balanced exactly over 16 training times and both classes. `N` denotes the
total number of **accepted training examples**. For budget `N`, each
time/class cell contains

\[
m=N/(2|T_{\rm tr}|)\in\{16,128,1024\}
\]

examples. Freeze paired seeds

`1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011`.

No seed may be replaced, removed, or restarted. The same nested examples are
used for the matched learners. Every `(seed,budget,method)` run starts from a
fresh copy of that seed's frozen initial tensors; budgets are not warm-started
from one another.

For each training time `t_j`, let `P_{+,j}=J_{t_j}` and `P_{-,j}=R_{t_j}` and
let `P_tr` also denote the pair indicator. Freeze

\[
\alpha_{y,j}=\sum_{(x,a)\in P_{\rm tr}}P_{y,j}(x,a),
\qquad
Z_{yjk}\sim P_{y,j}(\cdot\mid P_{\rm tr}).
\]

For each `(j,y)`, one 1,024-example maximum stream is drawn once; budgets 512
and 4,096 use its first 16 and 128 examples. The empirical risk is

\[
\widehat{\mathcal R}_N=
\frac{1}{2|T_{\rm tr}|m}\sum_{j,k}
\left[
\alpha_{+,j}\operatorname{softplus}(-\ell(Z_{+jk}))+
\alpha_{-,j}\operatorname{softplus}(\ell(Z_{-jk}))
\right].
\]

This estimates the original unnormalized masked risk. Independently
renormalizing the two classes is forbidden.

Training is CPU, deterministic single-thread, and binary64:

- AdamW, learning rate `1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, weight
  decay `1e-6`;
- batch size 128;
- gradient-norm clipping at 1;
- 3,000 updates;
- cosine decay to `1e-5`; and
- the final update is the decision checkpoint.

Exact and finite-sample validation BCE are post-selection diagnostics only and
cannot select a checkpoint. The stronger direct model receives 4,500 updates.
Hyperparameters may be debugged only on a separately frozen calibration
fixture. Metrics on this decision fixture may not change architecture,
splits, budgets, seeds, thresholds, or optimization.

The execution environment is Python 3.11.5, NumPy 2.4.6, SciPy 1.17.1, and
PyTorch 2.12.1 CPU. Use one thread and deterministic algorithms. Categorical
draws use NumPy `PCG64` inverse-CDF sampling in the frozen observation order.
For paired seed `s`, data, model, and batch streams use independent
`SeedSequence(s).spawn(3)` children. Weights use generator-driven Xavier
uniform initialization and biases are exactly zero. Each epoch is a PCG64
permutation of the accepted examples; because every `N` is divisible by 128,
no partial batch occurs. The learning rate at update `k=0,...,K-1` is

\[
\eta_k=10^{-5}+\tfrac12(10^{-3}-10^{-5})
[1+\cos(\pi k/(K-1))].
\]

The NumPy-to-PyTorch model-seed boundary is also frozen before execution.
Reconstruct spawn child one, call
`generate_state(1, dtype=np.uint64)` exactly once, convert that scalar to a
Python integer without truncation, and pass it to a fresh CPU
`torch.Generator.manual_seed`.  Every `(seed,budget,method)` creates a fresh
generator this way.  Linear layers are initialized in forward order
`(W_1,W_2,W_3)`, each by generator-driven Xavier uniform in PyTorch's native
row-major parameter shape, followed by an exactly zero bias.  Consequently
the three `21 -> 32 -> 32 -> 1` methods have byte-identical initial tensors
within each paired seed and budget; different-shape controls share the same
seed boundary but cannot share tensors.

Before training, emit SHA-256 digests of every maximum dataset, each prefix,
initial tensor collection, and complete batch-index schedule. Dataset and
batch hashes are common to paired methods.

Every `(seed,budget,method)` sampled run executes in a fresh isolated process.
Before NumPy, SciPy, or PyTorch is imported, set `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`,
`NUMEXPR_NUM_THREADS`, and `BLIS_NUM_THREADS` to one, `PYTHONHASHSEED` to
zero, and hide accelerators. In the worker, `threadpoolctl==3.6.0` must find
at least one native pool and report one thread for every discovered BLAS or
OpenMP pool; PyTorch must independently report one intra-op and one inter-op
thread with deterministic algorithms enabled. The runtime record includes OS,
CPU/machine, NumPy build/BLAS configuration, all library versions, native-pool
records, and its own digest.

One canonical configuration digest binds the optimizer betas, epsilon,
weight decay, learning-rate endpoints and sequence, batch size, clipping,
updates, architecture, features, safety map, certificate grid/chunk/limit,
fixture, expected environment, and every decision-bearing source and this
specification. Immediately before update zero the worker recomputes the full
preflight, including all dataset/prefix/schedule, RNG, tensor, parameter,
count, fixture, source, configuration, and environment identities.

Execution is exactly once. Before spawning a worker, the parent durably issues
one coordinate-specific launch authorization and binds it to the child process
identity. The fresh child must atomically consume that authorization before it
may create a worker session. A self-issued pipe token, same-process launch, or
unconsumed/reused authorization is not production execution evidence. An
atomic, fsync-backed ledger key then covers fixture, source/specification,
configuration, execution runtime, seed, budget, method, launch authorization,
worker session, and child process identity. The worker records `RESERVED`,
then durably records the complete `PREPARED` preflight before issuing a
single-use process-local execution permit. A duplicate key or restart is
rejected, including a prior `RESERVED`, `PREPARED`, `RUNNING`, `SUCCESS`,
`FAILURE`, or `HOLD` record.

Only the optimizer executor may mint a completion capability. It does so after
the exact frozen update count, final empirical-risk computation, immutable
parameter snapshot, continuous certificate, classifier construction, resource
accounting, and result construction. Its receipt binds the expected and
observed update counts, initial and final parameter identities, a rolling
per-update transcript, all launch/session/ledger identities, and the complete
result digest. The worker serializes the result, reopens and revalidates those
bytes, consumes the completion capability once, and only then records
`SUCCESS`. Free-form or caller-constructed `RUNNING -> SUCCESS` promotion is
forbidden. Any failure remains fail-closed and records `FAILURE` or `HOLD`
where custody has advanced far enough to do so.

The exact-population and sampled campaign aggregates are loader-only wrappers
over the complete canonical coordinate sets. They reopen every ledger and
saved payload, reject missing or extra coordinates and reused launch, session,
process, success, or completion identities, reconstruct the paired/nested
design, and bind total update and resource counts. Their raw aggregate records
remain scientifically ineligible until the separate execution-order ledger
attests the prerequisite, rank, exact, primary, control, metric, decision, and
audit barriers below. Caller-supplied metric containers are never production
decision evidence; decision metrics are freshly recomputed from the canonical
aggregate and the aggregate is reopened once more after the expensive
evaluation to close the custody window.

Resource accounting spans preparation, analytic-guide/features, optimization,
snapshotting, and certification. Report process CPU time, wall time, optimizer
wall time, preparation CPU/wall time, and fresh-process peak RSS normalized to
bytes. Because each method owns a fresh process, the peak is method-scoped and
includes its runtime baseline; analytic-guide costs cannot be excluded.

## 7. Evaluation

### 7.1 Primary statistics

Two co-primary requirements are retained, but only the first is called
in-domain:

1. exact excess BCE AULC on the in-domain joint time-and-pair test split; and
2. full-target-state, unconditional-base-normalized, observation-balanced,
   exact time-inhomogeneous path-KL AULC for retained ambiguous observations
   `(1,1,0)`, `(1,0,1)`, and `(0,1,1)`.

For method `m`, seed `s`, and budget `N`, the first ordinate is

\[
y^{\rm BCE}_{m,s,N}=E_{M_{\rm joint}}(\ell_{m,s,N}),
\]

and the second is

\[
y^{\rm path}_{m,s,N}=\frac13\sum_{a\in\mathcal A_{\rm amb}}
\frac{D_{\rm KL}(P^{\star,a}\Vert P^{m,s,N,a})}
{D_{\rm KL}(P^{\star,a}\Vert P^{\rm unconditional,a})},
\]

where `A_amb` is the three observations above. Each denominator must be
strictly positive. After applying a `1e-12` floor to every ordinate for ratio
statistics only, the equal-log-spacing AULC is

\[
A_{m,s}=\frac{y_{512,m,s}+2y_{4096,m,s}+y_{32768,m,s}}4.
\]

For paired log ratios `d_s=log(A_G+R,s/A_direct,s)`, report
`exp(mean_s d_s)`. The exact one-sided paired sign test at the material null
ratio `0.90` counts `A_G+R,s/A_direct,s < 0.90`; exact ties are non-wins. Seven
or eight wins give `p<=9/256<0.05` under independent paired seeds. The same
seven seeds must pass this test for both co-primary metrics.

For every nonnegative learned/control metric used in any ratio, replace both
numerator and denominator by `max(value,1e-12)` for the ratio statistic only;
absolute-reduction criteria always use raw values. Every unconditional path
normalizer must itself exceed `1e-12`, or the gate is on HOLD.

### 7.2 Mandatory metrics

- exact masked population excess BCE;
- centered log-information RMSE and maximum error;
- residual RMSE and oracle residual range;
- edge log-rate RMSE and maximum error separately for birth, death, and
  replacement;
- conditional-initial TV;
- intermediate and endpoint TV;
- path KL per observation, observation-weighted, retained-only, and
  overflow-only;
- Brier and reliability calibration error;
- information-semigroup, normalization, and edit-cycle residuals;
- CPU time and peak memory; and
- every interpolation and extrapolation stratum in Section 4.

Calibration uses the balanced positive/negative population mixture, with
posterior prediction `p=sigmoid(ell)`, exact posterior
`tau=J/(J+R)`, and cell mass `w=0.5*(J+R)`, uniformly over the 33 reporting
times. The Brier score is
`sum 0.5*[J*(1-p)^2+R*p^2]/sum w`. Reliability uses ten fixed equal-width
posterior bins `[k/10,(k+1)/10)` for `k=0,...,8` and `[0.9,1]` for the final
bin. Within each occupied bin, prediction and positive frequency are their
`w`-weighted means; ECE is the `w`-mass-weighted mean absolute gap. Empty
bins contribute zero and the maximum reliability gap is taken only over
occupied bins. No adaptive binning or post-result bin-count choice is allowed.

Population quantities use physical PMF weights. Centered log-information
errors remove, separately for each `(t,a)`, the state-weighted mean so that an
observation-only classifier gauge cannot masquerade as an edge error.

Path KL includes the correctly tilted initial law and the inhomogeneous jump
term. Target occupancy is propagated under the exact target bridge; candidate
occupancy and endpoints use each candidate's own changing rates. Primary and
refined integrations must be independent numerical calls.

The primary path lane uses `scipy.integrate.solve_ivp` with `DOP853`,
`rtol=2e-10`, `atol=2e-12`, and `max_step=1/128`; its `quad_vec` controls are
`epsabs=1e-11`, `epsrel=1e-10`, and `limit=2000`. The independently
instantiated refined lane uses `DOP853`, `rtol=2e-11`, `atol=2e-13`, and
`max_step=1/256`, with `quad_vec` `epsabs=1e-12`, `epsrel=1e-11`, and
`limit=2000`. Each call permits at most 300,000 potential evaluations. No
adaptive state is reused between primary/refined path or occupancy calls.

Before any learned path is evaluated, construct all 21 canonical reusable
reference records and emit one ordered reference-set digest. Each record binds
the actual fixture arrays, observation identity and mass, frozen runtime, both
solver configurations, exact target quantities, unconditional primary and
refined results, and its own content digest. All 21 must pass oracle-self path
KL, independently refined unconditional-denominator, and exact-target
occupancy controls; a partial reference set cannot evaluate a candidate.

For every retained-observation material criterion, freeze

\[
K^{\rm ret}_{m,s,N}=
\frac{\sum_{a\ne\mathsf{overflow}}p_A^{\rm mass}(a)
D_{\rm KL}(P^{\star,a}\Vert P^{m,s,N,a})}
{\sum_{a\ne\mathsf{overflow}}p_A^{\rm mass}(a)
D_{\rm KL}(P^{\star,a}\Vert P^{\rm unconditional,a})}.
\]

Every normalization denominator must be strictly positive.

### 7.3 Numerical gates

| Quantity | Required threshold |
|---|---:|
| terminal guide/target log-density error | `<=1e-12` |
| maximum terminal residual | `<=1e-10` |
| oracle self path KL | `<=1e-10` nat |
| primary/refined path-KL change | `<=1e-8` nat |
| primary/refined unconditional path-KL change | `<=1e-8` nat |
| primary and refined unconditional denominator | each `>1e-12` nat |
| exact-target occupancy maximum absolute error | `<=1e-8` |
| primary/refined endpoint TV | `<=1e-8` |
| generator row-sum residual | `<=1e-10` |
| scalar edit-cycle residual | `<=1e-10` |
| oracle product-positive maximum absolute logit | `<=1e-9` |

Any numerical-gate failure places the scientific decision on HOLD.

## 8. Frozen material-win criteria

All criteria below are required against the equal-parameter direct learner:

- both co-primary AULC paired geometric-mean ratios are `<=0.75`;
- the exact paired sign test at ratio `0.90` passes in the same at least 7 of 8
  seeds for both co-primary metrics;
- at `N=32768`, the paired geometric mean of
  `K_ret_G+R/K_ret_direct` is `<=0.80`, and the arithmetic mean over seeds of
  `K_ret_direct-K_ret_G+R` is at least `0.02`;
- at `N=32768`, for each seed form the arithmetic mean of its four OOD
  stratum scores; the paired geometric mean of proposed/direct balanced-score
  ratios is `<=0.80`, with no individual OOD stratum paired geometric-mean
  score ratio above `1.05`;
- at `N=32768`, the paired geometric-mean excess-BCE ratios on both `M_time`
  and `M_pair` are `<=1.05`;
- at `N=32768`, no edit family's paired geometric-mean weighted-median
  log-rate-error ratio exceeds `1.05`, and at least two of the three family
  ratios are `<=0.95`;
- against the wider/longer direct control, each co-primary AULC ratio is
  `<=0.90`, and its paired geometric-mean metric ratio is no worse than `1.00`
  at maximum `N`; and
- the exact residual correction scale is `<=0.70` of the direct correction
  scale defined below.

At `N=32768`, the paired geometric mean over seeds of
`K_ret_G+R/K_ret_guide-alone` must be `<=0.90`; the guide-alone denominator is
the same deterministic value for every seed. For each of the three ambiguous
observations, the paired-geometric-mean normalized path-KL ratio must be at
most `1.00`, and at least two must be at most `0.80`. Otherwise one favorable
observation may hide a failure.

For an edit family, take the weighted median absolute edge log-rate error over
all 32 nonterminal times, observations, states, and active edges, with weight
`p_A^mass(a) * mu_t^a(x) * q_t^a(x,y)` and uniform time weight. Compute this
per seed at `N=32768`, then take its paired geometric-mean ratio. No aggregate
may hide a failed observation, edge family, or extrapolation stratum.

Finally, at `N=32768` compute a proposed/direct paired geometric-mean path-KL
ratio separately for every one of the 21 observations; every ratio must be
`<=1.05`. Among the 20 retained observations, at least two of these ratios
must also be strictly below `1.00`; an overflow-only improvement or equality
on every retained observation is insufficient. The stronger
`<=1.00`/two-at-`<=0.80` rule above remains additional for the three ambiguous
observations.

For the correction-scale check, on all 32 nonterminal evaluation times define

\[
c_D=(\ell^\star-b_T)/(1-t),
\qquad c_R=r^\star/(1-t).
\]

Center each across states separately for every `(t,a)`, using weights
proportional to `0.5(J_t+R_t)`, then take the RMS under those same physical
weights over the complete finite universe. The required ratio is
`RMS(c_R)/RMS(c_D)<=0.70`. This measures target scale, not parameter count or
a continuous-time supremum.

## 9. Rank stress

Separately instantiate eight source and eight anchor types with cap two, giving
45 latent states and 45 retained anchor counts plus overflow. Index types by
`s,g in {0,...,7}`. For each `d in {1,2,3,4,8}`, freeze

\[
M^{(d)}_{sg}=\sum_{k=0}^{d-1}
\left(\frac{(s+1)(g+1)}{81}\right)^k,
\qquad
C^{(d)}_{sg}=\frac{M^{(d)}_{sg}}{\sum_jM^{(d)}_{sj}}.
\]

This positive Vandermonde product has exact ordinary rank `d`; positive row
normalization preserves it. Use detection `d_s=(55+s)/100`, so the emission
matrix is `diag(d) C^(d)`. Freeze

\[
\beta_s=(s+1)/100,
\qquad \delta_s=(20+s)/100,
\]

and, for `s != z`,

\[
R_{sz}=(((s+z)\bmod3)+1)/1000,
\qquad R_{ss}=0.
\]

Use clutter `nu_g=(g+1)/200`, `T=1`, uniform reference mass `1/46`, and
whole-observation contamination `0.08`. Record serialized arrays and SHA-256
digests before timing; the formulas above, not later digests, define the law.

Evaluate the complete `33 x 45 x 46` guide-density table at `t_j=j/32`. For
every `d`, require:

- analytic-guide relative agreement with exhaustive coefficient enumeration
  `<=1e-10`;
- at most `50,000,000` instrumented scalar coefficient updates;
- at most `5,000,000` simultaneously live float64 coefficient/table entries;
  and
- no occurrence-level matching enumeration in the timed implementation.

The counters apply only to the analytic fixed-rank implementation; the
independent exhaustive oracle is excluded from both and is run separately.
One **coefficient update** is one logical recurrence multiply-accumulate

\[
T_{\rm new}[m+e_k]\mathrel{+}=T_{\rm old}[m]w_k
\]

in either the observation-factor table or source-factor table, or one logical
final contraction multiply-accumulate `sum_m A_m B_m m!`. Miss/clutter is
channel `k=0`. Count every recurrence edge allowed by the frozen loop bounds,
including an edge whose floating weight happens to be zero; vectorizing or
fusing it does not change the count. Cache exactly one `A_c` table per retained
observation and one `B_q` table per latent state at each time, then contract
each of the `45 x 45` retained pairs. Overflow is the complement and adds no
coefficient update. The instrumented counter must equal a second count
computed directly from these loop bounds.

Peak analytic allocation is the sum of owned backing-buffer bytes, counting a
view's base allocation once and including temporaries. The allocation registry
must include: block-exponential input/output; survival and integral matrices;
terminal/effective emission factors; immigrant, clutter, miss, and reference
vectors; `U` and propagated `V`; all cached `A_c` and `B_q` coefficient tables;
two recurrence scratch tables; clean/mixed/density working grids; and the full
`33 x 45 x 46` output. Non-float64 numeric buffers count by their actual byte
size and cannot evade the gate. Require peak owned numeric bytes
`<=8*5,000,000`; report Python-object overhead separately with peak RSS.

The hard gate is operation/allocation based. Report, but do not threshold,
Python/NumPy/SciPy versions, OS, CPU model, BLAS build and thread count, one
warm-up, median of five wall-time repetitions, and process peak RSS. This is
computational correctness evidence, not learned superiority. Failure blocks
any fixed-rank scalability claim but does not retroactively alter the finite
primary metrics.

## 10. Required pre-training tests

1. `Q 1=0`, nonnegative off-diagonals, and all edit families active.
2. Clean mass rows, contaminated mass rows, and densities normalize under
   their declared measures.
3. PGF coefficients, labelled association enumeration, and rank-three
   coefficient contraction agree for every retained target cell.
4. The six-term permanent and the repeated-occurrence factorial cancellation
   are recovered exactly within tolerance.
5. Overflow is the complement of unconditioned retained probability.
6. Analytic reference rows normalize and remain at least `epsilon` after
   contamination for every state and frozen time.
7. One-type immigration--death guide values agree with an independent count
   oracle; a replacement-only typed case agrees with labelled enumeration.
8. `bar D_tau=S_tau D`, immigrant clutter, and rank preservation agree with
   independent calculations.
9. The exact residual is terminal-zero and its composite exactly reconstructs
   target information, all edge families, and the conditional initial law.
10. Exact target harmonicity, guide terminal identity, all-21 path-reference
    preflight, and oracle product-positive algebra controls pass.
11. Frozen arrays, split indices, and their SHA-256 digests are emitted before
    any learner result.

## 11. Stop rules

Stop or retain HOLD if any material-win or numerical criterion fails, or if:

- the in-domain win fails even when OOD improves;
- the stronger direct control removes the advantage;
- the fixed width-40/4,500-update direct control violates Section 8;
- guide plus residual fails to improve guide alone by the frozen `10%`;
- the correct guide fails the frozen mismatched-guide or guide-input
  identification margins;
- the exact residual correction scale is not at least `30%` smaller than the
  direct correction scale under the frozen weighting;
- a split, digest, seed, metric, budget, or threshold changes after results;
- gains occur only for overflow or one observation, fewer than two edit
  families meet the explicit `<=0.95` gain threshold, or fewer than two
  retained observations have a strict proposed/direct path ratio below one;
- support, factorial, clutter, contamination, boundary, normalization, or
  refinement checks fail;
- the rank operation/allocation gate fails.

The oracle-supervised eventwise and separate-family controls are diagnostic
only and cannot trigger a decision. The candidate-computable path bound from
Checkpoint 61 is also reported only as a theorem-development diagnostic in
this finite gate; no path-bound claim is authorized, so no undefined
"vacuity" predicate enters PASS or STOP.

A failure is information: the manuscript must narrow or pivot to a sparse,
bounded-treewidth, or sequential Monte Carlo association estimator. Thresholds
must not be relaxed to manufacture a pass.

## 12. Execution order

The order is a fail-closed state machine, not a chronology inferred from file
timestamps. Every phase requires a loader-issued, single-use authorization
bound to the current immutable ledger snapshot and campaign instance. Phase
evidence is content-addressed, and no authorization may be issued from a stale
or noncanonical state.

1. initialize the immutable plan and verify the already frozen overflow law,
   analytic guide, exact population/residual, arrays, splits, and prerequisite
   receipt;
2. run and durably verify the five-rank operation/allocation stress gate;
3. authorize and run the 24 exact-population capacity diagnostics, then reopen
   all 24 payloads and commit their canonical aggregate;
4. authorize and run only the 48 sampled primary coordinates (`direct` and
   `guided`) in their frozen interleaved order;
5. reopen those 48 primary checkpoints, compute their primary metrics without
   changing any configuration, and durably commit a primary-metric receipt;
6. only after that receipt exists, authorize and run the remaining 72 sampled
   stronger-direct, guide-input, and mismatched-guide controls in their frozen
   interleaved order;
7. reopen all 120 sampled payloads, reconstruct the paired/nested design, and
   commit the canonical sampled aggregate;
8. authorize one fresh candidate-decision computation from the canonical
   prerequisite, rank, exact, and sampled aggregates; recompute all non-path
   and path metrics from saved checkpoints and revalidate custody afterward;
9. keep the resulting `PASS`, `HOLD`, or `STOP` object non-authoritative while
   an implementation-separated code, evidence, and theory audit is performed;
   and
10. finalize a publication decision only when that audit receipt binds the
    exact candidate and every predecessor. Any failed phase terminalizes the
    order ledger as `HOLD` or `FAILURE`; later phases cannot be authorized.

There is deliberately no `run-all` command. Rank, exact, primary, metric,
control, aggregation, candidate, audit, and finalization are separate explicit
operations so that the user can execute compute-bearing phases on the pinned
target CPU runtime and inspect each durable barrier. Initialization and status
inspection never train a learner.

Two order implementations now coexist and are non-interchangeable. The older
foundation remains namespaced `TEST_ONLY_NO_RUN`. A separate production-order
core now owns a distinct authority domain, immutable plan, complete source
manifest, semantic runtime contract, durable prerequisite receipt, and the
`NEW -> PREREQUISITE_VERIFIED -> RANK_AUTHORIZED` prefix. It can recover a
receipt published before its event, reopens exact predecessor custody, and
fails closed on stale, terminal, noncanonical, or redirected state.

This prefix still cannot start scientific computation. Its plan and phase
records explicitly set production execution authorization and runner
integration to false, and coordinate issuance is dormant until a typed runner
binder exists. Separately, a loader-only 48-primary success-set barrier and a
durable primary-metric boundary now exist, but neither sampled launch records
nor metric receipts yet bind the production plan nonce, ledger head, and
single-use phase consumption. Consequently steps 2--10 above remain
unreachable from the production ledger. Production-to-runner integration and
a passing pinned target runtime are mandatory pre-execution barriers, not
clerical follow-up work.

## 13. Pre-execution audit record

The first strict audit found one P0 and eleven P1 specification defects before
any learner was implemented or run. The amendments above are authoritative:

- the asymmetric bounded-output handicap was replaced by one loose
  near-identity safety map containing both oracle targets plus a continuous
  post-fit Lipschitz certificate;
- the classifier denominator is the observation density `z_A`, while risks
  retain physical masses;
- sampled rejection weights, accepted-example budgets, nested prefixes, and
  masks are executable formulas;
- oracle population validation no longer selects checkpoints;
- interpolation and mutually exclusive OOD masks are exact Cartesian sets;
- AULC, normalization, paired ratios, and the exact sign test are fully
  specified;
- full-state path KL is no longer mislabeled in-domain;
- oracle-supervised controls cannot decide the empirical comparison;
- the stronger direct architecture and update schedule are fixed rather than
  post-hoc wall-clock matched;
- feature scaling, software, RNG streams, initialization, batching, schedule,
  and pre-training hashes are frozen; and
- the residual-scale diagnostic has a stated domain and weighting, while the
  not-yet-established path bound is non-decision-bearing.

Because these corrections precede every learner result, they strengthen the
preregistration without post-hoc threshold adaptation.

Two post-amendment audits closed the original specification defects, after
which implementation-custody audits deliberately reopened issues before any
optimizer update. Those audits found and corrected, among other issues, a
free-form synthetic `SUCCESS` path; incomplete per-update parameter custody;
pre-reservation and post-consumption orphan states; parent spawn, descriptor,
token, wait, and issuance-commit ambiguities; cleanup paths that could mask the
scientific exception; PID-reuse assumptions; conflicting repeated exit
observations; and aggregate/decision admission from caller-controlled objects.

The final sampled and exact launch protocols now require durable parent
issuance, observed-child binding, single-use child consumption, an owned worker
session, strict run-stage receipts, executor-only completion, saved-byte
reopening, and a separate parent-confirmed zero-exit receipt before a
`SUCCESS` checkpoint can enter canonical admission or aggregation. Confirmed
child death from `CONSUMED`, `RESERVED`, `PREPARED`, or `RUNNING` is closed by
a hash-chained parent-reaper `FAILURE`; existing child terminal evidence is
extended by a non-overwriting exit observation. Parent-reaper `HOLD`, changed
exit status, missing or duplicate run ownership, and nonzero exit paired with
`SUCCESS` fail closed. A final independent read-only audit reports no
actionable P0/P1/P2 in either lane.

The ordering foundation also passed its independent no-run audits after fixes
for mutable runtime-contract views, incomplete source closure, crash-durability
ordering, pending-file recovery, and dangling-symlink handling. This does not
remove its explicit `TEST_ONLY_NO_RUN` boundary. The local rank-runtime probe
found no `threadpoolctl`-visible native pool and therefore returned
`benchmark_metadata_complete=False`; the five-rank grid was not run. Checkpoint
64 records the implementation evidence and the remaining production-order and
target-runtime HOLDs. Checkpoint 63 remains evidence only for the analytic
guide prerequisite. No empirical PASS is authorized by this specification or
by implementation tests.
