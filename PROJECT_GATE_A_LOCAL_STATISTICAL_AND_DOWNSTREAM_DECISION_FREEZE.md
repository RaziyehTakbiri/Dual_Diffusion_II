# Gate-A local statistical and downstream-decision freeze

**Date:** 2026-08-30  
**State:** `GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISIONS_FROZEN`  
**Global state:** `DRAFT_NOT_EXECUTABLE`  
**Scientific execution:** none

## 1. Scope and authority

The normalized visible instruction is:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

This instruction authorizes autonomous local project work. The earlier standing
instruction, `Sounds great. Go ahead and finish them in parallel. Mark all the
completed tasks as the end.`, separately authorizes tracker maintenance for
independently validated completions. Neither instruction authorizes
network or source contact, data acquisition or access, entropy, runtime or
scientific execution, training, procurement, submission, or claim promotion.
Raw transport bytes, trailing HTML-space representation, account identity,
timestamp, and cryptographic authentication are unbound. The exact paths,
schema, statistical choices, and failure-state names are agent-selected
pre-outcome decisions.

This package is additive. It does not modify the execution preregistration,
pre-execution closure, power-route, pilot-route, runtime, or result artifacts.
It resolves exactly five locally decidable pre-execution fields and one Gate-A
downstream-behavior item. All other fields and all blockers remain open.

## 2. Exact additive field closures

The baseline active view has 172 unresolved fields: 166 pre-execution and six
post-execution. This freeze resolves exactly the following five pre-execution
fields:

| Field | Frozen value | Reason |
|---|---|---|
| `F107` aggregation unit | `NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_OF_PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE` | already fixed by the preregistered estimand; draws and cases remain nested rather than becoming replicates |
| `F113` multiplicity rule | `TWO_DOMAIN_ONE_SIDED_HOLM_STEP_DOWN_FWER_1_OVER_20` | controls the exact R3/R4 family while retaining separate domain decisions |
| `F128` familywise alpha | exact rational `1/20`, JSON projection `0.05` | fixed conventional confirmatory error budget, selected before outcomes |
| `F129` target power | exact rational `9/10`, JSON projection `0.9` | joint probability that both domain tests pass, not marginal per-domain power |
| `F148` infrastructure-rerun predicate | `NEVER_TRUE_NO_INFRASTRUCTURE_RERUN` | eliminates favorable-retry ambiguity; every infrastructure abort is terminal for the frozen route |

After this additive closure, unresolved counts are exactly 161 pre-execution,
six post-execution, and 167 total. Theory/statistics has 49 open and five
closed fields; method/runtime/compute remains 65/0; data/governance remains
52/0; final sealed freeze remains 1/0. All 12 blockers remain open because no
blocker is fully discharged.

No value is supplied for the primary metric, favorable direction, draws,
minimum effect, real--real floor, confidence method, pilot source, seed count or
values, group/case/draw counts, analysis formula, resample count, failure-rate
ceiling, or compute capacity.

## 3. Exact two-domain multiplicity rule

The family contains exactly `R3-PHYS` and `R4-RETAIL`. For each domain, the
future frozen primary analysis must produce a valid one-sided p-value for

```text
H_d: theta_d <= delta0_d
versus
A_d: theta_d > delta0_d.
```

At exact familywise alpha `1/20`, order the two p-values increasingly. An exact
tie is ordered `R3-PHYS` before `R4-RETAIL`. Reject the first ordered hypothesis
only when `p_(1) <= 1/40`. Reject the second only when the first was rejected
and `p_(2) <= 1/20`. Equality passes because the inequalities are closed.

The package's pure helper implements only this exact decision algebra on
caller-supplied exact rational p-values. It does not construct p-values or
confidence intervals. F112 remains open: its future confidence procedure must
be a valid inversion or simultaneous-bound construction compatible with this
Holm family. C20 still requires both domains to reject and separately exceed
their frozen effect requirements with multiplicity-adjusted bounds; one domain
cannot rescue the other.

For planning, `F129 = 9/10` means the joint success event
`PASS_R3 AND PASS_R4`. It is not permission to call two marginal 0.90 power
claims joint 0.90. The existing conservative candidate route may require each
domain's failure probability to be at most `1/20`, which guarantees joint power
at least `9/10` by the union bound without assuming independence. Final power
still requires the metric, margins, pilot, complete allocation, simulation
qualification, and compute capacity.

## 4. Exact R1/R2 downstream behavior

The R1 phase order is immutable:

```text
R1_RANK -> R1_EXACT -> R1_PRIMARY -> R1_METRICS -> R1_CONTROLS.
```

Each later phase is eligible only after an exact accepted `PASS` receipt for
the preceding phase. Five accepted phase-PASS receipts yield `R1_PASS` and make
R2 eligible, subject to every other frozen prerequisite.

For any R1 phase:

- `FAIL` produces terminal `R1_FAIL`;
- `HOLD` produces terminal `R1_HOLD`;
- `INFRA_ABORT` produces terminal `R1_INFRA_ABORT`; and
- an invalid, missing, noncanonical, cross-attempt, or custody-mismatched receipt
  produces terminal `R1_PROTOCOL_INVALID`.

In every non-PASS R1 branch, all later R1 phases and R2/R3/R4 are permanently
`NOT_APPLICABLE` for this route. No retry, resumption, replacement, top-up,
threshold/seed/config change, alternate route, or recovery launch is allowed.
The receipt and all already completed work remain reportable evidence.

R2 runs only after `R1_PASS`. Accepted `R2_PASS` makes R3 and R4 eligible only
subject to all other gates and their already precommitted dual-domain launch
contract. `R2_FAIL`, `R2_HOLD`, `R2_INFRA_ABORT`, or `R2_PROTOCOL_INVALID`
makes both real-domain slots permanently `NOT_APPLICABLE` for this route. An R1
or R2 failure never activates another manuscript route or replacement domain.

The frozen `F148` predicate is never true. Therefore an infrastructure abort
is not rerun even if no usable output appears. This is stricter than the
preregistration's optional future infrastructure-rerun allowance and removes
the need to decide whether an abort was favorable. F149, the admissible
failure-rate ceiling, remains open and must be set before execution.

## 5. Pure decision helpers and qualification

The companion module exposes two pure helpers:

1. `holm_two_domain`, which accepts exactly one rational p-value per named
   domain and returns the frozen order, thresholds, and rejection map; and
2. `downstream_state`, which accepts a contiguous R1 outcome prefix and an
   optional R2 outcome and returns exact eligibility, terminal state, and
   `NOT_APPLICABLE` roster.

The helpers reject binary floats, booleans, unknown domains/outcomes, gaps,
R2-before-R1, outcomes after a terminal branch, and oversized rational
components. They perform no file write, network access, process launch,
entropy, data operation, training, or scientific execution. Tests use only
synthetic caller-supplied values and temporary copies of the package for
hostile custody checks.

## 6. Nonclaims and next dependencies

This freeze does not close B04, B05, or B07. It does not select CKS, prove
characteristicness, choose the effect margin, validate a confidence procedure,
observe pilot variance, select any real seed count or registry, reserve compute,
admit a domain, access test data, or execute R1/R2. The Gate-A item
"R1-failure and R2-failure downstream behavior is frozen now" may close only
after exact independent review of this quartet. Every other Gate-A item remains
open unless separately supported.

This package is internal evidence only. Authority text, hashes, paths, and
operational state-machine details are excluded from an anonymous/public
submission. A publication-safe derivative and fresh anonymity audit are
required before reuse.
