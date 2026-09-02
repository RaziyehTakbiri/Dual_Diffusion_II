# B02 PhysioNet public-documentation observation and exact admission-gap checklist

**Package status:** `CANDIDATE_PUBLIC_DOCUMENTATION_AND_EXACT_FUTURE_RECEIPT_CHECKLIST_ONLY`  
**Reported date:** `2026-09-02` (local calendar date; not externally attested)  
**B02 status:** `OPEN`  
**B09 status:** `OPEN`  
**Field, blocker, task, Formal-Test, and result delta:** zero

## 1. Outcome

The official PhysioNet pages make the public source route materially clearer,
but they do not complete the project's evidentiary chain. A read-only public
documentation inspection confirmed the displayed dataset version, public
access classification, file license, and one archive's displayed byte count.
It did not download dataset bytes, capture an exact HTTP response, compute an
archive SHA-256, authenticate an accountable owner, create an institutional or
clinical determination, certify common support, create a real split, or admit
the domain.

Accordingly, this package closes no field or blocker. Its contribution is a
closed-world, machine-readable twelve-step authority-and-receipt checklist
bound to the already implemented fail-closed PhysioNet admission preflight.
That checklist prevents a future public-source observation from being mistaken
for a real snapshot, an approval, or an admission decision.

## 2. Official public documentation observed

The inspection was limited to these official public pages:

- [dataset root](https://physionet.org/content/challenge-2012/1.0.0/);
- [set-a archive metadata page](https://physionet.org/content/challenge-2012/1.0.0/set-a.tar.gz); and
- [dataset license page](https://physionet.org/content/challenge-2012/view-license/1.0.0/).

The pages displayed the following facts:

- title: `Predicting Mortality of ICU Patients: The PhysioNet/Computing in
  Cardiology Challenge 2012`;
- version: `1.0.0`;
- publication date: `2012-01-20`;
- access class: `Challenge Open Access`;
- access policy: anyone may access the files subject to the specified license;
- file license: `Open Data Commons Attribution License v1.0`;
- `set-a.tar.gz` displayed byte count: `6,632,372`; and
- set A is described as containing 4,000 records with outcomes available.

The inspection did **not** establish a raw page digest, raw archive digest,
complete allowlisted snapshot, or institutional applicability determination.
The official license itself warns that database contents can implicate rights
not covered by the database license, including privacy and data-protection
rights. Open access is therefore not treated as a self-executing project
governance approval.

No dataset archive, individual record, outcome file, restricted page, private
contact detail, or credential was opened or downloaded. No person or
institution was contacted. The underlying browser transport's exact request
count, response bytes, and timestamps are not claimed or sealed by this
package.

## 3. Why the observation closes no new field

F021 already contains the accepted official license-and-access record. The
fresh observation corroborates that existing field but adds no new field
delta. The six remaining PhysioNet fields have stricter definitions:

| Field | Required evidence | Why public documentation is insufficient |
|---|---|---|
| F019 | exact acquired allowlisted snapshot-version receipt | a displayed dataset version is not an acquired snapshot manifest |
| F020 | SHA-256 and byte count of the exact acquired raw snapshot, independently verified | no archive bytes were downloaded and no SHA-256 was published on the observed pages |
| F022 | authenticated applicable governance determination plus accountable-owner acceptance | open access and a license do not authenticate a project-specific clinical/institutional determination |
| F033 | content-addressed observation reference and acquisition-justification receipt | a data-description page is not the frozen observation-reference certificate |
| F034 | full-support component, proof, implementation certificate, and independent review bound to F033 | the source page proves no common-support construction |
| F058 | private, content-addressed complete patient-disjoint split manifest from the verified snapshot | no snapshot was acquired and no split was run |

F163, F166, and F167 are already closed as plans only. They are not approvals.
B02 therefore remains open on the six fields above plus actual admission, and
B09 remains open on externally authenticated determinations and accountable
acceptance.

## 4. Existing fail-closed implementation

The repository already contains the pure local implementation
`src/heterodiff/data/physionet_2012_admission_preflight.py`. This package binds
its exact 136,305 bytes at SHA-256
`bf5c12dcb5debe99533d00a813d7b522c42b588f5431803a8c2bac99b0f2bf07`
and its 67,299-byte test file at SHA-256
`25786cf1d2bc971c8b8f08c2aabc18fa192ed7b75fd67944486238fb83c8d57c`.
All 127 focused tests pass.

That implementation:

- separates synthetic qualification from structurally activated real-shaped
  receipts;
- revalidates exact nested receipt graphs rather than trusting dataclass
  labels or hashes supplied by a caller;
- binds snapshot, split, governance, support, duplicate-audit, F061, and
  admission evidence;
- rejects incomplete, aliased, mutated, underpowered, non-disjoint, excluded,
  retried, resplit, topped-up, duplicate-bearing, or nonzero-violation inputs;
- can return at most `ELIGIBLE_FOR_INDEPENDENT_ADMISSION`; and
- always records `domain_admitted=false` and requires a separate independent
  admission decision.

Correct structure is not authenticity. Synthetic digests and real-shaped test
objects are qualification inputs only and cannot satisfy any checklist item.

## 5. Exact next authority-and-receipt sequence

The machine record freezes these twelve steps in order:

1. `PHYS-E01-EXTERNAL-PRINCIPALS`: assign nine real, pairwise-distinct opaque
   principals and obtain nine externally authenticated role acceptances.
2. `PHYS-E02-DEFINITION-AND-CUSTODY-RECORDS`: authenticate selector, contact,
   approval, validator, conflict, escrow, key, and ACL records under the
   accepted two-domain external-intake contract.
3. `PHYS-A01-POPULATED-PRECONTACT-REVIEW`: populate, independently review, and
   admit the exact finite precontact instance.
4. `PHYS-A02-FRESH-ADMIN-AUTHORITY`: record fresh exact authority for the
   admitted administrative-contact roster before any such operation.
5. `PHYS-R01-ADMIN-AND-APPROVAL-RECEIPTS`: obtain authenticated source metadata,
   license/governance requirements, and all applicable approvals without a
   data download.
6. `PHYS-A03-DATA-ACCESS-INSTANCE`: separately populate, review, and admit the
   data-access instance, then record fresh exact data-access authority.
7. `PHYS-R02-SNAPSHOT`: acquire exactly one allowlisted open-access snapshot
   and bind version, bytes, raw SHA-256, schema, toolchain, and private custody.
8. `PHYS-R03-SUPPORT`: certify F033/F034 with the observation reference,
   acquisition justification, full-support component, proof, implementation,
   and independent review.
9. `PHYS-R04-RESOLVED-F061-REVIEW`: bind the observed natural-group total to the
   accepted 70/15/15 policy and obtain a distinct PhysioNet resolved-count
   review. The shared review does not approve observed counts.
10. `PHYS-R05-SPLIT-AND-DUPLICATE-AUDIT`: create and independently verify the
    complete patient-disjoint manifest and complete method-blind cross-split
    duplicate/near-duplicate audit.
11. `PHYS-R06-STRUCTURAL-PREFLIGHT`: run the accepted preflight with all 13
    training-only violation counts zero and all six receipt flags passing.
12. `PHYS-R07-INDEPENDENT-ADMISSION`: obtain a separate admission decision
    bound to the exact evidence aggregate.

Every step is currently unsatisfied and is marked `satisfied_by_this_package=false`.
Silence, a public webpage, a structurally valid JSON object, a hash without
authenticated source evidence, a local agent review, or a self-authored role
label cannot satisfy an external step.

## 6. F061 boundary

The currently accepted shared policy remains 70/15/15 Hamilton allocation,
minimum counts `(1,128,128)`, exact validation and test counts `128/128`, and
admissible natural-group totals `{852,853,854,855}`. Its accepted definition is
`6c7beda87ccf1b9b60b0787619fc637eeb3ab34d5f68e09608d46b4dcf11f946`;
the accepted shared review's raw SHA-256 is
`906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d`.

Those receipts freeze the policy only. A future observed PhysioNet group total
must still receive a distinct resolved-count review before any real split.

## 7. Machine record and validation boundary

The canonical machine record is
`research/fixtures/manuscript_v3_b02_physionet_public_documentation_gap_v1.json`.
Its semantic self-digest is
`1ea241dcfeddbdefe6eb390e128e41ddcc972c25c0850f0dcc8ced6d0689d12c`.
The read-only validator rejects duplicate JSON keys, noncanonical types,
changed public facts, reordered or promoted checklist rows, changed field
requirements, mutated bound implementation files, and any nonzero closure or
authority claim.

The package is a candidate until a separate independent review accepts its
exact bytes. Even after acceptance, its only permissible effect is recognition
of a documentation/gap-control artifact with zero field, blocker, operational,
Formal-Test, result, authority, data-access, or scientific delta.
