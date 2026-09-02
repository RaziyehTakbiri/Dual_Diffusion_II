from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
import hashlib
from pathlib import Path

import pytest

from heterodiff.evaluation import b12_integrated_offline_candidate as b12
from heterodiff.evaluation import b12_two_domain_adapter_stack as stack
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    PHYSIONET_DOMAIN_ID,
    RETAIL_DOMAIN_ID,
    ExactConfiguration,
    ExactEvent,
)
from heterodiff.experiments import two_domain_baseline_registry as b06


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py"


def _source_sha256() -> str:
    return hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def _fixtures() -> tuple[ExactConfiguration, ExactConfiguration]:
    return stack.qualification_fixture_configurations()


def _manifest() -> tuple[stack.AdapterConformanceRecord, ...]:
    retail, physionet = _fixtures()
    return stack.build_synthetic_conformance_manifest(
        retail_configuration=retail,
        physionet_configuration=physionet,
        module_source_sha256=_source_sha256(),
    )


def _direct_b06_roster() -> tuple[tuple[str, str, str], ...]:
    frozen = b06.FROZEN_REGISTRY
    domains = (stack.RETAIL_B06_DOMAIN_ID, stack.PHYSIONET_B06_DOMAIN_ID)
    primary = {row["method_id"]: row for row in frozen["primary_pair"]}
    controls = {row["control_id"]: row for row in frozen["controls"]}
    families = {row["family_id"]: row for row in frozen["literature_families"]}
    external = {
        (row["method_id"], row["domain_id"]): row
        for row in frozen["external_baselines"]
    }
    rows: list[tuple[str, str, str]] = []
    for adapter_id in (
        "association-aware-guide-plus-residual",
        "unified-direct-conditioner",
    ):
        for domain_id in domains:
            rows.append((adapter_id, domain_id, primary[adapter_id]["config_sha256"]))
    for adapter_id in (
        "analytic-guide-only-residual-removed",
        "direct-or-residual-only-analytic-guide-removed",
        "association-destroyed-or-factorized-eventwise",
        "unconditional-base-sanity-reference",
    ):
        for domain_id in domains:
            rows.append((adapter_id, domain_id, controls[adapter_id]["config_sha256"]))
    for adapter_id in (
        "ngdb-style-auxiliary-guide-plus-correction",
        "deft-style-generalized-h-frozen-base-correction",
        "task-compatible-same-base-smc-or-feynman-kac",
        "closest-variable-cardinality-point-or-edit-generator",
    ):
        for domain_id in domains:
            rows.append(
                (
                    adapter_id,
                    domain_id,
                    families[adapter_id]["implementation_by_domain"][domain_id][
                        "config_sha256"
                    ],
                )
            )
    for key in (
        ("CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1", "physionet-challenge-2012"),
        ("EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1", "online-retail-ii"),
    ):
        rows.append((key[0], key[1], external[key]["config_sha256"]))
    return tuple(rows)


def test_corrected_roster_is_exact_b06_and_excludes_all_legacy_family_hashes() -> None:
    assert stack.ADAPTER_ROSTER_SNAPSHOT == _direct_b06_roster()
    assert len(stack.ADAPTER_ROSTER_SNAPSHOT) == 22
    assert len(set(stack.ADAPTER_ROSTER_SNAPSHOT)) == 22
    assert stack.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS == tuple(range(12, 20))
    for ordinal, (legacy, corrected) in enumerate(
        zip(stack.LEGACY_PARTIAL_ROSTER_SNAPSHOT, stack.ADAPTER_ROSTER_SNAPSHOT)
    ):
        assert legacy[:2] == corrected[:2]
        if 12 <= ordinal < 20:
            assert legacy[2] != corrected[2]
        else:
            assert legacy[2] == corrected[2]
    legacy_bad_hashes = {
        stack.LEGACY_PARTIAL_ROSTER_SNAPSHOT[index][2]
        for index in range(12, 20)
    }
    corrected_family_hashes = {
        stack.ADAPTER_ROSTER_SNAPSHOT[index][2]
        for index in range(12, 20)
    }
    assert legacy_bad_hashes.isdisjoint(corrected_family_hashes)


def test_context_encoder_is_exact_64_deterministic_and_occurrence_complete() -> None:
    retail, physionet = _fixtures()
    for configuration, expected_dimension in ((retail, 10), (physionet, 112)):
        first = stack.encode_exact_context(configuration)
        second = stack.encode_exact_context(configuration)
        assert first == second
        assert len(first.coordinates) == stack.PRIMARY_CONTEXT_DIMENSION == 64
        assert all(type(value) is Fraction for value in first.coordinates)
        assert first.event_count == len(configuration.events) == 3
        assert len(first.ordered_event_sha256s) == first.event_count
        assert first.ordered_event_sha256s[0] == first.ordered_event_sha256s[1]
        assert len(configuration.events[0].coordinates) == expected_dimension
        assert first.semantic_payload()["context_dimension"] == 64


def test_duplicate_and_tie_multiplicity_cannot_be_silently_truncated() -> None:
    retail, _ = _fixtures()
    two_events = ExactConfiguration(RETAIL_DOMAIN_ID, retail.events[1:])
    complete = stack.encode_exact_context(retail)
    truncated = stack.encode_exact_context(two_events)
    assert complete.event_count == truncated.event_count + 1
    assert complete.configuration_sha256 != truncated.configuration_sha256
    assert complete.encoding_sha256 != truncated.encoding_sha256
    assert complete.ordered_event_sha256s != truncated.ordered_event_sha256s


def test_exact_event_dimensions_and_cross_domain_inputs_fail_closed() -> None:
    retail, physionet = _fixtures()
    source = _source_sha256()
    with pytest.raises(stack.B12AdapterStackError):
        stack.build_synthetic_conformance_manifest(
            retail_configuration=physionet,
            physionet_configuration=physionet,
            module_source_sha256=source,
        )
    with pytest.raises(stack.B12AdapterStackError):
        stack.build_synthetic_conformance_manifest(
            retail_configuration=retail,
            physionet_configuration=retail,
            module_source_sha256=source,
        )

    forged_event = object.__new__(ExactEvent)
    object.__setattr__(forged_event, "domain_id", RETAIL_DOMAIN_ID)
    object.__setattr__(forged_event, "coordinates", (Fraction(0),) * 9)
    forged_configuration = object.__new__(ExactConfiguration)
    object.__setattr__(forged_configuration, "domain_id", RETAIL_DOMAIN_ID)
    object.__setattr__(forged_configuration, "events", (forged_event,))
    with pytest.raises(stack.B12AdapterStackError):
        stack.encode_exact_context(forged_configuration)


def test_exact_concrete_types_reject_subclasses_and_duck_objects() -> None:
    class ConfigurationSubclass(ExactConfiguration):
        pass

    subclass = ConfigurationSubclass(RETAIL_DOMAIN_ID, ())
    with pytest.raises(TypeError):
        stack.encode_exact_context(subclass)
    with pytest.raises(TypeError):
        stack.encode_exact_context(object())  # type: ignore[arg-type]

    context = stack.encode_exact_context(_fixtures()[0])
    forged = replace(context, coordinates=tuple([Fraction(0)] * 63))
    with pytest.raises(stack.B12AdapterStackError):
        forged.semantic_payload()


def test_manifest_has_exact_order_dimensions_and_unique_source_bindings() -> None:
    manifest = _manifest()
    assert len(manifest) == 22
    assert tuple(
        (row.adapter_id, row.domain_id, row.config_sha256) for row in manifest
    ) == stack.ADAPTER_ROSTER_SNAPSHOT
    assert len({row.implementation_source_sha256 for row in manifest}) == 22
    for row in manifest:
        assert row.module_source_sha256 == _source_sha256()
        assert row.implementation_source_sha256 != row.config_sha256
        assert row.implementation_source_sha256 != stack.ZERO_SHA256
        assert row.f105_coordinate_dimension == (
            10 if row.domain_id == stack.RETAIL_B06_DOMAIN_ID else 112
        )
        assert row.event_count == 3
        assert "SYNTHETIC_EXACT_CONFIGURATION_INTERFACE_PASS" in row.conformance_result
        row.semantic_payload()


def test_all_22_receipts_are_exact_accepted_types_and_validate_individually() -> None:
    retail, physionet = _fixtures()
    receipts = stack.build_synthetic_adapter_receipts(
        retail_configuration=retail,
        physionet_configuration=physionet,
        module_source_sha256=_source_sha256(),
    )
    assert len(receipts) == 22
    assert all(type(receipt) is b12.AdapterReceipt for receipt in receipts)
    assert tuple(
        (receipt.adapter_id, receipt.domain_id, receipt.config_sha256)
        for receipt in receipts
    ) == stack.ADAPTER_ROSTER_SNAPSHOT
    for receipt in receipts:
        receipt.validate()
        assert (
            receipt.predicate.authentication_method_id
            == "DETERMINISTIC_LOCAL_SYNTHETIC_INTERFACE_QUALIFICATION_NOT_INDEPENDENT_V1"
        )
        assert (
            receipt.predicate.reviewer_principal_id
            == "LOCAL_SYNTHETIC_INTERFACE_QUALIFIER_NOT_INDEPENDENT"
        )


def test_config_source_output_and_record_mutations_fail_closed() -> None:
    record = _manifest()[12]
    legacy_hash = stack.LEGACY_PARTIAL_ROSTER_SNAPSHOT[12][2]
    assert legacy_hash != record.config_sha256
    with pytest.raises(stack.B12AdapterStackError):
        replace(record, config_sha256=legacy_hash).semantic_payload()
    with pytest.raises(stack.B12AdapterStackError):
        replace(record, implementation_source_sha256="1" * 64).semantic_payload()
    with pytest.raises(stack.B12AdapterStackError):
        replace(record, output_sha256="2" * 64).semantic_payload()
    with pytest.raises(stack.B12AdapterStackError):
        replace(record, record_sha256="3" * 64).semantic_payload()
    altered_receipt = replace(record.receipt, config_sha256=legacy_hash)
    with pytest.raises(ValueError):
        altered_receipt.validate()


@pytest.mark.parametrize("bad", ["0" * 64, "A" * 64, "1" * 63, "  " + "1" * 62])
def test_module_source_digest_must_be_exact_nonzero_lowercase(bad: str) -> None:
    retail, physionet = _fixtures()
    with pytest.raises((TypeError, stack.B12AdapterStackError)):
        stack.build_synthetic_conformance_manifest(
            retail_configuration=retail,
            physionet_configuration=physionet,
            module_source_sha256=bad,
        )


def test_public_alias_mutation_cannot_change_corrected_private_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = stack.ADAPTER_ROSTER_SNAPSHOT
    monkeypatch.setattr(b12, "REQUIRED_ADAPTER_ROSTER", ())
    monkeypatch.setattr(stack, "ADAPTER_ROSTER_SNAPSHOT", ())
    assert tuple(
        (row.adapter_id, row.domain_id, row.config_sha256) for row in _manifest()
    ) == before


def test_author_extension_interfaces_are_exact_eight_and_remain_open() -> None:
    obligations = stack.AUTHOR_EXTENSION_OBLIGATIONS
    assert len(obligations) == 8
    assert tuple(value.predicate_id for value in obligations) == tuple(
        [f"CSDI_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
        + [f"EDITPP_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
    )
    assert len({value.extension_id for value in obligations}) == 8
    for value in obligations:
        value.validate()
        assert value.status == "OPEN_IMPLEMENTATION_AND_RUNTIME_EVIDENCE_ABSENT"
        assert value.upstream_execution_claimed is False
        assert value.domain_scale_qualification_claimed is False
        with pytest.raises(stack.B12AdapterStackError):
            replace(value, status="CLOSED").validate()


def test_source_has_no_io_entropy_network_training_or_subprocess_import() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "http",
            "multiprocessing",
            "numpy",
            "os",
            "pathlib",
            "random",
            "requests",
            "secrets",
            "socket",
            "subprocess",
            "torch",
            "urllib",
        }
    )


def test_manifest_is_deterministic_and_input_sensitive() -> None:
    first = _manifest()
    second = _manifest()
    assert first == second
    retail, physionet = _fixtures()
    changed_retail = ExactConfiguration(RETAIL_DOMAIN_ID, retail.events[:-1])
    changed = stack.build_synthetic_conformance_manifest(
        retail_configuration=changed_retail,
        physionet_configuration=physionet,
        module_source_sha256=_source_sha256(),
    )
    for original, replacement in zip(first, changed):
        if original.domain_id == stack.RETAIL_B06_DOMAIN_ID:
            assert original.input_sha256 != replacement.input_sha256
            assert original.output_sha256 != replacement.output_sha256
        else:
            assert original == replacement
