# Independent review — F105 exact two-domain CKS metric instance

**Review date:** 2026-09-01  
**Disposition:** `GO`  
**Severity count:** `P0=0`, `P1=0`, `P2=0`  
**Accepted state:** `F105_TWO_DOMAIN_CKS_EXACT_INSTANCE_FROZEN_PREOUTCOME`

## 1. Reviewed bytes

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human contract | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md` | 15,242 | `5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef` |
| Machine contract | `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | 23,899 | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| Read-only validator | `research/diagnostics/manuscript_v3_f105_two_domain_cks_metric_instance_v1.py` | 37,339 | `ca99e505669ca77d632e1cbf1dc5a6a3f5523edc71b7b8e90456b30975d25064` |
| Pure exact source | `src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py` | 25,342 | `567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881` |
| Hostile tests | `tests/unit/test_manuscript_v3_f105_two_domain_cks_metric_instance_v1.py` | 17,542 | `f86daa76c8e0492e614107c7f777a914da826356d71edf09d2a59ddcfbbc6a82` |

The independently recomputed machine semantic digest is
`14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52`.
The machine JSON is canonical ASCII, one-line, terminal-LF JSON. All five files
are regular mode `0644` files with link count one.

## 2. Independent lanes

### Mathematical and implementation red team

The reviewer independently checked the count-normalized embedding, empty
configuration convention, multiplicity separation, event and outer Gaussian
kernels, injectivity of both transforms, characteristicness, strict propriety,
formal score algebra, lower-is-better orientation, direct-minus-guide sign, and
the supported formal `2 <= R <= 128` domain.

Two findings were raised and repaired before acceptance:

1. the original CustomerID boundary accepted leading-zero aliases despite the
   canonical-decimal contract; the source now accepts exactly
   `[1-9][0-9]{0,4}`, the validator independently rejects `00001`, and hostile
   tests reject `01` and `00001`;
2. the original custody reader rejected leaf symlinks but did not pin every
   parent-directory component; the validator now uses component-wise
   `dir_fd` plus `O_NOFOLLOW` directory opens, and a parent-directory symlink
   hostile is rejected.

After the repairs, the reviewer reported no remaining mathematical, source,
resource-bound, custody, or closure defect and issued `GO`.

### Domain, governance, count, and custody red team

The reviewer independently checked the two public root-page observations,
field/source separation, PhysioNet descriptor and 37-variable roster, missing
sentinel, Weight dual role, Retail eight-field schema, cancellation semantics,
missingness, exact time horizon, absence of a published timezone, cap labels,
token/resource bounds, whole-domain no-go rules, F043-to-F060 customer-key
projection, F060 successor semantics, every open-field boundary, and the
172-field ledger arithmetic.

The review confirmed that source facts, agent-selected schema/resource choices,
and derived horizon values are distinguished; no snapshot, raw-byte, license,
governance, privacy, admission, data, runtime, or scientific fact is promoted.
The source-civil F060 successor removes the unsupported UTC/instant assertion,
leaves the predecessor bytes unchanged, preserves the deterministic gap-pair
algorithm, leaves F061 null, and changes no field count. The reviewer reported
no remaining P0, P1, or P2 finding and issued `GO`.

## 3. Qualification

The cache-disabled focused package suite passes `43/43` from both the project
root and an unrelated working directory. The combined cache-disabled candidate,
generic theorem/reference, PhysioNet route, Retail route, and F060 regression
suite passes `452/452`. The mathematical reviewer independently ran the
candidate plus generic theorem/reference set and obtained `277/277`. The domain
reviewer separately reran the package and bound predecessor validators. The
standalone validator returns the semantic digest above.

Qualification covers exact supplied synthetic witnesses and package behavior.
It does not open a dataset, test a real parser/snapshot, generate entropy,
train a model, evaluate an empirical score, establish conditional-i.i.d. draws,
or perform scientific execution.

## 4. Accepted closure and count transition

The accepted all-or-nothing PRE closure roster is exactly:

```text
F023 F024 F026 F027 F028 F029 F030 F031
F042 F043 F045 F046 F047 F048 F049 F050 F051
F105
```

All 18 fields were independently confirmed OPEN before this package. Acceptance
moves PRE from `140 open / 26 closed` to `122 open / 44 closed`; POST remains
`3 open / 3 closed`; total moves from `143 open / 29 closed` to
`125 open / 47 closed`. F060 remains closed under its additive V2 successor and
has zero count delta.

F025, F032--F041, F044, F052--F059, F061, and F109--F112 remain open. B01--B12,
including B02, B03, and B04, remain open. No Formal Test or result closes. The
exact Gate-A CKS checkbox remains open because the preliminary manuscript
display has not been replaced and production integration/code matching has not
been accepted. Domain admission, contact, authentication, download/data access,
runtime, training, science, claims, and submission remain absent or
unauthorized.

## 5. Review authority and lifecycle

This review accepts only the exact bytes in Section 1 and the exact closure in
Section 4. It authorizes the truthful additive ledger/timetable reconciliation
requested by the user. It does not authorize any external or scientific action.
Any later change to a reviewed byte, transform, cap, horizon, schema, score,
field roster, F060 successor, or nonclosure invalidates this receipt and
requires a new content-addressed package and fresh independent review.
