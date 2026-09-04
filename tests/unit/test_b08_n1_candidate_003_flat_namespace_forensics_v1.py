import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    REPO_ROOT
    / "databricks/notebooks/"
    "b08_n1_candidate_003_flat_namespace_forensics_v1.py"
)
BUILDER = (
    REPO_ROOT
    / "databricks/notebooks/"
    "b08_n1_uc_native_overlay_lock_candidate.py"
)


def independent_nonidentity_journal_argv(step):
    venv_python = "<COMMAND_CWD>/build-venv/bin/python"
    tool_wheelhouse = "<COMMAND_CWD>/candidate/build-tool-wheelhouse"
    runtime_wheelhouse = "<COMMAND_CWD>/candidate/wheelhouse"
    return {
        "download_bootstrap_pip_wheel": [
            "<HOST_PYTHON>", "-I", "-B", "-m", "pip", "--isolated",
            "--disable-pip-version-check", "--no-cache-dir", "--quiet",
            "download", "--no-input", "--no-deps", "--only-binary=:all:",
            "--index-url", "<PRIMARY_INDEX_URL>", "--dest",
            tool_wheelhouse, "pip==25.0.1",
        ],
        "bootstrap_pip_into_isolated_venv": [
            "<HOST_PYTHON>", "-I", "-B", "-m", "pip", "--isolated",
            "--disable-pip-version-check", "--no-cache-dir", "--quiet",
            "--python", venv_python, "install", "--no-input", "--no-index",
            "--no-deps", "--only-binary=:all:", "--no-compile",
            "--require-hashes", "--find-links", tool_wheelhouse,
            "--requirement", "<COMMAND_CWD>/candidate/bootstrap-pip.lock",
        ],
        "download_exact_build_tool_wheels": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "download", "--no-deps", "--only-binary=:all:",
            "--index-url", "<PRIMARY_INDEX_URL>", "--dest", tool_wheelhouse,
            "setuptools==74.0.0", "wheel==0.45.1",
        ],
        "install_exact_build_tools_in_isolated_venv": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "install", "--no-index", "--only-binary=:all:",
            "--require-hashes", "--find-links", tool_wheelhouse,
            "--requirement", "<COMMAND_CWD>/candidate/build-tools.lock",
        ],
        "verify_isolated_build_tool_versions": [
            venv_python,
            "-c",
            (
                "import json;from importlib import metadata;print(json.dumps("
                "{name:metadata.version(name) for name in "
                "('pip','setuptools','wheel')},sort_keys=True))"
            ),
        ],
        "build_project_wheel_from_source_copy": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "wheel", "--no-deps", "--no-build-isolation",
            "--wheel-dir", runtime_wheelhouse, "<COMMAND_CWD>/project-source",
        ],
        "resolve_exact_runtime_roots_to_wheels": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "download", "--only-binary=:all:", "--index-url",
            "<PRIMARY_INDEX_URL>", "--extra-index-url",
            "<PYTORCH_CPU_INDEX_URL>", "--dest", runtime_wheelhouse,
            "numpy==2.4.6", "scipy==1.17.1", "threadpoolctl==3.6.0",
            "torch==2.12.1+cpu",
        ],
        "install_hash_locked_wheelhouse_to_isolated_overlay": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "install", "--no-index", "--only-binary=:all:",
            "--require-hashes", "--ignore-installed", "--no-compile",
            "--find-links", runtime_wheelhouse, "--prefix",
            "<COMMAND_CWD>/candidate/overlay", "--requirement",
            (
                "<COMMAND_CWD>/candidate/"
                "b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock.candidate"
            ),
        ],
    }.get(step)


def independently_extract_builder_pip_probe():
    tree = ast.parse(BUILDER.read_text())
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "PIP_IDENTITY_PROBE"
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "strip"
            and isinstance(node.value.func.value, ast.Constant)
            and isinstance(node.value.func.value.value, str)
        ):
            return node.value.func.value.value.strip()
    raise AssertionError("PIP_IDENTITY_PROBE literal not found in reviewed builder")


def load_notebook():
    spec = importlib.util.spec_from_file_location(
        "b08_n1_candidate_003_flat_namespace_forensics_v1",
        NOTEBOOK,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_canonical(value):
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def assert_no_authority(result):
    assert result["construction_or_reuse_authorized"] is False
    assert result["candidate_004_authorized"] is False


def synthetic_pip_identity(role):
    return {
        "pip_module_file_sha256": "1" * 64,
        "pip_module_file_size_bytes": 10,
        "pip_payload_closure_exact": True,
        "pip_payload_file_count": 3,
        "pip_payload_hashed_record_count": 2,
        "pip_payload_manifest_sha256": "2" * 64,
        "pip_payload_unhashed_record_count": 1,
        "pip_payload_unrecorded_bytecode_count": 0,
        "pip_record_file_sha256": "3" * 64,
        "pip_record_file_size_bytes": 20,
        "pip_version": "25.0.1",
        "runtime_role": role,
        "path_projection": {
            "pip_distribution_root_relative_to_install_prefix": (
                "lib/python3.12/site-packages"
            ),
            "pip_module_file_relative_to_install_prefix": (
                "lib/python3.12/site-packages/pip/__init__.py"
            ),
            "pip_record_file_relative_to_install_prefix": (
                "lib/python3.12/site-packages/pip-25.0.1.dist-info/RECORD"
            ),
        },
        "python_executable_relationship": (
            "RESOLVED_TARGET_WITHIN_INSTALL_PREFIX"
            if role == "ISOLATED_BUILD_VENV"
            else "RESOLVED_TARGET_OUTSIDE_INSTALL_PREFIX"
        ),
        "absolute_runtime_paths_persisted": False,
        "content_derived_payload_closure_persisted": True,
        "omitted_absolute_path_fields": [
            "pip_install_prefix",
            "pip_distribution_root",
            "pip_module_file",
            "pip_record_file",
            "python_executable",
        ],
    }


def synthetic_bootstrap_wheel():
    return {
        "filename": "pip-25.0.1-py3-none-any.whl",
        "sha256": "4" * 64,
        "size_bytes": 100_000,
        "distribution_name": "pip",
        "normalized_name": "pip",
        "version": "25.0.1",
        "wheel_tags": ["py3-none-any"],
        "embedded_record_sha256": "5" * 64,
        "embedded_payload_file_count": 10,
        "central_directory": {
            "entry_count": 10,
            "size_bytes": 1_000,
            "offset_bytes": 90_000,
            "zip64": False,
        },
    }


def synthetic_bootstrap_lock(wheel):
    payload = (
        "# REVIEW-PENDING F152 CANDIDATE; not an authority or runtime "
        "install instruction.\n"
        "# Install only after independent acceptance with --no-index "
        "--only-binary=:all: --require-hashes.\n"
        + wheel["normalized_name"]
        + "=="
        + wheel["version"]
        + " \\\n"
        + "    --hash=sha256:"
        + wheel["sha256"]
        + "\n"
    ).encode("ascii")
    return {"filename": "bootstrap-pip.lock", "sha256": sha256(payload)}


def promote_to_bootstrap_install_failure(module, receipt):
    state = receipt["attempt_state_before_failure_receipt_commit"]
    failed = state["command_journal"].pop()
    state["command_journal"].append(
        {
            "step": "download_bootstrap_pip_wheel",
            "argv": independent_nonidentity_journal_argv(
                "download_bootstrap_pip_wheel"
            ),
            "returncode": 0,
            "stdout_and_stderr_persisted": False,
            "output_excluded_as_nondeterministic_tool_telemetry": True,
        }
    )
    state["command_journal"].append(
        {
            "step": "rebind_host_pip_identity_before_target_install",
            "argv": [
                "<HOST_PYTHON>",
                "-I",
                "-B",
                "-c",
                "<pip-identity-probe>",
            ],
            "returncode": 0,
            "stdout_and_stderr_persisted": False,
            "output_excluded_as_nondeterministic_tool_telemetry": True,
        }
    )
    failed["step"] = "bootstrap_pip_into_isolated_venv"
    failed["argv"] = independent_nonidentity_journal_argv(
        "bootstrap_pip_into_isolated_venv"
    )
    state["command_journal"].append(failed)
    state["last_started_step"] = failed["step"]
    state["last_failed_step"] = failed["step"]
    state["last_completed_step"] = (
        "rebind_host_pip_identity_before_target_install"
    )
    state["host_pip_identity_reverified_before_target_install"] = True
    state["bootstrap_pip_install_begun"] = True
    state["build_tool_install_begun"] = True
    wheel = synthetic_bootstrap_wheel()
    state["bootstrap_pip_wheel_binding"] = wheel
    state["bootstrap_pip_lock_binding"] = synthetic_bootstrap_lock(wheel)
    receipt["error_detail"] = "bootstrap_pip_into_isolated_venv:returncode=1"
    return state


def independently_reconstruct_reviewed_intent():
    manifest_files = []
    source_paths = [
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "README.md",
        *sorted((REPO_ROOT / "src/heterodiff").rglob("*.py")),
    ]
    for path in source_paths:
        raw = path.read_bytes()
        manifest_files.append(
            {
                "relative_path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": sha256(raw),
                "size_bytes": len(raw),
                "mode_octal": "0644",
            }
        )
    manifest_projection = {
        "schema_version": "heterodiff-b08-n1-project-source-manifest-v1",
        "files": manifest_files,
    }
    source_manifest = {
        **manifest_projection,
        "record_sha256": sha256(
            b"heterodiff/b08/n1/project-source-manifest/v1\0"
            + independent_canonical(manifest_projection)
        ),
    }

    profile_path = REPO_ROOT / (
        "requirements/"
        "b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
        "native-runtime-profile-v2.template.json"
    )
    profile_raw = profile_path.read_bytes()
    profile_value = json.loads(profile_raw.decode("ascii"))
    profile_projection = dict(profile_value)
    profile_projection.pop("record_sha256")
    profile_validation = {
        "file_sha256": sha256(profile_raw),
        "semantic_sha256": sha256(
            b"heterodiff/b08/databricks-native-runtime-profile/v2\0"
            + independent_canonical(profile_projection)
        ),
    }

    builder_relative = (
        "databricks/notebooks/"
        "b08_n1_uc_native_overlay_lock_candidate.py"
    )
    launcher_relative = (
        "databricks/notebooks/"
        "b08_n1_uc_native_overlay_lock_candidate_launcher.py"
    )
    builder_raw = (REPO_ROOT / builder_relative).read_bytes()
    launcher_raw = (REPO_ROOT / launcher_relative).read_bytes()
    canonical_launcher_raw = (
        launcher_raw[:-1] if launcher_raw.endswith(b"\n") else launcher_raw
    )
    builder_binding = {
        "relative_path": builder_relative,
        "sha256": sha256(builder_raw),
        "size_bytes": len(builder_raw),
        "canonical_mode_octal": "0644",
        "runtime_mode_used_for_identity": False,
        "terminal_lf_policy": "EXACT_BYTES",
    }
    launcher_binding = {
        "relative_path": launcher_relative,
        "sha256": sha256(canonical_launcher_raw),
        "size_bytes": len(canonical_launcher_raw),
        "canonical_mode_octal": "0644",
        "runtime_mode_used_for_identity": False,
        "terminal_lf_policy": "IGNORE_EXACTLY_ONE_OPTIONAL_TERMINAL_LF",
    }

    source_snapshot_relative = (
        "requirements/"
        "b08-n1-candidate-003-project-source-snapshot-v1.json"
    )
    source_snapshot_raw = (REPO_ROOT / source_snapshot_relative).read_bytes()
    source_snapshot = json.loads(source_snapshot_raw.decode("ascii"))
    source_identity_projection = {
        "schema_version": "heterodiff-b08-n1-content-addressed-source-identity-v2",
        "identity_kind": "REVIEWED_CONTENT_ADDRESSED_SOURCE_SNAPSHOT",
        "reviewed_snapshot_anchor": {
            "relative_path": source_snapshot_relative,
            "sha256": sha256(source_snapshot_raw),
            "size_bytes": len(source_snapshot_raw),
            "canonical_mode_octal": "0644",
            "runtime_mode_used_for_identity": False,
        },
        "offline_declared_git_commit": source_snapshot["declared_git_commit"],
        "source_date_epoch": source_snapshot["source_date_epoch"],
        "project_source_manifest_sha256": source_manifest["record_sha256"],
        "project_source_file_count": len(manifest_files),
        "project_source_total_size_bytes": sum(
            item["size_bytes"] for item in manifest_files
        ),
        "construction_notebook": builder_binding,
        "hash_first_launcher": launcher_binding,
        "selected_source_bytes_match_reviewed_snapshot": True,
        "runtime_git_metadata_consulted": False,
        "live_git_checkout_identity_verified": False,
        "whole_repository_cleanliness_checked": False,
    }
    source_identity = {
        **source_identity_projection,
        "record_sha256": sha256(
            b"heterodiff/b08/n1/content-addressed-source-identity/v2\0"
            + independent_canonical(source_identity_projection)
        ),
    }

    review_bindings = [
        {
            "relative_path": (
                "PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_"
                "SUCCESSOR_V2_INDEPENDENT_REVIEW.md"
            ),
            "sha256": (
                "0d75872dc984fbbaf671875407b082dfb447bc007e55572158ed23383c2df450"
            ),
            "size_bytes": 8456,
            "mode_octal": "0755",
        },
        {
            "relative_path": (
                "PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_"
                "INDEPENDENT_REVIEW.md"
            ),
            "sha256": (
                "7612dbe3c4072c0ab2847bb17d99d6a5aa66ccfff80734f0d961baec57229a59"
            ),
            "size_bytes": 5735,
            "mode_octal": "0755",
        },
        {
            "relative_path": (
                "PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_001_"
                "OUTCOME.md"
            ),
            "sha256": (
                "f96160da93789d4749b3ce005182a0f57a49a5bc4408296d46ca4fd7fc71bcd7"
            ),
            "size_bytes": 5120,
            "mode_octal": "0755",
        },
    ]
    review_package_projection = {
        "schema_version": "heterodiff-b08-n1-candidate-003-review-package-v2",
        "builder_source_binding": builder_binding,
        "launcher_source_binding": launcher_binding,
        "project_source_manifest_sha256": source_manifest["record_sha256"],
        "project_source_file_count": len(manifest_files),
        "source_identity_binding": source_identity,
        "native_profile_file_sha256": profile_validation["file_sha256"],
        "native_profile_semantic_sha256": profile_validation[
            "semantic_sha256"
        ],
        "native_target_review_sha256": review_bindings[0]["sha256"],
        "uc_volume_probe_review_sha256": review_bindings[1]["sha256"],
        "uc_volume_probe_outcome_sha256": review_bindings[2]["sha256"],
    }
    review_package = {
        **review_package_projection,
        "record_sha256": sha256(
            b"heterodiff/b08/n1/candidate-003-review-package/v2\0"
            + independent_canonical(review_package_projection)
        ),
    }
    launch_evidence = {
        "schema_version": "heterodiff-b08-n1-hash-first-launch-v2",
        "builder_relative_path": builder_relative,
        "operator_expected_builder_sha256": builder_binding["sha256"],
        "executed_payload_sha256": builder_binding["sha256"],
        "executed_payload_size_bytes": builder_binding["size_bytes"],
        "launcher_relative_path": launcher_relative,
        "launcher_source_identity_kind": (
            "SHA256_OF_CANONICAL_LAUNCHER_PAYLOAD"
        ),
        "launcher_source_sha256": launcher_binding["sha256"],
        "launcher_source_size_bytes": launcher_binding["size_bytes"],
        "launcher_terminal_lf_policy": launcher_binding[
            "terminal_lf_policy"
        ],
        "same_in_memory_payload_compiled_and_executed": True,
    }
    parent = "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    candidate = "b08-n1-overlay-candidate-003"
    reserved_names = [
        f"{candidate}.attempt-intent.json",
        *(f"{candidate}.payload-{ordinal:04d}.bin" for ordinal in range(128)),
        f"{candidate}.payload-manifest.json",
        f"{candidate}.construction-receipt.json",
        f"{candidate}.construction-failure-receipt.json",
    ]
    intent = {
        "schema_version": "heterodiff-b08-n1-uc-native-attempt-intent-v2",
        "record_sha256": "0" * 64,
        "state": "ATTEMPT_SPENT_BEFORE_NETWORK_OR_BUILD",
        "profile": {
            "relative_path": profile_path.relative_to(REPO_ROOT).as_posix(),
            "file_sha256": profile_validation["file_sha256"],
            "semantic_sha256": profile_validation["semantic_sha256"],
            "independent_review": review_bindings[0],
            "uc_volume_probe_independent_review": review_bindings[1],
            "uc_volume_probe_001_outcome": review_bindings[2],
        },
        "source": {
            "reviewed_source_identity": source_identity,
            "source_date_epoch": source_identity["source_date_epoch"],
            "source_identity_verification_state": (
                "REVIEWED_SNAPSHOT_VERIFIED_AT_PREFLIGHT_BEFORE_INTENT_"
                "AND_AFTER_INTENT_BEFORE_NETWORK_OR_BUILD"
            ),
            "source_manifest_sha256": source_manifest["record_sha256"],
            "construction_notebook": builder_binding,
            "hash_first_launcher": launcher_binding,
            "live_git_checkout_identity_verified": False,
            "whole_repository_cleanliness_checked": False,
        },
        "external_review_authority": {
            "review_package": review_package,
            "operator_authorized_review_package_sha256": review_package[
                "record_sha256"
            ],
            "authorization_matched_before_intent": True,
            "hash_first_launch_evidence": launch_evidence,
        },
        "destination": {
            "virtual_candidate_prefix": f"{parent}/{candidate}",
            "parent": parent,
            "candidate_id": candidate,
            "reserved_leaf_names": reserved_names,
            "required_initial_state": "ALL_RESERVED_LEAVES_ABSENT",
        },
        "network": {
            "primary_index_url_sha256": sha256(
                b"https://pypi.org/simple"
            ),
            "pytorch_cpu_index_url_sha256": sha256(
                b"https://download.pytorch.org/whl/cpu"
            ),
            "explicitly_authorized": True,
        },
        "construction": {
            "one_shot": True,
            "base_runtime_install_permitted": False,
            "wheels_only": True,
            "sdists_permitted": False,
            "complete_transitive_hash_lock_required": True,
            "study_or_test_data_permitted": False,
            "calibration_training_or_inference_permitted": False,
            "external_concurrent_candidate_namespace_mutation_permitted": False,
            "uc_storage_protocol": "FLAT_APPEND_ONLY_EXCLUSIVE_CREATE",
            "payload_encoding": "DETERMINISTIC_ZIP_STORED_ZIP64_CHUNKS",
            "path_visible_binding": "EXACT_SIZE_AND_SHA256_TWO_FRESH_READBACKS",
            (
                "fsync_chmod_chown_inode_device_timestamp_rename_or_delete_"
                "used_for_uc_custody"
            ): False,
            "success_receipt_is_commit_marker": True,
        },
        "nonproofs": [
            "ATOMIC_SNAPSHOT",
            "CACHE_COHERENCE",
            "FUTURE_RUNTIME_OR_FUSE_STABILITY",
            "HISTORICAL_OBJECT_IDENTITY_OR_LINEAGE",
            "IMMUTABILITY",
            "PHYSICAL_DURABILITY",
            "LARGE_OBJECT_WRITE_GENERALIZATION_FROM_PROBE",
            "CAPACITY_OR_STORAGE_RESERVATION",
            "UNOBSERVED_NATIVE_PROFILE_TARGET_FIELDS",
            "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
            "UNIVERSAL_ATOMICITY",
        ],
    }
    intent_projection = dict(intent)
    intent_projection.pop("record_sha256")
    intent["record_sha256"] = sha256(
        b"heterodiff/b08/n1/uc-native-attempt-intent/v2\0"
        + independent_canonical(intent_projection)
    )
    return intent, independent_canonical(intent) + b"\n", review_package


def synthetic_intent(module):
    value = {
        "schema_version": module.ATTEMPT_INTENT_SCHEMA,
        "record_sha256": "0" * 64,
        "state": "ATTEMPT_SPENT_BEFORE_NETWORK_OR_BUILD",
        "profile": {},
        "source": {
            "source_manifest_sha256": module.EXPECTED_SOURCE_MANIFEST_SHA256,
            "reviewed_source_identity": {
                "record_sha256": module.EXPECTED_SOURCE_IDENTITY_SHA256,
            },
            "construction_notebook": {
                "sha256": module.EXPECTED_BUILDER_SHA256,
            },
            "hash_first_launcher": {
                "sha256": module.EXPECTED_LAUNCHER_SHA256,
            },
        },
        "external_review_authority": {
            "review_package": {
                "record_sha256": module.EXPECTED_REVIEW_PACKAGE_SHA256,
            },
            "operator_authorized_review_package_sha256": (
                module.EXPECTED_REVIEW_PACKAGE_SHA256
            ),
            "authorization_matched_before_intent": True,
            "hash_first_launch_evidence": {
                "executed_payload_sha256": module.EXPECTED_BUILDER_SHA256,
                "launcher_source_sha256": module.EXPECTED_LAUNCHER_SHA256,
                "same_in_memory_payload_compiled_and_executed": True,
            },
        },
        "destination": {
            "virtual_candidate_prefix": module.VIRTUAL_CANDIDATE_PREFIX,
            "parent": module.EXACT_PARENT,
            "candidate_id": module.CANDIDATE_ID,
            "reserved_leaf_names": list(module.reserved_leaf_names()),
            "required_initial_state": "ALL_RESERVED_LEAVES_ABSENT",
        },
        "network": {},
        "construction": {},
        "nonproofs": [],
    }
    projection = dict(value)
    projection.pop("record_sha256")
    value["record_sha256"] = sha256(
        module.ATTEMPT_INTENT_DOMAIN + independent_canonical(projection)
    )
    return value, independent_canonical(value) + b"\n"


def synthetic_failure(module, intent_raw, **overrides):
    intent_sha = sha256(intent_raw)
    intent_binding = {
        "name": module.INTENT_LEAF_NAME,
        "sha256": intent_sha,
        "size_bytes": len(intent_raw),
        "fresh_readback_count": 2,
    }
    state = {
        "attempt_namespace_spent": True,
        "intent_create_begun": True,
        "durable_intent_committed": True,
        "durable_intent_may_exist": True,
        "durable_intent_expected_sha256": intent_sha,
        "durable_intent_expected_size_bytes": len(intent_raw),
        "managed_uc_write_phase_entered": True,
        "managed_uc_write_begun": True,
        "managed_uc_exclusive_create_calls_begun": 1,
        "managed_uc_confirmed_leaf_count": 1,
        "managed_uc_confirmed_bytes_written": len(intent_raw),
        "managed_uc_last_leaf_create_begun": module.INTENT_LEAF_NAME,
        "managed_uc_last_leaf_may_exist": module.INTENT_LEAF_NAME,
        "managed_uc_last_leaf_expected_sha256": intent_sha,
        "managed_uc_last_leaf_expected_size_bytes": len(intent_raw),
        "managed_uc_last_confirmed_binding": dict(intent_binding),
        "managed_uc_confirmed_bindings": [dict(intent_binding)],
        "staging_write_begun": True,
        "preintent_source_identity_verification_begun": True,
        "preintent_source_identity_verification_completed": True,
        "postintent_source_identity_verification_begun": True,
        "postintent_source_identity_verification_completed": True,
        "staged_source_manifest_verified": True,
        "network_contact_begun": True,
        "package_resolution_begun": True,
        "isolated_venv_creation_begun": True,
        "host_pip_identity": synthetic_pip_identity(
            "HOST_NOTEBOOK_INTERPRETER"
        ),
        "host_pip_identity_reverified_before_target_install": False,
        "bootstrap_pip_wheel_binding": None,
        "bootstrap_pip_lock_binding": None,
        "isolated_venv_pip_identity": None,
        "bootstrap_pip_install_begun": False,
        "build_tool_install_begun": False,
        "project_wheel_build_begun": False,
        "overlay_install_begun": False,
        "managed_uc_payload_publish_begun": False,
        "success_receipt_phase_entered": False,
        "success_receipt_create_call_begun": False,
        "success_receipt_may_exist": False,
        "success_receipt_committed": False,
        "failure_receipt_commit_begun": True,
        "failure_receipt_create_call_begun": False,
        "failure_receipt_may_exist": False,
        "failure_receipt_committed": False,
        "failure_receipt_error_code": None,
        "failure_receipt_error_detail": None,
        "failure_receipt_skipped_for_terminal_receipt_ambiguity": False,
        "terminal_receipt_ambiguity": False,
        "staging_cleanup_begun": True,
        "staging_cleanup_completed": True,
        "last_started_step": "download_bootstrap_pip_wheel",
        "last_completed_step": "bind_host_pip_identity_before_bootstrap",
        "last_failed_step": "download_bootstrap_pip_wheel",
        "command_journal": [
            {
                "step": "bind_host_pip_identity_before_bootstrap",
                "argv": [
                    "<HOST_PYTHON>",
                    "-I",
                    "-B",
                    "-c",
                    "<pip-identity-probe>",
                ],
                "returncode": 0,
                "stdout_and_stderr_persisted": False,
                "output_excluded_as_nondeterministic_tool_telemetry": True,
            },
            {
                "step": "download_bootstrap_pip_wheel",
                "argv": independent_nonidentity_journal_argv(
                    "download_bootstrap_pip_wheel"
                ),
                "returncode": 1,
                "stdout_and_stderr_persisted": (
                    "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
                ),
                "output_excluded_as_nondeterministic_tool_telemetry": False,
                "failure_diagnostics": {
                    "stdout": {
                        "captured_byte_count": 0,
                        "captured_sha256": sha256(b""),
                        "observed_byte_count_before_termination": 0,
                        "capture_complete_through_process_termination": True,
                        "sanitized_tail_byte_limit": (
                            65_536
                        ),
                        "runtime_paths_and_exact_index_urls_sanitized": True,
                        "sanitized_tail_utf8": "",
                    },
                    "stderr": {
                        "captured_byte_count": 12,
                        "captured_sha256": sha256(b"safe failure"),
                        "observed_byte_count_before_termination": 12,
                        "capture_complete_through_process_termination": True,
                        "sanitized_tail_byte_limit": (
                            65_536
                        ),
                        "runtime_paths_and_exact_index_urls_sanitized": True,
                        "sanitized_tail_utf8": "safe failure",
                    },
                },
            }
        ],
    }
    value = {
        "schema_version": module.FAILURE_RECEIPT_SCHEMA,
        "decision": (
            "TERMINAL_NO_GO_PARTIAL_OR_FAILED_ATTEMPT_REVIEW_REQUIRED"
        ),
        "attempt_intent_sha256": intent_sha,
        "error_code": "TOOL_STEP_FAILED",
        "error_detail": "download_bootstrap_pip_wheel:returncode=1",
        "attempt_state_before_failure_receipt_commit": state,
        "safety": dict(module.EXPECTED_FAILURE_SAFETY),
        "not_proven": list(module.EXPECTED_FAILURE_NONPROOFS),
    }
    value.update(overrides)
    return value, independent_canonical(value) + b"\n"


def configure_fixture_target(module, monkeypatch, parent):
    monkeypatch.setattr(module, "EXACT_PARENT", str(parent))
    monkeypatch.setattr(
        module,
        "VIRTUAL_CANDIDATE_PREFIX",
        f"{parent}/{module.CANDIDATE_ID}",
    )
    # The production entrypoint is frozen to /Volumes. Unit fixtures exercise
    # the already separately tested implementation contract on a temporary
    # directory without weakening the production constant.
    monkeypatch.setattr(module, "validate_frozen_contract", lambda: None)
    probe = b"<pip-identity-probe>"
    monkeypatch.setattr(
        module,
        "EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES",
        len(probe),
    )
    monkeypatch.setattr(
        module,
        "EXPECTED_PIP_IDENTITY_PROBE_SHA256",
        sha256(probe),
    )


def write_valid_pair(module, monkeypatch, parent):
    configure_fixture_target(module, monkeypatch, parent)
    intent, intent_raw = synthetic_intent(module)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw))
    monkeypatch.setattr(
        module,
        "EXPECTED_INTENT_RECORD_SHA256",
        intent["record_sha256"],
    )
    _, failure_raw = synthetic_failure(module, intent_raw)
    intent_path = parent / module.INTENT_LEAF_NAME
    failure_path = parent / module.FAILURE_RECEIPT_LEAF_NAME
    intent_path.write_bytes(intent_raw)
    failure_path.write_bytes(failure_raw)
    return intent_path, failure_path, intent_raw, failure_raw


def capture_with_failure_mutation(module, monkeypatch, parent, mutate):
    configure_fixture_target(module, monkeypatch, parent)
    intent, intent_raw = synthetic_intent(module)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw))
    monkeypatch.setattr(
        module,
        "EXPECTED_INTENT_RECORD_SHA256",
        intent["record_sha256"],
    )
    failure, _ = synthetic_failure(module, intent_raw)
    mutate(failure)
    failure_raw = independent_canonical(failure) + b"\n"
    (parent / module.INTENT_LEAF_NAME).write_bytes(intent_raw)
    (parent / module.FAILURE_RECEIPT_LEAF_NAME).write_bytes(failure_raw)
    return module.capture_candidate()


def convert_failed_entry_to_exception(
    receipt,
    execution_error,
    execution_detail=None,
    capture_complete=False,
):
    entry = receipt["attempt_state_before_failure_receipt_commit"][
        "command_journal"
    ][1]
    entry["returncode"] = None
    entry["execution_error"] = execution_error
    entry["execution_error_detail"] = execution_detail
    entry.pop("output_excluded_as_nondeterministic_tool_telemetry")
    for stream in entry["failure_diagnostics"].values():
        stream["capture_complete_through_process_termination"] = (
            capture_complete
        )
    receipt["error_code"] = (
        execution_error
        if execution_error.startswith("TOOL_")
        else "TOOL_STEP_EXECUTION_FAILED"
    )
    receipt["error_detail"] = (
        "download_bootstrap_pip_wheel:"
        + execution_error
        + ("" if execution_detail is None else ":" + execution_detail)
    )
    return entry


def test_frozen_flat_namespace_contract_and_exact_expected_binding():
    module = load_notebook()
    names = module.reserved_leaf_names()

    assert module.EXACT_PARENT == (
        "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    )
    assert module.CANDIDATE_ID == "b08-n1-overlay-candidate-003"
    assert len(names) == len(set(names)) == 132
    assert names[0] == module.INTENT_LEAF_NAME
    assert names[1].endswith(".payload-0000.bin")
    assert names[128].endswith(".payload-0127.bin")
    assert names[-3:] == (
        module.PAYLOAD_MANIFEST_LEAF_NAME,
        module.SUCCESS_RECEIPT_LEAF_NAME,
        module.FAILURE_RECEIPT_LEAF_NAME,
    )
    assert all("/" not in name and "\\" not in name for name in names)
    assert module.EXPECTED_INTENT_SIZE_BYTES == 15_973
    assert module.EXPECTED_INTENT_FILE_SHA256 == (
        "ea8441151c07aef1a6fdf3320ff54d61237d3812b0c679cc0c2954a8db416015"
    )
    assert module.EXPECTED_INTENT_RECORD_SHA256 == (
        "f9832c8b78a802254891b2d6f117c6c54f958a729bbac44f7bc1fcb5979f224f"
    )
    assert module.EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES == 12_179


def test_all_twelve_builder_argv_bindings_have_independent_oracle():
    module = load_notebook()
    expected_steps = (
        "bind_host_pip_identity_before_bootstrap",
        "download_bootstrap_pip_wheel",
        "rebind_host_pip_identity_before_target_install",
        "bootstrap_pip_into_isolated_venv",
        "bind_isolated_venv_pip_identity_after_bootstrap",
        "download_exact_build_tool_wheels",
        "install_exact_build_tools_in_isolated_venv",
        "verify_isolated_build_tool_versions",
        "build_project_wheel_from_source_copy",
        "resolve_exact_runtime_roots_to_wheels",
        "install_hash_locked_wheelhouse_to_isolated_overlay",
        "rebind_isolated_venv_pip_identity_before_manifest",
    )
    assert module.EXPECTED_TOOL_JOURNAL_STEPS == expected_steps
    assert sha256(BUILDER.read_bytes()) == module.EXPECTED_BUILDER_SHA256

    probe = independently_extract_builder_pip_probe()
    probe_bytes = probe.encode("utf-8")
    assert len(probe_bytes) == module.EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES
    assert sha256(probe_bytes) == module.EXPECTED_PIP_IDENTITY_PROBE_SHA256
    identity_interpreters = {
        "bind_host_pip_identity_before_bootstrap": "<HOST_PYTHON>",
        "rebind_host_pip_identity_before_target_install": "<HOST_PYTHON>",
        "bind_isolated_venv_pip_identity_after_bootstrap": (
            "<COMMAND_CWD>/build-venv/bin/python"
        ),
        "rebind_isolated_venv_pip_identity_before_manifest": (
            "<COMMAND_CWD>/build-venv/bin/python"
        ),
    }
    for step in expected_steps:
        if step in identity_interpreters:
            argv = [identity_interpreters[step], "-I", "-B", "-c", probe]
        else:
            argv = independent_nonidentity_journal_argv(step)
            assert module.expected_nonidentity_journal_argv(step) == argv
        errors = []
        module.validate_journal_argv(step, argv, errors)
        assert errors == []
    assert module.EXPECTED_PIP_IDENTITY_PROBE_SHA256 == (
        "12ec0e3ba51bc36372fa66fc2976992a0eec7ad76c1929ee7c59628b976fe86c"
    )
    assert module.MAX_JOURNAL_STRING_BYTES == 16 * 1024
    assert (
        module.EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES
        <= module.MAX_JOURNAL_STRING_BYTES
    )


def test_builder_oracle_independently_reconstructs_exact_expected_intent():
    module = load_notebook()
    intent, raw, review_package = independently_reconstruct_reviewed_intent()

    assert len(raw) == module.EXPECTED_INTENT_SIZE_BYTES
    assert sha256(raw) == module.EXPECTED_INTENT_FILE_SHA256
    assert intent["record_sha256"] == module.EXPECTED_INTENT_RECORD_SHA256
    assert review_package["record_sha256"] == (
        module.EXPECTED_REVIEW_PACKAGE_SHA256
    )


def test_valid_stable_pair_reports_exact_diagnosis_without_mutation(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    intent_path, failure_path, _, _ = write_valid_pair(
        module, monkeypatch, tmp_path
    )
    before = {
        intent_path: intent_path.stat(),
        failure_path: failure_path.stat(),
    }

    result = module.capture_candidate()

    after = {
        intent_path: intent_path.stat(),
        failure_path: failure_path.stat(),
    }
    assert result["decision"] == (
        "PASS_READ_ONLY_FORENSIC_SCHEMA_CONFORMANT_JOURNALED_"
        "TERMINAL_FAILURE_RECEIPT"
    )
    assert result["candidate_disposition"] == (
        "PERMANENTLY_SPENT_SCHEMA_CONFORMANT_TERMINAL_FAILURE"
    )
    assert result["snapshots_equal"] is True
    assert result["diagnosis"]["failure_class"] == "SUBPROCESS_NONZERO_EXIT"
    assert result["diagnosis"]["failed_journal_entry_ordinal"] == 1
    assert result["diagnosis"]["failed_journal_returncode"] == 1
    assert result["diagnosis"]["error_code_binding"]["sha256"] == sha256(
        b"TOOL_STEP_FAILED"
    )
    assert result["diagnosis"]["stage_bindings"]["last_failed_step"][
        "sha256"
    ] == sha256(
        b"download_bootstrap_pip_wheel"
    )
    journal = result["diagnosis"]["command_journal"]
    assert journal["entry_count"] == 2
    stderr = journal["entries"][1]["failure_diagnostic_bindings"]["stderr"]
    assert stderr["sanitized_tail_size_bytes"] == len(b"safe failure")
    assert stderr["sanitized_tail_sha256"] == sha256(b"safe failure")
    assert "safe failure" not in json.dumps(journal)
    assert result["safety"]["control_payload_reads_completed"] == 4
    assert result["safety"]["direct_external_network_endpoint_accessed"] is False
    assert result["safety"]["databricks_managed_storage_io_attempted"] is True
    assert result["safety"][
        "databricks_managed_storage_io_may_have_been_performed"
    ] is True
    assert result["safety"]["parent_descriptor_open_completed_count"] == 2
    assert result["custody_model"]["receipt_writer_identity_authenticated"] is False
    assert result["custody_model"]["receipt_builder_authorship_claimed"] is False
    assert result["construction_or_reuse_authorized"] is False
    for path in before:
        assert before[path].st_size == after[path].st_size
        assert before[path].st_mtime_ns == after[path].st_mtime_ns


def test_receipt_text_is_never_republished_even_when_marked_sanitized(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    secret = "SELF_ASSERTED_SANITIZED_SECRET_7f691"

    def mutate(receipt):
        receipt["error_code"] = secret
        receipt["error_detail"] = secret
        state = receipt["attempt_state_before_failure_receipt_commit"]
        entry = state["command_journal"][1]
        entry["returncode"] = None
        entry["execution_error"] = secret
        entry["execution_error_detail"] = secret
        entry.pop("output_excluded_as_nondeterministic_tool_telemetry")
        stream = entry["failure_diagnostics"]["stderr"]
        stream["captured_byte_count"] = len(secret.encode())
        stream["observed_byte_count_before_termination"] = len(secret.encode())
        stream["captured_sha256"] = sha256(secret.encode())
        stream["sanitized_tail_utf8"] = secret

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    serialized = json.dumps(result, sort_keys=True)
    assert secret not in serialized
    assert "diagnosis" not in result
    assert (
        "FAILURE_COMMAND_JOURNAL_EXECUTION_ERROR_CLASS_INVALID"
        in result["validation_errors"]
    )


def test_invalid_declared_intent_record_is_never_republished(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    secret = "AWSSECRETACCESSKEY_INTENT_ABC123"
    intent, _ = synthetic_intent(module)
    intent["record_sha256"] = secret
    intent_raw = independent_canonical(intent) + b"\n"
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(
        module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw)
    )
    _, failure_raw = synthetic_failure(module, intent_raw)
    (tmp_path / module.INTENT_LEAF_NAME).write_bytes(intent_raw)
    (tmp_path / module.FAILURE_RECEIPT_LEAF_NAME).write_bytes(failure_raw)

    result = module.capture_candidate()

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert secret not in json.dumps(result, sort_keys=True)
    validation = result["control_validation"]["intent"]
    assert "declared_record_sha256" not in validation
    assert validation["declared_record_sha256_is_lower_hex"] is False
    assert validation["declared_record_sha256_matches_computed"] is False
    assert validation["declared_record_sha256_matches_expected"] is False
    assert_no_authority(result)


def test_builder_reachable_timeout_passes_without_republishing_text(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    secret = "SELF_ASSERTED_SANITIZED_SECRET_7f691"

    def mutate(receipt):
        receipt["error_code"] = "TOOL_STEP_EXECUTION_FAILED"
        receipt["error_detail"] = "download_bootstrap_pip_wheel:TimeoutExpired"
        state = receipt["attempt_state_before_failure_receipt_commit"]
        entry = state["command_journal"][1]
        entry["returncode"] = None
        entry["execution_error"] = "TimeoutExpired"
        entry["execution_error_detail"] = None
        entry.pop("output_excluded_as_nondeterministic_tool_telemetry")
        stream = entry["failure_diagnostics"]["stderr"]
        stream["captured_byte_count"] = len(secret.encode())
        stream["observed_byte_count_before_termination"] = len(secret.encode())
        stream["captured_sha256"] = sha256(secret.encode())
        stream["sanitized_tail_utf8"] = secret

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    serialized = json.dumps(result, sort_keys=True)
    assert secret not in serialized
    entry = result["diagnosis"]["command_journal"]["entries"][1]
    assert entry["execution_error_binding"]["sha256"] == sha256(
        b"TimeoutExpired"
    )
    assert entry["failure_diagnostic_bindings"]["stderr"][
        "sanitized_tail_sha256"
    ] == sha256(secret.encode())


@pytest.mark.parametrize("returncode", [-64, -1, 1, 255])
def test_linux_subprocess_returncode_boundaries_pass(
    tmp_path,
    monkeypatch,
    returncode,
):
    module = load_notebook()

    def mutate(receipt):
        entry = receipt["attempt_state_before_failure_receipt_commit"][
            "command_journal"
        ][1]
        entry["returncode"] = returncode
        receipt["error_detail"] = (
            "download_bootstrap_pip_wheel:returncode=" + str(returncode)
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert result["diagnosis"]["failed_journal_returncode"] == returncode


def test_builder_reachable_popen_os_error_requires_canonical_empty_streams(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt, "PermissionError", capture_complete=False
        )
        for stream in entry["failure_diagnostics"].values():
            stream["captured_byte_count"] = 0
            stream["observed_byte_count_before_termination"] = 0
            stream["captured_sha256"] = sha256(b"")
            stream["sanitized_tail_utf8"] = ""

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert result["diagnosis"]["failure_class"] == (
        "SUBPROCESS_EXECUTION_EXCEPTION"
    )


@pytest.mark.parametrize(
    ("execution_error", "execution_detail"),
    [
        ("TOOL_OUTPUT_READER_DID_NOT_QUIESCE", None),
        ("TOOL_OUTPUT_READER_FAILED", "stderr:RuntimeError"),
        ("TOOL_SUBPROCESS_SUPERVISOR_FAILED", "RuntimeError"),
    ],
)
def test_builder_reachable_candidate_errors_require_incomplete_capture(
    tmp_path,
    monkeypatch,
    execution_error,
    execution_detail,
):
    module = load_notebook()

    def mutate(receipt):
        convert_failed_entry_to_exception(
            receipt,
            execution_error,
            execution_detail,
            capture_complete=False,
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")


def test_builder_reachable_stream_overflow_has_exact_named_stream_evidence(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt,
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            "stderr",
            capture_complete=False,
        )
        stream = entry["failure_diagnostics"]["stderr"]
        stream["captured_byte_count"] = 16_777_216
        stream["observed_byte_count_before_termination"] = (
            16_777_217
        )
        stream["captured_sha256"] = "a" * 64

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        (
            "outer_nonzero_detail_none",
            "FAILURE_COMMAND_JOURNAL_NONZERO_DETAIL_MISMATCH",
        ),
        (
            "nonzero_capture_incomplete",
            "FAILURE_DIAGNOSTIC_NONZERO_CAPTURE_INCOMPLETE",
        ),
        (
            "stream_completeness_diverged",
            "FAILURE_DIAGNOSTIC_STREAM_COMPLETENESS_DIVERGED",
        ),
        (
            "captured_counter_over_bound",
            "FAILURE_DIAGNOSTIC_CAPTURE_COUNT_INVALID",
        ),
        (
            "returncode_above_posix_exit_domain",
            "FAILURE_COMMAND_JOURNAL_RETURNCODE_INVALID",
        ),
        (
            "returncode_below_linux_signal_domain",
            "FAILURE_COMMAND_JOURNAL_RETURNCODE_INVALID",
        ),
        (
            "popen_os_error_has_nonempty_capture",
            "FAILURE_DIAGNOSTIC_POPEN_OS_ERROR_NOT_CANONICAL_EMPTY",
        ),
        (
            "timeout_capture_incomplete",
            "FAILURE_DIAGNOSTIC_TIMEOUT_CAPTURE_NOT_COMPLETE",
        ),
        (
            "candidate_error_capture_complete",
            "FAILURE_DIAGNOSTIC_CANDIDATE_ERROR_CAPTURE_NOT_INCOMPLETE",
        ),
        (
            "overflow_stream_not_at_limit",
            "FAILURE_DIAGNOSTIC_STREAM_OVERFLOW_EVIDENCE_INVALID",
        ),
        (
            "reader_error_detail_not_identifier",
            "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH",
        ),
        (
            "supervisor_error_detail_not_identifier",
            "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH",
        ),
        (
            "cleanup_incomplete_without_error",
            "FAILURE_STAGING_CLEANUP_OUTCOME_INCOMPLETE",
        ),
        (
            "cleanup_complete_with_error",
            "FAILURE_STAGING_CLEANUP_OUTCOME_CONFLICT",
        ),
        (
            "cleanup_error_not_identifier",
            "FAILURE_STAGING_CLEANUP_ERROR_INVALID",
        ),
        (
            "pip_count_over_bound",
            "FAILURE_HOST_PIP_IDENTITY_PAYLOAD_CLOSURE_INVALID",
        ),
        (
            "pip_declared_file_count_under_three",
            "FAILURE_HOST_PIP_IDENTITY_PAYLOAD_CLOSURE_INVALID",
        ),
        (
            "pip_all_files_unrecorded_bytecode",
            "FAILURE_HOST_PIP_IDENTITY_PAYLOAD_CLOSURE_INVALID",
        ),
        (
            "pip_control_size_over_bound",
            "FAILURE_HOST_PIP_IDENTITY_SIZE_INVALID:"
            "pip_module_file_size_bytes",
        ),
        (
            "pip_path_noncanonical",
            "FAILURE_HOST_PIP_IDENTITY_PATH_PROJECTION_INVALID",
        ),
        (
            "pip_path_unrelated",
            "FAILURE_HOST_PIP_IDENTITY_PATH_RELATIONSHIP_INVALID",
        ),
        (
            "bootstrap_wheel_over_bound",
            "FAILURE_BOOTSTRAP_WHEEL_BINDING_CONTENT_INVALID",
        ),
        (
            "bootstrap_central_count_under_payload",
            "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID",
        ),
        (
            "bootstrap_payload_count_under_three",
            "FAILURE_BOOTSTRAP_WHEEL_BINDING_CONTENT_INVALID",
        ),
        (
            "bootstrap_central_size_below_header_floor",
            "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID",
        ),
        (
            "bootstrap_central_offset_below_local_header_floor",
            "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID",
        ),
        (
            "bootstrap_central_missing_trailer_space",
            "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID",
        ),
        (
            "bootstrap_nonzip64_entry_count_overflow",
            "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID",
        ),
        (
            "bootstrap_lock_not_derived",
            "FAILURE_BOOTSTRAP_LOCK_SHA256_DERIVATION_MISMATCH",
        ),
        (
            "arbitrary_execution_exception",
            "FAILURE_COMMAND_JOURNAL_EXECUTION_ERROR_CLASS_INVALID",
        ),
    ],
)
def test_builder_unreachable_receipt_states_fail_closed(
    tmp_path,
    monkeypatch,
    case,
    expected_error,
):
    module = load_notebook()

    def mutate(receipt):
        state = receipt["attempt_state_before_failure_receipt_commit"]
        if case == "outer_nonzero_detail_none":
            receipt["error_detail"] = None
        elif case == "nonzero_capture_incomplete":
            for stream in state["command_journal"][1][
                "failure_diagnostics"
            ].values():
                stream["capture_complete_through_process_termination"] = False
        elif case == "stream_completeness_diverged":
            state["command_journal"][1]["failure_diagnostics"]["stderr"][
                "capture_complete_through_process_termination"
            ] = False
        elif case == "captured_counter_over_bound":
            stream = state["command_journal"][1]["failure_diagnostics"][
                "stderr"
            ]
            stream["captured_byte_count"] = 16_777_217
            stream["observed_byte_count_before_termination"] = (
                16_777_217
            )
        elif case in {
            "returncode_above_posix_exit_domain",
            "returncode_below_linux_signal_domain",
        }:
            entry = state["command_journal"][1]
            entry["returncode"] = (
                256
                if case == "returncode_above_posix_exit_domain"
                else -65
            )
            receipt["error_detail"] = (
                "download_bootstrap_pip_wheel:returncode="
                + str(entry["returncode"])
            )
        elif case == "popen_os_error_has_nonempty_capture":
            convert_failed_entry_to_exception(
                receipt, "PermissionError", capture_complete=False
            )
        elif case == "timeout_capture_incomplete":
            convert_failed_entry_to_exception(
                receipt, "TimeoutExpired", capture_complete=False
            )
        elif case == "candidate_error_capture_complete":
            convert_failed_entry_to_exception(
                receipt,
                "TOOL_OUTPUT_READER_DID_NOT_QUIESCE",
                capture_complete=True,
            )
        elif case == "overflow_stream_not_at_limit":
            convert_failed_entry_to_exception(
                receipt,
                "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
                "stderr",
                capture_complete=False,
            )
        elif case == "reader_error_detail_not_identifier":
            convert_failed_entry_to_exception(
                receipt,
                "TOOL_OUTPUT_READER_FAILED",
                "stderr:RuntimeError:EXTRA",
                capture_complete=False,
            )
        elif case == "supervisor_error_detail_not_identifier":
            convert_failed_entry_to_exception(
                receipt,
                "TOOL_SUBPROCESS_SUPERVISOR_FAILED",
                "RuntimeError:EXTRA",
                capture_complete=False,
            )
        elif case == "cleanup_incomplete_without_error":
            state["staging_cleanup_completed"] = False
        elif case == "cleanup_complete_with_error":
            state["staging_cleanup_error"] = "OSError"
        elif case == "cleanup_error_not_identifier":
            state["staging_cleanup_completed"] = False
            state["staging_cleanup_error"] = "OSError:EXTRA"
        elif case == "pip_count_over_bound":
            identity = state["host_pip_identity"]
            identity["pip_payload_file_count"] = 250_001
            identity["pip_payload_hashed_record_count"] = (
                250_001
            )
            identity["pip_payload_unrecorded_bytecode_count"] = 0
        elif case == "pip_declared_file_count_under_three":
            identity = state["host_pip_identity"]
            identity["pip_payload_file_count"] = 2
            identity["pip_payload_hashed_record_count"] = 1
            identity["pip_payload_unhashed_record_count"] = 1
            identity["pip_payload_unrecorded_bytecode_count"] = 0
        elif case == "pip_all_files_unrecorded_bytecode":
            identity = state["host_pip_identity"]
            identity["pip_payload_file_count"] = 3
            identity["pip_payload_hashed_record_count"] = 0
            identity["pip_payload_unhashed_record_count"] = 0
            identity["pip_payload_unrecorded_bytecode_count"] = 3
        elif case == "pip_control_size_over_bound":
            state["host_pip_identity"]["pip_module_file_size_bytes"] = (
                16_777_217
            )
        elif case == "pip_path_noncanonical":
            state["host_pip_identity"]["path_projection"][
                "pip_distribution_root_relative_to_install_prefix"
            ] = "lib//python3.12/site-packages"
        elif case == "pip_path_unrelated":
            state["host_pip_identity"]["path_projection"][
                "pip_module_file_relative_to_install_prefix"
            ] = "lib/python3.12/site-packages/unrelated/module.py"
        elif case in {
            "bootstrap_wheel_over_bound",
            "bootstrap_central_count_under_payload",
            "bootstrap_payload_count_under_three",
            "bootstrap_central_size_below_header_floor",
            "bootstrap_central_offset_below_local_header_floor",
            "bootstrap_central_missing_trailer_space",
            "bootstrap_nonzip64_entry_count_overflow",
            "bootstrap_lock_not_derived",
        }:
            state = promote_to_bootstrap_install_failure(module, receipt)
            if case == "bootstrap_wheel_over_bound":
                state["bootstrap_pip_wheel_binding"]["size_bytes"] = (
                    4_294_967_297
                )
            elif case == "bootstrap_central_count_under_payload":
                state["bootstrap_pip_wheel_binding"]["central_directory"][
                    "entry_count"
                ] = 9
            elif case == "bootstrap_payload_count_under_three":
                state["bootstrap_pip_wheel_binding"][
                    "embedded_payload_file_count"
                ] = 2
            elif case == "bootstrap_central_size_below_header_floor":
                state["bootstrap_pip_wheel_binding"]["central_directory"][
                    "size_bytes"
                ] = 459
            elif case == "bootstrap_central_offset_below_local_header_floor":
                state["bootstrap_pip_wheel_binding"]["central_directory"][
                    "offset_bytes"
                ] = 309
            elif case == "bootstrap_central_missing_trailer_space":
                state["bootstrap_pip_wheel_binding"]["size_bytes"] = 91_000
            elif case == "bootstrap_nonzip64_entry_count_overflow":
                wheel = state["bootstrap_pip_wheel_binding"]
                wheel["size_bytes"] = 4_000_000
                wheel["central_directory"] = {
                    "entry_count": 0xFFFF,
                    "size_bytes": 46 * 0xFFFF,
                    "offset_bytes": 500_000,
                    "zip64": False,
                }
            else:
                state["bootstrap_pip_lock_binding"]["sha256"] = "9" * 64
        elif case == "arbitrary_execution_exception":
            receipt["error_code"] = "INVENTED_ERROR"
            receipt["error_detail"] = (
                "download_bootstrap_pip_wheel:INVENTED_ERROR"
            )
            entry = state["command_journal"][1]
            entry["returncode"] = None
            entry["execution_error"] = "INVENTED_ERROR"
            entry["execution_error_detail"] = None
            entry.pop("output_excluded_as_nondeterministic_tool_telemetry")
            for stream in entry["failure_diagnostics"].values():
                stream["capture_complete_through_process_termination"] = False
        else:
            raise AssertionError(case)

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert expected_error in result["validation_errors"]
    assert "diagnosis" not in result
    assert_no_authority(result)


def test_isolated_pip_identity_cannot_report_python_outside_prefix():
    module = load_notebook()
    identity = synthetic_pip_identity("ISOLATED_BUILD_VENV")
    identity["python_executable_relationship"] = (
        "RESOLVED_TARGET_OUTSIDE_INSTALL_PREFIX"
    )
    errors = []

    module.validate_portable_pip_identity(
        identity,
        "ISOLATED_BUILD_VENV",
        errors,
        "FAILURE_ISOLATED_PIP_IDENTITY",
    )

    assert "FAILURE_ISOLATED_PIP_IDENTITY_EXECUTABLE_RELATIONSHIP_INVALID" in errors


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        (
            "non_boolean_phase",
            "FAILURE_ATTEMPT_STATE_BOOLEAN_INVALID:network_contact_begun",
        ),
        ("negative_count", "FAILURE_CONFIRMED_LEAF_COUNT_INVALID"),
        (
            "zero_readback",
            "FAILURE_CONFIRMED_BINDING_READBACK_COUNT_INVALID",
        ),
        (
            "float_readback",
            "FAILURE_CONFIRMED_BINDING_READBACK_COUNT_INVALID",
        ),
        ("float_intent_size", "FAILURE_STATE_INTENT_SIZE_MISMATCH"),
        ("float_last_size", "FAILURE_LAST_LEAF_EXPECTED_SIZE_MISMATCH"),
        (
            "float_tail_limit",
            "FAILURE_DIAGNOSTIC_TAIL_LIMIT_INVALID",
        ),
        (
            "empty_capture_with_tail",
            "FAILURE_DIAGNOSTIC_EMPTY_CAPTURE_HAS_TAIL",
        ),
        (
            "string_returncode",
            "FAILURE_COMMAND_JOURNAL_RETURNCODE_INVALID",
        ),
        (
            "bad_diagnostic_sha256",
            "FAILURE_DIAGNOSTIC_CAPTURE_SHA256_INVALID",
        ),
        (
            "missing_required_state",
            "FAILURE_ATTEMPT_STATE_REQUIRED_KEY_MISSING:intent_create_begun",
        ),
        (
            "last_leaf_mismatch",
            "FAILURE_LAST_LEAF_CREATE_NAME_MISMATCH",
        ),
        ("unsafe_error_code", "FAILURE_ERROR_CODE_INVALID"),
        (
            "resolution_without_network",
            "FAILURE_ATTEMPT_STATE_NETWORK_RESOLUTION_DIVERGED",
        ),
        (
            "cleanup_completed_without_begin",
            "FAILURE_ATTEMPT_STATE_CAUSALITY_INVALID:"
            "staging_cleanup_completed_REQUIRES_staging_cleanup_begun",
        ),
        (
            "publish_without_overlay",
            "FAILURE_ATTEMPT_STATE_CAUSALITY_INVALID:"
            "managed_uc_payload_publish_begun_REQUIRES_overlay_install_begun",
        ),
        (
            "bootstrap_build_diverged",
            "FAILURE_ATTEMPT_STATE_BOOTSTRAP_BUILD_FLAGS_DIVERGED",
        ),
        (
            "tool_error_without_journal",
            "FAILURE_COMMAND_JOURNAL_EXACT_NONEMPTY_PREFIX_REQUIRED",
        ),
        (
            "failed_step_mismatch",
            "FAILURE_COMMAND_JOURNAL_FAILED_STEP_MISMATCH",
        ),
        (
            "arbitrary_journal_step",
            "FAILURE_COMMAND_JOURNAL_STEP_PREFIX_MISMATCH",
        ),
        (
            "failed_step_marked_completed",
            "FAILURE_COMMAND_JOURNAL_LAST_COMPLETED_STEP_MISMATCH",
        ),
        (
            "extra_state_key",
            "FAILURE_ATTEMPT_STATE_UNEXPECTED_KEYS",
        ),
        (
            "extra_create_call",
            "FAILURE_EXCLUSIVE_CREATE_CALL_COUNT_INVALID",
        ),
        (
            "arbitrary_host_pip_identity",
            "FAILURE_HOST_PIP_IDENTITY_SHAPE_INVALID",
        ),
        (
            "arbitrary_argv",
            "FAILURE_COMMAND_JOURNAL_ARGV_BINDING_MISMATCH",
        ),
        (
            "nonzero_with_exception_field",
            "FAILURE_COMMAND_JOURNAL_FAILURE_SHAPE_INVALID",
        ),
        (
            "bootstrap_without_bindings",
            "FAILURE_ATTEMPT_STATE_REQUIRED_MAPPING_MISSING:"
            "bootstrap_pip_wheel_binding",
        ),
    ],
)
def test_malformed_failure_state_is_fail_closed(
    tmp_path,
    monkeypatch,
    case,
    expected_error,
):
    module = load_notebook()

    def mutate(receipt):
        state = receipt["attempt_state_before_failure_receipt_commit"]
        if case == "non_boolean_phase":
            state["network_contact_begun"] = "NOT_A_BOOLEAN"
        elif case == "negative_count":
            state["managed_uc_confirmed_leaf_count"] = -900
        elif case == "zero_readback":
            state["managed_uc_confirmed_bindings"][0][
                "fresh_readback_count"
            ] = 0
            state["managed_uc_last_confirmed_binding"][
                "fresh_readback_count"
            ] = 0
        elif case == "float_readback":
            state["managed_uc_confirmed_bindings"][0][
                "fresh_readback_count"
            ] = 2.0
            state["managed_uc_last_confirmed_binding"][
                "fresh_readback_count"
            ] = 2.0
        elif case == "float_intent_size":
            state["durable_intent_expected_size_bytes"] = float(
                state["durable_intent_expected_size_bytes"]
            )
        elif case == "float_last_size":
            state["managed_uc_last_leaf_expected_size_bytes"] = float(
                state["managed_uc_last_leaf_expected_size_bytes"]
            )
        elif case == "float_tail_limit":
            state["command_journal"][1]["failure_diagnostics"]["stderr"][
                "sanitized_tail_byte_limit"
            ] = 65_536.0
        elif case == "empty_capture_with_tail":
            stream = state["command_journal"][1]["failure_diagnostics"][
                "stdout"
            ]
            stream["sanitized_tail_utf8"] = "not-empty"
        elif case == "string_returncode":
            state["command_journal"][1]["returncode"] = "1"
        elif case == "bad_diagnostic_sha256":
            state["command_journal"][1]["failure_diagnostics"]["stderr"][
                "captured_sha256"
            ] = "not-a-sha256"
        elif case == "missing_required_state":
            del state["intent_create_begun"]
        elif case == "last_leaf_mismatch":
            state["managed_uc_last_leaf_create_begun"] = (
                module.PAYLOAD_MANIFEST_LEAF_NAME
            )
        elif case == "unsafe_error_code":
            receipt["error_code"] = "unsafe code\n"
        elif case == "resolution_without_network":
            state["network_contact_begun"] = False
            state["package_resolution_begun"] = True
        elif case == "cleanup_completed_without_begin":
            state["staging_cleanup_begun"] = False
            state["staging_cleanup_completed"] = True
        elif case == "publish_without_overlay":
            state["managed_uc_payload_publish_begun"] = True
            state["overlay_install_begun"] = False
        elif case == "bootstrap_build_diverged":
            state["bootstrap_pip_install_begun"] = True
            state["build_tool_install_begun"] = False
        elif case == "tool_error_without_journal":
            state["command_journal"] = []
        elif case == "failed_step_mismatch":
            state["last_failed_step"] = "different_safe_stage"
        elif case == "arbitrary_journal_step":
            state["command_journal"][1]["step"] = "invented_tool_step"
            state["last_started_step"] = "invented_tool_step"
            state["last_failed_step"] = "invented_tool_step"
        elif case == "failed_step_marked_completed":
            state["last_completed_step"] = state["last_failed_step"]
        elif case == "extra_state_key":
            state["invented_state"] = False
        elif case == "extra_create_call":
            state["managed_uc_exclusive_create_calls_begun"] = 2
        elif case == "arbitrary_host_pip_identity":
            state["host_pip_identity"] = {"arbitrary": True}
        elif case == "arbitrary_argv":
            state["command_journal"][1]["argv"] = [
                "not-the-builder-command"
            ]
        elif case == "nonzero_with_exception_field":
            state["command_journal"][1]["execution_error_detail"] = "extra"
        elif case == "bootstrap_without_bindings":
            failed_entry = state["command_journal"].pop()
            state["command_journal"].append(
                {
                    "step": "download_bootstrap_pip_wheel",
                    "argv": ["<python>", "-m", "pip"],
                    "returncode": 0,
                    "stdout_and_stderr_persisted": False,
                    "output_excluded_as_nondeterministic_tool_telemetry": True,
                }
            )
            state["command_journal"].append(
                {
                    "step": "rebind_host_pip_identity_before_target_install",
                    "argv": [
                        "<HOST_PYTHON>",
                        "-I",
                        "-B",
                        "-c",
                        "<pip-identity-probe>",
                    ],
                    "returncode": 0,
                    "stdout_and_stderr_persisted": False,
                    "output_excluded_as_nondeterministic_tool_telemetry": True,
                }
            )
            failed_entry["step"] = "bootstrap_pip_into_isolated_venv"
            state["command_journal"].append(failed_entry)
            state["last_started_step"] = failed_entry["step"]
            state["last_failed_step"] = failed_entry["step"]
            state["last_completed_step"] = (
                "rebind_host_pip_identity_before_target_install"
            )
            state[
                "host_pip_identity_reverified_before_target_install"
            ] = True
            state["bootstrap_pip_install_begun"] = True
            state["build_tool_install_begun"] = True
        else:
            raise AssertionError(case)

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert expected_error in result["validation_errors"]
    assert "diagnosis" not in result
    assert_no_authority(result)


def test_flat_virtual_prefix_absent_and_unrelated_parent_files_are_ignored(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    unrelated = tmp_path / "unrelated-secret.bin"
    unrelated.write_bytes(b"must never be opened")
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert not (tmp_path / module.CANDIDATE_ID).exists()
    assert str(unrelated) not in opened
    assert unrelated.name not in opened
    assert "scandir" not in NOTEBOOK.read_text()


def test_control_leaf_opens_are_read_only_nofollow_and_nonblocking(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    observed = []
    original_open = module.os.open

    def recording_open(path, flags, *args, **kwargs):
        if kwargs.get("dir_fd") is not None:
            observed.append((os.fspath(path), flags))
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert len(observed) == 4
    for name, flags in observed:
        assert name in module.CONTROL_LEAF_NAMES
        assert flags & module.os.O_NOFOLLOW
        assert flags & module.os.O_NONBLOCK
        assert not flags & module.os.O_WRONLY
        assert not flags & module.os.O_RDWR


@pytest.mark.parametrize("present", [(), ("intent",), ("failure",)])
def test_incomplete_control_pair_holds_without_trusted_diagnosis(
    tmp_path,
    monkeypatch,
    present,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    intent, intent_raw = synthetic_intent(module)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw))
    monkeypatch.setattr(
        module, "EXPECTED_INTENT_RECORD_SHA256", intent["record_sha256"]
    )
    _, failure_raw = synthetic_failure(module, intent_raw)
    if "intent" in present:
        (tmp_path / module.INTENT_LEAF_NAME).write_bytes(intent_raw)
    if "failure" in present:
        (tmp_path / module.FAILURE_RECEIPT_LEAF_NAME).write_bytes(failure_raw)

    result = module.capture_candidate()

    assert result["decision"] == "HOLD_EXPECTED_CONTROL_PAIR_INCOMPLETE"
    assert "diagnosis" not in result
    assert result["construction_or_reuse_authorized"] is False
    assert result["candidate_004_authorized"] is False
    assert result["candidate_disposition"] == (
        "SPENT_NOT_ESTABLISHED_BY_THIS_CAPTURE"
        if not present
        else "PERMANENTLY_SPENT_UNRESOLVED"
    )


@pytest.mark.parametrize("extra_kind", ["payload", "manifest"])
def test_partial_payload_metadata_holds_and_payload_is_never_opened(
    tmp_path,
    monkeypatch,
    extra_kind,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    extra_name = (
        f"{module.CANDIDATE_ID}.payload-0000.bin"
        if extra_kind == "payload"
        else module.PAYLOAD_MANIFEST_LEAF_NAME
    )
    (tmp_path / extra_name).write_bytes(b"never-open-this-payload")
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"] == (
        "HOLD_PARTIAL_CANDIDATE_NAMESPACE_REVIEW_REQUIRED"
    )
    assert extra_name not in opened
    assert result["safety"][
        "unexpected_or_payload_leaf_payload_opened_or_read"
    ] is False


def test_success_receipt_visibility_is_terminal_ambiguity_and_not_read(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    success = tmp_path / module.SUCCESS_RECEIPT_LEAF_NAME
    success.write_bytes(b"never-open-success")
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"] == "HOLD_TERMINAL_RECEIPT_AMBIGUITY"
    assert module.SUCCESS_RECEIPT_LEAF_NAME not in opened
    assert "diagnosis" not in result


def test_virtual_prefix_directory_is_hold_and_never_traversed(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    virtual = tmp_path / module.CANDIDATE_ID
    virtual.mkdir()
    (virtual / "do-not-read").write_bytes(b"secret")

    result = module.capture_candidate()

    assert result["decision"] == "HOLD_VIRTUAL_CANDIDATE_PREFIX_NOT_ABSENT"
    assert result["snapshot_projections"][0][
        "virtual_candidate_prefix"
    ]["kind"] == "DIRECTORY"


@pytest.mark.parametrize("control_name", ["intent", "failure"])
def test_nonregular_control_is_never_opened_and_holds(
    tmp_path,
    monkeypatch,
    control_name,
):
    module = load_notebook()
    intent_path, failure_path, _, _ = write_valid_pair(
        module, monkeypatch, tmp_path
    )
    target = intent_path if control_name == "intent" else failure_path
    target.unlink()
    external = tmp_path / (control_name + "-external")
    external.write_bytes(b"must not be followed")
    target.symlink_to(external)
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"] == "HOLD_ALLOWLISTED_CONTROL_LEAF_UNREAD"
    assert target.name not in opened
    assert_no_authority(result)


@pytest.mark.parametrize("control_name", ["intent", "failure"])
def test_oversize_control_is_refused_before_open(
    tmp_path,
    monkeypatch,
    control_name,
):
    module = load_notebook()
    intent_path, failure_path, _, _ = write_valid_pair(
        module, monkeypatch, tmp_path
    )
    target = intent_path if control_name == "intent" else failure_path
    monkeypatch.setattr(module, "MAX_CONTROL_LEAF_BYTES", 4)
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_candidate()

    assert result["decision"] == "HOLD_ALLOWLISTED_CONTROL_LEAF_UNREAD"
    assert target.name not in opened
    assert_no_authority(result)


def test_control_growth_after_pre_stat_fails_closed(tmp_path, monkeypatch):
    module = load_notebook()
    intent_path, _, _, _ = write_valid_pair(module, monkeypatch, tmp_path)
    original_open = module.os.open
    changed = False

    def growing_open(path, *args, **kwargs):
        nonlocal changed
        if (
            not changed
            and os.fspath(path) == module.INTENT_LEAF_NAME
            and kwargs.get("dir_fd") is not None
        ):
            intent_path.write_bytes(intent_path.read_bytes() + b" ")
            changed = True
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", growing_open)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["candidate_disposition"] == "PERMANENTLY_SPENT_UNRESOLVED"
    assert_no_authority(result)


def test_post_stat_symlink_swap_fails_closed_without_read(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    intent_path, _, _, _ = write_valid_pair(module, monkeypatch, tmp_path)
    external = tmp_path / "external-secret"
    external.write_bytes(b"must-never-be-read")
    original_open = module.os.open
    original_read = module.os.read
    read_calls = []
    swapped = False

    def swapping_open(path, *args, **kwargs):
        nonlocal swapped
        if (
            not swapped
            and os.fspath(path) == module.INTENT_LEAF_NAME
            and kwargs.get("dir_fd") is not None
        ):
            intent_path.unlink()
            intent_path.symlink_to(external)
            swapped = True
        return original_open(path, *args, **kwargs)

    def recording_read(*args, **kwargs):
        read_calls.append(True)
        return original_read(*args, **kwargs)

    monkeypatch.setattr(module.os, "open", swapping_open)
    monkeypatch.setattr(module.os, "read", recording_read)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert read_calls == []
    assert_no_authority(result)


def test_namespace_change_within_snapshot_fails_closed(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    payload = tmp_path / f"{module.CANDIDATE_ID}.payload-0000.bin"
    original_projection = module.namespace_projection
    calls = 0

    def changing_projection(descriptor, observation_state):
        nonlocal calls
        projection = original_projection(descriptor, observation_state)
        calls += 1
        if calls == 1:
            payload.write_bytes(b"do-not-open")
        return projection

    monkeypatch.setattr(module, "namespace_projection", changing_projection)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["safety"][
        "unexpected_or_payload_leaf_payload_opened_or_read"
    ] is False
    assert_no_authority(result)


def test_visible_intent_is_latched_when_later_before_stat_fails(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    original_stat = module.os.stat
    late_name = f"{module.CANDIDATE_ID}.payload-0001.bin"

    def fail_after_intent(path, *args, **kwargs):
        if os.fspath(path) == late_name and kwargs.get("dir_fd") is not None:
            raise PermissionError("late reserved stat denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", fail_after_intent)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["candidate_disposition"] == "PERMANENTLY_SPENT_UNRESOLVED"
    assert_no_authority(result)


def test_payload_appearing_in_after_projection_is_latched_before_mismatch(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    original_stat_relative = module.stat_relative
    projection_ordinal = 0
    payload_name = f"{module.CANDIDATE_ID}.payload-0000.bin"

    def appearing_stat(descriptor, name, observation_state):
        nonlocal projection_ordinal
        if name == module.CANDIDATE_ID:
            projection_ordinal += 1
        if projection_ordinal == 2 and name == payload_name:
            (tmp_path / payload_name).write_bytes(b"visible-but-never-read")
        return original_stat_relative(descriptor, name, observation_state)

    monkeypatch.setattr(module, "stat_relative", appearing_stat)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["candidate_disposition"] == "PERMANENTLY_SPENT_UNRESOLVED"
    assert result["safety"][
        "unexpected_or_payload_leaf_payload_opened_or_read"
    ] is False
    assert_no_authority(result)


def test_change_between_snapshots_is_nonrepeatable_hold(tmp_path, monkeypatch):
    module = load_notebook()
    _, failure_path, _, _ = write_valid_pair(module, monkeypatch, tmp_path)
    original_snapshot = module.snapshot

    def changing_snapshot(ordinal, state):
        result = original_snapshot(ordinal, state)
        if ordinal == 1:
            failure_path.write_bytes(failure_path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(module, "snapshot", changing_snapshot)
    result = module.capture_candidate()

    assert result["decision"] == "HOLD_FORENSIC_PATH_SNAPSHOTS_NOT_REPEATABLE"
    assert "diagnosis" not in result
    assert_no_authority(result)


def test_same_size_content_change_between_snapshots_holds(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    _, failure_path, _, _ = write_valid_pair(module, monkeypatch, tmp_path)
    original_snapshot = module.snapshot

    def changing_snapshot(ordinal, state):
        result = original_snapshot(ordinal, state)
        if ordinal == 1:
            raw = bytearray(failure_path.read_bytes())
            raw[-2] = ord(" ") if raw[-2] != ord(" ") else ord("x")
            failure_path.write_bytes(bytes(raw))
        return result

    monkeypatch.setattr(module, "snapshot", changing_snapshot)
    result = module.capture_candidate()

    assert result["decision"] == "HOLD_FORENSIC_PATH_SNAPSHOTS_NOT_REPEATABLE"
    assert "diagnosis" not in result
    assert_no_authority(result)


@pytest.mark.parametrize(
    "bad_payload",
    [
        b'{"a":1,"a":2}\n',
        b'{"a":NaN}\n',
        b'{ "a":1}\n',
        b'{"a":1}\n\n',
        b"\xff",
    ],
)
def test_strict_json_rejects_duplicates_nonfinite_and_noncanonical_bytes(
    bad_payload,
):
    module = load_notebook()

    with pytest.raises(RuntimeError):
        module.parse_canonical_ascii_json(bad_payload, "CONTROL")


def test_receipt_intent_binding_mismatch_holds(tmp_path, monkeypatch):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    intent, intent_raw = synthetic_intent(module)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw))
    monkeypatch.setattr(
        module, "EXPECTED_INTENT_RECORD_SHA256", intent["record_sha256"]
    )
    _, failure_raw = synthetic_failure(
        module,
        intent_raw,
        attempt_intent_sha256="0" * 64,
    )
    (tmp_path / module.INTENT_LEAF_NAME).write_bytes(intent_raw)
    (tmp_path / module.FAILURE_RECEIPT_LEAF_NAME).write_bytes(failure_raw)

    result = module.capture_candidate()

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert "FAILURE_RECEIPT_INTENT_BINDING_MISMATCH" in result[
        "validation_errors"
    ]
    assert "diagnosis" not in result
    assert_no_authority(result)


def test_intent_semantic_mutation_holds_even_when_raw_expectation_is_adjusted(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    intent, _ = synthetic_intent(module)
    intent["state"] = "WRONG_STATE"
    projection = dict(intent)
    projection.pop("record_sha256")
    intent["record_sha256"] = sha256(
        module.ATTEMPT_INTENT_DOMAIN + independent_canonical(projection)
    )
    intent_raw = independent_canonical(intent) + b"\n"
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_raw))
    monkeypatch.setattr(module, "EXPECTED_INTENT_FILE_SHA256", sha256(intent_raw))
    monkeypatch.setattr(
        module, "EXPECTED_INTENT_RECORD_SHA256", intent["record_sha256"]
    )
    _, failure_raw = synthetic_failure(module, intent_raw)
    (tmp_path / module.INTENT_LEAF_NAME).write_bytes(intent_raw)
    (tmp_path / module.FAILURE_RECEIPT_LEAF_NAME).write_bytes(failure_raw)

    result = module.capture_candidate()

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert "INTENT_STATE_MISMATCH" in result["validation_errors"]
    assert_no_authority(result)


def test_permission_error_is_failure_not_absence(tmp_path, monkeypatch):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    original_stat = module.os.stat

    def denied(path, *args, **kwargs):
        if os.fspath(path) == module.INTENT_LEAF_NAME:
            raise PermissionError("denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", denied)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["error_type_binding"]["sha256"] == sha256(
        b"PermissionError"
    )
    assert_no_authority(result)


def test_parent_symlink_is_rejected_before_control_read(tmp_path, monkeypatch):
    module = load_notebook()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    configure_fixture_target(module, monkeypatch, alias)

    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["error_detail_binding"]["sha256"] == sha256(
        b"EXACT_PARENT_NOT_NONSYMLINK_DIRECTORY"
    )
    assert result["safety"][
        "control_payload_read_syscall_completed"
    ] is False
    assert result["safety"][
        "databricks_managed_storage_io_may_have_been_performed"
    ] is True
    assert result["safety"]["parent_descriptor_open_completed_count"] == 0
    assert result["safety"]["applies_only_to_this_forensic_run"] is True
    assert_no_authority(result)


def test_failed_parent_fstat_conservatively_reports_managed_io_may_have_occurred(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)

    def denied_fstat(_descriptor):
        raise PermissionError("fstat denied")

    monkeypatch.setattr(module.os, "fstat", denied_fstat)
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["safety"]["databricks_managed_storage_io_attempted"] is True
    assert result["safety"][
        "databricks_managed_storage_io_may_have_been_performed"
    ] is True
    assert result["safety"]["parent_descriptor_open_completed_count"] == 1
    assert_no_authority(result)


def test_zero_byte_control_read_reports_completed_read_syscall(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    (tmp_path / module.INTENT_LEAF_NAME).write_bytes(b"")
    state = {
        "reserved_path_visibility_observed": False,
        "control_payload_open_may_have_begun": False,
        "control_payload_read_syscall_may_have_begun": False,
        "control_payload_read_syscall_completed": False,
        "positive_control_payload_bytes_observed": False,
        "control_payload_bytes_read_total": 0,
        "control_payload_reads_completed": 0,
    }
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        before = module.stat_relative(
            descriptor, module.INTENT_LEAF_NAME, state
        )
        payload, binding = module.read_control_leaf(
            descriptor, module.INTENT_LEAF_NAME, before, state
        )
    finally:
        os.close(descriptor)

    assert payload == b""
    assert binding["payload_read"] is True
    assert state["control_payload_open_may_have_begun"] is True
    assert state["control_payload_read_syscall_may_have_begun"] is True
    assert state["control_payload_read_syscall_completed"] is True
    assert state["positive_control_payload_bytes_observed"] is False
    assert state["control_payload_bytes_read_total"] == 0
    assert state["control_payload_reads_completed"] == 1


def test_positive_read_is_ledgered_before_payload_extension_failure(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    configure_fixture_target(module, monkeypatch, tmp_path)
    payload = b"positive forensic bytes"
    (tmp_path / module.INTENT_LEAF_NAME).write_bytes(payload)
    state = {
        "reserved_path_visibility_observed": False,
        "control_payload_open_may_have_begun": False,
        "control_payload_read_syscall_may_have_begun": False,
        "control_payload_read_syscall_completed": False,
        "positive_control_payload_bytes_observed": False,
        "control_payload_bytes_read_total": 0,
        "control_payload_reads_completed": 0,
    }

    class FailingBytearray(bytearray):
        def extend(self, _chunk):
            raise MemoryError("forced extension failure")

    monkeypatch.setattr(module, "bytearray", FailingBytearray, raising=False)
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        before = module.stat_relative(
            descriptor, module.INTENT_LEAF_NAME, state
        )
        with pytest.raises(MemoryError, match="forced extension failure"):
            module.read_control_leaf(
                descriptor, module.INTENT_LEAF_NAME, before, state
            )
    finally:
        os.close(descriptor)

    assert state["control_payload_open_may_have_begun"] is True
    assert state["control_payload_read_syscall_may_have_begun"] is True
    assert state["control_payload_read_syscall_completed"] is True
    assert state["positive_control_payload_bytes_observed"] is True
    assert state["control_payload_bytes_read_total"] == len(payload)
    assert state["control_payload_reads_completed"] == 0


def test_payload_allocation_failure_closes_leaf_and_parent_descriptors(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)
    opened = []
    closed = []
    original_open = module.os.open
    original_close = module.os.close

    def recording_open(path, flags, *args, **kwargs):
        descriptor = original_open(path, flags, *args, **kwargs)
        opened.append(
            (os.fspath(path), descriptor, kwargs.get("dir_fd"))
        )
        return descriptor

    def recording_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    def failing_bytearray():
        raise MemoryError("forced payload allocation failure")

    monkeypatch.setattr(module.os, "open", recording_open)
    monkeypatch.setattr(module.os, "close", recording_close)
    monkeypatch.setattr(module, "bytearray", failing_bytearray, raising=False)

    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["error_type_binding"]["sha256"] == sha256(b"MemoryError")
    assert len(opened) == 2
    parent_path, parent_descriptor, parent_dir_fd = opened[0]
    leaf_name, leaf_descriptor, leaf_dir_fd = opened[1]
    assert parent_path == os.fspath(tmp_path)
    assert parent_dir_fd is None
    assert leaf_name == module.INTENT_LEAF_NAME
    assert leaf_dir_fd == parent_descriptor
    assert leaf_descriptor != parent_descriptor
    assert closed == [leaf_descriptor, parent_descriptor]
    assert result["safety"]["parent_descriptor_open_completed_count"] == 1
    assert result["safety"]["control_payload_open_may_have_begun"] is True
    assert result["safety"]["control_payload_read_syscall_may_have_begun"] is False
    assert_no_authority(result)


def test_public_failure_never_republishes_exception_text(monkeypatch):
    module = load_notebook()
    secret = "AWSSECRETACCESSKEY_RUNTIME_ABC123"

    def fail_contract():
        raise OSError(secret)

    monkeypatch.setattr(module, "validate_frozen_contract", fail_contract)
    result = module.capture_candidate()

    serialized = json.dumps(result, sort_keys=True)
    assert secret not in serialized
    assert result["error_type_binding"]["sha256"] == sha256(b"OSError")
    assert result["error_detail_binding"]["sha256"] == sha256(
        secret.encode()
    )
    assert_no_authority(result)


@pytest.mark.parametrize(
    "feature", ["O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK"]
)
def test_missing_os_open_flag_fails_closed_before_observation(
    monkeypatch,
    feature,
):
    module = load_notebook()
    monkeypatch.delattr(module.os, feature)

    with pytest.raises(
        RuntimeError,
        match="REQUIRED_OS_FEATURE_UNAVAILABLE:" + feature,
    ):
        module.validate_frozen_contract()


@pytest.mark.parametrize(
    ("capability", "expected"),
    [
        ("open_dir_fd", "OS_OPEN_DIR_FD_UNSUPPORTED"),
        ("stat_dir_fd", "OS_STAT_DIR_FD_UNSUPPORTED"),
        ("stat_nofollow", "OS_STAT_NOFOLLOW_UNSUPPORTED"),
    ],
)
def test_missing_os_capability_fails_closed_before_observation(
    monkeypatch,
    capability,
    expected,
):
    module = load_notebook()
    if capability == "open_dir_fd":
        monkeypatch.setattr(
            module.os,
            "supports_dir_fd",
            set(module.os.supports_dir_fd) - {module.os.open},
        )
    elif capability == "stat_dir_fd":
        monkeypatch.setattr(
            module.os,
            "supports_dir_fd",
            set(module.os.supports_dir_fd) - {module.os.stat},
        )
    else:
        monkeypatch.setattr(
            module.os,
            "supports_follow_symlinks",
            set(module.os.supports_follow_symlinks) - {module.os.stat},
        )

    with pytest.raises(RuntimeError, match=expected):
        module.validate_frozen_contract()


def test_source_has_no_mutating_network_subprocess_widget_or_spark_surface():
    source = NOTEBOOK.read_text()
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert imported_roots == {"hashlib", "json", "os", "stat"}
    assert all(
        alias.asname is None
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree))

    defined_functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    allowed_bare_calls = defined_functions | {
        "RuntimeError",
        "ValueError",
        "all",
        "any",
        "bool",
        "bytearray",
        "bytes",
        "dict",
        "enumerate",
        "hasattr",
        "len",
        "list",
        "min",
        "print",
        "range",
        "set",
        "sorted",
        "str",
        "sum",
        "type",
        "zip",
    }
    bare_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert bare_calls <= allowed_bare_calls

    def attribute_root(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    module_calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and attribute_root(node.func) in imported_roots
    }
    assert module_calls == {
        "hashlib.sha256",
        "json.dumps",
        "json.loads",
        "os.close",
        "os.fstat",
        "os.lstat",
        "os.open",
        "os.read",
        "os.stat",
        "stat.S_ISBLK",
        "stat.S_ISCHR",
        "stat.S_ISDIR",
        "stat.S_ISFIFO",
        "stat.S_ISLNK",
        "stat.S_ISREG",
        "stat.S_ISSOCK",
    }
    nonmodule_method_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and attribute_root(node.func) not in imported_roots
    }
    assert nonmodule_method_calls == {
        "append",
        "count",
        "decode",
        "encode",
        "endswith",
        "extend",
        "get",
        "hexdigest",
        "isalnum",
        "isascii",
        "isidentifier",
        "issubset",
        "items",
        "pop",
        "split",
        "startswith",
        "values",
    }
    referenced_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    assert "dbutils" not in referenced_names
    assert "subprocess" not in referenced_names
    assert "socket" not in referenced_names
    assert "requests" not in referenced_names
    assert "urllib" not in referenced_names
    assert "scandir" not in source
    assert "O_WRONLY" not in source
    assert "O_RDWR" not in source
    assert "O_CREAT" not in source
    assert "O_EXCL" not in source
    for forbidden in (
        "os.write",
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "os.mkdir",
        "os.makedirs",
        "os.rmdir",
        "os.chmod",
        "os.chown",
        "os.fsync",
        "spark.",
    ):
        assert forbidden not in source


def test_reviewed_forensic_notebook_bytes_are_frozen():
    raw = NOTEBOOK.read_bytes()

    assert len(raw) == 93_302
    assert sha256(raw) == (
        "c0ee94d4b09c6ebaffbf686e488bae4a114d6a412e7b528c453a3e3a27f69fb2"
    )


def test_import_is_inert_and_main_has_no_runtime_parameters(monkeypatch):
    module = load_notebook()
    sentinel = {"decision": "SENTINEL"}
    calls = []

    def fake_capture():
        calls.append(True)
        return sentinel

    monkeypatch.setattr(module, "capture_candidate", fake_capture)
    module.main()

    assert calls == [True]


@pytest.mark.parametrize(
    "safety_key",
    [
        "base_runtime_install_target_requested_by_notebook",
        "study_or_test_data_path_requested_by_notebook",
        "spark_operation_requested_by_notebook",
        "databricks_rest_api_requested_by_notebook",
        "scientific_execution_requested_by_notebook",
        "canonical_repository_lock_write_requested_by_notebook",
        "child_process_external_file_access_audited",
        "child_process_side_effects_outside_staging_proven_absent",
    ],
)
@pytest.mark.parametrize("numeric_false", [0, 0.0])
def test_failure_safety_rejects_numeric_false_coercion(
    tmp_path,
    monkeypatch,
    safety_key,
    numeric_false,
):
    module = load_notebook()

    def mutate(receipt):
        receipt["safety"][safety_key] = numeric_false

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert "FAILURE_SAFETY_PROJECTION_MISMATCH" in result[
        "validation_errors"
    ]
    assert_no_authority(result)


@pytest.mark.parametrize(
    "field",
    ["size_bytes", "fresh_readback_count"],
)
def test_last_confirmed_binding_rejects_float_equivalent_integer(
    tmp_path,
    monkeypatch,
    field,
):
    module = load_notebook()

    def mutate(receipt):
        binding = receipt["attempt_state_before_failure_receipt_commit"][
            "managed_uc_last_confirmed_binding"
        ]
        binding[field] = float(binding[field])

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert "FAILURE_LAST_CONFIRMED_BINDING_MISMATCH" in result[
        "validation_errors"
    ]
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_error"),
    [
        (
            "sanitized_tail_utf8",
            "",
            "FAILURE_DIAGNOSTIC_NONEMPTY_CAPTURE_HAS_EMPTY_TAIL",
        ),
        (
            "captured_sha256",
            sha256(b""),
            "FAILURE_DIAGNOSTIC_NONEMPTY_CAPTURE_HAS_EMPTY_SHA256",
        ),
    ],
)
def test_positive_capture_rejects_builder_impossible_empty_binding(
    tmp_path,
    monkeypatch,
    field,
    replacement,
    expected_error,
):
    module = load_notebook()

    def mutate(receipt):
        stream = receipt["attempt_state_before_failure_receipt_commit"][
            "command_journal"
        ][1]["failure_diagnostics"]["stderr"]
        assert stream["captured_byte_count"] == 12
        stream[field] = replacement

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert expected_error in result["validation_errors"]
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("size_bytes", 219),
        ("offset_bytes", 174),
    ],
)
def test_exact_pip_wheel_rejects_below_independent_structural_floor(
    field,
    value,
):
    module = load_notebook()
    wheel = synthetic_bootstrap_wheel()
    wheel["size_bytes"] = 417
    wheel["embedded_payload_file_count"] = 3
    wheel["central_directory"] = {
        "entry_count": 3,
        "size_bytes": 220,
        "offset_bytes": 175,
        "zip64": False,
    }
    wheel["central_directory"][field] = value
    errors = []

    module.validate_bootstrap_wheel_binding(wheel, errors)

    assert "FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID" in errors


def test_exact_pip_wheel_accepts_independent_minimum_structural_summary():
    module = load_notebook()
    wheel = synthetic_bootstrap_wheel()
    wheel["size_bytes"] = 417
    wheel["embedded_payload_file_count"] = 3
    wheel["central_directory"] = {
        "entry_count": 3,
        "size_bytes": 220,
        "offset_bytes": 175,
        "zip64": False,
    }
    errors = []

    module.validate_bootstrap_wheel_binding(wheel, errors)

    assert errors == []


def test_public_failure_reports_completed_snapshot_pair_from_ledger(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    write_valid_pair(module, monkeypatch, tmp_path)

    def fail_after_snapshots(_payload, _intent_sha256):
        raise TypeError("post-snapshot validator failure")

    monkeypatch.setattr(
        module, "validate_failure_receipt", fail_after_snapshots
    )
    result = module.capture_candidate()

    assert result["decision"] == (
        "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED"
    )
    assert result["snapshot_count_completed"] == 2
    assert len(result["completed_projection_sha256s"]) == 2
    assert result["custody_model"][
        "required_snapshot_pair_completed"
    ] is True
    assert result["safety"]["snapshot_pair_completed"] is True
    assert_no_authority(result)


def test_timeout_accepts_one_reader_chunk_of_raced_observed_bytes(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt,
            "TimeoutExpired",
            capture_complete=True,
        )
        stream = entry["failure_diagnostics"]["stderr"]
        stream["observed_byte_count_before_termination"] = (
            stream["captured_byte_count"] + 65_536
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert_no_authority(result)


def test_timeout_rejects_more_than_one_reader_chunk_of_raced_bytes(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt,
            "TimeoutExpired",
            capture_complete=True,
        )
        stream = entry["failure_diagnostics"]["stderr"]
        stream["observed_byte_count_before_termination"] = (
            stream["captured_byte_count"] + 65_537
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert (
        "FAILURE_DIAGNOSTIC_TIMEOUT_COUNT_DELTA_INVALID:stderr"
        in result["validation_errors"]
    )
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("execution_error", "execution_detail", "stream_name"),
    [
        ("TOOL_OUTPUT_READER_FAILED", "stderr:MemoryError", "stdout"),
        ("TOOL_OUTPUT_READER_FAILED", "stderr:MemoryError", "stderr"),
        (
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            "stderr",
            "stdout",
        ),
        (
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            "stderr",
            "stderr",
        ),
    ],
)
def test_quiescent_reader_errors_accept_one_chunk_of_accounting_lag(
    tmp_path,
    monkeypatch,
    execution_error,
    execution_detail,
    stream_name,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt,
            execution_error,
            execution_detail,
            capture_complete=False,
        )
        if execution_error == "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED":
            named = entry["failure_diagnostics"]["stderr"]
            named["captured_byte_count"] = module.MAX_CAPTURED_STREAM_BYTES
            named["observed_byte_count_before_termination"] = (
                module.MAX_CAPTURED_STREAM_BYTES + 1
            )
            named["captured_sha256"] = "a" * 64
            named["sanitized_tail_utf8"] = "bounded overflow"
        stream = entry["failure_diagnostics"][stream_name]
        stream["observed_byte_count_before_termination"] = (
            stream["captured_byte_count"] + module.READ_CHUNK_BYTES
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"].startswith("PASS_READ_ONLY_FORENSIC")
    assert_no_authority(result)


@pytest.mark.parametrize(
    ("execution_error", "execution_detail", "stream_name"),
    [
        ("TOOL_OUTPUT_READER_FAILED", "stderr:MemoryError", "stdout"),
        ("TOOL_OUTPUT_READER_FAILED", "stderr:MemoryError", "stderr"),
        (
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            "stderr",
            "stdout",
        ),
        (
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            "stderr",
            "stderr",
        ),
    ],
)
def test_quiescent_reader_errors_reject_more_than_one_chunk_of_accounting_lag(
    tmp_path,
    monkeypatch,
    execution_error,
    execution_detail,
    stream_name,
):
    module = load_notebook()

    def mutate(receipt):
        entry = convert_failed_entry_to_exception(
            receipt,
            execution_error,
            execution_detail,
            capture_complete=False,
        )
        if execution_error == "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED":
            named = entry["failure_diagnostics"]["stderr"]
            named["captured_byte_count"] = module.MAX_CAPTURED_STREAM_BYTES
            named["observed_byte_count_before_termination"] = (
                module.MAX_CAPTURED_STREAM_BYTES + 1
            )
            named["captured_sha256"] = "a" * 64
            named["sanitized_tail_utf8"] = "bounded overflow"
        stream = entry["failure_diagnostics"][stream_name]
        stream["observed_byte_count_before_termination"] = (
            stream["captured_byte_count"] + module.READ_CHUNK_BYTES + 1
        )

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert (
        "FAILURE_DIAGNOSTIC_QUIESCENT_READER_COUNT_DELTA_INVALID:"
        + stream_name
        in result["validation_errors"]
    )
    assert_no_authority(result)


def test_completed_non_timeout_failure_requires_exact_capture_count(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()

    def mutate(receipt):
        stream = receipt["attempt_state_before_failure_receipt_commit"][
            "command_journal"
        ][1]["failure_diagnostics"]["stderr"]
        stream["observed_byte_count_before_termination"] = 13

    result = capture_with_failure_mutation(
        module, monkeypatch, tmp_path, mutate
    )

    assert result["decision"] == "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
    assert "FAILURE_DIAGNOSTIC_COMPLETE_COUNT_MISMATCH" in result[
        "validation_errors"
    ]
    assert_no_authority(result)
