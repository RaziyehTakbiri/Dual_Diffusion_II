"""Reusable frozen preparation for the existing common-grid sampler.

Preparation changes setup cost, not the numerical law: paths, law identifiers,
seed namespaces and diagnostics match common_grid_sample_conditional for the
same inputs. Caller-owned weights/reference changes cannot alter the prepared
snapshot. This remains a coefficient-tilted hybrid numerical sampler, not an
exact Doob transform or a posterior-accuracy qualification.
"""
from copy import deepcopy
import hashlib
import threading

from heterodiff.experiments.factorized_common_grid_pipeline import (
    CommonGridDeviceFactorizedBasePopulation, PRECISION_POLICY,
    RESIDUAL_GATE_POLICY, _digest, _model_binding, _scope,
)
from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
from heterodiff.experiments.factorized_conditional_training import FactorizedObservation
from heterodiff.experiments.factorized_device_training import DeviceFactorizedPhysicalPotential
from heterodiff.processes.factorized_hybrid_sampler import (
    LearnedFactorizedSampler, conditional_initializer,
)

MAXIMUM_PREPARED_DRAWS = 4096


class PreparedConditionalSamplerError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise PreparedConditionalSamplerError(message)


class PreparedCommonGridConditionalSampler:
    """Prepare once, draw with fresh explicitly keyed streams up to a fixed cap.

    maximum_draws bounds calls that begin path sampling, including failed calls;
    invalid seed/record inputs and exhausted-budget refusals do not start a
    path. The inherited per-path resource limits remain unchanged. No wall-time
    deadline is added here; a caller needing one must supervise the operation.

    Public metadata is read-only or returned as a copy. Internal neural models
    are private frozen snapshots, not caller-owned objects. Calls are serialized
    to enforce the draw cap; concurrent performance has not been qualified.
    """

    __slots__ = (
        "_sampler", "_population_law_id", "_sampler_law_id",
        "_population_binding", "_diagnostic_template", "_maximum_draws",
        "_draws_begun", "_lock",
    )

    def __init__(
        self, base, model, reference, reverse_grid, context, observed, *,
        maximum_draws, expected_population_law_id=None,
    ):
        _need(type(maximum_draws) is int
              and 0 < maximum_draws <= MAXIMUM_PREPARED_DRAWS,
              "maximum_draws must be an integer from 1 through 4096")
        population = CommonGridDeviceFactorizedBasePopulation(
            base, reference, reverse_grid, context,
        )
        _model_binding(model, population)
        if expected_population_law_id is not None:
            _need(type(expected_population_law_id) is str
                  and expected_population_law_id == population.law_id,
                  "sampling BASE population does not match the expected training law")
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
        self._sampler = LearnedFactorizedSampler(
            population.reference, physical, population.grid, initializer=initializer,
        )
        self._population_law_id = population.law_id
        self._sampler_law_id = sampler_law
        self._population_binding = population.snapshot_binding()
        self._diagnostic_template = {
            "sampler_law_id": sampler_law,
            "base_population_law_id": population.law_id,
            "base_precision_policy": PRECISION_POLICY,
            "conditioner_precision_policy": "LEGACY_FP32",
            "residual_gate_policy": RESIDUAL_GATE_POLICY,
            "common_fixed_grid": population.grid,
            "expected_training_population_binding_checked": expected_population_law_id is not None,
            "scope": _scope(),
        }
        self._maximum_draws = maximum_draws
        self._draws_begun = 0
        self._lock = threading.Lock()

    @property
    def population_law_id(self):
        return self._population_law_id

    @property
    def sampler_law_id(self):
        return self._sampler_law_id

    @property
    def maximum_draws(self):
        return self._maximum_draws

    @property
    def draws_begun(self):
        return self._draws_begun

    def snapshot_binding(self):
        """Return copied preparation metadata; this is not a checkpoint."""
        with self._lock:
            return {
                "schema_version": "factorized-prepared-common-grid-sampler-v1",
                "population": deepcopy(self._population_binding),
                "population_law_id": self._population_law_id,
                "sampler_law_id": self._sampler_law_id,
                "maximum_draws": self._maximum_draws,
                "draws_begun": self._draws_begun,
                "failed_started_draws_count_toward_limit": True,
                "resumable_checkpoint": False,
                "same_numerical_law_as_common_grid_sample_conditional": True,
                "prepared_snapshot_reused": True,
                "hard_deadline_enforced": False,
                "scope": _scope(),
            }

    def sample_path(self, *, run_seed, record_id):
        _need(type(run_seed) is int and 0 <= run_seed < 2 ** 64,
              "uint64 run_seed required")
        _need(type(record_id) is bytes and bool(record_id),
              "explicit nonempty bytes record_id required")
        with self._lock:
            _need(self._draws_begun < self._maximum_draws,
                  "prepared conditional sampler draw limit exhausted")
            record = hashlib.sha256(
                self._sampler_law_id.encode("ascii") + record_id,
            ).digest()
            self._draws_begun += 1
            path = self._sampler.sample_path(
                run_seed=run_seed, record_id=record,
                branch_id=b"common-grid-linear-conditional",
            )
            # No preparation counters or extra keys are inserted: equivalence
            # covers the original diagnostic payload, not just sampled states.
            path.diagnostics.update(deepcopy(self._diagnostic_template))
            return path

