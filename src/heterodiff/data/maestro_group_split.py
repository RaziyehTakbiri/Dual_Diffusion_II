"""Frozen exact-composition group-disjoint sensitivity for MAESTRO v3.

The official MAESTRO labels remain facts on the immutable inventory records.
This module creates a *separate* sensitivity assignment in which every exact
``(canonical_composer, canonical_title)`` group belongs to one split.  It does
not parse MIDI, inspect model outputs, or replace the source labels.

The allocator first globally minimizes total absolute file-count deviation
from the published 962/137/177 train/validation/test counts and then globally
minimizes files moved from the retained source labels.  Groups are indivisible.
All remaining choices are resolved by a frozen, deterministic rule described
in :data:`MAESTRO_GROUP_SPLIT_ALGORITHM_DESCRIPTION`.
"""

from __future__ import annotations

import re
from dataclasses import InitVar, dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .maestro_inventory import (
    MAESTRO_V3_EXPECTED_MIDI_FILES,
    MaestroArchiveInventory,
    MaestroMidiInventory,
)


MAESTRO_GROUP_SPLIT_ORDER = ("train", "validation", "test")
MAESTRO_GROUP_SPLIT_TARGETS = (
    ("train", 962),
    ("validation", 137),
    ("test", 177),
)
MAESTRO_GROUP_SPLIT_ALGORITHM_ID = "exact-key-minimum-l1-then-moved-files-v2"
MAESTRO_GROUP_SPLIT_ALGORITHM_DESCRIPTION = (
    "Group by the exact NFC-preserved (canonical_composer, canonical_title) "
    "pair; order indivisible groups by decreasing member count and then a "
    "domain-separated SHA-256 group identifier; use exact integer min-cost "
    "dynamic programming to minimize first total absolute file-count deviation "
    "from 962/137/177 and second the global number of files moved from their "
    "retained source labels; only after moved-file cost, break count-vector "
    "ties by maximum absolute deviation, squared deviation, the ordered "
    "absolute-deviation vector, and the ordered count vector; then backtrack "
    "in reverse group order among globally optimal predecessors, preferring "
    "lower local moved-file cost and finally the fixed train/validation/test "
    "order."
)

_SPLIT_SET = frozenset(MAESTRO_GROUP_SPLIT_ORDER)
_TARGET_BY_SPLIT = dict(MAESTRO_GROUP_SPLIT_TARGETS)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_GROUP_ID_DOMAIN = b"heterodiff-maestro-v3-exact-composition-group-id-v1\0"
_FILE_ID_DOMAIN = b"heterodiff-maestro-v3-redacted-file-id-v1\0"
_MANIFEST_DOMAIN = b"heterodiff-maestro-v3-group-disjoint-manifest-v2\0"
_CHECKPOINT_INTERVAL = 32
_FACTORY_TOKEN = object()
_COST_INF = np.int32(1_000_000_000)


class MaestroGroupSplitError(ValueError):
    """Raised when a group-disjoint sensitivity manifest is inconsistent."""


def _sha256(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(field_name))
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(
            "{} must be a lowercase 64-character SHA-256 digest".format(field_name)
        )
    return value


def _split(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(field_name))
    if value not in _SPLIT_SET:
        raise ValueError(
            "{} must be one of {}".format(
                field_name, ", ".join(MAESTRO_GROUP_SPLIT_ORDER)
            )
        )
    return value


def _redacted_group_id(key: Tuple[str, str]) -> str:
    payload = {
        "canonical_composer": key[0],
        "canonical_title": key[1],
    }
    return sha256_bytes(
        _GROUP_ID_DOMAIN + canonical_json_dumps(payload).encode("utf-8")
    )


def _redacted_file_id(record: MaestroMidiInventory) -> str:
    # Hash the already verified content identity plus its immutable metadata row.
    # Neither the path nor the raw MIDI digest is exposed by the resulting ID.
    payload = {
        "metadata_row_number": record.metadata_row_number,
        "midi_content_sha256": record.sha256,
        "size_bytes": record.size_bytes,
    }
    return sha256_bytes(
        _FILE_ID_DOMAIN + canonical_json_dumps(payload).encode("utf-8")
    )


@dataclass(frozen=True)
class MaestroRedactedFileAssignment:
    """One public-safe pseudonymous file assignment with its source fact intact."""

    file_id_sha256: str
    source_split: str
    assigned_split: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "file_id_sha256",
            _sha256(self.file_id_sha256, field_name="file_id_sha256"),
        )
        object.__setattr__(
            self,
            "source_split",
            _split(self.source_split, field_name="source_split"),
        )
        object.__setattr__(
            self,
            "assigned_split",
            _split(self.assigned_split, field_name="assigned_split"),
        )

    @property
    def moved(self) -> bool:
        return self.source_split != self.assigned_split

    def to_public_dict(self) -> Dict[str, object]:
        return {
            "file_id_sha256": self.file_id_sha256,
            "source_split": self.source_split,
            "assigned_split": self.assigned_split,
            "moved_from_source_split": self.moved,
        }


@dataclass(frozen=True)
class MaestroExactCompositionAssignment:
    """One redacted exact-key group assigned atomically to a sensitivity split."""

    group_id_sha256: str
    assigned_split: str
    files: Tuple[MaestroRedactedFileAssignment, ...]
    source_split_counts: Tuple[Tuple[str, int], ...] = field(init=False)
    moved_file_count: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "group_id_sha256",
            _sha256(self.group_id_sha256, field_name="group_id_sha256"),
        )
        assigned_split = _split(self.assigned_split, field_name="assigned_split")
        object.__setattr__(self, "assigned_split", assigned_split)
        files = tuple(self.files)
        if not files:
            raise MaestroGroupSplitError("an exact-composition group must not be empty")
        if any(not isinstance(item, MaestroRedactedFileAssignment) for item in files):
            raise TypeError(
                "files must contain MaestroRedactedFileAssignment values"
            )
        files = tuple(sorted(files, key=lambda item: item.file_id_sha256))
        file_ids = tuple(item.file_id_sha256 for item in files)
        if len(set(file_ids)) != len(file_ids):
            raise MaestroGroupSplitError("file IDs must be unique within a group")
        if any(item.assigned_split != assigned_split for item in files):
            raise MaestroGroupSplitError(
                "every file in an exact-composition group must share its assignment"
            )
        source_counts = tuple(
            (
                split,
                sum(1 for item in files if item.source_split == split),
            )
            for split in MAESTRO_GROUP_SPLIT_ORDER
        )
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "source_split_counts", source_counts)
        object.__setattr__(
            self, "moved_file_count", sum(1 for item in files if item.moved)
        )

    @property
    def member_count(self) -> int:
        return len(self.files)

    @property
    def source_split_count(self) -> int:
        return sum(1 for _, count in self.source_split_counts if count)

    def to_public_dict(self) -> Dict[str, object]:
        return {
            "group_id_sha256": self.group_id_sha256,
            "assigned_split": self.assigned_split,
            "member_count": self.member_count,
            "source_split_counts": [
                {"source_split": split, "file_count": count}
                for split, count in self.source_split_counts
            ],
            "moved_file_count": self.moved_file_count,
            "files": [item.to_public_dict() for item in self.files],
        }


@dataclass(frozen=True)
class MaestroGroupDisjointSplit:
    """Immutable redacted manifest and aggregate balance/leakage diagnostics."""

    inventory_manifest_sha256: str
    groups: Tuple[MaestroExactCompositionAssignment, ...]
    _factory_token: InitVar[object]
    assignment_manifest_sha256: str = field(init=False)
    schema_version: int = field(default=2, init=False)

    def __post_init__(self, _factory_token: object) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise TypeError(
                "MaestroGroupDisjointSplit is factory-only; use "
                "build_maestro_group_disjoint_split"
            )
        object.__setattr__(
            self,
            "inventory_manifest_sha256",
            _sha256(
                self.inventory_manifest_sha256,
                field_name="inventory_manifest_sha256",
            ),
        )
        groups = tuple(self.groups)
        if not groups:
            raise MaestroGroupSplitError("groups must not be empty")
        if any(not isinstance(item, MaestroExactCompositionAssignment) for item in groups):
            raise TypeError(
                "groups must contain MaestroExactCompositionAssignment values"
            )
        groups = tuple(sorted(groups, key=lambda item: item.group_id_sha256))
        group_ids = tuple(item.group_id_sha256 for item in groups)
        if len(set(group_ids)) != len(group_ids):
            raise MaestroGroupSplitError("group IDs must be globally unique")
        file_ids = tuple(
            file.file_id_sha256 for group in groups for file in group.files
        )
        if len(file_ids) != MAESTRO_V3_EXPECTED_MIDI_FILES:
            raise MaestroGroupSplitError(
                "manifest must assign exactly {} files".format(
                    MAESTRO_V3_EXPECTED_MIDI_FILES
                )
            )
        if len(set(file_ids)) != len(file_ids):
            raise MaestroGroupSplitError("file IDs must be globally unique")

        replay = _allocate_groups(
            tuple(
                _AllocationGroup(
                    group_id_sha256=group.group_id_sha256,
                    size=group.member_count,
                    source_counts=tuple(
                        dict(group.source_split_counts)[split]
                        for split in MAESTRO_GROUP_SPLIT_ORDER
                    ),
                )
                for group in groups
            )
        )
        mismatches = tuple(
            group.group_id_sha256
            for group in groups
            if replay[group.group_id_sha256] != group.assigned_split
        )
        if mismatches:
            raise MaestroGroupSplitError(
                "represented assignments do not match the frozen deterministic "
                "allocation replay"
            )
        object.__setattr__(self, "groups", groups)
        digest = sha256_bytes(
            _MANIFEST_DOMAIN
            + canonical_json_dumps(self._public_payload()).encode("utf-8")
        )
        object.__setattr__(self, "assignment_manifest_sha256", digest)

    def _balance(self) -> List[Dict[str, object]]:
        result = []
        for split, target in MAESTRO_GROUP_SPLIT_TARGETS:
            assigned = sum(
                group.member_count
                for group in self.groups
                if group.assigned_split == split
            )
            result.append(
                {
                    "split": split,
                    "target_file_count": target,
                    "assigned_file_count": assigned,
                    "signed_deviation": assigned - target,
                    "assigned_group_count": sum(
                        1 for group in self.groups if group.assigned_split == split
                    ),
                }
            )
        return result

    def _movement(self) -> Dict[str, object]:
        transitions = []
        for source in MAESTRO_GROUP_SPLIT_ORDER:
            for assigned in MAESTRO_GROUP_SPLIT_ORDER:
                transitions.append(
                    {
                        "source_split": source,
                        "assigned_split": assigned,
                        "file_count": sum(
                            1
                            for group in self.groups
                            for item in group.files
                            if item.source_split == source
                            and item.assigned_split == assigned
                        ),
                    }
                )
        moved_groups = tuple(
            group for group in self.groups if group.moved_file_count
        )
        fully_moved = sum(
            1 for group in moved_groups if group.moved_file_count == group.member_count
        )
        return {
            "moved_file_count": sum(group.moved_file_count for group in self.groups),
            "unchanged_file_count": sum(
                group.member_count - group.moved_file_count for group in self.groups
            ),
            "moved_group_count": len(moved_groups),
            "partially_moved_group_count": sum(
                1
                for group in moved_groups
                if group.moved_file_count < group.member_count
            ),
            "fully_moved_group_count": fully_moved,
            "source_to_assigned_file_counts": transitions,
        }

    def _public_payload(self) -> Dict[str, object]:
        balance = self._balance()
        deviations = tuple(abs(int(item["signed_deviation"])) for item in balance)
        source_mixed_groups = sum(
            1 for group in self.groups if group.source_split_count > 1
        )
        pair_counts = {
            "train--validation": 0,
            "train--test": 0,
            "validation--test": 0,
        }
        return {
            "schema_version": self.schema_version,
            "dataset": "maestro-v3.0.0-midi",
            "gate": "exact-composition-group-disjoint-split-sensitivity",
            "inventory_manifest_sha256": self.inventory_manifest_sha256,
            "allocation": {
                "algorithm_id": MAESTRO_GROUP_SPLIT_ALGORITHM_ID,
                "algorithm_description": MAESTRO_GROUP_SPLIT_ALGORITHM_DESCRIPTION,
                "group_key": "exact canonical_composer plus canonical_title",
                "group_indivisibility_enforced": True,
                "global_lexicographic_objectives": [
                    "minimum total absolute file-count deviation",
                    "minimum total files moved from retained source labels",
                    "minimum maximum absolute file-count deviation",
                    "minimum sum of squared file-count deviations",
                    (
                        "minimum train/validation/test ordered absolute-deviation "
                        "vector"
                    ),
                    "minimum train/validation/test ordered assigned-count vector",
                ],
                "moved_file_cost_is_global_not_greedy": True,
                "deterministic_optimal_path_tie_break": (
                    "reverse frozen group order; lower local moved-file cost; "
                    "train/validation/test order"
                ),
                "model_outcomes_or_test_metrics_consulted": False,
                "source_labels_used_only_to_compute_moved_file_cost": True,
            },
            "balance": {
                "splits": balance,
                "target_file_count_total": sum(
                    target for _, target in MAESTRO_GROUP_SPLIT_TARGETS
                ),
                "assigned_file_count_total": sum(
                    group.member_count for group in self.groups
                ),
                "total_absolute_file_count_deviation": sum(deviations),
                "maximum_absolute_file_count_deviation": max(deviations),
                "exact_targets_met": not any(deviations),
            },
            "moves": self._movement(),
            "overlap": {
                "source_cross_split_exact_group_count": source_mixed_groups,
                "assigned_cross_split_exact_group_count": 0,
                "assigned_split_pair_overlap_counts": pair_counts,
                "is_exact_group_disjoint": True,
                "alias_or_near_duplicate_disjointness_claimed": False,
            },
            "group_count": len(self.groups),
            "file_count": sum(group.member_count for group in self.groups),
            "assignments": [group.to_public_dict() for group in self.groups],
            "privacy": {
                "composer_strings_included": False,
                "title_strings_included": False,
                "midi_or_audio_paths_included": False,
                "raw_midi_content_digests_included": False,
                "domain_separated_group_ids_included": True,
                "domain_separated_file_ids_included": True,
                "digest_pseudonyms_claimed_anonymous": False,
            },
            "claim_boundary": {
                "official_source_labels_modified": False,
                "official_source_split_reproduction_replaced": False,
                "exact_key_aliases_or_arrangements_detected": False,
                "model_outputs_inspected": False,
                "test_metrics_inspected": False,
            },
        }

    def to_public_dict(self) -> Dict[str, object]:
        """Return a fresh redacted assignment manifest with its own digest."""

        payload = self._public_payload()
        payload["assignment_manifest_sha256"] = self.assignment_manifest_sha256
        return payload

    def to_public_json(self) -> str:
        """Serialize the release-safe manifest as canonical JSON."""

        return canonical_json_dumps(self.to_public_dict())

    def public_summary(self) -> Mapping[str, object]:
        """Return aggregate diagnostics without the per-group assignment rows."""

        payload = self._public_payload()
        payload.pop("assignments")
        payload["assignment_manifest_sha256"] = self.assignment_manifest_sha256
        return payload


@dataclass(frozen=True)
class _ExactGroup:
    group_id_sha256: str
    members: Tuple[MaestroMidiInventory, ...]
    file_ids: Tuple[str, ...]
    source_counts: Tuple[int, int, int]

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass(frozen=True)
class _AllocationGroup:
    """The complete public facts consumed by the deterministic allocator."""

    group_id_sha256: str
    size: int
    source_counts: Tuple[int, int, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "group_id_sha256",
            _sha256(self.group_id_sha256, field_name="group_id_sha256"),
        )
        if isinstance(self.size, bool) or not isinstance(self.size, int):
            raise TypeError("allocation group size must be an integer")
        if self.size <= 0:
            raise ValueError("allocation group size must be positive")
        source_counts = tuple(self.source_counts)
        if len(source_counts) != len(MAESTRO_GROUP_SPLIT_ORDER):
            raise ValueError("allocation source_counts must have exactly three values")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in source_counts):
            raise TypeError("allocation source_counts must contain integers")
        if any(value < 0 for value in source_counts):
            raise ValueError("allocation source_counts must be nonnegative")
        if sum(source_counts) != self.size:
            raise ValueError("allocation source_counts must sum to group size")
        object.__setattr__(self, "source_counts", source_counts)


def _target_count_tuple(
    target_counts: Optional[Tuple[int, int, int]],
) -> Tuple[int, int, int]:
    if target_counts is None:
        return tuple(
            _TARGET_BY_SPLIT[split] for split in MAESTRO_GROUP_SPLIT_ORDER
        )
    values = tuple(target_counts)
    if len(values) != len(MAESTRO_GROUP_SPLIT_ORDER):
        raise ValueError("target_counts must have exactly three values")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TypeError("target_counts must contain integers")
    if any(value < 0 for value in values):
        raise ValueError("target_counts must be nonnegative")
    return values


def _advance_costs(
    previous: np.ndarray,
    group: _AllocationGroup,
    cap_validation: int,
    cap_test: int,
) -> np.ndarray:
    """Advance exact minimum moved-file costs for every reachable count state."""

    move_train, move_validation, move_test = tuple(
        group.size - source_count for source_count in group.source_counts
    )
    following = previous + np.int32(move_train)
    np.minimum(following, _COST_INF, out=following)

    if group.size <= cap_validation:
        validation_view = following[group.size :, :]
        validation_candidate = previous[: -group.size, :] + np.int32(
            move_validation
        )
        np.minimum(validation_view, validation_candidate, out=validation_view)
    if group.size <= cap_test:
        test_view = following[:, group.size :]
        test_candidate = previous[:, : -group.size] + np.int32(move_test)
        np.minimum(test_view, test_candidate, out=test_view)
    return following


def _count_vector_score(
    train_count: int,
    validation_count: int,
    test_count: int,
    moved_file_count: int,
    target_counts: Tuple[int, int, int],
) -> Tuple[object, ...]:
    counts = (train_count, validation_count, test_count)
    deviations = tuple(
        count - target for count, target in zip(counts, target_counts)
    )
    absolute = tuple(abs(value) for value in deviations)
    return (
        sum(absolute),
        moved_file_count,
        max(absolute),
        sum(value * value for value in deviations),
        absolute,
        counts,
    )


def _allocate_groups(
    groups: Sequence[_AllocationGroup],
    *,
    target_counts: Optional[Tuple[int, int, int]] = None,
) -> Dict[str, str]:
    """Return group-ID -> split under the frozen exact min-cost DP rule.

    ``target_counts`` is an internal oracle-test seam.  The only public builder
    omits it and therefore always uses the frozen 962/137/177 targets.
    """

    groups = tuple(groups)
    if any(not isinstance(group, _AllocationGroup) for group in groups):
        raise TypeError("groups must contain _AllocationGroup values")
    ordered = tuple(
        sorted(groups, key=lambda group: (-group.size, group.group_id_sha256))
    )
    if not ordered:
        raise MaestroGroupSplitError("at least one exact-composition group is required")
    group_ids = tuple(group.group_id_sha256 for group in ordered)
    if len(set(group_ids)) != len(group_ids):
        raise MaestroGroupSplitError("allocation group IDs must be unique")
    targets = _target_count_tuple(target_counts)
    total = sum(group.size for group in ordered)
    if total != sum(targets):
        raise MaestroGroupSplitError(
            "group file total must equal the allocation target total"
        )

    maximum_group_size = max(group.size for group in ordered)
    # Every global L1 optimum satisfies target_s + M - 1 for every split,
    # where M is the largest indivisible group.  Otherwise a bin that
    # overshoots by at least M can move any one of its groups to an underfull
    # bin and strictly reduce L1.  These caps therefore retain all candidates
    # for the secondary global moved-file objective.
    cap_validation = min(total, targets[1] + maximum_group_size - 1)
    cap_test = min(total, targets[2] + maximum_group_size - 1)
    cap_train = min(total, targets[0] + maximum_group_size - 1)

    initial_costs = np.full(
        (cap_validation + 1, cap_test + 1), _COST_INF, dtype=np.int32
    )
    initial_costs[0, 0] = 0
    checkpoints = {0: initial_costs}
    costs = initial_costs
    for index, group in enumerate(ordered, start=1):
        costs = _advance_costs(
            costs, group, cap_validation, cap_test
        )
        if index % _CHECKPOINT_INTERVAL == 0 or index == len(ordered):
            checkpoints[index] = costs

    best_state = None
    best_score = None
    for validation_raw, test_raw in np.argwhere(costs < _COST_INF):
        validation_count = int(validation_raw)
        test_count = int(test_raw)
        train_count = total - validation_count - test_count
        if train_count < 0 or train_count > cap_train:
            continue
        moved_file_count = int(costs[validation_count, test_count])
        score = _count_vector_score(
            train_count,
            validation_count,
            test_count,
            moved_file_count,
            targets,
        )
        if best_score is None or score < best_score:
            best_score = score
            best_state = (validation_count, test_count, moved_file_count)
    if best_state is None:
        raise RuntimeError("exact group allocation dynamic program found no state")

    current_validation, current_test, current_cost = best_state
    assigned: Dict[str, str] = {}
    block_end = len(ordered)
    while block_end:
        block_start = ((block_end - 1) // _CHECKPOINT_INTERVAL) * _CHECKPOINT_INTERVAL
        local_layers = [checkpoints[block_start]]
        for group in ordered[block_start:block_end]:
            local_layers.append(
                _advance_costs(
                    local_layers[-1], group, cap_validation, cap_test
                )
            )

        for local_index in range(block_end - block_start - 1, -1, -1):
            group = ordered[block_start + local_index]
            previous_rows = local_layers[local_index]
            choices = sorted(
                range(len(MAESTRO_GROUP_SPLIT_ORDER)),
                key=lambda split_index: (
                    group.size - group.source_counts[split_index],
                    split_index,
                ),
            )
            chosen = None
            for split_index in choices:
                split = MAESTRO_GROUP_SPLIT_ORDER[split_index]
                move_cost = group.size - group.source_counts[split_index]
                previous_validation = current_validation
                previous_test = current_test
                if split == "validation":
                    previous_validation -= group.size
                elif split == "test":
                    previous_test -= group.size
                if (
                    previous_validation < 0
                    or previous_validation > cap_validation
                    or previous_test < 0
                    or previous_test > cap_test
                ):
                    continue
                previous_cost = int(
                    previous_rows[previous_validation, previous_test]
                )
                if (
                    previous_cost < int(_COST_INF)
                    and previous_cost + move_cost == current_cost
                ):
                    chosen = (
                        split,
                        previous_validation,
                        previous_test,
                        previous_cost,
                    )
                    break
            if chosen is None:
                raise RuntimeError("failed to backtrack a minimum-cost group allocation")
            split, current_validation, current_test, current_cost = chosen
            assigned[group.group_id_sha256] = split
        block_end = block_start

    if (
        current_validation != 0
        or current_test != 0
        or current_cost != 0
        or len(assigned) != len(ordered)
    ):
        raise RuntimeError("group allocation backtracking did not reach the origin")
    return assigned


def build_maestro_group_disjoint_split(
    inventory: MaestroArchiveInventory,
) -> MaestroGroupDisjointSplit:
    """Build the frozen, redacted exact-key group-disjoint sensitivity.

    ``inventory.records[*].source_split`` is read as provenance and copied to
    the output assignment rows.  It is never overwritten or used as a target.
    No argument admits model outcomes, scores, checkpoints, or test metrics.
    """

    if not isinstance(inventory, MaestroArchiveInventory):
        raise TypeError("inventory must be a MaestroArchiveInventory")
    source_snapshot = tuple(
        (record.metadata_row_number, record.source_split) for record in inventory.records
    )

    grouped: Dict[Tuple[str, str], List[MaestroMidiInventory]] = {}
    for record in inventory.records:
        key = (record.canonical_composer, record.canonical_title)
        grouped.setdefault(key, []).append(record)

    group_ids_seen: Dict[str, Tuple[str, str]] = {}
    file_ids_seen: Dict[str, int] = {}
    exact_groups = []
    for key in sorted(grouped):
        group_id = _redacted_group_id(key)
        previous_key = group_ids_seen.get(group_id)
        if previous_key is not None and previous_key != key:
            raise MaestroGroupSplitError("domain-separated group ID collision")
        group_ids_seen[group_id] = key
        members = tuple(
            sorted(grouped[key], key=lambda record: record.metadata_row_number)
        )
        file_ids = []
        for record in members:
            file_id = _redacted_file_id(record)
            previous_row = file_ids_seen.get(file_id)
            if previous_row is not None and previous_row != record.metadata_row_number:
                raise MaestroGroupSplitError("domain-separated file ID collision")
            file_ids_seen[file_id] = record.metadata_row_number
            file_ids.append(file_id)
        source_counts = tuple(
            sum(1 for record in members if record.source_split == split)
            for split in MAESTRO_GROUP_SPLIT_ORDER
        )
        exact_groups.append(
            _ExactGroup(
                group_id_sha256=group_id,
                members=members,
                file_ids=tuple(file_ids),
                source_counts=source_counts,
            )
        )

    assigned_splits = _allocate_groups(
        tuple(
            _AllocationGroup(
                group_id_sha256=group.group_id_sha256,
                size=group.size,
                source_counts=group.source_counts,
            )
            for group in exact_groups
        )
    )
    assignments = []
    for group in exact_groups:
        assigned_split = assigned_splits[group.group_id_sha256]
        assignments.append(
            MaestroExactCompositionAssignment(
                group_id_sha256=group.group_id_sha256,
                assigned_split=assigned_split,
                files=tuple(
                    MaestroRedactedFileAssignment(
                        file_id_sha256=file_id,
                        source_split=record.source_split,
                        assigned_split=assigned_split,
                    )
                    for record, file_id in zip(group.members, group.file_ids)
                ),
            )
        )

    if source_snapshot != tuple(
        (record.metadata_row_number, record.source_split) for record in inventory.records
    ):
        raise RuntimeError("immutable inventory source labels changed during allocation")
    return MaestroGroupDisjointSplit(
        inventory_manifest_sha256=inventory.manifest_sha256,
        groups=tuple(assignments),
        _factory_token=_FACTORY_TOKEN,
    )


__all__ = [
    "MAESTRO_GROUP_SPLIT_ALGORITHM_DESCRIPTION",
    "MAESTRO_GROUP_SPLIT_ALGORITHM_ID",
    "MAESTRO_GROUP_SPLIT_ORDER",
    "MAESTRO_GROUP_SPLIT_TARGETS",
    "MaestroExactCompositionAssignment",
    "MaestroGroupDisjointSplit",
    "MaestroGroupSplitError",
    "MaestroRedactedFileAssignment",
    "build_maestro_group_disjoint_split",
]
