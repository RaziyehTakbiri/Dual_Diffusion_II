from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


_ROOT = Path(__file__).resolve().parents[2]
_FREEZE_PATH = _ROOT / (
    "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v1.json"
)
_DOCUMENT_PATH = _ROOT / "manuscript_v3/a1_development_checkpoint_freeze.md"
_GLOBAL_PREREG_PATH = _ROOT / (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)


def _reject_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _load(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda value: (_ for _ in ()).throw(
            AssertionError("nonfinite JSON constant: " + value)
        ),
    )
    assert isinstance(value, dict)
    return raw, value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count_nulls(value: Any) -> int:
    if value is None:
        return 1
    if isinstance(value, dict):
        return sum(_count_nulls(child) for child in value.values())
    if isinstance(value, list):
        return sum(_count_nulls(child) for child in value)
    return 0


def _assert_optional_file_binding(
    document: Dict[str, Any], path_key: str, digest_key: str
) -> bool:
    binding = document["implementation_binding"]
    relative_path = binding[path_key]
    expected_sha256 = binding[digest_key]
    if relative_path is None or expected_sha256 is None:
        assert relative_path is None
        assert expected_sha256 is None
        return False
    path = _ROOT / relative_path
    assert path.is_file()
    assert _sha256(path) == expected_sha256
    return True


def test_a1_development_freeze_is_canonical_and_source_bound() -> None:
    raw, freeze = _load(_FREEZE_PATH)
    canonical = (
        json.dumps(
            freeze,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")
    assert raw == canonical
    assert freeze["schema_version"] == (
        "manuscript-v3-a1-development-checkpoint-freeze-v1"
    )

    sources = freeze["source_bindings"]
    assert _sha256(_ROOT / sources["a1_specification_path"]) == (
        sources["a1_specification_sha256"]
    )
    assert _ROOT / sources["freeze_document_path"] == _DOCUMENT_PATH
    assert _ROOT / sources["machine_freeze_path"] == _FREEZE_PATH
    for path_name, digest_name in (
        (
            "global_execution_preregistration_path",
            "global_execution_preregistration_sha256",
        ),
        (
            "global_execution_preregistration_machine_path",
            "global_execution_preregistration_machine_sha256",
        ),
        (
            "global_execution_preregistration_test_path",
            "global_execution_preregistration_test_sha256",
        ),
    ):
        assert _sha256(_ROOT / sources[path_name]) == sources[digest_name]
    runtime = freeze["runtime_contract"]
    assert _sha256(_ROOT / runtime["environment_lock_path"]) == (
        runtime["environment_lock_sha256"]
    )


def test_a1_development_coordinate_and_training_contract_are_exact() -> None:
    _, freeze = _load(_FREEZE_PATH)
    assert freeze["scientific_scope"] == {
        "claim_promotion_permitted": False,
        "closes_c17": False,
        "confirmatory_or_production_evidence": False,
        "development_checkpoint_only": True,
        "lane_id": "A1-DEV-GUIDED-1729-N32768-V1",
        "production_aggregate_admission_permitted": False,
        "qualifies_r1": False,
        "qualifies_r2": False,
        "real_domain_test_access_permitted": False,
    }
    assert freeze["coordinate"] == {
        "accepted_example_budget": 32768,
        "batch_size": 128,
        "method": "guided",
        "optimizer_updates": 3000,
        "seed": 1729,
    }
    training = freeze["training_protocol"]
    assert training["architecture"] == [21, 32, 32, 1]
    assert training["parameter_count"] == 1793
    assert training["precision"] == "binary64"
    assert training["optimizer"] == {
        "betas": [0.9, 0.999],
        "epsilon": 1e-08,
        "id": "AdamW",
        "weight_decay": 0.000001,
    }
    assert training["learning_rate_schedule"] == {
        "final": 0.00001,
        "formula": "eta_k=1e-5+0.5*(1e-3-1e-5)*(1+cos(pi*k/(K-1)))",
        "initial": 0.001,
        "update_index_domain": "k=0,...,2999",
    }
    assert training["checkpoint_rule"] == "FINAL_UPDATE_ONLY"
    assert training["attempt_count"] == 1
    assert training["maximum_tuning_trials"] == 0
    assert training["early_stopping"] is False
    assert training["warm_start_permitted"] is False
    assert training["rerun_or_replacement_permitted"] is False


def test_a1_development_fixture_and_runtime_use_production_contract() -> None:
    _, freeze = _load(_FREEZE_PATH)
    fixture = freeze["fixture"]
    assert fixture["production_fixture_sha256"] == (
        "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
    )
    assert fixture["local_compatibility_fixture_admissible"] is False
    assert fixture["cap"] == 3
    assert fixture["horizon"] == 1.0
    assert fixture["state_count"] == 20
    assert fixture["observation_count"] == 21
    assert fixture["overflow_observation_index"] == 20
    assert fixture["evaluation_grid"] == "t_j=j/32_for_j=0,...,32"
    assert fixture["birth_rates"] == [0.38, 0.3, 0.24]
    assert fixture["death_rates_per_occurrence"] == [0.28, 0.34, 0.25]
    assert len(fixture["prerequisite_content_sha256"]) == 5

    runtime = freeze["runtime_contract"]
    assert runtime["system"] == "Darwin"
    assert runtime["machine"] == "arm64"
    assert runtime["minimum_macos_version"] == "14.0"
    assert runtime["python_version"] == "3.11.5"
    assert runtime["python_safe_path"] is True
    assert runtime["python_source_import_path"] == "src"
    assert runtime["python_write_bytecode"] is False
    assert runtime["numpy"] == "2.4.6"
    assert runtime["scipy"] == "1.17.1"
    assert runtime["torch"] == "2.12.1"
    assert runtime["threadpoolctl"] == "3.6.0"
    assert runtime["target_environment_installation_verified_pre_freeze"] is True
    assert runtime["fresh_development_runtime_observation_required"] is True
    assert runtime["formal_production_runtime_identity_approval_present"] is False
    assert (
        runtime[
            "formal_production_runtime_identity_approval_required_for_development_lane"
        ]
        is False
    )
    assert runtime["cpu_only"] is True
    assert runtime["accelerators_hidden"] is True
    assert runtime["deterministic_algorithms"] is True
    assert runtime["torch_intraop_threads"] == 1
    assert runtime["torch_interop_threads"] == 1
    assert runtime["thread_environment"]["PYTHONSAFEPATH"] == "1"
    assert runtime["thread_environment"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert set(runtime["thread_environment"].values()) == {"", "0", "1"}


def test_runner_binding_is_atomic_and_execution_authorized() -> None:
    _, freeze = _load(_FREEZE_PATH)
    source_bound = _assert_optional_file_binding(
        freeze, "runner_source_path", "runner_source_sha256"
    )
    test_bound = _assert_optional_file_binding(
        freeze, "runner_test_path", "runner_test_sha256"
    )
    binding = freeze["implementation_binding"]
    assert source_bound and test_bound
    assert binding == {
        "runner_source_path": "src/heterodiff/experiments/finite_association_development_checkpoint_runner.py",
        "runner_source_sha256": "bd493e39c097ee6f0befc78cec57a7d17c76c8ed6fbc0167c77fce3bd56084d9",
        "runner_test_path": "tests/unit/test_finite_association_development_checkpoint_runner.py",
        "runner_test_sha256": "535abf37475213218465214ba49932454bfb19c5e5ea33f26aff06ad92022e89",
        "source_manifest_sha256": "474fefc6dc06fb8d513e3848308e9e68a5ab86b13f2e5ba4442e362d19239379",
        "training_configuration_sha256": "db230ee90fa963941132c48f87be760662eaf0f229d13fdd7483cb6ef4ca74cf",
    }

    authorization = freeze["authorization"]
    assert authorization["current_state"] == "FROZEN_EXECUTION_AUTHORIZED"
    assert authorization["static_parameter_freeze_complete"] is True
    assert authorization["development_checkpoint_execution_authorized"] is True
    assert (
        authorization[
            "execution_permit_issuance_delegated_to_hash_bound_runner_after_fresh_preflight"
        ]
        is True
    )
    assert authorization["execution_permit_issued"] is False


def test_execution_and_result_slots_are_empty_before_the_run() -> None:
    _, freeze = _load(_FREEZE_PATH)
    assert all(value is None for value in freeze["execution_record"].values())
    result = freeze["result_record"]
    assert result["checkpoint_present"] is False
    assert all(
        value is None for key, value in result.items() if key != "checkpoint_present"
    )
    root = freeze["artifact_contract"]
    assert root["expected_capsule_output_root"] == (
        "artifacts/manuscript_v3_a1_development_checkpoint_v1"
    )
    assert "artifacts/a1_campaign_v4" in root["forbidden_output_roots"]
    artifact = _ROOT / root["expected_capsule_output_root"]
    if artifact.exists():
        assert artifact.is_dir() and not artifact.is_symlink()
        assert (artifact / "success-receipt.json").is_file() or (
            artifact / "failure-receipt.json"
        ).is_file()
    assert freeze["operational_limits"] == {
        "exceeding_limit_disposition": "REFUSED_OR_FAILURE_NO_CHECKPOINT_CLAIM",
        "maximum_capsule_output_bytes": 2 * 1024**3,
        "maximum_recorded_peak_rss_bytes": 8 * 1024**3,
        "maximum_wall_seconds": 3600,
        "operational_only_not_scientific_thresholds": True,
        "retry_or_substitute_coordinate_permitted_after_limit": False,
    }


def test_global_preregistration_state_is_unchanged_and_fail_closed() -> None:
    _, freeze = _load(_FREEZE_PATH)
    _, global_prereg = _load(_GLOBAL_PREREG_PATH)
    boundary = freeze["global_preregistration_boundary"]
    assert (
        _count_nulls(global_prereg) == boundary["expected_existing_global_null_count"]
    )
    assert len(global_prereg["unresolved_blockers"]) == (
        boundary["expected_existing_unresolved_blocker_count"]
    )
    assert global_prereg["confirmatory_execution_authorized"] is False
    assert boundary["confirmatory_execution_authorized"] is False
    assert boundary["global_preregistration_mutation_permitted_by_this_freeze"] is False
    assert boundary["r1_r2_r3_r4_status_change_permitted"] is False
    assert [row["current_status"] for row in global_prereg["slot_plan"]] == [
        "NOT_RUN",
        "NOT_RUN",
        "NOT_RUN",
        "NOT_RUN",
    ]


def test_human_freeze_states_the_nonpromotional_boundaries() -> None:
    text = _DOCUMENT_PATH.read_text("utf-8")
    for literal in (
        "A1-DEV-GUIDED-1729-N32768-V1",
        "FROZEN_EXECUTION_AUTHORIZED",
        "Checkpoint execution authorized now:** yes",
        "not an execution of\n`R1-A1`, `R2-HYBRID`, `R3-PHYS`, or `R4-RETAIL`",
        "retains all `174` existing `null` fields and all\n`12` unresolved blockers",
        "artifacts/manuscript_v3_a1_development_checkpoint_v1",
        "a `3600`-second wall timeout",
        "operational\ndevelopment ceilings, not scientific acceptance thresholds",
        "No optimizer permit exists until the\nbound runner completes its fresh preflight",
    ):
        assert literal in text
