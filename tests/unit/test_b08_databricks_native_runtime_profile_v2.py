from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_native_runtime_profile as v1
from heterodiff.experiments import b08_databricks_native_runtime_profile_v2 as v2


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / v2.PROFILE_PATH
V1_SOURCE = ROOT / "src/heterodiff/experiments/b08_databricks_native_runtime_profile.py"
V1_TEMPLATE = ROOT / v1.PROFILE_PATH
V1_REVIEW = ROOT / (
    "PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1_INDEPENDENT_REVIEW.md"
)
V2_SOURCE = ROOT / (
    "src/heterodiff/experiments/b08_databricks_native_runtime_profile_v2.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def redigest(record):
    return v2.with_semantic_digest(record)


def project_to_v1(record):
    result = deepcopy(record)
    result["schema_version"] = v1.SCHEMA_VERSION
    result["profile_id"] = v1.PROFILE_ID
    result["target"]["operating_system_release"] = "24.04.3 LTS"
    result["record_sha256"] = "0" * 64
    return v1.with_semantic_digest(result)


def observed_v2():
    return v2.bind_observed_capture(
        v2.build_draft_profile(),
        lock_sha256="1" * 64,
        source_revision="2" * 40,
        source_manifest_sha256="3" * 64,
        installed_distribution_metadata_observation_sha256="4" * 64,
        module_origin_observation_sha256="5" * 64,
        python_abi_observation_sha256="6" * 64,
        native_runtime_capture_sha256="7" * 64,
    )


def test_reviewed_v1_predecessor_bytes_are_exactly_preserved_and_pinned():
    assert sha256(V1_SOURCE) == v2.PREDECESSOR_PROFILE_SOURCE_SHA256
    assert sha256(V1_TEMPLATE) == v2.PREDECESSOR_TEMPLATE_FILE_SHA256
    assert sha256(V1_REVIEW) == v2.PREDECESSOR_INDEPENDENT_REVIEW_SHA256
    record = json.loads(V1_TEMPLATE.read_text("ascii"))
    assert record["record_sha256"] == v2.PREDECESSOR_TEMPLATE_RECORD_SHA256
    assert record["target"]["operating_system_release"] == "24.04.3 LTS"


def test_v2_canonical_template_is_exact_unresolved_draft():
    raw = TEMPLATE.read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == v2.canonical_json_bytes(record) + b"\n"
    assert record == v2.build_draft_profile()
    assert v2.validate_profile(record) == record
    assert record["schema_version"] == v2.SCHEMA_VERSION
    assert record["profile_id"] == v2.PROFILE_ID
    assert record["lifecycle_state"] == v2.DRAFT_UNRESOLVED_F152_LOCK
    assert record["target"]["operating_system_release"] == "24.04.4 LTS"
    assert record["f152_lock"]["sha256"] is None
    assert record["resolution"]["unresolved_paths"] == list(
        v2.UNRESOLVED_PATHS
    )


def test_v2_delta_from_v1_is_exactly_identity_domain_path_and_os_release():
    predecessor = v1.build_draft_profile()
    successor = v2.build_draft_profile()
    assert project_to_v1(successor) == predecessor
    assert successor["schema_version"] != predecessor["schema_version"]
    assert successor["profile_id"] != predecessor["profile_id"]
    assert v2.PROFILE_PATH != v1.PROFILE_PATH
    assert v2.RECORD_DOMAIN != v1.RECORD_DOMAIN
    assert successor["target"]["operating_system_release"] == "24.04.4 LTS"
    assert predecessor["target"]["operating_system_release"] == "24.04.3 LTS"


def test_expected_distributions_f153_and_authority_boundary_are_exactly_inherited():
    predecessor = v1.build_draft_profile()
    successor = v2.build_draft_profile()
    for section in (
        "native_route",
        "f152_lock",
        "f153_environment",
        "runtime_bindings",
        "resolution",
        "safety_boundary",
    ):
        assert successor[section] == predecessor[section]
    assert v2.EXPECTED_DISTRIBUTIONS == v1.EXPECTED_DISTRIBUTIONS
    assert v2.EXPECTED_MODULES == v1.EXPECTED_MODULES
    assert v2.F153_ENVIRONMENT == v1.F153_ENVIRONMENT
    assert v2.F153_ENVIRONMENT is not v1.F153_ENVIRONMENT
    assert v2.EXPECTED_DISTRIBUTIONS is not v1.EXPECTED_DISTRIBUTIONS
    assert not any(successor["safety_boundary"].values())


def test_observed_binding_is_exact_v1_semantics_under_v2_identity():
    successor = observed_v2()
    predecessor = v1.bind_observed_capture(
        v1.build_draft_profile(),
        lock_sha256="1" * 64,
        source_revision="2" * 40,
        source_manifest_sha256="3" * 64,
        installed_distribution_metadata_observation_sha256="4" * 64,
        module_origin_observation_sha256="5" * 64,
        python_abi_observation_sha256="6" * 64,
        native_runtime_capture_sha256="7" * 64,
    )
    assert v2.validate_profile(successor) == successor
    assert project_to_v1(successor) == predecessor
    assert successor["lifecycle_state"] == v2.OBSERVED_REVIEW_PENDING
    assert successor["resolution"]["unresolved_paths"] == list(
        v2.REVIEW_PENDING_UNRESOLVED_PATHS
    )
    assert successor["f152_lock"]["complete_transitive_lock"] is False
    assert successor["f152_lock"]["artifact_closure_verified"] is False
    assert successor["runtime_bindings"][
        "installed_payload_closure_verified"
    ] is False
    assert successor["runtime_bindings"][
        "module_distribution_ownership_verified"
    ] is False
    assert successor["runtime_bindings"][
        "every_process_worker_equivalence_verified"
    ] is False
    assert successor["runtime_bindings"][
        "f153_effective_runtime_satisfaction_verified"
    ] is False
    assert successor["resolution"]["eligible_for_scientific_execution"] is False
    assert not any(successor["safety_boundary"].values())


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        (None, "schema_version", v1.SCHEMA_VERSION),
        (None, "profile_id", v1.PROFILE_ID),
        ("target", "operating_system_release", "24.04.3 LTS"),
        ("target", "operating_system_release", "24.04 LTS"),
        ("target", "architecture", "arm64"),
        ("target", "machine_learning_runtime", True),
        ("target", "gpu_enabled", True),
        ("native_route", "custom_container_required", True),
        ("native_route", "network_resolution_or_install_permitted", True),
        ("f152_lock", "complete_transitive_lock", True),
        ("f152_lock", "artifact_closure_verified", True),
        ("runtime_bindings", "installed_payload_closure_verified", True),
        ("runtime_bindings", "module_distribution_ownership_verified", True),
        ("runtime_bindings", "every_process_worker_equivalence_verified", True),
        ("runtime_bindings", "f153_effective_runtime_satisfaction_verified", True),
        ("resolution", "eligible_for_scientific_execution", True),
        ("safety_boundary", "network_or_contact_authorized", True),
        ("safety_boundary", "study_data_access_authorized", True),
        ("safety_boundary", "scientific_execution_authorized", True),
        ("safety_boundary", "tracker_or_timetable_edit_authorized", True),
    ],
)
def test_redigested_identity_platform_or_authority_substitution_fails_closed(
    section, key, value
):
    record = observed_v2()
    if section is None:
        record[key] = value
    else:
        record[section][key] = value
    with pytest.raises(v2.NativeRuntimeProfileV2Error):
        v2.validate_profile(redigest(record))


def test_unknown_keys_noncanonical_types_and_invalid_digest_fail_closed():
    record = v2.build_draft_profile()
    record["unknown"] = False
    with pytest.raises(v2.NativeRuntimeProfileV2Error):
        v2.validate_profile(record)

    record = v2.build_draft_profile()
    record["target"]["pointer_bits"] = 64.0
    with pytest.raises(v2.NativeRuntimeProfileV2Error):
        v2.with_semantic_digest(record)

    record = v2.build_draft_profile()
    record["record_sha256"] = "A" * 64
    with pytest.raises(v2.NativeRuntimeProfileV2Error):
        v2.validate_profile(record)


def test_v1_and_v2_records_are_not_cross_accepted():
    with pytest.raises(v2.NativeRuntimeProfileV2Error):
        v2.validate_profile(v1.build_draft_profile())
    with pytest.raises(v1.NativeRuntimeProfileError):
        v1.validate_profile(v2.build_draft_profile())


def test_v2_module_has_no_io_network_process_spark_or_databricks_import_surface():
    tree = ast.parse(V2_SOURCE.read_text("utf-8"))
    imported_roots = set()
    called_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
    assert imported_roots.isdisjoint(
        {
            "os",
            "pathlib",
            "socket",
            "subprocess",
            "urllib",
            "requests",
            "pyspark",
            "databricks",
        }
    )
    assert called_names.isdisjoint({"open", "exec", "eval", "compile", "input"})
