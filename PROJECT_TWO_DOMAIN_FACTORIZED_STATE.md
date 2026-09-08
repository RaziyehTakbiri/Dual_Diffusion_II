# Factorized native state and reference — local proposal

## Outcome and status

The additive `two_domain_factorized_state.py` implementation represents legal
event metadata directly. It does not flatten patient-variable/time combinations,
Retail strings, dates, integer quantities, and mark branches into an enumerated
table of event-type IDs. An event has one immutable metadata key and either no
continuous coordinate or one log-magnitude coordinate.

This is executable local proposal code, not a change to the frozen F105 metric,
the existing 323-file runtime release, the accepted observation kernel, or an
admission of real data. No source rows, observed vocabularies, outcomes, training,
paid compute, or data downloads were used to choose this prior.

## Exact metadata and scalar fibers

`PhysioStateKey` retains the integer minute in `0..2880`, one of the frozen 37
parameter labels, and a value branch. Ordinary parameters have separate
`MISSING`, `ZERO`, and `POSITIVE` branches. Only `POSITIVE` has a coordinate:
`r = log(value)` with inverse `value = exp(r)`.

`GCS` and `MechVent` instead have `MISSING` and `ATOMIC(value)` branches, both
zero-dimensional. Every nonnegative exact rational value has an atomic prior
probability. They are not passed through a continuous Gaussian chart. This
choice preserves the broad *structural* rational input space of the frozen
metric: its schema labels GCS as a score and MechVent as binary, but explicitly
does not invent physiological-range/outlier exclusions. In particular, this
proposal does **not** assert that MechVent `3/2` or GCS `1/3` is clinically valid,
nor does it silently filter such a supplied record. A clinically restricted
support law would require an explicit separate choice and source-support audit.

`RetailStateKey` retains InvoiceNo, StockCode, optional Description, exact integer
Quantity, the seven-integer source-civil calendar, optional Country, and price
branch. Cancellation is derived from the exact InvoiceNo prefix, never sampled
independently. `ZERO` price is an atom. `NEGATIVE` and `POSITIVE` price use
`price = sign * exp(r)`. Missing and present-empty optional strings remain
different. Invoice `C` and `c`, Unicode normalization variants, and duplicate
event occurrences remain different where the frozen schema distinguishes them.

CustomerID, patient/record identity, and other static conditioning context are
supplied context, not fabricated event fields. No extra cross-row consistency
rules are inferred from an unseen dataset.

Every key exposes its dimension and an injective canonical metadata byte
encoding. Exact integers/rational numerator/denominator are encoded in hex, so
there is no decimal-string digit limit or integer-to-float conversion. The
canonical encoding is not a learned feature embedding. A neural compression of
these bytes, if supplied separately, must not be advertised as injective.

## Concrete normalized reference proposal

The following **pre-outcome defaults are proposed**, not scientifically adopted
or estimated from the source data. Their virtue here is explicit normalization,
full metadata support, and direct sampling without rejecting a malformed record.
They are not evidence of statistical adequacy.

### Finite ordinals

For `n` choices in their declared canonical order, let `k=ceil(log2(n))` and
`r=2^k-n`. Draw exactly `k` ideal fair bits as the integer `w`, and use `w mod n`.
Choice `i` has probability `2/2^k` if `i<r`, otherwise `1/2^k`.

This is an intentionally disclosed dyadic bias, **not a uniform distribution**.
It gives every choice positive probability and requires no modulo-rejection
loop. It is used for the 37 parameter labels, 2,881 Physio minute atoms,
1,000,000 six-digit invoice bodies, and 63,849,600,000,000 Retail source-civil
microsecond atoms in `[2009-12-01, 2011-12-10)`.

The invoice prefix has probabilities `none=1/2`, `C=1/4`, `c=1/4`; the six-digit
body retains leading zeroes. No invoice vocabulary is learned.

### UTF-8 factor grammar

StockCode is required, nonempty, and at most 256 UTF-8 bytes. Description is
optional and at most 4,096 bytes; Country is optional and at most 256 bytes.
Optional fields first choose missing/present with equal probability. A present
optional string may be empty.

At each non-forced position with remaining byte budget, stop with probability
`1/2`; otherwise append one valid Unicode scalar. StockCode forces its first
scalar. At exactly zero remaining bytes, stopping is forced. With at least four
bytes left, scalar widths 1, 2, 3, 4 have probabilities `1/2,1/4,1/8,1/8`.
With three bytes left they have `1/2,1/4,1/4`; with two bytes, `1/2,1/2`; with one
byte, width 1 is forced.

Within a width, choose a scalar by the finite ordinal rule. The scalar counts
are respectively `128, 1920, 61440, 1048576`. The three-byte mapping skips the
surrogate interval; the four-byte mapping ends at U+10FFFF. Every legal string
within the frozen byte bound has positive probability, with no UTF-8 rejection
or vocabulary table. This is a distribution on strings constructed directly,
not random arbitrary bytes later repaired into text.

The frozen ordinary text fields do not impose Unicode normalization, trimming,
or a control-character filter. This grammar therefore retains those distinctions
instead of inventing such restrictions. InvoiceNo has its separate stricter
ASCII grammar. Finite string bounds guarantee termination; exact probabilities
are products of continue/stop, width, and scalar factors.

### Unbounded integer Quantity

First choose magnitude zero with probability `1/2`. Otherwise choose positive
bit length `L` with `P(L=l)=(3/4)(1/4)^(l-1)`, draw its remaining `l-1` bits
uniformly, and choose sign by an independent fair bit. Thus `P(0)=1/2` and
`P(q)=3/2^(3l+1)` for a nonzero integer of bit length `l`.

This law is normalized on all integers and has a finite first absolute moment.
It does not use a finite Quantity range, exponentiate its absolute integer
value, or infer a source-data maximum. The number of entropy bits is unbounded
in principle. A finite execution budget can refuse; it must not redraw and
claim the ideal unconditional law.

### Atomic nonnegative rational prior

Each nonnegative rational has its unique finite regular continued fraction
`[a0; a1,...,aL]`, with `a0>=0`, internal tail terms at least 1, and the final
tail term at least 2. Integers have an empty tail. First sample `a0` using the
nonnegative magnitude law above: mass `1/2` at zero, and `3/2^(3l)` at each
positive integer of bit length `l`.

Choose an integer (empty tail) with probability `1/2`. Otherwise choose tail
length `L>=1` with `P(L=l)=2^-l`, sample each internal term as `1+A`, and its
last term as `2+A`, with independent `A` from the same nonnegative integer law.
This is normalized because the continued-fraction representation is unique and
each independent factor is normalized. Every nonnegative rational gets positive
mass, with no alternate-expansion double counting. There is no restriction to
`{0,1}` or a guessed GCS roster.

For GCS and MechVent, missing has mass `1/2` and present-atomic has mass `1/2`
times this rational prior. For ordinary Physio variables, missing/zero/positive
have probabilities `1/4,1/4,1/2`. Retail zero/negative/positive prices have
probabilities `1/2,1/4,1/4`. A one-dimensional fiber has an independent standard
normal reference in log magnitude; a zero-dimensional atom has no Gaussian
coordinate or coordinate-density factor.

### Exact mass, numerical log density, and resource refusal

`reference.mass(key)` returns a compact exact dyadic numerator and denominator
exponent. `reference.log_prob(key)` returns its logarithm without converting the
joint mass to binary64 and without any probability floor. Very long valid
metadata can have probability far below the smallest positive binary64; the
exact representation stays positive. `event_log_density` additionally includes
the standard-normal log density when the key has dimension one.

The implementation accepts an explicitly supplied `random.Random`, PCG64, or
PCG64DXSM generator. It does not silently assume that every NumPy generator
returns a 64-bit random word. The ideal prior is defined by unlimited independent
bits and ideal Gaussian draws; finite-state pseudorandom implementations do not
prove that ideal full-support law. Logical metadata-bit, integer-size, and
continued-fraction-length limits cause an explicit error. The Gaussian library's
internal entropy consumption is not part of the metadata-bit counter.

No failed draw is replaced, truncated, or retried as a successful shorter draw.
Conditioning on execution success, including representability/resource success,
can change a distribution; unchanged-law equivalence is not claimed. Exact
fraction materialization also has an explicit memory bound; the compact mass
and log interface do not impose a joint-probability cutoff.

## What the conversion interface proves — and does not

### Optional TRAIN-informed reference family

`TrainInformedMetadataReference(universal, train_occurrences, beta=Fraction(...))`
adds the explicitly supplied family
`rho_beta = (1-beta) * rho_train + beta * rho_universal`, with exact rational
`0 < beta < 1`. `rho_train` is the complete-key occurrence-frequency law from
the nonempty supplied tuple, retaining multiplicities. It is not a per-field
independence fit or an observed-only vocabulary. Every otherwise unseen legal
key keeps exactly `beta * rho_universal(key)` mass. Thus normalization and full
metadata support follow directly from the normalized component laws.

The supplied tuple is *labelled TRAIN by its caller*. This primitive does not
prove split identity, original-source admission, provenance, or absence of
held-out leakage. It must not be populated from validation/test records. It
retains only immutable complete keys; the continuous coordinates of supplied
occurrences are not fitted or recycled. A sampled one-dimensional fiber still
uses an independent standard normal, including on the empirical-key branch.

Exact masses remain a compact two-term expression, and log probabilities use
a stable two-term log sum. Rational beta is never first converted to a float:
a positive beta smaller than binary64's range still retains a positive exact
universal component. Sampling uses successive ideal-bit interval decisions for
the rational mixture choice and the uniform occurrence index. The latter is
genuinely uniform even when the roster length is not a power of two; it does
not reuse the deliberately biased finite-ordinal rule of the universal prior.
These variable-bit decisions share one explicit metadata entropy budget, and
refuse on exhaustion without redraw or a conditioned-law claim. Materializing
the exact combined fraction has a conservative denominator-memory bound.

This family can raise probability for complete keys already seen in TRAIN.
It does not solve tiny mass for a held-out unseen *complete* key: such a key
still receives only the beta-weighted universal mass. Neither beta nor this
optional family is scientifically adopted merely by providing executable code.

### Semantic and floating conversion scope

`encode_semantic_event` and `encode_metric_event` preserve every discrete field.
Atoms retain exact rational values. Scalar fibers default to requiring exact
conversion of a supplied rational to binary64. The explicit alternative policy
`ROUND_TO_BINARY64_WITH_EXACT_ERROR_RECORD` records the exact conversion error;
both policies record the separate floating log/exp roundtrip error. Neither
policy promises a bitwise analytic-chart roundtrip.

Overflow/underflow of a numerical exp/log conversion refuses without clipping.
The semantic inverse does not prove origin from the frozen bounded decimal
token parser or finite-binary64 generated constructor. Ideal continuous fibers
have topological support on their open magnitude intervals, not positive point
mass at every raw decimal observation. Merely adding this chart does not turn
raw atomic measurements into a density or solve a clean-hold singularity. A
source-measure lift or an explicitly different target law would be a scientific
change requiring its own account.

## Remaining integration and scientific choices

- A factorized configuration-count reference and balanced birth/death/metadata
  replacement implementation must consume these keys directly; this module
  does not claim compatibility with the old finite type-table process.
- A shared neural architecture must consume exact metadata and variable 0/1D
  fibers, with its own prospective parameter-count/fairness account. The old
  112/10-dimensional F105 embedding is still a metric injection, not an onto
  Gaussian generative chart.
- The accepted real-domain observation kernel remains occurrence-independent
  half-thinning with exact identity emissions. This module neither changes it
  nor establishes a common dominating observation measure. Any replacement or
  source-measure lift changes the scientific specification and must be explicit.
- Full support alone does not imply a useful prior: long strings or large
  metadata may have tiny mass, and bounded energy corrections may not overcome
  a poorly matched reference. No accuracy, adequacy, or compute-readiness claim
  follows from the tests below.

## Local qualification

The focused tests exercise all 37 missing-value types, atomic rational GCS and
MechVent values, signed scalar conversion, exact metadata distinctions, illegal
input refusal, dyadic/bit-length/continued-fraction arithmetic, UTF-8 boundary
scalars, tiny exact joint masses, replay, and explicit resource refusal. These
are supplied synthetic structural tests, not clinical validation, real-data
admission, scientific training, or GPU qualification.

The separate `test_factorized_scientific_amendment_integration.py` uses invented
complete keys from both domains with both universal and TRAIN-informed priors.
It joins those keys to the bounded smooth oracle's target lift and observation
smoothing, verifies exact F105 discrete-field preservation, and evaluates and
differentiates the shared CPU energy graph. The ordinary scalar alone changes;
GCS/MechVent and zero atoms keep no coordinate and remain exact. The test also
exercises log likelihoods larger than 1,000 without exponentiating them. This
is not a full training-loss or hybrid-trajectory integration, an analytic-guide
gradient implementation, or a production run.
