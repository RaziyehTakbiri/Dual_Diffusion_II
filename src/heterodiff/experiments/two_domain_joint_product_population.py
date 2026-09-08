"""Same-context joint/product sampling for a bounded finite candidate base.

The two branches start independently from the supplied initial law, propagate
the supplied candidate generator to (u,S), and sample observations only from
their terminal states. The product is (Y_u from branch 1, A from branch 2).
There is no cross-context permutation or data-forward corruption here.

This is a finite, time-homogeneous synthetic implementation of the population
construction, not the missing scalable learned hybrid simulator or continuous
K_m sampler. Initial, context, task and time laws remain explicit caller inputs;
no claim that they are the production Pi_N or a frozen full-support q is made.
The existing finite matrix-exponential oracle's documented numerical repairs
are retained. Its binary64 tables are not exact real-arithmetic probabilities.
Purpose-keyed PCG64 streams give replay and address separation, not an IID proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

from heterodiff.theory.finite_state import (
    transition_matrix, validate_generator, validate_probability_vector,
)


MAX_FINITE_STATES = 64
MAX_FINITE_OBSERVATIONS = 64
STREAM_NAMESPACE = "two-domain-finite-joint-product-synthetic-pcg64-v1"
DOMAIN_IDS = ("physionet-challenge-2012", "online-retail-ii")


class PopulationConstructionError(ValueError):
    pass


def _uint64(value, name):
    if type(value) is not int or not 0 <= value < 2**64:
        raise PopulationConstructionError(f"{name} must be a uint64 integer")
    return value


def _identifier(value, name):
    if type(value) is not bytes or not 1 <= len(value) <= 256:
        raise PopulationConstructionError(f"{name} must be bounded nonempty bytes")
    return value


def _frozen_array(value):
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(array.shape)


@dataclass(frozen=True)
class ConditionalContext:
    domain_id: str
    task_id: bytes
    context_id: bytes

    def __post_init__(self):
        if type(self.domain_id) is not str or self.domain_id not in DOMAIN_IDS:
            raise PopulationConstructionError("unknown domain")
        _identifier(self.task_id, "task_id")
        _identifier(self.context_id, "context_id")

    def record(self):
        return dict(domain_id=self.domain_id, task_id_hex=self.task_id.hex(),
                    context_id_hex=self.context_id.hex())


def candidate_generator_from_energy(reference_generator, energy_values):
    """Finite jump tilt q_phi(i,j)=q_0(i,j) exp(V_j-V_i), without clipping.

    This checks the finite represented matrix only. It does not certify a
    neural checkpoint, regularity, a hybrid path, or a time discretization.
    """
    raw = np.asarray(reference_generator)
    if raw.ndim != 2 or not 1 <= raw.shape[0] <= MAX_FINITE_STATES:
        raise PopulationConstructionError("finite generator size is out of bounds")
    matrix = validate_generator(raw)
    energy = np.asarray(energy_values)
    if energy.dtype.kind not in "iuf" or energy.shape != (len(matrix),) or not np.isfinite(energy).all():
        raise PopulationConstructionError("one finite real energy value per state required")
    result = np.zeros_like(matrix)
    with np.errstate(over="raise", invalid="raise", under="raise"):
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                if i != j and matrix[i, j] > 0:
                    delta = float(energy[j]) - float(energy[i])
                    result[i, j] = matrix[i, j] * np.exp(delta)
                    if not math.isfinite(result[i, j]) or result[i, j] <= 0:
                        raise PopulationConstructionError("energy tilt is not representable; no rate clipping")
            result[i, i] = -math.fsum(float(x) for x in result[i])
    return validate_generator(result)


@dataclass(frozen=True)
class BranchSample:
    initial_state: int
    latent_at_u: int
    terminal_state: int
    observation: int
    stream_addresses: tuple[str, ...]


@dataclass(frozen=True)
class JointProductSample:
    record_id: bytes
    context: ConditionalContext
    reverse_time: float
    horizon: float
    population_sha256: str
    branch_one: BranchSample
    branch_two: BranchSample

    @property
    def joint_pair(self):
        return self.branch_one.latent_at_u, self.branch_one.observation

    @property
    def product_pair(self):
        return self.branch_one.latent_at_u, self.branch_two.observation

    @property
    def model_direct_time(self):
        return self.horizon - self.reverse_time


class _ImmutableAfterConstruction:
    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError("finite population bindings are immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError("finite population bindings are immutable")


class FiniteCandidateBasePopulation(_ImmutableAfterConstruction):
    """Own a context-specific finite candidate generator and observation law."""

    def __init__(self, *, context, generator, initial_law, observation_kernel, horizon,
                 declaration_id):
        if type(context) is not ConditionalContext:
            raise PopulationConstructionError("an explicit ConditionalContext is required")
        if type(declaration_id) is not str or not 1 <= len(declaration_id) <= 256:
            raise PopulationConstructionError("an explicit finite synthetic law declaration is required")
        if type(horizon) is not float or not math.isfinite(horizon) or horizon <= 0:
            raise PopulationConstructionError("horizon must be a positive finite float")
        raw = np.asarray(generator)
        if raw.ndim != 2 or not 1 <= raw.shape[0] <= MAX_FINITE_STATES:
            raise PopulationConstructionError("finite generator size is out of bounds")
        q = validate_generator(raw)
        pi = validate_probability_vector(initial_law, len(q))
        if not (pi > 0).all():
            raise PopulationConstructionError("finite initial law must have full support")
        kernel = np.asarray(observation_kernel)
        if (kernel.dtype.kind not in "iuf" or kernel.ndim != 2
                or kernel.shape[0] != len(q)
                or not 1 <= kernel.shape[1] <= MAX_FINITE_OBSERVATIONS):
            raise PopulationConstructionError("observation kernel must have bounded state-by-observation shape")
        for row in kernel:
            validate_probability_vector(row, kernel.shape[1])
        if not (kernel > 0).all():
            raise PopulationConstructionError("finite observation kernel must have common positive support")
        self.context = context
        self.horizon = horizon
        self.declaration_id = declaration_id
        self.generator = _frozen_array(q)
        self.initial_law = _frozen_array(pi)
        self.observation_kernel = _frozen_array(kernel)
        binding = dict(context=context.record(), horizon=horizon.hex(),
                       declaration_id=declaration_id,
                       generator=self.generator.tolist(), initial_law=self.initial_law.tolist(),
                       observation_kernel=self.observation_kernel.tolist())
        self.population_sha256 = hashlib.sha256(json.dumps(
            binding, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode()).hexdigest()
        self._frozen = True

    def at_time(self, reverse_time):
        if type(reverse_time) is not float or not math.isfinite(reverse_time) or not 0 < reverse_time < self.horizon:
            raise PopulationConstructionError("time must be explicitly supplied inside (0,S)")
        return TimeConditionedFinitePopulation(self, reverse_time)

    def summary(self):
        return dict(
            scope="BOUNDED_FINITE_CANDIDATE_BASE_SYNTHETIC_POPULATION_ONLY",
            population_sha256=self.population_sha256, context=self.context.record(),
            declaration_id=self.declaration_id, stream_namespace=STREAM_NAMESPACE,
            general_learned_hybrid_sampler_implemented=False,
            continuous_observation_sampler_implemented=False,
            production_initial_task_context_time_laws_adopted=False,
            full_open_interval_time_support_verified=False,
            mathematical_iid_random_source_proven=False,
            actual_data_accessed=False, scientific_execution_authorized=False,
        )


class TimeConditionedFinitePopulation(_ImmutableAfterConstruction):
    """Cache finite propagators; draw both complete two-time branches separately."""

    def __init__(self, population, reverse_time):
        if type(population) is not FiniteCandidateBasePopulation:
            raise PopulationConstructionError("an exact finite population is required")
        if type(reverse_time) is not float or not math.isfinite(reverse_time) or not 0 < reverse_time < population.horizon:
            raise PopulationConstructionError("time must be explicitly supplied inside (0,S)")
        self.population = population
        self.reverse_time = reverse_time
        self.initial_to_u = _frozen_array(transition_matrix(population.generator, reverse_time))
        self.u_to_terminal = _frozen_array(transition_matrix(
            population.generator, population.horizon - reverse_time))
        self._frozen = True

    def joint_product_tables(self):
        p = self.population
        marginal_u = p.initial_law @ self.initial_to_u
        conditional_observation = self.u_to_terminal @ p.observation_kernel
        joint = marginal_u[:, None] * conditional_observation
        observation_marginal = joint.sum(axis=0)
        product = marginal_u[:, None] * observation_marginal[None, :]
        return dict(joint_mass=_frozen_array(joint), product_mass=_frozen_array(product),
                    optimal_logit=_frozen_array(np.log(joint) - np.log(product)))

    def _stream(self, run_seed, record_id, draw_ordinal, branch, role):
        p = self.population
        key = dict(namespace=STREAM_NAMESPACE, population_sha256=p.population_sha256,
                   context=p.context.record(), run_seed=run_seed, record_id_hex=record_id.hex(),
                   draw_ordinal=draw_ordinal, reverse_time=self.reverse_time.hex(),
                   branch=branch, role=role)
        digest = hashlib.sha256(json.dumps(key, sort_keys=True, separators=(",", ":")).encode()).digest()
        return np.random.Generator(np.random.PCG64(int.from_bytes(digest, "big"))), digest.hex()

    def sample(self, *, run_seed, record_id, draw_ordinal=0):
        _uint64(run_seed, "run_seed")
        _identifier(record_id, "record_id")
        _uint64(draw_ordinal, "draw_ordinal")
        p = self.population
        branches = []
        for branch in (1, 2):
            addresses = []
            def categorical(probabilities, role):
                rng, address = self._stream(run_seed, record_id, draw_ordinal, branch, role)
                addresses.append(address)
                return int(rng.choice(len(probabilities), p=probabilities))
            initial = categorical(p.initial_law, "initial")
            latent = categorical(self.initial_to_u[initial], "propagate-to-u")
            terminal = categorical(self.u_to_terminal[latent], "propagate-to-S")
            observation = categorical(p.observation_kernel[terminal], "terminal-observation")
            branches.append(BranchSample(initial, latent, terminal, observation, tuple(addresses)))
        return JointProductSample(record_id, p.context, self.reverse_time, p.horizon,
                                  p.population_sha256, branches[0], branches[1])
