"""Pure Online Retail II split and admission preflight contracts.

This module deliberately has no filesystem, network, subprocess, entropy,
workbook, or dataset access.  Every function consumes caller-supplied in-memory
values.  Receipt objects validate structure and crosslinks; they do not assert
that an external approval, proof, snapshot, or audit actually exists.

The effective Retail temporal rule uses source-civil microseconds and an
explicit F061 allocation.  The observation task retains its structural zeros.
No positive mixture, clutter, clipping, or theorem-convenience noise is
created here.  The only recognized future route is the already accepted
acquisition-justified positive dominated-mixture policy; this module does not
select or implement a structural-zero theorem extension.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import re
from dataclasses import dataclass, fields
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


DOMAIN_ID = "online-retail-ii"
SLOT_ID = "R4-RETAIL"
SPLITS = ("TRAIN", "VALIDATION", "TEST")
RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS = 63_849_600_000_000

F060_RULE_ID = (
    "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_"
    "SOURCE_CIVIL_F061_PARAMETERIZED_V2"
)
F060_ASSIGNMENT_SCHEMA = (
    "heterodiff-retail-f060-source-civil-f061-parameterized-assignment-v2"
)
LEGACY_MISBOUND_F105_SEMANTIC_SHA256 = (
    "14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52"
)
HISTORICAL_RETAIL_SPLIT_DESIGN_ID = (
    "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1"
)
HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256 = (
    "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b"
)
ACTIVE_RETAIL_SPLIT_CONTRACT_ID = (
    "RETAIL_F060_SOURCE_CIVIL_SHARED_F061_INTEGRATED_REPLAY_V3"
)
F061_ALLOCATION_SCHEMA = "heterodiff-f061-exact-allocation-definition-v1"
SHARED_F061_POLICY_SCHEMA = "heterodiff-two-domain-f061-shared-policy-v1"
INTEGRATED_F061_MODE = "EXACT_PROPORTIONS_HAMILTON"
SHARED_F061_HAMILTON_ROUNDING_RULE_ID = (
    "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
)
RETAIL_F061_ADAPTER_ID = "SHARED_POLICY_TO_RETAIL_F061_PROPOSAL_ADAPTER_V1"
RETAIL_F061_ADAPTER_SHA256 = (
    "c442a1a7ee95078d07852d600f7ea2c35ec52c309b6f97d9cbdba41374f878ee"
)
OBSERVATION_KERNEL_ID = "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"
COMMON_SUPPORT_POLICY_ID = (
    "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
    "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
)
DUPLICATE_AUDIT_ALGORITHM_ID = (
    "EXHAUSTIVE_CROSS_SPLIT_ROW_PAIR_EXACT_AND_RULE_BOUND_NEAR_DUPLICATE_V1"
)

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

REQUIRED_ADMISSION_RECEIPTS = (
    "snapshot_hash_verified",
    "license_access_record_verified",
    "governance_approval_verified",
    "complete_split_manifest_verified",
    "duplicate_and_near_duplicate_audit_verified",
    "observation_reference_and_support_receipt_verified",
)

RETAIL_RAW_FIELDS = (
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_CUSTOMER_RE = re.compile(r"[1-9][0-9]{0,4}\Z")
_SAFE_LOCATOR_PART_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
_SUPPORT_PLACEHOLDERS = frozenset(
    {"NONE", "NULL", "PENDING", "TBD", "TODO", "UNKNOWN", "UNRESOLVED"}
)

_ALLOCATION_PROPOSAL_DOMAIN = b"heterodiff/f061-allocation-proposal/v1\0"
_ALLOCATION_DEFINITION_DOMAIN = b"heterodiff/f061-allocation-definition/v1\0"
_ALLOCATION_RESOLUTION_DOMAIN = b"heterodiff/f061-allocation-resolution/v1\0"
_F060_INPUT_DOMAIN = b"heterodiff/retail-f060-source-civil-input/v2\0"
_F060_NORMALIZED_PROJECTION_DOMAIN = (
    b"heterodiff/retail-f060-source-civil-normalized-projection/v2\0"
)
_F060_ASSIGNMENT_DOMAIN = b"heterodiff/retail-f060-source-civil-assignment/v2\0"
_F060_ASSIGNMENT_VALIDATION_DOMAIN = (
    b"heterodiff/retail-f060-source-civil-assignment-validation/v2\0"
)
_SCHEMA_RECEIPT_DOMAIN = b"heterodiff/retail-schema-receipt/v1\0"
_GOVERNANCE_RECEIPT_DOMAIN = b"heterodiff/retail-governance-receipt/v1\0"
_SNAPSHOT_RECEIPT_DOMAIN = b"heterodiff/retail-snapshot-receipt/v1\0"
_SPLIT_RECEIPT_DOMAIN = b"heterodiff/retail-split-receipt/v1\0"
_SUPPORT_RECEIPT_DOMAIN = b"heterodiff/retail-support-receipt/v1\0"
_DUPLICATE_AUDIT_DOMAIN = b"heterodiff/retail-duplicate-audit/v1\0"
_DUPLICATE_AUDIT_INPUT_DOMAIN = b"heterodiff/retail-duplicate-audit-input/v1\0"
_DUPLICATE_AUDIT_COMPLETION_DOMAIN = (
    b"heterodiff/retail-duplicate-audit-completion/v1\0"
)
_ACTIVE_RETAIL_SPLIT_CONTRACT_DOMAIN = (
    b"heterodiff/retail-active-split-contract/v1\0"
)
_SHARED_F061_PROPOSAL_DOMAIN = (
    b"heterodiff/two-domain-f061-shared-policy-proposal/v1\0"
)
_SHARED_F061_DEFINITION_DOMAIN = (
    b"heterodiff/two-domain-f061-shared-policy-definition/v1\0"
)
_RETAIL_F061_ADAPTER_DOMAIN = (
    b"heterodiff/two-domain-f061-retail-adapter-contract/v1\0"
)


class RetailPreflightError(ValueError):
    """Fail-closed input, allocation, receipt, or crosslink error."""


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise RetailPreflightError("NONCANONICAL_VALUE") from error


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + _canonical_bytes(value)).hexdigest()


def retail_f061_adapter_record() -> Dict[str, Any]:
    """Return the exact shared-policy-to-Retail adapter contract."""

    return {
        "schema_version": "heterodiff-f061-adapter-contract-v1",
        "adapter_id": RETAIL_F061_ADAPTER_ID,
        "source_schema": SHARED_F061_POLICY_SCHEMA,
        "target_schema": F061_ALLOCATION_SCHEMA,
        "required_inputs": [
            "allocation_id",
            "mode",
            "values",
            "denominator",
            "minimum_counts",
            "power_requirement_id",
        ],
        "outputs": [
            "schema_version",
            "allocation_id",
            "mode",
            "values",
            "denominator",
            "minimum_counts",
            "power_requirement_id",
        ],
        "algorithm": "MAP_TUPLES_TO_TRAIN_VALIDATION_TEST_INTEGER_MAPPINGS_V1",
        "review_semantics": (
            "SHARED_POLICY_REVIEW_ONLY_NO_DOMAIN_RESOLUTION_REVIEW_V1"
        ),
    }


def retail_f061_adapter_sha256(record: object = None) -> str:
    """Recompute the domain-separated Retail adapter digest."""

    value = retail_f061_adapter_record() if record is None else record
    return _digest(_RETAIL_F061_ADAPTER_DOMAIN, value)


def active_retail_split_contract_record() -> Dict[str, Any]:
    """Return the canonical active integrated Retail split contract."""

    return {
        "schema_version": "heterodiff-retail-active-split-contract-v1",
        "contract_id": ACTIVE_RETAIL_SPLIT_CONTRACT_ID,
        "historical_provenance": {
            "design_id": HISTORICAL_RETAIL_SPLIT_DESIGN_ID,
            "design_raw_sha256": HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256,
            "legacy_misbound_f105_semantic_sha256": (
                LEGACY_MISBOUND_F105_SEMANTIC_SHA256
            ),
            "legacy_misbound_digest_is_split_contract": False,
        },
        "active_f060_successor": {
            "rule_id": F060_RULE_ID,
            "assignment_schema": F060_ASSIGNMENT_SCHEMA,
        },
        "domain_id": DOMAIN_ID,
        "slot_id": SLOT_ID,
        "normalized_input": {
            "container": "EXACT_NONEMPTY_BUILTIN_LIST_OF_EXACT_BUILTIN_DICTS",
            "keys": [
                "row_ordinal",
                "customer_key_hex",
                (
                    "timestamp_source_civil_microseconds_since_"
                    "2009_12_01"
                ),
            ],
            "ordinal_rule": "CONTIGUOUS_UNIQUE_ZERO_BASED_EXACT_INTEGERS",
            "customer_key_rule": (
                "LOWERCASE_HEX_OF_CANONICAL_POSITIVE_ASCII_DECIMAL_"
                "CUSTOMER_ID_MAX_5_DIGITS"
            ),
            "timestamp_semantics": (
                "EXACT_NONNEGATIVE_SOURCE_CIVIL_MICROSECONDS_SINCE_"
                "2009_12_01_NO_TIMEZONE_OR_INSTANT"
            ),
            "exclusive_horizon": RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS,
        },
        "natural_group": {
            "identity": "CANONICAL_CUSTOMER_ID_BYTES",
            "interval": "COMPLETE_CLOSED_MIN_MAX_SOURCE_CIVIL_TIMESTAMPS",
            "cross_split_grouping_forbidden": True,
        },
        "allocation": {
            "native_schema": F061_ALLOCATION_SCHEMA,
            "generic_splitter_modes": [
                "EXACT_COUNTS",
                INTEGRATED_F061_MODE,
            ],
            "integrated_admission_mode": INTEGRATED_F061_MODE,
            "hamilton_tie_order": list(SPLITS),
            "positive_values_and_minimum_counts_required": True,
            "power_review_binding_required": True,
            "shared_policy_schema": SHARED_F061_POLICY_SCHEMA,
            "retail_adapter_id": RETAIL_F061_ADAPTER_ID,
            "retail_adapter_sha256": RETAIL_F061_ADAPTER_SHA256,
            "retail_adapter_contract": retail_f061_adapter_record(),
        },
        "boundary_selection": {
            "timestamp_order": "ASCENDING_UNIQUE_EXACT_INTEGER",
            "eligible_gap_rule": "NO_COMPLETE_CUSTOMER_INTERVAL_CROSSES_GAP",
            "first_left_customer_count": "TARGET_TRAIN",
            "second_left_customer_count": "TARGET_TRAIN_PLUS_VALIDATION",
            "pair_tie_break": "LEXICOGRAPHICALLY_FIRST_ADJACENT_GAP_PAIR",
            "split_intervals": [
                "TRAIN_END_AT_OR_BEFORE_FIRST_GAP",
                "VALIDATION_START_AFTER_FIRST_AND_END_AT_OR_BEFORE_SECOND",
                "TEST_START_AFTER_SECOND",
            ],
        },
        "assignment_output": {
            "schema": F060_ASSIGNMENT_SCHEMA,
            "rule_id": F060_RULE_ID,
            "includes_f061_mode": True,
            "customer_assignment_order": "ASCENDING_CUSTOMER_KEY_BYTES",
            "row_assignment_order": "ASCENDING_ROW_ORDINAL",
            "input_permutation_invariant": True,
            "manifest_domain_hex": _F060_ASSIGNMENT_DOMAIN.hex(),
            "validation_domain_hex": (
                _F060_ASSIGNMENT_VALIDATION_DOMAIN.hex()
            ),
        },
        "prohibitions": {
            "exclusion_count": 0,
            "retry_count": 0,
            "resplit_count": 0,
            "top_up_count": 0,
            "fallback_or_customer_migration_permitted": False,
            "source_or_snapshot_opened_by_splitter": False,
        },
        "integrated_receipt_and_replay": {
            "active_contract_identity_bound": True,
            "shared_policy_definition_sha256_bound": True,
            "retail_adapter_identity_and_digest_bound": True,
            "normalized_rows_and_f061_allocation_replayed": True,
            "all_split_fields_and_self_digest_must_match_replay": True,
            "snapshot_projection_and_record_count_crosslinked": True,
            "maximum_decision": "ELIGIBLE_FOR_INDEPENDENT_ADMISSION",
            "domain_admitted": False,
            "split_receipt_domain_hex": _SPLIT_RECEIPT_DOMAIN.hex(),
        },
        "implementation": {
            "implementation_id": (
                "PURE_PYTHON_NO_IO_RETAIL_F060_SPLITTER_AND_REPLAY_V3"
            ),
            "module": (
                "heterodiff.data.online_retail_ii_admission_preflight"
            ),
            "entrypoints": [
                "resolve_f061_allocation",
                "split_retail_source_civil_rows",
                "RetailSplitReceipt.create",
                "evaluate_retail_training_admission",
            ],
            "filesystem_network_entropy_or_subprocess_access": False,
        },
    }


def active_retail_split_contract_sha256(record: object = None) -> str:
    """Hash the canonical active contract or one mutation for audit."""

    value = active_retail_split_contract_record() if record is None else record
    return _digest(_ACTIVE_RETAIL_SPLIT_CONTRACT_DOMAIN, value)


ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256 = (
    "b1a4fef836a50987b5d723e2bd133605bd907b4d7904f7cd6e87ca1d83077659"
)


def _validate_active_retail_split_contract_identity() -> None:
    """Reject runtime drift from the frozen active split contract."""

    if (
        active_retail_split_contract_sha256()
        != ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    ):
        raise RetailPreflightError("ACTIVE_RETAIL_SPLIT_CONTRACT_RUNTIME_DRIFT")


def _require_sha256(value: object, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise RetailPreflightError(name + " must be a lowercase SHA-256")
    return value


def _require_exact_int(value: object, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise RetailPreflightError(
            name + " must be an exact integer >= " + str(minimum)
        )
    return value


def _require_exact_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise RetailPreflightError(name + " must be an exact Boolean")
    return value


def _require_exact_string_constant(
    value: object,
    expected: str,
    code: str,
) -> str:
    """Reject equality-compatible subclasses at fixed string boundaries."""

    if type(value) is not str or value != expected:
        raise RetailPreflightError(code)
    return value


def _require_ascii_token(value: object, name: str, maximum: int = 160) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or not value.isascii()
        or value != value.strip()
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
    ):
        raise RetailPreflightError(name + " must be a bounded printable ASCII token")
    return value


def _require_nonplaceholder_identifier(value: object, name: str) -> str:
    token = _require_ascii_token(value, name)
    if token.upper() in _SUPPORT_PLACEHOLDERS:
        raise RetailPreflightError(name + " is unresolved")
    return token


def _require_private_locator(value: object, name: str) -> str:
    token = _require_ascii_token(value, name, 512)
    prefix = "private-custody/online-retail-ii/"
    if not token.startswith(prefix) or token.startswith("/") or "\\" in token:
        raise RetailPreflightError(name + " is not an Online Retail II private locator")
    parts = token.split("/")
    if any(
        part in ("", ".", "..") or _SAFE_LOCATOR_PART_RE.fullmatch(part) is None
        for part in parts
    ):
        raise RetailPreflightError(name + " has an unsafe locator component")
    if len(parts) < 4:
        raise RetailPreflightError(name + " must identify a private object")
    return token


def _strict_mapping(value: object, keys: Sequence[str], code: str) -> Mapping[str, Any]:
    if (
        type(value) is not dict
        or any(type(key) is not str for key in value)
        or set(value) != set(keys)
    ):
        raise RetailPreflightError(code)
    return value


def _split_integer_mapping(value: object, code: str, minimum: int) -> Dict[str, int]:
    mapping = _strict_mapping(value, SPLITS, code)
    return {
        split: _require_exact_int(mapping[split], code + "." + split, minimum)
        for split in SPLITS
    }


_F061_PROPOSAL_KEYS = (
    "schema_version",
    "allocation_id",
    "mode",
    "values",
    "denominator",
    "minimum_counts",
    "power_requirement_id",
)


def f061_allocation_proposal_sha256(proposal: object) -> str:
    """Hash the exact pre-review allocation proposal a receipt must bind."""

    row = _strict_mapping(
        proposal, _F061_PROPOSAL_KEYS, "INVALID_F061_PROPOSAL_ROSTER"
    )
    _require_exact_string_constant(
        row["schema_version"],
        F061_ALLOCATION_SCHEMA,
        "INVALID_F061_SCHEMA",
    )
    _require_nonplaceholder_identifier(row["allocation_id"], "allocation_id")
    _require_nonplaceholder_identifier(
        row["power_requirement_id"], "power_requirement_id"
    )
    mode = row["mode"]
    if type(mode) is not str or mode not in (
        "EXACT_COUNTS",
        "EXACT_PROPORTIONS_HAMILTON",
    ):
        raise RetailPreflightError("INVALID_F061_MODE")
    _split_integer_mapping(row["values"], "INVALID_F061_VALUES", 1)
    _split_integer_mapping(
        row["minimum_counts"], "INVALID_F061_MINIMUM_COUNTS", 1
    )
    if mode == "EXACT_COUNTS":
        if row["denominator"] is not None:
            raise RetailPreflightError("F061_COUNTS_DENOMINATOR_MUST_BE_NULL")
    else:
        _require_exact_int(row["denominator"], "denominator", 1)
    return _digest(_ALLOCATION_PROPOSAL_DOMAIN, dict(row))


def resolve_f061_allocation(
    allocation: object, customer_count: object
) -> Dict[str, Any]:
    """Resolve one exact, independently power-reviewed F061 definition.

    ``EXACT_COUNTS`` uses ``values`` as customer counts and requires
    ``denominator`` to be ``None``.  ``EXACT_PROPORTIONS_HAMILTON`` uses the
    three positive integer numerators in ``values`` and a positive denominator.
    Hamilton remainder ties use the fixed order TRAIN, VALIDATION, TEST.

    The supplied minimum counts are part of the power receipt boundary.  This
    function refuses unresolved reviews and any resolved split below a minimum.
    """

    count = _require_exact_int(customer_count, "customer_count", 1)
    keys = (
        "schema_version",
        "allocation_id",
        "mode",
        "values",
        "denominator",
        "minimum_counts",
        "power_requirement_id",
        "allocation_proposal_sha256",
        "power_review_receipt_sha256",
        "power_review_accepted",
    )
    row = _strict_mapping(allocation, keys, "INVALID_F061_ALLOCATION_ROSTER")
    _require_exact_string_constant(
        row["schema_version"],
        F061_ALLOCATION_SCHEMA,
        "INVALID_F061_SCHEMA",
    )
    allocation_id = _require_nonplaceholder_identifier(
        row["allocation_id"], "allocation_id"
    )
    power_requirement_id = _require_nonplaceholder_identifier(
        row["power_requirement_id"], "power_requirement_id"
    )
    proposal = {key: row[key] for key in _F061_PROPOSAL_KEYS}
    proposal_sha256 = _require_sha256(
        row["allocation_proposal_sha256"], "allocation_proposal_sha256"
    )
    if f061_allocation_proposal_sha256(proposal) != proposal_sha256:
        raise RetailPreflightError("F061_POWER_REVIEW_PROPOSAL_BINDING_MISMATCH")
    power_receipt = _require_sha256(
        row["power_review_receipt_sha256"], "power_review_receipt_sha256"
    )
    if (
        _require_exact_bool(
            row["power_review_accepted"],
            "power_review_accepted",
        )
        is not True
    ):
        raise RetailPreflightError("F061_POWER_REVIEW_UNRESOLVED")
    minimum_counts = _split_integer_mapping(
        row["minimum_counts"], "INVALID_F061_MINIMUM_COUNTS", 1
    )
    mode = row["mode"]
    if type(mode) is not str:
        raise RetailPreflightError("INVALID_F061_MODE")
    values = _split_integer_mapping(row["values"], "INVALID_F061_VALUES", 1)

    if mode == "EXACT_COUNTS":
        if row["denominator"] is not None:
            raise RetailPreflightError("F061_COUNTS_DENOMINATOR_MUST_BE_NULL")
        resolved = values
        if sum(resolved.values()) != count:
            raise RetailPreflightError("F061_COUNTS_DO_NOT_COVER_CUSTOMERS")
    elif mode == "EXACT_PROPORTIONS_HAMILTON":
        denominator = _require_exact_int(row["denominator"], "denominator", 1)
        if sum(values.values()) != denominator:
            raise RetailPreflightError("F061_PROPORTIONS_DO_NOT_SUM_TO_DENOMINATOR")
        resolved = {
            split: count * values[split] // denominator for split in SPLITS
        }
        remainders = {
            split: count * values[split] % denominator for split in SPLITS
        }
        remaining = count - sum(resolved.values())
        priority = sorted(
            SPLITS, key=lambda split: (-remainders[split], SPLITS.index(split))
        )
        for split in priority[:remaining]:
            resolved[split] += 1
    else:
        raise RetailPreflightError("INVALID_F061_MODE")

    underpowered = [
        split for split in SPLITS if resolved[split] < minimum_counts[split]
    ]
    if underpowered:
        raise RetailPreflightError(
            "F061_UNDERPOWERED_SPLIT:" + ",".join(underpowered)
        )
    definition = {
        "schema_version": F061_ALLOCATION_SCHEMA,
        "allocation_id": allocation_id,
        "mode": mode,
        "values": values,
        "denominator": row["denominator"],
        "minimum_counts": minimum_counts,
        "power_requirement_id": power_requirement_id,
        "allocation_proposal_sha256": proposal_sha256,
        "power_review_receipt_sha256": power_receipt,
        "power_review_accepted": True,
    }
    definition_sha256 = _digest(_ALLOCATION_DEFINITION_DOMAIN, definition)
    resolution = {
        "allocation_definition_sha256": definition_sha256,
        "customer_count": count,
        "resolved_customer_counts": resolved,
    }
    return {
        **definition,
        "allocation_definition_sha256": definition_sha256,
        "customer_count": count,
        "resolved_customer_counts": resolved,
        "resolved_allocation_sha256": _digest(
            _ALLOCATION_RESOLUTION_DOMAIN, resolution
        ),
    }


def _normalize_rows(
    rows: object,
) -> Tuple[Tuple[Dict[str, Any], ...], Dict[bytes, Tuple[int, int]]]:
    if type(rows) is not list or not rows:
        raise RetailPreflightError("INVALID_RETAIL_NORMALIZED_ROWS")
    expected = (
        "row_ordinal",
        "customer_key_hex",
        "timestamp_source_civil_microseconds_since_2009_12_01",
    )
    normalized = []
    ordinals = set()
    customer_intervals: Dict[bytes, Tuple[int, int]] = {}
    for raw in rows:
        row = _strict_mapping(raw, expected, "INVALID_RETAIL_NORMALIZED_ROW_ROSTER")
        ordinal = _require_exact_int(row["row_ordinal"], "row_ordinal")
        if ordinal in ordinals:
            raise RetailPreflightError("DUPLICATE_ROW_ORDINAL")
        ordinals.add(ordinal)
        key_hex = row["customer_key_hex"]
        if (
            type(key_hex) is not str
            or not key_hex
            or len(key_hex) % 2
            or len(key_hex) > 10
            or key_hex != key_hex.lower()
            or any(character not in "0123456789abcdef" for character in key_hex)
        ):
            raise RetailPreflightError("INVALID_CUSTOMER_KEY_HEX")
        try:
            key = bytes.fromhex(key_hex)
            customer_id = key.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise RetailPreflightError("INVALID_CUSTOMER_KEY_HEX") from error
        if _CUSTOMER_RE.fullmatch(customer_id) is None:
            raise RetailPreflightError("INVALID_CANONICAL_CUSTOMER_ID")
        timestamp = _require_exact_int(
            row["timestamp_source_civil_microseconds_since_2009_12_01"],
            "timestamp_source_civil_microseconds_since_2009_12_01",
        )
        if timestamp >= RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS:
            raise RetailPreflightError("SOURCE_CIVIL_TIMESTAMP_OUTSIDE_HORIZON")
        normalized.append(
            {
                "row_ordinal": ordinal,
                "customer_key_hex": key_hex,
                "timestamp_source_civil_microseconds_since_2009_12_01": timestamp,
            }
        )
        if key not in customer_intervals:
            customer_intervals[key] = (timestamp, timestamp)
        else:
            minimum, maximum = customer_intervals[key]
            customer_intervals[key] = (min(minimum, timestamp), max(maximum, timestamp))
    if ordinals != set(range(len(normalized))):
        raise RetailPreflightError("ROW_ORDINALS_MUST_BE_CONTIGUOUS_ZERO_BASED")
    normalized.sort(key=lambda item: item["row_ordinal"])
    return tuple(normalized), customer_intervals


def split_retail_source_civil_rows(
    rows: object, allocation: object
) -> Dict[str, Any]:
    """Apply the exact source-civil, F061-parameterized F060 V2 rule.

    The result is deterministic and independent of input row order.  It uses
    complete closed customer intervals and the lexicographically first pair of
    adjacent observed-timestamp gaps.  No fallback allocation, exclusion,
    retry, resplit, top-up, customer migration, or row reassignment exists.
    """

    normalized, intervals = _normalize_rows(rows)
    resolved = resolve_f061_allocation(allocation, len(intervals))
    targets = resolved["resolved_customer_counts"]
    timestamps = sorted(
        {
            row["timestamp_source_civil_microseconds_since_2009_12_01"]
            for row in normalized
        }
    )
    if len(timestamps) < 3:
        raise RetailPreflightError(
            "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
        )
    timestamp_index = {timestamp: index for index, timestamp in enumerate(timestamps)}
    start_counts = [0] * len(timestamps)
    end_counts = [0] * len(timestamps)
    indexed_intervals: Dict[bytes, Tuple[int, int]] = {}
    for key, (minimum, maximum) in intervals.items():
        start = timestamp_index[minimum]
        end = timestamp_index[maximum]
        indexed_intervals[key] = (start, end)
        start_counts[start] += 1
        end_counts[end] += 1

    feasible_gaps_by_left_count: Dict[int, list[int]] = {}
    left_count = 0
    started_count = 0
    customer_count = len(intervals)
    for gap in range(len(timestamps) - 1):
        left_count += end_counts[gap]
        started_count += start_counts[gap]
        right_count = customer_count - started_count
        if left_count + right_count == customer_count:
            feasible_gaps_by_left_count.setdefault(left_count, []).append(gap)

    first_candidates = feasible_gaps_by_left_count.get(targets["TRAIN"], [])
    second_candidates = feasible_gaps_by_left_count.get(
        targets["TRAIN"] + targets["VALIDATION"], []
    )
    selected: Optional[Tuple[int, int]] = None
    for first_gap in first_candidates:
        position = bisect.bisect_right(second_candidates, first_gap)
        if position < len(second_candidates):
            selected = (first_gap, second_candidates[position])
            break
    if selected is None:
        raise RetailPreflightError(
            "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
        )
    first_gap, second_gap = selected
    assignments: Dict[bytes, str] = {}
    for key, (start, end) in indexed_intervals.items():
        if end <= first_gap:
            assignments[key] = "TRAIN"
        elif start > first_gap and end <= second_gap:
            assignments[key] = "VALIDATION"
        elif start > second_gap:
            assignments[key] = "TEST"
        else:
            raise AssertionError("selected gaps do not preserve a customer interval")
    observed_customer_counts = {
        split: sum(value == split for value in assignments.values())
        for split in SPLITS
    }
    if observed_customer_counts != targets:
        raise AssertionError("selected gaps disagree with the F061 counts")

    row_assignments = [
        {
            "row_ordinal": row["row_ordinal"],
            "split": assignments[bytes.fromhex(row["customer_key_hex"])],
        }
        for row in normalized
    ]
    row_counts = {
        split: sum(item["split"] == split for item in row_assignments)
        for split in SPLITS
    }
    if any(row_counts[split] <= 0 for split in SPLITS):
        raise AssertionError("selected split has an empty row partition")
    boundary = {
        "train_last_timestamp_source_civil_microseconds_since_2009_12_01": (
            timestamps[first_gap]
        ),
        "validation_first_timestamp_source_civil_microseconds_since_2009_12_01": (
            timestamps[first_gap + 1]
        ),
        "validation_last_timestamp_source_civil_microseconds_since_2009_12_01": (
            timestamps[second_gap]
        ),
        "test_first_timestamp_source_civil_microseconds_since_2009_12_01": (
            timestamps[second_gap + 1]
        ),
    }
    input_payload = {
        "normalized_rows": list(normalized),
        "resolved_f061_allocation": resolved,
    }
    payload: Dict[str, Any] = {
        "schema_version": F060_ASSIGNMENT_SCHEMA,
        "rule_id": F060_RULE_ID,
        "domain_id": DOMAIN_ID,
        "slot_id": SLOT_ID,
        "outcome": "PASS",
        "normalized_projection_sha256": _digest(
            _F060_NORMALIZED_PROJECTION_DOMAIN, list(normalized)
        ),
        "rule_input_sha256": _digest(_F060_INPUT_DOMAIN, input_payload),
        "f061_mode": resolved["mode"],
        "allocation_definition_sha256": resolved["allocation_definition_sha256"],
        "resolved_allocation_sha256": resolved["resolved_allocation_sha256"],
        "row_count": len(normalized),
        "customer_count": customer_count,
        "target_customer_counts": targets,
        "observed_customer_counts": observed_customer_counts,
        "row_counts": row_counts,
        "boundary": boundary,
        "customer_assignments": [
            {"customer_key_hex": key.hex(), "split": assignments[key]}
            for key in sorted(assignments)
        ],
        "row_assignments": row_assignments,
        "exclusion_count": 0,
        "retry_count": 0,
        "resplit_count": 0,
        "top_up_count": 0,
        "source_or_snapshot_opened": False,
    }
    payload["assignment_manifest_sha256"] = _digest(
        _F060_ASSIGNMENT_DOMAIN, payload
    )
    return payload


def _dataclass_payload(value: object, excluded: Sequence[str] = ()) -> Dict[str, Any]:
    return {
        item.name: getattr(value, item.name)
        for item in fields(value)
        if item.name not in excluded
    }


def _revalidate_exact_dataclass(value: object, expected_type: type) -> bool:
    """Re-run a frozen receipt's constructor to detect post-issuance mutation."""

    if type(value) is not expected_type:
        return False
    try:
        rebuilt = expected_type(**_dataclass_payload(value))
    except (RetailPreflightError, TypeError, ValueError):
        return False
    return rebuilt == value


@dataclass(frozen=True)
class RetailSharedF061Policy:
    """Exact accepted shared policy and deterministic Retail adapter input."""

    schema_version: str
    allocation_id: str
    mode: str
    values: Tuple[int, int, int]
    denominator_is_null: bool
    denominator: int
    minimum_counts: Tuple[int, int, int]
    rounding_rule_id: str
    power_requirement_id: str
    allocation_proposal_sha256: str
    power_review_receipt_sha256: str
    power_review_accepted: bool
    allocation_definition_sha256: str
    retail_adapter_id: str
    retail_adapter_sha256: str

    def __post_init__(self) -> None:
        _require_exact_string_constant(
            self.schema_version,
            SHARED_F061_POLICY_SCHEMA,
            "SHARED_F061_POLICY_SCHEMA_MISMATCH",
        )
        _require_nonplaceholder_identifier(self.allocation_id, "allocation_id")
        _require_exact_string_constant(
            self.mode,
            INTEGRATED_F061_MODE,
            "SHARED_F061_MODE_MISMATCH",
        )
        for name in ("values", "minimum_counts"):
            value = getattr(self, name)
            if type(value) is not tuple or len(value) != 3:
                raise RetailPreflightError("SHARED_F061_TRIPLE_INVALID:" + name)
            for item in value:
                _require_exact_int(item, name, 1)
        if self.denominator_is_null is not False:
            raise RetailPreflightError("SHARED_F061_DENOMINATOR_NULL_FLAG_INVALID")
        denominator = _require_exact_int(self.denominator, "denominator", 1)
        if sum(self.values) != denominator:
            raise RetailPreflightError("SHARED_F061_VALUES_DO_NOT_SUM")
        _require_exact_string_constant(
            self.rounding_rule_id,
            SHARED_F061_HAMILTON_ROUNDING_RULE_ID,
            "SHARED_F061_ROUNDING_RULE_MISMATCH",
        )
        _require_nonplaceholder_identifier(
            self.power_requirement_id,
            "power_requirement_id",
        )
        _require_sha256(
            self.power_review_receipt_sha256,
            "power_review_receipt_sha256",
        )
        if _require_exact_bool(
            self.power_review_accepted,
            "power_review_accepted",
        ) is not True:
            raise RetailPreflightError("SHARED_F061_POWER_REVIEW_NOT_ACCEPTED")
        _require_exact_string_constant(
            self.retail_adapter_id,
            RETAIL_F061_ADAPTER_ID,
            "RETAIL_F061_ADAPTER_ID_MISMATCH",
        )
        _require_exact_string_constant(
            self.retail_adapter_sha256,
            RETAIL_F061_ADAPTER_SHA256,
            "RETAIL_F061_ADAPTER_SHA256_MISMATCH",
        )
        if retail_f061_adapter_sha256() != RETAIL_F061_ADAPTER_SHA256:
            raise RetailPreflightError("RETAIL_F061_ADAPTER_RUNTIME_DIGEST_MISMATCH")
        proposal_payload = {
            "schema_version": self.schema_version,
            "allocation_id": self.allocation_id,
            "mode": self.mode,
            "values": self.values,
            "denominator_is_null": self.denominator_is_null,
            "denominator": self.denominator,
            "minimum_counts": self.minimum_counts,
            "rounding_rule_id": self.rounding_rule_id,
            "power_requirement_id": self.power_requirement_id,
        }
        _require_sha256(
            self.allocation_proposal_sha256,
            "allocation_proposal_sha256",
        )
        if self.allocation_proposal_sha256 != _digest(
            _SHARED_F061_PROPOSAL_DOMAIN,
            proposal_payload,
        ):
            raise RetailPreflightError("SHARED_F061_PROPOSAL_DIGEST_MISMATCH")
        definition_payload = {
            "allocation_proposal_sha256": self.allocation_proposal_sha256,
            "power_review_receipt_sha256": self.power_review_receipt_sha256,
            "power_review_accepted": True,
        }
        _require_sha256(
            self.allocation_definition_sha256,
            "allocation_definition_sha256",
        )
        if self.allocation_definition_sha256 != _digest(
            _SHARED_F061_DEFINITION_DOMAIN,
            definition_payload,
        ):
            raise RetailPreflightError("SHARED_F061_DEFINITION_DIGEST_MISMATCH")

    @classmethod
    def create(
        cls,
        *,
        allocation_id: str,
        values: Tuple[int, int, int],
        denominator: int,
        minimum_counts: Tuple[int, int, int],
        power_requirement_id: str,
        power_review_receipt_sha256: str,
        power_review_accepted: bool,
    ) -> "RetailSharedF061Policy":
        proposal_payload = {
            "schema_version": SHARED_F061_POLICY_SCHEMA,
            "allocation_id": allocation_id,
            "mode": INTEGRATED_F061_MODE,
            "values": values,
            "denominator_is_null": False,
            "denominator": denominator,
            "minimum_counts": minimum_counts,
            "rounding_rule_id": SHARED_F061_HAMILTON_ROUNDING_RULE_ID,
            "power_requirement_id": power_requirement_id,
        }
        proposal_sha256 = _digest(
            _SHARED_F061_PROPOSAL_DOMAIN,
            proposal_payload,
        )
        definition_sha256 = _digest(
            _SHARED_F061_DEFINITION_DOMAIN,
            {
                "allocation_proposal_sha256": proposal_sha256,
                "power_review_receipt_sha256": power_review_receipt_sha256,
                "power_review_accepted": power_review_accepted,
            },
        )
        return cls(
            **proposal_payload,
            allocation_proposal_sha256=proposal_sha256,
            power_review_receipt_sha256=power_review_receipt_sha256,
            power_review_accepted=power_review_accepted,
            allocation_definition_sha256=definition_sha256,
            retail_adapter_id=RETAIL_F061_ADAPTER_ID,
            retail_adapter_sha256=RETAIL_F061_ADAPTER_SHA256,
        )

    def retail_allocation(self) -> Dict[str, Any]:
        """Project this exact accepted policy into the native Retail codec."""

        proposal = {
            "schema_version": F061_ALLOCATION_SCHEMA,
            "allocation_id": self.allocation_id,
            "mode": self.mode,
            "values": dict(zip(SPLITS, self.values)),
            "denominator": self.denominator,
            "minimum_counts": dict(zip(SPLITS, self.minimum_counts)),
            "power_requirement_id": self.power_requirement_id,
        }
        return {
            **proposal,
            "allocation_proposal_sha256": (
                f061_allocation_proposal_sha256(proposal)
            ),
            "power_review_receipt_sha256": self.power_review_receipt_sha256,
            "power_review_accepted": True,
        }


@dataclass(frozen=True)
class RetailSchemaReceipt:
    schema_id: str
    raw_fields: Tuple[str, ...]
    source_schema_sha256: str
    timestamp_semantics: str
    unit_price_semantics: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require_ascii_token(self.schema_id, "schema_id")
        if (
            type(self.raw_fields) is not tuple
            or any(type(value) is not str for value in self.raw_fields)
            or self.raw_fields != RETAIL_RAW_FIELDS
        ):
            raise RetailPreflightError("RETAIL_RAW_FIELD_ROSTER_MISMATCH")
        _require_sha256(self.source_schema_sha256, "source_schema_sha256")
        _require_exact_string_constant(
            self.timestamp_semantics,
            "SOURCE_CIVIL_SEVEN_TUPLE_NO_TIMEZONE_OR_INSTANT",
            "RETAIL_TIMESTAMP_SEMANTICS_MISMATCH",
        )
        _require_exact_string_constant(
            self.unit_price_semantics,
            "EXACT_SOURCE_DECIMAL_TOKEN_RATIONAL",
            "RETAIL_UNIT_PRICE_SEMANTICS_MISMATCH",
        )
        _require_sha256(self.receipt_sha256, "schema receipt_sha256")
        expected = _digest(
            _SCHEMA_RECEIPT_DOMAIN, _dataclass_payload(self, ("receipt_sha256",))
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("SCHEMA_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(
        cls,
        *,
        schema_id: str,
        source_schema_sha256: str,
    ) -> "RetailSchemaReceipt":
        payload = {
            "schema_id": schema_id,
            "raw_fields": RETAIL_RAW_FIELDS,
            "source_schema_sha256": source_schema_sha256,
            "timestamp_semantics": "SOURCE_CIVIL_SEVEN_TUPLE_NO_TIMEZONE_OR_INSTANT",
            "unit_price_semantics": "EXACT_SOURCE_DECIMAL_TOKEN_RATIONAL",
        }
        return cls(
            **payload,
            receipt_sha256=_digest(_SCHEMA_RECEIPT_DOMAIN, payload),
        )


@dataclass(frozen=True)
class RetailGovernanceReceipt:
    determination_id: str
    license_access_receipt_sha256: str
    privacy_determination_sha256: str
    retention_controls_receipt_sha256: str
    accountable_owner_acceptance_sha256: str
    analysis_scope: str
    approval_state: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require_nonplaceholder_identifier(self.determination_id, "determination_id")
        for name in (
            "license_access_receipt_sha256",
            "privacy_determination_sha256",
            "retention_controls_receipt_sha256",
            "accountable_owner_acceptance_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        _require_exact_string_constant(
            self.analysis_scope,
            "BOUNDED_INTERNAL_RESEARCH_ONLY",
            "INVALID_GOVERNANCE_ANALYSIS_SCOPE",
        )
        _require_exact_string_constant(
            self.approval_state,
            "APPROVED_FOR_BOUNDED_INTERNAL_ANALYSIS",
            "GOVERNANCE_APPROVAL_UNRESOLVED",
        )
        _require_sha256(self.receipt_sha256, "governance receipt_sha256")
        expected = _digest(
            _GOVERNANCE_RECEIPT_DOMAIN,
            _dataclass_payload(self, ("receipt_sha256",)),
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("GOVERNANCE_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(
        cls,
        *,
        determination_id: str,
        license_access_receipt_sha256: str,
        privacy_determination_sha256: str,
        retention_controls_receipt_sha256: str,
        accountable_owner_acceptance_sha256: str,
    ) -> "RetailGovernanceReceipt":
        payload = {
            "determination_id": determination_id,
            "license_access_receipt_sha256": license_access_receipt_sha256,
            "privacy_determination_sha256": privacy_determination_sha256,
            "retention_controls_receipt_sha256": retention_controls_receipt_sha256,
            "accountable_owner_acceptance_sha256": accountable_owner_acceptance_sha256,
            "analysis_scope": "BOUNDED_INTERNAL_RESEARCH_ONLY",
            "approval_state": "APPROVED_FOR_BOUNDED_INTERNAL_ANALYSIS",
        }
        return cls(
            **payload,
            receipt_sha256=_digest(_GOVERNANCE_RECEIPT_DOMAIN, payload),
        )


@dataclass(frozen=True)
class RetailSnapshotReceipt:
    snapshot_version: str
    source_version_receipt_sha256: str
    raw_snapshot_sha256: str
    raw_snapshot_bytes: int
    archive_inventory_sha256: str
    schema_receipt_sha256: str
    license_access_receipt_sha256: str
    governance_receipt_sha256: str
    normalized_projection_sha256: str
    normalized_projection_record_count: int
    private_locator: str
    post_snapshot_exclusion_count: int
    retry_resplit_topup_count: int
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require_ascii_token(self.snapshot_version, "snapshot_version")
        for name in (
            "source_version_receipt_sha256",
            "raw_snapshot_sha256",
            "archive_inventory_sha256",
            "schema_receipt_sha256",
            "license_access_receipt_sha256",
            "governance_receipt_sha256",
            "normalized_projection_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        _require_exact_int(self.raw_snapshot_bytes, "raw_snapshot_bytes", 1)
        _require_exact_int(
            self.normalized_projection_record_count,
            "normalized_projection_record_count",
            1,
        )
        _require_private_locator(self.private_locator, "snapshot private_locator")
        if (
            type(self.post_snapshot_exclusion_count) is not int
            or self.post_snapshot_exclusion_count != 0
        ):
            raise RetailPreflightError("POST_SNAPSHOT_EXCLUSION_FORBIDDEN")
        if (
            type(self.retry_resplit_topup_count) is not int
            or self.retry_resplit_topup_count != 0
        ):
            raise RetailPreflightError("SNAPSHOT_RETRY_RESPLIT_TOPUP_FORBIDDEN")
        _require_sha256(self.receipt_sha256, "snapshot receipt_sha256")
        expected = _digest(
            _SNAPSHOT_RECEIPT_DOMAIN,
            _dataclass_payload(self, ("receipt_sha256",)),
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("SNAPSHOT_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(cls, **values: Any) -> "RetailSnapshotReceipt":
        payload = dict(values)
        payload.setdefault("post_snapshot_exclusion_count", 0)
        payload.setdefault("retry_resplit_topup_count", 0)
        return cls(
            **payload,
            receipt_sha256=_digest(_SNAPSHOT_RECEIPT_DOMAIN, payload),
        )


def _validated_assignment_projection(value: object) -> Dict[str, Any]:
    """Validate the complete pure F060 output and return its receipt projection."""

    expected_keys = {
        "schema_version",
        "rule_id",
        "domain_id",
        "slot_id",
        "outcome",
        "normalized_projection_sha256",
        "rule_input_sha256",
        "f061_mode",
        "allocation_definition_sha256",
        "resolved_allocation_sha256",
        "row_count",
        "customer_count",
        "target_customer_counts",
        "observed_customer_counts",
        "row_counts",
        "boundary",
        "customer_assignments",
        "row_assignments",
        "exclusion_count",
        "retry_count",
        "resplit_count",
        "top_up_count",
        "source_or_snapshot_opened",
        "assignment_manifest_sha256",
    }
    _strict_mapping(
        value,
        tuple(expected_keys),
        "INVALID_F060_ASSIGNMENT_RESULT_ROSTER",
    )
    for name, expected in (
        ("schema_version", F060_ASSIGNMENT_SCHEMA),
        ("rule_id", F060_RULE_ID),
        ("domain_id", DOMAIN_ID),
        ("slot_id", SLOT_ID),
        ("outcome", "PASS"),
    ):
        _require_exact_string_constant(
            value[name],
            expected,
            "F060_ASSIGNMENT_IDENTITY_MISMATCH",
        )
    for name in (
        "normalized_projection_sha256",
        "rule_input_sha256",
        "allocation_definition_sha256",
        "resolved_allocation_sha256",
        "assignment_manifest_sha256",
    ):
        _require_sha256(value[name], name)
    f061_mode = value["f061_mode"]
    if type(f061_mode) is not str or f061_mode not in (
        "EXACT_COUNTS",
        INTEGRATED_F061_MODE,
    ):
        raise RetailPreflightError("INVALID_F060_F061_MODE")
    row_count = _require_exact_int(value["row_count"], "row_count", 3)
    customer_count = _require_exact_int(value["customer_count"], "customer_count", 3)

    count_rows: Dict[str, Dict[str, int]] = {}
    for name in (
        "target_customer_counts",
        "observed_customer_counts",
        "row_counts",
    ):
        raw_counts = _strict_mapping(
            value[name],
            SPLITS,
            "INVALID_F060_ASSIGNMENT_COUNT_ROSTER",
        )
        count_rows[name] = {
            split: _require_exact_int(raw_counts[split], name + "." + split, 1)
            for split in SPLITS
        }
    if count_rows["target_customer_counts"] != count_rows["observed_customer_counts"]:
        raise RetailPreflightError("F060_TARGET_OBSERVED_CUSTOMER_COUNT_MISMATCH")
    if sum(count_rows["observed_customer_counts"].values()) != customer_count:
        raise RetailPreflightError("F060_CUSTOMER_COUNT_MISMATCH")
    if sum(count_rows["row_counts"].values()) != row_count:
        raise RetailPreflightError("F060_ROW_COUNT_MISMATCH")

    customer_assignments = value["customer_assignments"]
    if (
        type(customer_assignments) is not list
        or len(customer_assignments) != customer_count
    ):
        raise RetailPreflightError("INVALID_F060_CUSTOMER_ASSIGNMENTS")
    customer_keys = set()
    observed_customer_counts = {split: 0 for split in SPLITS}
    for item in customer_assignments:
        _strict_mapping(
            item,
            ("customer_key_hex", "split"),
            "INVALID_F060_CUSTOMER_ASSIGNMENT",
        )
        key_hex = item["customer_key_hex"]
        split = item["split"]
        if (
            type(key_hex) is not str
            or not key_hex
            or key_hex in customer_keys
            or any(character not in "0123456789abcdef" for character in key_hex)
            or type(split) is not str
            or split not in SPLITS
        ):
            raise RetailPreflightError("INVALID_F060_CUSTOMER_ASSIGNMENT")
        customer_keys.add(key_hex)
        observed_customer_counts[split] += 1
    if observed_customer_counts != count_rows["observed_customer_counts"]:
        raise RetailPreflightError("F060_CUSTOMER_ASSIGNMENT_COUNT_MISMATCH")

    row_assignments = value["row_assignments"]
    if type(row_assignments) is not list or len(row_assignments) != row_count:
        raise RetailPreflightError("INVALID_F060_ROW_ASSIGNMENTS")
    observed_row_counts = {split: 0 for split in SPLITS}
    ordinals = set()
    for item in row_assignments:
        _strict_mapping(
            item,
            ("row_ordinal", "split"),
            "INVALID_F060_ROW_ASSIGNMENT",
        )
        ordinal = _require_exact_int(item["row_ordinal"], "row_ordinal")
        split = item["split"]
        if ordinal in ordinals or type(split) is not str or split not in SPLITS:
            raise RetailPreflightError("INVALID_F060_ROW_ASSIGNMENT")
        ordinals.add(ordinal)
        observed_row_counts[split] += 1
    if (
        ordinals != set(range(row_count))
        or observed_row_counts != count_rows["row_counts"]
    ):
        raise RetailPreflightError("F060_ROW_ASSIGNMENT_COUNT_MISMATCH")

    boundary = value["boundary"]
    boundary_keys = (
        "train_last_timestamp_source_civil_microseconds_since_2009_12_01",
        "validation_first_timestamp_source_civil_microseconds_since_2009_12_01",
        "validation_last_timestamp_source_civil_microseconds_since_2009_12_01",
        "test_first_timestamp_source_civil_microseconds_since_2009_12_01",
    )
    _strict_mapping(boundary, boundary_keys, "INVALID_F060_BOUNDARY_ROSTER")
    boundary_values = tuple(
        _require_exact_int(boundary[name], name) for name in boundary_keys
    )
    if not (
        boundary_values[0]
        < boundary_values[1]
        <= boundary_values[2]
        < boundary_values[3]
    ):
        raise RetailPreflightError("INVALID_F060_BOUNDARY_ORDER")
    if boundary_values[-1] >= RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS:
        raise RetailPreflightError("F060_BOUNDARY_OUTSIDE_HORIZON")
    for name in ("exclusion_count", "retry_count", "resplit_count", "top_up_count"):
        if type(value[name]) is not int or value[name] != 0:
            raise RetailPreflightError("F060_REPAIR_OR_EXCLUSION_FORBIDDEN")
    if type(value["source_or_snapshot_opened"]) is not bool or value[
        "source_or_snapshot_opened"
    ] is not False:
        raise RetailPreflightError("F060_PURE_SPLITTER_BOUNDARY_VIOLATED")

    manifest_payload = dict(value)
    manifest_digest = manifest_payload.pop("assignment_manifest_sha256")
    if _digest(_F060_ASSIGNMENT_DOMAIN, manifest_payload) != manifest_digest:
        raise RetailPreflightError("F060_ASSIGNMENT_MANIFEST_DIGEST_MISMATCH")
    projection = {
        "f060_rule_id": value["rule_id"],
        "f060_assignment_schema": value["schema_version"],
        "normalized_projection_sha256": value["normalized_projection_sha256"],
        "rule_input_sha256": value["rule_input_sha256"],
        "f061_mode": f061_mode,
        "allocation_definition_sha256": value["allocation_definition_sha256"],
        "resolved_allocation_sha256": value["resolved_allocation_sha256"],
        "assignment_manifest_sha256": manifest_digest,
        "boundary_sha256": _digest(_F060_ASSIGNMENT_VALIDATION_DOMAIN, boundary),
        "row_count": row_count,
        "customer_count": customer_count,
        "target_customer_counts": tuple(
            count_rows["target_customer_counts"][split] for split in SPLITS
        ),
        "observed_customer_counts": tuple(
            count_rows["observed_customer_counts"][split] for split in SPLITS
        ),
        "row_counts": tuple(count_rows["row_counts"][split] for split in SPLITS),
    }
    projection["assignment_validation_receipt_sha256"] = _digest(
        _F060_ASSIGNMENT_VALIDATION_DOMAIN, projection
    )
    return projection


_SPLIT_VALIDATION_FIELDS = (
    "f060_rule_id",
    "f060_assignment_schema",
    "active_split_contract_id",
    "active_split_contract_sha256",
    "normalized_projection_sha256",
    "rule_input_sha256",
    "f061_mode",
    "shared_policy_definition_sha256",
    "retail_f061_adapter_id",
    "retail_f061_adapter_sha256",
    "allocation_definition_sha256",
    "resolved_allocation_sha256",
    "assignment_manifest_sha256",
    "boundary_sha256",
    "row_count",
    "customer_count",
    "target_customer_counts",
    "observed_customer_counts",
    "row_counts",
)


@dataclass(frozen=True)
class RetailSplitReceipt:
    snapshot_receipt_sha256: str
    f060_rule_id: str
    f060_assignment_schema: str
    active_split_contract_id: str
    active_split_contract_sha256: str
    normalized_projection_sha256: str
    rule_input_sha256: str
    f061_mode: str
    shared_policy_definition_sha256: str
    retail_f061_adapter_id: str
    retail_f061_adapter_sha256: str
    allocation_definition_sha256: str
    resolved_allocation_sha256: str
    assignment_manifest_sha256: str
    boundary_sha256: str
    row_count: int
    customer_count: int
    target_customer_counts: Tuple[int, int, int]
    observed_customer_counts: Tuple[int, int, int]
    row_counts: Tuple[int, int, int]
    assignment_validation_receipt_sha256: str
    split_manifest_private_locator: str
    exclusion_count: int
    retry_count: int
    resplit_count: int
    top_up_count: int
    receipt_sha256: str

    def __post_init__(self) -> None:
        _validate_active_retail_split_contract_identity()
        _require_sha256(self.snapshot_receipt_sha256, "snapshot_receipt_sha256")
        _require_exact_string_constant(
            self.f060_rule_id,
            F060_RULE_ID,
            "SPLIT_F060_RULE_ID_MISMATCH",
        )
        _require_exact_string_constant(
            self.f060_assignment_schema,
            F060_ASSIGNMENT_SCHEMA,
            "SPLIT_F060_SCHEMA_MISMATCH",
        )
        _require_exact_string_constant(
            self.active_split_contract_id,
            ACTIVE_RETAIL_SPLIT_CONTRACT_ID,
            "ACTIVE_RETAIL_SPLIT_CONTRACT_ID_MISMATCH",
        )
        _require_exact_string_constant(
            self.active_split_contract_sha256,
            ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256,
            "ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256_MISMATCH",
        )
        _require_exact_string_constant(
            self.f061_mode,
            INTEGRATED_F061_MODE,
            "RETAIL_INTEGRATED_F061_MODE_MISMATCH",
        )
        _require_sha256(
            self.shared_policy_definition_sha256,
            "shared_policy_definition_sha256",
        )
        _require_exact_string_constant(
            self.retail_f061_adapter_id,
            RETAIL_F061_ADAPTER_ID,
            "RETAIL_F061_ADAPTER_ID_MISMATCH",
        )
        _require_exact_string_constant(
            self.retail_f061_adapter_sha256,
            RETAIL_F061_ADAPTER_SHA256,
            "RETAIL_F061_ADAPTER_SHA256_MISMATCH",
        )
        for name in (
            "normalized_projection_sha256",
            "rule_input_sha256",
            "allocation_definition_sha256",
            "resolved_allocation_sha256",
            "assignment_manifest_sha256",
            "boundary_sha256",
            "assignment_validation_receipt_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        row_count = _require_exact_int(self.row_count, "row_count", 3)
        customer_count = _require_exact_int(self.customer_count, "customer_count", 3)
        for name in (
            "target_customer_counts",
            "observed_customer_counts",
            "row_counts",
        ):
            values = getattr(self, name)
            if type(values) is not tuple or len(values) != 3:
                raise RetailPreflightError("SPLIT_COUNT_TRIPLE_INVALID")
            for value in values:
                _require_exact_int(value, name, 1)
        if self.target_customer_counts != self.observed_customer_counts:
            raise RetailPreflightError("SPLIT_TARGET_OBSERVED_COUNTS_MISMATCH")
        if (
            sum(self.observed_customer_counts) != customer_count
            or sum(self.row_counts) != row_count
        ):
            raise RetailPreflightError("SPLIT_TOTAL_COUNT_MISMATCH")
        validation_projection = {
            name: getattr(self, name)
            for name in _SPLIT_VALIDATION_FIELDS
        }
        if _digest(
            _F060_ASSIGNMENT_VALIDATION_DOMAIN, validation_projection
        ) != self.assignment_validation_receipt_sha256:
            raise RetailPreflightError("ASSIGNMENT_VALIDATION_RECEIPT_MISMATCH")
        _require_private_locator(
            self.split_manifest_private_locator, "split_manifest_private_locator"
        )
        for name in ("exclusion_count", "retry_count", "resplit_count", "top_up_count"):
            if type(getattr(self, name)) is not int or getattr(self, name) != 0:
                raise RetailPreflightError(
                    "SPLIT_EXCLUSION_RETRY_RESPLIT_TOPUP_FORBIDDEN"
                )
        _require_sha256(self.receipt_sha256, "split receipt_sha256")
        expected = _digest(
            _SPLIT_RECEIPT_DOMAIN, _dataclass_payload(self, ("receipt_sha256",))
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("SPLIT_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(
        cls,
        *,
        snapshot_receipt_sha256: str,
        normalized_rows: object,
        allocation: object,
        shared_policy: object,
        split_manifest_private_locator: str,
    ) -> "RetailSplitReceipt":
        if not _revalidate_exact_dataclass(
            shared_policy,
            RetailSharedF061Policy,
        ):
            raise RetailPreflightError("INVALID_SHARED_F061_POLICY")
        assert type(shared_policy) is RetailSharedF061Policy
        expected_allocation = shared_policy.retail_allocation()
        if (
            type(allocation) is not dict
            or _canonical_bytes(allocation)
            != _canonical_bytes(expected_allocation)
        ):
            raise RetailPreflightError("RETAIL_F061_ADAPTER_PROJECTION_MISMATCH")
        assignment_result = split_retail_source_civil_rows(
            normalized_rows, allocation
        )
        projection = _validated_assignment_projection(assignment_result)
        projection.pop("assignment_validation_receipt_sha256")
        payload = {
            "snapshot_receipt_sha256": snapshot_receipt_sha256,
            **projection,
            "active_split_contract_id": ACTIVE_RETAIL_SPLIT_CONTRACT_ID,
            "active_split_contract_sha256": (
                ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
            ),
            "shared_policy_definition_sha256": (
                shared_policy.allocation_definition_sha256
            ),
            "retail_f061_adapter_id": shared_policy.retail_adapter_id,
            "retail_f061_adapter_sha256": (
                shared_policy.retail_adapter_sha256
            ),
            "split_manifest_private_locator": split_manifest_private_locator,
            "exclusion_count": 0,
            "retry_count": 0,
            "resplit_count": 0,
            "top_up_count": 0,
        }
        payload["assignment_validation_receipt_sha256"] = _digest(
            _F060_ASSIGNMENT_VALIDATION_DOMAIN,
            {name: payload[name] for name in _SPLIT_VALIDATION_FIELDS},
        )
        return cls(
            **payload,
            receipt_sha256=_digest(_SPLIT_RECEIPT_DOMAIN, payload),
        )


@dataclass(frozen=True)
class RetailSupportReceipt:
    snapshot_receipt_sha256: str
    clean_observation_kernel_id: str
    common_support_policy_id: str
    observation_reference_id: str
    observation_reference_sha256: str
    full_support_component_id: str
    full_support_component_sha256: str
    mixture_weight_numerator: int
    mixture_weight_denominator: int
    support_proof_id: str
    support_proof_sha256: str
    support_implementation_id: str
    support_implementation_sha256: str
    support_certificate_id: str
    support_certificate_sha256: str
    acquisition_justification_receipt_sha256: str
    independent_review_receipt_sha256: str
    clean_kernel_kept_separate: bool
    theorem_convenience_noise_added: bool
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require_sha256(self.snapshot_receipt_sha256, "snapshot_receipt_sha256")
        _require_exact_string_constant(
            self.clean_observation_kernel_id,
            OBSERVATION_KERNEL_ID,
            "OBSERVATION_KERNEL_ID_MISMATCH",
        )
        _require_exact_string_constant(
            self.common_support_policy_id,
            COMMON_SUPPORT_POLICY_ID,
            "UNSELECTED_COMMON_SUPPORT_ROUTE",
        )
        _require_nonplaceholder_identifier(
            self.observation_reference_id, "observation_reference_id"
        )
        for name in (
            "full_support_component_id",
            "support_proof_id",
            "support_implementation_id",
            "support_certificate_id",
        ):
            _require_nonplaceholder_identifier(getattr(self, name), name)
        for name in (
            "observation_reference_sha256",
            "full_support_component_sha256",
            "support_proof_sha256",
            "support_implementation_sha256",
            "support_certificate_sha256",
            "acquisition_justification_receipt_sha256",
            "independent_review_receipt_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        numerator = _require_exact_int(
            self.mixture_weight_numerator, "mixture_weight_numerator", 1
        )
        denominator = _require_exact_int(
            self.mixture_weight_denominator, "mixture_weight_denominator", 2
        )
        if numerator >= denominator:
            raise RetailPreflightError(
                "MIXTURE_WEIGHT_MUST_LIE_STRICTLY_BETWEEN_ZERO_AND_ONE"
            )
        if _require_exact_bool(
            self.clean_kernel_kept_separate, "clean_kernel_kept_separate"
        ) is not True:
            raise RetailPreflightError("CLEAN_KERNEL_MUST_REMAIN_SEPARATE")
        if _require_exact_bool(
            self.theorem_convenience_noise_added,
            "theorem_convenience_noise_added",
        ) is not False:
            raise RetailPreflightError("THEOREM_CONVENIENCE_NOISE_FORBIDDEN")
        _require_sha256(self.receipt_sha256, "support receipt_sha256")
        expected = _digest(
            _SUPPORT_RECEIPT_DOMAIN,
            _dataclass_payload(self, ("receipt_sha256",)),
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("SUPPORT_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(cls, **values: Any) -> "RetailSupportReceipt":
        payload = dict(values)
        payload.setdefault("clean_observation_kernel_id", OBSERVATION_KERNEL_ID)
        payload.setdefault("common_support_policy_id", COMMON_SUPPORT_POLICY_ID)
        payload.setdefault("clean_kernel_kept_separate", True)
        payload.setdefault("theorem_convenience_noise_added", False)
        return cls(
            **payload,
            receipt_sha256=_digest(_SUPPORT_RECEIPT_DOMAIN, payload),
        )


@dataclass(frozen=True)
class RetailDuplicateAuditReceipt:
    snapshot_receipt_sha256: str
    split_receipt_sha256: str
    audit_id: str
    audit_algorithm_id: str
    audit_implementation_sha256: str
    audit_input_manifest_sha256: str
    completion_certificate_sha256: str
    audited_normalized_projection_sha256: str
    audited_assignment_manifest_sha256: str
    audited_row_count: int
    audited_customer_count: int
    eligible_cross_split_row_pair_count: int
    checked_cross_split_row_pair_count: int
    complete_roster_checked: bool
    exact_duplicate_cross_split_lineage_count: int
    near_duplicate_cross_split_lineage_count: int
    near_duplicate_rule_id: str
    model_outcome_or_metric_inspected: bool
    independently_verified: bool
    completion_attestation_sha256: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        _require_sha256(self.snapshot_receipt_sha256, "snapshot_receipt_sha256")
        _require_sha256(self.split_receipt_sha256, "split_receipt_sha256")
        _require_nonplaceholder_identifier(self.audit_id, "audit_id")
        _require_exact_string_constant(
            self.audit_algorithm_id,
            DUPLICATE_AUDIT_ALGORITHM_ID,
            "DUPLICATE_AUDIT_ALGORITHM_ID_MISMATCH",
        )
        _require_sha256(
            self.audit_implementation_sha256,
            "audit_implementation_sha256",
        )
        _require_sha256(
            self.completion_certificate_sha256,
            "completion_certificate_sha256",
        )
        for name in (
            "audited_normalized_projection_sha256",
            "audited_assignment_manifest_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        _require_exact_int(self.audited_row_count, "audited_row_count", 3)
        _require_exact_int(
            self.audited_customer_count,
            "audited_customer_count",
            3,
        )
        eligible_pair_count = _require_exact_int(
            self.eligible_cross_split_row_pair_count,
            "eligible_cross_split_row_pair_count",
            1,
        )
        checked_pair_count = _require_exact_int(
            self.checked_cross_split_row_pair_count,
            "checked_cross_split_row_pair_count",
        )
        if checked_pair_count > eligible_pair_count:
            raise RetailPreflightError("DUPLICATE_AUDIT_CHECKED_PAIR_COUNT_OVERFLOW")
        complete = _require_exact_bool(
            self.complete_roster_checked,
            "complete_roster_checked",
        )
        if complete and checked_pair_count != eligible_pair_count:
            raise RetailPreflightError("DUPLICATE_AUDIT_FALSE_COMPLETION_ATTESTATION")
        _require_nonplaceholder_identifier(
            self.near_duplicate_rule_id, "near_duplicate_rule_id"
        )
        _require_exact_int(
            self.exact_duplicate_cross_split_lineage_count,
            "exact_duplicate_cross_split_lineage_count",
        )
        _require_exact_int(
            self.near_duplicate_cross_split_lineage_count,
            "near_duplicate_cross_split_lineage_count",
        )
        _require_exact_bool(
            self.model_outcome_or_metric_inspected,
            "model_outcome_or_metric_inspected",
        )
        _require_exact_bool(self.independently_verified, "independently_verified")
        audit_input = {
            "snapshot_receipt_sha256": self.snapshot_receipt_sha256,
            "split_receipt_sha256": self.split_receipt_sha256,
            "audit_algorithm_id": self.audit_algorithm_id,
            "audit_implementation_sha256": self.audit_implementation_sha256,
            "audited_normalized_projection_sha256": (
                self.audited_normalized_projection_sha256
            ),
            "audited_assignment_manifest_sha256": (
                self.audited_assignment_manifest_sha256
            ),
            "audited_row_count": self.audited_row_count,
            "audited_customer_count": self.audited_customer_count,
            "eligible_cross_split_row_pair_count": (
                self.eligible_cross_split_row_pair_count
            ),
            "near_duplicate_rule_id": self.near_duplicate_rule_id,
        }
        _require_sha256(
            self.audit_input_manifest_sha256,
            "audit_input_manifest_sha256",
        )
        if self.audit_input_manifest_sha256 != _digest(
            _DUPLICATE_AUDIT_INPUT_DOMAIN,
            audit_input,
        ):
            raise RetailPreflightError("DUPLICATE_AUDIT_INPUT_MANIFEST_MISMATCH")
        completion = {
            "audit_input_manifest_sha256": self.audit_input_manifest_sha256,
            "completion_certificate_sha256": self.completion_certificate_sha256,
            "checked_cross_split_row_pair_count": (
                self.checked_cross_split_row_pair_count
            ),
            "complete_roster_checked": self.complete_roster_checked,
            "exact_duplicate_cross_split_lineage_count": (
                self.exact_duplicate_cross_split_lineage_count
            ),
            "near_duplicate_cross_split_lineage_count": (
                self.near_duplicate_cross_split_lineage_count
            ),
            "model_outcome_or_metric_inspected": (
                self.model_outcome_or_metric_inspected
            ),
            "independently_verified": self.independently_verified,
        }
        _require_sha256(
            self.completion_attestation_sha256,
            "completion_attestation_sha256",
        )
        if self.completion_attestation_sha256 != _digest(
            _DUPLICATE_AUDIT_COMPLETION_DOMAIN,
            completion,
        ):
            raise RetailPreflightError(
                "DUPLICATE_AUDIT_COMPLETION_ATTESTATION_MISMATCH"
            )
        _require_sha256(self.receipt_sha256, "duplicate audit receipt_sha256")
        expected = _digest(
            _DUPLICATE_AUDIT_DOMAIN,
            _dataclass_payload(self, ("receipt_sha256",)),
        )
        if self.receipt_sha256 != expected:
            raise RetailPreflightError("DUPLICATE_AUDIT_RECEIPT_DIGEST_MISMATCH")

    @classmethod
    def create(
        cls,
        *,
        snapshot_receipt_sha256: str,
        split_receipt: object,
        audit_id: str,
        audit_implementation_sha256: str,
        completion_certificate_sha256: str,
        checked_cross_split_row_pair_count: int,
        complete_roster_checked: bool,
        exact_duplicate_cross_split_lineage_count: int,
        near_duplicate_cross_split_lineage_count: int,
        near_duplicate_rule_id: str,
        model_outcome_or_metric_inspected: bool,
        independently_verified: bool,
    ) -> "RetailDuplicateAuditReceipt":
        if not _revalidate_exact_dataclass(split_receipt, RetailSplitReceipt):
            raise RetailPreflightError("INVALID_SPLIT_RECEIPT_FOR_DUPLICATE_AUDIT")
        assert type(split_receipt) is RetailSplitReceipt
        train_rows, validation_rows, test_rows = split_receipt.row_counts
        eligible_pair_count = (
            train_rows * validation_rows
            + train_rows * test_rows
            + validation_rows * test_rows
        )
        audit_input = {
            "snapshot_receipt_sha256": snapshot_receipt_sha256,
            "split_receipt_sha256": split_receipt.receipt_sha256,
            "audit_algorithm_id": DUPLICATE_AUDIT_ALGORITHM_ID,
            "audit_implementation_sha256": audit_implementation_sha256,
            "audited_normalized_projection_sha256": (
                split_receipt.normalized_projection_sha256
            ),
            "audited_assignment_manifest_sha256": (
                split_receipt.assignment_manifest_sha256
            ),
            "audited_row_count": split_receipt.row_count,
            "audited_customer_count": split_receipt.customer_count,
            "eligible_cross_split_row_pair_count": eligible_pair_count,
            "near_duplicate_rule_id": near_duplicate_rule_id,
        }
        input_manifest_sha256 = _digest(
            _DUPLICATE_AUDIT_INPUT_DOMAIN,
            audit_input,
        )
        completion = {
            "audit_input_manifest_sha256": input_manifest_sha256,
            "completion_certificate_sha256": completion_certificate_sha256,
            "checked_cross_split_row_pair_count": checked_cross_split_row_pair_count,
            "complete_roster_checked": complete_roster_checked,
            "exact_duplicate_cross_split_lineage_count": (
                exact_duplicate_cross_split_lineage_count
            ),
            "near_duplicate_cross_split_lineage_count": (
                near_duplicate_cross_split_lineage_count
            ),
            "model_outcome_or_metric_inspected": model_outcome_or_metric_inspected,
            "independently_verified": independently_verified,
        }
        payload = {
            "audit_id": audit_id,
            **audit_input,
            "audit_input_manifest_sha256": input_manifest_sha256,
            "completion_certificate_sha256": completion_certificate_sha256,
            "checked_cross_split_row_pair_count": checked_cross_split_row_pair_count,
            "complete_roster_checked": complete_roster_checked,
            "exact_duplicate_cross_split_lineage_count": (
                exact_duplicate_cross_split_lineage_count
            ),
            "near_duplicate_cross_split_lineage_count": (
                near_duplicate_cross_split_lineage_count
            ),
            "model_outcome_or_metric_inspected": model_outcome_or_metric_inspected,
            "independently_verified": independently_verified,
            "completion_attestation_sha256": _digest(
                _DUPLICATE_AUDIT_COMPLETION_DOMAIN,
                completion,
            ),
        }
        return cls(
            **payload,
            receipt_sha256=_digest(_DUPLICATE_AUDIT_DOMAIN, payload),
        )


@dataclass(frozen=True)
class TrainingOnlyViolationCounts:
    raw_format_failures: int
    identity_failures: int
    unknown_or_unbound_event_type_rows: int
    missing_or_invalid_required_value_rows: int
    event_transform_collisions: int
    horizon_violations: int
    cap_or_overflow_violations: int
    row_exclusions: int
    natural_group_exclusions: int
    natural_group_split_overlaps: int
    split_contract_failures: int
    clean_kernel_normalization_failures: int
    observation_subset_failures: int

    def __post_init__(self) -> None:
        if tuple(item.name for item in fields(self)) != ADMISSION_COMPONENTS:
            raise AssertionError("admission component dataclass drift")
        for name in ADMISSION_COMPONENTS:
            _require_exact_int(getattr(self, name), name)

    @classmethod
    def from_mapping(cls, value: object) -> "TrainingOnlyViolationCounts":
        row = _strict_mapping(value, ADMISSION_COMPONENTS, "INVALID_ADMISSION_VECTOR")
        return cls(**dict(row))

    def as_dict(self) -> Dict[str, int]:
        return {name: getattr(self, name) for name in ADMISSION_COMPONENTS}


@dataclass(frozen=True)
class AdmissionReceiptFlags:
    snapshot_hash_verified: bool
    license_access_record_verified: bool
    governance_approval_verified: bool
    complete_split_manifest_verified: bool
    duplicate_and_near_duplicate_audit_verified: bool
    observation_reference_and_support_receipt_verified: bool

    def __post_init__(self) -> None:
        if tuple(item.name for item in fields(self)) != REQUIRED_ADMISSION_RECEIPTS:
            raise AssertionError("admission receipt dataclass drift")
        for name in REQUIRED_ADMISSION_RECEIPTS:
            _require_exact_bool(getattr(self, name), name)

    @classmethod
    def from_mapping(cls, value: object) -> "AdmissionReceiptFlags":
        row = _strict_mapping(
            value, REQUIRED_ADMISSION_RECEIPTS, "INVALID_ADMISSION_RECEIPT_FLAGS"
        )
        return cls(**dict(row))

    def as_dict(self) -> Dict[str, bool]:
        return {name: getattr(self, name) for name in REQUIRED_ADMISSION_RECEIPTS}


def support_route_status(receipt: object) -> str:
    """Return ``UNRESOLVED`` unless an accepted-policy receipt is supplied.

    A supplied receipt is structurally coherent only.  This function does not
    externally authenticate its acquisition justification, proof, code, or
    independent review and therefore does not close F053/F054.
    """

    if receipt is None:
        return "UNRESOLVED"
    if not _revalidate_exact_dataclass(receipt, RetailSupportReceipt):
        raise RetailPreflightError("INVALID_SUPPORT_RECEIPT_TYPE")
    return "ACCEPTED_POLICY_RECEIPT_SUPPLIED_NOT_EXTERNALLY_AUTHENTICATED"


def evaluate_retail_training_admission(
    component_counts: object,
    receipt_flags: object,
    *,
    normalized_rows: object = None,
    allocation: object = None,
    shared_policy: object = None,
    schema_receipt: object = None,
    governance_receipt: object = None,
    snapshot_receipt: object = None,
    split_receipt: object = None,
    support_receipt: object = None,
    duplicate_audit_receipt: object = None,
) -> Dict[str, Any]:
    """Evaluate the exact Retail method-blind training-only admission gate.

    A passing result is only ``ELIGIBLE_FOR_INDEPENDENT_ADMISSION`` over
    caller-supplied receipt objects.  The exact normalized rows and F061
    allocation and an exactly revalidated accepted shared policy are mandatory
    replay evidence.  The integrated path recomputes the shared proposal and
    definition, runtime-checks the adapter contract, requires the native
    allocation to equal its deterministic projection, reruns F060, and checks
    every split-receipt field and self-digest.  It never admits the domain,
    performs external authentication, or accesses a source or dataset.
    """

    if type(component_counts) is not TrainingOnlyViolationCounts:
        raise RetailPreflightError("INVALID_TRAINING_ONLY_VIOLATION_VECTOR_TYPE")
    if type(receipt_flags) is not AdmissionReceiptFlags:
        raise RetailPreflightError("INVALID_ADMISSION_RECEIPT_FLAGS_TYPE")
    if not _revalidate_exact_dataclass(component_counts, TrainingOnlyViolationCounts):
        raise RetailPreflightError("INVALID_TRAINING_ONLY_VIOLATION_VECTOR_STATE")
    if not _revalidate_exact_dataclass(receipt_flags, AdmissionReceiptFlags):
        raise RetailPreflightError("INVALID_ADMISSION_RECEIPT_FLAGS_STATE")
    counts = component_counts.as_dict()
    flags = receipt_flags.as_dict()
    reasons = []
    nonzero = [name for name, value in counts.items() if value != 0]
    if nonzero:
        reasons.append("NONZERO_TRAINING_ONLY_VIOLATIONS")
    false_flags = [name for name, value in flags.items() if not value]
    if false_flags:
        reasons.append("MISSING_OR_UNVERIFIED_REQUIRED_RECEIPTS")

    try:
        _validate_active_retail_split_contract_identity()
    except RetailPreflightError:
        active_split_contract_valid = False
        reasons.append("ACTIVE_RETAIL_SPLIT_CONTRACT_RUNTIME_DRIFT")
    else:
        active_split_contract_valid = True
    shared_provenance_valid = (
        active_split_contract_valid
        and _revalidate_exact_dataclass(
            shared_policy,
            RetailSharedF061Policy,
        )
    )
    if not shared_provenance_valid:
        reasons.append("INTEGRATED_F061_PROVENANCE_MISSING_OR_INVALID")

    expected_types = (
        (schema_receipt, RetailSchemaReceipt, "SCHEMA_RECEIPT_MISSING_OR_INVALID"),
        (
            governance_receipt,
            RetailGovernanceReceipt,
            "GOVERNANCE_RECEIPT_MISSING_OR_INVALID",
        ),
        (
            snapshot_receipt,
            RetailSnapshotReceipt,
            "SNAPSHOT_RECEIPT_MISSING_OR_INVALID",
        ),
        (split_receipt, RetailSplitReceipt, "SPLIT_RECEIPT_MISSING_OR_INVALID"),
        (
            duplicate_audit_receipt,
            RetailDuplicateAuditReceipt,
            "DUPLICATE_AUDIT_RECEIPT_MISSING_OR_INVALID",
        ),
    )
    valid_receipts: Dict[type, bool] = {}
    for value, expected, reason in expected_types:
        valid = _revalidate_exact_dataclass(value, expected)
        valid_receipts[expected] = valid
        if not valid:
            reasons.append(reason)
    if support_receipt is None:
        support_receipt_valid = False
        reasons.append("COMMON_SUPPORT_POLICY_RECEIPT_UNRESOLVED")
    else:
        support_receipt_valid = _revalidate_exact_dataclass(
            support_receipt, RetailSupportReceipt
        )
        if not support_receipt_valid:
            reasons.append("SUPPORT_RECEIPT_MISSING_OR_INVALID")

    all_base_receipts_valid = all(valid_receipts.values())
    if all_base_receipts_valid and support_receipt_valid:
        assert type(schema_receipt) is RetailSchemaReceipt
        assert type(governance_receipt) is RetailGovernanceReceipt
        assert type(snapshot_receipt) is RetailSnapshotReceipt
        assert type(split_receipt) is RetailSplitReceipt
        assert type(support_receipt) is RetailSupportReceipt
        assert type(duplicate_audit_receipt) is RetailDuplicateAuditReceipt
        if (
            snapshot_receipt.schema_receipt_sha256
            != schema_receipt.receipt_sha256
        ):
            reasons.append("SNAPSHOT_SCHEMA_CROSSLINK_MISMATCH")
        if (
            snapshot_receipt.governance_receipt_sha256
            != governance_receipt.receipt_sha256
        ):
            reasons.append("SNAPSHOT_GOVERNANCE_CROSSLINK_MISMATCH")
        if (
            snapshot_receipt.license_access_receipt_sha256
            != governance_receipt.license_access_receipt_sha256
        ):
            reasons.append("LICENSE_ACCESS_CROSSLINK_MISMATCH")
        if split_receipt.snapshot_receipt_sha256 != snapshot_receipt.receipt_sha256:
            reasons.append("SPLIT_SNAPSHOT_CROSSLINK_MISMATCH")
        if (
            split_receipt.normalized_projection_sha256
            != snapshot_receipt.normalized_projection_sha256
        ):
            reasons.append("SPLIT_PROJECTION_CROSSLINK_MISMATCH")
        if (
            split_receipt.row_count
            != snapshot_receipt.normalized_projection_record_count
        ):
            reasons.append("SPLIT_SNAPSHOT_RECORD_COUNT_MISMATCH")
        if shared_provenance_valid:
            assert type(shared_policy) is RetailSharedF061Policy
            if (
                split_receipt.shared_policy_definition_sha256
                != shared_policy.allocation_definition_sha256
                or split_receipt.retail_f061_adapter_id
                != shared_policy.retail_adapter_id
                or split_receipt.retail_f061_adapter_sha256
                != shared_policy.retail_adapter_sha256
            ):
                reasons.append("SPLIT_F061_PROVENANCE_CROSSLINK_MISMATCH")
        if support_receipt.snapshot_receipt_sha256 != snapshot_receipt.receipt_sha256:
            reasons.append("SUPPORT_SNAPSHOT_CROSSLINK_MISMATCH")
        if (
            duplicate_audit_receipt.snapshot_receipt_sha256
            != snapshot_receipt.receipt_sha256
            or duplicate_audit_receipt.split_receipt_sha256
            != split_receipt.receipt_sha256
        ):
            reasons.append("DUPLICATE_AUDIT_CROSSLINK_MISMATCH")
        expected_cross_split_pair_count = (
            split_receipt.row_counts[0] * split_receipt.row_counts[1]
            + split_receipt.row_counts[0] * split_receipt.row_counts[2]
            + split_receipt.row_counts[1] * split_receipt.row_counts[2]
        )
        if (
            duplicate_audit_receipt.audited_normalized_projection_sha256
            != split_receipt.normalized_projection_sha256
            or duplicate_audit_receipt.audited_assignment_manifest_sha256
            != split_receipt.assignment_manifest_sha256
            or duplicate_audit_receipt.audited_row_count != split_receipt.row_count
            or duplicate_audit_receipt.audited_customer_count
            != split_receipt.customer_count
            or duplicate_audit_receipt.eligible_cross_split_row_pair_count
            != expected_cross_split_pair_count
            or duplicate_audit_receipt.checked_cross_split_row_pair_count
            != expected_cross_split_pair_count
        ):
            reasons.append("DUPLICATE_AUDIT_COVERAGE_MISMATCH")
        if not duplicate_audit_receipt.complete_roster_checked:
            reasons.append("DUPLICATE_AUDIT_ROSTER_INCOMPLETE")
        if (
            duplicate_audit_receipt.exact_duplicate_cross_split_lineage_count != 0
            or duplicate_audit_receipt.near_duplicate_cross_split_lineage_count != 0
        ):
            reasons.append("CROSS_SPLIT_DUPLICATE_OR_NEAR_DUPLICATE_LINEAGE")
        if duplicate_audit_receipt.model_outcome_or_metric_inspected:
            reasons.append("DUPLICATE_AUDIT_NOT_METHOD_BLIND")
        if not duplicate_audit_receipt.independently_verified:
            reasons.append("DUPLICATE_AUDIT_NOT_INDEPENDENTLY_VERIFIED")

    split_replay_status = "BLOCKED_BY_INVALID_RECEIPT"
    if normalized_rows is None or allocation is None:
        split_replay_status = "MISSING_OR_INVALID"
        reasons.append("SPLIT_REPLAY_INPUTS_MISSING_OR_INVALID")
    elif (
        type(allocation) is not dict
        or type(allocation.get("mode")) is not str
        or allocation["mode"] != INTEGRATED_F061_MODE
    ):
        split_replay_status = "INTEGRATED_F061_MODE_MISMATCH"
        reasons.append("INTEGRATED_F061_MODE_MISMATCH")
    elif not shared_provenance_valid:
        split_replay_status = "INTEGRATED_F061_PROVENANCE_INVALID"
    elif _canonical_bytes(allocation) != _canonical_bytes(
        shared_policy.retail_allocation()
    ):
        split_replay_status = "RETAIL_F061_ADAPTER_PROJECTION_MISMATCH"
        reasons.append("RETAIL_F061_ADAPTER_PROJECTION_MISMATCH")
    elif (
        valid_receipts[RetailSnapshotReceipt]
        and valid_receipts[RetailSplitReceipt]
    ):
        assert type(snapshot_receipt) is RetailSnapshotReceipt
        assert type(split_receipt) is RetailSplitReceipt
        try:
            replayed_split_receipt = RetailSplitReceipt.create(
                snapshot_receipt_sha256=snapshot_receipt.receipt_sha256,
                normalized_rows=normalized_rows,
                allocation=allocation,
                shared_policy=shared_policy,
                split_manifest_private_locator=(
                    split_receipt.split_manifest_private_locator
                ),
            )
        except (RetailPreflightError, TypeError, ValueError):
            split_replay_status = "MISSING_OR_INVALID"
            reasons.append("SPLIT_REPLAY_INPUTS_MISSING_OR_INVALID")
        else:
            if _dataclass_payload(replayed_split_receipt) != _dataclass_payload(
                split_receipt
            ):
                split_replay_status = "MISMATCH"
                reasons.append("SPLIT_RECEIPT_REPLAY_MISMATCH")
            elif (
                replayed_split_receipt.normalized_projection_sha256
                != snapshot_receipt.normalized_projection_sha256
                or replayed_split_receipt.row_count
                != snapshot_receipt.normalized_projection_record_count
            ):
                split_replay_status = "SNAPSHOT_CROSSLINK_MISMATCH"
                reasons.append("SPLIT_REPLAY_SNAPSHOT_CROSSLINK_MISMATCH")
            else:
                split_replay_status = "MATCHED"

    decision = "ELIGIBLE_FOR_INDEPENDENT_ADMISSION" if not reasons else "NO_GO"
    return {
        "domain_id": DOMAIN_ID,
        "slot_id": SLOT_ID,
        "statistic_id": "MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1",
        "threshold_id": "ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1",
        "maximum_hard_violation_count": max(counts.values()),
        "nonzero_components": nonzero,
        "missing_or_false_receipt_flags": false_flags,
        "split_replay_status": split_replay_status,
        "support_route_status": (
            support_route_status(None)
            if support_receipt is None
            else (
                support_route_status(support_receipt)
                if _revalidate_exact_dataclass(
                    support_receipt, RetailSupportReceipt
                )
                else "INVALID"
            )
        ),
        "reasons": reasons,
        "decision": decision,
        "domain_admitted": False,
        "independent_admission_required": True,
        "external_authentication_performed": False,
        "source_or_data_access_performed": False,
    }


__all__ = (
    "ACTIVE_RETAIL_SPLIT_CONTRACT_ID",
    "ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256",
    "ADMISSION_COMPONENTS",
    "AdmissionReceiptFlags",
    "COMMON_SUPPORT_POLICY_ID",
    "DOMAIN_ID",
    "DUPLICATE_AUDIT_ALGORITHM_ID",
    "F060_ASSIGNMENT_SCHEMA",
    "F060_RULE_ID",
    "F061_ALLOCATION_SCHEMA",
    "HISTORICAL_RETAIL_SPLIT_DESIGN_ID",
    "HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256",
    "INTEGRATED_F061_MODE",
    "LEGACY_MISBOUND_F105_SEMANTIC_SHA256",
    "OBSERVATION_KERNEL_ID",
    "REQUIRED_ADMISSION_RECEIPTS",
    "RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS",
    "RETAIL_F061_ADAPTER_ID",
    "RETAIL_F061_ADAPTER_SHA256",
    "RETAIL_RAW_FIELDS",
    "RetailDuplicateAuditReceipt",
    "RetailGovernanceReceipt",
    "RetailPreflightError",
    "RetailSchemaReceipt",
    "RetailSharedF061Policy",
    "RetailSnapshotReceipt",
    "RetailSplitReceipt",
    "RetailSupportReceipt",
    "SLOT_ID",
    "SHARED_F061_POLICY_SCHEMA",
    "SHARED_F061_HAMILTON_ROUNDING_RULE_ID",
    "SPLITS",
    "TrainingOnlyViolationCounts",
    "active_retail_split_contract_record",
    "active_retail_split_contract_sha256",
    "evaluate_retail_training_admission",
    "f061_allocation_proposal_sha256",
    "resolve_f061_allocation",
    "retail_f061_adapter_record",
    "retail_f061_adapter_sha256",
    "split_retail_source_civil_rows",
    "support_route_status",
)
