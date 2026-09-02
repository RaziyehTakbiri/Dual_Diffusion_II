"""Hostile qualification tests for the offline B12 integration stack."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path

import pytest

from heterodiff.evaluation import b12_independent_component_recomputation as independent
from heterodiff.evaluation import b12_integrated_offline_candidate as v2
from heterodiff.evaluation import b12_integration_stack as stack
from heterodiff.evaluation import b12_two_domain_adapter_stack as adapters


ROOT = Path(__file__).resolve().parents[2]


def _domain_sha(domain: str, value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + raw).hexdigest()


def _authentication(label: str = "GENERAL") -> stack.ReceiptAuthentication:
    return stack.ReceiptAuthentication(
        reviewer_principal_id="LOCAL-SYNTHETIC-" + label,
        authentication_method_id="DETERMINISTIC-OFFLINE-QUALIFICATION-V1",
        authentication_evidence_sha256=hashlib.sha256(
            ("b12-test-auth:" + label).encode("ascii")
        ).hexdigest(),
    )


def _runtime_mapping(generation: int = 1, predecessor: str = stack.ZERO_SHA256):
    payload = {
        "capacity_receipt_sha256": hashlib.sha256(b"capacity").hexdigest(),
        "deterministic_settings_sha256": hashlib.sha256(b"settings").hexdigest(),
        "generation": generation,
        "hardware_receipt_sha256": hashlib.sha256(b"hardware").hexdigest(),
        "lockfile_sha256": hashlib.sha256(b"lockfile").hexdigest(),
        "predecessor_binding_sha256": predecessor,
        "runtime_identity_id": "CALLER-SUPPLIED-RUNTIME-IDENTITY-TEST",
        "schema_version": stack.RUNTIME_IDENTITY_SCHEMA,
        "software_environment_sha256": hashlib.sha256(b"environment").hexdigest(),
    }
    result = dict(payload)
    result["binding_sha256"] = _domain_sha(
        "heterodiff-b12-runtime-identity-binding-v1", payload
    )
    return dict(sorted(result.items()))


def _ledger_event(
    ordinal: int,
    kind: str,
    previous: str,
    *,
    operation_id: str = "OPERATION",
    request_sha256: str = stack.ZERO_SHA256,
    observation_sha256=None,
):
    payload = {
        "event_kind": kind,
        "observation_sha256": observation_sha256,
        "operation_id": operation_id,
        "ordinal": ordinal,
        "previous_event_sha256": previous,
        "request_sha256": request_sha256,
    }
    return v2.LedgerEvent(
        ordinal=ordinal,
        event_kind=kind,
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=observation_sha256,
        previous_event_sha256=previous,
        event_sha256=v2.sha("heterodiff-b12-ledger-event-v1", payload),
    )


@pytest.fixture(scope="module")
def component_bindings():
    return stack.build_component_bindings(str(ROOT))


@pytest.fixture(scope="module")
def bound_outputs(component_bindings):
    return stack.run_and_independently_recompute(str(ROOT), component_bindings)


@pytest.fixture(scope="module")
def adapter_binding():
    return stack.build_synthetic_adapter_manifest_binding(str(ROOT))


@pytest.fixture(scope="module")
def capsule_plan(component_bindings):
    return stack.build_closed_world_capsule_plan(
        str(ROOT),
        "B12-OFFLINE-SYNTHETIC-CAPSULE-V1",
        stack.DEFAULT_CAPSULE_SOURCE_PATHS,
        component_bindings,
        _authentication("CAPSULE"),
    )


@pytest.fixture(scope="module")
def runner_parts(
    tmp_path_factory, capsule_plan, adapter_binding, bound_outputs
):
    parent = tmp_path_factory.mktemp("b12-runner-ledger")
    ledger_root = stack.create_durable_ledger(str(parent.resolve()), "ledger")
    stack.append_ledger_pair(
        ledger_root,
        "B12-SYNTHETIC-COMPONENT-OPERATION",
        bound_outputs.binding_document_bytes,
        bound_outputs.candidate_output_bytes,
    )
    ledger = stack.replay_durable_ledger(ledger_root).events
    execution_subject = stack.compute_execution_subject_v3(
        capsule_plan.receipt, adapter_binding, ledger, None
    )
    recomputation = stack.build_recomputation_receipt(
        execution_subject, bound_outputs, _authentication("RECOMPUTATION")
    )
    return capsule_plan.receipt, adapter_binding, ledger, recomputation


def test_runtime_identity_future_seam_is_exact_and_freshness_checked():
    mapping = _runtime_mapping()
    binding = stack.RuntimeIdentityBinding.from_mapping(mapping)
    binding.validate_fresh(1, stack.ZERO_SHA256)
    assert binding.runtime_identity_id == "CALLER-SUPPLIED-RUNTIME-IDENTITY-TEST"

    predecessor = binding.binding_sha256
    successor_mapping = _runtime_mapping(2, predecessor)
    successor = stack.RuntimeIdentityBinding.from_mapping(successor_mapping)
    successor.validate_fresh(2, predecessor)
    with pytest.raises(stack.B12IntegrationError, match="stale"):
        successor.validate_fresh(1, stack.ZERO_SHA256)


@pytest.mark.parametrize("mutation", ["missing", "extra", "zero", "bool", "subclass"])
def test_runtime_identity_rejects_missing_extra_zero_and_wrong_exact_types(mutation):
    mapping = _runtime_mapping()
    if mutation == "missing":
        mapping.pop("capacity_receipt_sha256")
    elif mutation == "extra":
        mapping["authority"] = True
    elif mutation == "zero":
        mapping["hardware_receipt_sha256"] = stack.ZERO_SHA256
    elif mutation == "bool":
        mapping["generation"] = True
    else:
        class Text(str):
            pass

        mapping["runtime_identity_id"] = Text(mapping["runtime_identity_id"])
    with pytest.raises((TypeError, stack.B12IntegrationError)):
        stack.RuntimeIdentityBinding.from_mapping(dict(sorted(mapping.items())))


def test_runtime_identity_rejects_subclass_and_duck():
    real = stack.RuntimeIdentityBinding.from_mapping(_runtime_mapping())

    class Subclass(stack.RuntimeIdentityBinding):
        pass

    subclass = Subclass(
        *[getattr(real, field.name) for field in dataclasses.fields(real)]
    )
    with pytest.raises(TypeError, match="concrete"):
        subclass.payload()

    class Duck(dict):
        pass

    with pytest.raises(stack.B12IntegrationError):
        stack.RuntimeIdentityBinding.from_mapping(Duck(_runtime_mapping()))


def test_component_bindings_are_exact_and_sources_are_reopened(component_bindings):
    assert len(component_bindings) == 4
    assert tuple(binding.ordinal for binding in component_bindings) == (0, 1, 2, 3)
    assert all(binding.validate_source(str(ROOT)) for binding in component_bindings)
    document = stack.component_binding_document_bytes(component_bindings)
    assert json.loads(document)["schema_version"] == stack.COMPONENT_BINDING_DOCUMENT_SCHEMA


def test_component_binding_rejects_subclass_duck_and_cross_binding(component_bindings):
    real = component_bindings[0]

    class Subclass(stack.ComponentBinding):
        pass

    subclass = Subclass(
        *[getattr(real, field.name) for field in dataclasses.fields(real)]
    )
    with pytest.raises(TypeError, match="concrete"):
        stack.component_binding_document_bytes((subclass,) + component_bindings[1:])
    with pytest.raises(TypeError):
        stack.component_binding_document_bytes((object(),) + component_bindings[1:])
    crossed = dataclasses.replace(
        component_bindings[0], source_sha256=component_bindings[1].source_sha256
    )
    with pytest.raises(stack.B12IntegrationError):
        crossed.validate_source(str(ROOT))


def test_primary_and_separate_recomputation_match_without_closure(bound_outputs):
    bound_outputs.validate()
    assert bound_outputs.candidate_output_bytes == bound_outputs.independent_output_bytes
    document = json.loads(bound_outputs.candidate_output_bytes)
    assert document["effects"] == {
        "authority_created": False,
        "blocker_delta": 0,
        "data_accessed": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "result_delta": 0,
        "science_executed": False,
        "tracker_edited": False,
    }
    assert document["formal_test29"]["closed"] is False
    assert document["formal_test30"]["closed"] is False
    assert document["single_macrostep"]["formal_tests_closed"] == 0
    assert document["two_macrostep"]["formal_tests_closed"] == 0


def test_independent_recomputation_rejects_resigned_source_substitution(bound_outputs):
    document = json.loads(bound_outputs.binding_document_bytes)
    document["bindings"][0]["source_sha256"] = "1" * 64
    body = dict(document["bindings"][0])
    body.pop("interface_sha256")
    document["bindings"][0]["interface_sha256"] = _domain_sha(
        "heterodiff-b12-component-binding-v1", body
    )
    raw = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii") + b"\n"
    with pytest.raises(independent.IndependentRecomputationError):
        independent.independently_recompute_component_output(str(ROOT), raw)
    with pytest.raises(independent.IndependentRecomputationError, match="canonical"):
        independent.independently_recompute_component_output(
            str(ROOT) + "/", bound_outputs.binding_document_bytes
        )


def test_bound_output_pair_rejects_tamper_and_subclass(bound_outputs):
    tampered = dataclasses.replace(
        bound_outputs,
        independent_output_bytes=b"{}\n",
        independent_output_sha256=hashlib.sha256(b"{}\n").hexdigest(),
    )
    with pytest.raises(stack.B12IntegrationError, match="differs"):
        tampered.validate()

    class Subclass(stack.BoundOutputPair):
        pass

    subclass = Subclass(
        *[getattr(bound_outputs, field.name) for field in dataclasses.fields(bound_outputs)]
    )
    with pytest.raises(TypeError, match="concrete"):
        subclass.validate()


def test_closed_world_capsule_round_trip_is_exact(tmp_path, capsule_plan):
    capsule_root = stack.write_closed_world_capsule(
        capsule_plan, str(tmp_path.resolve()), "capsule"
    )
    reopened = stack.validate_closed_world_capsule(capsule_root, capsule_plan)
    assert reopened == capsule_plan
    assert len(reopened.files) == len(stack.DEFAULT_CAPSULE_SOURCE_PATHS)
    assert reopened.receipt.manifest_sha256 == capsule_plan.receipt.manifest_sha256
    binding_payload = Path(capsule_root) / stack.COMPONENT_BINDING_PAYLOAD_NAME
    assert binding_payload.read_bytes() == capsule_plan.component_binding_document_bytes
    assert (
        reopened.receipt.ordered_file_sha256s[-1]
        == capsule_plan.component_binding_document_sha256
    )
    manifest = json.loads(reopened.manifest_bytes)
    assert manifest["scope"] == stack.CAPSULE_SCOPE
    assert "STANDALONE_EXECUTABLE" in manifest["scope"]


def test_capsule_rejects_partial_crash_and_pending_file(tmp_path, capsule_plan):
    partial = tmp_path / "partial"
    partial.mkdir(mode=0o700)
    pending = partial / ".000.payload.pending"
    pending.write_bytes(capsule_plan.files[0].raw_bytes[:17])
    pending.chmod(0o600)
    with pytest.raises(stack.B12IntegrationError, match="partial|unfinalized"):
        stack.validate_closed_world_capsule(str(partial.resolve()))


@pytest.mark.parametrize(
    "attack",
    [
        "tamper",
        "binding_tamper",
        "binding_missing",
        "extra",
        "mode",
        "hardlink",
        "symlink",
        "root_symlink",
    ],
)
def test_capsule_rejects_payload_custody_and_closed_world_attacks(
    tmp_path, capsule_plan, attack
):
    capsule_root = Path(
        stack.write_closed_world_capsule(
            capsule_plan, str(tmp_path.resolve()), "capsule"
        )
    )
    payload = capsule_root / capsule_plan.files[0].payload_name
    if attack == "tamper":
        raw = payload.read_bytes()
        payload.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        payload.chmod(0o600)
    elif attack == "binding_tamper":
        binding = capsule_root / stack.COMPONENT_BINDING_PAYLOAD_NAME
        raw = binding.read_bytes()
        binding.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        binding.chmod(0o600)
    elif attack == "binding_missing":
        (capsule_root / stack.COMPONENT_BINDING_PAYLOAD_NAME).unlink()
    elif attack == "extra":
        extra = capsule_root / "foreign.payload"
        extra.write_bytes(b"foreign")
        extra.chmod(0o600)
    elif attack == "mode":
        payload.chmod(0o644)
    elif attack == "hardlink":
        os.link(payload, tmp_path / "payload-alias")
    elif attack == "symlink":
        payload.unlink()
        payload.symlink_to(ROOT / capsule_plan.files[0].source_path)
    else:
        alias = tmp_path / "capsule-alias"
        alias.symlink_to(capsule_root, target_is_directory=True)
        with pytest.raises((OSError, stack.B12IntegrationError)):
            stack.validate_closed_world_capsule(str(alias.absolute()))
        return
    with pytest.raises((OSError, stack.B12IntegrationError)):
        stack.validate_closed_world_capsule(str(capsule_root.resolve()))


def test_capsule_rejects_path_escape_type_duck_subclass_and_cross_plan(
    tmp_path, capsule_plan, component_bindings
):
    with pytest.raises(stack.B12IntegrationError, match="escapes"):
        stack.build_closed_world_capsule_plan(
            str(ROOT),
            "CAPSULE",
            ("../outside",),
            component_bindings,
            _authentication(),
        )
    for alias in (
        "src//heterodiff/evaluation/b12_integration_stack.py",
        "src/./heterodiff/evaluation/b12_integration_stack.py",
        "src/heterodiff/evaluation/b12_integration_stack.py/",
    ):
        with pytest.raises(stack.B12IntegrationError, match="noncanonical"):
            stack.build_closed_world_capsule_plan(
                str(ROOT),
                "NONCANONICAL-PATH-CAPSULE",
                (alias,),
                component_bindings,
                _authentication(),
            )
    with pytest.raises(stack.B12IntegrationError, match="canonical"):
        stack.build_component_bindings(str(ROOT) + "/")
    with pytest.raises(TypeError):
        stack.write_closed_world_capsule(object(), str(tmp_path.resolve()), "x")

    class Subclass(stack.ClosedWorldCapsulePlan):
        pass

    subclass = Subclass(
        *[getattr(capsule_plan, field.name) for field in dataclasses.fields(capsule_plan)]
    )
    with pytest.raises(TypeError, match="concrete"):
        stack.write_closed_world_capsule(
            subclass, str(tmp_path.resolve()), "subclass"
        )

    capsule_root = stack.write_closed_world_capsule(
        capsule_plan, str(tmp_path.resolve()), "capsule"
    )
    other = stack.build_closed_world_capsule_plan(
        str(ROOT),
        "B12-OFFLINE-CROSSED-CAPSULE-V1",
        stack.DEFAULT_CAPSULE_SOURCE_PATHS,
        component_bindings,
        _authentication("OTHER"),
    )
    with pytest.raises(stack.B12IntegrationError, match="expected plan"):
        stack.validate_closed_world_capsule(capsule_root, other)


def test_capsule_rejects_duplicate_digest_roster(component_bindings):
    duplicate_paths = (
        stack.DEFAULT_CAPSULE_SOURCE_PATHS[0],
        stack.DEFAULT_CAPSULE_SOURCE_PATHS[0],
    )
    with pytest.raises(stack.B12IntegrationError, match="duplicates"):
        stack.build_closed_world_capsule_plan(
            str(ROOT),
            "DUPLICATE-CAPSULE",
            duplicate_paths,
            component_bindings,
            _authentication(),
        )


def test_ledger_crash_after_intent_is_durable_and_replayable(tmp_path):
    ledger_root = stack.create_durable_ledger(str(tmp_path.resolve()), "ledger")
    intent = stack.append_ledger_intent(ledger_root, "OP-ONE", b"request")
    replay = stack.replay_durable_ledger(
        ledger_root, require_complete=False, allow_empty=False
    )
    assert replay.events == (intent,)
    assert replay.complete_pairs is False
    with pytest.raises(stack.B12IntegrationError, match="without OUTCOME"):
        stack.replay_durable_ledger(ledger_root)
    outcome = stack.append_ledger_outcome(
        ledger_root, "OP-ONE", b"request", b"outcome"
    )
    replay = stack.replay_durable_ledger(ledger_root)
    assert replay.events == (intent, outcome)
    assert replay.complete_pairs is True and replay.pair_count == 1


def test_ledger_rejects_cross_pair_before_outcome_write(tmp_path):
    ledger_root = stack.create_durable_ledger(str(tmp_path.resolve()), "ledger")
    stack.append_ledger_intent(ledger_root, "OP-ONE", b"request")
    with pytest.raises(stack.B12IntegrationError, match="does not match"):
        stack.append_ledger_outcome(
            ledger_root, "OP-TWO", b"request", b"outcome"
        )
    with pytest.raises(stack.B12IntegrationError, match="does not match"):
        stack.append_ledger_outcome(
            ledger_root, "OP-ONE", b"different-request", b"outcome"
        )
    assert not stack.replay_durable_ledger(
        ledger_root, require_complete=False
    ).complete_pairs


@pytest.mark.parametrize("attack", ["tamper", "pending", "gap", "mode", "hardlink", "symlink", "root_symlink"])
def test_ledger_rejects_tamper_partial_path_and_link_attacks(tmp_path, attack):
    ledger_root = Path(
        stack.create_durable_ledger(str(tmp_path.resolve()), "ledger")
    )
    stack.append_ledger_pair(
        str(ledger_root), "OP-ONE", b"request", b"outcome"
    )
    first = ledger_root / "00000000000000000000.json"
    if attack == "tamper":
        document = json.loads(first.read_bytes())
        document["operation_id"] = "FOREIGN"
        first.write_bytes(
            json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
            + b"\n"
        )
        first.chmod(0o600)
    elif attack == "pending":
        pending = ledger_root / ".00000000000000000002.json.pending"
        pending.write_bytes(b"partial")
        pending.chmod(0o600)
    elif attack == "gap":
        first.rename(ledger_root / "00000000000000000007.json")
    elif attack == "mode":
        first.chmod(0o644)
    elif attack == "hardlink":
        os.link(first, tmp_path / "ledger-event-alias")
    elif attack == "symlink":
        raw_copy = tmp_path / "event-copy"
        raw_copy.write_bytes(first.read_bytes())
        raw_copy.chmod(0o600)
        first.unlink()
        first.symlink_to(raw_copy)
    else:
        alias = tmp_path / "ledger-alias"
        alias.symlink_to(ledger_root, target_is_directory=True)
        with pytest.raises((OSError, stack.B12IntegrationError)):
            stack.replay_durable_ledger(str(alias.absolute()))
        return
    with pytest.raises((OSError, stack.B12IntegrationError, ValueError)):
        stack.replay_durable_ledger(str(ledger_root.resolve()))


def test_ledger_replay_rejects_coherently_resigned_ordinal_previous_and_pair_mismatch():
    intent = _ledger_event(0, "INTENT", stack.ZERO_SHA256)
    wrong_ordinal = _ledger_event(2, "OUTCOME", intent.event_sha256,
                                  observation_sha256=stack.ZERO_SHA256)
    with pytest.raises(stack.B12IntegrationError, match="ordinal"):
        stack.DurableLedgerReplay(
            (intent, wrong_ordinal), True, 1, wrong_ordinal.event_sha256
        ).validate()

    wrong_previous = _ledger_event(
        1, "OUTCOME", "1" * 64, observation_sha256=stack.ZERO_SHA256
    )
    with pytest.raises(stack.B12IntegrationError, match="previous-event"):
        stack.DurableLedgerReplay(
            (intent, wrong_previous), True, 1, wrong_previous.event_sha256
        ).validate()

    crossed = _ledger_event(
        1,
        "OUTCOME",
        intent.event_sha256,
        operation_id="FOREIGN",
        observation_sha256=stack.ZERO_SHA256,
    )
    with pytest.raises(stack.B12IntegrationError, match="cross-binding"):
        stack.DurableLedgerReplay(
            (intent, crossed), True, 1, crossed.event_sha256
        ).validate()


def test_ledger_rejects_wrong_types_duck_and_subclass(tmp_path):
    ledger_root = stack.create_durable_ledger(str(tmp_path.resolve()), "ledger")

    class Text(str):
        pass

    with pytest.raises(TypeError):
        stack.append_ledger_intent(ledger_root, Text("OP"), b"request")
    with pytest.raises(TypeError):
        stack.replay_durable_ledger(ledger_root, require_complete=1)

    intent = _ledger_event(0, "INTENT", stack.ZERO_SHA256)

    class Subclass(v2.LedgerEvent):
        pass

    subclass = Subclass(
        *[getattr(intent, field.name) for field in dataclasses.fields(intent)]
    )
    with pytest.raises(TypeError, match="exact accepted"):
        stack.DurableLedgerReplay(
            (subclass,), False, 0, subclass.event_sha256
        ).validate()
    with pytest.raises(TypeError):
        stack.DurableLedgerReplay(
            (object(),), False, 0, stack.ZERO_SHA256
        ).validate()


def test_corrected_adapter_manifest_is_exact_22_and_legacy_mismatch_is_rejected(
    adapter_binding,
):
    adapter_binding.validate()
    triples = tuple(
        (receipt.adapter_id, receipt.domain_id, receipt.config_sha256)
        for receipt in adapter_binding.receipts
    )
    assert triples == adapters.ADAPTER_ROSTER_SNAPSHOT
    assert adapters.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS == tuple(range(12, 20))
    assert triples != v2.REQUIRED_ADAPTER_ROSTER
    assert len(set(adapter_binding.adapter_subject_sha256s)) == 22

    legacy_receipts = []
    for receipt, legacy_row in zip(
        adapter_binding.receipts, adapters.LEGACY_PARTIAL_ROSTER_SNAPSHOT
    ):
        adapter_id, domain_id, config_sha256 = legacy_row
        subject = v2.sha(
            "heterodiff-b12-adapter-subject-v1",
            {
                "adapter_id": adapter_id,
                "config_sha256": config_sha256,
                "domain_id": domain_id,
                "implementation_source_sha256": receipt.implementation_source_sha256,
                "input_sha256": receipt.input_sha256,
                "output_sha256": receipt.output_sha256,
            },
        )
        predicate = stack.build_authenticated_predicate(
            "ADAPTER_RECEIPT:" + adapter_id + ":" + domain_id,
            subject,
            _authentication("LEGACY-HOSTILE"),
        )
        legacy_receipts.append(
            v2.AdapterReceipt(
                adapter_id=adapter_id,
                domain_id=domain_id,
                config_sha256=config_sha256,
                implementation_source_sha256=receipt.implementation_source_sha256,
                input_sha256=receipt.input_sha256,
                output_sha256=receipt.output_sha256,
                predicate=predicate,
            )
        )
    with pytest.raises(stack.B12IntegrationError, match="legacy B12 v2"):
        stack.validate_adapter_receipt_manifest(tuple(legacy_receipts))


def test_adapter_manifest_rejects_order_type_duck_and_subclass(adapter_binding):
    with pytest.raises(stack.B12IntegrationError, match="roster"):
        stack.validate_adapter_receipt_manifest(
            (adapter_binding.receipts[1], adapter_binding.receipts[0])
            + adapter_binding.receipts[2:]
        )
    with pytest.raises(TypeError):
        stack.validate_adapter_receipt_manifest(
            (object(),) + adapter_binding.receipts[1:]
        )

    real = adapter_binding.receipts[0]

    class Subclass(v2.AdapterReceipt):
        pass

    subclass = Subclass(
        *[getattr(real, field.name) for field in dataclasses.fields(real)]
    )
    with pytest.raises(TypeError):
        stack.validate_adapter_receipt_manifest(
            (subclass,) + adapter_binding.receipts[1:]
        )

    class BindingSubclass(stack.AdapterManifestBinding):
        pass

    manifest_subclass = BindingSubclass(
        *[
            getattr(adapter_binding, field.name)
            for field in dataclasses.fields(adapter_binding)
        ]
    )
    with pytest.raises(TypeError, match="concrete"):
        manifest_subclass.validate()


def test_integrated_runner_binds_22_adapters_50_predicates_and_stays_open(
    runner_parts,
):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    runner = stack.build_open_integrated_runner_exercise(
        capsule, adapter_binding, ledger, recomputation
    )
    status = runner.status()
    assert len(runner.adapters.receipts) == 22
    assert len(runner.predicate_slots) == 50
    assert tuple(slot.predicate_id for slot in runner.predicate_slots) == (
        stack.residual_predicate_ids()
    )
    assert all(slot.receipt is None for slot in runner.predicate_slots)
    assert all(slot.state() == "OPEN_RECEIPT_ABSENT" for slot in runner.predicate_slots)
    assert status == {
        "b12_closed": False,
        "blocker_delta": 0,
        "field_delta": 0,
        "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
        "residual_receipts_missing": 50,
        "residual_receipts_present": 0,
        "result_delta": 0,
        "runtime_identity_present": False,
        "science_executed": False,
        "state": stack.RUNNER_STATE,
    }


def test_runner_rejects_predicate_subject_and_roster_cross_binding(runner_parts):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    runner = stack.build_open_integrated_runner_exercise(
        capsule, adapter_binding, ledger, recomputation
    )
    wrong = dataclasses.replace(
        runner.predicate_slots[0], expected_subject_sha256="1" * 64
    )
    with pytest.raises(stack.B12IntegrationError, match="subject"):
        dataclasses.replace(
            runner, predicate_slots=(wrong,) + runner.predicate_slots[1:]
        ).validate()
    with pytest.raises(stack.B12IntegrationError, match="roster"):
        dataclasses.replace(
            runner, predicate_slots=runner.predicate_slots[:-1]
        ).validate()


def test_real_residual_receipts_cannot_be_locally_minted(runner_parts):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    runner = stack.build_open_integrated_runner_exercise(
        capsule, adapter_binding, ledger, recomputation
    )
    with pytest.raises(stack.B12IntegrationError, match="caller supplied"):
        stack.build_authenticated_predicate(
            stack.residual_predicate_ids()[0],
            runner.predicate_slots[0].expected_subject_sha256,
            _authentication("FORBIDDEN-REAL-RESIDUAL"),
        )
    assert all(slot.receipt is None for slot in runner.predicate_slots)


def test_production_runner_rejects_missing_runtime_and_synthetic_authentication(
    runner_parts, bound_outputs
):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    with pytest.raises(stack.B12IntegrationError, match="runtime identity"):
        stack.build_integrated_runner_receipt(
            capsule, adapter_binding, ledger, recomputation, ()
        )

    runtime = stack.RuntimeIdentityBinding.from_mapping(_runtime_mapping())
    production_execution_subject = stack.compute_execution_subject_v3(
        capsule, adapter_binding, ledger, runtime
    )
    production_recomputation = stack.build_recomputation_receipt(
        production_execution_subject,
        bound_outputs,
        _authentication("HOSTILE-PRODUCTION-RECOMPUTATION"),
    )
    production_runner_subject = stack.compute_runner_subject_v3(
        capsule,
        adapter_binding,
        ledger,
        production_recomputation,
        runtime,
    )
    hostile_real_receipts = []
    for predicate_id in stack.residual_predicate_ids():
        payload = {
            "authentication_evidence_sha256": hashlib.sha256(
                ("hostile-real-residual:" + predicate_id).encode("ascii")
            ).hexdigest(),
            "authentication_method_id": "OFFLINEAUTH",
            "disposition": "ACCEPT",
            "predicate_id": predicate_id,
            "reviewer_principal_id": "LOCALAUTH",
            "subject_sha256": production_runner_subject,
        }
        hostile_real_receipts.append(
            v2.AuthenticatedPredicateReceipt(
                predicate_id=predicate_id,
                subject_sha256=production_runner_subject,
                reviewer_principal_id="LOCALAUTH",
                authentication_method_id="OFFLINEAUTH",
                authentication_evidence_sha256=payload[
                    "authentication_evidence_sha256"
                ],
                disposition="ACCEPT",
                receipt_sha256=v2.sha(
                    "heterodiff-b12-authenticated-predicate-v1", payload
                ),
            )
        )
    hostile_real_receipts = tuple(hostile_real_receipts)
    assert len(hostile_real_receipts) == 50
    assert tuple(receipt.predicate_id for receipt in hostile_real_receipts) == (
        stack.residual_predicate_ids()
    )
    assert all(
        receipt.subject_sha256 == production_runner_subject
        for receipt in hostile_real_receipts
    )
    with pytest.raises(stack.B12IntegrationError, match="local or synthetic"):
        stack.build_integrated_runner_receipt(
            capsule,
            adapter_binding,
            ledger,
            production_recomputation,
            hostile_real_receipts,
            runtime,
        )

    hostile_identities = (
        ("LOCALAUTH", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNALLOCALAUTH", "EXTERNAL-SIGNATURE-V1"),
        ("SYNTHETICREVIEWER", "EXTERNAL-SIGNATURE-V1"),
        ("trustedSYNTHETICreviewer", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNAL-REVIEWER", "OFFLINEAUTH"),
        ("EXTERNAL-REVIEWER", "EXTERNALOFFLINEAUTH"),
        ("testprincipal", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNALtestprincipal", "EXTERNAL-SIGNATURE-V1"),
    )
    for index, (principal, method) in enumerate(hostile_identities):
        authentication = stack.ReceiptAuthentication(
            reviewer_principal_id=principal,
            authentication_method_id=method,
            authentication_evidence_sha256=hashlib.sha256(
                ("hostile-auth-%d" % index).encode("ascii")
            ).hexdigest(),
        )
        synthetic = stack.build_authenticated_predicate(
            "SYNTHETIC_INTERFACE_EXERCISE:HOSTILE-%d" % index,
            "3" * 64,
            authentication,
        )
        slot = stack.ResidualPredicateSlot(
            synthetic.predicate_id, synthetic.subject_sha256, synthetic
        )
        with pytest.raises(stack.B12IntegrationError, match="local or synthetic"):
            slot.validate(synthetic.predicate_id, synthetic.subject_sha256)
        with pytest.raises(stack.B12IntegrationError, match="local or synthetic"):
            stack.build_integrated_runner_receipt(
                capsule,
                adapter_binding,
                ledger,
                recomputation,
                (synthetic,),
                runtime,
            )

    external_roster_mismatch = stack.build_authenticated_predicate(
        "SYNTHETIC_INTERFACE_EXERCISE:EXTERNAL-ROSTER-MISMATCH",
        "5" * 64,
        stack.ReceiptAuthentication(
            reviewer_principal_id="EXTERNAL-REVIEWER",
            authentication_method_id="EXTERNAL-SIGNATURE-V1",
            authentication_evidence_sha256=hashlib.sha256(
                b"external-roster-mismatch"
            ).hexdigest(),
        ),
    )
    with pytest.raises(stack.B12IntegrationError, match="roster"):
        stack.build_integrated_runner_receipt(
            capsule,
            adapter_binding,
            ledger,
            recomputation,
            (external_roster_mismatch,),
            runtime,
        )


def test_runner_rejects_recomputation_execution_cross_binding(
    runner_parts, bound_outputs
):
    capsule, adapter_binding, ledger, _ = runner_parts
    crossed = stack.build_recomputation_receipt(
        "2" * 64, bound_outputs, _authentication("CROSSED-RECOMPUTATION")
    )
    with pytest.raises(ValueError, match="execution subject"):
        stack.build_open_integrated_runner_exercise(
            capsule, adapter_binding, ledger, crossed
        )


def test_runner_rejects_duck_and_subclass_members(runner_parts):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    runner = stack.build_open_integrated_runner_exercise(
        capsule, adapter_binding, ledger, recomputation
    )

    class SlotSubclass(stack.ResidualPredicateSlot):
        pass

    real_slot = runner.predicate_slots[0]
    slot_subclass = SlotSubclass(
        *[
            getattr(real_slot, field.name)
            for field in dataclasses.fields(real_slot)
        ]
    )
    with pytest.raises(TypeError, match="slot"):
        dataclasses.replace(
            runner,
            predicate_slots=(slot_subclass,) + runner.predicate_slots[1:],
        ).validate()
    with pytest.raises(TypeError, match="slot"):
        dataclasses.replace(
            runner, predicate_slots=(object(),) + runner.predicate_slots[1:]
        ).validate()

    class RunnerSubclass(stack.IntegratedRunnerReceiptV3):
        pass

    subclass = RunnerSubclass(
        *[getattr(runner, field.name) for field in dataclasses.fields(runner)]
    )
    with pytest.raises(TypeError, match="concrete"):
        subclass.validate()


def test_runner_runtime_identity_is_optional_seam_not_a_selection(
    runner_parts,
):
    capsule, adapter_binding, ledger, recomputation = runner_parts
    runtime = stack.RuntimeIdentityBinding.from_mapping(_runtime_mapping())
    execution = stack.compute_execution_subject_v3(
        capsule, adapter_binding, ledger, runtime
    )
    assert execution != stack.compute_execution_subject_v3(
        capsule, adapter_binding, ledger, None
    )
    with pytest.raises(ValueError, match="execution subject"):
        recomputation.validate(execution)
    # The existing recomputation is intentionally bound to the absent-runtime
    # structural exercise and cannot be relabeled as a production runtime run.
    synthetic = stack.build_authenticated_predicate(
        "SYNTHETIC_INTERFACE_EXERCISE:RUNTIME-CROSS-BINDING",
        "4" * 64,
        _authentication("RUNTIME-CROSS-BINDING"),
    )
    with pytest.raises(stack.B12IntegrationError, match="local or synthetic"):
        stack.build_integrated_runner_receipt(
            capsule,
            adapter_binding,
            ledger,
            recomputation,
            (synthetic,),
            runtime,
        )
