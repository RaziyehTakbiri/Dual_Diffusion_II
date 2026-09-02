"""Deterministic offline whole-method composition on supplied synthetic inputs.

This module is an implementation qualification seam.  It composes one fixed-
seed Test-28 development initializer/sampler, one supplied Test-29/Test-30
two-macrostep path, the corrected 22-row adapter manifest, both exact F105
domain projections, the F144 structural checkpoint seam, the accepted B12
component/evidence capsule, a paired in-memory ledger, the open B12 runner,
and a separate recomputation implementation.

Nothing here is a production receipt.  The seed is a caller-visible synthetic
fixture value and all 50 real B12 residual receipt slots remain absent.  The
eight external author-extension *component interfaces* are exercised, but no
upstream package is executed and their 128 pending draw slots contain no model
output.  Production history is unauthenticated and Formal Tests 28--30 remain
open/pending.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Mapping, Tuple

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


SCHEMA_VERSION = "heterodiff-b12-whole-method-nonconfirmatory-runner-v1"
INPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
CORE_OUTPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-core-output-v1"
RECEIPT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-receipt-v1"
STATE = "OFFLINE_NONCONFIRMATORY_WHOLE_METHOD_EXERCISE_ONLY"
INPUT_DOMAIN = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
CORE_DOMAIN = "heterodiff-b12-whole-method-nonconfirmatory-core-v1"
RECEIPT_DOMAIN = "heterodiff-b12-whole-method-nonconfirmatory-receipt-v1"

FROZEN_INITIALIZER_ROW_ORDINAL = 5
FROZEN_INITIALIZER_SEED = int("12a5228200019dae", 16)
FROZEN_PATH_WORDS = (2, 27)
FROZEN_CHECKPOINT_STEP = 256
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
if len(REAL_RESIDUAL_IDS) != 50 or len(set(REAL_RESIDUAL_IDS)) != 50:
    raise RuntimeError("accepted B12 residual roster is not exact-50 unique")


class WholeMethodNonconfirmatoryError(ValueError):
    """Raised before a value crosses this nonconfirmatory boundary."""


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
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty text")
    return _sha256(domain.encode("ascii") + b"\0" + _canonical(value))


def _raw_domain_sha256(domain: str, raw: bytes) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty text")
    if type(raw) is not bytes:
        raise TypeError("raw digest input must be exact bytes")
    return _sha256(domain.encode("ascii") + b"\0" + raw)


def _exact_sha256(value: object, *, name: str, nonzero: bool = False) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise WholeMethodNonconfirmatoryError(name + " must be lowercase SHA-256")
    if nonzero and value == "0" * 64:
        raise WholeMethodNonconfirmatoryError(name + " must be nonzero")
    return value


@dataclass(frozen=True)
class SuppliedNonconfirmatoryInput:
    schema_version: str
    initializer_row_ordinal: int
    initializer_seed: int
    path_first_word: int
    path_second_word: int
    checkpoint_step: int
    input_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not SuppliedNonconfirmatoryInput:
            raise TypeError("supplied input must have exact concrete type")
        payload = {
            "checkpoint_step": self.checkpoint_step,
            "initializer_row_ordinal": self.initializer_row_ordinal,
            "initializer_seed": self.initializer_seed,
            "path_first_word": self.path_first_word,
            "path_second_word": self.path_second_word,
            "schema_version": self.schema_version,
        }
        if (
            self.schema_version != INPUT_SCHEMA
            or type(self.initializer_row_ordinal) is not int
            or self.initializer_row_ordinal != FROZEN_INITIALIZER_ROW_ORDINAL
            or type(self.initializer_seed) is not int
            or self.initializer_seed != FROZEN_INITIALIZER_SEED
            or type(self.path_first_word) is not int
            or type(self.path_second_word) is not int
            or (self.path_first_word, self.path_second_word) != FROZEN_PATH_WORDS
            or type(self.checkpoint_step) is not int
            or self.checkpoint_step != FROZEN_CHECKPOINT_STEP
        ):
            raise WholeMethodNonconfirmatoryError(
                "supplied input differs from the bounded nonconfirmatory fixture"
            )
        if self.input_sha256 != _domain_sha256(INPUT_DOMAIN, payload):
            raise WholeMethodNonconfirmatoryError("supplied input digest differs")
        return payload


def build_frozen_nonconfirmatory_input() -> SuppliedNonconfirmatoryInput:
    payload = {
        "checkpoint_step": FROZEN_CHECKPOINT_STEP,
        "initializer_row_ordinal": FROZEN_INITIALIZER_ROW_ORDINAL,
        "initializer_seed": FROZEN_INITIALIZER_SEED,
        "path_first_word": FROZEN_PATH_WORDS[0],
        "path_second_word": FROZEN_PATH_WORDS[1],
        "schema_version": INPUT_SCHEMA,
    }
    result = SuppliedNonconfirmatoryInput(
        schema_version=INPUT_SCHEMA,
        initializer_row_ordinal=FROZEN_INITIALIZER_ROW_ORDINAL,
        initializer_seed=FROZEN_INITIALIZER_SEED,
        path_first_word=FROZEN_PATH_WORDS[0],
        path_second_word=FROZEN_PATH_WORDS[1],
        checkpoint_step=FROZEN_CHECKPOINT_STEP,
        input_sha256=_domain_sha256(INPUT_DOMAIN, payload),
    )
    result.payload()
    return result


def supplied_input_canonical_json_bytes(value: SuppliedNonconfirmatoryInput) -> bytes:
    if type(value) is not SuppliedNonconfirmatoryInput:
        raise TypeError("value must have exact supplied-input type")
    return _canonical(value.payload()) + b"\n"


def _qualification_authentication(label: str) -> integration.ReceiptAuthentication:
    if type(label) is not str or not label or not label.isascii():
        raise TypeError("qualification label must be exact ASCII text")
    return integration.ReceiptAuthentication(
        reviewer_principal_id="LOCAL-SYNTHETIC-WHOLE-METHOD-" + label,
        authentication_method_id="DETERMINISTIC-OFFLINE-QUALIFICATION-V1",
        authentication_evidence_sha256=_domain_sha256(
            "heterodiff-b12-whole-method-local-authentication-v1", {"label": label}
        ),
    )


def _initializer_summary(supplied: SuppliedNonconfirmatoryInput) -> Mapping[str, object]:
    bundle = cp62.cp62_execution_capsule_bundle()
    if bundle.formal_test_28_closed or bundle.formal_test_28_status != "OPEN":
        raise WholeMethodNonconfirmatoryError("Test-28 predecessor state widened")
    row = bundle.request_bindings[supplied.initializer_row_ordinal - 1]
    if (
        row.row_ordinal != FROZEN_INITIALIZER_ROW_ORDINAL
        or row.fixture_id != "T28-M1-Q"
        or row.strategy != "fixed-budget-sir"
        or row.budget != 8
        or row.seed_value_present
        or row.request_instance_fully_bound
    ):
        raise WholeMethodNonconfirmatoryError("Test-28 request binding differs")
    source = exact_tilt.build_t28_m1_q_exact_score_provider()
    provider = score_facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    if (
        provider.certificate.certificate_sha256 != row.facade_certificate_sha256
        or source.certificate.certificate_sha256 != row.source_certificate_sha256
    ):
        raise WholeMethodNonconfirmatoryError("Test-28 source/facade binding differs")
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
        raise WholeMethodNonconfirmatoryError("initializer result arm differs")
    particles = [
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
    ]
    return {
        "adaptive_fallback_permitted": False,
        "budget": row.budget,
        "ess_warning": result.ess_warning,
        "fixture_id": row.fixture_id,
        "formal_test_28_closed": False,
        "initializer_role_sha256": row.initializer_role_sha256,
        "operational_source_law_verified": False,
        "particles": particles,
        "plan_seed_hex": supplied.initializer_seed.to_bytes(8, "big").hex(),
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


def _path_summary(supplied: SuppliedNonconfirmatoryInput) -> Mapping[str, object]:
    path_input = two.build_frozen_two_macrostep_path_input(
        single,
        test29,
        test30,
        supplied.path_first_word,
        supplied.path_second_word,
    )
    result = two.run_supplied_two_macrostep_path(single, test29, test30, path_input)
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
        raise WholeMethodNonconfirmatoryError("supplied path nonclaim boundary differs")
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


def _group_roster_sha256(rows: list[Mapping[str, object]]) -> str:
    return _domain_sha256(
        "heterodiff-f144-complete-f134-validation-group-roster-v1",
        [row["group_id_sha256"] for row in rows],
    )


def _normalized_factory_subject(score: Mapping[str, object], b06_domain_id: str) -> str:
    return _domain_sha256(
        "heterodiff-production-cks-score-v1",
        {
            "binary64_score_hex": score["binary64_score_hex"],
            "domain_id": b06_domain_id,
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


def _checkpoint_bridge(
    configuration: object, supplied: SuppliedNonconfirmatoryInput
) -> Mapping[str, object]:
    score_object = f105.production_conditional_cks_score(
        (configuration,) * training.F136_DRAWS_PER_CASE, configuration
    )
    score = dict(f105.score_record(score_object))
    f105_domain_id = score["domain_id"]
    b06_domain_id = F105_TO_B06_DOMAIN[f105_domain_id]
    executable = [
        row
        for row in training.executable_configuration_rows()
        if row["method_id"] == PRIMARY_METHOD_ID and row["domain_id"] == b06_domain_id
    ]
    if len(executable) != 1:
        raise WholeMethodNonconfirmatoryError("primary executable row is not unique")
    executable_sha256 = executable[0]["executable_configuration_sha256"]
    checkpoint_sha256 = _domain_sha256(
        "heterodiff-b12-synthetic-checkpoint-content-v1",
        {"b06_domain_id": b06_domain_id},
    )
    selection_sha256 = _domain_sha256(
        "heterodiff-b12-synthetic-selection-unit-v1",
        {"b06_domain_id": b06_domain_id},
    )
    normalized_factory_sha256 = _normalized_factory_subject(score, b06_domain_id)
    rows: list[Mapping[str, object]] = []
    for ordinal in range(training.F134_VALIDATION_GROUP_COUNT):
        group_sha256 = _domain_sha256(
            "heterodiff-b12-synthetic-f144-group-v1",
            {"b06_domain_id": b06_domain_id, "ordinal": ordinal},
        )
        group_integrity_sha256 = _domain_sha256(
            "heterodiff-f144-bound-group-score-integrity-v1",
            {
                "binary64_score_hex": score["binary64_score_hex"],
                "checkpoint_content_sha256": checkpoint_sha256,
                "domain_id": b06_domain_id,
                "draw_count": training.F136_DRAWS_PER_CASE,
                "executable_configuration_sha256": executable_sha256,
                "f105_factory_score_integrity_sha256": normalized_factory_sha256,
                "group_id_sha256": group_sha256,
                "integration_id": f105.PRODUCTION_INTEGRATION_ID,
                "method_id": PRIMARY_METHOD_ID,
                "metric_id": score["metric_id"],
                "ordinal": ordinal,
                "selection_unit_sha256": selection_sha256,
            },
        )
        rows.append(
            {
                "binary64_score_hex": score["binary64_score_hex"],
                "f105_factory_score_integrity_sha256": normalized_factory_sha256,
                "formal_score_sha256": score["formal_score_sha256"],
                "group_id_sha256": group_sha256,
                "ordinal": ordinal,
                "score_integrity_sha256": group_integrity_sha256,
                "symbolic_event_pair_work_units": score[
                    "symbolic_event_pair_work_units"
                ],
            }
        )
    roster_sha256 = _group_roster_sha256(rows)
    certificate_subject_sha256 = training.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=checkpoint_sha256,
        domain_id=b06_domain_id,
        executable_configuration_sha256=executable_sha256,
        group_roster_sha256=roster_sha256,
        group_score_integrity_sha256s=[
            row["score_integrity_sha256"] for row in rows
        ],
        method_id=PRIMARY_METHOD_ID,
        selection_unit_sha256=selection_sha256,
    )
    validation_input = {
        "checkpoint_content_sha256": checkpoint_sha256,
        "complete_roster_certificate_subject_sha256": certificate_subject_sha256,
        "completed_optimizer_updates": supplied.checkpoint_step,
        "domain_id": b06_domain_id,
        "executable_configuration_sha256": executable_sha256,
        "group_roster_sha256": roster_sha256,
        "group_scores": rows,
        "method_id": PRIMARY_METHOD_ID,
        "selection_unit_sha256": selection_sha256,
    }
    structural = training.validate_structural_checkpoint_validation(validation_input)
    actual_factory_sha256 = score["integrity_sha256"]
    if actual_factory_sha256 == normalized_factory_sha256:
        raise WholeMethodNonconfirmatoryError(
            "F105 and B06 namespace subjects unexpectedly collapsed"
        )
    namespace_bridge_sha256 = _domain_sha256(
        "heterodiff-b12-f105-f144-domain-namespace-bridge-v1",
        {
            "actual_f105_factory_integrity_sha256": actual_factory_sha256,
            "b06_domain_id": b06_domain_id,
            "f105_domain_id": f105_domain_id,
            "f144_normalized_factory_subject_sha256": normalized_factory_sha256,
            "mapping_policy": "EXPLICIT_BIJECTIVE_F105_TO_B06_DOMAIN_ID_ONLY",
        },
    )
    return {
        "actual_f105_factory_integrity_sha256": actual_factory_sha256,
        "b06_domain_id": b06_domain_id,
        "f105_domain_id": f105_domain_id,
        "f144_normalized_factory_subject_sha256": normalized_factory_sha256,
        "factory_and_f144_namespace_subjects_byte_equal": False,
        "f105_score": score,
        "namespace_bridge_sha256": namespace_bridge_sha256,
        "production_history_authenticated": False,
        "structural_checkpoint_receipt": structural,
    }


def _capsule_and_adapter_summary(project_root: str) -> Tuple[Mapping[str, object], object, object]:
    bindings = integration.build_component_bindings(project_root)
    adapter_binding = integration.build_synthetic_adapter_manifest_binding(project_root)
    capsule = integration.build_closed_world_capsule_plan(
        project_root,
        "B12-WHOLE-METHOD-NONCONFIRMATORY-CAPSULE-V1",
        CAPSULE_SOURCE_PATHS,
        bindings,
        _qualification_authentication("CAPSULE"),
    )
    summary = {
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
    }
    return summary, capsule, adapter_binding


def _external_author_extension_summary(project_root: str) -> Mapping[str, object]:
    source_path = Path(project_root) / (
        "src/heterodiff/evaluation/b12_external_author_extension_components.py"
    )
    source_sha256 = _sha256(source_path.read_bytes())
    retail, physionet = external.qualification_fixture_configurations()
    csdi = external.build_csdi_author_adapter(
        configuration=physionet, module_source_sha256=source_sha256
    )
    if external.decode_csdi_event_multiset(csdi.occurrences) != physionet:
        raise WholeMethodNonconfirmatoryError("CSDI occurrence decoder differs")
    editpp = external.build_editpp_author_adapter(
        configuration=retail, module_source_sha256=source_sha256
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
        module_source_sha256=source_sha256
    )
    predicate_ids = tuple(record.predicate_id for record in manifest)
    expected_ids = tuple(
        f"CSDI_AUTHOR_EXTENSION_{ordinal}" for ordinal in range(1, 5)
    ) + tuple(f"EDITPP_AUTHOR_EXTENSION_{ordinal}" for ordinal in range(1, 5))
    if predicate_ids != expected_ids:
        raise WholeMethodNonconfirmatoryError("external extension roster differs")
    interfaces = (csdi_interface, editpp_interface)
    if any(
        slot.status != external.DRAW_SLOT_STATUS
        or slot.generated_configuration_sha256 is not None
        for interface in interfaces
        for slot in interface.draw_slots
    ):
        raise WholeMethodNonconfirmatoryError("external pending slot minted output")
    manifest_sha256 = _domain_sha256(
        "heterodiff-b12-external-author-extension-manifest-binding-v1",
        {
            "implementation_record_sha256s": [
                record.record_sha256 for record in manifest
            ],
            "module_source_sha256": source_sha256,
            "predicate_ids": list(predicate_ids),
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
        "implementation_manifest_sha256": manifest_sha256,
        "implementation_record_sha256s": [
            record.record_sha256 for record in manifest
        ],
        "module_source_sha256": source_sha256,
        "predicate_ids": list(predicate_ids),
        "production_receipts_claimed": False,
        "upstream_native_functionality_claimed": False,
        "upstream_packages_executed": False,
    }


def _core_output(
    project_root: str, supplied: SuppliedNonconfirmatoryInput
) -> Tuple[Mapping[str, object], object, object]:
    supplied.payload()
    root = Path(project_root)
    if type(project_root) is not str or str(root) != project_root or root.resolve(strict=True) != root:
        raise WholeMethodNonconfirmatoryError("project root must be canonical absolute text")
    capsule_summary, capsule, adapter_binding = _capsule_and_adapter_summary(project_root)
    retail, physionet = adapters.qualification_fixture_configurations()
    context_encodings = [
        adapters.encode_exact_context(retail),
        adapters.encode_exact_context(physionet),
    ]
    output = {
        "adapter_and_capsule": capsule_summary,
        "context_encoders": [
            {
                "context_dimension": len(value.coordinates),
                "domain_id": value.b06_domain_id,
                "encoding_sha256": value.encoding_sha256,
                "event_count": value.event_count,
            }
            for value in context_encodings
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
            _checkpoint_bridge(retail, supplied),
            _checkpoint_bridge(physionet, supplied),
        ],
        "external_author_extensions": _external_author_extension_summary(project_root),
        "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
        "implementation_obligations_exercised": list(
            IMPLEMENTATION_OBLIGATIONS_EXERCISED
        ),
        "initializer_and_sampler": _initializer_summary(supplied),
        "real_residual_receipt_states": [
            {"predicate_id": predicate_id, "state": "OPEN_RECEIPT_ABSENT"}
            for predicate_id in REAL_RESIDUAL_IDS
        ],
        "schema_version": CORE_OUTPUT_SCHEMA,
        "state": STATE,
        "supplied_input_sha256": supplied.input_sha256,
        "two_macrostep_continuous_jump_path": _path_summary(supplied),
    }
    return output, capsule, adapter_binding


def _ledger_pair(request_bytes: bytes, outcome_bytes: bytes) -> Tuple[_v2.LedgerEvent, ...]:
    operation_id = "B12-WHOLE-METHOD-NONCONFIRMATORY-EXERCISE"
    request_sha256 = _raw_domain_sha256(
        "heterodiff-b12-operation-request-v1", request_bytes
    )
    intent_payload = {
        "event_kind": "INTENT",
        "observation_sha256": None,
        "operation_id": operation_id,
        "ordinal": 0,
        "previous_event_sha256": "0" * 64,
        "request_sha256": request_sha256,
    }
    intent = _v2.LedgerEvent(
        ordinal=0,
        event_kind="INTENT",
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=None,
        previous_event_sha256="0" * 64,
        event_sha256=_v2.sha("heterodiff-b12-ledger-event-v1", intent_payload),
    )
    outcome_payload = {
        "event_kind": "OUTCOME",
        "observation_sha256": _raw_domain_sha256(
            "heterodiff-b12-operation-outcome-v1", outcome_bytes
        ),
        "operation_id": operation_id,
        "ordinal": 1,
        "previous_event_sha256": intent.event_sha256,
        "request_sha256": request_sha256,
    }
    outcome = _v2.LedgerEvent(
        ordinal=1,
        event_kind="OUTCOME",
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=outcome_payload["observation_sha256"],
        previous_event_sha256=intent.event_sha256,
        event_sha256=_v2.sha("heterodiff-b12-ledger-event-v1", outcome_payload),
    )
    events = (intent, outcome)
    _v2.validate_ledger(events)
    return events


@dataclass(frozen=True)
class WholeMethodNonconfirmatoryReceipt:
    schema_version: str
    state: str
    supplied_input_sha256: str
    core_output_sha256: str
    independent_output_sha256: str
    independent_implementation_sha256: str
    capsule_manifest_sha256: str
    adapter_manifest_sha256: str
    ledger_event_sha256s: Tuple[str, str]
    open_residual_predicate_ids: Tuple[str, ...]
    runner_subject_sha256: str
    implementation_obligations_exercised: Tuple[str, ...]
    receipt_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not WholeMethodNonconfirmatoryReceipt:
            raise TypeError("receipt must have exact concrete type")
        payload = {
            "adapter_manifest_sha256": self.adapter_manifest_sha256,
            "capsule_manifest_sha256": self.capsule_manifest_sha256,
            "core_output_sha256": self.core_output_sha256,
            "implementation_obligations_exercised": list(
                self.implementation_obligations_exercised
            ),
            "independent_implementation_sha256": self.independent_implementation_sha256,
            "independent_output_sha256": self.independent_output_sha256,
            "ledger_event_sha256s": list(self.ledger_event_sha256s),
            "open_residual_predicate_ids": list(self.open_residual_predicate_ids),
            "runner_subject_sha256": self.runner_subject_sha256,
            "schema_version": self.schema_version,
            "state": self.state,
            "supplied_input_sha256": self.supplied_input_sha256,
        }
        if self.schema_version != RECEIPT_SCHEMA or self.state != STATE:
            raise WholeMethodNonconfirmatoryError("receipt schema or state differs")
        for name in (
            "supplied_input_sha256",
            "core_output_sha256",
            "independent_output_sha256",
            "independent_implementation_sha256",
            "capsule_manifest_sha256",
            "adapter_manifest_sha256",
            "runner_subject_sha256",
        ):
            _exact_sha256(getattr(self, name), name=name, nonzero=True)
        if self.core_output_sha256 != self.independent_output_sha256:
            raise WholeMethodNonconfirmatoryError("independent output digest differs")
        if (
            type(self.ledger_event_sha256s) is not tuple
            or len(self.ledger_event_sha256s) != 2
            or not all(
                _exact_sha256(value, name="ledger event", nonzero=True)
                for value in self.ledger_event_sha256s
            )
        ):
            raise WholeMethodNonconfirmatoryError("ledger event roster differs")
        if self.open_residual_predicate_ids != REAL_RESIDUAL_IDS:
            raise WholeMethodNonconfirmatoryError("open residual roster differs")
        if self.implementation_obligations_exercised != IMPLEMENTATION_OBLIGATIONS_EXERCISED:
            raise WholeMethodNonconfirmatoryError("implementation roster differs")
        if self.receipt_sha256 != _domain_sha256(RECEIPT_DOMAIN, payload):
            raise WholeMethodNonconfirmatoryError("receipt digest differs")
        return payload


def validate_whole_method_nonconfirmatory_receipt(
    receipt: WholeMethodNonconfirmatoryReceipt,
) -> WholeMethodNonconfirmatoryReceipt:
    if type(receipt) is not WholeMethodNonconfirmatoryReceipt:
        raise TypeError("receipt must have exact concrete type")
    receipt.payload()
    return receipt


def receipt_canonical_json_bytes(receipt: WholeMethodNonconfirmatoryReceipt) -> bytes:
    validate_whole_method_nonconfirmatory_receipt(receipt)
    document = dict(receipt.payload())
    document["receipt_sha256"] = receipt.receipt_sha256
    return _canonical(document) + b"\n"


def run_supplied_nonconfirmatory_whole_method(
    project_root: str,
    supplied_input: SuppliedNonconfirmatoryInput,
) -> WholeMethodNonconfirmatoryReceipt:
    """Execute the bounded offline composition and return one stable receipt."""

    if type(supplied_input) is not SuppliedNonconfirmatoryInput:
        raise TypeError("supplied_input must have exact concrete type")
    input_bytes = supplied_input_canonical_json_bytes(supplied_input)
    core, capsule, adapter_binding = _core_output(project_root, supplied_input)
    core_bytes = _canonical(core) + b"\n"
    core_sha256 = _sha256(core_bytes)

    independent_path = Path(project_root) / CAPSULE_SOURCE_PATHS[4]
    independent_raw = independent_path.read_bytes()
    independent_source_sha256 = _sha256(independent_raw)
    independent_module = importlib.import_module(
        "heterodiff.evaluation.b12_whole_method_nonconfirmatory_recomputation"
    )
    if type(independent_module) is not ModuleType:
        raise WholeMethodNonconfirmatoryError("independent module import differs")
    if Path(independent_module.__file__).resolve(strict=True) != independent_path:
        raise WholeMethodNonconfirmatoryError("independent module path differs")
    independent_bytes = independent_module.independently_recompute_whole_method(
        project_root, input_bytes
    )
    if type(independent_bytes) is not bytes or independent_bytes != core_bytes:
        raise WholeMethodNonconfirmatoryError("independent recomputation differs")

    ledger = _ledger_pair(input_bytes, core_bytes)
    execution_subject = integration.compute_execution_subject_v3(
        capsule.receipt, adapter_binding, ledger, None
    )
    output_pair = integration.BoundOutputPair(
        binding_document_bytes=input_bytes,
        candidate_output_bytes=core_bytes,
        independent_output_bytes=independent_bytes,
        candidate_output_sha256=core_sha256,
        independent_output_sha256=_sha256(independent_bytes),
        independent_implementation_sha256=independent_source_sha256,
    )
    output_pair.validate()
    recomputation = integration.build_recomputation_receipt(
        execution_subject,
        output_pair,
        _qualification_authentication("RECOMPUTATION"),
    )
    runner = integration.build_open_integrated_runner_exercise(
        capsule.receipt, adapter_binding, ledger, recomputation
    )
    status = runner.status()
    if status["residual_receipts_missing"] != 50 or status["science_executed"]:
        raise WholeMethodNonconfirmatoryError("open runner boundary differs")
    runner_subject = integration.compute_runner_subject_v3(
        capsule.receipt, adapter_binding, ledger, recomputation, None
    )
    payload = {
        "adapter_manifest_sha256": adapter_binding.manifest_sha256,
        "capsule_manifest_sha256": capsule.receipt.manifest_sha256,
        "core_output_sha256": core_sha256,
        "implementation_obligations_exercised": list(
            IMPLEMENTATION_OBLIGATIONS_EXERCISED
        ),
        "independent_implementation_sha256": independent_source_sha256,
        "independent_output_sha256": _sha256(independent_bytes),
        "ledger_event_sha256s": [event.event_sha256 for event in ledger],
        "open_residual_predicate_ids": list(REAL_RESIDUAL_IDS),
        "runner_subject_sha256": runner_subject,
        "schema_version": RECEIPT_SCHEMA,
        "state": STATE,
        "supplied_input_sha256": supplied_input.input_sha256,
    }
    receipt = WholeMethodNonconfirmatoryReceipt(
        schema_version=RECEIPT_SCHEMA,
        state=STATE,
        supplied_input_sha256=supplied_input.input_sha256,
        core_output_sha256=core_sha256,
        independent_output_sha256=_sha256(independent_bytes),
        independent_implementation_sha256=independent_source_sha256,
        capsule_manifest_sha256=capsule.receipt.manifest_sha256,
        adapter_manifest_sha256=adapter_binding.manifest_sha256,
        ledger_event_sha256s=tuple(event.event_sha256 for event in ledger),
        open_residual_predicate_ids=REAL_RESIDUAL_IDS,
        runner_subject_sha256=runner_subject,
        implementation_obligations_exercised=IMPLEMENTATION_OBLIGATIONS_EXERCISED,
        receipt_sha256=_domain_sha256(RECEIPT_DOMAIN, payload),
    )
    return validate_whole_method_nonconfirmatory_receipt(receipt)


__all__ = [
    "CAPSULE_SOURCE_PATHS",
    "CORE_OUTPUT_SCHEMA",
    "IMPLEMENTATION_OBLIGATIONS_EXERCISED",
    "INPUT_SCHEMA",
    "REAL_RESIDUAL_IDS",
    "RECEIPT_SCHEMA",
    "SCHEMA_VERSION",
    "STATE",
    "SuppliedNonconfirmatoryInput",
    "WholeMethodNonconfirmatoryError",
    "WholeMethodNonconfirmatoryReceipt",
    "build_frozen_nonconfirmatory_input",
    "receipt_canonical_json_bytes",
    "run_supplied_nonconfirmatory_whole_method",
    "supplied_input_canonical_json_bytes",
    "validate_whole_method_nonconfirmatory_receipt",
]
