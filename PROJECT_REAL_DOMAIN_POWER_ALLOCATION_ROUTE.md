# Real-domain power and allocation route v1

**Reported date:** 2026-08-30  
**State:** `REAL_DOMAIN_POWER_ALLOCATION_ROUTE_FROZEN_AND_SYNTHETICALLY_QUALIFIED_AWAITING_METRIC_MARGIN_PILOT_AND_COMPUTE`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** static power/allocation route with no scientific effect  
**Sole control predicate:** `POWER_AND_ALLOCATION_ROUTE_DEPENDENCY_AUDIT_VALIDATED`

## 1. Exact disposition

This four-file package freezes and synthetically qualifies one possible route
for a future real-domain power and allocation review. It does not complete
that review. It performs no source contact, browsing, acquisition, pilot,
data inspection, held-out access, model run, scientific execution, or tracker
edit. Its scientific effect is exactly zero.

The package closes no preregistration field and no blocker. In particular,
`B07`, `F060`, `F061`, `F110`, and every field from `F128` through `F138`
remain open. Every machine value for those fields remains typed `null`. The
values 0.05
familywise alpha and 0.90 joint power are planning candidates only; they are
not values of `F128` or `F129` and cannot be copied into the preregistration
without a later pre-outcome review and versioned freeze.

The package's only pass statement is that its dependency audit, exact
calculator contract, synthetic test vector, future simulation route, custody,
and nonclaim boundary are internally consistent. A pass is not evidence that
the real-domain study is powered.

## 2. Authority boundary

The bound normalized visible user authority is exactly:

> Alright, sounds good. Go ahead then.

Its UTF-8 length is 36 bytes and its SHA-256 is
`834e4a9458adde27cebea9341c11ef09e49dc04dbfb2d7b9a05ed9108a16413b`.
Only the normalized visible sentence is bound. Raw transport bytes, trailing
transport content, the conversation envelope, account identity, timestamp,
and cryptographic user authentication are not bound.

That authority covers this additive static package. It does not authorize a
tracker edit, external contact, web use, source/license/governance inquiry,
data access, pilot, entropy, runtime operation, or scientific execution.

## 3. Exact dependency audit

| Item | Current status | Value frozen here | Effect of this package |
|---|---|---:|---|
| `B07` power analysis and seed schedule | OPEN | none | remains open |
| `F060` Retail temporal rule | OPEN | `null` | remains open |
| `F061` train/validation/test allocation | OPEN | `null` | remains open |
| `F110` minimum meaningful decision threshold | OPEN | `null` | future `delta0`; remains open |
| `F128` familywise alpha | OPEN | `null` | 0.05 is candidate-only |
| `F129` target power | OPEN | `null` | 0.90 is candidate-only |
| `F130` minimum effect used for power | OPEN | `null` | requires frozen metric and margins |
| `F131` pilot source | OPEN | `null` | requires a later blinded train/validation receipt |
| `F132` independent training-seed count | OPEN | `null` | calculator route alone cannot select it |
| `F133` seed values or immutable receipt | OPEN | `null` | no entropy or registry created |
| `F134` natural-group counts by domain | OPEN | `null` | requires admitted snapshots/splits |
| `F135` conditioning cases per group | OPEN | `null` | requires allocation review |
| `F136` conditional draws per case | OPEN | `null` | requires allocation review |
| `F137` hierarchical paired formula | OPEN | `null` | candidate analysis is not a closure |
| `F138` confidence-interval resamples | OPEN | `null` | requires fixed simulation/MC-error design |

The unresolved primary metric prevents choosing its rigorous score range
`W`. The future `delta0` is exactly the still-open F110 minimum-meaningful
decision threshold used as the null margin. The future `delta1` is exactly the
still-open F130 planning alternative/minimum effect used for power. Neither is
selected here, and any later admitted values must satisfy `delta1 > delta0`.
The unresolved margins therefore prevent determining the strict gap
`delta1 - delta0`. The unobserved train/validation pilot and compute budget
prevent selecting a seed/group/case/draw allocation. Therefore a real seed
count cannot truthfully be frozen now.

## 4. Distribution-free seed-count calculator

### 4.1 Inputs and refusal boundary

The pure-standard-library calculator accepts only exact Python integers and
`fractions.Fraction` values:

- `W > 0`, the width of one bounded paired seed-level statistic;
- `0 < alpha_star < 1`, the per-domain planning type-I tail probability;
- `0 < beta_star < 1`, the per-domain planning type-II tail probability;
- `delta0`, the future F110 minimum-meaningful decision threshold/null margin;
  and
- `delta1`, the future F130 planning alternative/minimum effect used for
  power.

It refuses booleans, binary floats, decimal strings, and all other numeric
types. It also refuses `delta1 <= delta0`. Equality cannot establish positive
power for a lower confidence bound that must exceed the same margin.

After a supplied integer or `Fraction` is normalized, both its numerator and
denominator must have bit length at most 4096. A component with bit length
4097 or greater is refused before the certificate is constructed. This is an
explicit resource bound on the pure calculator, not a mathematical claim that
larger exact rationals are invalid.

### 4.2 Target formula

For gap `g = delta1 - delta0 > 0`, the target sufficient count is

```text
ceil[ W^2 (sqrt(ln(1/alpha_star)) + sqrt(ln(1/beta_star)))^2
      / (2 g^2) ].
```

The code does not evaluate this expression with floating point. For any
`x >= 1`, it power-of-two normalizes `x = 2^k y`, where `1 <= y < 2`, and uses

```text
ln(y) = 2 sum_{n=0}^infinity z^(2n+1)/(2n+1),
z = (y-1)/(y+1).
```

It sums the first 64 terms exactly as rational numbers. The omitted positive
tail is bounded above exactly by

```text
2 z^(2N+1) / ((2N+1)(1-z^2)),  N = 64.
```

The same construction bounds `ln(2)`, so both log intervals are rational and
outward-certified. If `A` and `B` are the exact upper endpoints, then

```text
(sqrt(A) + sqrt(B))^2 <= 2(A+B).
```

The returned integer is consequently the exact ceiling of the conservative
rational alternative

```text
W^2 (A+B) / g^2.
```

It is at least the target sufficient count; no float is silently treated as
proof. Conservatism is explicit.

### 4.3 Scope of the guarantee

The bound is a fixed-`N`, bounded-variable, distribution-free route for
independent training-seed means conditional on already frozen held-out groups
and cases. It does not establish a superpopulation guarantee over natural
groups. Any such claim would require a separate, proven independent-group
route. Seed-by-group cells must not be treated as IID observations.

### 4.4 Synthetic qualification vector

For a normalized CKS *example only*, a single-method score in `[-2,1]` gives a
paired direct-minus-guide score in `[-3,3]`, hence `W = 6`. With planning
`alpha_star = 1/40`, `beta_star = 1/20`, `delta0 = 0`, and `delta1 = 1`, the
exact conservative calculator returns 241 training seeds.

This proves that the calculator and certificate machinery operate on one
fully specified bounded synthetic scenario. It does not select CKS, prove CKS
characteristicness, choose either margin, select 241 real training seeds, or
close any power field.

## 5. Candidate family logic

The frozen candidate family contains exactly `R3-PHYS` and `R4-RETAIL`.
Candidate familywise alpha is `1/20` (0.05), candidate target joint power is
`9/10` (0.90), and the candidate multiplicity rule is Holm for two hypotheses.

For conservative planning, each domain uses `alpha_star = 1/40`. Requiring
each domain's failure probability to be at most `beta_star = 1/20` gives joint
success probability at least `1 - 2/20 = 9/10` by a union bound. No independence
between domain success events is assumed. Confirmatory inference still uses
the exact frozen Holm procedure, not a post hoc planning approximation.

These are candidates because the primary metric, its direction and range,
F110/`delta0`, F130/`delta1`, pilot object, and compute budget remain
unresolved. They must not be represented as preregistration values.

## 6. Pairing and analysis contract

The future design is fixed-`N` and paired:

- training seeds are replication units;
- natural groups and cases retain their hierarchy;
- direct and guide are paired at the same seed, group, case, and draw address;
- conditional draws are aggregated inside a case and are not independent
  replicates;
- seed-by-group cells are not treated as IID;
- a candidate hierarchical paired bootstrap resamples seeds and groups, then
  cases within groups, while preserving direct/guide pairing; and
- both `R3-PHYS` and `R4-RETAIL` must exceed the later frozen effect in the
  favorable direction with multiplicity-adjusted one-sided lower bounds.

No post-outcome metric, margin, allocation, formula, or multiplicity change is
permitted. No seed top-up, replacement, favorable-seed selection, or
sequential stopping is permitted.

The hierarchical bootstrap description is a route to qualify later, not a
value of `F137`. Exact weighting, degenerate-stratum rules, resample count,
confidence allocation, and fallback/refusal behavior remain to be frozen.

## 7. Future simulation-qualified allocation route

This section freezes a future procedure; it does not run that procedure.

1. Select and formally validate one primary metric before held-out access.
   Freeze its favorable direction and exact bound `W`; populate F110 as the
   exact null-margin `delta0` and F130 as the exact planning-alternative
   `delta1`, with `delta1 > delta0`.
2. Create a blinded train/validation-only pilot receipt made from centered
   paired residual objects. Pilot seeds must be disjoint from the confirmatory
   seed registry. Test outcomes are forbidden.
3. Before simulation, enumerate a finite literal grid over training seeds,
   natural groups, cases per group, draws per case, bootstrap resamples, and
   total compute. Also freeze the number and addresses of simulation trials,
   the exact Bernoulli success indicator for every condition, and a literal
   immutable simulation-trial stream/seed registry. The registry must be
   custody-bound, pairwise disjoint across every grid-point, condition, and
   trial ordinal, and disjoint from pilot and confirmatory seed registries.
4. Simulate the crossed seed-by-group/case paired design. Preserve the same
   seed, group, case, and draw addresses for direct and guide. Draws remain
   within-case Monte Carlo precision, never replicate inflation.
5. Evaluate the three named structural null truth patterns: both domains null,
   `R3` null with `R4` alternative, and `R4` null with `R3` alternative. These
   three names are not claimed to exhaust a composite-null nuisance space.
   Before execution, either supply a formal least-favorable/monotonicity proof
   showing that these patterns cover the composite null, or freeze a finite
   literal nuisance grid covered by the simultaneous Monte Carlo error
   allocation. Otherwise the route terminates no-go. Apply the exact planned
   Holm decision rule.
6. Evaluate joint power only where both domains are at their frozen
   alternatives. Include at least three marginal-preserving stress routes:
   event-count destruction, association-dependence destruction, and temporal
   order destruction.
7. Use simultaneous Clopper-Pearson upper bounds for familywise error over
   every grid point and admitted null condition. Use a simultaneous
   Clopper-Pearson lower bound for joint power over every required alternative
   and stress route. Each bound requires, within its condition, independent
   Bernoulli trials generated under a proved trial law; distinct addresses
   alone do not prove independence. Freeze and custody-bind the disjoint
   immutable trial-stream registry and the Monte Carlo confidence-error
   allocation across the entire finite collection before running.
8. A grid point passes only if every familywise-error upper bound is no larger
   than the frozen familywise alpha and every joint-power lower bound is no
   smaller than the frozen target power.
9. Select minimum total compute among passing points, with a literal frozen
   lexicographic tie break. There is no grid expansion, top-up, retry,
   replacement, or favorable selection after results.
10. If no grid point passes, terminate with no-go. A new pre-outcome version is
    required; the failed grid cannot be repaired after observing its results.

This route requires the metric/bound, F110/`delta0`, F130/`delta1`, pilot
receipt, finite grid, compute budget, exact Clopper-Pearson confidence
allocation, a proved within-condition independent Bernoulli trial law, a
disjoint immutable trial-stream/seed registry with custody, a literal
confirmatory seed registry, composite-null coverage by proof or a frozen
nuisance grid, and independent review before it can run.

## 8. One-way immutable inputs

The validator reopens and verifies exactly these current predecessor bytes:

| Ordinal | Role | Bytes | SHA-256 |
|---:|---|---:|---|
| 0 | execution preregistration human | 22,491 | `a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e` |
| 1 | execution preregistration machine | 39,771 | `edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706` |
| 2 | preexecution closure human | 14,938 | `fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d` |
| 3 | preexecution closure machine | 24,571 | `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` |
| 4 | precontact candidate human | 17,965 | `ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f` |
| 5 | precontact candidate machine | 23,932 | `95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be` |
| 6 | precontact candidate validator | 46,460 | `6bdfe3c943c8238d88dc5fba908918d9304ab9f377517a483c65cfac887a39dc` |
| 7 | precontact candidate hostile test | 27,389 | `40ba6642f81323fb9254520113697785513bb705e72232731657ae1c481d2856` |

All are required to be regular mode-0644, single-link files with a trailing
line feed. The bindings are one-way: this package does not mutate or authorize
mutation of any predecessor. Its machine record additionally binds the exact
bytes of this human route, the validator/calculator, and the hostile unit test
without recursively binding the machine record into itself.

## 9. What can and cannot close now

What is complete is narrow: an exact, conservative calculator implementation;
its proof contract; one synthetic qualification vector; a candidate
multiplicity/joint-power logic; a crossed-pairing analysis boundary; a finite
simulation-selection protocol; strict refusal and anti-drift rules; and
immutable custody validation.

What remains open is the scientific design: primary metric, rigorous bound,
effect margins, train/validation pilot, group/case/draw counts, compute budget,
bootstrap formula details, resample count, literal seed registry, split
allocation, Retail temporal rule, and independent review. Until those items
are frozen without held-out outcomes, `B07` cannot close and real-domain
execution remains unauthorized.
