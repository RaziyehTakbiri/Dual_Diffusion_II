# Independent review: B02/B03 locally decidable definition records

**Decision:** `GO_THREE_OFFLINE_DEFINITIONS_ONLY`  
**Finding counts:** P0 = 0; P1 = 0; P2 = 0  
**Review boundary:** internal exact-byte qualification, not external approval

## Exact reviewed bytes

| Artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `PROJECT_B02_B03_LOCALLY_DECIDABLE_DEFINITION_RECORDS.md` | 2,996 | 55 | `29fc1c06ed81ac594ce24a23c2c8124d8bd1fef756d119d80a842b632682213a` |
| `src/heterodiff/data/two_domain_precontact_definition_records.py` | 12,661 | 296 | `eb4bd98f9190d2e9e7275e5a4f6f1c7fddfa34f8bf3435214b3060f4180d4e30` |
| `research/fixtures/manuscript_v3_b02_b03_locally_decidable_definition_records_v1.json` | 3,032 | 45 | `7b8ae7f454fd094cb1ce1b7b3b93fc50f72bf329cc550d9365c3df1779344e7f` |
| `research/diagnostics/manuscript_v3_b02_b03_locally_decidable_definition_records_v1.py` | 9,716 | 224 | `d7c2facebbe2417eb999768f3a98851457fd6baf44dd9a22e9966297ca21bb2e` |
| `tests/unit/test_manuscript_v3_b02_b03_locally_decidable_definition_records_v1.py` | 9,566 | 246 | `c1481656ce316180416ee89d74da8cd4cc44d8b28da1be5a637e06b4cb088f66` |

The review applies only to these exact bytes. Any byte change invalidates this
receipt and requires a fresh review.

## Independently recomputed definition digests

The reviewer independently serialized each record as ASCII canonical JSON
(`sort_keys=True`, compact separators, `ensure_ascii=True`, no NaN), prepended
its distinct NUL-terminated domain, and recomputed SHA-256:

| Definition | Canonical bytes | SHA-256 |
|---|---:|---|
| held-out-material definition | 1,277 | `6aa31c23117ee604cf862c8654175f33a7baa5c501a02983e91de4146154fc5d` |
| final-opening rule | 925 | `fe0b51906c69930d6c1252491634588b1b08f4a3ec888a9a92bd6c13720c5efd` |
| append-only contact/access-log schema | 5,024 | `cf2e70cffd0e9deea4c5884b72489fccbcb0731695f2493fcf2a1f2182274fd3` |

All three independently recomputed values equal the bound values. The active
PhysioNet and Retail split-contract identities and digests also equal the
accepted activation-core lineage bound by the fixture.

## Reproduced checks

- Standalone closed-world validation passed from the project root and from an
  unrelated `/private/tmp` working directory, each returning
  `PASS_OFFLINE_DEFINITIONS_ONLY`, definition count 3, no independent review
  present in the candidate, and no operational authority present.
- The focused hostile suite passed 23/23 from the project root and 23/23 from
  `/private/tmp`.
- Relevant predecessor suites passed 369/369.
- Python bytecode compilation and static undefined-name/import checks passed.
- Independent probes confirmed that an OUTCOME start identical to its bound
  INTENT start is accepted and a one-nanosecond mismatch is rejected.
- The displayed entry-digest label followed by exactly one NUL octet equals the
  bytes decoded from `entry_digest_domain_hex`; there is no display/hex domain
  ambiguity.

The hostile replay covered Boolean/integer aliases, floating-point zero,
duplicate top-level and nested JSON keys, roster ordinals, symlink and hardlink
leaves, symlinked ancestors and roots, alternate/absolute fixture paths,
fixture and accepted-ancestor custody, exact binding paths and roles, NUL-domain
equivalence, immutable per-entry INTENT/OUTCOME files, immutable per-ordinal
head files, prior-entry and prior-head chain completeness, orphan/collision/gap
recovery, and cross-event OUTCOME-to-INTENT timestamp continuity.

## Qualified semantics and limitations

This receipt qualifies exactly three locally decidable offline definitions:
the held-out-material definition, the final-opening rule, and the append-only
contact/access-log schema. The held-out definition fails closed for mixed or
unknown lineage and covers complete TEST assignments and every outcome-bearing
descendant. The final-opening rule retains one-attempt, fresh exact authority,
distinct accepted approver, content-addressed freeze, durable intent, and prior
head prerequisites. The log schema specifies one immutable `O_EXCL` file per
entry and one immutable file per head ordinal, domain-separated digests,
complete prior links, exact event pairing, timestamp continuity, fsync ordering,
and terminal no-retry recovery.

This is an internal engineering review receipt. It is not an external
independent approval, principal acceptance, conflict-of-interest determination,
contact authority, data authority, key or ACL binding, escrow binding, or field
observation. It creates no network/contact/data/scientific budget, permits no
operation, edits no tracker or ledger, and closes neither B02, B03, F061, any
operational task, nor any scientific field. All populated-control and external-
authority slots remain blocked, null, false, or exact integer zero as specified
by the candidate package.
