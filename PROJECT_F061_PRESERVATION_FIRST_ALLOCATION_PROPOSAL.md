# F061 preservation-first shared allocation proposal

**Reported:** 2026-09-01  
**State:** `F061_PROPOSAL_FROZEN_AWAITING_SEPARATE_INDEPENDENT_POWER_REVIEW`  
**Package kind:** `ADDITIVE_F061_PROPOSAL_AND_EXACT_COUNT_COMPATIBILITY_GUARD`  
**F061:** open  
**B02/B03:** open  
**Network, contact, data, runtime, or science:** none

## 1. Outcome

This additive successor freezes one exact shared F061 proposal and a stricter
compatibility guard without changing any byte accepted by the B02/B03 offline
activation review or either accepted domain module. It fills no live tracker
field and is not an independent review of its own proposal.

The proposal preserves the historical pre-outcome 70/15/15 Hamilton design
while reconciling it with the later independently accepted statistical roster:

- F111 requires an exact 128-natural-group validation roster in each domain;
- F134 fixes exactly 128 natural groups per domain for the confirmatory route;
- all natural groups must be allocated, with no exclusion, replacement, top-up,
  retry, resplit, or proportion change; and
- the accepted activation core already provides a shared exact-proportions
  codec and domain-separated Retail and PhysioNet adapters.

The result is a proposal ready for a later, separately staffed independent
technical/statistical power-policy review. Until such a review byte-binds this
successor and explicitly accepts
the exact-count guard, the review receipt, review acceptance, and accepted
definition slots remain strict null and F061 remains open.

A first independent review returned `NO_GO` and issued no receipt. This
in-place candidate remediation closes only its two reported implementation
findings: the guarded-review carrier is now strict JSON-native raw bytes, and
the reviewer attestation has a frozen noncircular digest formula. It does not
convert that failed review into acceptance.

## 2. Exact twelve-slot proposal state

The first nine F061 slots are proposed as follows:

| Slot | Exact proposed value |
|---|---|
| `f061_allocation_id` | `TWO_DOMAIN_F061_HAMILTON_70_15_15_EXACT_128_VALIDATION_TEST_V1` |
| `f061_mode` | `EXACT_PROPORTIONS_HAMILTON` |
| `f061_values` | `(70, 15, 15)` for TRAIN, VALIDATION, TEST |
| `f061_denominator_is_null` | exact Boolean `false` |
| `f061_denominator` | exact integer `100` |
| `f061_minimum_counts` | `(1, 128, 128)` |
| `f061_rounding_rule_id` | `HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1` |
| `f061_power_requirement_id` | `B07_F134_EXACT_128_VALIDATION_AND_TEST_GROUPS_NO_EXCLUSION_V1` |
| `f061_allocation_proposal_sha256` | `cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679` |

The last three slots remain exactly:

| Slot | Current value |
|---|---|
| `f061_power_review_receipt_sha256` | `null` |
| `f061_power_review_accepted` | `null` |
| `f061_allocation_definition_sha256` | `null` |

The proposal digest is the existing accepted-core codec, not a replacement
codec:

```text
SHA256(
  UTF8("heterodiff/two-domain-f061-shared-policy-proposal/v1\0") ||
  canonical_ASCII_JSON(exact nine-field proposal)
)
```

The same known answer is reproduced independently by the accepted activation,
Retail, and PhysioNet shared-policy codecs.

## 3. Hamilton exact-count compatibility

Let `N` be the complete natural-group count before any split. Apply Hamilton
allocation to 70/15/15 with denominator 100 and descending integer remainder;
ties are resolved TRAIN, then VALIDATION, then TEST. The validation and test
counts are both exactly 128 if and only if:

| `N` | TRAIN | VALIDATION | TEST |
|---:|---:|---:|---:|
| 852 | 596 | 128 | 128 |
| 853 | 597 | 128 | 128 |
| 854 | 598 | 128 | 128 |
| 855 | 599 | 128 | 128 |

Thus the admissible total set is exactly `{852, 853, 854, 855}`. Every other
positive total is terminal:

```text
F061_EXACT_128_VALIDATION_TEST_COMPATIBILITY_TERMINAL_NO_GO
```

For example, `N=851` yields `(596,128,127)` and `N=856` yields
`(599,129,128)`. Neither is admissible. A larger count satisfying the minimum
is not a substitute for the exact later roster. There is no exclusion,
subsampling, group dropping, top-up, retry, resplit, alternate denominator,
or post-observation proportion change.

The exact guard has a separate semantic digest because the accepted proposal
codec binds minimums, not equality:

```text
98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef
```

This digest covers the exact 128/128 equality, the four admissible totals and
count triples, all-group preservation, terminal no-go rule, supported
entrypoint roster, direct-predecessor exclusion, Retail feasibility nonclaim,
the separate later PhysioNet count-review requirement, the exact raw-receipt
carrier, the reviewer-attestation formula, and the source/custody trust
boundary.

## 4. Sole supported successor entrypoints

For this policy, the sole supported projection and resolution entrypoints are:

```text
project_reviewed_shared_policy_to_retail
resolve_reviewed_retail_policy
project_reviewed_shared_policy_to_physionet_review_candidate
```

They live in
`src/heterodiff/data/two_domain_f061_preservation_first_successor.py` and wrap
the accepted generic predecessors without modifying them. Every count-bearing
entrypoint applies the equality guard before it can return a resolution.

Direct calls to the generic predecessor projection or Retail resolution are
unsupported for this exact policy. Those accepted predecessors correctly
implement their earlier contract: counts must meet minima. For example, their
generic path can accept validation count 129 when the minimum is 128. The
successor contract is narrower: later F111/F134 evidence requires equality,
so the supported wrapper rejects that same input terminally.

## 5. Future review must transitively bind the guard

A future `f061_power_review_receipt_sha256` is eligible only if it is the raw
SHA-256 of a canonical guarded-review receipt that includes all of the
following exact bindings:

1. shared proposal digest
   `cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679`;
2. exact-count guard digest
   `98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef`;
3. raw SHA-256 of this successor source and human record;
4. raw and semantic SHA-256 of the successor machine record;
5. the successor non-machine package aggregate, which covers the human,
   source, validator, and hostile-test bytes;
6. the exact sole-supported-entrypoint roster and explicit rejection of direct
   generic predecessor entrypoints;
7. an exact internal independent technical/statistical acceptance decision,
   reviewer principal, reviewer attestation,
   source/package reopening attestation, and independence/conflict check.

The authoritative receipt carrier is exact built-in `bytes` containing
duplicate-free canonical ASCII JSON with no terminal LF. Canonical JSON uses
sorted keys, separators `,` and `:`, no NaN or infinity, and JSON-native
arrays. In particular,
`sole_supported_projection_resolution_entrypoints` decodes to an exact
built-in list, not a tuple or subclass. Dict-only, bytearray, malformed,
duplicate-key, non-ASCII, pretty-printed, reordered-key, whitespace-suffixed,
and terminal-LF carriers fail closed.

The reviewer-attestation field is noncircular:

```text
independent_reviewer_attestation_sha256 =
  SHA256(
    ASCII("heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1\0")
    || canonical_ASCII_JSON(
         every exact receipt field except
         independent_reviewer_attestation_sha256
       )
  )
```

The source validator recomputes this value. It is a content attestation, not a
signature and not proof of externally authenticated reviewer identity.

The review's custody validator must reopen those bytes independently. The pure
source checker validates receipt structure, canonical raw bytes, attestation,
and digest linkage only; it cannot self-pin or independently reopen its own
raw source hash. Therefore actual source, human, machine, validator, test, and
package-aggregate reopening remains an explicit independent-custody duty. It
does not authenticate a reviewer or certify its own bytes. This review is not an
institutional, governance, ethics, privacy, operational, contact, or data-use
approval, and it does not claim externally authenticated reviewer identity.
The guarded receipt's
raw digest must equal the activation binding's
`f061_power_review_receipt_sha256`; the accepted core definition digest must
then bind that receipt digest, the exact proposal digest, and exact
`power_review_accepted=true`.

This chain makes the eventual definition transitively bind the equality guard:

```text
accepted F061 definition
  -> guarded review receipt raw digest
    -> proposal digest + guard semantic digest
       + successor source/human/machine/package exact bytes
```

A syntactically valid accepted-core binding without these exact raw
guard-binding receipt bytes
is refused by every supported successor entrypoint. This package does not
construct, simulate, pre-accept, or reserve such a receipt.

## 6. Domain boundary

### Retail

After a later guarded shared-policy acceptance, the Retail adapter may project
the exact proposal and the successor wrapper may resolve counts only for the
four admissible totals. Count resolution does not prove that the source-civil
F060 exhaustive gap-pair search has a feasible temporal boundary. A Retail
snapshot can still terminate no-go for temporal infeasibility, schema,
governance, support, custody, duplication, or admission reasons.

### PhysioNet

After a later guarded shared-policy acceptance and observation of the immutable
natural-group count, the PhysioNet wrapper may build a native proposal only for
one of the four admissible totals. The output deliberately leaves its separate
exact-count review receipt and acceptance null. The shared review establishes
lineage but never accepts the later snapshot-resolved patient counts.

No current snapshot count is observed or inferred. This package does not claim
that either domain has 852--855 available and admissible natural groups.

## 7. Preservation and evidence lineage

The package fixed-binds the complete ten-artifact accepted B02/B03 activation
candidate plus its independent review receipt. In particular, the accepted
activation core, Retail module, PhysioNet module, and their accepted tests
remain byte-for-byte unchanged.

It also fixed-binds the complete eight-artifact accepted theory/statistics
candidate plus its independent review receipt. That lineage supplies the
accepted F111 exact validation-roster rule, F134 exact 128 groups per domain,
no-quota-reduction rule, and B07 power/seed schedule. The older power route and
70/15/15 split-design records remain historical design evidence through the
accepted activation predecessor; neither is recharacterized as a power review.

`PROJECT_COMPLETION_TIMETABLE.md` and `PROJECT_EVIDENCE_LEDGER.md` are neither
package inputs nor outputs. No accepted predecessor is edited.

## 8. Authority and nonclaims

The visible instruction is exactly:

> Sounds good. Go ahead and finish them.

Its UTF-8 SHA-256 is
`3603d28cfd23787f17c427626c20792e9e66f3383b55d6d8090915ea9c7bea5c`.
It authorizes bounded offline construction and qualification only. It does not
authenticate account identity or time and grants no network, contact,
approval, data, snapshot, split, escrow, entropy, training, inference,
scientific-execution, result, release, claim, or submission authority.

This package:

- does not close F061, B02, B03, a Formal Test, a scientific field, a result,
  or an operational task;
- does not edit the timetable, evidence ledger, preregistration, manuscript,
  accepted core, or accepted domain modules;
- supplies no observed group count, real allocation, temporal boundary,
  split manifest, approval, reviewer identity authentication, or review
  acceptance;
- does not claim the later accepted B07 schedule independently proves this
  allocation policy; and
- does not promote synthetic `_complete_bindings()` or test receipts into
  project evidence.

## 9. Next exact action

Obtain a separately staffed independent technical/statistical review of this
exact content-addressed package. That review must issue the canonical guarded
receipt described above and
explicitly accept both the shared proposal and exact-count guard. Only then may
the accepted activation definition slots be populated and F061 considered for
closure. Retail resolution remains conditional on a complete eligible customer
roster and F060 feasibility; PhysioNet resolution remains conditional on the
observed immutable patient roster and a separate later native-count review.
