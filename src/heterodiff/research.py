"""Portable, CPU-only synthetic train/sample/evaluate entry point.

This is a reader demonstration of the existing numerical learner, not the full
paper experiment, a Bayes-consistency claim, or a replacement GPU qualification.
``inspect`` needs only the standard library. ``run`` supervises one fresh child
with a wall-clock deadline and writes only to an explicitly supplied new folder.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from fractions import Fraction
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from heterodiff.research_config import (
    FIXED_OPTIMIZER_POLICY, ResearchConfig, canonical_config_json, config_sha256, load_config,
)

GRID = (0., .25, .5, .75, 1.)
FIXTURE_VERSION = 'reader-two-domain-invented-fixture-v1'


def _seed(seed, label):
    return int.from_bytes(hashlib.sha256(seed.to_bytes(8, 'big') + label.encode()).digest()[:8], 'big')


def _json(path, value):
    # Exclusive creation: existing output is never replaced by a repeated run.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


@contextmanager
def _cpu_policy(torch):
    threads = torch.get_num_threads()
    deterministic = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True, warn_only=False)
        yield
    finally:
        torch.use_deterministic_algorithms(deterministic, warn_only=warn)
        torch.set_num_threads(threads)


def _fixture(config, method):
    """Two explicit factories; not yet an arbitrary-domain plug-in interface."""
    from heterodiff.data.two_domain_factorized_state import (
        FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
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

    if config.domain == 'R3-PHYS':
        atomic = FactoredEvent(PhysioStateKey(3, 'MechVent', 'ATOMIC', Fraction(1)))
        continuous = FactoredEvent(PhysioStateKey(3, 'HR', 'POSITIVE'), .2)
    else:
        def key(branch):
            return RetailStateKey('C123456', 'sku', 'name', -1, (2010, 1, 2, 3, 4, 5, 6), 'UK', branch)
        atomic, continuous = FactoredEvent(key('ZERO')), FactoredEvent(key('NEGATIVE'), .2)
    source = (atomic, continuous, continuous)  # Duplicate occurrences are deliberate.
    q = TrainInformedMetadataReference(FactorizedMetadataReference(config.domain), source, beta=Fraction(1, 4))
    oracle = FactorizedSmoothOracle(q, AmendmentParameters(.5, 4, 4, .2, .1, .25, .25, 1.))
    schedule = FactorizedSchedule(1., .25, .5, 1.)
    reference = ExactFactorizedReference(oracle, schedule,
        FactorizedSamplerLimits(maximum_jump_candidates=20000, maximum_initialization_trials=256))
    architecture = FactorizedEnergyArchitecture(FIXTURE_VERSION + ':' + config.domain,
        4, 1., .25, 1., 1., FactorizedEnergyLimits(4, 16, 2048, 16384))
    base = DeviceFactorizedEnergy.from_cpu(BoundedFactorizedConfigurationEnergy(
        architecture, initialization_seed=_seed(config.seed, 'base-initialization')), 'cpu')
    prototype = FactorizedConditionalModel(BoundedFactorizedConfigurationEnergy(
        architecture, initialization_seed=_seed(config.seed, 'conditional-initialization')),
        guide=FactorizedAssociationGuide(oracle), method_id=method, clean_hold=.25,
        remaining_clocks=schedule.remaining_clocks,
        observation_seed=_seed(config.seed, 'observation-encoder'),
        nuisance_seed=_seed(config.seed, 'nuisance'))
    model = DeviceFactorizedConditionalModel.from_cpu(prototype, 'cpu')
    context = FactorizedPopulationContext(config.domain, FIXTURE_VERSION, b'reader-synthetic-context', (0.,)*64)
    return source, reference, base, model, context


def _state(state):
    if state is None:
        return {'overflow': True, 'events': None}
    return {'overflow': False, 'events': [
        {'key_utf8': e.key.canonical_bytes().decode('utf-8'),
         'log_magnitude': e.coordinate, 'log_magnitude_hex': None if e.coordinate is None else e.coordinate.hex()}
        for e in state]}


def descriptive_evaluation(samples, source):
    """Tiny-sample summaries, NOT F105 or a conditional-distribution estimate."""
    if not samples:
        raise ValueError('at least one generated configuration is required')
    counts = [len(state) for state in samples]
    continuous_counts = [sum(e.coordinate is not None for e in state) for state in samples]
    coordinates = [e.coordinate for state in samples for e in state if e.coordinate is not None]
    source_continuous = sum(e.coordinate is not None for e in source)
    return {
        'scope': 'DESCRIPTIVE_SYNTHETIC_SAMPLE_SUMMARY_NOT_F105_OR_SCIENTIFIC_COMPARISON',
        'draw_count': len(samples), 'event_counts': counts,
        'mean_event_count': sum(counts)/len(counts),
        'mean_continuous_event_count': sum(continuous_counts)/len(continuous_counts),
        'empty_configuration_fraction': counts.count(0)/len(counts),
        'mean_log_magnitude_per_continuous_occurrence': sum(coordinates)/len(coordinates) if coordinates else None,
        'invented_source_event_count': len(source),
        'invented_source_continuous_event_count': source_continuous,
        'mean_absolute_count_difference_from_invented_source': sum(abs(n-len(source)) for n in counts)/len(counts),
        'held_out_dataset': False, 'method_superiority_established': False,
    }


def run_experiment(config, output):
    """Execute the CPU demo; direct Python callers receive a soft time budget.

    The public CLI adds a hard child-process deadline. A failed or interrupted
    output directory is retained for diagnosis; it is never a successful result.
    """
    if type(config) is not ResearchConfig:
        raise TypeError('a validated ResearchConfig is required')
    output = Path(output)
    if not output.parent.is_dir():
        raise ValueError('output parent must be an existing directory')
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    _json(output/'config.json', config.to_dict())
    try:
        import numpy as np
        import torch
        from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
        from heterodiff.experiments.factorized_device_training import (
            DeviceFactorizedBasePopulation, device_train_base_step,
            device_train_conditional_step, device_sample_conditional,
        )

        def budget():
            if time.monotonic() - started > config.maximum_seconds:
                raise TimeoutError('synthetic experiment time budget exceeded')

        def optimizer(model):
            policy = dict(FIXED_OPTIMIZER_POLICY)
            policy.pop('name')
            return torch.optim.AdamW(model.parameters(), **policy)

        methods, shared_base_digest = [], None
        with _cpu_policy(torch):
            for method in config.methods:
                budget()
                source, reference, base, model, context = _fixture(config, method)
                base_optimizer, conditional_optimizer = optimizer(base), optimizer(model)
                base_rng = np.random.default_rng(_seed(config.seed, 'base-training'))
                base_history, conditional_history = [], []
                for step in range(config.base_steps):
                    budget()
                    update = device_train_base_step(base, reference, (source,),
                        context=torch.zeros(64, device='cpu'), rng=base_rng, optimizer=base_optimizer,
                        sample_count=config.base_samples, jump_weight=1., precision_policy=config.precision_policy)
                    base_history.append({'step': step + 1, **update})
                base_digest = _parameter_digest(base)
                if shared_base_digest is not None and shared_base_digest != base_digest:
                    raise RuntimeError('method comparison must use identical trained BASE weights')
                shared_base_digest = base_digest
                population = DeviceFactorizedBasePopulation(base, reference, GRID, context,
                    precision_policy=config.precision_policy)
                for step in range(config.conditional_steps):
                    budget()
                    update = device_train_conditional_step(model, population,
                        optimizer=conditional_optimizer, reverse_time=None,
                        run_seed=_seed(config.seed, 'conditional-training'),
                        record_id=('step-' + str(step)).encode(), sample_count=config.conditional_samples)
                    conditional_history.append({'step': step + 1, **update})
                model_digest = _parameter_digest(model)
                # One explicitly invented retained observation. Not a held-out
                # patient/customer; no source access, preprocessing or split.
                observed = (source[-1],)
                paths = []
                for draw in range(config.draws):
                    budget()
                    paths.append(device_sample_conditional(base, model, reference, GRID, context, observed,
                        run_seed=_seed(config.seed, 'conditional-sampling'),
                        record_id=('draw-' + str(draw)).encode(), precision_policy=config.precision_policy))
                budget()
                if _parameter_digest(base) != base_digest or _parameter_digest(model) != model_digest:
                    raise RuntimeError('sampling changed model weights')
                samples = [p.terminal_state for p in paths]
                result = {
                    'method': method, 'base_history': base_history, 'conditional_history': conditional_history,
                    'base_weights_sha256': base_digest, 'conditional_weights_sha256': model_digest,
                    'reference_parameters': asdict(reference.parameters),
                    'reference_schedule': asdict(reference.schedule), 'metadata_train_mixture_beta': '1/4',
                    'architecture': asdict(base.architecture),
                    'source': _state(source), 'observation': _state(observed),
                    'samples': [_state(s) for s in samples],
                    'paths': [{'reverse_grid': p.reverse_grid,
                               'states': [_state(s) for s in p.states],
                               'diagnostics': p.diagnostics} for p in paths],
                    'evaluation': descriptive_evaluation(samples, source),
                    'weights_file': method + '.weights.pt',
                    'weights_are_not_a_resume_checkpoint': True,
                    'conditional_objective': 'NUMERICAL_QUERY_REFINED_JOINT_PRODUCT_LOGISTIC_RISK',
                    'exact_conditional_law_recovery_claimed': False,
                }
                with (output/result['weights_file']).open('xb') as stream:
                    torch.save({'schema_version': 'heterodiff-reader-weights-only-v1',
                                'base': base.state_dict(), 'conditional': model.state_dict(),
                                'method': method, 'config': config.to_dict()}, stream)
                _json(output/(method + '.json'), result)
                methods.append({'method': method, 'result_file': method + '.json',
                    'base_steps': len(base_history), 'conditional_steps': len(conditional_history),
                    'draws': len(samples), 'evaluation': result['evaluation']})
        budget()
        report = {
            'schema_version': 'heterodiff-reader-synthetic-experiment-v1',
            'decision': 'SYNTHETIC_TRAIN_SAMPLE_EVALUATE_COMPLETED',
            'config_sha256': config_sha256(config), 'fixture_version': FIXTURE_VERSION,
            'domain': config.domain, 'methods': methods,
            'identical_trained_base_weights_across_methods': len(methods) > 1,
            'base_weights_sha256': shared_base_digest,
            'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'torch': torch.__version__,
                         'heterodiff': _version('heterodiff')},
            'precision_policy': config.precision_policy, 'optimizer': dict(FIXED_OPTIMIZER_POLICY),
            'elapsed_seconds': time.monotonic() - started,
            'scope': {'synthetic_only': True, 'cpu_only': True, 'paper_results_reproduced': False,
                      'F105_executed': False, 'general_domain_plugin_support': False,
                      'training_resume_supported': False, 'speedup_claimed': False},
        }
        _json(output/'report.json', report)
        return report
    except Exception as error:
        _json(output/'failure.json', {'decision': 'SYNTHETIC_EXPERIMENT_FAILED',
              'error_type': type(error).__name__, 'error': str(error),
              'elapsed_seconds': time.monotonic() - started})
        raise


def _version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'run', '_worker'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.action == 'inspect':
            print(canonical_config_json(config))
            return 0
        if args.output is None:
            parser.error('--output is required for run')
        if args.action == '_worker':
            report = run_experiment(config, args.output)
            print(json.dumps({'decision': report['decision'], 'report': str(args.output/'report.json')}))
            return 0
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError('choose a new output directory; existing results are preserved')
        child = subprocess.run([sys.executable, '-m', 'heterodiff.research', '_worker',
            '--config', str(args.config.resolve()), '--output', str(args.output.absolute())],
            timeout=config.maximum_seconds, check=False)
        return child.returncode
    except (ValueError, TypeError, OSError, subprocess.TimeoutExpired) as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
