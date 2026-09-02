from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict, Mapping, Sequence, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT / "research/diagnostics/finite_association_r1_registry_aware_capsule_v1.py"
)
HUMAN_PATH = (
    ROOT / "manuscript_v3/a1_r1_registry_aware_source_execution_capsule_freeze_v1.md"
)
MACHINE_PATH = (
    ROOT / "research/fixtures/"
    "manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.json"
)
TEST_PATH = Path(__file__).resolve()
REGISTRATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-r1-registry-aware-overlay-source-registration-v1\0"
)
SOURCE_DOMAIN = (
    b"heterodiff-r1-registry-aware-preactivation-overlay-source-manifest-v1\0"
)
COORDINATE_DOMAIN = b"heterodiff-r1-registry-aware-coordinate-manifest-v1\0"
PHASE_EVENT_DOMAIN = b"heterodiff-r1-registry-aware-phase-event-schedule-v1\0"
REGISTRY_DOMAIN = b"heterodiff-r1-registry-aware-seed-registry-v1\0"
REGISTRY = [4052249444591756, 3253, 5003, 7411, 10007, 13007, 16001, 20011]
MILESTONE_STATE = (
    "R1_A1_REGISTRY_AWARE_OVERLAY_SOURCE_AND_COORDINATE_FREEZE_ZERO_EXECUTION_"
    "RUNTIME_ADAPTER_AND_BINDER_DEFERRED_NOT_EXECUTABLE"
)


def _load_module() -> Any:
    name = "_registry_aware_capsule_freeze_v1_test"
    specification = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


CAPSULE = _load_module()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    return payload, value


def _semantic_digest(record: Mapping[str, Any]) -> str:
    body = dict(record)
    body["record_sha256"] = None
    return _sha256(REGISTRATION_DOMAIN + _canonical_json(body))


def _rehash(record: Mapping[str, Any]) -> Dict[str, Any]:
    value = json.loads(_canonical_json(record).decode("ascii"))
    value["record_sha256"] = None
    value["record_sha256"] = _semantic_digest(value)
    return value


def _write_canonical(path: Path, record: Mapping[str, Any]) -> None:
    path.write_bytes(_canonical_json(record) + b"\n")


def _manifest_body(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "manifest_sha256"}


def _record_body(record: Mapping[str, Any], digest_key: str) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != digest_key}


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _module_name(relative_path: str) -> str:
    value = relative_path[4:-3].replace("/", ".")
    return value[: -len(".__init__")] if value.endswith(".__init__") else value


def _candidate_paths(module_name: str) -> Tuple[str, str]:
    stem = "src/" + module_name.replace(".", "/")
    return stem + ".py", stem + "/__init__.py"


def _ancestor_initializers(relative_path: str) -> Tuple[str, ...]:
    parts = relative_path.split("/")
    return tuple(
        "/".join(parts[: index + 1]) + "/__init__.py"
        for index in range(1, len(parts) - 1)
    )


def _independent_import_edges(paths: Sequence[str]) -> Tuple[Tuple[str, str], ...]:
    allowed = {_module_name(path): path for path in paths}
    required = set(CAPSULE.IMPORT_CLOSURE_ROOTS)
    for path in tuple(required):
        required.update(_ancestor_initializers(path))
    edges = set()
    pending = sorted(required)
    while pending:
        importer = pending.pop(0)
        tree = ast.parse((ROOT / importer).read_bytes(), filename=importer)
        importer_module = _module_name(importer)
        package = importer_module.split(".")
        if not importer.endswith("/__init__.py"):
            package = package[:-1]
        found = set()

        def register(module_name: str) -> None:
            if not module_name.startswith("heterodiff"):
                return
            assert module_name in allowed
            found.add(allowed[module_name])

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("heterodiff"):
                        register(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package[: len(package) - node.level + 1]
                    if node.module:
                        base.extend(node.module.split("."))
                    module_name = ".".join(base)
                else:
                    module_name = node.module or ""
                if not module_name.startswith("heterodiff"):
                    continue
                register(module_name)
                for alias in node.names:
                    child = module_name + "." + alias.name
                    if alias.name != "*" and child in allowed:
                        register(child)
        for imported in found:
            edges.add((importer, imported))
            for addition in (imported, *_ancestor_initializers(imported)):
                if addition not in required:
                    required.add(addition)
                    pending.append(addition)
        pending.sort()
    assert required == set(paths)
    return tuple(sorted(edges))


def _expected_binding_rows() -> Sequence[Dict[str, Any]]:
    rows = []
    for ordinal, (role, path) in enumerate(
        (
            ("HUMAN_REGISTRATION", HUMAN_PATH),
            ("STATIC_AUDIT_MODULE", MODULE_PATH),
            ("HOSTILE_TEST", TEST_PATH),
        )
    ):
        payload = path.read_bytes()
        rows.append(
            {
                "ordinal": ordinal,
                "role": role,
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(payload),
                "raw_sha256": _sha256(payload),
                "lf_only": b"\r" not in payload,
                "is_regular_file": True,
                "is_symlink": False,
            }
        )
    return rows


def test_static_audit_ast_is_stdlib_read_only_and_has_no_duplicate_keys() -> None:
    tree = ast.parse(MODULE_PATH.read_bytes(), filename=str(MODULE_PATH))
    allowed_import_roots = {
        "__future__",
        "ast",
        "dataclasses",
        "hashlib",
        "json",
        "pathlib",
        "stat",
        "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {
                alias.name.split(".")[0] for alias in node.names
            } <= allowed_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed_import_roots
        elif isinstance(node, ast.Dict):
            keys = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            ]
            assert len(keys) == len(set(keys))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "exec",
                    "eval",
                    "compile",
                    "__import__",
                    "open",
                }
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "write_bytes",
                    "write_text",
                    "mkdir",
                    "unlink",
                    "rename",
                    "rglob",
                    "glob",
                    "Popen",
                    "run",
                    "token_bytes",
                }
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("numpy", "torch", "subprocess", "socket", "requests", "urllib"):
        assert f"import {forbidden}" not in source
        assert f"from {forbidden}" not in source
    assert "_from_verified_sidecar" not in MODULE_PATH.read_text(encoding="utf-8")


def test_full_static_source_manifest_and_exact_base_identities() -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    manifest = audit["source_manifest"]
    assert manifest["closure_kind"] == "PREACTIVATION_MODULE_LOAD_STATIC_CLOSURE"
    assert manifest["row_count"] == 45
    assert manifest["base_path_count"] == 45
    assert manifest["overlay_row_count"] == 5
    assert manifest["virtual_adapter_row_present"] is False
    assert manifest["production_execution_import_closure_complete"] is False
    assert manifest["manifest_sha256"] == _sha256(
        SOURCE_DOMAIN + _canonical_json(_manifest_body(manifest))
    )
    assert tuple(row["path"] for row in manifest["rows"]) == CAPSULE.BASE_SOURCE_PATHS
    expectations = {
        path: (size, digest) for path, size, digest in CAPSULE.BASE_SOURCE_EXPECTATIONS
    }
    for row in manifest["rows"]:
        payload = (ROOT / row["path"]).read_bytes()
        assert expectations[row["path"]] == (len(payload), _sha256(payload))
        assert row["base_raw_sha256"] == _sha256(payload)
        assert row["execution_admissible"] is False
    assert len(manifest["nonpackage_candidate_inputs"]) == 3
    deferred = manifest["deferred_runtime_boundary"]
    assert deferred["deferred_source_count"] == 2
    approval = (
        "src/heterodiff/experiments/finite_association_runtime_identity_approval.py"
    )
    capture = (
        "src/heterodiff/experiments/finite_association_runtime_identity_capture.py"
    )
    identity = "src/heterodiff/experiments/finite_association_runtime_identity.py"
    assert deferred["known_local_chain_count"] == 6
    assert deferred["known_local_chain"] == [
        {
            "from_path": identity,
            "mechanism": "importlib.import_module_LITERAL",
            "to_path": approval,
        },
        {
            "from_path": approval,
            "mechanism": "NORMAL_IMPORT_FROM",
            "to_path": identity,
        },
        {
            "from_path": approval,
            "mechanism": "FUNCTION_LOCAL_IMPORT_FROM",
            "to_path": capture,
        },
        {
            "from_path": approval,
            "mechanism": "FUNCTION_LOCAL_CANONICAL_SELF_IMPORT",
            "to_path": approval,
        },
        {
            "from_path": capture,
            "mechanism": "NORMAL_IMPORT_FROM",
            "to_path": identity,
        },
        {
            "from_path": capture,
            "mechanism": "NORMAL_IMPORT_FROM",
            "to_path": approval,
        },
    ]
    assert deferred["dynamic_runtime_closure_complete"] is False
    assert deferred["production_execution_import_closure_complete"] is False


def test_all_initializers_are_parsed_and_initializer_only_imports_are_closed(
    tmp_path: Path,
) -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    observed = tuple(
        (row["importer_path"], row["imported_path"])
        for row in audit["source_manifest"]["static_import_edges"]
    )
    independent = _independent_import_edges(CAPSULE.BASE_SOURCE_PATHS)
    assert observed == independent
    assert len(observed) == 102
    assert (
        "src/heterodiff/models/__init__.py",
        "src/heterodiff/models/reference_config.py",
    ) in observed
    assert (
        "src/heterodiff/evaluation/__init__.py",
        "src/heterodiff/evaluation/metric_floor.py",
    ) in observed

    synthetic = ast.parse("from . import initializer_only_dependency\n")
    child = tmp_path / "src/heterodiff/models/initializer_only_dependency.py"
    child.parent.mkdir(parents=True)
    child.write_text("VALUE = 1\n", encoding="ascii")
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE._resolved_local_imports(
            tmp_path,
            "src/heterodiff/models/__init__.py",
            synthetic,
            {_module_name(path): path for path in CAPSULE.BASE_SOURCE_PATHS},
        )


def test_registry_record_and_all_overlay_assignments_are_semantically_equal() -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    manifest = audit["source_manifest"]
    registry = manifest["registry_semantics"]
    assert registry["replacement_seed_registry"] == REGISTRY
    assert registry["semantic_equality_verified"] is True
    expected_virtual = {
        "src/heterodiff/experiments/finite_association_residual_data.py": (
            30519,
            "8234585734b5e800cb6bc9c949e62bc7321c4f0d7cf3f06f25c5acf4619be646",
        ),
        "src/heterodiff/experiments/finite_association_isolated_runner.py": (
            246046,
            "b7a93ddb4980ed1e1665c8239ee79df2a208b64a5f894151e75b3caded3b7f05",
        ),
        "src/heterodiff/experiments/finite_association_exact_population_isolated_runner.py": (
            203943,
            "7e136cc430d532c9da1987c101ef21d77d0cb357c825cc22ba44fe7d9769aba9",
        ),
        "src/heterodiff/experiments/finite_association_execution_order.py": (
            49958,
            "448e2be0921ef93dece87b7faf2ff2acdde88d166e7c52031f03d8063a60750e",
        ),
        "src/heterodiff/experiments/finite_association_production_order.py": (
            131563,
            "7a75ab366dc38c90b3098c3b97890c6c91761b1e3ac9005e1f979ee504b3f2d6",
        ),
    }
    rules = {rule["path"]: rule for rule in CAPSULE.OVERLAY_RULES}
    rows = {row["path"]: row for row in manifest["rows"]}
    for path, (size, digest) in expected_virtual.items():
        row = rows[path]
        assert row["bytes"] == size
        assert row["virtual_raw_sha256"] == digest
        assert row["registry_semantic_equality_verified"] is True
        base = (ROOT / path).read_bytes()
        virtual = CAPSULE._apply_overlay(base, rules[path])
        assert CAPSULE._module_assignment_tuple(
            virtual, rules[path]["constant_name"], path
        ) == tuple(REGISTRY)
    assert _sha256(REGISTRY_DOMAIN + _canonical_json(REGISTRY)) == (
        audit["coordinate_manifests"]["registry_sha256"]
    )


def test_typed_coordinate_manifests_and_event_schedule_are_full_body_bound() -> None:
    coordinates = CAPSULE.coordinate_manifests()
    expected_counts = {
        "exact": 24,
        "primary": 48,
        "controls": 72,
        "complete_sampled": 120,
        "execution_phase_schedule": 144,
        "all_aggregate": 144,
    }
    for key, count in expected_counts.items():
        manifest = coordinates["manifests"][key]
        assert manifest["coordinate_count"] == count
        assert manifest["manifest_sha256"] == _sha256(
            COORDINATE_DOMAIN
            + _canonical_json(_record_body(manifest, "manifest_sha256"))
        )
        assert len(manifest["coordinates"]) == count
        assert len(manifest["underlying_request_projections"]) == count
    exact = coordinates["manifests"]["exact"]
    assert exact["coordinates"][0] == {
        "manifest_ordinal": 0,
        "manifest_ordinal_domain": "EXACT",
        "phase": "EXACT",
        "phase_coordinate_ordinal": 0,
        "seed_ordinal": 0,
        "coordinate_tag": "EXACT_SEED_METHOD",
        "seed": REGISTRY[0],
        "accepted_example_budget": None,
        "method": "direct",
    }
    assert exact["underlying_request_projections"][0] == [REGISTRY[0], "direct"]
    encoding = coordinates["coordinate_manifest_digest_domain_encoding"]
    assert encoding == {
        "ascii_label": CAPSULE.COORDINATE_MANIFEST_SCHEMA,
        "terminating_nul_hex": "00",
        "exact_prefix_hex": COORDINATE_DOMAIN.hex(),
    }
    assert bytes.fromhex(encoding["exact_prefix_hex"]) == (
        encoding["ascii_label"] + "\0"
    ).encode("ascii")
    phase = coordinates["manifests"]["execution_phase_schedule"]["coordinates"]
    aggregate = coordinates["manifests"]["all_aggregate"]["coordinates"]
    assert phase != aggregate
    events = coordinates["phase_event_schedule"]
    assert events["event_order"] == [
        "RANK",
        "EXACT",
        "PRIMARY",
        "PRIMARY_METRICS",
        "CONTROLS",
    ]
    assert events["events"][3]["event_tag"] == "PRIMARY_METRICS_BARRIER"
    assert events["events"][4]["phase_coordinate_count"] == 72
    assert events["events"][4]["prior_primary_coordinate_count"] == 48
    assert events["events"][4]["complete_sampled_coordinate_count"] == 120
    assert events["schedule_sha256"] == _sha256(
        PHASE_EVENT_DOMAIN + _canonical_json(_record_body(events, "schedule_sha256"))
    )

    hostile = json.loads(_canonical_json(exact).decode("ascii"))
    hostile["coordinates"][0], hostile["coordinates"][1] = (
        hostile["coordinates"][1],
        hostile["coordinates"][0],
    )
    assert (
        _sha256(
            COORDINATE_DOMAIN
            + _canonical_json(_record_body(hostile, "manifest_sha256"))
        )
        != exact["manifest_sha256"]
    )
    hostile = json.loads(_canonical_json(exact).decode("ascii"))
    hostile["coordinates"].append(hostile["coordinates"][0])
    assert len(hostile["coordinates"]) != hostile["coordinate_count"]
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE.TaggedCoordinateV1(
            phase="EXACT",
            phase_coordinate_ordinal=1,
            seed_ordinal=0,
            coordinate_tag="EXACT_SEED_METHOD",
            seed=REGISTRY[0],
            accepted_example_budget=None,
            method="direct",
        )


def test_runner_api_inventory_reopens_real_apis_without_freezing_a_binder() -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    inventory = audit["runner_api_inventory"]
    rows = inventory["phase_rows"]
    assert [row["phase"] for row in rows] == ["RANK", "EXACT", "PRIMARY", "CONTROLS"]
    assert inventory["inventory_only"] is True
    assert inventory["binder_schema_frozen"] is False
    assert inventory["successor_authority_frozen"] is False
    assert inventory["typed_coordinate_consumption_qualified"] is False
    assert inventory["phase_aggregate_admission_qualified"] is False
    for row in rows:
        assert row["inventory_only"] is True
        assert row["successor_request_schema_frozen"] is False
        assert row["successor_completion_schema_frozen"] is False
        assert row["typed_coordinate_consumption_qualified"] is False
        assert row["phase_aggregate_admission_qualified"] is False
        assert row["legacy_api_successor_compatible"] is False
        assert row["execution_admissible"] is False
        assert row["launch_allowed"] is False
        assert row["output_admissible"] is False
        for role in ("launcher", "loader", "revalidator"):
            signature = row[f"{role}_api_signature"]
            body = _record_body(signature, "signature_sha256")
            assert signature["signature_sha256"] == _sha256(
                b"heterodiff-r1-registry-aware-api-signature-v1\0"
                + _canonical_json(body)
            )
        assert row["execution_phase_schedule_manifest_sha256"] == (
            audit["coordinate_manifests"]["manifests"]["execution_phase_schedule"][
                "manifest_sha256"
            ]
        )
        assert row["phase_event_schedule_sha256"] == (
            audit["coordinate_manifests"]["phase_event_schedule"]["schedule_sha256"]
        )


def test_rosters_are_disjoint_closed_and_nonadmissible() -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    rosters = audit["rosters"]
    assert rosters["candidate_source_input_count"] == 48
    assert rosters["runtime_input_count"] == 7
    assert rosters["governance_count"] == len(CAPSULE.GOVERNANCE_BINDINGS)
    groups = [
        rosters["governance_custody"],
        rosters["candidate_source_inputs"],
        rosters["runtime_inputs"],
    ]
    path_sets = [{row["path"] for row in group} for group in groups]
    assert not path_sets[0] & path_sets[1]
    assert not path_sets[0] & path_sets[2]
    assert not path_sets[1] & path_sets[2]
    for group in groups:
        assert all(row["execution_admissible"] is False for row in group)
    assert all(row["is_regular_file"] is True for row in groups[0])
    assert all(row["is_symlink"] is False for row in groups[0])
    module_rows = [
        row
        for row in rosters["candidate_source_inputs"]
        if row["candidate_kind"] == "PYTHON_MODULE"
    ]
    assert len(module_rows) == 45
    for row in module_rows:
        assert row["raw_sha256"] == row["base_raw_sha256"]
        assert row["bytes"] == row["base_bytes"]
        assert row["path"] == row["base_path"] == row["virtual_target_path"]
        if row["role"] == "ONE_LITERAL_OVERLAY":
            assert row["virtual_materialized"] is False
            assert row["virtual_raw_sha256"] != row["base_raw_sha256"]


def test_preregistration_state_is_derived_and_no_gate_is_closed() -> None:
    state = CAPSULE.audit_static_overlay_source_freeze(ROOT)["preregistration_state"]
    assert state["historical_null_projection"] == {
        "total": 174,
        "preexecution": 168,
        "deferred_postexecution": 6,
    }
    assert state["pre_d1_resolved_null_count"] == 2
    assert state["effective_unresolved_null_projection"] == {
        "total": 172,
        "preexecution": 166,
        "deferred_postexecution": 6,
    }
    assert state["blockers"] == {
        "total": 12,
        "closed": 0,
        "remaining": 12,
        "confirmatory_execution": 10,
        "claim_promotion_and_submission": 2,
    }
    assert (
        state["freeze_predicate"][
            "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull"
        ]
        is False
    )
    assert state["freeze_predicate"]["test_data_unopened_before_freeze"] is None
    assert state["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert state["conditions_closed_by_this_milestone"] == 0
    current = state["authoritative_current_baselines"]
    assert current["execution_preregistration_state"] == "DRAFT_NOT_EXECUTABLE"
    assert current["execution_preregistration_unresolved_blocker_count"] == 12
    assert current["execution_preregistration_confirmatory_blocker_count"] == 10
    assert current["execution_preregistration_submission_blocker_count"] == 2
    assert current["execution_preregistration_freeze_predicate_verified"] is True
    assert current["cp76_readiness_status"] == "NOT_READY"
    assert current["cp76_manuscript_submission_ready"] is False


def test_symlink_ancestor_broken_symlink_and_toctou_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    target = real / "bound.txt"
    target.write_bytes(b"stable")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE._read_stable_regular_file(alias / "bound.txt")

    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "missing")
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE._require_absent_no_entry(broken)

    original = Path.read_bytes

    def mutate_after_read(path: Path) -> bytes:
        payload = original(path)
        if path == target:
            path.write_bytes(payload + b"!")
        return payload

    monkeypatch.setattr(Path, "read_bytes", mutate_after_read)
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE._read_stable_regular_file(target)


def test_source_extra_hash_and_scientific_overlay_mutations_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expectations = list(CAPSULE.BASE_SOURCE_EXPECTATIONS)
    path, size, digest = expectations[0]
    expectations[0] = (path, size, "0" * 64)
    monkeypatch.setattr(CAPSULE, "BASE_SOURCE_EXPECTATIONS", tuple(expectations))
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE.virtual_source_manifest(ROOT)
    monkeypatch.undo()

    monkeypatch.setattr(
        CAPSULE,
        "BASE_SOURCE_PATHS",
        CAPSULE.BASE_SOURCE_PATHS + ("src/heterodiff/forbidden_extra.py",),
    )
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE.virtual_source_manifest(ROOT)
    monkeypatch.undo()

    rules = [dict(rule) for rule in CAPSULE.OVERLAY_RULES]
    rules[0]["new_literal_utf8"] = "4_052_249_444_591_755"
    monkeypatch.setattr(CAPSULE, "OVERLAY_RULES", tuple(rules))
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE.virtual_source_manifest(ROOT)


def test_all_planned_and_legacy_roots_and_runtime_manifests_are_absent() -> None:
    audit = CAPSULE.audit_static_overlay_source_freeze(ROOT)
    for path in CAPSULE.PLANNED_OUTPUT_ROOTS + CAPSULE.LEGACY_PRODUCTION_ROOTS:
        assert not _path_has_entry(ROOT / path)
    assert not _path_has_entry(ROOT / CAPSULE.PLANNED_ADAPTER_TARGET)
    for path in CAPSULE.SUCCESSOR_RUNTIME_PATHS + (
        CAPSULE.LEGACY_RUNTIME_PATH,
        CAPSULE.LEGACY_RUNTIME_APPROVAL_PATH,
        CAPSULE.LEGACY_RUNTIME_CANDIDATE_ROOT,
    ):
        assert not _path_has_entry(ROOT / path)
    runtime = audit["runtime_and_activation_state"]
    for key, value in runtime.items():
        if key.endswith("_complete") or key in {
            "runtime_identity_present",
            "runtime_identity_approved",
            "overlay_source_tree_materialized",
            "production_order_authority_adapter_implemented",
            "legacy_virtual_production_order_execution_admissible",
            "legacy_rglob_source_manifest_usable_for_successor_activation",
            "permit_issuable",
            "direct_launch_allowed",
        }:
            assert value is False


def test_machine_sidecar_is_canonical_self_digested_and_exactly_live() -> None:
    payload, record = _load_json(MACHINE_PATH)
    assert payload == _canonical_json(record) + b"\n"
    assert record["record_sha256"] == _semantic_digest(record)
    assert record["milestone_state"] == MILESTONE_STATE
    assert record["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert _canonical_json(record["qualification_snapshot"]) == _canonical_json(
        CAPSULE.audit_static_overlay_source_freeze(ROOT)
    )
    assert record["registration_bindings"] == _expected_binding_rows()
    assert record["nonclaims"] == CAPSULE.REGISTRATION_NONCLAIMS
    assert (
        record["publication_anonymity_boundary"]
        == CAPSULE.PUBLICATION_ANONYMITY_BOUNDARY
    )
    qualification = CAPSULE.load_static_overlay_source_freeze_qualification(ROOT)
    assert type(qualification) is CAPSULE.StaticOverlaySourceFreezeQualification
    assert qualification.record_sha256 == record["record_sha256"]
    assert _canonical_json(qualification.snapshot()) == _canonical_json(
        record["qualification_snapshot"]
    )
    with pytest.raises(TypeError):
        CAPSULE.StaticOverlaySourceFreezeQualification()
    assert not hasattr(
        CAPSULE.StaticOverlaySourceFreezeQualification, "_from_verified_sidecar"
    )
    with pytest.raises(AttributeError):
        qualification.extra = False
    status = CAPSULE.status(ROOT)
    assert status["state"] == MILESTONE_STATE
    assert status["sidecar_record_sha256"] == record["record_sha256"]
    assert status["canonical_sidecar_and_bindings_reopened"] is True
    assert status["execution_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    (
        "extra_top_key",
        "anonymity_public_flip",
        "anonymity_extra_key",
        "nonclaim_removed",
        "nonclaim_alias",
        "snapshot_state_flip",
        "binding_bool_alias",
    ),
)
def test_rehashed_hostile_sidecars_are_rejected(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, record = _load_json(MACHINE_PATH)
    hostile = json.loads(_canonical_json(record).decode("ascii"))
    if mutation == "extra_top_key":
        hostile["extra"] = False
    elif mutation == "anonymity_public_flip":
        hostile["publication_anonymity_boundary"][
            "public_release_inclusion_permitted"
        ] = True
    elif mutation == "anonymity_extra_key":
        hostile["publication_anonymity_boundary"]["extra"] = False
    elif mutation == "nonclaim_removed":
        hostile["nonclaims"].pop("r1_qualified")
    elif mutation == "nonclaim_alias":
        hostile["nonclaims"]["r1_qualified"] = 0
    elif mutation == "snapshot_state_flip":
        hostile["qualification_snapshot"]["global_state"] = "FROZEN_EXECUTABLE"
    elif mutation == "binding_bool_alias":
        hostile["registration_bindings"][0]["ordinal"] = False
    else:  # pragma: no cover
        raise AssertionError(mutation)
    hostile = _rehash(hostile)
    path = tmp_path / "hostile.json"
    _write_canonical(path, hostile)
    monkeypatch.setattr(CAPSULE, "REGISTRATION_SIDECAR_PATH", str(path))
    with pytest.raises(CAPSULE.CapsuleError):
        CAPSULE.load_static_overlay_source_freeze_qualification(ROOT)


def test_human_registration_has_mandatory_nonclaims_and_no_local_identity() -> None:
    text = HUMAN_PATH.read_text(encoding="utf-8")
    assert MILESTONE_STATE in text
    assert "DRAFT_NOT_EXECUTABLE" in text
    assert "does not freeze a successor\nauthority or binder schema" in text
    assert "45-module" in text
    assert "102 local static-import edges" in text
    assert "RANK -> EXACT -> PRIMARY -> PRIMARY_METRICS -> CONTROLS" in text
    assert "cannot mint\nsuccessor-admissible records" in text
    assert "six distinct edges" in text
    assert "StaticOverlaySourceFreezeQualification" in text
    assert "Binder-schema freeze" in text
    assert "typed-coordinate consumption" in text
    assert "CP76\nremains `NOT_READY`" in text
    assert "172: 166 preexecution and 6 deferred" in text
    assert "closes none of the 12" in text
    assert "not anonymous-submission or public-release artifacts" in text
    assert "/Users/" not in text
    assert "mahtab" not in text.lower()


def test_no_extra_materialized_adapter_or_milestone_artifact_exists() -> None:
    expected = {HUMAN_PATH, MACHINE_PATH, MODULE_PATH, TEST_PATH}
    actual = {
        ROOT
        / "manuscript_v3/a1_r1_registry_aware_source_execution_capsule_freeze_v1.md",
        ROOT / "research/fixtures/"
        "manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.json",
        ROOT
        / "research/diagnostics/finite_association_r1_registry_aware_capsule_v1.py",
        ROOT / "tests/unit/"
        "test_manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.py",
    }
    assert actual == expected
    assert all(path.is_file() and not path.is_symlink() for path in expected)
    assert not _path_has_entry(ROOT / CAPSULE.PLANNED_ADAPTER_TARGET)
