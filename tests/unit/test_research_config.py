"""Portable synthetic configuration tests; no numerical library is imported."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys

import pytest

from heterodiff.research_config import (
    DOMAINS, FIXED_OPTIMIZER_POLICY, MAX_CONFIG_BYTES, METHODS, PRECISION_POLICY,
    SCHEMA_VERSION, ResearchConfig, ResearchConfigError, canonical_config_json,
    config_sha256, load_config, parse_config_json, validate_config,
)


def minimal(**changes):
    record = {"schema_version": SCHEMA_VERSION, "experiment_id": "synthetic-test", "domain": DOMAINS[0]}
    record.update(changes)
    return record


def test_defaults_are_small_explicit_synthetic_cpu_controls():
    config = validate_config(minimal())
    assert config.methods == METHODS
    assert config.device == "cpu"
    assert config.precision_policy == PRECISION_POLICY
    assert (config.base_steps, config.conditional_steps) == (2, 2)
    assert (config.base_samples, config.conditional_samples, config.draws) == (2, 1, 2)
    assert (config.seed, config.maximum_seconds) == (7, 120)
    assert set(config.to_dict()) == {
        "schema_version", "experiment_id", "domain", "methods", "device", "precision_policy",
        "base_steps", "conditional_steps", "base_samples", "conditional_samples", "draws", "seed",
        "maximum_seconds",
    }


def test_config_and_optimizer_policy_are_immutable_and_json_copy_is_independent():
    record = minimal(methods=[METHODS[0]])
    config = validate_config(record)
    record["methods"].append(METHODS[1])
    exported = config.to_dict()
    exported["methods"].append(METHODS[1])
    assert config.methods == (METHODS[0],)
    with pytest.raises(FrozenInstanceError):
        config.base_steps = 12
    with pytest.raises(TypeError):
        FIXED_OPTIMIZER_POLICY["lr"] = 0.5
    assert FIXED_OPTIMIZER_POLICY["betas"] == (0.9, 0.999)
    assert FIXED_OPTIMIZER_POLICY["eps"] == 1e-8
    assert FIXED_OPTIMIZER_POLICY["weight_decay"] == 0.0
    assert all(FIXED_OPTIMIZER_POLICY[key] is False for key in
               ("foreach", "fused", "amsgrad", "maximize", "capturable", "differentiable"))


def test_explicit_and_implicit_defaults_have_identical_semantic_identity():
    config = validate_config(minimal())
    expanded = parse_config_json(json.dumps(config.to_dict(), indent=4))
    reordered = parse_config_json(json.dumps(dict(reversed(list(config.to_dict().items())))))
    assert config == expanded == reordered
    assert canonical_config_json(config) == canonical_config_json(expanded)
    assert config_sha256(config) == config_sha256(expanded) == config_sha256(reordered)
    assert len(config_sha256(config)) == 64
    assert config_sha256(validate_config(minimal(seed=8))) != config_sha256(config)


def test_requested_method_order_is_preserved_in_identity():
    first = validate_config(minimal(methods=list(METHODS)))
    reverse = validate_config(minimal(methods=list(reversed(METHODS))))
    assert reverse.methods == tuple(reversed(METHODS))
    assert config_sha256(first) != config_sha256(reverse)


@pytest.mark.parametrize("field,low,high", [
    ("base_steps", 1, 16), ("conditional_steps", 1, 16),
    ("base_samples", 1, 4), ("conditional_samples", 1, 2),
    ("draws", 2, 16), ("seed", 0, 2**64 - 1), ("maximum_seconds", 1, 300),
])
def test_integer_bounds_are_inclusive_and_no_type_coercion_occurs(field, low, high):
    for value in (low, high):
        assert getattr(validate_config(minimal(**{field: value})), field) == value
    for value in (low - 1, high + 1, True, False, float(low), str(low), None, [], {}, float("nan"), float("inf")):
        with pytest.raises(ResearchConfigError, match=field):
            validate_config(minimal(**{field: value}))


@pytest.mark.parametrize("experiment_id", ["", "../result", "a/b", "a\\b", "a.b", "-demo", "_demo",
                                            "two words", "naïve", "\nresult", "a" * 65, 17, None, True])
def test_experiment_id_is_a_bounded_portable_ascii_identifier(experiment_id):
    with pytest.raises(ResearchConfigError, match="experiment_id"):
        validate_config(minimal(experiment_id=experiment_id))


@pytest.mark.parametrize("experiment_id", ["a", "0", "Demo_12-A", "a" * 64])
def test_valid_experiment_ids(experiment_id):
    assert validate_config(minimal(experiment_id=experiment_id)).experiment_id == experiment_id


@pytest.mark.parametrize("methods", [[], [METHODS[0], METHODS[0]], [METHODS[0]] * 3, ["other"],
                                     [True], [None], [[]], METHODS, METHODS[0], None, {}])
def test_method_roster_is_nonempty_unique_and_exact(methods):
    with pytest.raises(ResearchConfigError, match="methods"):
        validate_config(minimal(methods=methods))


@pytest.mark.parametrize("field,value", [
    ("schema_version", "v0"), ("schema_version", 1),
    ("domain", "new-domain"), ("domain", True),
    ("device", "cuda:0"), ("device", "CPU"), ("device", None),
    ("precision_policy", "LEGACY_FP32"), ("precision_policy", None),
])
def test_semantic_version_domain_device_and_precision_are_not_silently_changed(field, value):
    with pytest.raises(ResearchConfigError, match=field):
        validate_config(minimal(**{field: value}))


@pytest.mark.parametrize("field", ["optimizer", "lr", "data_path", "network", "maximum_seconds_soft", "retries"])
def test_unknown_fields_and_workflow_expansion_are_rejected(field):
    with pytest.raises(ResearchConfigError, match="unknown configuration fields"):
        validate_config(minimal(**{field: 1}))


@pytest.mark.parametrize("field", ["schema_version", "experiment_id", "domain"])
def test_required_fields_cannot_be_omitted(field):
    record = minimal()
    del record[field]
    with pytest.raises(ResearchConfigError, match="missing required"):
        validate_config(record)


@pytest.mark.parametrize("record", [[], (), None, "text", True, 7, {1: 2}])
def test_plain_json_object_with_string_keys_required(record):
    with pytest.raises(ResearchConfigError):
        validate_config(record)


def test_direct_dataclass_construction_obeys_same_value_contract():
    assert ResearchConfig(**minimal()) == validate_config(minimal())
    with pytest.raises(ResearchConfigError, match="methods"):
        ResearchConfig(**minimal(methods=[METHODS[0]]))
    with pytest.raises(ResearchConfigError, match="draws"):
        ResearchConfig(**minimal(draws=True))


@pytest.mark.parametrize("text", [
    '{"domain":"R3-PHYS","domain":"R4-RETAIL"}',
    '{"domain":"R3-PHYS","\\u0064omain":"R3-PHYS"}',
    '{"unknown":{"a":1,"a":2}}',
])
def test_duplicate_json_fields_including_escaped_and_nested_fields_are_rejected(text):
    with pytest.raises(ResearchConfigError, match="duplicate JSON field"):
        parse_config_json(text)


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_nonstandard_nonfinite_json_numbers_rejected(literal):
    text = json.dumps(minimal())[:-1] + ', "seed": ' + literal + '}'
    with pytest.raises(ResearchConfigError, match="non-finite"):
        parse_config_json(text)


def test_finite_json_syntax_that_overflows_to_infinity_is_also_rejected():
    text = json.dumps(minimal())[:-1] + ', "seed": 1e999}'
    with pytest.raises(ResearchConfigError, match="seed"):
        parse_config_json(text)


@pytest.mark.parametrize("text", ["", "{", "{} {}", "{\"domain\":'R3-PHYS'}", "{\"domain\": 1,}",
                                  "\ufeff{}", "[" * 2000, "{\"seed\":" + "9" * 5000 + "}"])
def test_malformed_or_excessively_nested_json_produces_a_config_error(text):
    with pytest.raises(ResearchConfigError):
        parse_config_json(text)


def test_input_size_is_utf8_bytes_and_not_only_character_count():
    with pytest.raises(ResearchConfigError, match="exceeds"):
        parse_config_json(" " * (MAX_CONFIG_BYTES + 1))
    with pytest.raises(ResearchConfigError, match="exceeds"):
        parse_config_json("é" * (MAX_CONFIG_BYTES // 2 + 1))
    with pytest.raises(ResearchConfigError, match="valid UTF-8"):
        parse_config_json("\ud800")
    with pytest.raises(ResearchConfigError, match="must be text"):
        parse_config_json(b"{}")


def test_load_config_reads_exact_requested_file_without_mutation(tmp_path):
    path = tmp_path / "experiment.json"
    payload = json.dumps(minimal()).encode("utf-8")
    path.write_bytes(payload)
    assert load_config(path) == validate_config(minimal())
    assert path.read_bytes() == payload
    assert list(tmp_path.iterdir()) == [path]


def test_load_config_reports_missing_directory_non_utf8_and_oversized_inputs(tmp_path):
    for path in (tmp_path / "missing.json", tmp_path):
        with pytest.raises(ResearchConfigError, match="cannot read"):
            load_config(path)
    path = tmp_path / "bad.json"
    path.write_bytes(b"\xff")
    with pytest.raises(ResearchConfigError, match="valid UTF-8"):
        load_config(path)
    path.write_bytes(b" " * (MAX_CONFIG_BYTES + 1))
    with pytest.raises(ResearchConfigError, match="exceeds"):
        load_config(path)


def test_sample_configs_are_local_path_free_explicit_small_cpu_demos():
    root = Path(__file__).resolve().parents[2]
    for domain, filename in zip(DOMAINS, ("synthetic_physio_cpu.json", "synthetic_retail_cpu.json")):
        path = root / "configs" / filename
        record = json.loads(path.read_text(encoding="utf-8"))
        config = load_config(path)
        assert config.domain == domain
        assert record == config.to_dict()
        assert config.base_steps == config.conditional_steps == config.draws == 2
        assert not any("/Users/" in str(value) or "/Workspace/" in str(value) for value in record.values())


def test_import_and_json_parsing_do_not_import_numerical_libraries():
    src = Path(__file__).resolve().parents[2] / "src"
    code = (
        "import sys; sys.path.insert(0, " + repr(str(src)) + "); "
        "from heterodiff.research_config import parse_config_json; "
        "parse_config_json(" + repr(json.dumps(minimal())) + "); "
        "assert not {'torch', 'numpy', 'scipy', 'heterodiff.events'} & set(sys.modules)"
    )
    completed = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code],
                               capture_output=True, text=True, timeout=10, check=False)
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("value", [minimal(), None, 1])
def test_semantic_helpers_require_validated_configuration(value):
    with pytest.raises(ResearchConfigError, match="validated ResearchConfig"):
        canonical_config_json(value)
    with pytest.raises(ResearchConfigError, match="validated ResearchConfig"):
        config_sha256(value)
