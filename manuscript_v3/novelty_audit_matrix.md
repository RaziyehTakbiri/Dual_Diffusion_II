# Manuscript v3 novelty audit matrix

**Status:** `UNRESOLVED`  
**Broad-framing verdict:** `METHOD-NOVELTY-NO-GO`  
**Narrow surviving route:** `C17-CENTERED-THEORY-AND-BENCHMARK-CANDIDATE`  
**Claim promotion authorized:** `NONE`  
**Audit date:** 2026-08-28  
**Scope:** working primary-source collision audit for Manuscript v3

This document is a fail-closed novelty audit. It records known collisions,
defines the only contribution route that presently survives as a hypothesis,
and states the evidence required before that route could be promoted. It is not
a systematic-review completeness claim, an independent external review, a
proof audit, a model-quality result, or a conference-readiness decision.

Any "independent" or "fresh" audit below means an ordinary technical recheck
that is separated from the original derivation or implementation. It does not
mean the discarded CP75 external-governance workflow: no four appointed
reviewers, trust root, identity ceremony, cryptographic signature, or approval
authority is required by this novelty audit.

`UNRESOLVED` means that Manuscript v3 may describe and test a candidate, but
may not call it new. The broad framing is already a no-go: none of native
mixed-state generation, random cardinality, birth/death/replacement dynamics,
generic Doob conditioning, a learned generalized information function, an
analytic guide plus neural correction, or missed-detection/clutter association
is a defensible standalone novelty claim.

The current manuscript and claim ledger remain controlling. No C-row or result
slot is promoted by this audit. CP76 remains a historical `NOT_READY`
assessment of its frozen snapshot; creating this previously absent support file
requires a later, separately hash-bound readiness assessment and does not make
the manuscript ready.

## 1. Audit rules

The matrix uses these dispositions:

- **`FULL-COLLISION`**: the proposed contribution is already occupied at the
  level stated. It must be treated as background or retired.
- **`STRONG-PARTIAL-COLLISION`**: the closest work contains the principal
  mechanism, so a more specific theorem, algorithm, or empirical distinction
  is required.
- **`FOUNDATION`**: the material is useful setup but is not a contribution.
- **`UNRESOLVED-DISTINCTION`**: this audit has not found an exact collision,
  but absence from this working matrix is not novelty evidence.
- **`KILL-IF-COLLIDED`**: the narrow route survives only while a final
  property-, equation-, supplement-, and available-code-level search fails to
  find a prior result with the same operative content.

For every row, the cited page is a primary paper page, proceedings page, or
publisher record. A title-level difference is irrelevant. The comparison must
use the complete mathematical object, observation law, algorithm, theorem,
initialization, and evaluated estimand. A later paper may supersede this matrix;
the search must therefore be rerun immediately before submission.

## 2. Closest-work collision matrix

| ID | Proposed ingredient or framing | Closest primary work | Collision found | Required disposition or surviving distinction |
|---|---|---|---|---|
| N01 | Native joint categorical and continuous generation | [CoDi (ICML 2023)](https://proceedings.mlr.press/v202/lee23i.html); [MultiFlow (ICML 2024)](https://proceedings.mlr.press/v235/campbell24a.html); [Diffuse Everything](https://openreview.net/forum?id=AjbiIcRt6q) | `FULL-COLLISION` | Categorical and continuous variables in native spaces are background, not a contribution. |
| N02 | A general generator combining continuous motion and jumps | [Generator Matching (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/819aaee144cb40e887a4aa9e781b1547-Abstract-Conference.html); [A Unified Approach to Analysis and Design of Denoising Markov Models (JMLR 2026)](https://www.jmlr.org/papers/v27/25-0693.html) | `FULL-COLLISION` | The generator/reversal formalism is cited foundation. A manuscript contribution must be estimator- and observation-specific. |
| N03 | Variable-cardinality generation by birth, death, thinning, insertion, deletion, or replacement | [Trans-Dimensional Generative Modeling via Jump Diffusion Models (NeurIPS 2023)](https://papers.neurips.cc/paper_files/paper/2023/hash/83a10a480fbec91c88f6a9293b4d2b05-Abstract-Conference.html); [Add and Thin (NeurIPS 2023)](https://papers.neurips.cc/paper_files/paper/2023/hash/b1d9c7e7bd265d81aae8d74a7a6bd7f1-Abstract-Conference.html); [Point Set Diffusion (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/cceb6b5d1781b6eb848f7e87bff5f74b-Abstract-Conference.html); [Edit-Based Flow Matching for Temporal Point Processes (ICLR 2026)](https://openreview.net/forum?id=FNf9IV1P2L) | `FULL-COLLISION` | Random cardinality and edit-family dynamics cannot be presented as new. |
| N04 | Conditional generation through a scalar Doob or generalized information function | [DEFT (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/hash/22d258dfbdf840ccbf266bbc545dd95f-Abstract-Conference.html); [A Framework for Conditional Diffusion Modelling](https://openreview.net/forum?id=k2PA7CUUJH); [Conditioning Continuous-Time Markov Processes by Guiding](https://doi.org/10.1080/17442508.2022.2150081) | `FULL-COLLISION` | C2 remains restricted foundation. The drift correction, jump-rate ratio, and conditional initial law must be attributed rather than claimed. |
| N05 | Learning a small conditional correction while freezing an unconditional model | [DEFT (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/hash/22d258dfbdf840ccbf266bbc545dd95f-Abstract-Conference.html); [Score Matching for Bridges Without Learning Time-Reversals (AISTATS 2025)](https://proceedings.mlr.press/v258/baker25a.html) | `FULL-COLLISION` | Frozen-base conditional fine-tuning and bridge-score learning are not the surviving distinction. |
| N06 | A tractable auxiliary guide combined with a neural correction | [Neural Guided Diffusion Bridges (ICML 2025)](https://proceedings.mlr.press/v267/yang25af.html) | `STRONG-PARTIAL-COLLISION` | “Analytic guide plus learned residual” is a no-go novelty sentence. Any surviving C3 claim must depend on the exact association law, cap defect, hybrid edit coverage, and C17 theorem together. |
| N07 | Joint-versus-product classification to learn a density ratio | [Noise-contrastive estimation](https://proceedings.mlr.press/v9/gutmann10a.html) | `FULL-COLLISION` | The logistic/NCE objective is standard. Novelty could only lie in a new theorem connecting its executable excess risk to the declared hybrid conditional path law. |
| N08 | Marginalizing missed detections, clutter, and ambiguous event-to-observation association | [Poisson multi-Bernoulli mixture observation models](https://doi.org/10.1109/TAES.2019.2920220) | `STRONG-PARTIAL-COLLISION` | Latent matching and miss/clutter summation are foundation. The exact heterogeneous normalized kernel and its use inside the cap-aware conditional estimator require a property-level distinction; the association idea alone is not new. |
| N09 | Inference or imputation with missing or censored events | [Imputing Missing Events in Continuous-Time Event Streams (ICML 2019)](https://proceedings.mlr.press/v97/mei19a.html); [Learning Temporal Point Processes with Intermittent Observations (AISTATS 2021)](https://proceedings.mlr.press/v130/gupta21a.html); [Inference for Mark-Censored Temporal Point Processes (UAI 2023)](https://proceedings.mlr.press/v216/boyd23a.html) | `FULL-COLLISION` | Missing-event inference is not a literature gap. The manuscript must distinguish its controlled unordered endpoint-observation task from temporal imputation and censoring. |
| N10 | Conditional generation of unordered point sets | [Point Set Diffusion (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/cceb6b5d1781b6eb848f7e87bff5f74b-Abstract-Conference.html) | `STRONG-PARTIAL-COLLISION` | Set-valued conditional sampling is occupied. The manuscript cannot rely on permutation invariance or subset conditioning as its contribution. |
| N11 | A capped typed-counting state and normalized capped-Poisson reversible reference | N02 and N03 cover the general generator ingredients; no exact-priority conclusion is made here. | `FOUNDATION` | C1 is a coherent, code-matched setup. It is not called novel even if the exact bookkeeping differs from a comparator. |
| N12 | Restricting an uncapped propagated association guide to the cap and isolating the blocked-birth harmonic defect | No exact collision established by this working audit. N02, N04, N06, and N08 are mandatory comparison families. | `UNRESOLVED-DISTINCTION` | The displayed cap-defect identity may support the narrow route only after a theorem-level primary-source search and independent proof audit. “Not found” is not a novelty verdict. |
| N13 | One association-informed residual potential coherently modifying continuous drift and all valid birth/death/replacement edges | N02, N04, and N06 occupy the generic scalar-control mechanism; N03 occupies the edit substrate. | `STRONG-PARTIAL-COLLISION` | The structural mechanism alone is not new. The surviving unit must include the exact observation law, cap accounting, estimator-specific theorem, and evidence that all channels behave as claimed. |
| N14 | An estimator-specific link from association/reference/cap error and joint-versus-product excess risk to full hybrid conditional-path KL or TV, including initialization | No exact collision established by this working audit; N02, N04--N08 are mandatory theorem comparisons. | `KILL-IF-COLLIDED` | This is the center of C17 and the only currently plausible theoretical novelty. A generic Girsanov, Doob, path-KL, classifier-consistency, or unobservable-error restatement fails the route. |
| N15 | A code-matched benchmark jointly testing continuous drift, birth, death, replacement, initial tilt, endpoint law, association ambiguity, cap error, and numerical path error | Existing works above contain subsets of these tests; no exact benchmark-equivalence conclusion is made here. | `UNRESOLVED-DISTINCTION` | The benchmark is contributory only if it is independently reproducible, exercises learned competitors rather than oracle code alone, and produces substantive comparative findings. Engineering custody counts are not benchmark evidence. |
| N16 | Broad “framework for heterogeneous event generation” framing | N01--N10 collectively occupy every broad ingredient. | `FULL-COLLISION` | Broad framework, firstness, and ingredient-aggregation language are prohibited. The paper must be titled and written around the exact cap-aware theorem and benchmark, if those survive. |

## 3. Broad-framing no-go

The following sentences, or semantic equivalents, are not admissible novelty
claims:

1. “We introduce a framework for joint discrete and continuous generation.”
2. “We introduce a variable-cardinality diffusion with birth and death.”
3. “We condition a hybrid generator using a Doob transform.”
4. “We freeze an unconditional model and learn a small conditional network.”
5. “We combine an analytic guide with a neural residual.”
6. “We marginalize latent correspondences between generated and observed
   events.”
7. “One scalar controls both continuous and discrete transitions.”
8. “We are the first to generate or complete missing heterogeneous events.”
9. “Our engineering verification establishes scientific correctness,
   usefulness, or novelty.”

The admissible current wording remains:

> We investigate a candidate cap-aware association preconditioner and learned
> residual for one declared class of noisy unordered observations of capped
> heterogeneous event configurations. Its novelty and empirical value are
> unresolved.

## 4. Narrow surviving C17-centered route

The only route that presently merits further main-track investigation is the
joint theory-and-benchmark package below. It is a candidate package, not a
claim.

### 4.1 Exact object

The route is restricted to all of the following together:

- a capped typed finite-counting state with declared multiplicity semantics;
- the selected reversible OU plus birth/death/replacement reference and a
  separately frozen learned base;
- a normalized at-most-one-anchor-per-occurrence observation family with
  misses, type confusion, declared atomic or affine-Gaussian mark noise,
  Poisson clutter, retained observations, overflow, and an admitted positive
  dominated branch;
- exact or certified association marginalization on the admitted resource
  domain;
- an uncapped independent auxiliary association guide, literal restriction to
  the capped state, and an explicit blocked-birth cap defect separated from
  base/reference mismatch and numerical error;
- a bounded learned residual trained by the declared same-context
  joint-versus-product risk, with an observation-only nuisance that has no
  path from process time or state;
- one total potential applied to continuous drift and every already-valid
  birth, death, and replacement edge, with structural zeros preserved; and
- the corresponding conditional initial tilt and an admitted numerical path
  sampler.

Removing any item may produce a useful ablation, but it does not retain the
same candidate contribution.

### 4.2 Required C17 theorem

Let the exact information function and plug-in approximation be

\[
h=\widetilde h\exp r^*,
\qquad
\widehat h=\widetilde h\exp r_\theta,
\qquad
e=r_\theta-r^*.
\]

A publishable C17 result must go beyond a generic Doob or path-change identity.
The theorem must not infer path-law control directly from a value-level
classification error. With

\[
\log(\widehat h/h)=r_\theta-r^*=e,
\]

the continuous and jump parts of the exact-versus-plug-in path divergence
depend on the hybrid Dirichlet/Bregman quantities

\[
\mathcal E_{\mathrm{hyb}}(e)
=\mathbb E\!\int
\left[
\tfrac12\|\bar a_u^{1/2}\nabla e_u(Y_u)\|^2
+\int \bar q_u^h(Y_u,dy')
\Phi\!\left(e_u(y')-e_u(Y_u)\right)
\right]du,
\qquad
\Phi(t)=e^t-1-t,
\]

with the exact orientation and state law fixed by the final theorem. Ordinary
logistic/NCE excess risk controls values under its sampling measure; it does
not by itself control continuous gradients or edit-edge increments. C17 must
therefore do one of the following, without silently changing the estimand:

1. prove an explicit coercivity/regularity bridge of the form

   \[
   \mathcal E_{\mathrm{hyb}}(e)
   \le C_{\mathrm{coer}}
   \left(\Delta_{\mathrm{NCE}}+\varepsilon_{\mathrm{projection}}\right)
   +\varepsilon_{\mathrm{derivative/edge}},
   \]

   with finite identified constants, matching measures, and separately bounded
   approximation terms; or
2. supply independently validated continuous-derivative and every-edit-edge
   certificates or losses that directly control the displayed functional,
   while keeping value-risk, derivative, and edge evidence distinct.

Under that mandatory bridge, the result must:

1. connect excess same-context joint-versus-product logistic risk, including
   bounded-class projection and nuisance gauge, to an executable value error
   for `e`;
2. prove the selected coercivity/regularity route or bind the separate
   derivative and edit-edge certificates just stated;
3. control or exactly decompose conditional path divergence using the correct
   continuous quadratic-gradient term and jump-rate relative-entropy/Bregman
   terms for birth, death, and replacement;
4. include the conditional initial-tilt discrepancy rather than silently
   starting from unconditional reference noise;
5. state every absolute-continuity, positivity, integrability, cap, and support
   assumption and preserve structural-zero edges;
6. contain only quantities evaluated or certified by the frozen mixed
   known-law oracle and end-to-end implementation; and
7. yield a nonvacuous numerical test. An unknown exact residual, an
   unobservable constant, or a bound dominated by an arbitrary global envelope
   does not satisfy this requirement.

The association, reference, and cap defects require a separate placement
argument. Because the same `tilde h` appears in `h` and `hhat`, it cancels from
`log(hhat/h)=e`; the cap/reference harmonic defect is not an independent
additive term in the exact target-versus-plug-in path divergence. It may enter
only through a proved construction such as:

- a stability or regularity estimate that bounds the size or approximability
  of `r*` from the residual PDE and measurable harmonic defect;
- a projection-error decomposition for the declared residual class; or
- an explicit intermediate-law comparison with a proved composition
  inequality and its own orientation and measures.

KL has no general triangle inequality. The theorem may not add guide,
cap/reference, residual, and path terms heuristically, nor count the same
defect once through `e` and again as a separate path-error summand.

C18 may support the route only if it becomes a nonvacuous, estimable
decomposition of base, observation/association, learned potential,
initialization, terminal-reference, and numerical errors. Otherwise C18 is
removed rather than presented as a theorem target.

### 4.3 Required benchmark

The benchmark must contain, at minimum:

- frozen finite A1 and mixed CTMC--OU known laws;
- exact or certified drift, birth, death, replacement, initial-law, endpoint,
  calibration, and path diagnostics;
- the matched unified direct conditioner;
- no-guide and oracle-guide controls on known laws;
- a Neural Guided Diffusion Bridges-style auxiliary-guide correction;
- a DEFT-style learned generalized-information-function control;
- task-compatible SMC or Feynman--Kac conditioning where available;
- one closest variable-cardinality point/edit generator on the common
  comparison surface;
- equal trainable-budget and equal total-compute views; and
- method-blind admitted PhysioNet and Online Retail tasks, with every failed
  run, refusal, timeout, OOM, calibration failure, and support failure retained.

The real-data tasks test a declared observation intervention. If missingness,
noise, or clutter is synthetically imposed, the paper must say
“controlled” or “semi-synthetic observation task”; it may not imply that the
kernel is the natural acquisition mechanism. A result in one domain is a
domain-specific finding. A common two-domain claim requires both prespecified
domains to pass without replacement after outcomes are known.

## 5. C-row disposition

| Claim | Novelty-audit disposition | Role in the narrow paper |
|---|---|---|
| C0 | `RETIRED` | Historical motivation only. |
| C1 | `FOUNDATION-NONNOVEL` | Define the state and cite the construction; never a contribution bullet. |
| C2 | `FOUNDATION-NONNOVEL` | State the restricted conditioning assumptions and cite standard machinery. |
| C3 | `NARROWED-UNRESOLVED` | May refer only to the complete object in Section 4.1. Promotion requires every novelty and evidence gate below. |
| C4 | `SUPPORTING-CONDITIONAL` | Claim sample or compute efficiency only after powered multi-budget learning curves and uncertainty; a one-budget win is insufficient. |
| C5 | `REQUIRED-VALIDITY-CLAIM` | Must pass the mixed known-law drift/edit/initializer/endpoint/path gate. |
| C6 | `REQUIRED-TASK-CHARACTERIZATION` | Method-blind training-only ambiguity admission; not itself a method contribution. |
| C7 | `DEFERRED` | Two domains do not establish generality. Remove broad cross-domain language. |
| C8 | `REQUIRED-PREREQUISITE` | Each frozen unconditional base must pass its independent quality gate. |
| C9 | `REQUIRED-BOUNDED-SCALING` | Any claim is limited to frozen count/anchor/ambiguity quantiles, hardware, error, memory, latency, and failure ceilings. |
| C10 | `DEFERRED` | No flexible-task claim without a separate frozen held-out-task estimand. |
| C11 | `SEPARATE-ROUTE` | The physical-time intervention is a future paper unless immutably frozen before Route-A outcome access; it is not mixed into this paper. |
| C12 | `SEPARATE-REPRODUCTION` | Source-reported material may appear as provenance or appendix context only after clean-room reproduction. |
| C13 | `SEPARATE-ROUTE` | CFC-versus-temporal-architecture comparisons are not part of the association-guidance contribution. |
| C14 | `RETIRED` | The broad quantization-equivalence claim remains prohibited. |
| C15 | `DEFERRED-OUT-OF-SCOPE` | No perceptual claim. |
| C16 | `DEFERRED-OUT-OF-SCOPE` | No clinical or retail utility claim; distributional fidelity is not utility. |
| C17 | `REQUIRED-HEADLINE-THEORY` | Must satisfy Section 4.2 and an independent proof/code audit. |
| C18 | `SUPPORTING-ONLY-IF-NONVACUOUS` | Include only as an estimable proved decomposition; otherwise remove. |
| C19 | `REQUIRED-ADMISSION` | Both real tasks need exact \((Y,A,z,K_m,\lambda_m)\) contracts and a defensible positivity/common-support route. |
| C20 | `REQUIRED-CONFIRMATORY-EVIDENCE` | Matched-total-compute improvement must pass in both admitted domains with no declared calibration or support regression. |

Result-slot scope for this route is correspondingly narrow:

- retain `R1-A1` and `R2-HYBRID` as validity gates;
- retain `R3-PHYS` and `R4-RETAIL` as the two confirmatory outcomes;
- remove `R5-ASAP` from the claimed package; and
- move `F1-TIME` to a separate future-route ledger.

## 6. Novelty and contribution kill criteria

### 6.1 Immediate C3 novelty no-go

C3 is retired as a novelty claim if any of the following occurs:

1. A primary paper, supplement, or available implementation already contains
   the operative combination in Section 4.1 and a theorem or algorithm with
   the same effect.
2. The proposed C17 statement reduces to a standard Doob transform,
   Girsanov/path-KL identity, generic classifier-consistency theorem, or a sum
   of previously known results without a new executable consequence.
3. Value-level logistic/NCE excess risk is asserted to control the continuous
   gradient or edit-edge increments without a proved coercivity/regularity
   inequality or separate derivative and every-edge certificates.
4. The cap/reference harmonic defect is inserted as an independent additive
   path-error term after it has canceled from `log(hhat/h)`, or is counted both
   through `e` and through a second unproved decomposition.
5. The cap term, association term, or learned residual disappears from the
   theorem's nonvacuous conclusion.
6. The theorem relies on the unknown exact `h`, exact residual, or another
   quantity that the implementation cannot evaluate, bound, or falsify.
7. The analytic preconditioner must be described as exact for the capped base
   to obtain the result.
8. The final property/equation/code comparison or independent reviewer does
   not affirm an irreducible distinction.

If C3 receives this no-go but the benchmark remains scientifically useful, the
work may continue only as an explicitly non-novel mechanism or evaluation
study. C20 alone does not restore a new-method claim.

### 6.2 Scientific-route no-go

The complete theory-and-benchmark route is not submission-ready if any of the
following holds:

1. The end-to-end learned trainer, conditional initializer, continuous-plus-
   jump sampler, native-domain adapters, or complete defect diagnostic remains
   document-only or only incrementally scoped.
2. `R2-HYBRID` fails any frozen drift, birth, death, replacement,
   initialization, endpoint, or path criterion.
3. Exact association refuses representative inputs and no separately validated
   approximation passes value, continuous-gradient, and every-edge-ratio gates.
4. Either real-domain task lacks material association ambiguity, a defensible
   observation semantics, or an admitted positivity/common-support route.
5. A domain, task, metric, threshold, comparator, seed rule, or failure rule is
   selected or replaced after outcome access.
6. The candidate base is weak, differently selected, or differently charged
   relative to the matched direct comparison.
7. The main effect occurs only against an under-tuned direct model, only with
   exposed/oracle association, or only outside the frozen count/ambiguity
   region.
8. A primary configuration score lacks its required properness or
   characteristicness result and no alternative was frozen before execution.
9. Either confirmatory domain misses the effect threshold or violates a
   declared calibration/support no-regression condition.
10. Failed, aborted, timed-out, refused, or OOM runs are excluded from the
    decision rule.

Negative or null outcomes remain reportable evidence. They do not become a
positive framework, novelty, scalability, or generality claim through
relabeling.

## 7. Promotion predicate

`METHOD-NOVELTY-GO` remains false until one immutable packet contains all of:

1. a pre-submission rerun of this primary-source matrix, including property,
   equation, supplement, and available-code comparisons;
2. a frozen end-to-end method definition and whole-method hostile audit;
3. the exact C17 theorem, proof, code-to-symbol map, and independent proof
   audit;
4. a nonvacuous mixed-oracle instantiation and a passing `R2-HYBRID` record;
5. a validated representative-scale association algorithm or an explicitly
   narrow exact-computation domain;
6. immutable task-admission records for PhysioNet and Online Retail;
7. preregistered comparator, compute, metric, power, multiplicity, failure,
   and no-regression rules;
8. complete `R3-PHYS` and `R4-RETAIL` artifacts, including all runs and
   failures;
9. a clean-room reproduction of the central theorem tables, figures, and
   result tables; and
10. a fresh final claim audit that distinguishes theorem/specification
    validity, implementation correctness, novelty, and empirical support.

Until that predicate is satisfied, the only allowed status is:

> **Broad framing: no-go. Narrow C17-centered theory-and-benchmark route:
> unresolved. No novelty or contribution claim promoted.**

## 8. Required follow-on artifacts

This audit identifies, but does not create or validate, the following:

1. a lean frozen scientific method record for the actual trained and sampled
   algorithm;
2. the C17/C18 theorem and independent proof-audit packet;
3. the complete A1 and mixed CTMC--OU known-law preregistration and results;
4. method-blind PhysioNet and Online Retail admission manifests;
5. a representative association-scaling artifact;
6. `execution_preregistration.md` with immutable estimands, metrics,
   thresholds, power, multiplicity, compute, and failure rules;
7. complete R1--R4 result artifacts and provenance transitions;
8. a clean-room reproduction report; and
9. a later content-addressed manuscript-readiness assessment over the changed
   snapshot.

The existing production protocol, CP75 external-response workflow, CP76
readiness sidecar, and incremental engineering checkpoints are retained as
internal history. None substitutes for the scientific artifacts above, and
none is evidence of novelty, theorem validity, empirical benefit, peer review,
venue acceptance, or submission readiness.
