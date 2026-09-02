from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_runtime_profile as profile


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "databricks/container/Dockerfile.dbr17.3-cpu"
VERIFIER = ROOT / "databricks/container/verify-runtime.py"
INPUT = ROOT / "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.in"
TEMPLATE = (
    ROOT / "requirements/"
    "b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
    "lock-wheel-manifest.template.json"
)
RESOLVED_LOCK = ROOT / "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
RESOLVED_MANIFEST = (
    ROOT / "requirements/"
    "b08-databricks-aws-dbr17.3-x86_64-cpu-py312.wheel-manifest.json"
)

SPEC = importlib.util.spec_from_file_location("b08_container_verifier", VERIFIER)
assert SPEC is not None and SPEC.loader is not None
VERIFIER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER_MODULE)


def test_construction_package_paths_exist_without_resolved_artifacts():
    assert DOCKERFILE.is_file()
    assert VERIFIER.is_file()
    assert INPUT.is_file()
    assert TEMPLATE.is_file()
    assert not RESOLVED_LOCK.exists()
    assert not RESOLVED_MANIFEST.exists()


def test_dependency_input_is_exact_but_explicitly_not_a_lock():
    text = INPUT.read_text(encoding="ascii")
    assert text.startswith(
        "# UNRESOLVED INPUT ONLY -- THIS FILE IS NOT A PRODUCTION LOCK."
    )
    rows = [
        row
        for row in text.splitlines()
        if row and not row.startswith("#") and not row.startswith("--")
    ]
    assert rows == [
        "numpy==2.4.6",
        "scipy==1.17.1",
        "threadpoolctl==3.6.0",
        "torch==2.12.1+cpu",
    ]
    assert "--extra-index-url https://download.pytorch.org/whl/cpu" in text
    assert "--hash=" not in text


def test_machine_template_is_canonical_unresolved_and_zero_claim():
    raw = TEMPLATE.read_bytes()
    value = json.loads(raw.decode("ascii"))
    assert raw == (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
    )
    assert value["record_state"] == ("UNRESOLVED_TEMPLATE_DO_NOT_BUILD_DO_NOT_INSTALL")
    assert value["base_image"] == {
        "digest_required": True,
        "resolved_manifest_digest": None,
        "resolved_reference": None,
    }
    assert value["lock"]["all_artifacts_hash_pinned"] is False
    assert value["lock"]["all_requirements_exactly_pinned"] is False
    assert value["lock"]["resolved_lock_sha256"] is None
    assert value["wheelhouse"]["artifact_count"] is None
    assert value["wheelhouse"]["artifacts"] == []
    assert value["wheelhouse"]["complete"] is False
    assert value["project_wheel"]["sha256"] is None
    assert value["container"]["build_verified"] is False
    assert value["container"]["final_image_manifest_digest"] is None
    assert value["qualification"] == {
        "image_build_executed": False,
        "offline_install_verified": False,
        "resolver_executed": False,
        "runtime_verifier_executed": False,
        "study_or_test_data_accessed": False,
    }


def _docker_instructions(text: str):
    logical = []
    current = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        current = current + (" " if current else "") + stripped.rstrip("\\").strip()
        if not stripped.endswith("\\"):
            logical.append(current)
            current = ""
    assert not current
    return logical


def test_dockerfile_is_digest_bound_offline_and_has_no_ignored_launch_hook():
    text = DOCKERFILE.read_text(encoding="ascii")
    instructions = _docker_instructions(text)
    assert "ARG BASE_IMAGE" in instructions
    assert "FROM ${BASE_IMAGE} AS heterodiff-runtime" in instructions
    assert "@sha256:[0-9a-f]{64}" in text
    assert "/databricks/python3/bin/python -m pip install" in text
    for option in (
        "--network=none",
        "--no-deps",
        "--no-index",
        "--find-links=/opt/heterodiff/wheelhouse",
        "--only-binary=:all:",
        "--require-hashes",
    ):
        assert option in text
    assert "requirements.lock" in text
    assert "wheel-manifest.json" in text
    assert "runtime-profile.json" in text
    assert "--supply-chain-only" in text
    assert "lock-wheel-manifest.template.json" not in text
    assert "cpu-py312.in" not in text
    assert "COPY . " not in text
    first_tokens = {row.split(None, 1)[0].upper() for row in instructions}
    assert "CMD" not in first_tokens
    assert "ENTRYPOINT" not in first_tokens


def test_dockerfile_contains_all_exact_deterministic_controls():
    text = DOCKERFILE.read_text(encoding="ascii")
    for name, value in VERIFIER_MODULE.EXPECTED_ENVIRONMENT.items():
        rendered = f'{name}=""' if value == "" else f"{name}={value}"
        assert rendered in text


def test_verifier_contract_is_linux_x86_64_cp312_cpu_only():
    assert VERIFIER_MODULE.TARGET_PROFILE == (
        "b08-databricks-aws-dbr17.3-linux-x86_64-cpu-py312"
    )
    assert VERIFIER_MODULE.EXPECTED_PYTHON == "3.12.3"
    assert VERIFIER_MODULE.EXPECTED_DISTRIBUTIONS == {
        "heterodiff": "0.1.0",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "threadpoolctl": "3.6.0",
        "torch": "2.12.1+cpu",
    }
    assert VERIFIER_MODULE.EXPECTED_ENVIRONMENT["CUDA_VISIBLE_DEVICES"] == ""


def test_verifier_rejects_template_as_a_resolved_wheel_manifest():
    with pytest.raises(
        VERIFIER_MODULE.RuntimeVerificationError,
        match="WHEEL_MANIFEST_KEY_ROSTER|WHEEL_MANIFEST_NOT_RESOLVED",
    ):
        VERIFIER_MODULE._load_resolved_manifest(TEMPLATE)


def test_verifier_rejects_nonempty_cuda_value():
    environment = dict(VERIFIER_MODULE.EXPECTED_ENVIRONMENT)
    VERIFIER_MODULE.verify_environment(environment)
    environment["CUDA_VISIBLE_DEVICES"] = " "
    with pytest.raises(
        VERIFIER_MODULE.RuntimeVerificationError,
        match="DETERMINISTIC_ENVIRONMENT_MISMATCH",
    ):
        VERIFIER_MODULE.verify_environment(environment)


def test_lock_parser_rejects_urls_paths_options_and_unhashed_rows():
    digest = "1" * 64
    valid = ("heterodiff==0.1.0 \\\n" f"    --hash=sha256:{digest}\n").encode("ascii")
    assert VERIFIER_MODULE._validate_lock_bytes(valid) == ("heterodiff==0.1.0",)
    invalid_rows = (
        f"heterodiff @ https://example.invalid/pkg.whl \\\n    --hash=sha256:{digest}\n",
        f"file:///tmp/pkg.whl \\\n    --hash=sha256:{digest}\n",
        f"--extra-index-url https://example.invalid/simple\nheterodiff==0.1.0 \\\n    --hash=sha256:{digest}\n",
        "heterodiff==0.1.0\n",
    )
    for raw in invalid_rows:
        with pytest.raises(VERIFIER_MODULE.RuntimeVerificationError):
            VERIFIER_MODULE._validate_lock_bytes(raw.encode("ascii"))


def _write_build_input_closure(tmp_path: Path):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    wheel_rows = (
        ("heterodiff==0.1.0", "heterodiff-0.1.0-py3-none-any.whl", "PROJECT_WHEEL"),
        (
            "numpy==2.4.6",
            "numpy-2.4.6-cp312-cp312-manylinux_2_28_x86_64.whl",
            "RUNTIME_DEPENDENCY",
        ),
        (
            "scipy==1.17.1",
            "scipy-1.17.1-cp312-cp312-manylinux_2_28_x86_64.whl",
            "RUNTIME_DEPENDENCY",
        ),
        (
            "threadpoolctl==3.6.0",
            "threadpoolctl-3.6.0-py3-none-any.whl",
            "RUNTIME_DEPENDENCY",
        ),
        (
            "torch==2.12.1+cpu",
            "torch-2.12.1+cpu-cp312-cp312-manylinux_2_28_x86_64.whl",
            "RUNTIME_DEPENDENCY",
        ),
    )
    artifacts = []
    lock_lines = []
    digests = {}
    for requirement, filename, role in wheel_rows:
        raw = ("fixture:" + filename).encode("ascii")
        (wheelhouse / filename).write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        digests[requirement] = digest
        artifacts.append(
            {
                "filename": filename,
                "requirement": requirement,
                "role": role,
                "sha256": digest,
                "size_bytes": len(raw),
            }
        )
        lock_lines.extend((requirement + " \\", "    --hash=sha256:" + digest))
    lock_path = tmp_path / "requirements.lock"
    lock_raw = ("\n".join(lock_lines) + "\n").encode("ascii")
    lock_path.write_bytes(lock_raw)
    manifest = {
        "artifacts": artifacts,
        "lock": {
            "all_artifacts_hash_pinned": True,
            "all_requirements_exactly_pinned": True,
            "path": "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock",
            "pip_require_hashes_required": True,
            "sha256": hashlib.sha256(lock_raw).hexdigest(),
        },
        "record_state": "RESOLVED_OFFLINE_WHEELHOUSE",
        "schema_version": "heterodiff-b08-databricks-container-wheel-manifest-v1",
        "target": VERIFIER_MODULE.TARGET_PROFILE,
    }
    manifest_raw = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("ascii")
        + b"\n"
    )
    manifest_path = tmp_path / "wheel-manifest.json"
    manifest_path.write_bytes(manifest_raw)

    runtime_profile = profile.build_draft_profile()
    runtime_profile["lifecycle_state"] = profile.BUILD_INPUTS_RESOLVED
    runtime_profile["container"]["base_image_manifest_digest"] = "sha256:" + "1" * 64
    runtime_profile["dependencies"].update(
        {
            "lockfile_sha256": hashlib.sha256(lock_raw).hexdigest(),
            "source_wheel_sha256": digests["heterodiff==0.1.0"],
            "wheel_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "complete_transitive_lock": True,
            "wheel_manifest_complete": True,
            "all_artifacts_linux_x86_64_cp312_compatible": True,
        }
    )
    torch_artifact = next(
        row for row in artifacts if row["requirement"] == "torch==2.12.1+cpu"
    )
    runtime_profile["torch"].update(
        {
            "version": "2.12.1+cpu",
            "wheel_filename": torch_artifact["filename"],
            "wheel_sha256": torch_artifact["sha256"],
        }
    )
    runtime_profile["resolution"]["unresolved_paths"] = list(
        profile.BUILD_STAGE_UNRESOLVED_PATHS
    )
    runtime_profile = profile.with_semantic_digest(runtime_profile)
    runtime_profile_path = tmp_path / "runtime-profile.json"
    runtime_profile_path.write_bytes(
        profile.canonical_json_bytes(runtime_profile) + b"\n"
    )
    return {
        "base_image_reference": (
            "databricksruntime/standard:17.3-LTS@sha256:" + "1" * 64
        ),
        "lock_path": lock_path,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "runtime_profile_path": runtime_profile_path,
        "wheelhouse": wheelhouse,
    }


def test_supply_chain_binds_exact_project_wheel_to_build_runtime_profile(tmp_path):
    closure = _write_build_input_closure(tmp_path)
    result = VERIFIER_MODULE.verify_offline_wheel_closure(
        manifest_path=closure["manifest_path"],
        lock_path=closure["lock_path"],
        wheelhouse_path=closure["wheelhouse"],
        runtime_profile_path=closure["runtime_profile_path"],
        base_image_reference=closure["base_image_reference"],
    )
    assert result["artifact_count"] == 5
    assert (
        result["project_wheel_sha256"] == closure["manifest"]["artifacts"][0]["sha256"]
    )


def test_supply_chain_rejects_mislabeled_project_wheel(tmp_path):
    closure = _write_build_input_closure(tmp_path)
    manifest = closure["manifest"]
    manifest["artifacts"][0]["role"] = "RUNTIME_DEPENDENCY"
    manifest["artifacts"][1]["role"] = "PROJECT_WHEEL"
    raw = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("ascii")
        + b"\n"
    )
    closure["manifest_path"].write_bytes(raw)
    with pytest.raises(
        VERIFIER_MODULE.RuntimeVerificationError,
        match="PROJECT_WHEEL_FILENAME_MISMATCH",
    ):
        VERIFIER_MODULE.verify_offline_wheel_closure(
            manifest_path=closure["manifest_path"],
            lock_path=closure["lock_path"],
            wheelhouse_path=closure["wheelhouse"],
            runtime_profile_path=closure["runtime_profile_path"],
            base_image_reference=closure["base_image_reference"],
        )


def test_verifier_has_no_network_subprocess_entropy_or_spark_surface():
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
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
            "databricks",
            "http",
            "pyspark",
            "random",
            "requests",
            "secrets",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    source = VERIFIER.read_text(encoding="utf-8")
    for forbidden in (
        "dbutils",
        "SparkSession",
        "spark.table",
        "torch.load",
        "numpy.load",
        "scipy.io",
    ):
        assert forbidden not in source
