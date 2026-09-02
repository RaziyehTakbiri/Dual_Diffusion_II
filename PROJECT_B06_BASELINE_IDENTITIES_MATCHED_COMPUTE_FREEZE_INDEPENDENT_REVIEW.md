# Independent review — B06 baseline identities and matched-compute freeze

**Review date:** `2026-09-01`  
**Decision:** `GO`  
**P0 / P1 / P2 findings:** `0 / 0 / 0`  
**Accepted delta:** exactly `F062--F103` and blocker `B06`  
**B08:** `OPEN`  
**B12:** `OPEN`

## 1. Decision

I independently reopened the sealed B06 candidate, recomputed its raw and
semantic bindings, reconstructed the 42-field projection against the accepted
preregistration, replayed the matched-compute and parameter-count arithmetic,
inspected the local source release, checked the frozen upstream repositories
and license receipts, and ran the required hostile suites from both the
project root and an unrelated working directory.

The candidate is internally and externally consistent for its stated
pre-outcome scope. It may be registered as closing exactly the 42 PRE fields
`F062` through `F103` and the single execution blocker `B06`. The review does
not accept or imply hardware calibration, capacity, executable external
adapters, domain-scale runtime, training, inference, results, or submission.

## 2. Sealed candidate identities

The canonical machine record is 186,707 bytes with raw SHA-256
`b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21`.
Its independently recomputed domain-separated semantic digest is
`aa3ab6c8cb05287304da321f2d5b4892b94d4483860d830a3e724c339b2809bd`.

The canonical registry JSON is 136,284 bytes with ordinary SHA-256
`5d59670786d66fd4e5a49c7a5e5b11f9dc0a240de3a59b8615de4134bcc00910`.
Its independently recomputed `HETERODIFF-B06-FROZEN-REGISTRY-V1\0`
domain-separated digest is
`b246f1454065b086c88f80b1cfe662f9bcbe8fbca66078f7e4d02f9b518d5b64`.

### 2.1 Current-package raw bindings

| Path | Bytes | Raw SHA-256 |
|---|---:|---|
| `src/heterodiff/experiments/matched_total_compute.py` | 15,028 | `be31b346c67b7d0ce0b82a3ff784739bf3d825fd9b94108dc1f8ae808586f8a0` |
| `tests/unit/test_matched_total_compute.py` | 14,128 | `05babf456f9d71632dbac2b43d93a046754a9d1bcee81e09ff5ec40df616c8ad` |
| `src/heterodiff/experiments/two_domain_baseline_registry.py` | 47,098 | `d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1` |
| `tests/unit/test_two_domain_baseline_registry.py` | 43,371 | `8fcd1a41b141fdccc43ca11a817c097ff9c266cb56dd4da207134fbdb929c3f7` |
| `src/heterodiff/experiments/two_domain_baseline_adapter_contract.py` | 15,666 | `749f1616d259a9425616fb8e84ca5f7ef15788722bb3d03198f06b81c4fb79ff` |
| `tests/unit/test_two_domain_baseline_adapter_contract.py` | 11,979 | `7c7f707650d43a51947558761248e906897101e27342bb84e5789cd3aa5dd0f2` |
| `research/fixtures/b06_upstream_receipts/csdi_7f24a436_LICENSE` | 1,071 | `76f5d72acd2d179c72f9c8d7212cc2e6904c1a15908951d0959b9ea13d528ba9` |
| `research/fixtures/b06_upstream_receipts/editpp_3113d2ee_LICENSE` | 1,118 | `94f6472f9fafcc23e53bd3914638c94f3ab39671fbf1195b2d798b9bf8072198` |
| `PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md` | 41,198 | `6a10a546a70d43aa71cb878e72ba09c24be949cd932e1cdf5becdeb732fa816a` |
| `research/diagnostics/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py` | 27,756 | `668370f04fb66effd9a57a2e6f8614d72800d522729b4e64a3f881c890c3b60a` |
| `tests/unit/test_manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py` | 12,544 | `aedfaf00236e8c10a014c5e7934b2cdc3df8c434e989efe6dad38e4f874b27ef` |

The machine file is self-bound semantically rather than by an impossible
embedded raw self-hash. All 30 package/predecessor files were regular,
single-link `0644` files with terminal LF; no package member or predecessor was
a symlink.

### 2.2 Accepted predecessor bindings

All 18 predecessor sizes and raw hashes matched the sealed manifest:

| Path | Bytes | Raw SHA-256 |
|---|---:|---|
| `manuscript_v3/execution_preregistration.md` | 22,491 | `a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e` |
| `research/fixtures/manuscript_v3_execution_preregistration_v1.json` | 39,771 | `edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706` |
| `manuscript_v3/execution_preregistration_preexecution_closure_v2.md` | 14,938 | `fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d` |
| `research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json` | 24,571 | `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` |
| `PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md` | 10,754 | `33c9df737f45411861f2a60a9ed99220f61e4ac66461999ed0367c482b5dbe3d` |
| `research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json` | 24,004 | `be7a96ab4898e89cf0167fcce48204142143bf071a194b24d480091a6c60530a` |
| `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md` | 9,596 | `4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb` |
| `research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json` | 12,639 | `c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54` |
| `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md` | 10,230 | `7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402` |
| `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md` | 15,242 | `5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef` |
| `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | 23,899 | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md` | 5,932 | `368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3` |
| `PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md` | 17,299 | `bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721` |
| `research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json` | 20,936 | `2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1` |
| `PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md` | 3,270 | `ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64` |
| `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` | 15,756 | `e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c` |
| `research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json` | 17,729 | `340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c` |
| `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_INDEPENDENT_REVIEW.md` | 10,999 | `951efca8ae87a6aab80c6dbd9e07bb42769fcf0424eb544e6d90c4cb94cdffa3` |

The six declared predecessor semantic digests also matched exactly:
pre-execution closure `a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4`,
baseline draft `4cad447dca7896d45c424ee16594cddf3cd83e8497ed0cb3ec875ced03dd5840`,
F104 `ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b`,
F105 `14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52`,
theory/statistics `335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491`,
and governance `8d39354b7d6d119c593b7943ebf5b78828f6810c91195e4ac50b0f4424036313`.

## 3. Independent scientific and implementation checks

### Exact field projection and state delta

The accepted preregistration contains exactly 42 null fields at the literal
pointers assigned to `F062--F103`. Every one is currently `PRE`, owned by
`B06`, and `OPEN`; the pointer roster is unique and in exact ordinal order.
`F104` is already `CLOSED` and is not touched.

I independently counted the live ledger before registration: PRE is 76 open /
90 closed, POST is 1 open / 5 closed, total is 77 open / 95 closed, and
blockers are 8 open / 4 closed. Closing the exact 42 PRE rows and only B06
therefore yields PRE 34/132, POST 1/5, total 35/137, and blockers 7/5. The
current timetable contains 159 checkboxes, 51 checked and 108 open. The three
named B06, Gate-A baseline/license, and Solo-Block-6 boxes yield exactly
54 checked / 105 open; Gate A moves from 4/8 to 5/8.

### Local method identity, architecture, and compute

All eight local source files reproduced their declared raw hashes. Replaying
the domain-separated path/hash aggregation produced release
`023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564`.
The production `ConfigurationEnergyArchitecture._parameter_count` expression
reproduces 105,601 base plus 105,601 conditioner, total 211,202 for PhysioNet,
and 92,545 plus 92,545, total 185,090 for Retail. These values are exact for
the declared one-type typed-DeepSets architecture; no loaded-checkpoint or
domain-scale runtime claim is made.

For each domain, the two primary rows have identical parameter-count objects,
training event ceilings, inference event ceilings, F104 fairness bindings,
future B08 weight/ceiling identities, charging rules, and no-top-up rules.
The F104 exact calculator remains integer/rational only. Hardware identities,
calibration weights, scalar and hard-axis ceiling values, and capacity are
unpopulated.

All primary, control, family/domain, external, and tuning-grid config digests
were independently recomputed from canonical JSON and matched the registry.
All capability matrices contain the exact 11-axis roster and only `NATIVE`,
`AUTHOR_EXTENSION`, or `INAPPLICABLE_WITH_PROOF`; no `UNKNOWN` or
`UNSUPPORTED` value remains.

### Upstream identity, license, and capability audit

The read-only upstream clones were clean. `git` identified the exact CSDI
commit `7f24a436f08d98853a6b43d4f7f04e5a65ecdf27` and EditPP commit
`3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918` as commit objects under their
official GitHub remotes. Their `LICENSE` files byte-match the two package
receipts and are MIT licenses. The bound CSDI config, entrypoint,
requirements, and independently inspected PhysioNet loader hashes match the
frozen commit. The bound EditPP entrypoint, train/task/model configs, `pixi.lock`,
loader, batch, and conditional-evaluation sources likewise match its frozen
commit.

The CSDI loader confirms the documented lossy 35-variable, integer-hour,
last-value, 48-by-35 interface. The EditPP sources confirm one-dimensional
arrival-time sequences and native time-prefix forecasting rather than the
project's structured Retail marks and arbitrary full-horizon subset protocol.
Thus the package's native-versus-author-extension boundary is conservative
and does not represent either upstream as natively satisfying F105/F109.

The bounded-alternative audit also reproduced: Add-Thin has the stated MIT
receipt; no license file is present at the audited Point Set Diffusion or
NeuralBridge commits; DEFT has the stated NVIDIA noncommercial
research/evaluation license. The selection rule explicitly denies a universal
SOTA or empirical-superiority claim. Official sources checked included the
frozen CSDI and EditPP repositories, the EditPP/OpenReview paper record, the
PMLR Neural Guided Diffusion Bridges record, and the NeurIPS DEFT record.

## 4. Validation and hostile checks

From the project root:

```text
PYTHONPATH=src python3 research/diagnostics/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py
PASS — record aa3ab6c8cb05287304da321f2d5b4892b94d4483860d830a3e724c339b2809bd

PYTHONPATH=src pytest -q tests/unit/test_two_domain_baseline_registry.py tests/unit/test_two_domain_baseline_adapter_contract.py tests/unit/test_matched_total_compute.py tests/unit/test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py tests/unit/test_manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py
261 passed in 3.09s
```

From unrelated working directory `/private/tmp`:

```text
PYTHONPATH=<project>/src python3 <project>/research/diagnostics/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py
PASS — same semantic and registry digests

PYTHONPATH=<project>/src pytest -q <project>/tests/unit/test_manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py
24 passed in 0.86s
```

The hostile package suite rejects coherent field/count/blocker/SOTA/B08/B12/
science mutations; source, human-record, and license-receipt mutations;
noncanonical, duplicate-key, and floating-point JSON; and root symlink,
machine hard-link, and mode substitutions. The three production surfaces have
no data, model-runtime, network, entropy, training, inference, or metric
execution surface.

The unrelated repository-wide suite was not rerun for this review. Previously
known Python-3.9 dataclass collection failures and five unrelated
identity-placeholder tests remain transparently outside the exact 261-test B06
qualification. No evidence in the focused run ties either pre-existing issue
to B06.

## 5. Accepted scope and nonclaims

This GO accepts only the static, pre-outcome identity/configuration/capability
and prospective matched-compute freeze. It authorizes the later tracker
registration of exactly:

- fields `F062--F103` as `CLOSED`;
- blocker `B06` as `CLOSED`;
- the B06 blocker checkbox, Gate-A baseline/license checkbox, and Solo-Block-6
  baseline identity/config/matched-compute checkbox as checked; and
- the exact resulting counts recorded in Section 3.

It does **not** close B08 or B12. It does not accept hardware, runtime,
calibration weights, resource ceilings, capacity, external-package execution,
author-extension implementations, executable control/family adapters,
domain-scale primary runtime, data access, entropy, training, inference,
scientific results, formal tests, claim promotion, release, or submission.

**Final independent decision:** `GO`, with P0/P1/P2 `0/0/0`.
