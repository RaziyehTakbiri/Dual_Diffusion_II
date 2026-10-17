"""Strict, standard-library-only configuration for the portable synthetic demo.

These small CPU budgets are diagnostic controls, not a paper experiment plan or
a production training configuration.  Model, observation and optimizer choices
are fixed here; changing an iteration count does not change those definitions.
Importing or parsing this module never imports Torch, reads data or runs a model.
"""

from dataclasses import asdict, dataclass, fields
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType


SCHEMA_VERSION = "heterodiff-synthetic-research-config-v1"
PRECISION_POLICY = "BASE_GRAPH_FP64_SHARED_V1"
DOMAINS = ("R3-PHYS", "R4-RETAIL")
METHODS = (
    "association-aware-guide-plus-residual",
    "unified-direct-conditioner",
)
MAX_CONFIG_BYTES = 64 * 1024
FIXED_OPTIMIZER_POLICY = MappingProxyType({
    "name": "AdamW", "lr": 0.001, "betas": (0.9, 0.999), "eps": 1e-8,
    "weight_decay": 0.0, "foreach": False, "fused": False,
    "amsgrad": False, "maximize": False, "capturable": False,
    "differentiable": False,
})


class ResearchConfigError(ValueError):
    """The supplied file is not a supported synthetic research configuration."""


def _require(condition, message):
    if not condition:
        raise ResearchConfigError(message)


def _integer(name, value, lower, upper):
    _require(type(value) is int and lower <= value <= upper,
             f"{name} must be an integer from {lower} through {upper}; booleans are not integers here")


@dataclass(frozen=True, slots=True)
class ResearchConfig:
    """Validated immutable settings for a small, invented-data CPU experiment.

    ``seed`` controls explicit initialization and training/sampling streams in
    the reader runner. ``draws`` is at least two for descriptive evaluation of
    generated samples against the synthetic reference, not a paper outcome.
    The wall-clock budget is passed to the runner; parsing alone cannot enforce
    execution time, reserve resources or establish scientific run readiness.
    """

    schema_version: str
    experiment_id: str
    domain: str
    methods: tuple[str, ...] = METHODS
    device: str = "cpu"
    precision_policy: str = PRECISION_POLICY
    base_steps: int = 2
    conditional_steps: int = 2
    base_samples: int = 2
    conditional_samples: int = 1
    draws: int = 2
    seed: int = 7
    maximum_seconds: int = 120

    def __post_init__(self):
        _require(type(self.schema_version) is str and self.schema_version == SCHEMA_VERSION,
                 f"schema_version must be {SCHEMA_VERSION}")
        _require(type(self.experiment_id) is str and
                 re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", self.experiment_id) is not None,
                 "experiment_id must be 1 to 64 ASCII letters, digits, underscores or hyphens, starting with a letter or digit")
        _require(type(self.domain) is str and self.domain in DOMAINS,
                 "domain must be R3-PHYS or R4-RETAIL for this first synthetic reader interface")
        _require(type(self.methods) is tuple and 1 <= len(self.methods) <= len(METHODS),
                 "methods must contain one or two supported method names")
        _require(all(type(method) is str and method in METHODS for method in self.methods),
                 "methods contains an unsupported method name")
        _require(len(set(self.methods)) == len(self.methods), "methods must not contain duplicates")
        _require(type(self.device) is str and self.device == "cpu",
                 "device must be cpu; this interface does not authorize or run a GPU experiment")
        _require(type(self.precision_policy) is str and self.precision_policy == PRECISION_POLICY,
                 f"precision_policy must remain {PRECISION_POLICY}")
        for name, lower, upper in (
            ("base_steps", 1, 16), ("conditional_steps", 1, 16),
            ("base_samples", 1, 4), ("conditional_samples", 1, 2),
            ("draws", 2, 16), ("seed", 0, 2**64 - 1),
            ("maximum_seconds", 1, 300),
        ):
            _integer(name, getattr(self, name), lower, upper)

    def to_dict(self):
        """Return a fresh JSON-compatible object, including all default values."""
        record = asdict(self)
        record["methods"] = list(self.methods)
        return record


def validate_config(record):
    """Validate a plain dictionary without coercing strings, floats or booleans.

    JSON ``methods`` is a list; it is copied into an immutable tuple. Unknown
    fields (including optimizer, data-path and GPU overrides) are errors.
    """
    _require(type(record) is dict, "configuration must be a JSON object")
    _require(all(type(key) is str for key in record), "configuration field names must be strings")
    allowed = {field.name for field in fields(ResearchConfig)}
    unknown = set(record) - allowed
    _require(not unknown, "unknown configuration fields: " + ", ".join(sorted(unknown)))
    missing = {"schema_version", "experiment_id", "domain"} - set(record)
    _require(not missing, "missing required configuration fields: " + ", ".join(sorted(missing)))
    copied = dict(record)
    if "methods" in copied:
        _require(type(copied["methods"]) is list, "methods must be a JSON array")
        copied["methods"] = tuple(copied["methods"])
    return ResearchConfig(**copied)


def _unique_object(pairs):
    record = {}
    for key, value in pairs:
        _require(key not in record, f"duplicate JSON field: {key}")
        record[key] = value
    return record


def _reject_constant(_value):
    raise ResearchConfigError("non-finite JSON numbers are not permitted")


def parse_config_json(text):
    """Parse one bounded UTF-8 JSON object; duplicate fields are never ignored."""
    _require(type(text) is str, "configuration JSON must be text")
    try:
        size = len(text.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise ResearchConfigError("configuration must be valid UTF-8 text") from exc
    _require(size <= MAX_CONFIG_BYTES, f"configuration exceeds {MAX_CONFIG_BYTES} UTF-8 bytes")
    try:
        record = json.loads(text, object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant)
    except ResearchConfigError:
        raise
    except (ValueError, RecursionError) as exc:
        raise ResearchConfigError("configuration is not valid bounded JSON") from exc
    return validate_config(record)


def load_config(path):
    """Read only the requested bounded local config file and validate its contents."""
    try:
        with Path(path).open("rb") as handle:
            payload = handle.read(MAX_CONFIG_BYTES + 1)
    except (OSError, TypeError, ValueError) as exc:
        raise ResearchConfigError("cannot read the requested local configuration file") from exc
    _require(len(payload) <= MAX_CONFIG_BYTES, f"configuration exceeds {MAX_CONFIG_BYTES} UTF-8 bytes")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ResearchConfigError("configuration file must be valid UTF-8") from exc
    return parse_config_json(text)


def canonical_config_json(config):
    """Stable semantic JSON including explicit defaults and requested method order."""
    _require(type(config) is ResearchConfig, "a validated ResearchConfig is required")
    return json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def config_sha256(config):
    """Hash normalized settings, not original file formatting or provenance."""
    return hashlib.sha256(canonical_config_json(config).encode("ascii")).hexdigest()
