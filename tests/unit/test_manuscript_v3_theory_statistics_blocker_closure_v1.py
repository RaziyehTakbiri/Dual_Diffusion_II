from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from heterodiff.evaluation import preoutcome_theory_statistics_contract as contract
from heterodiff.evaluation.fixed_r64_cks_statistical_adapter import (
    F109AddressedDraw,
    F109_CONDITIONAL_DRAWS_PER_CASE,
    F109DrawAddress,
    FIXED_R64_ADAPTER_ID,
    fixed_r64_conditional_cks_score,
    fixed_r64_direct_minus_guide,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    CKSInstanceError,
    physionet_configuration,
    retail_configuration,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    CKSProductionError,
)


def _constant_seed_values(value: Fraction) -> tuple[Fraction, ...]:
    return (value,) * contract.INDEPENDENT_TRAINING_SEED_COUNT


def _addressed_draws(
    configuration: object,
    *,
    domain_id: str = contract.PHYSIONET_DOMAIN_ID,
    count: int = 64,
    case_id: str = "CASE-000",
) -> tuple[F109AddressedDraw, ...]:
    return tuple(
        F109AddressedDraw(
            address=F109DrawAddress(
                domain_id=domain_id,
                seed_id="SEED-000",
                group_id="GROUP-000",
                case_id=case_id,
                draw_id=f"DRAW-{ordinal:03d}",
                conditioning_id="CONDITION-000",
            ),
            configuration=configuration,
        )
        for ordinal in range(count)
    )


def test_frozen_primary_metric_scale_and_schedule() -> None:
    assert contract.CONDITIONAL_DRAWS_PER_CASE == 64
    assert contract.PAIRED_DIFFERENCE_RANGE == (Fraction(-3), Fraction(3))
    assert contract.PAIRED_DIFFERENCE_WIDTH == 6
    assert contract.MINIMUM_MEANINGFUL_EFFECT == Fraction(1, 100)
    assert contract.PLANNING_ALTERNATIVE_EFFECT == 1
    assert contract.INDEPENDENT_TRAINING_SEED_COUNT == 256
    assert contract.CERTIFIED_MINIMUM_TRAINING_SEEDS == 246
    assert contract.INDEPENDENT_TRAINING_SEED_COUNT >= contract.CERTIFIED_MINIMUM_TRAINING_SEEDS
    assert F109_CONDITIONAL_DRAWS_PER_CASE == contract.CONDITIONAL_DRAWS_PER_CASE
    assert FIXED_R64_ADAPTER_ID == "F105_F109_FIXED_R64_CONFIRMATORY_ADAPTER_V1"


def test_fixed_r64_adapter_accepts_exact_confirmatory_count() -> None:
    empty = physionet_configuration(())
    draws = _addressed_draws(empty)
    result = fixed_r64_conditional_cks_score(draws, empty)
    assert result.draw_count == 64
    assert result.binary64_score == -1.0
    comparison = fixed_r64_direct_minus_guide(draws, draws, empty)
    assert comparison.draw_count == 64
    assert comparison.direct_minus_guide == 0.0


@pytest.mark.parametrize("count", [0, 1, 2, 63, 65, 128])
def test_fixed_r64_adapter_refuses_every_other_general_f105_count(count: int) -> None:
    empty = physionet_configuration(())
    draws = _addressed_draws(empty, count=count)
    with pytest.raises(CKSProductionError):
        fixed_r64_conditional_cks_score(draws, empty)
    with pytest.raises(CKSProductionError):
        fixed_r64_direct_minus_guide(draws, _addressed_draws(empty), empty)


def test_fixed_r64_adapter_preserves_domain_refusal() -> None:
    phys = physionet_configuration(())
    retail = retail_configuration(())
    with pytest.raises(CKSInstanceError):
        fixed_r64_conditional_cks_score(_addressed_draws(retail), phys)


def test_fixed_r64_adapter_refuses_unpaired_or_duplicate_addresses() -> None:
    empty = physionet_configuration(())
    direct = _addressed_draws(empty)
    guide = list(_addressed_draws(empty))
    guide[17] = F109AddressedDraw(
        address=replace(guide[17].address, draw_id="UNPAIRED-DRAW"),
        configuration=empty,
    )
    with pytest.raises(CKSProductionError, match="not exactly paired"):
        fixed_r64_direct_minus_guide(direct, tuple(guide), empty)
    duplicate = list(direct)
    duplicate[17] = F109AddressedDraw(
        address=duplicate[16].address,
        configuration=empty,
    )
    with pytest.raises(CKSProductionError, match="duplicate draw address"):
        fixed_r64_conditional_cks_score(tuple(duplicate), empty)


def test_fixed_r64_adapter_refuses_cross_case_and_noncanonical_addresses() -> None:
    empty = physionet_configuration(())
    rows = list(_addressed_draws(empty))
    rows[-1] = F109AddressedDraw(
        address=replace(rows[-1].address, case_id="CASE-OTHER"),
        configuration=empty,
    )
    with pytest.raises(CKSProductionError, match="spans more than one"):
        fixed_r64_conditional_cks_score(tuple(rows), empty)
    with pytest.raises(CKSProductionError, match="visible ASCII"):
        F109DrawAddress(
            domain_id="R3-PHYS",
            seed_id="bad seed",
            group_id="G",
            case_id="C",
            draw_id="D",
            conditioning_id="Q",
        )


def test_seed_registry_is_exact_stable_unique_uint64() -> None:
    registry = contract.confirmatory_seed_registry()
    assert registry == contract.CONFIRMATORY_SEED_REGISTRY
    assert len(registry) == len(set(registry)) == 256
    assert all(type(value) is int and 0 <= value < 2**64 for value in registry)
    digest = hashlib.sha256(
        b"".join(value.to_bytes(8, "big") for value in registry)
    ).hexdigest()
    assert digest == "73ecdd8ecfb4c3dd164bd47e5f71bebc8d62c0bde4d46a20c4262291d88fa350"


@pytest.mark.parametrize("integer", [1, 2, 20, 40, 257])
def test_log_interval_contains_math_log(integer: int) -> None:
    import math

    lower, upper = contract.log_interval_ge_one(Fraction(integer))
    target = math.log(integer)
    assert float(lower) <= target <= float(upper)
    assert lower <= upper


def test_log_and_sqrt_refuse_inexact_or_invalid_inputs() -> None:
    with pytest.raises(TypeError):
        contract.log_interval_ge_one(20)
    with pytest.raises(contract.StatisticalContractError):
        contract.log_interval_ge_one(Fraction(1, 2))
    with pytest.raises(TypeError):
        contract.sqrt_upper(2.0)
    with pytest.raises(contract.StatisticalContractError):
        contract.sqrt_upper(Fraction(-1))


def test_sqrt_upper_is_rigorous_and_tight() -> None:
    for value in (Fraction(0), Fraction(2), Fraction(3, 7), Fraction(10000)):
        upper = contract.sqrt_upper(value)
        assert upper * upper >= value
        if value:
            quantum = Fraction(1, (value.denominator << contract.SQRT_FRACTION_BITS))
            assert max(Fraction(0), upper - quantum) ** 2 < value


def test_seed_count_matches_accepted_predecessor_calculator() -> None:
    module_path = ROOT / "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py"
    spec = importlib.util.spec_from_file_location("power_route_for_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    predecessor = module.certified_seed_count(
        Fraction(6),
        Fraction(1, 40),
        Fraction(1, 20),
        Fraction(1, 100),
        Fraction(1),
    )
    assert predecessor["certified_seed_count"] == 246
    assert contract.certified_seed_count(
        width=Fraction(6),
        alpha_star=Fraction(1, 40),
        beta_star=Fraction(1, 20),
        null_margin=Fraction(1, 100),
        alternative=Fraction(1),
    ) == predecessor["certified_seed_count"]


def test_seed_count_refuses_wrong_types_and_nonpositive_gap() -> None:
    kwargs = dict(
        width=Fraction(6),
        alpha_star=Fraction(1, 40),
        beta_star=Fraction(1, 20),
        null_margin=Fraction(1, 100),
        alternative=Fraction(1),
    )
    for key, bad in (("width", 6), ("alpha_star", 0.025), ("beta_star", True)):
        attempt = dict(kwargs)
        attempt[key] = bad
        with pytest.raises(TypeError):
            contract.certified_seed_count(**attempt)
    kwargs["alternative"] = Fraction(1, 100)
    with pytest.raises(contract.StatisticalContractError):
        contract.certified_seed_count(**kwargs)


def test_hoeffding_exponent_and_lower_bound_are_exact() -> None:
    values = _constant_seed_values(Fraction(1))
    exponent = contract.hoeffding_exponent(values)
    assert exponent == Fraction(2 * 256) * Fraction(99, 100) ** 2 / 36
    lower = contract.hoeffding_lower_bound(values, alpha=Fraction(1, 40))
    assert type(lower) is Fraction
    assert Fraction(1, 100) < lower < 1


def test_holm_hoeffding_both_domains_pass_at_planning_alternative() -> None:
    result = contract.two_domain_holm_hoeffding(
        physionet_seed_values=_constant_seed_values(Fraction(1)),
        retail_seed_values=_constant_seed_values(Fraction(1)),
    )
    assert result.ordered_domains == contract.DOMAIN_IDS
    assert result.alpha_by_domain == {
        contract.PHYSIONET_DOMAIN_ID: Fraction(1, 40),
        contract.RETAIL_DOMAIN_ID: Fraction(1, 20),
    }
    assert result.rejected_by_domain == {
        contract.PHYSIONET_DOMAIN_ID: True,
        contract.RETAIL_DOMAIN_ID: True,
    }
    assert result.family_pass is True


def test_holm_hoeffding_one_domain_cannot_rescue_the_other() -> None:
    result = contract.two_domain_holm_hoeffding(
        physionet_seed_values=_constant_seed_values(Fraction(2)),
        retail_seed_values=_constant_seed_values(Fraction(0)),
    )
    assert result.rejected_by_domain[contract.PHYSIONET_DOMAIN_ID] is True
    assert result.rejected_by_domain[contract.RETAIL_DOMAIN_ID] is False
    assert result.family_pass is False


def test_holm_tie_order_is_physionet_first() -> None:
    values = _constant_seed_values(Fraction(1))
    result = contract.two_domain_holm_hoeffding(
        physionet_seed_values=values, retail_seed_values=values
    )
    assert result.ordered_domains == (
        contract.PHYSIONET_DOMAIN_ID,
        contract.RETAIL_DOMAIN_ID,
    )


@pytest.mark.parametrize(
    "bad_values,exception",
    [
        ([Fraction(1)] * 256, TypeError),
        ((Fraction(1),) * 255, contract.StatisticalContractError),
        ((Fraction(4),) * 256, contract.StatisticalContractError),
        ((1,) * 256, TypeError),
    ],
)
def test_hoeffding_refuses_incomplete_inexact_or_out_of_range_values(
    bad_values: object, exception: type[Exception]
) -> None:
    with pytest.raises(exception):
        contract.hoeffding_exponent(bad_values)


def test_real_real_partitions_are_deterministic_balanced_and_disjoint() -> None:
    groups = tuple(f"P{ordinal:03d}" for ordinal in range(128))
    first = contract.real_real_floor_partitions(
        domain_id=contract.PHYSIONET_DOMAIN_ID, group_ids=groups
    )
    second = contract.real_real_floor_partitions(
        domain_id=contract.PHYSIONET_DOMAIN_ID, group_ids=tuple(reversed(groups))
    )
    assert first == second
    assert len(first) == 256
    for left, right in first:
        assert len(left) == len(right) == 64
        assert not set(left).intersection(right)
        assert set(left).union(right) == set(groups)
    retail = contract.real_real_floor_partitions(
        domain_id=contract.RETAIL_DOMAIN_ID, group_ids=groups
    )
    assert retail != first


def test_real_real_floor_nearest_rank_q95() -> None:
    values = tuple(Fraction(value, 255) for value in range(256))
    assert contract.real_real_floor_q95(values) == Fraction(243, 255)
    assert contract.real_real_floor_q95(tuple(reversed(values))) == Fraction(243, 255)


def test_real_real_floor_refuses_bad_roster_and_values() -> None:
    with pytest.raises(contract.StatisticalContractError):
        contract.real_real_floor_partitions(
            domain_id=contract.PHYSIONET_DOMAIN_ID,
            group_ids=tuple(f"P{i}" for i in range(127)),
        )
    with pytest.raises(contract.StatisticalContractError):
        contract.real_real_floor_q95((Fraction(0),) * 255)
    with pytest.raises(contract.StatisticalContractError):
        contract.real_real_floor_q95((Fraction(3),) * 256)


_B05_ROSTER_SHA256 = "23" * 32
_B05_RECEIPT_SHA256 = "45" * 32


def _b05_attempts(*, failures: int = 1) -> tuple[contract.B05AttemptStatus, ...]:
    return tuple(
        contract.B05AttemptStatus(
            attempt_id=f"ATTEMPT-{ordinal:03d}",
            status="INFRA_ABORT" if ordinal < failures else "COMPLETE",
        )
        for ordinal in range(20)
    )


def _passing_b05_values(
    attempts: tuple[contract.B05AttemptStatus, ...],
) -> tuple[contract.B05CertifiedValue, ...]:
    raw = {
        "calibration_coverage_abs_error_upper": Fraction(1, 20),
        "support_violation_count": 0,
        "fidelity_guide_minus_direct_upper": Fraction(0),
        "initializer_kl_upper_nat": Fraction(1, 100),
        "association_tv_upper": Fraction(1, 100),
        "guide_latency_upper": Fraction(2),
        "direct_latency_lower": Fraction(1),
        "guide_peak_memory_upper": Fraction(2),
        "direct_peak_memory_lower": Fraction(1),
        "guide_total_compute_upper": Fraction(1),
        "direct_total_compute_lower": Fraction(1),
    }
    attempt_digest = contract.b05_attempt_manifest_sha256(attempts)
    return tuple(
        contract.B05CertifiedValue(
            metric_id=metric_id,
            unit_id=unit_id,
            bound_kind=bound_kind,
            value=raw[metric_id],
            roster_sha256=_B05_ROSTER_SHA256,
            attempt_manifest_sha256=attempt_digest,
            certification_receipt_sha256=_B05_RECEIPT_SHA256,
            certification_scope_id=contract.B05_CERTIFICATION_SCOPE_ID,
        )
        for metric_id, unit_id, bound_kind in contract.B05_VALUE_SPECS
    )


def _evaluate_b05(
    values: tuple[contract.B05CertifiedValue, ...],
    attempts: tuple[contract.B05AttemptStatus, ...],
) -> contract.B05ConstraintDecision:
    return contract.evaluate_b05_constraints(
        certified_values=values,
        attempts=attempts,
        roster_sha256=_B05_ROSTER_SHA256,
        certification_receipt_sha256=_B05_RECEIPT_SHA256,
    )


def test_b05_all_equal_boundaries_pass() -> None:
    attempts = _b05_attempts()
    decision = _evaluate_b05(_passing_b05_values(attempts), attempts)
    assert decision.all_frozen_inequalities_satisfied is True
    assert all(decision.component_thresholds_satisfied.values())
    assert decision.failure_rate == Fraction(1, 20)
    assert decision.latency_ratio == 2
    assert decision.peak_memory_ratio == 2
    assert decision.total_compute_ratio == 1
    assert decision.project_gate_pass is False
    assert decision.external_certification_authenticated is False


@pytest.mark.parametrize(
    "key,bad,component",
    [
        ("calibration_coverage_abs_error_upper", Fraction(51, 1000), "calibration-and-coverage"),
        ("support_violation_count", 1, "support-validity"),
        ("fidelity_guide_minus_direct_upper", Fraction(1, 1000), "event-count-type-mark-and-time-fidelity"),
        ("initializer_kl_upper_nat", Fraction(11, 1000), "initializer-error"),
        ("association_tv_upper", Fraction(11, 1000), "association-approximation-error"),
        ("attempt_statuses", 2, "run-failure-rate"),
        ("guide_latency_upper", Fraction(2001, 1000), "latency"),
        ("guide_peak_memory_upper", Fraction(2001, 1000), "peak-memory"),
        ("guide_total_compute_upper", Fraction(1001, 1000), "total-compute"),
    ],
)
def test_each_b05_threshold_fails_independently(
    key: str, bad: object, component: str
) -> None:
    attempts = _b05_attempts(failures=2 if component == "run-failure-rate" else 1)
    values = list(_passing_b05_values(attempts))
    if component != "run-failure-rate":
        ordinal = next(
            index for index, value in enumerate(values) if value.metric_id == key
        )
        values[ordinal] = replace(values[ordinal], value=bad)
    decision = _evaluate_b05(tuple(values), attempts)
    assert decision.component_thresholds_satisfied[component] is False
    assert decision.all_frozen_inequalities_satisfied is False


def test_b05_refuses_malformed_counts_and_ratios() -> None:
    attempts = _b05_attempts()
    values = list(_passing_b05_values(attempts))
    ordinal = next(
        index for index, value in enumerate(values)
        if value.metric_id == "direct_latency_lower"
    )
    values[ordinal] = replace(values[ordinal], value=Fraction(0))
    with pytest.raises(contract.StatisticalContractError):
        _evaluate_b05(tuple(values), attempts)
    values = list(_passing_b05_values(attempts))
    ordinal = next(
        index for index, value in enumerate(values)
        if value.metric_id == "association_tv_upper"
    )
    values[ordinal] = replace(values[ordinal], value=Fraction(2))
    with pytest.raises(contract.StatisticalContractError):
        _evaluate_b05(tuple(values), attempts)


def test_b05_refuses_wrong_unit_roster_attempt_receipt_and_status_metadata() -> None:
    attempts = _b05_attempts()
    baseline = list(_passing_b05_values(attempts))
    for mutation in (
        {"unit_id": "SECOND"},
        {"roster_sha256": "67" * 32},
        {"attempt_manifest_sha256": "89" * 32},
        {"certification_receipt_sha256": "ab" * 32},
    ):
        values = list(baseline)
        values[0] = replace(values[0], **mutation)
        with pytest.raises(contract.StatisticalContractError):
            _evaluate_b05(tuple(values), attempts)
    with pytest.raises(contract.StatisticalContractError):
        contract.B05AttemptStatus(attempt_id="A", status="RETRY")
    with pytest.raises(contract.StatisticalContractError):
        replace(baseline[0], certification_scope_id="WRONG-SCOPE")


def test_b05_failure_denominator_uses_every_scheduled_terminal_status() -> None:
    attempts = tuple(
        contract.B05AttemptStatus(attempt_id=f"A-{index}", status=status)
        for index, status in enumerate(
            (
                "COMPLETE",
                "ALGORITHMIC_FAILURE",
                "NONFINITE",
                "OOM_OR_TIMEOUT",
                "INFRA_ABORT",
            )
        )
    )
    decision = _evaluate_b05(_passing_b05_values(attempts), attempts)
    assert decision.failure_rate == Fraction(4, 5)
    assert decision.component_thresholds_satisfied["run-failure-rate"] is False
    assert decision.project_gate_pass is False


def test_c17_final_wording_is_unambiguous_exclusion() -> None:
    wording = contract.C17_FINAL_PUBLICATION_WORDING
    assert wording.startswith("Claim C17 is retired")
    assert "do not state or imply" in wording
    assert "theorem" in wording
    assert "empirical consequence" in wording


def test_module_has_no_effectful_import_surface() -> None:
    source = (ROOT / "src/heterodiff/evaluation/preoutcome_theory_statistics_contract.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import os",
        "import random",
        "import secrets",
        "import socket",
        "import subprocess",
        "import requests",
        "urllib",
        "open(",
        "Path(",
        "numpy",
        "scipy",
        "torch",
    )
    assert not any(token in source for token in forbidden)


def test_fixed_r64_adapter_has_no_io_rng_or_runtime_entrypoint() -> None:
    source = (ROOT / "src/heterodiff/evaluation/fixed_r64_cks_statistical_adapter.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import os",
        "import random",
        "import secrets",
        "import socket",
        "import subprocess",
        "import requests",
        "urllib",
        "open(",
        "Path(",
        "numpy",
        "scipy",
        "torch",
    )
    assert not any(token in source for token in forbidden)


def test_machine_fixture_is_canonical_and_semantically_bound_when_present() -> None:
    path = ROOT / "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json"
    if not path.exists():
        pytest.skip("machine fixture is added after the pure contract stabilizes")
    raw = path.read_bytes()
    record = json.loads(raw)
    assert raw == (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    payload = dict(record)
    digest = payload.pop("record_sha256")
    expected = hashlib.sha256(
        (record["schema_version"] + "\0").encode("ascii")
        + json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    assert digest == expected


def _validator_module():
    path = ROOT / "research/diagnostics/manuscript_v3_theory_statistics_blocker_closure_v1.py"
    spec = importlib.util.spec_from_file_location("theory_statistics_closure_validator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_0644(path: Path, raw: bytes = b"stable\n") -> None:
    path.write_bytes(raw)
    path.chmod(0o644)


def _copy_bound_package(tmp_path: Path):
    validator = _validator_module()
    copied_root = tmp_path / "package"
    for relative in (validator.MACHINE_PATH,) + validator.EXPECTED_BINDING_PATHS:
        source = ROOT / relative
        destination = copied_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return validator, copied_root


def _resign_outer_machine(validator, copied_root: Path) -> None:
    machine_path = copied_root / validator.MACHINE_PATH
    record = json.loads(machine_path.read_text(encoding="ascii"))
    for binding in record["bindings"]:
        raw = (copied_root / binding["path"]).read_bytes()
        binding["bytes"] = len(raw)
        binding["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        binding["terminal_lf"] = raw.endswith(b"\n")
    record["record_sha256"] = validator.semantic_digest(record)
    machine_path.write_bytes(
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "ascii"
        )
    )
    machine_path.chmod(0o644)


def test_stable_read_accepts_exact_root_chain_and_leaf(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "level").mkdir(parents=True)
    _write_0644(root / "level" / "leaf.txt")
    validator = _validator_module()
    assert validator.stable_read("level/leaf.txt", root=root) == b"stable\n"


def test_stable_read_rejects_symlink_root_and_intermediate(tmp_path: Path) -> None:
    real_root = tmp_path / "real-root"
    (real_root / "level").mkdir(parents=True)
    _write_0644(real_root / "level" / "leaf.txt")
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(real_root, target_is_directory=True)
    validator = _validator_module()
    with pytest.raises(validator.ValidationError):
        validator.stable_read("level/leaf.txt", root=linked_root)

    outer = tmp_path / "outer"
    outer.mkdir()
    (outer / "linked-level").symlink_to(
        real_root / "level", target_is_directory=True
    )
    with pytest.raises(validator.ValidationError):
        validator.stable_read("linked-level/leaf.txt", root=outer)


def test_stable_read_rejects_leaf_mode_and_hardlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    leaf = root / "leaf.txt"
    _write_0644(leaf)
    validator = _validator_module()
    leaf.chmod(0o600)
    with pytest.raises(validator.ValidationError, match="leaf custody invalid"):
        validator.stable_read("leaf.txt", root=root)
    leaf.chmod(0o644)
    os.link(leaf, root / "second-link.txt")
    with pytest.raises(validator.ValidationError, match="leaf custody invalid"):
        validator.stable_read("leaf.txt", root=root)


def test_stable_read_detects_ancestor_entry_swap_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    level = root / "level"
    level.mkdir(parents=True)
    _write_0644(level / "leaf.txt", b"captured\n")
    validator = _validator_module()
    real_read = validator.os.read
    swapped = False

    def swapping_read(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        raw = real_read(descriptor, size)
        if not swapped:
            swapped = True
            level.rename(root / "old-level")
            replacement = root / "level"
            replacement.mkdir()
            _write_0644(replacement / "leaf.txt", b"replacement\n")
        return raw

    monkeypatch.setattr(validator.os, "read", swapping_read)
    with pytest.raises(
        validator.ValidationError,
        match="(?:held directory custody|path entry) changed",
    ):
        validator.stable_read("level/leaf.txt", root=root)


def test_validator_rejects_resigned_source_change_against_frozen_receipt(
    tmp_path: Path,
) -> None:
    validator, copied_root = _copy_bound_package(tmp_path)
    source_path = copied_root / validator.SOURCE_PATH
    source_path.write_bytes(source_path.read_bytes() + b"# resigned mutation\n")
    source_path.chmod(0o644)
    _resign_outer_machine(validator, copied_root)
    with pytest.raises(validator.ValidationError, match="validator-frozen receipt"):
        validator.validate(root=copied_root)


def test_validator_rejects_resigned_semantic_pointer_and_authority_mutations(
    tmp_path: Path,
) -> None:
    validator, copied_root = _copy_bound_package(tmp_path)
    machine_path = copied_root / validator.MACHINE_PATH
    record = json.loads(machine_path.read_text(encoding="ascii"))
    record["field_closures"][0]["json_pointer"] = "/wrong"
    record["authority"]["scientific_execution_authorized"] = True
    record["record_sha256"] = validator.semantic_digest(record)
    machine_path.write_bytes(
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "ascii"
        )
    )
    machine_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root=copied_root)


def test_validator_binds_accepted_f105_dependency_and_go_review() -> None:
    validator = _validator_module()
    record = json.loads((ROOT / validator.MACHINE_PATH).read_text(encoding="ascii"))
    assert record["joint_b04_dependency"] == validator.expected_joint_b04_dependency()
    assert record["joint_b04_dependency"]["integration_review_disposition"] == "GO_P0_P1_P2_ZERO"
    assert record["joint_b04_dependency"]["general_engine_draw_domain"] == {
        "minimum": 2,
        "maximum": 128,
    }
    assert record["joint_b04_dependency"]["confirmatory_adapter_draw_count"] == 64
    binding_paths = tuple(row["path"] for row in record["bindings"])
    assert validator.F105_INTEGRATION_MACHINE_PATH in binding_paths
    assert validator.F105_INTEGRATION_REVIEW_PATH in binding_paths


def test_validator_does_not_compile_or_execute_captured_package_source() -> None:
    validator_source = (
        ROOT
        / "research/diagnostics/manuscript_v3_theory_statistics_blocker_closure_v1.py"
    ).read_text(encoding="utf-8")
    assert "exec(compile(" not in validator_source
    assert "_load_captured_source" not in validator_source


def test_validator_accepts_exact_package_when_fixture_is_present() -> None:
    path = ROOT / "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json"
    if not path.exists():
        pytest.skip("machine fixture is added after the pure contract stabilizes")
    result = _validator_module().validate()
    assert result["validation"] == "PASS"
    assert result["field_closure_count"] == 31
    assert result["certified_minimum_training_seeds"] == 246
    assert result["frozen_training_seeds"] == 256
    assert result["blockers_eligible_on_independent_acceptance"] == 4
    assert result["accepted_f105_joint_dependency"] is True
    assert result["scientific_execution"] is False


def test_semantic_digest_changes_for_a_resigned_field_mutation_when_fixture_present() -> None:
    path = ROOT / "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json"
    if not path.exists():
        pytest.skip("machine fixture is added after the pure contract stabilizes")
    validator = _validator_module()
    record = json.loads(path.read_text(encoding="ascii"))
    baseline = validator.semantic_digest(record)
    mutated = json.loads(json.dumps(record))
    mutated["field_closures"][6]["value"] = 63
    mutated.pop("record_sha256", None)
    assert validator.semantic_digest(mutated) != baseline


def test_validator_field_roster_is_exact() -> None:
    expected = (
        "F001", "F002", "F003", "F004", "F005", "F006",
        "F109", "F110", "F111", "F112",
        "F114", "F115", "F116", "F117", "F118", "F119",
        "F121", "F123", "F124", "F125", "F126", "F127", "F149",
        "F130", "F131", "F132", "F133", "F134", "F135", "F136", "F138",
    )
    assert _validator_module().EXPECTED_FIELD_IDS == expected
