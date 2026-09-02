"""Offline successor that connects the selected Test-28 state to the path.

This module repairs one narrow whole-method beta integration gap.  It does not
generalize the bounded two-macrostep path and does not widen any production,
Formal-Test, B12, runtime, data, training, scientific, or result state.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct
import sys
from types import FunctionType, ModuleType
from typing import Mapping, Optional, Tuple

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_tilt
from heterodiff.evaluation import formal_test29_test30_single_macrostep_integration as single
from heterodiff.evaluation import formal_test29_test30_two_macrostep_path_qualification as two
from heterodiff.evaluation import formal_test30_synthetic_coupled_path_qualification as test30
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as cp62
from heterodiff.processes import certified_initial_score_provider_v1 as score_facade
from heterodiff.processes import plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as initializer
from heterodiff.processes import formal_test29_finite_acyclic_route_oracle as test29
from heterodiff.theory.configuration_reference import TransformedEvent


SCHEMA_VERSION = "heterodiff-b12-whole-method-initializer-path-successor-v1"
CORE_SCHEMA = "heterodiff-b12-whole-method-initializer-path-core-v1"
RECEIPT_SCHEMA = "heterodiff-b12-whole-method-initializer-path-receipt-v1"
STATE = "OFFLINE_NONCONFIRMATORY_WHOLE_METHOD_BETA_INTEGRATED"
TRANSFORM_POLICY_ID = (
    "TEST28-TYPE-PARITY-FIRST-COORDINATE-ZERO-DIM-ZERO-TO-PATH-STATE-V1"
)
PATH_POLICY_ID = "BOUNDED-TWO-MACROSTEP-HEUN-EDIT-PATH-V1"
PROPOSED_TASK = (
    "Produce whole-method beta: initializer, continuous path, jump/edit law, "
    "and sampler integrated."
)
INDEPENDENT_RELATIVE_PATH = (
    "src/heterodiff/evaluation/"
    "b12_whole_method_initializer_path_integration_recomputation.py"
)
EXPECTED_INDEPENDENT_SOURCE_SHA256 = (
    "5c01fb8a195402cf012a815b92bcec13b86845bc088f8b1152d28aa6153a5f5f"
)
EXPECTED_INDEPENDENT_SOURCE_BYTES = 32_508
FROZEN_WORDS = (2, 27)
MACROSTEP_WIDTH = 0.25
RUN_ID = 29_032
MAX_TRANSFORM_EVENTS = 10_000
DIRECT_PUBLIC_API_CUSTODY_AUTHENTICATED = False
AUTHORITATIVE_QUALIFICATION_REQUIRES_ISOLATED_VALIDATOR = True
PREDECESSOR_MACHINE_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)
PREDECESSOR_MACHINE_SHA256 = (
    "a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b"
)
PREDECESSOR_RECORD_SHA256 = (
    "451ef6059fea8cb2f98128c388056bcd82739645a97dfdd56021055744cb04af"
)
PREDECESSOR_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)
FROZEN_INPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
FROZEN_INPUT_DOMAIN = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
FROZEN_INITIALIZER_ROW_ORDINAL = 5
FROZEN_INITIALIZER_SEED = int("12a5228200019dae", 16)
FROZEN_CHECKPOINT_STEP = 256
FROZEN_SUPPLIED_INPUT_SHA256 = (
    "f7e213442d073f88df73d2b33c21e43add4269a8a45b07714bfbd60b4b4ff971"
)
REAL_RESIDUAL_IDS = (
    "B02_REAL_DATA_ACQUISITION",
    "B03_REAL_DATA_SPLIT_AND_ESCROW",
    "B08_RUNTIME_COMPUTE_ENVELOPE",
    "B09_REAL_LICENSE_PRIVACY_APPROVALS",
    "F172_PROSPECTIVE_FREEZE_AFTER_TEST_SEAL",
    "ALL_PREEXECUTION_ARTIFACTS_ACCEPTED",
    "PRIMARY_64_DIMENSION_CONTEXT_ENCODER",
    "PRIMARY_DOMAIN_SCALE_RUNTIME",
    "PRIMARY_ADAPTER_RETAIL",
    "PRIMARY_ADAPTER_PHYSIONET",
    "CONTROL_ADAPTER_RETAIL",
    "CONTROL_ADAPTER_PHYSIONET",
    "LITERATURE_FAMILY_ADAPTER_RETAIL",
    "LITERATURE_FAMILY_ADAPTER_PHYSIONET",
    "CSDI_AUTHOR_EXTENSION_1",
    "CSDI_AUTHOR_EXTENSION_2",
    "CSDI_AUTHOR_EXTENSION_3",
    "CSDI_AUTHOR_EXTENSION_4",
    "EDITPP_AUTHOR_EXTENSION_1",
    "EDITPP_AUTHOR_EXTENSION_2",
    "EDITPP_AUTHOR_EXTENSION_3",
    "EDITPP_AUTHOR_EXTENSION_4",
    "PRODUCTION_SCHEMA_EXTERNAL_ACCEPTANCE",
    "RUNNER_AND_RECOMPUTATION",
    "UNCONDITIONAL_OPERATIONAL_PREDICTIONS",
    "PRODUCTION_RUNTIME_AND_DURABILITY",
    "TEST28_PRODUCTION_GATE_01",
    "TEST28_PRODUCTION_GATE_02",
    "TEST28_PRODUCTION_GATE_03",
    "TEST28_PRODUCTION_GATE_04",
    "TEST28_PRODUCTION_GATE_05",
    "TEST28_PRODUCTION_GATE_06",
    "TEST28_PRODUCTION_GATE_07",
    "TEST28_PRODUCTION_GATE_08",
    "TEST28_PRODUCTION_GATE_09",
    "TEST28_PRODUCTION_GATE_10",
    "TEST28_PRODUCTION_GATE_11",
    "TEST28_PRODUCTION_GATE_12",
    "TEST28_PRODUCTION_GATE_13",
    "TEST28_PRODUCTION_GATE_14",
    "TEST28_PRODUCTION_GATE_15",
    "TEST28_PRODUCTION_GATE_16",
    "TEST28_PRODUCTION_GATE_17",
    "TEST29_PRODUCTION_ROUTE_RECEIPT",
    "TEST29_WHOLE_METHOD_RESIDUAL",
    "TEST30_PRODUCTION_COUPLED_PATH_RECEIPT",
    "TEST30_WHOLE_METHOD_RESIDUAL",
    "REAL_IMMUTABLE_EXECUTION_LEDGER",
    "INDEPENDENT_REAL_RECOMPUTATION_RECEIPT",
    "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED",
)
if len(REAL_RESIDUAL_IDS) != 50 or len(set(REAL_RESIDUAL_IDS)) != 50:
    raise RuntimeError("frozen open residual roster is not exact-50 unique")


class WholeMethodInitializerPathError(ValueError):
    """Raised before a malformed value crosses the successor boundary."""


@dataclass(frozen=True)
class FrozenSuppliedInput:
    schema_version: str
    initializer_row_ordinal: int
    initializer_seed: int
    path_first_word: int
    path_second_word: int
    checkpoint_step: int
    input_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not FrozenSuppliedInput:
            raise TypeError("supplied input must have exact successor type")
        payload = {
            "checkpoint_step": self.checkpoint_step,
            "initializer_row_ordinal": self.initializer_row_ordinal,
            "initializer_seed": self.initializer_seed,
            "path_first_word": self.path_first_word,
            "path_second_word": self.path_second_word,
            "schema_version": self.schema_version,
        }
        if (
            self.schema_version != FROZEN_INPUT_SCHEMA
            or type(self.initializer_row_ordinal) is not int
            or self.initializer_row_ordinal != FROZEN_INITIALIZER_ROW_ORDINAL
            or type(self.initializer_seed) is not int
            or self.initializer_seed != FROZEN_INITIALIZER_SEED
            or type(self.path_first_word) is not int
            or type(self.path_second_word) is not int
            or (self.path_first_word, self.path_second_word) != FROZEN_WORDS
            or type(self.checkpoint_step) is not int
            or self.checkpoint_step != FROZEN_CHECKPOINT_STEP
        ):
            raise WholeMethodInitializerPathError("frozen supplied input differs")
        if self.input_sha256 != _domain_sha256(FROZEN_INPUT_DOMAIN, payload):
            raise WholeMethodInitializerPathError("frozen supplied input digest differs")
        if self.input_sha256 != FROZEN_SUPPLIED_INPUT_SHA256:
            raise WholeMethodInitializerPathError("frozen supplied input pin differs")
        return payload


def build_frozen_supplied_input() -> FrozenSuppliedInput:
    payload = {
        "checkpoint_step": FROZEN_CHECKPOINT_STEP,
        "initializer_row_ordinal": FROZEN_INITIALIZER_ROW_ORDINAL,
        "initializer_seed": FROZEN_INITIALIZER_SEED,
        "path_first_word": FROZEN_WORDS[0],
        "path_second_word": FROZEN_WORDS[1],
        "schema_version": FROZEN_INPUT_SCHEMA,
    }
    value = FrozenSuppliedInput(
        **payload,
        input_sha256=_domain_sha256(FROZEN_INPUT_DOMAIN, payload),
    )
    value.payload()
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    if type(domain) is not str or not domain or not domain.isascii() or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty ASCII text")
    return _sha256(domain.encode("ascii") + b"\0" + _canonical(value))


def _exact_sha256(value: object, *, name: str, nonzero: bool = True) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        or (nonzero and value == "0" * 64)
    ):
        raise WholeMethodInitializerPathError(name + " must be lowercase SHA-256")
    return value


def _json_pairs(pairs):
    if type(pairs) is not list:
        raise WholeMethodInitializerPathError("JSON pair roster differs")
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise WholeMethodInitializerPathError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _predecessor_binding(project_root: str) -> Mapping[str, object]:
    raw = _capture_stable_relative(
        project_root,
        PREDECESSOR_MACHINE_RELATIVE_PATH,
        expected_size=9789,
        expected_sha256=PREDECESSOR_MACHINE_SHA256,
    )
    if not raw.endswith(b"\n"):
        raise WholeMethodInitializerPathError("predecessor machine bytes differ")
    try:
        machine = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_json_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WholeMethodInitializerPathError("predecessor machine JSON differs") from error
    if type(machine) is not dict or _canonical(machine) + b"\n" != raw:
        raise WholeMethodInitializerPathError("predecessor machine is noncanonical")
    record_sha256 = machine.get("record_sha256")
    unsigned = dict(machine)
    unsigned.pop("record_sha256", None)
    if (
        record_sha256 != PREDECESSOR_RECORD_SHA256
        or record_sha256
        != _domain_sha256(
            "heterodiff-b12-whole-method-nonconfirmatory-runner-candidate-v1",
            unsigned,
        )
    ):
        raise WholeMethodInitializerPathError("predecessor self-record differs")
    receipt = machine["semantics"]["receipt"]
    route = machine["route_binding"]
    if (
        receipt["receipt_sha256"] != PREDECESSOR_RECEIPT_SHA256
        or route["stable_receipt_sha256"] != PREDECESSOR_RECEIPT_SHA256
        or route["supplied_input_sha256"] != FROZEN_SUPPLIED_INPUT_SHA256
        or route["open_residual_slot_count"] != 50
        or route["confirmatory_evidence"] is not False
    ):
        raise WholeMethodInitializerPathError("predecessor route boundary differs")
    return {
        "core_output_sha256": receipt["core_output_sha256"],
        "machine_raw_sha256": PREDECESSOR_MACHINE_SHA256,
        "machine_record_sha256": PREDECESSOR_RECORD_SHA256,
        "receipt_schema": receipt["schema_version"],
        "receipt_sha256": PREDECESSOR_RECEIPT_SHA256,
        "route_binding": dict(route),
    }


def _file_identity(metadata: os.stat_result) -> tuple:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _capture_stable_relative(
    project_root: str,
    relative_path: str,
    *,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    parts = tuple(relative_path.split("/"))
    if any(not part or part in (".", "..") for part in parts):
        raise WholeMethodInitializerPathError("captured path is noncanonical")
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(project_root, root_flags)
    opened = []
    try:
        root_before = os.fstat(root_fd)
        current = root_fd
        parents = []
        for part in parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            parents.append((descriptor, _file_identity(os.fstat(descriptor))))
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf = os.open(parts[-1], flags, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or before.st_size != expected_size
        ):
            raise WholeMethodInitializerPathError("captured file custody differs")
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        if (
            len(raw) != before.st_size
            or _sha256(raw) != expected_sha256
            or _file_identity(before) != _file_identity(os.fstat(leaf))
            or _file_identity(root_before) != _file_identity(os.fstat(root_fd))
            or any(
                identity != _file_identity(os.fstat(descriptor))
                for descriptor, identity in parents
            )
        ):
            raise WholeMethodInitializerPathError("captured file changed or differs")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _captured_independent_bytes(project_root: str) -> Tuple[bytes, str]:
    parts = tuple(INDEPENDENT_RELATIVE_PATH.split("/"))
    if any(not part or part in (".", "..") for part in parts):
        raise WholeMethodInitializerPathError("independent path is noncanonical")
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(project_root, root_flags)
    opened = []
    try:
        root_before = os.fstat(root_fd)
        current = root_fd
        parent_identities = []
        for part in parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            parent_identities.append((descriptor, _file_identity(os.fstat(descriptor))))
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf = os.open(parts[-1], flags, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or before.st_size != EXPECTED_INDEPENDENT_SOURCE_BYTES
        ):
            raise WholeMethodInitializerPathError("independent source custody differs")
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        if (
            len(raw) != before.st_size
            or _file_identity(before) != _file_identity(os.fstat(leaf))
            or _file_identity(root_before) != _file_identity(os.fstat(root_fd))
            or any(
                identity != _file_identity(os.fstat(descriptor))
                for descriptor, identity in parent_identities
            )
            or _sha256(raw) != EXPECTED_INDEPENDENT_SOURCE_SHA256
        ):
            raise WholeMethodInitializerPathError("independent source changed or differs")
        return raw, str(Path(project_root) / INDEPENDENT_RELATIVE_PATH)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _captured_independent_recomputation(project_root: str) -> Tuple[bytes, str]:
    raw, path = _captured_independent_bytes(project_root)
    target_name = (
        "heterodiff.evaluation."
        "b12_whole_method_initializer_path_integration_recomputation"
    )
    attribute = target_name.rsplit(".", 1)[1]
    import heterodiff.evaluation as evaluation_package

    missing = object()
    saved_module = sys.modules.get(target_name, missing)
    saved_attribute = getattr(evaluation_package, attribute, missing)
    module = ModuleType(target_name)
    module.__file__ = path
    module.__package__ = target_name.rpartition(".")[0]
    try:
        sys.modules[target_name] = module
        setattr(evaluation_package, attribute, module)
        code = compile(raw, path, "exec", dont_inherit=True)
        exec(code, module.__dict__)
        callback = getattr(module, "independently_recompute_beta_successor", None)
        if type(callback) is not FunctionType:
            raise WholeMethodInitializerPathError("captured callback differs")
        result = callback(project_root)
        if type(result) is not bytes:
            raise WholeMethodInitializerPathError("captured result must be exact bytes")
        return result, _sha256(raw)
    finally:
        if saved_module is missing:
            sys.modules.pop(target_name, None)
        else:
            sys.modules[target_name] = saved_module
        if saved_attribute is missing:
            try:
                delattr(evaluation_package, attribute)
            except AttributeError:
                pass
        else:
            setattr(evaluation_package, attribute, saved_attribute)


def _configuration_sha256(configuration: object) -> str:
    if type(configuration) is not tuple or len(configuration) > MAX_TRANSFORM_EVENTS:
        raise TypeError("configuration must be an exact bounded tuple")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-certified-initial-score-state-v1\0")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    for ordinal, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise TypeError("configuration must contain exact TransformedEvent values")
        digest.update(ordinal.to_bytes(8, "big", signed=False))
        digest.update(event.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(event.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _event_sha256(event: TransformedEvent, ordinal: int) -> str:
    return _domain_sha256(
        "heterodiff-b12-beta-selected-event-v1",
        {
            "coordinate_hex": [coordinate.hex() for coordinate in event.coordinates],
            "event_type": event.event_type,
            "ordinal": ordinal,
        },
    )


@dataclass(frozen=True)
class IntegratedPathOccurrence:
    serial: int
    kind: str
    coordinate: float
    role: str
    source_event_ordinal: Optional[int]
    source_event_sha256: Optional[str]

    def payload(self) -> Mapping[str, object]:
        if type(self) is not IntegratedPathOccurrence:
            raise TypeError("occurrence must have exact integrated type")
        if type(self.serial) is not int or not 1 <= self.serial <= MAX_TRANSFORM_EVENTS + 3:
            raise WholeMethodInitializerPathError("occurrence serial differs")
        if type(self.kind) is not str or self.kind not in ("A", "B"):
            raise WholeMethodInitializerPathError("occurrence kind differs")
        if type(self.coordinate) is not float or not math.isfinite(self.coordinate):
            raise WholeMethodInitializerPathError("occurrence coordinate differs")
        if self.role not in ("SELECTED_EVENT", "PATH_BIRTH"):
            raise WholeMethodInitializerPathError("occurrence role differs")
        if self.role == "SELECTED_EVENT":
            if type(self.source_event_ordinal) is not int or self.source_event_ordinal < 0:
                raise WholeMethodInitializerPathError("source ordinal differs")
            _exact_sha256(self.source_event_sha256, name="source event digest")
        elif self.source_event_ordinal is not None or self.source_event_sha256 is not None:
            raise WholeMethodInitializerPathError("synthetic occurrence has source claim")
        return {
            "coordinate_hex": self.coordinate.hex(),
            "kind": self.kind,
            "role": self.role,
            "serial": self.serial,
            "source_event_ordinal": self.source_event_ordinal,
            "source_event_sha256": self.source_event_sha256,
        }


def _state_payload(occurrences: Tuple[IntegratedPathOccurrence, ...]) -> list:
    if type(occurrences) is not tuple:
        raise WholeMethodInitializerPathError("path state must be an exact tuple")
    if any(type(item) is not IntegratedPathOccurrence for item in occurrences):
        raise TypeError("path state contains a non-exact occurrence")
    if tuple(item.serial for item in occurrences) != tuple(
        sorted(item.serial for item in occurrences)
    ) or len({item.serial for item in occurrences}) != len(occurrences):
        raise WholeMethodInitializerPathError("path occurrence serial custody differs")
    return [dict(item.payload()) for item in occurrences]


def _state_sha256(occurrences: Tuple[IntegratedPathOccurrence, ...]) -> str:
    return _domain_sha256(
        "heterodiff-b12-beta-integrated-path-state-v1", _state_payload(occurrences)
    )


@dataclass(frozen=True)
class InitializerPathState:
    schema_version: str
    transform_policy_id: str
    selected_configuration_sha256: str
    source_event_count: int
    empty_configuration_initial_state: bool
    occurrences: Tuple[IntegratedPathOccurrence, ...]
    initial_state_sha256: str
    transform_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not InitializerPathState:
            raise TypeError("state must have exact initializer-path type")
        if self.schema_version != SCHEMA_VERSION or self.transform_policy_id != TRANSFORM_POLICY_ID:
            raise WholeMethodInitializerPathError("transform schema or policy differs")
        _exact_sha256(
            self.selected_configuration_sha256,
            name="selected configuration digest",
        )
        if type(self.source_event_count) is not int or not 0 <= self.source_event_count <= MAX_TRANSFORM_EVENTS:
            raise WholeMethodInitializerPathError("source event count differs")
        if type(self.empty_configuration_initial_state) is not bool:
            raise TypeError("empty-state flag must be exact bool")
        occurrence_payload = _state_payload(self.occurrences)
        if self.empty_configuration_initial_state:
            if (
                self.source_event_count != 0
                or self.occurrences
            ):
                raise WholeMethodInitializerPathError("empty configuration semantics differ")
        else:
            if self.source_event_count != len(self.occurrences) or any(
                item.role != "SELECTED_EVENT" or item.source_event_ordinal != ordinal
                for ordinal, item in enumerate(self.occurrences)
            ):
                raise WholeMethodInitializerPathError("selected event roster differs")
        if self.initial_state_sha256 != _domain_sha256(
            "heterodiff-b12-beta-integrated-path-state-v1", occurrence_payload
        ):
            raise WholeMethodInitializerPathError("initial state digest differs")
        payload = {
            "empty_configuration_initial_state": self.empty_configuration_initial_state,
            "initial_state_sha256": self.initial_state_sha256,
            "occurrences": occurrence_payload,
            "schema_version": self.schema_version,
            "selected_configuration_sha256": self.selected_configuration_sha256,
            "source_event_count": self.source_event_count,
            "transform_policy_id": self.transform_policy_id,
        }
        if self.transform_sha256 != _domain_sha256(
            "heterodiff-b12-beta-initializer-path-transform-v1", payload
        ):
            raise WholeMethodInitializerPathError("transform digest differs")
        return payload


def transform_selected_configuration(
    configuration: object, selected_configuration_sha256: object
) -> InitializerPathState:
    """Map one exact selected configuration into a typed numerical path state."""

    digest = _configuration_sha256(configuration)
    if selected_configuration_sha256 != digest:
        raise WholeMethodInitializerPathError("selected configuration digest differs")
    occurrences = []
    for ordinal, event in enumerate(configuration):
        if event.event_type == 0 and event.coordinates != ():
            raise WholeMethodInitializerPathError("type-0 event must be zero-dimensional")
        if event.event_type == 1 and len(event.coordinates) != 1:
            raise WholeMethodInitializerPathError("type-1 event must be one-dimensional")
        if event.event_type not in (0, 1):
            raise WholeMethodInitializerPathError("selected event type is outside the frozen law")
        coordinate = 0.0 if event.event_type == 0 else event.coordinates[0]
        occurrences.append(
            IntegratedPathOccurrence(
                serial=ordinal + 1,
                kind="A" if event.event_type % 2 == 0 else "B",
                coordinate=float(coordinate),
                role="SELECTED_EVENT",
                source_event_ordinal=ordinal,
                source_event_sha256=_event_sha256(event, ordinal),
            )
        )
    empty = not occurrences
    exact_occurrences = tuple(occurrences)
    initial_sha256 = _state_sha256(exact_occurrences)
    payload = {
        "empty_configuration_initial_state": empty,
        "initial_state_sha256": initial_sha256,
        "occurrences": _state_payload(exact_occurrences),
        "schema_version": SCHEMA_VERSION,
        "selected_configuration_sha256": digest,
        "source_event_count": len(configuration),
        "transform_policy_id": TRANSFORM_POLICY_ID,
    }
    result = InitializerPathState(
        schema_version=SCHEMA_VERSION,
        transform_policy_id=TRANSFORM_POLICY_ID,
        selected_configuration_sha256=digest,
        source_event_count=len(configuration),
        empty_configuration_initial_state=empty,
        occurrences=exact_occurrences,
        initial_state_sha256=initial_sha256,
        transform_sha256=_domain_sha256(
            "heterodiff-b12-beta-initializer-path-transform-v1", payload
        ),
    )
    result.payload()
    return result


def validate_initializer_path_state(
    state: InitializerPathState, configuration: object
) -> InitializerPathState:
    if type(state) is not InitializerPathState:
        raise TypeError("state must have exact initializer-path type")
    state.payload()
    expected = transform_selected_configuration(
        configuration, state.selected_configuration_sha256
    )
    if state != expected:
        raise WholeMethodInitializerPathError("state differs from selected configuration")
    return state


def _execute_frozen_initializer(supplied: FrozenSuppliedInput):
    if type(supplied) is not FrozenSuppliedInput:
        raise TypeError("supplied input has the wrong exact successor type")
    supplied.payload()
    bundle = cp62.cp62_execution_capsule_bundle()
    row = bundle.request_bindings[supplied.initializer_row_ordinal - 1]
    if (
        row.row_ordinal != FROZEN_INITIALIZER_ROW_ORDINAL
        or row.fixture_id != "T28-M1-Q"
        or row.strategy != "fixed-budget-sir"
        or row.budget != 8
        or bundle.formal_test_28_status != "OPEN"
        or bundle.formal_test_28_closed
    ):
        raise WholeMethodInitializerPathError("initializer predecessor differs")
    source = exact_tilt.build_t28_m1_q_exact_score_provider()
    provider = score_facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    plan = initializer.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=supplied.initializer_seed,
        budget=row.budget,
        ess_warning_fraction=0.25,
    )
    owner = initializer.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    owner.validate_result(result)
    if type(result) is not initializer.MixedSupportInitialTiltSIRResultV2:
        raise WholeMethodInitializerPathError("initializer result arm differs")
    if result.selected_configuration_sha256 != _configuration_sha256(
        result.selected_configuration
    ):
        raise WholeMethodInitializerPathError("selected configuration custody differs")
    return result


def _stable_initializer_execution_sha256(result, supplied) -> str:
    row = cp62.cp62_execution_capsule_bundle().request_bindings[
        supplied.initializer_row_ordinal - 1
    ]
    payload = {
        "particles": [
            {
                "configuration_sha256": particle.scored.configuration_sha256,
                "exact_log_weight": [
                    str(particle.scored.exact_log_weight.numerator),
                    str(particle.scored.exact_log_weight.denominator),
                ],
                "normalized_weight_hex": particle.normalized_weight.hex(),
                "ordinal": ordinal,
            }
            for ordinal, particle in enumerate(result.particles)
        ],
        "budget": row.budget,
        "effective_sample_size_hex": result.effective_sample_size.hex(),
        "ess_warning": result.ess_warning,
        "initializer_row_ordinal": row.row_ordinal,
        "initializer_seed": supplied.initializer_seed,
        "maximum_normalized_weight_hex": result.maximum_normalized_weight.hex(),
        "proposal_stream_final_state_sha256": result.proposal_stream_final_state_sha256,
        "proposal_stream_initial_state_sha256": result.proposal_stream_initial_state_sha256,
        "resampling_stream_final_state_sha256": result.resampling_stream_final_state_sha256,
        "resampling_stream_initial_state_sha256": result.resampling_stream_initial_state_sha256,
        "resampling_uniform_53": result.resampling_uniform_53,
        "resampling_word": result.resampling_word,
        "request_binding_sha256": row.record_sha256,
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "selected_index": result.selected_index,
        "status": result.status,
        "strategy": row.strategy,
    }
    return _domain_sha256(
        "heterodiff-b12-beta-stable-initializer-execution-v1", payload
    )


def _increment(serial: int, word: int, step_index: int, right: bool) -> float:
    low_word = word & 31
    if right:
        numerator = ((7 * serial + 3 * low_word + 5 * step_index) % 13) - 6
    else:
        numerator = ((5 * serial + 2 * low_word + 3 * step_index) % 11) - 5
    return float(numerator) / 64.0


def _heun_half(coordinate: float, increment: float, kind: str) -> float:
    design = test30.frozen_synthetic_design()
    target = design.long_run_mean_a if kind == "A" else design.long_run_mean_b
    value = test30._heun_half(
        coordinate,
        duration=0.5 * MACROSTEP_WIDTH,
        increment=increment,
        theta=design.mean_reversion,
        diffusion=design.diffusion,
        long_run_mean=target,
    )
    if not math.isfinite(value):
        raise WholeMethodInitializerPathError("integrated Heun value became non-finite")
    return value


def _evolve(
    occurrences: Tuple[IntegratedPathOccurrence, ...], increments: Mapping[int, float]
) -> Tuple[IntegratedPathOccurrence, ...]:
    if tuple(sorted(increments)) != tuple(item.serial for item in occurrences):
        raise WholeMethodInitializerPathError("addressed increment roster differs")
    return tuple(
        IntegratedPathOccurrence(
            serial=item.serial,
            kind=item.kind,
            coordinate=_heun_half(
                item.coordinate, increments[item.serial], item.kind
            ),
            role=item.role,
            source_event_ordinal=item.source_event_ordinal,
            source_event_sha256=item.source_event_sha256,
        )
        for item in occurrences
    )


def _zero_cardinality_birth_fixture():
    gaussian = test29.GaussianDestination((Fraction(1, 4),), (Fraction(1, 4),))
    root = test29.StateSpec(
        "beta-zero-root",
        1,
        0,
        (
            test29.RouteSpec(
                "beta-zero-birth",
                test29.FAMILY_BIRTH,
                "beta-zero-terminal",
                Fraction(1),
                Fraction(1),
                (),
                gaussian,
            ),
        ),
    )
    terminal = test29.StateSpec("beta-zero-terminal", 0, 1, ())
    return test29.FixtureSpec(
        "b12-beta-zero-cardinality-birth-v1",
        (root, terminal),
        root.state_id,
        test29.WordLayout(0, 0, 1, 1),
    )


def _fixture_for_cardinality(cardinality: int):
    if type(cardinality) is not int or not 0 <= cardinality <= 3:
        raise WholeMethodInitializerPathError("path cardinality leaves bounded fixture")
    return (
        _zero_cardinality_birth_fixture()
        if cardinality == 0
        else two.dynamic_central_jump_fixture(test29, cardinality)
    )


def _increment_rows(items: Tuple[object, ...]) -> list:
    return [
        {
            "domain": item.address.domain,
            "domain_tag": item.address.domain_tag,
            "increment_hex": item.increment.hex(),
            "occurrence_serial": item.address.occurrence_serial,
            "philox_counter": list(item.address.philox_counter),
            "philox_key": list(item.address.philox_key),
            "proposal_index": item.address.proposal_index,
            "run_id": item.address.run_id,
            "step_index": item.address.step_index,
        }
        for item in items
    ]


def _created_occurrence(fixture, selection, serial: int) -> IntegratedPathOccurrence:
    route = next(
        item for item in fixture.initial_state.routes if item.route_id == selection.route_id
    )
    if route.gaussian_destination is None or len(selection.normal_cells) != 1:
        raise WholeMethodInitializerPathError("destination-bearing route differs")
    cell = selection.normal_cells[0]
    coordinate = float(route.gaussian_destination.mean[0]) + math.sqrt(
        float(route.gaussian_destination.variance[0])
    ) * cell.midpoint_representative()
    return IntegratedPathOccurrence(
        serial=serial,
        kind="A" if selection.family == test29.FAMILY_BIRTH else "B",
        coordinate=coordinate,
        role="PATH_BIRTH",
        source_event_ordinal=None,
        source_event_sha256=None,
    )


def run_bounded_integrated_path(
    state: InitializerPathState,
    configuration: object,
    words: object = FROZEN_WORDS,
) -> Mapping[str, object]:
    """Run the qualification-only path from the exact transformed initializer state."""

    validate_initializer_path_state(state, configuration)
    if type(words) is not tuple or words != FROZEN_WORDS or any(
        type(word) is not int or not 0 <= word < 2**64 for word in words
    ):
        raise WholeMethodInitializerPathError("bounded path word roster differs")
    path_input = {
        "initial_state_sha256": state.initial_state_sha256,
        "path_policy_id": PATH_POLICY_ID,
        "selected_configuration_sha256": state.selected_configuration_sha256,
        "transform_sha256": state.transform_sha256,
        "words": list(words),
    }
    path_input_sha256 = _domain_sha256(
        "heterodiff-b12-beta-integrated-path-input-v1", path_input
    )
    current = state.occurrences
    lineage = test29.LineageState(
        tuple(item.serial for item in current),
        (),
        1 if not current else max(item.serial for item in current) + 1,
    )
    steps = []
    for step_index, word in enumerate(words):
        before_sha256 = _state_sha256(current)
        fixture = _fixture_for_cardinality(len(lineage.active_serials))
        central_word = test29.AddressedUint64Word(
            test29.CP24CompatibleAddress(RUN_ID, step_index, 0), word
        )
        central_word = single._validate_central_word(
            test29, central_word, run_id=RUN_ID, step_index=step_index
        )
        oracle_run = test29.run_addressed_acyclic_fixture(
            fixture, (central_word,), run_id=RUN_ID, step_index=step_index
        )
        test29.validate_addressed_acyclic_run_result(
            fixture, (central_word,), oracle_run
        )
        selection = test29.select_one_step(fixture, fixture.initial_state_id, word)
        if oracle_run.transitions[0].selection != selection:
            raise WholeMethodInitializerPathError("Test-29 route selection differs")
        lineage_after, source_serial, created_serial = test29._advance_lineage(
            lineage, selection
        )
        left_records = tuple(
            single._addressed_increment(
                test30,
                run_id=RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30.TAG_BROWNIAN_LEFT,
                increment=_increment(serial, word, step_index, False),
            )
            for serial in lineage.active_serials
        )
        left_values = single._validate_increment_roster(
            test30,
            left_records,
            expected_serials=lineage.active_serials,
            run_id=RUN_ID,
            step_index=step_index,
            tag=test30.TAG_BROWNIAN_LEFT,
            label="beta left",
        )
        after_left = _evolve(current, left_values)
        after_left_sha256 = _state_sha256(after_left)
        live = {item.serial: item for item in after_left}
        if source_serial is not None:
            if source_serial not in live:
                raise WholeMethodInitializerPathError("Test-29 source is not live")
            del live[source_serial]
        created = None
        if created_serial is not None:
            created = _created_occurrence(fixture, selection, created_serial)
            if created.serial in live:
                raise WholeMethodInitializerPathError("fresh serial collided")
            live[created.serial] = created
        if tuple(sorted(live)) != lineage_after.active_serials:
            raise WholeMethodInitializerPathError("coordinate and Test-29 lineage differ")
        after_jump = tuple(live[serial] for serial in sorted(live))
        after_jump_sha256 = _state_sha256(after_jump)
        right_records = tuple(
            single._addressed_increment(
                test30,
                run_id=RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30.TAG_BROWNIAN_RIGHT,
                increment=_increment(serial, word, step_index, True),
            )
            for serial in lineage_after.active_serials
        )
        right_values = single._validate_increment_roster(
            test30,
            right_records,
            expected_serials=lineage_after.active_serials,
            run_id=RUN_ID,
            step_index=step_index,
            tag=test30.TAG_BROWNIAN_RIGHT,
            label="beta right",
        )
        after_right = _evolve(after_jump, right_values)
        after_right_sha256 = _state_sha256(after_right)
        edit = {
            "created_occurrence": None if created is None else dict(created.payload()),
            "family": selection.family,
            "normal_cell_indices": [cell.index for cell in selection.normal_cells],
            "raw64_word": word,
            "route_id": selection.route_id,
            "source_index": selection.source_index,
            "source_serial": source_serial,
        }
        edit["edit_sha256"] = _domain_sha256(
            "heterodiff-b12-beta-central-edit-v1", edit
        )
        steps.append(
            {
                "active_serials_after": list(lineage_after.active_serials),
                "active_serials_before": list(lineage.active_serials),
                "addressed_central_word": {
                    "counter": list(central_word.address.counter),
                    "key": list(central_word.address.key),
                    "raw64_word": central_word.raw64_word,
                },
                "after_jump_sha256": after_jump_sha256,
                "after_left_sha256": after_left_sha256,
                "after_right_sha256": after_right_sha256,
                "before_sha256": before_sha256,
                "central_edit": edit,
                "left_addressed_increments": _increment_rows(left_records),
                "left_state": _state_payload(after_left),
                "retired_serials_after": list(lineage_after.retired_serials),
                "retired_serials_before": list(lineage.retired_serials),
                "right_addressed_increments": _increment_rows(right_records),
                "right_state": _state_payload(after_right),
                "step_index": step_index,
            }
        )
        current = after_right
        lineage = lineage_after
    if steps[0]["before_sha256"] != state.initial_state_sha256 or any(
        steps[index]["before_sha256"] != steps[index - 1]["after_right_sha256"]
        for index in range(1, len(steps))
    ):
        raise WholeMethodInitializerPathError("path state continuity differs")
    report = {
        "arbitrary_length_general_strang_path_integrated": False,
        "bounded_two_macrostep_path_integrated": True,
        "cp23_addressed_increments_validated": True,
        "cp24_addressed_words_validated": True,
        "final_state": _state_payload(current),
        "final_state_sha256": _state_sha256(current),
        "formal_test_28_closed": False,
        "formal_test_29_closed": False,
        "formal_test_30_closed": False,
        "formal_test28_production_law_admissible": False,
        "initializer_to_path_integrated": True,
        "initial_state_sha256": state.initial_state_sha256,
        "path_input_sha256": path_input_sha256,
        "path_policy_id": PATH_POLICY_ID,
        "selected_configuration_sha256": state.selected_configuration_sha256,
        "steps": steps,
        "test29_route_and_lineage_semantics_integrated": True,
        "test30_heun_primitive_integrated": True,
        "transform_sha256": state.transform_sha256,
        "test28_initializer_admissible": True,
        "upstream_runtime_executed": False,
    }
    report["path_report_sha256"] = _domain_sha256(
        "heterodiff-b12-beta-integrated-path-report-v1", report
    )
    return report


def _core(project_root: str) -> Mapping[str, object]:
    root = Path(project_root)
    if type(project_root) is not str or str(root) != project_root or root.resolve(strict=True) != root:
        raise WholeMethodInitializerPathError("project root must be canonical absolute text")
    supplied = build_frozen_supplied_input()
    predecessor_binding = _predecessor_binding(project_root)
    result = _execute_frozen_initializer(supplied)
    stable_initializer_sha256 = _stable_initializer_execution_sha256(
        result, supplied
    )
    state = transform_selected_configuration(
        result.selected_configuration, result.selected_configuration_sha256
    )
    path = run_bounded_integrated_path(state, result.selected_configuration)
    custody_payload = {
        "derived_initial_state_sha256": state.initial_state_sha256,
        "initializer_result_sha256": stable_initializer_sha256,
        "integrated_path_input_sha256": path["path_input_sha256"],
        "integrated_path_report_sha256": path["path_report_sha256"],
        "predecessor_receipt_sha256": predecessor_binding["receipt_sha256"],
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "supplied_input_sha256": supplied.input_sha256,
        "transform_policy_id": TRANSFORM_POLICY_ID,
        "transform_sha256": state.transform_sha256,
    }
    custody_sha256 = _domain_sha256(
        "heterodiff-b12-beta-end-to-end-custody-v1", custody_payload
    )
    return {
        "custody_chain": dict(custody_payload, custody_chain_sha256=custody_sha256),
        "effects": {
            "blocker_delta": 0,
            "data_accessed": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "result_delta": 0,
            "science_executed": False,
            "tracker_or_ledger_edited": False,
            "training_executed": False,
            "upstream_runtimes_executed": False,
        },
        "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
        "initializer": {
            "stable_execution_sha256": stable_initializer_sha256,
            "selected_configuration_sha256": result.selected_configuration_sha256,
            "selected_event_count": len(result.selected_configuration),
            "selected_index": result.selected_index,
            "strategy": "fixed-budget-sir",
        },
        "initializer_path_state": dict(state.payload(), transform_sha256=state.transform_sha256),
        "integrated_path": path,
        "nonclaims": {
            "arbitrary_length_general_path": False,
            "b12_closed": False,
            "confirmatory_evidence": False,
            "gate_b0_feature_complete": False,
            "production_receipt": False,
            "real_residual_receipts_present": 0,
            "upstream_external_runtime": False,
            "direct_public_api_custody_authenticated": False,
        },
        "qualification_boundary": {
            "authoritative_isolated_hash_first_validator_required": True,
            "direct_public_api_custody_authenticated": False,
        },
        "open_residual_predicate_ids": list(REAL_RESIDUAL_IDS),
        "predecessor": predecessor_binding,
        "proposed_timetable_task_closures": [PROPOSED_TASK],
        "schema_version": CORE_SCHEMA,
        "state": STATE,
    }


@dataclass(frozen=True)
class WholeMethodBetaSuccessorReceipt:
    schema_version: str
    state: str
    predecessor_receipt_sha256: str
    supplied_input_sha256: str
    stable_initializer_execution_sha256: str
    core_output_sha256: str
    independent_output_sha256: str
    independent_implementation_sha256: str
    selected_configuration_sha256: str
    transform_policy_id: str
    transform_sha256: str
    derived_initial_state_sha256: str
    integrated_path_input_sha256: str
    integrated_path_report_sha256: str
    custody_chain_sha256: str
    test28_initializer_admissible: bool
    initializer_to_path_integrated: bool
    open_residual_slot_count: int
    proposed_timetable_task: str
    direct_public_api_custody_authenticated: bool
    authoritative_qualification_requires_isolated_validator: bool
    receipt_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not WholeMethodBetaSuccessorReceipt:
            raise TypeError("receipt must have exact successor type")
        if self.schema_version != RECEIPT_SCHEMA or self.state != STATE:
            raise WholeMethodInitializerPathError("receipt schema or state differs")
        for name in (
            "predecessor_receipt_sha256",
            "supplied_input_sha256",
            "stable_initializer_execution_sha256",
            "core_output_sha256",
            "independent_output_sha256",
            "independent_implementation_sha256",
            "selected_configuration_sha256",
            "transform_sha256",
            "derived_initial_state_sha256",
            "integrated_path_input_sha256",
            "integrated_path_report_sha256",
            "custody_chain_sha256",
        ):
            _exact_sha256(getattr(self, name), name=name)
        if self.core_output_sha256 != self.independent_output_sha256:
            raise WholeMethodInitializerPathError("independent output differs")
        if self.transform_policy_id != TRANSFORM_POLICY_ID:
            raise WholeMethodInitializerPathError("receipt transform policy differs")
        if self.test28_initializer_admissible is not True:
            raise WholeMethodInitializerPathError("local initializer admissibility differs")
        if self.initializer_to_path_integrated is not True:
            raise WholeMethodInitializerPathError("initializer-path integration differs")
        if type(self.open_residual_slot_count) is not int or self.open_residual_slot_count != 50:
            raise WholeMethodInitializerPathError("open residual count differs")
        if self.proposed_timetable_task != PROPOSED_TASK:
            raise WholeMethodInitializerPathError("proposed task differs")
        if self.direct_public_api_custody_authenticated is not False:
            raise WholeMethodInitializerPathError("direct API custody nonclaim differs")
        if self.authoritative_qualification_requires_isolated_validator is not True:
            raise WholeMethodInitializerPathError("isolated-validator boundary differs")
        expected_custody = _domain_sha256(
            "heterodiff-b12-beta-end-to-end-custody-v1",
            {
                "derived_initial_state_sha256": self.derived_initial_state_sha256,
                "initializer_result_sha256": self.stable_initializer_execution_sha256,
                "integrated_path_input_sha256": self.integrated_path_input_sha256,
                "integrated_path_report_sha256": self.integrated_path_report_sha256,
                "predecessor_receipt_sha256": self.predecessor_receipt_sha256,
                "selected_configuration_sha256": self.selected_configuration_sha256,
                "supplied_input_sha256": self.supplied_input_sha256,
                "transform_policy_id": self.transform_policy_id,
                "transform_sha256": self.transform_sha256,
            },
        )
        if self.custody_chain_sha256 != expected_custody:
            raise WholeMethodInitializerPathError("receipt custody chain differs")
        payload = {
            name: getattr(self, name)
            for name in self.__annotations__
            if name != "receipt_sha256"
        }
        if self.receipt_sha256 != _domain_sha256(
            "heterodiff-b12-whole-method-beta-successor-receipt-v1", payload
        ):
            raise WholeMethodInitializerPathError("receipt digest differs")
        return payload


def validate_beta_successor_receipt(
    receipt: WholeMethodBetaSuccessorReceipt,
) -> WholeMethodBetaSuccessorReceipt:
    if type(receipt) is not WholeMethodBetaSuccessorReceipt:
        raise TypeError("receipt must have exact successor type")
    receipt.payload()
    return receipt


def receipt_canonical_json_bytes(receipt: WholeMethodBetaSuccessorReceipt) -> bytes:
    validate_beta_successor_receipt(receipt)
    value = dict(receipt.payload())
    value["receipt_sha256"] = receipt.receipt_sha256
    return _canonical(value) + b"\n"


def run_whole_method_beta_successor(project_root: str) -> WholeMethodBetaSuccessorReceipt:
    """Execute the repaired bounded beta and require separate byte parity."""

    core = _core(project_root)
    core_bytes = _canonical(core) + b"\n"
    core_sha256 = _sha256(core_bytes)
    independent_bytes, independent_sha256 = _captured_independent_recomputation(
        project_root
    )
    if type(independent_bytes) is not bytes or independent_bytes != core_bytes:
        raise WholeMethodInitializerPathError("independent recomputation differs")
    custody = core["custody_chain"]
    payload = {
        "core_output_sha256": core_sha256,
        "custody_chain_sha256": custody["custody_chain_sha256"],
        "derived_initial_state_sha256": custody["derived_initial_state_sha256"],
        "independent_implementation_sha256": independent_sha256,
        "independent_output_sha256": _sha256(independent_bytes),
        "integrated_path_input_sha256": custody["integrated_path_input_sha256"],
        "integrated_path_report_sha256": custody["integrated_path_report_sha256"],
        "initializer_to_path_integrated": core["integrated_path"][
            "initializer_to_path_integrated"
        ],
        "open_residual_slot_count": 50,
        "predecessor_receipt_sha256": custody["predecessor_receipt_sha256"],
        "proposed_timetable_task": PROPOSED_TASK,
        "schema_version": RECEIPT_SCHEMA,
        "selected_configuration_sha256": custody["selected_configuration_sha256"],
        "supplied_input_sha256": custody["supplied_input_sha256"],
        "stable_initializer_execution_sha256": custody[
            "initializer_result_sha256"
        ],
        "state": STATE,
        "test28_initializer_admissible": core["integrated_path"][
            "test28_initializer_admissible"
        ],
        "transform_policy_id": TRANSFORM_POLICY_ID,
        "transform_sha256": custody["transform_sha256"],
        "direct_public_api_custody_authenticated": core["qualification_boundary"][
            "direct_public_api_custody_authenticated"
        ],
        "authoritative_qualification_requires_isolated_validator": core[
            "qualification_boundary"
        ]["authoritative_isolated_hash_first_validator_required"],
    }
    receipt = WholeMethodBetaSuccessorReceipt(
        **payload,
        receipt_sha256=_domain_sha256(
            "heterodiff-b12-whole-method-beta-successor-receipt-v1", payload
        ),
    )
    return validate_beta_successor_receipt(receipt)


__all__ = [
    "CORE_SCHEMA",
    "DIRECT_PUBLIC_API_CUSTODY_AUTHENTICATED",
    "FROZEN_WORDS",
    "FROZEN_SUPPLIED_INPUT_SHA256",
    "FrozenSuppliedInput",
    "InitializerPathState",
    "IntegratedPathOccurrence",
    "PATH_POLICY_ID",
    "PROPOSED_TASK",
    "RECEIPT_SCHEMA",
    "SCHEMA_VERSION",
    "STATE",
    "AUTHORITATIVE_QUALIFICATION_REQUIRES_ISOLATED_VALIDATOR",
    "TRANSFORM_POLICY_ID",
    "WholeMethodBetaSuccessorReceipt",
    "WholeMethodInitializerPathError",
    "receipt_canonical_json_bytes",
    "build_frozen_supplied_input",
    "run_bounded_integrated_path",
    "run_whole_method_beta_successor",
    "transform_selected_configuration",
    "validate_beta_successor_receipt",
    "validate_initializer_path_state",
]
