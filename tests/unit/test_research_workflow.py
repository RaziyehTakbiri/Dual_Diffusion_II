"""Reader-facing workflow checks with real tiny CPU training and sampling."""

from dataclasses import replace
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from heterodiff import research
from heterodiff.research_config import (
    DOMAINS, METHODS, SCHEMA_VERSION, config_sha256, validate_config,
)


def config_for(domain=DOMAINS[0], **changes):
    record = {
        "schema_version": SCHEMA_VERSION, "experiment_id": "workflow-test",
        "domain": domain, "base_steps": 1, "conditional_steps": 1,
        "base_samples": 2, "conditional_samples": 1, "draws": 2,
        "maximum_seconds": 120,
    }
    record.update(changes)
    return validate_config(record)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def real_runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("reader-workflow")
    runs = {}
    for domain in DOMAINS:
        config = config_for(domain)
        routes = []
        for route in ("first", "replay"):
            output = root / (domain + "-" + route)
            report = research.run_experiment(config, output)
            routes.append((output, report))
        runs[domain] = (config, routes)
    return runs


@pytest.mark.parametrize("domain", DOMAINS)
def test_real_training_sampling_and_descriptive_evaluation_complete_for_both_methods(real_runs, domain):
    config, ((output, report), _) = real_runs[domain]
    assert report["decision"] == "SYNTHETIC_TRAIN_SAMPLE_EVALUATE_COMPLETED"
    assert report["domain"] == domain
    assert report["config_sha256"] == config_sha256(config)
    assert report["identical_trained_base_weights_across_methods"] is True
    assert [row["method"] for row in report["methods"]] == list(METHODS)
    assert report["scope"] == {
        "synthetic_only": True, "cpu_only": True, "paper_results_reproduced": False,
        "F105_executed": False, "general_domain_plugin_support": False,
        "training_resume_supported": False, "speedup_claimed": False,
    }
    assert read_json(output / "report.json") == json.loads(json.dumps(report))
    assert read_json(output / "config.json") == config.to_dict()
    expected = {"config.json", "report.json"}
    for method in METHODS:
        expected.update((method + ".json", method + ".weights.pt"))
        result = read_json(output / (method + ".json"))
        assert result["method"] == method
        assert result["base_weights_sha256"] == report["base_weights_sha256"]
        for field in ("base_history", "conditional_history"):
            assert len(result[field]) == 1
            assert result[field][0]["step"] == 1
            assert math.isfinite(result[field][0]["loss"])
            assert result[field][0]["changed_parameter_elements"] > 0
        assert len(result["samples"]) == len(result["paths"]) == config.draws
        for path, sample in zip(result["paths"], result["samples"]):
            assert path["reverse_grid"] == list(research.GRID)
            assert len(path["states"]) == len(research.GRID)
            assert path["states"][-1] == path["states"][-2] == sample
            assert path["diagnostics"]["base_precision_policy"] == config.precision_policy
            for state in path["states"]:
                assert state["overflow"] is False
                assert 0 <= len(state["events"]) <= 4
                for event in state["events"]:
                    assert type(event["key_utf8"]) is str
                    if event["log_magnitude"] is None:
                        assert event["log_magnitude_hex"] is None
                    else:
                        assert math.isfinite(event["log_magnitude"])
                        assert float.fromhex(event["log_magnitude_hex"]) == event["log_magnitude"]
        evaluation = result["evaluation"]
        counts = [len(sample["events"]) for sample in result["samples"]]
        assert evaluation["draw_count"] == 2
        assert evaluation["event_counts"] == counts
        assert evaluation["mean_event_count"] == sum(counts) / len(counts)
        assert evaluation["mean_absolute_count_difference_from_invented_source"] == sum(abs(n - 3) for n in counts) / len(counts)
        assert evaluation["held_out_dataset"] is False
        assert evaluation["method_superiority_established"] is False
        assert "NOT_F105_OR_SCIENTIFIC_COMPARISON" in evaluation["scope"]
        assert result["weights_are_not_a_resume_checkpoint"] is True
        assert result["exact_conditional_law_recovery_claimed"] is False
    assert {path.name for path in output.iterdir()} == expected


@pytest.mark.parametrize("domain", DOMAINS)
def test_saved_weights_load_without_pickle_execution_and_match_the_report(real_runs, domain):
    import torch
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest

    config, ((output, report), _) = real_runs[domain]
    for method in METHODS:
        result = read_json(output / (method + ".json"))
        saved = torch.load(output / result["weights_file"], map_location="cpu", weights_only=True)
        assert set(saved) == {"schema_version", "base", "conditional", "method", "config"}
        assert saved["schema_version"] == "heterodiff-reader-weights-only-v1"
        assert saved["method"] == method
        assert saved["config"] == config.to_dict()
        _, _, base, model, _ = research._fixture(config, method)
        before_base, before_model = _parameter_digest(base), _parameter_digest(model)
        base.load_state_dict(saved["base"], strict=True)
        model.load_state_dict(saved["conditional"], strict=True)
        assert _parameter_digest(base) == result["base_weights_sha256"] != before_base
        assert _parameter_digest(model) == result["conditional_weights_sha256"] != before_model
        assert all(tensor.device.type == "cpu" and bool(torch.isfinite(tensor).all())
                   for state in (saved["base"], saved["conditional"]) for tensor in state.values())


@pytest.mark.parametrize("domain", DOMAINS)
def test_same_seed_repeats_training_and_paths_exactly_on_the_same_cpu_runtime(real_runs, domain):
    import torch

    _, ((first, first_report), (replay, replay_report)) = real_runs[domain]
    for method in METHODS:
        # Full JSON contains loss history, stream diagnostics and every path state.
        assert read_json(first / (method + ".json")) == read_json(replay / (method + ".json"))
        left = torch.load(first / (method + ".weights.pt"), map_location="cpu", weights_only=True)
        right = torch.load(replay / (method + ".weights.pt"), map_location="cpu", weights_only=True)
        for model in ("base", "conditional"):
            assert left[model].keys() == right[model].keys()
            assert all(torch.equal(left[model][name], right[model][name]) for name in left[model])
    assert {k: v for k, v in first_report.items() if k != "elapsed_seconds"} == {
        k: v for k, v in replay_report.items() if k != "elapsed_seconds"
    }


def test_seed_changes_explicit_initialization_and_labelled_streams():
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest

    config = config_for()
    _, _, base_a, model_a, _ = research._fixture(config, METHODS[0])
    _, _, base_b, model_b, _ = research._fixture(replace(config, seed=8), METHODS[0])
    assert _parameter_digest(base_a) != _parameter_digest(base_b)
    assert _parameter_digest(model_a) != _parameter_digest(model_b)
    labels = ("base-initialization", "conditional-initialization", "observation-encoder", "nuisance",
              "base-training", "conditional-training", "conditional-sampling")
    assert len({research._seed(config.seed, label) for label in labels}) == len(labels)
    assert all(research._seed(7, label) != research._seed(8, label) for label in labels)


def test_existing_output_is_never_overwritten(tmp_path, monkeypatch):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("existing user result", encoding="utf-8")
    monkeypatch.setattr(research, "_fixture", lambda *args: pytest.fail("no model may start on collision"))
    with pytest.raises(FileExistsError):
        research.run_experiment(config_for(), output)
    assert marker.read_text(encoding="utf-8") == "existing user result"
    assert list(output.iterdir()) == [marker]


def test_nonexistent_output_parent_is_rejected_before_any_write(tmp_path):
    with pytest.raises(ValueError, match="output parent"):
        research.run_experiment(config_for(), tmp_path / "missing" / "experiment")
    assert list(tmp_path.iterdir()) == []


def test_failed_model_operation_writes_failure_not_success_and_restores_cpu_settings(tmp_path, monkeypatch):
    import torch

    output = tmp_path / "failed"
    before = (torch.get_num_threads(), torch.are_deterministic_algorithms_enabled(),
              torch.is_deterministic_algorithms_warn_only_enabled())
    def fail(*_args):
        raise RuntimeError("intentional synthetic fixture failure")
    monkeypatch.setattr(research, "_fixture", fail)
    with pytest.raises(RuntimeError, match="intentional synthetic"):
        research.run_experiment(config_for(), output)
    assert read_json(output / "failure.json")["decision"] == "SYNTHETIC_EXPERIMENT_FAILED"
    assert not (output / "report.json").exists()
    assert before == (torch.get_num_threads(), torch.are_deterministic_algorithms_enabled(),
                      torch.is_deterministic_algorithms_warn_only_enabled())


def config_path(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config_for().to_dict()), encoding="utf-8")
    return path


def test_inspect_runs_with_site_packages_disabled_and_no_model_import_or_output(tmp_path):
    path = config_path(tmp_path)
    src = Path(__file__).resolve().parents[2] / "src"
    code = (
        "import sys; sys.path.insert(0, " + repr(str(src)) + "); "
        "from heterodiff.research import main; "
        "assert main(['inspect', '--config', " + repr(str(path)) + "]) == 0; "
        "assert not {'torch', 'numpy', 'scipy', 'heterodiff.events'} & set(sys.modules)"
    )
    child = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code],
                           capture_output=True, text=True, timeout=10, cwd=tmp_path, check=False)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == config_for().to_dict()
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("returncode", [0, 2, 7])
def test_cli_supervises_one_child_and_preserves_its_exit_status(tmp_path, monkeypatch, returncode):
    path = config_path(tmp_path)
    output = tmp_path / "new-result"
    calls = []
    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=returncode)
    monkeypatch.setattr(research.subprocess, "run", fake_run)
    assert research.main(["run", "--config", str(path), "--output", str(output)]) == returncode
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [sys.executable, "-m", "heterodiff.research", "_worker", "--config", str(path.resolve()),
                    "--output", str(output.absolute())]
    assert kwargs == {"timeout": config_for().maximum_seconds, "check": False}
    assert not output.exists()


def test_cli_timeout_is_failure_not_an_automatic_retry(tmp_path, monkeypatch, capsys):
    path = config_path(tmp_path)
    calls = []
    def timeout(argv, **kwargs):
        calls.append(argv)
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
    monkeypatch.setattr(research.subprocess, "run", timeout)
    assert research.main(["run", "--config", str(path), "--output", str(tmp_path / "new-result")]) == 1
    assert len(calls) == 1
    assert "TimeoutExpired" in capsys.readouterr().err


def test_cli_rejects_existing_output_before_child_launch(tmp_path, monkeypatch, capsys):
    path = config_path(tmp_path)
    output = tmp_path / "existing"
    output.mkdir()
    monkeypatch.setattr(research.subprocess, "run", lambda *args, **kwargs: pytest.fail("child must not launch"))
    assert research.main(["run", "--config", str(path), "--output", str(output)]) == 1
    assert "existing results are preserved" in capsys.readouterr().err
    assert list(output.iterdir()) == []


def test_cli_rejects_bad_config_without_child_launch(tmp_path, monkeypatch, capsys):
    path = tmp_path / "bad.json"
    path.write_text('{"device":"cuda:0"}', encoding="utf-8")
    monkeypatch.setattr(research.subprocess, "run", lambda *args, **kwargs: pytest.fail("child must not launch"))
    assert research.main(["run", "--config", str(path), "--output", str(tmp_path / "new-result")]) == 1
    assert "ResearchConfigError" in capsys.readouterr().err
