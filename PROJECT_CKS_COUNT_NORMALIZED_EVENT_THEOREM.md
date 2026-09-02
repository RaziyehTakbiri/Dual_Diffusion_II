# Count-normalized-event CKS theorem and Gate-A route disposition

**Reported date:** 2026-08-30  
**Package state:** `GENERIC_CKS_THEOREM_PROVED_EXACT_DOMAIN_INSTANCE_PENDING`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Project-control predicate:** `GATE_A_CKS_COUNT_NORMALIZED_EVENT_ROUTE_MATHEMATICALLY_VIABLE`  
**Exact Gate-A metric checkbox:** `OPEN`  
**B04:** `OPEN`

## 1. Authority, scope, and additive paths

The normalized visible user instruction for the overnight work is exactly:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

It authorizes substantial continued local project work during the user's
absence. The coordinator assigned this bounded theory lane: decide the frozen
count-channel plus normalized-event-measure CKS route, construct one additive
proof package if it is viable, or freeze a no-go counterexample if it is not.
Neither instruction authorizes a network request, source contact, protected-data
access, entropy, training, runtime/scientific execution, result generation,
submission, or a tracker edit by this package. Raw transport bytes, HTML-space
transport content, timestamps, the conversation envelope, account identity,
and any cryptographic user signature are unbound.

The four additive paths are:

1. `PROJECT_CKS_COUNT_NORMALIZED_EVENT_THEOREM.md`;
2. `research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json`;
3. `research/diagnostics/manuscript_v3_cks_count_normalized_event_theorem_v1.py`;
4. `tests/unit/test_manuscript_v3_cks_count_normalized_event_theorem_v1.py`.

No existing preregistration, manuscript, evidence ledger, completion timetable,
runtime module, or scientific result is modified. The companion implementation
is a read-only package validator with a pure exact-arithmetic finite-alphabet
oracle. It is not a production metric implementation.

## 2. Why this package is needed

The static selection freeze chose, for development, an explicit count channel
orthogonal to a characteristic normalized-event-measure channel. It listed the
empty, unequal-count, and multiplicity obligations, but correctly left
characteristicness and primary-metric selection unproved.

The current manuscript still displays a different preliminary formula:

```text
mu_x = integral k_E(e, .) x(de)
k_Gamma(x,y) = exp(-||mu_x-mu_y||^2/(2 sigma^2)).
```

That raw, unnormalized counting-measure expression is not the selected route.
In particular, characteristicness of `k_E` on probability measures alone does
not by itself state injectivity for arbitrary finite signed measures. This
package does not silently reinterpret that display. It proves the selected
count-normalized route below and requires a later manuscript/preregistration
amendment to use the exact formula before CKS can be admitted.

The distinction is necessary, not cosmetic. On the two-point event space
`E={u,v}`, take the rank-one event kernel `k_E(e,f)=g(e)g(f)` with `g(u)=1`
and `g(v)=2`. Its probability mean is `2-p({u})`, so it is characteristic on
probability measures on this two-point space. Nevertheless, the manuscript's
raw finite-measure embedding sends both `2 delta_u` and `delta_v` to the same
RKHS element. Thus event-kernel characteristicness on probabilities does not
rescue the preliminary raw formula when the cap is at least two. The selected
count-normalized construction separates that pair through its count channel.

## 3. Objects and assumptions

Let `(E, Sigma)` be the admitted transformed event space and let `N >= 1` be a
finite configuration cap. Write `Gamma_N(E)` for counting measures

```text
x = sum_{i=1}^n delta_{e_i},   0 <= n <= N,
```

where order is quotiented out and repeated `e_i` values are retained as
multiplicity. The empty counting measure is denoted `0`.

The theorem has the following exact assumptions.

| ID | Assumption | Purpose |
|---|---|---|
| `K1` | `E` is standard Borel and `Gamma_N(E)` carries the finite-counting/quotient Borel structure. | Makes configuration laws and the pullback kernel measurable. |
| `K2` | `k_E` is bounded, measurable, positive definite, and has a separable real RKHS `H_E`. | Makes all event mean embeddings and the outer Hilbert construction well defined. |
| `K3` | The probability mean map `p -> m_p := integral k_E(e,.) p(de)` is injective on all Borel probability measures on `E`. | This is the required event-kernel characteristicness; finite empirical tests cannot replace it. |
| `K4` | Count and event scales `a` and `b` are fixed finite real numbers with `a>0` and `b>0`. | Zero scale would erase a required channel. |
| `K5` | The outer configuration bandwidth `sigma` is fixed and satisfies `0<sigma<infinity`. | Required by the Gaussian characteristicness argument. |
| `K6` | The exact event representation is permutation invariant and injective before `k_E` is applied; schema changes invalidate the instance certificate. | Prevents type, mark, time, mask, or structural-zero aliases. |
| `K7` | Any training-fitted event preprocessing or bandwidth is selected without held-out/test information and is frozen before scoring. | Preserves the prospective evaluation boundary; it is not needed for the algebra once positive values are fixed. |

A sufficient future construction for `K3`, not an already admitted domain
instance, is an injective Borel encoding `T:E -> R^d` and

```text
k_E(e,f) = exp(-||T(e)-T(f)||^2/(2 tau^2)),   0<tau<infinity.
```

For standard-Borel `E`, an injective Borel `T` has a measurable inverse on its
image. The Euclidean Gaussian is characteristic, so its pullback is
characteristic. A future domain certificate must still bind the exact type
roster, masks, time/mark transforms, scaling, `d`, `tau`, cap, horizon,
segmentation, overflow rule, and structural-zero restrictions. Merely naming a
Gaussian is not that certificate.

## 4. Selected configuration embedding

For `x in Gamma_N(E)`, let `n_x=x(E)`. If `n_x>0`, define the normalized
empirical probability measure `p_x=x/n_x`; for the empty configuration there is
no invented empirical probability. In the orthogonal Hilbert direct sum
`H := R direct-sum H_E`, define

```text
Phi(x) = (a n_x, b m_{p_x})   when n_x>0,
Phi(0) = (0, 0).
```

The first coordinate is count times one fixed constant unit direction,
orthogonal to the event RKHS. The second channel is normalized by the count.
The configuration kernel is the exact Gaussian pullback

```text
k_Gamma(x,y)
  = exp(-||Phi(x)-Phi(y)||_H^2/(2 sigma^2)).
```

No random feature, Nyström approximation, rounded feature cache, or learned
noninjective bottleneck is part of this theorem.

## 5. Lemma 1: `Phi` is injective on finite counting measures

Suppose `Phi(x)=Phi(y)`. Equality of the first coordinates and `a>0` give
`n_x=n_y=:n`.

- If `n=0`, both counting measures are empty, hence `x=y=0`.
- If `n>0`, equality of the event coordinates and `b>0` give
  `m_{p_x}=m_{p_y}`. Assumption `K3` gives `p_x=p_y`. Multiplying the two
  probability measures by the common integer `n` gives `x=y`.

Thus `Phi` is injective. This argument explicitly covers all frozen edge cases:

- empty versus nonempty is separated by the count coordinate;
- unequal total masses are separated by the count coordinate even when their
  normalized empirical measures coincide;
- equal-valued duplicates survive because `p_x` contains their empirical mass;
- equal-count configurations with different multiplicities have different
  empirical probability measures and are separated by `K3`; and
- order never enters, because `x` is a counting measure.

Equivalently, for every distinct admissible pair `x,y`, the combined channel
detects the nonzero counting-measure difference `x-y`. This is a pairwise
detection statement for the nonlinear normalized map; it is not a claim that
`Phi` is linear on arbitrary signed measures.

## 6. Lemma 2: the Gaussian is characteristic on a separable Hilbert space

Let `H` be any separable real Hilbert space, let `sigma` be finite and strictly
positive, and define

```text
G_sigma(u,v)=exp(-||u-v||^2/(2 sigma^2)).
```

Then `G_sigma` is characteristic on Borel probability measures on `H`.

To prove it, let `nu=P-Q` and suppose the Gaussian kernel means of `P` and `Q`
are equal. Evaluating their difference at every `z in H` gives

```text
integral G_sigma(u,z) nu(du)=0.
```

Define the finite signed measure

```text
rho(du)=exp(-||u||^2/(2 sigma^2)) nu(du).
```

After multiplying the preceding identity by
`exp(||z||^2/(2 sigma^2))`, one obtains

```text
integral exp(<u,z>/sigma^2) rho(du)=0                 (1)
```

for every `z`. The integral is absolutely finite, because completing the square
gives

```text
exp(-||u||^2/(2 sigma^2)+<u,z>/sigma^2)
  <= exp(||z||^2/(2 sigma^2)).
```

Project `rho` onto any finite span of Hilbert coordinates. Equation (1) says
that the projected finite signed measure has zero bilateral Laplace transform
everywhere. Its Gaussian tail bound makes that transform entire; the identity
theorem followed by uniqueness of the Fourier transform gives a zero projected
measure. For a countable orthonormal basis of separable `H`, finite-coordinate
cylinders generate the Borel sigma-field. Hence `rho=0`, and the strictly
positive weighting density then gives `nu=0`. Therefore `P=Q`.

This proof does not require compactness or finite-dimensionality of `H`.

## 7. Theorem 1: `k_Gamma` is characteristic

Under `K1`--`K6`, `Phi` is a measurable Borel injection from the standard-Borel
configuration space into separable `H`. Lemma 2 makes the Gaussian
characteristic on `H`. If two configuration laws have equal `k_Gamma` mean
embeddings, their `Phi` pushforwards are equal; injectivity and the measurable
inverse on the Borel image then give equality of the original laws. Thus
`k_Gamma` is characteristic on all Borel probability laws on
`Gamma_N(E)`.

The proof applies to any finite cap, including a cap whose exact value is bound
later. It does not certify that either current domain has supplied an exact cap,
event schema, or `K3` certificate.

## 8. Theorem 2: CKS is a strictly proper loss

For a predictive configuration law `P` and realized target configuration `y`,
define, up to the target-only diagonal constant,

```text
CKS(P,y)
  = E[k_Gamma(X,X')] - 2 E[k_Gamma(X,y)],
```

where `X,X'` are independent with law `P`. For target law `Q`, boundedness of
`k_Gamma` makes every expectation finite and

```text
E_{Y~Q}[CKS(P,Y)] - E_{Y~Q}[CKS(Q,Y)]
  = E_PP[k_Gamma] - 2 E_PQ[k_Gamma] + E_QQ[k_Gamma]
  = MMD^2_{k_Gamma}(P,Q).
```

The right side is nonnegative and, by Theorem 1, equals zero exactly when
`P=Q`. Therefore CKS is strictly proper in the loss convention: **lower is
better**.

For the preregistered paired estimand

```text
primary_score_direct - primary_score_guide,
```

positive values favor the guide. Strict propriety is a population
identification result; it does not imply that the guide will empirically beat
the direct method, supply an effect size, or establish power.

For `R>=2` conditionally independent draws from one method, the ordered-pair
U-statistic

```text
1/[R(R-1)] sum_{r!=s} k_Gamma(X_r,X_s)
  - 2/R sum_r k_Gamma(X_r,y)
```

is unbiased for `CKS(P,y)`. Common random numbers across the direct and guide
methods do not change either marginal expectation, but within-method draws must
still satisfy the frozen conditional-iid law. Two draws are a mathematical
minimum, not the still-open final Monte Carlo allocation.

## 9. Hostile necessity audit

The following changes invalidate the theorem or its project application.

| Mutation | Consequence |
|---|---|
| Remove the count channel | `delta_e` and `2 delta_e` have identical normalized event channels. |
| Replace count by only an empty/nonempty flag | `delta_e` and `2 delta_e` again collide. |
| Set `a=0` or `b=0` | Unequal counts or equal-count event differences, respectively, can disappear. |
| Use a noncharacteristic event kernel | Distinct empirical probability measures can share `m_p`. |
| Drop multiplicity before normalization | Configurations differing only in repeated-event mass can collide. |
| Let `sigma` be zero, infinite, nonfinite, or outcome-selected | The outer theorem or the prospective freeze fails. |
| Substitute finite random features without a separate theorem | Feature collisions can destroy characteristicness. |
| Alias event types, masks, transformed times, or marks | The future event encoding is not injective. |
| Use fewer than two within-method conditional draws in the displayed estimator | The unbiased self-similarity U-statistic is undefined. |
| Fit preprocessing or bandwidth from test outcomes | Mathematical positivity may survive, but the preregistered evaluation is invalid. |

The companion pure oracle uses a finite categorical event alphabet and exact
rational arithmetic. In that special case the event mean is the empirical
frequency vector, and it computes

```text
a^2 (n_x-n_y)^2 + b^2 ||freq_x-freq_y||_2^2.
```

It qualifies the empty, unequal-count, proportional-duplicate, equal-count
duplicate, permutation, and zero-scale refusal cases. It is an executable
counterexample/witness oracle, not a numerical proof of the infinite-space
theorem.

## 10. Exact project effect and nonclosure

After the quartet and independent proof/code audit pass, the following additive
project-control predicate is supportable:

```text
GATE_A_CKS_COUNT_NORMALIZED_EVENT_ROUTE_MATHEMATICALLY_VIABLE = true.
```

This is substantive route disposition: the selected construction has a complete
generic characteristicness and strict-propriety proof, rather than merely a
plausibility note. It rules out a no-go based on empty configurations,
unequal mass, duplicates, or the outer Gaussian.

The proof establishes the orientation of this candidate CKS loss, and it is
consistent with the already hash-bound preregistration prose. It does not close
`F106`: that project field remains conditional on the final admitted primary
metric instance and is separately controlled. The stronger Gate-A checklist
item, `B04`, and every field `F105`--`F113` remain open. In particular, this
package supplies none of the following:

- an admitted exact PhysioNet or Retail event schema/kernel instance;
- the final cap, transforms, scaling, event bandwidth, or configuration
  bandwidth;
- a production implementation or implementation hash;
- the final aggregation unit or conditional draw count;
- a minimum meaningful effect, real--real floor, confidence procedure, or
  multiplicity rule;
- a real pilot, power result, data access, runtime, or scientific outcome.

The exact Gate-A timetable checkbox must remain unchecked until the domain
instances satisfy `K1`--`K7`, the selected formula replaces the preliminary
manuscript display, the production implementation is code-matched, and an
independent exact-instance audit passes. `B04` additionally needs every
remaining metric/effect field.

## 11. Publication and anonymity boundary

This internal evidence package may inform a later publication-safe theorem
derivative. The raw authority text, internal paths, hashes, byte counts, and
audit receipts are not manuscript content. A fresh scientific proof review,
code match, and anonymity review are required before publication. No absolute
user path, credential, token, cookie, person identifier, dataset row, protected
outcome, or scientific result is stored here.

## 12. Completion rule

The route-viability predicate may be consumed only after:

1. the human theorem, machine record, validator, and hostile tests are mutually
   hash-bound and pass from the workspace and an unrelated working directory;
2. the exact finite-oracle tests pass on every available supported Python
   interpreter without cache artifacts; and
3. an independent reviewer returns no P0, P1, or P2 defect in the proof,
   strict-propriety algebra, field effect, nonclaims, or custody.

Failure of any condition leaves the predicate unconsumed. Success still
preserves the prior 172-field, 12-blocker state.
