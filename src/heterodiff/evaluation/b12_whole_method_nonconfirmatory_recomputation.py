"""Separate recomputation of the B12 whole-method synthetic core output.

This module intentionally does not import the primary whole-method runner.  It
independently parses the supplied canonical input and re-executes the bounded
initializer, path, adapter, F105/F144, and capsule computations.  Its output is
still development-only and leaves every real B12 receipt absent.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence, Tuple

from heterodiff.evaluation import b12_integrated_offline_candidate as _v2
from heterodiff.evaluation import b12_external_author_extension_components as external
from heterodiff.evaluation import b12_integration_stack as integration
from heterodiff.evaluation import b12_two_domain_adapter_stack as adapters
from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_tilt
from heterodiff.evaluation import formal_test29_test30_single_macrostep_integration as single
from heterodiff.evaluation import formal_test29_test30_two_macrostep_path_qualification as two
from heterodiff.evaluation import formal_test30_synthetic_coupled_path_qualification as test30
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as cp62
from heterodiff.evaluation import two_domain_count_normalized_event_cks_production as f105
from heterodiff.experiments import two_domain_training_checkpoint_plan as training
from heterodiff.processes import certified_initial_score_provider_v1 as score_facade
from heterodiff.processes import formal_test29_finite_acyclic_route_oracle as test29
from heterodiff.processes import plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as initializer


INPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
CORE_OUTPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-core-output-v1"
STATE = "OFFLINE_NONCONFIRMATORY_WHOLE_METHOD_EXERCISE_ONLY"
FROZEN_ROW = 5
FROZEN_SEED = int("12a5228200019dae", 16)
FROZEN_WORDS = (2, 27)
FROZEN_STEP = 256
PRIMARY_METHOD_ID = "association-aware-guide-plus-residual"

F105_TO_B06_DOMAIN = {
    "R4-RETAIL": "online-retail-ii",
    "R3-PHYS": "physionet-challenge-2012",
}

CAPSULE_SOURCE_PATHS = (
    "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
    "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
    "src/heterodiff/evaluation/b12_integration_stack.py",
    "src/heterodiff/evaluation/b12_whole_method_nonconfirmatory_runner.py",
    "src/heterodiff/evaluation/b12_whole_method_nonconfirmatory_recomputation.py",
    "src/heterodiff/evaluation/b12_external_author_extension_components.py",
    "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
    "src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py",
    "src/heterodiff/experiments/two_domain_training_checkpoint_plan.py",
    "src/heterodiff/experiments/two_domain_baseline_registry.py",
    "src/heterodiff/evaluation/exact_rational_quadratic_initial_tilt.py",
    "src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py",
    "src/heterodiff/processes/certified_initial_score_provider_v1.py",
    "src/heterodiff/processes/plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py",
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
    "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
    "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
    "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
)

IMPLEMENTATION_OBLIGATIONS_EXERCISED = (
    "FIXED_SEED_DEVELOPMENT_INITIALIZER_AND_SAMPLER",
    "SUPPLIED_CONTINUOUS_LEFT_RIGHT_PATH",
    "SUPPLIED_CENTRAL_JUMP_EDIT_LAW",
    "ROLLING_TWO_MACROSTEP_COMPOSITION",
    "CORRECTED_EXACT_22_ADAPTER_INTERFACE_ROSTER",
    "EXACT_64_DIMENSION_CONTEXT_ENCODER_INTERFACE",
    "TWO_DOMAIN_F105_PRODUCTION_PROJECTION",
    "F105_TO_F144_DOMAIN_NAMESPACE_BRIDGE",
    "F144_EXACT_128_GROUP_STRUCTURAL_CHECKPOINT_SEAM",
    "COMPONENT_EVIDENCE_CAPSULE_AND_PAIRED_LEDGER",
    "OPEN_50_SLOT_RUNNER_AND_SEPARATE_RECOMPUTATION",
    "CSDI_AUTHOR_EXTENSION_1",
    "CSDI_AUTHOR_EXTENSION_2",
    "CSDI_AUTHOR_EXTENSION_3",
    "CSDI_AUTHOR_EXTENSION_4",
    "EDITPP_AUTHOR_EXTENSION_1",
    "EDITPP_AUTHOR_EXTENSION_2",
    "EDITPP_AUTHOR_EXTENSION_3",
    "EDITPP_AUTHOR_EXTENSION_4",
)

REAL_RESIDUAL_IDS = tuple(_v2.semantics()["residual_predicate_ids"])


class WholeMethodIndependentRecomputationError(ValueError):
    """Fail-closed independent recomputation error."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    return _sha256(domain.encode("ascii") + b"\0" + _canonical(value))


def _pairs(pairs: Sequence[Tuple[str, object]]) -> dict:
    if type(pairs) is not list:
        raise WholeMethodIndependentRecomputationError("JSON pairs differ")
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise WholeMethodIndependentRecomputationError("duplicate JSON key")
        result[key] = value
    return result


def _decode_input(raw: object) -> Mapping[str, object]:
    if type(raw) is not bytes or not raw.endswith(b"\n") or len(raw) > 4096:
        raise WholeMethodIndependentRecomputationError("input byte framing differs")
    try:
        value = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WholeMethodIndependentRecomputationError("input JSON differs") from error
    if _canonical(value) + b"\n" != raw:
        raise WholeMethodIndependentRecomputationError("input is not canonical")
    expected_keys = (
        "checkpoint_step",
        "initializer_row_ordinal",
        "initializer_seed",
        "path_first_word",
        "path_second_word",
        "schema_version",
    )
    if type(value) is not dict or tuple(sorted(value)) != expected_keys:
        raise WholeMethodIndependentRecomputationError("input schema differs")
    for name in expected_keys[:-1]:
        if type(value[name]) is not int:
            raise WholeMethodIndependentRecomputationError("input integer type differs")
    if (
        value["schema_version"] != INPUT_SCHEMA
        or value["initializer_row_ordinal"] != FROZEN_ROW
        or value["initializer_seed"] != FROZEN_SEED
        or (value["path_first_word"], value["path_second_word"]) != FROZEN_WORDS
        or value["checkpoint_step"] != FROZEN_STEP
    ):
        raise WholeMethodIndependentRecomputationError("input fixture differs")
    return value


def _auth(label: str) -> integration.ReceiptAuthentication:
    return integration.ReceiptAuthentication(
        reviewer_principal_id="LOCAL-SYNTHETIC-WHOLE-METHOD-" + label,
        authentication_method_id="DETERMINISTIC-OFFLINE-QUALIFICATION-V1",
        authentication_evidence_sha256=_domain_sha256(
            "heterodiff-b12-whole-method-local-authentication-v1", {"label": label}
        ),
    )


def _initializer_summary(value: Mapping[str, object]) -> Mapping[str, object]:
    bundle = cp62.cp62_execution_capsule_bundle()
    row = bundle.request_bindings[value["initializer_row_ordinal"] - 1]
    if (
        row.row_ordinal != FROZEN_ROW
        or row.fixture_id != "T28-M1-Q"
        or row.strategy != "fixed-budget-sir"
        or row.budget != 8
        or row.seed_value_present
        or row.request_instance_fully_bound
        or bundle.formal_test_28_closed
        or bundle.formal_test_28_status != "OPEN"
    ):
        raise WholeMethodIndependentRecomputationError("initializer binding differs")
    source = exact_tilt.build_t28_m1_q_exact_score_provider()
    provider = score_facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    plan = initializer.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=value["initializer_seed"],
        budget=row.budget,
        ess_warning_fraction=0.25,
    )
    owner = initializer.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    owner.validate_result(result)
    if type(result) is not initializer.MixedSupportInitialTiltSIRResultV2:
        raise WholeMethodIndependentRecomputationError("initializer result differs")
    return {
        "adaptive_fallback_permitted": False,
        "budget": row.budget,
        "ess_warning": result.ess_warning,
        "fixture_id": row.fixture_id,
        "formal_test_28_closed": False,
        "initializer_role_sha256": row.initializer_role_sha256,
        "operational_source_law_verified": False,
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
        "plan_seed_hex": value["initializer_seed"].to_bytes(8, "big").hex(),
        "proposal_stream_final_state_sha256": result.proposal_stream_final_state_sha256,
        "proposal_stream_initial_state_sha256": result.proposal_stream_initial_state_sha256,
        "request_binding_sha256": row.record_sha256,
        "resampling_stream_final_state_sha256": result.resampling_stream_final_state_sha256,
        "resampling_stream_initial_state_sha256": result.resampling_stream_initial_state_sha256,
        "resampling_uniform_53": result.resampling_uniform_53,
        "resampling_word_hex": result.resampling_word.to_bytes(8, "big").hex(),
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "selected_index": result.selected_index,
        "source_certificate_sha256": row.source_certificate_sha256,
        "stable_semantics_only_process_local_certificate_digests_excluded": True,
        "status": result.status,
        "strategy": row.strategy,
    }


def _path_summary(value: Mapping[str, object]) -> Mapping[str, object]:
    supplied = two.build_frozen_two_macrostep_path_input(
        single,
        test29,
        test30,
        value["path_first_word"],
        value["path_second_word"],
    )
    result = two.run_supplied_two_macrostep_path(single, test29, test30, supplied)
    if (
        not result.passed
        or not result.bounded_two_macrostep_path_integrated
        or result.arbitrary_length_general_strang_path_integrated
        or result.parent_custody_authenticated
        or result.test28_initializer_admissible
        or result.formal_test28_closed
        or result.formal_test29_closed
        or result.formal_test30_closed
    ):
        raise WholeMethodIndependentRecomputationError("path boundary differs")
    return {
        "address_count": result.total_address_count,
        "bounded_two_macrostep_path_integrated": True,
        "boundary_state_continuity": result.boundary_state_continuity,
        "complete_input_preflight_before_first_arithmetic": (
            result.complete_input_preflight_before_first_arithmetic
        ),
        "formal_test_28_closed": False,
        "formal_test_29_closed": False,
        "formal_test_30_closed": False,
        "global_address_identities_unique": result.global_address_identities_unique,
        "input_sha256": result.input_sha256,
        "parent_custody_authenticated": False,
        "report_sha256": result.report_sha256,
        "rolling_lineage_preserved": (
            result.rolling_test29_fresh_retired_lineage_preserved
        ),
        "steps": [
            {
                "central_jump_count": step.central_jump_count,
                "family": step.family,
                "raw64_word": step.raw64_word,
                "route_id": step.route_id,
                "step_index": step.step_index,
            }
            for step in result.steps
        ],
        "total_central_jumps": result.total_central_jumps,
        "total_left_heun_applications": result.total_left_heun_applications,
        "total_right_heun_applications": result.total_right_heun_applications,
    }


def _normalized_factory_subject(score: Mapping[str, object], domain: str) -> str:
    return _domain_sha256(
        "heterodiff-production-cks-score-v1",
        {
            "binary64_score_hex": score["binary64_score_hex"],
            "domain_id": domain,
            "draw_count": training.F136_DRAWS_PER_CASE,
            "formal_score_sha256": score["formal_score_sha256"],
            "integration_id": f105.PRODUCTION_INTEGRATION_ID,
            "metric_id": score["metric_id"],
            "score_direction": f105.SCORE_DIRECTION,
            "symbolic_event_pair_work_units": score[
                "symbolic_event_pair_work_units"
            ],
        },
    )


def _checkpoint_bridge(configuration: object, value: Mapping[str, object]) -> Mapping[str, object]:
    score = dict(
        f105.score_record(
            f105.production_conditional_cks_score(
                (configuration,) * training.F136_DRAWS_PER_CASE, configuration
            )
        )
    )
    f105_domain = score["domain_id"]
    b06_domain = F105_TO_B06_DOMAIN[f105_domain]
    executable = [
        row
        for row in training.executable_configuration_rows()
        if row["method_id"] == PRIMARY_METHOD_ID and row["domain_id"] == b06_domain
    ]
    if len(executable) != 1:
        raise WholeMethodIndependentRecomputationError("executable row differs")
    executable_sha = executable[0]["executable_configuration_sha256"]
    checkpoint_sha = _domain_sha256(
        "heterodiff-b12-synthetic-checkpoint-content-v1",
        {"b06_domain_id": b06_domain},
    )
    selection_sha = _domain_sha256(
        "heterodiff-b12-synthetic-selection-unit-v1",
        {"b06_domain_id": b06_domain},
    )
    normalized_factory = _normalized_factory_subject(score, b06_domain)
    rows = []
    for ordinal in range(training.F134_VALIDATION_GROUP_COUNT):
        group_sha = _domain_sha256(
            "heterodiff-b12-synthetic-f144-group-v1",
            {"b06_domain_id": b06_domain, "ordinal": ordinal},
        )
        integrity = _domain_sha256(
            "heterodiff-f144-bound-group-score-integrity-v1",
            {
                "binary64_score_hex": score["binary64_score_hex"],
                "checkpoint_content_sha256": checkpoint_sha,
                "domain_id": b06_domain,
                "draw_count": training.F136_DRAWS_PER_CASE,
                "executable_configuration_sha256": executable_sha,
                "f105_factory_score_integrity_sha256": normalized_factory,
                "group_id_sha256": group_sha,
                "integration_id": f105.PRODUCTION_INTEGRATION_ID,
                "method_id": PRIMARY_METHOD_ID,
                "metric_id": score["metric_id"],
                "ordinal": ordinal,
                "selection_unit_sha256": selection_sha,
            },
        )
        rows.append(
            {
                "binary64_score_hex": score["binary64_score_hex"],
                "f105_factory_score_integrity_sha256": normalized_factory,
                "formal_score_sha256": score["formal_score_sha256"],
                "group_id_sha256": group_sha,
                "ordinal": ordinal,
                "score_integrity_sha256": integrity,
                "symbolic_event_pair_work_units": score[
                    "symbolic_event_pair_work_units"
                ],
            }
        )
    roster_sha = _domain_sha256(
        "heterodiff-f144-complete-f134-validation-group-roster-v1",
        [row["group_id_sha256"] for row in rows],
    )
    subject = training.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=checkpoint_sha,
        domain_id=b06_domain,
        executable_configuration_sha256=executable_sha,
        group_roster_sha256=roster_sha,
        group_score_integrity_sha256s=[row["score_integrity_sha256"] for row in rows],
        method_id=PRIMARY_METHOD_ID,
        selection_unit_sha256=selection_sha,
    )
    structural = training.validate_structural_checkpoint_validation(
        {
            "checkpoint_content_sha256": checkpoint_sha,
            "complete_roster_certificate_subject_sha256": subject,
            "completed_optimizer_updates": value["checkpoint_step"],
            "domain_id": b06_domain,
            "executable_configuration_sha256": executable_sha,
            "group_roster_sha256": roster_sha,
            "group_scores": rows,
            "method_id": PRIMARY_METHOD_ID,
            "selection_unit_sha256": selection_sha,
        }
    )
    actual = score["integrity_sha256"]
    if actual == normalized_factory:
        raise WholeMethodIndependentRecomputationError("domain subjects collapsed")
    bridge_sha = _domain_sha256(
        "heterodiff-b12-f105-f144-domain-namespace-bridge-v1",
        {
            "actual_f105_factory_integrity_sha256": actual,
            "b06_domain_id": b06_domain,
            "f105_domain_id": f105_domain,
            "f144_normalized_factory_subject_sha256": normalized_factory,
            "mapping_policy": "EXPLICIT_BIJECTIVE_F105_TO_B06_DOMAIN_ID_ONLY",
        },
    )
    return {
        "actual_f105_factory_integrity_sha256": actual,
        "b06_domain_id": b06_domain,
        "f105_domain_id": f105_domain,
        "f144_normalized_factory_subject_sha256": normalized_factory,
        "factory_and_f144_namespace_subjects_byte_equal": False,
        "f105_score": score,
        "namespace_bridge_sha256": bridge_sha,
        "production_history_authenticated": False,
        "structural_checkpoint_receipt": structural,
    }


def _external_summary(project_root: str) -> Mapping[str, object]:
    source = Path(project_root) / (
        "src/heterodiff/evaluation/b12_external_author_extension_components.py"
    )
    source_sha = _sha256(source.read_bytes())
    retail, physionet = external.qualification_fixture_configurations()
    csdi = external.build_csdi_author_adapter(
        configuration=physionet, module_source_sha256=source_sha
    )
    if external.decode_csdi_event_multiset(csdi.occurrences) != physionet:
        raise WholeMethodIndependentRecomputationError("CSDI decode differs")
    editpp = external.build_editpp_author_adapter(
        configuration=retail, module_source_sha256=source_sha
    )
    csdi_interface = external.build_csdi_conditioning_interface(
        adapter=csdi, observed_occurrence_serials=(0, 2)
    )
    editpp_interface = external.build_editpp_conditioning_interface(
        adapter=editpp, observed_occurrence_serials=(1,)
    )
    csdi_interface.semantic_payload(adapter=csdi)
    editpp_interface.semantic_payload(adapter=editpp)
    manifest = external.build_author_extension_implementation_manifest(
        module_source_sha256=source_sha
    )
    ids = tuple(record.predicate_id for record in manifest)
    expected = tuple(f"CSDI_AUTHOR_EXTENSION_{i}" for i in range(1, 5)) + tuple(
        f"EDITPP_AUTHOR_EXTENSION_{i}" for i in range(1, 5)
    )
    if ids != expected:
        raise WholeMethodIndependentRecomputationError("extension IDs differ")
    interfaces = (csdi_interface, editpp_interface)
    if any(
        slot.status != external.DRAW_SLOT_STATUS
        or slot.generated_configuration_sha256 is not None
        for interface in interfaces
        for slot in interface.draw_slots
    ):
        raise WholeMethodIndependentRecomputationError("extension output minted")
    manifest_sha = _domain_sha256(
        "heterodiff-b12-external-author-extension-manifest-binding-v1",
        {
            "implementation_record_sha256s": [
                record.record_sha256 for record in manifest
            ],
            "module_source_sha256": source_sha,
            "predicate_ids": list(ids),
        },
    )
    return {
        "adapters": [
            {
                "adapter_id": adapter.adapter_id,
                "adapter_sha256": adapter.adapter_sha256,
                "context_dimension": len(adapter.context.coordinates),
                "context_encoding_sha256": adapter.context.encoding_sha256,
                "event_count": len(adapter.occurrences),
                "retail_structured_mark_head_count": len(
                    adapter.retail_mark_heads
                ),
                "upstream_package_executed": False,
            }
            for adapter in (csdi, editpp)
        ],
        "conditioning_interfaces": [
            {
                "adapter_id": interface.adapter_id,
                "draw_count": len(interface.draw_slots),
                "generated_output_count": sum(
                    slot.generated_configuration_sha256 is not None
                    for slot in interface.draw_slots
                ),
                "interface_sha256": interface.interface_sha256,
                "mask_sha256": interface.mask_sha256,
                "pending_draw_status": external.DRAW_SLOT_STATUS,
            }
            for interface in interfaces
        ],
        "csdi_occurrence_decoder_roundtrip_exact": True,
        "implementation_manifest_sha256": manifest_sha,
        "implementation_record_sha256s": [
            record.record_sha256 for record in manifest
        ],
        "module_source_sha256": source_sha,
        "predicate_ids": list(ids),
        "production_receipts_claimed": False,
        "upstream_native_functionality_claimed": False,
        "upstream_packages_executed": False,
    }


def _core(project_root: str, value: Mapping[str, object], input_sha256: str) -> Mapping[str, object]:
    root = Path(project_root)
    if type(project_root) is not str or str(root) != project_root or root.resolve(strict=True) != root:
        raise WholeMethodIndependentRecomputationError("project root differs")
    bindings = integration.build_component_bindings(project_root)
    adapter_binding = integration.build_synthetic_adapter_manifest_binding(project_root)
    capsule = integration.build_closed_world_capsule_plan(
        project_root,
        "B12-WHOLE-METHOD-NONCONFIRMATORY-CAPSULE-V1",
        CAPSULE_SOURCE_PATHS,
        bindings,
        _auth("CAPSULE"),
    )
    retail, physionet = adapters.qualification_fixture_configurations()
    encodings = [
        adapters.encode_exact_context(retail),
        adapters.encode_exact_context(physionet),
    ]
    return {
        "adapter_and_capsule": {
            "adapter_manifest_sha256": adapter_binding.manifest_sha256,
            "adapter_receipt_count": len(adapter_binding.receipts),
            "capsule_manifest_raw_sha256": capsule.manifest_raw_sha256,
            "capsule_receipt_manifest_sha256": capsule.receipt.manifest_sha256,
            "capsule_scope": integration.CAPSULE_SCOPE,
            "component_binding_document_sha256": capsule.component_binding_document_sha256,
            "component_binding_count": len(bindings),
            "legacy_adapter_mismatch_ordinals": list(
                adapters.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS
            ),
            "synthetic_adapter_interface_only": True,
        },
        "context_encoders": [
            {
                "context_dimension": len(item.coordinates),
                "domain_id": item.b06_domain_id,
                "encoding_sha256": item.encoding_sha256,
                "event_count": item.event_count,
            }
            for item in encodings
        ],
        "effects": {
            "authority_created": False,
            "blocker_delta": 0,
            "data_accessed": False,
            "entropy_acquired": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "production_receipts_minted": False,
            "result_delta": 0,
            "science_executed": False,
            "tracker_edited": False,
            "training_executed": False,
        },
        "f105_checkpoint_bridges": [
            _checkpoint_bridge(retail, value),
            _checkpoint_bridge(physionet, value),
        ],
        "external_author_extensions": _external_summary(project_root),
        "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
        "implementation_obligations_exercised": list(
            IMPLEMENTATION_OBLIGATIONS_EXERCISED
        ),
        "initializer_and_sampler": _initializer_summary(value),
        "real_residual_receipt_states": [
            {"predicate_id": identifier, "state": "OPEN_RECEIPT_ABSENT"}
            for identifier in REAL_RESIDUAL_IDS
        ],
        "schema_version": CORE_OUTPUT_SCHEMA,
        "state": STATE,
        "supplied_input_sha256": input_sha256,
        "two_macrostep_continuous_jump_path": _path_summary(value),
    }


def independently_recompute_whole_method(project_root: str, input_bytes: object) -> bytes:
    """Recompute the complete bounded core without importing the primary runner."""

    value = _decode_input(input_bytes)
    input_sha256 = _domain_sha256(
        "heterodiff-b12-whole-method-nonconfirmatory-input-v1", value
    )
    return _canonical(_core(project_root, value, input_sha256)) + b"\n"


__all__ = [
    "WholeMethodIndependentRecomputationError",
    "independently_recompute_whole_method",
]
