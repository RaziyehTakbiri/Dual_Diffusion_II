#!/usr/bin/env python3
"""Hash-first validator for the B12 Gate-B0 integration candidate."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.json"
)
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.py"
)
PRIMARY_SOURCE_REL = "src/heterodiff/evaluation/b12_integration_stack.py"
INDEPENDENT_SOURCE_REL = (
    "src/heterodiff/evaluation/b12_independent_component_recomputation.py"
)
SCHEMA_VERSION = (
    "heterodiff-b12-gate-b0-integration-implementation-candidate-v1"
)
STATE = (
    "IMPLEMENTATION_SURFACES_COMPLETE_REGISTRATION_PENDING_INDEPENDENT_REVIEW"
)
TASK_TEXT = (
    "Runtime identity, runner, capsule, ledger, and recomputation implementations exist."
)
MAX_FILE_BYTES = 5_000_000
ZERO_SHA256 = "0" * 64

EXPECTED_STATIC_BINDINGS = (
    (
        "human",
        "PROJECT_B12_GATE_B0_INTEGRATION_IMPLEMENTATION_CANDIDATE.md",
        7383,
        "023cb2b9c54212af11eca1c218bd6f67ac49277897d03eeab41dd40802799a7c",
    ),
    (
        "primary_integration_source",
        PRIMARY_SOURCE_REL,
        87584,
        "61ccbc749d0922f2e0aadb63c800952f0b8c5575bd5d884e3e574833cada3b59",
    ),
    (
        "independent_recomputation_source",
        INDEPENDENT_SOURCE_REL,
        16684,
        "8b2b9de7c1d64f79cb5517894201f6410338fc9ba8323aca34f55a99fcbd1055",
    ),
    (
        "focused_integration_tests",
        "tests/unit/test_b12_integration_stack.py",
        34479,
        "417139b0fcda9ed280647f6bf7d39ff0eb34ac5fe3fed8660702ce1812c00bf5",
    ),
    (
        "package_tests",
        "tests/unit/test_manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.py",
        7972,
        "5e928cd5fca422db0643ea9aadf6a810ddbe242796a7280c2f450dc6e67a5453",
    ),
)

EXPECTED_PREDECESSOR_BINDINGS = (
    (
        "corrected_adapter_human",
        "PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK.md",
        8866,
        "900eb147602eb7d74e1a54e69d9d684cf8a1e8fc433c030cad4d50a2a2937b49",
    ),
    (
        "corrected_adapter_source",
        "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
        34660,
        "44ece6452c8edfaadc7d6013a37208fb8648d3a6dbb3ce29bcecd97a90880a57",
    ),
    (
        "corrected_adapter_machine",
        "research/fixtures/manuscript_v3_b12_two_domain_adapter_stack_v1.json",
        9956,
        "ba65fe357caca90f64e89bac9d9c78fbbe379342fcf7f6321aceb4caf4f7b502",
    ),
    (
        "corrected_adapter_independent_review",
        "PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK_INDEPENDENT_REVIEW.md",
        8571,
        "3441c64ede3298ce5f0f0c58747e96c4818179b46abfa4c0d13753a5f66510e3",
    ),
    (
        "accepted_b12_v2_source",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
        14944,
        "b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd",
    ),
    (
        "accepted_b12_v2_machine",
        "research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json",
        8755,
        "825cfde8412474eba97dea4a4d2fb92fa8af99568ebeada05f6b33b71fcc680c",
    ),
    (
        "accepted_b12_v2_final_review",
        "PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE_INDEPENDENT_REVIEW.md",
        4988,
        "90e7d4f9f4f70bcd4a6da599c532a944629101d3d5b245f7b05ece01cb463a46",
    ),
    (
        "f105_exact_instance_source",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
        25342,
        "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881",
    ),
    (
        "b06_registry_source",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        47098,
        "d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1",
    ),
    (
        "matched_compute_source",
        "src/heterodiff/experiments/matched_total_compute.py",
        15028,
        "be31b346c67b7d0ce0b82a3ff784739bf3d825fd9b94108dc1f8ae808586f8a0",
    ),
    (
        "formal_test29_component_source",
        "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
        52186,
        "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089",
    ),
    (
        "formal_test30_component_source",
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
        42349,
        "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0",
    ),
    (
        "single_macrostep_component_source",
        "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
        61434,
        "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7",
    ),
    (
        "two_macrostep_component_source",
        "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
        59285,
        "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176",
    ),
)


class ValidationError(RuntimeError):
    """Raised when any exact-byte or semantic validation fails."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _domain_sha256(domain: str, value: Any) -> str:
    return hashlib.sha256(
        domain.encode("ascii") + b"\0" + _canonical_bytes(value)
    ).hexdigest()


def _identity(metadata: os.stat_result) -> Tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _canonical_relative(value: str) -> PurePosixPath:
    if type(value) is not str or not value or not value.isascii() or "\\" in value:
        raise ValidationError("path must be exact nonempty ASCII POSIX text")
    relative = PurePosixPath(value)
    if (
        relative.as_posix() != value
        or relative.is_absolute()
        or any(part in ("", ".", "..") for part in relative.parts)
    ):
        raise ValidationError("path is noncanonical or escapes the project root")
    return relative


def _read_stable_regular(relative_path: str) -> bytes:
    relative = _canonical_relative(relative_path)
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(str(ROOT), root_flags)
    opened = []
    try:
        before_root = os.fstat(root_fd)
        current = root_fd
        for part in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf = os.open(relative.name, flags, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or not 1 <= before.st_size <= MAX_FILE_BYTES
        ):
            raise ValidationError("file custody or size differs: " + relative_path)
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(leaf)
        after_root = os.fstat(root_fd)
        if (
            len(raw) != before.st_size
            or _identity(before) != _identity(after)
            or _identity(before_root) != _identity(after_root)
        ):
            raise ValidationError("file or project root changed during read")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _binding(role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "bytes": len(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "path": path,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "role": role,
        "terminal_lf": raw.endswith(b"\n"),
    }


def _verify_fixed_bindings(
    expected: Iterable[Tuple[str, str, int, str]]
) -> Tuple[Dict[str, Any], ...]:
    bindings = []
    for role, path, byte_count, raw_sha256 in expected:
        raw = _read_stable_regular(path)
        if len(raw) != byte_count or hashlib.sha256(raw).hexdigest() != raw_sha256:
            raise ValidationError("fixed binding differs: " + path)
        if not raw.endswith(b"\n"):
            raise ValidationError("fixed binding lacks terminal LF: " + path)
        bindings.append(_binding(role, path, raw))
    return tuple(bindings)


def _strict_json(value: object, name: str) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _strict_json(item, "%s[%d]" % (name, index))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError(name + " has a non-text key")
            _strict_json(item, name + "." + key)
        return
    raise ValidationError(name + " has a non-exact JSON type")


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    if type(pairs) is not list:
        raise ValidationError("JSON pairs must be an exact list")
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValidationError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _load_machine_record(raw: bytes) -> Dict[str, Any]:
    if type(raw) is not bytes or not raw.endswith(b"\n") or raw[:-1].endswith(b"\n"):
        raise ValidationError("machine record must have exactly one terminal LF")
    try:
        machine = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is invalid canonical JSON") from error
    if type(machine) is not dict:
        raise ValidationError("machine record root must be an exact object")
    _strict_json(machine, "machine")
    if _canonical_bytes(machine) + b"\n" != raw:
        raise ValidationError("machine record bytes are not canonical")
    return machine


_CAPTURED_MODULE_SPECS = (
    (
        "heterodiff.evaluation.b12_integrated_offline_candidate",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
    ),
    (
        "heterodiff.evaluation.two_domain_count_normalized_event_cks",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
    ),
    (
        "heterodiff.experiments.matched_total_compute",
        "src/heterodiff/experiments/matched_total_compute.py",
    ),
    (
        "heterodiff.experiments.two_domain_baseline_registry",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
    ),
    (
        "heterodiff.evaluation.b12_two_domain_adapter_stack",
        "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
    ),
    (
        "heterodiff.processes.formal_test29_finite_acyclic_route_oracle",
        "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
    ),
    (
        "heterodiff.evaluation.formal_test30_synthetic_coupled_path_qualification",
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
    ),
    (
        "heterodiff.evaluation.formal_test29_test30_single_macrostep_integration",
        "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
    ),
    (
        "heterodiff.evaluation.formal_test29_test30_two_macrostep_path_qualification",
        "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
    ),
    (
        "heterodiff.evaluation.b12_independent_component_recomputation",
        INDEPENDENT_SOURCE_REL,
    ),
    (
        "heterodiff.evaluation.b12_integration_stack",
        PRIMARY_SOURCE_REL,
    ),
)


@contextmanager
def _captured_module_graph():
    """Execute every project dependency from captured bytes, ignoring caches."""

    package_specs = (
        ("heterodiff", ROOT / "src/heterodiff"),
        ("heterodiff.evaluation", ROOT / "src/heterodiff/evaluation"),
        ("heterodiff.experiments", ROOT / "src/heterodiff/experiments"),
        ("heterodiff.processes", ROOT / "src/heterodiff/processes"),
    )
    controlled_names = tuple(name for name, _ in package_specs) + tuple(
        name for name, _ in _CAPTURED_MODULE_SPECS
    )
    missing = object()
    saved = {name: sys.modules.get(name, missing) for name in controlled_names}
    exact_by_path = {
        path: (byte_count, raw_sha256)
        for _, path, byte_count, raw_sha256 in (
            EXPECTED_STATIC_BINDINGS + EXPECTED_PREDECESSOR_BINDINGS
        )
    }
    modules: Dict[str, ModuleType] = {}
    try:
        for name, directory in package_specs:
            package = ModuleType(name)
            package.__file__ = str(directory / "__init__.py")
            package.__package__ = name
            package.__path__ = [str(directory)]
            sys.modules[name] = package
            modules[name] = package
            if "." in name:
                parent_name, attribute = name.rsplit(".", 1)
                setattr(modules[parent_name], attribute, package)
        for name, relative_path in _CAPTURED_MODULE_SPECS:
            raw = _read_stable_regular(relative_path)
            expected = exact_by_path.get(relative_path)
            if expected is None or expected != (
                len(raw),
                hashlib.sha256(raw).hexdigest(),
            ):
                raise ValidationError(
                    "captured module bytes differ from fixed binding: "
                    + relative_path
                )
            path = ROOT.joinpath(*_canonical_relative(relative_path).parts)
            module = ModuleType(name)
            module.__file__ = str(path)
            module.__package__ = name.rpartition(".")[0]
            sys.modules[name] = module
            modules[name] = module
            parent_name, attribute = name.rsplit(".", 1)
            setattr(modules[parent_name], attribute, module)
            code = compile(raw, str(path), "exec", dont_inherit=True)
            exec(code, module.__dict__)
        yield modules
    finally:
        for name in reversed(controlled_names):
            previous = saved[name]
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def _build_ledger_pair(module: ModuleType) -> Tuple[object, object]:
    request = b"B12-GATE-B0-DETERMINISTIC-COMPONENT-REQUEST-V1"
    outcome = b"B12-GATE-B0-DETERMINISTIC-COMPONENT-OUTCOME-V1"
    request_sha256 = module._raw_domain_sha256(
        "heterodiff-b12-operation-request-v1", request
    )
    intent = module._build_ledger_event(
        ordinal=0,
        event_kind="INTENT",
        operation_id="B12-GATE-B0-COMPONENT-EXERCISE",
        request_sha256=request_sha256,
        observation_sha256=None,
        previous_event_sha256=module.ZERO_SHA256,
    )
    result = module._build_ledger_event(
        ordinal=1,
        event_kind="OUTCOME",
        operation_id="B12-GATE-B0-COMPONENT-EXERCISE",
        request_sha256=request_sha256,
        observation_sha256=module._raw_domain_sha256(
            "heterodiff-b12-operation-outcome-v1", outcome
        ),
        previous_event_sha256=intent.event_sha256,
    )
    return intent, result


def _runtime_mapping(module: ModuleType) -> Dict[str, Any]:
    payload = {
        "capacity_receipt_sha256": hashlib.sha256(b"candidate-capacity").hexdigest(),
        "deterministic_settings_sha256": hashlib.sha256(b"candidate-settings").hexdigest(),
        "generation": 1,
        "hardware_receipt_sha256": hashlib.sha256(b"candidate-hardware").hexdigest(),
        "lockfile_sha256": hashlib.sha256(b"candidate-lockfile").hexdigest(),
        "predecessor_binding_sha256": module.ZERO_SHA256,
        "runtime_identity_id": "CALLER-SUPPLIED-RUNTIME-IDENTITY-STRUCTURAL-FIXTURE",
        "schema_version": module.RUNTIME_IDENTITY_SCHEMA,
        "software_environment_sha256": hashlib.sha256(b"candidate-environment").hexdigest(),
    }
    result = dict(payload)
    result["binding_sha256"] = module._domain_sha256(
        "heterodiff-b12-runtime-identity-binding-v1", payload
    )
    return dict(sorted(result.items()))


def _auth(module: ModuleType, label: str) -> object:
    return module.ReceiptAuthentication(
        reviewer_principal_id="LOCAL-SYNTHETIC-" + label,
        authentication_method_id="DETERMINISTIC-OFFLINE-QUALIFICATION-V1",
        authentication_evidence_sha256=hashlib.sha256(
            ("b12-gate-b0-validator:" + label).encode("ascii")
        ).hexdigest(),
    )


def _marker_hostility(module: ModuleType, runner_parts: Tuple[object, ...]) -> bool:
    capsule, adapters, ledger, recomputation, runtime = runner_parts
    hostile = (
        ("LOCALAUTH", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNALLOCALAUTH", "EXTERNAL-SIGNATURE-V1"),
        ("SYNTHETICREVIEWER", "EXTERNAL-SIGNATURE-V1"),
        ("trustedSYNTHETICreviewer", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNAL-REVIEWER", "OFFLINEAUTH"),
        ("EXTERNAL-REVIEWER", "EXTERNALOFFLINEAUTH"),
        ("testprincipal", "EXTERNAL-SIGNATURE-V1"),
        ("EXTERNALtestprincipal", "EXTERNAL-SIGNATURE-V1"),
    )
    for index, (principal, method) in enumerate(hostile):
        authentication = module.ReceiptAuthentication(
            reviewer_principal_id=principal,
            authentication_method_id=method,
            authentication_evidence_sha256=hashlib.sha256(
                ("validator-hostile-%d" % index).encode("ascii")
            ).hexdigest(),
        )
        receipt = module.build_authenticated_predicate(
            "SYNTHETIC_INTERFACE_EXERCISE:VALIDATOR-HOSTILE-%d" % index,
            "3" * 64,
            authentication,
        )
        try:
            module.build_integrated_runner_receipt(
                capsule,
                adapters,
                ledger,
                recomputation,
                (receipt,),
                runtime,
            )
        except module.B12IntegrationError as error:
            if "local or synthetic" not in str(error):
                return False
        else:
            return False
    return True


def derive_semantics() -> Dict[str, Any]:
    with _captured_module_graph() as modules:
        return _derive_semantics_from_captured_modules(modules)


def _derive_semantics_from_captured_modules(
    modules: Mapping[str, ModuleType],
) -> Dict[str, Any]:
    module = modules["heterodiff.evaluation.b12_integration_stack"]
    independent = modules[
        "heterodiff.evaluation.b12_independent_component_recomputation"
    ]
    v2 = modules["heterodiff.evaluation.b12_integrated_offline_candidate"]
    adapter_api = modules["heterodiff.evaluation.b12_two_domain_adapter_stack"]

    bindings = module.build_component_bindings(str(ROOT))
    outputs = module.run_and_independently_recompute(str(ROOT), bindings)
    capsule_plan = module.build_closed_world_capsule_plan(
        str(ROOT),
        "B12-GATE-B0-COMPONENT-EVIDENCE-CAPSULE-V1",
        module.DEFAULT_CAPSULE_SOURCE_PATHS,
        bindings,
        _auth(module, "CAPSULE"),
    )
    adapters = module.build_synthetic_adapter_manifest_binding(str(ROOT))
    ledger = _build_ledger_pair(module)
    v2.validate_ledger(ledger)
    execution_subject = module.compute_execution_subject_v3(
        capsule_plan.receipt, adapters, ledger, None
    )
    recomputation = module.build_recomputation_receipt(
        execution_subject, outputs, _auth(module, "RECOMPUTATION")
    )
    runner = module.build_open_integrated_runner_exercise(
        capsule_plan.receipt, adapters, ledger, recomputation
    )
    runner_status = runner.status()
    runtime = module.RuntimeIdentityBinding.from_mapping(_runtime_mapping(module))
    runtime.validate_fresh(1, module.ZERO_SHA256)

    runner_subject = module.compute_runner_subject_v3(
        capsule_plan.receipt, adapters, ledger, recomputation, None
    )
    locally_minted = True
    try:
        module.build_authenticated_predicate(
            module.residual_predicate_ids()[0],
            runner_subject,
            _auth(module, "FORBIDDEN-REAL-RESIDUAL"),
        )
    except module.B12IntegrationError:
        locally_minted = False

    path_results: Dict[str, bool] = {}
    relative_aliases = {
        "relative_double_separator_rejected": "src//heterodiff/evaluation/b12_integration_stack.py",
        "relative_dot_segment_rejected": "src/./heterodiff/evaluation/b12_integration_stack.py",
        "relative_trailing_separator_rejected": "src/heterodiff/evaluation/b12_integration_stack.py/",
    }
    for key, alias in relative_aliases.items():
        try:
            module._safe_relative_path(alias)
        except module.B12IntegrationError:
            path_results[key] = True
        else:
            path_results[key] = False
    absolute_aliases = {
        "absolute_root_trailing_separator_rejected": str(ROOT) + "/",
        "absolute_root_double_separator_rejected": str(ROOT.parent) + "//" + ROOT.name,
    }
    for key, alias in absolute_aliases.items():
        try:
            module._canonical_root(alias)
        except module.B12IntegrationError:
            path_results[key] = True
        else:
            path_results[key] = False

    effects = {
        "authority_created": False,
        "blocker_delta": 0,
        "contact_performed": False,
        "data_accessed": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "result_delta": 0,
        "runtime_identity_selected": False,
        "science_executed": False,
        "timetable_task_delta_applied": 0,
        "tracker_or_evidence_ledger_edited": False,
    }
    registration = {
        "applied_timetable_task_delta": 0,
        "independent_review_required_before_registration": True,
        "proposed_timetable_task_closure_count": 1,
        "proposed_timetable_task_closures": [TASK_TEXT],
    }
    manifest = json.loads(capsule_plan.manifest_bytes[:-1].decode("ascii"))
    return {
        "accepted_boundaries": {
            "accepted_b12_v2_review_sha256": (
                "90e7d4f9f4f70bcd4a6da599c532a944629101d3d5b245f7b05ece01cb463a46"
            ),
            "corrected_adapter_review_sha256": (
                "3441c64ede3298ce5f0f0c58747e96c4818179b46abfa4c0d13753a5f66510e3"
            ),
            "corrected_adapter_source_sha256": hashlib.sha256(
                _read_stable_regular(
                    "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py"
                )
            ).hexdigest(),
        },
        "canonical_path_hostility": dict(sorted(path_results.items())),
        "capsule_exercise": {
            "accepted_receipt_payload_digest_count": len(
                capsule_plan.receipt.ordered_file_sha256s
            ),
            "binding_payload_is_manifest_bound": (
                manifest["component_binding_payload"]["raw_sha256"]
                == capsule_plan.component_binding_document_sha256
            ),
            "binding_payload_is_physically_planned": (
                type(capsule_plan.component_binding_document_bytes) is bytes
                and capsule_plan.component_binding_document_bytes.endswith(b"\n")
            ),
            "binding_payload_is_receipt_bound": (
                capsule_plan.receipt.ordered_file_sha256s[-1]
                == capsule_plan.component_binding_document_sha256
            ),
            "component_binding_payload_name": module.COMPONENT_BINDING_PAYLOAD_NAME,
            "component_source_payload_count": len(capsule_plan.files),
            "manifest_raw_sha256": capsule_plan.manifest_raw_sha256,
            "scope": module.CAPSULE_SCOPE,
            "standalone_executable_claimed": False,
            "transitive_dependency_closure_claimed": False,
        },
        "effects": effects,
        "implementation_surfaces": {
            "capsule": "IMPLEMENTED_AND_FOCUSED_TESTED",
            "durable_paired_ledger": "IMPLEMENTED_AND_FOCUSED_TESTED",
            "independent_recomputation": (
                "IMPLEMENTED_AS_SEPARATE_MODULE_AND_FOCUSED_TESTED"
            ),
            "runner": "IMPLEMENTED_AND_FOCUSED_TESTED",
            "runtime_identity_binding": (
                "IMPLEMENTED_FUTURE_CALLER_SUPPLIED_SEAM_AND_FOCUSED_TESTED"
            ),
        },
        "ledger_exercise": {
            "complete_pairs": True,
            "event_count": len(ledger),
            "event_kinds": [event.event_kind for event in ledger],
            "final_event_sha256": ledger[-1].event_sha256,
            "operation_ids_match": ledger[0].operation_id == ledger[1].operation_id,
            "request_sha256s_match": ledger[0].request_sha256 == ledger[1].request_sha256,
        },
        "recomputation_exercise": {
            "binding_document_sha256": hashlib.sha256(
                outputs.binding_document_bytes
            ).hexdigest(),
            "candidate_and_independent_bytes_equal": (
                outputs.candidate_output_bytes == outputs.independent_output_bytes
            ),
            "candidate_output_sha256": outputs.candidate_output_sha256,
            "independent_implementation_sha256": (
                outputs.independent_implementation_sha256
            ),
            "independent_module_imports_primary_integration_module": (
                "b12_integration_stack" in independent.__dict__
            ),
            "independent_output_sha256": outputs.independent_output_sha256,
        },
        "registration_proposal": registration,
        "runner_exercise": {
            "b12_closed": runner_status["b12_closed"],
            "corrected_adapter_count": len(adapters.receipts),
            "embedded_nonproduction_authentication_rejected": _marker_hostility(
                module,
                (
                    capsule_plan.receipt,
                    adapters,
                    ledger,
                    recomputation,
                    runtime,
                ),
            ),
            "every_slot_subject_bound": all(
                slot.expected_subject_sha256 == runner_subject
                for slot in runner.predicate_slots
            ),
            "formal_test_states": runner_status["formal_test_states"],
            "legacy_adapter_mismatch_ordinals": list(
                adapter_api.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS
            ),
            "real_residual_accept_receipts_locally_minted": locally_minted,
            "residual_receipts_missing": runner_status["residual_receipts_missing"],
            "residual_receipts_present": runner_status["residual_receipts_present"],
            "residual_slot_count": len(runner.predicate_slots),
            "runtime_identity_present": runner_status["runtime_identity_present"],
            "science_executed": runner_status["science_executed"],
            "state": runner.state,
        },
        "runtime_identity_seam": {
            "actual_runtime_selected": False,
            "binding_sha256": runtime.binding_sha256,
            "exact_field_count": len(_runtime_mapping(module)),
            "future_caller_supplied_only": True,
            "generation": runtime.generation,
            "predecessor_sha256": runtime.predecessor_binding_sha256,
        },
        "schema_version": SCHEMA_VERSION,
        "state": STATE,
    }


def build_machine_candidate() -> Dict[str, Any]:
    static_bindings = list(_verify_fixed_bindings(EXPECTED_STATIC_BINDINGS))
    validator_raw = _read_stable_regular(VALIDATOR_REL)
    bindings = static_bindings + [_binding("validator", VALIDATOR_REL, validator_raw)]
    predecessor_bindings = list(
        _verify_fixed_bindings(EXPECTED_PREDECESSOR_BINDINGS)
    )
    semantics = derive_semantics()
    unsigned = {
        "bindings": bindings,
        "effects": semantics["effects"],
        "predecessor_bindings": predecessor_bindings,
        "registration_proposal": semantics["registration_proposal"],
        "schema_version": SCHEMA_VERSION,
        "semantics": semantics,
        "state": STATE,
    }
    result = dict(unsigned)
    result["record_sha256"] = _domain_sha256(SCHEMA_VERSION, unsigned)
    return dict(sorted(result.items()))


def validate() -> Dict[str, Any]:
    machine = _load_machine_record(_read_stable_regular(MACHINE_REL))
    expected = build_machine_candidate()
    if machine != expected:
        raise ValidationError("machine record differs from exact reconstructed candidate")
    if tuple(machine) != (
        "bindings",
        "effects",
        "predecessor_bindings",
        "record_sha256",
        "registration_proposal",
        "schema_version",
        "semantics",
        "state",
    ):
        raise ValidationError("machine top-level roster or order differs")
    proposal = machine["registration_proposal"]
    if proposal["proposed_timetable_task_closures"] != [TASK_TEXT]:
        raise ValidationError("registration proposal differs")
    if any(
        machine["effects"][key] not in (0, False)
        for key in machine["effects"]
    ):
        raise ValidationError("a prohibited applied effect is nonzero")
    if machine["semantics"]["runner_exercise"]["residual_receipts_present"] != 0:
        raise ValidationError("real residual receipts are not all OPEN")
    return {
        "decision": "PASS_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
        "proposed_timetable_task": TASK_TEXT,
        "proposed_timetable_task_closure_count": 1,
        "record_sha256": machine["record_sha256"],
    }


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--emit-candidate":
        print(_canonical_bytes(build_machine_candidate()).decode("ascii"))
        return 0
    if len(sys.argv) != 1:
        print("FAIL — unsupported arguments", file=sys.stderr)
        return 2
    try:
        result = validate()
    except Exception as error:
        print("FAIL — " + str(error), file=sys.stderr)
        return 1
    print(
        "PASS — exact five Gate-B0 implementation surfaces; sole candidate task; "
        "record " + result["record_sha256"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
