"""Predeclared multi-seed CPU mechanism comparison, not a superiority claim.

Two joint scenarios, three seeds, two actual conditional learners and five
analytic controls per scenario. Each complete route is saved; failures abort,
never rerun a seed or discard paths. No checkpoint or setting is selected by
observed evaluation. The exact target remains the cap-one reference submodel.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberConditionalBenchmark
from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import ContinuousFiberInitializationDiagnostic
from heterodiff.evaluation.continuous_multiseed_statistics import route_report, seed_summary, paired_contrast, paired_error_summary
from heterodiff.experiments.mixed_continuous_conditional_benchmark import (
    CDF_GRID, METHODS, IndependentHPotential, _fixture as _previous_fixture, category, materialize,
)

SCHEMA = 'continuous-multiseed-mechanism-comparison-v1'
GRID = tuple(i/8. for i in range(9))
SCENARIOS = (('reference-pressure', .8, .7), ('higher-pressure-shifted-observation', 2.5, 1.4))
SEEDS = (1201, 1202, 1203)
CONTROLS = ('direct-posterior', 'exact-h-exact-initial', 'exact-h-guide-initial',
            'guide-only', 'zero-clock-baseline')


@dataclass(frozen=True)
class ExperimentBudget:
    seeds: tuple = SEEDS
    control_draws: int = 2048
    neural_draws: int = 512
    updates: int = 32
    pairs_per_update: int = 2
    validation_pairs: int = 32
    maximum_seconds: int = 2400

    def __post_init__(self):
        if type(self.seeds) is not tuple or not self.seeds or len(set(self.seeds)) != len(self.seeds) or any(
                type(s) is not int or not 0 <= s < 2**64 for s in self.seeds) or len(self.seeds)>3:
            raise ValueError('one to three distinct uint64 seeds required')
        for name, cap in (('control_draws',2048), ('neural_draws',512), ('updates',32),
                          ('pairs_per_update',4), ('validation_pairs',32), ('maximum_seconds',2400)):
            value = getattr(self,name)
            if type(value) is not int or not 1 <= value <= cap:
                raise ValueError(f'{name} must be an integer in 1..{cap}')


def seed_for(seed, purpose):
    return int.from_bytes(hashlib.sha256(seed.to_bytes(8,'big')+purpose.encode()).digest()[:8],'big')


def specification(budget):
    return {'schema_version':SCHEMA, 'budget':asdict(budget), 'grid':list(GRID),
            'is_default_protocol_run':budget==ExperimentBudget(),
            'scenarios':[{'id':s,'theta':theta,'observation_value':y} for s,theta,y in SCENARIOS],
            'methods':list(METHODS), 'controls':list(CONTROLS),
            'joint_cdf_grid':list(CDF_GRID),
            'process':{'death_rate':1.,'continuous_rate':1.,'horizon':1.,'clean_hold':0.,
                'state_cap':1,'observation_cap':1,'observation_sd':.5,'observation_contamination':.1,
                'selected_key_mass':'COMPUTED_FROM_ACTUAL_REFERENCE_AND_RECORDED_IN_INITIALIZER_DIAGNOSTICS'},
            'seed_derivation':'FIRST_8_BYTES_BIG_ENDIAN_SHA256(UINT64_BIG_ENDIAN_SEED || UTF8_PURPOSE)',
            'seed_purposes':['conditioner','observation-encoder','nuisance','training-paths',
                'validation-times','validation-paths','evaluation-paths'],
            'control_seeds':{'direct':4201,'sampler':4202,'purpose':'scenario_id || control_name'},
            'validation_checkpoints':sorted(set((0,min(8,budget.updates),min(16,budget.updates),budget.updates))),
            'total_route_count':len(SCENARIOS)*(len(CONTROLS)+len(METHODS)*len(budget.seeds)),
            'primary_metric':'MAXIMUM_ABSOLUTE_ERROR_OVER_FIXED_3_CATEGORY_AND_21_JOINT_CDF_INDICATORS',
            'alpha_allocation':{'routes':.005,'seed_mixtures':.0025,'signed_contrasts':.0025},
            'scope':'SYNTHETIC_CAP_ONE_ZERO_BASE_LOCAL_CPU_MECHANISM_ONLY',
            'checkpoint_selection':False,'retry_failed_draws':False,'common_random_numbers_between_methods':False,
            'same_training_pairs_and_initial_tensors_within_seed':True,
            'validation_used_for_model_selection_or_early_stopping':False,
            'factorial_separation_of_theta_and_observation_effects':False,
            'training_seed_population_confidence_claimed':False}


def fixture(scenario, seed, method):
    from heterodiff.data.two_domain_factorized_state import FactoredEvent
    from heterodiff.experiments.factorized_conditional_pipeline import FactorizedPopulationContext
    from heterodiff.experiments.factorized_conditional_training import FactorizedConditionalModel
    from heterodiff.experiments.factorized_device_training import DeviceFactorizedConditionalModel
    from heterodiff.models.factorized_configuration_energy_torch import BoundedFactorizedConfigurationEnergy
    from heterodiff.processes.factorized_hybrid_sampler import ExactFactorizedReference
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    from heterodiff.theory.factorized_smooth_amendment import FactorizedSmoothOracle
    if scenario not in SCENARIOS or method not in METHODS:
        raise ValueError('declared scenario and method required')
    name, theta, y = scenario
    old_ref, previous, key, base, _, _, _ = _previous_fixture(method)
    parameters = replace(old_ref.parameters, reference_count_mean=theta)
    oracle = FactorizedSmoothOracle(old_ref.reference, parameters)
    reference = ExactFactorizedReference(oracle, old_ref.schedule, old_ref.limits)
    independent = ContinuousFiberConditionalBenchmark(replace(previous.spec, theta=theta, observation_value=y))
    model = DeviceFactorizedConditionalModel.from_cpu(FactorizedConditionalModel(
        BoundedFactorizedConfigurationEnergy(base.architecture, initialization_seed=seed_for(seed,'conditioner')),
        guide=FactorizedAssociationGuide(oracle),method_id=method,clean_hold=0.,
        remaining_clocks=reference.schedule.remaining_clocks,
        observation_seed=seed_for(seed,'observation-encoder'),nuisance_seed=seed_for(seed,'nuisance'),
        residual_gate_policy='LINEAR_ACTIVE_TIME_V1'),'cpu')
    context = FactorizedPopulationContext('R3-PHYS',SCHEMA,name.encode(),(0.,)*64)
    return reference, independent, key, base, model, context, (FactoredEvent(key,y),)


class GuideControlPotential:
    """Independent formula for the same uncapped guide (or zero-clock baseline)."""
    def __init__(self, diagnostic, key, *, zero_clock=False):
        self.diagnostic,self.key,self.zero_clock = diagnostic,key,zero_clock
        s = diagnostic.spec
        contamination = s.contamination*math.exp(-1.)*s.type_probabilities[1]*(
            math.exp(-.5*s.observation_value**2)/math.sqrt(2.*math.pi))
        # At most one observed coordinate; its clean density is bounded by the
        # Gaussian peak. This is deliberately not the cap-one retained .5 bound.
        self.upper_value_bound = math.nextafter(math.log(contamination+(1.-s.contamination)/(
            math.sqrt(2.*math.pi)*s.observation_sd)),math.inf)

    def value_grad(self,u,state):
        label = category(state,self.key)
        coordinate = state[0].coordinate if label=='CONTINUOUS' else None
        result = self.diagnostic.uncapped_log_likelihood_derivatives(
            self.diagnostic.spec.horizon if self.zero_clock else u,label,coordinate)
        gradient = result['gradient'] if label=='CONTINUOUS' else 0.
        return result['log_likelihood'],tuple((gradient,) if e.coordinate is not None else () for e in state)

    def value(self,u,state):
        return self.value_grad(u,state)[0]


def indicators(states,key):
    if not states:
        raise ValueError('complete nonempty draw roster required')
    labels = [category(s,key) for s in states]
    coordinates = [s[0].coordinate for s,label in zip(states,labels) if label=='CONTINUOUS']
    n = len(states)
    return [labels.count(label)/n for label in ('EMPTY','OTHER','CONTINUOUS')]+[
        sum(x<=boundary for x in coordinates)/n for boundary in CDF_GRID]


def target_indicators(target):
    return list(target.state_probabilities)+[target.continuous_cdf(x) for x in CDF_GRID]


def validation_pairs(population,seed,count,check):
    rng = np.random.default_rng(seed_for(seed,'validation-times'))
    pairs = []
    for i in range(count):
        check()
        u = population.active_times[int(rng.integers(len(population.active_times)))]
        j,p,_ = population.sample_pair(reverse_time=u,run_seed=seed_for(seed,'validation-paths'),
            record_id=f'held-out-pair-{i}'.encode())
        pairs.append((j,p))
    return pairs


def validation_loss(model,pairs):
    import torch
    from heterodiff.experiments.factorized_conditional_training import FactorizedTrainingBatch
    values = []
    with torch.no_grad():
        for start in range(0,len(pairs),4):
            batch = pairs[start:start+4]
            sides=[]
            for side in (0,1):
                rows=[p[side] for p in batch]
                sides.append(FactorizedTrainingBatch(tuple(r.states[0] for r in rows),
                    tuple(r.reverse_times[0] for r in rows),tuple(r.observations[0] for r in rows),rows[0].law_id))
            values.extend([float(model.paired_loss(*sides))]*len(batch))
    result = sum(values)/len(values)
    if not math.isfinite(result):
        raise ArithmeticError('nonfinite held-out paired loss')
    return result


def run_experiment(budget=ExperimentBudget(),*,progress=None):
    import torch
    from heterodiff.experiments.factorized_common_grid_pipeline import (
        CommonGridDeviceFactorizedBasePopulation,common_grid_train_conditional_step,
    )
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
    from heterodiff.experiments.factorized_device_qualification import _optimizer
    from heterodiff.experiments.factorized_prepared_conditional_sampler import PreparedCommonGridConditionalSampler
    from heterodiff.experiments.finite_conditional_learning_benchmark import _cpu_policy
    from heterodiff.processes.factorized_hybrid_sampler import LearnedFactorizedSampler

    if type(budget) is not ExperimentBudget:
        raise ValueError('exact explicit experiment budget required')
    spec=specification(budget)
    started=time.monotonic()
    def check():
        if time.monotonic()-started>budget.maximum_seconds:
            raise TimeoutError('multi-seed CPU deadline exceeded; partial routes are not a complete experiment')
    routes=[]
    targets={}
    def completed(record):
        routes.append(record)
        if progress is not None:
            progress(record,len(routes),spec['total_route_count'])
    scenario_diagnostics={}
    with _cpu_policy(torch):
        for scenario in SCENARIOS:
            check()
            name,_,_=scenario
            ref,oracle,key,_,_,_,_=fixture(scenario,budget.seeds[0],METHODS[0])
            target=oracle.terminal_posterior()
            targets[name]=target_indicators(target)
            diagnostic=ContinuousFiberInitializationDiagnostic(oracle.spec)
            scenario_diagnostics[name]=diagnostic.report()
            guide_initial=diagnostic.uncapped_conditioned_initial()
            for control in CONTROLS:
                samples=[]
                began=time.monotonic()
                work={'accepted_births':0,'accepted_deaths':0,'jump_candidates':0,'macrosteps':0}
                if control!='direct-posterior':
                    potential=(GuideControlPotential(diagnostic,key,zero_clock=control=='zero-clock-baseline')
                        if control in ('guide-only','zero-clock-baseline') else IndependentHPotential(oracle,key))
                    initial=(oracle.conditioned_initial() if control=='exact-h-exact-initial' else
                             target if control=='zero-clock-baseline' else guide_initial)
                    # Only for this stationary zero-BASE submodel: Pi_N*g/Z is
                    # also the endpoint posterior. Not valid for arbitrary priors.
                    sampler=LearnedFactorizedSampler(ref,potential,GRID,
                        initializer=lambda rng:materialize(initial,rng,ref,key))
                rng=np.random.default_rng(seed_for(4201,name+control))
                for i in range(budget.control_draws):
                    check()
                    if control=='direct-posterior':
                        samples.append(materialize(target,rng,ref,key))
                    else:
                        path=sampler.sample_path(run_seed=seed_for(4202,name+control),record_id=f'control-{i}'.encode())
                        samples.append(path.terminal_state)
                        work['accepted_births']+=path.diagnostics['accepted_birth']
                        work['accepted_deaths']+=path.diagnostics['accepted_death']
                        work['jump_candidates']+=path.diagnostics['jump_candidates']
                        work['macrosteps']+=len(GRID)-1
                completed({'scenario':name,'kind':'control','route':control,
                    'elapsed_seconds':time.monotonic()-began,'work':work,
                    'initialization_attempt_count':None,
                    'initialization_cost_included_in_elapsed':True,
                    'metrics':route_report(indicators(samples,key),targets[name],len(samples),family_count=spec['total_route_count'])})
            for seed in budget.seeds:
                expected_init=None
                expected_population=None
                for method in METHODS:
                    check()
                    began=time.monotonic()
                    ref,_,key,base,model,context,observed=fixture(scenario,seed,method)
                    initial_hash=_parameter_digest(model)
                    population=CommonGridDeviceFactorizedBasePopulation(base,ref,GRID,context)
                    if expected_init is None:
                        expected_init,expected_population=initial_hash,population.law_id
                    if initial_hash!=expected_init or population.law_id!=expected_population:
                        raise ArithmeticError('paired method initialization or BASE population differs')
                    validation=validation_pairs(population,seed,budget.validation_pairs,check)
                    optimizer=_optimizer(model)
                    losses=[{'update':0,'held_out_paired_loss':validation_loss(model,validation)}]
                    updates=[]
                    for step in range(1,budget.updates+1):
                        check()
                        updates.append(common_grid_train_conditional_step(model,population,optimizer=optimizer,
                            run_seed=seed_for(seed,'training-paths'),record_id=f'update-{step}'.encode(),
                            sample_count=budget.pairs_per_update))
                        if step in spec['validation_checkpoints']:
                            losses.append({'update':step,'held_out_paired_loss':validation_loss(model,validation)})
                    fit_seconds=time.monotonic()-began
                    preparation_began=time.monotonic()
                    sampler=PreparedCommonGridConditionalSampler(base,model,ref,GRID,context,observed,
                        maximum_draws=budget.neural_draws,expected_population_law_id=population.law_id)
                    preparation_seconds=time.monotonic()-preparation_began
                    samples=[]
                    work={'accepted_births':0,'accepted_deaths':0,'jump_candidates':0,'macrosteps':0}
                    began=time.monotonic()
                    for i in range(budget.neural_draws):
                        check()
                        path=sampler.sample_path(run_seed=seed_for(seed,'evaluation-paths'),record_id=f'evaluate-{i}'.encode())
                        samples.append(path.terminal_state)
                        work['accepted_births']+=path.diagnostics['accepted_birth']
                        work['accepted_deaths']+=path.diagnostics['accepted_death']
                        work['jump_candidates']+=path.diagnostics['jump_candidates']
                        work['macrosteps']+=len(GRID)-1
                    completed({'scenario':name,'kind':'neural','route':method,'training_seed':seed,
                        'initial_parameter_sha256':initial_hash,'final_parameter_sha256':_parameter_digest(model),
                        'population_law_id':population.law_id,'prepared_sampler':sampler.snapshot_binding(),
                        'fit_and_validation_seconds':fit_seconds,'evaluation_seconds':time.monotonic()-began,
                        'sampler_preparation_seconds':preparation_seconds,
                        'initialization_attempt_count':None,
                        'initialization_cost_included_in_evaluation_seconds':True,
                        'updates':updates,'held_out_paired_loss_curve':losses,
                        'training_pairs':budget.updates*budget.pairs_per_update,
                        'validation_pairs':budget.validation_pairs,'training_base_paths':budget.updates*budget.pairs_per_update*2,
                        'validation_base_paths':budget.validation_pairs*2,'work':work,
                        'metrics':route_report(indicators(samples,key),targets[name],len(samples),family_count=spec['total_route_count'])})
        summaries=[]
        for name,_,_ in SCENARIOS:
            means={}
            summaries_by_method={}
            for method in METHODS:
                selected=[next(r for r in routes if r['scenario']==name and r['route']==method and r.get('training_seed')==seed)
                    for seed in budget.seeds]
                means[method]=[r['metrics']['empirical_indicators'] for r in selected]
                summaries_by_method[method]=seed_summary(means[method],targets[name],budget.neural_draws)
            gr,direct=[summaries_by_method[m] for m in METHODS]
            gap=direct['mixture_maximum_indicator_error']-gr['mixture_maximum_indicator_error']
            gap_width=gr['mixture_sampling_half_width']+direct['mixture_sampling_half_width']
            summaries.append({'scenario':name,'methods':summaries_by_method,
                'training_seed_roster':list(budget.seeds),
                'paired_seed_error_gr_minus_dir':paired_error_summary(means[METHODS[0]],means[METHODS[1]],
                    targets[name],budget.neural_draws,route_family_count=spec['total_route_count']),
                'signed_probability_contrast_gr_minus_dir':paired_contrast(means[METHODS[0]],means[METHODS[1]],budget.neural_draws),
                'mixture_error_advantage_gr_point':gap,
                'mixture_error_advantage_gr_interval':[max(-1.,gap-gap_width),min(1.,gap+gap_width)],
                'advantage_scope':'EQUAL_WEIGHT_MIXTURE_OF_THIS_FITTED_SEED_ROSTER_FINITE_INDICATORS_NOT_TRAINING_SEED_POPULATION',
                'general_superiority_claimed':False})
        check()
    return {'schema_version':SCHEMA,'decision':'COMPLETE_PREDECLARED_MULTISEED_COMPARISON_REVIEW_ALL_ROUTES',
        'specification':spec,'routes':routes,'summaries':summaries,'initializer_diagnostics':scenario_diagnostics,
        'elapsed_seconds':time.monotonic()-started,
        'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,'device':'cpu','threads':1},
        'scope':{'real_data_accessed':False,'GPU_requested':False,'cloud_or_paid_jobs_launched':False,
            'failed_samples_discarded':0,'retries':0,'checkpoint_or_hyperparameter_selection':False,
            'analytic_cap_one_reference_target':True,'base_weights_zero_frozen_not_trained':True,
            'actual_mixed_neural_conditional_learner_and_sampler':True,'same_target_both_methods':True,
            'full_posterior_recovery_or_general_superiority_claimed':False,
            'matched_quality_speedup_claimed':False,'continuous_TV_or_KL_estimated_from_samples':False}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='new output directory beneath existing parent')
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    budget=ExperimentBudget()
    if args.inspect:
        print(json.dumps(specification(budget),indent=2,sort_keys=True));return 0
    if args.output is None:
        parser.error('--output is required unless --inspect')
    if not args.child:
        if args.output.exists() or not args.output.parent.is_dir():
            parser.error('output must be absent beneath an existing directory')
        command=[sys.executable,'-m','heterodiff.experiments.continuous_multiseed_benchmark',
                 '--output',str(args.output.resolve()),'--child']
        try:
            return subprocess.run(command,check=False,timeout=budget.maximum_seconds).returncode
        except subprocess.TimeoutExpired:
            print('CPU deadline exceeded; child terminated; partial routes are not a complete result',file=sys.stderr)
            return 2
    args.output.mkdir()
    def write(name,record):
        with (args.output/name).open('x',encoding='utf-8') as stream:
            json.dump(record,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
    write('protocol.json',specification(budget))
    def progress(record,completed,total):
        write(f'route-{completed:02d}.json',record)
        print(json.dumps({'completed_routes':completed,'total_routes':total,'scenario':record['scenario'],
                          'route':record['route'],'training_seed':record.get('training_seed')}),flush=True)
    try:
        report=run_experiment(budget,progress=progress)
        write('report.json',report)
    except Exception as error:
        write('failure.json',{'decision':'INCOMPLETE_NO_RETRY_OR_PARTIAL_SUCCESS','error_type':type(error).__name__,'detail':str(error)})
        raise
    print(json.dumps({'decision':report['decision'],'elapsed_seconds':report['elapsed_seconds'],'output':str(args.output)}),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
