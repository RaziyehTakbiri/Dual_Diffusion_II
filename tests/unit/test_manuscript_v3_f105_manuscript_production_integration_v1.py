from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for import_root in (ROOT, SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    conditional_cks_score,
    physionet_configuration,
    physionet_event_from_decimal_token,
    retail_configuration,
    retail_event_from_decimal_token,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    COMPARISON_DIRECTION,
    PRODUCTION_INTEGRATION_ID,
    SCORE_DIRECTION,
    production_conditional_cks_score,
)
from research.diagnostics.manuscript_v3_f105_manuscript_production_integration_v1 import (
    EXPECTED_RECORD_SHA256,
    MACHINE_PATH,
    STATE,
    ValidationError,
    _semantic_sha256,
    validate_package,
)


def _machine_record():
    return json.loads((ROOT / MACHINE_PATH).read_text(encoding="utf-8"))


def _copy_validation_tree(tmp_path: Path) -> Path:
    record = _machine_record()
    paths = [MACHINE_PATH]
    paths.extend(binding["path"] for binding in record["package_bindings"])
    paths.extend(item["path"] for item in record["frozen_inputs"])
    for relative in paths:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(0o644)
    return tmp_path


def _phys(value: str):
    return physionet_configuration(
        (
            physionet_event_from_decimal_token(
                elapsed_minutes=30,
                parameter="HR",
                value_text=value,
            ),
        )
    )


def _retail(quantity: int):
    return retail_configuration(
        (
            retail_event_from_decimal_token(
                invoice_no="123456",
                stock_code="SKU",
                description="item",
                quantity=quantity,
                invoice_calendar=(2010, 1, 2, 3, 4, 5, 6),
                unit_price_text="1.25",
                country="United Kingdom",
            ),
        )
    )


def test_read_only_validator_passes_current_package():
    assert validate_package() == {
        "state": STATE,
        "record_sha256": EXPECTED_RECORD_SHA256,
        "package_binding_count": 6,
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "target_predicate": True,
    }


def test_machine_semantic_digest_is_exact():
    record = _machine_record()
    assert record["record_sha256"] == EXPECTED_RECORD_SHA256
    assert _semantic_sha256(record) == EXPECTED_RECORD_SHA256


def test_machine_closure_boundary_keeps_blockers_and_fields_unchanged():
    closure = _machine_record()["closure_effect"]
    assert closure["field_count_delta"] == 0
    assert closure["blocker_count_delta"] == 0
    assert closure["all_b01_b12_open"] is True
    assert closure["b04_closed"] is False
    assert closure["f109_f112_closed"] is False
    assert closure["runtime_or_scientific_execution"] is False
    assert closure["claim_promotion"] is False


@pytest.mark.parametrize(
    "target,draws",
    [
        (_phys("80"), (_phys("80"), _phys("81"))),
        (_retail(1), (_retail(1), _retail(2))),
    ],
)
def test_production_formal_score_is_code_matched_in_both_domains(target, draws):
    production = production_conditional_cks_score(draws, target)
    assert production.formal_score == conditional_cks_score(draws, target)
    assert production.integration_id == PRODUCTION_INTEGRATION_ID
    assert production.score_direction == SCORE_DIRECTION


def test_direction_constant_is_exact():
    assert COMPARISON_DIRECTION == "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE"


def test_markdown_and_tex_display_both_dimensions_and_unit_parameters():
    markdown = (
        ROOT
        / "manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md"
    ).read_text(encoding="utf-8")
    tex = (
        ROOT
        / "manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.tex"
    ).read_text(encoding="utf-8")
    for text in (markdown, tex):
        assert "D_{\\mathrm{PHYS}}=112" in text
        assert "D_{\\mathrm{RETAIL}}=10" in text
        assert "a_d^2=b_d^2=\\tau_d^2=\\sigma_d^2=1" in text
        assert "\\widehat{\\operatorname{CKS}}_d" in text


def test_every_machine_binding_matches_current_bytes():
    for binding in _machine_record()["package_bindings"]:
        raw = (ROOT / binding["path"]).read_bytes()
        assert len(raw) == binding["bytes"]
        assert hashlib.sha256(raw).hexdigest() == binding["raw_sha256"]


def test_tampered_bound_file_refuses(tmp_path):
    root = _copy_validation_tree(tmp_path)
    target = root / "manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md"
    target.write_bytes(target.read_bytes() + b"tamper\n")
    with pytest.raises(ValidationError):
        validate_package(root)


def test_tampered_machine_semantics_refuse(tmp_path):
    root = _copy_validation_tree(tmp_path)
    path = root / MACHINE_PATH
    record = json.loads(path.read_text(encoding="utf-8"))
    record["closure_effect"]["b04_closed"] = True
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o644)
    with pytest.raises(ValidationError):
        validate_package(root)


def test_bound_file_symlink_refuses(tmp_path):
    root = _copy_validation_tree(tmp_path)
    path = root / "manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md"
    replacement = root / "replacement.md"
    replacement.write_bytes(path.read_bytes())
    replacement.chmod(0o644)
    path.unlink()
    path.symlink_to(replacement)
    with pytest.raises(ValidationError):
        validate_package(root)


def test_intermediate_directory_symlink_refuses(tmp_path):
    root = _copy_validation_tree(tmp_path / "root")
    real_manuscript = tmp_path / "real_manuscript"
    (root / "manuscript_v3").rename(real_manuscript)
    (root / "manuscript_v3").symlink_to(real_manuscript, target_is_directory=True)
    with pytest.raises(ValidationError):
        validate_package(root)


def test_root_symlink_alias_refuses(tmp_path):
    root = _copy_validation_tree(tmp_path / "root")
    alias = tmp_path / "root-alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValidationError):
        validate_package(alias)


def test_hardlinked_bound_file_refuses(tmp_path):
    root = _copy_validation_tree(tmp_path)
    path = root / "manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md"
    os.link(path, root / "second-link.md")
    with pytest.raises(ValidationError):
        validate_package(root)


def test_validator_runs_from_unrelated_working_directory():
    validator = (
        ROOT
        / "research/diagnostics/"
        "manuscript_v3_f105_manuscript_production_integration_v1.py"
    )
    completed = subprocess.run(
        [sys.executable, str(validator)],
        cwd="/private/tmp",
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["state"] == STATE
    assert result["record_sha256"] == EXPECTED_RECORD_SHA256


def test_machine_parameters_are_exact_and_no_fitting_is_claimed():
    record = _machine_record()
    semantics = record["metric_semantics"]
    assert semantics["event_tau_squared"] == "1"
    assert semantics["count_scale_squared"] == "1"
    assert semantics["event_scale_squared"] == "1"
    assert semantics["outer_sigma_squared"] == "1"
    assert record["production_contract"][
        "performs_io_or_randomness_or_fitting_or_threshold_decision"
    ] is False
    assert record["production_contract"][
        "factory_issued_field_integrity_digest_revalidated"
    ] is True


def test_formal_fraction_source_remains_exact():
    target = _phys("80")
    score = production_conditional_cks_score((target, _phys("81")), target)
    assert all(
        type(coefficient) is Fraction
        for _, coefficient in score.formal_score.terms
    )
