from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import stat

import pytest

from heterodiff.experiments import b08_databricks_aws_qualification as qualification


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/diagnostics/b08_databricks_aws_qualification_capture_v1.py"
ADMIN_TEMPLATE = (
    ROOT
    / "research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json"
)
SPEC = importlib.util.spec_from_file_location("b08_databricks_capture", SOURCE)
assert SPEC is not None and SPEC.loader is not None
capture_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture_module)


def write_canonical(path: Path, value: object) -> None:
    path.write_bytes(capture_module._canonical_bytes(value) + b"\n")
    path.chmod(0o600)


def valid_inputs(tmp_path: Path):
    cluster = tmp_path / "cluster.json"
    reservation = tmp_path / "reservation.json"
    write_canonical(
        cluster,
        {
            "aws_attributes": {"availability": "ON_DEMAND"},
            "data_security_mode": "SINGLE_USER",
            "node_type_id": "m6i.4xlarge",
            "num_workers": 0,
            "spark_version": "16.4.x-scala2.12",
        },
    )
    write_canonical(
        reservation,
        {
            "admin_record_schema": "b08-aws-admin-storage-reservation-v1",
            "combined_reservation_bytes": 1_133_871_366_144,
            "externally_verified": False,
            "qualification_nonclaim": "INPUT_ONLY_REQUIRES_EXTERNAL_REVIEW",
        },
    )
    return cluster, reservation


def test_admin_storage_input_template_is_canonical_hold_only():
    raw = ADMIN_TEMPLATE.read_bytes()
    value = json.loads(raw.decode("ascii"))
    assert raw == capture_module._canonical_bytes(value) + b"\n"
    assert value["record_state"] == "HOLD_UNPOPULATED_TEMPLATE"
    assert value["externally_verified"] is False
    assert value["project_effects"] == {
        "b08_closed": False,
        "blocker_count_delta": 0,
        "field_count_delta": 0,
        "timetable_checkbox_delta": 0,
    }


def test_capture_allowlist_covers_every_required_deterministic_control(
    monkeypatch,
):
    required = qualification.DETERMINISTIC_ENVIRONMENT_CONTROLS
    assert set(required) <= set(capture_module.DETERMINISM_ENV_ALLOWLIST)
    for name, value in required.items():
        monkeypatch.setenv(name, value)
    captured = capture_module._determinism_environment()
    assert {name: captured["present"][name] for name in required} == required


@pytest.mark.parametrize(
    ("input_mode", "receipt_mode"),
    [
        ("DATA_SECURITY_MODE_DEDICATED", "DEDICATED"),
        ("SINGLE_USER", "SINGLE_USER"),
        ("DEDICATED", "DEDICATED"),
    ],
)
def test_current_and_legacy_dedicated_mode_aliases_are_normalized(
    input_mode, receipt_mode
):
    signals = capture_module._cluster_target_signals(
        {
            "aws_attributes": {"availability": "ON_DEMAND"},
            "data_security_mode": input_mode,
            "node_type_id": "m6i.4xlarge",
            "spark_version": "16.4.x-scala2.12",
        }
    )
    assert signals["dedicated_access_mode"] == receipt_mode


@pytest.mark.parametrize(
    "input_mode",
    [
        "DATA_SECURITY_MODE_AUTO",
        "DATA_SECURITY_MODE_STANDARD",
        "NONE",
        "SHARED",
        "USER_ISOLATION",
    ],
)
def test_non_dedicated_data_security_modes_fail_closed(input_mode):
    with pytest.raises(
        capture_module.CaptureError, match="CLUSTER_DATA_SECURITY_MODE_NOT_DEDICATED"
    ):
        capture_module._cluster_target_signals(
            {
                "aws_attributes": {"availability": "ON_DEMAND"},
                "data_security_mode": input_mode,
                "node_type_id": "m6i.4xlarge",
                "spark_version": "16.4.x-scala2.12",
            }
        )


def test_current_databricks_dedicated_enum_round_trips_without_identity_data(
    tmp_path,
):
    cluster, reservation = valid_inputs(tmp_path)
    cluster_value = json.loads(cluster.read_text(encoding="ascii"))
    cluster_value["data_security_mode"] = "DATA_SECURITY_MODE_DEDICATED"
    write_canonical(cluster, cluster_value)
    output = tmp_path / "current-enum-receipt.json"

    created = capture_module.capture(
        str(cluster), str(reservation), str(output), None
    )
    receipt = json.loads(output.read_text(encoding="ascii"))
    assert receipt["input_captures"]["exported_sanitized_cluster_json"][
        "content"
    ]["data_security_mode"] == "DATA_SECURITY_MODE_DEDICATED"
    assert receipt["cluster_target_signals"]["dedicated_access_mode"] == (
        "DEDICATED"
    )
    assert created["decision"] == (
        "CAPTURE_WRITTEN_REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW"
    )
    capture_module.validate_only(
        str(cluster), str(reservation), str(output), None
    )


def test_end_to_end_capture_validate_no_clobber_and_private_mode(tmp_path):
    cluster, reservation = valid_inputs(tmp_path)
    output = tmp_path / "receipt.json"
    digest = "sha256:" + "a" * 64

    created = capture_module.capture(
        str(cluster), str(reservation), str(output), digest
    )
    assert created["decision"] == (
        "CAPTURE_WRITTEN_REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW"
    )
    assert created["study_or_test_data_accessed"] is False
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    validated = capture_module.validate_only(
        str(cluster), str(reservation), str(output), digest
    )
    assert validated["decision"] == (
        "VALID_RECEIPT_REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW"
    )
    assert validated["field_or_blocker_closure_authorized"] is False

    with pytest.raises(capture_module.CaptureError, match="NO_CLOBBER"):
        capture_module.capture(str(cluster), str(reservation), str(output), digest)


@pytest.mark.parametrize(
    "sensitive_key",
    [
        "client_secret",
        "clientSecret",
        "apiToken",
        "privateKey",
        "accessKey",
        "creatorUserName",
        "single_user_name",
    ],
)
def test_recursive_secret_and_private_identity_keys_fail_closed(
    tmp_path, sensitive_key
):
    cluster, reservation = valid_inputs(tmp_path)
    write_canonical(
        cluster,
        {
            "aws_attributes": {"availability": "ON_DEMAND"},
            sensitive_key: "redacted-but-forbidden-value",
            "data_security_mode": "DATA_SECURITY_MODE_DEDICATED",
            "node_type_id": "m6i.4xlarge",
            "spark_version": "16.4.x-scala2.12",
        },
    )
    with pytest.raises(capture_module.CaptureError, match="SENSITIVE_KEY"):
        capture_module.capture(
            str(cluster), str(reservation), str(tmp_path / "out.json"), None
        )

def test_noncanonical_input_fails_closed(tmp_path):
    cluster, reservation = valid_inputs(tmp_path)
    cluster.write_text(
        json.dumps(
            {
                "aws_attributes": {"availability": "ON_DEMAND"},
                "data_security_mode": "SINGLE_USER",
                "node_type_id": "m6i.4xlarge",
                "spark_version": "16.4.x-scala2.12",
            },
            indent=2,
        )
        + "\n",
        encoding="ascii",
    )
    cluster.chmod(0o600)
    with pytest.raises(capture_module.CaptureError, match="NONCANONICAL"):
        capture_module.capture(
            str(cluster), str(reservation), str(tmp_path / "out2.json"), None
        )


def test_rehashed_safety_omission_is_rejected(tmp_path):
    cluster, reservation = valid_inputs(tmp_path)
    output = tmp_path / "receipt.json"
    capture_module.capture(str(cluster), str(reservation), str(output), None)
    receipt = json.loads(output.read_text(encoding="ascii"))
    del receipt["safety_boundary"]["study_or_test_data_accessed"]
    unsigned = dict(receipt)
    del unsigned["receipt_payload_sha256"]
    receipt["receipt_payload_sha256"] = capture_module._sha256(
        capture_module.RECEIPT_DOMAIN + capture_module._canonical_bytes(unsigned)
    )
    tampered = tmp_path / "tampered.json"
    write_canonical(tampered, receipt)
    with pytest.raises(capture_module.CaptureError, match="KEY_ROSTER"):
        capture_module.validate_only(
            str(cluster), str(reservation), str(tampered), None
        )


def test_forbidden_dbfs_and_volume_output_paths_are_rejected():
    with pytest.raises(capture_module.CaptureError, match="DBFS_PATH_FORBIDDEN"):
        capture_module._absolute_local_path("/dbfs/tmp/out.json", "OUTPUT")
    with pytest.raises(capture_module.CaptureError, match="UNITY_CATALOG_VOLUME"):
        capture_module._absolute_local_path("/Volumes/c/s/v/out.json", "OUTPUT")
    with pytest.raises(capture_module.CaptureError, match="WORKSPACE_FUSE"):
        capture_module._absolute_local_path("/Workspace/Users/out.json", "OUTPUT")


def test_source_has_no_network_subprocess_entropy_or_databricks_api_surface():
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
        }
    )
    called_attributes = {
        (node.func.value.id, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }
    assert called_attributes.isdisjoint(
        {
            ("os", "system"),
            ("os", "popen"),
            ("os", "spawnl"),
            ("os", "spawnv"),
            ("os", "execv"),
        }
    )
