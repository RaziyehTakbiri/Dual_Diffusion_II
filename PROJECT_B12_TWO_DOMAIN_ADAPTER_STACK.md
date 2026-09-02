# B12 exact two-domain adapter stack — corrected B06 successor candidate

**State:** `SYNTHETIC_INTERFACE_IMPLEMENTED_RUNTIME_AND_ALGORITHM_RESIDUALS_OPEN`  
**Context dimension:** exactly `64`  
**Adapter-interface roster:** exactly `22` rows  
**Author-extension obligations:** exactly `8`, all open  
**Network, data, entropy, training, inference, or domain-scale execution:** none  
**Field, blocker, Formal-Test, result, or timetable delta:** zero

## 1. Implemented boundary

`src/heterodiff/evaluation/b12_two_domain_adapter_stack.py` implements one
deterministic, exact-type adapter interface over already-materialized F105
configurations. It exports:

- `PRIMARY_CONTEXT_DIMENSION = 64`;
- `ADAPTER_ROSTER_SNAPSHOT`;
- `AUTHOR_EXTENSION_OBLIGATIONS`;
- `ExactContextEncoding`;
- `AdapterConformanceRecord`;
- `encode_exact_context`;
- `build_synthetic_conformance_manifest`;
- `build_synthetic_adapter_receipts`; and
- `qualification_fixture_configurations`.

The manifest and receipt builders always return the exact 22 rows in the
corrected B06 identity/domain order. Every row binds separately:

1. the B06 adapter identity;
2. the B06 domain identity;
3. the exact B06 configuration SHA-256;
4. the raw adapter-module source SHA-256 supplied by the caller;
5. a nonzero row-specific implementation/source binding derived from that raw
   source, row identity, domain, configuration, and entry point;
6. the complete exact input-configuration digest;
7. the synthetic-interface output digest;
8. the exact coordinate dimension and event count; and
9. a typed `AdapterReceipt` from the accepted B12 receipt vocabulary.

The receipts truthfully identify their qualifier as
`LOCAL_SYNTHETIC_INTERFACE_QUALIFIER_NOT_INDEPENDENT` and their method as
`DETERMINISTIC_LOCAL_SYNTHETIC_INTERFACE_QUALIFICATION_NOT_INDEPENDENT_V1`.
They qualify only the deterministic interface. They do not authenticate an
independent reviewer or discharge a B12 residual predicate.

## 2. Material correction to the zero-delta B12 v2 partial contract

The previously accepted B12 v2 contract was indexing-only and closed no field,
blocker, Formal Test, or timetable task. Its eight literature-family row hashes
do not match B06's exact domain-specific implementation configuration digests in
`FROZEN_REGISTRY["literature_families"][*]["implementation_by_domain"]`. This
audit does not establish the provenance of those eight historical hashes.
This successor does not alter those accepted historical bytes. It derives the
new roster directly from B06 and proves that the only differences are exact
ordinals 12 through 19:

| Ordinal | Family | Domain | Historical v2 digest | Correct B06 implementation digest |
|---:|---|---|---|---|
| 12 | NGDB-style | Retail | `e5f37459809ad912af07daf42c7652968ab6ea7f54e936109752243a4357065a` | `680bd6c50aa481c0232a00dfe65cac9949432e07e79bb245c01cd7355b0434bd` |
| 13 | NGDB-style | PhysioNet | `1de711005c3c22de646dc870b4c6ac54c5a139fffd797a403072300bccfdfb52` | `4148c1e6f03781155eddc5ebe8446dbefce7c2de580a7914efc8b0a3ddca7586` |
| 14 | DEFT-style | Retail | `fc2c415774ed73dd9ecadf69fa1d3add984779c4f6075aea75b8c529df581ef0` | `96550380cdd9161cb64b8d727fd2896c3dde7e0c40869c52457e3f654bc7b683` |
| 15 | DEFT-style | PhysioNet | `2d41a2d142260f00a10847844fcd49ed50759aaad990fb715d8de979e8c03b21` | `1d485e0372b70c3e020d2af464b782d20dc8c050d919eece0ab8260fbacb2300` |
| 16 | same-base SMC/Feynman–Kac | Retail | `330de95230e6452d1fba9865e4ac4b991967f0e722b63ebb387fe59e2d5f2a60` | `94b3bad18048f96a1b99f03012c116da3e550df06548a00d6cecf17c4367dad6` |
| 17 | same-base SMC/Feynman–Kac | PhysioNet | `8041429a94237b549961a01fe8e4e965bfff648951e0f4b6904a0e7ac9449366` | `57bbcb95f58b55d1154470d829daccd966d8ecc1b11a0c9368aec7af309a93c6` |
| 18 | point/edit generator | Retail | `b04ae2fdc700e2b3677854b39f246f0188cf58f03adc11305e1258c04f14786b` | `38e51c2df150939cb375877b30f0c049f8c2ad1cabf6c69996e6961e2515eeca` |
| 19 | point/edit generator | PhysioNet | `192f069c927c3c6dc6356286f12e0a0c68d20b120651a1a72793a6eba59a5cca` | `a5d626a0e9f25d203cacf5790a9396185e8849a5d9f58fdae61521298394e2a8` |

The other 14 identity/domain/configuration rows match the historical partial
roster. No historical review is reinterpreted as acceptance of this successor.

## 3. Exact 22-row construction

The corrected roster is:

- two primary identities over Retail and PhysioNet: four rows;
- four control identities over both domains: eight rows;
- four literature-family identities over both domains, using the exact
  domain-specific implementation hashes: eight rows;
- CSDI over PhysioNet: one row; and
- EditPP over Retail: one row.

The implementation snapshot is private and immutable for internal validation;
rebinding the public roster alias or the earlier B12 public alias cannot change
a built manifest. Every record validates its exact ordinal, identity, domain,
configuration digest, class, source binding, input/output digests, coordinate
dimension, typed receipt, and self-digest.

## 4. Exact context and event semantics

The encoder accepts only exact `ExactConfiguration` and `ExactEvent` concrete
types. Retail events must have exactly ten exact `Fraction` coordinates;
PhysioNet events must have exactly 112. Cross-domain events and configurations,
wrong dimensions, noncanonical order, non-Fraction coordinates, over-cap
configurations, subclasses, and duck objects fail before a receipt is built.

The 64-coordinate projection is an exact deterministic qualification
interface. It makes no injectivity or learned-representation claim. Its custody
payload additionally contains:

- the digest of the complete canonical configuration;
- the exact event count; and
- one ordered digest per event occurrence.

Repeated identical events therefore remain repeated in the occurrence roster.
The API exposes no truncation argument, iterates every accepted occurrence,
and produces a different input and context digest if one duplicate/tied
occurrence is removed.

The configured F105 caps remain 1,067,371 Retail events and 131,072 PhysioNet
events. This package validates those limits but does not claim domain-scale
memory, time, streaming, or capacity qualification.

## 5. Separate author-extension interfaces

The following exact obligations are exported, validated, and deliberately
left `OPEN_IMPLEMENTATION_AND_RUNTIME_EVIDENCE_ABSENT`:

### CSDI / PhysioNet

1. `LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS`;
2. `VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER`;
3. `EXACT_PHYSIONET_F105_EVENT_ADAPTER`; and
4. `FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE`.

### EditPP / Retail

1. `STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS`;
2. `SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL`;
3. `EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER`; and
4. `ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE`.

Their interfaces reject false closure, upstream-execution, and domain-scale
qualification claims. No placeholder output is represented as an author
extension implementation.

## 6. Honest residual boundary

This package supplies executable deterministic interface qualification, not a
scientific algorithm stack. The following remain absent:

- loaded or trained primary/control checkpoints;
- executable clean-room literature algorithms and their scientific
  qualification;
- CSDI or EditPP package execution;
- every one of the eight author extensions above;
- real data adapters, snapshots, splits, or escrow;
- domain-scale execution and no-truncation resource qualification;
- B08 hardware, environment, ceiling, allocation, durability, or capacity
  receipts;
- real INTENT/OUTCOME execution ledgers;
- independent real recomputation;
- Formal Tests 28–30 production receipts; and
- independent acceptance of these successor bytes.

Accordingly, the 22 typed adapter receipts produced here are not eligible to
close B12, an adapter residual, a Formal Test, a field, or a timetable task.

## 7. Qualification

The focused suite contains 16 tests covering:

- direct reconciliation of all 22 rows to B06;
- exact rejection of all eight stale literature hashes;
- 64-dimensional determinism;
- Retail R10 and PhysioNet R112 enforcement;
- exact concrete types and cross-domain refusal;
- multiplicity, tied duplicates, and no-truncation custody;
- exact roster order and unique row-specific source bindings;
- individual validation of all 22 typed receipts;
- config/source/output/record and receipt mutation refusal;
- zero, uppercase, malformed, and short source-hash refusal;
- public-alias mutation resistance;
- exact eight-item open author-extension roster; and
- absence of I/O, entropy, network, training-framework, or subprocess imports.

Independent read-only review is required before this package can be indexed as
accepted component evidence.
