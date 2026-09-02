# B02/B03 locally decidable definition records

**State:** `THREE_OFFLINE_DEFINITIONS_FROZEN_OPERATIONAL_HOLD`  
**B02/B03/F061:** open/open/open  
**Contact, network, data, escrow, or scientific execution:** none

## Outcome

This additive package freezes exactly three definitions that can be decided
from accepted local design evidence without appointing people, asserting keys,
contacting a source, or observing data: the held-out-material definition, the
final-opening rule, and the append-only contact/access-log schema. Their
canonical records use distinct domain-separated SHA-256 digests and bind the
active PhysioNet and Retail split-contract lineage.

These records are definitions, not populated controls. They do not claim that
held-out material, a split manifest, an escrow, an approver, an authority, or
an operational log exists. They create no attempt budget or authority and do
not close B02, B03, F061, an operational task, or a scientific field.

## Exact boundary

Eight non-F061 slots necessarily remain unresolved: both selector records, the
contact-target roster and count, the approval-requirement roster, the approval-
receipt-validator roster, contact-roster completeness, and the escrow-control
binding. The conflict-of-interest determination also remains unresolved. All
nine owner principals and acceptances, all keys and ACLs, every external
observation, external independent review, authority, and operational budget
remain null, false, or zero.

The held-out definition treats the complete TEST assignments and all outcome-
bearing descendants as held out; mixed or unknown lineage fails closed. The
final-opening rule requires a content-addressed freeze, closed development,
a distinct accepted approver, fresh exact authority, durable intent, and the
prior log head. The log schema freezes separate immutable `0600` `O_EXCL`
files for INTENT and OUTCOME events and separate immutable per-ordinal head
files. Every OUTCOME's repeated `operation_started_time` must exactly equal the
same field in the INTENT bound by `intent_entry_sha256`; its finish time cannot
precede that shared start. The highest contiguous verified head is current.
Exact domains, links, types, nullability, timestamps, outcomes, ordering,
fsync, and terminal recovery rules permit no overwrite, retry, fallback,
deletion, or repair.

## Lineage and files

The package binds the exact bytes of the sealed offline activation package and
its internal independent qualification review, plus this document and the pure
definition module. Its closed-world machine record is
`research/fixtures/manuscript_v3_b02_b03_locally_decidable_definition_records_v1.json`.
The separate read-only validator and hostile test are outside semantic self-
binding to avoid a hash cycle.

This package contains no independent review receipt. A separate reviewer may
qualify its exact bytes later. Until then it is an offline successor candidate
only and must not be used to populate the remaining evidence slots.
