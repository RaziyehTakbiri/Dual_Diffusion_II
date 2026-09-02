# F061 preservation-first allocation independent review

**Review decision:** `ACCEPT_GUARDED_SHARED_POLICY`  
**Review kind:** internal independent technical/statistical policy review  
**P0/P1/P2:** `0/0/0`  
**Institutional, operational, governance, or data-use approval:** no  
**Reviewer identity externally authenticated:** no

## 1. Decision and exact receipt

I independently reopened the stable five-file successor and all twenty accepted
predecessor bindings before deciding. I accept the exact shared F061 proposal
and its preservation-first exact-count guard for their stated pre-outcome
scope. The canonical guarded receipt is 1,924 ASCII bytes with no terminal line
feed:

`research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json`

Its raw SHA-256 is
`906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d`.
The noncircular reviewer-attestation SHA-256 is
`cff5f426393fa714ea5530860a517c55265e103e20619d9cbb291cb905562afc`.
It is recomputed over the exact receipt mapping with the attestation field
removed, prefixed by the accepted NUL-terminated reviewer-attestation domain.

With that raw receipt digest and exact acceptance Boolean `true`, the accepted
activation-core codec independently gives F061 allocation-definition SHA-256
`6c7beda87ccf1b9b60b0787619fc637eeb3ab34d5f68e09608d46b4dcf11f946`.

## 2. Exact reviewed successor bytes

| Artifact | Bytes | Raw SHA-256 |
|---|---:|---|
| `PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md` | 12,695 | `2769df9d8da86b054857973b7025c03f6932e88fa683848171dd32af507ec052` |
| `src/heterodiff/data/two_domain_f061_preservation_first_successor.py` | 30,007 | `23ec428fad7997fb230613fa5c32b9fb68ef6a077d6d3aa20870e820dd2146f4` |
| `research/fixtures/manuscript_v3_f061_preservation_first_allocation_proposal_v1.json` | 15,037 | `4a6414b494328a7f7cd4030718af960764bb2ce1946fb7de093985983e725d32` |
| `research/diagnostics/manuscript_v3_f061_preservation_first_allocation_proposal_v1.py` | 34,046 | `3c2de5c40ae4dbc529aa95773aa2fc944892083d1050b1452f657fd8f06768b7` |
| `tests/unit/test_manuscript_v3_f061_preservation_first_allocation_proposal_v1.py` | 39,930 | `5be719dd73753f5ebd6ac8d51e46daf17152d1ea9f34dc3d9fa5c164577de7ef` |

The non-machine package aggregate is
`974c3c7ddc1c2316be9cfe42aeefabc7d3f81c5f3c61b5d5f9d33479f5ed669e`;
the machine semantic digest is
`de4f254330528b3ba191bc4e5ee73e41d6f81ad0d1402cd5a3977160380c88e4`.
The proposal digest is
`cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679`
and the remediated guard digest is
`98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef`.

## 3. Statistical and semantic audit

I independently recomputed Hamilton allocation for every positive total below
10,000 and analytically checked the adjacent rounding transitions. Validation
and test are both exactly 128 if and only if the complete natural-group total
is 852, 853, 854, or 855, producing respectively `(596,128,128)`,
`(597,128,128)`, `(598,128,128)`, and `(599,128,128)`. Totals 851 and 856
produce `(596,128,127)` and `(599,129,128)` and correctly terminate no-go.

The accepted F111 validation-only group-disjoint floor and F134 exact 128
natural groups per domain support the equality guard. The accepted theory
record expressly forbids quota reduction, replacement groups, repeated cases,
or silent reduction after admission. The successor consistently preserves all
natural groups and forbids exclusion, top-up, retry, resplit, alternate
proportions, or accepting a merely larger count.

Only these wrappers are supported:

1. `project_reviewed_shared_policy_to_retail`;
2. `resolve_reviewed_retail_policy`; and
3. `project_reviewed_shared_policy_to_physionet_review_candidate`.

The generic predecessors remain valid for their older minimum-count contracts,
but are explicitly unsupported for this exact-equality policy. The guarded
wrappers reject the demonstrated generic 856-total path. Raw canonical receipt
bytes, their raw digest, proposal/guard lineage, accepted-core definition
digest, and the wrapper inputs are all cross-bound.

Retail count resolution does not claim that an F060 temporal boundary exists.
PhysioNet projection remains only a later review candidate: its immutable
patient count must first be observed, and its resolved exact counts still
require a separate external PhysioNet review. The shared review does not accept
those future resolved counts.

## 4. Receipt and custody remediation review

The prior tuple/JSON mismatch is resolved. The authoritative receipt carrier is
canonical ASCII JSON with an exact list entrypoint roster. Raw JSON round trips
pass, while duplicate keys, malformed/non-ASCII/noncanonical bytes, forbidden
constants, terminal line feeds, wrong list order/type, and every attestation
mutation fail closed. The reviewer attestation is recomputed from a frozen
domain and a noncircular preimage. Supported wrappers require the exact raw
receipt bytes and reject digest mismatch or direct generic bypass.

The standalone validator reopened four current non-machine bindings and all
twenty predecessor bindings and returned
`PASS_PROPOSAL_ONLY_F061_REMAINS_OPEN` before this independent receipt existed.
The candidate hostile suite passed 139/139. The accepted activation, PhysioNet,
Retail, package, and theory/statistics regression union passed 429/429.

The activation-source phrase “before external power review” is historical
shorthand for review external to that pure proposal function, not a requirement
for externally authenticated identity or institutional approval. The accepted
human contract normatively requests independent shared-policy acceptance and
reserves an explicitly external review for later PhysioNet resolved counts.
The receipt schema also requires both external identity authentication and
institutional/operational/governance approval to remain false. These surfaces
are therefore consistent without altering accepted predecessor bytes.

## 5. Closure boundary and limitations

This review supports populating the accepted shared-policy review receipt,
acceptance, and definition bindings and therefore supports pre-outcome closure
of F061 only. It closes no blocker by itself. B02, B03, and B09 remain open.
It supplies no source selector, observed domain count, archive, snapshot,
temporal feasibility result, split manifest, governance determination, support
certificate, owner acceptance, contact, data access, escrow activation,
training, inference, scientific result, release, claim, or submission.

In particular, Retail feasibility and admission remain future fail-closed
checks, and the later PhysioNet snapshot-resolved exact-count review remains
mandatory and open. This internal reviewer principal is a technical review
lane, not an externally authenticated person or an institutional authority.
