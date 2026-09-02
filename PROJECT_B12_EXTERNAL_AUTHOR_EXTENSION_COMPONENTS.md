# B12 external author-extension components — offline candidate

**State:** `OFFLINE_AUTHOR_EXTENSION_COMPONENTS_IMPLEMENTED_PENDING_INDEPENDENT_REVIEW_RUNTIME_OPEN`  
**Claim scope:** `COMPONENT_IMPLEMENTATION_ONLY`  
**Exact predicates addressed:** four CSDI and four EditPP author-extension predicates  
**Upstream package execution, native-functionality claim, real data, entropy, training, inference, or production output:** none  
**Field, blocker, Formal-Test, result, timetable, tracker, or science delta:** zero

## 1. Outcome and boundary

`src/heterodiff/evaluation/b12_external_author_extension_components.py`
implements the deterministic local surfaces that were absent from the accepted
B12 two-domain adapter-stack package. The implementation covers exactly the
eight already-registered author-extension predicate identities:

1. `CSDI_AUTHOR_EXTENSION_1` —
   `LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS`;
2. `CSDI_AUTHOR_EXTENSION_2` —
   `VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER`;
3. `CSDI_AUTHOR_EXTENSION_3` —
   `EXACT_PHYSIONET_F105_EVENT_ADAPTER`;
4. `CSDI_AUTHOR_EXTENSION_4` —
   `FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE`;
5. `EDITPP_AUTHOR_EXTENSION_1` —
   `STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS`;
6. `EDITPP_AUTHOR_EXTENSION_2` —
   `SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL`;
7. `EDITPP_AUTHOR_EXTENSION_3` —
   `EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER`; and
8. `EDITPP_AUTHOR_EXTENSION_4` —
   `ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE`.

Each implementation record uses the exact original predicate ID, extension
ID, adapter identity, B06 domain, B06 configuration digest, accepted training
configuration digest, concrete entry point, and candidate source digest. Its
status is
`IMPLEMENTED_OFFLINE_PURE_COMPONENT_PENDING_INDEPENDENT_REVIEW`, and its claim
scope is exactly `COMPONENT_IMPLEMENTATION_ONLY`.

This successor resolves only the local component-absence facet. It does not
close the full original predicate because runtime qualification and production
evidence remain absent. In particular, it neither imports nor runs CSDI or
EditPP and never describes the extensions as upstream-native functionality.

## 2. Exact predecessor bindings

The implementation derives and validates the two external rows from the
accepted B06 registry:

| Adapter | Domain | B06 configuration SHA-256 | F139–F147 executable-configuration SHA-256 |
|---|---|---|---|
| `CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1` | `physionet-challenge-2012` | `72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046` | `e2c04e136c6799cbd4cc6dda82a6025881b912e70e8e51515f0eafd7af48b85b` |
| `EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1` | `online-retail-ii` | `64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee` | `21144dceee490dcb77d7b2aa49ed639daaca0fc13ff750b55e27ba9ffa3e7b5a` |

It also binds the complete accepted F139–F144/F147 plan semantics digest
`dd1c74d655f4cfeb4a895c11eb09a9e3ef41c328ce432ad782bce204e59585db`
and F144 checkpoint-selection semantics digest
`040db767c5bae9879ca5f006095dace2c43d4a2640af19839994465cff2011d2`.
Those bindings freeze the optimizer, learning-rate candidate roster,
precision, batch construction, completed-update bounds, validation rule,
checkpoint rule, and tuning limits. They are configuration constraints, not
evidence that any optimization or checkpoint operation occurred.

The accepted context implementation remains exactly 64-dimensional. The
candidate captures its class and function once at module initialization;
later rebinding a public predecessor-module alias cannot redirect a builder.

## 3. Occurrence-complete custody

Every adapter input is an already-materialized exact F105
`ExactConfiguration`. The candidate accepts exact concrete configuration,
event, tuple, integer, boolean, and `Fraction` types only. It validates the
frozen domain, canonical configuration order, exact event dimension, F105
coordinate structure, and the domain cap before constructing any record.

For every event occurrence, including repeated equal events, the occurrence
channel retains:

- a contiguous canonical serial;
- the exact F105 event;
- a digest of the full exact event payload; and
- a distinct occurrence digest binding the event digest, domain, and serial.

Two identical simultaneous rows therefore share an event digest but have
different occurrence digests. The channel exposes no truncation argument and
requires exact serials `0..n-1`. Within a parent adapter, removal, reordering,
expansion, cross-domain substitution, or digest mutation fails because the
channel must remain byte-consistent with the parent configuration and context.

The CSDI variable-cardinality decoder accepts the complete occurrence tuple
and returns an exact PhysioNet configuration. It supports zero, one, or more
events without a fixed-cardinality or padding parameter. It refuses a
noncanonical or incomplete serial roster and proves an exact round trip before
returning. The direct decoder intentionally treats any contiguous `0..n-1`
tuple as one complete standalone multiset; for example, a contiguous prefix is
a valid smaller standalone input. Substituting that prefix into an adapter
bound to a larger parent configuration still fails closed.

## 4. Exact F105 adapters

### 4.1 CSDI / PhysioNet

The CSDI author adapter enforces the accepted F105 `R^112` event structure:

- exactly one active member in the 37-coordinate type block;
- normalized elapsed time in `[0,1]`;
- a 37-coordinate type-specific binary presence block;
- a 37-coordinate type-specific transformed-value block;
- zero outside the active type;
- separation of missing from present zero; and
- a present transformed value in `[0,1)`.

It binds the complete occurrence channel and the accepted exact 64D context.
The adapter does not claim that native CSDI consumes `R^112`, retains
duplicates, or emits variable-cardinality F105 configurations. Those are
precisely the local author-extension functions implemented here.

### 4.2 EditPP / Retail

The EditPP author adapter enforces the accepted F105 `R^10` structure and
projects its ten exact transformed coordinates into named heads:

1. invoice token;
2. cancellation indicator;
3. stock token;
4. description presence;
5. description token;
6. source-civil time;
7. signed quantity;
8. signed unit price;
9. country presence; and
10. country token.

The heads bind their occurrence serial and exact event digest, and the parent
adapter additionally requires the ten head coordinates to equal the ten
coordinates of that exact occurrence event one by one. A self-consistent
redigested head using another valid event's coordinates is therefore refused.
The source-civil coordinate is kept as the F105 rational carrier; it is not
reinterpreted as UTC or another instant semantics. Optional-string presence
masks remain separate from token coordinates, and signed quantity/price
coordinates retain their exact F105 range.

The heads are explicitly
`EXACT_TRANSFORMED_F105_HEADS_NOT_INVERTED_RAW_SOURCE_TOKENS`. They do not claim
to recover raw invoice, stock, description, or country strings from the F105
coordinates. Raw parsing remains owned by the accepted F105 factory and future
real-data custody.

## 5. Frozen subset association and 64-draw surface

Both adapters expose an immutable conditioning-interface builder. A caller
supplies a strictly increasing exact tuple of occurrence serials. Empty, full,
or any arbitrary noncontiguous subset is supported. The builder creates:

- one boolean mask entry for every event occurrence;
- the ordered occurrence-digest roster for selected entries;
- a mask digest bound to the complete adapter;
- the exact accepted 64D context digest;
- the exact B06 and F139–F147 configuration digests;
- one immutable interface-subject digest; and
- exactly 64 draw slots with ordinals `0..63`.

Every draw slot has status
`AWAITING_EXTERNAL_MODEL_OUTPUT_NO_OUTPUT_MINTED` and contains no generated
configuration digest. The slots are deterministic interface positions, not
samples. No entropy, upstream call, synthetic result, or production receipt is
fabricated. Association is occurrence-specific: selecting the first versus
the second of two identical event rows produces different custody and mask
digests.

## 6. Fail-closed and nonclaim rules

The candidate refuses:

- wrong domains, dimensions, or exact types;
- malformed PhysioNet one-hot, presence, time, or value blocks;
- malformed Retail token, mask, source-civil, quantity, or price coordinates;
- cross-adapter conditioning;
- duplicate, unordered, negative, or out-of-range selected serials;
- non-64 draw rosters, reordered slots, populated slots, or widened statuses;
- zero, uppercase, short, or malformed candidate-source digests;
- mutation of a B06, training, context, event, occurrence, head, mask, slot,
  adapter, interface, or self-digest; and
- any implementation record claiming upstream-native behavior, upstream
  execution, domain-scale qualification, production evidence, or full closure.

The pure source imports no operating-system, filesystem, network, HTTP,
subprocess, random, secrets, numerical training, or upstream CSDI/EditPP
module. It reads no data and creates no external state.

## 7. Exact remaining boundary

Even after independent acceptance of this candidate, the following remain
open:

- execution of the pinned CSDI and EditPP packages;
- compatibility glue between these pure components and real upstream model
  input/output tensors or event processes;
- real dataset snapshots, parsing, admission, split, and custody receipts;
- actual F139–F147 tuning, training, validation, checkpoint, and selection;
- real conditional generation for every required method/domain/seed/case;
- domain-scale memory, time, no-truncation, and B08 resource qualification;
- authenticated runtime identity and production INTENT/OUTCOME receipts;
- independent scientific recomputation;
- the complete whole-method 22-row runtime roster;
- Formal Tests 28–30 execution and closure;
- B12 and all still-open blockers; and
- independent acceptance of the candidate package itself.

Accordingly, this package proposes no tracker or evidence-ledger edit and no
checkbox. If independently accepted, it is eligible only to replace
“implementation absent” with “offline component implemented” for the exact
eight predicate IDs listed in Section 1. Runtime and production facets remain
open under each identity.

## 8. Package and qualification

The candidate package is exactly:

1. this human record;
2. the pure implementation source;
3. the canonical machine record;
4. the read-only hash-first validator; and
5. the focused hostile test suite.

The validator opens one project-root directory descriptor with
`O_DIRECTORY|O_NOFOLLOW` and retains its exact device/inode/mode/link/size and
time identity across every package read. Each canonical relative path is
walked component by component from that descriptor: every parent is opened
with `O_DIRECTORY|O_NOFOLLOW`, and the leaf is opened with `O_NOFOLLOW`.
Parent directories must remain stable during the leaf read; leaves must remain
stable regular `0644`, single-link, bounded-size files. A copied capsule cannot
borrow exact bytes through a symlinked `src`, `research`, or other intermediate
directory.

The focused suite checks exact B06 and F139–F147 reconciliation, exact R112
and R10 structure, accepted 64D context binding, duplicate/multiplicity
custody, variable cardinality, structured heads, arbitrary subsets, exact
64-slot emptiness, cross-domain and cross-adapter refusal, mutation refusal,
alias-rebinding resistance, zero-delta semantics, forbidden imports, and F105
factory compatibility. Validator hostility covers copied-root replay, byte
tamper, leaf symlinks, intermediate-directory symlinks, and hard links.

Independent read-only review is required before any component-implementation
facet can be indexed as accepted evidence.
