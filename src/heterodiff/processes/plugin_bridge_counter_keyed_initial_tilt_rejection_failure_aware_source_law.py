"""Define the failure-aware abstract source law behind CP40.

Checkpoint forty names an exact finite-resolution target only after CP36 and
CP37 have successfully produced one direct word-free batch.  This additive
checkpoint closes the corresponding *abstract* source-level accounting gap.
It partitions CP36's normalized product-word template into proposal/scoring
coordinates ``V`` and one reserved decision coordinate ``W`` per attempt.
Under the already declared counterfactual product-uniform premise, ``V`` and
``W`` are independent.  A separate explicit factorization hypothesis states
that the word-free preparation/failure projection and all quotas are functions
of ``V`` alone; decisions use ``W`` only after every quota has been certified.
The existing CP36--CP40 artifacts motivate but do not prove this functional
noninterference statement, so this module labels and binds it as an assumption.

The predecision map is totalized as

``G(V) in {Failure36, Failure37} disjoint-union successful batches B``.

The exact fiber counts of ``G`` define symbolic masses.  Composing each
successful fiber with CP40's fixed-``B`` dyadic kernel gives one normalized law
on configurations plus distinct preparation-failure, quota-failure, and
exhaustion atoms.  The empty configuration remains a configuration atom.
No fiber is enumerated and no numeric failure, batch, configuration, or global
selection probability is materialized.

The ideal comparison is gated by the same successful predecision map.  If the
successful-source mass ``rho`` is zero, ideal and dyadic augmented laws agree.
If ``rho`` is positive, their total variation is strictly below
``rho*A/2**64``; universally it is strictly below ``A/2**64``.  If the global
dyadic selection mass ``S_Q`` is positive, the selected-conditioned distance
is strictly below ``rho*A/(2**64*S_Q)``.  The coefficient-one conditioning
bound follows from dividing by the larger of the ideal and dyadic selection
masses.  When ``S_Q`` is zero, the dyadic selected law and comparison bound
are undefined; the ideal selected law can still exist when ``S_P`` is positive.

These are finite, symbolic pushforward definitions under a separate abstract
premise.  They are not a law for live fixed-address Philox replay, not a live
initializer distribution, not ungated exact ideal rejection, and not the
normalized global analytic plug-in tilt.  ``describe`` calls no CP40 admit,
CP39 coordinate, CP38 resolve, CP37 decide, or CP36 prepare operation.

Hashes and runtime identities are same-process procedural custody witnesses
under a trusted unchanged runtime.  They are not cryptographic authentication
or cross-runtime portability guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_admission as _admission,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "failure-aware rejection source laws require the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise


PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-failure-aware-source-law-v1"
)
PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_POLICY = (
    "exact-checkpoint40-owner-and-transitive-checkpoint38-37-36-binding;"
    "normalized-cp36-coordinate-partition-proposal-versus-reserved-decision;"
    "word-free-predecision-factorization-before-decision-word-use;"
    "abstract-product-uniform-proposal-decision-independence-premise;"
    "distinct-preparation-failure-quota-failure-exhaustion-and-state-atoms;"
    "exact-symbolic-fiber-count-mixture-and-normalization;"
    "quota-gated-ideal-comparison-and-rho-zero-identity;"
    "universal-strict-A-over-2^64-augmented-bound;"
    "positive-global-selection-factor-one-conditioning-bound;"
    "arbitrary-joint-source-data-processing-only;"
    "no-parent-operation-enumeration-rng-live-law-or-numeric-mass-v1"
)
PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCOPE = (
    "finite-symbolic-product-uniform-failure-aware-source-kernel;"
    "normalized-logical-coordinate-template-and-finite-preimage-definitions;"
    "not-live-philox-source-uniformity-independence-or-randomness;"
    "not-numeric-failure-batch-state-exhaustion-or-selection-probabilities;"
    "not-arbitrary-dependent-source-product-mixture;"
    "not-live-initializer-admission-or-live-exception-relabeling;"
    "not-ungated-exact-ideal-rejection-or-normalized-global-analytic-tilt;"
    "not-all-strategy-formal-test28-tag3-brownian-path-liveness-or-sampler;"
    "not-scientific-model-quality-generality-or-manuscript-evidence;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_ATOMS = (
    "preparation_failure",
    "quota_certification_failure",
    "exhaustion",
    "configuration",
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_PREMISE = (
    "V-is-product-uniform-on-D^M;W-is-product-uniform-on-D^A;V-independent-of-W;"
    "explicit-predecision-factorization-hypothesis-required;counterfactual-"
    "abstract-variables-only;not-live-Philox"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE = (
    "the-direct-word-free-CP36-success-or-failure-projection-and-the-complete-"
    "CP37-quota-tuple-depend-only-on-proposal-scoring-coordinates-V;reserved-"
    "decision-coordinates-W-are-used-only-after-all-quotas-are-certified"
)
INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCHEMA_VERSION = (
    "initial-tilt-rejection-predecision-factorization-hypothesis-v1"
)
INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCOPE = (
    "fixed-CP40-transitive-CP36-CP38-hypotheses-and-normalized-coordinate-"
    "partition;assumed-functional-noninterference-of-word-free-predecision-"
    "failure-success-batch-from-reserved-decision-words;not-proved-by-current-"
    "executable-evaluator-and-not-a-live-Philox-statement"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_FIBER_DEFINITION = (
    "G(V)=F36-or-F37-or-B;N36=card(G^-1(F36));N37=card(G^-1(F37));"
    "N_B=card(G^-1(B));phi36=N36/D^M;phi37=N37/D^M;"
    "lambda_B=N_B/D^M;rho=sum_B(lambda_B)=1-phi36-phi37"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_LAW = (
    "Q(F36)=phi36;Q(F37)=phi37;Q(E)=sum_B(lambda_B*e_B);"
    "Q(x)=sum_B(lambda_B*m_B(x));duplicates-aggregate-within-and-across-B"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_NORMALIZATION_THEOREM = (
    "phi36+phi37+sum_B(lambda_B*(e_B+sum_x(m_B(x))))=1;"
    "empty-configuration-is-a-configuration-atom-distinct-from-E-F36-F37"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_TV_THEOREM = (
    "if-rho=0-then-TV(P_aug,Q_aug)=0;if-rho>0-then-"
    "TV(P_aug,Q_aug)<rho*A/D;universally-TV(P_aug,Q_aug)<A/D;D=2^64"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM = (
    "S_P=sum_B(lambda_B*Z_B^*)>=S_Q=sum_B(lambda_B*Z_B);if-S_Q=0-dyadic-"
    "selected-law-and-bound-undefined;Delta=TV(P_aug,Q_aug);if-S_Q>0-then-"
    "TV(P_sel,Q_sel)<=Delta/max(S_P,S_Q)=Delta/S_P<=Delta/S_Q<rho*A/"
    "(D*S_Q)<=A/(D*S_Q)"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_PROOF = (
    "for-selection-set-C-let-a=P(C),b=Q(C),c=L1_C,d=L1_not_C;"
    "eta=abs(a-b)<=d;conditioning-with-denominator-a-gives-TV(P_C,Q_C)<="
    "(c+eta)/(2a)<=TV(P,Q)/a;the-symmetric-bound-gives-TV(P_C,Q_C)<="
    "TV(P,Q)/max(a,b);here-a=S_P>=S_Q=b"
)
INITIAL_TILT_REJECTION_FAILURE_AWARE_DATA_PROCESSING_THEOREM = (
    "for-any-joint-source-nu-on-(V,W),TV(H#nu,H#U)<=TV(nu,U);"
    "no-product-mixture-formula-is-claimed-for-dependent-or-nonuniform-nu"
)

_SCHEMA_VERSION = (
    PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCHEMA_VERSION
)
_POLICY = PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_POLICY
_SCOPE = PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCOPE
_PREMISE = INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_PREMISE
_FACTORIZATION = INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
_FACTORIZATION_HYPOTHESIS_SCHEMA = (
    INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCHEMA_VERSION
)
_FACTORIZATION_HYPOTHESIS_SCOPE = (
    INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCOPE
)
_FIBERS = INITIAL_TILT_REJECTION_FAILURE_AWARE_FIBER_DEFINITION
_LAW = INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_LAW
_NORMALIZATION = INITIAL_TILT_REJECTION_FAILURE_AWARE_NORMALIZATION_THEOREM
_AUGMENTED_TV = INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_TV_THEOREM
_SELECTED_TV = INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM
_SELECTED_PROOF = INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_PROOF
_DATA_PROCESSING = INITIAL_TILT_REJECTION_FAILURE_AWARE_DATA_PROCESSING_THEOREM
_ATOMS = INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_ATOMS
_D = 1 << 64
_MAX_TEXT_LENGTH = 16_384
_MAX_COORDINATES = 65_536
_ZERO_SHA256 = "0" * 64

INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_DYADIC_DENOMINATOR = _D
INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_MAX_COORDINATES = _MAX_COORDINATES

_CERTIFICATE_TOKEN = object()
_SPECIFICATION_TOKEN = object()
_OWNER_TOKEN = object()
_HYPOTHESIS_TOKEN = object()

# CP40 is the only public parent.  All earlier objects are reached through its
# exact frozen ancestry; callers cannot independently splice them into CP41.
_coord = _admission._coord
_law = _admission._law
_decision = _law._decision
_prep = _decision._prep

_CP40_OWNER_TYPE = _admission.CounterKeyedInitialTiltRejectionAdmissionOwner
_CP40_CERT_TYPE = _admission.CounterKeyedInitialTiltRejectionAdmissionCertificate
_CP40_CERTIFICATE_PROPERTY = _CP40_OWNER_TYPE.certificate
_CP40_PARENT_PROPERTY = _CP40_OWNER_TYPE.coordination_owner
_CP40_OWNER_SNAPSHOT = _CP40_OWNER_TYPE._owner_snapshot
_CP40_REQUIRE_OWNER_SNAPSHOT = _CP40_OWNER_TYPE._require_owner_snapshot
_CP40_LIVE_CERTIFICATE = _CP40_OWNER_TYPE._live_certificate
_CP40_VALIDATE_CERTIFICATE = _admission._validate_certificate
_CP40_SURFACE_GUARD = _admission._require_parent_surfaces
_CP40_ADMIT = _CP40_OWNER_TYPE.admit

_CP39_OWNER_TYPE = _coord.CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner
_CP39_CERT_TYPE = (
    _coord.CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
)
_CP39_CERTIFICATE_PROPERTY = _CP39_OWNER_TYPE.certificate
_CP39_PARENT_PROPERTY = _CP39_OWNER_TYPE.finite_batch_law_owner
_CP39_COORDINATE = _CP39_OWNER_TYPE.coordinate

_CP38_OWNER_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawOwner
_CP38_CERT_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
_CP38_CERTIFICATE_PROPERTY = _CP38_OWNER_TYPE.certificate
_CP38_PARENT_PROPERTY = _CP38_OWNER_TYPE.decision_owner
_CP38_HYPOTHESIS_PROPERTY = _CP38_OWNER_TYPE.word_law_hypothesis
_CP38_VALIDATE_CERTIFICATE = _law._validate_certificate
_CP38_RESOLVE = _CP38_OWNER_TYPE.resolve

_CP37_OWNER_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionOwner
_CP37_CERT_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionCertificate
_CP37_CERTIFICATE_PROPERTY = _CP37_OWNER_TYPE.certificate
_CP37_PARENT_PROPERTY = _CP37_OWNER_TYPE.preparation_owner
_CP37_VALIDATE_CERTIFICATE = _decision._validate_certificate
_CP37_DECIDE = _CP37_OWNER_TYPE.decide

_CP36_OWNER_TYPE = _prep.CounterKeyedInitialTiltRejectionPreparationOwner
_CP36_CERT_TYPE = _prep.CounterKeyedInitialTiltRejectionPreparationCertificate
_CP36_CERTIFICATE_PROPERTY = _CP36_OWNER_TYPE.certificate
_CP36_HYPOTHESIS_PROPERTY = _CP36_OWNER_TYPE.word_family_hypothesis
_CP36_VALIDATE_CERTIFICATE = _prep._validate_certificate
_CP36_VALIDATE_HYPOTHESIS = (
    _prep.validate_initial_tilt_rejection_preparation_word_family_hypothesis
)
_CP36_PREPARE = _CP36_OWNER_TYPE.prepare
_CP36_HYPOTHESIS_TYPE = _prep.InitialTiltRejectionPreparationWordFamilyHypothesis

_CP38_HYPOTHESIS_TYPE = _law.FixedBatchIidUint64DecisionWordHypothesis
_CP38_VALIDATE_HYPOTHESIS = (
    _law.validate_fixed_batch_iid_uint64_decision_word_hypothesis
)


class PluginBridgeCounterKeyedInitialTiltRejectionFailureAwareSourceLawError(
    ArithmeticError
):
    """Raised when CP41 procedural custody changes during an operation."""


def _semantic_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError("%s exceeds the text bound" % name)
    if value != expected:
        raise ValueError("%s differs" % name)
    return value


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int = 0,
    maximum: Optional[int] = None,
) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact integer" % name)
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError("%s is outside its bound" % name)
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact Boolean" % name)
    if value is not expected:
        raise ValueError("%s differs" % name)
    return value


def _coordinate_digest(coordinates: Tuple[object, ...]) -> str:
    return _semantic_digest({"logical_word_coordinates": coordinates})


def _validate_coordinate_tuple(
    value: object,
    *,
    name: str,
    expected_length: int,
) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) != expected_length or len(value) > _MAX_COORDINATES:
        raise ValueError("%s has the wrong bounded length" % name)
    checked = []
    for position, coordinate in enumerate(value):
        if type(coordinate) is not tuple or len(coordinate) != 3:
            raise TypeError("%s[%d] is malformed" % (name, position))
        key, counter, offset = coordinate
        if type(key) is not tuple or len(key) != 2:
            raise TypeError("%s[%d].key is malformed" % (name, position))
        if type(counter) is not tuple or len(counter) != 4:
            raise TypeError("%s[%d].counter is malformed" % (name, position))
        checked_key = tuple(
            _exact_integer(item, name="%s[%d].key[%d]" % (name, position, index))
            for index, item in enumerate(key)
        )
        checked_counter = tuple(
            _exact_integer(
                item,
                name="%s[%d].counter[%d]" % (name, position, index),
            )
            for index, item in enumerate(counter)
        )
        checked_offset = _exact_integer(
            offset,
            name="%s[%d].offset" % (name, position),
        )
        checked.append((checked_key, checked_counter, checked_offset))
    return tuple(checked)


def _partition_coordinates(
    certificate: _CP36_CERT_TYPE,
) -> Tuple[
    Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...],
    Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...],
    Tuple[Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...],
]:
    checked = _CP36_VALIDATE_CERTIFICATE(certificate)
    if checked is not certificate:
        raise ValueError("CP36 certificate validation substituted")
    attempt_count = _exact_integer(
        certificate.attempt_budget,
        name="CP36.attempt_budget",
        minimum=1,
        maximum=64,
    )
    block_count = _exact_integer(
        certificate.blocks_per_attempt,
        name="CP36.blocks_per_attempt",
        minimum=1,
        maximum=64,
    )
    if type(certificate.block_raw64_word_counts) is not tuple:
        raise TypeError("CP36 block counts must be an exact tuple")
    if len(certificate.block_raw64_word_counts) != block_count:
        raise ValueError("CP36 block count length differs")
    block_counts = tuple(
        _exact_integer(
            count,
            name="CP36.block_raw64_word_counts[%d]" % index,
            minimum=1,
            maximum=_MAX_COORDINATES,
        )
        for index, count in enumerate(certificate.block_raw64_word_counts)
    )
    if block_counts[-1] != 1:
        raise ValueError("CP36 final reserved-decision block is not one word")
    words_per_attempt = sum(block_counts)
    total = attempt_count * words_per_attempt
    full = _validate_coordinate_tuple(
        certificate.logical_word_coordinates,
        name="CP36.logical_word_coordinates",
        expected_length=total,
    )
    proposal = []
    decision = []
    cursor = 0
    domain_tag = _prep.INITIAL_TILT_REJECTION_DOMAIN_TAG
    stage = _prep.INITIAL_TILT_REJECTION_STAGE_INDEX
    for attempt in range(attempt_count):
        for block, count in enumerate(block_counts):
            for offset in range(count):
                coordinate = full[cursor]
                expected = (
                    (0, domain_tag),
                    (0, 0, stage, attempt * block_count + block),
                    offset,
                )
                if coordinate != expected:
                    raise ValueError("CP36 normalized logical coordinate differs")
                if block == block_count - 1:
                    decision.append(coordinate)
                else:
                    proposal.append(coordinate)
                cursor += 1
    proposal_tuple = tuple(proposal)
    decision_tuple = tuple(decision)
    expected_proposal = attempt_count * certificate.reference_words_per_attempt
    if len(proposal_tuple) != expected_proposal:
        raise ValueError("CP36 proposal coordinate count differs")
    if len(decision_tuple) != attempt_count:
        raise ValueError("CP36 decision coordinate count differs")
    combined = proposal_tuple + decision_tuple
    if len(set(full)) != len(full) or len(set(combined)) != len(full):
        raise ValueError("CP36 coordinate partition is not distinct and complete")
    if set(combined) != set(full):
        raise ValueError("CP36 coordinate partition does not cover the template")
    return full, proposal_tuple, decision_tuple


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    excluded = {
        "checkpoint40_certificate",
        "checkpoint39_certificate",
        "checkpoint38_certificate",
        "checkpoint37_certificate",
        "checkpoint36_certificate",
        "checkpoint36_word_family_hypothesis",
        "checkpoint38_word_law_hypothesis",
        "factorization_hypothesis",
        "certificate_sha256",
    }
    return {name: values[name] for name in values if name not in excluded}


def _hypothesis_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    excluded = {
        "checkpoint36_word_family_hypothesis",
        "checkpoint38_word_law_hypothesis",
        "hypothesis_sha256",
    }
    return {name: values[name] for name in values if name not in excluded}


@dataclass(frozen=True, eq=False, init=False)
class InitialTiltRejectionPredecisionFactorizationHypothesis:
    """Explicit unproved functional-noninterference premise for CP41."""

    schema_version: str
    hypothesis_scope: str
    factorization_premise: str
    checkpoint36_word_family_hypothesis: _CP36_HYPOTHESIS_TYPE
    checkpoint36_word_family_hypothesis_sha256: str
    checkpoint38_word_law_hypothesis: _CP38_HYPOTHESIS_TYPE
    checkpoint38_word_law_hypothesis_sha256: str
    attempt_budget: int
    proposal_word_count: int
    decision_word_count: int
    full_coordinate_sha256: str
    proposal_coordinate_sha256: str
    decision_coordinate_sha256: str
    abstract_functional_noninterference_assumed: bool
    existing_artifacts_motivate_but_do_not_prove_factorization: bool
    executable_arbitrary_word_evaluator_equivalence_proved: bool
    live_preparation_failure_independence_certified: bool
    live_philox_statement: bool
    hypothesis_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("predecision factorization hypotheses cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _HYPOTHESIS_TOKEN:
            raise TypeError("predecision factorization hypotheses are sealed")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("predecision factorization hypothesis is incomplete")
        _validate_factorization_hypothesis_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("predecision factorization hypotheses are not pickleable")


def _factorization_hypothesis_fields() -> Tuple[str, ...]:
    return tuple(InitialTiltRejectionPredecisionFactorizationHypothesis.__annotations__)


def _validate_factorization_hypothesis_values(
    values: Mapping[str, object],
) -> None:
    _require_text(
        values["schema_version"],
        _FACTORIZATION_HYPOTHESIS_SCHEMA,
        name="factorization_hypothesis.schema_version",
    )
    _require_text(
        values["hypothesis_scope"],
        _FACTORIZATION_HYPOTHESIS_SCOPE,
        name="factorization_hypothesis.hypothesis_scope",
    )
    _require_text(
        values["factorization_premise"],
        _FACTORIZATION,
        name="factorization_hypothesis.factorization_premise",
    )
    cp36_hypothesis = values["checkpoint36_word_family_hypothesis"]
    if type(cp36_hypothesis) is not _CP36_HYPOTHESIS_TYPE:
        raise TypeError("factorization hypothesis has the wrong CP36 premise type")
    checked36 = _CP36_VALIDATE_HYPOTHESIS(cp36_hypothesis)
    if checked36 is not cp36_hypothesis:
        raise ValueError("CP36 hypothesis validation substituted")
    cp38_hypothesis = values["checkpoint38_word_law_hypothesis"]
    if type(cp38_hypothesis) is not _CP38_HYPOTHESIS_TYPE:
        raise TypeError("factorization hypothesis has the wrong CP38 premise type")
    checked38 = _CP38_VALIDATE_HYPOTHESIS(cp38_hypothesis)
    if checked38 is not cp38_hypothesis:
        raise ValueError("CP38 hypothesis validation substituted")
    for name, expected in (
        (
            "checkpoint36_word_family_hypothesis_sha256",
            cp36_hypothesis.hypothesis_sha256,
        ),
        (
            "checkpoint38_word_law_hypothesis_sha256",
            cp38_hypothesis.hypothesis_sha256,
        ),
    ):
        digest = _require_sha256(values[name], name="factorization_hypothesis." + name)
        if digest != expected:
            raise ValueError("factorization hypothesis parent digest differs")
    attempt_budget = _exact_integer(
        values["attempt_budget"],
        name="factorization_hypothesis.attempt_budget",
        minimum=1,
        maximum=64,
    )
    proposal_word_count = _exact_integer(
        values["proposal_word_count"],
        name="factorization_hypothesis.proposal_word_count",
        minimum=1,
        maximum=_MAX_COORDINATES,
    )
    decision_word_count = _exact_integer(
        values["decision_word_count"],
        name="factorization_hypothesis.decision_word_count",
        minimum=1,
        maximum=_MAX_COORDINATES,
    )
    for name in (
        "full_coordinate_sha256",
        "proposal_coordinate_sha256",
        "decision_coordinate_sha256",
        "hypothesis_sha256",
    ):
        _require_sha256(values[name], name="factorization_hypothesis." + name)
    if attempt_budget != cp36_hypothesis.attempt_budget:
        raise ValueError("factorization hypothesis attempt budget differs from CP36")
    if decision_word_count != attempt_budget:
        raise ValueError("factorization hypothesis decision count differs from CP36")
    expected_proposal_count = (
        attempt_budget * cp36_hypothesis.reference_words_per_attempt
    )
    if proposal_word_count != expected_proposal_count:
        raise ValueError("factorization hypothesis proposal count differs from CP36")
    block_counts = cp36_hypothesis.block_raw64_word_counts
    block_count = cp36_hypothesis.blocks_per_attempt
    full = _validate_coordinate_tuple(
        cp36_hypothesis.logical_word_coordinates,
        name="factorization_hypothesis.CP36.logical_word_coordinates",
        expected_length=proposal_word_count + decision_word_count,
    )
    proposal = []
    decision = []
    cursor = 0
    for attempt in range(attempt_budget):
        for block, count in enumerate(block_counts):
            segment = full[cursor : cursor + count]
            if block == block_count - 1:
                decision.extend(segment)
            else:
                proposal.extend(segment)
            cursor += count
    coordinate_expectations = (
        ("full_coordinate_sha256", _coordinate_digest(full)),
        ("proposal_coordinate_sha256", _coordinate_digest(tuple(proposal))),
        ("decision_coordinate_sha256", _coordinate_digest(tuple(decision))),
    )
    for name, expected in coordinate_expectations:
        if values[name] != expected:
            raise ValueError("factorization hypothesis %s differs from CP36" % name)
    for name in (
        "abstract_functional_noninterference_assumed",
        "existing_artifacts_motivate_but_do_not_prove_factorization",
    ):
        _exact_bool(values[name], True, name="factorization_hypothesis." + name)
    for name in (
        "executable_arbitrary_word_evaluator_equivalence_proved",
        "live_preparation_failure_independence_certified",
        "live_philox_statement",
    ):
        _exact_bool(values[name], False, name="factorization_hypothesis." + name)
    if values["hypothesis_sha256"] != _semantic_digest(_hypothesis_payload(values)):
        raise ValueError("predecision factorization hypothesis digest differs")


def _validate_factorization_hypothesis(
    hypothesis: object,
) -> InitialTiltRejectionPredecisionFactorizationHypothesis:
    """Validate and return the exact sealed factorization assumption."""

    if type(hypothesis) is not InitialTiltRejectionPredecisionFactorizationHypothesis:
        raise TypeError("hypothesis has the wrong exact factorization type")
    _validate_factorization_hypothesis_values(
        {name: getattr(hypothesis, name) for name in _factorization_hypothesis_fields()}
    )
    return hypothesis


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
    """Sealed CP40-bound abstract failure-aware source-law certificate."""

    schema_version: str
    certificate_scope: str
    source_law_policy: str
    source_law_role_sha256: str
    checkpoint40_certificate: _CP40_CERT_TYPE
    checkpoint40_certificate_sha256: str
    checkpoint40_runtime_sha256: str
    checkpoint40_owner_runtime_identity: int
    checkpoint39_certificate: _CP39_CERT_TYPE
    checkpoint39_certificate_sha256: str
    checkpoint38_certificate: _CP38_CERT_TYPE
    checkpoint38_certificate_sha256: str
    checkpoint37_certificate: _CP37_CERT_TYPE
    checkpoint37_certificate_sha256: str
    checkpoint36_certificate: _CP36_CERT_TYPE
    checkpoint36_certificate_sha256: str
    checkpoint36_word_family_hypothesis: _CP36_HYPOTHESIS_TYPE
    checkpoint36_word_family_hypothesis_sha256: str
    checkpoint38_word_law_hypothesis: _CP38_HYPOTHESIS_TYPE
    checkpoint38_word_law_hypothesis_sha256: str
    factorization_hypothesis: InitialTiltRejectionPredecisionFactorizationHypothesis
    factorization_hypothesis_sha256: str
    process_parameter_sha256: str
    attempt_budget: int
    raw_word_domain_size: int
    proposal_words_per_attempt: int
    proposal_word_count: int
    decision_word_count: int
    total_word_count: int
    common_dyadic_denominator_exponent: int
    full_coordinate_sha256: str
    proposal_coordinate_sha256: str
    decision_coordinate_sha256: str
    source_premise: str
    factorization_premise: str
    fiber_definition: str
    augmented_law_definition: str
    normalization_theorem: str
    augmented_tv_theorem: str
    selected_tv_theorem: str
    selected_tv_proof: str
    data_processing_theorem: str
    source_law_runtime_sha256: str
    exact_checkpoint40_owner_binding_certified: bool
    transitive_checkpoint38_37_36_binding_certified: bool
    exact_parent_hypothesis_identity_certified: bool
    normalized_coordinate_partition_certified: bool
    reserved_decision_coordinate_partition_certified: bool
    explicit_predecision_factorization_hypothesis_bound: bool
    functional_noninterference_proved_by_executable_evaluator: bool
    abstract_product_uniform_independence_premise_bound: bool
    distinct_failure_exhaustion_configuration_atoms_certified: bool
    exact_symbolic_fiber_definition_certified: bool
    failure_aware_augmented_law_defined: bool
    exact_augmented_normalization_certified: bool
    common_dyadic_denominator_exponent_certified: bool
    quota_gated_ideal_comparison_certified: bool
    rho_zero_augmented_tv_identity_certified: bool
    rho_positive_refined_augmented_tv_bound_certified: bool
    universal_augmented_tv_bound_certified: bool
    positive_selection_mass_conditioning_boundary_certified: bool
    factor_one_conditioning_inequality_certified: bool
    arbitrary_joint_source_data_processing_certified: bool
    no_parent_operational_call_certified: bool
    numeric_fiber_counts_materialized: bool
    numeric_failure_probability_materialized: bool
    numeric_successful_batch_distribution_materialized: bool
    numeric_global_configuration_masses_materialized: bool
    numeric_global_exhaustion_mass_materialized: bool
    numeric_global_selection_mass_materialized: bool
    arbitrary_source_product_mixture_certified: bool
    live_philox_source_law_certified: bool
    live_uniformity_certified: bool
    live_independence_certified: bool
    physical_randomness_certified: bool
    live_initializer_distribution_certified: bool
    live_exception_relabelled_as_sampled_failure: bool
    ungated_exact_ideal_rejection_certified: bool
    normalized_global_analytic_tilt_certified: bool
    all_strategy_general_initializer_certified: bool
    formal_test28_closed: bool
    tag3_payload_semantics_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("failure-aware source-law certificates cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("failure-aware source-law certificates are sealed")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("failure-aware source-law certificate is incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("failure-aware source-law certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate.__annotations__
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint40_owner_binding_certified",
    "transitive_checkpoint38_37_36_binding_certified",
    "exact_parent_hypothesis_identity_certified",
    "normalized_coordinate_partition_certified",
    "reserved_decision_coordinate_partition_certified",
    "explicit_predecision_factorization_hypothesis_bound",
    "abstract_product_uniform_independence_premise_bound",
    "distinct_failure_exhaustion_configuration_atoms_certified",
    "exact_symbolic_fiber_definition_certified",
    "failure_aware_augmented_law_defined",
    "exact_augmented_normalization_certified",
    "common_dyadic_denominator_exponent_certified",
    "quota_gated_ideal_comparison_certified",
    "rho_zero_augmented_tv_identity_certified",
    "rho_positive_refined_augmented_tv_bound_certified",
    "universal_augmented_tv_bound_certified",
    "positive_selection_mass_conditioning_boundary_certified",
    "factor_one_conditioning_inequality_certified",
    "arbitrary_joint_source_data_processing_certified",
    "no_parent_operational_call_certified",
    "passed",
)

_CERTIFICATE_NEGATIVE_FLAGS = (
    "functional_noninterference_proved_by_executable_evaluator",
    "numeric_fiber_counts_materialized",
    "numeric_failure_probability_materialized",
    "numeric_successful_batch_distribution_materialized",
    "numeric_global_configuration_masses_materialized",
    "numeric_global_exhaustion_mass_materialized",
    "numeric_global_selection_mass_materialized",
    "arbitrary_source_product_mixture_certified",
    "live_philox_source_law_certified",
    "live_uniformity_certified",
    "live_independence_certified",
    "physical_randomness_certified",
    "live_initializer_distribution_certified",
    "live_exception_relabelled_as_sampled_failure",
    "ungated_exact_ideal_rejection_certified",
    "normalized_global_analytic_tilt_certified",
    "all_strategy_general_initializer_certified",
    "formal_test28_closed",
    "tag3_payload_semantics_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
    "runtime_portable",
    "cryptographic_authentication",
)


def _bound_ancestry(
    admission_owner: object,
    *,
    require_live: bool,
) -> Tuple[object, ...]:
    if type(admission_owner) is not _CP40_OWNER_TYPE:
        raise TypeError("admission_owner has the wrong exact CP40 type")
    cp40_snapshot = _CP40_OWNER_SNAPSHOT(admission_owner)
    cp40_certificate = _CP40_CERTIFICATE_PROPERTY.__get__(
        admission_owner, _CP40_OWNER_TYPE
    )
    if require_live:
        live = _CP40_LIVE_CERTIFICATE(admission_owner, cp40_snapshot)
        _CP40_REQUIRE_OWNER_SNAPSHOT(admission_owner, cp40_snapshot)
        if live is not cp40_certificate:
            raise ValueError("CP40 live binding substituted its certificate")
    checked40 = _CP40_VALIDATE_CERTIFICATE(cp40_certificate)
    if checked40 is not cp40_certificate:
        raise ValueError("CP40 certificate validation substituted")

    cp39_owner = _CP40_PARENT_PROPERTY.__get__(admission_owner, _CP40_OWNER_TYPE)
    if type(cp39_owner) is not _CP39_OWNER_TYPE:
        raise TypeError("CP40 exposes the wrong exact CP39 owner type")
    cp39_certificate = _CP39_CERTIFICATE_PROPERTY.__get__(cp39_owner, _CP39_OWNER_TYPE)

    cp38_owner = _CP39_PARENT_PROPERTY.__get__(cp39_owner, _CP39_OWNER_TYPE)
    if type(cp38_owner) is not _CP38_OWNER_TYPE:
        raise TypeError("CP39 exposes the wrong exact CP38 owner type")
    cp38_certificate = _CP38_CERTIFICATE_PROPERTY.__get__(cp38_owner, _CP38_OWNER_TYPE)
    checked38 = _CP38_VALIDATE_CERTIFICATE(cp38_certificate)
    if checked38 is not cp38_certificate:
        raise ValueError("CP38 certificate validation substituted")

    cp37_owner = _CP38_PARENT_PROPERTY.__get__(cp38_owner, _CP38_OWNER_TYPE)
    if type(cp37_owner) is not _CP37_OWNER_TYPE:
        raise TypeError("CP38 exposes the wrong exact CP37 owner type")
    cp37_certificate = _CP37_CERTIFICATE_PROPERTY.__get__(cp37_owner, _CP37_OWNER_TYPE)
    checked37 = _CP37_VALIDATE_CERTIFICATE(cp37_certificate)
    if checked37 is not cp37_certificate:
        raise ValueError("CP37 certificate validation substituted")

    cp36_owner = _CP37_PARENT_PROPERTY.__get__(cp37_owner, _CP37_OWNER_TYPE)
    if type(cp36_owner) is not _CP36_OWNER_TYPE:
        raise TypeError("CP37 exposes the wrong exact CP36 owner type")
    cp36_certificate = _CP36_CERTIFICATE_PROPERTY.__get__(cp36_owner, _CP36_OWNER_TYPE)
    checked36 = _CP36_VALIDATE_CERTIFICATE(cp36_certificate)
    if checked36 is not cp36_certificate:
        raise ValueError("CP36 certificate validation substituted")

    if cp40_certificate.checkpoint39_certificate is not cp39_certificate:
        raise ValueError("CP40-to-CP39 certificate identity differs")
    if cp40_certificate.checkpoint38_certificate is not cp38_certificate:
        raise ValueError("CP40-to-CP38 certificate identity differs")
    if cp39_certificate.checkpoint38_certificate is not cp38_certificate:
        raise ValueError("CP39-to-CP38 certificate identity differs")
    if cp38_certificate.decision_certificate is not cp37_certificate:
        raise ValueError("CP38-to-CP37 certificate identity differs")
    if cp37_certificate.preparation_certificate is not cp36_certificate:
        raise ValueError("CP37-to-CP36 certificate identity differs")

    cp36_hypothesis = cp36_certificate.word_family_hypothesis
    if _CP36_VALIDATE_HYPOTHESIS(cp36_hypothesis) is not cp36_hypothesis:
        raise ValueError("CP36 word hypothesis validation substituted")
    owner_cp36_hypothesis = _CP36_HYPOTHESIS_PROPERTY.__get__(
        cp36_owner, _CP36_OWNER_TYPE
    )
    if owner_cp36_hypothesis is not cp36_hypothesis:
        raise ValueError("CP36 owner word-hypothesis identity differs")
    cp38_hypothesis = cp38_certificate.word_law_hypothesis
    if _CP38_VALIDATE_HYPOTHESIS(cp38_hypothesis) is not cp38_hypothesis:
        raise ValueError("CP38 word hypothesis validation substituted")
    owner_cp38_hypothesis = _CP38_HYPOTHESIS_PROPERTY.__get__(
        cp38_owner, _CP38_OWNER_TYPE
    )
    if owner_cp38_hypothesis is not cp38_hypothesis:
        raise ValueError("CP38 owner word-hypothesis identity differs")
    _CP40_REQUIRE_OWNER_SNAPSHOT(admission_owner, cp40_snapshot)
    return (
        cp40_snapshot,
        cp40_certificate,
        cp39_owner,
        cp39_certificate,
        cp38_owner,
        cp38_certificate,
        cp37_owner,
        cp37_certificate,
        cp36_owner,
        cp36_certificate,
        cp36_hypothesis,
        cp38_hypothesis,
    )


def _declare_factorization_hypothesis(
    admission_owner: object,
    *,
    hypothesis_scope: object,
    factorization_premise: object,
) -> InitialTiltRejectionPredecisionFactorizationHypothesis:
    """Declare the explicit assumption needed for the CP41 mixture theorem."""

    scope = _require_text(
        hypothesis_scope,
        _FACTORIZATION_HYPOTHESIS_SCOPE,
        name="hypothesis_scope",
    )
    premise = _require_text(
        factorization_premise,
        _FACTORIZATION,
        name="factorization_premise",
    )
    ancestry = _bound_ancestry(admission_owner, require_live=True)
    cp36_certificate = ancestry[9]
    cp36_hypothesis = ancestry[10]
    cp38_hypothesis = ancestry[11]
    full, proposal, decision = _partition_coordinates(cp36_certificate)
    values: Dict[str, object] = {
        "schema_version": _FACTORIZATION_HYPOTHESIS_SCHEMA,
        "hypothesis_scope": scope,
        "factorization_premise": premise,
        "checkpoint36_word_family_hypothesis": cp36_hypothesis,
        "checkpoint36_word_family_hypothesis_sha256": (
            cp36_hypothesis.hypothesis_sha256
        ),
        "checkpoint38_word_law_hypothesis": cp38_hypothesis,
        "checkpoint38_word_law_hypothesis_sha256": (cp38_hypothesis.hypothesis_sha256),
        "attempt_budget": cp36_certificate.attempt_budget,
        "proposal_word_count": len(proposal),
        "decision_word_count": len(decision),
        "full_coordinate_sha256": _coordinate_digest(full),
        "proposal_coordinate_sha256": _coordinate_digest(proposal),
        "decision_coordinate_sha256": _coordinate_digest(decision),
        "abstract_functional_noninterference_assumed": True,
        "existing_artifacts_motivate_but_do_not_prove_factorization": True,
        "executable_arbitrary_word_evaluator_equivalence_proved": False,
        "live_preparation_failure_independence_certified": False,
        "live_philox_statement": False,
        "hypothesis_sha256": _ZERO_SHA256,
    }
    values["hypothesis_sha256"] = _semantic_digest(_hypothesis_payload(values))
    return InitialTiltRejectionPredecisionFactorizationHypothesis(
        _construction_token=_HYPOTHESIS_TOKEN,
        **values,
    )


def _runtime_sha256() -> str:
    _require_dependency_surfaces()
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "premise": _PREMISE,
            "factorization": _FACTORIZATION,
            "fibers": _FIBERS,
            "law": _LAW,
            "normalization": _NORMALIZATION,
            "augmented_tv": _AUGMENTED_TV,
            "selected_tv": _SELECTED_TV,
            "selected_proof": _SELECTED_PROOF,
            "data_processing": _DATA_PROCESSING,
            "atoms": _ATOMS,
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "constants": (("D", _D), ("maximum_coordinates", _MAX_COORDINATES)),
        }
    )


def _validate_parent_support_flags(
    cp40: _CP40_CERT_TYPE,
    cp38: _CP38_CERT_TYPE,
    cp37: _CP37_CERT_TYPE,
    cp36: _CP36_CERT_TYPE,
) -> None:
    required = (
        (cp36, "reserved_decision_word_uninterpreted_certified"),
        (cp36, "logical_word_coordinates_normalized_template_certified"),
        (cp36, "failure_augmented_total_operational_pushforward_defined"),
        (cp37, "all_thresholds_before_decisions_certified"),
        (cp37, "conditional_abstract_iid_decision_law_certified"),
        (cp37, "no_new_words_or_caller_rng_certified"),
        (cp38, "direct_word_free_conditioning_projection_certified"),
        (cp38, "complete_fixed_batch_mass_partition_certified"),
        (cp38, "fixed_batch_abstract_iid_outcome_law_certified"),
        (
            cp40,
            "abstract_words_iid_uniform_and_independent_of_word_free_batch_certified",
        ),
        (cp40, "fixed_batch_augmented_target_certified"),
    )
    for record, name in required:
        if getattr(record, name, None) is not True:
            raise ValueError("required parent support flag %s is absent" % name)


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        ("schema_version", _SCHEMA_VERSION),
        ("certificate_scope", _SCOPE),
        ("source_law_policy", _POLICY),
        ("source_premise", _PREMISE),
        ("factorization_premise", _FACTORIZATION),
        ("fiber_definition", _FIBERS),
        ("augmented_law_definition", _LAW),
        ("normalization_theorem", _NORMALIZATION),
        ("augmented_tv_theorem", _AUGMENTED_TV),
        ("selected_tv_theorem", _SELECTED_TV),
        ("selected_tv_proof", _SELECTED_PROOF),
        ("data_processing_theorem", _DATA_PROCESSING),
    ):
        _require_text(values[name], expected, name="certificate." + name)
    _require_sha256(
        values["source_law_role_sha256"],
        name="certificate.source_law_role_sha256",
    )
    for name in (
        "checkpoint40_certificate_sha256",
        "checkpoint40_runtime_sha256",
        "checkpoint39_certificate_sha256",
        "checkpoint38_certificate_sha256",
        "checkpoint37_certificate_sha256",
        "checkpoint36_certificate_sha256",
        "checkpoint36_word_family_hypothesis_sha256",
        "checkpoint38_word_law_hypothesis_sha256",
        "factorization_hypothesis_sha256",
        "process_parameter_sha256",
        "full_coordinate_sha256",
        "proposal_coordinate_sha256",
        "decision_coordinate_sha256",
        "source_law_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate." + name)
    for name in (
        "checkpoint40_owner_runtime_identity",
        "attempt_budget",
        "raw_word_domain_size",
        "proposal_words_per_attempt",
        "proposal_word_count",
        "decision_word_count",
        "total_word_count",
        "common_dyadic_denominator_exponent",
    ):
        _exact_integer(values[name], name="certificate." + name, minimum=1)

    cp40 = values["checkpoint40_certificate"]
    if type(cp40) is not _CP40_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP40 parent type")
    if _CP40_VALIDATE_CERTIFICATE(cp40) is not cp40:
        raise ValueError("CP40 certificate validation substituted")
    cp39 = values["checkpoint39_certificate"]
    cp38 = values["checkpoint38_certificate"]
    cp37 = values["checkpoint37_certificate"]
    cp36 = values["checkpoint36_certificate"]
    if type(cp39) is not _CP39_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP39 parent type")
    if type(cp38) is not _CP38_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP38 parent type")
    if type(cp37) is not _CP37_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP37 parent type")
    if type(cp36) is not _CP36_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP36 parent type")
    if _CP38_VALIDATE_CERTIFICATE(cp38) is not cp38:
        raise ValueError("CP38 certificate validation substituted")
    if _CP37_VALIDATE_CERTIFICATE(cp37) is not cp37:
        raise ValueError("CP37 certificate validation substituted")
    if _CP36_VALIDATE_CERTIFICATE(cp36) is not cp36:
        raise ValueError("CP36 certificate validation substituted")
    if cp40.checkpoint39_certificate is not cp39:
        raise ValueError("certificate CP40-to-CP39 identity differs")
    if cp40.checkpoint38_certificate is not cp38:
        raise ValueError("certificate CP40-to-CP38 identity differs")
    if cp39.checkpoint38_certificate is not cp38:
        raise ValueError("certificate CP39-to-CP38 identity differs")
    if cp38.decision_certificate is not cp37:
        raise ValueError("certificate CP38-to-CP37 identity differs")
    if cp37.preparation_certificate is not cp36:
        raise ValueError("certificate CP37-to-CP36 identity differs")

    cp36_hypothesis = values["checkpoint36_word_family_hypothesis"]
    cp38_hypothesis = values["checkpoint38_word_law_hypothesis"]
    if cp36.word_family_hypothesis is not cp36_hypothesis:
        raise ValueError("certificate CP36 hypothesis identity differs")
    if cp38.word_law_hypothesis is not cp38_hypothesis:
        raise ValueError("certificate CP38 hypothesis identity differs")
    if _CP36_VALIDATE_HYPOTHESIS(cp36_hypothesis) is not cp36_hypothesis:
        raise ValueError("certificate CP36 hypothesis validation substituted")
    if _CP38_VALIDATE_HYPOTHESIS(cp38_hypothesis) is not cp38_hypothesis:
        raise ValueError("certificate CP38 hypothesis validation substituted")
    factorization = values["factorization_hypothesis"]
    checked_factorization = _validate_factorization_hypothesis(factorization)
    if checked_factorization is not factorization:
        raise ValueError("factorization hypothesis validation substituted")
    if factorization.checkpoint36_word_family_hypothesis is not cp36_hypothesis:
        raise ValueError("factorization hypothesis CP36 identity differs")
    if factorization.checkpoint38_word_law_hypothesis is not cp38_hypothesis:
        raise ValueError("factorization hypothesis CP38 identity differs")

    digest_expectations = (
        ("checkpoint40_certificate_sha256", cp40.certificate_sha256),
        ("checkpoint39_certificate_sha256", cp39.certificate_sha256),
        ("checkpoint38_certificate_sha256", cp38.certificate_sha256),
        ("checkpoint37_certificate_sha256", cp37.certificate_sha256),
        ("checkpoint36_certificate_sha256", cp36.certificate_sha256),
        (
            "checkpoint36_word_family_hypothesis_sha256",
            cp36_hypothesis.hypothesis_sha256,
        ),
        (
            "checkpoint38_word_law_hypothesis_sha256",
            cp38_hypothesis.hypothesis_sha256,
        ),
        ("factorization_hypothesis_sha256", factorization.hypothesis_sha256),
    )
    for name, expected in digest_expectations:
        if values[name] != expected:
            raise ValueError("certificate %s differs" % name)
    if (
        values["process_parameter_sha256"]
        != cp40.checkpoint38_certificate.process_parameter_sha256
    ):
        raise ValueError("certificate process digest differs")
    if values["checkpoint40_runtime_sha256"] != cp40.admission_runtime_sha256:
        raise ValueError("certificate CP40 runtime digest differs")

    full, proposal, decision = _partition_coordinates(cp36)
    expected_scalars = {
        "attempt_budget": cp36.attempt_budget,
        "raw_word_domain_size": _D,
        "proposal_words_per_attempt": cp36.reference_words_per_attempt,
        "proposal_word_count": len(proposal),
        "decision_word_count": len(decision),
        "total_word_count": len(full),
        "common_dyadic_denominator_exponent": len(proposal) + len(decision),
        "full_coordinate_sha256": _coordinate_digest(full),
        "proposal_coordinate_sha256": _coordinate_digest(proposal),
        "decision_coordinate_sha256": _coordinate_digest(decision),
        "source_law_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_scalars.items():
        if type(values[name]) is not type(expected) or values[name] != expected:
            raise ValueError("certificate.%s differs" % name)
    if factorization.attempt_budget != cp36.attempt_budget:
        raise ValueError("factorization hypothesis attempt budget differs")
    if factorization.proposal_word_count != len(proposal):
        raise ValueError("factorization hypothesis proposal count differs")
    if factorization.decision_word_count != len(decision):
        raise ValueError("factorization hypothesis decision count differs")
    for name in (
        "full_coordinate_sha256",
        "proposal_coordinate_sha256",
        "decision_coordinate_sha256",
    ):
        if getattr(factorization, name) != expected_scalars[name]:
            raise ValueError("factorization hypothesis coordinate digest differs")
    _validate_parent_support_flags(cp40, cp38, cp37, cp36)
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("failure-aware source-law certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate
    ):
        raise TypeError("certificate has the wrong exact CP41 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    admission_owner: _CP40_OWNER_TYPE,
    factorization_hypothesis: InitialTiltRejectionPredecisionFactorizationHypothesis,
    source_law_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
    ancestry = _bound_ancestry(admission_owner, require_live=True)
    cp40, cp39, cp38, cp37, cp36 = (
        ancestry[1],
        ancestry[3],
        ancestry[5],
        ancestry[7],
        ancestry[9],
    )
    cp36_hypothesis, cp38_hypothesis = ancestry[10], ancestry[11]
    checked_factorization = _validate_factorization_hypothesis(factorization_hypothesis)
    if checked_factorization.checkpoint36_word_family_hypothesis is not cp36_hypothesis:
        raise ValueError("factorization hypothesis does not bind the CP36 premise")
    if checked_factorization.checkpoint38_word_law_hypothesis is not cp38_hypothesis:
        raise ValueError("factorization hypothesis does not bind the CP38 premise")
    role = _require_sha256(source_law_role_sha256, name="source_law_role_sha256")
    full, proposal, decision = _partition_coordinates(cp36)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "source_law_policy": _POLICY,
        "source_law_role_sha256": role,
        "checkpoint40_certificate": cp40,
        "checkpoint40_certificate_sha256": cp40.certificate_sha256,
        "checkpoint40_runtime_sha256": cp40.admission_runtime_sha256,
        "checkpoint40_owner_runtime_identity": id(admission_owner),
        "checkpoint39_certificate": cp39,
        "checkpoint39_certificate_sha256": cp39.certificate_sha256,
        "checkpoint38_certificate": cp38,
        "checkpoint38_certificate_sha256": cp38.certificate_sha256,
        "checkpoint37_certificate": cp37,
        "checkpoint37_certificate_sha256": cp37.certificate_sha256,
        "checkpoint36_certificate": cp36,
        "checkpoint36_certificate_sha256": cp36.certificate_sha256,
        "checkpoint36_word_family_hypothesis": cp36_hypothesis,
        "checkpoint36_word_family_hypothesis_sha256": (
            cp36_hypothesis.hypothesis_sha256
        ),
        "checkpoint38_word_law_hypothesis": cp38_hypothesis,
        "checkpoint38_word_law_hypothesis_sha256": (cp38_hypothesis.hypothesis_sha256),
        "factorization_hypothesis": checked_factorization,
        "factorization_hypothesis_sha256": checked_factorization.hypothesis_sha256,
        "process_parameter_sha256": cp38.process_parameter_sha256,
        "attempt_budget": cp36.attempt_budget,
        "raw_word_domain_size": _D,
        "proposal_words_per_attempt": cp36.reference_words_per_attempt,
        "proposal_word_count": len(proposal),
        "decision_word_count": len(decision),
        "total_word_count": len(full),
        "common_dyadic_denominator_exponent": len(proposal) + len(decision),
        "full_coordinate_sha256": _coordinate_digest(full),
        "proposal_coordinate_sha256": _coordinate_digest(proposal),
        "decision_coordinate_sha256": _coordinate_digest(decision),
        "source_premise": _PREMISE,
        "factorization_premise": _FACTORIZATION,
        "fiber_definition": _FIBERS,
        "augmented_law_definition": _LAW,
        "normalization_theorem": _NORMALIZATION,
        "augmented_tv_theorem": _AUGMENTED_TV,
        "selected_tv_theorem": _SELECTED_TV,
        "selected_tv_proof": _SELECTED_PROOF,
        "data_processing_theorem": _DATA_PROCESSING,
        "source_law_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _specification_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    excluded = {
        "certificate",
        "full_logical_word_coordinates",
        "proposal_word_coordinates",
        "decision_word_coordinates",
        "specification_sha256",
    }
    return {name: values[name] for name in values if name not in excluded}


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification:
    """One non-enumerating symbolic source-kernel specification."""

    certificate: CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate
    certificate_sha256: str
    source_atoms: Tuple[str, ...]
    full_logical_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    proposal_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    decision_word_coordinates: Tuple[
        Tuple[Tuple[int, int], Tuple[int, int, int, int], int], ...
    ]
    full_coordinate_sha256: str
    proposal_coordinate_sha256: str
    decision_coordinate_sha256: str
    attempt_budget: int
    raw_word_domain_size: int
    proposal_word_count: int
    decision_word_count: int
    total_word_count: int
    common_dyadic_denominator_base: int
    common_dyadic_denominator_exponent: int
    common_dyadic_denominator_integer_materialized: bool
    source_premise: str
    factorization_premise: str
    fiber_definition: str
    augmented_law_definition: str
    normalization_theorem: str
    augmented_tv_theorem: str
    selected_tv_theorem: str
    selected_tv_proof: str
    data_processing_theorem: str
    preparation_failure_fiber_count: Optional[object]
    quota_failure_fiber_count: Optional[object]
    successful_batch_fiber_counts: Optional[object]
    preparation_failure_probability: Optional[object]
    quota_failure_probability: Optional[object]
    successful_source_mass_rho: Optional[object]
    successful_batch_distribution: Optional[object]
    global_configuration_masses: Optional[object]
    global_exhaustion_mass: Optional[object]
    global_dyadic_selection_mass: Optional[object]
    global_ideal_selection_mass: Optional[object]
    selected_conditioned_numeric_bound: Optional[object]
    universal_augmented_tv_strict_upper_numerator: int
    universal_augmented_tv_strict_upper_denominator: int
    universal_augmented_tv_upper_is_strict: bool
    symbolic_fiber_law_defined: bool
    exact_symbolic_normalization_defined: bool
    factorization_is_explicit_assumption: bool
    factorization_executable_proof_absent: bool
    rho_zero_branch_explicit: bool
    rho_positive_refined_bound_symbolic: bool
    selected_conditioned_boundary_requires_positive_S_Q: bool
    selected_conditioned_factor_one_bound_symbolic: bool
    arbitrary_source_data_processing_only: bool
    empty_configuration_is_configuration_atom: bool
    failure_atoms_distinct_from_exhaustion: bool
    duplicate_configurations_aggregate_within_and_across_batches: bool
    numeric_fibers_or_masses_materialized: bool
    live_source_or_initializer_law: bool
    ungated_ideal_rejection_law: bool
    formal_test28_closed: bool
    specification_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("source-law symbolic specifications cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SPECIFICATION_TOKEN:
            raise TypeError("source-law symbolic specifications are sealed")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("source-law symbolic specification is incomplete")
        _validate_specification_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("source-law symbolic specifications are not pickleable")


def _specification_fields() -> Tuple[str, ...]:
    specification_type = (
        CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification
    )
    return tuple(specification_type.__annotations__)


_SPECIFICATION_POSITIVE_FLAGS = (
    "universal_augmented_tv_upper_is_strict",
    "symbolic_fiber_law_defined",
    "exact_symbolic_normalization_defined",
    "factorization_is_explicit_assumption",
    "factorization_executable_proof_absent",
    "rho_zero_branch_explicit",
    "rho_positive_refined_bound_symbolic",
    "selected_conditioned_boundary_requires_positive_S_Q",
    "selected_conditioned_factor_one_bound_symbolic",
    "arbitrary_source_data_processing_only",
    "empty_configuration_is_configuration_atom",
    "failure_atoms_distinct_from_exhaustion",
    "duplicate_configurations_aggregate_within_and_across_batches",
)

_SPECIFICATION_NEGATIVE_FLAGS = (
    "common_dyadic_denominator_integer_materialized",
    "numeric_fibers_or_masses_materialized",
    "live_source_or_initializer_law",
    "ungated_ideal_rejection_law",
    "formal_test28_closed",
)

_SPECIFICATION_ABSENT_FIELDS = (
    "preparation_failure_fiber_count",
    "quota_failure_fiber_count",
    "successful_batch_fiber_counts",
    "preparation_failure_probability",
    "quota_failure_probability",
    "successful_source_mass_rho",
    "successful_batch_distribution",
    "global_configuration_masses",
    "global_exhaustion_mass",
    "global_dyadic_selection_mass",
    "global_ideal_selection_mass",
    "selected_conditioned_numeric_bound",
)


def _validate_specification_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate
    ] = None,
) -> None:
    certificate = values["certificate"]
    if trusted_certificate is None:
        checked_certificate = _validate_certificate(certificate)
    else:
        if certificate is not trusted_certificate:
            raise ValueError("symbolic specification certificate identity differs")
        checked_certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="specification.certificate_sha256",
    )
    if values["certificate_sha256"] != checked_certificate.certificate_sha256:
        raise ValueError("symbolic specification certificate digest differs")
    atoms = values["source_atoms"]
    if type(atoms) is not tuple or len(atoms) != len(_ATOMS):
        raise ValueError("symbolic specification atom family differs")
    for position, (actual, expected) in enumerate(zip(atoms, _ATOMS)):
        _require_text(
            actual,
            expected,
            name="specification.source_atoms[%d]" % position,
        )

    cp36 = checked_certificate.checkpoint36_certificate
    full_expected, proposal_expected, decision_expected = _partition_coordinates(cp36)
    full = _validate_coordinate_tuple(
        values["full_logical_word_coordinates"],
        name="specification.full_logical_word_coordinates",
        expected_length=len(full_expected),
    )
    proposal = _validate_coordinate_tuple(
        values["proposal_word_coordinates"],
        name="specification.proposal_word_coordinates",
        expected_length=len(proposal_expected),
    )
    decision = _validate_coordinate_tuple(
        values["decision_word_coordinates"],
        name="specification.decision_word_coordinates",
        expected_length=len(decision_expected),
    )
    if (
        full != full_expected
        or proposal != proposal_expected
        or decision != decision_expected
    ):
        raise ValueError("symbolic specification coordinate partition differs")
    for name, coordinates, expected_digest in (
        ("full_coordinate_sha256", full, checked_certificate.full_coordinate_sha256),
        (
            "proposal_coordinate_sha256",
            proposal,
            checked_certificate.proposal_coordinate_sha256,
        ),
        (
            "decision_coordinate_sha256",
            decision,
            checked_certificate.decision_coordinate_sha256,
        ),
    ):
        digest = _require_sha256(values[name], name="specification." + name)
        if digest != expected_digest or digest != _coordinate_digest(coordinates):
            raise ValueError("symbolic specification %s differs" % name)
    expected_scalars = {
        "attempt_budget": checked_certificate.attempt_budget,
        "raw_word_domain_size": _D,
        "proposal_word_count": len(proposal),
        "decision_word_count": len(decision),
        "total_word_count": len(full),
        "common_dyadic_denominator_base": _D,
        "common_dyadic_denominator_exponent": len(proposal) + len(decision),
        "universal_augmented_tv_strict_upper_numerator": (
            checked_certificate.attempt_budget
        ),
        "universal_augmented_tv_strict_upper_denominator": _D,
    }
    for name, expected in expected_scalars.items():
        actual = _exact_integer(values[name], name="specification." + name, minimum=1)
        if actual != expected:
            raise ValueError("symbolic specification.%s differs" % name)
    for name, expected in (
        ("source_premise", _PREMISE),
        ("factorization_premise", _FACTORIZATION),
        ("fiber_definition", _FIBERS),
        ("augmented_law_definition", _LAW),
        ("normalization_theorem", _NORMALIZATION),
        ("augmented_tv_theorem", _AUGMENTED_TV),
        ("selected_tv_theorem", _SELECTED_TV),
        ("selected_tv_proof", _SELECTED_PROOF),
        ("data_processing_theorem", _DATA_PROCESSING),
    ):
        _require_text(values[name], expected, name="specification." + name)
    for name in _SPECIFICATION_ABSENT_FIELDS:
        if values[name] is not None:
            raise ValueError("symbolic specification.%s must be absent" % name)
    for name in _SPECIFICATION_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="specification." + name)
    for name in _SPECIFICATION_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="specification." + name)
    _require_sha256(
        values["specification_sha256"],
        name="specification.specification_sha256",
    )
    if values["specification_sha256"] != _semantic_digest(
        _specification_payload(values)
    ):
        raise ValueError("source-law symbolic specification digest differs")


def _validate_specification(
    specification: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification:
    specification_type = (
        CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification
    )
    if type(specification) is not specification_type:
        raise TypeError("specification has the wrong exact CP41 type")
    _validate_specification_values(
        {name: getattr(specification, name) for name in _specification_fields()},
        trusted_certificate=trusted_certificate,
    )
    return specification


def _make_specification(
    certificate: CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification:
    checked = _validate_certificate(certificate)
    full, proposal, decision = _partition_coordinates(checked.checkpoint36_certificate)
    values: Dict[str, object] = {
        "certificate": checked,
        "certificate_sha256": checked.certificate_sha256,
        "source_atoms": _ATOMS,
        "full_logical_word_coordinates": full,
        "proposal_word_coordinates": proposal,
        "decision_word_coordinates": decision,
        "full_coordinate_sha256": _coordinate_digest(full),
        "proposal_coordinate_sha256": _coordinate_digest(proposal),
        "decision_coordinate_sha256": _coordinate_digest(decision),
        "attempt_budget": checked.attempt_budget,
        "raw_word_domain_size": _D,
        "proposal_word_count": len(proposal),
        "decision_word_count": len(decision),
        "total_word_count": len(full),
        "common_dyadic_denominator_base": _D,
        "common_dyadic_denominator_exponent": len(proposal) + len(decision),
        "source_premise": _PREMISE,
        "factorization_premise": _FACTORIZATION,
        "fiber_definition": _FIBERS,
        "augmented_law_definition": _LAW,
        "normalization_theorem": _NORMALIZATION,
        "augmented_tv_theorem": _AUGMENTED_TV,
        "selected_tv_theorem": _SELECTED_TV,
        "selected_tv_proof": _SELECTED_PROOF,
        "data_processing_theorem": _DATA_PROCESSING,
        **{name: None for name in _SPECIFICATION_ABSENT_FIELDS},
        "universal_augmented_tv_strict_upper_numerator": checked.attempt_budget,
        "universal_augmented_tv_strict_upper_denominator": _D,
        **{name: True for name in _SPECIFICATION_POSITIVE_FLAGS},
        **{name: False for name in _SPECIFICATION_NEGATIVE_FLAGS},
        "specification_sha256": _ZERO_SHA256,
    }
    values["specification_sha256"] = _semantic_digest(_specification_payload(values))
    return CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification(
        _construction_token=_SPECIFICATION_TOKEN,
        **values,
    )


class CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
    """Immutable owner of one descriptive CP41 source-kernel operation."""

    __slots__ = (
        "_admission_owner",
        "_admission_owner_identity",
        "_coordination_owner",
        "_coordination_owner_identity",
        "_finite_batch_law_owner",
        "_finite_batch_law_owner_identity",
        "_decision_owner",
        "_decision_owner_identity",
        "_preparation_owner",
        "_preparation_owner_identity",
        "_factorization_hypothesis",
        "_factorization_hypothesis_identity",
        "_source_law_policy",
        "_source_law_policy_identity",
        "_source_law_role_sha256",
        "_source_law_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_specification",
        "_specification_identity",
        "_certificate_validator",
        "_certificate_builder",
        "_specification_validator",
        "_specification_builder",
        "_ancestry_resolver",
        "_surface_guard",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("failure-aware source-law owners cannot subclass")

    def __init__(
        self,
        admission_owner: _CP40_OWNER_TYPE,
        factorization_hypothesis: (
            InitialTiltRejectionPredecisionFactorizationHypothesis
        ),
        source_law_policy: str,
        source_law_role_sha256: str,
        certificate: (CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate),
        specification: (
            CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification
        ),
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("failure-aware source-law owners require certification")
        policy = _require_text(
            source_law_policy,
            _POLICY,
            name="source_law_policy",
        )
        role = _require_sha256(
            source_law_role_sha256,
            name="source_law_role_sha256",
        )
        ancestry = _bound_ancestry(admission_owner, require_live=False)
        checked_hypothesis = _validate_factorization_hypothesis(
            factorization_hypothesis
        )
        checked_certificate = _validate_certificate(certificate)
        checked_specification = _validate_specification(
            specification,
            trusted_certificate=checked_certificate,
        )
        if checked_certificate.checkpoint40_certificate is not ancestry[1]:
            raise ValueError("owner CP40 certificate identity differs")
        if checked_certificate.factorization_hypothesis is not checked_hypothesis:
            raise ValueError("owner factorization hypothesis identity differs")
        if checked_certificate.checkpoint40_owner_runtime_identity != id(
            admission_owner
        ):
            raise ValueError("owner CP40 runtime identity differs")
        bindings = (
            ("_admission_owner", admission_owner),
            ("_admission_owner_identity", admission_owner),
            ("_coordination_owner", ancestry[2]),
            ("_coordination_owner_identity", ancestry[2]),
            ("_finite_batch_law_owner", ancestry[4]),
            ("_finite_batch_law_owner_identity", ancestry[4]),
            ("_decision_owner", ancestry[6]),
            ("_decision_owner_identity", ancestry[6]),
            ("_preparation_owner", ancestry[8]),
            ("_preparation_owner_identity", ancestry[8]),
            ("_factorization_hypothesis", checked_hypothesis),
            ("_factorization_hypothesis_identity", checked_hypothesis),
            ("_source_law_policy", policy),
            ("_source_law_policy_identity", policy),
            ("_source_law_role_sha256", role),
            ("_source_law_role_sha256_identity", role),
            ("_certificate", checked_certificate),
            ("_certificate_identity", checked_certificate),
            ("_specification", checked_specification),
            ("_specification_identity", checked_specification),
            ("_certificate_validator", _validate_certificate),
            ("_certificate_builder", _make_certificate),
            ("_specification_validator", _validate_specification),
            ("_specification_builder", _make_specification),
            ("_ancestry_resolver", _bound_ancestry),
            ("_surface_guard", _require_surfaces),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("failure-aware source-law owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("failure-aware source-law owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("failure-aware source-law owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
        return self._certificate

    @property
    def admission_owner(self) -> _CP40_OWNER_TYPE:
        return self._admission_owner

    @property
    def factorization_hypothesis(
        self,
    ) -> InitialTiltRejectionPredecisionFactorizationHypothesis:
        return self._factorization_hypothesis

    def _identity_state(self) -> Tuple[object, ...]:
        if self._surface_guard is not _require_surfaces:
            raise ValueError("failure-aware source-law surface guard changed")
        self._surface_guard()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("failure-aware source-law owner seal differs")
        current = (
            self._admission_owner,
            self._coordination_owner,
            self._finite_batch_law_owner,
            self._decision_owner,
            self._preparation_owner,
            self._factorization_hypothesis,
            self._source_law_policy,
            self._source_law_role_sha256,
            self._certificate,
            self._specification,
        )
        frozen = (
            self._admission_owner_identity,
            self._coordination_owner_identity,
            self._finite_batch_law_owner_identity,
            self._decision_owner_identity,
            self._preparation_owner_identity,
            self._factorization_hypothesis_identity,
            self._source_law_policy_identity,
            self._source_law_role_sha256_identity,
            self._certificate_identity,
            self._specification_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("failure-aware source-law owner identity changed")
        callbacks = (
            (self._certificate_validator, _validate_certificate),
            (self._certificate_builder, _make_certificate),
            (self._specification_validator, _validate_specification),
            (self._specification_builder, _make_specification),
            (self._ancestry_resolver, _bound_ancestry),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("failure-aware source-law cached callback changed")
        return current

    def _owner_snapshot(self) -> Tuple[object, ...]:
        return self._identity_state()

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 10:
            raise TypeError("failure-aware source-law owner snapshot is malformed")
        current = self._identity_state()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            error_type = (
                PluginBridgeCounterKeyedInitialTiltRejectionFailureAwareSourceLawError
            )
            raise error_type("failure-aware source-law owner changed during operation")

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
        self._require_owner_snapshot(owner_snapshot)
        ancestry = self._ancestry_resolver(
            self._admission_owner,
            require_live=False,
        )
        expected_owners = (
            self._coordination_owner,
            self._finite_batch_law_owner,
            self._decision_owner,
            self._preparation_owner,
        )
        actual_owners = (ancestry[2], ancestry[4], ancestry[6], ancestry[8])
        if any(
            live is not expected
            for live, expected in zip(actual_owners, expected_owners)
        ):
            raise ValueError("failure-aware source-law transitive owner changed")
        checked = self._certificate_validator(self._certificate)
        expected_certificates = (
            ancestry[1],
            ancestry[3],
            ancestry[5],
            ancestry[7],
            ancestry[9],
        )
        actual_certificates = (
            checked.checkpoint40_certificate,
            checked.checkpoint39_certificate,
            checked.checkpoint38_certificate,
            checked.checkpoint37_certificate,
            checked.checkpoint36_certificate,
        )
        if any(
            actual is not expected
            for actual, expected in zip(actual_certificates, expected_certificates)
        ):
            raise ValueError("failure-aware source-law certificate ancestry changed")
        if checked.factorization_hypothesis is not self._factorization_hypothesis:
            raise ValueError("failure-aware source-law factorization premise changed")
        if checked.checkpoint40_owner_runtime_identity != id(self._admission_owner):
            raise ValueError("failure-aware source-law CP40 owner identity differs")
        if checked.source_law_role_sha256 != self._source_law_role_sha256:
            raise ValueError("failure-aware source-law role differs")
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def describe(
        self,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification:
        """Return the cached symbolic definition without any parent operation."""

        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        checked = self._specification_validator(
            self._specification,
            trusted_certificate=certificate,
        )
        if checked is not self._specification:
            raise ValueError("CP41 specification validation substituted")
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def validate_specification(
        self,
        specification: object,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification:
        """Validate a stored specification without drawing or enumerating."""

        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        checked = self._specification_validator(
            specification,
            trusted_certificate=certificate,
        )
        expected = self._specification_builder(certificate)
        for field in _specification_fields():
            actual = getattr(checked, field)
            target = getattr(expected, field)
            if field == "certificate":
                if actual is not target:
                    raise ValueError("CP41 specification certificate differs")
            elif type(actual) is not type(target) or actual != target:
                raise ValueError("CP41 specification.%s differs" % field)
        self._require_owner_snapshot(owner_snapshot)
        return checked


def _certify_source_law(
    admission_owner: object,
    factorization_hypothesis: object,
    *,
    source_law_policy: object,
    source_law_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
    policy = _require_text(
        source_law_policy,
        _POLICY,
        name="source_law_policy",
    )
    role = _require_sha256(
        source_law_role_sha256,
        name="source_law_role_sha256",
    )
    checked_hypothesis = _validate_factorization_hypothesis(factorization_hypothesis)
    certificate = _make_certificate(admission_owner, checked_hypothesis, role)
    specification = _make_specification(certificate)
    return CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner(
        admission_owner,
        checked_hypothesis,
        policy,
        role,
        certificate,
        specification,
        _construction_token=_OWNER_TOKEN,
    )


def _require_matching_source_law(
    admission_owner: object,
    factorization_hypothesis: object,
    owner: object,
    *,
    source_law_policy: object,
    source_law_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
    _require_text(source_law_policy, _POLICY, name="source_law_policy")
    role = _require_sha256(
        source_law_role_sha256,
        name="source_law_role_sha256",
    )
    if type(admission_owner) is not _CP40_OWNER_TYPE:
        raise TypeError("admission_owner has the wrong exact CP40 type")
    hypothesis = _validate_factorization_hypothesis(factorization_hypothesis)
    if type(owner) is not CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
        raise TypeError("owner has the wrong exact CP41 type")
    snapshot = owner._owner_snapshot()
    if owner.admission_owner is not admission_owner:
        raise ValueError("owner belongs to another CP40 parent")
    if owner.factorization_hypothesis is not hypothesis:
        raise ValueError("owner belongs to another factorization premise")
    if owner._source_law_policy != _POLICY or owner._source_law_role_sha256 != role:
        raise ValueError("owner policy or role differs")
    owner._live_certificate(snapshot)
    owner._require_owner_snapshot(snapshot)
    return owner


_FROZEN_DEPENDENCY_SURFACES = (
    ("_admission", _admission),
    ("_coord", _coord),
    ("_law", _law),
    ("_decision", _decision),
    ("_prep", _prep),
    ("_CP40_OWNER_TYPE", _CP40_OWNER_TYPE),
    ("_CP40_CERT_TYPE", _CP40_CERT_TYPE),
    ("_CP40_CERTIFICATE_PROPERTY", _CP40_CERTIFICATE_PROPERTY),
    ("_CP40_PARENT_PROPERTY", _CP40_PARENT_PROPERTY),
    ("_CP40_OWNER_SNAPSHOT", _CP40_OWNER_SNAPSHOT),
    ("_CP40_REQUIRE_OWNER_SNAPSHOT", _CP40_REQUIRE_OWNER_SNAPSHOT),
    ("_CP40_LIVE_CERTIFICATE", _CP40_LIVE_CERTIFICATE),
    ("_CP40_VALIDATE_CERTIFICATE", _CP40_VALIDATE_CERTIFICATE),
    ("_CP40_SURFACE_GUARD", _CP40_SURFACE_GUARD),
    ("_CP40_ADMIT", _CP40_ADMIT),
    ("_CP39_OWNER_TYPE", _CP39_OWNER_TYPE),
    ("_CP39_CERT_TYPE", _CP39_CERT_TYPE),
    ("_CP39_CERTIFICATE_PROPERTY", _CP39_CERTIFICATE_PROPERTY),
    ("_CP39_PARENT_PROPERTY", _CP39_PARENT_PROPERTY),
    ("_CP39_COORDINATE", _CP39_COORDINATE),
    ("_CP38_OWNER_TYPE", _CP38_OWNER_TYPE),
    ("_CP38_CERT_TYPE", _CP38_CERT_TYPE),
    ("_CP38_CERTIFICATE_PROPERTY", _CP38_CERTIFICATE_PROPERTY),
    ("_CP38_PARENT_PROPERTY", _CP38_PARENT_PROPERTY),
    ("_CP38_HYPOTHESIS_PROPERTY", _CP38_HYPOTHESIS_PROPERTY),
    ("_CP38_RESOLVE", _CP38_RESOLVE),
    ("_CP37_OWNER_TYPE", _CP37_OWNER_TYPE),
    ("_CP37_CERT_TYPE", _CP37_CERT_TYPE),
    ("_CP37_CERTIFICATE_PROPERTY", _CP37_CERTIFICATE_PROPERTY),
    ("_CP37_PARENT_PROPERTY", _CP37_PARENT_PROPERTY),
    ("_CP37_DECIDE", _CP37_DECIDE),
    ("_CP36_OWNER_TYPE", _CP36_OWNER_TYPE),
    ("_CP36_CERT_TYPE", _CP36_CERT_TYPE),
    ("_CP36_CERTIFICATE_PROPERTY", _CP36_CERTIFICATE_PROPERTY),
    ("_CP36_HYPOTHESIS_PROPERTY", _CP36_HYPOTHESIS_PROPERTY),
    ("_CP36_PREPARE", _CP36_PREPARE),
    ("_CP36_HYPOTHESIS_TYPE", _CP36_HYPOTHESIS_TYPE),
    ("_CP38_HYPOTHESIS_TYPE", _CP38_HYPOTHESIS_TYPE),
    ("_CP38_VALIDATE_CERTIFICATE", _CP38_VALIDATE_CERTIFICATE),
    ("_CP37_VALIDATE_CERTIFICATE", _CP37_VALIDATE_CERTIFICATE),
    ("_CP36_VALIDATE_CERTIFICATE", _CP36_VALIDATE_CERTIFICATE),
    ("_CP36_VALIDATE_HYPOTHESIS", _CP36_VALIDATE_HYPOTHESIS),
    ("_CP38_VALIDATE_HYPOTHESIS", _CP38_VALIDATE_HYPOTHESIS),
)


def _require_dependency_surfaces(
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_DEPENDENCY_SURFACES,
) -> None:
    if globals().get("_FROZEN_DEPENDENCY_SURFACES") is not frozen:
        raise ValueError("CP41 frozen dependency surfaces changed")
    for name, expected in frozen:
        if globals().get(name) is not expected:
            raise ValueError("CP41 dependency surface %s changed" % name)
    current = (
        (_CP40_OWNER_TYPE.certificate, _CP40_CERTIFICATE_PROPERTY),
        (_CP40_OWNER_TYPE.coordination_owner, _CP40_PARENT_PROPERTY),
        (_CP40_OWNER_TYPE._owner_snapshot, _CP40_OWNER_SNAPSHOT),
        (_CP40_OWNER_TYPE._require_owner_snapshot, _CP40_REQUIRE_OWNER_SNAPSHOT),
        (_CP40_OWNER_TYPE._live_certificate, _CP40_LIVE_CERTIFICATE),
        (_CP40_OWNER_TYPE.admit, _CP40_ADMIT),
        (_CP39_OWNER_TYPE.certificate, _CP39_CERTIFICATE_PROPERTY),
        (_CP39_OWNER_TYPE.finite_batch_law_owner, _CP39_PARENT_PROPERTY),
        (_CP39_OWNER_TYPE.coordinate, _CP39_COORDINATE),
        (_CP38_OWNER_TYPE.certificate, _CP38_CERTIFICATE_PROPERTY),
        (_CP38_OWNER_TYPE.decision_owner, _CP38_PARENT_PROPERTY),
        (_CP38_OWNER_TYPE.word_law_hypothesis, _CP38_HYPOTHESIS_PROPERTY),
        (_CP38_OWNER_TYPE.resolve, _CP38_RESOLVE),
        (_CP37_OWNER_TYPE.certificate, _CP37_CERTIFICATE_PROPERTY),
        (_CP37_OWNER_TYPE.preparation_owner, _CP37_PARENT_PROPERTY),
        (_CP37_OWNER_TYPE.decide, _CP37_DECIDE),
        (_CP36_OWNER_TYPE.certificate, _CP36_CERTIFICATE_PROPERTY),
        (_CP36_OWNER_TYPE.word_family_hypothesis, _CP36_HYPOTHESIS_PROPERTY),
        (_CP36_OWNER_TYPE.prepare, _CP36_PREPARE),
    )
    if any(live is not expected for live, expected in current):
        raise ValueError("CP41 dependency class surface changed")
    _CP40_SURFACE_GUARD()


_PUBLIC_DECLARE_NAME = (
    "declare_initial_tilt_rejection_predecision_factorization_hypothesis"
)
_PUBLIC_VALIDATE_HYPOTHESIS_NAME = (
    "validate_initial_tilt_rejection_predecision_factorization_hypothesis"
)
_PUBLIC_CERTIFY_NAME = "certify_initial_tilt_rejection_failure_aware_source_law"
_PUBLIC_MATCHING_NAME = (
    "require_matching_initial_tilt_rejection_failure_aware_source_law"
)
_PUBLIC_VALIDATE_CERTIFICATE_NAME = (
    "validate_initial_tilt_rejection_failure_aware_source_law_certificate"
)

_FROZEN_OPERATION_SURFACES = tuple(
    sorted(
        (
            (name, value)
            for name, value in globals().items()
            if not name.startswith("_")
        ),
        key=lambda item: item[0],
    )
)
_FROZEN_PRIVATE_NAMESPACE = tuple(
    sorted(
        (
            (name, value)
            for name, value in globals().items()
            if name.startswith("_") and not name.startswith("__")
        ),
        key=lambda item: item[0],
    )
)


def _bind_public_api(
    declare_impl: object,
    validate_hypothesis_impl: object,
    certify_impl: object,
    matching_impl: object,
) -> Tuple[object, object, object, object, object]:
    namespace = globals()
    late_surfaces: Tuple[Tuple[str, object], ...] = ()

    def require_late_surfaces() -> None:
        for name, expected in late_surfaces:
            if namespace.get(name) is not expected:
                raise ValueError("CP41 late operation surface %s changed" % name)
        _require_surfaces()

    def declare(
        admission_owner: object,
        *,
        hypothesis_scope: object,
        factorization_premise: object,
    ) -> InitialTiltRejectionPredecisionFactorizationHypothesis:
        """Declare the explicit assumption needed for the CP41 theorem."""

        require_late_surfaces()
        return declare_impl(
            admission_owner,
            hypothesis_scope=hypothesis_scope,
            factorization_premise=factorization_premise,
        )

    def validate_hypothesis(
        hypothesis: object,
    ) -> InitialTiltRejectionPredecisionFactorizationHypothesis:
        """Validate and return the exact sealed factorization assumption."""

        require_late_surfaces()
        return validate_hypothesis_impl(hypothesis)

    def certify(
        admission_owner: object,
        factorization_hypothesis: object,
        *,
        source_law_policy: object,
        source_law_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
        """Certify the descriptive CP41 source-kernel owner."""

        require_late_surfaces()
        return certify_impl(
            admission_owner,
            factorization_hypothesis,
            source_law_policy=source_law_policy,
            source_law_role_sha256=source_law_role_sha256,
        )

    def matching(
        admission_owner: object,
        factorization_hypothesis: object,
        owner: object,
        *,
        source_law_policy: object,
        source_law_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner:
        """Return the exact matching CP41 owner or fail closed."""

        require_late_surfaces()
        return matching_impl(
            admission_owner,
            factorization_hypothesis,
            owner,
            source_law_policy=source_law_policy,
            source_law_role_sha256=source_law_role_sha256,
        )

    def validate_certificate(
        admission_owner: object,
        factorization_hypothesis: object,
        owner: object,
        *,
        source_law_policy: object,
        source_law_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate:
        """Validate and return the exact matching CP41 certificate."""

        return matching(
            admission_owner,
            factorization_hypothesis,
            owner,
            source_law_policy=source_law_policy,
            source_law_role_sha256=source_law_role_sha256,
        ).certificate

    late_surfaces = (
        ("_declare_factorization_hypothesis", declare_impl),
        ("_validate_factorization_hypothesis", validate_hypothesis_impl),
        ("_certify_source_law", certify_impl),
        ("_require_matching_source_law", matching_impl),
        ("_require_surfaces", _require_surfaces),
        (
            "InitialTiltRejectionPredecisionFactorizationHypothesis",
            InitialTiltRejectionPredecisionFactorizationHypothesis,
        ),
        (
            "CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner",
            CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner,
        ),
        (_PUBLIC_DECLARE_NAME, declare),
        (_PUBLIC_VALIDATE_HYPOTHESIS_NAME, validate_hypothesis),
        (_PUBLIC_CERTIFY_NAME, certify),
        (_PUBLIC_MATCHING_NAME, matching),
        (_PUBLIC_VALIDATE_CERTIFICATE_NAME, validate_certificate),
    )
    return declare, validate_hypothesis, certify, matching, validate_certificate


def _require_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_OPERATION_SURFACES,
    private_namespace: Tuple[Tuple[str, object], ...] = _FROZEN_PRIVATE_NAMESPACE,
) -> None:
    namespace = globals()
    if namespace.get("_require_dependency_surfaces") is not dependency_guard:
        raise ValueError("CP41 dependency guard changed")
    if namespace.get("_FROZEN_OPERATION_SURFACES") is not frozen:
        raise ValueError("CP41 frozen operation surfaces changed")
    if namespace.get("_FROZEN_PRIVATE_NAMESPACE") is not private_namespace:
        raise ValueError("CP41 private namespace snapshot changed")
    for name, expected in frozen + private_namespace:
        if namespace.get(name) is not expected:
            raise ValueError("CP41 operation surface %s changed" % name)
    dependency_guard()


_PUBLIC_FUNCTIONS = _bind_public_api(
    _declare_factorization_hypothesis,
    _validate_factorization_hypothesis,
    _certify_source_law,
    _require_matching_source_law,
)
for _public_name, _public_function in zip(
    (
        _PUBLIC_DECLARE_NAME,
        _PUBLIC_VALIDATE_HYPOTHESIS_NAME,
        _PUBLIC_CERTIFY_NAME,
        _PUBLIC_MATCHING_NAME,
        _PUBLIC_VALIDATE_CERTIFICATE_NAME,
    ),
    _PUBLIC_FUNCTIONS,
):
    _public_function.__name__ = _public_name
    _public_function.__qualname__ = _public_name
    globals()[_public_name] = _public_function


__all__ = [
    "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_POLICY",
    "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCOPE",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_ATOMS",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_PREMISE",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE",
    "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCHEMA_VERSION",
    "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCOPE",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_FIBER_DEFINITION",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_LAW",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_NORMALIZATION_THEOREM",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_TV_THEOREM",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_PROOF",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_DATA_PROCESSING_THEOREM",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_DYADIC_DENOMINATOR",
    "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_MAX_COORDINATES",
    "InitialTiltRejectionPredecisionFactorizationHypothesis",
    "CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate",
    "CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification",
    "CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionFailureAwareSourceLawError",
    _PUBLIC_DECLARE_NAME,
    _PUBLIC_VALIDATE_HYPOTHESIS_NAME,
    _PUBLIC_CERTIFY_NAME,
    _PUBLIC_MATCHING_NAME,
    _PUBLIC_VALIDATE_CERTIFICATE_NAME,
]
