"""Fail-closed official-MAESTRO evidence publication.

The release runner fixes the complete policy needed to reconstruct the
MAESTRO v3 evidence bundle: resource ceilings, required dependency versions,
component schemas and digest domains, participating source modules, the
semantic-v3 boundary, and the exact group-split-v2 algorithm.  The caller must
provide explicit absolute input paths and a new output directory outside the
trusted dataset root.

Publication is all-or-nothing within one verified parent directory.  The
runner holds an opened parent directory descriptor, builds ``public/`` and
``private/`` inside a fresh descriptor-relative staging directory, flushes and
rechecks every byte and mode, revalidates source and lockfile identities, and
uses a kernel no-replace rename.  Only macOS ``renameatx_np(RENAME_EXCL)`` and
Linux libc ``renameat2(RENAME_NOREPLACE)`` are admitted; unsupported platforms,
symbols, or filesystems fail closed.  A failure after the rename is reported
as published with durability unconfirmed, never as not published.

Artifact JSON is exactly canonical UTF-8 without a trailing newline.  CLI
progress and terminal status are canonical JSON *lines*; their newline is a
transport delimiter and is not part of any claimed artifact identity.
"""

from __future__ import annotations

import argparse
import ast
import ctypes
import errno
import hashlib
import importlib.util
import os
import secrets
import stat
import sys
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Dict, Optional, Sequence, TextIO, Tuple, Union

from heterodiff.artifacts import (
    ArtifactChecksum,
    RuntimeProvenance,
    canonical_json_dumps,
    sha256_bytes,
)

from .maestro_group_split import (
    MAESTRO_GROUP_SPLIT_ALGORITHM_ID,
    build_maestro_group_disjoint_split,
)
from .maestro_inventory import (
    MAESTRO_V3_EXPECTED_MIDI_FILES,
    MaestroInventoryLimits,
    MaestroV3InventoryInput,
    inventory_maestro_v3,
)
from .maestro_raw_audit import (
    PINNED_MIDO_ORACLE_VERSION,
    audit_maestro_v3_raw_midi,
)
from .maestro_semantic_corpus import (
    MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN,
    MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_SPLIT_DIGEST_DOMAIN,
    MAESTRO_SEMANTIC_CORPUS_GATE,
    MAESTRO_SEMANTIC_CORPUS_SCHEMA_VERSION,
    MAESTRO_SEMANTIC_PUBLIC_DIGEST_DOMAIN,
    audit_maestro_v3_semantic_corpus,
)
from .maestro_semantics import MaestroSemanticLimits
from .midi_raw import MidiParseLimits


PathLike = Union[str, os.PathLike]
ProgressCallback = Callable[[str], None]

MAESTRO_EVIDENCE_PIPELINE_ID = "official-maestro-v3-evidence-bundle-v2"

PUBLIC_DIRECTORY = "public"
PRIVATE_DIRECTORY = "private"
INVENTORY_PUBLIC_FILENAME = "maestro_v3_inventory_public.json"
RAW_PUBLIC_FILENAME = "maestro_v3_raw_audit_public.json"
SEMANTIC_PUBLIC_FILENAME = "maestro_v3_semantic_census_public.json"
SEMANTIC_PRIVATE_FILENAME = "maestro_v3_semantic_census_private.json"
GROUP_PUBLIC_FILENAME = "maestro_v3_group_split_public.json"
GROUP_MANIFEST_FILENAME = "maestro_v3_group_split_manifest_redacted.json"
SOURCE_MANIFEST_FILENAME = "maestro_v3_pipeline_source_manifest.json"
BUNDLE_MANIFEST_FILENAME = "maestro_v3_evidence_bundle_manifest.json"

_PUBLIC_MODE = 0o644
_PRIVATE_MODE = 0o600
_PUBLIC_DIRECTORY_MODE = 0o755
_PRIVATE_DIRECTORY_MODE = 0o700
_BUNDLE_DIRECTORY_MODE = 0o755

_FROZEN_ARTIFACT_LAYOUT = (
    ("{}/{}".format(PUBLIC_DIRECTORY, INVENTORY_PUBLIC_FILENAME), "public", _PUBLIC_MODE),
    ("{}/{}".format(PUBLIC_DIRECTORY, RAW_PUBLIC_FILENAME), "public", _PUBLIC_MODE),
    ("{}/{}".format(PUBLIC_DIRECTORY, SEMANTIC_PUBLIC_FILENAME), "public", _PUBLIC_MODE),
    ("{}/{}".format(PUBLIC_DIRECTORY, GROUP_PUBLIC_FILENAME), "public", _PUBLIC_MODE),
    (
        "{}/{}".format(PUBLIC_DIRECTORY, GROUP_MANIFEST_FILENAME),
        "public-redacted",
        _PUBLIC_MODE,
    ),
    (
        "{}/{}".format(PUBLIC_DIRECTORY, SOURCE_MANIFEST_FILENAME),
        "public-source-identity",
        _PUBLIC_MODE,
    ),
    (
        "{}/{}".format(PRIVATE_DIRECTORY, SEMANTIC_PRIVATE_FILENAME),
        "private-owner-only",
        _PRIVATE_MODE,
    ),
    ("{}/{}".format(PUBLIC_DIRECTORY, BUNDLE_MANIFEST_FILENAME), "public", _PUBLIC_MODE),
)
_FROZEN_NON_MANIFEST_PATHS = frozenset(
    path for path, _visibility, _mode in _FROZEN_ARTIFACT_LAYOUT
    if path != "{}/{}".format(PUBLIC_DIRECTORY, BUNDLE_MANIFEST_FILENAME)
)

_FROZEN_GROUP_SCHEMA_VERSION = 2
_FROZEN_GROUP_ALGORITHM_ID = "exact-key-minimum-l1-then-moved-files-v2"
_FROZEN_SEMANTIC_SCHEMA_VERSION = 3
_FROZEN_SEMANTIC_GATE = "full-corpus-midi-clock-semantic-census-v3"

_EXPECTED_LOCK_PATH = "requirements/r0-maestro-macos-arm64-py311.lock"
_EXPECTED_LOCK_SHA256 = "546f22259a1ce383b9a89a0cbc7a1565fb5cae9193ca522111c70b6dd6efb660"
_EXPECTED_LOCK_SIZE_BYTES = 895
_EXPECTED_DISTRIBUTIONS = {
    "heterodiff": "0.1.0",
    "mido": "1.3.3",
    "numpy": "2.4.6",
}

_INVENTORY_LIMIT_VALUES = {
    "max_metadata_bytes": 64 * 1024 * 1024,
    "max_metadata_rows": 10_000,
    "max_midi_files": 10_000,
    "max_midi_file_bytes": 64 * 1024 * 1024,
    "max_total_midi_bytes": 8 * 1024 * 1024 * 1024,
    "max_field_characters": 16_384,
    "max_path_components": 64,
}
_RAW_LIMIT_VALUES = {
    "maximum_file_bytes": 8 * 1024 * 1024,
    "maximum_tracks": 256,
    "maximum_track_bytes": 8 * 1024 * 1024,
    "maximum_event_payload_bytes": 4 * 1024 * 1024,
    "maximum_events_per_track": 150_000,
    "maximum_total_events": 150_000,
    "maximum_absolute_tick": 0x7FFFFFFF,
    "maximum_ticks_per_quarter_note": 0x7FFF,
}
_SEMANTIC_LIMIT_VALUES = {
    "maximum_tracks": 256,
    "maximum_total_events": 150_000,
    "maximum_note_events": 150_000,
    "maximum_note_onsets": 100_000,
    "maximum_open_notes": 100_000,
    "maximum_atomic_note_events": 20_000,
    "maximum_tempo_events": 20_000,
    "maximum_tempo_points": 20_001,
    "maximum_control_changes": 150_000,
    "maximum_midi_port_events": 20_000,
    "maximum_time_signatures": 20_000,
}

MAESTRO_V3_RELEASE_INVENTORY_LIMITS = MaestroInventoryLimits(
    **_INVENTORY_LIMIT_VALUES
)
MAESTRO_V3_RELEASE_RAW_LIMITS = MidiParseLimits(**_RAW_LIMIT_VALUES)
MAESTRO_V3_RELEASE_SEMANTIC_LIMITS = MaestroSemanticLimits(
    **_SEMANTIC_LIMIT_VALUES
)

_INVENTORY_DIGEST_DOMAIN = b""
_RAW_DIGEST_DOMAIN = b"heterodiff-maestro-v3-raw-midi-audit-v1\0"
_SEMANTIC_PRIVATE_DIGEST_DOMAIN = (
    b"heterodiff-maestro-semantic-corpus-private-v3\0"
)
_SEMANTIC_PUBLIC_DIGEST_DOMAIN = (
    b"heterodiff-maestro-semantic-corpus-public-v3\0"
)
_ORPHAN_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN = (
    b"heterodiff-maestro-orphan-closure-sensitivity-audit-manifests-v1\0"
)
_ORPHAN_SENSITIVITY_SPLIT_DIGEST_DOMAIN = (
    b"heterodiff-maestro-orphan-closure-sensitivity-audit-split-v1\0"
)
_GROUP_MANIFEST_DIGEST_DOMAIN = (
    b"heterodiff-maestro-v3-group-disjoint-manifest-v2\0"
)
_SOURCE_MANIFEST_DIGEST_DOMAIN = (
    b"heterodiff-maestro-v3-pipeline-source-manifest-v1\0"
)
_PIPELINE_SPEC_DIGEST_DOMAIN = b"heterodiff-maestro-v3-pipeline-spec-v2\0"

# Every project module imported transitively by this entry point is explicit.
# The AST closure check below rejects a new local dependency until this list and
# therefore the pipeline-spec digest are deliberately revised.
_SOURCE_MODULE_ALLOWLIST = (
    ("heterodiff", "src/heterodiff/__init__.py"),
    ("heterodiff.artifacts", "src/heterodiff/artifacts/__init__.py"),
    ("heterodiff.artifacts.manifest", "src/heterodiff/artifacts/manifest.py"),
    ("heterodiff.data", "src/heterodiff/data/__init__.py"),
    ("heterodiff.data.atomic_counting_grid", "src/heterodiff/data/atomic_counting_grid.py"),
    ("heterodiff.data.maestro_evidence", "src/heterodiff/data/maestro_evidence.py"),
    ("heterodiff.data.maestro_group_split", "src/heterodiff/data/maestro_group_split.py"),
    ("heterodiff.data.maestro_inventory", "src/heterodiff/data/maestro_inventory.py"),
    ("heterodiff.data.maestro_orphan_closure_sensitivity", "src/heterodiff/data/maestro_orphan_closure_sensitivity.py"),
    ("heterodiff.data.maestro_pairing_sensitivity", "src/heterodiff/data/maestro_pairing_sensitivity.py"),
    ("heterodiff.data.maestro_raw_audit", "src/heterodiff/data/maestro_raw_audit.py"),
    ("heterodiff.data.maestro_semantic_corpus", "src/heterodiff/data/maestro_semantic_corpus.py"),
    ("heterodiff.data.maestro_semantics", "src/heterodiff/data/maestro_semantics.py"),
    ("heterodiff.data.midi_raw", "src/heterodiff/data/midi_raw.py"),
    ("heterodiff.data.physionet_2012_adapter", "src/heterodiff/data/physionet_2012_adapter.py"),
    ("heterodiff.data.physionet_2012_inventory", "src/heterodiff/data/physionet_2012_inventory.py"),
    ("heterodiff.data.physionet_2012_raw", "src/heterodiff/data/physionet_2012_raw.py"),
    ("heterodiff.data.reference_tensor", "src/heterodiff/data/reference_tensor.py"),
    ("heterodiff.data.synthetic_typed_hawkes", "src/heterodiff/data/synthetic_typed_hawkes.py"),
    ("heterodiff.events", "src/heterodiff/events/__init__.py"),
    ("heterodiff.events.configuration", "src/heterodiff/events/configuration.py"),
    ("heterodiff.events.observations", "src/heterodiff/events/observations.py"),
    ("heterodiff.events.schema", "src/heterodiff/events/schema.py"),
    ("heterodiff.events.transforms", "src/heterodiff/events/transforms.py"),
    ("heterodiff.validation", "src/heterodiff/validation/__init__.py"),
    ("heterodiff.validation.mido_oracle", "src/heterodiff/validation/mido_oracle.py"),
)

# Exact mapping-key contracts. Dynamic count-map key policies are recorded
# separately in the pipeline spec and enforced by component validators.
_KEY_SCHEMAS = {
    "inventory.public": (
        "schema_version", "dataset", "gate", "metadata_sha256",
        "metadata_size_bytes", "manifest_sha256", "midi_file_count",
        "midi_size_bytes", "source_splits", "composition_disjointness",
        "privacy", "claim_boundary",
    ),
    "inventory.public.source_split": (
        "source_split", "content_sha256", "midi_file_count", "midi_size_bytes",
    ),
    "inventory.public.disjointness": (
        "key_definition", "is_cross_split_disjoint",
        "cross_split_collision_count", "affected_midi_file_count",
        "split_pair_collision_counts", "source_splits_modified",
    ),
    "inventory.public.privacy": (
        "source_composer_strings_included", "source_title_strings_included",
        "midi_paths_included", "audio_paths_included",
    ),
    "inventory.public.claim": (
        "audio_files_required_or_verified", "midi_content_parsed",
        "note_events_inferred", "model_events_constructed",
        "source_splits_reassigned",
    ),
    "inventory.private": (
        "schema_version", "dataset", "gate", "metadata", "records",
        "source_splits", "exact_composition_cross_split_collisions",
    ),
    "inventory.private.metadata": ("path", "sha256", "size_bytes"),
    "inventory.private.record": (
        "metadata_row_number", "canonical_composer", "canonical_title",
        "source_split", "year", "midi_path", "audio_path", "duration",
        "sha256", "size_bytes",
    ),
    "inventory.private.split": ("source_split", "content_sha256"),
    "inventory.private.collision": (
        "canonical_composer", "canonical_title", "source_splits", "midi_paths",
    ),
    "raw.public": (
        "schema_version", "dataset", "gate", "inventory_manifest_sha256",
        "audit_sha256", "midi_parse_limits", "file_verification", "oracle",
        "headers", "tracks", "events", "raw_controllers", "maxima",
        "privacy", "claim_boundary",
    ),
    "raw.public.file_verification": (
        "expected_file_count", "verified_file_count", "verified_size_bytes",
        "sha256_and_size_rechecked", "parse_pass_count",
    ),
    "raw.public.oracle": ("required", "distribution", "pinned_version", "pass_count"),
    "raw.public.headers": ("format_type_counts", "ticks_per_quarter_note_counts"),
    "raw.public.tracks": ("track_count_distribution", "total_track_count"),
    "raw.public.events": (
        "total_event_count", "category_counts", "channel_message_counts",
        "meta_type_counts", "sysex_status_counts",
        "running_status_channel_event_count", "note_on_velocity_zero_count",
    ),
    "raw.public.controllers": (
        "controller_number_counts", "controller_64_66_67_value_counts",
        "controller_values_interpreted_as_pedal_state",
    ),
    "raw.public.controller_value": ("controller", "value", "count"),
    "raw.public.maxima": (
        "file_size_bytes", "tracks_per_file", "events_per_file",
        "events_per_track", "track_size_bytes", "track_end_tick",
        "delta_ticks", "absolute_ticks", "event_payload_bytes",
    ),
    "raw.public.privacy": (
        "trusted_root_included", "midi_paths_included", "composer_strings_included",
        "title_strings_included",
    ),
    "raw.public.claim": (
        "raw_midi_bytes_verified", "raw_midi_events_parsed",
        "note_on_velocity_zero_rewritten", "note_events_paired",
        "pedal_state_inferred", "tempo_converted_to_seconds",
        "score_alignment_inferred", "grid_quantization_applied",
        "model_windows_constructed",
    ),
    "raw.private": (
        "schema_version", "dataset", "gate", "inventory_manifest_sha256",
        "midi_parse_limits", "oracle", "records", "aggregate",
    ),
    "raw.private.oracle": ("required", "distribution", "version"),
    "raw.private.record": (
        "metadata_row_number", "midi_path", "source_split", "sha256",
        "size_bytes", "format_type", "ticks_per_quarter_note",
        "track_event_counts", "track_byte_lengths", "track_end_ticks",
        "event_category_counts", "channel_message_counts", "meta_type_counts",
        "controller_counts", "pedal_controller_value_counts",
        "sysex_status_counts", "running_status_event_count",
        "note_on_velocity_zero_count", "maximum_delta_ticks",
        "maximum_absolute_ticks", "maximum_event_payload_bytes", "oracle_passed",
    ),
    "raw.private.aggregate": (
        "file_count", "file_size_bytes", "parse_pass_count", "oracle_required",
        "oracle_pass_count", "format_type_counts", "ticks_per_quarter_note_counts",
        "track_count_counts", "total_track_count", "total_event_count",
        "event_category_counts", "channel_message_counts", "meta_type_counts",
        "controller_counts", "pedal_controller_value_counts", "sysex_status_counts",
        "running_status_event_count", "note_on_velocity_zero_count",
        "maximum_file_size_bytes", "maximum_tracks_per_file",
        "maximum_events_per_file", "maximum_events_per_track",
        "maximum_track_size_bytes", "maximum_track_end_tick",
        "maximum_delta_ticks", "maximum_absolute_ticks",
        "maximum_event_payload_bytes",
    ),
    "semantic.public": (
        "schema_version", "dataset", "gate", "gate_status",
        "inventory_manifest_sha256", "raw_audit_sha256",
        "semantic_manifests_sha256", "pairing_sensitivity_manifests_sha256",
        "raw_oracle", "semantic_limits", "window_policy", "aggregate",
        "source_splits", "privacy", "claim_boundary", "public_summary_sha256",
    ),
    "semantic.private": (
        "schema_version", "dataset", "gate", "inventory_manifest_sha256",
        "raw_audit_sha256", "raw_oracle_version", "semantic_limits",
        "window_policy", "records", "aggregate", "source_splits",
        "semantic_manifests_sha256", "pairing_sensitivity_manifests_sha256",
        "gate_status",
    ),
    "semantic.private.record": (
        "metadata_row_number", "midi_path", "source_split", "sha256",
        "size_bytes", "status", "failure_code", "failure_detail",
        "failure_detail_sha256", "semantic_manifest_sha256",
        "pairing_sensitivity_manifest_sha256", "pairing_comparison_status",
        "orphan_closure_sensitivity_status",
        "orphan_closure_sensitivity_rejection_code",
        "orphan_closure_sensitivity_failure_detail_sha256",
        "orphan_closure_sensitivity_manifest_sha256",
        "note_count", "pairing_note_count", "fifo_lifo_changed_pair_count",
        "fifo_lifo_changed_release_tick_count",
        "fifo_lifo_total_absolute_release_tick_difference",
        "retrigger_candidate_note_count", "retrigger_truncated_note_count",
        "retrigger_total_removed_duration_ticks",
        "raw_close_same_tick_precedence_count",
        "simultaneous_same_identity_open_group_count",
        "simultaneous_same_identity_open_event_count",
        "simultaneous_same_identity_open_excess_count", "closure_spelling_counts",
        "controller_count", "pedal_controller_counts", "tempo_point_count",
        "explicit_tempo_event_count", "midi_port_event_count",
        "time_signature_count", "pitch_minimum", "pitch_maximum",
        "out_of_88_key_note_count", "note_producing_streams",
        "projection_collision_cell_count", "projection_collision_event_count",
        "projection_collision_excess_event_count", "projection_collision_by_pitch",
        "projection_collision_pitch_multiplicity_histogram",
        "projection_collision_multiplicity_histogram",
        "maximum_projection_collision_cell_multiplicity",
        "projection_collision_window_count", "maximum_grid_index", "window_count",
        "tail_retained_window_count", "window_ineligible", "projection_admitted",
    ),
    "semantic.aggregate": (
        "scope", "file_count", "semantic_pass_count", "semantic_failure_count",
        "failure_code_counts", "orphan_closure_sensitivity_attempted_count",
        "orphan_closure_sensitivity_admitted_count",
        "orphan_closure_sensitivity_rejected_count",
        "orphan_closure_sensitivity_rejection_code_counts",
        "orphan_closure_sensitivity_manifests_sha256",
        "note_count", "pairing_evidence_piece_count",
        "pairing_invariant_piece_count", "pairing_representation_sensitive_piece_count",
        "pairing_note_count", "fifo_lifo_changed_pair_count",
        "fifo_lifo_changed_release_tick_count",
        "fifo_lifo_total_absolute_release_tick_difference",
        "retrigger_candidate_note_count", "retrigger_truncated_note_count",
        "retrigger_total_removed_duration_ticks",
        "raw_close_same_tick_precedence_count",
        "simultaneous_same_identity_open_group_count",
        "simultaneous_same_identity_open_event_count",
        "simultaneous_same_identity_open_excess_count", "closure_spelling_counts",
        "controller_count", "pedal_fact_count", "pedal_controller_counts",
        "tempo_point_count", "explicit_tempo_event_count", "midi_port_event_count",
        "time_signature_count", "pitch_minimum", "pitch_maximum",
        "out_of_88_key_note_count", "out_of_88_key_piece_count",
        "note_producing_stream_count", "multiple_note_stream_piece_count",
        "maximum_note_streams_per_piece", "projection_collision_cell_count",
        "projection_collision_event_count", "projection_collision_excess_event_count",
        "projection_collision_piece_count", "projection_collision_by_pitch",
        "projection_collision_pitch_multiplicity_histogram",
        "projection_collision_multiplicity_histogram",
        "maximum_projection_collision_cell_multiplicity",
        "projection_collision_piece_histogram",
        "projection_collision_piece_profile_histogram",
        "maximum_projection_collision_cells_per_piece",
        "maximum_projection_collision_events_per_piece",
        "maximum_projection_collision_excess_events_per_piece",
        "projection_collision_window_count", "maximum_grid_index", "window_count",
        "tail_retained_window_count", "empty_piece_count",
        "window_ineligible_piece_count", "projection_admitted_piece_count",
        "semantic_manifests_sha256", "pairing_sensitivity_manifests_sha256",
    ),
    "semantic.collision_pitch": (
        "pitch", "cell_count", "event_count", "excess_event_count",
    ),
    "semantic.collision_pitch_multiplicity": (
        "pitch", "cell_multiplicity", "cell_count",
    ),
    "semantic.collision_piece_profile": (
        "pitch_multiplicity_histogram", "collision_window_count", "piece_count",
    ),
    "semantic.public.raw_oracle": (
        "required", "distribution", "pinned_version", "pass_count",
    ),
    "semantic.public.window": (
        "length", "stride", "piece_concatenation", "tail_retained", "grid",
    ),
    "semantic.private.window": (
        "length", "stride", "piece_concatenation", "tail_retained",
    ),
    "semantic.public.privacy": (
        "trusted_root_included", "midi_paths_included",
        "composer_or_title_strings_included", "note_ids_included",
        "failure_details_included", "per_file_rows_included",
        "pairing_assignments_included",
        "orphan_closure_sensitivity_failure_details_included",
    ),
    "semantic.public.claim": (
        "status_scope_is_primary_census_only",
        "overall_semantic_projection_gate_closed",
        "semantic_policy_failures_repaired_or_excluded",
        "pairing_sensitivity_completed_for_semantic_passes",
        "pairing_sensitivity_selected_as_primary_policy",
        "orphan_closure_sensitivity_attempted_for_each_primary_orphan_failure",
        "orphan_closure_sensitivity_selected_as_primary_policy",
        "orphan_closure_sensitivity_outcomes_change_primary_status",
        "projection_collisions_dropped_or_resolved", "lossy_tensor_emitted",
        "model_windows_materialized", "source_splits_reassigned",
        "training_ready_claimed",
    ),
    "group.public": (
        "schema_version", "dataset", "gate", "inventory_manifest_sha256",
        "allocation", "balance", "moves", "overlap", "group_count", "file_count",
        "privacy", "claim_boundary", "assignment_manifest_sha256",
    ),
    "group.manifest": (
        "schema_version", "dataset", "gate", "inventory_manifest_sha256",
        "allocation", "balance", "moves", "overlap", "group_count", "file_count",
        "assignments", "privacy", "claim_boundary", "assignment_manifest_sha256",
    ),
    "group.allocation": (
        "algorithm_id", "algorithm_description", "group_key",
        "group_indivisibility_enforced", "global_lexicographic_objectives",
        "moved_file_cost_is_global_not_greedy",
        "deterministic_optimal_path_tie_break",
        "model_outcomes_or_test_metrics_consulted",
        "source_labels_used_only_to_compute_moved_file_cost",
    ),
    "group.balance": (
        "splits", "target_file_count_total", "assigned_file_count_total",
        "total_absolute_file_count_deviation", "maximum_absolute_file_count_deviation",
        "exact_targets_met",
    ),
    "group.balance.split": (
        "split", "target_file_count", "assigned_file_count", "signed_deviation",
        "assigned_group_count",
    ),
    "group.moves": (
        "moved_file_count", "unchanged_file_count", "moved_group_count",
        "partially_moved_group_count", "fully_moved_group_count",
        "source_to_assigned_file_counts",
    ),
    "group.move": ("source_split", "assigned_split", "file_count"),
    "group.overlap": (
        "source_cross_split_exact_group_count",
        "assigned_cross_split_exact_group_count",
        "assigned_split_pair_overlap_counts", "is_exact_group_disjoint",
        "alias_or_near_duplicate_disjointness_claimed",
    ),
    "group.assignment": (
        "group_id_sha256", "assigned_split", "member_count", "source_split_counts",
        "moved_file_count", "files",
    ),
    "group.assignment.source_count": ("source_split", "file_count"),
    "group.assignment.file": (
        "file_id_sha256", "source_split", "assigned_split",
        "moved_from_source_split",
    ),
    "group.privacy": (
        "composer_strings_included", "title_strings_included",
        "midi_or_audio_paths_included", "raw_midi_content_digests_included",
        "domain_separated_group_ids_included", "domain_separated_file_ids_included",
        "digest_pseudonyms_claimed_anonymous",
    ),
    "group.claim": (
        "official_source_labels_modified", "official_source_split_reproduction_replaced",
        "exact_key_aliases_or_arrangements_detected", "model_outputs_inspected",
        "test_metrics_inspected",
    ),
    "source.manifest": (
        "schema_version", "artifact_kind", "pipeline_id",
        "pipeline_spec_sha256", "execution_form", "files",
    ),
    "source.execution_form": (
        "kind", "immutable_wheel_claimed",
        "transitive_local_import_closure_checked",
    ),
    "source.file": ("module", "path", "size_bytes", "sha256"),
    "bundle.manifest": (
        "schema_version", "artifact_kind", "dataset", "pipeline_id",
        "pipeline_spec", "pipeline_spec_sha256", "runtime", "environment_lock",
        "source_identity", "component_status", "publication", "artifacts",
        "manifest_scope", "privacy",
    ),
    "bundle.runtime": (
        "python_version", "python_implementation", "system", "release", "machine",
        "dependencies",
    ),
    "bundle.dependency": ("name", "version"),
    "bundle.environment_lock": ("path", "size_bytes", "sha256"),
    "bundle.source_identity": ("source_manifest_sha256", "immutable_wheel_claimed"),
    "bundle.component_status": (
        "semantic_gate_status", "semantic_schema_version", "group_schema_version",
        "group_algorithm_id", "group_assignment_manifest_sha256",
    ),
    "bundle.publication": (
        "atomic_commit_backend", "atomic_no_replace", "target_absent_required",
        "staging_and_target_share_opened_parent_directory",
        "parent_directory_fsync_required_for_durable_success", "atomicity_scope",
    ),
    "bundle.artifact": ("path", "size_bytes", "sha256", "visibility"),
    "bundle.manifest_scope": (
        "listed_artifact_count", "manifest_self_identity_included",
        "canonical_json_utf8_without_trailing_newline",
    ),
    "bundle.privacy": (
        "absolute_input_or_output_paths_included",
        "private_semantic_contents_included",
        "private_semantic_artifact_identity_included",
    ),
}


def _validated_mapping_key_schema_spec(
    schemas: Mapping[str, Sequence[str]],
) -> Dict[str, Sequence[str]]:
    """Return the canonical key-schema spec after validating its declaration.

    Runtime exact-key checks compare sets, so a duplicate in the declarative
    tuple would otherwise be invisible there while still changing the frozen
    pipeline-spec bytes.  Reject malformed declarations before computing the
    pipeline identity.
    """

    result: Dict[str, Sequence[str]] = {}
    for schema_name, declared_keys in sorted(schemas.items()):
        if not isinstance(schema_name, str) or not schema_name:
            raise ValueError("mapping-key schema names must be nonempty strings")
        if isinstance(declared_keys, (str, bytes)) or not isinstance(
            declared_keys, Sequence
        ):
            raise TypeError(
                "mapping-key schema {!r} must be a sequence".format(schema_name)
            )
        keys = tuple(declared_keys)
        if not keys:
            raise ValueError(
                "mapping-key schema {!r} must not be empty".format(schema_name)
            )
        if any(not isinstance(key, str) or not key for key in keys):
            raise TypeError(
                "mapping-key schema {!r} keys must be nonempty strings".format(
                    schema_name
                )
            )
        duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
        if duplicates:
            raise ValueError(
                "mapping-key schema {!r} contains duplicate keys: {}".format(
                    schema_name, duplicates
                )
            )
        result[schema_name] = sorted(keys)
    return result

_DYNAMIC_KEY_POLICIES = {
    "inventory.split_pair_collision_counts": (
        "subset of test--train, test--validation, train--validation in sorted source order"
    ),
    "raw.numeric_count_maps": "canonical base-10 integer keys within field support",
    "raw.meta_count_map": "lowercase 0x00 through 0x7f",
    "raw.sysex_count_map": "0xf0 or 0xf7",
    "semantic.failure_code_counts": "frozen semantic failure-code allowlist",
    "semantic.orphan_closure_sensitivity_rejection_code_counts": (
        "frozen orphan-closure sensitivity rejection-code allowlist"
    ),
    "semantic.collision_histograms": "canonical positive base-10 integer keys",
}

_PIPELINE_SPEC = {
    "schema_version": 2,
    "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
    "dataset": "maestro-v3.0.0",
    "resource_limits": {
        "inventory": dict(_INVENTORY_LIMIT_VALUES),
        "raw_midi": dict(_RAW_LIMIT_VALUES),
        "semantic": dict(_SEMANTIC_LIMIT_VALUES),
    },
    "oracle": {
        "distribution": "mido",
        "required_version": PINNED_MIDO_ORACLE_VERSION,
        "required_for_every_file": True,
    },
    "semantic_component": {
        "schema_version": _FROZEN_SEMANTIC_SCHEMA_VERSION,
        "gate": _FROZEN_SEMANTIC_GATE,
    },
    "group_component": {
        "schema_version": _FROZEN_GROUP_SCHEMA_VERSION,
        "algorithm_id": _FROZEN_GROUP_ALGORITHM_ID,
    },
    "expected_distributions": dict(_EXPECTED_DISTRIBUTIONS),
    "environment_lock": {
        "path": _EXPECTED_LOCK_PATH,
        "sha256": _EXPECTED_LOCK_SHA256,
        "size_bytes": _EXPECTED_LOCK_SIZE_BYTES,
    },
    "component_digest_domains_hex": {
        "inventory": _INVENTORY_DIGEST_DOMAIN.hex(),
        "raw": _RAW_DIGEST_DOMAIN.hex(),
        "semantic_private": _SEMANTIC_PRIVATE_DIGEST_DOMAIN.hex(),
        "semantic_public": _SEMANTIC_PUBLIC_DIGEST_DOMAIN.hex(),
        "orphan_closure_sensitivity_manifests": (
            _ORPHAN_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN.hex()
        ),
        "orphan_closure_sensitivity_split": (
            _ORPHAN_SENSITIVITY_SPLIT_DIGEST_DOMAIN.hex()
        ),
        "group_manifest": _GROUP_MANIFEST_DIGEST_DOMAIN.hex(),
        "source_manifest": _SOURCE_MANIFEST_DIGEST_DOMAIN.hex(),
    },
    "source_module_allowlist": [
        {"module": module, "path": path}
        for module, path in _SOURCE_MODULE_ALLOWLIST
    ],
    "mapping_key_schemas": _validated_mapping_key_schema_spec(_KEY_SCHEMAS),
    "dynamic_key_policies": dict(_DYNAMIC_KEY_POLICIES),
    "public_sentinel_policy_version": 1,
    "output": {
        "canonical_json_utf8_without_trailing_newline": True,
        "public_directory_mode_octal": "0755",
        "public_file_mode_octal": "0644",
        "private_directory_mode_octal": "0700",
        "private_file_mode_octal": "0600",
        "target_must_be_absent": True,
        "kernel_atomic_no_replace_required": True,
        "atomicity_scope": "one directory entry within one opened same-filesystem parent",
        "artifact_layout": [
            {
                "path": path,
                "visibility": visibility,
                "mode_octal": "{:04o}".format(mode),
                "listed_as_artifact_in_bundle_manifest": path
                != "{}/{}".format(PUBLIC_DIRECTORY, BUNDLE_MANIFEST_FILENAME),
            }
            for path, visibility, mode in _FROZEN_ARTIFACT_LAYOUT
        ],
    },
}
_PIPELINE_SPEC_BYTES = canonical_json_dumps(_PIPELINE_SPEC).encode("utf-8")
MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256 = sha256_bytes(
    _PIPELINE_SPEC_DIGEST_DOMAIN + _PIPELINE_SPEC_BYTES
)

_SEMANTIC_FAILURE_CODES = frozenset(
    (
        "FORMAT_NOT_0_OR_1", "PPQN_NOT_DIVISIBLE_BY_FOUR",
        "LIMIT_MAXIMUM_TRACKS", "LIMIT_MAXIMUM_TOTAL_EVENTS",
        "LIMIT_MIDI_PORT_EVENTS", "LIMIT_TEMPO_EVENTS",
        "LIMIT_TIME_SIGNATURES", "LIMIT_NOTE_EVENTS", "LIMIT_CONTROL_CHANGES",
        "LIMIT_NOTE_ONSETS", "LIMIT_ATOMIC_NOTE_EVENTS",
        "NONPOSITIVE_NOTE_DURATION", "LIMIT_OPEN_NOTES", "NONPOSITIVE_TEMPO",
        "LIMIT_TEMPO_POINTS", "ORPHAN_NOTE_CLOSURE",
        "CONFLICTING_TEMPO_VALUES", "DANGLING_NOTE_ONSETS",
    )
)

_ORPHAN_CLOSURE_SENSITIVITY_REJECTION_CODES = frozenset(
    (
        "ATOMIC_NOTE_EVENT_LIMIT_EXCEEDED",
        "DANGLING_ONSET_AFTER_CANDIDATE_DROP",
        "NO_QUALIFYING_REDUNDANT_ORPHAN_CLOSURE",
        "NONPOSITIVE_NOTE_DURATION",
        "NOTE_EVENT_LIMIT_EXCEEDED",
        "NOTE_ONSET_LIMIT_EXCEEDED",
        "OPEN_NOTE_LIMIT_EXCEEDED",
        "ORPHAN_NOT_ADJACENT_SAME_TICK_PRE_ONSET",
        "PRIMARY_SEMANTICS_ADMITTED",
        "PRIMARY_SEMANTIC_FAILURE_NOT_ORPHAN_NOTE_CLOSURE",
        "REWRITE_DELTA_VLQ_EXCEEDED",
        "REWRITE_EVENT_COUNT_MISMATCH",
        "REWRITE_PARSE_FAILURE",
        "REWRITE_RESOURCE_LIMIT_EXCEEDED",
        "REWRITE_TRACK_EMPTY",
        "TRANSFORMED_SEMANTIC_FAILURE",
    )
)


class MaestroEvidencePipelineError(RuntimeError):
    """Raised before publication when the evidence run fails closed."""


class MaestroEvidenceArgumentError(ValueError):
    """Raised for a CLI argument error before the pipeline starts."""


class MaestroAtomicCommitUnsupportedError(MaestroEvidencePipelineError):
    """Raised when a kernel no-replace directory rename is unavailable."""


class MaestroEvidencePublishedDurabilityError(MaestroEvidencePipelineError):
    """The bundle is visible, but syncing its parent directory failed."""

    def __init__(self, result: "MaestroEvidenceBundleResult", cause: OSError):
        self.result = result
        self.cause = cause
        super().__init__(
            "bundle was atomically published, but parent-directory durability "
            "could not be confirmed: {}".format(cause)
        )


@dataclass(frozen=True)
class MaestroEvidenceBundleResult:
    """Identity of one atomically published and parent-synced bundle."""

    output_directory: Path
    artifacts: Tuple[ArtifactChecksum, ...]
    bundle_manifest_sha256: str
    bundle_manifest_size_bytes: int
    atomic_commit_backend: str
    publication_status: str = "PUBLISHED_DURABLE"

    def __post_init__(self) -> None:
        if not isinstance(self.output_directory, Path) or not self.output_directory.is_absolute():
            raise ValueError("output_directory must be an absolute Path")
        artifacts = tuple(self.artifacts)
        if len(artifacts) != 7 or any(
            not isinstance(item, ArtifactChecksum) for item in artifacts
        ):
            raise ValueError("artifacts must contain the seven non-manifest payloads")
        if len({item.path.casefold() for item in artifacts}) != len(artifacts):
            raise ValueError("artifact paths must be portably unique")
        if frozenset(item.path for item in artifacts) != _FROZEN_NON_MANIFEST_PATHS:
            raise ValueError(
                "artifacts must match the seven frozen non-manifest paths"
            )
        object.__setattr__(self, "artifacts", artifacts)
        _require_sha256(self.bundle_manifest_sha256, name="bundle_manifest_sha256")
        if (
            isinstance(self.bundle_manifest_size_bytes, bool)
            or not isinstance(self.bundle_manifest_size_bytes, int)
            or self.bundle_manifest_size_bytes <= 0
        ):
            raise ValueError("bundle_manifest_size_bytes must be positive")
        if not isinstance(self.atomic_commit_backend, str) or not self.atomic_commit_backend:
            raise ValueError("atomic_commit_backend must be nonempty")
        if self.publication_status not in {
            "PUBLISHED_DURABLE",
            "PUBLISHED_DURABILITY_UNCONFIRMED",
        }:
            raise ValueError("publication_status is unsupported")


@dataclass(frozen=True)
class _SourceSnapshot:
    payload: bytes
    digest: str
    lock_checksum: ArtifactChecksum


@dataclass(frozen=True)
class _AtomicBackend:
    name: str
    function: object
    flag: int


@dataclass
class _VerifiedParent:
    lexical_path: Path
    resolved_path: Path
    descriptor: int
    identity: Tuple[int, int, int]
    output_name: str


@dataclass(frozen=True)
class _Payload:
    logical_path: str
    data: bytes
    mode: int
    visibility: str


def _require_sha256(value: object, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MaestroEvidencePipelineError(
            "{} must be a lowercase SHA-256 digest".format(name)
        )
    return value


def _canonical_bytes(value: object) -> bytes:
    return canonical_json_dumps(value).encode("utf-8")


def _mapping(value: object, *, name: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise MaestroEvidencePipelineError("{} must be a mapping".format(name))
    return value


def _sequence(value: object, *, name: str) -> Sequence:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MaestroEvidencePipelineError("{} must be a sequence".format(name))
    return value


def _exact_keys(value: object, schema_name: str) -> Mapping:
    mapping = _mapping(value, name=schema_name)
    expected = frozenset(_KEY_SCHEMAS[schema_name])
    actual = frozenset(mapping.keys())
    if actual != expected:
        raise MaestroEvidencePipelineError(
            "{} keys differ from frozen schema; missing={}, extra={}".format(
                schema_name,
                sorted(expected - actual),
                sorted(actual - expected),
            )
        )
    return mapping


def _strict_path(value: PathLike, *, name: str) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError("{} must be a string or path-like object".format(name))
    raw = os.fspath(value)
    if not isinstance(raw, str):
        raise TypeError("{} must resolve to a text path".format(name))
    try:
        raw.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise MaestroEvidencePipelineError(
            "{} must contain valid Unicode scalar text".format(name)
        ) from error
    if not raw or unicodedata.normalize("NFC", raw) != raw:
        raise MaestroEvidencePipelineError("{} must be nonempty NFC text".format(name))
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs"}
        for character in raw
    ):
        raise MaestroEvidencePipelineError(
            "{} must not contain control, format, or surrogate characters".format(name)
        )
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise MaestroEvidencePipelineError("{} must be absolute".format(name))
    if ".." in candidate.parts:
        raise MaestroEvidencePipelineError(
            "{} must not contain parent traversal".format(name)
        )
    return candidate


def _reject_symlink_components(path: Path, *, final_must_exist: bool) -> None:
    current = Path(path.anchor)
    parts = path.parts[1:] if path.anchor else path.parts
    for index, component in enumerate(parts):
        current = current / component
        final = index == len(parts) - 1
        try:
            status = current.lstat()
        except FileNotFoundError:
            if final and not final_must_exist:
                return
            raise MaestroEvidencePipelineError(
                "path component does not exist: {}".format(current)
            )
        if stat.S_ISLNK(status.st_mode):
            raise MaestroEvidencePipelineError(
                "input and output paths must not contain symlink components: {}".format(
                    current
                )
            )


def _identity(status: os.stat_result) -> Tuple[int, int, int]:
    return (status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode))


def _regular_file_observation(status: os.stat_result) -> Tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _open_verified_parent(output: Path, trusted_root: Path) -> _VerifiedParent:
    _reject_symlink_components(output, final_must_exist=False)
    parent = output.parent
    resolved_parent = parent.resolve(strict=True)
    resolved_root = trusted_root.resolve(strict=True)
    resolved_output = resolved_parent / output.name
    try:
        resolved_output.relative_to(resolved_root)
    except ValueError:
        pass
    else:
        raise MaestroEvidencePipelineError(
            "output_directory must be outside the trusted dataset root"
        )

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(resolved_parent), flags)
    try:
        opened = os.fstat(descriptor)
        named = resolved_parent.lstat()
        if (
            not stat.S_ISDIR(opened.st_mode)
            or stat.S_ISLNK(named.st_mode)
            or _identity(opened) != _identity(named)
        ):
            raise MaestroEvidencePipelineError(
                "opened output parent does not match its verified directory path"
            )
        _reject_symlink_components(parent, final_must_exist=True)
        if parent.resolve(strict=True) != resolved_parent:
            raise MaestroEvidencePipelineError(
                "lexical output parent changed while it was being opened"
            )
        try:
            os.stat(output.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise MaestroEvidencePipelineError(
                "output_directory already exists and will not be overwritten"
            )
        return _VerifiedParent(
            lexical_path=parent,
            resolved_path=resolved_parent,
            descriptor=descriptor,
            identity=_identity(opened),
            output_name=output.name,
        )
    except Exception:
        os.close(descriptor)
        raise


def _revalidate_parent(parent: _VerifiedParent) -> None:
    opened = os.fstat(parent.descriptor)
    try:
        _reject_symlink_components(parent.lexical_path, final_must_exist=True)
        named = parent.resolved_path.lstat()
        lexical_resolved = parent.lexical_path.resolve(strict=True)
    except (FileNotFoundError, MaestroEvidencePipelineError) as error:
        raise MaestroEvidencePipelineError(
            "output parent or an ancestor was retargeted during the run"
        ) from error
    if (
        parent.identity != _identity(opened)
        or parent.identity != _identity(named)
        or stat.S_ISLNK(named.st_mode)
        or lexical_resolved != parent.resolved_path
    ):
        raise MaestroEvidencePipelineError(
            "output parent or an ancestor was retargeted during the run"
        )


def _select_atomic_backend() -> _AtomicBackend:
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        try:
            function = libc.renameatx_np
        except AttributeError as error:
            raise MaestroAtomicCommitUnsupportedError(
                "macOS renameatx_np is unavailable; no safe fallback is admitted"
            ) from error
        function.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        return _AtomicBackend(
            name="darwin-renameatx_np-RENAME_EXCL",
            function=function,
            flag=0x00000004,
        )
    if sys.platform.startswith("linux"):
        try:
            function = libc.renameat2
        except AttributeError as error:
            raise MaestroAtomicCommitUnsupportedError(
                "Linux libc renameat2 is unavailable; syscall-number fallbacks are not admitted"
            ) from error
        function.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        return _AtomicBackend(
            name="linux-renameat2-RENAME_NOREPLACE",
            function=function,
            flag=1,
        )
    raise MaestroAtomicCommitUnsupportedError(
        "atomic no-replace publication is supported only on admitted macOS and Linux APIs"
    )


def _safe_entry_name(value: str, *, name: str) -> bytes:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or "/" in value
        or unicodedata.normalize("NFC", value) != value
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    ):
        raise MaestroEvidencePipelineError("{} is not a safe entry name".format(name))
    return os.fsencode(value)


def _atomic_commit_noreplace(
    backend: _AtomicBackend,
    *,
    parent_fd: int,
    staging_name: str,
    output_name: str,
) -> None:
    source = _safe_entry_name(staging_name, name="staging_name")
    target = _safe_entry_name(output_name, name="output_name")
    ctypes.set_errno(0)
    result = backend.function(
        parent_fd, source, parent_fd, target, backend.flag
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise MaestroEvidencePipelineError(
            "output_directory appeared during the run; atomic no-replace commit refused it"
        )
    if error_number in {
        errno.ENOSYS,
        errno.EINVAL,
        getattr(errno, "ENOTSUP", errno.EINVAL),
        getattr(errno, "EOPNOTSUPP", errno.EINVAL),
    }:
        raise MaestroAtomicCommitUnsupportedError(
            "the output filesystem does not support the required atomic no-replace commit: {}".format(
                os.strerror(error_number)
            )
        )
    raise OSError(error_number, os.strerror(error_number), output_name)


def _project_root() -> Path:
    source = Path(__file__)
    _reject_symlink_components(source, final_must_exist=True)
    root = source.resolve(strict=True).parents[3]
    return root


def _local_module_source_exists(project_root: Path, module_name: str) -> bool:
    relative = Path("src") / Path(*module_name.split("."))
    return (project_root / relative.with_suffix(".py")).is_file() or (
        project_root / relative / "__init__.py"
    ).is_file()


def _local_imports(
    module_name: str,
    path: Path,
    project_root: Path,
    source_bytes: Optional[bytes] = None,
) -> Tuple[str, ...]:
    if source_bytes is None:
        source_bytes = path.read_bytes()
    tree = ast.parse(source_bytes, filename=str(path))
    package = module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "heterodiff" or alias.name.startswith("heterodiff."):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                relative = "." * node.level + (node.module or "")
                try:
                    target = importlib.util.resolve_name(relative, package)
                except (ImportError, ValueError) as error:
                    raise MaestroEvidencePipelineError(
                        "cannot resolve local import {!r} in {}".format(relative, module_name)
                    ) from error
            else:
                target = node.module or ""
            if target == "heterodiff" or target.startswith("heterodiff."):
                found.add(target)
                for alias in node.names:
                    candidate = target + "." + alias.name
                    if alias.name != "*" and _local_module_source_exists(
                        project_root, candidate
                    ):
                        found.add(candidate)
    return tuple(sorted(found))


def _validate_source_import_closure(
    project_root: Path,
    captured_sources: Optional[Mapping[str, bytes]] = None,
) -> None:
    allowlist = {module: path for module, path in _SOURCE_MODULE_ALLOWLIST}
    reached = set()
    pending = ["heterodiff.data.maestro_evidence"]
    while pending:
        module = pending.pop()
        if module in reached:
            continue
        if module not in allowlist:
            raise MaestroEvidencePipelineError(
                "participating local module is absent from source allowlist: {}".format(module)
            )
        reached.add(module)
        components = module.split(".")
        for length in range(1, len(components)):
            parent = ".".join(components[:length])
            if parent not in reached:
                pending.append(parent)
        path = project_root / allowlist[module]
        source_bytes = None
        if captured_sources is not None:
            try:
                source_bytes = captured_sources[module]
            except KeyError as error:
                raise MaestroEvidencePipelineError(
                    "captured source bytes are incomplete for {}".format(module)
                ) from error
        for imported in _local_imports(module, path, project_root, source_bytes):
            if imported not in reached:
                pending.append(imported)
    if reached != set(allowlist):
        raise MaestroEvidencePipelineError(
            "source allowlist contains modules outside the participating import closure: {}".format(
                sorted(set(allowlist) - reached)
            )
        )


def _read_stable_regular_file(path: Path, *, logical_path: str) -> Tuple[bytes, ArtifactChecksum]:
    _reject_symlink_components(path, final_must_exist=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise MaestroEvidencePipelineError(
                "source identity entry is not a regular file: {}".format(logical_path)
            )
        digest = hashlib.sha256()
        chunks = []
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(descriptor)
        named = path.lstat()
        _reject_symlink_components(path, final_must_exist=True)
        if (
            _regular_file_observation(before) != _regular_file_observation(after)
            or _regular_file_observation(before)
            != _regular_file_observation(named)
            or before.st_size != size
        ):
            raise MaestroEvidencePipelineError(
                "source identity entry changed while it was being captured: {}".format(
                    logical_path
                )
            )
        data = b"".join(chunks)
        checksum = ArtifactChecksum(
            path=logical_path,
            sha256=digest.hexdigest(),
            size_bytes=size,
        )
    except BaseException as primary:
        _close_preserving_primary(descriptor, primary)
        raise
    else:
        os.close(descriptor)
    return data, checksum


def _capture_source_snapshot() -> _SourceSnapshot:
    project_root = _project_root()
    modules = tuple(module for module, _relative in _SOURCE_MODULE_ALLOWLIST)
    relative_paths = tuple(relative for _module, relative in _SOURCE_MODULE_ALLOWLIST)
    if len(set(modules)) != len(modules) or len(set(relative_paths)) != len(relative_paths):
        raise MaestroEvidencePipelineError(
            "source module allowlist contains a duplicate module or path"
        )
    files = []
    captured_sources = {}
    for module, relative in _SOURCE_MODULE_ALLOWLIST:
        module_relative = Path("src") / Path(*module.split("."))
        canonical_paths = {
            module_relative.with_suffix(".py").as_posix(),
            (module_relative / "__init__.py").as_posix(),
        }
        if relative not in canonical_paths:
            raise MaestroEvidencePipelineError(
                "source allowlist path does not canonically identify {}".format(module)
            )
        path = project_root / relative
        source_bytes, checksum = _read_stable_regular_file(
            path, logical_path=relative
        )
        captured_sources[module] = source_bytes
        files.append(
            {
                "module": module,
                "path": relative,
                "size_bytes": checksum.size_bytes,
                "sha256": checksum.sha256,
            }
        )
    _validate_source_import_closure(project_root, captured_sources)
    lock_path = project_root / _EXPECTED_LOCK_PATH
    _lock_bytes, lock_checksum = _read_stable_regular_file(
        lock_path, logical_path=_EXPECTED_LOCK_PATH
    )
    if (
        lock_checksum.sha256 != _EXPECTED_LOCK_SHA256
        or lock_checksum.size_bytes != _EXPECTED_LOCK_SIZE_BYTES
    ):
        raise MaestroEvidencePipelineError(
            "the frozen r0 environment lockfile identity does not match the pipeline spec"
        )
    manifest = {
        "schema_version": 1,
        "artifact_kind": "heterodiff-participating-source-module-manifest",
        "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
        "pipeline_spec_sha256": MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256,
        "execution_form": {
            "kind": "source-tree-module-manifest",
            "immutable_wheel_claimed": False,
            "transitive_local_import_closure_checked": True,
        },
        "files": files,
    }
    _exact_keys(manifest, "source.manifest")
    _exact_keys(manifest["execution_form"], "source.execution_form")
    for item in manifest["files"]:
        _exact_keys(item, "source.file")
    if (
        manifest["schema_version"] != 1
        or manifest["artifact_kind"]
        != "heterodiff-participating-source-module-manifest"
        or manifest["pipeline_id"] != MAESTRO_EVIDENCE_PIPELINE_ID
        or manifest["pipeline_spec_sha256"]
        != MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256
        or manifest["execution_form"]
        != {
            "kind": "source-tree-module-manifest",
            "immutable_wheel_claimed": False,
            "transitive_local_import_closure_checked": True,
        }
        or [item["module"] for item in manifest["files"]] != list(modules)
        or [item["path"] for item in manifest["files"]] != list(relative_paths)
    ):
        raise MaestroEvidencePipelineError(
            "source manifest identity differs from the frozen contract"
        )
    payload = _canonical_bytes(manifest)
    return _SourceSnapshot(
        payload=payload,
        digest=sha256_bytes(_SOURCE_MANIFEST_DIGEST_DOMAIN + payload),
        lock_checksum=lock_checksum,
    )


def _revalidate_source_snapshot(expected: _SourceSnapshot) -> None:
    observed = _capture_source_snapshot()
    if observed != expected:
        raise MaestroEvidencePipelineError(
            "participating source modules or frozen environment lock changed during the run"
        )


def _capture_runtime() -> RuntimeProvenance:
    runtime = RuntimeProvenance.capture(tuple(_EXPECTED_DISTRIBUTIONS))
    observed = {item.name: item.version for item in runtime.dependencies}
    if observed != _EXPECTED_DISTRIBUTIONS:
        raise MaestroEvidencePipelineError(
            "installed distribution versions do not match the frozen r0 policy: expected {}, observed {}".format(
                _EXPECTED_DISTRIBUTIONS, observed
            )
        )
    return runtime


def _runtime_dict(runtime: RuntimeProvenance) -> Dict[str, object]:
    return {
        "python_version": runtime.python_version,
        "python_implementation": runtime.python_implementation,
        "system": runtime.system,
        "release": runtime.release,
        "machine": runtime.machine,
        "dependencies": [
            {"name": item.name, "version": item.version}
            for item in runtime.dependencies
        ],
    }


def _assert_frozen_limit_instances() -> None:
    checks = (
        (MAESTRO_V3_RELEASE_INVENTORY_LIMITS, _INVENTORY_LIMIT_VALUES),
        (MAESTRO_V3_RELEASE_RAW_LIMITS, _RAW_LIMIT_VALUES),
        (MAESTRO_V3_RELEASE_SEMANTIC_LIMITS, _SEMANTIC_LIMIT_VALUES),
    )
    for instance, expected in checks:
        actual_names = frozenset(instance.__dataclass_fields__)
        if actual_names != frozenset(expected):
            raise MaestroEvidencePipelineError(
                "resource-limit field names differ from the frozen pipeline spec"
            )
        if any(getattr(instance, key) != value for key, value in expected.items()):
            raise MaestroEvidencePipelineError(
                "resource-limit values differ from the frozen pipeline spec"
            )
    if (
        MAESTRO_SEMANTIC_CORPUS_SCHEMA_VERSION
        != _FROZEN_SEMANTIC_SCHEMA_VERSION
        or MAESTRO_SEMANTIC_CORPUS_GATE != _FROZEN_SEMANTIC_GATE
        or MAESTRO_SEMANTIC_PUBLIC_DIGEST_DOMAIN
        != _SEMANTIC_PUBLIC_DIGEST_DOMAIN
        or MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN
        != _ORPHAN_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN
        or MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_SPLIT_DIGEST_DOMAIN
        != _ORPHAN_SENSITIVITY_SPLIT_DIGEST_DOMAIN
    ):
        raise MaestroEvidencePipelineError(
            "imported semantic corpus constants differ from frozen v3 release policy"
        )
    if MAESTRO_GROUP_SPLIT_ALGORITHM_ID != _FROZEN_GROUP_ALGORITHM_ID:
        raise MaestroEvidencePipelineError(
            "imported group algorithm ID differs from frozen v2 release policy"
        )


def _private_digest(payload: Mapping, domain: bytes) -> str:
    return sha256_bytes(domain + _canonical_bytes(payload))


def _validate_limit_mapping(value: object, expected: Mapping, *, name: str) -> Mapping:
    mapping = _mapping(value, name=name)
    if mapping != expected:
        raise MaestroEvidencePipelineError(
            "{} field names or values differ from the frozen pipeline spec".format(name)
        )
    return mapping


def _validate_inventory(inventory: object) -> Tuple[Mapping, Mapping]:
    private = _exact_keys(inventory.to_private_dict(), "inventory.private")
    metadata = _exact_keys(private["metadata"], "inventory.private.metadata")
    records = _sequence(private["records"], name="inventory.private.records")
    splits = _sequence(private["source_splits"], name="inventory.private.source_splits")
    collisions = _sequence(
        private["exact_composition_cross_split_collisions"],
        name="inventory.private.collisions",
    )
    for item in records:
        _exact_keys(item, "inventory.private.record")
    for item in splits:
        _exact_keys(item, "inventory.private.split")
    for item in collisions:
        _exact_keys(item, "inventory.private.collision")
    recomputed = _private_digest(private, _INVENTORY_DIGEST_DOMAIN)
    if recomputed != getattr(inventory, "manifest_sha256", None):
        raise MaestroEvidencePipelineError("inventory self-digest recomputation failed")

    split_summaries = []
    for split in splits:
        label = split["source_split"]
        members = [record for record in records if record["source_split"] == label]
        split_summaries.append(
            {
                "source_split": label,
                "content_sha256": split["content_sha256"],
                "midi_file_count": len(members),
                "midi_size_bytes": sum(record["size_bytes"] for record in members),
            }
        )
    affected_paths = set()
    pair_counts = Counter()
    for collision in collisions:
        affected_paths.update(collision["midi_paths"])
        labels = collision["source_splits"]
        for left_index, left in enumerate(labels):
            for right in labels[left_index + 1 :]:
                pair_counts["{}--{}".format(left, right)] += 1
    expected = {
        "schema_version": private["schema_version"],
        "dataset": private["dataset"],
        "gate": private["gate"],
        "metadata_sha256": metadata["sha256"],
        "metadata_size_bytes": metadata["size_bytes"],
        "manifest_sha256": recomputed,
        "midi_file_count": len(records),
        "midi_size_bytes": sum(record["size_bytes"] for record in records),
        "source_splits": split_summaries,
        "composition_disjointness": {
            "key_definition": "exact canonical_composer plus canonical_title",
            "is_cross_split_disjoint": not collisions,
            "cross_split_collision_count": len(collisions),
            "affected_midi_file_count": len(affected_paths),
            "split_pair_collision_counts": dict(sorted(pair_counts.items())),
            "source_splits_modified": False,
        },
        "privacy": {
            "source_composer_strings_included": False,
            "source_title_strings_included": False,
            "midi_paths_included": False,
            "audio_paths_included": False,
        },
        "claim_boundary": {
            "audio_files_required_or_verified": False,
            "midi_content_parsed": False,
            "note_events_inferred": False,
            "model_events_constructed": False,
            "source_splits_reassigned": False,
        },
    }
    public = _exact_keys(inventory.public_summary(), "inventory.public")
    _exact_keys(public["composition_disjointness"], "inventory.public.disjointness")
    _exact_keys(public["privacy"], "inventory.public.privacy")
    _exact_keys(public["claim_boundary"], "inventory.public.claim")
    for item in _sequence(public["source_splits"], name="inventory.public.source_splits"):
        _exact_keys(item, "inventory.public.source_split")
    if public != expected:
        raise MaestroEvidencePipelineError(
            "inventory public/private projection differs from the frozen contract"
        )
    return public, private


def _pairs_dict(values: object, *, formatter: Callable[[object], str] = str) -> Dict[str, object]:
    result = {}
    for pair in _sequence(values, name="count pairs"):
        if not isinstance(pair, Sequence) or len(pair) != 2:
            raise MaestroEvidencePipelineError("count-pair entry is malformed")
        result[formatter(pair[0])] = pair[1]
    return result


def _validate_raw(raw_audit: object, inventory_digest: str) -> Tuple[Mapping, Mapping]:
    private = _exact_keys(raw_audit.to_private_dict(), "raw.private")
    _validate_limit_mapping(
        private["midi_parse_limits"], _RAW_LIMIT_VALUES, name="raw MIDI limits"
    )
    oracle = _exact_keys(private["oracle"], "raw.private.oracle")
    aggregate = _exact_keys(private["aggregate"], "raw.private.aggregate")
    records = _sequence(private["records"], name="raw.private.records")
    for record in records:
        _exact_keys(record, "raw.private.record")
    recomputed = _private_digest(private, _RAW_DIGEST_DOMAIN)
    if recomputed != getattr(raw_audit, "audit_sha256", None):
        raise MaestroEvidencePipelineError("raw-audit self-digest recomputation failed")
    if private["inventory_manifest_sha256"] != inventory_digest:
        raise MaestroEvidencePipelineError("raw audit is not bound to inventory")

    meta = lambda value: "0x{:02x}".format(value)
    status = lambda value: "0x{:02x}".format(value)
    pedal_values = []
    for triple in aggregate["pedal_controller_value_counts"]:
        if not isinstance(triple, Sequence) or len(triple) != 3:
            raise MaestroEvidencePipelineError("raw pedal-count triple is malformed")
        pedal_values.append(
            {"controller": triple[0], "value": triple[1], "count": triple[2]}
        )
    expected = {
        "schema_version": private["schema_version"],
        "dataset": private["dataset"],
        "gate": private["gate"],
        "inventory_manifest_sha256": inventory_digest,
        "audit_sha256": recomputed,
        "midi_parse_limits": private["midi_parse_limits"],
        "file_verification": {
            "expected_file_count": MAESTRO_V3_EXPECTED_MIDI_FILES,
            "verified_file_count": aggregate["file_count"],
            "verified_size_bytes": aggregate["file_size_bytes"],
            "sha256_and_size_rechecked": True,
            "parse_pass_count": aggregate["parse_pass_count"],
        },
        "oracle": {
            "required": oracle["required"],
            "distribution": oracle["distribution"],
            "pinned_version": oracle["version"],
            "pass_count": aggregate["oracle_pass_count"],
        },
        "headers": {
            "format_type_counts": _pairs_dict(aggregate["format_type_counts"]),
            "ticks_per_quarter_note_counts": _pairs_dict(
                aggregate["ticks_per_quarter_note_counts"]
            ),
        },
        "tracks": {
            "track_count_distribution": _pairs_dict(aggregate["track_count_counts"]),
            "total_track_count": aggregate["total_track_count"],
        },
        "events": {
            "total_event_count": aggregate["total_event_count"],
            "category_counts": _pairs_dict(aggregate["event_category_counts"]),
            "channel_message_counts": _pairs_dict(aggregate["channel_message_counts"]),
            "meta_type_counts": _pairs_dict(aggregate["meta_type_counts"], formatter=meta),
            "sysex_status_counts": _pairs_dict(
                aggregate["sysex_status_counts"], formatter=status
            ),
            "running_status_channel_event_count": aggregate["running_status_event_count"],
            "note_on_velocity_zero_count": aggregate["note_on_velocity_zero_count"],
        },
        "raw_controllers": {
            "controller_number_counts": _pairs_dict(aggregate["controller_counts"]),
            "controller_64_66_67_value_counts": pedal_values,
            "controller_values_interpreted_as_pedal_state": False,
        },
        "maxima": {
            "file_size_bytes": aggregate["maximum_file_size_bytes"],
            "tracks_per_file": aggregate["maximum_tracks_per_file"],
            "events_per_file": aggregate["maximum_events_per_file"],
            "events_per_track": aggregate["maximum_events_per_track"],
            "track_size_bytes": aggregate["maximum_track_size_bytes"],
            "track_end_tick": aggregate["maximum_track_end_tick"],
            "delta_ticks": aggregate["maximum_delta_ticks"],
            "absolute_ticks": aggregate["maximum_absolute_ticks"],
            "event_payload_bytes": aggregate["maximum_event_payload_bytes"],
        },
        "privacy": {
            "trusted_root_included": False,
            "midi_paths_included": False,
            "composer_strings_included": False,
            "title_strings_included": False,
        },
        "claim_boundary": {
            "raw_midi_bytes_verified": True,
            "raw_midi_events_parsed": True,
            "note_on_velocity_zero_rewritten": False,
            "note_events_paired": False,
            "pedal_state_inferred": False,
            "tempo_converted_to_seconds": False,
            "score_alignment_inferred": False,
            "grid_quantization_applied": False,
            "model_windows_constructed": False,
        },
    }
    public = _exact_keys(raw_audit.public_summary(), "raw.public")
    for key, schema in (
        ("file_verification", "raw.public.file_verification"),
        ("oracle", "raw.public.oracle"),
        ("headers", "raw.public.headers"),
        ("tracks", "raw.public.tracks"),
        ("events", "raw.public.events"),
        ("raw_controllers", "raw.public.controllers"),
        ("maxima", "raw.public.maxima"),
        ("privacy", "raw.public.privacy"),
        ("claim_boundary", "raw.public.claim"),
    ):
        _exact_keys(public[key], schema)
    for item in public["raw_controllers"]["controller_64_66_67_value_counts"]:
        _exact_keys(item, "raw.public.controller_value")
    if public != expected:
        raise MaestroEvidencePipelineError(
            "raw public/private projection differs from the frozen contract"
        )
    if (
        oracle != {"required": True, "distribution": "mido", "version": PINNED_MIDO_ORACLE_VERSION}
        or aggregate["oracle_pass_count"] != MAESTRO_V3_EXPECTED_MIDI_FILES
    ):
        raise MaestroEvidencePipelineError("raw audit lacks the complete pinned oracle")
    return public, private


def _validate_semantic_aggregate(value: object, *, name: str) -> Mapping:
    aggregate = _exact_keys(value, "semantic.aggregate")
    if aggregate["scope"] not in {"all", "test", "train", "validation"}:
        raise MaestroEvidencePipelineError("{} has unsupported scope".format(name))
    failures = _mapping(aggregate["failure_code_counts"], name=name + ".failure_code_counts")
    if not set(failures).issubset(_SEMANTIC_FAILURE_CODES):
        raise MaestroEvidencePipelineError("{} contains an unknown failure code".format(name))
    orphan_rejections = _mapping(
        aggregate["orphan_closure_sensitivity_rejection_code_counts"],
        name=name + ".orphan_closure_sensitivity_rejection_code_counts",
    )
    if not set(orphan_rejections).issubset(
        _ORPHAN_CLOSURE_SENSITIVITY_REJECTION_CODES
    ):
        raise MaestroEvidencePipelineError(
            "{} contains an unknown orphan-closure sensitivity rejection code".format(
                name
            )
        )
    if aggregate["orphan_closure_sensitivity_attempted_count"] != failures.get(
        "ORPHAN_NOTE_CLOSURE", 0
    ):
        raise MaestroEvidencePipelineError(
            "{} does not attempt the named sensitivity for every primary orphan failure".format(
                name
            )
        )
    if aggregate["orphan_closure_sensitivity_attempted_count"] != (
        aggregate["orphan_closure_sensitivity_admitted_count"]
        + aggregate["orphan_closure_sensitivity_rejected_count"]
    ):
        raise MaestroEvidencePipelineError(
            "{} orphan-closure sensitivity outcomes do not partition attempts".format(
                name
            )
        )
    if sum(orphan_rejections.values()) != aggregate[
        "orphan_closure_sensitivity_rejected_count"
    ]:
        raise MaestroEvidencePipelineError(
            "{} orphan-closure rejection counts disagree with rejected attempts".format(
                name
            )
        )
    _require_sha256(
        aggregate["orphan_closure_sensitivity_manifests_sha256"],
        name=name + ".orphan_closure_sensitivity_manifests_sha256",
    )
    closure = _mapping(aggregate["closure_spelling_counts"], name=name + ".closure")
    if not set(closure).issubset({"note_off", "note_on_velocity_zero"}):
        raise MaestroEvidencePipelineError("{} contains an unknown closure spelling".format(name))
    pedals = _mapping(aggregate["pedal_controller_counts"], name=name + ".pedals")
    if not set(pedals).issubset({"64", "66", "67"}):
        raise MaestroEvidencePipelineError("{} contains an unknown pedal controller".format(name))
    for histogram_name, minimum in (
        ("projection_collision_multiplicity_histogram", 2),
        ("projection_collision_piece_histogram", 1),
    ):
        histogram = _mapping(aggregate[histogram_name], name=name + "." + histogram_name)
        for key in histogram:
            if not key.isascii() or not key.isdigit() or str(int(key)) != key or int(key) < minimum:
                raise MaestroEvidencePipelineError(
                    "{} has an invalid histogram key".format(name)
                )
    for item in _sequence(
        aggregate["projection_collision_by_pitch"], name=name + ".collision_pitch"
    ):
        _exact_keys(item, "semantic.collision_pitch")
    for item in _sequence(
        aggregate["projection_collision_pitch_multiplicity_histogram"],
        name=name + ".collision_pitch_multiplicity",
    ):
        _exact_keys(item, "semantic.collision_pitch_multiplicity")
    for item in _sequence(
        aggregate["projection_collision_piece_profile_histogram"],
        name=name + ".collision_piece_profile",
    ):
        profile = _exact_keys(item, "semantic.collision_piece_profile")
        for joint_count in _sequence(
            profile["pitch_multiplicity_histogram"],
            name=name + ".collision_piece_profile.pitch_multiplicity_histogram",
        ):
            _exact_keys(joint_count, "semantic.collision_pitch_multiplicity")
    return aggregate


def _validate_semantic(
    semantic: object,
    inventory_digest: str,
    raw_digest: str,
) -> Tuple[Mapping, Mapping]:
    private = _exact_keys(semantic.to_private_dict(), "semantic.private")
    _validate_limit_mapping(
        private["semantic_limits"], _SEMANTIC_LIMIT_VALUES, name="semantic limits"
    )
    _exact_keys(private["window_policy"], "semantic.private.window")
    records = _sequence(private["records"], name="semantic.private.records")
    for record in records:
        record = _exact_keys(record, "semantic.private.record")
        sensitivity_status = record["orphan_closure_sensitivity_status"]
        if sensitivity_status is None:
            if any(
                record[key] is not None
                for key in (
                    "orphan_closure_sensitivity_rejection_code",
                    "orphan_closure_sensitivity_failure_detail_sha256",
                    "orphan_closure_sensitivity_manifest_sha256",
                )
            ):
                raise MaestroEvidencePipelineError(
                    "absent orphan-closure sensitivity contains per-file evidence"
                )
        elif sensitivity_status == "sensitivity_admitted":
            if record["failure_code"] != "ORPHAN_NOTE_CLOSURE" or any(
                record[key] is not None
                for key in (
                    "orphan_closure_sensitivity_rejection_code",
                    "orphan_closure_sensitivity_failure_detail_sha256",
                )
            ):
                raise MaestroEvidencePipelineError(
                    "admitted orphan-closure sensitivity has invalid per-file fields"
                )
            _require_sha256(
                record["orphan_closure_sensitivity_manifest_sha256"],
                name="semantic.private.record.orphan_closure_sensitivity_manifest_sha256",
            )
        elif sensitivity_status == "sensitivity_rejected":
            if (
                record["failure_code"] != "ORPHAN_NOTE_CLOSURE"
                or record["orphan_closure_sensitivity_rejection_code"]
                not in _ORPHAN_CLOSURE_SENSITIVITY_REJECTION_CODES
            ):
                raise MaestroEvidencePipelineError(
                    "rejected orphan-closure sensitivity has invalid per-file fields"
                )
            _require_sha256(
                record["orphan_closure_sensitivity_failure_detail_sha256"],
                name=(
                    "semantic.private.record."
                    "orphan_closure_sensitivity_failure_detail_sha256"
                ),
            )
            _require_sha256(
                record["orphan_closure_sensitivity_manifest_sha256"],
                name="semantic.private.record.orphan_closure_sensitivity_manifest_sha256",
            )
        else:
            raise MaestroEvidencePipelineError(
                "semantic private record has unsupported orphan-closure sensitivity status"
            )
        if record["failure_code"] == "ORPHAN_NOTE_CLOSURE" and (
            sensitivity_status is None
        ):
            raise MaestroEvidencePipelineError(
                "primary orphan failure lacks its named sensitivity audit"
            )
        for item in record["projection_collision_by_pitch"]:
            _exact_keys(item, "semantic.collision_pitch")
        for item in record["projection_collision_pitch_multiplicity_histogram"]:
            _exact_keys(item, "semantic.collision_pitch_multiplicity")
        histogram = _mapping(
            record["projection_collision_multiplicity_histogram"],
            name="semantic.private.record.collision_histogram",
        )
        for key in histogram:
            if not key.isascii() or not key.isdigit() or str(int(key)) != key or int(key) < 2:
                raise MaestroEvidencePipelineError(
                    "semantic private collision histogram key is invalid"
                )
    aggregate = _validate_semantic_aggregate(private["aggregate"], name="semantic.aggregate")
    split_aggregates = _sequence(private["source_splits"], name="semantic.source_splits")
    for item in split_aggregates:
        _validate_semantic_aggregate(item, name="semantic.source_split")
    if [item["scope"] for item in split_aggregates] != ["test", "train", "validation"]:
        raise MaestroEvidencePipelineError("semantic source-split scopes are not frozen")
    if (
        private["schema_version"] != _FROZEN_SEMANTIC_SCHEMA_VERSION
        or private["gate"] != _FROZEN_SEMANTIC_GATE
        or private["inventory_manifest_sha256"] != inventory_digest
        or private["raw_audit_sha256"] != raw_digest
        or private["raw_oracle_version"] != PINNED_MIDO_ORACLE_VERSION
    ):
        raise MaestroEvidencePipelineError("semantic private identity differs from frozen v3")
    private_digest = _private_digest(private, _SEMANTIC_PRIVATE_DIGEST_DOMAIN)
    if private_digest != getattr(semantic, "census_sha256", None):
        raise MaestroEvidencePipelineError("semantic private self-digest recomputation failed")

    public_without_digest = {
        "schema_version": private["schema_version"],
        "dataset": private["dataset"],
        "gate": private["gate"],
        "gate_status": private["gate_status"],
        "inventory_manifest_sha256": private["inventory_manifest_sha256"],
        "raw_audit_sha256": private["raw_audit_sha256"],
        "semantic_manifests_sha256": private["semantic_manifests_sha256"],
        "pairing_sensitivity_manifests_sha256": private[
            "pairing_sensitivity_manifests_sha256"
        ],
        "raw_oracle": {
            "required": True,
            "distribution": "mido",
            "pinned_version": private["raw_oracle_version"],
            "pass_count": MAESTRO_V3_EXPECTED_MIDI_FILES,
        },
        "semantic_limits": private["semantic_limits"],
        "window_policy": {
            **private["window_policy"],
            "grid": "exact PPQN/4 MIDI-clock grid, not a score grid",
        },
        "aggregate": aggregate,
        "source_splits": list(split_aggregates),
        "privacy": {
            "trusted_root_included": False,
            "midi_paths_included": False,
            "composer_or_title_strings_included": False,
            "note_ids_included": False,
            "failure_details_included": False,
            "orphan_closure_sensitivity_failure_details_included": False,
            "per_file_rows_included": False,
            "pairing_assignments_included": False,
        },
        "claim_boundary": {
            "status_scope_is_primary_census_only": True,
            "overall_semantic_projection_gate_closed": False,
            "semantic_policy_failures_repaired_or_excluded": False,
            "pairing_sensitivity_completed_for_semantic_passes": True,
            "pairing_sensitivity_selected_as_primary_policy": False,
            "orphan_closure_sensitivity_attempted_for_each_primary_orphan_failure": True,
            "orphan_closure_sensitivity_selected_as_primary_policy": False,
            "orphan_closure_sensitivity_outcomes_change_primary_status": False,
            "projection_collisions_dropped_or_resolved": False,
            "lossy_tensor_emitted": False,
            "model_windows_materialized": False,
            "source_splits_reassigned": False,
            "training_ready_claimed": False,
        },
    }
    public_digest = _private_digest(
        public_without_digest, _SEMANTIC_PUBLIC_DIGEST_DOMAIN
    )
    expected = dict(public_without_digest)
    expected["public_summary_sha256"] = public_digest
    public = _exact_keys(semantic.public_summary(), "semantic.public")
    _exact_keys(public["raw_oracle"], "semantic.public.raw_oracle")
    _exact_keys(public["window_policy"], "semantic.public.window")
    _exact_keys(public["privacy"], "semantic.public.privacy")
    _exact_keys(public["claim_boundary"], "semantic.public.claim")
    _validate_semantic_aggregate(public["aggregate"], name="semantic.public.aggregate")
    for item in public["source_splits"]:
        _validate_semantic_aggregate(item, name="semantic.public.source_split")
    if public != expected:
        raise MaestroEvidencePipelineError(
            "semantic public/private projection differs from the frozen v3 contract"
        )
    if (
        public_digest != getattr(semantic, "public_summary_sha256", None)
        or private["gate_status"] not in {"PRIMARY_PASS", "HOLD"}
    ):
        raise MaestroEvidencePipelineError("semantic public self-digest or gate status failed")
    return public, private


def _validate_group(group: object, inventory_digest: str) -> Tuple[Mapping, Mapping]:
    if MAESTRO_GROUP_SPLIT_ALGORITHM_ID != _FROZEN_GROUP_ALGORITHM_ID:
        raise MaestroEvidencePipelineError(
            "imported group algorithm ID differs from frozen v2 release policy"
        )
    full = _exact_keys(group.to_public_dict(), "group.manifest")
    summary = _exact_keys(group.public_summary(), "group.public")
    summary_from_full = dict(full)
    assignments = _sequence(summary_from_full.pop("assignments"), name="group.assignments")
    if summary != summary_from_full:
        raise MaestroEvidencePipelineError(
            "group summary must equal the full redacted manifest minus assignments"
        )
    for value, schema in (
        (full["allocation"], "group.allocation"),
        (full["balance"], "group.balance"),
        (full["moves"], "group.moves"),
        (full["overlap"], "group.overlap"),
        (full["privacy"], "group.privacy"),
        (full["claim_boundary"], "group.claim"),
    ):
        _exact_keys(value, schema)
    for item in full["balance"]["splits"]:
        _exact_keys(item, "group.balance.split")
    for item in full["moves"]["source_to_assigned_file_counts"]:
        _exact_keys(item, "group.move")
    for assignment in assignments:
        assignment = _exact_keys(assignment, "group.assignment")
        for count in assignment["source_split_counts"]:
            _exact_keys(count, "group.assignment.source_count")
        for file_assignment in assignment["files"]:
            _exact_keys(file_assignment, "group.assignment.file")
    if (
        full["schema_version"] != _FROZEN_GROUP_SCHEMA_VERSION
        or full["dataset"] != "maestro-v3.0.0-midi"
        or full["gate"] != "exact-composition-group-disjoint-split-sensitivity"
        or full["allocation"]["algorithm_id"] != _FROZEN_GROUP_ALGORITHM_ID
        or full["inventory_manifest_sha256"] != inventory_digest
        or getattr(group, "schema_version", None) != _FROZEN_GROUP_SCHEMA_VERSION
    ):
        raise MaestroEvidencePipelineError("group artifact differs from frozen v2 policy")
    if full["privacy"] != {
        "composer_strings_included": False,
        "title_strings_included": False,
        "midi_or_audio_paths_included": False,
        "raw_midi_content_digests_included": False,
        "domain_separated_group_ids_included": True,
        "domain_separated_file_ids_included": True,
        "digest_pseudonyms_claimed_anonymous": False,
    } or full["claim_boundary"] != {
        "official_source_labels_modified": False,
        "official_source_split_reproduction_replaced": False,
        "exact_key_aliases_or_arrangements_detected": False,
        "model_outputs_inspected": False,
        "test_metrics_inspected": False,
    }:
        raise MaestroEvidencePipelineError("group privacy or claim boundary differs from v2")
    claimed = _require_sha256(
        full["assignment_manifest_sha256"], name="group assignment digest"
    )
    digest_payload = dict(full)
    digest_payload.pop("assignment_manifest_sha256")
    recomputed = _private_digest(digest_payload, _GROUP_MANIFEST_DIGEST_DOMAIN)
    if (
        recomputed != claimed
        or recomputed != getattr(group, "assignment_manifest_sha256", None)
    ):
        raise MaestroEvidencePipelineError("group manifest self-digest recomputation failed")
    return summary, full


def _json_string_sentinel(value: object) -> Optional[bytes]:
    if not isinstance(value, str) or not value:
        return None
    return canonical_json_dumps(value).encode("utf-8")


def _scan_public_payloads(
    payloads: Sequence[_Payload],
    *,
    trusted_root: Path,
    metadata_csv: Path,
    output_directory: Path,
    inventory_private: Mapping,
    semantic_private: Mapping,
) -> None:
    base_values = {
        str(trusted_root), str(trusted_root.resolve(strict=True)),
        str(metadata_csv), str(metadata_csv.resolve(strict=True)),
        str(output_directory),
    }
    source_values = set()
    raw_digests = set()
    per_file_semantic_digests = set()
    source_values.add(inventory_private["metadata"]["path"])
    for record in inventory_private["records"]:
        source_values.update(
            (
                record["canonical_composer"], record["canonical_title"],
                record["midi_path"], record["audio_path"],
            )
        )
        raw_digests.add(record["sha256"])
    failure_values = {
        record["failure_detail"]
        for record in semantic_private["records"]
        if record["failure_detail"] is not None
    }
    for record in semantic_private["records"]:
        for key in (
            "failure_detail_sha256",
            "semantic_manifest_sha256",
            "pairing_sensitivity_manifest_sha256",
            "orphan_closure_sensitivity_failure_detail_sha256",
            "orphan_closure_sensitivity_manifest_sha256",
        ):
            value = record.get(key)
            if value is not None:
                per_file_semantic_digests.add(value)
    common = (
        base_values
        | source_values
        | failure_values
        | raw_digests
        | per_file_semantic_digests
    )
    common_sentinels = tuple(
        sentinel
        for sentinel in (_json_string_sentinel(value) for value in common)
        if sentinel is not None
    )
    metadata_and_split_digests = {
        inventory_private["metadata"]["sha256"],
        *(
            item["content_sha256"] for item in inventory_private["source_splits"]
        ),
    }
    group_extra = tuple(
        sentinel
        for sentinel in (
            _json_string_sentinel(value) for value in metadata_and_split_digests
        )
        if sentinel is not None
    )
    for payload in payloads:
        if not payload.logical_path.startswith(PUBLIC_DIRECTORY + "/"):
            continue
        sentinels = common_sentinels
        if payload.logical_path in {
            "{}/{}".format(PUBLIC_DIRECTORY, GROUP_PUBLIC_FILENAME),
            "{}/{}".format(PUBLIC_DIRECTORY, GROUP_MANIFEST_FILENAME),
            "{}/{}".format(PUBLIC_DIRECTORY, BUNDLE_MANIFEST_FILENAME),
        }:
            sentinels += group_extra
        for sentinel in sentinels:
            if sentinel in payload.data:
                raise MaestroEvidencePipelineError(
                    "public sentinel scan detected a private source value in {}".format(
                        payload.logical_path
                    )
                )


def _artifact_checksum(payload: _Payload) -> ArtifactChecksum:
    return ArtifactChecksum(
        path=payload.logical_path,
        sha256=sha256_bytes(payload.data),
        size_bytes=len(payload.data),
    )


def _validate_bundle_manifest_structure(value: object) -> Dict[str, object]:
    manifest = _exact_keys(value, "bundle.manifest")
    runtime = _exact_keys(manifest["runtime"], "bundle.runtime")
    observed_dependencies = []
    for dependency in _sequence(
        runtime["dependencies"], name="bundle.runtime.dependencies"
    ):
        dependency = _exact_keys(dependency, "bundle.dependency")
        observed_dependencies.append((dependency["name"], dependency["version"]))
    for key, schema in (
        ("environment_lock", "bundle.environment_lock"),
        ("source_identity", "bundle.source_identity"),
        ("component_status", "bundle.component_status"),
        ("publication", "bundle.publication"),
        ("manifest_scope", "bundle.manifest_scope"),
        ("privacy", "bundle.privacy"),
    ):
        _exact_keys(manifest[key], schema)
    artifacts = _sequence(manifest["artifacts"], name="bundle.artifacts")
    observed_visibility = {}
    for artifact in artifacts:
        artifact = _exact_keys(artifact, "bundle.artifact")
        path = artifact["path"]
        if path in observed_visibility:
            raise MaestroEvidencePipelineError(
                "bundle manifest contains a duplicate artifact path"
            )
        observed_visibility[path] = artifact["visibility"]
        _require_sha256(artifact["sha256"], name="bundle artifact digest")
        if (
            isinstance(artifact["size_bytes"], bool)
            or not isinstance(artifact["size_bytes"], int)
            or artifact["size_bytes"] <= 0
        ):
            raise MaestroEvidencePipelineError(
                "bundle artifact size must be a positive integer"
            )
    expected_visibility = {
        path: visibility
        for path, visibility, _mode in _FROZEN_ARTIFACT_LAYOUT
        if path in _FROZEN_NON_MANIFEST_PATHS
    }
    if observed_visibility != expected_visibility:
        raise MaestroEvidencePipelineError(
            "bundle artifact paths or visibility classes differ from the frozen layout"
        )
    if (
        manifest["schema_version"] != 2
        or manifest["artifact_kind"]
        != "official-maestro-v3-evidence-bundle-manifest"
        or manifest["dataset"] != "maestro-v3.0.0"
        or manifest["pipeline_id"] != MAESTRO_EVIDENCE_PIPELINE_ID
        or manifest["pipeline_spec"] != _PIPELINE_SPEC
        or manifest["pipeline_spec_sha256"]
        != MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256
        or observed_dependencies != list(_EXPECTED_DISTRIBUTIONS.items())
        or manifest["environment_lock"]
        != {
            "path": _EXPECTED_LOCK_PATH,
            "size_bytes": _EXPECTED_LOCK_SIZE_BYTES,
            "sha256": _EXPECTED_LOCK_SHA256,
        }
        or manifest["source_identity"]["immutable_wheel_claimed"] is not False
        or manifest["component_status"]["semantic_schema_version"]
        != _FROZEN_SEMANTIC_SCHEMA_VERSION
        or manifest["component_status"]["group_schema_version"]
        != _FROZEN_GROUP_SCHEMA_VERSION
        or manifest["component_status"]["group_algorithm_id"]
        != _FROZEN_GROUP_ALGORITHM_ID
        or manifest["publication"]["atomic_no_replace"] is not True
        or manifest["publication"]["target_absent_required"] is not True
        or manifest["publication"][
            "staging_and_target_share_opened_parent_directory"
        ]
        is not True
        or manifest["publication"][
            "parent_directory_fsync_required_for_durable_success"
        ]
        is not True
        or manifest["manifest_scope"]
        != {
            "listed_artifact_count": 7,
            "manifest_self_identity_included": False,
            "canonical_json_utf8_without_trailing_newline": True,
        }
        or manifest["privacy"]
        != {
            "absolute_input_or_output_paths_included": False,
            "private_semantic_contents_included": False,
            "private_semantic_artifact_identity_included": True,
        }
    ):
        raise MaestroEvidencePipelineError(
            "bundle manifest identity, scope, or privacy differs from the frozen contract"
        )
    _require_sha256(
        manifest["environment_lock"]["sha256"], name="environment lock digest"
    )
    _require_sha256(
        manifest["source_identity"]["source_manifest_sha256"],
        name="source manifest digest",
    )
    _require_sha256(
        manifest["component_status"]["group_assignment_manifest_sha256"],
        name="group manifest digest",
    )
    return dict(manifest)


def _bundle_manifest(
    *,
    runtime: RuntimeProvenance,
    source: _SourceSnapshot,
    artifacts: Sequence[Tuple[ArtifactChecksum, str]],
    semantic_status: object,
    group_digest: str,
    atomic_backend: str,
) -> Dict[str, object]:
    ordered = tuple(sorted(artifacts, key=lambda item: item[0].path))
    manifest = {
        "schema_version": 2,
        "artifact_kind": "official-maestro-v3-evidence-bundle-manifest",
        "dataset": "maestro-v3.0.0",
        "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
        "pipeline_spec": _PIPELINE_SPEC,
        "pipeline_spec_sha256": MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256,
        "runtime": _runtime_dict(runtime),
        "environment_lock": {
            "path": source.lock_checksum.path,
            "size_bytes": source.lock_checksum.size_bytes,
            "sha256": source.lock_checksum.sha256,
        },
        "source_identity": {
            "source_manifest_sha256": source.digest,
            "immutable_wheel_claimed": False,
        },
        "component_status": {
            "semantic_gate_status": semantic_status,
            "semantic_schema_version": _FROZEN_SEMANTIC_SCHEMA_VERSION,
            "group_schema_version": _FROZEN_GROUP_SCHEMA_VERSION,
            "group_algorithm_id": _FROZEN_GROUP_ALGORITHM_ID,
            "group_assignment_manifest_sha256": group_digest,
        },
        "publication": {
            "atomic_commit_backend": atomic_backend,
            "atomic_no_replace": True,
            "target_absent_required": True,
            "staging_and_target_share_opened_parent_directory": True,
            "parent_directory_fsync_required_for_durable_success": True,
            "atomicity_scope": (
                "complete bundle directory-entry visibility within one opened "
                "same-filesystem parent; not a claim about remote replicas, "
                "backup systems, or filesystems that violate local rename semantics"
            ),
        },
        "artifacts": [
            {
                "path": checksum.path,
                "size_bytes": checksum.size_bytes,
                "sha256": checksum.sha256,
                "visibility": visibility,
            }
            for checksum, visibility in ordered
        ],
        "manifest_scope": {
            "listed_artifact_count": len(ordered),
            "manifest_self_identity_included": False,
            "canonical_json_utf8_without_trailing_newline": True,
        },
        "privacy": {
            "absolute_input_or_output_paths_included": False,
            "private_semantic_contents_included": False,
            "private_semantic_artifact_identity_included": True,
        },
    }
    return _validate_bundle_manifest_structure(manifest)


def _open_directory_at(parent_fd: int, name: str) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    return os.open(name, flags, dir_fd=parent_fd)


def _attach_cleanup_error(primary: BaseException, attribute: str, error: BaseException) -> None:
    """Preserve a primary failure while retaining cleanup diagnostics."""

    try:
        existing = getattr(primary, attribute, ())
        if not isinstance(existing, tuple):
            existing = (existing,)
        setattr(primary, attribute, existing + (error,))
    except Exception:
        pass


def _close_preserving_primary(descriptor: int, primary: BaseException) -> None:
    try:
        os.close(descriptor)
    except BaseException as error:
        _attach_cleanup_error(primary, "descriptor_cleanup_errors", error)


def _write_exact_file_at(directory_fd: int, name: str, data: bytes, mode: int) -> None:
    _safe_entry_name(name, name="artifact filename")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, mode, dir_fd=directory_fd)
    try:
        os.fchmod(descriptor, mode)
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError(errno.EIO, "short write while staging artifact")
            offset += written
        os.fsync(descriptor)
    except BaseException as primary:
        _close_preserving_primary(descriptor, primary)
        raise
    else:
        os.close(descriptor)

    read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    verifier = os.open(name, read_flags, dir_fd=directory_fd)
    try:
        before = os.fstat(verifier)
        if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != mode:
            raise MaestroEvidencePipelineError("staged artifact type or mode is incorrect")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(verifier, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(verifier)
        if (
            _identity(before) != _identity(after)
            or before.st_size != after.st_size
            or size != len(data)
            or digest.hexdigest() != sha256_bytes(data)
        ):
            raise MaestroEvidencePipelineError("staged artifact identity verification failed")
    except BaseException as primary:
        _close_preserving_primary(verifier, primary)
        raise
    else:
        os.close(verifier)


def _verify_open_directory_identity(
    *,
    parent_fd: int,
    name: str,
    descriptor: int,
    expected_identity: Optional[Tuple[int, int, int]] = None,
    expected_mode: Optional[int] = None,
    expected_entries: Optional[Sequence[str]] = None,
) -> Tuple[int, int, int]:
    opened = os.fstat(descriptor)
    named = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    observed_identity = _identity(opened)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or not stat.S_ISDIR(named.st_mode)
        or observed_identity != _identity(named)
        or (expected_identity is not None and observed_identity != expected_identity)
    ):
        raise MaestroEvidencePipelineError(
            "staging directory entry no longer names its opened directory"
        )
    if expected_mode is not None and stat.S_IMODE(opened.st_mode) != expected_mode:
        raise MaestroEvidencePipelineError("staging directory mode is incorrect")
    if expected_entries is not None:
        observed_entries = frozenset(os.listdir(descriptor))
        if observed_entries != frozenset(expected_entries):
            raise MaestroEvidencePipelineError(
                "staging directory entries differ from the frozen layout"
            )
    return observed_identity


def _cleanup_staging(
    parent_fd: int,
    staging_name: str,
    payloads: Sequence[_Payload],
    *,
    expected_stage_identity: Optional[Tuple[int, int, int]] = None,
    expected_child_identities: Optional[Mapping[str, Tuple[int, int, int]]] = None,
) -> None:
    try:
        stage_fd = _open_directory_at(parent_fd, staging_name)
    except FileNotFoundError:
        return
    try:
        _verify_open_directory_identity(
            parent_fd=parent_fd,
            name=staging_name,
            descriptor=stage_fd,
            expected_identity=expected_stage_identity,
        )
        for directory in (PUBLIC_DIRECTORY, PRIVATE_DIRECTORY):
            try:
                child_fd = _open_directory_at(stage_fd, directory)
            except FileNotFoundError:
                continue
            try:
                expected_child_identity = None
                if expected_child_identities is not None:
                    expected_child_identity = expected_child_identities.get(directory)
                _verify_open_directory_identity(
                    parent_fd=stage_fd,
                    name=directory,
                    descriptor=child_fd,
                    expected_identity=expected_child_identity,
                )
                for payload in payloads:
                    parsed = PurePosixPath(payload.logical_path)
                    if parsed.parts[0] != directory:
                        continue
                    try:
                        os.unlink(parsed.name, dir_fd=child_fd)
                    except FileNotFoundError:
                        pass
                os.fsync(child_fd)
            finally:
                os.close(child_fd)
            os.rmdir(directory, dir_fd=stage_fd)
        os.fsync(stage_fd)
    finally:
        os.close(stage_fd)
    os.rmdir(staging_name, dir_fd=parent_fd)
    os.fsync(parent_fd)


def _publish_bundle(
    *,
    parent: _VerifiedParent,
    backend: _AtomicBackend,
    payloads: Sequence[_Payload],
    source_snapshot: _SourceSnapshot,
    result: MaestroEvidenceBundleResult,
    progress: Optional[ProgressCallback],
) -> None:
    staging_name = ".{}-staging-{}".format(
        parent.output_name, secrets.token_hex(16)
    )
    expected_layout = {
        path: (visibility, mode)
        for path, visibility, mode in _FROZEN_ARTIFACT_LAYOUT
    }
    observed_layout = {
        payload.logical_path: (payload.visibility, payload.mode)
        for payload in payloads
    }
    if len(payloads) != len(expected_layout) or observed_layout != expected_layout:
        raise MaestroEvidencePipelineError(
            "artifact paths, visibility classes, or modes differ from the frozen output layout"
        )
    os.mkdir(staging_name, mode=0o700, dir_fd=parent.descriptor)
    published = False
    stage_fd = -1
    public_fd = -1
    private_fd = -1
    stage_identity = None
    child_identities: Dict[str, Tuple[int, int, int]] = {}
    expected_public_entries = tuple(
        PurePosixPath(path).name
        for path, _visibility, _mode in _FROZEN_ARTIFACT_LAYOUT
        if path.startswith(PUBLIC_DIRECTORY + "/")
    )
    expected_private_entries = (SEMANTIC_PRIVATE_FILENAME,)
    try:
        stage_fd = _open_directory_at(parent.descriptor, staging_name)
        stage_identity = _verify_open_directory_identity(
            parent_fd=parent.descriptor,
            name=staging_name,
            descriptor=stage_fd,
        )
        os.mkdir(PUBLIC_DIRECTORY, mode=0o700, dir_fd=stage_fd)
        os.mkdir(PRIVATE_DIRECTORY, mode=0o700, dir_fd=stage_fd)
        public_fd = _open_directory_at(stage_fd, PUBLIC_DIRECTORY)
        private_fd = _open_directory_at(stage_fd, PRIVATE_DIRECTORY)
        child_identities[PUBLIC_DIRECTORY] = _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PUBLIC_DIRECTORY,
            descriptor=public_fd,
        )
        child_identities[PRIVATE_DIRECTORY] = _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PRIVATE_DIRECTORY,
            descriptor=private_fd,
        )
        for payload in payloads:
            parsed = PurePosixPath(payload.logical_path)
            if parsed.parts[0] == PUBLIC_DIRECTORY:
                directory_fd = public_fd
            else:
                directory_fd = private_fd
            _write_exact_file_at(directory_fd, parsed.name, payload.data, payload.mode)

        os.fchmod(public_fd, _PUBLIC_DIRECTORY_MODE)
        os.fsync(public_fd)
        os.fchmod(private_fd, _PRIVATE_DIRECTORY_MODE)
        os.fsync(private_fd)
        os.fchmod(stage_fd, _BUNDLE_DIRECTORY_MODE)
        os.fsync(stage_fd)

        _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PUBLIC_DIRECTORY,
            descriptor=public_fd,
            expected_identity=child_identities[PUBLIC_DIRECTORY],
            expected_mode=_PUBLIC_DIRECTORY_MODE,
            expected_entries=expected_public_entries,
        )
        _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PRIVATE_DIRECTORY,
            descriptor=private_fd,
            expected_identity=child_identities[PRIVATE_DIRECTORY],
            expected_mode=_PRIVATE_DIRECTORY_MODE,
            expected_entries=expected_private_entries,
        )
        _verify_open_directory_identity(
            parent_fd=parent.descriptor,
            name=staging_name,
            descriptor=stage_fd,
            expected_identity=stage_identity,
            expected_mode=_BUNDLE_DIRECTORY_MODE,
            expected_entries=(PUBLIC_DIRECTORY, PRIVATE_DIRECTORY),
        )

        if progress is not None:
            progress("precommit: staged bytes and modes flushed; revalidating identities")
        _revalidate_parent(parent)
        os.fsync(parent.descriptor)
        _revalidate_source_snapshot(source_snapshot)
        _revalidate_parent(parent)
        _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PUBLIC_DIRECTORY,
            descriptor=public_fd,
            expected_identity=child_identities[PUBLIC_DIRECTORY],
            expected_mode=_PUBLIC_DIRECTORY_MODE,
            expected_entries=expected_public_entries,
        )
        _verify_open_directory_identity(
            parent_fd=stage_fd,
            name=PRIVATE_DIRECTORY,
            descriptor=private_fd,
            expected_identity=child_identities[PRIVATE_DIRECTORY],
            expected_mode=_PRIVATE_DIRECTORY_MODE,
            expected_entries=expected_private_entries,
        )
        _verify_open_directory_identity(
            parent_fd=parent.descriptor,
            name=staging_name,
            descriptor=stage_fd,
            expected_identity=stage_identity,
            expected_mode=_BUNDLE_DIRECTORY_MODE,
            expected_entries=(PUBLIC_DIRECTORY, PRIVATE_DIRECTORY),
        )
        _atomic_commit_noreplace(
            backend,
            parent_fd=parent.descriptor,
            staging_name=staging_name,
            output_name=parent.output_name,
        )
        published = True
        for descriptor in (public_fd, private_fd, stage_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        public_fd = -1
        private_fd = -1
        stage_fd = -1
        try:
            os.fsync(parent.descriptor)
        except OSError as error:
            uncertain = replace(
                result,
                publication_status="PUBLISHED_DURABILITY_UNCONFIRMED",
            )
            raise MaestroEvidencePublishedDurabilityError(uncertain, error) from error
    except BaseException as primary:
        if public_fd >= 0:
            _close_preserving_primary(public_fd, primary)
        if private_fd >= 0:
            _close_preserving_primary(private_fd, primary)
        if stage_fd >= 0:
            _close_preserving_primary(stage_fd, primary)
        if not published:
            try:
                _cleanup_staging(
                    parent.descriptor,
                    staging_name,
                    payloads,
                    expected_stage_identity=stage_identity,
                    expected_child_identities=child_identities,
                )
            except BaseException as cleanup_error:
                _attach_cleanup_error(primary, "staging_cleanup_error", cleanup_error)
        raise


def run_maestro_v3_evidence_pipeline(
    *,
    trusted_root: PathLike,
    metadata_csv: PathLike,
    output_directory: PathLike,
    progress: Optional[ProgressCallback] = None,
) -> MaestroEvidenceBundleResult:
    """Run every frozen gate and atomically publish one evidence bundle."""

    root = _strict_path(trusted_root, name="trusted_root")
    metadata = _strict_path(metadata_csv, name="metadata_csv")
    output_lexical = _strict_path(output_directory, name="output_directory")
    _reject_symlink_components(root, final_must_exist=True)
    _reject_symlink_components(metadata, final_must_exist=True)
    root_status = root.lstat()
    metadata_status = metadata.lstat()
    if not stat.S_ISDIR(root_status.st_mode):
        raise MaestroEvidencePipelineError("trusted_root must be a directory")
    if not stat.S_ISREG(metadata_status.st_mode):
        raise MaestroEvidencePipelineError("metadata_csv must be a regular file")
    declared = MaestroV3InventoryInput(root=root, metadata_csv=metadata)
    parent = _open_verified_parent(output_lexical, root)
    output = parent.resolved_path / parent.output_name
    try:
        if progress is not None:
            progress("preflight: paths and output parent verified")
        backend = _select_atomic_backend()
        _assert_frozen_limit_instances()
        runtime = _capture_runtime()
        source_snapshot = _capture_source_snapshot()

        if progress is not None:
            progress("inventory: verifying metadata and referenced MIDI bytes")
        inventory = inventory_maestro_v3(
            declared, limits=MAESTRO_V3_RELEASE_INVENTORY_LIMITS
        )
        if progress is not None:
            progress("raw-audit: running strict parser and pinned Mido oracle")
        raw_audit = audit_maestro_v3_raw_midi(
            inventory,
            root,
            limits=MAESTRO_V3_RELEASE_RAW_LIMITS,
            require_mido_oracle=True,
        )
        if progress is not None:
            progress("semantic-census: running frozen semantic-v3 census")
        semantic = audit_maestro_v3_semantic_corpus(
            inventory,
            raw_audit,
            root,
            limits=MAESTRO_V3_RELEASE_SEMANTIC_LIMITS,
        )
        if progress is not None:
            progress("group-split: running frozen exact-key v2 allocation")
        group = build_maestro_group_disjoint_split(inventory)

        inventory_public, inventory_private = _validate_inventory(inventory)
        inventory_digest = inventory_public["manifest_sha256"]
        raw_public, _raw_private = _validate_raw(raw_audit, inventory_digest)
        raw_digest = raw_public["audit_sha256"]
        semantic_public, semantic_private = _validate_semantic(
            semantic, inventory_digest, raw_digest
        )
        group_public, group_manifest = _validate_group(group, inventory_digest)

        non_manifest_payloads = [
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, INVENTORY_PUBLIC_FILENAME),
                _canonical_bytes(inventory_public), _PUBLIC_MODE, "public"
            ),
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, RAW_PUBLIC_FILENAME),
                _canonical_bytes(raw_public), _PUBLIC_MODE, "public"
            ),
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, SEMANTIC_PUBLIC_FILENAME),
                _canonical_bytes(semantic_public), _PUBLIC_MODE, "public"
            ),
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, GROUP_PUBLIC_FILENAME),
                _canonical_bytes(group_public), _PUBLIC_MODE, "public"
            ),
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, GROUP_MANIFEST_FILENAME),
                _canonical_bytes(group_manifest), _PUBLIC_MODE, "public-redacted"
            ),
            _Payload(
                "{}/{}".format(PUBLIC_DIRECTORY, SOURCE_MANIFEST_FILENAME),
                source_snapshot.payload, _PUBLIC_MODE, "public-source-identity"
            ),
            _Payload(
                "{}/{}".format(PRIVATE_DIRECTORY, SEMANTIC_PRIVATE_FILENAME),
                _canonical_bytes(semantic_private), _PRIVATE_MODE, "private-owner-only"
            ),
        ]
        artifact_entries = tuple(
            (_artifact_checksum(payload), payload.visibility)
            for payload in non_manifest_payloads
        )
        bundle = _bundle_manifest(
            runtime=runtime,
            source=source_snapshot,
            artifacts=artifact_entries,
            semantic_status=semantic_public["gate_status"],
            group_digest=group_public["assignment_manifest_sha256"],
            atomic_backend=backend.name,
        )
        bundle_payload = _Payload(
            "{}/{}".format(PUBLIC_DIRECTORY, BUNDLE_MANIFEST_FILENAME),
            _canonical_bytes(bundle),
            _PUBLIC_MODE,
            "public",
        )
        all_payloads = tuple(non_manifest_payloads) + (bundle_payload,)
        _scan_public_payloads(
            all_payloads,
            trusted_root=root,
            metadata_csv=metadata,
            output_directory=output,
            inventory_private=inventory_private,
            semantic_private=semantic_private,
        )
        result = MaestroEvidenceBundleResult(
            output_directory=output,
            artifacts=tuple(item[0] for item in artifact_entries),
            bundle_manifest_sha256=sha256_bytes(bundle_payload.data),
            bundle_manifest_size_bytes=len(bundle_payload.data),
            atomic_commit_backend=backend.name,
        )
        if progress is not None:
            progress("serialize: component schemas, digests, and public sentinels verified")
        _publish_bundle(
            parent=parent,
            backend=backend,
            payloads=all_payloads,
            source_snapshot=source_snapshot,
            result=result,
            progress=progress,
        )
        if progress is not None:
            try:
                progress("complete: bundle published and parent directory synced")
            except Exception:
                pass
        return result
    finally:
        try:
            os.close(parent.descriptor)
        except OSError:
            pass


class _CanonicalArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MaestroEvidenceArgumentError(message)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _CanonicalArgumentParser(
        prog="heterodiff-maestro-evidence",
        description="Publish the frozen official MAESTRO v3 evidence bundle.",
    )
    parser.add_argument("--trusted-root", required=True)
    parser.add_argument("--metadata-csv", required=True)
    parser.add_argument("--output-directory", required=True)
    return parser


def _emit_json_line(stream: TextIO, payload: Mapping) -> None:
    stream.write(canonical_json_dumps(payload) + "\n")
    stream.flush()


def _progress_printer(stream: TextIO) -> ProgressCallback:
    def report(message: str) -> None:
        _emit_json_line(
            stream,
            {
                "event": "progress",
                "message": message,
                "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
            },
        )
    return report


def _result_status(result: MaestroEvidenceBundleResult, status: str) -> Dict[str, object]:
    return {
        "atomic_commit_backend": result.atomic_commit_backend,
        "bundle_manifest_sha256": result.bundle_manifest_sha256,
        "bundle_manifest_size_bytes": result.bundle_manifest_size_bytes,
        "output_directory": str(result.output_directory),
        "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
        "publication_status": status,
    }


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    out = sys.stdout if stdout is None else stdout
    err = sys.stderr if stderr is None else stderr
    parser = _argument_parser()
    try:
        arguments = parser.parse_args(argv)
    except MaestroEvidenceArgumentError as error:
        try:
            _emit_json_line(
                err,
                {
                    "error_type": type(error).__name__,
                    "message": str(error),
                    "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
                    "publication_status": "NOT_STARTED",
                },
            )
        except Exception:
            pass
        return 2

    progress = _progress_printer(err)
    try:
        result = run_maestro_v3_evidence_pipeline(
            trusted_root=arguments.trusted_root,
            metadata_csv=arguments.metadata_csv,
            output_directory=arguments.output_directory,
            progress=progress,
        )
    except MaestroEvidencePublishedDurabilityError as error:
        status = _result_status(error.result, "PUBLISHED_DURABILITY_UNCONFIRMED")
        status["error_type"] = type(error.cause).__name__
        status["message"] = str(error.cause)
        try:
            _emit_json_line(err, status)
        except Exception:
            pass
        return 3
    except Exception as error:
        status = {
            "error_type": type(error).__name__,
            "message": str(error),
            "pipeline_id": MAESTRO_EVIDENCE_PIPELINE_ID,
            "publication_status": "NOT_PUBLISHED_BY_THIS_RUN",
        }
        cleanup_error = getattr(error, "staging_cleanup_error", None)
        if cleanup_error is not None:
            status["staging_cleanup_error"] = repr(cleanup_error)
        try:
            _emit_json_line(err, status)
        except Exception:
            pass
        return 1

    try:
        _emit_json_line(out, _result_status(result, "PUBLISHED_DURABLE"))
    except Exception as output_error:
        status = _result_status(result, "PUBLISHED_STATUS_OUTPUT_FAILED")
        status["error_type"] = type(output_error).__name__
        status["message"] = str(output_error)
        try:
            _emit_json_line(err, status)
        except Exception:
            pass
        return 4
    return 0


__all__ = [
    "BUNDLE_MANIFEST_FILENAME",
    "GROUP_MANIFEST_FILENAME",
    "GROUP_PUBLIC_FILENAME",
    "INVENTORY_PUBLIC_FILENAME",
    "MAESTRO_EVIDENCE_PIPELINE_ID",
    "MAESTRO_EVIDENCE_PIPELINE_SPEC_SHA256",
    "MAESTRO_V3_RELEASE_INVENTORY_LIMITS",
    "MAESTRO_V3_RELEASE_RAW_LIMITS",
    "MAESTRO_V3_RELEASE_SEMANTIC_LIMITS",
    "MaestroAtomicCommitUnsupportedError",
    "MaestroEvidenceArgumentError",
    "MaestroEvidenceBundleResult",
    "MaestroEvidencePipelineError",
    "MaestroEvidencePublishedDurabilityError",
    "PRIVATE_DIRECTORY",
    "PUBLIC_DIRECTORY",
    "RAW_PUBLIC_FILENAME",
    "SEMANTIC_PRIVATE_FILENAME",
    "SEMANTIC_PUBLIC_FILENAME",
    "SOURCE_MANIFEST_FILENAME",
    "main",
    "run_maestro_v3_evidence_pipeline",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
