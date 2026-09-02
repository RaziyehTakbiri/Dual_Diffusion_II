"""Materialize CP37's exact fixed-batch counterfactual outcome law.

Checkpoint thirty-seven returns either the first finite-resolution rejection
success or bounded exhaustion.  This additive checkpoint gives that total
outcome an operational boundary: a selected canonical configuration is valid
as an initial state, while exhaustion is a valid no-state result.  A parent
exception or validation failure remains an operational failure and is never
converted to exhaustion.

For one already fixed CP36 proposal-and-score batch, put ``D = 2**64`` and
``p_i = K_i / D``, where ``K_i`` is CP37's conservative quota.  Under the
separate abstract premise that the reserved decision words are iid uniform on
``{0, ..., D-1}``, this module materializes the complete exact law

``P(J=i | B) = p_i * product_{l<i}(1-p_l)`` and
``P(E | B) = product_i(1-p_i)``.

It also aggregates equal candidate configurations and, when selection has
positive probability, records the exact configuration law conditional on
selection.  Here ``B`` is a direct word-free projection containing candidate
configurations, exact score gaps, and quotas.  It excludes reserved decision
words, decisions, outcomes, and parent digests that indirectly bind those
words.  Conditioning on the full CP36 or CP37 record would instead make the
live outcome deterministic.

Separately, CP37's independent-coordinate common-uniform comparison and data
processing through the attempt-to-configuration/exhaustion map give a strict
``A / 2**64`` bound for the augmented dyadic-versus-ideal configuration law.
This unconditioned bound is never reused after conditioning on selection,
where small selection mass can amplify discrepancy.

These statements are not a law for the live fixed-address Philox trace, a law
for CP36 success, an exact ideal-rejection law, or a normalized global tilted
target.  The generic distributional ``initializer_admissible`` flag remains
false.  A selected configuration is only certified structurally valid as one
operational initial state.

Lineage and tag-3 payloads are deliberately absent.  Their current namespaces
do not distinguish every initialization index under one run, so attaching
them here would make the general multi-initialization contract unsound.

Hashes and identities are process-local custody witnesses under a trusted,
unchanged runtime, not cryptographic authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_decision as _decision,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed rejection finite-batch laws require the optional "
            "PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.theory.configuration_reference import (
    MAX_TRANSFORMED_COORDINATE_DIMENSION,
    TransformedConfiguration,
    TransformedEvent,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-finite-batch-law-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_POLICY = (
    "exact-checkpoint37-owner-certificate-result-and-tree-binding;"
    "one-parent-decision-call;selected-state-or-bounded-exhaustion;"
    "complete-exact-fixed-batch-first-success-and-exhaustion-mass-partition;"
    "duplicate-configuration-aggregation;"
    "augmented-configuration-ideal-tv-strictly-less-than-A-over-2^64;"
    "direct-word-free-candidate-gap-quota-conditioning-projection;"
    "selected-configuration-law-only-when-selection-mass-positive;"
    "conditional-abstract-iid-decision-word-premise-only;"
    "selected-configuration-structural-initial-state-validity-not-law-admission;"
    "no-lineage-tag3-new-words-caller-rng-retry-fallback-or-rollback-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCOPE = (
    "bounded-finite-resolution-rejection-operational-initial-state-capability;"
    "fixed-successful-proposal-score-batch-abstract-decision-word-law-only;"
    "live-fixed-address-result-is-deterministic;"
    "not-cp36-success-law-failure-probability-or-unconditional-initializer;"
    "not-live-uniformity-independence-randomness-or-global-one-shot-use;"
    "not-exact-ideal-rejection-normalized-global-tilt-or-analytic-target;"
    "not-generic-distributional-initializer-admission;"
    "not-lineage-tag3-brownian-drift-path-liveness-or-sampler;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR = 1 << 64
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS = 64
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS = 64
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT = (
    MAX_TRANSFORMED_COORDINATE_DIMENSION
)
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES = ("selected", "exhausted")
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM = (
    "P(J=j|B)=p_j*product_{i<j}(1-p_i);" "P(E|B)=product_i(1-p_i);p_i=K_i/2^64"
)
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM = (
    "m_B(x)=sum_{j:x_j=x}P(J=j|B);Z_B=sum_x m_B(x)=1-P(E|B);"
    "if-Z_B>0-then-P(X=x|B,Selected)=m_B(x)/Z_B"
)
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_AUGMENTED_IDEAL_TV_THEOREM = (
    "under-separate-independent-coordinate-ideal-and-dyadic-bernoulli-"
    "sequences-coupled-by-common-continuous-uniforms;data-processing-through-"
    "attempt-to-configuration-plus-exhaustion-gives-TV-strictly-less-than-"
    "A/2^64"
)
INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION = (
    "selected-CP37-canonical-configuration-is-structurally-valid-as-one-"
    "operational-initial-state;CP37-exhaustion-is-a-valid-no-state-outcome;"
    "parent-exception-or-validation-failure-returns-no-result"
)
FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION = (
    "fixed-batch-iid-uint64-decision-word-hypothesis-v1"
)
FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE = (
    "counterfactual-word-substitution-conditional-on-direct-word-free-"
    "candidate-gap-quota-projection;not-full-cp36-or-cp37-record;not-live-"
    "philox-word-law"
)
FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE = (
    "given-the-direct-projection-of-attempt-index-canonical-configuration-"
    "exact-score-gap-and-conservative-quota-that-excludes-every-reserved-word-"
    "decision-outcome-and-parent-digest;replace-each-decision-word-by-a-"
    "separate-abstract-variable-iid-uniform-on-{0,...,2^64-1}-and-independent-"
    "of-that-projection;these-variables-are-not-the-live-philox-words"
)

_SCHEMA_VERSION = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCHEMA_VERSION
)
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCOPE
_CONFIGURATION_THEOREM = (
    INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM
)
_AUGMENTED_IDEAL_TV_THEOREM = (
    INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_AUGMENTED_IDEAL_TV_THEOREM
)
_D = INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR
_ZERO_SHA256 = "0" * 64
_CONDITIONING_PROJECTION_SCHEMA = "fixed-candidate-gap-quota-stream-projection-v2"
_CONDITIONING_PROJECTION_EXCLUDED_FIELDS = (
    "reserved-decision-words",
    "decisions",
    "realized-outcome",
    "preparation-attempt-digests",
    "threshold-digests",
    "parent-result-digests",
)
_MAX_INTEGER_BITS = 131_072
_MAX_PROBABILITY_BITS = 8_192
_MAX_TEXT_LENGTH = 16_384

_HYPOTHESIS_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_ATTEMPT_MASS_TOKEN = object()
_CONFIGURATION_MASS_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

# Freeze the exact checkpoint-37 surfaces used by this module.  Runtime checks
# reject later class/module callback substitution before a public operation.
_DEC_OWNER_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionOwner
_DEC_CERT_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionCertificate
_DEC_RESULT_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionResult
_DEC_THRESHOLD_TYPE = _decision.CounterKeyedInitialTiltRejectionThreshold
_DEC_ATTEMPT_DECISION_TYPE = _decision.CounterKeyedInitialTiltRejectionAttemptDecision
_DEC_PREP_ATTEMPT_TYPE = _decision._PREP_ATTEMPT_TYPE
_DEC_PREP_RESULT_TYPE = _decision._PREP_RESULT_TYPE
_DEC_OWNER_SNAPSHOT = _DEC_OWNER_TYPE._owner_snapshot
_DEC_REQUIRE_OWNER_SNAPSHOT = _DEC_OWNER_TYPE._require_owner_snapshot
_DEC_LIVE_CERTIFICATE = _DEC_OWNER_TYPE._live_certificate
_DEC_DECIDE = _DEC_OWNER_TYPE.decide
_DEC_VALIDATE_RESULT = _DEC_OWNER_TYPE.validate_result
_DEC_CERTIFICATE_PROPERTY = _DEC_OWNER_TYPE.certificate
_DEC_VALIDATE_CERTIFICATE = _decision._validate_certificate
_DEC_VALIDATE_RESULT_VALUES = _decision._validate_result_values
_DEC_CERTIFICATE_FIELDS = _decision._certificate_fields
_DEC_RESULT_FIELDS = _decision._result_fields
_DEC_THRESHOLD_FIELDS = _decision._threshold_fields
_DEC_ATTEMPT_DECISION_FIELDS = _decision._decision_fields
_DEC_FRACTION_PARTS = _decision._fraction_parts
_PREP_RESULT_FIELDS = _decision._prep._result_fields
_PREP_PREFLIGHT_RESULT_VALUES = _decision._PREP_PREFLIGHT_RESULT_VALUES
_PREP_RESULT_SNAPSHOT = _decision._PREP_RESULT_SNAPSHOT
_PREP_REQUIRE_RESULT_UNCHANGED = _decision._PREP_REQUIRE_RESULT_UNCHANGED
_CONFIGURATION_SHA256 = _decision._CONFIGURATION_SHA256


class PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError(ArithmeticError):
    """Fail-closed checkpoint-thirty-eight finite-batch-law error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError("%s exceeds the text resource limit" % name)
    if value != expected:
        raise ValueError("%s differs from the exported value" % name)
    return value


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 hexadecimal string" % name)
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact Boolean" % name)
    if value is not expected:
        raise ValueError("%s must remain %s" % (name, expected))
    return value


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int = 0,
    maximum: int = (1 << 64) - 1,
) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact Python integer" % name)
    if value.bit_length() > _MAX_INTEGER_BITS:
        raise ValueError("%s exceeds the integer-bit resource limit" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s is outside its frozen bound" % name)
    return value


def _signed_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact Python integer" % name)
    if value.bit_length() > _MAX_INTEGER_BITS:
        raise ValueError("%s exceeds the integer-bit resource limit" % name)
    return value


def _fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    checked_numerator = _exact_integer(
        numerator,
        name=name + ".numerator",
        maximum=(1 << _MAX_PROBABILITY_BITS) - 1,
    )
    checked_denominator = _exact_integer(
        denominator,
        name=name + ".denominator",
        minimum=1,
        maximum=(1 << _MAX_PROBABILITY_BITS) - 1,
    )
    result = Fraction(checked_numerator, checked_denominator)
    if (
        result.numerator != checked_numerator
        or result.denominator != checked_denominator
    ):
        raise ValueError("%s must be stored in reduced form" % name)
    return result


def _optional_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    defined: bool,
    name: str,
) -> Optional[Fraction]:
    if defined:
        return _fraction_parts(numerator, denominator, name=name)
    if numerator is not None or denominator is not None:
        raise ValueError("%s must be absent when undefined" % name)
    return None


def _exact_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    length: Optional[int] = None,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) > maximum:
        raise ValueError("%s exceeds its tuple resource limit" % name)
    if length is not None and len(value) != length:
        raise ValueError("%s has the wrong fixed length" % name)
    return value


def _integer_projection(value: int) -> Tuple[str, str]:
    checked = _signed_integer(value, name="digest integer")
    return ("negative" if checked < 0 else "nonnegative", format(abs(checked), "x"))


def _typed_digest_value(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-hex-v1", *_integer_projection(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("digest floats must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("digest floats must use positive zero")
        return ["binary64-hex-v1", value.hex()]
    if type(value) is str:
        if len(value) > _MAX_TEXT_LENGTH:
            raise ValueError("digest text exceeds the resource limit")
        return ["string-v1", value]
    if type(value) is tuple:
        if len(value) > 4_096:
            raise ValueError("digest tuple exceeds the resource limit")
        return ["tuple-v1", [_typed_digest_value(item) for item in value]]
    if isinstance(value, Mapping):
        if len(value) > 512:
            raise ValueError("digest mapping exceeds the resource limit")
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("digest mappings require exact text keys")
            items.append((key, _typed_digest_value(item)))
        items.sort(key=lambda pair: pair[0])
        return ["mapping-v1", items]
    raise TypeError("unsupported digest value of type %s" % type(value).__name__)


def _semantic_digest(value: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _typed_digest_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-initial-tilt-rejection-finite-batch-law-v1\x00")
    digest.update(encoded)
    return digest.hexdigest()


def _configuration_key(
    configuration: object,
    *,
    name: str,
) -> Tuple[Tuple[int, Tuple[float, ...]], ...]:
    if type(configuration) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if (
        len(configuration)
        > INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS
    ):
        raise ValueError("%s exceeds the configuration event limit" % name)
    keys = []
    for position, event in enumerate(configuration):
        event_name = "%s[%d]" % (name, position)
        if type(event) is not TransformedEvent:
            raise TypeError("%s has the wrong exact event type" % event_name)
        event_type = _exact_integer(
            event.event_type,
            name=event_name + ".event_type",
            maximum=(1 << 63) - 1,
        )
        coordinates = _exact_tuple(
            event.coordinates,
            name=event_name + ".coordinates",
            maximum=(INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT),
        )
        checked_coordinates = []
        for coordinate_position, coordinate in enumerate(coordinates):
            if type(coordinate) is not float or not math.isfinite(coordinate):
                raise ValueError(
                    "%s.coordinates[%d] must be finite binary64"
                    % (event_name, coordinate_position)
                )
            if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
                raise ValueError("%s coordinates must use positive zero" % event_name)
            checked_coordinates.append(coordinate)
        keys.append((event_type, tuple(checked_coordinates)))
    return tuple(keys)


def _configuration_digest(configuration: object, *, name: str) -> str:
    _configuration_key(configuration, name=name)
    digest = _CONFIGURATION_SHA256(configuration)
    return _require_sha256(digest, name=name + ".sha256")


def _record_snapshot(record: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return tuple(getattr(record, field) for field in fields)


def _require_record_unchanged(
    record: object,
    fields: Tuple[str, ...],
    snapshot: Tuple[object, ...],
    *,
    name: str,
) -> None:
    if type(snapshot) is not tuple or len(snapshot) != len(fields):
        raise TypeError("%s snapshot is malformed" % name)
    current = _record_snapshot(record, fields)
    for position, (live, before) in enumerate(zip(current, snapshot)):
        field = fields[position]
        if live is before:
            continue
        if type(live) is not type(before) or live != before:
            raise ValueError("%s.%s changed" % (name, field))


def _require_parent_surfaces() -> None:
    expected = (
        (_DEC_OWNER_TYPE._owner_snapshot, _DEC_OWNER_SNAPSHOT),
        (_DEC_OWNER_TYPE._require_owner_snapshot, _DEC_REQUIRE_OWNER_SNAPSHOT),
        (_DEC_OWNER_TYPE._live_certificate, _DEC_LIVE_CERTIFICATE),
        (_DEC_OWNER_TYPE.decide, _DEC_DECIDE),
        (_DEC_OWNER_TYPE.validate_result, _DEC_VALIDATE_RESULT),
        (_DEC_OWNER_TYPE.certificate, _DEC_CERTIFICATE_PROPERTY),
        (_decision._validate_certificate, _DEC_VALIDATE_CERTIFICATE),
        (_decision._validate_result_values, _DEC_VALIDATE_RESULT_VALUES),
        (_decision._certificate_fields, _DEC_CERTIFICATE_FIELDS),
        (_decision._result_fields, _DEC_RESULT_FIELDS),
        (_decision._threshold_fields, _DEC_THRESHOLD_FIELDS),
        (_decision._decision_fields, _DEC_ATTEMPT_DECISION_FIELDS),
        (_decision._fraction_parts, _DEC_FRACTION_PARTS),
        (_decision._prep._result_fields, _PREP_RESULT_FIELDS),
        (_decision._PREP_PREFLIGHT_RESULT_VALUES, _PREP_PREFLIGHT_RESULT_VALUES),
        (_decision._PREP_RESULT_SNAPSHOT, _PREP_RESULT_SNAPSHOT),
        (
            _decision._PREP_REQUIRE_RESULT_UNCHANGED,
            _PREP_REQUIRE_RESULT_UNCHANGED,
        ),
        (_decision._CONFIGURATION_SHA256, _CONFIGURATION_SHA256),
    )
    if any(live is not frozen for live, frozen in expected):
        raise ValueError("checkpoint-37 dependency surface changed")


def _decision_certificate_snapshot(certificate: _DEC_CERT_TYPE) -> Tuple[object, ...]:
    return _record_snapshot(certificate, _DEC_CERTIFICATE_FIELDS())


def _validate_decision_certificate(certificate: object) -> _DEC_CERT_TYPE:
    if type(certificate) is not _DEC_CERT_TYPE:
        raise TypeError("decision certificate has the wrong exact CP37 type")
    snapshot = _decision_certificate_snapshot(certificate)
    checked = _DEC_VALIDATE_CERTIFICATE(certificate)
    _require_record_unchanged(
        certificate,
        _DEC_CERTIFICATE_FIELDS(),
        snapshot,
        name="checkpoint-37 certificate",
    )
    if checked is not certificate:
        raise ValueError("CP37 validation substituted its certificate")
    return certificate


def _runtime_sha256() -> str:
    expected = {
        "dyadic_denominator": 1 << 64,
        "maximum_attempts": 64,
        "maximum_configuration_events": 64,
        "maximum_coordinates_per_event": 65_536,
        "maximum_probability_bits": 8_192,
    }
    actual = {
        "dyadic_denominator": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR
        ),
        "maximum_attempts": INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS,
        "maximum_configuration_events": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS
        ),
        "maximum_coordinates_per_event": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT
        ),
        "maximum_probability_bits": _MAX_PROBABILITY_BITS,
    }
    if actual != expected:
        raise ValueError("rejection-finite-batch-law constants changed")
    if _decision.INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR != _D:
        raise ValueError("checkpoint-37 dyadic denominator changed")
    if _decision.INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS != 64:
        raise ValueError("checkpoint-37 attempt limit changed")
    _require_parent_surfaces()
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "outcome_theorem": (
                INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM
            ),
            "configuration_theorem": (_CONFIGURATION_THEOREM),
            "augmented_ideal_tv_theorem": _AUGMENTED_IDEAL_TV_THEOREM,
            "operational_definition": (
                INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION
            ),
            "conditioning_projection_schema": _CONDITIONING_PROJECTION_SCHEMA,
            "conditioning_projection_excluded_fields": (
                _CONDITIONING_PROJECTION_EXCLUDED_FIELDS
            ),
            "hypothesis_schema": (
                FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION
            ),
            "hypothesis_scope": (FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE),
            "hypothesis_premise": FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE,
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "constants": tuple(sorted(actual.items())),
        }
    )


def _hypothesis_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "hypothesis_sha256")


@dataclass(frozen=True, eq=False, init=False)
class FixedBatchIidUint64DecisionWordHypothesis:
    """Explicit counterfactual source premise for a word-free batch projection."""

    schema_version: str
    hypothesis_scope: str
    word_source_premise: str
    raw_word_domain_size: int
    conditioning_projection_excludes_reserved_words: bool
    conditioning_projection_excludes_decisions_and_outcome: bool
    conditioning_projection_excludes_word_binding_parent_digests: bool
    abstract_words_iid_uniform_uint64: bool
    abstract_words_independent_of_projection: bool
    live_philox_words_identified_with_abstract_words: bool
    live_uniformity_certified: bool
    live_independence_certified: bool
    physical_randomness_certified: bool
    hypothesis_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("fixed-batch word hypotheses cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _HYPOTHESIS_TOKEN:
            raise TypeError("fixed-batch word hypotheses are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("fixed-batch word hypothesis fields are incomplete")
        _validate_hypothesis_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("fixed-batch word hypotheses are not pickle objects")


def _hypothesis_fields() -> Tuple[str, ...]:
    return tuple(FixedBatchIidUint64DecisionWordHypothesis.__annotations__)


def _validate_hypothesis_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        (
            "schema_version",
            FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION,
        ),
        ("hypothesis_scope", FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE),
        ("word_source_premise", FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE),
    ):
        _require_text(values[name], expected, name="hypothesis.%s" % name)
    _exact_integer(
        values["raw_word_domain_size"],
        name="hypothesis.raw_word_domain_size",
        minimum=_D,
        maximum=_D,
    )
    for name in (
        "conditioning_projection_excludes_reserved_words",
        "conditioning_projection_excludes_decisions_and_outcome",
        "conditioning_projection_excludes_word_binding_parent_digests",
        "abstract_words_iid_uniform_uint64",
        "abstract_words_independent_of_projection",
    ):
        _exact_bool(values[name], True, name="hypothesis.%s" % name)
    for name in (
        "live_philox_words_identified_with_abstract_words",
        "live_uniformity_certified",
        "live_independence_certified",
        "physical_randomness_certified",
    ):
        _exact_bool(values[name], False, name="hypothesis.%s" % name)
    _require_sha256(values["hypothesis_sha256"], name="hypothesis.hypothesis_sha256")
    if values["hypothesis_sha256"] != _semantic_digest(_hypothesis_payload(values)):
        raise ValueError("fixed-batch word hypothesis digest differs")


def validate_fixed_batch_iid_uint64_decision_word_hypothesis(
    hypothesis: object,
) -> FixedBatchIidUint64DecisionWordHypothesis:
    """Validate and return the exact sealed counterfactual-word premise."""

    if type(hypothesis) is not FixedBatchIidUint64DecisionWordHypothesis:
        raise TypeError("hypothesis has the wrong exact fixed-batch type")
    _validate_hypothesis_values(
        {name: getattr(hypothesis, name) for name in _hypothesis_fields()}
    )
    return hypothesis


def declare_fixed_batch_iid_uint64_decision_word_hypothesis(
    *,
    hypothesis_scope: object,
    word_source_premise: object,
) -> FixedBatchIidUint64DecisionWordHypothesis:
    """Declare the explicit abstract-word premise without asserting it live."""

    scope = _require_text(
        hypothesis_scope,
        FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE,
        name="hypothesis_scope",
    )
    premise = _require_text(
        word_source_premise,
        FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE,
        name="word_source_premise",
    )
    values: Dict[str, object] = {
        "schema_version": (
            FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION
        ),
        "hypothesis_scope": scope,
        "word_source_premise": premise,
        "raw_word_domain_size": _D,
        "conditioning_projection_excludes_reserved_words": True,
        "conditioning_projection_excludes_decisions_and_outcome": True,
        "conditioning_projection_excludes_word_binding_parent_digests": True,
        "abstract_words_iid_uniform_uint64": True,
        "abstract_words_independent_of_projection": True,
        "live_philox_words_identified_with_abstract_words": False,
        "live_uniformity_certified": False,
        "live_independence_certified": False,
        "physical_randomness_certified": False,
        "hypothesis_sha256": _ZERO_SHA256,
    }
    values["hypothesis_sha256"] = _semantic_digest(_hypothesis_payload(values))
    return FixedBatchIidUint64DecisionWordHypothesis(
        _construction_token=_HYPOTHESIS_TOKEN,
        **values,
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "decision_certificate",
        "word_law_hypothesis",
        "certificate_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
    """Sealed CP37-bound finite-batch counterfactual-law certificate."""

    schema_version: str
    certificate_scope: str
    law_policy: str
    law_role_sha256: str
    word_law_hypothesis: FixedBatchIidUint64DecisionWordHypothesis
    word_law_hypothesis_sha256: str
    decision_certificate: _DEC_CERT_TYPE
    decision_certificate_sha256: str
    decision_runtime_sha256: str
    decision_owner_runtime_identity: int
    process_parameter_sha256: str
    attempt_budget: int
    dyadic_denominator: int
    fixed_batch_outcome_theorem: str
    fixed_batch_configuration_theorem: str
    augmented_configuration_ideal_tv_theorem: str
    operational_outcome_definition: str
    law_runtime_sha256: str
    exact_checkpoint37_owner_binding_certified: bool
    complete_fixed_batch_mass_partition_certified: bool
    duplicate_configuration_aggregation_certified: bool
    augmented_configuration_ideal_tv_comparison_certified: bool
    direct_word_free_conditioning_projection_certified: bool
    fixed_batch_abstract_iid_outcome_law_certified: bool
    fixed_batch_abstract_iid_selected_configuration_law_certified: bool
    selected_configuration_structural_initial_state_validity_certified: bool
    exhaustion_is_valid_no_state_outcome_certified: bool
    operational_failure_distinct_from_exhaustion_certified: bool
    exactly_one_parent_decision_call_certified: bool
    deterministic_replay_certified: bool
    no_new_words_or_caller_rng_certified: bool
    passed: bool
    live_initializer_distribution_admitted: bool
    initializer_admissible: bool
    finite_resolution_global_tilted_law_sampling_certified: bool
    success_conditioned_ideal_tv_comparison_certified: bool
    normalized_tilted_initializer_certified: bool
    exact_ideal_rejection_law_certified: bool
    cp36_failure_probability_certified: bool
    cp36_success_conditioned_proposal_score_record_distribution_certified: bool
    live_uniformity_certified: bool
    live_independence_certified: bool
    physical_randomness_certified: bool
    global_address_one_shot_use_certified: bool
    analytic_target_certified: bool
    lineage_certified: bool
    tag3_payload_coordination_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    test28_closed: bool
    result_promotion_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-finite-batch-law certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError(
                "rejection-finite-batch-law certificates are module-created"
            )
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError(
                "rejection-finite-batch-law certificate fields are incomplete"
            )
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError(
            "rejection-finite-batch-law certificates are not pickle objects"
        )


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate.__annotations__
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint37_owner_binding_certified",
    "complete_fixed_batch_mass_partition_certified",
    "duplicate_configuration_aggregation_certified",
    "augmented_configuration_ideal_tv_comparison_certified",
    "direct_word_free_conditioning_projection_certified",
    "fixed_batch_abstract_iid_outcome_law_certified",
    "fixed_batch_abstract_iid_selected_configuration_law_certified",
    "selected_configuration_structural_initial_state_validity_certified",
    "exhaustion_is_valid_no_state_outcome_certified",
    "operational_failure_distinct_from_exhaustion_certified",
    "exactly_one_parent_decision_call_certified",
    "deterministic_replay_certified",
    "no_new_words_or_caller_rng_certified",
    "passed",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "live_initializer_distribution_admitted",
    "initializer_admissible",
    "finite_resolution_global_tilted_law_sampling_certified",
    "success_conditioned_ideal_tv_comparison_certified",
    "normalized_tilted_initializer_certified",
    "exact_ideal_rejection_law_certified",
    "cp36_failure_probability_certified",
    "cp36_success_conditioned_proposal_score_record_distribution_certified",
    "live_uniformity_certified",
    "live_independence_certified",
    "physical_randomness_certified",
    "global_address_one_shot_use_certified",
    "analytic_target_certified",
    "lineage_certified",
    "tag3_payload_coordination_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "test28_closed",
    "result_promotion_admissible",
    "runtime_portable",
    "cryptographic_authentication",
)


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "law_policy": _POLICY,
        "fixed_batch_outcome_theorem": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM
        ),
        "fixed_batch_configuration_theorem": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM
        ),
        "augmented_configuration_ideal_tv_theorem": _AUGMENTED_IDEAL_TV_THEOREM,
        "operational_outcome_definition": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION
        ),
    }
    for name, expected in expected_text.items():
        _require_text(values[name], expected, name="certificate.%s" % name)
    for name in (
        "law_role_sha256",
        "word_law_hypothesis_sha256",
        "decision_certificate_sha256",
        "decision_runtime_sha256",
        "process_parameter_sha256",
        "law_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate.%s" % name)
    hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
        values["word_law_hypothesis"]
    )
    if values["word_law_hypothesis_sha256"] != hypothesis.hypothesis_sha256:
        raise ValueError("certificate word-law hypothesis digest differs")
    parent = _validate_decision_certificate(values["decision_certificate"])
    expected_scalars = {
        "decision_certificate_sha256": parent.certificate_sha256,
        "decision_runtime_sha256": parent.decision_runtime_sha256,
        "process_parameter_sha256": parent.process_parameter_sha256,
        "attempt_budget": parent.attempt_budget,
        "dyadic_denominator": _D,
        "law_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("certificate.%s differs" % name)
    _exact_integer(
        values["decision_owner_runtime_identity"],
        name="certificate.decision_owner_runtime_identity",
        minimum=1,
        maximum=(1 << 64) - 1,
    )
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate.%s" % name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate.%s" % name)
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("rejection-finite-batch-law certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    ):
        raise TypeError(
            "certificate has the wrong exact rejection-finite-batch-law type"
        )
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    decision_owner: _DEC_OWNER_TYPE,
    word_law_hypothesis: FixedBatchIidUint64DecisionWordHypothesis,
    law_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
    parent = _DEC_CERTIFICATE_PROPERTY.__get__(decision_owner, _DEC_OWNER_TYPE)
    _validate_decision_certificate(parent)
    hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
        word_law_hypothesis
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "law_policy": _POLICY,
        "law_role_sha256": law_role_sha256,
        "word_law_hypothesis": hypothesis,
        "word_law_hypothesis_sha256": hypothesis.hypothesis_sha256,
        "decision_certificate": parent,
        "decision_certificate_sha256": parent.certificate_sha256,
        "decision_runtime_sha256": parent.decision_runtime_sha256,
        "decision_owner_runtime_identity": id(decision_owner),
        "process_parameter_sha256": parent.process_parameter_sha256,
        "attempt_budget": parent.attempt_budget,
        "dyadic_denominator": _D,
        "fixed_batch_outcome_theorem": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM
        ),
        "fixed_batch_configuration_theorem": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM
        ),
        "augmented_configuration_ideal_tv_theorem": _AUGMENTED_IDEAL_TV_THEOREM,
        "operational_outcome_definition": (
            INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION
        ),
        "law_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _attempt_mass_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "threshold",
        "preparation_attempt",
        "configuration",
        "mass_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionAttemptMass:
    """One exact first-success mass under the fixed-batch abstract premise."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    certificate_sha256: str
    threshold: _DEC_THRESHOLD_TYPE
    threshold_sha256: str
    preparation_attempt: _DEC_PREP_ATTEMPT_TYPE
    preparation_attempt_sha256: str
    attempt_index: int
    configuration: TransformedConfiguration
    configuration_sha256: str
    configuration_ordinal: int
    delta_numerator: int
    delta_denominator: int
    acceptance_quota: int
    acceptance_probability_numerator: int
    acceptance_probability_denominator: int
    survival_before_numerator: int
    survival_before_denominator: int
    fixed_batch_first_selection_probability_numerator: int
    fixed_batch_first_selection_probability_denominator: int
    survival_after_numerator: int
    survival_after_denominator: int
    selected_conditioned_probability_defined: bool
    selected_conditioned_probability_numerator: Optional[int]
    selected_conditioned_probability_denominator: Optional[int]
    abstract_iid_decision_word_premise_only: bool
    mass_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "rejection-finite-batch-law attempt masses cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATTEMPT_MASS_TOKEN:
            raise TypeError(
                "rejection-finite-batch-law attempt masses are module-created"
            )
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError(
                "rejection-finite-batch-law attempt-mass fields are incomplete"
            )
        _validate_attempt_mass_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError(
            "rejection-finite-batch-law attempt masses are not pickle objects"
        )


def _attempt_mass_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionAttemptMass.__annotations__)


def _preflight_threshold(
    threshold: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
    name: str,
) -> _DEC_THRESHOLD_TYPE:
    if type(threshold) is not _DEC_THRESHOLD_TYPE:
        raise TypeError("%s has the wrong exact CP37 threshold type" % name)
    if threshold.certificate is not certificate.decision_certificate:
        raise ValueError("%s belongs to another CP37 certificate" % name)
    _require_sha256(threshold.threshold_sha256, name=name + ".threshold_sha256")
    _exact_integer(
        threshold.attempt_index,
        name=name + ".attempt_index",
        maximum=certificate.attempt_budget - 1,
    )
    _exact_integer(
        threshold.acceptance_quota,
        name=name + ".acceptance_quota",
        maximum=_D,
    )
    return threshold


def _validate_attempt_mass_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("attempt mass trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="attempt_mass.schema")
    _require_sha256(
        values["certificate_sha256"], name="attempt_mass.certificate_sha256"
    )
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("attempt mass certificate digest differs")
    threshold = _preflight_threshold(
        values["threshold"], certificate=certificate, name="attempt_mass.threshold"
    )
    _require_sha256(values["threshold_sha256"], name="attempt_mass.threshold_sha256")
    if values["threshold_sha256"] != threshold.threshold_sha256:
        raise ValueError("attempt mass threshold digest differs")
    attempt = values["preparation_attempt"]
    if type(attempt) is not _DEC_PREP_ATTEMPT_TYPE:
        raise TypeError("attempt mass has the wrong exact CP36 attempt type")
    if attempt is not threshold.preparation_attempt:
        raise ValueError("attempt mass lost CP36 attempt identity")
    _require_sha256(
        values["preparation_attempt_sha256"],
        name="attempt_mass.preparation_attempt_sha256",
    )
    if values["preparation_attempt_sha256"] != attempt.attempt_sha256:
        raise ValueError("attempt mass CP36 attempt digest differs")
    attempt_index = _exact_integer(
        values["attempt_index"],
        name="attempt_mass.attempt_index",
        maximum=certificate.attempt_budget - 1,
    )
    if (
        attempt_index != threshold.attempt_index
        or attempt_index != attempt.attempt_index
    ):
        raise ValueError("attempt mass index differs from its parents")
    configuration = values["configuration"]
    if configuration is not attempt.canonical_configuration:
        raise ValueError("attempt mass configuration identity differs")
    configuration_digest = _configuration_digest(
        configuration, name="attempt_mass.configuration"
    )
    _require_sha256(
        values["configuration_sha256"], name="attempt_mass.configuration_sha256"
    )
    if values["configuration_sha256"] != configuration_digest or (
        values["configuration_sha256"] != attempt.canonical_configuration_sha256
    ):
        raise ValueError("attempt mass configuration digest differs")
    _exact_integer(
        values["configuration_ordinal"],
        name="attempt_mass.configuration_ordinal",
        maximum=certificate.attempt_budget - 1,
    )
    delta = _DEC_FRACTION_PARTS(
        values["delta_numerator"],
        values["delta_denominator"],
        name="attempt_mass.delta",
    )
    expected_delta = Fraction(
        threshold.delta_numerator,
        threshold.delta_denominator,
    )
    if delta != expected_delta or delta > 0:
        raise ValueError("attempt mass score gap differs")
    quota = _exact_integer(
        values["acceptance_quota"],
        name="attempt_mass.acceptance_quota",
        maximum=_D,
    )
    if quota != threshold.acceptance_quota:
        raise ValueError("attempt mass quota differs")
    acceptance = _fraction_parts(
        values["acceptance_probability_numerator"],
        values["acceptance_probability_denominator"],
        name="attempt_mass.acceptance_probability",
    )
    if acceptance != Fraction(quota, _D):
        raise ValueError("attempt mass acceptance probability differs")
    survival = _fraction_parts(
        values["survival_before_numerator"],
        values["survival_before_denominator"],
        name="attempt_mass.survival_before",
    )
    first_mass = _fraction_parts(
        values["fixed_batch_first_selection_probability_numerator"],
        values["fixed_batch_first_selection_probability_denominator"],
        name="attempt_mass.fixed_batch_first_selection_probability",
    )
    if first_mass != survival * acceptance:
        raise ValueError("attempt first-selection mass differs")
    survival_after = _fraction_parts(
        values["survival_after_numerator"],
        values["survival_after_denominator"],
        name="attempt_mass.survival_after",
    )
    if survival_after != survival * (1 - acceptance):
        raise ValueError("attempt survival-after mass differs")
    if survival != first_mass + survival_after:
        raise ValueError("attempt mass does not telescope")
    defined = values["selected_conditioned_probability_defined"]
    if type(defined) is not bool:
        raise TypeError("attempt conditioned-law flag must be an exact Boolean")
    conditioned = _optional_fraction_parts(
        values["selected_conditioned_probability_numerator"],
        values["selected_conditioned_probability_denominator"],
        defined=defined,
        name="attempt_mass.selected_conditioned_probability",
    )
    if conditioned is not None and not 0 <= conditioned <= 1:
        raise ValueError("attempt conditioned probability escaped [0,1]")
    _exact_bool(
        values["abstract_iid_decision_word_premise_only"],
        True,
        name="attempt_mass.abstract_iid_decision_word_premise_only",
    )
    _require_sha256(values["mass_sha256"], name="attempt_mass.mass_sha256")
    if values["mass_sha256"] != _semantic_digest(_attempt_mass_payload(values)):
        raise ValueError("attempt-mass digest differs")


def _make_attempt_mass(
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
    threshold: _DEC_THRESHOLD_TYPE,
    *,
    configuration_ordinal: int,
    survival_before: Fraction,
    selection_probability: Fraction,
) -> CounterKeyedInitialTiltRejectionAttemptMass:
    attempt = threshold.preparation_attempt
    acceptance = Fraction(threshold.acceptance_quota, _D)
    first_mass = survival_before * acceptance
    survival_after = survival_before * (1 - acceptance)
    conditioned = (
        None if selection_probability == 0 else first_mass / selection_probability
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "threshold": threshold,
        "threshold_sha256": threshold.threshold_sha256,
        "preparation_attempt": attempt,
        "preparation_attempt_sha256": attempt.attempt_sha256,
        "attempt_index": threshold.attempt_index,
        "configuration": attempt.canonical_configuration,
        "configuration_sha256": attempt.canonical_configuration_sha256,
        "configuration_ordinal": configuration_ordinal,
        "delta_numerator": threshold.delta_numerator,
        "delta_denominator": threshold.delta_denominator,
        "acceptance_quota": threshold.acceptance_quota,
        "acceptance_probability_numerator": acceptance.numerator,
        "acceptance_probability_denominator": acceptance.denominator,
        "survival_before_numerator": survival_before.numerator,
        "survival_before_denominator": survival_before.denominator,
        "fixed_batch_first_selection_probability_numerator": first_mass.numerator,
        "fixed_batch_first_selection_probability_denominator": first_mass.denominator,
        "survival_after_numerator": survival_after.numerator,
        "survival_after_denominator": survival_after.denominator,
        "selected_conditioned_probability_defined": conditioned is not None,
        "selected_conditioned_probability_numerator": (
            None if conditioned is None else conditioned.numerator
        ),
        "selected_conditioned_probability_denominator": (
            None if conditioned is None else conditioned.denominator
        ),
        "abstract_iid_decision_word_premise_only": True,
        "mass_sha256": _ZERO_SHA256,
    }
    values["mass_sha256"] = _semantic_digest(_attempt_mass_payload(values))
    return CounterKeyedInitialTiltRejectionAttemptMass(
        _construction_token=_ATTEMPT_MASS_TOKEN,
        **values,
    )


def _configuration_mass_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "configuration", "mass_sha256")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionConfigurationMass:
    """One duplicate-aggregated candidate-configuration mass."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    certificate_sha256: str
    configuration_ordinal: int
    representative_attempt_index: int
    attempt_indices: Tuple[int, ...]
    duplicate_attempt_count: int
    configuration: TransformedConfiguration
    configuration_sha256: str
    fixed_batch_selection_probability_numerator: int
    fixed_batch_selection_probability_denominator: int
    selected_conditioned_probability_defined: bool
    selected_conditioned_probability_numerator: Optional[int]
    selected_conditioned_probability_denominator: Optional[int]
    exact_configuration_key_aggregation: bool
    abstract_iid_decision_word_premise_only: bool
    mass_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "rejection-finite-batch-law configuration masses cannot subclass"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CONFIGURATION_MASS_TOKEN:
            raise TypeError("configuration masses are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("configuration-mass fields are incomplete")
        _validate_configuration_mass_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("configuration masses are not pickle objects")


def _configuration_mass_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionConfigurationMass.__annotations__)


def _validate_configuration_mass_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("configuration mass trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(
        values["schema_version"], _SCHEMA_VERSION, name="configuration_mass.schema"
    )
    _require_sha256(
        values["certificate_sha256"], name="configuration_mass.certificate_sha256"
    )
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("configuration mass certificate digest differs")
    ordinal = _exact_integer(
        values["configuration_ordinal"],
        name="configuration_mass.configuration_ordinal",
        maximum=certificate.attempt_budget - 1,
    )
    representative = _exact_integer(
        values["representative_attempt_index"],
        name="configuration_mass.representative_attempt_index",
        maximum=certificate.attempt_budget - 1,
    )
    indices = _exact_tuple(
        values["attempt_indices"],
        name="configuration_mass.attempt_indices",
        maximum=certificate.attempt_budget,
    )
    if not indices:
        raise ValueError("configuration mass must cover at least one attempt")
    checked_indices = tuple(
        _exact_integer(
            item,
            name="configuration_mass.attempt_indices[%d]" % position,
            maximum=certificate.attempt_budget - 1,
        )
        for position, item in enumerate(indices)
    )
    if checked_indices != tuple(sorted(set(checked_indices))):
        raise ValueError("configuration mass attempt indices must increase uniquely")
    if representative != checked_indices[0]:
        raise ValueError("configuration representative is not the first attempt")
    count = _exact_integer(
        values["duplicate_attempt_count"],
        name="configuration_mass.duplicate_attempt_count",
        minimum=1,
        maximum=certificate.attempt_budget,
    )
    if count != len(checked_indices):
        raise ValueError("configuration duplicate count differs")
    configuration = values["configuration"]
    configuration_digest = _configuration_digest(
        configuration, name="configuration_mass.configuration"
    )
    _require_sha256(
        values["configuration_sha256"],
        name="configuration_mass.configuration_sha256",
    )
    if values["configuration_sha256"] != configuration_digest:
        raise ValueError("configuration mass configuration digest differs")
    mass = _fraction_parts(
        values["fixed_batch_selection_probability_numerator"],
        values["fixed_batch_selection_probability_denominator"],
        name="configuration_mass.fixed_batch_selection_probability",
    )
    if not 0 <= mass <= 1:
        raise ValueError("configuration mass escaped [0,1]")
    defined = values["selected_conditioned_probability_defined"]
    if type(defined) is not bool:
        raise TypeError("configuration conditioned-law flag must be exact Boolean")
    conditioned = _optional_fraction_parts(
        values["selected_conditioned_probability_numerator"],
        values["selected_conditioned_probability_denominator"],
        defined=defined,
        name="configuration_mass.selected_conditioned_probability",
    )
    if conditioned is not None and not 0 <= conditioned <= 1:
        raise ValueError("configuration conditioned mass escaped [0,1]")
    _exact_bool(
        values["exact_configuration_key_aggregation"],
        True,
        name="configuration_mass.exact_configuration_key_aggregation",
    )
    _exact_bool(
        values["abstract_iid_decision_word_premise_only"],
        True,
        name="configuration_mass.abstract_iid_decision_word_premise_only",
    )
    _require_sha256(values["mass_sha256"], name="configuration_mass.mass_sha256")
    if ordinal >= certificate.attempt_budget:
        raise ValueError("configuration ordinal exceeds the attempt budget")
    if values["mass_sha256"] != _semantic_digest(_configuration_mass_payload(values)):
        raise ValueError("configuration-mass digest differs")


def _make_configuration_mass(
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
    *,
    configuration_ordinal: int,
    attempt_indices: Tuple[int, ...],
    configuration: TransformedConfiguration,
    configuration_sha256: str,
    fixed_batch_mass: Fraction,
    selection_probability: Fraction,
) -> CounterKeyedInitialTiltRejectionConfigurationMass:
    conditioned = (
        None if selection_probability == 0 else fixed_batch_mass / selection_probability
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "configuration_ordinal": configuration_ordinal,
        "representative_attempt_index": attempt_indices[0],
        "attempt_indices": attempt_indices,
        "duplicate_attempt_count": len(attempt_indices),
        "configuration": configuration,
        "configuration_sha256": configuration_sha256,
        "fixed_batch_selection_probability_numerator": fixed_batch_mass.numerator,
        "fixed_batch_selection_probability_denominator": fixed_batch_mass.denominator,
        "selected_conditioned_probability_defined": conditioned is not None,
        "selected_conditioned_probability_numerator": (
            None if conditioned is None else conditioned.numerator
        ),
        "selected_conditioned_probability_denominator": (
            None if conditioned is None else conditioned.denominator
        ),
        "exact_configuration_key_aggregation": True,
        "abstract_iid_decision_word_premise_only": True,
        "mass_sha256": _ZERO_SHA256,
    }
    values["mass_sha256"] = _semantic_digest(_configuration_mass_payload(values))
    return CounterKeyedInitialTiltRejectionConfigurationMass(
        _construction_token=_CONFIGURATION_MASS_TOKEN,
        **values,
    )


@dataclass(frozen=True)
class _LawData:
    conditioning_projection_sha256: str
    attempt_masses: Tuple[CounterKeyedInitialTiltRejectionAttemptMass, ...]
    configuration_masses: Tuple[CounterKeyedInitialTiltRejectionConfigurationMass, ...]
    attempt_to_configuration_ordinal: Tuple[int, ...]
    exhaustion_probability: Fraction
    selection_probability: Fraction


def _first_success_partition(
    quotas: object,
) -> Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...], Fraction, Fraction]:
    checked_quotas = _exact_tuple(
        quotas,
        name="first_success_partition.quotas",
        maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS,
    )
    if not checked_quotas:
        raise ValueError("first-success partition requires at least one quota")
    survival = Fraction(1)
    survival_befores = []
    first_masses = []
    for position, quota in enumerate(checked_quotas):
        checked_quota = _exact_integer(
            quota,
            name="first_success_partition.quotas[%d]" % position,
            maximum=_D,
        )
        survival_befores.append(survival)
        acceptance = Fraction(checked_quota, _D)
        first_masses.append(survival * acceptance)
        survival *= 1 - acceptance
    exhaustion = survival
    selection = 1 - exhaustion
    if sum(first_masses, Fraction(0)) != selection:
        raise PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError(
            "first-success masses do not telescope"
        )
    return (
        tuple(survival_befores),
        tuple(first_masses),
        exhaustion,
        selection,
    )


def _stable_configuration_key_partition(
    configuration_keys: object,
) -> Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...], Tuple[int, ...]]:
    keys = _exact_tuple(
        configuration_keys,
        name="configuration_key_partition.keys",
        maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS,
    )
    if not keys:
        raise ValueError("configuration-key partition requires at least one key")
    unique_keys = []
    representative_indices = []
    contributors = []
    mapping = []
    for position, key in enumerate(keys):
        if type(key) is not tuple:
            raise TypeError("configuration partition keys must be exact tuples")
        try:
            ordinal = unique_keys.index(key)
        except ValueError:
            ordinal = len(unique_keys)
            unique_keys.append(key)
            representative_indices.append(position)
            contributors.append([])
        contributors[ordinal].append(position)
        mapping.append(ordinal)
    return (
        tuple(representative_indices),
        tuple(tuple(indices) for indices in contributors),
        tuple(mapping),
    )


def _preflight_decision_result(
    result: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
) -> _DEC_RESULT_TYPE:
    if type(result) is not _DEC_RESULT_TYPE:
        raise TypeError("parent result has the wrong exact CP37 type")
    if result.certificate is not certificate.decision_certificate:
        raise ValueError("parent result belongs to another CP37 certificate")
    _require_sha256(result.result_sha256, name="parent_result.result_sha256")
    attempt_budget = _exact_integer(
        result.attempt_budget,
        name="parent_result.attempt_budget",
        minimum=1,
        maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS,
    )
    if attempt_budget != certificate.attempt_budget:
        raise ValueError("parent result attempt budget differs")
    thresholds = _exact_tuple(
        result.thresholds,
        name="parent_result.thresholds",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    decisions = _exact_tuple(
        result.decisions,
        name="parent_result.decisions",
        maximum=certificate.attempt_budget,
    )
    if not decisions:
        raise ValueError("parent result has no interpreted decision")
    for position, decision in enumerate(decisions):
        if type(decision) is not _DEC_ATTEMPT_DECISION_TYPE:
            raise TypeError(
                "parent_result.decisions[%d] has the wrong exact type" % position
            )
        _exact_integer(
            decision.attempt_index,
            name="parent_result.decisions[%d].attempt_index" % position,
            maximum=certificate.attempt_budget - 1,
        )
        _exact_integer(
            decision.decision_word,
            name="parent_result.decisions[%d].decision_word" % position,
        )
        _require_sha256(
            decision.decision_sha256,
            name="parent_result.decisions[%d].decision_sha256" % position,
        )
    for position, threshold in enumerate(thresholds):
        checked_threshold = _preflight_threshold(
            threshold,
            certificate=certificate,
            name="parent_result.thresholds[%d]" % position,
        )
        attempt = checked_threshold.preparation_attempt
        if type(attempt) is not _DEC_PREP_ATTEMPT_TYPE:
            raise TypeError("parent threshold has the wrong CP36 attempt type")
        configuration = _exact_tuple(
            attempt.canonical_configuration,
            name="parent_result.thresholds[%d].configuration" % position,
            maximum=(INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS),
        )
        _configuration_key(
            configuration,
            name="parent_result.thresholds[%d].configuration" % position,
        )
    preparation_result = result.preparation_result
    if type(preparation_result) is not _DEC_PREP_RESULT_TYPE:
        raise TypeError("parent result has the wrong exact CP36 preparation type")
    _PREP_PREFLIGHT_RESULT_VALUES(
        {name: getattr(preparation_result, name) for name in _PREP_RESULT_FIELDS()}
    )
    if len(preparation_result.attempts) != len(thresholds):
        raise ValueError("parent preparation attempt count differs")
    for position, threshold in enumerate(thresholds):
        if threshold.preparation_attempt is not preparation_result.attempts[position]:
            raise ValueError("parent threshold lost CP36 attempt identity")
    if type(result.outcome) is not str or (
        result.outcome not in _decision.INITIAL_TILT_REJECTION_DECISION_OUTCOMES
    ):
        raise ValueError("parent result outcome is unknown")
    return result


def _decision_result_tree_snapshot(result: _DEC_RESULT_TYPE) -> Tuple[object, ...]:
    return (
        _record_snapshot(result, _DEC_RESULT_FIELDS()),
        tuple(
            _record_snapshot(threshold, _DEC_THRESHOLD_FIELDS())
            for threshold in result.thresholds
        ),
        tuple(
            _record_snapshot(item, _DEC_ATTEMPT_DECISION_FIELDS())
            for item in result.decisions
        ),
        _PREP_RESULT_SNAPSHOT(result.preparation_result),
    )


def _require_decision_result_tree_unchanged(
    result: _DEC_RESULT_TYPE,
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
) -> None:
    _preflight_decision_result(result, certificate=certificate)
    if type(snapshot) is not tuple or len(snapshot) != 4:
        raise TypeError("CP37 result-tree snapshot is malformed")
    result_before, threshold_befores, decision_befores, preparation_before = snapshot
    _require_record_unchanged(
        result,
        _DEC_RESULT_FIELDS(),
        result_before,
        name="CP37 result",
    )
    if len(threshold_befores) != len(result.thresholds):
        raise ValueError("CP37 threshold count changed")
    for position, (threshold, before) in enumerate(
        zip(result.thresholds, threshold_befores)
    ):
        _require_record_unchanged(
            threshold,
            _DEC_THRESHOLD_FIELDS(),
            before,
            name="CP37 threshold %d" % position,
        )
    if len(decision_befores) != len(result.decisions):
        raise ValueError("CP37 decision count changed")
    for position, (item, before) in enumerate(zip(result.decisions, decision_befores)):
        _require_record_unchanged(
            item,
            _DEC_ATTEMPT_DECISION_FIELDS(),
            before,
            name="CP37 decision %d" % position,
        )
    _PREP_REQUIRE_RESULT_UNCHANGED(
        result.preparation_result,
        preparation_before,
        certificate=certificate.decision_certificate.preparation_certificate,
    )


def _projection_digest_bytes(
    digest: object,
    tag: bytes,
    payload: bytes,
) -> None:
    if type(tag) is not bytes or not tag:
        raise TypeError("projection digest tags must be nonempty exact bytes")
    if type(payload) is not bytes:
        raise TypeError("projection digest payloads must be exact bytes")
    if len(tag) >= 1 << 16 or len(payload) >= 1 << 64:
        raise ValueError("projection digest field exceeds its framing limit")
    digest.update(len(tag).to_bytes(2, "big"))
    digest.update(tag)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)


def _projection_digest_integer(
    digest: object,
    tag: bytes,
    value: object,
) -> None:
    checked = _signed_integer(value, name="projection digest integer")
    sign = b"-" if checked < 0 else b"+"
    payload = sign + format(abs(checked), "x").encode("ascii")
    _projection_digest_bytes(digest, tag, payload)


def _conditioning_projection_sha256(result: _DEC_RESULT_TYPE) -> str:
    digest = hashlib.sha256()
    digest.update(
        b"heterodiff-initial-tilt-rejection-finite-batch-law-"
        b"conditioning-projection-v2\x00"
    )
    _projection_digest_bytes(
        digest,
        b"projection-schema",
        _CONDITIONING_PROJECTION_SCHEMA.encode("ascii"),
    )
    _projection_digest_integer(digest, b"attempt-count", len(result.thresholds))
    for position, threshold in enumerate(result.thresholds):
        configuration_key = _configuration_key(
            threshold.preparation_attempt.canonical_configuration,
            name="conditioning_projection.configuration[%d]" % position,
        )
        _projection_digest_integer(digest, b"attempt-index", position)
        _projection_digest_integer(
            digest, b"configuration-event-count", len(configuration_key)
        )
        for event_position, (event_type, coordinates) in enumerate(configuration_key):
            _projection_digest_integer(digest, b"event-index", event_position)
            _projection_digest_integer(digest, b"event-type", event_type)
            _projection_digest_integer(digest, b"coordinate-count", len(coordinates))
            for coordinate in coordinates:
                _projection_digest_bytes(
                    digest,
                    b"coordinate-binary64-hex",
                    coordinate.hex().encode("ascii"),
                )
        for tag, value in (
            (b"delta-numerator", threshold.delta_numerator),
            (b"delta-denominator", threshold.delta_denominator),
            (b"acceptance-quota", threshold.acceptance_quota),
        ):
            _projection_digest_integer(digest, tag, value)
    _projection_digest_bytes(
        digest,
        b"excluded-fields",
        ";".join(_CONDITIONING_PROJECTION_EXCLUDED_FIELDS).encode("ascii"),
    )
    return digest.hexdigest()


def _materialize_law(
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
    parent: _DEC_RESULT_TYPE,
) -> _LawData:
    _preflight_decision_result(parent, certificate=certificate)
    thresholds = parent.thresholds
    configuration_keys = []
    for position, threshold in enumerate(thresholds):
        attempt = threshold.preparation_attempt
        key = _configuration_key(
            attempt.canonical_configuration,
            name="law.configuration[%d]" % position,
        )
        configuration_keys.append(key)
    (
        representative_indices,
        contributor_lists,
        attempt_to_configuration,
    ) = _stable_configuration_key_partition(tuple(configuration_keys))
    unique_configurations = tuple(
        thresholds[index].preparation_attempt.canonical_configuration
        for index in representative_indices
    )
    unique_configuration_sha256s = tuple(
        thresholds[index].preparation_attempt.canonical_configuration_sha256
        for index in representative_indices
    )

    survival_befores, first_masses, exhaustion, selection = _first_success_partition(
        tuple(threshold.acceptance_quota for threshold in thresholds)
    )

    attempt_masses = tuple(
        _make_attempt_mass(
            certificate,
            threshold,
            configuration_ordinal=attempt_to_configuration[position],
            survival_before=survival_befores[position],
            selection_probability=selection,
        )
        for position, threshold in enumerate(thresholds)
    )
    configuration_masses = []
    for ordinal, indices in enumerate(contributor_lists):
        aggregate = sum((first_masses[index] for index in indices), Fraction(0))
        configuration_masses.append(
            _make_configuration_mass(
                certificate,
                configuration_ordinal=ordinal,
                attempt_indices=tuple(indices),
                configuration=unique_configurations[ordinal],
                configuration_sha256=unique_configuration_sha256s[ordinal],
                fixed_batch_mass=aggregate,
                selection_probability=selection,
            )
        )
    configuration_mass_tuple = tuple(configuration_masses)
    if (
        sum(
            (
                Fraction(
                    row.fixed_batch_selection_probability_numerator,
                    row.fixed_batch_selection_probability_denominator,
                )
                for row in configuration_mass_tuple
            ),
            Fraction(0),
        )
        != selection
    ):
        raise PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError(
            "configuration masses do not equal the selection normalizer"
        )
    if (
        selection > 0
        and sum(
            (
                Fraction(
                    row.selected_conditioned_probability_numerator,
                    row.selected_conditioned_probability_denominator,
                )
                for row in configuration_mass_tuple
            ),
            Fraction(0),
        )
        != 1
    ):
        raise PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError(
            "conditioned configuration masses do not normalize"
        )
    return _LawData(
        conditioning_projection_sha256=_conditioning_projection_sha256(parent),
        attempt_masses=attempt_masses,
        configuration_masses=configuration_mass_tuple,
        attempt_to_configuration_ordinal=tuple(attempt_to_configuration),
        exhaustion_probability=exhaustion,
        selection_probability=selection,
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_decision_result",
        "attempt_masses",
        "configuration_masses",
        "selected_configuration",
        "result_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
    """A live selected/exhausted outcome plus its counterfactual batch law."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    certificate_sha256: str
    parent_decision_result: _DEC_RESULT_TYPE
    parent_decision_result_sha256: str
    run_id: int
    initialization_index: int
    attempt_budget: int
    conditioning_projection_sha256: str
    conditioning_projection_excludes_reserved_words: bool
    conditioning_projection_excludes_decisions_and_outcome: bool
    conditioning_projection_excludes_word_binding_parent_digests: bool
    attempt_masses: Tuple[CounterKeyedInitialTiltRejectionAttemptMass, ...]
    attempt_mass_sha256s: Tuple[str, ...]
    configuration_masses: Tuple[CounterKeyedInitialTiltRejectionConfigurationMass, ...]
    configuration_mass_sha256s: Tuple[str, ...]
    attempt_to_configuration_ordinal: Tuple[int, ...]
    unique_configuration_count: int
    fixed_batch_exhaustion_probability_numerator: int
    fixed_batch_exhaustion_probability_denominator: int
    fixed_batch_selection_probability_numerator: int
    fixed_batch_selection_probability_denominator: int
    augmented_configuration_ideal_tv_strict_upper_numerator: int
    augmented_configuration_ideal_tv_strict_upper_denominator: int
    augmented_configuration_ideal_tv_upper_is_strict: bool
    ideal_comparison_uses_separate_common_uniform_coupling: bool
    success_conditioned_ideal_tv_bound_claimed: bool
    augmented_law_normalization_numerator: int
    augmented_law_normalization_denominator: int
    grouped_selection_mass_numerator: int
    grouped_selection_mass_denominator: int
    selected_conditioned_configuration_law_defined: bool
    outcome: str
    selected_attempt_index: Optional[int]
    selected_configuration: Optional[TransformedConfiguration]
    selected_configuration_sha256: Optional[str]
    selected_configuration_ordinal: Optional[int]
    counterfactual_mass_of_realized_outcome_numerator: int
    counterfactual_mass_of_realized_outcome_denominator: int
    counterfactual_aggregate_mass_of_realized_configuration_numerator: Optional[int]
    counterfactual_aggregate_mass_of_realized_configuration_denominator: Optional[int]
    counterfactual_conditioned_mass_of_realized_configuration_numerator: Optional[int]
    counterfactual_conditioned_mass_of_realized_configuration_denominator: Optional[int]
    reported_counterfactual_masses_require_abstract_iid_premise: bool
    selected_configuration_structurally_valid_as_initial_state: bool
    bounded_exhaustion_is_valid_no_state_outcome: bool
    operational_failure_returned_as_exhaustion: bool
    actual_outcome_is_counterfactual_draw: bool
    deterministic_fixed_address_replay_only: bool
    initializer_output_admitted: bool
    initializer_admissible: bool
    lineage_attached: bool
    tag3_payload_attached: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-batch-law results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("finite-batch-law results are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("finite-batch-law result fields are incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-batch-law results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionFiniteBatchLawResult.__annotations__)


def _require_record_matches(
    actual: object,
    expected: object,
    fields: Tuple[str, ...],
    *,
    identity_fields: Tuple[str, ...],
    name: str,
) -> None:
    for field in fields:
        live = getattr(actual, field)
        target = getattr(expected, field)
        if field in identity_fields:
            if live is not target:
                raise ValueError("%s.%s identity differs" % (name, field))
        elif type(live) is not type(target) or live != target:
            raise ValueError("%s.%s differs" % (name, field))


def _fraction_from_row(
    row: object,
    numerator_name: str,
    denominator_name: str,
) -> Fraction:
    return Fraction(getattr(row, numerator_name), getattr(row, denominator_name))


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("result trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    for name in (
        "certificate_sha256",
        "parent_decision_result_sha256",
        "conditioning_projection_sha256",
        "result_sha256",
    ):
        _require_sha256(values[name], name="result.%s" % name)
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    parent = _preflight_decision_result(
        values["parent_decision_result"], certificate=certificate
    )
    if values["parent_decision_result_sha256"] != parent.result_sha256:
        raise ValueError("result CP37 parent digest differs")
    expected_scalars = {
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": parent.attempt_budget,
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("result.%s differs from CP37" % name)
    attempt_masses = _exact_tuple(
        values["attempt_masses"],
        name="result.attempt_masses",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    attempt_digests = _exact_tuple(
        values["attempt_mass_sha256s"],
        name="result.attempt_mass_sha256s",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    configuration_masses = _exact_tuple(
        values["configuration_masses"],
        name="result.configuration_masses",
        maximum=certificate.attempt_budget,
    )
    if not configuration_masses:
        raise ValueError("result must retain at least one candidate configuration")
    configuration_digests = _exact_tuple(
        values["configuration_mass_sha256s"],
        name="result.configuration_mass_sha256s",
        maximum=certificate.attempt_budget,
        length=len(configuration_masses),
    )
    mapping = _exact_tuple(
        values["attempt_to_configuration_ordinal"],
        name="result.attempt_to_configuration_ordinal",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    unique_count = _exact_integer(
        values["unique_configuration_count"],
        name="result.unique_configuration_count",
        minimum=1,
        maximum=certificate.attempt_budget,
    )
    if unique_count != len(configuration_masses):
        raise ValueError("result unique-configuration count differs")
    checked_mapping = tuple(
        _exact_integer(
            ordinal,
            name="result.attempt_to_configuration_ordinal[%d]" % position,
            maximum=unique_count - 1,
        )
        for position, ordinal in enumerate(mapping)
    )
    if set(checked_mapping) != set(range(unique_count)):
        raise ValueError("result configuration mapping is not surjective")

    _DEC_VALIDATE_RESULT_VALUES(
        {name: getattr(parent, name) for name in _DEC_RESULT_FIELDS()}
    )
    expected_law = _materialize_law(certificate, parent)
    if values["conditioning_projection_sha256"] != (
        expected_law.conditioning_projection_sha256
    ):
        raise ValueError("result word-free conditioning projection differs")
    for name in (
        "conditioning_projection_excludes_reserved_words",
        "conditioning_projection_excludes_decisions_and_outcome",
        "conditioning_projection_excludes_word_binding_parent_digests",
    ):
        _exact_bool(values[name], True, name="result.%s" % name)
    if checked_mapping != expected_law.attempt_to_configuration_ordinal:
        raise ValueError("result attempt-to-configuration mapping differs")
    if len(attempt_masses) != len(expected_law.attempt_masses):
        raise ValueError("result attempt-mass count differs")
    for position, (row, expected) in enumerate(
        zip(attempt_masses, expected_law.attempt_masses)
    ):
        if type(row) is not CounterKeyedInitialTiltRejectionAttemptMass:
            raise TypeError("result attempt mass has the wrong exact type")
        _validate_attempt_mass_values(
            {name: getattr(row, name) for name in _attempt_mass_fields()},
            trusted_certificate=certificate,
        )
        _require_record_matches(
            row,
            expected,
            _attempt_mass_fields(),
            identity_fields=(
                "certificate",
                "threshold",
                "preparation_attempt",
                "configuration",
            ),
            name="result.attempt_masses[%d]" % position,
        )
        _require_sha256(
            attempt_digests[position],
            name="result.attempt_mass_sha256s[%d]" % position,
        )
        if attempt_digests[position] != row.mass_sha256:
            raise ValueError("result attempt-mass digest sequence differs")
    if len(configuration_masses) != len(expected_law.configuration_masses):
        raise ValueError("result configuration-mass count differs")
    for position, (row, expected) in enumerate(
        zip(configuration_masses, expected_law.configuration_masses)
    ):
        if type(row) is not CounterKeyedInitialTiltRejectionConfigurationMass:
            raise TypeError("result configuration mass has the wrong exact type")
        _validate_configuration_mass_values(
            {name: getattr(row, name) for name in _configuration_mass_fields()},
            trusted_certificate=certificate,
        )
        _require_record_matches(
            row,
            expected,
            _configuration_mass_fields(),
            identity_fields=("certificate", "configuration"),
            name="result.configuration_masses[%d]" % position,
        )
        _require_sha256(
            configuration_digests[position],
            name="result.configuration_mass_sha256s[%d]" % position,
        )
        if configuration_digests[position] != row.mass_sha256:
            raise ValueError("result configuration-mass digest sequence differs")

    exhaustion = _fraction_parts(
        values["fixed_batch_exhaustion_probability_numerator"],
        values["fixed_batch_exhaustion_probability_denominator"],
        name="result.fixed_batch_exhaustion_probability",
    )
    selection = _fraction_parts(
        values["fixed_batch_selection_probability_numerator"],
        values["fixed_batch_selection_probability_denominator"],
        name="result.fixed_batch_selection_probability",
    )
    normalization = _fraction_parts(
        values["augmented_law_normalization_numerator"],
        values["augmented_law_normalization_denominator"],
        name="result.augmented_law_normalization",
    )
    grouped = _fraction_parts(
        values["grouped_selection_mass_numerator"],
        values["grouped_selection_mass_denominator"],
        name="result.grouped_selection_mass",
    )
    if exhaustion != expected_law.exhaustion_probability:
        raise ValueError("result exhaustion probability differs")
    if selection != expected_law.selection_probability:
        raise ValueError("result selection probability differs")
    if normalization != 1 or exhaustion + selection != 1:
        raise ValueError("result augmented law does not normalize")
    if grouped != selection:
        raise ValueError("result grouped selection mass differs")
    ideal_tv_upper = _fraction_parts(
        values["augmented_configuration_ideal_tv_strict_upper_numerator"],
        values["augmented_configuration_ideal_tv_strict_upper_denominator"],
        name="result.augmented_configuration_ideal_tv_strict_upper",
    )
    if ideal_tv_upper != Fraction(certificate.attempt_budget, _D):
        raise ValueError("result augmented ideal-TV upper bound differs")
    _exact_bool(
        values["augmented_configuration_ideal_tv_upper_is_strict"],
        True,
        name="result.augmented_configuration_ideal_tv_upper_is_strict",
    )
    _exact_bool(
        values["ideal_comparison_uses_separate_common_uniform_coupling"],
        True,
        name="result.ideal_comparison_uses_separate_common_uniform_coupling",
    )
    _exact_bool(
        values["success_conditioned_ideal_tv_bound_claimed"],
        False,
        name="result.success_conditioned_ideal_tv_bound_claimed",
    )
    conditioned_defined = values["selected_conditioned_configuration_law_defined"]
    if type(conditioned_defined) is not bool:
        raise TypeError("result conditioned-law flag must be an exact Boolean")
    if conditioned_defined is not (selection > 0):
        raise ValueError("result conditioned-law definition flag differs")

    outcome = values["outcome"]
    if type(outcome) is not str or (
        outcome not in INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES
    ):
        raise ValueError("result outcome is unknown")
    if outcome != parent.outcome:
        raise ValueError("result outcome differs from CP37")
    realized = _fraction_parts(
        values["counterfactual_mass_of_realized_outcome_numerator"],
        values["counterfactual_mass_of_realized_outcome_denominator"],
        name="result.counterfactual_mass_of_realized_outcome",
    )
    parent_realized = Fraction(
        parent.conditional_outcome_probability_numerator,
        parent.conditional_outcome_probability_denominator,
    )
    if realized != parent_realized:
        raise ValueError("result realized outcome mass differs from CP37")
    if outcome == "selected":
        selected_index = _exact_integer(
            values["selected_attempt_index"],
            name="result.selected_attempt_index",
            maximum=certificate.attempt_budget - 1,
        )
        if selected_index != parent.selected_attempt_index:
            raise ValueError("result selected attempt differs")
        selected_configuration = values["selected_configuration"]
        if selected_configuration is not parent.selected_configuration:
            raise ValueError("result selected configuration identity differs")
        selected_digest = _configuration_digest(
            selected_configuration, name="result.selected_configuration"
        )
        _require_sha256(
            values["selected_configuration_sha256"],
            name="result.selected_configuration_sha256",
        )
        if values["selected_configuration_sha256"] != selected_digest or (
            selected_digest != parent.selected_configuration_sha256
        ):
            raise ValueError("result selected configuration digest differs")
        ordinal = _exact_integer(
            values["selected_configuration_ordinal"],
            name="result.selected_configuration_ordinal",
            maximum=unique_count - 1,
        )
        if ordinal != checked_mapping[selected_index]:
            raise ValueError("result selected configuration ordinal differs")
        attempt_mass = _fraction_from_row(
            attempt_masses[selected_index],
            "fixed_batch_first_selection_probability_numerator",
            "fixed_batch_first_selection_probability_denominator",
        )
        if realized != attempt_mass:
            raise ValueError("result selected attempt mass differs")
        aggregate = _fraction_parts(
            values["counterfactual_aggregate_mass_of_realized_configuration_numerator"],
            values[
                "counterfactual_aggregate_mass_of_realized_configuration_denominator"
            ],
            name="result.counterfactual_aggregate_mass_of_realized_configuration",
        )
        conditioned = _fraction_parts(
            values[
                "counterfactual_conditioned_mass_of_realized_" "configuration_numerator"
            ],
            values[
                "counterfactual_conditioned_mass_of_realized_"
                "configuration_denominator"
            ],
            name=(
                "result.counterfactual_conditioned_mass_of_realized_" "configuration"
            ),
        )
        expected_row = configuration_masses[ordinal]
        if aggregate != _fraction_from_row(
            expected_row,
            "fixed_batch_selection_probability_numerator",
            "fixed_batch_selection_probability_denominator",
        ):
            raise ValueError("result selected configuration aggregate differs")
        if conditioned != _fraction_from_row(
            expected_row,
            "selected_conditioned_probability_numerator",
            "selected_conditioned_probability_denominator",
        ):
            raise ValueError("result selected configuration conditioned mass differs")
        if _configuration_key(
            selected_configuration, name="result.selected_configuration"
        ) != _configuration_key(
            expected_row.configuration,
            name="result.selected_configuration_representative",
        ):
            raise ValueError("selected configuration row has another structure")
        expected_flags = {
            "selected_configuration_structurally_valid_as_initial_state": True,
            "bounded_exhaustion_is_valid_no_state_outcome": False,
        }
    else:
        for name in (
            "selected_attempt_index",
            "selected_configuration",
            "selected_configuration_sha256",
            "selected_configuration_ordinal",
            "counterfactual_aggregate_mass_of_realized_configuration_numerator",
            "counterfactual_aggregate_mass_of_realized_configuration_denominator",
            ("counterfactual_conditioned_mass_of_realized_" "configuration_numerator"),
            (
                "counterfactual_conditioned_mass_of_realized_"
                "configuration_denominator"
            ),
        ):
            if values[name] is not None:
                raise ValueError("exhausted result %s must be absent" % name)
        if realized != exhaustion:
            raise ValueError("result exhaustion mass differs from realized mass")
        expected_flags = {
            "selected_configuration_structurally_valid_as_initial_state": False,
            "bounded_exhaustion_is_valid_no_state_outcome": True,
        }
    for name, expected in expected_flags.items():
        _exact_bool(values[name], expected, name="result.%s" % name)
    for name, expected in (
        ("reported_counterfactual_masses_require_abstract_iid_premise", True),
        ("operational_failure_returned_as_exhaustion", False),
        ("actual_outcome_is_counterfactual_draw", False),
        ("deterministic_fixed_address_replay_only", True),
        ("initializer_output_admitted", False),
        ("initializer_admissible", False),
        ("lineage_attached", False),
        ("tag3_payload_attached", False),
    ):
        _exact_bool(values[name], expected, name="result.%s" % name)
    if values["result_sha256"] != _semantic_digest(_result_payload(values)):
        raise ValueError("finite-batch-law result digest differs")


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
    parent: _DEC_RESULT_TYPE,
    *,
    law: Optional[_LawData] = None,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
    if law is None:
        law = _materialize_law(certificate, parent)
    elif type(law) is not _LawData:
        raise TypeError("law must be the exact internal finite-batch-law data")
    if parent.outcome == "selected":
        selected_index = parent.selected_attempt_index
        ordinal = law.attempt_to_configuration_ordinal[selected_index]
        configuration_row = law.configuration_masses[ordinal]
        aggregate = Fraction(
            configuration_row.fixed_batch_selection_probability_numerator,
            configuration_row.fixed_batch_selection_probability_denominator,
        )
        conditioned = Fraction(
            configuration_row.selected_conditioned_probability_numerator,
            configuration_row.selected_conditioned_probability_denominator,
        )
        valid_initial_state = True
        exhausted = False
    else:
        selected_index = None
        ordinal = None
        aggregate = None
        conditioned = None
        valid_initial_state = False
        exhausted = True
    realized = Fraction(
        parent.conditional_outcome_probability_numerator,
        parent.conditional_outcome_probability_denominator,
    )
    ideal_tv_upper = Fraction(parent.attempt_budget, _D)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "parent_decision_result": parent,
        "parent_decision_result_sha256": parent.result_sha256,
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": parent.attempt_budget,
        "conditioning_projection_sha256": law.conditioning_projection_sha256,
        "conditioning_projection_excludes_reserved_words": True,
        "conditioning_projection_excludes_decisions_and_outcome": True,
        "conditioning_projection_excludes_word_binding_parent_digests": True,
        "attempt_masses": law.attempt_masses,
        "attempt_mass_sha256s": tuple(row.mass_sha256 for row in law.attempt_masses),
        "configuration_masses": law.configuration_masses,
        "configuration_mass_sha256s": tuple(
            row.mass_sha256 for row in law.configuration_masses
        ),
        "attempt_to_configuration_ordinal": law.attempt_to_configuration_ordinal,
        "unique_configuration_count": len(law.configuration_masses),
        "fixed_batch_exhaustion_probability_numerator": (
            law.exhaustion_probability.numerator
        ),
        "fixed_batch_exhaustion_probability_denominator": (
            law.exhaustion_probability.denominator
        ),
        "fixed_batch_selection_probability_numerator": (
            law.selection_probability.numerator
        ),
        "fixed_batch_selection_probability_denominator": (
            law.selection_probability.denominator
        ),
        "augmented_configuration_ideal_tv_strict_upper_numerator": (
            ideal_tv_upper.numerator
        ),
        "augmented_configuration_ideal_tv_strict_upper_denominator": (
            ideal_tv_upper.denominator
        ),
        "augmented_configuration_ideal_tv_upper_is_strict": True,
        "ideal_comparison_uses_separate_common_uniform_coupling": True,
        "success_conditioned_ideal_tv_bound_claimed": False,
        "augmented_law_normalization_numerator": 1,
        "augmented_law_normalization_denominator": 1,
        "grouped_selection_mass_numerator": law.selection_probability.numerator,
        "grouped_selection_mass_denominator": law.selection_probability.denominator,
        "selected_conditioned_configuration_law_defined": (
            law.selection_probability > 0
        ),
        "outcome": parent.outcome,
        "selected_attempt_index": selected_index,
        "selected_configuration": parent.selected_configuration,
        "selected_configuration_sha256": parent.selected_configuration_sha256,
        "selected_configuration_ordinal": ordinal,
        "counterfactual_mass_of_realized_outcome_numerator": realized.numerator,
        "counterfactual_mass_of_realized_outcome_denominator": realized.denominator,
        "counterfactual_aggregate_mass_of_realized_configuration_numerator": (
            None if aggregate is None else aggregate.numerator
        ),
        "counterfactual_aggregate_mass_of_realized_configuration_denominator": (
            None if aggregate is None else aggregate.denominator
        ),
        "counterfactual_conditioned_mass_of_realized_"
        "configuration_numerator": (
            None if conditioned is None else conditioned.numerator
        ),
        "counterfactual_conditioned_mass_of_realized_"
        "configuration_denominator": (
            None if conditioned is None else conditioned.denominator
        ),
        "reported_counterfactual_masses_require_abstract_iid_premise": True,
        "selected_configuration_structurally_valid_as_initial_state": (
            valid_initial_state
        ),
        "bounded_exhaustion_is_valid_no_state_outcome": exhausted,
        "operational_failure_returned_as_exhaustion": False,
        "actual_outcome_is_counterfactual_draw": False,
        "deterministic_fixed_address_replay_only": True,
        "initializer_output_admitted": False,
        "initializer_admissible": False,
        "lineage_attached": False,
        "tag3_payload_attached": False,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_result_payload(values))
    return CounterKeyedInitialTiltRejectionFiniteBatchLawResult(
        _construction_token=_RESULT_TOKEN,
        **values,
    )


def _preflight_result_record(
    result: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
    if type(result) is not CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
        raise TypeError("result has the wrong exact finite-batch-law type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to another finite-batch-law certificate")
    _require_text(result.schema_version, _SCHEMA_VERSION, name="result.schema")
    for name in (
        "certificate_sha256",
        "parent_decision_result_sha256",
        "conditioning_projection_sha256",
        "result_sha256",
    ):
        _require_sha256(getattr(result, name), name="result.%s" % name)
    if result.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    _exact_integer(result.run_id, name="result.run_id")
    _exact_integer(
        result.initialization_index,
        name="result.initialization_index",
    )
    attempt_budget = _exact_integer(
        result.attempt_budget,
        name="result.attempt_budget",
        minimum=1,
        maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS,
    )
    if attempt_budget != certificate.attempt_budget:
        raise ValueError("result attempt budget differs")
    attempt_masses = _exact_tuple(
        result.attempt_masses,
        name="result.attempt_masses",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    for position, row in enumerate(attempt_masses):
        if type(row) is not CounterKeyedInitialTiltRejectionAttemptMass:
            raise TypeError("result attempt mass has the wrong exact type")
        _require_sha256(
            row.mass_sha256,
            name="result.attempt_masses[%d].mass_sha256" % position,
        )
        _configuration_key(
            row.configuration,
            name="result.attempt_masses[%d].configuration" % position,
        )
    attempt_mass_sha256s = _exact_tuple(
        result.attempt_mass_sha256s,
        name="result.attempt_mass_sha256s",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    for position, digest in enumerate(attempt_mass_sha256s):
        _require_sha256(
            digest,
            name="result.attempt_mass_sha256s[%d]" % position,
        )
        if digest != attempt_masses[position].mass_sha256:
            raise ValueError("result attempt-mass digest sequence differs")
    configuration_masses = _exact_tuple(
        result.configuration_masses,
        name="result.configuration_masses",
        maximum=certificate.attempt_budget,
    )
    if not configuration_masses:
        raise ValueError("result has no configuration-mass rows")
    for position, row in enumerate(configuration_masses):
        if type(row) is not CounterKeyedInitialTiltRejectionConfigurationMass:
            raise TypeError("result configuration mass has the wrong exact type")
        _require_sha256(
            row.mass_sha256,
            name="result.configuration_masses[%d].mass_sha256" % position,
        )
        _exact_tuple(
            row.attempt_indices,
            name="result.configuration_masses[%d].attempt_indices" % position,
            maximum=certificate.attempt_budget,
        )
        configuration = _exact_tuple(
            row.configuration,
            name="result.configuration_masses[%d].configuration" % position,
            maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS,
        )
        _configuration_key(
            configuration,
            name="result.configuration_masses[%d].configuration" % position,
        )
    configuration_mass_sha256s = _exact_tuple(
        result.configuration_mass_sha256s,
        name="result.configuration_mass_sha256s",
        maximum=certificate.attempt_budget,
        length=len(configuration_masses),
    )
    for position, digest in enumerate(configuration_mass_sha256s):
        _require_sha256(
            digest,
            name="result.configuration_mass_sha256s[%d]" % position,
        )
        if digest != configuration_masses[position].mass_sha256:
            raise ValueError("result configuration-mass digest sequence differs")
    mapping = _exact_tuple(
        result.attempt_to_configuration_ordinal,
        name="result.attempt_to_configuration_ordinal",
        maximum=certificate.attempt_budget,
        length=certificate.attempt_budget,
    )
    unique_count = _exact_integer(
        result.unique_configuration_count,
        name="result.unique_configuration_count",
        minimum=1,
        maximum=certificate.attempt_budget,
    )
    if unique_count != len(configuration_masses):
        raise ValueError("result unique-configuration count differs")
    for position, ordinal in enumerate(mapping):
        _exact_integer(
            ordinal,
            name="result.attempt_to_configuration_ordinal[%d]" % position,
            maximum=unique_count - 1,
        )
    for numerator_name, denominator_name in (
        (
            "fixed_batch_exhaustion_probability_numerator",
            "fixed_batch_exhaustion_probability_denominator",
        ),
        (
            "fixed_batch_selection_probability_numerator",
            "fixed_batch_selection_probability_denominator",
        ),
        (
            "augmented_configuration_ideal_tv_strict_upper_numerator",
            "augmented_configuration_ideal_tv_strict_upper_denominator",
        ),
        (
            "augmented_law_normalization_numerator",
            "augmented_law_normalization_denominator",
        ),
        ("grouped_selection_mass_numerator", "grouped_selection_mass_denominator"),
        (
            "counterfactual_mass_of_realized_outcome_numerator",
            "counterfactual_mass_of_realized_outcome_denominator",
        ),
    ):
        _fraction_parts(
            getattr(result, numerator_name),
            getattr(result, denominator_name),
            name="result.%s" % numerator_name.removesuffix("_numerator"),
        )
    if type(result.outcome) is not str or (
        result.outcome not in INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES
    ):
        raise ValueError("result outcome is unknown")
    for name in (
        "conditioning_projection_excludes_reserved_words",
        "conditioning_projection_excludes_decisions_and_outcome",
        "conditioning_projection_excludes_word_binding_parent_digests",
        "augmented_configuration_ideal_tv_upper_is_strict",
        "ideal_comparison_uses_separate_common_uniform_coupling",
        "success_conditioned_ideal_tv_bound_claimed",
        "selected_conditioned_configuration_law_defined",
        "reported_counterfactual_masses_require_abstract_iid_premise",
        "selected_configuration_structurally_valid_as_initial_state",
        "bounded_exhaustion_is_valid_no_state_outcome",
        "operational_failure_returned_as_exhaustion",
        "actual_outcome_is_counterfactual_draw",
        "deterministic_fixed_address_replay_only",
        "initializer_output_admitted",
        "initializer_admissible",
        "lineage_attached",
        "tag3_payload_attached",
    ):
        if type(getattr(result, name)) is not bool:
            raise TypeError("result.%s must be an exact Boolean" % name)
    if result.outcome == "selected":
        _exact_integer(
            result.selected_attempt_index,
            name="result.selected_attempt_index",
            maximum=certificate.attempt_budget - 1,
        )
        selected_configuration = _exact_tuple(
            result.selected_configuration,
            name="result.selected_configuration",
            maximum=INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS,
        )
        _configuration_key(
            selected_configuration,
            name="result.selected_configuration",
        )
        _require_sha256(
            result.selected_configuration_sha256,
            name="result.selected_configuration_sha256",
        )
        _exact_integer(
            result.selected_configuration_ordinal,
            name="result.selected_configuration_ordinal",
            maximum=certificate.attempt_budget - 1,
        )
        for numerator_name, denominator_name in (
            (
                "counterfactual_aggregate_mass_of_realized_configuration_numerator",
                "counterfactual_aggregate_mass_of_realized_configuration_denominator",
            ),
            (
                (
                    "counterfactual_conditioned_mass_of_realized_"
                    "configuration_numerator"
                ),
                (
                    "counterfactual_conditioned_mass_of_realized_"
                    "configuration_denominator"
                ),
            ),
        ):
            _fraction_parts(
                getattr(result, numerator_name),
                getattr(result, denominator_name),
                name="result.%s" % numerator_name.removesuffix("_numerator"),
            )
    else:
        for name in (
            "selected_attempt_index",
            "selected_configuration",
            "selected_configuration_sha256",
            "selected_configuration_ordinal",
            "counterfactual_aggregate_mass_of_realized_configuration_numerator",
            "counterfactual_aggregate_mass_of_realized_configuration_denominator",
            ("counterfactual_conditioned_mass_of_realized_" "configuration_numerator"),
            (
                "counterfactual_conditioned_mass_of_realized_"
                "configuration_denominator"
            ),
        ):
            if getattr(result, name) is not None:
                raise ValueError("exhausted result %s must be absent" % name)
    _preflight_decision_result(
        result.parent_decision_result,
        certificate=certificate,
    )
    return result


def _result_tree_snapshot(
    result: CounterKeyedInitialTiltRejectionFiniteBatchLawResult,
) -> Tuple[object, ...]:
    return (
        _record_snapshot(result, _result_fields()),
        tuple(
            _record_snapshot(row, _attempt_mass_fields())
            for row in result.attempt_masses
        ),
        tuple(
            _record_snapshot(row, _configuration_mass_fields())
            for row in result.configuration_masses
        ),
        _record_snapshot(result.parent_decision_result, _DEC_RESULT_FIELDS()),
    )


def _require_result_tree_unchanged(
    result: CounterKeyedInitialTiltRejectionFiniteBatchLawResult,
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
) -> None:
    _preflight_result_record(result, certificate=certificate)
    if type(snapshot) is not tuple or len(snapshot) != 4:
        raise TypeError("finite-batch-law result-tree snapshot is malformed")
    result_before, attempt_befores, configuration_befores, parent_before = snapshot
    _require_record_unchanged(
        result,
        _result_fields(),
        result_before,
        name="finite-batch-law result",
    )
    if len(attempt_befores) != len(result.attempt_masses):
        raise ValueError("finite-batch-law attempt-mass count changed")
    for position, (row, before) in enumerate(
        zip(result.attempt_masses, attempt_befores)
    ):
        _require_record_unchanged(
            row,
            _attempt_mass_fields(),
            before,
            name="finite-batch-law attempt mass %d" % position,
        )
    if len(configuration_befores) != len(result.configuration_masses):
        raise ValueError("finite-batch-law configuration-mass count changed")
    for position, (row, before) in enumerate(
        zip(result.configuration_masses, configuration_befores)
    ):
        _require_record_unchanged(
            row,
            _configuration_mass_fields(),
            before,
            name="finite-batch-law configuration mass %d" % position,
        )
    _require_record_unchanged(
        result.parent_decision_result,
        _DEC_RESULT_FIELDS(),
        parent_before,
        name="finite-batch-law CP37 parent",
    )


class CounterKeyedInitialTiltRejectionFiniteBatchLawOwner:
    """Immutable owner of one CP37-bound finite-batch-law operation."""

    __slots__ = (
        "_decision_owner",
        "_decision_owner_identity",
        "_decision_certificate",
        "_decision_certificate_identity",
        "_word_law_hypothesis",
        "_word_law_hypothesis_identity",
        "_law_policy",
        "_law_policy_identity",
        "_law_role_sha256",
        "_law_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_decision_certificate_snapshot",
        "_decision_certificate_snapshot_identity",
        "_hypothesis_snapshot",
        "_hypothesis_snapshot_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_parent_owner_snapshot",
        "_parent_require_owner_snapshot",
        "_parent_live_certificate",
        "_parent_decide",
        "_parent_validate_result",
        "_parent_preflight",
        "_law_builder",
        "_result_builder",
        "_result_validator",
        "_result_preflight",
        "_result_tree_snapshotter",
        "_result_tree_unchanged_checker",
        "_parent_tree_snapshotter",
        "_parent_tree_unchanged_checker",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-batch-law owners cannot be subclassed")

    def __init__(
        self,
        decision_owner: _DEC_OWNER_TYPE,
        word_law_hypothesis: FixedBatchIidUint64DecisionWordHypothesis,
        law_policy: str,
        law_role_sha256: str,
        certificate: CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("finite-batch-law owners require certification")
        if type(decision_owner) is not _DEC_OWNER_TYPE:
            raise TypeError("decision_owner has the wrong exact CP37 type")
        hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
            word_law_hypothesis
        )
        policy = _require_text(law_policy, _POLICY, name="law_policy")
        role = _require_sha256(law_role_sha256, name="law_role_sha256")
        checked = _validate_certificate(certificate)
        parent = _DEC_CERTIFICATE_PROPERTY.__get__(decision_owner, _DEC_OWNER_TYPE)
        if checked.decision_certificate is not parent:
            raise ValueError("owner CP37 certificate identity differs")
        if checked.word_law_hypothesis is not hypothesis:
            raise ValueError("owner word-law hypothesis identity differs")
        if checked.decision_owner_runtime_identity != id(decision_owner):
            raise ValueError("certificate CP37 owner runtime identity differs")
        parent_snapshot = _decision_certificate_snapshot(parent)
        hypothesis_snapshot = _record_snapshot(hypothesis, _hypothesis_fields())
        certificate_snapshot = _record_snapshot(checked, _certificate_fields())
        bindings = (
            ("_decision_owner", decision_owner),
            ("_decision_owner_identity", decision_owner),
            ("_decision_certificate", parent),
            ("_decision_certificate_identity", parent),
            ("_word_law_hypothesis", hypothesis),
            ("_word_law_hypothesis_identity", hypothesis),
            ("_law_policy", policy),
            ("_law_policy_identity", policy),
            ("_law_role_sha256", role),
            ("_law_role_sha256_identity", role),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_decision_certificate_snapshot", parent_snapshot),
            ("_decision_certificate_snapshot_identity", parent_snapshot),
            ("_hypothesis_snapshot", hypothesis_snapshot),
            ("_hypothesis_snapshot_identity", hypothesis_snapshot),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_parent_owner_snapshot", _DEC_OWNER_SNAPSHOT),
            ("_parent_require_owner_snapshot", _DEC_REQUIRE_OWNER_SNAPSHOT),
            ("_parent_live_certificate", _DEC_LIVE_CERTIFICATE),
            ("_parent_decide", _DEC_DECIDE),
            ("_parent_validate_result", _DEC_VALIDATE_RESULT),
            ("_parent_preflight", _preflight_decision_result),
            ("_law_builder", _materialize_law),
            ("_result_builder", _make_result),
            ("_result_validator", _validate_result_values),
            ("_result_preflight", _preflight_result_record),
            ("_result_tree_snapshotter", _result_tree_snapshot),
            ("_result_tree_unchanged_checker", _require_result_tree_unchanged),
            ("_parent_tree_snapshotter", _decision_result_tree_snapshot),
            (
                "_parent_tree_unchanged_checker",
                _require_decision_result_tree_unchanged,
            ),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("finite-batch-law owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("finite-batch-law owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-batch-law owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
        return self._certificate

    @property
    def decision_owner(self) -> _DEC_OWNER_TYPE:
        return self._decision_owner

    @property
    def word_law_hypothesis(self) -> FixedBatchIidUint64DecisionWordHypothesis:
        return self._word_law_hypothesis

    def _owner_snapshot(self) -> Tuple[object, ...]:
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("finite-batch-law owner seal differs")
        current = (
            self._decision_owner,
            self._decision_certificate,
            self._word_law_hypothesis,
            self._law_policy,
            self._law_role_sha256,
            self._certificate,
            self._decision_certificate_snapshot,
            self._hypothesis_snapshot,
            self._certificate_snapshot,
        )
        frozen = (
            self._decision_owner_identity,
            self._decision_certificate_identity,
            self._word_law_hypothesis_identity,
            self._law_policy_identity,
            self._law_role_sha256_identity,
            self._certificate_identity,
            self._decision_certificate_snapshot_identity,
            self._hypothesis_snapshot_identity,
            self._certificate_snapshot_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("finite-batch-law owner identity changed")
        callbacks = (
            (self._parent_owner_snapshot, _DEC_OWNER_SNAPSHOT),
            (self._parent_require_owner_snapshot, _DEC_REQUIRE_OWNER_SNAPSHOT),
            (self._parent_live_certificate, _DEC_LIVE_CERTIFICATE),
            (self._parent_decide, _DEC_DECIDE),
            (self._parent_validate_result, _DEC_VALIDATE_RESULT),
            (self._parent_preflight, _preflight_decision_result),
            (self._law_builder, _materialize_law),
            (self._result_builder, _make_result),
            (self._result_validator, _validate_result_values),
            (self._result_preflight, _preflight_result_record),
            (self._result_tree_snapshotter, _result_tree_snapshot),
            (self._result_tree_unchanged_checker, _require_result_tree_unchanged),
            (self._parent_tree_snapshotter, _decision_result_tree_snapshot),
            (
                self._parent_tree_unchanged_checker,
                _require_decision_result_tree_unchanged,
            ),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("finite-batch-law cached callback changed")
        return current

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 9:
            raise TypeError("finite-batch-law owner snapshot is malformed")
        current = self._owner_snapshot()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError(
                "finite-batch-law owner changed during operation"
            )

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
        self._require_owner_snapshot(owner_snapshot)
        _require_parent_surfaces()
        parent_snapshot = self._parent_owner_snapshot(self._decision_owner)
        live_parent = self._parent_live_certificate(
            self._decision_owner,
            parent_snapshot,
        )
        self._parent_require_owner_snapshot(self._decision_owner, parent_snapshot)
        if live_parent is not self._decision_certificate:
            raise ValueError("CP37 live binding substituted its certificate")
        _require_record_unchanged(
            self._decision_certificate,
            _DEC_CERTIFICATE_FIELDS(),
            self._decision_certificate_snapshot,
            name="CP37 certificate",
        )
        checked_hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
            self._word_law_hypothesis
        )
        if checked_hypothesis is not self._word_law_hypothesis:
            raise ValueError("word-law validation substituted its hypothesis")
        _require_record_unchanged(
            self._word_law_hypothesis,
            _hypothesis_fields(),
            self._hypothesis_snapshot,
            name="word-law hypothesis",
        )
        certificate = _validate_certificate(self._certificate)
        if certificate.decision_owner_runtime_identity != id(self._decision_owner):
            raise ValueError("certificate CP37 owner runtime identity differs")
        _require_record_unchanged(
            certificate,
            _certificate_fields(),
            self._certificate_snapshot,
            name="finite-batch-law certificate",
        )
        self._require_owner_snapshot(owner_snapshot)
        return certificate

    def resolve(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
        """Call CP37 once and attach the exact word-free finite-batch law."""

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index,
            name="initialization_index",
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        parent_owner_snapshot = self._parent_owner_snapshot(self._decision_owner)
        parent = self._parent_decide(
            self._decision_owner,
            checked_run,
            checked_initialization,
        )
        self._parent_require_owner_snapshot(
            self._decision_owner,
            parent_owner_snapshot,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        parent = self._parent_preflight(parent, certificate=certificate)
        parent_tree = self._parent_tree_snapshotter(parent)
        checked_parent = self._parent_validate_result(
            self._decision_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP37 validation substituted its result")
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        law = self._law_builder(certificate, parent)
        result = self._result_builder(certificate, parent, law=law)
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
        """Replay validation without calling CP37 decide or CP36 prepare."""

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index,
            name="initialization_index",
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        if type(result) is not CounterKeyedInitialTiltRejectionFiniteBatchLawResult:
            raise TypeError("result has the wrong exact finite-batch-law type")
        shallow_run = _exact_integer(result.run_id, name="result.run_id")
        shallow_initialization = _exact_integer(
            result.initialization_index,
            name="result.initialization_index",
        )
        if shallow_run != checked_run or shallow_initialization != (
            checked_initialization
        ):
            raise ValueError("result request coordinates differ")
        checked_result = self._result_preflight(result, certificate=certificate)
        result_tree = self._result_tree_snapshotter(checked_result)
        parent = checked_result.parent_decision_result
        parent_tree = self._parent_tree_snapshotter(parent)
        checked_parent = self._parent_validate_result(
            self._decision_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP37 validation substituted its result")
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        self._result_validator(
            {name: getattr(checked_result, name) for name in _result_fields()},
            trusted_certificate=certificate,
        )
        law = self._law_builder(certificate, parent)
        expected = self._result_builder(certificate, parent, law=law)
        if checked_result.result_sha256 != expected.result_sha256:
            raise ValueError("finite-batch-law replay digest differs")
        if checked_result.certificate is not expected.certificate or (
            checked_result.parent_decision_result is not expected.parent_decision_result
        ):
            raise ValueError("finite-batch-law replay ancestry identity differs")
        if checked_result.selected_configuration is not expected.selected_configuration:
            raise ValueError("finite-batch-law selected configuration identity differs")
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate,
        )
        self._result_tree_unchanged_checker(
            checked_result,
            result_tree,
            certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return checked_result


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law(
    decision_owner: object,
    word_law_hypothesis: object,
    *,
    law_policy: object,
    law_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawOwner:
    """Certify the exact CP37-bound counterfactual finite-batch law layer."""

    if type(decision_owner) is not _DEC_OWNER_TYPE:
        raise TypeError("decision_owner has the wrong exact CP37 type")
    hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
        word_law_hypothesis
    )
    policy = _require_text(law_policy, _POLICY, name="law_policy")
    role = _require_sha256(law_role_sha256, name="law_role_sha256")
    _require_parent_surfaces()
    parent_snapshot = _DEC_OWNER_SNAPSHOT(decision_owner)
    parent = _DEC_LIVE_CERTIFICATE(decision_owner, parent_snapshot)
    _DEC_REQUIRE_OWNER_SNAPSHOT(decision_owner, parent_snapshot)
    if parent is not _DEC_CERTIFICATE_PROPERTY.__get__(
        decision_owner,
        _DEC_OWNER_TYPE,
    ):
        raise ValueError("CP37 live binding substituted its certificate")
    certificate = _make_certificate(decision_owner, hypothesis, role)
    _DEC_REQUIRE_OWNER_SNAPSHOT(decision_owner, parent_snapshot)
    owner = CounterKeyedInitialTiltRejectionFiniteBatchLawOwner(
        decision_owner,
        hypothesis,
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner_snapshot = owner._owner_snapshot()
    owner._live_certificate(owner_snapshot)
    owner._require_owner_snapshot(owner_snapshot)
    return owner


def require_matching_counter_keyed_initial_tilt_rejection_finite_batch_law(
    decision_owner: object,
    word_law_hypothesis: object,
    owner: object,
    *,
    law_policy: object,
    law_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawOwner:
    """Require exact CP37, hypothesis, policy, role, and live custody."""

    if type(decision_owner) is not _DEC_OWNER_TYPE:
        raise TypeError("decision_owner has the wrong exact CP37 type")
    hypothesis = validate_fixed_batch_iid_uint64_decision_word_hypothesis(
        word_law_hypothesis
    )
    if type(owner) is not CounterKeyedInitialTiltRejectionFiniteBatchLawOwner:
        raise TypeError("owner has the wrong exact finite-batch-law type")
    policy = _require_text(law_policy, _POLICY, name="law_policy")
    role = _require_sha256(law_role_sha256, name="law_role_sha256")
    snapshot = owner._owner_snapshot()
    certificate = owner._live_certificate(snapshot)
    if owner.decision_owner is not decision_owner:
        raise ValueError("owner uses another CP37 parent")
    if owner.word_law_hypothesis is not hypothesis:
        raise ValueError("owner uses another word-law hypothesis")
    if certificate.law_policy != policy:
        raise ValueError("owner uses another finite-batch-law policy")
    if certificate.law_role_sha256 != role:
        raise ValueError("owner uses another finite-batch-law role")
    if certificate.decision_owner_runtime_identity != id(decision_owner):
        raise ValueError("owner certificate uses another CP37 runtime identity")
    owner._require_owner_snapshot(snapshot)
    return owner


def validate_counter_keyed_initial_tilt_rejection_finite_batch_law_certificate(
    decision_owner: object,
    word_law_hypothesis: object,
    owner: object,
    *,
    law_policy: object,
    law_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate:
    """Return the reconstructed live checkpoint-thirty-eight certificate."""

    return require_matching_counter_keyed_initial_tilt_rejection_finite_batch_law(
        decision_owner,
        word_law_hypothesis,
        owner,
        law_policy=law_policy,
        law_role_sha256=law_role_sha256,
    ).certificate


__all__ = [
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_"
        "SCHEMA_VERSION"
    ),
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCOPE",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_AUGMENTED_IDEAL_TV_THEOREM",
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION",
    "FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION",
    "FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE",
    "FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE",
    "FixedBatchIidUint64DecisionWordHypothesis",
    "CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate",
    "CounterKeyedInitialTiltRejectionAttemptMass",
    "CounterKeyedInitialTiltRejectionConfigurationMass",
    "CounterKeyedInitialTiltRejectionFiniteBatchLawResult",
    "CounterKeyedInitialTiltRejectionFiniteBatchLawOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError",
    "declare_fixed_batch_iid_uint64_decision_word_hypothesis",
    "validate_fixed_batch_iid_uint64_decision_word_hypothesis",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law",
    "require_matching_counter_keyed_initial_tilt_rejection_finite_batch_law",
    "validate_counter_keyed_initial_tilt_rejection_finite_batch_law_certificate",
]
