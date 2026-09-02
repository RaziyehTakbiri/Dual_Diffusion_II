"""Bounded tag-3 raw-prefix custody for bootstrap lineage occurrences.

Checkpoint twenty-three reserves one direct ``initializer`` Philox address for
each positive lineage serial.  This additive successor binds one exact
checkpoint-twenty-four owner, accepts an already existing bootstrap-form
lineage state, and consumes a caller-declared positive raw64 prefix from every
live occurrence's tag-3 stream.  The initializer step coordinate is fixed to
zero.  Empty bootstrap states return an empty, zero-word transcript.

The words are deliberately uninterpreted.  This module does not draw a count,
type, event, coordinate, categorical variable, Gaussian variable, rejection
proposal, SIR particle, or conditional initializer.  It therefore does not
admit an initializer, path, Strang step, or full sampler.  Reissuing the same
address deliberately replays the same prefix; no one-shot, independence,
physical-randomness, portability, or cryptographic claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass
import platform
import sys
from typing import Dict, Mapping, Tuple

import numpy as np

try:
    from heterodiff.processes import (
        plugin_bridge_continuous_route_evidence as _route_evidence,
    )
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_lineage_contract as _lineage,
    )
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_operational_epoch_loop as _epoch,
    )
    from heterodiff.processes import plugin_bridge_operational_thinning as _thinning
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "initializer-stream consumption requires the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise
from heterodiff.theory.configuration_reference import TransformedEvent


PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initializer-stream-consumption-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY = (
    "exact-checkpoint24-and-checkpoint23-owner-binding;"
    "bootstrap-form-initial-lineage-only;fixed-initializer-step-zero;"
    "exact-tag3-stream-per-live-serial;positive-bounded-raw64-prefix;"
    "exact-pre-post-philox-snapshots;same-runtime-local-prefix-replay;"
    "no-upper-counter-carry;unchanged-lineage-and-model-projection-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE = (
    "same-runtime-procedural-tag3-raw64-prefix-custody;"
    "existing-bootstrap-form-lineage-only;empty-state-zero-word-only;"
    "not-initializer-output-or-law;not-reference-conditional-or-tilted-law;"
    "not-enumeration-rejection-or-sir;not-exact-uniform-categorical-integer-"
    "or-gaussian-law;not-statistical-independence;not-physical-randomness;"
    "not-global-run-id-uniqueness;not-one-shot-address-use;"
    "not-brownian-consumption-or-coupling;not-drift;not-path;not-strang;"
    "not-target-or-stationarity;not-liveness;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)

COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX = 0
COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS = 64
COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE = 4_096
COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS = 65_536
_MAX_RAW64_WORDS_PER_OCCURRENCE = (
    COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE
)

_CERTIFICATE_TOKEN = object()
_OCCURRENCE_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()
_ZERO_SHA256 = "0" * 64


class PluginBridgeCounterKeyedInitializerStreamConsumptionError(ArithmeticError):
    """Fail-closed checkpoint-twenty-five custody error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    excluded = set(names)
    return {name: value for name, value in values.items() if name not in excluded}


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact bool" % name)
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact Python integer" % name)
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _exact_positive_word_count(value: object, *, name: str) -> int:
    result = _exact_nonnegative_integer(value, name=name)
    if result == 0:
        raise ValueError("%s must be positive for a live occurrence" % name)
    if (
        result
        > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE
    ):
        raise ValueError("%s exceeds the per-occurrence maximum bound" % name)
    return result


def _preflight_word_plan(
    raw64_word_counts: object,
    *,
    expected_records: int,
) -> Tuple[Tuple[int, ...], int]:
    if type(raw64_word_counts) is not tuple:
        raise TypeError("raw64_word_counts must be an exact tuple")
    if (
        len(raw64_word_counts)
        > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
    ):
        raise ValueError("raw64 word-count plan exceeds the record bound")
    if len(raw64_word_counts) != expected_records:
        raise ValueError("raw64 word-count plan does not cover every occurrence")
    checked = []
    total = 0
    for position, value in enumerate(raw64_word_counts):
        count = _exact_positive_word_count(
            value,
            name="raw64_word_counts[%d]" % position,
        )
        total += count
        if total > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS:
            raise ValueError("raw64 word-count plan exceeds the aggregate bound")
        checked.append(count)
    return tuple(checked), total


def _preflight_state_shape(state: object) -> _lineage.OperationalLineageState:
    if type(state) is not _lineage.OperationalLineageState:
        raise TypeError("initial_state must be an exact OperationalLineageState")
    for name in (
        "occurrences",
        "occurrence_sha256s",
        "retired_identifiers",
        "retired_identifier_sha256s",
        "model_configuration",
    ):
        if type(getattr(state, name)) is not tuple:
            raise TypeError("initial_state.%s must be an exact tuple" % name)
    if (
        len(state.occurrences)
        > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
    ):
        raise ValueError("initial lineage exceeds the initializer stream bound")
    if len(state.occurrence_sha256s) != len(state.occurrences):
        raise ValueError("initial occurrence digest count differs")
    if len(state.model_configuration) != len(state.occurrences):
        raise ValueError("initial model projection count differs")
    if state.retired_identifiers or state.retired_identifier_sha256s:
        raise ValueError("initializer consumption requires a bootstrap state")
    return state


def _snapshot_matches(
    left: _route_evidence.PhiloxRouteStateSnapshot,
    right: _route_evidence.PhiloxRouteStateSnapshot,
) -> bool:
    return all(
        getattr(left, name) == getattr(right, name)
        for name in _route_evidence._snapshot_fields()
    )


def _capture_fields(value: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return tuple(getattr(value, name) for name in fields)


def _require_fields_unchanged(
    value: object,
    fields: Tuple[str, ...],
    before: Tuple[object, ...],
    *,
    identity_fields: Tuple[str, ...],
    name: str,
) -> None:
    if len(before) != len(fields):
        raise ValueError("%s field snapshot is incomplete" % name)
    for field, expected in zip(fields, before):
        actual = getattr(value, field)
        if field in identity_fields:
            if actual is not expected:
                raise ValueError("%s field %s changed identity" % (name, field))
        elif not _thinning._field_matches(field, actual, expected):
            raise ValueError("%s field %s changed" % (name, field))


def _preflight_raw_words(words: object, *, expected: int) -> Tuple[int, ...]:
    if type(words) is not tuple:
        raise TypeError("raw64_words must be an exact tuple")
    if len(words) != expected:
        raise ValueError("raw64 word tuple length differs from its request")
    if (
        len(words)
        > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE
    ):
        raise ValueError("raw64 word tuple exceeds the per-occurrence bound")
    checked = []
    for index, word in enumerate(words):
        if type(word) is not int:
            raise TypeError("raw64_words[%d] must be an exact integer" % index)
        if word < 0 or word > _lineage.MAX_UINT64:
            raise ValueError("raw64_words[%d] is outside uint64" % index)
        checked.append(word)
    return tuple(checked)


def _runtime_sha256() -> str:
    probe = np.random.Generator(
        np.random.Philox(
            key=np.asarray((0, 3), dtype=np.uint64),
            counter=np.asarray((0, 0, 1, 0), dtype=np.uint64),
        )
    )
    probe_initial = _route_evidence._capture_philox_state(probe)
    probe_words = tuple(
        int(value) for value in np.atleast_1d(probe.bit_generator.random_raw(5))
    )
    probe_final = _route_evidence._capture_philox_state(probe)
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-counter-keyed-initializer-consumption-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "policy": (
                PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY
            ),
            "scope": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE,
            "step_index": COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX,
            "maximum_stream_records": (
                COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
            ),
            "maximum_words_per_occurrence": (_MAX_RAW64_WORDS_PER_OCCURRENCE),
            "maximum_total_words": (
                COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS
            ),
            "initializer_domain": _lineage.COUNTER_KEY_DOMAIN_INITIALIZER,
            "initializer_domain_tag": _lineage.COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
            "probe_initial_sha256": probe_initial.snapshot_sha256,
            "probe_words": probe_words,
            "probe_final_sha256": probe_final.snapshot_sha256,
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerStreamConsumptionCertificate:
    """Transitive certificate for bounded tag-3 prefix custody."""

    schema_version: str
    certificate_scope: str
    consumption_policy: str
    consumption_role_sha256: str
    process_parameter_sha256: str
    checkpoint24_certificate: _epoch.CounterKeyedOperationalEpochLoopCertificate
    checkpoint24_certificate_sha256: str
    checkpoint24_role_sha256: str
    checkpoint24_runtime_sha256: str
    checkpoint23_certificate: _lineage.CounterKeyedLineageCertificate
    checkpoint23_certificate_sha256: str
    checkpoint23_role_sha256: str
    checkpoint23_runtime_sha256: str
    consumption_runtime_sha256: str
    philox_snapshot_schema_version: str
    rng_bit_generator: str
    initializer_domain: str
    initializer_domain_tag: int
    initializer_step_index: int
    maximum_stream_records: int
    maximum_raw64_words_per_occurrence: int
    maximum_total_raw64_words: int
    exact_checkpoint24_owner_binding_certified: bool
    exact_checkpoint23_owner_binding_certified: bool
    bootstrap_form_initial_state_gate_certified: bool
    fixed_initializer_step_zero_certified: bool
    exact_initializer_tag3_address_certified: bool
    complete_live_occurrence_coverage_certified: bool
    positive_raw64_prefix_per_nonempty_occurrence_certified: bool
    exact_pre_post_snapshot_custody_certified: bool
    same_runtime_prefix_replay_certified: bool
    recorded_upper_counter_limb_preservation_certified: bool
    bounded_work_preflight_certified: bool
    no_caller_rng_certified: bool
    unchanged_lineage_state_identity_certified: bool
    occurrence_stream_consumption_certified: bool
    initializer_stream_consumption_certified: bool
    event_or_configuration_generation_certified: bool
    initializer_output_law_certified: bool
    reference_initializer_law_certified: bool
    conditional_or_tilted_initializer_law_certified: bool
    enumeration_rejection_or_sir_certified: bool
    exact_uniform_law_certified: bool
    exact_categorical_law_certified: bool
    exact_integer_law_certified: bool
    exact_gaussian_law_certified: bool
    analytic_output_law_certified: bool
    statistical_independence_certified: bool
    physical_randomness_certified: bool
    global_run_id_uniqueness_certified: bool
    duplicate_address_use_prevention_certified: bool
    lineage_fork_prevention_certified: bool
    brownian_stream_consumption_certified: bool
    brownian_additive_coupling_certified: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    strang_sampler_admissible: bool
    full_sampler_admissible: bool
    analytic_target_preserved: bool
    rounded_stationarity_certified: bool
    sampler_liveness_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedInitializerStreamConsumptionCertificate cannot be "
            "subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("initializer-stream certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer-stream certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer-stream certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerStreamConsumptionCertificate.__annotations__)


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint24_certificate",
        "checkpoint23_certificate",
        "certificate_sha256",
    )


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitializerStreamConsumptionCertificate:
    if type(certificate) is not CounterKeyedInitializerStreamConsumptionCertificate:
        raise TypeError("certificate has the wrong exact type")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if (
        values["schema_version"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCHEMA_VERSION
    ):
        raise ValueError("initializer-stream certificate schema differs")
    if (
        values["certificate_scope"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE
    ):
        raise ValueError("initializer-stream certificate scope differs")
    if (
        values["consumption_policy"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY
    ):
        raise ValueError("initializer-stream certificate policy differs")
    role = _thinning._require_sha256(
        values["consumption_role_sha256"],
        name="certificate.consumption_role_sha256",
    )
    del role
    parent24 = _epoch._validate_certificate(values["checkpoint24_certificate"])
    parent23 = _lineage._validate_certificate(values["checkpoint23_certificate"])
    if parent24.checkpoint23_certificate_sha256 != parent23.certificate_sha256:
        raise ValueError("checkpoint-24 and checkpoint-23 certificates differ")
    if parent24.checkpoint23_role_sha256 != parent23.contract_role_sha256:
        raise ValueError("checkpoint-24 and checkpoint-23 roles differ")
    if parent24.checkpoint23_runtime_sha256 != parent23.contract_runtime_sha256:
        raise ValueError("checkpoint-24 and checkpoint-23 runtimes differ")
    expected_scalars = {
        "process_parameter_sha256": parent24.process_parameter_sha256,
        "checkpoint24_certificate_sha256": parent24.certificate_sha256,
        "checkpoint24_role_sha256": parent24.epoch_role_sha256,
        "checkpoint24_runtime_sha256": parent24.epoch_runtime_sha256,
        "checkpoint23_certificate_sha256": parent23.certificate_sha256,
        "checkpoint23_role_sha256": parent23.contract_role_sha256,
        "checkpoint23_runtime_sha256": parent23.contract_runtime_sha256,
        "philox_snapshot_schema_version": (parent23.philox_snapshot_schema_version),
        "rng_bit_generator": parent23.rng_bit_generator,
        "initializer_domain": _lineage.COUNTER_KEY_DOMAIN_INITIALIZER,
        "initializer_domain_tag": _lineage.COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
        "initializer_step_index": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX
        ),
        "maximum_stream_records": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS
        ),
    }
    for name, expected in expected_scalars.items():
        if values[name] != expected or type(values[name]) is not type(expected):
            raise ValueError("initializer-stream certificate %s differs" % name)
    positive = (
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "bootstrap_form_initial_state_gate_certified",
        "fixed_initializer_step_zero_certified",
        "exact_initializer_tag3_address_certified",
        "complete_live_occurrence_coverage_certified",
        "positive_raw64_prefix_per_nonempty_occurrence_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "bounded_work_preflight_certified",
        "no_caller_rng_certified",
        "unchanged_lineage_state_identity_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "passed",
    )
    negative = (
        "event_or_configuration_generation_certified",
        "initializer_output_law_certified",
        "reference_initializer_law_certified",
        "conditional_or_tilted_initializer_law_certified",
        "enumeration_rejection_or_sir_certified",
        "exact_uniform_law_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in positive:
        if _exact_bool(values[name], name="certificate.%s" % name) is not True:
            raise ValueError("initializer-stream positive claim differs")
    for name in negative:
        if _exact_bool(values[name], name="certificate.%s" % name) is not False:
            raise ValueError("initializer-stream negative claim differs")
    for name in (
        "consumption_runtime_sha256",
        "certificate_sha256",
    ):
        _thinning._require_sha256(values[name], name="certificate.%s" % name)
    if values["consumption_runtime_sha256"] != _runtime_sha256():
        raise ValueError("initializer-stream certificate runtime differs")
    expected_digest = _thinning._semantic_digest(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("initializer-stream certificate digest differs")
    return certificate


def _make_certificate(
    parent24: _epoch.CounterKeyedOperationalEpochLoopCertificate,
    parent23: _lineage.CounterKeyedLineageCertificate,
    *,
    consumption_role_sha256: str,
) -> CounterKeyedInitializerStreamConsumptionCertificate:
    checked24 = _epoch._validate_certificate(parent24)
    checked23 = _lineage._validate_certificate(parent23)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCHEMA_VERSION
        ),
        "certificate_scope": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE
        ),
        "consumption_policy": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY
        ),
        "consumption_role_sha256": consumption_role_sha256,
        "process_parameter_sha256": checked24.process_parameter_sha256,
        "checkpoint24_certificate": parent24,
        "checkpoint24_certificate_sha256": checked24.certificate_sha256,
        "checkpoint24_role_sha256": checked24.epoch_role_sha256,
        "checkpoint24_runtime_sha256": checked24.epoch_runtime_sha256,
        "checkpoint23_certificate": parent23,
        "checkpoint23_certificate_sha256": checked23.certificate_sha256,
        "checkpoint23_role_sha256": checked23.contract_role_sha256,
        "checkpoint23_runtime_sha256": checked23.contract_runtime_sha256,
        "consumption_runtime_sha256": _runtime_sha256(),
        "philox_snapshot_schema_version": checked23.philox_snapshot_schema_version,
        "rng_bit_generator": checked23.rng_bit_generator,
        "initializer_domain": _lineage.COUNTER_KEY_DOMAIN_INITIALIZER,
        "initializer_domain_tag": _lineage.COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
        "initializer_step_index": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX
        ),
        "maximum_stream_records": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS
        ),
        "certificate_sha256": _ZERO_SHA256,
    }
    positive = (
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "bootstrap_form_initial_state_gate_certified",
        "fixed_initializer_step_zero_certified",
        "exact_initializer_tag3_address_certified",
        "complete_live_occurrence_coverage_certified",
        "positive_raw64_prefix_per_nonempty_occurrence_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "bounded_work_preflight_certified",
        "no_caller_rng_certified",
        "unchanged_lineage_state_identity_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "passed",
    )
    negative = tuple(
        name
        for name in CounterKeyedInitializerStreamConsumptionCertificate.__annotations__
        if name.endswith("certified") or name.endswith("admissible")
    )
    for name in negative:
        if name not in positive:
            values[name] = False
    for name in positive:
        values[name] = True
    for name in (
        "analytic_target_preserved",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        values[name] = False
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return CounterKeyedInitializerStreamConsumptionCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerOccurrenceConsumption:
    """One exact tag-3 prefix bound to one bootstrap occurrence."""

    certificate: CounterKeyedInitializerStreamConsumptionCertificate
    certificate_sha256: str
    position: int
    occurrence: _lineage.OperationalLineagedOccurrence
    occurrence_sha256: str
    identifier: _lineage.OperationalLineageIdentifier
    identifier_sha256: str
    event: TransformedEvent
    event_model_key: Tuple[object, ...]
    run_id: int
    initialization_index: int
    step_index: int
    occurrence_serial: int
    raw64_word_count: int
    initializer_stream: _lineage.CounterKeyedPhiloxStream
    initializer_stream_sha256: str
    initializer_address_sha256: str
    stream_initial_state: _route_evidence.PhiloxRouteStateSnapshot
    stream_initial_snapshot_sha256: str
    stream_initial_state_sha256: str
    raw64_words: Tuple[int, ...]
    stream_final_state: _route_evidence.PhiloxRouteStateSnapshot
    stream_final_snapshot_sha256: str
    stream_final_state_sha256: str
    parent_execution_used_this_stream: bool
    successor_execution_invoked_this_stream: bool
    successor_execution_consumed_this_stream: bool
    occurrence_identity_preserved: bool
    event_identity_preserved: bool
    no_upper_counter_carry: bool
    same_runtime_only: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedInitializerOccurrenceConsumption cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _OCCURRENCE_TOKEN:
            raise TypeError("initializer occurrence records are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer occurrence record fields are incomplete")
        _preflight_raw_words(
            values["raw64_words"],
            expected=_exact_positive_word_count(
                values["raw64_word_count"],
                name="record.raw64_word_count",
            ),
        )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_occurrence_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer occurrence records are not pickle objects")


def _occurrence_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerOccurrenceConsumption.__annotations__)


def _occurrence_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "occurrence",
        "identifier",
        "event",
        "initializer_stream",
        "stream_initial_state",
        "stream_final_state",
        "record_sha256",
    )


def _validate_occurrence_record(
    record: object,
) -> CounterKeyedInitializerOccurrenceConsumption:
    if type(record) is not CounterKeyedInitializerOccurrenceConsumption:
        raise TypeError("record has the wrong exact occurrence-consumption type")
    values = {name: getattr(record, name) for name in _occurrence_fields()}
    certificate = _validate_certificate(values["certificate"])
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("occurrence record certificate digest differs")
    position = _exact_nonnegative_integer(values["position"], name="record.position")
    if position >= certificate.maximum_stream_records:
        raise ValueError("occurrence record position exceeds the bound")
    if type(values["occurrence"]) is not _lineage.OperationalLineagedOccurrence:
        raise TypeError("record occurrence has the wrong exact type")
    occurrence = _lineage._validate_occurrence(values["occurrence"])
    if values["occurrence_sha256"] != occurrence.occurrence_sha256:
        raise ValueError("occurrence record occurrence digest differs")
    if occurrence.certificate_sha256 != certificate.checkpoint23_certificate_sha256:
        raise ValueError("occurrence record belongs to another lineage certificate")
    if values["identifier"] is not values["occurrence"].identifier:
        raise ValueError("occurrence record identifier identity differs")
    identifier = _lineage._validate_identifier(values["identifier"])
    if values["identifier_sha256"] != identifier.identifier_sha256:
        raise ValueError("occurrence record identifier digest differs")
    if identifier.certificate_sha256 != certificate.checkpoint23_certificate_sha256:
        raise ValueError("occurrence identifier belongs to another certificate")
    if values["event"] is not values["occurrence"].event:
        raise ValueError("occurrence record event identity differs")
    if type(values["event"]) is not TransformedEvent:
        raise TypeError("occurrence record event has the wrong exact type")
    if values["event_model_key"] != values["event"].model_key():
        raise ValueError("occurrence record model key differs")
    run_id = _lineage._exact_uint64(values["run_id"], name="record.run_id")
    initialization_index = _lineage._exact_uint64(
        values["initialization_index"],
        name="record.initialization_index",
    )
    if identifier.run_id != run_id:
        raise ValueError("occurrence record identifier has another run")
    if identifier.origin_initialization_index != initialization_index:
        raise ValueError("occurrence record uses another initialization")
    if values["step_index"] != certificate.initializer_step_index:
        raise ValueError("occurrence record initializer step differs")
    if type(values["step_index"]) is not int:
        raise TypeError("occurrence record step index must be an exact integer")
    serial = _lineage._exact_positive_uint64(
        values["occurrence_serial"],
        name="record.occurrence_serial",
    )
    if serial != identifier.serial:
        raise ValueError("occurrence record serial differs from its identifier")
    count = _exact_positive_word_count(
        values["raw64_word_count"],
        name="record.raw64_word_count",
    )
    words = _preflight_raw_words(values["raw64_words"], expected=count)
    del words
    if type(values["initializer_stream"]) is not _lineage.CounterKeyedPhiloxStream:
        raise TypeError("initializer stream has the wrong exact type")
    stream = _lineage._validate_stream_record(values["initializer_stream"])
    if stream.certificate is not certificate.checkpoint23_certificate:
        raise ValueError("initializer stream has another certificate object")
    if values["initializer_stream_sha256"] != stream.stream_sha256:
        raise ValueError("initializer stream digest differs")
    if values["initializer_address_sha256"] != stream.address.address_sha256:
        raise ValueError("initializer address digest differs")
    address = stream.address
    if address.domain != certificate.initializer_domain:
        raise ValueError("initializer stream domain differs")
    if address.domain_tag != certificate.initializer_domain_tag:
        raise ValueError("initializer stream tag differs")
    if address.run_id != run_id or address.step_index != values["step_index"]:
        raise ValueError("initializer stream run or step differs")
    if address.occurrence_serial != serial or address.proposal_index != 0:
        raise ValueError("initializer stream subject coordinates differ")
    if values["stream_initial_state"] is not stream.initial_state:
        raise ValueError("initializer initial-state identity differs")
    initial = _route_evidence._validate_snapshot(values["stream_initial_state"])
    final = _route_evidence._validate_snapshot(values["stream_final_state"])
    if values["stream_initial_snapshot_sha256"] != initial.snapshot_sha256:
        raise ValueError("initializer initial snapshot digest differs")
    if values["stream_initial_state_sha256"] != initial.state_sha256:
        raise ValueError("initializer initial state digest differs")
    if values["stream_final_snapshot_sha256"] != final.snapshot_sha256:
        raise ValueError("initializer final snapshot digest differs")
    if values["stream_final_state_sha256"] != final.state_sha256:
        raise ValueError("initializer final state digest differs")
    expected_booleans = {
        "parent_execution_used_this_stream": False,
        "successor_execution_invoked_this_stream": True,
        "successor_execution_consumed_this_stream": True,
        "occurrence_identity_preserved": True,
        "event_identity_preserved": True,
        "no_upper_counter_carry": True,
        "same_runtime_only": True,
    }
    for name, expected in expected_booleans.items():
        if _exact_bool(values[name], name="record.%s" % name) is not expected:
            raise ValueError("initializer occurrence flag %s differs" % name)
    if stream.parent_execution_used_this_stream is not False:
        raise ValueError("frozen parent stream consumption flag differs")
    if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
        raise ValueError("initializer stream recorded an upper counter carry")
    for name in (
        "certificate_sha256",
        "occurrence_sha256",
        "identifier_sha256",
        "initializer_stream_sha256",
        "initializer_address_sha256",
        "stream_initial_snapshot_sha256",
        "stream_initial_state_sha256",
        "stream_final_snapshot_sha256",
        "stream_final_state_sha256",
        "record_sha256",
    ):
        _thinning._require_sha256(values[name], name="record.%s" % name)
    expected_digest = _thinning._semantic_digest(_occurrence_payload(values))
    if values["record_sha256"] != expected_digest:
        raise ValueError("initializer occurrence record digest differs")
    return record


def _make_occurrence_record(
    certificate: CounterKeyedInitializerStreamConsumptionCertificate,
    occurrence: _lineage.OperationalLineagedOccurrence,
    stream: _lineage.CounterKeyedPhiloxStream,
    final_state: _route_evidence.PhiloxRouteStateSnapshot,
    raw64_words: Tuple[int, ...],
    *,
    position: int,
    initialization_index: int,
) -> CounterKeyedInitializerOccurrenceConsumption:
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "position": position,
        "occurrence": occurrence,
        "occurrence_sha256": occurrence.occurrence_sha256,
        "identifier": occurrence.identifier,
        "identifier_sha256": occurrence.identifier.identifier_sha256,
        "event": occurrence.event,
        "event_model_key": occurrence.event.model_key(),
        "run_id": occurrence.identifier.run_id,
        "initialization_index": initialization_index,
        "step_index": COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX,
        "occurrence_serial": occurrence.identifier.serial,
        "raw64_word_count": len(raw64_words),
        "initializer_stream": stream,
        "initializer_stream_sha256": stream.stream_sha256,
        "initializer_address_sha256": stream.address.address_sha256,
        "stream_initial_state": stream.initial_state,
        "stream_initial_snapshot_sha256": stream.initial_state.snapshot_sha256,
        "stream_initial_state_sha256": stream.initial_state.state_sha256,
        "raw64_words": raw64_words,
        "stream_final_state": final_state,
        "stream_final_snapshot_sha256": final_state.snapshot_sha256,
        "stream_final_state_sha256": final_state.state_sha256,
        "parent_execution_used_this_stream": False,
        "successor_execution_invoked_this_stream": True,
        "successor_execution_consumed_this_stream": True,
        "occurrence_identity_preserved": True,
        "event_identity_preserved": True,
        "no_upper_counter_carry": True,
        "same_runtime_only": True,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _thinning._semantic_digest(_occurrence_payload(values))
    return CounterKeyedInitializerOccurrenceConsumption(
        **values,
        _construction_token=_OCCURRENCE_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerStreamConsumptionResult:
    """Complete ordered tag-3 prefix transcript for one bootstrap state."""

    certificate: CounterKeyedInitializerStreamConsumptionCertificate
    certificate_sha256: str
    initial_state: _lineage.OperationalLineageState
    initial_state_sha256: str
    final_state: _lineage.OperationalLineageState
    final_state_sha256: str
    run_id: int
    initialization_index: int
    step_index: int
    raw64_word_counts: Tuple[int, ...]
    occurrences: Tuple[CounterKeyedInitializerOccurrenceConsumption, ...]
    occurrence_sha256s: Tuple[str, ...]
    total_raw64_words: int
    stream_count: int
    empty_state_zero_word: bool
    all_requested_streams_consumed: bool
    exact_initial_final_state_identity: bool
    initial_model_projection_unchanged: bool
    no_caller_rng: bool
    same_runtime_only: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedInitializerStreamConsumptionResult cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("initializer-stream results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer-stream result fields are incomplete")
        if type(values["raw64_word_counts"]) is not tuple:
            raise TypeError("result word counts must be an exact tuple")
        if type(values["occurrences"]) is not tuple:
            raise TypeError("result occurrences must be an exact tuple")
        if type(values["occurrence_sha256s"]) is not tuple:
            raise TypeError("result occurrence digests must be an exact tuple")
        if (
            len(values["occurrences"])
            > COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
        ):
            raise ValueError("result occurrence tuple exceeds its bound")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_result_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer-stream results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerStreamConsumptionResult.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "initial_state",
        "final_state",
        "occurrences",
        "result_sha256",
    )


def _validate_result_record(
    result: object,
) -> CounterKeyedInitializerStreamConsumptionResult:
    if type(result) is not CounterKeyedInitializerStreamConsumptionResult:
        raise TypeError("result has the wrong exact initializer-consumption type")
    values = {name: getattr(result, name) for name in _result_fields()}
    certificate = _validate_certificate(values["certificate"])
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("initializer result certificate digest differs")
    _preflight_state_shape(values["initial_state"])
    if values["final_state"] is not values["initial_state"]:
        raise ValueError("initializer result changed the lineage state object")
    initial = _lineage._validate_state(values["initial_state"])
    if values["initial_state_sha256"] != initial.state_sha256:
        raise ValueError("initializer initial-state digest differs")
    if values["final_state_sha256"] != initial.state_sha256:
        raise ValueError("initializer final-state digest differs")
    run_id = _lineage._exact_uint64(values["run_id"], name="result.run_id")
    if run_id != initial.run_id:
        raise ValueError("initializer result uses another run")
    initialization_index = _lineage._exact_uint64(
        values["initialization_index"],
        name="result.initialization_index",
    )
    if initialization_index != initial.initialization_index:
        raise ValueError("initializer result uses another initialization")
    step_index = _exact_nonnegative_integer(
        values["step_index"],
        name="result.step_index",
    )
    if step_index != certificate.initializer_step_index:
        raise ValueError("initializer result step differs")
    counts, total = _preflight_word_plan(
        values["raw64_word_counts"],
        expected_records=len(initial.occurrences),
    )
    if type(values["occurrences"]) is not tuple:
        raise TypeError("initializer result records must be an exact tuple")
    if len(values["occurrences"]) != len(initial.occurrences):
        raise ValueError("initializer result record coverage differs")
    records = tuple(
        _validate_occurrence_record(record) for record in values["occurrences"]
    )
    if values["occurrence_sha256s"] != tuple(
        record.record_sha256 for record in records
    ):
        raise ValueError("initializer result record digest order differs")
    if (
        values["stream_count"] != len(records)
        or type(values["stream_count"]) is not int
    ):
        raise ValueError("initializer result stream count differs")
    if values["total_raw64_words"] != total:
        raise ValueError("initializer result total raw64 count differs")
    if type(values["total_raw64_words"]) is not int:
        raise TypeError("initializer total raw64 count must be an exact integer")
    for position, (parent, record, count) in enumerate(
        zip(initial.occurrences, records, counts)
    ):
        if record.certificate is not values["certificate"]:
            raise ValueError("initializer result record has another certificate")
        if record.position != position or record.occurrence is not parent:
            raise ValueError("initializer result record position or identity differs")
        if record.raw64_word_count != count:
            raise ValueError("initializer result record word count differs")
    expected_booleans = {
        "empty_state_zero_word": len(records) == 0,
        "all_requested_streams_consumed": True,
        "exact_initial_final_state_identity": True,
        "initial_model_projection_unchanged": True,
        "no_caller_rng": True,
        "same_runtime_only": True,
    }
    for name, expected in expected_booleans.items():
        if _exact_bool(values[name], name="result.%s" % name) is not expected:
            raise ValueError("initializer result flag %s differs" % name)
    for name in (
        "certificate_sha256",
        "initial_state_sha256",
        "final_state_sha256",
        "result_sha256",
    ):
        _thinning._require_sha256(values[name], name="result.%s" % name)
    expected_digest = _thinning._semantic_digest(_result_payload(values))
    if values["result_sha256"] != expected_digest:
        raise ValueError("initializer result digest differs")
    return result


def _make_result(
    certificate: CounterKeyedInitializerStreamConsumptionCertificate,
    initial_state: _lineage.OperationalLineageState,
    counts: Tuple[int, ...],
    records: Tuple[CounterKeyedInitializerOccurrenceConsumption, ...],
) -> CounterKeyedInitializerStreamConsumptionResult:
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "initial_state": initial_state,
        "initial_state_sha256": initial_state.state_sha256,
        "final_state": initial_state,
        "final_state_sha256": initial_state.state_sha256,
        "run_id": initial_state.run_id,
        "initialization_index": initial_state.initialization_index,
        "step_index": COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX,
        "raw64_word_counts": counts,
        "occurrences": records,
        "occurrence_sha256s": tuple(record.record_sha256 for record in records),
        "total_raw64_words": sum(counts),
        "stream_count": len(records),
        "empty_state_zero_word": len(records) == 0,
        "all_requested_streams_consumed": True,
        "exact_initial_final_state_identity": True,
        "initial_model_projection_unchanged": True,
        "no_caller_rng": True,
        "same_runtime_only": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _thinning._semantic_digest(_result_payload(values))
    return CounterKeyedInitializerStreamConsumptionResult(
        **values,
        _construction_token=_RESULT_TOKEN,
    )


class CounterKeyedInitializerStreamConsumptionOwner:
    """Immutable owner of checkpoint-twenty-five tag-3 prefix custody."""

    __slots__ = (
        "_epoch_owner",
        "_certified_epoch_owner",
        "_contract_owner",
        "_certified_contract_owner",
        "_consumption_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedInitializerStreamConsumptionOwner cannot be subclassed"
        )

    def __init__(
        self,
        epoch_owner: _epoch.CounterKeyedOperationalEpochLoop,
        consumption_role_sha256: str,
        certificate: CounterKeyedInitializerStreamConsumptionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("initializer-stream owners require certification")
        if type(epoch_owner) is not _epoch.CounterKeyedOperationalEpochLoop:
            raise TypeError("epoch_owner has the wrong exact type")
        role = _thinning._require_sha256(
            consumption_role_sha256,
            name="consumption_role_sha256",
        )
        checked = _validate_certificate(certificate)
        if checked.consumption_role_sha256 != role:
            raise ValueError("initializer-stream role differs from certificate")
        contract_owner = epoch_owner.contract_owner
        object.__setattr__(self, "_epoch_owner", epoch_owner)
        object.__setattr__(self, "_certified_epoch_owner", epoch_owner)
        object.__setattr__(self, "_contract_owner", contract_owner)
        object.__setattr__(self, "_certified_contract_owner", contract_owner)
        object.__setattr__(self, "_consumption_role_sha256", role)
        object.__setattr__(self, "_certificate", checked)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("initializer-stream owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("initializer-stream owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer-stream owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedInitializerStreamConsumptionCertificate:
        return self._certificate

    @property
    def epoch_owner(self) -> _epoch.CounterKeyedOperationalEpochLoop:
        return self._epoch_owner

    @property
    def contract_owner(self) -> _lineage.CounterKeyedLineageContractOwner:
        return self._contract_owner

    def _require_live_binding(
        self,
    ) -> CounterKeyedInitializerStreamConsumptionCertificate:
        _thinning._require_binary64_environment()
        if type(self._epoch_owner) is not _epoch.CounterKeyedOperationalEpochLoop:
            raise TypeError("initializer-stream epoch owner has the wrong type")
        if self._epoch_owner is not self._certified_epoch_owner:
            raise ValueError("initializer-stream epoch-owner binding changed")
        if self._epoch_owner.contract_owner is not self._contract_owner:
            raise ValueError("initializer-stream checkpoint-23 binding changed")
        if self._contract_owner is not self._certified_contract_owner:
            raise ValueError("initializer-stream contract-owner binding changed")
        checkpoint24 = self._epoch_owner._require_live_binding()
        checkpoint23 = self._contract_owner._require_live_binding()
        if self.certificate.checkpoint24_certificate is not checkpoint24:
            raise ValueError("initializer-stream checkpoint-24 certificate changed")
        if self.certificate.checkpoint23_certificate is not checkpoint23:
            raise ValueError("initializer-stream checkpoint-23 certificate changed")
        if self.certificate.consumption_runtime_sha256 != _runtime_sha256():
            raise ValueError("live initializer-stream runtime differs")
        expected = _make_certificate(
            checkpoint24,
            checkpoint23,
            consumption_role_sha256=self._consumption_role_sha256,
        )
        for name in _certificate_fields():
            actual_value = getattr(self.certificate, name)
            expected_value = getattr(expected, name)
            if name in ("checkpoint24_certificate", "checkpoint23_certificate"):
                if actual_value is not expected_value:
                    raise ValueError("initializer-stream parent certificate changed")
            elif not _thinning._field_matches(name, actual_value, expected_value):
                raise ValueError(
                    "initializer-stream certificate field %s differs" % name
                )
        _thinning._require_binary64_environment()
        return self.certificate

    def _validate_bootstrap_state(
        self,
        state: object,
    ) -> _lineage.OperationalLineageState:
        preflight = _preflight_state_shape(state)
        checked = _lineage._validate_state(preflight)
        if (
            checked.certificate_sha256
            != self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("initial lineage belongs to another certificate")
        if checked.next_serial != len(checked.occurrences) + 1:
            raise ValueError("bootstrap lineage next serial differs")
        if len(checked.model_configuration) != len(checked.occurrences):
            raise ValueError("bootstrap model projection count differs")
        for position, (occurrence, event) in enumerate(
            zip(checked.occurrences, checked.model_configuration)
        ):
            identifier = occurrence.identifier
            if identifier.origin_kind != "initial":
                raise ValueError("initializer consumption requires initial origins")
            if identifier.serial != position + 1:
                raise ValueError("bootstrap serial differs from tuple position")
            if identifier.origin_initial_position != position:
                raise ValueError("bootstrap origin position differs")
            if identifier.origin_initialization_index != checked.initialization_index:
                raise ValueError("bootstrap occurrence uses another initialization")
            if occurrence.event is not event:
                raise ValueError("bootstrap model projection lost event identity")
        return preflight

    def _preflight_request(
        self,
        initial_state: object,
        raw64_word_counts: object,
    ) -> Tuple[_lineage.OperationalLineageState, Tuple[int, ...]]:
        shaped = _preflight_state_shape(initial_state)
        counts, _ = _preflight_word_plan(
            raw64_word_counts,
            expected_records=len(shaped.occurrences),
        )
        checked = self._validate_bootstrap_state(shaped)
        return checked, counts

    def validate_occurrence_consumption(
        self,
        record: CounterKeyedInitializerOccurrenceConsumption,
        occurrence: _lineage.OperationalLineagedOccurrence,
        *,
        position: object,
        raw64_word_count: object,
    ) -> CounterKeyedInitializerOccurrenceConsumption:
        """Deeply replay one exact tag-3 prefix record."""

        self._require_live_binding()
        checked_position = _exact_nonnegative_integer(position, name="position")
        checked_count = _exact_positive_word_count(
            raw64_word_count,
            name="raw64_word_count",
        )
        if type(occurrence) is not _lineage.OperationalLineagedOccurrence:
            raise TypeError("occurrence has the wrong exact type")
        _lineage._validate_occurrence(occurrence)
        checked_record = _validate_occurrence_record(record)
        record_fields = _occurrence_fields()
        record_before = _capture_fields(record, record_fields)
        parent_fields = _lineage._occurrence_fields()
        parent_before = _capture_fields(occurrence, parent_fields)
        if checked_record.certificate is not self.certificate:
            raise ValueError("occurrence record belongs to another owner")
        if checked_record.occurrence is not occurrence:
            raise ValueError("occurrence record belongs to another occurrence")
        if checked_record.identifier is not occurrence.identifier:
            raise ValueError("occurrence record identifier identity differs")
        if checked_record.event is not occurrence.event:
            raise ValueError("occurrence record event identity differs")
        if (
            occurrence.certificate_sha256
            != self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("occurrence belongs to another lineage certificate")
        if (
            occurrence.identifier.certificate_sha256
            != self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("occurrence identifier has another certificate")
        if checked_record.position != checked_position:
            raise ValueError("occurrence record position differs")
        if checked_record.raw64_word_count != checked_count:
            raise ValueError("occurrence record word count differs")
        stream = checked_record.initializer_stream
        if stream.certificate is not self.contract_owner.certificate:
            raise ValueError("occurrence stream belongs to another parent owner")
        self.contract_owner.validate_stream(stream)
        generator = self.contract_owner.reconstruct_stream(stream)
        initial = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(initial, checked_record.stream_initial_state):
            raise ValueError("occurrence replay initial snapshot differs")
        replay_words = tuple(
            int(value)
            for value in np.atleast_1d(
                generator.bit_generator.random_raw(checked_count)
            )
        )
        final = _route_evidence._capture_philox_state(generator)
        if replay_words != checked_record.raw64_words:
            raise ValueError("occurrence raw64 prefix did not replay")
        if not _snapshot_matches(final, checked_record.stream_final_state):
            raise ValueError("occurrence final snapshot did not replay")
        if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
            raise PluginBridgeCounterKeyedInitializerStreamConsumptionError(
                "initializer raw64 prefix carried into an upper address limb"
            )
        self._require_live_binding()
        _validate_occurrence_record(record)
        _lineage._validate_occurrence(occurrence)
        if (
            occurrence.certificate_sha256
            != self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("occurrence certificate changed during replay")
        if (
            occurrence.identifier.certificate_sha256
            != self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("occurrence identifier changed certificate")
        _require_fields_unchanged(
            record,
            record_fields,
            record_before,
            identity_fields=(
                "certificate",
                "occurrence",
                "identifier",
                "event",
                "event_model_key",
                "initializer_stream",
                "stream_initial_state",
                "raw64_words",
                "stream_final_state",
            ),
            name="occurrence record",
        )
        _require_fields_unchanged(
            occurrence,
            parent_fields,
            parent_before,
            identity_fields=("identifier", "event", "event_model_key"),
            name="parent occurrence",
        )
        if record.occurrence is not occurrence:
            raise ValueError("occurrence record parent changed during replay")
        if record.position != checked_position:
            raise ValueError("occurrence record position changed during replay")
        if record.raw64_word_count != checked_count:
            raise ValueError("occurrence word count changed during replay")
        return record

    def consume(
        self,
        initial_state: _lineage.OperationalLineageState,
        *,
        raw64_word_counts: object,
    ) -> CounterKeyedInitializerStreamConsumptionResult:
        """Consume one bounded tag-3 raw64 prefix per bootstrap occurrence."""

        self._require_live_binding()
        state, counts = self._preflight_request(initial_state, raw64_word_counts)
        state_fields = _lineage._state_fields()
        state_before = _capture_fields(state, state_fields)
        parent_fields = _lineage._occurrence_fields()
        occurrence_befores = tuple(
            _capture_fields(occurrence, parent_fields)
            for occurrence in state.occurrences
        )
        records = []
        for position, (occurrence, count) in enumerate(zip(state.occurrences, counts)):
            stream = self.contract_owner.make_initializer_stream(
                state.run_id,
                COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX,
                occurrence.identifier.serial,
            )
            if stream.certificate is not self.contract_owner.certificate:
                raise ValueError("initializer stream has another parent certificate")
            generator = self.contract_owner.reconstruct_stream(stream)
            initial = _route_evidence._capture_philox_state(generator)
            if not _snapshot_matches(initial, stream.initial_state):
                raise ValueError("initializer stream did not start at its receipt")
            words = tuple(
                int(value)
                for value in np.atleast_1d(generator.bit_generator.random_raw(count))
            )
            final = _route_evidence._capture_philox_state(generator)
            if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
                raise PluginBridgeCounterKeyedInitializerStreamConsumptionError(
                    "initializer raw64 prefix carried into an upper address limb"
                )
            record = _make_occurrence_record(
                self.certificate,
                occurrence,
                stream,
                final,
                words,
                position=position,
                initialization_index=state.initialization_index,
            )
            self.validate_occurrence_consumption(
                record,
                occurrence,
                position=position,
                raw64_word_count=count,
            )
            records.append(record)
        result = _make_result(self.certificate, state, counts, tuple(records))
        self.validate_result(
            result,
            state,
            raw64_word_counts=counts,
        )
        self._validate_bootstrap_state(state)
        _require_fields_unchanged(
            state,
            state_fields,
            state_before,
            identity_fields=(
                "occurrences",
                "occurrence_sha256s",
                "retired_identifiers",
                "retired_identifier_sha256s",
                "model_configuration",
            ),
            name="consumed initial lineage state",
        )
        for occurrence, before in zip(state.occurrences, occurrence_befores):
            _lineage._validate_occurrence(occurrence)
            _require_fields_unchanged(
                occurrence,
                parent_fields,
                before,
                identity_fields=("identifier", "event", "event_model_key"),
                name="consumed initial occurrence",
            )
        return result

    def validate_result(
        self,
        result: CounterKeyedInitializerStreamConsumptionResult,
        initial_state: _lineage.OperationalLineageState,
        *,
        raw64_word_counts: object,
    ) -> CounterKeyedInitializerStreamConsumptionResult:
        """Revalidate a complete result and replay every local stream."""

        self._require_live_binding()
        state, counts = self._preflight_request(initial_state, raw64_word_counts)
        checked = _validate_result_record(result)
        result_fields = _result_fields()
        result_before = _capture_fields(result, result_fields)
        state_fields = _lineage._state_fields()
        state_before = _capture_fields(state, state_fields)
        record_fields = _occurrence_fields()
        record_befores = tuple(
            _capture_fields(record, record_fields) for record in checked.occurrences
        )
        parent_fields = _lineage._occurrence_fields()
        occurrence_befores = tuple(
            _capture_fields(occurrence, parent_fields)
            for occurrence in state.occurrences
        )
        if checked.certificate is not self.certificate:
            raise ValueError("initializer result belongs to another owner")
        if checked.initial_state is not state or checked.final_state is not state:
            raise ValueError("initializer result belongs to another state object")
        if checked.raw64_word_counts != counts:
            raise ValueError("initializer result uses another word-count plan")
        for position, (occurrence, record, count) in enumerate(
            zip(state.occurrences, checked.occurrences, counts)
        ):
            self.validate_occurrence_consumption(
                record,
                occurrence,
                position=position,
                raw64_word_count=count,
            )
        self._require_live_binding()
        _validate_result_record(result)
        self._validate_bootstrap_state(state)
        _require_fields_unchanged(
            result,
            result_fields,
            result_before,
            identity_fields=(
                "certificate",
                "initial_state",
                "final_state",
                "raw64_word_counts",
                "occurrences",
                "occurrence_sha256s",
            ),
            name="initializer result",
        )
        _require_fields_unchanged(
            state,
            state_fields,
            state_before,
            identity_fields=(
                "occurrences",
                "occurrence_sha256s",
                "retired_identifiers",
                "retired_identifier_sha256s",
                "model_configuration",
            ),
            name="initial lineage state",
        )
        for position, (
            occurrence,
            record,
            record_before,
            occurrence_before,
        ) in enumerate(
            zip(
                state.occurrences,
                result.occurrences,
                record_befores,
                occurrence_befores,
            )
        ):
            _validate_occurrence_record(record)
            _lineage._validate_occurrence(occurrence)
            _require_fields_unchanged(
                record,
                record_fields,
                record_before,
                identity_fields=(
                    "certificate",
                    "occurrence",
                    "identifier",
                    "event",
                    "event_model_key",
                    "initializer_stream",
                    "stream_initial_state",
                    "raw64_words",
                    "stream_final_state",
                ),
                name="initializer result occurrence record %d" % position,
            )
            _require_fields_unchanged(
                occurrence,
                parent_fields,
                occurrence_before,
                identity_fields=("identifier", "event", "event_model_key"),
                name="initializer result parent occurrence %d" % position,
            )
        if result.initial_state is not state or result.final_state is not state:
            raise ValueError("initializer result state changed during replay")
        if result.raw64_word_counts != counts:
            raise ValueError("initializer result plan changed during replay")
        return result


def certify_plugin_bridge_counter_keyed_initializer_stream_consumption(
    epoch_owner: _epoch.CounterKeyedOperationalEpochLoop,
    *,
    consumption_policy: object,
    consumption_role_sha256: object,
) -> CounterKeyedInitializerStreamConsumptionOwner:
    """Certify the checkpoint-twenty-five tag-3 prefix successor."""

    if type(consumption_policy) is not str:
        raise TypeError("consumption_policy must be exact text")
    if (
        consumption_policy
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY
    ):
        raise ValueError("only the exported initializer-stream policy is supported")
    role = _thinning._require_sha256(
        consumption_role_sha256,
        name="consumption_role_sha256",
    )
    if type(epoch_owner) is not _epoch.CounterKeyedOperationalEpochLoop:
        raise TypeError("epoch_owner has the wrong exact type")
    checkpoint24 = epoch_owner._require_live_binding()
    contract_owner = epoch_owner.contract_owner
    checkpoint23 = contract_owner._require_live_binding()
    certificate = _make_certificate(
        checkpoint24,
        checkpoint23,
        consumption_role_sha256=role,
    )
    owner = CounterKeyedInitializerStreamConsumptionOwner(
        epoch_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_initializer_stream_consumption(
    epoch_owner: _epoch.CounterKeyedOperationalEpochLoop,
    owner: CounterKeyedInitializerStreamConsumptionOwner,
    *,
    consumption_policy: object,
    consumption_role_sha256: object,
) -> CounterKeyedInitializerStreamConsumptionOwner:
    """Require exact parent identity, role, policy, and live custody."""

    if type(consumption_policy) is not str:
        raise TypeError("consumption_policy must be exact text")
    if (
        consumption_policy
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY
    ):
        raise ValueError("only the exported initializer-stream policy is supported")
    role = _thinning._require_sha256(
        consumption_role_sha256,
        name="consumption_role_sha256",
    )
    if type(owner) is not CounterKeyedInitializerStreamConsumptionOwner:
        raise TypeError("owner has the wrong exact type")
    if owner.epoch_owner is not epoch_owner:
        raise ValueError("initializer-stream owner uses another epoch owner")
    if owner.certificate.consumption_role_sha256 != role:
        raise ValueError("initializer-stream owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_counter_keyed_initializer_stream_consumption_certificate(
    epoch_owner: _epoch.CounterKeyedOperationalEpochLoop,
    owner: CounterKeyedInitializerStreamConsumptionOwner,
    *,
    consumption_policy: object,
    consumption_role_sha256: object,
) -> CounterKeyedInitializerStreamConsumptionCertificate:
    """Return the reconstructed live checkpoint-twenty-five certificate."""

    return require_matching_plugin_bridge_counter_keyed_initializer_stream_consumption(
        epoch_owner,
        owner,
        consumption_policy=consumption_policy,
        consumption_role_sha256=consumption_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE",
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX",
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS",
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_RAW64_WORDS_PER_OCCURRENCE",
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS",
    "CounterKeyedInitializerStreamConsumptionCertificate",
    "CounterKeyedInitializerOccurrenceConsumption",
    "CounterKeyedInitializerStreamConsumptionResult",
    "CounterKeyedInitializerStreamConsumptionOwner",
    "PluginBridgeCounterKeyedInitializerStreamConsumptionError",
    "certify_plugin_bridge_counter_keyed_initializer_stream_consumption",
    "require_matching_plugin_bridge_counter_keyed_initializer_stream_consumption",
    "validate_plugin_bridge_counter_keyed_initializer_stream_consumption_certificate",
]
