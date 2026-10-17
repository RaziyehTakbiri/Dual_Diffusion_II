# Independent continuous-fiber guide and initialization diagnostic

This document derives the independent analytic control used by the
[prospective multi-seed protocol](MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md).
It specifies formulas and reproduction, not default experiment results.
The implementation is
[continuous_fiber_initialization_diagnostic.py](../src/heterodiff/evaluation/continuous_fiber_initialization_diagnostic.py),
with independent and native-guide cross-checks in
[test_continuous_fiber_initialization_diagnostic.py](../tests/unit/test_continuous_fiber_initialization_diagnostic.py).

## 1. One initial prior, two different future processes

Fix a selected complete continuous key with reference probability rho, and
scientific count cap N=1. Project the actual full-support key law into:

- E: no occurrence;
- O: one occurrence with any other key;
- C: one occurrence with the selected key and coordinate z.

The implementation's category order is EMPTY, OTHER, CONTINUOUS, or E,O,C.
O is an aggregate for calculation, not an artificial replacement event.
Materialization for the real sampler preserves the original non-selected key
and its correct atomic or continuous fiber.

Both initializers below start from the same capped reference prior Pi_N:

\[
\pi_E=\frac1{1+\theta},\qquad
\pi_O=\frac{\theta(1-\rho)}{1+\theta},\qquad
\pi_C=\frac{\theta\rho}{1+\theta},
\]

with standard-normal coordinate density phi_1(z) conditional on C. The BASE
potential is zero. The diagnostic rejects a different BASE potential or a
nonstationary initial prior rather than relabeling its comparison.

The **exact capped likelihood** propagates through the cap-respecting
birth/death/OU process. Births are suppressed while an occurrence is present.
Its independent finite-state/Gaussian-mixture oracle is
[continuous_fiber_conditional_benchmark.py](../src/heterodiff/evaluation/continuous_fiber_conditional_benchmark.py).

The **uncapped guide likelihood** propagates through immigration/death/OU:
births remain possible when an occurrence is already present. The future
latent count can exceed one. Applying the initial cap to Pi_N does not impose
that cap on this future process. This is the auxiliary reference used by the
association guide, as distinguished in the
[association and initializer appendix](../manuscript_v3/hybrid_diffusion_association_initializer_proof_v1.md).

Thus the two normalized initial laws are Pi_N times different propagated
likelihoods. Neither is compared with an uncapped initial prior.

## 2. Observation channel and clocks

The observed datum consists of exactly one selected-key occurrence with
coordinate y. The observation cap is M=1, with a separate overflow atom.
Clean observations retain each occurrence with probability p=1/2 and add
independent N(0,sigma^2) noise to each retained continuous coordinate.
Whole-observation contamination instead draws from a unit-rate Poisson
reference observation. Its continuous coordinate is standard normal and is
**not** passed through the clean noise channel again.

Write phi_s for the density of N(0,s^2). The reference density of this particular
one-key observation, relative to its coordinate's Lebesgue measure, is

\[
\lambda_y=e^{-1}\rho\phi_1(y).
\]

At physical time u, let tau=H-u be the remaining active duration. The selected
protocol has zero clean hold. For death rate delta and continuous rate c,
define

\[
\begin{aligned}
s&=e^{-\delta\tau}, & r&=p s, &
\eta&=p\theta(1-s),\\
a&=e^{-c\tau/2}, & v&=\sigma^2+1-a^2, &
F(y)&=\phi_{\sqrt{1+\sigma^2}}(y).
\end{aligned}
\tag{1}
\]

Here r is the probability that an initial occurrence survives and is retained;
eta is the total mean number of retained future immigrants across **all**
keys. The OU convention matches the real sampler:
dZ=-(c/2)Z dt+sqrt(c)dW, with contraction a and variance 1-a^2.

## 3. Independently derived uncapped likelihood

Set kappa=epsilon lambda_y and L=(1-epsilon)exp(-eta). The absolute propagated
observation densities are

\[
\begin{aligned}
h_U(u,E;y)&=\kappa+L\eta\rho F(y),\\
h_U(u,O;y)&=\kappa+L(1-r)\eta\rho F(y),\\
h_U(u,C,z;y)&=\kappa+L\left[
 r\phi_{\sqrt v}(y-az)+(1-r)\eta\rho F(y)\right].
\end{aligned}
\tag{2}
\]

**Derivation.** Retained immigrants form a Poisson process of total mean eta.
Exactly zero retained immigrants has probability exp(-eta); exactly one
selected immigrant with noisy coordinate y has density
exp(-eta) eta rho F(y). Starting at E leaves only the latter possibility.

Starting at O, the initial occurrence cannot explain a selected-key
observation. It must not survive-and-be-retained, giving the factor 1-r.
Starting at C gives two disjoint cases: the retained ancestor explains y and
there are no retained immigrants; or that ancestor is not retained and one
immigrant explains y. Adding the whole-observation contamination gives (2).
This derivation excludes every extra retained occurrence. In particular,
exp(-eta) and 1-r must not be dropped merely because the *initial* count is
capped at one.

The code returns absolute densities. The actual association implementation
uses reference-density ratios h_U/lambda_y. At fixed y this changes log h by
the constant -log lambda_y. It does not change normalized initial laws,
coordinate derivatives, or jump likelihood ratios. The separate native-guide
tests compare log values after this conversion and compare gradients and
Hessians directly, including atomic and continuous OTHER examples from the
actual full-support reference.

### Terminal and no-jump identities

At u=H, tau=0, r=p, eta=0, a=1 and v=sigma^2. Equation (2) reduces to the
actual terminal channel:

\[
g(E;y)=g(O;y)=\kappa,\qquad
g(C,z;y)=\kappa+(1-\epsilon)p\phi_\sigma(y-z).
\tag{3}
\]

The capped and uncapped likelihoods therefore agree at the terminal time.
If delta=0, there are neither deaths nor births in this reference submodel;
the two future processes agree for all times, including their initializers.
Neither identity asserts agreement when active births encounter the cap.

## 4. A normalized Gaussian-mixture guide initializer

Evaluate the quantities in (1)–(2) at u=0. Define

\[
A=\kappa+L(1-r)\eta\rho F(y),\qquad B=Lr,
\]

so h_U(0,C,z;y)=A+B phi_sqrt(v)(y-az). Completing the square gives

\[
\phi_1(z)\phi_{\sqrt v}(y-az)
=F(y)\phi_{\sqrt{v_*}}(z-m_*),
\quad m_*=\frac{ay}{1+\sigma^2},\quad
v_*=1-\frac{a^2}{1+\sigma^2}.
\tag{4}
\]

The uncapped-guide evidence under the capped initial prior is

\[
Z_U=\pi_E h_U(0,E;y)+\pi_O h_U(0,O;y)
    +\pi_C\{A+B F(y)\}.
\tag{5}
\]

The initial atom probabilities are pi_E h_U(0,E;y)/Z_U and
pi_O h_U(0,O;y)/Z_U. The C component is a two-Gaussian **joint** density:

\[
f_U(z)=\frac{\pi_C}{Z_U}
 \left[A\phi_1(z)+B F(y)\phi_{\sqrt{v_*}}(z-m_*)\right].
\tag{6}
\]

Its component weights sum to the posterior probability of C, not to one.
`uncapped_conditioned_initial()` returns this law as `MixedGaussianLaw`, with
direct mixture sampling. This is the ideal guide initializer derived from
Pi_N h_U, evaluated in floating point. Direct mixture sampling and the
cap-conditioned rejection construction target the same ideal law; their
finite-RNG and resource behavior are separate implementation questions.
It is not the exact capped-process
initializer Pi_N h_cap unless those likelihoods agree after normalization.

The independent capped oracle likewise returns a Gaussian-mixture initial law.
With the stationary prior, the two initializers have the same Gaussian
component means and variances in C; the category/component weights differ.

## 5. What the analytic diagnostics measure

Let p_E,p_O,f_cap and q_E,q_O,f_U denote the exact capped and guide initial
laws, with f_cap and f_U their joint C densities. Their mixed-state total
variation is

\[
\operatorname{TV}(P_0^{\rm cap},P_0^U)
=\tfrac12\left[|p_E-q_E|+|p_O-q_O|
       +\int_{\mathbb R}|f_{\rm cap}(z)-f_U(z)|\,dz\right].
\tag{7}
\]

O is an atom only in this projected representation. In the full event carrier,
both initial laws have the same conditional non-selected-key/fiber distribution:
their likelihoods are constant within O. Its full-state L1 contribution is
therefore exactly |p_O-q_O|. This shared conditional distribution, together
with the explicit C density, is why (7) also gives the full initializer TV in
this submodel; projection alone would generally give only a lower bound.

`initializer_comparison()` evaluates the two atom terms and the one-dimensional
integral, and returns category probabilities, conditional C means/variances,
evidences, TV and the quadrature error estimate. QUADPACK's error output is a
numerical estimate, **not a certified interval**. No Monte Carlo samples are
used to estimate (7). This known-law initializer TV must not be confused with
an empirical terminal TV estimate from a finite CDF grid.

For C, write h_U=A+B G(z), w=B G/(A+B G), and k=a(y-az)/v. Its derivatives are

\[
\partial_z\log h_U=w k,\qquad
\partial_z^2\log h_U=-w a^2/v+w(1-w)k^2.
\tag{8}
\]

E and O have zero coordinate derivative in the projected law; a materialized
continuous OTHER event still retains its real coordinate, with derivative
zero. `score_comparison()` compares likelihood, log-likelihood, score and
Hessian with the independent capped oracle at declared times and coordinates.
The report's default query set contains five times and 21 C coordinates on
[-3,3], together with E/O queries at each time. Reported maxima are over that
finite set. They are not uniform bounds over every coordinate or time, and
neither small classifier loss nor a terminal identity establishes them.

## 6. The five predeclared sampler controls

The [prospective protocol](MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md) fixes these
controls before inspecting default results. All sampler routes use its common
eight-step grid and actual hybrid integrator.

| Control identifier | Initial law | Physical likelihood | Interpretation |
|---|---|---|---|
| `direct-posterior` | Not applicable | No evolution | Direct independent draws from the exact endpoint posterior; sampling reference control. |
| `exact-h-exact-initial` | Pi_N h_cap, normalized | Exact capped h_cap | Real integrator supplied with the correct continuous-time likelihood and initial law. |
| `exact-h-guide-initial` | Pi_N h_U, normalized | Exact capped h_cap | Changes only initialization relative to the preceding sampler control. |
| `guide-only` | Pi_N h_U, normalized | Uncapped h_U | Changes only physical likelihood relative to the preceding control; untrained G+R baseline. |
| `zero-clock-baseline` | Pi_N g, normalized | Terminal g at every time | Untrained DIR baseline, with no residual and no remaining-time propagation. |

The zero-clock initial law happens to equal the exact endpoint posterior for
the stationary reference model. Evolving it under a time-independent g does
not thereby preserve that posterior or make the route an exact conditional
sampler.

Contrasts of controls 2–3 and 3–4 isolate choices within a fixed numerical
sampler, not additive contributions to terminal TV or KL. Even the exact-h
control uses approximate splitting/Heun transitions rather than an exact Doob
transition kernel. The continuous-time oracle, actual numerical BASE law and
learned conditional law remain distinct, as explained in
[mixed conditional contract v3](../manuscript_v3/hybrid_diffusion_mixed_conditional_contract_v3.md).

The protocol separately fixes neural seeds, training/validation work, endpoint
draw counts and finite-indicator uncertainty reporting. This diagnostic does
not modify those choices, select favorable settings, or establish a method
ranking. Its two scenarios change theta and y together, not factorially.

## 7. Reproduction without Databricks

Use the local environment described in [REPRODUCING.md](../REPRODUCING.md).
The following computes analytic diagnostics only: no training, sampler
experiment, real-data access, or GPU operation. It obtains rho from the actual
full-support reference instead of rounding it to a nominal value.

```python
from fractions import Fraction
import json

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import (
    ContinuousFiberInitializationDiagnostic,
)

key = PhysioStateKey(3, "HR", "POSITIVE")
reference = TrainInformedMetadataReference(
    FactorizedMetadataReference("R3-PHYS"),
    (FactoredEvent(key, 0.2),), beta=Fraction(1, 4),
)
rho = float(reference.mass(key).as_fraction())
spec = ContinuousFiberSpec(
    theta=0.8, observation_value=0.7,
    type_probabilities=(1.0 - rho, rho),
)
diagnostic = ContinuousFiberInitializationDiagnostic(spec)
print(json.dumps(diagnostic.initializer_comparison(), indent=2))
```

The second predeclared scenario changes only the displayed scenario settings
to `theta=2.5, observation_value=1.4`; all other protocol choices remain fixed.
The full analytic report, including the bounded score grid, is available from
`diagnostic.report()`. Each returned law supports `sample(rng)` with an explicit
NumPy generator and returns a projected category/coordinate pair.

Run the focused correctness and native-guide checks from the repository root:

```bash
python -m pytest -q tests/unit/test_continuous_fiber_initialization_diagnostic.py
```

The independent diagnostic module imports neither the native guide nor the
learned sampler. Its separate tests deliberately import the native guide for
cross-checking, so those tests additionally require the repository's Torch
test environment. Default multi-seed experiment execution is governed by the
prospective protocol and is not implicitly launched by these analytic calls.
