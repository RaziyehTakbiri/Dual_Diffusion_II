# F109--F112 statistical successor to the F105 metric display

**State:** `F105_R64_EFFECT_FLOOR_AND_HOLM_HOEFFDING_STATISTICS_FROZEN_PREOUTCOME`  
**Predecessor preserved:** `manuscript_v3_f105_metric_integration_successor_v2.md`

The F105 theorem and general production evaluator support the exact formal
domain `2 <= R <= 128`. The confirmatory analysis is a narrower, additive
selection: every case uses exactly `R=64` conditional draws per method. The
only supported production-facing confirmatory entrypoint is
`fixed_r64_cks_statistical_adapter.py`; it consumes explicit canonical
address-bearing rows, refuses every other draw count, and requires unique
within-case addresses plus byte-identical method-neutral direct/guide address
rosters before calling the general evaluator. Thus the predecessor's supported
range remains true while F109 and the supplied-roster pairing rule are now
code-matched.

For each case, direct and guide use the same target and matched draw addresses.
The adapter certifies consistency of the caller-supplied address rosters, not
the provenance of the configurations; later execution custody must prove that
the declared addresses are truthful and that the streams meet the required
law.
The primary score is the displayed F105 off-diagonal U-score. A single-method
score is in `[-2,1]`, so the paired direct-minus-guide value is in `[-3,3]`.
Positive values favor the guide. The domain estimand retains the frozen F137
aggregation and is the equal mean over 256 complete training-seed aggregates.

The minimum meaningful effect is exactly `delta0=1/100` CKS score-difference
units. For domain `d`, the confirmatory hypothesis is

```text
H_d: theta_d <= 1/100  versus  A_d: theta_d > 1/100.
```

For the complete bounded seed roster, the one-sided confidence method is

```text
L_d(alpha) = mean_s M[d,s] - 6 sqrt(log(1/alpha)/(2*256)).
```

Logarithms and square roots are outward-enclosed with exact rational
arithmetic. The corresponding Hoeffding exponent is compared directly with
certified upper enclosures of `log(40)` and `log(20)` under the frozen
two-domain Holm order. An exponent tie orders R3-PHYS before R4-RETAIL. Both
domains must reject; one domain cannot rescue the other. There is no bootstrap
or alternate confidence fallback.

The real--real floor is a validation-only descriptive negative control: the
nearest-rank 95th percentile of 256 deterministic domain-separated balanced
group-disjoint splits, each evaluated by biased empirical MMD-squared using the
same F105 configuration kernel. It is never subtracted from the primary score,
used as its uncertainty, or used to tune `1/100`.

The earlier F105 integration statement that F109--F112 remained open was exact
for that immutable package checkpoint. That predecessor now has an independent
`GO` receipt with no P0/P1/P2 findings and is byte-bound by this successor's
qualification package. This additive successor freezes those four fields and,
upon its own independent acceptance, completes B04's pre-outcome definition.

This successor reports no floor value, score, interval, p-value, pilot, model
run, Formal Test, result, domain admission, scientific claim, or execution
authority. Missing roster, pairing, boundedness, stream-law, custody, or
certification evidence is terminal no-go, not permission to change `R`, the
effect, floor, or confidence method.
