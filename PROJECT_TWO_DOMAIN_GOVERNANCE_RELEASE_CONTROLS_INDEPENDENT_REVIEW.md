# Independent review — two-domain governance and release controls

**Review date:** `2026-09-01`  
**Disposition:** `GO`  
**Severity count:** `P0=0`, `P1=0`, `P2=0`  
**Accepted state:** `TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_FROZEN_PREEXECUTION`

## 1. Reviewed bytes

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human contract | `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` | 15,756 | `e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c` |
| Pure control source | `src/heterodiff/data/two_domain_governance_release_controls.py` | 9,720 | `8c5a1d74194a5cd1dbae1784360df2bffe392430bd48d74b1846fba6de802cef` |
| Machine contract | `research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json` | 17,729 | `340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c` |
| Read-only validator | `research/diagnostics/manuscript_v3_two_domain_governance_release_controls_v1.py` | 27,473 | `ff3074cd63a7ca97e656960ab65e5afcaa8d70322fd3e3e179a51700f9cf07bc` |
| Hostile tests | `tests/unit/test_manuscript_v3_two_domain_governance_release_controls_v1.py` | 16,157 | `73077ad44c316539b667f8c6c120a61f63039d6c01d847aefb72dfb11e9ccb24` |

The independently observed machine semantic digest is
`8d39354b7d6d119c593b7943ebf5b78828f6810c91195e4ac50b0f4424036313`.
The machine contract is canonical one-line ASCII JSON with one terminal LF and
no duplicate keys. Its semantic self-digest is domain-separated and excludes
only the self-digest field. All five reviewed files are regular mode `0644`
files with link count one and a terminal LF.

## 2. Accepted predecessor lineage

The validator's ten exact predecessor bindings were independently recomputed:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Accepted preregistration | `manuscript_v3/execution_preregistration.md` | 22,491 | `a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e` |
| Accepted preregistration machine | `research/fixtures/manuscript_v3_execution_preregistration_v1.json` | 39,771 | `edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706` |
| Accepted pre-execution closure | `manuscript_v3/execution_preregistration_preexecution_closure_v2.md` | 14,938 | `fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d` |
| Accepted pre-execution closure machine | `research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json` | 24,571 | `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` |
| Accepted F105 engine | `src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py` | 25,342 | `567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881` |
| Accepted F105 contract | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md` | 15,242 | `5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef` |
| Accepted F105 machine | `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | 23,899 | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| Accepted F105 validator | `research/diagnostics/manuscript_v3_f105_two_domain_cks_metric_instance_v1.py` | 37,339 | `ca99e505669ca77d632e1cbf1dc5a6a3f5523edc71b7b8e90456b30975d25064` |
| Accepted F105 tests | `tests/unit/test_manuscript_v3_f105_two_domain_cks_metric_instance_v1.py` | 17,542 | `f86daa76c8e0492e614107c7f777a914da826356d71edf09d2a59ddcfbbc6a82` |
| Accepted F105 independent review | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md` | 5,932 | `368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3` |

Every bound predecessor is a regular mode `0644`, link-count-one,
terminal-LF file. The hashes match the accepted preregistration, pre-execution
closure, F105 package, and F105 independent-review lineage. This package is an
additive successor and does not reinterpret or replace those bytes.

## 3. Independent semantic and security audit

The official PhysioNet project page was checked directly. It identifies
*Predicting Mortality of ICU Patients: The PhysioNet/Computing in Cardiology
Challenge 2012*, version `1.0.0`, published `2012-01-20`; says anyone may access
the files subject to the specified license; and names the file license as Open
Data Commons Attribution License v1.0. The project-specific license permits
use, sharing, and modification subject to attribution while warning that
individual contents can involve separate privacy, data-protection, and other
rights. The package truthfully records only observed page semantics and does
not claim page-byte custody, a local snapshot, a raw digest, or governance
approval.

The official UCI record was checked directly. It identifies Online Retail II as
dataset `502`, DOI `10.24432/C5CG6D`, file `online_retail_II.xlsx`, under
Creative Commons Attribution 4.0 International, and describes sharing and
adaptation for any purpose with appropriate credit. The page presents no
immutable file version or raw digest. The package therefore correctly leaves
the exact Retail snapshot/hash and applicable governance determination open.

The occurrence-private ordinal semantics preserve duplicate-valued and
simultaneous occurrences. Exact independent half-thinning assigns every
ordinal subset mass `2^-n`, including the empty-source convention, without
sampling or entropy in this package. The admission statistic is a strict,
ordered, method-blind training-only maximum over 13 exact nonnegative integer
components; admission requires all components zero and all six independently
verified receipts. Positive counts, missing receipts, malformed inputs,
exclusions, retries, resplits, top-ups, and post-outcome repair fail closed.

The release predicate accepts only a normalized relative-path manifest with
exact release classes, hashes, sensitivity flags, scan/review gates, and final
owner approval. A passing predicate says only
`RELEASE_ELIGIBLE_FOR_SEPARATE_OWNER_ACTION`; it neither releases nor supplies
legal, privacy, ethics, venue, or governance approval.

The custody reader requires an absolute canonical nonsymlink root, traverses
every ancestor through directory descriptors with `O_NOFOLLOW`, fingerprints
root/ancestors before and after the read, opens the leaf with `O_NOFOLLOW`,
requires a stable regular leaf, and then enforces mode `0644`, link count one,
and terminal LF for package and predecessor files. Hostile root symlink,
intermediate symlink, leaf hardlink, mode drift, predecessor drift, and source
mutation cases are rejected.

The source is captured once during validation. The validator parses those
captured bytes as inert syntax and applies `ast.literal_eval` only to five
required unique top-level assignments. It never imports, compiles, or executes
the bound source. Injected default-argument effects do not run; duplicate,
missing, or nonliteral required assignments fail closed.

No overclaim was found. The machine record fixes every expected field value,
package binding, predecessor binding, remaining-open requirement, blocker
status, and nonclaim; recomputing the semantic self-digest after an overclaim
does not make the record valid.

Official references checked on the review date:

- <https://physionet.org/content/challenge-2012/1.0.0/>
- <https://physionet.org/content/challenge-2012/view-license/1.0.0/>
- <https://archive.ics.uci.edu/dataset/502/online+retail+ii>

## 4. Qualification

The standalone validator passed from both the project root and unrelated
working directory `/private/tmp`, returning the semantic digest in Section 1,
the exact 17-field roster, `15` PRE closures, `2` POST closures, and zero
blocker closures.

The focused hostile package suite passed `40/40` from both the project root and
`/private/tmp`. The five-suite package-and-lineage regression passed `183/183`
from both locations using absolute test paths in the unrelated working
directory. That regression comprised:

- `tests/unit/test_manuscript_v3_two_domain_governance_release_controls_v1.py`;
- `tests/unit/test_manuscript_v3_execution_preregistration_preexecution_closure_v2.py`;
- `tests/unit/test_manuscript_v3_f105_two_domain_cks_metric_instance_v1.py`;
- `tests/unit/test_two_domain_count_normalized_event_cks_production.py`; and
- `tests/unit/test_manuscript_v3_submission_readiness.py`.

For transparency, a deliberately broader probe that additionally included
the unrelated legacy `tests/unit/test_manuscript_v3_scientific_route.py` suite
returned `192 passed / 3 failed`; isolation returned `9 passed / 3 failed` in
that legacy suite. The three failures are existing numerical/fixture
compatibility mismatches in the mixed-path-KL, cap-defect, and finite-A1
scientific-route checks. None imports, binds, exercises, or is modified by this
governance package, and all package-and-lineage suites remain green. They are
therefore recorded as an out-of-scope ambient observation, not a finding
against these reviewed bytes and not authority to edit any theory file.

Qualification performed no network acquisition of dataset files, source-data
open/parse/split, authentication, contact, scientific entropy, training,
result inspection, release, scan, audit report, clean-room reproduction, or
tracker mutation.

## 5. Accepted bounded closure

The accepted all-or-nothing closure roster is exactly:

```text
PRE:  F021 F025 F032 F035 F036 F037
      F040 F044 F052 F055 F056 F057
      F163 F166 F167
POST: F164 F165
```

All 17 fields were confirmed OPEN in the accepted predecessor ledger view, and
the PRE/POST classification matches the ledger. The independently recomputed
additive transition is exact:

```text
PRE:   122 open / 44 closed  -15/+15 -> 107 open / 59 closed
POST:    3 open /  3 closed   -2/+2  ->   1 open /  5 closed
TOTAL: 125 open / 47 closed  -17/+17 -> 108 open / 64 closed
BLOCKERS CLOSED: 0
```

B02, B03, B09, B10, and B11 remain open with the package's stated missing
snapshots/hashes, governance determinations, populated splits and admission,
support certificates, owner acceptance, final release package/scans/decision,
independent identities/reports/dispositions, and observed clean-room
reproduction still absent. No other field, blocker, Formal Test, result,
runtime/data/science/claim/submission gate, or tracker entry closes.

## 6. Review authority and lifecycle

This review accepts only the exact five candidate byte strings in Section 1,
their exact ten predecessor bindings in Section 2, and the exact bounded
17-field delta in Section 5. It authorizes only truthful additive registration
of that delta after acceptance. It does not authorize acquisition, contact,
approval, admission, training, scientific execution, result inspection,
release, audit, clean-room reproduction, submission, or any blocker closure.

Any later change to a reviewed candidate byte, predecessor binding, official
source observation, field roster, count transition, control predicate, custody
rule, or nonclaim invalidates this receipt and requires a new content-addressed
package and fresh independent review.
