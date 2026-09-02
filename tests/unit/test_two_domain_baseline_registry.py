"""Independent hostile qualification for the frozen B06 baseline registry."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.experiments import matched_total_compute as f104
from heterodiff.experiments import two_domain_baseline_registry as registry


ROOT = Path(__file__).resolve().parents[2]


class _DictSubclass(dict):
    pass


class _ListSubclass(list):
    pass


def _fresh():
    return registry.build_registry()


def _manual_canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _manual_config_sha256(value):
    return hashlib.sha256(
        b"HETERODIFF-B06-CONFIG-V1\0" + _manual_canonical(value)
    ).hexdigest()


def _set_path(value, path, replacement):
    target = value
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = replacement


def _all_config_rows(value):
    for primary in value["primary_pair"]:
        yield "primary:" + primary["method_id"], primary["config"], primary[
            "config_sha256"
        ]
    for control in value["controls"]:
        yield "control:" + control["control_id"], control["config"], control[
            "config_sha256"
        ]
    for family in value["literature_families"]:
        for domain_id in registry.DOMAIN_IDS:
            config = family["configs_by_domain"][domain_id]
            yield (
                "family:" + family["family_id"] + ":" + domain_id,
                config,
                family["implementation_by_domain"][domain_id]["config_sha256"],
            )
    for external in value["external_baselines"]:
        yield (
            "external:" + external["method_id"],
            external["config"],
            external["config_sha256"],
        )


def test_exact_domain_method_control_and_family_rosters_are_frozen():
    assert registry.DOMAIN_IDS == (
        "physionet-challenge-2012",
        "online-retail-ii",
    )
    assert registry.PRIMARY_METHOD_IDS == (
        "association-aware-guide-plus-residual",
        "unified-direct-conditioner",
    )
    assert registry.CONTROL_IDS == (
        "analytic-guide-only-residual-removed",
        "direct-or-residual-only-analytic-guide-removed",
        "association-destroyed-or-factorized-eventwise",
        "unconditional-base-sanity-reference",
    )
    assert registry.COMPARATOR_FAMILY_IDS == (
        "ngdb-style-auxiliary-guide-plus-correction",
        "deft-style-generalized-h-frozen-base-correction",
        "task-compatible-same-base-smc-or-feynman-kac",
        "closest-variable-cardinality-point-or-edit-generator",
    )
    value = _fresh()
    assert tuple(value["domain_ids"]) == registry.DOMAIN_IDS
    assert tuple(row["method_id"] for row in value["primary_pair"]) == (
        registry.PRIMARY_METHOD_IDS
    )
    assert tuple(row["control_id"] for row in value["controls"]) == (
        registry.CONTROL_IDS
    )
    assert tuple(row["family_id"] for row in value["literature_families"]) == (
        registry.COMPARATOR_FAMILY_IDS
    )
    assert tuple(row["domain_id"] for row in value["external_baselines"]) == (
        registry.DOMAIN_IDS
    )


def test_top_level_and_local_release_fields_are_exact_and_ordered():
    value = _fresh()
    assert tuple(value) == (
        "schema",
        "state",
        "domain_ids",
        "local_source_release",
        "primary_pair",
        "controls",
        "literature_families",
        "external_baselines",
        "external_selection_audit",
        "f104_binding",
        "nonclaims",
    )
    assert value["schema"] == "HETERODIFF_B06_BASELINE_REGISTRY_V1"
    assert value["state"] == (
        "B06_IDENTITIES_CONFIGS_CAPABILITIES_AND_MATCHED_COMPUTE_FROZEN"
    )
    release = value["local_source_release"]
    assert tuple(release) == (
        "repository",
        "revision",
        "digest_domain",
        "files",
        "public_license_grant_claimed",
        "scope",
    )
    assert release["repository"] == registry.LOCAL_REPOSITORY
    assert release["revision"] == registry.LOCAL_RELEASE_REVISION
    assert release["revision"] == "sha256:" + registry.LOCAL_RELEASE_SHA256
    assert release["public_license_grant_claimed"] is False
    assert release["scope"] == "INTERNAL_RESEARCH_SOURCE_IDENTITY_ONLY"


def test_primary_pair_and_config_field_rosters_are_complete():
    value = _fresh()
    for row in value["primary_pair"]:
        assert tuple(row) == (
            "method_id",
            "repository",
            "commit_or_release",
            "config",
            "config_sha256",
            "parameter_count",
            "training_compute_budget",
            "inference_compute_budget",
            "prospective_matched_compute_record",
        )
        assert tuple(row["config"]) == (
            "schema",
            "method_id",
            "same_frozen_base_release_by_domain",
            "domain_configs",
            "test_access_permitted_for_selection",
            "post_test_change_permitted",
        )
        assert row["config"]["test_access_permitted_for_selection"] is False
        assert row["config"]["post_test_change_permitted"] is False
        assert tuple(row["config"]["domain_configs"]) == registry.DOMAIN_IDS
        for domain_id in registry.DOMAIN_IDS:
            domain = row["config"]["domain_configs"][domain_id]
            assert tuple(domain) == (
                "base",
                "conditional_architecture",
                "conditional_modules",
                "conditional_source_class",
                "conditioning_context_encoder_status",
                "parameter_count",
                "training_budget",
                "inference_budget",
            )
            assert tuple(domain["base"]) == (
                "domain_id",
                "f105_event_dimension",
                "maximum_events",
                "architecture",
                "source_class",
                "event_type_interface",
                "event_hidden_width",
                "event_embedding_width",
                "context_dimension",
                "context_hidden_width",
                "context_embedding_width",
                "readout_hidden_width",
                "pooling",
                "reverse_steps",
                "parameter_count_procedure",
                "native_runtime_configuration_cap_limit",
                "domain_scale_runtime_status",
                "current_runtime_qualification_claimed",
            )


def test_control_field_rosters_modes_and_noninterchangeability_are_explicit():
    value = _fresh()
    expected_modes = (
        (["ANALYTIC_GUIDE", "FROZEN_BASE"], ["LEARNED_RESIDUAL"]),
        (["LEARNED_RESIDUAL", "FROZEN_BASE"], ["ANALYTIC_GUIDE"]),
        (
            ["FACTORIZED_EVENTWISE_CONDITIONER", "FROZEN_BASE"],
            ["CROSS_EVENT_ASSOCIATION_FEATURES"],
        ),
        (["FROZEN_BASE"], ["ALL_CONDITIONERS_AND_GUIDES"]),
    )
    for row, (active, removed) in zip(value["controls"], expected_modes):
        assert tuple(row) == (
            "control_id",
            "implementation",
            "config",
            "config_sha256",
        )
        config = row["config"]
        assert tuple(config) == (
            "schema",
            "control_id",
            "implementation",
                "domain_ids",
                "same_frozen_base_release",
                "mode",
                "training_compute_budget_by_domain",
                "inference_compute_budget_by_domain",
                "compute_is_charged_to_control",
                "may_discharge_literature_family_without_proof",
                "b12_runtime_qualification_required",
                "current_runtime_qualification_claimed",
                "post_test_change_permitted",
            )
        assert config["implementation"] == (
            "B06_STATIC_CONTROL_CONFIGURATION_CONTRACT::"
            "heterodiff.experiments.two_domain_baseline_registry:"
            "validate_control_configuration::B12_RUNTIME_REQUIRED"
        )
        assert config["mode"] == {
            "active_components": active,
            "removed_components": removed,
        }
        assert config["compute_is_charged_to_control"] is True
        assert config["may_discharge_literature_family_without_proof"] is False
        assert config["b12_runtime_qualification_required"] is True
        assert config["current_runtime_qualification_claimed"] is False
        assert config["post_test_change_permitted"] is False
        assert tuple(config["training_compute_budget_by_domain"]) == (
            registry.DOMAIN_IDS
        )
        assert tuple(config["inference_compute_budget_by_domain"]) == (
            registry.DOMAIN_IDS
        )
        for domain_id in registry.DOMAIN_IDS:
            assert config["training_compute_budget_by_domain"][domain_id] == (
                registry.training_compute_budget(domain_id)
            )
            assert config["inference_compute_budget_by_domain"][domain_id] == (
                registry.inference_compute_budget(domain_id)
            )
        registry.validate_control_configuration(config)


def test_literature_family_fields_and_both_domain_rows_are_complete():
    value = _fresh()
    for family in value["literature_families"]:
        assert tuple(family) == (
            "family_id",
            "implementation_by_domain",
            "inapplicability_or_equivalence_justification_by_domain",
            "configs_by_domain",
        )
        assert tuple(family["implementation_by_domain"]) == registry.DOMAIN_IDS
        assert tuple(family["configs_by_domain"]) == registry.DOMAIN_IDS
        assert tuple(
            family["inapplicability_or_equivalence_justification_by_domain"]
        ) == registry.DOMAIN_IDS
        for domain_id in registry.DOMAIN_IDS:
            implementation = family["implementation_by_domain"][domain_id]
            assert tuple(implementation) == (
                "implementation_id",
                "source_interface",
                "config_sha256",
                "capability_matrix",
                "training_compute_budget_id",
                "inference_compute_budget_id",
                "b12_runtime_qualification_required",
            )
            config = family["configs_by_domain"][domain_id]
            assert tuple(config) == (
                "schema",
                "family_id",
                "domain_id",
                "adapter_id",
                "source_interface",
                "origin",
                "objective",
                "task_interface",
                "conditioning_semantics",
                "training_compute_budget",
                "inference_compute_budget",
                "capability_matrix",
                "extension_license_scope",
                "b12_runtime_qualification_required",
                "post_test_change_permitted",
            )
            assert implementation["implementation_id"] == config["adapter_id"]
            assert implementation["source_interface"] == config["source_interface"]
            assert config["source_interface"] == (
                "heterodiff.experiments.two_domain_baseline_adapter_contract:"
                "registry_adapter_declaration"
            )
            assert implementation["training_compute_budget_id"] == config[
                "training_compute_budget"
            ]["budget_id"]
            assert implementation["inference_compute_budget_id"] == config[
                "inference_compute_budget"
            ]["budget_id"]
            assert config["training_compute_budget"] == (
                registry.training_compute_budget(domain_id)
            )
            assert config["inference_compute_budget"] == (
                registry.inference_compute_budget(domain_id)
            )
            assert implementation["b12_runtime_qualification_required"] is True
            assert config["post_test_change_permitted"] is False
            registry.validate_family_configuration(config)


def test_every_capability_matrix_has_exact_axes_order_and_final_state():
    value = _fresh()
    matrices = []
    for family in value["literature_families"]:
        for domain_id in registry.DOMAIN_IDS:
            matrices.append(family["configs_by_domain"][domain_id]["capability_matrix"])
            matrices.append(
                family["implementation_by_domain"][domain_id]["capability_matrix"]
            )
    for external in value["external_baselines"]:
        matrices.append(external["config"]["capability_matrix"])
        matrices.append(
            external["native_capability_and_extension_statement"][
                "capability_matrix"
            ]
        )
    assert len(matrices) == 20
    for matrix in matrices:
        assert tuple(matrix) == registry.CAPABILITY_AXES
        assert set(matrix.values()) <= registry.FINAL_CAPABILITY_STATES
        assert "UNKNOWN" not in matrix.values()
        assert "UNSUPPORTED" not in matrix.values()


def test_local_source_release_hashes_are_independently_recomputed_from_disk():
    value = _fresh()
    rows = value["local_source_release"]["files"]
    assert [(row["path"], row["raw_sha256"]) for row in rows] == list(
        registry.LOCAL_SOURCE_RELEASE_FILES
    )
    assert len({row["path"] for row in rows}) == len(rows) == 8
    for row in rows:
        path = ROOT / row["path"]
        assert path.is_file()
        assert not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["raw_sha256"]


def test_local_source_release_aggregate_is_independently_recomputed():
    digest = hashlib.sha256(
        b"HETERODIFF-B06-LOCAL-METHOD-SOURCE-RELEASE-V1\0"
    )
    for path, raw_sha256 in registry.LOCAL_SOURCE_RELEASE_FILES:
        digest.update(path.encode("ascii"))
        digest.update(b"\0")
        digest.update(raw_sha256.encode("ascii"))
        digest.update(b"\0")
    assert digest.hexdigest() == registry.LOCAL_RELEASE_SHA256
    assert registry.local_source_release_sha256() == registry.LOCAL_RELEASE_SHA256


def test_every_config_digest_is_independently_recomputed():
    value = _fresh()
    rows = list(_all_config_rows(value))
    assert len(rows) == 16
    for label, config, claimed in rows:
        assert claimed == _manual_config_sha256(config), label
        assert claimed == registry.config_sha256(config), label
        assert len(claimed) == 64 and claimed == claimed.lower()


def test_tuning_candidate_grid_digests_are_exact_and_selection_is_test_blind():
    value = _fresh()
    for external in value["external_baselines"]:
        tuning = external["tuning_budget"]
        assert tuning is external["config"]["tuning_budget"]
        assert tuning["maximum_trials"] == registry.TUNING_TRIAL_LIMIT == 8
        assert tuning["candidate_grid_sha256"] == _manual_config_sha256(
            tuning["candidate_grid"]
        )
        assert tuning["selection_data"] == "TRAIN_AND_VALIDATION_ONLY"
        assert tuning["selection_metric"] == "F105_VALIDATION_SCORE_LOWER_IS_BETTER"
        assert tuning["tie_rule"] == "LEXICOGRAPHIC_CANONICAL_CONFIG_BYTES"
        assert tuning["failed_or_aborted_trials_charged"] is True
        assert tuning["test_access_permitted"] is False
        assert tuning["unused_transfer_or_postresult_topup_permitted"] is False


@pytest.mark.parametrize(
    ("domain_id", "base", "conditional", "total"),
    [
        ("physionet-challenge-2012", 105601, 105601, 211202),
        ("online-retail-ii", 92545, 92545, 185090),
    ],
)
def test_parameter_counts_are_exact_and_primary_pair_matched(
    domain_id, base, conditional, total
):
    value = _fresh()
    assert registry.frozen_base_parameter_count(domain_id) == base
    assert registry.conditional_module_parameter_count(domain_id) == conditional
    expected = {
        "frozen_unconditional_base": base,
        "trainable_conditioner": conditional,
        "total": total,
    }
    assert registry.primary_parameter_count(domain_id) == expected
    for row in value["primary_pair"]:
        assert row["parameter_count"][domain_id] == expected
        assert row["config"]["domain_configs"][domain_id]["parameter_count"] == expected
    assert value["primary_pair"][0]["parameter_count"][domain_id] == (
        value["primary_pair"][1]["parameter_count"][domain_id]
    )


def test_frozen_base_count_executes_the_hashed_deepsets_count_routine_exactly():
    source_path = ROOT / "src/heterodiff/models/configuration_energy_torch.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    architecture = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ConfigurationEnergyArchitecture"
    )
    source_method = next(
        node
        for node in architecture.body
        if isinstance(node, ast.FunctionDef) and node.name == "_parameter_count"
    )
    executable_method = copy.deepcopy(source_method)
    executable_method.decorator_list = []
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__",
                names=[ast.alias(name="annotations")],
                level=0,
            ),
            executable_method,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(source_path), "exec"), namespace)
    production_count = namespace["_parameter_count"]

    for domain_id in registry.DOMAIN_IDS:
        exact = production_count(
            (registry.EVENT_DIMENSION_BY_DOMAIN[domain_id],),
            context_dimension=64,
            event_hidden_width=128,
            event_embedding_width=128,
            context_hidden_width=128,
            context_embedding_width=128,
            readout_hidden_width=128,
        )
        assert exact == registry.frozen_base_parameter_count(domain_id)


def test_primary_pair_shares_release_but_preserves_distinct_conditioning_roles():
    value = _fresh()
    guide, direct = value["primary_pair"]
    for row in (guide, direct):
        assert row["repository"] == registry.LOCAL_REPOSITORY
        assert row["commit_or_release"] == registry.LOCAL_RELEASE_REVISION
        assert row["config"]["same_frozen_base_release_by_domain"] == {
            domain_id: registry.LOCAL_RELEASE_REVISION
            for domain_id in registry.DOMAIN_IDS
        }
    for domain_id in registry.DOMAIN_IDS:
        assert guide["config"]["domain_configs"][domain_id][
            "conditional_architecture"
        ] == "ANALYTIC_ASSOCIATION_GUIDE_PLUS_ONE_LEARNED_RESIDUAL"
        assert direct["config"]["domain_configs"][domain_id][
            "conditional_architecture"
        ] == "UNIFIED_DIRECT_ONE_LEARNED_CONDITIONER"


def test_primary_architecture_is_bound_to_hashed_typed_deepsets_classes():
    value = _fresh()
    guide, direct = value["primary_pair"]
    for row in (guide, direct):
        for domain_id in registry.DOMAIN_IDS:
            domain = row["config"]["domain_configs"][domain_id]
            base = domain["base"]
            assert base["architecture"] == "HASHED_TYPED_DEEPSETS_ENERGY_V1"
            assert base["source_class"] == (
                "heterodiff.models.configuration_energy_torch:"
                "BoundedConfigurationEnergy"
            )
            assert base["event_type_interface"] == (
                "ONE_F105_EXACT_VECTOR_TYPE_PER_DOMAIN"
            )
            assert base["pooling"] == (
                "EXACT_MULTIPLICITY_PRESERVING_SEGMENT_SUM"
            )
            assert base["parameter_count_procedure"] == (
                "CONFIGURATION_ENERGY_ARCHITECTURE_PARAMETER_COUNT_"
                "EXACT_INTEGER_V1"
            )
            assert base["native_runtime_configuration_cap_limit"] == 10_000
            assert "B12" in base["domain_scale_runtime_status"]
            assert base["current_runtime_qualification_claimed"] is False
            assert domain["conditional_modules"] == 1
            assert domain["conditioning_context_encoder_status"] == (
                "FROZEN_64_DIMENSION_INTERFACE_B12_IMPLEMENTATION_REQUIRED"
            )
    assert guide["config"]["domain_configs"][registry.PHYSIONET_DOMAIN_ID][
        "conditional_source_class"
    ] == (
        "heterodiff.models.configuration_residual_torch:"
        "CertifiedConditionalResidualCheckpoint"
    )
    assert direct["config"]["domain_configs"][registry.PHYSIONET_DOMAIN_ID][
        "conditional_source_class"
    ] == (
        "heterodiff.models.configuration_energy_torch:"
        "CertifiedConfigurationEnergyCheckpoint"
    )


def test_primary_training_and_inference_budgets_are_exactly_equal():
    value = _fresh()
    guide, direct = value["primary_pair"]
    for domain_id in registry.DOMAIN_IDS:
        training = guide["training_compute_budget"][domain_id]
        inference = guide["inference_compute_budget"][domain_id]
        assert training == direct["training_compute_budget"][domain_id]
        assert inference == direct["inference_compute_budget"][domain_id]
        assert training == registry.training_compute_budget(domain_id)
        assert inference == registry.inference_compute_budget(domain_id)
        assert training == guide["config"]["domain_configs"][domain_id][
            "training_budget"
        ]
        assert inference == guide["config"]["domain_configs"][domain_id][
            "inference_budget"
        ]
        for budget in (training, inference):
            assert budget["formula_id"] == f104.CALCULATOR_ID
            assert tuple(budget["phase_event_count_ceilings"]) == f104.PHASES
            for phase in f104.PHASES:
                counts = budget["phase_event_count_ceilings"][phase]
                assert tuple(counts) == f104.RESOURCE_EVENTS
                assert all(type(count) is int and count >= 0 for count in counts.values())
            assert budget["prospective_primary_pair_equality_required"] is True
            assert budget["failed_attempts_and_author_extensions_charged"] is True
            assert budget["unused_transfer_or_postresult_topup_permitted"] is False
            assert budget["hardware_weights_and_capacity_owned_by_B08"] is True


def test_primary_prospective_compute_records_are_valid_equal_and_leave_b08_open():
    value = _fresh()
    guide, direct = value["primary_pair"]
    assert tuple(guide["prospective_matched_compute_record"]) == registry.DOMAIN_IDS
    assert tuple(direct["prospective_matched_compute_record"]) == registry.DOMAIN_IDS
    for domain_id in registry.DOMAIN_IDS:
        guide_record = guide["prospective_matched_compute_record"][domain_id]
        direct_record = direct["prospective_matched_compute_record"][domain_id]
        for record, method_id, role in (
            (guide_record, registry.PRIMARY_METHOD_ID, f104.PRIMARY_METHOD_ROLE),
            (
                direct_record,
                registry.PRIMARY_COMPARATOR_ID,
                f104.PRIMARY_COMPARATOR_ROLE,
            ),
        ):
            assert tuple(record) == (
                "schema_version",
                "budget_id",
                "method_id",
                "method_role",
                "domain_id",
                "training_compute_budget_id",
                "inference_compute_budget_id",
                "calibration_weight_record_id",
                "scalar_ceiling_id",
                "hard_axis_ceiling_ids",
                "fairness_bindings",
                "accounting_policy",
                "unpopulated_b08_values",
            )
            assert record["schema_version"] == f104.PROSPECTIVE_BUDGET_SCHEMA_VERSION
            assert record["method_id"] == method_id
            assert record["method_role"] == role
            assert record["domain_id"] == domain_id
            assert record["training_compute_budget_id"] == (
                registry.training_compute_budget(domain_id)["budget_id"]
            )
            assert record["inference_compute_budget_id"] == (
                registry.inference_compute_budget(domain_id)["budget_id"]
            )
            assert tuple(record["hard_axis_ceiling_ids"]) == f104.HARD_AXES
            assert len(set(record["hard_axis_ceiling_ids"].values())) == len(
                f104.HARD_AXES
            )
            assert tuple(record["fairness_bindings"]) == f104.FAIRNESS_BINDING_KEYS
            assert record["fairness_bindings"]["metric_workload_id"] == (
                "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
            )
            assert record["accounting_policy"] == {
                "failed_attempts_charged": True,
                "author_extensions_charged": True,
                "unique_preprocessing_charged": True,
                "unused_allocation_transfer_permitted": False,
                "post_result_top_up_permitted": False,
            }
            assert tuple(record["unpopulated_b08_values"]) == (
                f104.UNPOPULATED_B08_VALUE_KEYS
            )
            assert set(record["unpopulated_b08_values"].values()) == {False}
            assert f104.validate_prospective_budget_record(record) == record

        equality = f104.validate_primary_pair_equality(
            guide_record, direct_record
        )
        assert equality["domain_id"] == domain_id
        assert equality["matched_fields"] == list(f104.PRIMARY_PAIR_MATCHED_FIELDS)
        assert equality["equal_prospective_ceiling_and_selection_opportunity"] is True
        assert equality["realized_resource_equality_claimed"] is False
        assert equality["b08_resource_values_assigned"] is False


def test_frozen_training_budget_counts_are_independently_derived():
    for domain_id in registry.DOMAIN_IDS:
        budget = registry.training_compute_budget(domain_id)[
            "phase_event_count_ceilings"
        ]
        assert all(value == 0 for value in budget["PILOT"].values())
        assert all(value == 0 for value in budget["CONFIRMATORY_INFERENCE"].values())
        tuning = budget["TUNING"]
        final = budget["FINAL_TRAINING"]
        assert tuning["BASE_FORWARD"] == 8 * 1024
        assert tuning["GUIDE_EVALUATION"] == 8 * 1024
        assert tuning["ODE_OR_SDE_STEP"] == 8 * 1024 * 4
        assert tuning["DATA_ADAPTER_RECORD"] == 8 * 1024 * 16
        assert tuning["METRIC_DRAW_EVALUATION"] == 8 * 128
        assert final["BASE_FORWARD"] == 256 * 4096
        assert final["GUIDE_EVALUATION"] == 256 * 4096
        assert final["ODE_OR_SDE_STEP"] == 256 * 4096 * 4
        assert final["DATA_ADAPTER_RECORD"] == 256 * 4096 * 16


def test_frozen_inference_budget_counts_are_independently_derived():
    caps = {
        registry.PHYSIONET_DOMAIN_ID: 131_072,
        registry.RETAIL_DOMAIN_ID: 1_067_371,
    }
    draws = 256 * 128 * 1 * 64
    for domain_id in registry.DOMAIN_IDS:
        budget = registry.inference_compute_budget(domain_id)[
            "phase_event_count_ceilings"
        ]
        assert all(value == 0 for value in budget["PILOT"].values())
        assert all(value == 0 for value in budget["TUNING"].values())
        assert all(value == 0 for value in budget["FINAL_TRAINING"].values())
        inference = budget["CONFIRMATORY_INFERENCE"]
        assert inference["BASE_FORWARD"] == draws * 256
        assert inference["CONDITIONER_FORWARD"] == draws * 256
        assert inference["GUIDE_EVALUATION"] == draws * 256
        assert inference["ODE_OR_SDE_STEP"] == draws * 256
        assert inference["DATA_ADAPTER_RECORD"] == draws * caps[domain_id]
        assert inference["METRIC_DRAW_EVALUATION"] == 256 * 128 * 64 * 64


def test_external_baseline_selection_is_exactly_csdi_and_editpp():
    value = _fresh()
    physionet, retail = value["external_baselines"]
    assert (
        physionet["domain_id"],
        physionet["method_id"],
        physionet["repository"],
        physionet["commit"],
    ) == (
        registry.PHYSIONET_DOMAIN_ID,
        "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1",
        "https://github.com/ermongroup/CSDI",
        "7f24a436f08d98853a6b43d4f7f04e5a65ecdf27",
    )
    assert (
        retail["domain_id"],
        retail["method_id"],
        retail["repository"],
        retail["commit"],
    ) == (
        registry.RETAIL_DOMAIN_ID,
        "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1",
        "https://github.com/martenlienen/editpp",
        "3113d2ee32086b11dd1f4a47d4bdbc5e8cd8f918",
    )
    assert registry.ADD_THIN_REPOSITORY not in {
        row["repository"] for row in value["external_baselines"]
    }


def test_external_license_and_upstream_file_receipts_are_exact():
    value = _fresh()
    physionet, retail = value["external_baselines"]
    for row, digest, size in (
        (physionet, registry.CSDI_LICENSE_SHA256, registry.CSDI_LICENSE_BYTES),
        (retail, registry.EDITPP_LICENSE_SHA256, registry.EDITPP_LICENSE_BYTES),
    ):
        assert row["license"] == {
            "path": "LICENSE",
            "spdx": "MIT",
            "raw_sha256": digest,
            "bytes": size,
            "scope": (
                "CODE_CONFIGS_AND_MODIFICATIONS; "
                "WEIGHTS_SEPARATELY_CUSTODIED_IF_USED"
            ),
        }
    assert physionet["config"]["upstream_config_sha256"] == (
        registry.CSDI_UPSTREAM_CONFIG_SHA256
    )
    assert physionet["config"]["upstream_entrypoint_sha256"] == (
        registry.CSDI_UPSTREAM_ENTRYPOINT_SHA256
    )
    assert physionet["config"]["upstream_requirements_sha256"] == (
        registry.CSDI_REQUIREMENTS_SHA256
    )
    assert retail["config"]["upstream_entrypoint_sha256"] == (
        registry.EDITPP_ENTRYPOINT_SHA256
    )
    assert retail["config"]["upstream_train_config_sha256"] == (
        registry.EDITPP_TRAIN_CONFIG_SHA256
    )
    assert retail["config"]["upstream_task_config_sha256"] == (
        registry.EDITPP_TASK_CONFIG_SHA256
    )
    assert retail["config"]["upstream_model_config_sha256"] == (
        registry.EDITPP_MODEL_CONFIG_SHA256
    )
    assert retail["config"]["upstream_lock_sha256"] == registry.EDITPP_LOCK_SHA256


def test_external_native_capabilities_and_author_extension_gaps_are_explicit():
    value = _fresh()
    csdi, editpp = value["external_baselines"]
    csdi_matrix = csdi["config"]["capability_matrix"]
    assert csdi_matrix["MISSING_OR_PARTIALLY_OBSERVED_MARKS"] == "NATIVE"
    assert csdi_matrix["CONDITIONAL_SAMPLING_INTERFACE"] == "NATIVE"
    assert csdi_matrix["SHARED_BASE_COMPATIBILITY"] == "INAPPLICABLE_WITH_PROOF"
    for axis in (
        "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION",
        "DOMAIN_PHYSICAL_TIME",
        "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY",
        "TYPED_EVENTS_AND_CONTINUOUS_MARKS",
        "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY",
    ):
        assert csdi_matrix[axis] == "AUTHOR_EXTENSION"

    editpp_matrix = editpp["config"]["capability_matrix"]
    assert editpp_matrix["DOMAIN_PHYSICAL_TIME"] == "NATIVE"
    assert editpp_matrix["SHARED_BASE_COMPATIBILITY"] == "INAPPLICABLE_WITH_PROOF"
    for axis in (
        "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION",
        "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY",
        "TYPED_EVENTS_AND_CONTINUOUS_MARKS",
        "MISSING_OR_PARTIALLY_OBSERVED_MARKS",
        "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY",
        "CONDITIONAL_SAMPLING_INTERFACE",
    ):
        assert editpp_matrix[axis] == "AUTHOR_EXTENSION"

    for row in (csdi, editpp):
        assert row["config"]["source_interface"] == (
            "heterodiff.experiments.two_domain_baseline_adapter_contract:"
            "registry_adapter_declaration"
        )
        assert row["config"]["training_compute_budget"] == (
            registry.training_compute_budget(row["domain_id"])
        )
        assert row["config"]["inference_compute_budget"] == (
            registry.inference_compute_budget(row["domain_id"])
        )
        assert row["config"]["b12_runtime_qualification_required"] is True
        statement = row["native_capability_and_extension_statement"]
        assert statement["capability_matrix"] == row["config"]["capability_matrix"]
        assert statement["author_extensions"] == row["config"]["author_extensions"]
        assert len(statement["author_extensions"]) == 4
        assert len(set(statement["author_extensions"])) == 4
        assert statement["all_extension_compute_charged"] is True
        assert statement["runtime_qualification_owned_by_B12"] is True


def test_selection_audit_is_bounded_and_does_not_claim_universal_sota():
    audit = _fresh()["external_selection_audit"]
    assert audit["selection_rule_id"] == (
        "B06-STRONGEST-ELIGIBLE-WITHIN-FROZEN-AUDIT-ROSTER-V1"
    )
    assert audit["universal_state_of_the_art_claimed"] is False
    assert audit["criteria_in_order"] == [
        "TASK_COMPATIBLE_CONDITIONAL_GENERATION",
        "OFFICIAL_PUBLIC_IMPLEMENTATION",
        "IMMUTABLE_REVISION",
        "RETRIEVED_CODE_LICENSE",
        "DOMAIN_EVIDENCE",
        "FINITE_ADAPTER_AND_TUNING_PLAN",
    ]
    assert audit["physionet_decision"]["selected"] == (
        "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1"
    )
    assert audit["retail_decision"]["selected"] == (
        "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1"
    )
    assert len(audit["physionet_decision"]["audited_alternatives"]) == 3
    assert len(audit["retail_decision"]["audited_alternatives"]) == 4
    assert any(
        "ADD_THIN" in item
        for item in audit["retail_decision"]["audited_alternatives"]
    )


def test_literature_origins_and_equivalence_nonclaims_are_explicit():
    value = _fresh()
    families = {
        row["family_id"]: row for row in value["literature_families"]
    }
    for family_id in registry.COMPARATOR_FAMILY_IDS:
        for domain_id in registry.DOMAIN_IDS:
            origin = families[family_id]["configs_by_domain"][domain_id]["origin"]
            assert origin["upstream_code_used"] is False
    edit_family = families[registry.COMPARATOR_FAMILY_IDS[3]]
    for domain_id in registry.DOMAIN_IDS:
        origin = edit_family["configs_by_domain"][domain_id]["origin"]
        assert origin["upstream_repository"] == registry.EDITPP_REPOSITORY
        assert origin["upstream_commit_observed"] == registry.EDITPP_COMMIT
        assert "FUTURE_B12_ADAPTER" in origin["reason"]

    for family_id, family in families.items():
        for domain_id in registry.DOMAIN_IDS:
            justification = family[
                "inapplicability_or_equivalence_justification_by_domain"
            ][domain_id]
            same_retail = (
                family_id == registry.COMPARATOR_FAMILY_IDS[3]
                and domain_id == registry.RETAIL_DOMAIN_ID
            )
            assert justification["inapplicability_claimed"] is False
            assert justification["cross_row_equivalence_claimed"] is same_retail
            assert justification["b12_execution_or_result_claimed"] is False
            expected = "MATCH" if same_retail else "DISTINCT_ROW"
            assert set(justification["equivalence_dimensions"].values()) == {
                expected
            }


def test_f104_boundary_and_project_nonclaims_are_exact():
    value = _fresh()
    assert value["f104_binding"] == {
        "formula": "C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]",
        "formula_semantic_sha256": (
            "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b"
        ),
        "primary_training_budgets_equal_within_domain": True,
        "primary_inference_budgets_equal_within_domain": True,
        "hardware_calibration_weights_populated": False,
        "b08_remains_open": True,
    }
    assert value["nonclaims"] == {
        "external_packages_installed_or_executed": False,
        "training_or_inference_executed": False,
        "hardware_or_capacity_selected": False,
        "b08_closed": False,
        "b12_closed": False,
        "formal_test_or_result_created": False,
        "submission_ready": False,
    }


def test_canonical_registry_validates_and_returns_a_detached_copy():
    canonical = _fresh()
    result = registry.validate_registry(canonical)
    assert result == canonical == registry.FROZEN_REGISTRY
    assert result is not canonical
    assert result["primary_pair"] is not canonical["primary_pair"]
    result["state"] = "MUTATED"
    assert canonical["state"] != "MUTATED"
    assert registry.FROZEN_REGISTRY["state"] != "MUTATED"
    assert registry.build_registry() == canonical


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("schema",), "ALIEN"),
        (("state",), "DRAFT"),
        (("domain_ids",), ["online-retail-ii", "physionet-challenge-2012"]),
        (("local_source_release", "repository"), "content-addressed:alien"),
        (("local_source_release", "revision"), "sha256:" + "0" * 64),
        (("local_source_release", "files", 0, "raw_sha256"), "0" * 64),
        (("local_source_release", "public_license_grant_claimed"), True),
        (("primary_pair", 0, "method_id"), "alien-primary"),
        (("primary_pair", 0, "config_sha256"), "0" * 64),
        (
            ("primary_pair", 0, "parameter_count", "physionet-challenge-2012", "total"),
            1,
        ),
        (
            (
                "primary_pair",
                1,
                "training_compute_budget",
                "physionet-challenge-2012",
                "formula_id",
            ),
            "ALIEN",
        ),
        (("controls", 0, "control_id"), "alien-control"),
        (("controls", 1, "config_sha256"), "0" * 64),
        (("controls", 2, "config", "post_test_change_permitted"), True),
        (("literature_families", 0, "family_id"), "alien-family"),
        (
            (
                "literature_families",
                1,
                "configs_by_domain",
                "physionet-challenge-2012",
                "capability_matrix",
                "CONDITIONAL_SAMPLING_INTERFACE",
            ),
            "UNKNOWN",
        ),
        (
            (
                "literature_families",
                2,
                "implementation_by_domain",
                "online-retail-ii",
                "config_sha256",
            ),
            "0" * 64,
        ),
        (
            (
                "literature_families",
                3,
                "inapplicability_or_equivalence_justification_by_domain",
                "online-retail-ii",
                "b12_execution_or_result_claimed",
            ),
            True,
        ),
        (("external_baselines", 0, "repository"), "https://example.invalid"),
        (("external_baselines", 0, "commit"), "0" * 40),
        (("external_baselines", 0, "license", "spdx"), "UNKNOWN"),
        (("external_baselines", 1, "license", "raw_sha256"), "0" * 64),
        (("external_baselines", 1, "config_sha256"), "0" * 64),
        (
            (
                "external_baselines",
                0,
                "native_capability_and_extension_statement",
                "capability_matrix",
                "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION",
            ),
            "UNSUPPORTED",
        ),
        (("external_baselines", 1, "tuning_budget", "maximum_trials"), 9),
        (("external_selection_audit", "universal_state_of_the_art_claimed"), True),
        (("f104_binding", "hardware_calibration_weights_populated"), True),
        (("f104_binding", "b08_remains_open"), False),
        (("nonclaims", "external_packages_installed_or_executed"), True),
        (("nonclaims", "b12_closed"), True),
        (("nonclaims", "submission_ready"), True),
    ],
)
def test_hostile_semantic_mutations_fail_closed(path, replacement):
    value = _fresh()
    _set_path(value, path, replacement)
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_registry(value)


def test_missing_extra_and_reordered_roster_rows_fail_closed():
    for mutate in (
        lambda value: value["controls"].pop(),
        lambda value: value["primary_pair"].reverse(),
        lambda value: value["literature_families"].reverse(),
        lambda value: value["external_baselines"].reverse(),
        lambda value: value.__setitem__("alien", None),
    ):
        candidate = _fresh()
        mutate(candidate)
        with pytest.raises(registry.BaselineRegistryError):
            registry.validate_registry(candidate)


def test_nested_tuple_and_json_carrier_subclasses_fail_closed():
    candidates = []
    value = _fresh()
    value["domain_ids"] = tuple(value["domain_ids"])
    candidates.append(value)

    value = _fresh()
    value["controls"][0]["config"]["mode"]["active_components"] = tuple(
        value["controls"][0]["config"]["mode"]["active_components"]
    )
    candidates.append(value)

    value = _fresh()
    value["primary_pair"][0]["config"] = _DictSubclass(
        value["primary_pair"][0]["config"]
    )
    candidates.append(value)

    value = _fresh()
    value["external_baselines"][0]["config"]["author_extensions"] = _ListSubclass(
        value["external_baselines"][0]["config"]["author_extensions"]
    )
    candidates.append(value)

    for candidate in candidates:
        with pytest.raises(registry.BaselineRegistryError, match="non-exact JSON"):
            registry.validate_registry(candidate)


@pytest.mark.parametrize("hostile", [1.0, float("nan"), object(), (1, 2)])
def test_config_digest_refuses_nonexact_or_nonjson_carriers(hostile):
    with pytest.raises(registry.BaselineRegistryError):
        registry.config_sha256({"hostile": hostile})


def test_top_level_dictionary_subclass_is_refused():
    with pytest.raises(TypeError, match="exact dictionary"):
        registry.validate_registry(_DictSubclass(_fresh()))


def test_control_and_family_validators_reject_role_or_boundary_mutations():
    value = _fresh()
    control = copy.deepcopy(value["controls"][0]["config"])
    control["control_id"] = "alien"
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_control_configuration(control)
    control = copy.deepcopy(value["controls"][0]["config"])
    control["post_test_change_permitted"] = True
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_control_configuration(control)

    family = copy.deepcopy(value["literature_families"][0]["configs_by_domain"][
        registry.PHYSIONET_DOMAIN_ID
    ])
    family["domain_id"] = "alien"
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_family_configuration(family)
    family = copy.deepcopy(value["literature_families"][0]["configs_by_domain"][
        registry.PHYSIONET_DOMAIN_ID
    ])
    family["capability_matrix"][registry.CAPABILITY_AXES[0]] = "UNKNOWN"
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_family_configuration(family)
    family = copy.deepcopy(value["literature_families"][0]["configs_by_domain"][
        registry.PHYSIONET_DOMAIN_ID
    ])
    family["b12_runtime_qualification_required"] = False
    with pytest.raises(registry.BaselineRegistryError):
        registry.validate_family_configuration(family)
