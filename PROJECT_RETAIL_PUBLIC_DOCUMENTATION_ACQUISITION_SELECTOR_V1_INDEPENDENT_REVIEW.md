# Independent review — Retail public-documentation acquisition selector V1

**Reviewed:** 2026-09-02  
**Disposition:** `GO_RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_NO_FIELD_CLOSURE`  
**Field closures authorized:** none  
**Blocker closures authorized:** none  
**Timetable closures authorized:** none  
**Findings:** P0 `0`; P1 `0`; P2 `0`

## 1. Decision

I independently accept this package as a pure, owner-independent Retail
acquisition-selector and external-readiness contract. It freezes one exact
official archive target, a content-addressed future version rule, the accepted
external-intake wrapper, and twelve closed-world obligations without accessing
dataset bytes or manufacturing authority, custody, governance, split, or
admission evidence.

This is deliberately a zero-delta acceptance. F038, F039, F041, F053, F054,
and F059 remain open; B03 and B09 remain open. F040, F061, F163, and F167 keep
only their already accepted predecessor status and are not reclosed. No Formal
Test, result slot, timetable item, data-access state, scientific operation,
release, or submission state changes.

## 2. Exact candidate custody

The five files were regular, single-link `0644` files with these exact sizes
and raw SHA-256 digests immediately before the review was written:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_RETAIL_PUBLIC_DOCUMENTATION_ACQUISITION_SELECTOR_V1.md` | 6,569 | `cd920ff38f6478b91d3e763206abbe175fe407335edbc09d07dcc062dc51db0f` |
| `src/heterodiff/data/retail_public_documentation_acquisition_selector.py` | 17,279 | `225d82fd1449eeb709674e4395f5b1e683d895621aef30344b0f877d5a39be4f` |
| `research/fixtures/manuscript_v3_retail_public_documentation_acquisition_selector_v1.json` | 8,910 | `6cf978a194899778c6bf1c2de4eb535a91f6ca490a5cbee8328d5558ef1f782e` |
| `research/diagnostics/manuscript_v3_retail_public_documentation_acquisition_selector_v1.py` | 15,589 | `fe966845df438f9ece95d4670f93f1873011a33d2af08db1df96a8429e537473` |
| `tests/unit/test_manuscript_v3_retail_public_documentation_acquisition_selector_v1.py` | 13,290 | `55f9ec7e194d34f44a3c6efdd3b2753d828cfb34cc192a411c8763346e7ca3e5` |

The machine fixture is ASCII canonical JSON with one terminal LF. Independent
domain-separated recomputation produced:

- machine semantic SHA-256
  `2a87d9584995d9a8dc195595389db68bd1053d8e46df6490682a5891eabe9505`;
- selector-core SHA-256
  `ad48db3ec83d55e9da9f8d7e02c85b8e094d237e87b10f34f72d4575d4310244`.

Both values exactly match the machine record. The embedded human and source
bindings also match the raw bytes above.

## 3. Predecessor lineage

I independently reread and rehashed all eight accepted predecessor artifacts.
Every size and digest matched:

| Predecessor | Bytes | SHA-256 |
|---|---:|---|
| Two-domain governance machine | 17,729 | `340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c` |
| Two-domain governance review | 10,999 | `951efca8ae87a6aab80c6dbd9e07bb42769fcf0424eb544e6d90c4cb94cdffa3` |
| Offline-precontact activation machine | 22,137 | `d74333a2c381daa953803e9346efb0ab63d6744265bfa8e7e260b1d1932fc0ee` |
| Offline-precontact activation review | 10,196 | `a1baf2b04740ac38540a4008dcb09042f8c92fa978c51fe22ac54cb30c81f0d0` |
| External-evidence intake machine | 11,920 | `af4d46e652d24d71382a746e3a043491c2f978275098e266e6f77f4286906a9f` |
| External-evidence intake review | 7,792 | `f69e29bebcee4f16eea354e2810085de8e0df4c07570e1aec378e96c70132101` |
| F061 allocation machine | 15,037 | `4a6414b494328a7f7cd4030718af960764bb2ce1946fb7de093985983e725d32` |
| F061 allocation review | 6,841 | `053de959f3fffabf0da21a4c9e997b96e170f1fbc4b9295d71fef8e8347835eb` |

The owner-bound Retail selector digest independently agrees with the accepted
intake codec's domain-separated `RETAIL_SELECTOR_RECORD` definition digest.
Construction requires a nonplaceholder opaque owner identifier but explicitly
does not authenticate it.

## 4. Official UCI fact audit

I independently inspected the official UCI Online Retail II record at
`https://archive.ics.uci.edu/dataset/502/online+retail+ii`. The current official
page confirms dataset 502, Online Retail II, donation display 9/20/2019,
1,067,371 instances, missing values, the 2009--2011 source period, eight
described raw fields, creator Daqing Chen, citation year 2012, DOI
`10.24432/C5CG6D`, CC BY 4.0, member `online_retail_II.xlsx`, and display size
43.5 MB.

The page's embedded official metadata independently exposes member size
45,622,278 bytes and `totalCompressedSize` 45,622,418 bytes. A bounded
read-only HEAD request returned `200 OK` for the metadata page and the exact
archive target
`https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip`.
The archive HEAD exposed neither a content length nor an immutable revision or
raw SHA-256. No archive body or workbook byte was requested by this review.

The package therefore draws the correct boundary: the DOI and public metadata
identify the dataset and a current target, but do not authenticate a particular
archive byte snapshot. F038 and F039 cannot close until private acquisition,
rehashing, inventory reconstruction, custody verification, and separate
external acceptance occur.

## 5. Fail-closed semantic audit

The selector admits exactly the official archive locator with zero redirects,
fallbacks, and retries and a zero attempt budget before fresh authority. It
forbids authentication, substitution, silent update, unexpected members, and
member-size drift. The future version is derived only as
`UCI-502-C5CG6D-ARCHIVE-SHA256-{raw_archive_sha256}`.

Independent hostile probes confirmed refusal of an alternate mirror, a
redirect, an extra receipt key, Boolean-as-integer status, and a receipt that
claims the dataset was opened. The focused suite additionally rejects member
name/size drift, archive-size drift, malformed hashes, missing recomputation,
missing custody verification, placeholders, role drift, missing external
authentication, missing independent verification, and partial checklist
population.

The exact twelve obligation IDs are unique and the current readiness roster is
wholly empty. The empty roster returns
`HOLD_REAL_RETAIL_EVIDENCE_INCOMPLETE`. Even a structurally complete synthetic
roster returns only
`STRUCTURALLY_COMPLETE_INPUT_REQUIRES_PRIVATE_CUSTODY_REPLAY_AND_EXTERNAL_INDEPENDENT_REVIEW`
with both field and blocker closure authorization false. In particular:

- the license is not treated as an applicable governance/privacy approval;
- a selector owner ID is not treated as authenticated owner acceptance;
- syntax-only hashes are not treated as replayed private custody;
- the F061 policy is not treated as a populated Retail split;
- temporal feasibility, common support, duplicate leakage, and the thirteen-
  zero admission decision remain externally evidenced obligations.

The source is pure: it imports only standard hashing, JSON, regular-expression,
and typing facilities; it exposes no filesystem, network, subprocess, entropy,
dataset, parsing, training, inference, or tracker-writing effect surface.

## 6. Validation results

The read-only validator passed from the project root and from an unrelated
working directory with the identical decision
`PASS_RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_NO_FIELD_CLOSURE`, twelve readiness
obligations, empty eligible field/blocker rosters, and tracker/ledger authority
false.

All requested tests were run with Python bytecode disabled, the source path
explicit, and the pytest cache provider disabled:

| Surface | Result |
|---|---:|
| Candidate focused suite | 38/38 passed |
| Exact bounded candidate/predecessor compatibility roster | 413/413 passed |

The 413-test roster covered this candidate plus the accepted external-intake,
offline-precontact activation, Online Retail II admission preflight,
two-domain governance controls, and F061 allocation packages.

## 7. Exact closure eligibility

The active ledger agrees with the candidate boundary: F038/F039/F041/F053/
F054/F059 and B03/B09 are open; F040/F061/F163/F167 are prior accepted records
or plans only. None of the missing real evidence was created here.

The exact eligible project delta is therefore empty:

- eligible fields: `[]`;
- eligible blockers: `[]`;
- timetable tasks: none;
- Formal Tests and results: zero;
- tracker or evidence-ledger edit authority: false.

No P0, P1, or P2 defect was found within this narrow selector/readiness claim.
A future closing package must begin with fresh exact authority and accountable
owner/custodian identities, then acquire and independently replay the private
snapshot and complete the governance, support, split, feasibility, leakage,
admission, and owner-acceptance obligations. This review supplies none of
those external facts.
