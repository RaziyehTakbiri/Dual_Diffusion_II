"""Durable metric barrier for the 48 frozen sampled primary learners.

Importing this module uses only the Python standard library and performs no
evaluation.  The sole public construction boundary accepts the loader-only
48-primary success set, computes both metric families itself, reopens canonical
checkpoint custody after evaluation, and commits a content-derived receipt.
Callers cannot supply metric records or metric hashes to that boundary.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import fields, is_dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import tempfile
import time
from types import MappingProxyType
from typing import Iterator, Tuple

from .finite_association_production_order import (
    DEFAULT_SOURCE_PATHS as _PRODUCTION_SOURCE_RELATIVE_PATHS,
    frozen_production_source_manifest,
)


# Version 2 is the first structurally framed encoding.  Its NumPy-scalar
# framing was finalized before any v2 receipt or artifact directory existed.
_RECEIPT_SCHEMA = "heterodiff-a1-primary-metric-receipt-v2"
_CONFIGURATION_SCHEMA = "heterodiff-a1-primary-metric-configuration-v2"
_SOURCE_SCHEMA = "heterodiff-a1-primary-metric-source-v2"
_MEMBER_SCHEMA = "heterodiff-a1-primary-metric-member-v2"
_ORDERED_METRICS_SCHEMA = "heterodiff-a1-primary-ordered-metrics-v2"
_NONPATH_DECISION_VALUES_SCHEMA = (
    "heterodiff-a1-primary-nonpath-decision-values-v2"
)
_PATH_DECISION_VALUES_SCHEMA = "heterodiff-a1-primary-path-decision-values-v2"
_FLOAT_VALUE_SCHEMA = "heterodiff-a1-primary-python-float-v2"
_FLOAT_VECTOR_SCHEMA = "heterodiff-a1-primary-float64-vector-v2"
_RECEIPT_FILE = "primary-metric-receipt.json"
_MAXIMUM_RECEIPT_BYTES = 1024 * 1024
_MAXIMUM_STALE_METRIC_TEMPORARIES = 64
_SOURCE_FILES = tuple(_PRODUCTION_SOURCE_RELATIVE_PATHS)
_MEMBER_FIELDS = frozenset(
    (
        "schema",
        "ordinal",
        "seed",
        "budget",
        "method",
        "run_key_sha256",
        "success_receipt_sha256",
        "optimizer_completion_receipt_sha256",
        "parameter_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "feature_sha256",
        "reference_set_sha256",
        "nonpath_content_sha256",
        "path_content_sha256",
        "nonpath_decision_values",
        "nonpath_decision_values_sha256",
        "path_decision_values",
        "path_decision_values_sha256",
        "metric_pair_sha256",
    )
)
_RECEIPT_FIELDS = frozenset(
    (
        "schema",
        "campaign_sha256",
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "execution_runtime_sha256",
        "primary_coordinate_manifest_sha256",
        "primary_ordered_success_receipts_sha256",
        "primary_ordered_checkpoint_sha256",
        "primary_success_set_sha256",
        "metric_source_sha256",
        "metric_configuration_sha256",
        "metric_runtime_contract_sha256",
        "metric_runtime_observation",
        "metric_runtime_observation_sha256",
        "reference_set_sha256",
        "ordered_metric_records",
        "ordered_metric_records_sha256",
        "coordinate_count",
        "evaluation_started_unix_ns",
        "evaluation_completed_unix_ns",
        "freshly_computed",
        "post_evaluation_revalidated",
        "execution_order_attested",
        "scientific_decision_eligible",
        "primary_metric_receipt_sha256",
    )
)


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return encoded.encode("ascii")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _lower_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _split_metric_runtime_observation(value: object) -> tuple[dict, str]:
    if type(value) is not dict:
        raise TypeError("metric runtime observation must be an exact dictionary")
    from heterodiff.experiments.finite_association_production_order import (
        validate_production_runtime_observation,
    )

    checked = validate_production_runtime_observation(value)
    body = dict(checked)
    claimed = body.pop("runtime_observation_sha256")
    return body, claimed


def frozen_association_primary_metric_source_sha256() -> str:
    """Hash the complete source closure used by this metric boundary."""

    repository = Path(__file__).resolve().parents[3]
    manifest = frozen_production_source_manifest(repository)
    if tuple(item["path"] for item in manifest["files"]) != _SOURCE_FILES:
        raise RuntimeError("primary metric source closure changed while hashing")
    return _sha256_json(
        {
            "schema": _SOURCE_SCHEMA,
            "production_source_manifest_sha256": manifest[
                "source_manifest_sha256"
            ],
            "files": manifest["files"],
        }
    )


def frozen_association_primary_metric_configuration_sha256(
    *, metric_source_sha256: object,
) -> str:
    """Return the code-bound, argument-free metric configuration identity."""

    return _sha256_json(
        {
            "schema": _CONFIGURATION_SCHEMA,
            "metric_source_sha256": _lower_sha256(
                metric_source_sha256, name="metric_source_sha256"
            ),
            "coordinate_manifest": "48-direct-guided-interleaved-v1",
            "nonpath_evaluator": "frozen-33-knot-v1",
            "path_evaluator": "all-21-primary-and-refined-v1",
            "metric_content_encoding": "typed-stream-v2",
            "decision_value_encoding": "typed-canonical-json-v2",
            "metric_runtime_preflight": "production-runtime-observation-v1",
            "pre_and_post_source_runtime_match": True,
            "post_evaluation_revalidation": True,
        }
    )


def frozen_association_primary_metric_directory() -> Path:
    """Return the one repository-local location for the primary receipt."""

    return (
        Path(__file__).resolve().parents[3]
        / "artifacts"
        / "a1_primary_metrics_v2"
    )


def _metric_content_sha256(value: object) -> str:
    """Hash an exact typed metric record without accepting a claimed digest."""

    import numpy as np

    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-primary-metric-typed-stream-v2\0")

    def emit_bytes(tag: bytes, payload: bytes) -> None:
        digest.update(tag)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)

    def emit(item: object) -> None:
        if item is None:
            digest.update(b"N")
        elif type(item) is bool:
            digest.update(b"B1" if item else b"B0")
        elif isinstance(item, np.generic):
            if item.dtype.hasobject:
                raise TypeError("NumPy metric scalars must not contain objects")
            digest.update(b"G")
            emit_bytes(b"Q", item.dtype.str.encode("ascii"))
            emit_bytes(b"D", item.tobytes())
        elif type(item) is int:
            emit_bytes(b"I", str(item).encode("ascii"))
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError("metric content contains a non-finite scalar")
            emit_bytes(b"F", item.hex().encode("ascii"))
        elif type(item) is str:
            emit_bytes(b"S", item.encode("utf-8"))
        elif type(item) is bytes:
            emit_bytes(b"Y", item)
        elif type(item) is np.ndarray:
            if item.dtype.hasobject:
                raise TypeError("metric arrays must not have object dtype")
            contiguous = np.ascontiguousarray(item)
            emit_bytes(b"A", contiguous.dtype.str.encode("ascii"))
            emit(tuple(int(size) for size in contiguous.shape))
            emit_bytes(b"D", contiguous.tobytes(order="C"))
        elif type(item) is tuple:
            digest.update(b"T")
            digest.update(len(item).to_bytes(8, "big"))
            for nested in item:
                emit(nested)
        elif type(item) is list:
            digest.update(b"L")
            digest.update(len(item).to_bytes(8, "big"))
            for nested in item:
                emit(nested)
        elif type(item) is dict:
            if not all(type(key) is str for key in item):
                raise TypeError("metric mappings require string keys")
            digest.update(b"M")
            digest.update(len(item).to_bytes(8, "big"))
            for key in sorted(item):
                emit(key)
                emit(item[key])
        elif is_dataclass(item) and not isinstance(item, type):
            record_type = type(item)
            record_fields = fields(item)
            emit_bytes(
                b"C",
                (record_type.__module__ + "." + record_type.__qualname__).encode(
                    "utf-8"
                ),
            )
            digest.update(len(record_fields).to_bytes(8, "big"))
            for field in record_fields:
                emit(field.name)
                emit(getattr(item, field.name))
        else:
            raise TypeError(
                "unsupported metric content type %s" % type(item).__name__
            )

    emit(value)
    return digest.hexdigest()


_MASKED_VALUE_NAMES = (
    "train",
    "validation",
    "joint_interpolation",
    "time_interpolation",
    "pair_interpolation",
    "latent_three",
    "anchor_three",
    "both_three",
    "overflow",
    "balanced_ood",
)
_CENTERED_VALUE_NAMES = (
    "physical_weighted_rmse",
    "maximum_absolute_error",
)
_RESIDUAL_VALUE_NAMES = (
    "physical_weighted_rmse",
    "maximum_absolute_error",
    "candidate_minimum",
    "candidate_maximum",
    "candidate_range",
    "oracle_minimum",
    "oracle_maximum",
    "oracle_range",
)
_EDGE_VALUE_NAMES = (
    "physical_weight",
    "physical_weighted_rmse",
    "maximum_absolute_error",
    "weighted_median_absolute_error",
)
_CONDITIONAL_TV_VALUE_NAMES = (
    "observation_weighted_mean",
    "retained_observation_weighted_mean",
    "maximum",
    "overflow",
)
_CALIBRATION_VALUE_NAMES = (
    "brier",
    "optimal_brier",
    "excess_brier",
    "reliability_ece",
    "maximum_reliability_gap",
)
_COHERENCE_VALUE_NAMES = (
    "terminal_maximum_absolute_log_information_error",
    "terminal_maximum_absolute_residual",
    "generator_row_sum_maximum_absolute_residual",
    "normalization_physical_weighted_rmse",
    "normalization_maximum_absolute_residual",
    "semigroup_physical_weighted_rmse",
    "semigroup_maximum_absolute_residual",
    "edit_cycle_maximum_absolute_residual",
)
_NONPATH_DECISION_FIELDS = frozenset(
    (
        "schema",
        "masked_excess_bce",
        "centered_log_information",
        "residual",
        "edge_log_rates",
        "conditional_initial_tv",
        "calibration",
        "coherence",
    )
)
_PATH_GATE_VECTOR_NAMES = (
    "oracle_self_path_kl_per_observation",
    "unconditional_refinement_change_per_observation",
    "reference_target_marginal_error_per_observation",
    "candidate_path_refinement_change_per_observation",
    "candidate_endpoint_refinement_tv_per_observation",
    "candidate_target_marginal_error_per_observation",
)
_PATH_DECISION_FIELDS = frozenset(
    (
        "schema",
        "retained_normalized_path_score",
        "ambiguous_normalized_path_score",
        "observation_mass",
        "path_kl_per_observation",
        "normalized_path_kl_per_observation",
        "unconditional_path_kl_per_observation",
        "refined_unconditional_path_kl_per_observation",
        "numerical_gate_inputs",
        "numerical_gate_failures",
    )
)
_FLOAT_VALUE_FIELDS = frozenset(("schema", "hex"))
_FLOAT_VECTOR_FIELDS = frozenset(
    ("schema", "dtype", "shape", "values")
)


def _encoded_float(value: object, *, name: str) -> dict:
    if type(value) is not float or not math.isfinite(value):
        raise TypeError("%s must be a finite exact Python float" % name)
    return {"schema": _FLOAT_VALUE_SCHEMA, "hex": value.hex()}


def _validated_encoded_float(
    value: object, *, name: str, nonnegative: bool
) -> float:
    if type(value) is not dict or set(value) != _FLOAT_VALUE_FIELDS:
        raise RuntimeError("%s has an invalid typed-float schema" % name)
    token = value.get("hex")
    if value.get("schema") != _FLOAT_VALUE_SCHEMA or type(token) is not str:
        raise RuntimeError("%s has an invalid typed-float encoding" % name)
    try:
        decoded = float.fromhex(token)
    except ValueError as error:
        raise RuntimeError("%s has an invalid hexadecimal float" % name) from error
    if (
        not math.isfinite(decoded)
        or decoded.hex() != token
        or (nonnegative and decoded < 0.0)
    ):
        raise RuntimeError("%s has a noncanonical or invalid float" % name)
    return decoded


def _encoded_float_vector(value: object, *, name: str) -> dict:
    import numpy as np

    if type(value) is not np.ndarray:
        raise TypeError("%s must be an exact NumPy array" % name)
    if value.dtype.str != "<f8" or value.shape != (21,):
        raise TypeError("%s must be an exact little-endian float64 vector" % name)
    if not np.all(np.isfinite(value)) or np.any(value < 0.0):
        raise ValueError("%s must be finite and nonnegative" % name)
    return {
        "schema": _FLOAT_VECTOR_SCHEMA,
        "dtype": value.dtype.str,
        "shape": [21],
        "values": [float(item).hex() for item in value],
    }


def _validated_float_vector(value: object, *, name: str) -> tuple:
    if type(value) is not dict or set(value) != _FLOAT_VECTOR_FIELDS:
        raise RuntimeError("%s has an invalid typed-vector schema" % name)
    items = value.get("values")
    if (
        value.get("schema") != _FLOAT_VECTOR_SCHEMA
        or value.get("dtype") != "<f8"
        or value.get("shape") != [21]
        or type(items) is not list
        or len(items) != 21
    ):
        raise RuntimeError("%s has an invalid typed-vector encoding" % name)
    decoded = []
    for index, token in enumerate(items):
        if type(token) is not str:
            raise RuntimeError("%s[%d] is not a float token" % (name, index))
        try:
            item = float.fromhex(token)
        except ValueError as error:
            raise RuntimeError(
                "%s[%d] has an invalid hexadecimal float" % (name, index)
            ) from error
        if not math.isfinite(item) or item < 0.0 or item.hex() != token:
            raise RuntimeError(
                "%s[%d] has a noncanonical or invalid float" % (name, index)
            )
        decoded.append(item)
    return tuple(decoded)


def _encoded_float_record(value: object, names: tuple, *, label: str) -> dict:
    return {
        name: _encoded_float(getattr(value, name), name=label + "." + name)
        for name in names
    }


def _validated_float_record(
    value: object,
    names: tuple,
    *,
    label: str,
    signed: frozenset = frozenset(),
) -> dict:
    if type(value) is not dict or set(value) != set(names):
        raise RuntimeError("%s has an invalid exact schema" % label)
    return {
        name: _validated_encoded_float(
            value[name], name=label + "." + name, nonnegative=name not in signed
        )
        for name in names
    }


def _build_nonpath_decision_values(nonpath: object) -> dict:
    edges = {}
    for family in ("birth", "death", "replacement"):
        source = getattr(nonpath.edge_log_rates, family)
        edges[family] = {
            "family": source.family,
            "active_edge_count": source.active_edge_count,
            **_encoded_float_record(
                source, _EDGE_VALUE_NAMES, label="edge_log_rates." + family
            ),
        }
    return {
        "schema": _NONPATH_DECISION_VALUES_SCHEMA,
        "masked_excess_bce": _encoded_float_record(
            nonpath.masked_excess_bce,
            _MASKED_VALUE_NAMES,
            label="masked_excess_bce",
        ),
        "centered_log_information": _encoded_float_record(
            nonpath.centered_log_information,
            _CENTERED_VALUE_NAMES,
            label="centered_log_information",
        ),
        "residual": _encoded_float_record(
            nonpath.residual, _RESIDUAL_VALUE_NAMES, label="residual"
        ),
        "edge_log_rates": edges,
        "conditional_initial_tv": _encoded_float_record(
            nonpath.conditional_initial_tv,
            _CONDITIONAL_TV_VALUE_NAMES,
            label="conditional_initial_tv",
        ),
        "calibration": _encoded_float_record(
            nonpath.calibration,
            _CALIBRATION_VALUE_NAMES,
            label="calibration",
        ),
        "coherence": {
            **_encoded_float_record(
                nonpath.coherence, _COHERENCE_VALUE_NAMES, label="coherence"
            ),
            "edit_cycle_count": nonpath.coherence.edit_cycle_count,
        },
    }


def _validated_nonpath_decision_values(value: object) -> dict:
    if type(value) is not dict or set(value) != _NONPATH_DECISION_FIELDS:
        raise RuntimeError("nonpath decision values have an invalid exact schema")
    if value.get("schema") != _NONPATH_DECISION_VALUES_SCHEMA:
        raise RuntimeError("nonpath decision values have an invalid schema")
    masked = _validated_float_record(
        value["masked_excess_bce"],
        _MASKED_VALUE_NAMES,
        label="masked_excess_bce",
    )
    expected_balanced = math.fsum(
        masked[name] for name in ("latent_three", "anchor_three", "both_three", "overflow")
    ) / 4.0
    if not math.isclose(
        masked["balanced_ood"], expected_balanced, rel_tol=2.0e-13, abs_tol=2.0e-14
    ):
        raise RuntimeError("nonpath balanced OOD value is inconsistent")
    _validated_float_record(
        value["centered_log_information"],
        _CENTERED_VALUE_NAMES,
        label="centered_log_information",
    )
    residual = _validated_float_record(
        value["residual"],
        _RESIDUAL_VALUE_NAMES,
        label="residual",
        signed=frozenset(
            (
                "candidate_minimum",
                "candidate_maximum",
                "oracle_minimum",
                "oracle_maximum",
            )
        ),
    )
    for prefix in ("candidate", "oracle"):
        if residual[prefix + "_maximum"] < residual[prefix + "_minimum"] or not math.isclose(
            residual[prefix + "_range"],
            residual[prefix + "_maximum"] - residual[prefix + "_minimum"],
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise RuntimeError("nonpath %s residual range is inconsistent" % prefix)
    edges = value["edge_log_rates"]
    if type(edges) is not dict or set(edges) != {"birth", "death", "replacement"}:
        raise RuntimeError("nonpath edge values have an invalid exact schema")
    for family in ("birth", "death", "replacement"):
        record = edges[family]
        expected_fields = {"family", "active_edge_count", *_EDGE_VALUE_NAMES}
        if type(record) is not dict or set(record) != expected_fields:
            raise RuntimeError("nonpath %s edge values have an invalid schema" % family)
        count = record.get("active_edge_count")
        if record.get("family") != family or type(count) is not int or count <= 0:
            raise RuntimeError("nonpath %s edge identity is invalid" % family)
        checked_edge = _validated_float_record(
            {name: record[name] for name in _EDGE_VALUE_NAMES},
            _EDGE_VALUE_NAMES,
            label="edge_log_rates." + family,
        )
        if checked_edge["physical_weight"] <= 0.0:
            raise RuntimeError("nonpath %s physical weight is not positive" % family)
    _validated_float_record(
        value["conditional_initial_tv"],
        _CONDITIONAL_TV_VALUE_NAMES,
        label="conditional_initial_tv",
    )
    calibration = _validated_float_record(
        value["calibration"],
        _CALIBRATION_VALUE_NAMES,
        label="calibration",
    )
    if not math.isclose(
        calibration["excess_brier"],
        calibration["brier"] - calibration["optimal_brier"],
        rel_tol=2.0e-12,
        abs_tol=2.0e-14,
    ):
        raise RuntimeError("nonpath excess Brier value is inconsistent")
    coherence = value["coherence"]
    expected_coherence = set(_COHERENCE_VALUE_NAMES) | {"edit_cycle_count"}
    if type(coherence) is not dict or set(coherence) != expected_coherence:
        raise RuntimeError("nonpath coherence values have an invalid schema")
    _validated_float_record(
        {name: coherence[name] for name in _COHERENCE_VALUE_NAMES},
        _COHERENCE_VALUE_NAMES,
        label="coherence",
    )
    count = coherence.get("edit_cycle_count")
    if type(count) is not int or count <= 0:
        raise RuntimeError("nonpath edit-cycle count is invalid")
    return value


def _build_path_decision_values(path: object) -> dict:
    import numpy as np

    observations = path.observations

    def vector(getter) -> object:
        return np.asarray([getter(item) for item in observations], dtype=np.float64)

    gate_inputs = {
        "oracle_self_path_kl_per_observation": vector(
            lambda item: item.reference.oracle_self_path_kl
        ),
        "unconditional_refinement_change_per_observation": vector(
            lambda item: item.reference.primary_refined_unconditional_path_kl_change
        ),
        "reference_target_marginal_error_per_observation": vector(
            lambda item: item.reference.target_marginal_maximum_absolute_error
        ),
        "candidate_path_refinement_change_per_observation": vector(
            lambda item: item.primary_refined_path_kl_change
        ),
        "candidate_endpoint_refinement_tv_per_observation": vector(
            lambda item: item.primary_refined_endpoint_total_variation
        ),
        "candidate_target_marginal_error_per_observation": vector(
            lambda item: item.primary_target_marginal_maximum_absolute_error
        ),
    }
    return {
        "schema": _PATH_DECISION_VALUES_SCHEMA,
        "retained_normalized_path_score": _encoded_float(
            path.retained_normalized_path_score,
            name="retained_normalized_path_score",
        ),
        "ambiguous_normalized_path_score": _encoded_float(
            path.ambiguous_normalized_path_score,
            name="ambiguous_normalized_path_score",
        ),
        "observation_mass": _encoded_float_vector(
            path.observation_mass,
            name="observation_mass",
        ),
        "path_kl_per_observation": _encoded_float_vector(
            path.path_kl_per_observation,
            name="path_kl_per_observation",
        ),
        "normalized_path_kl_per_observation": _encoded_float_vector(
            path.normalized_path_kl_per_observation,
            name="normalized_path_kl_per_observation",
        ),
        "unconditional_path_kl_per_observation": _encoded_float_vector(
            path.unconditional_path_kl_per_observation,
            name="unconditional_path_kl_per_observation",
        ),
        "refined_unconditional_path_kl_per_observation": _encoded_float_vector(
            vector(lambda item: item.reference.refined_unconditional_path_kl),
            name="refined_unconditional_path_kl_per_observation",
        ),
        "numerical_gate_inputs": {
            name: _encoded_float_vector(items, name=name)
            for name, items in gate_inputs.items()
        },
        "numerical_gate_failures": list(path.numerical_gate_failures),
    }


def _validated_path_decision_values(value: object) -> dict:
    if type(value) is not dict or set(value) != _PATH_DECISION_FIELDS:
        raise RuntimeError("path decision values have an invalid exact schema")
    if value.get("schema") != _PATH_DECISION_VALUES_SCHEMA:
        raise RuntimeError("path decision values have an invalid schema")
    retained = _validated_encoded_float(
        value["retained_normalized_path_score"],
        name="retained_normalized_path_score",
        nonnegative=True,
    )
    ambiguous = _validated_encoded_float(
        value["ambiguous_normalized_path_score"],
        name="ambiguous_normalized_path_score",
        nonnegative=True,
    )
    observation_mass = _validated_float_vector(
        value["observation_mass"], name="observation_mass"
    )
    path_kl = _validated_float_vector(
        value["path_kl_per_observation"], name="path_kl_per_observation"
    )
    normalized = _validated_float_vector(
        value["normalized_path_kl_per_observation"],
        name="normalized_path_kl_per_observation",
    )
    primary_baseline = _validated_float_vector(
        value["unconditional_path_kl_per_observation"],
        name="unconditional_path_kl_per_observation",
    )
    refined_baseline = _validated_float_vector(
        value["refined_unconditional_path_kl_per_observation"],
        name="refined_unconditional_path_kl_per_observation",
    )
    if (
        any(item <= 0.0 for item in observation_mass)
        or not math.isclose(
            math.fsum(observation_mass), 1.0, rel_tol=0.0, abs_tol=2.0e-12
        )
    ):
        raise RuntimeError("path observation masses are not a positive law")
    if retained < 0.0 or any(
        item <= 1.0e-12 for item in primary_baseline + refined_baseline
    ):
        raise RuntimeError("path decision values contain an invalid normalizer")
    for index, (path_value, baseline, normalized_value) in enumerate(
        zip(path_kl, primary_baseline, normalized)
    ):
        if not math.isclose(
            normalized_value,
            path_value / baseline,
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise RuntimeError(
                "path normalized value %d is inconsistent" % index
            )
    retained_path = math.fsum(
        observation_mass[index] * path_kl[index] for index in range(20)
    )
    retained_baseline = math.fsum(
        observation_mass[index] * primary_baseline[index]
        for index in range(20)
    )
    if retained_baseline <= 0.0 or not math.isclose(
        retained,
        retained_path / retained_baseline,
        rel_tol=2.0e-13,
        abs_tol=2.0e-14,
    ):
        raise RuntimeError("path retained normalized score is inconsistent")
    expected_ambiguous = math.fsum(normalized[index] for index in (8, 7, 5)) / 3.0
    if not math.isclose(
        ambiguous, expected_ambiguous, rel_tol=2.0e-13, abs_tol=2.0e-14
    ):
        raise RuntimeError("path ambiguous normalized score is inconsistent")
    gates = value["numerical_gate_inputs"]
    if type(gates) is not dict or set(gates) != set(_PATH_GATE_VECTOR_NAMES):
        raise RuntimeError("path numerical-gate inputs have an invalid schema")
    decoded_gates = {
        name: _validated_float_vector(gates[name], name=name)
        for name in _PATH_GATE_VECTOR_NAMES
    }
    failures = value["numerical_gate_failures"]
    if type(failures) is not list or not all(
        type(item) is str and bool(item) for item in failures
    ):
        raise RuntimeError("path numerical-gate failures are invalid")
    expected_failures = []
    for index in range(21):
        messages = []
        if decoded_gates["oracle_self_path_kl_per_observation"][index] > 1.0e-10:
            messages.append("oracle self path KL exceeds 1e-10 nat")
        if decoded_gates["unconditional_refinement_change_per_observation"][index] > 1.0e-8:
            messages.append(
                "primary/refined unconditional path-KL change exceeds 1e-8 nat"
            )
        reference_target_failed = (
            decoded_gates["reference_target_marginal_error_per_observation"][index]
            > 1.0e-8
        )
        if reference_target_failed:
            messages.append("target occupancy error exceeds 1e-8")
        if decoded_gates["candidate_path_refinement_change_per_observation"][index] > 1.0e-8:
            messages.append("primary/refined path-KL change exceeds 1e-8 nat")
        if decoded_gates["candidate_endpoint_refinement_tv_per_observation"][index] > 1.0e-8:
            messages.append("primary/refined endpoint TV exceeds 1e-8")
        if (
            decoded_gates["candidate_target_marginal_error_per_observation"][index]
            > 1.0e-8
            and not reference_target_failed
        ):
            messages.append("target occupancy error exceeds 1e-8")
        expected_failures.extend(
            "observation %d: %s" % (index, message) for message in messages
        )
    if failures != expected_failures:
        raise RuntimeError("path numerical-gate failures are inconsistent")
    return value


def _freeze_decision_values(value: object) -> object:
    """Decode typed values and recursively remove every mutation surface."""

    if type(value) is dict and set(value) == _FLOAT_VALUE_FIELDS:
        return _validated_encoded_float(
            value, name="decision value", nonnegative=False
        )
    if type(value) is dict and set(value) == _FLOAT_VECTOR_FIELDS:
        decoded = _validated_float_vector(value, name="decision vector")
        return MappingProxyType(
            {
                "dtype": value["dtype"],
                "shape": tuple(value["shape"]),
                "values": decoded,
            }
        )
    if type(value) is dict:
        return MappingProxyType(
            {key: _freeze_decision_values(item) for key, item in value.items()}
        )
    if type(value) is list:
        return tuple(_freeze_decision_values(item) for item in value)
    if type(value) in (str, int, bool) or value is None:
        return value
    raise TypeError("decision values contain an unsupported immutable type")


def _metric_pair_sha256(member: dict) -> str:
    body = dict(member)
    body.pop("metric_pair_sha256", None)
    return _sha256_json(body)


def _build_metric_member(
    ordinal: int,
    coordinate: Tuple[int, int, str],
    verified_checkpoint: object,
    nonpath: object,
    path: object,
) -> dict:
    from heterodiff.evaluation.finite_association_path_evaluator import (
        FiniteAssociationPathEvaluation,
    )
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        FiniteAssociationNonPathEvaluation,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
    )

    if type(verified_checkpoint) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("metric construction requires a canonical checkpoint")
    if type(nonpath) is not FiniteAssociationNonPathEvaluation:
        raise TypeError("primary nonpath result has a noncanonical type")
    if type(path) is not FiniteAssociationPathEvaluation:
        raise TypeError("primary path result has a noncanonical type")
    _require_fitted_checkpoint_integrity(verified_checkpoint.checkpoint)
    checkpoint = verified_checkpoint.checkpoint
    if (
        checkpoint.preflight.seed,
        checkpoint.preflight.budget,
        checkpoint.preflight.method,
    ) != coordinate:
        raise RuntimeError("primary metric checkpoint order changed")
    expected = (
        checkpoint.final_snapshot.parameter_sha256,
        checkpoint.classifier_sha256,
        verified_checkpoint.success_receipt_sha256,
        verified_checkpoint.campaign_sha256,
    )
    for label, result in (("nonpath", nonpath), ("path", path)):
        observed = (
            result.parameter_sha256,
            result.classifier_sha256,
            result.execution_receipt_sha256,
            result.campaign_sha256,
        )
        if result.production_bound is not True or observed != expected:
            raise RuntimeError(
                "primary %s result is not bound to canonical SUCCESS custody"
                % label
            )
    if nonpath.feature_sha256 != checkpoint.certificate.feature_sha256:
        raise RuntimeError("primary nonpath feature identity changed")
    nonpath_decision_values = _build_nonpath_decision_values(nonpath)
    path_decision_values = _build_path_decision_values(path)
    member = {
        "schema": _MEMBER_SCHEMA,
        "ordinal": ordinal,
        "seed": coordinate[0],
        "budget": coordinate[1],
        "method": coordinate[2],
        "run_key_sha256": checkpoint.run_key_sha256,
        "success_receipt_sha256": verified_checkpoint.success_receipt_sha256,
        "optimizer_completion_receipt_sha256": (
            verified_checkpoint.optimizer_completion_receipt_sha256
        ),
        "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
        "classifier_sha256": checkpoint.classifier_sha256,
        "certificate_sha256": checkpoint.certificate.certificate_sha256,
        "feature_sha256": checkpoint.certificate.feature_sha256,
        "reference_set_sha256": path.reference_set_sha256,
        "nonpath_content_sha256": _metric_content_sha256(nonpath),
        "path_content_sha256": _metric_content_sha256(path),
        "nonpath_decision_values": nonpath_decision_values,
        "nonpath_decision_values_sha256": _sha256_json(
            nonpath_decision_values
        ),
        "path_decision_values": path_decision_values,
        "path_decision_values_sha256": _sha256_json(path_decision_values),
    }
    member["metric_pair_sha256"] = _metric_pair_sha256(member)
    return _validated_metric_member(member, ordinal=ordinal, coordinate=coordinate)


def _validated_metric_member(
    value: object, *, ordinal: int, coordinate: Tuple[int, int, str]
) -> dict:
    if type(value) is not dict or set(value) != _MEMBER_FIELDS:
        raise RuntimeError("primary metric member has an invalid exact schema")
    if (
        value.get("schema") != _MEMBER_SCHEMA
        or value.get("ordinal") != ordinal
        or (
            value.get("seed"),
            value.get("budget"),
            value.get("method"),
        )
        != coordinate
    ):
        raise RuntimeError("primary metric member order is not canonical")
    for name in (
        "run_key_sha256",
        "success_receipt_sha256",
        "optimizer_completion_receipt_sha256",
        "parameter_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "feature_sha256",
        "reference_set_sha256",
        "nonpath_content_sha256",
        "path_content_sha256",
        "nonpath_decision_values_sha256",
        "path_decision_values_sha256",
        "metric_pair_sha256",
    ):
        _lower_sha256(value.get(name), name=name)
    nonpath_values = _validated_nonpath_decision_values(
        value.get("nonpath_decision_values")
    )
    path_values = _validated_path_decision_values(
        value.get("path_decision_values")
    )
    if value["nonpath_decision_values_sha256"] != _sha256_json(nonpath_values):
        raise RuntimeError("primary nonpath decision-value digest is inconsistent")
    if value["path_decision_values_sha256"] != _sha256_json(path_values):
        raise RuntimeError("primary path decision-value digest is inconsistent")
    if value["metric_pair_sha256"] != _metric_pair_sha256(value):
        raise RuntimeError("primary metric-pair digest is inconsistent")
    return value


def _validated_metric_receipt(value: object) -> dict:
    from heterodiff.experiments.finite_association_isolated_runner import (
        _canonical_sampled_primary_coordinates,
        _primary_coordinate_manifest_sha256,
    )

    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise RuntimeError("primary metric receipt has an invalid exact schema")
    if value.get("schema") != _RECEIPT_SCHEMA:
        raise RuntimeError("primary metric receipt schema is invalid")
    for name in (
        "campaign_sha256",
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "execution_runtime_sha256",
        "primary_coordinate_manifest_sha256",
        "primary_ordered_success_receipts_sha256",
        "primary_ordered_checkpoint_sha256",
        "primary_success_set_sha256",
        "metric_source_sha256",
        "metric_configuration_sha256",
        "metric_runtime_contract_sha256",
        "metric_runtime_observation_sha256",
        "reference_set_sha256",
        "ordered_metric_records_sha256",
        "primary_metric_receipt_sha256",
    ):
        _lower_sha256(value.get(name), name=name)
    if value["primary_coordinate_manifest_sha256"] != (
        _primary_coordinate_manifest_sha256()
    ):
        raise RuntimeError("primary metric coordinate manifest changed")
    current_source = frozen_association_primary_metric_source_sha256()
    current_configuration = (
        frozen_association_primary_metric_configuration_sha256(
            metric_source_sha256=current_source
        )
    )
    if (
        value["metric_source_sha256"] != current_source
        or value["metric_configuration_sha256"] != current_configuration
    ):
        raise RuntimeError("primary metric receipt has stale source custody")
    from heterodiff.experiments.finite_association_production_order import (
        frozen_production_runtime_contract_sha256,
    )

    if value["metric_runtime_contract_sha256"] != (
        frozen_production_runtime_contract_sha256()
    ):
        raise RuntimeError("primary metric runtime contract is stale")
    runtime_observation = value.get("metric_runtime_observation")
    if type(runtime_observation) is not dict:
        raise RuntimeError("primary metric runtime custody is inconsistent")
    runtime_record = dict(runtime_observation)
    runtime_record["runtime_observation_sha256"] = value[
        "metric_runtime_observation_sha256"
    ]
    try:
        _split_metric_runtime_observation(runtime_record)
    except (TypeError, ValueError, RuntimeError) as error:
        raise RuntimeError(
            "primary metric runtime custody is inconsistent"
        ) from error
    coordinates = _canonical_sampled_primary_coordinates()
    records = value.get("ordered_metric_records")
    if type(records) is not list or len(records) != len(coordinates):
        raise RuntimeError("primary metric receipt requires exactly 48 records")
    uniqueness = {
        name: set()
        for name in (
            "run_key_sha256",
            "success_receipt_sha256",
            "optimizer_completion_receipt_sha256",
            "metric_pair_sha256",
        )
    }
    reference_sets = set()
    for ordinal, (record, coordinate) in enumerate(zip(records, coordinates)):
        checked = _validated_metric_member(
            record, ordinal=ordinal, coordinate=coordinate
        )
        reference_sets.add(checked["reference_set_sha256"])
        for name, observed in uniqueness.items():
            item = checked[name]
            if item in observed:
                raise RuntimeError("primary metric receipt reuses %s" % name)
            observed.add(item)
    if reference_sets != {value["reference_set_sha256"]}:
        raise RuntimeError("primary metric receipt mixes path reference sets")
    ordered_digest = _sha256_json(
        {"schema": _ORDERED_METRICS_SCHEMA, "records": records}
    )
    if value["ordered_metric_records_sha256"] != ordered_digest:
        raise RuntimeError("primary ordered metric digest is inconsistent")
    started = value.get("evaluation_started_unix_ns")
    completed = value.get("evaluation_completed_unix_ns")
    if (
        isinstance(started, bool)
        or type(started) is not int
        or started <= 0
        or isinstance(completed, bool)
        or type(completed) is not int
        or completed < started
    ):
        raise RuntimeError("primary metric evaluation timestamps are invalid")
    if (
        value.get("coordinate_count") != 48
        or value.get("freshly_computed") is not True
        or value.get("post_evaluation_revalidated") is not True
        or value.get("execution_order_attested") is not False
        or value.get("scientific_decision_eligible") is not False
    ):
        raise RuntimeError("primary metric receipt overstates its authority")
    body = dict(value)
    claimed = body.pop("primary_metric_receipt_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("primary metric receipt digest is inconsistent")
    return value


def _same_primary_identity(left: object, right: object) -> bool:
    names = (
        "campaign_sha256",
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "execution_runtime_sha256",
        "coordinate_manifest_sha256",
        "ordered_success_receipts_sha256",
        "ordered_checkpoint_sha256",
        "primary_success_set_sha256",
    )
    return all(getattr(left, name) == getattr(right, name) for name in names)


_PRIMARY_RECEIPT_IDENTITY_BINDINGS = (
    ("campaign_sha256", "campaign_sha256"),
    ("source_sha256", "source_sha256"),
    ("configuration_sha256", "configuration_sha256"),
    ("fixture_sha256", "fixture_sha256"),
    ("execution_runtime_sha256", "execution_runtime_sha256"),
    ("primary_coordinate_manifest_sha256", "coordinate_manifest_sha256"),
    (
        "primary_ordered_success_receipts_sha256",
        "ordered_success_receipts_sha256",
    ),
    ("primary_ordered_checkpoint_sha256", "ordered_checkpoint_sha256"),
    ("primary_success_set_sha256", "primary_success_set_sha256"),
)


def _require_receipt_matches_primary_identity(
    receipt: dict, primary: object
) -> None:
    """Reject a pre-existing receipt not bound to the admitted primary set."""

    mismatches = [
        receipt_name
        for receipt_name, primary_name in _PRIMARY_RECEIPT_IDENTITY_BINDINGS
        if receipt[receipt_name] != getattr(primary, primary_name)
    ]
    if mismatches:
        raise RuntimeError(
            "existing primary metric receipt differs from admitted primary "
            "custody: %s" % ", ".join(mismatches)
        )


def _build_metric_receipt(
    primary: object,
    records: tuple,
    *,
    metric_source_sha256: object,
    metric_configuration_sha256: object,
    metric_runtime_observation: object,
    reference_set_sha256: object,
    evaluation_started_unix_ns: int,
    evaluation_completed_unix_ns: int,
) -> dict:
    from heterodiff.experiments.finite_association_isolated_runner import (
        LedgerVerifiedFrozenAssociationPrimarySuccessSet,
    )

    if type(primary) is not LedgerVerifiedFrozenAssociationPrimarySuccessSet:
        raise TypeError("metric receipt construction requires primary admission")
    if type(records) is not tuple or len(records) != 48:
        raise TypeError("metric receipt construction requires 48 derived records")
    source_sha256 = _lower_sha256(
        metric_source_sha256, name="metric_source_sha256"
    )
    configuration_sha256 = _lower_sha256(
        metric_configuration_sha256,
        name="metric_configuration_sha256",
    )
    expected_configuration = (
        frozen_association_primary_metric_configuration_sha256(
            metric_source_sha256=source_sha256
        )
    )
    if configuration_sha256 != expected_configuration:
        raise RuntimeError("captured metric configuration is inconsistent")
    runtime_body, runtime_sha256 = _split_metric_runtime_observation(
        metric_runtime_observation
    )
    from heterodiff.experiments.finite_association_production_order import (
        frozen_production_runtime_contract_sha256,
    )
    record_list = [dict(item) for item in records]
    body = {
        "schema": _RECEIPT_SCHEMA,
        "campaign_sha256": primary.campaign_sha256,
        "source_sha256": primary.source_sha256,
        "configuration_sha256": primary.configuration_sha256,
        "fixture_sha256": primary.fixture_sha256,
        "execution_runtime_sha256": primary.execution_runtime_sha256,
        "primary_coordinate_manifest_sha256": (
            primary.coordinate_manifest_sha256
        ),
        "primary_ordered_success_receipts_sha256": (
            primary.ordered_success_receipts_sha256
        ),
        "primary_ordered_checkpoint_sha256": (
            primary.ordered_checkpoint_sha256
        ),
        "primary_success_set_sha256": primary.primary_success_set_sha256,
        "metric_source_sha256": source_sha256,
        "metric_configuration_sha256": configuration_sha256,
        "metric_runtime_contract_sha256": (
            frozen_production_runtime_contract_sha256()
        ),
        "metric_runtime_observation": runtime_body,
        "metric_runtime_observation_sha256": runtime_sha256,
        "reference_set_sha256": _lower_sha256(
            reference_set_sha256, name="reference_set_sha256"
        ),
        "ordered_metric_records": record_list,
        "ordered_metric_records_sha256": _sha256_json(
            {"schema": _ORDERED_METRICS_SCHEMA, "records": record_list}
        ),
        "coordinate_count": 48,
        "evaluation_started_unix_ns": evaluation_started_unix_ns,
        "evaluation_completed_unix_ns": evaluation_completed_unix_ns,
        "freshly_computed": True,
        "post_evaluation_revalidated": True,
        "execution_order_attested": False,
        "scientific_decision_eligible": False,
    }
    receipt = dict(body)
    receipt["primary_metric_receipt_sha256"] = _sha256_json(body)
    return dict(_validated_metric_receipt(receipt))


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("primary metric receipt contains duplicate keys")
        result[key] = value
    return result


def _read_receipt(path: Path) -> dict:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("primary metric receipt is absent") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("primary metric receipt is not a regular file")
    if metadata.st_size <= 0 or metadata.st_size > _MAXIMUM_RECEIPT_BYTES:
        raise RuntimeError("primary metric receipt has an invalid byte length")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(os.fspath(path), flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        ):
            raise RuntimeError(
                "primary metric receipt identity changed while opening"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(_MAXIMUM_RECEIPT_BYTES + 1)
    finally:
        os.close(descriptor)
    if not payload:
        raise RuntimeError("primary metric receipt is empty")
    if len(payload) > _MAXIMUM_RECEIPT_BYTES:
        raise RuntimeError("primary metric receipt exceeds its byte limit")
    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON constant %s" % token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("primary metric receipt is invalid JSON") from error
    checked = dict(_validated_metric_receipt(value))
    if payload != _canonical_json(checked) + b"\n":
        raise RuntimeError("primary metric receipt bytes are not canonical")
    after = os.lstat(path)
    if (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
    ):
        raise RuntimeError("primary metric receipt changed while reading")
    return checked


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory_durable(path: Path) -> None:
    missing = []
    current = path
    while True:
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            missing.append(current)
            if current.parent == current:
                raise RuntimeError("primary metric directory has no durable parent")
            current = current.parent
            continue
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("primary metric custody path is not a directory")
        break
    for directory in reversed(missing):
        directory.mkdir()
        _fsync_directory(directory.parent)


def _validated_metric_directory_path() -> Path:
    raw_directory = frozen_association_primary_metric_directory()
    if not raw_directory.is_absolute():
        raise RuntimeError("primary metric directory must be absolute")
    for component in (raw_directory.parent, raw_directory):
        try:
            metadata = os.lstat(component)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(
                "primary metric custody ancestors must not be symlinks"
            )
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("primary metric custody path is not a directory")
    return raw_directory


def _reconcile_metric_temporary_files(directory: Path) -> None:
    stale = []
    for path in directory.iterdir():
        prefix = ".primary-metric-"
        if not path.name.startswith(prefix):
            continue
        suffix = path.name[len(prefix) :]
        if (
            not suffix
            or len(suffix) > 64
            or any(
                character
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                for character in suffix
            )
        ):
            raise RuntimeError("primary metric temporary name is invalid")
        stale.append(path)
        if len(stale) > _MAXIMUM_STALE_METRIC_TEMPORARIES:
            raise RuntimeError("too many stale primary metric temporaries")
    changed = False
    for path in sorted(stale, key=lambda value: value.name):
        if not stat.S_ISREG(path.lstat().st_mode):
            raise RuntimeError("primary metric temporary path is not regular")
        path.unlink()
        changed = True
    if changed:
        _fsync_directory(directory)


@contextmanager
def _locked_receipt_directory(
    *, create: bool = False
) -> Iterator[Tuple[Path, Path]]:
    if type(create) is not bool:
        raise TypeError("create must be boolean")
    raw_directory = _validated_metric_directory_path()
    if create:
        _ensure_directory_durable(raw_directory)
    else:
        try:
            metadata = os.lstat(raw_directory)
        except FileNotFoundError as error:
            raise RuntimeError("primary metric directory is absent") from error
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("primary metric directory is absent")
    directory = raw_directory.resolve(strict=True)
    if directory != raw_directory:
        raise RuntimeError("primary metric custody escaped its canonical path")
    lock_path = directory / "primary-metric.lock"
    receipt_path = directory / _RECEIPT_FILE
    try:
        lock_status = os.lstat(lock_path)
    except FileNotFoundError:
        lock_status = None
        if not create:
            raise RuntimeError("primary metric lock is absent")
    else:
        if not stat.S_ISREG(lock_status.st_mode):
            raise RuntimeError("primary metric lock is not a regular file")
    flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    if create:
        flags |= os.O_CREAT
    try:
        descriptor = os.open(os.fspath(lock_path), flags, 0o600)
    except FileNotFoundError as error:
        raise RuntimeError("primary metric lock is absent") from error
    try:
        opened = os.fstat(descriptor)
        current = os.lstat(lock_path)
        if not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(
            current.st_mode
        ) or (
            opened.st_dev,
            opened.st_ino,
        ) != (current.st_dev, current.st_ino):
            raise RuntimeError("primary metric lock identity changed while opening")
        if lock_status is not None and (
            lock_status.st_dev,
            lock_status.st_ino,
        ) != (opened.st_dev, opened.st_ino):
            raise RuntimeError("primary metric lock was substituted while opening")
        if lock_status is None:
            os.fsync(descriptor)
            _fsync_directory(directory)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        try:
            current = os.lstat(lock_path)
            if (
                current.st_dev,
                current.st_ino,
            ) != (opened.st_dev, opened.st_ino):
                raise RuntimeError("primary metric lock changed while held")
            _reconcile_metric_temporary_files(directory)
            yield directory, receipt_path
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _load_existing_metric_receipt_if_present() -> dict | None:
    """Return a validated existing record, or ``None`` only for true absence.

    A present directory without its durable lock, a symlink, a nonregular
    receipt, or invalid receipt bytes is a custody failure rather than a signal
    to recompute.  This distinction keeps recovery fail closed.
    """

    raw_directory = _validated_metric_directory_path()
    try:
        metadata = os.lstat(raw_directory)
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError("primary metric custody path is not a directory")
    lock_path = raw_directory / "primary-metric.lock"
    try:
        os.lstat(lock_path)
    except FileNotFoundError:
        entries = tuple(raw_directory.iterdir())
        if entries:
            raise RuntimeError(
                "primary metric directory lacks its lock and is not empty"
            )
        lock_create = True
    else:
        lock_create = False
    with _locked_receipt_directory(create=lock_create) as (_, path):
        try:
            os.lstat(path)
        except FileNotFoundError:
            return None
        return _read_receipt(path)


def _persist_metric_receipt(receipt: dict) -> bool:
    checked = dict(_validated_metric_receipt(receipt))
    payload = _canonical_json(checked) + b"\n"
    with _locked_receipt_directory(create=True) as (directory, path):
        if path.exists() or path.is_symlink():
            existing = _read_receipt(path)
            if existing != checked:
                raise RuntimeError(
                    "existing primary metric receipt differs from fresh metrics"
                )
            return False
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=str(directory),
                prefix=".primary-metric-",
                delete=False,
            ) as handle:
                temporary_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_name, path)
            except FileExistsError:
                existing = _read_receipt(path)
                if existing != checked:
                    raise RuntimeError(
                        "concurrent primary metric receipt is conflicting"
                    )
                return False
            _fsync_directory(directory)
            return True
        finally:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
                else:
                    _fsync_directory(directory)


def _reopen_primary_snapshot_allowing_controls():
    """Rebuild primary identities while allowing later controls to exist."""

    from heterodiff.experiments import finite_association_isolated_runner as runner

    directory = runner._absolute_without_symlink_resolution(
        runner.frozen_association_campaign_directory()
    )
    with runner._locked_ledger(directory, create=False) as (_, ledger):
        snapshot = ledger
        custody = runner._sampled_aggregate_custody_sha256(snapshot)
    checkpoints, identities, success_set = (
        runner._assemble_frozen_association_primary_success_set(
            directory,
            snapshot,
            allow_post_primary_state=True,
        )
    )
    with runner._locked_ledger(directory, create=False) as (_, current):
        if runner._sampled_aggregate_custody_sha256(current) != custody:
            raise RuntimeError(
                "sampled campaign changed while primary metrics were loading"
            )
    return checkpoints, identities, success_set


_VERIFIED_PRIMARY_METRIC_KEY = object()


class LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
    """Immutable loader admission of the durable primary metric receipt."""

    __slots__ = (
        "_primary_metric_receipt_sha256",
        "_primary_success_set_sha256",
        "_ordered_metric_records_sha256",
        "_campaign_sha256",
        "_source_sha256",
        "_configuration_sha256",
        "_fixture_sha256",
        "_execution_runtime_sha256",
        "_coordinate_manifest_sha256",
        "_ordered_success_receipts_sha256",
        "_ordered_checkpoint_sha256",
        "_reference_set_sha256",
        "_metric_source_sha256",
        "_metric_configuration_sha256",
        "_metric_runtime_contract_sha256",
        "_metric_runtime_observation_sha256",
        "_ordered_metric_values",
        "_locked",
    )

    def __init__(self, record: dict, *, _construction_key: object) -> None:
        if _construction_key is not _VERIFIED_PRIMARY_METRIC_KEY:
            raise TypeError("primary metric wrappers come only from the loader")
        checked = dict(_validated_metric_receipt(record))
        for name in (
            "primary_metric_receipt_sha256",
            "primary_success_set_sha256",
            "ordered_metric_records_sha256",
            "campaign_sha256",
            "source_sha256",
            "configuration_sha256",
            "fixture_sha256",
            "execution_runtime_sha256",
            "primary_coordinate_manifest_sha256",
            "primary_ordered_success_receipts_sha256",
            "primary_ordered_checkpoint_sha256",
            "reference_set_sha256",
            "metric_source_sha256",
            "metric_configuration_sha256",
            "metric_runtime_contract_sha256",
            "metric_runtime_observation_sha256",
        ):
            attribute_name = {
                "primary_coordinate_manifest_sha256": (
                    "coordinate_manifest_sha256"
                ),
                "primary_ordered_success_receipts_sha256": (
                    "ordered_success_receipts_sha256"
                ),
                "primary_ordered_checkpoint_sha256": (
                    "ordered_checkpoint_sha256"
                ),
            }.get(name, name)
            object.__setattr__(self, "_" + attribute_name, checked[name])
        ordered_values = []
        for member in checked["ordered_metric_records"]:
            ordered_values.append(
                MappingProxyType(
                    {
                        "ordinal": member["ordinal"],
                        "coordinate": (
                            member["seed"],
                            member["budget"],
                            member["method"],
                        ),
                        "nonpath": _freeze_decision_values(
                            member["nonpath_decision_values"]
                        ),
                        "path": _freeze_decision_values(
                            member["path_decision_values"]
                        ),
                        "nonpath_content_sha256": member[
                            "nonpath_content_sha256"
                        ],
                        "path_content_sha256": member[
                            "path_content_sha256"
                        ],
                        "nonpath_decision_values_sha256": member[
                            "nonpath_decision_values_sha256"
                        ],
                        "path_decision_values_sha256": member[
                            "path_decision_values_sha256"
                        ],
                    }
                )
            )
        object.__setattr__(self, "_ordered_metric_values", tuple(ordered_values))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("primary metric receipt wrapper is immutable")
        object.__setattr__(self, name, value)

    @property
    def primary_metric_receipt_sha256(self) -> str:
        return self._primary_metric_receipt_sha256

    @property
    def primary_success_set_sha256(self) -> str:
        return self._primary_success_set_sha256

    @property
    def ordered_metric_records_sha256(self) -> str:
        return self._ordered_metric_records_sha256

    @property
    def ordered_metric_values(self) -> tuple:
        """Recover all decision-bearing values as deeply immutable records."""

        return self._ordered_metric_values

    @property
    def campaign_sha256(self) -> str:
        return self._campaign_sha256

    @property
    def source_sha256(self) -> str:
        return self._source_sha256

    @property
    def configuration_sha256(self) -> str:
        return self._configuration_sha256

    @property
    def fixture_sha256(self) -> str:
        return self._fixture_sha256

    @property
    def execution_runtime_sha256(self) -> str:
        return self._execution_runtime_sha256

    @property
    def coordinate_manifest_sha256(self) -> str:
        return self._coordinate_manifest_sha256

    @property
    def ordered_success_receipts_sha256(self) -> str:
        return self._ordered_success_receipts_sha256

    @property
    def ordered_checkpoint_sha256(self) -> str:
        return self._ordered_checkpoint_sha256

    @property
    def reference_set_sha256(self) -> str:
        return self._reference_set_sha256

    @property
    def metric_source_sha256(self) -> str:
        return self._metric_source_sha256

    @property
    def metric_configuration_sha256(self) -> str:
        return self._metric_configuration_sha256

    @property
    def metric_runtime_observation_sha256(self) -> str:
        return self._metric_runtime_observation_sha256

    @property
    def metric_runtime_contract_sha256(self) -> str:
        return self._metric_runtime_contract_sha256

    @property
    def coordinate_count(self) -> int:
        return 48

    @property
    def execution_order_attested(self) -> bool:
        return False

    @property
    def scientific_decision_eligible(self) -> bool:
        return False


def _admit_metric_receipt(
    record: dict,
) -> LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
    return LedgerVerifiedFrozenAssociationPrimaryMetricReceipt(
        record, _construction_key=_VERIFIED_PRIMARY_METRIC_KEY
    )


def compute_and_commit_frozen_association_primary_metrics(
    primary_success_set: object,
) -> LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
    """Recover matching custody or compute both metrics for all 48 primaries.

    This function intentionally has no callback, record, digest, path, or
    configuration argument.  Every metric record and every content digest is
    created inside this boundary from canonical checkpoint custody.  A valid
    pre-existing receipt is reopened and revalidated before any evaluator is
    reached; conflicting or malformed existing custody fails before compute.
    """

    from heterodiff.experiments.finite_association_isolated_runner import (
        LedgerVerifiedFrozenAssociationPrimarySuccessSet,
        revalidate_completed_frozen_association_primary_success_set,
    )

    if type(primary_success_set) is not (
        LedgerVerifiedFrozenAssociationPrimarySuccessSet
    ):
        raise TypeError("primary metrics require canonical primary admission")
    admitted = revalidate_completed_frozen_association_primary_success_set(
        primary_success_set
    )
    if not _same_primary_identity(admitted, primary_success_set):
        raise RuntimeError("primary success-set changed before metric evaluation")
    existing = _load_existing_metric_receipt_if_present()
    if existing is not None:
        _require_receipt_matches_primary_identity(existing, admitted)
        recovered = load_committed_frozen_association_primary_metrics()
        if not _same_primary_identity(recovered, admitted):
            raise RuntimeError(
                "recovered primary metric admission differs from primary custody"
            )
        return revalidate_committed_frozen_association_primary_metrics(
            recovered
        )

    metric_source_before = frozen_association_primary_metric_source_sha256()
    metric_configuration_before = (
        frozen_association_primary_metric_configuration_sha256(
            metric_source_sha256=metric_source_before
        )
    )
    from heterodiff.experiments.finite_association_production_order import (
        _capture_legacy_metric_runtime_preflight,
    )

    metric_runtime_before = _capture_legacy_metric_runtime_preflight()

    # Evaluator and training modules are deliberately imported only after the
    # durable-receipt recovery and source/runtime preflight barriers above.
    from heterodiff.evaluation.finite_association_path_evaluator import (
        build_frozen_association_path_references,
        evaluate_finite_association_paths,
    )
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        evaluate_finite_association_nonpath,
    )
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        build_frozen_association_residual_fixture,
    )
    from heterodiff.experiments.finite_association_isolated_runner import (
        revalidate_successful_frozen_association_checkpoint,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        bind_fitted_association_checkpoint_evaluator,
    )

    started = time.time_ns()
    records = []
    try:
        fixture = build_frozen_association_residual_fixture()
        references = build_frozen_association_path_references(fixture)
        references.require_preflight_pass()
        for ordinal, (coordinate, checkpoint) in enumerate(
            zip(admitted.coordinates, admitted.checkpoints)
        ):
            revalidate_successful_frozen_association_checkpoint(checkpoint)
            evaluator = bind_fitted_association_checkpoint_evaluator(checkpoint)
            nonpath = evaluate_finite_association_nonpath(evaluator, fixture)
            revalidate_successful_frozen_association_checkpoint(checkpoint)
            path = evaluate_finite_association_paths(
                evaluator, fixture, reference_set=references
            )
            revalidate_successful_frozen_association_checkpoint(checkpoint)
            records.append(
                _build_metric_member(
                    ordinal, coordinate, checkpoint, nonpath, path
                )
            )
    except BaseException as primary_error:
        try:
            revalidate_completed_frozen_association_primary_success_set(admitted)
        except BaseException as revalidation_error:
            primary_error.add_note(
                "post-evaluation primary revalidation also failed: %r"
                % revalidation_error
            )
        raise
    completed = time.time_ns()
    post = revalidate_completed_frozen_association_primary_success_set(admitted)
    if not _same_primary_identity(post, admitted):
        raise RuntimeError("primary success-set changed during metric evaluation")
    metric_source_after = frozen_association_primary_metric_source_sha256()
    metric_configuration_after = (
        frozen_association_primary_metric_configuration_sha256(
            metric_source_sha256=metric_source_after
        )
    )
    metric_runtime_after = _capture_legacy_metric_runtime_preflight()
    if (
        metric_source_after != metric_source_before
        or metric_configuration_after != metric_configuration_before
        or metric_runtime_after != metric_runtime_before
    ):
        raise RuntimeError(
            "metric source, configuration, or runtime changed during evaluation"
        )
    receipt = _build_metric_receipt(
        post,
        tuple(records),
        metric_source_sha256=metric_source_before,
        metric_configuration_sha256=metric_configuration_before,
        metric_runtime_observation=metric_runtime_before,
        reference_set_sha256=references.reference_set_sha256,
        evaluation_started_unix_ns=started,
        evaluation_completed_unix_ns=completed,
    )
    _persist_metric_receipt(receipt)
    return load_committed_frozen_association_primary_metrics()


def load_committed_frozen_association_primary_metrics(
) -> LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
    """Load the receipt and re-open its 48 checkpoint identities.

    Unlike primary-stage admission, this loader remains valid after sampled
    controls and the full aggregate are present, provided all primary custody
    identities are unchanged.
    """

    with _locked_receipt_directory() as (_, path):
        receipt = _read_receipt(path)
    _, identities, success_set = _reopen_primary_snapshot_allowing_controls()
    comparisons = {
        "campaign_sha256": success_set["campaign_sha256"],
        "source_sha256": success_set["source_sha256"],
        "configuration_sha256": success_set["configuration_sha256"],
        "fixture_sha256": success_set["fixture_sha256"],
        "execution_runtime_sha256": success_set["execution_runtime_sha256"],
        "primary_coordinate_manifest_sha256": success_set[
            "coordinate_manifest_sha256"
        ],
        "primary_ordered_success_receipts_sha256": success_set[
            "ordered_success_receipts_sha256"
        ],
        "primary_ordered_checkpoint_sha256": success_set[
            "ordered_checkpoint_sha256"
        ],
        "primary_success_set_sha256": success_set[
            "primary_success_set_sha256"
        ],
    }
    if any(receipt[name] != expected for name, expected in comparisons.items()):
        raise RuntimeError("primary metric receipt differs from current custody")
    for receipt_member, identity in zip(
        receipt["ordered_metric_records"], identities
    ):
        expected = {
            "run_key_sha256": identity["run_key_sha256"],
            "success_receipt_sha256": identity["success_ledger_sha256"],
            "optimizer_completion_receipt_sha256": identity[
                "optimizer_completion_receipt_sha256"
            ],
            "parameter_sha256": identity["parameter_sha256"],
            "classifier_sha256": identity["classifier_sha256"],
            "certificate_sha256": identity["certificate_sha256"],
            "feature_sha256": identity["feature_sha256"],
        }
        if any(
            receipt_member[name] != value for name, value in expected.items()
        ):
            raise RuntimeError(
                "primary metric member differs from current checkpoint custody"
            )
    with _locked_receipt_directory() as (_, path):
        if _read_receipt(path) != receipt:
            raise RuntimeError("primary metric receipt changed while loading")
    return _admit_metric_receipt(receipt)


def revalidate_committed_frozen_association_primary_metrics(
    admitted: object,
) -> LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
    """Reopen canonical files and match an earlier metric admission."""

    if type(admitted) is not LedgerVerifiedFrozenAssociationPrimaryMetricReceipt:
        raise TypeError("primary metric revalidation requires loader admission")
    fresh = load_committed_frozen_association_primary_metrics()
    if (
        fresh.primary_metric_receipt_sha256
        != admitted.primary_metric_receipt_sha256
        or fresh.primary_success_set_sha256
        != admitted.primary_success_set_sha256
        or fresh.ordered_metric_records_sha256
        != admitted.ordered_metric_records_sha256
    ):
        raise RuntimeError("canonical primary metric receipt changed")
    return fresh


__all__ = [
    "LedgerVerifiedFrozenAssociationPrimaryMetricReceipt",
    "compute_and_commit_frozen_association_primary_metrics",
    "frozen_association_primary_metric_configuration_sha256",
    "frozen_association_primary_metric_directory",
    "frozen_association_primary_metric_source_sha256",
    "load_committed_frozen_association_primary_metrics",
    "revalidate_committed_frozen_association_primary_metrics",
]
