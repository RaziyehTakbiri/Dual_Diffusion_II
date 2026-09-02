# B02/B03 Offline Precontact Activation — Independent Review

**Review date:** 2026-09-01  
**Review kind:** internal independent exact-byte, semantic, hostile, and custody
review  
**Reviewer lane:** Codex `/root/implementation_code_audit`, with an isolated
package-validator sub-audit  
**Decision:** `GO_OFFLINE_PRECONTACT_QUALIFICATION_ONLY_OPERATIONAL_HOLD`  
**P0/P1/P2:** `0/0/0`  
**Machine semantic SHA-256:**
`2a150e0b3037d01e6b311d9ab4c17157f20031f75b644a7c8778007c168b9fec`

This is an internal technical review, not an externally authenticated identity,
institutional determination, governance approval, or externally attested time.

## 1. Exact decision

The exact sealed package is accepted for one bounded purpose:

`B02_B03_JOINT_OFFLINE_ACTIVATION_PREFLIGHT_IMPLEMENTED_AND_QUALIFIED`.

The package implements and qualifies an inert, closed-world offline activation
core for the future PhysioNet Challenge 2012 and Online Retail II precontact
workflow. It binds the active domain split implementations, their historical
design predecessors, the shared two-stage F061 policy boundary, the complete
owner and definition gap rosters, the exact four-operation future roster, and a
strict zero-authority execution boundary.

The operational decision remains `HOLD`. The package is not a populated
precontact instance, does not admit one, and creates no authority or attempt
budget.

## 2. Exact reviewed bytes

| Ordinal | Artifact | Bytes | Raw SHA-256 |
|---:|---|---:|---|
| 0 | `PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md` | 17,235 | `a7e882f209b26d9cf6dec449eb4fd93b78df0903be9294704ea857066dfe00ed` |
| 1 | `src/heterodiff/data/two_domain_offline_precontact_activation.py` | 51,882 | `f192e3eedbeb73f2eb1ea0705e56af65ea723a91071db93835b9b8f56046d97c` |
| 2 | `tests/unit/test_two_domain_offline_precontact_activation.py` | 32,506 | `e96d4648095fe25332ae36deac5f27a1aafe80cc5ac3b50a1efcd9f39b4b1144` |
| 3 | `src/heterodiff/data/physionet_2012_admission_preflight.py` | 136,305 | `bf5c12dcb5debe99533d00a813d7b522c42b588f5431803a8c2bac99b0f2bf07` |
| 4 | `tests/unit/test_physionet_2012_admission_preflight.py` | 67,299 | `25786cf1d2bc971c8b8f08c2aabc18fa192ed7b75fd67944486238fb83c8d57c` |
| 5 | `src/heterodiff/data/online_retail_ii_admission_preflight.py` | 89,545 | `3f204d65c87b8ee7896209c687f2394a1a9c23cdf9a7670b40227cf46e518764` |
| 6 | `tests/unit/test_online_retail_ii_admission_preflight.py` | 52,656 | `1016755132b5bfd0ef8378c6adee60eacbe5fb571240c06d5e84804c99769c5a` |
| 7 | `research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json` | 22,137 | `d74333a2c381daa953803e9346efb0ab63d6744265bfa8e7e260b1d1932fc0ee` |
| 8 | `research/diagnostics/manuscript_v3_b02_b03_offline_precontact_activation_v1.py` | 35,949 | `e1803c8ecccb63d0da4ebb71a9676291c45678b735f4cffc58b5073814d4647b` |
| 9 | `tests/unit/test_manuscript_v3_b02_b03_offline_precontact_activation_v1.py` | 23,669 | `03e85a57f4b57fca8d498295650a0672dbfb8f2e1c17358c93141370ca8c5716` |

The machine semantic record binds ordinals 0--6. The validator and package
tests at ordinals 8--9 are deliberately outside semantic self-binding to avoid
a hash cycle; this review binds their final bytes independently.

## 3. Frozen predecessor roster

The validator reverified this exact 16-file closed-world predecessor roster:

| Ordinal | Artifact | Bytes | Raw SHA-256 |
|---:|---|---:|---|
| 0 | `PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md` | 7,078 | `ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2` |
| 1 | `research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json` | 8,461 | `0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8` |
| 2 | `PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md` | 23,012 | `ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126` |
| 3 | `research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json` | 33,638 | `7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590` |
| 4 | `PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md` | 17,965 | `ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f` |
| 5 | `research/fixtures/manuscript_v3_solo_block2_precontact_instance_candidate_v1.json` | 23,932 | `95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be` |
| 6 | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md` | 15,242 | `5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef` |
| 7 | `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | 23,899 | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| 8 | `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` | 15,756 | `e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c` |
| 9 | `research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json` | 17,729 | `340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c` |
| 10 | `PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md` | 15,223 | `a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139` |
| 11 | `research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json` | 15,915 | `536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28` |
| 12 | `PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md` | 10,761 | `2d84753fe87032a81d377a469f858f1702b14474371bfd2d147fd87824bb4b7a` |
| 13 | `research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json` | 16,543 | `a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8` |
| 14 | `PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md` | 11,226 | `49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1` |
| 15 | `research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json` | 13,409 | `b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b` |

All 7 package bindings and all 16 frozen-input bindings matched after the final
test replay. The custody validator requires canonical relative paths, regular
`0644` single-link files, stable ancestors and leaf identity, exact byte counts,
exact SHA-256 values, bounded reads, and terminal line feeds.

## 4. Independent checks and results

| Check | Result |
|---|---:|
| Standalone read-only package validator | PASS |
| Package semantic/custody/hostile suite | 48/48 passed |
| Shared core focused suite | 95/95 passed |
| PhysioNet focused suite | 127/127 passed |
| Online Retail II focused suite | 99/99 passed |
| Combined three-module suite | 321/321 passed |
| Static compile and prohibited-I/O/import checks | clean |
| Exact package and frozen binding stability after tests | PASS |

The primary lane also replayed the standalone validator and all 48 package
tests from an unrelated working directory; both passed without relying on the
caller working directory.

The review verified:

- exactly four future operations, in fixed order, with ADMIN rows first and
  dormant DATA rows second;
- seven exact administrative questions on both ADMIN rows;
- no authentication, download, protected-data opening, redirect, retry,
  fallback, contact, split, escrow, or scientific execution capability;
- ten strict-false authority/capability flags and six exact-zero budgets;
- nine owner principals, nine owner acceptances, and one strict-null conflict
  determination;
- all 24 unresolved definition slots, comprising 12 shared F061 slots, 11
  other precontact definition slots, and the conflict determination;
- all three external-review slots and every future observation as strict null;
- exact active and historical PhysioNet and Retail split-contract lineage;
- full duplicate and near-duplicate audit receipt, coverage, and crosslink
  revalidation in both domain modules; and
- a two-stage F061 route: shared exact proportions first, followed by a
  separately reviewed PhysioNet exact-count projection after a real natural
  group count is observed.

## 5. Pre-seal findings remediated

The independent review identified and required remediation of these P2 issues
before the final seal:

1. the initial machine summary did not enumerate every owner, approval,
   selector, escrow, F061, and external-review null prerequisite;
2. hostile package tests did not directly exercise every malformed
   binding-hash, byte-count, ordinal, and unsafe-path carrier;
3. partial F061 HOLD states did not immediately reject a present nonpositive
   denominator, a true denominator-null flag, or a non-Hamilton rounding rule;
   and
4. the public missing-field inventory omitted the unresolved F061 denominator.

All four were corrected before sealing. Exact-type semantic comparison now
prevents Python boolean/integer/float coercion, hostile custody cases are
directly covered, malformed present F061 values fail immediately, and the core
null inventory and public missing-field report agree exactly at 24/24.

No P0, P1, or P2 finding remains on the reviewed bytes.

## 6. Closure and nonclosure

This review permits the tracker to close exactly one additive enabling item:

`B02_B03_JOINT_OFFLINE_ACTIVATION_PREFLIGHT_IMPLEMENTED_AND_QUALIFIED`.

Exact deltas:

| Surface | Delta |
|---|---:|
| Timetable enabling tasks checked | +1 |
| Scientific fields closed | 0 |
| B01--B12 blockers closed | 0 |
| Original Solo-Block-2 operational tasks closed | 0 |
| Formal Tests closed | 0 |
| Scientific result slots filled | 0 |
| Authority or attempt budget created | 0 |
| External contacts or requests made | 0 |
| Datasets authenticated, downloaded, opened, or parsed | 0 |
| Splits, escrow operations, training, inference, or scientific runs | 0 |

B02, B03, F061, and all seven original Solo-Block-2 operational tasks remain
open. The current state is
`OFFLINE_ACTIVATION_PREFLIGHT_COMPLETE_AWAITING_HUMAN_OWNER_ROSTER`.

## 7. Next admissible step

Populate the owner/acceptance, conflict-of-interest, approval-target,
approval-validator, contact-roster, escrow-control, and shared F061 policy
slots with real, content-addressed receipts. Then independently review that
populated precontact instance. Only after that separate admission may fresh,
exact ADMIN-contact authority be requested. This review supplies none of those
receipts or authorities.
