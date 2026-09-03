"""Additive preservation-first F061 proposal and exact-count guards.

This module leaves the independently accepted activation and domain modules
unchanged.  It narrows their generic Hamilton seams to one proposed shared
policy and adds the exact-count compatibility condition required by the later
accepted F111/F134 roster decisions.

The proposal is *not* an independent power review.  Nothing here can create a
review receipt, accept the proposal, close F061, observe a dataset, or perform
contact, acquisition, splitting, training, inference, or scientific work.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Tuple

from heterodiff.data import online_retail_ii_admission_preflight as retail
from heterodiff.data import physionet_2012_admission_preflight as physionet
from heterodiff.data import two_domain_offline_precontact_activation as activation


SCHEMA_VERSION = "heterodiff-two-domain-f061-preservation-first-successor-v1"
PACKAGE_KIND = "ADDITIVE_F061_PROPOSAL_AND_EXACT_COUNT_COMPATIBILITY_GUARD"
STATE = "F061_PROPOSAL_FROZEN_AWAITING_SEPARATE_INDEPENDENT_POWER_REVIEW"
F061_FIELD_STATUS = "OPEN"

SPLIT_NAMES = ("TRAIN", "VALIDATION", "TEST")
ALLOCATION_ID = (
    "TWO_DOMAIN_F061_HAMILTON_70_15_15_EXACT_128_VALIDATION_TEST_V1"
)
MODE = "EXACT_PROPORTIONS_HAMILTON"
VALUES = (70, 15, 15)
DENOMINATOR_IS_NULL = False
DENOMINATOR = 100
MINIMUM_COUNTS = (1, 128, 128)
ROUNDING_RULE_ID = (
    "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
)
POWER_REQUIREMENT_ID = (
    "B07_F134_EXACT_128_VALIDATION_AND_TEST_GROUPS_NO_EXCLUSION_V1"
)
PROPOSAL_DOMAIN = b"heterodiff/two-domain-f061-shared-policy-proposal/v1\0"
PROPOSAL_SHA256 = (
    "cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679"
)

REQUIRED_VALIDATION_COUNT = 128
REQUIRED_TEST_COUNT = 128
ADMISSIBLE_NATURAL_GROUP_TOTALS = (852, 853, 854, 855)
ADMISSIBLE_TOTAL_COUNT_PAIRS = (
    (852, (596, 128, 128)),
    (853, (597, 128, 128)),
    (854, (598, 128, 128)),
    (855, (599, 128, 128)),
)
TERMINAL_NO_GO_CODE = (
    "F061_EXACT_128_VALIDATION_TEST_COMPATIBILITY_TERMINAL_NO_GO"
)
PHYSIONET_FUTURE_REVIEW_STATE = (
    "AWAITING_SEPARATE_EXTERNAL_PHYSIONET_EXACT_COUNT_REVIEW"
)
GUARD_CONTRACT_SCHEMA = (
    "heterodiff-two-domain-f061-exact-count-guard-contract-v1"
)
GUARD_CONTRACT_DOMAIN = (
    b"heterodiff/two-domain-f061-exact-count-guard-contract/v1\0"
)
GUARD_CONTRACT_SHA256 = (
    "98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef"
)
GUARDED_REVIEW_SCHEMA = (
    "heterodiff-two-domain-f061-guarded-power-review-receipt-v1"
)
GUARDED_REVIEW_SCOPE = (
    "SHARED_F061_POWER_AND_EXACT_COUNT_GUARD_ACCEPTANCE"
)
REVIEWER_ATTESTATION_DOMAIN = (
    b"heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1\0"
)
REVIEWER_ATTESTATION_DOMAIN_ASCII = (
    "heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1"
)
SUCCESSOR_SOURCE_PATH = (
    "src/heterodiff/data/two_domain_f061_preservation_first_successor.py"
)
SUCCESSOR_HUMAN_PATH = "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md"
SUCCESSOR_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f061_preservation_first_allocation_proposal_v1.json"
)
SOLE_SUPPORTED_ENTRYPOINTS = (
    "project_reviewed_shared_policy_to_retail",
    "resolve_reviewed_retail_policy",
    "project_reviewed_shared_policy_to_physionet_review_candidate",
)

_PROPOSAL_KEYS = (
    "schema_version",
    "allocation_id",
    "mode",
    "values",
    "denominator_is_null",
    "denominator",
    "minimum_counts",
    "rounding_rule_id",
    "power_requirement_id",
)
_GUARDED_REVIEW_KEYS = (
    "schema_version",
    "review_scope",
    "review_kind",
    "decision",
    "accepted",
    "independent_reviewer_principal_id",
    "independent_reviewer_attestation_sha256",
    "shared_policy_proposal_sha256",
    "exact_count_guard_contract_sha256",
    "successor_source_path",
    "successor_source_raw_sha256",
    "successor_human_path",
    "successor_human_raw_sha256",
    "successor_machine_path",
    "successor_machine_raw_sha256",
    "successor_machine_record_sha256",
    "successor_package_aggregate_sha256",
    "source_and_package_hashes_reopened_before_decision",
    "sole_supported_projection_resolution_entrypoints",
    "direct_generic_predecessor_entrypoints_supported",
    "reviewer_independence_and_conflict_checked",
    "institutional_operational_or_governance_approval",
    "reviewer_identity_externally_authenticated",
)


class F061SuccessorError(ValueError):
    """Fail-closed malformed, incompatible, or overclaimed successor input."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _exact_positive_int(value: Any, code: str) -> int:
    if type(value) is not int or value < 1:
        raise F061SuccessorError(code)
    return value


def _exact_count_triple(value: Any, code: str) -> Tuple[int, int, int]:
    if type(value) is not tuple or len(value) != 3:
        raise F061SuccessorError(code)
    if any(type(item) is not int or item < 1 for item in value):
        raise F061SuccessorError(code)
    return value


def _exact_ascii_token(value: Any, code: str) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > 256
        or value != value.strip()
        or not value.isascii()
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
    ):
        raise F061SuccessorError(code)
    return value


def recognized_proposal() -> Dict[str, Any]:
    """Return the sole proposed shared F061 policy, without review metadata."""

    return {
        "schema_version": activation.F061_ALLOCATION_SCHEMA,
        "allocation_id": ALLOCATION_ID,
        "mode": MODE,
        "values": VALUES,
        "denominator_is_null": DENOMINATOR_IS_NULL,
        "denominator": DENOMINATOR,
        "minimum_counts": MINIMUM_COUNTS,
        "rounding_rule_id": ROUNDING_RULE_ID,
        "power_requirement_id": POWER_REQUIREMENT_ID,
    }


def validate_recognized_proposal(value: Any) -> Dict[str, Any]:
    """Require the exact proposal carrier and return a defensive copy."""

    if type(value) is not dict or set(value) != set(_PROPOSAL_KEYS):
        raise F061SuccessorError("F061_PROPOSAL_SCHEMA_NONCANONICAL")
    expected = recognized_proposal()
    for key in _PROPOSAL_KEYS:
        observed = value[key]
        wanted = expected[key]
        if type(observed) is not type(wanted) or observed != wanted:
            raise F061SuccessorError("F061_PROPOSAL_DRIFT:" + key)
    return dict(expected)


def recognized_proposal_sha256(value: Any) -> str:
    """Recompute the accepted-core proposal codec for the exact proposal."""

    proposal = validate_recognized_proposal(value)
    observed = hashlib.sha256(PROPOSAL_DOMAIN + _canonical_bytes(proposal)).hexdigest()
    if observed != PROPOSAL_SHA256:
        raise F061SuccessorError("F061_PROPOSAL_KNOWN_ANSWER_MISMATCH")
    return observed


def exact_count_guard_contract() -> Dict[str, Any]:
    """Return the semantic guard an eventual review must accept and bind."""

    return {
        "schema_version": GUARD_CONTRACT_SCHEMA,
        "shared_policy_proposal_sha256": PROPOSAL_SHA256,
        "split_names": SPLIT_NAMES,
        "values": VALUES,
        "denominator": DENOMINATOR,
        "minimum_counts": MINIMUM_COUNTS,
        "required_exact_counts": {
            "VALIDATION": REQUIRED_VALIDATION_COUNT,
            "TEST": REQUIRED_TEST_COUNT,
        },
        "admissible_natural_group_totals": ADMISSIBLE_NATURAL_GROUP_TOTALS,
        "admissible_total_count_pairs": ADMISSIBLE_TOTAL_COUNT_PAIRS,
        "all_natural_groups_must_be_allocated": True,
        "exclusion_topup_retry_resplit_or_proportion_change_permitted": False,
        "larger_than_128_validation_or_test_substitution_permitted": False,
        "terminal_no_go_code": TERMINAL_NO_GO_CODE,
        "sole_supported_projection_resolution_entrypoints": (
            SOLE_SUPPORTED_ENTRYPOINTS
        ),
        "direct_generic_predecessor_projection_or_resolution_supported_for_this_policy": (
            False
        ),
        "retail_temporal_feasibility_claimed_by_count_resolution": False,
        "physionet_resolved_counts_require_separate_external_review": True,
        "guarded_review_receipt_carrier": (
            "CANONICAL_DUPLICATE_FREE_ASCII_JSON_NO_TERMINAL_LF"
        ),
        "reviewer_attestation_domain_ascii": REVIEWER_ATTESTATION_DOMAIN_ASCII,
        "reviewer_attestation_domain_suffix_hex": "00",
        "reviewer_attestation_preimage": (
            "ALL_EXACT_RECEIPT_FIELDS_EXCLUDING_"
            "INDEPENDENT_REVIEWER_ATTESTATION_SHA256"
        ),
        "reviewer_attestation_is_identity_signature": False,
        "independent_custody_reopens_actual_candidate_bytes": True,
        "source_self_pins_own_raw_sha256": False,
    }


def exact_count_guard_contract_sha256() -> str:
    observed = hashlib.sha256(
        GUARD_CONTRACT_DOMAIN + _canonical_bytes(exact_count_guard_contract())
    ).hexdigest()
    if observed != GUARD_CONTRACT_SHA256:
        raise F061SuccessorError("F061_EXACT_COUNT_GUARD_KNOWN_ANSWER_MISMATCH")
    return observed


def _reject_duplicate_pairs(pairs: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise F061SuccessorError("F061_GUARDED_REVIEW_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reviewer_attestation_sha256(value: Dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("independent_reviewer_attestation_sha256", None)
    return hashlib.sha256(
        REVIEWER_ATTESTATION_DOMAIN + _canonical_bytes(payload)
    ).hexdigest()


def _validate_guarded_power_review_mapping(value: Any) -> Dict[str, Any]:
    if type(value) is not dict or set(value) != set(_GUARDED_REVIEW_KEYS):
        raise F061SuccessorError("F061_GUARDED_REVIEW_RECEIPT_SCHEMA_NONCANONICAL")
    exact_strings = {
        "schema_version": GUARDED_REVIEW_SCHEMA,
        "review_scope": GUARDED_REVIEW_SCOPE,
        "review_kind": "INDEPENDENT_TECHNICAL_STATISTICAL_POLICY_REVIEW",
        "decision": "ACCEPT_GUARDED_SHARED_POLICY",
        "shared_policy_proposal_sha256": PROPOSAL_SHA256,
        "exact_count_guard_contract_sha256": GUARD_CONTRACT_SHA256,
        "successor_source_path": SUCCESSOR_SOURCE_PATH,
        "successor_human_path": SUCCESSOR_HUMAN_PATH,
        "successor_machine_path": SUCCESSOR_MACHINE_PATH,
    }
    for key, expected in exact_strings.items():
        if type(value[key]) is not str or value[key] != expected:
            raise F061SuccessorError("F061_GUARDED_REVIEW_DRIFT:" + key)
    if value["accepted"] is not True:
        raise F061SuccessorError("F061_GUARDED_REVIEW_NOT_ACCEPTED")
    _exact_ascii_token(
        value["independent_reviewer_principal_id"],
        "F061_GUARDED_REVIEWER_PRINCIPAL_NONCANONICAL",
    )
    for key in (
        "independent_reviewer_attestation_sha256",
        "successor_source_raw_sha256",
        "successor_human_raw_sha256",
        "successor_machine_raw_sha256",
        "successor_machine_record_sha256",
        "successor_package_aggregate_sha256",
    ):
        if not _is_sha256(value[key]):
            raise F061SuccessorError("F061_GUARDED_REVIEW_INVALID_SHA256:" + key)
    if value["source_and_package_hashes_reopened_before_decision"] is not True:
        raise F061SuccessorError("F061_GUARDED_REVIEW_CUSTODY_NOT_REOPENED")
    if value["reviewer_independence_and_conflict_checked"] is not True:
        raise F061SuccessorError("F061_GUARDED_REVIEW_INDEPENDENCE_UNRESOLVED")
    if value["institutional_operational_or_governance_approval"] is not False:
        raise F061SuccessorError("F061_GUARDED_REVIEW_APPROVAL_SMUGGLED")
    if value["reviewer_identity_externally_authenticated"] is not False:
        raise F061SuccessorError("F061_GUARDED_REVIEW_IDENTITY_OVERCLAIM")
    if (
        type(value["sole_supported_projection_resolution_entrypoints"])
        is not list
        or value["sole_supported_projection_resolution_entrypoints"]
        != list(SOLE_SUPPORTED_ENTRYPOINTS)
    ):
        raise F061SuccessorError("F061_GUARDED_REVIEW_ENTRYPOINT_ROSTER_DRIFT")
    if value["direct_generic_predecessor_entrypoints_supported"] is not False:
        raise F061SuccessorError("F061_GENERIC_PREDECESSOR_BYPASS_ADVERTISED")
    if value["independent_reviewer_attestation_sha256"] != (
        _reviewer_attestation_sha256(value)
    ):
        raise F061SuccessorError("F061_GUARDED_REVIEW_ATTESTATION_DIGEST_MISMATCH")
    return dict(value)


def validate_guarded_power_review_receipt(value: Any) -> Dict[str, Any]:
    """Validate exact raw bytes of one future guard-binding review receipt.

    The receipt is canonical ASCII JSON without a terminal line feed.  Its raw
    SHA-256 is the value that must occupy the accepted core's
    ``f061_power_review_receipt_sha256`` slot.  Independent custody validation
    must separately reopen the listed package bytes and authenticate reviewer
    separation; this pure structural checker makes neither claim itself.  This
    is a technical/statistical review, not institutional or operational approval.
    """

    if type(value) is not bytes:
        raise F061SuccessorError("F061_GUARDED_REVIEW_RAW_BYTES_REQUIRED")
    if not value or len(value) > 65536:
        raise F061SuccessorError("F061_GUARDED_REVIEW_RAW_BYTE_COUNT_INVALID")
    if value.endswith(b"\n"):
        raise F061SuccessorError("F061_GUARDED_REVIEW_TERMINAL_LF_FORBIDDEN")
    try:
        text = value.decode("ascii")
    except UnicodeDecodeError as error:
        raise F061SuccessorError("F061_GUARDED_REVIEW_NON_ASCII") from error
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                F061SuccessorError("F061_GUARDED_REVIEW_FORBIDDEN_JSON_CONSTANT")
            ),
        )
    except F061SuccessorError:
        raise
    except (json.JSONDecodeError, ValueError) as error:
        raise F061SuccessorError("F061_GUARDED_REVIEW_JSON_MALFORMED") from error
    checked = _validate_guarded_power_review_mapping(decoded)
    if value != _canonical_bytes(checked):
        raise F061SuccessorError("F061_GUARDED_REVIEW_NONCANONICAL_BYTES")
    return checked


def guarded_power_review_receipt_sha256(value: Any) -> str:
    """Return the raw SHA-256 of one validated canonical future receipt."""

    validate_guarded_power_review_receipt(value)
    return hashlib.sha256(value).hexdigest()


def _validate_guarded_review_for_expected_sha256(
    guarded_review_receipt: Any,
    expected_receipt_sha256: Any,
) -> Dict[str, Any]:
    if guarded_review_receipt is None:
        raise F061SuccessorError("F061_GUARDED_REVIEW_RECEIPT_REQUIRED")
    if not _is_sha256(expected_receipt_sha256):
        raise F061SuccessorError("F061_INDEPENDENT_POWER_REVIEW_RECEIPT_ABSENT")
    checked = validate_guarded_power_review_receipt(guarded_review_receipt)
    observed = guarded_power_review_receipt_sha256(guarded_review_receipt)
    if observed != expected_receipt_sha256:
        raise F061SuccessorError("F061_GUARDED_REVIEW_RECEIPT_BINDING_MISMATCH")
    return checked


def hamilton_counts(natural_group_count: Any) -> Tuple[int, int, int]:
    """Apply the frozen 70/15/15 Hamilton rule with TRAIN-first tie order."""

    count = _exact_positive_int(
        natural_group_count,
        "F061_NATURAL_GROUP_COUNT_NONCANONICAL",
    )
    floors = [count * numerator // DENOMINATOR for numerator in VALUES]
    remainders = [count * numerator % DENOMINATOR for numerator in VALUES]
    remaining = count - sum(floors)
    order = sorted(range(3), key=lambda index: (-remainders[index], index))
    for index in order[:remaining]:
        floors[index] += 1
    return (floors[0], floors[1], floors[2])


def exact_count_compatibility_predicate(
    natural_group_count: Any,
    resolved_counts: Any,
) -> bool:
    """Recognize exactly 128 validation and 128 test groups, or fail closed.

    With the frozen all-group 70/15/15 Hamilton rule, this is true exactly for
    total natural-group counts 852, 853, 854, and 855.  Every other total is a
    terminal no-go; the function never proposes exclusion, top-up, retry,
    resplit, proportion changes, or a larger-than-128 substitute roster.
    """

    count = _exact_positive_int(
        natural_group_count,
        "F061_NATURAL_GROUP_COUNT_NONCANONICAL",
    )
    if count not in ADMISSIBLE_NATURAL_GROUP_TOTALS:
        raise F061SuccessorError(TERMINAL_NO_GO_CODE)
    counts = _exact_count_triple(
        resolved_counts,
        "F061_RESOLVED_COUNTS_NONCANONICAL",
    )
    expected = hamilton_counts(count)
    if counts != expected or sum(counts) != count:
        raise F061SuccessorError("F061_RESOLVED_COUNTS_HAMILTON_MISMATCH")
    if (
        counts[1] != REQUIRED_VALIDATION_COUNT
        or counts[2] != REQUIRED_TEST_COUNT
    ):
        raise F061SuccessorError(TERMINAL_NO_GO_CODE)
    lookup = dict(ADMISSIBLE_TOTAL_COUNT_PAIRS)
    if lookup.get(count) != counts:
        raise F061SuccessorError("F061_ADMISSIBLE_COUNT_TABLE_MISMATCH")
    return True


def _proposal_from_bindings(
    bindings: activation.OfflineDefinitionBindings,
) -> Dict[str, Any]:
    if type(bindings) is not activation.OfflineDefinitionBindings:
        raise F061SuccessorError("F061_SHARED_BINDINGS_WRONG_TYPE")
    return {
        "schema_version": bindings.f061_allocation_schema,
        "allocation_id": bindings.f061_allocation_id,
        "mode": bindings.f061_mode,
        "values": bindings.f061_values,
        "denominator_is_null": bindings.f061_denominator_is_null,
        "denominator": bindings.f061_denominator,
        "minimum_counts": bindings.f061_minimum_counts,
        "rounding_rule_id": bindings.f061_rounding_rule_id,
        "power_requirement_id": bindings.f061_power_requirement_id,
    }


def validate_reviewed_shared_policy_bindings(
    bindings: Any,
    guarded_review_receipt: Any = None,
) -> activation.OfflineDefinitionBindings:
    """Validate a future independently accepted instance of this proposal.

    This function can validate supplied review lineage but cannot mint it.  A
    proposal-only record with null review slots necessarily fails here.
    """

    if type(bindings) is not activation.OfflineDefinitionBindings:
        raise F061SuccessorError("F061_SHARED_BINDINGS_WRONG_TYPE")
    proposal = _proposal_from_bindings(bindings)
    validate_recognized_proposal(proposal)
    if bindings.f061_allocation_proposal_sha256 != PROPOSAL_SHA256:
        raise F061SuccessorError("F061_SHARED_PROPOSAL_BINDING_MISMATCH")
    if not _is_sha256(bindings.f061_power_review_receipt_sha256):
        raise F061SuccessorError("F061_INDEPENDENT_POWER_REVIEW_RECEIPT_ABSENT")
    _validate_guarded_review_for_expected_sha256(
        guarded_review_receipt,
        bindings.f061_power_review_receipt_sha256,
    )
    if bindings.f061_power_review_accepted is not True:
        raise F061SuccessorError("F061_INDEPENDENT_POWER_REVIEW_NOT_ACCEPTED")
    if not _is_sha256(bindings.f061_allocation_definition_sha256):
        raise F061SuccessorError("F061_SHARED_DEFINITION_BINDING_ABSENT")
    try:
        observed_proposal = activation.f061_allocation_proposal_sha256(bindings)
        observed_definition = activation.f061_allocation_definition_sha256(bindings)
    except (activation.OfflineActivationError, TypeError, ValueError) as error:
        raise F061SuccessorError("F061_ACCEPTED_CORE_REVALIDATION_FAILED") from error
    if observed_proposal != PROPOSAL_SHA256:
        raise F061SuccessorError("F061_ACCEPTED_CORE_PROPOSAL_DIGEST_MISMATCH")
    if observed_definition != bindings.f061_allocation_definition_sha256:
        raise F061SuccessorError("F061_ACCEPTED_CORE_DEFINITION_DIGEST_MISMATCH")
    return bindings


def project_reviewed_shared_policy_to_retail(
    bindings: Any,
    guarded_review_receipt: Any = None,
) -> Dict[str, Any]:
    """Wrap the accepted core's Retail projection for only this exact policy."""

    checked = validate_reviewed_shared_policy_bindings(
        bindings,
        guarded_review_receipt,
    )
    try:
        projected = activation.project_shared_policy_to_retail_f061_proposal(
            checked
        )
    except (activation.OfflineActivationError, TypeError, ValueError) as error:
        raise F061SuccessorError("F061_ACCEPTED_RETAIL_PROJECTION_FAILED") from error
    expected = {
        "schema_version": retail.F061_ALLOCATION_SCHEMA,
        "allocation_id": ALLOCATION_ID,
        "mode": MODE,
        "values": dict(zip(SPLIT_NAMES, VALUES)),
        "denominator": DENOMINATOR,
        "minimum_counts": dict(zip(SPLIT_NAMES, MINIMUM_COUNTS)),
        "power_requirement_id": POWER_REQUIREMENT_ID,
    }
    if type(projected) is not dict or projected != expected:
        raise F061SuccessorError("F061_ACCEPTED_RETAIL_PROJECTION_DRIFT")
    return dict(projected)


def resolve_reviewed_retail_policy(
    shared_policy: Any,
    customer_count: Any,
    guarded_review_receipt: Any = None,
) -> Dict[str, Any]:
    """Resolve Retail only when its accepted shared policy and counts match.

    This validates allocation counts only.  It does not claim that an exact
    Retail temporal boundary pair exists or that a snapshot/split is admitted.
    """

    if type(shared_policy) is not retail.RetailSharedF061Policy:
        raise F061SuccessorError("F061_RETAIL_SHARED_POLICY_WRONG_TYPE")
    proposal = {
        "schema_version": shared_policy.schema_version,
        "allocation_id": shared_policy.allocation_id,
        "mode": shared_policy.mode,
        "values": shared_policy.values,
        "denominator_is_null": shared_policy.denominator_is_null,
        "denominator": shared_policy.denominator,
        "minimum_counts": shared_policy.minimum_counts,
        "rounding_rule_id": shared_policy.rounding_rule_id,
        "power_requirement_id": shared_policy.power_requirement_id,
    }
    validate_recognized_proposal(proposal)
    if shared_policy.allocation_proposal_sha256 != PROPOSAL_SHA256:
        raise F061SuccessorError("F061_RETAIL_SHARED_PROPOSAL_BINDING_MISMATCH")
    if shared_policy.power_review_accepted is not True:
        raise F061SuccessorError("F061_RETAIL_SHARED_REVIEW_NOT_ACCEPTED")
    _validate_guarded_review_for_expected_sha256(
        guarded_review_receipt,
        shared_policy.power_review_receipt_sha256,
    )
    count = _exact_positive_int(
        customer_count,
        "F061_NATURAL_GROUP_COUNT_NONCANONICAL",
    )
    exact_count_compatibility_predicate(count, hamilton_counts(count))
    try:
        allocation = shared_policy.retail_allocation()
        resolution = retail.resolve_f061_allocation(allocation, count)
    except (retail.RetailPreflightError, TypeError, ValueError) as error:
        raise F061SuccessorError("F061_RETAIL_RESOLUTION_FAILED") from error
    counts_mapping = resolution.get("resolved_customer_counts")
    if type(counts_mapping) is not dict or set(counts_mapping) != set(SPLIT_NAMES):
        raise F061SuccessorError("F061_RETAIL_RESOLVED_COUNTS_SCHEMA_DRIFT")
    counts = tuple(counts_mapping[name] for name in SPLIT_NAMES)
    exact_count_compatibility_predicate(count, counts)
    return dict(resolution)


def project_reviewed_shared_policy_to_physionet_review_candidate(
    bindings: Any,
    natural_group_count: Any,
    guarded_review_receipt: Any = None,
) -> Dict[str, Any]:
    """Build a fail-closed future PhysioNet exact-count review candidate.

    The returned exact native proposal still has null external-review slots.
    The accepted shared review is lineage only and cannot accept the later
    snapshot-resolved counts.
    """

    checked = validate_reviewed_shared_policy_bindings(
        bindings,
        guarded_review_receipt,
    )
    count = _exact_positive_int(
        natural_group_count,
        "F061_NATURAL_GROUP_COUNT_NONCANONICAL",
    )
    exact_count_compatibility_predicate(count, hamilton_counts(count))
    try:
        projected = activation.project_shared_policy_to_physionet_f061_proposal(
            checked,
            count,
        )
    except (activation.OfflineActivationError, TypeError, ValueError) as error:
        raise F061SuccessorError("F061_ACCEPTED_PHYSIONET_PROJECTION_FAILED") from error
    counts = projected.get("counts")
    exact_count_compatibility_predicate(count, counts)
    if (
        projected.get("numerators") != VALUES
        or projected.get("denominator") != DENOMINATOR
        or projected.get("minimum_counts") != MINIMUM_COUNTS
        or projected.get("rounding_rule_id") != ROUNDING_RULE_ID
    ):
        raise F061SuccessorError("F061_ACCEPTED_PHYSIONET_PROJECTION_DRIFT")
    try:
        native_proposal_sha256 = physionet.f061_allocation_proposal_sha256(
            patient_count=count,
            numerators=VALUES,
            denominator=DENOMINATOR,
            counts=counts,
            minimum_counts=MINIMUM_COUNTS,
            rounding_rule_id=ROUNDING_RULE_ID,
            shared_policy_allocation_id=ALLOCATION_ID,
            shared_policy_values=VALUES,
            shared_policy_denominator=DENOMINATOR,
            shared_policy_minimum_counts=MINIMUM_COUNTS,
            shared_policy_rounding_rule_id=ROUNDING_RULE_ID,
            shared_policy_power_requirement_id=POWER_REQUIREMENT_ID,
            shared_policy_proposal_sha256=PROPOSAL_SHA256,
            shared_policy_review_receipt_sha256=(
                checked.f061_power_review_receipt_sha256
            ),
            shared_policy_review_accepted=True,
            shared_policy_definition_sha256=(
                checked.f061_allocation_definition_sha256
            ),
            physionet_adapter_id=activation.PHYSIONET_F061_ADAPTER_ID,
            physionet_adapter_sha256=activation.PHYSIONET_F061_ADAPTER_SHA256,
        )
    except (physionet.AdmissionPreflightError, TypeError, ValueError) as error:
        raise F061SuccessorError("F061_PHYSIONET_NATIVE_PROPOSAL_FAILED") from error
    return {
        "schema_version": SCHEMA_VERSION,
        "state": PHYSIONET_FUTURE_REVIEW_STATE,
        "patient_count": count,
        "numerators": VALUES,
        "denominator": DENOMINATOR,
        "counts": counts,
        "minimum_counts": MINIMUM_COUNTS,
        "rounding_rule_id": ROUNDING_RULE_ID,
        "shared_policy_allocation_id": ALLOCATION_ID,
        "shared_policy_power_requirement_id": POWER_REQUIREMENT_ID,
        "shared_policy_proposal_sha256": PROPOSAL_SHA256,
        "shared_policy_review_receipt_sha256": (
            checked.f061_power_review_receipt_sha256
        ),
        "shared_policy_definition_sha256": (
            checked.f061_allocation_definition_sha256
        ),
        "physionet_native_proposal_sha256": native_proposal_sha256,
        "physionet_exact_count_review_receipt_sha256": None,
        "physionet_exact_count_review_accepted": None,
        "shared_review_accepts_resolved_counts": False,
        "f061_closed": False,
    }


def proposal_only_status() -> Dict[str, Any]:
    """Expose the exact proposal with deliberately null acceptance slots."""

    return {
        "schema_version": SCHEMA_VERSION,
        "package_kind": PACKAGE_KIND,
        "state": STATE,
        "f061_field_status": F061_FIELD_STATUS,
        "proposal": recognized_proposal(),
        "allocation_proposal_sha256": PROPOSAL_SHA256,
        "exact_count_guard_contract": exact_count_guard_contract(),
        "exact_count_guard_contract_sha256": GUARD_CONTRACT_SHA256,
        "future_power_review_must_byte_bind_successor_package": True,
        "sole_supported_projection_resolution_entrypoints": (
            SOLE_SUPPORTED_ENTRYPOINTS
        ),
        "direct_generic_predecessor_entrypoints_supported": False,
        "power_review_receipt_sha256": None,
        "power_review_accepted": None,
        "allocation_definition_sha256": None,
        "independent_review_created_by_module": False,
        "tracker_or_evidence_ledger_edited": False,
    }


__all__ = [
    "ADMISSIBLE_NATURAL_GROUP_TOTALS",
    "ADMISSIBLE_TOTAL_COUNT_PAIRS",
    "ALLOCATION_ID",
    "DENOMINATOR",
    "DENOMINATOR_IS_NULL",
    "F061SuccessorError",
    "F061_FIELD_STATUS",
    "GUARDED_REVIEW_SCHEMA",
    "GUARDED_REVIEW_SCOPE",
    "GUARD_CONTRACT_SCHEMA",
    "GUARD_CONTRACT_SHA256",
    "MINIMUM_COUNTS",
    "MODE",
    "PACKAGE_KIND",
    "PHYSIONET_FUTURE_REVIEW_STATE",
    "POWER_REQUIREMENT_ID",
    "PROPOSAL_SHA256",
    "ROUNDING_RULE_ID",
    "REVIEWER_ATTESTATION_DOMAIN_ASCII",
    "SCHEMA_VERSION",
    "SPLIT_NAMES",
    "STATE",
    "SOLE_SUPPORTED_ENTRYPOINTS",
    "TERMINAL_NO_GO_CODE",
    "VALUES",
    "exact_count_compatibility_predicate",
    "exact_count_guard_contract",
    "exact_count_guard_contract_sha256",
    "guarded_power_review_receipt_sha256",
    "hamilton_counts",
    "project_reviewed_shared_policy_to_physionet_review_candidate",
    "project_reviewed_shared_policy_to_retail",
    "proposal_only_status",
    "recognized_proposal",
    "recognized_proposal_sha256",
    "resolve_reviewed_retail_policy",
    "validate_recognized_proposal",
    "validate_guarded_power_review_receipt",
    "validate_reviewed_shared_policy_bindings",
]
