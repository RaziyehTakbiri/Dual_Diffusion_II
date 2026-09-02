# Independent review of the F137 hierarchical paired-analysis formula freeze

**Reviewed:** 2026-09-01  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F137_PARAMETERIZED_NATURAL_GROUP_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FROZEN_PREOUTCOME`  
**Accepted control predicate:** `F137_PARAMETERIZED_NATURAL_GROUP_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict

`GO` for the exact four-file F137 package identified below.

The final reviewed package has zero P0, zero P1, and zero P2 findings. It
freezes the parameterized finite-roster natural-group hierarchical paired point
estimator and the exact caller-supplied one-plan empirical resampling transform
for F137. It supplies no primary metric, production numeric representation,
score, bound, effect margin, confidence method, resample count, weight,
cardinality, seed, registry, data, entropy, runtime, result, inference, or
decision.

The accepted field and count delta is exactly:

- F137, `/power_and_seed_plan/hierarchical_paired_analysis_formula`, changes
  from `OPEN` to `CLOSED`;
- the effective pre-execution view changes from 145 open / 21 closed to
  144 open / 22 closed;
- the post-execution view remains three open / three closed;
- total fields change from 148 open / 24 closed to 147 open / 25 closed; and
- every blocker, Formal Test, result slot, runtime state, operational task, and
  scientific state keeps its prior status.

This receipt is independent acceptance evidence only. It does not itself edit
the project timetable or evidence ledger and supplies no network, contact,
data, entropy, runtime, scientific, claim-promotion, release, or submission
authority.

## 2. Exact reviewed package

All four files were reopened through their canonical project paths. Each was a
regular, single-link `0644` file. Their exact accepted bindings are:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human record | `PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE.md` | 12,160 | `12174a5da4b0c43773a89b4a1c01e97b7a8208e7d849520c5310e2909defb52e` |
| Machine record | `research/fixtures/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json` | 24,002 | `2ce4fc0af580c9b0572496ee932467d185b0710744541342a41ce8715df65a06` |
| Read-only validator and pure evaluator | `research/diagnostics/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py` | 68,065 | `59f1f294fb6b8878bb89a5759c12242762dd223af06da709de6be4410a88e3e2` |
| Hostile tests | `tests/unit/test_manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py` | 40,414 | `59c8a40ffd39632d47eaa63fe4d39baa18886d4b4a0d29c5e124b49820b7b855` |

The four reviewed files total 144,641 bytes and 2,999 lines. The machine record
is duplicate-free canonical ASCII JSON with one terminal line feed. An
independent implementation, without importing the package validator,
recomputed the domain-separated semantic digest
`6bd2cc0bfd8dead57318775f82f39d8ba22a4919c5eae3628a6fffb584a3d6a8`,
exactly matching its embedded `record_sha256`.

## 3. Predecessor, baseline, and anti-drift verification

The review independently reopened and hashed all 35 bound predecessor files.
Every byte count and SHA-256 value matched the machine record, and every file
was regular, single-link, and exact mode `0644`. The bound groups are:

| Predecessor group | Bound files |
|---|---:|
| Anti-drift policy | 1 |
| Execution preregistration | 2 |
| Pre-execution closure v2 | 2 |
| Real-domain power-allocation route | 4 |
| Pilot-variance/power-strategy draft | 4 |
| Gate-A local statistical freeze | 4 |
| Accepted F104 count anchor and independent review | 5 |
| Accepted B11 post-execution count anchor and independent review | 5 |
| PhysioNet patient natural-group carrier | 4 |
| Retail customer natural-group carrier | 4 |
| **Total** | **35** |

Applicable generic predecessor semantic self-digests were independently
recomputed. The execution-preregistration machine and the custom PhysioNet
carrier are exact-byte bound and their required semantic projections are
parsed and checked. The review does not falsely apply the generic digest
algorithm to the PhysioNet carrier's custom `record_sha256` scheme.

The accepted F104 successor establishes 145 open / 21 closed pre-execution
fields. The accepted B11 successor preserves that pre-execution view and
closes exactly post-execution F168, F170, and F171, leaving F164, F165, and
F169 open. The immediate F137 baseline is therefore 145/21 PRE plus 3/3 POST,
or 148 open / 24 closed in total.

An independent F001--F172 roster calculation confirmed 166 pre-execution and
six post-execution fields. Adding only F137 to the exact 21-field closed PRE
roster yields 22 closed and 144 open PRE fields. The three closed and three
open POST fields remain unchanged, preserving 172 total fields. This is a
direct count-reducing closure after the two accepted zero-field B07 precursor
packages and creates no prohibited third precursor layer.

## 4. Formula, roster, and resampling-law audit

For each admitted domain separately, the frozen point formula is direct minus
guide, averaged over paired draws within each case, combined by exact positive
rational case weights within natural group, combined by exact positive
rational natural-group weights within seed, and then averaged equally over
complete training seeds. Group weights sum exactly to one; case weights sum
exactly to one within each group. The package does not populate those weights.

The evaluator requires at least two distinct complete seeds and at least one
group, case per group, and draw per case. It accepts heterogeneous
group-specific case cardinalities and case-specific draw cardinalities while
requiring the same complete frozen roster across seeds and the direct/guide
pair. The expected source order is exactly seed, group, case, then draw.

For each explicit caller plan, it requires exactly S uniform-with-replacement
seed indices, G categorical-with-replacement group indices, and, for each
selected group occurrence, exactly that group's C-g categorical case indices.
It crosses every selected seed occurrence with every selected group
occurrence. One case-index vector is shared across all selected seed
occurrences for the same group occurrence; duplicate group occurrences retain
separate case-index vectors. Selected occurrences are averaged without
reapplying weights. Draws are already averaged inside cases and cannot appear
in a plan.

The caller supplies a finite nonempty tuple of plans. Each plan is transformed
independently into one ordered replicate value. The evaluator neither chooses,
recommends, defaults, nor reports a numeric plan count, and the tuple length is
not F138 evidence. It returns only the point estimate, ordered exact replicate
vector, structural singleton flags, and the algebraic zero-spread flag; it
returns no confidence interval, p-value, lower bound, decision, or scientific
claim.

## 5. Independent exact-arithmetic recomputation

The review independently reconstructed the finite law rather than relying only
on the evaluator's output. For the two-seed, two-group qualification roster
with case counts `(1, 2)`, group weights `(1/4, 3/4)`, and within-group case
weights `(1)` and `(1/3, 2/3)`, there are exactly 100 ordered realized plan
states:

- four ordered seed-index vectors;
- group-index vectors whose case-map state counts sum to
  `1 + 4 + 4 + 16 = 25`; and
- `4 * 25 = 100` complete ordered states.

The exact probabilities sum to one. For the base values, the independently
computed point estimate is `4` and the probability-weighted mean of all 100
replicates is exactly `4`. For the heterogeneous multi-draw values, the point
estimate and exact replicate expectation are both `17/4`. The known supplied
plan evaluates to `7/2` after the heterogeneous draw means are formed. These
calculations confirm the no-double-weighting law, full seed/group Cartesian
product, shared per-occurrence case maps, and draw-within-case averaging.

Direct/guide reversal negates both point and replicate outputs; a common score
shift cancels; coherent seed/group/case reordering and identity relabeling
preserve values; and the two admitted domains remain separate.

## 6. Identity, refusal, and parameterization boundary

All domain, seed, group, case, draw, and conditioning identities are nonempty
exact strings restricted to ASCII bytes `0x21` through `0x7e`. Seed and group
identities are unique at their levels; cases are unique within group; draws are
unique within case. Conditioning identities are unique within each natural
group and paired one-to-one with canonical case identities. Reuse across
different groups or domains is permitted only because the full composite
address remains distinct.

The direct and guide row rosters must contain the exact ordered key roster and
the exact complete address/conditioning product. Missing, extra, duplicate,
out-of-order, cross-domain, unbalanced-across-seed, or mispaired rows fail
before arithmetic. Scores and weights must be exact built-in integers or
`fractions.Fraction` values within the frozen bit bounds; booleans, floats,
subclasses, nonpositive weights, normalization failures, and invalid indices
fail closed.

Singleton group, case, and draw layers are allowed deterministic layers and
are explicitly flagged. Identical supplied replicates produce
`ZERO_EMPIRICAL_BOOTSTRAP_SPREAD`, an algebraic output only. Invalid input has
the terminal disposition `F137_INPUT_INVALID_TERMINAL_NO_GO`; there is no drop,
imputation, retry, top-up, favorable selection, reweighting, fallback,
retraining, alternate method, or domain pooling.

F137 owns only the parameterized formula and transform. F105, F109--F112,
F130--F136, and F138 remain open, as do all actual operands, weights,
cardinalities, seed identities, registries, snapshots, admitted instances,
pilot values, confidence choices, and result-bearing artifacts.

## 7. Custody, hostile qualification, and effect surface

The validator performs canonical relative-path checks and componentwise
no-follow reads through held directory descriptors. Every leaf is required to
be a regular, single-link exact-`0644` file at the before-path,
before-descriptor, after-descriptor, and after-path observations. Its
fingerprint includes device, inode, size, modification time, change time, full
mode, and link count. Root, ancestor, descriptor, and final namespace identity
are rechecked, so symlink, hard-link, permission, inode-substitution, and
mid-read mutation races fail closed.

The machine record must be duplicate-free canonical ASCII JSON, carry the
correct domain-separated semantic self-digest, bind every nonmachine package
file, and equal the fully reconstructed expected record. Hostile tests cover
identity/address/cardinality and source-order errors, direct/guide mispairing,
empty or malformed rosters, conditioning-ID collisions, invalid exact types
and bounds, invalid weights and plans, case-map cardinality, singleton layers,
zero-spread interpretation, F112/F138 leakage, predecessor mutation,
noncanonical and duplicate JSON, custody substitutions and races, count and
field drift, fully re-signed false promotion, and current-package mutation.
All mutation tests operate only on disposable copies.

Direct source inspection found only standard-library exact arithmetic,
hashing, JSON, read-only filesystem, path, stat, and typing dependencies. The
source contains no writer, RNG, clock-derived scientific input, network or
connector client, subprocess launcher, project-science import, data reader,
training route, runtime-capture route, production worker, inference route,
claim promoter, or submission route.

## 8. Executed qualification

All qualification used Python bytecode writing disabled and pytest's cache
provider disabled.

| Working context | Qualification | Result |
|---|---|---|
| Project root | Canonical F137 validator entry point | `PASS`; semantic digest `6bd2cc0bfd8dead57318775f82f39d8ba22a4919c5eae3628a6fffb584a3d6a8` |
| `/private/tmp` current working directory | Canonical F137 validator by absolute path | `PASS`; same semantic digest |
| Project root | F137 focused hostile suite | `126 passed in 1.45s` |
| `/private/tmp` current working directory | F137 focused hostile suite against the canonical absolute package | `126 passed in 1.45s` |
| Project root | Accepted F104, B11, and F137 suites together | `379 passed in 3.24s` |
| Independent finite-law implementation | Base and heterogeneous-draw 100-state enumerations | probability `1`; replicate expectation equals point estimate in both cases |

The canonical four-file package and all 35 bound predecessor files retained
their exact byte receipts across these read-only runs.

## 9. Findings and preserved nonclosures

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

The following remain expressly unclosed or unperformed:

- F105, F109--F112, F130--F136, F138, and every other field not already
  independently closed;
- post-execution F164, F165, and F169; B11 remains open, while the accepted
  F168, F170, and F171 plan closures remain unchanged;
- B07 and all 12 blockers;
- Formal Tests 28 and 29 (`OPEN`) and Formal Test 30 (`PENDING`);
- R1--R4 and all four result slots;
- every primary metric, score representation, bound, effect margin,
  confidence method, resample count, weight, cardinality, seed, registry,
  snapshot, pilot value, interval, p-value, inference, and decision; and
- network/contact/repository/license/data activity, operational receipts,
  entropy, training, scientific or production execution, runtime authority,
  claims, release, submission, and publication approval.

## 10. Independent acceptance boundary

The exact package receives `INDEPENDENT_REVIEW_GO`. A later authorized
timetable and evidence-ledger reconciliation may register only F137 and the
corresponding 145/21 to 144/22 PRE transition, while preserving the 3/3 POST
view and 148/24 to 147/25 total transition. It must cite the exact four-file
package and this receipt and leave every listed nonclosure unchanged.

This receipt does not populate F112 or F138; choose any metric, numeric type,
weight, cardinality, seed, bootstrap count, or scientific operand; generate
bootstrap indices; admit data; execute a runtime; close B07 or B11; alter any
Formal Test or result; or authorize any later action. Any byte change to the
reviewed four-file package or any of its 35 bound predecessor files invalidates
this receipt and requires a fresh independent review.
