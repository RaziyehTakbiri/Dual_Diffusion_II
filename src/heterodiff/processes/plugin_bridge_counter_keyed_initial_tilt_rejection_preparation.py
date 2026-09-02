"""Prepare a complete fixed budget of finite rejection proposals and scores.

This additive checkpoint joins checkpoint twenty-eight's finite reference
transform to checkpoint thirty's deterministic initial log-factor composer.
Checkpoint twenty-seven first materializes the entire rejection prefix.  Each
attempt contains the exact checkpoint-twenty-eight proposal layout followed by
one reserved, uninterpreted word.  The proposal is transformed and scored, but
the reserved word is never converted to a variate, compared, or used to choose
an attempt.  Consequently this module supplies preparation, not rejection
sampling, acceptance, admission, or an initialized state.

The only probabilistic statement is conditional and source-parametric.  If a
separate abstract family of iid uniform uint64 variables is indexed by the
distinct full logical word coordinates frozen here, the total deterministic
operational map into ``Success(preparation)`` or one distinguished
``Failure`` symbol has its corresponding finite pushforward kernel.  Its
success value is an abstract algorithmic batch (finite candidates, scores,
reserved words, and address labels), not the live CP27 transcript or CP36
result record.  This
failure augmentation is necessary because CP30 scoring is checked and can
fail.  It does not bound failure probability or define a successful-record
conditional law.  For an arbitrary source law ``nu`` on those words, data
processing gives
``TV(F#nu,F#U) <= TV(nu,U)``.  Combining this with a separately supplied source
approximation bound is only a conditional source-plus-algorithm triangle
ledger.  The live fixed-address Philox trace and output are deterministic
point masses; no live uniformity, independence, or randomness is certified.

Hashes and identities are process-local custody witnesses under a trusted,
unchanged runtime, not cryptographic authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import platform
import sys
from typing import Dict, Mapping, Tuple, get_args, get_origin, get_type_hints

try:
    from heterodiff.models import configuration_initial_tilt_composer_torch as _tilt
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_reference_initializer as _reference,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed rejection preparation requires the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJumpComposer,
)
from heterodiff.theory.configuration_reference import (
    TransformedConfiguration,
    TransformedEvent,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-preparation-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY = (
    "exact-checkpoint28-and-checkpoint30-owner-binding;"
    "exact-shared-reference-composer-and-process-ancestry;"
    "factory-frozen-canonical-residual-context-and-attempt-budget;"
    "checkpoint27-rejection-full-prefix-before-evaluation;"
    "checkpoint28-layout-plus-one-reserved-uninterpreted-decision-word;"
    "complete-raw-slot-transform-before-count-decode;"
    "checkpoint30-point-score-and-exact-q-minus-U-witness;"
    "distinct-full-logical-word-coordinate-custody;"
    "conditional-abstract-iid-uint64-pushforward-data-processing-ledger;"
    "no-acceptance-selection-admission-retry-or-fallback-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCOPE = (
    "bounded-fixed-budget-finite-reference-proposal-and-point-score-preparation;"
    "complete-tag7-prefix-and-reserved-uninterpreted-word-custody;"
    "counterfactual-distinct-coordinate-product-uniform-pushforward-only;"
    "live-fixed-address-trace-and-output-are-deterministic-point-masses;"
    "not-acceptance-predicate-decision-success-or-exhaustion;"
    "not-exponential-bernoulli-first-accepted-or-normalized-tilted-initializer;"
    "not-exact-Pi_N-continuous-gaussian-or-analytic-target;"
    "not-live-uniformity-independence-randomness-or-global-one-shot-use;"
    "not-rejection-sir-admission-lineage-tag3-path-drift-liveness-or-sampler;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCHEMA_VERSION = (
    "initial-tilt-rejection-distinct-coordinate-word-family-hypothesis-v1"
)
INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCOPE = (
    "fixed-manifest-fixed-attempt-budget-normalized-logical-coordinate-template;"
    "universal-over-exact-uint64-run-and-initialization-instantiations;"
    "abstract-iid-uniform-uint64-substitution-only;"
    "failure-augmented-total-map-success-preparation-disjoint-union-failure;"
    "no-failure-probability-or-success-conditional-law-claim;"
    "repeated-coordinate-denotes-the-same-variable-so-coordinates-must-be-distinct;"
    "not-a-law-for-live-counter-keyed-philox-words-or-outputs"
)
INITIAL_TILT_REJECTION_WORD_FAMILY_PREMISE = (
    "for-every-exact-uint64-(run_id,initialization_index)-instantiate-the-"
    "normalized-(zero,zero)-template-by-replacing-only-its-run-and-initialization-"
    "limbs;replace-each-resulting-distinct-full-logical-word-coordinate-by-one-"
    "separate-abstract-iid-variable-uniform-on-{0,...,2^64-1};finite-injective-"
    "coordinate-relabeling-preserves-the-product-uniform-pushforward-premise;"
    "apply-the-total-deterministic-operational-map-that-returns-either-a-"
    "successful-preparation-record-or-one-distinguished-failure-symbol;this-"
    "family-is-not-the-live-philox-trace"
)
INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM = "TV(F#nu,F#U)<=TV(nu,U)"
INITIAL_TILT_REJECTION_TRIANGLE_LEDGER = (
    "conditional-only;source-plus-algorithm-triangle-ledger;requires-a-separate-"
    "proved-bound-on-TV(nu,U);no-live-source-bound-is-supplied-here"
)
INITIAL_TILT_REJECTION_ABSTRACT_PUSHFORWARD_CODOMAIN = (
    "Success(abstract-algorithmic-batch-of-finite-candidates-scores-reserved-"
    "words-and-address-labels-without-CP27-Philox-transcript-live-digests-or-"
    "CP36-result-record)-disjoint-union-"
    "Failure(distinguished-operational-failure-symbol);no-failure-probability-"
    "or-success-conditioned-law-certified;live-CP36-result-is-not-F-output"
)
INITIAL_TILT_REJECTION_STRATEGY = "rejection"
INITIAL_TILT_REJECTION_STAGE_INDEX = 1
INITIAL_TILT_REJECTION_DOMAIN_TAG = 7
INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT = 1
INITIAL_TILT_REJECTION_MIN_ATTEMPTS = 1
INITIAL_TILT_REJECTION_MAX_ATTEMPTS = 64
INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS = 64
INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS = 65_536
INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION = 4_096
INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH = 16_384
INITIAL_TILT_REJECTION_MAX_INTEGER_BITS = 131_072

_SCHEMA_VERSION = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION
)
_PREPARATION_POLICY = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY
)
_PREPARATION_SCOPE = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCOPE
)

_ZERO_SHA256 = "0" * 64
_HYPOTHESIS_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_ATTEMPT_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_CP28_TYPE = _reference.CounterKeyedReferenceInitializerOwner
_CP28_CERT_TYPE = _reference.CounterKeyedReferenceInitializerCertificate
_CP28_RESULT_TYPE = _reference.CounterKeyedReferenceInitializerResult
_CP28_MANIFEST_TYPE = _reference.FiniteResolutionCappedPoissonManifest
_CP28_RAW_SLOT_TYPE = _reference.CounterKeyedReferenceInitializerRawSlot
_CP28_LIVE = _CP28_TYPE._require_live_binding
_CP28_VALIDATE_RESULT = _CP28_TYPE.validate_result
_CP28_CERTIFICATE_PROPERTY = _CP28_TYPE.certificate
_CP28_MANIFEST_PROPERTY = _CP28_TYPE.manifest
_CP28_PROTOCOL_PROPERTY = _CP28_TYPE.protocol_owner
_CP28_VALIDATE_CERTIFICATE = _reference._validate_certificate
_CP28_VALIDATE_MANIFEST = _reference._validate_manifest
_CP28_VALIDATE_RESULT_RECORD = _reference._validate_result_record
_CP28_VALIDATE_SLOT_RECORD = _reference._validate_slot_record
_CP28_MATERIALIZE_SLOT_FIELDS = _reference._materialize_slot_fields
_CP28_MAKE_SLOT = _reference._make_slot
_CP28_QUOTA_POSITION = _reference._quota_position
_CP28_EVENT_SHA256 = _reference._event_sha256
_CP28_CONFIGURATION_SHA256 = _reference._configuration_sha256

_CP27_TYPE = _reference._protocol.CounterKeyedInitializerProtocolOwner
_CP27_CERT_TYPE = _reference._protocol.CounterKeyedInitializerProtocolCertificate
_CP27_RESULT_TYPE = _reference._protocol.CounterKeyedInitializerProtocolResult
_CP27_LIVE = _CP27_TYPE._require_live_binding
_CP27_ALLOCATE = _CP27_TYPE.allocate
_CP27_VALIDATE_RESULT = _CP27_TYPE.validate_result
_CP27_CERTIFICATE_PROPERTY = _CP27_TYPE.certificate
_CP27_VALIDATE_CERTIFICATE = _reference._protocol._validate_certificate
_CP27_VALIDATE_RESULT_RECORD = _reference._protocol._validate_result_record

_TILT_TYPE = _tilt.ConfigurationInitialTiltComposer
_TILT_CERT_TYPE = _tilt.InitialTiltCompositionCertificate
_TILT_EVALUATION_TYPE = _tilt.InitialTiltPointEvaluation
_TILT_OWNER_SNAPSHOT = _TILT_TYPE._owner_snapshot
_TILT_REQUIRE_OWNER_SNAPSHOT = _TILT_TYPE._require_owner_snapshot
_TILT_LIVE_COMPONENTS = _TILT_TYPE._live_components
_TILT_EVALUATE = _TILT_TYPE.evaluate
_TILT_VALIDATE_EVALUATION = _TILT_TYPE.validate_evaluation
_TILT_CERTIFICATE_PROPERTY = _TILT_TYPE.certificate
_TILT_REFERENCE_COMPOSER_PROPERTY = _TILT_TYPE.reference_composer
_TILT_VALIDATE_CERTIFICATE = _tilt._validate_certificate
_TILT_VALIDATED_CONTEXT = _tilt._validated_context
_TILT_CONTEXT_SHA256 = _tilt._context_sha256
_TILT_CONFIGURATION_SHA256 = _tilt._configuration_sha256

_PROTOCOL = _reference._protocol
_CONTROL = _PROTOCOL._control
_LINEAGE = _PROTOCOL._lineage
_SEMANTIC_DIGEST = _PROTOCOL._thinning._semantic_digest
_REQUIRE_SHA256 = _PROTOCOL._thinning._require_sha256
_FIELD_MATCHES = _PROTOCOL._thinning._field_matches
_SAME_FLOAT = _PROTOCOL._thinning._same_float
_COMPOSER_TYPE = ProcessValidReferenceJumpComposer
_COMPOSER_LIVE = _COMPOSER_TYPE._require_live_binding
_EVENT_MODEL_KEY = TransformedEvent.model_key
_REFERENCE_ANCESTRY = _reference._reference_ancestry
_CAPTURE_FIELDS = _CONTROL._capture_fields
_REQUIRE_FIELDS_UNCHANGED = _CONTROL._require_fields_unchanged
_MAX_WORDS_PER_STREAM = (
    _CONTROL.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
)
_MAX_PREFLIGHT_RECORD_VISITS = 4_096


class PluginBridgeCounterKeyedInitialTiltRejectionPreparationError(ArithmeticError):
    """Fail-closed fixed-budget rejection-preparation error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH:
        raise ValueError("%s exceeds the text bound" % name)
    if value != expected:
        raise ValueError("%s differs from the exported value" % name)
    return value


def _require_sha256(value: object, *, name: str) -> str:
    return _REQUIRE_SHA256(value, name=name)


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact bool" % name)
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
    if value.bit_length() > INITIAL_TILT_REJECTION_MAX_INTEGER_BITS:
        raise ValueError("%s exceeds the integer-bit bound" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s is outside its frozen bound" % name)
    return value


def _exact_float(value: object, *, name: str, canonical_zero: bool = True) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact binary64 float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    if canonical_zero and value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError("%s must use canonical positive zero" % name)
    return value


def _exact_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    if type(numerator) is not int or type(denominator) is not int:
        raise TypeError("%s parts must be exact Python integers" % name)
    if (
        numerator.bit_length() > INITIAL_TILT_REJECTION_MAX_INTEGER_BITS
        or denominator.bit_length() > INITIAL_TILT_REJECTION_MAX_INTEGER_BITS
    ):
        raise ValueError("%s exceeds the integer-bit bound" % name)
    if denominator <= 0:
        raise ValueError("%s denominator must be positive" % name)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise ValueError("%s must be stored in reduced form" % name)
    return result


def _exact_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    length: int | None = None,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) > maximum:
        raise ValueError("%s exceeds its tuple bound" % name)
    if length is not None and len(value) != length:
        raise ValueError("%s has the wrong fixed length" % name)
    return value


def _require_callback_custody(custody_check: object | None) -> None:
    if custody_check is None:
        return
    if not callable(custody_check):
        raise TypeError("custody_check must be callable")
    custody_check()


def _attempt_layout(
    manifest: _CP28_MANIFEST_TYPE,
    attempt_budget: object,
) -> Tuple[int, Tuple[int, ...], int, int, int]:
    _preflight_manifest_structure(manifest, name="attempt_layout.manifest")
    attempt_count = _exact_integer(
        attempt_budget,
        name="attempt_budget",
        minimum=INITIAL_TILT_REJECTION_MIN_ATTEMPTS,
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
    )
    blocks = tuple(manifest.canonical_block_raw64_word_counts) + (1,)
    block_count = len(blocks)
    reference_words = manifest.required_raw64_words
    words_per_attempt = reference_words + 1
    maximum_by_records = INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS // block_count
    maximum_by_words = INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS // (
        words_per_attempt
    )
    maximum = min(
        INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
        maximum_by_records,
        maximum_by_words,
    )
    if attempt_count > maximum:
        raise ValueError("attempt_budget exceeds the fixed layout resource bound")
    if attempt_count * block_count > INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS:
        raise ValueError("attempt layout exceeds the record cap")
    if attempt_count * words_per_attempt > INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS:
        raise ValueError("attempt layout exceeds the word cap")
    return attempt_count, blocks, block_count, reference_words, words_per_attempt


def _logical_word_coordinates(
    attempt_budget: int,
    block_counts: Tuple[int, ...],
) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...]:
    coordinates = tuple(
        (
            (0, INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (
                0,
                0,
                INITIAL_TILT_REJECTION_STAGE_INDEX,
                attempt * len(block_counts) + block,
            ),
            offset,
        )
        for attempt in range(attempt_budget)
        for block, count in enumerate(block_counts)
        for offset in range(count)
    )
    if len(coordinates) != attempt_budget * sum(block_counts):
        raise RuntimeError("logical word coordinate count differs")
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("logical word coordinates are not distinct")
    return coordinates


def _instantiate_logical_word_coordinate_template(
    template: object,
    *,
    run_id: object,
    initialization_index: object,
) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...]:
    checked_run = _exact_integer(run_id, name="run_id")
    checked_initialization = _exact_integer(
        initialization_index, name="initialization_index"
    )
    if type(template) is not tuple:
        raise TypeError("logical word coordinate template must be an exact tuple")
    raw = _preflight_logical_word_coordinates(
        template,
        name="logical_word_coordinate_template",
        expected_length=len(template),
    )
    instantiated = tuple(
        (
            (checked_run, key[1]),
            (counter[0], checked_initialization, counter[2], counter[3]),
            offset,
        )
        for key, counter, offset in raw
    )
    if len(set(instantiated)) != len(instantiated):
        raise ValueError("instantiated logical word coordinates are not distinct")
    return instantiated


def _word_coordinate_digest(
    coordinates: Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...]
) -> str:
    return _SEMANTIC_DIGEST({"logical_word_coordinates": coordinates})


def _preflight_logical_word_coordinates(
    value: object,
    *,
    name: str,
    expected_length: int,
) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...]:
    outer = _exact_tuple(
        value,
        name=name,
        maximum=INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
        length=expected_length,
    )
    checked = []
    for position, coordinate in enumerate(outer):
        item = _exact_tuple(
            coordinate,
            name="%s[%d]" % (name, position),
            maximum=3,
            length=3,
        )
        key = _exact_tuple(
            item[0],
            name="%s[%d].key" % (name, position),
            maximum=2,
            length=2,
        )
        counter = _exact_tuple(
            item[1],
            name="%s[%d].counter" % (name, position),
            maximum=4,
            length=4,
        )
        checked_key = tuple(
            _exact_integer(
                word,
                name="%s[%d].key[%d]" % (name, position, index),
            )
            for index, word in enumerate(key)
        )
        checked_counter = tuple(
            _exact_integer(
                word,
                name="%s[%d].counter[%d]" % (name, position, index),
            )
            for index, word in enumerate(counter)
        )
        offset = _exact_integer(item[2], name="%s[%d].offset" % (name, position))
        checked.append((checked_key, checked_counter, offset))
    del checked
    return outer  # type: ignore[return-value]


def _preflight_block_counts(
    value: object,
    *,
    name: str,
    expected_length: int,
) -> Tuple[int, ...]:
    raw = _exact_tuple(
        value,
        name=name,
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=expected_length,
    )
    return tuple(
        _exact_integer(
            item,
            name="%s[%d]" % (name, position),
            minimum=1,
            maximum=_MAX_WORDS_PER_STREAM,
        )
        for position, item in enumerate(raw)
    )


def _freeze_certificate_schemas() -> Tuple[object, ...]:
    pending = [_CP28_CERT_TYPE, _CP27_CERT_TYPE, _TILT_CERT_TYPE]
    frozen = []
    seen = set()
    while pending:
        record_type = pending.pop()
        if record_type in seen:
            continue
        seen.add(record_type)
        fields = tuple(record_type.__annotations__)
        if not fields or len(fields) > 128:
            raise TypeError("parent certificate has an invalid field schema")
        hints = get_type_hints(record_type)
        if tuple(hints) != fields:
            raise TypeError("parent certificate annotations are incomplete")
        resolved = tuple((field, hints[field]) for field in fields)
        frozen.append((record_type, fields, resolved))
        for _, annotation in resolved:
            if isinstance(annotation, type) and annotation.__name__.endswith(
                "Certificate"
            ):
                pending.append(annotation)
    return tuple(frozen)


_PARENT_CERTIFICATE_SCHEMAS = _freeze_certificate_schemas()
_PARENT_CERTIFICATE_SCHEMA_BY_TYPE = {
    record_type: (fields, resolved)
    for record_type, fields, resolved in _PARENT_CERTIFICATE_SCHEMAS
}


def _freeze_operation_schemas() -> Tuple[object, ...]:
    operation_types = (
        _CP27_RESULT_TYPE,
        _PROTOCOL.CounterKeyedInitializerProtocolEntry,
        _CONTROL.CounterKeyedGlobalInitializerControlResult,
        _CONTROL.CounterKeyedGlobalInitializerControlConsumption,
        _CONTROL.CounterKeyedGlobalInitializerControlStream,
        _CONTROL.CounterKeyedGlobalInitializerControlAddress,
        _CONTROL._route_evidence.PhiloxRouteStateSnapshot,
    )
    frozen = []
    for record_type in operation_types:
        fields = tuple(record_type.__annotations__)
        hints = get_type_hints(record_type)
        if not fields or tuple(hints) != fields:
            raise TypeError("operation-record annotations are incomplete")
        frozen.append(
            (record_type, fields, tuple((field, hints[field]) for field in fields))
        )
    return tuple(frozen)


_OPERATION_SCHEMAS = _freeze_operation_schemas()
_OPERATION_SCHEMA_BY_TYPE = {
    record_type: (fields, resolved)
    for record_type, fields, resolved in _OPERATION_SCHEMAS
}


def _preflight_operation_tuple_resources(
    value: object,
    *,
    record_type: type,
    field: str,
    name: str,
) -> None:
    fixed_lengths = {
        (_CONTROL.CounterKeyedGlobalInitializerControlAddress, "philox_key"): 2,
        (_CONTROL.CounterKeyedGlobalInitializerControlAddress, "philox_counter"): 4,
        (_CONTROL._route_evidence.PhiloxRouteStateSnapshot, "counter"): 4,
        (_CONTROL._route_evidence.PhiloxRouteStateSnapshot, "key"): 2,
        (_CONTROL._route_evidence.PhiloxRouteStateSnapshot, "buffer"): 4,
    }
    if (record_type, field) in fixed_lengths:
        exact = fixed_lengths[(record_type, field)]
        _exact_tuple(value, name=name, maximum=exact, length=exact)
        return
    record_fields = {
        "entries",
        "entry_sha256s",
        "consumptions",
        "consumption_sha256s",
        "control_plan",
        "active_stage_roles",
        "work_item_raw64_word_counts",
    }
    if field in record_fields:
        _exact_tuple(
            value,
            name=name,
            maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        )
        return
    if field == "raw64_words":
        _exact_tuple(value, name=name, maximum=_MAX_WORDS_PER_STREAM)
        return
    _exact_tuple(value, name=name, maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS)


def _preflight_operation_value(
    value: object,
    annotation: object,
    *,
    name: str,
    seen: set,
) -> None:
    if annotation in (str, int, bool, float):
        if type(value) is not annotation:
            raise TypeError("%s has the wrong exact primitive type" % name)
        if annotation is str and len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH:
            raise ValueError("%s exceeds the text bound" % name)
        if (
            annotation is int
            and value.bit_length() > INITIAL_TILT_REJECTION_MAX_INTEGER_BITS
        ):
            raise ValueError("%s exceeds the integer-bit bound" % name)
        if annotation is float:
            _exact_float(value, name=name)
        return
    origin = get_origin(annotation)
    if origin is tuple:
        raw = _exact_tuple(value, name=name, maximum=_MAX_WORDS_PER_STREAM)
        arguments = get_args(annotation)
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            for position, item in enumerate(raw):
                _preflight_operation_value(
                    item,
                    arguments[0],
                    name="%s[%d]" % (name, position),
                    seen=seen,
                )
            return
        if len(raw) != len(arguments):
            raise ValueError("%s has the wrong fixed-tuple length" % name)
        for position, (item, item_type) in enumerate(zip(raw, arguments)):
            _preflight_operation_value(
                item,
                item_type,
                name="%s[%d]" % (name, position),
                seen=seen,
            )
        return
    if isinstance(annotation, type):
        if type(value) is not annotation:
            raise TypeError("%s has the wrong exact record type" % name)
        if annotation in _PARENT_CERTIFICATE_SCHEMA_BY_TYPE:
            _preflight_certificate_record(value, annotation, name=name, seen=seen)
        elif annotation in _OPERATION_SCHEMA_BY_TYPE:
            _preflight_operation_record(value, annotation, name=name, seen=seen)
        return
    raise TypeError("%s has an unsupported operation annotation" % name)


def _preflight_operation_record(
    value: object,
    expected_type: type,
    *,
    name: str,
    seen: set | None = None,
) -> object:
    if type(value) is not expected_type:
        raise TypeError("%s has the wrong exact operation-record type" % name)
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return value
    if len(seen) >= _MAX_PREFLIGHT_RECORD_VISITS:
        raise ValueError("operation tree exceeds the record-visit bound")
    seen.add(identity)
    fields, resolved = _OPERATION_SCHEMA_BY_TYPE[expected_type]
    if tuple(expected_type.__annotations__) != fields:
        raise ValueError("%s operation schema changed" % name)
    for field, annotation in resolved:
        if get_origin(annotation) is tuple:
            _preflight_operation_tuple_resources(
                getattr(value, field),
                record_type=expected_type,
                field=field,
                name="%s.%s" % (name, field),
            )
        _preflight_operation_value(
            getattr(value, field),
            annotation,
            name="%s.%s" % (name, field),
            seen=seen,
        )
    return value


def _preflight_certificate_value(
    value: object,
    annotation: object,
    *,
    name: str,
    seen: set,
) -> None:
    if annotation in (str, int, bool, float):
        if type(value) is not annotation:
            raise TypeError("%s has the wrong exact primitive type" % name)
        if annotation is str and len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH:
            raise ValueError("%s exceeds the text bound" % name)
        if annotation is int and value.bit_length() > (
            INITIAL_TILT_REJECTION_MAX_INTEGER_BITS
        ):
            raise ValueError("%s exceeds the integer-bit bound" % name)
        if annotation is float:
            _exact_float(value, name=name, canonical_zero=True)
        return
    origin = get_origin(annotation)
    if origin is tuple:
        raw = _exact_tuple(value, name=name, maximum=128)
        arguments = get_args(annotation)
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            for position, item in enumerate(raw):
                _preflight_certificate_value(
                    item,
                    arguments[0],
                    name="%s[%d]" % (name, position),
                    seen=seen,
                )
            return
        if len(raw) != len(arguments):
            raise ValueError("%s has the wrong fixed tuple length" % name)
        for position, (item, item_type) in enumerate(zip(raw, arguments)):
            _preflight_certificate_value(
                item,
                item_type,
                name="%s[%d]" % (name, position),
                seen=seen,
            )
        return
    if isinstance(annotation, type):
        if type(value) is not annotation:
            raise TypeError("%s has the wrong exact record type" % name)
        if annotation in _PARENT_CERTIFICATE_SCHEMA_BY_TYPE:
            _preflight_certificate_record(value, annotation, name=name, seen=seen)
        return
    raise TypeError("%s has an unsupported certificate annotation" % name)


def _preflight_certificate_record(
    value: object,
    expected_type: type,
    *,
    name: str,
    seen: set | None = None,
) -> object:
    if type(value) is not expected_type:
        raise TypeError("%s has the wrong exact certificate type" % name)
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return value
    if len(seen) >= _MAX_PREFLIGHT_RECORD_VISITS:
        raise ValueError("certificate tree exceeds the record-visit bound")
    seen.add(identity)
    fields, resolved = _PARENT_CERTIFICATE_SCHEMA_BY_TYPE[expected_type]
    if tuple(expected_type.__annotations__) != fields:
        raise ValueError("%s certificate schema changed" % name)
    for field, annotation in resolved:
        _preflight_certificate_value(
            getattr(value, field),
            annotation,
            name="%s.%s" % (name, field),
            seen=seen,
        )
    return value


def _require_parent_surfaces() -> None:
    expected = (
        (_CP28_TYPE._require_live_binding, _CP28_LIVE),
        (_CP28_TYPE.validate_result, _CP28_VALIDATE_RESULT),
        (_CP28_TYPE.certificate, _CP28_CERTIFICATE_PROPERTY),
        (_CP28_TYPE.manifest, _CP28_MANIFEST_PROPERTY),
        (_CP28_TYPE.protocol_owner, _CP28_PROTOCOL_PROPERTY),
        (_reference._validate_certificate, _CP28_VALIDATE_CERTIFICATE),
        (_reference._validate_manifest, _CP28_VALIDATE_MANIFEST),
        (_reference._validate_result_record, _CP28_VALIDATE_RESULT_RECORD),
        (_reference._validate_slot_record, _CP28_VALIDATE_SLOT_RECORD),
        (_reference._materialize_slot_fields, _CP28_MATERIALIZE_SLOT_FIELDS),
        (_reference._make_slot, _CP28_MAKE_SLOT),
        (_reference._quota_position, _CP28_QUOTA_POSITION),
        (_reference._event_sha256, _CP28_EVENT_SHA256),
        (_reference._configuration_sha256, _CP28_CONFIGURATION_SHA256),
        (_CP27_TYPE._require_live_binding, _CP27_LIVE),
        (_CP27_TYPE.allocate, _CP27_ALLOCATE),
        (_CP27_TYPE.validate_result, _CP27_VALIDATE_RESULT),
        (_CP27_TYPE.certificate, _CP27_CERTIFICATE_PROPERTY),
        (_PROTOCOL._validate_certificate, _CP27_VALIDATE_CERTIFICATE),
        (_PROTOCOL._validate_result_record, _CP27_VALIDATE_RESULT_RECORD),
        (_TILT_TYPE._owner_snapshot, _TILT_OWNER_SNAPSHOT),
        (_TILT_TYPE._require_owner_snapshot, _TILT_REQUIRE_OWNER_SNAPSHOT),
        (_TILT_TYPE._live_components, _TILT_LIVE_COMPONENTS),
        (_TILT_TYPE.evaluate, _TILT_EVALUATE),
        (_TILT_TYPE.validate_evaluation, _TILT_VALIDATE_EVALUATION),
        (_TILT_TYPE.certificate, _TILT_CERTIFICATE_PROPERTY),
        (_TILT_TYPE.reference_composer, _TILT_REFERENCE_COMPOSER_PROPERTY),
        (_tilt._validate_certificate, _TILT_VALIDATE_CERTIFICATE),
        (_tilt._validated_context, _TILT_VALIDATED_CONTEXT),
        (_tilt._context_sha256, _TILT_CONTEXT_SHA256),
        (_tilt._configuration_sha256, _TILT_CONFIGURATION_SHA256),
        (_COMPOSER_TYPE._require_live_binding, _COMPOSER_LIVE),
        (TransformedEvent.model_key, _EVENT_MODEL_KEY),
        (_reference._reference_ancestry, _REFERENCE_ANCESTRY),
        (_CONTROL._capture_fields, _CAPTURE_FIELDS),
        (_CONTROL._require_fields_unchanged, _REQUIRE_FIELDS_UNCHANGED),
    )
    for live, frozen in expected:
        if live is not frozen:
            raise ValueError("a cached parent callback surface changed")


def _runtime_sha256() -> str:
    constants = {
        "strategy": INITIAL_TILT_REJECTION_STRATEGY,
        "stage": INITIAL_TILT_REJECTION_STAGE_INDEX,
        "domain_tag": INITIAL_TILT_REJECTION_DOMAIN_TAG,
        "reserved_words": INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT,
        "minimum_attempts": INITIAL_TILT_REJECTION_MIN_ATTEMPTS,
        "maximum_attempts": INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
        "maximum_records": INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        "maximum_words": INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
        "maximum_context": INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION,
    }
    expected = {
        "strategy": "rejection",
        "stage": 1,
        "domain_tag": 7,
        "reserved_words": 1,
        "minimum_attempts": 1,
        "maximum_attempts": 64,
        "maximum_records": 64,
        "maximum_words": 65_536,
        "maximum_context": 4_096,
    }
    if constants != expected:
        raise ValueError("rejection-preparation constants changed")
    if _PROTOCOL.INITIALIZER_STRATEGY_REJECTION != "rejection":
        raise ValueError("checkpoint-27 rejection strategy changed")
    if _PROTOCOL.INITIALIZER_STAGE_REJECTION_ATTEMPT != 1:
        raise ValueError("checkpoint-27 rejection stage changed")
    _require_parent_surfaces()
    return _SEMANTIC_DIGEST(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _PREPARATION_POLICY,
            "scope": _PREPARATION_SCOPE,
            "python": tuple(sys.version_info[:3]),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "constants": tuple(sorted(constants.items())),
            "abstract_pushforward_codomain": (
                INITIAL_TILT_REJECTION_ABSTRACT_PUSHFORWARD_CODOMAIN
            ),
            "checkpoint28_schema": getattr(
                _reference,
                "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION",
            ),
            "checkpoint30_schema": _tilt.CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION,
        }
    )


def _hypothesis_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "reference_initializer_certificate",
        "manifest",
        "logical_word_coordinates",
        "hypothesis_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class InitialTiltRejectionPreparationWordFamilyHypothesis:
    """Concrete-layout-bound abstract iid word-family premise."""

    schema_version: str
    hypothesis_scope: str
    abstract_word_family_premise: str
    abstract_pushforward_codomain: str
    data_processing_theorem: str
    conditional_triangle_ledger: str
    reference_initializer_certificate: _CP28_CERT_TYPE
    reference_initializer_certificate_sha256: str
    reference_initializer_owner_runtime_identity: int
    manifest: _CP28_MANIFEST_TYPE
    manifest_sha256: str
    attempt_budget: int
    reference_block_count: int
    blocks_per_attempt: int
    reference_words_per_attempt: int
    words_per_attempt: int
    total_stream_records: int
    total_raw64_words: int
    block_raw64_word_counts: Tuple[int, ...]
    logical_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    logical_word_coordinate_sha256: str
    distinct_full_logical_word_coordinates_required: bool
    logical_word_coordinates_are_normalized_template: bool
    universal_run_initialization_instantiation_required: bool
    finite_injective_coordinate_relabeling_invariance_acknowledged: bool
    abstract_iid_uniform_uint64_family_assumed: bool
    repeated_coordinate_same_variable_acknowledged: bool
    deterministic_batch_pushforward_kernel_defined: bool
    failure_augmented_total_operational_map_acknowledged: bool
    failure_probability_certified: bool
    successful_record_conditional_law_certified: bool
    data_processing_accounting_conditional: bool
    source_plus_algorithm_triangle_ledger_conditional: bool
    live_philox_family_identified_with_abstract_family: bool
    actual_live_uniformity_certified: bool
    actual_live_independence_certified: bool
    physical_randomness_certified: bool
    live_initializer_distribution_admitted: bool
    global_address_one_shot_use_certified: bool
    hypothesis_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("word-family hypotheses cannot be subclassed")

    def __init__(
        self,
        *,
        _construction_token: object,
        _custody_check: object | None = None,
        **values: object,
    ) -> None:
        if _construction_token is not _HYPOTHESIS_TOKEN:
            raise TypeError("word-family hypotheses are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("word-family hypothesis fields are incomplete")
        _validate_hypothesis_values(values, custody_check=_custody_check)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("word-family hypotheses are not pickle objects")


def _hypothesis_fields() -> Tuple[str, ...]:
    return tuple(InitialTiltRejectionPreparationWordFamilyHypothesis.__annotations__)


def _validate_hypothesis_values(
    values: Mapping[str, object],
    *,
    hypothesis_record: object | None = None,
    custody_check: object | None = None,
) -> None:
    expected_text = {
        "schema_version": INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCHEMA_VERSION,
        "hypothesis_scope": INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCOPE,
        "abstract_word_family_premise": INITIAL_TILT_REJECTION_WORD_FAMILY_PREMISE,
        "abstract_pushforward_codomain": (
            INITIAL_TILT_REJECTION_ABSTRACT_PUSHFORWARD_CODOMAIN
        ),
        "data_processing_theorem": INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM,
        "conditional_triangle_ledger": INITIAL_TILT_REJECTION_TRIANGLE_LEDGER,
    }
    for name, expected in expected_text.items():
        _require_text(values[name], expected, name="hypothesis.%s" % name)
    parent = _preflight_certificate_record(
        values["reference_initializer_certificate"],
        _CP28_CERT_TYPE,
        name="hypothesis.reference_initializer_certificate",
    )
    _preflight_manifest_structure(values["manifest"], name="hypothesis.manifest")
    parent_snapshot = _parent_certificate_graph_snapshot((parent,))
    manifest_snapshot = _manifest_operation_snapshot(values["manifest"])
    hypothesis_before = (
        None
        if hypothesis_record is None
        else _record_snapshot(hypothesis_record, _hypothesis_fields())
    )
    checked_parent = _CP28_VALIDATE_CERTIFICATE(parent)
    if hypothesis_record is not None:
        _require_record_snapshot_unchanged(
            hypothesis_record,
            _hypothesis_fields(),
            hypothesis_before,
            name="word-family hypothesis",
        )
    _require_parent_certificate_graph_unchanged(parent_snapshot)
    _require_manifest_operation_unchanged(values["manifest"], manifest_snapshot)
    _require_callback_custody(custody_check)
    if checked_parent is not parent:
        raise ValueError("word-family CP28 validation substituted its certificate")
    manifest = _CP28_VALIDATE_MANIFEST(values["manifest"])
    if hypothesis_record is not None:
        _require_record_snapshot_unchanged(
            hypothesis_record,
            _hypothesis_fields(),
            hypothesis_before,
            name="word-family hypothesis",
        )
    _require_parent_certificate_graph_unchanged(parent_snapshot)
    _require_manifest_operation_unchanged(values["manifest"], manifest_snapshot)
    _require_callback_custody(custody_check)
    if parent.manifest is not manifest:
        raise ValueError("word-family hypothesis manifest identity differs")
    (
        attempt_budget,
        blocks,
        block_count,
        reference_words,
        words_per_attempt,
    ) = _attempt_layout(manifest, values["attempt_budget"])
    coordinates = _preflight_logical_word_coordinates(
        values["logical_word_coordinates"],
        name="hypothesis.logical_word_coordinates",
        expected_length=attempt_budget * words_per_attempt,
    )
    expected_coordinates = _logical_word_coordinates(attempt_budget, blocks)
    if coordinates != expected_coordinates:
        raise ValueError("word-family logical coordinates differ from the layout")
    expected_scalars = {
        "reference_initializer_certificate_sha256": parent.certificate_sha256,
        "manifest_sha256": manifest.manifest_sha256,
        "reference_block_count": block_count - 1,
        "blocks_per_attempt": block_count,
        "reference_words_per_attempt": reference_words,
        "words_per_attempt": words_per_attempt,
        "total_stream_records": attempt_budget * block_count,
        "total_raw64_words": attempt_budget * words_per_attempt,
        "block_raw64_word_counts": blocks,
        "logical_word_coordinate_sha256": _word_coordinate_digest(coordinates),
    }
    _preflight_block_counts(
        values["block_raw64_word_counts"],
        name="hypothesis.block_raw64_word_counts",
        expected_length=block_count,
    )
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("word-family hypothesis %s differs" % name)
    identity = _exact_integer(
        values["reference_initializer_owner_runtime_identity"],
        name="hypothesis.reference_initializer_owner_runtime_identity",
        minimum=1,
    )
    if identity == 0:
        raise ValueError("word-family owner identity is invalid")
    for name in (
        "distinct_full_logical_word_coordinates_required",
        "logical_word_coordinates_are_normalized_template",
        "universal_run_initialization_instantiation_required",
        "finite_injective_coordinate_relabeling_invariance_acknowledged",
        "abstract_iid_uniform_uint64_family_assumed",
        "repeated_coordinate_same_variable_acknowledged",
        "deterministic_batch_pushforward_kernel_defined",
        "failure_augmented_total_operational_map_acknowledged",
        "data_processing_accounting_conditional",
        "source_plus_algorithm_triangle_ledger_conditional",
    ):
        _exact_bool(values[name], True, name="hypothesis.%s" % name)
    for name in (
        "live_philox_family_identified_with_abstract_family",
        "failure_probability_certified",
        "successful_record_conditional_law_certified",
        "actual_live_uniformity_certified",
        "actual_live_independence_certified",
        "physical_randomness_certified",
        "live_initializer_distribution_admitted",
        "global_address_one_shot_use_certified",
    ):
        _exact_bool(values[name], False, name="hypothesis.%s" % name)
    for name in (
        "reference_initializer_certificate_sha256",
        "manifest_sha256",
        "logical_word_coordinate_sha256",
        "hypothesis_sha256",
    ):
        _require_sha256(values[name], name="hypothesis.%s" % name)
    expected_digest = _SEMANTIC_DIGEST(_hypothesis_payload(values))
    if values["hypothesis_sha256"] != expected_digest:
        raise ValueError("word-family hypothesis digest differs")


def _validate_hypothesis(
    hypothesis: object,
    *,
    custody_check: object | None = None,
) -> InitialTiltRejectionPreparationWordFamilyHypothesis:
    if type(hypothesis) is not InitialTiltRejectionPreparationWordFamilyHypothesis:
        raise TypeError("hypothesis has the wrong exact word-family type")
    values = {name: getattr(hypothesis, name) for name in _hypothesis_fields()}
    _validate_hypothesis_values(
        values,
        hypothesis_record=hypothesis,
        custody_check=custody_check,
    )
    return hypothesis


def validate_initial_tilt_rejection_preparation_word_family_hypothesis(
    hypothesis: object,
) -> InitialTiltRejectionPreparationWordFamilyHypothesis:
    """Validate the sealed hypothesis record without asserting a live law."""

    return _validate_hypothesis(hypothesis)


def _preflight_word_family_hypothesis(hypothesis: object) -> None:
    if type(hypothesis) is not InitialTiltRejectionPreparationWordFamilyHypothesis:
        raise TypeError("word_family_hypothesis has the wrong exact type")
    hints = get_type_hints(InitialTiltRejectionPreparationWordFamilyHypothesis)
    fields = _hypothesis_fields()
    if tuple(hints) != fields:
        raise ValueError("word-family hypothesis schema changed")
    for field in fields:
        value = getattr(hypothesis, field)
        annotation = hints[field]
        if annotation is str:
            if (
                type(value) is not str
                or len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH
            ):
                raise TypeError("hypothesis.%s must be bounded exact text" % field)
        elif annotation is int:
            _exact_integer(value, name="hypothesis.%s" % field)
        elif annotation is bool:
            if type(value) is not bool:
                raise TypeError("hypothesis.%s must be an exact bool" % field)
    _preflight_certificate_record(
        hypothesis.reference_initializer_certificate,
        _CP28_CERT_TYPE,
        name="hypothesis.reference_initializer_certificate",
    )
    _parent_certificate_graph_snapshot((hypothesis.reference_initializer_certificate,))
    _preflight_manifest_structure(hypothesis.manifest, name="hypothesis.manifest")
    block_count = _exact_integer(
        hypothesis.blocks_per_attempt,
        name="hypothesis.blocks_per_attempt",
        minimum=1,
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
    )
    _preflight_block_counts(
        hypothesis.block_raw64_word_counts,
        name="hypothesis.block_raw64_word_counts",
        expected_length=block_count,
    )
    total_words = _exact_integer(
        hypothesis.total_raw64_words,
        name="hypothesis.total_raw64_words",
        maximum=INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
    )
    _preflight_logical_word_coordinates(
        hypothesis.logical_word_coordinates,
        name="hypothesis.logical_word_coordinates",
        expected_length=total_words,
    )
    for field in (
        "reference_initializer_certificate_sha256",
        "manifest_sha256",
        "logical_word_coordinate_sha256",
        "hypothesis_sha256",
    ):
        _require_sha256(getattr(hypothesis, field), name="hypothesis.%s" % field)


def declare_initial_tilt_rejection_preparation_word_family_hypothesis(
    reference_initializer_owner: object,
    *,
    attempt_budget: object,
) -> InitialTiltRejectionPreparationWordFamilyHypothesis:
    """Declare the abstract source premise for one normalized CP28/A template."""

    checked_attempts = _exact_integer(
        attempt_budget,
        name="attempt_budget",
        minimum=INITIAL_TILT_REJECTION_MIN_ATTEMPTS,
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
    )
    if type(reference_initializer_owner) is not _CP28_TYPE:
        raise TypeError("reference_initializer_owner has the wrong exact CP28 type")
    manifest = _CP28_MANIFEST_PROPERTY.__get__(reference_initializer_owner, _CP28_TYPE)
    _preflight_manifest_structure(manifest, name="certification.manifest")
    manifest_snapshot = _manifest_operation_snapshot(manifest)
    parent = _CP28_CERTIFICATE_PROPERTY.__get__(reference_initializer_owner, _CP28_TYPE)
    parent_snapshot = _parent_certificate_graph_snapshot((parent,))

    def require_dependencies() -> None:
        _require_manifest_operation_unchanged(manifest, manifest_snapshot)
        _require_parent_certificate_graph_unchanged(parent_snapshot)

    _attempt_layout(manifest, checked_attempts)
    require_dependencies()
    live_parent = _CP28_LIVE(reference_initializer_owner)
    require_dependencies()
    if live_parent is not parent:
        raise ValueError("word-family declaration CP28 certificate identity changed")
    (
        attempt_count,
        blocks,
        block_count,
        reference_words,
        words_per_attempt,
    ) = _attempt_layout(manifest, checked_attempts)
    require_dependencies()
    coordinates = _logical_word_coordinates(attempt_count, blocks)
    values: Dict[str, object] = {
        "schema_version": INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCHEMA_VERSION,
        "hypothesis_scope": INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCOPE,
        "abstract_word_family_premise": INITIAL_TILT_REJECTION_WORD_FAMILY_PREMISE,
        "abstract_pushforward_codomain": (
            INITIAL_TILT_REJECTION_ABSTRACT_PUSHFORWARD_CODOMAIN
        ),
        "data_processing_theorem": INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM,
        "conditional_triangle_ledger": INITIAL_TILT_REJECTION_TRIANGLE_LEDGER,
        "reference_initializer_certificate": parent,
        "reference_initializer_certificate_sha256": parent.certificate_sha256,
        "reference_initializer_owner_runtime_identity": id(reference_initializer_owner),
        "manifest": manifest,
        "manifest_sha256": manifest.manifest_sha256,
        "attempt_budget": attempt_count,
        "reference_block_count": block_count - 1,
        "blocks_per_attempt": block_count,
        "reference_words_per_attempt": reference_words,
        "words_per_attempt": words_per_attempt,
        "total_stream_records": attempt_count * block_count,
        "total_raw64_words": attempt_count * words_per_attempt,
        "block_raw64_word_counts": blocks,
        "logical_word_coordinates": coordinates,
        "logical_word_coordinate_sha256": _word_coordinate_digest(coordinates),
        "distinct_full_logical_word_coordinates_required": True,
        "logical_word_coordinates_are_normalized_template": True,
        "universal_run_initialization_instantiation_required": True,
        "finite_injective_coordinate_relabeling_invariance_acknowledged": True,
        "abstract_iid_uniform_uint64_family_assumed": True,
        "repeated_coordinate_same_variable_acknowledged": True,
        "deterministic_batch_pushforward_kernel_defined": True,
        "failure_augmented_total_operational_map_acknowledged": True,
        "data_processing_accounting_conditional": True,
        "source_plus_algorithm_triangle_ledger_conditional": True,
        "live_philox_family_identified_with_abstract_family": False,
        "failure_probability_certified": False,
        "successful_record_conditional_law_certified": False,
        "actual_live_uniformity_certified": False,
        "actual_live_independence_certified": False,
        "physical_randomness_certified": False,
        "live_initializer_distribution_admitted": False,
        "global_address_one_shot_use_certified": False,
        "hypothesis_sha256": _ZERO_SHA256,
    }
    values["hypothesis_sha256"] = _SEMANTIC_DIGEST(_hypothesis_payload(values))
    result = InitialTiltRejectionPreparationWordFamilyHypothesis(
        **values,
        _construction_token=_HYPOTHESIS_TOKEN,
        _custody_check=require_dependencies,
    )
    require_dependencies()
    live_parent = _CP28_LIVE(reference_initializer_owner)
    require_dependencies()
    if live_parent is not parent:
        raise ValueError("word-family declaration CP28 certificate identity changed")
    return result


def _canonical_context(
    initial_tilt_composer: _TILT_TYPE,
    residual_context: object,
    *,
    custody_certificate: object | None = None,
    custody_snapshot: object | None = None,
    dependency_guard: object | None = None,
) -> Tuple[float, ...]:
    if (custody_certificate is None) is not (custody_snapshot is None):
        raise TypeError("canonical-context custody arguments are incomplete")

    def require_custody() -> None:
        if custody_certificate is not None:
            _require_preparation_certificate_operation_unchanged(
                custody_certificate, custody_snapshot
            )
        _require_callback_custody(dependency_guard)

    certificate = _TILT_CERTIFICATE_PROPERTY.__get__(initial_tilt_composer, _TILT_TYPE)
    require_custody()
    _preflight_certificate_record(
        certificate,
        _TILT_CERT_TYPE,
        name="initial_tilt_composer.certificate",
    )
    certificate_snapshot = _parent_certificate_graph_snapshot((certificate,))
    context = _TILT_VALIDATED_CONTEXT(
        residual_context,
        dimension=certificate.residual_context_dimension,
        name="residual_context",
    )
    _require_parent_certificate_graph_unchanged(certificate_snapshot)
    require_custody()
    if len(context) > INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION:
        raise ValueError("residual_context exceeds the frozen dimension bound")
    return context


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint28_certificate",
        "checkpoint27_certificate",
        "checkpoint30_certificate",
        "manifest",
        "word_family_hypothesis",
        "residual_context",
        "logical_word_coordinates",
        "certificate_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionPreparationCertificate:
    """Sealed fixed-budget proposal-and-score preparation certificate."""

    schema_version: str
    certificate_scope: str
    preparation_policy: str
    preparation_role_sha256: str
    process_parameter_sha256: str
    checkpoint28_certificate: _CP28_CERT_TYPE
    checkpoint28_certificate_sha256: str
    checkpoint28_initializer_role_sha256: str
    checkpoint28_runtime_sha256: str
    checkpoint27_certificate: _CP27_CERT_TYPE
    checkpoint27_certificate_sha256: str
    checkpoint27_protocol_role_sha256: str
    checkpoint27_runtime_sha256: str
    checkpoint30_certificate: _TILT_CERT_TYPE
    checkpoint30_certificate_sha256: str
    checkpoint30_composition_role_sha256: str
    checkpoint30_runtime_sha256: str
    reference_initializer_owner_runtime_identity: int
    initial_tilt_composer_runtime_identity: int
    reference_composer_runtime_identity: int
    process_runtime_identity: int
    manifest: _CP28_MANIFEST_TYPE
    manifest_sha256: str
    word_family_hypothesis: InitialTiltRejectionPreparationWordFamilyHypothesis
    word_family_hypothesis_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    residual_context_dimension: int
    attempt_budget: int
    reference_block_count: int
    blocks_per_attempt: int
    reference_words_per_attempt: int
    words_per_attempt: int
    total_stream_records: int
    total_raw64_words: int
    block_raw64_word_counts: Tuple[int, ...]
    logical_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    logical_word_coordinate_sha256: str
    logical_word_coordinates_normalized_template_certified: bool
    universal_run_initialization_instantiation_certified: bool
    injective_coordinate_relabeling_invariance_certified: bool
    global_initial_log_factor_upper_bound: float
    global_upper_bound_numerator: int
    global_upper_bound_denominator: int
    data_processing_theorem: str
    conditional_triangle_ledger: str
    preparation_runtime_sha256: str
    exact_checkpoint28_owner_binding_certified: bool
    exact_checkpoint30_owner_binding_certified: bool
    exact_shared_reference_composer_identity_certified: bool
    exact_shared_process_identity_certified: bool
    canonical_residual_context_frozen: bool
    fixed_attempt_budget_preflight_certified: bool
    complete_fixed_prefix_materialization_certified: bool
    exact_checkpoint28_candidate_transform_certified: bool
    complete_raw_slot_materialization_certified: bool
    checkpoint30_point_scoring_certified: bool
    exact_q_minus_upper_bound_witness_certified: bool
    reserved_decision_word_uninterpreted_certified: bool
    logical_word_coordinate_custody_certified: bool
    deterministic_replay_certified: bool
    conditional_abstract_finite_pushforward_defined: bool
    failure_augmented_total_operational_pushforward_defined: bool
    conditional_data_processing_accounting_defined: bool
    no_caller_rng_certified: bool
    no_retry_or_fallback_certified: bool
    acceptance_predicate_certified: bool
    acceptance_decision_certified: bool
    rejection_success_or_exhaustion_certified: bool
    failure_probability_certified: bool
    successful_record_conditional_law_certified: bool
    exponential_bernoulli_law_certified: bool
    first_accepted_output_certified: bool
    normalized_tilted_initializer_certified: bool
    exact_pi_n_law_certified: bool
    exact_continuous_gaussian_law_certified: bool
    analytic_target_certified: bool
    actual_live_uniformity_certified: bool
    actual_live_independence_certified: bool
    physical_randomness_certified: bool
    global_address_one_shot_use_certified: bool
    rejection_sampling_admissible: bool
    sir_admissible: bool
    initializer_admissible: bool
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
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-preparation certificates cannot be subclassed")

    def __init__(
        self,
        *,
        _construction_token: object,
        _custody_check: object | None = None,
        **values: object,
    ) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("rejection-preparation certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("rejection-preparation certificate fields are incomplete")
        _validate_certificate_values(values, custody_check=_custody_check)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-preparation certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionPreparationCertificate.__annotations__)


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint28_owner_binding_certified",
    "exact_checkpoint30_owner_binding_certified",
    "exact_shared_reference_composer_identity_certified",
    "exact_shared_process_identity_certified",
    "canonical_residual_context_frozen",
    "fixed_attempt_budget_preflight_certified",
    "complete_fixed_prefix_materialization_certified",
    "exact_checkpoint28_candidate_transform_certified",
    "complete_raw_slot_materialization_certified",
    "checkpoint30_point_scoring_certified",
    "exact_q_minus_upper_bound_witness_certified",
    "reserved_decision_word_uninterpreted_certified",
    "logical_word_coordinate_custody_certified",
    "logical_word_coordinates_normalized_template_certified",
    "universal_run_initialization_instantiation_certified",
    "injective_coordinate_relabeling_invariance_certified",
    "deterministic_replay_certified",
    "conditional_abstract_finite_pushforward_defined",
    "failure_augmented_total_operational_pushforward_defined",
    "conditional_data_processing_accounting_defined",
    "no_caller_rng_certified",
    "no_retry_or_fallback_certified",
    "passed",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "acceptance_predicate_certified",
    "acceptance_decision_certified",
    "rejection_success_or_exhaustion_certified",
    "failure_probability_certified",
    "successful_record_conditional_law_certified",
    "exponential_bernoulli_law_certified",
    "first_accepted_output_certified",
    "normalized_tilted_initializer_certified",
    "exact_pi_n_law_certified",
    "exact_continuous_gaussian_law_certified",
    "analytic_target_certified",
    "actual_live_uniformity_certified",
    "actual_live_independence_certified",
    "physical_randomness_certified",
    "global_address_one_shot_use_certified",
    "rejection_sampling_admissible",
    "sir_admissible",
    "initializer_admissible",
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


def _validate_certificate_values(
    values: Mapping[str, object],
    *,
    certificate_record: object | None = None,
    custody_check: object | None = None,
) -> None:
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _PREPARATION_SCOPE,
        "preparation_policy": _PREPARATION_POLICY,
        "data_processing_theorem": INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM,
        "conditional_triangle_ledger": INITIAL_TILT_REJECTION_TRIANGLE_LEDGER,
    }
    for name, expected in expected_text.items():
        _require_text(values[name], expected, name="certificate.%s" % name)
    parent28 = _preflight_certificate_record(
        values["checkpoint28_certificate"],
        _CP28_CERT_TYPE,
        name="certificate.checkpoint28_certificate",
    )
    parent27 = _preflight_certificate_record(
        values["checkpoint27_certificate"],
        _CP27_CERT_TYPE,
        name="certificate.checkpoint27_certificate",
    )
    parent30 = _preflight_certificate_record(
        values["checkpoint30_certificate"],
        _TILT_CERT_TYPE,
        name="certificate.checkpoint30_certificate",
    )
    _preflight_manifest_structure(values["manifest"], name="certificate.manifest")
    _preflight_word_family_hypothesis(values["word_family_hypothesis"])
    dependency_snapshot = _certificate_values_dependency_snapshot(values)
    certificate_before = (
        None
        if certificate_record is None
        else _record_snapshot(certificate_record, _certificate_fields())
    )
    checked28 = _CP28_VALIDATE_CERTIFICATE(parent28)
    if certificate_record is not None:
        _require_record_snapshot_unchanged(
            certificate_record,
            _certificate_fields(),
            certificate_before,
            name="rejection-preparation certificate",
        )
    _require_certificate_values_dependencies_unchanged(values, dependency_snapshot)
    _require_callback_custody(custody_check)
    checked27 = _CP27_VALIDATE_CERTIFICATE(parent27)
    if certificate_record is not None:
        _require_record_snapshot_unchanged(
            certificate_record,
            _certificate_fields(),
            certificate_before,
            name="rejection-preparation certificate",
        )
    _require_certificate_values_dependencies_unchanged(values, dependency_snapshot)
    _require_callback_custody(custody_check)
    checked30 = _TILT_VALIDATE_CERTIFICATE(parent30)
    if certificate_record is not None:
        _require_record_snapshot_unchanged(
            certificate_record,
            _certificate_fields(),
            certificate_before,
            name="rejection-preparation certificate",
        )
    _require_certificate_values_dependencies_unchanged(values, dependency_snapshot)
    _require_callback_custody(custody_check)
    if (
        checked28 is not parent28
        or checked27 is not parent27
        or checked30 is not parent30
    ):
        raise ValueError("parent certificate validation substituted a record")
    if parent28.checkpoint27_certificate is not parent27:
        raise ValueError("certificate checkpoint-27 identity differs")
    manifest = _CP28_VALIDATE_MANIFEST(values["manifest"])
    if certificate_record is not None:
        _require_record_snapshot_unchanged(
            certificate_record,
            _certificate_fields(),
            certificate_before,
            name="rejection-preparation certificate",
        )
    _require_certificate_values_dependencies_unchanged(values, dependency_snapshot)
    _require_callback_custody(custody_check)
    if parent28.manifest is not manifest:
        raise ValueError("certificate manifest identity differs")
    hypothesis = _validate_hypothesis(
        values["word_family_hypothesis"], custody_check=custody_check
    )
    if certificate_record is not None:
        _require_record_snapshot_unchanged(
            certificate_record,
            _certificate_fields(),
            certificate_before,
            name="rejection-preparation certificate",
        )
    _require_certificate_values_dependencies_unchanged(values, dependency_snapshot)
    _require_callback_custody(custody_check)
    if hypothesis.reference_initializer_certificate is not parent28:
        raise ValueError("certificate hypothesis has another CP28 certificate")
    if hypothesis.manifest is not manifest:
        raise ValueError("certificate hypothesis has another manifest")
    (
        attempt_budget,
        blocks,
        block_count,
        reference_words,
        words_per_attempt,
    ) = _attempt_layout(manifest, values["attempt_budget"])
    context = _exact_tuple(
        values["residual_context"],
        name="certificate.residual_context",
        maximum=INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION,
        length=parent30.residual_context_dimension,
    )
    for position, item in enumerate(context):
        _exact_float(item, name="certificate.residual_context[%d]" % position)
    coordinates = _preflight_logical_word_coordinates(
        values["logical_word_coordinates"],
        name="certificate.logical_word_coordinates",
        expected_length=attempt_budget * words_per_attempt,
    )
    if coordinates is not hypothesis.logical_word_coordinates:
        raise ValueError("certificate must preserve hypothesis coordinate identity")
    expected_scalars = {
        "checkpoint28_certificate_sha256": parent28.certificate_sha256,
        "checkpoint28_initializer_role_sha256": parent28.initializer_role_sha256,
        "checkpoint28_runtime_sha256": parent28.initializer_runtime_sha256,
        "checkpoint27_certificate_sha256": parent27.certificate_sha256,
        "checkpoint27_protocol_role_sha256": parent27.protocol_role_sha256,
        "checkpoint27_runtime_sha256": parent27.protocol_runtime_sha256,
        "checkpoint30_certificate_sha256": parent30.certificate_sha256,
        "checkpoint30_composition_role_sha256": parent30.composition_role_sha256,
        "checkpoint30_runtime_sha256": parent30.composer_runtime_sha256,
        "process_parameter_sha256": parent28.process_parameter_sha256,
        "manifest_sha256": manifest.manifest_sha256,
        "word_family_hypothesis_sha256": hypothesis.hypothesis_sha256,
        "residual_context_sha256": _TILT_CONTEXT_SHA256(context),
        "residual_context_dimension": len(context),
        "reference_block_count": block_count - 1,
        "blocks_per_attempt": block_count,
        "reference_words_per_attempt": reference_words,
        "words_per_attempt": words_per_attempt,
        "total_stream_records": attempt_budget * block_count,
        "total_raw64_words": attempt_budget * words_per_attempt,
        "block_raw64_word_counts": blocks,
        "logical_word_coordinate_sha256": hypothesis.logical_word_coordinate_sha256,
        "global_initial_log_factor_upper_bound": (
            parent30.initial_log_factor_upper_bound
        ),
        "preparation_runtime_sha256": _runtime_sha256(),
    }
    _preflight_block_counts(
        values["block_raw64_word_counts"],
        name="certificate.block_raw64_word_counts",
        expected_length=block_count,
    )
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is float and type(expected) is float:
            if not _SAME_FLOAT(actual, expected):
                raise ValueError("rejection-preparation certificate %s differs" % name)
        elif type(actual) is not type(expected) or actual != expected:
            raise ValueError("rejection-preparation certificate %s differs" % name)
    for name in (
        "preparation_role_sha256",
        "process_parameter_sha256",
        "checkpoint28_certificate_sha256",
        "checkpoint28_initializer_role_sha256",
        "checkpoint28_runtime_sha256",
        "checkpoint27_certificate_sha256",
        "checkpoint27_protocol_role_sha256",
        "checkpoint27_runtime_sha256",
        "checkpoint30_certificate_sha256",
        "checkpoint30_composition_role_sha256",
        "checkpoint30_runtime_sha256",
        "manifest_sha256",
        "word_family_hypothesis_sha256",
        "residual_context_sha256",
        "logical_word_coordinate_sha256",
        "preparation_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate.%s" % name)
    for name in (
        "reference_initializer_owner_runtime_identity",
        "initial_tilt_composer_runtime_identity",
        "reference_composer_runtime_identity",
        "process_runtime_identity",
    ):
        _exact_integer(values[name], name="certificate.%s" % name, minimum=1)
    upper = _exact_float(
        values["global_initial_log_factor_upper_bound"],
        name="certificate.global_initial_log_factor_upper_bound",
    )
    numerator = _exact_integer(
        values["global_upper_bound_numerator"],
        name="certificate.global_upper_bound_numerator",
        minimum=-(1 << 131071),
        maximum=(1 << 131071),
    )
    denominator = _exact_integer(
        values["global_upper_bound_denominator"],
        name="certificate.global_upper_bound_denominator",
        minimum=1,
        maximum=(1 << 131071),
    )
    if Fraction(numerator, denominator) != Fraction.from_float(upper):
        raise ValueError("certificate global upper-bound fraction differs")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate.%s" % name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate.%s" % name)
    expected_digest = _SEMANTIC_DIGEST(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("rejection-preparation certificate digest differs")


def _validate_certificate(
    certificate: object,
    *,
    custody_check: object | None = None,
) -> CounterKeyedInitialTiltRejectionPreparationCertificate:
    if type(certificate) is not CounterKeyedInitialTiltRejectionPreparationCertificate:
        raise TypeError("certificate has the wrong exact rejection-preparation type")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    _validate_certificate_values(
        values,
        certificate_record=certificate,
        custody_check=custody_check,
    )
    return certificate


def _make_certificate(
    reference_initializer_owner: _CP28_TYPE,
    initial_tilt_composer: _TILT_TYPE,
    residual_context: Tuple[float, ...],
    attempt_budget: int,
    preparation_role_sha256: str,
    hypothesis: InitialTiltRejectionPreparationWordFamilyHypothesis,
    *,
    custody_check: object | None = None,
) -> CounterKeyedInitialTiltRejectionPreparationCertificate:
    parent28 = _CP28_CERTIFICATE_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    _require_callback_custody(custody_check)
    protocol_owner = _CP28_PROTOCOL_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    _require_callback_custody(custody_check)
    parent27 = _CP27_CERTIFICATE_PROPERTY.__get__(protocol_owner, _CP27_TYPE)
    _require_callback_custody(custody_check)
    parent30 = _TILT_CERTIFICATE_PROPERTY.__get__(initial_tilt_composer, _TILT_TYPE)
    _require_callback_custody(custody_check)
    manifest = _CP28_MANIFEST_PROPERTY.__get__(reference_initializer_owner, _CP28_TYPE)
    _require_callback_custody(custody_check)
    (
        attempt_count,
        blocks,
        block_count,
        reference_words,
        words_per_attempt,
    ) = _attempt_layout(manifest, attempt_budget)
    reference_composer = _TILT_REFERENCE_COMPOSER_PROPERTY.__get__(
        initial_tilt_composer, _TILT_TYPE
    )
    _require_callback_custody(custody_check)
    process = reference_composer.process
    _require_callback_custody(custody_check)
    upper = parent30.initial_log_factor_upper_bound
    upper_fraction = Fraction.from_float(upper)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _PREPARATION_SCOPE,
        "preparation_policy": _PREPARATION_POLICY,
        "preparation_role_sha256": preparation_role_sha256,
        "process_parameter_sha256": parent28.process_parameter_sha256,
        "checkpoint28_certificate": parent28,
        "checkpoint28_certificate_sha256": parent28.certificate_sha256,
        "checkpoint28_initializer_role_sha256": parent28.initializer_role_sha256,
        "checkpoint28_runtime_sha256": parent28.initializer_runtime_sha256,
        "checkpoint27_certificate": parent27,
        "checkpoint27_certificate_sha256": parent27.certificate_sha256,
        "checkpoint27_protocol_role_sha256": parent27.protocol_role_sha256,
        "checkpoint27_runtime_sha256": parent27.protocol_runtime_sha256,
        "checkpoint30_certificate": parent30,
        "checkpoint30_certificate_sha256": parent30.certificate_sha256,
        "checkpoint30_composition_role_sha256": parent30.composition_role_sha256,
        "checkpoint30_runtime_sha256": parent30.composer_runtime_sha256,
        "reference_initializer_owner_runtime_identity": id(reference_initializer_owner),
        "initial_tilt_composer_runtime_identity": id(initial_tilt_composer),
        "reference_composer_runtime_identity": id(reference_composer),
        "process_runtime_identity": id(process),
        "manifest": manifest,
        "manifest_sha256": manifest.manifest_sha256,
        "word_family_hypothesis": hypothesis,
        "word_family_hypothesis_sha256": hypothesis.hypothesis_sha256,
        "residual_context": residual_context,
        "residual_context_sha256": _TILT_CONTEXT_SHA256(residual_context),
        "residual_context_dimension": len(residual_context),
        "attempt_budget": attempt_count,
        "reference_block_count": block_count - 1,
        "blocks_per_attempt": block_count,
        "reference_words_per_attempt": reference_words,
        "words_per_attempt": words_per_attempt,
        "total_stream_records": attempt_count * block_count,
        "total_raw64_words": attempt_count * words_per_attempt,
        "block_raw64_word_counts": blocks,
        "logical_word_coordinates": hypothesis.logical_word_coordinates,
        "logical_word_coordinate_sha256": hypothesis.logical_word_coordinate_sha256,
        "global_initial_log_factor_upper_bound": upper,
        "global_upper_bound_numerator": upper_fraction.numerator,
        "global_upper_bound_denominator": upper_fraction.denominator,
        "data_processing_theorem": INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM,
        "conditional_triangle_ledger": INITIAL_TILT_REJECTION_TRIANGLE_LEDGER,
        "preparation_runtime_sha256": _runtime_sha256(),
        "certificate_sha256": _ZERO_SHA256,
    }
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        values[name] = True
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        values[name] = False
    values["certificate_sha256"] = _SEMANTIC_DIGEST(_certificate_payload(values))
    result = CounterKeyedInitialTiltRejectionPreparationCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
        _custody_check=custody_check,
    )
    _require_callback_custody(custody_check)
    return result


def _attempt_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_entries",
        "proposal_raw64_blocks",
        "proposal_raw_slots",
        "selected_raw_events",
        "canonical_configuration",
        "score_evaluation",
        "logical_word_coordinates",
        "attempt_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionAttempt:
    """One completely transformed and scored, but undecided, attempt."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate
    certificate_sha256: str
    run_id: int
    initialization_index: int
    attempt_index: int
    parent_entry_start: int
    parent_entry_stop: int
    parent_entries: Tuple[_PROTOCOL.CounterKeyedInitializerProtocolEntry, ...]
    parent_entry_sha256s: Tuple[str, ...]
    proposal_raw64_blocks: Tuple[Tuple[int, ...], ...]
    proposal_block_offsets: Tuple[int, ...]
    proposal_concatenated_raw64_words: Tuple[int, ...]
    proposal_total_raw64_words: int
    reserved_decision_entry_sha256: str
    reserved_decision_raw64_block: Tuple[int, ...]
    reserved_decision_raw64_word: int
    logical_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    logical_word_coordinate_sha256: str
    count_word_offset: int
    count_raw64_word: int
    count_quota_position: int
    sampled_cardinality: int
    proposal_raw_slots: Tuple[_CP28_RAW_SLOT_TYPE, ...]
    proposal_raw_slot_sha256s: Tuple[str, ...]
    selected_raw_events: TransformedConfiguration
    selected_raw_event_sha256s: Tuple[str, ...]
    canonical_configuration: TransformedConfiguration
    canonical_configuration_sha256: str
    canonical_position_to_raw_slot: Tuple[int, ...]
    raw_slot_to_canonical_position: Tuple[int | None, ...]
    score_evaluation: _TILT_EVALUATION_TYPE
    score_evaluation_sha256: str
    q_numerator: int
    q_denominator: int
    global_upper_bound_numerator: int
    global_upper_bound_denominator: int
    q_minus_upper_bound_numerator: int
    q_minus_upper_bound_denominator: int
    q_minus_upper_bound_nonpositive: bool
    exact_cp28_equivalent_candidate_transform: bool
    all_raw_slots_materialized_before_count_decode: bool
    duplicate_stable_canonical_bijection: bool
    checkpoint30_point_score_validated: bool
    reserved_decision_word_uninterpreted: bool
    acceptance_predicate_evaluated: bool
    acceptance_decision_made: bool
    exponential_or_uniform_transform_applied: bool
    attempt_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-preparation attempts cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATTEMPT_TOKEN:
            raise TypeError("rejection-preparation attempts are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("rejection-preparation attempt fields are incomplete")
        _preflight_attempt_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-preparation attempts are not pickle objects")


def _attempt_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionAttempt.__annotations__)


def _preflight_event(event: object, *, name: str, maximum_dimension: int) -> None:
    if type(event) is not TransformedEvent:
        raise TypeError("%s has the wrong exact transformed-event type" % name)
    _exact_integer(event.event_type, name=name + ".event_type")
    coordinates = _exact_tuple(
        event.coordinates,
        name=name + ".coordinates",
        maximum=maximum_dimension,
    )
    for position, coordinate in enumerate(coordinates):
        _exact_float(coordinate, name="%s.coordinates[%d]" % (name, position))


def _preflight_configuration(
    configuration: object,
    *,
    name: str,
    maximum_cardinality: int,
    maximum_dimension: int,
) -> TransformedConfiguration:
    checked = _exact_tuple(
        configuration,
        name=name,
        maximum=maximum_cardinality,
    )
    for position, event in enumerate(checked):
        _preflight_event(
            event,
            name="%s[%d]" % (name, position),
            maximum_dimension=maximum_dimension,
        )
    return checked  # type: ignore[return-value]


def _preflight_raw_words(
    value: object,
    *,
    name: str,
    maximum: int,
    length: int | None = None,
) -> Tuple[int, ...]:
    words = _exact_tuple(value, name=name, maximum=maximum, length=length)
    for position, word in enumerate(words):
        _exact_integer(word, name="%s[%d]" % (name, position))
    return words  # type: ignore[return-value]


def _preflight_sha256_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    length: int,
) -> Tuple[str, ...]:
    raw = _exact_tuple(value, name=name, maximum=maximum, length=length)
    return tuple(
        _require_sha256(item, name="%s[%d]" % (name, position))
        for position, item in enumerate(raw)
    )


def _preflight_index_tuple(
    value: object,
    *,
    name: str,
    length: int,
    maximum_value: int,
    optional: bool = False,
) -> Tuple[int | None, ...]:
    raw = _exact_tuple(value, name=name, maximum=length, length=length)
    checked = []
    for position, item in enumerate(raw):
        if optional and item is None:
            checked.append(None)
        else:
            checked.append(
                _exact_integer(
                    item,
                    name="%s[%d]" % (name, position),
                    maximum=maximum_value,
                )
            )
    return tuple(checked)


def _preflight_tilt_evaluation(evaluation: object, *, certificate: object) -> None:
    if type(evaluation) is not _TILT_EVALUATION_TYPE:
        raise TypeError("score evaluation has the wrong exact checkpoint-30 type")
    if type(certificate) is not CounterKeyedInitialTiltRejectionPreparationCertificate:
        raise TypeError("score certificate has the wrong exact preparation type")
    fields = tuple(_TILT_EVALUATION_TYPE.__annotations__)
    hints = get_type_hints(_TILT_EVALUATION_TYPE)
    if tuple(hints) != fields:
        raise ValueError("checkpoint-30 evaluation schema changed")
    for field in fields:
        if field in ("configuration", "residual_context"):
            continue
        _preflight_certificate_value(
            getattr(evaluation, field),
            hints[field],
            name="score_evaluation.%s" % field,
            seen=set(),
        )
    _preflight_configuration(
        evaluation.configuration,
        name="score_evaluation.configuration",
        maximum_cardinality=certificate.manifest.total_cap,
        maximum_dimension=certificate.manifest.maximum_coordinate_dimension,
    )
    context = _exact_tuple(
        evaluation.residual_context,
        name="score_evaluation.residual_context",
        maximum=INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION,
        length=certificate.residual_context_dimension,
    )
    for position, item in enumerate(context):
        _exact_float(item, name="score_evaluation.residual_context[%d]" % position)


def _preflight_preparation_certificate(certificate: object, *, name: str) -> None:
    if type(certificate) is not CounterKeyedInitialTiltRejectionPreparationCertificate:
        raise TypeError("%s has the wrong exact preparation-certificate type" % name)
    for field in (
        "schema_version",
        "certificate_scope",
        "preparation_policy",
        "data_processing_theorem",
        "conditional_triangle_ledger",
    ):
        value = getattr(certificate, field)
        if (
            type(value) is not str
            or len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH
        ):
            raise TypeError("%s.%s must be bounded exact text" % (name, field))
    for field in (
        "preparation_role_sha256",
        "process_parameter_sha256",
        "checkpoint28_certificate_sha256",
        "checkpoint28_initializer_role_sha256",
        "checkpoint28_runtime_sha256",
        "checkpoint27_certificate_sha256",
        "checkpoint27_protocol_role_sha256",
        "checkpoint27_runtime_sha256",
        "checkpoint30_certificate_sha256",
        "checkpoint30_composition_role_sha256",
        "checkpoint30_runtime_sha256",
        "manifest_sha256",
        "word_family_hypothesis_sha256",
        "residual_context_sha256",
        "logical_word_coordinate_sha256",
        "preparation_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, field), name="%s.%s" % (name, field))
    for field in (
        "reference_initializer_owner_runtime_identity",
        "initial_tilt_composer_runtime_identity",
        "reference_composer_runtime_identity",
        "process_runtime_identity",
    ):
        _exact_integer(
            getattr(certificate, field),
            name="%s.%s" % (name, field),
            minimum=1,
        )
    for field in (
        "residual_context_dimension",
        "attempt_budget",
        "reference_block_count",
        "blocks_per_attempt",
        "reference_words_per_attempt",
        "words_per_attempt",
        "total_stream_records",
        "total_raw64_words",
    ):
        _exact_integer(
            getattr(certificate, field),
            name="%s.%s" % (name, field),
            maximum=INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
        )
    manifest = certificate.manifest
    _preflight_manifest_structure(manifest, name=name + ".manifest")
    _parent_certificate_graph_snapshot(
        (
            certificate.checkpoint28_certificate,
            certificate.checkpoint27_certificate,
            certificate.checkpoint30_certificate,
        )
    )
    _preflight_word_family_hypothesis(certificate.word_family_hypothesis)
    for field in (
        "total_cap",
        "maximum_coordinate_dimension",
        "required_raw64_words",
    ):
        _exact_integer(
            getattr(manifest, field),
            name="%s.manifest.%s" % (name, field),
            maximum=INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
        )
    _preflight_block_counts(
        certificate.block_raw64_word_counts,
        name=name + ".block_raw64_word_counts",
        expected_length=certificate.blocks_per_attempt,
    )
    context = _exact_tuple(
        certificate.residual_context,
        name=name + ".residual_context",
        maximum=INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION,
        length=certificate.residual_context_dimension,
    )
    for position, item in enumerate(context):
        _exact_float(item, name="%s.residual_context[%d]" % (name, position))
    _preflight_logical_word_coordinates(
        certificate.logical_word_coordinates,
        name=name + ".logical_word_coordinates",
        expected_length=certificate.total_raw64_words,
    )
    _exact_float(
        certificate.global_initial_log_factor_upper_bound,
        name=name + ".global_initial_log_factor_upper_bound",
    )
    _exact_fraction_parts(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
        name=name + ".global_upper_bound",
    )
    for field in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(getattr(certificate, field), True, name="%s.%s" % (name, field))
    for field in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(getattr(certificate, field), False, name="%s.%s" % (name, field))


def _preflight_raw_slot(slot: object, *, name: str, manifest: object) -> None:
    if type(slot) is not _CP28_RAW_SLOT_TYPE:
        raise TypeError("%s has the wrong exact CP28 raw-slot type" % name)
    if type(manifest) is not _CP28_MANIFEST_TYPE:
        raise TypeError("%s manifest has the wrong exact type" % name)
    fields = tuple(_CP28_RAW_SLOT_TYPE.__annotations__)
    hints = get_type_hints(_CP28_RAW_SLOT_TYPE)
    if tuple(hints) != fields:
        raise ValueError("CP28 raw-slot schema changed")
    large_tuple_fields = {
        "coordinate_word_offsets",
        "coordinate_raw64_words",
        "coordinate_bucket_indices",
        "coordinate_midpoint_numerators",
        "coordinate_probability_hexes",
        "coordinate_codebook_values",
        "coordinate_value_hexes",
        "active_coordinates",
    }
    for field in fields:
        if field in large_tuple_fields or field == "event":
            continue
        _preflight_certificate_value(
            getattr(slot, field),
            hints[field],
            name="%s.%s" % (name, field),
            seen=set(),
        )
    for field in large_tuple_fields:
        raw = _exact_tuple(
            getattr(slot, field),
            name="%s.%s" % (name, field),
            maximum=manifest.maximum_coordinate_dimension,
        )
        annotation = get_args(hints[field])[0]
        for position, item in enumerate(raw):
            _preflight_certificate_value(
                item,
                annotation,
                name="%s.%s[%d]" % (name, field, position),
                seen=set(),
            )
    _preflight_event(
        slot.event,
        name=name + ".event",
        maximum_dimension=manifest.maximum_coordinate_dimension,
    )


_MATERIALIZED_SLOT_FIELD_NAMES = (
    "raw_slot_index",
    "type_word_offset",
    "type_raw64_word",
    "type_quota_position",
    "event_type",
    "event_dimension",
    "coordinate_word_count",
    "coordinate_word_offsets",
    "coordinate_raw64_words",
    "coordinate_bucket_indices",
    "coordinate_midpoint_numerators",
    "coordinate_probability_hexes",
    "coordinate_codebook_values",
    "coordinate_value_hexes",
    "active_coordinates",
    "event",
    "event_sha256",
)


def _preflight_materialized_slot_fields(
    fields: object,
    *,
    manifest: object,
    words: Tuple[int, ...],
    raw_slot_index: int,
) -> Dict[str, object]:
    if type(fields) is not dict:
        raise TypeError("CP28 slot materializer returned another type")
    expected_keys = set(_MATERIALIZED_SLOT_FIELD_NAMES)
    if any(type(key) is not str for key in fields):
        raise TypeError("CP28 materialized slot keys must be exact text")
    if set(fields) != expected_keys:
        raise ValueError("CP28 materialized slot field set differs")
    for name, maximum in (
        ("raw_slot_index", manifest.total_cap - 1),
        ("type_word_offset", len(words) - 1),
        ("type_raw64_word", (1 << 64) - 1),
        ("type_quota_position", len(manifest.type_ids) - 1),
        ("event_type", (1 << 64) - 1),
        ("event_dimension", manifest.maximum_coordinate_dimension),
        ("coordinate_word_count", manifest.maximum_coordinate_dimension),
    ):
        _exact_integer(fields[name], name="materialized.%s" % name, maximum=maximum)
    if fields["raw_slot_index"] != raw_slot_index:
        raise ValueError("CP28 materialized raw-slot index differs")
    coordinate_count = manifest.maximum_coordinate_dimension
    for name, item_type in (
        ("coordinate_word_offsets", int),
        ("coordinate_raw64_words", int),
        ("coordinate_bucket_indices", int),
        ("coordinate_midpoint_numerators", int),
        ("coordinate_probability_hexes", str),
        ("coordinate_codebook_values", float),
        ("coordinate_value_hexes", str),
    ):
        raw = _exact_tuple(
            fields[name],
            name="materialized.%s" % name,
            maximum=coordinate_count,
            length=coordinate_count,
        )
        for position, item in enumerate(raw):
            if type(item) is not item_type:
                raise TypeError("materialized.%s[%d] has wrong type" % (name, position))
            if item_type is int:
                _exact_integer(item, name="materialized.%s[%d]" % (name, position))
            elif item_type is float:
                _exact_float(item, name="materialized.%s[%d]" % (name, position))
            elif len(item) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH:
                raise ValueError("materialized text exceeds its bound")
    active = _exact_tuple(
        fields["active_coordinates"],
        name="materialized.active_coordinates",
        maximum=coordinate_count,
        length=fields["event_dimension"],
    )
    for position, item in enumerate(active):
        _exact_float(item, name="materialized.active_coordinates[%d]" % position)
    _preflight_event(
        fields["event"],
        name="materialized.event",
        maximum_dimension=coordinate_count,
    )
    _require_sha256(fields["event_sha256"], name="materialized.event_sha256")
    return fields


def _materialized_slot_fields_snapshot(fields: Dict[str, object]) -> Tuple[object, ...]:
    return (
        tuple((name, fields[name]) for name in _MATERIALIZED_SLOT_FIELD_NAMES),
        _record_snapshot(fields["event"], tuple(TransformedEvent.__annotations__)),
    )


def _require_materialized_slot_fields_unchanged(
    fields: Dict[str, object],
    snapshot: Tuple[object, ...],
    *,
    manifest: _CP28_MANIFEST_TYPE,
    words: Tuple[int, ...],
    raw_slot_index: int,
) -> None:
    _preflight_materialized_slot_fields(
        fields,
        manifest=manifest,
        words=words,
        raw_slot_index=raw_slot_index,
    )
    fields_before, event_before = snapshot
    if type(fields_before) is not tuple or len(fields_before) != len(
        _MATERIALIZED_SLOT_FIELD_NAMES
    ):
        raise TypeError("materialized slot-field snapshot is malformed")
    identity_fields = {
        "coordinate_word_offsets",
        "coordinate_raw64_words",
        "coordinate_bucket_indices",
        "coordinate_midpoint_numerators",
        "coordinate_probability_hexes",
        "coordinate_codebook_values",
        "coordinate_value_hexes",
        "active_coordinates",
        "event",
    }
    for expected_name, before in fields_before:
        if type(expected_name) is not str or expected_name not in fields:
            raise TypeError("materialized slot-field snapshot is malformed")
        current = fields[expected_name]
        if type(current) is not type(before) or not _FIELD_MATCHES(
            expected_name, current, before
        ):
            raise ValueError("materialized slot field %s changed" % expected_name)
        if expected_name in identity_fields and current is not before:
            raise ValueError(
                "materialized slot field %s identity changed" % expected_name
            )
    event = fields["event"]
    _REQUIRE_FIELDS_UNCHANGED(
        event,
        tuple(TransformedEvent.__annotations__),
        event_before,
        identity_fields=("coordinates",),
        name="rejection-preparation materialized event %d" % raw_slot_index,
    )


def _preflight_attempt_values(values: Mapping[str, object]) -> None:
    certificate = values["certificate"]
    _preflight_preparation_certificate(certificate, name="attempt.certificate")
    if type(values["schema_version"]) is not str:
        raise TypeError("attempt.schema_version must be exact text")
    _require_sha256(values["certificate_sha256"], name="attempt.certificate_sha256")
    attempt_index = _exact_integer(
        values["attempt_index"],
        name="attempt.attempt_index",
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS - 1,
    )
    _exact_integer(values["run_id"], name="attempt.run_id")
    _exact_integer(values["initialization_index"], name="attempt.initialization_index")
    blocks_per_attempt = _exact_integer(
        certificate.blocks_per_attempt,
        name="attempt.certificate.blocks_per_attempt",
        minimum=1,
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
    )
    entries = _exact_tuple(
        values["parent_entries"],
        name="attempt.parent_entries",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=blocks_per_attempt,
    )
    for position, entry in enumerate(entries):
        if type(entry) is not _PROTOCOL.CounterKeyedInitializerProtocolEntry:
            raise TypeError("attempt.parent_entries[%d] has the wrong type" % position)
        if type(entry.strategy) is not str or type(entry.semantic_role) is not str:
            raise TypeError("attempt parent entry strategy/role must be exact text")
        for field in (
            "plan_position",
            "chronological_index",
            "work_item_index",
            "block_index",
            "stage_index",
            "attempt_index",
        ):
            _exact_integer(
                getattr(entry, field),
                name="attempt.parent_entries[%d].%s" % (position, field),
            )
        _require_sha256(
            entry.entry_sha256,
            name="attempt.parent_entries[%d].entry_sha256" % position,
        )
        _exact_integer(
            entry.raw64_word_count,
            name="attempt.parent_entries[%d].raw64_word_count" % position,
            minimum=1,
            maximum=_MAX_WORDS_PER_STREAM,
        )
        _preflight_raw_words(
            entry.raw64_words,
            name="attempt.parent_entries[%d].raw64_words" % position,
            maximum=_MAX_WORDS_PER_STREAM,
            length=entry.raw64_word_count,
        )
    _preflight_sha256_tuple(
        values["parent_entry_sha256s"],
        name="attempt.parent_entry_sha256s",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=blocks_per_attempt,
    )
    _exact_integer(
        values["parent_entry_start"],
        name="attempt.parent_entry_start",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
    )
    _exact_integer(
        values["parent_entry_stop"],
        name="attempt.parent_entry_stop",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
    )
    proposal_blocks = _exact_tuple(
        values["proposal_raw64_blocks"],
        name="attempt.proposal_raw64_blocks",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.reference_block_count,
    )
    for position, block in enumerate(proposal_blocks):
        _preflight_raw_words(
            block,
            name="attempt.proposal_raw64_blocks[%d]" % position,
            maximum=_MAX_WORDS_PER_STREAM,
            length=certificate.block_raw64_word_counts[position],
        )
    _preflight_raw_words(
        values["proposal_concatenated_raw64_words"],
        name="attempt.proposal_concatenated_raw64_words",
        maximum=INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS,
        length=certificate.reference_words_per_attempt,
    )
    offsets = _exact_tuple(
        values["proposal_block_offsets"],
        name="attempt.proposal_block_offsets",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.reference_block_count + 1,
    )
    for position, offset in enumerate(offsets):
        _exact_integer(
            offset,
            name="attempt.proposal_block_offsets[%d]" % position,
            maximum=certificate.reference_words_per_attempt,
        )
    _exact_integer(
        values["proposal_total_raw64_words"],
        name="attempt.proposal_total_raw64_words",
        maximum=certificate.reference_words_per_attempt,
    )
    _require_sha256(
        values["reserved_decision_entry_sha256"],
        name="attempt.reserved_decision_entry_sha256",
    )
    _preflight_raw_words(
        values["reserved_decision_raw64_block"],
        name="attempt.reserved_decision_raw64_block",
        maximum=1,
        length=1,
    )
    _exact_integer(
        values["reserved_decision_raw64_word"],
        name="attempt.reserved_decision_raw64_word",
    )
    _preflight_logical_word_coordinates(
        values["logical_word_coordinates"],
        name="attempt.logical_word_coordinates",
        expected_length=certificate.words_per_attempt,
    )
    _require_sha256(
        values["logical_word_coordinate_sha256"],
        name="attempt.logical_word_coordinate_sha256",
    )
    for name, maximum in (
        ("count_word_offset", certificate.reference_words_per_attempt - 1),
        ("count_raw64_word", (1 << 64) - 1),
        ("count_quota_position", certificate.manifest.total_cap),
        ("sampled_cardinality", certificate.manifest.total_cap),
    ):
        _exact_integer(values[name], name="attempt.%s" % name, maximum=maximum)
    raw_slots = _exact_tuple(
        values["proposal_raw_slots"],
        name="attempt.proposal_raw_slots",
        maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        length=certificate.manifest.total_cap,
    )
    for position, slot in enumerate(raw_slots):
        _preflight_raw_slot(
            slot,
            name="attempt.proposal_raw_slots[%d]" % position,
            manifest=certificate.manifest,
        )
    _preflight_sha256_tuple(
        values["proposal_raw_slot_sha256s"],
        name="attempt.proposal_raw_slot_sha256s",
        maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        length=certificate.manifest.total_cap,
    )
    _preflight_configuration(
        values["selected_raw_events"],
        name="attempt.selected_raw_events",
        maximum_cardinality=certificate.manifest.total_cap,
        maximum_dimension=certificate.manifest.maximum_coordinate_dimension,
    )
    _preflight_configuration(
        values["canonical_configuration"],
        name="attempt.canonical_configuration",
        maximum_cardinality=certificate.manifest.total_cap,
        maximum_dimension=certificate.manifest.maximum_coordinate_dimension,
    )
    cardinality = _exact_integer(
        values["sampled_cardinality"],
        name="attempt.sampled_cardinality",
        maximum=certificate.manifest.total_cap,
    )
    _preflight_sha256_tuple(
        values["selected_raw_event_sha256s"],
        name="attempt.selected_raw_event_sha256s",
        maximum=certificate.manifest.total_cap,
        length=cardinality,
    )
    _require_sha256(
        values["canonical_configuration_sha256"],
        name="attempt.canonical_configuration_sha256",
    )
    _preflight_index_tuple(
        values["canonical_position_to_raw_slot"],
        name="attempt.canonical_position_to_raw_slot",
        length=cardinality,
        maximum_value=max(0, certificate.manifest.total_cap - 1),
    )
    _preflight_index_tuple(
        values["raw_slot_to_canonical_position"],
        name="attempt.raw_slot_to_canonical_position",
        length=certificate.manifest.total_cap,
        maximum_value=max(0, cardinality - 1),
        optional=True,
    )
    _preflight_tilt_evaluation(values["score_evaluation"], certificate=certificate)
    _require_sha256(
        values["score_evaluation_sha256"],
        name="attempt.score_evaluation_sha256",
    )
    _exact_fraction_parts(
        values["q_numerator"], values["q_denominator"], name="attempt.q"
    )
    _exact_fraction_parts(
        values["global_upper_bound_numerator"],
        values["global_upper_bound_denominator"],
        name="attempt.global_upper_bound",
    )
    _exact_fraction_parts(
        values["q_minus_upper_bound_numerator"],
        values["q_minus_upper_bound_denominator"],
        name="attempt.q_minus_upper_bound",
    )
    for name, expected in (
        ("q_minus_upper_bound_nonpositive", True),
        ("exact_cp28_equivalent_candidate_transform", True),
        ("all_raw_slots_materialized_before_count_decode", True),
        ("duplicate_stable_canonical_bijection", True),
        ("checkpoint30_point_score_validated", True),
        ("reserved_decision_word_uninterpreted", True),
        ("acceptance_predicate_evaluated", False),
        ("acceptance_decision_made", False),
        ("exponential_or_uniform_transform_applied", False),
    ):
        _exact_bool(values[name], expected, name="attempt.%s" % name)
    _require_sha256(values["attempt_sha256"], name="attempt.attempt_sha256")
    if attempt_index >= certificate.attempt_budget:
        raise ValueError("attempt index exceeds the certified budget")


def _validate_attempt_values(
    values: Mapping[str, object],
    *,
    custody_check: object | None = None,
) -> None:
    _preflight_attempt_values(values)
    operation_snapshot = _attempt_values_operation_snapshot(values)
    raw_certificate = values["certificate"]

    def require_attempt_custody() -> None:
        _require_attempt_values_operation_unchanged(
            values,
            operation_snapshot,
            certificate=raw_certificate,
        )
        _require_callback_custody(custody_check)

    certificate = _validate_certificate(
        raw_certificate,
        custody_check=require_attempt_custody,
    )
    require_attempt_custody()
    if values["schema_version"] != (
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION
    ):
        raise ValueError("attempt schema differs")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("attempt certificate digest differs")
    attempt_index = values["attempt_index"]
    start = attempt_index * certificate.blocks_per_attempt
    stop = start + certificate.blocks_per_attempt
    if values["parent_entry_start"] != start or values["parent_entry_stop"] != stop:
        raise ValueError("attempt parent-entry range differs")
    entries = values["parent_entries"]
    if values["parent_entry_sha256s"] != tuple(entry.entry_sha256 for entry in entries):
        raise ValueError("attempt parent entry digests differ")
    expected_counts = certificate.block_raw64_word_counts
    for block, (entry, expected_count) in enumerate(zip(entries, expected_counts)):
        if (
            entry.strategy != INITIAL_TILT_REJECTION_STRATEGY
            or entry.stage_index != INITIAL_TILT_REJECTION_STAGE_INDEX
            or entry.attempt_index
            != attempt_index * certificate.blocks_per_attempt + block
            or entry.work_item_index != attempt_index
            or entry.block_index != block
            or entry.raw64_word_count != expected_count
        ):
            raise ValueError("attempt parent entry address/layout differs")
    proposal_blocks = values["proposal_raw64_blocks"]
    if any(
        block is not entry.raw64_words
        for block, entry in zip(proposal_blocks, entries[:-1])
    ):
        raise ValueError("attempt proposal block identity differs")
    decision_block = values["reserved_decision_raw64_block"]
    if decision_block is not entries[-1].raw64_words:
        raise ValueError("attempt reserved decision block identity differs")
    if values["reserved_decision_raw64_word"] != decision_block[0]:
        raise ValueError("attempt reserved decision word differs")
    if values["reserved_decision_entry_sha256"] != entries[-1].entry_sha256:
        raise ValueError("attempt reserved decision entry digest differs")
    offsets = [0]
    for block in proposal_blocks:
        offsets.append(offsets[-1] + len(block))
    if values["proposal_block_offsets"] != tuple(offsets):
        raise ValueError("attempt proposal block offsets differ")
    words = tuple(word for block in proposal_blocks for word in block)
    if values["proposal_concatenated_raw64_words"] != words:
        raise ValueError("attempt proposal concatenation differs")
    if values["proposal_total_raw64_words"] != len(words):
        raise ValueError("attempt proposal total differs")
    run_id = values["run_id"]
    initialization_index = values["initialization_index"]
    coordinates = tuple(
        (
            (run_id, INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (
                0,
                initialization_index,
                INITIAL_TILT_REJECTION_STAGE_INDEX,
                attempt_index * certificate.blocks_per_attempt + block,
            ),
            offset,
        )
        for block, count in enumerate(expected_counts)
        for offset in range(count)
    )
    if values["logical_word_coordinates"] != coordinates:
        raise ValueError("attempt logical word coordinates differ")
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("attempt logical word coordinates repeat")
    if values["logical_word_coordinate_sha256"] != _word_coordinate_digest(coordinates):
        raise ValueError("attempt logical coordinate digest differs")
    manifest = certificate.manifest
    count_word = words[manifest.count_word_offset]
    cardinality = _CP28_QUOTA_POSITION(count_word, manifest.count_cumulative_ends)
    if (
        values["count_word_offset"] != manifest.count_word_offset
        or values["count_raw64_word"] != count_word
        or values["count_quota_position"] != cardinality
        or values["sampled_cardinality"] != cardinality
    ):
        raise ValueError("attempt count transform differs")
    slots = values["proposal_raw_slots"]
    if values["proposal_raw_slot_sha256s"] != tuple(slot.slot_sha256 for slot in slots):
        raise ValueError("attempt raw-slot digest sequence differs")
    slot_snapshots = tuple(_slot_operation_snapshot(slot) for slot in slots)
    dimension_by_type = dict(manifest.type_dimensions)
    for position, slot in enumerate(slots):
        checked_slot = _CP28_VALIDATE_SLOT_RECORD(slot)
        require_attempt_custody()
        if checked_slot is not slot:
            raise ValueError("CP28 slot validation substituted its record")
        for current_position, (current, before) in enumerate(
            zip(slots, slot_snapshots)
        ):
            _require_slot_operation_unchanged(
                current,
                before,
                position=current_position,
                manifest=manifest,
            )
        if slot.raw_slot_index != position or slot.active is not (
            position < cardinality
        ):
            raise ValueError("attempt raw-slot index/activity differs")
        if slot.certificate_sha256 != certificate.checkpoint28_certificate_sha256:
            raise ValueError("attempt raw slot belongs to another CP28 certificate")
        expected_type_offset = manifest.type_segment_offset + position
        expected_type_word = words[expected_type_offset]
        expected_type_position = _CP28_QUOTA_POSITION(
            expected_type_word,
            manifest.type_cumulative_ends,
        )
        expected_event_type = manifest.type_ids[expected_type_position]
        expected_event_dimension = dimension_by_type[expected_event_type]
        expected_coordinate_offsets = tuple(
            manifest.coordinate_segment_offset
            + position * manifest.coordinate_row_stride
            + coordinate_index
            for coordinate_index in range(manifest.maximum_coordinate_dimension)
        )
        if (
            slot.type_word_offset != expected_type_offset
            or slot.type_raw64_word != expected_type_word
            or slot.type_quota_position != expected_type_position
            or slot.event_type != expected_event_type
            or slot.event_dimension != expected_event_dimension
            or slot.coordinate_word_offsets != expected_coordinate_offsets
            or slot.coordinate_raw64_words
            != tuple(words[offset] for offset in expected_coordinate_offsets)
        ):
            raise ValueError("attempt raw slot is not tied to proposal words")
    selected = tuple(slot.event for slot in slots[:cardinality])
    if len(values["selected_raw_events"]) != len(selected) or any(
        actual is not expected
        for actual, expected in zip(values["selected_raw_events"], selected)
    ):
        raise ValueError("attempt selected raw events differ")
    if values["selected_raw_event_sha256s"] != tuple(
        _CP28_EVENT_SHA256(event) for event in selected
    ):
        raise ValueError("attempt selected event digests differ")
    canonical_order = tuple(
        sorted(
            range(cardinality),
            key=lambda index: (_EVENT_MODEL_KEY(slots[index].event), index),
        )
    )
    canonical = tuple(slots[index].event for index in canonical_order)
    if len(values["canonical_configuration"]) != len(canonical) or any(
        actual is not expected
        for actual, expected in zip(values["canonical_configuration"], canonical)
    ):
        raise ValueError("attempt canonical configuration differs")
    if values["canonical_configuration_sha256"] != _CP28_CONFIGURATION_SHA256(
        canonical
    ):
        raise ValueError("attempt canonical configuration digest differs")
    if values["canonical_position_to_raw_slot"] != canonical_order:
        raise ValueError("attempt canonical-to-raw map differs")
    raw_to_canonical = [None] * manifest.total_cap
    for canonical_position, raw_position in enumerate(canonical_order):
        raw_to_canonical[raw_position] = canonical_position
    if values["raw_slot_to_canonical_position"] != tuple(raw_to_canonical):
        raise ValueError("attempt raw-to-canonical map differs")
    evaluation = values["score_evaluation"]
    if evaluation.certificate is not certificate.checkpoint30_certificate:
        raise ValueError("attempt score belongs to another CP30 certificate")
    if evaluation.configuration_sha256 != _TILT_CONFIGURATION_SHA256(canonical):
        raise ValueError("attempt score configuration digest differs")
    if tuple(_EVENT_MODEL_KEY(event) for event in evaluation.configuration) != tuple(
        _EVENT_MODEL_KEY(event) for event in canonical
    ):
        raise ValueError("attempt score configuration differs")
    if evaluation.residual_context != certificate.residual_context:
        raise ValueError("attempt score differs from the frozen context")
    if values["score_evaluation_sha256"] != evaluation.evaluation_sha256:
        raise ValueError("attempt score digest differs")
    q = Fraction(
        values["q_numerator"],
        values["q_denominator"],
    )
    expected_q = Fraction(
        evaluation.exact_initial_log_factor_numerator,
        evaluation.exact_initial_log_factor_denominator,
    )
    if q != expected_q:
        raise ValueError("attempt exact q differs from CP30")
    upper = Fraction(
        values["global_upper_bound_numerator"],
        values["global_upper_bound_denominator"],
    )
    expected_upper = Fraction(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
    )
    if upper != expected_upper:
        raise ValueError("attempt global upper bound differs")
    difference = Fraction(
        values["q_minus_upper_bound_numerator"],
        values["q_minus_upper_bound_denominator"],
    )
    if difference != q - upper or difference > 0:
        raise ValueError("attempt q-minus-upper-bound witness differs")
    for name in (
        "certificate_sha256",
        "reserved_decision_entry_sha256",
        "logical_word_coordinate_sha256",
        "canonical_configuration_sha256",
        "score_evaluation_sha256",
        "attempt_sha256",
    ):
        _require_sha256(values[name], name="attempt.%s" % name)
    if values["attempt_sha256"] != _SEMANTIC_DIGEST(_attempt_payload(values)):
        raise ValueError("attempt digest differs")
    require_attempt_custody()


def _make_attempt_values(
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
    entries: Tuple[_PROTOCOL.CounterKeyedInitializerProtocolEntry, ...],
    slots: Tuple[_CP28_RAW_SLOT_TYPE, ...],
    score: _TILT_EVALUATION_TYPE,
    *,
    run_id: int,
    initialization_index: int,
    attempt_index: int,
) -> Dict[str, object]:
    manifest = certificate.manifest
    proposal_entries = entries[:-1]
    raw_blocks = tuple(entry.raw64_words for entry in proposal_entries)
    offsets = [0]
    for block in raw_blocks:
        offsets.append(offsets[-1] + len(block))
    words = tuple(word for block in raw_blocks for word in block)
    decision_block = entries[-1].raw64_words
    cardinality = _CP28_QUOTA_POSITION(
        words[manifest.count_word_offset], manifest.count_cumulative_ends
    )
    selected = tuple(slot.event for slot in slots[:cardinality])
    canonical_order = tuple(
        sorted(
            range(cardinality),
            key=lambda index: (_EVENT_MODEL_KEY(slots[index].event), index),
        )
    )
    canonical = tuple(slots[index].event for index in canonical_order)
    raw_to_canonical = [None] * manifest.total_cap
    for canonical_position, raw_position in enumerate(canonical_order):
        raw_to_canonical[raw_position] = canonical_position
    coordinates = tuple(
        (
            (run_id, INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (
                0,
                initialization_index,
                INITIAL_TILT_REJECTION_STAGE_INDEX,
                attempt_index * certificate.blocks_per_attempt + block,
            ),
            offset,
        )
        for block, count in enumerate(certificate.block_raw64_word_counts)
        for offset in range(count)
    )
    q = Fraction(
        score.exact_initial_log_factor_numerator,
        score.exact_initial_log_factor_denominator,
    )
    upper = Fraction(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
    )
    difference = q - upper
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "attempt_index": attempt_index,
        "parent_entry_start": attempt_index * certificate.blocks_per_attempt,
        "parent_entry_stop": (attempt_index + 1) * certificate.blocks_per_attempt,
        "parent_entries": entries,
        "parent_entry_sha256s": tuple(entry.entry_sha256 for entry in entries),
        "proposal_raw64_blocks": raw_blocks,
        "proposal_block_offsets": tuple(offsets),
        "proposal_concatenated_raw64_words": words,
        "proposal_total_raw64_words": len(words),
        "reserved_decision_entry_sha256": entries[-1].entry_sha256,
        "reserved_decision_raw64_block": decision_block,
        "reserved_decision_raw64_word": decision_block[0],
        "logical_word_coordinates": coordinates,
        "logical_word_coordinate_sha256": _word_coordinate_digest(coordinates),
        "count_word_offset": manifest.count_word_offset,
        "count_raw64_word": words[manifest.count_word_offset],
        "count_quota_position": cardinality,
        "sampled_cardinality": cardinality,
        "proposal_raw_slots": slots,
        "proposal_raw_slot_sha256s": tuple(slot.slot_sha256 for slot in slots),
        "selected_raw_events": selected,
        "selected_raw_event_sha256s": tuple(
            _CP28_EVENT_SHA256(event) for event in selected
        ),
        "canonical_configuration": canonical,
        "canonical_configuration_sha256": _CP28_CONFIGURATION_SHA256(canonical),
        "canonical_position_to_raw_slot": canonical_order,
        "raw_slot_to_canonical_position": tuple(raw_to_canonical),
        "score_evaluation": score,
        "score_evaluation_sha256": score.evaluation_sha256,
        "q_numerator": q.numerator,
        "q_denominator": q.denominator,
        "global_upper_bound_numerator": upper.numerator,
        "global_upper_bound_denominator": upper.denominator,
        "q_minus_upper_bound_numerator": difference.numerator,
        "q_minus_upper_bound_denominator": difference.denominator,
        "q_minus_upper_bound_nonpositive": difference <= 0,
        "exact_cp28_equivalent_candidate_transform": True,
        "all_raw_slots_materialized_before_count_decode": True,
        "duplicate_stable_canonical_bijection": True,
        "checkpoint30_point_score_validated": True,
        "reserved_decision_word_uninterpreted": True,
        "acceptance_predicate_evaluated": False,
        "acceptance_decision_made": False,
        "exponential_or_uniform_transform_applied": False,
        "attempt_sha256": _ZERO_SHA256,
    }
    values["attempt_sha256"] = _SEMANTIC_DIGEST(_attempt_payload(values))
    return values


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_protocol_result",
        "attempts",
        "logical_word_coordinates",
        "result_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionPreparationResult:
    """One complete fixed-budget prefix with all proposal scores and no decision."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate
    certificate_sha256: str
    parent_protocol_result: _CP27_RESULT_TYPE
    parent_result_sha256: str
    run_id: int
    initialization_index: int
    attempt_budget: int
    block_raw64_word_counts: Tuple[int, ...]
    blocks_per_attempt: int
    total_stream_records: int
    total_raw64_words: int
    parent_entry_sha256s: Tuple[str, ...]
    attempts: Tuple[CounterKeyedInitialTiltRejectionAttempt, ...]
    attempt_sha256s: Tuple[str, ...]
    logical_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    logical_word_coordinate_sha256: str
    complete_fixed_prefix_materialized_before_scoring: bool
    all_attempts_materialized_and_scored_in_canonical_order: bool
    reserved_decision_words_uninterpreted: bool
    late_failure_has_no_result: bool
    retry_fallback_or_rollback_claimed: bool
    acceptance_or_selection_performed: bool
    deterministic_fixed_address_replay_only: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-preparation results cannot be subclassed")

    def __init__(
        self,
        *,
        _construction_token: object,
        _custody_check: object | None = None,
        **values: object,
    ) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("rejection-preparation results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("rejection-preparation result fields are incomplete")
        _preflight_result_values(values)
        _validate_result_values(values, custody_check=_custody_check)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-preparation results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionPreparationResult.__annotations__)


def _preflight_parent_result(result: object, *, certificate: object) -> None:
    _preflight_operation_record(
        result,
        _CP27_RESULT_TYPE,
        name="result.parent_protocol_result operation tree",
    )
    if type(result) is not _CP27_RESULT_TYPE:
        raise TypeError("parent_protocol_result has the wrong exact CP27 type")
    _preflight_preparation_certificate(certificate, name="result.certificate")
    entries = _exact_tuple(
        result.entries,
        name="parent_protocol_result.entries",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    _exact_tuple(
        result.entry_sha256s,
        name="parent_protocol_result.entry_sha256s",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    for position, entry in enumerate(entries):
        if type(entry) is not _PROTOCOL.CounterKeyedInitializerProtocolEntry:
            raise TypeError("parent entry %d has the wrong exact type" % position)
        word_count = _exact_integer(
            entry.raw64_word_count,
            name="parent_protocol_result.entries[%d].raw64_word_count" % position,
            minimum=1,
            maximum=_MAX_WORDS_PER_STREAM,
        )
        _preflight_raw_words(
            entry.raw64_words,
            name="parent_protocol_result.entries[%d].raw64_words" % position,
            maximum=_MAX_WORDS_PER_STREAM,
            length=word_count,
        )


def _preflight_result_values(values: Mapping[str, object]) -> None:
    certificate = values["certificate"]
    _preflight_preparation_certificate(certificate, name="result.certificate")
    if type(values["schema_version"]) is not str:
        raise TypeError("result.schema_version must be exact text")
    for name in (
        "certificate_sha256",
        "parent_result_sha256",
        "logical_word_coordinate_sha256",
        "result_sha256",
    ):
        _require_sha256(values[name], name="result.%s" % name)
    for name, maximum in (
        ("run_id", (1 << 64) - 1),
        ("initialization_index", (1 << 64) - 1),
        ("attempt_budget", INITIAL_TILT_REJECTION_MAX_ATTEMPTS),
        ("blocks_per_attempt", INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS),
        ("total_stream_records", INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS),
        ("total_raw64_words", INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS),
    ):
        _exact_integer(values[name], name="result.%s" % name, maximum=maximum)
    _preflight_protocol_tree(values["parent_protocol_result"], certificate=certificate)
    attempts = _exact_tuple(
        values["attempts"],
        name="result.attempts",
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
        length=certificate.attempt_budget,
    )
    for position, attempt in enumerate(attempts):
        if type(attempt) is not CounterKeyedInitialTiltRejectionAttempt:
            raise TypeError("result.attempts[%d] has the wrong exact type" % position)
        _preflight_attempt_values(
            {name: getattr(attempt, name) for name in _attempt_fields()}
        )
    _preflight_sha256_tuple(
        values["parent_entry_sha256s"],
        name="result.parent_entry_sha256s",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    _preflight_sha256_tuple(
        values["attempt_sha256s"],
        name="result.attempt_sha256s",
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
        length=certificate.attempt_budget,
    )
    _preflight_block_counts(
        values["block_raw64_word_counts"],
        name="result.block_raw64_word_counts",
        expected_length=certificate.blocks_per_attempt,
    )
    _preflight_logical_word_coordinates(
        values["logical_word_coordinates"],
        name="result.logical_word_coordinates",
        expected_length=certificate.total_raw64_words,
    )
    for name, expected in (
        ("complete_fixed_prefix_materialized_before_scoring", True),
        ("all_attempts_materialized_and_scored_in_canonical_order", True),
        ("reserved_decision_words_uninterpreted", True),
        ("late_failure_has_no_result", True),
        ("retry_fallback_or_rollback_claimed", False),
        ("acceptance_or_selection_performed", False),
        ("deterministic_fixed_address_replay_only", True),
    ):
        _exact_bool(values[name], expected, name="result.%s" % name)


def _validate_result_values(
    values: Mapping[str, object],
    *,
    custody_check: object | None = None,
) -> None:
    _preflight_result_values(values)
    raw_certificate = values["certificate"]
    attempts = values["attempts"]
    attempt_snapshots = tuple(_attempt_tree_snapshot(attempt) for attempt in attempts)
    parent = values["parent_protocol_result"]
    parent_snapshot = _protocol_tree_snapshot(parent)

    def require_result_custody() -> None:
        _require_parent_unchanged(parent, parent_snapshot)
        for position, (attempt, before) in enumerate(zip(attempts, attempt_snapshots)):
            _require_attempt_tree_unchanged(
                attempt,
                before,
                certificate=raw_certificate,
                position=position,
            )
        _require_callback_custody(custody_check)

    certificate = _validate_certificate(
        raw_certificate,
        custody_check=require_result_custody,
    )
    require_result_custody()
    if values["schema_version"] != (
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION
    ):
        raise ValueError("rejection-preparation result schema differs")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("rejection-preparation result certificate digest differs")
    checked_parent = _CP27_VALIDATE_RESULT_RECORD(parent)
    require_result_custody()
    if checked_parent is not parent:
        raise ValueError("CP27 record validation substituted its result")
    if parent.certificate is not certificate.checkpoint27_certificate:
        raise ValueError("result parent belongs to another checkpoint-27 owner")
    if values["parent_result_sha256"] != parent.result_sha256:
        raise ValueError("result parent digest differs")
    expected_request = {
        "strategy": INITIAL_TILT_REJECTION_STRATEGY,
        "strategy_budget": certificate.attempt_budget,
        "work_item_raw64_word_counts": certificate.block_raw64_word_counts,
        "selection_raw64_word_count": 0,
    }
    for name, expected in expected_request.items():
        if getattr(parent, name) != expected:
            raise ValueError("result parent request field %s differs" % name)
    expected_scalars = {
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": certificate.attempt_budget,
        "block_raw64_word_counts": certificate.block_raw64_word_counts,
        "blocks_per_attempt": certificate.blocks_per_attempt,
        "total_stream_records": certificate.total_stream_records,
        "total_raw64_words": certificate.total_raw64_words,
        "parent_entry_sha256s": parent.entry_sha256s,
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("rejection-preparation result %s differs" % name)
    if values["attempt_sha256s"] != tuple(
        attempt.attempt_sha256 for attempt in attempts
    ):
        raise ValueError("result attempt digest sequence differs")
    expected_coordinates = _instantiate_logical_word_coordinate_template(
        certificate.logical_word_coordinates,
        run_id=parent.run_id,
        initialization_index=parent.initialization_index,
    )
    attempt_coordinates = tuple(
        coordinate
        for attempt in attempts
        for coordinate in attempt.logical_word_coordinates
    )
    if attempt_coordinates != expected_coordinates:
        raise ValueError("attempt coordinates do not instantiate the template")
    if values["logical_word_coordinates"] != expected_coordinates:
        raise ValueError("result logical word coordinates differ")
    if len(set(expected_coordinates)) != len(expected_coordinates):
        raise ValueError("result logical word coordinates repeat")
    if values["logical_word_coordinate_sha256"] != _word_coordinate_digest(
        expected_coordinates
    ):
        raise ValueError("result logical coordinate digest differs")
    for position, attempt in enumerate(attempts):
        _validate_attempt_values(
            {name: getattr(attempt, name) for name in _attempt_fields()},
            custody_check=require_result_custody,
        )
        require_result_custody()
        if attempt.certificate is not certificate:
            raise ValueError("result attempt %d belongs elsewhere" % position)
        if (
            attempt.attempt_index != position
            or attempt.run_id != parent.run_id
            or attempt.initialization_index != parent.initialization_index
        ):
            raise ValueError("result attempt chronology differs")
        start = position * certificate.blocks_per_attempt
        stop = start + certificate.blocks_per_attempt
        expected_entries = parent.entries[start:stop]
        if len(attempt.parent_entries) != len(expected_entries) or any(
            actual is not expected
            for actual, expected in zip(attempt.parent_entries, expected_entries)
        ):
            raise ValueError("result attempt parent-entry identities differ")
    for name in (
        "certificate_sha256",
        "parent_result_sha256",
        "logical_word_coordinate_sha256",
        "result_sha256",
    ):
        _require_sha256(values[name], name="result.%s" % name)
    if values["result_sha256"] != _SEMANTIC_DIGEST(_result_payload(values)):
        raise ValueError("rejection-preparation result digest differs")
    require_result_custody()


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
    parent: _CP27_RESULT_TYPE,
    attempts: Tuple[CounterKeyedInitialTiltRejectionAttempt, ...],
) -> CounterKeyedInitialTiltRejectionPreparationResult:
    coordinates = _instantiate_logical_word_coordinate_template(
        certificate.logical_word_coordinates,
        run_id=parent.run_id,
        initialization_index=parent.initialization_index,
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "parent_protocol_result": parent,
        "parent_result_sha256": parent.result_sha256,
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": certificate.attempt_budget,
        "block_raw64_word_counts": certificate.block_raw64_word_counts,
        "blocks_per_attempt": certificate.blocks_per_attempt,
        "total_stream_records": certificate.total_stream_records,
        "total_raw64_words": certificate.total_raw64_words,
        "parent_entry_sha256s": parent.entry_sha256s,
        "attempts": attempts,
        "attempt_sha256s": tuple(attempt.attempt_sha256 for attempt in attempts),
        "logical_word_coordinates": coordinates,
        "logical_word_coordinate_sha256": _word_coordinate_digest(coordinates),
        "complete_fixed_prefix_materialized_before_scoring": True,
        "all_attempts_materialized_and_scored_in_canonical_order": True,
        "reserved_decision_words_uninterpreted": True,
        "late_failure_has_no_result": True,
        "retry_fallback_or_rollback_claimed": False,
        "acceptance_or_selection_performed": False,
        "deterministic_fixed_address_replay_only": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _SEMANTIC_DIGEST(_result_payload(values))
    parent_snapshot = _protocol_tree_snapshot(parent)
    attempt_snapshots = tuple(_attempt_tree_snapshot(attempt) for attempt in attempts)
    certificate_snapshot = _preparation_certificate_operation_snapshot(certificate)

    def require_creation_custody() -> None:
        _require_preparation_certificate_operation_unchanged(
            certificate, certificate_snapshot
        )
        _require_parent_unchanged(parent, parent_snapshot)
        for position, (attempt, before) in enumerate(zip(attempts, attempt_snapshots)):
            _require_attempt_tree_unchanged(
                attempt,
                before,
                certificate=certificate,
                position=position,
            )

    result = CounterKeyedInitialTiltRejectionPreparationResult(
        **values,
        _construction_token=_RESULT_TOKEN,
        _custody_check=require_creation_custody,
    )
    require_creation_custody()
    return result


def _record_snapshot(record: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return _CAPTURE_FIELDS(record, fields)


def _protocol_tree_snapshot(parent: _CP27_RESULT_TYPE) -> Tuple[object, ...]:
    _preflight_operation_record(
        parent, _CP27_RESULT_TYPE, name="checkpoint-27 tree root"
    )
    control = parent.parent_control_result
    if type(control) is not _CONTROL.CounterKeyedGlobalInitializerControlResult:
        raise TypeError("checkpoint-26 tree result has the wrong exact type")
    certificate_roots = (parent.certificate, control.certificate) + tuple(
        certificate
        for record in control.consumptions
        for certificate in (record.certificate, record.control_stream.certificate)
    )
    return (
        _record_snapshot(parent, tuple(_CP27_RESULT_TYPE.__annotations__)),
        tuple(_entry_operation_tree_snapshot(entry) for entry in parent.entries),
        _record_snapshot(control, tuple(type(control).__annotations__)),
        tuple(
            (
                _record_snapshot(record, tuple(type(record).__annotations__)),
                _record_snapshot(
                    record.control_stream,
                    tuple(type(record.control_stream).__annotations__),
                ),
                _record_snapshot(
                    record.control_stream.address,
                    tuple(type(record.control_stream.address).__annotations__),
                ),
                _record_snapshot(
                    record.control_stream.initial_state,
                    tuple(type(record.control_stream.initial_state).__annotations__),
                ),
                _record_snapshot(
                    record.stream_initial_state,
                    tuple(type(record.stream_initial_state).__annotations__),
                ),
                _record_snapshot(
                    record.stream_final_state,
                    tuple(type(record.stream_final_state).__annotations__),
                ),
            )
            for record in control.consumptions
        ),
        _parent_certificate_graph_snapshot(certificate_roots),
    )


def _preflight_protocol_tree(
    parent: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
) -> _CP27_RESULT_TYPE:
    _preflight_operation_record(
        parent, _CP27_RESULT_TYPE, name="checkpoint-27 operation tree"
    )
    _preflight_parent_result(parent, certificate=certificate)
    control = parent.parent_control_result
    if type(control) is not _CONTROL.CounterKeyedGlobalInitializerControlResult:
        raise TypeError("checkpoint-26 parent result has the wrong exact type")
    consumptions = _exact_tuple(
        control.consumptions,
        name="checkpoint-26 consumptions",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    _preflight_sha256_tuple(
        control.consumption_sha256s,
        name="checkpoint-26 consumption digests",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    entries = _exact_tuple(
        parent.entries,
        name="checkpoint-27 entries",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
        length=certificate.total_stream_records,
    )
    for position, entry in enumerate(entries):
        _preflight_operation_record(
            entry,
            _PROTOCOL.CounterKeyedInitializerProtocolEntry,
            name="checkpoint-27 entry %d transitive tree" % position,
        )
    route_type = _CONTROL._route_evidence.PhiloxRouteStateSnapshot
    for position, record in enumerate(consumptions):
        if type(record) is not _CONTROL.CounterKeyedGlobalInitializerControlConsumption:
            raise TypeError("checkpoint-26 consumption %d has wrong type" % position)
        count = _exact_integer(
            record.raw64_word_count,
            name="checkpoint-26 consumption %d word count" % position,
            minimum=1,
            maximum=_MAX_WORDS_PER_STREAM,
        )
        _preflight_raw_words(
            record.raw64_words,
            name="checkpoint-26 consumption %d words" % position,
            maximum=_MAX_WORDS_PER_STREAM,
            length=count,
        )
        stream = record.control_stream
        if type(stream) is not _CONTROL.CounterKeyedGlobalInitializerControlStream:
            raise TypeError("checkpoint-26 stream %d has wrong type" % position)
        address = stream.address
        if type(address) is not _CONTROL.CounterKeyedGlobalInitializerControlAddress:
            raise TypeError("checkpoint-26 address %d has wrong type" % position)
        for label, raw in (
            ("key", address.philox_key),
            ("counter", address.philox_counter),
        ):
            _preflight_raw_words(
                raw,
                name="checkpoint-26 address %d %s" % (position, label),
                maximum=4,
            )
        for label, state in (
            ("stream initial", stream.initial_state),
            ("record initial", record.stream_initial_state),
            ("record final", record.stream_final_state),
        ):
            if type(state) is not route_type:
                raise TypeError(
                    "checkpoint-26 %s state %d has wrong type" % (label, position)
                )
            for field in ("counter", "key", "buffer"):
                _preflight_raw_words(
                    getattr(state, field),
                    name="checkpoint-26 %s state %d %s" % (label, position, field),
                    maximum=4,
                )
    return parent


def _require_parent_unchanged(
    parent: _CP27_RESULT_TYPE,
    snapshot: Tuple[object, ...],
) -> None:
    _preflight_operation_record(
        parent, _CP27_RESULT_TYPE, name="current checkpoint-27 operation tree"
    )
    entries = _exact_tuple(
        parent.entries,
        name="checkpoint-27 result entries",
        maximum=INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS,
    )
    for position, entry in enumerate(entries):
        _preflight_operation_record(
            entry,
            _PROTOCOL.CounterKeyedInitializerProtocolEntry,
            name="checkpoint-27 entry %d operation tree" % position,
        )
        count = _exact_integer(
            entry.raw64_word_count,
            name="checkpoint-27 entries[%d].raw64_word_count" % position,
            minimum=1,
            maximum=_MAX_WORDS_PER_STREAM,
        )
        _preflight_raw_words(
            entry.raw64_words,
            name="checkpoint-27 entries[%d].raw64_words" % position,
            maximum=_MAX_WORDS_PER_STREAM,
            length=count,
        )
    if type(snapshot) is not tuple or len(snapshot) != 5:
        raise TypeError("checkpoint-27 tree snapshot is malformed")
    (
        parent_before,
        entry_befores,
        control_before,
        record_befores,
        certificate_before,
    ) = snapshot
    _REQUIRE_FIELDS_UNCHANGED(
        parent,
        tuple(_CP27_RESULT_TYPE.__annotations__),
        parent_before,
        identity_fields=(
            "certificate",
            "work_item_raw64_word_counts",
            "control_plan",
            "parent_control_result",
            "entries",
            "entry_sha256s",
        ),
        name="rejection-preparation checkpoint-27 result",
    )
    if len(entry_befores) != len(parent.entries):
        raise ValueError("checkpoint-27 entry tree length changed")
    for position, (entry, before) in enumerate(zip(parent.entries, entry_befores)):
        _require_entry_operation_tree_unchanged(
            entry,
            before,
            position=position,
        )
    control = parent.parent_control_result
    _REQUIRE_FIELDS_UNCHANGED(
        control,
        tuple(type(control).__annotations__),
        control_before,
        identity_fields=(
            "certificate",
            "control_plan",
            "consumptions",
            "consumption_sha256s",
        ),
        name="rejection-preparation checkpoint-26 result",
    )
    if len(record_befores) != len(control.consumptions):
        raise ValueError("checkpoint-26 consumption tree length changed")
    for position, (record, before_tree) in enumerate(
        zip(control.consumptions, record_befores)
    ):
        (
            record_before,
            stream_before,
            address_before,
            stream_initial_before,
            initial_before,
            final_before,
        ) = before_tree
        _REQUIRE_FIELDS_UNCHANGED(
            record,
            tuple(type(record).__annotations__),
            record_before,
            identity_fields=(
                "certificate",
                "control_stream",
                "stream_initial_state",
                "raw64_words",
                "stream_final_state",
            ),
            name="rejection-preparation checkpoint-26 consumption %d" % position,
        )
        stream = record.control_stream
        _REQUIRE_FIELDS_UNCHANGED(
            stream,
            tuple(type(stream).__annotations__),
            stream_before,
            identity_fields=("certificate", "address", "initial_state"),
            name="rejection-preparation checkpoint-26 stream %d" % position,
        )
        _REQUIRE_FIELDS_UNCHANGED(
            stream.address,
            tuple(type(stream.address).__annotations__),
            address_before,
            identity_fields=("philox_key", "philox_counter"),
            name="rejection-preparation checkpoint-26 address %d" % position,
        )
        _REQUIRE_FIELDS_UNCHANGED(
            stream.initial_state,
            tuple(type(stream.initial_state).__annotations__),
            stream_initial_before,
            identity_fields=("counter", "key", "buffer"),
            name="checkpoint-26 stream initial state %d" % position,
        )
        for label, state, state_before in (
            ("initial", record.stream_initial_state, initial_before),
            ("final", record.stream_final_state, final_before),
        ):
            _REQUIRE_FIELDS_UNCHANGED(
                state,
                tuple(type(state).__annotations__),
                state_before,
                identity_fields=("counter", "key", "buffer"),
                name="checkpoint-26 %s state %d" % (label, position),
            )
    _require_parent_certificate_graph_unchanged(certificate_before)


def _compare_record_fields(
    actual: object,
    expected: object,
    fields: Tuple[str, ...],
    *,
    identity_fields: Tuple[str, ...],
    name: str,
) -> None:
    for field in fields:
        left = getattr(actual, field)
        right = getattr(expected, field)
        if field in identity_fields:
            matches = left is right
        else:
            matches = _FIELD_MATCHES(field, left, right)
        if not matches:
            raise ValueError("%s field %s differs" % (name, field))


def _preflight_reference_structure(reference: object, *, name: str) -> None:
    reference_type = _reference.CappedPoissonConfigurationReference
    if type(reference) is not reference_type:
        raise TypeError("%s has the wrong exact reference type" % name)
    type_ids = _exact_tuple(
        reference.type_ids,
        name=name + ".type_ids",
        maximum=_reference.MAX_CONFIGURATION_EVENT_TYPES,
    )
    if not type_ids:
        raise ValueError("%s has no event types" % name)
    for position, type_id in enumerate(type_ids):
        _exact_integer(type_id, name="%s.type_ids[%d]" % (name, position))
    mapping_type = _reference.MappingProxyType
    for field, item_type in (
        ("type_dimensions", int),
        ("type_weights", float),
        ("type_intensities", float),
        ("_type_positions", int),
    ):
        mapping = getattr(reference, field)
        if type(mapping) is not mapping_type:
            raise TypeError("%s.%s has the wrong exact mapping type" % (name, field))
        if len(mapping) != len(type_ids):
            raise ValueError("%s.%s has the wrong bounded size" % (name, field))
        for position, (key, item) in enumerate(mapping.items()):
            _exact_integer(key, name="%s.%s[%d].key" % (name, field, position))
            if type(item) is not item_type:
                raise TypeError(
                    "%s.%s[%d] has the wrong type" % (name, field, position)
                )
            if item_type is int:
                _exact_integer(
                    item,
                    name="%s.%s[%d]" % (name, field, position),
                    maximum=_reference.MAX_TRANSFORMED_COORDINATE_DIMENSION,
                )
            else:
                _exact_float(item, name="%s.%s[%d]" % (name, field, position))
    _exact_float(reference.activity, name=name + ".activity")
    _exact_integer(
        reference.total_cap,
        name=name + ".total_cap",
        maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
    )
    _exact_float(reference.log_normalizer, name=name + ".log_normalizer")
    array_type = _reference.np.ndarray
    array_fields = (
        ("count_log_masses", reference.total_cap + 1, False),
        ("_count_probability_vector", reference.total_cap + 1, True),
        ("_count_sampling_cdf", reference.total_cap + 1, True),
        ("_type_weight_vector", len(type_ids), False),
        ("_type_sampling_cdf", len(type_ids), True),
    )
    for field, length, optional in array_fields:
        array = getattr(reference, field)
        if optional and array is None:
            continue
        if type(array) is not array_type:
            raise TypeError("%s.%s has the wrong exact array type" % (name, field))
        if array.ndim != 1 or array.size != length:
            raise ValueError("%s.%s has the wrong bounded shape" % (name, field))
        if array.dtype != _reference.np.dtype(_reference.np.float64):
            raise TypeError("%s.%s has the wrong array dtype" % (name, field))
        if not array.flags.c_contiguous or array.flags.owndata or array.flags.writeable:
            raise ValueError(
                "%s.%s must match the parent immutable array layout" % (name, field)
            )
        for position, item in enumerate(array):
            _exact_float(float(item), name="%s.%s[%d]" % (name, field, position))


def _preflight_manifest_structure(manifest: object, *, name: str) -> None:
    if type(manifest) is not _CP28_MANIFEST_TYPE:
        raise TypeError("%s has the wrong exact manifest type" % name)
    for field in ("schema_version", "manifest_policy", "coordinate_transform"):
        value = getattr(manifest, field)
        if (
            type(value) is not str
            or len(value) > INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH
        ):
            raise TypeError("%s.%s must be bounded exact text" % (name, field))
    _preflight_reference_structure(manifest.reference, name=name + ".reference")
    parameter_key = _exact_tuple(
        manifest.reference_parameter_key,
        name=name + ".reference_parameter_key",
        maximum=4,
        length=4,
    )
    if type(parameter_key[0]) is not str:
        raise TypeError("%s reference parameter tag must be exact text" % name)
    parameter_types = _exact_tuple(
        parameter_key[1],
        name=name + ".reference_parameter_key.types",
        maximum=_reference.MAX_CONFIGURATION_EVENT_TYPES,
    )
    for position, item in enumerate(parameter_types):
        triple = _exact_tuple(
            item,
            name="%s.reference_parameter_key.types[%d]" % (name, position),
            maximum=3,
            length=3,
        )
        _exact_integer(triple[0], name="%s.reference type id" % name)
        _exact_integer(
            triple[1],
            name="%s.reference type dimension" % name,
            maximum=_reference.MAX_TRANSFORMED_COORDINATE_DIMENSION,
        )
        _exact_float(triple[2], name="%s.reference type weight" % name)
    _exact_float(parameter_key[2], name=name + ".reference_parameter_key.activity")
    _exact_integer(
        parameter_key[3],
        name=name + ".reference_parameter_key.total_cap",
        maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
    )
    type_ids = _exact_tuple(
        manifest.type_ids,
        name=name + ".type_ids",
        maximum=_reference.MAX_CONFIGURATION_EVENT_TYPES,
    )
    for position, item in enumerate(type_ids):
        _exact_integer(item, name="%s.type_ids[%d]" % (name, position))
    dimensions = _exact_tuple(
        manifest.type_dimensions,
        name=name + ".type_dimensions",
        maximum=_reference.MAX_CONFIGURATION_EVENT_TYPES,
        length=len(type_ids),
    )
    for position, item in enumerate(dimensions):
        pair = _exact_tuple(
            item,
            name="%s.type_dimensions[%d]" % (name, position),
            maximum=2,
            length=2,
        )
        _exact_integer(pair[0], name="%s.type_dimensions[%d].type" % (name, position))
        _exact_integer(
            pair[1],
            name="%s.type_dimensions[%d].dimension" % (name, position),
            maximum=_reference.MAX_TRANSFORMED_COORDINATE_DIMENSION,
        )
    total_cap = _exact_integer(
        manifest.total_cap,
        name=name + ".total_cap",
        maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
    )
    ratio_fields = (
        ("count_target_probability_ratios", total_cap + 1),
        ("type_target_probability_ratios", len(type_ids)),
    )
    for field, maximum in ratio_fields:
        ratios = _exact_tuple(
            getattr(manifest, field),
            name="%s.%s" % (name, field),
            maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
            length=maximum,
        )
        for position, item in enumerate(ratios):
            pair = _exact_tuple(
                item,
                name="%s.%s[%d]" % (name, field, position),
                maximum=2,
                length=2,
            )
            for part, integer in enumerate(pair):
                _exact_integer(
                    integer,
                    name="%s.%s[%d][%d]" % (name, field, position, part),
                    maximum=(1 << 131071),
                )
    for field, maximum in (
        ("count_dyadic_quotas", total_cap + 1),
        ("count_cumulative_ends", total_cap + 1),
        ("type_dyadic_quotas", len(type_ids)),
        ("type_cumulative_ends", len(type_ids)),
    ):
        items = _exact_tuple(
            getattr(manifest, field),
            name="%s.%s" % (name, field),
            maximum=_reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
            length=maximum,
        )
        for position, item in enumerate(items):
            _exact_integer(
                item,
                name="%s.%s[%d]" % (name, field, position),
                maximum=(1 << 64),
            )
    _exact_float(manifest.activity, name=name + ".activity")
    for field in (
        "maximum_coordinate_dimension",
        "raw_word_bits",
        "coordinate_bucket_bits",
        "coordinate_ignored_low_bits",
        "count_word_offset",
        "type_segment_offset",
        "coordinate_segment_offset",
        "coordinate_row_stride",
        "required_raw64_words",
        "count_quantization_tv_numerator",
        "count_quantization_tv_denominator",
        "type_quantization_tv_numerator",
        "type_quantization_tv_denominator",
    ):
        _exact_integer(
            getattr(manifest, field),
            name="%s.%s" % (name, field),
            maximum=(1 << 131071),
        )
    blocks = _exact_tuple(
        manifest.canonical_block_raw64_word_counts,
        name=name + ".canonical_block_raw64_word_counts",
        maximum=16,
    )
    for position, block in enumerate(blocks):
        _exact_integer(
            block,
            name="%s.canonical_block_raw64_word_counts[%d]" % (name, position),
            maximum=_MAX_WORDS_PER_STREAM,
        )
    for field in (
        "reference_parameter_sha256",
        "manifest_runtime_sha256",
        "manifest_sha256",
    ):
        _require_sha256(getattr(manifest, field), name="%s.%s" % (name, field))


def _reference_operation_snapshot(reference: object) -> Tuple[object, ...]:
    _preflight_reference_structure(reference, name="manifest.reference")
    fields = tuple(type(reference).__annotations__)
    mapping_fields = (
        "type_dimensions",
        "type_weights",
        "type_intensities",
        "_type_positions",
    )
    array_fields = (
        "count_log_masses",
        "_count_probability_vector",
        "_count_sampling_cdf",
        "_type_weight_vector",
        "_type_sampling_cdf",
    )
    arrays = []
    for field in array_fields:
        array = getattr(reference, field)
        arrays.append(
            None
            if array is None
            else (
                tuple(array.shape),
                array.dtype.str,
                tuple(array.strides),
                bool(array.flags.c_contiguous),
                bool(array.flags.owndata),
                bool(array.flags.writeable),
                array.tobytes(order="C"),
            )
        )
    return (
        _record_snapshot(reference, fields),
        tuple(
            (field, tuple(getattr(reference, field).items()))
            for field in mapping_fields
        ),
        tuple(zip(array_fields, arrays)),
    )


def _require_reference_operation_unchanged(
    reference: object,
    snapshot: Tuple[object, ...],
) -> None:
    _preflight_reference_structure(reference, name="current manifest.reference")
    if type(snapshot) is not tuple or len(snapshot) != 3:
        raise TypeError("reference operation snapshot is malformed")
    before, mapping_befores, array_befores = snapshot
    _require_record_snapshot_unchanged(
        reference,
        tuple(type(reference).__annotations__),
        before,
        name="rejection-preparation manifest reference",
    )
    for field, expected_items in mapping_befores:
        current_items = tuple(getattr(reference, field).items())
        if len(current_items) != len(expected_items):
            raise ValueError("manifest reference mapping %s changed" % field)
        for position, ((key, item), (before_key, before_item)) in enumerate(
            zip(current_items, expected_items)
        ):
            if type(key) is not type(before_key) or key != before_key:
                raise ValueError(
                    "manifest reference mapping %s key %d changed" % (field, position)
                )
            if type(item) is float:
                matches = type(before_item) is float and _SAME_FLOAT(item, before_item)
            else:
                matches = type(item) is type(before_item) and item == before_item
            if not matches:
                raise ValueError(
                    "manifest reference mapping %s item %d changed" % (field, position)
                )
    for field, expected_array in array_befores:
        current = getattr(reference, field)
        if expected_array is None:
            if current is not None:
                raise ValueError("manifest reference array %s changed" % field)
            continue
        (
            expected_shape,
            expected_dtype,
            expected_strides,
            expected_c_contiguous,
            expected_owndata,
            expected_writeable,
            expected_bytes,
        ) = expected_array
        if current is None or (
            tuple(current.shape) != expected_shape
            or current.dtype.str != expected_dtype
            or tuple(current.strides) != expected_strides
            or bool(current.flags.c_contiguous) is not expected_c_contiguous
            or bool(current.flags.owndata) is not expected_owndata
            or bool(current.flags.writeable) is not expected_writeable
            or current.tobytes(order="C") != expected_bytes
        ):
            raise ValueError("manifest reference array %s changed" % field)


def _manifest_operation_snapshot(manifest: object) -> Tuple[object, ...]:
    _preflight_manifest_structure(manifest, name="manifest")
    return (
        _record_snapshot(manifest, tuple(_CP28_MANIFEST_TYPE.__annotations__)),
        _reference_operation_snapshot(manifest.reference),
    )


def _require_manifest_operation_unchanged(
    manifest: object,
    snapshot: Tuple[object, ...],
) -> None:
    _preflight_manifest_structure(manifest, name="current manifest")
    if type(snapshot) is not tuple or len(snapshot) != 2:
        raise TypeError("manifest operation snapshot is malformed")
    before, reference_before = snapshot
    _require_record_snapshot_unchanged(
        manifest,
        tuple(_CP28_MANIFEST_TYPE.__annotations__),
        before,
        name="rejection-preparation manifest",
    )
    _require_reference_operation_unchanged(manifest.reference, reference_before)


def _hypothesis_operation_snapshot(hypothesis: object) -> Tuple[object, ...]:
    _preflight_word_family_hypothesis(hypothesis)
    return (
        _record_snapshot(hypothesis, _hypothesis_fields()),
        _parent_certificate_graph_snapshot(
            (hypothesis.reference_initializer_certificate,)
        ),
        _manifest_operation_snapshot(hypothesis.manifest),
    )


def _require_hypothesis_operation_unchanged(
    hypothesis: object,
    snapshot: Tuple[object, ...],
) -> None:
    _preflight_word_family_hypothesis(hypothesis)
    if type(snapshot) is not tuple or len(snapshot) != 3:
        raise TypeError("hypothesis operation snapshot is malformed")
    before, parent_graph, manifest_before = snapshot
    _require_record_snapshot_unchanged(
        hypothesis,
        _hypothesis_fields(),
        before,
        name="rejection-preparation word-family hypothesis",
    )
    _require_parent_certificate_graph_unchanged(parent_graph)
    _require_manifest_operation_unchanged(hypothesis.manifest, manifest_before)


def _certificate_values_dependency_snapshot(
    values: Mapping[str, object],
) -> Tuple[object, ...]:
    parent_graph = _parent_certificate_graph_snapshot(
        (
            values["checkpoint28_certificate"],
            values["checkpoint27_certificate"],
            values["checkpoint30_certificate"],
        )
    )
    return (
        parent_graph,
        _manifest_operation_snapshot(values["manifest"]),
        _hypothesis_operation_snapshot(values["word_family_hypothesis"]),
    )


def _require_certificate_values_dependencies_unchanged(
    values: Mapping[str, object],
    snapshot: Tuple[object, ...],
) -> None:
    if type(snapshot) is not tuple or len(snapshot) != 3:
        raise TypeError("certificate dependency snapshot is malformed")
    parent_graph, manifest_before, hypothesis_before = snapshot
    _require_parent_certificate_graph_unchanged(parent_graph)
    _require_manifest_operation_unchanged(values["manifest"], manifest_before)
    _require_hypothesis_operation_unchanged(
        values["word_family_hypothesis"], hypothesis_before
    )


def _snapshot_identity_fields(
    fields: Tuple[str, ...], snapshot: Tuple[object, ...]
) -> Tuple[str, ...]:
    if type(snapshot) is not tuple or len(snapshot) != len(fields):
        raise TypeError("record snapshot is malformed")
    return tuple(
        field
        for field, before in zip(fields, snapshot)
        if type(before) not in (str, int, bool, float)
    )


def _require_record_snapshot_unchanged(
    record: object,
    fields: Tuple[str, ...],
    snapshot: Tuple[object, ...],
    *,
    name: str,
) -> None:
    _REQUIRE_FIELDS_UNCHANGED(
        record,
        fields,
        snapshot,
        identity_fields=_snapshot_identity_fields(fields, snapshot),
        name=name,
    )


def _parent_certificate_graph_snapshot(
    roots: Tuple[object, ...],
) -> Tuple[Tuple[object, ...], ...]:
    pending = list(roots)
    seen = set()
    manifest_snapshots = {}
    snapshot = []
    while pending:
        record = pending.pop()
        record_type = type(record)
        if record_type not in _PARENT_CERTIFICATE_SCHEMA_BY_TYPE:
            raise TypeError("parent certificate graph has an unknown record type")
        if id(record) in seen:
            continue
        seen.add(id(record))
        fields, _ = _PARENT_CERTIFICATE_SCHEMA_BY_TYPE[record_type]
        _preflight_certificate_record(
            record,
            record_type,
            name="attempt certificate parent graph",
        )
        before = _record_snapshot(record, fields)
        manifest = None
        manifest_before = None
        if record_type is _CP28_CERT_TYPE:
            manifest = record.manifest
            manifest_identity = id(manifest)
            if manifest_identity in manifest_snapshots:
                saved_manifest, manifest_before = manifest_snapshots[manifest_identity]
                if manifest is not saved_manifest:
                    raise ValueError("parent graph manifest identity collision")
            else:
                _preflight_manifest_structure(
                    manifest,
                    name="attempt certificate parent graph manifest",
                )
                manifest_before = _manifest_operation_snapshot(manifest)
                manifest_snapshots[manifest_identity] = (manifest, manifest_before)
        snapshot.append(
            (record_type, record, fields, before, manifest, manifest_before)
        )
        for field in fields:
            child = getattr(record, field)
            if type(child) in _PARENT_CERTIFICATE_SCHEMA_BY_TYPE:
                pending.append(child)
    return tuple(snapshot)


def _require_parent_certificate_graph_unchanged(
    snapshot: Tuple[Tuple[object, ...], ...]
) -> None:
    if type(snapshot) is not tuple or len(snapshot) > 128:
        raise TypeError("parent certificate graph snapshot is malformed")
    for position, item in enumerate(snapshot):
        if type(item) is not tuple or len(item) != 6:
            raise TypeError("parent certificate graph snapshot is malformed")
        record_type, record, fields, before, manifest, manifest_before = item
        if type(record_type) is not type or type(record) is not record_type:
            raise TypeError("parent certificate graph record changed type")
        _preflight_certificate_record(
            record,
            record_type,
            name="current attempt certificate parent graph[%d]" % position,
        )
        _require_record_snapshot_unchanged(
            record,
            fields,
            before,
            name="attempt parent certificate graph record %d" % position,
        )
        if record_type is _CP28_CERT_TYPE:
            if record.manifest is not manifest:
                raise ValueError("checkpoint-28 certificate manifest identity changed")
            _require_manifest_operation_unchanged(manifest, manifest_before)
        elif manifest is not None or manifest_before is not None:
            raise TypeError("non-CP28 parent graph has manifest custody")


def _preparation_certificate_operation_snapshot(
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
) -> Tuple[object, ...]:
    _preflight_preparation_certificate(certificate, name="attempt.certificate")
    fields = _certificate_fields()
    return (
        _record_snapshot(certificate, fields),
        _parent_certificate_graph_snapshot(
            (
                certificate.checkpoint28_certificate,
                certificate.checkpoint27_certificate,
                certificate.checkpoint30_certificate,
            )
        ),
        _manifest_operation_snapshot(certificate.manifest),
        _hypothesis_operation_snapshot(certificate.word_family_hypothesis),
    )


def _require_preparation_certificate_operation_unchanged(
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
    snapshot: Tuple[object, ...],
) -> None:
    _preflight_preparation_certificate(certificate, name="current attempt.certificate")
    if type(snapshot) is not tuple or len(snapshot) != 4:
        raise TypeError("preparation certificate snapshot is malformed")
    before, parent_graph, manifest_before, hypothesis_before = snapshot
    fields = _certificate_fields()
    _require_record_snapshot_unchanged(
        certificate,
        fields,
        before,
        name="rejection-preparation attempt certificate",
    )
    _require_parent_certificate_graph_unchanged(parent_graph)
    _require_manifest_operation_unchanged(certificate.manifest, manifest_before)
    _require_hypothesis_operation_unchanged(
        certificate.word_family_hypothesis,
        hypothesis_before,
    )


def _entry_operation_tree_snapshot(
    entry: _PROTOCOL.CounterKeyedInitializerProtocolEntry,
) -> Tuple[object, ...]:
    _preflight_operation_record(
        entry,
        _PROTOCOL.CounterKeyedInitializerProtocolEntry,
        name="attempt parent-entry operation tree",
    )
    record = entry.parent_consumption
    stream = record.control_stream
    address = stream.address
    return (
        _record_snapshot(entry, tuple(type(entry).__annotations__)),
        _record_snapshot(record, tuple(type(record).__annotations__)),
        _record_snapshot(stream, tuple(type(stream).__annotations__)),
        _record_snapshot(address, tuple(type(address).__annotations__)),
        _record_snapshot(
            stream.initial_state,
            tuple(type(stream.initial_state).__annotations__),
        ),
        _record_snapshot(
            record.stream_initial_state,
            tuple(type(record.stream_initial_state).__annotations__),
        ),
        _record_snapshot(
            record.stream_final_state,
            tuple(type(record.stream_final_state).__annotations__),
        ),
        _parent_certificate_graph_snapshot((record.certificate, stream.certificate)),
    )


def _require_entry_operation_tree_unchanged(
    entry: _PROTOCOL.CounterKeyedInitializerProtocolEntry,
    snapshot: Tuple[object, ...],
    *,
    position: int,
) -> None:
    _preflight_operation_record(
        entry,
        _PROTOCOL.CounterKeyedInitializerProtocolEntry,
        name="current attempt parent-entry operation tree",
    )
    if type(snapshot) is not tuple or len(snapshot) != 8:
        raise TypeError("attempt parent-entry tree snapshot is malformed")
    record = entry.parent_consumption
    stream = record.control_stream
    records = (
        (entry, snapshot[0], "entry"),
        (record, snapshot[1], "consumption"),
        (stream, snapshot[2], "stream"),
        (stream.address, snapshot[3], "address"),
        (stream.initial_state, snapshot[4], "stream initial state"),
        (record.stream_initial_state, snapshot[5], "record initial state"),
        (record.stream_final_state, snapshot[6], "record final state"),
    )
    for current, before, label in records:
        _require_record_snapshot_unchanged(
            current,
            tuple(type(current).__annotations__),
            before,
            name="attempt parent entry %d %s" % (position, label),
        )
    _require_parent_certificate_graph_unchanged(snapshot[7])


def _slot_operation_snapshot(slot: _CP28_RAW_SLOT_TYPE) -> Tuple[object, ...]:
    return (
        _record_snapshot(slot, tuple(_CP28_RAW_SLOT_TYPE.__annotations__)),
        _record_snapshot(slot.event, tuple(TransformedEvent.__annotations__)),
    )


def _require_slot_operation_unchanged(
    slot: _CP28_RAW_SLOT_TYPE,
    snapshot: Tuple[object, ...],
    *,
    position: int,
    manifest: _CP28_MANIFEST_TYPE,
) -> None:
    _preflight_raw_slot(
        slot,
        name="current raw slot %d" % position,
        manifest=manifest,
    )
    slot_before, event_before = snapshot
    _REQUIRE_FIELDS_UNCHANGED(
        slot,
        tuple(_CP28_RAW_SLOT_TYPE.__annotations__),
        slot_before,
        identity_fields=(
            "coordinate_word_offsets",
            "coordinate_raw64_words",
            "coordinate_bucket_indices",
            "coordinate_midpoint_numerators",
            "coordinate_probability_hexes",
            "coordinate_codebook_values",
            "coordinate_value_hexes",
            "active_coordinates",
            "event",
        ),
        name="rejection-preparation raw slot %d" % position,
    )
    _REQUIRE_FIELDS_UNCHANGED(
        slot.event,
        tuple(TransformedEvent.__annotations__),
        event_before,
        identity_fields=("coordinates",),
        name="rejection-preparation raw-slot event %d" % position,
    )


def _score_operation_snapshot(score: _TILT_EVALUATION_TYPE) -> Tuple[object, ...]:
    return (
        _record_snapshot(score, tuple(_TILT_EVALUATION_TYPE.__annotations__)),
        tuple(
            _record_snapshot(event, tuple(TransformedEvent.__annotations__))
            for event in score.configuration
        ),
        _parent_certificate_graph_snapshot((score.certificate,)),
    )


def _require_score_operation_unchanged(
    score: _TILT_EVALUATION_TYPE,
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
) -> None:
    _preflight_tilt_evaluation(score, certificate=certificate)
    if type(snapshot) is not tuple or len(snapshot) != 3:
        raise TypeError("CP30 score operation snapshot is malformed")
    score_before, event_befores, certificate_before = snapshot
    _REQUIRE_FIELDS_UNCHANGED(
        score,
        tuple(_TILT_EVALUATION_TYPE.__annotations__),
        score_before,
        identity_fields=("certificate", "configuration", "residual_context"),
        name="rejection-preparation CP30 score",
    )
    if len(event_befores) != len(score.configuration):
        raise ValueError("CP30 score configuration length changed")
    for position, (event, before) in enumerate(zip(score.configuration, event_befores)):
        _REQUIRE_FIELDS_UNCHANGED(
            event,
            tuple(TransformedEvent.__annotations__),
            before,
            identity_fields=("coordinates",),
            name="rejection-preparation score event %d" % position,
        )
    _require_parent_certificate_graph_unchanged(certificate_before)


def _attempt_values_operation_snapshot(
    values: Mapping[str, object],
) -> Tuple[object, ...]:
    _preflight_attempt_values(values)
    certificate = values["certificate"]
    entries = values["parent_entries"]
    slots = values["proposal_raw_slots"]
    score = values["score_evaluation"]
    return (
        tuple((name, values[name]) for name in _attempt_fields()),
        _preparation_certificate_operation_snapshot(certificate),
        tuple(_entry_operation_tree_snapshot(entry) for entry in entries),
        tuple(_slot_operation_snapshot(slot) for slot in slots),
        tuple(
            _record_snapshot(event, tuple(TransformedEvent.__annotations__))
            for event in values["selected_raw_events"]
        ),
        tuple(
            _record_snapshot(event, tuple(TransformedEvent.__annotations__))
            for event in values["canonical_configuration"]
        ),
        _score_operation_snapshot(score),
    )


def _require_attempt_values_operation_unchanged(
    values: Mapping[str, object],
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
) -> None:
    _preflight_attempt_values(values)
    if type(snapshot) is not tuple or len(snapshot) != 7:
        raise TypeError("attempt-values operation snapshot is malformed")
    (
        fields_before,
        certificate_before,
        entry_befores,
        slot_befores,
        selected_befores,
        canonical_befores,
        score_before,
    ) = snapshot
    if type(fields_before) is not tuple or len(fields_before) != len(_attempt_fields()):
        raise TypeError("attempt-values field snapshot is malformed")
    for expected_name, before in fields_before:
        if type(expected_name) is not str or expected_name not in values:
            raise TypeError("attempt-values field snapshot is malformed")
        current = values[expected_name]
        if type(before) not in (str, int, bool, float):
            if current is not before:
                raise ValueError(
                    "attempt-values field %s identity changed" % expected_name
                )
        elif type(current) is not type(before) or not _FIELD_MATCHES(
            expected_name, current, before
        ):
            raise ValueError("attempt-values field %s changed" % expected_name)
    if values["certificate"] is not certificate:
        raise ValueError("attempt-values certificate identity changed")
    _require_preparation_certificate_operation_unchanged(
        certificate,
        certificate_before,
    )
    entries = values["parent_entries"]
    if type(entry_befores) is not tuple or len(entries) != len(entry_befores):
        raise ValueError("attempt-values parent-entry count changed")
    for position, (entry, before) in enumerate(zip(entries, entry_befores)):
        _require_entry_operation_tree_unchanged(
            entry,
            before,
            position=position,
        )
    slots = values["proposal_raw_slots"]
    if type(slot_befores) is not tuple or len(slots) != len(slot_befores):
        raise ValueError("attempt-values raw-slot count changed")
    for position, (slot, before) in enumerate(zip(slots, slot_befores)):
        _require_slot_operation_unchanged(
            slot,
            before,
            position=position,
            manifest=certificate.manifest,
        )
    for label, current_events, event_befores in (
        ("selected", values["selected_raw_events"], selected_befores),
        ("canonical", values["canonical_configuration"], canonical_befores),
    ):
        if len(current_events) != len(event_befores):
            raise ValueError("attempt-values %s event count changed" % label)
        for position, (event, before) in enumerate(zip(current_events, event_befores)):
            _require_record_snapshot_unchanged(
                event,
                tuple(TransformedEvent.__annotations__),
                before,
                name="attempt-values %s event %d" % (label, position),
            )
    _require_score_operation_unchanged(
        values["score_evaluation"],
        score_before,
        certificate=certificate,
    )


def _attempt_tree_snapshot(
    attempt: CounterKeyedInitialTiltRejectionAttempt,
) -> Tuple[object, ...]:
    return (
        _record_snapshot(attempt, _attempt_fields()),
        tuple(
            _entry_operation_tree_snapshot(entry) for entry in attempt.parent_entries
        ),
        tuple(_slot_operation_snapshot(slot) for slot in attempt.proposal_raw_slots),
        tuple(
            _record_snapshot(event, tuple(TransformedEvent.__annotations__))
            for event in attempt.selected_raw_events
        ),
        tuple(
            _record_snapshot(event, tuple(TransformedEvent.__annotations__))
            for event in attempt.canonical_configuration
        ),
        _score_operation_snapshot(attempt.score_evaluation),
    )


def _require_attempt_tree_unchanged(
    attempt: CounterKeyedInitialTiltRejectionAttempt,
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
    position: int,
) -> None:
    _preflight_attempt_values(
        {name: getattr(attempt, name) for name in _attempt_fields()}
    )
    if type(snapshot) is not tuple or len(snapshot) != 6:
        raise TypeError("rejection-preparation attempt-tree snapshot is malformed")
    (
        attempt_before,
        entry_befores,
        slot_befores,
        selected_befores,
        canonical_befores,
        score_before,
    ) = snapshot
    _REQUIRE_FIELDS_UNCHANGED(
        attempt,
        _attempt_fields(),
        attempt_before,
        identity_fields=(
            "certificate",
            "parent_entries",
            "parent_entry_sha256s",
            "proposal_raw64_blocks",
            "proposal_block_offsets",
            "proposal_concatenated_raw64_words",
            "reserved_decision_raw64_block",
            "logical_word_coordinates",
            "proposal_raw_slots",
            "proposal_raw_slot_sha256s",
            "selected_raw_events",
            "selected_raw_event_sha256s",
            "canonical_configuration",
            "canonical_position_to_raw_slot",
            "raw_slot_to_canonical_position",
            "score_evaluation",
        ),
        name="rejection-preparation attempt %d" % position,
    )
    if len(entry_befores) != len(attempt.parent_entries):
        raise ValueError("rejection-preparation attempt parent-entry count changed")
    for entry_position, (entry, before) in enumerate(
        zip(attempt.parent_entries, entry_befores)
    ):
        _require_entry_operation_tree_unchanged(
            entry,
            before,
            position=entry_position,
        )
    if len(slot_befores) != len(attempt.proposal_raw_slots):
        raise ValueError("rejection-preparation attempt slot count changed")
    for slot_position, (slot, before) in enumerate(
        zip(attempt.proposal_raw_slots, slot_befores)
    ):
        _require_slot_operation_unchanged(
            slot,
            before,
            position=slot_position,
            manifest=certificate.manifest,
        )
    for label, current_events, event_befores in (
        ("selected", attempt.selected_raw_events, selected_befores),
        ("canonical", attempt.canonical_configuration, canonical_befores),
    ):
        if len(current_events) != len(event_befores):
            raise ValueError("rejection-preparation %s event count changed" % label)
        for event_position, (event, before) in enumerate(
            zip(current_events, event_befores)
        ):
            _require_record_snapshot_unchanged(
                event,
                tuple(TransformedEvent.__annotations__),
                before,
                name="attempt %d %s event %d" % (position, label, event_position),
            )
    _require_score_operation_unchanged(
        attempt.score_evaluation,
        score_before,
        certificate=certificate,
    )


def _result_tree_snapshot(
    result: CounterKeyedInitialTiltRejectionPreparationResult,
) -> Tuple[object, ...]:
    return (
        _record_snapshot(result, _result_fields()),
        _protocol_tree_snapshot(result.parent_protocol_result),
        tuple(_attempt_tree_snapshot(attempt) for attempt in result.attempts),
    )


def _require_result_tree_unchanged(
    result: CounterKeyedInitialTiltRejectionPreparationResult,
    snapshot: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
) -> None:
    _preflight_result_values({name: getattr(result, name) for name in _result_fields()})
    if type(snapshot) is not tuple or len(snapshot) != 3:
        raise TypeError("rejection-preparation result-tree snapshot is malformed")
    result_before, parent_before, attempt_befores = snapshot
    _REQUIRE_FIELDS_UNCHANGED(
        result,
        _result_fields(),
        result_before,
        identity_fields=(
            "certificate",
            "parent_protocol_result",
            "block_raw64_word_counts",
            "parent_entry_sha256s",
            "attempts",
            "attempt_sha256s",
            "logical_word_coordinates",
        ),
        name="rejection-preparation result",
    )
    _require_parent_unchanged(result.parent_protocol_result, parent_before)
    if len(attempt_befores) != len(result.attempts):
        raise ValueError("rejection-preparation result attempt count changed")
    for position, (attempt, before) in enumerate(zip(result.attempts, attempt_befores)):
        _require_attempt_tree_unchanged(
            attempt,
            before,
            certificate=certificate,
            position=position,
        )


class CounterKeyedInitialTiltRejectionPreparationOwner:
    """Immutable owner of one fixed rejection-attempt preparation pipeline."""

    __slots__ = (
        "_reference_initializer_owner",
        "_reference_initializer_owner_identity",
        "_initial_tilt_composer",
        "_initial_tilt_composer_identity",
        "_protocol_owner",
        "_protocol_owner_identity",
        "_reference_composer",
        "_reference_composer_identity",
        "_process",
        "_process_identity",
        "_manifest",
        "_manifest_identity",
        "_residual_context",
        "_residual_context_identity",
        "_attempt_budget",
        "_attempt_budget_identity",
        "_preparation_policy",
        "_preparation_policy_identity",
        "_preparation_role_sha256",
        "_preparation_role_sha256_identity",
        "_word_family_hypothesis",
        "_word_family_hypothesis_identity",
        "_certificate",
        "_certificate_identity",
        "_hypothesis_snapshot",
        "_hypothesis_snapshot_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_protocol_allocate",
        "_protocol_validate_result",
        "_slot_materializer",
        "_slot_maker",
        "_tilt_evaluate",
        "_tilt_validate_evaluation",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedInitialTiltRejectionPreparationOwner cannot subclass"
        )

    def __init__(
        self,
        reference_initializer_owner: _CP28_TYPE,
        initial_tilt_composer: _TILT_TYPE,
        protocol_owner: _CP27_TYPE,
        reference_composer: _COMPOSER_TYPE,
        process: object,
        manifest: _CP28_MANIFEST_TYPE,
        residual_context: Tuple[float, ...],
        attempt_budget: int,
        preparation_policy: str,
        preparation_role_sha256: str,
        word_family_hypothesis: InitialTiltRejectionPreparationWordFamilyHypothesis,
        certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("rejection-preparation owners require certification")
        if type(reference_initializer_owner) is not _CP28_TYPE:
            raise TypeError("reference initializer owner has the wrong exact type")
        if type(initial_tilt_composer) is not _TILT_TYPE:
            raise TypeError("initial tilt composer has the wrong exact type")
        if type(protocol_owner) is not _CP27_TYPE:
            raise TypeError("protocol owner has the wrong exact type")
        if type(reference_composer) is not _COMPOSER_TYPE:
            raise TypeError("reference composer has the wrong exact type")
        _preflight_preparation_certificate(
            certificate, name="owner construction certificate"
        )
        if manifest is not certificate.manifest:
            raise ValueError("owner manifest identity differs from its certificate")
        if word_family_hypothesis is not certificate.word_family_hypothesis:
            raise ValueError("owner hypothesis identity differs from its certificate")
        if protocol_owner.certificate is not certificate.checkpoint27_certificate:
            raise ValueError("owner protocol identity differs from its certificate")
        persistent_snapshot = _preparation_certificate_operation_snapshot(certificate)

        def require_persistent_custody() -> None:
            _require_preparation_certificate_operation_unchanged(
                certificate, persistent_snapshot
            )

        checked_manifest = _CP28_VALIDATE_MANIFEST(manifest)
        require_persistent_custody()
        if checked_manifest is not manifest:
            raise ValueError("owner manifest validation substituted its record")
        canonical_context = _canonical_context(
            initial_tilt_composer,
            residual_context,
            custody_certificate=certificate,
            custody_snapshot=persistent_snapshot,
        )
        require_persistent_custody()
        if canonical_context != residual_context:
            raise ValueError("residual context is not canonical")
        context = residual_context
        checked_attempts = _exact_integer(
            attempt_budget,
            name="attempt_budget",
            minimum=1,
            maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
        )
        policy = _require_text(
            preparation_policy,
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY,
            name="preparation_policy",
        )
        role = _require_sha256(preparation_role_sha256, name="preparation_role_sha256")
        hypothesis = _validate_hypothesis(
            word_family_hypothesis,
            custody_check=require_persistent_custody,
        )
        require_persistent_custody()
        checked_certificate = _validate_certificate(
            certificate,
            custody_check=require_persistent_custody,
        )
        require_persistent_custody()
        hypothesis_snapshot = tuple(
            getattr(hypothesis, name) for name in _hypothesis_fields()
        )
        certificate_snapshot = tuple(
            getattr(checked_certificate, name) for name in _certificate_fields()
        )
        bindings = (
            ("_reference_initializer_owner", reference_initializer_owner),
            ("_reference_initializer_owner_identity", reference_initializer_owner),
            ("_initial_tilt_composer", initial_tilt_composer),
            ("_initial_tilt_composer_identity", initial_tilt_composer),
            ("_protocol_owner", protocol_owner),
            ("_protocol_owner_identity", protocol_owner),
            ("_reference_composer", reference_composer),
            ("_reference_composer_identity", reference_composer),
            ("_process", process),
            ("_process_identity", process),
            ("_manifest", checked_manifest),
            ("_manifest_identity", checked_manifest),
            ("_residual_context", context),
            ("_residual_context_identity", context),
            ("_attempt_budget", checked_attempts),
            ("_attempt_budget_identity", checked_attempts),
            ("_preparation_policy", policy),
            ("_preparation_policy_identity", policy),
            ("_preparation_role_sha256", role),
            ("_preparation_role_sha256_identity", role),
            ("_word_family_hypothesis", hypothesis),
            ("_word_family_hypothesis_identity", hypothesis),
            ("_certificate", checked_certificate),
            ("_certificate_identity", checked_certificate),
            ("_hypothesis_snapshot", hypothesis_snapshot),
            ("_hypothesis_snapshot_identity", hypothesis_snapshot),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_protocol_allocate", _CP27_ALLOCATE),
            ("_protocol_validate_result", _CP27_VALIDATE_RESULT),
            ("_slot_materializer", _CP28_MATERIALIZE_SLOT_FIELDS),
            ("_slot_maker", _CP28_MAKE_SLOT),
            ("_tilt_evaluate", _TILT_EVALUATE),
            ("_tilt_validate_evaluation", _TILT_VALIDATE_EVALUATION),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("rejection-preparation owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("rejection-preparation owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-preparation owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedInitialTiltRejectionPreparationCertificate:
        return self._certificate

    @property
    def reference_initializer_owner(self) -> _CP28_TYPE:
        return self._reference_initializer_owner

    @property
    def initial_tilt_composer(self) -> _TILT_TYPE:
        return self._initial_tilt_composer

    @property
    def word_family_hypothesis(
        self,
    ) -> InitialTiltRejectionPreparationWordFamilyHypothesis:
        return self._word_family_hypothesis

    def _owner_snapshot(self) -> Tuple[object, ...]:
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("rejection-preparation owner seal differs")
        current = (
            self._reference_initializer_owner,
            self._initial_tilt_composer,
            self._protocol_owner,
            self._reference_composer,
            self._process,
            self._manifest,
            self._residual_context,
            self._attempt_budget,
            self._preparation_policy,
            self._preparation_role_sha256,
            self._word_family_hypothesis,
            self._certificate,
        )
        frozen = (
            self._reference_initializer_owner_identity,
            self._initial_tilt_composer_identity,
            self._protocol_owner_identity,
            self._reference_composer_identity,
            self._process_identity,
            self._manifest_identity,
            self._residual_context_identity,
            self._attempt_budget_identity,
            self._preparation_policy_identity,
            self._preparation_role_sha256_identity,
            self._word_family_hypothesis_identity,
            self._certificate_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("rejection-preparation owner identity changed")
        callbacks = (
            (self._protocol_allocate, _CP27_ALLOCATE),
            (self._protocol_validate_result, _CP27_VALIDATE_RESULT),
            (self._slot_materializer, _CP28_MATERIALIZE_SLOT_FIELDS),
            (self._slot_maker, _CP28_MAKE_SLOT),
            (self._tilt_evaluate, _TILT_EVALUATE),
            (self._tilt_validate_evaluation, _TILT_VALIDATE_EVALUATION),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("rejection-preparation cached callback changed")
        return current

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 12:
            raise TypeError("rejection-preparation owner snapshot is malformed")
        current = self._owner_snapshot()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise PluginBridgeCounterKeyedInitialTiltRejectionPreparationError(
                "rejection-preparation owner changed during operation"
            )

    def _require_persistent_records(
        self, *, custody_check: object | None = None
    ) -> None:
        owner_snapshot = self._owner_snapshot()
        persistent_snapshot = _preparation_certificate_operation_snapshot(
            self._certificate
        )

        def require_persistent_custody() -> None:
            _require_preparation_certificate_operation_unchanged(
                self._certificate, persistent_snapshot
            )
            self._require_owner_snapshot(owner_snapshot)
            _require_callback_custody(custody_check)

        hypothesis = _validate_hypothesis(
            self._word_family_hypothesis,
            custody_check=require_persistent_custody,
        )
        require_persistent_custody()
        if tuple(getattr(hypothesis, name) for name in _hypothesis_fields()) != (
            self._hypothesis_snapshot
        ):
            raise ValueError("rejection-preparation hypothesis changed")
        certificate = _validate_certificate(
            self._certificate,
            custody_check=require_persistent_custody,
        )
        require_persistent_custody()
        if tuple(getattr(certificate, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("rejection-preparation certificate changed")

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
        *,
        custody_check: object | None = None,
    ) -> CounterKeyedInitialTiltRejectionPreparationCertificate:
        persistent_snapshot = _preparation_certificate_operation_snapshot(
            owner_snapshot[11]
        )

        def require_live_custody() -> None:
            _require_preparation_certificate_operation_unchanged(
                owner_snapshot[11], persistent_snapshot
            )
            self._require_owner_snapshot(owner_snapshot)
            _require_callback_custody(custody_check)

        self._require_owner_snapshot(owner_snapshot)
        self._require_persistent_records(custody_check=custody_check)
        require_live_custody()
        _require_parent_surfaces()
        parent28 = _CP28_LIVE(owner_snapshot[0])
        require_live_custody()
        if parent28 is not owner_snapshot[11].checkpoint28_certificate:
            raise ValueError("rejection-preparation CP28 certificate identity changed")
        parent27 = _CP27_LIVE(owner_snapshot[2])
        require_live_custody()
        if parent27 is not owner_snapshot[11].checkpoint27_certificate:
            raise ValueError("rejection-preparation CP27 certificate identity changed")
        tilt_snapshot = _TILT_OWNER_SNAPSHOT(owner_snapshot[1])
        require_live_custody()
        _TILT_LIVE_COMPONENTS(owner_snapshot[1], tilt_snapshot)
        require_live_custody()
        if tilt_snapshot[3] is not owner_snapshot[11].checkpoint30_certificate:
            raise ValueError("rejection-preparation CP30 certificate identity changed")
        composer, process, _ = _REFERENCE_ANCESTRY(owner_snapshot[2])
        require_live_custody()
        if composer is not owner_snapshot[3]:
            raise ValueError("rejection-preparation CP28 composer ancestry changed")
        if process is not owner_snapshot[4]:
            raise ValueError("rejection-preparation CP28 process ancestry changed")
        tilt_composer = _TILT_REFERENCE_COMPOSER_PROPERTY.__get__(
            owner_snapshot[1], _TILT_TYPE
        )
        require_live_custody()
        if tilt_composer is not composer:
            raise ValueError("CP28 and CP30 reference composer identities differ")
        if tilt_composer.process is not process:
            raise ValueError("CP28 and CP30 process identities differ")
        require_live_custody()
        live_manifest = _CP28_MANIFEST_PROPERTY.__get__(owner_snapshot[0], _CP28_TYPE)
        require_live_custody()
        if live_manifest is not owner_snapshot[5]:
            raise ValueError("rejection-preparation manifest identity changed")
        expected = _make_certificate(
            owner_snapshot[0],
            owner_snapshot[1],
            owner_snapshot[6],
            owner_snapshot[7],
            owner_snapshot[9],
            owner_snapshot[10],
            custody_check=require_live_custody,
        )
        require_live_custody()
        _compare_record_fields(
            owner_snapshot[11],
            expected,
            _certificate_fields(),
            identity_fields=(
                "checkpoint28_certificate",
                "checkpoint27_certificate",
                "checkpoint30_certificate",
                "manifest",
                "word_family_hypothesis",
                "residual_context",
                "logical_word_coordinates",
            ),
            name="rejection-preparation certificate",
        )
        self._require_persistent_records(custody_check=custody_check)
        require_live_custody()
        return owner_snapshot[11]

    def _require_dependency_return(
        self,
        snapshot: Tuple[object, ...],
        *,
        custody_check: object | None = None,
    ) -> None:
        if (
            self._live_certificate(snapshot, custody_check=custody_check)
            is not snapshot[11]
        ):
            raise ValueError("rejection-preparation certificate identity changed")

    def _materialize_attempt(
        self,
        owner_snapshot: Tuple[object, ...],
        parent: _CP27_RESULT_TYPE,
        parent_snapshot: Tuple[object, ...],
        completed_attempts: Tuple[CounterKeyedInitialTiltRejectionAttempt, ...],
        completed_attempt_snapshots: Tuple[Tuple[object, ...], ...],
        *,
        run_id: int,
        initialization_index: int,
        attempt_index: int,
    ) -> CounterKeyedInitialTiltRejectionAttempt:
        certificate = owner_snapshot[11]
        owner_persistent_snapshot = _preparation_certificate_operation_snapshot(
            certificate
        )
        _require_parent_unchanged(parent, parent_snapshot)
        self._require_completed_attempts_unchanged(
            completed_attempts,
            completed_attempt_snapshots,
            certificate=certificate,
        )
        start = attempt_index * certificate.blocks_per_attempt
        stop = start + certificate.blocks_per_attempt
        entries = parent.entries[start:stop]
        words = tuple(word for entry in entries[:-1] for word in entry.raw64_words)
        materialized = []
        materialized_snapshots = []
        slots = []
        slot_snapshots = []
        persistent_snapshot = owner_persistent_snapshot

        def require_retained_custody() -> None:
            _require_preparation_certificate_operation_unchanged(
                certificate, persistent_snapshot
            )
            _require_parent_unchanged(parent, parent_snapshot)
            self._require_completed_attempts_unchanged(
                completed_attempts,
                completed_attempt_snapshots,
                certificate=certificate,
            )
            for position, (prior_fields, fields_before) in enumerate(
                zip(materialized, materialized_snapshots)
            ):
                _require_materialized_slot_fields_unchanged(
                    prior_fields,
                    fields_before,
                    manifest=certificate.manifest,
                    words=words,
                    raw_slot_index=position,
                )
            for position, (prior_slot, slot_before) in enumerate(
                zip(slots, slot_snapshots)
            ):
                _require_slot_operation_unchanged(
                    prior_slot,
                    slot_before,
                    position=position,
                    manifest=certificate.manifest,
                )

        for raw_slot_index in range(certificate.manifest.total_cap):
            fields = self._slot_materializer(
                certificate.manifest,
                words,
                raw_slot_index=raw_slot_index,
            )
            checked_fields = _preflight_materialized_slot_fields(
                fields,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=raw_slot_index,
            )
            fields_snapshot = _materialized_slot_fields_snapshot(checked_fields)
            require_retained_custody()
            _require_materialized_slot_fields_unchanged(
                checked_fields,
                fields_snapshot,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=raw_slot_index,
            )
            self._require_dependency_return(
                owner_snapshot,
                custody_check=require_retained_custody,
            )
            _require_parent_unchanged(parent, parent_snapshot)
            self._require_completed_attempts_unchanged(
                completed_attempts,
                completed_attempt_snapshots,
                certificate=certificate,
            )
            for position, (prior, before) in enumerate(
                zip(materialized, materialized_snapshots)
            ):
                _require_materialized_slot_fields_unchanged(
                    prior,
                    before,
                    manifest=certificate.manifest,
                    words=words,
                    raw_slot_index=position,
                )
            _require_materialized_slot_fields_unchanged(
                checked_fields,
                fields_snapshot,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=raw_slot_index,
            )
            materialized.append(checked_fields)
            materialized_snapshots.append(
                _materialized_slot_fields_snapshot(checked_fields)
            )
        cardinality = _CP28_QUOTA_POSITION(
            words[certificate.manifest.count_word_offset],
            certificate.manifest.count_cumulative_ends,
        )
        for raw_slot_index, fields in enumerate(materialized):
            slot = self._slot_maker(
                certificate.checkpoint28_certificate,
                certificate.manifest,
                fields,
                active=raw_slot_index < cardinality,
            )
            _preflight_raw_slot(
                slot,
                name="fresh materialized slot %d" % raw_slot_index,
                manifest=certificate.manifest,
            )
            fresh_slot_snapshot = _slot_operation_snapshot(slot)
            require_retained_custody()
            _require_slot_operation_unchanged(
                slot,
                fresh_slot_snapshot,
                position=raw_slot_index,
                manifest=certificate.manifest,
            )
            self._require_dependency_return(
                owner_snapshot,
                custody_check=require_retained_custody,
            )
            _require_parent_unchanged(parent, parent_snapshot)
            self._require_completed_attempts_unchanged(
                completed_attempts,
                completed_attempt_snapshots,
                certificate=certificate,
            )
            for position, (prior_fields, fields_before) in enumerate(
                zip(materialized, materialized_snapshots)
            ):
                _require_materialized_slot_fields_unchanged(
                    prior_fields,
                    fields_before,
                    manifest=certificate.manifest,
                    words=words,
                    raw_slot_index=position,
                )
            for position, (prior, before) in enumerate(zip(slots, slot_snapshots)):
                _require_slot_operation_unchanged(
                    prior,
                    before,
                    position=position,
                    manifest=certificate.manifest,
                )
            _require_slot_operation_unchanged(
                slot,
                fresh_slot_snapshot,
                position=raw_slot_index,
                manifest=certificate.manifest,
            )
            _preflight_raw_slot(
                slot,
                name="materialized slot %d" % raw_slot_index,
                manifest=certificate.manifest,
            )
            slot_snapshot = _slot_operation_snapshot(slot)
            checked_slot = _CP28_VALIDATE_SLOT_RECORD(slot)
            require_retained_custody()
            _require_slot_operation_unchanged(
                slot,
                slot_snapshot,
                position=raw_slot_index,
                manifest=certificate.manifest,
            )
            self._require_dependency_return(
                owner_snapshot,
                custody_check=require_retained_custody,
            )
            _require_parent_unchanged(parent, parent_snapshot)
            self._require_completed_attempts_unchanged(
                completed_attempts,
                completed_attempt_snapshots,
                certificate=certificate,
            )
            for position, (prior_fields, fields_before) in enumerate(
                zip(materialized, materialized_snapshots)
            ):
                _require_materialized_slot_fields_unchanged(
                    prior_fields,
                    fields_before,
                    manifest=certificate.manifest,
                    words=words,
                    raw_slot_index=position,
                )
            if checked_slot is not slot:
                raise ValueError("CP28 slot validation substituted its record")
            _require_slot_operation_unchanged(
                slot,
                slot_snapshot,
                position=raw_slot_index,
                manifest=certificate.manifest,
            )
            for position, (prior, before) in enumerate(zip(slots, slot_snapshots)):
                _require_slot_operation_unchanged(
                    prior,
                    before,
                    position=position,
                    manifest=certificate.manifest,
                )
            slots.append(slot)
            slot_snapshots.append(_slot_operation_snapshot(slot))
        canonical_order = tuple(
            sorted(
                range(cardinality),
                key=lambda index: (_EVENT_MODEL_KEY(slots[index].event), index),
            )
        )
        canonical = tuple(slots[index].event for index in canonical_order)
        score = self._tilt_evaluate(
            owner_snapshot[1],
            canonical,
            residual_context=owner_snapshot[6],
        )
        _preflight_tilt_evaluation(score, certificate=certificate)
        fresh_score_snapshot = _score_operation_snapshot(score)
        require_retained_custody()
        _require_score_operation_unchanged(
            score,
            fresh_score_snapshot,
            certificate=certificate,
        )
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_retained_custody,
        )
        _require_parent_unchanged(parent, parent_snapshot)
        self._require_completed_attempts_unchanged(
            completed_attempts,
            completed_attempt_snapshots,
            certificate=certificate,
        )
        for position, (prior_fields, fields_before) in enumerate(
            zip(materialized, materialized_snapshots)
        ):
            _require_materialized_slot_fields_unchanged(
                prior_fields,
                fields_before,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=position,
            )
        for position, (slot, before) in enumerate(zip(slots, slot_snapshots)):
            _require_slot_operation_unchanged(
                slot,
                before,
                position=position,
                manifest=certificate.manifest,
            )
        _require_score_operation_unchanged(
            score,
            fresh_score_snapshot,
            certificate=certificate,
        )
        score_snapshot = fresh_score_snapshot
        checked_score = self._tilt_validate_evaluation(
            owner_snapshot[1],
            score,
            canonical,
            residual_context=owner_snapshot[6],
        )
        require_retained_custody()
        _require_score_operation_unchanged(
            score,
            score_snapshot,
            certificate=certificate,
        )
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_retained_custody,
        )
        _require_parent_unchanged(parent, parent_snapshot)
        self._require_completed_attempts_unchanged(
            completed_attempts,
            completed_attempt_snapshots,
            certificate=certificate,
        )
        for position, (prior_fields, fields_before) in enumerate(
            zip(materialized, materialized_snapshots)
        ):
            _require_materialized_slot_fields_unchanged(
                prior_fields,
                fields_before,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=position,
            )
        for position, (slot, before) in enumerate(zip(slots, slot_snapshots)):
            _require_slot_operation_unchanged(
                slot,
                before,
                position=position,
                manifest=certificate.manifest,
            )
        _require_score_operation_unchanged(
            score,
            score_snapshot,
            certificate=certificate,
        )
        if checked_score is not score:
            raise ValueError("CP30 validation substituted its score record")
        values = _make_attempt_values(
            certificate,
            entries,
            tuple(slots),
            score,
            run_id=run_id,
            initialization_index=initialization_index,
            attempt_index=attempt_index,
        )
        attempt = CounterKeyedInitialTiltRejectionAttempt(
            **values, _construction_token=_ATTEMPT_TOKEN
        )
        attempt_snapshot = _attempt_tree_snapshot(attempt)
        _validate_attempt_values(
            {name: getattr(attempt, name) for name in _attempt_fields()},
            custody_check=require_retained_custody,
        )

        def require_attempt_custody() -> None:
            require_retained_custody()
            _require_attempt_tree_unchanged(
                attempt,
                attempt_snapshot,
                certificate=certificate,
                position=attempt_index,
            )

        require_attempt_custody()
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_attempt_custody,
        )
        _require_parent_unchanged(parent, parent_snapshot)
        self._require_completed_attempts_unchanged(
            completed_attempts,
            completed_attempt_snapshots,
            certificate=certificate,
        )
        for position, (prior_fields, fields_before) in enumerate(
            zip(materialized, materialized_snapshots)
        ):
            _require_materialized_slot_fields_unchanged(
                prior_fields,
                fields_before,
                manifest=certificate.manifest,
                words=words,
                raw_slot_index=position,
            )
        _require_attempt_tree_unchanged(
            attempt,
            attempt_snapshot,
            certificate=certificate,
            position=attempt_index,
        )
        return attempt

    @staticmethod
    def _require_completed_attempts_unchanged(
        attempts: Tuple[CounterKeyedInitialTiltRejectionAttempt, ...],
        snapshots: Tuple[Tuple[object, ...], ...],
        *,
        certificate: CounterKeyedInitialTiltRejectionPreparationCertificate,
    ) -> None:
        if len(attempts) != len(snapshots):
            raise ValueError("completed-attempt custody length changed")
        for position, (attempt, snapshot) in enumerate(zip(attempts, snapshots)):
            _require_attempt_tree_unchanged(
                attempt,
                snapshot,
                certificate=certificate,
                position=position,
            )

    def prepare(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionPreparationResult:
        """Materialize and score every fixed attempt; make no decision."""

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        persistent_snapshot = _preparation_certificate_operation_snapshot(certificate)
        parent = self._protocol_allocate(
            owner_snapshot[2],
            checked_run,
            checked_initialization,
            strategy=INITIAL_TILT_REJECTION_STRATEGY,
            strategy_budget=certificate.attempt_budget,
            work_item_raw64_word_counts=certificate.block_raw64_word_counts,
            selection_raw64_word_count=0,
        )
        _preflight_protocol_tree(parent, certificate=certificate)
        parent_snapshot = _protocol_tree_snapshot(parent)

        def require_parent_custody() -> None:
            _require_parent_unchanged(parent, parent_snapshot)
            _require_preparation_certificate_operation_unchanged(
                certificate, persistent_snapshot
            )
            self._require_owner_snapshot(owner_snapshot)

        require_parent_custody()
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_parent_custody,
        )
        require_parent_custody()
        checked_parent = self._protocol_validate_result(
            owner_snapshot[2],
            parent,
            checked_run,
            checked_initialization,
            strategy=INITIAL_TILT_REJECTION_STRATEGY,
            strategy_budget=certificate.attempt_budget,
            work_item_raw64_word_counts=certificate.block_raw64_word_counts,
            selection_raw64_word_count=0,
        )
        require_parent_custody()
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_parent_custody,
        )
        if checked_parent is not parent:
            raise ValueError("checkpoint-27 validation substituted its result")
        _require_parent_unchanged(parent, parent_snapshot)
        attempts = []
        attempt_snapshots = []
        for attempt_index in range(certificate.attempt_budget):
            attempt = self._materialize_attempt(
                owner_snapshot,
                parent,
                parent_snapshot,
                tuple(attempts),
                tuple(attempt_snapshots),
                run_id=checked_run,
                initialization_index=checked_initialization,
                attempt_index=attempt_index,
            )
            self._require_completed_attempts_unchanged(
                tuple(attempts),
                tuple(attempt_snapshots),
                certificate=certificate,
            )
            attempts.append(attempt)
            attempt_snapshots.append(_attempt_tree_snapshot(attempt))
        result = _make_result(certificate, parent, tuple(attempts))
        result_snapshot = _result_tree_snapshot(result)
        checked = self._validate_result_operation(
            result, checked_run, checked_initialization
        )
        if checked is not result:
            raise ValueError("rejection-preparation validation substituted its result")
        _require_result_tree_unchanged(
            result,
            result_snapshot,
            certificate=certificate,
        )

        def require_result_custody() -> None:
            require_parent_custody()
            _require_result_tree_unchanged(
                result,
                result_snapshot,
                certificate=certificate,
            )

        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_result_custody,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionPreparationResult:
        """Replay CP27 and CP30 only; never allocate or invoke CP28 initialize."""

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        return self._validate_result_operation(
            result, checked_run, checked_initialization
        )

    def _validate_result_operation(
        self,
        result: object,
        checked_run: int,
        checked_initialization: int,
    ) -> CounterKeyedInitialTiltRejectionPreparationResult:
        if type(result) is not CounterKeyedInitialTiltRejectionPreparationResult:
            raise TypeError("result has the wrong exact rejection-preparation type")
        values = {name: getattr(result, name) for name in _result_fields()}
        _preflight_result_values(values)
        result_snapshot = _result_tree_snapshot(result)
        owner_snapshot = self._owner_snapshot()
        trusted_certificate = owner_snapshot[11]
        if values["certificate"] is not trusted_certificate:
            raise ValueError("result belongs to another rejection-preparation owner")
        parent = values["parent_protocol_result"]
        if parent.certificate is not trusted_certificate.checkpoint27_certificate:
            raise ValueError("result parent belongs to another checkpoint-27 owner")
        trusted_control_certificate = (
            trusted_certificate.checkpoint27_certificate.checkpoint26_certificate
        )
        if parent.parent_control_result.certificate is not trusted_control_certificate:
            raise ValueError("result control parent belongs to another owner")
        for position, record in enumerate(parent.parent_control_result.consumptions):
            if record.certificate is not trusted_control_certificate or (
                record.control_stream.certificate is not trusted_control_certificate
            ):
                raise ValueError(
                    "result control consumption %d belongs to another owner" % position
                )
        for position, entry in enumerate(parent.entries):
            record = entry.parent_consumption
            if record.certificate is not trusted_control_certificate or (
                record.control_stream.certificate is not trusted_control_certificate
            ):
                raise ValueError(
                    "result parent entry %d has another control certificate" % position
                )
        for position, attempt in enumerate(values["attempts"]):
            if attempt.certificate is not trusted_certificate:
                raise ValueError("result attempt %d belongs elsewhere" % position)
            if (
                attempt.score_evaluation.certificate
                is not trusted_certificate.checkpoint30_certificate
            ):
                raise ValueError("result attempt %d score belongs elsewhere" % position)

        def require_result_custody() -> None:
            _require_result_tree_unchanged(
                result,
                result_snapshot,
                certificate=trusted_certificate,
            )

        certificate = self._live_certificate(
            owner_snapshot,
            custody_check=require_result_custody,
        )
        require_result_custody()
        if result.certificate is not certificate:
            raise ValueError("result belongs to another rejection-preparation owner")
        if result.run_id != checked_run or (
            result.initialization_index != checked_initialization
        ):
            raise ValueError("result request coordinates differ")
        _validate_result_values(
            values,
            custody_check=require_result_custody,
        )
        require_result_custody()
        parent = result.parent_protocol_result
        _preflight_protocol_tree(parent, certificate=certificate)
        parent_snapshot = _protocol_tree_snapshot(parent)
        persistent_snapshot = _preparation_certificate_operation_snapshot(certificate)

        def require_replay_custody() -> None:
            require_result_custody()
            _require_parent_unchanged(parent, parent_snapshot)
            _require_preparation_certificate_operation_unchanged(
                certificate, persistent_snapshot
            )
            self._require_owner_snapshot(owner_snapshot)

        checked_parent = self._protocol_validate_result(
            owner_snapshot[2],
            parent,
            checked_run,
            checked_initialization,
            strategy=INITIAL_TILT_REJECTION_STRATEGY,
            strategy_budget=certificate.attempt_budget,
            work_item_raw64_word_counts=certificate.block_raw64_word_counts,
            selection_raw64_word_count=0,
        )
        require_replay_custody()
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_replay_custody,
        )
        if checked_parent is not parent:
            raise ValueError("checkpoint-27 validation substituted its result")
        _require_parent_unchanged(parent, parent_snapshot)
        _require_result_tree_unchanged(
            result,
            result_snapshot,
            certificate=certificate,
        )
        for attempt in result.attempts:
            _preflight_tilt_evaluation(
                attempt.score_evaluation, certificate=certificate
            )
            checked_score = self._tilt_validate_evaluation(
                owner_snapshot[1],
                attempt.score_evaluation,
                attempt.canonical_configuration,
                residual_context=owner_snapshot[6],
            )
            require_replay_custody()
            self._require_dependency_return(
                owner_snapshot,
                custody_check=require_replay_custody,
            )
            if checked_score is not attempt.score_evaluation:
                raise ValueError("checkpoint-30 validation substituted its score")
            _require_parent_unchanged(parent, parent_snapshot)
            _require_result_tree_unchanged(
                result,
                result_snapshot,
                certificate=certificate,
            )
        _validate_result_values(
            {name: getattr(result, name) for name in _result_fields()},
            custody_check=require_replay_custody,
        )
        self._require_dependency_return(
            owner_snapshot,
            custody_check=require_replay_custody,
        )
        require_replay_custody()
        self._require_owner_snapshot(owner_snapshot)
        return result


def _direct_ancestry(
    reference_initializer_owner: object,
    initial_tilt_composer: object,
    *,
    custody_check: object | None = None,
) -> Tuple[_CP27_TYPE, _COMPOSER_TYPE, object, _CP28_MANIFEST_TYPE]:
    if type(reference_initializer_owner) is not _CP28_TYPE:
        raise TypeError("reference_initializer_owner has the wrong exact CP28 type")
    if type(initial_tilt_composer) is not _TILT_TYPE:
        raise TypeError("initial_tilt_composer has the wrong exact CP30 type")
    parent28 = _CP28_CERTIFICATE_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    parent30 = _TILT_CERTIFICATE_PROPERTY.__get__(initial_tilt_composer, _TILT_TYPE)
    _preflight_certificate_record(
        parent28,
        _CP28_CERT_TYPE,
        name="reference_initializer_owner.certificate",
    )
    _preflight_certificate_record(
        parent30,
        _TILT_CERT_TYPE,
        name="initial_tilt_composer.certificate",
    )
    dependency_snapshot = _parent_certificate_graph_snapshot((parent28, parent30))

    def require_dependencies() -> None:
        _require_parent_certificate_graph_unchanged(dependency_snapshot)
        _require_callback_custody(custody_check)

    live28 = _CP28_LIVE(reference_initializer_owner)
    require_dependencies()
    if live28 is not parent28:
        raise ValueError("checkpoint-28 live binding substituted its certificate")
    protocol_owner = _CP28_PROTOCOL_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    require_dependencies()
    live27 = _CP27_LIVE(protocol_owner)
    require_dependencies()
    if live27 is not parent28.checkpoint27_certificate:
        raise ValueError("checkpoint-27 live binding substituted its certificate")
    tilt_snapshot = _TILT_OWNER_SNAPSHOT(initial_tilt_composer)
    require_dependencies()
    _TILT_LIVE_COMPONENTS(initial_tilt_composer, tilt_snapshot)
    require_dependencies()
    composer, process, _ = _REFERENCE_ANCESTRY(protocol_owner)
    require_dependencies()
    tilt_composer = _TILT_REFERENCE_COMPOSER_PROPERTY.__get__(
        initial_tilt_composer, _TILT_TYPE
    )
    require_dependencies()
    if tilt_composer is not composer:
        raise ValueError("checkpoint-28 and checkpoint-30 composers differ")
    if tilt_composer.process is not process:
        raise ValueError("checkpoint-28 and checkpoint-30 process ancestry differs")
    manifest = _CP28_MANIFEST_PROPERTY.__get__(reference_initializer_owner, _CP28_TYPE)
    require_dependencies()
    _preflight_manifest_structure(manifest, name="direct ancestry manifest")
    manifest_snapshot = _manifest_operation_snapshot(manifest)
    checked_manifest = _CP28_VALIDATE_MANIFEST(manifest)
    require_dependencies()
    _require_manifest_operation_unchanged(manifest, manifest_snapshot)
    if checked_manifest is not manifest:
        raise ValueError("checkpoint-28 manifest validation substituted its record")
    return protocol_owner, composer, process, manifest


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation(
    reference_initializer_owner: object,
    initial_tilt_composer: object,
    *,
    residual_context: object,
    attempt_budget: object,
    preparation_policy: object,
    preparation_role_sha256: object,
    word_family_hypothesis: object,
) -> CounterKeyedInitialTiltRejectionPreparationOwner:
    """Certify fixed-budget candidate transformation and CP30 scoring only."""

    checked_attempts = _exact_integer(
        attempt_budget,
        name="attempt_budget",
        minimum=INITIAL_TILT_REJECTION_MIN_ATTEMPTS,
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
    )
    if type(residual_context) is not tuple:
        raise TypeError("residual_context must be an exact tuple at certification")
    if len(residual_context) > INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION:
        raise ValueError("residual_context exceeds the frozen dimension bound")
    for position, item in enumerate(residual_context):
        _exact_float(item, name="residual_context[%d]" % position)
    if type(reference_initializer_owner) is not _CP28_TYPE:
        raise TypeError("reference_initializer_owner has the wrong exact CP28 type")
    if type(initial_tilt_composer) is not _TILT_TYPE:
        raise TypeError("initial_tilt_composer has the wrong exact CP30 type")
    manifest = _CP28_MANIFEST_PROPERTY.__get__(reference_initializer_owner, _CP28_TYPE)
    parent28 = _CP28_CERTIFICATE_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    parent30 = _TILT_CERTIFICATE_PROPERTY.__get__(initial_tilt_composer, _TILT_TYPE)
    _preflight_manifest_structure(manifest, name="certification.manifest")
    _preflight_certificate_record(
        parent28,
        _CP28_CERT_TYPE,
        name="certification.checkpoint28_certificate",
    )
    _preflight_certificate_record(
        parent30,
        _TILT_CERT_TYPE,
        name="certification.checkpoint30_certificate",
    )
    _preflight_word_family_hypothesis(word_family_hypothesis)
    parent_snapshot = _parent_certificate_graph_snapshot((parent28, parent30))
    manifest_snapshot = _manifest_operation_snapshot(manifest)
    hypothesis_snapshot = _hypothesis_operation_snapshot(word_family_hypothesis)

    def require_certification_custody() -> None:
        _require_parent_certificate_graph_unchanged(parent_snapshot)
        _require_manifest_operation_unchanged(manifest, manifest_snapshot)
        _require_hypothesis_operation_unchanged(
            word_family_hypothesis, hypothesis_snapshot
        )

    _attempt_layout(manifest, checked_attempts)
    require_certification_custody()
    policy = _require_text(
        preparation_policy,
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY,
        name="preparation_policy",
    )
    role = _require_sha256(preparation_role_sha256, name="preparation_role_sha256")
    ancestry = _direct_ancestry(
        reference_initializer_owner,
        initial_tilt_composer,
        custody_check=require_certification_custody,
    )
    require_certification_custody()
    context = _canonical_context(
        initial_tilt_composer,
        residual_context,
        dependency_guard=require_certification_custody,
    )
    require_certification_custody()
    attempt_count, _, _, _, _ = _attempt_layout(ancestry[3], checked_attempts)
    require_certification_custody()
    hypothesis = _validate_hypothesis(
        word_family_hypothesis,
        custody_check=require_certification_custody,
    )
    require_certification_custody()
    parent_certificate = _CP28_CERTIFICATE_PROPERTY.__get__(
        reference_initializer_owner, _CP28_TYPE
    )
    require_certification_custody()
    if hypothesis.reference_initializer_certificate is not parent_certificate:
        raise ValueError("word-family hypothesis belongs to another CP28 certificate")
    if hypothesis.reference_initializer_owner_runtime_identity != id(
        reference_initializer_owner
    ):
        raise ValueError("word-family hypothesis belongs to another CP28 owner")
    if hypothesis.manifest is not ancestry[3]:
        raise ValueError("word-family hypothesis belongs to another manifest")
    if hypothesis.attempt_budget != attempt_count:
        raise ValueError("word-family hypothesis uses another attempt budget")
    certificate = _make_certificate(
        reference_initializer_owner,
        initial_tilt_composer,
        context,
        attempt_count,
        role,
        hypothesis,
        custody_check=require_certification_custody,
    )
    require_certification_custody()
    owner = CounterKeyedInitialTiltRejectionPreparationOwner(
        reference_initializer_owner,
        initial_tilt_composer,
        ancestry[0],
        ancestry[1],
        ancestry[2],
        ancestry[3],
        context,
        attempt_count,
        policy,
        role,
        hypothesis,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    require_certification_custody()
    snapshot = owner._owner_snapshot()
    owner._live_certificate(snapshot)
    owner._require_owner_snapshot(snapshot)
    return owner


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation(
    reference_initializer_owner: object,
    initial_tilt_composer: object,
    owner: object,
    *,
    residual_context: object,
    attempt_budget: object,
    preparation_policy: object,
    preparation_role_sha256: object,
    word_family_hypothesis: object,
) -> CounterKeyedInitialTiltRejectionPreparationOwner:
    """Require exact parents, frozen inputs, role, policy, and live custody."""

    if type(owner) is not CounterKeyedInitialTiltRejectionPreparationOwner:
        raise TypeError("owner has the wrong exact rejection-preparation type")
    if type(reference_initializer_owner) is not _CP28_TYPE:
        raise TypeError("reference_initializer_owner has the wrong exact CP28 type")
    if type(initial_tilt_composer) is not _TILT_TYPE:
        raise TypeError("initial_tilt_composer has the wrong exact CP30 type")
    context_input = _exact_tuple(
        residual_context,
        name="residual_context",
        maximum=INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION,
    )
    for position, item in enumerate(context_input):
        _exact_float(item, name="residual_context[%d]" % position)
    _exact_integer(
        attempt_budget,
        name="attempt_budget",
        minimum=INITIAL_TILT_REJECTION_MIN_ATTEMPTS,
        maximum=INITIAL_TILT_REJECTION_MAX_ATTEMPTS,
    )
    _preflight_word_family_hypothesis(word_family_hypothesis)
    snapshot = owner._owner_snapshot()
    persistent_snapshot = _preparation_certificate_operation_snapshot(snapshot[11])
    hypothesis_snapshot = _hypothesis_operation_snapshot(word_family_hypothesis)

    def require_matching_custody() -> None:
        _require_preparation_certificate_operation_unchanged(
            snapshot[11], persistent_snapshot
        )
        _require_hypothesis_operation_unchanged(
            word_family_hypothesis, hypothesis_snapshot
        )
        owner._require_owner_snapshot(snapshot)

    policy = _require_text(
        preparation_policy,
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY,
        name="preparation_policy",
    )
    role = _require_sha256(preparation_role_sha256, name="preparation_role_sha256")
    hypothesis = _validate_hypothesis(
        word_family_hypothesis,
        custody_check=require_matching_custody,
    )
    require_matching_custody()
    if owner.reference_initializer_owner is not reference_initializer_owner:
        raise ValueError("owner uses another checkpoint-28 owner")
    if owner.initial_tilt_composer is not initial_tilt_composer:
        raise ValueError("owner uses another checkpoint-30 composer")
    if owner.word_family_hypothesis is not hypothesis:
        raise ValueError("owner uses another word-family hypothesis")
    context = _canonical_context(
        initial_tilt_composer,
        context_input,
        custody_certificate=snapshot[11],
        custody_snapshot=persistent_snapshot,
        dependency_guard=require_matching_custody,
    )
    require_matching_custody()
    attempt_count, _, _, _, _ = _attempt_layout(owner._manifest, attempt_budget)
    require_matching_custody()
    certificate = owner._live_certificate(
        snapshot,
        custody_check=require_matching_custody,
    )
    if context != owner._residual_context:
        raise ValueError("owner uses another residual context")
    if attempt_count != owner._attempt_budget:
        raise ValueError("owner uses another attempt budget")
    if certificate.preparation_policy != policy:
        raise ValueError("owner uses another preparation policy")
    if certificate.preparation_role_sha256 != role:
        raise ValueError("owner uses another preparation role")
    require_matching_custody()
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation_certificate(
    reference_initializer_owner: object,
    initial_tilt_composer: object,
    owner: object,
    *,
    residual_context: object,
    attempt_budget: object,
    preparation_policy: object,
    preparation_role_sha256: object,
    word_family_hypothesis: object,
) -> CounterKeyedInitialTiltRejectionPreparationCertificate:
    """Return the reconstructed live rejection-preparation certificate."""

    return (
        require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation(
            reference_initializer_owner,
            initial_tilt_composer,
            owner,
            residual_context=residual_context,
            attempt_budget=attempt_budget,
            preparation_policy=preparation_policy,
            preparation_role_sha256=preparation_role_sha256,
            word_family_hypothesis=word_family_hypothesis,
        ).certificate
    )


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCOPE",
    "INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCHEMA_VERSION",
    "INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCOPE",
    "INITIAL_TILT_REJECTION_WORD_FAMILY_PREMISE",
    "INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM",
    "INITIAL_TILT_REJECTION_TRIANGLE_LEDGER",
    "INITIAL_TILT_REJECTION_STRATEGY",
    "INITIAL_TILT_REJECTION_STAGE_INDEX",
    "INITIAL_TILT_REJECTION_DOMAIN_TAG",
    "INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT",
    "INITIAL_TILT_REJECTION_MIN_ATTEMPTS",
    "INITIAL_TILT_REJECTION_MAX_ATTEMPTS",
    "INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS",
    "INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS",
    "INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION",
    "InitialTiltRejectionPreparationWordFamilyHypothesis",
    "CounterKeyedInitialTiltRejectionPreparationCertificate",
    "CounterKeyedInitialTiltRejectionAttempt",
    "CounterKeyedInitialTiltRejectionPreparationResult",
    "CounterKeyedInitialTiltRejectionPreparationOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionPreparationError",
    "declare_initial_tilt_rejection_preparation_word_family_hypothesis",
    "validate_initial_tilt_rejection_preparation_word_family_hypothesis",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation",
    (
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "preparation_certificate"
    ),
]
