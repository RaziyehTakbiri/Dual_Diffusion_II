"""Counter-key namespaces and lineage sidecars over checkpoint twenty-two.

This additive contract binds to one exact, live checkpoint-twenty-two owner.
It provides an injective *address layout* for fresh NumPy Philox states and a
deterministic lineage annotation for an already returned, fully revalidated
checkpoint-twenty-two transcript.  The Philox key is exactly ``(run_id,
domain_tag)`` and its initial counter is exactly ``(0, step_index,
occurrence_serial, proposal_index)``.  No address component is hashed,
truncated, folded, or used as a seed.

The stream receipts are namespace objects.  In particular, adding a receipt
to a checkpoint-twenty-two proposal does not assert that the frozen parent
execution used that stream.  Initializer and Brownian domains reserve
collision-free addresses only; this module does not consume those streams or
certify Brownian laws, coarse/fine coupling, statistical independence,
cryptographic security, runtime portability, an exact sampling law, a path,
or a full sampler.

Lineage identifiers are a sealed sidecar.  They are never inserted into the
model configuration passed to a potential, guide, rate, or reference kernel.
Bootstrap labels equal-valued duplicate occurrences by their canonical tuple
positions.  This is an arbitrary labelled lift of an unlabelled model state.
Subsequent accepted edits follow the parent's exact positional edit and use a
stable sort by ``event.model_key()`` only.  Rejection and the terminal waiting
record reuse the exact lineage state object.  Callers continuing into another
step must pass the exact terminal state returned by the preceding annotation;
the retained retired-identifier ledger prevents reuse within that custody
chain, but this module does not police deliberate forks from an older state.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
import platform
import sys
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

try:
    from heterodiff.processes import (
        plugin_bridge_continuous_route_evidence as _route_evidence,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning as _thinning,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning_loop as _loop,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning_loop_route_evidence as _parent,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed lineage contracts require the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise
from heterodiff.processes.plugin_bridge_sampler import ReferenceCandidateIntensity
from heterodiff.processes.reversible_hybrid_reference import (
    MAX_HYBRID_STATE_COORDINATES,
    HybridJumpKind,
)
from heterodiff.theory.configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    TransformedEvent,
)


PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-lineage-contract-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY = (
    "exact-checkpoint22-owner-binding;validated-post-hoc-parent-annotation;"
    "direct-philox-key-run-domain-and-counter-zero-step-occurrence-proposal;"
    "fixed-domain-separation;checkpoint21-initial-state-snapshot;"
    "positional-bootstrap-and-stable-model-key-lineage-edits;"
    "retired-serial-no-reuse-ledger;no-identifier-model-projection-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCOPE = (
    "same-runtime-finite-resolution-philox-address-and-reconstruction;"
    "jump-proposal-and-terminal-wait-namespace-receipts;"
    "initializer-and-left-right-brownian-address-reservations-only;"
    "post-hoc-lineage-annotation-of-successful-checkpoint22-results;"
    "duplicate-safe-positional-edit-custody;fresh-monotone-serials;"
    "independent-bootstrap-or-fork-requires-fresh-run-id;"
    "initialization-index-not-in-occurrence-stream-address;"
    "not-checkpoint22-proposal-keyed-execution;not-parent-stream-consumption;"
    "not-initializer-consumption;not-brownian-consumption-or-coupling;"
    "not-statistical-independence;not-physical-randomness;"
    "not-exact-categorical-integer-or-gaussian-law;"
    "not-analytic-output-law;not-target-or-stationarity;not-liveness;"
    "not-drift;not-path;not-strang;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)
COUNTER_KEYED_PHILOX_ADDRESS_LAYOUT = (
    "key=(run_id,domain_tag);" "counter=(0,step_index,occurrence_serial,proposal_index)"
)

COUNTER_KEY_DOMAIN_JUMP_PROPOSAL = "jump_proposal"
COUNTER_KEY_DOMAIN_TERMINAL_WAIT = "terminal_wait"
COUNTER_KEY_DOMAIN_INITIALIZER = "initializer"
COUNTER_KEY_DOMAIN_BROWNIAN_LEFT = "brownian_left"
COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT = "brownian_right"

COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL = 1
COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT = 2
COUNTER_KEY_DOMAIN_TAG_INITIALIZER = 3
COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT = 4
COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT = 5

COUNTER_KEY_DOMAIN_TAGS = MappingProxyType(
    {
        COUNTER_KEY_DOMAIN_JUMP_PROPOSAL: COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL,
        COUNTER_KEY_DOMAIN_TERMINAL_WAIT: COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT,
        COUNTER_KEY_DOMAIN_INITIALIZER: COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
        COUNTER_KEY_DOMAIN_BROWNIAN_LEFT: COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT,
        COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT: COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT,
    }
)
_MAPPING_PROXY_TYPE = type(MappingProxyType({}))

MAX_UINT64 = (1 << 64) - 1
MAX_LINEAGE_NEXT_SERIAL = 1 << 64
MAX_OPERATIONAL_LINEAGE_IDENTIFIERS = (
    MAX_CONFIGURATION_CARDINALITY + _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS
)

_CERTIFICATE_TOKEN = object()
_ADDRESS_TOKEN = object()
_STREAM_TOKEN = object()
_IDENTIFIER_TOKEN = object()
_OCCURRENCE_TOKEN = object()
_STATE_TOKEN = object()
_TRANSITION_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_ZERO_SHA256 = "0" * 64
_INITIAL_ORIGIN = "initial"
_BIRTH_ORIGIN = "birth"
_REPLACEMENT_ORIGIN = "replacement"


class PluginBridgeCounterKeyedLineageContractError(ArithmeticError):
    """Raised when a stream or lineage annotation cannot be reconstructed."""


def _exact_uint64(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 0 or value > MAX_UINT64:
        raise ValueError("%s must lie in [0, 2**64 - 1]" % name)
    return value


def _exact_positive_uint64(value: object, *, name: str) -> int:
    result = _exact_uint64(value, name=name)
    if result == 0:
        raise ValueError("%s must be positive" % name)
    return result


def _exact_next_serial(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 1 or value > MAX_LINEAGE_NEXT_SERIAL:
        raise ValueError("%s must lie in [1, 2**64]" % name)
    return value


def _exact_optional_uint64(value: object, *, name: str) -> Optional[int]:
    if value is None:
        return None
    return _exact_uint64(value, name=name)


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be boolean" % name)
    return value


def _require_domain_tag_mapping() -> Tuple[Tuple[str, int], ...]:
    expected = (
        ("jump_proposal", 1),
        ("terminal_wait", 2),
        ("initializer", 3),
        ("brownian_left", 4),
        ("brownian_right", 5),
    )
    exported = (
        (COUNTER_KEY_DOMAIN_JUMP_PROPOSAL, COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL),
        (COUNTER_KEY_DOMAIN_TERMINAL_WAIT, COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT),
        (COUNTER_KEY_DOMAIN_INITIALIZER, COUNTER_KEY_DOMAIN_TAG_INITIALIZER),
        (COUNTER_KEY_DOMAIN_BROWNIAN_LEFT, COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT),
        (
            COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
            COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT,
        ),
    )
    if exported != expected:
        raise ValueError("counter-key domain constants changed")
    if type(COUNTER_KEY_DOMAIN_TAGS) is not _MAPPING_PROXY_TYPE:
        raise TypeError("counter-key domain tags must remain an immutable mapping")
    if tuple(COUNTER_KEY_DOMAIN_TAGS.items()) != expected:
        raise ValueError("counter-key domain-tag mapping changed")
    return expected


def _domain_tag(domain: object) -> Tuple[str, int]:
    if type(domain) is not str:
        raise TypeError("counter-keyed Philox domain must be exact text")
    for expected_domain, tag in _require_domain_tag_mapping():
        if domain == expected_domain:
            return domain, tag
    raise ValueError("counter-keyed Philox address domain is unknown")


def _runtime_sha256() -> str:
    if (
        MAX_UINT64 != (1 << 64) - 1
        or MAX_LINEAGE_NEXT_SERIAL != 1 << 64
        or MAX_CONFIGURATION_CARDINALITY != 100_000
        or MAX_HYBRID_STATE_COORDINATES != 4_000_000
        or MAX_OPERATIONAL_LINEAGE_IDENTIFIERS
        != 100_000 + _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS
    ):
        raise ValueError("counter-keyed lineage resource constants changed")
    if (_INITIAL_ORIGIN, _BIRTH_ORIGIN, _REPLACEMENT_ORIGIN) != (
        "initial",
        "birth",
        "replacement",
    ):
        raise ValueError("counter-keyed lineage origin tokens changed")
    domain_tags = _require_domain_tag_mapping()
    probe = np.random.Generator(
        np.random.Philox(
            key=np.asarray((7, COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL), dtype=np.uint64),
            counter=np.asarray((0, 11, 0, 13), dtype=np.uint64),
        )
    )
    snapshot = _route_evidence._capture_philox_state(probe)
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-counter-keyed-lineage-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "probe_snapshot_sha256": snapshot.snapshot_sha256,
            "snapshot_schema": (
                _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
            ),
            "maximum_proposals": _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
            "maximum_lineage_identifiers": MAX_OPERATIONAL_LINEAGE_IDENTIFIERS,
            "maximum_lineage_next_serial": MAX_LINEAGE_NEXT_SERIAL,
            "maximum_configuration_cardinality": MAX_CONFIGURATION_CARDINALITY,
            "maximum_live_coordinates": MAX_HYBRID_STATE_COORDINATES,
            "domain_tags": domain_tags,
            "lineage_origin_tokens": (
                _INITIAL_ORIGIN,
                _BIRTH_ORIGIN,
                _REPLACEMENT_ORIGIN,
            ),
            "policy": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
        }
    )


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedLineageCertificate:
    """Sealed transitive certificate for the checkpoint-twenty-three layer."""

    schema_version: str
    certificate_scope: str
    contract_policy: str
    contract_role_sha256: str
    process_parameter_sha256: str
    parent_certificate_sha256: str
    parent_role_sha256: str
    parent_runtime_sha256: str
    loop_certificate_sha256: str
    route_evidence_certificate_sha256: str
    thinning_certificate_sha256: str
    rate_certificate_sha256: str
    contract_runtime_sha256: str
    philox_snapshot_schema_version: str
    rng_bit_generator: str
    address_layout: str
    maximum_uint64: int
    maximum_proposals: int
    maximum_lineage_identifiers: int
    maximum_live_coordinates: int
    jump_proposal_domain: str
    jump_proposal_domain_tag: int
    terminal_wait_domain: str
    terminal_wait_domain_tag: int
    initializer_domain: str
    initializer_domain_tag: int
    brownian_left_domain: str
    brownian_left_domain_tag: int
    brownian_right_domain: str
    brownian_right_domain_tag: int
    exact_parent_owner_binding_certified: bool
    parent_result_revalidation_before_annotation_certified: bool
    direct_unhashed_address_components_certified: bool
    injective_fixed_domain_address_layout_certified: bool
    exact_checkpoint21_initial_snapshot_certified: bool
    same_runtime_stream_reconstruction_certified: bool
    immutable_stream_receipt_certified: bool
    sealed_lineage_sidecar_certified: bool
    positional_initial_duplicate_lift_certified: bool
    stable_model_key_only_edit_order_certified: bool
    accepted_fresh_monotone_lineage_certified: bool
    accepted_exact_index_destruction_certified: bool
    rejection_exact_state_reuse_certified: bool
    terminal_exact_state_preservation_certified: bool
    retired_serial_no_reuse_ledger_certified: bool
    bounded_lineage_ledger_certified: bool
    bounded_live_coordinate_preflight_certified: bool
    identifier_excluded_from_model_projection_certified: bool
    checkpoint22_proposal_keyed_execution_certified: bool
    checkpoint22_stream_consumption_certified: bool
    occurrence_stream_consumption_certified: bool
    initializer_stream_consumption_certified: bool
    brownian_stream_consumption_certified: bool
    brownian_additive_coupling_certified: bool
    statistical_independence_certified: bool
    physical_randomness_certified: bool
    global_run_id_uniqueness_certified: bool
    duplicate_address_use_prevention_certified: bool
    lineage_fork_prevention_certified: bool
    exact_categorical_law_certified: bool
    exact_integer_law_certified: bool
    exact_gaussian_law_certified: bool
    analytic_output_law_certified: bool
    analytic_target_preserved: bool
    rounded_stationarity_certified: bool
    sampler_liveness_certified: bool
    unconditional_local_completion_certified: bool
    unconditional_exact_frozen_jump_law_certified: bool
    exact_real_time_poisson_or_ctmc_path: bool
    conditional_posterior_or_doob_target: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    strang_sampler_admissible: bool
    full_sampler_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedLineageCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("counter-keyed lineage certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("counter-keyed lineage certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-counter-keyed-lineage-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("counter-keyed lineage certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedLineageCertificate.__annotations__)


def _validate_certificate(certificate: object) -> CounterKeyedLineageCertificate:
    if type(certificate) is not CounterKeyedLineageCertificate:
        raise TypeError("certificate must be an exact CounterKeyedLineageCertificate")
    expected_text = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCOPE,
        "contract_policy": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
        "address_layout": COUNTER_KEYED_PHILOX_ADDRESS_LAYOUT,
        "jump_proposal_domain": COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
        "terminal_wait_domain": COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
        "initializer_domain": COUNTER_KEY_DOMAIN_INITIALIZER,
        "brownian_left_domain": COUNTER_KEY_DOMAIN_BROWNIAN_LEFT,
        "brownian_right_domain": COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("counter-keyed lineage certificate %s differs" % name)
    expected_integers = {
        "maximum_uint64": MAX_UINT64,
        "maximum_proposals": _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
        "maximum_lineage_identifiers": MAX_OPERATIONAL_LINEAGE_IDENTIFIERS,
        "maximum_live_coordinates": MAX_HYBRID_STATE_COORDINATES,
        "jump_proposal_domain_tag": COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL,
        "terminal_wait_domain_tag": COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT,
        "initializer_domain_tag": COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
        "brownian_left_domain_tag": COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT,
        "brownian_right_domain_tag": COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT,
    }
    for name, expected in expected_integers.items():
        if type(getattr(certificate, name)) is not int:
            raise TypeError("certificate.%s must be an exact integer" % name)
        if getattr(certificate, name) != expected:
            raise ValueError("counter-keyed lineage certificate %s differs" % name)
    for name in (
        "contract_role_sha256",
        "process_parameter_sha256",
        "parent_certificate_sha256",
        "parent_role_sha256",
        "parent_runtime_sha256",
        "loop_certificate_sha256",
        "route_evidence_certificate_sha256",
        "thinning_certificate_sha256",
        "rate_certificate_sha256",
        "contract_runtime_sha256",
        "certificate_sha256",
    ):
        _thinning._require_sha256(
            getattr(certificate, name), name="certificate.%s" % name
        )
    true_flags = (
        "exact_parent_owner_binding_certified",
        "parent_result_revalidation_before_annotation_certified",
        "direct_unhashed_address_components_certified",
        "injective_fixed_domain_address_layout_certified",
        "exact_checkpoint21_initial_snapshot_certified",
        "same_runtime_stream_reconstruction_certified",
        "immutable_stream_receipt_certified",
        "sealed_lineage_sidecar_certified",
        "positional_initial_duplicate_lift_certified",
        "stable_model_key_only_edit_order_certified",
        "accepted_fresh_monotone_lineage_certified",
        "accepted_exact_index_destruction_certified",
        "rejection_exact_state_reuse_certified",
        "terminal_exact_state_preservation_certified",
        "retired_serial_no_reuse_ledger_certified",
        "bounded_lineage_ledger_certified",
        "bounded_live_coordinate_preflight_certified",
        "identifier_excluded_from_model_projection_certified",
        "passed",
    )
    false_flags = (
        "checkpoint22_proposal_keyed_execution_certified",
        "checkpoint22_stream_consumption_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "unconditional_local_completion_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_real_time_poisson_or_ctmc_path",
        "conditional_posterior_or_doob_target",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags:
        _exact_bool(getattr(certificate, name), name="certificate.%s" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("counter-keyed lineage positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("counter-keyed lineage negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    expected_digest = _thinning._semantic_digest(_without(values, "certificate_sha256"))
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("counter-keyed lineage certificate digest differs")
    return certificate


def _make_certificate(
    parent_certificate: _parent.OperationalThinningLoopRouteEvidenceCertificate,
    *,
    contract_role_sha256: str,
) -> CounterKeyedLineageCertificate:
    checked = _parent._validate_certificate(parent_certificate)
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCOPE,
        "contract_policy": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
        "contract_role_sha256": contract_role_sha256,
        "process_parameter_sha256": checked.process_parameter_sha256,
        "parent_certificate_sha256": checked.certificate_sha256,
        "parent_role_sha256": checked.integration_role_sha256,
        "parent_runtime_sha256": checked.integration_runtime_sha256,
        "loop_certificate_sha256": checked.loop_certificate_sha256,
        "route_evidence_certificate_sha256": (
            checked.route_evidence_certificate_sha256
        ),
        "thinning_certificate_sha256": checked.thinning_certificate_sha256,
        "rate_certificate_sha256": checked.rate_certificate_sha256,
        "contract_runtime_sha256": _runtime_sha256(),
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
        "address_layout": COUNTER_KEYED_PHILOX_ADDRESS_LAYOUT,
        "maximum_uint64": MAX_UINT64,
        "maximum_proposals": _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
        "maximum_lineage_identifiers": MAX_OPERATIONAL_LINEAGE_IDENTIFIERS,
        "maximum_live_coordinates": MAX_HYBRID_STATE_COORDINATES,
        "jump_proposal_domain": COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
        "jump_proposal_domain_tag": COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL,
        "terminal_wait_domain": COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
        "terminal_wait_domain_tag": COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT,
        "initializer_domain": COUNTER_KEY_DOMAIN_INITIALIZER,
        "initializer_domain_tag": COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
        "brownian_left_domain": COUNTER_KEY_DOMAIN_BROWNIAN_LEFT,
        "brownian_left_domain_tag": COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT,
        "brownian_right_domain": COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
        "brownian_right_domain_tag": COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT,
        "exact_parent_owner_binding_certified": True,
        "parent_result_revalidation_before_annotation_certified": True,
        "direct_unhashed_address_components_certified": True,
        "injective_fixed_domain_address_layout_certified": True,
        "exact_checkpoint21_initial_snapshot_certified": True,
        "same_runtime_stream_reconstruction_certified": True,
        "immutable_stream_receipt_certified": True,
        "sealed_lineage_sidecar_certified": True,
        "positional_initial_duplicate_lift_certified": True,
        "stable_model_key_only_edit_order_certified": True,
        "accepted_fresh_monotone_lineage_certified": True,
        "accepted_exact_index_destruction_certified": True,
        "rejection_exact_state_reuse_certified": True,
        "terminal_exact_state_preservation_certified": True,
        "retired_serial_no_reuse_ledger_certified": True,
        "bounded_lineage_ledger_certified": True,
        "bounded_live_coordinate_preflight_certified": True,
        "identifier_excluded_from_model_projection_certified": True,
        "checkpoint22_proposal_keyed_execution_certified": False,
        "checkpoint22_stream_consumption_certified": False,
        "occurrence_stream_consumption_certified": False,
        "initializer_stream_consumption_certified": False,
        "brownian_stream_consumption_certified": False,
        "brownian_additive_coupling_certified": False,
        "statistical_independence_certified": False,
        "physical_randomness_certified": False,
        "global_run_id_uniqueness_certified": False,
        "duplicate_address_use_prevention_certified": False,
        "lineage_fork_prevention_certified": False,
        "exact_categorical_law_certified": False,
        "exact_integer_law_certified": False,
        "exact_gaussian_law_certified": False,
        "analytic_output_law_certified": False,
        "analytic_target_preserved": False,
        "rounded_stationarity_certified": False,
        "sampler_liveness_certified": False,
        "unconditional_local_completion_certified": False,
        "unconditional_exact_frozen_jump_law_certified": False,
        "exact_real_time_poisson_or_ctmc_path": False,
        "conditional_posterior_or_doob_target": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "strang_sampler_admissible": False,
        "full_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _thinning._semantic_digest(
        _without(values, "certificate_sha256")
    )
    return CounterKeyedLineageCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedPhiloxAddress:
    """One injective direct Philox address under a fixed semantic domain."""

    schema_version: str
    certificate_sha256: str
    domain: str
    domain_tag: int
    run_id: int
    step_index: int
    occurrence_serial: int
    proposal_index: int
    philox_key: Tuple[int, int]
    philox_counter: Tuple[int, int, int, int]
    address_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedPhiloxAddress cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ADDRESS_TOKEN:
            raise TypeError("counter-keyed Philox addresses are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("counter-keyed Philox address fields are incomplete")
        if (
            values["schema_version"]
            != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION
        ):
            raise ValueError("counter-keyed Philox address schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="address.certificate_sha256"
        )
        domain, expected_tag = _domain_tag(values["domain"])
        tag = _exact_uint64(values["domain_tag"], name="address.domain_tag")
        if tag != expected_tag:
            raise ValueError("counter-keyed Philox domain tag differs")
        run_id = _exact_uint64(values["run_id"], name="address.run_id")
        step_index = _exact_uint64(values["step_index"], name="address.step_index")
        occurrence_serial = _exact_uint64(
            values["occurrence_serial"], name="address.occurrence_serial"
        )
        proposal_index = _exact_uint64(
            values["proposal_index"], name="address.proposal_index"
        )
        if domain in (
            COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
            COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
        ):
            if occurrence_serial != 0:
                raise ValueError(
                    "proposal/wait addresses require occurrence serial zero"
                )
            maximum = _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS
            if domain == COUNTER_KEY_DOMAIN_JUMP_PROPOSAL:
                if proposal_index >= maximum:
                    raise ValueError(
                        "jump-proposal address exceeds the parent proposal range"
                    )
            elif proposal_index > maximum:
                raise ValueError(
                    "terminal-wait address exceeds the parent completion range"
                )
        else:
            if occurrence_serial == 0:
                raise ValueError(
                    "occurrence addresses require a positive lineage serial"
                )
            if proposal_index != 0:
                raise ValueError(
                    "initializer/Brownian addresses require proposal index zero"
                )
        expected_key = (run_id, tag)
        expected_counter = (0, step_index, occurrence_serial, proposal_index)
        if type(values["philox_key"]) is not tuple:
            raise TypeError("address.philox_key must be an exact tuple")
        if type(values["philox_counter"]) is not tuple:
            raise TypeError("address.philox_counter must be an exact tuple")
        if values["philox_key"] != expected_key:
            raise ValueError("counter-keyed Philox key differs from its address")
        if values["philox_counter"] != expected_counter:
            raise ValueError("counter-keyed Philox counter differs from its address")
        for index, word in enumerate(values["philox_key"]):
            _exact_uint64(word, name="address.philox_key[%d]" % index)
        for index, word in enumerate(values["philox_counter"]):
            _exact_uint64(word, name="address.philox_counter[%d]" % index)
        _thinning._require_sha256(
            values["address_sha256"], name="address.address_sha256"
        )
        expected_digest = _thinning._semantic_digest(_without(values, "address_sha256"))
        if values["address_sha256"] != expected_digest:
            raise ValueError("counter-keyed Philox address digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("counter-keyed Philox addresses are not pickle objects")


def _address_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedPhiloxAddress.__annotations__)


def _validate_address(address: object) -> CounterKeyedPhiloxAddress:
    if type(address) is not CounterKeyedPhiloxAddress:
        raise TypeError("address must be an exact CounterKeyedPhiloxAddress")
    return CounterKeyedPhiloxAddress(
        **{name: getattr(address, name) for name in _address_fields()},
        _construction_token=_ADDRESS_TOKEN,
    )


def _make_address(
    certificate: CounterKeyedLineageCertificate,
    *,
    domain: str,
    run_id: int,
    step_index: int,
    occurrence_serial: int,
    proposal_index: int,
) -> CounterKeyedPhiloxAddress:
    checked_certificate = _validate_certificate(certificate)
    checked_domain, tag = _domain_tag(domain)
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "domain": checked_domain,
        "domain_tag": tag,
        "run_id": run_id,
        "step_index": step_index,
        "occurrence_serial": occurrence_serial,
        "proposal_index": proposal_index,
        "philox_key": (run_id, tag),
        "philox_counter": (0, step_index, occurrence_serial, proposal_index),
        "address_sha256": _ZERO_SHA256,
    }
    values["address_sha256"] = _thinning._semantic_digest(
        _without(values, "address_sha256")
    )
    return CounterKeyedPhiloxAddress(**values, _construction_token=_ADDRESS_TOKEN)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedPhiloxStream:
    """Immutable receipt for one reconstructable, initially unused stream."""

    certificate: CounterKeyedLineageCertificate
    certificate_sha256: str
    address: CounterKeyedPhiloxAddress
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
        raise TypeError("CounterKeyedPhiloxStream cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _STREAM_TOKEN:
            raise TypeError("counter-keyed Philox streams are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("counter-keyed Philox stream fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("counter-keyed stream certificate differs")
        address = _validate_address(values["address"])
        if address.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("counter-keyed stream address has another certificate")
        if values["address_sha256"] != address.address_sha256:
            raise ValueError("counter-keyed stream address digest differs")
        snapshot = _route_evidence._validate_snapshot(values["initial_state"])
        if values["initial_snapshot_sha256"] != snapshot.snapshot_sha256:
            raise ValueError("counter-keyed stream snapshot digest differs")
        if values["initial_state_sha256"] != snapshot.state_sha256:
            raise ValueError("counter-keyed stream state digest differs")
        if snapshot.key != address.philox_key:
            raise ValueError("counter-keyed stream key differs from its address")
        if snapshot.counter != address.philox_counter:
            raise ValueError("counter-keyed stream counter differs from its address")
        if snapshot.buffer != (0, 0, 0, 0) or snapshot.buffer_pos != 4:
            raise ValueError("counter-keyed stream initial buffer is not empty")
        if snapshot.has_uint32 != 0 or snapshot.uinteger != 0:
            raise ValueError("counter-keyed stream initial uint32 cache is not empty")
        expected_booleans = {
            "buffer_is_zero": True,
            "uint32_cache_is_zero": True,
            "parent_execution_used_this_stream": False,
            "same_runtime_only": True,
        }
        for name, expected in expected_booleans.items():
            if _exact_bool(values[name], name="stream.%s" % name) is not expected:
                raise ValueError("counter-keyed stream %s differs" % name)
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
            raise ValueError("counter-keyed Philox stream digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("counter-keyed Philox streams are not pickle objects")


def _stream_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedPhiloxStream.__annotations__)


def _validate_stream_record(stream: object) -> CounterKeyedPhiloxStream:
    if type(stream) is not CounterKeyedPhiloxStream:
        raise TypeError("stream must be an exact CounterKeyedPhiloxStream")
    return CounterKeyedPhiloxStream(
        **{name: getattr(stream, name) for name in _stream_fields()},
        _construction_token=_STREAM_TOKEN,
    )


def _make_stream(
    certificate: CounterKeyedLineageCertificate,
    address: CounterKeyedPhiloxAddress,
) -> CounterKeyedPhiloxStream:
    checked_certificate = _validate_certificate(certificate)
    checked_address = _validate_address(address)
    if checked_address.certificate_sha256 != checked_certificate.certificate_sha256:
        raise ValueError("stream address belongs to another certificate")
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
    return CounterKeyedPhiloxStream(**values, _construction_token=_STREAM_TOKEN)


@dataclass(frozen=True, eq=False, init=False)
class OperationalLineageIdentifier:
    """A run-local monotone serial together with its immutable creation origin."""

    schema_version: str
    certificate_sha256: str
    run_id: int
    serial: int
    origin_kind: str
    origin_initialization_index: Optional[int]
    origin_initial_position: Optional[int]
    origin_step_index: Optional[int]
    origin_proposal_index: Optional[int]
    identifier_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLineageIdentifier cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _IDENTIFIER_TOKEN:
            raise TypeError("operational lineage identifiers are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational lineage identifier fields are incomplete")
        if (
            values["schema_version"]
            != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION
        ):
            raise ValueError("operational lineage identifier schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="identifier.certificate_sha256"
        )
        _exact_uint64(values["run_id"], name="identifier.run_id")
        _exact_positive_uint64(values["serial"], name="identifier.serial")
        origin_kind = values["origin_kind"]
        if type(origin_kind) is not str or origin_kind not in (
            _INITIAL_ORIGIN,
            _BIRTH_ORIGIN,
            _REPLACEMENT_ORIGIN,
        ):
            raise ValueError("operational lineage identifier origin is unknown")
        initialization_index = _exact_optional_uint64(
            values["origin_initialization_index"],
            name="identifier.origin_initialization_index",
        )
        initial_position = _exact_optional_uint64(
            values["origin_initial_position"],
            name="identifier.origin_initial_position",
        )
        step_index = _exact_optional_uint64(
            values["origin_step_index"], name="identifier.origin_step_index"
        )
        proposal_index = _exact_optional_uint64(
            values["origin_proposal_index"],
            name="identifier.origin_proposal_index",
        )
        if origin_kind == _INITIAL_ORIGIN:
            if initialization_index is None or initial_position is None:
                raise ValueError("initial lineage requires initialization and position")
            if step_index is not None or proposal_index is not None:
                raise ValueError("initial lineage cannot have proposal origin fields")
        else:
            if initialization_index is not None or initial_position is not None:
                raise ValueError("edit-created lineage cannot have initial fields")
            if step_index is None or proposal_index is None:
                raise ValueError("edit-created lineage requires step and proposal")
            if proposal_index >= _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS:
                raise ValueError("lineage origin proposal exceeds parent range")
        _thinning._require_sha256(
            values["identifier_sha256"], name="identifier.identifier_sha256"
        )
        expected_digest = _thinning._semantic_digest(
            _without(values, "identifier_sha256")
        )
        if values["identifier_sha256"] != expected_digest:
            raise ValueError("operational lineage identifier digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational lineage identifiers are not pickle objects")


def _identifier_fields() -> Tuple[str, ...]:
    return tuple(OperationalLineageIdentifier.__annotations__)


def _validate_identifier(identifier: object) -> OperationalLineageIdentifier:
    if type(identifier) is not OperationalLineageIdentifier:
        raise TypeError("identifier must be an exact OperationalLineageIdentifier")
    return OperationalLineageIdentifier(
        **{name: getattr(identifier, name) for name in _identifier_fields()},
        _construction_token=_IDENTIFIER_TOKEN,
    )


def _make_identifier(
    certificate: CounterKeyedLineageCertificate,
    *,
    run_id: int,
    serial: int,
    origin_kind: str,
    origin_initialization_index: Optional[int] = None,
    origin_initial_position: Optional[int] = None,
    origin_step_index: Optional[int] = None,
    origin_proposal_index: Optional[int] = None,
) -> OperationalLineageIdentifier:
    checked_certificate = _validate_certificate(certificate)
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "run_id": run_id,
        "serial": serial,
        "origin_kind": origin_kind,
        "origin_initialization_index": origin_initialization_index,
        "origin_initial_position": origin_initial_position,
        "origin_step_index": origin_step_index,
        "origin_proposal_index": origin_proposal_index,
        "identifier_sha256": _ZERO_SHA256,
    }
    values["identifier_sha256"] = _thinning._semantic_digest(
        _without(values, "identifier_sha256")
    )
    return OperationalLineageIdentifier(**values, _construction_token=_IDENTIFIER_TOKEN)


@dataclass(frozen=True, eq=False, init=False)
class OperationalLineagedOccurrence:
    """One unlabelled model event paired with a sidecar lineage identifier."""

    schema_version: str
    certificate_sha256: str
    identifier: OperationalLineageIdentifier
    identifier_sha256: str
    event: TransformedEvent
    event_model_key: Tuple[object, ...]
    occurrence_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLineagedOccurrence cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _OCCURRENCE_TOKEN:
            raise TypeError("operational lineaged occurrences are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational lineaged occurrence fields are incomplete")
        if (
            values["schema_version"]
            != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION
        ):
            raise ValueError("operational lineaged occurrence schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="occurrence.certificate_sha256"
        )
        identifier = _validate_identifier(values["identifier"])
        if values["identifier_sha256"] != identifier.identifier_sha256:
            raise ValueError("lineaged occurrence identifier digest differs")
        if identifier.certificate_sha256 != values["certificate_sha256"]:
            raise ValueError("lineaged occurrence identifier has another certificate")
        event = values["event"]
        if type(event) is not TransformedEvent:
            raise TypeError(
                "lineaged occurrence event must be an exact TransformedEvent"
            )
        reconstructed_event = TransformedEvent(event.event_type, event.coordinates)
        if (
            reconstructed_event.event_type != event.event_type
            or len(reconstructed_event.coordinates) != len(event.coordinates)
            or any(
                not _thinning._same_float(supplied, expected)
                for supplied, expected in zip(
                    event.coordinates, reconstructed_event.coordinates
                )
            )
        ):
            raise ValueError("lineaged occurrence event is not canonical")
        if type(values["event_model_key"]) is not tuple:
            raise TypeError("lineaged occurrence model key must be an exact tuple")
        if values["event_model_key"] != event.model_key():
            raise ValueError("lineaged occurrence model key differs")
        _thinning._require_sha256(
            values["occurrence_sha256"], name="occurrence.occurrence_sha256"
        )
        expected_digest = _thinning._semantic_digest(
            _without(values, "identifier", "event", "occurrence_sha256")
        )
        if values["occurrence_sha256"] != expected_digest:
            raise ValueError("operational lineaged occurrence digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational lineaged occurrences are not pickle objects")


def _occurrence_fields() -> Tuple[str, ...]:
    return tuple(OperationalLineagedOccurrence.__annotations__)


def _validate_occurrence(
    occurrence: object,
) -> OperationalLineagedOccurrence:
    if type(occurrence) is not OperationalLineagedOccurrence:
        raise TypeError("occurrence must be an exact OperationalLineagedOccurrence")
    return OperationalLineagedOccurrence(
        **{name: getattr(occurrence, name) for name in _occurrence_fields()},
        _construction_token=_OCCURRENCE_TOKEN,
    )


def _make_occurrence(
    certificate: CounterKeyedLineageCertificate,
    identifier: OperationalLineageIdentifier,
    event: TransformedEvent,
) -> OperationalLineagedOccurrence:
    checked_certificate = _validate_certificate(certificate)
    checked_identifier = _validate_identifier(identifier)
    if checked_identifier.certificate_sha256 != checked_certificate.certificate_sha256:
        raise ValueError("lineaged occurrence identifier has another certificate")
    if type(event) is not TransformedEvent:
        raise TypeError("event must be an exact TransformedEvent")
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "identifier": checked_identifier,
        "identifier_sha256": checked_identifier.identifier_sha256,
        "event": event,
        "event_model_key": event.model_key(),
        "occurrence_sha256": _ZERO_SHA256,
    }
    values["occurrence_sha256"] = _thinning._semantic_digest(
        _without(values, "identifier", "event", "occurrence_sha256")
    )
    return OperationalLineagedOccurrence(
        **values, _construction_token=_OCCURRENCE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class OperationalLineageState:
    """Ordered live sidecar state plus all retired identifiers in this chain."""

    schema_version: str
    certificate_sha256: str
    run_id: int
    initialization_index: int
    occurrences: Tuple[OperationalLineagedOccurrence, ...]
    occurrence_sha256s: Tuple[str, ...]
    retired_identifiers: Tuple[OperationalLineageIdentifier, ...]
    retired_identifier_sha256s: Tuple[str, ...]
    next_serial: int
    model_configuration: Tuple[TransformedEvent, ...]
    model_state_sha256: str
    identifiers_absent_from_model_projection: bool
    state_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLineageState cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _STATE_TOKEN:
            raise TypeError("operational lineage states are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational lineage state fields are incomplete")
        if (
            values["schema_version"]
            != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION
        ):
            raise ValueError("operational lineage state schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="lineage_state.certificate_sha256"
        )
        run_id = _exact_uint64(values["run_id"], name="lineage_state.run_id")
        initialization_index = _exact_uint64(
            values["initialization_index"],
            name="lineage_state.initialization_index",
        )
        if type(values["occurrences"]) is not tuple:
            raise TypeError("lineage-state occurrences must be an exact tuple")
        if type(values["occurrence_sha256s"]) is not tuple:
            raise TypeError("lineage-state occurrence digests must be an exact tuple")
        if type(values["retired_identifiers"]) is not tuple:
            raise TypeError("retired identifiers must be an exact tuple")
        if type(values["retired_identifier_sha256s"]) is not tuple:
            raise TypeError("retired identifier digests must be an exact tuple")
        if len(values["occurrence_sha256s"]) != len(values["occurrences"]):
            raise ValueError("lineage-state occurrence digest count differs")
        if len(values["retired_identifier_sha256s"]) != len(
            values["retired_identifiers"]
        ):
            raise ValueError("retired identifier digest count differs")
        if len(values["occurrences"]) > MAX_CONFIGURATION_CARDINALITY:
            raise ValueError("lineage-state live occurrence tuple exceeds its bound")
        if (
            len(values["occurrences"]) + len(values["retired_identifiers"])
            > MAX_OPERATIONAL_LINEAGE_IDENTIFIERS
        ):
            raise ValueError("lineage-state identifier ledger exceeds its bound")
        live_coordinate_count = 0
        for index, occurrence in enumerate(values["occurrences"]):
            if type(occurrence) is not OperationalLineagedOccurrence:
                raise TypeError(
                    "lineage-state occurrence %d has the wrong exact type" % index
                )
            event = occurrence.event
            if type(event) is not TransformedEvent:
                raise TypeError(
                    "lineage-state event %d has the wrong exact type" % index
                )
            if type(event.coordinates) is not tuple:
                raise TypeError(
                    "lineage-state event %d coordinates must be an exact tuple" % index
                )
            live_coordinate_count += len(event.coordinates)
            if live_coordinate_count > MAX_HYBRID_STATE_COORDINATES:
                raise ValueError("lineage-state live coordinates exceed their bound")
        occurrences = tuple(
            _validate_occurrence(occurrence) for occurrence in values["occurrences"]
        )
        if values["occurrence_sha256s"] != tuple(
            occurrence.occurrence_sha256 for occurrence in occurrences
        ):
            raise ValueError("lineage-state occurrence digest sequence differs")
        retired = tuple(
            _validate_identifier(identifier)
            for identifier in values["retired_identifiers"]
        )
        if values["retired_identifier_sha256s"] != tuple(
            identifier.identifier_sha256 for identifier in retired
        ):
            raise ValueError("retired identifier digest sequence differs")
        all_identifiers = tuple(item.identifier for item in occurrences) + retired
        for identifier in all_identifiers:
            if identifier.certificate_sha256 != values["certificate_sha256"]:
                raise ValueError("lineage state contains another certificate")
            if identifier.run_id != run_id:
                raise ValueError("lineage state contains another run")
            if (
                identifier.origin_kind == _INITIAL_ORIGIN
                and identifier.origin_initialization_index != initialization_index
            ):
                raise ValueError("initial lineage uses another initialization")
        serials = tuple(identifier.serial for identifier in all_identifiers)
        if len(set(serials)) != len(serials):
            raise ValueError("live and retired lineage serials must be unique")
        next_serial = _exact_next_serial(
            values["next_serial"], name="lineage_state.next_serial"
        )
        if any(serial >= next_serial for serial in serials):
            raise ValueError("lineage state contains an unallocated serial")
        if len(serials) != next_serial - 1:
            raise ValueError("lineage state serial ledger has a gap")
        initial_identifiers = tuple(
            identifier
            for identifier in all_identifiers
            if identifier.origin_kind == _INITIAL_ORIGIN
        )
        initial_positions = tuple(
            identifier.origin_initial_position for identifier in initial_identifiers
        )
        if len(set(initial_positions)) != len(initial_positions):
            raise ValueError("initial lineage positions must be unique")
        if set(initial_positions) != set(range(len(initial_positions))):
            raise ValueError("initial lineage positions must be contiguous from zero")
        for identifier in initial_identifiers:
            if identifier.serial != identifier.origin_initial_position + 1:
                raise ValueError("bootstrap lineage serial differs from its position")
        edit_origins = tuple(
            (
                identifier.origin_step_index,
                identifier.origin_proposal_index,
            )
            for identifier in all_identifiers
            if identifier.origin_kind in (_BIRTH_ORIGIN, _REPLACEMENT_ORIGIN)
        )
        if len(set(edit_origins)) != len(edit_origins):
            raise ValueError("edit-created lineage origins must be unique")
        edit_identifiers = tuple(
            sorted(
                (
                    identifier
                    for identifier in all_identifiers
                    if identifier.origin_kind in (_BIRTH_ORIGIN, _REPLACEMENT_ORIGIN)
                ),
                key=lambda identifier: identifier.serial,
            )
        )
        serial_ordered_origins = tuple(
            (identifier.origin_step_index, identifier.origin_proposal_index)
            for identifier in edit_identifiers
        )
        if any(
            right <= left
            for left, right in zip(
                serial_ordered_origins,
                serial_ordered_origins[1:],
            )
        ):
            raise ValueError("edit-created lineage origins contradict serial order")
        replacement_identifiers = tuple(
            identifier
            for identifier in edit_identifiers
            if identifier.origin_kind == _REPLACEMENT_ORIGIN
        )
        if len(replacement_identifiers) > len(retired):
            raise ValueError("replacement lineage lacks a retired source")
        retired_serials = tuple(sorted(identifier.serial for identifier in retired))
        for rank, replacement in enumerate(replacement_identifiers, start=1):
            if bisect_left(retired_serials, replacement.serial) < rank:
                raise ValueError(
                    "replacement lineage has no feasible earlier retired source"
                )
        expected_configuration = tuple(occurrence.event for occurrence in occurrences)
        if type(values["model_configuration"]) is not tuple:
            raise TypeError("lineage model projection must be an exact tuple")
        if values["model_configuration"] != expected_configuration:
            raise ValueError("lineage model projection differs")
        if (
            tuple(sorted(expected_configuration, key=TransformedEvent.model_key))
            != expected_configuration
        ):
            raise ValueError("lineage model projection is not canonical")
        if values["model_state_sha256"] != _loop._configuration_sha256(
            expected_configuration
        ):
            raise ValueError("lineage model-state digest differs")
        if (
            _exact_bool(
                values["identifiers_absent_from_model_projection"],
                name="lineage_state.identifiers_absent_from_model_projection",
            )
            is not True
        ):
            raise ValueError("lineage identifiers leaked into the model projection")
        for name in (
            "certificate_sha256",
            "model_state_sha256",
            "state_sha256",
        ):
            _thinning._require_sha256(values[name], name="lineage_state.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "occurrences",
                "retired_identifiers",
                "model_configuration",
                "state_sha256",
            )
        )
        if values["state_sha256"] != expected_digest:
            raise ValueError("operational lineage state digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational lineage states are not pickle objects")


def _state_fields() -> Tuple[str, ...]:
    return tuple(OperationalLineageState.__annotations__)


def _validate_state(state: object) -> OperationalLineageState:
    if type(state) is not OperationalLineageState:
        raise TypeError("state must be an exact OperationalLineageState")
    return OperationalLineageState(
        **{name: getattr(state, name) for name in _state_fields()},
        _construction_token=_STATE_TOKEN,
    )


def _make_state(
    certificate: CounterKeyedLineageCertificate,
    *,
    run_id: int,
    initialization_index: int,
    occurrences: Tuple[OperationalLineagedOccurrence, ...],
    retired_identifiers: Tuple[OperationalLineageIdentifier, ...],
    next_serial: int,
) -> OperationalLineageState:
    checked_certificate = _validate_certificate(certificate)
    if type(occurrences) is not tuple or type(retired_identifiers) is not tuple:
        raise TypeError("lineage state components must be exact tuples")
    model_configuration = tuple(occurrence.event for occurrence in occurrences)
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "occurrences": occurrences,
        "occurrence_sha256s": tuple(
            occurrence.occurrence_sha256 for occurrence in occurrences
        ),
        "retired_identifiers": retired_identifiers,
        "retired_identifier_sha256s": tuple(
            identifier.identifier_sha256 for identifier in retired_identifiers
        ),
        "next_serial": next_serial,
        "model_configuration": model_configuration,
        "model_state_sha256": _loop._configuration_sha256(model_configuration),
        "identifiers_absent_from_model_projection": True,
        "state_sha256": _ZERO_SHA256,
    }
    values["state_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "occurrences",
            "retired_identifiers",
            "model_configuration",
            "state_sha256",
        )
    )
    return OperationalLineageState(**values, _construction_token=_STATE_TOKEN)


def _state_values_match(
    left: OperationalLineageState,
    right: OperationalLineageState,
) -> bool:
    return (
        left.schema_version == right.schema_version
        and left.certificate_sha256 == right.certificate_sha256
        and left.run_id == right.run_id
        and left.initialization_index == right.initialization_index
        and left.occurrence_sha256s == right.occurrence_sha256s
        and left.retired_identifier_sha256s == right.retired_identifier_sha256s
        and left.next_serial == right.next_serial
        and left.model_configuration == right.model_configuration
        and left.model_state_sha256 == right.model_state_sha256
        and left.identifiers_absent_from_model_projection
        is right.identifiers_absent_from_model_projection
        and left.state_sha256 == right.state_sha256
    )


def _derive_lineage_edit(
    certificate: CounterKeyedLineageCertificate,
    iteration: _loop.OperationalProposalIteration,
    pre_state: OperationalLineageState,
    *,
    step_index: int,
) -> Tuple[
    Optional[OperationalLineageIdentifier],
    Optional[OperationalLineageIdentifier],
    Optional[OperationalLineagedOccurrence],
    OperationalLineageState,
]:
    checked_certificate = _validate_certificate(certificate)
    if type(iteration) is not _loop.OperationalProposalIteration:
        raise TypeError("iteration must be an exact OperationalProposalIteration")
    checked_state = _validate_state(pre_state)
    checked_step = _exact_uint64(step_index, name="step_index")
    if checked_state.certificate_sha256 != checked_certificate.certificate_sha256:
        raise ValueError("lineage edit state has another certificate")
    proposal = iteration.route_draw.candidate.proposal
    if checked_state.model_configuration != proposal.source_configuration:
        raise ValueError("lineage edit source projection differs from its proposal")
    source_index = proposal.source_occurrence_index
    selected: Optional[OperationalLineageIdentifier] = None
    if source_index is not None:
        if type(source_index) is not int or isinstance(source_index, bool):
            raise TypeError("proposal source index must be an exact integer")
        if source_index < 0 or source_index >= len(checked_state.occurrences):
            raise ValueError("proposal source index is outside the lineage state")
        selected = checked_state.occurrences[source_index].identifier
        if checked_state.occurrences[source_index].event != proposal.source_event:
            raise ValueError("proposal indexed source event differs from lineage state")
    if not iteration.accepted:
        return selected, None, None, pre_state
    mutable = list(checked_state.occurrences)
    retired = list(checked_state.retired_identifiers)
    destroyed: Optional[OperationalLineageIdentifier] = None
    created: Optional[OperationalLineagedOccurrence] = None
    next_serial = checked_state.next_serial
    if proposal.kind is HybridJumpKind.BIRTH:
        if source_index is not None or proposal.destination_event is None:
            raise ValueError("accepted birth has inconsistent edit metadata")
        if next_serial > MAX_UINT64:
            raise PluginBridgeCounterKeyedLineageContractError(
                "lineage serial space is exhausted"
            )
        identifier = _make_identifier(
            checked_certificate,
            run_id=checked_state.run_id,
            serial=next_serial,
            origin_kind=_BIRTH_ORIGIN,
            origin_step_index=checked_step,
            origin_proposal_index=iteration.proposal_index,
        )
        created = _make_occurrence(
            checked_certificate, identifier, proposal.destination_event
        )
        mutable.append(created)
        next_serial += 1
    elif proposal.kind is HybridJumpKind.DEATH:
        if source_index is None or selected is None:
            raise ValueError("accepted death has no indexed source lineage")
        destroyed_occurrence = mutable.pop(source_index)
        destroyed = destroyed_occurrence.identifier
        if destroyed is not selected:
            raise ValueError("accepted death selected another lineage")
        retired.append(destroyed)
    elif proposal.kind is HybridJumpKind.REPLACEMENT:
        if (
            source_index is None
            or selected is None
            or proposal.destination_event is None
        ):
            raise ValueError("accepted replacement has inconsistent edit metadata")
        destroyed_occurrence = mutable.pop(source_index)
        destroyed = destroyed_occurrence.identifier
        if destroyed is not selected:
            raise ValueError("accepted replacement selected another lineage")
        retired.append(destroyed)
        if next_serial > MAX_UINT64:
            raise PluginBridgeCounterKeyedLineageContractError(
                "lineage serial space is exhausted"
            )
        identifier = _make_identifier(
            checked_certificate,
            run_id=checked_state.run_id,
            serial=next_serial,
            origin_kind=_REPLACEMENT_ORIGIN,
            origin_step_index=checked_step,
            origin_proposal_index=iteration.proposal_index,
        )
        created = _make_occurrence(
            checked_certificate, identifier, proposal.destination_event
        )
        mutable.append(created)
        next_serial += 1
    else:  # pragma: no cover - parent exact enum validation
        raise ValueError("parent proposal uses an unknown edit kind")
    if len(mutable) + len(retired) > MAX_OPERATIONAL_LINEAGE_IDENTIFIERS:
        raise PluginBridgeCounterKeyedLineageContractError(
            "lineage identifier ledger exhausted its resource bound"
        )
    post_occurrences = tuple(
        sorted(mutable, key=lambda occurrence: occurrence.event.model_key())
    )
    post_state = _make_state(
        checked_certificate,
        run_id=checked_state.run_id,
        initialization_index=checked_state.initialization_index,
        occurrences=post_occurrences,
        retired_identifiers=tuple(retired),
        next_serial=next_serial,
    )
    if post_state.model_configuration != iteration.decision.result_configuration:
        raise ValueError("accepted lineage edit differs from the parent result")
    return selected, destroyed, created, post_state


@dataclass(frozen=True, eq=False, init=False)
class OperationalLineageTransition:
    """Sealed deterministic sidecar transition for one parent proposal."""

    certificate: CounterKeyedLineageCertificate
    certificate_sha256: str
    parent_iteration: _loop.OperationalProposalIteration
    parent_iteration_sha256: str
    parent_route_evidence: _route_evidence.OperationalReferenceRouteEvidence
    parent_route_evidence_sha256: str
    run_id: int
    step_index: int
    proposal_index: int
    edit_kind: str
    accepted: bool
    source_occurrence_index: Optional[int]
    selected_source_identifier: Optional[OperationalLineageIdentifier]
    selected_source_identifier_sha256: Optional[str]
    destroyed_identifier: Optional[OperationalLineageIdentifier]
    destroyed_identifier_sha256: Optional[str]
    created_occurrence: Optional[OperationalLineagedOccurrence]
    created_occurrence_sha256: Optional[str]
    pre_state: OperationalLineageState
    pre_state_sha256: str
    post_state: OperationalLineageState
    post_state_sha256: str
    rejection_reused_exact_state: bool
    accepted_allocated_fresh_serial: bool
    accepted_destroyed_exact_index: bool
    stable_model_key_sort_only: bool
    identifiers_absent_from_model_projection: bool
    transition_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLineageTransition cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _TRANSITION_TOKEN:
            raise TypeError("operational lineage transitions are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational lineage transition fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("lineage transition certificate differs")
        iteration = values["parent_iteration"]
        if type(iteration) is not _loop.OperationalProposalIteration:
            raise TypeError("lineage transition parent has the wrong exact type")
        _loop.OperationalProposalIteration(
            **{name: getattr(iteration, name) for name in _loop._iteration_fields()},
            _construction_token=_loop._ITERATION_TOKEN,
        )
        if values["parent_iteration_sha256"] != iteration.iteration_sha256:
            raise ValueError("lineage transition parent digest differs")
        if iteration.certificate_sha256 != certificate.loop_certificate_sha256:
            raise ValueError("lineage transition iteration has another certificate")
        route_evidence = _parent._validate_route_evidence_record(
            values["parent_route_evidence"]
        )
        if values["parent_route_evidence_sha256"] != route_evidence.evidence_sha256:
            raise ValueError("lineage transition route-evidence digest differs")
        if (
            route_evidence.certificate_sha256
            != certificate.route_evidence_certificate_sha256
        ):
            raise ValueError("lineage transition evidence has another certificate")
        _parent._require_iteration_evidence_binding(iteration, route_evidence)
        run_id = _exact_uint64(values["run_id"], name="transition.run_id")
        step_index = _exact_uint64(values["step_index"], name="transition.step_index")
        proposal_index = _exact_uint64(
            values["proposal_index"], name="transition.proposal_index"
        )
        if proposal_index != iteration.proposal_index:
            raise ValueError("lineage transition proposal index differs")
        proposal = iteration.route_draw.candidate.proposal
        if values["edit_kind"] != proposal.kind.value:
            raise ValueError("lineage transition edit kind differs")
        accepted = _exact_bool(values["accepted"], name="transition.accepted")
        if accepted is not iteration.accepted:
            raise ValueError("lineage transition acceptance differs")
        source_index = values["source_occurrence_index"]
        if source_index is not None:
            source_index = _exact_uint64(
                source_index, name="transition.source_occurrence_index"
            )
        if source_index != proposal.source_occurrence_index:
            raise ValueError("lineage transition source index differs")
        pre_state = _validate_state(values["pre_state"])
        post_state = _validate_state(values["post_state"])
        if pre_state.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("lineage transition pre-state has another certificate")
        if post_state.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("lineage transition post-state has another certificate")
        if pre_state.run_id != run_id or post_state.run_id != run_id:
            raise ValueError("lineage transition state uses another run")
        if values["pre_state_sha256"] != pre_state.state_sha256:
            raise ValueError("lineage transition pre-state digest differs")
        if values["post_state_sha256"] != post_state.state_sha256:
            raise ValueError("lineage transition post-state digest differs")
        (
            expected_selected,
            expected_destroyed,
            expected_created,
            expected_post,
        ) = _derive_lineage_edit(
            certificate,
            iteration,
            values["pre_state"],
            step_index=step_index,
        )
        selected = values["selected_source_identifier"]
        selected_sha = values["selected_source_identifier_sha256"]
        if expected_selected is None:
            if selected is not None or selected_sha is not None:
                raise ValueError("lineage transition has an unexpected selected source")
        else:
            checked_selected = _validate_identifier(selected)
            if selected is not expected_selected:
                raise ValueError("lineage transition selected another source object")
            if selected_sha != checked_selected.identifier_sha256:
                raise ValueError("lineage transition selected-source digest differs")
        destroyed = values["destroyed_identifier"]
        destroyed_sha = values["destroyed_identifier_sha256"]
        if expected_destroyed is None:
            if destroyed is not None or destroyed_sha is not None:
                raise ValueError("lineage transition has an unexpected destruction")
        else:
            checked_destroyed = _validate_identifier(destroyed)
            if destroyed is not expected_destroyed:
                raise ValueError("lineage transition destroyed another identifier")
            if destroyed_sha != checked_destroyed.identifier_sha256:
                raise ValueError(
                    "lineage transition destroyed-identifier digest differs"
                )
        created = values["created_occurrence"]
        created_sha = values["created_occurrence_sha256"]
        if expected_created is None:
            if created is not None or created_sha is not None:
                raise ValueError("lineage transition has an unexpected creation")
        else:
            checked_created = _validate_occurrence(created)
            if checked_created.occurrence_sha256 != expected_created.occurrence_sha256:
                raise ValueError("lineage transition created occurrence differs")
            if created_sha != checked_created.occurrence_sha256:
                raise ValueError("lineage transition created-occurrence digest differs")
            if any(created is occurrence for occurrence in pre_state.occurrences):
                raise ValueError("created occurrence was already live before the edit")
            if sum(created is occurrence for occurrence in post_state.occurrences) != 1:
                raise ValueError(
                    "created occurrence is not the exact unique post-state object"
                )
        if not _state_values_match(post_state, expected_post):
            raise ValueError("lineage transition post-state differs from replay")
        if accepted:
            expected_live = list(pre_state.occurrences)
            expected_retired = list(pre_state.retired_identifiers)
            if source_index is not None:
                removed = expected_live.pop(source_index)
                if destroyed is not removed.identifier:
                    raise ValueError(
                        "accepted edit did not destroy the exact indexed lineage"
                    )
                expected_retired.append(destroyed)
            if created is not None:
                expected_live.append(created)
            expected_live = sorted(
                expected_live,
                key=lambda occurrence: occurrence.event.model_key(),
            )
            if len(expected_live) != len(post_state.occurrences) or any(
                supplied is not expected
                for supplied, expected in zip(
                    post_state.occurrences,
                    expected_live,
                )
            ):
                raise ValueError("accepted edit changed survivor identity or order")
            if len(expected_retired) != len(post_state.retired_identifiers) or any(
                supplied is not expected
                for supplied, expected in zip(
                    post_state.retired_identifiers,
                    expected_retired,
                )
            ):
                raise ValueError("accepted edit changed retired-lineage custody")
        expected_flags = {
            "rejection_reused_exact_state": not accepted,
            "accepted_allocated_fresh_serial": accepted
            and proposal.kind in (HybridJumpKind.BIRTH, HybridJumpKind.REPLACEMENT),
            "accepted_destroyed_exact_index": accepted
            and proposal.kind in (HybridJumpKind.DEATH, HybridJumpKind.REPLACEMENT),
            "stable_model_key_sort_only": True,
            "identifiers_absent_from_model_projection": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="transition.%s" % name) is not expected:
                raise ValueError("lineage transition %s differs" % name)
        if not accepted and values["post_state"] is not values["pre_state"]:
            raise ValueError("rejected lineage transition did not reuse exact state")
        if accepted and values["post_state"] is values["pre_state"]:
            raise ValueError("accepted lineage transition reused its pre-state")
        for name in (
            "certificate_sha256",
            "parent_iteration_sha256",
            "parent_route_evidence_sha256",
            "pre_state_sha256",
            "post_state_sha256",
            "transition_sha256",
        ):
            _thinning._require_sha256(values[name], name="transition.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "parent_iteration",
                "parent_route_evidence",
                "selected_source_identifier",
                "destroyed_identifier",
                "created_occurrence",
                "pre_state",
                "post_state",
                "transition_sha256",
            )
        )
        if values["transition_sha256"] != expected_digest:
            raise ValueError("operational lineage transition digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational lineage transitions are not pickle objects")


def _transition_fields() -> Tuple[str, ...]:
    return tuple(OperationalLineageTransition.__annotations__)


def _validate_transition(
    transition: object,
) -> OperationalLineageTransition:
    if type(transition) is not OperationalLineageTransition:
        raise TypeError("transition must be an exact OperationalLineageTransition")
    return OperationalLineageTransition(
        **{name: getattr(transition, name) for name in _transition_fields()},
        _construction_token=_TRANSITION_TOKEN,
    )


def _make_transition(
    certificate: CounterKeyedLineageCertificate,
    iteration: _loop.OperationalProposalIteration,
    route_evidence: _route_evidence.OperationalReferenceRouteEvidence,
    pre_state: OperationalLineageState,
    *,
    run_id: int,
    step_index: int,
) -> OperationalLineageTransition:
    checked_evidence = _parent._validate_route_evidence_record(route_evidence)
    _parent._require_iteration_evidence_binding(iteration, checked_evidence)
    selected, destroyed, created, post_state = _derive_lineage_edit(
        certificate, iteration, pre_state, step_index=step_index
    )
    proposal = iteration.route_draw.candidate.proposal
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "parent_iteration": iteration,
        "parent_iteration_sha256": iteration.iteration_sha256,
        "parent_route_evidence": route_evidence,
        "parent_route_evidence_sha256": checked_evidence.evidence_sha256,
        "run_id": run_id,
        "step_index": step_index,
        "proposal_index": iteration.proposal_index,
        "edit_kind": proposal.kind.value,
        "accepted": iteration.accepted,
        "source_occurrence_index": proposal.source_occurrence_index,
        "selected_source_identifier": selected,
        "selected_source_identifier_sha256": (
            None if selected is None else selected.identifier_sha256
        ),
        "destroyed_identifier": destroyed,
        "destroyed_identifier_sha256": (
            None if destroyed is None else destroyed.identifier_sha256
        ),
        "created_occurrence": created,
        "created_occurrence_sha256": (
            None if created is None else created.occurrence_sha256
        ),
        "pre_state": pre_state,
        "pre_state_sha256": pre_state.state_sha256,
        "post_state": post_state,
        "post_state_sha256": post_state.state_sha256,
        "rejection_reused_exact_state": not iteration.accepted,
        "accepted_allocated_fresh_serial": iteration.accepted
        and proposal.kind in (HybridJumpKind.BIRTH, HybridJumpKind.REPLACEMENT),
        "accepted_destroyed_exact_index": iteration.accepted
        and proposal.kind in (HybridJumpKind.DEATH, HybridJumpKind.REPLACEMENT),
        "stable_model_key_sort_only": True,
        "identifiers_absent_from_model_projection": True,
        "transition_sha256": _ZERO_SHA256,
    }
    values["transition_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "parent_iteration",
            "parent_route_evidence",
            "selected_source_identifier",
            "destroyed_identifier",
            "created_occurrence",
            "pre_state",
            "post_state",
            "transition_sha256",
        )
    )
    return OperationalLineageTransition(**values, _construction_token=_TRANSITION_TOKEN)


@dataclass(frozen=True, eq=False, init=False)
class OperationalLocalThinningLineageResult:
    """Post-hoc lineage annotation of one validated checkpoint-22 result."""

    certificate: CounterKeyedLineageCertificate
    certificate_sha256: str
    parent_result: _parent.OperationalLocalThinningRouteEvidence
    parent_result_sha256: str
    run_id: int
    step_index: int
    initial_state: OperationalLineageState
    initial_state_sha256: str
    transitions: Tuple[OperationalLineageTransition, ...]
    transition_sha256s: Tuple[str, ...]
    final_state: OperationalLineageState
    final_state_sha256: str
    initial_model_state_sha256: str
    final_model_state_sha256: str
    terminal_waiting_draw_sha256: str
    proposal_count: int
    accepted_count: int
    rejected_count: int
    created_lineage_count: int
    destroyed_lineage_count: int
    parent_result_revalidated: bool
    terminal_reused_exact_lineage_state: bool
    checkpoint22_execution_was_proposal_keyed: bool
    checkpoint22_execution_used_contract_streams: bool
    identifiers_absent_from_model_projection: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLocalThinningLineageResult cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("operational lineage results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational lineage result fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("operational lineage result certificate differs")
        parent_result = values["parent_result"]
        if type(parent_result) is not _parent.OperationalLocalThinningRouteEvidence:
            raise TypeError("lineage parent result has the wrong exact type")
        _parent.OperationalLocalThinningRouteEvidence(
            **{name: getattr(parent_result, name) for name in _parent._result_fields()},
            _construction_token=_parent._RESULT_TOKEN,
        )
        if values["parent_result_sha256"] != parent_result.result_sha256:
            raise ValueError("operational lineage parent-result digest differs")
        if parent_result.certificate_sha256 != certificate.parent_certificate_sha256:
            raise ValueError(
                "operational lineage result has another parent certificate"
            )
        run_id = _exact_uint64(values["run_id"], name="lineage_result.run_id")
        step_index = _exact_uint64(
            values["step_index"], name="lineage_result.step_index"
        )
        initial_state = _validate_state(values["initial_state"])
        final_state = _validate_state(values["final_state"])
        if initial_state.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("lineage result initial state has another certificate")
        if final_state.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("lineage result final state has another certificate")
        if initial_state.run_id != run_id or final_state.run_id != run_id:
            raise ValueError("lineage result state uses another run")
        if values["initial_state_sha256"] != initial_state.state_sha256:
            raise ValueError("lineage result initial-state digest differs")
        if values["final_state_sha256"] != final_state.state_sha256:
            raise ValueError("lineage result final-state digest differs")
        loop_result = parent_result.loop_result
        if initial_state.model_configuration != (
            loop_result.initial_intensity.source_configuration
        ):
            raise ValueError("lineage result initial model projection differs")
        if final_state.model_configuration != loop_result.final_configuration:
            raise ValueError("lineage result final model projection differs")
        if values["initial_model_state_sha256"] != initial_state.model_state_sha256:
            raise ValueError("lineage result initial model digest differs")
        if values["final_model_state_sha256"] != final_state.model_state_sha256:
            raise ValueError("lineage result final model digest differs")
        if (
            values["terminal_waiting_draw_sha256"]
            != loop_result.terminal_waiting_draw_sha256
        ):
            raise ValueError("lineage result terminal waiting digest differs")
        if type(values["transitions"]) is not tuple:
            raise TypeError("lineage result transitions must be an exact tuple")
        if type(values["transition_sha256s"]) is not tuple:
            raise TypeError("lineage transition digests must be an exact tuple")
        if len(values["transitions"]) > _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS:
            raise ValueError("lineage result transition tuple exceeds its bound")
        if len(values["transitions"]) != loop_result.proposal_count:
            raise ValueError("lineage result transition count differs")
        transitions = tuple(
            _validate_transition(transition) for transition in values["transitions"]
        )
        if values["transition_sha256s"] != tuple(
            transition.transition_sha256 for transition in transitions
        ):
            raise ValueError("lineage result transition digest sequence differs")
        current_state = values["initial_state"]
        created_count = 0
        destroyed_count = 0
        for index, (iteration, evidence, transition) in enumerate(
            zip(
                loop_result.iterations,
                parent_result.route_evidences,
                transitions,
            )
        ):
            if transition.certificate is not certificate:
                raise ValueError("lineage transition has another certificate object")
            if transition.parent_iteration is not iteration:
                raise ValueError("lineage transition has another parent iteration")
            if transition.parent_route_evidence is not evidence:
                raise ValueError("lineage transition has another route evidence")
            if transition.run_id != run_id or transition.step_index != step_index:
                raise ValueError("lineage transition address differs from result")
            if transition.proposal_index != index:
                raise ValueError("lineage transition indices are not contiguous")
            if transition.pre_state is not current_state:
                raise ValueError("lineage transition did not use the exact prior state")
            current_state = transition.post_state
            created_count += int(transition.created_occurrence is not None)
            destroyed_count += int(transition.destroyed_identifier is not None)
        if values["final_state"] is not current_state:
            raise ValueError(
                "lineage result final state is not the exact chain terminal"
            )
        for name in (
            "proposal_count",
            "accepted_count",
            "rejected_count",
            "created_lineage_count",
            "destroyed_lineage_count",
        ):
            _loop._exact_nonnegative_integer(
                values[name], name="lineage_result.%s" % name
            )
        expected_counts = {
            "proposal_count": loop_result.proposal_count,
            "accepted_count": loop_result.accepted_count,
            "rejected_count": loop_result.rejected_count,
            "created_lineage_count": created_count,
            "destroyed_lineage_count": destroyed_count,
        }
        for name, expected in expected_counts.items():
            if values[name] != expected:
                raise ValueError("lineage result %s differs" % name)
        expected_booleans = {
            "parent_result_revalidated": True,
            "terminal_reused_exact_lineage_state": True,
            "checkpoint22_execution_was_proposal_keyed": False,
            "checkpoint22_execution_used_contract_streams": False,
            "identifiers_absent_from_model_projection": True,
        }
        for name, expected in expected_booleans.items():
            if (
                _exact_bool(values[name], name="lineage_result.%s" % name)
                is not expected
            ):
                raise ValueError("lineage result %s differs" % name)
        for name in (
            "certificate_sha256",
            "parent_result_sha256",
            "initial_state_sha256",
            "final_state_sha256",
            "initial_model_state_sha256",
            "final_model_state_sha256",
            "terminal_waiting_draw_sha256",
            "result_sha256",
        ):
            _thinning._require_sha256(values[name], name="lineage_result.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "parent_result",
                "initial_state",
                "transitions",
                "final_state",
                "result_sha256",
            )
        )
        if values["result_sha256"] != expected_digest:
            raise ValueError("operational lineage result digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational lineage results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(OperationalLocalThinningLineageResult.__annotations__)


def _validate_result_record(
    result: object,
) -> OperationalLocalThinningLineageResult:
    if type(result) is not OperationalLocalThinningLineageResult:
        raise TypeError("result must be an exact OperationalLocalThinningLineageResult")
    return OperationalLocalThinningLineageResult(
        **{name: getattr(result, name) for name in _result_fields()},
        _construction_token=_RESULT_TOKEN,
    )


def _make_lineage_result(
    certificate: CounterKeyedLineageCertificate,
    parent_result: _parent.OperationalLocalThinningRouteEvidence,
    initial_state: OperationalLineageState,
    transitions: Tuple[OperationalLineageTransition, ...],
    *,
    run_id: int,
    step_index: int,
) -> OperationalLocalThinningLineageResult:
    final_state = initial_state if not transitions else transitions[-1].post_state
    loop_result = parent_result.loop_result
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "parent_result": parent_result,
        "parent_result_sha256": parent_result.result_sha256,
        "run_id": run_id,
        "step_index": step_index,
        "initial_state": initial_state,
        "initial_state_sha256": initial_state.state_sha256,
        "transitions": transitions,
        "transition_sha256s": tuple(
            transition.transition_sha256 for transition in transitions
        ),
        "final_state": final_state,
        "final_state_sha256": final_state.state_sha256,
        "initial_model_state_sha256": initial_state.model_state_sha256,
        "final_model_state_sha256": final_state.model_state_sha256,
        "terminal_waiting_draw_sha256": loop_result.terminal_waiting_draw_sha256,
        "proposal_count": loop_result.proposal_count,
        "accepted_count": loop_result.accepted_count,
        "rejected_count": loop_result.rejected_count,
        "created_lineage_count": sum(
            int(transition.created_occurrence is not None) for transition in transitions
        ),
        "destroyed_lineage_count": sum(
            int(transition.destroyed_identifier is not None)
            for transition in transitions
        ),
        "parent_result_revalidated": True,
        "terminal_reused_exact_lineage_state": True,
        "checkpoint22_execution_was_proposal_keyed": False,
        "checkpoint22_execution_used_contract_streams": False,
        "identifiers_absent_from_model_projection": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "parent_result",
            "initial_state",
            "transitions",
            "final_state",
            "result_sha256",
        )
    )
    return OperationalLocalThinningLineageResult(
        **values, _construction_token=_RESULT_TOKEN
    )


class CounterKeyedLineageContractOwner:
    """Immutable owner of standalone addresses and post-hoc lineage overlays."""

    __slots__ = (
        "_parent_owner",
        "_certified_parent_owner",
        "_loop_owner",
        "_route_evidence_owner",
        "_thinning_owner",
        "_reference_composer",
        "_contract_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedLineageContractOwner cannot be subclassed")

    def __init__(
        self,
        parent_owner: _parent.BoundedOperationalThinningLoopRouteEvidence,
        contract_role_sha256: str,
        certificate: CounterKeyedLineageCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("counter-keyed lineage owners require certification")
        if (
            type(parent_owner)
            is not _parent.BoundedOperationalThinningLoopRouteEvidence
        ):
            raise TypeError("parent_owner has the wrong exact type")
        role = _thinning._require_sha256(
            contract_role_sha256, name="contract_role_sha256"
        )
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.contract_role_sha256 != role:
            raise ValueError("counter-keyed lineage role differs from certificate")
        object.__setattr__(self, "_parent_owner", parent_owner)
        object.__setattr__(self, "_certified_parent_owner", parent_owner)
        object.__setattr__(self, "_loop_owner", parent_owner.loop_owner)
        object.__setattr__(
            self, "_route_evidence_owner", parent_owner.route_evidence_owner
        )
        object.__setattr__(self, "_thinning_owner", parent_owner.thinning_owner)
        object.__setattr__(self, "_reference_composer", parent_owner.reference_composer)
        object.__setattr__(self, "_contract_role_sha256", role)
        object.__setattr__(self, "_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CounterKeyedLineageContractOwner is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CounterKeyedLineageContractOwner is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("counter-keyed lineage owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedLineageCertificate:
        return self._certificate

    @property
    def parent_owner(
        self,
    ) -> _parent.BoundedOperationalThinningLoopRouteEvidence:
        return self._parent_owner

    @property
    def loop_owner(self) -> _loop.BoundedOperationalThinningLoop:
        return self._loop_owner

    @property
    def route_evidence_owner(
        self,
    ) -> _route_evidence.ContinuousRouteEvidenceOwner:
        return self._route_evidence_owner

    @property
    def thinning_owner(self) -> _thinning.OperationalJumpThinning:
        return self._thinning_owner

    @property
    def reference_composer(self):  # type: ignore[no-untyped-def]
        return self._reference_composer

    def _require_live_binding(self) -> CounterKeyedLineageCertificate:
        _thinning._require_binary64_environment()
        if (
            type(self._parent_owner)
            is not _parent.BoundedOperationalThinningLoopRouteEvidence
        ):
            raise TypeError("parent owner has the wrong exact type")
        if self._parent_owner is not self._certified_parent_owner:
            raise ValueError("counter-keyed lineage parent-owner binding changed")
        parent_certificate = self._parent_owner._require_live_binding()
        if self._parent_owner.loop_owner is not self._loop_owner:
            raise ValueError("counter-keyed lineage loop-owner binding changed")
        if self._parent_owner.route_evidence_owner is not self._route_evidence_owner:
            raise ValueError("counter-keyed route-evidence-owner binding changed")
        if self._parent_owner.thinning_owner is not self._thinning_owner:
            raise ValueError("counter-keyed thinning-owner binding changed")
        if self._parent_owner.reference_composer is not self._reference_composer:
            raise ValueError("counter-keyed reference-composer binding changed")
        if self.certificate.contract_runtime_sha256 != _runtime_sha256():
            raise ValueError("live counter-keyed lineage runtime differs")
        expected = _make_certificate(
            parent_certificate,
            contract_role_sha256=self._contract_role_sha256,
        )
        for name in _certificate_fields():
            if not _thinning._field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "counter-keyed lineage certificate field %s differs" % name
                )
        _thinning._require_binary64_environment()
        return self.certificate

    def _make_domain_stream(
        self,
        *,
        domain: str,
        run_id: object,
        step_index: object,
        occurrence_serial: object,
        proposal_index: object,
    ) -> CounterKeyedPhiloxStream:
        self._require_live_binding()
        checked_run = _exact_uint64(run_id, name="run_id")
        checked_step = _exact_uint64(step_index, name="step_index")
        checked_occurrence = _exact_uint64(occurrence_serial, name="occurrence_serial")
        checked_proposal = _exact_uint64(proposal_index, name="proposal_index")
        address = _make_address(
            self.certificate,
            domain=domain,
            run_id=checked_run,
            step_index=checked_step,
            occurrence_serial=checked_occurrence,
            proposal_index=checked_proposal,
        )
        stream = _make_stream(self.certificate, address)
        self.validate_stream(stream)
        return stream

    def make_jump_proposal_stream(
        self,
        run_id: object,
        step_index: object,
        proposal_index: object,
    ) -> CounterKeyedPhiloxStream:
        """Issue a standalone jump-proposal namespace receipt.

        The receipt does not state that checkpoint twenty-two consumed it.
        """

        return self._make_domain_stream(
            domain=COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=0,
            proposal_index=proposal_index,
        )

    def make_terminal_wait_stream(
        self,
        run_id: object,
        step_index: object,
        completed_proposals: object,
    ) -> CounterKeyedPhiloxStream:
        """Issue a standalone terminal-wait namespace receipt."""

        return self._make_domain_stream(
            domain=COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=0,
            proposal_index=completed_proposals,
        )

    def make_initializer_stream(
        self,
        run_id: object,
        step_index: object,
        occurrence_serial: object,
    ) -> CounterKeyedPhiloxStream:
        """Reserve an initializer address; no initializer draw is certified."""

        return self._make_domain_stream(
            domain=COUNTER_KEY_DOMAIN_INITIALIZER,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=occurrence_serial,
            proposal_index=0,
        )

    def make_brownian_left_stream(
        self,
        run_id: object,
        step_index: object,
        occurrence_serial: object,
    ) -> CounterKeyedPhiloxStream:
        """Reserve a left Brownian address; no increment law is certified."""

        return self._make_domain_stream(
            domain=COUNTER_KEY_DOMAIN_BROWNIAN_LEFT,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=occurrence_serial,
            proposal_index=0,
        )

    def make_brownian_right_stream(
        self,
        run_id: object,
        step_index: object,
        occurrence_serial: object,
    ) -> CounterKeyedPhiloxStream:
        """Reserve a right Brownian address; no increment law is certified."""

        return self._make_domain_stream(
            domain=COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=occurrence_serial,
            proposal_index=0,
        )

    def validate_stream(
        self, stream: CounterKeyedPhiloxStream
    ) -> CounterKeyedPhiloxStream:
        """Validate a stream receipt and reconstruct its exact initial state."""

        self._require_live_binding()
        checked = _validate_stream_record(stream)
        if checked.certificate is not self.certificate:
            raise ValueError("counter-keyed stream belongs to another owner")
        generator = _route_evidence._generator_from_snapshot(checked.initial_state)
        reconstructed = _route_evidence._capture_philox_state(generator)
        if reconstructed.snapshot_sha256 != checked.initial_snapshot_sha256:
            raise PluginBridgeCounterKeyedLineageContractError(
                "counter-keyed stream initial snapshot did not reconstruct"
            )
        self._require_live_binding()
        return stream

    def reconstruct_stream(
        self, stream: CounterKeyedPhiloxStream
    ) -> np.random.Generator:
        """Return a fresh local generator at the receipt's exact initial state."""

        self.validate_stream(stream)
        generator = _route_evidence._generator_from_snapshot(stream.initial_state)
        reconstructed = _route_evidence._capture_philox_state(generator)
        if reconstructed.snapshot_sha256 != stream.initial_snapshot_sha256:
            raise PluginBridgeCounterKeyedLineageContractError(
                "fresh counter-keyed stream differs from its receipt"
            )
        return generator

    def bootstrap_lineage(
        self,
        initial_intensity: ReferenceCandidateIntensity,
        *,
        run_id: object,
        initialization_index: object,
    ) -> OperationalLineageState:
        """Lift canonical tuple positions to arbitrary initial labels 1..n.

        Independent bootstraps or deliberate lineage forks must use a fresh
        ``run_id``.  ``initialization_index`` records provenance but is not a
        Philox-address limb, and this owner does not maintain a global run-ID
        registry or prevent duplicate receipt issuance.
        """

        self._require_live_binding()
        checked_intensity = self.reference_composer.validate_candidate_intensity(
            initial_intensity
        )
        checked_run = _exact_uint64(run_id, name="run_id")
        checked_initialization = _exact_uint64(
            initialization_index, name="initialization_index"
        )
        configuration = checked_intensity.source_configuration
        if len(configuration) + 1 > MAX_LINEAGE_NEXT_SERIAL:
            raise PluginBridgeCounterKeyedLineageContractError(
                "initial configuration exhausts lineage serials"
            )
        occurrences = []
        for position, event in enumerate(configuration):
            identifier = _make_identifier(
                self.certificate,
                run_id=checked_run,
                serial=position + 1,
                origin_kind=_INITIAL_ORIGIN,
                origin_initialization_index=checked_initialization,
                origin_initial_position=position,
            )
            occurrences.append(_make_occurrence(self.certificate, identifier, event))
        result = _make_state(
            self.certificate,
            run_id=checked_run,
            initialization_index=checked_initialization,
            occurrences=tuple(occurrences),
            retired_identifiers=(),
            next_serial=len(occurrences) + 1,
        )
        self._require_live_binding()
        return result

    def _validate_parent_result(
        self,
        parent_result: _parent.OperationalLocalThinningRouteEvidence,
    ) -> _parent.OperationalLocalThinningRouteEvidence:
        if type(parent_result) is not _parent.OperationalLocalThinningRouteEvidence:
            raise TypeError("parent_result has the wrong exact type")
        loop_result = parent_result.loop_result
        return self.parent_owner.validate_result(
            parent_result,
            loop_result.initial_intensity,
            loop_result.initial_envelope,
            clock_start=loop_result.clock_start,
            right_endpoint=loop_result.right_endpoint,
            proposal_budget=loop_result.proposal_budget,
            base_context=loop_result.base_context,
            residual_context=loop_result.residual_context,
        )

    def _require_initial_state_for_step(
        self,
        initial_state: OperationalLineageState,
        parent_result: _parent.OperationalLocalThinningRouteEvidence,
        *,
        run_id: int,
        step_index: int,
    ) -> OperationalLineageState:
        checked = _validate_state(initial_state)
        if checked.certificate_sha256 != self.certificate.certificate_sha256:
            raise ValueError("initial lineage state belongs to another certificate")
        if checked.run_id != run_id:
            raise ValueError("initial lineage state belongs to another run")
        if checked.model_configuration != (
            parent_result.loop_result.initial_intensity.source_configuration
        ):
            raise ValueError("initial lineage projection differs from parent source")
        for identifier in (
            tuple(occurrence.identifier for occurrence in checked.occurrences)
            + checked.retired_identifiers
        ):
            if (
                identifier.origin_kind in (_BIRTH_ORIGIN, _REPLACEMENT_ORIGIN)
                and identifier.origin_step_index >= step_index
            ):
                raise ValueError("pre-existing edit lineage does not precede this step")
        return initial_state

    def annotate_result(
        self,
        parent_result: _parent.OperationalLocalThinningRouteEvidence,
        initial_state: OperationalLineageState,
        *,
        run_id: object,
        step_index: object,
    ) -> OperationalLocalThinningLineageResult:
        """Revalidate and deterministically annotate one parent transcript."""

        self._require_live_binding()
        checked_parent = self._validate_parent_result(parent_result)
        checked_run = _exact_uint64(run_id, name="run_id")
        checked_step = _exact_uint64(step_index, name="step_index")
        current = self._require_initial_state_for_step(
            initial_state,
            checked_parent,
            run_id=checked_run,
            step_index=checked_step,
        )
        transitions = []
        for iteration, evidence in zip(
            checked_parent.loop_result.iterations,
            checked_parent.route_evidences,
        ):
            transition = _make_transition(
                self.certificate,
                iteration,
                evidence,
                current,
                run_id=checked_run,
                step_index=checked_step,
            )
            transitions.append(transition)
            current = transition.post_state
        result = _make_lineage_result(
            self.certificate,
            checked_parent,
            initial_state,
            tuple(transitions),
            run_id=checked_run,
            step_index=checked_step,
        )
        self.validate_lineage_result(
            result,
            initial_state,
            run_id=checked_run,
            step_index=checked_step,
        )
        self._require_live_binding()
        return result

    def validate_lineage_result(
        self,
        result: OperationalLocalThinningLineageResult,
        initial_state: OperationalLineageState,
        *,
        run_id: object,
        step_index: object,
    ) -> OperationalLocalThinningLineageResult:
        """Replay lineage without accepting or advancing a caller-owned RNG.

        Transitive checkpoint-twenty-two validation may advance fresh local
        replay generators.  It does not consume a checkpoint-twenty-three
        address receipt.
        """

        self._require_live_binding()
        checked_run = _exact_uint64(run_id, name="run_id")
        checked_step = _exact_uint64(step_index, name="step_index")
        checked_result = _validate_result_record(result)
        if checked_result.certificate is not self.certificate:
            raise ValueError("lineage result belongs to another owner")
        if result.initial_state is not initial_state:
            raise ValueError("lineage validation requires the exact initial state")
        if result.run_id != checked_run or result.step_index != checked_step:
            raise ValueError("lineage validation run or step differs")
        checked_parent = self._validate_parent_result(result.parent_result)
        self._require_initial_state_for_step(
            initial_state,
            checked_parent,
            run_id=checked_run,
            step_index=checked_step,
        )
        replayed = []
        current = initial_state
        for iteration, evidence in zip(
            checked_parent.loop_result.iterations,
            checked_parent.route_evidences,
        ):
            transition = _make_transition(
                self.certificate,
                iteration,
                evidence,
                current,
                run_id=checked_run,
                step_index=checked_step,
            )
            replayed.append(transition)
            current = transition.post_state
        if tuple(item.transition_sha256 for item in replayed) != (
            result.transition_sha256s
        ):
            raise ValueError("lineage result differs from deterministic replay")
        if result.final_state.state_sha256 != current.state_sha256:
            raise ValueError("lineage result final state differs from replay")
        self._require_live_binding()
        return result


def certify_plugin_bridge_counter_keyed_lineage_contract(
    parent_owner: _parent.BoundedOperationalThinningLoopRouteEvidence,
    *,
    contract_policy: object,
    contract_role_sha256: object,
) -> CounterKeyedLineageContractOwner:
    """Certify the checkpoint-twenty-three additive contract."""

    if type(contract_policy) is not str:
        raise TypeError("contract_policy must be exact text")
    if contract_policy != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY:
        raise ValueError("only the exported counter-keyed lineage policy is supported")
    role = _thinning._require_sha256(contract_role_sha256, name="contract_role_sha256")
    if type(parent_owner) is not _parent.BoundedOperationalThinningLoopRouteEvidence:
        raise TypeError("parent_owner has the wrong exact type")
    parent_certificate = parent_owner._require_live_binding()
    certificate = _make_certificate(parent_certificate, contract_role_sha256=role)
    owner = CounterKeyedLineageContractOwner(
        parent_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_lineage_contract(
    parent_owner: _parent.BoundedOperationalThinningLoopRouteEvidence,
    owner: CounterKeyedLineageContractOwner,
    *,
    contract_policy: object,
    contract_role_sha256: object,
) -> CounterKeyedLineageContractOwner:
    """Require exact parent identity, role, policy, and live transitive custody."""

    if type(contract_policy) is not str:
        raise TypeError("contract_policy must be exact text")
    if contract_policy != PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY:
        raise ValueError("only the exported counter-keyed lineage policy is supported")
    role = _thinning._require_sha256(contract_role_sha256, name="contract_role_sha256")
    if type(owner) is not CounterKeyedLineageContractOwner:
        raise TypeError("owner must be an exact CounterKeyedLineageContractOwner")
    if owner.parent_owner is not parent_owner:
        raise ValueError("counter-keyed lineage owner uses another parent owner")
    if owner.certificate.contract_role_sha256 != role:
        raise ValueError("counter-keyed lineage owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_counter_keyed_lineage_certificate(
    parent_owner: _parent.BoundedOperationalThinningLoopRouteEvidence,
    owner: CounterKeyedLineageContractOwner,
    *,
    contract_policy: object,
    contract_role_sha256: object,
) -> CounterKeyedLineageCertificate:
    """Return the reconstructed live checkpoint-twenty-three certificate."""

    return require_matching_plugin_bridge_counter_keyed_lineage_contract(
        parent_owner,
        owner,
        contract_policy=contract_policy,
        contract_role_sha256=contract_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCOPE",
    "COUNTER_KEYED_PHILOX_ADDRESS_LAYOUT",
    "COUNTER_KEY_DOMAIN_JUMP_PROPOSAL",
    "COUNTER_KEY_DOMAIN_TERMINAL_WAIT",
    "COUNTER_KEY_DOMAIN_INITIALIZER",
    "COUNTER_KEY_DOMAIN_BROWNIAN_LEFT",
    "COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT",
    "COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL",
    "COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT",
    "COUNTER_KEY_DOMAIN_TAG_INITIALIZER",
    "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT",
    "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT",
    "COUNTER_KEY_DOMAIN_TAGS",
    "MAX_UINT64",
    "MAX_LINEAGE_NEXT_SERIAL",
    "MAX_OPERATIONAL_LINEAGE_IDENTIFIERS",
    "CounterKeyedLineageCertificate",
    "CounterKeyedLineageContractOwner",
    "CounterKeyedPhiloxAddress",
    "CounterKeyedPhiloxStream",
    "OperationalLineageIdentifier",
    "OperationalLineagedOccurrence",
    "OperationalLineageState",
    "OperationalLineageTransition",
    "OperationalLocalThinningLineageResult",
    "PluginBridgeCounterKeyedLineageContractError",
    "certify_plugin_bridge_counter_keyed_lineage_contract",
    "require_matching_plugin_bridge_counter_keyed_lineage_contract",
    "validate_plugin_bridge_counter_keyed_lineage_certificate",
]
