# Adopted mixed-domain scientific direction

Date: 2026-09-08.

Decision: **ADOPTED STRUCTURAL AMENDMENT; NUMERICAL INSTANCE AND PRODUCTION INTEGRATION OPEN**.

Authority: the user asked to fix the domain-representation/observation mismatch
and delegated the scientific choice to the assistant, prioritizing a strong
ICML/ICLR/NeurIPS-quality contribution. This authorizes the local design,
code, synthetic checks and plan amendment below. It does not authorize paid
jobs, real-data access, training, or assertions of publishability.

## Selected design and why

We select a mixed discrete/continuous, variable-cardinality model. Exact
metadata live in a countable key space; only genuine continuous magnitudes
have log-value coordinates. A normalized factorized reference covers the
declared semantic carrier without a finite observed vocabulary. Zero,
missingness, timestamps, quantities, identities, and GCS/MechVent values stay
atomic. Birth/death changes the configuration; OU diffusion moves only the
continuous coordinates. The initial replacement rate is explicitly zero.

Two statistical changes are inseparable from this repair:

1. The training target is a Gaussian lift of the finite TRAIN empirical law,
   mixed with a positive reference component. This gives a positive smooth
   reference density even during the clean hold. It is **not the unchanged
   empirical target**, and reference contamination also changes metadata/count
   probabilities.
2. Half-thinning remains occurrence-wise with probability 1/2. Retained exact
   keys stay exact, but genuine continuous values receive Gaussian noise in
   their log chart. A whole-observation reference mixture supplies common
   support, including empty and overflow observations. The original continuous
   identity channel is superseded, not merely relabeled as smooth.

The selected reference family mixes an exact complete-key frequency law fit
only from TRAIN with a positive universal grammar component. It therefore
improves mass on observed TRAIN keys without restricting support to their
vocabulary. Its mixture weight is a prospective scientific setting shared
across methods. Unseen held-out keys still rely on the universal branch;
this is not a claim to solve rare-key conditional sampling by itself.

The exact laws, quotient factorials, reversibility argument, initial-density
regularity, matching likelihood, auxiliary guide and bounds are derived in
[the mathematical specification](PROJECT_MIXED_DOMAIN_SCIENTIFIC_AMENDMENT_MATH.md).
In particular the guide is the **uncapped independent-reference guide**
restricted to capped states; it is not silently promoted to the capped or
learned-base conditional likelihood. The cap-defect and learned-residual
obligations remain real.

We reject treating an arbitrary F105 vector as a generative state, adding
noise to discrete coordinates and rounding them afterwards, retaining an
atomic empirical target during a claimed smooth clean hold, or limiting the
reference to observed keys. Each would leave a scientific mismatch hidden.

## Contribution and evaluation discipline

Jump-diffusion generation of variable-dimensional data already exists; it is
not itself a novelty claim for this manuscript. See Campbell et al.,
[Trans-Dimensional Generative Modeling via Jump Diffusion Models, NeurIPS 2023](https://arxiv.org/abs/2305.16261).
Our research direction is the association-aware conditional guide/residual
construction on unordered mixed event configurations, with explicit
approximation/error accounting. Its novelty relative to the full literature
and its empirical value are still to be demonstrated, not assumed from this
design decision.

The amendment adds a checkable approximation statement. For the unchanged
F105 kernel, with all its adopted scales equal to one,

    MMD(P_TRAIN, Q_0) <= (1-alpha) tau sqrt(2/pi)/4 + alpha sqrt(2).

The sharper lift term multiplies by E[n_cont/n; n>0]. This is an ideal-law,
unconditional bound against the finite training empirical distribution, not
a population-generalization, posterior, learned-sampler or finite-precision
guarantee. The mathematical note gives the separate likelihood/evidence
dependence needed for conditional comparisons. Letting alpha and tau shrink
reduces target bias but worsens density/derivative conditioning; this tradeoff
must be measured rather than hidden.

All comparators must use the same declared target lift, observation channel,
splits, scoring rule, and accounting units. Validation/test truths stay RAW;
only their observations use the amended channel. Do not smooth held-out
truths to make the model appear correct. Separate target regularization from
observation noise in a prospectively fixed sensitivity study. Select and
freeze its numeric grid, default rule, replication, budget and stopping rule
before outcome-dependent comparison; no test-set tuning or unreported
post-result changes. No arbitrary synthetic test constants are adopted as
scientific hyperparameters by this record.

## Completed local implementation

- [Factorized state/reference](src/heterodiff/data/two_domain_factorized_state.py):
  exact metadata keys, 0/1D fibers, normalized integer/rational/UTF-8 reference
  grammar, exact/log-space key masses and explicit conversion errors.
- [Smooth-law oracle](src/heterodiff/theory/factorized_smooth_amendment.py):
  quotient-normalized training lift, positive target mixture, matching-sum
  retained/overflow likelihood, terminal and propagated auxiliary guide,
  finite-RNG synthetic sampling and the unconditional F105 bias bound.
- [Shared metadata energy](src/heterodiff/models/factorized_configuration_energy_torch.py):
  complete canonical byte input rather than per-type learned heads, separate
  true 0/1D tensors, permutation/duplicate-preserving bounded CPU FP32 energy.
  Its exact count is 96,705 per energy, not the full method parameter budget.

These are bounded local components. The oracle supports up to 128 events and
12 anchors per exact key by default and refuses larger computations. Those
limits neither replace the domain caps nor permit dropping data. Ideal
countable support is not a claim that a finite PRNG/binary64 implementation
exactly samples the ideal law. The shared encoder processes every supplied
byte but its learned finite-dimensional representation is not injective.
The broad semantic GCS/MechVent carrier is not a clinical-validity certificate.

Independent mathematical review checked the reference normalization,
quotient/duplicate factors and guide formulas. Review-driven numerical fixes
reject invalid variances, NaN/infinite log arithmetic and underflow that would
silently delete a probabilistic branch. This is not a global interval-numerics
or countable-fiber path-KL certificate.

## What this closes, and what follows

The **structural scientific decision and its bounded local implementation are
complete**. The earlier "which model/observation family?" decision is no longer
waiting for user input. This is a coherent replacement specification, not
full production closure or a theorem transferring every old certificate.

F063/F064/F065 and F069/F070/F071 retain their finite-type predecessor
source/configuration/count evidence only. They do not freeze the full new
method; 96,705 is a single-energy count, excluding external observation and
nuisance components. No full-method successor budget is implied.

**Later same-day integration completed:** the factorized state/reference/guide
is now connected to actual BASE and conditional losses, full-interval independent
learned-BASE pairs, cap-correct reference-posterior initialization and learned
birth/death-OU paths. See the [local integration record](PROJECT_FACTORIZED_CONDITIONAL_PIPELINE_LOCAL_INTEGRATION.md).
The efficient reference-posterior initializer is implemented for retained and
overflow observations; it is no longer merely the next strategy.

Next, prove or explicitly bound the additional derivative/path/numerical
obligations and qualify larger matching/count workloads. The jump-thinning
envelope can still be costly for rare keys; initializer improvement alone does
not establish scalable conditional sampling. Specify the prospective numeric
regularization/noise sensitivity design and update all affected compute totals.
Prepare the explicit device-local successor and bounded parity qualification;
no container/ECR setup or paid launch is requested by this local milestone.

Real-data support/admission, source-origin/round-trip treatment, split
feasibility, full numerical science settings, complete resource/spend/storage
limits, GPU/runtime qualification, full formal tests and empirical results
remain open. The accepted CPU lock and its 323-source/235-test historical
receipt are preserved and do not qualify these additions.

Six observation fields are reopened honestly: F025/F032/F035 for PhysioNet
and F044/F052/F055 for Retail. Their frozen predecessor remains historical;
the adopted structural successor requires a fully specified numeric instance
and matched code/review before these fields close again. F033/F034/F053/F054
were already open. B02/B03 were already open, so no further checkbox reopens.
Current totals: **61 checked / 102 open / 163 timetable tasks; 31 fields open /
141 closed (PRE 30/136, POST 1/5); 8 blockers open / 4 closed; Formal Tests
28/29/30 OPEN/OPEN/PENDING; scientific results 0/4**.

Verification: **1,022 selected local CPU tests passed** (423 focused
and adjacent-component cases plus 599 broader regression cases). Static checks
passed and all 323 accepted CPU source hashes/sizes remained unchanged. See the
[verification record](PROJECT_EVIDENCE_LEDGER.md#2026-09-08-mixed-domain-scientific-amendment-and-local-verification)
for the exact scope; no new Databricks or GPU success is claimed.
