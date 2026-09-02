# Independent review: B02/B03/B09 external-evidence intake contract

**Review date:** 2026-09-01  
**Decision:** `GO_OFFLINE_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_ONLY`  
**Finding counts:** P0 = 0; P1 = 0; P2 = 0  
**Review boundary:** independent internal exact-byte engineering qualification,
not external evidence acceptance, institutional approval, or operational
authority

## Exact reviewed bytes

| Ordinal | Artifact | Bytes | Lines | SHA-256 |
|---:|---|---:|---:|---|
| 0 | `PROJECT_B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_PACKAGE.md` | 8,700 | 172 | `08813c91b11e33f34bd6ff5a3e41197d029bd3d90fd18431c43182771e6b16ad` |
| 1 | `src/heterodiff/data/two_domain_external_evidence_intake.py` | 68,846 | 1,732 | `ede0c1890d1e1f39a522a064fe94a78ab65fe5618687ca525c05b4cba7001d85` |
| 2 | `research/fixtures/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json` | 11,920 | 249 | `af4d46e652d24d71382a746e3a043491c2f978275098e266e6f77f4286906a9f` |
| 3 | `research/diagnostics/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.py` | 14,537 | 368 | `29a7661b68f249d0cb9a8c295c21ac84e27b916c78b2f7ad532d86a1a4975225` |
| 4 | `tests/unit/test_manuscript_v3_b02_b03_b09_external_evidence_intake_v1.py` | 17,693 | 417 | `17ab7d1f688184a1a93b9fd7f821d78bad27e59f7aa54e79ace4669a2dd1e415` |

All five were regular `0644`, single-link files on device `16777234` at the
final replay. The review applies only to these exact bytes. Any byte change
invalidates this review and requires a fresh independent review. The exact
contract-record SHA-256 independently recomputed as
`0d145f31dcb3f1a1a84c7845cf6a469c5e4b8ade8a9a66eb630c988d2eda02b9`.

## Reproduced results

| Check | Result |
|---|---:|
| Standalone read-only validator, Python 3.11 | PASS |
| Standalone read-only validator, Python 3.9 | PASS |
| Focused package/hostile/custody suite, Python 3.11 | 49/49 passed |
| Focused package/hostile/custody suite, Python 3.9 | 49/49 passed |
| Independent additional hostile probes | 333/333 passed |
| Active shared/PhysioNet/Retail precontact-core regressions | 321/321 passed |
| Bound activation/definition/F061/governance/split package regressions | 404/404 passed |

The 404-test replay temporarily isolated and then restored three pre-existing
Retail bytecode-cache files so that the predecessor's cache-hygiene assertion
could be executed rather than excluded. No candidate, accepted predecessor,
tracker, ledger, or source-reference byte was changed by that replay.

## Hostile review coverage

The independent probes replayed all eighteen raw evidence-object roles, not
only their public digests. For every role they exercised missing and extra
terminal line feeds, noncanonical whitespace, duplicate JSON keys, raw-digest
and verification-receipt substitution, envelope-role substitution, and a
fully rebound foreign payload field. The raw parser accepted only exact
built-in bytes containing ASCII canonical JSON plus one terminal LF, rejected
duplicate keys, and recomputed each manifest byte count, raw SHA-256, payload
digest, verification-receipt digest, and semantic cross-link.

The review also covered:

- exact built-in type enforcement and equality-liar subclasses on instance,
  principal, receipt, definition, count, manifest, path, digest, media,
  authority, blocker, raw-bundle, and raw-byte surfaces;
- semantic Gregorian validation on both acceptance issue times and all ACL
  effective-time surfaces, including invalid 1900/2026 leap dates, invalid
  month ends, valid 2000/2024 leap dates, and valid month ends;
- all nine pairwise-distinct owner principals, all eighteen external-verifier
  versus owner separation checks, and the complete 36-pair conflict roster;
- the v1 no-conflict boundary: any identified managed or unmanaged conflict is
  rejected and requires a separately reviewed successor;
- exact two-target contact coverage, fixed PhysioNet and Retail ADMIN
  operations and destinations, no additional or fallback target, exact count
  `2`, and exact completeness;
- per-domain approval determinations, the signed-no-approval branch, global
  requirement uniqueness, one-to-one complete validator coverage, accepted
  issuer binding, and validator-versus-owner separation;
- selector identity and URL bindings, key custody and key/ACL acceptance,
  three-entry least-privilege ACL semantics, seven escrow-principal links,
  accepted held-out/opening definitions, key/ACL digests, and
  `activation_claimed=false`;
- no-follow canonical-root custody, exact `0600` private evidence files,
  regular-file and single-link enforcement, and rejection of leaf, ancestor,
  root-symlink, hard-link, mode, path, size, digest, and identity attacks;
- all false authority flags, all exact-zero budgets, self-review rejection,
  tracker/ledger nonclaim, blocker nonclosure, exact machine-package bindings,
  duplicate/foreign machine JSON, and closure-delta substitution; and
- exact accepted lineage for the three local definitions, the guarded F061
  definition and raw review receipt, governance controls, and both active
  split-design predecessors.

Future content identifiers for the storage boundary, retention/deletion
policy, incident-response policy, authentication evidence, and other external
records are intentionally population-time values. Changing one is not a
valid substitution of an already frozen populated packet: the raw evidence
object, its payload digest, its manifest digest, and every dependent outer
binding must all change, after which the resulting packet still reaches only
external-review eligibility. This internal review makes no claim that any
future digest identifies genuine evidence.

## Qualified semantics and trust boundary

The exact candidate is qualified as an inert, closed-world structural intake
contract. Its empty instance returns
`HOLD_REAL_EXTERNAL_EVIDENCE_INCOMPLETE`. A fully populated, semantically
cross-bound eighteen-object instance can return only
`ELIGIBLE_FOR_SEPARATE_EXTERNAL_INDEPENDENT_REVIEW`.

The validator deliberately does not authenticate a real person, verify an
external signature, adjudicate the truth of a source-evidence digest, or
convert structural completion into admission. Opaque principal syntax,
pairwise role separation, raw-object replay, and a declared external
verification result are necessary structural conditions, not proof of real
identity or external authority. The later external reviewer must reopen the
private evidence, authenticate the principals and signatures, reject names,
role labels, placeholders, or false attestations, verify the underlying
evidence, and separately accept the populated packet. Synthetic complete
values remain test fixtures only and are not evidence.

## Exact closure and nonclosure

This review does not itself edit the timetable or evidence ledger. After this
review is separately registered, exactly one enabling project-control item is
eligible to be checked:

`B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_IMPLEMENTED_AND_QUALIFIED`.

No other task or field is eligible to close from this review.

| Surface | Exact delta |
|---|---:|
| Scientific fields closed | 0 |
| B01--B12 blockers closed | 0 |
| Original operational tasks closed | 0 |
| Formal Tests closed | 0 |
| Scientific result slots filled | 0 |
| Network/contact/authentication/data/snapshot/split/escrow/science operations | 0 |
| Authority flags made true | 0 |
| Attempt budgets made nonzero | 0 |

B02, B03, and B09 remain open. All nine real principal assignments, all nine
real authenticated acceptances, all nine future definition bindings, all
eighteen real private evidence objects, the populated-packet external review,
and every later exact operational authority remain absent or pending. This
review date is local metadata and is not externally attested.
