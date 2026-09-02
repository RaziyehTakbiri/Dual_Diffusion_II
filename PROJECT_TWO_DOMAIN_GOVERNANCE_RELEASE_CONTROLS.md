# Two-domain governance, observation, admission, release, and anonymity controls

**Package state:** `TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_FROZEN_PREEXECUTION`  
**Reported date:** `2026-09-01`  
**Project state:** `DRAFT_NOT_EXECUTABLE`  
**Data acquired, opened, parsed, or split:** no  
**Approval, legal determination, release, audit report, or clean-room run created:** no

## 1. Scope and exact effect

This additive package implements the parts of B02, B03, B09, B10, and B11 that
can be completed from official public documentation and offline pre-outcome
design. It contains a pure control implementation, a machine contract, a
read-only validator, and hostile qualification tests. It neither contacts a
person nor accesses a dataset.

The validator never imports, compiles, or executes the bound source module. It
parses inert syntax and uses `ast.literal_eval` only on the five required,
unique module-level constant assignments; missing, duplicate, or nonliteral
assignments fail closed.

After independent acceptance, the package supports closure of exactly these 17
fields:

- PhysioNet: `F021`, `F025`, `F032`, `F035`, `F036`, `F037`;
- Retail: `F040`, `F044`, `F052`, `F055`, `F056`, `F057`;
- governance and release: `F163`, `F164`, `F165`, `F166`, `F167`.

The package closes no blocker. In particular:

- B02 still requires `F019`, `F020`, `F022`, `F033`, `F034`, `F058`, the raw snapshot
  hash, an applicable governance determination, the populated patient split,
  the observation-reference/support certificate, and independent admission;
- B03 still requires `F038`, `F039`, `F041`, `F053`, `F054`, `F059`, `F061`,
  the exact Retail snapshot and hash, an applicable governance determination,
  the populated customer split and counts, the observation-reference/support
  certificate, and independent admission;
- B09 still requires the actual applicable approvals/determinations and
  acceptance of the plans by the accountable owner; a plan is not an approval;
- B10 still requires a final venue package, populated content manifest, privacy
  and anonymity scans, dispositions, and an explicit release decision;
- B11 still requires `F169`, admitted independent identities and appointments,
  final reports, finding dispositions, and an observed clean-room reproduction.

### Accepted predecessor and exact additive transition

This package is an additive successor to the byte-bound accepted execution
preregistration, its accepted pre-execution closure, and the accepted F105
two-domain CKS metric package, including its independent-review receipt. The
machine record binds those ten predecessor artifacts and does not reinterpret
or replace them.

The accepted predecessor state is PRE 122 open / 44 closed, POST 3 open / 3
closed, total 125 open / 47 closed. Closing exactly the listed 15 PRE and 2 POST
fields yields PRE 107 open / 59 closed, POST 1 open / 5 closed, total 108 open /
64 closed: PRE -15/+15, POST -2/+2, total -17/+17, and **0 blockers closed**.

There is no authority or evidence here for training, formal-test execution,
scientific entropy, result inspection, claim promotion, release, submission, or
tracker mutation.

## 2. Official public-documentation observations

The following are semantic observations, not archived page-byte or transport
receipts. The package does not claim that the pages cannot later change.

### 2.1 PhysioNet

The official project page identifies **Predicting Mortality of ICU Patients:
The PhysioNet/Computing in Cardiology Challenge 2012**, version `1.0.0`,
published `2012-01-20`. It says anyone may access the files subject to the
specified license and identifies the file license as the Open Data Commons
Attribution License v1.0:

- project: <https://physionet.org/content/challenge-2012/1.0.0/>
- project-specific license text:
  <https://physionet.org/content/challenge-2012/view-license/1.0.0/>

The license text describes ODC-By v1.0 as permitting use, sharing, and
modification of the database subject to attribution. It also explicitly warns
that individual contents can involve rights outside the database license,
including privacy and data-protection rights. This package therefore records
the license/access facts but does not infer clinical-governance approval from
them.

The official source release identity is recorded as
`PHYSIONET_CHALLENGE_2012_VERSION_1.0.0_PUBLISHED_2012_01_20`, but it is not
misregistered as a local snapshot. `F019` and `F020` therefore remain open
until an exact acquired snapshot binds that release identity and raw hash.
`F021` is the exact public-documentation license/access record above. `F022`
remains open.

### 2.2 Online Retail II

The official UCI record identifies **Online Retail II**, dataset ID `502`, DOI
`10.24432/C5CG6D`, the file `online_retail_II.xlsx`, and a Creative Commons
Attribution 4.0 International license:

- dataset record: <https://archive.ics.uci.edu/dataset/502/online+retail+ii>

The official page says CC BY 4.0 permits sharing and adaptation for any purpose
with appropriate credit. `F040` is frozen as this exact source/license/access
record. Because the page does not expose an immutable file version or raw
digest, `F038` and `F039` remain open. No privacy or ethics determination is
inferred from the license.

## 3. Frozen partial-observation task

The same clean kernel is used for both domains. Let the complete generated
endpoint configuration `Y` be the already frozen occurrence-expanded
configuration for one natural group. Assign every occurrence a private
canonical ordinal after the raw row has passed the frozen adapter. Equal-valued
and simultaneous occurrences retain separate ordinals. For PhysioNet the
ordinal is the zero-based position among admitted time-series rows in original
record-file order after static descriptors are removed. For Retail it is the
already frozen contiguous source-workbook row ordinal. Neither domain may sort,
deduplicate, or regenerate ordinals for this purpose.

Conditional observation `A` is an unordered subconfiguration of `Y`. Each
occurrence is retained independently with exact probability `1/2`; a retained
occurrence keeps its event type, time, mark, and multiplicity unchanged. For a
source configuration with `n` occurrences, every exact ordinal subset has mass
`2^-n`. Empty `Y` maps to empty `A` with probability one.

The clean kernel ID is
`OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1`. It has:

- detection probability exactly `1/2` for every admitted occurrence;
- identity type/mark/time emission for retained occurrences;
- no confusion, clutter, false positives, timestamp jitter, value noise,
  imputation, deduplication, row synthesis, or group mixing;
- no data-fitted parameter; and
- no sampling implementation in this package. A future run requires its own
  frozen scientific entropy and seed custody.

This closes `F025/F032/F035` and `F044/F052/F055`. It deliberately does not
close `F033/F034/F053/F054`: the normalized observation reference and the
positive/common-support certificate must be separately constructed and
code-matched. Failure to do that is domain `NO_GO`; the clean kernel cannot be
changed merely to make a theorem apply.

## 4. Method-blind training-only admission rule

For each domain, compute the ordered vector of exact nonnegative integer counts:

1. raw-format failures;
2. identity failures;
3. unknown or unbound event-type rows;
4. missing or invalid required-value rows;
5. event-transform collisions;
6. horizon violations;
7. cap or overflow violations;
8. row exclusions;
9. natural-group exclusions;
10. natural-group split overlaps;
11. split-contract failures;
12. clean-kernel normalization failures; and
13. observation-subset failures.

`F036/F056` are
`MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1`, the maximum of that ordered
vector. `F037/F057` are
`ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1`. Admission additionally requires
verified nonnull receipts for the raw snapshot hash, license/access record,
governance approval, complete split manifest, and observation-reference/support
certificate, plus a separately verified exact/near-duplicate leakage-audit
receipt. The latter audit may distinguish independently occurring equal events
from shared source lineage; this package does not invent a distance threshold
or count all natural coincidences as leakage. Thus the current domains cannot
pass merely because the numeric vector has not yet been computed.

The statistic is computed only from training data and custody metadata and is
method-blind: it may not inspect validation/test events, labels, model outputs,
losses, metrics, or claims. Any positive component, missing receipt, malformed
report, exclusion, retry, resplit, top-up, or post-outcome repair is `NO_GO`.

## 5. Data-license compliance plan (`F163`)

The exact plan is `TWO_DOMAIN_DATA_LICENSE_COMPLIANCE_PLAN_V1`:

1. Before acquisition, bind the official source identity, direct official
   license URL, observed license name/version, required citation/attribution,
   acquisition method, raw byte count, and raw SHA-256.
2. Obtain and bind the applicable governance or institutional determination;
   public access and a copyright/database license are not substitutes.
3. Keep raw archives, normalized rows, identifiers, and split assignments in
   internal restricted custody. The default public bundle contains no source
   data or row/group-level derivative.
4. For PhysioNet, preserve the ODC-By notice/URI and source attribution for any
   permitted public produced work or database derivative; separately review
   rights in individual contents and clinical/privacy restrictions.
5. For Retail, preserve the UCI dataset citation, DOI, CC BY 4.0 notice and
   license link with any permitted public derivative.
6. Inventory every third-party code/model/data dependency with source, exact
   version/commit, license, compatibility, notices, and redistribution class.
7. A missing, conflicting, expired, unverifiable, or unapproved term is
   terminal `NO_GO`. No agent supplies legal advice or self-approves a legal,
   ethics, privacy, or institutional determination.

## 6. Clinical governance and interpretation (`F166`)

`PHYSIONET_CLINICAL_GOVERNANCE_AND_INTERPRETATION_PLAN_V1` requires:

- a documented determination by the applicable accountable institution before
  use, even though the official archive is publicly accessible;
- least-privilege internal custody, named access roles, retention/deletion
  rules, an incident route, and no attempt to identify or contact a patient;
- no patient-level public artifact, raw record, RecordID, split assignment,
  prediction, embedding, nearest-neighbor example, or reconstructable trace;
- aggregate reporting only after privacy review and cell-size disclosure
  review;
- explicit retrospective-research, non-diagnostic, non-treatment, and
  non-deployment language;
- no causal, bedside-utility, transportability, subgroup-equity, or prospective
  clinical claim without separately appropriate evidence; and
- clinical interpretation review before claim promotion.

The plan is frozen; the actual determination, owner acceptance, and review
remain absent.

## 7. Retail privacy and exposure control (`F167`)

`RETAIL_PRIVACY_DUPLICATE_EXPOSURE_MEMBERSHIP_PLAN_V1` treats CustomerID,
invoice identifiers, exact timestamps, free text, country, rare purchase
patterns, split assignments, row-level outputs, embeddings, and checkpoints as
internal restricted material. It requires:

- no public raw or normalized rows, customer/invoice keys, exact transaction
  traces, row-level predictions/samples, memorized examples, or nearest
  neighbors;
- exact duplicate, near-duplicate, cross-split group, temporal leakage, rare
  pattern, and free-text exposure audits;
- aggregate cells of fewer than 20 natural groups suppressed or coarsened,
  with all differencing/composition attacks reviewed across tables;
- model/checkpoint release withheld unless membership-inference, attribute
  inference, memorization/extraction, and canary controls pass a separately
  frozen audit with owner approval; and
- immediate `NO_GO` for a missing CustomerID or any row that would require
  exclusion under the already frozen whole-domain rule.

These are conservative project controls, not claims about identifiability of
the source or a completed privacy audit.

## 8. Release plan (`F164`)

`CODE_MODEL_ARTIFACT_RELEASE_PLAN_V1` requires one content-addressed manifest
that classifies every file as:

- `PUBLIC_PROJECT_CODE`;
- `PUBLIC_CONFIG_OR_SCHEMA`;
- `PUBLIC_AGGREGATE_RESULT`;
- `PUBLIC_MODEL_CANDIDATE`;
- `INTERNAL_RESTRICTED`; or
- `NEVER_RELEASE`.

The default release may contain project-created code, tests, environment locks,
schemas, documentation, and privacy-reviewed aggregate results. Raw or
normalized source data, natural-group identifiers, split manifests, row-level
outputs, custody logs, secrets, and internal absolute paths are forbidden.
Models/checkpoints remain internal until the F167 model privacy gates pass.

Before any owner release action, every manifest byte must be hashed and all
license-attribution, privacy, membership-inference, absolute-path, secret,
identity, and venue-anonymity reviews must pass. The pure helper returns only
`RELEASE_ELIGIBLE_FOR_SEPARATE_OWNER_ACTION`; it never performs a release.

## 9. Submission anonymization plan (`F165`)

`DOUBLE_BLIND_SUBMISSION_ANONYMIZATION_PLAN_V1` requires two scans of a clean
candidate package, with remediation and a fresh scan after any change:

- author names, handles, emails, affiliations, ORCIDs, acknowledgements,
  grants, self-identifying prose, repository/account names, and contact links;
- absolute paths, usernames, hostnames, job labels, workspace IDs, credentials,
  tokens, environment dumps, terminal histories, and internal custody paths;
- filenames, comments, revision history, tracked-change metadata, document/PDF
  metadata, image metadata, archive member names, hidden files, notebooks, and
  generated auxiliary files;
- citations and self-references for compliance with the selected venue's
  current anonymity rule; and
- byte-for-byte comparison between the scanned candidate and the final upload
  candidate.

The actual venue rules, package, scans, findings, dispositions, and upload are
future receipts. Consequently B10 remains open.

## 10. B11 boundary

The existing accepted F168/F170/F171 plans remain authoritative. This package
does not select an independent person, create an appointment or conflict-of-
interest receipt, populate `F169`, execute an audit, or run a clean-room
reproduction. A local subagent review of this package, if performed, is package
qualification and cannot substitute for the final B11 audits.

## 11. Package and qualification

The package roster is:

- `src/heterodiff/data/two_domain_governance_release_controls.py`;
- `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md`;
- `research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json`;
- `research/diagnostics/manuscript_v3_two_domain_governance_release_controls_v1.py`;
- `tests/unit/test_manuscript_v3_two_domain_governance_release_controls_v1.py`.

The source is pure. Hostile tests cover exact half-thinning support, duplicate
occurrences, malformed ordinal carriers, the zero-only admission threshold,
missing receipts, strict types, release classification, path traversal,
sensitive public entries, missing scans/approval, canonical machine JSON,
semantic self-digest, package hash bindings, and all nonclaims.

Independent acceptance may register only the 17-field delta in Section 1. It
must not close B02, B03, B09, B10, B11, any formal test, any result slot, or any
runtime/data/science/claim/submission gate.
