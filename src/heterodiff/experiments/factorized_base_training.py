"""Actual relative-score/jump-flux BASE objective, local CPU prototype only.

The amended TRAIN target is reference-corrupted exactly before evaluating the
population integrands of executable_method_spec §4.2. This is not fixed-grid
denoising, supervised regression to invented energies, or a claim that a bounded
neural class realizes the exact reverse law. All source/context labels and
scientific parameters are explicit caller inputs; no data admission occurs.
"""

from dataclasses import dataclass
import math

import numpy as np
import torch

from heterodiff.data.two_domain_factorized_state import FactoredEvent
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedConfigurationBatch,
)


class FactorizedBaseTrainingError(ValueError):
    pass


def _need(condition, code):
    if not condition:
        raise FactorizedBaseTrainingError(code)


def _finite(value, label):
    _need(type(value) in (torch.Tensor, torch.nn.Parameter) and bool(torch.isfinite(value).all()),
          "NONFINITE_" + label + "_NO_CLIPPING")


def pack_base_batch(model, states, forward_times, context):
    """Explicit CPU FP32 scalar conversion; exact metadata never becomes float."""
    _need(type(states) is tuple and len(states) > 0 and type(forward_times) is tuple
          and len(states) == len(forward_times), "ALIGNED_NONEMPTY_STATE_TIME_TUPLES_REQUIRED")
    _need(type(context) is torch.Tensor and context.dtype == torch.float32
          and context.device.type == "cpu" and tuple(context.shape) == (64,),
          "EXPLICIT_CPU_FP32_CONTEXT_VECTOR_REQUIRED")
    _finite(context, "CONTEXT")
    events, owners = [], []
    for ordinal, state in enumerate(states):
        _need(type(state) is tuple and all(type(event) is FactoredEvent for event in state),
              "EXACT_FACTORED_STATE_REQUIRED")
        events.extend(state)
        owners.extend([ordinal] * len(state))
    coordinates = tuple(torch.tensor([] if event.coordinate is None else [event.coordinate],
                                     dtype=torch.float32, device="cpu", requires_grad=True)
                        for event in events)
    for value in coordinates:
        _finite(value, "CONVERTED_COORDINATE")
    return FactorizedConfigurationBatch(
        model.architecture.architecture_sha256,
        tuple(event.key.canonical_bytes() for event in events),
        tuple(event.key.dimension for event in events), coordinates, tuple(owners),
        torch.tensor(forward_times, dtype=torch.float32, device="cpu"),
        context.detach().clone().expand(len(states), 64))


def relative_continuous_score_terms(values, batch):
    """Per-state sum [0.5 V_r² + V_rr - r V_r], no atomic differentiation.

    Each continuous fiber is scalar, so the diagonal Hessian is exact autograd,
    not a stochastic trace estimate. FP32 derivatives are accumulated in FP64.
    The caller applies the process-owned continuous schedule rate afterward.
    """
    _need(type(batch) is FactorizedConfigurationBatch and type(values) is torch.Tensor
          and tuple(values.shape) == tuple(batch.forward_time.shape)
          and values.device.type == "cpu" and values.requires_grad,
          "DIFFERENTIABLE_ALIGNED_ENERGY_VECTOR_REQUIRED")
    _finite(values, "ENERGY")
    terms = [value.double() * 0 for value in values]
    total = values.sum()
    for dimension, coordinate, owner in zip(batch.coordinate_dimensions, batch.coordinates, batch.owners):
        if dimension == 0:
            _need(tuple(coordinate.shape) == (0,), "ATOMIC_COORDINATES_MUST_BE_EMPTY")
            continue
        _need(dimension == 1 and tuple(coordinate.shape) == (1,) and coordinate.requires_grad,
              "SCALAR_DIFFERENTIABLE_FIBER_REQUIRED")
        gradient = torch.autograd.grad(total, coordinate, create_graph=True,
                                       retain_graph=True, allow_unused=True)[0]
        if gradient is None:
            continue  # A constant-in-coordinate potential is legal.
        if gradient.requires_grad:
            second = torch.autograd.grad(gradient.sum(), coordinate, create_graph=True,
                                         retain_graph=True, allow_unused=True)[0]
        else:
            second = None
        gradient = gradient.double()
        hessian = gradient.sum() * 0 if second is None else second.double().sum()
        contribution = .5 * gradient.square().sum() + hessian - (coordinate.detach().double() * gradient).sum()
        terms[owner] = terms[owner] + contribution
    result = torch.stack(terms)
    _finite(result, "RELATIVE_CONTINUOUS_SCORE")
    return result


def jump_flux_terms(source_values, destination_values, unnormalized_rates):
    """Lambda0 * [exp(delta V) + delta V], with the positive linear sign."""
    _need(type(source_values) is torch.Tensor and type(destination_values) is torch.Tensor
          and type(unnormalized_rates) is torch.Tensor
          and source_values.ndim == 1 and source_values.shape == destination_values.shape == unnormalized_rates.shape,
          "ALIGNED_JUMP_VECTORS_REQUIRED")
    for value in (source_values, destination_values, unnormalized_rates):
        _finite(value, "JUMP_INPUT")
        _need(value.device.type == "cpu", "CPU_JUMP_INPUTS_REQUIRED")
    _need(bool((unnormalized_rates >= 0).all()), "NONNEGATIVE_UNNORMALIZED_RATES_REQUIRED")
    delta = destination_values.double() - source_values.double()
    terms = unnormalized_rates.detach().double() * (torch.exp(delta) + delta)
    _finite(terms, "JUMP_FLUX")
    return terms


@dataclass(frozen=True)
class BaseObjective:
    total: torch.Tensor
    continuous: torch.Tensor
    jump: torch.Tensor
    source_batch: FactorizedConfigurationBatch


def base_objective_on_corrupted_states(model, states, destinations, forward_times,
                                        context, continuous_rates, jump_rates,
                                        *, jump_weight):
    """Deterministic objective seam; supplied corruption/proposal law is external."""
    _need(type(model) is BoundedFactorizedConfigurationEnergy, "EXACT_FACTORIZED_ENERGY_REQUIRED")
    _need(type(jump_weight) is float and math.isfinite(jump_weight) and jump_weight > 0,
          "EXPLICIT_POSITIVE_JUMP_WEIGHT_REQUIRED")
    _need(type(continuous_rates) is tuple and type(jump_rates) is tuple
          and len(states) == len(destinations) == len(continuous_rates) == len(jump_rates),
          "ALIGNED_OBJECTIVE_INPUTS_REQUIRED")
    _need(all(type(rate) is float and math.isfinite(rate) and rate >= 0
              for rate in continuous_rates + jump_rates), "FINITE_NONNEGATIVE_RATES_REQUIRED")
    source_batch = pack_base_batch(model, states, forward_times, context)
    destination_batch = pack_base_batch(model, destinations, forward_times, context)
    source_values = model(source_batch)
    destination_values = model(destination_batch)
    continuous_terms = relative_continuous_score_terms(source_values, source_batch)
    continuous = (continuous_terms * torch.tensor(continuous_rates, dtype=torch.float64, device="cpu")).mean()
    jump = jump_flux_terms(source_values, destination_values,
                           torch.tensor(jump_rates, dtype=torch.float64, device="cpu")).mean()
    total = continuous + jump_weight * jump
    _finite(total, "BASE_OBJECTIVE")
    return BaseObjective(total, continuous, jump, source_batch)


def _validate_optimizer(model, optimizer):
    _need(type(optimizer) is torch.optim.AdamW and len(optimizer.param_groups) == 1,
          "ONE_ADAMW_PARAMETER_GROUP_REQUIRED")
    group = optimizer.param_groups[0]
    trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
    selected = tuple(group["params"])
    _need(trainable and len(selected) == len(trainable)
          and {id(value) for value in selected} == {id(value) for value in trainable},
          "ALL_AND_ONLY_TRAINABLE_PARAMETERS_REQUIRED")
    _need(group["betas"] == (.9, .999) and group["eps"] == 1e-8 and group["weight_decay"] == 0.0,
          "DECLARED_ADAMW_SETTINGS_REQUIRED")
    _need(all(group.get(flag, False) is False for flag in (
        "amsgrad", "maximize", "foreach", "fused", "capturable", "differentiable")),
        "EXPLICIT_NONFUSED_SINGLE_STEP_ADAMW_REQUIRED")
    _need(type(group["lr"]) is float and math.isfinite(group["lr"]) and group["lr"] > 0,
          "FINITE_POSITIVE_LEARNING_RATE_REQUIRED")
    return trainable


def train_base_step(model, reference_process, train_sources, *, context, rng,
                    optimizer, sample_count, jump_weight):
    """One real AdamW step, with exact reference corruption of amended Q0.

    This runs a user-requested local step, not the frozen 4096-update cadence.
    Uniform active-time sampling estimates the declared expectation, so there
    is no extra 1/omega multiplier. A representability/resource failure stops;
    failure after optimizer mutation is not rolled back and relabelled success.
    """
    from heterodiff.processes.factorized_hybrid_sampler import ExactFactorizedReference
    _need(type(model) is BoundedFactorizedConfigurationEnergy, "EXACT_FACTORIZED_ENERGY_REQUIRED")
    _need(type(reference_process) is ExactFactorizedReference, "EXACT_FACTORIZED_REFERENCE_PROCESS_REQUIRED")
    _need(type(rng) is np.random.Generator and type(rng.bit_generator) in (np.random.PCG64, np.random.PCG64DXSM),
          "EXPLICIT_PCG64_GENERATOR_REQUIRED")
    _need(type(sample_count) is int and 1 <= sample_count <= 64, "LOCAL_SAMPLE_COUNT_LIMIT")
    _need(type(train_sources) is tuple and train_sources, "EXPLICIT_NONEMPTY_TRAIN_SOURCE_ROSTER_REQUIRED")
    schedule = reference_process.schedule
    _need(model.architecture.total_cap == reference_process.oracle.parameters.reference_cap
          and model.architecture.horizon == schedule.horizon,
          "MODEL_PROCESS_CAP_HORIZON_MISMATCH")
    trainable = _validate_optimizer(model, optimizer)
    _need(type(context) is torch.Tensor and context.dtype == torch.float32
          and context.device.type == "cpu" and tuple(context.shape) == (64,),
          "EXPLICIT_CPU_FP32_CONTEXT_VECTOR_REQUIRED")
    _finite(context, "CONTEXT")
    states, destinations, times, continuous_rates, jump_rates, kinds = [], [], [], [], [], []
    for _ in range(sample_count):
        uniform = float(rng.random())
        _need(0 < uniform < 1, "ACTIVE_TIME_RNG_ENDPOINT_NO_REDRAW")
        time = schedule.clean_hold + (schedule.horizon - schedule.clean_hold) * uniform
        _need(schedule.clean_hold < time < schedule.horizon, "ACTIVE_TIME_NOT_REPRESENTABLE_NO_REDRAW")
        encoded_time = float(torch.tensor(time, dtype=torch.float32, device="cpu"))
        _need(schedule.clean_hold < encoded_time < schedule.horizon,
              "ACTIVE_TIME_FP32_ENDPOINT_NO_REDRAW")
        source = reference_process.oracle.sample_training_target(train_sources, rng)
        state = reference_process.sample_forward(source, time, rng)
        proposal = reference_process.proposal(state, rng)
        if proposal is None:
            destination, total_rate, kind = state, 0.0, "NO_EXIT"
        else:
            destination, total_rate, kind = proposal
        physical_rate = float(schedule.reverse_jump_rate(schedule.horizon - time))
        weighted_rate = physical_rate * float(total_rate)
        _need(math.isfinite(weighted_rate) and weighted_rate >= 0,
              "REFERENCE_PROPOSAL_RATE_NOT_REPRESENTABLE")
        states.append(state)
        destinations.append(destination)
        times.append(time)
        continuous_rates.append(float(schedule.reverse_continuous_rate(schedule.horizon - time)))
        jump_rates.append(weighted_rate)
        kinds.append(kind)
    before = {name: parameter.detach().clone() for name, parameter in model.named_parameters()}
    objective = base_objective_on_corrupted_states(
        model, tuple(states), tuple(destinations), tuple(times), context,
        tuple(continuous_rates), tuple(jump_rates), jump_weight=jump_weight)
    optimizer.zero_grad(set_to_none=True)
    objective.total.backward()
    for parameter in trainable:
        if parameter.grad is not None:
            _need(parameter.grad.dtype == torch.float32 and parameter.grad.device.type == "cpu",
                  "CPU_FP32_GRADIENT_REQUIRED")
            _finite(parameter.grad, "BASE_GRADIENT")
    optimizer.step()
    for name, parameter in model.named_parameters():
        _finite(parameter, "PARAMETER_AFTER_UPDATE_STEP_MAY_BE_SPENT")
        _need(parameter.dtype == torch.float32 and parameter.device.type == "cpu",
              "CPU_FP32_PARAMETERS_REQUIRED")
        if not parameter.requires_grad:
            _need(torch.equal(before[name], parameter), "FROZEN_PARAMETER_MUTATED")
    for parameter in trainable:
        for name in ("exp_avg", "exp_avg_sq"):
            value = optimizer.state.get(parameter, {}).get(name)
            if value is not None:
                _finite(value, "OPTIMIZER_MOMENT_AFTER_UPDATE_STEP_MAY_BE_SPENT")
                _need(value.dtype == torch.float32 and value.device.type == "cpu", "CPU_FP32_MOMENTS_REQUIRED")
    changed = sum(not torch.equal(before[name], value.detach()) for name, value in model.named_parameters())
    return {"scope": "LOCAL_AMENDED_BASE_SCORE_AND_JUMP_FLUX_STEP_ONLY",
            "loss": float(objective.total.detach()), "continuous_loss": float(objective.continuous.detach()),
            "jump_loss": float(objective.jump.detach()), "jump_weight": jump_weight,
            "sample_count": sample_count, "forward_times": tuple(times),
            "source_cardinalities": tuple(map(len, states)), "proposal_kinds": tuple(kinds),
            "continuous_dimensions": sum(event.key.dimension for state in states for event in state),
            "changed_parameter_tensors": changed,
            "reference_forward_corruption": "EXACT_OU_AND_CAPPED_BIRTH_DEATH_FINITE_RNG_IMPLEMENTATION",
            "time_law": "UNIFORM_STRICT_ACTIVE_INTERVAL_EXPECTATION",
            "one_proposal_unnormalized_jump_weight": True,
            "atomic_coordinates_differentiated": False,
            "source_to_fp32_coordinate_rounding": "EXPLICIT_CPU_NUMERICAL_PROTOTYPE",
            "train_roster_admission_verified": False, "production_cadence_completed": False,
            "exact_population_minimizer_representable_claimed": False, "gpu_execution": False}
