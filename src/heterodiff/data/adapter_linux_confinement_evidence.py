"""Prospective Linux-confinement evidence and outer-receipt schemas.

This module is deliberately incapable of recording a successful Linux run.
It freezes the evidence vocabulary and a synthetic, all-false outer-receipt
shape that can be validated on a non-Linux development host.  Constructing,
serializing, parsing, or hashing either artifact is not execution evidence.

The future native supervisor must use a separately reviewed executed-record
type.  In particular, callers cannot promote any observation, hostile-control,
containment, publication, or decision field through the prospective receipt
defined here.

The ``synthetic_*_transcript_sha256`` fields accept only digest-shaped fixture
values: no executed-transcript preimage type or validator exists here.  The
separate staging run binding deterministically correlates a policy digest,
supervisor epoch, run sequence, and nonce, but it is not an observation and
does not make arbitrary digest-only joins resistant to cross-run splicing.
The executed outer-receipt type and complete teardown-deadline protocol remain
future work.

This schema does cross-check the fixed evidence plan and staging contract for
process-role names, release-gate event names, and the symbolic inner-completion
digest transport.  Those are schema-coherence checks only.  No release-gate
preimage validator, native-supervisor completion-record validator, or executed
postrun finalization envelope is implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final

from . import adapter_linux_confinement_evidence_plan as _evidence_plan
from . import adapter_linux_confinement_staging_protocol as _staging
from .adapter_linux_confinement_acceptance import (
    LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS,
    LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS,
    LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS,
    LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS,
    LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS,
    linux_confinement_acceptance_contract_sha256,
)
from .adapter_linux_confinement_policy import (
    LINUX_CONFINEMENT_FALSE_CLAIM_IDS,
    LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_TARGET_STATUS,
    MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES,
    LinuxConfinementPolicyV1,
    linux_confinement_policy_bytes,
    linux_confinement_policy_sha256,
)
from .adapter_source_bound_child_runner import (
    MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES,
    SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE,
    SourceBoundAdapterChildRunReceiptV1,
    source_bound_adapter_child_run_receipt_bytes,
    source_bound_adapter_child_run_receipt_sha256,
)


LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-evidence-schema-contract.v1"
)
LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_BYTES: Final = (
    64 * 1024
)

PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.prospective-linux-confinement-outer-receipt.v1"
)
PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DIGEST_DOMAIN: Final = (
    PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE
)
PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ORIGIN: Final = (
    "SYNTHETIC_SCHEMA_FIXTURE"
)
PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DECISION_STATUS: Final = (
    "NOT_MADE_BY_PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT"
)
MAXIMUM_PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_BYTES: Final = (
    128 * 1024
)

LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS: Final = (
    "application",
    "bubblewrap-monitor",
    "bubblewrap-setup-child",
    "privileged-supervisor",
    "sandbox-pid1-reaper",
    "unprivileged-preexec-launcher",
    "userns-map-observation-helper",
)
LINUX_CONFINEMENT_RELEASE_EVENT_IDS: Final = tuple(
    event.value for event in _staging.LinuxConfinementStagingEvent
)
LINUX_CONFINEMENT_OUTER_RECEIPT_BINDING_FIELD_IDS: Final = (
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "inner-v1-receipt-byte-count",
    "inner-v1-receipt-plain-sha256",
    "inner-v1-receipt-sha256",
    "linux-confinement-policy-sha256",
    "run-nonce-hex",
    "run-sequence-number",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "supervisor-epoch-id-hex",
    "synthetic-observation-transcript-sha256",
    "synthetic-pidfd-bound-process-identity-transcript-sha256",
    "synthetic-release-transcript-sha256",
    "synthetic-userns-map-observation-transcript-sha256",
)

_PROSPECTIVE_EXECUTION_FALSE_FIELD_IDS: Final = (
    "evidence_observations_collected",
    "hostile_controls_executed",
    "linux_execution_observed",
    "native_supervisor_executed",
)
_PROSPECTIVE_BOUNDARY_FALSE_FIELD_IDS: Final = (
    "digest_only_synthetic_joins_reject_cross_run_splice",
    "direct_arbitrary_transcript_digests_prove_execution_or_confinement",
    "executed_postrun_finalization_envelope_defined",
    "executed_transcript_preimage_type_defined",
    "executed_transcript_preimage_validator_defined",
    "future_executed_outer_receipt_type_defined",
    "native_supervisor_completion_record_validator_defined",
    "release_gate_preimage_validator_defined",
    "staging_run_binding_proves_execution_or_confinement",
    (
        "synthetic_outer_binding_implements_plan_full_postrun_"
        "finalization_binding"
    ),
    "teardown_deadline_protocol_complete",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_256_BIT_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class LinuxConfinementEvidenceCode(str, Enum):
    """Closed, nonreflecting prospective evidence failures."""

    INPUT_TYPE = "LINUX_CONFINEMENT_EVIDENCE_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_EVIDENCE_INPUT_RESOURCE"
    JSON_INVALID = "LINUX_CONFINEMENT_EVIDENCE_JSON_INVALID"
    SCHEMA_INVALID = "LINUX_CONFINEMENT_EVIDENCE_SCHEMA_INVALID"
    CANONICAL_MISMATCH = (
        "LINUX_CONFINEMENT_EVIDENCE_CANONICAL_MISMATCH"
    )
    POLICY_BINDING_MISMATCH = (
        "LINUX_CONFINEMENT_EVIDENCE_POLICY_BINDING_MISMATCH"
    )
    TRANSCRIPT_BINDING_MISMATCH = (
        "LINUX_CONFINEMENT_EVIDENCE_TRANSCRIPT_BINDING_MISMATCH"
    )
    INNER_RECEIPT_INVALID = (
        "LINUX_CONFINEMENT_EVIDENCE_INNER_RECEIPT_INVALID"
    )
    CLAIM_PROMOTION = "LINUX_CONFINEMENT_EVIDENCE_CLAIM_PROMOTION"
    INTERNAL = "LINUX_CONFINEMENT_EVIDENCE_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementEvidenceCode.INPUT_TYPE: (
            "Linux confinement evidence input has an invalid exact type"
        ),
        LinuxConfinementEvidenceCode.INPUT_RESOURCE: (
            "Linux confinement evidence input exceeds its byte ceiling"
        ),
        LinuxConfinementEvidenceCode.JSON_INVALID: (
            "Linux confinement evidence JSON is invalid"
        ),
        LinuxConfinementEvidenceCode.SCHEMA_INVALID: (
            "Linux confinement evidence schema is invalid"
        ),
        LinuxConfinementEvidenceCode.CANONICAL_MISMATCH: (
            "Linux confinement evidence bytes are not canonical"
        ),
        LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH: (
            "Linux confinement evidence policy binding differs"
        ),
        LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH: (
            "Linux confinement evidence transcript binding differs"
        ),
        LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID: (
            "Linux confinement evidence inner receipt is invalid"
        ),
        LinuxConfinementEvidenceCode.CLAIM_PROMOTION: (
            "Linux confinement prospective evidence promoted a claim"
        ),
        LinuxConfinementEvidenceCode.INTERNAL: (
            "Linux confinement evidence processing failed internally"
        ),
    }
)


class LinuxConfinementEvidenceError(ValueError):
    """One fixed-message error that never reflects untrusted bytes."""

    def __init__(self, code: LinuxConfinementEvidenceCode) -> None:
        if type(code) is not LinuxConfinementEvidenceCode:
            raise TypeError("Linux confinement evidence code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementEvidenceCode) -> None:
    raise LinuxConfinementEvidenceError(code) from None


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii", "strict"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _evidence_plan_artifact_type() -> str:
    try:
        value = (
            _evidence_plan
            .LINUX_CONFINEMENT_EVIDENCE_PLAN_ARTIFACT_TYPE
        )
    except AttributeError:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not str or not value:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _evidence_plan_sha256() -> str:
    try:
        value = _evidence_plan.linux_confinement_evidence_plan_sha256()
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _staging_contract_artifact_type() -> str:
    try:
        value = (
            _staging
            .LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_ARTIFACT_TYPE
        )
    except AttributeError:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not str or not value:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _staging_contract_sha256() -> str:
    try:
        value = (
            _staging
            .linux_confinement_staging_protocol_contract_sha256()
        )
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _staging_run_binding_artifact_type() -> str:
    try:
        value = (
            _staging
            .LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE
        )
    except AttributeError:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not str or not value:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _staging_run_binding_sha256(
    *,
    policy_sha256: str,
    supervisor_epoch_id_hex: str,
    run_sequence_number: int,
    run_nonce_hex: str,
) -> str:
    try:
        value = _staging.linux_confinement_staging_run_binding_sha256(
            policy_sha256=policy_sha256,
            supervisor_epoch_id_hex=supervisor_epoch_id_hex,
            run_sequence_number=run_sequence_number,
            run_nonce_hex=run_nonce_hex,
        )
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH)
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH)
    return value


def _evidence_plan_tree() -> dict:
    try:
        value = _evidence_plan.linux_confinement_evidence_plan_tree()
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not dict:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _staging_contract_tree() -> dict:
    try:
        value = _staging.linux_confinement_staging_protocol_contract_tree()
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if type(value) is not dict:
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return value


def _cross_contract_coherence_tree() -> dict:
    """Fail closed unless the fixed plan and staging vocabularies agree."""

    plan = _evidence_plan_tree()
    staging = _staging_contract_tree()
    try:
        spec_groups = tuple(
            plan[name]
            for name in (
                "observation_specs",
                "hostile_control_specs",
                "structural_join_specs",
            )
        )
        if any(type(group) is not list for group in spec_groups):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)
        all_subject_roles = []
        for group in spec_groups:
            for spec in group:
                if type(spec) is not dict:
                    _fail(LinuxConfinementEvidenceCode.INTERNAL)
                roles = spec["subject_role_ids"]
                if (
                    type(roles) is not list
                    or not roles
                    or any(type(role) is not str or not role for role in roles)
                ):
                    _fail(LinuxConfinementEvidenceCode.INTERNAL)
                all_subject_roles.extend(roles)
        role_counts = {
            role: all_subject_roles.count(role)
            for role in LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
        }
        if (
            any(count <= 0 for count in role_counts.values())
            or "bubblewrap-setup-child" not in all_subject_roles
            or "setup-child" in all_subject_roles
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)

        release_gates = plan["release_gate_specs"]
        if (
            type(release_gates) is not list
            or len(release_gates) != 2
            or any(type(gate) is not dict for gate in release_gates)
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)
        release_gate_event_ids = tuple(
            gate["staging_event_id"] for gate in release_gates
        )
        release_gate_ids = tuple(gate["gate_id"] for gate in release_gates)
        expected_release_gate_ids = (
            "stage1-required-observation-gate",
            "stage2-required-observation-gate",
        )
        expected_release_gate_event_ids = (
            "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
            "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED",
        )
        event_ids = staging["event_ids"]
        evidence_digest_event_ids = staging["evidence_digest_event_ids"]
        if (
            release_gate_ids != expected_release_gate_ids
            or release_gate_event_ids != expected_release_gate_event_ids
            or type(event_ids) is not list
            or type(evidence_digest_event_ids) is not list
            or any(
                type(event_id) is not str
                for event_id in event_ids + evidence_digest_event_ids
            )
            or any(
                event_id not in event_ids
                or event_id not in evidence_digest_event_ids
                for event_id in release_gate_event_ids
            )
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)
        gate_artifact_types = tuple(
            gate["preimage_artifact_type"] for gate in release_gates
        )
        gate_digest_domains = tuple(
            gate["preimage_digest_domain"] for gate in release_gates
        )
        gate_preimage_encoding_ids = tuple(
            gate["canonical_preimage_encoding_id"]
            for gate in release_gates
        )
        gate_digest_computation_ids = tuple(
            gate["preimage_digest_computation_id"]
            for gate in release_gates
        )
        expected_gate_artifact_types = (
            (
                "heterodiff.adapter.linux-confinement-stage1-"
                "release-gate-preimage.v1"
            ),
            (
                "heterodiff.adapter.linux-confinement-stage2-"
                "release-gate-preimage.v1"
            ),
        )
        expected_preimage_encoding_id = (
            "length-framed-declared-field-sequence-v1"
        )
        expected_digest_computation_id = (
            "sha256-domain-nul-u64be-length-canonical-preimage-v1"
        )
        if (
            any(
                type(value) is not str or not value
                for value in (
                    gate_artifact_types
                    + gate_digest_domains
                    + gate_preimage_encoding_ids
                    + gate_digest_computation_ids
                )
            )
            or gate_artifact_types != expected_gate_artifact_types
            or gate_artifact_types != gate_digest_domains
            or gate_preimage_encoding_ids
            != (expected_preimage_encoding_id,) * 2
            or gate_digest_computation_ids
            != (expected_digest_computation_id,) * 2
            or any(
                gate["canonical_preimage_constructed"] is not False
                or gate["canonical_preimage_validated"] is not False
                or gate["staging_event_recorded"] is not False
                for gate in release_gates
            )
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)

        completion = plan["inner_v1_completion_record_schema"]
        payload = staging["event_payload_schema"]
        plan_rules = plan["plan_rules"]
        if (
            type(completion) is not dict
            or type(payload) is not dict
            or type(plan_rules) is not dict
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)
        completion_artifact_type = completion["artifact_type"]
        completion_digest_domain = completion["digest_domain"]
        completion_digest_computation_id = completion[
            "digest_computation_id"
        ]
        completion_preimage_encoding_id = completion[
            "canonical_preimage_encoding_id"
        ]
        completion_event_id = completion["digest_transport_event_id"]
        completion_payload_field_id = completion[
            "digest_transport_event_payload_field_id"
        ]
        completion_semantics_id = completion[
            "digest_transport_semantics_id"
        ]
        staging_completion_semantics_id = payload[
            "inner_v1_complete_evidence_digest_semantics_id"
        ]
        staging_evidence_digest_encoding_id = payload[
            "evidence_digest_encoding_id"
        ]
        expected_completion_artifact_type = (
            _evidence_plan
            .LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        )
        expected_completion_semantics_id = (
            "caller-supplied-digest-shaped-reference-to-future-canonical-"
            "native-supervisor-inner-completion-record-v1"
        )
        if (
            type(completion_artifact_type) is not str
            or completion_artifact_type != expected_completion_artifact_type
            or completion_digest_domain != completion_artifact_type
            or completion_digest_computation_id
            != expected_digest_computation_id
            or completion_preimage_encoding_id
            != expected_preimage_encoding_id
            or completion_event_id != "INNER_V1_COMPLETE"
            or completion_event_id not in event_ids
            or completion_event_id not in evidence_digest_event_ids
            or completion_payload_field_id != "evidence_digest_sha256"
            or completion_semantics_id != expected_completion_semantics_id
            or completion_semantics_id
            != staging_completion_semantics_id
            or staging_evidence_digest_encoding_id
            != "lowercase-hex-fixed-64-nonzero-v1"
            or completion["canonical_preimage_constructed"] is not False
            or completion["canonical_preimage_validated"] is not False
            or completion["canonical_preimage_custody_validated"]
            is not False
            or completion["digest_recomputed"] is not False
            or completion[
                "full_release_transcript_digest_admitted_to_preimage"
            ]
            is not False
            or completion["staging_reducer_validates_digest_preimage"]
            is not False
            or completion["staging_reducer_validates_preimage_custody"]
            is not False
            or payload["evidence_digest_preimages_validated_by_reducer"]
            is not False
            or payload[
                "staging_run_binding_sha256_required_every_event"
            ]
            is not True
            or plan_rules["release_gate_preimage_validation_performed"]
            is not False
            or plan_rules[
                "inner_v1_completion_preimage_validation_performed"
            ]
            is not False
            or plan_rules[
                "inner_v1_complete_event_digest_is_completion_record_reference"
            ]
            is not True
            or plan_rules[
                "completion_record_contains_full_release_transcript_digest"
            ]
            is not False
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)

        postrun_binding_field_ids = plan[
            "postrun_leaf_finalization_binding_field_ids"
        ]
        plan_only_postrun_binding_field_ids = tuple(
            field_id
            for field_id in postrun_binding_field_ids
            if field_id
            not in LINUX_CONFINEMENT_OUTER_RECEIPT_BINDING_FIELD_IDS
        )
        if (
            type(postrun_binding_field_ids) is not list
            or not postrun_binding_field_ids
            or any(
                type(field_id) is not str or not field_id
                for field_id in postrun_binding_field_ids
            )
            or len(postrun_binding_field_ids)
            != len(set(postrun_binding_field_ids))
            or not plan_only_postrun_binding_field_ids
            or "inner-v1-completion-record-sha256"
            not in postrun_binding_field_ids
            or "full-release-transcript-sha256"
            not in postrun_binding_field_ids
            or plan_rules[
                "postrun_leaf_finalization_binding_required"
            ]
            is not True
            or plan_rules[
                "postrun_leaf_finalization_binding_is_append_only"
            ]
            is not True
            or plan_rules[
                "full_release_transcript_is_append_only_prefix_extension"
            ]
            is not True
        ):
            _fail(LinuxConfinementEvidenceCode.INTERNAL)
    except LinuxConfinementEvidenceError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)

    return {
        "all_process_identity_roles_occur_in_plan": True,
        "bubblewrap_setup_child_role_occurs_in_plan": True,
        "inner_v1_complete_digest_transport_matches_staging": True,
        "inner_v1_completion_record_artifact_type": (
            completion_artifact_type
        ),
        "inner_v1_completion_record_digest_computation_id": (
            completion_digest_computation_id
        ),
        "inner_v1_completion_record_digest_domain": (
            completion_digest_domain
        ),
        "inner_v1_completion_record_preimage_encoding_id": (
            completion_preimage_encoding_id
        ),
        "inner_v1_completion_record_plan_schema_defined": True,
        "inner_v1_completion_record_validation_performed": False,
        "inner_v1_complete_evidence_digest_encoding_id": (
            staging_evidence_digest_encoding_id
        ),
        "inner_v1_complete_event_payload_field_id": (
            completion_payload_field_id
        ),
        "inner_v1_complete_event_payload_semantics_id": (
            completion_semantics_id
        ),
        "legacy_setup_child_role_occurs_in_plan": False,
        "plan_postrun_leaf_finalization_binding_field_ids": list(
            postrun_binding_field_ids
        ),
        "plan_only_postrun_leaf_finalization_binding_field_ids": list(
            plan_only_postrun_binding_field_ids
        ),
        "process_identity_role_occurrence_counts": role_counts,
        "release_gate_event_ids_match_staging": True,
        "release_gate_ids": list(release_gate_ids),
        "release_gate_plan_preimage_artifact_types": list(
            gate_artifact_types
        ),
        "release_gate_plan_preimage_digest_computation_ids": list(
            gate_digest_computation_ids
        ),
        "release_gate_plan_preimage_digest_domains": list(
            gate_digest_domains
        ),
        "release_gate_plan_preimage_encoding_ids": list(
            gate_preimage_encoding_ids
        ),
        "release_gate_plan_schemas_defined": True,
        "release_gate_preimage_validation_performed": False,
        "release_gate_staging_event_ids": list(
            release_gate_event_ids
        ),
        (
            "synthetic_outer_binding_implements_plan_full_postrun_"
            "finalization_binding"
        ): False,
    }


def _fixed_false_state(ids: tuple[str, ...]) -> tuple[tuple[str, bool], ...]:
    return tuple((name, False) for name in ids)


_OUTER_POSITIVE_FALSE_STATE = _fixed_false_state(
    LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
)
_INHERITED_INNER_FALSE_STATE = _fixed_false_state(
    LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
)
_BROAD_FALSE_STATE = _fixed_false_state(
    LINUX_CONFINEMENT_FALSE_CLAIM_IDS
)
_PROSPECTIVE_BOUNDARY_FALSE_STATE = _fixed_false_state(
    _PROSPECTIVE_BOUNDARY_FALSE_FIELD_IDS
)


def _schema_contract_tree() -> dict:
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_ARTIFACT_TYPE
        ),
        "bound_contracts": {
            "acceptance_contract_artifact_type": (
                LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE
            ),
            "acceptance_contract_sha256": (
                linux_confinement_acceptance_contract_sha256()
            ),
            "base_policy_artifact_type": (
                LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE
            ),
            "evidence_plan_artifact_type": (
                _evidence_plan_artifact_type()
            ),
            "evidence_plan_sha256": _evidence_plan_sha256(),
            "staging_protocol_artifact_type": (
                _staging_contract_artifact_type()
            ),
            "staging_protocol_contract_sha256": (
                _staging_contract_sha256()
            ),
            "staging_run_binding_artifact_type": (
                _staging_run_binding_artifact_type()
            ),
        },
        "cross_contract_coherence": _cross_contract_coherence_tree(),
        "digest_semantics": {
            "acceptance-contract-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "evidence-schema-contract-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "evidence-plan-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "inner-v1-receipt-plain-sha256": "plain-sha256-v1",
            "inner-v1-receipt-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "linux-confinement-policy-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "staging-run-binding-sha256": (
                "staging-run-correlation-binding-sha256-v1"
            ),
            "synthetic-observation-transcript-sha256": (
                "unvalidated-digest-shaped-synthetic-fixture-v1"
            ),
            (
                "synthetic-pidfd-bound-process-identity-transcript-"
                "sha256"
            ): (
                "unvalidated-digest-shaped-synthetic-fixture-v1"
            ),
            "synthetic-release-transcript-sha256": (
                "unvalidated-digest-shaped-synthetic-fixture-v1"
            ),
            "staging-protocol-contract-sha256": (
                "length-framed-domain-sha256-v1"
            ),
            "synthetic-userns-map-observation-transcript-sha256": (
                "unvalidated-digest-shaped-synthetic-fixture-v1"
            ),
        },
        "fixed_requirements": {
            "all_claim_states_false": True,
            "builder_revalidates_inner_v1_receipt_exact_bytes": True,
            "canonical_ascii_json_required": True,
            "caller_asserted_match_is_not_evidence": True,
            (
                "digest_only_synthetic_joins_reject_cross_run_splice"
            ): False,
            (
                "direct_arbitrary_transcript_digests_prove_execution_"
                "or_confinement"
            ): False,
            "direct_synthetic_dataclass_proves_inner_bytes": False,
            "executed_postrun_finalization_envelope_defined": False,
            "executed_record_type_defined": False,
            "executed_transcript_preimage_type_defined": False,
            "executed_transcript_preimage_validator_defined": False,
            "future_executed_outer_receipt_type_defined": False,
            "inner_v1_false_fields_preserved": True,
            "linux_execution_performed": False,
            "native_supervisor_required_for_future_executed_record": True,
            (
                "native_supervisor_completion_record_validator_defined"
            ): False,
            "noncanonical_or_unknown_fields_rejected": True,
            "plan_inner_v1_completion_record_schema_defined": True,
            "plan_release_gate_preimage_schemas_defined": True,
            "raw_file_descriptor_number_is_process_identity": False,
            "release_gate_preimage_validator_defined": False,
            "staging_run_binding_is_correlation_syntax_only": True,
            "staging_run_binding_is_execution_evidence": False,
            (
                "synthetic_outer_binding_implements_plan_full_postrun_"
                "finalization_binding"
            ): False,
            "synthetic_fixture_is_execution_evidence": False,
            "teardown_deadline_protocol_complete": False,
        },
        "format_version": "1",
        "outer_receipt_schema": {
            "artifact_type": (
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE
            ),
            "binding_field_ids": list(
                LINUX_CONFINEMENT_OUTER_RECEIPT_BINDING_FIELD_IDS
            ),
            "broad_false_claim_ids": list(
                LINUX_CONFINEMENT_FALSE_CLAIM_IDS
            ),
            "decision_status_id": (
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DECISION_STATUS
            ),
            "execution_false_field_ids": list(
                _PROSPECTIVE_EXECUTION_FALSE_FIELD_IDS
            ),
            "inherited_inner_false_field_ids": list(
                LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
            ),
            "permitted_outer_positive_claim_ids": list(
                LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
            ),
            "record_origin_id": (
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ORIGIN
            ),
            "status_id": (
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_STATUS
            ),
            "synthetic_boundary_false_field_ids": list(
                _PROSPECTIVE_BOUNDARY_FALSE_FIELD_IDS
            ),
        },
        "prospective_observation_schema": {
            "admitted_result_ids": ["NOT_OBSERVED"],
            "mandatory_nonclaim_ids": list(
                LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS
            ),
            "required_hostile_control_ids": list(
                LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS
            ),
            "required_observation_ids": list(
                LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS
            ),
        },
        "prospective_release_schema": {
            "event_ids": list(LINUX_CONFINEMENT_RELEASE_EVENT_IDS),
            "process_identity_role_ids": list(
                LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
            ),
            "raw_fd_numbers_serialized": False,
            "run_nonce_is_authenticator": False,
            "run_nonce_is_secret": False,
        },
        "status_id": (
            LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_STATUS
        ),
        "target_status_id": LINUX_CONFINEMENT_TARGET_STATUS,
    }


def linux_confinement_evidence_schema_contract_tree() -> dict:
    """Return a fresh projection of the fixed prospective schema contract."""

    return _schema_contract_tree()


def linux_confinement_evidence_schema_contract_bytes() -> bytes:
    """Serialize the fixed prospective schema as canonical ASCII JSON."""

    try:
        result = json.dumps(
            _schema_contract_tree(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementEvidenceCode.INTERNAL)
    return result


def linux_confinement_evidence_schema_contract_sha256() -> str:
    """Return the length-framed domain digest of the schema contract."""

    return _domain_sha256(
        LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_evidence_schema_contract_bytes(),
    )


def _validate_digest(
    value: object,
    *,
    code: LinuxConfinementEvidenceCode,
) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(code)
    return value


def _validate_public_id(
    value: object,
    *,
    code: LinuxConfinementEvidenceCode,
) -> str:
    if (
        type(value) is not str
        or _PUBLIC_256_BIT_ID_RE.fullmatch(value) is None
        or value == "0" * 64
    ):
        _fail(code)
    return value


def _validate_false_state(
    value: object,
    *,
    expected: tuple[tuple[str, bool], ...],
) -> None:
    if (
        type(value) is not tuple
        or value != expected
        or any(
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not bool
            or item[1] is not False
            for item in value
        )
    ):
        _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)


@dataclass(frozen=True)
class ProspectiveLinuxConfinementOuterReceiptV1:
    """Synthetic join-shape fixture with every execution claim fixed false."""

    acceptance_contract_sha256: str
    evidence_plan_sha256: str
    linux_confinement_policy_sha256: str
    staging_protocol_contract_sha256: str
    staging_run_binding_sha256: str
    evidence_schema_contract_sha256: str
    supervisor_epoch_id_hex: str
    run_nonce_hex: str
    run_sequence_number: int
    synthetic_pidfd_bound_process_identity_transcript_sha256: str
    synthetic_observation_transcript_sha256: str
    synthetic_release_transcript_sha256: str
    synthetic_userns_map_observation_transcript_sha256: str
    inner_v1_receipt_byte_count: int
    inner_v1_receipt_plain_sha256: str
    inner_v1_receipt_sha256: str
    artifact_type: str = field(
        default=(
            PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE
        ),
        init=False,
    )
    format_version: str = field(default="1", init=False)
    record_origin_id: str = field(
        default=PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ORIGIN,
        init=False,
    )
    implementation_status_id: str = field(
        default=PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_STATUS,
        init=False,
    )
    target_status_id: str = field(
        default=LINUX_CONFINEMENT_TARGET_STATUS,
        init=False,
    )
    decision_status: str = field(
        default=(
            PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DECISION_STATUS
        ),
        init=False,
    )
    outer_positive_claim_state: tuple[tuple[str, bool], ...] = field(
        default=_OUTER_POSITIVE_FALSE_STATE,
        init=False,
    )
    inherited_inner_false_claim_state: tuple[
        tuple[str, bool], ...
    ] = field(
        default=_INHERITED_INNER_FALSE_STATE,
        init=False,
    )
    broad_claim_state: tuple[tuple[str, bool], ...] = field(
        default=_BROAD_FALSE_STATE,
        init=False,
    )
    synthetic_boundary_nonclaim_state: tuple[
        tuple[str, bool], ...
    ] = field(
        default=_PROSPECTIVE_BOUNDARY_FALSE_STATE,
        init=False,
    )
    evidence_observations_collected: bool = field(
        default=False,
        init=False,
    )
    hostile_controls_executed: bool = field(default=False, init=False)
    linux_execution_observed: bool = field(default=False, init=False)
    native_supervisor_executed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self) is not ProspectiveLinuxConfinementOuterReceiptV1:
            _fail(LinuxConfinementEvidenceCode.INPUT_TYPE)
        fixed = (
            (
                self.artifact_type,
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE,
            ),
            (self.format_version, "1"),
            (
                self.record_origin_id,
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ORIGIN,
            ),
            (
                self.implementation_status_id,
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_STATUS,
            ),
            (self.target_status_id, LINUX_CONFINEMENT_TARGET_STATUS),
            (
                self.decision_status,
                PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DECISION_STATUS,
            ),
        )
        if any(
            type(observed) is not str or observed != expected
            for observed, expected in fixed
        ):
            _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)
        if self.acceptance_contract_sha256 != (
            linux_confinement_acceptance_contract_sha256()
        ):
            _fail(
                LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH
            )
        _validate_digest(
            self.acceptance_contract_sha256,
            code=LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH,
        )
        _validate_digest(
            self.evidence_plan_sha256,
            code=(
                LinuxConfinementEvidenceCode
                .TRANSCRIPT_BINDING_MISMATCH
            ),
        )
        _validate_digest(
            self.staging_protocol_contract_sha256,
            code=(
                LinuxConfinementEvidenceCode
                .TRANSCRIPT_BINDING_MISMATCH
            ),
        )
        _validate_digest(
            self.evidence_schema_contract_sha256,
            code=(
                LinuxConfinementEvidenceCode
                .TRANSCRIPT_BINDING_MISMATCH
            ),
        )
        if self.staging_protocol_contract_sha256 != (
            _staging_contract_sha256()
        ) or self.evidence_schema_contract_sha256 != (
            linux_confinement_evidence_schema_contract_sha256()
        ) or self.evidence_plan_sha256 != (
            _evidence_plan_sha256()
        ):
            _fail(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            )
        _validate_digest(
            self.linux_confinement_policy_sha256,
            code=LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH,
        )
        epoch = _validate_public_id(
            self.supervisor_epoch_id_hex,
            code=LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH,
        )
        nonce = _validate_public_id(
            self.run_nonce_hex,
            code=LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH,
        )
        if epoch == nonce:
            _fail(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            )
        if (
            type(self.run_sequence_number) is not int
            or self.run_sequence_number < 0
            or self.run_sequence_number
            >= MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES
        ):
            _fail(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            )
        expected_run_binding = _staging_run_binding_sha256(
            policy_sha256=self.linux_confinement_policy_sha256,
            supervisor_epoch_id_hex=epoch,
            run_sequence_number=self.run_sequence_number,
            run_nonce_hex=nonce,
        )
        _validate_digest(
            self.staging_run_binding_sha256,
            code=(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            ),
        )
        if self.staging_run_binding_sha256 != expected_run_binding:
            _fail(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            )
        synthetic_transcript_digests = (
            self.synthetic_pidfd_bound_process_identity_transcript_sha256,
            self.synthetic_observation_transcript_sha256,
            self.synthetic_release_transcript_sha256,
            self.synthetic_userns_map_observation_transcript_sha256,
        )
        for value in synthetic_transcript_digests:
            _validate_digest(
                value,
                code=(
                    LinuxConfinementEvidenceCode
                    .TRANSCRIPT_BINDING_MISMATCH
                ),
            )
        if len(set(synthetic_transcript_digests)) != len(
            synthetic_transcript_digests
        ):
            _fail(
                LinuxConfinementEvidenceCode.TRANSCRIPT_BINDING_MISMATCH
            )
        if (
            type(self.inner_v1_receipt_byte_count) is not int
            or self.inner_v1_receipt_byte_count <= 0
            or self.inner_v1_receipt_byte_count
            > MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES
        ):
            _fail(LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID)
        inner_digests = (
            self.inner_v1_receipt_plain_sha256,
            self.inner_v1_receipt_sha256,
        )
        for value in inner_digests:
            _validate_digest(
                value,
                code=LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID,
            )
        if len(set(inner_digests)) != len(inner_digests):
            _fail(LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID)
        _validate_false_state(
            self.outer_positive_claim_state,
            expected=_OUTER_POSITIVE_FALSE_STATE,
        )
        _validate_false_state(
            self.inherited_inner_false_claim_state,
            expected=_INHERITED_INNER_FALSE_STATE,
        )
        _validate_false_state(
            self.broad_claim_state,
            expected=_BROAD_FALSE_STATE,
        )
        _validate_false_state(
            self.synthetic_boundary_nonclaim_state,
            expected=_PROSPECTIVE_BOUNDARY_FALSE_STATE,
        )
        if any(
            type(getattr(self, name)) is not bool
            or getattr(self, name) is not False
            for name in _PROSPECTIVE_EXECUTION_FALSE_FIELD_IDS
        ):
            _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)


def _receipt_tree(
    value: ProspectiveLinuxConfinementOuterReceiptV1,
) -> dict:
    return {
        "artifact_type": value.artifact_type,
        "bindings": {
            "acceptance_contract_sha256": (
                value.acceptance_contract_sha256
            ),
            "evidence_plan_sha256": value.evidence_plan_sha256,
            "evidence_schema_contract_sha256": (
                value.evidence_schema_contract_sha256
            ),
            "inner_v1_receipt_byte_count": (
                value.inner_v1_receipt_byte_count
            ),
            "inner_v1_receipt_plain_sha256": (
                value.inner_v1_receipt_plain_sha256
            ),
            "inner_v1_receipt_sha256": value.inner_v1_receipt_sha256,
            "linux_confinement_policy_sha256": (
                value.linux_confinement_policy_sha256
            ),
            "run_nonce_hex": value.run_nonce_hex,
            "run_sequence_number": value.run_sequence_number,
            "staging_protocol_contract_sha256": (
                value.staging_protocol_contract_sha256
            ),
            "staging_run_binding_sha256": (
                value.staging_run_binding_sha256
            ),
            "supervisor_epoch_id_hex": value.supervisor_epoch_id_hex,
            "synthetic_observation_transcript_sha256": (
                value.synthetic_observation_transcript_sha256
            ),
            (
                "synthetic_pidfd_bound_process_identity_transcript_"
                "sha256"
            ): (
                value
                .synthetic_pidfd_bound_process_identity_transcript_sha256
            ),
            "synthetic_release_transcript_sha256": (
                value.synthetic_release_transcript_sha256
            ),
            "synthetic_userns_map_observation_transcript_sha256": (
                value.synthetic_userns_map_observation_transcript_sha256
            ),
        },
        "claim_state": {
            "broad_claim_state": dict(value.broad_claim_state),
            "evidence_observations_collected": (
                value.evidence_observations_collected
            ),
            "hostile_controls_executed": (
                value.hostile_controls_executed
            ),
            "inherited_inner_false_claim_state": dict(
                value.inherited_inner_false_claim_state
            ),
            "linux_execution_observed": value.linux_execution_observed,
            "native_supervisor_executed": (
                value.native_supervisor_executed
            ),
            "outer_positive_claim_state": dict(
                value.outer_positive_claim_state
            ),
            "synthetic_boundary_nonclaim_state": dict(
                value.synthetic_boundary_nonclaim_state
            ),
        },
        "decision_status": value.decision_status,
        "format_version": value.format_version,
        "implementation_status_id": value.implementation_status_id,
        "record_origin_id": value.record_origin_id,
        "target_status_id": value.target_status_id,
    }


def _validate_receipt(
    value: object,
) -> ProspectiveLinuxConfinementOuterReceiptV1:
    if type(value) is not ProspectiveLinuxConfinementOuterReceiptV1:
        _fail(LinuxConfinementEvidenceCode.INPUT_TYPE)
    try:
        ProspectiveLinuxConfinementOuterReceiptV1.__post_init__(value)
    except LinuxConfinementEvidenceError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
    return value


def prospective_linux_confinement_outer_receipt_tree(
    value: ProspectiveLinuxConfinementOuterReceiptV1,
) -> dict:
    """Return a fresh canonical-tree projection of one prospective receipt."""

    return _receipt_tree(_validate_receipt(value))


def prospective_linux_confinement_outer_receipt_bytes(
    value: ProspectiveLinuxConfinementOuterReceiptV1,
) -> bytes:
    """Serialize one all-false prospective receipt as canonical ASCII JSON."""

    receipt = _validate_receipt(value)
    try:
        result = json.dumps(
            _receipt_tree(receipt),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (AttributeError, TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_BYTES
    ):
        _fail(LinuxConfinementEvidenceCode.INPUT_RESOURCE)
    return result


def prospective_linux_confinement_outer_receipt_sha256(
    value: ProspectiveLinuxConfinementOuterReceiptV1,
) -> str:
    """Return the length-framed domain digest of a prospective receipt."""

    return _domain_sha256(
        PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DIGEST_DOMAIN,
        prospective_linux_confinement_outer_receipt_bytes(value),
    )


def _inner_receipt_identities(
    value: object,
) -> tuple[int, str, str]:
    if type(value) is not SourceBoundAdapterChildRunReceiptV1:
        _fail(LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID)
    try:
        SourceBoundAdapterChildRunReceiptV1.__post_init__(value)
        raw = source_bound_adapter_child_run_receipt_bytes(value)
        domain_digest = source_bound_adapter_child_run_receipt_sha256(
            value
        )
    except Exception:
        _fail(LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID)
    if (
        any(
            not hasattr(value, name) or getattr(value, name) is not False
            for name in LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
        )
        or value.artifact_type
        != SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
    ):
        _fail(LinuxConfinementEvidenceCode.INNER_RECEIPT_INVALID)
    return (
        len(raw),
        hashlib.sha256(raw).hexdigest(),
        domain_digest,
    )


def build_prospective_linux_confinement_outer_receipt(
    policy: LinuxConfinementPolicyV1,
    inner_v1_receipt: SourceBoundAdapterChildRunReceiptV1,
    *,
    supervisor_epoch_id_hex: str,
    run_nonce_hex: str,
    run_sequence_number: int,
    synthetic_pidfd_bound_process_identity_transcript_sha256: str,
    synthetic_observation_transcript_sha256: str,
    synthetic_release_transcript_sha256: str,
    synthetic_userns_map_observation_transcript_sha256: str,
) -> ProspectiveLinuxConfinementOuterReceiptV1:
    """Build an all-false synthetic shape, not an executed transcript join."""

    if type(policy) is not LinuxConfinementPolicyV1:
        _fail(
            LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH
        )
    try:
        linux_confinement_policy_bytes(policy)
        policy_digest = linux_confinement_policy_sha256(policy)
    except Exception:
        _fail(
            LinuxConfinementEvidenceCode.POLICY_BINDING_MISMATCH
        )
    inner_count, inner_plain, inner_domain = _inner_receipt_identities(
        inner_v1_receipt
    )
    run_binding = _staging_run_binding_sha256(
        policy_sha256=policy_digest,
        supervisor_epoch_id_hex=supervisor_epoch_id_hex,
        run_sequence_number=run_sequence_number,
        run_nonce_hex=run_nonce_hex,
    )
    try:
        return ProspectiveLinuxConfinementOuterReceiptV1(
            acceptance_contract_sha256=(
                linux_confinement_acceptance_contract_sha256()
            ),
            evidence_plan_sha256=(
                _evidence_plan_sha256()
            ),
            linux_confinement_policy_sha256=policy_digest,
            staging_protocol_contract_sha256=(
                _staging_contract_sha256()
            ),
            staging_run_binding_sha256=run_binding,
            evidence_schema_contract_sha256=(
                linux_confinement_evidence_schema_contract_sha256()
            ),
            supervisor_epoch_id_hex=supervisor_epoch_id_hex,
            run_nonce_hex=run_nonce_hex,
            run_sequence_number=run_sequence_number,
            synthetic_pidfd_bound_process_identity_transcript_sha256=(
                synthetic_pidfd_bound_process_identity_transcript_sha256
            ),
            synthetic_observation_transcript_sha256=(
                synthetic_observation_transcript_sha256
            ),
            synthetic_release_transcript_sha256=(
                synthetic_release_transcript_sha256
            ),
            synthetic_userns_map_observation_transcript_sha256=(
                synthetic_userns_map_observation_transcript_sha256
            ),
            inner_v1_receipt_byte_count=inner_count,
            inner_v1_receipt_plain_sha256=inner_plain,
            inner_v1_receipt_sha256=inner_domain,
        )
    except LinuxConfinementEvidenceError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)


class _DuplicateKeyError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError()
        result[key] = value
    return result


def _reject_constant(_: str) -> object:
    raise ValueError()


def _exact_keys(value: object, expected: set[str]) -> dict:
    if (
        type(value) is not dict
        or any(type(key) is not str for key in value)
        or set(value) != expected
    ):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
    return value


def _parsed_false_state(
    value: object,
    *,
    expected_ids: tuple[str, ...],
) -> tuple[tuple[str, bool], ...]:
    mapping = _exact_keys(value, set(expected_ids))
    if any(type(item) is not bool for item in mapping.values()):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
    if any(item is not False for item in mapping.values()):
        _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)
    return tuple((name, mapping[name]) for name in expected_ids)


def parse_prospective_linux_confinement_outer_receipt(
    raw: bytes,
) -> ProspectiveLinuxConfinementOuterReceiptV1:
    """Strictly parse, reconstruct, and canonical-check arbitrary bytes."""

    if type(raw) is not bytes:
        _fail(LinuxConfinementEvidenceCode.INPUT_TYPE)
    if (
        not raw
        or len(raw)
        > MAXIMUM_PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_BYTES
    ):
        _fail(LinuxConfinementEvidenceCode.INPUT_RESOURCE)
    try:
        tree = json.loads(
            raw.decode("ascii", "strict"),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except (
        UnicodeError,
        json.JSONDecodeError,
        _DuplicateKeyError,
        RecursionError,
        ValueError,
    ):
        _fail(LinuxConfinementEvidenceCode.JSON_INVALID)
    tree = _exact_keys(
        tree,
        {
            "artifact_type",
            "bindings",
            "claim_state",
            "decision_status",
            "format_version",
            "implementation_status_id",
            "record_origin_id",
            "target_status_id",
        },
    )
    bindings = _exact_keys(
        tree["bindings"],
        {
            "acceptance_contract_sha256",
            "evidence_plan_sha256",
            "evidence_schema_contract_sha256",
            "inner_v1_receipt_byte_count",
            "inner_v1_receipt_plain_sha256",
            "inner_v1_receipt_sha256",
            "linux_confinement_policy_sha256",
            "run_nonce_hex",
            "run_sequence_number",
            "staging_protocol_contract_sha256",
            "staging_run_binding_sha256",
            "supervisor_epoch_id_hex",
            "synthetic_observation_transcript_sha256",
            (
                "synthetic_pidfd_bound_process_identity_transcript_"
                "sha256"
            ),
            "synthetic_release_transcript_sha256",
            "synthetic_userns_map_observation_transcript_sha256",
        },
    )
    claims = _exact_keys(
        tree["claim_state"],
        {
            "broad_claim_state",
            "evidence_observations_collected",
            "hostile_controls_executed",
            "inherited_inner_false_claim_state",
            "linux_execution_observed",
            "native_supervisor_executed",
            "outer_positive_claim_state",
            "synthetic_boundary_nonclaim_state",
        },
    )
    _parsed_false_state(
        claims["outer_positive_claim_state"],
        expected_ids=(
            LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
        ),
    )
    _parsed_false_state(
        claims["inherited_inner_false_claim_state"],
        expected_ids=(
            LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
        ),
    )
    _parsed_false_state(
        claims["broad_claim_state"],
        expected_ids=LINUX_CONFINEMENT_FALSE_CLAIM_IDS,
    )
    _parsed_false_state(
        claims["synthetic_boundary_nonclaim_state"],
        expected_ids=_PROSPECTIVE_BOUNDARY_FALSE_FIELD_IDS,
    )
    for name in _PROSPECTIVE_EXECUTION_FALSE_FIELD_IDS:
        value = claims[name]
        if type(value) is not bool:
            _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
        if value is not False:
            _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)
    try:
        receipt = ProspectiveLinuxConfinementOuterReceiptV1(
            acceptance_contract_sha256=(
                bindings["acceptance_contract_sha256"]
            ),
            evidence_plan_sha256=bindings["evidence_plan_sha256"],
            linux_confinement_policy_sha256=(
                bindings["linux_confinement_policy_sha256"]
            ),
            staging_protocol_contract_sha256=(
                bindings["staging_protocol_contract_sha256"]
            ),
            staging_run_binding_sha256=(
                bindings["staging_run_binding_sha256"]
            ),
            evidence_schema_contract_sha256=(
                bindings["evidence_schema_contract_sha256"]
            ),
            supervisor_epoch_id_hex=(
                bindings["supervisor_epoch_id_hex"]
            ),
            run_nonce_hex=bindings["run_nonce_hex"],
            run_sequence_number=bindings["run_sequence_number"],
            synthetic_pidfd_bound_process_identity_transcript_sha256=(
                bindings[
                    (
                        "synthetic_pidfd_bound_process_identity_"
                        "transcript_sha256"
                    )
                ]
            ),
            synthetic_observation_transcript_sha256=(
                bindings["synthetic_observation_transcript_sha256"]
            ),
            synthetic_release_transcript_sha256=(
                bindings["synthetic_release_transcript_sha256"]
            ),
            synthetic_userns_map_observation_transcript_sha256=(
                bindings[
                    (
                        "synthetic_userns_map_observation_"
                        "transcript_sha256"
                    )
                ]
            ),
            inner_v1_receipt_byte_count=(
                bindings["inner_v1_receipt_byte_count"]
            ),
            inner_v1_receipt_plain_sha256=(
                bindings["inner_v1_receipt_plain_sha256"]
            ),
            inner_v1_receipt_sha256=(
                bindings["inner_v1_receipt_sha256"]
            ),
        )
    except LinuxConfinementEvidenceError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail(LinuxConfinementEvidenceCode.SCHEMA_INVALID)
    fixed = (
        (tree["artifact_type"], receipt.artifact_type),
        (tree["decision_status"], receipt.decision_status),
        (tree["format_version"], receipt.format_version),
        (
            tree["implementation_status_id"],
            receipt.implementation_status_id,
        ),
        (tree["record_origin_id"], receipt.record_origin_id),
        (tree["target_status_id"], receipt.target_status_id),
    )
    if any(
        type(observed) is not str or observed != expected
        for observed, expected in fixed
    ):
        _fail(LinuxConfinementEvidenceCode.CLAIM_PROMOTION)
    if prospective_linux_confinement_outer_receipt_bytes(receipt) != raw:
        _fail(LinuxConfinementEvidenceCode.CANONICAL_MISMATCH)
    return receipt


__all__ = [
    "LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_STATUS",
    "LINUX_CONFINEMENT_OUTER_RECEIPT_BINDING_FIELD_IDS",
    "LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS",
    "LINUX_CONFINEMENT_RELEASE_EVENT_IDS",
    "MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_SCHEMA_CONTRACT_BYTES",
    "MAXIMUM_PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_BYTES",
    "PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ARTIFACT_TYPE",
    "PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DECISION_STATUS",
    "PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_DIGEST_DOMAIN",
    "PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_ORIGIN",
    "PROSPECTIVE_LINUX_CONFINEMENT_OUTER_RECEIPT_STATUS",
    "LinuxConfinementEvidenceCode",
    "LinuxConfinementEvidenceError",
    "ProspectiveLinuxConfinementOuterReceiptV1",
    "build_prospective_linux_confinement_outer_receipt",
    "linux_confinement_evidence_schema_contract_bytes",
    "linux_confinement_evidence_schema_contract_sha256",
    "linux_confinement_evidence_schema_contract_tree",
    "parse_prospective_linux_confinement_outer_receipt",
    "prospective_linux_confinement_outer_receipt_bytes",
    "prospective_linux_confinement_outer_receipt_sha256",
    "prospective_linux_confinement_outer_receipt_tree",
]
