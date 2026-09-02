# B06 baseline identities and matched-compute freeze — DRAFT candidate

**Reported project date:** `2026-09-01`  
**Document state:** `DRAFT_CANDIDATE_PENDING_INDEPENDENT_REVIEW`  
**Candidate scope:** `F062--F103` and blocker `B06` only  
**Closure claimed by this document:** none  
**Tracker or evidence-ledger edit made here:** none  
**B08:** `OPEN`  
**B12:** `OPEN`

## 1. Decision and review boundary

This record presents the exact, content-addressed candidate values for all 42
pre-execution B06 fields, F062 through F103. It also records the accepted F104
matched-total-compute contract, the frozen local and upstream identities, the
bounded external-baseline selection audit, and the remaining runtime and
resource gaps.

The registry bytes are frozen as an input to this candidate, but this document
does **not** independently accept those bytes and does **not** close B06 or any
field. B06 and F062--F103 may be registered as closed only if a separate
read-only review accepts the complete content-addressed package with no
material finding. A later authorized integration must then edit the evidence
ledger and timetable; this construction does neither.

The candidate delta is all-or-nothing: exactly F062--F103, 42 pre-execution
fields, and B06. If independently accepted and later registered, the projected
count transition is 76 open / 90 closed to 34 open / 132 closed for
pre-execution fields, while post-execution remains 1 open / 5 closed. The
projected blocker transition is 8 open / 4 closed to 7 open / 5 closed, with
only B06 changing. Until those two later acts occur, these are projections,
not current tracker state.

## 2. Exact byte and semantic bindings

The authoritative registry is the in-memory `FROZEN_REGISTRY` produced by
`src/heterodiff/experiments/two_domain_baseline_registry.py`. Its canonical
ASCII JSON is `json.dumps(value, sort_keys=True, separators=(",", ":"),
ensure_ascii=True).encode("ascii")`.

| Evidence | Bytes or scope | SHA-256 |
|---|---:|---|
| B06 registry source | frozen file | `d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1` |
| Canonical registry JSON, ordinary SHA-256 | 136,284 bytes | `5d59670786d66fd4e5a49c7a5e5b11f9dc0a240de3a59b8615de4134bcc00910` |
| Canonical registry JSON, domain `HETERODIFF-B06-FROZEN-REGISTRY-V1\0` | semantic binding | `b246f1454065b086c88f80b1cfe662f9bcbe8fbca66078f7e4d02f9b518d5b64` |
| Local method source-release aggregate | eight files, domain-separated | `023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564` |
| Registry hostile tests | frozen file | `8fcd1a41b141fdccc43ca11a817c097ff9c266cb56dd4da207134fbdb929c3f7` |
| F104 production compute contract | frozen file | `be31b346c67b7d0ce0b82a3ff784739bf3d825fd9b94108dc1f8ae808586f8a0` |
| F104 production tests | frozen file | `05babf456f9d71632dbac2b43d93a046754a9d1bcee81e09ff5ec40df616c8ad` |
| B06-to-B12 adapter contract | frozen file | `749f1616d259a9425616fb8e84ca5f7ef15788722bb3d03198f06b81c4fb79ff` |
| Adapter-contract tests | frozen file | `7c7f707650d43a51947558761248e906897101e27342bb84e5789cd3aa5dd0f2` |
| Retrieved CSDI `LICENSE` receipt | 1,071 bytes | `76f5d72acd2d179c72f9c8d7212cc2e6904c1a15908951d0959b9ea13d528ba9` |
| Retrieved EditPP `LICENSE` receipt | 1,118 bytes | `94f6472f9fafcc23e53bd3914638c94f3ab39671fbf1195b2d798b9bf8072198` |

The ordinary canonical-registry SHA-256 and the domain-separated registry
binding are deliberately distinct. Neither is the later package-record
self-digest.

### 2.1 Accepted predecessor raw digests

| Role | Path | Raw SHA-256 |
|---|---|---|
| Accepted preregistration | `manuscript_v3/execution_preregistration.md` | `a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e` |
| Preregistration machine | `research/fixtures/manuscript_v3_execution_preregistration_v1.json` | `edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706` |
| Pre-execution closure | `manuscript_v3/execution_preregistration_preexecution_closure_v2.md` | `fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d` |
| Pre-execution closure machine | `research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json` | `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` |
| Baseline/compute draft | `PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md` | `33c9df737f45411861f2a60a9ed99220f61e4ac66461999ed0367c482b5dbe3d` |
| Baseline/compute draft machine | `research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json` | `be7a96ab4898e89cf0167fcce48204142143bf071a194b24d480091a6c60530a` |
| Accepted F104 record | `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md` | `4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb` |
| Accepted F104 machine | `research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json` | `c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54` |
| Accepted F104 review | `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md` | `7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402` |
| Accepted F105 record | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md` | `5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef` |
| Accepted F105 machine | `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| Accepted F105 review | `PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md` | `368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3` |
| Theory/statistics closure | `PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md` | `bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721` |
| Theory/statistics machine | `research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json` | `2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1` |
| Theory/statistics review | `PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md` | `ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64` |
| Governance/release controls | `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` | `e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c` |
| Governance machine | `research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json` | `340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c` |
| Governance review | `PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_INDEPENDENT_REVIEW.md` | `951efca8ae87a6aab80c6dbd9e07bb42769fcf0424eb544e6d90c4cb94cdffa3` |

The corresponding accepted machine semantic digests are, respectively where
applicable: pre-execution closure `a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4`,
baseline draft `4cad447dca7896d45c424ee16594cddf3cd83e8497ed0cb3ec875ced03dd5840`,
F104 `ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b`,
F105 `14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52`,
theory/statistics `335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491`,
and governance `8d39354b7d6d119c593b7943ebf5b78828f6810c91195e4ac50b0f4424036313`.

## 3. Exact local identities and primary configurations

Both primary rows use repository
`content-addressed:workspace/heterodiff/b06-local-deepsets-method-source-release-v1`
and release
`sha256:023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564`.
The release is the domain-separated aggregate of these exact files:

| Source path | Raw SHA-256 |
|---|---|
| `src/heterodiff/theory/association_operational_guide.py` | `9540a3bce5e865a2f3d35192f55ba72a9574243d959f404e5c500f27c3919d7f` |
| `src/heterodiff/theory/association_preconditioner.py` | `29e8a37fa1b74a37fc84d5208793e00e9b19674d6988bcfad46ac50613b1148c` |
| `src/heterodiff/theory/association_totalized_jump_guide.py` | `6b519b59994e763900c3d17fee6d44e8ec793e09db5ecffaffd1e47374fc7dd4` |
| `src/heterodiff/models/configuration_energy_torch.py` | `355e81ffba2eb2a7cf314f685ac9ea89fc7af6c61e4908a935b6032245879815` |
| `src/heterodiff/models/configuration_residual_torch.py` | `3afc4534f09f2cf41e3a737322c44112620fb9055aa51378c3c326c9c4a2293b` |
| `src/heterodiff/models/configuration_totalized_jump_potential_composer_torch.py` | `bbb31fc7e48c2d18a8ae7b196f20639ec56d0e8089a210222b437c6a8bb78076` |
| `src/heterodiff/models/configuration_totalized_jump_residual_torch.py` | `285d320f2a462954db54bd70cafff9266b4e31baf45e1d1276fdf3497b17cfff` |
| `src/heterodiff/processes/plugin_bridge_sampler.py` | `f6d7357f193651416b68cca9f3365855f520c5a7c2eb876114fc9e286627abc2` |

This is an internal content identity, not a public repository or public license
grant. The registry explicitly sets `public_license_grant_claimed=false` and
`scope=INTERNAL_RESEARCH_SOURCE_IDENTITY_ONLY`.

For every config digest in this record,
`config_sha256(v)=SHA256("HETERODIFF-B06-CONFIG-V1\0" || canonical_json(v))`.
The primary config hashes are:

| Role and method ID | Exact config SHA-256 |
|---|---|
| Primary method, `association-aware-guide-plus-residual` | `c44af50b915d024cb6019ee82a2998410afd3401fdb84c5313a84bc98fa543b1` |
| Primary comparator, `unified-direct-conditioner` | `f5c87a6c66defe9e1e8bb12e9578bc9317892af06dce0b88a5b1b81933b742a5` |

Each domain config uses `HASHED_TYPED_DEEPSETS_ENERGY_V1` with source class
`heterodiff.models.configuration_energy_torch:BoundedConfigurationEnergy`,
one F105 exact-vector type per domain, multiplicity-preserving segment-sum
pooling, and 256 reverse steps. Event, context, embedding, and readout hidden
widths are 128; context dimension is 64. PhysioNet has event dimension 112 and
cap 131,072; Retail has event dimension 10 and cap 1,067,371.

The primary method uses
`ANALYTIC_ASSOCIATION_GUIDE_PLUS_ONE_LEARNED_RESIDUAL` and source class
`heterodiff.models.configuration_residual_torch:CertifiedConditionalResidualCheckpoint`.
The comparator uses `UNIFIED_DIRECT_ONE_LEARNED_CONDITIONER` and source class
`heterodiff.models.configuration_energy_torch:CertifiedConfigurationEnergyCheckpoint`.
Each has exactly one conditional module. Both record
`FROZEN_64_DIMENSION_INTERFACE_B12_IMPLEMENTATION_REQUIRED` for the context
encoder, disallow test-based selection and post-test changes, and use the same
base release.

### 3.1 Exact parameter-count object `P`

`P` is the exact value of both F065 and F071:

```json
{"online-retail-ii":{"frozen_unconditional_base":92545,"total":185090,"trainable_conditioner":92545},"physionet-challenge-2012":{"frozen_unconditional_base":105601,"total":211202,"trainable_conditioner":105601}}
```

The procedure is
`CONFIGURATION_ENERGY_ARCHITECTURE_PARAMETER_COUNT_EXACT_INTEGER_V1`.
The conditional module is counted by the same typed-DeepSets architecture as
the frozen base; the total is their exact sum. This is an architectural count,
not a loaded-checkpoint or runtime receipt.

## 4. Exact event-count budgets

The ordered F104 phases are `PILOT`, `TUNING`, `FINAL_TRAINING`, and
`CONFIRMATORY_INFERENCE`. The ordered resource events are:

1. `BASE_FORWARD`;
2. `BASE_BACKWARD`;
3. `CONDITIONER_FORWARD`;
4. `CONDITIONER_BACKWARD`;
5. `GUIDE_EVALUATION`;
6. `RESAMPLING_STEP`;
7. `ODE_OR_SDE_STEP`;
8. `DATA_ADAPTER_RECORD`;
9. `METRIC_DRAW_EVALUATION`; and
10. `OTHER_DECLARED_OPERATION`.

The following table completely defines the exact ten-key count vectors used
below; blank shorthand is not used, and every omitted phase reference means
the explicit `Z` row.

| Vector | BASE_FORWARD | BASE_BACKWARD | CONDITIONER_FORWARD | CONDITIONER_BACKWARD | GUIDE_EVALUATION | RESAMPLING_STEP | ODE_OR_SDE_STEP | DATA_ADAPTER_RECORD | METRIC_DRAW_EVALUATION | OTHER_DECLARED_OPERATION |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Z` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `T` | 8,192 | 0 | 8,192 | 8,192 | 8,192 | 0 | 32,768 | 131,072 | 1,024 | 0 |
| `F` | 1,048,576 | 0 | 1,048,576 | 1,048,576 | 1,048,576 | 0 | 4,194,304 | 16,777,216 | 0 | 0 |
| `I_PHYS` | 536,870,912 | 0 | 536,870,912 | 0 | 536,870,912 | 0 | 536,870,912 | 274,877,906,944 | 134,217,728 | 0 |
| `I_RETAIL` | 536,870,912 | 0 | 536,870,912 | 0 | 536,870,912 | 0 | 536,870,912 | 2,238,439,227,392 | 134,217,728 | 0 |

For domain `d`, `TRAIN[d]` is the exact object with:

- `budget_id`: `B06-PRIMARY-TRAINING-{UPPERCASE_DOMAIN_ID}-V1`;
- `formula_id`: `EXACT_WEIGHTED_RESOURCE_LEDGER_V1`;
- `scope`: `PER_METHOD_PER_DOMAIN_COMPLETE_256_SEED_ROSTER`;
- `phase_event_count_ceilings`: `PILOT=Z`, `TUNING=T`,
  `FINAL_TRAINING=F`, `CONFIRMATORY_INFERENCE=Z`;
- `prospective_primary_pair_equality_required=true`;
- `failed_attempts_and_author_extensions_charged=true`;
- `unused_transfer_or_postresult_topup_permitted=false`; and
- `hardware_weights_and_capacity_owned_by_B08=true`.

The uppercase domain IDs are exactly `PHYSIONET-CHALLENGE-2012` and
`ONLINE-RETAIL-II`. `TRAIN_BY_DOMAIN` is the exact two-key object mapping each
lowercase domain ID to its `TRAIN[d]`. It is the value of both F066 and F072.

For domain `d`, `INFER[d]` is the exact object with:

- `budget_id`: `B06-PRIMARY-INFERENCE-{UPPERCASE_DOMAIN_ID}-V1`;
- `formula_id`: `EXACT_WEIGHTED_RESOURCE_LEDGER_V1`;
- `scope`: `PER_METHOD_PER_DOMAIN_COMPLETE_CONFIRMATORY_ROSTER`;
- `phase_event_count_ceilings`: `PILOT=Z`, `TUNING=Z`,
  `FINAL_TRAINING=Z`, and `CONFIRMATORY_INFERENCE=I_PHYS` for PhysioNet or
  `I_RETAIL` for Retail;
- the same four equality, charging, no-top-up, and B08 boolean values as
  `TRAIN[d]`.

`INFER_BY_DOMAIN` is the exact two-key object mapping each lowercase domain ID
to `INFER[d]`. It is the value of both F067 and F073. These ceilings derive
from 256 training seeds, 128 groups per domain, one conditioning case per
group, 64 addressed draws per case, and 256 reverse steps per draw.

### 4.1 F104 matched-total-compute contract

The accepted formula is

`C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]`.

Counts are exact nonnegative built-in integers, and calibration weights are
future strictly positive exact integers or `fractions.Fraction` values.
Booleans, floats, subclasses, negative counts, nonpositive weights,
missing/extra or reordered cells, and over-bound rational components fail
closed. Input components are limited to 4,096 bits and accumulated components
to 8,192 bits.

Within a domain, the primary pair has identical training and inference event
ceilings and identical prospective references to the base checkpoint, F134
group roster, F135 case roster, F109 R64 draw roster, precision policy, F105
metric workload, future B08 weight record, future scalar ceiling, and all eight
future hard-axis ceilings. Failed attempts, extensions, and unique
preprocessing are charged; allocation transfer and post-result top-up are
forbidden. Realized-resource equality is not claimed.

The eight separate hard axes are wall time, accelerator time, peak device
memory, peak host memory, model-evaluation count, persistent bytes, failure
count, and parameter count. Every corresponding value-assignment flag remains
false, as do the hardware identity, runtime identity, scalar ceiling, and
capacity-reservation flags. Therefore the event-count budgets are prospective
method budgets, not B08 calibration or capacity evidence.

## 5. Exact control values

All four implementation fields have the exact value
`B06_STATIC_CONTROL_CONFIGURATION_CONTRACT::heterodiff.experiments.two_domain_baseline_registry:validate_control_configuration::B12_RUNTIME_REQUIRED`.

Each control config is the exact object formed from schema
`HETERODIFF_B06_CONTROL_CONFIG_V1`, its control ID, that implementation string,
both domain IDs, the common local release, the exact mode below,
`training_compute_budget_by_domain=TRAIN_BY_DOMAIN`,
`inference_compute_budget_by_domain=INFER_BY_DOMAIN`,
`compute_is_charged_to_control=true`,
`may_discharge_literature_family_without_proof=false`,
`b12_runtime_qualification_required=true`,
`current_runtime_qualification_claimed=false`, and
`post_test_change_permitted=false`.

| Ordinal | Control ID | Active components | Removed components | Exact config SHA-256 |
|---:|---|---|---|---|
| 0 | `analytic-guide-only-residual-removed` | `ANALYTIC_GUIDE`, `FROZEN_BASE` | `LEARNED_RESIDUAL` | `37d5178c836ced493dec1fe49b08ab042e738c5c24edc5867830528154b51ae4` |
| 1 | `direct-or-residual-only-analytic-guide-removed` | `LEARNED_RESIDUAL`, `FROZEN_BASE` | `ANALYTIC_GUIDE` | `e175d468fb0df523c9adb2f6aa2e6f4b843b872e54234f63a1f41465f8bef212` |
| 2 | `association-destroyed-or-factorized-eventwise` | `FACTORIZED_EVENTWISE_CONDITIONER`, `FROZEN_BASE` | `CROSS_EVENT_ASSOCIATION_FEATURES` | `a2f91e01e1bdc6854fef6a045df802eaf4a5e60ef124c4303b0694d40ed36008` |
| 3 | `unconditional-base-sanity-reference` | `FROZEN_BASE` | `ALL_CONDITIONERS_AND_GUIDES` | `7ecfb6dd842a781d70ac147e374a501f819c8f61cd20f38442526079fb607032` |

These are static configuration contracts. They do not claim executable
control runners or B12 qualification.

## 6. Exact literature-family values

The exact source interface for every family/domain implementation is
`heterodiff.experiments.two_domain_baseline_adapter_contract:registry_adapter_declaration`.
Every implementation object contains exactly: `implementation_id`,
`source_interface`, `config_sha256`, `capability_matrix`,
`training_compute_budget_id`, `inference_compute_budget_id`, and
`b12_runtime_qualification_required=true`.

### 6.1 Capability matrices

The following table completely defines the capability matrix for each family.
`AE` means the exact string `AUTHOR_EXTENSION`; `N` means `NATIVE`; and `IP`
means `INAPPLICABLE_WITH_PROOF`.

| Exact axis | NGDB | DEFT | same-base SMC/Feynman–Kac | point/edit generator |
|---|---|---|---|---|
| `VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION` | AE | AE | AE | AE |
| `DOMAIN_PHYSICAL_TIME` | AE | AE | AE | N |
| `SIMULTANEOUS_EVENTS_AND_MULTIPLICITY` | AE | AE | AE | AE |
| `TYPED_EVENTS_AND_CONTINUOUS_MARKS` | AE | AE | AE | AE |
| `MISSING_OR_PARTIALLY_OBSERVED_MARKS` | AE | AE | AE | AE |
| `UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY` | AE | AE | AE | AE |
| `HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS` | AE | AE | AE | AE |
| `CONDITIONAL_SAMPLING_INTERFACE` | N | N | N | AE |
| `SHARED_BASE_COMPATIBILITY` | IP | N | N | IP |
| `TRAINING_TUNING_AND_INFERENCE_INTERFACES` | AE | AE | AE | AE |
| `NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY` | AE | AE | AE | AE |

### 6.2 Implementation objects by domain

For each row below, the training and inference budget IDs are exactly the
corresponding `TRAIN[d].budget_id` and `INFER[d].budget_id`; the capability
matrix is the family column above.

| Family | Domain | Exact implementation ID | Exact config SHA-256 |
|---|---|---|---|
| NGDB | `physionet-challenge-2012` | `B06-NGDB-STYLE-AUXILIARY-GUIDE-PLUS-CORRECTION-PHYSIONET-CHALLENGE-2012-V1` | `4148c1e6f03781155eddc5ebe8446dbefce7c2de580a7914efc8b0a3ddca7586` |
| NGDB | `online-retail-ii` | `B06-NGDB-STYLE-AUXILIARY-GUIDE-PLUS-CORRECTION-ONLINE-RETAIL-II-V1` | `680bd6c50aa481c0232a00dfe65cac9949432e07e79bb245c01cd7355b0434bd` |
| DEFT | `physionet-challenge-2012` | `B06-DEFT-STYLE-GENERALIZED-H-FROZEN-BASE-CORRECTION-PHYSIONET-CHALLENGE-2012-V1` | `1d485e0372b70c3e020d2af464b782d20dc8c050d919eece0ab8260fbacb2300` |
| DEFT | `online-retail-ii` | `B06-DEFT-STYLE-GENERALIZED-H-FROZEN-BASE-CORRECTION-ONLINE-RETAIL-II-V1` | `96550380cdd9161cb64b8d727fd2896c3dde7e0c40869c52457e3f654bc7b683` |
| same-base SMC/Feynman–Kac | `physionet-challenge-2012` | `B06-TASK-COMPATIBLE-SAME-BASE-SMC-OR-FEYNMAN-KAC-PHYSIONET-CHALLENGE-2012-V1` | `57bbcb95f58b55d1154470d829daccd966d8ecc1b11a0c9368aec7af309a93c6` |
| same-base SMC/Feynman–Kac | `online-retail-ii` | `B06-TASK-COMPATIBLE-SAME-BASE-SMC-OR-FEYNMAN-KAC-ONLINE-RETAIL-II-V1` | `94b3bad18048f96a1b99f03012c116da3e550df06548a00d6cecf17c4367dad6` |
| point/edit generator | `physionet-challenge-2012` | `B06-CLOSEST-VARIABLE-CARDINALITY-POINT-OR-EDIT-GENERATOR-PHYSIONET-CHALLENGE-2012-V1` | `a5d626a0e9f25d203cacf5790a9396185e8849a5d9f58fdae61521298394e2a8` |
| point/edit generator | `online-retail-ii` | `B06-CLOSEST-VARIABLE-CARDINALITY-POINT-OR-EDIT-GENERATOR-ONLINE-RETAIL-II-V1` | `38e51c2df150939cb375877b30f0c049f8c2ad1cabf6c69996e6961e2515eeca` |

The exact family config behind each digest has schema
`HETERODIFF_B06_LITERATURE_FAMILY_DOMAIN_CONFIG_V1`; its family and domain IDs;
the implementation ID as `adapter_id`; the common source interface; objective
`F105_CONDITIONAL_SAMPLE_GENERATION_SAME_CASE_ROSTER`; task interface
`EXACT_64_DRAW_F105_CONFIGURATION_BATCH`; conditioning semantics
`FROZEN_DOMAIN_PARTIAL_OBSERVATION_INTERFACE`; exact `TRAIN[d]` and `INFER[d]`;
the matrix above; license scope
`INTERNAL_RESEARCH_ONLY_NO_PUBLIC_DISTRIBUTION_UNTIL_B10_REVIEW`;
`b12_runtime_qualification_required=true`; and
`post_test_change_permitted=false`.

Its exact origins are:

- NGDB: reference `NEURAL_GUIDED_DIFFUSION_BRIDGES_ICML_2025`, repository
  `https://github.com/bookdiver/neuralbridge`, commit
  `e73b878b99d8a3b41685921dd31736cf764a277c`, `upstream_code_used=false`,
  reason `NO_LICENSE_FILE_AT_FROZEN_COMMIT; CLEAN_ROOM_INTERFACE_ONLY`.
- DEFT: reference `DEFT_GENERALIZED_H_TRANSFORM_2024`, repository
  `https://github.com/alexdenker/DEFT`, commit
  `2495d46593cb48253e8f879131cdd82fcc17be7f`, `upstream_code_used=false`,
  reason `IMAGE_INVERSE_PROBLEM_CODE_NOT_IMPORTED; CLEAN_ROOM_INTERFACE_ONLY`.
- same-base SMC/Feynman–Kac: reference
  `SAME_BASE_SEQUENTIAL_MONTE_CARLO_FEYNMAN_KAC_CONTROL`, null repository and
  commit, `upstream_code_used=false`, reason `LOCAL_EXACT_ALGORITHM_INTERFACE`.
- point/edit generator: reference
  `EDIT_BASED_FLOW_MATCHING_FOR_TEMPORAL_POINT_PROCESSES_ICLR_2026`, EditPP
  repository and frozen commit below, `upstream_code_used=false`, reason
  `MIT_UPSTREAM_SELECTED; FUTURE_B12_ADAPTER_MAY_USE_CODE_ONLY_UNDER_THE_FROZEN_LICENSE_AND_EXTENSION_BOUNDARY`.

### 6.3 Exact justification objects

`DISTINCT[d]` is the exact object with `domain_id=d`, disposition
`IMPLEMENTED_AS_DISTINCT_ROW_NO_INAPPLICABILITY_OR_EQUIVALENCE_CLAIM`,
`inapplicability_claimed=false`, `cross_row_equivalence_claimed=false`,
`b12_execution_or_result_claimed=false`, and all five equivalence dimensions
`OBJECTIVE`, `PROPOSAL_OR_CONDITIONING_SEMANTICS`, `MODEL_CLASS`, `COMPUTE`, and
`TASK_INTERFACE` equal to `DISTINCT_ROW`.

`RETAIL_MATCH` is the exact object with `domain_id=online-retail-ii`,
disposition
`IMPLEMENTED_AND_IDENTICAL_TO_RETAIL_EXTERNAL_BASELINE_WITH_ROLE_SPECIFIC_PROOF`,
`inapplicability_claimed=false`, `cross_row_equivalence_claimed=true`,
`b12_execution_or_result_claimed=false`, and all five equivalence dimensions
equal to `MATCH`.

The justification-by-domain objects for NGDB, DEFT, and same-base
SMC/Feynman–Kac map PhysioNet to `DISTINCT[physionet-challenge-2012]` and Retail
to `DISTINCT[online-retail-ii]`. The point/edit object maps PhysioNet to its
`DISTINCT` object and Retail to `RETAIL_MATCH`. The Retail match is a
role/config identity declaration; it is not a B12 execution or result claim.

## 7. Bounded external-baseline selection and source audit

The exact selection rule is
`B06-STRONGEST-ELIGIBLE-WITHIN-FROZEN-AUDIT-ROSTER-V1`. Criteria, in order,
are task-compatible conditional generation, official public implementation,
immutable revision, retrieved code license, domain evidence, and a finite
adapter/tuning plan. The registry explicitly sets
`universal_state_of_the_art_claimed=false`.

Accordingly, “strongest” means best aligned among the candidates actually
audited under those frozen criteria. It is not a global SOTA, empirical
superiority, leaderboard, exhaustive-literature, or future-proof claim. No
external baseline was run and no performance outcome was inspected.

### 7.1 PhysioNet: CSDI

The bounded selection is [CSDI](https://github.com/ermongroup/CSDI) at exact
[commit `7f24a436...`](https://github.com/ermongroup/CSDI/commit/7f24a436f08d98853a6b43d4f7f04e5a65ecdf27).
Its native strengths are probabilistic conditional imputation, an explicit
PhysioNet entry point, missing/partially observed marks, and a conditional
sampling interface. Its exact project gaps are material:

- the pinned loader has a [35-variable list](https://github.com/ermongroup/CSDI/blob/7f24a436f08d98853a6b43d4f7f04e5a65ecdf27/dataset_physio.py#L9-L13),
  omitting `MechVent` and `Weight` and spelling troponins differently from the
  F105 schema;
- it [parses only integer hours](https://github.com/ermongroup/CSDI/blob/7f24a436f08d98853a6b43d4f7f04e5a65ecdf27/dataset_physio.py#L16-L44),
  discarding minute timing;
- its per-hour mapping [retains one value per repeated parameter](https://github.com/ermongroup/CSDI/blob/7f24a436f08d98853a6b43d4f7f04e5a65ecdf27/dataset_physio.py#L21-L32),
  so same-parameter multiplicity is not lossless; and
- it constructs [48 hourly rows over 35 variables](https://github.com/ermongroup/CSDI/blob/7f24a436f08d98853a6b43d4f7f04e5a65ecdf27/dataset_physio.py#L35-L45),
  rather than the exact variable-cardinality F105 event multiset.

Therefore exact physical time, simultaneous multiplicity, typed/continuous
marks, arbitrary unordered observations, horizon/cap semantics, the exact
F105 event adapter, and the addressed R64 interface are author extensions and
remain B12 obligations. CSDI is not claimed to be natively F105-compatible.

### 7.2 Retail: EditPP

The bounded selection is [EditPP](https://github.com/martenlienen/editpp) at
exact [commit `3113d2ee...`](https://github.com/martenlienen/editpp/commit/3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918),
with its [official paper record](https://openreview.net/forum?id=FNf9IV1P2L).
It natively supplies continuous-time point-sequence generation/editing and
prefix-style temporal conditioning, but not this project’s Retail object:

- its loader reads only [one-dimensional `arrival_times`](https://github.com/martenlienen/editpp/blob/3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918/editflows/data/tpps.py#L49-L72),
  and its batch constructor [requires one-dimensional sequences](https://github.com/martenlienen/editpp/blob/3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918/editflows/editflows.py#L83-L91);
- its native real-data roster does not contain Online Retail II; and
- its conditional evaluation is [time-prefix/suffix forecasting](https://github.com/martenlienen/editpp/blob/3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918/editflows/train_task.py#L724-L770),
  not the exact arbitrary-subset F105/F109 observation protocol.

Thus the structured invoice/stock/description/quantity/price/country mark
heads, duplicate-occurrence serial channel, source-civil Retail adapter, and
arbitrary unordered-subset R64 interface are explicit author extensions.
This record does not say EditPP lacks conditional support; it says the native
prefix-conditioning interface is not the exact project interface.

### 7.3 Audited alternatives and licenses

The main frozen alternatives included [Add-Thin](https://github.com/davecasp/add-thin)
at [`aeb051349...`](https://github.com/davecasp/add-thin/commit/aeb051349f130636dca1a90a5582289a29968bfe),
[Point Set Diffusion](https://github.com/davecasp/point-set-diffusion) at
[`16144a080...`](https://github.com/davecasp/point-set-diffusion/commit/16144a08058f63b434eeb102d446bbd5869c2173),
[NeuralBridge](https://github.com/bookdiver/neuralbridge) at
[`e73b878b...`](https://github.com/bookdiver/neuralbridge/commit/e73b878b99d8a3b41685921dd31736cf764a277c),
and [DEFT](https://github.com/alexdenker/DEFT) at
[`2495d465...`](https://github.com/alexdenker/DEFT/commit/2495d46593cb48253e8f879131cdd82fcc17be7f).

Add-Thin had an MIT license receipt
`255e3af542368979678cdb1c0afd01e1c95a3303252d8b6cc8832b63e1794a30`
but a scalar-time, prefix/window forecast interface without the exact Retail
marks or arbitrary full-horizon subset semantics. Point Set Diffusion and
NeuralBridge had no visible license file at their audited commits, so no code
use is authorized or claimed. DEFT had a retrieved NVIDIA Source Code License
limited to noncommercial research/evaluation, hash
`ed262a2f6c8952233fe6c81b2c66fe41096f5fa43610aaaaa7e933d1d9fdc729`;
its image inverse-problem code was not imported. These facts support the
bounded roster decision, not a universal ranking.

## 8. Exact external field objects

### 8.1 CSDI / PhysioNet

The method ID is `CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1`; repository and
commit are the exact values in Section 7.1. Its exact license object is:

```json
{"bytes":1071,"path":"LICENSE","raw_sha256":"76f5d72acd2d179c72f9c8d7212cc2e6904c1a15908951d0959b9ea13d528ba9","scope":"CODE_CONFIGS_AND_MODIFICATIONS; WEIGHTS_SEPARATELY_CUSTODIED_IF_USED","spdx":"MIT"}
```

Its exact config digest is
`72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046`.
The bound upstream artifacts are `config/base.yaml` hash
`a492e8e1f682cec19549da2c7f4e13cf04067f6db260142a0243aba3daaab0e7`,
`exe_physio.py` hash
`8d50d41f021c777728319c201c0956d0d107c0d58a5c23870a1730633b79c136`,
and requirements hash
`6a14207beb17400d8595e111a5bc2d26f4886acea7d84952f501a419d5d372ce`.
Frozen upstream defaults are epochs 200, batch size 16, and 50 diffusion
steps. The independently audited `dataset_physio.py` hash is
`a79fd1def63b39da5bcd9a9fd897df9ae834e097188f6289f8e75ae704a2adcc`.

Its exact capability matrix is the CSDI column below, and its exact extension
list is, in order:

1. `LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS`;
2. `VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER`;
3. `EXACT_PHYSIONET_F105_EVENT_ADAPTER`; and
4. `FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE`.

### 8.2 EditPP / Retail

The method ID is `EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1`; repository and
commit are the exact values in Section 7.2. Its exact license object is:

```json
{"bytes":1118,"path":"LICENSE","raw_sha256":"94f6472f9fafcc23e53bd3914638c94f3ab39671fbf1195b2d798b9bf8072198","scope":"CODE_CONFIGS_AND_MODIFICATIONS; WEIGHTS_SEPARATELY_CUSTODIED_IF_USED","spdx":"MIT"}
```

Its exact config digest is
`64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee`.
The bound upstream artifacts are `train.py` hash
`e716d4878f2683e4fa440e7da21fbe7ac1abd33302982fe56456b4c427ee58df`,
`config/train.yaml` hash
`2dfbdc3ce212cea887c272ec3a6a16fb66d810f75a58a40ab666e035461988cd`,
`config/task/tef.yaml` hash
`e8786d6de3fb58d949fef6b7e856ec9441047ca41dcb463e2e4f09fcb1d194a9`,
`config/task/model/llama2.yaml` hash
`67ec74d9df9912f3aab008d216b40406baf4d9df865bd1921959b0a0cdb02d42`,
and lock hash
`e66774092d4d2d1b14d0dbf3a184a2fc708986c651e30f7f71119c864f6957d8`.
Frozen upstream defaults are 5,000 maximum steps, 100 sample steps, precision
`32`, conditioning `independent`, hidden size 64, two hidden layers, four
attention heads, and maximum log rate `32`.

Its exact extension list is, in order:

1. `STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS`;
2. `SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL`;
3. `EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER`; and
4. `ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE`.

### 8.3 Exact external capability statements

| Exact axis | CSDI | EditPP |
|---|---|---|
| `VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `DOMAIN_PHYSICAL_TIME` | `AUTHOR_EXTENSION` | `NATIVE` |
| `SIMULTANEOUS_EVENTS_AND_MULTIPLICITY` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `TYPED_EVENTS_AND_CONTINUOUS_MARKS` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `MISSING_OR_PARTIALLY_OBSERVED_MARKS` | `NATIVE` | `AUTHOR_EXTENSION` |
| `UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `CONDITIONAL_SAMPLING_INTERFACE` | `NATIVE` | `AUTHOR_EXTENSION` |
| `SHARED_BASE_COMPATIBILITY` | `INAPPLICABLE_WITH_PROOF` | `INAPPLICABLE_WITH_PROOF` |
| `TRAINING_TUNING_AND_INFERENCE_INTERFACES` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |
| `NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY` | `AUTHOR_EXTENSION` | `AUTHOR_EXTENSION` |

For each method, the exact native-capability/extension statement is the object
containing its complete matrix above, its ordered four-item extension list,
`all_extension_compute_charged=true`, and
`runtime_qualification_owned_by_B12=true`.

### 8.4 Exact external tuning budgets

The exact CSDI tuning object is:

```json
{"budget_id":"B06-TUNING-CSDI-PHYSIONET-V1","candidate_grid":{"channels":[64,128],"diffusion_layers":[4,6],"learning_rate":["1/2000","1/1000"]},"candidate_grid_sha256":"0fa79885fb16295a0198a818288fe29f77abec048a2b90010689d523f6b60b21","failed_or_aborted_trials_charged":true,"maximum_trials":8,"selection_data":"TRAIN_AND_VALIDATION_ONLY","selection_metric":"F105_VALIDATION_SCORE_LOWER_IS_BETTER","test_access_permitted":false,"tie_rule":"LEXICOGRAPHIC_CANONICAL_CONFIG_BYTES","unused_transfer_or_postresult_topup_permitted":false}
```

The exact EditPP tuning object is:

```json
{"budget_id":"B06-TUNING-EDITPP-RETAIL-V1","candidate_grid":{"alignment":["replace","delta"],"coupling":["independent","sequence-length"],"hidden_size":[256,512]},"candidate_grid_sha256":"8513a6d56780776069d73558b578f79756f73c74a750d7d00b179769d0fb445a","failed_or_aborted_trials_charged":true,"maximum_trials":8,"selection_data":"TRAIN_AND_VALIDATION_ONLY","selection_metric":"F105_VALIDATION_SCORE_LOWER_IS_BETTER","test_access_permitted":false,"tie_rule":"LEXICOGRAPHIC_CANONICAL_CONFIG_BYTES","unused_transfer_or_postresult_topup_permitted":false}
```

## 9. One-by-one F062--F103 candidate projection

The aliases `P`, `TRAIN_BY_DOMAIN`, `INFER_BY_DOMAIN`, the four family
implementation/justification objects, and the two external statements and
tuning objects are exactly and completely defined above. This table therefore
enumerates each field’s exact value without replacing a complex object by a
prose approximation.

| Field | Exact candidate value | Evidence |
|---|---|---|
| F062 | `content-addressed:workspace/heterodiff/b06-local-deepsets-method-source-release-v1` | Section 3; registry `primary_pair[0].repository` |
| F063 | `sha256:023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564` | Section 3; `primary_pair[0].commit_or_release` |
| F064 | `c44af50b915d024cb6019ee82a2998410afd3401fdb84c5313a84bc98fa543b1` | Section 3; guide config digest |
| F065 | exact object `P` | Section 3.1 |
| F066 | exact object `TRAIN_BY_DOMAIN` | Section 4 |
| F067 | exact object `INFER_BY_DOMAIN` | Section 4 |
| F068 | `content-addressed:workspace/heterodiff/b06-local-deepsets-method-source-release-v1` | Section 3; registry `primary_pair[1].repository` |
| F069 | `sha256:023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564` | Section 3; `primary_pair[1].commit_or_release` |
| F070 | `f5c87a6c66defe9e1e8bb12e9578bc9317892af06dce0b88a5b1b81933b742a5` | Section 3; direct config digest |
| F071 | exact object `P` | Section 3.1 |
| F072 | exact object `TRAIN_BY_DOMAIN` | Section 4 |
| F073 | exact object `INFER_BY_DOMAIN` | Section 4 |
| F074 | exact common static-control implementation string | Section 5, ordinal 0 |
| F075 | `37d5178c836ced493dec1fe49b08ab042e738c5c24edc5867830528154b51ae4` | Section 5, ordinal 0 |
| F076 | exact common static-control implementation string | Section 5, ordinal 1 |
| F077 | `e175d468fb0df523c9adb2f6aa2e6f4b843b872e54234f63a1f41465f8bef212` | Section 5, ordinal 1 |
| F078 | exact common static-control implementation string | Section 5, ordinal 2 |
| F079 | `a2f91e01e1bdc6854fef6a045df802eaf4a5e60ef124c4303b0694d40ed36008` | Section 5, ordinal 2 |
| F080 | exact common static-control implementation string | Section 5, ordinal 3 |
| F081 | `7ecfb6dd842a781d70ac147e374a501f819c8f61cd20f38442526079fb607032` | Section 5, ordinal 3 |
| F082 | NGDB implementation-by-domain object | Sections 6.1–6.2 |
| F083 | `{physionet-challenge-2012:DISTINCT[physionet-challenge-2012], online-retail-ii:DISTINCT[online-retail-ii]}` | Section 6.3 |
| F084 | DEFT implementation-by-domain object | Sections 6.1–6.2 |
| F085 | `{physionet-challenge-2012:DISTINCT[physionet-challenge-2012], online-retail-ii:DISTINCT[online-retail-ii]}` | Section 6.3 |
| F086 | same-base SMC/Feynman–Kac implementation-by-domain object | Sections 6.1–6.2 |
| F087 | `{physionet-challenge-2012:DISTINCT[physionet-challenge-2012], online-retail-ii:DISTINCT[online-retail-ii]}` | Section 6.3 |
| F088 | point/edit-generator implementation-by-domain object | Sections 6.1–6.2 |
| F089 | `{physionet-challenge-2012:DISTINCT[physionet-challenge-2012], online-retail-ii:RETAIL_MATCH}` | Section 6.3 |
| F090 | `CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1` | Sections 7.1 and 8.1 |
| F091 | `https://github.com/ermongroup/CSDI` | Sections 7.1 and 8.1 |
| F092 | `7f24a436f08d98853a6b43d4f7f04e5a65ecdf27` | Sections 7.1 and 8.1 |
| F093 | exact CSDI license JSON object | Section 8.1 |
| F094 | `72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046` | Section 8.1 |
| F095 | exact CSDI matrix + four extensions + two true booleans | Sections 8.1 and 8.3 |
| F096 | exact CSDI tuning JSON object | Section 8.4 |
| F097 | `EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1` | Sections 7.2 and 8.2 |
| F098 | `https://github.com/martenlienen/editpp` | Sections 7.2 and 8.2 |
| F099 | `3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918` | Sections 7.2 and 8.2 |
| F100 | exact EditPP license JSON object | Section 8.2 |
| F101 | `64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee` | Section 8.2 |
| F102 | exact EditPP matrix + four extensions + two true booleans | Sections 8.2 and 8.3 |
| F103 | exact EditPP tuning JSON object | Section 8.4 |

## 10. License, release, and nonexecution boundary

The retrieved CSDI and EditPP MIT receipts support the recorded scope
`CODE_CONFIGS_AND_MODIFICATIONS; WEIGHTS_SEPARATELY_CUSTODIED_IF_USED` at the
exact commits. They do not establish a license for any dataset, future model
weight, third-party dependency, paper asset, or local primary source release.
Required notices and the exact scope of any public derivative must be handled
by the separate release/anonymization process.

Every family config further carries
`INTERNAL_RESEARCH_ONLY_NO_PUBLIC_DISTRIBUTION_UNTIL_B10_REVIEW`. This candidate
does not close B10, authorize public distribution, or convert an absent or
restricted upstream license into permission. NeuralBridge and Point Set
Diffusion code are not used; DEFT code is not imported; future EditPP code use
is conditional on the frozen MIT and extension boundary.

No external package was installed or executed for this freeze. No external
model was transformed. No data was acquired, opened, parsed, or split. No
scientific entropy, training, inference, result inspection, formal-test
result, scientific result, submission, or publication claim occurred.

## 11. Why B08 and B12 remain open

### B08 remains `OPEN`

The package freezes integer resource-event ceilings and prospective equality
identifiers only. It supplies no hardware or runtime identity, calibration
weight, scalar ceiling value, hard-axis ceiling value, capacity reservation,
or resource receipt. Consequently the F104 scalar cannot yet be instantiated
on a selected environment, and no availability or feasibility claim follows.

### B12 remains `OPEN`

The adapter contract validates identities, capability declarations, exact
F105 materialized values, and canonical F109 R64 addresses; it has no loader,
model transformation, training, inference, or metric-execution surface. The
remaining B12 obligations include:

- implementing and qualifying the 64-dimensional conditioning-context
  encoder for the primary pair;
- qualifying streaming or a limit lift for the local base’s current native
  10,000-configuration runtime cap against domain caps 131,072 and 1,067,371,
  with no truncation;
- building executable control and literature-family adapters;
- implementing the four CSDI and four EditPP author extensions;
- installing and qualifying any permitted upstream packages; and
- passing the end-to-end runner and whole-method gates.

No row in this candidate substitutes identity or configuration validation for
those executable obligations.

## 12. Qualification and candidate handoff

The frozen F104 production contract, B06 registry, and B06-to-B12 adapter
contract pass the combined focused hostile suite: `237 passed`. Coverage
includes exact integer/rational compute types and bounds, prospective primary
equality, registry reconstruction, local source-release hashing, parameter
counts, config digests, capability rosters, license receipts, domain mapping,
canonical 64-row F109 addressing, and explicit B08/B12 refusal boundaries.

This receipt is still a `DRAFT_CANDIDATE_PENDING_INDEPENDENT_REVIEW`. A review
must reopen the exact bytes, recompute every raw and semantic digest, replay
the field projection and count delta, test hostile mutations from the project
root and an unrelated working directory, audit the official-source statements,
and report P0/P1/P2 findings. Only a GO receipt may make the candidate eligible
for the later ledger/timetable registration described in Section 1.
