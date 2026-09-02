"""Pinned fresh-process worker for independent counting-gate audit checks.

The standard-library audit parent launches one worker per domain.  This worker
safe-loads the actual step-five checkpoint, reconstructs the prefix state,
replays steps six through twelve, byte-compares the complete restart manifests,
and independently derives the configuration, grid, adapter, and Torch-target
digests from the production builders.

It emits one bounded canonical PASS/HOLD object on stdout.  It creates no audit
report, executor receipt, evidence bundle, gate decision, or claim.  It shares
production builders and checkpoint validation code, so this is procedural
cross-checking rather than a cryptographic trust root.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
from typing import Mapping, Optional, Sequence, Tuple

import numpy as np
import torch

import heterodiff.cross_domain_gate.atomic_counting_training_torch as training
from heterodiff.cross_domain_gate.atomic_counting_training_torch import (
    ATOMIC_COUNTING_GATE_ID,
    AtomicCountingTrainingStep,
    M_ACG_1_TRAINING_CONFIG,
    P_ACG_1_TRAINING_CONFIG,
    adapt_counting_task_set,
    build_atomic_counting_trainer,
    build_checkpoint_bindings,
    configure_atomic_counting_deterministic_runtime,
    load_atomic_counting_checkpoint,
    local_gate_external_digests,
    training_manifest_bytes,
)
from heterodiff.cross_domain_gate.counting_windows import (
    build_m_acg_1_task_set,
    build_p_acg_1_task_set,
)
from heterodiff.data.cross_domain_counting_fixtures import (
    build_m_acg_1,
    build_p_acg_1,
)


AUDIT_WORKER_SCHEMA = "heterodiff-cross-domain-audit-worker-v1"
RUN_RECEIPT_SCHEMA = "heterodiff-cross-domain-completed-run-receipt-v1"
MAX_JSON_BYTES = 256 * 1024 * 1024
MAX_RECEIPT_BYTES = 2 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024

COMPARISON_FIELDS = (
    "step_losses_float32_bytes",
    "model_parameters_float32_bytes",
    "optimizer_state",
    "scheduler_state",
    "completed_step",
    "ordered_task_sampler_state",
    "corruption_generator_state",
    "global_cpu_torch_rng_state",
)


class AtomicCountingAuditWorkerError(RuntimeError):
    """A worker input or independently checked invariant failed."""


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AtomicCountingAuditWorkerError(
            "value is not canonical JSON"
        ) from error


def _strict_json_bytes(raw: bytes, *, name: str) -> object:
    def reject_constant(value: str) -> None:
        raise AtomicCountingAuditWorkerError(
            "{} contains non-standard JSON constant {}".format(name, value)
        )

    def object_pairs(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise AtomicCountingAuditWorkerError(
                    "{} contains duplicate key {!r}".format(name, key)
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AtomicCountingAuditWorkerError(
            "{} is not strict JSON".format(name)
        ) from error
    if _canonical_json_bytes(value) != raw:
        raise AtomicCountingAuditWorkerError(
            "{} is not exact canonical JSON".format(name)
        )
    return value


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _read_bounded(path: Path, *, limit: int, name: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise AtomicCountingAuditWorkerError(
            "{} cannot be opened".format(name)
        ) from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise AtomicCountingAuditWorkerError(
                "{} must be a nonempty regular file".format(name)
            )
        if before.st_size > limit:
            raise AtomicCountingAuditWorkerError(
                "{} exceeds its byte ceiling".format(name)
            )
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingAuditWorkerError(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingAuditWorkerError(
                "{} grew while reading".format(name)
            )
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise AtomicCountingAuditWorkerError(
                "{} changed while reading".format(name)
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _load_json(path: Path, *, limit: int, name: str) -> Tuple[bytes, dict]:
    raw = _read_bounded(path, limit=limit, name=name)
    value = _strict_json_bytes(raw, name=name)
    if type(value) is not dict:
        raise AtomicCountingAuditWorkerError(
            "{} must contain one object".format(name)
        )
    return raw, value


def _configuration_payload_digest(fixture) -> str:
    configuration = fixture.configuration
    configuration.validate()
    if configuration.observed is None:
        raise AtomicCountingAuditWorkerError("configuration observation state is absent")
    events = []
    for event, observation in zip(
        configuration.events, configuration.observed.events
    ):
        events.append(
            {
                "event_time": event.event_time,
                "event_type": event.event_type,
                "marks": {
                    name: list(values)
                    for name, values in sorted(event.marks.items())
                },
                "source_observed_marks": sorted(observation.observed_marks),
                "source_time_observed": observation.time_observed,
                "source_type_observed": observation.type_observed,
            }
        )
    return _domain_digest(
        "heterodiff.atomic-counting.evidence-configuration-payload.v1",
        {
            "cardinality_observed": configuration.observed.cardinality_observed,
            "events": events,
            "fixture_id": fixture.fixture_id,
            "schema_version": configuration.schema.version,
        },
    )


def _grid_arrays(grid) -> Tuple[Tuple[str, np.ndarray], ...]:
    arrays = [
        ("cell_counts", grid.cell_counts),
        ("occurrence_present", grid.occurrence_present),
        ("time_observed", grid.time_observed),
        ("type_observed", grid.type_observed),
    ]
    for mapping_name, mapping in (
        ("mark_values", grid.mark_values),
        ("mark_applicable", grid.mark_applicable),
        ("mark_present", grid.mark_present),
        ("mark_observed", grid.mark_observed),
    ):
        arrays.extend(
            ("{}.{}".format(mapping_name, name), value)
            for name, value in sorted(mapping.items())
        )
    return tuple(arrays)


def _grid_payload_digest(grid) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff.atomic-counting.evidence-grid-payload.v1\x00")
    header = _canonical_json_bytes(
        {
            "cardinality_observed": grid.cardinality_observed,
            "number_of_event_types": grid.number_of_event_types,
            "number_of_time_atoms": grid.number_of_time_atoms,
            "slot_capacity": grid.slot_capacity,
        }
    )
    digest.update(len(header).to_bytes(8, "big"))
    digest.update(header)
    for name, value in _grid_arrays(grid):
        contiguous = np.array(value, copy=True, order="C")
        if contiguous.dtype.kind == "f":
            if np.any(~np.isfinite(contiguous)):
                raise AtomicCountingAuditWorkerError(
                    "grid contains a nonfinite floating value"
                )
            contiguous[contiguous == 0.0] = 0.0
        metadata = _canonical_json_bytes(
            {
                "dtype": contiguous.dtype.str,
                "name": name,
                "shape": list(contiguous.shape),
            }
        )
        raw = contiguous.tobytes(order="C")
        digest.update(len(metadata).to_bytes(8, "big"))
        digest.update(metadata)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _schema_payload(schema) -> Mapping[str, object]:
    """Rebuild the reference schema payload without its digest helper."""

    reference = schema.time_reference
    if reference is None:
        raise AtomicCountingAuditWorkerError("reference schema has no time axis")
    return {
        "allow_simultaneous": schema.allow_simultaneous,
        "event_types": [
            {
                "fields": [
                    {
                        "dimension": field.dimension,
                        "lower": field.lower,
                        "name": field.name,
                        "support": field.support.value,
                        "unit": field.unit,
                        "upper": field.upper,
                    }
                    for field in event_type.fields
                ],
                "name": event_type.name,
                "type_id": event_type.type_id,
            }
            for event_type in schema.event_types
        ],
        "horizon": schema.horizon,
        "multiplicity_mode": schema.multiplicity_mode.value,
        "time_measure": schema.time_measure.value,
        "time_reference": {
            "atom_weights": list(reference.atom_weights),
            "atoms": list(reference.atoms),
            "continuous_weight": reference.continuous_weight,
            "kind": reference.kind.value,
        },
        "version": schema.version,
    }


def _coordinate_axes(schema) -> Tuple[Tuple[Tuple[str, int], ...], ...]:
    native_dimensions = {}
    transformed_dimensions = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            native_dimensions[field.name] = max(
                native_dimensions.get(field.name, 0), field.dimension
            )
            transformed_dimensions[field.name] = max(
                transformed_dimensions.get(field.name, 0),
                field.transformed_dimension,
            )
    native = tuple(
        (name, coordinate)
        for name in sorted(native_dimensions)
        for coordinate in range(native_dimensions[name])
    )
    transformed = tuple(
        (name, coordinate)
        for name in sorted(transformed_dimensions)
        for coordinate in range(transformed_dimensions[name])
    )
    return native, transformed


def _array_digest_update(digest, name: str, value: object) -> None:
    if type(value) is not np.ndarray:
        raise AtomicCountingAuditWorkerError(
            "adapter state contains a non-array payload"
        )
    contiguous = np.array(value, copy=True, order="C")
    if contiguous.dtype.kind == "f" and np.any(~np.isfinite(contiguous)):
        raise AtomicCountingAuditWorkerError(
            "adapter state contains a nonfinite floating value"
        )
    metadata = _canonical_json_bytes(
        {
            "dtype": contiguous.dtype.str,
            "name": name,
            "shape": list(contiguous.shape),
        }
    )
    raw = contiguous.tobytes(order="C")
    digest.update(len(metadata).to_bytes(8, "big"))
    digest.update(metadata)
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)


def _adapter_state_digest(target) -> str:
    """Recompute the complete identifier-free adapter state from arrays."""

    layout = target.layout
    schema = layout.schema
    native, transformed = _coordinate_axes(schema)
    reference = schema.time_reference
    if reference is None:
        raise AtomicCountingAuditWorkerError("adapter layout has no time axis")
    schema_digest = _domain_digest(
        "heterodiff.atomic-counting-reference.schema.v1",
        _schema_payload(schema),
    )
    layout_digest = _domain_digest(
        "heterodiff.atomic-counting-reference.layout.v1",
        {
            "field_coordinates": [list(item) for item in native],
            "native_atom_count": len(reference.atoms),
            "reference_length": layout.reference_length,
            "schema_digest": schema_digest,
            "schema_version": "heterodiff-atomic-counting-reference-layout-v1",
            "slot_capacity": layout.slot_capacity,
            "transformed_coordinates": [list(item) for item in transformed],
            "type_ids": [item.type_id for item in schema.event_types],
        },
    )
    if (
        tuple(layout.field_coordinates) != native
        or tuple(layout.transformed_coordinates) != transformed
    ):
        raise AtomicCountingAuditWorkerError(
            "independent and adapter coordinate axes differ"
        )
    digest = hashlib.sha256()
    digest.update(b"heterodiff.atomic-counting-reference.state.v1\x00")
    header = _canonical_json_bytes(
        {
            "cardinality_observed": target.cardinality_observed,
            "layout_digest": layout_digest,
            "schema_version": "heterodiff-atomic-counting-reference-state-v1",
        }
    )
    digest.update(len(header).to_bytes(8, "big"))
    digest.update(header)
    for name in (
        "exact_counts",
        "occurrence_present",
        "clean_presence",
        "native_mark_values",
        "transformed_mark_values",
        "structural_applicability",
        "source_observed",
        "transformed_clean_presence",
        "transformed_structural_applicability",
        "transformed_source_observed",
        "time_observed",
        "type_observed",
        "valid_time_mask",
        "position_coordinates",
    ):
        _array_digest_update(digest, name, getattr(target, name))
    return digest.hexdigest()


def _torch_target_payload_digest(tasks) -> str:
    """Recompute the exact dense CPU tensors without the production helper."""

    tensor_names = (
        "clean_count",
        "clean_presence",
        "transformed_mark",
        "structural_applicable",
        "source_observed",
        "valid_time",
        "anchor_count",
        "anchor_count_observed",
    )
    task_records = []
    for task_id, target in zip(tasks.task_ids, tasks.targets):
        tensors = []
        for name in tensor_names:
            value = getattr(target, name)
            if (
                type(value) is not torch.Tensor
                or value.device.type != "cpu"
                or value.layout != torch.strided
            ):
                raise AtomicCountingAuditWorkerError(
                    "Torch target is not an exact dense CPU tensor"
                )
            contiguous = value.detach().clone().contiguous()
            if contiguous.is_floating_point() and not bool(
                torch.isfinite(contiguous).all().item()
            ):
                raise AtomicCountingAuditWorkerError(
                    "Torch target contains a nonfinite floating value"
                )
            tensors.append(
                {
                    "data_sha256": hashlib.sha256(
                        contiguous.numpy().tobytes(order="C")
                    ).hexdigest(),
                    "dtype": str(contiguous.dtype).removeprefix("torch."),
                    "name": name,
                    "shape": list(contiguous.shape),
                }
            )
        task_records.append({"task_id": task_id, "tensors": tensors})
    config = tasks.config
    model_shape = [
        config.reference_positions,
        config.number_of_event_types,
        config.slot_capacity,
        config.number_of_presence_coordinates,
        config.number_of_continuous_coordinates,
        list(config.continuous_presence_indices),
    ]
    if _canonical_json_bytes(model_shape) != _canonical_json_bytes(
        list(config.shape_signature)
    ):
        raise AtomicCountingAuditWorkerError(
            "independent and Torch model shape signatures differ"
        )
    return _domain_digest(
        "heterodiff.atomic-counting-target-tensor-payload.v1",
        {
            "format": "heterodiff-atomic-counting-target-tensor-payload-v1",
            "model_shape": model_shape,
            "tasks": task_records,
        },
    )


def _scalar(value: object, *, name: str) -> torch.Tensor:
    if type(value) is not dict or set(value) != {"data_hex", "dtype", "shape"}:
        raise AtomicCountingAuditWorkerError("{} is not a tensor scalar".format(name))
    if value["dtype"] != "float32" or value["shape"] != []:
        raise AtomicCountingAuditWorkerError("{} has the wrong dtype/shape".format(name))
    try:
        raw = bytes.fromhex(value["data_hex"])
    except (TypeError, ValueError) as error:
        raise AtomicCountingAuditWorkerError("{} bytes are invalid".format(name)) from error
    if len(raw) != 4:
        raise AtomicCountingAuditWorkerError("{} byte length is invalid".format(name))
    number = struct.unpack("<f", raw)[0]
    if not math.isfinite(number):
        raise AtomicCountingAuditWorkerError("{} is nonfinite".format(name))
    result = torch.tensor(number, dtype=torch.float32, device="cpu")
    if result.detach().numpy().tobytes(order="C") != raw:
        raise AtomicCountingAuditWorkerError("{} changed float32 bytes".format(name))
    return result


def _prefix_records(value: Mapping[str, object]) -> Tuple[AtomicCountingTrainingStep, ...]:
    records = value.get("step_records")
    if type(records) is not list or len(records) != 5:
        raise AtomicCountingAuditWorkerError(
            "prefix manifest must contain exactly five records"
        )
    result = []
    for expected_step, record in enumerate(records, start=1):
        if type(record) is not dict:
            raise AtomicCountingAuditWorkerError("prefix step record is invalid")
        result.append(
            AtomicCountingTrainingStep(
                completed_step=record["completed_step"],
                task_index=record["task_index"],
                task_id=record["task_id"],
                total_loss=_scalar(record["total_loss"], name="total_loss"),
                count_loss=_scalar(record["count_loss"], name="count_loss"),
                presence_loss=_scalar(
                    record["presence_loss"], name="presence_loss"
                ),
                continuous_loss=_scalar(
                    record["continuous_loss"], name="continuous_loss"
                ),
                occupied_count=record["occupied_count"],
                empty_count=record["empty_count"],
                present_count=record["present_count"],
                absent_count=record["absent_count"],
                continuous_count=record["continuous_count"],
            )
        )
        if result[-1].completed_step != expected_step:
            raise AtomicCountingAuditWorkerError(
                "prefix records are not consecutive"
            )
    return tuple(result)


def _build(domain: str):
    if domain == "music":
        fixture = build_m_acg_1()
        task_set = build_m_acg_1_task_set()
        config = M_ACG_1_TRAINING_CONFIG
    elif domain == "clinical_style":
        fixture = build_p_acg_1()
        task_set = build_p_acg_1_task_set()
        config = P_ACG_1_TRAINING_CONFIG
    else:
        raise AtomicCountingAuditWorkerError("unknown domain")
    tasks = adapt_counting_task_set(task_set)
    bindings = build_checkpoint_bindings(
        tasks,
        config,
        external_digests=dict(local_gate_external_digests()),
    )
    return fixture, task_set, tasks, config, bindings


def _trainer(tasks, config, bindings):
    return build_atomic_counting_trainer(tasks, config, bindings)


def _state_bytes(trainer) -> bytes:
    return training_manifest_bytes(trainer, ())


def _negative_checkpoint_probes(
    checkpoint_raw: bytes,
    checkpoint_path: Path,
    checkpoint_sha: str,
    tasks,
    config,
    bindings,
) -> None:
    with tempfile.TemporaryDirectory(prefix="atomic-counting-audit-probe-") as directory:
        root = Path(directory)
        attacks = {}
        attacks["appended"] = checkpoint_raw + b"appended"
        payload_bytes = training._parse_checkpoint_container(checkpoint_raw)
        payload = training._decode_checkpoint_payload(
            payload_bytes, MAX_CHECKPOINT_BYTES
        )
        payload = copy.deepcopy(payload)
        payload["gate_id"] = ATOMIC_COUNTING_GATE_ID + "-mutated"
        attacks["canonical-rewrap"] = training._checkpoint_container(
            training._torch_payload_bytes(payload)
        )
        for name, raw in attacks.items():
            path = root / (name + ".ckpt")
            path.write_bytes(raw)
            probe = _trainer(tasks, config, bindings)
            before = _state_bytes(probe)
            try:
                load_atomic_counting_checkpoint(
                    probe,
                    path,
                    expected_sha256=hashlib.sha256(raw).hexdigest(),
                    minimum_step_exclusive=0,
                )
            except training.AtomicCountingCheckpointError:
                pass
            else:
                raise AtomicCountingAuditWorkerError(
                    "{} checkpoint attack was accepted".format(name)
                )
            if _state_bytes(probe) != before:
                raise AtomicCountingAuditWorkerError(
                    "{} checkpoint attack mutated live state".format(name)
                )
        probe = _trainer(tasks, config, bindings)
        before = _state_bytes(probe)
        wrong_sha = "0" * 64 if checkpoint_sha != "0" * 64 else "1" * 64
        try:
            load_atomic_counting_checkpoint(
                probe,
                checkpoint_path,
                expected_sha256=wrong_sha,
                minimum_step_exclusive=0,
            )
        except training.AtomicCountingCheckpointError:
            pass
        else:
            raise AtomicCountingAuditWorkerError(
                "checkpoint load accepted the wrong external SHA"
            )
        if _state_bytes(probe) != before:
            raise AtomicCountingAuditWorkerError(
                "wrong-SHA checkpoint probe mutated live state"
            )


def _validate_receipt(
    receipt: Mapping[str, object],
    *,
    domain: str,
    artifact_digests: Mapping[str, str],
    artifact_sizes: Mapping[str, int],
    bindings,
) -> None:
    if (
        receipt.get("schema_version") != RUN_RECEIPT_SCHEMA
        or receipt.get("artifact_kind") != "completed-training-run"
        or receipt.get("domain") != domain
        or receipt.get("gate_id") != ATOMIC_COUNTING_GATE_ID
        or receipt.get("synthetic_test_only") is not False
    ):
        raise AtomicCountingAuditWorkerError("receipt identity is not production")
    if receipt.get("checkpoint_bindings") != bindings.as_dict():
        raise AtomicCountingAuditWorkerError(
            "receipt checkpoint bindings differ from independent reconstruction"
        )
    artifacts = receipt.get("artifacts")
    if type(artifacts) is not dict or set(artifacts) != set(artifact_digests):
        raise AtomicCountingAuditWorkerError("receipt artifact inventory is invalid")
    for name, digest in artifact_digests.items():
        if artifacts[name] != {
            "sha256": digest,
            "size_bytes": artifact_sizes[name],
        }:
            raise AtomicCountingAuditWorkerError(
                "receipt does not bind {}".format(name)
            )


def audit_domain(
    *,
    domain: str,
    continuous_path: Path,
    prefix_path: Path,
    resumed_path: Path,
    checkpoint_path: Path,
    receipt_path: Path,
) -> Mapping[str, object]:
    configure_atomic_counting_deterministic_runtime()
    continuous_raw, continuous = _load_json(
        continuous_path, limit=MAX_JSON_BYTES, name="continuous manifest"
    )
    prefix_raw, prefix = _load_json(
        prefix_path, limit=MAX_JSON_BYTES, name="prefix manifest"
    )
    resumed_raw, resumed = _load_json(
        resumed_path, limit=MAX_JSON_BYTES, name="resumed manifest"
    )
    checkpoint_raw = _read_bounded(
        checkpoint_path, limit=MAX_CHECKPOINT_BYTES, name="checkpoint"
    )
    _receipt_raw, receipt = _load_json(
        receipt_path, limit=MAX_RECEIPT_BYTES, name="run receipt"
    )
    artifacts = {
        "checkpoint": checkpoint_raw,
        "continuous_manifest": continuous_raw,
        "prefix_manifest": prefix_raw,
        "resumed_manifest": resumed_raw,
    }
    artifact_digests = {
        name: hashlib.sha256(raw).hexdigest()
        for name, raw in sorted(artifacts.items())
    }
    artifact_sizes = {name: len(raw) for name, raw in artifacts.items()}

    fixture, task_set, tasks, config, bindings = _build(domain)
    _validate_receipt(
        receipt,
        domain=domain,
        artifact_digests=artifact_digests,
        artifact_sizes=artifact_sizes,
        bindings=bindings,
    )
    checkpoint_sha = artifact_digests["checkpoint"]
    _negative_checkpoint_probes(
        checkpoint_raw,
        checkpoint_path,
        checkpoint_sha,
        tasks,
        config,
        bindings,
    )

    trainer = _trainer(tasks, config, bindings)
    restored_step = load_atomic_counting_checkpoint(
        trainer,
        checkpoint_path,
        expected_sha256=checkpoint_sha,
        minimum_step_exclusive=0,
        expected_parent_checkpoint_sha256="genesis",
    )
    if (
        restored_step != 5
        or trainer.completed_step != 5
        or trainer.last_restored_checkpoint_sha256 != checkpoint_sha
    ):
        raise AtomicCountingAuditWorkerError(
            "safe checkpoint restore did not produce exact step-five state"
        )
    records = _prefix_records(prefix)
    if training_manifest_bytes(trainer, records) != prefix_raw:
        raise AtomicCountingAuditWorkerError(
            "safe-loaded checkpoint does not reconstruct the prefix manifest"
        )
    if prefix.get("step_records") != continuous.get("step_records", [])[:5]:
        raise AtomicCountingAuditWorkerError(
            "prefix records differ from the continuous first five steps"
        )
    replay_records = records + trainer.train_until(12)
    replay_raw = training_manifest_bytes(trainer, replay_records)
    if replay_raw != resumed_raw or replay_raw != continuous_raw:
        raise AtomicCountingAuditWorkerError(
            "fresh safe-load replay is not byte-identical to both final manifests"
        )
    if continuous != resumed:
        raise AtomicCountingAuditWorkerError(
            "continuous and resumed parsed manifests differ"
        )
    compared = {
        "step_losses_float32_bytes": continuous["step_records"],
        "model_parameters_float32_bytes": continuous["model_state"],
        "optimizer_state": continuous["optimizer_state"],
        "scheduler_state": continuous["scheduler_state"],
        "completed_step": continuous["completed_step"],
        "ordered_task_sampler_state": continuous["sampler_state"],
        "corruption_generator_state": continuous["corruption_generator_state"],
        "global_cpu_torch_rng_state": continuous["global_torch_rng_state"],
    }
    replay_parsed = _strict_json_bytes(replay_raw, name="replayed manifest")
    replay_compared = {
        "step_losses_float32_bytes": replay_parsed["step_records"],
        "model_parameters_float32_bytes": replay_parsed["model_state"],
        "optimizer_state": replay_parsed["optimizer_state"],
        "scheduler_state": replay_parsed["scheduler_state"],
        "completed_step": replay_parsed["completed_step"],
        "ordered_task_sampler_state": replay_parsed["sampler_state"],
        "corruption_generator_state": replay_parsed["corruption_generator_state"],
        "global_cpu_torch_rng_state": replay_parsed["global_torch_rng_state"],
    }
    if tuple(compared) != COMPARISON_FIELDS or compared != replay_compared:
        raise AtomicCountingAuditWorkerError(
            "one or more frozen replay fields differ"
        )

    grid = fixture.to_atomic_counting_grid(max_occurrences_per_cell=2)
    adapter_digest = _adapter_state_digest(task_set.target)
    tensor_digest = _torch_target_payload_digest(tasks)
    binding_values = bindings.as_dict()
    if (
        adapter_digest != task_set.target.state_digest
        or adapter_digest != tasks.target_state_digest
        or binding_values.get("converted_state") != adapter_digest
        or binding_values.get("tensor") != tensor_digest
    ):
        raise AtomicCountingAuditWorkerError(
            "independent adapter/Torch digests differ from checkpoint bindings"
        )
    inventory = {
        "adapter_target_state_sha256": adapter_digest,
        "configuration_payload_sha256": _configuration_payload_digest(fixture),
        "grid_tensor_payload_sha256": _grid_payload_digest(grid),
        "torch_target_payload_sha256": tensor_digest,
    }
    if len(set(inventory.values())) != len(inventory):
        raise AtomicCountingAuditWorkerError(
            "independent digest inventory contains aliases"
        )
    first_post_restore = replay_records[5]
    return {
        "artifact_digests": artifact_digests,
        "checkpoint_integrity": {
            "bindings_validated_before_mutation": True,
            "canonical_rewrap_rejected": True,
            "container_no_trailing_bytes": True,
            "decoder": "torch.load(weights_only=True)",
            "expected_sha_required": True,
            "failure_atomicity_verified": True,
            "parent_checkpoint_sha256": "genesis",
            "payload_completed_step": 5,
            "restore_step_range": [6, 12],
            "save_step": 5,
        },
        "checkpoint_replay": {
            "compared_step_range": [1, 12],
            "comparison_fields": list(COMPARISON_FIELDS),
            "comparison_status": "BITWISE_EQUAL",
            "continuous_manifest_sha256": artifact_digests[
                "continuous_manifest"
            ],
            "first_post_restore_step": first_post_restore.completed_step,
            "first_post_restore_task_id": first_post_restore.task_id,
            "resumed_manifest_sha256": artifact_digests["resumed_manifest"],
        },
        "domain": domain,
        "gate_id": ATOMIC_COUNTING_GATE_ID,
        "independent_digest_inventory": inventory,
        "schema_version": AUDIT_WORKER_SCHEMA,
        "status": "PASS",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="pinned independent atomic-counting audit worker"
    )
    parser.add_argument(
        "--domain", choices=("music", "clinical_style"), required=True
    )
    parser.add_argument("--continuous", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--resumed", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser


def main(arguments: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        result = audit_domain(
            domain=args.domain,
            continuous_path=args.continuous,
            prefix_path=args.prefix,
            resumed_path=args.resumed,
            checkpoint_path=args.checkpoint,
            receipt_path=args.receipt,
        )
        sys.stdout.buffer.write(_canonical_json_bytes(result))
        sys.stdout.buffer.flush()
        return 0
    except Exception as error:
        payload = {
            "error_type": type(error).__name__,
            "message": str(error),
            "schema_version": AUDIT_WORKER_SCHEMA,
            "status": "HOLD",
        }
        sys.stdout.buffer.write(_canonical_json_bytes(payload))
        sys.stdout.buffer.flush()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["AtomicCountingAuditWorkerError", "audit_domain", "main"]
