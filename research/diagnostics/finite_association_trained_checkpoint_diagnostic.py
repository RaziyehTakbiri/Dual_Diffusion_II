"""Frozen D1 diagnostic for the immutable trained A1 V2 checkpoint.

This file intentionally lives outside :mod:`heterodiff`.  The only scientific
implementation it may import is the byte-frozen source tree retained inside
the successful V2 development-checkpoint capsule.  It can reopen and evaluate
that checkpoint; it cannot train, resume, select, replace, or promote it.

The parent process validates the complete V2 artifact inventory, launches a
safe-path worker under the exact frozen virtual environment, validates the
worker's result, reopens the V2 inventory, and only then publishes two files by
one directory rename into a new sibling artifact root.
"""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import secrets
import stat
import struct
import subprocess
import sys
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-a1-trained-checkpoint-diagnostic-v1"
RECEIPT_SCHEMA_VERSION = (
    "heterodiff-a1-trained-checkpoint-diagnostic-success-receipt-v1"
)
LANE_ID = "A1-D1-TRAINED-CHECKPOINT-DIAGNOSTIC-V1"
STATUS = "COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC"
SCOPE = "TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY"

V2_ARTIFACT_RELATIVE_PATH = (
    "artifacts/manuscript_v3_a1_development_checkpoint_v2"
)
V2_CAPSULE_RELATIVE_PATH = V2_ARTIFACT_RELATIVE_PATH + "/capsule"
OUTPUT_RELATIVE_PATH = "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1"
ATTEMPT_MARKER_RELATIVE_PATH = (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json"
)
FREEZE_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_freeze_v1.json"
)
HUMAN_FREEZE_RELATIVE_PATH = (
    "manuscript_v3/a1_trained_checkpoint_diagnostic_freeze.md"
)
IMPLEMENTATION_RELATIVE_PATH = (
    "research/diagnostics/finite_association_trained_checkpoint_diagnostic.py"
)
TEST_RELATIVE_PATH = (
    "tests/unit/test_finite_association_trained_checkpoint_diagnostic.py"
)
TARGET_PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"

PROTECTED_PRODUCTION_RELATIVE_PATHS = (
    "artifacts/a1_campaign_v4",
    "artifacts/a1_finite_association_production_order_v1",
)

EXPECTED_OUTER_RECEIPT_RAW_SHA256 = (
    "7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885"
)
EXPECTED_OUTER_RECEIPT_SELF_SHA256 = (
    "154d64d654a4f175f07e323524782f90af29dbbb5f81c053ce0105a67dbfe747"
)
EXPECTED_OUTER_INVENTORY_SHA256 = (
    "fefefdeb8799236052e1ce2c4132453d026cd6b2a991ea92cc96d19e7046a189"
)
EXPECTED_CAPSULE_MANIFEST_SHA256 = (
    "d1f08dcca28c1a3f38b4e0cfbd965f3efb44dc6ed9b33687374e614c1a53c9ed"
)
EXPECTED_RUN_KEY_SHA256 = (
    "dc7484372d3f8a633755450bda9d70f0ed182005dba052a0fa86747ae0fe4f70"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c"
)
EXPECTED_INNER_SUCCESS_SHA256 = (
    "df4c5770f10350e4f0a0267842de775731349de67cc282cec1e6bbddfc7bc6cc"
)
EXPECTED_CAMPAIGN_SHA256 = (
    "5bdf07f03e5f6ebb0340c6a55a3f9af45a89ee2010232650faa8cab54dc98508"
)
EXPECTED_PARAMETER_SHA256 = (
    "d0bf29778dd866f5cd752f76be39df05d8dc2d6a89476070b77dd25326530388"
)
EXPECTED_FEATURE_SHA256 = (
    "f73a1a793aae93001d7537ddfdd44955d33bdc14ba37dbc397e056d67111d37d"
)
EXPECTED_CLASSIFIER_SHA256 = (
    "5f35eddd4354b2ecf77abb9e01b46fbedf17bb917727827478a9bbc11cd3f14e"
)
EXPECTED_CERTIFICATE_SHA256 = (
    "008a0df7c67600932257991ddf5b69fa77fb9056b90f45ec280f45629ad89926"
)
EXPECTED_EXECUTION_RUNTIME_SHA256 = (
    "032a7e48bccd0efbd79606621daf0825885b76ea83118ab2d75ac8aa4d905ea0"
)
EXPECTED_SOURCE_SHA256 = (
    "1ead8f21969b1ebf31d98fca846efc21edbf9dee95a8e4c7be8e19bf9b16dfb1"
)
EXPECTED_CONFIGURATION_SHA256 = (
    "eda69c9d2a57c62ce4805da1d3cad9606619ef703eda5d6a45fb1b602022f968"
)
EXPECTED_PREFLIGHT_SHA256 = (
    "b8fd9ccf80ddd2993c3d546f9cb28583d93d82af66e69b09d2f9cd339e41ef3b"
)
EXPECTED_FIXTURE_SHA256 = (
    "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
)
EXPECTED_PATH_CONTENT_SHA256 = (
    "ba9de201cdf249d9c2adeb07202075e20765e0bab637ce79668fde245b19f67f"
)
EXPECTED_PATH_RUNTIME_SHA256 = (
    "4992cb102180bb6e6bf76a70280a19a6ca0952b5148c662c331ebafcbb504cda"
)
EXPECTED_FAMILY_PARTITION_SHA256 = (
    "bc54ccc360803bc1673508a540a59ba48c24d58b8a316b0c3674632542cefc6f"
)
EXPECTED_FAMILY_EDGE_COUNTS = (30, 30, 60)
EXPECTED_COORDINATE = {"seed": 1729, "budget": 32768, "method": "guided"}
EXPECTED_UPDATES = 3000
EXPECTED_PATH_RUNTIME = {
    "python_version": "3.11.5",
    "numpy_version": "2.4.6",
    "scipy_version": "1.17.1",
    "ode_method": "scipy.integrate.solve_ivp:DOP853",
    "quadrature_method": "scipy.integrate.quad_vec",
}
EXPECTED_PRIMARY_SOLVER_SETTINGS = {
    "label": "primary",
    "rtol": 2.0e-10,
    "atol": 2.0e-12,
    "max_step": 1.0 / 128.0,
    "quadrature_epsabs": 1.0e-11,
    "quadrature_epsrel": 1.0e-10,
    "quadrature_limit": 2_000,
    "max_potential_evaluations": 300_000,
}
EXPECTED_REFINED_SOLVER_SETTINGS = {
    "label": "refined",
    "rtol": 2.0e-11,
    "atol": 2.0e-13,
    "max_step": 1.0 / 256.0,
    "quadrature_epsabs": 1.0e-12,
    "quadrature_epsrel": 1.0e-11,
    "quadrature_limit": 2_000,
    "max_potential_evaluations": 300_000,
}

FAMILY_ORDER = ("birth", "death", "replacement")
COMPONENT_ORDER = (
    "K0_NORMALIZED_INITIALIZER",
    "KC_CONTINUOUS_COORDINATES",
    "K_PLUS_BIRTH",
    "K_MINUS_DEATH",
    "K_R_REPLACEMENT",
)
CONTINUOUS_DISPOSITION = "NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"
FAMILY_REFINEMENT_NAMES = ("initial", "birth", "death", "replacement", "total")
FAMILY_CROSSCHECK_NAMES = (
    "primary_family_initial_vs_separate_aggregate",
    "primary_family_dynamic_vs_separate_aggregate",
    "primary_family_total_vs_separate_aggregate",
    "refined_family_initial_vs_separate_aggregate",
    "refined_family_dynamic_vs_separate_aggregate",
    "refined_family_total_vs_separate_aggregate",
    "primary_separate_initial_vs_public_aggregate",
    "primary_separate_dynamic_vs_public_aggregate",
    "primary_separate_total_vs_public_aggregate",
)
PRIMARY_REFINED_LIMIT = 1.0e-8
FAMILY_AGGREGATE_LIMIT = 1.0e-8
TARGET_MARGINAL_LIMIT = 1.0e-8
TERMINAL_LIMIT = 1.0e-10
NONPATH_TERMINAL_LOG_LIMIT = 1.0e-12
NONPATH_COHERENCE_LIMIT = 1.0e-10
MAXIMUM_WORKER_OUTPUT_BYTES = 64 * 1024 * 1024
WORKER_TIMEOUT_SECONDS = 3600.0
_V2_INVENTORY_DOMAIN = b"heterodiff-a1-development-artifact-inventory-v2\0"
_ARRAY_DOMAIN = b"heterodiff-a1-trained-diagnostic-array-v1\0"
_RECORD_DOMAIN = b"heterodiff-a1-trained-diagnostic-record-v1\0"
_WORKER_REQUEST_DOMAIN = b"heterodiff-a1-trained-diagnostic-worker-request-v1\0"
_ATTEMPT_MARKER_DOMAIN = b"heterodiff-a1-trained-diagnostic-attempt-marker-v1\0"
_THREAD_VARIABLES = (
    "BLIS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)
NONPATH_RECORD_FIELDS = frozenset(
    {
        "parameter_sha256",
        "feature_sha256",
        "classifier_sha256",
        "execution_receipt_sha256",
        "campaign_sha256",
        "production_bound",
        "classifier_logit_grid",
        "log_information_grid",
        "residual_log_grid",
        "masked_excess_bce",
        "centered_log_information",
        "residual",
        "edge_log_rates",
        "conditional_initial_tv",
        "calibration",
        "coherence",
    }
)
PATH_RUNTIME_FIELDS = frozenset(EXPECTED_PATH_RUNTIME)
PATH_SOLVER_FIELDS = frozenset(EXPECTED_PRIMARY_SOLVER_SETTINGS)
PATH_REFERENCE_FIELDS = frozenset(
    {
        "frozen_fixture_sha256",
        "fixture_content_sha256",
        "runtime",
        "reference_sha256",
        "observation_index",
        "observation_mass",
        "unconditional_path_kl",
        "refined_unconditional_path_kl",
        "primary_refined_unconditional_path_kl_change",
        "oracle_self_path_kl",
        "target_marginal_maximum_absolute_error",
        "target_initial_normalizer",
        "target_initial_law",
        "target_generator_grid",
        "primary_solver_settings",
        "refined_solver_settings",
        "oracle_self_potential_evaluations",
        "unconditional_potential_evaluations",
        "refined_unconditional_potential_evaluations",
    }
)
PATH_REFERENCE_SET_FIELDS = frozenset(
    {
        "frozen_fixture_sha256",
        "fixture_content_sha256",
        "runtime",
        "primary_solver_settings",
        "refined_solver_settings",
        "references",
        "reference_set_sha256",
    }
)
AGGREGATE_PATH_FIELDS = frozenset(
    {
        "parameter_sha256",
        "classifier_sha256",
        "execution_receipt_sha256",
        "campaign_sha256",
        "production_bound",
        "reference_set_sha256",
        "observations",
        "observation_mass",
        "path_kl_per_observation",
        "unconditional_path_kl_per_observation",
        "normalized_path_kl_per_observation",
        "endpoint_total_variation_per_observation",
        "maximum_intermediate_total_variation_per_observation",
        "observation_weighted_path_kl",
        "retained_path_kl_mean",
        "retained_normalized_path_score",
        "overflow_path_kl",
        "overflow_normalized_path_score",
        "observation_weighted_endpoint_total_variation",
        "retained_endpoint_total_variation_mean",
        "overflow_endpoint_total_variation",
        "ambiguous_observation_indices",
        "ambiguous_normalized_path_kl",
        "ambiguous_normalized_path_score",
        "numerical_gate_failures",
    }
)
AGGREGATE_OBSERVATION_FIELDS = frozenset(
    {
        "parameter_sha256",
        "classifier_sha256",
        "execution_receipt_sha256",
        "campaign_sha256",
        "production_bound",
        "reference",
        "candidate_initial_normalizer",
        "candidate_initial_law",
        "candidate_generator_grid",
        "target_marginals",
        "candidate_marginals",
        "target_integrated_occupation",
        "candidate_integrated_occupation",
        "marginal_total_variation",
        "path_kl_initial",
        "path_kl_dynamic",
        "path_kl_total",
        "normalized_path_kl",
        "maximum_intermediate_total_variation",
        "endpoint_total_variation",
        "primary_refined_path_kl_change",
        "primary_refined_endpoint_total_variation",
        "primary_path_quadrature_error",
        "refined_path_quadrature_error",
        "primary_target_marginal_maximum_absolute_error",
        "primary_solver_settings",
        "refined_solver_settings",
        "primary_path_potential_evaluations",
        "refined_path_potential_evaluations",
        "primary_candidate_occupancy_potential_evaluations",
        "refined_candidate_occupancy_potential_evaluations",
    }
)
EVIDENCE_BINDING_FIELDS = frozenset(
    {
        "coordinate",
        "run_key_sha256",
        "success_receipt_sha256",
        "campaign_sha256",
        "parameter_sha256",
        "feature_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "optimizer_steps_taken",
        "nonpath_identity_matches",
        "aggregate_path_identity_matches",
        "internal_analysis_only",
    }
)
EVIDENCE_BINDING_SOURCE_FIELDS = frozenset(
    {
        "run_key_sha256",
        "success_receipt_sha256",
        "campaign_sha256",
        "parameter_sha256",
        "feature_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "optimizer_steps_taken",
    }
)


class DiagnosticRefusal(RuntimeError):
    """Fail-closed refusal before a diagnostic artifact can be issued."""


def _workspace_root() -> Path:
    source = Path(__file__).absolute()
    try:
        status = source.lstat()
    except OSError as error:
        raise DiagnosticRefusal("diagnostic implementation is not readable") from error
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise DiagnosticRefusal("diagnostic implementation must be a regular file")
    root = source.parents[2]
    if source.resolve(strict=True) != source or root.resolve(strict=True) != root:
        raise DiagnosticRefusal("diagnostic workspace path is not canonical")
    if source.relative_to(root).as_posix() != IMPLEMENTATION_RELATIVE_PATH:
        raise DiagnosticRefusal("diagnostic implementation path is not frozen")
    return root


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise DiagnosticRefusal("value is not canonical finite JSON") from error


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise DiagnosticRefusal("%s is not a SHA-256 digest" % name)
    try:
        int(value, 16)
    except ValueError as error:
        raise DiagnosticRefusal("%s is not hexadecimal" % name) from error
    if value != value.lower():
        raise DiagnosticRefusal("%s is not lowercase" % name)
    return value


def _read_regular_bytes(path: Path, *, maximum: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise DiagnosticRefusal("required file is absent: %s" % path) from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise DiagnosticRefusal("required file is not regular: %s" % path)
    if before.st_size < 0 or before.st_size > maximum:
        raise DiagnosticRefusal("required file has an invalid size: %s" % path)
    with open(path, "rb") as handle:
        payload = handle.read(maximum + 1)
    after = path.lstat()
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_before != identity_after or len(payload) != before.st_size:
        raise DiagnosticRefusal("required file changed while it was read: %s" % path)
    return payload


def _parse_json_object(payload: bytes) -> Dict[str, Any]:
    def reject_duplicates(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DiagnosticRefusal("JSON object contains a duplicate key")
            result[key] = value
        return result

    def parse_finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise DiagnosticRefusal("JSON contains a non-finite number")
        return value

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_float=parse_finite_float,
            parse_constant=lambda token: (_ for _ in ()).throw(
                DiagnosticRefusal("JSON contains non-finite token %s" % token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DiagnosticRefusal("file is not valid UTF-8 JSON") from error
    if type(value) is not dict:
        raise DiagnosticRefusal("JSON root must be an object")
    return value


def _finite_number(value: object, *, name: str) -> float:
    if type(value) not in (int, float):
        raise DiagnosticRefusal("%s is not a real JSON number" % name)
    checked = float(value)
    if not math.isfinite(checked):
        raise DiagnosticRefusal("%s is not finite" % name)
    return checked


def _finite_nonnegative(value: object, *, name: str) -> float:
    checked = _finite_number(value, name=name)
    if checked < 0.0:
        raise DiagnosticRefusal("%s is negative" % name)
    return checked


def _validate_array_descriptor(
    value: object, *, name: str, shape: Sequence[int], dtype: str = "<f8"
) -> str:
    if (
        type(value) is not dict
        or set(value) != {"dtype", "shape", "sha256"}
        or value.get("dtype") != dtype
        or value.get("shape") != list(shape)
    ):
        raise DiagnosticRefusal("%s has an invalid array descriptor" % name)
    return _require_sha256(value.get("sha256"), name=name + " sha256")


def _numerically_equal(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=2.0e-12, abs_tol=2.0e-14)


def _path_digest_text(digest: object, value: str) -> None:
    encoded = value.encode("utf-8")
    digest.update(len(encoded).to_bytes(8, "little", signed=False))
    digest.update(encoded)


def _solver_settings_record_sha256(settings: Mapping[str, object]) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-solver-settings-v1\0")
    _path_digest_text(digest, str(settings["label"]))
    _path_digest_text(digest, "<f8")
    _path_digest_text(digest, "5")
    float_payload = struct.pack(
        "<5d",
        *(
            float(settings[name])
            for name in (
                "rtol",
                "atol",
                "max_step",
                "quadrature_epsabs",
                "quadrature_epsrel",
            )
        ),
    )
    digest.update(len(float_payload).to_bytes(8, "little", signed=False))
    digest.update(float_payload)
    _path_digest_text(digest, "<i8")
    _path_digest_text(digest, "2")
    integer_payload = struct.pack(
        "<2q",
        int(settings["quadrature_limit"]),
        int(settings["max_potential_evaluations"]),
    )
    digest.update(len(integer_payload).to_bytes(8, "little", signed=False))
    digest.update(integer_payload)
    return digest.hexdigest()


def _reference_set_record_sha256(references: Sequence[Mapping[str, object]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-reference-set-v1\0")
    for value in (
        EXPECTED_FIXTURE_SHA256,
        EXPECTED_PATH_CONTENT_SHA256,
        EXPECTED_PATH_RUNTIME_SHA256,
        _solver_settings_record_sha256(EXPECTED_PRIMARY_SOLVER_SETTINGS),
        _solver_settings_record_sha256(EXPECTED_REFINED_SOLVER_SETTINGS),
        "reported-denominator:primary",
    ):
        _path_digest_text(digest, value)
    for reference in references:
        _path_digest_text(digest, str(reference["reference_sha256"]))
    return digest.hexdigest()


def _file_sha256(path: Path, *, maximum: int = 64 * 1024 * 1024) -> str:
    return _sha256_bytes(_read_regular_bytes(path, maximum=maximum))


def _self_digest(record: Mapping[str, object], *, field: str, domain: bytes) -> str:
    projected = dict(record)
    projected.pop(field, None)
    return _sha256_bytes(domain + _canonical_json_bytes(projected))


def _inventory(root: Path, *, exclude: Sequence[str] = ()) -> Tuple[Dict[str, object], ...]:
    try:
        root_status = root.lstat()
    except OSError as error:
        raise DiagnosticRefusal("artifact root is absent: %s" % root) from error
    if stat.S_ISLNK(root_status.st_mode) or not stat.S_ISDIR(root_status.st_mode):
        raise DiagnosticRefusal("artifact root is not a regular directory")
    excluded = frozenset(exclude)
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise DiagnosticRefusal("artifact inventory contains a symlink")
        if stat.S_ISDIR(status.st_mode):
            continue
        if not stat.S_ISREG(status.st_mode):
            raise DiagnosticRefusal("artifact inventory contains a special file")
        if relative in excluded:
            continue
        payload = _read_regular_bytes(path, maximum=2 * 1024**3)
        rows.append(
            {
                "path": relative,
                "bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )
    if len({row["path"] for row in rows}) != len(rows):
        raise DiagnosticRefusal("artifact inventory contains duplicate paths")
    return tuple(rows)


def _validate_outer_v2_custody(root: Path) -> Dict[str, object]:
    artifact_root = root / V2_ARTIFACT_RELATIVE_PATH
    receipt_path = artifact_root / "success-receipt.json"
    payload = _read_regular_bytes(receipt_path, maximum=32 * 1024 * 1024)
    if _sha256_bytes(payload) != EXPECTED_OUTER_RECEIPT_RAW_SHA256:
        raise DiagnosticRefusal("V2 outer success receipt bytes changed")
    receipt = _parse_json_object(payload)
    claimed = _require_sha256(receipt.get("receipt_sha256"), name="receipt_sha256")
    if (
        claimed != EXPECTED_OUTER_RECEIPT_SELF_SHA256
        or _self_digest(receipt, field="receipt_sha256", domain=b"") != claimed
    ):
        raise DiagnosticRefusal("V2 outer success receipt self-digest changed")
    inner = receipt.get("inner_success")
    if type(inner) is not dict:
        raise DiagnosticRefusal("V2 outer receipt lacks inner SUCCESS custody")
    required = {
        "schema": "heterodiff-a1-development-checkpoint-receipt-v2",
        "lane_id": "A1-DEV-GUIDED-1729-N32768-V2",
        "state": "SUCCESS_DEVELOPMENT_CHECKPOINT",
        "receipt_sha256": EXPECTED_OUTER_RECEIPT_SELF_SHA256,
        "capsule_manifest_sha256": EXPECTED_CAPSULE_MANIFEST_SHA256,
        "artifact_inventory_sha256": EXPECTED_OUTER_INVENTORY_SHA256,
    }
    if any(receipt.get(key) != value for key, value in required.items()):
        raise DiagnosticRefusal("V2 outer receipt identity changed")
    false_fields = (
        "claim_promotion",
        "closes_c17",
        "confirmatory_execution",
        "production_order_admissible",
        "qualifies_r1",
        "qualifies_r2",
        "real_domain_test_accessed",
        "replacement_permitted",
        "retry_permitted",
        "scientific_result_eligible",
    )
    if any(receipt.get(name) is not False for name in false_fields):
        raise DiagnosticRefusal("V2 development-only nonclaim boundary changed")
    expected_inner = {
        "run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "success_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "certificate_sha256": EXPECTED_CERTIFICATE_SHA256,
        "execution_runtime_sha256": EXPECTED_EXECUTION_RUNTIME_SHA256,
        "source_manifest_sha256": EXPECTED_SOURCE_SHA256,
        "training_configuration_sha256": EXPECTED_CONFIGURATION_SHA256,
        "preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "optimizer_steps_taken": EXPECTED_UPDATES,
        "parent_confirmed_zero_child_exit": True,
        "inner_scientific_decision_eligible": False,
    }
    if any(inner.get(key) != value for key, value in expected_inner.items()):
        raise DiagnosticRefusal("V2 inner SUCCESS summary changed")
    if receipt.get("coordinate") != {
        "budget": EXPECTED_COORDINATE["budget"],
        "method": EXPECTED_COORDINATE["method"],
        "seed": EXPECTED_COORDINATE["seed"],
    }:
        raise DiagnosticRefusal("V2 coordinate changed")
    saved_inventory = receipt.get("artifact_inventory_before_receipt")
    if type(saved_inventory) is not list:
        raise DiagnosticRefusal("V2 outer receipt lacks its inventory")
    inventory = _inventory(artifact_root, exclude=("success-receipt.json",))
    if list(inventory) != saved_inventory:
        raise DiagnosticRefusal("V2 artifact inventory changed")
    inventory_sha = _sha256_bytes(
        _V2_INVENTORY_DOMAIN + _canonical_json_bytes(list(inventory))
    )
    if inventory_sha != EXPECTED_OUTER_INVENTORY_SHA256:
        raise DiagnosticRefusal("V2 artifact inventory digest changed")
    return {
        "receipt": receipt,
        "inventory": list(inventory),
        "inventory_sha256": inventory_sha,
        "outer_receipt_raw_sha256": EXPECTED_OUTER_RECEIPT_RAW_SHA256,
    }


def _validate_protected_roots_absent(root: Path) -> None:
    for relative in PROTECTED_PRODUCTION_RELATIVE_PATHS:
        path = root / relative
        if os.path.lexists(path):
            raise DiagnosticRefusal("protected production path exists: %s" % relative)


def _validate_machine_freeze(root: Path) -> Dict[str, object]:
    path = root / FREEZE_RELATIVE_PATH
    payload = _read_regular_bytes(path, maximum=4 * 1024 * 1024)
    freeze = _parse_json_object(payload)
    if freeze.get("schema") != (
        "heterodiff-a1-trained-development-checkpoint-diagnostic-freeze-v1"
    ):
        raise DiagnosticRefusal("D1 machine freeze schema is not final")
    if freeze.get("lane_id") != LANE_ID:
        raise DiagnosticRefusal("D1 lane identifier changed")
    bindings = freeze.get("implementation_binding")
    if type(bindings) is not dict:
        raise DiagnosticRefusal("D1 machine freeze lacks implementation bindings")
    required_files = (
        (
            "orchestration_source_path",
            "orchestration_source_sha256",
            IMPLEMENTATION_RELATIVE_PATH,
        ),
        ("runner_test_path", "runner_test_sha256", TEST_RELATIVE_PATH),
    )
    for path_field, digest_field, expected_path in required_files:
        if bindings.get(path_field) != expected_path:
            raise DiagnosticRefusal("D1 machine freeze path binding changed")
        digest = _require_sha256(bindings.get(digest_field), name=digest_field)
        if _file_sha256(root / expected_path) != digest:
            raise DiagnosticRefusal("D1 implementation binding changed: %s" % expected_path)
    human_digest = _file_sha256(root / HUMAN_FREEZE_RELATIVE_PATH)
    expected = freeze.get("v2_checkpoint_custody")
    if type(expected) is not dict:
        raise DiagnosticRefusal("D1 machine freeze lacks V2 custody")
    expected_pins = {
        "outer_success_receipt_raw_sha256": EXPECTED_OUTER_RECEIPT_RAW_SHA256,
        "outer_success_receipt_self_sha256": EXPECTED_OUTER_RECEIPT_SELF_SHA256,
        "inner_success_ledger_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "final_parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "certificate_sha256": EXPECTED_CERTIFICATE_SHA256,
        "execution_runtime_sha256": EXPECTED_EXECUTION_RUNTIME_SHA256,
        "source_manifest_sha256": EXPECTED_SOURCE_SHA256,
        "training_configuration_sha256": EXPECTED_CONFIGURATION_SHA256,
        "preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
    }
    if any(expected.get(key) != value for key, value in expected_pins.items()):
        raise DiagnosticRefusal("D1 machine freeze custody pins changed")
    fixture = freeze.get("fixture")
    runtime = freeze.get("runtime")
    family_freeze = freeze.get("family_supplement")
    if (
        type(fixture) is not dict
        or type(runtime) is not dict
        or type(family_freeze) is not dict
        or fixture.get("production_fixture_sha256") != EXPECTED_FIXTURE_SHA256
        or fixture.get("ordered_path_content_sha256")
        != EXPECTED_PATH_CONTENT_SHA256
        or fixture.get("edge_family_partition_sha256")
        != EXPECTED_FAMILY_PARTITION_SHA256
        or runtime.get("expected_path_runtime_sha256")
        != EXPECTED_PATH_RUNTIME_SHA256
        or family_freeze.get("edge_family_partition_sha256")
        != EXPECTED_FAMILY_PARTITION_SHA256
        or family_freeze.get("active_edge_counts")
        != {"birth": 30, "death": 30, "replacement": 60}
    ):
        raise DiagnosticRefusal("D1 fixture/path/family runtime pins changed")
    protocol = freeze.get("completion_contract")
    nonpath = freeze.get("nonpath_evaluation")
    paths = freeze.get("path_evaluation")
    family = freeze.get("family_supplement")
    training = freeze.get("training_boundary")
    scientific = freeze.get("scientific_boundary")
    authorization = freeze.get("authorization")
    if any(type(value) is not dict for value in (protocol, nonpath, paths, family, training)):
        raise DiagnosticRefusal("D1 machine freeze lacks protocol sections")
    if (
        protocol.get("eligible_complete_outcome") != STATUS
        or protocol.get("scope") != SCOPE
        or nonpath.get("all_33_times_required") is not True
        or nonpath.get("all_20_states_required") is not True
        or nonpath.get("all_21_observations_required") is not True
        or nonpath.get("classifier_grid_shape") != [33, 20, 21]
        or nonpath.get("terminal_guide_target_log_density_maximum_absolute_error")
        != NONPATH_TERMINAL_LOG_LIMIT
        or nonpath.get("maximum_terminal_residual") != NONPATH_COHERENCE_LIMIT
        or nonpath.get("generator_row_sum_maximum_absolute_residual")
        != NONPATH_COHERENCE_LIMIT
        or nonpath.get("scalar_edit_cycle_maximum_absolute_residual")
        != NONPATH_COHERENCE_LIMIT
        or paths.get("aggregate_all_21_observations_required") is not True
        or paths.get("reference_preflight_all_21_observations_required") is not True
        or paths.get("reference_preflight_must_pass_before_candidate_evaluation")
        is not True
        or family.get("all_21_observations_required") is not True
        or family.get("aggregate_initial_crosscheck_maximum_absolute_difference")
        != FAMILY_AGGREGATE_LIMIT
        or family.get("aggregate_dynamic_crosscheck_maximum_absolute_difference")
        != FAMILY_AGGREGATE_LIMIT
        or family.get("aggregate_total_crosscheck_maximum_absolute_difference")
        != FAMILY_AGGREGATE_LIMIT
        or family.get("opposing_family_error_cancellation_permitted") is not False
        or training
        != {
            "checkpoint_fine_tuning_permitted": False,
            "checkpoint_overwrite_permitted": False,
            "checkpoint_selection_permitted": False,
            "new_checkpoint_creation_permitted": False,
            "optimizer_construction_permitted": False,
            "optimizer_update_count": 0,
            "training_permitted": False,
        }
    ):
        raise DiagnosticRefusal("D1 frozen protocol changed")
    expected_scientific = {
        "c17_closed": False,
        "c17_theorem_proved": False,
        "claim_promotion": False,
        "confirmatory_execution": False,
        "confirmatory_result": False,
        "development_checkpoint_diagnostic_only": True,
        "full_fork_b_certificate_complete": False,
        "production_authorized": False,
        "production_order_admissible": False,
        "qualifies_r1": False,
        "qualifies_r2": False,
        "rigorous_numerical_enclosure_present": False,
        "scientific_result_eligible": False,
        "simultaneous_coverage_proved": False,
    }
    expected_authorization = {
        "current_state": "FROZEN_DIAGNOSTIC_EXECUTION_AUTHORIZED",
        "diagnostic_execution_authorized": True,
        "optimizer_permit_creation_authorized": False,
        "production_execution_authorized": False,
        "training_entry_point_authorized": False,
        "v2_checkpoint_read_only_access_authorized": True,
    }
    if scientific != expected_scientific or authorization != expected_authorization:
        raise DiagnosticRefusal("D1 frozen authorization/nonclaim boundary changed")
    attempt = freeze.get("attempt_policy")
    artifact = freeze.get("artifact_contract")
    if (
        type(attempt) is not dict
        or type(artifact) is not dict
        or attempt.get("attempt_count") != 1
        or attempt.get("retry_permitted") is not False
        or attempt.get("resume_permitted") is not False
        or attempt.get("durable_attempt_marker_path")
        != ATTEMPT_MARKER_RELATIVE_PATH
        or attempt.get("marker_committed_before_worker_launch") is not True
        or artifact.get("atomic_install_after_all_checks_pass") is not True
        or artifact.get("expected_output_root") != OUTPUT_RELATIVE_PATH
        or artifact.get("expected_output_regular_files_exact")
        != ["diagnostic-record.json", "success-receipt.json"]
        or artifact.get("bound_input_byte_copies_permitted_in_output") is not False
        or artifact.get(
            "published_records_collectively_bind_implementation_test_machine_and_human_freeze_sha256"
        )
        is not True
    ):
        raise DiagnosticRefusal("D1 one-attempt publication policy changed")
    return {
        "record": freeze,
        "raw_sha256": _sha256_bytes(payload),
        "implementation_sha256": bindings["orchestration_source_sha256"],
        "test_sha256": bindings["runner_test_sha256"],
        "human_freeze_sha256": human_digest,
    }


def _worker_environment(root: Path, request_sha256: str) -> Dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"):
            environment.pop(name, None)
    for name in _THREAD_VARIABLES:
        environment[name] = "1"
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONSAFEPATH": "1",
            "PYTHONPATH": str(root / V2_CAPSULE_RELATIVE_PATH / "src"),
            "HETERODIFF_D1_WORKER_REQUEST_SHA256": request_sha256,
        }
    )
    return environment


def _worker_command(root: Path) -> Tuple[str, ...]:
    python = root / TARGET_PYTHON_RELATIVE_PATH
    try:
        status = python.lstat()
        resolved = python.resolve(strict=True)
        resolved_status = resolved.stat()
    except OSError as error:
        raise DiagnosticRefusal("frozen target Python is absent") from error
    if not (stat.S_ISREG(status.st_mode) or stat.S_ISLNK(status.st_mode)):
        raise DiagnosticRefusal("frozen target Python path is invalid")
    if not stat.S_ISREG(resolved_status.st_mode) or not os.access(resolved, os.X_OK):
        raise DiagnosticRefusal("frozen target Python is not executable")
    return (
        str(python),
        "-P",
        "-B",
        str(root / IMPLEMENTATION_RELATIVE_PATH),
        "--worker",
    )


def _run_worker_subprocess(
    root: Path,
    *,
    implementation_sha256: str,
    freeze_sha256: str,
    human_freeze_sha256: str,
    attempt_marker: Mapping[str, object],
) -> Dict[str, object]:
    request = {
        "schema": "heterodiff-a1-trained-diagnostic-worker-request-v1",
        "lane_id": LANE_ID,
        "workspace_root": str(root),
        "implementation_sha256": implementation_sha256,
        "freeze_sha256": freeze_sha256,
        "human_freeze_sha256": human_freeze_sha256,
        "nonce": attempt_marker["nonce"],
        "attempt_marker_raw_sha256": attempt_marker["raw_sha256"],
        "attempt_marker_record_sha256": attempt_marker["record_sha256"],
    }
    request_bytes = _canonical_json_bytes(request)
    request_sha = _sha256_bytes(_WORKER_REQUEST_DOMAIN + request_bytes)
    try:
        completed = subprocess.run(
            _worker_command(root),
            input=request_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(root / V2_CAPSULE_RELATIVE_PATH),
            env=_worker_environment(root, request_sha),
            timeout=WORKER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise DiagnosticRefusal("D1 worker exceeded its frozen timeout") from error
    except OSError as error:
        raise DiagnosticRefusal("D1 worker could not be launched") from error
    if completed.returncode != 0:
        message = completed.stderr[:4096].decode("utf-8", errors="replace")
        raise DiagnosticRefusal(
            "D1 worker failed with return code %d: %s"
            % (completed.returncode, message)
        )
    if completed.stderr != b"":
        raise DiagnosticRefusal("D1 worker emitted unexpected stderr")
    if len(completed.stdout) > MAXIMUM_WORKER_OUTPUT_BYTES:
        raise DiagnosticRefusal("D1 worker output exceeds the frozen limit")
    if not completed.stdout.endswith(b"\n") or completed.stdout.count(b"\n") != 1:
        raise DiagnosticRefusal("D1 worker output is not one canonical JSON line")
    record = _parse_json_object(completed.stdout[:-1])
    if completed.stdout != _canonical_json_bytes(record) + b"\n":
        raise DiagnosticRefusal("D1 worker output is not canonical JSON")
    if record.get("worker_request_sha256") != request_sha:
        raise DiagnosticRefusal("D1 worker result is not bound to its parent request")
    return record


def _validate_coherence_record(coherence: object) -> None:
    value_names = {
        "terminal_maximum_absolute_log_information_error",
        "terminal_maximum_absolute_residual",
        "generator_row_sum_maximum_absolute_residual",
        "normalization_physical_weighted_rmse",
        "normalization_maximum_absolute_residual",
        "semigroup_physical_weighted_rmse",
        "semigroup_maximum_absolute_residual",
        "edit_cycle_maximum_absolute_residual",
    }
    if type(coherence) is not dict or set(coherence) != value_names | {
        "edit_cycle_count"
    }:
        raise DiagnosticRefusal("D1 nonpath coherence schema is not closed")
    values = {
        name: _finite_nonnegative(coherence.get(name), name="nonpath." + name)
        for name in value_names
    }
    count = coherence.get("edit_cycle_count")
    if type(count) is not int or count <= 0:
        raise DiagnosticRefusal("D1 nonpath edit-cycle count is invalid")
    thresholds = {
        "terminal_maximum_absolute_log_information_error": (
            NONPATH_TERMINAL_LOG_LIMIT
        ),
        "terminal_maximum_absolute_residual": NONPATH_COHERENCE_LIMIT,
        "generator_row_sum_maximum_absolute_residual": NONPATH_COHERENCE_LIMIT,
        "edit_cycle_maximum_absolute_residual": NONPATH_COHERENCE_LIMIT,
    }
    failed = [
        name for name, limit in thresholds.items() if values[name] > limit
    ]
    if failed:
        raise DiagnosticRefusal(
            "D1 nonpath frozen numerical gate failed: %s" % ", ".join(failed)
        )


def _validate_nonpath_record(nonpath: object) -> None:
    if type(nonpath) is not dict or set(nonpath) != NONPATH_RECORD_FIELDS:
        raise DiagnosticRefusal("D1 nonpath record schema is not closed")
    expected_identity = {
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "execution_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "production_bound": True,
    }
    if any(nonpath.get(name) != value for name, value in expected_identity.items()):
        raise DiagnosticRefusal("D1 nonpath checkpoint identity is invalid")
    for name in (
        "classifier_logit_grid",
        "log_information_grid",
        "residual_log_grid",
    ):
        _validate_array_descriptor(
            nonpath.get(name), name="nonpath." + name, shape=(33, 20, 21)
        )

    simple_groups = {
        "masked_excess_bce": {
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
        },
        "centered_log_information": {
            "physical_weighted_rmse",
            "maximum_absolute_error",
        },
    }
    for group_name, fields_expected in simple_groups.items():
        group = nonpath.get(group_name)
        if type(group) is not dict or set(group) != fields_expected:
            raise DiagnosticRefusal("D1 nonpath %s schema is not closed" % group_name)
        for name in fields_expected:
            _finite_nonnegative(group.get(name), name=group_name + "." + name)

    residual = nonpath.get("residual")
    residual_fields = {
        "physical_weighted_rmse",
        "maximum_absolute_error",
        "candidate_minimum",
        "candidate_maximum",
        "candidate_range",
        "oracle_minimum",
        "oracle_maximum",
        "oracle_range",
    }
    if type(residual) is not dict or set(residual) != residual_fields:
        raise DiagnosticRefusal("D1 nonpath residual schema is not closed")
    for name in ("physical_weighted_rmse", "maximum_absolute_error"):
        _finite_nonnegative(residual.get(name), name="nonpath residual " + name)
    for prefix in ("candidate", "oracle"):
        minimum = _finite_number(
            residual.get(prefix + "_minimum"), name=prefix + " residual minimum"
        )
        maximum = _finite_number(
            residual.get(prefix + "_maximum"), name=prefix + " residual maximum"
        )
        span = _finite_nonnegative(
            residual.get(prefix + "_range"), name=prefix + " residual range"
        )
        if maximum < minimum or not _numerically_equal(span, maximum - minimum):
            raise DiagnosticRefusal("D1 nonpath residual range is inconsistent")

    edge = nonpath.get("edge_log_rates")
    if type(edge) is not dict or set(edge) != set(FAMILY_ORDER):
        raise DiagnosticRefusal("D1 nonpath edge-family schema is not closed")
    edge_fields = {
        "family",
        "active_edge_count",
        "physical_weight",
        "physical_weighted_rmse",
        "maximum_absolute_error",
        "weighted_median_absolute_error",
    }
    for index, name in enumerate(FAMILY_ORDER):
        group = edge.get(name)
        if (
            type(group) is not dict
            or set(group) != edge_fields
            or group.get("family") != name
            or group.get("active_edge_count") != EXPECTED_FAMILY_EDGE_COUNTS[index]
        ):
            raise DiagnosticRefusal("D1 nonpath edge-family identity is invalid")
        for field in edge_fields - {"family", "active_edge_count"}:
            value = _finite_nonnegative(
                group.get(field), name="nonpath edge " + name + "." + field
            )
            if field == "physical_weight" and value <= 0.0:
                raise DiagnosticRefusal("D1 nonpath edge physical weight is zero")

    initial_tv = nonpath.get("conditional_initial_tv")
    initial_fields = {
        "per_observation",
        "observation_weighted_mean",
        "retained_observation_weighted_mean",
        "maximum",
        "overflow",
    }
    if type(initial_tv) is not dict or set(initial_tv) != initial_fields:
        raise DiagnosticRefusal("D1 nonpath initial-TV schema is not closed")
    _validate_array_descriptor(
        initial_tv.get("per_observation"),
        name="nonpath conditional_initial_tv.per_observation",
        shape=(21,),
    )
    for name in initial_fields - {"per_observation"}:
        _finite_nonnegative(initial_tv.get(name), name="nonpath initial TV " + name)

    calibration = nonpath.get("calibration")
    calibration_fields = {
        "brier",
        "optimal_brier",
        "excess_brier",
        "reliability_ece",
        "maximum_reliability_gap",
        "bin_mass",
        "bin_mean_prediction",
        "bin_positive_frequency",
    }
    if type(calibration) is not dict or set(calibration) != calibration_fields:
        raise DiagnosticRefusal("D1 nonpath calibration schema is not closed")
    for name in (
        "brier",
        "optimal_brier",
        "excess_brier",
        "reliability_ece",
        "maximum_reliability_gap",
    ):
        _finite_nonnegative(calibration.get(name), name="nonpath calibration " + name)
    for name in ("bin_mass", "bin_mean_prediction", "bin_positive_frequency"):
        _validate_array_descriptor(
            calibration.get(name), name="nonpath calibration " + name, shape=(10,)
        )

    _validate_coherence_record(nonpath.get("coherence"))


def _require_worker_nonpath_gates(nonpath: object) -> None:
    coherence = getattr(nonpath, "coherence", None)
    if coherence is None:
        raise DiagnosticRefusal("D1 nonpath evaluation lacks coherence diagnostics")
    _validate_coherence_record(
        {
            name: getattr(coherence, name)
            for name in (
                "terminal_maximum_absolute_log_information_error",
                "terminal_maximum_absolute_residual",
                "generator_row_sum_maximum_absolute_residual",
                "normalization_physical_weighted_rmse",
                "normalization_maximum_absolute_residual",
                "semigroup_physical_weighted_rmse",
                "semigroup_maximum_absolute_residual",
                "edit_cycle_maximum_absolute_residual",
                "edit_cycle_count",
            )
        }
    )


def _validate_runtime_record(runtime: object) -> None:
    if runtime != EXPECTED_PATH_RUNTIME:
        raise DiagnosticRefusal("D1 path runtime record changed")


def _validate_solver_record(settings: object, *, refined: bool) -> None:
    expected = (
        EXPECTED_REFINED_SOLVER_SETTINGS
        if refined
        else EXPECTED_PRIMARY_SOLVER_SETTINGS
    )
    if settings != expected:
        raise DiagnosticRefusal("D1 path solver settings changed")


def _validate_reference_record(
    reference: object, *, observation_index: int
) -> float:
    if type(reference) is not dict or set(reference) != PATH_REFERENCE_FIELDS:
        raise DiagnosticRefusal("D1 path reference schema is not closed")
    if (
        reference.get("frozen_fixture_sha256") != EXPECTED_FIXTURE_SHA256
        or reference.get("fixture_content_sha256") != EXPECTED_PATH_CONTENT_SHA256
        or type(reference.get("observation_index")) is not int
        or reference.get("observation_index") != observation_index
    ):
        raise DiagnosticRefusal("D1 path reference identity is invalid")
    _require_sha256(reference.get("reference_sha256"), name="path reference sha256")
    _validate_runtime_record(reference.get("runtime"))
    _validate_solver_record(reference.get("primary_solver_settings"), refined=False)
    _validate_solver_record(reference.get("refined_solver_settings"), refined=True)
    mass = _finite_nonnegative(
        reference.get("observation_mass"), name="path reference mass"
    )
    baseline = _finite_nonnegative(
        reference.get("unconditional_path_kl"), name="unconditional path KL"
    )
    refined_baseline = _finite_nonnegative(
        reference.get("refined_unconditional_path_kl"),
        name="refined unconditional path KL",
    )
    change = _finite_nonnegative(
        reference.get("primary_refined_unconditional_path_kl_change"),
        name="unconditional path refinement",
    )
    oracle_self = _finite_nonnegative(
        reference.get("oracle_self_path_kl"), name="oracle self path KL"
    )
    target_error = _finite_nonnegative(
        reference.get("target_marginal_maximum_absolute_error"),
        name="reference target-marginal error",
    )
    normalizer = _finite_nonnegative(
        reference.get("target_initial_normalizer"),
        name="reference initial normalizer",
    )
    if (
        mass <= 0.0
        or baseline <= 1.0e-12
        or refined_baseline <= 1.0e-12
        or normalizer <= 0.0
        or oracle_self > 1.0e-10
        or target_error > TARGET_MARGINAL_LIMIT
        or change > PRIMARY_REFINED_LIMIT
        or not _numerically_equal(change, abs(baseline - refined_baseline))
    ):
        raise DiagnosticRefusal("D1 path reference numerical preflight failed")
    _validate_array_descriptor(
        reference.get("target_initial_law"),
        name="path reference target_initial_law",
        shape=(20,),
    )
    _validate_array_descriptor(
        reference.get("target_generator_grid"),
        name="path reference target_generator_grid",
        shape=(33, 20, 20),
    )
    for name in (
        "oracle_self_potential_evaluations",
        "unconditional_potential_evaluations",
        "refined_unconditional_potential_evaluations",
    ):
        if type(reference.get(name)) is not int or reference.get(name) <= 0:
            raise DiagnosticRefusal("D1 path reference evaluation count is invalid")
    return mass


def _validate_path_reference_preflight(preflight: object) -> Tuple[Dict[str, object], ...]:
    if type(preflight) is not dict or set(preflight) != PATH_REFERENCE_SET_FIELDS:
        raise DiagnosticRefusal("D1 path-reference preflight schema is not closed")
    if (
        preflight.get("frozen_fixture_sha256") != EXPECTED_FIXTURE_SHA256
        or preflight.get("fixture_content_sha256") != EXPECTED_PATH_CONTENT_SHA256
    ):
        raise DiagnosticRefusal("D1 path-reference preflight identity is invalid")
    _validate_runtime_record(preflight.get("runtime"))
    _validate_solver_record(preflight.get("primary_solver_settings"), refined=False)
    _validate_solver_record(preflight.get("refined_solver_settings"), refined=True)
    reference_set_sha256 = _require_sha256(
        preflight.get("reference_set_sha256"), name="path reference-set sha256"
    )
    references = preflight.get("references")
    if type(references) is not list or len(references) != 21:
        raise DiagnosticRefusal("D1 path-reference preflight lacks 21 observations")
    masses = [
        _validate_reference_record(reference, observation_index=index)
        for index, reference in enumerate(references)
    ]
    if not _numerically_equal(math.fsum(masses), 1.0):
        raise DiagnosticRefusal("D1 path-reference masses do not sum to one")
    if reference_set_sha256 != _reference_set_record_sha256(references):
        raise DiagnosticRefusal("D1 path reference-set digest is inconsistent")
    return tuple(references)


def _validate_aggregate_path(
    aggregate: object, references: Sequence[Mapping[str, object]]
) -> Tuple[Dict[str, object], ...]:
    if type(aggregate) is not dict or set(aggregate) != AGGREGATE_PATH_FIELDS:
        raise DiagnosticRefusal("D1 aggregate path schema is not closed")
    expected_identity = {
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "execution_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "production_bound": True,
    }
    if (
        any(aggregate.get(name) != value for name, value in expected_identity.items())
        or aggregate.get("numerical_gate_failures") != []
    ):
        raise DiagnosticRefusal("D1 aggregate path identity or gate is invalid")
    _require_sha256(
        aggregate.get("reference_set_sha256"), name="aggregate reference-set sha256"
    )
    observations = aggregate.get("observations")
    if type(observations) is not list or len(observations) != 21:
        raise DiagnosticRefusal("D1 aggregate path lacks 21 observations")

    array_shapes = {
        "candidate_initial_law": (20,),
        "candidate_generator_grid": (33, 20, 20),
        "target_marginals": (33, 20),
        "candidate_marginals": (33, 20),
        "target_integrated_occupation": (20,),
        "candidate_integrated_occupation": (20,),
        "marginal_total_variation": (33,),
    }
    scalar_names = (
        "candidate_initial_normalizer",
        "path_kl_initial",
        "path_kl_dynamic",
        "path_kl_total",
        "normalized_path_kl",
        "maximum_intermediate_total_variation",
        "endpoint_total_variation",
        "primary_refined_path_kl_change",
        "primary_refined_endpoint_total_variation",
        "primary_path_quadrature_error",
        "refined_path_quadrature_error",
        "primary_target_marginal_maximum_absolute_error",
    )
    scalar_rows = []
    for index, (observation, reference) in enumerate(zip(observations, references)):
        if (
            type(observation) is not dict
            or set(observation) != AGGREGATE_OBSERVATION_FIELDS
        ):
            raise DiagnosticRefusal("D1 aggregate observation schema is not closed")
        if (
            any(
                observation.get(name) != value
                for name, value in expected_identity.items()
            )
            or observation.get("reference") != reference
            or reference.get("observation_index") != index
        ):
            raise DiagnosticRefusal("D1 aggregate observation identity is invalid")
        _validate_solver_record(observation.get("primary_solver_settings"), refined=False)
        _validate_solver_record(observation.get("refined_solver_settings"), refined=True)
        for name, shape in array_shapes.items():
            _validate_array_descriptor(
                observation.get(name), name="aggregate observation " + name, shape=shape
            )
        values = {
            name: _finite_nonnegative(
                observation.get(name), name="aggregate observation " + name
            )
            for name in scalar_names
        }
        if (
            values["candidate_initial_normalizer"] <= 0.0
            or not _numerically_equal(
                values["path_kl_total"],
                values["path_kl_initial"] + values["path_kl_dynamic"],
            )
            or not _numerically_equal(
                values["normalized_path_kl"],
                values["path_kl_total"] / float(reference["unconditional_path_kl"]),
            )
            or values["primary_refined_path_kl_change"] > PRIMARY_REFINED_LIMIT
            or values["primary_refined_endpoint_total_variation"]
            > PRIMARY_REFINED_LIMIT
            or values["primary_target_marginal_maximum_absolute_error"]
            > TARGET_MARGINAL_LIMIT
        ):
            raise DiagnosticRefusal("D1 aggregate observation numerical gate failed")
        for name in (
            "primary_path_potential_evaluations",
            "refined_path_potential_evaluations",
            "primary_candidate_occupancy_potential_evaluations",
            "refined_candidate_occupancy_potential_evaluations",
        ):
            if type(observation.get(name)) is not int or observation.get(name) <= 0:
                raise DiagnosticRefusal("D1 aggregate evaluation count is invalid")
        scalar_rows.append(values)

    float_vectors = {
        "observation_mass": [float(item["observation_mass"]) for item in references],
        "path_kl_per_observation": [item["path_kl_total"] for item in scalar_rows],
        "unconditional_path_kl_per_observation": [
            float(item["unconditional_path_kl"]) for item in references
        ],
        "normalized_path_kl_per_observation": [
            item["normalized_path_kl"] for item in scalar_rows
        ],
        "endpoint_total_variation_per_observation": [
            item["endpoint_total_variation"] for item in scalar_rows
        ],
        "maximum_intermediate_total_variation_per_observation": [
            item["maximum_intermediate_total_variation"] for item in scalar_rows
        ],
    }
    for name, values in float_vectors.items():
        digest = _validate_array_descriptor(
            aggregate.get(name), name="aggregate " + name, shape=(21,)
        )
        if digest != _array_sha256(values):
            raise DiagnosticRefusal("D1 aggregate array digest is inconsistent")

    ambiguous_indices = (8, 7, 5)
    import numpy as np

    index_digest = _validate_array_descriptor(
        aggregate.get("ambiguous_observation_indices"),
        name="aggregate ambiguous_observation_indices",
        shape=(3,),
        dtype="<i8",
    )
    if index_digest != _array_sha256(np.asarray(ambiguous_indices, dtype=np.int64)):
        raise DiagnosticRefusal("D1 aggregate ambiguous indices changed")
    ambiguous_values = [
        scalar_rows[index]["normalized_path_kl"] for index in ambiguous_indices
    ]
    if _validate_array_descriptor(
        aggregate.get("ambiguous_normalized_path_kl"),
        name="aggregate ambiguous_normalized_path_kl",
        shape=(3,),
    ) != _array_sha256(ambiguous_values):
        raise DiagnosticRefusal("D1 aggregate ambiguous values are inconsistent")

    masses = float_vectors["observation_mass"]
    path_values = float_vectors["path_kl_per_observation"]
    baseline_values = float_vectors["unconditional_path_kl_per_observation"]
    endpoint_values = float_vectors["endpoint_total_variation_per_observation"]
    retained_mass = math.fsum(masses[:-1])
    retained_path = math.fsum(
        mass * value for mass, value in zip(masses[:-1], path_values[:-1])
    )
    retained_baseline = math.fsum(
        mass * value for mass, value in zip(masses[:-1], baseline_values[:-1])
    )
    expected_summaries = {
        "observation_weighted_path_kl": math.fsum(
            mass * value for mass, value in zip(masses, path_values)
        ),
        "retained_path_kl_mean": retained_path / retained_mass,
        "retained_normalized_path_score": retained_path / retained_baseline,
        "overflow_path_kl": path_values[-1],
        "overflow_normalized_path_score": scalar_rows[-1]["normalized_path_kl"],
        "observation_weighted_endpoint_total_variation": math.fsum(
            mass * value for mass, value in zip(masses, endpoint_values)
        ),
        "retained_endpoint_total_variation_mean": math.fsum(
            mass * value for mass, value in zip(masses[:-1], endpoint_values[:-1])
        )
        / retained_mass,
        "overflow_endpoint_total_variation": endpoint_values[-1],
        "ambiguous_normalized_path_score": math.fsum(ambiguous_values) / 3.0,
    }
    for name, expected in expected_summaries.items():
        actual = _finite_nonnegative(aggregate.get(name), name="aggregate " + name)
        if not _numerically_equal(actual, expected):
            raise DiagnosticRefusal("D1 aggregate summary is inconsistent")
    return tuple(observations)


def _validate_evidence_binding(evidence: object) -> None:
    expected = {
        "coordinate": [
            EXPECTED_COORDINATE["seed"],
            EXPECTED_COORDINATE["budget"],
            EXPECTED_COORDINATE["method"],
        ],
        "run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "success_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "certificate_sha256": EXPECTED_CERTIFICATE_SHA256,
        "optimizer_steps_taken": EXPECTED_UPDATES,
        "nonpath_identity_matches": True,
        "aggregate_path_identity_matches": True,
        "internal_analysis_only": True,
    }
    if (
        type(evidence) is not dict
        or set(evidence) != EVIDENCE_BINDING_FIELDS
        or evidence != expected
    ):
        raise DiagnosticRefusal("D1 evidence binding is incomplete")


def _validate_execution_runtime(runtime: object) -> None:
    expected = {
        "python": "3.11.5",
        "numpy": "2.4.6",
        "path_runtime": EXPECTED_PATH_RUNTIME,
        "path_runtime_sha256": EXPECTED_PATH_RUNTIME_SHA256,
        "thread_environment": {name: "1" for name in _THREAD_VARIABLES},
        "pythonhashseed": "0",
        "cuda_visible_devices": "",
        "capsule_source_only": True,
    }
    if type(runtime) is not dict or runtime != expected:
        raise DiagnosticRefusal("D1 execution runtime record is incomplete")


def _validate_cross_section_consistency(
    family: Mapping[str, object],
    references: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
) -> None:
    rows = family["observations"]
    for index, (row, reference, observation) in enumerate(
        zip(rows, references, observations)
    ):
        if (
            row.get("observation_index") != index
            or not _numerically_equal(
                float(row["observation_mass"]), float(reference["observation_mass"])
            )
        ):
            raise DiagnosticRefusal("D1 family/reference observation binding changed")
        for row_name, observation_name in (
            ("public_primary_aggregate_initial", "path_kl_initial"),
            ("public_primary_aggregate_dynamic", "path_kl_dynamic"),
            ("public_primary_aggregate_total", "path_kl_total"),
        ):
            if not _numerically_equal(
                float(row[row_name]), float(observation[observation_name])
            ):
                raise DiagnosticRefusal("D1 family/public aggregate binding changed")


def _validate_family_supplement(family: object) -> None:
    expected_fields = {
        "schema_version",
        "orientation",
        "family_names",
        "component_order",
        "continuous_component_disposition",
        "active_edge_counts",
        "edge_family_partition_sha256",
        "observation_count",
        "observations",
        "observation_weighted_initial",
        "observation_weighted_birth",
        "observation_weighted_death",
        "observation_weighted_replacement",
        "observation_weighted_total",
        "maximum_primary_refined_component_change",
        "maximum_family_aggregate_crosscheck_absolute_difference",
        "maximum_target_marginal_absolute_error",
        "maximum_terminal_log_potential_absolute_error",
        "interval_certified",
        "rigorous_numerical_enclosure_present",
        "numerical_failures",
    }
    if type(family) is not dict or set(family) != expected_fields:
        raise DiagnosticRefusal("D1 family supplement schema is not closed")
    if (
        family.get("schema_version")
        != "heterodiff-a1-trained-family-supplement-v1"
        or family.get("orientation")
        != "KL(P_EXACT_TARGET_H || P_TRAINED_CHECKPOINT_H_HAT)"
        or family.get("family_names") != list(FAMILY_ORDER)
        or family.get("component_order") != list(COMPONENT_ORDER)
        or family.get("active_edge_counts") != list(EXPECTED_FAMILY_EDGE_COUNTS)
        or family.get("edge_family_partition_sha256")
        != EXPECTED_FAMILY_PARTITION_SHA256
        or family.get("continuous_component_disposition")
        != CONTINUOUS_DISPOSITION
        or family.get("observation_count") != 21
        or family.get("interval_certified") is not False
        or family.get("rigorous_numerical_enclosure_present") is not False
        or family.get("numerical_failures") != []
    ):
        raise DiagnosticRefusal("D1 family supplement identity is invalid")
    rows = family.get("observations")
    if type(rows) is not list or len(rows) != 21:
        raise DiagnosticRefusal("D1 family supplement lacks exactly 21 rows")

    row_fields = {
        "observation_index",
        "observation_mass",
        "components",
        "primary_family_orientation",
        "refined_family_orientation",
        "primary_family_supplied_reference_marginal_used",
        "refined_family_supplied_reference_marginal_used",
        "primary_dynamic",
        "primary_total",
        "refined_dynamic",
        "refined_total",
        "separate_primary_aggregate_initial",
        "separate_primary_aggregate_dynamic",
        "separate_primary_aggregate_total",
        "separate_refined_aggregate_initial",
        "separate_refined_aggregate_dynamic",
        "separate_refined_aggregate_total",
        "public_primary_aggregate_initial",
        "public_primary_aggregate_dynamic",
        "public_primary_aggregate_total",
        "refinements",
        "crosschecks",
        "target_marginal_maximum_absolute_error",
        "primary_family_occupancy_target_maximum_absolute_error",
        "refined_family_occupancy_target_maximum_absolute_error",
        "terminal_log_potential_maximum_absolute_error",
        "primary_family_quadrature_error_estimate",
        "refined_family_quadrature_error_estimate",
        "numerical_failures",
    }
    component_fields = {
        "component_id",
        "applicability",
        "target_measure",
        "primary",
        "refined",
        "primary_refined_absolute_difference",
        "active_aggregate_edge_count",
        "entered_total",
        "interval_certified",
    }
    expected_metadata = (
        ("APPLICABLE", "EXACT_CONDITIONED_TARGET_INITIAL_LAW", 0, True),
        (CONTINUOUS_DISPOSITION, CONTINUOUS_DISPOSITION, 0, False),
        (
            "APPLICABLE",
            "EXACT_CONDITIONED_TARGET_OCCUPATION",
            EXPECTED_FAMILY_EDGE_COUNTS[0],
            True,
        ),
        (
            "APPLICABLE",
            "EXACT_CONDITIONED_TARGET_OCCUPATION",
            EXPECTED_FAMILY_EDGE_COUNTS[1],
            True,
        ),
        (
            "APPLICABLE",
            "EXACT_CONDITIONED_TARGET_OCCUPATION",
            EXPECTED_FAMILY_EDGE_COUNTS[2],
            True,
        ),
    )
    masses = []
    primary_components = [[] for _ in COMPONENT_ORDER]
    refinements_seen = []
    crosschecks_seen = []
    target_errors = []
    terminal_errors = []
    row_primary_totals = []
    for expected_index, row in enumerate(rows):
        if type(row) is not dict or set(row) != row_fields:
            raise DiagnosticRefusal("D1 family row schema is not closed")
        if type(row.get("observation_index")) is not int or row.get(
            "observation_index"
        ) != expected_index:
            raise DiagnosticRefusal("D1 family observation order is invalid")
        mass = _finite_nonnegative(
            row.get("observation_mass"), name="family observation mass"
        )
        if mass <= 0.0:
            raise DiagnosticRefusal("D1 family observation mass is not positive")
        masses.append(mass)
        if (
            row.get("primary_family_orientation")
            != "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
            or row.get("refined_family_orientation")
            != "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
            or row.get("primary_family_supplied_reference_marginal_used") is not True
            or row.get("refined_family_supplied_reference_marginal_used") is not True
            or row.get("numerical_failures") != []
        ):
            raise DiagnosticRefusal("D1 family solver contract is invalid")
        components = row.get("components")
        if type(components) is not list or len(components) != len(COMPONENT_ORDER):
            raise DiagnosticRefusal("D1 family row lacks five ordered components")
        primary = []
        refined = []
        component_changes = []
        for position, (component, metadata) in enumerate(
            zip(components, expected_metadata)
        ):
            if type(component) is not dict or set(component) != component_fields:
                raise DiagnosticRefusal("D1 family component schema is not closed")
            applicability, target_measure, edge_count, entered = metadata
            if (
                component.get("component_id") != COMPONENT_ORDER[position]
                or component.get("applicability") != applicability
                or component.get("target_measure") != target_measure
                or component.get("active_aggregate_edge_count") != edge_count
                or component.get("entered_total") is not entered
                or component.get("interval_certified") is not False
            ):
                raise DiagnosticRefusal("D1 family component metadata is invalid")
            if position == 1:
                if any(
                    component.get(name) is not None
                    for name in (
                        "primary",
                        "refined",
                        "primary_refined_absolute_difference",
                    )
                ):
                    raise DiagnosticRefusal("D1 KC component is not N/A")
                continue
            primary_value = _finite_nonnegative(
                component.get("primary"), name="family component primary"
            )
            refined_value = _finite_nonnegative(
                component.get("refined"), name="family component refined"
            )
            change = _finite_nonnegative(
                component.get("primary_refined_absolute_difference"),
                name="family component refinement",
            )
            if (
                not _numerically_equal(change, abs(primary_value - refined_value))
                or change > PRIMARY_REFINED_LIMIT
            ):
                raise DiagnosticRefusal("D1 family component refinement is invalid")
            primary.append(primary_value)
            refined.append(refined_value)
            component_changes.append(change)
            primary_components[position].append(primary_value)

        numeric_names = (
            "primary_dynamic",
            "primary_total",
            "refined_dynamic",
            "refined_total",
            "separate_primary_aggregate_initial",
            "separate_primary_aggregate_dynamic",
            "separate_primary_aggregate_total",
            "separate_refined_aggregate_initial",
            "separate_refined_aggregate_dynamic",
            "separate_refined_aggregate_total",
            "public_primary_aggregate_initial",
            "public_primary_aggregate_dynamic",
            "public_primary_aggregate_total",
            "target_marginal_maximum_absolute_error",
            "primary_family_occupancy_target_maximum_absolute_error",
            "refined_family_occupancy_target_maximum_absolute_error",
            "terminal_log_potential_maximum_absolute_error",
            "primary_family_quadrature_error_estimate",
            "refined_family_quadrature_error_estimate",
        )
        values = {
            name: _finite_nonnegative(row.get(name), name="family row " + name)
            for name in numeric_names
        }
        primary_dynamic = math.fsum(primary[1:])
        refined_dynamic = math.fsum(refined[1:])
        internal_equalities = (
            (values["primary_dynamic"], primary_dynamic),
            (values["primary_total"], primary[0] + primary_dynamic),
            (values["refined_dynamic"], refined_dynamic),
            (values["refined_total"], refined[0] + refined_dynamic),
            (
                values["separate_primary_aggregate_total"],
                values["separate_primary_aggregate_initial"]
                + values["separate_primary_aggregate_dynamic"],
            ),
            (
                values["separate_refined_aggregate_total"],
                values["separate_refined_aggregate_initial"]
                + values["separate_refined_aggregate_dynamic"],
            ),
            (
                values["public_primary_aggregate_total"],
                values["public_primary_aggregate_initial"]
                + values["public_primary_aggregate_dynamic"],
            ),
        )
        if any(not _numerically_equal(left, right) for left, right in internal_equalities):
            raise DiagnosticRefusal("D1 family component sums are inconsistent")

        refinements = row.get("refinements")
        if type(refinements) is not dict or set(refinements) != set(
            FAMILY_REFINEMENT_NAMES
        ):
            raise DiagnosticRefusal("D1 family refinement schema is not closed")
        checked_refinements = {
            name: _finite_nonnegative(
                refinements.get(name), name="family refinement " + name
            )
            for name in FAMILY_REFINEMENT_NAMES
        }
        expected_refinements = {
            "initial": component_changes[0],
            "birth": component_changes[1],
            "death": component_changes[2],
            "replacement": component_changes[3],
            "total": abs(values["primary_total"] - values["refined_total"]),
        }
        if any(
            value > PRIMARY_REFINED_LIMIT
            or not _numerically_equal(value, expected_refinements[name])
            for name, value in checked_refinements.items()
        ):
            raise DiagnosticRefusal("D1 family row refinements are invalid")
        refinements_seen.extend(checked_refinements.values())

        crosschecks = row.get("crosschecks")
        if type(crosschecks) is not dict or set(crosschecks) != set(
            FAMILY_CROSSCHECK_NAMES
        ):
            raise DiagnosticRefusal("D1 family crosscheck schema is not closed")
        expected_crosschecks = {
            FAMILY_CROSSCHECK_NAMES[0]: abs(
                primary[0] - values["separate_primary_aggregate_initial"]
            ),
            FAMILY_CROSSCHECK_NAMES[1]: abs(
                values["primary_dynamic"]
                - values["separate_primary_aggregate_dynamic"]
            ),
            FAMILY_CROSSCHECK_NAMES[2]: abs(
                values["primary_total"]
                - values["separate_primary_aggregate_total"]
            ),
            FAMILY_CROSSCHECK_NAMES[3]: abs(
                refined[0] - values["separate_refined_aggregate_initial"]
            ),
            FAMILY_CROSSCHECK_NAMES[4]: abs(
                values["refined_dynamic"]
                - values["separate_refined_aggregate_dynamic"]
            ),
            FAMILY_CROSSCHECK_NAMES[5]: abs(
                values["refined_total"]
                - values["separate_refined_aggregate_total"]
            ),
            FAMILY_CROSSCHECK_NAMES[6]: abs(
                values["separate_primary_aggregate_initial"]
                - values["public_primary_aggregate_initial"]
            ),
            FAMILY_CROSSCHECK_NAMES[7]: abs(
                values["separate_primary_aggregate_dynamic"]
                - values["public_primary_aggregate_dynamic"]
            ),
            FAMILY_CROSSCHECK_NAMES[8]: abs(
                values["separate_primary_aggregate_total"]
                - values["public_primary_aggregate_total"]
            ),
        }
        checked_crosschecks = {
            name: _finite_nonnegative(
                crosschecks.get(name), name="family crosscheck " + name
            )
            for name in FAMILY_CROSSCHECK_NAMES
        }
        if any(
            value > FAMILY_AGGREGATE_LIMIT
            or not _numerically_equal(value, expected_crosschecks[name])
            for name, value in checked_crosschecks.items()
        ):
            raise DiagnosticRefusal("D1 family row crosschecks are invalid")
        crosschecks_seen.extend(checked_crosschecks.values())

        row_target_errors = (
            values["target_marginal_maximum_absolute_error"],
            values["primary_family_occupancy_target_maximum_absolute_error"],
            values["refined_family_occupancy_target_maximum_absolute_error"],
        )
        if max(row_target_errors) > TARGET_MARGINAL_LIMIT:
            raise DiagnosticRefusal("D1 family target-marginal gate failed")
        if values["terminal_log_potential_maximum_absolute_error"] > TERMINAL_LIMIT:
            raise DiagnosticRefusal("D1 family terminal gate failed")
        target_errors.extend(row_target_errors)
        terminal_errors.append(
            values["terminal_log_potential_maximum_absolute_error"]
        )
        row_primary_totals.append(values["primary_total"])

    if not _numerically_equal(math.fsum(masses), 1.0):
        raise DiagnosticRefusal("D1 family observation masses do not sum to one")

    weighted_values = []
    for values in primary_components:
        if not values:
            weighted_values.append(None)
        else:
            weighted_values.append(
                math.fsum(mass * value for mass, value in zip(masses, values))
            )
    expected_weighted = {
        "observation_weighted_initial": weighted_values[0],
        "observation_weighted_birth": weighted_values[2],
        "observation_weighted_death": weighted_values[3],
        "observation_weighted_replacement": weighted_values[4],
        "observation_weighted_total": math.fsum(
            mass * value for mass, value in zip(masses, row_primary_totals)
        ),
    }
    checked_weighted = {
        name: _finite_nonnegative(family.get(name), name="family " + name)
        for name in expected_weighted
    }
    if any(
        expected is None or not _numerically_equal(checked_weighted[name], expected)
        for name, expected in expected_weighted.items()
    ) or not _numerically_equal(
        checked_weighted["observation_weighted_total"],
        math.fsum(
            checked_weighted[name]
            for name in (
                "observation_weighted_initial",
                "observation_weighted_birth",
                "observation_weighted_death",
                "observation_weighted_replacement",
            )
        ),
    ):
        raise DiagnosticRefusal("D1 family weighted summaries are inconsistent")

    maxima = {
        "maximum_primary_refined_component_change": max(refinements_seen),
        "maximum_family_aggregate_crosscheck_absolute_difference": max(
            crosschecks_seen
        ),
        "maximum_target_marginal_absolute_error": max(target_errors),
        "maximum_terminal_log_potential_absolute_error": max(terminal_errors),
    }
    for name, expected in maxima.items():
        actual = _finite_nonnegative(family.get(name), name="family " + name)
        if not _numerically_equal(actual, expected):
            raise DiagnosticRefusal("D1 family maximum summary is inconsistent")
    if (
        maxima["maximum_primary_refined_component_change"] > PRIMARY_REFINED_LIMIT
        or maxima["maximum_family_aggregate_crosscheck_absolute_difference"]
        > FAMILY_AGGREGATE_LIMIT
        or maxima["maximum_target_marginal_absolute_error"] > TARGET_MARGINAL_LIMIT
        or maxima["maximum_terminal_log_potential_absolute_error"] > TERMINAL_LIMIT
    ):
        raise DiagnosticRefusal("D1 family aggregate numerical gate failed")


def _validate_worker_record(record: Mapping[str, object]) -> None:
    expected_top_level = {
        "schema_version",
        "lane_id",
        "status",
        "scope",
        "worker_request_sha256",
        "implementation_sha256",
        "freeze_sha256",
        "human_freeze_sha256",
        "attempt_marker",
        "checkpoint_custody",
        "coverage",
        "runtime",
        "nonpath",
        "path_reference_preflight",
        "aggregate_path",
        "evidence_binding",
        "family_supplement",
        "numerical_disposition",
        "nonclaims",
        "diagnostic_record_sha256",
    }
    if set(record) != expected_top_level:
        raise DiagnosticRefusal("D1 worker record top-level schema is not closed")
    for name in (
        "worker_request_sha256",
        "implementation_sha256",
        "freeze_sha256",
        "human_freeze_sha256",
    ):
        _require_sha256(record.get(name), name=name)
    if (
        record.get("schema_version") != SCHEMA_VERSION
        or record.get("lane_id") != LANE_ID
        or record.get("status") != STATUS
        or record.get("scope") != SCOPE
    ):
        raise DiagnosticRefusal("D1 worker returned the wrong result identity")
    claimed = _require_sha256(
        record.get("diagnostic_record_sha256"), name="diagnostic_record_sha256"
    )
    if _self_digest(record, field="diagnostic_record_sha256", domain=_RECORD_DOMAIN) != claimed:
        raise DiagnosticRefusal("D1 worker record self-digest is inconsistent")
    attempt = record.get("attempt_marker")
    if (
        type(attempt) is not dict
        or set(attempt)
        != {"path", "state", "attempt_number", "raw_sha256", "record_sha256"}
        or attempt.get("path") != ATTEMPT_MARKER_RELATIVE_PATH
        or attempt.get("state") != "ATTEMPT_CONSUMED_NONRETRYABLE"
        or attempt.get("attempt_number") != 1
    ):
        raise DiagnosticRefusal("D1 worker lacks its durable attempt marker")
    _require_sha256(attempt.get("raw_sha256"), name="attempt marker raw_sha256")
    _require_sha256(
        attempt.get("record_sha256"), name="attempt marker record_sha256"
    )
    custody = record.get("checkpoint_custody")
    expected = {
        "source_artifact_root": V2_ARTIFACT_RELATIVE_PATH,
        "outer_success_receipt_raw_sha256": EXPECTED_OUTER_RECEIPT_RAW_SHA256,
        "outer_success_receipt_self_sha256": EXPECTED_OUTER_RECEIPT_SELF_SHA256,
        "inner_success_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "certificate_sha256": EXPECTED_CERTIFICATE_SHA256,
        "execution_runtime_sha256": EXPECTED_EXECUTION_RUNTIME_SHA256,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "configuration_sha256": EXPECTED_CONFIGURATION_SHA256,
        "preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "path_content_sha256": EXPECTED_PATH_CONTENT_SHA256,
        "path_runtime_sha256": EXPECTED_PATH_RUNTIME_SHA256,
        "coordinate": dict(EXPECTED_COORDINATE),
        "optimizer_steps_taken": EXPECTED_UPDATES,
        "checkpoint_was_loaded_through_canonical_success_ledger": True,
        "checkpoint_was_revalidated_after_diagnostics": True,
    }
    if type(custody) is not dict or custody != expected:
        raise DiagnosticRefusal("D1 worker checkpoint custody is incomplete")
    expected_custody_fields = {
        "source_artifact_root",
        "outer_success_receipt_raw_sha256",
        "outer_success_receipt_self_sha256",
        "inner_success_receipt_sha256",
        "campaign_sha256",
        "run_key_sha256",
        "checkpoint_sha256",
        "parameter_sha256",
        "feature_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "execution_runtime_sha256",
        "source_sha256",
        "configuration_sha256",
        "preflight_sha256",
        "fixture_sha256",
        "path_content_sha256",
        "path_runtime_sha256",
        "coordinate",
        "optimizer_steps_taken",
        "checkpoint_was_loaded_through_canonical_success_ledger",
        "checkpoint_was_revalidated_after_diagnostics",
    }
    if set(custody) != expected_custody_fields:
        raise DiagnosticRefusal("D1 worker checkpoint custody schema is not closed")
    coverage = record.get("coverage")
    if type(coverage) is not dict or coverage != {
        "all_33_nonpath_evaluated": True,
        "all_21_path_reference_preflight_passed": True,
        "all_21_aggregate_path_evaluated": True,
        "all_21_family_supplement_evaluated": True,
        "canonical_observation_order_used": True,
        "evidence_binder_completed": True,
    }:
        raise DiagnosticRefusal("D1 worker coverage is incomplete")
    _validate_execution_runtime(record.get("runtime"))
    _validate_nonpath_record(record.get("nonpath"))
    references = _validate_path_reference_preflight(
        record.get("path_reference_preflight")
    )
    observations = _validate_aggregate_path(record.get("aggregate_path"), references)
    if record["aggregate_path"].get("reference_set_sha256") != record[
        "path_reference_preflight"
    ].get("reference_set_sha256"):
        raise DiagnosticRefusal("D1 aggregate/reference-set binding changed")
    _validate_evidence_binding(record.get("evidence_binding"))
    _validate_family_supplement(record.get("family_supplement"))
    _validate_cross_section_consistency(
        record["family_supplement"], references, observations
    )
    disposition = record.get("numerical_disposition")
    if type(disposition) is not dict or disposition != {
        "primary_refined_limit": PRIMARY_REFINED_LIMIT,
        "family_aggregate_crosscheck_limit": FAMILY_AGGREGATE_LIMIT,
        "target_marginal_limit": TARGET_MARGINAL_LIMIT,
        "terminal_limit": TERMINAL_LIMIT,
        "nonpath_terminal_log_limit": NONPATH_TERMINAL_LOG_LIMIT,
        "nonpath_coherence_limit": NONPATH_COHERENCE_LIMIT,
        "all_required_checks_passed": True,
        "adaptive_float64_not_interval_proof": True,
    }:
        raise DiagnosticRefusal("D1 numerical disposition is incomplete")
    nonclaims = record.get("nonclaims")
    required_false = (
        "scientific_result_eligible",
        "production_checkpoint",
        "production_order_admissible",
        "confirmatory_execution_authorized",
        "qualifies_r1",
        "qualifies_r2",
        "closes_c17",
        "c17_theorem_proved",
        "manuscript_claim_promoted",
        "real_domain_evidence",
        "continuous_coordinate_energy_exercised",
        "occurrence_attached_mark_fibers_exercised",
        "rigorous_numerical_enclosure_present",
        "interval_certified",
        "training_performed_by_diagnostic",
        "checkpoint_selected_by_diagnostic",
    )
    if type(nonclaims) is not dict or any(
        nonclaims.get(name) is not False for name in required_false
    ):
        raise DiagnosticRefusal("D1 worker attempted a prohibited promotion")
    if set(nonclaims) != set(required_false):
        raise DiagnosticRefusal("D1 worker nonclaim schema is not closed")
    forbidden_true_names = {
        "scientific_result_eligible",
        "production_checkpoint",
        "production_order_admissible",
        "confirmatory_execution_authorized",
        "qualifies_r1",
        "qualifies_r2",
        "closes_c17",
        "c17_theorem_proved",
        "manuscript_claim_promoted",
        "real_domain_evidence",
        "interval_certified",
        "rigorous_numerical_enclosure_present",
        "training_performed",
        "training_performed_by_diagnostic",
        "checkpoint_selected_by_diagnostic",
    }

    def scan(value: object) -> None:
        if type(value) is dict:
            for key, item in value.items():
                if key in forbidden_true_names and item is not False:
                    raise DiagnosticRefusal("D1 record contains a forbidden overclaim")
                scan(item)
        elif type(value) is list:
            for item in value:
                scan(item)

    scan(record)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_new_file(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def _consume_attempt(
    root: Path,
    *,
    freeze_sha256: str,
    implementation_sha256: str,
    test_sha256: str,
    human_freeze_sha256: str,
) -> Dict[str, object]:
    """Irreversibly consume the one D1 attempt before any worker can start."""

    marker_path = root / ATTEMPT_MARKER_RELATIVE_PATH
    output_path = root / OUTPUT_RELATIVE_PATH
    if os.path.lexists(marker_path):
        raise DiagnosticRefusal("D1 attempt was already consumed; retry is forbidden")
    if os.path.lexists(output_path):
        raise DiagnosticRefusal("D1 output already exists; retry is forbidden")
    nonce = secrets.token_hex(32)
    marker: Dict[str, object] = {
        "schema_version": "heterodiff-a1-trained-diagnostic-attempt-marker-v1",
        "lane_id": LANE_ID,
        "state": "ATTEMPT_CONSUMED_NONRETRYABLE",
        "attempt_number": 1,
        "nonce": nonce,
        "freeze_sha256": freeze_sha256,
        "implementation_sha256": implementation_sha256,
        "test_sha256": test_sha256,
        "human_freeze_sha256": human_freeze_sha256,
        "v2_outer_success_receipt_raw_sha256": (
            EXPECTED_OUTER_RECEIPT_RAW_SHA256
        ),
        "v2_inner_success_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "v2_run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "v2_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "expected_output_root": OUTPUT_RELATIVE_PATH,
        "retry_permitted": False,
        "resume_permitted": False,
        "training_permitted": False,
        "scientific_result_eligible": False,
        "production_order_admissible": False,
        "confirmatory_execution_authorized": False,
        "manuscript_claim_promoted": False,
    }
    marker["record_sha256"] = _self_digest(
        marker, field="record_sha256", domain=_ATTEMPT_MARKER_DOMAIN
    )
    payload = _canonical_json_bytes(marker)
    # O_EXCL is deliberate.  Even an interrupted write leaves a path that
    # permanently closes the lane; a worker is never launched until fsync.
    _write_new_file(marker_path, payload)
    _fsync_directory(marker_path.parent)
    reopened = _read_regular_bytes(marker_path, maximum=1024 * 1024)
    if reopened != payload:
        raise DiagnosticRefusal("D1 attempt marker changed after commit")
    return {
        "path": ATTEMPT_MARKER_RELATIVE_PATH,
        "state": marker["state"],
        "attempt_number": 1,
        "nonce": nonce,
        "raw_sha256": _sha256_bytes(payload),
        "record_sha256": marker["record_sha256"],
    }


def _require_attempt_marker_unchanged(
    root: Path, expected: Mapping[str, object]
) -> None:
    path = root / ATTEMPT_MARKER_RELATIVE_PATH
    payload = _read_regular_bytes(path, maximum=1024 * 1024)
    if _sha256_bytes(payload) != expected.get("raw_sha256"):
        raise DiagnosticRefusal("D1 attempt marker changed during evaluation")
    marker = _parse_json_object(payload)
    expected_fields = {
        "schema_version",
        "lane_id",
        "state",
        "attempt_number",
        "nonce",
        "freeze_sha256",
        "implementation_sha256",
        "test_sha256",
        "human_freeze_sha256",
        "v2_outer_success_receipt_raw_sha256",
        "v2_inner_success_receipt_sha256",
        "v2_run_key_sha256",
        "v2_checkpoint_sha256",
        "expected_output_root",
        "retry_permitted",
        "resume_permitted",
        "training_permitted",
        "scientific_result_eligible",
        "production_order_admissible",
        "confirmatory_execution_authorized",
        "manuscript_claim_promoted",
        "record_sha256",
    }
    if (
        set(marker) != expected_fields
        or marker.get("schema_version")
        != "heterodiff-a1-trained-diagnostic-attempt-marker-v1"
        or marker.get("lane_id") != LANE_ID
        or marker.get("record_sha256") != expected.get("record_sha256")
        or marker.get("nonce") != expected.get("nonce")
        or marker.get("state") != "ATTEMPT_CONSUMED_NONRETRYABLE"
        or marker.get("attempt_number") != 1
        or any(
            marker.get(name) is not False
            for name in (
                "retry_permitted",
                "resume_permitted",
                "training_permitted",
                "scientific_result_eligible",
                "production_order_admissible",
                "confirmatory_execution_authorized",
                "manuscript_claim_promoted",
            )
        )
        or _self_digest(
            marker, field="record_sha256", domain=_ATTEMPT_MARKER_DOMAIN
        )
        != marker.get("record_sha256")
    ):
        raise DiagnosticRefusal("D1 attempt marker custody is invalid")


def _require_publication_binding_bytes(
    root: Path,
    *,
    freeze_sha256: str,
    implementation_sha256: str,
    test_sha256: str,
    human_freeze_sha256: str,
) -> None:
    expected = (
        (FREEZE_RELATIVE_PATH, freeze_sha256),
        (IMPLEMENTATION_RELATIVE_PATH, implementation_sha256),
        (TEST_RELATIVE_PATH, test_sha256),
        (HUMAN_FREEZE_RELATIVE_PATH, human_freeze_sha256),
    )
    for relative, digest in expected:
        if _file_sha256(root / relative) != digest:
            raise DiagnosticRefusal(
                "D1 launch-bound bytes changed immediately before publication"
            )


def _publish_success(
    root: Path,
    record: Mapping[str, object],
    *,
    freeze_sha256: str,
    implementation_sha256: str,
    test_sha256: str,
    human_freeze_sha256: str,
    attempt_marker: Mapping[str, object],
) -> Dict[str, object]:
    output = root / OUTPUT_RELATIVE_PATH
    if os.path.lexists(output):
        raise DiagnosticRefusal("D1 output root already exists; rerun is forbidden")
    _require_publication_binding_bytes(
        root,
        freeze_sha256=freeze_sha256,
        implementation_sha256=implementation_sha256,
        test_sha256=test_sha256,
        human_freeze_sha256=human_freeze_sha256,
    )
    artifacts = output.parent
    try:
        artifacts_status = artifacts.lstat()
    except OSError as error:
        raise DiagnosticRefusal("workspace artifacts directory is absent") from error
    if stat.S_ISLNK(artifacts_status.st_mode) or not stat.S_ISDIR(
        artifacts_status.st_mode
    ):
        raise DiagnosticRefusal("workspace artifacts path is unsafe")
    staging = artifacts / ("." + output.name + ".staging-" + secrets.token_hex(16))
    if os.path.lexists(staging):
        raise DiagnosticRefusal("D1 staging collision")
    os.mkdir(staging, 0o700)
    record_payload = _canonical_json_bytes(record)
    record_raw_sha = _sha256_bytes(record_payload)
    receipt: Dict[str, object] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "status": STATUS,
        "scope": SCOPE,
        "diagnostic_record_path": "diagnostic-record.json",
        "diagnostic_record_raw_sha256": record_raw_sha,
        "diagnostic_record_sha256": record["diagnostic_record_sha256"],
        "freeze_sha256": freeze_sha256,
        "implementation_sha256": implementation_sha256,
        "test_sha256": test_sha256,
        "human_freeze_sha256": human_freeze_sha256,
        "attempt_marker_path": ATTEMPT_MARKER_RELATIVE_PATH,
        "attempt_marker_raw_sha256": attempt_marker["raw_sha256"],
        "attempt_marker_record_sha256": attempt_marker["record_sha256"],
        "source_v2_artifact_root": V2_ARTIFACT_RELATIVE_PATH,
        "source_v2_outer_receipt_raw_sha256": EXPECTED_OUTER_RECEIPT_RAW_SHA256,
        "training_performed": False,
        "production_order_admissible": False,
        "confirmatory_execution_authorized": False,
        "qualifies_r1": False,
        "qualifies_r2": False,
        "closes_c17": False,
        "manuscript_claim_promoted": False,
    }
    receipt["receipt_sha256"] = _self_digest(
        receipt, field="receipt_sha256", domain=b""
    )
    try:
        _write_new_file(staging / "diagnostic-record.json", record_payload)
        _write_new_file(
            staging / "success-receipt.json", _canonical_json_bytes(receipt)
        )
        _fsync_directory(staging)
        _require_publication_binding_bytes(
            root,
            freeze_sha256=freeze_sha256,
            implementation_sha256=implementation_sha256,
            test_sha256=test_sha256,
            human_freeze_sha256=human_freeze_sha256,
        )
        _require_launch_bindings_unchanged(
            root,
            {
                "freeze_sha256": freeze_sha256,
                "implementation_sha256": implementation_sha256,
                "test_sha256": test_sha256,
                "human_freeze_sha256": human_freeze_sha256,
            },
        )
        if os.path.lexists(output):
            raise DiagnosticRefusal("D1 output appeared before publication")
        os.replace(staging, output)
        _fsync_directory(artifacts)
    except BaseException:
        if os.path.lexists(staging):
            for name in ("diagnostic-record.json", "success-receipt.json"):
                candidate = staging / name
                if os.path.lexists(candidate):
                    candidate.unlink()
            staging.rmdir()
        raise
    return receipt


def _require_launch_bindings_unchanged(
    root: Path, readiness: Mapping[str, object]
) -> Dict[str, object]:
    freeze = _validate_machine_freeze(root)
    expected = {
        "freeze_sha256": freeze["raw_sha256"],
        "implementation_sha256": freeze["implementation_sha256"],
        "test_sha256": freeze["test_sha256"],
        "human_freeze_sha256": freeze["human_freeze_sha256"],
    }
    if any(readiness.get(name) != value for name, value in expected.items()):
        raise DiagnosticRefusal("D1 launch bindings changed during evaluation")
    return expected


def _validate_published_success(
    root: Path,
    *,
    expected_record: Mapping[str, object],
    expected_receipt: Mapping[str, object],
    attempt_marker: Mapping[str, object],
    readiness: Mapping[str, object],
) -> Dict[str, object]:
    output = root / OUTPUT_RELATIVE_PATH
    rows = _inventory(output)
    if [row["path"] for row in rows] != [
        "diagnostic-record.json",
        "success-receipt.json",
    ]:
        raise DiagnosticRefusal("published D1 root has an unexpected inventory")
    record_payload = _read_regular_bytes(
        output / "diagnostic-record.json", maximum=MAXIMUM_WORKER_OUTPUT_BYTES
    )
    record = _parse_json_object(record_payload)
    if (
        record_payload != _canonical_json_bytes(record)
        or record != expected_record
    ):
        raise DiagnosticRefusal("published D1 record differs from worker output")
    _validate_worker_record(record)
    receipt_payload = _read_regular_bytes(
        output / "success-receipt.json", maximum=4 * 1024 * 1024
    )
    receipt = _parse_json_object(receipt_payload)
    expected_receipt_fields = {
        "schema_version",
        "lane_id",
        "status",
        "scope",
        "diagnostic_record_path",
        "diagnostic_record_raw_sha256",
        "diagnostic_record_sha256",
        "freeze_sha256",
        "implementation_sha256",
        "test_sha256",
        "human_freeze_sha256",
        "attempt_marker_path",
        "attempt_marker_raw_sha256",
        "attempt_marker_record_sha256",
        "source_v2_artifact_root",
        "source_v2_outer_receipt_raw_sha256",
        "training_performed",
        "production_order_admissible",
        "confirmatory_execution_authorized",
        "qualifies_r1",
        "qualifies_r2",
        "closes_c17",
        "manuscript_claim_promoted",
        "receipt_sha256",
    }
    if (
        receipt_payload != _canonical_json_bytes(receipt)
        or set(receipt) != expected_receipt_fields
        or receipt != expected_receipt
        or receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION
        or receipt.get("status") != STATUS
        or receipt.get("scope") != SCOPE
        or receipt.get("diagnostic_record_raw_sha256")
        != _sha256_bytes(record_payload)
        or receipt.get("diagnostic_record_sha256")
        != record.get("diagnostic_record_sha256")
        or _self_digest(receipt, field="receipt_sha256", domain=b"")
        != receipt.get("receipt_sha256")
    ):
        raise DiagnosticRefusal("published D1 success receipt is invalid")
    for name in (
        "training_performed",
        "production_order_admissible",
        "confirmatory_execution_authorized",
        "qualifies_r1",
        "qualifies_r2",
        "closes_c17",
        "manuscript_claim_promoted",
    ):
        if receipt.get(name) is not False:
            raise DiagnosticRefusal("published D1 receipt contains an overclaim")
    _require_attempt_marker_unchanged(root, attempt_marker)
    _require_launch_bindings_unchanged(root, readiness)
    _validate_outer_v2_custody(root)
    _validate_protected_roots_absent(root)
    return receipt


def _array_sha256(value: object) -> str:
    import numpy as np

    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(_ARRAY_DOMAIN)
    dtype = array.dtype.str.encode("ascii")
    shape = ",".join(str(int(size)) for size in array.shape).encode("ascii")
    payload = array.tobytes(order="C")
    for part in (dtype, shape, payload):
        digest.update(len(part).to_bytes(8, "little", signed=False))
        digest.update(part)
    return digest.hexdigest()


def _json_safe(value: object, *, exclude_elapsed: bool = True) -> object:
    """Convert a frozen scientific record to finite JSON without tensor bytes."""

    import numpy as np

    if is_dataclass(value):
        result = {}
        for field in fields(value):
            if field.name.startswith("_"):
                continue
            if exclude_elapsed and "elapsed_" in field.name:
                continue
            result[field.name] = _json_safe(
                getattr(value, field.name), exclude_elapsed=exclude_elapsed
            )
        return result
    if isinstance(value, np.ndarray):
        return {
            "dtype": value.dtype.str,
            "shape": [int(size) for size in value.shape],
            "sha256": _array_sha256(value),
        }
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_json_safe(item, exclude_elapsed=exclude_elapsed) for item in value]
    if isinstance(value, list):
        return [_json_safe(item, exclude_elapsed=exclude_elapsed) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item, exclude_elapsed=exclude_elapsed)
            for key, item in value.items()
        }
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DiagnosticRefusal("scientific record contains a non-finite value")
        return value
    raise DiagnosticRefusal("scientific record contains an unsupported value")


def _worker_require_environment(root: Path, request: Mapping[str, object]) -> None:
    if platform.python_version() != "3.11.5":
        raise DiagnosticRefusal("D1 worker Python version is not frozen")
    if platform.machine() != "arm64":
        raise DiagnosticRefusal("D1 worker machine is not native arm64")
    if any(os.environ.get(name) != "1" for name in _THREAD_VARIABLES):
        raise DiagnosticRefusal("D1 worker numerical thread environment changed")
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise DiagnosticRefusal("D1 worker hash seed changed")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise DiagnosticRefusal("D1 worker is not CPU-only")
    if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise DiagnosticRefusal("D1 worker bytecode suppression is absent")
    capsule = root / V2_CAPSULE_RELATIVE_PATH
    if Path.cwd().resolve(strict=True) != capsule:
        raise DiagnosticRefusal("D1 worker current directory is not the V2 capsule")
    expected_pythonpath = str(capsule / "src")
    if os.environ.get("PYTHONPATH") != expected_pythonpath:
        raise DiagnosticRefusal("D1 worker PYTHONPATH is not capsule-exclusive")
    if request.get("workspace_root") != str(root):
        raise DiagnosticRefusal("D1 worker request targets another workspace")
    implementation = root / IMPLEMENTATION_RELATIVE_PATH
    if request.get("implementation_sha256") != _file_sha256(implementation):
        raise DiagnosticRefusal("D1 worker implementation changed")
    freeze = root / FREEZE_RELATIVE_PATH
    if request.get("freeze_sha256") != _file_sha256(freeze):
        raise DiagnosticRefusal("D1 worker freeze changed")
    if request.get("human_freeze_sha256") != _file_sha256(
        root / HUMAN_FREEZE_RELATIVE_PATH
    ):
        raise DiagnosticRefusal("D1 worker human freeze changed")
    nonce = request.get("nonce")
    if type(nonce) is not str or len(nonce) != 64:
        raise DiagnosticRefusal("D1 worker attempt nonce is invalid")
    _require_sha256(
        request.get("attempt_marker_raw_sha256"),
        name="attempt_marker_raw_sha256",
    )
    _require_sha256(
        request.get("attempt_marker_record_sha256"),
        name="attempt_marker_record_sha256",
    )
    _require_attempt_marker_unchanged(
        root,
        {
            "nonce": nonce,
            "raw_sha256": request["attempt_marker_raw_sha256"],
            "record_sha256": request["attempt_marker_record_sha256"],
        },
    )


def _require_capsule_module_provenance(capsule_source: Path) -> None:
    checked = 0
    for name, module in tuple(sys.modules.items()):
        if name != "heterodiff" and not name.startswith("heterodiff."):
            continue
        raw = getattr(module, "__file__", None)
        if raw is None:
            raise DiagnosticRefusal("loaded heterodiff module lacks a source path")
        path = Path(raw).resolve(strict=True)
        try:
            path.relative_to(capsule_source)
        except ValueError as error:
            raise DiagnosticRefusal(
                "heterodiff import escaped the immutable V2 capsule: %s" % name
            ) from error
        checked += 1
    if checked == 0:
        raise DiagnosticRefusal("no capsule modules were provenance-checked")


class _ExactPotential:
    def __init__(self, fixture: object, observation_index: int) -> None:
        self._fixture = fixture
        self._observation = fixture.observation.observation_at(observation_index)

    def __call__(self, direct_time: object):
        import numpy as np

        if isinstance(direct_time, (bool, np.bool_)):
            raise TypeError("direct_time must be real")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > 1.0:
            raise ValueError("direct_time must lie in [0,1]")
        remaining = max(0.0, 1.0 - time)
        value = self._fixture.oracle.backward_information(
            remaining, self._observation
        )
        result = np.asarray(value, dtype=np.float64)
        if result.shape != (20,) or np.any(result <= 0.0) or not np.all(
            np.isfinite(result)
        ):
            raise DiagnosticRefusal("exact finite potential is invalid")
        return result


class _ExactTargetMarginal:
    def __init__(self, fixture: object, potential: _ExactPotential) -> None:
        self._fixture = fixture
        self._potential = potential

    def __call__(self, direct_time: object):
        import numpy as np

        time = float(direct_time)
        unconditioned = (
            self._fixture.initial_marginal
            @ self._fixture.oracle.forward_transition(time)
        )
        unnormalized = unconditioned * self._potential(time)
        normalizer = math.fsum(float(value) for value in unnormalized)
        if not math.isfinite(normalizer) or normalizer <= 0.0:
            raise DiagnosticRefusal("exact target marginal normalizer is invalid")
        result = np.asarray(unnormalized / normalizer, dtype=np.float64)
        if result.shape != (20,) or np.any(result < 0.0) or not np.all(
            np.isfinite(result)
        ):
            raise DiagnosticRefusal("exact target marginal is invalid")
        return result


def _family_partition(fixture: object):
    import numpy as np

    generator = np.asarray(fixture.oracle.generator, dtype=np.float64)
    states = fixture.latent_space.states
    matrix = np.full(generator.shape, -1, dtype=np.int64)
    indices = {family: index for index, family in enumerate(FAMILY_ORDER)}
    for source in range(generator.shape[0]):
        for destination in range(generator.shape[1]):
            if source == destination or generator[source, destination] <= 0.0:
                continue
            family = fixture.oracle.transition_family(
                states[source], states[destination]
            )
            if family not in indices:
                raise DiagnosticRefusal("positive edge has no frozen family")
            matrix[source, destination] = indices[family]
    counts = tuple(int(np.count_nonzero(matrix == index)) for index in range(3))
    digest = hashlib.sha256()
    digest.update(b"heterodiff-finite-a1-aggregate-edge-family-partition-v1\0")
    digest.update(np.ascontiguousarray(matrix).tobytes(order="C"))
    if counts != EXPECTED_FAMILY_EDGE_COUNTS:
        raise DiagnosticRefusal("frozen family edge counts changed")
    if digest.hexdigest() != EXPECTED_FAMILY_PARTITION_SHA256:
        raise DiagnosticRefusal("frozen family partition changed")
    return matrix, counts, digest.hexdigest()


def _family_supplement(evaluator: object, fixture: object, aggregate: object) -> Dict[str, object]:
    import numpy as np

    from heterodiff.evaluation.finite_association_path_evaluator import (
        PRIMARY_PATH_SOLVER_SETTINGS,
        REFINED_PATH_SOLVER_SETTINGS,
    )
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        CertifiedFiniteAssociationPotentialAdapter,
    )
    from heterodiff.theory.finite_bridge_family_path_control import (
        tilted_path_kl_by_edge_family,
    )
    from heterodiff.theory.finite_bridge_path_control import tilted_path_kl

    families, counts, family_digest = _family_partition(fixture)
    settings_pair = (PRIMARY_PATH_SOLVER_SETTINGS, REFINED_PATH_SOLVER_SETTINGS)
    records = []
    evaluator.assert_integrity()
    try:
        for index in range(21):
            exact = _ExactPotential(fixture, index)
            target = _ExactTargetMarginal(fixture, exact)

            def family_call(settings: object):
                return tilted_path_kl_by_edge_family(
                    fixture.initial_marginal,
                    fixture.oracle.generator,
                    exact,
                    CertifiedFiniteAssociationPotentialAdapter(
                        evaluator, fixture, index
                    ),
                    1.0,
                    families,
                    evaluation_times=fixture.times,
                    rtol=settings.rtol,
                    atol=settings.atol,
                    max_step=settings.max_step,
                    quadrature_epsabs=settings.quadrature_epsabs,
                    quadrature_epsrel=settings.quadrature_epsrel,
                    quadrature_limit=settings.quadrature_limit,
                    max_potential_evaluations=settings.max_potential_evaluations,
                    reference_marginal=target,
                )

            def aggregate_call(settings: object):
                return tilted_path_kl(
                    fixture.initial_marginal,
                    fixture.oracle.generator,
                    exact,
                    CertifiedFiniteAssociationPotentialAdapter(
                        evaluator, fixture, index
                    ),
                    1.0,
                    evaluation_times=fixture.times,
                    rtol=settings.rtol,
                    atol=settings.atol,
                    max_step=settings.max_step,
                    quadrature_epsabs=settings.quadrature_epsabs,
                    quadrature_epsrel=settings.quadrature_epsrel,
                    quadrature_limit=settings.quadrature_limit,
                    max_potential_evaluations=settings.max_potential_evaluations,
                )

            primary_family, refined_family = tuple(
                family_call(settings) for settings in settings_pair
            )
            primary_aggregate, refined_aggregate = tuple(
                aggregate_call(settings) for settings in settings_pair
            )
            public_aggregate = aggregate.observations[index]
            target_grid = np.stack(
                [target(float(time)) for time in fixture.times], axis=0
            )
            target_error = float(
                np.max(
                    np.abs(
                        target_grid
                        - fixture.population.conditional_time[:, :, index]
                    )
                )
            )
            primary_family_target_error = float(
                np.max(np.abs(primary_family.occupancy.marginals - target_grid))
            )
            refined_family_target_error = float(
                np.max(np.abs(refined_family.occupancy.marginals - target_grid))
            )
            candidate_terminal = CertifiedFiniteAssociationPotentialAdapter(
                evaluator, fixture, index
            ).log_potential_vector(1.0)
            terminal_error = float(
                np.max(
                    np.abs(
                        candidate_terminal
                        - fixture.observation.log_density_kernel[:, index]
                    )
                )
            )
            refinements = {
                "initial": abs(primary_family.initial - refined_family.initial),
                "birth": abs(
                    primary_family.birth_dynamic - refined_family.birth_dynamic
                ),
                "death": abs(
                    primary_family.death_dynamic - refined_family.death_dynamic
                ),
                "replacement": abs(
                    primary_family.replacement_dynamic
                    - refined_family.replacement_dynamic
                ),
                "total": abs(primary_family.total - refined_family.total),
            }
            crosschecks = {
                FAMILY_CROSSCHECK_NAMES[0]: abs(
                    primary_family.initial - primary_aggregate.initial
                ),
                FAMILY_CROSSCHECK_NAMES[1]: abs(
                    primary_family.dynamic - primary_aggregate.dynamic
                ),
                FAMILY_CROSSCHECK_NAMES[2]: abs(
                    primary_family.total - primary_aggregate.total
                ),
                FAMILY_CROSSCHECK_NAMES[3]: abs(
                    refined_family.initial - refined_aggregate.initial
                ),
                FAMILY_CROSSCHECK_NAMES[4]: abs(
                    refined_family.dynamic - refined_aggregate.dynamic
                ),
                FAMILY_CROSSCHECK_NAMES[5]: abs(
                    refined_family.total - refined_aggregate.total
                ),
                FAMILY_CROSSCHECK_NAMES[6]: abs(
                    primary_aggregate.initial - public_aggregate.path_kl_initial
                ),
                FAMILY_CROSSCHECK_NAMES[7]: abs(
                    primary_aggregate.dynamic - public_aggregate.path_kl_dynamic
                ),
                FAMILY_CROSSCHECK_NAMES[8]: abs(
                    primary_aggregate.total - public_aggregate.path_kl_total
                ),
            }
            failures = []
            if any(
                result.orientation != "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
                or result.supplied_reference_marginal_used is not True
                for result in (primary_family, refined_family)
            ):
                failures.append("family target-first/reference-marginal contract failed")
            failures.extend(
                "%s primary/refined change exceeds 1e-8" % name
                for name, value in refinements.items()
                if value > PRIMARY_REFINED_LIMIT
            )
            failures.extend(
                "%s crosscheck exceeds 1e-8" % name
                for name, value in crosschecks.items()
                if value > FAMILY_AGGREGATE_LIMIT
            )
            if target_error > TARGET_MARGINAL_LIMIT:
                failures.append("analytic target/fixture marginal error exceeds 1e-8")
            if primary_family_target_error > TARGET_MARGINAL_LIMIT:
                failures.append("primary family occupancy/target error exceeds 1e-8")
            if refined_family_target_error > TARGET_MARGINAL_LIMIT:
                failures.append("refined family occupancy/target error exceeds 1e-8")
            if terminal_error > TERMINAL_LIMIT:
                failures.append("terminal boundary error exceeds 1e-10")
            if failures:
                raise DiagnosticRefusal(
                    "family supplement observation %d refused: %s"
                    % (index, "; ".join(failures))
                )
            components = [
                {
                    "component_id": COMPONENT_ORDER[0],
                    "applicability": "APPLICABLE",
                    "target_measure": "EXACT_CONDITIONED_TARGET_INITIAL_LAW",
                    "primary": primary_family.initial,
                    "refined": refined_family.initial,
                    "primary_refined_absolute_difference": refinements["initial"],
                    "active_aggregate_edge_count": 0,
                    "entered_total": True,
                    "interval_certified": False,
                },
                {
                    "component_id": COMPONENT_ORDER[1],
                    "applicability": CONTINUOUS_DISPOSITION,
                    "target_measure": CONTINUOUS_DISPOSITION,
                    "primary": None,
                    "refined": None,
                    "primary_refined_absolute_difference": None,
                    "active_aggregate_edge_count": 0,
                    "entered_total": False,
                    "interval_certified": False,
                },
            ]
            for component, family, edge_count in zip(
                COMPONENT_ORDER[2:], FAMILY_ORDER, counts
            ):
                field = family + "_dynamic"
                components.append(
                    {
                        "component_id": component,
                        "applicability": "APPLICABLE",
                        "target_measure": "EXACT_CONDITIONED_TARGET_OCCUPATION",
                        "primary": getattr(primary_family, field),
                        "refined": getattr(refined_family, field),
                        "primary_refined_absolute_difference": refinements[family],
                        "active_aggregate_edge_count": edge_count,
                        "entered_total": True,
                        "interval_certified": False,
                    }
                )
            records.append(
                {
                    "observation_index": index,
                    "observation_mass": float(
                        fixture.population.observation_marginal_mass[index]
                    ),
                    "components": components,
                    "primary_family_orientation": primary_family.orientation,
                    "refined_family_orientation": refined_family.orientation,
                    "primary_family_supplied_reference_marginal_used": (
                        primary_family.supplied_reference_marginal_used
                    ),
                    "refined_family_supplied_reference_marginal_used": (
                        refined_family.supplied_reference_marginal_used
                    ),
                    "primary_dynamic": primary_family.dynamic,
                    "primary_total": primary_family.total,
                    "refined_dynamic": refined_family.dynamic,
                    "refined_total": refined_family.total,
                    "separate_primary_aggregate_initial": primary_aggregate.initial,
                    "separate_primary_aggregate_dynamic": primary_aggregate.dynamic,
                    "separate_primary_aggregate_total": primary_aggregate.total,
                    "separate_refined_aggregate_initial": refined_aggregate.initial,
                    "separate_refined_aggregate_dynamic": refined_aggregate.dynamic,
                    "separate_refined_aggregate_total": refined_aggregate.total,
                    "public_primary_aggregate_initial": (
                        public_aggregate.path_kl_initial
                    ),
                    "public_primary_aggregate_dynamic": (
                        public_aggregate.path_kl_dynamic
                    ),
                    "public_primary_aggregate_total": public_aggregate.path_kl_total,
                    "refinements": refinements,
                    "crosschecks": crosschecks,
                    "target_marginal_maximum_absolute_error": target_error,
                    "primary_family_occupancy_target_maximum_absolute_error": (
                        primary_family_target_error
                    ),
                    "refined_family_occupancy_target_maximum_absolute_error": (
                        refined_family_target_error
                    ),
                    "terminal_log_potential_maximum_absolute_error": terminal_error,
                    "primary_family_quadrature_error_estimate": (
                        primary_family.quadrature_error_estimate
                    ),
                    "refined_family_quadrature_error_estimate": (
                        refined_family.quadrature_error_estimate
                    ),
                    "numerical_failures": [],
                }
            )
    finally:
        evaluator.assert_integrity()
    mass = np.asarray(
        fixture.population.observation_marginal_mass, dtype=np.float64
    )

    def weighted(component_index: int, field: str = "primary") -> float:
        return float(
            mass
            @ np.asarray(
                [row["components"][component_index][field] for row in records],
                dtype=np.float64,
            )
        )

    weighted_initial = weighted(0)
    weighted_birth = weighted(2)
    weighted_death = weighted(3)
    weighted_replacement = weighted(4)
    weighted_total = float(
        mass @ np.asarray([row["primary_total"] for row in records])
    )
    if not math.isclose(
        weighted_total,
        math.fsum(
            (
                weighted_initial,
                weighted_birth,
                weighted_death,
                weighted_replacement,
            )
        ),
        rel_tol=2.0e-12,
        abs_tol=2.0e-14,
    ):
        raise DiagnosticRefusal("family weighted total is inconsistent")
    return {
        "schema_version": "heterodiff-a1-trained-family-supplement-v1",
        "orientation": "KL(P_EXACT_TARGET_H || P_TRAINED_CHECKPOINT_H_HAT)",
        "family_names": list(FAMILY_ORDER),
        "component_order": list(COMPONENT_ORDER),
        "continuous_component_disposition": CONTINUOUS_DISPOSITION,
        "active_edge_counts": list(counts),
        "edge_family_partition_sha256": family_digest,
        "observation_count": len(records),
        "observations": records,
        "observation_weighted_initial": weighted_initial,
        "observation_weighted_birth": weighted_birth,
        "observation_weighted_death": weighted_death,
        "observation_weighted_replacement": weighted_replacement,
        "observation_weighted_total": weighted_total,
        "maximum_primary_refined_component_change": max(
            value
            for row in records
            for value in row["refinements"].values()
        ),
        "maximum_family_aggregate_crosscheck_absolute_difference": max(
            value
            for row in records
            for value in row["crosschecks"].values()
        ),
        "maximum_target_marginal_absolute_error": max(
            value
            for row in records
            for value in (
                row["target_marginal_maximum_absolute_error"],
                row[
                    "primary_family_occupancy_target_maximum_absolute_error"
                ],
                row[
                    "refined_family_occupancy_target_maximum_absolute_error"
                ],
            )
        ),
        "maximum_terminal_log_potential_absolute_error": max(
            row["terminal_log_potential_maximum_absolute_error"] for row in records
        ),
        "interval_certified": False,
        "rigorous_numerical_enclosure_present": False,
        "numerical_failures": [],
    }


def _worker_record(root: Path, request: Mapping[str, object]) -> Dict[str, object]:
    from heterodiff.experiments.finite_association_residual_training_torch import (
        bind_fitted_association_checkpoint_evaluator,
        configure_frozen_association_training_environment,
    )

    configure_frozen_association_training_environment()
    import numpy as np

    from heterodiff.evaluation.finite_association_decision import (
        bind_frozen_association_sampled_run_evidence,
    )
    from heterodiff.evaluation.finite_association_path_evaluator import (
        FiniteAssociationPathRuntime,
        build_frozen_association_path_references,
        evaluate_finite_association_paths,
        finite_association_path_fixture_content_sha256,
    )
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        evaluate_finite_association_nonpath,
    )
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        build_frozen_association_residual_fixture,
        frozen_association_fixture_content_digests,
        frozen_association_fixture_sha256,
        frozen_association_residual_splits,
    )
    from heterodiff.experiments.finite_association_isolated_runner import (
        load_successful_frozen_association_checkpoint,
        revalidate_successful_frozen_association_checkpoint,
    )

    capsule_source = root / V2_CAPSULE_RELATIVE_PATH / "src"
    _require_capsule_module_provenance(capsule_source)
    verified = load_successful_frozen_association_checkpoint(
        EXPECTED_RUN_KEY_SHA256
    )
    revalidate_successful_frozen_association_checkpoint(verified)
    checkpoint = verified.checkpoint
    identity = {
        "inner_success_receipt_sha256": verified.success_receipt_sha256,
        "campaign_sha256": verified.campaign_sha256,
        "run_key_sha256": checkpoint.run_key_sha256,
        "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
        "feature_sha256": checkpoint.certificate.feature_sha256,
        "classifier_sha256": checkpoint.classifier_sha256,
        "certificate_sha256": checkpoint.certificate.certificate_sha256,
        "execution_runtime_sha256": checkpoint.execution_runtime_sha256,
        "source_sha256": checkpoint.preflight.source_sha256,
        "configuration_sha256": checkpoint.preflight.configuration_sha256,
        "preflight_sha256": checkpoint.preflight.preflight_sha256,
        "fixture_sha256": checkpoint.preflight.fixture_sha256,
        "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
    }
    expected_identity = {
        "inner_success_receipt_sha256": EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": EXPECTED_CAMPAIGN_SHA256,
        "run_key_sha256": EXPECTED_RUN_KEY_SHA256,
        "parameter_sha256": EXPECTED_PARAMETER_SHA256,
        "feature_sha256": EXPECTED_FEATURE_SHA256,
        "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        "certificate_sha256": EXPECTED_CERTIFICATE_SHA256,
        "execution_runtime_sha256": EXPECTED_EXECUTION_RUNTIME_SHA256,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "configuration_sha256": EXPECTED_CONFIGURATION_SHA256,
        "preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "optimizer_steps_taken": EXPECTED_UPDATES,
    }
    if identity != expected_identity:
        raise DiagnosticRefusal("canonical loader returned unexpected V2 identity")
    if {
        "seed": checkpoint.preflight.seed,
        "budget": checkpoint.preflight.budget,
        "method": checkpoint.preflight.method,
    } != EXPECTED_COORDINATE:
        raise DiagnosticRefusal("canonical loader returned unexpected coordinate")

    fixture = build_frozen_association_residual_fixture()
    splits = frozen_association_residual_splits(fixture)
    fixture_sha = frozen_association_fixture_sha256(
        frozen_association_fixture_content_digests(fixture, splits)
    )
    path_content = finite_association_path_fixture_content_sha256(fixture)
    runtime = FiniteAssociationPathRuntime.current()
    if (
        fixture_sha != EXPECTED_FIXTURE_SHA256
        or path_content != EXPECTED_PATH_CONTENT_SHA256
        or runtime.sha256 != EXPECTED_PATH_RUNTIME_SHA256
        or not runtime.is_frozen_execution_runtime
    ):
        raise DiagnosticRefusal("fresh D1 fixture/path runtime changed")

    evaluator = bind_fitted_association_checkpoint_evaluator(verified)
    nonpath = evaluate_finite_association_nonpath(evaluator, fixture, splits)
    _require_worker_nonpath_gates(nonpath)
    evaluator.assert_integrity()
    revalidate_successful_frozen_association_checkpoint(verified)
    references = build_frozen_association_path_references(fixture)
    references.require_preflight_pass()
    evaluator.assert_integrity()
    revalidate_successful_frozen_association_checkpoint(verified)
    aggregate = evaluate_finite_association_paths(
        evaluator, fixture, reference_set=references, test_only=False
    )
    if not aggregate.numerical_gate_passed:
        raise DiagnosticRefusal("all-21 aggregate path numerical gate failed")
    evaluator.assert_integrity()
    revalidate_successful_frozen_association_checkpoint(verified)
    evidence = bind_frozen_association_sampled_run_evidence(
        verified, nonpath, aggregate
    )
    evaluator.assert_integrity()
    revalidate_successful_frozen_association_checkpoint(verified)
    family = _family_supplement(evaluator, fixture, aggregate)
    evaluator.assert_integrity()
    revalidate_successful_frozen_association_checkpoint(verified)
    _require_capsule_module_provenance(capsule_source)

    request_bytes = _canonical_json_bytes(request)
    request_sha = _sha256_bytes(_WORKER_REQUEST_DOMAIN + request_bytes)
    record: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "status": STATUS,
        "scope": SCOPE,
        "worker_request_sha256": request_sha,
        "implementation_sha256": request["implementation_sha256"],
        "freeze_sha256": request["freeze_sha256"],
        "human_freeze_sha256": request["human_freeze_sha256"],
        "attempt_marker": {
            "path": ATTEMPT_MARKER_RELATIVE_PATH,
            "state": "ATTEMPT_CONSUMED_NONRETRYABLE",
            "attempt_number": 1,
            "raw_sha256": request["attempt_marker_raw_sha256"],
            "record_sha256": request["attempt_marker_record_sha256"],
        },
        "checkpoint_custody": {
            "source_artifact_root": V2_ARTIFACT_RELATIVE_PATH,
            "outer_success_receipt_raw_sha256": EXPECTED_OUTER_RECEIPT_RAW_SHA256,
            "outer_success_receipt_self_sha256": EXPECTED_OUTER_RECEIPT_SELF_SHA256,
            "inner_success_receipt_sha256": verified.success_receipt_sha256,
            "campaign_sha256": verified.campaign_sha256,
            "run_key_sha256": checkpoint.run_key_sha256,
            "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
            "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
            "feature_sha256": checkpoint.certificate.feature_sha256,
            "classifier_sha256": checkpoint.classifier_sha256,
            "certificate_sha256": checkpoint.certificate.certificate_sha256,
            "execution_runtime_sha256": checkpoint.execution_runtime_sha256,
            "source_sha256": checkpoint.preflight.source_sha256,
            "configuration_sha256": checkpoint.preflight.configuration_sha256,
            "preflight_sha256": checkpoint.preflight.preflight_sha256,
            "fixture_sha256": fixture_sha,
            "path_content_sha256": path_content,
            "path_runtime_sha256": runtime.sha256,
            "coordinate": dict(EXPECTED_COORDINATE),
            "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
            "checkpoint_was_loaded_through_canonical_success_ledger": True,
            "checkpoint_was_revalidated_after_diagnostics": True,
        },
        "coverage": {
            "all_33_nonpath_evaluated": True,
            "all_21_path_reference_preflight_passed": True,
            "all_21_aggregate_path_evaluated": True,
            "all_21_family_supplement_evaluated": True,
            "canonical_observation_order_used": True,
            "evidence_binder_completed": True,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "path_runtime": _json_safe(runtime),
            "path_runtime_sha256": runtime.sha256,
            "thread_environment": {
                name: os.environ.get(name) for name in _THREAD_VARIABLES
            },
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "capsule_source_only": True,
        },
        "nonpath": _json_safe(nonpath),
        "path_reference_preflight": _json_safe(references),
        "aggregate_path": _json_safe(aggregate),
        "evidence_binding": {
            "coordinate": [evidence.seed, evidence.budget, evidence.method],
            "run_key_sha256": evidence.run_key_sha256,
            "success_receipt_sha256": evidence.success_receipt_sha256,
            "campaign_sha256": evidence.campaign_sha256,
            "parameter_sha256": evidence.parameter_sha256,
            "feature_sha256": evidence.feature_sha256,
            "classifier_sha256": evidence.classifier_sha256,
            "certificate_sha256": evidence.certificate_sha256,
            "optimizer_steps_taken": evidence.optimizer_steps_taken,
            "nonpath_identity_matches": True,
            "aggregate_path_identity_matches": True,
            "internal_analysis_only": True,
        },
        "family_supplement": family,
        "numerical_disposition": {
            "primary_refined_limit": PRIMARY_REFINED_LIMIT,
            "family_aggregate_crosscheck_limit": FAMILY_AGGREGATE_LIMIT,
            "target_marginal_limit": TARGET_MARGINAL_LIMIT,
            "terminal_limit": TERMINAL_LIMIT,
            "nonpath_terminal_log_limit": NONPATH_TERMINAL_LOG_LIMIT,
            "nonpath_coherence_limit": NONPATH_COHERENCE_LIMIT,
            "all_required_checks_passed": True,
            "adaptive_float64_not_interval_proof": True,
        },
        "nonclaims": {
            "scientific_result_eligible": False,
            "production_checkpoint": False,
            "production_order_admissible": False,
            "confirmatory_execution_authorized": False,
            "qualifies_r1": False,
            "qualifies_r2": False,
            "closes_c17": False,
            "c17_theorem_proved": False,
            "manuscript_claim_promoted": False,
            "real_domain_evidence": False,
            "continuous_coordinate_energy_exercised": False,
            "occurrence_attached_mark_fibers_exercised": False,
            "rigorous_numerical_enclosure_present": False,
            "interval_certified": False,
            "training_performed_by_diagnostic": False,
            "checkpoint_selected_by_diagnostic": False,
        },
    }
    record["diagnostic_record_sha256"] = _self_digest(
        record, field="diagnostic_record_sha256", domain=_RECORD_DOMAIN
    )
    return record


def _worker_main() -> int:
    payload = sys.stdin.buffer.read(1024 * 1024 + 1)
    if len(payload) > 1024 * 1024:
        raise DiagnosticRefusal("D1 worker request exceeds its byte limit")
    request = _parse_json_object(payload)
    if set(request) != {
        "schema",
        "lane_id",
        "workspace_root",
        "implementation_sha256",
        "freeze_sha256",
        "human_freeze_sha256",
        "nonce",
        "attempt_marker_raw_sha256",
        "attempt_marker_record_sha256",
    }:
        raise DiagnosticRefusal("D1 worker request schema is not closed")
    if request.get("schema") != "heterodiff-a1-trained-diagnostic-worker-request-v1":
        raise DiagnosticRefusal("D1 worker request schema changed")
    if request.get("lane_id") != LANE_ID:
        raise DiagnosticRefusal("D1 worker request lane changed")
    request_sha = _sha256_bytes(_WORKER_REQUEST_DOMAIN + _canonical_json_bytes(request))
    if os.environ.get("HETERODIFF_D1_WORKER_REQUEST_SHA256") != request_sha:
        raise DiagnosticRefusal("D1 worker lacks its parent request binding")
    root = Path(str(request.get("workspace_root")))
    if not root.is_absolute() or root.resolve(strict=True) != root:
        raise DiagnosticRefusal("D1 worker workspace root is not canonical")
    _worker_require_environment(root, request)
    record = _worker_record(root, request)
    _validate_worker_record(record)
    sys.stdout.buffer.write(_canonical_json_bytes(record) + b"\n")
    sys.stdout.buffer.flush()
    return 0


def audit_ready(root: Optional[Path] = None) -> Dict[str, object]:
    workspace = _workspace_root() if root is None else root
    if workspace.resolve(strict=True) != workspace:
        raise DiagnosticRefusal("workspace root is not canonical")
    freeze = _validate_machine_freeze(workspace)
    v2 = _validate_outer_v2_custody(workspace)
    _validate_protected_roots_absent(workspace)
    output = workspace / OUTPUT_RELATIVE_PATH
    if os.path.lexists(output):
        raise DiagnosticRefusal("D1 output already exists; execution is closed")
    if os.path.lexists(workspace / ATTEMPT_MARKER_RELATIVE_PATH):
        raise DiagnosticRefusal("D1 attempt is already consumed; retry is forbidden")
    return {
        "schema_version": "heterodiff-a1-trained-diagnostic-readiness-v1",
        "lane_id": LANE_ID,
        "ready": True,
        "training_permitted": False,
        "output_absent": True,
        "attempt_marker_absent": True,
        "freeze_sha256": freeze["raw_sha256"],
        "implementation_sha256": freeze["implementation_sha256"],
        "test_sha256": freeze["test_sha256"],
        "human_freeze_sha256": freeze["human_freeze_sha256"],
        "v2_outer_receipt_raw_sha256": v2["outer_receipt_raw_sha256"],
        "v2_inventory_sha256": v2["inventory_sha256"],
    }


def execute_once(root: Optional[Path] = None) -> Dict[str, object]:
    workspace = _workspace_root() if root is None else root
    readiness = audit_ready(workspace)
    before = _validate_outer_v2_custody(workspace)
    attempt_marker = _consume_attempt(
        workspace,
        freeze_sha256=readiness["freeze_sha256"],
        implementation_sha256=readiness["implementation_sha256"],
        test_sha256=readiness["test_sha256"],
        human_freeze_sha256=readiness["human_freeze_sha256"],
    )
    record = _run_worker_subprocess(
        workspace,
        implementation_sha256=readiness["implementation_sha256"],
        freeze_sha256=readiness["freeze_sha256"],
        human_freeze_sha256=readiness["human_freeze_sha256"],
        attempt_marker=attempt_marker,
    )
    _validate_worker_record(record)
    if (
        record.get("implementation_sha256") != readiness["implementation_sha256"]
        or record.get("freeze_sha256") != readiness["freeze_sha256"]
        or record.get("human_freeze_sha256")
        != readiness["human_freeze_sha256"]
    ):
        raise DiagnosticRefusal("D1 worker result has different launch bindings")
    if record.get("attempt_marker") != {
        key: attempt_marker[key]
        for key in ("path", "state", "attempt_number", "raw_sha256", "record_sha256")
    }:
        raise DiagnosticRefusal("D1 worker result binds another attempt marker")
    _require_attempt_marker_unchanged(workspace, attempt_marker)
    after = _validate_outer_v2_custody(workspace)
    if before["inventory"] != after["inventory"]:
        raise DiagnosticRefusal("immutable V2 capsule changed during D1")
    _validate_protected_roots_absent(workspace)
    _require_launch_bindings_unchanged(workspace, readiness)
    _require_attempt_marker_unchanged(workspace, attempt_marker)
    if os.path.lexists(workspace / OUTPUT_RELATIVE_PATH):
        raise DiagnosticRefusal("D1 output appeared during computation")
    receipt = _publish_success(
        workspace,
        record,
        freeze_sha256=readiness["freeze_sha256"],
        implementation_sha256=readiness["implementation_sha256"],
        test_sha256=readiness["test_sha256"],
        human_freeze_sha256=readiness["human_freeze_sha256"],
        attempt_marker=attempt_marker,
    )
    return _validate_published_success(
        workspace,
        expected_record=record,
        expected_receipt=receipt,
        attempt_marker=attempt_marker,
        readiness=readiness,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true")
    group.add_argument("--execute-trained-diagnostic", action="store_true")
    group.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.worker:
        return _worker_main()
    if arguments.audit:
        result = audit_ready()
    else:
        result = execute_once()
    sys.stdout.buffer.write(_canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DiagnosticRefusal as error:
        sys.stderr.write("REFUSED: %s\n" % error)
        raise SystemExit(2)
