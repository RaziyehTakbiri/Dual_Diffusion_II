"""Finite-state population-risk benchmark with an independent posterior target.

This is an atomic special-case mechanism experiment, not the existing mixed
neural learner, a Monte Carlo generalization study or a continuous-path theorem.
The three scenarios, all observation branches, checkpoints and optimizer are
declared before running. No method is selected based on the resulting scores.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
from scipy.linalg import expm

from heterodiff.evaluation.finite_conditional_benchmark import (
    FiniteBenchmarkSpec, FiniteConditionalBenchmark,
)

GRID = (0., .25, .5, .75, 1.)
SCENARIOS = (
    ('weak-base-tilt-low-cap-pressure', .4, .1),
    ('strong-base-tilt-low-cap-pressure', .4, 1.),
    ('strong-base-tilt-high-cap-pressure', 2.5, 1.),
)
METHODS = ('guide-only', 'association-aware-guide-plus-residual', 'unified-direct-conditioner')
RESIDUAL_BOUND = 4.
OPTIMIZER = {'lr': .001, 'betas': (.9, .999), 'eps': 1e-8, 'weight_decay': 0.,
             'foreach': False, 'fused': False, 'amsgrad': False,
             'maximize': False, 'capturable': False, 'differentiable': False}


@contextmanager
def _cpu_policy(torch):
    old_threads = torch.get_num_threads()
    old_det = torch.are_deterministic_algorithms_enabled()
    old_warn = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        yield
    finally:
        torch.use_deterministic_algorithms(old_det, warn_only=old_warn)
        torch.set_num_threads(old_threads)


def conditional_distribution(oracle, observation, likelihoods, grid=GRID):
    """Exact finite summation of the normalized-twist approximation.

    Terminal h is required to equal g. Nuisance offsets are excluded. The
    initial law and every transition row are explicitly normalized; this is
    not claimed to be the target Doob law when h is not backward-harmonic.
    """
    h = np.asarray(likelihoods, dtype=np.float64)
    if h.shape != (len(grid), len(oracle.states)) or not np.isfinite(h).all() or np.min(h) <= 0:
        raise ValueError('one positive finite likelihood per grid state is required')
    if tuple(grid) != GRID:
        raise ValueError('this benchmark uses the declared common fixed grid')
    if not np.array_equal(h[-1], oracle.observation_likelihood(observation)):
        raise ValueError('terminal likelihood must be exactly the observation channel')
    normalizer = float(oracle.prior @ h[0])
    if not math.isfinite(normalizer) or normalizer <= 0:
        raise ValueError('initial likelihood normalizer is not representable')
    initial = oracle.prior * h[0] / normalizer
    law = initial.copy()
    defects = []
    transitions = []
    for i, (start, end) in enumerate(zip(grid, grid[1:])):
        kernel = oracle.transition(end - start)
        row_normalizer = kernel @ h[i+1]
        if not np.isfinite(row_normalizer).all() or np.min(row_normalizer) <= 0:
            raise ValueError('transition likelihood normalizer is not representable')
        transition = kernel * h[i+1][None, :] / row_normalizer[:, None]
        if not np.isfinite(transition).all() or not np.allclose(transition.sum(axis=1), 1., atol=1e-12, rtol=0):
            raise ArithmeticError('normalized transition is not stochastic')
        law = law @ transition
        transitions.append(transition)
        defects.append(np.log(row_normalizer) - np.log(h[i]))
    e = float(sum(np.max(np.abs(d)) for d in defects))
    # This conservative finite-grid path bound is deliberately distinct from
    # a classifier-risk or continuous hybrid-diffusion bound.
    bound = 1. if e >= .5 * math.log(3.) else .5 * math.expm1(2. * e)
    return law, {'initial': initial, 'transitions': transitions,
                 'harmonic_defects': np.array(defects), 'harmonic_defect_sum_sup': e,
                 'path_and_terminal_TV_upper_bound': bound, 'initial_normalizer': normalizer}


def _metrics(oracle, observation, h):
    predicted, diagnostics = conditional_distribution(oracle, observation, h)
    target = oracle.terminal_posterior(observation)
    tv = float(.5 * np.abs(predicted-target).sum())
    kl = float(np.sum(target * np.log(target/predicted)))
    if tv > diagnostics['path_and_terminal_TV_upper_bound'] + 2e-12:
        raise ArithmeticError('computed TV violates the finite-grid defect bound')
    return {'terminal_TV': tv, 'terminal_KL_target_to_approximation': max(0., kl),
            'terminal_KL_unrounded': kl,
            'predicted_terminal_distribution': predicted.tolist(),
            'harmonic_defect_sum_sup': diagnostics['harmonic_defect_sum_sup'],
            'path_and_terminal_TV_upper_bound': diagnostics['path_and_terminal_TV_upper_bound']}


def gate_boundary_diagnostic():
    """A two-state counterexample to generally bounded cubic-gate residuals."""
    q = np.array([[-2., 2.], [1., -1.]])
    qref = np.array([[-1., 1.], [1., -1.]])
    g = np.array([.2, .8])
    first_order = (q-qref) @ g / g
    rows = []
    for tau in (1e-1, 1e-2, 1e-3, 1e-4, 1e-5):
        correction = np.log(expm(tau*q) @ g) - np.log(expm(tau*qref) @ g)
        rows.append({'remaining_time': tau,
                     'linear_scaled_correction': (correction/tau).tolist(),
                     'cubic_scaled_correction': (correction/tau**3).tolist()})
    return {'scope': 'TWO_STATE_FINITE_GENERATOR_COUNTEREXAMPLE',
            'first_order_limit': first_order.tolist(), 'rows': rows,
            'legacy_gate_changed': False, 'global_linear_gate_realizability_claimed': False}


def _case(oracle, observation, steps, check):
    import torch
    from torch.nn import functional as F

    started = time.monotonic()
    target_h = np.array([oracle.backward_likelihood(t, observation) for t in GRID])
    target_h[-1] = oracle.observation_likelihood(observation)
    evidence = oracle.evidence(observation)
    marginals = np.array([oracle.marginal(t) for t in GRID[:-1]])
    positive = marginals * target_h[:-1] / evidence
    if not np.allclose(positive.sum(axis=1), 1., atol=2e-12, rtol=0):
        raise ArithmeticError('all time slices must share one terminal evidence')
    joint = torch.tensor(positive, dtype=torch.float64, device='cpu')
    product = torch.tensor(marginals, dtype=torch.float64, device='cpu')
    gate = torch.tensor([(1.-t) for t in GRID[:-1]], dtype=torch.float64, device='cpu')[:, None]
    guide = np.array([[oracle.uncapped_reference_likelihood(state, 1.-t, observation)
                       for state in oracle.states] for t in GRID])
    guide[-1] = target_h[-1]
    capped = np.array([oracle.capped_reference_likelihood(1.-t, observation) for t in GRID])
    direct = np.tile(target_h[-1], (len(GRID), 1))

    def loss(logit):
        return .5 * torch.mean(torch.sum(joint * F.softplus(-logit) + product * F.softplus(logit), dim=1))

    optimum = float(loss(torch.tensor(np.log(target_h[:-1]/evidence), dtype=torch.float64)))
    oracle_check = _metrics(oracle, observation, target_h)
    if oracle_check['terminal_TV'] > 2e-12:
        raise ArithmeticError('oracle Doob propagation does not recover independent posterior')
    curves = {'guide-only': [{'step': 0, **_metrics(oracle, observation, guide)}]}
    work = {}
    checkpoints = sorted({0, steps, *(s for s in (32, 128, 512, 2048) if s <= steps)})
    for method, baseline in ((METHODS[1], guide), (METHODS[2], direct)):
        check()
        train_start = time.monotonic()
        # Saturated, observation-specific finite table. This isolates the
        # mechanism from byte encoders and finite-sample generalization.
        residual = torch.nn.Parameter(torch.zeros_like(joint))
        nuisance = torch.nn.Parameter(torch.zeros((), dtype=torch.float64, device='cpu'))
        optimizer = torch.optim.AdamW([residual, nuisance], **OPTIMIZER)
        baseline_log = torch.tensor(np.log(baseline[:-1]), dtype=torch.float64, device='cpu')
        snapshots = []
        snapshot_time = 0.
        for step in range(steps+1):
            check()
            physical_log = baseline_log + gate * RESIDUAL_BOUND * torch.tanh(residual)
            objective = loss(physical_log+nuisance)
            if not bool(torch.isfinite(objective)):
                raise ArithmeticError('nonfinite population objective')
            if step in checkpoints:
                eval_start = time.monotonic()
                h = np.vstack((np.exp(physical_log.detach().numpy()), target_h[-1]))
                snapshots.append({'step': step, 'population_logistic_loss': float(objective.detach()),
                    'unrestricted_optimum_loss': optimum,
                    'population_logistic_excess': max(0., float(objective.detach())-optimum),
                    'observation_only_nuisance': float(nuisance.detach()),
                    'maximum_absolute_ungated_residual': float((RESIDUAL_BOUND*torch.tanh(residual)).abs().max().detach()),
                    **_metrics(oracle, observation, h)})
                snapshot_time += time.monotonic()-eval_start
            if step == steps:
                break
            optimizer.zero_grad(set_to_none=True)
            objective.backward()
            optimizer.step()
        curves[method] = snapshots
        work[method] = {'optimizer_updates': steps,
            'population_class_state_terms_per_update': 2*len(GRID[:-1])*len(oracle.states),
            'optimizer_update_population_class_state_terms': steps*2*len(GRID[:-1])*len(oracle.states),
            'objective_evaluations_including_final_diagnostic': steps+1,
            'all_objective_evaluation_population_class_state_terms': (steps+1)*2*len(GRID[:-1])*len(oracle.states),
            'work_count_scope': 'LEARNED_OBJECTIVE_ONLY_ORACLE_PREPARATION_AND_LAW_EVALUATION_SEPARATE',
            'train_and_checkpoint_evaluation_seconds': time.monotonic()-train_start,
            'checkpoint_evaluation_seconds': snapshot_time,
            'trainable_scalars': residual.numel()+nuisance.numel()}
    return {'observation': list(observation) if observation is not None else 'OVERFLOW',
        'evidence': evidence, 'target_terminal_distribution': oracle.terminal_posterior(observation).tolist(),
        'exact_oracle_control': oracle_check,
        'uncapped_vs_capped_reference_max_abs': float(np.max(np.abs(guide-capped))),
        'uncapped_reference_vs_toy_base_max_abs': float(np.max(np.abs(guide-target_h))),
        'curves': curves, 'work': work,
        'case_seconds_including_preparation_and_evaluation': time.monotonic()-started}


def run_benchmark(*, steps=2048, maximum_seconds=120):
    if type(steps) is not int or not 1 <= steps <= 2048:
        raise ValueError('steps must be an integer between 1 and 2048')
    if type(maximum_seconds) is not int or not 1 <= maximum_seconds <= 300:
        raise ValueError('maximum_seconds must be an integer between 1 and 300')
    started = time.monotonic()
    import scipy
    import torch

    def check():
        if time.monotonic()-started > maximum_seconds:
            raise TimeoutError('finite conditional benchmark exceeded its CPU time budget')

    results = []
    with _cpu_policy(torch):
        for name, theta, scale in SCENARIOS:
            spec = FiniteBenchmarkSpec(theta=theta)
            states = FiniteConditionalBenchmark(spec).states
            potential = [scale*(.35*a-.2*b+.15*a*b) for a, b in states]
            oracle = FiniteConditionalBenchmark(spec, potential=potential)
            cases = []
            for observation in oracle.observations:
                check()
                cases.append(_case(oracle, observation, steps, check))
            results.append({'scenario': name, 'specification': spec.to_dict(),
                'states': [list(s) for s in states], 'base_potential': potential,
                'initial_prior': oracle.prior.tolist(), 'base_generator': oracle.generator.tolist(),
                'cases': cases})
    check()
    return {'schema_version': 'heterodiff-finite-conditional-learning-benchmark-v1',
        'decision': 'FINITE_CONDITIONAL_BENCHMARK_COMPLETED_NOT_FULL_MODEL_QUALIFICATION',
        'contract': 'COMMON_FIXED_GRID_LINEAR_GATE_NORMALIZED_TWIST_V2',
        'grid': list(GRID), 'steps_per_learned_route': steps, 'maximum_seconds': maximum_seconds,
        'methods': list(METHODS), 'residual_bound': RESIDUAL_BOUND,
        'optimizer': {'name': 'AdamW', **OPTIMIZER},
        'training': 'EXACT_FINITE_POPULATION_RISK_OBSERVATION_SPECIFIC_FP64_TABLES',
        'scenario_count': len(results), 'observation_case_count': sum(len(s['cases']) for s in results),
        'results': results, 'gate_boundary_diagnostic': gate_boundary_diagnostic(),
        'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                     'scipy': scipy.__version__, 'torch': torch.__version__},
        'elapsed_seconds': time.monotonic()-started,
        'scope': {'synthetic_only': True, 'cpu_only': True, 'population_risk_not_sample_generalization': True,
                  'finite_matrix_reference_not_exact_arithmetic': True, 'fixed_toy_BASE_not_trained_BASE': True,
                  'two_domain_neural_learner_qualified': False, 'continuous_fiber_or_Heun_qualified': False,
                  'legacy_gate_or_objective_changed': False, 'paid_or_gpu_jobs_launched': False,
                  'F105_or_real_data_used': False, 'method_superiority_preasserted': False}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--steps', type=int, default=2048)
    parser.add_argument('--maximum-seconds', type=int, default=120)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError('choose an absent output JSON file')
        if not args.output.parent.is_dir():
            raise ValueError('output parent must already exist')
        if not 1 <= args.steps <= 2048 or not 1 <= args.maximum_seconds <= 300:
            raise ValueError('steps or deadline outside supported bounds')
        if not args.worker:
            return subprocess.run([sys.executable, '-m', __spec__.name,
                '--worker', '--output', str(args.output.absolute()), '--steps', str(args.steps),
                '--maximum-seconds', str(args.maximum_seconds)],
                check=False, timeout=args.maximum_seconds).returncode
        result = run_benchmark(steps=args.steps, maximum_seconds=args.maximum_seconds)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
        print(json.dumps({'decision': result['decision'], 'output': str(args.output),
                          'observation_cases': result['observation_case_count']}))
        return 0
    except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired) as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
