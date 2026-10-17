"""CPU-only actual hybrid sampler/neural learner vs an independent fiber law.

The analytic control has the exact capped h and conditioned initial law, but
uses the project's unchanged approximate hybrid integrator. The neural routes
use a zero neural BASE, actual paired training, guide/residual initialization,
and the same integrator. They are NOT exact conditioning of the training grid.
All routes and budgets are fixed before running; no retry or sample filtering.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    ContinuousFiberConditionalBenchmark, ContinuousFiberSpec,
)

METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
CDF_GRID = tuple(float(x) for x in np.linspace(-3., 3., 21))
SCHEMA = 'mixed-continuous-neural-benchmark-v1'


@dataclass(frozen=True)
class BenchmarkBudget:
    oracle_draws: int = 2048
    neural_draws: int = 64
    conditional_steps: int = 8
    pairs_per_step: int = 2
    maximum_seconds: int = 600

    def __post_init__(self):
        caps = (8192, 256, 32, 4, 1200)
        for (name, value), cap in zip(vars(self).items(), caps):
            if type(value) is not int or not 1 <= value <= cap:
                raise ValueError(f'{name} must be an integer in 1..{cap}')


def _fixture(method=METHODS[0]):
    import torch
    from heterodiff.data.two_domain_factorized_state import (
        FactoredEvent, FactorizedMetadataReference, PhysioStateKey,
        TrainInformedMetadataReference,
    )
    from heterodiff.experiments.factorized_conditional_pipeline import FactorizedPopulationContext
    from heterodiff.experiments.factorized_conditional_training import FactorizedConditionalModel
    from heterodiff.experiments.factorized_device_training import DeviceFactorizedConditionalModel
    from heterodiff.models.factorized_configuration_energy_torch import (
        BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
    )
    from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
    from heterodiff.processes.factorized_hybrid_sampler import (
        ExactFactorizedReference, FactorizedSamplerLimits, FactorizedSchedule,
    )
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle

    key = PhysioStateKey(3, 'HR', 'POSITIVE')
    q = TrainInformedMetadataReference(FactorizedMetadataReference('R3-PHYS'),
        (FactoredEvent(key, .2),), beta=Fraction(1, 4))
    rho = float(q.mass(key).as_fraction())
    spec = ContinuousFiberSpec(theta=.8, type_probabilities=(1.-rho, rho),
        death_rate=1., continuous_rate=1., horizon=1., observation_sd=.5,
        contamination=.1, observation_value=.7)
    independent = ContinuousFiberConditionalBenchmark(spec)
    oracle = FactorizedSmoothOracle(q, AmendmentParameters(
        reference_count_mean=.8, reference_cap=1, observation_cap=1,
        death_rate=1., target_contamination=.1, target_log_value_sd=.25,
        observation_contamination=.1, observation_log_value_sd=.5))
    schedule = FactorizedSchedule(1., 0., 1., 1.)
    reference = ExactFactorizedReference(oracle, schedule, FactorizedSamplerLimits(
        maximum_events=1, maximum_jump_candidates=20000, maximum_initialization_trials=1024))
    arch = FactorizedEnergyArchitecture('CONTINUOUS_FIBER_NEURAL_V1', 1, 1., .25, 1., 1.,
        FactorizedEnergyLimits(4, 16, 2048, 16384))
    cpu_base = BoundedFactorizedConfigurationEnergy(arch, initialization_seed=101)
    with torch.no_grad():
        for parameter in cpu_base.parameters():
            parameter.zero_()
    base = DeviceFactorizedEnergy.from_cpu(cpu_base, 'cpu')
    cpu_model = FactorizedConditionalModel(
        BoundedFactorizedConfigurationEnergy(arch, initialization_seed=102),
        guide=FactorizedAssociationGuide(oracle), method_id=method, clean_hold=0.,
        remaining_clocks=schedule.remaining_clocks, observation_seed=103, nuisance_seed=104,
        residual_gate_policy='LINEAR_ACTIVE_TIME_V1')
    model = DeviceFactorizedConditionalModel.from_cpu(cpu_model, 'cpu')
    context = FactorizedPopulationContext('R3-PHYS', SCHEMA, b'invented-observation', (0.,)*64)
    return reference, independent, key, base, model, context, (FactoredEvent(key, .7),)


def category(state, key):
    if len(state) > 1:
        raise ValueError('the independent target covers cap one only')
    return 'EMPTY' if not state else ('CONTINUOUS' if state[0].key == key else 'OTHER')


def materialize(law, rng, reference, key):
    """Materialize OTHER using the real key/fiber law, never a synthetic key."""
    from heterodiff.data.two_domain_factorized_state import FactoredEvent
    label, coordinate = law.sample(rng)
    if label == 'EMPTY':
        return ()
    if label == 'CONTINUOUS':
        return (FactoredEvent(key, float(coordinate)),)
    if label != 'OTHER':
        raise ValueError('unknown independent state category')
    for _ in range(1024):
        event = reference.reference.sample_event(rng)
        if event.key != key:
            return (event,)
    raise RuntimeError('OTHER conditional-key draw budget exhausted; no fallback or discarded path')


class IndependentHPotential:
    """Exact capped backward likelihood, not the production association guide."""
    def __init__(self, oracle, key):
        self.oracle, self.key = oracle, key
        s = oracle.spec
        if s.potential != (0., 0., 0.):
            raise ValueError('this actual-sampler control requires zero BASE potential')
        constant = s.contamination * math.exp(-1.) * s.type_probabilities[1] * (
            math.exp(-.5*s.observation_value**2)/math.sqrt(2.*math.pi))
        self._upper = math.log(constant + (1.-s.contamination)*.5 /
                               (math.sqrt(2.*math.pi)*s.observation_sd))

    def _args(self, state):
        label = category(state, self.key)
        return label, state[0].coordinate if label == 'CONTINUOUS' else None

    def value(self, u, state):
        label, coordinate = self._args(state)
        return math.log(self.oracle.backward_likelihood(u, label, coordinate))

    def value_grad(self, u, state):
        label, coordinate = self._args(state)
        result = self.oracle.log_likelihood_derivatives(u, label, coordinate)
        gradient = result['gradient'] if label == 'CONTINUOUS' else 0.
        return result['log_likelihood'], tuple(
            (gradient,) if event.coordinate is not None else () for event in state)

    @property
    def upper_value_bound(self):
        return self._upper


def discrepancy(states, key, target, *, family_alpha=.01, route_count=5):
    """Finite indicator-grid error, NOT empirical total variation or KL.

    A union Hoeffding bound covers 3 category + 21 joint-CDF indicators on all
    five predeclared routes under ideal independent route draws. The finite
    keyed PRNG implementation is not itself a proof of statistical independence.
    """
    if not states:
        raise ValueError('nonempty complete draw roster required')
    labels = [category(state, key) for state in states]
    n = len(states)
    probabilities = [labels.count(label)/n for label in ('EMPTY', 'OTHER', 'CONTINUOUS')]
    coordinates = [state[0].coordinate for state, label in zip(states, labels) if label == 'CONTINUOUS']
    empirical = [sum(value <= x for value in coordinates)/n for x in CDF_GRID]
    expected = [float(target.continuous_cdf(x)) for x in CDF_GRID]
    error = max(abs(a-b) for a, b in zip(probabilities, target.state_probabilities))
    cdf_error = max(abs(a-b) for a, b in zip(empirical, expected))
    width = math.sqrt(math.log(2.*(3+len(CDF_GRID))*route_count/family_alpha)/(2.*n))
    mean, variance = target.continuous_moments()
    return {
        'draw_count': n, 'observed_key_draw_count': len(coordinates),
        'category_probabilities': probabilities,
        'target_category_probabilities': list(target.state_probabilities),
        'maximum_category_error': error, 'joint_cdf_grid': list(CDF_GRID),
        'joint_cdf_empirical': empirical, 'joint_cdf_target': expected,
        'maximum_joint_cdf_grid_error': cdf_error,
        'simultaneous_indicator_error_bound': width,
        'family_alpha': family_alpha, 'family_route_count': route_count,
        'finite_indicator_discrepancy_within_bound': max(error, cdf_error) <= width,
        'bound_assumption': 'IDEAL_INDEPENDENT_DRAWS_FOR_EACH_ROUTE_AND_FIXED_INDICATORS',
        'bound_is_sampling_error_around_own_route_not_a_total_bias_bound': True,
        'oracle_comparison_interpretation': 'FINITE_INDICATOR_NULL_CHECK_NOT_ACCURACY_CERTIFICATION',
        'posterior_accuracy_proved': False, 'continuous_TV_or_KL_estimated': False,
        'coordinate_mean_descriptive': float(np.mean(coordinates)) if coordinates else None,
        'coordinate_variance_descriptive': float(np.var(coordinates)) if coordinates else None,
        'target_coordinate_mean': float(mean), 'target_coordinate_variance': float(variance),
    }


def run_benchmark(budget=BenchmarkBudget()):
    import torch
    from heterodiff.experiments.factorized_common_grid_pipeline import (
        CommonGridDeviceFactorizedBasePopulation,
        common_grid_sample_conditional, common_grid_train_conditional_step,
    )
    from heterodiff.experiments.factorized_device_qualification import _optimizer
    from heterodiff.experiments.finite_conditional_learning_benchmark import _cpu_policy
    from heterodiff.processes.factorized_hybrid_sampler import LearnedFactorizedSampler

    if type(budget) is not BenchmarkBudget:
        raise ValueError('exact benchmark budget required')
    started = time.monotonic()
    def check():
        if time.monotonic()-started > budget.maximum_seconds:
            raise TimeoutError('bounded CPU benchmark deadline exceeded; no partial success')
    routes = []
    with _cpu_policy(torch):
        ref, independent, key, _, _, _, _ = _fixture()
        target = independent.terminal_posterior()
        initial = independent.conditioned_initial()
        rng = np.random.default_rng(7301)
        direct = []
        for _ in range(budget.oracle_draws):
            check()
            direct.append(materialize(target, rng, ref, key))
        routes.append({'route': 'independent-posterior-iid-control',
                       'metrics': discrepancy(direct, key, target)})
        for steps in (4, 16):
            grid = tuple(float(x) for x in np.linspace(0., 1., steps+1))
            sampler = LearnedFactorizedSampler(ref, IndependentHPotential(independent, key), grid,
                initializer=lambda rng: materialize(initial, rng, ref, key))
            samples, births, deaths = [], 0, 0
            begun = time.monotonic()
            for i in range(budget.oracle_draws):
                check()
                path = sampler.sample_path(run_seed=7302, record_id=(
                    f'independent-h-grid-{steps}-draw-{i}').encode())
                samples.append(path.terminal_state)
                births += path.diagnostics['accepted_birth']
                deaths += path.diagnostics['accepted_death']
            routes.append({'route': f'actual-sampler-independent-h-grid-{steps}',
                'grid': list(grid), 'exact_capped_h': True, 'exact_conditioned_initial_law': True,
                'exact_continuous_path_claimed': False, 'accepted_births': births,
                'accepted_deaths': deaths, 'elapsed_seconds': time.monotonic()-begun,
                'metrics': discrepancy(samples, key, target)})
        grid = tuple(float(x) for x in np.linspace(0., 1., 9))
        for method in METHODS:
            check()
            ref, _, key, base, model, context, observed = _fixture(method)
            population = CommonGridDeviceFactorizedBasePopulation(base, ref, grid, context)
            optimizer = _optimizer(model)
            updates = []
            begun = time.monotonic()
            for step in range(budget.conditional_steps):
                check()
                updates.append(common_grid_train_conditional_step(model, population,
                    optimizer=optimizer, run_seed=7303, record_id=f'train-{step}'.encode(),
                    sample_count=budget.pairs_per_step))
            samples = []
            for i in range(budget.neural_draws):
                check()
                samples.append(common_grid_sample_conditional(base, model, ref, grid, context,
                    observed, run_seed=7304, record_id=f'evaluate-{i}'.encode(),
                    expected_population_law_id=population.law_id).terminal_state)
            routes.append({'route': 'actual-neural-'+method, 'method': method,
                'grid': list(grid), 'updates': updates, 'population': population.snapshot_binding(),
                'base_neural_parameters_all_zero_and_frozen': True,
                'base_model_trained_in_this_comparison': False,
                'sampler_initializer': (
                    'UNCAPPED_FUTURE_REFERENCE_GUIDE_CONDITIONED_AT_INITIAL_CAP_PLUS_RESIDUAL'
                    if method == METHODS[0] else
                    'ZERO_CLOCK_OBSERVATION_BASELINE_CONDITIONED_AT_INITIAL_CAP_PLUS_RESIDUAL'),
                'combined_learning_reference_initialization_interpolation_and_numerical_error': True,
                'elapsed_seconds': time.monotonic()-begun,
                'metrics': discrepancy(samples, key, target)})
        check()
    return {'schema_version': SCHEMA, 'decision': 'MIXED_CONTINUOUS_BENCHMARK_COMPLETE_REVIEW_METRICS',
        'budget': asdict(budget), 'seed_roster': [7301, 7302, 7303, 7304],
        'independent_spec': asdict(independent.spec), 'routes': routes,
        'elapsed_seconds': time.monotonic()-started,
        'environment': {'python': platform.python_version(), 'torch': torch.__version__,
                        'numpy': np.__version__, 'device': 'cpu'},
        'scope': {'synthetic_only': True, 'actual_mixed_neural_models_used': True,
            'actual_hybrid_sampler_used': True, 'target_independent_of_neural_and_guide_code': True,
            'cap_one_benchmark_not_general_carrier_theorem': True,
            'exact_Bayes_target_of_numerical_training_population_claimed': False,
            'full_posterior_or_statistical_superiority_claimed': False,
            'real_data_accessed': False, 'F105_executed': False, 'GPU_requested': False,
            'cloud_or_paid_job_launched': False, 'packages_installed': False,
            'retries': 0, 'discarded_failed_samples': 0, 'resumable_checkpoint_created': False}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new JSON file; never overwritten')
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error('output must be absent beneath an existing directory')
    if not args.child:
        command = [sys.executable, '-m', __name__ if __name__ != '__main__' else
            'heterodiff.experiments.mixed_continuous_conditional_benchmark',
            '--output', str(args.output.resolve()), '--child']
        try:
            return subprocess.run(command, check=False, timeout=BenchmarkBudget().maximum_seconds).returncode
        except subprocess.TimeoutExpired:
            print('CPU benchmark timed out; child terminated; no success claimed', file=sys.stderr)
            return 2
    result = run_benchmark()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'decision': result['decision'], 'route_count': len(result['routes']),
                      'elapsed_seconds': result['elapsed_seconds'], 'output': str(args.output)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
