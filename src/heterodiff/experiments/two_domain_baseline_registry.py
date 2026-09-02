"""Frozen two-domain baseline identity and configuration registry.

This module is the production-readable part of the B06 pre-outcome freeze.  It
contains no data reader, model import, training entrypoint, network call,
randomness, or external-package import.  It records identities and validates
configuration interfaces; B12 separately owns executable adapters, runners,
and whole-method qualification, while B08 owns hardware and calibrated
resource values.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict, Mapping, Tuple

from heterodiff.experiments.matched_total_compute import (
    ACCOUNTING_POLICY_KEYS,
    CALCULATOR_ID,
    FAIRNESS_BINDING_KEYS,
    HARD_AXES,
    PRIMARY_COMPARATOR_ROLE,
    PRIMARY_METHOD_ROLE,
    PROSPECTIVE_BUDGET_SCHEMA_VERSION,
    UNPOPULATED_B08_VALUE_KEYS,
    validate_primary_pair_equality,
)


PHYSIONET_DOMAIN_ID = "physionet-challenge-2012"
RETAIL_DOMAIN_ID = "online-retail-ii"
DOMAIN_IDS = (PHYSIONET_DOMAIN_ID, RETAIL_DOMAIN_ID)

PRIMARY_METHOD_ID = "association-aware-guide-plus-residual"
PRIMARY_COMPARATOR_ID = "unified-direct-conditioner"
PRIMARY_METHOD_IDS = (PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID)

CONTROL_IDS = (
    "analytic-guide-only-residual-removed",
    "direct-or-residual-only-analytic-guide-removed",
    "association-destroyed-or-factorized-eventwise",
    "unconditional-base-sanity-reference",
)

COMPARATOR_FAMILY_IDS = (
    "ngdb-style-auxiliary-guide-plus-correction",
    "deft-style-generalized-h-frozen-base-correction",
    "task-compatible-same-base-smc-or-feynman-kac",
    "closest-variable-cardinality-point-or-edit-generator",
)

CAPABILITY_AXES = (
    "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION",
    "DOMAIN_PHYSICAL_TIME",
    "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY",
    "TYPED_EVENTS_AND_CONTINUOUS_MARKS",
    "MISSING_OR_PARTIALLY_OBSERVED_MARKS",
    "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY",
    "HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS",
    "CONDITIONAL_SAMPLING_INTERFACE",
    "SHARED_BASE_COMPATIBILITY",
    "TRAINING_TUNING_AND_INFERENCE_INTERFACES",
    "NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY",
)
FINAL_CAPABILITY_STATES = frozenset(
    ("NATIVE", "AUTHOR_EXTENSION", "INAPPLICABLE_WITH_PROOF")
)

LOCAL_REPOSITORY = (
    "content-addressed:workspace/heterodiff/b06-local-deepsets-method-source-release-v1"
)
LOCAL_RELEASE_SHA256 = (
    "023e5e54f359e5b1c4b13ca22c5ff922cb85cbd105cf98d0261da2352fd81564"
)
LOCAL_RELEASE_REVISION = "sha256:" + LOCAL_RELEASE_SHA256
LOCAL_SOURCE_RELEASE_DOMAIN = b"HETERODIFF-B06-LOCAL-METHOD-SOURCE-RELEASE-V1\0"
LOCAL_SOURCE_RELEASE_FILES = (
    (
        "src/heterodiff/theory/association_operational_guide.py",
        "9540a3bce5e865a2f3d35192f55ba72a9574243d959f404e5c500f27c3919d7f",
    ),
    (
        "src/heterodiff/theory/association_preconditioner.py",
        "29e8a37fa1b74a37fc84d5208793e00e9b19674d6988bcfad46ac50613b1148c",
    ),
    (
        "src/heterodiff/theory/association_totalized_jump_guide.py",
        "6b519b59994e763900c3d17fee6d44e8ec793e09db5ecffaffd1e47374fc7dd4",
    ),
    (
        "src/heterodiff/models/configuration_energy_torch.py",
        "355e81ffba2eb2a7cf314f685ac9ea89fc7af6c61e4908a935b6032245879815",
    ),
    (
        "src/heterodiff/models/configuration_residual_torch.py",
        "3afc4534f09f2cf41e3a737322c44112620fb9055aa51378c3c326c9c4a2293b",
    ),
    (
        "src/heterodiff/models/configuration_totalized_jump_potential_composer_torch.py",
        "bbb31fc7e48c2d18a8ae7b196f20639ec56d0e8089a210222b437c6a8bb78076",
    ),
    (
        "src/heterodiff/models/configuration_totalized_jump_residual_torch.py",
        "285d320f2a462954db54bd70cafff9266b4e31baf45e1d1276fdf3497b17cfff",
    ),
    (
        "src/heterodiff/processes/plugin_bridge_sampler.py",
        "f6d7357f193651416b68cca9f3365855f520c5a7c2eb876114fc9e286627abc2",
    ),
)

CSDI_REPOSITORY = "https://github.com/ermongroup/CSDI"
CSDI_COMMIT = "7f24a436f08d98853a6b43d4f7f04e5a65ecdf27"
CSDI_LICENSE_SHA256 = (
    "76f5d72acd2d179c72f9c8d7212cc2e6904c1a15908951d0959b9ea13d528ba9"
)
CSDI_LICENSE_BYTES = 1071
CSDI_UPSTREAM_CONFIG_SHA256 = (
    "a492e8e1f682cec19549da2c7f4e13cf04067f6db260142a0243aba3daaab0e7"
)
CSDI_UPSTREAM_ENTRYPOINT_SHA256 = (
    "8d50d41f021c777728319c201c0956d0d107c0d58a5c23870a1730633b79c136"
)
CSDI_REQUIREMENTS_SHA256 = (
    "6a14207beb17400d8595e111a5bc2d26f4886acea7d84952f501a419d5d372ce"
)

ADD_THIN_REPOSITORY = "https://github.com/davecasp/add-thin"
ADD_THIN_COMMIT = "aeb051349f130636dca1a90a5582289a29968bfe"
ADD_THIN_LICENSE_SHA256 = (
    "255e3af542368979678cdb1c0afd01e1c95a3303252d8b6cc8832b63e1794a30"
)
ADD_THIN_LICENSE_BYTES = 1065
ADD_THIN_TRAIN_CONFIG_SHA256 = (
    "cacc38ac4442ea96ee093c7a8d68324dc5197df0a2e178095e0411ead6a43065"
)
ADD_THIN_MODEL_CONFIG_SHA256 = (
    "671c03581432de2d5447b861a5cd1c07cbbbbf4055b9f5ada2023cfda1504078"
)
ADD_THIN_CONFIG_SOURCE_SHA256 = (
    "7f327407933f6b847bcd969357c9cdbe6eb278a2d29d6748e3ea6da4d7c79ae9"
)

EDITPP_REPOSITORY = "https://github.com/martenlienen/editpp"
EDITPP_COMMIT = "3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918"
EDITPP_LICENSE_SHA256 = (
    "94f6472f9fafcc23e53bd3914638c94f3ab39671fbf1195b2d798b9bf8072198"
)
EDITPP_LICENSE_BYTES = 1118
EDITPP_ENTRYPOINT_SHA256 = (
    "e716d4878f2683e4fa440e7da21fbe7ac1abd33302982fe56456b4c427ee58df"
)
EDITPP_TRAIN_CONFIG_SHA256 = (
    "2dfbdc3ce212cea887c272ec3a6a16fb66d810f75a58a40ab666e035461988cd"
)
EDITPP_TASK_CONFIG_SHA256 = (
    "e8786d6de3fb58d949fef6b7e856ec9441047ca41dcb463e2e4f09fcb1d194a9"
)
EDITPP_MODEL_CONFIG_SHA256 = (
    "67ec74d9df9912f3aab008d216b40406baf4d9df865bd1921959b0a0cdb02d42"
)
EDITPP_LOCK_SHA256 = (
    "e66774092d4d2d1b14d0dbf3a184a2fc708986c651e30f7f71119c864f6957d8"
)

EVENT_DIMENSION_BY_DOMAIN = {
    PHYSIONET_DOMAIN_ID: 112,
    RETAIL_DOMAIN_ID: 10,
}
MAXIMUM_EVENTS_BY_DOMAIN = {
    PHYSIONET_DOMAIN_ID: 131_072,
    RETAIL_DOMAIN_ID: 1_067_371,
}
TRAINING_SEED_COUNT = 256
NATURAL_GROUP_COUNT = 128
CONDITIONING_CASES_PER_GROUP = 1
CONDITIONAL_DRAWS_PER_CASE = 64
REVERSE_STEPS_PER_DRAW = 256
TUNING_TRIAL_LIMIT = 8


class BaselineRegistryError(ValueError):
    """Raised when a baseline registry value violates the frozen contract."""


def _validate_exact_json_tree(value: object, path: str = "$") -> None:
    """Reject JSON-lookalike subclasses and tuple-for-array substitutions."""

    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_exact_json_tree(item, f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise BaselineRegistryError(f"non-string object key at {path}")
            _validate_exact_json_tree(item, f"{path}.{key}")
        return
    raise BaselineRegistryError(
        f"non-exact JSON carrier at {path}: {type(value).__name__}"
    )


def canonical_json_bytes(value: object) -> bytes:
    """Return canonical ASCII JSON for an exact registry object."""

    _validate_exact_json_tree(value)
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise BaselineRegistryError("value is not canonical-JSON encodable") from error


def config_sha256(value: object) -> str:
    return hashlib.sha256(
        b"HETERODIFF-B06-CONFIG-V1\0" + canonical_json_bytes(value)
    ).hexdigest()


def local_source_release_sha256() -> str:
    digest = hashlib.sha256(LOCAL_SOURCE_RELEASE_DOMAIN)
    for path, raw_sha256 in LOCAL_SOURCE_RELEASE_FILES:
        digest.update(path.encode("ascii"))
        digest.update(b"\0")
        digest.update(raw_sha256.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _linear_parameters(input_width: int, output_width: int) -> int:
    return input_width * output_width + output_width


def frozen_base_parameter_count(domain_id: str) -> int:
    """Exact count of the hashed typed-DeepSets energy architecture."""

    event_dimension = EVENT_DIMENSION_BY_DOMAIN[domain_id]
    event_hidden = 128
    event_embedding = 128
    context_dimension = 64
    context_hidden = 128
    context_embedding = 128
    readout_hidden = 128
    event = (
        _linear_parameters(event_dimension, event_hidden)
        + _linear_parameters(event_hidden, event_embedding)
    )
    context = (
        _linear_parameters(context_dimension + 1, context_hidden)
        + _linear_parameters(context_hidden, context_embedding)
    )
    readout_input = event_embedding + context_embedding + 1
    readout = (
        _linear_parameters(readout_input, readout_hidden)
        + _linear_parameters(readout_hidden, readout_hidden)
        + _linear_parameters(readout_hidden, 1)
    )
    return event + context + readout


def conditional_module_parameter_count(domain_id: str) -> int:
    """One role-separated conditional DeepSets energy/residual module."""

    return frozen_base_parameter_count(domain_id)


def primary_parameter_count(domain_id: str) -> Dict[str, int]:
    base = frozen_base_parameter_count(domain_id)
    conditional = conditional_module_parameter_count(domain_id)
    return {
        "frozen_unconditional_base": base,
        "trainable_conditioner": conditional,
        "total": base + conditional,
    }


def _zero_counts() -> Dict[str, int]:
    return {
        "BASE_FORWARD": 0,
        "BASE_BACKWARD": 0,
        "CONDITIONER_FORWARD": 0,
        "CONDITIONER_BACKWARD": 0,
        "GUIDE_EVALUATION": 0,
        "RESAMPLING_STEP": 0,
        "ODE_OR_SDE_STEP": 0,
        "DATA_ADAPTER_RECORD": 0,
        "METRIC_DRAW_EVALUATION": 0,
        "OTHER_DECLARED_OPERATION": 0,
    }


def training_compute_budget(domain_id: str) -> Dict[str, object]:
    """Finite method-neutral event ceilings, identical for the primary pair."""

    tuning = _zero_counts()
    tuning_updates = TUNING_TRIAL_LIMIT * 1_024
    tuning.update(
        {
            "BASE_FORWARD": tuning_updates,
            "CONDITIONER_FORWARD": tuning_updates,
            "CONDITIONER_BACKWARD": tuning_updates,
            "GUIDE_EVALUATION": tuning_updates,
            "ODE_OR_SDE_STEP": tuning_updates * 4,
            "DATA_ADAPTER_RECORD": tuning_updates * 16,
            "METRIC_DRAW_EVALUATION": TUNING_TRIAL_LIMIT * NATURAL_GROUP_COUNT,
        }
    )
    final = _zero_counts()
    final_updates = TRAINING_SEED_COUNT * 4_096
    final.update(
        {
            "BASE_FORWARD": final_updates,
            "CONDITIONER_FORWARD": final_updates,
            "CONDITIONER_BACKWARD": final_updates,
            "GUIDE_EVALUATION": final_updates,
            "ODE_OR_SDE_STEP": final_updates * 4,
            "DATA_ADAPTER_RECORD": final_updates * 16,
        }
    )
    return {
        "budget_id": "B06-PRIMARY-TRAINING-" + domain_id.upper() + "-V1",
        "formula_id": CALCULATOR_ID,
        "scope": "PER_METHOD_PER_DOMAIN_COMPLETE_256_SEED_ROSTER",
        "phase_event_count_ceilings": {
            "PILOT": _zero_counts(),
            "TUNING": tuning,
            "FINAL_TRAINING": final,
            "CONFIRMATORY_INFERENCE": _zero_counts(),
        },
        "prospective_primary_pair_equality_required": True,
        "failed_attempts_and_author_extensions_charged": True,
        "unused_transfer_or_postresult_topup_permitted": False,
        "hardware_weights_and_capacity_owned_by_B08": True,
    }


def inference_compute_budget(domain_id: str) -> Dict[str, object]:
    draws = (
        TRAINING_SEED_COUNT
        * NATURAL_GROUP_COUNT
        * CONDITIONING_CASES_PER_GROUP
        * CONDITIONAL_DRAWS_PER_CASE
    )
    inference = _zero_counts()
    inference.update(
        {
            "BASE_FORWARD": draws * REVERSE_STEPS_PER_DRAW,
            "CONDITIONER_FORWARD": draws * REVERSE_STEPS_PER_DRAW,
            "GUIDE_EVALUATION": draws * REVERSE_STEPS_PER_DRAW,
            "ODE_OR_SDE_STEP": draws * REVERSE_STEPS_PER_DRAW,
            "DATA_ADAPTER_RECORD": draws * MAXIMUM_EVENTS_BY_DOMAIN[domain_id],
            "METRIC_DRAW_EVALUATION": (
                TRAINING_SEED_COUNT
                * NATURAL_GROUP_COUNT
                * CONDITIONAL_DRAWS_PER_CASE
                * CONDITIONAL_DRAWS_PER_CASE
            ),
        }
    )
    return {
        "budget_id": "B06-PRIMARY-INFERENCE-" + domain_id.upper() + "-V1",
        "formula_id": CALCULATOR_ID,
        "scope": "PER_METHOD_PER_DOMAIN_COMPLETE_CONFIRMATORY_ROSTER",
        "phase_event_count_ceilings": {
            "PILOT": _zero_counts(),
            "TUNING": _zero_counts(),
            "FINAL_TRAINING": _zero_counts(),
            "CONFIRMATORY_INFERENCE": inference,
        },
        "prospective_primary_pair_equality_required": True,
        "failed_attempts_and_author_extensions_charged": True,
        "unused_transfer_or_postresult_topup_permitted": False,
        "hardware_weights_and_capacity_owned_by_B08": True,
    }


def prospective_primary_budget_record(
    method_id: str, domain_id: str
) -> Dict[str, object]:
    """Bind one primary role to the shared future B08 ceiling identities."""

    if method_id not in PRIMARY_METHOD_IDS or domain_id not in DOMAIN_IDS:
        raise BaselineRegistryError("unknown primary method/domain budget row")
    role = (
        PRIMARY_METHOD_ROLE
        if method_id == PRIMARY_METHOD_ID
        else PRIMARY_COMPARATOR_ROLE
    )
    prefix = "B06-" + domain_id.upper()
    record = {
        "schema_version": PROSPECTIVE_BUDGET_SCHEMA_VERSION,
        "budget_id": prefix + "-" + method_id.upper() + "-PROSPECTIVE-V1",
        "method_id": method_id,
        "method_role": role,
        "domain_id": domain_id,
        "training_compute_budget_id": training_compute_budget(domain_id)[
            "budget_id"
        ],
        "inference_compute_budget_id": inference_compute_budget(domain_id)[
            "budget_id"
        ],
        "calibration_weight_record_id": prefix + "-FUTURE-B08-WEIGHTS-V1",
        "scalar_ceiling_id": prefix + "-FUTURE-B08-SCALAR-CEILING-V1",
        "hard_axis_ceiling_ids": {
            axis: prefix + "-FUTURE-B08-" + axis + "-CEILING-V1"
            for axis in HARD_AXES
        },
        "fairness_bindings": {
            "shared_base_checkpoint_id": LOCAL_RELEASE_REVISION,
            "group_roster_id": "F134-128-NATURAL-GROUPS-PER-DOMAIN-V1",
            "conditioning_case_roster_id": "F135-ONE-CASE-PER-GROUP-V1",
            "draw_roster_id": "F109-R64-ADDRESSED-DRAW-ROSTER-V1",
            "precision_policy_id": "B06-SHARED-PRECISION-POLICY-V1",
            "metric_workload_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
        },
        "accounting_policy": {
            "failed_attempts_charged": True,
            "author_extensions_charged": True,
            "unique_preprocessing_charged": True,
            "unused_allocation_transfer_permitted": False,
            "post_result_top_up_permitted": False,
        },
        "unpopulated_b08_values": {
            "hardware_identity_value_assigned": False,
            "runtime_identity_value_assigned": False,
            "calibration_weight_values_assigned": False,
            "scalar_ceiling_value_assigned": False,
            "hard_axis_ceiling_values_assigned": False,
            "capacity_reserved": False,
        },
    }
    if tuple(record["hard_axis_ceiling_ids"]) != HARD_AXES:
        raise BaselineRegistryError("hard-axis ceiling roster differs")
    if tuple(record["fairness_bindings"]) != FAIRNESS_BINDING_KEYS:
        raise BaselineRegistryError("fairness binding roster differs")
    if tuple(record["accounting_policy"]) != ACCOUNTING_POLICY_KEYS:
        raise BaselineRegistryError("accounting policy roster differs")
    if tuple(record["unpopulated_b08_values"]) != UNPOPULATED_B08_VALUE_KEYS:
        raise BaselineRegistryError("unpopulated B08 roster differs")
    return record


def _base_config(domain_id: str) -> Dict[str, object]:
    return {
        "domain_id": domain_id,
        "f105_event_dimension": EVENT_DIMENSION_BY_DOMAIN[domain_id],
        "maximum_events": MAXIMUM_EVENTS_BY_DOMAIN[domain_id],
        "architecture": "HASHED_TYPED_DEEPSETS_ENERGY_V1",
        "source_class": (
            "heterodiff.models.configuration_energy_torch:"
            "BoundedConfigurationEnergy"
        ),
        "event_type_interface": "ONE_F105_EXACT_VECTOR_TYPE_PER_DOMAIN",
        "event_hidden_width": 128,
        "event_embedding_width": 128,
        "context_dimension": 64,
        "context_hidden_width": 128,
        "context_embedding_width": 128,
        "readout_hidden_width": 128,
        "pooling": "EXACT_MULTIPLICITY_PRESERVING_SEGMENT_SUM",
        "reverse_steps": REVERSE_STEPS_PER_DRAW,
        "parameter_count_procedure": (
            "CONFIGURATION_ENERGY_ARCHITECTURE_PARAMETER_COUNT_EXACT_INTEGER_V1"
        ),
        "native_runtime_configuration_cap_limit": 10_000,
        "domain_scale_runtime_status": (
            "B12_STREAMING_OR_LIMIT_LIFT_QUALIFICATION_REQUIRED_NO_TRUNCATION"
        ),
        "current_runtime_qualification_claimed": False,
    }


def _primary_config(method_id: str) -> Dict[str, object]:
    if method_id not in PRIMARY_METHOD_IDS:
        raise BaselineRegistryError("unknown primary method")
    conditional_kind = (
        "ANALYTIC_ASSOCIATION_GUIDE_PLUS_ONE_LEARNED_RESIDUAL"
        if method_id == PRIMARY_METHOD_ID
        else "UNIFIED_DIRECT_ONE_LEARNED_CONDITIONER"
    )
    return {
        "schema": "HETERODIFF_B06_PRIMARY_CONFIG_V1",
        "method_id": method_id,
        "same_frozen_base_release_by_domain": {
            domain_id: LOCAL_RELEASE_REVISION for domain_id in DOMAIN_IDS
        },
        "domain_configs": {
            domain_id: {
                "base": _base_config(domain_id),
                "conditional_architecture": conditional_kind,
                "conditional_modules": 1,
                "conditional_source_class": (
                    "heterodiff.models.configuration_residual_torch:"
                    "CertifiedConditionalResidualCheckpoint"
                    if method_id == PRIMARY_METHOD_ID
                    else "heterodiff.models.configuration_energy_torch:"
                    "CertifiedConfigurationEnergyCheckpoint"
                ),
                "conditioning_context_encoder_status": (
                    "FROZEN_64_DIMENSION_INTERFACE_B12_IMPLEMENTATION_REQUIRED"
                ),
                "parameter_count": primary_parameter_count(domain_id),
                "training_budget": training_compute_budget(domain_id),
                "inference_budget": inference_compute_budget(domain_id),
            }
            for domain_id in DOMAIN_IDS
        },
        "test_access_permitted_for_selection": False,
        "post_test_change_permitted": False,
    }


def _control_configs() -> Tuple[Dict[str, object], ...]:
    modes = (
        {
            "active_components": ["ANALYTIC_GUIDE", "FROZEN_BASE"],
            "removed_components": ["LEARNED_RESIDUAL"],
        },
        {
            "active_components": ["LEARNED_RESIDUAL", "FROZEN_BASE"],
            "removed_components": ["ANALYTIC_GUIDE"],
        },
        {
            "active_components": ["FACTORIZED_EVENTWISE_CONDITIONER", "FROZEN_BASE"],
            "removed_components": ["CROSS_EVENT_ASSOCIATION_FEATURES"],
        },
        {
            "active_components": ["FROZEN_BASE"],
            "removed_components": ["ALL_CONDITIONERS_AND_GUIDES"],
        },
    )
    rows = []
    for control_id, mode in zip(CONTROL_IDS, modes):
        rows.append(
            {
                "schema": "HETERODIFF_B06_CONTROL_CONFIG_V1",
                "control_id": control_id,
                "implementation": (
                    "B06_STATIC_CONTROL_CONFIGURATION_CONTRACT::"
                    "heterodiff.experiments.two_domain_baseline_registry:"
                    "validate_control_configuration::B12_RUNTIME_REQUIRED"
                ),
                "domain_ids": list(DOMAIN_IDS),
                "same_frozen_base_release": LOCAL_RELEASE_REVISION,
                "mode": mode,
                "training_compute_budget_by_domain": {
                    domain_id: training_compute_budget(domain_id)
                    for domain_id in DOMAIN_IDS
                },
                "inference_compute_budget_by_domain": {
                    domain_id: inference_compute_budget(domain_id)
                    for domain_id in DOMAIN_IDS
                },
                "compute_is_charged_to_control": True,
                "may_discharge_literature_family_without_proof": False,
                "b12_runtime_qualification_required": True,
                "current_runtime_qualification_claimed": False,
                "post_test_change_permitted": False,
            }
        )
    return tuple(rows)


def _family_capabilities(family_id: str) -> Dict[str, str]:
    """Declare broad native concepts separately from exact project adapters."""

    values = {axis: "AUTHOR_EXTENSION" for axis in CAPABILITY_AXES}
    if family_id == COMPARATOR_FAMILY_IDS[0]:
        values["CONDITIONAL_SAMPLING_INTERFACE"] = "NATIVE"
        values["SHARED_BASE_COMPATIBILITY"] = "INAPPLICABLE_WITH_PROOF"
    elif family_id == COMPARATOR_FAMILY_IDS[1]:
        values["CONDITIONAL_SAMPLING_INTERFACE"] = "NATIVE"
        values["SHARED_BASE_COMPATIBILITY"] = "NATIVE"
    elif family_id == COMPARATOR_FAMILY_IDS[2]:
        values["CONDITIONAL_SAMPLING_INTERFACE"] = "NATIVE"
        values["SHARED_BASE_COMPATIBILITY"] = "NATIVE"
    elif family_id == COMPARATOR_FAMILY_IDS[3]:
        values["VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION"] = (
            "AUTHOR_EXTENSION"
        )
        values["DOMAIN_PHYSICAL_TIME"] = "NATIVE"
        values["SHARED_BASE_COMPATIBILITY"] = "INAPPLICABLE_WITH_PROOF"
    else:
        raise BaselineRegistryError("unknown family capability row")
    return values


def _family_config(family_id: str, domain_id: str) -> Dict[str, object]:
    if family_id not in COMPARATOR_FAMILY_IDS or domain_id not in DOMAIN_IDS:
        raise BaselineRegistryError("unknown family/domain row")
    origins = {
        COMPARATOR_FAMILY_IDS[0]: {
            "reference": "NEURAL_GUIDED_DIFFUSION_BRIDGES_ICML_2025",
            "upstream_repository": "https://github.com/bookdiver/neuralbridge",
            "upstream_commit_observed": "e73b878b99d8a3b41685921dd31736cf764a277c",
            "upstream_code_used": False,
            "reason": "NO_LICENSE_FILE_AT_FROZEN_COMMIT; CLEAN_ROOM_INTERFACE_ONLY",
        },
        COMPARATOR_FAMILY_IDS[1]: {
            "reference": "DEFT_GENERALIZED_H_TRANSFORM_2024",
            "upstream_repository": "https://github.com/alexdenker/DEFT",
            "upstream_commit_observed": "2495d46593cb48253e8f879131cdd82fcc17be7f",
            "upstream_code_used": False,
            "reason": "IMAGE_INVERSE_PROBLEM_CODE_NOT_IMPORTED; CLEAN_ROOM_INTERFACE_ONLY",
        },
        COMPARATOR_FAMILY_IDS[2]: {
            "reference": "SAME_BASE_SEQUENTIAL_MONTE_CARLO_FEYNMAN_KAC_CONTROL",
            "upstream_repository": None,
            "upstream_commit_observed": None,
            "upstream_code_used": False,
            "reason": "LOCAL_EXACT_ALGORITHM_INTERFACE",
        },
        COMPARATOR_FAMILY_IDS[3]: {
            "reference": "EDIT_BASED_FLOW_MATCHING_FOR_TEMPORAL_POINT_PROCESSES_ICLR_2026",
            "upstream_repository": EDITPP_REPOSITORY,
            "upstream_commit_observed": EDITPP_COMMIT,
            "upstream_code_used": False,
            "reason": (
                "MIT_UPSTREAM_SELECTED; FUTURE_B12_ADAPTER_MAY_USE_CODE_ONLY_"
                "UNDER_THE_FROZEN_LICENSE_AND_EXTENSION_BOUNDARY"
            ),
        },
    }
    return {
        "schema": "HETERODIFF_B06_LITERATURE_FAMILY_DOMAIN_CONFIG_V1",
        "family_id": family_id,
        "domain_id": domain_id,
        "adapter_id": "B06-" + family_id.upper() + "-" + domain_id.upper() + "-V1",
        "source_interface": (
            "heterodiff.experiments.two_domain_baseline_adapter_contract:"
            "registry_adapter_declaration"
        ),
        "origin": origins[family_id],
        "objective": "F105_CONDITIONAL_SAMPLE_GENERATION_SAME_CASE_ROSTER",
        "task_interface": "EXACT_64_DRAW_F105_CONFIGURATION_BATCH",
        "conditioning_semantics": "FROZEN_DOMAIN_PARTIAL_OBSERVATION_INTERFACE",
        "training_compute_budget": training_compute_budget(domain_id),
        "inference_compute_budget": inference_compute_budget(domain_id),
        "capability_matrix": _family_capabilities(family_id),
        "extension_license_scope": (
            "INTERNAL_RESEARCH_ONLY_NO_PUBLIC_DISTRIBUTION_UNTIL_B10_REVIEW"
        ),
        "b12_runtime_qualification_required": True,
        "post_test_change_permitted": False,
    }


def _family_justification(family_id: str, domain_id: str) -> Dict[str, object]:
    same_retail = (
        family_id == COMPARATOR_FAMILY_IDS[3] and domain_id == RETAIL_DOMAIN_ID
    )
    return {
        "domain_id": domain_id,
        "disposition": (
            "IMPLEMENTED_AND_IDENTICAL_TO_RETAIL_EXTERNAL_BASELINE_WITH_ROLE_SPECIFIC_PROOF"
            if same_retail
            else "IMPLEMENTED_AS_DISTINCT_ROW_NO_INAPPLICABILITY_OR_EQUIVALENCE_CLAIM"
        ),
        "inapplicability_claimed": False,
        "cross_row_equivalence_claimed": same_retail,
        "equivalence_dimensions": {
            "OBJECTIVE": "MATCH" if same_retail else "DISTINCT_ROW",
            "PROPOSAL_OR_CONDITIONING_SEMANTICS": "MATCH" if same_retail else "DISTINCT_ROW",
            "MODEL_CLASS": "MATCH" if same_retail else "DISTINCT_ROW",
            "COMPUTE": "MATCH" if same_retail else "DISTINCT_ROW",
            "TASK_INTERFACE": "MATCH" if same_retail else "DISTINCT_ROW",
        },
        "b12_execution_or_result_claimed": False,
    }


def _tuning_budget(method_id: str, grid: Mapping[str, object]) -> Dict[str, object]:
    return {
        "budget_id": "B06-TUNING-" + method_id.upper() + "-V1",
        "maximum_trials": TUNING_TRIAL_LIMIT,
        "candidate_grid": dict(grid),
        "candidate_grid_sha256": config_sha256(dict(grid)),
        "selection_data": "TRAIN_AND_VALIDATION_ONLY",
        "selection_metric": "F105_VALIDATION_SCORE_LOWER_IS_BETTER",
        "tie_rule": "LEXICOGRAPHIC_CANONICAL_CONFIG_BYTES",
        "failed_or_aborted_trials_charged": True,
        "test_access_permitted": False,
        "unused_transfer_or_postresult_topup_permitted": False,
    }


def _external_configs() -> Tuple[Dict[str, object], Dict[str, object]]:
    csdi_grid = {
        "channels": [64, 128],
        "diffusion_layers": [4, 6],
        "learning_rate": ["1/2000", "1/1000"],
    }
    csdi_matrix = {
        "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION": "AUTHOR_EXTENSION",
        "DOMAIN_PHYSICAL_TIME": "AUTHOR_EXTENSION",
        "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY": "AUTHOR_EXTENSION",
        "TYPED_EVENTS_AND_CONTINUOUS_MARKS": "AUTHOR_EXTENSION",
        "MISSING_OR_PARTIALLY_OBSERVED_MARKS": "NATIVE",
        "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY": "AUTHOR_EXTENSION",
        "HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS": "AUTHOR_EXTENSION",
        "CONDITIONAL_SAMPLING_INTERFACE": "NATIVE",
        "SHARED_BASE_COMPATIBILITY": "INAPPLICABLE_WITH_PROOF",
        "TRAINING_TUNING_AND_INFERENCE_INTERFACES": "AUTHOR_EXTENSION",
        "NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY": "AUTHOR_EXTENSION",
    }
    csdi = {
        "schema": "HETERODIFF_B06_EXTERNAL_BASELINE_CONFIG_V1",
        "domain_id": PHYSIONET_DOMAIN_ID,
        "method_id": "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1",
        "source_interface": (
            "heterodiff.experiments.two_domain_baseline_adapter_contract:"
            "registry_adapter_declaration"
        ),
        "repository": CSDI_REPOSITORY,
        "commit": CSDI_COMMIT,
        "upstream_config_path": "config/base.yaml",
        "upstream_config_sha256": CSDI_UPSTREAM_CONFIG_SHA256,
        "upstream_entrypoint_path": "exe_physio.py",
        "upstream_entrypoint_sha256": CSDI_UPSTREAM_ENTRYPOINT_SHA256,
        "upstream_requirements_sha256": CSDI_REQUIREMENTS_SHA256,
        "upstream_defaults": {"epochs": 200, "batch_size": 16, "diffusion_steps": 50},
        "author_extensions": [
            "LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS",
            "VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER",
            "EXACT_PHYSIONET_F105_EVENT_ADAPTER",
            "FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE",
        ],
        "capability_matrix": csdi_matrix,
        "training_compute_budget": training_compute_budget(PHYSIONET_DOMAIN_ID),
        "inference_compute_budget": inference_compute_budget(PHYSIONET_DOMAIN_ID),
        "tuning_budget": _tuning_budget("CSDI-PHYSIONET", csdi_grid),
        "b12_runtime_qualification_required": True,
        "post_test_change_permitted": False,
    }

    editpp_grid = {
        "coupling": ["independent", "sequence-length"],
        "hidden_size": [256, 512],
        "alignment": ["replace", "delta"],
    }
    editpp_matrix = {
        "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION": "AUTHOR_EXTENSION",
        "DOMAIN_PHYSICAL_TIME": "NATIVE",
        "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY": "AUTHOR_EXTENSION",
        "TYPED_EVENTS_AND_CONTINUOUS_MARKS": "AUTHOR_EXTENSION",
        "MISSING_OR_PARTIALLY_OBSERVED_MARKS": "AUTHOR_EXTENSION",
        "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY": "AUTHOR_EXTENSION",
        "HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS": "AUTHOR_EXTENSION",
        "CONDITIONAL_SAMPLING_INTERFACE": "AUTHOR_EXTENSION",
        "SHARED_BASE_COMPATIBILITY": "INAPPLICABLE_WITH_PROOF",
        "TRAINING_TUNING_AND_INFERENCE_INTERFACES": "AUTHOR_EXTENSION",
        "NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY": "AUTHOR_EXTENSION",
    }
    editpp = {
        "schema": "HETERODIFF_B06_EXTERNAL_BASELINE_CONFIG_V1",
        "domain_id": RETAIL_DOMAIN_ID,
        "method_id": "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1",
        "source_interface": (
            "heterodiff.experiments.two_domain_baseline_adapter_contract:"
            "registry_adapter_declaration"
        ),
        "repository": EDITPP_REPOSITORY,
        "commit": EDITPP_COMMIT,
        "upstream_entrypoint_path": "train.py",
        "upstream_entrypoint_sha256": EDITPP_ENTRYPOINT_SHA256,
        "upstream_train_config_path": "config/train.yaml",
        "upstream_train_config_sha256": EDITPP_TRAIN_CONFIG_SHA256,
        "upstream_task_config_path": "config/task/tef.yaml",
        "upstream_task_config_sha256": EDITPP_TASK_CONFIG_SHA256,
        "upstream_model_config_path": "config/task/model/llama2.yaml",
        "upstream_model_config_sha256": EDITPP_MODEL_CONFIG_SHA256,
        "upstream_lock_sha256": EDITPP_LOCK_SHA256,
        "upstream_defaults": {
            "maximum_steps": 5000,
            "sample_steps": 100,
            "training_precision": "32",
            "conditioning_mechanism": "independent",
            "hidden_size": 64,
            "hidden_layers": 2,
            "attention_heads": 4,
            "maximum_log_rate": "32",
        },
        "author_extensions": [
            "STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS",
            "SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL",
            "EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER",
            "ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE",
        ],
        "capability_matrix": editpp_matrix,
        "training_compute_budget": training_compute_budget(RETAIL_DOMAIN_ID),
        "inference_compute_budget": inference_compute_budget(RETAIL_DOMAIN_ID),
        "tuning_budget": _tuning_budget("EDITPP-RETAIL", editpp_grid),
        "b12_runtime_qualification_required": True,
        "post_test_change_permitted": False,
    }
    return csdi, editpp


def _external_selection_audit() -> Dict[str, object]:
    return {
        "selection_rule_id": "B06-STRONGEST-ELIGIBLE-WITHIN-FROZEN-AUDIT-ROSTER-V1",
        "reported_date": "2026-09-01",
        "universal_state_of_the_art_claimed": False,
        "criteria_in_order": [
            "TASK_COMPATIBLE_CONDITIONAL_GENERATION",
            "OFFICIAL_PUBLIC_IMPLEMENTATION",
            "IMMUTABLE_REVISION",
            "RETRIEVED_CODE_LICENSE",
            "DOMAIN_EVIDENCE",
            "FINITE_ADAPTER_AND_TUNING_PLAN",
        ],
        "physionet_decision": {
            "selected": "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1",
            "reason": (
                "OFFICIAL_PROBABILISTIC_CONDITIONAL_IMPUTATION_CODE_EXPLICITLY_"
                "TARGETS_PHYSIONET_AND_HAS_AN_MIT_LICENSE; EVENT_MULTISET_GAPS_"
                "ARE_EXPLICITLY_CHARGED_AUTHOR_EXTENSIONS"
            ),
            "audited_alternatives": [
                "RAINDROP_CLASSIFICATION_INTERFACE_NOT_CONDITIONAL_GENERATION",
                "NEURALBRIDGE_NO_LICENSE_FILE_AND_NO_PHYSIONET_TASK_INTERFACE",
                "DEFT_IMAGE_INVERSE_PROBLEM_INTERFACE_NOT_PHYSIONET_EVENT_GENERATION",
            ],
        },
        "retail_decision": {
            "selected": "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1",
            "reason": (
                "OFFICIAL_MIT_LICENSED_2026_INSERTION_DELETION_AND_SUBSTITUTION_"
                "GENERATOR_WITH_CONDITIONAL_EXPERIMENTS; STRUCTURED_RETAIL_MARKS_"
                "AND_EXACT_ASSOCIATION_CONDITIONING_ARE_CHARGED_EXTENSIONS"
            ),
            "audited_alternatives": [
                "POINT_SET_DIFFUSION_REPOSITORY_HAS_NO_RETRIEVED_LICENSE_FILE",
                "ADD_THIN_2023_UNMARKED_PREFIX_FORECAST_INTERFACE_IS_STRICTLY_LESS_TASK_ALIGNED",
                "CSDI_FIXED_MULTIVARIATE_TIME_SERIES_INTERFACE_NOT_RETAIL_EVENT_SET",
                "EASYTPP_AUTOREGRESSIVE_FORECAST_INTERFACE_NOT_UNORDERED_CONFIGURATION",
            ],
        },
    }


def build_registry() -> Dict[str, object]:
    primary_configs = {
        method_id: _primary_config(method_id) for method_id in PRIMARY_METHOD_IDS
    }
    control_configs = _control_configs()
    family_configs = {
        family_id: {
            domain_id: _family_config(family_id, domain_id)
            for domain_id in DOMAIN_IDS
        }
        for family_id in COMPARATOR_FAMILY_IDS
    }
    family_justifications = {
        family_id: {
            domain_id: _family_justification(family_id, domain_id)
            for domain_id in DOMAIN_IDS
        }
        for family_id in COMPARATOR_FAMILY_IDS
    }
    external_configs = _external_configs()
    return {
        "schema": "HETERODIFF_B06_BASELINE_REGISTRY_V1",
        "state": "B06_IDENTITIES_CONFIGS_CAPABILITIES_AND_MATCHED_COMPUTE_FROZEN",
        "domain_ids": list(DOMAIN_IDS),
        "local_source_release": {
            "repository": LOCAL_REPOSITORY,
            "revision": LOCAL_RELEASE_REVISION,
            "digest_domain": LOCAL_SOURCE_RELEASE_DOMAIN[:-1].decode("ascii"),
            "files": [
                {"path": path, "raw_sha256": raw_sha256}
                for path, raw_sha256 in LOCAL_SOURCE_RELEASE_FILES
            ],
            "public_license_grant_claimed": False,
            "scope": "INTERNAL_RESEARCH_SOURCE_IDENTITY_ONLY",
        },
        "primary_pair": [
            {
                "method_id": method_id,
                "repository": LOCAL_REPOSITORY,
                "commit_or_release": LOCAL_RELEASE_REVISION,
                "config": primary_configs[method_id],
                "config_sha256": config_sha256(primary_configs[method_id]),
                "parameter_count": {
                    domain_id: primary_parameter_count(domain_id)
                    for domain_id in DOMAIN_IDS
                },
                "training_compute_budget": {
                    domain_id: training_compute_budget(domain_id)
                    for domain_id in DOMAIN_IDS
                },
                "inference_compute_budget": {
                    domain_id: inference_compute_budget(domain_id)
                    for domain_id in DOMAIN_IDS
                },
                "prospective_matched_compute_record": {
                    domain_id: prospective_primary_budget_record(
                        method_id, domain_id
                    )
                    for domain_id in DOMAIN_IDS
                },
            }
            for method_id in PRIMARY_METHOD_IDS
        ],
        "controls": [
            {
                "control_id": control["control_id"],
                "implementation": control["implementation"],
                "config": control,
                "config_sha256": config_sha256(control),
            }
            for control in control_configs
        ],
        "literature_families": [
            {
                "family_id": family_id,
                "implementation_by_domain": {
                    domain_id: {
                        "implementation_id": family_configs[family_id][domain_id][
                            "adapter_id"
                        ],
                        "source_interface": family_configs[family_id][domain_id][
                            "source_interface"
                        ],
                        "config_sha256": config_sha256(
                            family_configs[family_id][domain_id]
                        ),
                        "capability_matrix": family_configs[family_id][domain_id][
                            "capability_matrix"
                        ],
                        "training_compute_budget_id": family_configs[family_id][
                            domain_id
                        ]["training_compute_budget"]["budget_id"],
                        "inference_compute_budget_id": family_configs[family_id][
                            domain_id
                        ]["inference_compute_budget"]["budget_id"],
                        "b12_runtime_qualification_required": True,
                    }
                    for domain_id in DOMAIN_IDS
                },
                "inapplicability_or_equivalence_justification_by_domain": (
                    family_justifications[family_id]
                ),
                "configs_by_domain": family_configs[family_id],
            }
            for family_id in COMPARATOR_FAMILY_IDS
        ],
        "external_baselines": [
            {
                "domain_id": config["domain_id"],
                "method_id": config["method_id"],
                "repository": config["repository"],
                "commit": config["commit"],
                "license": {
                    "path": "LICENSE",
                    "spdx": "MIT",
                    "raw_sha256": (
                        CSDI_LICENSE_SHA256
                        if config["domain_id"] == PHYSIONET_DOMAIN_ID
                        else EDITPP_LICENSE_SHA256
                    ),
                    "bytes": (
                        CSDI_LICENSE_BYTES
                        if config["domain_id"] == PHYSIONET_DOMAIN_ID
                        else EDITPP_LICENSE_BYTES
                    ),
                    "scope": "CODE_CONFIGS_AND_MODIFICATIONS; WEIGHTS_SEPARATELY_CUSTODIED_IF_USED",
                },
                "config": config,
                "config_sha256": config_sha256(config),
                "native_capability_and_extension_statement": {
                    "capability_matrix": config["capability_matrix"],
                    "author_extensions": config["author_extensions"],
                    "all_extension_compute_charged": True,
                    "runtime_qualification_owned_by_B12": True,
                },
                "tuning_budget": config["tuning_budget"],
            }
            for config in external_configs
        ],
        "external_selection_audit": _external_selection_audit(),
        "f104_binding": {
            "formula": "C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]",
            "formula_semantic_sha256": (
                "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b"
            ),
            "primary_training_budgets_equal_within_domain": True,
            "primary_inference_budgets_equal_within_domain": True,
            "hardware_calibration_weights_populated": False,
            "b08_remains_open": True,
        },
        "nonclaims": {
            "external_packages_installed_or_executed": False,
            "training_or_inference_executed": False,
            "hardware_or_capacity_selected": False,
            "b08_closed": False,
            "b12_closed": False,
            "formal_test_or_result_created": False,
            "submission_ready": False,
        },
    }


def _validate_capability_matrix(value: object) -> None:
    if type(value) is not dict or tuple(value) != CAPABILITY_AXES:
        raise BaselineRegistryError("capability matrix has the wrong axes/order")
    if any(state not in FINAL_CAPABILITY_STATES for state in value.values()):
        raise BaselineRegistryError("capability matrix contains a nonfinal state")


def validate_control_configuration(value: object) -> None:
    if type(value) is not dict or value.get("control_id") not in CONTROL_IDS:
        raise BaselineRegistryError("invalid control configuration")
    if value.get("b12_runtime_qualification_required") is not True:
        raise BaselineRegistryError("control must preserve the B12 boundary")
    if value.get("current_runtime_qualification_claimed") is not False:
        raise BaselineRegistryError("control claims an unqualified runtime")
    if value.get("post_test_change_permitted") is not False:
        raise BaselineRegistryError("control permits post-test change")


def validate_family_configuration(value: object) -> None:
    if type(value) is not dict:
        raise BaselineRegistryError("family configuration must be a dictionary")
    if value.get("family_id") not in COMPARATOR_FAMILY_IDS:
        raise BaselineRegistryError("unknown family")
    if value.get("domain_id") not in DOMAIN_IDS:
        raise BaselineRegistryError("unknown family domain")
    _validate_capability_matrix(value.get("capability_matrix"))
    if value.get("b12_runtime_qualification_required") is not True:
        raise BaselineRegistryError("family must preserve the B12 boundary")


def validate_registry(value: object) -> Dict[str, object]:
    """Validate and detach a complete frozen registry."""

    if type(value) is not dict:
        raise TypeError("registry must be an exact dictionary")
    expected = build_registry()
    if canonical_json_bytes(value) != canonical_json_bytes(expected):
        raise BaselineRegistryError("registry differs from the frozen value")
    if local_source_release_sha256() != LOCAL_RELEASE_SHA256:
        raise BaselineRegistryError("local source release digest differs")
    primary = value["primary_pair"]
    if len(primary) != 2 or tuple(row["method_id"] for row in primary) != PRIMARY_METHOD_IDS:
        raise BaselineRegistryError("primary-pair roster differs")
    for domain_id in DOMAIN_IDS:
        if primary[0]["parameter_count"][domain_id] != primary[1]["parameter_count"][domain_id]:
            raise BaselineRegistryError("primary parameter counts are not matched")
        if primary[0]["training_compute_budget"][domain_id] != primary[1]["training_compute_budget"][domain_id]:
            raise BaselineRegistryError("primary training budgets are not matched")
        if primary[0]["inference_compute_budget"][domain_id] != primary[1]["inference_compute_budget"][domain_id]:
            raise BaselineRegistryError("primary inference budgets are not matched")
        match = validate_primary_pair_equality(
            primary[0]["prospective_matched_compute_record"][domain_id],
            primary[1]["prospective_matched_compute_record"][domain_id],
        )
        if match["equal_prospective_ceiling_and_selection_opportunity"] is not True:
            raise BaselineRegistryError("primary prospective compute does not match")
        if match["b08_resource_values_assigned"] is not False:
            raise BaselineRegistryError("B08 resource values were assigned")
    if tuple(row["control_id"] for row in value["controls"]) != CONTROL_IDS:
        raise BaselineRegistryError("control roster differs")
    for row in value["controls"]:
        validate_control_configuration(row["config"])
        if row["config_sha256"] != config_sha256(row["config"]):
            raise BaselineRegistryError("control config digest differs")
    if tuple(row["family_id"] for row in value["literature_families"]) != COMPARATOR_FAMILY_IDS:
        raise BaselineRegistryError("literature-family roster differs")
    for family in value["literature_families"]:
        for domain_id in DOMAIN_IDS:
            config = family["configs_by_domain"][domain_id]
            validate_family_configuration(config)
            if family["implementation_by_domain"][domain_id]["config_sha256"] != config_sha256(config):
                raise BaselineRegistryError("family config digest differs")
    external = value["external_baselines"]
    if tuple(row["domain_id"] for row in external) != DOMAIN_IDS:
        raise BaselineRegistryError("external-domain roster differs")
    for row in external:
        _validate_capability_matrix(
            row["native_capability_and_extension_statement"]["capability_matrix"]
        )
        if row["config_sha256"] != config_sha256(row["config"]):
            raise BaselineRegistryError("external config digest differs")
        if row["tuning_budget"]["maximum_trials"] != TUNING_TRIAL_LIMIT:
            raise BaselineRegistryError("external tuning budget differs")
    return deepcopy(value)


FROZEN_REGISTRY = build_registry()


__all__ = [
    "ADD_THIN_COMMIT",
    "ADD_THIN_LICENSE_SHA256",
    "ADD_THIN_REPOSITORY",
    "BaselineRegistryError",
    "CAPABILITY_AXES",
    "COMPARATOR_FAMILY_IDS",
    "CONDITIONAL_DRAWS_PER_CASE",
    "CONTROL_IDS",
    "CSDI_COMMIT",
    "CSDI_LICENSE_SHA256",
    "CSDI_REPOSITORY",
    "DOMAIN_IDS",
    "EDITPP_COMMIT",
    "EDITPP_LICENSE_SHA256",
    "EDITPP_REPOSITORY",
    "FINAL_CAPABILITY_STATES",
    "FROZEN_REGISTRY",
    "LOCAL_RELEASE_REVISION",
    "LOCAL_SOURCE_RELEASE_FILES",
    "PRIMARY_METHOD_IDS",
    "build_registry",
    "canonical_json_bytes",
    "conditional_module_parameter_count",
    "config_sha256",
    "frozen_base_parameter_count",
    "inference_compute_budget",
    "local_source_release_sha256",
    "primary_parameter_count",
    "prospective_primary_budget_record",
    "training_compute_budget",
    "validate_control_configuration",
    "validate_family_configuration",
    "validate_registry",
]
