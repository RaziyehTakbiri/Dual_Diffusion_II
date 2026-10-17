# Prospective CPU multi-seed continuous-fiber comparison

Protocol date: 2026-09-13. This document specifies the experiment before its
default results are inspected. It is a bounded mechanism comparison, not a
powered paper-level superiority study. Any subsequent result belongs in a
separate report; do not rewrite these choices to fit the observations.

## Scientific question and fixed scope

Do the actual mixed neural G+R and DIR implementations approach the same
independently computable conditional target under matched training work, and
how do observed errors compare with guide-only and initialization controls?

The [mixed conditional contract v3](../manuscript_v3/hybrid_diffusion_mixed_conditional_contract_v3.md)
applies. The BASE is a frozen all-zero neural model; the independent target is
the exact continuous-time, cap-one CTMC/OU posterior. The training population
uses the actual common-grid numerical sampler and is not silently equated with
that continuous-time law. All data and observations are invented.

The full actual key/fiber reference and selected key remain those of the
[preceding continuous-fiber benchmark](MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md).
The selected key mass is computed from that reference, not rounded. OTHER is
materialized using the original reference restricted to non-selected keys,
including their actual continuous or atomic fibers.

## Predeclared roster and work

| Choice | Fixed value |
|---|---|
| Scenario A | theta=0.8, observation coordinate y=0.7 |
| Scenario B | theta=2.5, observation coordinate y=1.4 |
| Other process/channel parameters | death rate=1, OU rate=1, horizon=1, clean hold=0, state cap=1, observation cap=1, observation noise SD=0.5, whole-channel contamination=0.1 |
| Initial unconditional law | Stationary capped reference law, with standard-normal continuous coordinates |
| Grid for every actual-sampler route | 0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1 |
| Neural methods | association-aware-guide-plus-residual; unified-direct-conditioner |
| Training/initialization seed roster | 1201, 1202, 1203 |
| Neural gate | LINEAR_ACTIVE_TIME_V1, opt-in; legacy policy unchanged |
| Training per scenario/method/seed | 32 optimizer updates, 2 joint/product pairs per update |
| Recorded training loss | All 32 updates |
| Separate synthetic validation-pair loss | At updates 0, 8, 16, 32; fixed 32-pair roster evaluated in bounded chunks of 4 |
| Endpoint evaluation | Final update 32 only, 512 draws per scenario/method/seed |
| Control evaluation | Five control routes per scenario, 2,048 draws each, once per scenario |
| Runtime scope | One local CPU child, one intra-operation thread, 2,400-second hard child deadline |

Initialization, training, validation and evaluation namespaces are separately
derived from the declared seeds and recorded by the implementation. Within a
scenario and seed, the two methods start from matched neural tensors and share
the same declared training-pair law. Distinct physical-law namespaces need not
produce identical per-draw randomness: **common random numbers between neural
methods are not claimed**. Pairing below means the fixed training-seed and
evaluation-record indices.

Changing theta and y together gives two joint scenarios. This is not a
factorial experiment identifying the separate effects of cap pressure and
observation location. Three declared seeds are not a representative sample of
every possible initialization or training run.

There are 12 final neural rows, 10 control rows, 6,144 neural endpoint draws,
20,480 control draws and 384 neural optimizer updates. Training consumes 768
joint/product pairs. The four fixed validation evaluations contribute 1,536
pair-loss evaluations across the 12 fitted models; reuse of a fixed validation
roster is not 1,536 independent validation datasets. Report actual generated
paths and validation reuse separately.

Validation losses use disjoint synthetic validation streams, not the final
endpoint-evaluation roster. No minimum-loss checkpoint, favorable seed,
scenario, observation, grid or sample is selected.

## Controls and interpretation

Each scenario has these five controls on the same eight-step grid where a
sampler is used:

1. Direct draws from the independent endpoint posterior.
2. Independent exact capped h in the actual sampler, with the independent exact
   conditioned initial law.
3. The same exact capped h and sampler, with the uncapped future-reference guide
   initializer conditioned at the initial cap.
4. Uncapped future-reference guide-only h and its corresponding guide
   initializer, with no trained residual.
5. Zero-clock observation-likelihood h and its zero-clock initializer, with no
   trained residual.

Contrasting controls 2 and 3 changes initialization while keeping numerical
transition coefficients and grid fixed. Contrasting controls 3 and 4 changes
the physical guide while keeping the guide initializer fixed. These are
controlled numerical-law contrasts, not additive TV/KL error decompositions.
Control 5 is the untrained DIR baseline; control 4 is the untrained G+R baseline.
The two trained methods still intend the same conditional target.

An independent closed-form guide/control implementation must retain the same
uncapped-reference and initial-cap convention and be checked against the
existing association implementation before use. A faster prepared sampler
must preserve frozen weights, context, grid, initializer and law identity.
Preparation is an efficiency measure, not a new statistical target.

## Fixed observables and primary reports

Let L=24. The observable vector contains three category indicators in order
EMPTY, OTHER, CONTINUOUS, followed by 21 indicators

    1{selected continuous key is present and coordinate <= x},
    x = -3, -2.7, ..., 2.7, 3.

These are joint CDF probabilities, not CDFs conditioned on observing that key.
The independently computed target vector p is scenario-specific.

For each route report the full empirical indicator vector, its target vector,
largest category error, and largest joint-CDF-grid error. Define the combined
finite-indicator discrepancy E=max_l |q_l-p_l|, where q is a route's true
indicator-probability vector. Its estimate replaces q by empirical means.
This is neither total variation over the continuous state space nor KL.

For each neural method/scenario additionally report:

- Every seed's two discrepancy metrics and combined discrepancy, with draw count.
- The equal-weight three-seed mixture's indicator vector and discrepancies.
- Mean, range and sample SD of the three seed-specific estimated discrepancies.
- Paired, seed-indexed G+R minus DIR discrepancies and their descriptive mean.
- The paired difference between methods' seed-average signed indicator vectors.

The mixture is a different estimand from the average seed-specific discrepancy:
max of an average can hide opposing seed biases. Always display both. Seed SD
and range computed from empirical discrepancies contain Monte Carlo noise;
they are not purified estimates of training instability. Coordinate means and
variances, training losses and validation losses remain descriptive diagnostics.

## Monte Carlo uncertainty, separate from training-seed generalization

Condition on all fitted models and the predeclared scenario/seed roster.
Assume ideal independent evaluation record draws within each fixed route, and
independence across record pairs where paired contrasts are used. Dependence
between the two methods within a record pair is allowed. Deterministic keyed
pseudorandom streams do not themselves prove these ideal assumptions.

For independent bounded variables, Hoeffding's inequality bounds deviation of
their sum about its own expectation without requiring identical means. We use
its two-sided form and a union bound. Bibliographic basis:
[Hoeffding (1963), Journal of the American Statistical Association 58(301), 13–30](https://doi.org/10.1080/01621459.1963.10500830);
[primary paper scan](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf).
The following finite-roster allocations and applications are this protocol's
derivation, not an additional claim from the source.

The total failure probability alpha=0.01 is split in advance:

| Family | Members | Allocated alpha |
|---|---:|---:|
| A: individual route indicator means | 22 routes times 24 indicators | 0.005 |
| B: neural three-seed mixture indicator means | 4 scenario/method mixtures times 24 indicators | 0.0025 |
| C: paired seed-average signed method differences | 2 scenarios times 24 indicators | 0.0025 |

No independence between these families or between indicators is required for
the union bound. The complete three-family statement concerns only evaluation
sampling conditional on these fitted models, not inference over unseen seeds.

### A. Per-route means and discrepancy intervals

For n draws in a route, use

    w_route(n) = sqrt(log(2 * 22 * L / 0.005) / (2*n)).

Simultaneously for all 22 route vectors, every empirical indicator mean is
within this half-width of its own route probability except on an event of
probability at most 0.005. The widths are 0.1094221364 for n=512 and
0.0547110682 for n=2,048.

The map q -> max_l |q_l-p_l| is 1-Lipschitz in the maximum norm. Consequently,
E lies in [max(0, E_hat-w), min(1, E_hat+w)] on the same event. The same
statement holds for the category-only and joint-CDF-only maxima. These are
finite-observable discrepancy intervals, not bounds on unobserved tails,
all measurable sets, full posterior approximation error or TV.

For a paired seed's discrepancy difference Delta=E_GR-E_DIR, the interval
Delta_hat +/- (w_GR+w_DIR), intersected with [-1,1], is valid on family A's
event. Averaging these paired seed differences preserves that conservative
half-width when draw counts are equal. It does not create extra training seeds.

### B. Equal-weight seed mixtures

There are S=3 seeds and n=512 draws per seed. Define

    q_bar = (q_1201 + q_1202 + q_1203)/3,
    qhat_bar = (qhat_1201 + qhat_1202 + qhat_1203)/3.

The Sn=1,536 bounded evaluation variables need not have equal expectations.
Conditional independence suffices for

    w_mix = sqrt(log(2 * 4 * L / 0.0025) / (2*S*n))
          = 0.0605125673.

This covers all four mixture indicator vectors with allocated alpha=0.0025.
The maximum-error Lipschitz argument above also supplies intervals for mixture
discrepancies. A difference of mixture discrepancies uses half-width 2*w_mix.
These are statements about these three fitted-model mixtures, not the
distribution of a new training seed.

### C. Paired signed indicator contrasts

For fixed scenario, seed and record index, let

    D_sj,l = I_GR,sj,l - I_DIR,sj,l, in [-1,1].

Its average over Sn records estimates q_bar_GR,l-q_bar_DIR,l. Applying
Hoeffding with range length two gives the simultaneous half-width

    w_pair = sqrt(2 * log(2 * 2 * L / 0.0025) / (S*n))
           = 0.1172371436.

The factor two inside the square root reflects the range [-1,1]; using the
Bernoulli range-one width here would be wrong. The mean contrast can be
computed from paired seed mean vectors without storing raw record pairs.
Independence between methods is not required, and shared random numbers are
not claimed. A signed indicator difference is not itself a difference in
closeness to the target; report the separate discrepancy contrasts as such.

### Power and permitted conclusions

These conservative widths are known before execution. In particular, 512
draws per fitted model and three seeds do not promise resolution of differences
of a few percentage points. A comparison can be inconclusive; completion is
not a quality pass. Do not increase budgets or switch statistics after viewing
which method looks favorable in this run.

Do not use a normal-theory three-seed standard error or a tiny-seed bootstrap
to claim reliable generalization over training randomness. The protocol
separates conditional draw-noise bounds from descriptive seed variation; it
does not solve training-seed population inference. Lower loss does not certify
coordinate-score accuracy or conditional sampling quality.

## Matched work, costs and failure handling

Both neural methods get equal update counts, pair counts, checkpoint-loss
rosters and final draw counts, not a claim of equal wall-clock cost. Report
setup/preparation, training, validation and sampling time separately when
available; include actual path/macrostep counts and initialization work.
State which costs are included. No GPU speedup or cost-to-quality crossing is
claimed: no quality threshold or repeated stopping rule was selected here.

Run once with the fixed default work under the supervised 2,400-second CPU
deadline. Reduced budgets are for tests and must not be presented as default
evidence. Resource exhaustion, non-finite values, failed sampling or timeout
stop the run and preserve an honest incomplete/failure report; there are no
automatic retries, replacement samples or best-seed selection. A later
engineering-correction rerun must retain and distinguish the earlier outcome.

No paid/cloud job, GPU operation, real-data admission, F105 evaluation,
general neural posterior theorem, successor checkpoint-resume qualification,
production amendment or formal plan-closure claim is authorized by this
experiment. Its scientific output is the complete declared comparison, with
uncertainty and approximation scopes visible.
