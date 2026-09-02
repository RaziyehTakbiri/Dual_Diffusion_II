# Independent review: B12 exact two-domain adapter-stack successor

**Review date:** 2026-09-01  
**Decision:** `GO_B12_ADAPTER_STACK_COMPONENT_INDEXING_ONLY`  
**Findings:** P0 = 0; P1 = 0; P2 = 0  
**Boundary:** independent local exact-byte engineering review only; no network,
data, entropy, training, inference, upstream-package execution, domain-scale
runtime, scientific, Formal-Test, field, blocker, result, or timetable-task
acceptance

This review accepts the exact successor bytes below as truthful synthetic
interface component evidence. It does not reinterpret the accepted B12 v2
partial-contract bytes, close a B12 residual, or make the synthetic local
receipt principal an independent scientific or operational authenticator.

## Exact reviewed bytes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK.md` | 8,866 | `900eb147602eb7d74e1a54e69d9d684cf8a1e8fc433c030cad4d50a2a2937b49` |
| `src/heterodiff/evaluation/b12_two_domain_adapter_stack.py` | 34,660 | `44ece6452c8edfaadc7d6013a37208fb8648d3a6dbb3ce29bcecd97a90880a57` |
| `research/fixtures/manuscript_v3_b12_two_domain_adapter_stack_v1.json` | 9,956 | `ba65fe357caca90f64e89bac9d9c78fbbe379342fcf7f6321aceb4caf4f7b502` |
| `research/diagnostics/manuscript_v3_b12_two_domain_adapter_stack_v1.py` | 13,962 | `a5a32d69dcdaf940a33990fb26b1a9150cb3c12eb7e46584d1c40aef51f5b94b` |
| `tests/unit/test_b12_two_domain_adapter_stack.py` | 13,259 | `268ba5bf9e4ff57e1df1108aceb4106a957df7a541a6f1de43f2b6ff2f197d64` |

All five were reopened through stable no-follow descriptors and were regular
`0644` single-link files with terminal LF. Any byte change invalidates this
review. The machine record was independently confirmed as duplicate-key-free,
ASCII, canonical JSON with one terminal LF. Its semantic self-digest is
`b92b5e9a09dd618eaee0ea147ec9277a214a2cff133ee0038a34099f753afb36`;
its raw-file SHA-256 is the machine binding above.

The review also reopened the exact predecessor bytes pinned by the validator:

| Predecessor artifact | Bytes | SHA-256 |
|---|---:|---|
| `src/heterodiff/experiments/two_domain_baseline_registry.py` | 47,098 | `d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1` |
| `research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json` | 186,707 | `b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21` |
| `src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py` | 25,342 | `567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881` |
| `src/heterodiff/evaluation/b12_integrated_offline_candidate.py` | 14,944 | `b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd` |
| `research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json` | 8,755 | `825cfde8412474eba97dea4a4d2fb92fa8af99568ebeada05f6b33b71fcc680c` |
| `PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE_INDEPENDENT_REVIEW.md` | 4,988 | `90e7d4f9f4f70bcd4a6da599c532a944629101d3d5b245f7b05ece01cb463a46` |

## Verification results

- Standalone hash-first validator from the project root: PASS, record
  `b92b5e9a09dd618eaee0ea147ec9277a214a2cff133ee0038a34099f753afb36`.
- The same validator invoked by absolute path from `/private/tmp`: PASS with
  the identical record. This confirms that validation does not depend on the
  caller's working directory.
- Focused successor suite: 16/16 passed.
- Relevant B06 registry/freeze, F105 exact-instance/production, and accepted
  B12 v2 predecessor regressions: 187/187 passed.
- Independent roster, projection, source-binding, output-binding, receipt, and
  extension replay: PASS for both domain contexts, all 22 rows, and all eight
  open obligations.
- Hostile exact-type, subclass, false-closure, public-alias-rebinding,
  malformed-source-hash, cross-domain, mutation, and duplicate-removal paths:
  PASS fail-closed.
- Static import review found no filesystem, network, subprocess, entropy,
  training-framework, or array-framework surface in the successor module.

## Independently derived B06 reconciliation

The review constructed the roster directly from the pinned
`FROZEN_REGISTRY`, using the two primary configurations, four control
configurations, four domain-specific literature-family implementations, and
the two external configurations. It did not use the successor's roster builder
for this derivation.

The result is exactly 22 unique identity/domain/configuration rows: four
primary, eight control, eight literature-family, one CSDI/PhysioNet, and one
EditPP/Retail. Its independently serialized raw roster SHA-256 is
`adff7b63088bb9f08bc107debc03f9ca2c9c9747b34fc8ece1bcf6fdef2c70ec`.

Identity and domain order match the accepted B12 v2 partial roster. Fourteen
configuration hashes also match. The only differences are the eight
literature-family hashes at zero-based ordinals 12 through 19, inclusive.
Each corrected value exactly equals the corresponding B06
`implementation_by_domain[*].config_sha256`; the set of eight historical
hashes and the set of eight corrected hashes are disjoint.

The accepted B12 v2 runner snapshot still contains the historical eight
hashes. This successor correctly leaves those accepted bytes untouched, so a
future integrated B12 successor must adopt the corrected snapshot before these
22 receipts can participate in one coherent runner bundle. This review accepts
the correction as component evidence; it does not claim that integration has
already occurred.

## Context, occurrence, type, and source boundaries

The review independently reproduced the complete configuration payloads, all
ordered occurrence digests, the ordinal-separated SHA-512 accumulation, all
64 exact `Fraction` coordinates, both configuration digests, and both context
self-digests. Retail remains exactly R10 and PhysioNet exactly R112. Removing
one repeated tied occurrence changes the event count, ordered occurrence
roster, complete configuration digest, and context digest. The public encoder
has one configuration parameter and no truncation option.

Manifest construction accepts only exact concrete F105 configuration/event
types, enforces domain, dimension, canonical order, and the pinned F105 caps,
and builds its context internally. Every reviewed row separately carries its
B06 configuration hash and a nonzero unique source binding derived from the
actual reviewed module SHA-256, row identity, domain, configuration, and exact
entry point. Independent recomputation matched all 22 implementation/source
bindings, output hashes, predicate subjects, evidence hashes, and receipt
hashes.

The source digest remains an exact nonzero caller-supplied input to the general
API; the bound fixture is trustworthy only because the validator supplies and
checks the actual captured-source hash first. This is not production source
attestation and is not treated as one here.

The CSDI and EditPP interfaces expose four obligations each. All eight retain
`OPEN_IMPLEMENTATION_AND_RUNTIME_EVIDENCE_ABSENT`, reject a closed status,
reject upstream-execution claims, and reject domain-scale-qualification claims.
The generated adapter receipts therefore qualify only the deterministic local
synthetic interface. They do not establish the upstream algorithms or their
author extensions.

## Acceptance, effects, and residuals

The exact reviewed bytes are eligible for component-evidence indexing with
zero field, blocker, Formal-Test, result, science, authority, and timetable
delta. The timetable and evidence ledger were not edited by this review. No
checkbox is eligible to be marked from this package alone, and B12 remains
open.

The following remain explicit residuals:

- integration of the corrected 22-row snapshot into a reviewed successor to
  the accepted B12 runner contract;
- loaded or trained primary/control checkpoints and their real adapter
  implementations;
- executable clean-room literature-family algorithms and scientific
  qualification;
- CSDI and EditPP upstream-package execution and all four-plus-four author
  extensions;
- real data adapters, immutable snapshots, splits, escrow, licenses, privacy,
  and external acceptances;
- domain-scale no-truncation resource qualification for the frozen caps;
- B08 production hardware, environment, ceilings, allocation, durability,
  and capacity evidence;
- real paired immutable INTENT/OUTCOME ledgers, independent real
  recomputation, and production runner/capsule bindings;
- Formal Tests 28--30 production receipts and residual closures; and
- final independent integrated B12 acceptance and B12 closure.

