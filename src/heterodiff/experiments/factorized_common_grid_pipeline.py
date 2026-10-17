"""Opt-in common-grid neural conditional learning and numerical sampling.

The fixed grid gives paired training queries one BASE endpoint law. The linear
residual gate is an explicit successor, not a reinterpretation of legacy cubic
receipts. BASE uses BASE_GRAPH_FP64_SHARED_V1; conditional graphs remain their
existing precision. The physical sampler still tilts coefficients and applies
its hybrid numerical scheme. It is NOT the finite benchmark's exactly
normalized transition-row twist or an exact conditioned numerical path.
"""
from copy import deepcopy
import hashlib
import json
import math

import torch

from heterodiff.experiments.factorized_conditional_pipeline import (
    FactorizedPopulationContext, _clock_binding, _parameter_digest,
    _reference_identity,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedObservation, FactorizedTrainingBatch,
)
from heterodiff.experiments.factorized_device_training import (
    DeviceFactorizedConditionalModel, DeviceFactorizedPhysicalPotential,
    _optimizer_parameters, _update,
)
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, LearnedFactorizedSampler, _Streams,
    conditional_initializer,
)

PRECISION_POLICY = "BASE_GRAPH_FP64_SHARED_V1"
RESIDUAL_GATE_POLICY = "LINEAR_ACTIVE_TIME_V1"
POPULATION_CONTRACT = "COMMON_FIXED_GRID_NEURAL_BASE_POPULATION_V1"


class CommonGridPipelineError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise CommonGridPipelineError(message)


def _digest(record):
    return hashlib.sha256(json.dumps(
        record, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _scope():
    return {
        "common_fixed_base_path_law": True,
        "query_time_inserted_into_grid": False,
        "finite_grid_training_law": True,
        "continuous_time_conditional_recovery_claimed": False,
        "exact_numerical_doob_transform_claimed": False,
        "physical_sampler": "COEFFICIENT_TILTED_HYBRID_NUMERICAL_SCHEME",
        "stage_time_interpolation_qualified": False,
        "potential_evaluation_scope": "HEUN_AND_MIDPOINT_STATES_BEYOND_TRAINING_MACRO_NODES",
        "production_qualification": False,
        "real_data_accessed_by_entrypoint": False,
        "paid_or_remote_jobs_launched": False,
    }


class CommonGridDeviceFactorizedBasePopulation:
    """Frozen BASE snapshots, one grid, and independently keyed whole paths.

    Query time is absent from path and endpoint-observation stream namespaces.
    Repeating a seed/record at another admitted query reconstructs the same two
    whole paths and observations, selecting only another existing grid state.
    This is not a cache and finite-PRNG replay is not a proof of ideal IID draws.
    """

    def __init__(self, base, reference, reverse_grid, context):
        _need(type(base) is DeviceFactorizedEnergy
              and type(reference) is ExactFactorizedReference
              and type(context) is FactorizedPopulationContext,
              "exact device BASE, reference and context required")
        _need(context.domain_id == reference.reference.domain_id
              and base.architecture.total_cap == reference.parameters.reference_cap
              and base.architecture.horizon == reference.schedule.horizon,
              "common-grid population carrier mismatch")
        _need(type(reverse_grid) is tuple and
              all(type(u) is float and math.isfinite(u) for u in reverse_grid),
              "explicit finite float grid tuple required")
        self.reference, self.context = deepcopy(reference), context
        self.physical = DeviceFactorizedPhysicalPotential(
            base, base_context=context.base_context,
            clean_hold=reference.schedule.clean_hold,
            precision_policy=PRECISION_POLICY,
        )
        self.sampler = LearnedFactorizedSampler(
            self.reference, self.physical, reverse_grid,
        )
        self._grid = self.sampler.grid
        hold = reference.schedule.horizon - reference.schedule.clean_hold
        self._active_times = tuple(u for u in self._grid if u < hold)
        _need(bool(self._active_times) and self._active_times[0] == 0.0,
              "grid needs reverse time zero in its active-time roster")
        self._binding_sha256 = _digest(self._binding_record())
        self._law_id = "common-grid-neural-base-v1-" + self._binding_sha256

    @property
    def grid(self):
        return self._grid

    @property
    def active_times(self):
        return self._active_times

    @property
    def law_id(self):
        return self._law_id

    @property
    def precision_policy(self):
        return PRECISION_POLICY

    def _reference_identity(self):
        return _reference_identity(self.reference)

    def snapshot_binding(self):
        """JSON-ready experiment metadata, not a resumable checkpoint."""
        self._validate_binding()
        return {
            **self._binding_record(),
            "population_law_id": self.law_id,
            "grid_values": list(self.grid),
            "active_time_values": list(self.active_times),
            "time_policy": "UNIFORM_DISCRETE_ACTIVE_GRID",
            "active_time_weights": [
                {"reverse_time": u, "numerator": 1,
                 "denominator": len(self.active_times)}
                for u in self.active_times
            ],
            "required_residual_gate_policy": RESIDUAL_GATE_POLICY,
            "resumable_checkpoint": False,
            "scope": _scope(),
        }

    def _binding_record(self):
        return {
            "contract": POPULATION_CONTRACT,
            "base_parameters": _parameter_digest(self.physical.base),
            "architecture": self.physical.base.architecture.architecture_sha256,
            "device": str(self.physical.device),
            "torch_version": torch.__version__,
            "cuda_build": torch.version.cuda,
            "base_precision_policy": self.physical.precision_policy,
            "reference": self._reference_identity(),
            "context": self.context.binding().hex(),
            "grid": [u.hex() for u in self._grid],
            "active_times": [u.hex() for u in self._active_times],
            "schedule": self.reference.schedule.__dict__,
        }

    def _validate_binding(self):
        _need(type(self.physical) is DeviceFactorizedPhysicalPotential
              and self.physical.precision_policy == PRECISION_POLICY
              and self.physical.model is None
              and self.sampler.potential is self.physical
              and self.sampler.reference is self.reference
              and self.sampler.initializer is None
              and self.sampler.grid == self._grid
              and _digest(self._binding_record()) == self._binding_sha256,
              "common-grid population snapshot or grid changed")
        return PRECISION_POLICY

    def _query_time(self, value):
        _need(type(value) is float and math.isfinite(value)
              and value in self._active_times,
              "query must be an existing active grid time; no refinement or hold query")
        return value

    def sample_pair(self, *, reverse_time, run_seed, record_id):
        self._validate_binding()
        u = self._query_time(reverse_time)
        _need(type(record_id) is bytes and bool(record_id),
              "explicit pair record id required")
        record = hashlib.sha256(
            self.context.binding() + self.law_id.encode("ascii") + record_id,
        ).digest()
        paths, observations = [], []
        for branch in (b"common-grid-joint-one", b"common-grid-product-two"):
            path = self.sampler.sample_path(
                run_seed=run_seed, record_id=record, branch_id=branch,
            )
            visible = self.reference.oracle.sample_observation(
                path.terminal_state,
                _Streams(run_seed, record, branch).rng("terminal-observation"),
            )
            observations.append(FactorizedObservation(
                visible, self.context.domain_id, self.context.task_id,
                self.context.context_bytes,
            ))
            path.diagnostics.update({
                "population_law_id": self.law_id,
                "base_precision_policy": PRECISION_POLICY,
                "common_fixed_grid": self.grid,
                "active_training_times": self.active_times,
                "query_refined_grid": False,
                "query_time_in_path_or_observation_namespace": False,
                "scope": _scope(),
            })
            paths.append(path)
        state = paths[0].at_time(u)
        joint = FactorizedTrainingBatch(
            (state,), (u,), (observations[0],), self.law_id,
        )
        product = FactorizedTrainingBatch(
            (state,), (u,), (observations[1],), self.law_id,
        )
        return joint, product, tuple(paths)


def _model_binding(model, population):
    _need(type(model) is DeviceFactorizedConditionalModel
          and type(population) is CommonGridDeviceFactorizedBasePopulation,
          "exact common-grid population and device conditional model required")
    population._validate_binding()
    _need(getattr(model, "residual_gate_policy", None) == RESIDUAL_GATE_POLICY,
          "common-grid successor requires LINEAR_ACTIVE_TIME_V1")
    _need(model.device == population.physical.device
          and model.conditioner.architecture == population.physical.base.architecture
          and model.guide.identity_sha256 == population._reference_identity(),
          "conditional architecture, reference or device mismatch")
    _need(model.horizon == population.reference.schedule.horizon
          and model.clean_hold == population.reference.schedule.clean_hold,
          "conditional horizon or hold mismatch")
    _clock_binding(model, population.reference)


def common_grid_train_conditional_step(
    model, population, *, optimizer, run_seed, record_id,
    sample_count, reverse_time=None,
):
    """One paired update, uniformly over existing active grid points by default."""
    _model_binding(model, population)
    _need(type(sample_count) is int and 0 < sample_count <=
          model.conditioner.architecture.limits.maximum_batch_size,
          "conditional sample count limit")
    _need(type(record_id) is bytes and bool(record_id),
          "explicit step record id required")
    if reverse_time is not None:
        population._query_time(reverse_time)
    _optimizer_parameters(model, optimizer)
    record = hashlib.sha256(
        population.context.binding() + population.law_id.encode("ascii") + record_id,
    ).digest()
    stream = _Streams(run_seed, record, b"common-grid-training-time")
    joints, products, paths = [], [], []
    for i in range(sample_count):
        u = reverse_time
        if u is None:
            index = int(stream.rng("active-grid-index", i).integers(
                len(population.active_times),
            ))
            u = population.active_times[index]
        j, p, pair = population.sample_pair(
            reverse_time=u, run_seed=run_seed,
            record_id=record_id + i.to_bytes(8, "big"),
        )
        joints.append(j)
        products.append(p)
        paths.extend(pair)
    time_policy = ("UNIFORM_DISCRETE_ACTIVE_GRID" if reverse_time is None
                   else "FIXED_ACTIVE_GRID_TIME_DIAGNOSTIC")
    time_record = {"policy": time_policy, "active_times": population.active_times,
                   "fixed_time": reverse_time}
    law = population.law_id + "-time-" + _digest(time_record)
    joint = FactorizedTrainingBatch(
        tuple(j.states[0] for j in joints),
        tuple(j.reverse_times[0] for j in joints),
        tuple(j.observations[0] for j in joints), law,
    )
    product = FactorizedTrainingBatch(
        joint.states, joint.reverse_times,
        tuple(p.observations[0] for p in products), law,
    )
    loss = model.paired_loss(joint, product)
    changed = _update(model, optimizer, loss)
    return {
        "decision": "LOCAL_COMMON_GRID_CONDITIONAL_STEP_COMPLETE",
        "loss": float(loss.detach()),
        "changed_parameter_elements": changed,
        "device": str(model.device),
        "reverse_times": joint.reverse_times,
        "time_policy": time_policy,
        "active_training_times": population.active_times,
        "base_paths_generated": len(paths),
        "actual_macrosteps": sum(len(p.reverse_grid) - 1 for p in paths),
        "query_refined_paths": 0,
        "law_id": law,
        "population_law_id": population.law_id,
        "base_precision_policy": PRECISION_POLICY,
        "residual_gate_policy": RESIDUAL_GATE_POLICY,
        "method_id": model.method_id,
        "scientific_training_completed": False,
        "scope": _scope(),
    }


def common_grid_sample_conditional(
    base, model, reference, reverse_grid, context, observed, *,
    run_seed, record_id, expected_population_law_id=None,
):
    """Sample a linearly gated coefficient-tilted path on the declared grid.

    The analytic proposal plus residual-only rejection has its stated initial
    target. Later hybrid numerical transitions are not normalized Doob rows.
    A changed BASE/grid/context defines a new sampling law. Supply the trained
    population's law_id to enforce that binding; otherwise compare the returned
    base_population_law_id explicitly. Neither mode is a checkpoint restore.
    """
    population = CommonGridDeviceFactorizedBasePopulation(
        base, reference, reverse_grid, context,
    )
    _model_binding(model, population)
    if expected_population_law_id is not None:
        _need(type(expected_population_law_id) is str
              and expected_population_law_id == population.law_id,
              "sampling BASE population does not match the expected training law")
    _need(type(record_id) is bytes and bool(record_id),
          "explicit sample record id required")
    observation = FactorizedObservation(
        observed, context.domain_id, context.task_id, context.context_bytes,
    )
    physical = DeviceFactorizedPhysicalPotential(
        base, base_context=context.base_context, conditional_model=model,
        observation=observation, clean_hold=reference.schedule.clean_hold,
        precision_policy=PRECISION_POLICY,
    )
    initializer = conditional_initializer(
        physical.model.guide, physical, observed, population.reference.schedule,
        model.method_id,
        maximum_trials=population.reference.limits.maximum_initialization_trials,
    )
    observation_record = None if observed is None else [
        [event.key.canonical_bytes().hex(),
         None if event.coordinate is None else event.coordinate.hex()]
        for event in observed
    ]
    sampler_law = "common-grid-conditional-v1-" + _digest({
        "base_population": population.law_id,
        "conditional_parameters": _parameter_digest(physical.model),
        "method": model.method_id,
        "residual_gate_policy": RESIDUAL_GATE_POLICY,
        "observation": observation_record,
        "physical_sampler": "COEFFICIENT_TILTED_HYBRID_NUMERICAL_SCHEME",
    })
    record = hashlib.sha256(sampler_law.encode("ascii") + record_id).digest()
    path = LearnedFactorizedSampler(
        population.reference, physical, population.grid, initializer=initializer,
    ).sample_path(
        run_seed=run_seed, record_id=record,
        branch_id=b"common-grid-linear-conditional",
    )
    path.diagnostics.update({
        "sampler_law_id": sampler_law,
        "base_population_law_id": population.law_id,
        "base_precision_policy": PRECISION_POLICY,
        "conditioner_precision_policy": "LEGACY_FP32",
        "residual_gate_policy": RESIDUAL_GATE_POLICY,
        "common_fixed_grid": population.grid,
        "expected_training_population_binding_checked": expected_population_law_id is not None,
        "scope": _scope(),
    })
    return path


def common_grid_integration_smoke(*, maximum_seconds=30.0):
    """Fixed CPU 2-BASE/2-conditional/2-draw integration in all four cases.

    The caller must select one CPU thread; this function does not change global
    numerical settings. The deadline is checked between operations (soft), with
    fixed operation counts and existing per-path limits. No dataset, GPU,
    package installation, external job or filesystem output is requested.
    A failed operation raises rather than returning a partial PASS report.
    """
    import time
    import numpy as np
    from heterodiff.experiments.factorized_conditional_training import FactorizedConditionalModel
    from heterodiff.experiments.factorized_device_training import device_train_base_step
    from heterodiff.experiments.factorized_precision_pipeline_qualification import (
        DOMAINS, METHODS, GRID, _fixture,
    )
    from heterodiff.models.factorized_configuration_energy_torch import BoundedFactorizedConfigurationEnergy
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide

    _need(type(maximum_seconds) is float and math.isfinite(maximum_seconds)
          and 0 < maximum_seconds <= 30.0, "smoke deadline must be a positive float <=30 seconds")
    _need(torch.get_num_threads() == 1, "integration smoke requires caller-selected one CPU thread")
    started = time.monotonic()

    def budget():
        _need(time.monotonic() - started < maximum_seconds,
              "common-grid integration smoke soft deadline exceeded")

    def optimizer(model):
        return torch.optim.AdamW(
            model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8,
            weight_decay=0.0, foreach=False, fused=False, amsgrad=False,
            maximize=False, capturable=False, differentiable=False,
        )

    cases = []
    for domain in DOMAINS:
        for method in METHODS:
            budget()
            # Reuse the existing data-free mixed/duplicate fixture, but construct
            # the successor head explicitly instead of relabeling its legacy head.
            source, reference, base, _, context = _fixture(domain, method)
            _need(str(base.device) == "cpu", "smoke fixture must remain CPU-only")
            cpu_model = FactorizedConditionalModel(
                BoundedFactorizedConfigurationEnergy(
                    base.architecture, initialization_seed=42,
                ),
                guide=FactorizedAssociationGuide(reference.oracle), method_id=method,
                clean_hold=reference.schedule.clean_hold,
                remaining_clocks=reference.schedule.remaining_clocks,
                observation_seed=43, nuisance_seed=44,
                residual_gate_policy=RESIDUAL_GATE_POLICY,
            )
            model = DeviceFactorizedConditionalModel.from_cpu(cpu_model, "cpu")
            base_initial = _parameter_digest(base)
            conditional_initial = _parameter_digest(model)
            base_optimizer = optimizer(base)
            base_rng = np.random.default_rng(730)
            base_updates = []
            for _ in range(2):
                budget()
                base_updates.append(device_train_base_step(
                    base, reference, (source,), context=torch.zeros(
                        64, dtype=torch.float32, device="cpu",
                    ), rng=base_rng, optimizer=base_optimizer,
                    sample_count=2, jump_weight=1.0,
                    precision_policy=PRECISION_POLICY,
                ))
            population = CommonGridDeviceFactorizedBasePopulation(
                base, reference, GRID, context,
            )
            conditional_optimizer = optimizer(model)
            conditional_updates = []
            for step in range(2):
                budget()
                conditional_updates.append(common_grid_train_conditional_step(
                    model, population, optimizer=conditional_optimizer,
                    run_seed=731,
                    record_id=b"common-grid-smoke-step-" + step.to_bytes(8, "big"),
                    sample_count=1,
                ))
            paths = []
            for draw in range(2):
                budget()
                path = common_grid_sample_conditional(
                    base, model, reference, GRID, context, (source[-1],),
                    run_seed=732,
                    record_id=b"common-grid-smoke-draw-" + draw.to_bytes(8, "big"),
                    expected_population_law_id=population.law_id,
                )
                _need(path.reverse_grid == GRID and
                      path.terminal_state is path.states[-2],
                      "smoke conditional grid or clean hold changed")
                _need(all(len(state) <= 4 and all(
                    event.key.domain_id == domain and
                    (event.coordinate is None or math.isfinite(event.coordinate))
                    for event in state
                ) for state in path.states), "smoke produced invalid or nonfinite events")
                paths.append({
                    "grid": list(path.reverse_grid),
                    "event_counts": [len(state) for state in path.states],
                    "state_grid_sha256": _digest([
                        [[event.key.canonical_bytes().hex(), event.coordinate]
                         for event in state] for state in path.states
                    ]),
                    "accepted_births": path.diagnostics["accepted_birth"],
                    "accepted_deaths": path.diagnostics["accepted_death"],
                    "jump_candidates": path.diagnostics["jump_candidates"],
                    "clean_hold_preserved": True,
                    "expected_training_population_binding_checked":
                        path.diagnostics["expected_training_population_binding_checked"],
                })
            _need(all(math.isfinite(row["loss"]) and
                      row["changed_parameter_elements"] > 0
                      for row in base_updates + conditional_updates),
                  "smoke update nonfinite or no parameters changed")
            _need(all(bool(torch.isfinite(p).all())
                      for item in (base, model) for p in item.parameters()),
                  "smoke model contains nonfinite parameters")
            base_final, conditional_final = _parameter_digest(base), _parameter_digest(model)
            _need(base_initial != base_final and conditional_initial != conditional_final,
                  "smoke training did not change model parameters")
            cases.append({
                "domain_id": domain, "method_id": method,
                "base_optimizer_updates": 2, "conditional_optimizer_updates": 2,
                "conditional_draw_count": 2,
                "base_initial_parameters_sha256": base_initial,
                "base_trained_parameters_sha256": base_final,
                "conditional_initial_parameters_sha256": conditional_initial,
                "conditional_trained_parameters_sha256": conditional_final,
                "frozen_population_matches_trained_base":
                    _parameter_digest(population.physical.base) == base_final,
                "base_updates": base_updates,
                "conditional_updates": conditional_updates,
                "population": population.snapshot_binding(),
                "conditional_paths": paths,
                "all_checked_quantities_finite": True,
            })
    shared = all(
        len({row["population"]["population_law_id"] for row in cases
             if row["domain_id"] == domain}) == 1 for domain in DOMAINS
    )
    _need(shared, "matched methods did not receive the same trained BASE population")
    _need(all(row["frozen_population_matches_trained_base"] for row in cases),
          "frozen population does not match trained BASE")
    budget()
    return {
        "schema_version": "factorized-common-grid-neural-integration-smoke-v1",
        "decision": "PASS_LOCAL_CPU_TRAINED_BASE_COMMON_GRID_INTEGRATION_ONLY",
        "device": "cpu",
        "base_precision_policy": PRECISION_POLICY,
        "residual_gate_policy": RESIDUAL_GATE_POLICY,
        "elapsed_seconds": time.monotonic() - started,
        "maximum_seconds_soft": maximum_seconds,
        "hard_deadline_enforced_by_entrypoint": False,
        "bounds": {
            "cases": 4, "base_optimizer_updates": 8,
            "conditional_optimizer_updates": 8, "base_samples_per_update": 2,
            "conditional_samples_per_update": 1,
            "paired_base_paths": 16, "conditional_paths": 8,
            "state_cap": 4, "retries": 0, "cpu_threads": 1,
        },
        "completed_case_count": len(cases),
        "shared_trained_base_within_domain": shared,
        "cases": cases,
        "scope": {
            **_scope(),
            "synthetic_integration_only": True,
            "exact_posterior_comparison_performed": False,
            "method_superiority_established": False,
            "checkpoint_resume_exercised": False,
            "files_written": False,
            "gpu_requested": False,
        },
    }
