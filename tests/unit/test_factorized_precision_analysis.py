"""The local precision report must not hide failed legacy comparisons."""
import pytest
import torch

from heterodiff.experiments.factorized_precision_analysis import _compare, run_local_precision_analysis
from heterodiff.experiments.factorized_device_qualification import TOLERANCES


def test_actual_fixed_local_precision_report_with_original_tolerances():
    threads = torch.get_num_threads()
    deterministic = torch.are_deterministic_algorithms_enabled()
    report = run_local_precision_analysis()
    assert torch.get_num_threads() == threads
    assert torch.are_deterministic_algorithms_enabled() == deterministic
    assert report['decision'] == 'PASS_LOCAL_PRECISION_CONTROLS_ONLY'
    assert report['case_count'] == 4 and report['synthetic_adamw_steps'] == 28
    assert len({(c['domain'], c['method']) for c in report['cases']}) == 4
    assert not report['scope']['GPU_execution']
    assert not report['scope']['legacy_CPU_GPU_parity_closed']
    assert not report['scope']['candidate_GPU_qualified']
    assert not report['scope']['production_precision_policy_adopted']
    for row in report['cases']:
        assert all(row['checks'].values())
        comparisons = row['comparisons']
        assert comparisons['legacy_vs_functional_fp32']['updated_parameters']['exact']
        assert comparisons['shared_fp64_exact_cpu_replay']['updated_parameters']['exact']
        assert comparisons['shared_fp64_batched_vs_rowwise']['updated_parameters']['within_existing_tolerance']
        assert 'legacy_fp32_vs_shared_fp64_NOT_legacy_GPU_parity' in comparisons
        for comparison in comparisons.values():
            update = comparison['updated_parameters']
            assert (update['atol'], update['rtol']) == TOLERANCES['updated_parameter']
            assert update['scalar_count'] == 96705
    # This report is not allowed to omit the legacy mismatch to make a pass.
    assert any(not c['comparisons']['legacy_fp32_vs_shared_fp64_NOT_legacy_GPU_parity']
               ['updated_parameters']['within_existing_tolerance'] for c in report['cases'])


@pytest.mark.parametrize('left,right', [
    ({'a': None}, {'b': None}), ({'a': None}, {'a': torch.zeros(1)}),
    ({'a': torch.zeros(1)}, {'a': torch.zeros(2)}),
    ({'a': torch.zeros(1)}, {'a': torch.tensor([float('nan')])}),
    ({'a': torch.tensor([float('inf')])}, {'a': torch.zeros(1)}),
])
def test_comparison_rejects_invalid_or_partial_evidence(left, right):
    with pytest.raises(ValueError):
        _compare(left, right, 'updated_parameter')


def test_comparison_retains_failure_counts_and_exactness():
    result = _compare({'a': torch.tensor([0., 1., 2.])},
                      {'a': torch.tensor([1e-3, 1., 2.])}, 'updated_parameter')
    assert not result['exact'] and not result['within_existing_tolerance']
    assert result['failing_scalar_count'] == 1 and result['scalar_count'] == 3


def test_loss_only_failure_cannot_be_hidden_by_exact_gradient_update_checks(monkeypatch):
    from heterodiff.experiments import factorized_precision_analysis as analysis
    original = analysis._evaluate
    def altered(domain, method, variant):
        loss, gradients, updated = original(domain, method, variant)
        if variant == 'rowwise_shared_fp64':
            loss = {name: value + 1. for name, value in loss.items()}
        return loss, gradients, updated
    monkeypatch.setattr(analysis, '_evaluate', altered)
    report = analysis.run_local_precision_analysis()
    assert report['decision'] == 'FAIL_LOCAL_PRECISION_CONTROLS'
    assert all(not c['checks']['shared_fp64_cpu_layout_stress_pass'] for c in report['cases'])


def test_final_variant_crossing_soft_deadline_cannot_return_pass(monkeypatch):
    from heterodiff.experiments import factorized_precision_analysis as analysis
    clock, count = [0.], [0]
    def evaluate(*args):
        count[0] += 1
        if count[0] == 28:
            clock[0] = 120.001
        return ({k: 0. for k in ('total', 'continuous', 'jump')},
                {'readout_hidden.weight': torch.zeros(128, 257)},
                {'readout_hidden.weight': torch.zeros(128, 257)})
    monkeypatch.setattr(analysis.time, 'perf_counter', lambda: clock[0])
    monkeypatch.setattr(analysis, '_evaluate', evaluate)
    with pytest.raises(TimeoutError, match='120-second'):
        analysis.run_local_precision_analysis()
