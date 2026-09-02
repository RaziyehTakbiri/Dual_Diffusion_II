from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from heterodiff.evaluation import b12_external_author_extension_components as ext
from heterodiff.evaluation import b12_two_domain_adapter_stack as accepted_stack
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    PHYSIONET_DOMAIN_ID,
    RETAIL_DOMAIN_ID,
    ExactConfiguration,
    ExactEvent,
    physionet_event_from_decimal_token,
    retail_event_from_decimal_token,
)
from heterodiff.experiments import two_domain_baseline_registry as b06
from heterodiff.experiments import two_domain_training_checkpoint_plan as training


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/heterodiff/evaluation/b12_external_author_extension_components.py"
MACHINE = (
    ROOT
    / "research/fixtures/manuscript_v3_b12_external_author_extension_components_v1.json"
)
VALIDATOR = (
    ROOT
    / "research/diagnostics/manuscript_v3_b12_external_author_extension_components_v1.py"
)


def _source_sha256() -> str:
    return hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def _fixtures() -> tuple[ExactConfiguration, ExactConfiguration]:
    return ext.qualification_fixture_configurations()


def _adapters() -> tuple[ext.ExternalAuthorAdapter, ext.ExternalAuthorAdapter]:
    retail, physionet = _fixtures()
    source = _source_sha256()
    return (
        ext.build_csdi_author_adapter(
            configuration=physionet,
            module_source_sha256=source,
        ),
        ext.build_editpp_author_adapter(
            configuration=retail,
            module_source_sha256=source,
        ),
    )


def test_manifest_is_exact_eight_and_binds_original_residual_ids() -> None:
    records = ext.build_author_extension_implementation_manifest(
        module_source_sha256=_source_sha256()
    )
    assert len(records) == 8
    assert len({record.record_sha256 for record in records}) == 8
    assert tuple(record.predicate_id for record in records) == tuple(
        [f"CSDI_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
        + [f"EDITPP_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
    )
    assert tuple(record.extension_id for record in records) == tuple(
        obligation.extension_id
        for obligation in accepted_stack.AUTHOR_EXTENSION_OBLIGATIONS
    )
    for record in records:
        record.semantic_payload()
        assert record.status == ext.COMPONENT_STATUS
        assert record.claim_scope == "COMPONENT_IMPLEMENTATION_ONLY"
        assert record.upstream_native_functionality_claimed is False
        assert record.upstream_execution_claimed is False
        assert record.domain_scale_runtime_qualified is False
        assert record.production_receipt_claimed is False
        assert callable(getattr(ext, record.entrypoint))


def test_exact_b06_and_f139_f147_bindings_are_derived_without_roster_drift() -> None:
    b06_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in b06.FROZEN_REGISTRY["external_baselines"]
    }
    training_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in training.executable_configuration_rows()
    }
    expected = (
        (
            ext.CSDI_ADAPTER_ID,
            ext.CSDI_B06_DOMAIN_ID,
            ext.CSDI_B06_CONFIG_SHA256,
            ext.CSDI_TRAINING_CONFIG_SHA256,
        ),
        (
            ext.EDITPP_ADAPTER_ID,
            ext.EDITPP_B06_DOMAIN_ID,
            ext.EDITPP_B06_CONFIG_SHA256,
            ext.EDITPP_TRAINING_CONFIG_SHA256,
        ),
    )
    for method_id, domain_id, config_sha256, executable_sha256 in expected:
        assert b06_rows[(method_id, domain_id)]["config_sha256"] == config_sha256
        assert (
            training_rows[(method_id, domain_id)]["executable_configuration_sha256"]
            == executable_sha256
        )
    assert training.plan_semantics_sha256() == ext.TRAINING_PLAN_SEMANTICS_SHA256
    assert training.f144_semantics_sha256() == ext.F144_SEMANTICS_SHA256


def test_exact_r112_r10_adapters_and_accepted_64d_context() -> None:
    csdi, editpp = _adapters()
    assert csdi.f105_domain_id == PHYSIONET_DOMAIN_ID
    assert editpp.f105_domain_id == RETAIL_DOMAIN_ID
    assert all(len(row.event.coordinates) == 112 for row in csdi.occurrences)
    assert all(len(row.event.coordinates) == 10 for row in editpp.occurrences)
    for adapter in (csdi, editpp):
        adapter.semantic_payload()
        assert len(adapter.context.coordinates) == ext.PRIMARY_CONTEXT_DIMENSION == 64
        assert adapter.context == accepted_stack.encode_exact_context(adapter.configuration)
        assert adapter.context.event_count == len(adapter.occurrences) == 3


def test_tied_duplicate_occurrences_are_separate_and_never_truncated() -> None:
    csdi, editpp = _adapters()
    for adapter in (csdi, editpp):
        duplicate_groups: dict[str, list[ext.OccurrenceChannelRow]] = {}
        for row in adapter.occurrences:
            duplicate_groups.setdefault(row.event_sha256, []).append(row)
        duplicates = next(group for group in duplicate_groups.values() if len(group) == 2)
        assert duplicates[0].event == duplicates[1].event
        assert duplicates[0].event_sha256 == duplicates[1].event_sha256
        assert duplicates[0].serial != duplicates[1].serial
        assert duplicates[0].occurrence_sha256 != duplicates[1].occurrence_sha256
        assert len(adapter.occurrences) == len(adapter.configuration.events)

    shortened = ExactConfiguration(
        PHYSIONET_DOMAIN_ID,
        csdi.configuration.events[:-1],
    )
    changed = ext.build_csdi_author_adapter(
        configuration=shortened,
        module_source_sha256=_source_sha256(),
    )
    assert changed.adapter_sha256 != csdi.adapter_sha256
    assert changed.context.encoding_sha256 != csdi.context.encoding_sha256


def test_csdi_variable_cardinality_decoder_round_trips_empty_one_and_three() -> None:
    _, physionet = _fixtures()
    for configuration in (
        ExactConfiguration(PHYSIONET_DOMAIN_ID, ()),
        ExactConfiguration(PHYSIONET_DOMAIN_ID, physionet.events[:1]),
        physionet,
    ):
        adapter = ext.build_csdi_author_adapter(
            configuration=configuration,
            module_source_sha256=_source_sha256(),
        )
        assert ext.decode_csdi_event_multiset(adapter.occurrences) == configuration

    adapter = ext.build_csdi_author_adapter(
        configuration=physionet,
        module_source_sha256=_source_sha256(),
    )
    # A contiguous prefix is a valid standalone variable-cardinality multiset.
    prefix = adapter.occurrences[:-1]
    assert ext.decode_csdi_event_multiset(prefix) == ExactConfiguration(
        PHYSIONET_DOMAIN_ID,
        tuple(row.event for row in prefix),
    )
    # The same prefix cannot be substituted into its three-event parent adapter.
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(adapter, occurrences=prefix).semantic_payload()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.decode_csdi_event_multiset(adapter.occurrences[1:])
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.decode_csdi_event_multiset(tuple(reversed(adapter.occurrences)))


def test_physionet_semantic_blocks_fail_closed_when_forged() -> None:
    _, physionet = _fixtures()
    valid = physionet.events[0]
    coordinates = list(valid.coordinates)
    coordinates[0] = Fraction(1)
    coordinates[1] = Fraction(1)
    forged = ExactEvent(PHYSIONET_DOMAIN_ID, tuple(coordinates))
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_csdi_author_adapter(
            configuration=ExactConfiguration(PHYSIONET_DOMAIN_ID, (forged,)),
            module_source_sha256=_source_sha256(),
        )

    coordinates = list(valid.coordinates)
    active = coordinates[:37].index(Fraction(1))
    coordinates[38 + active] = Fraction(0)
    coordinates[75 + active] = Fraction(1, 2)
    forged_missing = ExactEvent(PHYSIONET_DOMAIN_ID, tuple(coordinates))
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_csdi_author_adapter(
            configuration=ExactConfiguration(PHYSIONET_DOMAIN_ID, (forged_missing,)),
            module_source_sha256=_source_sha256(),
        )


def test_editpp_structured_heads_are_exact_and_occurrence_associated() -> None:
    _, editpp = _adapters()
    assert len(editpp.retail_mark_heads) == len(editpp.occurrences) == 3
    for row, heads in zip(editpp.occurrences, editpp.retail_mark_heads):
        payload = heads.semantic_payload()
        assert heads.occurrence_serial == row.serial
        assert heads.event_sha256 == row.event_sha256
        assert tuple(
            getattr(heads, name)
            for name in (
                "invoice_token",
                "cancellation",
                "stock_token",
                "description_present",
                "description_token",
                "source_civil_time",
                "quantity",
                "unit_price",
                "country_present",
                "country_token",
            )
        ) == row.event.coordinates
        assert payload["semantics"].endswith("NOT_INVERTED_RAW_SOURCE_TOKENS")
    duplicate_heads = [
        heads
        for heads in editpp.retail_mark_heads
        if heads.event_sha256 == editpp.retail_mark_heads[0].event_sha256
    ]
    assert len(duplicate_heads) == 2
    assert duplicate_heads[0].heads_sha256 != duplicate_heads[1].heads_sha256


def test_fully_redigested_retail_head_coordinate_reassociation_fails_closed() -> None:
    _, editpp = _adapters()
    target = editpp.retail_mark_heads[0]
    donor = editpp.retail_mark_heads[-1]
    coordinate_names = (
        "invoice_token",
        "cancellation",
        "stock_token",
        "description_present",
        "description_token",
        "source_civil_time",
        "quantity",
        "unit_price",
        "country_present",
        "country_token",
    )
    donor_coordinates = tuple(getattr(donor, name) for name in coordinate_names)
    head_payload = target.semantic_payload()
    head_payload["coordinates"] = tuple(
        ext._fraction_payload(value, name="hostile Retail head")
        for value in donor_coordinates
    )
    forged_head = replace(
        target,
        **{name: value for name, value in zip(coordinate_names, donor_coordinates)},
        heads_sha256=ext._digest(
            "heterodiff-b12-editpp-retail-structured-mark-heads-v1",
            head_payload,
        ),
    )
    # The head is internally self-consistent; rejection must come from its
    # coordinate-by-coordinate association to the parent occurrence event.
    forged_head.semantic_payload()
    adapter_payload = editpp.semantic_payload()
    forged_head_payloads = list(adapter_payload["retail_mark_heads"])
    forged_head_payloads[0] = forged_head.semantic_payload()
    adapter_payload["retail_mark_heads"] = tuple(forged_head_payloads)
    forged_adapter = replace(
        editpp,
        retail_mark_heads=(forged_head,) + editpp.retail_mark_heads[1:],
        adapter_sha256=ext._digest(
            "heterodiff-b12-external-author-adapter-v1",
            adapter_payload,
        ),
    )
    with pytest.raises(
        ext.ExternalAuthorExtensionError,
        match="differ from their bound occurrence event",
    ):
        forged_adapter.semantic_payload()


def test_retail_source_civil_and_optional_mark_invariants_fail_closed() -> None:
    retail, _ = _fixtures()
    assert all(Fraction(0) <= event.coordinates[5] < Fraction(1) for event in retail.events)
    valid = retail.events[0]
    coordinates = list(valid.coordinates)
    coordinates[5] = Fraction(1)
    forged_time = ExactEvent(RETAIL_DOMAIN_ID, tuple(coordinates))
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_editpp_author_adapter(
            configuration=ExactConfiguration(RETAIL_DOMAIN_ID, (forged_time,)),
            module_source_sha256=_source_sha256(),
        )

    coordinates = list(valid.coordinates)
    coordinates[3] = Fraction(0)
    coordinates[4] = Fraction(1, 2)
    forged_missing = ExactEvent(RETAIL_DOMAIN_ID, tuple(coordinates))
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_editpp_author_adapter(
            configuration=ExactConfiguration(RETAIL_DOMAIN_ID, (forged_missing,)),
            module_source_sha256=_source_sha256(),
        )


@pytest.mark.parametrize("kind", ["csdi", "editpp"])
def test_arbitrary_subset_masks_are_frozen_and_have_exact_64_empty_slots(kind: str) -> None:
    csdi, editpp = _adapters()
    adapter = csdi if kind == "csdi" else editpp
    builder = (
        ext.build_csdi_conditioning_interface
        if kind == "csdi"
        else ext.build_editpp_conditioning_interface
    )
    for subset in ((), (0,), (1,), (0, 2), tuple(range(len(adapter.occurrences)))):
        interface = builder(
            adapter=adapter,
            observed_occurrence_serials=subset,
        )
        payload = interface.semantic_payload(adapter=adapter)
        assert interface.observation_mask == tuple(
            index in subset for index in range(len(adapter.occurrences))
        )
        assert len(interface.draw_slots) == ext.DRAW_COUNT == 64
        assert tuple(slot.draw_ordinal for slot in interface.draw_slots) == tuple(range(64))
        assert all(slot.status == ext.DRAW_SLOT_STATUS for slot in interface.draw_slots)
        assert all(slot.generated_configuration_sha256 is None for slot in interface.draw_slots)
        assert payload["runtime_output_claimed"] is False


def test_duplicate_subset_association_changes_custody_even_for_equal_events() -> None:
    csdi, _ = _adapters()
    duplicate_serials = [
        row.serial
        for row in csdi.occurrences
        if row.event_sha256 == csdi.occurrences[0].event_sha256
    ]
    assert len(duplicate_serials) == 2
    left = ext.build_csdi_conditioning_interface(
        adapter=csdi,
        observed_occurrence_serials=(duplicate_serials[0],),
    )
    right = ext.build_csdi_conditioning_interface(
        adapter=csdi,
        observed_occurrence_serials=(duplicate_serials[1],),
    )
    assert left.observed_occurrence_sha256s != right.observed_occurrence_sha256s
    assert left.mask_sha256 != right.mask_sha256
    assert left.interface_sha256 != right.interface_sha256


def test_subset_serials_and_cross_adapter_conditioning_fail_closed() -> None:
    csdi, editpp = _adapters()
    for bad in ((1, 0), (0, 0), (-1,), (3,)):
        with pytest.raises((TypeError, ext.ExternalAuthorExtensionError)):
            ext.build_csdi_conditioning_interface(
                adapter=csdi,
                observed_occurrence_serials=bad,
            )
    with pytest.raises(TypeError):
        ext.build_csdi_conditioning_interface(
            adapter=csdi,
            observed_occurrence_serials=[0],  # type: ignore[arg-type]
        )
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_csdi_conditioning_interface(
            adapter=editpp,
            observed_occurrence_serials=(),
        )
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_editpp_conditioning_interface(
            adapter=csdi,
            observed_occurrence_serials=(),
        )


def test_cross_domain_exact_types_and_invalid_source_hashes_fail_closed() -> None:
    retail, physionet = _fixtures()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_csdi_author_adapter(
            configuration=retail,
            module_source_sha256=_source_sha256(),
        )
    with pytest.raises(ext.ExternalAuthorExtensionError):
        ext.build_editpp_author_adapter(
            configuration=physionet,
            module_source_sha256=_source_sha256(),
        )

    class ConfigurationSubclass(ExactConfiguration):
        pass

    subclass = ConfigurationSubclass(PHYSIONET_DOMAIN_ID, ())
    with pytest.raises(TypeError):
        ext.build_csdi_author_adapter(
            configuration=subclass,
            module_source_sha256=_source_sha256(),
        )
    for bad in ("0" * 64, "A" * 64, "f" * 63, "not-a-digest"):
        with pytest.raises(ext.ExternalAuthorExtensionError):
            ext.build_author_extension_implementation_manifest(
                module_source_sha256=bad
            )


def test_adapter_and_occurrence_mutations_are_rejected() -> None:
    csdi, editpp = _adapters()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(csdi, b06_config_sha256="1" * 64).semantic_payload()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(csdi, training_executable_config_sha256="1" * 64).semantic_payload()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(csdi, adapter_sha256="1" * 64).semantic_payload()
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(
            csdi,
            occurrences=csdi.occurrences[:-1],
        ).semantic_payload()
    bad_occurrence = replace(csdi.occurrences[0], occurrence_sha256="1" * 64)
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(
            csdi,
            occurrences=(bad_occurrence,) + csdi.occurrences[1:],
        ).semantic_payload()
    bad_head = replace(editpp.retail_mark_heads[0], heads_sha256="1" * 64)
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(
            editpp,
            retail_mark_heads=(bad_head,) + editpp.retail_mark_heads[1:],
        ).semantic_payload()


def test_conditioning_and_draw_slot_mutations_are_rejected() -> None:
    csdi, _ = _adapters()
    interface = ext.build_csdi_conditioning_interface(
        adapter=csdi,
        observed_occurrence_serials=(0,),
    )
    for forged in (
        replace(interface, mask_sha256="1" * 64),
        replace(interface, interface_sha256="1" * 64),
        replace(interface, observation_mask=(False,) * interface.event_count),
        replace(interface, draw_slots=interface.draw_slots[:-1]),
    ):
        with pytest.raises(ext.ExternalAuthorExtensionError):
            forged.semantic_payload(adapter=csdi)
    bad_slot = replace(interface.draw_slots[0], status="ACCEPT", slot_sha256="1" * 64)
    with pytest.raises(ext.ExternalAuthorExtensionError):
        replace(
            interface,
            draw_slots=(bad_slot,) + interface.draw_slots[1:],
        ).semantic_payload(adapter=csdi)
    minted = replace(
        interface.draw_slots[0],
        generated_configuration_sha256="1" * 64,  # type: ignore[arg-type]
    )
    with pytest.raises(ext.ExternalAuthorExtensionError):
        minted.semantic_payload(
            adapter_id=csdi.adapter_id,
            interface_subject_sha256=interface.interface_subject_sha256,
        )


def test_implementation_claim_widening_is_rejected() -> None:
    record = ext.build_author_extension_implementation_manifest(
        module_source_sha256=_source_sha256()
    )[0]
    for forged in (
        replace(record, status="CLOSED"),
        replace(record, claim_scope="FULL_RUNTIME_CLOSURE"),
        replace(record, upstream_native_functionality_claimed=True),
        replace(record, upstream_execution_claimed=True),
        replace(record, domain_scale_runtime_qualified=True),
        replace(record, production_receipt_claimed=True),
        replace(record, record_sha256="1" * 64),
    ):
        with pytest.raises(ext.ExternalAuthorExtensionError):
            forged.semantic_payload()


def test_public_predecessor_alias_rebinding_cannot_redirect_context_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, physionet = _fixtures()
    baseline = ext.build_csdi_author_adapter(
        configuration=physionet,
        module_source_sha256=_source_sha256(),
    )

    def forbidden(_: ExactConfiguration) -> object:
        raise AssertionError("rebound public alias was called")

    monkeypatch.setattr(accepted_stack, "encode_exact_context", forbidden)
    rebuilt = ext.build_csdi_author_adapter(
        configuration=physionet,
        module_source_sha256=_source_sha256(),
    )
    assert rebuilt == baseline


def test_candidate_semantics_are_deterministic_and_zero_delta() -> None:
    first = ext.candidate_semantics(module_source_sha256=_source_sha256())
    second = ext.candidate_semantics(module_source_sha256=_source_sha256())
    assert first == second
    assert first["component_implementation_predicate_ids"] == tuple(
        [f"CSDI_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
        + [f"EDITPP_AUTHOR_EXTENSION_{index}" for index in range(1, 5)]
    )
    assert first["draw_count_per_interface"] == 64
    assert first["effects"] == {
        "blocker_delta": 0,
        "field_delta": 0,
        "formal_test_delta": 0,
        "result_delta": 0,
        "science_delta": 0,
        "timetable_task_delta": 0,
        "tracker_edited": False,
    }
    assert all(value is False for value in first["nonclaims"].values())


def test_source_has_no_io_network_entropy_training_or_upstream_imports() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            literal_keys = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            ]
            assert len(literal_keys) == len(set(literal_keys))
    imported = set()
    imported_full = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".", 1)[0])
                imported_full.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
            imported_full.add(node.module)
    assert imported.isdisjoint(
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
    assert not any("csdi" in name.lower() or "editpp" in name.lower() for name in imported_full)
    for function in (
        ext.build_csdi_author_adapter,
        ext.decode_csdi_event_multiset,
        ext.build_editpp_author_adapter,
        ext.build_csdi_conditioning_interface,
        ext.build_editpp_conditioning_interface,
    ):
        assert "trunc" not in inspect.signature(function).parameters


def test_f105_factories_produce_values_admitted_by_the_author_adapters() -> None:
    physio = ExactConfiguration(
        PHYSIONET_DOMAIN_ID,
        (
            physionet_event_from_decimal_token(
                elapsed_minutes=2880,
                parameter="Weight",
                value_text="0",
            ),
        ),
    )
    retail = ExactConfiguration(
        RETAIL_DOMAIN_ID,
        (
            retail_event_from_decimal_token(
                invoice_no="c000001",
                stock_code="x",
                description=None,
                quantity=-2,
                invoice_calendar=(2011, 12, 9, 23, 59, 59, 999999),
                unit_price_text="-0.5",
                country="",
            ),
        ),
    )
    assert ext.build_csdi_author_adapter(
        configuration=physio,
        module_source_sha256=_source_sha256(),
    ).f105_domain_id == PHYSIONET_DOMAIN_ID
    assert ext.build_editpp_author_adapter(
        configuration=retail,
        module_source_sha256=_source_sha256(),
    ).f105_domain_id == RETAIL_DOMAIN_ID


def _copy_validator_capsule(destination: Path) -> None:
    machine = json.loads(MACHINE.read_text(encoding="ascii"))
    paths = {
        MACHINE.relative_to(ROOT).as_posix(),
        VALIDATOR.relative_to(ROOT).as_posix(),
        *(binding["path"] for binding in machine["bindings"]),
        *(binding["path"] for binding in machine["predecessor_bindings"]),
    }
    for relative in paths:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)


def _validator_result(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / VALIDATOR.relative_to(ROOT)), "--root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_hash_first_validator_passes_project_root_and_copied_capsule(tmp_path: Path) -> None:
    direct = _validator_result(ROOT)
    assert direct.returncode == 0, direct.stderr
    assert "PASS_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS_ONLY" in direct.stdout
    copied = tmp_path / "capsule"
    _copy_validator_capsule(copied)
    result = _validator_result(copied)
    assert result.returncode == 0, result.stderr


def test_hash_first_validator_refuses_tamper_leaf_or_parent_symlink_and_hardlink(
    tmp_path: Path,
) -> None:
    tampered = tmp_path / "tampered"
    _copy_validator_capsule(tampered)
    source = tampered / SOURCE.relative_to(ROOT)
    source.write_bytes(source.read_bytes() + b"\n")
    assert _validator_result(tampered).returncode != 0

    linked = tmp_path / "linked"
    _copy_validator_capsule(linked)
    machine_path = linked / MACHINE.relative_to(ROOT)
    original = linked / "machine-original.json"
    machine_path.rename(original)
    machine_path.symlink_to(original)
    assert _validator_result(linked).returncode != 0

    parent_linked = tmp_path / "parent-linked"
    _copy_validator_capsule(parent_linked)
    shutil.rmtree(parent_linked / "src")
    (parent_linked / "src").symlink_to(ROOT / "src", target_is_directory=True)
    parent_result = _validator_result(parent_linked)
    assert parent_result.returncode != 0
    assert "cannot safely open parent" in parent_result.stderr

    hardlinked = tmp_path / "hardlinked"
    _copy_validator_capsule(hardlinked)
    human = hardlinked / "PROJECT_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS.md"
    alias = hardlinked / "human-alias.md"
    os.link(human, alias)
    assert _validator_result(hardlinked).returncode != 0
