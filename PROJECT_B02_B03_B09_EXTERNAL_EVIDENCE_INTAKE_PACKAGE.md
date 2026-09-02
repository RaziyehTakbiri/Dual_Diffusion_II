# B02/B03/B09 external-evidence intake package

**State:** `INTAKE_CONTRACT_FROZEN_AWAITING_REAL_EXTERNAL_EVIDENCE`  
**B02/B03/B09:** open/open/open  
**Network, contact, authentication, data, escrow activation, or science:** none

## Outcome

This package turns every remaining human or external prerequisite for the
two-domain B02/B03/B09 route into one exact, fail-closed intake contract. It
specifies the nine distinct accountable principals and their nine authenticated
acceptances, the nine unresolved definition slots, the exact private-evidence
manifest, canonical digest rules, independence constraints, keys and ACL
binding, and the boundary between evidence collection and operational
authority.

The package is deliberately empty. It appoints nobody, asserts no approval,
creates no key, contacts no source, opens no data, activates no escrow, and
grants no attempt budget. A structurally complete future packet reaches only
`ELIGIBLE_FOR_SEPARATE_EXTERNAL_INDEPENDENT_REVIEW`. It still cannot authorize
an ADMIN request, data access, a split, a held-out opening, or scientific work.

## What is already resolved

The intake contract binds the accepted local definitions and guarded F061
decision rather than asking a future submitter to recreate them:

- held-out-material definition:
  `6aa31c23117ee604cf862c8654175f33a7baa5c501a02983e91de4146154fc5d`;
- final-opening rule:
  `fe0b51906c69930d6c1252491634588b1b08f4a3ec888a9a92bd6c13720c5efd`;
- append-only log schema:
  `cf2e70cffd0e9deea4c5884b72489fccbcb0731695f2493fcf2a1f2182274fd3`;
- F061 allocation definition:
  `6c7beda87ccf1b9b60b0787619fc637eeb3ab34d5f68e09608d46b4dcf11f946`;
- canonical F061 independent-review receipt bytes:
  `906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d`.

## Exact remaining intake

### Nine principals and acceptances

Exactly one opaque principal identifier and one externally authenticated
acceptance receipt are required for each role:

1. accountable governance owner;
2. license/privacy/institutional approval endpoint;
3. raw-snapshot custodian;
4. deterministic split operator;
5. independent held-out escrow custodian;
6. independent final-opening approver;
7. key and ACL acceptance authority;
8. retention/deletion owner; and
9. incident-response owner.

All nine principal identifiers must be pairwise distinct. A name, email
address, role label, or self-authored placeholder is not an acceptable opaque
identifier. Every acceptance must bind the intake-contract digest, the exact
role and scope, the conflict-of-interest determination, all prohibited
authority claims, an external authentication method and evidence digest, an
RFC 3339 UTC issue time, and exact `acceptance=true`.

### Nine unresolved definition slots

The future populated envelope must contain:

1. a PhysioNet selector-record digest;
2. a Retail selector-record digest;
3. a complete contact-target-roster digest;
4. the exact contact-target count `2`;
5. an approval-requirement-roster digest;
6. an approval-receipt-validator-roster digest;
7. a conflict-of-interest-determination digest;
8. exact `contact_roster_complete=true`; and
9. an escrow-control-binding digest.

Unknown or silence never means “no approval required.” That conclusion needs a
signed determination and its source evidence. Contact-target count must equal
the exact roster length of two. The roster must cover exactly the frozen
PhysioNet and Retail ADMIN operations; additional or fallback targets require a
separately reviewed successor contract. A complete escrow binding must bind the accepted held-out
definition and opening rule, three distinct control principals, key and ACL
manifests, the storage boundary, retention/deletion policy, and incident
response policy, while retaining `activation_claimed=false` at intake.

### Private evidence manifest

The public package stores only content hashes and safe locators. Real identity,
signature, key, ACL, approval, and relationship evidence belongs under the
closed path pattern:

`research/private_evidence/b02_b03_b09/<evidence-group>/<receipt-file>`

No private directory or evidence file is created by this package. Each future
manifest item must declare an exact ordinal and role, canonical relative path,
positive byte count, raw SHA-256, media type, sensitivity flag, externally
verified authentication flag, and separate verification-receipt digest.
Required roles occur exactly once: seven externally decided record classes,
key and ACL manifests, and all nine principal acceptances. Secret key material
and raw personal data must never be embedded in the public machine record.

Hashes alone are never sufficient. Review eligibility requires the validator
to load all eighteen exact raw evidence objects through no-follow, single-link,
`0600` private-file custody; reject duplicate-key or noncanonical JSON; recompute
every byte count, raw digest, payload digest, and verification receipt; then
semantically replay every record. The replay cross-binds each acceptance to its
exact role, principal, contract, conflict determination, scope, prohibitions,
and authentication evidence; both selectors to the frozen domains and URLs;
the roster to its exact count and operations; every approval requirement to one
validator; the conflict determination to all 36 role pairs; and the escrow to
the accepted definitions, seven control principals, key manifest, ACL manifest,
storage boundary, retention/deletion policy, and incident-response policy.

## Minimal completion checklist

The external coordinator should complete these in order:

- [ ] Assign nine real, pairwise-distinct principals using opaque identifiers.
- [ ] Obtain nine externally authenticated, role-specific acceptance receipts.
- [ ] Produce and authenticate the conflict-of-interest determination covering
      every role pair with no identified conflict. Intake v1 admits neither a
      managed nor an unmanaged conflict; either requires a reviewed successor.
- [ ] Freeze both selector records and the complete two-domain contact roster;
      confirm the exact target count and completeness declaration.
- [ ] Freeze the per-domain approval requirements; explicitly authenticate any
      “no approval required” determination.
- [ ] Assign validators for every approval receipt and freeze the validator
      roster with complete coverage.
- [ ] Create the key and ACL manifests without exposing private key material;
      obtain acceptance by the distinct key/ACL authority.
- [ ] Bind escrow custody, final-opening approval, storage, retention/deletion,
      and incident response to the accepted local definitions.
- [ ] Place each real evidence object in the approved private evidence area and
      populate the exact eighteen-item evidence manifest.
- [ ] Run the read-only structural validator, then obtain a separate external
      independent review of the populated packet.
- [ ] Only after that review, request fresh exact authority for separately
      registered operations; never infer authority from intake completion.

## Fail-closed rules

The validator accepts exactly two structural states. A wholly empty template
returns `HOLD_REAL_EXTERNAL_EVIDENCE_INCOMPLETE`. A complete, exact, externally
verified manifest accompanied by all replayed raw bytes returns
`ELIGIBLE_FOR_SEPARATE_EXTERNAL_INDEPENDENT_REVIEW`.
Partial population, aliased principals, missing roles, booleans masquerading as
integers, noncanonical hashes or paths, unverified authentication, a self-
ingested review receipt, any nonzero budget, any authority flag, or any blocker
closure claim is rejected.

Synthetic complete values exist only inside unit tests to exercise the second
branch. They are not evidence, identities, approvals, or authority.

## Files and qualification boundary

The pure contract and structural population validator are implemented in
`src/heterodiff/data/two_domain_external_evidence_intake.py`. The canonical
machine fixture is
`research/fixtures/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json`.
A separate read-only custody validator and hostile unit tests are outside the
semantic self-binding to avoid a hash cycle.

This candidate contains no independent review of its own bytes. If a separate
review accepts the exact package, the only permissible timetable effect is to
close one enabling project-control item:

`B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_IMPLEMENTED_AND_QUALIFIED`.

The field delta, blocker delta, operational-task delta, Formal-Test delta, and
scientific-result delta remain zero. B02, B03, and B09 remain open until the
real external evidence and later execution evidence satisfy their existing
closure contracts.
