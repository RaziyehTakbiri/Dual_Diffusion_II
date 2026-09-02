"""Collision-disjoint global initializer-control raw-prefix custody.

Checkpoint twenty-five consumes occurrence-local tag-3 prefixes only after
lineage serials exist.  This additive successor reserves tag 7 for control
work that must occur before cardinality, event types, and occurrence serials
are known.  For one ``run_id`` and ``initialization_index``, a caller supplies
a bounded, strictly lexicographic plan of
``(stage_index, attempt_index, raw64_word_count)`` triples.  Each triple owns
the direct Philox address

``key=(run_id, 7); counter=(0, initialization_index, stage_index, attempt_index)``.

The returned words are deliberately uninterpreted.  Stage and attempt indices
have no initializer-law semantics here, and the module does not choose a
cardinality, type, event, coordinate, rejection branch, SIR ancestry, or final
lineage.  Reissuing an address replays its prefix.  The contract is procedural
and same-runtime only; it does not claim one-shot use, independence, physical
randomness, portability, or cryptographic authentication.
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
        plugin_bridge_counter_keyed_initializer_stream_consumption as _consumption,
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
            "global initializer control requires the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise


PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-global-initializer-control-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY = (
    "exact-checkpoint25-checkpoint24-checkpoint23-owner-binding;"
    "collision-disjoint-direct-tag7-global-control-domain;"
    "initialization-index-address-coordinate;"
    "strict-lexicographic-stage-attempt-plan;"
    "positive-bounded-raw64-prefix;exact-pre-post-philox-snapshots;"
    "same-runtime-local-prefix-replay;no-upper-counter-carry;"
    "no-caller-rng;uninterpreted-control-words-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE = (
    "same-runtime-procedural-global-initializer-control-prefix-custody;"
    "empty-plan-is-namespace-noop-not-empty-configuration;"
    "not-stage-or-attempt-semantics;not-branch-or-retry-chronology;"
    "not-cardinality-type-event-coordinate-or-configuration-law;"
    "not-reference-conditional-or-tilted-initializer-law;"
    "not-enumeration-rejection-resampling-or-sir;"
    "not-exact-uniform-categorical-integer-or-gaussian-law;"
    "not-tag3-cross-initialization-disjointness-or-payload-coordination;"
    "not-accepted-configuration-to-lineage-mapping;"
    "not-statistical-independence;not-physical-randomness;"
    "not-global-run-id-uniqueness;not-global-one-shot-address-use;"
    "not-append-or-continuation-semantics;"
    "not-brownian-consumption-or-coupling;not-drift;not-path;not-strang;"
    "not-target-or-stationarity;not-liveness;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)

COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL = "global_initializer_control"
COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL = 7
COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT = (
    "key=(run_id,7);counter=(0,initialization_index,stage_index,attempt_index)"
)
COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS = 64
COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM = 4_096
COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS = 65_536

_CERTIFICATE_TOKEN = object()
_ADDRESS_TOKEN = object()
_STREAM_TOKEN = object()
_RECORD_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()
_ZERO_SHA256 = "0" * 64


class PluginBridgeCounterKeyedGlobalInitializerControlError(ArithmeticError):
    """Fail-closed checkpoint-twenty-six control-custody error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    excluded = set(names)
    return {name: value for name, value in values.items() if name not in excluded}


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact bool" % name)
    return value


def _exact_positive_word_count(value: object, *, name: str) -> int:
    count = _lineage._exact_uint64(value, name=name)
    if count == 0:
        raise ValueError("%s must be positive" % name)
    if count > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM:
        raise ValueError("%s exceeds the per-stream maximum bound" % name)
    return count


def _reserved_parent_domain_tags() -> Tuple[Tuple[str, int], ...]:
    checkpoint23 = _lineage._require_domain_tag_mapping()
    expected = checkpoint23 + (
        (
            _epoch.COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH,
            _epoch.COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH,
        ),
    )
    canonical = (
        ("jump_proposal", 1),
        ("terminal_wait", 2),
        ("initializer", 3),
        ("brownian_left", 4),
        ("brownian_right", 5),
        ("operational_epoch", 6),
    )
    if expected != canonical:
        raise ValueError("parent counter-key domain tags changed")
    tags = tuple(tag for _, tag in expected)
    if len(set(tags)) != len(tags):
        raise ValueError("parent counter-key domain tags collide")
    if COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL in tags:
        raise ValueError("global initializer-control tag collides with a parent")
    if COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL in tuple(
        domain for domain, _ in expected
    ):
        raise ValueError("global initializer-control domain collides with a parent")
    return expected


def _require_canonical_domain_tag_tuple(
    values: object,
) -> Tuple[Tuple[str, int], ...]:
    if type(values) is not tuple:
        raise TypeError("reserved_parent_domain_tags must be an exact tuple")
    if len(values) != 6:
        raise ValueError("reserved_parent_domain_tags must contain exactly six pairs")
    checked = []
    for position, entry in enumerate(values):
        if type(entry) is not tuple or len(entry) != 2:
            raise TypeError(
                "reserved_parent_domain_tags[%d] must be an exact pair" % position
            )
        if type(entry[0]) is not str:
            raise TypeError(
                "reserved_parent_domain_tags[%d].domain must be exact text" % position
            )
        tag = _lineage._exact_uint64(
            entry[1], name="reserved_parent_domain_tags[%d].tag" % position
        )
        checked.append((entry[0], tag))
    return tuple(checked)


def _preflight_control_plan(
    control_plan: object,
) -> Tuple[Tuple[Tuple[int, int, int], ...], int]:
    if type(control_plan) is not tuple:
        raise TypeError("control_plan must be an exact tuple")
    if len(control_plan) > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS:
        raise ValueError("control plan exceeds the stream-record bound")
    total = 0
    previous = None
    for position, request in enumerate(control_plan):
        if type(request) is not tuple:
            raise TypeError("control_plan[%d] must be an exact tuple" % position)
        if len(request) != 3:
            raise ValueError(
                "control_plan[%d] must contain exactly three fields" % position
            )
        stage = _lineage._exact_uint64(
            request[0], name="control_plan[%d].stage_index" % position
        )
        attempt = _lineage._exact_uint64(
            request[1], name="control_plan[%d].attempt_index" % position
        )
        count = _exact_positive_word_count(
            request[2], name="control_plan[%d].raw64_word_count" % position
        )
        address_coordinates = (stage, attempt)
        if previous is not None and address_coordinates <= previous:
            raise ValueError(
                "control plan addresses must be strictly lexicographically increasing"
            )
        previous = address_coordinates
        total += count
        if total > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS:
            raise ValueError("control plan exceeds the aggregate raw64 bound")
    return control_plan, total


def _preflight_raw_words(words: object, *, expected: int) -> Tuple[int, ...]:
    if type(words) is not tuple:
        raise TypeError("raw64_words must be an exact tuple")
    if len(words) != expected:
        raise ValueError("raw64 word tuple length differs from its request")
    if len(words) > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM:
        raise ValueError("raw64 word tuple exceeds the per-stream bound")
    checked = []
    for index, word in enumerate(words):
        checked.append(_lineage._exact_uint64(word, name="raw64_words[%d]" % index))
    return tuple(checked)


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


def _runtime_sha256() -> str:
    parent_tags = _reserved_parent_domain_tags()
    if COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL != 7:
        raise ValueError("global initializer-control domain tag changed")
    probe = np.random.Generator(
        np.random.Philox(
            key=np.asarray((5, 7), dtype=np.uint64),
            counter=np.asarray((0, 11, 13, 17), dtype=np.uint64),
        )
    )
    initial = _route_evidence._capture_philox_state(probe)
    words = tuple(
        int(value) for value in np.atleast_1d(probe.bit_generator.random_raw(5))
    )
    final = _route_evidence._capture_philox_state(probe)
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-global-initializer-control-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "policy": PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY,
            "scope": PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE,
            "domain_name": COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL,
            "domain_tag": COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL,
            "address_layout": COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT,
            "control_plan_shape": ("(stage_index,attempt_index,raw64_word_count)"),
            "control_plan_order": ("strict-lexicographic-(stage_index,attempt_index)"),
            "reserved_parent_domain_tags": parent_tags,
            "maximum_stream_records": (
                COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
            ),
            "maximum_words_per_stream": (
                COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
            ),
            "maximum_total_words": (
                COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
            ),
            "probe_initial_sha256": initial.snapshot_sha256,
            "probe_words": words,
            "probe_final_sha256": final.snapshot_sha256,
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedGlobalInitializerControlCertificate:
    """Transitive certificate for the tag-7 global control namespace."""

    schema_version: str
    certificate_scope: str
    control_policy: str
    control_role_sha256: str
    process_parameter_sha256: str
    checkpoint25_certificate: (
        _consumption.CounterKeyedInitializerStreamConsumptionCertificate
    )
    checkpoint25_certificate_sha256: str
    checkpoint25_role_sha256: str
    checkpoint25_runtime_sha256: str
    checkpoint24_certificate_sha256: str
    checkpoint24_role_sha256: str
    checkpoint24_runtime_sha256: str
    checkpoint23_certificate_sha256: str
    checkpoint23_role_sha256: str
    checkpoint23_runtime_sha256: str
    control_runtime_sha256: str
    philox_snapshot_schema_version: str
    rng_bit_generator: str
    global_control_domain: str
    global_control_domain_tag: int
    address_layout: str
    reserved_parent_domain_tags: Tuple[Tuple[str, int], ...]
    maximum_stream_records: int
    maximum_raw64_words_per_stream: int
    maximum_total_raw64_words: int
    exact_checkpoint25_owner_binding_certified: bool
    exact_checkpoint24_owner_binding_certified: bool
    exact_checkpoint23_owner_binding_certified: bool
    collision_disjoint_tag7_domain_certified: bool
    initialization_index_address_coordinate_certified: bool
    exact_direct_control_address_certified: bool
    canonical_control_plan_certified: bool
    within_plan_unique_address_certified: bool
    bounded_work_preflight_certified: bool
    empty_plan_zero_word_certified: bool
    exact_pre_post_snapshot_custody_certified: bool
    same_runtime_prefix_replay_certified: bool
    recorded_upper_counter_limb_preservation_certified: bool
    no_caller_rng_certified: bool
    global_control_stream_consumption_certified: bool
    global_initializer_control_namespace_certified: bool
    stage_semantics_certified: bool
    attempt_semantics_certified: bool
    branch_chronology_semantics_certified: bool
    abandoned_or_retry_address_nonreuse_certified: bool
    global_duplicate_address_use_prevention_certified: bool
    global_run_id_uniqueness_certified: bool
    tag3_cross_initialization_disjointness_certified: bool
    tag3_occurrence_payload_coordination_certified: bool
    tag3_occurrence_stream_consumption_certified: bool
    accepted_configuration_to_lineage_mapping_certified: bool
    occurrence_serial_allocation_certified: bool
    initialization_index_uniqueness_certified: bool
    append_or_continuation_semantics_certified: bool
    event_or_configuration_generation_certified: bool
    cardinality_law_certified: bool
    event_type_law_certified: bool
    coordinate_law_certified: bool
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
            "CounterKeyedGlobalInitializerControlCertificate cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("global-control certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("global-control certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedGlobalInitializerControlCertificate.__annotations__)


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "checkpoint25_certificate", "certificate_sha256")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedGlobalInitializerControlCertificate:
    if type(certificate) is not CounterKeyedGlobalInitializerControlCertificate:
        raise TypeError("certificate has the wrong exact type")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION
        ),
        "certificate_scope": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE
        ),
        "control_policy": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY
        ),
        "global_control_domain": COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL,
        "address_layout": COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT,
    }
    for name, expected in expected_text.items():
        if values[name] != expected or type(values[name]) is not str:
            raise ValueError("global-control certificate %s differs" % name)
    _thinning._require_sha256(
        values["control_role_sha256"], name="certificate.control_role_sha256"
    )
    parent25 = _consumption._validate_certificate(values["checkpoint25_certificate"])
    parent24 = parent25.checkpoint24_certificate
    parent23 = parent25.checkpoint23_certificate
    reserved_tags = _require_canonical_domain_tag_tuple(
        values["reserved_parent_domain_tags"]
    )
    expected_scalars = {
        "process_parameter_sha256": parent25.process_parameter_sha256,
        "checkpoint25_certificate_sha256": parent25.certificate_sha256,
        "checkpoint25_role_sha256": parent25.consumption_role_sha256,
        "checkpoint25_runtime_sha256": parent25.consumption_runtime_sha256,
        "checkpoint24_certificate_sha256": parent24.certificate_sha256,
        "checkpoint24_role_sha256": parent24.epoch_role_sha256,
        "checkpoint24_runtime_sha256": parent24.epoch_runtime_sha256,
        "checkpoint23_certificate_sha256": parent23.certificate_sha256,
        "checkpoint23_role_sha256": parent23.contract_role_sha256,
        "checkpoint23_runtime_sha256": parent23.contract_runtime_sha256,
        "philox_snapshot_schema_version": parent23.philox_snapshot_schema_version,
        "rng_bit_generator": parent23.rng_bit_generator,
        "global_control_domain_tag": (
            COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL
        ),
        "reserved_parent_domain_tags": _reserved_parent_domain_tags(),
        "maximum_stream_records": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_stream": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
        ),
        "maximum_total_raw64_words": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
        ),
    }
    for name, expected in expected_scalars.items():
        if values[name] != expected or type(values[name]) is not type(expected):
            raise ValueError("global-control certificate %s differs" % name)
    if reserved_tags != _reserved_parent_domain_tags():
        raise ValueError("global-control reserved parent domains differ")
    positive = (
        "exact_checkpoint25_owner_binding_certified",
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "collision_disjoint_tag7_domain_certified",
        "initialization_index_address_coordinate_certified",
        "exact_direct_control_address_certified",
        "canonical_control_plan_certified",
        "within_plan_unique_address_certified",
        "bounded_work_preflight_certified",
        "empty_plan_zero_word_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "no_caller_rng_certified",
        "global_control_stream_consumption_certified",
        "global_initializer_control_namespace_certified",
        "passed",
    )
    negative = (
        "stage_semantics_certified",
        "attempt_semantics_certified",
        "branch_chronology_semantics_certified",
        "abandoned_or_retry_address_nonreuse_certified",
        "global_duplicate_address_use_prevention_certified",
        "global_run_id_uniqueness_certified",
        "tag3_cross_initialization_disjointness_certified",
        "tag3_occurrence_payload_coordination_certified",
        "tag3_occurrence_stream_consumption_certified",
        "accepted_configuration_to_lineage_mapping_certified",
        "occurrence_serial_allocation_certified",
        "initialization_index_uniqueness_certified",
        "append_or_continuation_semantics_certified",
        "event_or_configuration_generation_certified",
        "cardinality_law_certified",
        "event_type_law_certified",
        "coordinate_law_certified",
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
            raise ValueError("global-control positive claim %s differs" % name)
    for name in negative:
        if _exact_bool(values[name], name="certificate.%s" % name) is not False:
            raise ValueError("global-control negative claim %s differs" % name)
    for name in ("control_runtime_sha256", "certificate_sha256"):
        _thinning._require_sha256(values[name], name="certificate.%s" % name)
    if values["control_runtime_sha256"] != _runtime_sha256():
        raise ValueError("global-control certificate runtime differs")
    expected_digest = _thinning._semantic_digest(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("global-control certificate digest differs")
    return certificate


def _make_certificate(
    parent25: _consumption.CounterKeyedInitializerStreamConsumptionCertificate,
    *,
    control_role_sha256: str,
) -> CounterKeyedGlobalInitializerControlCertificate:
    checked25 = _consumption._validate_certificate(parent25)
    parent24 = checked25.checkpoint24_certificate
    parent23 = checked25.checkpoint23_certificate
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION
        ),
        "certificate_scope": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE
        ),
        "control_policy": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY
        ),
        "control_role_sha256": control_role_sha256,
        "process_parameter_sha256": checked25.process_parameter_sha256,
        "checkpoint25_certificate": parent25,
        "checkpoint25_certificate_sha256": checked25.certificate_sha256,
        "checkpoint25_role_sha256": checked25.consumption_role_sha256,
        "checkpoint25_runtime_sha256": checked25.consumption_runtime_sha256,
        "checkpoint24_certificate_sha256": parent24.certificate_sha256,
        "checkpoint24_role_sha256": parent24.epoch_role_sha256,
        "checkpoint24_runtime_sha256": parent24.epoch_runtime_sha256,
        "checkpoint23_certificate_sha256": parent23.certificate_sha256,
        "checkpoint23_role_sha256": parent23.contract_role_sha256,
        "checkpoint23_runtime_sha256": parent23.contract_runtime_sha256,
        "control_runtime_sha256": _runtime_sha256(),
        "philox_snapshot_schema_version": parent23.philox_snapshot_schema_version,
        "rng_bit_generator": parent23.rng_bit_generator,
        "global_control_domain": COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL,
        "global_control_domain_tag": (
            COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL
        ),
        "address_layout": COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT,
        "reserved_parent_domain_tags": _reserved_parent_domain_tags(),
        "maximum_stream_records": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_stream": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
        ),
        "maximum_total_raw64_words": (
            COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
        ),
        "certificate_sha256": _ZERO_SHA256,
    }
    positive = (
        "exact_checkpoint25_owner_binding_certified",
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "collision_disjoint_tag7_domain_certified",
        "initialization_index_address_coordinate_certified",
        "exact_direct_control_address_certified",
        "canonical_control_plan_certified",
        "within_plan_unique_address_certified",
        "bounded_work_preflight_certified",
        "empty_plan_zero_word_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "no_caller_rng_certified",
        "global_control_stream_consumption_certified",
        "global_initializer_control_namespace_certified",
        "passed",
    )
    boolean_fields = tuple(
        name
        for name in CounterKeyedGlobalInitializerControlCertificate.__annotations__
        if name.endswith("certified") or name.endswith("admissible")
    )
    for name in boolean_fields:
        values[name] = name in positive
    for name in (
        "analytic_target_preserved",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        values[name] = False
    values["passed"] = True
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return CounterKeyedGlobalInitializerControlCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedGlobalInitializerControlAddress:
    """One direct tag-7 address before occurrence serials exist."""

    schema_version: str
    certificate_sha256: str
    domain: str
    domain_tag: int
    run_id: int
    initialization_index: int
    stage_index: int
    attempt_index: int
    philox_key: Tuple[int, int]
    philox_counter: Tuple[int, int, int, int]
    address_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedGlobalInitializerControlAddress cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ADDRESS_TOKEN:
            raise TypeError("global-control addresses are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("global-control address fields are incomplete")
        if values["schema_version"] != (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION
        ):
            raise ValueError("global-control address schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="address.certificate_sha256"
        )
        if values["domain"] != COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL:
            raise ValueError("global-control address domain differs")
        tag = _lineage._exact_uint64(values["domain_tag"], name="address.domain_tag")
        if tag != COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL:
            raise ValueError("global-control address tag differs")
        run_id = _lineage._exact_uint64(values["run_id"], name="address.run_id")
        initialization_index = _lineage._exact_uint64(
            values["initialization_index"], name="address.initialization_index"
        )
        stage_index = _lineage._exact_uint64(
            values["stage_index"], name="address.stage_index"
        )
        attempt_index = _lineage._exact_uint64(
            values["attempt_index"], name="address.attempt_index"
        )
        expected_key = (run_id, COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL)
        expected_counter = (
            0,
            initialization_index,
            stage_index,
            attempt_index,
        )
        if type(values["philox_key"]) is not tuple:
            raise TypeError("address.philox_key must be an exact tuple")
        if type(values["philox_counter"]) is not tuple:
            raise TypeError("address.philox_counter must be an exact tuple")
        if values["philox_key"] != expected_key:
            raise ValueError("global-control key differs from its address")
        if values["philox_counter"] != expected_counter:
            raise ValueError("global-control counter differs from its address")
        for index, word in enumerate(values["philox_key"]):
            _lineage._exact_uint64(word, name="address.philox_key[%d]" % index)
        for index, word in enumerate(values["philox_counter"]):
            _lineage._exact_uint64(word, name="address.philox_counter[%d]" % index)
        _thinning._require_sha256(
            values["address_sha256"], name="address.address_sha256"
        )
        expected_digest = _thinning._semantic_digest(_without(values, "address_sha256"))
        if values["address_sha256"] != expected_digest:
            raise ValueError("global-control address digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control addresses are not pickle objects")


def _address_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedGlobalInitializerControlAddress.__annotations__)


def _validate_address(
    address: object,
) -> CounterKeyedGlobalInitializerControlAddress:
    if type(address) is not CounterKeyedGlobalInitializerControlAddress:
        raise TypeError("address has the wrong exact global-control type")
    return CounterKeyedGlobalInitializerControlAddress(
        **{name: getattr(address, name) for name in _address_fields()},
        _construction_token=_ADDRESS_TOKEN,
    )


def _make_address(
    certificate: CounterKeyedGlobalInitializerControlCertificate,
    *,
    run_id: int,
    initialization_index: int,
    stage_index: int,
    attempt_index: int,
) -> CounterKeyedGlobalInitializerControlAddress:
    checked = _validate_certificate(certificate)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION
        ),
        "certificate_sha256": checked.certificate_sha256,
        "domain": COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL,
        "domain_tag": COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "stage_index": stage_index,
        "attempt_index": attempt_index,
        "philox_key": (
            run_id,
            COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL,
        ),
        "philox_counter": (
            0,
            initialization_index,
            stage_index,
            attempt_index,
        ),
        "address_sha256": _ZERO_SHA256,
    }
    values["address_sha256"] = _thinning._semantic_digest(
        _without(values, "address_sha256")
    )
    return CounterKeyedGlobalInitializerControlAddress(
        **values, _construction_token=_ADDRESS_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedGlobalInitializerControlStream:
    """Initially unused same-runtime Philox receipt for one tag-7 address."""

    certificate: CounterKeyedGlobalInitializerControlCertificate
    certificate_sha256: str
    address: CounterKeyedGlobalInitializerControlAddress
    address_sha256: str
    initial_state: _route_evidence.PhiloxRouteStateSnapshot
    initial_snapshot_sha256: str
    initial_state_sha256: str
    buffer_is_zero: bool
    uint32_cache_is_zero: bool
    parent_execution_used_this_stream: bool
    same_runtime_only: bool
    stream_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedGlobalInitializerControlStream cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _STREAM_TOKEN:
            raise TypeError("global-control streams are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("global-control stream fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("global-control stream certificate differs")
        address = _validate_address(values["address"])
        if address.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("global-control address has another certificate")
        if values["address_sha256"] != address.address_sha256:
            raise ValueError("global-control address digest differs")
        snapshot = _route_evidence._validate_snapshot(values["initial_state"])
        if values["initial_snapshot_sha256"] != snapshot.snapshot_sha256:
            raise ValueError("global-control initial snapshot digest differs")
        if values["initial_state_sha256"] != snapshot.state_sha256:
            raise ValueError("global-control initial state digest differs")
        if snapshot.key != address.philox_key:
            raise ValueError("global-control initial key differs")
        if snapshot.counter != address.philox_counter:
            raise ValueError("global-control initial counter differs")
        if snapshot.buffer != (0, 0, 0, 0) or snapshot.buffer_pos != 4:
            raise ValueError("global-control initial buffer is not empty")
        if snapshot.has_uint32 != 0 or snapshot.uinteger != 0:
            raise ValueError("global-control initial uint32 cache is not empty")
        expected_flags = {
            "buffer_is_zero": True,
            "uint32_cache_is_zero": True,
            "parent_execution_used_this_stream": False,
            "same_runtime_only": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="stream.%s" % name) is not expected:
                raise ValueError("global-control stream flag %s differs" % name)
        for name in (
            "certificate_sha256",
            "address_sha256",
            "initial_snapshot_sha256",
            "initial_state_sha256",
            "stream_sha256",
        ):
            _thinning._require_sha256(values[name], name="stream.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "address",
                "initial_state",
                "stream_sha256",
            )
        )
        if values["stream_sha256"] != expected_digest:
            raise ValueError("global-control stream digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control streams are not pickle objects")


def _stream_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedGlobalInitializerControlStream.__annotations__)


def _validate_stream_record(
    stream: object,
) -> CounterKeyedGlobalInitializerControlStream:
    if type(stream) is not CounterKeyedGlobalInitializerControlStream:
        raise TypeError("stream has the wrong exact global-control type")
    return CounterKeyedGlobalInitializerControlStream(
        **{name: getattr(stream, name) for name in _stream_fields()},
        _construction_token=_STREAM_TOKEN,
    )


def _make_stream(
    certificate: CounterKeyedGlobalInitializerControlCertificate,
    address: CounterKeyedGlobalInitializerControlAddress,
) -> CounterKeyedGlobalInitializerControlStream:
    checked_certificate = _validate_certificate(certificate)
    checked_address = _validate_address(address)
    if checked_address.certificate_sha256 != checked_certificate.certificate_sha256:
        raise ValueError("global-control address belongs to another certificate")
    bit_generator = np.random.Philox(
        key=np.asarray(checked_address.philox_key, dtype=np.uint64),
        counter=np.asarray(checked_address.philox_counter, dtype=np.uint64),
    )
    snapshot = _route_evidence._capture_philox_state(np.random.Generator(bit_generator))
    values: Dict[str, object] = {
        "certificate": checked_certificate,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "address": checked_address,
        "address_sha256": checked_address.address_sha256,
        "initial_state": snapshot,
        "initial_snapshot_sha256": snapshot.snapshot_sha256,
        "initial_state_sha256": snapshot.state_sha256,
        "buffer_is_zero": True,
        "uint32_cache_is_zero": True,
        "parent_execution_used_this_stream": False,
        "same_runtime_only": True,
        "stream_sha256": _ZERO_SHA256,
    }
    values["stream_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "address",
            "initial_state",
            "stream_sha256",
        )
    )
    return CounterKeyedGlobalInitializerControlStream(
        **values, _construction_token=_STREAM_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedGlobalInitializerControlConsumption:
    """One exact raw64 prefix from one global control address."""

    certificate: CounterKeyedGlobalInitializerControlCertificate
    certificate_sha256: str
    position: int
    run_id: int
    initialization_index: int
    stage_index: int
    attempt_index: int
    raw64_word_count: int
    control_stream: CounterKeyedGlobalInitializerControlStream
    control_stream_sha256: str
    control_address_sha256: str
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
    no_upper_counter_carry: bool
    same_runtime_only: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedGlobalInitializerControlConsumption cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RECORD_TOKEN:
            raise TypeError("global-control consumption records are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("global-control consumption fields are incomplete")
        count = _exact_positive_word_count(
            values["raw64_word_count"], name="record.raw64_word_count"
        )
        _preflight_raw_words(values["raw64_words"], expected=count)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_consumption_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control consumption records are not pickle objects")


def _record_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedGlobalInitializerControlConsumption.__annotations__)


def _record_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "control_stream",
        "stream_initial_state",
        "stream_final_state",
        "record_sha256",
    )


def _validate_consumption_record(
    record: object,
) -> CounterKeyedGlobalInitializerControlConsumption:
    if type(record) is not CounterKeyedGlobalInitializerControlConsumption:
        raise TypeError("record has the wrong exact global-control type")
    values = {name: getattr(record, name) for name in _record_fields()}
    certificate = _validate_certificate(values["certificate"])
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("global-control record certificate digest differs")
    position = _lineage._exact_uint64(values["position"], name="record.position")
    if position >= certificate.maximum_stream_records:
        raise ValueError("global-control record position exceeds the bound")
    run_id = _lineage._exact_uint64(values["run_id"], name="record.run_id")
    initialization_index = _lineage._exact_uint64(
        values["initialization_index"], name="record.initialization_index"
    )
    stage_index = _lineage._exact_uint64(
        values["stage_index"], name="record.stage_index"
    )
    attempt_index = _lineage._exact_uint64(
        values["attempt_index"], name="record.attempt_index"
    )
    count = _exact_positive_word_count(
        values["raw64_word_count"], name="record.raw64_word_count"
    )
    _preflight_raw_words(values["raw64_words"], expected=count)
    if type(values["control_stream"]) is not CounterKeyedGlobalInitializerControlStream:
        raise TypeError("record control stream has the wrong exact type")
    stream = _validate_stream_record(values["control_stream"])
    if stream.certificate is not certificate:
        raise ValueError("record stream has another certificate object")
    if values["control_stream_sha256"] != stream.stream_sha256:
        raise ValueError("record control-stream digest differs")
    if values["control_address_sha256"] != stream.address.address_sha256:
        raise ValueError("record control-address digest differs")
    address = stream.address
    if (
        address.run_id != run_id
        or address.initialization_index != initialization_index
        or address.stage_index != stage_index
        or address.attempt_index != attempt_index
    ):
        raise ValueError("record coordinates differ from its control address")
    if values["stream_initial_state"] is not stream.initial_state:
        raise ValueError("record initial-state identity differs")
    initial = _route_evidence._validate_snapshot(values["stream_initial_state"])
    final = _route_evidence._validate_snapshot(values["stream_final_state"])
    expected_digests = {
        "stream_initial_snapshot_sha256": initial.snapshot_sha256,
        "stream_initial_state_sha256": initial.state_sha256,
        "stream_final_snapshot_sha256": final.snapshot_sha256,
        "stream_final_state_sha256": final.state_sha256,
    }
    for name, expected in expected_digests.items():
        if values[name] != expected:
            raise ValueError("global-control record %s differs" % name)
    expected_flags = {
        "parent_execution_used_this_stream": False,
        "successor_execution_invoked_this_stream": True,
        "successor_execution_consumed_this_stream": True,
        "no_upper_counter_carry": True,
        "same_runtime_only": True,
    }
    for name, expected in expected_flags.items():
        if _exact_bool(values[name], name="record.%s" % name) is not expected:
            raise ValueError("global-control record flag %s differs" % name)
    if stream.parent_execution_used_this_stream is not False:
        raise ValueError("global-control stream parent-use flag differs")
    if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
        raise ValueError("global-control record contains an upper counter carry")
    for name in (
        "certificate_sha256",
        "control_stream_sha256",
        "control_address_sha256",
        "stream_initial_snapshot_sha256",
        "stream_initial_state_sha256",
        "stream_final_snapshot_sha256",
        "stream_final_state_sha256",
        "record_sha256",
    ):
        _thinning._require_sha256(values[name], name="record.%s" % name)
    expected_digest = _thinning._semantic_digest(_record_payload(values))
    if values["record_sha256"] != expected_digest:
        raise ValueError("global-control record digest differs")
    return record


def _make_consumption_record(
    certificate: CounterKeyedGlobalInitializerControlCertificate,
    stream: CounterKeyedGlobalInitializerControlStream,
    final_state: _route_evidence.PhiloxRouteStateSnapshot,
    raw64_words: Tuple[int, ...],
    *,
    position: int,
) -> CounterKeyedGlobalInitializerControlConsumption:
    address = stream.address
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "position": position,
        "run_id": address.run_id,
        "initialization_index": address.initialization_index,
        "stage_index": address.stage_index,
        "attempt_index": address.attempt_index,
        "raw64_word_count": len(raw64_words),
        "control_stream": stream,
        "control_stream_sha256": stream.stream_sha256,
        "control_address_sha256": address.address_sha256,
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
        "no_upper_counter_carry": True,
        "same_runtime_only": True,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _thinning._semantic_digest(_record_payload(values))
    return CounterKeyedGlobalInitializerControlConsumption(
        **values, _construction_token=_RECORD_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedGlobalInitializerControlResult:
    """Complete ordered raw-prefix transcript for one canonical control plan."""

    certificate: CounterKeyedGlobalInitializerControlCertificate
    certificate_sha256: str
    run_id: int
    initialization_index: int
    control_plan: Tuple[Tuple[int, int, int], ...]
    consumptions: Tuple[CounterKeyedGlobalInitializerControlConsumption, ...]
    consumption_sha256s: Tuple[str, ...]
    total_raw64_words: int
    stream_count: int
    empty_plan_zero_word: bool
    canonical_control_plan: bool
    within_plan_unique_addresses: bool
    all_requested_streams_consumed: bool
    no_caller_rng: bool
    same_runtime_only: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedGlobalInitializerControlResult cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("global-control results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("global-control result fields are incomplete")
        _preflight_control_plan(values["control_plan"])
        if type(values["consumptions"]) is not tuple:
            raise TypeError("result consumptions must be an exact tuple")
        if type(values["consumption_sha256s"]) is not tuple:
            raise TypeError("result consumption digests must be an exact tuple")
        if (
            len(values["consumptions"])
            > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
        ):
            raise ValueError("result consumption tuple exceeds its bound")
        if len(values["consumption_sha256s"]) != len(values["consumptions"]):
            raise ValueError("result consumption digest count differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_result_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedGlobalInitializerControlResult.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "consumptions", "result_sha256")


def _validate_result_record(
    result: object,
) -> CounterKeyedGlobalInitializerControlResult:
    if type(result) is not CounterKeyedGlobalInitializerControlResult:
        raise TypeError("result has the wrong exact global-control type")
    values = {name: getattr(result, name) for name in _result_fields()}
    certificate = _validate_certificate(values["certificate"])
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("global-control result certificate digest differs")
    run_id = _lineage._exact_uint64(values["run_id"], name="result.run_id")
    initialization_index = _lineage._exact_uint64(
        values["initialization_index"], name="result.initialization_index"
    )
    plan, total = _preflight_control_plan(values["control_plan"])
    if type(values["consumptions"]) is not tuple:
        raise TypeError("result consumptions must be an exact tuple")
    if len(values["consumptions"]) != len(plan):
        raise ValueError("global-control result coverage differs from its plan")
    records = tuple(
        _validate_consumption_record(record) for record in values["consumptions"]
    )
    if type(values["consumption_sha256s"]) is not tuple:
        raise TypeError("result consumption digests must be an exact tuple")
    if len(values["consumption_sha256s"]) != len(records):
        raise ValueError("global-control result digest count differs")
    expected_digests = tuple(record.record_sha256 for record in records)
    if values["consumption_sha256s"] != expected_digests:
        raise ValueError("global-control result digest order differs")
    if values["total_raw64_words"] != total:
        raise ValueError("global-control result total word count differs")
    if type(values["total_raw64_words"]) is not int:
        raise TypeError("result total word count must be an exact integer")
    if values["stream_count"] != len(records):
        raise ValueError("global-control result stream count differs")
    if type(values["stream_count"]) is not int:
        raise TypeError("result stream count must be an exact integer")
    for position, (entry, record) in enumerate(zip(plan, records)):
        stage, attempt, count = entry
        if record.certificate is not certificate:
            raise ValueError("global-control result record has another certificate")
        if record.position != position:
            raise ValueError("global-control result record position differs")
        if (
            record.run_id != run_id
            or record.initialization_index != initialization_index
            or record.stage_index != stage
            or record.attempt_index != attempt
            or record.raw64_word_count != count
        ):
            raise ValueError("global-control result record differs from its plan")
    expected_flags = {
        "empty_plan_zero_word": len(plan) == 0,
        "canonical_control_plan": True,
        "within_plan_unique_addresses": True,
        "all_requested_streams_consumed": True,
        "no_caller_rng": True,
        "same_runtime_only": True,
    }
    for name, expected in expected_flags.items():
        if _exact_bool(values[name], name="result.%s" % name) is not expected:
            raise ValueError("global-control result flag %s differs" % name)
    for name in ("certificate_sha256", "result_sha256"):
        _thinning._require_sha256(values[name], name="result.%s" % name)
    expected_digest = _thinning._semantic_digest(_result_payload(values))
    if values["result_sha256"] != expected_digest:
        raise ValueError("global-control result digest differs")
    return result


def _make_result(
    certificate: CounterKeyedGlobalInitializerControlCertificate,
    *,
    run_id: int,
    initialization_index: int,
    control_plan: Tuple[Tuple[int, int, int], ...],
    records: Tuple[CounterKeyedGlobalInitializerControlConsumption, ...],
) -> CounterKeyedGlobalInitializerControlResult:
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "control_plan": control_plan,
        "consumptions": records,
        "consumption_sha256s": tuple(record.record_sha256 for record in records),
        "total_raw64_words": sum(entry[2] for entry in control_plan),
        "stream_count": len(records),
        "empty_plan_zero_word": len(records) == 0,
        "canonical_control_plan": True,
        "within_plan_unique_addresses": True,
        "all_requested_streams_consumed": True,
        "no_caller_rng": True,
        "same_runtime_only": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _thinning._semantic_digest(_result_payload(values))
    return CounterKeyedGlobalInitializerControlResult(
        **values, _construction_token=_RESULT_TOKEN
    )


class CounterKeyedGlobalInitializerControlOwner:
    """Immutable owner of checkpoint-twenty-six tag-7 prefix custody."""

    __slots__ = (
        "_consumption_owner",
        "_certified_consumption_owner",
        "_epoch_owner",
        "_certified_epoch_owner",
        "_contract_owner",
        "_certified_contract_owner",
        "_control_role_sha256",
        "_certified_control_role_sha256",
        "_certificate",
        "_certified_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedGlobalInitializerControlOwner cannot be subclassed"
        )

    def __init__(
        self,
        consumption_owner: (_consumption.CounterKeyedInitializerStreamConsumptionOwner),
        control_role_sha256: str,
        certificate: CounterKeyedGlobalInitializerControlCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("global-control owners require certification")
        if type(consumption_owner) is not (
            _consumption.CounterKeyedInitializerStreamConsumptionOwner
        ):
            raise TypeError("consumption_owner has the wrong exact type")
        role = _thinning._require_sha256(
            control_role_sha256, name="control_role_sha256"
        )
        checked = _validate_certificate(certificate)
        if checked.control_role_sha256 != role:
            raise ValueError("global-control role differs from certificate")
        epoch_owner = consumption_owner.epoch_owner
        contract_owner = consumption_owner.contract_owner
        object.__setattr__(self, "_consumption_owner", consumption_owner)
        object.__setattr__(self, "_certified_consumption_owner", consumption_owner)
        object.__setattr__(self, "_epoch_owner", epoch_owner)
        object.__setattr__(self, "_certified_epoch_owner", epoch_owner)
        object.__setattr__(self, "_contract_owner", contract_owner)
        object.__setattr__(self, "_certified_contract_owner", contract_owner)
        object.__setattr__(self, "_control_role_sha256", role)
        object.__setattr__(self, "_certified_control_role_sha256", role)
        object.__setattr__(self, "_certificate", checked)
        object.__setattr__(self, "_certified_certificate", checked)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("global-control owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("global-control owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("global-control owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedGlobalInitializerControlCertificate:
        return self._certificate

    @property
    def consumption_owner(
        self,
    ) -> _consumption.CounterKeyedInitializerStreamConsumptionOwner:
        return self._consumption_owner

    @property
    def epoch_owner(self) -> _epoch.CounterKeyedOperationalEpochLoop:
        return self._epoch_owner

    @property
    def contract_owner(self) -> _lineage.CounterKeyedLineageContractOwner:
        return self._contract_owner

    def _require_live_binding(
        self,
    ) -> CounterKeyedGlobalInitializerControlCertificate:
        _thinning._require_binary64_environment()
        if type(self._consumption_owner) is not (
            _consumption.CounterKeyedInitializerStreamConsumptionOwner
        ):
            raise TypeError("global-control checkpoint-25 owner has the wrong type")
        if self._consumption_owner is not self._certified_consumption_owner:
            raise ValueError("global-control checkpoint-25 owner binding changed")
        if self._consumption_owner.epoch_owner is not self._epoch_owner:
            raise ValueError("global-control checkpoint-24 binding changed")
        if self._consumption_owner.contract_owner is not self._contract_owner:
            raise ValueError("global-control checkpoint-23 binding changed")
        if self._epoch_owner is not self._certified_epoch_owner:
            raise ValueError("global-control cached checkpoint-24 owner changed")
        if self._contract_owner is not self._certified_contract_owner:
            raise ValueError("global-control cached checkpoint-23 owner changed")
        if self._control_role_sha256 != self._certified_control_role_sha256:
            raise ValueError("global-control certified role changed")
        if self._certificate is not self._certified_certificate:
            raise ValueError("global-control certified certificate object changed")
        checkpoint25 = self._consumption_owner._require_live_binding()
        checkpoint24 = self._epoch_owner.certificate
        checkpoint23 = self._contract_owner.certificate
        if checkpoint25.checkpoint24_certificate is not checkpoint24:
            raise ValueError("global-control checkpoint-24 certificate changed")
        if checkpoint25.checkpoint23_certificate is not checkpoint23:
            raise ValueError("global-control checkpoint-23 certificate changed")
        if self.certificate.checkpoint25_certificate is not checkpoint25:
            raise ValueError("global-control checkpoint-25 certificate changed")
        if self.certificate.control_runtime_sha256 != _runtime_sha256():
            raise ValueError("live global-control runtime differs")
        expected = _make_certificate(
            checkpoint25,
            control_role_sha256=self._control_role_sha256,
        )
        for name in _certificate_fields():
            actual_value = getattr(self.certificate, name)
            expected_value = getattr(expected, name)
            if name == "checkpoint25_certificate":
                if actual_value is not expected_value:
                    raise ValueError(
                        "global-control parent certificate identity changed"
                    )
            elif not _thinning._field_matches(name, actual_value, expected_value):
                raise ValueError("global-control certificate field %s differs" % name)
        _thinning._require_binary64_environment()
        return self.certificate

    def _preflight_request(
        self,
        run_id: object,
        initialization_index: object,
        control_plan: object,
    ) -> Tuple[int, int, Tuple[Tuple[int, int, int], ...]]:
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        checked_plan, _ = _preflight_control_plan(control_plan)
        return checked_run, checked_initialization, checked_plan

    def _make_control_stream(
        self,
        *,
        run_id: int,
        initialization_index: int,
        stage_index: int,
        attempt_index: int,
    ) -> CounterKeyedGlobalInitializerControlStream:
        address = _make_address(
            self.certificate,
            run_id=run_id,
            initialization_index=initialization_index,
            stage_index=stage_index,
            attempt_index=attempt_index,
        )
        return _make_stream(self.certificate, address)

    def validate_control_stream(
        self,
        stream: CounterKeyedGlobalInitializerControlStream,
        *,
        run_id: object,
        initialization_index: object,
        stage_index: object,
        attempt_index: object,
    ) -> CounterKeyedGlobalInitializerControlStream:
        """Validate and reconstruct one initially unused direct receipt."""

        self._require_live_binding()
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        checked_stage = _lineage._exact_uint64(stage_index, name="stage_index")
        checked_attempt = _lineage._exact_uint64(attempt_index, name="attempt_index")
        checked = _validate_stream_record(stream)
        stream_fields = _stream_fields()
        stream_before = _capture_fields(stream, stream_fields)
        if checked.certificate is not self.certificate:
            raise ValueError("global-control stream belongs to another owner")
        address = checked.address
        address_fields = _address_fields()
        address_before = _capture_fields(address, address_fields)
        if (
            address.run_id != checked_run
            or address.initialization_index != checked_initialization
            or address.stage_index != checked_stage
            or address.attempt_index != checked_attempt
        ):
            raise ValueError("global-control stream coordinates differ")
        generator = _route_evidence._generator_from_snapshot(checked.initial_state)
        reconstructed = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(reconstructed, checked.initial_state):
            raise PluginBridgeCounterKeyedGlobalInitializerControlError(
                "global-control initial state did not reconstruct"
            )
        self._require_live_binding()
        _validate_stream_record(stream)
        _require_fields_unchanged(
            stream,
            stream_fields,
            stream_before,
            identity_fields=("certificate", "address", "initial_state"),
            name="global-control stream",
        )
        _require_fields_unchanged(
            address,
            address_fields,
            address_before,
            identity_fields=("philox_key", "philox_counter"),
            name="global-control stream address",
        )
        if stream.address is not address:
            raise ValueError("global-control stream address custody changed")
        return stream

    def reconstruct_control_stream(
        self,
        stream: CounterKeyedGlobalInitializerControlStream,
        *,
        run_id: object,
        initialization_index: object,
        stage_index: object,
        attempt_index: object,
    ) -> np.random.Generator:
        """Return a fresh local Philox generator at one validated receipt."""

        if type(stream) is not CounterKeyedGlobalInitializerControlStream:
            raise TypeError("stream has the wrong exact global-control type")
        stream_fields = _stream_fields()
        stream_before = _capture_fields(stream, stream_fields)
        address = stream.address
        address_fields = _address_fields()
        address_before = _capture_fields(address, address_fields)
        self.validate_control_stream(
            stream,
            run_id=run_id,
            initialization_index=initialization_index,
            stage_index=stage_index,
            attempt_index=attempt_index,
        )
        generator = _route_evidence._generator_from_snapshot(stream.initial_state)
        reconstructed = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(reconstructed, stream.initial_state):
            raise PluginBridgeCounterKeyedGlobalInitializerControlError(
                "fresh global-control stream differs from its receipt"
            )
        self._require_live_binding()
        _validate_stream_record(stream)
        _require_fields_unchanged(
            stream,
            stream_fields,
            stream_before,
            identity_fields=("certificate", "address", "initial_state"),
            name="reconstructed global-control stream",
        )
        _require_fields_unchanged(
            address,
            address_fields,
            address_before,
            identity_fields=("philox_key", "philox_counter"),
            name="reconstructed global-control address",
        )
        if stream.address is not address:
            raise ValueError("reconstructed global-control address changed")
        return generator

    def validate_stream_consumption(
        self,
        record: CounterKeyedGlobalInitializerControlConsumption,
        *,
        position: object,
        plan_entry: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedGlobalInitializerControlConsumption:
        """Deeply replay one exact tag-7 raw-prefix record."""

        checked_position = _lineage._exact_uint64(position, name="position")
        if checked_position >= self.certificate.maximum_stream_records:
            raise ValueError("position exceeds the stream-record bound")
        if type(plan_entry) is not tuple:
            raise TypeError("plan_entry must be an exact tuple")
        if len(plan_entry) != 3:
            raise ValueError("plan_entry must contain exactly three fields")
        stage = _lineage._exact_uint64(plan_entry[0], name="plan_entry.stage_index")
        attempt = _lineage._exact_uint64(plan_entry[1], name="plan_entry.attempt_index")
        count = _exact_positive_word_count(
            plan_entry[2], name="plan_entry.raw64_word_count"
        )
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        checked = _validate_consumption_record(record)
        record_fields = _record_fields()
        record_before = _capture_fields(record, record_fields)
        if checked.certificate is not self.certificate:
            raise ValueError("global-control record belongs to another owner")
        if checked.position != checked_position:
            raise ValueError("global-control record position differs")
        if (
            checked.run_id != checked_run
            or checked.initialization_index != checked_initialization
            or checked.stage_index != stage
            or checked.attempt_index != attempt
            or checked.raw64_word_count != count
        ):
            raise ValueError("global-control record differs from its plan entry")
        stream = checked.control_stream
        stream_fields = _stream_fields()
        stream_before = _capture_fields(stream, stream_fields)
        address = stream.address
        address_fields = _address_fields()
        address_before = _capture_fields(address, address_fields)
        self.validate_control_stream(
            stream,
            run_id=checked_run,
            initialization_index=checked_initialization,
            stage_index=stage,
            attempt_index=attempt,
        )
        generator = _route_evidence._generator_from_snapshot(stream.initial_state)
        initial = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(initial, checked.stream_initial_state):
            raise ValueError("global-control replay initial snapshot differs")
        replay_words = tuple(
            int(value)
            for value in np.atleast_1d(generator.bit_generator.random_raw(count))
        )
        final = _route_evidence._capture_philox_state(generator)
        if replay_words != checked.raw64_words:
            raise ValueError("global-control raw64 prefix did not replay")
        if not _snapshot_matches(final, checked.stream_final_state):
            raise ValueError("global-control final snapshot did not replay")
        if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
            raise PluginBridgeCounterKeyedGlobalInitializerControlError(
                "global-control prefix carried into an upper address limb"
            )
        self._require_live_binding()
        _validate_consumption_record(record)
        _require_fields_unchanged(
            record,
            record_fields,
            record_before,
            identity_fields=(
                "certificate",
                "control_stream",
                "stream_initial_state",
                "raw64_words",
                "stream_final_state",
            ),
            name="global-control consumption record",
        )
        _require_fields_unchanged(
            stream,
            stream_fields,
            stream_before,
            identity_fields=("certificate", "address", "initial_state"),
            name="global-control consumption stream",
        )
        _require_fields_unchanged(
            address,
            address_fields,
            address_before,
            identity_fields=("philox_key", "philox_counter"),
            name="global-control consumption address",
        )
        if record.control_stream is not stream or stream.address is not address:
            raise ValueError("global-control nested stream custody changed")
        if record.position != checked_position:
            raise ValueError("global-control record position changed during replay")
        return record

    def consume(
        self,
        run_id: object,
        initialization_index: object,
        *,
        control_plan: object,
    ) -> CounterKeyedGlobalInitializerControlResult:
        """Consume one bounded local raw64 prefix per canonical plan entry."""

        self._require_live_binding()
        checked_run, checked_initialization, plan = self._preflight_request(
            run_id, initialization_index, control_plan
        )
        records = []
        for position, (stage, attempt, count) in enumerate(plan):
            stream = self._make_control_stream(
                run_id=checked_run,
                initialization_index=checked_initialization,
                stage_index=stage,
                attempt_index=attempt,
            )
            generator = _route_evidence._generator_from_snapshot(stream.initial_state)
            initial = _route_evidence._capture_philox_state(generator)
            if not _snapshot_matches(initial, stream.initial_state):
                raise ValueError("global-control stream did not start at its receipt")
            words = tuple(
                int(value)
                for value in np.atleast_1d(generator.bit_generator.random_raw(count))
            )
            final = _route_evidence._capture_philox_state(generator)
            if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
                raise PluginBridgeCounterKeyedGlobalInitializerControlError(
                    "global-control prefix carried into an upper address limb"
                )
            record = _make_consumption_record(
                self.certificate,
                stream,
                final,
                words,
                position=position,
            )
            records.append(record)
        result = _make_result(
            self.certificate,
            run_id=checked_run,
            initialization_index=checked_initialization,
            control_plan=plan,
            records=tuple(records),
        )
        self.validate_result(
            result,
            checked_run,
            checked_initialization,
            control_plan=plan,
        )
        return result

    def validate_result(
        self,
        result: CounterKeyedGlobalInitializerControlResult,
        run_id: object,
        initialization_index: object,
        *,
        control_plan: object,
    ) -> CounterKeyedGlobalInitializerControlResult:
        """Revalidate a complete result and replay every local stream."""

        self._require_live_binding()
        checked_run, checked_initialization, plan = self._preflight_request(
            run_id, initialization_index, control_plan
        )
        if type(result) is not CounterKeyedGlobalInitializerControlResult:
            raise TypeError("result has the wrong exact global-control type")
        if type(result.consumptions) is not tuple:
            raise TypeError("result consumptions must be an exact tuple")
        if (
            len(result.consumptions)
            > COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
        ):
            raise ValueError("result consumption tuple exceeds its bound")
        checked = _validate_result_record(result)
        result_fields = _result_fields()
        result_before = _capture_fields(result, result_fields)
        record_fields = _record_fields()
        record_befores = tuple(
            _capture_fields(record, record_fields) for record in checked.consumptions
        )
        streams = tuple(record.control_stream for record in checked.consumptions)
        stream_fields = _stream_fields()
        stream_befores = tuple(
            _capture_fields(stream, stream_fields) for stream in streams
        )
        addresses = tuple(stream.address for stream in streams)
        address_fields = _address_fields()
        address_befores = tuple(
            _capture_fields(address, address_fields) for address in addresses
        )
        if checked.certificate is not self.certificate:
            raise ValueError("global-control result belongs to another owner")
        if checked.run_id != checked_run:
            raise ValueError("global-control result uses another run")
        if checked.initialization_index != checked_initialization:
            raise ValueError("global-control result uses another initialization")
        if checked.control_plan != plan:
            raise ValueError("global-control result uses another control plan")
        for position, (entry, record) in enumerate(zip(plan, checked.consumptions)):
            self.validate_stream_consumption(
                record,
                position=position,
                plan_entry=entry,
                run_id=checked_run,
                initialization_index=checked_initialization,
            )
        self._require_live_binding()
        _validate_result_record(result)
        _require_fields_unchanged(
            result,
            result_fields,
            result_before,
            identity_fields=(
                "certificate",
                "control_plan",
                "consumptions",
                "consumption_sha256s",
            ),
            name="global-control result",
        )
        for position, (
            record,
            record_before,
            stream,
            stream_before,
            address,
            address_before,
        ) in enumerate(
            zip(
                result.consumptions,
                record_befores,
                streams,
                stream_befores,
                addresses,
                address_befores,
            )
        ):
            _validate_consumption_record(record)
            _require_fields_unchanged(
                record,
                record_fields,
                record_before,
                identity_fields=(
                    "certificate",
                    "control_stream",
                    "stream_initial_state",
                    "raw64_words",
                    "stream_final_state",
                ),
                name="global-control result record %d" % position,
            )
            _require_fields_unchanged(
                stream,
                stream_fields,
                stream_before,
                identity_fields=("certificate", "address", "initial_state"),
                name="global-control result stream %d" % position,
            )
            _require_fields_unchanged(
                address,
                address_fields,
                address_before,
                identity_fields=("philox_key", "philox_counter"),
                name="global-control result address %d" % position,
            )
            if record.control_stream is not stream or stream.address is not address:
                raise ValueError("global-control nested result custody changed")
        if result.control_plan != plan:
            raise ValueError("global-control plan changed during replay")
        return result


def certify_plugin_bridge_counter_keyed_global_initializer_control(
    consumption_owner: _consumption.CounterKeyedInitializerStreamConsumptionOwner,
    *,
    control_policy: object,
    control_role_sha256: object,
) -> CounterKeyedGlobalInitializerControlOwner:
    """Certify the checkpoint-twenty-six tag-7 control successor."""

    if type(control_policy) is not str:
        raise TypeError("control_policy must be exact text")
    if control_policy != PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY:
        raise ValueError("only the exported global-control policy is supported")
    role = _thinning._require_sha256(control_role_sha256, name="control_role_sha256")
    if type(consumption_owner) is not (
        _consumption.CounterKeyedInitializerStreamConsumptionOwner
    ):
        raise TypeError("consumption_owner has the wrong exact type")
    checkpoint25 = consumption_owner._require_live_binding()
    certificate = _make_certificate(
        checkpoint25,
        control_role_sha256=role,
    )
    owner = CounterKeyedGlobalInitializerControlOwner(
        consumption_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_global_initializer_control(
    consumption_owner: _consumption.CounterKeyedInitializerStreamConsumptionOwner,
    owner: CounterKeyedGlobalInitializerControlOwner,
    *,
    control_policy: object,
    control_role_sha256: object,
) -> CounterKeyedGlobalInitializerControlOwner:
    """Require exact checkpoint-25 identity, role, policy, and live custody."""

    if type(control_policy) is not str:
        raise TypeError("control_policy must be exact text")
    if control_policy != PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY:
        raise ValueError("only the exported global-control policy is supported")
    role = _thinning._require_sha256(control_role_sha256, name="control_role_sha256")
    if type(owner) is not CounterKeyedGlobalInitializerControlOwner:
        raise TypeError("owner has the wrong exact type")
    if owner.consumption_owner is not consumption_owner:
        raise ValueError("global-control owner uses another checkpoint-25 owner")
    if owner.certificate.control_role_sha256 != role:
        raise ValueError("global-control owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_counter_keyed_global_initializer_control_certificate(
    consumption_owner: _consumption.CounterKeyedInitializerStreamConsumptionOwner,
    owner: CounterKeyedGlobalInitializerControlOwner,
    *,
    control_policy: object,
    control_role_sha256: object,
) -> CounterKeyedGlobalInitializerControlCertificate:
    """Return the reconstructed live checkpoint-twenty-six certificate."""

    return require_matching_plugin_bridge_counter_keyed_global_initializer_control(
        consumption_owner,
        owner,
        control_policy=control_policy,
        control_role_sha256=control_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE",
    "COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL",
    "COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL",
    "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT",
    "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS",
    "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM",
    "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS",
    "CounterKeyedGlobalInitializerControlCertificate",
    "CounterKeyedGlobalInitializerControlAddress",
    "CounterKeyedGlobalInitializerControlStream",
    "CounterKeyedGlobalInitializerControlConsumption",
    "CounterKeyedGlobalInitializerControlResult",
    "CounterKeyedGlobalInitializerControlOwner",
    "PluginBridgeCounterKeyedGlobalInitializerControlError",
    "certify_plugin_bridge_counter_keyed_global_initializer_control",
    "require_matching_plugin_bridge_counter_keyed_global_initializer_control",
    "validate_plugin_bridge_counter_keyed_global_initializer_control_certificate",
]
