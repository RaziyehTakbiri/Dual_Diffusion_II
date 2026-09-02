"""Read-only overlay-source and coordinate freeze for the A1 R1 successor.

The module freezes source bytes, seed overlays, coordinate identities, and a
descriptive legacy API inventory.  It does not freeze a binder schema,
materialize an adapter, import project modules, issue a permit, launch a process,
or write any file.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = (
    "heterodiff-manuscript-v3-a1-r1-registry-aware-overlay-source-"
    "coordinate-freeze-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-registry-aware-static-overlay-source-freeze-qualification-v1"
)
SOURCE_MANIFEST_SCHEMA = (
    "heterodiff-r1-registry-aware-preactivation-overlay-source-manifest-v1"
)
SOURCE_MANIFEST_DOMAIN = (SOURCE_MANIFEST_SCHEMA + "\0").encode("ascii")
OVERLAY_RULE_SCHEMA = "heterodiff-r1-registry-aware-overlay-rule-v1"
OVERLAY_RULE_DOMAIN = (OVERLAY_RULE_SCHEMA + "\0").encode("ascii")
COORDINATE_MANIFEST_SCHEMA = "heterodiff-r1-registry-aware-coordinate-manifest-v1"
COORDINATE_MANIFEST_DOMAIN = (COORDINATE_MANIFEST_SCHEMA + "\0").encode("ascii")
PHASE_EVENT_SCHEMA = "heterodiff-r1-registry-aware-phase-event-schedule-v1"
PHASE_EVENT_DOMAIN = (PHASE_EVENT_SCHEMA + "\0").encode("ascii")
REGISTRY_DOMAIN = b"heterodiff-r1-registry-aware-seed-registry-v1\0"
REGISTRATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-r1-registry-aware-overlay-source-registration-v1\0"
)
MILESTONE_STATE = (
    "R1_A1_REGISTRY_AWARE_OVERLAY_SOURCE_AND_COORDINATE_FREEZE_ZERO_EXECUTION_"
    "RUNTIME_ADAPTER_AND_BINDER_DEFERRED_NOT_EXECUTABLE"
)

REGISTRY = (4052249444591756, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
EXPOSED_SEED = 1729
SAMPLE_BUDGETS = (512, 4096, 32768)
EXACT_METHODS = ("direct", "guided", "strong_direct")
PRIMARY_METHODS = ("direct", "guided")
CONTROL_METHODS = ("strong_direct", "guide_input", "mismatch")

PLANNED_ADAPTER_TARGET = (
    "src/heterodiff/experiments/finite_association_registry_aware_capsule_v1.py"
)
STATIC_AUDIT_MODULE_PATH = (
    "research/diagnostics/finite_association_r1_registry_aware_capsule_v1.py"
)
REGISTRATION_SIDECAR_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.json"
)
MILESTONE_ARTIFACT_PATHS = (
    "manuscript_v3/a1_r1_registry_aware_source_execution_capsule_freeze_v1.md",
    REGISTRATION_SIDECAR_PATH,
    STATIC_AUDIT_MODULE_PATH,
    (
        "tests/unit/"
        "test_manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.py"
    ),
)
PUBLICATION_ANONYMITY_BOUNDARY = {
    "internal_registration_not_submission_artifact": True,
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "raw_milestone_artifact_paths": list(MILESTONE_ARTIFACT_PATHS),
    "raw_milestone_artifact_inclusion_permitted": False,
    "raw_predecessor_custody_inclusion_permitted": False,
    "source_paths_and_local_custody_metadata_internal_only": True,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "publication_roster_frozen": False,
    "fresh_anonymity_audit_required": True,
}
REGISTRATION_NONCLAIMS = {
    "registry_integration_complete": False,
    "source_amendment_complete": False,
    "overlay_source_tree_materialized": False,
    "adapter_implemented": False,
    "execution_capsule_complete": False,
    "runtime_bundle_complete": False,
    "binder_schema_frozen": False,
    "successor_authority_frozen": False,
    "typed_coordinate_consumption_qualified": False,
    "phase_aggregate_admission_qualified": False,
    "binder_integration_complete": False,
    "runner_integration_complete": False,
    "production_order_activation_complete": False,
    "primary_metrics_integration_complete": False,
    "candidate_decision_integration_complete": False,
    "permit_issued": False,
    "phase_consumption_issued": False,
    "rank_execution_authorized": False,
    "rank_execution_performed": False,
    "training_execution_authorized": False,
    "training_execution_performed": False,
    "production_execution_authorized": False,
    "production_execution_performed": False,
    "scientific_execution_authorized": False,
    "scientific_result_eligible": False,
    "scientific_result_produced": False,
    "r1_qualified": False,
    "r2_qualified": False,
    "c17_proved": False,
    "claim_promoted": False,
    "submission_ready": False,
}

BASE_SOURCE_PATHS = (
    "src/heterodiff/__init__.py",
    "src/heterodiff/evaluation/__init__.py",
    "src/heterodiff/evaluation/finite_association_decision.py",
    "src/heterodiff/evaluation/finite_association_path_evaluator.py",
    "src/heterodiff/evaluation/finite_association_residual_evaluator.py",
    "src/heterodiff/evaluation/finite_association_residual_metrics.py",
    "src/heterodiff/evaluation/metric_floor.py",
    "src/heterodiff/events/__init__.py",
    "src/heterodiff/events/configuration.py",
    "src/heterodiff/events/observations.py",
    "src/heterodiff/events/schema.py",
    "src/heterodiff/events/transforms.py",
    "src/heterodiff/experiments/__init__.py",
    "src/heterodiff/experiments/finite_association_exact_population_isolated_runner.py",
    "src/heterodiff/experiments/finite_association_exact_population_torch.py",
    "src/heterodiff/experiments/finite_association_execution_order.py",
    "src/heterodiff/experiments/finite_association_guided_residual_pilot.py",
    "src/heterodiff/experiments/finite_association_isolated_runner.py",
    "src/heterodiff/experiments/finite_association_primary_metrics.py",
    "src/heterodiff/experiments/finite_association_production_order.py",
    "src/heterodiff/experiments/finite_association_rank_stress.py",
    "src/heterodiff/experiments/finite_association_residual_data.py",
    "src/heterodiff/experiments/finite_association_residual_training_torch.py",
    "src/heterodiff/experiments/finite_association_runtime_attestor.py",
    "src/heterodiff/experiments/finite_association_runtime_identity.py",
    "src/heterodiff/models/__init__.py",
    "src/heterodiff/models/finite_association_residual_torch.py",
    "src/heterodiff/models/finite_bridge_residual.py",
    "src/heterodiff/models/reference_config.py",
    "src/heterodiff/theory/__init__.py",
    "src/heterodiff/theory/conditional_bridge.py",
    "src/heterodiff/theory/exact_reversal.py",
    "src/heterodiff/theory/finite_atomic_association_bridge.py",
    "src/heterodiff/theory/finite_atomic_counting.py",
    "src/heterodiff/theory/finite_atomic_overflow_observation.py",
    "src/heterodiff/theory/finite_atomic_reference_guide.py",
    "src/heterodiff/theory/finite_bridge_path_control.py",
    "src/heterodiff/theory/finite_bridge_population.py",
    "src/heterodiff/theory/finite_state.py",
    "src/heterodiff/theory/gaussian_particle_bridge.py",
    "src/heterodiff/theory/immigration_death.py",
    "src/heterodiff/theory/path_kl.py",
    "src/heterodiff/theory/regional_configuration_bridge.py",
    "src/heterodiff/theory/singular_schema.py",
    "src/heterodiff/theory/unordered_association.py",
)
BASE_SOURCE_PATHS_SHA256 = (
    "1c33dc40712f2b71471e29b2eac2b5de8c95f256025a38dfd51d0712ca43a82c"
)
BASE_SOURCE_EXPECTATIONS = (
    (
        "src/heterodiff/__init__.py",
        1387,
        "26fdc70b2d9f92ad41f740e1963ab409986f391aac2c85c5649379b26164a53e",
    ),
    (
        "src/heterodiff/evaluation/__init__.py",
        1085,
        "1957eb6081e80a72b26e0ad25cb2cdced7a6e03807a3055ee364c161989f30e1",
    ),
    (
        "src/heterodiff/evaluation/finite_association_decision.py",
        99180,
        "aa8a4112085d4741e3ba654bcac28b6883fa70566129ab88dca12be656c2ae20",
    ),
    (
        "src/heterodiff/evaluation/finite_association_path_evaluator.py",
        79833,
        "2d67fd5caa8e1c0fb75196ca11603d60663e9577f7fbd35f9b1e1333a0b30a1b",
    ),
    (
        "src/heterodiff/evaluation/finite_association_residual_evaluator.py",
        56492,
        "abf6a2d3807266797b90c079a1ae21bbf07d3c03ed6ed52e8257b4ef41c55f83",
    ),
    (
        "src/heterodiff/evaluation/finite_association_residual_metrics.py",
        14342,
        "d97602921d0c676ab244b68887cb558f8f3e3c3b1ecab110ebc2d317beb448f7",
    ),
    (
        "src/heterodiff/evaluation/metric_floor.py",
        19602,
        "85c6a0cd5302dbd3cbc33596be92be7349e88e430bb7e267ba39671be984e4d6",
    ),
    (
        "src/heterodiff/events/__init__.py",
        1222,
        "3e4e213835262634f5f795e60dafda08fc3d599a5741088f567215d5406640b9",
    ),
    (
        "src/heterodiff/events/configuration.py",
        16009,
        "66fdc15a1253be8490ff3a18ca9355344388a7820cf7f74c293372669585c0c4",
    ),
    (
        "src/heterodiff/events/observations.py",
        14142,
        "bf1377f543f0adbd5d690c61ebff4eff08db73aa47ef7fd4bc516eeb026e0698",
    ),
    (
        "src/heterodiff/events/schema.py",
        18274,
        "bebe1ac4c106ea58f05ef01568dfceb6ccd6580443baf6e43a8da8ea45cfe3e6",
    ),
    (
        "src/heterodiff/events/transforms.py",
        16464,
        "0bcd1e09de33c635b347fd7bb38646e32a32227cbd4fe70766a27b41156b16d0",
    ),
    (
        "src/heterodiff/experiments/__init__.py",
        68,
        "86d9d5bbd5cb739ce0dc1290f015717ce4aebf2a768d4658b596e0e117f32191",
    ),
    (
        "src/heterodiff/experiments/finite_association_exact_population_isolated_runner.py",
        203927,
        "e9ab2ee47d0ccc8ff615187405c948bb5927ffc95ff08607e42e4ed095d662ef",
    ),
    (
        "src/heterodiff/experiments/finite_association_exact_population_torch.py",
        116705,
        "699c609807d5f68a1f36a76eeac5b36b06fa6eef52e6e74cf318acb0faf194c9",
    ),
    (
        "src/heterodiff/experiments/finite_association_execution_order.py",
        49946,
        "e31753485aad2d5dc57ab0c5dfa80697ac4a11ab7937c62b4c8875d3038c0185",
    ),
    (
        "src/heterodiff/experiments/finite_association_guided_residual_pilot.py",
        27593,
        "4669c109c5fb4def854107ad4f117d2a8c6109beeeda9ba4eb9525b4b48f4e90",
    ),
    (
        "src/heterodiff/experiments/finite_association_isolated_runner.py",
        246030,
        "13e0d042e9bb509e11c4ffc9d2381565f2a939def7a0add38380bfedce63240f",
    ),
    (
        "src/heterodiff/experiments/finite_association_primary_metrics.py",
        73944,
        "46cb70c1a5cb9c1de31122443ed37cf6f92edb098044e3d78f546b14683b6421",
    ),
    (
        "src/heterodiff/experiments/finite_association_production_order.py",
        131551,
        "be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1",
    ),
    (
        "src/heterodiff/experiments/finite_association_rank_stress.py",
        124227,
        "ead7544be821d58874fd07d4293adc078257f8efb47a82a1e91ea2fa0b702c67",
    ),
    (
        "src/heterodiff/experiments/finite_association_residual_data.py",
        30503,
        "30c5d002c2e88238b840b3685f614d9ad42eda48782d655fabc859d6f4f82ac3",
    ),
    (
        "src/heterodiff/experiments/finite_association_residual_training_torch.py",
        102620,
        "44876731d31705c8c815cd586bf2b03b0490777db6a13ad8679e5199b794f115",
    ),
    (
        "src/heterodiff/experiments/finite_association_runtime_attestor.py",
        94575,
        "1c1e1e1e72b73eb6224223259927bfc3956dc033f62cf9796b1d276db77d019f",
    ),
    (
        "src/heterodiff/experiments/finite_association_runtime_identity.py",
        45660,
        "ba10c8053796b6d36bc02a2bea0716a443bba35fd1190333292b87701eb18bf0",
    ),
    (
        "src/heterodiff/models/__init__.py",
        408,
        "461f713772ce4b9b0d60a71af7df493708f3f4b335dcd59251aba4c6ad1e3e27",
    ),
    (
        "src/heterodiff/models/finite_association_residual_torch.py",
        47743,
        "c57834c57a9340c121ed1df88811ade136bbfc8ca5638acf975653fa2faa5690",
    ),
    (
        "src/heterodiff/models/finite_bridge_residual.py",
        12137,
        "872c8e6d5280df9fc74a2cac33034290fbda2d902fcc8a1994675cdfbf113676",
    ),
    (
        "src/heterodiff/models/reference_config.py",
        13685,
        "9ac1c2d0422467390ce95eccb075f4a55bcdd98b0544577058072c987c17c318",
    ),
    (
        "src/heterodiff/theory/__init__.py",
        6156,
        "7396b7366268fd5c7a4642671440719a2d65b88c178116f16875d9e1f05431a6",
    ),
    (
        "src/heterodiff/theory/conditional_bridge.py",
        8938,
        "6cbb6c80a9bf4cc5a32a921a431b651617d6fa79cc7bad6a97ed61eac0b1db7a",
    ),
    (
        "src/heterodiff/theory/exact_reversal.py",
        5692,
        "7f33ba16b953f1186b059ed8fb754ee69579ea3755bdb57577408d6e92b70a80",
    ),
    (
        "src/heterodiff/theory/finite_atomic_association_bridge.py",
        22215,
        "1c9f8b2c3e53f97870f07d636505e04147f3dfe3f048b03c15f4fd8c2942133c",
    ),
    (
        "src/heterodiff/theory/finite_atomic_counting.py",
        37720,
        "e9fc4f10a49c36ac2e1d48dca2e9e04586cf81eb7c3f0d6d6a708a43a669bda8",
    ),
    (
        "src/heterodiff/theory/finite_atomic_overflow_observation.py",
        20270,
        "6aed0aff991daff6fd20e67733bc87e5379d971d4256009d54c2fb76a3cc477e",
    ),
    (
        "src/heterodiff/theory/finite_atomic_reference_guide.py",
        28598,
        "56cd3cae88f395b082c59c674a45104de45c3311981f86563a114db7fa97a0b7",
    ),
    (
        "src/heterodiff/theory/finite_bridge_path_control.py",
        45529,
        "1cdb2cf82016ad0979fff3ef7451fe6116904cca772b017e6e605b78b476c502",
    ),
    (
        "src/heterodiff/theory/finite_bridge_population.py",
        25808,
        "6ebbce521f876436b5229c28f725f7256c013f7a22d81f722b923632e124261e",
    ),
    (
        "src/heterodiff/theory/finite_state.py",
        17818,
        "50462bba10a441325c06affe72660b53960a7793faa7722b94cd4fa6af434468",
    ),
    (
        "src/heterodiff/theory/gaussian_particle_bridge.py",
        35177,
        "41e63b43fdb7afa3a2d321ba64a0efb6cba5fe9598a43932a0f5e7daae4a42b0",
    ),
    (
        "src/heterodiff/theory/immigration_death.py",
        23289,
        "66fff8cfe944abe3df02842490e86b06d16145e3a164684d8106832c35e1204c",
    ),
    (
        "src/heterodiff/theory/path_kl.py",
        15389,
        "769992c89f151d90c04c66c50cad538bfa859396d8f6737aa6b5e05e39bb173a",
    ),
    (
        "src/heterodiff/theory/regional_configuration_bridge.py",
        46562,
        "47793fa9e65eea0f45faf491311e67aa206b025f6926cc3766d4055b8d752862",
    ),
    (
        "src/heterodiff/theory/singular_schema.py",
        25869,
        "f2bdaee061a2b00eea32896204cab014796e674a7a44be8a1c5ad57459fe94c5",
    ),
    (
        "src/heterodiff/theory/unordered_association.py",
        7866,
        "8ba24367974abc2289b8245691e80f2fdd4107de5e165324838c9b224d0bdbc4",
    ),
)
IMPORT_CLOSURE_ROOTS = (
    "src/heterodiff/evaluation/finite_association_decision.py",
    "src/heterodiff/experiments/finite_association_exact_population_isolated_runner.py",
    "src/heterodiff/experiments/finite_association_execution_order.py",
    "src/heterodiff/experiments/finite_association_isolated_runner.py",
    "src/heterodiff/experiments/finite_association_primary_metrics.py",
    "src/heterodiff/experiments/finite_association_production_order.py",
    "src/heterodiff/experiments/finite_association_rank_stress.py",
)
DENYLISTED_DEVELOPMENT_SOURCES = (
    "research/diagnostics/finite_association_trained_checkpoint_diagnostic.py",
    "src/heterodiff/experiments/finite_association_development_checkpoint_runner.py",
    "src/heterodiff/experiments/finite_association_development_checkpoint_runner_v2.py",
)
EXPECTED_DYNAMIC_IMPORT_SITES = (
    {
        "importer_path": (
            "src/heterodiff/experiments/finite_association_runtime_attestor.py"
        ),
        "call_kind": "__import__",
        "literal_target": "struct",
        "local_target_path": None,
        "admitted_by_static_source_closure": False,
    },
    {
        "importer_path": (
            "src/heterodiff/experiments/finite_association_runtime_identity.py"
        ),
        "call_kind": "importlib.import_module",
        "literal_target": (
            "heterodiff.experiments." "finite_association_runtime_identity_approval"
        ),
        "local_target_path": (
            "src/heterodiff/experiments/"
            "finite_association_runtime_identity_approval.py"
        ),
        "admitted_by_static_source_closure": False,
    },
)
DEFERRED_RUNTIME_SOURCE_EXPECTATIONS = (
    (
        "RUNTIME_IDENTITY_APPROVAL",
        "src/heterodiff/experiments/finite_association_runtime_identity_approval.py",
        75807,
        "42ebb7bc482bd8cdcc1adc30fd83ad6bf7ccfe968891ad500dfe1062157db5f2",
    ),
    (
        "RUNTIME_IDENTITY_CAPTURE",
        "src/heterodiff/experiments/finite_association_runtime_identity_capture.py",
        83865,
        "399151d43e45974a42e7108dad224f1e0e474b90d452c74488c50b9de2d8ea93",
    ),
)
NONPACKAGE_SOURCE_EXPECTATIONS = (
    (
        "PYPROJECT",
        "pyproject.toml",
        823,
        "78d8cddc752e6d2d41c6e050132ea71e65fb374a02a6fb00c2cf12ec3ff89fa0",
    ),
    (
        "ENVIRONMENT_LOCK",
        "requirements/m1-reference-macos-arm64-py311.lock",
        736,
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
    ),
    (
        "A1_SPECIFICATION_62",
        "research/62_a1_association_guided_residual_falsification_spec.md",
        47468,
        "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c",
    ),
)

OVERLAY_RULES = (
    {
        "schema": OVERLAY_RULE_SCHEMA,
        "path": "src/heterodiff/experiments/finite_association_residual_data.py",
        "constant_name": "PAIRED_SEEDS",
        "assignment_prefix_utf8": "PAIRED_SEEDS = (",
        "old_literal_utf8": "1_729",
        "new_literal_utf8": "4_052_249_444_591_756",
        "required_assignment_occurrences": 1,
        "required_literal_replacements": 1,
        "preserve_all_other_bytes": True,
    },
    {
        "schema": OVERLAY_RULE_SCHEMA,
        "path": "src/heterodiff/experiments/finite_association_isolated_runner.py",
        "constant_name": "_SEEDS",
        "assignment_prefix_utf8": "_SEEDS = (",
        "old_literal_utf8": "1_729",
        "new_literal_utf8": "4_052_249_444_591_756",
        "required_assignment_occurrences": 1,
        "required_literal_replacements": 1,
        "preserve_all_other_bytes": True,
    },
    {
        "schema": OVERLAY_RULE_SCHEMA,
        "path": (
            "src/heterodiff/experiments/"
            "finite_association_exact_population_isolated_runner.py"
        ),
        "constant_name": "_SEEDS",
        "assignment_prefix_utf8": "_SEEDS = (",
        "old_literal_utf8": "1_729",
        "new_literal_utf8": "4_052_249_444_591_756",
        "required_assignment_occurrences": 1,
        "required_literal_replacements": 1,
        "preserve_all_other_bytes": True,
    },
    {
        "schema": OVERLAY_RULE_SCHEMA,
        "path": "src/heterodiff/experiments/finite_association_execution_order.py",
        "constant_name": "PAIRED_SEEDS",
        "assignment_prefix_utf8": "PAIRED_SEEDS = (",
        "old_literal_utf8": "1729",
        "new_literal_utf8": "4052249444591756",
        "required_assignment_occurrences": 1,
        "required_literal_replacements": 1,
        "preserve_all_other_bytes": True,
    },
    {
        "schema": OVERLAY_RULE_SCHEMA,
        "path": "src/heterodiff/experiments/finite_association_production_order.py",
        "constant_name": "PAIRED_SEEDS",
        "assignment_prefix_utf8": "PAIRED_SEEDS = (",
        "old_literal_utf8": "1729",
        "new_literal_utf8": "4052249444591756",
        "required_assignment_occurrences": 1,
        "required_literal_replacements": 1,
        "preserve_all_other_bytes": True,
    },
)

PLANNED_OUTPUT_ROOTS = (
    "artifacts/a1_r1_registry_aware_source_execution_capsule_v1",
    "artifacts/a1_r1_registry_aware_production_order_v1",
    "artifacts/a1_r1_registry_aware_rank_stress_gate_v1.json",
    "artifacts/a1_r1_registry_aware_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_r1_registry_aware_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_r1_registry_aware_exact_population_campaign_v1",
    "artifacts/a1_r1_registry_aware_sampled_campaign_v1",
    "artifacts/a1_r1_registry_aware_primary_metrics_v1",
    "artifacts/a1_r1_registry_aware_candidate_decision_v1",
    "artifacts/a1_r1_registry_aware_independent_audit_v1",
    "artifacts/a1_r1_registry_aware_publication_decision_v1",
)
LEGACY_PRODUCTION_ROOTS = (
    "artifacts/a1_finite_association_production_order_v1",
    "artifacts/a1_rank_stress_gate_v1.json",
    "artifacts/a1_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_exact_population_campaign_v4",
    "artifacts/a1_campaign_v4",
    "artifacts/a1_primary_metrics_v1",
    "artifacts/a1_primary_metrics_v2",
    "artifacts/a1_candidate_decision_v1",
    "artifacts/a1_independent_audit_v1",
    "artifacts/a1_publication_decision_v1",
)
SUCCESSOR_RUNTIME_PATHS = (
    "requirements/m1-reference-macos-arm64-py311.r1-registry-v1.runtime-identity.json",
    "requirements/m1-reference-macos-arm64-py311.r1-registry-v1.runtime-identity.approval.json",
)
LEGACY_RUNTIME_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)
LEGACY_RUNTIME_APPROVAL_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.approval.json"
)
LEGACY_RUNTIME_CANDIDATE_ROOT = (
    "requirements/runtime-identity-candidates/m1-reference-macos-arm64-py311"
)

POSTDRAW_RECORD_SHA256 = (
    "0e49be2ca1fcfd901f2f50d3acdcf9786cebb630744623c457ef2a791666a4bb"
)
PREDRAW_RECORD_SHA256 = (
    "79e285045a1b99cd22121b51b92746cc2027abd8ff31351ae182bb71da5154b6"
)
REGISTRY_RAW_SHA256 = "d2854c9b1bbc7fb668d5741c3544b4b47adef340bcf58e74db33ba461f9b378b"
REGISTRY_RECORD_SHA256 = (
    "2be16cc37b6e046c95538679b05e334b0f299e08eed5c1ac67be1a5077f18f05"
)

GOVERNANCE_BINDINGS = (
    (
        "POSTDRAW_HUMAN",
        "manuscript_v3/a1_r1_replacement_seed_draw_postdraw_registration_v1.md",
        "bd6232c99b09b0490ed5ab9f8cd56de4b1b253ef07d402ac719f3e445362e582",
        None,
        None,
    ),
    (
        "POSTDRAW_MACHINE",
        "research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.json",
        "a13e038ea5f04379a75e48e086a9e597b6217dbaae2ae39ccebae74ebdfe8db0",
        POSTDRAW_RECORD_SHA256,
        "record_sha256",
    ),
    (
        "POSTDRAW_TEST",
        "tests/unit/test_manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.py",
        "3b558e88bade175f7a7a811dcaceee57879ed7f8831e877a91f17485559c6184",
        None,
        None,
    ),
    (
        "DRAW_ATTEMPT",
        "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1.attempt.json",
        "fa9047433d62620d145fda0a9f56aabf4296003356d9c3b4336b455d1e4de76b",
        "ec5984402ee5f9dbde658713bfa43d4026e32851b8a7dff53ef703a7ac1d47d5",
        "record_sha256",
    ),
    (
        "DRAW_RECORD",
        "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1/seed-draw-record.json",
        "63cff401182cf6502cd51d9d732eaccb0bec4c63ddbb4ff308b0d968a56dbd0f",
        "51702215c41e7832e12685cde8e8a1674c106956afb872d2e428a181be6c912b",
        "record_sha256",
    ),
    (
        "SEED_REGISTRY",
        "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1/replacement-seed-registry.json",
        REGISTRY_RAW_SHA256,
        REGISTRY_RECORD_SHA256,
        "record_sha256",
    ),
    (
        "DRAW_SUCCESS",
        "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1/success-receipt.json",
        "89705733ba5c26967981223fd760198be9844f5c38c7e793821bdda82aa37056",
        "d4f36bdf4a6fd6c1a363b80a98f25efbda5ec5faddcd04fe1dc330be4b67df65",
        "record_sha256",
    ),
    (
        "PREDRAW_HUMAN",
        "manuscript_v3/a1_r1_replacement_seed_draw_freeze_v1.md",
        "c657d9276dccc28b2b826968c376925a23368683cdccea2cf948b92ffa4277d5",
        None,
        None,
    ),
    (
        "PREDRAW_MACHINE",
        "research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.json",
        "39b4b26a95b7ee867f53981638902d4b5ae00d7e58dbdc203bce6b3177b3cf56",
        PREDRAW_RECORD_SHA256,
        "record_sha256",
    ),
    (
        "PREDRAW_MODULE",
        "research/diagnostics/finite_association_r1_replacement_seed_draw.py",
        "124d9e41cad3dc3a63c34e165a3d4bcfa380181f5efb83abd490ad61c9c99a9b",
        None,
        None,
    ),
    (
        "PREDRAW_TEST",
        "tests/unit/test_manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.py",
        "a3ebf3315f32c5765461cc92b1098fe065a5e681df7cd6faa6417fc58851b968",
        None,
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2_MACHINE",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
        "record_sha256",
    ),
    (
        "AUTHORITATIVE_CLAIM_LEDGER",
        "manuscript_v3/claim_ledger.md",
        "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
        None,
        None,
    ),
    (
        "AUTHORITATIVE_EXECUTION_PREREGISTRATION_HUMAN",
        "manuscript_v3/execution_preregistration.md",
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
        None,
    ),
    (
        "AUTHORITATIVE_EXECUTION_PREREGISTRATION_MACHINE",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
        None,
    ),
    (
        "CP76_READINESS_MANIFEST",
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
        None,
        None,
    ),
    (
        "CP76_READINESS_TEST",
        "tests/unit/test_manuscript_v3_submission_readiness.py",
        "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc",
        None,
        None,
    ),
    (
        "CP76_READINESS_CHECKLIST",
        "research/preregistrations/cp76_manuscript_v3_submission_readiness_checklist_v1.md",
        "002aae4bdd9ccf3b80b514cea6de767a05390611fec63f416bce01cb4d8e56b4",
        None,
        None,
    ),
    (
        "D1_EVIDENCE_REGISTRATION",
        "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
        "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
        "d1c52907ba0bbb6b17cb2cb4e930d983623f39c161ad8a116afa43dccbbfa1b9",
        "record_sha256",
    ),
    (
        "D1_ATTEMPT",
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
        "acfc404eca9ed711279087861518b7e9b32dfdb5fec4aaba318b50e7b4854e14",
        "4d9bdd188be51385d08c4a7540905096ce1f4f856ee313a524542f51684bbeb6",
        "record_sha256",
    ),
    (
        "D1_DIAGNOSTIC_RECORD",
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json",
        "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
        "68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6",
        "diagnostic_record_sha256",
    ),
    (
        "D1_SUCCESS",
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json",
        "eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada",
        "54167cf673861b93db3dd6cd354f9e08796bef59ef19b08ca4b03e59c4a62105",
        "receipt_sha256",
    ),
    (
        "D1_V2_CHECKPOINT",
        "artifacts/manuscript_v3_a1_development_checkpoint_v2/capsule/artifacts/a1_campaign_v4/dc7484372d3f8a633755450bda9d70f0ed182005dba052a0fa86747ae0fe4f70.pt",
        "e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c",
        None,
        None,
    ),
    (
        "D1_V2_SUCCESS",
        "artifacts/manuscript_v3_a1_development_checkpoint_v2/success-receipt.json",
        "7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885",
        "154d64d654a4f175f07e323524782f90af29dbbb5f81c053ce0105a67dbfe747",
        "receipt_sha256",
    ),
)


class CapsuleError(RuntimeError):
    """Fail-closed static capsule error."""


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise CapsuleError("value is not canonical ASCII JSON") from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise CapsuleError(name + " is not an exact lowercase SHA-256")
    return value


def _require_exact_keys(record: Any, keys: Sequence[str], name: str) -> None:
    if type(record) is not dict or set(record) != set(keys):
        raise CapsuleError(name + " does not have the exact frozen fields")


@dataclass(frozen=True)
class TaggedCoordinateV1:
    phase: str
    phase_coordinate_ordinal: int
    seed_ordinal: int
    coordinate_tag: str
    seed: int
    accepted_example_budget: Any
    method: str

    def __post_init__(self) -> None:
        if self.phase not in {"EXACT", "PRIMARY", "CONTROLS"}:
            raise CapsuleError("tagged coordinate phase is not frozen")
        if (
            type(self.phase_coordinate_ordinal) is not int
            or self.phase_coordinate_ordinal < 0
        ):
            raise CapsuleError(
                "phase coordinate ordinal is not an exact nonnegative integer"
            )
        if (
            type(self.seed_ordinal) is not int
            or self.seed_ordinal < 0
            or self.seed_ordinal >= len(REGISTRY)
            or type(self.seed) is not int
            or self.seed != REGISTRY[self.seed_ordinal]
        ):
            raise CapsuleError("tagged coordinate seed identity changed")
        if type(self.method) is not str:
            raise CapsuleError("tagged coordinate method has the wrong exact type")
        if self.phase == "EXACT":
            if (
                self.coordinate_tag != "EXACT_SEED_METHOD"
                or self.accepted_example_budget is not None
                or self.method not in EXACT_METHODS
            ):
                raise CapsuleError("exact tagged coordinate is invalid")
        else:
            allowed = PRIMARY_METHODS if self.phase == "PRIMARY" else CONTROL_METHODS
            if (
                self.coordinate_tag != "SAMPLED_SEED_BUDGET_METHOD"
                or type(self.accepted_example_budget) is not int
                or self.accepted_example_budget not in SAMPLE_BUDGETS
                or self.method not in allowed
            ):
                raise CapsuleError("sampled tagged coordinate is invalid")
        if self.phase == "EXACT":
            expected_ordinal = self.seed_ordinal * len(
                EXACT_METHODS
            ) + EXACT_METHODS.index(self.method)
        elif self.phase == "PRIMARY":
            expected_ordinal = (
                self.seed_ordinal * len(SAMPLE_BUDGETS) * len(PRIMARY_METHODS)
                + SAMPLE_BUDGETS.index(self.accepted_example_budget)
                * len(PRIMARY_METHODS)
                + PRIMARY_METHODS.index(self.method)
            )
        else:
            expected_ordinal = (
                self.seed_ordinal * len(SAMPLE_BUDGETS) * len(CONTROL_METHODS)
                + SAMPLE_BUDGETS.index(self.accepted_example_budget)
                * len(CONTROL_METHODS)
                + CONTROL_METHODS.index(self.method)
            )
        if self.phase_coordinate_ordinal != expected_ordinal:
            raise CapsuleError("phase coordinate ordinal is not the frozen derivation")

    def to_record(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "phase_coordinate_ordinal": self.phase_coordinate_ordinal,
            "seed_ordinal": self.seed_ordinal,
            "coordinate_tag": self.coordinate_tag,
            "seed": self.seed,
            "accepted_example_budget": self.accepted_example_budget,
            "method": self.method,
        }

    def underlying_request_projection(self) -> Sequence[Any]:
        if self.phase == "EXACT":
            return [self.seed, self.method]
        return [self.seed, self.accepted_example_budget, self.method]

    @classmethod
    def from_record(cls, value: Any) -> "TaggedCoordinateV1":
        keys = (
            "phase",
            "phase_coordinate_ordinal",
            "seed_ordinal",
            "coordinate_tag",
            "seed",
            "accepted_example_budget",
            "method",
        )
        _require_exact_keys(value, keys, "tagged coordinate")
        return cls(**value)


@dataclass(frozen=True)
class PhaseEventV1:
    event_ordinal: int
    event_tag: str
    phase: str
    phase_coordinate_count: int
    phase_coordinate_manifest_sha256: Any
    prior_primary_coordinate_count: int
    prior_primary_coordinate_manifest_sha256: Any
    complete_sampled_coordinate_count: int
    complete_sampled_coordinate_manifest_sha256: Any
    primary_metrics_barrier_required: bool

    def __post_init__(self) -> None:
        if type(self.event_ordinal) is not int or self.event_ordinal < 0:
            raise CapsuleError("phase event ordinal is invalid")
        if type(self.event_tag) is not str or type(self.phase) is not str:
            raise CapsuleError("phase event tag has the wrong exact type")
        for name in (
            "phase_coordinate_count",
            "prior_primary_coordinate_count",
            "complete_sampled_coordinate_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise CapsuleError("phase event count has the wrong exact type")
        if type(self.primary_metrics_barrier_required) is not bool:
            raise CapsuleError("phase event barrier flag has the wrong exact type")
        for name in (
            "phase_coordinate_manifest_sha256",
            "prior_primary_coordinate_manifest_sha256",
            "complete_sampled_coordinate_manifest_sha256",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_sha256(value, name)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


class StaticOverlaySourceFreezeQualification:
    """Immutable proof that the sidecar matched a fresh static custody audit."""

    __slots__ = ("_canonical_snapshot", "_record_sha256")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("qualification is constructed only by the supported loader")

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    def snapshot(self) -> Dict[str, Any]:
        value = json.loads(self._canonical_snapshot.decode("ascii"))
        if type(value) is not dict:
            raise CapsuleError("verified qualification snapshot changed type")
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("static source-freeze qualification is immutable")


def _stat_identity(value: Any) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _ancestor_directory_identities(
    path: Path,
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    rows = []
    for ancestor in reversed(path.absolute().parents):
        information = ancestor.lstat()
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise CapsuleError("custody path has a symlink or nondirectory ancestor")
        rows.append((str(ancestor), _stat_identity(information)))
    return tuple(rows)


def _existing_ancestor_directory_identities(
    path: Path,
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    """Bind the existing nonsymlink prefix of a possibly absent path."""

    rows = []
    for ancestor in reversed(path.absolute().parents):
        try:
            information = ancestor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise CapsuleError("custody path has a symlink or nondirectory ancestor")
        rows.append((str(ancestor), _stat_identity(information)))
    return tuple(rows)


def _read_stable_regular_file(path: Path) -> Tuple[bytes, Any]:
    ancestors_before = _ancestor_directory_identities(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise CapsuleError("bound source is not a nonsymlink regular file")
    payload = path.read_bytes()
    after = path.lstat()
    ancestors_after = _ancestor_directory_identities(path)
    if ancestors_before != ancestors_after:
        raise CapsuleError("bound source ancestor changed while being read")
    if _stat_identity(before) != _stat_identity(after):
        raise CapsuleError("bound source changed while being read")
    if len(payload) != after.st_size:
        raise CapsuleError("bound source length changed while being read")
    return payload, after


def _require_absent_no_entry(path: Path) -> None:
    ancestors_before = _existing_ancestor_directory_identities(path)
    try:
        path.lstat()
    except FileNotFoundError:
        if ancestors_before != _existing_ancestor_directory_identities(path):
            raise CapsuleError("required-absent path ancestor changed")
        return
    raise CapsuleError("required-absent path has an entry")


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _module_name(relative_path: str) -> str:
    prefix = "src/"
    if not relative_path.startswith(prefix) or not relative_path.endswith(".py"):
        raise CapsuleError("source path is not a Python module")
    value = relative_path[len(prefix) : -3].replace("/", ".")
    return value[: -len(".__init__")] if value.endswith(".__init__") else value


def _module_candidate_paths(module_name: str) -> Tuple[str, str]:
    stem = "src/" + module_name.replace(".", "/")
    return stem + ".py", stem + "/__init__.py"


def _ancestor_package_paths(relative_path: str) -> Tuple[str, ...]:
    parts = relative_path.split("/")
    ancestors = []
    for index in range(1, len(parts) - 1):
        candidate = "/".join(parts[: index + 1]) + "/__init__.py"
        ancestors.append(candidate)
    return tuple(ancestors)


def _resolved_local_imports(
    root: Path, importer_path: str, tree: ast.AST, allowed: Mapping[str, str]
) -> Tuple[str, ...]:
    importer_module = _module_name(importer_path)
    package_parts = importer_module.split(".")
    if not importer_path.endswith("/__init__.py"):
        package_parts = package_parts[:-1]
    found = set()

    def register(module_name: str) -> None:
        if not module_name.startswith("heterodiff"):
            return
        candidates = _module_candidate_paths(module_name)
        existing = [
            candidate for candidate in candidates if _path_has_entry(root / candidate)
        ]
        if module_name in allowed:
            found.add(allowed[module_name])
            return
        if existing:
            raise CapsuleError(
                "local import resolves outside the closed allowlist: " + module_name
            )
        raise CapsuleError(
            "heterodiff import does not resolve to a frozen source: " + module_name
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("heterodiff"):
                    register(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level > len(package_parts) + 1:
                    raise CapsuleError("relative import escapes the package")
                base_parts = package_parts[: len(package_parts) - node.level + 1]
                if node.module:
                    base_parts.extend(node.module.split("."))
                module_name = ".".join(base_parts)
            else:
                module_name = node.module or ""
            if not module_name.startswith("heterodiff"):
                continue
            register(module_name)
            for alias in node.names:
                if alias.name == "*":
                    continue
                child = module_name + "." + alias.name
                candidates = _module_candidate_paths(child)
                if child in allowed or any(
                    _path_has_entry(root / value) for value in candidates
                ):
                    register(child)
    return tuple(sorted(found))


def _assert_static_import_closure(root: Path) -> Tuple[Dict[str, str], ...]:
    if tuple(sorted(BASE_SOURCE_PATHS)) != BASE_SOURCE_PATHS:
        raise CapsuleError("base source paths are not lexically sorted")
    if len(BASE_SOURCE_PATHS) != 45 or len(set(BASE_SOURCE_PATHS)) != 45:
        raise CapsuleError("base source allowlist is not the frozen 45-path set")
    if _sha256(_canonical_json(list(BASE_SOURCE_PATHS))) != BASE_SOURCE_PATHS_SHA256:
        raise CapsuleError("base source path-list identity changed")
    expected_paths = tuple(row[0] for row in BASE_SOURCE_EXPECTATIONS)
    if expected_paths != BASE_SOURCE_PATHS:
        raise CapsuleError("base source expectations do not match the allowlist")
    for relative_path, expected_bytes, expected_sha256 in BASE_SOURCE_EXPECTATIONS:
        payload, _ = _read_stable_regular_file(root / relative_path)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha256:
            raise CapsuleError("frozen base source bytes changed")
    if set(DENYLISTED_DEVELOPMENT_SOURCES) & set(BASE_SOURCE_PATHS):
        raise CapsuleError("development source entered the candidate allowlist")
    path_by_module = {_module_name(path): path for path in BASE_SOURCE_PATHS}
    if len(path_by_module) != len(BASE_SOURCE_PATHS):
        raise CapsuleError("source allowlist has duplicate module identities")
    required = set(IMPORT_CLOSURE_ROOTS)
    for path in tuple(required):
        required.update(_ancestor_package_paths(path))
    edges = set()
    pending = list(sorted(required))
    while pending:
        importer = pending.pop(0)
        if importer not in BASE_SOURCE_PATHS:
            raise CapsuleError("import closure requires an unfrozen source")
        payload, _ = _read_stable_regular_file(root / importer)
        try:
            tree = ast.parse(payload, filename=importer)
        except SyntaxError as error:
            raise CapsuleError("candidate source is not valid Python syntax") from error
        for imported in _resolved_local_imports(root, importer, tree, path_by_module):
            edges.add((importer, imported))
            additions = {imported, *_ancestor_package_paths(imported)} - required
            if additions:
                required.update(additions)
                pending.extend(sorted(additions))
    if required != set(BASE_SOURCE_PATHS):
        missing = sorted(required - set(BASE_SOURCE_PATHS))
        extra = sorted(set(BASE_SOURCE_PATHS) - required)
        raise CapsuleError(
            "explicit source allowlist is not the exact root closure; missing=%r extra=%r"
            % (missing, extra)
        )
    return tuple(
        {"importer_path": importer, "imported_path": imported}
        for importer, imported in sorted(edges)
    )


def _dynamic_import_inventory(root: Path) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for importer_path in BASE_SOURCE_PATHS:
        payload, _ = _read_stable_regular_file(root / importer_path)
        try:
            tree = ast.parse(payload, filename=importer_path)
        except SyntaxError as error:
            raise CapsuleError("candidate source is not valid Python syntax") from error
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                call_kind = "__import__"
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
                and node.func.attr == "import_module"
            ):
                call_kind = "importlib.import_module"
            else:
                continue
            target = None
            if (
                node.args
                and isinstance(node.args[0], ast.Constant)
                and type(node.args[0].value) is str
            ):
                target = node.args[0].value
            local_path = None
            if target is not None and target.startswith("heterodiff"):
                candidates = _module_candidate_paths(target)
                matches = [
                    candidate
                    for candidate in candidates
                    if _path_has_entry(root / candidate)
                ]
                if len(matches) != 1:
                    raise CapsuleError("dynamic local import target is ambiguous")
                local_path = matches[0]
            rows.append(
                {
                    "importer_path": importer_path,
                    "call_kind": call_kind,
                    "literal_target": target,
                    "local_target_path": local_path,
                    "admitted_by_static_source_closure": (
                        local_path in BASE_SOURCE_PATHS
                        if local_path is not None
                        else False
                    ),
                }
            )
    actual = tuple(rows)
    if actual != EXPECTED_DYNAMIC_IMPORT_SITES:
        raise CapsuleError("dynamic import inventory changed")
    return actual


def _overlay_rule_sha256(rule: Mapping[str, Any]) -> str:
    return _sha256(OVERLAY_RULE_DOMAIN + _canonical_json(rule))


def _apply_overlay(payload: bytes, rule: Mapping[str, Any]) -> bytes:
    prefix = rule["assignment_prefix_utf8"].encode("ascii")
    old = rule["old_literal_utf8"].encode("ascii")
    new = rule["new_literal_utf8"].encode("ascii")
    if payload.count(prefix) != rule["required_assignment_occurrences"]:
        raise CapsuleError("overlay assignment occurrence count changed")
    start = payload.find(prefix) + len(prefix)
    if start < len(prefix) or payload[start : start + len(old)] != old:
        raise CapsuleError("overlay literal is not at the frozen assignment position")
    virtual = payload[:start] + new + payload[start + len(old) :]
    if virtual.count(prefix + new) != rule["required_literal_replacements"]:
        raise CapsuleError("overlay replacement count is not exact")
    if (
        virtual[:start] != payload[:start]
        or virtual[start + len(new) :] != payload[start + len(old) :]
    ):
        raise CapsuleError("overlay changed bytes outside the one literal")
    return virtual


def _module_assignment_tuple(payload: bytes, name: str, path: str) -> Tuple[int, ...]:
    try:
        tree = ast.parse(payload, filename=path)
    except SyntaxError as error:
        raise CapsuleError("overlay output is not valid Python syntax") from error
    matches = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            try:
                value = ast.literal_eval(node.value)
            except (TypeError, ValueError) as error:
                raise CapsuleError("overlaid seed assignment is not literal") from error
            matches.append(value)
    if len(matches) != 1 or type(matches[0]) is not tuple:
        raise CapsuleError("overlaid seed assignment is not an exact tuple")
    if any(type(value) is not int for value in matches[0]):
        raise CapsuleError("overlaid seed tuple contains a non-integer")
    return matches[0]


def _expected_file_rows(
    root: Path, expectations: Sequence[Sequence[Any]], *, roster: str
) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for ordinal, item in enumerate(expectations):
        if len(item) == 3:
            relative_path, expected_bytes, expected_sha256 = item
            role = "BASE_MODULE_SOURCE"
        elif len(item) == 4:
            role, relative_path, expected_bytes, expected_sha256 = item
        else:
            raise CapsuleError("file expectation row has the wrong arity")
        if (
            type(role) is not str
            or type(relative_path) is not str
            or type(expected_bytes) is not int
            or type(expected_sha256) is not str
        ):
            raise CapsuleError("file expectation row has the wrong exact types")
        payload, information = _read_stable_regular_file(root / relative_path)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha256:
            raise CapsuleError("frozen file identity changed")
        rows.append(
            {
                "ordinal": ordinal,
                "role": role,
                "path": relative_path,
                "raw_sha256": expected_sha256,
                "bytes": expected_bytes,
                "mode_octal": format(stat.S_IMODE(information.st_mode), "04o"),
                "is_regular_file": True,
                "is_symlink": False,
                "roster": roster,
                "execution_admissible": False,
            }
        )
    return tuple(rows)


def _registry_semantics(root: Path) -> Dict[str, Any]:
    path = root / (
        "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1/"
        "replacement-seed-registry.json"
    )
    payload, _ = _read_stable_regular_file(path)
    if _sha256(payload) != REGISTRY_RAW_SHA256:
        raise CapsuleError("replacement registry raw identity changed")
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CapsuleError("replacement registry is not ASCII JSON") from error
    if type(record) is not dict:
        raise CapsuleError("replacement registry is not an object")
    if record.get("record_sha256") != REGISTRY_RECORD_SHA256:
        raise CapsuleError("replacement registry self identity changed")
    values = record.get("replacement_seed_registry")
    if type(values) is not list or any(type(value) is not int for value in values):
        raise CapsuleError("replacement registry has the wrong exact types")
    if tuple(values) != REGISTRY:
        raise CapsuleError("replacement registry differs from the frozen registry")
    if (
        any(
            type(value) is not int or value < 0 or value >= 2**53
            for value in REGISTRY
        )
        or len(set(REGISTRY)) != 8
        or REGISTRY[1:] != (3253, 5003, 7411, 10007, 13007, 16001, 20011)
    ):
        raise CapsuleError("frozen registry invariants changed")
    if (
        record.get("replacement_ordinal") != 0
        or type(record.get("replacement_ordinal")) is not int
        or record.get("replacement_seed") != REGISTRY[0]
        or type(record.get("replacement_seed")) is not int
        or record.get("registry_length") != 8
        or type(record.get("registry_length")) is not int
        or record.get("registry_unique") is not True
    ):
        raise CapsuleError("replacement registry invariants changed")
    return {
        "path": (
            "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1/"
            "replacement-seed-registry.json"
        ),
        "raw_sha256": REGISTRY_RAW_SHA256,
        "record_sha256": REGISTRY_RECORD_SHA256,
        "replacement_seed_registry": list(REGISTRY),
        "semantic_equality_verified": True,
    }


def _deferred_runtime_boundary(root: Path) -> Dict[str, Any]:
    rows = _expected_file_rows(
        root, DEFERRED_RUNTIME_SOURCE_EXPECTATIONS, roster="DEFERRED_RUNTIME_SOURCE"
    )
    return {
        "deferred_source_rows": list(rows),
        "deferred_source_count": 2,
        "known_local_chain": [
            {
                "from_path": (
                    "src/heterodiff/experiments/finite_association_runtime_identity.py"
                ),
                "mechanism": "importlib.import_module_LITERAL",
                "to_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
            },
            {
                "from_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
                "mechanism": "NORMAL_IMPORT_FROM",
                "to_path": (
                    "src/heterodiff/experiments/"
                    "finite_association_runtime_identity.py"
                ),
            },
            {
                "from_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
                "mechanism": "FUNCTION_LOCAL_IMPORT_FROM",
                "to_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[1][1],
            },
            {
                "from_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
                "mechanism": "FUNCTION_LOCAL_CANONICAL_SELF_IMPORT",
                "to_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
            },
            {
                "from_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[1][1],
                "mechanism": "NORMAL_IMPORT_FROM",
                "to_path": (
                    "src/heterodiff/experiments/"
                    "finite_association_runtime_identity.py"
                ),
            },
            {
                "from_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[1][1],
                "mechanism": "NORMAL_IMPORT_FROM",
                "to_path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[0][1],
            },
        ],
        "known_local_chain_count": 6,
        "runtime_loader_sites": [
            {
                "path": (
                    "src/heterodiff/experiments/finite_association_runtime_attestor.py"
                ),
                "mechanism": "importlib.util.spec_from_file_location_THEN_exec_module",
                "target_role": "RUNTIME_IDENTITY_SOURCE",
            },
            {
                "path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[1][1],
                "mechanism": "importlib.util.spec_from_file_location_THEN_exec_module",
                "target_role": "RUNTIME_IDENTITY_SOURCE",
            },
            {
                "path": DEFERRED_RUNTIME_SOURCE_EXPECTATIONS[1][1],
                "mechanism": "importlib.import_module_VARIABLE_EXTERNAL_MODULE_NAMES",
                "target_role": "EXTERNAL_NUMERICAL_RUNTIME_MODULES",
            },
        ],
        "dynamic_runtime_closure_complete": False,
        "production_execution_import_closure_complete": False,
        "execution_admissible": False,
    }


def virtual_source_manifest(workspace_root: Any) -> Dict[str, Any]:
    root = Path(workspace_root).resolve(strict=True)
    edges = _assert_static_import_closure(root)
    dynamic_imports = _dynamic_import_inventory(root)
    registry = _registry_semantics(root)
    deferred_runtime = _deferred_runtime_boundary(root)
    nonpackage_inputs = _expected_file_rows(
        root, NONPACKAGE_SOURCE_EXPECTATIONS, roster="NONPACKAGE_CANDIDATE_INPUT"
    )
    rules_by_path = {rule["path"]: rule for rule in OVERLAY_RULES}
    if len(rules_by_path) != 5 or not set(rules_by_path) <= set(BASE_SOURCE_PATHS):
        raise CapsuleError("overlay rules are not the frozen five-source subset")
    expected_by_path = {
        path: (expected_bytes, expected_sha256)
        for path, expected_bytes, expected_sha256 in BASE_SOURCE_EXPECTATIONS
    }
    rows = []
    for ordinal, relative_path in enumerate(BASE_SOURCE_PATHS):
        payload, _ = _read_stable_regular_file(root / relative_path)
        expected_bytes, expected_sha256 = expected_by_path[relative_path]
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha256:
            raise CapsuleError("base source differs from its frozen identity")
        rule = rules_by_path.get(relative_path)
        virtual = payload if rule is None else _apply_overlay(payload, rule)
        if rule is not None:
            if (
                _module_assignment_tuple(virtual, rule["constant_name"], relative_path)
                != REGISTRY
            ):
                raise CapsuleError("overlaid seed tuple differs from the registry")
        rows.append(
            {
                "ordinal": ordinal,
                "path": relative_path,
                "bytes": len(virtual),
                "base_raw_sha256": _sha256(payload),
                "virtual_raw_sha256": _sha256(virtual),
                "source_kind": (
                    "UNCHANGED_BASE" if rule is None else "ONE_LITERAL_OVERLAY"
                ),
                "overlay_rule_sha256": (
                    None if rule is None else _overlay_rule_sha256(rule)
                ),
                "registry_semantic_equality_verified": rule is not None,
                "execution_admissible": False,
            }
        )
    if len(rows) != 45:
        raise CapsuleError(
            "virtual scientific source manifest does not contain 45 rows"
        )
    _require_absent_no_entry(root / PLANNED_ADAPTER_TARGET)
    body = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "closure_kind": "PREACTIVATION_MODULE_LOAD_STATIC_CLOSURE",
        "ordering": "LEXICALLY_SORTED_45_BASE_PATHS",
        "admission_policy": "EXPLICIT_STATIC_ALLOWLIST_ONLY_NO_GLOB_OR_RGLOB",
        "base_path_count": 45,
        "overlay_row_count": 5,
        "row_count": 45,
        "base_path_list_sha256": BASE_SOURCE_PATHS_SHA256,
        "static_import_edges": list(edges),
        "static_import_edge_count": len(edges),
        "import_closure_roots": list(IMPORT_CLOSURE_ROOTS),
        "all_reachable_package_initializers_parsed": True,
        "dynamic_discovery_used_for_admission": False,
        "dynamic_import_sites": list(dynamic_imports),
        "dynamic_import_site_count": len(dynamic_imports),
        "deferred_runtime_boundary": deferred_runtime,
        "nonpackage_candidate_inputs": list(nonpackage_inputs),
        "nonpackage_candidate_input_count": 3,
        "registry_semantics": registry,
        "planned_adapter_target": PLANNED_ADAPTER_TARGET,
        "planned_adapter_target_lstat_absent": True,
        "static_audit_module_path": STATIC_AUDIT_MODULE_PATH,
        "static_audit_module_is_not_a_runtime_adapter": True,
        "virtual_adapter_row_present": False,
        "production_execution_import_closure_complete": False,
        "rows": rows,
    }
    return {
        **body,
        "manifest_sha256": _sha256(SOURCE_MANIFEST_DOMAIN + _canonical_json(body)),
    }


def _coordinate_manifest(
    phase: str, coordinates: Sequence[TaggedCoordinateV1], ordering: str
) -> Dict[str, Any]:
    records = [
        {
            "manifest_ordinal": manifest_ordinal,
            "manifest_ordinal_domain": phase,
            **coordinate.to_record(),
        }
        for manifest_ordinal, coordinate in enumerate(coordinates)
    ]
    projections = [
        list(coordinate.underlying_request_projection()) for coordinate in coordinates
    ]
    tags = sorted({coordinate.coordinate_tag for coordinate in coordinates})
    body = {
        "schema": COORDINATE_MANIFEST_SCHEMA,
        "phase": phase,
        "coordinate_shape": ["seed", "accepted_example_budget", "method"],
        "tagged_coordinate_fields": [
            "phase",
            "phase_coordinate_ordinal",
            "seed_ordinal",
            "coordinate_tag",
            "seed",
            "accepted_example_budget",
            "method",
        ],
        "coordinate_tags": tags,
        "coordinate_count": len(records),
        "manifest_ordinal_fields": [
            "manifest_ordinal",
            "manifest_ordinal_domain",
        ],
        "ordering": ordering,
        "coordinates": records,
        "underlying_request_projections": projections,
        "exact_wrapper_projection_shape": ["seed", "method"],
        "sampled_wrapper_projection_shape": [
            "seed",
            "accepted_example_budget",
            "method",
        ],
        "wrapper_projection_is_frozen": True,
    }
    return {
        **body,
        "manifest_sha256": _sha256(COORDINATE_MANIFEST_DOMAIN + _canonical_json(body)),
    }


def coordinate_manifests() -> Dict[str, Any]:
    exact = [
        TaggedCoordinateV1(
            phase="EXACT",
            phase_coordinate_ordinal=(
                seed_ordinal * len(EXACT_METHODS) + method_ordinal
            ),
            seed_ordinal=seed_ordinal,
            coordinate_tag="EXACT_SEED_METHOD",
            seed=seed,
            accepted_example_budget=None,
            method=method,
        )
        for seed_ordinal, seed in enumerate(REGISTRY)
        for method_ordinal, method in enumerate(EXACT_METHODS)
    ]
    primary = [
        TaggedCoordinateV1(
            phase="PRIMARY",
            phase_coordinate_ordinal=(
                seed_ordinal * len(SAMPLE_BUDGETS) * len(PRIMARY_METHODS)
                + budget_ordinal * len(PRIMARY_METHODS)
                + method_ordinal
            ),
            seed_ordinal=seed_ordinal,
            coordinate_tag="SAMPLED_SEED_BUDGET_METHOD",
            seed=seed,
            accepted_example_budget=budget,
            method=method,
        )
        for seed_ordinal, seed in enumerate(REGISTRY)
        for budget_ordinal, budget in enumerate(SAMPLE_BUDGETS)
        for method_ordinal, method in enumerate(PRIMARY_METHODS)
    ]
    controls = [
        TaggedCoordinateV1(
            phase="CONTROLS",
            phase_coordinate_ordinal=(
                seed_ordinal * len(SAMPLE_BUDGETS) * len(CONTROL_METHODS)
                + budget_ordinal * len(CONTROL_METHODS)
                + method_ordinal
            ),
            seed_ordinal=seed_ordinal,
            coordinate_tag="SAMPLED_SEED_BUDGET_METHOD",
            seed=seed,
            accepted_example_budget=budget,
            method=method,
        )
        for seed_ordinal, seed in enumerate(REGISTRY)
        for budget_ordinal, budget in enumerate(SAMPLE_BUDGETS)
        for method_ordinal, method in enumerate(CONTROL_METHODS)
    ]
    complete = []
    for seed_ordinal, seed in enumerate(REGISTRY):
        for budget in SAMPLE_BUDGETS:
            for method in PRIMARY_METHODS + CONTROL_METHODS:
                phase = "PRIMARY" if method in PRIMARY_METHODS else "CONTROLS"
                complete.append(
                    TaggedCoordinateV1(
                        phase=phase,
                        phase_coordinate_ordinal=(
                            seed_ordinal
                            * len(SAMPLE_BUDGETS)
                            * (
                                len(PRIMARY_METHODS)
                                if phase == "PRIMARY"
                                else len(CONTROL_METHODS)
                            )
                            + SAMPLE_BUDGETS.index(budget)
                            * (
                                len(PRIMARY_METHODS)
                                if phase == "PRIMARY"
                                else len(CONTROL_METHODS)
                            )
                            + (
                                PRIMARY_METHODS.index(method)
                                if phase == "PRIMARY"
                                else CONTROL_METHODS.index(method)
                            )
                        ),
                        seed_ordinal=seed_ordinal,
                        coordinate_tag="SAMPLED_SEED_BUDGET_METHOD",
                        seed=seed,
                        accepted_example_budget=budget,
                        method=method,
                    )
                )
    phase_schedule = exact + primary + controls
    all_aggregate = exact + complete
    if len(exact) != 24 or len(primary) != 48 or len(controls) != 72:
        raise CapsuleError("phase coordinate count changed")
    if len(complete) != 120 or len(phase_schedule) != 144 or len(all_aggregate) != 144:
        raise CapsuleError("aggregate coordinate count changed")
    if phase_schedule == all_aggregate:
        raise CapsuleError("phase schedule was conflated with aggregate identity order")
    manifests = {
        "exact": _coordinate_manifest(
            "EXACT", exact, "SEED_ORDINAL_THEN_EXACT_METHOD_ORDINAL"
        ),
        "primary": _coordinate_manifest(
            "PRIMARY",
            primary,
            "SEED_ORDINAL_THEN_BUDGET_ORDINAL_THEN_PRIMARY_METHOD_ORDINAL",
        ),
        "controls": _coordinate_manifest(
            "CONTROLS",
            controls,
            "SEED_ORDINAL_THEN_BUDGET_ORDINAL_THEN_CONTROL_METHOD_ORDINAL",
        ),
        "complete_sampled": _coordinate_manifest(
            "COMPLETE_SAMPLED",
            complete,
            "SEED_ORDINAL_THEN_BUDGET_ORDINAL_THEN_INTERLEAVED_METHOD_ORDINAL",
        ),
        "execution_phase_schedule": _coordinate_manifest(
            "EXECUTION_PHASE_SCHEDULE_EXACT_PRIMARY_CONTROLS",
            phase_schedule,
            "EXACT_THEN_PRIMARY_THEN_CONTROLS_WITH_PRIMARY_METRICS_BARRIER",
        ),
        "all_aggregate": _coordinate_manifest(
            "ALL_AGGREGATE_EXACT_COMPLETE_SAMPLED",
            all_aggregate,
            "EXACT_THEN_COMPLETE_SAMPLED_INTERLEAVED",
        ),
    }
    events = (
        PhaseEventV1(0, "RANK_GATE", "RANK", 0, None, 0, None, 0, None, False),
        PhaseEventV1(
            1,
            "COORDINATE_PHASE",
            "EXACT",
            24,
            manifests["exact"]["manifest_sha256"],
            0,
            None,
            0,
            None,
            False,
        ),
        PhaseEventV1(
            2,
            "COORDINATE_PHASE",
            "PRIMARY",
            48,
            manifests["primary"]["manifest_sha256"],
            0,
            None,
            0,
            None,
            False,
        ),
        PhaseEventV1(
            3,
            "PRIMARY_METRICS_BARRIER",
            "PRIMARY_METRICS",
            0,
            None,
            48,
            manifests["primary"]["manifest_sha256"],
            0,
            None,
            True,
        ),
        PhaseEventV1(
            4,
            "COORDINATE_PHASE",
            "CONTROLS",
            72,
            manifests["controls"]["manifest_sha256"],
            48,
            manifests["primary"]["manifest_sha256"],
            120,
            manifests["complete_sampled"]["manifest_sha256"],
            True,
        ),
    )
    event_body = {
        "schema": PHASE_EVENT_SCHEMA,
        "event_order": [
            "RANK",
            "EXACT",
            "PRIMARY",
            "PRIMARY_METRICS",
            "CONTROLS",
        ],
        "events": [event.to_record() for event in events],
        "event_count": 5,
        "issues_authority": False,
    }
    return {
        "registry": list(REGISTRY),
        "registry_length": 8,
        "registry_unique": True,
        "replacement_ordinal": 0,
        "exposed_seed": EXPOSED_SEED,
        "registry_sha256": _sha256(REGISTRY_DOMAIN + _canonical_json(list(REGISTRY))),
        "coordinate_manifest_schema": COORDINATE_MANIFEST_SCHEMA,
        "coordinate_manifest_digest_domain_encoding": {
            "ascii_label": COORDINATE_MANIFEST_SCHEMA,
            "terminating_nul_hex": "00",
            "exact_prefix_hex": COORDINATE_MANIFEST_DOMAIN.hex(),
        },
        "phase_schedule_has_primary_metrics_barrier": True,
        "complete_sampled_interleaves_primary_and_controls_by_seed_budget": True,
        "phase_schedule_and_aggregate_order_are_distinct": True,
        "manifests": manifests,
        "phase_event_schedule": {
            **event_body,
            "schedule_sha256": _sha256(
                PHASE_EVENT_DOMAIN + _canonical_json(event_body)
            ),
        },
    }


def _governance_roster(root: Path) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for ordinal, (role, relative_path, raw_sha256, semantic, semantic_key) in enumerate(
        GOVERNANCE_BINDINGS
    ):
        payload, information = _read_stable_regular_file(root / relative_path)
        if _sha256(payload) != raw_sha256:
            raise CapsuleError("governance custody hash changed")
        if semantic is not None:
            try:
                value = json.loads(payload.decode("ascii"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise CapsuleError(
                    "semantic custody record is not ASCII JSON"
                ) from error
            if type(value) is not dict or value.get(semantic_key) != semantic:
                raise CapsuleError("governance semantic custody changed")
        rows.append(
            {
                "ordinal": ordinal,
                "role": role,
                "path": relative_path,
                "raw_sha256": raw_sha256,
                "semantic_sha256": semantic,
                "bytes": len(payload),
                "mode_octal": format(stat.S_IMODE(information.st_mode), "04o"),
                "is_regular_file": True,
                "is_symlink": False,
                "execution_admissible": False,
            }
        )
    return tuple(rows)


def _candidate_source_roster(
    root: Path, manifest: Mapping[str, Any]
) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for ordinal, row in enumerate(manifest["rows"]):
        _, information = _read_stable_regular_file(root / row["path"])
        materialized = row["source_kind"] == "UNCHANGED_BASE"
        mode = format(stat.S_IMODE(information.st_mode), "04o")
        rows.append(
            {
                "ordinal": ordinal,
                "role": row["source_kind"],
                "path": row["path"],
                "raw_sha256": row["base_raw_sha256"],
                "bytes": information.st_size,
                "mode_octal": mode,
                "is_regular_file": True,
                "is_symlink": False,
                "identity_kind": "BASE_CUSTODY",
                "base_path": row["path"],
                "base_raw_sha256": row["base_raw_sha256"],
                "base_bytes": information.st_size,
                "base_mode_octal": mode,
                "base_present": True,
                "base_is_regular_file": True,
                "base_is_symlink": False,
                "virtual_target_path": row["path"],
                "virtual_raw_sha256": row["virtual_raw_sha256"],
                "virtual_bytes": row["bytes"],
                "virtual_materialized": materialized,
                "candidate_kind": "PYTHON_MODULE",
                "execution_admissible": False,
            }
        )
    for input_row in manifest["nonpackage_candidate_inputs"]:
        rows.append(
            {
                "ordinal": len(rows),
                "role": input_row["role"],
                "path": input_row["path"],
                "raw_sha256": input_row["raw_sha256"],
                "bytes": input_row["bytes"],
                "mode_octal": input_row["mode_octal"],
                "is_regular_file": True,
                "is_symlink": False,
                "source_materialized_at_target": True,
                "source_from_path": input_row["path"],
                "candidate_kind": "NONPACKAGE_SOURCE_INPUT",
                "execution_admissible": False,
            }
        )
    return tuple(rows)


def _runtime_input_roster(root: Path) -> Tuple[Dict[str, Any], ...]:
    roles = (
        ("SUCCESSOR_RUNTIME_IDENTITY", SUCCESSOR_RUNTIME_PATHS[0]),
        ("SUCCESSOR_RUNTIME_APPROVAL", SUCCESSOR_RUNTIME_PATHS[1]),
        ("LEGACY_RUNTIME_IDENTITY_DENIED", LEGACY_RUNTIME_PATH),
        ("LEGACY_RUNTIME_APPROVAL_DENIED", LEGACY_RUNTIME_APPROVAL_PATH),
        ("LEGACY_RUNTIME_CANDIDATE_ROOT_DENIED", LEGACY_RUNTIME_CANDIDATE_ROOT),
    )
    rows = [
        {
            **row,
            "present": True,
            "approved": False,
        }
        for row in _expected_file_rows(
            root,
            DEFERRED_RUNTIME_SOURCE_EXPECTATIONS,
            roster="DEFERRED_RUNTIME_SOURCE",
        )
    ]
    for role, relative_path in roles:
        _require_absent_no_entry(root / relative_path)
        rows.append(
            {
                "ordinal": len(rows),
                "role": role,
                "path": relative_path,
                "raw_sha256": None,
                "bytes": None,
                "mode_octal": None,
                "is_regular_file": False,
                "is_symlink": False,
                "present": False,
                "approved": False,
                "execution_admissible": False,
            }
        )
    return tuple(rows)


_PHASE_APIS = {
    "RANK": {
        "coordinate_manifest_key": None,
        "legacy_request_type": None,
        "launcher_module": "heterodiff.experiments.finite_association_rank_stress",
        "launcher_qualname": "launch_association_rank_stress_gate",
        "loader_module": "heterodiff.experiments.finite_association_rank_stress",
        "loader_qualname": "load_association_rank_stress_gate_result",
        "revalidator_module": "heterodiff.experiments.finite_association_rank_stress",
        "revalidator_qualname": (
            "LoaderVerifiedAssociationRankStressGateResult.revalidate_prepared_custody"
        ),
        "result_type": "LoaderVerifiedAssociationRankStressGateResult",
    },
    "EXACT": {
        "coordinate_manifest_key": "exact",
        "legacy_request_type": "FrozenExactPopulationRunRequest",
        "launcher_module": (
            "heterodiff.experiments.finite_association_exact_population_isolated_runner"
        ),
        "launcher_qualname": "launch_frozen_exact_population_run",
        "loader_module": (
            "heterodiff.experiments.finite_association_exact_population_isolated_runner"
        ),
        "loader_qualname": "load_completed_frozen_exact_population_campaign",
        "revalidator_module": (
            "heterodiff.experiments.finite_association_exact_population_isolated_runner"
        ),
        "revalidator_qualname": "revalidate_completed_frozen_exact_population_diagnostic",
        "result_type": "LedgerVerifiedExactPopulationDiagnostic",
    },
    "PRIMARY": {
        "coordinate_manifest_key": "primary",
        "legacy_request_type": "FrozenAssociationSampledRunRequest",
        "launcher_module": "heterodiff.experiments.finite_association_isolated_runner",
        "launcher_qualname": "launch_frozen_association_sampled_run",
        "loader_module": "heterodiff.experiments.finite_association_isolated_runner",
        "loader_qualname": "load_completed_frozen_association_primary_success_set",
        "revalidator_module": (
            "heterodiff.experiments.finite_association_isolated_runner"
        ),
        "revalidator_qualname": "revalidate_completed_frozen_association_primary_success_set",
        "result_type": "LedgerVerifiedFrozenAssociationPrimarySuccessSet",
    },
    "CONTROLS": {
        "coordinate_manifest_key": "controls",
        "legacy_request_type": "FrozenAssociationSampledRunRequest",
        "launcher_module": "heterodiff.experiments.finite_association_isolated_runner",
        "launcher_qualname": "launch_frozen_association_sampled_run",
        "loader_module": "heterodiff.experiments.finite_association_isolated_runner",
        "loader_qualname": "load_completed_frozen_association_sampled_campaign",
        "revalidator_module": (
            "heterodiff.experiments.finite_association_isolated_runner"
        ),
        "revalidator_qualname": "revalidate_completed_frozen_association_sampled_campaign",
        "result_type": "LedgerVerifiedFrozenAssociationSampledCampaign",
    },
}


def _virtual_row_by_module(manifest: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {_module_name(row["path"]): row for row in manifest["rows"]}


def _definition_for_qualname(tree: ast.Module, qualname: str) -> ast.AST:
    current = list(tree.body)
    found = None
    for part in qualname.split("."):
        matches = [
            node
            for node in current
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == part
        ]
        if len(matches) != 1:
            raise CapsuleError("bound API qualname is not an exact source definition")
        found = matches[0]
        current = list(found.body) if isinstance(found, ast.ClassDef) else []
    if found is None:
        raise CapsuleError("bound API qualname is empty")
    return found


def _api_signature(root: Path, module_name: str, qualname: str) -> Dict[str, Any]:
    paths = [path for path in BASE_SOURCE_PATHS if _module_name(path) == module_name]
    if len(paths) != 1:
        raise CapsuleError("bound API module is not an exact candidate source")
    relative_path = paths[0]
    payload, _ = _read_stable_regular_file(root / relative_path)
    try:
        tree = ast.parse(payload, filename=relative_path)
    except SyntaxError as error:
        raise CapsuleError("bound API source is not valid Python") from error
    definition = _definition_for_qualname(tree, qualname)
    if not isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise CapsuleError("bound API qualname is not callable source")
    arguments = definition.args

    def argument_record(argument: ast.arg) -> Dict[str, Any]:
        return {
            "name": argument.arg,
            "annotation_ast": (
                None
                if argument.annotation is None
                else ast.dump(argument.annotation, include_attributes=False)
            ),
        }

    body = {
        "module": module_name,
        "qualname": qualname,
        "definition_kind": type(definition).__name__,
        "positional_only": [argument_record(value) for value in arguments.posonlyargs],
        "positional_or_keyword": [argument_record(value) for value in arguments.args],
        "keyword_only": [argument_record(value) for value in arguments.kwonlyargs],
        "vararg": None
        if arguments.vararg is None
        else argument_record(arguments.vararg),
        "kwarg": None if arguments.kwarg is None else argument_record(arguments.kwarg),
        "positional_default_count": len(arguments.defaults),
        "keyword_default_presence": [
            value is not None for value in arguments.kw_defaults
        ],
        "return_annotation_ast": (
            None
            if definition.returns is None
            else ast.dump(definition.returns, include_attributes=False)
        ),
    }
    return {
        **body,
        "signature_sha256": _sha256(
            b"heterodiff-r1-registry-aware-api-signature-v1\0" + _canonical_json(body)
        ),
    }


def _assert_class_symbol(root: Path, module_name: str, qualname: str) -> None:
    paths = [path for path in BASE_SOURCE_PATHS if _module_name(path) == module_name]
    if len(paths) != 1:
        raise CapsuleError("bound result module is not exact")
    payload, _ = _read_stable_regular_file(root / paths[0])
    tree = ast.parse(payload, filename=paths[0])
    if not isinstance(_definition_for_qualname(tree, qualname), ast.ClassDef):
        raise CapsuleError("bound result type is not a class")


def runner_api_inventory_rows(
    root: Path, manifest: Mapping[str, Any], coordinates: Mapping[str, Any]
) -> Tuple[Dict[str, Any], ...]:
    """Describe bound legacy APIs without qualifying a successor binder."""

    by_module = _virtual_row_by_module(manifest)
    rows = []
    for phase in ("RANK", "EXACT", "PRIMARY", "CONTROLS"):
        api = _PHASE_APIS[phase]
        key = api["coordinate_manifest_key"]
        coordinate = None if key is None else coordinates["manifests"][key]
        module_names = (
            api["launcher_module"],
            api["loader_module"],
            api["revalidator_module"],
        )
        if any(name not in by_module for name in module_names):
            raise CapsuleError("legacy API module is outside the source closure")
        launcher_signature = _api_signature(
            root, api["launcher_module"], api["launcher_qualname"]
        )
        loader_signature = _api_signature(
            root, api["loader_module"], api["loader_qualname"]
        )
        revalidator_signature = _api_signature(
            root, api["revalidator_module"], api["revalidator_qualname"]
        )
        _assert_class_symbol(root, api["loader_module"], api["result_type"])
        if api["legacy_request_type"] is not None:
            _assert_class_symbol(
                root, api["launcher_module"], api["legacy_request_type"]
            )
        rows.append(
            {
                "phase": phase,
                "coordinate_count": 0
                if coordinate is None
                else coordinate["coordinate_count"],
                "coordinate_manifest_sha256": (
                    None if coordinate is None else coordinate["manifest_sha256"]
                ),
                "legacy_request_type": api["legacy_request_type"],
                "launcher_module": api["launcher_module"],
                "launcher_qualname": api["launcher_qualname"],
                "launcher_source_sha256": by_module[api["launcher_module"]][
                    "virtual_raw_sha256"
                ],
                "launcher_api_signature": launcher_signature,
                "loader_module": api["loader_module"],
                "loader_qualname": api["loader_qualname"],
                "loader_source_sha256": by_module[api["loader_module"]][
                    "virtual_raw_sha256"
                ],
                "loader_api_signature": loader_signature,
                "revalidator_module": api["revalidator_module"],
                "revalidator_qualname": api["revalidator_qualname"],
                "revalidator_source_sha256": by_module[api["revalidator_module"]][
                    "virtual_raw_sha256"
                ],
                "revalidator_api_signature": revalidator_signature,
                "result_type": api["result_type"],
                "registry_raw_sha256": REGISTRY_RAW_SHA256,
                "registry_record_sha256": REGISTRY_RECORD_SHA256,
                "registry_semantic_sha256": coordinates["registry_sha256"],
                "all_aggregate_manifest_sha256": coordinates["manifests"][
                    "all_aggregate"
                ]["manifest_sha256"],
                "execution_phase_schedule_manifest_sha256": coordinates["manifests"][
                    "execution_phase_schedule"
                ]["manifest_sha256"],
                "phase_event_schedule_sha256": coordinates["phase_event_schedule"][
                    "schedule_sha256"
                ],
                "source_manifest_sha256": manifest["manifest_sha256"],
                "inventory_only": True,
                "successor_request_schema_frozen": False,
                "successor_completion_schema_frozen": False,
                "typed_coordinate_consumption_qualified": False,
                "phase_aggregate_admission_qualified": False,
                "legacy_api_successor_compatible": False,
                "execution_admissible": False,
                "launch_allowed": False,
                "output_admissible": False,
            }
        )
    return tuple(rows)


def _load_bound_ascii_json(
    root: Path, relative_path: str, raw_sha256: str, record_sha256: Any
) -> Dict[str, Any]:
    payload, _ = _read_stable_regular_file(root / relative_path)
    if _sha256(payload) != raw_sha256:
        raise CapsuleError("bound state record raw identity changed")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CapsuleError("bound state record is not ASCII JSON") from error
    if type(value) is not dict:
        raise CapsuleError("bound state record has the wrong exact type")
    if record_sha256 is not None and value.get("record_sha256") != record_sha256:
        raise CapsuleError("bound state record semantic identity changed")
    return value


def _preregistration_state_projection(root: Path) -> Dict[str, Any]:
    closure = _load_bound_ascii_json(
        root,
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    )
    postdraw = _load_bound_ascii_json(
        root,
        "research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.json",
        "a13e038ea5f04379a75e48e086a9e597b6217dbaae2ae39ccebae74ebdfe8db0",
        POSTDRAW_RECORD_SHA256,
    )
    current_preregistration = _load_bound_ascii_json(
        root,
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    )
    cp76_manifest = _load_bound_ascii_json(
        root,
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
        None,
    )
    nulls = closure.get("null_projection")
    blockers = closure.get("blocker_projection")
    freeze = closure.get("freeze_predicate_projection")
    if (
        type(nulls) is not dict
        or type(blockers) is not dict
        or type(freeze) is not dict
    ):
        raise CapsuleError("closure-v2 state projection has the wrong types")
    expected_nulls = {
        "historical_total_null_count": 174,
        "historical_preexecution_null_count": 168,
        "historical_deferred_postexecution_null_count": 6,
        "projected_resolved_pre_d1_null_count": 2,
        "effective_total_unresolved_null_count": 172,
        "effective_preexecution_unresolved_null_count": 166,
        "effective_deferred_postexecution_unresolved_null_count": 6,
    }
    for key, expected in expected_nulls.items():
        if type(nulls.get(key)) is not int or nulls.get(key) != expected:
            raise CapsuleError("closure-v2 null projection changed")
    expected_stage_counts = {
        "CONFIRMATORY_EXECUTION": 10,
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
    }
    if (
        type(blockers.get("effective_unresolved_blocker_count")) is not int
        or blockers.get("effective_unresolved_blocker_count") != 12
        or type(blockers.get("blockers_closed_by_closure")) is not int
        or blockers.get("blockers_closed_by_closure") != 0
        or _canonical_json(blockers.get("effective_stage_counts"))
        != _canonical_json(expected_stage_counts)
    ):
        raise CapsuleError("closure-v2 blocker projection changed")
    predicate = freeze.get("effective_predicate")
    expected_predicate = {
        "all_claim_promotion_and_submission_blockers_closed": False,
        "all_confirmatory_execution_blockers_closed": False,
        "all_required_preexecution_artifacts_present_and_hash_bound": False,
        "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull": False,
        "claim_boundary_approved": False,
        "claim_promotion_or_submission_permitted": False,
        "current_state": "DRAFT_NOT_EXECUTABLE",
        "domain_admission_complete": False,
        "freeze_receipt_present": False,
        "frozen_executable_state_if_and_only_if_execution_predicates_true": (
            "FROZEN_EXECUTABLE"
        ),
        "known_law_and_whole_method_gates_complete": False,
        "power_review_complete": False,
        "test_data_unopened_before_freeze": None,
    }
    if _canonical_json(predicate) != _canonical_json(expected_predicate):
        raise CapsuleError("closure-v2 freeze predicate changed")
    if closure.get("global_state") != "DRAFT_NOT_EXECUTABLE":
        raise CapsuleError("closure-v2 global state changed")
    if postdraw.get("global_state") != "DRAFT_NOT_EXECUTABLE":
        raise CapsuleError("postdraw global state changed")
    current_blockers = current_preregistration.get("unresolved_blockers")
    if (
        current_preregistration.get("state") != "DRAFT_NOT_EXECUTABLE"
        or current_preregistration.get(
            "required_preexecution_null_fields_are_execution_blocking"
        )
        is not True
        or type(current_blockers) is not list
        or len(current_blockers) != 12
        or any(type(row) is not dict for row in current_blockers)
        or sum(
            row.get("blocking_stage") == "CONFIRMATORY_EXECUTION"
            for row in current_blockers
        )
        != 10
        or sum(
            row.get("blocking_stage")
            == "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION"
            for row in current_blockers
        )
        != 2
        or _canonical_json(current_preregistration.get("freeze_predicate"))
        != _canonical_json(expected_predicate)
    ):
        raise CapsuleError("current authoritative preregistration state changed")
    if (
        cp76_manifest.get("readiness_status") != "NOT_READY"
        or cp76_manifest.get("manuscript_submission_ready") is not False
    ):
        raise CapsuleError("current CP76 readiness state changed")
    return {
        "historical_null_projection": {
            "total": 174,
            "preexecution": 168,
            "deferred_postexecution": 6,
        },
        "pre_d1_resolved_null_count": 2,
        "effective_unresolved_null_projection": {
            "total": 172,
            "preexecution": 166,
            "deferred_postexecution": 6,
        },
        "blockers": {
            "total": 12,
            "closed": 0,
            "remaining": 12,
            "confirmatory_execution": 10,
            "claim_promotion_and_submission": 2,
        },
        "freeze_predicate": expected_predicate,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "authoritative_current_baselines": {
            "claim_ledger_raw_sha256": (
                "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245"
            ),
            "execution_preregistration_human_raw_sha256": (
                "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e"
            ),
            "execution_preregistration_machine_raw_sha256": (
                "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"
            ),
            "execution_preregistration_state": "DRAFT_NOT_EXECUTABLE",
            "execution_preregistration_unresolved_blocker_count": 12,
            "execution_preregistration_confirmatory_blocker_count": 10,
            "execution_preregistration_submission_blocker_count": 2,
            "execution_preregistration_freeze_predicate_verified": True,
            "cp76_manifest_raw_sha256": (
                "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06"
            ),
            "cp76_test_raw_sha256": (
                "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc"
            ),
            "cp76_checklist_raw_sha256": (
                "002aae4bdd9ccf3b80b514cea6de767a05390611fec63f416bce01cb4d8e56b4"
            ),
            "cp76_readiness_status": "NOT_READY",
            "cp76_manuscript_submission_ready": False,
        },
        "closure_v2_raw_sha256": (
            "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"
        ),
        "closure_v2_record_sha256": (
            "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"
        ),
        "postdraw_record_sha256": POSTDRAW_RECORD_SHA256,
        "conditions_closed_by_this_milestone": 0,
    }


def audit_static_overlay_source_freeze(workspace_root: Any) -> Dict[str, Any]:
    """Audit static overlay and coordinate custody without project imports."""

    requested_root = Path(workspace_root).absolute()
    root_information = requested_root.lstat()
    if stat.S_ISLNK(root_information.st_mode) or not stat.S_ISDIR(
        root_information.st_mode
    ):
        raise CapsuleError("workspace root is not a nonsymlink directory")
    root = requested_root.resolve(strict=True)
    if root != requested_root:
        raise CapsuleError("workspace root is not canonical")
    manifest = virtual_source_manifest(root)
    coordinates = coordinate_manifests()
    governance = _governance_roster(root)
    candidate = _candidate_source_roster(root, manifest)
    runtime = _runtime_input_roster(root)
    path_sets = (
        {row["path"] for row in governance},
        {row["path"] for row in candidate},
        {row["path"] for row in runtime},
    )
    if any(
        path_sets[left] & path_sets[right] for left, right in ((0, 1), (0, 2), (1, 2))
    ):
        raise CapsuleError("capsule rosters are not path-disjoint")
    for relative_path in PLANNED_OUTPUT_ROOTS + LEGACY_PRODUCTION_ROOTS:
        _require_absent_no_entry(root / relative_path)
    if len(candidate) != 48 or len(runtime) != 7:
        raise CapsuleError("candidate or runtime roster count changed")
    api_rows = runner_api_inventory_rows(root, manifest, coordinates)
    preregistration = _preregistration_state_projection(root)
    return {
        "schema": QUALIFICATION_SCHEMA,
        "status": "LIVE_STATIC_AUDIT_PASS_ZERO_EXECUTION_NOT_EXECUTABLE",
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "planned_output_boundary": {
            "planned_output_roots": list(PLANNED_OUTPUT_ROOTS),
            "planned_output_root_count": 11,
            "all_planned_output_roots_lstat_absent": True,
            "authority_domain_frozen": False,
            "binder_schemas_frozen": False,
            "records_issued": 0,
        },
        "source_manifest": manifest,
        "overlay_rules": [
            {"rule": rule, "rule_sha256": _overlay_rule_sha256(rule)}
            for rule in OVERLAY_RULES
        ],
        "coordinate_manifests": coordinates,
        "runner_api_inventory": {
            "phase_row_order": ["RANK", "EXACT", "PRIMARY", "CONTROLS"],
            "phase_rows": list(api_rows),
            "inventory_only": True,
            "binder_schema_frozen": False,
            "successor_authority_frozen": False,
            "typed_coordinate_consumption_qualified": False,
            "phase_aggregate_admission_qualified": False,
            "private_qualification_type": "StaticOverlaySourceFreezeQualification",
            "private_qualification_requires_canonical_sidecar_loader": True,
            "binder_integration_complete": False,
        },
        "rosters": {
            "governance_custody": list(governance),
            "candidate_source_inputs": list(candidate),
            "runtime_inputs": list(runtime),
            "governance_count": len(governance),
            "candidate_source_input_count": len(candidate),
            "runtime_input_count": len(runtime),
            "path_sets_disjoint": True,
            "all_execution_admissible_false": True,
        },
        "preregistration_state": preregistration,
        "legacy_and_development_replay_boundary": {
            "legacy_v1_authorizations_admissible": False,
            "legacy_v1_permits_admissible": False,
            "legacy_v1_consumptions_admissible": False,
            "legacy_v1_receipts_admissible": False,
            "legacy_runtime_identity_admissible": False,
            "d1_checkpoint_admissible": False,
            "d1_diagnostic_evidence_admissible": False,
            "d1_is_prior_observed_development_knowledge": True,
            "d1_seed_1729_quarantined_all_methods_lanes_budgets": True,
            "replay_into_successor_authority_permitted": False,
        },
        "runtime_and_activation_state": {
            "successor_runtime_identity_path": SUCCESSOR_RUNTIME_PATHS[0],
            "successor_runtime_approval_path": SUCCESSOR_RUNTIME_PATHS[1],
            "legacy_runtime_identity_path": LEGACY_RUNTIME_PATH,
            "legacy_runtime_approval_path": LEGACY_RUNTIME_APPROVAL_PATH,
            "legacy_runtime_candidate_root": LEGACY_RUNTIME_CANDIDATE_ROOT,
            "runtime_manifest_sha256": None,
            "runtime_approval_sha256": None,
            "runtime_identity_present": False,
            "runtime_identity_approved": False,
            "overlay_source_tree_materialized": False,
            "runtime_bundle_complete": False,
            "activation_complete": False,
            "production_order_activation_complete": False,
            "production_order_authority_adapter_implemented": False,
            "legacy_virtual_production_order_execution_admissible": False,
            "legacy_rglob_source_manifest_usable_for_successor_activation": False,
            "primary_metrics_integration_complete": False,
            "candidate_decision_integration_complete": False,
            "registry_integration_complete": False,
            "source_amendment_complete": False,
            "execution_capsule_complete": False,
            "binder_integration_complete": False,
            "runner_integration_complete": False,
            "permit_issuable": False,
            "direct_launch_allowed": False,
        },
        "execution_nonclaims": {
            "source_write_performed": False,
            "artifact_write_performed": False,
            "entropy_contacted": False,
            "network_contacted": False,
            "subprocess_launched": False,
            "permit_issued": False,
            "phase_consumption_issued": False,
            "registry_integration_performed": False,
            "source_amendment_performed": False,
            "execution_capsule_completed": False,
            "runtime_bundle_completed": False,
            "binder_integration_completed": False,
            "rank_execution_authorized": False,
            "training_execution_authorized": False,
            "production_execution_authorized": False,
            "scientific_execution_authorized": False,
            "result_eligible": False,
            "scientific_result_eligible": False,
            "r1_qualified": False,
            "r2_qualified": False,
            "c17_proved": False,
            "claim_promoted": False,
            "submission_ready": False,
        },
        "legacy_production_roots": {
            "paths": list(LEGACY_PRODUCTION_ROOTS),
            "count": 11,
            "all_lstat_absent": True,
        },
        "source_target_state": {
            "planned_adapter_target_path": PLANNED_ADAPTER_TARGET,
            "planned_adapter_target_lstat_absent": True,
            "overlay_bytes_materialized_as_source_tree": False,
            "source_amendment_performed": False,
            "static_audit_module_path": STATIC_AUDIT_MODULE_PATH,
            "static_audit_module_is_not_runtime_adapter": True,
        },
        "next_gate": {
            "required_milestone": (
                "ADDITIVE_VERSIONED_SUCCESSOR_AUTHORITY_RUNTIME_ADAPTER_AND_BINDER_"
                "IMPLEMENTATION"
            ),
            "must_implement_and_enforce_successor_authority_runtime_adapter_and_binder": True,
            "future_binder_must_bind_execution_phase_schedule_manifest": True,
            "future_binder_must_bind_phase_event_schedule_with_metrics_barrier": True,
            "future_binder_must_bind_all_aggregate_manifest": True,
            "legacy_source_bytes_must_remain_unchanged": True,
            "rank_or_production_execution_permitted_before_gate": False,
        },
        "milestone_state": MILESTONE_STATE,
    }


def load_static_overlay_source_freeze_qualification(
    workspace_root: Any,
) -> StaticOverlaySourceFreezeQualification:
    """Reopen the canonical sidecar and return a non-executable custody proof."""

    requested_root = Path(workspace_root).absolute()
    information = requested_root.lstat()
    if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
        raise CapsuleError("workspace root is not a nonsymlink directory")
    root = requested_root.resolve(strict=True)
    if root != requested_root:
        raise CapsuleError("workspace root is not canonical")
    payload, _ = _read_stable_regular_file(root / REGISTRATION_SIDECAR_PATH)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CapsuleError("registration sidecar is not ASCII JSON") from error
    top_fields = (
        "schema_version",
        "registration_id",
        "registration_mode",
        "scope",
        "milestone_state",
        "global_state",
        "qualification_snapshot",
        "nonclaims",
        "publication_anonymity_boundary",
        "next_gate",
        "registration_bindings",
        "record_sha256",
    )
    _require_exact_keys(record, top_fields, "registration sidecar")
    if payload != _canonical_json(record) + b"\n":
        raise CapsuleError("registration sidecar is not canonical LF-terminated JSON")
    body = dict(record)
    record_sha256 = body.get("record_sha256")
    _require_sha256(record_sha256, "registration sidecar self digest")
    body["record_sha256"] = None
    if _sha256(REGISTRATION_DOMAIN + _canonical_json(body)) != record_sha256:
        raise CapsuleError("registration sidecar self digest changed")
    if (
        record.get("schema_version") != SCHEMA_VERSION
        or record.get("registration_id")
        != "A1_R1_REGISTRY_AWARE_OVERLAY_SOURCE_COORDINATE_FREEZE_V1"
        or record.get("registration_mode") != "ADDITIVE_STATIC_ZERO_EXECUTION"
        or record.get("scope") != "INTERNAL_PREREGISTRATION_DEVELOPMENT_CUSTODY"
        or record.get("milestone_state") != MILESTONE_STATE
        or record.get("global_state") != "DRAFT_NOT_EXECUTABLE"
    ):
        raise CapsuleError("registration sidecar state changed")
    live = audit_static_overlay_source_freeze(root)
    if _canonical_json(record.get("qualification_snapshot")) != _canonical_json(live):
        raise CapsuleError("registration sidecar differs from the fresh static audit")
    if _canonical_json(record.get("next_gate")) != _canonical_json(live["next_gate"]):
        raise CapsuleError("registration next gate changed")
    nonclaims = record.get("nonclaims")
    if _canonical_json(nonclaims) != _canonical_json(REGISTRATION_NONCLAIMS):
        raise CapsuleError("registration nonclaims are not exact false booleans")
    if _canonical_json(record.get("publication_anonymity_boundary")) != _canonical_json(
        PUBLICATION_ANONYMITY_BOUNDARY
    ):
        raise CapsuleError("publication anonymity boundary changed")
    bindings = record.get("registration_bindings")
    if type(bindings) is not list or len(bindings) != 3:
        raise CapsuleError("registration binding roster changed")
    expected_paths = {
        "HUMAN_REGISTRATION": (
            "manuscript_v3/a1_r1_registry_aware_source_execution_capsule_freeze_v1.md"
        ),
        "STATIC_AUDIT_MODULE": STATIC_AUDIT_MODULE_PATH,
        "HOSTILE_TEST": (
            "tests/unit/"
            "test_manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.py"
        ),
    }
    observed_roles = []
    for ordinal, row in enumerate(bindings):
        fields = (
            "ordinal",
            "role",
            "path",
            "bytes",
            "raw_sha256",
            "lf_only",
            "is_regular_file",
            "is_symlink",
        )
        _require_exact_keys(row, fields, "registration binding")
        role = row.get("role")
        if type(role) is not str or role not in expected_paths:
            raise CapsuleError("registration binding role changed")
        relative_path = expected_paths[role]
        if (
            type(row.get("ordinal")) is not int
            or row.get("ordinal") != ordinal
            or row.get("path") != relative_path
            or row.get("lf_only") is not True
            or row.get("is_regular_file") is not True
            or row.get("is_symlink") is not False
        ):
            raise CapsuleError("registration binding custody changed")
        bound_payload, _ = _read_stable_regular_file(root / relative_path)
        if (
            type(row.get("bytes")) is not int
            or row.get("bytes") != len(bound_payload)
            or row.get("raw_sha256") != _sha256(bound_payload)
            or b"\r" in bound_payload
        ):
            raise CapsuleError("registration binding bytes changed")
        observed_roles.append(role)
    if observed_roles != [
        "HUMAN_REGISTRATION",
        "STATIC_AUDIT_MODULE",
        "HOSTILE_TEST",
    ]:
        raise CapsuleError("registration binding order changed")
    qualification = object.__new__(StaticOverlaySourceFreezeQualification)
    object.__setattr__(qualification, "_canonical_snapshot", _canonical_json(live))
    object.__setattr__(qualification, "_record_sha256", record_sha256)
    return qualification


def status(workspace_root: Any) -> Dict[str, Any]:
    """Return the durable static source-freeze state after reopening the sidecar."""

    qualification = load_static_overlay_source_freeze_qualification(workspace_root)
    audit = qualification.snapshot()
    return {
        "schema": "heterodiff-a1-r1-registry-aware-overlay-source-freeze-status-v1",
        "state": MILESTONE_STATE,
        "qualification_status": audit["status"],
        "sidecar_record_sha256": qualification.record_sha256,
        "canonical_sidecar_and_bindings_reopened": True,
        "source_manifest_sha256": audit["source_manifest"]["manifest_sha256"],
        "runtime_manifest_sha256": None,
        "runtime_approval_sha256": None,
        "overlay_source_tree_materialized": False,
        "adapter_implemented": False,
        "permit_issuable": False,
        "execution_authorized": False,
    }


__all__ = [
    "BASE_SOURCE_PATHS",
    "DENYLISTED_DEVELOPMENT_SOURCES",
    "PLANNED_ADAPTER_TARGET",
    "REGISTRY",
    "StaticOverlaySourceFreezeQualification",
    "TaggedCoordinateV1",
    "audit_static_overlay_source_freeze",
    "coordinate_manifests",
    "load_static_overlay_source_freeze_qualification",
    "status",
    "virtual_source_manifest",
]
