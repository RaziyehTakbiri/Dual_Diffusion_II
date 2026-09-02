"""Hostile tests for the stopped Formal-Test-30 synthetic precursor package."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List

import pytest

from heterodiff.evaluation import (
    formal_test30_synthetic_coupled_path_qualification as coupling,
)


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "formal_test30_synthetic_coupling_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        module.SOURCE_PATH,
        module.SPEC_PATH,
        module.CP23_PATH,
        module.FREEZE_PATH,
        module.FREEZE_MACHINE_PATH,
    ]


def _copy_paths(paths: Iterable[str], tmp_path: Path) -> Path:
    for relative in paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _copy_package(module: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(_roster(module), tmp_path)


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _coherently_rebind_file(record: Dict[str, Any], relative: str, raw: bytes) -> None:
    matches = [
        row
        for group in ("package_bindings", "input_bindings")
        for row in record[group]
        if row["path"] == relative
    ]
    assert len(matches) == 1
    matches[0]["bytes"] = len(raw)
    matches[0]["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    matches[0]["trailing_lf"] = raw.endswith(b"\n")


def _replace(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def test_canonical_package_validates_with_exact_narrow_effect(validator: ModuleType):
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED"
        ),
        "eligible_after_independent_audit": True,
        "formal_test30": "PENDING",
        "formal_tests_closed": 0,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_exact_five_file_package_roster_is_bound(validator: ModuleType):
    review = validator.expected_record()["scope_review"]
    assert review == {
        "physical_file_count": 5,
        "pure_source_file_count": 1,
        "evidence_artifact_count": 4,
        "exact_package_roster": [
            validator.SOURCE_PATH,
            validator.HUMAN_PATH,
            validator.MACHINE_PATH,
            validator.VALIDATOR_PATH,
            validator.TEST_PATH,
        ],
        "consolidated_hostile_test": True,
        "unlisted_package_file_present": False,
        "hard_pinned_source_file_count": 1,
        "hard_pinned_input_file_count": 4,
    }
    assert len(validator.expected_record()["package_bindings"]) == 4


def test_authority_is_exact_and_grants_no_expansive_action(validator: ModuleType):
    row = validator.expected_record()["authority_provenance"]
    raw = row["normalized_visible_text"].encode("utf-8")
    assert len(raw) == 207
    assert hashlib.sha256(raw).hexdigest() == validator.AUTHORITY_SHA256
    assert row["continued_bounded_local_project_work_authorized"] is True
    for key in (
        "external_contact_or_browsing_authorized",
        "data_access_or_download_authorized",
        "entropy_or_live_randomness_authorized",
        "runtime_approval_authorized",
        "scientific_execution_authorized",
        "training_authorized",
        "claim_promotion_or_submission_authorized",
        "tracker_edit_authorized_by_package",
    ):
        assert row[key] is False


def test_exact_receipt_is_bound_including_positive_and_negative_flags(
    validator: ModuleType,
):
    receipt = validator.expected_record()["qualification_receipt"]
    assert receipt["levels"] == [2, 3, 4, 5]
    assert receipt["explicit_input_count"] == 160
    assert receipt["tag4_input_count"] == receipt["tag5_input_count"] == 80
    assert receipt["derived_coarse_increment_count"] == 140
    for key in (
        "coarse_equal_sum_fine",
        "persistent_lineage_across_levels",
        "retired_lineage_ledger_across_levels",
        "edit_family_counts_match_oracle",
        "path_contraction_passed",
        "finest_path_tolerance_passed",
        "endpoint_contraction_passed",
        "finest_endpoint_tolerance_passed",
        "frozen_levels_and_tolerances_used",
        "passed",
    ):
        assert receipt[key] is True
    for key in (
        "live_cp23_stream_consumed",
        "gaussian_source_law_certified",
        "general_split_step_integrated",
        "independent_recomputation_present",
        "formal_test30_closed",
    ):
        assert receipt[key] is False
    assert receipt["report_sha256"] == (
        "9f01d9e2de05836a463d64403d96ce441b45dc01a56160408db13e2b7e76b498"
    )


def test_internal_only_publication_boundary_is_fail_closed(validator: ModuleType):
    row = validator.expected_record()["publication_boundary"]
    assert row["internal_evidence_only"] is True
    assert row["anonymous_or_public_inclusion_permitted"] is False
    assert row["publication_safe_derivative_required"] is True
    assert row["fresh_anonymity_audit_required"] is True
    assert row["visible_authority_text_permitted_in_derivative"] is False
    assert row["internal_paths_hashes_or_receipts_permitted_in_derivative"] is False
    assert row["account_identity_present"] is False
    assert row["absolute_local_paths_present"] is False
    assert row["credentials_tokens_cookies_or_secrets_present"] is False
    assert row["raw_data_or_test_data_content_present"] is False


def test_cp23_level_obstruction_and_physical_increment_semantics_are_exact(
    validator: ModuleType,
):
    record = validator.expected_record()
    cp23 = record["cp23_contract"]
    assert cp23["level_limb_present"] is False
    assert cp23["independent_direct_redraw_at_each_level_permitted"] is False
    assert cp23["receipt_certifies_brownian_law"] is False
    assert "FINEST_LEVEL_ONLY" in cp23["safe_v1_strategy"]
    receipt = record["qualification_receipt"]
    assert "DELTA_W_NOT_STANDARDIZED_NORMAL_Z" in receipt["input_semantics"]
    assert "EXACT_DYADIC_REAL_SUM" in receipt["input_semantics"]


def test_endpoint_receipt_is_exactly_a_hypothetical_moment_oracle(
    validator: ModuleType,
):
    receipt = validator.expected_record()["qualification_receipt"]
    assert "IDEAL_IID_GAUSSIAN_MOMENT_PREMISE" in receipt["endpoint_metric"]
    assert "NOT_ASSERTED_OF_SUPPLIED_VALUES" in receipt["endpoint_law_premise"]
    assert receipt["gaussian_source_law_certified"] is False
    assert receipt["endpoint_w2_by_level"] == [
        0.0007573522254040962,
        0.00018472254789865305,
        4.5611333826692866e-05,
        1.1332163239868087e-05,
    ]


def test_formal_test30_and_all_existing_inventory_obligations_remain_open(
    validator: ModuleType,
):
    record = validator.expected_record()
    contract = record["formal_test30_contract"]
    assert contract["prior_state"] == contract["state_after_package"] == "PENDING"
    assert contract["formal_test_closed_by_package"] is False
    assert contract["existing_missing_obligations_declared_closed"] == []
    assert contract["existing_missing_obligations_remaining"] == [
        "TAG4_BROWNIAN_STREAM_CONSUMPTION",
        "TAG5_BROWNIAN_STREAM_CONSUMPTION",
        "PERSISTENT_EDIT_LINEAGE",
        "STEP_HALVING_COUPLING",
    ]
    effects = record["control_effects"]
    assert effects["formal_tests_closed"] == 0
    assert effects["existing_fields_closed"] == 0
    assert effects["blockers_closed"] == 0
    assert effects["scientific_results_produced"] == 0
    assert effects["tracker_edited"] is False


def test_source_ast_has_no_rng_network_subprocess_or_write_surface(
    validator: ModuleType,
):
    safety = validator.expected_record()["source_safety"]
    assert safety["ast_parsed"] is True
    for key in (
        "filesystem_write_call_present",
        "rng_or_entropy_import_present",
        "network_import_present",
        "subprocess_import_present",
        "tracker_mutation_present",
    ):
        assert safety[key] is False
    tree = ast.parse((ROOT / validator.SOURCE_PATH).read_text(encoding="utf-8"))
    imports = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    imports.update(
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not imports.intersection(
        {"random", "secrets", "numpy", "requests", "urllib", "socket", "subprocess"}
    )


def test_source_execution_custody_hard_pins_and_executes_only_verified_bytes(
    validator: ModuleType,
):
    row = validator.expected_record()["source_execution_custody"]
    assert row == {
        "hard_pinned_source_sha256": validator.EXPECTED_SOURCE_SHA256,
        "hard_pinned_input_sha256": validator.EXPECTED_INPUT_SHA256,
        "all_five_hard_pins_checked_before_source_execution": True,
        "stable_read_source_payload_executed_directly": True,
        "source_path_reopened_for_execution": False,
        "cached_bytecode_loader_used": False,
        "importlib_path_loader_used": False,
    }


def test_qualification_receipt_rejects_a_name_only_result_type_impostor(
    validator: ModuleType,
):
    expected_type = type("ExpectedQualification", (), {})
    impostor_type = type("SyntheticCoupledPathQualification", (), {})
    module = ModuleType("result_type_impostor")
    module.SyntheticCoupledPathQualification = expected_type
    module.run_frozen_synthetic_qualification = impostor_type
    with pytest.raises(validator.ValidationError, match="another qualification type"):
        validator._qualification_receipt(module)


@pytest.mark.parametrize(
    ("pointer", "value"),
    (
        ("state", "FORMAL_TEST30_COMPLETE"),
        ("scope_review.physical_file_count", 6),
        ("global_state", "EXECUTABLE"),
        ("authority_provenance.entropy_or_live_randomness_authorized", True),
        ("publication_boundary.anonymous_or_public_inclusion_permitted", True),
        ("formal_test30_contract.state_after_package", "PASS"),
        ("formal_test30_contract.formal_test_closed_by_package", True),
        ("cp23_contract.level_limb_present", True),
        ("cp23_contract.independent_direct_redraw_at_each_level_permitted", True),
        ("frozen_design.path_tolerance", 0.25),
        ("lineage_fixture.retired_serials", [1]),
        ("qualification_receipt.path_pair_gaps.2", 0.0),
        ("qualification_receipt.endpoint_w2_by_level.3", 0.0),
        ("qualification_receipt.retired_lineage_ledger_across_levels", False),
        ("qualification_receipt.report_sha256", "0" * 64),
        ("control_effects.formal_tests_closed", 1),
        ("strict_nonclaims.formal_test30_closed", True),
        ("remaining_gaps", []),
    ),
)
def test_rehashed_semantic_machine_mutations_are_rejected(
    validator: ModuleType, tmp_path: Path, pointer: str, value: Any
):
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: _replace(record, pointer, value))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    "negative_field",
    (
        "live_cp23_stream_consumed",
        "gaussian_source_law_certified",
        "general_split_step_integrated",
        "independent_recomputation_present",
        "formal_test30_closed",
    ),
)
def test_each_negative_receipt_flag_flip_is_rejected_even_after_record_redigest(
    validator: ModuleType, tmp_path: Path, negative_field: str
):
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace(
            record, "qualification_receipt." + negative_field, True
        ),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_wrong_machine_self_digest_and_noncanonical_json_are_rejected(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace(record, "state", "OTHER"),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)
    root = _copy_package(validator, tmp_path / "noncanonical")
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative",
    (
        "PROJECT_FORMAL_TEST30_SYNTHETIC_COUPLED_PATH_QUALIFICATION.md",
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
        "manuscript_v3/executable_method_spec.md",
        "src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py",
        "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md",
        "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json",
    ),
)
def test_bound_file_mutation_is_rejected(
    validator: ModuleType, tmp_path: Path, relative: str
):
    root = _copy_package(validator, tmp_path)
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative",
    (
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
        "manuscript_v3/executable_method_spec.md",
        "src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py",
        "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md",
        "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json",
    ),
)
def test_hard_pins_reject_comment_drift_after_coherent_machine_rebind(
    validator: ModuleType, tmp_path: Path, relative: str
):
    root = _copy_package(validator, tmp_path)
    path = root / relative
    raw = path.read_bytes() + b"# coherent allowed-import comment drift\n"
    path.write_bytes(raw)
    path.chmod(0o644)
    _rewrite_machine(
        validator,
        root,
        lambda record: _coherently_rebind_file(record, relative, raw),
    )
    with pytest.raises(
        validator.ValidationError,
        match="hard-pinned SHA-256 differs before source execution",
    ):
        validator.validate(root)


def test_effectful_coherently_rebound_source_is_rejected_before_execution(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path)
    source = root / validator.SOURCE_PATH
    marker = tmp_path / "source-must-not-execute"
    raw = source.read_bytes() + (
        "\nfrom pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('executed')\n"
        + "raise AssertionError('SOURCE_EXECUTED')\n"
    ).encode("utf-8")
    source.write_bytes(raw)
    source.chmod(0o644)
    _rewrite_machine(
        validator,
        root,
        lambda record: _coherently_rebind_file(record, validator.SOURCE_PATH, raw),
    )
    with pytest.raises(
        validator.ValidationError,
        match="hard-pinned SHA-256 differs before source execution",
    ):
        validator.validate(root)
    assert not marker.exists()


def test_verified_source_loader_never_reopens_path_or_cached_bytecode(
    validator: ModuleType, tmp_path: Path, monkeypatch
):
    marker = tmp_path / "unbound-path-bytes-executed"
    hostile_path = tmp_path / "hostile_source.py"
    hostile_path.write_text(
        "from pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('unbound execution')\n",
        encoding="utf-8",
    )
    hostile_path.chmod(0o644)
    py_compile.compile(str(hostile_path), doraise=True)
    verified_payload = (ROOT / validator.SOURCE_PATH).read_bytes()
    monkeypatch.setattr(validator, "SOURCE_PATH", str(hostile_path))
    loaded = validator._load_source(verified_payload)
    assert loaded.SCHEMA_VERSION == "heterodiff-formal-test30-synthetic-coupled-path-v1"
    assert not marker.exists()


def test_forbidden_source_import_is_rejected_before_receipt_use(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path)
    path = root / validator.SOURCE_PATH
    path.write_bytes(path.read_bytes() + b"\nimport random\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="forbidden module"):
        validator._source_safety(path.read_bytes())
    with pytest.raises(
        validator.ValidationError,
        match="hard-pinned SHA-256 differs before source execution",
    ):
        validator.validate(root)


def test_symlink_hardlink_and_executable_mode_are_rejected(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path / "symlink")
    human = root / validator.HUMAN_PATH
    target = root / "human-copy"
    target.write_bytes(human.read_bytes())
    target.chmod(0o644)
    human.unlink()
    human.symlink_to(target)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "hardlink")
    source = root / validator.SOURCE_PATH
    os.link(source, root / "source-hardlink")
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "mode")
    (root / validator.VALIDATOR_PATH).chmod(0o755)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_unsafe_paths_fail_closed(validator: ModuleType):
    for hostile in ("", ".", "..", "../escape", "/absolute", "a//b", "a/./b"):
        with pytest.raises(validator.ValidationError):
            validator._safe_relative_path(ROOT, hostile)


def test_validation_is_read_only(validator: ModuleType):
    paths = [ROOT / relative for relative in _roster(validator)]
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in paths
    }
    validator.validate()
    after = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in paths
    }
    assert before == after


def test_validator_runs_from_unrelated_current_directory(
    validator: ModuleType, tmp_path: Path
):
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(ROOT / VALIDATOR_REL)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "FORMAL_TEST30_SYNTHETIC_COUPLING_VALIDATION_PASS" in completed.stdout


def _fixture():
    design = coupling.frozen_synthetic_design()
    return design, coupling.build_frozen_explicit_inputs(design)


def _replace_address(item, **changes):
    return replace(item, address=replace(item.address, **changes))


def test_frozen_qualification_is_nonvacuous_and_narrow():
    result = coupling.run_frozen_synthetic_qualification()
    assert result.passed is True
    assert result.levels == (2, 3, 4, 5)
    assert result.explicit_input_count == 160
    assert result.tag4_input_count == 80
    assert result.tag5_input_count == 80
    assert result.derived_coarse_increment_count == 140
    assert result.coarse_sum_comparisons == 140
    assert result.coarse_equal_sum_fine is True
    assert result.persistent_lineage_across_levels is True
    assert result.retired_lineage_ledger_across_levels is True
    assert result.edit_family_counts_match_oracle is True
    assert result.path_pair_gaps == pytest.approx(
        (0.012165171492164367, 0.0031967310499734225, 0.0014979918645190993),
        rel=0.0,
        abs=1.0e-15,
    )
    assert result.endpoint_w2_by_level == pytest.approx(
        (
            0.0007573522254040962,
            0.00018472254789865305,
            4.5611333826692866e-05,
            1.1332163239868087e-05,
        ),
        rel=0.0,
        abs=1.0e-15,
    )
    assert result.design_sha256 == (
        "72be25d5cf27b94330f9c42ea21013aef06b1ae8a70aa01b12fa23212506ed83"
    )
    assert result.input_sha256 == (
        "fe19802595eac780b95954124b276bf121f2a014bd651de10d7adc280da44315"
    )
    assert result.report_sha256 == (
        "9f01d9e2de05836a463d64403d96ce441b45dc01a56160408db13e2b7e76b498"
    )
    assert "DELTA_W_NOT_STANDARDIZED_NORMAL_Z" in result.input_semantics
    assert "PRE_AND_POST_EDIT_CHECKPOINTS" in result.path_norm
    assert "IDEAL_IID_GAUSSIAN_MOMENT_PREMISE" in result.endpoint_metric
    assert "NOT_ASSERTED_OF_SUPPLIED_VALUES" in result.endpoint_law_premise
    assert result.live_cp23_stream_consumed is False
    assert result.gaussian_source_law_certified is False
    assert result.general_split_step_integrated is False
    assert result.independent_recomputation_present is False
    assert result.formal_test30_closed is False


def test_finest_addresses_are_exact_cp23_tag4_tag5_layout():
    design, supplied = _fixture()
    identities = set()
    for item in supplied:
        address = item.address
        assert address.domain_tag in (4, 5)
        assert address.philox_key == (design.run_id, address.domain_tag)
        assert address.philox_counter == (
            0,
            address.step_index,
            address.occurrence_serial,
            0,
        )
        assert address.identity not in identities
        identities.add(address.identity)


@pytest.mark.parametrize(
    "changes",
    (
        {"domain": "initializer"},
        {"domain_tag": 3},
        {"proposal_index": 1, "philox_counter": (0, 0, 1, 1)},
        {"occurrence_serial": 0, "philox_counter": (0, 0, 0, 0)},
        {"philox_key": (23030, 5)},
        {"philox_counter": (0, 1, 1, 0)},
        {"philox_key": (23030, True)},
        {"philox_counter": (False, 0, 1, 0)},
    ),
)
def test_address_hostiles_fail_closed(changes):
    design, supplied = _fixture()
    del design
    with pytest.raises((TypeError, ValueError)):
        _replace_address(supplied[0], **changes)


@pytest.mark.parametrize("field", ("run_id", "step_index", "occurrence_serial"))
def test_noncanonical_integer_subclasses_are_rejected(field):
    class StrangeInt(int):
        pass

    _design, supplied = _fixture()
    with pytest.raises(TypeError):
        _replace_address(
            supplied[0], **{field: StrangeInt(getattr(supplied[0].address, field))}
        )


def test_noncanonical_string_kinds_and_address_domain_are_rejected():
    class StrangeText(str):
        pass

    class EqualitySpoof:
        def __eq__(self, other):
            return other in ("A", "birth")

    for value in (StrangeText("A"), EqualitySpoof()):
        with pytest.raises(TypeError, match="occurrence.kind"):
            coupling.SyntheticOccurrence(1, value, 0.0)
    created = coupling.SyntheticOccurrence(2, "A", 0.0)
    for value in (StrangeText("birth"), EqualitySpoof()):
        with pytest.raises(TypeError, match="edit.kind"):
            coupling.FrozenLineageEdit(1, value, None, created)
    _design, supplied = _fixture()
    with pytest.raises(TypeError, match="address.domain"):
        _replace_address(supplied[0], domain=StrangeText(supplied[0].address.domain))


@pytest.mark.parametrize("value", (True, math.inf, -math.inf, math.nan))
def test_increment_payload_must_be_finite_real_non_boolean(value):
    _design, supplied = _fixture()
    with pytest.raises((TypeError, ValueError)):
        replace(supplied[0], increment=value)


def test_missing_extra_duplicate_and_reordered_inputs_fail_closed():
    design, supplied = _fixture()
    hostile_inputs = (
        supplied[:-1],
        supplied + (supplied[-1],),
        supplied[:1] + (supplied[0],) + supplied[1:],
        (supplied[1], supplied[0]) + supplied[2:],
    )
    for hostile in hostile_inputs:
        with pytest.raises(coupling.SyntheticCoupledPathError):
            coupling.qualify_synthetic_coupled_path(design, hostile)


def test_prebirth_postdeath_and_wrong_run_addresses_fail_closed():
    design, supplied = _fixture()
    first = supplied[0]
    hostile_addresses = (
        _replace_address(
            first,
            occurrence_serial=3,
            philox_counter=(0, first.address.step_index, 3, 0),
        ),
        _replace_address(
            first,
            run_id=design.run_id + 1,
            philox_key=(design.run_id + 1, first.address.domain_tag),
        ),
        _replace_address(
            first,
            step_index=31,
            occurrence_serial=2,
            philox_counter=(0, 31, 2, 0),
        ),
    )
    for hostile_item in hostile_addresses:
        hostile = (hostile_item,) + supplied[1:]
        with pytest.raises(coupling.SyntheticCoupledPathError):
            coupling.qualify_synthetic_coupled_path(design, hostile)


def test_named_v1_refuses_changed_levels_parameters_edits_and_tolerances():
    design, supplied = _fixture()
    changed_designs = (
        replace(design, levels=(3, 4, 5)),
        replace(design, horizon=2.0),
        replace(design, mean_reversion=0.8),
        replace(design, diffusion=0.9),
        replace(design, long_run_mean_a=0.36),
        replace(design, path_tolerance=0.03),
        replace(design, endpoint_w2_tolerance=0.007),
        replace(
            design,
            edits=(
                replace(
                    design.edits[0],
                    created=replace(design.edits[0].created, coordinate=0.21),
                ),
            )
            + design.edits[1:],
        ),
    )
    for changed in changed_designs:
        with pytest.raises(coupling.SyntheticCoupledPathError):
            coupling.qualify_synthetic_coupled_path(changed, supplied)


def test_lineage_replay_refuses_reuse_gap_and_retired_resurrection():
    design = coupling.frozen_synthetic_design()
    bad_creation = replace(
        design.edits[0], created=coupling.SyntheticOccurrence(4, "A", 0.2)
    )
    with pytest.raises(coupling.SyntheticCoupledPathError):
        replace(design, edits=(bad_creation,) + design.edits[1:])
    bad_replacement = replace(
        design.edits[1], created=coupling.SyntheticOccurrence(1, "B", -0.1)
    )
    with pytest.raises(coupling.SyntheticCoupledPathError):
        replace(design, edits=(design.edits[0], bad_replacement, design.edits[2]))
    resurrect = replace(design.edits[2], source_serial=1)
    with pytest.raises(coupling.SyntheticCoupledPathError):
        replace(design, edits=design.edits[:2] + (resurrect,))


def test_changed_explicit_value_has_distinct_bound_receipt():
    design, supplied = _fixture()
    baseline = coupling.qualify_synthetic_coupled_path(design, supplied)
    changed = (
        supplied[:10]
        + (replace(supplied[10], increment=supplied[10].increment + 2.0**-40),)
        + supplied[11:]
    )
    result = coupling.qualify_synthetic_coupled_path(design, changed)
    assert result.input_sha256 != baseline.input_sha256
    assert result.report_sha256 != baseline.report_sha256


def test_coarse_values_are_exact_dyadic_sums_not_redrawn_cp23_addresses():
    design, supplied = _fixture()
    finest = coupling._validate_finest_inputs(design, supplied)
    levels = coupling._derive_all_levels(design, finest)
    assert tuple(level for level, _ in levels) == design.levels
    for (coarse_level, coarse), (_fine_level, fine) in zip(levels[:-1], levels[1:]):
        rosters = coupling._live_roster_by_step(design, coarse_level)
        for step, serials in enumerate(rosters):
            for serial in serials:
                assert coarse[(step, serial, 4)] == (
                    fine[(2 * step, serial, 4)] + fine[(2 * step, serial, 5)]
                )
                assert coarse[(step, serial, 5)] == (
                    fine[(2 * step + 1, serial, 4)] + fine[(2 * step + 1, serial, 5)]
                )


def test_report_is_deterministic_and_side_effect_free():
    first = coupling.run_frozen_synthetic_qualification()
    second = coupling.run_frozen_synthetic_qualification()
    assert first == second
