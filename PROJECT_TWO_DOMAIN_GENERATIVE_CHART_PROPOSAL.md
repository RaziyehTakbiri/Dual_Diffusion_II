# Two-domain generative-chart proposal

Status: **local proposal and executable support audit; not scientific adoption**.
The accepted F105 metric, B06 registry, half-thinning observation kernel,
323-file CPU release, data-admission rules and project caps are unchanged.
No dataset was acquired or opened, and no paid job or scientific run occurred.

## Outcome

There is no legal inverse that turns arbitrary Gaussian vectors in R112 or R10
into the frozen PhysioNet/Retail event schema while preserving the declared
bijective-chart continuous objective. Those dimensions belong to an injective
metric embedding, not an onto generative chart. Nearest one-hot selection,
timestamp/quantity rounding, string-code projection, missingness thresholding,
or post-sampling metadata replacement would change the model law and is not
implemented here.

The new module supplies two useful executable boundaries:

1. An exact inverse/image-membership check for the frozen semantic F105 maps.
   Invalid coordinates fail rather than being repaired.
2. A compatible **explicit finite subset** of typed fibers: all discrete
   fields are stratum labels, a positive/negative scalar mark has one Euclidean
   log coordinate, and zero/missing marks have no continuous coordinate.
   These fibers work with the existing capped Gaussian reference and yield
   legal F105 events through the frozen public generated-value factories.

This completes a local chart-interface implementation, not a full-domain
generative schema. A prospective schema/reference/architecture revision is
still required before real-domain training can use it.

## What the existing sources actually require

`manuscript_v3/executable_method_spec.md` §2.1 places atomic time and other
atomic coordinates in the discrete stratum label; only atomless coordinates
have bijections to an open Euclidean fiber. Section 4.2 explicitly excludes a
non-bijective or finite-boundary transform from its continuous relative-score
objective. `events/schema.py` likewise requires exact boundary atoms to be
separate discrete types/fields, not clipped into open supports.

In contrast, `two_domain_baseline_registry.py` currently freezes
`ONE_F105_EXACT_VECTOR_TYPE_PER_DOMAIN`, with 112 PhysioNet coordinates and 10
Retail coordinates. The mismatch is therefore not a Databricks configuration
problem: it is an unresolved executable model-space choice.

The authoritative metric maps are
`evaluation/two_domain_count_normalized_event_cks.py` and
`PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md`. The semantic inverse checks:

| Field | Exact image constraint; no repair permitted |
|---|---|
| PhysioNet parameter | Exactly one of 37 one-hot positions is 1; the rest are 0. |
| PhysioNet elapsed time | t/2880 for an integer t in the closed interval 0..2880. |
| PhysioNet missingness/value | Only the selected variable may have a nonzero mask/value; mask is 0 or 1; missing has zero payload; present v>=0 maps to v/(1+v). |
| Retail invoice/string fields | A valid finite UTF-8 length-prefixed integer code, followed by the frozen token grammar and byte limits; no normalization or trimming. |
| Retail cancellation | Exactly 0 or 1 and consistent with the preserved invoice token, including its c/C case. |
| Retail optional text | Missing and present-empty remain different; a missing mask requires zero payload. |
| Retail time | Exact integer source-civil microseconds in the frozen half-open horizon; Gregorian calendar reconstructed without a timezone conversion. |
| Retail Quantity | q/(1+abs(q)) with integer q, not an arbitrary real. |
| Retail UnitPrice | Signed rational v/(1+abs(v)); no positive-price-only assumption. |

The frozen `ExactEvent` class checks exact Fraction carriers and dimensions,
not all of these image conditions. Successfully constructing or scoring that
carrier therefore does not itself prove a legal raw-domain decoded event.
The new audit is additive and does not reinterpret existing score receipts.

Decoded records are **semantic records**, not byte-for-byte source records.
For example, `80`, `80.0` and `+080.00` have the same metric value. The inverse
cannot recover which spelling was used, original row ordinals, file bytes,
patient/customer identifiers, or static context. Existing supplied-input
adapters retain those separately. Duplicates are never dropped.

The inverse recognizes the frozen mathematical rational event image. It is
not a claim that every rational has an allowed <=256-character source decimal
spelling or an exact binary64 generated representation. Exact source grammar
and generated-value numeric policy remain separate boundaries.

## Executable supplied-fiber proposal

`data/two_domain_generative_chart_proposal.py` exposes:

- `decode_metric_event` and `audit_metric_configuration` for exact image checks;
- `PhysioFiberKey(elapsed_minutes, parameter)`;
- `RetailFiberKey(invoice_no, stock_code, description, quantity,
  invoice_calendar, country)`;
- `ScalarFiberSpec(event_type, key, branch)`; and
- `ScalarFiberChartProposal(fibers)` with explicit encode/decode methods.

PhysioNet branches are `MISSING`, `ZERO`, `POSITIVE`. Retail branches are
`NEGATIVE`, `ZERO`, `POSITIVE`; required UnitPrice has no missing branch.
For positive v use r=log(v); for negative price v use r=log(-v).
The inverse is +/-exp(r). Zero/missing strata are genuinely zero-dimensional.
Discrete keys never enter an OU coordinate or get overwritten after a draw.

The test fixtures explicitly supply only HR at minute 0 and one synthetic
Retail metadata tuple, plus their scalar branches. They are not a selected
production subset, a fitted codebook, an instruction to discard other rows,
or proof of full-domain coverage. Unknown keys/types fail. The module chooses
no reference weights, activity, cap, missing/zero probabilities, clinical
range constraints, source categories or scientific support exclusions.

The implementation uses binary64 exp/log and refuses overflow/underflow.
Analytic bijectivity does not imply machine-bitwise inversion. Encoding uses
`REQUIRE_EXACT_BINARY64` by default. A caller may explicitly select the
proposal policy `ROUND_TO_BINARY64_WITH_EXACT_ERROR_RECORD`; the returned
record retains the original Fraction, represented native value, exact
conversion error, and exact decoded log/exp round-trip error. No conversion
policy is adopted by this local implementation. This documented scalar
conversion is distinct from—and does not authorize—rounding illegal discrete
metric coordinates into valid labels.

The support audit and configuration decoder have a 4,096-event local resource
limit and a 65,536-bit exact-coordinate bound. These are rejection limits for
this new bounded utility, not revised scientific domain caps. Refusal at a
local arithmetic limit is distinguished from an off-image event finding.

## Why a full reference/schema successor is necessary

Even a literal PhysioNet flattening of only minute, variable and
missing/zero/positive strata requires

`2,881 × 37 × 3 = 319,791` discrete strata.

That already exceeds the existing reference's 4,096-type implementation limit.
Retail has 63,849,600,000,000 source-civil microsecond atoms before invoice,
stock, description, country and integer-quantity labels are combined. Bounded
UTF-8 strings have a finite but enormous roster; Quantity is not assigned a
finite support bound by F105. A complete flat enumeration is not supplied here.

The current general reference also has a 100,000 cardinality implementation
limit, versus frozen F105 caps 131,072 and 1,067,371. The B06 registry separately
records a 10,000 native-runtime cap. None may be reconciled by truncating,
excluding, top-coding, resplitting or silently changing accepted caps.

The preferred investigation direction is a **factorized atom-bearing state
and reference**, with explicit normalized discrete laws and balanced jumps,
plus Euclidean coordinates only for genuinely continuous fields. This requires
new reference sampling/rate machinery and an architecture/capacity successor,
not just a decoder. The following choices are still prospective:

1. Whether decimal-valued marks are modeled as exact recorded atoms or as
   measurements of continuous latent quantities. The former requires a
   discrete/atomic law; the latter needs an explicit measurement/quantization
   likelihood and target-space definition. Log transforms alone do not settle
   that modeling choice.
2. Full-support discrete laws for times, strings, integer quantities,
   missingness and zero atoms, with tractable normalization and sampling.
   An observed-only vocabulary or time coarsening is not automatically allowed.
3. Matching B06 model interfaces, parameter counts, weights/state memory,
   fairness accounting and executable cap/resource limits.
4. Observation-reference and support mathematics consistent with the retained
   clean observation rule below.

No option is adopted, no new production codebook is generated, and no complete
schema is falsely declared finalized merely because the subset interface runs.

## Frozen observation rule remains unchanged

`PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` §3 already closes the clean
kernel definition as `OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1` for both
domains. Every occurrence is independently retained with probability 1/2;
retained type/time/marks are unchanged. There is no jitter, mark noise, type
confusion, clutter, imputation or group mixing. Source occurrence lineage must
remain separate from metric canonical sorting.

This chart proposal does not replace that kernel with Gaussian noise.
F033/F034 and F053/F054—the observation reference/common-support fields—remain
separate open obligations. Under an atomless continuous-mark model, nonempty
identity observations contain point mass at the source coordinates; a fixed
atomless Gaussian observation reference does not dominate those masses.
Adding a small Gaussian contamination component does not erase the retained
singular mass. An exact-record atomic model, a separately justified singular
theorem/implementation route, or an expressly authorized kernel/target
successor must resolve the issue; it cannot be solved by an undocumented
decoder projection.

## Local evidence and handoff

The new tests exercise all 37 PhysioNet parameters with missing/zero/positive
exact values, source-time endpoints, Retail Unicode/case/missing/empty fields,
maximum UTF-8 lengths, final civil microsecond, negative quantities/prices,
off-image rejection, multiplicity, local resource limits, explicit numeric
error records, and actual capped-Gaussian samples on the declared tiny fibers.

Initial focused regression: **197 tests passed**. The final run/review is
reported by the parent task; these tests are synthetic local qualification,
not real-domain training, source admission, full support certification,
scientific results or authorization to launch paid compute.
