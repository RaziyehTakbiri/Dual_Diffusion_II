from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest

from heterodiff.experiments import b08_local_host_capacity_gap as policy


PROJECT_ROOT = Path(__file__).absolute().parents[2]
VALIDATOR_PATH = PROJECT_ROOT / "research/diagnostics/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py"
SPEC = importlib.util.spec_from_file_location("b08_package_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def _copy_file(root: Path, relative: str) -> None:
    source = PROJECT_ROOT / relative
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o644)


@pytest.fixture()
def package_copy(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    for relative in validator.EXPECTED_PREDECESSOR_SHA256:
        _copy_file(root, relative)
    for relative in validator.PACKAGE_ROSTER:
        _copy_file(root, relative)
    return root


def _machine(root: Path) -> dict:
    payload = (root / validator.MACHINE_PATH).read_bytes()
    return validator.decode_canonical_json_file(payload)


def _write_machine(root: Path, record: dict, *, recompute: bool = True) -> None:
    value = deepcopy(record)
    if recompute:
        value["record_sha256"] = validator._record_digest(value)
    (root / validator.MACHINE_PATH).write_bytes(validator.canonical_json_bytes(value) + b"\n")


def _rebind_package_file(root: Path, record: dict, relative: str) -> None:
    rows = record["package_bindings_excluding_machine_self"]
    for row in rows:
        if row["path"] == relative:
            payload = (root / relative).read_bytes()
            metadata = os.lstat(root / relative)
            row.update(
                {
                    "bytes": len(payload),
                    "mode_octal": "%04o" % stat.S_IMODE(metadata.st_mode),
                    "nlink": metadata.st_nlink,
                    "raw_sha256": hashlib.sha256(payload).hexdigest(),
                    "terminal_lf": payload.endswith(b"\n"),
                }
            )
            break
    else:
        raise AssertionError(relative)
    record["package_aggregate_sha256"] = validator.package_aggregate_sha256(rows)


def _rebind_predecessor(root: Path, record: dict, relative: str) -> None:
    rows = record["accepted_predecessor_bindings"]
    for row in rows:
        if row["path"] == relative:
            payload = (root / relative).read_bytes()
            metadata = os.lstat(root / relative)
            row.update(
                {
                    "bytes": len(payload),
                    "mode_octal": "%04o" % stat.S_IMODE(metadata.st_mode),
                    "nlink": metadata.st_nlink,
                    "raw_sha256": hashlib.sha256(payload).hexdigest(),
                    "terminal_lf": payload.endswith(b"\n"),
                }
            )
            return
    raise AssertionError(relative)


def test_exact_projection_digest_and_rosters() -> None:
    projection = policy.supported_projection()
    assert policy.sha256_json(projection) == validator.EXPECTED_PROJECTION_SHA256
    assert [row["field_id"] for row in projection["field_closures"]] == ["F153", "F158", "F161"]
    assert [row["field_id"] for row in projection["residual_gaps"]] == [
        "F150", "F151", "F152", "F154", "F155", "F156", "F157", "F159", "F160", "F162"
    ]
    assert projection["capacity_gate"]["B08_close_permitted"] is False
    assert all(row["satisfied"] is False for row in projection["capacity_gate"]["requirements"])


def test_exact_hardware_environment_and_storage_nonclaims() -> None:
    projection = policy.supported_projection()
    hardware = projection["hardware_observation"]
    assert hardware["hardware_public_profile_sha256"] == validator.EXPECTED_HARDWARE_PROFILE_SHA256
    assert hardware["private_identifiers_recorded_in_package"] is False
    assert hardware["production_hardware_selected"] is False
    assert hardware["production_hardware_reserved"] is False
    environment = projection["software_environment_observation"]
    assert environment["software_environment_observation_sha256"] == validator.EXPECTED_ENVIRONMENT_SHA256
    assert environment["production_environment_selected"] is False
    assert environment["complete_b12_runtime_present"] is False
    storage = projection["storage_observation"]
    assert storage["persistent_bytes_reserved"] == 0
    assert storage["reservation_created"] is False
    assert storage["production_capacity_receipt"] is False


def test_f153_exact_fail_closed_policy() -> None:
    value = policy.deterministic_settings_value()
    assert value["policy_id"] == "B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1"
    assert value["accelerator_policy"] == "CPU_ONLY_CUDA_AND_MPS_DISABLED"
    assert value["torch"] == {
        "cudnn_benchmark": False,
        "deterministic_algorithms": True,
        "interop_threads": 1,
        "threads": 1,
        "warn_only": False,
    }
    assert value["production_determinism_demonstrated_by_this_package"] is False
    assert value["f141_precision_owned_separately"] is True


def test_f158_exact_zero_empirical_pilot() -> None:
    value = policy.pilot_compute_allocation_value()
    for name in (
        "accelerator_hours", "model_evaluations", "persistent_bytes",
        "scientific_or_empirical_pilot_runs", "wall_time_seconds",
    ):
        assert value[name] == 0 and type(value[name]) is int
    assert value["f104_resource_event_counts_all_zero"] is True
    assert value["synthetic_environment_calibration_is_not_empirical_pilot"] is True
    assert value["transfer_or_topup_permitted"] is False


def test_f161_exact_zero_failure_reserve_and_charging() -> None:
    value = policy.failure_reserve_value()
    for name in (
        "accelerator_hours", "extra_attempt_count", "model_evaluations",
        "persistent_bytes", "wall_time_seconds",
    ):
        assert value[name] == 0 and type(value[name]) is int
    assert value["infrastructure_rerun_predicate"] == "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN"
    assert value["failed_and_aborted_scheduled_attempts_charged_to_original_allocation"] is True
    assert value["replacement_or_retry_permitted"] is False
    assert value["post_result_topup_permitted"] is False


def test_synthetic_receipts_exact_and_self_digested() -> None:
    sha_receipt = policy.sha256_calibration_receipt()
    torch_receipt = policy.torch_calibration_receipt()
    assert sha_receipt["receipt_sha256"] == validator.EXPECTED_SHA_CALIBRATION_SHA256
    assert torch_receipt["receipt_sha256"] == validator.EXPECTED_TORCH_CALIBRATION_SHA256
    assert {row["sha256"] for row in sha_receipt["rows"]} == {
        "3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351"
    }
    assert {row["output_sha256"] for row in torch_receipt["rows"]} == {
        "94816432ec6b2c0dda21ed9420dfad8ea5cf0f6d987dd20fef54500d9825f43d"
    }
    assert sha_receipt["production_capacity_or_f104_weight_claimed"] is False
    assert torch_receipt["production_capacity_determinism_or_f104_weight_claimed"] is False
    policy.validate_sha256_calibration_receipt(sha_receipt)
    policy.validate_torch_calibration_receipt(torch_receipt)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("capacity_gate", "B08_close_permitted"), True),
        (("capacity_gate", "requirements", 0, "satisfied"), True),
        (("hardware_observation", "production_hardware_selected"), True),
        (("hardware_observation", "production_hardware_reserved"), True),
        (("hardware_observation", "private_identifiers_recorded_in_package"), True),
        (("software_environment_observation", "production_environment_selected"), True),
        (("software_environment_observation", "complete_b12_runtime_present"), True),
        (("storage_observation", "reservation_created"), True),
        (("storage_observation", "persistent_bytes_reserved"), 1),
        (("field_closures", 0, "field_id"), "F150"),
        (("field_closures", 1, "value", "wall_time_seconds"), 1),
        (("field_closures", 2, "value", "extra_attempt_count"), 1),
        (("residual_gaps", 0, "status"), "CLOSED"),
        (("sha256_calibration_receipt", "rows", 0, "wall_time_ns"), 1),
        (("torch_calibration_receipt", "rows", 0, "output_sha256"), "0" * 64),
    ],
)
def test_supported_projection_rejects_semantic_mutations(path: tuple, replacement: object) -> None:
    projection = policy.supported_projection()
    target = projection
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = replacement
    with pytest.raises(ValueError):
        policy.validate_supported_projection(projection)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"extra": False}),
        lambda value: value.pop("capacity_gate"),
        lambda value: value.__setitem__("field_closures", tuple(value["field_closures"])),
        lambda value: value.__setitem__("residual_gaps", list(reversed(value["residual_gaps"]))),
    ],
)
def test_supported_projection_rejects_schema_mutations(mutation) -> None:
    projection = policy.supported_projection()
    mutation(projection)
    with pytest.raises(ValueError):
        policy.validate_supported_projection(projection)


def test_supported_projection_rejects_equal_comparing_integer_subclass() -> None:
    class HostileInteger(int):
        pass

    projection = policy.supported_projection()
    projection["storage_observation"]["persistent_bytes_reserved"] = HostileInteger(0)
    with pytest.raises(ValueError, match="non-exact JSON-native type"):
        policy.validate_supported_projection(projection)


@pytest.mark.parametrize(
    ("receipt_builder", "validator_function", "mutation"),
    [
        (policy.sha256_calibration_receipt, policy.validate_sha256_calibration_receipt, lambda r: r.__setitem__("receipt_sha256", "0" * 64)),
        (policy.sha256_calibration_receipt, policy.validate_sha256_calibration_receipt, lambda r: r["rows"][0].__setitem__("ordinal", True)),
        (policy.sha256_calibration_receipt, policy.validate_sha256_calibration_receipt, lambda r: r["rows"][0].__setitem__("wall_time_ns", True)),
        (policy.sha256_calibration_receipt, policy.validate_sha256_calibration_receipt, lambda r: r.__setitem__("rows", tuple(r["rows"]))),
        (policy.torch_calibration_receipt, policy.validate_torch_calibration_receipt, lambda r: r.__setitem__("receipt_sha256", "0" * 64)),
        (policy.torch_calibration_receipt, policy.validate_torch_calibration_receipt, lambda r: r["rows"][0].__setitem__("shape", (512, 512, 512))),
        (policy.torch_calibration_receipt, policy.validate_torch_calibration_receipt, lambda r: r["rows"][0].__setitem__("ordinal", True)),
        (policy.torch_calibration_receipt, policy.validate_torch_calibration_receipt, lambda r: r.__setitem__("mps_available", 0)),
    ],
)
def test_receipt_validators_reject_hostile_types_and_mutations(receipt_builder, validator_function, mutation) -> None:
    receipt = receipt_builder()
    mutation(receipt)
    with pytest.raises(ValueError):
        validator_function(receipt)


def test_canonical_package_validator_passes() -> None:
    result = validator.validate_package(PROJECT_ROOT)
    assert result["state"] == validator.STATE
    assert result["B08_closed"] is False
    assert result["field_ids"] == ["F153", "F158", "F161"]
    assert result["residual_field_ids"] == [
        "F150", "F151", "F152", "F154", "F155", "F156", "F157", "F159", "F160", "F162"
    ]


def test_standalone_validator_passes_from_unrelated_working_directory(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines()[0] == "PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN"


@pytest.mark.parametrize(
    ("section", "key", "replacement"),
    [
        ("field_delta", "field_ids", ["F150", "F153", "F158", "F161"]),
        ("field_delta", "blockers_closed", 1),
        ("count_transition", "after", {"pre_execution_open": 20}),
        ("blocker_transition", "closed_now", ["B08"]),
        ("gate_a_transition", "hardware_capacity_item_closed", True),
        ("project_effects_and_nonclaims", "B08_closed", True),
        ("project_effects_and_nonclaims", "capacity_reservation_or_resource_receipt_created", True),
        ("authority_boundary", "hardware_or_storage_reservation_authorized_or_performed", True),
        ("qualification_boundary", "self_review_or_self_acceptance", True),
        ("evidence_ready_registration", "permitted_blocker_delta", ["B08"]),
    ],
)
def test_validator_rejects_coherently_resigned_false_claims(
    package_copy: Path, section: str, key: str, replacement: object
) -> None:
    record = _machine(package_copy)
    record[section][key] = replacement
    _write_machine(package_copy, record)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_coherently_resigned_projection_change(package_copy: Path) -> None:
    record = _machine(package_copy)
    record["supported_projection"]["capacity_gate"]["B08_close_permitted"] = True
    record["supported_projection_sha256"] = validator.sha256_json(record["supported_projection"])
    _write_machine(package_copy, record)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_changed_source_even_after_package_rebinding(package_copy: Path) -> None:
    source = package_copy / validator.SOURCE_PATH
    source.write_bytes(source.read_bytes() + b"\nimport os\n")
    record = _machine(package_copy)
    _rebind_package_file(package_copy, record, validator.SOURCE_PATH)
    _write_machine(package_copy, record)
    with pytest.raises(validator.ValidationError, match="source raw hash"):
        validator.validate_package(package_copy)


def test_validator_rejects_changed_human_even_after_package_rebinding(package_copy: Path) -> None:
    human = package_copy / validator.HUMAN_PATH
    human.write_bytes(human.read_bytes() + b"drift\n")
    record = _machine(package_copy)
    _rebind_package_file(package_copy, record, validator.HUMAN_PATH)
    _write_machine(package_copy, record)
    with pytest.raises(validator.ValidationError, match="human record raw hash"):
        validator.validate_package(package_copy)


def test_validator_rejects_changed_predecessor_even_after_rebinding(package_copy: Path) -> None:
    relative = "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json"
    target = package_copy / relative
    target.write_bytes(target.read_bytes() + b" ")
    record = _machine(package_copy)
    _rebind_predecessor(package_copy, record, relative)
    _write_machine(package_copy, record)
    with pytest.raises(validator.ValidationError, match="predecessor hash drift"):
        validator.validate_package(package_copy)


@pytest.mark.parametrize("relative", [validator.HUMAN_PATH, validator.SOURCE_PATH, validator.TEST_PATH])
def test_validator_rejects_missing_package_file(package_copy: Path, relative: str) -> None:
    (package_copy / relative).unlink()
    with pytest.raises((FileNotFoundError, validator.ValidationError)):
        validator.validate_package(package_copy)


def test_validator_rejects_package_symlink(package_copy: Path) -> None:
    target = package_copy / validator.SOURCE_PATH
    payload = target.read_bytes()
    target.unlink()
    real = target.with_name("real_source.py")
    real.write_bytes(payload)
    real.chmod(0o644)
    target.symlink_to(real.name)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_package_hardlink(package_copy: Path) -> None:
    target = package_copy / validator.HUMAN_PATH
    alias = target.with_name("hardlink_alias.md")
    os.link(target, alias)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


@pytest.mark.parametrize("mode", [0o600, 0o664, 0o755])
def test_validator_rejects_package_mode_change(package_copy: Path, mode: int) -> None:
    (package_copy / validator.HUMAN_PATH).chmod(mode)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_machine_without_terminal_lf(package_copy: Path) -> None:
    path = package_copy / validator.MACHINE_PATH
    path.write_bytes(path.read_bytes().removesuffix(b"\n"))
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_machine_with_extra_terminal_lf(package_copy: Path) -> None:
    path = package_copy / validator.MACHINE_PATH
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_noncanonical_machine_json(package_copy: Path) -> None:
    path = package_copy / validator.MACHINE_PATH
    record = _machine(package_copy)
    path.write_text(json.dumps(record, sort_keys=False, indent=2) + "\n", encoding="ascii")
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_validator_rejects_duplicate_key_machine_json(package_copy: Path) -> None:
    path = package_copy / validator.MACHINE_PATH
    payload = path.read_bytes()
    assert payload.startswith(b"{")
    path.write_bytes(b'{"state":"forged",' + payload[1:])
    with pytest.raises(validator.ValidationError, match="duplicate JSON key"):
        validator.validate_package(package_copy)


def test_validator_rejects_nonfinite_machine_json(package_copy: Path) -> None:
    path = package_copy / validator.MACHINE_PATH
    path.write_bytes(b'{"value":NaN}\n')
    with pytest.raises(validator.ValidationError):
        validator.validate_package(package_copy)


def test_machine_binding_and_record_digest_are_noncyclic() -> None:
    record = _machine(PROJECT_ROOT)
    assert record["machine_self_binding"] == {
        "path": validator.MACHINE_PATH,
        "raw_self_hash_embedded": False,
        "semantic_self_digest_field": "record_sha256",
    }
    assert record["record_sha256"] == validator._record_digest(record)
    assert all(row["path"] != validator.MACHINE_PATH for row in record["package_bindings_excluding_machine_self"])


def test_source_effect_surface_is_pure() -> None:
    payload = (PROJECT_ROOT / validator.SOURCE_PATH).read_bytes()
    validator._validate_source_effect_surface(payload)


def test_no_tracker_or_ledger_is_in_package_or_predecessor_bindings() -> None:
    record = _machine(PROJECT_ROOT)
    paths = set(record["package_file_roster"])
    paths.update(row["path"] for row in record["accepted_predecessor_bindings"])
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in paths
    assert "PROJECT_EVIDENCE_LEDGER.md" not in paths
    assert all(not path.startswith("sources/") for path in paths)
