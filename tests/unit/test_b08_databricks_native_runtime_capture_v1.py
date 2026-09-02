from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import stat

import pytest

from heterodiff.experiments import b08_databricks_native_runtime_profile as native


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/diagnostics/b08_databricks_native_runtime_capture_v1.py"
SPEC = importlib.util.spec_from_file_location("b08_native_capture", SOURCE)
assert SPEC is not None and SPEC.loader is not None
capture_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture_module)


SOURCE_REVISION = "a" * 40
SOURCE_MANIFEST = "b" * 64


def exact_lock_bytes() -> bytes:
    rows = []
    for ordinal, (name, version) in enumerate(
        native.EXPECTED_DISTRIBUTIONS.items(), start=1
    ):
        rows.extend(
            (
                f"{name}=={version}",
                "    --hash=sha256:" + format(ordinal, "064x"),
            )
        )
    return ("\n".join(rows) + "\n").encode("ascii")


def project_root(tmp_path: Path, *, include_lock: bool = True) -> Path:
    root = tmp_path / "project"
    profile_path = root / native.PROFILE_PATH
    profile_path.parent.mkdir(parents=True)
    profile_path.write_bytes(
        native.canonical_json_bytes(native.build_draft_profile()) + b"\n"
    )
    if include_lock:
        lock_path = root / native.F152_LOCK_PATH
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_bytes(exact_lock_bytes())
    return root


def install_fake_runtime(monkeypatch):
    for name, value in native.F153_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    fake_abi = {
        "soabi": "cpython-312-x86_64-linux-gnu",
        "multiarch": "x86_64-linux-gnu",
        "extension_suffix": ".cpython-312-x86_64-linux-gnu.so",
        "cache_tag": "cpython-312",
        "pointer_bits": 64,
        "byteorder": "little",
        "libc_name": "glibc",
        "libc_version": "2.39",
        "platform_tag": "linux-x86_64",
    }
    fake_runtime = {
        "databricks_runtime_environment": "17.3",
        "system": "Linux",
        "machine": "x86_64",
        "python_implementation": "CPython",
        "python_version": "3.12.3",
        "python_executable": "/databricks/python3/bin/python3",
        "unobserved_target_paths": list(native.UNOBSERVED_TARGET_PATHS),
    }
    distribution_entries = [
        {
            "name": name,
            "version": version,
            "metadata_root": "/databricks/python/lib",
        }
        for name, version in sorted(native.EXPECTED_DISTRIBUTIONS.items())
    ]
    fake_distributions = {
        "entries": distribution_entries,
        "metadata_observation_sha256": capture_module._collection_sha256(
            distribution_entries
        ),
        "payload_closure_verified": False,
    }
    module_entries = [
        {
            "distribution": distribution,
            "module": module,
            "origin": f"/databricks/python/lib/{module}/__init__.py",
            "origin_sha256": format(ordinal, "064x"),
            "origin_size_bytes": ordinal,
            "distribution_metadata_root_observation": "/databricks/python/lib",
            "distribution_ownership_verified": False,
        }
        for ordinal, (distribution, module) in enumerate(
            sorted(native.EXPECTED_MODULES.items()), start=11
        )
    ]
    fake_origins = {
        "entries": module_entries,
        "origin_observation_sha256": capture_module._collection_sha256(
            module_entries
        ),
        "distribution_ownership_verified": False,
    }
    monkeypatch.setattr(
        capture_module, "_runtime_identity", lambda: (fake_runtime, fake_abi)
    )
    monkeypatch.setattr(
        capture_module,
        "_installed_distributions",
        lambda: (fake_distributions, {}),
    )
    monkeypatch.setattr(capture_module, "_module_origins", lambda roots: fake_origins)
    return fake_runtime, fake_abi, fake_distributions, fake_origins


def write_redigested_private_receipt(path: Path, receipt: dict) -> None:
    unsigned = dict(receipt)
    unsigned.pop("receipt_payload_sha256", None)
    receipt["receipt_payload_sha256"] = capture_module._sha256(
        capture_module.RECEIPT_DOMAIN + capture_module._canonical_bytes(unsigned)
    )
    path.write_bytes(capture_module._canonical_bytes(receipt) + b"\n")
    path.chmod(0o600)


def test_missing_f152_lock_is_explicit_terminal_blocker(tmp_path, monkeypatch):
    root = project_root(tmp_path, include_lock=False)
    install_fake_runtime(monkeypatch)
    monkeypatch.setattr(
        capture_module,
        "_runtime_identity",
        lambda: (_ for _ in ()).throw(AssertionError("runtime inspection reached")),
    )
    monkeypatch.setattr(
        capture_module,
        "_installed_distributions",
        lambda: (_ for _ in ()).throw(AssertionError("package inspection reached")),
    )
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="F152_LOCK_UNRESOLVED"
    ):
        capture_module.capture(
            str(root),
            SOURCE_REVISION,
            SOURCE_MANIFEST,
            str(tmp_path / "receipt.json"),
        )


def test_semantically_rehashed_profile_tamper_fails_before_capture(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    record = native.build_draft_profile()
    record["native_route"]["network_resolution_or_install_permitted"] = True
    record = native.with_semantic_digest(record)
    (root / native.PROFILE_PATH).write_bytes(
        native.canonical_json_bytes(record) + b"\n"
    )
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="NATIVE_PROFILE_INVALID"
    ):
        capture_module.capture(
            str(root),
            SOURCE_REVISION,
            SOURCE_MANIFEST,
            str(tmp_path / "receipt.json"),
        )


def test_capture_binds_source_lock_runtime_origins_abi_and_is_no_clobber(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    fake_runtime, fake_abi, fake_distributions, fake_origins = install_fake_runtime(
        monkeypatch
    )
    output = tmp_path / "receipt.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
    )
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert output.read_bytes() == capture_module._canonical_bytes(receipt) + b"\n"
    assert receipt["source_binding"] == {
        "revision": SOURCE_REVISION,
        "manifest_sha256": SOURCE_MANIFEST,
        "declaration_externally_authenticated": False,
    }
    assert receipt["f152_lock_observation"]["path"] == native.F152_LOCK_PATH
    assert receipt["f152_lock_observation"]["requirement_count"] == len(
        native.EXPECTED_DISTRIBUTIONS
    )
    assert receipt["f152_lock_observation"][
        "complete_transitive_lock_verified_by_capture"
    ] is False
    assert receipt["f152_lock_observation"][
        "artifact_closure_verified_by_capture"
    ] is False
    assert receipt["f152_lock_observation"][
        "all_declared_requirements_sha256_hashed"
    ] is True
    assert receipt["native_runtime"] == fake_runtime
    assert receipt["native_runtime"]["unobserved_target_paths"] == list(
        native.UNOBSERVED_TARGET_PATHS
    )
    assert receipt["python_abi"]["observation"] == fake_abi
    assert receipt["installed_distributions"] == fake_distributions
    assert receipt["module_origins"] == fake_origins
    assert receipt["f153_controls"] == capture_module._f153_controls(
        native.F153_ENVIRONMENT
    )
    assert receipt["f153_controls"][
        "f153_effective_runtime_satisfaction_claimed"
    ] is False
    assert receipt["f153_controls"]["torch_runtime_observation_performed"] is False
    assert receipt["f153_controls"][
        "every_process_worker_equivalence_verified"
    ] is False
    assert receipt["safety_boundary"]["study_or_test_data_accessed"] is False
    assert receipt["safety_boundary"]["scientific_execution_performed"] is False
    assert capture_module.validate_only(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
    ) == receipt
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="OUTPUT_NO_CLOBBER"
    ):
        capture_module.capture(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
        )


@pytest.mark.parametrize(
    ("revision", "manifest", "error"),
    [
        ("A" * 40, SOURCE_MANIFEST, "SOURCE_REVISION_INVALID"),
        ("a" * 39, SOURCE_MANIFEST, "SOURCE_REVISION_INVALID"),
        (SOURCE_REVISION, "b" * 63, "SOURCE_MANIFEST_SHA256_INVALID"),
        (SOURCE_REVISION, "G" * 64, "SOURCE_MANIFEST_SHA256_INVALID"),
    ],
)
def test_source_revision_and_manifest_inputs_fail_closed(
    tmp_path, monkeypatch, revision, manifest, error
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    with pytest.raises(capture_module.NativeRuntimeCaptureError, match=error):
        capture_module.capture(
            str(root), revision, manifest, str(tmp_path / "receipt.json")
        )


def test_validate_only_rejects_different_declared_source_binding(tmp_path, monkeypatch):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    output = tmp_path / "receipt.json"
    capture_module.capture(str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output))
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="RECEIPT_SOURCE_BINDING_MISMATCH",
    ):
        capture_module.validate_only(
            str(root), "c" * 40, SOURCE_MANIFEST, str(output)
        )


def test_rehashed_safety_overclaim_is_rejected(tmp_path, monkeypatch):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    output = tmp_path / "receipt.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
    )
    receipt["safety_boundary"]["scientific_execution_performed"] = True
    tampered = tmp_path / "tampered.json"
    write_redigested_private_receipt(tampered, receipt)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="RECEIPT_SAFETY_BOUNDARY_MISMATCH",
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(tampered)
        )


@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("complete_transitive_lock_verified_by_capture", "COMPLETENESS_OVERCLAIM"),
        ("artifact_closure_verified_by_capture", "ARTIFACT_CLOSURE_OVERCLAIM"),
    ],
)
def test_self_redigested_f152_closure_overclaims_are_rejected(
    tmp_path, monkeypatch, field, error
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["f152_lock_observation"][field] = True
    forged_path = tmp_path / (field + ".json")
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(capture_module.NativeRuntimeCaptureError, match=error):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_self_redigested_requirement_list_must_equal_bound_lock(tmp_path, monkeypatch):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["f152_lock_observation"]["requirements"][0]["sha256_hash_count"] = 99
    forged_path = tmp_path / "forged-requirements.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="RECEIPT_F152_LOCK_BINDING_MISMATCH",
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_self_redigested_abi_with_recomputed_inner_digest_is_rejected(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["python_abi"]["observation"]["pointer_bits"] = 32
    forged["python_abi"]["observation_sha256"] = capture_module._collection_sha256(
        forged["python_abi"]["observation"]
    )
    forged_path = tmp_path / "forged-abi.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="RECEIPT_ABI_POINTER_BITS_INVALID"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_self_redigested_distribution_metadata_and_payload_claim_are_rejected(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["installed_distributions"]["payload_closure_verified"] = True
    forged_path = tmp_path / "forged-payload.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="PAYLOAD_CLOSURE_OVERCLAIM"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )

    forged = deepcopy(receipt)
    forged["installed_distributions"]["entries"][0]["version"] = "9.9.9"
    forged["installed_distributions"][
        "metadata_observation_sha256"
    ] = capture_module._collection_sha256(
        forged["installed_distributions"]["entries"]
    )
    forged_path = tmp_path / "forged-distributions.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="INSTALLED_VERSION_MISMATCH"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_self_redigested_module_origin_and_ownership_claim_are_rejected(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["module_origins"]["distribution_ownership_verified"] = True
    forged_path = tmp_path / "forged-ownership.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="MODULE_OWNERSHIP_OVERCLAIM"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )

    forged = deepcopy(receipt)
    forged["module_origins"]["entries"][0]["origin"] = "/tmp/forged.py"
    forged["module_origins"]["origin_observation_sha256"] = (
        capture_module._collection_sha256(forged["module_origins"]["entries"])
    )
    forged_path = tmp_path / "forged-origin.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="RECEIPT_MODULES_CURRENT_STATE_MISMATCH",
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_self_redigested_runtime_and_f153_effectiveness_claim_are_rejected(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    valid_path = tmp_path / "valid.json"
    receipt = capture_module.capture(
        str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(valid_path)
    )
    forged = deepcopy(receipt)
    forged["native_runtime"]["unobserved_target_paths"] = []
    forged_path = tmp_path / "forged-runtime.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="UNOBSERVED_TARGET_ROSTER_INVALID",
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )

    forged = deepcopy(receipt)
    forged["f153_controls"]["f153_effective_runtime_satisfaction_claimed"] = True
    forged_path = tmp_path / "forged-f153.json"
    write_redigested_private_receipt(forged_path, forged)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="F153_CONTROLS_INVALID"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(forged_path)
        )


def test_validate_only_rejects_repeated_invalid_source_literals_before_receipt(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    output = tmp_path / "receipt.json"
    capture_module.capture(str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output))
    for revision, manifest, error in (
        ("z" * 40, SOURCE_MANIFEST, "SOURCE_REVISION_INVALID"),
        (SOURCE_REVISION, "z" * 64, "SOURCE_MANIFEST_SHA256_INVALID"),
    ):
        with pytest.raises(capture_module.NativeRuntimeCaptureError, match=error):
            capture_module.validate_only(str(root), revision, manifest, str(output))


def test_validate_only_rejects_symlink_hardlink_and_nonprivate_receipts(
    tmp_path, monkeypatch
):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    output = tmp_path / "receipt.json"
    capture_module.capture(str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output))

    symlink = tmp_path / "receipt-symlink.json"
    symlink.symlink_to(output)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="RECEIPT_SYMLINK_FORBIDDEN"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(symlink)
        )

    hardlink = tmp_path / "receipt-hardlink.json"
    os.link(output, hardlink)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="RECEIPT_HARDLINK_FORBIDDEN"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(hardlink)
        )
    hardlink.unlink()

    output.chmod(0o666)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="RECEIPT_MODE_NOT_PRIVATE_0600"
    ):
        capture_module.validate_only(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
        )


def test_capture_does_not_clobber_preexisting_output_symlink(tmp_path, monkeypatch):
    root = project_root(tmp_path)
    install_fake_runtime(monkeypatch)
    target = tmp_path / "target.json"
    target.write_text("unchanged", encoding="ascii")
    output = tmp_path / "receipt-link.json"
    output.symlink_to(target)
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="OUTPUT_NO_CLOBBER"
    ):
        capture_module.capture(
            str(root), SOURCE_REVISION, SOURCE_MANIFEST, str(output)
        )
    assert target.read_text(encoding="ascii") == "unchanged"


@pytest.mark.parametrize(
    ("raw", "error"),
    [
        (b"numpy==2.4.6\n", "REQUIREMENT_WITHOUT_HASH"),
        (b"--index-url https://example.invalid\n", "FORBIDDEN_SYNTAX"),
        (
            b"numpy>=2.4.6\n    --hash=sha256:" + b"1" * 64 + b"\n",
            "FORBIDDEN_SYNTAX",
        ),
    ],
)
def test_lock_parser_rejects_unhashed_or_resolver_syntax(raw, error):
    with pytest.raises(capture_module.NativeRuntimeCaptureError, match=error):
        capture_module._parse_lock(raw)


def test_any_f153_environment_mismatch_fails_closed(monkeypatch):
    for name, value in native.F153_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("OMP_NUM_THREADS", "2")
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError,
        match="F153_ENVIRONMENT_MISMATCH:OMP_NUM_THREADS",
    ):
        capture_module._f153_environment()


def test_resolved_parent_symlink_alias_into_forbidden_mount_is_rejected(
    tmp_path, monkeypatch
):
    forbidden = tmp_path / "forbidden"
    forbidden.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(forbidden, target_is_directory=True)
    monkeypatch.setattr(
        capture_module,
        "FORBIDDEN_OUTPUT_ROOTS",
        ((forbidden.resolve(), "TEST_FORBIDDEN_OUTPUT"),),
    )
    with pytest.raises(
        capture_module.NativeRuntimeCaptureError, match="TEST_FORBIDDEN_OUTPUT"
    ):
        capture_module._output_path(str(alias / "receipt.json"))


def test_source_has_no_network_subprocess_entropy_spark_or_science_imports():
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
            "databricks",
            "pyspark",
            "socket",
            "subprocess",
            "requests",
            "urllib",
            "http",
            "random",
            "secrets",
            "numpy",
            "scipy",
            "torch",
        }
    )
    source_text = SOURCE.read_text(encoding="utf-8")
    assert "dbutils" not in source_text
    assert "spark." not in source_text
    assert "os.system" not in source_text
    assert "os.popen" not in source_text
