"""Torch-free evidence reconstruction for the atomic-counting smoke gate.

This module is deliberately downstream of training.  It never imports Torch,
starts a training run, or turns a checkpoint into a claim.  Instead it accepts
four immutable artifacts from each completed domain run, a canonical executor
receipt, and a separate canonical audit report.  It then rebuilds the generated
source fixture, lossless counting grid, conditioning tasks, and all deterministic
contract digests from the production NumPy adapters.

The public evidence core and the private run-attestation envelope are separate
objects.  Runtime and peak-RSS observations are nondeterministic and therefore
cannot participate in the byte-identical independently rebuilt core.  They are
range-checked and content-bound in the private envelope.  Likewise, the public
core proves that both tasks remain in one natural group but never publishes the
group identifier.  The identifier appears only in the owner-only envelope.

Publication stages a complete directory, fsyncs every file and directory, and
uses an admitted kernel no-replace rename primitive.  There is no overwrite or
unsafe rename fallback.  Repository import state remains ``NOT_EXECUTED``;
calling the publisher requires explicit completed-run inputs.

The production surface rejects the exact synthetic checkpoint marker and
performs a bounded structural check for a ``torch.save``-style archive without
importing Torch.  That check and the frozen argv schemas support reproducible
procedure and internal consistency; they do not authenticate a hostile
producer.  Artifact custody, run provenance, and reviewer independence remain
separate procedural-audit assumptions.  This publisher is not a trust root.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
from enum import Enum
import errno
import hashlib
import io
import json
import math
from numbers import Integral, Real
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
import struct
import sys
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union
import unicodedata
import zipfile

import numpy as np

from heterodiff.cross_domain_gate.counting_windows import (
    CountingDomainTaskSet,
    build_m_acg_1_task_set,
    build_p_acg_1_task_set,
)
from heterodiff.data.atomic_counting_grid import AtomicCountingGridTensor
from heterodiff.data.cross_domain_counting_fixtures import (
    M_ACG_1_MIDI_PARSE_LIMITS,
    CountingFixtureDomain,
    CountingFixtureResult,
    build_m_acg_1,
    build_p_acg_1,
)


PathLike = Union[str, os.PathLike]

EVIDENCE_EXECUTION_STATUS = "NOT_EXECUTED"
EVIDENCE_EXECUTION_BLOCKER = (
    "No completed music and clinical-style run artifacts, canonical executor "
    "receipts, and independent PASS audit reports have been supplied."
)

_RUN_RECEIPT_SCHEMA = "heterodiff-cross-domain-completed-run-receipt-v1"
_AUDIT_SCHEMA = "heterodiff-cross-domain-independent-audit-v1"
_PUBLIC_SCHEMA = "heterodiff-cross-domain-public-evidence-core-v1"
_PRIVATE_SCHEMA = "heterodiff-cross-domain-private-run-attestation-v1"
_ROOT_SCHEMA = "heterodiff-cross-domain-evidence-publication-v1"
_TRAINING_MANIFEST_FORMAT = (
    "heterodiff-atomic-counting-restart-comparison-v1"
)
_TRAINING_CONFIG_FORMAT = "heterodiff-atomic-counting-training-v1"
_BINDINGS_FORMAT = "heterodiff-atomic-counting-bindings-v1"
_TASK_BUNDLE_FORMAT = "heterodiff-atomic-counting-training-tasks-v1"
_CHECKPOINT_FORMAT = "heterodiff-atomic-counting-checkpoint-v1"
_CHECKPOINT_MAGIC = b"HACGCP1\x00"
_CHECKPOINT_HEADER_BYTES = 4
_SYNTHETIC_CHECKPOINT_PAYLOAD = (
    b"SYNTHETIC_TEST_ONLY:not-a-torch-checkpoint"
)
_GENESIS = "genesis"
_GATE_ID = "heterodiff-cross-domain-atomic-counting-reference-gate-v1"

_MAX_JSON_BYTES = 256 * 1024 * 1024
_MAX_RECEIPT_BYTES = 2 * 1024 * 1024
_MAX_AUDIT_BYTES = 2 * 1024 * 1024
_MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024
_MAX_LOG_BYTES = 2 * 1024 * 1024
_MAX_OUTPUT_BYTES = 256 * 1024 * 1024
_MAX_RSS_BYTES = 2 * 1024 * 1024 * 1024
_MAX_RUNTIME_SECONDS = 120.0
_MAX_STATE_NODES = 100_000
_MAX_TENSOR_ELEMENTS = 20_000_000

_REQUIRED_BINDING_KEYS = frozenset(
    {
        "schema",
        "task",
        "corruption",
        "model",
        "loss",
        "training_config",
        "source_fixture",
        "converted_state",
        "tensor",
        "split_group_policy",
        "train_transform",
        "code_source",
        "dependency_lock",
        "environment_manifest",
        "gate_id",
        "gate_spec",
    }
)

_COMPARISON_FIELDS = (
    "step_losses_float32_bytes",
    "model_parameters_float32_bytes",
    "optimizer_state",
    "scheduler_state",
    "completed_step",
    "ordered_task_sampler_state",
    "corruption_generator_state",
    "global_cpu_torch_rng_state",
)

_FALSIFICATION_CHECKS = (
    "01_source_coverage",
    "02_exact_counts",
    "03_round_trip",
    "04_identifier_free_state",
    "05_schema_integrity",
    "06_mask_separation",
    "07_padding",
    "08_capacity",
    "09_native_support",
    "10_canonical_persistence",
    "11_corruption_draw_order_and_full_shape",
    "12_task_split_integrity",
    "13_count_two_nontriviality",
    "14_absent_mark_presence_nontriviality",
    "15_continuous_branch_nontriviality",
    "16_rng_isolation",
    "17_checkpoint_integrity_and_failure_atomicity",
    "18_fresh_process_restart_bitwise_equality",
    "19_predeclared_resource_bounds",
    "20_public_private_schema_and_atomic_publication",
)

_PUBLIC_FORBIDDEN_KEYS = frozenset(
    {
        "record_id",
        "patient_id",
        "sample_id",
        "group_id",
        "event_id",
        "event_ids",
        "source_path",
        "absolute_path",
        "raw_row",
        "raw_rows",
        "raw_value",
        "patient_value",
        "reversible_pseudonym",
    }
)

_KNOWN_PRIVATE_PUBLIC_IDENTIFIERS = (
    "900001",
    "synthetic-maestro-group-1",
)

_SECRET_KEY_FRAGMENTS = (
    "api_key",
    "credential",
    "password",
    "private_key",
    "secret",
    "access_token",
    "refresh_token",
)

_BLOCKED_CLAIMS = (
    "clinical_validity",
    "cross_domain_generalization",
    "ethics_or_dataset_authorization",
    "likelihood_or_elbo_quality",
    "listening_study_result",
    "model_or_sample_quality",
    "official_maestro_experiment",
    "official_physionet_experiment",
)

_PUBLIC_GENERATED_NOTICE = (
    "Both sources are generated representation fixtures only. No official "
    "MAESTRO item, PhysioNet record, patient value, outcome, or official-data "
    "experiment is represented. Fixture checks are not model-quality, clinical, "
    "or cross-domain-generalization results."
)

_BASE_SKIP_REASON = (
    "cross-domain atomic-counting gate requires the pinned Torch extra"
)

_BASE_SKIP_MANIFEST = (
    {
        "count": 1,
        "path": "tests/unit/test_atomic_counting_reference_torch.py",
        "reason": _BASE_SKIP_REASON,
    },
    {
        "count": 1,
        "path": (
            "tests/integration/"
            "test_cross_domain_atomic_counting_training_torch.py"
        ),
        "reason": _BASE_SKIP_REASON,
    },
)

_EXPECTED_BASE_PASSED = 184
_EXPECTED_PINNED_PASSED = 292
_BOOTSTRAP_SCHEMA = "heterodiff-atomic-counting-source-bootstrap-v1"
_BOOTSTRAP_RELATIVE_PATH = (
    "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py"
)

_BASE_TEST_COMMAND = (
    "python3",
    "-S",
    "-s",
    "-B",
    _BOOTSTRAP_RELATIVE_PATH,
    "focused-pytest",
    "base",
)

_PINNED_TEST_COMMAND = (
    ".venv-m1/bin/python",
    "-S",
    "-s",
    "-B",
    _BOOTSTRAP_RELATIVE_PATH,
    "focused-pytest",
    "pinned",
)

_BASE_INTERPRETER_IDENTITY = MappingProxyType(
    {
        "implementation": "CPython",
        "resolved_executable_sha256": (
            "b82a1dcaab6a6deae7a574bdbad8e5299909930664cb585f4a0116b905131582"
        ),
        "resolved_executable_size_bytes": 4_003_360,
        "version": "3.9.13",
    }
)

_PINNED_INTERPRETER_IDENTITY = MappingProxyType(
    {
        "implementation": "CPython",
        "resolved_executable_sha256": (
            "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
        ),
        "resolved_executable_size_bytes": 152_624,
        "version": "3.11.5",
    }
)

_STATIC_ENFORCEMENT_STAGES = {
    "batch_size": "configuration-preflight-before-training",
    "checkpoint_bytes": "preflight-before-checkpoint-decode-or-publication",
    "declared_axes": "preflight-before-dense-grid-allocation",
    "field_dimensions": "preflight-before-dense-grid-allocation",
    "log_bytes": "preflight-before-log-publication",
    "output_bytes": "preflight-before-output-publication",
    "parameter_count": "preflight-before-parameter-allocation",
    "parsed_source_items": "streaming-before-accepting-next-item",
    "semantic_occurrences": "streaming-before-accepting-next-occurrence",
    "slot_capacity": "preflight-before-grid-and-target-allocation",
    "source_bytes": "preflight-before-source-parse",
    "worker_processes": "configuration-preflight-before-training",
}

_REVIEW_PROTOCOL_TEXT = (
    "Independent adversarial review must examine representation correctness, "
    "conditioning leakage, stochastic corruption, loss normalization, RNG "
    "isolation, checkpoint integrity and replay, resource enforcement, public "
    "redaction, claim boundaries, and durable no-replace publication. Any "
    "unresolved scientific, integrity, privacy, or resource finding is HOLD."
)

_POLICY_TEXT = {
    CountingFixtureDomain.MUSIC: (
        "Parse the digest-locked generated format-0 PPQ MIDI with bounded raw "
        "limits; apply frozen FIFO note semantics; retain every admitted note "
        "onset as one finite-counting occurrence on the two-atom MIDI-clock "
        "grid; retain velocity and onset-offset marks and exact private source "
        "provenance; reject truncation, aggregation, and official-data claims."
    ),
    CountingFixtureDomain.CLINICAL_STYLE: (
        "Parse the digest-locked generated strict UTF-8/LF PhysioNet-2012-style "
        "CSV with bounded streaming limits; treat admission descriptors only "
        "as context; retain every admitted observation row as one finite-counting "
        "occurrence on the minute grid; apply the frozen -1 missing-value rules; "
        "retain exact private row provenance; reject official-patient and "
        "clinical-validity claims."
    ),
}

_IMPLEMENTATION_PATHS = {
    CountingFixtureDomain.MUSIC: (
        "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py",
        "src/heterodiff/data/midi_raw.py",
        "src/heterodiff/data/maestro_semantics.py",
        "src/heterodiff/data/cross_domain_counting_fixtures.py",
        "src/heterodiff/data/atomic_counting_grid.py",
        "src/heterodiff/data/atomic_counting_reference.py",
        "src/heterodiff/cross_domain_gate/counting_windows.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_reference_torch.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_training_torch.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_training_worker_torch.py",
    ),
    CountingFixtureDomain.CLINICAL_STYLE: (
        "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py",
        "src/heterodiff/data/physionet_2012_raw.py",
        "src/heterodiff/data/physionet_2012_adapter.py",
        "src/heterodiff/data/cross_domain_counting_fixtures.py",
        "src/heterodiff/data/atomic_counting_grid.py",
        "src/heterodiff/data/atomic_counting_reference.py",
        "src/heterodiff/cross_domain_gate/counting_windows.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_reference_torch.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_training_torch.py",
        "src/heterodiff/cross_domain_gate/atomic_counting_training_worker_torch.py",
    ),
}

_DOMAIN_SEEDS = {
    CountingFixtureDomain.MUSIC: (3201, 3203, 3209),
    CountingFixtureDomain.CLINICAL_STYLE: (3301, 3303, 3309),
}

_TASK_INDEX_SEQUENCE = {
    CountingFixtureDomain.MUSIC: (1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0),
    CountingFixtureDomain.CLINICAL_STYLE: (0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1),
}


class AtomicCountingEvidenceError(RuntimeError):
    """Base class for evidence reconstruction and publication failures."""


class AtomicCountingEvidenceInputError(AtomicCountingEvidenceError):
    """An input artifact, receipt, or audit report is invalid."""


class AtomicCountingEvidencePrerequisiteError(AtomicCountingEvidenceError):
    """A required preregistered check or independent review is not PASS."""


class AtomicCountingEvidencePublicationError(AtomicCountingEvidenceError):
    """A staged evidence directory cannot be durably published."""


class AtomicCountingAtomicCommitUnsupportedError(
    AtomicCountingEvidencePublicationError
):
    """The host lacks an admitted atomic no-replace directory primitive."""


class AtomicCountingDurabilityUnconfirmedError(
    AtomicCountingEvidencePublicationError
):
    """Publication became visible but the parent-directory fsync failed."""

    def __init__(
        self, message: str, result: "EvidencePublicationResult"
    ) -> None:
        super().__init__(message)
        self.result = result


class _EvidencePreparationMode(Enum):
    """Internal caller-selected mode; artifact fields never select it."""

    PRODUCTION = "production"
    SYNTHETIC_TEST = "synthetic_test"


@dataclass(frozen=True)
class CompletedDomainRun:
    """Filesystem inputs for one completed, separately audited domain run."""

    domain: CountingFixtureDomain
    continuous_manifest: PathLike
    prefix_manifest: PathLike
    resumed_manifest: PathLike
    checkpoint: PathLike
    run_receipt: PathLike
    audit_report: PathLike

    def __post_init__(self) -> None:
        if type(self.domain) is not CountingFixtureDomain:
            raise TypeError("domain must be an exact CountingFixtureDomain value")
        normalized = []
        for name in (
            "continuous_manifest",
            "prefix_manifest",
            "resumed_manifest",
            "checkpoint",
            "run_receipt",
            "audit_report",
        ):
            value = getattr(self, name)
            if not isinstance(value, (str, os.PathLike)):
                raise TypeError("{} must be path-like".format(name))
            path = Path(value)
            if not path.name or path.name in {".", ".."}:
                raise ValueError("{} must name one file".format(name))
            object.__setattr__(self, name, path)
            normalized.append(path)
        if len({os.fspath(path) for path in normalized}) != len(normalized):
            raise ValueError("completed-run input paths must be distinct")


@dataclass(frozen=True)
class PreparedCrossDomainEvidence:
    """Complete canonical publication tree held in memory before any write."""

    files: Mapping[str, bytes]
    execution_class: str
    public_bundle_digests: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.execution_class not in (
            "SYNTHETIC_TEST_ONLY",
            "EVIDENCE_COMPLETE_AWAITING_GATE_DECISION",
        ):
            raise ValueError("unknown evidence execution class")
        if type(self.files) is not dict or not self.files:
            raise TypeError("files must be a nonempty plain dictionary")
        copied: Dict[str, bytes] = {}
        for path, payload in self.files.items():
            _validate_relative_artifact_path(path)
            if type(payload) is not bytes:
                raise TypeError("prepared evidence payloads must be exact bytes")
            copied[path] = bytes(payload)
        expected = {
            "manifest.json",
            "public/music.json",
            "public/clinical_style.json",
            "private/music-run-attestation.json",
            "private/clinical_style-run-attestation.json",
        }
        if set(copied) != expected:
            raise ValueError("prepared evidence has missing or unknown files")
        if sum(len(value) for value in copied.values()) > _MAX_OUTPUT_BYTES:
            raise AtomicCountingEvidenceInputError(
                "prepared evidence exceeds the output byte ceiling"
            )
        object.__setattr__(self, "files", MappingProxyType(copied))
        digests = dict(self.public_bundle_digests)
        if set(digests) != {"music", "clinical_style"}:
            raise ValueError("public bundle digest mapping is incomplete")
        for name, value in digests.items():
            _require_sha256(value, name="{} bundle digest".format(name))
        object.__setattr__(
            self, "public_bundle_digests", MappingProxyType(digests)
        )


@dataclass(frozen=True)
class EvidencePublicationResult:
    output_directory: Path
    status: str
    atomic_backend: str
    execution_class: str
    manifest_sha256: str
    manifest_size_bytes: int
    public_bundle_digests: Mapping[str, str]


@dataclass(frozen=True)
class EvidenceVerificationResult:
    output_directory: Path
    status: str
    execution_class: str
    manifest_sha256: str
    public_bundle_digests: Mapping[str, str]


@dataclass(frozen=True)
class _AtomicBackend:
    name: str
    function: object
    flag: int


@dataclass(frozen=True)
class _TensorRecord:
    dtype: str
    shape: Tuple[int, ...]
    data: bytes


@dataclass(frozen=True)
class _ValidatedDomain:
    domain: CountingFixtureDomain
    preparation_mode: _EvidencePreparationMode
    deterministic_core: Mapping[str, object]
    private_envelope: Mapping[str, object]
    public_bundle_digest: str
    forbidden_public_identifiers: Tuple[str, ...]


def repository_evidence_status() -> Mapping[str, str]:
    """Return the honest import-time state; this function performs no I/O."""

    return MappingProxyType(
        {
            "status": EVIDENCE_EXECUTION_STATUS,
            "blocker": EVIDENCE_EXECUTION_BLOCKER,
        }
    )


def _project_root() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise AtomicCountingEvidenceInputError(
            "value is not canonical-JSON serializable"
        ) from error
    return text.encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AtomicCountingEvidenceInputError(
            "{} must be a lowercase SHA-256 digest".format(name)
        )
    return value


def _plain_int(
    value: object, *, name: str, minimum: int = 0, maximum: int = 2**63 - 1
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise AtomicCountingEvidenceInputError("{} must be an integer".format(name))
    result = int(value)
    if result < minimum or result > maximum:
        raise AtomicCountingEvidenceInputError(
            "{} must lie in [{}, {}]".format(name, minimum, maximum)
        )
    return result


def _finite_real(
    value: object,
    *,
    name: str,
    minimum: float = 0.0,
    maximum: float = float("inf"),
    strictly_positive: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AtomicCountingEvidenceInputError("{} must be real".format(name))
    result = float(value)
    if (
        not math.isfinite(result)
        or result < minimum
        or result > maximum
        or (strictly_positive and result <= 0.0)
    ):
        raise AtomicCountingEvidenceInputError(
            "{} is outside its finite admitted range".format(name)
        )
    return result


def _expect_keys(value: object, expected: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise AtomicCountingEvidenceInputError(
            "{} must be a plain JSON object".format(name)
        )
    expected_set = set(expected)
    actual = set(value)
    if actual != expected_set:
        missing = sorted(expected_set - actual)
        extra = sorted(actual - expected_set)
        raise AtomicCountingEvidenceInputError(
            "{} has invalid fields (missing={}, extra={})".format(
                name, missing, extra
            )
        )
    return value


def _strict_json_bytes(raw: bytes, *, name: str) -> object:
    def reject_constant(value: str) -> None:
        raise AtomicCountingEvidenceInputError(
            "{} contains non-standard JSON constant {}".format(name, value)
        )

    def object_pairs(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise AtomicCountingEvidenceInputError(
                    "{} contains duplicate key {!r}".format(name, key)
                )
            result[key] = value
        return result

    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except UnicodeDecodeError as error:
        raise AtomicCountingEvidenceInputError(
            "{} is not strict UTF-8".format(name)
        ) from error
    except json.JSONDecodeError as error:
        raise AtomicCountingEvidenceInputError(
            "{} is not valid JSON".format(name)
        ) from error
    if _canonical_json_bytes(value) != raw:
        raise AtomicCountingEvidenceInputError(
            "{} is not the exact canonical JSON encoding".format(name)
        )
    _reject_secret_or_timestamp_keys(value, name=name)
    return value


def _reject_secret_or_timestamp_keys(value: object, *, name: str) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise AtomicCountingEvidenceInputError(
                    "{} contains a non-string JSON key".format(name)
                )
            lowered = key.lower()
            if "timestamp" in lowered or any(
                fragment in lowered for fragment in _SECRET_KEY_FRAGMENTS
            ):
                raise AtomicCountingEvidenceInputError(
                    "{} contains forbidden secret/timestamp field {!r}".format(
                        name, key
                    )
                )
            _reject_secret_or_timestamp_keys(item, name=name)
    elif type(value) is list:
        for item in value:
            _reject_secret_or_timestamp_keys(item, name=name)


def _reject_public_fields(
    value: object,
    *,
    name: str = "public evidence",
    forbidden_identifiers: Sequence[str] = (),
) -> None:
    identifiers = tuple(
        sorted(
            set(_KNOWN_PRIVATE_PUBLIC_IDENTIFIERS).union(forbidden_identifiers)
        )
    )

    def reject_identifier(item: object) -> None:
        if type(item) is str:
            if any(identifier in item for identifier in identifiers):
                raise AtomicCountingEvidenceInputError(
                    "{} exposes a forbidden public identifier value".format(
                        name
                    )
                )
            if _contains_absolute_or_home_path(item):
                raise AtomicCountingEvidenceInputError(
                    "{} exposes an absolute or home path value".format(name)
                )
        if type(item) is int and any(
            identifier.isdecimal() and item == int(identifier)
            for identifier in identifiers
        ):
            raise AtomicCountingEvidenceInputError(
                "{} exposes a forbidden public numeric identifier".format(name)
            )
        if type(item) is float and item.is_integer() and any(
            identifier.isdecimal() and int(item) == int(identifier)
            for identifier in identifiers
        ):
            raise AtomicCountingEvidenceInputError(
                "{} exposes a forbidden public numeric identifier".format(name)
            )

    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise AtomicCountingEvidenceInputError(
                    "{} contains a non-string public key".format(name)
                )
            if key.lower() in _PUBLIC_FORBIDDEN_KEYS:
                raise AtomicCountingEvidenceInputError(
                    "{} exposes forbidden public field {!r}".format(name, key)
                )
            reject_identifier(key)
            _reject_public_fields(
                item,
                name=name,
                forbidden_identifiers=identifiers,
            )
    elif type(value) in (list, tuple):
        for item in value:
            _reject_public_fields(
                item,
                name=name,
                forbidden_identifiers=identifiers,
            )
    else:
        reject_identifier(value)


def _contains_absolute_or_home_path(value: str) -> bool:
    """Recognize path tokens without banning legitimate relative-path strings.

    Frozen public argv and source manifests intentionally contain canonical
    project-relative paths such as ``src/heterodiff/...``.  Ordinary prose also
    contains slash compounds such as ``publisher/verifier``.  An absolute path,
    however, begins either at the start of a string or after a token boundary;
    this covers POSIX paths and file URIs, Windows drive paths, UNC paths, and
    shell home shorthands while preserving those admitted relative strings.
    """

    if type(value) is not str:
        raise TypeError("public path candidate must be a string")

    def at_boundary(index: int) -> bool:
        if index == 0:
            return True
        previous = value[index - 1]
        return not (previous.isalnum() or previous in "._~-")

    for index, character in enumerate(value):
        if not at_boundary(index):
            continue
        if character == "/":
            return True
        if character == "~":
            tail = value[index + 1 :]
            separator = min(
                (
                    position
                    for position in (tail.find("/"), tail.find("\\"))
                    if position >= 0
                ),
                default=-1,
            )
            if separator >= 0 and all(
                item.isalnum() or item in "._-" for item in tail[:separator]
            ):
                return True
        if (
            character.isascii()
            and character.isalpha()
            and index + 2 < len(value)
            and value[index + 1] == ":"
            and value[index + 2] in "/\\"
        ):
            return True
        if character == "\\" and value[index : index + 2] == "\\\\":
            return True
    return False


def _validate_relative_artifact_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise AtomicCountingEvidencePublicationError(
            "artifact path must be a nonempty canonical relative string"
        )
    path = Path(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise AtomicCountingEvidencePublicationError(
            "artifact path must not be absolute or traverse directories"
        )
    if value != path.as_posix():
        raise AtomicCountingEvidencePublicationError(
            "artifact path must use canonical POSIX separators"
        )
    return value


def _reject_symlink_components(path: Path, *, final_must_exist: bool) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for index, part in enumerate(absolute.parts[1:]):
        current = current / part
        final = index == len(absolute.parts[1:]) - 1
        try:
            status = current.lstat()
        except FileNotFoundError:
            if final and not final_must_exist:
                return
            raise AtomicCountingEvidenceInputError(
                "path component does not exist: {}".format(current)
            )
        if stat.S_ISLNK(status.st_mode):
            raise AtomicCountingEvidenceInputError(
                "input/output paths must not contain symlink components"
            )


def _file_observation(status: os.stat_result) -> Tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _read_verified_file(path: Path, *, limit: int, name: str) -> bytes:
    _reject_symlink_components(path, final_must_exist=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        named = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(named.st_mode)
            or _file_observation(before) != _file_observation(named)
        ):
            raise AtomicCountingEvidenceInputError(
                "{} is not one stable regular file".format(name)
            )
        if before.st_size > limit:
            raise AtomicCountingEvidenceInputError(
                "{} exceeds its byte ceiling".format(name)
            )
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingEvidenceInputError(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingEvidenceInputError(
                "{} grew while reading".format(name)
            )
        after = os.fstat(descriptor)
        if _file_observation(after) != _file_observation(before):
            raise AtomicCountingEvidenceInputError(
                "{} changed while reading".format(name)
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _load_json_file(path: Path, *, limit: int, name: str) -> Tuple[bytes, dict]:
    raw = _read_verified_file(path, limit=limit, name=name)
    value = _strict_json_bytes(raw, name=name)
    if type(value) is not dict:
        raise AtomicCountingEvidenceInputError(
            "{} must contain one JSON object".format(name)
        )
    return raw, value


def _relative_command(value: object, *, name: str) -> Tuple[str, ...]:
    if type(value) is not list or not value or len(value) > 64:
        raise AtomicCountingEvidenceInputError(
            "{} must be a bounded argv list".format(name)
        )
    result = []
    for token in value:
        if (
            type(token) is not str
            or not token
            or len(token.encode("utf-8")) > 1024
            or "\x00" in token
            or "\n" in token
            or "\r" in token
        ):
            raise AtomicCountingEvidenceInputError(
                "{} contains an invalid argv token".format(name)
            )
        path = Path(token)
        if path.is_absolute() or token.startswith("~"):
            raise AtomicCountingEvidenceInputError(
                "{} must not contain absolute/home paths".format(name)
            )
        result.append(token)
    return tuple(result)


def _expected_training_commands(
    domain: CountingFixtureDomain, checkpoint_sha256: str
) -> Mapping[str, Tuple[str, ...]]:
    """Return the only admitted worker argv for each restart branch."""

    checkpoint_digest = _require_sha256(
        checkpoint_sha256, name="training command checkpoint digest"
    )
    directory = "runs/{}".format(domain.value)
    common = (
        ".venv-m1/bin/python",
        "-S",
        "-s",
        "-B",
        "-W",
        "error",
        _BOOTSTRAP_RELATIVE_PATH,
        "training-worker",
        "--domain",
        domain.value,
    )
    checkpoint = directory + "/step5.ckpt"
    prefix_output = directory + "/prefix.json"
    return MappingProxyType(
        {
            "continuous": common
            + (
                "--mode",
                "continuous",
                "--output",
                directory + "/continuous.json",
            ),
            "prefix": common
            + (
                "--mode",
                "prefix",
                "--output",
                prefix_output,
                "--checkpoint",
                checkpoint,
            ),
            "resume": common
            + (
                "--mode",
                "resume",
                "--output",
                directory + "/resumed.json",
                "--checkpoint",
                checkpoint,
                "--expected-checkpoint-sha",
                checkpoint_digest,
                "--prior-output",
                prefix_output,
            ),
        }
    )


def _source_tree_digest(root: Path) -> str:
    source_root = root / "src" / "heterodiff"
    test_root = root / "tests"
    optional_relatives = (
        ".pytest.ini",
        "conftest.py",
        "pytest.ini",
        "setup.cfg",
        "sitecustomize.py",
        "src/conftest.py",
        "src/sitecustomize.py",
        "src/usercustomize.py",
        "tox.ini",
        "usercustomize.py",
    )
    required_paths = (
        *source_root.rglob("*.py"),
        *test_root.rglob("*.py"),
        root / "pyproject.toml",
    )
    if not required_paths:
        raise AtomicCountingEvidenceInputError("local source tree is empty")
    optional_before = {}
    for relative in optional_relatives:
        path = root / relative
        _reject_symlink_components(path.parent, final_must_exist=True)
        try:
            optional_before[relative] = _file_observation(path.lstat())
        except FileNotFoundError:
            optional_before[relative] = None
    entries = {
        path.relative_to(root).as_posix(): path for path in required_paths
    }
    entries.update(
        {relative: root / relative for relative in optional_relatives}
    )
    digest = hashlib.sha256()
    digest.update(b"heterodiff.atomic-counting-source-test-config-startup-tree.v3\x00")
    for relative_text, path in sorted(entries.items()):
        relative = relative_text.encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        if (
            relative_text in optional_before
            and optional_before[relative_text] is None
        ):
            digest.update(b"\x00")
            continue
        raw = _read_verified_file(
            path, limit=8 * 1024 * 1024, name="implementation source"
        )
        digest.update(b"\x01")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    for relative, before in optional_before.items():
        path = root / relative
        try:
            after = _file_observation(path.lstat())
        except FileNotFoundError:
            after = None
        if after != before:
            raise AtomicCountingEvidenceInputError(
                "optional source/startup configuration changed while hashing"
            )
    return digest.hexdigest()


def _implementation_manifest(
    root: Path, domain: CountingFixtureDomain
) -> Tuple[Mapping[str, object], ...]:
    result = []
    for relative in _IMPLEMENTATION_PATHS[domain]:
        path = root / relative
        raw = _read_verified_file(
            path, limit=8 * 1024 * 1024, name="implementation source"
        )
        result.append(
            {
                "path": relative,
                "sha256": _sha256(raw),
                "size_bytes": len(raw),
            }
        )
    return tuple(result)


def _configuration_payload(fixture: CountingFixtureResult) -> Mapping[str, object]:
    configuration = fixture.configuration
    configuration.validate()
    assert configuration.observed is not None
    events = []
    for event, observation in zip(
        configuration.events, configuration.observed.events
    ):
        events.append(
            {
                "event_time": event.event_time,
                "event_type": event.event_type,
                "marks": {
                    name: list(values) for name, values in sorted(event.marks.items())
                },
                "source_observed_marks": sorted(observation.observed_marks),
                "source_time_observed": observation.time_observed,
                "source_type_observed": observation.type_observed,
            }
        )
    return {
        "cardinality_observed": configuration.observed.cardinality_observed,
        "events": events,
        "fixture_id": fixture.fixture_id,
        "schema_version": configuration.schema.version,
    }


def _configuration_payload_digest(fixture: CountingFixtureResult) -> str:
    return _domain_digest(
        "heterodiff.atomic-counting.evidence-configuration-payload.v1",
        _configuration_payload(fixture),
    )


def _array_manifest(name: str, value: np.ndarray) -> Mapping[str, object]:
    if type(value) is not np.ndarray or not value.flags.c_contiguous:
        value = np.array(value, copy=True, order="C")
    return {
        "dtype": value.dtype.str,
        "name": name,
        "shape": list(value.shape),
    }


def _grid_arrays(
    grid: AtomicCountingGridTensor,
) -> Tuple[Tuple[str, np.ndarray], ...]:
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


def _binary_array_digest(
    domain_tag: str,
    header: Mapping[str, object],
    arrays: Sequence[Tuple[str, np.ndarray]],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain_tag.encode("ascii"))
    digest.update(b"\x00")
    header_bytes = _canonical_json_bytes(header)
    digest.update(len(header_bytes).to_bytes(8, "big"))
    digest.update(header_bytes)
    for name, value in arrays:
        contiguous = np.array(value, copy=True, order="C")
        if contiguous.dtype.kind == "f":
            if np.any(~np.isfinite(contiguous)):
                raise AtomicCountingEvidenceInputError(
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


def _grid_payload_digest(grid: AtomicCountingGridTensor) -> str:
    return _binary_array_digest(
        "heterodiff.atomic-counting.evidence-grid-payload.v1",
        {
            "cardinality_observed": grid.cardinality_observed,
            "number_of_event_types": grid.number_of_event_types,
            "number_of_time_atoms": grid.number_of_time_atoms,
            "slot_capacity": grid.slot_capacity,
        },
        _grid_arrays(grid),
    )


def _model_shape_contract(
    task_set: CountingDomainTaskSet,
) -> Mapping[str, object]:
    target = task_set.target
    r = target.layout.reference_length
    k = target.layout.number_of_types
    s = target.layout.slot_capacity
    presence = len(target.layout.field_coordinates)
    continuous = len(target.layout.transformed_coordinates)
    indices = tuple(
        target.layout.field_coordinates.index(coordinate)
        for coordinate in target.layout.transformed_coordinates
    )
    input_width = (
        4
        + 3 * s * presence
        + s * continuous
        + s * presence
        + 1
        + s
        + 1
        + 1
        + 8
        + 3
        + 1
    )
    parameter_count = (
        k * 8
        + input_width * 64
        + 64
        + 64 * 32
        + 32
        + 32 * 3
        + 3
        + (s * presence) * (32 * 2 + 2)
        + (s * continuous) * (32 + 1)
    )
    return {
        "continuous_presence_indices": list(indices),
        "input_width": input_width,
        "number_of_continuous_coordinates": continuous,
        "number_of_event_types": k,
        "number_of_presence_coordinates": presence,
        "parameter_budget": 250_000,
        "parameter_count": parameter_count,
        "reference_positions": r,
        "shape_signature": [r, k, s, presence, continuous, list(indices)],
        "slot_capacity": s,
        "type_embedding_width": 8,
        "trunk_widths": [64, 32],
    }


def _torch_target_payload_digest(task_set: CountingDomainTaskSet) -> str:
    """Digest the exact NumPy bytes consumed by the Torch target constructor.

    The conversion mirrors ``AtomicCountingReferenceTarget.from_encoded_reference``
    without importing Torch.  It is deliberately not the configuration digest or
    the native-grid digest.
    """

    target = task_set.target
    model = _model_shape_contract(task_set)
    r = int(model["reference_positions"])
    k = int(model["number_of_event_types"])
    s = int(model["slot_capacity"])
    presence = int(model["number_of_presence_coordinates"])
    indices = tuple(int(value) for value in model["continuous_presence_indices"])
    template = np.zeros((k, s, presence), dtype=np.bool_)
    field_index = {
        coordinate: index
        for index, coordinate in enumerate(target.layout.field_coordinates)
    }
    for type_index, event_type in enumerate(target.layout.schema.event_types):
        for field in event_type.fields:
            for coordinate in range(field.dimension):
                template[
                    type_index, :, field_index[(field.name, coordinate)]
                ] = True
    structural = np.zeros((r, k, s, presence), dtype=np.bool_)
    structural[target.valid_time_mask] = template
    mapped_source = target.source_observed[..., indices]
    if not np.array_equal(mapped_source, target.transformed_source_observed):
        raise AtomicCountingEvidenceInputError(
            "native/transformed source-observation axes disagree"
        )

    task_records = []
    for task in task_set.tasks:
        arrays = (
            ("clean_count", target.exact_counts[np.newaxis, ...].astype(np.int64)),
            ("clean_presence", target.clean_presence[np.newaxis, ...]),
            (
                "transformed_mark",
                target.transformed_mark_values[np.newaxis, ...].astype(np.float32),
            ),
            ("structural_applicable", structural[np.newaxis, ...]),
            ("source_observed", target.source_observed[np.newaxis, ...]),
            ("valid_time", target.valid_time_mask[np.newaxis, ...]),
            (
                "anchor_count",
                task.raster.anchor_count[np.newaxis, ...].astype(np.int64),
            ),
            (
                "anchor_count_observed",
                task.raster.anchor_count_observed[np.newaxis, ...],
            ),
        )
        tensors = []
        for name, value in arrays:
            contiguous = np.array(value, copy=True, order="C")
            dtype_name = {
                np.dtype(np.int64): "int64",
                np.dtype(np.bool_): "bool",
                np.dtype(np.float32): "float32",
            }.get(contiguous.dtype)
            if dtype_name is None:
                raise AtomicCountingEvidenceInputError(
                    "Torch-target mirror produced an unsupported dtype"
                )
            tensors.append(
                {
                    "data_sha256": _sha256(contiguous.tobytes(order="C")),
                    "dtype": dtype_name,
                    "name": name,
                    "shape": list(contiguous.shape),
                }
            )
        task_records.append({"task_id": task.task_id.value, "tensors": tensors})
    return _domain_digest(
        "heterodiff.atomic-counting-target-tensor-payload.v1",
        {
            "format": "heterodiff-atomic-counting-target-tensor-payload-v1",
            "model_shape": model["shape_signature"],
            "tasks": task_records,
        },
    )


def _round_trip_digest(
    fixture: CountingFixtureResult,
    grid: AtomicCountingGridTensor,
    configuration_digest: str,
    grid_digest: str,
) -> str:
    decoded = grid.to_configuration()
    source = fixture.configuration
    if decoded.state_key() != source.state_key():
        raise AtomicCountingEvidenceInputError(
            "grid round trip changed identifier-free configuration state"
        )
    if decoded.observed != source.observed:
        raise AtomicCountingEvidenceInputError(
            "grid round trip changed source-observation masks"
        )
    if (
        decoded.sample_id != source.sample_id
        or decoded.group_id != source.group_id
        or tuple(event.event_id for event in decoded.events)
        != tuple(event.event_id for event in source.events)
    ):
        raise AtomicCountingEvidenceInputError(
            "grid round trip changed private provenance sidecars"
        )
    rebuilt = AtomicCountingGridTensor.from_configuration(
        decoded, max_occurrences_per_cell=grid.slot_capacity
    )
    rebuilt_digest = _grid_payload_digest(rebuilt)
    if rebuilt_digest != grid_digest:
        raise AtomicCountingEvidenceInputError(
            "grid round-trip payload bytes are not stable"
        )
    reconstructed = fixture.reconstruct_source_bytes()
    if _sha256(reconstructed) != fixture.source_sha256:
        raise AtomicCountingEvidenceInputError(
            "private source reconstruction changed fixture identity"
        )
    return _domain_digest(
        "heterodiff.atomic-counting.evidence-round-trip.v1",
        {
            "configuration_payload_digest": configuration_digest,
            "grid_payload_digest": grid_digest,
            "private_event_sidecars_preserved": True,
            "private_group_sidecar_preserved": True,
            "private_sample_sidecar_preserved": True,
            "rebuilt_grid_payload_digest": rebuilt_digest,
            "source_reconstruction_sha256": fixture.source_sha256,
        },
    )


def _training_config(domain: CountingFixtureDomain) -> Mapping[str, object]:
    model_seed, task_seed, corruption_seed = _DOMAIN_SEEDS[domain]
    return {
        "adam_epsilon": 1e-8,
        "batch_size": 1,
        "betas": [0.9, 0.999],
        "checkpoint_step": 5,
        "corruption_seed": corruption_seed,
        "domain": domain.value,
        "foreach": False,
        "format": _TRAINING_CONFIG_FORMAT,
        "fused": False,
        "learning_rate": 0.001,
        "maximum_steps": 12,
        "model_seed": model_seed,
        "parameter_budget": 250_000,
        "scheduler_gamma": 0.9,
        "scheduler_step_size": 4,
        "task_seed": task_seed,
        "task_sequence": list(_TASK_INDEX_SEQUENCE[domain]),
        "weight_decay": 0.0,
        "worker_processes": 0,
    }


def _training_config_digest(domain: CountingFixtureDomain) -> str:
    return _domain_digest(
        "heterodiff.atomic-counting-training-config.v1",
        _training_config(domain),
    )


def _task_bundle_digest(
    task_set: CountingDomainTaskSet, model: Mapping[str, object]
) -> str:
    return _domain_digest(
        "heterodiff.atomic-counting-training-tasks.v1",
        {
            "domain": task_set.domain.value,
            "format": _TASK_BUNDLE_FORMAT,
            "model_config": model["shape_signature"],
            "schema_digest": task_set.target.schema_digest,
            "source_fixture_digest": task_set.source_sha256,
            "split_group_policy_digest": task_set.policy_digest,
            "target_state_digest": task_set.target.state_digest,
            "task_ids": ["U", "A"],
            "task_set_digest": task_set.task_set_digest,
        },
    )


def _derived_binding_values(
    *,
    task_set: CountingDomainTaskSet,
    model: Mapping[str, object],
    code_source_digest: str,
    dependency_lock_digest: str,
    environment_manifest_digest: str,
    gate_spec_digest: str,
) -> Mapping[str, str]:
    corruption_mapping = {
        "alpha_bar": 0.8,
        "count_mask_probability": 0.5,
        "draw_order": ["U_count", "U_presence", "Z"],
        "full_shape": True,
        "model_shape": {
            key: model[key]
            for key in (
                "continuous_presence_indices",
                "input_width",
                "number_of_continuous_coordinates",
                "number_of_event_types",
                "number_of_presence_coordinates",
                "parameter_budget",
                "parameter_count",
                "reference_positions",
                "slot_capacity",
                "type_embedding_width",
                "trunk_widths",
            )
        },
        "presence_mask_probability": 0.5,
        "step": 1,
    }
    loss_mapping = {
        "continuous": "enabled-branch-mean-epsilon-mse",
        "count": "0.5-occupied-plus-0.5-empty-cross-entropy",
        "presence": "0.5-positive-plus-0.5-zero-cross-entropy",
        "weights": [1.0, 1.0, 1.0],
    }
    transform_mapping = {
        "fitted": False,
        "positive": "natural-log",
        "real": "identity",
    }
    return {
        "schema": task_set.target.schema_digest,
        "task": task_set.task_set_digest,
        "corruption": _domain_digest(
            "heterodiff.atomic-counting-corruption.v1", corruption_mapping
        ),
        "model": _domain_digest(
            "heterodiff.atomic-counting-model.v1",
            corruption_mapping["model_shape"],
        ),
        "loss": _domain_digest(
            "heterodiff.atomic-counting-loss.v1", loss_mapping
        ),
        "training_config": _training_config_digest(task_set.domain),
        "source_fixture": task_set.source_sha256,
        "converted_state": task_set.target.state_digest,
        "tensor": _torch_target_payload_digest(task_set),
        "split_group_policy": task_set.policy_digest,
        "train_transform": _domain_digest(
            "heterodiff.atomic-counting-transform.v1", transform_mapping
        ),
        "code_source": code_source_digest,
        "dependency_lock": dependency_lock_digest,
        "environment_manifest": environment_manifest_digest,
        "gate_id": _GATE_ID,
        "gate_spec": gate_spec_digest,
    }


def _bindings_digest(bindings: Mapping[str, str]) -> str:
    return _domain_digest(
        "heterodiff.atomic-counting-checkpoint-bindings.v1",
        {"format": _BINDINGS_FORMAT, "values": dict(bindings)},
    )


def _tensor_record(
    value: object,
    *,
    name: str,
    allowed_dtypes: Tuple[str, ...] = (
        "bool",
        "uint8",
        "int64",
        "float32",
        "float64",
    ),
) -> _TensorRecord:
    mapping = _expect_keys(value, {"data_hex", "dtype", "shape"}, name=name)
    dtype_name = mapping["dtype"]
    if type(dtype_name) is not str or dtype_name not in allowed_dtypes:
        raise AtomicCountingEvidenceInputError(
            "{} has unsupported dtype".format(name)
        )
    shape_value = mapping["shape"]
    if type(shape_value) is not list or len(shape_value) > 8:
        raise AtomicCountingEvidenceInputError(
            "{} has an invalid shape".format(name)
        )
    shape = tuple(
        _plain_int(
            dimension,
            name="{} shape".format(name),
            minimum=0,
            maximum=_MAX_TENSOR_ELEMENTS,
        )
        for dimension in shape_value
    )
    elements = math.prod(shape)
    if elements > _MAX_TENSOR_ELEMENTS:
        raise AtomicCountingEvidenceInputError(
            "{} exceeds the tensor element ceiling".format(name)
        )
    data_hex = mapping["data_hex"]
    if type(data_hex) is not str or len(data_hex) % 2:
        raise AtomicCountingEvidenceInputError(
            "{} tensor bytes are not hexadecimal".format(name)
        )
    try:
        data = bytes.fromhex(data_hex)
    except ValueError as error:
        raise AtomicCountingEvidenceInputError(
            "{} tensor bytes are not hexadecimal".format(name)
        ) from error
    sizes = {"bool": 1, "uint8": 1, "int64": 8, "float32": 4, "float64": 8}
    if len(data) != elements * sizes[dtype_name]:
        raise AtomicCountingEvidenceInputError(
            "{} byte length disagrees with dtype and shape".format(name)
        )
    if dtype_name == "bool" and any(byte not in (0, 1) for byte in data):
        raise AtomicCountingEvidenceInputError(
            "{} contains a noncanonical boolean byte".format(name)
        )
    if dtype_name in ("float32", "float64"):
        dtype = np.dtype("<f4" if dtype_name == "float32" else "<f8")
        array = np.frombuffer(data, dtype=dtype)
        if np.any(~np.isfinite(array)):
            raise AtomicCountingEvidenceInputError(
                "{} contains a nonfinite tensor value".format(name)
            )
    return _TensorRecord(dtype_name, shape, data)


def _decode_state_manifest(
    value: object, *, name: str, budget: Optional[list[int]] = None
) -> object:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > _MAX_STATE_NODES:
        raise AtomicCountingEvidenceInputError(
            "{} exceeds the state-tree node ceiling".format(name)
        )
    if type(value) is not dict or type(value.get("kind")) is not str:
        raise AtomicCountingEvidenceInputError(
            "{} is not a state-manifest node".format(name)
        )
    kind = value["kind"]
    if kind == "none":
        _expect_keys(value, {"kind"}, name=name)
        return None
    if kind == "bool":
        mapping = _expect_keys(value, {"kind", "value"}, name=name)
        if type(mapping["value"]) is not bool:
            raise AtomicCountingEvidenceInputError(
                "{} boolean node is invalid".format(name)
            )
        return mapping["value"]
    if kind == "int":
        mapping = _expect_keys(value, {"kind", "value"}, name=name)
        return _plain_int(
            mapping["value"],
            name="{} integer".format(name),
            minimum=-(2**63),
            maximum=2**63 - 1,
        )
    if kind == "float":
        mapping = _expect_keys(value, {"kind", "value"}, name=name)
        if type(mapping["value"]) is not str or len(mapping["value"]) > 128:
            raise AtomicCountingEvidenceInputError(
                "{} float node is invalid".format(name)
            )
        try:
            result = float.fromhex(mapping["value"])
        except ValueError as error:
            raise AtomicCountingEvidenceInputError(
                "{} float node is invalid".format(name)
            ) from error
        if not math.isfinite(result) or result.hex() != mapping["value"]:
            raise AtomicCountingEvidenceInputError(
                "{} float node is nonfinite or noncanonical".format(name)
            )
        return result
    if kind == "str":
        mapping = _expect_keys(value, {"kind", "value"}, name=name)
        if type(mapping["value"]) is not str or len(mapping["value"]) > 1_000_000:
            raise AtomicCountingEvidenceInputError(
                "{} string node is invalid".format(name)
            )
        return mapping["value"]
    if kind == "tensor":
        mapping = _expect_keys(value, {"kind", "value"}, name=name)
        return _tensor_record(mapping["value"], name=name)
    if kind in ("list", "tuple"):
        mapping = _expect_keys(value, {"kind", "items"}, name=name)
        if type(mapping["items"]) is not list or len(mapping["items"]) > _MAX_STATE_NODES:
            raise AtomicCountingEvidenceInputError(
                "{} sequence node is invalid".format(name)
            )
        items = tuple(
            _decode_state_manifest(
                item, name="{}[{}]".format(name, index), budget=budget
            )
            for index, item in enumerate(mapping["items"])
        )
        return items if kind == "tuple" else list(items)
    if kind == "dict":
        mapping = _expect_keys(value, {"kind", "items"}, name=name)
        if type(mapping["items"]) is not list or len(mapping["items"]) > _MAX_STATE_NODES:
            raise AtomicCountingEvidenceInputError(
                "{} mapping node is invalid".format(name)
            )
        result = {}
        for index, item in enumerate(mapping["items"]):
            if type(item) is not list or len(item) != 2:
                raise AtomicCountingEvidenceInputError(
                    "{} mapping item {} is invalid".format(name, index)
                )
            key_manifest, child = item
            if (
                type(key_manifest) is not list
                or len(key_manifest) != 2
                or key_manifest[0] not in ("str", "int")
            ):
                raise AtomicCountingEvidenceInputError(
                    "{} mapping key {} is invalid".format(name, index)
                )
            key = key_manifest[1]
            if key_manifest[0] == "str":
                if type(key) is not str:
                    raise AtomicCountingEvidenceInputError(
                        "{} mapping key must be a string".format(name)
                    )
            else:
                key = _plain_int(
                    key,
                    name="{} mapping key".format(name),
                    minimum=-(2**63),
                    maximum=2**63 - 1,
                )
            if key in result:
                raise AtomicCountingEvidenceInputError(
                    "{} contains a duplicate state key".format(name)
                )
            result[key] = _decode_state_manifest(
                child, name="{}[{!r}]".format(name, key), budget=budget
            )
        return result
    raise AtomicCountingEvidenceInputError(
        "{} has unsupported state kind {!r}".format(name, kind)
    )


def _tensor_scalar_float32(value: object, *, name: str) -> np.float32:
    record = _tensor_record(value, name=name, allowed_dtypes=("float32",))
    if record.shape != ():
        raise AtomicCountingEvidenceInputError(
            "{} must be one float32 scalar".format(name)
        )
    return np.frombuffer(record.data, dtype=np.dtype("<f4"))[0]


def _expected_parameter_shapes(
    model: Mapping[str, object]
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    k = int(model["number_of_event_types"])
    input_width = int(model["input_width"])
    s = int(model["slot_capacity"])
    presence = int(model["number_of_presence_coordinates"])
    continuous = int(model["number_of_continuous_coordinates"])
    result = [
        ("type_embedding.weight", (k, 8)),
        ("first_linear.weight", (64, input_width)),
        ("first_linear.bias", (64,)),
        ("second_linear.weight", (32, 64)),
        ("second_linear.bias", (32,)),
        ("count_head.weight", (3, 32)),
        ("count_head.bias", (3,)),
    ]
    for index in range(s * presence):
        result.extend(
            (
                ("presence_heads.{}.weight".format(index), (2, 32)),
                ("presence_heads.{}.bias".format(index), (2,)),
            )
        )
    for index in range(s * continuous):
        result.extend(
            (
                ("epsilon_heads.{}.weight".format(index), (1, 32)),
                ("epsilon_heads.{}.bias".format(index), (1,)),
            )
        )
    return tuple(result)


def _validate_model_state(value: object, model: Mapping[str, object], *, name: str) -> None:
    decoded = _decode_state_manifest(value, name=name)
    if type(decoded) is not dict:
        raise AtomicCountingEvidenceInputError("{} must decode to a mapping".format(name))
    expected = _expected_parameter_shapes(model)
    if tuple(decoded) != tuple(parameter for parameter, _shape in expected):
        raise AtomicCountingEvidenceInputError(
            "{} parameter names/order differ from the frozen architecture".format(name)
        )
    count = 0
    for parameter, shape in expected:
        record = decoded[parameter]
        if (
            type(record) is not _TensorRecord
            or record.dtype != "float32"
            or record.shape != shape
        ):
            raise AtomicCountingEvidenceInputError(
                "{} parameter {} has the wrong dtype or shape".format(name, parameter)
            )
        count += math.prod(shape)
    if count != model["parameter_count"]:
        raise AtomicCountingEvidenceInputError(
            "{} parameter bytes disagree with static parameter count".format(name)
        )


def _tensor_int64_values(value: _TensorRecord, *, name: str) -> Tuple[int, ...]:
    if value.dtype != "int64":
        raise AtomicCountingEvidenceInputError("{} must be int64".format(name))
    return tuple(int(item) for item in np.frombuffer(value.data, dtype=np.dtype("<i8")))


def _validate_sampler_state(
    value: object,
    *,
    domain: CountingFixtureDomain,
    completed_step: int,
    name: str,
) -> None:
    decoded = _decode_state_manifest(value, name=name)
    expected_keys = {
        "version",
        "dataset_size",
        "seed",
        "epoch",
        "cursor",
        "batches_emitted",
        "permutation",
        "generator_state",
    }
    if type(decoded) is not dict or set(decoded) != expected_keys:
        raise AtomicCountingEvidenceInputError(
            "{} sampler fields are incomplete".format(name)
        )
    task_seed = _DOMAIN_SEEDS[domain][1]
    expected_epoch = 2 if completed_step == 5 else 5
    expected_cursor = 1 if completed_step == 5 else 2
    expected_permutation = (
        _TASK_INDEX_SEQUENCE[domain][4:6]
        if completed_step == 5
        else _TASK_INDEX_SEQUENCE[domain][10:12]
    )
    if (
        decoded["version"] != 1
        or decoded["dataset_size"] != 2
        or decoded["seed"] != task_seed
        or decoded["epoch"] != expected_epoch
        or decoded["cursor"] != expected_cursor
        or decoded["batches_emitted"] != completed_step
    ):
        raise AtomicCountingEvidenceInputError(
            "{} sampler counters differ from deterministic replay".format(name)
        )
    permutation = decoded["permutation"]
    generator = decoded["generator_state"]
    if (
        type(permutation) is not _TensorRecord
        or permutation.shape != (2,)
        or _tensor_int64_values(permutation, name=name) != expected_permutation
        or type(generator) is not _TensorRecord
        or generator.dtype != "uint8"
        or len(generator.data) == 0
        or len(generator.data) > 1_000_000
    ):
        raise AtomicCountingEvidenceInputError(
            "{} sampler tensors differ from deterministic replay".format(name)
        )


def _validate_optimizer_scheduler(
    optimizer: object,
    scheduler: object,
    *,
    model: Mapping[str, object],
    completed_step: int,
    name: str,
) -> None:
    optimizer_state = _decode_state_manifest(optimizer, name=name + ".optimizer")
    scheduler_state = _decode_state_manifest(scheduler, name=name + ".scheduler")
    if (
        type(optimizer_state) is not dict
        or set(optimizer_state) != {"state", "param_groups"}
        or type(optimizer_state["state"]) is not dict
        or type(optimizer_state["param_groups"]) is not list
        or len(optimizer_state["param_groups"]) != 1
    ):
        raise AtomicCountingEvidenceInputError(
            "{} optimizer state is not one AdamW group".format(name)
        )
    parameter_tensors = len(_expected_parameter_shapes(model))
    if set(optimizer_state["state"]) != set(range(parameter_tensors)):
        raise AtomicCountingEvidenceInputError(
            "{} optimizer does not cover every parameter tensor".format(name)
        )
    for index, parameter_state in optimizer_state["state"].items():
        if type(parameter_state) is not dict or not {
            "step",
            "exp_avg",
            "exp_avg_sq",
        } <= set(parameter_state):
            raise AtomicCountingEvidenceInputError(
                "{} AdamW state {} is incomplete".format(name, index)
            )
        for key in ("step", "exp_avg", "exp_avg_sq"):
            if type(parameter_state[key]) is not _TensorRecord:
                raise AtomicCountingEvidenceInputError(
                    "{} AdamW state tensor {} is invalid".format(name, key)
                )
    group = optimizer_state["param_groups"][0]
    if type(group) is not dict:
        raise AtomicCountingEvidenceInputError("{} optimizer group is invalid".format(name))
    required_group = {
        "lr": 0.001 * (0.9 ** (completed_step // 4)),
        "betas": (0.9, 0.999),
        "eps": 1e-8,
        "weight_decay": 0.0,
        "amsgrad": False,
        "maximize": False,
        "foreach": False,
        "capturable": False,
        "differentiable": False,
        "fused": False,
    }
    for key, expected in required_group.items():
        actual = group.get(key)
        if key == "lr":
            if type(actual) is not float or not math.isclose(
                actual, expected, rel_tol=0.0, abs_tol=1e-18
            ):
                raise AtomicCountingEvidenceInputError(
                    "{} optimizer field {} differs".format(name, key)
                )
        elif actual != expected:
            raise AtomicCountingEvidenceInputError(
                "{} optimizer field {} differs".format(name, key)
            )
    if (
        type(scheduler_state) is not dict
        or scheduler_state.get("step_size") != 4
        or scheduler_state.get("gamma") != 0.9
        or scheduler_state.get("last_epoch") != completed_step
    ):
        raise AtomicCountingEvidenceInputError(
            "{} StepLR state differs from the frozen contract".format(name)
        )


def _validate_step_records(
    records: object,
    *,
    domain: CountingFixtureDomain,
    completed_step: int,
    model: Mapping[str, object],
    name: str,
) -> None:
    if type(records) is not list or len(records) != completed_step:
        raise AtomicCountingEvidenceInputError(
            "{} must contain every completed step".format(name)
        )
    expected_keys = {
        "absent_count",
        "completed_step",
        "continuous_count",
        "continuous_loss",
        "count_loss",
        "empty_count",
        "occupied_count",
        "presence_loss",
        "present_count",
        "task_id",
        "task_index",
        "total_loss",
    }
    task_sequence = _TASK_INDEX_SEQUENCE[domain][:completed_step]
    any_continuous = False
    r = int(model["reference_positions"])
    k = int(model["number_of_event_types"])
    s = int(model["slot_capacity"])
    p = int(model["number_of_presence_coordinates"])
    c = int(model["number_of_continuous_coordinates"])
    for index, record_value in enumerate(records, start=1):
        record = _expect_keys(record_value, expected_keys, name="{} step".format(name))
        task_index = task_sequence[index - 1]
        if (
            record["completed_step"] != index
            or record["task_index"] != task_index
            or record["task_id"] != ("U", "A")[task_index]
        ):
            raise AtomicCountingEvidenceInputError(
                "{} task order differs from the preregistered sampler".format(name)
            )
        total = _tensor_scalar_float32(record["total_loss"], name=name + ".total")
        count = _tensor_scalar_float32(record["count_loss"], name=name + ".count")
        presence = _tensor_scalar_float32(
            record["presence_loss"], name=name + ".presence"
        )
        continuous = _tensor_scalar_float32(
            record["continuous_loss"], name=name + ".continuous"
        )
        summed = np.float32(np.float32(count + presence) + continuous)
        if total.tobytes() != summed.tobytes():
            raise AtomicCountingEvidenceInputError(
                "{} total loss is not the float32 component sum".format(name)
            )
        limits = {
            "occupied_count": r * k,
            "empty_count": r * k,
            "present_count": r * k * s * p,
            "absent_count": r * k * s * p,
            "continuous_count": r * k * s * c,
        }
        for field, maximum in limits.items():
            _plain_int(
                record[field], name="{} {}".format(name, field), maximum=maximum
            )
        any_continuous = any_continuous or record["continuous_count"] > 0
    if completed_step == 12 and not any_continuous:
        raise AtomicCountingEvidenceInputError(
            "{} never exercised a continuous-loss coordinate".format(name)
        )


def _validate_training_manifest(
    value: object,
    *,
    domain: CountingFixtureDomain,
    completed_step: int,
    model: Mapping[str, object],
    expected_bindings_digest: str,
    expected_task_bundle_digest: str,
    expected_training_config_digest: str,
    name: str,
) -> dict:
    keys = {
        "bindings_digest",
        "completed_step",
        "corruption_generator_state",
        "domain",
        "format",
        "gate_id",
        "global_torch_rng_state",
        "model_state",
        "optimizer_state",
        "parameter_count",
        "sampler_state",
        "scheduler_state",
        "step_records",
        "task_bundle_digest",
        "training_config_digest",
    }
    manifest = _expect_keys(value, keys, name=name)
    if (
        manifest["format"] != _TRAINING_MANIFEST_FORMAT
        or manifest["gate_id"] != _GATE_ID
        or manifest["domain"] != domain.value
        or manifest["completed_step"] != completed_step
        or manifest["bindings_digest"] != expected_bindings_digest
        or manifest["task_bundle_digest"] != expected_task_bundle_digest
        or manifest["training_config_digest"] != expected_training_config_digest
        or manifest["parameter_count"] != model["parameter_count"]
    ):
        raise AtomicCountingEvidenceInputError(
            "{} identity/configuration bindings are invalid".format(name)
        )
    _validate_model_state(manifest["model_state"], model, name=name + ".model")
    _validate_optimizer_scheduler(
        manifest["optimizer_state"],
        manifest["scheduler_state"],
        model=model,
        completed_step=completed_step,
        name=name,
    )
    _validate_sampler_state(
        manifest["sampler_state"],
        domain=domain,
        completed_step=completed_step,
        name=name + ".sampler",
    )
    for field in ("corruption_generator_state", "global_torch_rng_state"):
        record = _tensor_record(
            manifest[field], name=name + "." + field, allowed_dtypes=("uint8",)
        )
        if len(record.shape) != 1 or not record.data or len(record.data) > 1_000_000:
            raise AtomicCountingEvidenceInputError(
                "{} {} is not a bounded CPU generator state".format(name, field)
            )
    _validate_step_records(
        manifest["step_records"],
        domain=domain,
        completed_step=completed_step,
        model=model,
        name=name,
    )
    return manifest


def _validate_production_torch_zip(payload: bytes) -> Mapping[str, object]:
    """Boundedly recognize a ``torch.save``-style ZIP without importing Torch.

    This is structural discrimination, not an authenticity check.  A hostile
    producer can construct the same archive shape; run provenance and reviewer
    independence therefore remain external audit/custody assumptions.
    """

    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), mode="r")
    except (zipfile.BadZipFile, ValueError) as error:
        raise AtomicCountingEvidenceInputError(
            "production checkpoint payload is not a bounded Torch archive"
        ) from error
    with archive:
        entries = archive.infolist()
        if not entries or len(entries) > 4096:
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive entry count is invalid"
            )
        names = [entry.filename for entry in entries]
        if len(set(names)) != len(names):
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive has duplicate entries"
            )
        roots = set()
        relative_entries = {}
        total_uncompressed = 0
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            parts = path.parts
            unix_mode = (entry.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(unix_mode)
            if (
                type(name) is not str
                or not name
                or "\\" in name
                or path.is_absolute()
                or len(parts) < 2
                or name != "/".join(parts)
                or any(part in ("", ".", "..") for part in parts)
                or any(
                    unicodedata.category(character) in {"Cc", "Cf", "Cs"}
                    for character in name
                )
                or len(name.encode("utf-8")) > 4096
                or entry.is_dir()
                or bool(entry.flag_bits & 0x1)
                or file_type not in (0, stat.S_IFREG)
                or entry.file_size < 0
                or entry.compress_size < 0
            ):
                raise AtomicCountingEvidenceInputError(
                    "production checkpoint Torch archive contains an unsafe entry"
                )
            total_uncompressed += entry.file_size
            if (
                entry.file_size > _MAX_CHECKPOINT_BYTES
                or total_uncompressed > _MAX_CHECKPOINT_BYTES
            ):
                raise AtomicCountingEvidenceInputError(
                    "production checkpoint expanded archive exceeds its byte ceiling"
                )
            roots.add(parts[0])
            relative_entries["/".join(parts[1:])] = entry
        if len(roots) != 1:
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive must have one root"
            )
        required = {"byteorder", "data.pkl", "version"}
        if not required.issubset(relative_entries):
            raise AtomicCountingEvidenceInputError(
                "production checkpoint lacks required Torch archive structure"
            )
        storage_names = {
            name
            for name in relative_entries
            if len(name.split("/")) == 2
            and name.startswith("data/")
            and name.split("/", 1)[1].isdecimal()
        }
        if not storage_names:
            raise AtomicCountingEvidenceInputError(
                "production checkpoint has no Torch tensor-storage entries"
            )
        try:
            data_pickle = archive.read(relative_entries["data.pkl"])
            version = archive.read(relative_entries["version"])
            byteorder = archive.read(relative_entries["byteorder"])
            corrupt_name = archive.testzip()
        except Exception as error:
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive cannot be boundedly read"
            ) from error
        if corrupt_name is not None:
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive has a CRC failure"
            )
        if (
            len(data_pickle) < 2
            or data_pickle[0] != 0x80
            or data_pickle[1] not in range(2, 6)
            or version.strip() not in {b"1", b"2", b"3", b"4"}
            or byteorder.strip() not in {b"little", b"big"}
        ):
            raise AtomicCountingEvidenceInputError(
                "production checkpoint Torch archive metadata is invalid"
            )
    return {
        "archive_entry_count": len(entries),
        "archive_uncompressed_bytes": total_uncompressed,
        "payload_profile": "bounded-pytorch-zip-structure",
    }


def _validate_checkpoint_container(
    raw: bytes, *, preparation_mode: _EvidencePreparationMode
) -> Mapping[str, object]:
    if type(preparation_mode) is not _EvidencePreparationMode:
        raise TypeError("preparation_mode must be an internal mode value")
    if len(raw) > _MAX_CHECKPOINT_BYTES:
        raise AtomicCountingEvidenceInputError(
            "checkpoint exceeds the preregistered byte ceiling"
        )
    minimum = len(_CHECKPOINT_MAGIC) + _CHECKPOINT_HEADER_BYTES
    if len(raw) < minimum or raw[: len(_CHECKPOINT_MAGIC)] != _CHECKPOINT_MAGIC:
        raise AtomicCountingEvidenceInputError("checkpoint magic is invalid")
    header_size = struct.unpack(
        ">I", raw[len(_CHECKPOINT_MAGIC) : minimum]
    )[0]
    if header_size == 0 or header_size > 65_536:
        raise AtomicCountingEvidenceInputError("checkpoint header size is invalid")
    header_stop = minimum + header_size
    if header_stop > len(raw):
        raise AtomicCountingEvidenceInputError("checkpoint header is truncated")
    header_value = _strict_json_bytes(
        raw[minimum:header_stop], name="checkpoint header"
    )
    header = _expect_keys(
        header_value,
        {"container_version", "format", "payload_length", "payload_sha256"},
        name="checkpoint header",
    )
    payload = raw[header_stop:]
    payload_length = _plain_int(
        header["payload_length"],
        name="checkpoint payload length",
        minimum=1,
        maximum=_MAX_CHECKPOINT_BYTES,
    )
    payload_digest = _require_sha256(
        header["payload_sha256"], name="checkpoint payload digest"
    )
    if (
        header["container_version"] != 1
        or header["format"] != _CHECKPOINT_FORMAT
        or payload_length != len(payload)
        or payload_digest != _sha256(payload)
    ):
        raise AtomicCountingEvidenceInputError(
            "checkpoint header/payload integrity is invalid"
        )
    if preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST:
        if payload != _SYNTHETIC_CHECKPOINT_PAYLOAD:
            raise AtomicCountingEvidenceInputError(
                "synthetic test checkpoint is not the exact admitted marker"
            )
        payload_structure = {
            "payload_profile": "exact-synthetic-test-marker"
        }
    else:
        if payload == _SYNTHETIC_CHECKPOINT_PAYLOAD:
            raise AtomicCountingEvidencePrerequisiteError(
                "production preparation refuses the exact synthetic checkpoint marker"
            )
        payload_structure = _validate_production_torch_zip(payload)
    return {
        "container_version": 1,
        "format": _CHECKPOINT_FORMAT,
        "payload_length": len(payload),
        "payload_sha256": payload_digest,
        **payload_structure,
    }


def _validate_artifact_receipt(
    value: object,
    *,
    actual: Mapping[str, bytes],
    name: str,
) -> Mapping[str, Mapping[str, object]]:
    mapping = _expect_keys(value, actual.keys(), name=name)
    result = {}
    for artifact_name, raw in actual.items():
        entry = _expect_keys(
            mapping[artifact_name],
            {"sha256", "size_bytes"},
            name="{} {}".format(name, artifact_name),
        )
        digest = _require_sha256(
            entry["sha256"], name="{} {} sha256".format(name, artifact_name)
        )
        size = _plain_int(
            entry["size_bytes"],
            name="{} {} size".format(name, artifact_name),
            maximum=_MAX_OUTPUT_BYTES,
        )
        if digest != _sha256(raw) or size != len(raw):
            raise AtomicCountingEvidenceInputError(
                "{} {} does not bind the supplied file".format(name, artifact_name)
            )
        result[artifact_name] = {"sha256": digest, "size_bytes": size}
    return result


def _canonical_distribution_name(value: str) -> str:
    if type(value) is not str or not value:
        raise AtomicCountingEvidenceInputError("lock distribution name is invalid")
    result = value.lower().replace("_", "-").replace(".", "-")
    while "--" in result:
        result = result.replace("--", "-")
    if not result or result.startswith("-") or result.endswith("-"):
        raise AtomicCountingEvidenceInputError("lock distribution name is invalid")
    return result


def _locked_distributions(lock_raw: bytes) -> Mapping[str, str]:
    try:
        text = lock_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AtomicCountingEvidenceInputError("dependency lock is not UTF-8") from error
    result = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise AtomicCountingEvidenceInputError(
                "dependency lock line {} is not an exact pin".format(line_number)
            )
        declared_name, version = line.split("==")
        if (
            not declared_name
            or not version
            or declared_name != declared_name.strip()
            or version != version.strip()
        ):
            raise AtomicCountingEvidenceInputError(
                "dependency lock line {} is noncanonical".format(line_number)
            )
        name = _canonical_distribution_name(declared_name)
        if name in result:
            raise AtomicCountingEvidenceInputError(
                "dependency lock repeats {}".format(name)
            )
        result[name] = version
    if not result:
        raise AtomicCountingEvidenceInputError("dependency lock has no distributions")
    return dict(sorted(result.items()))


def _expected_bootstrap_attestation(root: Path) -> Mapping[str, object]:
    bootstrap_raw = _read_verified_file(
        root / _BOOTSTRAP_RELATIVE_PATH,
        limit=1024 * 1024,
        name="source bootstrap",
    )
    return MappingProxyType(
        {
            "bootstrap_sha256": _sha256(bootstrap_raw),
            "executable_sha256": (
                "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
            ),
            "executable_size_bytes": 152_624,
            "python_implementation": "cpython",
            "python_version": "3.11.5",
            "schema": _BOOTSTRAP_SCHEMA,
        }
    )


def _validate_environment(
    value: object, *, lock_raw: bytes, root: Path
) -> Mapping[str, object]:
    keys = {
        "bootstrap_attestation",
        "default_device",
        "default_dtype",
        "environment",
        "format",
        "locked_distributions",
        "machine",
        "mps_available_but_unused",
        "numpy_version",
        "os_name",
        "platform",
        "python_implementation",
        "python_major_minor",
        "python_version",
        "torch_cuda_version",
        "torch_flags",
        "torch_version",
    }
    environment = _expect_keys(value, keys, name="run environment")
    exact = {
        "default_device": "cpu",
        "default_dtype": "torch.float32",
        "environment": {
            "MKL_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
        },
        "format": "heterodiff-atomic-counting-pinned-runtime-v1",
        "locked_distributions": _locked_distributions(lock_raw),
        "machine": "arm64",
        "numpy_version": "2.4.6",
        "os_name": "posix",
        "platform": "darwin",
        "python_implementation": "cpython",
        "python_major_minor": [3, 11],
        "python_version": "3.11.5",
        "torch_cuda_version": None,
        "torch_flags": {
            "deterministic_algorithms": True,
            "deterministic_warn_only": False,
            "mkldnn_enabled": False,
            "num_interop_threads": 1,
            "num_threads": 1,
        },
        "torch_version": "2.12.1",
    }
    for key, expected in exact.items():
        if environment[key] != expected:
            raise AtomicCountingEvidenceInputError(
                "run environment field {} differs from the complete pinned runtime".format(
                    key
                )
            )
    attestation = environment["bootstrap_attestation"]
    expected_attestation = _expected_bootstrap_attestation(root)
    if (
        type(attestation) is not dict
        or set(attestation) != set(expected_attestation)
        or attestation != dict(expected_attestation)
    ):
        raise AtomicCountingEvidenceInputError(
            "run source-bootstrap attestation differs from the frozen runtime"
        )
    if type(environment["mps_available_but_unused"]) is not bool:
        raise AtomicCountingEvidenceInputError(
            "run environment MPS observation is invalid"
        )
    return environment


def _required_dynamic_stage_sequence(branch: str) -> Tuple[str, ...]:
    if branch not in ("continuous", "prefix", "resume"):
        raise AtomicCountingEvidenceInputError("unknown training branch")
    result = [
        "fixture-parse-and-task-construction",
        "reference-and-task-conversion",
        "trainer-initialization",
    ]
    if branch == "resume":
        result.extend(
            (
                "checkpoint-load-preflight",
                "checkpoint-validation",
                "checkpoint-restore",
            )
        )
        steps = 7
    else:
        steps = 12 if branch == "continuous" else 5
    for _step in range(steps):
        result.extend(
            (
                "corruption-and-conversion",
                "forward",
                "backward",
                "optimizer-and-scheduler",
            )
        )
    if branch == "prefix":
        result.extend(
            (
                "checkpoint-save-preflight",
                "checkpoint-serialization",
                "checkpoint-save",
            )
        )
    result.extend(("comparison-output-preflight", "comparison-output"))
    return tuple(result)


def _validate_resource_receipt(value: object, *, artifacts: Mapping[str, bytes]) -> Mapping[str, object]:
    resources = _expect_keys(value, {"limits", "observations"}, name="resources")
    expected_limits = {
        "batch_size": 1,
        "checkpoint_bytes": _MAX_CHECKPOINT_BYTES,
        "log_bytes": _MAX_LOG_BYTES,
        "output_bytes": _MAX_OUTPUT_BYTES,
        "parameter_count": 250_000,
        "peak_rss_bytes": _MAX_RSS_BYTES,
        "runtime_seconds": _MAX_RUNTIME_SECONDS,
        "training_steps": 12,
        "worker_processes": 0,
    }
    limits = _expect_keys(resources["limits"], expected_limits, name="resource limits")
    if limits != expected_limits:
        raise AtomicCountingEvidenceInputError(
            "resource limits differ from the preregistered literals"
        )
    observations = _expect_keys(
        resources["observations"],
        {"continuous", "prefix", "resume"},
        name="resource observations",
    )
    validated_observations = {}
    artifact_for_branch = {
        "continuous": "continuous_manifest",
        "prefix": "prefix_manifest",
        "resume": "resumed_manifest",
    }
    for branch in ("continuous", "prefix", "resume"):
        entry = _expect_keys(
            observations[branch],
            {"log_bytes", "output_bytes", "stages"},
            name="{} resource observation".format(branch),
        )
        log_bytes = _plain_int(
            entry["log_bytes"], name=branch + " log_bytes", maximum=_MAX_LOG_BYTES
        )
        output = _plain_int(
            entry["output_bytes"],
            name=branch + " output_bytes",
            maximum=_MAX_OUTPUT_BYTES,
        )
        if output != len(artifacts[artifact_for_branch[branch]]):
            raise AtomicCountingEvidenceInputError(
                "{} output byte observation disagrees with its manifest".format(branch)
            )
        stages = entry["stages"]
        required = _required_dynamic_stage_sequence(branch)
        if type(stages) is not list or len(stages) != len(required):
            raise AtomicCountingEvidencePrerequisiteError(
                "{} dynamic-stage inventory is incomplete".format(branch)
            )
        validated_stages = []
        previous_elapsed = -1.0
        previous_peak = -1
        for index, (stage_value, expected_stage) in enumerate(
            zip(stages, required), start=1
        ):
            stage = _expect_keys(
                stage_value,
                {"elapsed_seconds", "peak_rss_bytes", "stage", "stage_index"},
                name="{} stage {}".format(branch, index),
            )
            elapsed = _finite_real(
                stage["elapsed_seconds"],
                name="{} stage elapsed".format(branch),
                maximum=_MAX_RUNTIME_SECONDS,
            )
            peak = _plain_int(
                stage["peak_rss_bytes"],
                name="{} stage peak RSS".format(branch),
                maximum=_MAX_RSS_BYTES,
            )
            if (
                stage["stage"] != expected_stage
                or stage["stage_index"] != index
                or elapsed < previous_elapsed
                or peak < previous_peak
            ):
                raise AtomicCountingEvidencePrerequisiteError(
                    "{} dynamic-stage order/observations are invalid".format(branch)
                )
            previous_elapsed = elapsed
            previous_peak = peak
            validated_stages.append(
                {
                    "elapsed_seconds": elapsed,
                    "peak_rss_bytes": peak,
                    "stage": expected_stage,
                    "stage_index": index,
                }
            )
        validated_observations[branch] = {
            "log_bytes": log_bytes,
            "output_bytes": output,
            "stages": validated_stages,
        }
    resumed_branch_elapsed = sum(
        validated_observations[branch]["stages"][-1]["elapsed_seconds"]
        for branch in ("prefix", "resume")
    )
    if resumed_branch_elapsed > _MAX_RUNTIME_SECONDS:
        raise AtomicCountingEvidencePrerequisiteError(
            "prefix plus resume final elapsed time exceeds the preregistered "
            "resumed-branch runtime ceiling"
        )
    return {"limits": expected_limits, "observations": validated_observations}


def _preflight_run_receipt_structure(
    value: object,
    *,
    domain: CountingFixtureDomain,
    preparation_mode: _EvidencePreparationMode,
    artifacts: Mapping[str, bytes],
    lock_raw: bytes,
    root: Path,
) -> Mapping[str, object]:
    """Reject cheap receipt failures before any fixture/grid allocation."""

    receipt = _expect_keys(
        value,
        {
            "artifact_kind",
            "artifacts",
            "checkpoint_bindings",
            "domain",
            "environment",
            "gate_id",
            "resources",
            "schema_version",
            "synthetic_test_only",
            "training_commands",
        },
        name="run receipt",
    )
    if (
        receipt["schema_version"] != _RUN_RECEIPT_SCHEMA
        or receipt["artifact_kind"] != "completed-training-run"
        or receipt["domain"] != domain.value
        or receipt["gate_id"] != _GATE_ID
        or type(receipt["synthetic_test_only"]) is not bool
    ):
        raise AtomicCountingEvidenceInputError("run receipt identity is invalid")
    expected_synthetic = (
        preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST
    )
    if receipt["synthetic_test_only"] is not expected_synthetic:
        raise AtomicCountingEvidencePrerequisiteError(
            "run receipt execution declaration disagrees with the explicit "
            "{} preparation mode".format(preparation_mode.value)
        )
    _validate_artifact_receipt(
        receipt["artifacts"], actual=artifacts, name="run receipt artifacts"
    )
    bindings = _expect_keys(
        receipt["checkpoint_bindings"],
        _REQUIRED_BINDING_KEYS,
        name="checkpoint bindings",
    )
    for key, value_digest in bindings.items():
        if key == "gate_id":
            if value_digest != _GATE_ID:
                raise AtomicCountingEvidenceInputError(
                    "checkpoint gate_id binding is invalid"
                )
        else:
            _require_sha256(value_digest, name="checkpoint binding {}".format(key))
    if bindings["converted_state"] == bindings["tensor"]:
        raise AtomicCountingEvidencePrerequisiteError(
            "checkpoint bindings do not independently bind converted state and "
            "Torch target tensor; converted_state/tensor are a copied alias"
        )
    _validate_environment(
        receipt["environment"], lock_raw=lock_raw, root=root
    )
    _validate_resource_receipt(receipt["resources"], artifacts=artifacts)
    return receipt


def _validate_run_receipt(
    value: object,
    *,
    domain: CountingFixtureDomain,
    preparation_mode: _EvidencePreparationMode,
    artifacts: Mapping[str, bytes],
    expected_bindings: Mapping[str, str],
    lock_raw: bytes,
    root: Path,
) -> Mapping[str, object]:
    receipt = _expect_keys(
        value,
        {
            "artifact_kind",
            "artifacts",
            "checkpoint_bindings",
            "domain",
            "environment",
            "gate_id",
            "resources",
            "schema_version",
            "synthetic_test_only",
            "training_commands",
        },
        name="run receipt",
    )
    if (
        receipt["schema_version"] != _RUN_RECEIPT_SCHEMA
        or receipt["artifact_kind"] != "completed-training-run"
        or receipt["domain"] != domain.value
        or receipt["gate_id"] != _GATE_ID
        or type(receipt["synthetic_test_only"]) is not bool
    ):
        raise AtomicCountingEvidenceInputError("run receipt identity is invalid")
    expected_synthetic = (
        preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST
    )
    if receipt["synthetic_test_only"] is not expected_synthetic:
        raise AtomicCountingEvidencePrerequisiteError(
            "run receipt execution declaration disagrees with the explicit "
            "{} preparation mode".format(preparation_mode.value)
        )
    artifact_entries = _validate_artifact_receipt(
        receipt["artifacts"], actual=artifacts, name="run receipt artifacts"
    )
    bindings = _expect_keys(
        receipt["checkpoint_bindings"],
        _REQUIRED_BINDING_KEYS,
        name="checkpoint bindings",
    )
    normalized_bindings = {}
    for key, value_digest in bindings.items():
        if key == "gate_id":
            if value_digest != _GATE_ID:
                raise AtomicCountingEvidenceInputError(
                    "checkpoint gate_id binding is invalid"
                )
            normalized_bindings[key] = value_digest
        else:
            normalized_bindings[key] = _require_sha256(
                value_digest, name="checkpoint binding {}".format(key)
            )
    if normalized_bindings != dict(expected_bindings):
        copied_alias = (
            normalized_bindings.get("converted_state")
            == normalized_bindings.get("tensor")
        )
        detail = (
            "; converted_state/tensor are a copied alias"
            if copied_alias
            else ""
        )
        raise AtomicCountingEvidencePrerequisiteError(
            "checkpoint bindings do not independently bind converted state and Torch target tensor{}".format(
                detail
            )
        )
    commands = _expect_keys(
        receipt["training_commands"],
        {"continuous", "prefix", "resume"},
        name="training commands",
    )
    validated_commands = {}
    expected_commands = _expected_training_commands(
        domain, _sha256(artifacts["checkpoint"])
    )
    for branch in ("continuous", "prefix", "resume"):
        argv = _relative_command(commands[branch], name=branch + " command")
        if argv != expected_commands[branch]:
            raise AtomicCountingEvidenceInputError(
                "{} command is not the exact frozen worker argv".format(branch)
            )
        validated_commands[branch] = list(argv)
    environment = _validate_environment(
        receipt["environment"], lock_raw=lock_raw, root=root
    )
    resources = _validate_resource_receipt(receipt["resources"], artifacts=artifacts)
    return {
        **receipt,
        "artifacts": artifact_entries,
        "checkpoint_bindings": normalized_bindings,
        "training_commands": validated_commands,
        "environment": environment,
        "resources": resources,
    }


def _validate_interpreter_identity(
    value: object, *, pinned: bool, name: str
) -> Mapping[str, object]:
    expected = (
        _PINNED_INTERPRETER_IDENTITY
        if pinned
        else _BASE_INTERPRETER_IDENTITY
    )
    identity = _expect_keys(value, expected, name=name)
    if type(identity["implementation"]) is not str:
        raise AtomicCountingEvidenceInputError(
            "{} implementation must be a string".format(name)
        )
    resolved_digest = _require_sha256(
        identity["resolved_executable_sha256"],
        name=name + " resolved executable",
    )
    if type(identity["resolved_executable_size_bytes"]) is not int:
        raise AtomicCountingEvidenceInputError(
            "{} resolved executable size must be an integer".format(name)
        )
    resolved_size = _plain_int(
        identity["resolved_executable_size_bytes"],
        name=name + " resolved executable size",
    )
    if type(identity["version"]) is not str:
        raise AtomicCountingEvidenceInputError(
            "{} version must be a string".format(name)
        )
    normalized = {
        "implementation": identity["implementation"],
        "resolved_executable_sha256": resolved_digest,
        "resolved_executable_size_bytes": resolved_size,
        "version": identity["version"],
    }
    if normalized != dict(expected):
        raise AtomicCountingEvidenceInputError(
            "{} does not match the frozen interpreter identity".format(name)
        )
    return normalized


def _validate_test_run(value: object, *, pinned: bool, name: str) -> Mapping[str, object]:
    run = _expect_keys(
        value,
        {
            "command",
            "exit_code",
            "interpreter_identity",
            "passed",
            "skip_reasons",
            "skipped",
            "warnings",
        },
        name=name,
    )
    command_tuple = _relative_command(run["command"], name=name + " command")
    expected_command = _PINNED_TEST_COMMAND if pinned else _BASE_TEST_COMMAND
    if command_tuple != expected_command:
        raise AtomicCountingEvidenceInputError(
            "{} command is not the exact frozen focused pytest argv".format(name)
        )
    command = list(command_tuple)
    passed = _plain_int(run["passed"], name=name + " passed", minimum=1, maximum=1_000_000)
    skipped = _plain_int(run["skipped"], name=name + " skipped", maximum=1_000_000)
    warnings = _plain_int(run["warnings"], name=name + " warnings", maximum=1_000_000)
    if run["exit_code"] != 0 or warnings != 0:
        raise AtomicCountingEvidencePrerequisiteError(
            "{} did not complete cleanly with warnings-as-errors".format(name)
        )
    expected_passed = (
        _EXPECTED_PINNED_PASSED if pinned else _EXPECTED_BASE_PASSED
    )
    if passed != expected_passed:
        raise AtomicCountingEvidencePrerequisiteError(
            "{} must report exactly {} passed tests".format(
                name, expected_passed
            )
        )
    reasons = run["skip_reasons"]
    if type(reasons) is not list:
        raise AtomicCountingEvidenceInputError("{} skip reasons are invalid".format(name))
    if pinned:
        if skipped != 0 or reasons:
            raise AtomicCountingEvidencePrerequisiteError(
                "pinned test run must have zero skips"
            )
    else:
        expected = [dict(item) for item in _BASE_SKIP_MANIFEST]
        if skipped != 2 or reasons != expected:
            raise AtomicCountingEvidencePrerequisiteError(
                "base test run must have the exact two path-bound pinned-extra skips"
            )
    return {
        "command": command,
        "exit_code": 0,
        "interpreter_identity": _validate_interpreter_identity(
            run["interpreter_identity"],
            pinned=pinned,
            name=name + " interpreter identity",
        ),
        "passed": passed,
        "skip_reasons": reasons,
        "skipped": skipped,
        "warnings": 0,
    }


def _validate_audit_report(
    value: object,
    *,
    raw_receipt: bytes,
    domain: CountingFixtureDomain,
    synthetic_test_only: bool,
    artifacts: Mapping[str, bytes],
    digest_inventory: Mapping[str, str],
) -> Mapping[str, object]:
    audit = _expect_keys(
        value,
        {
            "adversarial_review",
            "artifact_digests",
            "artifact_kind",
            "checkpoint_integrity",
            "checkpoint_replay",
            "domain",
            "falsification_checks",
            "gate_id",
            "independent_digest_inventory",
            "run_receipt_sha256",
            "schema_version",
            "synthetic_test_only",
            "test_runs",
        },
        name="audit report",
    )
    if (
        audit["schema_version"] != _AUDIT_SCHEMA
        or audit["artifact_kind"] != "independent-gate-audit"
        or audit["domain"] != domain.value
        or audit["gate_id"] != _GATE_ID
        or audit["synthetic_test_only"] is not synthetic_test_only
        or audit["run_receipt_sha256"] != _sha256(raw_receipt)
    ):
        raise AtomicCountingEvidenceInputError("audit report identity is invalid")
    artifact_digests = _expect_keys(
        audit["artifact_digests"], artifacts, name="audit artifact digests"
    )
    for artifact_name, raw in artifacts.items():
        if artifact_digests[artifact_name] != _sha256(raw):
            raise AtomicCountingEvidenceInputError(
                "audit report does not bind {}".format(artifact_name)
            )
    checks = _expect_keys(
        audit["falsification_checks"],
        _FALSIFICATION_CHECKS,
        name="falsification checks",
    )
    failed = sorted(key for key, status in checks.items() if status != "PASS")
    if failed:
        raise AtomicCountingEvidencePrerequisiteError(
            "falsification checks are not PASS: {}".format(", ".join(failed))
        )
    tests = _expect_keys(audit["test_runs"], {"base", "pinned"}, name="test runs")
    validated_tests = {
        "base": _validate_test_run(tests["base"], pinned=False, name="base tests"),
        "pinned": _validate_test_run(tests["pinned"], pinned=True, name="pinned tests"),
    }
    replay = _expect_keys(
        audit["checkpoint_replay"],
        {
            "compared_step_range",
            "comparison_fields",
            "comparison_status",
            "continuous_manifest_sha256",
            "first_post_restore_step",
            "first_post_restore_task_id",
            "resumed_manifest_sha256",
        },
        name="checkpoint replay audit",
    )
    first_task = ("U", "A")[_TASK_INDEX_SEQUENCE[domain][5]]
    if (
        replay["comparison_status"] != "BITWISE_EQUAL"
        or replay["compared_step_range"] != [1, 12]
        or replay["comparison_fields"] != list(_COMPARISON_FIELDS)
        or replay["continuous_manifest_sha256"]
        != _sha256(artifacts["continuous_manifest"])
        or replay["resumed_manifest_sha256"]
        != _sha256(artifacts["resumed_manifest"])
        or replay["first_post_restore_step"] != 6
        or replay["first_post_restore_task_id"] != first_task
    ):
        raise AtomicCountingEvidencePrerequisiteError(
            "checkpoint restart audit is incomplete or not bitwise equal"
        )
    checkpoint = _expect_keys(
        audit["checkpoint_integrity"],
        {
            "bindings_validated_before_mutation",
            "canonical_rewrap_rejected",
            "container_no_trailing_bytes",
            "decoder",
            "expected_sha_required",
            "failure_atomicity_verified",
            "parent_checkpoint_sha256",
            "payload_completed_step",
            "restore_step_range",
            "save_step",
        },
        name="checkpoint integrity audit",
    )
    expected_checkpoint = {
        "bindings_validated_before_mutation": True,
        "canonical_rewrap_rejected": True,
        "container_no_trailing_bytes": True,
        "decoder": "torch.load(weights_only=True)",
        "expected_sha_required": True,
        "failure_atomicity_verified": True,
        "parent_checkpoint_sha256": _GENESIS,
        "payload_completed_step": 5,
        "restore_step_range": [6, 12],
        "save_step": 5,
    }
    if checkpoint != expected_checkpoint:
        raise AtomicCountingEvidencePrerequisiteError(
            "checkpoint integrity audit is not the complete frozen contract"
        )
    inventory = _expect_keys(
        audit["independent_digest_inventory"],
        digest_inventory,
        name="independent digest inventory",
    )
    if inventory != dict(digest_inventory):
        raise AtomicCountingEvidencePrerequisiteError(
            "audit did not independently bind configuration/grid/Torch payloads"
        )
    review = _expect_keys(
        audit["adversarial_review"],
        {"review_protocol_digest", "scope", "status", "unresolved_findings"},
        name="adversarial review",
    )
    expected_review_digest = _domain_digest(
        "heterodiff.atomic-counting.independent-review-protocol.v1",
        {"text": _REVIEW_PROTOCOL_TEXT},
    )
    if (
        review["status"] != "PASS"
        or review["scope"] != "independent-scientific-integrity-privacy-resource"
        or review["unresolved_findings"] != []
        or review["review_protocol_digest"] != expected_review_digest
    ):
        raise AtomicCountingEvidencePrerequisiteError(
            "independent adversarial review is HOLD or incomplete"
        )
    return {
        **audit,
        "falsification_checks": dict(checks),
        "test_runs": validated_tests,
    }


def _distinct_atom_count(fixture: CountingFixtureResult) -> int:
    records = set()
    for event in fixture.configuration.events:
        records.add(
            _canonical_json_bytes(
                {
                    "event_time": event.event_time,
                    "event_type": event.event_type,
                    "marks": {
                        name: list(values)
                        for name, values in sorted(event.marks.items())
                    },
                }
            )
        )
    return len(records)


def _parser_limits(
    fixture: CountingFixtureResult,
) -> Mapping[str, object]:
    if fixture.domain is CountingFixtureDomain.MUSIC:
        limits = M_ACG_1_MIDI_PARSE_LIMITS
        parser = {
            "maximum_absolute_tick": limits.maximum_absolute_tick,
            "maximum_event_payload_bytes": limits.maximum_event_payload_bytes,
            "maximum_events_per_track": limits.maximum_events_per_track,
            "maximum_file_bytes": limits.maximum_file_bytes,
            "maximum_ticks_per_quarter_note": limits.maximum_ticks_per_quarter_note,
            "maximum_total_events": limits.maximum_total_events,
            "maximum_track_bytes": limits.maximum_track_bytes,
            "maximum_tracks": limits.maximum_tracks,
            "parser": "bounded-standard-midi-file",
        }
    else:
        parser = {
            "admission_descriptor_count": 6,
            "dual_role_parameter_count": 1,
            "final_lf_required": True,
            "maximum_data_rows": 32,
            "maximum_elapsed_minutes": 2880,
            "parser": "bounded-physionet-2012-style-csv",
            "strict_utf8": True,
        }
    return {
        "fixture_resource_limits": fixture.resource_limits.as_dict(),
        "source_parser_limits": parser,
    }


def _grid_manifest(grid: AtomicCountingGridTensor) -> Tuple[Mapping[str, object], ...]:
    return tuple(_array_manifest(name, value) for name, value in _grid_arrays(grid))


def _mask_totals(grid: AtomicCountingGridTensor) -> Mapping[str, int]:
    return {
        "active_occurrences": int(grid.occurrence_present.sum()),
        "mark_applicable_coordinates": sum(
            int(value.sum()) for value in grid.mark_applicable.values()
        ),
        "mark_observed_coordinates": sum(
            int(value.sum()) for value in grid.mark_observed.values()
        ),
        "mark_present_coordinates": sum(
            int(value.sum()) for value in grid.mark_present.values()
        ),
        "time_observed_occurrences": int(grid.time_observed.sum()),
        "type_observed_occurrences": int(grid.type_observed.sum()),
    }


def _validate_domain_run(
    run: CompletedDomainRun, *, preparation_mode: _EvidencePreparationMode
) -> _ValidatedDomain:
    if type(preparation_mode) is not _EvidencePreparationMode:
        raise TypeError("preparation_mode must be an internal mode value")
    domain = run.domain
    root = _project_root()
    paths = (
        run.continuous_manifest,
        run.prefix_manifest,
        run.resumed_manifest,
        run.checkpoint,
        run.run_receipt,
        run.audit_report,
    )
    observations = []
    for path in paths:
        _reject_symlink_components(path, final_must_exist=True)
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode):
            raise AtomicCountingEvidenceInputError(
                "completed-run inputs must be regular files"
            )
        observations.append((status.st_dev, status.st_ino))
    if len(set(observations)) != len(observations):
        raise AtomicCountingEvidenceInputError(
            "completed-run inputs must not be hard-link aliases"
        )

    continuous_raw, continuous_value = _load_json_file(
        run.continuous_manifest,
        limit=_MAX_JSON_BYTES,
        name=domain.value + " continuous manifest",
    )
    prefix_raw, prefix_value = _load_json_file(
        run.prefix_manifest,
        limit=_MAX_JSON_BYTES,
        name=domain.value + " prefix manifest",
    )
    resumed_raw, resumed_value = _load_json_file(
        run.resumed_manifest,
        limit=_MAX_JSON_BYTES,
        name=domain.value + " resumed manifest",
    )
    checkpoint_raw = _read_verified_file(
        run.checkpoint,
        limit=_MAX_CHECKPOINT_BYTES,
        name=domain.value + " checkpoint",
    )
    receipt_raw, receipt_value = _load_json_file(
        run.run_receipt,
        limit=_MAX_RECEIPT_BYTES,
        name=domain.value + " run receipt",
    )
    audit_raw, audit_value = _load_json_file(
        run.audit_report,
        limit=_MAX_AUDIT_BYTES,
        name=domain.value + " audit report",
    )
    artifacts = {
        "checkpoint": checkpoint_raw,
        "continuous_manifest": continuous_raw,
        "prefix_manifest": prefix_raw,
        "resumed_manifest": resumed_raw,
    }
    checkpoint_header = _validate_checkpoint_container(
        checkpoint_raw, preparation_mode=preparation_mode
    )
    lock_path = root / "requirements" / "m1-reference-macos-arm64-py311.lock"
    gate_path = root / "research" / "32_cross_domain_atomic_counting_reference_gate.md"
    lock_raw = _read_verified_file(
        lock_path, limit=1024 * 1024, name="dependency lock"
    )
    gate_raw = _read_verified_file(
        gate_path, limit=2 * 1024 * 1024, name="gate specification"
    )
    receipt_identity = _preflight_run_receipt_structure(
        receipt_value,
        domain=domain,
        preparation_mode=preparation_mode,
        artifacts=artifacts,
        lock_raw=lock_raw,
        root=root,
    )

    fixture = build_m_acg_1() if domain is CountingFixtureDomain.MUSIC else build_p_acg_1()
    task_set = (
        build_m_acg_1_task_set()
        if domain is CountingFixtureDomain.MUSIC
        else build_p_acg_1_task_set()
    )
    fixture.configuration.validate()
    task_set.validate()
    grid = fixture.to_atomic_counting_grid(max_occurrences_per_cell=2)
    configuration_digest = _configuration_payload_digest(fixture)
    grid_digest = _grid_payload_digest(grid)
    torch_target_digest = _torch_target_payload_digest(task_set)
    round_trip_digest = _round_trip_digest(
        fixture, grid, configuration_digest, grid_digest
    )
    digest_inventory = {
        "adapter_target_state_sha256": task_set.target.state_digest,
        "configuration_payload_sha256": configuration_digest,
        "grid_tensor_payload_sha256": grid_digest,
        "torch_target_payload_sha256": torch_target_digest,
    }
    if len(set(digest_inventory.values())) != len(digest_inventory):
        raise AtomicCountingEvidencePrerequisiteError(
            "independently defined configuration/grid/Torch payload identities alias"
        )

    model = _model_shape_contract(task_set)
    task_bundle_digest = _task_bundle_digest(task_set, model)
    training_config_digest = _training_config_digest(domain)
    source_tree_digest = _source_tree_digest(root)
    environment = _validate_environment(
        receipt_identity["environment"], lock_raw=lock_raw, root=root
    )
    environment_digest = _domain_digest(
        "heterodiff.atomic-counting-local-environment.v1",
        environment,
    )
    expected_bindings = _derived_binding_values(
        task_set=task_set,
        model=model,
        code_source_digest=source_tree_digest,
        dependency_lock_digest=_sha256(lock_raw),
        environment_manifest_digest=environment_digest,
        gate_spec_digest=_sha256(gate_raw),
    )
    receipt = _validate_run_receipt(
        receipt_value,
        domain=domain,
        preparation_mode=preparation_mode,
        artifacts=artifacts,
        expected_bindings=expected_bindings,
        lock_raw=lock_raw,
        root=root,
    )
    bindings_digest = _bindings_digest(expected_bindings)
    continuous = _validate_training_manifest(
        continuous_value,
        domain=domain,
        completed_step=12,
        model=model,
        expected_bindings_digest=bindings_digest,
        expected_task_bundle_digest=task_bundle_digest,
        expected_training_config_digest=training_config_digest,
        name=domain.value + " continuous manifest",
    )
    prefix = _validate_training_manifest(
        prefix_value,
        domain=domain,
        completed_step=5,
        model=model,
        expected_bindings_digest=bindings_digest,
        expected_task_bundle_digest=task_bundle_digest,
        expected_training_config_digest=training_config_digest,
        name=domain.value + " prefix manifest",
    )
    resumed = _validate_training_manifest(
        resumed_value,
        domain=domain,
        completed_step=12,
        model=model,
        expected_bindings_digest=bindings_digest,
        expected_task_bundle_digest=task_bundle_digest,
        expected_training_config_digest=training_config_digest,
        name=domain.value + " resumed manifest",
    )
    if continuous_raw != resumed_raw or continuous != resumed:
        raise AtomicCountingEvidencePrerequisiteError(
            "continuous and fresh-process resumed manifests are not byte-identical"
        )
    if prefix["step_records"] != continuous["step_records"][:5]:
        raise AtomicCountingEvidencePrerequisiteError(
            "checkpoint prefix records differ from the continuous branch"
        )
    if prefix["global_torch_rng_state"] != continuous["global_torch_rng_state"]:
        raise AtomicCountingEvidencePrerequisiteError(
            "global Torch RNG changed across the explicit-generator run"
        )

    synthetic = preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST
    audit = _validate_audit_report(
        audit_value,
        raw_receipt=receipt_raw,
        domain=domain,
        synthetic_test_only=synthetic,
        artifacts=artifacts,
        digest_inventory=digest_inventory,
    )

    implementation_manifest = _implementation_manifest(root, domain)
    policy_text = _POLICY_TEXT[domain]
    policy_digest = _domain_digest(
        "heterodiff.atomic-counting.semantic-policy.v1",
        {"domain": domain.value, "text": policy_text},
    )
    task_public = task_set.public_manifest()
    if "source_sha256" not in task_public:
        raise AtomicCountingEvidenceInputError(
            "task public manifest lost source binding"
        )
    multiplicity = task_set.target.public_manifest()["multiplicity_histogram"]
    mask_totals = _mask_totals(grid)
    cardinality = len(fixture.configuration.events)
    if not (
        cardinality
        == grid.cardinality
        == int(grid.cell_counts.sum())
        == mask_totals["active_occurrences"]
        == task_set.target.cardinality
    ):
        raise AtomicCountingEvidencePrerequisiteError(
            "independently reconstructed cross-layer cardinalities disagree"
        )

    execution_class = (
        "SYNTHETIC_TEST_ONLY"
        if preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST
        else "EVIDENCE_COMPLETE_AWAITING_GATE_DECISION"
    )
    authorized_language = (
        "Synthetic publisher/verifier fixture only; no empirical or gate claim."
        if synthetic
        else (
            "The generated-fixture representation and deterministic restart "
            "checks recorded here completed under the declared bounded gate. "
            "This is not model-quality, official-data, clinical-validity, or "
            "cross-domain-generalization evidence; the gate decision remains separate."
        )
    )
    resource_contract = {
        "limits": receipt["resources"]["limits"],
        "required_dynamic_stage_inventory": {
            branch: list(_required_dynamic_stage_sequence(branch))
            for branch in ("continuous", "prefix", "resume")
        },
        "static_enforcement_stages": dict(_STATIC_ENFORCEMENT_STAGES),
    }
    declared_cap_digest = _domain_digest(
        "heterodiff.atomic-counting.resource-contract.v1", resource_contract
    )
    deterministic_core: Dict[str, object] = {
        "checkpoint_replay": {
            "checkpoint_container": checkpoint_header,
            "checkpoint_sha256": _sha256(checkpoint_raw),
            "compared_step_range": [1, 12],
            "comparison_fields": list(_COMPARISON_FIELDS),
            "continuous_manifest_sha256": _sha256(continuous_raw),
            "first_post_restore_step": 6,
            "genesis_parent": _GENESIS,
            "prefix_manifest_sha256": _sha256(prefix_raw),
            "resumed_manifest_sha256": _sha256(resumed_raw),
            "save_step": 5,
        },
        "configuration": {
            "adapter_state_digest": task_set.target.state_digest,
            "cardinality": cardinality,
            "configuration_payload_digest": configuration_digest,
            "distinct_atom_count": _distinct_atom_count(fixture),
            "multiplicity_histogram": multiplicity,
            "schema_digest": task_set.target.schema_digest,
        },
        "domain": domain.value,
        "execution_class": execution_class,
        "gate_id": _GATE_ID,
        "grid_tensor": {
            "array_manifest": list(_grid_manifest(grid)),
            "count_sum": int(grid.cell_counts.sum()),
            "mask_totals": mask_totals,
            "round_trip_digest": round_trip_digest,
            "slot_capacity": grid.slot_capacity,
            "tensor_payload_digest": grid_digest,
        },
        "privacy_and_claim_boundary": {
            "authorized_language": authorized_language,
            "blocked_claims": list(_BLOCKED_CLAIMS),
            "checkpoint_provenance_boundary": (
                "Torch-free checkpoint inspection establishes bounded archive "
                "structure and internal content bindings only. Authentic run "
                "provenance, artifact custody, and reviewer independence remain "
                "external procedural audit assumptions; the publisher is not a "
                "trust root."
            ),
            "forbidden_public_fields": sorted(_PUBLIC_FORBIDDEN_KEYS),
            "generated_fixture": True,
            "generated_fixture_notice": _PUBLIC_GENERATED_NOTICE,
        },
        "schema_version": _PUBLIC_SCHEMA,
        "semantic_policy": {
            "canonical_policy_digest": policy_digest,
            "canonical_policy_text": policy_text,
            "implementation_source_manifest": list(implementation_manifest),
        },
        "source_fixture": {
            "fixture_id": fixture.fixture_id,
            "parser_limits": _parser_limits(fixture),
            "source_byte_length": fixture.source_byte_length,
            "source_format_version": fixture.source_format,
            "source_sha256": fixture.source_sha256,
        },
        "tasks_and_split": {
            "group_count": 1,
            "group_policy_digest": _domain_digest(
                "heterodiff.atomic-counting.natural-group-policy.v1",
                {
                    "group_before_task_expansion": True,
                    "source_split": "train",
                    "task_count": 2,
                },
            ),
            "single_group_integrity": len(set(task_set.task_group_ids)) == 1,
        },
        "training": {
            "checkpoint_bindings_digest": bindings_digest,
            "code_source_tree_digest": source_tree_digest,
            "command_argv": receipt["training_commands"],
            "dependency_lock": {
                "path": "requirements/m1-reference-macos-arm64-py311.lock",
                "sha256": _sha256(lock_raw),
                "size_bytes": len(lock_raw),
            },
            "environment": receipt["environment"],
            "gate_specification": {
                "path": "research/32_cross_domain_atomic_counting_reference_gate.md",
                "sha256": _sha256(gate_raw),
                "size_bytes": len(gate_raw),
            },
            "independent_digest_inventory": digest_inventory,
            "parameter_count": model["parameter_count"],
            "resolved_config": _training_config(domain),
            "resource_contract": {
                **resource_contract,
                "declared_cap_digest": declared_cap_digest,
            },
            "seeds": {
                "corruption": _DOMAIN_SEEDS[domain][2],
                "model_and_global": _DOMAIN_SEEDS[domain][0],
                "task_sampler": _DOMAIN_SEEDS[domain][1],
            },
            "task_bundle_digest": task_bundle_digest,
            "task_set_digest": task_set.task_set_digest,
            "torch_target_payload_digest": torch_target_digest,
        },
    }
    forbidden_public_identifiers = tuple(
        sorted(
            {
                task_set.source_group_id,
                *(
                    ()
                    if task_set.source_sample_id == task_set.fixture_id
                    else (task_set.source_sample_id,)
                ),
            }
        )
    )
    _reject_public_fields(
        deterministic_core,
        forbidden_identifiers=forbidden_public_identifiers,
    )
    public_digest = _domain_digest(
        "heterodiff.atomic-counting.public-evidence-core.v1",
        deterministic_core,
    )
    public_core_file_sha256 = _sha256(
        _canonical_json_bytes(
            {**deterministic_core, "bundle_digest": public_digest}
        )
    )
    group_policy_digest = deterministic_core["tasks_and_split"][
        "group_policy_digest"
    ]
    gate_run_identifier = _domain_digest(
        "heterodiff.atomic-counting.gate-run-identifier.v1",
        {
            "artifacts": {
                name: _sha256(raw) for name, raw in sorted(artifacts.items())
            },
            "domain": domain.value,
            "environment_digest": environment_digest,
            "gate_id": _GATE_ID,
            "run_receipt_sha256": _sha256(receipt_raw),
        },
    )
    private_envelope: Dict[str, object] = {
        "artifact_digests": {
            name: {"sha256": _sha256(raw), "size_bytes": len(raw)}
            for name, raw in sorted(artifacts.items())
        },
        "audit_report": audit,
        "audit_report_sha256": _sha256(audit_raw),
        "domain": domain.value,
        "declared_cap_digest": declared_cap_digest,
        "execution_environment_digest": environment_digest,
        "execution_class": execution_class,
        "gate_id": _GATE_ID,
        "gate_run_identifier": gate_run_identifier,
        "monitored_stage_inventory": {
            branch: [
                stage["stage"]
                for stage in receipt["resources"]["observations"][branch][
                    "stages"
                ]
            ]
            for branch in ("continuous", "prefix", "resume")
        },
        "observed_resources": receipt["resources"]["observations"],
        "public_bundle_digest": public_digest,
        "public_core_file_sha256": public_core_file_sha256,
        "run_receipt": receipt,
        "run_receipt_sha256": _sha256(receipt_raw),
        "schema_version": _PRIVATE_SCHEMA,
        "tasks_and_split": {
            "conditioning_policy_digest": task_set.policy_digest,
            "group_count": 1,
            "group_policy_digest": group_policy_digest,
            "immutable_task_ids": [
                task.task_id.value for task in task_set.tasks
            ],
            "natural_group_id": task_set.source_group_id,
            "single_group_integrity": len(set(task_set.task_group_ids)) == 1,
        },
        "verdicts": {
            "adversarial_review": "PASS",
            "checkpoint_integrity": "PASS",
            "checkpoint_replay": "PASS",
            "falsification_checks": "PASS",
            "resource_bounds": "PASS",
            "test_runs": "PASS",
        },
    }
    return _ValidatedDomain(
        domain=domain,
        preparation_mode=preparation_mode,
        deterministic_core=deterministic_core,
        private_envelope=private_envelope,
        public_bundle_digest=public_digest,
        forbidden_public_identifiers=forbidden_public_identifiers,
    )


def _public_bundle(domain: _ValidatedDomain) -> bytes:
    value = dict(domain.deterministic_core)
    value["bundle_digest"] = domain.public_bundle_digest
    _reject_public_fields(
        value,
        forbidden_identifiers=domain.forbidden_public_identifiers,
    )
    return _canonical_json_bytes(value)


def _private_bundle(domain: _ValidatedDomain) -> bytes:
    value = dict(domain.private_envelope)
    envelope_digest = _domain_digest(
        "heterodiff.atomic-counting.private-run-attestation.v1", value
    )
    value["attestation_digest"] = envelope_digest
    return _canonical_json_bytes(value)


def _prepare_cross_domain_evidence(
    runs: Sequence[CompletedDomainRun],
    *,
    preparation_mode: _EvidencePreparationMode,
) -> PreparedCrossDomainEvidence:
    """Validate both runs under an internal caller-selected evidence mode."""

    if type(preparation_mode) is not _EvidencePreparationMode:
        raise TypeError("preparation_mode must be an internal mode value")

    if type(runs) not in (tuple, list) or len(runs) != 2:
        raise AtomicCountingEvidenceInputError(
            "exactly two completed domain runs are required"
        )
    if any(type(run) is not CompletedDomainRun for run in runs):
        raise TypeError("runs must contain exact CompletedDomainRun instances")
    by_domain = {run.domain: run for run in runs}
    if set(by_domain) != {
        CountingFixtureDomain.MUSIC,
        CountingFixtureDomain.CLINICAL_STYLE,
    }:
        raise AtomicCountingEvidenceInputError(
            "one music and one clinical-style run are required"
        )
    validated = {
        domain: _validate_domain_run(
            by_domain[domain], preparation_mode=preparation_mode
        )
        for domain in (
            CountingFixtureDomain.MUSIC,
            CountingFixtureDomain.CLINICAL_STYLE,
        )
    }
    execution_class = (
        "SYNTHETIC_TEST_ONLY"
        if preparation_mode is _EvidencePreparationMode.SYNTHETIC_TEST
        else "EVIDENCE_COMPLETE_AWAITING_GATE_DECISION"
    )
    files = {
        "public/music.json": _public_bundle(
            validated[CountingFixtureDomain.MUSIC]
        ),
        "public/clinical_style.json": _public_bundle(
            validated[CountingFixtureDomain.CLINICAL_STYLE]
        ),
        "private/music-run-attestation.json": _private_bundle(
            validated[CountingFixtureDomain.MUSIC]
        ),
        "private/clinical_style-run-attestation.json": _private_bundle(
            validated[CountingFixtureDomain.CLINICAL_STYLE]
        ),
    }
    artifact_manifest = [
        {
            "path": path,
            "schema_version": (
                _PUBLIC_SCHEMA if path.startswith("public/") else _PRIVATE_SCHEMA
            ),
            "sha256": _sha256(payload),
            "size_bytes": len(payload),
            "visibility": "public" if path.startswith("public/") else "private",
        }
        for path, payload in sorted(files.items())
    ]
    manifest_payload: Dict[str, object] = {
        "artifacts": artifact_manifest,
        "domain_public_bundle_digests": {
            domain.value: validated[domain].public_bundle_digest
            for domain in (
                CountingFixtureDomain.MUSIC,
                CountingFixtureDomain.CLINICAL_STYLE,
            )
        },
        "execution_class": execution_class,
        "gate_decision": "NOT_MADE_BY_EVIDENCE_PUBLISHER",
        "gate_id": _GATE_ID,
        "schema_version": _ROOT_SCHEMA,
    }
    manifest_payload["manifest_payload_digest"] = _domain_digest(
        "heterodiff.atomic-counting.evidence-publication-manifest.v1",
        manifest_payload,
    )
    files["manifest.json"] = _canonical_json_bytes(manifest_payload)
    return PreparedCrossDomainEvidence(
        files=files,
        execution_class=execution_class,
        public_bundle_digests={
            domain.value: validated[domain].public_bundle_digest
            for domain in (
                CountingFixtureDomain.MUSIC,
                CountingFixtureDomain.CLINICAL_STYLE,
            )
        },
    )


def prepare_cross_domain_evidence(
    runs: Sequence[CompletedDomainRun],
) -> PreparedCrossDomainEvidence:
    """Production-only, write-free reconstruction of completed evidence.

    The production mode is selected by this API, never by a receipt Boolean.
    Checkpoint inspection is deliberately Torch-free and establishes bounded
    structural compatibility, not provenance authenticity or a trust root.
    """

    return _prepare_cross_domain_evidence(
        runs, preparation_mode=_EvidencePreparationMode.PRODUCTION
    )


def prepare_synthetic_test_evidence(
    runs: Sequence[CompletedDomainRun],
) -> PreparedCrossDomainEvidence:
    """Explicit write-free test path requiring the exact synthetic marker."""

    return _prepare_cross_domain_evidence(
        runs, preparation_mode=_EvidencePreparationMode.SYNTHETIC_TEST
    )


def _safe_entry_name(value: str, *, name: str) -> bytes:
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or unicodedata.normalize("NFC", value) != value
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    ):
        raise AtomicCountingEvidencePublicationError(
            "{} is not a safe directory entry".format(name)
        )
    return os.fsencode(value)


def _select_atomic_backend() -> _AtomicBackend:
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        try:
            function = libc.renameatx_np
        except AttributeError as error:
            raise AtomicCountingAtomicCommitUnsupportedError(
                "macOS renameatx_np is unavailable; no unsafe fallback is admitted"
            ) from error
        function.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        return _AtomicBackend(
            "darwin-renameatx_np-RENAME_EXCL", function, 0x00000004
        )
    if sys.platform.startswith("linux"):
        try:
            function = libc.renameat2
        except AttributeError as error:
            raise AtomicCountingAtomicCommitUnsupportedError(
                "Linux libc renameat2 is unavailable; no syscall-number fallback is admitted"
            ) from error
        function.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        return _AtomicBackend(
            "linux-renameat2-RENAME_NOREPLACE", function, 1
        )
    raise AtomicCountingAtomicCommitUnsupportedError(
        "atomic no-replace publication is admitted only on macOS and Linux"
    )


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
    if error_number in (errno.EEXIST, errno.ENOTEMPTY):
        raise AtomicCountingEvidencePublicationError(
            "output directory appeared during publication; no-replace commit refused it"
        )
    if error_number in {
        errno.ENOSYS,
        errno.EINVAL,
        getattr(errno, "ENOTSUP", errno.EINVAL),
        getattr(errno, "EOPNOTSUPP", errno.EINVAL),
    }:
        raise AtomicCountingAtomicCommitUnsupportedError(
            "output filesystem lacks the required atomic no-replace primitive"
        )
    raise OSError(error_number, os.strerror(error_number), output_name)


def _directory_identity(status: os.stat_result) -> Tuple[int, int, int]:
    return (status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode))


def _open_output_parent(output: Path) -> Tuple[int, Path, Tuple[int, int, int]]:
    if not output.name or output.name in {".", ".."}:
        raise AtomicCountingEvidencePublicationError(
            "output directory must name one new child"
        )
    _safe_entry_name(output.name, name="output directory name")
    _reject_symlink_components(output, final_must_exist=False)
    parent = output.parent.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(parent, flags)
    try:
        opened = os.fstat(descriptor)
        named = parent.lstat()
        identity = _directory_identity(opened)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or stat.S_ISLNK(named.st_mode)
            or identity != _directory_identity(named)
        ):
            raise AtomicCountingEvidencePublicationError(
                "output parent is not one stable non-symlink directory"
            )
        try:
            os.stat(output.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise AtomicCountingEvidencePublicationError(
                "output directory already exists and will not be overwritten"
            )
        return descriptor, parent, identity
    except BaseException:
        os.close(descriptor)
        raise


def _revalidate_output_parent(
    descriptor: int, path: Path, identity: Tuple[int, int, int]
) -> None:
    opened = os.fstat(descriptor)
    named = path.lstat()
    _reject_symlink_components(path, final_must_exist=True)
    if (
        identity != _directory_identity(opened)
        or identity != _directory_identity(named)
        or stat.S_ISLNK(named.st_mode)
    ):
        raise AtomicCountingEvidencePublicationError(
            "output parent changed during publication"
        )


def _write_file_at(
    directory_fd: int, name: str, payload: bytes, *, mode: int
) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, mode, dir_fd=directory_fd)
    try:
        os.fchmod(descriptor, mode)
        position = 0
        while position < len(payload):
            written = os.write(descriptor, payload[position:])
            if written <= 0:
                raise AtomicCountingEvidencePublicationError(
                    "short write while staging evidence"
                )
            position += written
        os.fsync(descriptor)
        status = os.fstat(descriptor)
        if (
            not stat.S_ISREG(status.st_mode)
            or stat.S_IMODE(status.st_mode) != mode
            or status.st_size != len(payload)
        ):
            raise AtomicCountingEvidencePublicationError(
                "staged evidence file metadata is invalid"
            )
    finally:
        os.close(descriptor)


def _verify_staged_tree(
    stage_fd: int, public_fd: int, private_fd: int, prepared: PreparedCrossDomainEvidence
) -> None:
    if set(os.listdir(stage_fd)) != {"manifest.json", "public", "private"}:
        raise AtomicCountingEvidencePublicationError(
            "staged evidence root has unexpected entries"
        )
    if set(os.listdir(public_fd)) != {"music.json", "clinical_style.json"}:
        raise AtomicCountingEvidencePublicationError(
            "staged public directory has unexpected entries"
        )
    if set(os.listdir(private_fd)) != {
        "music-run-attestation.json",
        "clinical_style-run-attestation.json",
    }:
        raise AtomicCountingEvidencePublicationError(
            "staged private directory has unexpected entries"
        )
    checks = (
        (stage_fd, "manifest.json", "manifest.json", 0o644),
        (public_fd, "music.json", "public/music.json", 0o644),
        (
            public_fd,
            "clinical_style.json",
            "public/clinical_style.json",
            0o644,
        ),
        (
            private_fd,
            "music-run-attestation.json",
            "private/music-run-attestation.json",
            0o600,
        ),
        (
            private_fd,
            "clinical_style-run-attestation.json",
            "private/clinical_style-run-attestation.json",
            0o600,
        ),
    )
    for descriptor, entry, relative, mode in checks:
        status = os.stat(entry, dir_fd=descriptor, follow_symlinks=False)
        if (
            not stat.S_ISREG(status.st_mode)
            or stat.S_IMODE(status.st_mode) != mode
            or status.st_size != len(prepared.files[relative])
        ):
            raise AtomicCountingEvidencePublicationError(
                "staged file {} failed metadata verification".format(relative)
            )
    if (
        stat.S_IMODE(os.fstat(public_fd).st_mode) != 0o755
        or stat.S_IMODE(os.fstat(private_fd).st_mode) != 0o700
    ):
        raise AtomicCountingEvidencePublicationError(
            "staged public/private directory modes are invalid"
        )


def _cleanup_stage(parent_fd: int, stage_name: str) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        stage_fd = os.open(stage_name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        return
    try:
        for directory, files in (
            ("public", ("music.json", "clinical_style.json")),
            (
                "private",
                (
                    "music-run-attestation.json",
                    "clinical_style-run-attestation.json",
                ),
            ),
        ):
            try:
                child_fd = os.open(directory, flags, dir_fd=stage_fd)
            except FileNotFoundError:
                continue
            try:
                for file_name in files:
                    try:
                        os.unlink(file_name, dir_fd=child_fd)
                    except FileNotFoundError:
                        pass
            finally:
                os.close(child_fd)
            try:
                os.rmdir(directory, dir_fd=stage_fd)
            except FileNotFoundError:
                pass
        try:
            os.unlink("manifest.json", dir_fd=stage_fd)
        except FileNotFoundError:
            pass
    finally:
        os.close(stage_fd)
    try:
        os.rmdir(stage_name, dir_fd=parent_fd)
    except FileNotFoundError:
        pass


def _publish_prepared_evidence(
    prepared: PreparedCrossDomainEvidence, output_directory: PathLike
) -> EvidencePublicationResult:
    output = Path(output_directory)
    parent_fd, parent_path, parent_identity = _open_output_parent(output)
    backend = _select_atomic_backend()
    stage_name: Optional[str] = None
    committed = False
    try:
        for _attempt in range(128):
            candidate = ".{}-{}.staging".format(
                output.name, secrets.token_hex(12)
            )
            _safe_entry_name(candidate, name="staging directory name")
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            stage_name = candidate
            break
        if stage_name is None:
            raise AtomicCountingEvidencePublicationError(
                "could not allocate a unique staging directory"
            )
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        stage_fd = os.open(stage_name, flags, dir_fd=parent_fd)
        try:
            os.mkdir("public", 0o755, dir_fd=stage_fd)
            os.mkdir("private", 0o700, dir_fd=stage_fd)
            public_fd = os.open("public", flags, dir_fd=stage_fd)
            private_fd = os.open("private", flags, dir_fd=stage_fd)
            try:
                os.fchmod(public_fd, 0o755)
                os.fchmod(private_fd, 0o700)
                _write_file_at(
                    stage_fd,
                    "manifest.json",
                    prepared.files["manifest.json"],
                    mode=0o644,
                )
                _write_file_at(
                    public_fd,
                    "music.json",
                    prepared.files["public/music.json"],
                    mode=0o644,
                )
                _write_file_at(
                    public_fd,
                    "clinical_style.json",
                    prepared.files["public/clinical_style.json"],
                    mode=0o644,
                )
                _write_file_at(
                    private_fd,
                    "music-run-attestation.json",
                    prepared.files["private/music-run-attestation.json"],
                    mode=0o600,
                )
                _write_file_at(
                    private_fd,
                    "clinical_style-run-attestation.json",
                    prepared.files[
                        "private/clinical_style-run-attestation.json"
                    ],
                    mode=0o600,
                )
                os.fsync(public_fd)
                os.fsync(private_fd)
                _verify_staged_tree(stage_fd, public_fd, private_fd, prepared)
            finally:
                os.close(private_fd)
                os.close(public_fd)
            os.fchmod(stage_fd, 0o755)
            os.fsync(stage_fd)
        finally:
            os.close(stage_fd)
        _revalidate_output_parent(parent_fd, parent_path, parent_identity)
        try:
            os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise AtomicCountingEvidencePublicationError(
                "output directory appeared before the no-replace commit"
            )
        _atomic_commit_noreplace(
            backend,
            parent_fd=parent_fd,
            staging_name=stage_name,
            output_name=output.name,
        )
        committed = True
        resolved_output = parent_path / output.name
        result = EvidencePublicationResult(
            output_directory=resolved_output,
            status="PUBLISHED_DURABILITY_UNCONFIRMED",
            atomic_backend=backend.name,
            execution_class=prepared.execution_class,
            manifest_sha256=_sha256(prepared.files["manifest.json"]),
            manifest_size_bytes=len(prepared.files["manifest.json"]),
            public_bundle_digests=prepared.public_bundle_digests,
        )
        try:
            os.fsync(parent_fd)
        except OSError as error:
            raise AtomicCountingDurabilityUnconfirmedError(
                "evidence directory is visible but parent-directory durability is unconfirmed",
                result,
            ) from error
        return EvidencePublicationResult(
            output_directory=resolved_output,
            status="PUBLISHED_DURABLE",
            atomic_backend=backend.name,
            execution_class=prepared.execution_class,
            manifest_sha256=result.manifest_sha256,
            manifest_size_bytes=result.manifest_size_bytes,
            public_bundle_digests=prepared.public_bundle_digests,
        )
    finally:
        if stage_name is not None and not committed:
            _cleanup_stage(parent_fd, stage_name)
        os.close(parent_fd)


def publish_cross_domain_evidence(
    runs: Sequence[CompletedDomainRun], output_directory: PathLike
) -> EvidencePublicationResult:
    """Production entry point: validate and durably publish both domain runs.

    The internal production mode, rather than a self-declared receipt field,
    controls validation.  Successful publication means only that a complete
    evidence object awaits an external gate decision; this function never
    returns or records ``REFERENCE-GO``.
    """

    prepared = prepare_cross_domain_evidence(runs)
    return _publish_prepared_evidence(prepared, output_directory)


def publish_synthetic_test_evidence(
    runs: Sequence[CompletedDomainRun], output_directory: PathLike
) -> EvidencePublicationResult:
    """Explicit test-only path used to falsify publication and verification."""

    prepared = prepare_synthetic_test_evidence(runs)
    if prepared.execution_class != "SYNTHETIC_TEST_ONLY":
        raise AtomicCountingEvidencePrerequisiteError(
            "test publisher accepts only SYNTHETIC_TEST_ONLY inputs"
        )
    return _publish_prepared_evidence(prepared, output_directory)


def _verify_prepared_tree(
    prepared: PreparedCrossDomainEvidence, output_directory: PathLike
) -> EvidenceVerificationResult:
    output = Path(output_directory)
    _reject_symlink_components(output, final_must_exist=True)
    status = output.lstat()
    if not stat.S_ISDIR(status.st_mode) or stat.S_IMODE(status.st_mode) != 0o755:
        raise AtomicCountingEvidenceInputError(
            "published evidence root must be a mode-0755 directory"
        )
    if set(os.listdir(output)) != {"manifest.json", "public", "private"}:
        raise AtomicCountingEvidenceInputError(
            "published evidence root has missing or unknown entries"
        )
    for directory, mode, entries in (
        ("public", 0o755, {"music.json", "clinical_style.json"}),
        (
            "private",
            0o700,
            {"music-run-attestation.json", "clinical_style-run-attestation.json"},
        ),
    ):
        path = output / directory
        child_status = path.lstat()
        if (
            not stat.S_ISDIR(child_status.st_mode)
            or stat.S_ISLNK(child_status.st_mode)
            or stat.S_IMODE(child_status.st_mode) != mode
            or set(os.listdir(path)) != entries
        ):
            raise AtomicCountingEvidenceInputError(
                "published {} directory is invalid".format(directory)
            )
    for relative, expected in prepared.files.items():
        mode = 0o600 if relative.startswith("private/") else 0o644
        path = output / relative
        raw = _read_verified_file(path, limit=_MAX_OUTPUT_BYTES, name=relative)
        if stat.S_IMODE(path.lstat().st_mode) != mode:
            raise AtomicCountingEvidenceInputError(
                "published file {} has the wrong mode".format(relative)
            )
        if raw != expected:
            raise AtomicCountingEvidenceInputError(
                "published file {} differs from independent reconstruction".format(
                    relative
                )
            )
    return EvidenceVerificationResult(
        output_directory=output.resolve(strict=True),
        status="VERIFIED_BYTE_IDENTICAL_CORE_AND_ATTESTATION",
        execution_class=prepared.execution_class,
        manifest_sha256=_sha256(prepared.files["manifest.json"]),
        public_bundle_digests=prepared.public_bundle_digests,
    )


def verify_published_cross_domain_evidence(
    runs: Sequence[CompletedDomainRun], output_directory: PathLike
) -> EvidenceVerificationResult:
    """Production verifier; rebuild every byte and reject synthetic objects."""

    output = Path(output_directory)
    _raw, manifest = _load_json_file(
        output / "manifest.json",
        limit=_MAX_RECEIPT_BYTES,
        name="production published-manifest preflight",
    )
    if manifest.get("execution_class") == "SYNTHETIC_TEST_ONLY":
        raise AtomicCountingEvidencePrerequisiteError(
            "production verification refuses SYNTHETIC_TEST_ONLY inputs"
        )
    prepared = prepare_cross_domain_evidence(runs)
    return _verify_prepared_tree(prepared, output_directory)


def verify_synthetic_test_evidence(
    runs: Sequence[CompletedDomainRun], output_directory: PathLike
) -> EvidenceVerificationResult:
    """Explicit test-only verifier for a synthetic publisher fixture."""

    prepared = prepare_synthetic_test_evidence(runs)
    if prepared.execution_class != "SYNTHETIC_TEST_ONLY":
        raise AtomicCountingEvidencePrerequisiteError(
            "test verifier accepts only SYNTHETIC_TEST_ONLY inputs"
        )
    return _verify_prepared_tree(prepared, output_directory)


__all__ = [
    "AtomicCountingAtomicCommitUnsupportedError",
    "AtomicCountingDurabilityUnconfirmedError",
    "AtomicCountingEvidenceError",
    "AtomicCountingEvidenceInputError",
    "AtomicCountingEvidencePrerequisiteError",
    "AtomicCountingEvidencePublicationError",
    "CompletedDomainRun",
    "EVIDENCE_EXECUTION_BLOCKER",
    "EVIDENCE_EXECUTION_STATUS",
    "EvidencePublicationResult",
    "EvidenceVerificationResult",
    "PreparedCrossDomainEvidence",
    "prepare_cross_domain_evidence",
    "prepare_synthetic_test_evidence",
    "publish_cross_domain_evidence",
    "publish_synthetic_test_evidence",
    "repository_evidence_status",
    "verify_published_cross_domain_evidence",
    "verify_synthetic_test_evidence",
]
