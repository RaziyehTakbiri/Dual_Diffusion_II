# Manuscript v3 Execution Preregistration

**State:** `DRAFT_NOT_EXECUTABLE`  
**Route:** `NARROW_THEORY_AND_TWO_DOMAIN_BENCHMARK`  
**Confirmatory execution authorized:** no

This document is the human-readable preregistration for the smallest current
Manuscript-v3 contribution route. Its machine companion is
[`research/fixtures/manuscript_v3_execution_preregistration_v1.json`](../research/fixtures/manuscript_v3_execution_preregistration_v1.json).
The companion contains explicit `null` values for every unresolved scientific,
statistical, data-governance, and compute decision. Neither document may be
treated as executable until a later content-addressed freeze replaces every
required pre-execution `null`, closes every confirmatory-execution blocker,
and records the exact frozen pre-execution artifacts.

This is a publication preregistration. It does not authorize the CP50/Test-28
production workflow, alter the final v26 ledger or gates, complete CP75 review,
or promote any manuscript claim or result slot.

The proof, methods/statistics, and clean-room checks below are ordinary
research-quality audits. They do not recreate CP75: no externally appointed
four-reviewer panel, trust root, identity ceremony, signature, or authority is
required. A fresh audit may be performed by a qualified collaborator or by a
separately executed reproducibility process, with its scope and evidence
reported transparently.

## 1. Frozen contribution boundary

The proposed paper is a narrow theory-and-benchmark study of association-aware
preconditioning. It is not a general heterogeneous-generation framework,
cross-domain generality, sample-efficiency, clinical utility, perceptual
quality, or production-readiness paper.

The only candidate contribution claims are:

1. **C17, narrow theory target.** A code-matched theorem may relate declared
   target/reference or association-guide discrepancy to residual or
   conditional-path error under explicit assumptions. C18's broader end-to-end
   reliability decomposition is out of scope.
2. **C20, two-domain benchmark target.** On one frozen noisy unordered-subset
   task in each of PhysioNet Challenge 2012 and Online Retail II, the
   association-aware guide plus residual may improve conditional configuration
   fidelity over a unified direct conditioner under one frozen base and matched
   total compute.
3. **C3, conditional method wording only.** A new-method claim is permitted
   only after exact method freeze and a fresh, code-aware novelty audit
   issues `METHOD-NOVELTY-GO`. Otherwise the paper must use empirical-mechanism
   wording and must not call the construction novel.

Claims C1 and C2 remain attributed foundation material. C5, C6, C8, C9, and
C19 are prerequisites, not headline findings. C0 and C14 remain retired.
C4, C7, C10--C13, C15, C16, and C18 are excluded from this route. In
particular, ASAP/R5 and the physical-time fallback/F1 are not confirmatory
slots for this paper.

No failure may be used to activate Route B, replace a domain, add a seed, change
a metric, or relax a threshold. A different route requires a new manuscript
and preregistration frozen before its outcomes are observed.

## 2. Confirmatory slots and order

The only in-scope slots, in mandatory order, are:

| Slot | Role | Current state | Unlocking condition |
|---|---|---|---|
| `R1-A1` | Finite atomic known-law falsification gate | `NOT_RUN` | Exact fixture, grid, estimands, tolerances, and implementation are frozen and the complete gate passes. |
| `R2-HYBRID` | Mixed capped CTMC--OU known-law gate | `NOT_RUN` | Drift, birth, death, replacement, initialization, endpoint, and path checks pass their frozen exact or certified bounds. |
| `R3-PHYS` | PhysioNet primary benchmark | `NOT_RUN` | R1/R2, method freeze, base-quality, scaling, task admission, power, and artifact gates all pass. |
| `R4-RETAIL` | Retail primary benchmark | `NOT_RUN` | The same prerequisites pass and the Retail task is independently admitted. |

R1 and R2 must finish before any R3/R4 test outcome is generated. R3 and R4
are separate domain estimands; they are never pooled to hide a failing domain.

## 3. Known-law and theory gates

Before real-domain execution, the freeze must provide complete parameters,
evaluation grids, reference implementations, and numerical tolerances for:

- the finite A1 count-CTMC fixture;
- a capped mixed CTMC--OU fixture with continuous marks and at least one
  type-changing edge;
- drift, birth, death, and replacement conditional corrections;
- conditional initialization, endpoint law, and path diagnostics;
- source/destination Radon--Nikodym factors, multiplicity factors, cap-boundary
  flux, association normalization, and nuisance invariance; and
- exact or certified KL/TV and componentwise numerical error bounds.

The C17 theorem requires a final statement, assumptions, proof, executable
quantities, code-definition crosswalk, counterexamples or boundary cases, and
a fresh proof/code audit. Its statement must explicitly identify the
assumptions under which excess logistic density-ratio risk controls the hybrid
Dirichlet error: both the continuous `gradient e` term and the discrete legal-
edge differences of `e` must appear. The error decomposition must keep
target/reference mismatch, analytic-guide approximation, residual estimation,
cap restriction/defect, initialization, terminal-reference, and numerical
terms nonoverlapping; in particular, the cap defect cannot be counted again as
a base/reference term. Existing incremental software audits and the
nonconfirmatory CP29/Test-28 diagnostic are engineering evidence only; they do
not satisfy R1, R2, C17, or whole-method approval.

### Current partial falsification checkpoint

The unproved theorem target is now written explicitly in
[`c17_hybrid_path_error_theorem.md`](c17_hybrid_path_error_theorem.md). It
freezes the direction `KL(exact conditioned law || plug-in conditioned law)`,
the initializer, continuous-gradient, birth, death, and replacement terms,
the required regularity and support assumptions, and the two permissible
routes from value-level NCE evidence to path error. It also records why a
general NCE-to-hybrid-energy implication is currently unavailable. This is a
statement and proof-obligation document, not the final C17 theorem or proof.

A focused diagnostic now exists in
[`mixed_ctmc_ou_known_law_oracle.py`](../src/heterodiff/evaluation/mixed_ctmc_ou_known_law_oracle.py),
with its focused test in
[`test_mixed_ctmc_ou_known_law_oracle.py`](../tests/unit/test_mixed_ctmc_ou_known_law_oracle.py).
It exercises a six-state capped two-type CTMC with nonempty birth, death, and
replacement families, multiplied by an independent scalar OU process. It
checks finite information functions, conditional initial and endpoint laws,
discrete Doob path likelihood identities, the conditioned OU drift and
moments, and a uniformization truncation tail with floating-point roundoff
reported separately.

That fixture is intentionally factorized. It does **not** exercise a learned
residual, cap-defect cancellation, association marginalization, or continuous
marks attached to occurrences. Its numerical ODE/PDE residuals are diagnostics
rather than rigorous arithmetic enclosures.

The next partial checkpoint follows the direct-certificate route frozen in
[`c17_fork_b_direct_certificate_contract.md`](c17_fork_b_direct_certificate_contract.md).
The independent implementation and hostile tests are
[`mixed_ctmc_ou_path_kl_diagnostic.py`](../src/heterodiff/evaluation/mixed_ctmc_ou_path_kl_diagnostic.py)
and
[`test_mixed_ctmc_ou_path_kl_diagnostic.py`](../tests/unit/test_mixed_ctmc_ou_path_kl_diagnostic.py).
On the same factorized finite fixture, a terminal-matched nonzero residual gives
the forward orientation `KL(P_EXACT_H || P_PLUGIN_H_EXP_E) =
0.22604807707806723`, decomposed into initializer
`0.12608683355724082`, OU continuous-gradient `0.010453333333333335`,
birth `0.029135431076622087`, death `0.016340611640645607`, and
replacement `0.04403186747022539`. A separately propagated reverse
orientation is `0.2180141647976705`, and an independent fixed-quadrature,
direct-Poisson calculation differs from the forward total by
`8.326672684688674e-17`.

The path-change identity is exact for the declared ideal finite fixture, but
the reported jump integrals are ordinary floating-point quadrature, not
interval enclosures. This checkpoint exercises the five direct quantities; it
does not train or assess a learned estimator, marginalize associations, test
state-dependent occurrence marks, or exercise the cap-defect cancellation.
It therefore does not establish the missing real-domain derivative/every-edge
certificate or the general C17 bridge. Accordingly, R2 remains `NOT_RUN`, C17
remains `UNPROVED`, all final theorem, fixture, grid, and tolerance fields below
remain unresolved, and confirmatory execution remains unauthorized.

The cap-defect obligation is now isolated in
[`c17_cap_defect_cancellation_contract.md`](c17_cap_defect_cancellation_contract.md),
implemented by
[`mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py`](../src/heterodiff/evaluation/mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py),
and covered by
[`test_mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py`](../tests/unit/test_mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py).
On the same factorized fixture, the restricted cap-three auxiliary guide has a
nonzero blocked-birth defect with maximum magnitude
`0.5361111111111103`, while the blocked-birth identity residual is
`6.661338147750939e-16`. Factoring the exact and plug-in potentials through
that shared guide recovers their error to `5.551115123125783e-17` and leaves
the five path quantities unchanged: initializer `0.12608683355724076`, OU
continuous-gradient `0.010453333333333335`, birth
`0.029135431076622087`, death `0.016340611640645607`, replacement
`0.04403186747022539`, and total `0.22604807707806718`. The cap defect is
therefore explicitly excluded as an additional path-KL summand. This is an
ordinary binary64/SciPy cancellation diagnostic, not an interval proof or a
general cap-stability theorem.

The association-side evaluator is frozen in
[`c17_finite_a1_association_component_contract.md`](c17_finite_a1_association_component_contract.md),
with the family split in
[`finite_bridge_family_path_control.py`](../src/heterodiff/theory/finite_bridge_family_path_control.py),
the all-observation wrapper in
[`finite_association_fork_b_diagnostic.py`](../src/heterodiff/evaluation/finite_association_fork_b_diagnostic.py),
and hostile tests in
[`test_finite_association_fork_b_diagnostic.py`](../tests/unit/test_finite_association_fork_b_diagnostic.py).
It evaluates all `21` finite A1 observations, including overflow, under the
exact target semigroup and partitions `30` birth, `30` death, and `60`
replacement edges. A deterministic **test-only** perturbation produces the
observation-weighted diagnostic values initializer
`0.00223346825475464`, birth `0.002322966460349031`, death
`0.0009899328996185747`, replacement `3.66747719559582e-05`, and total
`0.005583042386678205`; the continuous term is
`NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES`, not numeric evidence. The maximum
family-versus-aggregate check is `1.3877787807814457e-17`. These numbers test
the evaluator, not a learned model.

This local A1 checkpoint deliberately refuses production-bound evaluators:
the local compatibility fixture token differs from the preregistered
production-runtime token, and no frozen production path-content binding is
available here. A genuine learned checkpoint therefore requires a separate
runtime-bound lane after the authorized training stage. Neither checkpoint
exercises occurrence-attached mark fibers, supplies rigorous numerical
enclosures, completes R1 or R2, proves C17, promotes a claim, or authorizes
confirmatory execution.

## 4. Datasets, tasks, and admission

The two fixed confirmatory datasets are PhysioNet Challenge 2012 and Online
Retail II. No substitute dataset is permitted after this preregistration is
frozen.

For each domain, the executable freeze must specify and hash:

- acquisition source, version, license, schema, and raw snapshot;
- generated endpoint `Y`, context `z`, observation `A`, event types, marks,
  physical-time semantics, horizon, cap, segmentation, and overflow rule;
- the exact clean observation kernel, observation reference, and either a
  naturally positive dominated route or a proved and implemented
  common-support/structural-zero extension;
- detection, noise, confusion, clutter, missingness, and tie/multiplicity
  semantics, each justified by the application rather than added to make the
  theorem convenient; and
- a method-blind, training-only admission statistic and threshold.

PhysioNet uses patient groups; static admission fields, if retained, belong in
`z` rather than the generated event configuration. Retail uses customer-window
groups and must define cancellation, country, simultaneous line-item, quantity,
price, and invoice-time handling. If either domain fails its frozen admission
rule without arbitrary added noise, C20 is not tested or promoted.

## 5. Splits and leakage controls

The freeze must contain literal group lists or content-addressed split
manifests. PhysioNet splits are patient-disjoint. Retail splits are
customer-disjoint and temporal under a fully specified cutoff/window rule.
All preprocessing, vocabularies, normalization, caps, task/noise models,
kernel bandwidths, and approximation tuning are fit on training data only.

Validation data may select hyperparameters and checkpoints under one frozen
rule. Confirmatory test data remain sealed until the method, baselines,
hyperparameters, seeds, metric, thresholds, and promotion rule are frozen.
Exact/near-duplicate, group-overlap, and temporal-leakage reports are required.
Conditioning cases and observation randomness are paired across methods using
the frozen seed registry.

## 6. Methods, baselines, and ablations

All methods use the same frozen unconditional base checkpoint within a domain.
The sole primary comparison is:

- association-aware analytic guide plus learned residual; versus
- unified direct conditioning with matched total compute.

The minimum interpretation set is:

- analytic guide with residual removed;
- direct/residual conditioning with the analytic guide removed;
- an association-destroyed or factorized/eventwise control;
- the unconditional base as a sanity reference; and
- one strongest task-compatible external/domain baseline per domain.

The following four literature-facing comparator families are mandatory in
both domains unless the frozen preregistration gives a domain-specific,
technically checkable inapplicability or equivalence justification:

- a Neural Guided Diffusion Bridges (NGDB)-style auxiliary guide plus
  correction;
- a DEFT-style learned generalized-information-function correction with the
  base frozen;
- task-compatible same-base SMC/Feynman--Kac conditioning; and
- the closest variable-cardinality point/edit generator that natively supports
  the frozen task intersection.

One comparator cannot silently stand in for another. Any claimed equivalence
must identify the matched objective, proposal/conditioning semantics, model
class, compute, and task interface. An inapplicable comparator remains in the
reported matrix with its frozen reason.

Every implementation requires a repository and commit, license, exact config,
parameter count, native-capability statement, tuning budget, and compute rule.
Extensions written by the authors must be labeled. Baselines, ablations, or
tuning budgets cannot change after test access.

## 7. Metrics and estimands

The domain-level primary estimand is the natural-group-weighted paired mean of
`primary_score_direct - primary_score_guide`; the favorable direction is
positive when the selected score is lower-is-better. Domains are analyzed
separately.

Configuration kernel score (CKS) may be primary only after a theorem establishes
the required characteristicness/injectivity on the exact admitted capped
configuration space. Otherwise one named validated alternative must be selected
before test access. There is no runtime or post-result metric fallback.

The freeze must provide the primary score, direction, aggregation unit,
training-only fitting rule, Monte Carlo draws per conditioning case, minimum
meaningful effect, real--real floor, confidence procedure, and multiplicity
rule. It must also provide no-regression margins or upper bounds for
calibration/coverage, support validity, event count, type/mark/time behavior,
initializer error, association approximation, run failure, latency, memory,
and compute. Known-law primary metrics are exact or certified KL/TV under the
frozen fixtures. Other metrics are secondary and cannot rescue a failed
primary result.

## 8. Power, seeds, and analysis

The confirmatory design is fixed-N and paired. A blinded training/validation
power analysis must freeze:

- familywise alpha and multiplicity family;
- target power and minimum meaningful effect;
- the pilot variance source and its exclusion from confirmatory estimation;
- the exact independent training/checkpoint seed count;
- natural groups and conditioning cases per group in each domain;
- conditional draws per case;
- the hierarchical paired bootstrap or mixed-effects formula;
- confidence-interval method and resample count; and
- the literal seed registry or an immutable generation receipt.

Training seeds are replicates. Multiple conditional draws from one trained
model and case are Monte Carlo samples, not independent replicates. Seeds are
paired across the primary methods. No seed top-up, replacement, favorable-seed
selection, or sequential stopping is permitted. CP50/v26's 2,048 seeds,
32-shard layout, 554 estimator records, and Test-28 Bonferroni thresholds are
not power evidence for this manuscript.

## 9. Training, stopping, failure, and exclusions

The freeze must set optimizer, schedule, precision, batch construction,
maximum epochs/steps, validation metric, early-stopping patience, checkpoint
tie rule, and maximum tuning trials. Validation early stopping is permitted
only under that frozen rule; experiment-level optional stopping is not.

Every scheduled run has exactly one terminal status: `COMPLETE`,
`ALGORITHMIC_FAILURE`, `NONFINITE`, `OOM_OR_TIMEOUT`, or `INFRA_ABORT`.
Algorithmic failure, initializer refusal/exhaustion, nonfinite output, OOM, and
timeout remain in the declared estimand and are not rerun. An infrastructure
rerun is allowed only under a predeclared objective predicate that establishes
no usable stochastic, model, or metric output was produced; it uses the same
seed and config and is recorded. The freeze must set the admissible failure
ceiling. No test-set exclusion is permitted.

## 10. Compute and fairness

The freeze must identify hardware, software/container and environment digests,
precision, deterministic settings, parameter counts, optimizer budgets,
tuning trials, per-run wall-time/accelerator-hour/memory/model-evaluation
ceilings, total pilot/tuning/final allocation, and failure reserve. The primary
methods receive matched total training and inference compute under one explicit
formula. Planned and realized compute and every failed or aborted run are
reported. No post-result compute top-up is permitted.

## 11. Artifact and result-promotion contract

Before test access, the following must exist with immutable digests:

- this preregistration and its fully populated machine companion;
- code, environment/container, data acquisition, schema, preprocessing, and
  split manifests;
- method, base, baseline, ablation, checkpoint-selection, and seed configs;
- power, domain-admission, theorem/proof, known-law, scaling, and base-quality
  gate artifacts;
- exact run schedule, metric specification, thresholds, and compute budget;
  and
- a test-access receipt showing that the preceding artifacts were already
  frozen.

After execution, the record must contain raw predictions/samples, per-run logs
and checkpoints, primary and secondary metric tables, all failures,
exclusions, deviations and aborted attempts, compute receipts, a fresh
methods/statistics audit, a clean-room reproduction audit, and the exact
claim-ledger transition.

C20 may be promoted only if both R3 and R4 exceed the frozen minimum effect in
the favorable direction with multiplicity-adjusted confidence bounds and all
no-regression, failure, scaling, base-quality, compute, R1, and R2 gates pass.
C17 additionally requires its completed proof package. C3 additionally
requires `METHOD-NOVELTY-GO`. A null, negative, or failed gate is a valid
terminal result and cannot be repaired by changing the design.

## 12. Current blockers and user-only decisions

The following choices are intentionally unresolved. Items 1--8, together with
the data-use, governance, and privacy parts of item 9, block confirmatory
execution:

1. final approval of the retained claim wording and C17 theorem statement;
2. exact PhysioNet and Retail snapshots, licenses, governance, representations,
   observation mechanisms, caps, horizons, and admission thresholds;
3. positive/common-support theorem route for each task;
4. CKS characteristicness proof or the exact alternative primary score;
5. meaningful-effect, no-regression, known-law, scaling, and failure thresholds;
6. baseline repositories/commits and the matched-compute formula;
7. alpha, power target, pilot variance source, seed/group/case/draw counts, and
   analysis formula;
8. hardware and total compute/tuning budget;
9. release, anonymization, data-license, clinical, and privacy decisions.

Before claim promotion or submission, the project must also record the scope
and responsible process for the ordinary proof/code, methods/statistics, and
clean-room reproducibility audits. Those audits need not be externally
appointed or cryptographically signed, and their assignment is not a reason to
delay the scientific implementation or a fully frozen confirmatory run.

Until every execution-blocking choice is resolved, all required implementations
and pre-execution gate artifacts exist, and the machine companion has no
required pre-execution `null`, the only valid state is
`DRAFT_NOT_EXECUTABLE` and no confirmatory run may start. Unresolved
post-execution audit assignments continue to block claim promotion and
submission, not execution.
