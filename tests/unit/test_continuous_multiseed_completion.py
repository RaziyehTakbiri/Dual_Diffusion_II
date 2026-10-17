"""Fixed-pair continuation evidence, deterministic equivalence and no-retry tests."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import numpy as np
import pytest
import scipy
import torch

from heterodiff.experiments import continuous_multiseed_benchmark as original
from heterodiff.experiments import continuous_multiseed_completion as completion

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / completion.ORIGINAL_DIRECTORY
REVIEW = ROOT / completion.REVIEW_PATH
VERIFICATION = ROOT / completion.VERIFICATION_PATH


@pytest.fixture(autouse=True)
def one_cpu_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def versions():
    return {"python": platform.python_version(), "torch": torch.__version__,
            "numpy": np.__version__, "scipy": scipy.__version__}


def scientific_route(route):
    return {k: v for k, v in route.items() if k not in (
        "fit_and_validation_seconds", "evaluation_seconds", "sampler_preparation_seconds", "elapsed_seconds",
    )}


@pytest.fixture(scope="module")
def reduced_original():
    # Keep all three original seeds and 22 routes, reducing work only for tests.
    budget = original.ExperimentBudget(control_draws=2, neural_draws=2, updates=1,
        pairs_per_update=2, validation_pairs=2, maximum_seconds=60)
    report = original.run_experiment(budget)
    assert len(report["routes"]) == 22
    assert report["specification"]["is_default_protocol_run"] is False
    return budget, report


def test_actual_reviewed_prefix_revalidates_without_changing_original_files():
    before = {p.name: digest(p) for p in ORIGINAL.iterdir()}
    prefix = completion.validate_original(ORIGINAL, REVIEW, VERIFICATION, ROOT)
    assert prefix.budget == original.ExperimentBudget()
    assert len(prefix.routes) == len(prefix.bindings["preserved_route_artifacts"]) == 20
    assert completion.fixed_roster(prefix.budget)[-2:] == (
        (original.SCENARIOS[-1][0], "neural", original.METHODS[0], 1203),
        (original.SCENARIOS[-1][0], "neural", original.METHODS[1], 1203),
    )
    assert prefix.expected_environment["torch"] == "2.12.1"
    assert prefix.routes[-1]["population_law_id"] == (
        "common-grid-neural-base-v1-2e2c6842212a42bb8e88ae1195be8426bf665d713c2cd363e016fcdd99058c32")
    assert {p.name: digest(p) for p in ORIGINAL.iterdir()} == before
    assert not (ORIGINAL / "report.json").exists()


def test_clean_inspection_validates_without_torch_or_output(tmp_path):
    code = (
        "import sys; from heterodiff.experiments import continuous_multiseed_completion as c; "
        f"assert c.main(['--source-root',{str(ROOT)!r},'--inspect']) == 0; "
        "assert 'torch' not in sys.modules, 'inspection imported Torch'"
    )
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, check=True)
    record = json.loads(result.stdout)
    assert record["decision"] == "FIXED_TWENTY_ROUTE_PREFIX_VALIDATED_NO_COMPLETION_RUN"
    assert record["separate_execution_deadline_seconds"] == 1800
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("target", ["route", "protocol", "review", "verification"])
def test_changed_original_artifact_hash_is_refused(tmp_path, target):
    directory = tmp_path / "original"
    shutil.copytree(ORIGINAL, directory)
    review = tmp_path / "review.json"
    verification = tmp_path / "verification.json"
    shutil.copyfile(REVIEW, review)
    shutil.copyfile(VERIFICATION, verification)
    path = {"route": directory / "route-20.json", "protocol": directory / "protocol.json",
            "review": review, "verification": verification}[target]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(completion.CompletionError, match="artifact hash mismatch"):
        completion.validate_original(directory, review, verification, ROOT)


@pytest.mark.parametrize("change", ["missing", "extra", "complete-report"])
def test_original_namespace_must_be_exact_twenty_route_prefix(tmp_path, change):
    directory = tmp_path / "original"
    shutil.copytree(ORIGINAL, directory)
    if change == "missing":
        (directory / "route-20.json").unlink()
    else:
        (directory / ("route-21.json" if change == "extra" else "report.json")).write_text("{}")
    with pytest.raises(completion.CompletionError, match="exact reviewed 20-route namespace"):
        completion.validate_original(directory, REVIEW, VERIFICATION, ROOT)


@pytest.mark.parametrize("changed_path", [completion.SOURCE_PATHS[0], "docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md"])
def test_changed_source_or_scientific_protocol_is_refused(tmp_path, changed_path):
    for relative in completion.SOURCE_PATHS + ("docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md",):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    altered = tmp_path / changed_path
    altered.write_bytes(altered.read_bytes() + b"\n")
    with pytest.raises(completion.CompletionError, match="(?:source|protocol) hash mismatch"):
        completion.validate_original(ORIGINAL, REVIEW, VERIFICATION, tmp_path)


@pytest.mark.parametrize("change", ["missing", "duplicate", "reordered", "wrong-seed", "changed-alpha", "changed-draws"])
def test_assembled_route_roster_or_family_cannot_be_changed(reduced_original, change):
    budget, report = reduced_original
    routes = deepcopy(report["routes"])
    if change == "missing":
        routes.pop()
    elif change == "duplicate":
        routes[-1] = deepcopy(routes[-2])
    elif change == "reordered":
        routes[-1], routes[-2] = routes[-2], routes[-1]
    elif change == "wrong-seed":
        routes[-1]["training_seed"] = 9999
    elif change == "changed-alpha":
        routes[-1]["metrics"]["alpha_family"] = 0.01
    else:
        routes[-1]["metrics"]["draw_count"] += 1
    with pytest.raises(completion.CompletionError):
        completion.validate_routes(routes, budget, complete=True)


def test_reduced_missing_pair_exactly_matches_original_neural_loop_and_full_summary(reduced_original, tmp_path):
    budget, baseline = reduced_original
    prefix = completion.ValidatedPrefix(tuple(deepcopy(baseline["routes"][:20])), budget,
        {"test_only": True, "original_scientific_budget_reduced": True}, versions())
    saved_prefix = json.dumps(prefix.routes, sort_keys=True, allow_nan=False)
    output = tmp_path / "completion"
    progress = []
    report = completion._complete(prefix, output, 60, progress=lambda r, n, total: progress.append((n, total)))
    assert progress == [(21, 22), (22, 22)]
    assert json.dumps(prefix.routes, sort_keys=True, allow_nan=False) == saved_prefix
    assert sorted(p.name for p in output.iterdir()) == [
        "continuation-intent.json", "report.json", "route-21.json", "route-22.json",
    ]
    assert report["decision"] == "COMPLETE_FIXED_ROSTER_WITH_AUTHORIZED_TIME_EXTENSION"
    assert len(report["routes"]) == 22
    assert report["routes"][:20] == baseline["routes"][:20]
    for new, old in zip(report["routes"][-2:], baseline["routes"][-2:]):
        assert scientific_route(new) == scientific_route(old)
    assert report["summaries"] == baseline["summaries"]
    assert report["initializer_diagnostics"] == baseline["initializer_diagnostics"]
    assert report["specification"] == baseline["specification"]
    assert report["specification"]["is_default_protocol_run"] is False
    assert report["specification"]["alpha_allocation"] == {
        "routes": 0.005, "seed_mixtures": 0.0025, "signed_contrasts": 0.0025,
    }
    disclosure = report["continuation"]
    assert disclosure["original_single_attempt_success"] is False
    assert disclosure["original_attempt_timed_out"] is True
    assert disclosure["checkpoint_resumed"] is False
    assert disclosure["additional_original_unsaved_work_unknown"] is True
    assert disclosure["interrupted_unsaved_prefix_recomputed_from_original_seed"] is True
    assert disclosure["scientific_settings_or_statistical_families_changed"] is False
    assert disclosure["implicit_retries"] == 0
    assert json.loads((output / "report.json").read_text())["decision"] == report["decision"]


def test_population_and_initial_tensor_mismatch_refuse_before_training(reduced_original, monkeypatch):
    budget, _ = reduced_original
    monkeypatch.setattr(original, "validation_pairs", lambda *a: pytest.fail("mismatch reached training/validation"))
    for kwargs, message in (({"expected_population": "wrong"}, "BASE population"),
                            ({"expected_initial": "wrong"}, "initialization")):
        with pytest.raises(completion.CompletionError, match=message):
            completion.run_neural_route(original.SCENARIOS[-1], 1203, original.METHODS[0], budget, lambda: None, **kwargs)


def test_wrong_environment_fails_before_output_creation(reduced_original, tmp_path):
    budget, report = reduced_original
    prefix = completion.ValidatedPrefix(tuple(report["routes"][:20]), budget, {},
        {**versions(), "torch": "deliberately-not-installed-" + torch.__version__})
    output = tmp_path / "must-not-exist"
    with pytest.raises(completion.CompletionError, match="environment differs"):
        completion._complete(prefix, output, 60)
    assert not output.exists()


def test_intent_precedes_work_and_failed_route_is_never_retried(reduced_original, tmp_path, monkeypatch):
    budget, report = reduced_original
    prefix = completion.ValidatedPrefix(tuple(deepcopy(report["routes"][:20])), budget, {}, versions())
    output = tmp_path / "failed"
    calls = []
    def fail(*args, **kwargs):
        assert (output / "continuation-intent.json").is_file()
        calls.append((args[1], args[2]))
        raise RuntimeError("forced bounded failure")
    monkeypatch.setattr(completion, "run_neural_route", fail)
    with pytest.raises(RuntimeError, match="forced bounded failure"):
        completion._complete(prefix, output, 60)
    assert calls == [(1203, original.METHODS[0])]
    assert sorted(p.name for p in output.iterdir()) == ["continuation-failure.json", "continuation-intent.json"]
    with pytest.raises(completion.CompletionError, match="output must be absent"):
        completion._complete(prefix, output, 60)
    assert len(calls) == 1


@pytest.mark.parametrize("deadline", [0, -1, True, 1.0, 86401])
def test_invalid_execution_deadline_cannot_change_scientific_budget(deadline):
    with pytest.raises(completion.CompletionError, match="execution deadline"):
        completion._deadline_seconds(deadline)
    assert original.ExperimentBudget().maximum_seconds == 2400


def test_duplicate_json_key_and_nonfinite_constant_are_refused():
    for payload in (b'{"a":1,"a":2}', b'{"a":NaN}'):
        with pytest.raises(completion.CompletionError):
            completion._json(payload)


def test_original_benchmark_bytes_still_match_prelaunch_verification():
    verification = json.loads(VERIFICATION.read_text())
    source = completion.SOURCE_PATHS[0]
    assert digest(ROOT / source) == verification["source_sha256"][source]
    assert digest(REVIEW) == completion.REVIEW_SHA256
    assert digest(VERIFICATION) == completion.VERIFICATION_SHA256
