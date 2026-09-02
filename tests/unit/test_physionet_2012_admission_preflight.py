from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.data import physionet_2012_admission_preflight as preflight


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "src/heterodiff/data/physionet_2012_admission_preflight.py"
PATIENT_COUNT = 854


class IntSubclass(int):
    pass


class StringSubclass(str):
    pass


class EqualityLyingString(str):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = str.__hash__


class TupleSubclass(tuple):
    pass


class DictSubclass(dict):
    pass


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def locator(name: str) -> preflight.PrivateLocator:
    return preflight.PrivateLocator(
        custody_root_id="PHYSIONET-CUSTODY-V1",
        relative_path=f"physionet/{name}",
    )


def real_activation() -> preflight.ActivationReceipt:
    return preflight.ActivationReceipt(
        state=preflight.ACTIVATED_REAL_STATE,
        activation_id="PHYSIONET-B02-ACTIVATION-V1",
        reviewed_precontact_instance_sha256=digest("precontact"),
        independent_precontact_review_sha256=digest("precontact-review"),
        data_access_authority_sha256=digest("data-access-authority"),
        custody_approval_sha256=digest("custody-approval"),
    )


def patient_rows(count: int = PATIENT_COUNT) -> tuple[preflight.PatientRecord, ...]:
    return tuple(
        preflight.PatientRecord(record_ordinal=index, patient_id=str(index + 1))
        for index in range(count)
    )


def file_rows(
    count: int = PATIENT_COUNT,
) -> tuple[preflight.AllowlistedFileReceipt, ...]:
    return tuple(
        preflight.AllowlistedFileReceipt(
            file_ordinal=index,
            source_partition="set-a",
            logical_path=f"set-a/{index + 1}.txt",
            record_id=str(index + 1),
            raw_sha256=digest(f"record-{index + 1}"),
            byte_count=100 + index,
        )
        for index in range(count)
    )


def archive(
    activation: preflight.ActivationReceipt,
) -> preflight.RawArchiveReceipt:
    real = activation.state == preflight.ACTIVATED_REAL_STATE
    return preflight.RawArchiveReceipt(
        activation=activation,
        domain_id=preflight.DOMAIN_ID,
        snapshot_version="PHYSIONET-CHALLENGE-2012-1.0.0-EXACT-ROSTER-V1",
        raw_archive_sha256=digest("raw-archive"),
        raw_archive_bytes=5_000_000,
        source_version_receipt_sha256=digest("source-version"),
        license_access_receipt_sha256=digest("license-access"),
        archive_locator=locator("raw/archive.bin"),
        access_outcome_receipt_sha256=(digest("access-outcome") if real else None),
    )


def snapshot(
    activation: preflight.ActivationReceipt,
    *,
    rows: tuple[preflight.PatientRecord, ...] | None = None,
    files: tuple[preflight.AllowlistedFileReceipt, ...] | None = None,
) -> preflight.SnapshotReceipt:
    real = activation.state == preflight.ACTIVATED_REAL_STATE
    return preflight.SnapshotReceipt(
        activation=activation,
        archive=archive(activation),
        allowlisted_files=file_rows() if files is None else files,
        patient_projection=patient_rows() if rows is None else rows,
        source_schema_receipt_sha256=digest("source-schema"),
        toolchain=preflight.ToolchainIdentity(),
        snapshot_locator=locator("snapshot/manifest.json"),
        snapshot_verification_receipt_sha256=(
            digest("snapshot-verification") if real else None
        ),
    )


def allocation(
    activation: preflight.ActivationReceipt,
) -> preflight.F061Allocation:
    if activation.state == preflight.ACTIVATED_REAL_STATE:
        shared_allocation_id = "TWO-DOMAIN-F061-POWER-REVIEWED-V1"
        shared_power_requirement_id = "TWO-DOMAIN-F061-POWER-REQUIREMENT-V1"
        shared_proposal_sha256 = preflight.shared_f061_policy_proposal_sha256(
            allocation_id=shared_allocation_id,
            values=(60, 20, 20),
            denominator=100,
            minimum_counts=(500, 160, 160),
            rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            power_requirement_id=shared_power_requirement_id,
        )
        shared_review_receipt_sha256 = digest("shared-f061-policy-review")
        shared_definition_sha256 = (
            preflight.shared_f061_policy_definition_sha256(
                allocation_proposal_sha256=shared_proposal_sha256,
                power_review_receipt_sha256=shared_review_receipt_sha256,
                power_review_accepted=True,
            )
        )
        proposal_sha256 = preflight.f061_allocation_proposal_sha256(
            patient_count=PATIENT_COUNT,
            numerators=(60, 20, 20),
            denominator=100,
            counts=(512, 171, 171),
            minimum_counts=(500, 160, 160),
            rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            shared_policy_allocation_id=shared_allocation_id,
            shared_policy_values=(60, 20, 20),
            shared_policy_denominator=100,
            shared_policy_minimum_counts=(500, 160, 160),
            shared_policy_rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            shared_policy_power_requirement_id=shared_power_requirement_id,
            shared_policy_proposal_sha256=shared_proposal_sha256,
            shared_policy_review_receipt_sha256=(
                shared_review_receipt_sha256
            ),
            shared_policy_review_accepted=True,
            shared_policy_definition_sha256=shared_definition_sha256,
            physionet_adapter_id=preflight.PHYSIONET_F061_ADAPTER_ID,
            physionet_adapter_sha256=(
                preflight.PHYSIONET_F061_ADAPTER_SHA256
            ),
        )
        review = preflight.F061ExternalReviewBinding(
            proposal_sha256=proposal_sha256,
            accepted=True,
            review_receipt_sha256=digest("power-review"),
            review_locator=locator("power/f061-review.json"),
        )
        return preflight.make_f061_allocation(
            patient_count=PATIENT_COUNT,
            review_state="POWER_REVIEWED",
            numerators=(60, 20, 20),
            denominator=100,
            counts=(512, 171, 171),
            minimum_counts=(500, 160, 160),
            external_review_binding=review,
            shared_policy_allocation_id=shared_allocation_id,
            shared_policy_values=(60, 20, 20),
            shared_policy_denominator=100,
            shared_policy_minimum_counts=(500, 160, 160),
            shared_policy_rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            shared_policy_power_requirement_id=shared_power_requirement_id,
            shared_policy_proposal_sha256=shared_proposal_sha256,
            shared_policy_review_receipt_sha256=(
                shared_review_receipt_sha256
            ),
            shared_policy_review_accepted=True,
            shared_policy_definition_sha256=shared_definition_sha256,
            physionet_adapter_id=preflight.PHYSIONET_F061_ADAPTER_ID,
            physionet_adapter_sha256=(
                preflight.PHYSIONET_F061_ADAPTER_SHA256
            ),
        )
    return preflight.make_synthetic_candidate_f061_allocation(
        patient_count=PATIENT_COUNT
    )


def split(
    snapshot_receipt: preflight.SnapshotReceipt,
) -> preflight.PatientSplitReceipt:
    return preflight.build_patient_disjoint_split(
        snapshot=snapshot_receipt,
        allocation=allocation(snapshot_receipt.activation),
        split_locator=locator("split/manifest.json"),
        split_verification_receipt_sha256=(
            digest("split-verification")
            if snapshot_receipt.activation.state == preflight.ACTIVATED_REAL_STATE
            else None
        ),
    )


def unresolved_governance(
    activation: preflight.ActivationReceipt,
) -> preflight.GovernanceReceipt:
    return preflight.GovernanceReceipt(
        activation=activation,
        determination_state="UNRESOLVED",
        governance_record_sha256=None,
        accountable_owner_acceptance_sha256=None,
        determination_locator=None,
    )


def approved_governance(
    activation: preflight.ActivationReceipt,
) -> preflight.GovernanceReceipt:
    return preflight.GovernanceReceipt(
        activation=activation,
        determination_state="APPROVED_FOR_FROZEN_PHYSIONET_RESEARCH_USE",
        governance_record_sha256=digest("governance"),
        accountable_owner_acceptance_sha256=digest("owner-acceptance"),
        determination_locator=locator("governance/determination.json"),
    )


def certified_support(
    activation: preflight.ActivationReceipt,
) -> preflight.ObservationSupportReceipt:
    return preflight.ObservationSupportReceipt(
        activation=activation,
        f033_state="CERTIFIED",
        f034_state="CERTIFIED",
        clean_kernel_id=preflight.OBSERVATION_KERNEL_ID,
        common_support_route_id=preflight.COMMON_SUPPORT_ROUTE_ID,
        observation_reference_id="PHYSIONET-OBSERVATION-REFERENCE-V1",
        observation_reference_sha256=digest("observation-reference"),
        full_support_component_id="PHYSIONET-FULL-SUPPORT-COMPONENT-V1",
        full_support_component_sha256=digest("full-support-component"),
        mixture_weight_numerator=1,
        mixture_weight_denominator=100,
        acquisition_justification_receipt_sha256=digest("acquisition-justification"),
        proof_certificate_sha256=digest("support-proof"),
        implementation_certificate_sha256=digest("support-code"),
        independent_review_receipt_sha256=digest("support-review"),
        support_receipt_locator=locator("support/f033-f034.json"),
        clean_kernel_kept_separate=True,
        theorem_convenience_noise_added=False,
    )


def duplicate_audit(
    activation: preflight.ActivationReceipt,
    snapshot_receipt: preflight.SnapshotReceipt,
    split_receipt: preflight.PatientSplitReceipt,
    *,
    exact_count: int = 0,
    near_count: int = 0,
    complete: bool = True,
) -> preflight.DuplicateAuditReceipt:
    real = activation.state == preflight.ACTIVATED_REAL_STATE
    train, validation, test = split_receipt.record_counts
    eligible_pair_count = (
        train * validation + train * test + validation * test
    )
    return preflight.DuplicateAuditReceipt.create(
        activation=activation,
        snapshot=snapshot_receipt,
        split=split_receipt,
        checked_cross_split_record_pair_count=(
            eligible_pair_count if complete else 0
        ),
        complete_roster_checked=complete,
        exact_duplicate_cross_split_count=exact_count,
        near_duplicate_cross_split_count=near_count,
        outcome_or_label_content_inspected=False,
        completion_certificate_sha256=digest("duplicate-audit-certificate"),
        audit_verification_receipt_sha256=(
            digest("duplicate-audit-verification") if real else None
        ),
        audit_locator=locator("audit/duplicates.json"),
    )


def zero_counts() -> preflight.ViolationCountVector:
    return preflight.ViolationCountVector((0,) * len(preflight.ADMISSION_COMPONENTS))


def test_frozen_toolchain_identities_are_exact() -> None:
    identity = preflight.ToolchainIdentity()
    assert identity.to_dict() == {
        "parser_id": preflight.PARSER_ID,
        "parser_source_sha256": preflight.PARSER_SOURCE_SHA256,
        "inventory_id": preflight.INVENTORY_ID,
        "inventory_source_sha256": preflight.INVENTORY_SOURCE_SHA256,
        "f105_transform_id": preflight.F105_TRANSFORM_ID,
        "f105_transform_source_sha256": preflight.F105_TRANSFORM_SOURCE_SHA256,
        "split_algorithm_id": preflight.SPLIT_ALGORITHM_ID,
        "candidate_split_algorithm_id": preflight.CANDIDATE_SPLIT_ALGORITHM_ID,
        "split_contract_sha256": preflight.SPLIT_CONTRACT_SHA256,
    }
    with pytest.raises(preflight.AdmissionPreflightError, match="identity drift"):
        replace(identity, parser_source_sha256=digest("wrong-parser"))
    with pytest.raises(preflight.AdmissionPreflightError, match="identity drift"):
        replace(
            identity,
            split_contract_sha256=(
                preflight.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
            ),
        )


def test_explicit_f061_split_contract_digest_is_canonical_and_non_aliasing() -> None:
    payload = preflight.explicit_f061_split_contract_record()
    implementation = preflight.split_implementation_record()
    implementation_canonical = json.dumps(
        implementation,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    implementation_recomputed = hashlib.sha256(
        preflight.SPLIT_IMPLEMENTATION_DOMAIN + implementation_canonical
    ).hexdigest()
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    recomputed = hashlib.sha256(
        preflight.EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN + canonical
    ).hexdigest()

    assert payload["schema_version"] == preflight.SPLIT_CONTRACT_SCHEMA_VERSION
    assert payload["split_algorithm_id"] == preflight.SPLIT_ALGORITHM_ID
    assert payload["split_implementation_id"] == preflight.SPLIT_IMPLEMENTATION_ID
    assert (
        payload["split_implementation_sha256"]
        == preflight.SPLIT_IMPLEMENTATION_SHA256
    )
    assert payload["split_implementation"] == implementation
    assert implementation_recomputed == preflight.SPLIT_IMPLEMENTATION_SHA256
    assert (
        payload["historical_candidate_algorithm_id"]
        == preflight.CANDIDATE_SPLIT_ALGORITHM_ID
    )
    assert (
        payload["historical_candidate_contract_raw_sha256"]
        == preflight.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
    )
    assert recomputed == preflight.SPLIT_CONTRACT_SHA256
    assert (
        preflight.SPLIT_CONTRACT_SHA256
        != preflight.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
    )

    payload["split_algorithm_id"] = preflight.CANDIDATE_SPLIT_ALGORITHM_ID
    changed = hashlib.sha256(
        preflight.EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN
        + json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    assert changed != preflight.SPLIT_CONTRACT_SHA256
    assert (
        preflight.explicit_f061_split_contract_record()["split_algorithm_id"]
        == preflight.SPLIT_ALGORITHM_ID
    )


def test_split_contract_binds_exact_patient_order_encoding() -> None:
    payload = preflight.explicit_f061_split_contract_record()
    implementation = preflight.split_implementation_record()
    ordering_digest = implementation["ordering_digest"]
    patient_sort = implementation["patient_sort"]

    assert preflight.PATIENT_ORDER_DOMAIN.hex() == (
        "68657465726f646966662f70687973696f6e65742d70617469656e742d6f7264"
        "65722f763100"
    )
    assert preflight.PATIENT_ORDER_DOMAIN_SHA256 == (
        "d1863b21f48a7b8a892b9abe97e5e897ba33086dde1d2423d06b30f1a13a6c32"
    )
    assert ordering_digest == {
        "hash_algorithm": "sha256",
        "domain_bytes_hex": preflight.PATIENT_ORDER_DOMAIN_HEX,
        "domain_bytes_sha256": preflight.PATIENT_ORDER_DOMAIN_SHA256,
        "length_prefix_width_bytes": 2,
        "length_prefix_byteorder": "big",
        "length_prefix_signed": False,
        "message_fields_in_order": [
            "domain_bytes",
            "patient_byte_length_prefix",
            "patient_bytes",
        ],
    }
    assert patient_sort == {
        "primary": "DIGEST_BYTES_ASCENDING",
        "tie_break": "PATIENT_ASCII_BYTES_ASCENDING",
    }
    assert payload["patient_order_domain_bytes_hex"] == (
        preflight.PATIENT_ORDER_DOMAIN_HEX
    )
    assert payload["patient_order_length_prefix_width_bytes"] == 2
    assert payload["patient_order_length_prefix_byteorder"] == "big"
    assert payload["patient_order_length_prefix_signed"] is False
    assert payload["patient_order_patient_encoding"] == "ascii"


@pytest.mark.parametrize(
    ("name", "changed"),
    (
        ("PATIENT_ORDER_DOMAIN", b"changed-domain\x00"),
        ("PATIENT_ORDER_DOMAIN_SHA256", "0" * 64),
        ("PATIENT_ORDER_LENGTH_PREFIX_BYTES", 1),
        ("PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER", "little"),
        ("PATIENT_ORDER_LENGTH_PREFIX_SIGNED", True),
        ("PATIENT_ORDER_PATIENT_ENCODING", "utf-8"),
        ("PATIENT_ORDER_HASH_ALGORITHM", "sha512"),
        ("PATIENT_ORDER_PRIMARY_SORT", "PATIENT_BYTES_ASCENDING"),
        ("PATIENT_ORDER_TIE_BREAK", "NONE"),
    ),
)
def test_split_fails_closed_on_ordering_policy_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    changed: object,
) -> None:
    activation = preflight.synthetic_activation("ORDER-POLICY-DRIFT")
    snapshot_receipt = snapshot(activation)
    f061 = allocation(activation)
    monkeypatch.setattr(preflight, name, changed)
    with pytest.raises(preflight.AdmissionPreflightError, match="identity drift"):
        preflight.build_patient_disjoint_split(
            snapshot=snapshot_receipt,
            allocation=f061,
            split_locator=locator("split/order-policy-drift.json"),
        )


def test_patient_assignment_is_sensitive_to_the_bound_ordering_domain() -> None:
    patient_ids = tuple(str(index + 1) for index in range(PATIENT_COUNT))
    counts = preflight.CANDIDATE_ALLOCATION_NUMERATORS

    def assignment_for(domain: bytes) -> dict[str, str]:
        ordered = sorted(
            patient_ids,
            key=lambda patient_id: (
                hashlib.sha256(
                    domain
                    + len(patient_id.encode("ascii")).to_bytes(
                        2,
                        byteorder="big",
                        signed=False,
                    )
                    + patient_id.encode("ascii")
                ).digest(),
                patient_id.encode("ascii"),
            ),
        )
        resolved_counts = (598, 128, 128)
        result: dict[str, str] = {}
        cursor = 0
        for split_name, count in zip(preflight.SPLIT_NAMES, resolved_counts):
            for patient_id in ordered[cursor : cursor + count]:
                result[patient_id] = split_name
            cursor += count
        return result

    current = assignment_for(preflight.PATIENT_ORDER_DOMAIN)
    changed = assignment_for(b"changed-domain\x00")
    assert counts == (70, 15, 15)
    assert current != changed
    assert any(current[patient_id] != changed[patient_id] for patient_id in patient_ids)


def test_historical_candidate_identity_stays_separate_from_active_contract() -> None:
    assert (
        preflight.CANDIDATE_SPLIT_ALGORITHM_ID
        == "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
    )
    assert preflight.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256 == (
        "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
    )
    assert (
        preflight.SPLIT_ALGORITHM_ID
        == "PHYSIONET_PATIENT_HASH_EXPLICIT_F061_HAMILTON_V1"
    )
    assert preflight.SPLIT_CONTRACT_SHA256 not in {
        preflight.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256,
        digest(preflight.CANDIDATE_SPLIT_ALGORITHM_ID),
    }


@pytest.mark.parametrize(
    "path",
    ("/absolute", "../escape", "a/../escape", "a\\b", "a//b", "./a"),
)
def test_private_locator_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.PrivateLocator("ROOT", path)


def test_private_locator_is_frozen() -> None:
    value = locator("snapshot/value.json")
    with pytest.raises(FrozenInstanceError):
        value.relative_path = "changed"  # type: ignore[misc]


def test_synthetic_activation_has_no_operational_authority() -> None:
    activation = preflight.synthetic_activation("QUALIFICATION")
    assert activation.state == preflight.SYNTHETIC_STATE
    assert not activation.real_instance_structurally_enabled
    assert activation.to_dict()["authority_authenticated_by_this_module"] is False
    with pytest.raises(preflight.AdmissionPreflightError, match="must not carry"):
        replace(
            activation,
            data_access_authority_sha256=digest("not-allowed"),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "reviewed_precontact_instance_sha256",
        "independent_precontact_review_sha256",
        "data_access_authority_sha256",
        "custody_approval_sha256",
    ),
)
def test_real_activation_requires_every_gate(field_name: str) -> None:
    values = real_activation().__dict__.copy()
    values[field_name] = None
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.ActivationReceipt(**values)


def test_activation_rejects_string_subclasses() -> None:
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(real_activation(), state=StringSubclass(preflight.ACTIVATED_REAL_STATE))


def test_raw_archive_requires_exact_hash_count_and_activation_state() -> None:
    synthetic = preflight.synthetic_activation()
    value = archive(synthetic)
    assert value.raw_archive_bytes == 5_000_000
    assert value.to_dict()["archive_bytes_opened_or_hashed_by_this_module"] is False
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, raw_archive_sha256="A" * 64)
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, raw_archive_bytes=True)
    with pytest.raises(preflight.AdmissionPreflightError, match="synthetic archive"):
        replace(value, access_outcome_receipt_sha256=digest("false-access"))
    with pytest.raises(preflight.AdmissionPreflightError, match="requires an access"):
        replace(archive(real_activation()), access_outcome_receipt_sha256=None)


@pytest.mark.parametrize(
    "changes",
    (
        {"source_partition": "test"},
        {"logical_path": "/1.txt"},
        {"logical_path": "set-a/../1.txt"},
        {"logical_path": "set-a/name.txt"},
        {"record_id": "01"},
        {"record_id": "2"},
        {"file_ordinal": True},
        {"byte_count": 0},
        {"raw_sha256": "f" * 63},
    ),
)
def test_allowlisted_file_receipt_fails_closed(changes: dict[str, object]) -> None:
    base: dict[str, object] = {
        "file_ordinal": 0,
        "source_partition": "set-a",
        "logical_path": "set-a/1.txt",
        "record_id": "1",
        "raw_sha256": digest("record"),
        "byte_count": 100,
    }
    base.update(changes)
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.AllowlistedFileReceipt(**base)  # type: ignore[arg-type]


def test_snapshot_is_canonical_under_input_permutation() -> None:
    activation = preflight.synthetic_activation("PERMUTATION")
    rows = patient_rows()
    files = file_rows()
    first = snapshot(activation, rows=rows, files=files)
    second = snapshot(
        activation,
        rows=tuple(reversed(rows)),
        files=tuple(reversed(files)),
    )
    assert first.snapshot_receipt_sha256 == second.snapshot_receipt_sha256
    assert first.archive_inventory_sha256 == second.archive_inventory_sha256
    assert first.normalized_projection_sha256 == second.normalized_projection_sha256
    assert not first.externally_verified
    assert first.to_dict()["raw_or_normalized_data_opened_by_this_module"] is False


def test_real_snapshot_is_only_structurally_verified() -> None:
    value = snapshot(real_activation())
    assert value.externally_verified
    assert value.activation.to_dict()["authority_authenticated_by_this_module"] is False


def test_snapshot_rejects_duplicate_or_mismatched_rosters() -> None:
    activation = preflight.synthetic_activation("BAD-ROSTER")
    files = list(file_rows())
    files[1] = replace(
        files[1],
        source_partition="set-b",
        logical_path="set-b/1.txt",
        record_id="1",
    )
    with pytest.raises(preflight.AdmissionPreflightError, match="RecordIDs must be unique"):
        snapshot(activation, files=tuple(files))

    rows = list(patient_rows())
    rows[1] = replace(rows[1], patient_id="999999")
    with pytest.raises(preflight.AdmissionPreflightError, match="does not bind"):
        snapshot(activation, rows=tuple(rows))


@pytest.mark.parametrize(
    "field_name",
    ("post_snapshot_exclusion_count", "retry_resplit_topup_count"),
)
def test_snapshot_rejects_anti_selection_counts(field_name: str) -> None:
    value = snapshot(preflight.synthetic_activation("ANTI-SELECTION"))
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, **{field_name: 1})


def test_snapshot_rejects_tuple_subclasses_and_synthetic_verification() -> None:
    activation = preflight.synthetic_activation("STRICT-TUPLE")
    with pytest.raises(preflight.AdmissionPreflightError):
        snapshot(activation, files=TupleSubclass(file_rows()))  # type: ignore[arg-type]
    with pytest.raises(preflight.AdmissionPreflightError, match="must not carry"):
        replace(
            snapshot(activation),
            snapshot_verification_receipt_sha256=digest("false-verification"),
        )


def test_unresolved_f061_is_all_null_and_cannot_split() -> None:
    unresolved = preflight.F061Allocation(
        review_state="UNRESOLVED",
        patient_count=None,
        numerators=None,
        denominator=None,
        counts=None,
        minimum_counts=None,
        rounding_rule_id=None,
        external_review_binding=None,
    )
    value = snapshot(preflight.synthetic_activation("UNRESOLVED-F061"))
    with pytest.raises(preflight.AdmissionPreflightError, match="unresolved"):
        preflight.build_patient_disjoint_split(
            snapshot=value,
            allocation=unresolved,
            split_locator=locator("split/unresolved.json"),
        )
    with pytest.raises(preflight.AdmissionPreflightError, match="all-null"):
        replace(unresolved, denominator=100)


def test_f061_keeps_70_15_15_synthetic_candidate_only() -> None:
    synthetic = allocation(preflight.synthetic_activation("F061"))
    assert synthetic.numerators == (70, 15, 15)
    assert synthetic.denominator == 100
    assert synthetic.counts == (598, 128, 128)
    assert synthetic.minimum_counts == (1, 1, 1)
    with pytest.raises(preflight.AdmissionPreflightError, match="candidate"):
        replace(
            synthetic,
            numerators=(69, 16, 15),
            counts=(589, 137, 128),
        )
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(synthetic, denominator=True)
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(synthetic, counts=(598, True, 128))
    with pytest.raises(preflight.AdmissionPreflightError, match="external review"):
        replace(
            synthetic,
            external_review_binding=allocation(
                real_activation()
            ).external_review_binding,
        )


def test_real_f061_accepts_explicit_reviewed_proportions_and_minimums() -> None:
    value = allocation(real_activation())
    assert value.numerators == (60, 20, 20)
    assert value.counts == (512, 171, 171)
    assert value.minimum_counts == (500, 160, 160)
    assert len(value.proposal_sha256 or "") == 64
    assert value.external_review_binding is not None
    assert value.external_review_binding.accepted is True
    assert value.external_review_binding.proposal_sha256 == value.proposal_sha256
    assert len(value.external_review_binding.binding_sha256) == 64
    value.validate_for_patient_count(PATIENT_COUNT, real_activation())


def test_real_f061_binds_accepted_shared_policy_and_exact_adapter() -> None:
    value = allocation(real_activation())
    assert value.shared_policy_values == value.numerators
    assert value.shared_policy_denominator == value.denominator
    assert value.shared_policy_minimum_counts == value.minimum_counts
    assert value.shared_policy_review_accepted is True
    assert value.physionet_adapter_id == preflight.PHYSIONET_F061_ADAPTER_ID
    assert (
        value.physionet_adapter_sha256
        == preflight.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert preflight.physionet_f061_adapter_sha256() == (
        preflight.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert value.external_review_binding is not None
    review = value.external_review_binding.to_dict()
    assert review["review_scope"] == preflight.PHYSIONET_RESOLVED_F061_REVIEW_SCOPE
    assert review["shared_policy_review_accepts_resolved_counts"] is False


def test_shared_policy_review_receipt_cannot_be_reused_for_resolved_counts() -> None:
    value = allocation(real_activation())
    assert value.external_review_binding is not None
    reused = replace(
        value.external_review_binding,
        review_receipt_sha256=value.shared_policy_review_receipt_sha256,
    )
    with pytest.raises(preflight.AdmissionPreflightError, match="must be distinct"):
        replace(value, external_review_binding=reused)


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"shared_policy_values": (61, 19, 20)}, "differs from shared policy"),
        ({"shared_policy_definition_sha256": "0" * 64}, "definition digest"),
        ({"shared_policy_review_accepted": False}, "explicitly accept"),
        ({"physionet_adapter_id": "FOREIGN-ADAPTER"}, "adapter identity"),
        ({"physionet_adapter_sha256": "0" * 64}, "adapter digest"),
    ),
)
def test_real_f061_rejects_shared_policy_or_adapter_lineage_drift(
    changes: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(preflight.AdmissionPreflightError, match=message):
        replace(allocation(real_activation()), **changes)


def test_native_f061_cannot_diverge_from_shared_policy_values() -> None:
    with pytest.raises(
        preflight.AdmissionPreflightError,
        match="differs from shared policy",
    ):
        replace(
            allocation(real_activation()),
            numerators=(61, 19, 20),
            counts=(521, 162, 171),
        )


def test_self_consistent_foreign_shared_policy_cannot_back_native_projection() -> None:
    foreign_proposal = preflight.shared_f061_policy_proposal_sha256(
        allocation_id="FOREIGN-SHARED-F061-POLICY",
        values=(61, 19, 20),
        denominator=100,
        minimum_counts=(500, 160, 160),
        rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
        power_requirement_id="FOREIGN-POWER-REQUIREMENT",
    )
    foreign_review = digest("foreign-shared-policy-review")
    foreign_definition = preflight.shared_f061_policy_definition_sha256(
        allocation_proposal_sha256=foreign_proposal,
        power_review_receipt_sha256=foreign_review,
        power_review_accepted=True,
    )
    with pytest.raises(
        preflight.AdmissionPreflightError,
        match="differs from shared policy",
    ):
        preflight.f061_allocation_proposal_sha256(
            patient_count=PATIENT_COUNT,
            numerators=(60, 20, 20),
            denominator=100,
            counts=(512, 171, 171),
            minimum_counts=(500, 160, 160),
            rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            shared_policy_allocation_id="FOREIGN-SHARED-F061-POLICY",
            shared_policy_values=(61, 19, 20),
            shared_policy_denominator=100,
            shared_policy_minimum_counts=(500, 160, 160),
            shared_policy_rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
            shared_policy_power_requirement_id="FOREIGN-POWER-REQUIREMENT",
            shared_policy_proposal_sha256=foreign_proposal,
            shared_policy_review_receipt_sha256=foreign_review,
            shared_policy_review_accepted=True,
            shared_policy_definition_sha256=foreign_definition,
            physionet_adapter_id=preflight.PHYSIONET_F061_ADAPTER_ID,
            physionet_adapter_sha256=preflight.PHYSIONET_F061_ADAPTER_SHA256,
        )


def test_f061_proposal_digest_and_external_acceptance_are_exactly_bound() -> None:
    value = allocation(real_activation())
    changed_proposal = preflight.f061_allocation_proposal_sha256(
        patient_count=PATIENT_COUNT,
        numerators=(60, 20, 20),
        denominator=100,
        counts=(512, 171, 171),
        minimum_counts=(499, 160, 160),
        rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
    )
    assert changed_proposal != value.proposal_sha256
    compact_ratio_proposal = preflight.f061_allocation_proposal_sha256(
        patient_count=PATIENT_COUNT,
        numerators=(3, 1, 1),
        denominator=5,
        counts=(512, 171, 171),
        minimum_counts=(500, 160, 160),
        rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
    )
    assert compact_ratio_proposal != value.proposal_sha256
    changed_count_proposal = preflight.f061_allocation_proposal_sha256(
        patient_count=PATIENT_COUNT + 1,
        numerators=(60, 20, 20),
        denominator=100,
        counts=(513, 171, 171),
        minimum_counts=(500, 160, 160),
        rounding_rule_id=preflight.F061_ROUNDING_RULE_ID,
    )
    assert changed_count_proposal != value.proposal_sha256
    with pytest.raises(preflight.AdmissionPreflightError, match="rounding-rule"):
        preflight.f061_allocation_proposal_sha256(
            patient_count=PATIENT_COUNT,
            numerators=(60, 20, 20),
            denominator=100,
            counts=(512, 171, 171),
            minimum_counts=(500, 160, 160),
            rounding_rule_id="SOME-OTHER-ROUNDING-RULE",
        )
    assert value.external_review_binding is not None
    foreign_review = replace(
        value.external_review_binding,
        proposal_sha256=changed_proposal,
    )
    with pytest.raises(preflight.AdmissionPreflightError, match="exact proposal"):
        replace(value, external_review_binding=foreign_review)
    with pytest.raises(preflight.AdmissionPreflightError, match="explicitly accept"):
        replace(value.external_review_binding, accepted=False)
    with pytest.raises(preflight.AdmissionPreflightError, match="external review"):
        replace(value, external_review_binding=None)


def test_split_graph_rejects_low_level_f061_review_binding_mutation() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    value = allocation(activation)
    assert value.external_review_binding is not None
    object.__setattr__(
        value.external_review_binding,
        "binding_sha256",
        digest("forged-review-binding"),
    )
    with pytest.raises(preflight.AdmissionPreflightError, match="revalidation"):
        preflight.build_patient_disjoint_split(
            snapshot=snapshot_receipt,
            allocation=value,
            split_locator=locator("split/forged-review.json"),
            split_verification_receipt_sha256=digest("split-review"),
        )


def test_f061_review_rejects_mutated_locator_even_when_digest_is_recomputed() -> None:
    value = allocation(real_activation())
    assert value.external_review_binding is not None
    corrupted_locator = locator("power/original-review.json")
    object.__setattr__(corrupted_locator, "relative_path", "../escaped-review.json")
    with pytest.raises(preflight.AdmissionPreflightError, match="locator.*revalidation"):
        replace(
            value.external_review_binding,
            review_locator=corrupted_locator,
        )


def test_f061_underpowered_and_inconsistent_counts_fail_closed() -> None:
    with pytest.raises(preflight.AdmissionPreflightError, match="underpowered"):
        preflight.make_f061_allocation(
            patient_count=10,
            review_state="POWER_REVIEWED",
            numerators=(60, 20, 20),
            denominator=100,
            counts=(6, 2, 2),
            minimum_counts=(6, 3, 1),
            external_review_binding=None,
        )
    valid = allocation(real_activation())
    with pytest.raises(preflight.AdmissionPreflightError, match="do not exhaust"):
        replace(valid, counts=(511, 171, 171))
    with pytest.raises(preflight.AdmissionPreflightError, match="Hamilton"):
        replace(valid, counts=(511, 172, 171))
    with pytest.raises(preflight.AdmissionPreflightError, match="snapshot"):
        valid.validate_for_patient_count(PATIENT_COUNT - 1, real_activation())


def test_activation_and_f061_review_states_cannot_be_mixed() -> None:
    synthetic = preflight.synthetic_activation("STATE-MIX")
    real = real_activation()
    with pytest.raises(preflight.AdmissionPreflightError, match="synthetic split"):
        allocation(real).validate_for_patient_count(PATIENT_COUNT, synthetic)
    with pytest.raises(preflight.AdmissionPreflightError, match="power-reviewed"):
        allocation(synthetic).validate_for_patient_count(PATIENT_COUNT, real)


def test_patient_split_is_deterministic_disjoint_and_all_record_preserving() -> None:
    snapshot_receipt = snapshot(preflight.synthetic_activation("SPLIT"))
    first = split(snapshot_receipt)
    second = split(snapshot_receipt)
    assert first.split_manifest_sha256 == second.split_manifest_sha256
    assert first.patient_counts == (598, 128, 128)
    assert sum(first.record_counts) == PATIENT_COUNT
    assert tuple(row.record_ordinal for row in first.record_assignments) == tuple(
        range(PATIENT_COUNT)
    )
    by_patient: dict[str, set[str]] = {}
    for row in first.record_assignments:
        by_patient.setdefault(row.patient_id, set()).add(row.split)
    assert all(len(values) == 1 for values in by_patient.values())
    assert not first.structurally_complete_for_real_instance
    assert first.to_dict()["publication_safe"] is False


def test_real_split_is_activation_and_power_review_gated() -> None:
    value = split(snapshot(real_activation()))
    assert value.structurally_complete_for_real_instance
    assert value.allocation.power_reviewed
    assert value.split_verification_receipt_sha256 == digest("split-verification")
    assert value.exclusion_count == value.retry_count == 0
    assert value.resplit_count == value.top_up_count == 0
    with pytest.raises(preflight.AdmissionPreflightError, match="verification"):
        replace(value, split_verification_receipt_sha256=None)


def test_split_receipt_revalidates_assignment_contents_fail_closed() -> None:
    value = split(snapshot(preflight.synthetic_activation("HOSTILE-SPLIT")))
    patients = list(value.patient_assignments)
    patients[0] = replace(patients[0], order_sha256=digest("forged-order"))
    with pytest.raises(preflight.AdmissionPreflightError, match="ordering digest"):
        replace(value, patient_assignments=tuple(patients))

    records = list(value.record_assignments)
    records[0] = replace(records[0], record_ordinal=1)
    with pytest.raises(preflight.AdmissionPreflightError, match="0..R-1"):
        replace(value, record_assignments=tuple(records))

    false_counts = list(value.patient_counts)
    false_counts[0] -= 1
    false_counts[1] += 1
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, patient_counts=tuple(false_counts))


def test_split_rejects_snapshot_or_locator_subclasses() -> None:
    value = snapshot(preflight.synthetic_activation("STRICT-SPLIT"))

    class SnapshotSubclass(preflight.SnapshotReceipt):
        pass

    subclass = SnapshotSubclass(**{
        field_name: getattr(value, field_name)
        for field_name in (
            "activation",
            "archive",
            "allowlisted_files",
            "patient_projection",
            "source_schema_receipt_sha256",
            "toolchain",
            "snapshot_locator",
            "snapshot_verification_receipt_sha256",
            "post_snapshot_exclusion_count",
            "retry_resplit_topup_count",
        )
    })
    with pytest.raises(preflight.AdmissionPreflightError, match="exact Snapshot"):
        preflight.build_patient_disjoint_split(
            snapshot=subclass,
            allocation=allocation(value.activation),
            split_locator=locator("split/subclass.json"),
        )


def test_unresolved_support_keeps_f033_f034_null() -> None:
    value = preflight.unresolved_observation_support(
        preflight.synthetic_activation("SUPPORT-NULL")
    )
    assert value.f033_state == value.f034_state == "UNRESOLVED"
    assert value.observation_reference_id is None
    assert value.proof_certificate_sha256 is None
    assert not value.certified
    with pytest.raises(preflight.AdmissionPreflightError, match="must not carry"):
        replace(value, observation_reference_id="UNPROVED-REFERENCE")


def test_synthetic_activation_cannot_claim_certified_support() -> None:
    real_value = certified_support(real_activation())
    with pytest.raises(preflight.AdmissionPreflightError, match="synthetic"):
        replace(
            real_value,
            activation=preflight.synthetic_activation("FORGED-SUPPORT"),
        )


@pytest.mark.parametrize(
    "changes",
    (
        {"clean_kernel_kept_separate": False},
        {"theorem_convenience_noise_added": True},
        {"f034_state": "UNRESOLVED"},
        {"mixture_weight_numerator": 0},
        {"mixture_weight_numerator": 100},
        {"mixture_weight_denominator": True},
        {"observation_reference_sha256": None},
        {"full_support_component_id": None},
        {"full_support_component_sha256": None},
        {"proof_certificate_sha256": None},
        {"independent_review_receipt_sha256": None},
        {"common_support_route_id": "CONVENIENCE-NOISE"},
    ),
)
def test_certified_support_fails_closed_on_missing_or_unjustified_parts(
    changes: dict[str, object],
) -> None:
    value = certified_support(real_activation())
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, **changes)


def test_governance_remains_unresolved_for_synthetic_activation() -> None:
    activation = preflight.synthetic_activation("GOVERNANCE")
    value = unresolved_governance(activation)
    assert not value.approved
    with pytest.raises(preflight.AdmissionPreflightError, match="cannot carry"):
        preflight.GovernanceReceipt(
            activation=activation,
            determination_state="APPROVED_FOR_FROZEN_PHYSIONET_RESEARCH_USE",
            governance_record_sha256=digest("fake"),
            accountable_owner_acceptance_sha256=digest("fake-owner"),
            determination_locator=locator("governance/fake.json"),
        )


def test_real_governance_requires_record_owner_and_private_locator() -> None:
    value = approved_governance(real_activation())
    assert value.approved
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, accountable_owner_acceptance_sha256=None)
    with pytest.raises(preflight.AdmissionPreflightError):
        replace(value, determination_locator=None)


def test_governance_support_and_duplicate_self_digests_bind_exact_content() -> None:
    activation = real_activation()
    governance = approved_governance(activation)
    support = certified_support(activation)
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    for value in (
        governance.governance_receipt_sha256,
        support.support_receipt_sha256,
        audit.duplicate_audit_receipt_sha256,
    ):
        assert len(value) == 64
    assert (
        replace(
            governance,
            governance_record_sha256=digest("different-governance"),
        ).governance_receipt_sha256
        != governance.governance_receipt_sha256
    )
    assert (
        replace(support, mixture_weight_denominator=101).support_receipt_sha256
        != support.support_receipt_sha256
    )
    assert (
        replace(audit, near_duplicate_cross_split_count=1)
        .duplicate_audit_receipt_sha256
        != audit.duplicate_audit_receipt_sha256
    )


def test_duplicate_audit_binds_exact_inputs_coverage_and_certificates() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    train, validation, test = split_receipt.record_counts
    expected_pairs = train * validation + train * test + validation * test

    assert audit.audit_algorithm_id == preflight.DUPLICATE_AUDIT_ALGORITHM_ID
    assert audit.audit_implementation_sha256 == (
        preflight.DUPLICATE_AUDIT_IMPLEMENTATION_SHA256
    )
    assert audit.near_duplicate_rule_id == preflight.DUPLICATE_NEAR_RULE_ID
    assert audit.audited_normalized_projection_sha256 == (
        split_receipt.normalized_projection_sha256
    )
    assert audit.audited_record_count == len(split_receipt.record_assignments)
    assert audit.audited_patient_count == len(split_receipt.patient_assignments)
    assert audit.eligible_cross_split_record_pair_count == expected_pairs
    assert audit.checked_cross_split_record_pair_count == expected_pairs
    assert audit.coverage_complete
    for value in (
        audit.audit_input_manifest_sha256,
        audit.completion_certificate_sha256,
        audit.completion_attestation_sha256,
    ):
        assert len(value) == 64
    implementation = preflight.duplicate_audit_implementation_record()
    assert hashlib.sha256(
        preflight.DUPLICATE_AUDIT_IMPLEMENTATION_DOMAIN
        + json.dumps(
            implementation,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest() == preflight.DUPLICATE_AUDIT_IMPLEMENTATION_SHA256
    changed = replace(
        audit,
        completion_certificate_sha256=digest("changed-audit-certificate"),
    )
    assert changed.completion_attestation_sha256 != (
        audit.completion_attestation_sha256
    )


@pytest.mark.parametrize(
    "changes",
    (
        {"audit_algorithm_id": "FOREIGN-INCOMPLETE-AUDIT"},
        {"near_duplicate_rule_id": "FOREIGN-NEAR-RULE"},
        {"audit_implementation_sha256": "0" * 64},
    ),
)
def test_duplicate_audit_rejects_foreign_identity(changes: dict[str, object]) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    with pytest.raises(preflight.AdmissionPreflightError, match="identity|digest"):
        replace(
            duplicate_audit(activation, snapshot_receipt, split_receipt),
            **changes,
        )


def test_duplicate_audit_constructor_recomputes_implementation_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    monkeypatch.setattr(
        preflight,
        "DUPLICATE_AUDIT_IMPLEMENTATION_SCHEMA_VERSION",
        "foreign-duplicate-audit-implementation",
    )
    with pytest.raises(
        preflight.AdmissionPreflightError,
        match="implementation identity drift",
    ):
        replace(audit)


@pytest.mark.parametrize(
    "changes",
    (
        {
            "eligible_cross_split_record_pair_count": 1,
            "checked_cross_split_record_pair_count": 1,
            "complete_roster_checked": True,
        },
        {"audited_normalized_projection_sha256": "0" * 64},
        {"audited_assignment_manifest_sha256": "0" * 64},
        {"audited_record_count": 3, "audited_patient_count": 3},
    ),
)
def test_self_consistent_forged_duplicate_audit_is_final_no_go(
    changes: dict[str, object],
) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    forged = replace(
        duplicate_audit(activation, snapshot_receipt, split_receipt),
        **changes,
    )
    assert forged.complete_roster_checked
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=approved_governance(activation),
        support=certified_support(activation),
        duplicate_audit=forged,
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert not decision.receipt_flag_mapping()[
        "duplicate_and_near_duplicate_audit_verified"
    ]


def test_duplicate_audit_is_method_blind_and_activation_gated() -> None:
    activation = preflight.synthetic_activation("DUPLICATES")
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    value = duplicate_audit(activation, snapshot_receipt, split_receipt)
    assert not value.verified
    assert not value.passed
    with pytest.raises(preflight.AdmissionPreflightError, match="locator"):
        replace(value, audit_locator=None)
    with pytest.raises(preflight.AdmissionPreflightError, match="identity drift"):
        replace(value, near_duplicate_rule_id="TBD")
    with pytest.raises(preflight.AdmissionPreflightError, match="must not inspect"):
        replace(value, outcome_or_label_content_inspected=True)
    with pytest.raises(preflight.AdmissionPreflightError, match="must not carry"):
        replace(
            value,
            audit_verification_receipt_sha256=digest("false-verification"),
        )


def test_real_duplicate_audit_distinguishes_verification_from_pass() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    value = duplicate_audit(
        activation,
        snapshot_receipt,
        split_receipt,
        near_count=1,
    )
    assert value.verified
    assert not value.passed


def test_violation_vector_requires_exact_order_types_and_cardinality() -> None:
    mapping = {name: 0 for name in preflight.ADMISSION_COMPONENTS}
    value = preflight.ViolationCountVector.from_mapping(mapping)
    assert value.maximum == 0
    assert value.nonzero_components == ()
    assert tuple(value.to_dict()) == preflight.ADMISSION_COMPONENTS

    reversed_mapping = {name: 0 for name in reversed(preflight.ADMISSION_COMPONENTS)}
    with pytest.raises(preflight.AdmissionPreflightError, match="exact ordered"):
        preflight.ViolationCountVector.from_mapping(reversed_mapping)
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.ViolationCountVector.from_mapping(DictSubclass(mapping))
    lying_keys = {
        EqualityLyingString("FOREIGN-COMPONENT"): 0,
        **{name: 0 for name in preflight.ADMISSION_COMPONENTS[1:]},
    }
    with pytest.raises(preflight.AdmissionPreflightError, match="built-in string"):
        preflight.ViolationCountVector.from_mapping(lying_keys)
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.ViolationCountVector((0,) * 12)
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.ViolationCountVector((0,) * 12 + (True,))
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.ViolationCountVector((0,) * 12 + (-1,))
    with pytest.raises(preflight.AdmissionPreflightError, match="TRAIN only"):
        replace(value, evaluation_split="TEST")


def test_synthetic_qualification_can_never_admit() -> None:
    activation = preflight.synthetic_activation("FULL-SYNTHETIC")
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=unresolved_governance(activation),
        support=preflight.unresolved_observation_support(activation),
        duplicate_audit=duplicate_audit(
            activation, snapshot_receipt, split_receipt
        ),
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert decision.domain_admitted is False
    assert decision.independent_admission_required is True
    assert tuple(decision.receipt_flag_mapping()) == preflight.REQUIRED_RECEIPT_FLAGS
    assert not any(decision.receipt_flag_mapping().values())
    with pytest.raises(preflight.AdmissionPreflightError, match="contradicts"):
        replace(
            decision,
            decision="ELIGIBLE_FOR_INDEPENDENT_ADMISSION",
        )


def test_complete_real_shaped_packet_is_only_independent_admission_eligible() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    governance = approved_governance(activation)
    support = certified_support(activation)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=governance,
        support=support,
        duplicate_audit=audit,
        violation_counts=zero_counts(),
    )
    assert decision.decision == "ELIGIBLE_FOR_INDEPENDENT_ADMISSION"
    assert decision.domain_admitted is False
    assert decision.independent_admission_required is True
    assert all(decision.receipt_flag_mapping().values())
    assert decision.duplicate_audit_findings == (0, 0)
    assert decision.snapshot_receipt_sha256 == snapshot_receipt.snapshot_receipt_sha256
    assert decision.split_manifest_sha256 == split_receipt.split_manifest_sha256
    assert (
        decision.governance_receipt_sha256
        == governance.governance_receipt_sha256
    )
    assert decision.support_receipt_sha256 == support.support_receipt_sha256
    assert (
        decision.duplicate_audit_receipt_sha256
        == audit.duplicate_audit_receipt_sha256
    )
    assert len(decision.evidence_aggregate_sha256) == 64
    assert len(decision.record_sha256) == 64
    malformed_flags = list(decision.receipt_flags)
    malformed_flags[0] = list(malformed_flags[0])  # type: ignore[assignment]
    with pytest.raises(preflight.AdmissionPreflightError, match="exact.*pair"):
        replace(decision, receipt_flags=tuple(malformed_flags))


def test_admission_evidence_aggregate_changes_with_exact_receipt_identity() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    support = certified_support(activation)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    first_governance = approved_governance(activation)
    second_governance = replace(
        first_governance,
        governance_record_sha256=digest("alternate-governance-record"),
    )
    first = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=first_governance,
        support=support,
        duplicate_audit=audit,
        violation_counts=zero_counts(),
    )
    second = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=second_governance,
        support=support,
        duplicate_audit=audit,
        violation_counts=zero_counts(),
    )
    assert first.governance_receipt_sha256 != second.governance_receipt_sha256
    assert first.evidence_aggregate_sha256 != second.evidence_aggregate_sha256
    assert first.record_sha256 != second.record_sha256


@pytest.mark.parametrize("component_index", range(len(preflight.ADMISSION_COMPONENTS)))
def test_each_of_13_violation_components_forces_no_go(component_index: int) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    counts = [0] * len(preflight.ADMISSION_COMPONENTS)
    counts[component_index] = 1
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=approved_governance(activation),
        support=certified_support(activation),
        duplicate_audit=duplicate_audit(
            activation, snapshot_receipt, split_receipt
        ),
        violation_counts=preflight.ViolationCountVector(tuple(counts)),
    )
    assert decision.decision == "NO_GO"
    assert decision.violation_counts.nonzero_components == (
        preflight.ADMISSION_COMPONENTS[component_index],
    )


@pytest.mark.parametrize("exact_count,near_count", ((1, 0), (0, 1), (2, 3)))
def test_duplicate_or_near_duplicate_findings_force_no_go(
    exact_count: int, near_count: int
) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=approved_governance(activation),
        support=certified_support(activation),
        duplicate_audit=duplicate_audit(
            activation,
            snapshot_receipt,
            split_receipt,
            exact_count=exact_count,
            near_count=near_count,
        ),
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert decision.receipt_flag_mapping()[
        "duplicate_and_near_duplicate_audit_verified"
    ]


def test_unresolved_f033_f034_force_real_packet_no_go() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=approved_governance(activation),
        support=preflight.unresolved_observation_support(activation),
        duplicate_audit=duplicate_audit(
            activation, snapshot_receipt, split_receipt
        ),
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert not decision.receipt_flag_mapping()[
        "observation_reference_and_support_receipt_verified"
    ]


def test_unresolved_governance_forces_real_packet_no_go() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=unresolved_governance(activation),
        support=certified_support(activation),
        duplicate_audit=duplicate_audit(
            activation, snapshot_receipt, split_receipt
        ),
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert not decision.receipt_flag_mapping()["governance_approval_verified"]


def test_incomplete_duplicate_audit_forces_real_packet_no_go() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    decision = preflight.evaluate_admission_preflight(
        snapshot=snapshot_receipt,
        split=split_receipt,
        governance=approved_governance(activation),
        support=certified_support(activation),
        duplicate_audit=duplicate_audit(
            activation,
            snapshot_receipt,
            split_receipt,
            complete=False,
        ),
        violation_counts=zero_counts(),
    )
    assert decision.decision == "NO_GO"
    assert not decision.receipt_flag_mapping()[
        "duplicate_and_near_duplicate_audit_verified"
    ]


def test_mismatched_receipt_activations_and_links_are_rejected() -> None:
    first_activation = real_activation()
    second_activation = replace(
        real_activation(), activation_id="PHYSIONET-B02-ACTIVATION-V2"
    )
    snapshot_receipt = snapshot(first_activation)
    split_receipt = split(snapshot_receipt)
    with pytest.raises(preflight.AdmissionPreflightError, match="activation differs"):
        preflight.evaluate_admission_preflight(
            snapshot=snapshot_receipt,
            split=split_receipt,
            governance=approved_governance(second_activation),
            support=certified_support(first_activation),
            duplicate_audit=duplicate_audit(
                first_activation, snapshot_receipt, split_receipt
            ),
            violation_counts=zero_counts(),
        )

    audit = duplicate_audit(first_activation, snapshot_receipt, split_receipt)
    with pytest.raises(preflight.AdmissionPreflightError, match="does not bind"):
        preflight.evaluate_admission_preflight(
            snapshot=snapshot_receipt,
            split=split_receipt,
            governance=approved_governance(first_activation),
            support=certified_support(first_activation),
            duplicate_audit=replace(
                audit,
                split_manifest_sha256=digest("wrong-split"),
            ),
            violation_counts=zero_counts(),
        )


def test_admission_rechecks_split_assignments_against_snapshot_projection() -> None:
    activation = real_activation()
    original_snapshot = snapshot(activation)
    changed_rows = list(patient_rows())
    changed_rows[-1] = replace(changed_rows[-1], patient_id="999999")
    changed_files = list(file_rows())
    changed_files[-1] = replace(
        changed_files[-1],
        logical_path="set-a/999999.txt",
        record_id="999999",
    )
    changed_snapshot = snapshot(
        activation,
        rows=tuple(changed_rows),
        files=tuple(changed_files),
    )
    changed_split = split(changed_snapshot)
    forged_binding = replace(
        changed_split,
        snapshot_receipt_sha256=original_snapshot.snapshot_receipt_sha256,
        normalized_projection_sha256=original_snapshot.normalized_projection_sha256,
    )
    with pytest.raises(preflight.AdmissionPreflightError, match="exact snapshot"):
        preflight.evaluate_admission_preflight(
            snapshot=original_snapshot,
            split=forged_binding,
            governance=approved_governance(activation),
            support=certified_support(activation),
            duplicate_audit=duplicate_audit(
                activation, original_snapshot, forged_binding
            ),
            violation_counts=zero_counts(),
        )


def test_admission_revalidates_frozen_receipts_against_low_level_mutation() -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    object.__setattr__(audit, "outcome_or_label_content_inspected", True)
    with pytest.raises(preflight.AdmissionPreflightError, match="revalidation"):
        preflight.evaluate_admission_preflight(
            snapshot=snapshot_receipt,
            split=split_receipt,
            governance=approved_governance(activation),
            support=certified_support(activation),
            duplicate_audit=audit,
            violation_counts=zero_counts(),
        )


@pytest.mark.parametrize(
    "target_name,digest_field",
    (
        ("governance", "governance_receipt_sha256"),
        ("support", "support_receipt_sha256"),
        ("audit", "duplicate_audit_receipt_sha256"),
    ),
)
def test_admission_rejects_forged_receipt_self_digest_crossbindings(
    target_name: str,
    digest_field: str,
) -> None:
    activation = real_activation()
    snapshot_receipt = snapshot(activation)
    split_receipt = split(snapshot_receipt)
    governance = approved_governance(activation)
    support = certified_support(activation)
    audit = duplicate_audit(activation, snapshot_receipt, split_receipt)
    targets = {
        "governance": governance,
        "support": support,
        "audit": audit,
    }
    object.__setattr__(targets[target_name], digest_field, digest("foreign-receipt"))
    with pytest.raises(preflight.AdmissionPreflightError, match="revalidation"):
        preflight.evaluate_admission_preflight(
            snapshot=snapshot_receipt,
            split=split_receipt,
            governance=governance,
            support=support,
            duplicate_audit=audit,
            violation_counts=zero_counts(),
        )


def test_normalized_projection_digest_is_order_independent_but_content_sensitive() -> None:
    rows = patient_rows()
    assert preflight.normalized_projection_sha256(rows) == (
        preflight.normalized_projection_sha256(tuple(reversed(rows)))
    )
    changed = list(rows)
    changed[-1] = replace(changed[-1], patient_id="999999")
    assert preflight.normalized_projection_sha256(tuple(changed)) != (
        preflight.normalized_projection_sha256(rows)
    )


def test_projection_rejects_incomplete_ordinals_and_inexact_tuple() -> None:
    rows = patient_rows(3)
    with pytest.raises(preflight.AdmissionPreflightError):
        preflight.normalized_projection_sha256(TupleSubclass(rows))
    with pytest.raises(preflight.AdmissionPreflightError, match="0..R-1"):
        preflight.normalized_projection_sha256(
            (rows[0], replace(rows[1], record_ordinal=3), rows[2])
        )


@pytest.mark.parametrize(
    "field_name,hostile_value",
    (("patient_id", "0"), ("record_ordinal", False)),
)
def test_projection_rejects_low_level_mutated_patient_rows(
    field_name: str,
    hostile_value: object,
) -> None:
    rows = list(patient_rows(3))
    object.__setattr__(rows[1], field_name, hostile_value)
    with pytest.raises(preflight.AdmissionPreflightError, match="revalidation"):
        preflight.normalized_projection_sha256(tuple(rows))


def test_source_has_no_io_network_process_entropy_or_randomness_surface() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imported_roots = set()
    called_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
    assert not imported_roots.intersection(
        {"os", "socket", "subprocess", "urllib", "requests", "http", "random", "secrets"}
    )
    assert not called_names.intersection(
        {
            "open",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "urlopen",
            "connect",
            "send",
            "sendall",
            "Popen",
            "run",
            "system",
            "urandom",
        }
    )


def test_public_api_exposes_no_data_or_network_executor() -> None:
    prohibited = (
        "open",
        "load",
        "download",
        "fetch",
        "contact",
        "request",
        "write",
        "persist",
        "train",
        "infer",
        "sample",
    )
    assert all(
        not any(token in name.casefold() for token in prohibited)
        for name in preflight.__all__
    )
