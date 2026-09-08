"""Draft arithmetic for checkpoint validation and paired-population work.

No frozen record is changed. Logical draws, score calls and sample-path steps
are not GPU launches, FLOPs, wall time, monetary cost or measured throughput.
The primary-pair ceiling proposal preserves the old B06 envelope and adds an
explicit validation allowance using B06's existing inference-event convention.
Its adoption and the runtime-specific event mapping remain separate decisions.
The additional classifier nuisance and raw observation encoder are not silently
included in the historical base+conditioner parameter counts or event weights.
The separate joint/product population workload is not included in the numeric
old-plus-validation envelope. That envelope is not a complete training budget.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from heterodiff.experiments import two_domain_baseline_registry as b06
from heterodiff.experiments import two_domain_training_checkpoint_plan as training
from heterodiff.experiments.matched_total_compute import PHASES, RESOURCE_EVENTS


SCHEMA_VERSION = "heterodiff-two-domain-compute-budget-amendment-draft-v1"
STATE = "DRAFT_ARITHMETIC_PROPOSAL_REQUIRES_REVIEW_AND_ADOPTION"


class BudgetAmendmentError(ValueError):
    """A requested row or an inherited workload contract is not supported."""


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def _positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise BudgetAmendmentError(name + " must be a positive integer")
    return value


def _configuration(method_id, domain_id):
    if type(method_id) is not str or type(domain_id) is not str:
        raise BudgetAmendmentError("method_id and domain_id must be strings")
    rows = [row for row in training.executable_configuration_rows()
            if (row["method_id"], row["domain_id"]) == (method_id, domain_id)]
    if len(rows) != 1:
        raise BudgetAmendmentError("Unknown or ambiguous frozen method/domain")
    return rows[0]


def _count(value, name):
    if type(value) is not int or value < 0:
        raise BudgetAmendmentError(name + " must be a nonnegative integer")
    return value


def method_operation_mapping(method_id, domain_id):
    """Resolve declared components without turning static adapters into models."""
    row = _configuration(method_id, domain_id)
    kind = row["registry_kind"]
    result = {
        "registry_kind": kind,
        "method_id": method_id,
        "domain_id": domain_id,
        "config_sha256": row["b06_config_sha256"],
        "actual_nonprimary_sampler_steps": None,
        "upstream_defaults_are_adopted_runtime_settings": False,
        "free_cross_role_reuse_or_deduplication_claimed": False,
        "frozen_schedule_changed": False,
    }
    if kind == "PRIMARY":
        result.update(
            implementation_status="ADDITIVE_LOCAL_PRIMARY_PIPELINE_NOT_PRODUCTION_QUALIFIED",
            declared_learned_conditioner_target=True,
            removed_components=[],
            source_interface="heterodiff.experiments.hybrid_conditional_training:ObservedConditionalTrainingModel",
            remaining_mechanism_decision="REVIEW_REAL_DOMAIN_SCHEMA_LAW_AND_NUMERICAL_SAMPLER_SUCCESSOR",
        )
    elif kind == "CONTROL":
        config = next(c["config"] for c in b06.FROZEN_REGISTRY["controls"] if c["control_id"] == method_id)
        active = config["mode"]["active_components"]
        learned = any(c in active for c in ("LEARNED_RESIDUAL", "FACTORIZED_EVENTWISE_CONDITIONER"))
        result.update(
            implementation_status="STATIC_CONTROL_COMPONENT_CONTRACT_NOT_EXECUTABLE_TRAINING_OR_SAMPLING",
            declared_learned_conditioner_target=learned,
            active_components=deepcopy(active),
            removed_components=deepcopy(config["mode"]["removed_components"]),
            source_interface=config["implementation"],
            remaining_mechanism_decision=(
                "IMPLEMENT_DECLARED_CONTROL_AND_MAP_ITS_ACTUAL_OPERATIONS" if learned else
                "REVIEW_INHERITED_OPTIMIZER_AND_CHECKPOINT_SCHEDULE_FOR_CONTROL_WITHOUT_LEARNED_TARGET"
            ),
        )
    elif kind == "LITERATURE_FAMILY":
        config = next(f["configs_by_domain"][domain_id] for f in b06.FROZEN_REGISTRY["literature_families"]
                      if f["implementation_by_domain"][domain_id]["implementation_id"] == method_id)
        result.update(
            implementation_status="STATIC_MATERIALIZED_DRAW_CONTRACT_NOT_EXECUTABLE_FAMILY_ALGORITHM",
            declared_learned_conditioner_target=None,
            family_id=config["family_id"],
            source_interface=config["source_interface"],
            objective=config["objective"],
            task_interface=config["task_interface"],
            remaining_mechanism_decision="IMPLEMENT_FAMILY_OPTIMIZER_POPULATION_AND_SAMPLER_MECHANISM",
        )
    else:
        config = next(e["config"] for e in b06.FROZEN_REGISTRY["external_baselines"]
                      if (e["method_id"], e["domain_id"]) == (method_id, domain_id))
        result.update(
            implementation_status="STATIC_EXTERNAL_IDENTITY_AND_AUTHOR_EXTENSION_BOUNDARY_NOT_MODEL_EXECUTION",
            declared_learned_conditioner_target=None,
            source_interface=config["source_interface"],
            frozen_upstream_defaults=deepcopy(config["upstream_defaults"]),
            author_extensions=deepcopy(config["author_extensions"]),
            remaining_mechanism_decision="CONNECT_PINNED_EXTERNAL_MODEL_AND_DECLARED_EXTENSIONS_THEN_MAP_OPERATIONS",
        )
    return result


def hybrid_sampler_operation_counts(*, completed_paths, active_intervals, held_intervals,
                                    nonempty_heun_halfsteps, jump_candidates,
                                    waiting_time_draws, accepted_jumps,
                                    zero_intensity_terminations=None):
    """Successful-path call arithmetic, conditional on supplied aggregate counts.

This does not execute or authenticate a trajectory. A macrointerval is not a
potential query. Zero intensity and finite-addition termination make C+A an
upper bound, not an exact universal intensity-preflight count.
"""
    values = (completed_paths, active_intervals, held_intervals, nonempty_heun_halfsteps,
              jump_candidates, waiting_time_draws, accepted_jumps)
    for value in values:
        _count(value, "sampler count")
    p, a, h, e, c, w, j = values
    if (e > 2*a or j > c or not c <= w <= c+a
            or (p == 0 and any(values[1:])) or (p and a+h < p)
            or (a == 0 and (e or c or w or j))):
        raise BudgetAmendmentError("inconsistent successful-path counters")
    preflights = None
    if zero_intensity_terminations is not None:
        z = _count(zero_intensity_terminations, "zero_intensity_terminations")
        if w-c+z > a:
            raise BudgetAmendmentError("too many terminal intensity/clock checks")
        preflights = w+z
    return {
        "scope": "SUCCESSFUL_LOCAL_HYBRID_PATH_CALL_ARITHMETIC_NOT_EXECUTION_EVIDENCE",
        "complete_paths": p, "actual_macrointervals": a+h,
        "active_macrointervals": a, "held_macrointervals": h,
        "initializer_callback_calls": p,
        "heun_halfstep_calls": 2*a,
        "nonempty_heun_halfsteps": e,
        "physical_value_grad_calls": 2*e,
        "physical_value_grad_call_upper_bound": 4*a,
        "jump_substep_calls": a,
        "physical_value_calls": w+c,
        "candidate_draw_calls": c, "acceptance_uniform_draws": c,
        "waiting_time_draws": w, "accepted_jumps": j, "rejected_jumps": c-j,
        "reference_intensity_preflight_calls": preflights,
        "reference_intensity_preflight_lower_bound": w,
        "reference_intensity_preflight_upper_bound": c+a,
        "path_rng_stream_requests_excluding_observation_callback": p+2*a+w+2*c,
        "normal_scalar_draws_and_coordinate_arithmetic": None,
        "reference_candidate_internal_work": None,
        "failed_or_partial_execution_work_covered": False,
        "f104_weights_or_budget_ceiling_assigned": False,
    }


def hybrid_grid_workload(*, complete_paths, nominal_intervals, query_refined_paths):
    """Each current explicit query refinement adds exactly one interval/path."""
    paths = _count(complete_paths, "complete_paths")
    intervals = _positive_int(nominal_intervals, "nominal_intervals")
    refined = _count(query_refined_paths, "query_refined_paths")
    if refined > paths or intervals > 10000 or (refined and intervals == 10000):
        raise BudgetAmendmentError("query refinement exceeds path count or local grid limit")
    return {
        "nominal_macrointervals": paths*intervals,
        "additional_query_refinement_intervals": refined,
        "actual_macrointervals_for_supplied_refinement_count": paths*intervals+refined,
        "active_and_held_interval_partition": None,
        "frozen_numerical_law_preserved_by_refinement": False,
        "refinement_adopted_or_execution_observed": False,
    }


def neural_potential_operation_counts(*, value_calls, value_grad_calls,
                                     include_base, conditional,
                                     active_conditional_queries=None):
    """Call decomposition for the current uncached TorchHybridPotential."""
    v = _count(value_calls, "value_calls")
    g = _count(value_grad_calls, "value_grad_calls")
    if type(include_base) is not bool or type(conditional) is not bool or not (include_base or conditional):
        raise BudgetAmendmentError("explicit supported potential role required")
    queries = v+g
    if active_conditional_queries is not None:
        _count(active_conditional_queries, "active_conditional_queries")
        if active_conditional_queries > queries or (not conditional and active_conditional_queries):
            raise BudgetAmendmentError("active conditional queries exceed role/count")
    return {
        "scope": "CURRENT_TORCH_HYBRID_POTENTIAL_CALLBACK_STRUCTURE_NOT_GPU_OR_F104_UNITS",
        "total_scalar_potential_queries": queries,
        "base_forward_calls": queries if include_base else 0,
        "baseline_callback_calls": queries if conditional else 0,
        "condition_observation_encoder_calls": queries if conditional else 0,
        "conditional_backbone_forward_calls": active_conditional_queries if conditional else 0,
        "conditional_backbone_forward_upper_bound": queries if conditional else 0,
        "nuisance_forward_calls": 0,
        "coordinate_autograd_requests_upper_bound": g,
        "actual_coordinate_autograd_requests": None,
        "baseline_internal_value_and_derivative_work": None,
        "parameter_training_backward_calls": 0,
        "encoder_caching_or_free_reuse_assumed": False,
    }


def conditional_rejection_workload(*, completed_draws, max_proposals_per_draw,
                                   proposal_counts=None):
    """Conditional Pi_N rejection only; caller supplies, not adopts, a cap."""
    n = _count(completed_draws, "completed_draws")
    cap = _positive_int(max_proposals_per_draw, "max_proposals_per_draw")
    if cap > 100000:
        raise BudgetAmendmentError("proposal cap exceeds local initializer implementation limit")
    total = None
    if proposal_counts is not None:
        if type(proposal_counts) is not tuple or len(proposal_counts) != n:
            raise BudgetAmendmentError("one exact proposal count per completed draw required")
        for count in proposal_counts:
            if not 1 <= _count(count, "proposal count") <= cap:
                raise BudgetAmendmentError("proposal count outside supplied cap")
        total = sum(proposal_counts)
    return {
        "completed_draws": n, "caller_supplied_local_proposal_cap": cap,
        "proposal_count_lower_bound": n, "proposal_count_upper_bound": n*cap,
        "actual_reference_configuration_calls": total,
        "actual_initial_factor_value_calls": total,
        "actual_acceptance_uniform_draws": total,
        "base_potential_calls": 0, "nuisance_calls": 0,
        "expected_rejection_proposals": None,
        "internal_reference_proposal_generation_work": None,
        "failed_draw_work_covered": False,
        "cap_adopted_for_science_or_spend": False,
    }


def observation_design_operation_counts(*, anchor_dimension, global_dimension,
                                       batch_size, joint_anchor_count, product_anchor_count):
    """Exact dense shapes for two condition encoders plus two nuisance passes.

MAC terms are scalar dot-product multiply-accumulates, not a calibrated cost
or all FLOPs. No raw data/model is read and no schema is adopted here.
"""
    a = _positive_int(anchor_dimension, "anchor_dimension")
    d = _positive_int(global_dimension, "global_dimension")
    b = _positive_int(batch_size, "batch_size")
    anchors = _count(joint_anchor_count, "joint_anchor_count") + _count(product_anchor_count, "product_anchor_count")
    encoder_parameters = 64*(a+64+d)+8448
    encoder_macs = anchors*(64*a+4096) + 2*b*(64*(64+d)+4096)
    return {
        "scope": "CURRENT_OBSERVATION_DESIGN_PAIRED_BATCH_DENSE_ARITHMETIC_NOT_F104_OR_FLOPS",
        "condition_encoder_forward_passes": 2,
        "nuisance_forward_passes": 2,
        "nuisance_encoder_forward_passes": 2,
        "all_encoder_dense_layer_calls": 16,
        "nuisance_head_dense_layer_calls": 4,
        "all_encoder_dense_mac_terms": 2*encoder_macs,
        "nuisance_head_dense_mac_terms": 2*b*(64*32+32),
        "all_encoder_dense_bias_additions_and_tanh_elements_each": 2*(128*anchors+256*b),
        "nuisance_head_bias_additions": 2*b*33,
        "nuisance_head_tanh_elements": 2*b*32,
        "pooling_input_elements": 2*64*anchors,
        "pooling_normalization_divisions": 4*b*64,
        "unique_condition_encoder_parameters": encoder_parameters,
        "unique_nuisance_encoder_parameters": encoder_parameters,
        "unique_nuisance_head_parameters": 2113,
        "additional_unique_parameters": 2*encoder_parameters+2113,
        "historical_internal_context_mlp_counted_again": False,
        "tensorization_validation_sorting_and_reduction_algorithm_work": None,
        "gradient_and_optimizer_scalar_work": None,
        "production_schema_or_parameter_successor_adopted": False,
    }


def f105_symbolic_work_from_cardinalities(draw_counts, target_count):
    """Actual factory's event-pair loop count for one R64 score, not execution."""
    if type(draw_counts) is not tuple or len(draw_counts) != 64:
        raise BudgetAmendmentError("exact R64 draw-cardinality tuple required")
    for count in draw_counts:
        _count(count, "draw cardinality")
    target = _count(target_count, "target cardinality")
    total, squares = sum(draw_counts), sum(n*n for n in draw_counts)
    return {
        "configuration_kernel_calls": 2080,
        "symbolic_event_pair_work_units": 64*squares + 64*target*target + (total*total-squares)//2 + target*total,
        "coordinate_dimension_and_exact_rational_bit_work": None,
        "factory_score_evaluated": False,
        "f104_metric_weight_or_work_ceiling_assigned": False,
    }


def overflow_observation_wrapper_counts(*, batch_size, encoder_forward_passes):
    """Separate proposed two-independent-wrapper addition; V1 is unchanged.

Each wrapper evaluates its retained encoder on all rows, concatenates the
overflow bit, then applies a 65->64 affine map and tanh. These counters cover
only that added map, not the retained encoder or nuisance head.
"""
    batch = _positive_int(batch_size, "batch_size")
    passes = _count(encoder_forward_passes, "encoder_forward_passes")
    return {
        "scope": "SEPARATE_OVERFLOW_ENCODER_SUCCESSOR_PROPOSAL_ADDITION_ONLY",
        "unique_parameters_per_wrapper": 4224,
        "two_independent_wrappers_unique_parameter_addition": 8448,
        "additional_dense_layer_calls": passes,
        "additional_dense_mac_terms": passes*batch*65*64,
        "additional_bias_additions": passes*batch*64,
        "additional_tanh_elements": passes*batch*64,
        "retained_encoder_work_avoided_for_overflow_rows": False,
        "nuisance_automatically_added_to_physical_potential": False,
        "production_design_adopted": False,
    }


def _primary_config(method_id, domain_id):
    for method in b06.FROZEN_REGISTRY["primary_pair"]:
        if method["method_id"] == method_id:
            return method["config"]["domain_configs"][domain_id]
    return None


def _checkpoint_steps(update_limit, cadence):
    _positive_int(update_limit, "update_limit")
    _positive_int(cadence, "cadence")
    steps = list(range(cadence, update_limit + 1, cadence))
    if not steps or steps[-1] != update_limit:
        steps.append(update_limit)
    return steps


def _validation_work(checkpoint_count, replicas, groups, draws, reverse_steps):
    score_calls = checkpoint_count * replicas * groups
    draw_count = score_calls * draws
    return {
        "checkpoint_validation_passes": checkpoint_count * replicas,
        "group_score_calls": score_calls,
        "generated_conditional_draws": draw_count,
        "reverse_steps_per_draw": reverse_steps,
        "logical_reverse_sample_path_steps": (
            None if reverse_steps is None else draw_count * reverse_steps
        ),
        # Distinct configuration-pair evaluations for one F105 score; actual
        # event-pair work also depends on configuration cardinalities.
        "cks_unique_configuration_pair_evaluations": (
            score_calls * (draws * (draws - 1) // 2 + draws)
        ),
        "actual_cks_symbolic_event_pair_work": None,
        "actual_model_forward_calls": None,
        "gpu_kernel_launches": None,
    }


def _population_generation_work(updates, batch_size, replicas, reverse_steps):
    record_count = updates * batch_size * replicas
    trajectories = 2 * record_count
    return {
        "scheduled_optimizer_updates": updates * replicas,
        "logical_training_examples": record_count,
        "complete_learned_base_trajectories": trajectories,
        "nominal_reverse_sample_path_steps": trajectories * reverse_steps,
    }


def _joint_product_population_work(primary, batch_size, final_updates,
                                   tuning_updates, trials, seeds, reverse_steps):
    """Count fresh two-branch construction, never infer a control's algorithm."""
    applicable = primary is not None
    return {
        "scope": "CONDITIONAL_PRIMARY_FRESH_TWO_BRANCH_POPULATION_WORKLOAD_NOT_F104_EVENTS",
        "source_function": (
            "heterodiff.processes.learned_hybrid_training_sampler:"
            "LearnedHybridTrainingSampler.sample_pair"
        ),
        "condition": "ONE_FRESH_JOINT_PRODUCT_PAIR_PER_LOGICAL_TRAINING_EXAMPLE",
        "primary_pair_workload_applicability": applicable,
        "nonprimary_or_control_applicability_inferred": False,
        "complete_learned_base_trajectories_per_training_example": 2 if applicable else None,
        "branches_share_task_context_and_query_time": True if applicable else None,
        "branch_random_streams_are_separate": True if applicable else None,
        "nominal_reverse_steps_per_complete_trajectory": reverse_steps,
        "per_optimizer_update": (
            _population_generation_work(1, batch_size, 1, reverse_steps) if applicable else None
        ),
        "per_final_training_seed": (
            _population_generation_work(final_updates, batch_size, 1, reverse_steps)
            if applicable else None
        ),
        "complete_final_training_seed_roster": (
            _population_generation_work(final_updates, batch_size, seeds, reverse_steps)
            if applicable else None
        ),
        "tuning_trial_roster_at_cap": (
            _population_generation_work(tuning_updates, batch_size, trials, reverse_steps)
            if applicable else None
        ),
        "tuning_scope": "ONE_F147_TRIAL_ROSTER_NOT_MULTIPLIED_BY_FINAL_TRAINING_SEEDS",
        "reference_initializer_and_observation_callback_calls_each": ({
            "per_optimizer_update": 2*batch_size,
            "per_final_training_seed": 2*batch_size*final_updates,
            "complete_final_training_seed_roster": 2*batch_size*final_updates*seeds,
            "tuning_trial_roster_at_cap": 2*batch_size*tuning_updates*trials,
        } if applicable else None),
        "population_callback_count_unit": "ONE_CALLBACK_PER_COMPLETE_BRANCH_NOT_INTERNAL_RNG_OR_MODEL_WORK",
        "population_work_is_separate_from_checkpoint_validation": True,
        "reuse_or_free_population_construction_claimed": False,
        "query_refinement_may_increase_actual_grid_interval_count": True,
        "actual_query_refined_grid_intervals": None,
        "actual_active_substeps_rejection_thinning_and_oracle_calls": None,
        "actual_initializer_and_observation_kernel_work": None,
        "actual_encoder_classifier_nuisance_and_backprop_work": None,
        "f104_population_event_mapping": None,
        "numeric_population_event_allowance": None,
        "nominal_steps_are_model_calls_or_gpu_launches": False,
        "actual_execution_or_production_law_qualification_claimed": False,
    }


def training_run_workload(method_id, domain_id):
    """Return the inherited schedule for one method/domain and its full roster.

All 22 configuration rows retain their scheduled obligations. For controls or
external/family adapters this does not assert that optimizer/sampler behavior
is implemented or that the primary sampler's 256 steps apply to that adapter.
"""
    config = _configuration(method_id, domain_id)
    primary = _primary_config(method_id, domain_id)
    validation = training.validation_metric_value()
    batch_size = training.batch_construction_value()["b06_data_adapter_records_per_optimizer_update"]
    final_updates = config["f143_completed_optimizer_update_bound"]
    tuning_updates = config["tuning_updates_per_trial"]
    trials = config["tuning_maximum_trials"]
    cadence = validation["checkpoint_cadence"]["every_completed_optimizer_updates"]
    groups = validation["f134_validation_group_count"]
    draws = validation["draw_count_per_group"]
    seeds = b06.TRAINING_SEED_COUNT
    values = (batch_size, final_updates, tuning_updates, trials, cadence, groups, draws, seeds)
    for value in values:
        _positive_int(value, "inherited workload")
    if validation["checkpoint_cadence"]["terminal_f143_bound_included"] is not True:
        raise BudgetAmendmentError("Terminal validation must be included")
    reverse_steps = None if primary is None else primary["base"]["reverse_steps"]
    if reverse_steps is not None:
        _positive_int(reverse_steps, "reverse_steps")
    final_checkpoints = _checkpoint_steps(final_updates, cadence)
    tuning_checkpoints = _checkpoint_steps(tuning_updates, cadence)
    return {
        "method_id": method_id, "domain_id": domain_id,
        "registry_kind": config["registry_kind"],
        "declared_operation_mapping": method_operation_mapping(method_id, domain_id),
        "b06_config_sha256": config["b06_config_sha256"],
        "cpu_predecessor_configuration_sha256": config["executable_configuration_sha256"],
        "f144_semantics_sha256": config["f144_semantics_sha256"],
        "batch_size": batch_size, "final_updates_per_seed": final_updates,
        "final_checkpoint_update_indices": final_checkpoints,
        "groups_per_validation_pass": groups, "draws_per_group": draws,
        "training_seed_count": seeds,
        "joint_product_population_generation": _joint_product_population_work(
            primary, batch_size, final_updates, tuning_updates, trials, seeds, reverse_steps
        ),
        "per_seed_final_validation": _validation_work(len(final_checkpoints), 1, groups, draws, reverse_steps),
        "final_training_roster": {
            "scheduled_seed_count": seeds,
            "scheduled_optimizer_updates": seeds * final_updates,
            "logical_training_record_visits": seeds * final_updates * batch_size,
            "validation": _validation_work(len(final_checkpoints), seeds, groups, draws, reverse_steps),
        },
        "tuning": {
            "maximum_trials": trials,
            "updates_per_trial": tuning_updates,
            "checkpoint_update_indices_per_trial": tuning_checkpoints,
            "scheduled_optimizer_updates_at_trial_cap": trials * tuning_updates,
            "logical_training_record_visits_at_trial_cap": trials * tuning_updates * batch_size,
            "validation_at_trial_cap": _validation_work(len(tuning_checkpoints), trials, groups, draws, reverse_steps),
            "scope": "ONE_F147_TRIAL_ROSTER_NOT_MULTIPLIED_BY_FINAL_TRAINING_SEEDS",
        },
        "confirmatory_inference": _validation_work(1, seeds, groups, draws, reverse_steps),
        "pilot_empirical_runs": 0, "additional_failure_reserve_runs": 0,
        "failed_attempts_charged": True, "retry_or_replacement_permitted": False,
        "sampler_step_mapping": "PRIMARY_B06_256_STEP_CONVENTION" if primary else "NONPRIMARY_RUNTIME_MAPPING_UNRESOLVED",
        "optimizer_applicability_for_removed_component_controls_verified": False,
        "gpu_precision_or_numerical_equivalence_inferred": False,
        "measured_work_or_scientific_execution": False,
    }


def _validation_event_allowance(domain_id, group_score_calls):
    """Scale the old B06 per-group inference convention, not measured calls."""
    inference = b06.inference_compute_budget(domain_id)["phase_event_count_ceilings"]["CONFIRMATORY_INFERENCE"]
    original_group_calls = b06.TRAINING_SEED_COUNT * b06.NATURAL_GROUP_COUNT * b06.CONDITIONING_CASES_PER_GROUP
    result = {}
    for event in RESOURCE_EVENTS:
        scaled, remainder = divmod(inference[event] * group_score_calls, original_group_calls)
        if remainder:
            raise BudgetAmendmentError("B06 per-group event convention is not integral")
        result[event] = scaled
    return result


def _conditional_training_accounting(method_id, domain_id, workload):
    """Keep known call structure separate from an unchosen production ledger.

This is arithmetic on the existing schedule, not a model import, execution,
parameter measurement, or proof of a codec/generator's law. Calls refer to the
current two-class implementation when used once per optimizer update; they
are not F104 units, per-example counts, FLOPs, GPU launches or F157 ceilings.
"""
    base = _primary_config(method_id, domain_id)["base"]
    context_parameters = (
        (base["context_dimension"] + 1) * base["context_hidden_width"]
        + base["context_hidden_width"]
        + base["context_hidden_width"] * base["context_embedding_width"]
        + base["context_embedding_width"]
    )
    primary = method_id == b06.PRIMARY_METHOD_ID
    return {
        "state": "PROSPECTIVE_CLASSIFIER_AND_ENCODER_ACCOUNTING_UNRESOLVED",
        "historical_base_and_conditioner_parameter_counts": b06.primary_parameter_count(domain_id),
        "already_counted_internal_context_mlp_parameters_per_module": context_parameters,
        "internal_context_mlp_already_in_both_base_and_conditioner_counts": True,
        "raw_observation_task_context_feature_encoder_is_the_counted_internal_mlp": False,
        "additional_unique_nuisance_parameters": None,
        "additional_unique_raw_encoder_parameters": None,
        "successor_unique_parameter_total": None,
        "successor_frozen_and_trainable_parameter_partition": None,
        "unique_parameter_counting_rule": (
            "HISTORICAL_BASE_PLUS_CONDITIONER_PLUS_UNIQUE_ADDITIONAL_NUISANCE_"
            "AND_RAW_ENCODER_PARAMETERS_WITHOUT_DOUBLE_COUNTING"
        ),
        "required_prospective_configuration_and_parameter_fields": (
            ["F064", "F065"] if primary else ["F070", "F071"]
        ),
        "historical_configuration_or_parameter_fields_changed": False,
        "prospective_configuration_or_parameter_successor_adopted": False,
        "primary_pair_parameter_matching_reverified": False,
        "implementation_call_structure_not_f104_event_counts": {
            "source_function": (
                "heterodiff.models.two_domain_conditional_training_loss:"
                "equal_prior_joint_product_loss"
            ),
            "condition": "ONE_CURRENT_PAIRED_LOSS_CALL_PER_SCHEDULED_OPTIMIZER_UPDATE",
            "call_count_unit": "BATCHED_FORWARD_PASS_NOT_PER_RECORD_EVALUATION",
            "logical_examples_per_class_forward_pass": workload["batch_size"],
            "logical_classifier_evaluations_per_update": 2 * workload["batch_size"],
            "logical_nuisance_evaluations_per_update": 2 * workload["batch_size"],
            "classifier_calls_per_update": 2,
            "nuisance_calls_per_update": 2,
            "backbone_calls_per_valid_shared_time_update": [0, 2],
            "clean_hold_may_skip_backbone_but_not_nuisance": True,
            "classifier_calls_per_final_training_seed": 2 * workload["final_updates_per_seed"],
            "nuisance_calls_per_final_training_seed": 2 * workload["final_updates_per_seed"],
            "classifier_calls_complete_final_seed_roster": (
                2 * workload["final_training_roster"]["scheduled_optimizer_updates"]
            ),
            "nuisance_calls_complete_final_seed_roster": (
                2 * workload["final_training_roster"]["scheduled_optimizer_updates"]
            ),
            "classifier_calls_tuning_trial_roster": (
                2 * workload["tuning"]["scheduled_optimizer_updates_at_trial_cap"]
            ),
            "nuisance_calls_tuning_trial_roster": (
                2 * workload["tuning"]["scheduled_optimizer_updates_at_trial_cap"]
            ),
            "nuisance_excluded_from_current_physical_potential_surface": True,
            "nuisance_charged_automatically_per_reverse_step": False,
            "actual_execution_observed": False,
        },
        "observed_model_pair_call_structure": {
            "source_function": "heterodiff.experiments.hybrid_conditional_training:observed_joint_product_loss",
            "condition": "ONE_VALID_OBSERVED_PAIR_LOSS_PER_COMPLETED_OPTIMIZER_UPDATE",
            "condition_observation_encoder_passes_per_update": 2,
            "nuisance_encoder_passes_per_update": 2,
            "nuisance_head_passes_per_update": 2,
            "condition_encoder_is_evaluated_even_when_all_records_are_in_clean_hold": True,
            "optimizer_zero_grad_calls_per_update": 1,
            "loss_backward_calls_per_update": 1,
            "adamw_step_calls_per_update": 1,
            "backward_calls_are_not_f104_backwards_or_scalar_gradient_operation_counts": True,
            "concrete_schema_dimensions_required_for_additional_unique_parameter_count": True,
            "parameter_formula": "2*(64*(anchor_dimension+64+global_dimension)+8448)+2113",
        },
        "classifier_nuisance_forward_backward_f104_event_mapping": None,
        "raw_encoder_feature_preprocessing_f104_event_mapping": None,
        "old_one_conditioner_forward_per_update_allowance_sufficient": None,
        "f104_weights_or_scalar_cost_inferred_from_calls": False,
        "f157_aggregate_ceiling_inferred_from_calls": False,
        "all_additional_operations_must_be_prospectively_declared_and_charged": True,
        "other_declared_operation_numeric_allowance_chosen": False,
    }


def proposed_primary_phase_ceiling(method_id, domain_id):
    """Propose equal primary-pair F104 event envelopes with validation added.

The preserved base envelope is not reinterpreted as realized use. In
particular, its eight-trial resource opportunity does not enlarge F147's
one-trial primary schedule. New guide allowance is equally available to both
primary methods even when one does not consume an analytic-guide operation.
"""
    workload = training_run_workload(method_id, domain_id)
    if workload["registry_kind"] != "PRIMARY":
        raise BudgetAmendmentError("Only primary-pair event mappings are proposed")
    old_training = b06.training_compute_budget(domain_id)["phase_event_count_ceilings"]
    old_inference = b06.inference_compute_budget(domain_id)["phase_event_count_ceilings"]
    original = {phase: {event: old_training[phase][event] + old_inference[phase][event]
                        for event in RESOURCE_EVENTS} for phase in PHASES}
    additions = {phase: {event: 0 for event in RESOURCE_EVENTS} for phase in PHASES}
    additions["TUNING"] = _validation_event_allowance(domain_id, workload["tuning"]["validation_at_trial_cap"]["group_score_calls"])
    additions["FINAL_TRAINING"] = _validation_event_allowance(domain_id, workload["final_training_roster"]["validation"]["group_score_calls"])
    proposed = {phase: {event: original[phase][event] + additions[phase][event]
                        for event in RESOURCE_EVENTS} for phase in PHASES}
    return {
        "method_id": method_id, "domain_id": domain_id,
        "state": STATE,
        "original_combined_phase_event_envelope": original,
        "additional_checkpoint_validation_allowance": additions,
        "proposed_combined_phase_event_ceiling": proposed,
        "proposed_event_ceiling_scope": "ORIGINAL_PLUS_CHECKPOINT_VALIDATION_ONLY_NOT_FULL_TRAINING",
        "joint_product_population_generation": workload["joint_product_population_generation"],
        "population_work_mapped_into_proposed_event_ceiling": False,
        "complete_training_budget_qualification_claimed": False,
        "validation_metric_convention": "B06_R64_SQUARED_RESOURCE_ALLOWANCE_NOT_ACTUAL_EVENT_PAIR_WORK",
        "validation_sampling_convention": "B06_LOGICAL_PER_DRAW_EVENT_ALLOWANCE_NOT_BATCHED_GPU_CALL_COUNT",
        "all_original_allowances_preserved": True,
        "equal_primary_pair_prospective_opportunity_required": True,
        "f147_trial_limit_unchanged": workload["tuning"]["maximum_trials"],
        "conditional_training_accounting": _conditional_training_accounting(method_id, domain_id, workload),
        "weights": None, "scalar_ceiling": None,
        "wall_seconds": None, "gpu_hours": None, "peak_host_bytes": None,
        "peak_device_bytes": None, "storage_bytes": None,
        "f157_aggregate_model_evaluation_ceiling": None,
        "parameter_count_hard_axis_ceiling": None,
        "approved_for_execution_or_spend": False,
    }


def build_budget_amendment():
    """Build a detached draft report; no file, data, device or model access."""
    configs = training.executable_configuration_rows()
    rows = [training_run_workload(row["method_id"], row["domain_id"]) for row in configs]
    proposals = [proposed_primary_phase_ceiling(row["method_id"], row["domain_id"])
                 for row in configs if row["registry_kind"] == "PRIMARY"]
    if len(rows) != 22 or len(proposals) != 4:
        raise BudgetAmendmentError("Expected 22 configuration rows and four primary rows")
    for domain in b06.DOMAIN_IDS:
        pair = [row for row in proposals if row["domain_id"] == domain]
        if len(pair) != 2 or pair[0]["proposed_combined_phase_event_ceiling"] != pair[1]["proposed_combined_phase_event_ceiling"]:
            raise BudgetAmendmentError("Primary-pair prospective equality failed")
    body = {
        "schema_version": SCHEMA_VERSION, "state": STATE,
        "source_semantics": {
            "b06_registry_canonical_sha256": _digest(b06.FROZEN_REGISTRY),
            "training_plan_semantic_sha256": training.plan_semantics_sha256(),
            "f144_semantics_sha256": training.f144_semantics_sha256(),
            "bindings_are_content_identities_not_execution_receipts": True,
        },
        "method_domain_workloads": rows,
        "primary_pair_ceiling_proposals": proposals,
        "tuning_trial_count_across_all_rows": sum(row["tuning"]["maximum_trials"] for row in rows),
        "scheduled_final_seed_runs_across_all_rows": len(rows) * b06.TRAINING_SEED_COUNT,
        "role_rows_deduplicated_or_free_compute_claimed": False,
        "symbolic_operation_ledger": {
            "explicit_query_refinement": "hybrid_grid_workload",
            "successful_hybrid_paths": "hybrid_sampler_operation_counts",
            "physical_neural_callbacks": "neural_potential_operation_counts",
            "conditional_initializer": "conditional_rejection_workload",
            "paired_observation_encoders_and_nuisance": "observation_design_operation_counts",
            "separate_overflow_encoder_successor_addition": "overflow_observation_wrapper_counts",
            "f105_cardinality_dependent_event_pair_work": "f105_symbolic_work_from_cardinalities",
            "scope": "PURE_FORMULAS_REQUIRE_DECLARED_OR_OBSERVED_COUNTS_NOT_MEASURED_BUDGETS",
            "all22_method_rows_have_explicit_semantic_mapping": True,
            "nonprimary_executable_mechanisms_complete": False,
            "failed_attempts_startup_checkpoint_copy_and_serialization_work": None,
            "scalar_weights_hardware_and_spending_limits": None,
        },
        "remaining_decisions": {
            "scientific_or_implementation": [
                "REVIEW_PRIMARY_REAL_DOMAIN_SCHEMA_LAW_ARCHITECTURE_AND_NUMERICAL_GRID_SUCCESSORS",
                "REVIEW_FOUR_CONTROL_DOMAIN_ROWS_WITH_NO_DECLARED_LEARNED_TARGET_BUT_INHERITED_OPTIMIZER_SCHEDULE",
                "IMPLEMENT_FOUR_LEARNED_CONTROL_EIGHT_FAMILY_AND_TWO_EXTERNAL_ROW_MECHANISMS",
                "DEFINE_OPERATION_UNITS_AND_FAILURE_OVERHEAD_CHARGING_WITHOUT_FREE_REUSE",
            ],
            "measurement": [
                "SUPPLY_ACTUAL_ACTIVE_EMPTY_HEUN_JUMP_CLOCK_REJECTION_AND_OBSERVATION_CARDINALITY_COUNTS",
                "CALIBRATE_F104_WEIGHTS_AND_RUNTIME_MEMORY_THROUGHPUT_ON_CHOSEN_HARDWARE",
            ],
            "operator": [
                "SELECT_AVAILABLE_HARDWARE_AND_EXPLICIT_WALL_TIME_MEMORY_STORAGE_SPEND_CEILINGS",
                "REVIEW_EQUAL_MATCHED_PRIMARY_BUDGET_SUCCESSOR_BEFORE_ANY_LAUNCH",
            ],
        },
        "unknowns": [
            "NONPRIMARY_AND_REMOVED_COMPONENT_CONTROL_OPTIMIZER_SAMPLER_EVENT_MAPPING",
            "PRIMARY_LOGICAL_EVENT_TO_ACTUAL_RUNTIME_OPERATION_MAPPING",
            "FRESH_JOINT_PRODUCT_POPULATION_GENERATION_F104_EVENT_MAPPING_AND_ALLOWANCE",
            "QUERY_REFINED_GRID_AND_ACTIVE_SUBSTEP_REJECTION_THINNING_ORACLE_WORK",
            "POPULATION_INITIALIZER_AND_OBSERVATION_KERNEL_OPERATION_WORK",
            "PAIRED_CLASSIFIER_AND_NUISANCE_FORWARD_BACKWARD_F104_EVENT_MAPPING",
            "RAW_OBSERVATION_TASK_CONTEXT_ENCODER_AND_PREPROCESSING_F104_EVENT_MAPPING",
            "UNIQUE_NUISANCE_AND_RAW_ENCODER_PARAMETER_COUNTS_AND_PARAMETER_COUNT_HARD_AXIS",
            "F064_F065_F070_F071_PROSPECTIVE_CONFIGURATION_AND_PARAMETER_COUNT_SUCCESSORS",
            "F105_CARDINALITY_DEPENDENT_SYMBOLIC_EVENT_PAIR_WORK",
            "F104_EVENT_SPECIFIC_RUNTIME_CALIBRATION_WEIGHTS",
            "WALL_TIME_GPU_HOURS_PEAK_HOST_DEVICE_MEMORY_AND_STORAGE_CEILINGS",
            "TOTAL_SPEND_LIMIT_AND_APPROVED_CAPACITY",
            "GPU_NUMERICAL_DETERMINISM_AND_CPU_REFERENCE_EQUIVALENCE",
        ],
        "scope": "VALIDATION_AND_PAIRED_POPULATION_WORKLOAD_DRAFT_NOT_FULL_COMPUTE_QUALIFICATION",
        "f066_f072_or_b06_closed": False,
        "f064_f065_f070_f071_prospective_successors_adopted": False,
        "budgets_adopted_or_old_frozen_records_changed": False,
        "paid_job_launch_or_training_authorized": False,
    }
    body["record_sha256"] = _digest(body)
    return deepcopy(body)
