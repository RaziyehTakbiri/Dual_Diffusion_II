"""Production custody core for the frozen finite-association campaign.

This module is intentionally separate from ``finite_association_execution_order``.
The latter is a ``TEST_ONLY_NO_RUN`` state-machine exercise; none of its plans,
events, or receipts are accepted here.  This production core performs no rank
calculation, learner execution, metric evaluation, or scientific decision.

Scientific state transitions will be added only as phase-specific binders that
reopen canonical typed evidence.  There is deliberately no public function that
accepts an opaque evidence digest and advances this ledger.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import secrets
import stat
import sys
from types import MappingProxyType
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

from heterodiff.experiments import finite_association_runtime_attestor as runtime_attestor
from heterodiff.experiments import finite_association_runtime_identity as runtime_identity


AUTHORITY_DOMAIN = "A1_FINITE_ASSOCIATION_PRODUCTION_ORDER_V1"
ARTIFACT_DIRECTORY_NAME = "a1_finite_association_production_order_v1"
ARTIFACT_RELATIVE_PATH = "artifacts/" + ARTIFACT_DIRECTORY_NAME
PLAN_FILE_NAME = "plan.json"
EVENT_DIRECTORY_NAME = "events"
AUTHORIZATION_DIRECTORY_NAME = "authorizations"
COORDINATE_PERMIT_DIRECTORY_NAME = "coordinate_permits"
PREREQUISITE_DIRECTORY_NAME = "prerequisite"
PREREQUISITE_RECEIPT_FILE_NAME = "prerequisite-receipt.json"
LOCK_FILE_NAME = ".ledger.lock"

PLAN_SCHEMA = "heterodiff-a1-finite-association-production-order-plan-v2"
EVENT_SCHEMA = "heterodiff-a1-finite-association-production-order-event-v1"
AUTHORIZATION_SCHEMA = (
    "heterodiff-a1-finite-association-production-phase-authorization-v2"
)
AUTHORIZATION_CONSUMPTION_SCHEMA = (
    "heterodiff-a1-finite-association-production-phase-consumption-v2"
)
COORDINATE_PERMIT_SCHEMA = (
    "heterodiff-a1-finite-association-production-coordinate-permit-v1"
)
COORDINATE_CONSUMPTION_SCHEMA = (
    "heterodiff-a1-finite-association-production-coordinate-consumption-v1"
)
ARTIFACT_IDENTITY_SCHEMA = (
    "heterodiff-a1-finite-association-production-artifact-identity-v1"
)
RUNTIME_OBSERVATION_SCHEMA = "heterodiff-a1-production-runtime-observation-v1"
PRODUCTION_RUNTIME_CONTRACT_SCHEMA_V2 = (
    "heterodiff-a1-production-runtime-contract-v2"
)
RUNTIME_IDENTITY_REFERENCE_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-reference-v2"
)
PREREQUISITE_RECEIPT_SCHEMA_V2 = (
    "heterodiff-a1-production-prerequisite-receipt-v2"
)
PREREQUISITE_EVIDENCE_TYPE_V2 = "FROZEN_PREREQUISITE_V2"
PREREQUISITE_OPERATION_V2 = runtime_attestor.ATTESTED_PREREQUISITE_OPERATION
PREREQUISITE_REVALIDATION_OPERATION_V2 = (
    runtime_attestor.REVALIDATE_PREREQUISITE_OPERATION
)
PRODUCTION_SOURCE_MANIFEST_SCHEMA = (
    "heterodiff-a1-production-source-manifest-v1"
)

MAXIMUM_PLAN_BYTES = 2 * 1024 * 1024
MAXIMUM_EVENT_BYTES = 256 * 1024
MAXIMUM_RECEIPT_BYTES = 8 * 1024 * 1024
_PENDING_FILE_PREFIX = ".pending-uncommitted-"
_PENDING_NONCE_HEX_LENGTH = 32

PAIRED_SEEDS = (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
EXACT_METHODS = ("direct", "guided", "strong_direct")
SAMPLE_BUDGETS = (512, 4096, 32768)
PRIMARY_METHODS = ("direct", "guided")
CONTROL_METHODS = ("strong_direct", "guide_input", "mismatch")

EXACT_COORDINATES = tuple(
    (seed, method) for seed in PAIRED_SEEDS for method in EXACT_METHODS
)
PRIMARY_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in PRIMARY_METHODS
)
CONTROL_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in CONTROL_METHODS
)
COMPLETE_SAMPLED_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in PRIMARY_METHODS + CONTROL_METHODS
)

_FROZEN_PREREQUISITE_DIGESTS = (
    "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
    "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
    "09273f6bcee7c1a09165392e6ecf0125157b747d242c1f993a982ce3b2833cc7",
    "d6326ffb38c4c3ccf5aed1002f8cbd75fe5411f60d07172d5511730a63daba45",
    "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
)
_PREREQUISITE_RESULT_FIELD_NAMES = (
    "generator_digest",
    "observation_digest",
    "population_digest",
    "guide_digest",
    "split_digest",
    "generator_row_sum_residual",
    "association_determinant",
    "ambiguous_permanent",
    "clean_overflow_minimum",
    "clean_overflow_maximum",
    "density_minimum",
    "density_maximum",
    "terminal_guide_log_error",
    "maximum_terminal_residual",
    "maximum_retained_initial_residual",
    "maximum_overall_initial_residual",
    "joint_weighted_initial_absolute_residual",
    "initial_overflow_probability",
    "retained_weighted_residual_share",
    "immigrant_terminal_mean",
    "immigrant_anchor_intensity",
    "target_harmonicity_residual",
    "guide_rank_propagation_residual",
    "correction_scale_ratio",
    "pair_partition_sizes",
    "passed",
    "failures",
)

ORDERED_STATES = (
    "NEW",
    "PREREQUISITE_VERIFIED",
    "RANK_AUTHORIZED",
    "RANK_RUNNING",
    "RANK_VERIFIED",
    "EXACT_AUTHORIZED",
    "EXACT_RUNNING",
    "EXACT_AGGREGATED",
    "PRIMARY_AUTHORIZED",
    "PRIMARY_RUNNING",
    "PRIMARY_SUCCESS_SET",
    "PRIMARY_METRICS_AUTHORIZED",
    "PRIMARY_METRICS_RUNNING",
    "PRIMARY_METRICS_COMMITTED",
    "CONTROLS_AUTHORIZED",
    "CONTROLS_RUNNING",
    "SAMPLED_SUCCESS_SET",
    "SAMPLED_AGGREGATED",
    "DECISION_AUTHORIZED",
    "DECISION_RUNNING",
    "DECISION_CANDIDATE",
    "AUDIT_AUTHORIZED",
    "AUDIT_RUNNING",
    "AUDIT_VERIFIED",
    "FINALIZATION_AUTHORIZED",
    "FINALIZED",
)
TERMINAL_STATES = ("HOLD", "FAILURE")
AUTHORIZATION_STATES = (
    "RANK_AUTHORIZED",
    "EXACT_AUTHORIZED",
    "PRIMARY_AUTHORIZED",
    "PRIMARY_METRICS_AUTHORIZED",
    "CONTROLS_AUTHORIZED",
    "DECISION_AUTHORIZED",
    "AUDIT_AUTHORIZED",
    "FINALIZATION_AUTHORIZED",
)
COORDINATE_PHASES = ("EXACT", "PRIMARY", "CONTROLS")
_COORDINATES_BY_PHASE = {
    "EXACT": EXACT_COORDINATES,
    "PRIMARY": PRIMARY_COORDINATES,
    "CONTROLS": CONTROL_COORDINATES,
}
_PHASE_AUTHORIZED_STATE = {
    "EXACT": "EXACT_AUTHORIZED",
    "PRIMARY": "PRIMARY_AUTHORIZED",
    "CONTROLS": "CONTROLS_AUTHORIZED",
}
_PHASE_RUNNING_STATE = {
    "EXACT": "EXACT_RUNNING",
    "PRIMARY": "PRIMARY_RUNNING",
    "CONTROLS": "CONTROLS_RUNNING",
}

SPECIFICATION_SOURCE_PATH = (
    "research/62_a1_association_guided_residual_falsification_spec.md"
)
_REQUIRED_NONPACKAGE_SOURCE_PATHS = (
    "pyproject.toml",
    "requirements/m1-reference-macos-arm64-py311.lock",
    SPECIFICATION_SOURCE_PATH,
)
_PREEXISTING_PRODUCTION_OUTPUTS = (
    "artifacts/a1_rank_stress_gate_v1.json",
    "artifacts/a1_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_exact_population_campaign_v4",
    "artifacts/a1_campaign_v4",
    "artifacts/a1_primary_metrics_v1",
    "artifacts/a1_primary_metrics_v2",
    "artifacts/a1_candidate_decision_v1",
    "artifacts/a1_independent_audit_v1",
    "artifacts/a1_publication_decision_v1",
)
NON_HOSTILE_HOST_THREAT_MODEL = (
    "Local non-hostile host with fail-closed accidental/stale/torn/replay "
    "custody; not a defense against a malicious account that can rewrite "
    "the workspace, process memory, or kernel state."
)

_SNAPSHOT_KEY = object()
_AUTHORIZATION_KEY = object()
_CONSUMPTION_KEY = object()
_COORDINATE_PERMIT_KEY = object()
_COORDINATE_CONSUMPTION_KEY = object()
_PREREQUISITE_KEY = object()

_EVIDENCE_TRANSITIONS = {
    PREREQUISITE_EVIDENCE_TYPE_V2: (
        "NEW",
        "PREREQUISITE_VERIFIED",
        None,
    ),
    "RANK_PHASE_OPENED_V1": (
        "PREREQUISITE_VERIFIED",
        "RANK_AUTHORIZED",
        None,
    ),
}
_SCIENTIFIC_EVIDENCE_TYPES = frozenset(_EVIDENCE_TRANSITIONS)


def _plain_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json_value(item) for item in value]
    return value


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
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


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _require_sha256(value: object, *, name: str) -> str:
    if not _is_sha256(value):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _frozen_prerequisite_fixture_sha256() -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-association-fixture-v1\0")
    for value in _FROZEN_PREREQUISITE_DIGESTS:
        digest.update(value.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_attested_prerequisite_payload(
    payload: object,
) -> Dict[str, Any]:
    """Require the exact frozen result identity without importing numerics."""

    if type(payload) is not dict:
        raise ValueError("attested prerequisite payload must be an exact object")
    checked = dict(payload)
    if (
        set(checked) != {"schema", "class_module", "class_name", "fields"}
        or checked.get("schema") != runtime_attestor.TYPED_PREREQUISITE_SCHEMA
        or checked.get("class_module")
        != (
            "heterodiff.experiments."
            "finite_association_guided_residual_pilot"
        )
        or checked.get("class_name")
        != "AssociationResidualPrerequisiteResult"
        or type(checked.get("fields")) is not list
    ):
        raise ValueError("attested prerequisite payload identity is invalid")
    rows = checked["fields"]
    if tuple(
        row.get("name") if type(row) is dict else None for row in rows
    ) != _PREREQUISITE_RESULT_FIELD_NAMES:
        raise ValueError("attested prerequisite fields are not frozen")
    by_name = {row["name"]: row["value"] for row in rows}
    for name, expected in zip(
        _PREREQUISITE_RESULT_FIELD_NAMES[:5],
        _FROZEN_PREREQUISITE_DIGESTS,
    ):
        if by_name[name] != {"kind": "scalar", "value": expected}:
            raise ValueError("attested prerequisite digest fields changed")
    if by_name["passed"] != {"kind": "scalar", "value": True}:
        raise ValueError("attested prerequisite did not pass")
    if by_name["failures"] != {"kind": "string-tuple", "value": []}:
        raise ValueError("attested prerequisite contains failures")
    return checked


def _deep_freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _frozen_runtime_contract_record() -> Dict[str, Any]:
    return {
        "schema": "heterodiff-a1-production-runtime-contract-v1",
        "python": "3.11.5",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "torch": "2.12.1",
        "threadpoolctl": "3.6.0",
        "cpu_only": True,
        "accelerators_hidden": True,
        "deterministic_algorithms": True,
        "thread_environment": {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
        },
        "native_pool_contract": {
            "minimum_discovered_pool_count": 1,
            "every_discovered_pool_thread_count": 1,
        },
        "numpy_build_configuration_nonempty": True,
        "host_identity_contract": {
            "platform": True,
            "system": True,
            "release": True,
            "machine": True,
            "processor": True,
        },
    }


FROZEN_RUNTIME_CONTRACT = _deep_freeze(_frozen_runtime_contract_record())


def frozen_production_runtime_contract_sha256() -> str:
    """Return the legacy metric-process contract digest.

    Primary-metric custody predates the target-process attestor and still
    names this exact v1 contract.  Production-order plans use the separately
    bound v2 contract below; retaining this helper avoids silently relabeling
    historical metric receipts as process-attested evidence.
    """

    return _sha256_json(_frozen_runtime_contract_record())


def _production_runtime_contract_v2_record(
    *,
    source_manifest_sha256: str,
    environment_lock_sha256: str,
    runtime_identity_manifest_sha256: str,
    minimum_macos_version: str,
) -> Dict[str, Any]:
    """Build the plan-specific target-process contract without probing a host."""

    for name, value in (
        ("source_manifest_sha256", source_manifest_sha256),
        ("environment_lock_sha256", environment_lock_sha256),
        ("runtime_identity_manifest_sha256", runtime_identity_manifest_sha256),
    ):
        _require_sha256(value, name=name)
    # The request and target-manifest reference carry the three plan-specific
    # digests above.  The subprocess module owns the exact static v2 runtime
    # contract; duplicating that schema here would create two authorities.
    return runtime_attestor.frozen_runtime_contract_v2(
        source_manifest_sha256=source_manifest_sha256,
        environment_lock_sha256=environment_lock_sha256,
        runtime_identity_manifest_sha256=runtime_identity_manifest_sha256,
        minimum_macos_version=minimum_macos_version,
    )


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError("source path must be a nonempty NUL-free string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError("source path must be normalized workspace-relative POSIX")
    return value


def _require_nonsymlink_source_ancestors(
    workspace_root: Path, path: Path
) -> Path:
    """Keep source custody on a lexical, non-symlinked workspace path."""

    root = Path(os.path.abspath(os.fspath(workspace_root)))
    candidate = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("production source escaped the workspace") from error
    root_status = root.lstat()
    if stat.S_ISLNK(root_status.st_mode) or not stat.S_ISDIR(
        root_status.st_mode
    ):
        raise ValueError("production source workspace is not a regular directory")
    current = root
    for component in relative.parts[:-1]:
        current = current / component
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise ValueError(
                "production source custody ancestors must not be symlinks"
            )
        if not stat.S_ISDIR(status.st_mode):
            raise ValueError(
                "production source custody ancestor is not a directory"
            )
    return candidate


def _sha256_file(path: Path, maximum_bytes: int) -> Tuple[str, int]:
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode):
        raise ValueError("source path is not a regular file: %s" % path)
    if status.st_size > maximum_bytes:
        raise ValueError("source path exceeds its byte limit: %s" % path)
    digest = hashlib.sha256()
    consumed = 0
    descriptor = os.open(
        os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            status.st_dev,
            status.st_ino,
            status.st_size,
            status.st_mtime_ns,
        ):
            raise RuntimeError("source path identity changed while opening: %s" % path)
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                consumed += len(block)
                if consumed > maximum_bytes:
                    raise ValueError("source path grew beyond its byte limit")
                digest.update(block)
    finally:
        os.close(descriptor)
    after = path.lstat()
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
        raise RuntimeError("source path changed while hashing: %s" % path)
    return digest.hexdigest(), consumed


@dataclass(frozen=True)
class SourcePathIdentity:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _relative_path(self.path)
        _require_sha256(self.sha256, name="source sha256")
        if isinstance(self.size_bytes, bool) or type(self.size_bytes) is not int:
            raise TypeError("source size must be an integer")
        if self.size_bytes < 0:
            raise ValueError("source size must be nonnegative")


def _discover_source_paths(workspace_root: Path) -> Tuple[str, ...]:
    source_root = workspace_root / "src" / "heterodiff"
    _require_nonsymlink_source_ancestors(workspace_root, source_root)
    try:
        status = source_root.lstat()
    except FileNotFoundError as error:
        raise ValueError("workspace lacks src/heterodiff") from error
    if not stat.S_ISDIR(status.st_mode):
        raise ValueError("src/heterodiff is not a regular directory")
    discovered = []
    for path in source_root.rglob("*"):
        path_status = path.lstat()
        if stat.S_ISLNK(path_status.st_mode):
            raise ValueError("Python source closure contains a symlink")
        if stat.S_ISDIR(path_status.st_mode):
            continue
        if path.suffix == ".py":
            if not stat.S_ISREG(path_status.st_mode):
                raise ValueError(
                    "Python source closure contains a nonregular path"
                )
            discovered.append(path.relative_to(workspace_root).as_posix())
    paths = tuple(sorted(set(discovered).union(_REQUIRED_NONPACKAGE_SOURCE_PATHS)))
    if not paths:
        raise ValueError("production source closure is empty")
    for relative in paths:
        _relative_path(relative)
        path = workspace_root / relative
        _require_nonsymlink_source_ancestors(workspace_root, path)
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("required production source is not regular: %s" % relative)
    return paths


_MODULE_WORKSPACE_ROOT = Path(__file__).resolve(strict=True).parents[3]
DEFAULT_SOURCE_PATHS = _discover_source_paths(_MODULE_WORKSPACE_ROOT)


def source_path_identity(
    workspace_root: os.PathLike, relative_path: str
) -> SourcePathIdentity:
    root = Path(workspace_root).resolve(strict=True)
    relative = _relative_path(relative_path)
    path = _require_nonsymlink_source_ancestors(root, root / relative)
    digest, size = _sha256_file(path, MAXIMUM_PLAN_BYTES * 16)
    _require_nonsymlink_source_ancestors(root, path)
    return SourcePathIdentity(relative, digest, size)


def frozen_production_source_manifest(
    workspace_root: os.PathLike,
) -> Dict[str, Any]:
    """Return the complete, identity-checked executable source manifest."""

    root = Path(workspace_root).resolve(strict=True)
    paths = _discover_source_paths(root)
    identities = [
        source_path_identity(root, relative).__dict__ for relative in paths
    ]
    if _discover_source_paths(root) != paths:
        raise RuntimeError("production source closure changed while hashing")
    body = {
        "schema": PRODUCTION_SOURCE_MANIFEST_SCHEMA,
        "files": identities,
    }
    manifest = dict(body)
    manifest["source_manifest_sha256"] = _sha256_json(identities)
    return manifest


def canonical_artifact_directory(workspace_root: os.PathLike) -> Path:
    root = Path(workspace_root).resolve(strict=True)
    return root / ARTIFACT_RELATIVE_PATH


def _artifact_identity(workspace_root: Path) -> Dict[str, str]:
    resolved = canonical_artifact_directory(workspace_root)
    body = {
        "schema": ARTIFACT_IDENTITY_SCHEMA,
        "relative_path": ARTIFACT_RELATIVE_PATH,
        "resolved_path_sha256": hashlib.sha256(
            os.fspath(resolved).encode("utf-8")
        ).hexdigest(),
    }
    value = dict(body)
    value["identity_sha256"] = _sha256_json(body)
    return value


def _coordinate_payload() -> Dict[str, Any]:
    return {
        "exact": [list(value) for value in EXACT_COORDINATES],
        "primary": [list(value) for value in PRIMARY_COORDINATES],
        "controls": [list(value) for value in CONTROL_COORDINATES],
        "complete_sampled": [list(value) for value in COMPLETE_SAMPLED_COORDINATES],
    }


def _coordinate_manifest_sha256(phase: str) -> str:
    if phase not in COORDINATE_PHASES:
        raise ValueError("coordinate phase is not frozen")
    return _sha256_json(
        {
            "schema": "heterodiff-a1-production-%s-coordinate-manifest-v1"
            % phase.lower(),
            "coordinates": [list(value) for value in _COORDINATES_BY_PHASE[phase]],
        }
    )


def _preexisting_output_status(workspace_root: Path) -> Tuple[str, ...]:
    present = []
    for relative in _PREEXISTING_PRODUCTION_OUTPUTS:
        path = workspace_root / relative
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        present.append(relative)
    return tuple(present)


def _workspace_runtime_identity_manifest(
    workspace_root: Path,
) -> runtime_identity.RuntimeIdentityManifest:
    """Structurally bind the fixed target manifest; never grant launch here."""

    root = Path(workspace_root).resolve(strict=True)
    return runtime_identity.load_runtime_identity_manifest(
        root / runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
        lockfile_path=root / runtime_identity.LOCKFILE_RELATIVE_PATH,
    )


def _runtime_identity_reference(
    manifest: runtime_identity.RuntimeIdentityManifest,
) -> Dict[str, Any]:
    if type(manifest) is not runtime_identity.RuntimeIdentityManifest:
        raise TypeError("runtime identity reference requires a loaded manifest")
    record = manifest.record
    component_names = (
        "profile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
    )
    distribution_projection = []
    for index, raw_distribution in enumerate(record["distributions"]):
        distribution = _plain_json_value(raw_distribution)
        metadata_files = distribution["metadata_files"]
        origin = os.path.dirname(metadata_files[0]["path"])
        if not origin or any(
            os.path.dirname(metadata_file["path"]) != origin
            for metadata_file in metadata_files
        ):
            raise ValueError(
                "runtime distribution %d metadata files lack one origin"
                % index
            )
        distribution_projection.append(
            {
                "name": distribution["name"],
                "version": distribution["version"],
                "origin": origin,
                "metadata_files": metadata_files,
            }
        )
    return {
        "schema": RUNTIME_IDENTITY_REFERENCE_SCHEMA,
        "relative_path": runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
        "manifest_schema": record["schema"],
        "manifest_sha256": manifest.manifest_sha256,
        "environment_lock_sha256": record["lockfile"]["sha256"],
        "component_sha256": {
            name: _sha256_json(record[name]) for name in component_names
        },
        "runtime_projection_sha256": {
            "distributions": _sha256_json(distribution_projection),
        },
        "approved": manifest.approved,
    }


def _plan_body(workspace_root: Path, sources: Sequence[str]) -> Dict[str, Any]:
    manifest = frozen_production_source_manifest(workspace_root)
    identities = manifest["files"]
    if tuple(item["path"] for item in identities) != tuple(sources):
        raise RuntimeError("production source discovery changed during planning")
    identity_manifest = _workspace_runtime_identity_manifest(workspace_root)
    identity_reference = _runtime_identity_reference(identity_manifest)
    lock_identity = next(
        item
        for item in identities
        if item["path"] == runtime_identity.LOCKFILE_RELATIVE_PATH
    )
    if (
        lock_identity["sha256"]
        != identity_reference["environment_lock_sha256"]
    ):
        raise RuntimeError(
            "production source lock and runtime identity manifest disagree"
        )
    runtime_contract = _production_runtime_contract_v2_record(
        source_manifest_sha256=manifest["source_manifest_sha256"],
        environment_lock_sha256=identity_reference[
            "environment_lock_sha256"
        ],
        runtime_identity_manifest_sha256=identity_reference[
            "manifest_sha256"
        ],
        minimum_macos_version=identity_manifest.record["profile"][
            "minimum_macos_version"
        ],
    )
    artifact_identity = _artifact_identity(workspace_root)
    return {
        "schema": PLAN_SCHEMA,
        "authority_domain": AUTHORITY_DOMAIN,
        "artifact_directory_name": ARTIFACT_DIRECTORY_NAME,
        "artifact_identity": artifact_identity,
        "campaign_instance_nonce_sha256": hashlib.sha256(
            secrets.token_bytes(32)
        ).hexdigest(),
        "coordinates": _coordinate_payload(),
        "coordinate_manifest_sha256": {
            phase.lower(): _coordinate_manifest_sha256(phase)
            for phase in COORDINATE_PHASES
        },
        "ordered_states": list(ORDERED_STATES),
        "terminal_states": list(TERMINAL_STATES),
        "authorization_states": list(AUTHORIZATION_STATES),
        "runtime_contract": runtime_contract,
        "runtime_identity_manifest": identity_reference,
        "source_paths": identities,
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "specification": next(
            item for item in identities if item["path"] == SPECIFICATION_SOURCE_PATH
        ),
        "preexisting_output_policy": {
            "schema": "heterodiff-a1-production-preexisting-output-policy-v1",
            "must_be_absent_at_initialization": list(
                _PREEXISTING_PRODUCTION_OUTPUTS
            ),
        },
        "threat_model": NON_HOSTILE_HOST_THREAT_MODEL,
        "production_order_authority": True,
        "production_execution_authority": False,
        "runner_integration_complete": False,
        "test_only_no_run": False,
        "opaque_evidence_admission_allowed": False,
    }


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(os.fspath(directory), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory_durable(directory: Path) -> None:
    missing = []
    current = directory
    while True:
        try:
            status = current.lstat()
        except FileNotFoundError:
            missing.append(current)
            parent = current.parent
            if parent == current:
                raise ValueError("cannot find a durable parent directory")
            current = parent
            continue
        if not stat.S_ISDIR(status.st_mode):
            raise ValueError("custody path is not a regular directory")
        break
    for path in reversed(missing):
        path.mkdir()
        _fsync_directory(path.parent)


def _is_pending_file_name(name: str) -> bool:
    if not name.startswith(_PENDING_FILE_PREFIX):
        return False
    suffix = name[len(_PENDING_FILE_PREFIX) :]
    return len(suffix) == _PENDING_NONCE_HEX_LENGTH and all(
        character in "0123456789abcdef" for character in suffix
    )


def _new_pending_file(parent: Path) -> Tuple[int, Path]:
    for _ in range(128):
        path = parent / (_PENDING_FILE_PREFIX + secrets.token_hex(16))
        try:
            descriptor = os.open(
                os.fspath(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except FileExistsError:
            continue
        return descriptor, path
    raise RuntimeError("could not allocate an exclusive pending record")


def _atomic_exclusive_json(path: Path, value: Mapping[str, Any]) -> None:
    _ensure_directory_durable(path.parent)
    payload = _canonical_json(value)
    descriptor, pending = _new_pending_file(path.parent)
    linked = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(os.fspath(pending), os.fspath(path), follow_symlinks=False)
        linked = True
        _fsync_directory(path.parent)
    finally:
        try:
            pending.unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(path.parent)
    if not linked:
        raise RuntimeError("exclusive record publication did not complete")


def _reconcile_pending_directory(directory: Path) -> None:
    try:
        status = directory.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(status.st_mode):
        raise ValueError("custody path is not a regular directory")
    for path in tuple(directory.iterdir()):
        if not path.name.startswith(_PENDING_FILE_PREFIX):
            continue
        if not _is_pending_file_name(path.name):
            raise ValueError("malformed pending custody filename")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("pending custody path is not a regular file")
        path.unlink()
        _fsync_directory(directory)


def _reconcile_pending_entries(directory: Path) -> None:
    _reconcile_pending_directory(directory)
    for child in (
        directory / EVENT_DIRECTORY_NAME,
        directory / AUTHORIZATION_DIRECTORY_NAME,
        directory / COORDINATE_PERMIT_DIRECTORY_NAME,
        directory / PREREQUISITE_DIRECTORY_NAME,
    ):
        _reconcile_pending_directory(child)
    permits = directory / COORDINATE_PERMIT_DIRECTORY_NAME
    try:
        if stat.S_ISDIR(permits.lstat().st_mode):
            for phase in permits.iterdir():
                _reconcile_pending_directory(phase)
    except FileNotFoundError:
        pass


def _absolute_without_symlink_resolution(path: os.PathLike) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _require_production_artifact_directory(directory: Path) -> Path:
    candidate = _absolute_without_symlink_resolution(directory)
    if (
        candidate.name != ARTIFACT_DIRECTORY_NAME
        or candidate.parent.name != "artifacts"
    ):
        raise ValueError("production ledger is outside its canonical directory")
    for path in (candidate.parent.parent, candidate.parent, candidate):
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise ValueError(
                "production artifact custody ancestors must not be symlinks"
            )
        if not stat.S_ISDIR(status.st_mode):
            raise ValueError(
                "production artifact path is not a regular directory"
            )
    return candidate


@contextmanager
def _locked_artifact_directory(
    directory: Path, *, create: bool = False
) -> Iterator[None]:
    if type(create) is not bool:
        raise TypeError("create must be boolean")
    directory = _require_production_artifact_directory(directory)
    lock_path = directory / LOCK_FILE_NAME
    try:
        lock_status = lock_path.lstat()
    except FileNotFoundError:
        lock_status = None
    else:
        if not stat.S_ISREG(lock_status.st_mode):
            raise ValueError("production lock path is not a regular file")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if lock_status is None:
        if not create:
            raise ValueError("production lock is absent")
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | nofollow
    else:
        flags = os.O_RDWR | nofollow
    descriptor = os.open(os.fspath(lock_path), flags, 0o600)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("opened production lock is not a regular file")
        if lock_status is not None and (
            lock_status.st_dev,
            lock_status.st_ino,
        ) != (opened.st_dev, opened.st_ino):
            raise ValueError("production lock identity changed while opening")
        current = lock_path.lstat()
        if not stat.S_ISREG(current.st_mode) or (
            current.st_dev,
            current.st_ino,
        ) != (opened.st_dev, opened.st_ino):
            raise ValueError("production lock identity changed while opening")
        if lock_status is None:
            os.fsync(descriptor)
            _fsync_directory(directory)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        acquired = lock_path.lstat()
        if not stat.S_ISREG(acquired.st_mode) or (
            acquired.st_dev,
            acquired.st_ino,
        ) != (opened.st_dev, opened.st_ino):
            raise ValueError("production lock changed while acquiring")
        _reconcile_pending_entries(directory)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _read_json_bounded(path: Path, maximum_bytes: int) -> Dict[str, Any]:
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode):
        raise ValueError("custody record is not a regular file")
    if status.st_size <= 0 or status.st_size > maximum_bytes:
        raise ValueError("custody record has an invalid byte length")
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
            status.st_dev,
            status.st_ino,
            status.st_size,
            status.st_mtime_ns,
        ):
            raise RuntimeError("custody record identity changed while opening")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(maximum_bytes + 1)
    finally:
        os.close(descriptor)
    if len(payload) > maximum_bytes:
        raise ValueError("custody record exceeds its byte limit")
    after = path.lstat()
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
        raise RuntimeError("custody record changed while reading")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("custody record is not canonical JSON") from error
    if type(value) is not dict or payload != _canonical_json(value):
        raise ValueError("custody record bytes are not canonical")
    return value


class ProductionOrderSnapshot:
    __slots__ = (
        "_artifact_directory",
        "_plan",
        "_state",
        "_head_event_sha256",
        "_event_count",
        "_coordinate_progress",
        "_locked",
    )

    def __init__(
        self,
        construction_key: object,
        artifact_directory: Path,
        plan: Mapping[str, Any],
        state: str,
        head_event_sha256: str,
        event_count: int,
        coordinate_progress: Mapping[str, int],
    ) -> None:
        if construction_key is not _SNAPSHOT_KEY:
            raise TypeError("production snapshots come only from the canonical loader")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_plan", _deep_freeze(dict(plan)))
        object.__setattr__(self, "_state", state)
        object.__setattr__(self, "_head_event_sha256", head_event_sha256)
        object.__setattr__(self, "_event_count", event_count)
        object.__setattr__(
            self, "_coordinate_progress", _deep_freeze(dict(coordinate_progress))
        )
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("production snapshot is immutable")
        object.__setattr__(self, name, value)

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def plan(self) -> Mapping[str, Any]:
        return self._plan

    @property
    def state(self) -> str:
        return self._state

    @property
    def plan_sha256(self) -> str:
        return self._plan["plan_sha256"]

    @property
    def campaign_instance_nonce_sha256(self) -> str:
        return self._plan["campaign_instance_nonce_sha256"]

    @property
    def head_event_sha256(self) -> str:
        return self._head_event_sha256

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def coordinate_progress(self) -> Mapping[str, int]:
        return self._coordinate_progress


class ProductionVerifiedPrerequisite:
    """Loader-only binding of a fresh prerequisite recomputation to one plan."""

    __slots__ = ("_snapshot", "_record", "_locked")

    def __init__(
        self,
        construction_key: object,
        snapshot: ProductionOrderSnapshot,
        record: Mapping[str, Any],
    ) -> None:
        if construction_key is not _PREREQUISITE_KEY:
            raise TypeError("production prerequisite evidence comes only from its binder")
        if type(snapshot) is not ProductionOrderSnapshot:
            raise TypeError("prerequisite evidence requires a production snapshot")
        checked = _validate_prerequisite_receipt_record(record, snapshot.plan)
        object.__setattr__(self, "_snapshot", snapshot)
        object.__setattr__(self, "_record", _deep_freeze(checked))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("production prerequisite evidence is immutable")
        object.__setattr__(self, name, value)

    @property
    def snapshot(self) -> ProductionOrderSnapshot:
        return self._snapshot

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    @property
    def receipt_sha256(self) -> str:
        return self._record["receipt_sha256"]


def _validate_prerequisite_receipt_record(
    record: Mapping[str, Any], plan: Mapping[str, Any]
) -> Dict[str, Any]:
    checked = dict(record)
    required = {
        "schema",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "source_manifest_sha256",
        "runtime_contract_sha256",
        "runtime_identity_manifest_sha256",
        "runtime_identity_components_sha256",
        "specification_sha256",
        "attestor_envelope",
        "attestor_envelope_sha256",
        "pre_runtime_observation_sha256",
        "post_runtime_observation_sha256",
        "stable_runtime_sha256",
        "typed_prerequisite_result_sha256",
        "fixture_sha256",
        "passed",
        "receipt_sha256",
    }
    if set(checked) != required:
        raise ValueError("production prerequisite receipt schema is invalid")
    body = dict(checked)
    claimed = _require_sha256(
        body.pop("receipt_sha256", None), name="prerequisite receipt"
    )
    identity_reference_value = plan.get("runtime_identity_manifest")
    identity_reference = (
        _plain_json_value(identity_reference_value)
        if isinstance(identity_reference_value, Mapping)
        else None
    )
    if (
        checked["schema"] != PREREQUISITE_RECEIPT_SCHEMA_V2
        or checked["passed"] is not True
        or checked["plan_sha256"] != plan["plan_sha256"]
        or checked["campaign_instance_nonce_sha256"]
        != plan["campaign_instance_nonce_sha256"]
        or checked["source_manifest_sha256"]
        != plan["source_manifest_sha256"]
        or checked["runtime_contract_sha256"]
        != _sha256_json(plan["runtime_contract"])
        or type(identity_reference) is not dict
        or identity_reference.get("approved") is not True
        or checked["runtime_identity_manifest_sha256"]
        != identity_reference.get("manifest_sha256")
        or checked["runtime_identity_components_sha256"]
        != _sha256_json(identity_reference.get("component_sha256"))
        or checked["specification_sha256"] != plan["specification"]["sha256"]
        or _sha256_json(body) != claimed
    ):
        raise ValueError("production prerequisite receipt is inconsistent")
    for name in (
        "runtime_identity_manifest_sha256",
        "runtime_identity_components_sha256",
        "attestor_envelope_sha256",
        "pre_runtime_observation_sha256",
        "post_runtime_observation_sha256",
        "stable_runtime_sha256",
        "typed_prerequisite_result_sha256",
        "fixture_sha256",
    ):
        _require_sha256(checked[name], name=name)
    envelope = runtime_attestor.validate_runtime_attestor_envelope(
        checked["attestor_envelope"], plan=plan
    )
    pre = envelope["pre_observation"]
    post = envelope["post_observation"]
    request = runtime_attestor.runtime_attestor_request_from_observation(pre)
    expected_attestor_source_sha256 = next(
        (
            row["sha256"]
            for row in plan["source_paths"]
            if row["path"] == runtime_attestor.ATTESTOR_SOURCE_RELATIVE_PATH
        ),
        None,
    )
    payload = _validate_attested_prerequisite_payload(
        envelope["typed_prerequisite_result"]
    )
    if (
        request["operation"] != PREREQUISITE_OPERATION_V2
        or request["attestor_source_sha256"]
        != expected_attestor_source_sha256
        or envelope["envelope_sha256"]
        != checked["attestor_envelope_sha256"]
        or pre["observation_sha256"]
        != checked["pre_runtime_observation_sha256"]
        or post["observation_sha256"]
        != checked["post_runtime_observation_sha256"]
        or pre["stable_runtime_sha256"]
        != checked["stable_runtime_sha256"]
        or post["stable_runtime_sha256"]
        != checked["stable_runtime_sha256"]
        or envelope["typed_prerequisite_result_sha256"]
        != checked["typed_prerequisite_result_sha256"]
        or _sha256_json(payload)
        != checked["typed_prerequisite_result_sha256"]
        or checked["fixture_sha256"]
        != _frozen_prerequisite_fixture_sha256()
    ):
        raise ValueError("production prerequisite receipt is inconsistent")
    return checked


def _prerequisite_receipt_path(directory: Path) -> Path:
    return (
        directory
        / PREREQUISITE_DIRECTORY_NAME
        / PREREQUISITE_RECEIPT_FILE_NAME
    )


def _load_optional_prerequisite_receipt_locked(
    directory: Path, plan: Mapping[str, Any]
) -> Optional[Dict[str, Any]]:
    path = _prerequisite_receipt_path(directory)
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    record = _read_json_bounded(path, MAXIMUM_RECEIPT_BYTES)
    return _validate_prerequisite_receipt_record(record, plan)


def _load_prerequisite_receipt_locked(
    directory: Path, plan: Mapping[str, Any]
) -> Dict[str, Any]:
    record = _load_optional_prerequisite_receipt_locked(directory, plan)
    if record is None:
        raise FileNotFoundError("production prerequisite receipt is absent")
    return record


def _persist_prerequisite_receipt_locked(
    directory: Path,
    plan: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    checked = _validate_prerequisite_receipt_record(receipt, plan)
    if len(_canonical_json(checked)) > MAXIMUM_RECEIPT_BYTES:
        raise ValueError("production prerequisite receipt exceeds its byte limit")
    existing = _load_optional_prerequisite_receipt_locked(directory, plan)
    if existing is not None:
        if existing != checked:
            raise FileExistsError(
                "a different production prerequisite receipt already exists"
            )
        return existing
    path = _prerequisite_receipt_path(directory)
    _atomic_exclusive_json(path, checked)
    committed = _load_prerequisite_receipt_locked(directory, plan)
    if committed != checked:
        raise RuntimeError("production prerequisite receipt changed on publication")
    return committed


def _prerequisite_predecessor_receipts_sha256(
    plan: Mapping[str, Any], receipt: Mapping[str, Any]
) -> str:
    checked = _validate_prerequisite_receipt_record(receipt, plan)
    return _sha256_json(
        {
            "schema": (
                "heterodiff-a1-production-prerequisite-predecessors-v2"
            ),
            "plan_sha256": plan["plan_sha256"],
            "campaign_instance_nonce_sha256": plan[
                "campaign_instance_nonce_sha256"
            ],
            "source_manifest_sha256": checked["source_manifest_sha256"],
            "runtime_contract_sha256": checked["runtime_contract_sha256"],
            "runtime_identity_manifest_sha256": checked[
                "runtime_identity_manifest_sha256"
            ],
            "runtime_identity_components_sha256": checked[
                "runtime_identity_components_sha256"
            ],
            "specification_sha256": checked["specification_sha256"],
            "attestor_envelope_sha256": checked[
                "attestor_envelope_sha256"
            ],
            "pre_runtime_observation_sha256": checked[
                "pre_runtime_observation_sha256"
            ],
            "post_runtime_observation_sha256": checked[
                "post_runtime_observation_sha256"
            ],
            "stable_runtime_sha256": checked["stable_runtime_sha256"],
            "typed_prerequisite_result_sha256": checked[
                "typed_prerequisite_result_sha256"
            ],
            "fixture_sha256": checked["fixture_sha256"],
        }
    )


def _validate_coordinates(value: object) -> None:
    expected = _coordinate_payload()
    if value != expected:
        raise ValueError("production coordinate manifests are not frozen")


def _validate_plan(
    plan: Mapping[str, Any],
    expected_paths: Sequence[str],
    expected_runtime_identity: Mapping[str, Any],
    expected_minimum_macos_version: str,
) -> None:
    required = {
        "schema",
        "authority_domain",
        "artifact_directory_name",
        "artifact_identity",
        "campaign_instance_nonce_sha256",
        "coordinates",
        "coordinate_manifest_sha256",
        "ordered_states",
        "terminal_states",
        "authorization_states",
        "runtime_contract",
        "runtime_identity_manifest",
        "source_paths",
        "source_manifest_sha256",
        "specification",
        "preexisting_output_policy",
        "threat_model",
        "production_order_authority",
        "production_execution_authority",
        "runner_integration_complete",
        "test_only_no_run",
        "opaque_evidence_admission_allowed",
        "plan_sha256",
    }
    if type(plan) is not dict or set(plan) != required:
        raise ValueError("production plan schema is invalid")
    body = dict(plan)
    claimed = _require_sha256(body.pop("plan_sha256", None), name="plan_sha256")
    if _sha256_json(body) != claimed or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("production plan digest/schema is invalid")
    if (
        plan.get("authority_domain") != AUTHORITY_DOMAIN
        or plan.get("production_order_authority") is not True
        or plan.get("production_execution_authority") is not False
        or plan.get("runner_integration_complete") is not False
        or plan.get("test_only_no_run") is not False
        or plan.get("opaque_evidence_admission_allowed") is not False
    ):
        raise ValueError("production authority flags are invalid")
    if plan.get("artifact_directory_name") != ARTIFACT_DIRECTORY_NAME:
        raise ValueError("production artifact directory identity is invalid")
    _validate_coordinates(plan.get("coordinates"))
    expected_manifests = {
        phase.lower(): _coordinate_manifest_sha256(phase)
        for phase in COORDINATE_PHASES
    }
    if plan.get("coordinate_manifest_sha256") != expected_manifests:
        raise ValueError("coordinate manifest digests are invalid")
    if (
        plan.get("ordered_states") != list(ORDERED_STATES)
        or plan.get("terminal_states") != list(TERMINAL_STATES)
        or plan.get("authorization_states") != list(AUTHORIZATION_STATES)
        or plan.get("threat_model") != NON_HOSTILE_HOST_THREAT_MODEL
    ):
        raise ValueError("production plan contract is invalid")
    if not _is_sha256(plan.get("campaign_instance_nonce_sha256")):
        raise ValueError("campaign-instance nonce digest is invalid")
    identities = plan.get("source_paths")
    if type(identities) is not list or [
        item.get("path") if type(item) is dict else None for item in identities
    ] != list(expected_paths):
        raise ValueError("production source manifest paths/order are invalid")
    parsed = [SourcePathIdentity(**item) for item in identities]
    if _sha256_json(identities) != plan.get("source_manifest_sha256"):
        raise ValueError("production source manifest digest is invalid")
    identity_reference = plan.get("runtime_identity_manifest")
    if (
        type(identity_reference) is not dict
        or identity_reference != dict(expected_runtime_identity)
        or set(identity_reference)
        != {
            "schema",
            "relative_path",
            "manifest_schema",
            "manifest_sha256",
            "environment_lock_sha256",
            "component_sha256",
            "runtime_projection_sha256",
            "approved",
        }
        or identity_reference.get("schema")
        != RUNTIME_IDENTITY_REFERENCE_SCHEMA
        or identity_reference.get("relative_path")
        != runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
        or identity_reference.get("manifest_schema")
        != runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA
        or type(identity_reference.get("approved")) is not bool
    ):
        raise ValueError("production runtime identity binding is invalid")
    for name in ("manifest_sha256", "environment_lock_sha256"):
        _require_sha256(identity_reference.get(name), name=name)
    component_names = {
        "profile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
    }
    components = identity_reference.get("component_sha256")
    if type(components) is not dict or set(components) != component_names:
        raise ValueError("production runtime component bindings are invalid")
    for name, value in components.items():
        _require_sha256(value, name="runtime identity component %s" % name)
    runtime_projection = identity_reference.get(
        "runtime_projection_sha256"
    )
    if type(runtime_projection) is not dict or set(runtime_projection) != {
        "distributions"
    }:
        raise ValueError("production runtime projection bindings are invalid")
    _require_sha256(
        runtime_projection["distributions"],
        name="runtime distribution projection",
    )
    expected_runtime_contract = _production_runtime_contract_v2_record(
        source_manifest_sha256=plan["source_manifest_sha256"],
        environment_lock_sha256=identity_reference[
            "environment_lock_sha256"
        ],
        runtime_identity_manifest_sha256=identity_reference[
            "manifest_sha256"
        ],
        minimum_macos_version=expected_minimum_macos_version,
    )
    if plan.get("runtime_contract") != expected_runtime_contract:
        raise ValueError("production target-runtime contract is invalid")
    specification = next(
        item for item in identities if item["path"] == SPECIFICATION_SOURCE_PATH
    )
    if plan.get("specification") != specification:
        raise ValueError("production specification identity is invalid")
    artifact = plan.get("artifact_identity")
    if type(artifact) is not dict:
        raise ValueError("production artifact identity is absent")
    artifact_body = dict(artifact)
    artifact_claimed = _require_sha256(
        artifact_body.pop("identity_sha256", None), name="artifact identity"
    )
    if (
        artifact.get("schema") != ARTIFACT_IDENTITY_SCHEMA
        or artifact.get("relative_path") != ARTIFACT_RELATIVE_PATH
        or not _is_sha256(artifact.get("resolved_path_sha256"))
        or _sha256_json(artifact_body) != artifact_claimed
    ):
        raise ValueError("production artifact identity is invalid")
    policy = plan.get("preexisting_output_policy")
    if policy != {
        "schema": "heterodiff-a1-production-preexisting-output-policy-v1",
        "must_be_absent_at_initialization": list(_PREEXISTING_PRODUCTION_OUTPUTS),
    }:
        raise ValueError("preexisting-output policy is invalid")
    del parsed


def initialize_production_order_plan(
    workspace_root: os.PathLike,
) -> ProductionOrderSnapshot:
    """Create the production plan only when every compute artifact is absent."""

    root = Path(workspace_root).resolve(strict=True)
    present = _preexisting_output_status(root)
    if present:
        raise FileExistsError(
            "production initialization rejects preexisting outputs: %s"
            % ", ".join(present)
        )
    source_paths = _discover_source_paths(root)
    directory = canonical_artifact_directory(root)
    try:
        directory.lstat()
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError("production order artifact already exists")
    _ensure_directory_durable(directory.parent)
    directory.mkdir()
    _fsync_directory(directory.parent)
    try:
        body = _plan_body(root, source_paths)
        plan = dict(body)
        plan["plan_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(directory / PLAN_FILE_NAME, plan)
        with _locked_artifact_directory(directory, create=True):
            return _load_snapshot_locked(directory)
    except BaseException:
        # Never remove a visible production directory here: an interrupted
        # initialization is evidence requiring operator inspection.
        raise


def _transition_allowed(from_state: str, to_state: str) -> bool:
    if from_state in TERMINAL_STATES or from_state == "FINALIZED":
        return False
    if to_state in TERMINAL_STATES:
        return True
    if from_state not in ORDERED_STATES or to_state not in ORDERED_STATES:
        return False
    return ORDERED_STATES.index(to_state) == ORDERED_STATES.index(from_state) + 1


def _event_path(directory: Path, ordinal: int) -> Path:
    return directory / EVENT_DIRECTORY_NAME / ("%012d.json" % ordinal)


def _validate_event(
    event: Mapping[str, Any],
    *,
    plan_sha256: str,
    expected_ordinal: int,
    previous_sha256: str,
    current_state: str,
) -> Tuple[str, Dict[str, int]]:
    required = {
        "schema",
        "ordinal",
        "plan_sha256",
        "previous_event_sha256",
        "from_state",
        "to_state",
        "event_kind",
        "evidence",
        "timestamp_utc",
        "authority_domain",
        "event_sha256",
    }
    if type(event) is not dict or set(event) != required:
        raise ValueError("production event schema is invalid")
    body = dict(event)
    claimed = _require_sha256(
        body.pop("event_sha256", None), name="event_sha256"
    )
    if _sha256_json(body) != claimed:
        raise ValueError("production event digest is invalid")
    if (
        event.get("schema") != EVENT_SCHEMA
        or event.get("ordinal") != expected_ordinal
        or event.get("plan_sha256") != plan_sha256
        or event.get("previous_event_sha256") != previous_sha256
        or event.get("from_state") != current_state
        or event.get("authority_domain") != AUTHORITY_DOMAIN
    ):
        raise ValueError("production event chain is invalid")
    try:
        datetime.strptime(event["timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("production event timestamp is invalid") from error
    kind = event.get("event_kind")
    evidence = event.get("evidence")
    if kind == "TERMINALIZED":
        if event["to_state"] not in TERMINAL_STATES or type(evidence) is not dict:
            raise ValueError("terminal production event is invalid")
        if set(evidence) != {"reason_code", "detail"}:
            raise ValueError("terminal evidence schema is invalid")
        if (
            type(evidence["reason_code"]) is not str
            or not evidence["reason_code"]
            or type(evidence["detail"]) is not str
            or not evidence["detail"]
        ):
            raise ValueError("terminal evidence contents are invalid")
        if not _transition_allowed(current_state, event["to_state"]):
            raise ValueError("terminal production transition is forbidden")
        return claimed, {phase: 0 for phase in COORDINATE_PHASES}
    # Scientific events are intentionally recognized but cannot be emitted by
    # any public generic writer.  Phase-specific binders must supply this exact
    # sealed schema after reopening canonical typed evidence.
    if kind != "CANONICAL_EVIDENCE_COMMITTED" or type(evidence) is not dict:
        raise ValueError("production event kind is not recognized")
    expected_evidence = {
        "evidence_type",
        "canonical_loader_receipt_sha256",
        "predecessor_receipts_sha256",
        "phase",
        "coordinate_ordinal",
        "coordinate_consumption_sha256",
    }
    if set(evidence) != expected_evidence:
        raise ValueError("canonical production evidence schema is invalid")
    if evidence["evidence_type"] not in _SCIENTIFIC_EVIDENCE_TYPES:
        raise ValueError("canonical production evidence type is invalid")
    for name in (
        "canonical_loader_receipt_sha256",
        "predecessor_receipts_sha256",
    ):
        _require_sha256(evidence[name], name=name)
    phase = evidence["phase"]
    ordinal = evidence["coordinate_ordinal"]
    consumption = evidence["coordinate_consumption_sha256"]
    progress = {value: 0 for value in COORDINATE_PHASES}
    expected_from, expected_to, expected_phase = _EVIDENCE_TRANSITIONS[
        evidence["evidence_type"]
    ]
    if (
        current_state != expected_from
        or event["to_state"] != expected_to
        or phase != expected_phase
    ):
        raise ValueError("canonical evidence type has the wrong transition")
    if phase is None:
        if ordinal is not None or consumption is not None:
            raise ValueError("non-coordinate evidence claims coordinate custody")
    else:
        if phase not in COORDINATE_PHASES:
            raise ValueError("production evidence phase is invalid")
        if isinstance(ordinal, bool) or type(ordinal) is not int or ordinal < 0:
            raise ValueError("production evidence coordinate ordinal is invalid")
        if ordinal >= len(_COORDINATES_BY_PHASE[phase]):
            raise ValueError("production evidence coordinate ordinal is out of range")
        _require_sha256(consumption, name="coordinate consumption")
        progress[phase] = ordinal + 1
    if not _transition_allowed(current_state, event["to_state"]):
        # Same-state coordinate completion is permitted only while a phase is
        # already running.  Exact progress is reconstructed below by the loader.
        if not (
            event["to_state"] == current_state
            and phase in COORDINATE_PHASES
            and current_state == _PHASE_RUNNING_STATE[phase]
        ):
            raise ValueError("canonical production transition is forbidden")
    return claimed, progress


def _load_snapshot_locked(directory: Path) -> ProductionOrderSnapshot:
    directory = _require_production_artifact_directory(directory)
    workspace_root = directory.parent.parent
    expected_paths = _discover_source_paths(workspace_root)
    identity_manifest = _workspace_runtime_identity_manifest(workspace_root)
    expected_runtime_identity = _runtime_identity_reference(identity_manifest)
    plan = _read_json_bounded(directory / PLAN_FILE_NAME, MAXIMUM_PLAN_BYTES)
    _validate_plan(
        plan,
        expected_paths,
        expected_runtime_identity,
        identity_manifest.record["profile"]["minimum_macos_version"],
    )
    if plan["artifact_identity"] != _artifact_identity(workspace_root):
        raise ValueError("production artifact identity changed")
    current_sources = [
        source_path_identity(workspace_root, value).__dict__
        for value in expected_paths
    ]
    if current_sources != plan["source_paths"]:
        raise ValueError("production source identities are stale")
    events_directory = directory / EVENT_DIRECTORY_NAME
    try:
        status = events_directory.lstat()
    except FileNotFoundError:
        paths = []
    else:
        if not stat.S_ISDIR(status.st_mode):
            raise ValueError("production event path is not a regular directory")
        paths = sorted(events_directory.iterdir(), key=lambda value: value.name)
    if len(paths) > 1024:
        raise ValueError("production event ledger exceeds its frozen bound")
    state = "NEW"
    previous = "0" * 64
    progress = {phase: 0 for phase in COORDINATE_PHASES}
    prerequisite_event = None
    rank_open_event = None
    for ordinal, path in enumerate(paths, 1):
        if path.name != "%012d.json" % ordinal:
            raise ValueError("production event ordinals are not contiguous")
        event = _read_json_bounded(path, MAXIMUM_EVENT_BYTES)
        previous, event_progress = _validate_event(
            event,
            plan_sha256=plan["plan_sha256"],
            expected_ordinal=ordinal,
            previous_sha256=previous,
            current_state=state,
        )
        phase = event["evidence"].get("phase")
        if (
            event["event_kind"] == "CANONICAL_EVIDENCE_COMMITTED"
            and event["evidence"]["evidence_type"]
            == PREREQUISITE_EVIDENCE_TYPE_V2
        ):
            if ordinal != 1 or prerequisite_event is not None:
                raise ValueError("production prerequisite event placement is invalid")
            prerequisite_event = event
        if (
            event["event_kind"] == "CANONICAL_EVIDENCE_COMMITTED"
            and event["evidence"]["evidence_type"] == "RANK_PHASE_OPENED_V1"
        ):
            if ordinal != 2 or rank_open_event is not None:
                raise ValueError("production rank-open event placement is invalid")
            rank_open_event = event
        if event["event_kind"] == "CANONICAL_EVIDENCE_COMMITTED" and phase:
            expected = progress[phase]
            observed = event["evidence"]["coordinate_ordinal"]
            if observed != expected:
                raise ValueError("production coordinate evidence is not contiguous")
            progress[phase] = event_progress[phase]
        state = event["to_state"]
    durable_prerequisite = _load_optional_prerequisite_receipt_locked(
        directory, plan
    )
    if prerequisite_event is not None:
        if durable_prerequisite is None:
            raise ValueError(
                "committed prerequisite event lacks its durable receipt"
            )
        if (
            durable_prerequisite["receipt_sha256"]
            != prerequisite_event["evidence"][
                "canonical_loader_receipt_sha256"
            ]
        ):
            raise ValueError(
                "committed prerequisite event and durable receipt disagree"
            )
        expected_predecessor = _prerequisite_predecessor_receipts_sha256(
            plan, durable_prerequisite
        )
        if (
            prerequisite_event["evidence"]["predecessor_receipts_sha256"]
            != expected_predecessor
        ):
            raise ValueError(
                "prerequisite event predecessor custody is inconsistent"
            )
    if rank_open_event is not None:
        if durable_prerequisite is None or prerequisite_event is None:
            raise ValueError("rank-open event lacks prerequisite custody")
        expected_predecessor = _sha256_json(
            {
                "schema": "heterodiff-a1-production-rank-open-predecessors-v2",
                "plan_sha256": plan["plan_sha256"],
                "prerequisite_receipt_sha256": durable_prerequisite[
                    "receipt_sha256"
                ],
                "head_event_sha256": rank_open_event[
                    "previous_event_sha256"
                ],
            }
        )
        if (
            rank_open_event["evidence"]["canonical_loader_receipt_sha256"]
            != durable_prerequisite["receipt_sha256"]
            or rank_open_event["evidence"]["predecessor_receipts_sha256"]
            != expected_predecessor
        ):
            raise ValueError("rank-open event custody is inconsistent")
    return ProductionOrderSnapshot(
        _SNAPSHOT_KEY,
        directory,
        plan,
        state,
        previous,
        len(paths),
        progress,
    )


def load_production_order_snapshot(
    artifact_directory: os.PathLike,
) -> ProductionOrderSnapshot:
    directory = _absolute_without_symlink_resolution(artifact_directory)
    with _locked_artifact_directory(directory):
        return _load_snapshot_locked(directory)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _append_canonical_evidence_event_locked(
    directory: Path,
    snapshot: ProductionOrderSnapshot,
    *,
    evidence_type: str,
) -> ProductionOrderSnapshot:
    """Internal writer used only after a phase-specific canonical revalidation."""

    if evidence_type not in _SCIENTIFIC_EVIDENCE_TYPES:
        raise ValueError("phase-specific evidence type is not frozen")
    expected_from, to_state, phase = _EVIDENCE_TRANSITIONS[evidence_type]
    if phase is not None or snapshot.state != expected_from:
        raise PermissionError("phase-specific evidence is not current")
    if not _transition_allowed(snapshot.state, to_state):
        raise PermissionError("phase-specific production transition is forbidden")
    if evidence_type == PREREQUISITE_EVIDENCE_TYPE_V2:
        receipt = _load_prerequisite_receipt_locked(directory, snapshot.plan)
        predecessor_receipts_sha256 = (
            _prerequisite_predecessor_receipts_sha256(
                snapshot.plan, receipt
            )
        )
    elif evidence_type == "RANK_PHASE_OPENED_V1":
        receipt = _load_committed_prerequisite_binding_locked(
            directory, snapshot
        )
        predecessor_receipts_sha256 = _sha256_json(
            {
                "schema": "heterodiff-a1-production-rank-open-predecessors-v2",
                "plan_sha256": snapshot.plan_sha256,
                "prerequisite_receipt_sha256": receipt["receipt_sha256"],
                "head_event_sha256": snapshot.head_event_sha256,
            }
        )
    else:  # pragma: no cover - the frozen map is exhaustive above.
        raise AssertionError("unhandled production evidence type")
    evidence = {
        "evidence_type": evidence_type,
        "canonical_loader_receipt_sha256": receipt["receipt_sha256"],
        "predecessor_receipts_sha256": predecessor_receipts_sha256,
        "phase": None,
        "coordinate_ordinal": None,
        "coordinate_consumption_sha256": None,
    }
    body = {
        "schema": EVENT_SCHEMA,
        "ordinal": snapshot.event_count + 1,
        "plan_sha256": snapshot.plan_sha256,
        "previous_event_sha256": snapshot.head_event_sha256,
        "from_state": snapshot.state,
        "to_state": to_state,
        "event_kind": "CANONICAL_EVIDENCE_COMMITTED",
        "evidence": evidence,
        "timestamp_utc": _timestamp(),
        "authority_domain": AUTHORITY_DOMAIN,
    }
    event = dict(body)
    event["event_sha256"] = _sha256_json(body)
    validated_sha256, _ = _validate_event(
        event,
        plan_sha256=snapshot.plan_sha256,
        expected_ordinal=snapshot.event_count + 1,
        previous_sha256=snapshot.head_event_sha256,
        current_state=snapshot.state,
    )
    if validated_sha256 != event["event_sha256"]:
        raise AssertionError("prepublication event validation changed its digest")
    _atomic_exclusive_json(
        _event_path(directory, snapshot.event_count + 1), event
    )
    return _load_snapshot_locked(directory)


def validate_production_runtime_observation(
    value: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate a captured runtime record without probing the current host."""

    if type(value) is not dict:
        raise TypeError("production runtime observation must be an exact dictionary")
    record = dict(value)
    required = {
        "schema",
        "versions",
        "thread_environment",
        "native_pools",
        "numpy_configuration",
        "torch_environment",
        "host",
        "runtime_observation_sha256",
    }
    if set(record) != required:
        raise ValueError("production runtime observation schema is incomplete")
    body = dict(record)
    claimed = _require_sha256(
        body.pop("runtime_observation_sha256", None),
        name="runtime observation",
    )
    if _sha256_json(body) != claimed or record["schema"] != RUNTIME_OBSERVATION_SCHEMA:
        raise ValueError("production runtime observation digest/schema is invalid")
    contract = _frozen_runtime_contract_record()
    expected_versions = {
        name: contract[name]
        for name in ("python", "numpy", "scipy", "torch", "threadpoolctl")
    }
    if record["versions"] != expected_versions:
        raise ValueError("production runtime versions do not match the contract")
    if record["thread_environment"] != contract["thread_environment"]:
        raise ValueError("production runtime thread environment is not frozen")
    pools = record["native_pools"]
    if type(pools) is not list or len(pools) < contract[
        "native_pool_contract"
    ]["minimum_discovered_pool_count"]:
        raise ValueError("production runtime native-pool evidence is incomplete")
    pool_keys = []
    for pool in pools:
        if type(pool) is not dict or set(pool) != {
            "user_api",
            "internal_api",
            "prefix",
            "version",
            "num_threads",
        }:
            raise ValueError("production runtime native-pool schema is invalid")
        if any(
            type(pool[name]) is not str or not pool[name]
            for name in ("user_api", "internal_api", "prefix")
        ) or (
            pool["version"] is not None
            and (type(pool["version"]) is not str or not pool["version"])
        ):
            raise ValueError("production runtime native-pool identity is incomplete")
        if pool["num_threads"] != 1 or type(pool["num_threads"]) is not int:
            raise ValueError("production runtime native pool is not single-threaded")
        pool_keys.append(
            (
                pool["user_api"],
                pool["internal_api"],
                pool["prefix"],
                str(pool["version"]),
            )
        )
    if pool_keys != sorted(pool_keys) or len(pool_keys) != len(set(pool_keys)):
        raise ValueError("production runtime native-pool order is not canonical")
    configuration = record["numpy_configuration"]
    if type(configuration) is not dict or not configuration:
        raise ValueError("production NumPy build configuration is unavailable")
    _canonical_json(configuration)
    torch_environment = record["torch_environment"]
    expected_torch_keys = {
        "torch_cpu_only",
        "cuda_available",
        "torch_threads",
        "torch_interop_threads",
        "deterministic_algorithms",
        "configured_environment",
    }
    if type(torch_environment) is not dict or set(torch_environment) != expected_torch_keys:
        raise ValueError("production PyTorch runtime schema is invalid")
    configured = torch_environment["configured_environment"]
    expected_configured = {
        "python_version": contract["python"],
        "numpy_version": contract["numpy"],
        "scipy_version": contract["scipy"],
        "torch_version": contract["torch"],
        "torch_cpu_only": True,
        "torch_threads": 1,
        "torch_interop_threads": 1,
        "deterministic_algorithms": True,
    }
    if (
        torch_environment["torch_cpu_only"] is not True
        or torch_environment["cuda_available"] is not False
        or torch_environment["torch_threads"] != 1
        or type(torch_environment["torch_threads"]) is not int
        or torch_environment["torch_interop_threads"] != 1
        or type(torch_environment["torch_interop_threads"]) is not int
        or torch_environment["deterministic_algorithms"] is not True
        or configured != expected_configured
    ):
        raise ValueError("production PyTorch runtime is not frozen CPU-only")
    host = record["host"]
    if type(host) is not dict or set(host) != {
        "platform",
        "system",
        "release",
        "machine",
        "processor",
        "python_implementation",
        "executable_binary_sha256",
    }:
        raise ValueError("production host identity schema is invalid")
    if any(
        type(host[name]) is not str or not host[name]
        for name in (
            "platform",
            "system",
            "release",
            "machine",
            "processor",
            "python_implementation",
        )
    ):
        raise ValueError("production host identity metadata is incomplete")
    _require_sha256(
        host["executable_binary_sha256"], name="Python executable binary"
    )
    return record


def _capture_legacy_metric_runtime_preflight() -> Dict[str, Any]:
    """Legacy in-process metric observation; never prerequisite attestation."""

    contract = _frozen_runtime_contract_record()
    observed_environment = {
        name: os.environ.get(name)
        for name in contract["thread_environment"]
    }
    if observed_environment != contract["thread_environment"]:
        raise RuntimeError(
            "production runtime environment must be frozen before numerical imports"
        )

    import numpy as np
    import scipy
    import threadpoolctl
    import torch
    from heterodiff.experiments.finite_association_residual_training_torch import (
        configure_frozen_association_training_environment,
    )

    configured = configure_frozen_association_training_environment()
    versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "threadpoolctl": threadpoolctl.__version__,
    }
    expected_versions = {
        name: contract[name]
        for name in ("python", "numpy", "scipy", "torch", "threadpoolctl")
    }
    if versions != expected_versions:
        raise RuntimeError("production runtime library versions are not frozen")
    pools = threadpoolctl.threadpool_info()
    normalized_pools = []
    for pool in pools:
        count = pool.get("num_threads")
        if isinstance(count, bool) or type(count) is not int or count != 1:
            raise RuntimeError("a production native pool is not single-threaded")
        normalized = {
            "user_api": pool.get("user_api"),
            "internal_api": pool.get("internal_api"),
            "prefix": pool.get("prefix"),
            "version": pool.get("version"),
            "num_threads": count,
        }
        if any(
            type(normalized[name]) is not str or not normalized[name]
            for name in ("user_api", "internal_api", "prefix")
        ) or (
            normalized["version"] is not None
            and (
                type(normalized["version"]) is not str
                or not normalized["version"]
            )
        ):
            raise RuntimeError("production native-pool metadata is incomplete")
        normalized_pools.append(normalized)
    normalized_pools.sort(
        key=lambda value: (
            value["user_api"],
            value["internal_api"],
            value["prefix"],
            str(value["version"]),
        )
    )
    if len(normalized_pools) < contract["native_pool_contract"][
        "minimum_discovered_pool_count"
    ]:
        raise RuntimeError("production runtime exposes no qualifying native pool")
    numpy_configuration = getattr(np.__config__, "CONFIG", None)
    if not isinstance(numpy_configuration, dict) or not numpy_configuration:
        raise RuntimeError("production NumPy build configuration is unavailable")
    _canonical_json(numpy_configuration)
    processor = platform.processor() or platform.uname().processor or platform.machine()
    executable = Path(sys.executable).resolve(strict=True)
    executable_sha256, _ = _sha256_file(executable, 512 * 1024 * 1024)
    host = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": processor,
        "python_implementation": platform.python_implementation(),
        "executable_binary_sha256": executable_sha256,
    }
    if any(type(host[name]) is not str or not host[name] for name in (
        "platform", "system", "release", "machine", "processor"
    )):
        raise RuntimeError("production host identity metadata is incomplete")
    torch_environment = {
        "torch_cpu_only": torch.version.cuda is None,
        "cuda_available": bool(torch.cuda.is_available()),
        "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "configured_environment": {
            key: getattr(configured, key)
            for key in (
                "python_version",
                "numpy_version",
                "scipy_version",
                "torch_version",
                "torch_cpu_only",
                "torch_threads",
                "torch_interop_threads",
                "deterministic_algorithms",
            )
        },
    }
    if (
        torch_environment["torch_cpu_only"] is not True
        or torch_environment["cuda_available"] is not False
        or torch_environment["torch_threads"] != 1
        or torch_environment["torch_interop_threads"] != 1
        or torch_environment["deterministic_algorithms"] is not True
    ):
        raise RuntimeError("production PyTorch runtime is not frozen CPU-only")
    body = {
        "schema": RUNTIME_OBSERVATION_SCHEMA,
        "versions": versions,
        "thread_environment": observed_environment,
        "native_pools": normalized_pools,
        "numpy_configuration": numpy_configuration,
        "torch_environment": torch_environment,
        "host": host,
    }
    record = dict(body)
    record["runtime_observation_sha256"] = _sha256_json(body)
    return validate_production_runtime_observation(record)


def validate_production_runtime_observation_v2(
    value: Mapping[str, Any], *, plan: Mapping[str, Any]
) -> Dict[str, Any]:
    """Validate one historical child observation against an immutable plan."""

    return runtime_attestor.validate_runtime_attestor_observation(
        value, plan=plan
    )


def _metadata_only_production_runtime_preflight(
    snapshot: ProductionOrderSnapshot,
) -> Dict[str, Any]:
    if type(snapshot) is not ProductionOrderSnapshot:
        raise TypeError("target-runtime preflight requires a production snapshot")
    _require_live_module_workspace(snapshot)
    if snapshot.state in TERMINAL_STATES:
        raise PermissionError("target-runtime preflight rejects terminal custody")
    manifest = (
        runtime_identity.require_approved_checked_in_runtime_identity_manifest()
    )
    reference = _runtime_identity_reference(manifest)
    expected_contract = _production_runtime_contract_v2_record(
        source_manifest_sha256=snapshot.plan["source_manifest_sha256"],
        environment_lock_sha256=reference["environment_lock_sha256"],
        runtime_identity_manifest_sha256=reference["manifest_sha256"],
        minimum_macos_version=manifest.record["profile"][
            "minimum_macos_version"
        ],
    )
    if _plain_json_value(snapshot.plan["runtime_contract"]) != expected_contract:
        raise ValueError("target-runtime contract is not frozen")
    if (
        reference != _plain_json_value(
            snapshot.plan["runtime_identity_manifest"]
        )
        or manifest.identity_files_verified is not True
    ):
        raise PermissionError("target-runtime identity is not plan-bound and verified")
    body = {
        "schema": "heterodiff-a1-production-runtime-metadata-preflight-v2",
        "plan_sha256": snapshot.plan_sha256,
        "campaign_instance_nonce_sha256": (
            snapshot.campaign_instance_nonce_sha256
        ),
        "source_manifest_sha256": snapshot.plan["source_manifest_sha256"],
        "runtime_contract_sha256": _sha256_json(
            snapshot.plan["runtime_contract"]
        ),
        "runtime_identity_manifest_sha256": manifest.manifest_sha256,
        "runtime_identity_components_sha256": _sha256_json(
            reference["component_sha256"]
        ),
        "identity_files_verified": True,
        "metadata_only": True,
        "scientific_compute_executed": False,
    }
    record = dict(body)
    record["metadata_preflight_sha256"] = _sha256_json(body)
    return record


def capture_production_runtime_preflight(
    snapshot: ProductionOrderSnapshot,
) -> Dict[str, Any]:
    """Validate v2 runtime custody using metadata only and no numerics."""

    return _metadata_only_production_runtime_preflight(snapshot)


def _launch_attested_production_prerequisite(
    snapshot: ProductionOrderSnapshot,
    *,
    operation: str = PREREQUISITE_OPERATION_V2,
) -> Dict[str, Any]:
    if operation not in (
        PREREQUISITE_OPERATION_V2,
        PREREQUISITE_REVALIDATION_OPERATION_V2,
    ):
        raise ValueError("attested prerequisite operation is not frozen")
    capture_production_runtime_preflight(snapshot)
    return runtime_attestor._launch_runtime_attestor(snapshot, operation)


def _attested_prerequisite_semantic_binding(
    envelope: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    expected_operation: Optional[str] = None,
) -> Dict[str, Any]:
    checked = runtime_attestor.validate_runtime_attestor_envelope(
        envelope, plan=plan
    )
    request = runtime_attestor.runtime_attestor_request_from_observation(
        checked["pre_observation"]
    )
    expected_attestor_source_sha256 = next(
        (
            row["sha256"]
            for row in plan["source_paths"]
            if row["path"] == runtime_attestor.ATTESTOR_SOURCE_RELATIVE_PATH
        ),
        None,
    )
    if (
        request["attestor_source_sha256"]
        != expected_attestor_source_sha256
        or (
            expected_operation is not None
            and request["operation"] != expected_operation
        )
    ):
        raise ValueError("attested prerequisite has the wrong worker custody")
    payload = _validate_attested_prerequisite_payload(
        checked["typed_prerequisite_result"]
    )
    pre = checked["pre_observation"]
    post = checked["post_observation"]
    return {
        "schema": "heterodiff-a1-production-prerequisite-semantics-v2",
        "plan_sha256": plan["plan_sha256"],
        "campaign_instance_nonce_sha256": plan[
            "campaign_instance_nonce_sha256"
        ],
        "source_manifest_sha256": plan["source_manifest_sha256"],
        "runtime_contract_sha256": _sha256_json(plan["runtime_contract"]),
        "runtime_identity_manifest_sha256": plan[
            "runtime_identity_manifest"
        ]["manifest_sha256"],
        "runtime_identity_components_sha256": _sha256_json(
            plan["runtime_identity_manifest"]["component_sha256"]
        ),
        "specification_sha256": plan["specification"]["sha256"],
        "stable_runtime_sha256": pre["stable_runtime_sha256"],
        "post_stable_runtime_sha256": post["stable_runtime_sha256"],
        "typed_prerequisite_result_sha256": _sha256_json(payload),
        "fixture_sha256": _frozen_prerequisite_fixture_sha256(),
        "passed": True,
    }


def _build_prerequisite_receipt_v2(
    snapshot: ProductionOrderSnapshot,
    envelope: Mapping[str, Any],
) -> Dict[str, Any]:
    checked = runtime_attestor.validate_runtime_attestor_envelope(
        envelope, plan=snapshot.plan
    )
    request = runtime_attestor.runtime_attestor_request_from_observation(
        checked["pre_observation"]
    )
    if request["operation"] != PREREQUISITE_OPERATION_V2:
        raise ValueError("initial prerequisite receipt has the wrong operation")
    semantics = _attested_prerequisite_semantic_binding(
        checked,
        plan=snapshot.plan,
        expected_operation=PREREQUISITE_OPERATION_V2,
    )
    pre = checked["pre_observation"]
    post = checked["post_observation"]
    body = {
        "schema": PREREQUISITE_RECEIPT_SCHEMA_V2,
        "plan_sha256": snapshot.plan_sha256,
        "campaign_instance_nonce_sha256": (
            snapshot.campaign_instance_nonce_sha256
        ),
        "source_manifest_sha256": semantics["source_manifest_sha256"],
        "runtime_contract_sha256": semantics["runtime_contract_sha256"],
        "runtime_identity_manifest_sha256": semantics[
            "runtime_identity_manifest_sha256"
        ],
        "runtime_identity_components_sha256": semantics[
            "runtime_identity_components_sha256"
        ],
        "specification_sha256": semantics["specification_sha256"],
        "attestor_envelope": checked,
        "attestor_envelope_sha256": checked["envelope_sha256"],
        "pre_runtime_observation_sha256": pre["observation_sha256"],
        "post_runtime_observation_sha256": post["observation_sha256"],
        "stable_runtime_sha256": semantics["stable_runtime_sha256"],
        "typed_prerequisite_result_sha256": semantics[
            "typed_prerequisite_result_sha256"
        ],
        "fixture_sha256": semantics["fixture_sha256"],
        "passed": True,
    }
    receipt = dict(body)
    receipt["receipt_sha256"] = _sha256_json(body)
    if len(_canonical_json(receipt)) > MAXIMUM_RECEIPT_BYTES:
        raise ValueError("production prerequisite receipt exceeds its byte limit")
    return _validate_prerequisite_receipt_record(receipt, snapshot.plan)


def _require_live_module_workspace(snapshot: ProductionOrderSnapshot) -> None:
    """Prevent a plan over unrelated bytes from authorizing imported runners."""

    planned_root = _require_production_artifact_directory(
        snapshot.artifact_directory
    ).parent.parent
    live_root = Path(__file__).resolve(strict=True).parents[3]
    if planned_root != live_root:
        raise PermissionError(
            "compute-bearing production operations require the live module workspace"
        )


def _load_committed_prerequisite_binding_locked(
    directory: Path, snapshot: ProductionOrderSnapshot
) -> Dict[str, Any]:
    if snapshot.event_count < 1 or snapshot.state == "NEW":
        raise PermissionError("production prerequisite has not been committed")
    event = _read_json_bounded(_event_path(directory, 1), MAXIMUM_EVENT_BYTES)
    if (
        event["event_kind"] != "CANONICAL_EVIDENCE_COMMITTED"
        or event["from_state"] != "NEW"
        or event["to_state"] != "PREREQUISITE_VERIFIED"
        or event["evidence"]["evidence_type"]
        != PREREQUISITE_EVIDENCE_TYPE_V2
    ):
        raise RuntimeError("first production event is not the prerequisite binding")
    receipt = _load_prerequisite_receipt_locked(directory, snapshot.plan)
    if (
        event["evidence"]["canonical_loader_receipt_sha256"]
        != receipt["receipt_sha256"]
    ):
        raise RuntimeError("prerequisite event no longer binds its durable receipt")
    return receipt


def load_production_prerequisite_evidence(
    artifact_directory: os.PathLike,
) -> ProductionVerifiedPrerequisite:
    """Load already-committed prerequisite custody without recomputation."""

    directory = _absolute_without_symlink_resolution(artifact_directory)
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        receipt = _load_committed_prerequisite_binding_locked(
            directory, snapshot
        )
        return ProductionVerifiedPrerequisite(
            _PREREQUISITE_KEY, snapshot, receipt
        )


def verify_and_commit_production_prerequisite(
    snapshot: ProductionOrderSnapshot,
) -> ProductionVerifiedPrerequisite:
    """Run phase 1 only in its attested child and commit receipt before event."""

    if type(snapshot) is not ProductionOrderSnapshot:
        raise TypeError("prerequisite verification requires a production snapshot")
    if snapshot.state != "NEW":
        raise PermissionError("prerequisite verification is allowed only from NEW")
    _require_live_module_workspace(snapshot)
    directory = _absolute_without_symlink_resolution(
        snapshot.artifact_directory
    )
    with _locked_artifact_directory(directory):
        current = _load_snapshot_locked(directory)
        if (
            current.state != "NEW"
            or current.plan_sha256 != snapshot.plan_sha256
            or current.head_event_sha256 != snapshot.head_event_sha256
            or current.event_count != snapshot.event_count
        ):
            raise PermissionError("production prerequisite snapshot is stale")
        if _preexisting_output_status(directory.parent.parent):
            raise FileExistsError(
                "prerequisite verification rejects preexisting phase outputs"
            )
        orphan = _load_optional_prerequisite_receipt_locked(
            directory, current.plan
        )
        if orphan is not None:
            committed = _append_canonical_evidence_event_locked(
                directory,
                current,
                evidence_type=PREREQUISITE_EVIDENCE_TYPE_V2,
            )
            return ProductionVerifiedPrerequisite(
                _PREREQUISITE_KEY, committed, orphan
            )
        baseline = (
            current.plan_sha256,
            current.head_event_sha256,
            current.event_count,
            current.state,
        )

    envelope = _launch_attested_production_prerequisite(current)
    receipt = _build_prerequisite_receipt_v2(current, envelope)

    with _locked_artifact_directory(directory):
        committed_from = _load_snapshot_locked(directory)
        if committed_from.state in TERMINAL_STATES:
            raise PermissionError("production order terminalized during attestation")
        if committed_from.state != "NEW":
            durable_receipt = _load_committed_prerequisite_binding_locked(
                directory, committed_from
            )
            return ProductionVerifiedPrerequisite(
                _PREREQUISITE_KEY, committed_from, durable_receipt
            )
        if _preexisting_output_status(directory.parent.parent):
            raise FileExistsError(
                "a phase output appeared during prerequisite recomputation"
            )
        existing = _load_optional_prerequisite_receipt_locked(
            directory, committed_from.plan
        )
        if existing is None:
            if (
                (
                    committed_from.plan_sha256,
                    committed_from.head_event_sha256,
                    committed_from.event_count,
                    committed_from.state,
                )
                != baseline
            ):
                raise PermissionError(
                    "prerequisite result became stale during attestation"
                )
            durable_receipt = _persist_prerequisite_receipt_locked(
                directory, committed_from.plan, receipt
            )
        else:
            # Fresh challenges and process IDs make independently valid v2
            # receipts byte-distinct.  The first exclusive durable publication
            # is canonical; a concurrent loser adopts it without overwrite.
            durable_receipt = existing
        committed = _append_canonical_evidence_event_locked(
            directory,
            committed_from,
            evidence_type=PREREQUISITE_EVIDENCE_TYPE_V2,
        )
    return ProductionVerifiedPrerequisite(
        _PREREQUISITE_KEY, committed, durable_receipt
    )


def revalidate_production_prerequisite(
    admitted: ProductionVerifiedPrerequisite,
) -> ProductionVerifiedPrerequisite:
    """Re-attest phase 1 and match only its stable scientific semantics."""

    if type(admitted) is not ProductionVerifiedPrerequisite:
        raise TypeError("prerequisite revalidation requires loader admission")
    _require_live_module_workspace(admitted.snapshot)
    directory = _absolute_without_symlink_resolution(
        admitted.snapshot.artifact_directory
    )
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        if snapshot.state == "NEW" or snapshot.state in TERMINAL_STATES:
            raise PermissionError(
                "prerequisite revalidation requires a live admitted phase"
            )
        if (
            snapshot.plan_sha256 != admitted.snapshot.plan_sha256
            or snapshot.campaign_instance_nonce_sha256
            != admitted.snapshot.campaign_instance_nonce_sha256
        ):
            raise RuntimeError("production prerequisite plan changed")
        durable_receipt = _load_committed_prerequisite_binding_locked(
            directory, snapshot
        )
        if (
            durable_receipt["receipt_sha256"] != admitted.receipt_sha256
            or durable_receipt != _plain_json_value(admitted.record)
        ):
            raise RuntimeError("committed prerequisite receipt changed")
        baseline = (
            snapshot.plan_sha256,
            snapshot.head_event_sha256,
            snapshot.event_count,
            snapshot.state,
        )

    fresh_envelope = _launch_attested_production_prerequisite(
        snapshot,
        operation=PREREQUISITE_REVALIDATION_OPERATION_V2,
    )
    durable_semantics = _attested_prerequisite_semantic_binding(
        durable_receipt["attestor_envelope"],
        plan=snapshot.plan,
        expected_operation=PREREQUISITE_OPERATION_V2,
    )
    fresh_semantics = _attested_prerequisite_semantic_binding(
        fresh_envelope,
        plan=snapshot.plan,
        expected_operation=PREREQUISITE_REVALIDATION_OPERATION_V2,
    )
    if fresh_semantics != durable_semantics:
        raise RuntimeError("canonical prerequisite semantic result changed")

    with _locked_artifact_directory(directory):
        current = _load_snapshot_locked(directory)
        if (
            (
                current.plan_sha256,
                current.head_event_sha256,
                current.event_count,
                current.state,
            )
            != baseline
        ):
            raise PermissionError(
                "production order changed during prerequisite revalidation"
            )
        current_receipt = _load_committed_prerequisite_binding_locked(
            directory, current
        )
        if current_receipt != durable_receipt:
            raise RuntimeError("prerequisite custody changed during revalidation")
    return ProductionVerifiedPrerequisite(
        _PREREQUISITE_KEY, current, current_receipt
    )


def open_production_rank_phase(
    prerequisite: ProductionVerifiedPrerequisite,
) -> ProductionOrderSnapshot:
    """Open rank authorization only from freshly revalidated phase-1 evidence."""

    canonical = revalidate_production_prerequisite(prerequisite)
    directory = _absolute_without_symlink_resolution(
        canonical.snapshot.artifact_directory
    )
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        if snapshot.state != "PREREQUISITE_VERIFIED":
            raise PermissionError("rank phase is not the current barrier")
        if _preexisting_output_status(directory.parent.parent):
            raise FileExistsError("rank phase rejects preexisting compute artifacts")
        return _append_canonical_evidence_event_locked(
            directory,
            snapshot,
            evidence_type="RANK_PHASE_OPENED_V1",
        )


def terminalize_production_order(
    snapshot: ProductionOrderSnapshot,
    terminal_state: str,
    *,
    reason_code: str,
    detail: str,
) -> ProductionOrderSnapshot:
    """Fail closed.  This is the only public generic state mutation."""

    if type(snapshot) is not ProductionOrderSnapshot:
        raise TypeError("terminalization requires a loader-created snapshot")
    if terminal_state not in TERMINAL_STATES:
        raise ValueError("terminal_state must be HOLD or FAILURE")
    if type(reason_code) is not str or not reason_code or len(reason_code) > 128:
        raise ValueError("reason_code must be a bounded nonempty string")
    if type(detail) is not str or not detail or len(detail) > 4096:
        raise ValueError("detail must be a bounded nonempty string")
    directory = _absolute_without_symlink_resolution(
        snapshot.artifact_directory
    )
    with _locked_artifact_directory(directory):
        current = _load_snapshot_locked(directory)
        if (
            current.plan_sha256 != snapshot.plan_sha256
            or current.head_event_sha256 != snapshot.head_event_sha256
            or current.state != snapshot.state
        ):
            raise PermissionError("production snapshot is stale")
        if not _transition_allowed(current.state, terminal_state):
            raise PermissionError("production ledger is already terminal")
        body = {
            "schema": EVENT_SCHEMA,
            "ordinal": current.event_count + 1,
            "plan_sha256": current.plan_sha256,
            "previous_event_sha256": current.head_event_sha256,
            "from_state": current.state,
            "to_state": terminal_state,
            "event_kind": "TERMINALIZED",
            "evidence": {"reason_code": reason_code, "detail": detail},
            "timestamp_utc": _timestamp(),
            "authority_domain": AUTHORITY_DOMAIN,
        }
        event = dict(body)
        event["event_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(
            _event_path(directory, current.event_count + 1), event
        )
        return _load_snapshot_locked(directory)


class ProductionPhaseAuthorization:
    __slots__ = ("_artifact_directory", "_record", "_locked")

    def __init__(
        self, construction_key: object, artifact_directory: Path, record: dict
    ) -> None:
        if construction_key is not _AUTHORIZATION_KEY:
            raise TypeError("phase authorizations come only from the canonical loader")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(record))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("phase authorization is immutable")
        object.__setattr__(self, name, value)

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    @property
    def phase(self) -> str:
        return self._record["phase"]

    @property
    def authorization_sha256(self) -> str:
        return self._record["authorization_sha256"]


class ProductionPhaseConsumption:
    __slots__ = ("_artifact_directory", "_record", "_locked")

    def __init__(
        self, construction_key: object, artifact_directory: Path, record: dict
    ) -> None:
        if construction_key is not _CONSUMPTION_KEY:
            raise TypeError("phase consumptions come only from the canonical loader")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(record))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("phase consumption is immutable")
        object.__setattr__(self, name, value)

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    @property
    def phase(self) -> str:
        return self._record["phase"]

    @property
    def consumption_sha256(self) -> str:
        return self._record["consumption_sha256"]


def _authorization_paths(directory: Path, phase: str) -> Tuple[Path, Path]:
    if phase not in AUTHORIZATION_STATES:
        raise PermissionError("phase is not production-authorizable")
    base = directory / AUTHORIZATION_DIRECTORY_NAME / phase.lower()
    return base.with_suffix(".issued.json"), base.with_suffix(".consumed.json")


def _validate_authorization(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "phase",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "artifact_identity_sha256",
        "head_event_sha256",
        "authorization_nonce_sha256",
        "issued_timestamp_utc",
        "authority_domain",
        "order_progression_authorized",
        "production_execution_authorized",
        "runner_binding_required",
        "runner_binding_complete",
        "scientific_evidence_required",
        "authorization_sha256",
    }
    if type(record) is not dict or set(record) != required:
        raise ValueError("production authorization schema is invalid")
    body = dict(record)
    claimed = _require_sha256(
        body.pop("authorization_sha256", None), name="authorization_sha256"
    )
    if (
        _sha256_json(body) != claimed
        or record.get("schema") != AUTHORIZATION_SCHEMA
        or record.get("phase") not in AUTHORIZATION_STATES
        or record.get("authority_domain") != AUTHORITY_DOMAIN
        or record.get("order_progression_authorized") is not True
        or record.get("production_execution_authorized") is not False
        or record.get("runner_binding_required") is not True
        or record.get("runner_binding_complete") is not False
        or record.get("scientific_evidence_required") is not True
    ):
        raise ValueError("production authorization contents are invalid")
    for name in (
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "artifact_identity_sha256",
        "head_event_sha256",
        "authorization_nonce_sha256",
    ):
        _require_sha256(record[name], name=name)
    try:
        datetime.strptime(record["issued_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("production authorization timestamp is invalid") from error


def _load_authorization_locked(
    directory: Path, phase: str
) -> ProductionPhaseAuthorization:
    issued, _ = _authorization_paths(directory, phase)
    record = _read_json_bounded(issued, MAXIMUM_RECEIPT_BYTES)
    _validate_authorization(record)
    return ProductionPhaseAuthorization(_AUTHORIZATION_KEY, directory, record)


def load_production_phase_authorization(
    artifact_directory: os.PathLike, phase: str
) -> ProductionPhaseAuthorization:
    """Reload a custody-only phase authorization after interruption."""

    directory = _absolute_without_symlink_resolution(artifact_directory)
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        authorization = _load_authorization_locked(directory, phase)
        if (
            snapshot.state != phase
            or authorization.record["plan_sha256"] != snapshot.plan_sha256
            or authorization.record["campaign_instance_nonce_sha256"]
            != snapshot.campaign_instance_nonce_sha256
            or authorization.record["artifact_identity_sha256"]
            != snapshot.plan["artifact_identity"]["identity_sha256"]
            or authorization.record["head_event_sha256"]
            != snapshot.head_event_sha256
        ):
            raise PermissionError("production phase authorization is stale")
        return authorization


def issue_production_phase_authorization(
    snapshot: ProductionOrderSnapshot, phase: str
) -> ProductionPhaseAuthorization:
    if type(snapshot) is not ProductionOrderSnapshot:
        raise TypeError("authorization requires a loader-created snapshot")
    if phase not in AUTHORIZATION_STATES:
        raise PermissionError("phase is not production-authorizable")
    directory = _absolute_without_symlink_resolution(
        snapshot.artifact_directory
    )
    with _locked_artifact_directory(directory):
        current = _load_snapshot_locked(directory)
        if (
            current.state != phase
            or current.plan_sha256 != snapshot.plan_sha256
            or current.head_event_sha256 != snapshot.head_event_sha256
        ):
            raise PermissionError("only the current production phase may authorize")
        if phase == "RANK_AUTHORIZED" and _preexisting_output_status(
            directory.parent.parent
        ):
            raise FileExistsError(
                "rank authorization rejects preexisting compute artifacts"
            )
        issued, consumed = _authorization_paths(directory, phase)
        if issued.exists():
            existing = _load_authorization_locked(directory, phase)
            if (
                existing.record["plan_sha256"] != current.plan_sha256
                or existing.record["campaign_instance_nonce_sha256"]
                != current.campaign_instance_nonce_sha256
                or existing.record["artifact_identity_sha256"]
                != current.plan["artifact_identity"]["identity_sha256"]
                or existing.record["head_event_sha256"]
                != current.head_event_sha256
            ):
                raise PermissionError(
                    "existing production phase authorization is stale"
                )
            return existing
        if consumed.exists():
            raise ValueError(
                "phase consumption exists without its issued authorization"
            )
        body = {
            "schema": AUTHORIZATION_SCHEMA,
            "phase": phase,
            "plan_sha256": current.plan_sha256,
            "campaign_instance_nonce_sha256": current.campaign_instance_nonce_sha256,
            "artifact_identity_sha256": current.plan["artifact_identity"][
                "identity_sha256"
            ],
            "head_event_sha256": current.head_event_sha256,
            "authorization_nonce_sha256": hashlib.sha256(
                secrets.token_bytes(32)
            ).hexdigest(),
            "issued_timestamp_utc": _timestamp(),
            "authority_domain": AUTHORITY_DOMAIN,
            "order_progression_authorized": True,
            "production_execution_authorized": False,
            "runner_binding_required": True,
            "runner_binding_complete": False,
            "scientific_evidence_required": True,
        }
        record = dict(body)
        record["authorization_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(issued, record)
        return _load_authorization_locked(directory, phase)


def _validate_consumption(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "phase",
        "authorization_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "artifact_identity_sha256",
        "authorized_head_event_sha256",
        "consumer_id",
        "consumed_timestamp_utc",
        "authority_domain",
        "production_execution_permit_issued",
        "runner_binding_required",
        "runner_binding_complete",
        "scientific_execution_authorized",
        "consumption_sha256",
    }
    if type(record) is not dict or set(record) != required:
        raise ValueError("production phase-consumption schema is invalid")
    body = dict(record)
    claimed = _require_sha256(
        body.pop("consumption_sha256", None), name="consumption_sha256"
    )
    if (
        _sha256_json(body) != claimed
        or record.get("schema") != AUTHORIZATION_CONSUMPTION_SCHEMA
        or record.get("phase") not in AUTHORIZATION_STATES
        or record.get("authority_domain") != AUTHORITY_DOMAIN
        or record.get("production_execution_permit_issued") is not False
        or record.get("runner_binding_required") is not True
        or record.get("runner_binding_complete") is not False
        or record.get("scientific_execution_authorized") is not False
    ):
        raise ValueError("production phase-consumption contents are invalid")
    for name in (
        "authorization_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "artifact_identity_sha256",
        "authorized_head_event_sha256",
    ):
        _require_sha256(record[name], name=name)
    if (
        type(record["consumer_id"]) is not str
        or not record["consumer_id"]
        or len(record["consumer_id"]) > 256
        or "\x00" in record["consumer_id"]
    ):
        raise ValueError("production consumer_id is invalid")
    try:
        datetime.strptime(
            record["consumed_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except (TypeError, ValueError) as error:
        raise ValueError("production phase-consumption timestamp is invalid") from error


def consume_production_phase_authorization(
    authorization: ProductionPhaseAuthorization, *, consumer_id: str
) -> ProductionPhaseConsumption:
    if type(authorization) is not ProductionPhaseAuthorization:
        raise TypeError("consumption requires a loader-created authorization")
    directory = _absolute_without_symlink_resolution(
        authorization.artifact_directory
    )
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        canonical = _load_authorization_locked(directory, authorization.phase)
        _, consumed_path = _authorization_paths(directory, authorization.phase)
        if (
            snapshot.state != authorization.phase
            or snapshot.head_event_sha256
            != authorization.record["head_event_sha256"]
            or canonical.authorization_sha256
            != authorization.authorization_sha256
            or canonical.record != authorization.record
        ):
            raise PermissionError("production phase authorization is stale")
        if authorization.phase == "RANK_AUTHORIZED" and (
            _preexisting_output_status(directory.parent.parent)
        ):
            raise FileExistsError(
                "rank authorization consumption rejects preexisting artifacts"
            )
        if consumed_path.exists():
            loaded = _read_json_bounded(
                consumed_path, MAXIMUM_RECEIPT_BYTES
            )
            _validate_consumption(loaded)
            if (
                loaded["authorization_sha256"]
                != authorization.authorization_sha256
                or loaded["plan_sha256"] != snapshot.plan_sha256
                or loaded["campaign_instance_nonce_sha256"]
                != snapshot.campaign_instance_nonce_sha256
                or loaded["artifact_identity_sha256"]
                != snapshot.plan["artifact_identity"]["identity_sha256"]
                or loaded["authorized_head_event_sha256"]
                != snapshot.head_event_sha256
                or loaded["consumer_id"] != consumer_id
            ):
                raise PermissionError(
                    "production phase authorization was consumed differently"
                )
            return ProductionPhaseConsumption(
                _CONSUMPTION_KEY, directory, loaded
            )
        body = {
            "schema": AUTHORIZATION_CONSUMPTION_SCHEMA,
            "phase": authorization.phase,
            "authorization_sha256": authorization.authorization_sha256,
            "plan_sha256": snapshot.plan_sha256,
            "campaign_instance_nonce_sha256": snapshot.campaign_instance_nonce_sha256,
            "artifact_identity_sha256": snapshot.plan["artifact_identity"][
                "identity_sha256"
            ],
            "authorized_head_event_sha256": snapshot.head_event_sha256,
            "consumer_id": consumer_id,
            "consumed_timestamp_utc": _timestamp(),
            "authority_domain": AUTHORITY_DOMAIN,
            "production_execution_permit_issued": False,
            "runner_binding_required": True,
            "runner_binding_complete": False,
            "scientific_execution_authorized": False,
        }
        record = dict(body)
        record["consumption_sha256"] = _sha256_json(body)
        _validate_consumption(record)
        _atomic_exclusive_json(consumed_path, record)
        loaded = _read_json_bounded(consumed_path, MAXIMUM_RECEIPT_BYTES)
        _validate_consumption(loaded)
        return ProductionPhaseConsumption(_CONSUMPTION_KEY, directory, loaded)


def load_production_phase_consumption(
    artifact_directory: os.PathLike, phase: str
) -> ProductionPhaseConsumption:
    """Reload a custody-only phase consumption after interruption."""

    directory = _absolute_without_symlink_resolution(artifact_directory)
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        authorization = _load_authorization_locked(directory, phase)
        _, path = _authorization_paths(directory, phase)
        record = _read_json_bounded(path, MAXIMUM_RECEIPT_BYTES)
        _validate_consumption(record)
        if (
            snapshot.state != phase
            or record["authorization_sha256"]
            != authorization.authorization_sha256
            or record["plan_sha256"] != snapshot.plan_sha256
            or record["campaign_instance_nonce_sha256"]
            != snapshot.campaign_instance_nonce_sha256
            or record["artifact_identity_sha256"]
            != snapshot.plan["artifact_identity"]["identity_sha256"]
            or record["authorized_head_event_sha256"]
            != snapshot.head_event_sha256
        ):
            raise PermissionError("production phase consumption is stale")
        return ProductionPhaseConsumption(_CONSUMPTION_KEY, directory, record)


class ProductionCoordinatePermit:
    __slots__ = ("_artifact_directory", "_record", "_locked")

    def __init__(
        self, construction_key: object, artifact_directory: Path, record: dict
    ) -> None:
        if construction_key is not _COORDINATE_PERMIT_KEY:
            raise TypeError("coordinate permits come only from the canonical loader")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(record))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("coordinate permit is immutable")
        object.__setattr__(self, name, value)

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    @property
    def phase(self) -> str:
        return self._record["phase"]

    @property
    def coordinate(self) -> tuple:
        return tuple(self._record["coordinate"])

    @property
    def permit_sha256(self) -> str:
        return self._record["permit_sha256"]


class ProductionCoordinateConsumption:
    __slots__ = ("_artifact_directory", "_record", "_locked")

    def __init__(
        self, construction_key: object, artifact_directory: Path, record: dict
    ) -> None:
        if construction_key is not _COORDINATE_CONSUMPTION_KEY:
            raise TypeError("coordinate consumptions come only from the canonical loader")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(record))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("coordinate consumption is immutable")
        object.__setattr__(self, name, value)

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    @property
    def consumption_sha256(self) -> str:
        return self._record["consumption_sha256"]


def _coordinate_paths(
    directory: Path, phase: str, ordinal: int
) -> Tuple[Path, Path]:
    base = (
        directory
        / COORDINATE_PERMIT_DIRECTORY_NAME
        / phase.lower()
        / ("%012d" % ordinal)
    )
    return base.with_suffix(".issued.json"), base.with_suffix(".consumed.json")


def _validate_coordinate_permit(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "phase",
        "coordinate_ordinal",
        "coordinate",
        "coordinate_manifest_sha256",
        "phase_consumption_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "head_event_sha256",
        "permit_nonce_sha256",
        "issued_timestamp_utc",
        "authority_domain",
        "permit_sha256",
    }
    if type(record) is not dict or set(record) != required:
        raise ValueError("production coordinate-permit schema is invalid")
    body = dict(record)
    claimed = _require_sha256(body.pop("permit_sha256", None), name="permit_sha256")
    phase = record.get("phase")
    ordinal = record.get("coordinate_ordinal")
    if (
        _sha256_json(body) != claimed
        or record.get("schema") != COORDINATE_PERMIT_SCHEMA
        or phase not in COORDINATE_PHASES
        or isinstance(ordinal, bool)
        or type(ordinal) is not int
        or ordinal < 0
        or ordinal >= len(_COORDINATES_BY_PHASE.get(phase, ()))
        or record.get("coordinate")
        != list(_COORDINATES_BY_PHASE[phase][ordinal])
        or record.get("coordinate_manifest_sha256")
        != _coordinate_manifest_sha256(phase)
        or record.get("authority_domain") != AUTHORITY_DOMAIN
    ):
        raise ValueError("production coordinate-permit contents are invalid")
    for name in (
        "phase_consumption_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "head_event_sha256",
        "permit_nonce_sha256",
    ):
        _require_sha256(record[name], name=name)
    try:
        datetime.strptime(record["issued_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("production coordinate-permit timestamp is invalid") from error


def issue_next_production_coordinate_permit(
    phase_consumption: ProductionPhaseConsumption,
) -> ProductionCoordinatePermit:
    """Dormant scaffold: runner binding must exist before permit issuance."""

    if type(phase_consumption) is not ProductionPhaseConsumption:
        raise TypeError("coordinate issuance requires phase consumption custody")
    if (
        phase_consumption.record["production_execution_permit_issued"] is not True
        or phase_consumption.record["runner_binding_complete"] is not True
        or phase_consumption.record["scientific_execution_authorized"] is not True
    ):
        raise PermissionError(
            "coordinate execution is unavailable until a typed runner binder exists"
        )
    reverse = {value: key for key, value in _PHASE_AUTHORIZED_STATE.items()}
    phase = reverse.get(phase_consumption.phase)
    if phase not in COORDINATE_PHASES:
        raise PermissionError("phase consumption is not coordinate-bearing")
    directory = _absolute_without_symlink_resolution(
        phase_consumption.artifact_directory
    )
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        _, consumed_path = _authorization_paths(
            directory, phase_consumption.phase
        )
        canonical = _read_json_bounded(consumed_path, MAXIMUM_RECEIPT_BYTES)
        _validate_consumption(canonical)
        if canonical != dict(phase_consumption.record):
            raise PermissionError("phase consumption is not canonical")
        if (
            canonical["plan_sha256"] != snapshot.plan_sha256
            or canonical["campaign_instance_nonce_sha256"]
            != snapshot.campaign_instance_nonce_sha256
            or snapshot.state
            not in (
                _PHASE_AUTHORIZED_STATE[phase],
                _PHASE_RUNNING_STATE[phase],
            )
        ):
            raise PermissionError("coordinate phase is stale or not current")
        ordinal = snapshot.coordinate_progress[phase]
        if ordinal >= len(_COORDINATES_BY_PHASE[phase]):
            raise PermissionError("coordinate phase is already complete")
        issued, consumed = _coordinate_paths(directory, phase, ordinal)
        if issued.exists() or consumed.exists():
            raise FileExistsError("next coordinate already has permit custody")
        body = {
            "schema": COORDINATE_PERMIT_SCHEMA,
            "phase": phase,
            "coordinate_ordinal": ordinal,
            "coordinate": list(_COORDINATES_BY_PHASE[phase][ordinal]),
            "coordinate_manifest_sha256": _coordinate_manifest_sha256(phase),
            "phase_consumption_sha256": phase_consumption.consumption_sha256,
            "plan_sha256": snapshot.plan_sha256,
            "campaign_instance_nonce_sha256": snapshot.campaign_instance_nonce_sha256,
            "head_event_sha256": snapshot.head_event_sha256,
            "permit_nonce_sha256": hashlib.sha256(
                secrets.token_bytes(32)
            ).hexdigest(),
            "issued_timestamp_utc": _timestamp(),
            "authority_domain": AUTHORITY_DOMAIN,
        }
        record = dict(body)
        record["permit_sha256"] = _sha256_json(body)
        _validate_coordinate_permit(record)
        _atomic_exclusive_json(issued, record)
        loaded = _read_json_bounded(issued, MAXIMUM_RECEIPT_BYTES)
        _validate_coordinate_permit(loaded)
        return ProductionCoordinatePermit(
            _COORDINATE_PERMIT_KEY, directory, loaded
        )


def _validate_coordinate_consumption(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "phase",
        "coordinate_ordinal",
        "coordinate",
        "permit_sha256",
        "phase_consumption_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "head_event_sha256",
        "runner_id",
        "consumed_timestamp_utc",
        "authority_domain",
        "consumption_sha256",
    }
    if type(record) is not dict or set(record) != required:
        raise ValueError("production coordinate-consumption schema is invalid")
    body = dict(record)
    claimed = _require_sha256(
        body.pop("consumption_sha256", None), name="coordinate consumption"
    )
    phase = record.get("phase")
    ordinal = record.get("coordinate_ordinal")
    if (
        _sha256_json(body) != claimed
        or record.get("schema") != COORDINATE_CONSUMPTION_SCHEMA
        or phase not in COORDINATE_PHASES
        or isinstance(ordinal, bool)
        or type(ordinal) is not int
        or ordinal < 0
        or ordinal >= len(_COORDINATES_BY_PHASE.get(phase, ()))
        or record.get("coordinate")
        != list(_COORDINATES_BY_PHASE[phase][ordinal])
        or record.get("authority_domain") != AUTHORITY_DOMAIN
        or type(record.get("runner_id")) is not str
        or not record["runner_id"]
        or len(record["runner_id"]) > 256
        or "\x00" in record["runner_id"]
    ):
        raise ValueError("production coordinate-consumption contents are invalid")
    for name in (
        "permit_sha256",
        "phase_consumption_sha256",
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "head_event_sha256",
    ):
        _require_sha256(record[name], name=name)
    try:
        datetime.strptime(
            record["consumed_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except (TypeError, ValueError) as error:
        raise ValueError("production coordinate-consumption timestamp is invalid") from error


def consume_production_coordinate_permit(
    permit: ProductionCoordinatePermit, *, runner_id: str
) -> ProductionCoordinateConsumption:
    if type(permit) is not ProductionCoordinatePermit:
        raise TypeError("coordinate consumption requires a loader-created permit")
    directory = _absolute_without_symlink_resolution(
        permit.artifact_directory
    )
    phase = permit.phase
    ordinal = permit.record["coordinate_ordinal"]
    with _locked_artifact_directory(directory):
        snapshot = _load_snapshot_locked(directory)
        issued_path, consumed_path = _coordinate_paths(directory, phase, ordinal)
        canonical = _read_json_bounded(issued_path, MAXIMUM_RECEIPT_BYTES)
        _validate_coordinate_permit(canonical)
        if consumed_path.exists():
            raise PermissionError("production coordinate permit was already consumed")
        if (
            canonical != dict(permit.record)
            or snapshot.plan_sha256 != permit.record["plan_sha256"]
            or snapshot.campaign_instance_nonce_sha256
            != permit.record["campaign_instance_nonce_sha256"]
            or snapshot.head_event_sha256 != permit.record["head_event_sha256"]
            or snapshot.coordinate_progress[phase] != ordinal
            or snapshot.state
            not in (
                _PHASE_AUTHORIZED_STATE[phase],
                _PHASE_RUNNING_STATE[phase],
            )
        ):
            raise PermissionError("production coordinate permit is stale")
        body = {
            "schema": COORDINATE_CONSUMPTION_SCHEMA,
            "phase": phase,
            "coordinate_ordinal": ordinal,
            "coordinate": list(permit.coordinate),
            "permit_sha256": permit.permit_sha256,
            "phase_consumption_sha256": permit.record[
                "phase_consumption_sha256"
            ],
            "plan_sha256": snapshot.plan_sha256,
            "campaign_instance_nonce_sha256": snapshot.campaign_instance_nonce_sha256,
            "head_event_sha256": snapshot.head_event_sha256,
            "runner_id": runner_id,
            "consumed_timestamp_utc": _timestamp(),
            "authority_domain": AUTHORITY_DOMAIN,
        }
        record = dict(body)
        record["consumption_sha256"] = _sha256_json(body)
        _validate_coordinate_consumption(record)
        _atomic_exclusive_json(consumed_path, record)
        loaded = _read_json_bounded(consumed_path, MAXIMUM_RECEIPT_BYTES)
        _validate_coordinate_consumption(loaded)
        return ProductionCoordinateConsumption(
            _COORDINATE_CONSUMPTION_KEY, directory, loaded
        )


def _status_payload(snapshot: ProductionOrderSnapshot) -> Dict[str, Any]:
    return {
        "schema": "heterodiff-a1-finite-association-production-order-status-v1",
        "authority_domain": AUTHORITY_DOMAIN,
        "artifact_directory": os.fspath(snapshot.artifact_directory),
        "plan_sha256": snapshot.plan_sha256,
        "campaign_instance_nonce_sha256": snapshot.campaign_instance_nonce_sha256,
        "state": snapshot.state,
        "head_event_sha256": snapshot.head_event_sha256,
        "event_count": snapshot.event_count,
        "coordinate_progress": dict(snapshot.coordinate_progress),
        "production_execution_authorized": False,
        "runner_integration_complete": False,
        "compute_started_by_status": False,
    }


__all__ = [
    "AUTHORITY_DOMAIN",
    "ARTIFACT_DIRECTORY_NAME",
    "ARTIFACT_RELATIVE_PATH",
    "AUTHORIZATION_STATES",
    "COMPLETE_SAMPLED_COORDINATES",
    "CONTROL_COORDINATES",
    "COORDINATE_PHASES",
    "DEFAULT_SOURCE_PATHS",
    "EXACT_COORDINATES",
    "FROZEN_RUNTIME_CONTRACT",
    "ORDERED_STATES",
    "PRIMARY_COORDINATES",
    "PREREQUISITE_EVIDENCE_TYPE_V2",
    "PRODUCTION_RUNTIME_CONTRACT_SCHEMA_V2",
    "PRODUCTION_SOURCE_MANIFEST_SCHEMA",
    "RUNTIME_OBSERVATION_SCHEMA",
    "ProductionOrderSnapshot",
    "ProductionPhaseAuthorization",
    "ProductionPhaseConsumption",
    "ProductionVerifiedPrerequisite",
    "TERMINAL_STATES",
    "canonical_artifact_directory",
    "capture_production_runtime_preflight",
    "consume_production_phase_authorization",
    "initialize_production_order_plan",
    "frozen_production_runtime_contract_sha256",
    "frozen_production_source_manifest",
    "issue_production_phase_authorization",
    "load_production_order_snapshot",
    "load_production_phase_authorization",
    "load_production_phase_consumption",
    "load_production_prerequisite_evidence",
    "open_production_rank_phase",
    "revalidate_production_prerequisite",
    "source_path_identity",
    "terminalize_production_order",
    "validate_production_runtime_observation",
    "validate_production_runtime_observation_v2",
    "verify_and_commit_production_prerequisite",
]
