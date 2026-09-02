# F105 exact two-domain count-normalized-event CKS instance

**Reported date:** 2026-09-01  
**Candidate state:** `F105_TWO_DOMAIN_CKS_EXACT_INSTANCE_FROZEN_PREOUTCOME`  
**Global scientific state:** `DRAFT_NOT_EXECUTABLE`  
**Primary metric ID:** `TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1`

## 1. Authority, purpose, and boundary

The two normalized visible user instructions authorizing this work are exactly:

> Adopt CKS for F105 and build the exact two-domain metric instance.

This text is 66 UTF-8 bytes and has SHA-256
`a185a475568c39c840cb4cf105321538d334ad0f81cfe3d7856edd6a3ae2abdc`.

> Makes sense, go ahead and finish the tasks you mentioned above.

This text is 63 UTF-8 bytes and has SHA-256
`9cc94897178bda0c7a8acc3d6a3a17e328640f2968ad3802f7fcfda5c4fa7898`.

They authorize the exact pre-outcome domain instance, its pure symbolic source,
qualification, independent review, and truthful tracker reconciliation. They do
not authorize dataset download or opening, authentication, contact, access
requests, entropy, training, scientific execution, result generation, claim
promotion, or submission. Raw conversation transport, account identity,
timestamps, signatures, and authority authentication are not bound.

This package uses read-only public documentation observations from exactly two
root pages:

- [PhysioNet Challenge 2012, version 1.0.0](https://physionet.org/content/challenge-2012/1.0.0/);
- [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii).

No dataset file or test set was downloaded or opened. No raw HTTP response,
HTML byte buffer, redirect history, transport count, page timestamp, or external
attestation is custodied. The facts below are normalized page observations, not
raw-byte receipts. Consequently F019--F022 and F038--F041 remain open even where
a page displays a version or license label.

## 2. Hard-bound mathematical route

The package binds the accepted generic theorem and exact symbolic reference
implementation. For a finite occurrence-expanded configuration `x`, let `n_x`
be its count and define

```text
m_x = (1/n_x) sum_i phi(T(e_i))  when n_x > 0,
m_empty = 0,
Phi(x) = (n_x, m_x).
```

For each domain, `phi` is the RKHS feature map of the Gaussian event kernel

```text
k_event(e,f) = exp(-||T(e)-T(f)||^2 / 2),
```

and the configuration kernel is

```text
k_configuration(x,y)
  = exp(-((n_x-n_y)^2 + ||m_x-m_y||^2) / 2).
```

Thus the frozen squared parameters are `a^2=b^2=tau^2=sigma^2=1` in both
domains. Count normalization prevents the preliminary raw-mean collision, the
positive count channel preserves multiplicity, and the empty configuration has
zero event channel. Each domain transform below is a Borel injection into a
finite-dimensional Euclidean space. The Gaussian event kernel is therefore
characteristic on the transformed event space; the count-plus-normalized mean
map is injective on admitted finite counting measures; and the outer Gaussian
is characteristic on their image. The bound generic theorem then gives strict
propriety.

For future caller-selected `2 <= R <= 128` conditionally i.i.d. draws
`X_1,...,X_R` and target `y`, the exact formal loss is

```text
1/[R(R-1)] sum_{r != s} k_configuration(X_r,X_s)
  - 2/R sum_r k_configuration(X_r,y).
```

Lower is better. The already-frozen paired orientation remains
`score_direct - score_guide`, so a positive value favors the guide. This package
does not select `R`; F109 stays open. It constructs canonical exact rational
combinations of nested exponential symbols and performs no binary64
exponential or numeric score comparison.

## 3. PhysioNet domain instance (`R3-PHYS`)

### 3.1 Documentation observations

The public page describes 12,000 ICU records, the first 48 hours after
admission, six general descriptors, and up to 37 time-series variables. It
states that timestamps are elapsed `HH:MM`, valid values are nonnegative, and
`-1` denotes missing or unknown. It also warns that simultaneous and multiple
measurements and outliers may occur. The exact observed time-series roster is:

| Parameter | Unit | Parameter | Unit |
|---|---|---|---|
| Albumin | g/dL | ALP | IU/L |
| ALT | IU/L | AST | IU/L |
| Bilirubin | mg/dL | BUN | mg/dL |
| Cholesterol | mg/dL | Creatinine | mg/dL |
| DiasABP | mmHg | FiO2 | fraction |
| GCS | score | Glucose | mg/dL |
| HCO3 | mmol/L | HCT | percent |
| HR | bpm | K | mEq/L |
| Lactate | mmol/L | Mg | mmol/L |
| MAP | mmHg | MechVent | binary |
| Na | mEq/L | NIDiasABP | mmHg |
| NIMAP | mmHg | NISysABP | mmHg |
| PaCO2 | mmHg | PaO2 | mmHg |
| pH | pH | Platelets | cells/nL |
| RespRate | bpm | SaO2 | percent |
| SysABP | mmHg | Temp | degC |
| TropI | ug/L | TropT | ug/L |
| Urine | mL | WBC | cells/nL |
| Weight | kg |  |  |

The six descriptors are `RecordID`, `Age`, `Gender`, `Height`, `ICUType`, and
admission `Weight`; later `Weight` rows retain their time-series role.

### 3.2 Exact event map

Let `j` be the index in the 37-name roster, `t` an integer elapsed minute in
the closed interval `[0,2880]`, and `v` either missing or a nonnegative exact
rational. Source plain-decimal tokens are decoded as exact rationals without a
decimal-to-binary64 round trip and are bounded to 256 ASCII bytes; excess is a
whole-domain no-go. Generated binary64 values, when supplied, are decoded to
their exact `as_integer_ratio` rational. The transform is in `R^112`:

```text
T_phys(t,j,v)
  = [ one_hot_37(j),
      t/2880,
      type_specific_present_mask_37(j,v),
      type_specific_value_37(j, v/(1+v)) ].
```

Missing `-1` maps to presence zero and value zero only in the active type slot;
present zero maps to presence one and value zero. This separates missing from
present zero, preserves type and time, and is injective on the admitted event
schema. Exact units remain metadata; no physiologic range or outlier exclusion
is invented.

### 3.3 Frozen task/resource semantics

- `Y` is the complete admitted occurrence-expanded multiset of time-series rows
  for one `RecordID` in the first 48 hours. Order is irrelevant, but
  multiplicity and simultaneous rows are preserved.
- `z` contains the custody/split identity and the static descriptors. Static
  descriptors are not generated events. Admission `Weight` is static; later
  `Weight` measurements are events.
- The horizon is exactly 2,880 elapsed minutes with event support `[0,2880]`.
- The agent-selected per-configuration cap is `131072 = 2^17` rows. It is a
  resource decision, not a source fact.
- Any cap excess, unknown parameter, invalid time, invalid value, malformed
  required row, collision, truncation requirement, or row/patient exclusion
  makes the whole PhysioNet domain `NO_GO`. There is no truncation, retry,
  resplit, top-up, imputation of required values, or row reassignment.

These values close F023, F024, and F026--F031. F025 and F032--F037 stay open:
no observation kernel, reference, support certificate, noise/clutter rule, or
admission statistic/threshold is supplied.

## 4. Online Retail II domain instance (`R4-RETAIL`)

### 4.1 Documentation observations

The UCI page describes 1,067,371 transaction rows from a UK-based non-store
retailer over 2009-12-01 through 2011-12-09 and lists eight fields:
`InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`,
`UnitPrice`, `CustomerID`, and `Country`. It describes `InvoiceNo` as six digits
with a leading `c` indicating cancellation, `StockCode` as nominal, signed
numeric quantity, unit price in sterling, a nominal customer identifier, and
country. The page reports missing values and labels the dataset CC BY 4.0. It
does not state a timezone.

The source documentation alone does not prove a raw snapshot, per-field raw
grammar, access record, governance approval, or privacy approval. Those remain
separate open receipts.

### 4.2 Exact token, time, and event maps

For a finite UTF-8 byte string `s`, define a length-prefixed base-256 integer
`C(s)` whose length-`n` code interval immediately precedes the length-`n+1`
interval, then define `J(s)=C(s)/(C(s)+1)`. UTF-8 and this length prefix make
`J` injective. Present source strings are not trimmed, case-folded, or Unicode
normalized. `StockCode` is required and bounded to 256 UTF-8 bytes;
`Description` is optional and bounded to 4,096; `Country` is optional and
bounded to 256. Missing and present-empty optional strings are distinct.

`InvoiceNo` is exactly six ASCII digits, or ASCII `c`/`C` followed by six
digits. The cancellation indicator is one exactly in the latter case, while
the raw invoice token is also retained. `CustomerID` context is the canonical
decimal rendering of a positive integer with one to five digits. Its F060
opaque customer key is exactly the lowercase hexadecimal encoding of those
ASCII bytes; one contiguous `row_ordinal` is retained per source row, including
all equal-time and duplicate rows.

Because the source page states no timezone, time is an exact Gregorian
**source-civil** seven-tuple `(year,month,day,hour,minute,second,microsecond)`.
Its carrier is exact source-civil microseconds since
`2009-12-01 00:00:00.000000`; it asserts no UTC instant, offset, locale,
daylight-saving rule, or timezone conversion. The half-open horizon is

```text
[2009-12-01 00:00:00.000000, 2011-12-10 00:00:00.000000)
= 739 days
= 63,849,600 seconds
= 63,849,600,000,000 microseconds.
```

For signed exact rational `q`, let `S(q)=q/(1+|q|)`. Quantity is an exact
integer; a source UnitPrice decimal is an exact rational with a 256-ASCII-byte
token bound; a generated binary64 price is its exact binary64 rational. The
transform is in `R^10`:

```text
T_retail(row)
  = [ J(InvoiceNo), cancellation,
      J(StockCode), Description_present, J(Description_or_empty),
      source_civil_microseconds / 63,849,600,000,000,
      S(Quantity), S(UnitPrice),
      Country_present, J(Country_or_empty) ].
```

The optional-string coordinates are zero when missing. Their presence masks
separate missing from present empty. `S` is injective, so decimal values are not
collapsed through binary64.

### 4.3 Frozen task/resource semantics

- `Y` is the complete admitted occurrence-expanded multiset of transaction
  line-item rows for one `CustomerID` over the frozen horizon.
- `z` contains the canonical customer key for custody, grouping, and splitting;
  it is not an event coordinate.
- All rows with the same customer are one configuration. Multiplicity,
  duplicate line items, multiple rows with one invoice, and simultaneous rows
  are preserved. No one-country-per-customer constraint is imposed.
- The conservative per-configuration cap is `1,067,371`, the documented whole
  dataset row count. Its use is conditional on the future exact snapshot
  agreeing with that source-level bound.
- Missing `Description` or `Country` is represented by its mask. Missing or
  malformed required `CustomerID`, `InvoiceNo`, `StockCode`, `Quantity`,
  `InvoiceDate`, or `UnitPrice`, cap excess, time outside the horizon, or any
  need for exclusion/truncation makes the whole Retail domain `NO_GO`. There is
  no retry, resplit, top-up, customer migration, row reassignment, or country
  coercion.

These values close F042, F043, and F045--F051. F044 and F052--F057 stay open:
no observation kernel, reference, support certificate, noise/clutter rule, or
admission statistic/threshold is supplied.

## 5. Additive F060 timestamp-semantic correction

The earlier F060 freeze used the carrier name
`timestamp_utc_microseconds` and asserted Unix-epoch UTC semantics. The public
UCI documentation supplies no timezone, so that claim cannot be retained.
Historical F060 files remain byte-stable. This package additively supersedes
only the timestamp carrier and rule identifier:

```text
rule_id = RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_SOURCE_CIVIL_F061_PARAMETERIZED_V2
normalized row keys =
  row_ordinal,
  customer_key_hex,
  timestamp_source_civil_microseconds_since_2009_12_01
timestamp domain = integer [0, 63,849,600,000,000)
```

The exhaustive ordered-gap search, complete-customer closed intervals,
lexicographic selection order, exact future F061 customer counts, windows
`train t<=T_g1`, `validation T_g1<t<=T_g2`, `test t>T_g2`, strict separation,
no-fallback rules, and terminal code
`NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR` are unchanged. The
correction has zero field-count delta: F060 remains closed to its successor
value and F061 remains open/null.

## 6. Exact field disposition

The candidate all-or-nothing closure roster is exactly 18 PRE fields:

```text
F023 F024 F026 F027 F028 F029 F030 F031
F042 F043 F045 F046 F047 F048 F049 F050 F051
F105
```

If independent review passes, PRE moves from 140 open / 26 closed to
122 open / 44 closed. POST remains 3 open / 3 closed. The total moves from
143 open / 29 closed to 125 open / 47 closed. The F060 successor correction
does not change those counts.

The exact Gate-A CKS checkbox remains open. The generic theorem requires the
selected formula to replace the preliminary manuscript display, production
integration/code matching, and an independent exact-instance audit before that
checkbox can close. This package supplies the exact instance and audit target,
but does not edit the locked manuscript display or claim production
integration. B02, B03, B04, and all other B01--B12 blockers remain open.
F025, F032--F041, F044, F052--F059, F061, and F109--F112 remain open. No Formal
Test, result slot, data admission, scientific run, or claim closes.

## 7. Pure implementation and qualification boundary

The bound source is
`src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py`. It imports
no project runtime, performs no I/O, network access, randomness, fitting,
training, exponential evaluation, or scientific computation. It enforces exact
built-in types, occurrence multiplicity, domain separation, caps, transforms,
and the `2 <= R <= 128` supported score-construction domain. Hostile tests cover
schema changes, missing/present separation, decimal-vs-binary64 distinction,
token injectivity, exact civil time, permutation/multiplicity, empty/count/event
channels, cross-domain refusal, cap refusal, score identity/orientation, package
tampering, re-signing, nonregular custody, and effectful import surfaces.

Passing these tests establishes exact source/package conformance only. It does
not validate a future raw parser, actual snapshot, model output, draw
independence, floating approximation, production resource use, or any empirical
metric value.

## 8. Publication and anti-drift boundary

This is internal project-control evidence. A publication-safe derivative must
remove internal paths, authority text, hashes, and custody details and undergo a
fresh anonymity, methods/statistics, license, governance, and claim-boundary
audit. Public documentation facts must be cited to their public sources; this
package is not a substitute for source or license records.

The candidate must be accepted or rejected all-or-nothing. Any material change
to a transform, roster, cap, horizon, score formula, parameter, field roster,
F060 correction, source, validator, test, or human document requires a new
content-addressed package and fresh independent review.
