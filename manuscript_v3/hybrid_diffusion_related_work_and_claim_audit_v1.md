# Hybrid diffusion: related-work and claim audit

Date: 2026-09-13.

Status: bounded, primary-source review supporting the manuscript-first work
package. This is not an exhaustive literature review, novelty certification,
venue-readiness assessment or a new end-to-end error theorem. It changes no
scientific parameters, acceptance tolerances, data or executable model.

## 1. Assessment

The paper should not present the combination of jumps and diffusion, an
analytic guide plus a neural correction, or joint/product density-ratio
classification as new on their own. Each has a clear prior connection below.
The potentially distinctive object is the *specific conditional generative
construction*: occurrence-preserving atomic/continuous event configurations,
association-aware noisy observations, an explicit independent-reference
guide/initializer, and a learned correction under a shared target and
observation definition. Whether that construction is novel and useful still
requires closer comparison and informative experiments.

The current mathematical amendment repairs a real modeling problem: exact
discrete fields and singular continuous identity observations cannot simply
be treated as one smooth Euclidean density. Its repair also changes the
training target and observation task. This must be disclosed as a scientific
choice, not marketed as a free implementation improvement.

The historical C17 path-error claim remains **retired, not proved**. New
population-objective identities or successful numerical tests do not restore
it. See [the retirement record](c17_retirement_no_claim_successor_v1.md) and
[the current mathematical specification](../PROJECT_MIXED_DOMAIN_SCIENTIFIC_AMENDMENT_MATH.md).

## 2. Five directly relevant primary sources

### 2.1 Variable dimension and jump-diffusion generation

Andrew Campbell, William Harvey, Christian Weilbach, Valentin De Bortoli,
Tom Rainforth and Arnaud Doucet. *Trans-Dimensional Generative Modeling via
Jump Diffusion Models*. NeurIPS 2023.

The paper jointly generates dimension and values through a time-reversed
jump diffusion and derives a training objective. Its experiments include
conditional diffusion guidance. Therefore neither variable-cardinality
generation nor guiding a changing-dimensional state is sufficient as our
novelty claim. The useful comparison is between its representation,
conditioning mechanism and training objective and our exact-key fibers,
occurrence associations and conditional-ratio construction. This audit does
not claim their method cannot be adapted to our task. [Official paper,
Sections 3 and 5.1.1; Appendix C](https://papers.neurips.cc/paper_files/paper/2023/file/83a10a480fbec91c88f6a9293b4d2b05-Paper-Conference.pdf).

### 2.2 Analytic auxiliary guidance

Moritz Schauer, Frank van der Meulen and Harry van Zanten. *Guided proposals
for simulating multi-dimensional diffusion bridges*. Bernoulli 23(4A),
2917–2950, 2017. DOI: 10.3150/16-BEJ833.

An auxiliary tractable diffusion supplies a guiding term; a change-of-measure
argument relates proposal and target bridge laws under explicit conditions.
That is the relevant antecedent for using an independent-reference guide.
Its bridge-law equivalence is not a theorem we may import merely because our
drift has a similar form: our state space, jump mechanism and observation
law differ. [Author manuscript, Section 2 and Theorem 1](https://arxiv.org/pdf/1311.3606).

### 2.3 Guidance beyond ordinary diffusions

Marc Corstanje, Frank van der Meulen and Moritz Schauer. *Conditioning
continuous-time Markov processes by guiding*. Stochastics 95(6), 963–996,
2023. DOI: 10.1080/17442508.2022.2150081.

This work develops guided Markov processes and includes discrete-state jump
examples. Its Theorem 3.3 states conditions for a likelihood-ratio relation
up to the conditioning horizon. It prevents us from describing guidance of
jump processes as an unexplored principle. It is also a useful starting point
for checking, rather than assuming, a later hybrid path-law theorem.
[Author manuscript, Sections 2–4 and Theorem 3.3](https://arxiv.org/pdf/2111.11377).

### 2.4 Analytic guide plus neural residual

Gefan Yang, Frank van der Meulen and Stefan Sommer. *Neural Guided Diffusion
Bridges*. ICML 2025, PMLR 267:71210–71230.

The method explicitly augments a guided diffusion proposal with a learned
drift correction and optimizes a variational bridge approximation. Thus
“analytic guide plus neural residual” is not our standalone contribution.
Our prospective distinction is the association-aware hybrid configuration
law and conditional learning route, not the existence of the correction
architecture. Compare the actual objectives and conditioning assumptions;
do not treat a Euclidean bridge baseline as identical to our observation
task without specifying the adaptation. [Official publication](https://proceedings.mlr.press/v267/yang25af.html),
[author manuscript, Section 4.1](https://arxiv.org/html/2502.11909v2#S4.SS1).

### 2.5 Joint/product classification and likelihood-to-evidence ratios

Joeri Hermans, Volodimir Begy and Gilles Louppe. *Likelihood-free MCMC with
Amortized Approximate Ratio Estimators*. ICML 2020, PMLR 119:4239–4248.

Dependent joint pairs versus independent product pairs yield a Bayes-optimal
classifier whose logit is a likelihood-to-evidence log ratio. Section 3.1
and Equations 16–17 give this exact connection. Our use of two BASE paths
does not make that identity novel. The model-specific questions are which
path law generates those pairs, whether the implemented function class can
represent that log ratio, and how ratio approximation affects the hybrid
sampler. [Official paper, Section 3.1](https://proceedings.mlr.press/v119/hermans20a/hermans20a.pdf).

These five sources were selected for direct conceptual proximity. They do
not exhaust the relevant marked-point-process, finite-set association,
discrete diffusion or conditional simulation literature. In particular,
no priority claim is established here for the matching polynomial or the
Poisson posterior decomposition.

## 3. Claim wording and the evidence it needs

| Proposed statement | Current defensible wording | What would justify a stronger statement |
|---|---|---|
| General hybrid diffusion model | A reusable construction on the declared countable-key/continuous-fiber configuration carrier | Public interfaces and an additional adapter; precise extension assumptions and limitations |
| Exact association-aware guide | An exact guide for the stated **uncapped independent reference**, evaluated on capped states | Never equate it with the capped or learned BASE likelihood without an additional result |
| Better conditional learning | A hypothesis that a structured guide reduces the correction learning burden | Held-out conditional quality, guide/residual ablations, common data/observation laws and matched budgets |
| Likelihood-free conditional objective | A joint/product classification objective with a stated population Bayes identity | Proof that the sampler-induced law and implemented nuisance/gate class satisfy the identity's assumptions |
| Reference-posterior initialization | A normalized ideal reference-weighted posterior construction for the specified observation branches | Full branch coverage, exact-law proof and numerical approximation/refusal reporting; not a learned-posterior claim |
| Strong error guarantee | Limited identities and target-shift bounds, each with its own assumptions | A separate proof connecting learned function errors, path measures, discretization and initial law |
| Reproducible experiments | Source, configurations and runnable examples supporting declared experiments | Fresh-install validation and scripts reproducing every reported table/figure |

The most promising empirical hypothesis is narrow and falsifiable: *under a
shared target lift, observation channel, BASE model and numerical schedule,
does exact-reference association structure improve conditional quality or
quality per computational budget relative to direct conditioning?* A
negative answer is scientifically possible. Reference-only, residual-only
and guide-plus-residual variants should distinguish an informative guide
from extra capacity, extra computation or an easier observation task.

## 4. Focused proof priorities

### A. Normalize the actual laws before comparing them

Keep separate the raw empirical target, its smoothed/reference-mixture
successor, the capped reference law, the uncapped guide reference, the
learned continuous-time process and the numerical path family. A proof about
one is not a certificate for another. The target-lift bound is a useful
limited result precisely because it quantifies a disclosed change rather
than erasing it.

For the configuration reference, present the quotient pushforward and the
Poisson-conditioned count law. Prove birth/death detailed balance including
duplicate occurrences and the cap boundary; state the Gaussian integration
by parts domain for each continuous fiber. A finite-count cap controls the
number of simultaneous coordinates, not their unbounded magnitudes or the
number of possible discrete keys.

For the reference guide and initializer, prove the association sum by
conditioning on ancestor/detection indicators and immigrant observations.
Retain the single global Poisson factor, occurrence multiplicities, overflow
branch and **total-count** conditioning. This is a tractable and directly
testable theorem target; its scientific distinctiveness still needs a wider
association-literature comparison. Do not label exponential per-key matching
work polynomial or generally scalable.

### B. State a useful BASE population-objective identity

For the reversible reference, an exact excess-objective decomposition can
identify the desired continuous gradient and jump-potential differences.
The proof must keep the orientation of the reference edge measure, jump
rate weighting and density factors explicit. It needs Gaussian integration
by parts with vanishing boundary terms and integrable jump expressions.
Time weighting and zero-clock intervals must agree with the training
definition. This supplies a mathematical interpretation of the objective,
not finite-sample consistency or convergence of AdamW.

The implemented jump term is proportional to `exp(Delta V) + Delta V`.
Under reference detailed balance, the excess around `V*=log f` has the
nonnegative factor `f(y)[exp(Delta r)-1-Delta r]`, with
`r=V-log f`, integrated against the oriented measure
`Pi_N(dx) q_0(x,dy)`. This orientation matters: replacing `f(y)` by `f(x)`
without reversing the residual increment changes the identity.

### C. Separate Bayes classification from representability

At a fixed time, let `J_u` be the joint law of an interior BASE state and its
terminal observation, and let `M_u` be the product of the corresponding
marginals. With equal class priors, the unrestricted Bayes logit is
`log(dJ_u/dM_u)`. A pointwise logistic-risk proof is short and useful. The
finite neural architecture, residual gate and nuisance term need not attain
that unrestricted minimizer.

Independent source inspection found two material qualifications:

1. `FactorizedBasePopulation.sample_pair` inserts the queried time into the
   numerical grid and regenerates complete paths. The terminal law can
   therefore depend on that query. A time-independent nuisance cannot be
   asserted to equal the evidence term for every query without a proof of
   time-invariant evidence or a corrected common-path/time-aware design.
2. The gated residual is constrained near the clean hold. Exact endpoint
   agreement does not establish that the required residual vanishes at the
   gate's cubic rate. Without that property, the selected architecture has
   an approximation error even at the population optimum.

These are scientific definition/representation issues, not reasons to add
another hardware qualification test. A portable synthetic demo may expose
the current implementation faithfully, but must not claim that it resolves
them.

### D. Do not infer score error from small classification loss

A concrete counterexample makes the missing implication visible. Let joint
and product distributions coincide with a standard Gaussian continuous
coordinate `X`, so the Bayes logit is zero. For balanced binary logistic
risk and smooth bounded logits `r_k(x)=sin(kx)/k`,

    R(r_k)-R(0) <= E[r_k(X)^2]/8 <= 1/(8k^2),
    E[|r_k'(X)|^2] = E[cos(kX)^2] = (1+exp(-2k^2))/2.

The first line follows from the pointwise logistic risk's second derivative
being at most `1/4`; the second is the Gaussian characteristic function.
The loss tends to optimum but derivative energy does not tend to zero.
This is a mathematical diagnostic, not an assertion that the fixed network
class realizes all these functions. It shows why a claim covering arbitrary
smooth logits needs additional quantitative regularity or coercivity.

Accordingly, any future path-error result must separately control coordinate
gradients, jump likelihood-ratio increments, initial-law error and numerical
error under the measures appearing in that result. Neither Bayes optimality,
classification calibration, precision parity nor exact checkpoint replay
supplies those controls by itself. Restoring a path theorem requires a new
explicit statement and proof; the retired C17 record is not amended here.

## 5. Scientific experiment and release implications

The next informative experiment should use a problem with a known or
independently computable conditional target. Measure conditional count/key
and continuous-coordinate quality, association ambiguity, and calibration
under the same noisy observation law for both methods. Report initialization,
matching and sampling work as part of method cost. A lower training loss
alone is not evidence of a better generative model.

Control experiments should include empty/duplicate configurations, atomic-only
and mixed fibers, rare observed keys, informative versus weak guides, and
observation-noise/target-regularization sensitivity. These need not all be
large GPU runs. A small analytically anchored experiment can disprove a
proposed claim earlier and more cheaply than a large real-data sweep.

The repository should expose the scientific contract: normalized reference
sampling/evaluation, valid event/key representation, observation sampling and
likelihood, training objective, sampler, and evaluation. Readers need small
CPU examples, configuration-driven GPU recipes and documented approximation
limits. Databricks, AWS identities and private paths are not mathematical
requirements. Numerical tests remain valuable supporting evidence, but test
counts should not be presented as theorem or novelty counts.

## 6. Review boundary

This audit read the current mixed-domain mathematical specification, the C17
retirement record and the relevant BASE/joint-product implementation paths.
It used five cited primary works and performed no model execution. No
production claim, statistical result, data admission, paid compute approval
or broad novelty judgment follows from this document.

### Independent read of the consolidated draft

The concurrently prepared [scientific core](hybrid_diffusion_scientific_core_v1.md)
and [claim/proof plan](hybrid_diffusion_claims_and_proof_plan_v1.md) were reviewed
independently. The displayed arguments for reference normalization/balance,
target domination, the BASE excess identity, balanced logistic excess and
limited target shift were checked. In particular, the positive linear jump
term, the reversed edge-density factor `f(y)`, the logistic `1/2` class weights
and the conditional bound's evidence denominator are consistent.

Review feedback requested two clarifications in the scientific core: DIR
initialization uses the zero-clock likelihood rather than the propagated
G+R guide, and the nuisance/residual decomposition is not identifiable. A
state-independent time offset may be absorbed in the gated residual where
its approximation class permits; query-dependent evidence alone is not a
proof that the whole classifier class cannot represent the Bayes logit.
The actual unresolved questions are representability under that gate and a
common path-law interpretation. The source author incorporated this feedback.

This completes a bounded independent algebra/assumption read of those working
propositions, not final theorem selection, a full guide/initializer proof,
global regularity verification or external peer review. Those remaining
scientific tasks should stay open in the plan.
