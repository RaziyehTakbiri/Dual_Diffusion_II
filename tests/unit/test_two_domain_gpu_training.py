"""Local synthetic Torch qualification; no CUDA-hardware success is assumed."""

from fractions import Fraction
from io import BytesIO

import pytest
import torch

from heterodiff.experiments import two_domain_gpu_training as gpu


class SmallExecutionModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor([[0.1]], dtype=torch.float32))
        self.bias = torch.nn.Parameter(torch.tensor([0.0], dtype=torch.float32))
        self.unused_branch = torch.nn.Parameter(torch.tensor([0.2], dtype=torch.float32))
        self.frozen_base = torch.nn.Parameter(torch.tensor([[0.3]], dtype=torch.float32), requires_grad=False)

    def forward(self, values):
        return values @ self.weight + self.bias + values @ self.frozen_base


def identity(**changes):
    values = dict(method_id='association-aware-guide-plus-residual',
                  domain_id='physionet-challenge-2012', seed_ordinal=0, seed_value=137)
    values.update(changes)
    return gpu.RunIdentity(**values)


def roster(size=17, **changes):
    values = dict(domain_id='physionet-challenge-2012',
                  record_ids=tuple(f'train{index:03}'.encode() for index in range(size)),
                  fields={'x': torch.arange(size, dtype=torch.float32).reshape(-1, 1) / 20,
                          'target': torch.zeros(size, 1, dtype=torch.float32),
                          'index': torch.arange(size, dtype=torch.int64),
                          'mask': torch.ones(size, 1, dtype=torch.bool)})
    values.update(changes)
    return gpu.TensorTrainingRoster(**values)


VALIDATION_IDS = tuple(f'validation{index:03}'.encode() for index in range(128))


def loss(model, batch, generator):
    assert batch['mask'].dtype == torch.bool
    assert batch['index'].dtype == torch.int64
    assert generator.device == batch['x'].device
    return ((model(batch['x']) - batch['target']) ** 2).mean()


def validation(model, step, run_identity):
    assert model.training is False
    assert run_identity == identity()
    return gpu.ValidationObservation(torch.full((128,), 0.125, dtype=torch.float64))


def run(**changes):
    values = dict(model=SmallExecutionModel(), roster=roster(), identity=identity(),
                  device='cpu', loss_adapter=loss, validation_group_ids=VALIDATION_IDS,
                  validation_adapter=validation,
                  schedule=gpu.NonconfirmatorySchedule(maximum_updates=3, validation_every=1))
    values.update(changes)
    return gpu.run_training_qualification(**values)


def test_real_adamw_updates_cyclic_batch16_without_modifying_supplied_model():
    original = SmallExecutionModel()
    before = {key: value.clone() for key, value in original.state_dict().items()}
    seen = []
    def checked_loss(model, batch, generator):
        seen.append(tuple(batch['index'].tolist()))
        assert model.weight.dtype == torch.float32
        assert model.weight.device.type == 'cpu'
        return loss(model, batch, generator)
    result = run(model=original, loss_adapter=checked_loss)
    assert seen == [tuple(range(16)), (16,) + tuple(range(15)), (15, 16) + tuple(range(14))]
    assert result.completed_updates == 3
    assert result.selected_checkpoint_step == 1
    assert not torch.equal(result.checkpoints[-1].model_state['weight'], before['weight'])
    for key, value in original.state_dict().items():
        assert torch.equal(value, before[key])
    for checkpoint in result.checkpoints:
        assert torch.equal(checkpoint.model_state['frozen_base'], before['frozen_base'])
        assert torch.equal(checkpoint.model_state['unused_branch'], before['unused_branch'])
        group = checkpoint.optimizer_state['param_groups'][0]
        assert len(checkpoint.optimizer_state['param_groups']) == 1
        assert len(group['params']) == 3  # Includes unused trainable, excludes frozen base.
        assert group['lr'] == 0.001 and group['betas'] == (0.9, 0.999)
        assert group['eps'] == 1e-8 and group['weight_decay'] == 0
        for option in ('amsgrad', 'maximize', 'foreach', 'fused', 'capturable', 'differentiable'):
            assert group[option] is False
        assert len(checkpoint.optimizer_state['state']) == 2  # No fake gradient for unused branch.
        for state in checkpoint.optimizer_state['state'].values():
            for name in ('exp_avg', 'exp_avg_sq'):
                assert state[name].dtype == torch.float32
                assert state[name].device.type == 'cpu'
                assert torch.isfinite(state[name]).all()


def test_fixed_run_repeatability_and_rng_global_settings_are_restored():
    rng_before = torch.random.get_rng_state().clone()
    settings = [(obj, name, getattr(obj, name)) for obj, name, _ in gpu._precision_settings()]
    mode = (torch.are_deterministic_algorithms_enabled(),
            torch.is_deterministic_algorithms_warn_only_enabled(),
            torch.backends.cudnn.benchmark, torch.backends.cudnn.deterministic)
    def random_loss(model, batch, generator):
        assert torch.are_deterministic_algorithms_enabled()
        assert not torch.is_deterministic_algorithms_warn_only_enabled()
        assert not torch.backends.cudnn.benchmark
        assert all(getattr(obj, name) == value for obj, name, value in gpu._precision_settings())
        noise = torch.rand(batch['target'].shape, generator=generator,
                           device=batch['target'].device, dtype=torch.float32)
        return ((model(batch['x']) - noise) ** 2).mean()
    first = run(loss_adapter=random_loss)
    second = run(loss_adapter=random_loss)
    assert first.losses == second.losses
    for key in first.checkpoints[-1].model_state:
        assert torch.equal(first.checkpoints[-1].model_state[key], second.checkpoints[-1].model_state[key])
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert all(getattr(obj, name) == value for obj, name, value in settings)
    assert mode == (torch.are_deterministic_algorithms_enabled(),
                    torch.is_deterministic_algorithms_warn_only_enabled(),
                    torch.backends.cudnn.benchmark, torch.backends.cudnn.deterministic)


def test_score_improvement_never_early_stops_and_ties_keep_earliest():
    seen = []
    def changing_validation(model, step, run_identity):
        seen.append(step)
        return gpu.ValidationObservation(torch.full((128,), {-1: 0, 1: -1, 2: -1, 3: 0}[step], dtype=torch.float64))
    result = run(validation_adapter=changing_validation)
    assert seen == [1, 2, 3]
    assert result.completed_updates == 3 and result.selected_checkpoint_step == 1
    assert result.summary()['full_frozen_schedule_executed'] is False
    assert result.summary()['cuda_execution_observed'] is False
    assert result.summary()['production_training_or_resume_authorized'] is False
    assert result.summary()['f105_factory_certification_supplied'] is False
    assert result.summary()['scientific_result_created'] is False


def test_frozen_schedule_is_exact_and_short_qualification_retains_terminal_step():
    full = gpu.NonconfirmatorySchedule()
    assert full.maximum_updates == 4096
    assert full.checkpoint_steps == tuple(range(256, 4097, 256))
    assert len(full.checkpoint_steps) == 16
    assert full.matches_frozen_final_training_schedule
    short = gpu.NonconfirmatorySchedule(3, 2)
    assert short.checkpoint_steps == (2, 3)
    assert [item.completed_updates for item in run(schedule=short).checkpoints] == [2, 3]


def test_checkpoint_serialization_is_detached_inspection_only_not_resume():
    result = run()
    first, last = result.checkpoints[0], result.checkpoints[-1]
    serialized = gpu.checkpoint_to_bytes(last)
    inspected = gpu.inspect_checkpoint_bytes(serialized)
    assert inspected['scope'] == gpu.SCOPE
    assert inspected['production_resume_permitted'] is False
    assert inspected['identity'] == identity().to_dict()
    assert inspected['completed_updates'] == 3
    for key in inspected['model_state']:
        assert torch.equal(inspected['model_state'][key], last.model_state[key])
        assert inspected['model_state'][key].device.type == 'cpu'
    inspected['model_state']['weight'].fill_(99)
    assert not torch.equal(inspected['model_state']['weight'], last.model_state['weight'])
    first.model_state['weight'].fill_(88)
    assert not torch.equal(first.model_state['weight'], last.model_state['weight'])
    assert not hasattr(gpu, 'resume_training')
    restored_model = SmallExecutionModel()
    restored_model.load_state_dict(gpu.inspect_checkpoint_bytes(serialized)['model_state'])
    assert torch.equal(restored_model.weight, last.model_state['weight'])


def test_failure_restores_rng_flags_without_retry_or_success_checkpoint():
    calls = []
    rng = torch.random.get_rng_state().clone()
    mode = torch.are_deterministic_algorithms_enabled()
    def nonfinite_loss(model, batch, generator):
        calls.append(1)
        torch.rand(1, generator=generator)
        return model(batch['x']).mean() * float('nan')
    with pytest.raises(gpu.TrainingQualificationError) as failure:
        run(loss_adapter=nonfinite_loss)
    assert calls == [1]
    assert failure.value.completed_updates == 0
    assert torch.equal(torch.random.get_rng_state(), rng)
    assert torch.are_deterministic_algorithms_enabled() == mode


def test_nonfinite_after_optimizer_step_is_terminal_with_honest_update_count(monkeypatch):
    original_step = torch.optim.AdamW.step
    def corrupt_step(self, *args, **kwargs):
        value = original_step(self, *args, **kwargs)
        with torch.no_grad():
            self.param_groups[0]['params'][0].fill_(float('inf'))
        return value
    monkeypatch.setattr(torch.optim.AdamW, 'step', corrupt_step)
    with pytest.raises(gpu.TrainingQualificationError, match='finite FP32') as failure:
        run()
    assert failure.value.completed_updates == 1


def test_no_cpu_fallback_when_cuda_requested(monkeypatch):
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    with pytest.raises(gpu.TrainingQualificationError, match='fallback is forbidden'):
        run(device='cuda:0')


def test_cuda_workspace_and_visibility_checks_do_not_modify_environment(monkeypatch):
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    monkeypatch.setattr(torch.cuda, 'device_count', lambda: 1)
    monkeypatch.delenv('CUBLAS_WORKSPACE_CONFIG', raising=False)
    with pytest.raises(gpu.TrainingQualificationError, match='CUBLAS_WORKSPACE_CONFIG'):
        gpu.resolve_training_device('cuda:0')
    with pytest.raises(gpu.TrainingQualificationError, match='not visible'):
        gpu.resolve_training_device('cuda:1')


@pytest.mark.parametrize('device', ['cuda', 'auto', 'mps', 'cuda:-1', 'cuda:00', 0])
def test_device_must_be_explicit_without_implicit_distributed_execution(device):
    with pytest.raises(gpu.TrainingQualificationError):
        gpu.resolve_training_device(device)


@pytest.mark.parametrize('scores', [torch.zeros(127, dtype=torch.float64),
                                   torch.zeros(128, dtype=torch.float32),
                                   torch.full((128,), float('nan'), dtype=torch.float64),
                                   torch.full((128,), 2.0, dtype=torch.float64)])
def test_validation_is_complete_finite_cpu_binary64(scores):
    with pytest.raises(gpu.TrainingQualificationError):
        run(validation_adapter=lambda *args: gpu.ValidationObservation(scores))


def test_validation_draw_count_and_callback_type_cannot_be_relaxed():
    with pytest.raises(gpu.TrainingQualificationError, match='R=64'):
        run(validation_adapter=lambda *args: gpu.ValidationObservation(torch.zeros(128, dtype=torch.float64), 2))
    with pytest.raises(gpu.TrainingQualificationError, match='unsupported observation'):
        run(validation_adapter=lambda *args: 0.0)


def test_validation_aggregation_uses_exact_ratios_not_tensor_mean():
    scores = torch.zeros(128, dtype=torch.float64)
    scores[0], scores[1], scores[2] = 1.0, 2.0**-54, -1.0
    expected = float(Fraction(1, 2**54) / 128).hex()
    assert gpu.ValidationObservation(scores).aggregate_hex() == expected


@pytest.mark.parametrize('changes', [dict(seed_ordinal=True), dict(seed_ordinal=256),
                                    dict(seed_value=-1), dict(method_id='unknown'),
                                    dict(domain_id='third-domain')])
def test_fixed_run_identity_is_required(changes):
    with pytest.raises(gpu.TrainingQualificationError):
        identity(**changes)


def test_domain_and_group_disjointness_are_enforced():
    with pytest.raises(gpu.TrainingQualificationError, match='cross-domain'):
        run(roster=roster(domain_id='online-retail-ii'))
    overlapping = tuple(sorted((b'train000',) + VALIDATION_IDS[1:]))
    with pytest.raises(gpu.TrainingQualificationError, match='overlap'):
        run(validation_group_ids=overlapping)


def test_unsorted_or_small_roster_and_implicit_precision_casts_are_refused():
    with pytest.raises(gpu.TrainingQualificationError):
        roster(size=15)
    with pytest.raises(gpu.TrainingQualificationError):
        roster(record_ids=tuple(reversed(roster().record_ids)))
    with pytest.raises(gpu.TrainingQualificationError):
        roster(fields={'x': torch.zeros(17, 1, dtype=torch.float64)})
    with pytest.raises(gpu.TrainingQualificationError, match='explicit FP32 successor'):
        run(model=SmallExecutionModel().double())


def test_no_trainable_parameters_or_unfrozen_rate_is_refused():
    model = SmallExecutionModel()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    with pytest.raises(gpu.TrainingQualificationError, match='trainable parameters'):
        run(model=model)
    with pytest.raises(gpu.TrainingQualificationError, match='exact frozen candidate'):
        run(learning_rate=Fraction(1, 10))


def test_live_or_test_dataset_role_and_resume_archive_are_not_accepted():
    with pytest.raises(gpu.TrainingQualificationError, match='synthetic'):
        roster(source_kind='ACTUAL_STUDY_TRAINING_DATA')
    buffer = BytesIO()
    torch.save({'scope': gpu.SCOPE, 'production_resume_permitted': True}, buffer)
    with pytest.raises(gpu.TrainingQualificationError, match='inspection-only'):
        gpu.inspect_checkpoint_bytes(buffer.getvalue())


def test_full_uint64_caller_seed_and_per_method_tuning_limits():
    selected = identity(seed_value=2**64 - 1)
    result = run(identity=selected, validation_adapter=lambda *args: gpu.ValidationObservation(torch.zeros(128, dtype=torch.float64)))
    assert result.identity.seed_value == 2**64 - 1
    with pytest.raises(gpu.TrainingQualificationError):
        identity(seed_value=2**64)
    assert identity(trial_ordinal=0).trial_ordinal == 0
    with pytest.raises(gpu.TrainingQualificationError, match='trial_ordinal'):
        identity(trial_ordinal=1)  # Primary method has one frozen configuration.
    external = next(row for row in gpu.frozen.maximum_tuning_trials_value()['rows'] if row['maximum_trials'] == 8)
    assert gpu.RunIdentity(external['method_id'], external['domain_id'], 0, 9, 7).trial_ordinal == 7
    with pytest.raises(gpu.TrainingQualificationError, match='1024-update'):
        run(identity=identity(trial_ordinal=0), schedule=gpu.NonconfirmatorySchedule())


def test_validation_random_draws_do_not_change_training_random_stream():
    validation_draws = []
    def global_random_loss(model, batch, generator):
        noise = torch.rand(batch['target'].shape, dtype=torch.float32)
        return ((model(batch['x']) - noise) ** 2).mean()
    def random_validation(model, step, run_identity):
        validation_draws.append(torch.rand(50).clone())
        return validation(model, step, run_identity)
    first = run(loss_adapter=global_random_loss)
    second = run(loss_adapter=global_random_loss, validation_adapter=random_validation)
    assert first.losses == second.losses
    assert not torch.equal(validation_draws[0], validation_draws[1])
    assert torch.equal(first.checkpoints[-1].model_state['weight'], second.checkpoints[-1].model_state['weight'])


@pytest.mark.parametrize('name', ['weight', 'frozen_base'])
def test_validation_callback_cannot_modify_any_model_parameter(name):
    def mutate_validation(model, step, run_identity):
        getattr(model, name).add_(1)
        return validation(model, step, run_identity)
    with pytest.raises(gpu.TrainingQualificationError, match='validation callback mutated') as failure:
        run(validation_adapter=mutate_validation)
    assert failure.value.completed_updates == 1


def test_loss_callback_cannot_mutate_frozen_base_or_trainable_roster():
    def mutate_base(model, batch, generator):
        with torch.no_grad():
            model.frozen_base.add_(1)
        return loss(model, batch, generator)
    with pytest.raises(gpu.TrainingQualificationError, match='frozen parameter') as failure:
        run(loss_adapter=mutate_base)
    assert failure.value.completed_updates == 0
    def change_trainable(model, batch, generator):
        model.unused_branch.requires_grad_(False)
        return loss(model, batch, generator)
    with pytest.raises(gpu.TrainingQualificationError, match='trainable parameter roster'):
        run(loss_adapter=change_trainable)
    def replace_parameter(model, batch, generator):
        model.weight = torch.nn.Parameter(model.weight.detach().clone())
        return loss(model, batch, generator)
    with pytest.raises(gpu.TrainingQualificationError, match='trainable parameter roster'):
        run(loss_adapter=replace_parameter)


def test_nonfinite_gradient_is_terminal_before_any_optimizer_update():
    def corrupt_gradient(model, batch, generator):
        model.weight.register_hook(lambda gradient: torch.full_like(gradient, float('inf')))
        return loss(model, batch, generator)
    with pytest.raises(gpu.TrainingQualificationError, match='present gradients') as failure:
        run(loss_adapter=corrupt_gradient)
    assert failure.value.completed_updates == 0


def test_checkpoint_records_exact_local_configuration_and_learning_rate():
    result = run(configuration_id='SYNTHETIC_LINEAR_MODEL_FIXED_TARGET_V1')
    config = result.training_configuration
    assert config['learning_rate_exact_rational'] == '1/1000'
    assert config['maximum_updates'] == 3 and config['validation_every'] == 1
    assert config['caller_configuration_id'] == 'SYNTHETIC_LINEAR_MODEL_FIXED_TARGET_V1'
    assert config['model_and_loss_scientific_configuration_independently_verified'] is False
    assert config['independent_validation_draws_authenticated'] is False
    assert len(config['configuration_sha256']) == 64
    for checkpoint in result.checkpoints:
        assert checkpoint.training_configuration == config
    inspected = gpu.inspect_checkpoint_bytes(gpu.checkpoint_to_bytes(result.checkpoints[-1]))
    assert inspected['training_configuration'] == config
    assert result.summary()['training_configuration'] == config


def test_inherited_autocast_is_disabled_for_loss_and_validation():
    def full_precision_loss(model, batch, generator):
        assert not torch.is_autocast_enabled('cpu')
        return loss(model, batch, generator)
    def full_precision_validation(model, step, run_identity):
        assert not torch.is_autocast_enabled('cpu')
        return validation(model, step, run_identity)
    with torch.autocast(device_type='cpu', dtype=torch.bfloat16):
        run(loss_adapter=full_precision_loss, validation_adapter=full_precision_validation)
        assert torch.is_autocast_enabled('cpu')
