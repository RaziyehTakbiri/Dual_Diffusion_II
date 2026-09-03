"""Pure, activation-gated PhysioNet 2012 admission preflight.

The module accepts caller-supplied, content-addressed receipts and normalized
patient identifiers.  It performs no filesystem, archive, network, process,
entropy, training, inference, or scientific-result operation.  Synthetic
receipts can qualify the deterministic contracts.  Real-shaped receipts are
accepted only with an explicit structural activation record and can become no
more than eligible for a separate independent admission decision.

In particular, this module does not authenticate an authority, governance
decision, dataset, hash, private locator, proof, or audit merely because a
caller supplies a correctly shaped value.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Dict, Optional, Tuple


DOMAIN_ID = "physionet-challenge-2012"
SLOT_ID = "R3-PHYS"

SYNTHETIC_STATE = "SYNTHETIC_QUALIFICATION_ONLY"
ACTIVATED_REAL_STATE = "ACTIVATED_REAL_INSTANCE_STRUCTURAL_RECEIPTS_ONLY"
ACTIVATION_STATES = (SYNTHETIC_STATE, ACTIVATED_REAL_STATE)

PARSER_ID = "HETERODIFF_PHYSIONET_2012_LOSSLESS_RAW_PARSER_V1"
PARSER_SOURCE_SHA256 = (
    "ff869134bfd696964c23bf7a2dbd0b2b428811b0fb3058cd7f3bd688dd48968c"
)
INVENTORY_ID = "HETERODIFF_PHYSIONET_2012_EXPLICIT_ALLOWLIST_INVENTORY_V1"
INVENTORY_SOURCE_SHA256 = (
    "50f3eb80ba284400c4dea76a04a162b72be090bc62628b692dca548c3a203985"
)
F105_TRANSFORM_ID = "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1:R3-PHYS:R112"
F105_TRANSFORM_SOURCE_SHA256 = (
    "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881"
)
SPLIT_ALGORITHM_ID = "PHYSIONET_PATIENT_HASH_EXPLICIT_F061_HAMILTON_V1"
CANDIDATE_SPLIT_ALGORITHM_ID = "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256 = (
    "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
)
SPLIT_CONTRACT_SCHEMA_VERSION = (
    "heterodiff-physionet-explicit-f061-hamilton-split-contract-v1"
)
F061_ROUNDING_RULE_ID = (
    "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
)
SHARED_F061_POLICY_SCHEMA = "heterodiff-two-domain-f061-shared-policy-v1"
SHARED_F061_POLICY_MODE = "EXACT_PROPORTIONS_HAMILTON"
PHYSIONET_F061_ADAPTER_ID = (
    "SHARED_POLICY_AND_NATURAL_GROUP_COUNT_TO_PHYSIONET_F061_PROPOSAL_ADAPTER_V1"
)
PHYSIONET_F061_ADAPTER_SHA256 = (
    "018def4ab7d7f991d4820da612489b5162d91d8c04e4231f3429295cb032a52b"
)
PHYSIONET_RESOLVED_F061_REVIEW_SCOPE = (
    "PHYSIONET_SNAPSHOT_RESOLVED_COUNTS_AND_NATIVE_PROPOSAL_V1"
)

OBSERVATION_KERNEL_ID = "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"
COMMON_SUPPORT_ROUTE_ID = (
    "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
    "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
)
ADMISSION_STATISTIC_ID = "MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1"
ADMISSION_THRESHOLD_ID = "ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1"
DUPLICATE_AUDIT_ALGORITHM_ID = (
    "PHYSIONET_METHOD_BLIND_CROSS_SPLIT_RECORD_LINEAGE_AUDIT_V1"
)
DUPLICATE_NEAR_RULE_ID = (
    "PHYSIONET_REVIEWED_METHOD_BLIND_NEAR_DUPLICATE_LINEAGE_RULE_V1"
)
DUPLICATE_AUDIT_IMPLEMENTATION_ID = (
    "PHYSIONET_COMPLETE_CROSS_SPLIT_RECORD_PAIR_AUDIT_POLICY_V1"
)
DUPLICATE_AUDIT_IMPLEMENTATION_SCHEMA_VERSION = (
    "heterodiff-physionet-duplicate-audit-implementation-v1"
)

SPLIT_NAMES = ("TRAIN", "VALIDATION", "TEST")
CANDIDATE_ALLOCATION_NUMERATORS = (70, 15, 15)
CANDIDATE_ALLOCATION_DENOMINATOR = 100
CANDIDATE_MINIMUM_COUNTS = (1, 1, 1)
CANDIDATE_MINIMUM_PATIENT_COUNT = 5
VIOLATION_EVALUATION_SPLIT = "TRAIN"

ADMISSION_COMPONENTS = (
    "raw_format_failures",
    "identity_failures",
    "unknown_or_unbound_event_type_rows",
    "missing_or_invalid_required_value_rows",
    "event_transform_collisions",
    "horizon_violations",
    "cap_or_overflow_violations",
    "row_exclusions",
    "natural_group_exclusions",
    "natural_group_split_overlaps",
    "split_contract_failures",
    "clean_kernel_normalization_failures",
    "observation_subset_failures",
)
REQUIRED_RECEIPT_FLAGS = (
    "snapshot_hash_verified",
    "license_access_record_verified",
    "governance_approval_verified",
    "complete_split_manifest_verified",
    "duplicate_and_near_duplicate_audit_verified",
    "observation_reference_and_support_receipt_verified",
)

PATIENT_ORDER_DOMAIN_HEX = (
    "68657465726f646966662f70687973696f6e65742d70617469656e742d6f7264"
    "65722f763100"
)
PATIENT_ORDER_DOMAIN = bytes.fromhex(PATIENT_ORDER_DOMAIN_HEX)
PATIENT_ORDER_DOMAIN_SHA256 = hashlib.sha256(PATIENT_ORDER_DOMAIN).hexdigest()
PATIENT_ORDER_LENGTH_PREFIX_BYTES = 2
PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER = "big"
PATIENT_ORDER_LENGTH_PREFIX_SIGNED = False
PATIENT_ORDER_PATIENT_ENCODING = "ascii"
PATIENT_ORDER_HASH_ALGORITHM = "sha256"
PATIENT_ORDER_PRIMARY_SORT = "DIGEST_BYTES_ASCENDING"
PATIENT_ORDER_TIE_BREAK = "PATIENT_ASCII_BYTES_ASCENDING"
SPLIT_IMPLEMENTATION_ID = (
    "PHYSIONET_EXPLICIT_F061_PATIENT_HASH_CONTIGUOUS_ASSIGNMENT_V1"
)
SPLIT_IMPLEMENTATION_SCHEMA_VERSION = (
    "heterodiff-physionet-explicit-f061-split-implementation-v1"
)
NORMALIZED_PROJECTION_DOMAIN = (
    b"heterodiff/physionet-normalized-split-input/v1\x00"
)
SNAPSHOT_RECEIPT_DOMAIN = b"heterodiff/physionet-b02-snapshot-receipt/v1\x00"
SPLIT_RECEIPT_DOMAIN = b"heterodiff/physionet-split-manifest/v1\x00"
ADMISSION_RECEIPT_DOMAIN = b"heterodiff/physionet-b02-admission-preflight/v1\x00"
ADMISSION_EVIDENCE_DOMAIN = b"heterodiff/physionet-b02-admission-evidence/v1\x00"
F061_PROPOSAL_DOMAIN = b"heterodiff/physionet-f061-allocation-proposal/v1\x00"
F061_REVIEW_BINDING_DOMAIN = b"heterodiff/physionet-f061-review-binding/v1\x00"
SHARED_F061_DEFINITION_DOMAIN = (
    b"heterodiff/two-domain-f061-shared-policy-definition/v1\x00"
)
SHARED_F061_PROPOSAL_DOMAIN = (
    b"heterodiff/two-domain-f061-shared-policy-proposal/v1\x00"
)
PHYSIONET_F061_ADAPTER_DOMAIN = (
    b"heterodiff/two-domain-f061-physionet-adapter-contract/v1\x00"
)
EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN = (
    b"heterodiff/physionet-explicit-f061-split-contract/v1\x00"
)
SPLIT_IMPLEMENTATION_DOMAIN = (
    b"heterodiff/physionet-explicit-f061-split-implementation/v1\x00"
)
GOVERNANCE_RECEIPT_DOMAIN = b"heterodiff/physionet-b02-governance-receipt/v1\x00"
SUPPORT_RECEIPT_DOMAIN = b"heterodiff/physionet-b02-support-receipt/v1\x00"
DUPLICATE_AUDIT_RECEIPT_DOMAIN = (
    b"heterodiff/physionet-b02-duplicate-audit-receipt/v1\x00"
)
DUPLICATE_AUDIT_IMPLEMENTATION_DOMAIN = (
    b"heterodiff/physionet-b02-duplicate-audit-implementation/v1\x00"
)
DUPLICATE_AUDIT_ASSIGNMENT_MANIFEST_DOMAIN = (
    b"heterodiff/physionet-b02-duplicate-audit-assignment-manifest/v1\x00"
)
DUPLICATE_AUDIT_INPUT_DOMAIN = (
    b"heterodiff/physionet-b02-duplicate-audit-input/v1\x00"
)
DUPLICATE_AUDIT_COMPLETION_DOMAIN = (
    b"heterodiff/physionet-b02-duplicate-audit-completion/v1\x00"
)
SYNTHETIC_DIGEST_DOMAIN = b"heterodiff/physionet-b02-synthetic-receipt/v1\x00"

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_SOURCE_LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_PATIENT_ID_RE = re.compile(r"[1-9][0-9]{0,63}\Z")
_RECORD_PATH_RE = re.compile(r"[1-9][0-9]{0,63}\.txt\Z")
_MODELING_ROLE_LABELS = frozenset(
    {"train", "training", "val", "valid", "validation", "test", "testing"}
)
_PLACEHOLDER_TOKENS = frozenset(
    {"none", "null", "pending", "tbd", "todo", "unknown", "unresolved"}
)


class AdmissionPreflightError(ValueError):
    """Raised when an offline receipt or preflight contract fails closed."""


def _exact_string(value: object, *, name: str, maximum: int = 256) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or not value.isascii()
        or value != value.strip()
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
    ):
        raise AdmissionPreflightError(
            f"{name} must be a nonempty bounded printable-ASCII exact string"
        )
    return value


def _exact_token(value: object, *, name: str) -> str:
    result = _exact_string(value, name=name, maximum=128)
    if _SAFE_TOKEN_RE.fullmatch(result) is None:
        raise AdmissionPreflightError(f"{name} is not a normalized token")
    return result


def _nonplaceholder_token(value: object, *, name: str) -> str:
    result = _exact_token(value, name=name)
    if result.casefold() in _PLACEHOLDER_TOKENS:
        raise AdmissionPreflightError(f"{name} must not be a placeholder")
    return result


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise AdmissionPreflightError(
            f"{name} must be a lowercase 64-character SHA-256 digest"
        )
    return value


def _optional_sha256(value: object, *, name: str) -> Optional[str]:
    if value is None:
        return None
    return _sha256(value, name=name)


def _exact_int(value: object, *, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise AdmissionPreflightError(
            f"{name} must be an exact integer greater than or equal to {minimum}"
        )
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise AdmissionPreflightError(f"{name} must be an exact Boolean")
    return value


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AdmissionPreflightError("value is not canonical ASCII JSON") from exc


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + _canonical_bytes(value)).hexdigest()


def physionet_f061_adapter_record() -> Dict[str, object]:
    """Return the canonical shared-policy-to-PhysioNet adapter contract."""

    return {
        "schema_version": "heterodiff-f061-adapter-contract-v1",
        "adapter_id": PHYSIONET_F061_ADAPTER_ID,
        "source_schema": SHARED_F061_POLICY_SCHEMA,
        "target_schema": "PHYSIONET_F061_SNAPSHOT_RESOLVED_PROPOSAL_CODEC_V1",
        "required_inputs": [
            "values",
            "denominator",
            "minimum_counts",
            "rounding_rule_id",
            "natural_group_count",
        ],
        "outputs": [
            "patient_count",
            "numerators",
            "denominator",
            "counts",
            "minimum_counts",
            "rounding_rule_id",
        ],
        "algorithm": (
            "HAMILTON_DESCENDING_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
        ),
        "review_semantics": (
            "REQUIRES_SEPARATE_LATER_PHYSIONET_RESOLVED_COUNT_REVIEW_V1"
        ),
    }


def physionet_f061_adapter_sha256() -> str:
    return _digest(
        PHYSIONET_F061_ADAPTER_DOMAIN,
        physionet_f061_adapter_record(),
    )


def shared_f061_policy_proposal_sha256(
    *,
    allocation_id: object,
    values: object,
    denominator: object,
    minimum_counts: object,
    rounding_rule_id: object,
    power_requirement_id: object,
) -> str:
    checked_allocation_id = _nonplaceholder_token(
        allocation_id,
        name="shared F061 allocation_id",
    )
    checked_power_requirement_id = _nonplaceholder_token(
        power_requirement_id,
        name="shared F061 power_requirement_id",
    )
    if type(values) is not tuple or len(values) != 3:
        raise AdmissionPreflightError(
            "shared F061 values must be an exact triple"
        )
    checked_values = tuple(
        _exact_int(value, name="shared F061 value", minimum=1)
        for value in values
    )
    checked_denominator = _exact_int(
        denominator,
        name="shared F061 denominator",
        minimum=1,
    )
    if sum(checked_values) != checked_denominator:
        raise AdmissionPreflightError(
            "shared F061 values must sum to denominator"
        )
    if type(minimum_counts) is not tuple or len(minimum_counts) != 3:
        raise AdmissionPreflightError(
            "shared F061 minimum_counts must be an exact triple"
        )
    checked_minimums = tuple(
        _exact_int(value, name="shared F061 minimum", minimum=1)
        for value in minimum_counts
    )
    if (
        type(rounding_rule_id) is not str
        or rounding_rule_id != F061_ROUNDING_RULE_ID
    ):
        raise AdmissionPreflightError("shared F061 rounding-rule identity drift")
    return _digest(
        SHARED_F061_PROPOSAL_DOMAIN,
        {
            "schema_version": SHARED_F061_POLICY_SCHEMA,
            "allocation_id": checked_allocation_id,
            "mode": SHARED_F061_POLICY_MODE,
            "values": checked_values,
            "denominator_is_null": False,
            "denominator": checked_denominator,
            "minimum_counts": checked_minimums,
            "rounding_rule_id": rounding_rule_id,
            "power_requirement_id": checked_power_requirement_id,
        },
    )


def shared_f061_policy_definition_sha256(
    *,
    allocation_proposal_sha256: object,
    power_review_receipt_sha256: object,
    power_review_accepted: object,
) -> str:
    proposal = _sha256(
        allocation_proposal_sha256,
        name="shared F061 allocation_proposal_sha256",
    )
    review = _sha256(
        power_review_receipt_sha256,
        name="shared F061 power_review_receipt_sha256",
    )
    if _exact_bool(
        power_review_accepted,
        name="shared F061 power_review_accepted",
    ) is not True:
        raise AdmissionPreflightError(
            "shared F061 policy review must explicitly accept"
        )
    return _digest(
        SHARED_F061_DEFINITION_DOMAIN,
        {
            "allocation_proposal_sha256": proposal,
            "power_review_receipt_sha256": review,
            "power_review_accepted": True,
        },
    )


def _validate_physionet_f061_adapter_identity() -> None:
    if physionet_f061_adapter_sha256() != PHYSIONET_F061_ADAPTER_SHA256:
        raise AdmissionPreflightError("PhysioNet F061 adapter identity drift")


def duplicate_audit_implementation_record() -> Dict[str, object]:
    """Return the exact content-addressed method-blind audit policy."""

    return {
        "schema_version": DUPLICATE_AUDIT_IMPLEMENTATION_SCHEMA_VERSION,
        "implementation_id": DUPLICATE_AUDIT_IMPLEMENTATION_ID,
        "identity_kind": (
            "CANONICAL_EXTERNAL_AUDIT_POLICY_SPECIFICATION_NOT_SOURCE_BYTES"
        ),
        "audit_algorithm_id": DUPLICATE_AUDIT_ALGORITHM_ID,
        "near_duplicate_rule_id": DUPLICATE_NEAR_RULE_ID,
        "audit_unit": "PRESERVED_NORMALIZED_RECORD_LINEAGE",
        "eligible_pair_rule": (
            "EVERY_UNORDERED_RECORD_PAIR_WHOSE_ASSIGNED_SPLITS_DIFFER"
        ),
        "eligible_pair_count_formula": (
            "TRAIN_X_VALIDATION_PLUS_TRAIN_X_TEST_PLUS_VALIDATION_X_TEST"
        ),
        "required_findings": [
            "exact_duplicate_cross_split_count",
            "near_duplicate_cross_split_count",
        ],
        "complete_roster_required": True,
        "checked_pair_count_must_equal_eligible_pair_count": True,
        "model_outcome_or_label_content_inspection_permitted": False,
        "input_bindings": [
            "snapshot_receipt_sha256",
            "split_manifest_sha256",
            "normalized_projection_sha256",
            "assignment_manifest_sha256",
            "record_count",
            "patient_count",
            "eligible_cross_split_record_pair_count",
        ],
        "completion_bindings": [
            "audit_input_manifest_sha256",
            "completion_certificate_sha256",
            "checked_cross_split_record_pair_count",
            "complete_roster_checked",
            "exact_duplicate_cross_split_count",
            "near_duplicate_cross_split_count",
            "outcome_or_label_content_inspected",
            "audit_verification_receipt_sha256",
        ],
    }


DUPLICATE_AUDIT_IMPLEMENTATION_SHA256 = _digest(
    DUPLICATE_AUDIT_IMPLEMENTATION_DOMAIN,
    duplicate_audit_implementation_record(),
)


def _validate_duplicate_audit_implementation_identity() -> None:
    if _digest(
        DUPLICATE_AUDIT_IMPLEMENTATION_DOMAIN,
        duplicate_audit_implementation_record(),
    ) != DUPLICATE_AUDIT_IMPLEMENTATION_SHA256:
        raise AdmissionPreflightError(
            "duplicate audit implementation identity drift"
        )


def split_implementation_record() -> Dict[str, object]:
    """Return the exact content-addressed split policy executed below."""

    return {
        "schema_version": SPLIT_IMPLEMENTATION_SCHEMA_VERSION,
        "implementation_id": SPLIT_IMPLEMENTATION_ID,
        "identity_kind": (
            "CANONICAL_EXECUTABLE_POLICY_SPECIFICATION_NOT_SOURCE_BYTES"
        ),
        "patient_input": "DISTINCT_VALIDATED_PATIENT_ID_STRINGS",
        "patient_encoding": PATIENT_ORDER_PATIENT_ENCODING,
        "ordering_digest": {
            "hash_algorithm": PATIENT_ORDER_HASH_ALGORITHM,
            "domain_bytes_hex": PATIENT_ORDER_DOMAIN.hex(),
            "domain_bytes_sha256": hashlib.sha256(
                PATIENT_ORDER_DOMAIN
            ).hexdigest(),
            "length_prefix_width_bytes": PATIENT_ORDER_LENGTH_PREFIX_BYTES,
            "length_prefix_byteorder": PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER,
            "length_prefix_signed": PATIENT_ORDER_LENGTH_PREFIX_SIGNED,
            "message_fields_in_order": [
                "domain_bytes",
                "patient_byte_length_prefix",
                "patient_bytes",
            ],
        },
        "patient_sort": {
            "primary": PATIENT_ORDER_PRIMARY_SORT,
            "tie_break": PATIENT_ORDER_TIE_BREAK,
        },
        "split_sequence": list(SPLIT_NAMES),
        "allocation_counts_source": "EXACT_REVIEWED_F061_HAMILTON_COUNTS",
        "assignment_rule": (
            "CONTIGUOUS_ORDERED_PATIENT_SLICES_BY_SPLIT_SEQUENCE_AND_COUNTS"
        ),
        "receipt_patient_order": "PATIENT_ASCII_BYTES_ASCENDING",
        "record_assignment_rule": (
            "PRESERVE_RECORD_ORDINAL_AND_INHERIT_PATIENT_SPLIT"
        ),
    }


SPLIT_IMPLEMENTATION_SHA256 = _digest(
    SPLIT_IMPLEMENTATION_DOMAIN,
    split_implementation_record(),
)


def explicit_f061_split_contract_record() -> Dict[str, object]:
    """Return the canonical successor contract, distinct from the 70/15/15 design."""

    return {
        "schema_version": SPLIT_CONTRACT_SCHEMA_VERSION,
        "domain_id": DOMAIN_ID,
        "slot_id": SLOT_ID,
        "split_algorithm_id": SPLIT_ALGORITHM_ID,
        "split_implementation_id": SPLIT_IMPLEMENTATION_ID,
        "split_implementation_sha256": SPLIT_IMPLEMENTATION_SHA256,
        "split_implementation": split_implementation_record(),
        "historical_candidate_algorithm_id": CANDIDATE_SPLIT_ALGORITHM_ID,
        "historical_candidate_contract_raw_sha256": (
            HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
        ),
        "split_names": list(SPLIT_NAMES),
        "allocation_mode": "EXACT_PROPORTIONS_HAMILTON",
        "rounding_rule_id": F061_ROUNDING_RULE_ID,
        "allocation_review_state_required": "POWER_REVIEWED",
        "allocation_proposal_fields": [
            "patient_count",
            "numerators",
            "denominator",
            "counts",
            "minimum_counts",
            "rounding_rule_id",
        ],
        "external_review_binding_fields": [
            "proposal_sha256",
            "accepted",
            "review_receipt_sha256",
            "review_locator",
        ],
        "patient_id": "MINIMAL_POSITIVE_ASCII_DECIMAL_STRING_MAX_64_BYTES",
        "patient_order_domain_bytes_hex": PATIENT_ORDER_DOMAIN_HEX,
        "patient_order_domain_bytes_sha256": PATIENT_ORDER_DOMAIN_SHA256,
        "patient_order_length_prefix_width_bytes": (
            PATIENT_ORDER_LENGTH_PREFIX_BYTES
        ),
        "patient_order_length_prefix_byteorder": (
            PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER
        ),
        "patient_order_length_prefix_signed": PATIENT_ORDER_LENGTH_PREFIX_SIGNED,
        "patient_order_patient_encoding": PATIENT_ORDER_PATIENT_ENCODING,
        "patient_order_hash_algorithm": PATIENT_ORDER_HASH_ALGORITHM,
        "patient_order_primary_sort": PATIENT_ORDER_PRIMARY_SORT,
        "patient_order_tie_break": PATIENT_ORDER_TIE_BREAK,
        "records_and_patients_preserved": True,
        "patient_disjoint": True,
        "exclusion_retry_resplit_topup_permitted": False,
        "filesystem_network_process_entropy_or_data_opening": False,
    }


SPLIT_CONTRACT_SHA256 = _digest(
    EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN,
    explicit_f061_split_contract_record(),
)


def _validate_split_implementation_identity() -> None:
    if PATIENT_ORDER_DOMAIN.hex() != PATIENT_ORDER_DOMAIN_HEX:
        raise AdmissionPreflightError("patient ordering domain identity drift")
    if hashlib.sha256(PATIENT_ORDER_DOMAIN).hexdigest() != (
        PATIENT_ORDER_DOMAIN_SHA256
    ):
        raise AdmissionPreflightError(
            "patient ordering domain digest identity drift"
        )
    if _digest(
        SPLIT_IMPLEMENTATION_DOMAIN,
        split_implementation_record(),
    ) != SPLIT_IMPLEMENTATION_SHA256:
        raise AdmissionPreflightError("split implementation identity drift")
    if _digest(
        EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN,
        explicit_f061_split_contract_record(),
    ) != SPLIT_CONTRACT_SHA256:
        raise AdmissionPreflightError("split contract identity drift")


def _revalidate_exact_dataclass(value: object, expected_type: type) -> bool:
    """Re-run frozen dataclass invariants and detect low-level mutation."""

    if type(value) is not expected_type:
        return False
    try:
        values = {
            item.name: getattr(value, item.name)
            for item in fields(value)
            if item.init
        }
        rebuilt = expected_type(**values)
    except (AdmissionPreflightError, AttributeError, TypeError, ValueError):
        return False
    return rebuilt == value


def synthetic_digest(label: object, role: object) -> str:
    checked_label = _exact_token(label, name="synthetic label")
    checked_role = _exact_token(role, name="synthetic role")
    return hashlib.sha256(
        SYNTHETIC_DIGEST_DOMAIN
        + checked_label.encode("ascii")
        + b"\x00"
        + checked_role.encode("ascii")
    ).hexdigest()


@dataclass(frozen=True)
class PrivateLocator:
    """Opaque custody-root identity plus a normalized relative private path."""

    custody_root_id: str
    relative_path: str

    def __post_init__(self) -> None:
        _exact_token(self.custody_root_id, name="custody_root_id")
        path = _exact_string(self.relative_path, name="relative_path", maximum=512)
        if path.startswith("/") or "\\" in path or "\x00" in path:
            raise AdmissionPreflightError("private locator path must be relative POSIX")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise AdmissionPreflightError("private locator path is not normalized")
        if str(PurePosixPath(path)) != path:
            raise AdmissionPreflightError("private locator path is not canonical")

    def to_dict(self) -> Dict[str, str]:
        return {
            "custody_root_id": self.custody_root_id,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True)
class ActivationReceipt:
    """Structural gate only; never an authentication claim by this module."""

    state: str
    activation_id: str
    reviewed_precontact_instance_sha256: Optional[str]
    independent_precontact_review_sha256: Optional[str]
    data_access_authority_sha256: Optional[str]
    custody_approval_sha256: Optional[str]

    def __post_init__(self) -> None:
        if type(self.state) is not str or self.state not in ACTIVATION_STATES:
            raise AdmissionPreflightError("activation state is not frozen")
        _exact_token(self.activation_id, name="activation_id")
        values = (
            self.reviewed_precontact_instance_sha256,
            self.independent_precontact_review_sha256,
            self.data_access_authority_sha256,
            self.custody_approval_sha256,
        )
        if self.state == SYNTHETIC_STATE:
            if any(value is not None for value in values):
                raise AdmissionPreflightError(
                    "synthetic activation must not carry operational authority hashes"
                )
        else:
            names = (
                "reviewed_precontact_instance_sha256",
                "independent_precontact_review_sha256",
                "data_access_authority_sha256",
                "custody_approval_sha256",
            )
            for name, value in zip(names, values):
                _sha256(value, name=name)

    @property
    def real_instance_structurally_enabled(self) -> bool:
        return self.state == ACTIVATED_REAL_STATE

    def to_dict(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "activation_id": self.activation_id,
            "reviewed_precontact_instance_sha256": self.reviewed_precontact_instance_sha256,
            "independent_precontact_review_sha256": self.independent_precontact_review_sha256,
            "data_access_authority_sha256": self.data_access_authority_sha256,
            "custody_approval_sha256": self.custody_approval_sha256,
            "authority_authenticated_by_this_module": False,
        }


def synthetic_activation(label: object = "DEFAULT") -> ActivationReceipt:
    checked = _exact_token(label, name="synthetic activation label")
    return ActivationReceipt(
        state=SYNTHETIC_STATE,
        activation_id="SYNTHETIC:" + checked,
        reviewed_precontact_instance_sha256=None,
        independent_precontact_review_sha256=None,
        data_access_authority_sha256=None,
        custody_approval_sha256=None,
    )


@dataclass(frozen=True)
class ToolchainIdentity:
    parser_id: str = PARSER_ID
    parser_source_sha256: str = PARSER_SOURCE_SHA256
    inventory_id: str = INVENTORY_ID
    inventory_source_sha256: str = INVENTORY_SOURCE_SHA256
    f105_transform_id: str = F105_TRANSFORM_ID
    f105_transform_source_sha256: str = F105_TRANSFORM_SOURCE_SHA256
    split_algorithm_id: str = SPLIT_ALGORITHM_ID
    candidate_split_algorithm_id: str = CANDIDATE_SPLIT_ALGORITHM_ID
    split_contract_sha256: str = SPLIT_CONTRACT_SHA256

    def __post_init__(self) -> None:
        expected = (
            ("parser_id", PARSER_ID),
            ("parser_source_sha256", PARSER_SOURCE_SHA256),
            ("inventory_id", INVENTORY_ID),
            ("inventory_source_sha256", INVENTORY_SOURCE_SHA256),
            ("f105_transform_id", F105_TRANSFORM_ID),
            ("f105_transform_source_sha256", F105_TRANSFORM_SOURCE_SHA256),
            ("split_algorithm_id", SPLIT_ALGORITHM_ID),
            ("candidate_split_algorithm_id", CANDIDATE_SPLIT_ALGORITHM_ID),
            ("split_contract_sha256", SPLIT_CONTRACT_SHA256),
        )
        for name, value in expected:
            if type(getattr(self, name)) is not str or getattr(self, name) != value:
                raise AdmissionPreflightError(f"toolchain identity drift: {name}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "parser_id": self.parser_id,
            "parser_source_sha256": self.parser_source_sha256,
            "inventory_id": self.inventory_id,
            "inventory_source_sha256": self.inventory_source_sha256,
            "f105_transform_id": self.f105_transform_id,
            "f105_transform_source_sha256": self.f105_transform_source_sha256,
            "split_algorithm_id": self.split_algorithm_id,
            "candidate_split_algorithm_id": self.candidate_split_algorithm_id,
            "split_contract_sha256": self.split_contract_sha256,
        }


@dataclass(frozen=True)
class RawArchiveReceipt:
    activation: ActivationReceipt
    domain_id: str
    snapshot_version: str
    raw_archive_sha256: str
    raw_archive_bytes: int
    source_version_receipt_sha256: str
    license_access_receipt_sha256: str
    archive_locator: PrivateLocator
    access_outcome_receipt_sha256: Optional[str]

    def __post_init__(self) -> None:
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("raw archive requires an exact activation")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "raw archive activation fails exact revalidation"
            )
        if type(self.domain_id) is not str or self.domain_id != DOMAIN_ID:
            raise AdmissionPreflightError("raw archive domain is not PhysioNet")
        _exact_string(self.snapshot_version, name="snapshot_version", maximum=128)
        _sha256(self.raw_archive_sha256, name="raw_archive_sha256")
        _exact_int(self.raw_archive_bytes, name="raw_archive_bytes", minimum=1)
        _sha256(
            self.source_version_receipt_sha256,
            name="source_version_receipt_sha256",
        )
        _sha256(
            self.license_access_receipt_sha256,
            name="license_access_receipt_sha256",
        )
        if type(self.archive_locator) is not PrivateLocator:
            raise AdmissionPreflightError("archive_locator must be exact")
        if not _revalidate_exact_dataclass(self.archive_locator, PrivateLocator):
            raise AdmissionPreflightError(
                "archive_locator fails exact revalidation"
            )
        access = _optional_sha256(
            self.access_outcome_receipt_sha256,
            name="access_outcome_receipt_sha256",
        )
        if self.activation.state == SYNTHETIC_STATE and access is not None:
            raise AdmissionPreflightError(
                "synthetic archive must not carry a real access-outcome receipt"
            )
        if self.activation.state == ACTIVATED_REAL_STATE and access is None:
            raise AdmissionPreflightError(
                "activated real archive requires an access-outcome receipt"
            )

    def to_dict(self) -> Dict[str, object]:
        return {
            "activation_id": self.activation.activation_id,
            "receipt_state": self.activation.state,
            "domain_id": self.domain_id,
            "snapshot_version": self.snapshot_version,
            "raw_archive_sha256": self.raw_archive_sha256,
            "raw_archive_bytes": self.raw_archive_bytes,
            "source_version_receipt_sha256": self.source_version_receipt_sha256,
            "license_access_receipt_sha256": self.license_access_receipt_sha256,
            "archive_locator": self.archive_locator.to_dict(),
            "access_outcome_receipt_sha256": self.access_outcome_receipt_sha256,
            "archive_bytes_opened_or_hashed_by_this_module": False,
        }


@dataclass(frozen=True)
class AllowlistedFileReceipt:
    file_ordinal: int
    source_partition: str
    logical_path: str
    record_id: str
    raw_sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        _exact_int(self.file_ordinal, name="file_ordinal")
        label = _exact_string(
            self.source_partition, name="source_partition", maximum=64
        )
        if (
            _SOURCE_LABEL_RE.fullmatch(label) is None
            or label.casefold() in _MODELING_ROLE_LABELS
        ):
            raise AdmissionPreflightError(
                "source_partition must be a source label, not a modeling role"
            )
        path = _exact_string(self.logical_path, name="logical_path", maximum=512)
        if path.startswith("/") or "\\" in path:
            raise AdmissionPreflightError("allowlisted logical path must be relative POSIX")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise AdmissionPreflightError("allowlisted logical path is not normalized")
        if str(PurePosixPath(path)) != path:
            raise AdmissionPreflightError("allowlisted logical path is not canonical")
        record_id = _exact_string(self.record_id, name="record_id", maximum=64)
        if _PATIENT_ID_RE.fullmatch(record_id) is None:
            raise AdmissionPreflightError("record_id must be minimal positive ASCII decimal")
        if _RECORD_PATH_RE.fullmatch(PurePosixPath(path).name) is None:
            raise AdmissionPreflightError("allowlisted filename must be a numeric .txt record")
        if PurePosixPath(path).stem != record_id:
            raise AdmissionPreflightError("record_id must equal the filename stem")
        _sha256(self.raw_sha256, name="allowlisted raw_sha256")
        _exact_int(self.byte_count, name="allowlisted byte_count", minimum=1)

    def to_dict(self) -> Dict[str, object]:
        return {
            "file_ordinal": self.file_ordinal,
            "source_partition": self.source_partition,
            "logical_path": self.logical_path,
            "record_id": self.record_id,
            "raw_sha256": self.raw_sha256,
            "byte_count": self.byte_count,
        }


@dataclass(frozen=True)
class PatientRecord:
    record_ordinal: int
    patient_id: str

    def __post_init__(self) -> None:
        _exact_int(self.record_ordinal, name="record_ordinal")
        value = _exact_string(self.patient_id, name="patient_id", maximum=64)
        if _PATIENT_ID_RE.fullmatch(value) is None:
            raise AdmissionPreflightError(
                "patient_id must be minimal positive ASCII decimal"
            )

    def to_dict(self) -> Dict[str, object]:
        return {
            "record_ordinal": self.record_ordinal,
            "patient_id": self.patient_id,
        }


def _canonical_patient_projection(rows: object) -> Tuple[PatientRecord, ...]:
    if type(rows) is not tuple or not rows:
        raise AdmissionPreflightError("patient projection must be a nonempty exact tuple")
    if any(type(row) is not PatientRecord for row in rows):
        raise AdmissionPreflightError("patient projection has an inexact row")
    if any(
        not _revalidate_exact_dataclass(row, PatientRecord)
        for row in rows
    ):
        raise AdmissionPreflightError(
            "patient projection row fails exact revalidation"
        )
    ordered = tuple(sorted(rows, key=lambda row: row.record_ordinal))
    if tuple(row.record_ordinal for row in ordered) != tuple(range(len(ordered))):
        raise AdmissionPreflightError("record ordinals must be exactly 0..R-1")
    return ordered


def normalized_projection_sha256(rows: object) -> str:
    ordered = _canonical_patient_projection(rows)
    return _digest(
        NORMALIZED_PROJECTION_DOMAIN,
        [row.to_dict() for row in ordered],
    )


@dataclass(frozen=True)
class SnapshotReceipt:
    activation: ActivationReceipt
    archive: RawArchiveReceipt
    allowlisted_files: Tuple[AllowlistedFileReceipt, ...]
    patient_projection: Tuple[PatientRecord, ...]
    source_schema_receipt_sha256: str
    toolchain: ToolchainIdentity
    snapshot_locator: PrivateLocator
    snapshot_verification_receipt_sha256: Optional[str]
    post_snapshot_exclusion_count: int = 0
    retry_resplit_topup_count: int = 0
    archive_inventory_sha256: str = field(init=False)
    normalized_projection_sha256: str = field(init=False)
    snapshot_receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("snapshot requires an exact activation")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "snapshot activation fails exact revalidation"
            )
        if type(self.archive) is not RawArchiveReceipt:
            raise AdmissionPreflightError("snapshot archive receipt is inexact")
        if not _revalidate_exact_dataclass(self.archive, RawArchiveReceipt):
            raise AdmissionPreflightError(
                "snapshot archive receipt fails exact revalidation"
            )
        if self.archive.activation != self.activation:
            raise AdmissionPreflightError("archive and snapshot activation differ")
        if type(self.allowlisted_files) is not tuple or not self.allowlisted_files:
            raise AdmissionPreflightError("allowlisted files must be a nonempty tuple")
        if any(type(row) is not AllowlistedFileReceipt for row in self.allowlisted_files):
            raise AdmissionPreflightError("allowlisted file roster has an inexact row")
        if any(
            not _revalidate_exact_dataclass(row, AllowlistedFileReceipt)
            for row in self.allowlisted_files
        ):
            raise AdmissionPreflightError(
                "allowlisted file roster row fails exact revalidation"
            )
        files = tuple(sorted(self.allowlisted_files, key=lambda row: row.file_ordinal))
        if tuple(row.file_ordinal for row in files) != tuple(range(len(files))):
            raise AdmissionPreflightError("file ordinals must be exactly 0..R-1")
        if len({row.logical_path for row in files}) != len(files):
            raise AdmissionPreflightError("allowlisted logical paths must be unique")
        if len({row.record_id for row in files}) != len(files):
            raise AdmissionPreflightError("allowlisted RecordIDs must be unique")
        projection = _canonical_patient_projection(self.patient_projection)
        if len(files) != len(projection):
            raise AdmissionPreflightError("file and patient projection counts differ")
        for file_row, patient_row in zip(files, projection):
            if (
                file_row.file_ordinal != patient_row.record_ordinal
                or file_row.record_id != patient_row.patient_id
            ):
                raise AdmissionPreflightError(
                    "allowlisted file roster does not bind the patient projection"
                )
        _sha256(
            self.source_schema_receipt_sha256,
            name="source_schema_receipt_sha256",
        )
        if type(self.toolchain) is not ToolchainIdentity:
            raise AdmissionPreflightError("snapshot toolchain identity is inexact")
        if not _revalidate_exact_dataclass(self.toolchain, ToolchainIdentity):
            raise AdmissionPreflightError(
                "snapshot toolchain identity fails exact revalidation"
            )
        if type(self.snapshot_locator) is not PrivateLocator:
            raise AdmissionPreflightError("snapshot_locator must be exact")
        if not _revalidate_exact_dataclass(self.snapshot_locator, PrivateLocator):
            raise AdmissionPreflightError(
                "snapshot_locator fails exact revalidation"
            )
        verification = _optional_sha256(
            self.snapshot_verification_receipt_sha256,
            name="snapshot_verification_receipt_sha256",
        )
        if self.activation.state == SYNTHETIC_STATE and verification is not None:
            raise AdmissionPreflightError(
                "synthetic snapshot must not carry external verification"
            )
        if self.activation.state == ACTIVATED_REAL_STATE and verification is None:
            raise AdmissionPreflightError(
                "activated real snapshot requires independent verification receipt"
            )
        _exact_int(
            self.post_snapshot_exclusion_count,
            name="post_snapshot_exclusion_count",
        )
        _exact_int(
            self.retry_resplit_topup_count,
            name="retry_resplit_topup_count",
        )
        if self.post_snapshot_exclusion_count != 0:
            raise AdmissionPreflightError("post-snapshot exclusion is forbidden")
        if self.retry_resplit_topup_count != 0:
            raise AdmissionPreflightError("retry, resplit, or top-up is forbidden")
        object.__setattr__(self, "allowlisted_files", files)
        object.__setattr__(self, "patient_projection", projection)
        inventory_digest = _digest(
            b"heterodiff/physionet-b02-allowlisted-inventory/v1\x00",
            [row.to_dict() for row in files],
        )
        projection_digest = normalized_projection_sha256(projection)
        object.__setattr__(self, "archive_inventory_sha256", inventory_digest)
        object.__setattr__(self, "normalized_projection_sha256", projection_digest)
        payload = self._payload()
        object.__setattr__(
            self,
            "snapshot_receipt_sha256",
            _digest(SNAPSHOT_RECEIPT_DOMAIN, payload),
        )

    @property
    def externally_verified(self) -> bool:
        return (
            self.activation.state == ACTIVATED_REAL_STATE
            and self.archive.access_outcome_receipt_sha256 is not None
            and self.snapshot_verification_receipt_sha256 is not None
        )

    def _payload(self) -> Dict[str, object]:
        return {
            "activation": self.activation.to_dict(),
            "archive": self.archive.to_dict(),
            "allowlisted_files": [row.to_dict() for row in self.allowlisted_files],
            "patient_projection": [row.to_dict() for row in self.patient_projection],
            "source_schema_receipt_sha256": self.source_schema_receipt_sha256,
            "toolchain": self.toolchain.to_dict(),
            "snapshot_locator": self.snapshot_locator.to_dict(),
            "snapshot_verification_receipt_sha256": self.snapshot_verification_receipt_sha256,
            "post_snapshot_exclusion_count": self.post_snapshot_exclusion_count,
            "retry_resplit_topup_count": self.retry_resplit_topup_count,
            "archive_inventory_sha256": self.archive_inventory_sha256,
            "normalized_projection_sha256": self.normalized_projection_sha256,
            "raw_or_normalized_data_opened_by_this_module": False,
        }

    def to_dict(self) -> Dict[str, object]:
        result = self._payload()
        result["snapshot_receipt_sha256"] = self.snapshot_receipt_sha256
        result["externally_verified"] = self.externally_verified
        return result


def f061_allocation_proposal_sha256(
    *,
    patient_count: object,
    numerators: object,
    denominator: object,
    counts: object,
    minimum_counts: object,
    rounding_rule_id: object,
    shared_policy_allocation_id: object = None,
    shared_policy_values: object = None,
    shared_policy_denominator: object = None,
    shared_policy_minimum_counts: object = None,
    shared_policy_rounding_rule_id: object = None,
    shared_policy_power_requirement_id: object = None,
    shared_policy_proposal_sha256: object = None,
    shared_policy_review_receipt_sha256: object = None,
    shared_policy_review_accepted: object = None,
    shared_policy_definition_sha256: object = None,
    physionet_adapter_id: object = None,
    physionet_adapter_sha256: object = None,
) -> str:
    """Return the canonical digest of one exact F061 allocation proposal."""

    checked_patient_count = _exact_int(
        patient_count,
        name="F061 proposal patient_count",
        minimum=1,
    )
    if type(numerators) is not tuple or len(numerators) != 3:
        raise AdmissionPreflightError(
            "F061 proposal numerators must be an exact triple"
        )
    checked_numerators = tuple(
        _exact_int(value, name=f"F061 proposal {name} numerator", minimum=1)
        for name, value in zip(SPLIT_NAMES, numerators)
    )
    checked_denominator = _exact_int(
        denominator,
        name="F061 proposal denominator",
        minimum=1,
    )
    if sum(checked_numerators) != checked_denominator:
        raise AdmissionPreflightError(
            "F061 proposal numerators must sum exactly to its denominator"
        )
    if type(counts) is not tuple or len(counts) != 3:
        raise AdmissionPreflightError("F061 proposal counts must be an exact triple")
    checked_counts = tuple(
        _exact_int(value, name=f"F061 proposal {name} count", minimum=1)
        for name, value in zip(SPLIT_NAMES, counts)
    )
    if type(minimum_counts) is not tuple or len(minimum_counts) != 3:
        raise AdmissionPreflightError(
            "F061 proposal minimum_counts must be an exact triple"
        )
    checked_minimum_counts = tuple(
        _exact_int(value, name=f"F061 proposal {name} minimum", minimum=1)
        for name, value in zip(SPLIT_NAMES, minimum_counts)
    )
    if (
        type(rounding_rule_id) is not str
        or rounding_rule_id != F061_ROUNDING_RULE_ID
    ):
        raise AdmissionPreflightError("F061 proposal rounding-rule identity drift")
    if sum(checked_counts) != checked_patient_count:
        raise AdmissionPreflightError("F061 proposal counts do not exhaust patients")
    if checked_counts != _hamilton_counts(
        checked_patient_count,
        checked_numerators,  # type: ignore[arg-type]
        checked_denominator,
    ):
        raise AdmissionPreflightError(
            "F061 proposal counts do not match its exact Hamilton allocation"
        )
    if any(
        value < minimum
        for value, minimum in zip(checked_counts, checked_minimum_counts)
    ):
        raise AdmissionPreflightError(
            "F061 proposal is underpowered against its reviewed minimum_counts"
        )
    provenance_values = (
        shared_policy_allocation_id,
        shared_policy_values,
        shared_policy_denominator,
        shared_policy_minimum_counts,
        shared_policy_rounding_rule_id,
        shared_policy_power_requirement_id,
        shared_policy_proposal_sha256,
        shared_policy_review_receipt_sha256,
        shared_policy_review_accepted,
        shared_policy_definition_sha256,
        physionet_adapter_id,
        physionet_adapter_sha256,
    )
    if all(value is None for value in provenance_values):
        checked_shared_proposal = None
        checked_shared_allocation_id = None
        checked_shared_values = None
        checked_shared_denominator = None
        checked_shared_minimums = None
        checked_shared_rounding = None
        checked_shared_power_requirement_id = None
        checked_shared_review = None
        checked_shared_accepted = None
        checked_shared_definition = None
        checked_adapter_id = None
        checked_adapter_sha256 = None
    else:
        if any(value is None for value in provenance_values):
            raise AdmissionPreflightError(
                "F061 shared-policy provenance must be complete or all-null"
            )
        _validate_physionet_f061_adapter_identity()
        checked_shared_allocation_id = _nonplaceholder_token(
            shared_policy_allocation_id,
            name="F061 shared-policy allocation_id",
        )
        if type(shared_policy_values) is not tuple:
            raise AdmissionPreflightError(
                "F061 shared-policy values must be an exact triple"
            )
        checked_shared_values = shared_policy_values
        checked_shared_denominator = _exact_int(
            shared_policy_denominator,
            name="F061 shared-policy denominator",
            minimum=1,
        )
        if type(shared_policy_minimum_counts) is not tuple:
            raise AdmissionPreflightError(
                "F061 shared-policy minimum_counts must be an exact triple"
            )
        checked_shared_minimums = shared_policy_minimum_counts
        if (
            type(shared_policy_rounding_rule_id) is not str
            or shared_policy_rounding_rule_id != F061_ROUNDING_RULE_ID
        ):
            raise AdmissionPreflightError(
                "F061 shared-policy rounding-rule identity drift"
            )
        checked_shared_rounding = shared_policy_rounding_rule_id
        checked_shared_power_requirement_id = _nonplaceholder_token(
            shared_policy_power_requirement_id,
            name="F061 shared-policy power_requirement_id",
        )
        if (
            checked_shared_values != checked_numerators
            or checked_shared_denominator != checked_denominator
            or checked_shared_minimums != checked_minimum_counts
        ):
            raise AdmissionPreflightError(
                "PhysioNet native F061 proposal differs from shared policy"
            )
        checked_shared_proposal = _sha256(
            shared_policy_proposal_sha256,
            name="F061 shared-policy proposal_sha256",
        )
        if checked_shared_proposal != shared_f061_policy_proposal_sha256(
            allocation_id=checked_shared_allocation_id,
            values=checked_shared_values,
            denominator=checked_shared_denominator,
            minimum_counts=checked_shared_minimums,
            rounding_rule_id=checked_shared_rounding,
            power_requirement_id=checked_shared_power_requirement_id,
        ):
            raise AdmissionPreflightError(
                "F061 shared-policy proposal digest mismatch"
            )
        checked_shared_review = _sha256(
            shared_policy_review_receipt_sha256,
            name="F061 shared-policy review_receipt_sha256",
        )
        checked_shared_accepted = _exact_bool(
            shared_policy_review_accepted,
            name="F061 shared-policy review accepted",
        )
        if checked_shared_accepted is not True:
            raise AdmissionPreflightError(
                "F061 shared-policy review must explicitly accept"
            )
        checked_shared_definition = _sha256(
            shared_policy_definition_sha256,
            name="F061 shared-policy definition_sha256",
        )
        if checked_shared_definition != shared_f061_policy_definition_sha256(
            allocation_proposal_sha256=checked_shared_proposal,
            power_review_receipt_sha256=checked_shared_review,
            power_review_accepted=True,
        ):
            raise AdmissionPreflightError(
                "F061 shared-policy definition digest mismatch"
            )
        if (
            type(physionet_adapter_id) is not str
            or physionet_adapter_id != PHYSIONET_F061_ADAPTER_ID
        ):
            raise AdmissionPreflightError("PhysioNet F061 adapter identity drift")
        checked_adapter_id = physionet_adapter_id
        if (
            type(physionet_adapter_sha256) is not str
            or physionet_adapter_sha256 != PHYSIONET_F061_ADAPTER_SHA256
        ):
            raise AdmissionPreflightError("PhysioNet F061 adapter digest drift")
        checked_adapter_sha256 = physionet_adapter_sha256
    payload = {
        "domain_id": DOMAIN_ID,
        "slot_id": SLOT_ID,
        "split_names": list(SPLIT_NAMES),
        "patient_count": checked_patient_count,
        "numerators": list(checked_numerators),
        "denominator": checked_denominator,
        "counts": list(checked_counts),
        "minimum_counts": list(checked_minimum_counts),
        "rounding_rule_id": rounding_rule_id,
        "shared_policy_schema": SHARED_F061_POLICY_SCHEMA,
        "shared_policy_allocation_id": checked_shared_allocation_id,
        "shared_policy_mode": (
            None if checked_shared_allocation_id is None else SHARED_F061_POLICY_MODE
        ),
        "shared_policy_values": checked_shared_values,
        "shared_policy_denominator": checked_shared_denominator,
        "shared_policy_minimum_counts": checked_shared_minimums,
        "shared_policy_rounding_rule_id": checked_shared_rounding,
        "shared_policy_power_requirement_id": (
            checked_shared_power_requirement_id
        ),
        "shared_policy_proposal_sha256": checked_shared_proposal,
        "shared_policy_review_receipt_sha256": checked_shared_review,
        "shared_policy_review_accepted": checked_shared_accepted,
        "shared_policy_definition_sha256": checked_shared_definition,
        "physionet_adapter_id": checked_adapter_id,
        "physionet_adapter_sha256": checked_adapter_sha256,
        "resolved_count_review_scope": PHYSIONET_RESOLVED_F061_REVIEW_SCOPE,
    }
    return _digest(F061_PROPOSAL_DOMAIN, payload)


@dataclass(frozen=True)
class F061ExternalReviewBinding:
    """Explicit accepted external review of one exact F061 proposal digest."""

    proposal_sha256: str
    accepted: bool
    review_receipt_sha256: str
    review_locator: PrivateLocator
    binding_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _sha256(self.proposal_sha256, name="F061 reviewed proposal_sha256")
        if _exact_bool(self.accepted, name="F061 review accepted") is not True:
            raise AdmissionPreflightError("F061 external review must explicitly accept")
        _sha256(self.review_receipt_sha256, name="F061 review_receipt_sha256")
        if type(self.review_locator) is not PrivateLocator:
            raise AdmissionPreflightError("F061 review locator is inexact")
        if not _revalidate_exact_dataclass(self.review_locator, PrivateLocator):
            raise AdmissionPreflightError(
                "F061 review locator fails exact revalidation"
            )
        payload = {
            "proposal_sha256": self.proposal_sha256,
            "accepted": self.accepted,
            "review_receipt_sha256": self.review_receipt_sha256,
            "review_locator": self.review_locator.to_dict(),
            "review_scope": PHYSIONET_RESOLVED_F061_REVIEW_SCOPE,
            "shared_policy_review_accepts_resolved_counts": False,
        }
        object.__setattr__(
            self,
            "binding_sha256",
            _digest(F061_REVIEW_BINDING_DOMAIN, payload),
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "proposal_sha256": self.proposal_sha256,
            "accepted": self.accepted,
            "review_receipt_sha256": self.review_receipt_sha256,
            "review_locator": self.review_locator.to_dict(),
            "review_scope": PHYSIONET_RESOLVED_F061_REVIEW_SCOPE,
            "shared_policy_review_accepts_resolved_counts": False,
            "binding_sha256": self.binding_sha256,
        }


@dataclass(frozen=True)
class F061Allocation:
    review_state: str
    patient_count: Optional[int]
    numerators: Optional[Tuple[int, int, int]]
    denominator: Optional[int]
    counts: Optional[Tuple[int, int, int]]
    minimum_counts: Optional[Tuple[int, int, int]]
    rounding_rule_id: Optional[str]
    external_review_binding: Optional[F061ExternalReviewBinding]
    shared_policy_allocation_id: Optional[str] = None
    shared_policy_values: Optional[Tuple[int, int, int]] = None
    shared_policy_denominator: Optional[int] = None
    shared_policy_minimum_counts: Optional[Tuple[int, int, int]] = None
    shared_policy_rounding_rule_id: Optional[str] = None
    shared_policy_power_requirement_id: Optional[str] = None
    shared_policy_proposal_sha256: Optional[str] = None
    shared_policy_review_receipt_sha256: Optional[str] = None
    shared_policy_review_accepted: Optional[bool] = None
    shared_policy_definition_sha256: Optional[str] = None
    physionet_adapter_id: Optional[str] = None
    physionet_adapter_sha256: Optional[str] = None
    proposal_sha256: Optional[str] = field(init=False)

    def __post_init__(self) -> None:
        states = (
            "UNRESOLVED",
            "SYNTHETIC_QUALIFICATION_ONLY",
            "POWER_REVIEWED",
        )
        if type(self.review_state) is not str or self.review_state not in states:
            raise AdmissionPreflightError("F061 review_state is not frozen")
        if self.review_state == "UNRESOLVED":
            if any(
                value is not None
                for value in (
                    self.patient_count,
                    self.numerators,
                    self.denominator,
                    self.counts,
                    self.minimum_counts,
                    self.rounding_rule_id,
                    self.shared_policy_allocation_id,
                    self.shared_policy_values,
                    self.shared_policy_denominator,
                    self.shared_policy_minimum_counts,
                    self.shared_policy_rounding_rule_id,
                    self.shared_policy_power_requirement_id,
                    self.shared_policy_proposal_sha256,
                    self.shared_policy_review_receipt_sha256,
                    self.shared_policy_review_accepted,
                    self.shared_policy_definition_sha256,
                    self.physionet_adapter_id,
                    self.physionet_adapter_sha256,
                    self.external_review_binding,
                )
            ):
                raise AdmissionPreflightError("unresolved F061 must remain all-null")
            object.__setattr__(self, "proposal_sha256", None)
            return
        count = _exact_int(self.patient_count, name="F061 patient_count", minimum=1)
        if type(self.numerators) is not tuple or len(self.numerators) != 3:
            raise AdmissionPreflightError("F061 numerators must be an exact triple")
        numerators = tuple(
            _exact_int(value, name=f"F061 {name} numerator", minimum=1)
            for name, value in zip(SPLIT_NAMES, self.numerators)
        )
        denominator = _exact_int(
            self.denominator,
            name="F061 denominator",
            minimum=1,
        )
        if sum(numerators) != denominator:
            raise AdmissionPreflightError(
                "F061 positive numerators must sum exactly to the denominator"
            )
        if type(self.counts) is not tuple or len(self.counts) != 3:
            raise AdmissionPreflightError("F061 counts must be an exact triple")
        counts = tuple(
            _exact_int(value, name=f"F061 {name} count", minimum=1)
            for name, value in zip(SPLIT_NAMES, self.counts)
        )
        if type(self.minimum_counts) is not tuple or len(self.minimum_counts) != 3:
            raise AdmissionPreflightError(
                "F061 minimum_counts must be an exact triple"
            )
        minimum_counts = tuple(
            _exact_int(value, name=f"F061 {name} minimum", minimum=1)
            for name, value in zip(SPLIT_NAMES, self.minimum_counts)
        )
        if (
            type(self.rounding_rule_id) is not str
            or self.rounding_rule_id != F061_ROUNDING_RULE_ID
        ):
            raise AdmissionPreflightError("F061 rounding-rule identity drift")
        if sum(counts) != count:
            raise AdmissionPreflightError("F061 counts do not exhaust patients")
        expected = _hamilton_counts(count, numerators, denominator)
        if counts != expected:
            raise AdmissionPreflightError(
                "F061 counts do not match its explicit Hamilton proportions"
            )
        if any(value < minimum for value, minimum in zip(counts, minimum_counts)):
            raise AdmissionPreflightError(
                "F061 allocation is underpowered against reviewed minimum_counts"
            )
        proposal_digest = f061_allocation_proposal_sha256(
            patient_count=count,
            numerators=numerators,
            denominator=denominator,
            counts=counts,
            minimum_counts=minimum_counts,
            rounding_rule_id=self.rounding_rule_id,
            shared_policy_allocation_id=self.shared_policy_allocation_id,
            shared_policy_values=self.shared_policy_values,
            shared_policy_denominator=self.shared_policy_denominator,
            shared_policy_minimum_counts=self.shared_policy_minimum_counts,
            shared_policy_rounding_rule_id=(
                self.shared_policy_rounding_rule_id
            ),
            shared_policy_power_requirement_id=(
                self.shared_policy_power_requirement_id
            ),
            shared_policy_proposal_sha256=(
                self.shared_policy_proposal_sha256
            ),
            shared_policy_review_receipt_sha256=(
                self.shared_policy_review_receipt_sha256
            ),
            shared_policy_review_accepted=self.shared_policy_review_accepted,
            shared_policy_definition_sha256=(
                self.shared_policy_definition_sha256
            ),
            physionet_adapter_id=self.physionet_adapter_id,
            physionet_adapter_sha256=self.physionet_adapter_sha256,
        )
        object.__setattr__(self, "proposal_sha256", proposal_digest)
        if self.review_state == "SYNTHETIC_QUALIFICATION_ONLY":
            if any(
                value is not None
                for value in (
                    self.shared_policy_proposal_sha256,
                    self.shared_policy_allocation_id,
                    self.shared_policy_values,
                    self.shared_policy_denominator,
                    self.shared_policy_minimum_counts,
                    self.shared_policy_rounding_rule_id,
                    self.shared_policy_power_requirement_id,
                    self.shared_policy_review_receipt_sha256,
                    self.shared_policy_review_accepted,
                    self.shared_policy_definition_sha256,
                    self.physionet_adapter_id,
                    self.physionet_adapter_sha256,
                )
            ):
                raise AdmissionPreflightError(
                    "synthetic F061 must not claim accepted shared-policy provenance"
                )
            if self.external_review_binding is not None:
                raise AdmissionPreflightError(
                    "synthetic F061 allocation must not carry an external review"
                )
            if (
                numerators != CANDIDATE_ALLOCATION_NUMERATORS
                or denominator != CANDIDATE_ALLOCATION_DENOMINATOR
                or minimum_counts != CANDIDATE_MINIMUM_COUNTS
                or count < CANDIDATE_MINIMUM_PATIENT_COUNT
            ):
                raise AdmissionPreflightError(
                    "synthetic F061 is limited to the accepted 70/15/15 candidate"
                )
        if self.review_state == "POWER_REVIEWED":
            if any(
                value is None
                for value in (
                    self.shared_policy_proposal_sha256,
                    self.shared_policy_allocation_id,
                    self.shared_policy_values,
                    self.shared_policy_denominator,
                    self.shared_policy_minimum_counts,
                    self.shared_policy_rounding_rule_id,
                    self.shared_policy_power_requirement_id,
                    self.shared_policy_review_receipt_sha256,
                    self.shared_policy_review_accepted,
                    self.shared_policy_definition_sha256,
                    self.physionet_adapter_id,
                    self.physionet_adapter_sha256,
                )
            ):
                raise AdmissionPreflightError(
                    "power-reviewed F061 requires complete shared-policy provenance"
                )
            if type(self.external_review_binding) is not F061ExternalReviewBinding:
                raise AdmissionPreflightError(
                    "power-reviewed F061 requires an exact external review binding"
                )
            if not _revalidate_exact_dataclass(
                self.external_review_binding,
                F061ExternalReviewBinding,
            ):
                raise AdmissionPreflightError(
                    "F061 external review binding fails exact revalidation"
                )
            if self.external_review_binding.proposal_sha256 != proposal_digest:
                raise AdmissionPreflightError(
                    "F061 external review does not bind the exact proposal digest"
                )
            if self.external_review_binding.review_receipt_sha256 == (
                self.shared_policy_review_receipt_sha256
            ):
                raise AdmissionPreflightError(
                    "shared-policy and resolved-count reviews must be distinct"
                )

    def validate_for_patient_count(self, patient_count: object, activation: object) -> None:
        if self.review_state == "UNRESOLVED":
            raise AdmissionPreflightError("F061 allocation is unresolved")
        if type(activation) is not ActivationReceipt:
            raise AdmissionPreflightError("F061 validation requires exact activation")
        count = _exact_int(patient_count, name="patient_count", minimum=1)
        if count != self.patient_count:
            raise AdmissionPreflightError(
                "F061 patient_count differs from the supplied snapshot"
            )
        if activation.state == SYNTHETIC_STATE:
            if self.review_state != "SYNTHETIC_QUALIFICATION_ONLY":
                raise AdmissionPreflightError(
                    "synthetic split requires synthetic F061 qualification values"
                )
        elif self.review_state != "POWER_REVIEWED":
            raise AdmissionPreflightError(
                "activated real split requires power-reviewed F061 values"
            )

    @property
    def power_reviewed(self) -> bool:
        return (
            self.review_state == "POWER_REVIEWED"
            and type(self.external_review_binding) is F061ExternalReviewBinding
            and self.external_review_binding.accepted is True
            and self.external_review_binding.proposal_sha256
            == self.proposal_sha256
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "review_state": self.review_state,
            "patient_count": self.patient_count,
            "numerators": None if self.numerators is None else list(self.numerators),
            "denominator": self.denominator,
            "counts": None if self.counts is None else list(self.counts),
            "minimum_counts": (
                None if self.minimum_counts is None else list(self.minimum_counts)
            ),
            "rounding_rule_id": self.rounding_rule_id,
            "shared_policy_schema": SHARED_F061_POLICY_SCHEMA,
            "shared_policy_allocation_id": self.shared_policy_allocation_id,
            "shared_policy_mode": (
                None
                if self.shared_policy_allocation_id is None
                else SHARED_F061_POLICY_MODE
            ),
            "shared_policy_values": (
                None
                if self.shared_policy_values is None
                else list(self.shared_policy_values)
            ),
            "shared_policy_denominator": self.shared_policy_denominator,
            "shared_policy_minimum_counts": (
                None
                if self.shared_policy_minimum_counts is None
                else list(self.shared_policy_minimum_counts)
            ),
            "shared_policy_rounding_rule_id": (
                self.shared_policy_rounding_rule_id
            ),
            "shared_policy_power_requirement_id": (
                self.shared_policy_power_requirement_id
            ),
            "shared_policy_proposal_sha256": (
                self.shared_policy_proposal_sha256
            ),
            "shared_policy_review_receipt_sha256": (
                self.shared_policy_review_receipt_sha256
            ),
            "shared_policy_review_accepted": self.shared_policy_review_accepted,
            "shared_policy_definition_sha256": (
                self.shared_policy_definition_sha256
            ),
            "physionet_adapter_id": self.physionet_adapter_id,
            "physionet_adapter_sha256": self.physionet_adapter_sha256,
            "resolved_count_review_scope": PHYSIONET_RESOLVED_F061_REVIEW_SCOPE,
            "proposal_sha256": self.proposal_sha256,
            "external_review_binding": (
                None
                if self.external_review_binding is None
                else self.external_review_binding.to_dict()
            ),
        }


def _hamilton_counts(
    patient_count: int,
    numerators: Tuple[int, int, int],
    denominator: int,
) -> Tuple[int, int, int]:
    count = _exact_int(patient_count, name="patient_count", minimum=1)
    floors = [count * numerator // denominator for numerator in numerators]
    remainders = [count * numerator % denominator for numerator in numerators]
    remaining = count - sum(floors)
    priority = sorted(range(3), key=lambda index: (-remainders[index], index))
    for index in priority[:remaining]:
        floors[index] += 1
    return tuple(floors)  # type: ignore[return-value]


def make_f061_allocation(
    *,
    patient_count: object,
    review_state: object,
    numerators: object,
    denominator: object,
    counts: object,
    minimum_counts: object,
    external_review_binding: object,
    shared_policy_allocation_id: object = None,
    shared_policy_values: object = None,
    shared_policy_denominator: object = None,
    shared_policy_minimum_counts: object = None,
    shared_policy_rounding_rule_id: object = None,
    shared_policy_power_requirement_id: object = None,
    shared_policy_proposal_sha256: object = None,
    shared_policy_review_receipt_sha256: object = None,
    shared_policy_review_accepted: object = None,
    shared_policy_definition_sha256: object = None,
    physionet_adapter_id: object = None,
    physionet_adapter_sha256: object = None,
) -> F061Allocation:
    if type(review_state) is not str:
        raise AdmissionPreflightError("review_state must be an exact string")
    return F061Allocation(
        review_state=review_state,
        patient_count=patient_count,  # type: ignore[arg-type]
        numerators=numerators,  # type: ignore[arg-type]
        denominator=denominator,  # type: ignore[arg-type]
        counts=counts,  # type: ignore[arg-type]
        minimum_counts=minimum_counts,  # type: ignore[arg-type]
        rounding_rule_id=F061_ROUNDING_RULE_ID,
        shared_policy_allocation_id=(
            shared_policy_allocation_id  # type: ignore[arg-type]
        ),
        shared_policy_values=shared_policy_values,  # type: ignore[arg-type]
        shared_policy_denominator=(
            shared_policy_denominator  # type: ignore[arg-type]
        ),
        shared_policy_minimum_counts=(
            shared_policy_minimum_counts  # type: ignore[arg-type]
        ),
        shared_policy_rounding_rule_id=(
            shared_policy_rounding_rule_id  # type: ignore[arg-type]
        ),
        shared_policy_power_requirement_id=(
            shared_policy_power_requirement_id  # type: ignore[arg-type]
        ),
        shared_policy_proposal_sha256=(
            shared_policy_proposal_sha256  # type: ignore[arg-type]
        ),
        shared_policy_review_receipt_sha256=(
            shared_policy_review_receipt_sha256  # type: ignore[arg-type]
        ),
        shared_policy_review_accepted=(
            shared_policy_review_accepted  # type: ignore[arg-type]
        ),
        shared_policy_definition_sha256=(
            shared_policy_definition_sha256  # type: ignore[arg-type]
        ),
        physionet_adapter_id=physionet_adapter_id,  # type: ignore[arg-type]
        physionet_adapter_sha256=(
            physionet_adapter_sha256  # type: ignore[arg-type]
        ),
        external_review_binding=external_review_binding,  # type: ignore[arg-type]
    )


def make_synthetic_candidate_f061_allocation(
    *, patient_count: object
) -> F061Allocation:
    """Instantiate only the accepted, non-power-justified 70/15/15 candidate."""

    count = _exact_int(
        patient_count,
        name="synthetic candidate patient_count",
        minimum=CANDIDATE_MINIMUM_PATIENT_COUNT,
    )
    return make_f061_allocation(
        patient_count=count,
        review_state="SYNTHETIC_QUALIFICATION_ONLY",
        numerators=CANDIDATE_ALLOCATION_NUMERATORS,
        denominator=CANDIDATE_ALLOCATION_DENOMINATOR,
        counts=_hamilton_counts(
            count,
            CANDIDATE_ALLOCATION_NUMERATORS,
            CANDIDATE_ALLOCATION_DENOMINATOR,
        ),
        minimum_counts=CANDIDATE_MINIMUM_COUNTS,
        external_review_binding=None,
    )


@dataclass(frozen=True)
class PatientAssignment:
    patient_id: str
    order_sha256: str
    split: str

    def __post_init__(self) -> None:
        if (
            type(self.patient_id) is not str
            or _PATIENT_ID_RE.fullmatch(self.patient_id) is None
        ):
            raise AdmissionPreflightError("assignment patient_id is invalid")
        _sha256(self.order_sha256, name="patient order_sha256")
        if type(self.split) is not str or self.split not in SPLIT_NAMES:
            raise AdmissionPreflightError("assignment split is not frozen")

    def to_dict(self) -> Dict[str, str]:
        return {
            "patient_id": self.patient_id,
            "order_sha256": self.order_sha256,
            "split": self.split,
        }


@dataclass(frozen=True)
class RecordAssignment:
    record_ordinal: int
    patient_id: str
    split: str

    def __post_init__(self) -> None:
        _exact_int(self.record_ordinal, name="assignment record_ordinal")
        if (
            type(self.patient_id) is not str
            or _PATIENT_ID_RE.fullmatch(self.patient_id) is None
        ):
            raise AdmissionPreflightError("record assignment patient_id is invalid")
        if type(self.split) is not str or self.split not in SPLIT_NAMES:
            raise AdmissionPreflightError("record assignment split is not frozen")

    def to_dict(self) -> Dict[str, object]:
        return {
            "record_ordinal": self.record_ordinal,
            "patient_id": self.patient_id,
            "split": self.split,
        }


def _patient_order_digest(patient_id: str) -> bytes:
    _validate_split_implementation_identity()
    patient_bytes = patient_id.encode(PATIENT_ORDER_PATIENT_ENCODING)
    return hashlib.sha256(
        PATIENT_ORDER_DOMAIN
        + len(patient_bytes).to_bytes(
            PATIENT_ORDER_LENGTH_PREFIX_BYTES,
            byteorder=PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER,
            signed=PATIENT_ORDER_LENGTH_PREFIX_SIGNED,
        )
        + patient_bytes
    ).digest()


@dataclass(frozen=True)
class PatientSplitReceipt:
    activation: ActivationReceipt
    snapshot_receipt_sha256: str
    normalized_projection_sha256: str
    allocation: F061Allocation
    split_locator: PrivateLocator
    split_verification_receipt_sha256: Optional[str]
    patient_assignments: Tuple[PatientAssignment, ...]
    record_assignments: Tuple[RecordAssignment, ...]
    patient_counts: Tuple[int, int, int]
    record_counts: Tuple[int, int, int]
    exclusion_count: int = 0
    retry_count: int = 0
    resplit_count: int = 0
    top_up_count: int = 0
    split_manifest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("split receipt activation is inexact")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "split receipt activation fails exact revalidation"
            )
        _sha256(self.snapshot_receipt_sha256, name="snapshot_receipt_sha256")
        _sha256(
            self.normalized_projection_sha256,
            name="split normalized_projection_sha256",
        )
        if type(self.allocation) is not F061Allocation:
            raise AdmissionPreflightError("split allocation is inexact")
        if not _revalidate_exact_dataclass(self.allocation, F061Allocation):
            raise AdmissionPreflightError(
                "split allocation fails exact revalidation"
            )
        if type(self.split_locator) is not PrivateLocator:
            raise AdmissionPreflightError("split locator is inexact")
        if not _revalidate_exact_dataclass(self.split_locator, PrivateLocator):
            raise AdmissionPreflightError("split locator fails exact revalidation")
        verification = _optional_sha256(
            self.split_verification_receipt_sha256,
            name="split_verification_receipt_sha256",
        )
        if self.activation.state == SYNTHETIC_STATE and verification is not None:
            raise AdmissionPreflightError(
                "synthetic split must not carry external verification"
            )
        if self.activation.state == ACTIVATED_REAL_STATE and verification is None:
            raise AdmissionPreflightError(
                "activated real split requires independent verification"
            )
        if type(self.patient_assignments) is not tuple or any(
            type(row) is not PatientAssignment for row in self.patient_assignments
        ):
            raise AdmissionPreflightError("patient assignments are inexact")
        if any(
            not _revalidate_exact_dataclass(row, PatientAssignment)
            for row in self.patient_assignments
        ):
            raise AdmissionPreflightError(
                "patient assignment fails exact revalidation"
            )
        if type(self.record_assignments) is not tuple or any(
            type(row) is not RecordAssignment for row in self.record_assignments
        ):
            raise AdmissionPreflightError("record assignments are inexact")
        if any(
            not _revalidate_exact_dataclass(row, RecordAssignment)
            for row in self.record_assignments
        ):
            raise AdmissionPreflightError(
                "record assignment fails exact revalidation"
            )
        if type(self.patient_counts) is not tuple or len(self.patient_counts) != 3:
            raise AdmissionPreflightError("patient_counts must be an exact triple")
        if type(self.record_counts) is not tuple or len(self.record_counts) != 3:
            raise AdmissionPreflightError("record_counts must be an exact triple")
        for name, values in (
            ("patient_counts", self.patient_counts),
            ("record_counts", self.record_counts),
        ):
            for value in values:
                _exact_int(value, name=name)
        for name in ("exclusion_count", "retry_count", "resplit_count", "top_up_count"):
            value = _exact_int(getattr(self, name), name=name)
            if value != 0:
                raise AdmissionPreflightError(
                    "split exclusion, retry, resplit, and top-up counts must be zero"
                )
        if tuple(self.patient_counts) != self.allocation.counts:
            raise AdmissionPreflightError("split patient counts differ from F061")
        if sum(self.patient_counts) != len(self.patient_assignments):
            raise AdmissionPreflightError("split patient count is inconsistent")
        if sum(self.record_counts) != len(self.record_assignments):
            raise AdmissionPreflightError("split record count is inconsistent")
        self.allocation.validate_for_patient_count(
            len(self.patient_assignments), self.activation
        )
        patient_ids = tuple(row.patient_id for row in self.patient_assignments)
        if len(set(patient_ids)) != len(patient_ids):
            raise AdmissionPreflightError("split patient assignments are not unique")
        if patient_ids != tuple(sorted(patient_ids, key=lambda value: value.encode("ascii"))):
            raise AdmissionPreflightError(
                "split patient assignments are not in canonical patient-byte order"
            )
        assert self.allocation.counts is not None
        ordered = sorted(
            patient_ids,
            key=lambda value: (_patient_order_digest(value), value.encode("ascii")),
        )
        expected_split_by_patient: Dict[str, str] = {}
        cursor = 0
        for split, count in zip(SPLIT_NAMES, self.allocation.counts):
            for patient_id in ordered[cursor : cursor + count]:
                expected_split_by_patient[patient_id] = split
            cursor += count
        for row in self.patient_assignments:
            if row.order_sha256 != _patient_order_digest(row.patient_id).hex():
                raise AdmissionPreflightError("patient ordering digest is inconsistent")
            if row.split != expected_split_by_patient.get(row.patient_id):
                raise AdmissionPreflightError(
                    "patient assignment differs from deterministic F061 allocation"
                )
        record_ordinals = tuple(row.record_ordinal for row in self.record_assignments)
        if record_ordinals != tuple(range(len(self.record_assignments))):
            raise AdmissionPreflightError(
                "record assignments must be ordered exactly 0..R-1"
            )
        assigned_patients = set(patient_ids)
        seen_record_patients = set()
        for row in self.record_assignments:
            if row.patient_id not in assigned_patients:
                raise AdmissionPreflightError(
                    "record assignment refers to an unassigned patient"
                )
            if row.split != expected_split_by_patient[row.patient_id]:
                raise AdmissionPreflightError(
                    "record assignment crosses its patient's split"
                )
            seen_record_patients.add(row.patient_id)
        if seen_record_patients != assigned_patients:
            raise AdmissionPreflightError(
                "every assigned patient must have at least one preserved record"
            )
        derived_patient_counts = tuple(
            sum(row.split == split for row in self.patient_assignments)
            for split in SPLIT_NAMES
        )
        derived_record_counts = tuple(
            sum(row.split == split for row in self.record_assignments)
            for split in SPLIT_NAMES
        )
        if derived_patient_counts != self.patient_counts:
            raise AdmissionPreflightError("declared patient split counts are false")
        if derived_record_counts != self.record_counts:
            raise AdmissionPreflightError("declared record split counts are false")
        payload = self._payload()
        object.__setattr__(
            self,
            "split_manifest_sha256",
            _digest(SPLIT_RECEIPT_DOMAIN, payload),
        )

    @property
    def structurally_complete_for_real_instance(self) -> bool:
        return (
            self.activation.real_instance_structurally_enabled
            and self.allocation.power_reviewed
            and self.split_verification_receipt_sha256 is not None
        )

    def _payload(self) -> Dict[str, object]:
        return {
            "activation_id": self.activation.activation_id,
            "receipt_state": self.activation.state,
            "domain_id": DOMAIN_ID,
            "slot_id": SLOT_ID,
            "snapshot_receipt_sha256": self.snapshot_receipt_sha256,
            "normalized_projection_sha256": self.normalized_projection_sha256,
            "split_algorithm_id": SPLIT_ALGORITHM_ID,
            "split_contract_sha256": SPLIT_CONTRACT_SHA256,
            "allocation": self.allocation.to_dict(),
            "split_locator": self.split_locator.to_dict(),
            "split_verification_receipt_sha256": (
                self.split_verification_receipt_sha256
            ),
            "patient_assignments": [row.to_dict() for row in self.patient_assignments],
            "record_assignments": [row.to_dict() for row in self.record_assignments],
            "patient_counts": dict(zip(SPLIT_NAMES, self.patient_counts)),
            "record_counts": dict(zip(SPLIT_NAMES, self.record_counts)),
            "exclusion_count": self.exclusion_count,
            "retry_count": self.retry_count,
            "resplit_count": self.resplit_count,
            "top_up_count": self.top_up_count,
            "private_patient_identifiers_present": True,
            "publication_safe": False,
        }

    def to_dict(self) -> Dict[str, object]:
        result = self._payload()
        result["split_manifest_sha256"] = self.split_manifest_sha256
        result["structurally_complete_for_real_instance"] = (
            self.structurally_complete_for_real_instance
        )
        return result


def build_patient_disjoint_split(
    *,
    snapshot: object,
    allocation: object,
    split_locator: object,
    split_verification_receipt_sha256: object = None,
) -> PatientSplitReceipt:
    """Build a deterministic in-memory split without opening or writing data."""

    if type(snapshot) is not SnapshotReceipt:
        raise AdmissionPreflightError("snapshot must be an exact SnapshotReceipt")
    if type(allocation) is not F061Allocation:
        raise AdmissionPreflightError("allocation must be an exact F061Allocation")
    if type(split_locator) is not PrivateLocator:
        raise AdmissionPreflightError("split_locator must be exact")
    if not _snapshot_graph_revalidates(snapshot):
        raise AdmissionPreflightError("snapshot graph fails exact revalidation")
    if not _revalidate_exact_dataclass(allocation, F061Allocation):
        raise AdmissionPreflightError("F061 allocation fails exact revalidation")
    if not _revalidate_exact_dataclass(split_locator, PrivateLocator):
        raise AdmissionPreflightError("split locator fails exact revalidation")
    projection = snapshot.patient_projection
    patient_ids = {row.patient_id for row in projection}
    allocation.validate_for_patient_count(len(patient_ids), snapshot.activation)
    assert allocation.counts is not None
    ordered = sorted(
        patient_ids,
        key=lambda value: (_patient_order_digest(value), value.encode("ascii")),
    )
    split_by_patient: Dict[str, str] = {}
    cursor = 0
    for split, count in zip(SPLIT_NAMES, allocation.counts):
        for patient_id in ordered[cursor : cursor + count]:
            split_by_patient[patient_id] = split
        cursor += count
    if cursor != len(ordered) or len(split_by_patient) != len(ordered):
        raise AdmissionPreflightError("internal patient assignment preservation failure")
    patient_assignments = tuple(
        PatientAssignment(
            patient_id=patient_id,
            order_sha256=_patient_order_digest(patient_id).hex(),
            split=split_by_patient[patient_id],
        )
        for patient_id in sorted(patient_ids, key=lambda value: value.encode("ascii"))
    )
    record_assignments = tuple(
        RecordAssignment(
            record_ordinal=row.record_ordinal,
            patient_id=row.patient_id,
            split=split_by_patient[row.patient_id],
        )
        for row in projection
    )
    patient_counts = tuple(
        sum(row.split == split for row in patient_assignments) for split in SPLIT_NAMES
    )
    record_counts = tuple(
        sum(row.split == split for row in record_assignments) for split in SPLIT_NAMES
    )
    if len({row.patient_id for row in patient_assignments}) != len(patient_ids):
        raise AdmissionPreflightError("patient assignments are not one-to-one")
    for patient_id in patient_ids:
        if len({row.split for row in record_assignments if row.patient_id == patient_id}) != 1:
            raise AdmissionPreflightError("patient disjointness failure")
    return PatientSplitReceipt(
        activation=snapshot.activation,
        snapshot_receipt_sha256=snapshot.snapshot_receipt_sha256,
        normalized_projection_sha256=snapshot.normalized_projection_sha256,
        allocation=allocation,
        split_locator=split_locator,
        split_verification_receipt_sha256=(
            split_verification_receipt_sha256  # type: ignore[arg-type]
        ),
        patient_assignments=patient_assignments,
        record_assignments=record_assignments,
        patient_counts=patient_counts,  # type: ignore[arg-type]
        record_counts=record_counts,  # type: ignore[arg-type]
    )


@dataclass(frozen=True)
class GovernanceReceipt:
    activation: ActivationReceipt
    determination_state: str
    governance_record_sha256: Optional[str]
    accountable_owner_acceptance_sha256: Optional[str]
    determination_locator: Optional[PrivateLocator]
    governance_receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("governance activation is inexact")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "governance activation fails exact revalidation"
            )
        states = ("UNRESOLVED", "APPROVED_FOR_FROZEN_PHYSIONET_RESEARCH_USE")
        if type(self.determination_state) is not str or self.determination_state not in states:
            raise AdmissionPreflightError("governance determination state is invalid")
        if self.determination_state == "UNRESOLVED":
            if any(
                value is not None
                for value in (
                    self.governance_record_sha256,
                    self.accountable_owner_acceptance_sha256,
                    self.determination_locator,
                )
            ):
                raise AdmissionPreflightError("unresolved governance must remain all-null")
        else:
            if not self.activation.real_instance_structurally_enabled:
                raise AdmissionPreflightError(
                    "synthetic activation cannot carry a governance approval"
                )
            _sha256(self.governance_record_sha256, name="governance_record_sha256")
            _sha256(
                self.accountable_owner_acceptance_sha256,
                name="accountable_owner_acceptance_sha256",
            )
            if type(self.determination_locator) is not PrivateLocator:
                raise AdmissionPreflightError(
                    "governance determination locator is required"
                )
            if not _revalidate_exact_dataclass(
                self.determination_locator,
                PrivateLocator,
            ):
                raise AdmissionPreflightError(
                    "governance determination locator fails exact revalidation"
                )
        payload = {
            "activation": self.activation.to_dict(),
            "determination_state": self.determination_state,
            "governance_record_sha256": self.governance_record_sha256,
            "accountable_owner_acceptance_sha256": (
                self.accountable_owner_acceptance_sha256
            ),
            "determination_locator": (
                None
                if self.determination_locator is None
                else self.determination_locator.to_dict()
            ),
        }
        object.__setattr__(
            self,
            "governance_receipt_sha256",
            _digest(GOVERNANCE_RECEIPT_DOMAIN, payload),
        )

    @property
    def approved(self) -> bool:
        return (
            self.activation.real_instance_structurally_enabled
            and self.determination_state
            == "APPROVED_FOR_FROZEN_PHYSIONET_RESEARCH_USE"
            and self.governance_record_sha256 is not None
            and self.accountable_owner_acceptance_sha256 is not None
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "activation": self.activation.to_dict(),
            "determination_state": self.determination_state,
            "governance_record_sha256": self.governance_record_sha256,
            "accountable_owner_acceptance_sha256": (
                self.accountable_owner_acceptance_sha256
            ),
            "determination_locator": (
                None
                if self.determination_locator is None
                else self.determination_locator.to_dict()
            ),
            "governance_receipt_sha256": self.governance_receipt_sha256,
        }


@dataclass(frozen=True)
class ObservationSupportReceipt:
    activation: ActivationReceipt
    f033_state: str
    f034_state: str
    clean_kernel_id: str
    common_support_route_id: str
    observation_reference_id: Optional[str]
    observation_reference_sha256: Optional[str]
    full_support_component_id: Optional[str]
    full_support_component_sha256: Optional[str]
    mixture_weight_numerator: Optional[int]
    mixture_weight_denominator: Optional[int]
    acquisition_justification_receipt_sha256: Optional[str]
    proof_certificate_sha256: Optional[str]
    implementation_certificate_sha256: Optional[str]
    independent_review_receipt_sha256: Optional[str]
    support_receipt_locator: Optional[PrivateLocator]
    clean_kernel_kept_separate: bool
    theorem_convenience_noise_added: bool
    support_receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("support activation is inexact")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "support activation fails exact revalidation"
            )
        if type(self.clean_kernel_id) is not str or self.clean_kernel_id != OBSERVATION_KERNEL_ID:
            raise AdmissionPreflightError("support clean-kernel identity drift")
        if (
            type(self.common_support_route_id) is not str
            or self.common_support_route_id != COMMON_SUPPORT_ROUTE_ID
        ):
            raise AdmissionPreflightError("common-support route identity drift")
        _exact_bool(self.clean_kernel_kept_separate, name="clean_kernel_kept_separate")
        _exact_bool(
            self.theorem_convenience_noise_added,
            name="theorem_convenience_noise_added",
        )
        if not self.clean_kernel_kept_separate:
            raise AdmissionPreflightError("clean kernel must remain separate")
        if self.theorem_convenience_noise_added:
            raise AdmissionPreflightError("theorem-convenience noise is forbidden")
        states = ("UNRESOLVED", "CERTIFIED")
        if (
            type(self.f033_state) is not str
            or type(self.f034_state) is not str
            or self.f033_state not in states
            or self.f034_state not in states
        ):
            raise AdmissionPreflightError("F033/F034 support state is invalid")
        if self.f033_state != self.f034_state:
            raise AdmissionPreflightError("F033 and F034 must resolve all-or-nothing")
        optional_values = (
            self.observation_reference_id,
            self.observation_reference_sha256,
            self.full_support_component_id,
            self.full_support_component_sha256,
            self.mixture_weight_numerator,
            self.mixture_weight_denominator,
            self.acquisition_justification_receipt_sha256,
            self.proof_certificate_sha256,
            self.implementation_certificate_sha256,
            self.independent_review_receipt_sha256,
            self.support_receipt_locator,
        )
        if self.f033_state == "UNRESOLVED":
            if any(value is not None for value in optional_values):
                raise AdmissionPreflightError(
                    "unresolved F033/F034 must not carry reference or proof values"
                )
        else:
            if not self.activation.real_instance_structurally_enabled:
                raise AdmissionPreflightError(
                    "synthetic activation cannot carry certified F033/F034 evidence"
                )
            _nonplaceholder_token(
                self.observation_reference_id,
                name="observation_reference_id",
            )
            _sha256(
                self.observation_reference_sha256,
                name="observation_reference_sha256",
            )
            _nonplaceholder_token(
                self.full_support_component_id,
                name="full_support_component_id",
            )
            _sha256(
                self.full_support_component_sha256,
                name="full_support_component_sha256",
            )
            numerator = _exact_int(
                self.mixture_weight_numerator,
                name="mixture_weight_numerator",
                minimum=1,
            )
            denominator = _exact_int(
                self.mixture_weight_denominator,
                name="mixture_weight_denominator",
                minimum=2,
            )
            if numerator >= denominator:
                raise AdmissionPreflightError(
                    "positive mixture weight must be strictly below one"
                )
            for name in (
                "acquisition_justification_receipt_sha256",
                "proof_certificate_sha256",
                "implementation_certificate_sha256",
                "independent_review_receipt_sha256",
            ):
                _sha256(getattr(self, name), name=name)
            if type(self.support_receipt_locator) is not PrivateLocator:
                raise AdmissionPreflightError(
                    "certified F033/F034 requires a private support-receipt locator"
                )
            if not _revalidate_exact_dataclass(
                self.support_receipt_locator,
                PrivateLocator,
            ):
                raise AdmissionPreflightError(
                    "support receipt locator fails exact revalidation"
                )
        payload = {
            "activation": self.activation.to_dict(),
            "f033_state": self.f033_state,
            "f034_state": self.f034_state,
            "clean_kernel_id": self.clean_kernel_id,
            "common_support_route_id": self.common_support_route_id,
            "observation_reference_id": self.observation_reference_id,
            "observation_reference_sha256": self.observation_reference_sha256,
            "full_support_component_id": self.full_support_component_id,
            "full_support_component_sha256": self.full_support_component_sha256,
            "mixture_weight_numerator": self.mixture_weight_numerator,
            "mixture_weight_denominator": self.mixture_weight_denominator,
            "acquisition_justification_receipt_sha256": (
                self.acquisition_justification_receipt_sha256
            ),
            "proof_certificate_sha256": self.proof_certificate_sha256,
            "implementation_certificate_sha256": (
                self.implementation_certificate_sha256
            ),
            "independent_review_receipt_sha256": (
                self.independent_review_receipt_sha256
            ),
            "support_receipt_locator": (
                None
                if self.support_receipt_locator is None
                else self.support_receipt_locator.to_dict()
            ),
            "clean_kernel_kept_separate": self.clean_kernel_kept_separate,
            "theorem_convenience_noise_added": self.theorem_convenience_noise_added,
        }
        object.__setattr__(
            self,
            "support_receipt_sha256",
            _digest(SUPPORT_RECEIPT_DOMAIN, payload),
        )

    @property
    def certified(self) -> bool:
        return self.f033_state == self.f034_state == "CERTIFIED"

    def to_dict(self) -> Dict[str, object]:
        return {
            "activation": self.activation.to_dict(),
            "f033_state": self.f033_state,
            "f034_state": self.f034_state,
            "clean_kernel_id": self.clean_kernel_id,
            "common_support_route_id": self.common_support_route_id,
            "observation_reference_id": self.observation_reference_id,
            "observation_reference_sha256": self.observation_reference_sha256,
            "full_support_component_id": self.full_support_component_id,
            "full_support_component_sha256": self.full_support_component_sha256,
            "mixture_weight_numerator": self.mixture_weight_numerator,
            "mixture_weight_denominator": self.mixture_weight_denominator,
            "acquisition_justification_receipt_sha256": (
                self.acquisition_justification_receipt_sha256
            ),
            "proof_certificate_sha256": self.proof_certificate_sha256,
            "implementation_certificate_sha256": (
                self.implementation_certificate_sha256
            ),
            "independent_review_receipt_sha256": (
                self.independent_review_receipt_sha256
            ),
            "support_receipt_locator": (
                None
                if self.support_receipt_locator is None
                else self.support_receipt_locator.to_dict()
            ),
            "clean_kernel_kept_separate": self.clean_kernel_kept_separate,
            "theorem_convenience_noise_added": self.theorem_convenience_noise_added,
            "support_receipt_sha256": self.support_receipt_sha256,
        }


def unresolved_observation_support(
    activation: object,
) -> ObservationSupportReceipt:
    if type(activation) is not ActivationReceipt:
        raise AdmissionPreflightError("support requires exact activation")
    return ObservationSupportReceipt(
        activation=activation,
        f033_state="UNRESOLVED",
        f034_state="UNRESOLVED",
        clean_kernel_id=OBSERVATION_KERNEL_ID,
        common_support_route_id=COMMON_SUPPORT_ROUTE_ID,
        observation_reference_id=None,
        observation_reference_sha256=None,
        full_support_component_id=None,
        full_support_component_sha256=None,
        mixture_weight_numerator=None,
        mixture_weight_denominator=None,
        acquisition_justification_receipt_sha256=None,
        proof_certificate_sha256=None,
        implementation_certificate_sha256=None,
        independent_review_receipt_sha256=None,
        support_receipt_locator=None,
        clean_kernel_kept_separate=True,
        theorem_convenience_noise_added=False,
    )


def _duplicate_assignment_manifest_sha256(
    split: PatientSplitReceipt,
) -> str:
    return _digest(
        DUPLICATE_AUDIT_ASSIGNMENT_MANIFEST_DOMAIN,
        {
            "split_manifest_sha256": split.split_manifest_sha256,
            "normalized_projection_sha256": split.normalized_projection_sha256,
            "patient_assignments": [
                row.to_dict() for row in split.patient_assignments
            ],
            "record_assignments": [
                row.to_dict() for row in split.record_assignments
            ],
            "patient_counts": dict(zip(SPLIT_NAMES, split.patient_counts)),
            "record_counts": dict(zip(SPLIT_NAMES, split.record_counts)),
        },
    )


def _eligible_cross_split_record_pair_count(
    record_counts: Tuple[int, int, int],
) -> int:
    train, validation, test = record_counts
    return train * validation + train * test + validation * test


@dataclass(frozen=True)
class DuplicateAuditReceipt:
    activation: ActivationReceipt
    snapshot_receipt_sha256: str
    split_manifest_sha256: str
    audited_normalized_projection_sha256: str
    audited_assignment_manifest_sha256: str
    audited_record_count: int
    audited_patient_count: int
    eligible_cross_split_record_pair_count: int
    checked_cross_split_record_pair_count: int
    audit_algorithm_id: str
    audit_implementation_sha256: str
    near_duplicate_rule_id: str
    exact_duplicate_cross_split_count: int
    near_duplicate_cross_split_count: int
    complete_roster_checked: bool
    outcome_or_label_content_inspected: bool
    completion_certificate_sha256: str
    audit_verification_receipt_sha256: Optional[str]
    audit_locator: PrivateLocator
    audit_input_manifest_sha256: str = field(init=False)
    completion_attestation_sha256: str = field(init=False)
    duplicate_audit_receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_duplicate_audit_implementation_identity()
        if type(self.activation) is not ActivationReceipt:
            raise AdmissionPreflightError("duplicate audit activation is inexact")
        if not _revalidate_exact_dataclass(self.activation, ActivationReceipt):
            raise AdmissionPreflightError(
                "duplicate audit activation fails exact revalidation"
            )
        for name in (
            "snapshot_receipt_sha256",
            "split_manifest_sha256",
            "audited_normalized_projection_sha256",
            "audited_assignment_manifest_sha256",
            "completion_certificate_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        if (
            type(self.audit_algorithm_id) is not str
            or self.audit_algorithm_id != DUPLICATE_AUDIT_ALGORITHM_ID
        ):
            raise AdmissionPreflightError("duplicate audit algorithm identity drift")
        if (
            type(self.audit_implementation_sha256) is not str
            or self.audit_implementation_sha256
            != DUPLICATE_AUDIT_IMPLEMENTATION_SHA256
        ):
            raise AdmissionPreflightError(
                "duplicate audit implementation identity drift"
            )
        if (
            type(self.near_duplicate_rule_id) is not str
            or self.near_duplicate_rule_id != DUPLICATE_NEAR_RULE_ID
        ):
            raise AdmissionPreflightError(
                "duplicate audit near-duplicate rule identity drift"
            )
        _exact_int(self.audited_record_count, name="audited_record_count", minimum=3)
        _exact_int(
            self.audited_patient_count,
            name="audited_patient_count",
            minimum=3,
        )
        eligible = _exact_int(
            self.eligible_cross_split_record_pair_count,
            name="eligible_cross_split_record_pair_count",
            minimum=1,
        )
        checked = _exact_int(
            self.checked_cross_split_record_pair_count,
            name="checked_cross_split_record_pair_count",
        )
        if checked > eligible:
            raise AdmissionPreflightError(
                "duplicate audit checked pair count exceeds eligible roster"
            )
        complete = _exact_bool(
            self.complete_roster_checked,
            name="complete_roster_checked",
        )
        if complete and checked != eligible:
            raise AdmissionPreflightError(
                "duplicate audit false completion attestation"
            )
        _exact_int(
            self.exact_duplicate_cross_split_count,
            name="exact_duplicate_cross_split_count",
        )
        _exact_int(
            self.near_duplicate_cross_split_count,
            name="near_duplicate_cross_split_count",
        )
        _exact_bool(
            self.outcome_or_label_content_inspected,
            name="outcome_or_label_content_inspected",
        )
        if self.outcome_or_label_content_inspected:
            raise AdmissionPreflightError(
                "method-blind duplicate audit must not inspect outcomes or labels"
            )
        verification = _optional_sha256(
            self.audit_verification_receipt_sha256,
            name="audit_verification_receipt_sha256",
        )
        if type(self.audit_locator) is not PrivateLocator:
            raise AdmissionPreflightError("duplicate audit locator is inexact")
        if not _revalidate_exact_dataclass(self.audit_locator, PrivateLocator):
            raise AdmissionPreflightError(
                "duplicate audit locator fails exact revalidation"
            )
        if self.activation.state == SYNTHETIC_STATE and verification is not None:
            raise AdmissionPreflightError(
                "synthetic duplicate audit must not carry external verification"
            )
        if self.activation.state == ACTIVATED_REAL_STATE and verification is None:
            raise AdmissionPreflightError(
                "activated duplicate audit requires independent verification"
            )
        audit_input = self._audit_input()
        object.__setattr__(
            self,
            "audit_input_manifest_sha256",
            _digest(DUPLICATE_AUDIT_INPUT_DOMAIN, audit_input),
        )
        completion = self._completion()
        object.__setattr__(
            self,
            "completion_attestation_sha256",
            _digest(DUPLICATE_AUDIT_COMPLETION_DOMAIN, completion),
        )
        object.__setattr__(
            self,
            "duplicate_audit_receipt_sha256",
            _digest(DUPLICATE_AUDIT_RECEIPT_DOMAIN, self._payload()),
        )

    def _audit_input(self) -> Dict[str, object]:
        return {
            "snapshot_receipt_sha256": self.snapshot_receipt_sha256,
            "split_manifest_sha256": self.split_manifest_sha256,
            "audit_algorithm_id": self.audit_algorithm_id,
            "audit_implementation_sha256": self.audit_implementation_sha256,
            "near_duplicate_rule_id": self.near_duplicate_rule_id,
            "audited_normalized_projection_sha256": (
                self.audited_normalized_projection_sha256
            ),
            "audited_assignment_manifest_sha256": (
                self.audited_assignment_manifest_sha256
            ),
            "audited_record_count": self.audited_record_count,
            "audited_patient_count": self.audited_patient_count,
            "eligible_cross_split_record_pair_count": (
                self.eligible_cross_split_record_pair_count
            ),
        }

    def _completion(self) -> Dict[str, object]:
        return {
            "audit_input_manifest_sha256": self.audit_input_manifest_sha256,
            "completion_certificate_sha256": self.completion_certificate_sha256,
            "checked_cross_split_record_pair_count": (
                self.checked_cross_split_record_pair_count
            ),
            "complete_roster_checked": self.complete_roster_checked,
            "exact_duplicate_cross_split_count": (
                self.exact_duplicate_cross_split_count
            ),
            "near_duplicate_cross_split_count": (
                self.near_duplicate_cross_split_count
            ),
            "outcome_or_label_content_inspected": (
                self.outcome_or_label_content_inspected
            ),
            "audit_verification_receipt_sha256": (
                self.audit_verification_receipt_sha256
            ),
        }

    def _payload(self) -> Dict[str, object]:
        return {
            "activation": self.activation.to_dict(),
            **self._audit_input(),
            "audit_input_manifest_sha256": self.audit_input_manifest_sha256,
            "completion_certificate_sha256": self.completion_certificate_sha256,
            "checked_cross_split_record_pair_count": (
                self.checked_cross_split_record_pair_count
            ),
            "complete_roster_checked": self.complete_roster_checked,
            "exact_duplicate_cross_split_count": (
                self.exact_duplicate_cross_split_count
            ),
            "near_duplicate_cross_split_count": (
                self.near_duplicate_cross_split_count
            ),
            "outcome_or_label_content_inspected": (
                self.outcome_or_label_content_inspected
            ),
            "audit_verification_receipt_sha256": (
                self.audit_verification_receipt_sha256
            ),
            "completion_attestation_sha256": (
                self.completion_attestation_sha256
            ),
            "audit_locator": self.audit_locator.to_dict(),
        }

    @classmethod
    def create(
        cls,
        *,
        activation: object,
        snapshot: object,
        split: object,
        checked_cross_split_record_pair_count: object,
        complete_roster_checked: object,
        exact_duplicate_cross_split_count: object,
        near_duplicate_cross_split_count: object,
        outcome_or_label_content_inspected: object,
        completion_certificate_sha256: object,
        audit_verification_receipt_sha256: object,
        audit_locator: object,
    ) -> "DuplicateAuditReceipt":
        if not _snapshot_graph_revalidates(snapshot):
            raise AdmissionPreflightError(
                "duplicate audit requires an exact snapshot graph"
            )
        if not _split_graph_revalidates(split):
            raise AdmissionPreflightError(
                "duplicate audit requires an exact split graph"
            )
        assert type(snapshot) is SnapshotReceipt
        assert type(split) is PatientSplitReceipt
        if activation != snapshot.activation or activation != split.activation:
            raise AdmissionPreflightError(
                "duplicate audit activation differs from snapshot or split"
            )
        if (
            split.snapshot_receipt_sha256 != snapshot.snapshot_receipt_sha256
            or split.normalized_projection_sha256
            != snapshot.normalized_projection_sha256
        ):
            raise AdmissionPreflightError(
                "duplicate audit split does not bind the exact snapshot"
            )
        return cls(
            activation=activation,
            snapshot_receipt_sha256=snapshot.snapshot_receipt_sha256,
            split_manifest_sha256=split.split_manifest_sha256,
            audited_normalized_projection_sha256=(
                split.normalized_projection_sha256
            ),
            audited_assignment_manifest_sha256=(
                _duplicate_assignment_manifest_sha256(split)
            ),
            audited_record_count=len(split.record_assignments),
            audited_patient_count=len(split.patient_assignments),
            eligible_cross_split_record_pair_count=(
                _eligible_cross_split_record_pair_count(split.record_counts)
            ),
            checked_cross_split_record_pair_count=(
                checked_cross_split_record_pair_count
            ),
            audit_algorithm_id=DUPLICATE_AUDIT_ALGORITHM_ID,
            audit_implementation_sha256=(
                DUPLICATE_AUDIT_IMPLEMENTATION_SHA256
            ),
            near_duplicate_rule_id=DUPLICATE_NEAR_RULE_ID,
            exact_duplicate_cross_split_count=(
                exact_duplicate_cross_split_count
            ),
            near_duplicate_cross_split_count=(
                near_duplicate_cross_split_count
            ),
            complete_roster_checked=complete_roster_checked,
            outcome_or_label_content_inspected=(
                outcome_or_label_content_inspected
            ),
            completion_certificate_sha256=completion_certificate_sha256,
            audit_verification_receipt_sha256=(
                audit_verification_receipt_sha256
            ),
            audit_locator=audit_locator,
        )

    @property
    def coverage_complete(self) -> bool:
        return (
            self.complete_roster_checked
            and self.checked_cross_split_record_pair_count
            == self.eligible_cross_split_record_pair_count
        )

    @property
    def verified(self) -> bool:
        return (
            self.activation.real_instance_structurally_enabled
            and self.coverage_complete
            and self.audit_verification_receipt_sha256 is not None
        )

    @property
    def passed(self) -> bool:
        return (
            self.verified
            and self.exact_duplicate_cross_split_count == 0
            and self.near_duplicate_cross_split_count == 0
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            **self._payload(),
            "duplicate_audit_receipt_sha256": (
                self.duplicate_audit_receipt_sha256
            ),
            "coverage_complete": self.coverage_complete,
        }


@dataclass(frozen=True)
class ViolationCountVector:
    values: Tuple[int, ...]
    evaluation_split: str = VIOLATION_EVALUATION_SPLIT

    def __post_init__(self) -> None:
        if (
            type(self.evaluation_split) is not str
            or self.evaluation_split != VIOLATION_EVALUATION_SPLIT
        ):
            raise AdmissionPreflightError(
                "admission violations must be evaluated on TRAIN only"
            )
        if type(self.values) is not tuple or len(self.values) != len(ADMISSION_COMPONENTS):
            raise AdmissionPreflightError("violation vector must have exactly 13 entries")
        for name, value in zip(ADMISSION_COMPONENTS, self.values):
            _exact_int(value, name=name)

    @classmethod
    def from_mapping(cls, value: object) -> "ViolationCountVector":
        if type(value) is not dict:
            raise AdmissionPreflightError(
                "violation mapping must have the exact ordered 13-component roster"
            )
        keys = tuple(value.keys())
        if (
            len(keys) != len(ADMISSION_COMPONENTS)
            or any(type(name) is not str for name in keys)
            or keys != ADMISSION_COMPONENTS
        ):
            raise AdmissionPreflightError(
                "violation mapping must have exact ordered built-in string keys"
            )
        return cls(tuple(value[name] for name in keys))

    @property
    def maximum(self) -> int:
        return max(self.values)

    @property
    def nonzero_components(self) -> Tuple[str, ...]:
        return tuple(
            name for name, value in zip(ADMISSION_COMPONENTS, self.values) if value
        )

    def to_dict(self) -> Dict[str, int]:
        return dict(zip(ADMISSION_COMPONENTS, self.values))


@dataclass(frozen=True)
class AdmissionPreflightDecision:
    activation_id: str
    statistic_id: str
    threshold_id: str
    snapshot_receipt_sha256: str
    split_manifest_sha256: str
    governance_receipt_sha256: str
    support_receipt_sha256: str
    duplicate_audit_receipt_sha256: str
    violation_counts: ViolationCountVector
    receipt_flags: Tuple[Tuple[str, bool], ...]
    duplicate_audit_findings: Tuple[int, int]
    decision: str
    domain_admitted: bool
    independent_admission_required: bool
    evidence_aggregate_sha256: str = field(init=False)
    record_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _exact_token(self.activation_id, name="decision activation_id")
        if (
            type(self.statistic_id) is not str
            or self.statistic_id != ADMISSION_STATISTIC_ID
        ):
            raise AdmissionPreflightError("admission statistic identity drift")
        if (
            type(self.threshold_id) is not str
            or self.threshold_id != ADMISSION_THRESHOLD_ID
        ):
            raise AdmissionPreflightError("admission threshold identity drift")
        evidence_digests = (
            ("snapshot_receipt_sha256", self.snapshot_receipt_sha256),
            ("split_manifest_sha256", self.split_manifest_sha256),
            ("governance_receipt_sha256", self.governance_receipt_sha256),
            ("support_receipt_sha256", self.support_receipt_sha256),
            (
                "duplicate_audit_receipt_sha256",
                self.duplicate_audit_receipt_sha256,
            ),
        )
        for name, value in evidence_digests:
            _sha256(value, name=name)
        if type(self.violation_counts) is not ViolationCountVector:
            raise AdmissionPreflightError("decision violation vector is inexact")
        if not _revalidate_exact_dataclass(
            self.violation_counts,
            ViolationCountVector,
        ):
            raise AdmissionPreflightError(
                "decision violation vector fails exact revalidation"
            )
        if type(self.receipt_flags) is not tuple:
            raise AdmissionPreflightError("receipt flags must be an exact tuple")
        if any(
            type(row) is not tuple or len(row) != 2
            for row in self.receipt_flags
        ):
            raise AdmissionPreflightError(
                "each receipt flag must be an exact name/Boolean pair"
            )
        if tuple(name for name, _ in self.receipt_flags) != REQUIRED_RECEIPT_FLAGS:
            raise AdmissionPreflightError("receipt flag roster differs from frozen order")
        for name, value in self.receipt_flags:
            _exact_string(name, name="receipt flag name")
            _exact_bool(value, name=f"receipt flag {name}")
        if (
            type(self.duplicate_audit_findings) is not tuple
            or len(self.duplicate_audit_findings) != 2
        ):
            raise AdmissionPreflightError("duplicate findings must be an exact pair")
        for value in self.duplicate_audit_findings:
            _exact_int(value, name="duplicate finding")
        if type(self.decision) is not str or self.decision not in (
            "NO_GO",
            "ELIGIBLE_FOR_INDEPENDENT_ADMISSION",
        ):
            raise AdmissionPreflightError("preflight decision is invalid")
        if self.domain_admitted is not False or self.independent_admission_required is not True:
            raise AdmissionPreflightError(
                "offline preflight must never claim final domain admission"
            )
        structurally_eligible = (
            self.violation_counts.maximum == 0
            and all(value for _, value in self.receipt_flags)
            and self.duplicate_audit_findings == (0, 0)
        )
        if (
            self.decision == "ELIGIBLE_FOR_INDEPENDENT_ADMISSION"
            and not structurally_eligible
        ):
            raise AdmissionPreflightError(
                "independent-admission eligibility contradicts supplied evidence"
            )
        evidence_payload = {
            "activation_id": self.activation_id,
            "snapshot_receipt_sha256": self.snapshot_receipt_sha256,
            "split_manifest_sha256": self.split_manifest_sha256,
            "governance_receipt_sha256": self.governance_receipt_sha256,
            "support_receipt_sha256": self.support_receipt_sha256,
            "duplicate_audit_receipt_sha256": (
                self.duplicate_audit_receipt_sha256
            ),
        }
        evidence_aggregate = _digest(
            ADMISSION_EVIDENCE_DOMAIN,
            evidence_payload,
        )
        object.__setattr__(
            self,
            "evidence_aggregate_sha256",
            evidence_aggregate,
        )
        payload = {
            "activation_id": self.activation_id,
            "statistic_id": self.statistic_id,
            "threshold_id": self.threshold_id,
            "evidence": evidence_payload,
            "evidence_aggregate_sha256": evidence_aggregate,
            "violation_evaluation_split": self.violation_counts.evaluation_split,
            "violation_counts": self.violation_counts.to_dict(),
            "receipt_flags": dict(self.receipt_flags),
            "duplicate_audit_findings": list(self.duplicate_audit_findings),
            "decision": self.decision,
            "domain_admitted": self.domain_admitted,
            "independent_admission_required": self.independent_admission_required,
        }
        object.__setattr__(
            self,
            "record_sha256",
            _digest(ADMISSION_RECEIPT_DOMAIN, payload),
        )

    def receipt_flag_mapping(self) -> Dict[str, bool]:
        return dict(self.receipt_flags)


def _snapshot_graph_revalidates(value: object) -> bool:
    if not _revalidate_exact_dataclass(value, SnapshotReceipt):
        return False
    assert type(value) is SnapshotReceipt
    return (
        _revalidate_exact_dataclass(value.activation, ActivationReceipt)
        and _revalidate_exact_dataclass(value.archive, RawArchiveReceipt)
        and _revalidate_exact_dataclass(value.archive.archive_locator, PrivateLocator)
        and all(
            _revalidate_exact_dataclass(row, AllowlistedFileReceipt)
            for row in value.allowlisted_files
        )
        and all(
            _revalidate_exact_dataclass(row, PatientRecord)
            for row in value.patient_projection
        )
        and _revalidate_exact_dataclass(value.toolchain, ToolchainIdentity)
        and _revalidate_exact_dataclass(value.snapshot_locator, PrivateLocator)
    )


def _split_graph_revalidates(value: object) -> bool:
    if not _revalidate_exact_dataclass(value, PatientSplitReceipt):
        return False
    assert type(value) is PatientSplitReceipt
    review = value.allocation.external_review_binding
    review_valid = review is None or (
        _revalidate_exact_dataclass(review, F061ExternalReviewBinding)
        and _revalidate_exact_dataclass(review.review_locator, PrivateLocator)
        and review.proposal_sha256 == value.allocation.proposal_sha256
        and review.accepted is True
    )
    return (
        _revalidate_exact_dataclass(value.activation, ActivationReceipt)
        and _revalidate_exact_dataclass(value.allocation, F061Allocation)
        and review_valid
        and _revalidate_exact_dataclass(value.split_locator, PrivateLocator)
        and all(
            _revalidate_exact_dataclass(row, PatientAssignment)
            for row in value.patient_assignments
        )
        and all(
            _revalidate_exact_dataclass(row, RecordAssignment)
            for row in value.record_assignments
        )
    )


def _admission_receipt_graphs_revalidate(
    *,
    snapshot: SnapshotReceipt,
    split: PatientSplitReceipt,
    governance: GovernanceReceipt,
    support: ObservationSupportReceipt,
    duplicate_audit: DuplicateAuditReceipt,
    violation_counts: ViolationCountVector,
) -> bool:
    governance_locator_valid = (
        governance.determination_locator is None
        or _revalidate_exact_dataclass(
            governance.determination_locator, PrivateLocator
        )
    )
    support_locator_valid = (
        support.support_receipt_locator is None
        or _revalidate_exact_dataclass(
            support.support_receipt_locator, PrivateLocator
        )
    )
    return (
        _snapshot_graph_revalidates(snapshot)
        and _split_graph_revalidates(split)
        and _revalidate_exact_dataclass(governance, GovernanceReceipt)
        and _revalidate_exact_dataclass(governance.activation, ActivationReceipt)
        and governance_locator_valid
        and _revalidate_exact_dataclass(support, ObservationSupportReceipt)
        and _revalidate_exact_dataclass(support.activation, ActivationReceipt)
        and support_locator_valid
        and _revalidate_exact_dataclass(duplicate_audit, DuplicateAuditReceipt)
        and _revalidate_exact_dataclass(
            duplicate_audit.activation, ActivationReceipt
        )
        and _revalidate_exact_dataclass(
            duplicate_audit.audit_locator, PrivateLocator
        )
        and _revalidate_exact_dataclass(violation_counts, ViolationCountVector)
    )


def evaluate_admission_preflight(
    *,
    snapshot: object,
    split: object,
    governance: object,
    support: object,
    duplicate_audit: object,
    violation_counts: object,
) -> AdmissionPreflightDecision:
    """Evaluate structural eligibility while always reserving final admission."""

    if type(snapshot) is not SnapshotReceipt:
        raise AdmissionPreflightError("snapshot receipt is inexact")
    if type(split) is not PatientSplitReceipt:
        raise AdmissionPreflightError("split receipt is inexact")
    if type(governance) is not GovernanceReceipt:
        raise AdmissionPreflightError("governance receipt is inexact")
    if type(support) is not ObservationSupportReceipt:
        raise AdmissionPreflightError("support receipt is inexact")
    if type(duplicate_audit) is not DuplicateAuditReceipt:
        raise AdmissionPreflightError("duplicate audit receipt is inexact")
    if type(violation_counts) is not ViolationCountVector:
        raise AdmissionPreflightError("violation vector is inexact")
    if not _admission_receipt_graphs_revalidate(
        snapshot=snapshot,
        split=split,
        governance=governance,
        support=support,
        duplicate_audit=duplicate_audit,
        violation_counts=violation_counts,
    ):
        raise AdmissionPreflightError(
            "one or more admission receipt graphs fail exact revalidation"
        )
    activation = snapshot.activation
    for name, receipt_activation in (
        ("split", split.activation),
        ("governance", governance.activation),
        ("support", support.activation),
        ("duplicate audit", duplicate_audit.activation),
    ):
        if receipt_activation != activation:
            raise AdmissionPreflightError(f"{name} activation differs from snapshot")
    if (
        split.snapshot_receipt_sha256 != snapshot.snapshot_receipt_sha256
        or split.normalized_projection_sha256
        != snapshot.normalized_projection_sha256
    ):
        raise AdmissionPreflightError("split does not bind the exact snapshot")
    expected_record_projection = tuple(
        (row.record_ordinal, row.patient_id) for row in snapshot.patient_projection
    )
    observed_record_projection = tuple(
        (row.record_ordinal, row.patient_id) for row in split.record_assignments
    )
    if observed_record_projection != expected_record_projection:
        raise AdmissionPreflightError(
            "split assignments do not preserve the exact snapshot projection"
        )
    if (
        duplicate_audit.snapshot_receipt_sha256
        != snapshot.snapshot_receipt_sha256
        or duplicate_audit.split_manifest_sha256 != split.split_manifest_sha256
    ):
        raise AdmissionPreflightError("duplicate audit does not bind snapshot and split")
    expected_eligible_pair_count = _eligible_cross_split_record_pair_count(
        split.record_counts
    )
    duplicate_audit_replay_valid = (
        duplicate_audit.audit_algorithm_id == DUPLICATE_AUDIT_ALGORITHM_ID
        and duplicate_audit.audit_implementation_sha256
        == DUPLICATE_AUDIT_IMPLEMENTATION_SHA256
        and duplicate_audit.near_duplicate_rule_id == DUPLICATE_NEAR_RULE_ID
        and duplicate_audit.audited_normalized_projection_sha256
        == split.normalized_projection_sha256
        and duplicate_audit.audited_assignment_manifest_sha256
        == _duplicate_assignment_manifest_sha256(split)
        and duplicate_audit.audited_record_count == len(split.record_assignments)
        and duplicate_audit.audited_patient_count == len(split.patient_assignments)
        and duplicate_audit.eligible_cross_split_record_pair_count
        == expected_eligible_pair_count
        and duplicate_audit.checked_cross_split_record_pair_count
        == expected_eligible_pair_count
        and duplicate_audit.complete_roster_checked
    )
    receipt_flags = (
        ("snapshot_hash_verified", snapshot.externally_verified),
        (
            "license_access_record_verified",
            snapshot.externally_verified
            and snapshot.archive.license_access_receipt_sha256 is not None,
        ),
        ("governance_approval_verified", governance.approved),
        (
            "complete_split_manifest_verified",
            split.structurally_complete_for_real_instance,
        ),
        (
            "duplicate_and_near_duplicate_audit_verified",
            duplicate_audit.verified and duplicate_audit_replay_valid,
        ),
        (
            "observation_reference_and_support_receipt_verified",
            support.certified and support.activation.real_instance_structurally_enabled,
        ),
    )
    duplicates_zero = (
        duplicate_audit.exact_duplicate_cross_split_count == 0
        and duplicate_audit.near_duplicate_cross_split_count == 0
    )
    eligible = (
        activation.real_instance_structurally_enabled
        and violation_counts.maximum == 0
        and all(value for _, value in receipt_flags)
        and duplicates_zero
        and split.exclusion_count
        == split.retry_count
        == split.resplit_count
        == split.top_up_count
        == 0
        and snapshot.post_snapshot_exclusion_count == 0
        and snapshot.retry_resplit_topup_count == 0
    )
    return AdmissionPreflightDecision(
        activation_id=activation.activation_id,
        statistic_id=ADMISSION_STATISTIC_ID,
        threshold_id=ADMISSION_THRESHOLD_ID,
        snapshot_receipt_sha256=snapshot.snapshot_receipt_sha256,
        split_manifest_sha256=split.split_manifest_sha256,
        governance_receipt_sha256=governance.governance_receipt_sha256,
        support_receipt_sha256=support.support_receipt_sha256,
        duplicate_audit_receipt_sha256=(
            duplicate_audit.duplicate_audit_receipt_sha256
        ),
        violation_counts=violation_counts,
        receipt_flags=receipt_flags,
        duplicate_audit_findings=(
            duplicate_audit.exact_duplicate_cross_split_count,
            duplicate_audit.near_duplicate_cross_split_count,
        ),
        decision=(
            "ELIGIBLE_FOR_INDEPENDENT_ADMISSION" if eligible else "NO_GO"
        ),
        domain_admitted=False,
        independent_admission_required=True,
    )


__all__ = [
    "ACTIVATED_REAL_STATE",
    "ADMISSION_COMPONENTS",
    "ADMISSION_STATISTIC_ID",
    "ADMISSION_THRESHOLD_ID",
    "AdmissionPreflightDecision",
    "AdmissionPreflightError",
    "ActivationReceipt",
    "AllowlistedFileReceipt",
    "CANDIDATE_ALLOCATION_DENOMINATOR",
    "CANDIDATE_ALLOCATION_NUMERATORS",
    "CANDIDATE_MINIMUM_COUNTS",
    "CANDIDATE_MINIMUM_PATIENT_COUNT",
    "CANDIDATE_SPLIT_ALGORITHM_ID",
    "COMMON_SUPPORT_ROUTE_ID",
    "DOMAIN_ID",
    "DUPLICATE_AUDIT_ALGORITHM_ID",
    "DUPLICATE_AUDIT_IMPLEMENTATION_DOMAIN",
    "DUPLICATE_AUDIT_IMPLEMENTATION_ID",
    "DUPLICATE_AUDIT_IMPLEMENTATION_SCHEMA_VERSION",
    "DUPLICATE_AUDIT_IMPLEMENTATION_SHA256",
    "DUPLICATE_NEAR_RULE_ID",
    "DuplicateAuditReceipt",
    "EXPLICIT_F061_SPLIT_CONTRACT_DOMAIN",
    "F061Allocation",
    "F061ExternalReviewBinding",
    "F061_ROUNDING_RULE_ID",
    "F105_TRANSFORM_ID",
    "F105_TRANSFORM_SOURCE_SHA256",
    "GovernanceReceipt",
    "HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256",
    "INVENTORY_ID",
    "INVENTORY_SOURCE_SHA256",
    "OBSERVATION_KERNEL_ID",
    "ObservationSupportReceipt",
    "PARSER_ID",
    "PARSER_SOURCE_SHA256",
    "PATIENT_ORDER_DOMAIN",
    "PATIENT_ORDER_DOMAIN_HEX",
    "PATIENT_ORDER_DOMAIN_SHA256",
    "PATIENT_ORDER_HASH_ALGORITHM",
    "PATIENT_ORDER_LENGTH_PREFIX_BYTEORDER",
    "PATIENT_ORDER_LENGTH_PREFIX_BYTES",
    "PATIENT_ORDER_LENGTH_PREFIX_SIGNED",
    "PATIENT_ORDER_PATIENT_ENCODING",
    "PATIENT_ORDER_PRIMARY_SORT",
    "PATIENT_ORDER_TIE_BREAK",
    "PHYSIONET_F061_ADAPTER_ID",
    "PHYSIONET_F061_ADAPTER_SHA256",
    "PHYSIONET_RESOLVED_F061_REVIEW_SCOPE",
    "PatientRecord",
    "PatientSplitReceipt",
    "PrivateLocator",
    "REQUIRED_RECEIPT_FLAGS",
    "RawArchiveReceipt",
    "SLOT_ID",
    "SHARED_F061_POLICY_MODE",
    "SHARED_F061_POLICY_SCHEMA",
    "SPLIT_ALGORITHM_ID",
    "SPLIT_CONTRACT_SHA256",
    "SPLIT_CONTRACT_SCHEMA_VERSION",
    "SPLIT_IMPLEMENTATION_DOMAIN",
    "SPLIT_IMPLEMENTATION_ID",
    "SPLIT_IMPLEMENTATION_SCHEMA_VERSION",
    "SPLIT_IMPLEMENTATION_SHA256",
    "SPLIT_NAMES",
    "SYNTHETIC_STATE",
    "SnapshotReceipt",
    "ToolchainIdentity",
    "ViolationCountVector",
    "VIOLATION_EVALUATION_SPLIT",
    "build_patient_disjoint_split",
    "duplicate_audit_implementation_record",
    "evaluate_admission_preflight",
    "explicit_f061_split_contract_record",
    "f061_allocation_proposal_sha256",
    "make_f061_allocation",
    "make_synthetic_candidate_f061_allocation",
    "normalized_projection_sha256",
    "physionet_f061_adapter_record",
    "physionet_f061_adapter_sha256",
    "shared_f061_policy_definition_sha256",
    "shared_f061_policy_proposal_sha256",
    "split_implementation_record",
    "synthetic_activation",
    "synthetic_digest",
    "unresolved_observation_support",
]
