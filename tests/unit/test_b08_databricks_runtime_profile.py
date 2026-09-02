from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_runtime_profile as profile


ROOT = Path(__file__).resolve().parents[2]
MACHINE = ROOT / profile.PROFILE_PATH
SOURCE = ROOT / "src/heterodiff/experiments/b08_databricks_runtime_profile.py"
HISTORICAL_LOCK = ROOT / profile.HISTORICAL_LOCK_PATH


def build_inputs_profile():
    record = profile.build_draft_profile()
    record["lifecycle_state"] = profile.BUILD_INPUTS_RESOLVED
    record["container"]["base_image_manifest_digest"] = "sha256:" + "1" * 64
    record["dependencies"].update(
        {
            "lockfile_sha256": "4" * 64,
            "source_wheel_sha256": "5" * 64,
            "wheel_manifest_sha256": "6" * 64,
            "complete_transitive_lock": True,
            "wheel_manifest_complete": True,
            "all_artifacts_linux_x86_64_cp312_compatible": True,
        }
    )
    record["torch"].update(
        {
            "version": "2.12.1+cpu",
            "wheel_filename": (
                "torch-2.12.1+cpu-cp312-cp312-" "manylinux_2_28_x86_64.whl"
            ),
            "wheel_sha256": "8" * 64,
        }
    )
    record["resolution"]["unresolved_paths"] = list(
        profile.BUILD_STAGE_UNRESOLVED_PATHS
    )
    return profile.with_semantic_digest(record)


def eligible_profile():
    record = profile.build_draft_profile()
    record["lifecycle_state"] = profile.ELIGIBLE_RESOLVED
    record["container"].update(
        {
            "base_image_manifest_digest": "sha256:" + "1" * 64,
            "final_image_manifest_digest": "sha256:" + "2" * 64,
            "final_image_reference_sha256": "3" * 64,
        }
    )
    record["dependencies"].update(
        {
            "lockfile_sha256": "4" * 64,
            "source_wheel_sha256": "5" * 64,
            "wheel_manifest_sha256": "6" * 64,
            "installed_distribution_manifest_sha256": "7" * 64,
            "complete_transitive_lock": True,
            "wheel_manifest_complete": True,
            "all_artifacts_linux_x86_64_cp312_compatible": True,
        }
    )
    record["torch"].update(
        {
            "version": "2.12.1+cpu",
            "wheel_filename": (
                "torch-2.12.1+cpu-cp312-cp312-" "manylinux_2_28_x86_64.whl"
            ),
            "wheel_sha256": "8" * 64,
            "cpu_runtime_probe_sha256": "9" * 64,
        }
    )
    record["resolution"].update(
        {
            "unresolved_paths": [],
            "runtime_observation_sha256": "a" * 64,
            "eligible_for_data_free_b08_qualification": True,
        }
    )
    return profile.with_semantic_digest(record)


def redigest(record):
    return profile.with_semantic_digest(record)


def test_machine_declaration_is_exact_canonical_draft():
    record = json.loads(MACHINE.read_text(encoding="ascii"))
    assert record == profile.build_draft_profile()
    assert profile.validate_profile(record) == record
    assert MACHINE.read_bytes() == profile.canonical_json_bytes(record) + b"\n"
    assert record["lifecycle_state"] == profile.DRAFT_UNRESOLVED
    assert record["resolution"]["eligible_for_data_free_b08_qualification"] is False
    assert record["resolution"]["eligible_for_scientific_execution"] is False
    assert record["resolution"]["unresolved_paths"] == list(profile.UNRESOLVED_PATHS)


def test_exact_linux_dbr17_python312_x86_64_cpu_target_and_environment():
    record = profile.build_draft_profile()
    target = record["target"]
    assert profile.PROFILE_ID == ("b08-databricks-aws-dbr17.3-linux-x86_64-cpu-py312")
    assert record["dependencies"]["source_wheel_path"] == (
        "requirements/wheelhouse/"
        "b08-databricks-aws-dbr17.3-x86_64-cpu-py312/"
        "heterodiff-0.1.0-py3-none-any.whl"
    )
    assert record["dependencies"]["expected_distributions"] == {
        "heterodiff": "0.1.0",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "threadpoolctl": "3.6.0",
        "torch": "2.12.1+cpu",
    }
    assert target["cloud_provider"] == "AWS"
    assert target["compute_mode"] == "CLASSIC_DEDICATED"
    assert target["databricks_runtime_release"] == "17.3 LTS"
    assert target["databricks_runtime_version"] == "17.3.x-scala2.13"
    assert target["operating_system_family"] == "Linux"
    assert target["architecture"] == "x86_64"
    assert target["oci_architecture"] == "amd64"
    assert target["python_version"] == "3.12.3"
    assert target["python_abi"] == "cp312"
    assert target["cpu_only"] is True
    assert target["gpu_enabled"] is False
    assert record["deterministic_environment"] == {
        "BLIS_NUM_THREADS": "1",
        "CUDA_VISIBLE_DEVICES": "",
        "LANG": "C",
        "LC_ALL": "C",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
        "PYTHONUTF8": "1",
        "TZ": "UTC",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    assert len(record["deterministic_environment"]) == 15


def test_fully_bound_successor_is_eligible_only_for_data_free_qualification():
    record = eligible_profile()
    assert profile.validate_profile(record) == record
    assert record["lifecycle_state"] == profile.ELIGIBLE_RESOLVED
    assert record["resolution"]["unresolved_paths"] == []
    assert record["resolution"]["eligible_for_data_free_b08_qualification"] is True
    assert record["resolution"]["eligible_for_scientific_execution"] is False
    assert record["qualification_boundary"]["scientific_execution_authorized"] is False
    assert record["qualification_boundary"]["study_data_access_authorized"] is False
    assert record["qualification_boundary"]["b08_closure_authorized"] is False


def test_build_inputs_state_cross_binds_exact_prebuild_artifacts_only():
    record = build_inputs_profile()
    assert profile.validate_profile(record) == record
    assert record["lifecycle_state"] == profile.BUILD_INPUTS_RESOLVED
    assert record["container"]["base_image_manifest_digest"] == ("sha256:" + "1" * 64)
    assert record["dependencies"]["lockfile_sha256"] == "4" * 64
    assert record["dependencies"]["source_wheel_sha256"] == "5" * 64
    assert record["dependencies"]["wheel_manifest_sha256"] == "6" * 64
    assert record["torch"]["version"] == "2.12.1+cpu"
    assert record["torch"]["wheel_sha256"] == "8" * 64
    assert record["resolution"]["eligible_for_data_free_b08_qualification"] is False
    assert record["resolution"]["eligible_for_scientific_execution"] is False


def test_build_stage_unresolved_path_roster_is_exact_and_exported():
    assert profile.BUILD_STAGE_UNRESOLVED_PATHS == (
        "/container/final_image_manifest_digest",
        "/container/final_image_reference_sha256",
        "/dependencies/installed_distribution_manifest_sha256",
        "/resolution/runtime_observation_sha256",
        "/torch/cpu_runtime_probe_sha256",
    )
    record = build_inputs_profile()
    assert record["resolution"]["unresolved_paths"] == list(
        profile.BUILD_STAGE_UNRESOLVED_PATHS
    )
    assert record["container"]["final_image_manifest_digest"] is None
    assert record["container"]["final_image_reference_sha256"] is None
    assert record["dependencies"]["installed_distribution_manifest_sha256"] is None
    assert record["torch"]["cpu_runtime_probe_sha256"] is None
    assert record["resolution"]["runtime_observation_sha256"] is None


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("container", "base_image_manifest_digest", None),
        ("container", "base_image_manifest_digest", "1" * 64),
        ("dependencies", "lockfile_sha256", None),
        ("dependencies", "source_wheel_sha256", None),
        ("dependencies", "wheel_manifest_sha256", None),
        ("dependencies", "complete_transitive_lock", False),
        ("dependencies", "wheel_manifest_complete", False),
        ("dependencies", "all_artifacts_linux_x86_64_cp312_compatible", False),
        ("torch", "version", None),
        ("torch", "version", "2.11.0+cpu"),
        ("torch", "wheel_filename", None),
        ("torch", "wheel_sha256", None),
    ],
)
def test_build_inputs_state_requires_every_exact_build_binding(section, key, value):
    record = build_inputs_profile()
    record[section][key] = value
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("container", "final_image_manifest_digest", "sha256:" + "2" * 64),
        ("container", "final_image_reference_sha256", "3" * 64),
        ("dependencies", "installed_distribution_manifest_sha256", "7" * 64),
        ("torch", "cpu_runtime_probe_sha256", "9" * 64),
        ("resolution", "runtime_observation_sha256", "a" * 64),
        ("resolution", "eligible_for_data_free_b08_qualification", True),
    ],
)
def test_build_inputs_state_rejects_postbuild_or_runtime_claims(section, key, value):
    record = build_inputs_profile()
    record[section][key] = value
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


def test_build_inputs_state_rejects_inexact_unresolved_roster():
    record = build_inputs_profile()
    record["resolution"]["unresolved_paths"] = list(
        profile.BUILD_STAGE_UNRESOLVED_PATHS[:-1]
    )
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("target", "operating_system_family", "Darwin"),
        ("target", "operating_system_distribution", "macOS"),
        ("target", "architecture", "arm64"),
        ("target", "oci_architecture", "arm64"),
        ("target", "python_version", "3.11.5"),
        ("target", "python_abi", "cp311"),
        ("target", "databricks_runtime_release", "16.4 LTS"),
        ("target", "databricks_runtime_version", "16.4.x-scala2.12"),
        ("target", "machine_learning_runtime", True),
        ("target", "cpu_only", False),
        ("target", "gpu_enabled", True),
        ("container", "image_platform", "linux/arm64"),
    ],
)
def test_platform_runtime_or_mac_substitution_fails_closed(section, key, value):
    record = eligible_profile()
    record[section][key] = value
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("base_image_manifest_digest", None),
        ("base_image_manifest_digest", "1" * 64),
        ("base_image_manifest_digest", "sha256:" + "1" * 63),
        ("final_image_manifest_digest", None),
        ("final_image_manifest_digest", "2" * 64),
        ("final_image_manifest_digest", "sha256:" + "G" * 64),
        ("final_image_reference_sha256", None),
        ("final_image_reference_sha256", "3" * 63),
    ],
)
def test_eligible_profile_requires_full_base_and_final_image_digests(key, value):
    record = eligible_profile()
    record["container"][key] = value
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    "key",
    [
        "lockfile_sha256",
        "source_wheel_sha256",
        "wheel_manifest_sha256",
        "installed_distribution_manifest_sha256",
    ],
)
def test_eligible_profile_requires_every_dependency_digest(key):
    record = eligible_profile()
    record["dependencies"][key] = None
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    "key",
    [
        "complete_transitive_lock",
        "wheel_manifest_complete",
        "all_artifacts_linux_x86_64_cp312_compatible",
    ],
)
def test_eligible_profile_requires_complete_compatible_wheel_closure(key):
    record = eligible_profile()
    record["dependencies"][key] = False
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


def test_exact_dependency_versions_cannot_drift():
    record = eligible_profile()
    record["dependencies"]["expected_distributions"]["numpy"] = "2.4.7"
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("version", "2.12.1"),
        ("version", "2.11.0+cpu"),
        ("version", "2.12.1+cu128"),
        ("wheel_filename", "torch-2.12.1+cu128-cp312-linux_x86_64.whl"),
        ("wheel_filename", "torch-2.12.1+cpu-cp311-linux_x86_64.whl"),
        ("wheel_filename", "torch-2.12.1+cpu-cp312-linux_aarch64.whl"),
        ("wheel_sha256", None),
        ("cpu_runtime_probe_sha256", None),
        ("cuda_compiled", True),
        ("cuda_available", True),
        ("mps_compiled", True),
        ("mps_available", True),
        ("distribution_variant", "CUDA"),
        ("deterministic_algorithms", False),
        ("warn_only", True),
        ("intraop_threads", 2),
        ("interop_threads", 2),
        ("cudnn_benchmark", True),
    ],
)
def test_non_cpu_or_nondeterministic_torch_profile_fails_closed(key, value):
    record = eligible_profile()
    record["torch"][key] = value
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(record))


def test_deterministic_environment_is_exact_including_empty_cuda_value():
    record = eligible_profile()
    assert record["deterministic_environment"]["CUDA_VISIBLE_DEVICES"] == ""
    for mutation in (
        lambda env: env.__setitem__("CUDA_VISIBLE_DEVICES", "-1"),
        lambda env: env.__setitem__("OMP_NUM_THREADS", "2"),
        lambda env: env.pop("LANG"),
        lambda env: env.__setitem__("EXTRA", "1"),
    ):
        hostile = deepcopy(record)
        mutation(hostile["deterministic_environment"])
        with pytest.raises(profile.RuntimeProfileError):
            profile.validate_profile(redigest(hostile))


def test_declared_draft_cannot_partially_bind_or_overclaim_eligibility():
    draft = profile.build_draft_profile()
    draft["container"]["base_image_manifest_digest"] = "sha256:" + "1" * 64
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(draft))

    draft = profile.build_draft_profile()
    draft["resolution"]["eligible_for_data_free_b08_qualification"] = True
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(draft))

    draft = profile.build_draft_profile()
    draft["resolution"]["unresolved_paths"] = []
    with pytest.raises(profile.RuntimeProfileError):
        profile.validate_profile(redigest(draft))


def test_historical_mac_identity_cannot_substitute_even_with_a_fresh_digest():
    record = eligible_profile()
    record["profile_id"] = profile.HISTORICAL_PROFILE_ID
    with pytest.raises(
        profile.RuntimeProfileError,
        match="historical macOS profile cannot substitute",
    ):
        profile.validate_profile(redigest(record))


def test_compatibility_seam_is_additive_lineage_only_and_preserves_old_lock():
    old_bytes = HISTORICAL_LOCK.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == profile.HISTORICAL_LOCK_SHA256
    relation = profile.compatibility_seam(
        profile.HISTORICAL_PROFILE_ID,
        profile.HISTORICAL_LOCK_PATH,
        profile.HISTORICAL_LOCK_SHA256,
    )
    assert relation == profile.build_draft_profile()["compatibility"]
    assert relation["successor_profile_id"] == profile.PROFILE_ID
    assert relation["historical_receipts_modified"] is False
    assert relation["historical_profile_eligible_as_successor"] is False
    assert relation["mapping_creates_eligibility"] is False
    assert HISTORICAL_LOCK.read_bytes() == old_bytes


@pytest.mark.parametrize(
    "arguments",
    [
        ("macos-alias", profile.HISTORICAL_LOCK_PATH, profile.HISTORICAL_LOCK_SHA256),
        (
            profile.HISTORICAL_PROFILE_ID,
            "requirements/other.lock",
            profile.HISTORICAL_LOCK_SHA256,
        ),
        (profile.HISTORICAL_PROFILE_ID, profile.HISTORICAL_LOCK_PATH, "0" * 64),
    ],
)
def test_compatibility_seam_rejects_inexact_historical_identity(arguments):
    with pytest.raises(profile.RuntimeProfileError):
        profile.compatibility_seam(*arguments)


def test_semantic_digest_and_closed_schema_reject_tampering():
    record = eligible_profile()
    record["target"]["python_version"] = "3.12.4"
    with pytest.raises(profile.RuntimeProfileError, match="semantic digest"):
        profile.validate_profile(record)

    record = eligible_profile()
    record["extra"] = False
    with pytest.raises(profile.RuntimeProfileError, match="missing or unknown keys"):
        profile.validate_profile(record)


def test_pure_contract_source_has_no_effect_surface():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(
        {
            "os",
            "pathlib",
            "socket",
            "subprocess",
            "requests",
            "urllib",
            "http",
            "random",
            "secrets",
        }
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({"open", "exec", "eval", "compile", "__import__"})
