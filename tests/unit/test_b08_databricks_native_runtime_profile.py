from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_native_runtime_profile as native


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / native.PROFILE_PATH


def redigest(record):
    return native.with_semantic_digest(record)


def observed_profile():
    return native.bind_observed_capture(
        native.build_draft_profile(),
        lock_sha256="1" * 64,
        source_revision="2" * 40,
        source_manifest_sha256="3" * 64,
        installed_distribution_metadata_observation_sha256="4" * 64,
        module_origin_observation_sha256="5" * 64,
        python_abi_observation_sha256="6" * 64,
        native_runtime_capture_sha256="7" * 64,
    )


def test_canonical_template_is_exact_unresolved_draft():
    raw = TEMPLATE.read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == native.canonical_json_bytes(record) + b"\n"
    assert record == native.build_draft_profile()
    assert native.validate_profile(record) == record
    assert record["lifecycle_state"] == native.DRAFT_UNRESOLVED_F152_LOCK
    assert record["f152_lock"]["path"] == native.F152_LOCK_PATH
    assert record["f152_lock"]["sha256"] is None
    assert record["resolution"]["unresolved_paths"] == list(native.UNRESOLVED_PATHS)


def test_native_route_has_no_container_registry_instance_profile_or_network():
    route = native.build_draft_profile()["native_route"]
    assert route == {
        "route_kind": "NATIVE_DBR_HASH_LOCKED_WHEELHOUSE",
        "custom_container_required": False,
        "container_registry_required": False,
        "aws_instance_profile_required": False,
        "network_resolution_or_install_permitted": False,
        "editable_install_permitted": False,
        "sdist_install_permitted": False,
        "pip_no_index_required": True,
        "pip_require_hashes_required": True,
        "pip_only_binary_required": True,
        "module_origin_observation_required": True,
        "module_distribution_ownership_claimed": False,
    }


def test_exact_native_dbr_target_and_all_15_f153_values_are_preserved():
    record = native.build_draft_profile()
    assert record["target"] == {
        "service": "DATABRICKS",
        "cloud_provider": "AWS",
        "compute_mode": "CLASSIC_DEDICATED_SINGLE_NODE",
        "runtime_engine": "STANDARD",
        "machine_learning_runtime": False,
        "photon_enabled": False,
        "databricks_runtime_release": "17.3 LTS",
        "databricks_runtime_version_prefix": "17.3",
        "spark_version": "4.0.0",
        "python_implementation": "CPython",
        "python_version": "3.12.3",
        "python_abi": "cp312",
        "operating_system_family": "Linux",
        "operating_system_distribution": "Ubuntu",
        "operating_system_release": "24.04.3 LTS",
        "architecture": "x86_64",
        "pointer_bits": 64,
        "byteorder": "little",
        "cpu_only": True,
        "gpu_enabled": False,
    }
    assert len(record["f153_environment"]) == 15
    assert record["f153_environment"] == native.F153_ENVIRONMENT
    assert record["f153_environment"]["CUDA_VISIBLE_DEVICES"] == ""


def test_observed_profile_binds_every_runtime_identity_but_grants_no_authority():
    record = observed_profile()
    assert native.validate_profile(record) == record
    assert record["lifecycle_state"] == native.OBSERVED_REVIEW_PENDING
    assert record["f152_lock"]["sha256"] == "1" * 64
    assert record["f152_lock"]["complete_transitive_lock"] is False
    assert record["f152_lock"]["artifact_closure_verified"] is False
    assert "/f152_lock/complete_transitive_lock" in record["resolution"][
        "unresolved_paths"
    ]
    assert record["resolution"]["unresolved_paths"] == list(
        native.REVIEW_PENDING_UNRESOLVED_PATHS
    )
    assert record["resolution"]["eligible_for_data_free_independent_review"] is True
    assert record["resolution"]["eligible_for_scientific_execution"] is False
    assert set(record["runtime_bindings"]) >= {
        "source_revision",
        "source_manifest_sha256",
        "installed_distribution_metadata_observation_sha256",
        "module_origin_observation_sha256",
        "python_abi_observation_sha256",
        "native_runtime_capture_sha256",
    }
    assert record["runtime_bindings"]["installed_payload_closure_verified"] is False
    assert record["runtime_bindings"]["module_distribution_ownership_verified"] is False
    assert record["runtime_bindings"][
        "torch_deterministic_runtime_observation_sha256"
    ] is None
    assert record["runtime_bindings"][
        "every_process_worker_equivalence_verified"
    ] is False
    assert record["runtime_bindings"][
        "f153_effective_runtime_satisfaction_verified"
    ] is False
    assert not any(record["safety_boundary"].values())


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("native_route", "custom_container_required", True),
        ("native_route", "container_registry_required", True),
        ("native_route", "aws_instance_profile_required", True),
        ("native_route", "network_resolution_or_install_permitted", True),
        ("target", "operating_system_family", "Darwin"),
        ("target", "architecture", "arm64"),
        ("target", "python_version", "3.11.5"),
        ("target", "databricks_runtime_version_prefix", "16.4"),
        ("target", "machine_learning_runtime", True),
        ("target", "gpu_enabled", True),
    ],
)
def test_route_or_platform_substitution_fails_closed(section, key, value):
    record = observed_profile()
    record[section][key] = value
    with pytest.raises(native.NativeRuntimeProfileError):
        native.validate_profile(redigest(record))


def test_draft_rejects_fabricated_f152_resolution():
    record = native.build_draft_profile()
    record["f152_lock"]["sha256"] = "a" * 64
    with pytest.raises(native.NativeRuntimeProfileError, match="unresolved"):
        native.validate_profile(redigest(record))


def test_observed_state_forbids_capture_from_claiming_transitive_completeness():
    record = observed_profile()
    record["f152_lock"]["complete_transitive_lock"] = True
    with pytest.raises(native.NativeRuntimeProfileError, match="cannot claim complete"):
        native.validate_profile(redigest(record))


def test_environment_mutation_fails_even_after_redigest():
    record = deepcopy(observed_profile())
    record["f153_environment"]["OMP_NUM_THREADS"] = "2"
    with pytest.raises(native.NativeRuntimeProfileError, match="f153_environment"):
        native.validate_profile(redigest(record))


def test_every_safety_authority_must_remain_false():
    for key in native.build_draft_profile()["safety_boundary"]:
        record = observed_profile()
        record["safety_boundary"][key] = True
        with pytest.raises(native.NativeRuntimeProfileError, match="safety_boundary"):
            native.validate_profile(redigest(record))


def test_unknown_key_and_stale_digest_fail_closed():
    record = observed_profile()
    record["unknown"] = False
    with pytest.raises(native.NativeRuntimeProfileError, match="unknown keys"):
        native.validate_profile(record)
    record = observed_profile()
    record["target"]["spark_version"] = "4.0.1"
    with pytest.raises(native.NativeRuntimeProfileError, match="semantic digest"):
        native.validate_profile(record)
