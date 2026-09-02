# B02/B03 joint offline precontact activation preflight

**Date:** 2026-09-01  
**Schema:** `heterodiff-b02-b03-offline-precontact-activation-v1`  
**State:** `OFFLINE_ACTIVATION_PREFLIGHT_COMPLETE_AWAITING_HUMAN_OWNER_ROSTER`  
**B02:** open  
**B03:** open  
**External contact or data access:** none

## 1. Outcome

This package completes the next safe implementation step for the two real-domain
blockers. It turns the earlier static protocol design into executable,
fail-closed offline controls:

1. a shared four-operation precontact state machine;
2. a PhysioNet snapshot, patient-split, support, leakage, and admission
   preflight;
3. a source-civil Online Retail II customer-temporal split and admission
   preflight; and
4. hostile tests showing that unresolved authority, ownership, support, power,
   snapshot, or receipt facts cannot be converted into an operational GO.

The package does not contact either registered source, browse documentation,
authenticate, download, open or parse a real dataset, create an institutional
determination, activate escrow, train a model, inspect held-out data, or create
a scientific result. All source-derived observations remain strict nulls.

The bounded offline preflight is complete. The exact finite operational
precontact instance is not populated or admitted because concrete accountable
owners, custodians, approval targets, accepted key/ACL controls, and the F061
allocation decision remain absent. Consequently the seven operational
Solo-Block-2 timetable boxes remain open.

## 2. Authority boundary

The visible instruction is exactly:

> Okay, let's move forward then.

Its UTF-8 SHA-256 is
`706de12ea5e317649aa6550fa4c7c53a4b0a19b369a3fe032d80f38f76872138`.
It supports continued bounded offline construction and review. It is not a
row-bound source-contact authorization and cannot prospectively bind the
content hash of a package that did not yet exist when the instruction was
given. It also cannot create an accountable institutional, privacy, ethics,
license, security, or escrow-owner decision.

The accepted prospective seal and static protocol therefore retain their
ordering:

`offline package -> independent GO -> exact owner/approval roster -> exact
fresh ADMIN authority -> durable intent -> ADMIN outcome -> approvals ->
reviewed DATA instance -> exact fresh DATA authority -> durable intent ->
acquisition -> snapshot/split/escrow`.

Prior V2 authority was limited to one exact PhysioNet root-page attempt and is
terminal no-retry. V4 and V5 are dormant offline definitions with zero usable
operational budget. None transfers authority to this package.

## 3. Exact package

The canonical machine record binds the current bytes of:

- `PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md`;
- `src/heterodiff/data/two_domain_offline_precontact_activation.py`;
- `tests/unit/test_two_domain_offline_precontact_activation.py`;
- `src/heterodiff/data/physionet_2012_admission_preflight.py`;
- `tests/unit/test_physionet_2012_admission_preflight.py`;
- `src/heterodiff/data/online_retail_ii_admission_preflight.py`; and
- `tests/unit/test_online_retail_ii_admission_preflight.py`.

The machine record is
`research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json`.
Its read-only validator and hostile tests are respectively:

- `research/diagnostics/manuscript_v3_b02_b03_offline_precontact_activation_v1.py`;
- `tests/unit/test_manuscript_v3_b02_b03_offline_precontact_activation_v1.py`.

Those two qualification files are outside semantic self-binding to avoid a
hash cycle. The independent review binds their final bytes separately.

## 4. Shared activation core

The shared core admits exactly four contiguous roster rows:

| Row | Domain | Phase | Exact target | Current eligibility |
|---:|---|---|---|---|
| 0 | PhysioNet Challenge 2012 | ADMIN | `https://physionet.org/content/challenge-2012/1.0.0/` | ineligible; zero budget |
| 1 | Online Retail II | ADMIN | `https://archive.ics.uci.edu/dataset/502/online+retail+ii` | ineligible; zero budget |
| 2 | PhysioNet Challenge 2012 | DATA | future immutable locator from exact row-0 success | dormant/ineligible |
| 3 | Online Retail II | DATA | future immutable locator from exact row-1 success | dormant/ineligible |

Every row has maximum attempts one, retries zero, redirects zero, fallbacks
zero, and current execution budget zero. ADMIN rows are administrative metadata
questions only and expressly prohibit credentials, authentication, download,
protected data, and outcomes. DATA rows cannot become eligible unless all of
the following exist for the same domain and exact package lineage:

- exact ADMIN success;
- every required approval receipt;
- an independently reviewed data-access instance;
- fresh exact data-access authority; and
- a durable no-clobber intent receipt.

The exact seven-question ADMIN roster is identical for rows 0 and 1:

1. canonical dataset identifier and current immutable version or revision;
2. exactly one immutable archive locator, SHA-256, and byte count;
3. exact terms for access, storage, analysis, publication, redistribution, and
   retention;
4. account, authentication, and data-use-agreement requirements;
5. governance, ethics, privacy, clinical, and institutional approvals;
6. storage, deletion, retention, disclosure, and publication controls; and
7. schema and timezone metadata needed to evaluate the frozen selector and
   split rules deterministically.

The DATA exact-target slots remain strict null in the offline state. Their
deterministic derivation fields point only to a future matching ADMIN success;
the symbolic derivation is not treated as an observed locator.

The shared F061 seam is an activation-specific allocation-policy codec. It
permits only positive TRAIN/VALIDATION/TEST proportions, positive minimums,
Hamilton allocation with the frozen tie order, and an explicit power
requirement. It is not itself a Retail proposal, a PhysioNet proposal, or an
exact domain allocation. Its policy digest uses a separate schema and
domain-separation tag from both domain-native codecs.

Two content-addressed deterministic adapters preserve that boundary. The
Retail adapter projects an accepted shared policy into Retail's native
proposal roster. The PhysioNet adapter can do so only after the immutable
snapshot's patient count is observed; it Hamilton-resolves the patient counts
and creates a native proposal that still requires a separate later PhysioNet
external review of those exact counts. The adapters never reuse a shared-policy
digest as a domain proposal or definition digest. The actual policy,
proportions, minimums, power requirement, accepted policy review, domain-native
proposals, exact PhysioNet counts, later PhysioNet review, and final definition
digests all remain strict null in the default state.

The forward-only state machine preserves all thirteen stages frozen by the
static design. Skipped stages, ambiguous or mutable targets, unknown outcomes,
non-null pre-execution observations, budget smuggling, retry/fallback claims,
or DATA activation without the complete dependency chain are hard failures.

The unresolved-owner manifest is closed-world and includes:

1. accountable governance owner;
2. license/privacy or institutional approval endpoint;
3. raw snapshot custodian;
4. deterministic split operator;
5. independent held-out escrow custodian;
6. final-opening approver;
7. key and ACL acceptance authority;
8. retention/deletion owner; and
9. incident-response owner.

Role labels are not identities. The offline preflight remains on `HOLD` while
any identity, acceptance receipt, or conflict-of-interest determination is
null. Even a complete structural population can reach only
`ELIGIBLE_FOR_EXTERNAL_INDEPENDENT_REVIEW`; this module cannot ingest its own
review receipt, advance to the reviewed state, or authorize an operation.

## 5. PhysioNet admission preflight

The PhysioNet module provides pure validation for the future exact archive,
allowlisted-file inventory, snapshot, governance, support, duplicate audit,
patient-disjoint split, and admission receipts. It binds the existing raw
parser/inventory identity and the exact F105 37-variable `R^112` transform.

The patient splitter is deterministic and natural-group disjoint. It accepts
only an explicit F061 allocation and refuses unresolved, malformed,
underpowered, overlapping, exclusion-dependent, retried, or resplit inputs.
The shared-policy adapter may construct the native proposal only after the
patient count is observed. A separate external PhysioNet power review must then
explicitly accept a domain-separated digest of that exact patient count,
proportions, Hamilton counts, minimums, and rounding rule. No patient or row may
be removed to make a split feasible.

The integrated native proposal binds the accepted shared-policy proposal,
policy-review receipt and acceptance, shared-policy definition digest, and the
exact PhysioNet adapter identity/digest. Those bindings establish lineage only:
the shared-policy review expressly does not accept the later snapshot-resolved
counts, which remain subject to the separate PhysioNet review.

The historical frozen split-design JSON remains bound by its raw SHA-256 as a
fixed-count candidate receipt. Its historical candidate algorithm identifier
is not advertised as the active successor. The active explicit-F061 Hamilton
contract instead has its own canonical successor payload and digest, which
bind the historical receipt as provenance without aliasing its identity.
That successor also binds and runtime-validates the exact patient-order domain
bytes, ASCII patient encoding, two-byte unsigned big-endian length prefix,
SHA-256 ordering digest, byte tie break, contiguous allocation, receipt order,
record inheritance, and content-addressed executable-policy identity.

Admission uses the already frozen ordered thirteen-component training-only
hard-violation vector and six receipt flags. Every count must be exactly zero,
every receipt must verify, and the duplicate/near-duplicate audit must pass.
That audit binds its exact algorithm and implementation, the snapshot, split,
patient/record projection and manifests, the derived eligible and checked
cross-split record-pair counts, full-roster completion, certificate, and input
and completion digests. Partial, foreign, or self-consistent forged audit
receipts fail closed.
The support receipt must identify a code-matched observation reference,
certificate, proof, and acquisition justification. The module never invents a
positive mixture, contamination, clipping, or theorem-convenience noise.

The following real-instance evidence remains absent:

- F019 immutable snapshot version/archive roster;
- F020 raw SHA-256 and byte count;
- F022 accountable governance determination;
- F033 normalized observation reference;
- F034 positive/common-support certificate;
- F058 private populated patient-disjoint split manifest;
- F061 power-reviewed shared policy plus the later snapshot-resolved exact
  patient allocation and domain review; and
- the actual zero-violation/six-receipt admission record.

## 6. Online Retail II admission preflight

The Retail module implements the effective F060 V2 source-civil rule. Its
normalized timestamp carrier is source-civil microseconds since
`2009-12-01 00:00:00`, within the frozen 739-day horizon; it makes no UTC,
offset, locale, or daylight-saving claim. The exact normalized key is
`timestamp_source_civil_microseconds_since_2009_12_01`; shortened aliases are
not accepted.

The splitter keeps every row of one customer together, searches only exact
customer-disjoint chronological windows, accepts an explicit F061 allocation,
and fails closed if no exact boundary pair exists. An accepted shared policy is
projected through the content-addressed Retail adapter into Retail's native
proposal codec before its own definition is resolved. Exclusion, quarantine,
customer migration, retry, resplit, top-up, and post-outcome repair remain
forbidden.

The integrated admission path accepts only the exact-proportions Hamilton mode
and binds the accepted shared-policy definition plus the exact Retail adapter
identity/digest. The generic native splitter may still validate an exact-count
input as a local utility, but such an input is not eligible for this integrated
admission package and cannot bypass the shared-policy lineage.

The historical 70/15/15 Retail split-design JSON remains bound by its actual
raw hash and historical algorithm identifier. The earlier value once reused as
a Retail contract hash is retained and explicitly labeled only as a legacy
misbound F105 semantic digest; it is never accepted as a split contract. The
active source-civil/shared-policy/replay successor has its own canonical,
runtime-recomputed contract record and digest.

Admission does not trust a caller-constructed split receipt. It requires the
exact normalized rows and F061 allocation, replays the F060 split, rebuilds the
receipt against the snapshot, and compares every field and self-digest. The
duplicate audit binds its exhaustive algorithm and implementation, the exact
split/projection/manifests, derived eligible and checked cross-split row-pair
counts, a complete-roster attestation, its certificate, and its input and
completion digests. A partial or zero-pair audit cannot pass as complete.

Its snapshot, schema, governance, support, duplicate-audit, split, and
admission receipts follow the same strict principles as PhysioNet. The support
seam remains visible: the only recognized route is the already accepted
acquisition-justified positive dominated-mixture policy. A normalized
reference, full-support component, positive weight, proof, implementation,
certificate, scientific acquisition justification, and independent review are
all required. The module neither selects the still-unproved structural-zero
extension nor fabricates a component merely to make a theorem apply.

The following real-instance evidence remains absent:

- F038 immutable snapshot version;
- F039 raw SHA-256 and byte count;
- F041 accountable governance/privacy determination;
- F053 normalized observation reference;
- F054 positive/common-support certificate;
- F059 private populated customer-disjoint temporal split manifest;
- F061 power-reviewed exact allocation/count projection; and
- the actual zero-violation/six-receipt admission record.

## 7. Local-data and custody finding

A metadata-only filename scan of the project and the two additional writable
workspace roots found no identifiable PhysioNet Challenge 2012 archive or
record dataset and no identifiable Online Retail II workbook, archive, real
snapshot manifest, populated split manifest, approval receipt, or admission
receipt. This is a workspace-scoped result, not a claim of global absence.

The earlier PhysioNet root-page custody row has a zero-byte body, no emitted
HTTP request, and a terminal no-retry outcome. It is not a dataset snapshot.
No real dataset was opened or parsed during this package.

## 8. Qualification and hostile cases

Qualification requires:

1. exact byte/hash binding for every package and frozen predecessor file;
2. semantic self-digest agreement for the canonical machine record;
3. pure focused tests for all three implementation modules;
4. synthetic deterministic split replay in both domains;
5. hostile rejection of malformed hashes, byte counts, paths, owner rosters,
   reordered admission vectors, nonzero violations, missing receipts,
   structural-zero shortcuts, group overlap, exclusions, retries, resplits,
   underpowered/unresolved allocations, and infeasible temporal boundaries;
6. hostile rejection of skipped state-machine stages, non-null future
   observations, ADMIN permission expansion, DATA-row activation, and any
   nonzero current execution budget; and
7. independent review with no unresolved P0, P1, or P2 finding.

All tests use synthetic in-memory values or read-only package bytes. The
package exposes no network, connector, subprocess, credential, entropy,
acquisition, raw-data opening, training, inference, result, release, or
submission route.

## 9. Closure boundary and next exact action

Upon independent GO, this package closes exactly one enabling timetable item:

`B02_B03_JOINT_OFFLINE_ACTIVATION_PREFLIGHT_IMPLEMENTED_AND_QUALIFIED`.

It closes no F field, B02/B03 blocker, Formal Test, scientific result, or one
of the seven operational Solo-Block-2 actions. In particular, code that can
validate future evidence is not itself that evidence.

The next exact action is to populate the owner/approval/escrow manifest and
obtain an independent acceptance of the shared F061 allocation policy. The
Retail native proposal can then be projected deterministically; the PhysioNet
native proposal and its exact counts must wait for the observed immutable
patient count and a separate domain review. Only after the complete finite
precontact instance is populated and independently admitted may a fresh
authorization bind the accepted package aggregate, exact ADMIN rows 0 and 1,
exact URLs/request hashes, one attempt each, and zero retry/redirect/fallback
while keeping authentication, download, and data access false.
