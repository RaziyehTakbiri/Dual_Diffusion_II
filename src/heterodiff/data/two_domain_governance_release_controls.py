"""Pure controls for the two-domain observation, admission, and release plans.

This module deliberately performs no acquisition, parsing, splitting, training,
network access, persistence, release, or scientific execution.  It gives future
runners small fail-closed predicates for contracts frozen by the companion
governance package.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional, Sequence, Tuple


PHYSIONET_DOMAIN = "physionet-challenge-2012"
RETAIL_DOMAIN = "online-retail-ii"
DOMAINS = (PHYSIONET_DOMAIN, RETAIL_DOMAIN)

OBSERVATION_KERNEL_ID = "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"
ADMISSION_STATISTIC_ID = "MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1"
ADMISSION_THRESHOLD_ID = "ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1"

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

RELEASE_CLASSES = (
    "PUBLIC_PROJECT_CODE",
    "PUBLIC_CONFIG_OR_SCHEMA",
    "PUBLIC_AGGREGATE_RESULT",
    "PUBLIC_MODEL_CANDIDATE",
    "INTERNAL_RESTRICTED",
    "NEVER_RELEASE",
)

PUBLIC_CLASSES = frozenset(RELEASE_CLASSES[:4])
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SAFE_PATH_PART_RE = re.compile(r"[A-Za-z0-9._-]+\Z")


class ContractError(ValueError):
    """Raised when an offline control receives a malformed contract input."""


def _exact_int(value: object, *, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ContractError(f"{name} must be an exact integer >= {minimum}")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise ContractError(f"{name} must be an exact Boolean")
    return value


def _exact_mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise ContractError(f"{name} must be an exact mapping")
    return value


def _exact_sequence(value: object, *, name: str) -> Sequence[Any]:
    if type(value) is not list:
        raise ContractError(f"{name} must be an exact list")
    return value


def half_thinning_mass_exponent(
    source_occurrence_ordinals: object,
    observed_occurrence_ordinals: object,
) -> Optional[int]:
    """Return ``n`` for mass ``2**(-n)``, or ``None`` off kernel support.

    Occurrence ordinals make duplicate-valued and simultaneous events distinct.
    Both arguments must be strictly increasing exact nonnegative integer lists.
    The observed list must be a subset of the source list.  The function does
    not sample and consumes no entropy.
    """

    source = _exact_sequence(source_occurrence_ordinals, name="source ordinals")
    observed = _exact_sequence(
        observed_occurrence_ordinals, name="observed ordinals"
    )
    for label, values in (("source", source), ("observed", observed)):
        previous = -1
        for index, value in enumerate(values):
            current = _exact_int(value, name=f"{label}[{index}]")
            if current <= previous:
                raise ContractError(f"{label} ordinals must be strictly increasing")
            previous = current
    if not set(observed).issubset(source):
        return None
    return len(source)


def evaluate_training_admission(
    domain_id: object,
    component_counts: object,
    receipt_flags: object,
) -> Mapping[str, Any]:
    """Evaluate the frozen method-blind training-only admission predicate."""

    if type(domain_id) is not str or domain_id not in DOMAINS:
        raise ContractError("domain_id is not one of the two frozen domains")
    counts = _exact_mapping(component_counts, name="component_counts")
    flags = _exact_mapping(receipt_flags, name="receipt_flags")
    if tuple(counts) != ADMISSION_COMPONENTS:
        raise ContractError("component_counts has a missing, extra, or reordered key")
    if tuple(flags) != REQUIRED_ADMISSION_RECEIPTS:
        raise ContractError("receipt_flags has a missing, extra, or reordered key")
    normalized_counts = {
        key: _exact_int(counts[key], name=f"component_counts.{key}")
        for key in ADMISSION_COMPONENTS
    }
    normalized_flags = {
        key: _exact_bool(flags[key], name=f"receipt_flags.{key}")
        for key in REQUIRED_ADMISSION_RECEIPTS
    }
    maximum = max(normalized_counts.values(), default=0)
    missing_receipts = [key for key, value in normalized_flags.items() if not value]
    passed = maximum == 0 and not missing_receipts
    return {
        "domain_id": domain_id,
        "statistic_id": ADMISSION_STATISTIC_ID,
        "threshold_id": ADMISSION_THRESHOLD_ID,
        "maximum_hard_violation_count": maximum,
        "nonzero_components": [
            key for key, value in normalized_counts.items() if value != 0
        ],
        "missing_required_receipts": missing_receipts,
        "decision": "ADMIT" if passed else "NO_GO",
    }


def _validate_relative_public_path(path: object) -> str:
    if type(path) is not str or not path or len(path) > 512:
        raise ContractError("release path must be a nonempty bounded string")
    if path.startswith("/") or "\\" in path or "\x00" in path:
        raise ContractError("release path must be normalized and relative")
    parts = path.split("/")
    if any(part in ("", ".", "..") or not SAFE_PATH_PART_RE.fullmatch(part) for part in parts):
        raise ContractError("release path contains an unsafe component")
    return path


def evaluate_release_manifest(manifest: object) -> Mapping[str, Any]:
    """Evaluate a future publication manifest under the frozen release gate.

    A passing result is only a structural predicate.  It does not constitute
    legal approval, venue anonymity acceptance, a privacy audit, or a release.
    """

    value = _exact_mapping(manifest, name="manifest")
    expected = (
        "entries",
        "license_attribution_review_passed",
        "privacy_review_passed",
        "membership_inference_review_passed",
        "absolute_path_scan_passed",
        "secret_scan_passed",
        "identity_scan_passed",
        "venue_anonymity_scan_passed",
        "final_owner_release_approval_present",
    )
    if tuple(value) != expected:
        raise ContractError("release manifest has a missing, extra, or reordered key")
    entries = _exact_sequence(value["entries"], name="entries")
    seen_paths = set()
    public_count = 0
    prohibited_public_entries = []
    for ordinal, raw_entry in enumerate(entries):
        entry = _exact_mapping(raw_entry, name=f"entries[{ordinal}]")
        if tuple(entry) != (
            "relative_path",
            "sha256",
            "release_class",
            "contains_source_data",
            "contains_natural_group_identifier",
            "contains_row_level_prediction_or_sample",
            "contains_secret_or_credential",
            "contains_internal_absolute_path",
            "contains_author_identity_or_affiliation",
        ):
            raise ContractError(f"entries[{ordinal}] has an invalid field roster")
        path = _validate_relative_public_path(entry["relative_path"])
        if path in seen_paths:
            raise ContractError("release manifest contains a duplicate path")
        seen_paths.add(path)
        digest = entry["sha256"]
        if type(digest) is not str or SHA256_RE.fullmatch(digest) is None:
            raise ContractError(f"entries[{ordinal}].sha256 is invalid")
        release_class = entry["release_class"]
        if type(release_class) is not str or release_class not in RELEASE_CLASSES:
            raise ContractError(f"entries[{ordinal}].release_class is invalid")
        sensitive = []
        for key in tuple(entry)[3:]:
            flag = _exact_bool(entry[key], name=f"entries[{ordinal}].{key}")
            if flag:
                sensitive.append(key)
        if release_class in PUBLIC_CLASSES:
            public_count += 1
            if sensitive:
                prohibited_public_entries.append(
                    {"relative_path": path, "reasons": sensitive}
                )
    gate_flags = {
        key: _exact_bool(value[key], name=key) for key in expected[1:]
    }
    failed_gates = [key for key, passed in gate_flags.items() if not passed]
    decision = (
        "RELEASE_ELIGIBLE_FOR_SEPARATE_OWNER_ACTION"
        if entries and not prohibited_public_entries and not failed_gates
        else "NO_GO"
    )
    return {
        "entry_count": len(entries),
        "public_entry_count": public_count,
        "prohibited_public_entries": prohibited_public_entries,
        "failed_gates": failed_gates,
        "decision": decision,
        "release_performed": False,
    }


__all__: Tuple[str, ...] = (
    "ADMISSION_COMPONENTS",
    "ADMISSION_STATISTIC_ID",
    "ADMISSION_THRESHOLD_ID",
    "ContractError",
    "DOMAINS",
    "OBSERVATION_KERNEL_ID",
    "PHYSIONET_DOMAIN",
    "PUBLIC_CLASSES",
    "RELEASE_CLASSES",
    "REQUIRED_ADMISSION_RECEIPTS",
    "RETAIL_DOMAIN",
    "evaluate_release_manifest",
    "evaluate_training_admission",
    "half_thinning_mass_exponent",
)
