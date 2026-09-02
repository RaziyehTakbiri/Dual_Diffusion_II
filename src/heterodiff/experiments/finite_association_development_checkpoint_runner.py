"""One-attempt development execution for one frozen finite-A1 checkpoint.

This runner intentionally does not extend or impersonate the A1 production
order.  It copies the complete decision-bearing source closure into a durable
development capsule and invokes the existing sampled-runner implementation
unchanged inside that capsule.  Consequently ``artifacts/a1_campaign_v4`` is
created only below the capsule, never at the repository production path.

The resulting checkpoint is useful for learned-evaluator integration.  It is
not R1/R2 evidence, is not admissible to a production aggregate, and cannot
promote a manuscript claim.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-a1-development-checkpoint-runner-v1"
RECEIPT_SCHEMA_VERSION = "heterodiff-a1-development-checkpoint-receipt-v1"
LANE_ID = "A1-DEV-GUIDED-1729-N32768-V1"
SEED = 1729
BUDGET = 32768
METHOD = "guided"
EXPECTED_UPDATES = 3000
MAXIMUM_WALL_SECONDS = 3600
MAXIMUM_PEAK_RSS_BYTES = 8 * 1024**3
MAXIMUM_ARTIFACT_BYTES = 2 * 1024**3
ARTIFACT_RELATIVE_PATH = "artifacts/manuscript_v3_a1_development_checkpoint_v1"
CAPSULE_DIRECTORY_NAME = "capsule"
INNER_CAMPAIGN_RELATIVE_PATH = "artifacts/a1_campaign_v4"
PRODUCTION_ORDER_RELATIVE_PATH = "artifacts/a1_finite_association_production_order_v1"
FORBIDDEN_OUTPUT_RELATIVE_PATHS = (
    INNER_CAMPAIGN_RELATIVE_PATH,
    PRODUCTION_ORDER_RELATIVE_PATH,
)
RETAINED_FREEZE_FILE_NAME = "authorized-freeze.json"
RETAINED_RUNNER_TEST_FILE_NAME = "authorized-runner-test.py"
FREEZE_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v1.json"
)
RUNNER_RELATIVE_PATH = (
    "src/heterodiff/experiments/" "finite_association_development_checkpoint_runner.py"
)
RUNNER_TEST_RELATIVE_PATH = (
    "tests/unit/test_finite_association_development_checkpoint_runner.py"
)
SPECIFICATION_RELATIVE_PATH = (
    "research/62_a1_association_guided_residual_falsification_spec.md"
)
LOCK_RELATIVE_PATH = "requirements/m1-reference-macos-arm64-py311.lock"
FREEZE_DOCUMENT_RELATIVE_PATH = "manuscript_v3/a1_development_checkpoint_freeze.md"
GLOBAL_PREREGISTRATION_RELATIVE_PATH = "manuscript_v3/execution_preregistration.md"
GLOBAL_PREREGISTRATION_MACHINE_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
GLOBAL_PREREGISTRATION_TEST_RELATIVE_PATH = (
    "tests/unit/test_manuscript_v3_scientific_route.py"
)
TARGET_FIXTURE_SHA256 = (
    "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
)
TARGET_PREREQUISITE_SHA256S = (
    "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
    "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
    "09273f6bcee7c1a09165392e6ecf0125157b747d242c1f993a982ce3b2833cc7",
    "d6326ffb38c4c3ccf5aed1002f8cbd75fe5411f60d07172d5511730a63daba45",
    "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
)
STATIC_FREEZE_SEMANTIC_SHA256 = (
    "2c975bac0afa357e899383d0fc0297d7579b2a4dc99b5366186479cacee0e9ef"
)
_STATIC_FREEZE_SECTION_NAMES = (
    "artifact_contract",
    "checkpoint_acceptance",
    "coordinate",
    "execution_record",
    "fixture",
    "global_preregistration_boundary",
    "operational_limits",
    "result_record",
    "runtime_contract",
    "schema_version",
    "scientific_scope",
    "source_bindings",
    "training_protocol",
)
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
REQUIRED_DISTRIBUTIONS = (
    ("filelock", "3.32.0"),
    ("fsspec", "2026.6.0"),
    ("iniconfig", "2.3.0"),
    ("Jinja2", "3.1.6"),
    ("MarkupSafe", "3.0.3"),
    ("mpmath", "1.3.0"),
    ("networkx", "3.6.1"),
    ("numpy", "2.4.6"),
    ("packaging", "26.2"),
    ("pip", "23.2.1"),
    ("pluggy", "1.6.0"),
    ("pyflakes", "3.4.0"),
    ("Pygments", "2.20.0"),
    ("pytest", "9.1.1"),
    ("scipy", "1.17.1"),
    ("setuptools", "65.5.0"),
    ("sympy", "1.14.0"),
    ("torch", "2.12.1"),
    ("threadpoolctl", "3.6.0"),
    ("typing_extensions", "4.16.0"),
)
_MAXIMUM_JSON_BYTES = 16 * 1024 * 1024
_PROCESS_MONITOR_INTERVAL_SECONDS = 2.0
_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_LAUNCH_GATE_ENVIRONMENT_NAME = "HETERODIFF_A1_DEVELOPMENT_LAUNCH_GATE_FD"
_LAUNCH_GATE_TOKEN = b"HETERODIFF_A1_DEVELOPMENT_LAUNCH_GO_V1\n"
_LAUNCH_GATE_TOKEN_SHA256 = hashlib.sha256(_LAUNCH_GATE_TOKEN).hexdigest()
_ISOLATED_RUNNER_GATE_BOOTSTRAP = (
    "import os\n"
    "import runpy\n"
    "fd=int(os.environ.pop('HETERODIFF_A1_DEVELOPMENT_LAUNCH_GATE_FD'))\n"
    "payload=bytearray()\n"
    "while True:\n"
    "    chunk=os.read(fd,4096)\n"
    "    if not chunk:\n"
    "        break\n"
    "    payload.extend(chunk)\n"
    "os.close(fd)\n"
    "if bytes(payload)!=b'HETERODIFF_A1_DEVELOPMENT_LAUNCH_GO_V1\\n':\n"
    "    raise SystemExit(73)\n"
    "runpy.run_module("
    "'heterodiff.experiments.finite_association_isolated_runner',"
    "run_name='__main__',alter_sys=True)\n"
)
_TERMINAL_RECEIPT_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "started_unix_ns",
        "finished_unix_ns",
        "detail",
        "child_returncode",
        "partial_custody",
        "boundary_drift",
        "retry_permitted",
        "replacement_permitted",
        "checkpoint_claimed",
        "scientific_result_eligible",
        "production_order_admissible",
        "qualifies_r1",
        "qualifies_r2",
        "claim_promotion",
        "record_sha256",
    }
)
_SUCCESS_RECEIPT_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "started_unix_ns",
        "finished_unix_ns",
        "coordinate",
        "freeze_sha256",
        "retained_authorized_freeze_sha256",
        "retained_runner_test_sha256",
        "runner_source_sha256",
        "runner_test_sha256",
        "capsule_manifest_sha256",
        "runtime_preflight_sha256",
        "execution_permit_sha256",
        "execution_permit_consumption_sha256",
        "execution_outcome_linkage_sha256",
        "artifact_bytes_before_receipt",
        "artifact_inventory_before_receipt",
        "artifact_inventory_sha256",
        "inner_success",
        "retry_permitted",
        "replacement_permitted",
        "scientific_result_eligible",
        "production_order_admissible",
        "confirmatory_execution",
        "qualifies_r1",
        "qualifies_r2",
        "closes_c17",
        "claim_promotion",
        "real_domain_test_accessed",
        "receipt_sha256",
    }
)
_INNER_SUCCESS_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "run_key_sha256",
        "ledger_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "launch_authorization_sha256",
        "launch_receipt_sha256",
        "worker_session_sha256",
        "worker_process_identity_sha256",
        "worker_process_id",
        "worker_parent_process_id",
        "campaign_sha256",
        "success_receipt_sha256",
        "execution_runtime_sha256",
        "execution_runtime_record",
        "source_manifest_sha256",
        "training_configuration_sha256",
        "fixture_sha256",
        "preflight_sha256",
        "dataset_sha256",
        "batch_schedule_sha256",
        "initial_parameter_sha256",
        "parameter_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "certified_maximum_absolute_correction",
        "optimizer_steps_taken",
        "optimizer_transcript_sha256",
        "completion_receipt_sha256",
        "checkpoint_file",
        "checkpoint_sha256",
        "final_empirical_risk",
        "maximum_unclipped_gradient_norm",
        "optimizer_wall_seconds",
        "total_wall_seconds",
        "total_cpu_seconds",
        "process_peak_rss_bytes",
        "parent_confirmed_zero_child_exit",
        "inner_scientific_decision_eligible",
    }
)
_INNER_RUNTIME_FIELDS = frozenset(
    {
        "schema",
        "python",
        "python_implementation",
        "numpy",
        "scipy",
        "torch",
        "threadpoolctl",
        "platform",
        "system",
        "release",
        "machine",
        "processor",
        "cpu_identity",
        "thread_environment",
        "native_pools",
        "numpy_configuration",
        "torch_environment",
        "sha256",
    }
)
_RUNTIME_PROBE_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "python",
        "machine",
        "profile",
        "macos_version",
        "translated",
        "distributions",
        "environment",
        "native_pools",
        "fixture_sha256",
        "prerequisite_content_sha256",
        "source_manifest_sha256",
        "training_configuration_sha256",
        "preflight",
    }
)
_RUNTIME_PREFLIGHT_FIELDS = frozenset(
    {
        "seed",
        "budget",
        "method",
        "composition_mode",
        "input_features",
        "hidden_width",
        "updates",
        "torch_generator_seed",
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "custody_sha256",
        "all_dataset_sha256",
        "all_batch_schedule_sha256",
        "dataset_sha256",
        "batch_schedule_sha256",
        "training_tensor_sha256",
        "initial_parameter_sha256",
        "preflight_sha256",
        "parameter_count",
        "forward_multiply_add_count",
    }
)
_ISSUED_PERMIT_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "coordinate",
        "issued_unix_ns",
        "freeze_sha256",
        "runner_source_sha256",
        "runner_test_sha256",
        "capsule_manifest_sha256",
        "runtime_preflight_sha256",
        "one_attempt",
        "retry_or_replacement_permitted",
        "confirmatory_or_production_authority",
        "permit_sha256",
    }
)
_ATTEMPT_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "started_unix_ns",
        "coordinate",
        "freeze_sha256",
        "capsule_manifest_sha256",
        "runtime_preflight_sha256",
        "execution_permit_sha256",
        "retry_permitted",
        "replacement_permitted",
        "record_sha256",
    }
)
_PERMIT_CONSUMPTION_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "coordinate",
        "issued_permit_sha256",
        "launch_gate_protocol",
        "launch_gate_token_sha256",
        "outer_sampled_runner_process_id",
        "launched_unix_ns",
        "record_sha256",
    }
)
_OUTCOME_LINKAGE_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "state",
        "coordinate",
        "permit_consumption_sha256",
        "outer_sampled_runner_process_id",
        "outer_child_returncode",
        "inner_launch_authorization_sha256",
        "inner_launch_receipt_sha256",
        "worker_session_sha256",
        "worker_process_identity_sha256",
        "worker_process_id",
        "worker_parent_process_id",
        "linked_unix_ns",
        "record_sha256",
    }
)


class DevelopmentCheckpointRefusal(RuntimeError):
    """Raised before optimization when the frozen development contract fails."""


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def development_artifact_root(workspace_root: Optional[Path] = None) -> Path:
    root = _workspace_root() if workspace_root is None else Path(workspace_root)
    return root / ARTIFACT_RELATIVE_PATH


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_CHARACTERS for character in value)
    ):
        raise DevelopmentCheckpointRefusal(
            "%s must be a lowercase SHA-256 digest" % name
        )
    return value


def _read_regular_bytes(path: Path, *, maximum: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise DevelopmentCheckpointRefusal(
            "required file is absent: %s" % path
        ) from error
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise DevelopmentCheckpointRefusal(
            "required path is not a nonsymlink regular file: %s" % path
        )
    if before.st_size > maximum:
        raise DevelopmentCheckpointRefusal("required file exceeds its byte cap")
    payload = path.read_bytes()
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
        raise DevelopmentCheckpointRefusal("required file changed while read")
    return payload


def _parse_json_object(payload: bytes) -> Dict[str, Any]:
    def reject_duplicates(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DevelopmentCheckpointRefusal("duplicate JSON key: " + key)
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda item: (_ for _ in ()).throw(
                DevelopmentCheckpointRefusal("nonfinite JSON constant: " + item)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DevelopmentCheckpointRefusal("JSON input is invalid") from error
    if type(value) is not dict:
        raise DevelopmentCheckpointRefusal("JSON root must be an object")
    return value


def _read_json(path: Path, *, maximum: int = _MAXIMUM_JSON_BYTES) -> Dict[str, Any]:
    return _parse_json_object(_read_regular_bytes(path, maximum=maximum))


def _sha256_file(path: Path, *, maximum: int = _MAXIMUM_JSON_BYTES) -> str:
    return _sha256_bytes(_read_regular_bytes(path, maximum=maximum))


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _require_safe_artifacts_directory(root: Path, *, create: bool) -> Optional[Path]:
    """Return an in-workspace, nonsymlink artifacts directory or refuse."""

    try:
        root_status = root.lstat()
    except OSError as error:
        raise DevelopmentCheckpointRefusal("workspace root is absent") from error
    if not stat.S_ISDIR(root_status.st_mode) or root.is_symlink():
        raise DevelopmentCheckpointRefusal("workspace root is not a safe directory")
    artifacts = root / "artifacts"
    if not _lexists(artifacts):
        if not create:
            return None
        try:
            artifacts.mkdir(mode=0o755)
            _fsync_directory(root)
        except OSError as error:
            raise DevelopmentCheckpointRefusal(
                "artifacts directory could not be created safely"
            ) from error
    try:
        status = artifacts.lstat()
        resolved = artifacts.resolve(strict=True)
    except OSError as error:
        raise DevelopmentCheckpointRefusal("artifacts directory is unsafe") from error
    if (
        not stat.S_ISDIR(status.st_mode)
        or artifacts.is_symlink()
        or resolved != artifacts.absolute()
        or resolved.parent != root.absolute()
    ):
        raise DevelopmentCheckpointRefusal(
            "artifacts directory is redirected or not a directory"
        )
    return artifacts


def _write_retained_bytes(path: Path, payload: bytes) -> None:
    with open(path, "xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    _fsync_directory(path.parent)


def _atomic_write_json(path: Path, value: Mapping[str, object]) -> None:
    payload = _canonical_json_bytes(value)
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = ""
        _fsync_directory(path.parent)
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _runtime_environment(base: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    source = os.environ if base is None else base
    result = {str(key): str(value) for key, value in source.items()}
    for name in THREAD_ENVIRONMENT:
        result[name] = "1"
    result["PYTHONHASHSEED"] = "0"
    result["CUDA_VISIBLE_DEVICES"] = ""
    return result


def _target_python(root: Path) -> Path:
    candidate = root / ".venv-m1/bin/python"
    try:
        candidate_status = candidate.lstat()
        resolved = candidate.resolve(strict=True)
        resolved_status = resolved.stat()
    except OSError as error:
        raise DevelopmentCheckpointRefusal(
            "the exact .venv-m1 interpreter is absent"
        ) from error
    if (
        not (
            stat.S_ISREG(candidate_status.st_mode)
            or stat.S_ISLNK(candidate_status.st_mode)
        )
        or not stat.S_ISREG(resolved_status.st_mode)
        or not os.access(candidate, os.X_OK)
    ):
        raise DevelopmentCheckpointRefusal("the exact .venv-m1 interpreter is absent")
    # Keep the venv launcher path rather than the resolved base executable so
    # Python retains the venv prefix and its exact locked site-packages.  The
    # capsule preflight below independently attests the interpreter, ABI,
    # architecture, distributions, and numerical runtime before optimization.
    return candidate


def _current_source_and_configuration() -> Tuple[str, str]:
    from heterodiff.experiments.finite_association_residual_training_torch import (
        frozen_association_training_configuration_sha256,
        frozen_association_training_source_sha256,
    )

    source = frozen_association_training_source_sha256()
    configuration = frozen_association_training_configuration_sha256(
        source_sha256=source
    )
    return source, configuration


def _require_authorized_freeze(root: Path) -> Dict[str, Any]:
    freeze = _read_json(root / FREEZE_RELATIVE_PATH)
    if freeze.get("schema_version") != (
        "manuscript-v3-a1-development-checkpoint-freeze-v1"
    ):
        raise DevelopmentCheckpointRefusal("development freeze schema changed")
    if set(freeze) != set(_STATIC_FREEZE_SECTION_NAMES) | {
        "authorization",
        "implementation_binding",
    }:
        raise DevelopmentCheckpointRefusal("development freeze root fields changed")
    semantic_projection = {
        name: freeze.get(name) for name in _STATIC_FREEZE_SECTION_NAMES
    }
    if (
        _sha256_bytes(_canonical_json_bytes(semantic_projection))
        != STATIC_FREEZE_SEMANTIC_SHA256
    ):
        raise DevelopmentCheckpointRefusal(
            "development freeze scientific/runtime semantics changed"
        )
    scope = freeze.get("scientific_scope")
    coordinate = freeze.get("coordinate")
    limits = freeze.get("operational_limits")
    authorization = freeze.get("authorization")
    binding = freeze.get("implementation_binding")
    if not all(
        type(item) is dict
        for item in (scope, coordinate, limits, authorization, binding)
    ):
        raise DevelopmentCheckpointRefusal("development freeze sections are malformed")
    if (
        scope.get("lane_id") != LANE_ID
        or scope.get("development_checkpoint_only") is not True
        or scope.get("confirmatory_or_production_evidence") is not False
        or scope.get("production_aggregate_admission_permitted") is not False
        or scope.get("qualifies_r1") is not False
        or scope.get("qualifies_r2") is not False
        or scope.get("claim_promotion_permitted") is not False
    ):
        raise DevelopmentCheckpointRefusal("development scientific scope changed")
    if coordinate != {
        "accepted_example_budget": BUDGET,
        "batch_size": 128,
        "method": METHOD,
        "optimizer_updates": EXPECTED_UPDATES,
        "seed": SEED,
    }:
        raise DevelopmentCheckpointRefusal("development coordinate changed")
    if (
        limits.get("maximum_wall_seconds") != MAXIMUM_WALL_SECONDS
        or limits.get("maximum_recorded_peak_rss_bytes") != MAXIMUM_PEAK_RSS_BYTES
        or limits.get("maximum_capsule_output_bytes") != MAXIMUM_ARTIFACT_BYTES
        or limits.get("retry_or_substitute_coordinate_permitted_after_limit")
        is not False
    ):
        raise DevelopmentCheckpointRefusal("development resource contract changed")
    if authorization != {
        "current_state": "FROZEN_EXECUTION_AUTHORIZED",
        "development_checkpoint_execution_authorized": True,
        "execution_conditions": [
            "RUNNER_SOURCE_AND_TEST_HASH_BOUND",
            "FINAL_SOURCE_MANIFEST_RECOMPUTED",
            "FINAL_TRAINING_CONFIGURATION_RECOMPUTED",
            "TARGET_RUNTIME_ATTESTED",
            "CAPSULE_ROOT_ABSENT",
            "SINGLE_USE_PERMIT_ISSUED",
        ],
        "execution_permit_issuance_delegated_to_hash_bound_runner_after_fresh_preflight": True,
        "execution_permit_issued": False,
        "static_parameter_freeze_complete": True,
    }:
        raise DevelopmentCheckpointRefusal("development execution is not authorized")
    if set(binding) != {
        "runner_source_path",
        "runner_source_sha256",
        "runner_test_path",
        "runner_test_sha256",
        "source_manifest_sha256",
        "training_configuration_sha256",
    }:
        raise DevelopmentCheckpointRefusal("runner binding fields changed")
    expected_paths = {
        "runner_source_path": RUNNER_RELATIVE_PATH,
        "runner_test_path": RUNNER_TEST_RELATIVE_PATH,
    }
    for name, expected in expected_paths.items():
        if binding.get(name) != expected:
            raise DevelopmentCheckpointRefusal("runner binding path changed")
    for name in (
        "runner_source_sha256",
        "runner_test_sha256",
        "source_manifest_sha256",
        "training_configuration_sha256",
    ):
        _require_sha256(binding.get(name), name="implementation binding." + name)
    source_digest = _sha256_file(root / RUNNER_RELATIVE_PATH)
    test_digest = _sha256_file(root / RUNNER_TEST_RELATIVE_PATH)
    if (
        binding.get("runner_source_sha256") != source_digest
        or binding.get("runner_test_sha256") != test_digest
    ):
        raise DevelopmentCheckpointRefusal("runner source/test bytes changed")
    live_source, live_configuration = _current_source_and_configuration()
    if (
        binding.get("source_manifest_sha256") != live_source
        or binding.get("training_configuration_sha256") != live_configuration
    ):
        raise DevelopmentCheckpointRefusal("training source/configuration changed")
    source_bindings = freeze["source_bindings"]
    for path_name, digest_name in (
        ("a1_specification_path", "a1_specification_sha256"),
        (
            "global_execution_preregistration_path",
            "global_execution_preregistration_sha256",
        ),
        (
            "global_execution_preregistration_machine_path",
            "global_execution_preregistration_machine_sha256",
        ),
        (
            "global_execution_preregistration_test_path",
            "global_execution_preregistration_test_sha256",
        ),
    ):
        relative = source_bindings[path_name]
        if _sha256_file(root / relative) != source_bindings[digest_name]:
            raise DevelopmentCheckpointRefusal("bound preregistration bytes changed")
    runtime_contract = freeze["runtime_contract"]
    if (
        _sha256_file(root / runtime_contract["environment_lock_path"])
        != runtime_contract["environment_lock_sha256"]
    ):
        raise DevelopmentCheckpointRefusal("development runtime lock changed")
    return freeze


def _validate_retained_authorized_freeze(
    freeze: Mapping[str, object], *, receipt: Mapping[str, object]
) -> None:
    if set(freeze) != set(_STATIC_FREEZE_SECTION_NAMES) | {
        "authorization",
        "implementation_binding",
    }:
        raise DevelopmentCheckpointRefusal("retained freeze root fields changed")
    semantic_projection = {
        name: freeze.get(name) for name in _STATIC_FREEZE_SECTION_NAMES
    }
    if (
        _sha256_bytes(_canonical_json_bytes(semantic_projection))
        != STATIC_FREEZE_SEMANTIC_SHA256
    ):
        raise DevelopmentCheckpointRefusal("retained freeze semantics changed")
    if freeze.get("authorization") != {
        "current_state": "FROZEN_EXECUTION_AUTHORIZED",
        "development_checkpoint_execution_authorized": True,
        "execution_conditions": [
            "RUNNER_SOURCE_AND_TEST_HASH_BOUND",
            "FINAL_SOURCE_MANIFEST_RECOMPUTED",
            "FINAL_TRAINING_CONFIGURATION_RECOMPUTED",
            "TARGET_RUNTIME_ATTESTED",
            "CAPSULE_ROOT_ABSENT",
            "SINGLE_USE_PERMIT_ISSUED",
        ],
        "execution_permit_issuance_delegated_to_hash_bound_runner_after_fresh_preflight": True,
        "execution_permit_issued": False,
        "static_parameter_freeze_complete": True,
    }:
        raise DevelopmentCheckpointRefusal("retained freeze authorization changed")
    binding = freeze.get("implementation_binding")
    inner = receipt.get("inner_success")
    if type(binding) is not dict or type(inner) is not dict:
        raise DevelopmentCheckpointRefusal("retained freeze binding is malformed")
    if (
        binding.get("runner_source_path") != RUNNER_RELATIVE_PATH
        or binding.get("runner_test_path") != RUNNER_TEST_RELATIVE_PATH
        or binding.get("runner_source_sha256") != receipt.get("runner_source_sha256")
        or binding.get("runner_test_sha256") != receipt.get("runner_test_sha256")
        or binding.get("source_manifest_sha256") != inner.get("source_manifest_sha256")
        or binding.get("training_configuration_sha256")
        != inner.get("training_configuration_sha256")
    ):
        raise DevelopmentCheckpointRefusal("retained freeze binding differs")


def _retain_authorization_evidence(
    root: Path, destination: Path, *, bindings: Mapping[str, str]
) -> None:
    freeze_payload = _read_regular_bytes(
        root / FREEZE_RELATIVE_PATH, maximum=_MAXIMUM_JSON_BYTES
    )
    test_payload = _read_regular_bytes(
        root / RUNNER_TEST_RELATIVE_PATH, maximum=64 * 1024 * 1024
    )
    if (
        _sha256_bytes(freeze_payload) != bindings["freeze_sha256"]
        or _sha256_bytes(test_payload) != bindings["runner_test_sha256"]
    ):
        raise DevelopmentCheckpointRefusal(
            "authorization evidence changed before retention"
        )
    _write_retained_bytes(destination / RETAINED_FREEZE_FILE_NAME, freeze_payload)
    _write_retained_bytes(destination / RETAINED_RUNNER_TEST_FILE_NAME, test_payload)


def _require_retained_authorization_evidence(
    artifact_root: Path, *, bindings: Mapping[str, str]
) -> None:
    freeze_path = artifact_root / RETAINED_FREEZE_FILE_NAME
    test_path = artifact_root / RETAINED_RUNNER_TEST_FILE_NAME
    freeze_payload = _read_regular_bytes(freeze_path, maximum=_MAXIMUM_JSON_BYTES)
    test_payload = _read_regular_bytes(test_path, maximum=64 * 1024 * 1024)
    if (
        _sha256_bytes(freeze_payload) != bindings["freeze_sha256"]
        or _sha256_bytes(test_payload) != bindings["runner_test_sha256"]
        or freeze_path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        or test_path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    ):
        raise DevelopmentCheckpointRefusal("retained authorization evidence changed")


def _source_file_rows(root: Path) -> Tuple[Dict[str, object], ...]:
    paths = [
        root / "pyproject.toml",
        root / LOCK_RELATIVE_PATH,
        root / SPECIFICATION_RELATIVE_PATH,
    ]
    source_root = root / "src/heterodiff"
    for path in sorted(source_root.rglob("*.py"), key=lambda item: item.as_posix()):
        paths.append(path)
    rows = []
    for path in paths:
        payload = _read_regular_bytes(path, maximum=64 * 1024 * 1024)
        relative = path.relative_to(root).as_posix()
        rows.append(
            {
                "path": relative,
                "bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )
    return tuple(rows)


def _copy_capsule(root: Path, destination: Path) -> Dict[str, object]:
    rows = _source_file_rows(root)
    for row in rows:
        relative = str(row["path"])
        source = root / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = _read_regular_bytes(source, maximum=64 * 1024 * 1024)
        if _sha256_bytes(payload) != row["sha256"]:
            raise DevelopmentCheckpointRefusal("source changed during capsule copy")
        with open(target, "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(target, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    manifest: Dict[str, object] = {
        "schema": "heterodiff-a1-development-source-capsule-manifest-v1",
        "lane_id": LANE_ID,
        "file_count": len(rows),
        "files": list(rows),
    }
    manifest["manifest_sha256"] = _sha256_bytes(_canonical_json_bytes(manifest))
    return manifest


def _verify_capsule_source_manifest(
    capsule: Path, manifest: Mapping[str, object]
) -> None:
    checked = dict(manifest)
    claimed = _require_sha256(
        checked.pop("manifest_sha256", None), name="capsule manifest_sha256"
    )
    if _sha256_bytes(_canonical_json_bytes(checked)) != claimed:
        raise DevelopmentCheckpointRefusal("capsule source manifest digest changed")
    if (
        set(checked) != {"schema", "lane_id", "file_count", "files"}
        or checked.get("schema")
        != "heterodiff-a1-development-source-capsule-manifest-v1"
        or checked.get("lane_id") != LANE_ID
        or type(checked.get("file_count")) is not int
        or type(checked.get("files")) is not list
        or checked["file_count"] != len(checked["files"])
    ):
        raise DevelopmentCheckpointRefusal("capsule source manifest shape changed")
    observed_paths = []
    for row in checked["files"]:
        if type(row) is not dict or set(row) != {"path", "bytes", "sha256"}:
            raise DevelopmentCheckpointRefusal("capsule source row shape changed")
        relative = row.get("path")
        size = row.get("bytes")
        if (
            type(relative) is not str
            or not relative
            or relative.startswith("/")
            or ".." in Path(relative).parts
            or type(size) is not int
            or size < 0
        ):
            raise DevelopmentCheckpointRefusal("capsule source row is invalid")
        expected = _require_sha256(row.get("sha256"), name="capsule source row sha256")
        path = capsule / relative
        payload = _read_regular_bytes(path, maximum=64 * 1024 * 1024)
        if len(payload) != size or _sha256_bytes(payload) != expected:
            raise DevelopmentCheckpointRefusal("capsule source bytes changed")
        if path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            raise DevelopmentCheckpointRefusal("capsule source became writable")
        observed_paths.append(relative)
    if observed_paths != sorted(observed_paths) or len(observed_paths) != len(
        set(observed_paths)
    ):
        raise DevelopmentCheckpointRefusal("capsule source order changed")
    actual_nonoutput_paths = set()
    for path in capsule.rglob("*"):
        relative_path = path.relative_to(capsule)
        if relative_path.parts and relative_path.parts[0] == "artifacts":
            continue
        status = path.lstat()
        if stat.S_ISDIR(status.st_mode):
            continue
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
            raise DevelopmentCheckpointRefusal(
                "capsule contains a nonregular importable source"
            )
        actual_nonoutput_paths.add(relative_path.as_posix())
    if actual_nonoutput_paths != set(observed_paths):
        raise DevelopmentCheckpointRefusal(
            "capsule contains an unbound or missing importable source"
        )


def _root_binding_snapshot(root: Path) -> Dict[str, str]:
    return {
        "freeze_sha256": _sha256_file(root / FREEZE_RELATIVE_PATH),
        "runner_source_sha256": _sha256_file(root / RUNNER_RELATIVE_PATH),
        "runner_test_sha256": _sha256_file(root / RUNNER_TEST_RELATIVE_PATH),
        "freeze_document_sha256": _sha256_file(
            root / FREEZE_DOCUMENT_RELATIVE_PATH, maximum=64 * 1024 * 1024
        ),
        "a1_specification_sha256": _sha256_file(
            root / SPECIFICATION_RELATIVE_PATH, maximum=64 * 1024 * 1024
        ),
        "runtime_lock_sha256": _sha256_file(
            root / LOCK_RELATIVE_PATH, maximum=64 * 1024 * 1024
        ),
        "global_preregistration_sha256": _sha256_file(
            root / GLOBAL_PREREGISTRATION_RELATIVE_PATH,
            maximum=64 * 1024 * 1024,
        ),
        "global_preregistration_machine_sha256": _sha256_file(
            root / GLOBAL_PREREGISTRATION_MACHINE_RELATIVE_PATH,
            maximum=64 * 1024 * 1024,
        ),
        "global_preregistration_test_sha256": _sha256_file(
            root / GLOBAL_PREREGISTRATION_TEST_RELATIVE_PATH,
            maximum=64 * 1024 * 1024,
        ),
    }


def _require_unchanged_root_bindings(root: Path, expected: Mapping[str, str]) -> None:
    if _root_binding_snapshot(root) != dict(expected):
        raise DevelopmentCheckpointRefusal(
            "freeze or runner source/test bytes changed during execution"
        )


def _require_forbidden_outputs_absent(root: Path) -> None:
    if any(_lexists(root / relative) for relative in FORBIDDEN_OUTPUT_RELATIVE_PATHS):
        raise DevelopmentCheckpointRefusal("a forbidden production output path exists")


def _capsule_python_environment(
    capsule: Path, base: Optional[Mapping[str, str]] = None
) -> Dict[str, str]:
    result = _runtime_environment(base)
    result["PYTHONPATH"] = str(capsule / "src")
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    result["PYTHONSAFEPATH"] = "1"
    return result


def _distribution_versions() -> Dict[str, str]:
    observed: Dict[str, str] = {}
    for name, expected in REQUIRED_DISTRIBUTIONS:
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise DevelopmentCheckpointRefusal(
                "required distribution is absent: " + name
            ) from error
        if actual != expected:
            raise DevelopmentCheckpointRefusal(
                "distribution %s is %s, expected %s" % (name, actual, expected)
            )
        observed[name] = actual
    return observed


def _probe_current_capsule() -> Dict[str, object]:
    """Run only inside an exact-runtime source capsule; never optimize."""

    import platform
    import struct
    import sys
    import sysconfig

    import threadpoolctl

    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
        frozen_association_fixture_sha256,
        run_association_residual_prerequisite_gate,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        configure_frozen_association_training_environment,
        prepare_frozen_association_residual_training,
    )

    expected_environment = {name: "1" for name in THREAD_ENVIRONMENT}
    expected_environment.update(
        {
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONSAFEPATH": "1",
        }
    )
    if any(
        os.environ.get(name) != value for name, value in expected_environment.items()
    ):
        raise DevelopmentCheckpointRefusal(
            "development runtime environment differs from the freeze"
        )
    profile = {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_abi": sysconfig.get_config_var("SOABI"),
        "pointer_bits": struct.calcsize("P") * 8,
        "byteorder": sys.byteorder,
    }
    if profile != {
        "system": "Darwin",
        "machine": "arm64",
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "python_abi": "cpython-311-darwin",
        "pointer_bits": 64,
        "byteorder": "little",
    }:
        raise DevelopmentCheckpointRefusal(
            "development process is not the frozen native CPython profile"
        )
    macos_version = platform.mac_ver()[0]
    try:
        macos_components = tuple(int(item) for item in macos_version.split("."))
    except ValueError as error:
        raise DevelopmentCheckpointRefusal("macOS version is not canonical") from error
    if not macos_components or macos_components < (14, 0):
        raise DevelopmentCheckpointRefusal("macOS version predates the frozen minimum")

    environment = configure_frozen_association_training_environment()
    pools = threadpoolctl.threadpool_info()
    pool_paths = tuple(item.get("filepath") for item in pools)
    if (
        not pools
        or len(set(pool_paths)) != len(pool_paths)
        or any(
            type(item.get("filepath")) is not str
            or not os.path.isabs(str(item.get("filepath")))
            or item.get("user_api") not in ("blas", "openmp")
            or item.get("num_threads") != 1
            for item in pools
        )
    ):
        raise DevelopmentCheckpointRefusal("native numerical pools are not frozen")
    fixture = frozen_association_fixture_sha256()
    gate = run_association_residual_prerequisite_gate()
    if fixture != TARGET_FIXTURE_SHA256 or not gate.passed:
        raise DevelopmentCheckpointRefusal("frozen A1 prerequisite did not pass")
    prepared = prepare_frozen_association_residual_training(SEED, BUDGET, METHOD)
    source, configuration = _current_source_and_configuration()
    if (
        prepared.preflight.fixture_sha256 != fixture
        or prepared.preflight.source_sha256 != source
        or prepared.preflight.configuration_sha256 != configuration
        or prepared.preflight.updates != EXPECTED_UPDATES
    ):
        raise DevelopmentCheckpointRefusal("development preflight is inconsistent")
    return {
        "schema": "heterodiff-a1-development-runtime-preflight-v1",
        "lane_id": LANE_ID,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "profile": profile,
        "macos_version": macos_version,
        "translated": False,
        "distributions": _distribution_versions(),
        "environment": asdict(environment),
        "native_pools": pools,
        "fixture_sha256": fixture,
        "prerequisite_content_sha256": list(FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS),
        "source_manifest_sha256": source,
        "training_configuration_sha256": configuration,
        "preflight": asdict(prepared.preflight),
    }


def _verify_inner_success() -> Dict[str, object]:
    """Run inside the capsule and reopen the unchanged inner SUCCESS custody."""

    from heterodiff.experiments.finite_association_isolated_runner import (
        frozen_association_campaign_directory,
        load_successful_frozen_association_checkpoint,
        revalidate_successful_frozen_association_checkpoint,
    )

    directory = frozen_association_campaign_directory()
    ledger_path = directory / "ledger.json"
    ledger_payload = _read_regular_bytes(ledger_path, maximum=_MAXIMUM_JSON_BYTES)
    ledger_sha256 = _sha256_bytes(ledger_payload)
    ledger = _parse_json_object(ledger_payload)
    runs = ledger.get("runs")
    if type(runs) is not dict or len(runs) != 1:
        raise DevelopmentCheckpointRefusal("inner campaign must contain one run")
    run_key, record = next(iter(runs.items()))
    if type(record) is not dict or record.get("state") != "SUCCESS":
        raise DevelopmentCheckpointRefusal("inner run is not SUCCESS")
    verified = load_successful_frozen_association_checkpoint(run_key)
    revalidate_successful_frozen_association_checkpoint(verified)
    authorizations = ledger.get("launch_authorizations")
    if (
        type(authorizations) is not dict
        or len(authorizations) != 1
        or set(authorizations) != {verified.launch_authorization_sha256}
    ):
        raise DevelopmentCheckpointRefusal(
            "inner campaign must contain exactly one launch authorization"
        )
    if _sha256_file(ledger_path) != ledger_sha256:
        raise DevelopmentCheckpointRefusal("inner ledger changed during verification")
    checkpoint = verified.checkpoint
    runtime = _validate_inner_runtime_record(
        record.get("runtime"), expected_sha256=checkpoint.execution_runtime_sha256
    )
    if (
        checkpoint.preflight.seed != SEED
        or checkpoint.preflight.budget != BUDGET
        or checkpoint.preflight.method != METHOD
        or checkpoint.optimizer_steps_taken != EXPECTED_UPDATES
        or checkpoint.preflight.fixture_sha256 != TARGET_FIXTURE_SHA256
    ):
        raise DevelopmentCheckpointRefusal("inner checkpoint coordinate changed")
    return {
        "schema": "heterodiff-a1-development-inner-success-summary-v1",
        "lane_id": LANE_ID,
        "run_key_sha256": checkpoint.run_key_sha256,
        "ledger_sha256": ledger_sha256,
        "prepared_ledger_sha256": checkpoint.prepared_ledger_sha256,
        "running_ledger_sha256": verified.running_ledger_sha256,
        "launch_authorization_sha256": verified.launch_authorization_sha256,
        "launch_receipt_sha256": verified.launch_receipt_sha256,
        "worker_session_sha256": verified.worker_session_sha256,
        "worker_process_identity_sha256": verified.worker_process_identity_sha256,
        "worker_process_id": verified.worker_process_id,
        "worker_parent_process_id": verified.worker_parent_process_id,
        "campaign_sha256": verified.campaign_sha256,
        "success_receipt_sha256": verified.success_receipt_sha256,
        "execution_runtime_sha256": checkpoint.execution_runtime_sha256,
        "execution_runtime_record": runtime,
        "source_manifest_sha256": checkpoint.preflight.source_sha256,
        "training_configuration_sha256": checkpoint.preflight.configuration_sha256,
        "fixture_sha256": checkpoint.preflight.fixture_sha256,
        "preflight_sha256": checkpoint.preflight.preflight_sha256,
        "dataset_sha256": checkpoint.preflight.dataset_sha256,
        "batch_schedule_sha256": checkpoint.preflight.batch_schedule_sha256,
        "initial_parameter_sha256": checkpoint.preflight.initial_parameter_sha256,
        "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
        "classifier_sha256": checkpoint.classifier_sha256,
        "certificate_sha256": checkpoint.certificate.certificate_sha256,
        "certified_maximum_absolute_correction": checkpoint.certificate.certified_maximum_absolute_correction,
        "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
        "optimizer_transcript_sha256": checkpoint.optimizer_transcript_sha256,
        "completion_receipt_sha256": checkpoint.optimizer_completion_receipt.completion_receipt_sha256,
        "checkpoint_file": record["checkpoint_file"],
        "checkpoint_sha256": record["checkpoint_sha256"],
        "final_empirical_risk": checkpoint.final_empirical_risk,
        "maximum_unclipped_gradient_norm": checkpoint.maximum_unclipped_gradient_norm,
        "optimizer_wall_seconds": checkpoint.elapsed_training_seconds,
        "total_wall_seconds": checkpoint.total_wall_seconds,
        "total_cpu_seconds": checkpoint.total_cpu_seconds,
        "process_peak_rss_bytes": checkpoint.process_peak_rss_bytes,
        "parent_confirmed_zero_child_exit": record.get("exit_child_returncode") == 0,
        "inner_scientific_decision_eligible": False,
    }


def _run_json_subprocess(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> Dict[str, object]:
    completed = subprocess.run(
        tuple(command),
        cwd=str(cwd),
        env=dict(environment),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise DevelopmentCheckpointRefusal(
            "capsule subprocess failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-4096:]
        )
    if len(completed.stdout) > _MAXIMUM_JSON_BYTES:
        raise DevelopmentCheckpointRefusal("capsule subprocess output exceeds its cap")
    try:
        decoded = completed.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DevelopmentCheckpointRefusal(
            "capsule subprocess output is not UTF-8"
        ) from error
    lines = decoded.splitlines()
    if len(lines) != 1:
        raise DevelopmentCheckpointRefusal(
            "capsule subprocess output is not one JSON row"
        )
    value = _parse_json_object(lines[0].encode("utf-8"))
    if completed.stdout != _canonical_json_bytes(value) + b"\n":
        raise DevelopmentCheckpointRefusal(
            "capsule subprocess output is not canonical JSON"
        )
    return value


def _validate_runtime_probe(
    probe: Mapping[str, object], *, binding: Mapping[str, object]
) -> None:
    if set(probe) != _RUNTIME_PROBE_FIELDS:
        raise DevelopmentCheckpointRefusal("development runtime probe fields changed")
    exact_scalars = {
        "schema": "heterodiff-a1-development-runtime-preflight-v1",
        "lane_id": LANE_ID,
        "python": "3.11.5",
        "machine": "arm64",
        "translated": False,
        "fixture_sha256": TARGET_FIXTURE_SHA256,
        "source_manifest_sha256": binding.get("source_manifest_sha256"),
        "training_configuration_sha256": binding.get("training_configuration_sha256"),
    }
    if any(probe.get(key) != value for key, value in exact_scalars.items()):
        raise DevelopmentCheckpointRefusal(
            "development runtime probe differs from the frozen profile or binding"
        )
    if probe.get("profile") != {
        "system": "Darwin",
        "machine": "arm64",
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "python_abi": "cpython-311-darwin",
        "pointer_bits": 64,
        "byteorder": "little",
    }:
        raise DevelopmentCheckpointRefusal("development runtime profile changed")
    macos_version = probe.get("macos_version")
    if type(macos_version) is not str:
        raise DevelopmentCheckpointRefusal("development macOS version is absent")
    try:
        macos_components = tuple(int(item) for item in macos_version.split("."))
    except ValueError as error:
        raise DevelopmentCheckpointRefusal(
            "development macOS version is not canonical"
        ) from error
    if not macos_components or macos_components < (14, 0):
        raise DevelopmentCheckpointRefusal(
            "development macOS version predates the frozen minimum"
        )
    if probe.get("distributions") != dict(REQUIRED_DISTRIBUTIONS):
        raise DevelopmentCheckpointRefusal("development runtime distributions changed")
    environment = probe.get("environment")
    if type(environment) is not dict or environment != {
        "python_version": "3.11.5",
        "numpy_version": "2.4.6",
        "scipy_version": "1.17.1",
        "torch_version": "2.12.1",
        "torch_cpu_only": True,
        "torch_threads": 1,
        "torch_interop_threads": 1,
        "deterministic_algorithms": True,
    }:
        raise DevelopmentCheckpointRefusal("development numerical mode changed")
    if probe.get("prerequisite_content_sha256") != list(TARGET_PREREQUISITE_SHA256S):
        raise DevelopmentCheckpointRefusal("development A1 prerequisites changed")
    pools = probe.get("native_pools")
    if type(pools) is not list or not pools:
        raise DevelopmentCheckpointRefusal("development native pools are absent")
    pool_paths = []
    for row in pools:
        if (
            type(row) is not dict
            or type(row.get("filepath")) is not str
            or not os.path.isabs(str(row.get("filepath")))
            or row.get("user_api") not in ("blas", "openmp")
            or row.get("num_threads") != 1
        ):
            raise DevelopmentCheckpointRefusal("development native pool changed")
        pool_paths.append(row["filepath"])
    if len(pool_paths) != len(set(pool_paths)):
        raise DevelopmentCheckpointRefusal("development native pools are duplicated")
    preflight = probe.get("preflight")
    if (
        type(preflight) is not dict
        or set(preflight) != _RUNTIME_PREFLIGHT_FIELDS
        or any(
            preflight.get(key) != value
            for key, value in {
                "seed": SEED,
                "budget": BUDGET,
                "method": METHOD,
                "composition_mode": METHOD,
                "updates": EXPECTED_UPDATES,
                "input_features": 21,
                "hidden_width": 32,
                "parameter_count": 1793,
                "fixture_sha256": TARGET_FIXTURE_SHA256,
                "source_sha256": binding.get("source_manifest_sha256"),
                "configuration_sha256": binding.get("training_configuration_sha256"),
            }.items()
        )
    ):
        raise DevelopmentCheckpointRefusal("development training preflight changed")


def _validate_inner_runtime_record(
    value: object, *, expected_sha256: object
) -> Dict[str, object]:
    if type(value) is not dict:
        raise DevelopmentCheckpointRefusal("inner execution runtime is absent")
    runtime = dict(value)
    if set(runtime) != _INNER_RUNTIME_FIELDS:
        raise DevelopmentCheckpointRefusal("inner execution runtime fields changed")
    claimed = _require_sha256(
        runtime.pop("sha256", None), name="inner execution runtime.sha256"
    )
    if (
        claimed != expected_sha256
        or _sha256_bytes(_canonical_json_bytes(runtime)) != claimed
    ):
        raise DevelopmentCheckpointRefusal("inner execution runtime digest differs")
    runtime["sha256"] = claimed
    if any(
        runtime.get(name) != expected
        for name, expected in {
            "python": "3.11.5",
            "python_implementation": "CPython",
            "numpy": "2.4.6",
            "scipy": "1.17.1",
            "torch": "2.12.1",
            "threadpoolctl": "3.6.0",
            "system": "Darwin",
            "machine": "arm64",
        }.items()
    ):
        raise DevelopmentCheckpointRefusal("inner execution runtime profile changed")
    expected_thread_environment = {
        **{name: "1" for name in THREAD_ENVIRONMENT},
        "PYTHONHASHSEED": "0",
        "CUDA_VISIBLE_DEVICES": "",
    }
    if runtime.get("thread_environment") != expected_thread_environment:
        raise DevelopmentCheckpointRefusal(
            "inner execution runtime thread environment changed"
        )
    pools = runtime.get("native_pools")
    if (
        type(pools) is not list
        or not pools
        or any(type(row) is not dict or row.get("num_threads") != 1 for row in pools)
    ):
        raise DevelopmentCheckpointRefusal("inner execution runtime pools changed")
    torch_environment = runtime.get("torch_environment")
    if type(torch_environment) is not dict or torch_environment != {
        "python_version": "3.11.5",
        "numpy_version": "2.4.6",
        "scipy_version": "1.17.1",
        "torch_version": "2.12.1",
        "torch_cpu_only": True,
        "torch_threads": 1,
        "torch_interop_threads": 1,
        "deterministic_algorithms": True,
    }:
        raise DevelopmentCheckpointRefusal("inner Torch runtime changed")
    return runtime


def _remaining_timeout(deadline: float, *, maximum: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0.0:
        raise DevelopmentCheckpointRefusal("development wall-time ceiling elapsed")
    return min(maximum, remaining)


def _terminate_process_group(process: subprocess.Popen[bytes]) -> int:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        return int(process.wait(timeout=10))
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return int(process.wait())


def _wait_for_child_with_limits(
    process: subprocess.Popen[bytes], *, artifact_root: Path, deadline: float
) -> Tuple[int, bool]:
    """Wait while enforcing the whole-attempt wall and artifact ceilings."""

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                return _terminate_process_group(process), True
            try:
                return (
                    int(
                        process.wait(
                            timeout=min(_PROCESS_MONITOR_INTERVAL_SECONDS, remaining)
                        )
                    ),
                    False,
                )
            except subprocess.TimeoutExpired:
                _tree_size(artifact_root)
    except BaseException:
        _terminate_process_group(process)
        raise


def _tree_size(path: Path) -> int:
    total = 0
    for candidate in path.rglob("*"):
        try:
            status = candidate.lstat()
        except FileNotFoundError:
            # The live child uses atomic temporary files.  A vanished entry is
            # checked on the next monitor pass and cannot survive final audit.
            continue
        if stat.S_ISLNK(status.st_mode):
            raise DevelopmentCheckpointRefusal("artifact tree contains a symlink")
        if stat.S_ISREG(status.st_mode):
            total += status.st_size
            if total > MAXIMUM_ARTIFACT_BYTES:
                raise DevelopmentCheckpointRefusal("artifact tree exceeds 2 GiB")
        elif not stat.S_ISDIR(status.st_mode):
            raise DevelopmentCheckpointRefusal("artifact tree contains a special file")
    return total


def _artifact_inventory(
    artifact_root: Path, *, exclude_relative_paths: Sequence[str] = ()
) -> Tuple[Dict[str, object], ...]:
    excluded = frozenset(exclude_relative_paths)
    rows = []
    for path in sorted(artifact_root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(artifact_root).as_posix()
        if relative in excluded:
            continue
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise DevelopmentCheckpointRefusal("artifact inventory contains a symlink")
        if stat.S_ISDIR(status.st_mode):
            continue
        if not stat.S_ISREG(status.st_mode):
            raise DevelopmentCheckpointRefusal(
                "artifact inventory contains a special file"
            )
        if status.st_size > MAXIMUM_ARTIFACT_BYTES:
            raise DevelopmentCheckpointRefusal("artifact file exceeds 2 GiB")
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        after = path.lstat()
        if (
            status.st_dev,
            status.st_ino,
            status.st_size,
            status.st_mtime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise DevelopmentCheckpointRefusal("artifact file changed during inventory")
        rows.append(
            {"path": relative, "bytes": status.st_size, "sha256": digest.hexdigest()}
        )
    if len({row["path"] for row in rows}) != len(rows):
        raise DevelopmentCheckpointRefusal("artifact inventory paths are duplicated")
    return tuple(rows)


def _artifact_inventory_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    return _sha256_bytes(
        b"heterodiff-a1-development-artifact-inventory-v1\0"
        + _canonical_json_bytes(list(rows))
    )


def _require_saved_json_equals(path: Path, expected: Mapping[str, object]) -> None:
    payload = _read_regular_bytes(path, maximum=_MAXIMUM_JSON_BYTES)
    if payload != _canonical_json_bytes(expected):
        raise DevelopmentCheckpointRefusal("saved evidence bytes changed: %s" % path)


def _validate_self_digested_record(
    value: Mapping[str, object], *, field: str, name: str
) -> Dict[str, object]:
    record = dict(value)
    claimed = _require_sha256(record.pop(field, None), name=name + "." + field)
    if _sha256_bytes(_canonical_json_bytes(record)) != claimed:
        raise DevelopmentCheckpointRefusal(name + " digest differs")
    record[field] = claimed
    return record


def _validate_permit_consumption(
    value: Mapping[str, object],
    *,
    permit: Mapping[str, object],
) -> Dict[str, object]:
    record = _validate_self_digested_record(
        value, field="record_sha256", name="permit consumption"
    )
    if (
        set(record) != _PERMIT_CONSUMPTION_FIELDS
        or record.get("schema") != "heterodiff-a1-development-permit-consumption-v1"
        or record.get("lane_id") != LANE_ID
        or record.get("state") != "CONSUMED_LAUNCHED"
        or record.get("coordinate")
        != {"seed": SEED, "budget": BUDGET, "method": METHOD}
        or record.get("issued_permit_sha256") != permit.get("permit_sha256")
        or record.get("launch_gate_protocol") != "PIPE_EOF_FAIL_CLOSED_V1"
        or record.get("launch_gate_token_sha256") != _LAUNCH_GATE_TOKEN_SHA256
        or type(record.get("outer_sampled_runner_process_id")) is not int
        or record["outer_sampled_runner_process_id"] <= 0
        or type(record.get("launched_unix_ns")) is not int
        or record["launched_unix_ns"] <= 0
    ):
        raise DevelopmentCheckpointRefusal("permit consumption differs")
    return record


def _validate_outcome_linkage(
    value: Mapping[str, object],
    *,
    consumption: Mapping[str, object],
    inner: Mapping[str, object],
) -> Dict[str, object]:
    record = _validate_self_digested_record(
        value, field="record_sha256", name="outcome linkage"
    )
    if (
        set(record) != _OUTCOME_LINKAGE_FIELDS
        or record.get("schema") != "heterodiff-a1-development-outcome-linkage-v1"
        or record.get("lane_id") != LANE_ID
        or record.get("state") != "ACCEPTED_SUCCESS_LINKAGE"
        or record.get("coordinate")
        != {"seed": SEED, "budget": BUDGET, "method": METHOD}
        or record.get("permit_consumption_sha256") != consumption.get("record_sha256")
        or record.get("outer_child_returncode") != 0
        or record.get("inner_launch_authorization_sha256")
        != inner.get("launch_authorization_sha256")
        or record.get("inner_launch_receipt_sha256")
        != inner.get("launch_receipt_sha256")
        or record.get("worker_session_sha256") != inner.get("worker_session_sha256")
        or record.get("worker_process_identity_sha256")
        != inner.get("worker_process_identity_sha256")
        or record.get("worker_process_id") != inner.get("worker_process_id")
        or record.get("worker_parent_process_id")
        != inner.get("worker_parent_process_id")
        or record.get("outer_sampled_runner_process_id")
        != inner.get("worker_parent_process_id")
        or type(record.get("outer_sampled_runner_process_id")) is not int
        or record["outer_sampled_runner_process_id"] <= 0
        or type(record.get("worker_process_id")) is not int
        or record["worker_process_id"] <= 0
        or record.get("outer_sampled_runner_process_id")
        != consumption.get("outer_sampled_runner_process_id")
        or type(record.get("linked_unix_ns")) is not int
        or record["linked_unix_ns"] <= 0
    ):
        raise DevelopmentCheckpointRefusal("outcome linkage differs")
    return record


def _optional_regular_sha256(path: Path, *, maximum: int) -> Optional[str]:
    if not _lexists(path):
        return None
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or path.is_symlink()
            or before.st_size > maximum
        ):
            return None
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        after = path.lstat()
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            return None
        return digest.hexdigest()
    except (OSError, DevelopmentCheckpointRefusal):
        return None


def _terminal_custody(artifact_root: Path) -> Dict[str, object]:
    inner = artifact_root / CAPSULE_DIRECTORY_NAME / INNER_CAMPAIGN_RELATIVE_PATH
    paths = {
        "retained_authorized_freeze_sha256": artifact_root / RETAINED_FREEZE_FILE_NAME,
        "retained_runner_test_sha256": artifact_root / RETAINED_RUNNER_TEST_FILE_NAME,
        "attempt_sha256": artifact_root / "attempt.json",
        "execution_permit_sha256": artifact_root / "execution-permit.json",
        "execution_permit_consumption_sha256": artifact_root
        / "execution-permit-consumption.json",
        "execution_outcome_linkage_sha256": artifact_root
        / "execution-outcome-linkage.json",
        "capsule_manifest_file_sha256": artifact_root / "capsule-source-manifest.json",
        "runtime_preflight_file_sha256": artifact_root / "runtime-preflight.json",
        "partial_inner_ledger_sha256": inner / "ledger.json",
        "inner_stdout_sha256": artifact_root / "inner-run.stdout",
        "inner_stderr_sha256": artifact_root / "inner-run.stderr",
    }
    return {
        name: _optional_regular_sha256(path, maximum=MAXIMUM_ARTIFACT_BYTES)
        for name, path in paths.items()
    }


def _boundary_drift(
    root: Path, *, expected_bindings: Optional[Mapping[str, str]] = None
) -> Dict[str, bool]:
    bindings_changed = False
    if expected_bindings is not None:
        try:
            bindings_changed = _root_binding_snapshot(root) != dict(expected_bindings)
        except DevelopmentCheckpointRefusal:
            bindings_changed = True
    return {
        "main_campaign_root_present": _lexists(root / INNER_CAMPAIGN_RELATIVE_PATH),
        "production_order_root_present": _lexists(
            root / PRODUCTION_ORDER_RELATIVE_PATH
        ),
        "root_binding_changed": bindings_changed,
    }


def _terminal_record(
    *,
    state: str,
    started_unix_ns: int,
    detail: str,
    returncode: Optional[int],
    custody: Optional[Mapping[str, object]] = None,
    boundary_drift: Optional[Mapping[str, bool]] = None,
) -> Dict[str, object]:
    record: Dict[str, object] = {
        "schema": "heterodiff-a1-development-attempt-terminal-v1",
        "lane_id": LANE_ID,
        "state": state,
        "started_unix_ns": started_unix_ns,
        "finished_unix_ns": time.time_ns(),
        "detail": detail[-4096:],
        "child_returncode": returncode,
        "partial_custody": dict(custody or {}),
        "boundary_drift": dict(boundary_drift or {}),
        "retry_permitted": False,
        "replacement_permitted": False,
        "checkpoint_claimed": False,
        "scientific_result_eligible": False,
        "production_order_admissible": False,
        "qualifies_r1": False,
        "qualifies_r2": False,
        "claim_promotion": False,
    }
    record["record_sha256"] = _sha256_bytes(_canonical_json_bytes(record))
    return record


def _validate_terminal_receipt(value: Mapping[str, object]) -> Dict[str, object]:
    record = dict(value)
    if set(record) != _TERMINAL_RECEIPT_FIELDS:
        raise DevelopmentCheckpointRefusal("terminal receipt fields changed")
    claimed = _require_sha256(
        record.pop("record_sha256", None), name="terminal record_sha256"
    )
    if _sha256_bytes(_canonical_json_bytes(record)) != claimed:
        raise DevelopmentCheckpointRefusal("terminal receipt digest differs")
    record["record_sha256"] = claimed
    if (
        record.get("schema") != "heterodiff-a1-development-attempt-terminal-v1"
        or record.get("lane_id") != LANE_ID
        or record.get("state") not in ("TIMEOUT", "FAILURE", "REFUSED", "INTERRUPTED")
        or record.get("retry_permitted") is not False
        or record.get("replacement_permitted") is not False
        or record.get("checkpoint_claimed") is not False
        or record.get("scientific_result_eligible") is not False
        or record.get("production_order_admissible") is not False
        or record.get("qualifies_r1") is not False
        or record.get("qualifies_r2") is not False
        or record.get("claim_promotion") is not False
    ):
        raise DevelopmentCheckpointRefusal("terminal receipt claims changed")
    custody = record.get("partial_custody")
    expected_custody_fields = {
        "retained_authorized_freeze_sha256",
        "retained_runner_test_sha256",
        "attempt_sha256",
        "execution_permit_sha256",
        "execution_permit_consumption_sha256",
        "execution_outcome_linkage_sha256",
        "capsule_manifest_file_sha256",
        "runtime_preflight_file_sha256",
        "partial_inner_ledger_sha256",
        "inner_stdout_sha256",
        "inner_stderr_sha256",
    }
    if type(custody) is not dict or set(custody) != expected_custody_fields:
        raise DevelopmentCheckpointRefusal("terminal partial custody changed")
    for name, digest in custody.items():
        if digest is not None:
            _require_sha256(digest, name="terminal partial custody." + name)
    boundary = record.get("boundary_drift")
    if (
        type(boundary) is not dict
        or set(boundary)
        != {
            "main_campaign_root_present",
            "production_order_root_present",
            "root_binding_changed",
        }
        or any(type(value) is not bool for value in boundary.values())
    ):
        raise DevelopmentCheckpointRefusal("terminal boundary drift changed")
    return record


def _validate_success_receipt(value: Mapping[str, object]) -> Dict[str, object]:
    receipt = dict(value)
    if set(receipt) != _SUCCESS_RECEIPT_FIELDS:
        raise DevelopmentCheckpointRefusal("success receipt fields changed")
    claimed = _require_sha256(
        receipt.pop("receipt_sha256", None), name="success receipt_sha256"
    )
    if _sha256_bytes(_canonical_json_bytes(receipt)) != claimed:
        raise DevelopmentCheckpointRefusal("success receipt digest differs")
    receipt["receipt_sha256"] = claimed
    if (
        receipt.get("schema") != RECEIPT_SCHEMA_VERSION
        or receipt.get("lane_id") != LANE_ID
        or receipt.get("state") != "SUCCESS_DEVELOPMENT_CHECKPOINT"
        or receipt.get("coordinate")
        != {"seed": SEED, "budget": BUDGET, "method": METHOD}
        or receipt.get("retry_permitted") is not False
        or receipt.get("replacement_permitted") is not False
        or receipt.get("scientific_result_eligible") is not False
        or receipt.get("production_order_admissible") is not False
        or receipt.get("confirmatory_execution") is not False
        or receipt.get("qualifies_r1") is not False
        or receipt.get("qualifies_r2") is not False
        or receipt.get("closes_c17") is not False
        or receipt.get("claim_promotion") is not False
        or receipt.get("real_domain_test_accessed") is not False
    ):
        raise DevelopmentCheckpointRefusal("success receipt claims changed")
    inner = receipt.get("inner_success")
    if (
        type(inner) is not dict
        or set(inner) != _INNER_SUCCESS_FIELDS
        or inner.get("schema") != "heterodiff-a1-development-inner-success-summary-v1"
        or inner.get("lane_id") != LANE_ID
        or inner.get("optimizer_steps_taken") != EXPECTED_UPDATES
        or inner.get("fixture_sha256") != TARGET_FIXTURE_SHA256
        or inner.get("parent_confirmed_zero_child_exit") is not True
        or inner.get("inner_scientific_decision_eligible") is not False
    ):
        raise DevelopmentCheckpointRefusal("success receipt inner custody changed")
    for name in (
        "freeze_sha256",
        "retained_authorized_freeze_sha256",
        "retained_runner_test_sha256",
        "runner_source_sha256",
        "runner_test_sha256",
        "capsule_manifest_sha256",
        "runtime_preflight_sha256",
        "execution_permit_sha256",
        "execution_permit_consumption_sha256",
        "execution_outcome_linkage_sha256",
    ):
        _require_sha256(receipt.get(name), name="success " + name)
    for name in (
        "run_key_sha256",
        "campaign_sha256",
        "ledger_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "launch_authorization_sha256",
        "launch_receipt_sha256",
        "worker_session_sha256",
        "worker_process_identity_sha256",
        "success_receipt_sha256",
        "execution_runtime_sha256",
        "checkpoint_sha256",
        "source_manifest_sha256",
        "training_configuration_sha256",
        "certificate_sha256",
        "optimizer_transcript_sha256",
        "preflight_sha256",
        "dataset_sha256",
        "batch_schedule_sha256",
        "initial_parameter_sha256",
        "parameter_sha256",
        "classifier_sha256",
        "completion_receipt_sha256",
    ):
        _require_sha256(inner.get(name), name="success inner." + name)
    _validate_inner_runtime_record(
        inner.get("execution_runtime_record"),
        expected_sha256=inner.get("execution_runtime_sha256"),
    )
    if receipt.get("retained_authorized_freeze_sha256") != receipt.get(
        "freeze_sha256"
    ) or receipt.get("retained_runner_test_sha256") != receipt.get(
        "runner_test_sha256"
    ):
        raise DevelopmentCheckpointRefusal(
            "retained authorization evidence digests differ"
        )
    inventory = receipt.get("artifact_inventory_before_receipt")
    if type(inventory) is not list:
        raise DevelopmentCheckpointRefusal("success artifact inventory is absent")
    inventory_paths = []
    inventory_bytes = 0
    for row in inventory:
        if type(row) is not dict or set(row) != {"path", "bytes", "sha256"}:
            raise DevelopmentCheckpointRefusal("success artifact inventory row changed")
        path = row.get("path")
        size = row.get("bytes")
        if (
            type(path) is not str
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or type(size) is not int
            or size < 0
        ):
            raise DevelopmentCheckpointRefusal(
                "success artifact inventory row is invalid"
            )
        _require_sha256(row.get("sha256"), name="success artifact sha256")
        inventory_paths.append(path)
        inventory_bytes += size
    if inventory_bytes > MAXIMUM_ARTIFACT_BYTES:
        raise DevelopmentCheckpointRefusal("final artifact exceeds 2 GiB")
    if (
        inventory_paths != sorted(inventory_paths)
        or len(inventory_paths) != len(set(inventory_paths))
        or receipt.get("artifact_bytes_before_receipt") != inventory_bytes
        or receipt.get("artifact_inventory_sha256")
        != _artifact_inventory_sha256(inventory)
    ):
        raise DevelopmentCheckpointRefusal("success artifact inventory differs")
    inventory_by_path = {row["path"]: row for row in inventory}
    if inventory_by_path.get(RETAINED_FREEZE_FILE_NAME, {}).get(
        "sha256"
    ) != receipt.get("freeze_sha256") or inventory_by_path.get(
        RETAINED_RUNNER_TEST_FILE_NAME, {}
    ).get(
        "sha256"
    ) != receipt.get(
        "runner_test_sha256"
    ):
        raise DevelopmentCheckpointRefusal(
            "success inventory omits retained authorization evidence"
        )
    return receipt


def _revalidate_durable_success(
    workspace_root: Path,
    artifact_root: Path,
    receipt: Mapping[str, object],
    *,
    timeout: float = 600.0,
) -> None:
    checked = _validate_success_receipt(receipt)
    _require_saved_json_equals(artifact_root / "success-receipt.json", checked)
    capsule = artifact_root / CAPSULE_DIRECTORY_NAME
    retained_freeze_payload = _read_regular_bytes(
        artifact_root / RETAINED_FREEZE_FILE_NAME, maximum=_MAXIMUM_JSON_BYTES
    )
    retained_test_payload = _read_regular_bytes(
        artifact_root / RETAINED_RUNNER_TEST_FILE_NAME,
        maximum=64 * 1024 * 1024,
    )
    if (
        _sha256_bytes(retained_freeze_payload) != checked["freeze_sha256"]
        or _sha256_bytes(retained_test_payload) != checked["runner_test_sha256"]
    ):
        raise DevelopmentCheckpointRefusal(
            "retained authorization evidence differs from receipt"
        )
    retained_freeze = _parse_json_object(retained_freeze_payload)
    _validate_retained_authorized_freeze(retained_freeze, receipt=checked)
    manifest = _read_json(artifact_root / "capsule-source-manifest.json")
    if manifest.get("manifest_sha256") != checked["capsule_manifest_sha256"]:
        raise DevelopmentCheckpointRefusal(
            "durable capsule manifest differs from receipt"
        )
    _verify_capsule_source_manifest(capsule, manifest)
    runner_rows = [
        row
        for row in manifest["files"]
        if type(row) is dict and row.get("path") == RUNNER_RELATIVE_PATH
    ]
    if (
        len(runner_rows) != 1
        or runner_rows[0].get("sha256") != checked["runner_source_sha256"]
    ):
        raise DevelopmentCheckpointRefusal(
            "retained capsule runner differs from receipt"
        )
    probe = _read_json(artifact_root / "runtime-preflight.json")
    inner = checked["inner_success"]
    binding = {
        "source_manifest_sha256": inner["source_manifest_sha256"],
        "training_configuration_sha256": inner["training_configuration_sha256"],
    }
    _validate_runtime_probe(probe, binding=binding)
    if (
        _sha256_bytes(_canonical_json_bytes(probe))
        != checked["runtime_preflight_sha256"]
    ):
        raise DevelopmentCheckpointRefusal("durable runtime preflight differs")
    permit = _validate_self_digested_record(
        _read_json(artifact_root / "execution-permit.json"),
        field="permit_sha256",
        name="execution permit",
    )
    if (
        set(permit) != _ISSUED_PERMIT_FIELDS
        or permit.get("schema") != "heterodiff-a1-development-single-use-permit-v1"
        or permit.get("lane_id") != LANE_ID
        or permit.get("state") != "ISSUED"
        or permit.get("coordinate")
        != {"seed": SEED, "budget": BUDGET, "method": METHOD}
        or permit.get("permit_sha256") != checked["execution_permit_sha256"]
        or permit.get("freeze_sha256") != checked["freeze_sha256"]
        or permit.get("runner_source_sha256") != checked["runner_source_sha256"]
        or permit.get("runner_test_sha256") != checked["runner_test_sha256"]
        or permit.get("capsule_manifest_sha256") != checked["capsule_manifest_sha256"]
        or permit.get("runtime_preflight_sha256") != checked["runtime_preflight_sha256"]
        or permit.get("one_attempt") is not True
        or permit.get("retry_or_replacement_permitted") is not False
        or permit.get("confirmatory_or_production_authority") is not False
    ):
        raise DevelopmentCheckpointRefusal("durable execution permit differs")
    attempt = _validate_self_digested_record(
        _read_json(artifact_root / "attempt.json"),
        field="record_sha256",
        name="attempt",
    )
    if (
        set(attempt) != _ATTEMPT_FIELDS
        or attempt.get("schema") != "heterodiff-a1-development-attempt-v1"
        or attempt.get("lane_id") != LANE_ID
        or attempt.get("state") != "PREPARED"
        or attempt.get("coordinate")
        != {"seed": SEED, "budget": BUDGET, "method": METHOD}
        or attempt.get("freeze_sha256") != checked["freeze_sha256"]
        or attempt.get("capsule_manifest_sha256") != checked["capsule_manifest_sha256"]
        or attempt.get("runtime_preflight_sha256")
        != checked["runtime_preflight_sha256"]
        or attempt.get("execution_permit_sha256") != checked["execution_permit_sha256"]
        or attempt.get("retry_permitted") is not False
        or attempt.get("replacement_permitted") is not False
    ):
        raise DevelopmentCheckpointRefusal("durable attempt record differs")
    consumption = _validate_permit_consumption(
        _read_json(artifact_root / "execution-permit-consumption.json"),
        permit=permit,
    )
    if (
        consumption.get("record_sha256")
        != checked["execution_permit_consumption_sha256"]
    ):
        raise DevelopmentCheckpointRefusal("durable permit consumption differs")
    outcome_linkage = _validate_outcome_linkage(
        _read_json(artifact_root / "execution-outcome-linkage.json"),
        consumption=consumption,
        inner=inner,
    )
    if (
        outcome_linkage.get("record_sha256")
        != checked["execution_outcome_linkage_sha256"]
    ):
        raise DevelopmentCheckpointRefusal("durable outcome linkage differs")
    expected_inventory = checked["artifact_inventory_before_receipt"]
    observed_inventory = list(
        _artifact_inventory(
            artifact_root, exclude_relative_paths=("success-receipt.json",)
        )
    )
    if observed_inventory != expected_inventory:
        raise DevelopmentCheckpointRefusal("durable artifact inventory differs")
    python = _target_python(workspace_root)
    fresh = _run_json_subprocess(
        (
            str(python),
            "-P",
            "-m",
            "heterodiff.experiments.finite_association_development_checkpoint_runner",
            "--verify-inner-success",
        ),
        cwd=capsule,
        environment=_capsule_python_environment(capsule),
        timeout=timeout,
    )
    if fresh != inner:
        raise DevelopmentCheckpointRefusal(
            "fresh inner verification differs from the success receipt"
        )
    if (
        list(
            _artifact_inventory(
                artifact_root, exclude_relative_paths=("success-receipt.json",)
            )
        )
        != expected_inventory
    ):
        raise DevelopmentCheckpointRefusal(
            "fresh inner verification mutated durable evidence"
        )
    _require_saved_json_equals(artifact_root / "success-receipt.json", checked)


def execute_development_checkpoint() -> Dict[str, object]:
    root = _workspace_root()
    artifacts = _require_safe_artifacts_directory(root, create=True)
    if artifacts is None:  # pragma: no cover - create=True is exhaustive
        raise DevelopmentCheckpointRefusal("artifacts directory is absent")
    artifact_root = development_artifact_root(root)
    if _lexists(artifact_root):
        raise DevelopmentCheckpointRefusal(
            "development attempt already exists; retry is forbidden"
        )
    _require_forbidden_outputs_absent(root)
    started_unix_ns = time.time_ns()
    deadline = time.monotonic() + MAXIMUM_WALL_SECONDS
    freeze = _require_authorized_freeze(root)
    root_bindings = _root_binding_snapshot(root)
    current_freeze_payload = _read_regular_bytes(
        root / FREEZE_RELATIVE_PATH, maximum=_MAXIMUM_JSON_BYTES
    )
    implementation_binding = freeze["implementation_binding"]
    if (
        _parse_json_object(current_freeze_payload) != freeze
        or _sha256_bytes(current_freeze_payload) != root_bindings["freeze_sha256"]
        or implementation_binding.get("runner_source_sha256")
        != root_bindings["runner_source_sha256"]
        or implementation_binding.get("runner_test_sha256")
        != root_bindings["runner_test_sha256"]
    ):
        raise DevelopmentCheckpointRefusal(
            "authorized freeze or bound implementation changed during preflight"
        )
    python = _target_python(root)
    temporary = Path(tempfile.mkdtemp(prefix=".a1-development-", dir=str(artifacts)))
    published = False
    process = None
    child_wait_completed = False
    gate_read_fd = None
    gate_write_fd = None
    try:
        _retain_authorization_evidence(root, temporary, bindings=root_bindings)
        capsule = temporary / CAPSULE_DIRECTORY_NAME
        capsule.mkdir()
        manifest = _copy_capsule(root, capsule)
        _atomic_write_json(temporary / "capsule-source-manifest.json", manifest)
        probe_command = (
            str(python),
            "-P",
            "-m",
            "heterodiff.experiments.finite_association_development_checkpoint_runner",
            "--probe-capsule",
        )
        capsule_environment = _capsule_python_environment(capsule)
        probe = _run_json_subprocess(
            probe_command,
            cwd=capsule,
            environment=capsule_environment,
            timeout=_remaining_timeout(deadline, maximum=600),
        )
        binding = freeze["implementation_binding"]
        _validate_runtime_probe(probe, binding=binding)
        _atomic_write_json(temporary / "runtime-preflight.json", probe)
        _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
        permit: Dict[str, object] = {
            "schema": "heterodiff-a1-development-single-use-permit-v1",
            "lane_id": LANE_ID,
            "state": "ISSUED",
            "coordinate": {"seed": SEED, "budget": BUDGET, "method": METHOD},
            "issued_unix_ns": time.time_ns(),
            "freeze_sha256": root_bindings["freeze_sha256"],
            "runner_source_sha256": root_bindings["runner_source_sha256"],
            "runner_test_sha256": root_bindings["runner_test_sha256"],
            "capsule_manifest_sha256": manifest["manifest_sha256"],
            "runtime_preflight_sha256": _sha256_bytes(_canonical_json_bytes(probe)),
            "one_attempt": True,
            "retry_or_replacement_permitted": False,
            "confirmatory_or_production_authority": False,
        }
        permit["permit_sha256"] = _sha256_bytes(_canonical_json_bytes(permit))
        _atomic_write_json(temporary / "execution-permit.json", permit)
        prepared = {
            "schema": "heterodiff-a1-development-attempt-v1",
            "lane_id": LANE_ID,
            "state": "PREPARED",
            "started_unix_ns": started_unix_ns,
            "coordinate": {"seed": SEED, "budget": BUDGET, "method": METHOD},
            "freeze_sha256": root_bindings["freeze_sha256"],
            "capsule_manifest_sha256": manifest["manifest_sha256"],
            "runtime_preflight_sha256": _sha256_bytes(_canonical_json_bytes(probe)),
            "execution_permit_sha256": permit["permit_sha256"],
            "retry_permitted": False,
            "replacement_permitted": False,
        }
        prepared["record_sha256"] = _sha256_bytes(_canonical_json_bytes(prepared))
        _atomic_write_json(temporary / "attempt.json", prepared)
        _tree_size(temporary)
        _require_forbidden_outputs_absent(root)
        os.replace(temporary, artifact_root)
        published = True
        _fsync_directory(artifacts)
        if artifact_root.is_symlink() or not artifact_root.is_dir():
            raise DevelopmentCheckpointRefusal(
                "published development attempt root is unsafe"
            )
        capsule = artifact_root / CAPSULE_DIRECTORY_NAME
        capsule_environment = _capsule_python_environment(capsule)
        command = (
            str(python),
            "-P",
            "-c",
            _ISOLATED_RUNNER_GATE_BOOTSTRAP,
            "--execute-learner",
            "--seed",
            str(SEED),
            "--budget",
            str(BUDGET),
            "--method",
            METHOD,
        )
        stdout_path = artifact_root / "inner-run.stdout"
        stderr_path = artifact_root / "inner-run.stderr"
        timed_out = False
        with open(stdout_path, "xb") as stdout_handle, open(
            stderr_path, "xb"
        ) as stderr_handle:
            _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
            gate_read_fd, gate_write_fd = os.pipe()
            worker_environment = dict(capsule_environment)
            worker_environment[_LAUNCH_GATE_ENVIRONMENT_NAME] = str(gate_read_fd)
            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(capsule),
                    env=worker_environment,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    start_new_session=True,
                    pass_fds=(gate_read_fd,),
                )
                consumption = {
                    "schema": "heterodiff-a1-development-permit-consumption-v1",
                    "lane_id": LANE_ID,
                    "state": "CONSUMED_LAUNCHED",
                    "coordinate": {
                        "seed": SEED,
                        "budget": BUDGET,
                        "method": METHOD,
                    },
                    "issued_permit_sha256": permit["permit_sha256"],
                    "launch_gate_protocol": "PIPE_EOF_FAIL_CLOSED_V1",
                    "launch_gate_token_sha256": _LAUNCH_GATE_TOKEN_SHA256,
                    "outer_sampled_runner_process_id": process.pid,
                    "launched_unix_ns": time.time_ns(),
                }
                consumption["record_sha256"] = _sha256_bytes(
                    _canonical_json_bytes(consumption)
                )
                _validate_permit_consumption(consumption, permit=permit)
                _atomic_write_json(
                    artifact_root / "execution-permit-consumption.json",
                    consumption,
                )
                written = os.write(gate_write_fd, _LAUNCH_GATE_TOKEN)
                if written != len(_LAUNCH_GATE_TOKEN):
                    raise DevelopmentCheckpointRefusal(
                        "development launch gate write was incomplete"
                    )
                os.close(gate_write_fd)
                gate_write_fd = None
                os.close(gate_read_fd)
                gate_read_fd = None
            except BaseException:
                for descriptor in (gate_write_fd, gate_read_fd):
                    if descriptor is not None:
                        try:
                            os.close(descriptor)
                        except OSError:
                            pass
                gate_write_fd = None
                gate_read_fd = None
                if process is not None:
                    _terminate_process_group(process)
                    child_wait_completed = True
                raise
            returncode, timed_out = _wait_for_child_with_limits(
                process, artifact_root=artifact_root, deadline=deadline
            )
            child_wait_completed = True
        if timed_out or returncode != 0:
            _tree_size(artifact_root)
            _require_saved_json_equals(
                artifact_root / "capsule-source-manifest.json", manifest
            )
            _require_saved_json_equals(artifact_root / "runtime-preflight.json", probe)
            _require_saved_json_equals(artifact_root / "execution-permit.json", permit)
            _require_saved_json_equals(artifact_root / "attempt.json", prepared)
            _verify_capsule_source_manifest(capsule, manifest)
            terminal = _terminal_record(
                state="TIMEOUT" if timed_out else "FAILURE",
                started_unix_ns=started_unix_ns,
                detail="inner sampled runner did not complete successfully",
                returncode=returncode,
                custody=_terminal_custody(artifact_root),
                boundary_drift=_boundary_drift(root, expected_bindings=root_bindings),
            )
            _atomic_write_json(artifact_root / "failure-receipt.json", terminal)
            return terminal
        verify = _run_json_subprocess(
            (
                str(python),
                "-P",
                "-m",
                "heterodiff.experiments.finite_association_development_checkpoint_runner",
                "--verify-inner-success",
            ),
            cwd=capsule,
            environment=capsule_environment,
            timeout=_remaining_timeout(deadline, maximum=600),
        )
        probe_preflight = probe.get("preflight")
        if (
            type(probe_preflight) is not dict
            or verify.get("optimizer_steps_taken") != EXPECTED_UPDATES
            or verify.get("fixture_sha256") != TARGET_FIXTURE_SHA256
            or verify.get("source_manifest_sha256") != binding["source_manifest_sha256"]
            or verify.get("training_configuration_sha256")
            != binding["training_configuration_sha256"]
            or verify.get("parent_confirmed_zero_child_exit") is not True
            or verify.get("inner_scientific_decision_eligible") is not False
            or process is None
            or verify.get("worker_parent_process_id") != process.pid
            or any(
                verify.get(name) != probe_preflight.get(name)
                for name in (
                    "preflight_sha256",
                    "dataset_sha256",
                    "batch_schedule_sha256",
                    "initial_parameter_sha256",
                )
            )
            or float(verify.get("certified_maximum_absolute_correction", 21.0)) > 20.0
            or int(verify.get("process_peak_rss_bytes", MAXIMUM_PEAK_RSS_BYTES + 1))
            > MAXIMUM_PEAK_RSS_BYTES
        ):
            terminal = _terminal_record(
                state="REFUSED",
                started_unix_ns=started_unix_ns,
                detail="inner SUCCESS failed the development acceptance contract",
                returncode=returncode,
                custody=_terminal_custody(artifact_root),
                boundary_drift=_boundary_drift(root, expected_bindings=root_bindings),
            )
            _atomic_write_json(artifact_root / "failure-receipt.json", terminal)
            return terminal
        outcome_linkage: Dict[str, object] = {
            "schema": "heterodiff-a1-development-outcome-linkage-v1",
            "lane_id": LANE_ID,
            "state": "ACCEPTED_SUCCESS_LINKAGE",
            "coordinate": {"seed": SEED, "budget": BUDGET, "method": METHOD},
            "permit_consumption_sha256": consumption["record_sha256"],
            "outer_sampled_runner_process_id": process.pid,
            "outer_child_returncode": returncode,
            "inner_launch_authorization_sha256": verify["launch_authorization_sha256"],
            "inner_launch_receipt_sha256": verify["launch_receipt_sha256"],
            "worker_session_sha256": verify["worker_session_sha256"],
            "worker_process_identity_sha256": verify["worker_process_identity_sha256"],
            "worker_process_id": verify["worker_process_id"],
            "worker_parent_process_id": verify["worker_parent_process_id"],
            "linked_unix_ns": time.time_ns(),
        }
        outcome_linkage["record_sha256"] = _sha256_bytes(
            _canonical_json_bytes(outcome_linkage)
        )
        _validate_outcome_linkage(
            outcome_linkage, consumption=consumption, inner=verify
        )
        _atomic_write_json(
            artifact_root / "execution-outcome-linkage.json", outcome_linkage
        )
        _require_saved_json_equals(
            artifact_root / "capsule-source-manifest.json", manifest
        )
        _require_saved_json_equals(artifact_root / "runtime-preflight.json", probe)
        _require_saved_json_equals(artifact_root / "execution-permit.json", permit)
        _require_saved_json_equals(artifact_root / "attempt.json", prepared)
        _require_retained_authorization_evidence(artifact_root, bindings=root_bindings)
        _verify_capsule_source_manifest(capsule, manifest)
        _require_unchanged_root_bindings(root, root_bindings)
        _require_forbidden_outputs_absent(root)
        _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
        inventory = list(_artifact_inventory(artifact_root))
        _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
        _require_retained_authorization_evidence(artifact_root, bindings=root_bindings)
        _verify_capsule_source_manifest(capsule, manifest)
        _require_unchanged_root_bindings(root, root_bindings)
        _require_forbidden_outputs_absent(root)
        artifact_bytes = sum(int(row["bytes"]) for row in inventory)
        receipt: Dict[str, object] = {
            "schema": RECEIPT_SCHEMA_VERSION,
            "lane_id": LANE_ID,
            "state": "SUCCESS_DEVELOPMENT_CHECKPOINT",
            "started_unix_ns": started_unix_ns,
            "finished_unix_ns": time.time_ns(),
            "coordinate": {"seed": SEED, "budget": BUDGET, "method": METHOD},
            "freeze_sha256": root_bindings["freeze_sha256"],
            "retained_authorized_freeze_sha256": root_bindings["freeze_sha256"],
            "retained_runner_test_sha256": root_bindings["runner_test_sha256"],
            "runner_source_sha256": root_bindings["runner_source_sha256"],
            "runner_test_sha256": root_bindings["runner_test_sha256"],
            "capsule_manifest_sha256": manifest["manifest_sha256"],
            "runtime_preflight_sha256": _sha256_bytes(_canonical_json_bytes(probe)),
            "execution_permit_sha256": permit["permit_sha256"],
            "execution_permit_consumption_sha256": consumption["record_sha256"],
            "execution_outcome_linkage_sha256": outcome_linkage["record_sha256"],
            "artifact_bytes_before_receipt": artifact_bytes,
            "artifact_inventory_before_receipt": inventory,
            "artifact_inventory_sha256": _artifact_inventory_sha256(inventory),
            "inner_success": verify,
            "retry_permitted": False,
            "replacement_permitted": False,
            "scientific_result_eligible": False,
            "production_order_admissible": False,
            "confirmatory_execution": False,
            "qualifies_r1": False,
            "qualifies_r2": False,
            "closes_c17": False,
            "claim_promotion": False,
            "real_domain_test_accessed": False,
        }
        receipt["receipt_sha256"] = _sha256_bytes(_canonical_json_bytes(receipt))
        _validate_success_receipt(receipt)
        receipt_payload = _canonical_json_bytes(receipt)
        if artifact_bytes + len(receipt_payload) > MAXIMUM_ARTIFACT_BYTES:
            raise DevelopmentCheckpointRefusal("final artifact exceeds 2 GiB")
        _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
        _require_unchanged_root_bindings(root, root_bindings)
        _require_forbidden_outputs_absent(root)
        _atomic_write_json(artifact_root / "success-receipt.json", receipt)
        _revalidate_durable_success(
            root,
            artifact_root,
            receipt,
            timeout=_remaining_timeout(deadline, maximum=600),
        )
        _remaining_timeout(deadline, maximum=MAXIMUM_WALL_SECONDS)
        _require_unchanged_root_bindings(root, root_bindings)
        _require_forbidden_outputs_absent(root)
        return receipt
    except BaseException as error:
        for descriptor in (gate_write_fd, gate_read_fd):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if process is not None and not child_wait_completed:
            try:
                _terminate_process_group(process)
            except BaseException:
                pass
        if not published:
            shutil.rmtree(temporary, ignore_errors=True)
        else:
            failure_path = artifact_root / "failure-receipt.json"
            if not _lexists(failure_path):
                state = (
                    "REFUSED"
                    if isinstance(error, DevelopmentCheckpointRefusal)
                    else "INTERRUPTED"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "FAILURE"
                )
                terminal = _terminal_record(
                    state=state,
                    started_unix_ns=started_unix_ns,
                    detail="%s: %s" % (type(error).__name__, error),
                    returncode=None,
                    custody=_terminal_custody(artifact_root),
                    boundary_drift=_boundary_drift(
                        root, expected_bindings=root_bindings
                    ),
                )
                try:
                    _atomic_write_json(failure_path, terminal)
                except Exception:
                    pass
        raise


def development_checkpoint_status() -> Dict[str, object]:
    workspace = _workspace_root()
    artifacts = _require_safe_artifacts_directory(workspace, create=False)
    if artifacts is None:
        return {
            "lane_id": LANE_ID,
            "state": "NOT_STARTED",
            "retry_permitted": False,
            "replacement_permitted": False,
        }
    root = development_artifact_root(workspace)
    if not _lexists(root):
        return {
            "lane_id": LANE_ID,
            "state": "NOT_STARTED",
            "retry_permitted": False,
            "replacement_permitted": False,
        }
    if root.is_symlink() or not root.is_dir():
        raise DevelopmentCheckpointRefusal(
            "development attempt root is redirected or not a directory"
        )
    success = root / "success-receipt.json"
    failure = root / "failure-receipt.json"
    if success.is_file() and not failure.exists():
        receipt = _validate_success_receipt(_read_json(success))
        _revalidate_durable_success(workspace, root, receipt)
        return receipt
    if failure.is_file() and not success.exists():
        return _validate_terminal_receipt(_read_json(failure))
    return {
        "lane_id": LANE_ID,
        "state": "INCOMPLETE_OR_CONFLICTING_ATTEMPT",
        "retry_permitted": False,
        "replacement_permitted": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute or inspect one frozen A1 development checkpoint."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-development-checkpoint", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--probe-capsule", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument(
        "--verify-inner-success", action="store_true", help=argparse.SUPPRESS
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.probe_capsule:
        print(_canonical_json_bytes(_probe_current_capsule()).decode("ascii"))
        return 0
    if arguments.verify_inner_success:
        print(_canonical_json_bytes(_verify_inner_success()).decode("ascii"))
        return 0
    if arguments.status:
        print(_canonical_json_bytes(development_checkpoint_status()).decode("ascii"))
        return 0
    result = execute_development_checkpoint()
    print(_canonical_json_bytes(result).decode("ascii"))
    return 0 if result.get("state") == "SUCCESS_DEVELOPMENT_CHECKPOINT" else 1


if __name__ == "__main__":  # pragma: no cover - explicit execution only
    raise SystemExit(main())


__all__ = [
    "ARTIFACT_RELATIVE_PATH",
    "BUDGET",
    "DevelopmentCheckpointRefusal",
    "EXPECTED_UPDATES",
    "LANE_ID",
    "MAXIMUM_ARTIFACT_BYTES",
    "MAXIMUM_PEAK_RSS_BYTES",
    "MAXIMUM_WALL_SECONDS",
    "METHOD",
    "SCHEMA_VERSION",
    "SEED",
    "development_artifact_root",
    "development_checkpoint_status",
    "execute_development_checkpoint",
    "main",
]
