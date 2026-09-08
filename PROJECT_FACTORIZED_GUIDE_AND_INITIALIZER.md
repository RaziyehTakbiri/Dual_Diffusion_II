# Factorized analytic guide and reference initializer — local implementation

Date: 2026-09-08. Scope: additive local/synthetic CPU implementation of the
selected mixed-domain structural amendment. No data admission, real-data run,
paid compute, numerical parameter adoption, GPU qualification, or transfer of
the historical frozen CPU certificates is claimed.

## Implemented interfaces

`src/heterodiff/theory/factorized_association_guide_torch.py` exposes
`FactorizedAssociationGuide(oracle)` with three operations:

- `log_value(state, observed, coordinates=None, jump_clock=..., continuous_clock=...)`
  computes the actual per-exact-key partial-matching log dynamic program. Its
  scalar result is a differentiable CPU float64 tensor. Aligned coordinate
  tensors have shape `(1,)` for a continuous fiber or `(0,)` for an atomic
  fiber; gradients preserve the supplied occurrence order, including repeated
  keys. Structural impossible branches are removed before log-sum-exp, so
  impossible clean matches, empty graphs, and overflow have finite zero
  derivatives when appropriate. There is no artificial atomic coordinate.
- `upper_log_bound(observed)` evaluates the fixed-observation envelope from
  the mathematical note. It is a finite-arithmetic evaluation of that bound,
  not an interval or global numerical certificate for the learned graph.
- `sample_reference_posterior(observed, rng, jump_clock=..., continuous_clock=...)`
  implements the retained and overflow reference-initialization formulas. It
  returns a canonical tuple of exact-key events, preserving multiplicities.

The guide deep-copies the supplied oracle/reference and records an identity
including its parameters, limits, domain, and any supplied TRAIN-key mixture
roster. This is an explicit local snapshot, not authentication that a caller's
roster was admitted TRAIN data. Numeric scientific parameters remain supplied
by the caller.

## Exact target of the initializer

The guide is the **uncapped auxiliary** birth/death/OU propagated observation
likelihood, evaluated at capped states. It is not the exact propagated
likelihood of the capped reference process and is not the learned BASE
likelihood. The cap-defect distinction in
`PROJECT_MIXED_DOMAIN_SCIENTIFIC_AMENDMENT_MATH.md`, section 6, is unchanged.
At zero clocks the same interface evaluates the actual amended terminal
observation likelihood, as used by DIR.

The initializer implements the section 6.2 probability law proportional to
`Pi_N(state) * h_tilde(state, observed)`. For retained observations, it selects
the whole-observation contamination branch using its evidence weight. In the
clean branch, observed ancestors and the independent unobserved Poisson
population are conditioned on their **joint total count** being at most N.
It does not truncate a sampled configuration, independently cap components,
or rejection-sample an exact rare metadata match. Ancestor coordinates use
the derived Gaussian conditional distribution within their existing fibers.

For overflow, it samples the count from weights proportional to
`p_N(n) * h_tilde(n, overflow)` using a binomial/Poisson tail recurrence, then
draws iid event marks from the normalized reference. The observation's
overflow bit is not reinterpreted as an ordinary empty observation.

The implementation does not target a Q0 or learned-BASE posterior. A physical
conditional sampler may follow it with bounded **residual-only** acceptance;
the BASE energy and observation-only nuisance must not enter that correction.
That connection is implemented and tested separately by the conditional
sampler/learner modules, not certified by this module alone.

## Numerical and resource boundaries

Per-key matching, count recurrences, and materialized events have explicit
work limits. These are refusal limits, not reduced scientific cardinality
caps. A sampled count exceeding local materialization limits causes refusal,
not dropping events or redrawing until a smaller count appears.

Categorical selection uses a log exponential race, preserving log weights
without converting tiny masses into a probability floor. PCG64/PCG64DXSM,
binary64 normal/exponential variates, and finite arithmetic are numerical
approximations to the ideal laws. Endpoint/nonfinite/underflow cases refuse
where required; exact ideal sampling, rare-event accuracy at arbitrary scales,
and successful execution at full real-domain caps are not claimed.

## Local verification

The focused guide/initializer suite passes **64 synthetic tests**. Coverage
includes actual numeric-oracle value parity for retained/empty/atomic/mixed/
overflow observations, first and second coordinate finite differences,
repeated-key occurrence order, finite impossible-branch gradients, fixed
observation bounds, capped retained/overflow count laws, Gaussian ancestor
moments, seeded replay, TRAIN-mixture identity, and resource refusal without
changing the law. No real data or GPU was used.

This completes the bounded guide/initializer implementation milestone. It
does not close whole-model training, sampling convergence, generalized
theorem qualification, the numerical amendment instance, or either complete
project track.
