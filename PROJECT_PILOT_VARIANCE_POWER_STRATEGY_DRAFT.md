# Pilot-Variance and Power-Strategy Draft

**Date:** 2026-08-30  
**State:** `PILOT_VARIANCE_AND_POWER_STRATEGY_DRAFT_FROZEN_AWAITING_METRIC_PILOT_AND_COMPUTE`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`  
**Project-control predicate:** `PILOT_VARIANCE_AND_POWER_STRATEGY_DRAFT_VALIDATED`

## 1. Scope and authority

This additive package completes only the Solo-Block-3 pilot-variance and
power-strategy **draft**. It does not populate any preregistration field, close
any blocker, run a pilot, select a metric or effect, generate a seed, inspect a
dataset, contact a source, access held-out material, reserve compute, or execute
science.

The normalized visible instruction is:

> Sounds great. Go ahead and finish them in parallel. Mark all the completed tasks as the end.

That instruction authorizes local Block-2/Block-3 drafting and later tracker
maintenance for independently validated completions. It does not authorize
external contact, data access, entropy, runtime execution, training, scientific
claims, or submission. Raw transport bytes, the conversation envelope, trailing
HTML-space representation, account identity, and timestamp are unbound. Exact
paths, schemas, formulas, and refusal rules are agent-selected implementation
details.

## 2. Exact nonclosure

`B07`, `F060`, `F061`, `F110`, and every field `F128` through `F138` remain
`OPEN` and typed null. In particular:

- `F110` will eventually hold the decision threshold/null margin `delta0`;
- `F130` will eventually hold the distinct planning alternative `delta1`, with
  `delta1 > delta0`;
- `F131` still lacks a realized, hash-bound pilot source;
- `F132` still lacks an admitted training-seed count;
- `F133` still lacks a confirmatory seed registry or generation receipt; and
- group, case, draw, analysis, and interval counts remain unset.

Candidate familywise alpha `0.05`, candidate joint power `0.90`, per-domain
planning alpha `0.025`, and per-domain planning failure probability `0.05`
remain candidates only. The 241-seed result in the predecessor power package is
a synthetic calculator vector, not the manuscript design.

## 3. Future pilot input contract

A later pilot may begin only after a separately reviewed and authorized pilot
instance binds all of the following before any method output is produced:

1. the selected primary metric, direction, exact lower and upper bounds of one
   final paired seed-level direct-minus-guide statistic, its width `W_pair`,
   and the metric implementation hash; `W_pair` is not the width of one
   unpaired metric value;
2. F110/`delta0` and F130/`delta1`, with `delta1 > delta0`;
3. exact training/validation snapshot and split-manifest hashes for both
   domains, with held-out test material inaccessible;
4. an immutable pilot-seed registry disjoint from every confirmatory and
   simulation-trial registry, plus a reviewed IID or exchangeability law for
   pilot training seeds that matches the future confirmatory training
   mechanism except for the disjoint values;
5. exact natural-group, case, and conditional-draw rosters and exact rational
   weights; every case and group weight must be strictly positive and the
   weights at each aggregation level must sum exactly to one;
6. exact paired direct/guide stochastic addresses, and a reviewed inference-
   stream law that pairs the two methods within an address, keeps streams
   independent across pilot training seeds, and matches the confirmatory
   inference mechanism;
7. terminal-status and no-retry rules, including the future F148
   infrastructure predicate if any; and
8. a finite output schema and independent recomputation plan.

The pilot uses training and validation material only. It is excluded from
confirmatory estimation, cannot tune the held-out test rule, and cannot supply a
manuscript result. Test data, test outcomes, and confirmatory seeds are forbidden.

## 4. Pairing and aggregation

For domain `d`, pilot seed `s`, natural group `g`, conditioning case `c`, and
draw address `r`, define the paired score difference

```text
Y[d,s,g,c,r] = score_direct[d,s,g,c,r] - score_guide[d,s,g,c,r].
```

Direct and guide must share the same seed, group, case, draw address, and
conditioning input. Conditional draws are Monte Carlo samples inside a case;
they are never training replicates. Cases remain nested in their natural group.
Training seeds are the only independent model-training replication unit.

Using weights frozen before pilot output, aggregate in this order. Case and
group weights are exact positive rationals and sum exactly to one within every
weighted mean; zero, negative, missing, outcome-dependent, or merely
approximately normalized weights are invalid.

```text
case_mean[d,s,g,c] = mean over paired draws r
group_cell[d,s,g]  = weighted mean over cases c within group g
seed_mean[d,s]     = weighted mean over natural groups g
```

The paired score difference must have an exact frozen interval `[L_pair,
U_pair]`. Convex aggregation preserves that interval, so the final paired
seed-level statistic has certified width `W_pair = U_pair - L_pair`. The
predecessor power bound uses this paired-statistic width; an unpaired primary-
metric width must not be substituted.

The pilot point estimate and conditional training-seed variance are

```text
pilot_mean[d] = (1/S) * sum_s seed_mean[d,s]
pilot_seed_variance[d] =
    sum_s (seed_mean[d,s] - pilot_mean[d])^2 / (S - 1).
```

The variance requires at least two complete, independently registered pilot
seeds. Treating it as a transportable pilot variance source additionally
requires the reviewed IID/exchangeability and stream-matching receipts from
Section 3; distinct addresses or a disjoint registry alone do not establish
independence or transportability. The variance is conditional on the frozen
development groups and cases. It is not a superpopulation variance claim for
unseen patients or customers.

## 5. Crossed residual object

For power simulation that models seed, natural-group, case, and draw variation,
the pilot must retain the complete balanced paired draw array `Y` with its
addresses, the derived case means, and the group-cell array. Define

```text
grand[d]       = mean over s,g of group_cell[d,s,g]
seed_main[d,s] = mean_g group_cell[d,s,g] - grand[d]
group_main[d,g]= mean_s group_cell[d,s,g] - grand[d]
interaction[d,s,g] = group_cell[d,s,g]
                   - grand[d] - seed_main[d,s] - group_main[d,g].
```

These are centered algebraic components, not claims of independent random
effects. A later simulation may resample them only under a frozen and justified
crossed seed-by-group law. Seed-by-group cells, groups, cases, and draws may not
be relabeled as independent seeds.

The group-cell object alone does not identify within-group case variation or
within-case Monte Carlo variation. Therefore any candidate grid that changes
the number of cases or draws must use the retained `Y` array under a separately
frozen hierarchical resampling/generation law that specifies seed, group,
case, and draw sampling and the disjoint simulation streams. A grid point that
asks for more cases or draws than the retained nonparametric support supplies
is inadmissible unless a separately validated parametric generation law was
frozen before pilot output. If neither route is available, case/draw allocation
remains unidentified and the strategy stops with no-go; it may not extrapolate
from group cells.

The residual receipt must preserve exact reconstruction from `Y` through case,
group, and seed summaries, zero-sum identities, the original bounded range,
the full scheduled roster, and every terminal status. It must contain no
held-out outcomes, raw person/customer identifier, or publication-sensitive
path.

## 6. Failure and missingness

No scheduled row may be silently dropped, imputed, replaced, or rerun. Until a
metric-specific worst-case score and the F148 infrastructure predicate are
frozen, any non-`COMPLETE` pilot cell makes the variance source unavailable and
terminates this pilot version as
`PILOT_VARIANCE_UNAVAILABLE_TERMINAL_NO_GO`.

Unbalanced seed/group/case/draw rosters, a pairing mismatch, identifier alias,
duplicate address, out-of-range score, nonfinite value, registry overlap, or
test-material reference has the same terminal no-go disposition. A failed pilot
may inform a new pre-outcome protocol version, but it cannot be repaired,
resumed, topped up, or selectively rerun within the failed version.

## 7. Power-strategy pipeline

After a valid pilot receipt exists, the future strategy is:

1. freeze one finite grid over training seeds, groups, cases, draws, bootstrap
   resamples, simulation trials, and compute, together with the exact
   hierarchical law that makes every case/draw-dependent point identifiable
   from the retained pilot object;
2. use the exact paired hierarchy above and the selected paired seed-statistic
   bound `W_pair`;
3. evaluate the exact two-domain Holm decision rule under every admitted null
   condition and every required alternative/stress condition;
4. require within-condition independent Bernoulli simulation trials from a
   disjoint immutable trial-stream registry;
5. use simultaneously allocated Clopper--Pearson upper bounds for familywise
   error and lower bounds for joint two-domain power;
6. cover the composite null through a formal least-favorable/monotonicity proof
   or a frozen finite nuisance grid, otherwise stop with no-go;
7. select the minimum-compute passing grid point by a frozen lexicographic tie
   rule within the B08 capacity ceiling; and
8. prohibit grid expansion, seed top-up, replacement, favorable selection,
   sequential stopping, cross-domain pooling, and post-outcome changes.

This incorporates the exact predecessor power-route contract. It does not run
the route or establish that any grid point will pass.

## 8. Synthetic qualification boundary

The companion validator exposes a pure exact-arithmetic summary for already
aggregated per-seed paired values. It verifies at least two exact values,
computes the exact mean and Bessel-corrected sample variance, and rejects binary
floats, booleans, nonfinite surrogates, duplicate seed identifiers, or oversized
rational components. Synthetic fixtures exercise translation invariance,
permutation invariance, zero variance, exact fractions, and refusal paths.

This qualification proves only the seed-summary algebra and the static
dependency contract. It does not establish the future seed/stream
IID-or-exchangeability law, weight normalization, case/draw variance
identification, raw-data parsing, the future metric, crossed resampling,
Clopper--Pearson implementation, compute, a real pilot, or a scientific result.

## 9. Anonymity and publication boundary

This package is internal evidence only. Raw authority provenance, hashes, local
paths, registry details, and future operational receipts are excluded from an
anonymous or public submission. A publication-safe derivative and fresh
anonymity audit are required before any inclusion. No absolute user path,
credential, token, cookie, person identifier, or dataset row is stored here.

## 10. Completion statement

The Solo-Block-3 **draft** item may be marked complete only after the companion
machine record, read-only validator, hostile tests, exact custody, and
independent review pass. That checkmark has scientific scorecard effect zero.
Gate A's stronger item—“pilot variance and power approach are valid”—remains
open until a real admissible pilot, metric/effect freeze, compute proof, and
independent statistical review exist.
