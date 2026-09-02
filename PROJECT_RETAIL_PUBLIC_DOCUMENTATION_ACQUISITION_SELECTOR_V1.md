# Retail public-documentation acquisition selector and external-readiness contract

**State:** `RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_FROZEN_NO_DATA_ACCESS`  
**Date:** 2026-09-02  
**Data downloaded, opened, parsed, or split:** no  
**Principal, approval, authority, or governance determination created:** no

## Outcome

This additive Wave-3 package converts the remaining Online Retail II public
metadata into one exact owner-independent acquisition-selector core, a
content-addressed future snapshot-version rule, an exact owner-bound wrapper
compatible with the accepted external-evidence intake contract, and a
twelve-obligation Retail external-readiness checklist. The source is pure and
performs no I/O.

The package does not fill a tracker field. It gives a future accountable owner
stable bytes to accept and gives a future custodian a single no-fallback
archive target whose acquired bytes must be independently rehashed before
F038/F039 can even become candidates for external review.

## Official public-documentation observations

The official UCI Online Retail II record currently identifies dataset `502`,
DOI `10.24432/C5CG6D`, creator Daqing Chen, citation year 2012, and CC BY 4.0.
It advertises 1,067,371 instances, missing values, the member
`online_retail_II.xlsx`, display size `43.5 MB`, exact member size 45,622,278
bytes, and an embedded `totalCompressedSize` of 45,622,418 bytes. It lists the
eight raw fields already frozen by the accepted Retail preflight. The exact
public targets are:

- metadata: <https://archive.ics.uci.edu/dataset/502/online+retail+ii>
- archive: <https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip>
- license: <https://creativecommons.org/licenses/by/4.0/legalcode>

These are semantic observations, not an archived page-byte receipt. A bounded
read-only HEAD check on 2026-09-02 returned `200 OK` for both UCI targets; the
archive response exposed no immutable revision, raw hash, or content length.
The project and synced-reference filename scans found no matching local
workbook, archive, or exact UCI page snapshot. No dataset bytes were requested
or stored by this package.

The UCI page does not expose an immutable dataset revision or raw archive
SHA-256. The DOI identifies the dataset, not a particular byte snapshot.
Therefore the package explicitly keeps F038 and F039 open.

## Exact selector and future version rule

The selector permits exactly one future target, the official archive URL
above, with no redirect, fallback, retry, authentication, alternate mirror, or
silent substitution. Before fresh exact authority its attempt budget is zero.
The only allowlisted archive member is `online_retail_II.xlsx`; extra members,
path traversal, symlinks, directories, size drift, or name drift are no-go.

After an authorized custodian has durably recorded intent, streamed the raw
archive into fresh private custody, recomputed the raw archive hash, recomputed
the one-member inventory, and obtained independent custody verification, the
pure source derives:

`UCI-502-C5CG6D-ARCHIVE-SHA256-{raw_archive_sha256}`.

That content-addressed value is the candidate F038 snapshot version and the
same recomputed digest is the candidate F039 raw snapshot hash. A pure-function
PASS is only structural. The private bytes, authenticated authority and owner
acceptance must still be replayed by the accepted intake/custody machinery and
accepted by a separate external reviewer. This package never closes F038 or
F039 itself.

## Owner-bound intake compatibility

The source constructs the exact Retail selector payload required by the
accepted B02/B03/B09 external-evidence intake v1. It requires a nonplaceholder
opaque accountable-owner principal ID and reproduces the intake contract's
domain-separated definition-record digest. Construction does not authenticate
that principal or close `retail_selector_record_sha256`; the future private
packet still needs the owner's externally authenticated acceptance and the
complete nine-principal evidence bundle.

## Exact external dependencies

The twelve closed-world obligations are:

1. owner-bound selector and acceptance;
2. fresh exact DATA authority and durable no-clobber intent;
3. content-addressed raw snapshot, version, byte count and inventory;
4. applicable authenticated governance/privacy determination;
5. complete schema, source-civil time, CustomerID and row-preservation receipt;
6. normalized code-matched observation reference for F053;
7. acquisition-justified positive/common-support proof, implementation,
   certificate and independent review for F054;
8. populated private customer-disjoint temporal split and accepted F061 replay;
9. observed temporal feasibility or terminal domain no-go;
10. complete exact/rule-bound near-duplicate leakage audit;
11. the thirteen-zero-count, six-receipt independent admission decision; and
12. applicable owner acceptance of the accepted F163/F167 plans and release
    boundary.

The readiness validator accepts only a wholly empty HOLD template or a wholly
populated exact roster. Partial population, placeholders, role drift, malformed
hashes, missing authentication, or missing independent verification fail
closed. Even a structurally complete roster reaches only private-custody replay
and external independent review; it creates no field or blocker authority.

## Exact nonclosure

The eligible tracker delta is zero fields and zero blockers. F038, F039, F041,
F053, F054, and F059 stay open; B03 and B09 stay open. F040 and F061 remain
closed only through their already accepted predecessor packages and are not
reclosed here. F163 and F167 remain accepted plans, not actual approvals or
owner acceptances. No Formal Test, training run, scientific result, release,
or submission state changes.

## Package

The candidate consists of:

- `PROJECT_RETAIL_PUBLIC_DOCUMENTATION_ACQUISITION_SELECTOR_V1.md`;
- `src/heterodiff/data/retail_public_documentation_acquisition_selector.py`;
- `research/fixtures/manuscript_v3_retail_public_documentation_acquisition_selector_v1.json`;
- `research/diagnostics/manuscript_v3_retail_public_documentation_acquisition_selector_v1.py`; and
- `tests/unit/test_manuscript_v3_retail_public_documentation_acquisition_selector_v1.py`.

The machine record binds the accepted governance, offline-precontact,
external-intake, and F061 machine/review lineage plus the human and pure source
bytes. The read-only validator and hostile tests are qualification files
outside semantic self-binding. No independent-review receipt is created by the
author.
