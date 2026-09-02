"""Exact synthetic-interface adapter stack for the accepted B12 roster.

This module implements the locally supportable part of the B12 adapter work:

* one exact 64-dimensional deterministic context-encoder interface;
* one source-bound synthetic conformance adapter for every row of the accepted
  22-row B06-derived B12 roster; and
* explicit, still-open interfaces for the four CSDI and four EditPP author
  extensions.

The adapter output is a qualification artifact over already-materialized exact
F105 configurations.  It is not a trained model output, an upstream-package
execution, a domain-scale runtime receipt, or evidence that an author
extension exists.  The typed :class:`AdapterReceipt` values returned here are
therefore synthetic-interface receipts only.  They cannot discharge any B12
residual predicate without separate authenticated evidence.

There is no network, filesystem, entropy, data-loader, training, inference, or
subprocess surface in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Dict, Mapping, Tuple

from heterodiff.evaluation import b12_integrated_offline_candidate as _b12
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    DOMAIN_SPECS,
    PHYSIONET_DOMAIN_ID,
    RETAIL_DOMAIN_ID,
    ExactConfiguration,
    ExactEvent,
)
from heterodiff.experiments import two_domain_baseline_registry as _b06


SCHEMA_VERSION = "heterodiff-b12-two-domain-adapter-stack-v1"
PRIMARY_CONTEXT_DIMENSION = 64
ZERO_SHA256 = "0" * 64

PHYSIONET_B06_DOMAIN_ID = "physionet-challenge-2012"
RETAIL_B06_DOMAIN_ID = "online-retail-ii"

F105_TO_B06_DOMAIN: Mapping[str, str] = {
    PHYSIONET_DOMAIN_ID: PHYSIONET_B06_DOMAIN_ID,
    RETAIL_DOMAIN_ID: RETAIL_B06_DOMAIN_ID,
}
B06_TO_F105_DOMAIN: Mapping[str, str] = {
    value: key for key, value in F105_TO_B06_DOMAIN.items()
}
_DOMAIN_DIMENSION_AND_CAP = {
    PHYSIONET_DOMAIN_ID: (112, 131072),
    RETAIL_DOMAIN_ID: (10, 1067371),
}
for _domain_id, (_dimension, _cap) in _DOMAIN_DIMENSION_AND_CAP.items():
    _spec = DOMAIN_SPECS[_domain_id]
    if (_spec.coordinate_dimension, _spec.configuration_cap) != (_dimension, _cap):
        raise RuntimeError("F105 domain dimension or cap differs from the frozen contract")


class B12AdapterStackError(ValueError):
    """Raised before an input can cross the exact adapter boundary."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(domain: str, value: Any) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be a nonempty exact string")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _exact_sha256(value: object, *, name: str, nonzero: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be an exact string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise B12AdapterStackError(f"{name} must be a lowercase SHA-256 digest")
    if nonzero and value == ZERO_SHA256:
        raise B12AdapterStackError(f"{name} must be nonzero")
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a nonnegative exact integer")
    return value


def _fraction_payload(value: Fraction) -> Tuple[str, str]:
    if type(value) is not Fraction:
        raise TypeError("an event coordinate is not an exact Fraction")
    return (str(value.numerator), str(value.denominator))


def _event_payload(event: ExactEvent, *, f105_domain_id: str) -> Dict[str, Any]:
    if type(event) is not ExactEvent:
        raise TypeError("configuration events must have exact ExactEvent type")
    if event.domain_id != f105_domain_id:
        raise B12AdapterStackError("an event crosses the frozen domain boundary")
    expected_dimension = _DOMAIN_DIMENSION_AND_CAP[f105_domain_id][0]
    if type(event.coordinates) is not tuple or len(event.coordinates) != expected_dimension:
        raise B12AdapterStackError("event coordinate dimension differs from F105")
    coordinates = tuple(_fraction_payload(value) for value in event.coordinates)
    return {
        "coordinates": coordinates,
        "f105_domain_id": f105_domain_id,
    }


def _configuration_payload(configuration: ExactConfiguration) -> Dict[str, Any]:
    if type(configuration) is not ExactConfiguration:
        raise TypeError("configuration must have exact ExactConfiguration type")
    if type(configuration.domain_id) is not str or configuration.domain_id not in F105_TO_B06_DOMAIN:
        raise B12AdapterStackError("configuration domain is not frozen")
    if type(configuration.events) is not tuple:
        raise TypeError("configuration events must be an exact tuple")
    if tuple(sorted(configuration.events)) != configuration.events:
        raise B12AdapterStackError("configuration events are not in canonical order")
    coordinate_dimension, configuration_cap = _DOMAIN_DIMENSION_AND_CAP[
        configuration.domain_id
    ]
    if len(configuration.events) > configuration_cap:
        raise B12AdapterStackError("configuration exceeds the exact F105 domain cap")
    event_payloads = tuple(
        _event_payload(event, f105_domain_id=configuration.domain_id)
        for event in configuration.events
    )
    return {
        "b06_domain_id": F105_TO_B06_DOMAIN[configuration.domain_id],
        "event_count": len(event_payloads),
        "events": event_payloads,
        "f105_coordinate_dimension": coordinate_dimension,
        "f105_domain_id": configuration.domain_id,
    }


def _configuration_sha256(configuration: ExactConfiguration) -> str:
    return _sha256(
        "heterodiff-b12-exact-configuration-v1",
        _configuration_payload(configuration),
    )


@dataclass(frozen=True)
class ExactContextEncoding:
    """One exact 64-coordinate qualification encoding with occurrence custody."""

    b06_domain_id: str
    f105_domain_id: str
    coordinates: Tuple[Fraction, ...]
    event_count: int
    ordered_event_sha256s: Tuple[str, ...]
    configuration_sha256: str
    encoding_sha256: str

    def semantic_payload(self) -> Dict[str, Any]:
        if type(self) is not ExactContextEncoding:
            raise TypeError("context encoding must have exact concrete type")
        if self.b06_domain_id not in B06_TO_F105_DOMAIN:
            raise B12AdapterStackError("context B06 domain is not frozen")
        if self.f105_domain_id != B06_TO_F105_DOMAIN[self.b06_domain_id]:
            raise B12AdapterStackError("context domain mapping is inconsistent")
        if type(self.coordinates) is not tuple or len(self.coordinates) != PRIMARY_CONTEXT_DIMENSION:
            raise B12AdapterStackError("context dimension is not exactly 64")
        coordinate_payload = tuple(_fraction_payload(value) for value in self.coordinates)
        count = _exact_nonnegative_integer(self.event_count, name="event_count")
        if type(self.ordered_event_sha256s) is not tuple:
            raise TypeError("ordered_event_sha256s must be an exact tuple")
        if len(self.ordered_event_sha256s) != count:
            raise B12AdapterStackError("occurrence digest roster was truncated or expanded")
        event_digests = tuple(
            _exact_sha256(value, name="event occurrence digest")
            for value in self.ordered_event_sha256s
        )
        configuration_sha256 = _exact_sha256(
            self.configuration_sha256,
            name="configuration_sha256",
        )
        payload = {
            "b06_domain_id": self.b06_domain_id,
            "configuration_sha256": configuration_sha256,
            "context_coordinates": coordinate_payload,
            "context_dimension": PRIMARY_CONTEXT_DIMENSION,
            "event_count": count,
            "f105_domain_id": self.f105_domain_id,
            "ordered_event_sha256s": event_digests,
        }
        if self.encoding_sha256 != _sha256(
            "heterodiff-b12-exact-context-encoding-v1", payload
        ):
            raise B12AdapterStackError("context encoding digest mismatch")
        return payload


def encode_exact_context(configuration: ExactConfiguration) -> ExactContextEncoding:
    """Encode every exact event occurrence without a truncation parameter.

    The 64-coordinate projection is deterministic and exact.  Its custody
    payload separately retains one digest per occurrence, including repeated
    identical rows, and the digest of the complete canonical configuration.
    No injectivity or learned-representation claim is made for the 64-vector.
    """

    payload = _configuration_payload(configuration)
    event_payloads = payload["events"]
    event_sha256s = tuple(
        _sha256("heterodiff-b12-exact-event-v1", event_payload)
        for event_payload in event_payloads
    )
    accumulators = [0] * PRIMARY_CONTEXT_DIMENSION
    for ordinal, event_payload in enumerate(event_payloads):
        occurrence_bytes = hashlib.sha512(
            b"heterodiff-b12-context-occurrence-v1\0"
            + str(ordinal).encode("ascii")
            + b"\0"
            + _canonical(event_payload)
        ).digest()
        for index, byte in enumerate(occurrence_bytes):
            accumulators[index] += byte - 128
    event_count = len(event_payloads)
    denominator = 128 * max(1, event_count)
    coordinates = tuple(Fraction(value, denominator) for value in accumulators)
    configuration_sha256 = _sha256(
        "heterodiff-b12-exact-configuration-v1", payload
    )
    semantic_payload = {
        "b06_domain_id": payload["b06_domain_id"],
        "configuration_sha256": configuration_sha256,
        "context_coordinates": tuple(_fraction_payload(value) for value in coordinates),
        "context_dimension": PRIMARY_CONTEXT_DIMENSION,
        "event_count": event_count,
        "f105_domain_id": payload["f105_domain_id"],
        "ordered_event_sha256s": event_sha256s,
    }
    result = ExactContextEncoding(
        b06_domain_id=payload["b06_domain_id"],
        f105_domain_id=payload["f105_domain_id"],
        coordinates=coordinates,
        event_count=event_count,
        ordered_event_sha256s=event_sha256s,
        configuration_sha256=configuration_sha256,
        encoding_sha256=_sha256(
            "heterodiff-b12-exact-context-encoding-v1", semantic_payload
        ),
    )
    result.semantic_payload()
    return result


def _legacy_partial_roster_snapshot() -> Tuple[Tuple[str, str, str], ...]:
    """Recover the accepted zero-delta v2 roster for successor comparison only."""

    public = _b12.REQUIRED_ADAPTER_ROSTER
    private = tuple(tuple(row) for row in _b12.semantics()["required_adapter_roster"])
    if type(public) is not tuple or tuple(public) != private:
        raise RuntimeError("accepted B12 public and private adapter rosters differ")
    if len(private) != 22 or len(set(private)) != 22:
        raise RuntimeError("accepted B12 adapter roster is not exact 22-row unique")
    return private


def _corrected_b06_roster_snapshot() -> Tuple[Tuple[str, str, str], ...]:
    """Derive the successor roster directly from the frozen B06 registry."""

    frozen = _b06.FROZEN_REGISTRY
    if type(frozen) is not dict:
        raise RuntimeError("B06 frozen registry must be an exact dictionary")
    domains = (RETAIL_B06_DOMAIN_ID, PHYSIONET_B06_DOMAIN_ID)
    primary_by_id = {
        row["method_id"]: row for row in frozen["primary_pair"]
    }
    control_by_id = {
        row["control_id"]: row for row in frozen["controls"]
    }
    family_by_id = {
        row["family_id"]: row for row in frozen["literature_families"]
    }
    external_by_key = {
        (row["method_id"], row["domain_id"]): row
        for row in frozen["external_baselines"]
    }
    rows = []
    for adapter_id in _PRIMARY_IDS:
        row = primary_by_id[adapter_id]
        for domain_id in domains:
            rows.append((adapter_id, domain_id, row["config_sha256"]))
    for adapter_id in _CONTROL_IDS:
        row = control_by_id[adapter_id]
        for domain_id in domains:
            rows.append((adapter_id, domain_id, row["config_sha256"]))
    for adapter_id in _LITERATURE_IDS:
        family = family_by_id[adapter_id]
        implementations = family["implementation_by_domain"]
        for domain_id in domains:
            rows.append(
                (
                    adapter_id,
                    domain_id,
                    implementations[domain_id]["config_sha256"],
                )
            )
    for adapter_id, domain_id in (
        (_CSDI_ID, PHYSIONET_B06_DOMAIN_ID),
        (_EDITPP_ID, RETAIL_B06_DOMAIN_ID),
    ):
        row = external_by_key[(adapter_id, domain_id)]
        rows.append((adapter_id, domain_id, row["config_sha256"]))
    snapshot = tuple(rows)
    if len(snapshot) != 22 or len(set(snapshot)) != 22:
        raise RuntimeError("corrected B06 adapter roster is not exact 22-row unique")
    for row in snapshot:
        if type(row) is not tuple or len(row) != 3:
            raise RuntimeError("corrected B06 adapter row shape differs")
        adapter_id, domain_id, config_sha256 = row
        if type(adapter_id) is not str or not adapter_id:
            raise RuntimeError("corrected B06 adapter identity differs")
        if domain_id not in B06_TO_F105_DOMAIN:
            raise RuntimeError("corrected B06 adapter domain differs")
        _exact_sha256(config_sha256, name="corrected B06 config_sha256", nonzero=True)
    return snapshot


_PRIMARY_IDS = (
    "association-aware-guide-plus-residual",
    "unified-direct-conditioner",
)
_CONTROL_IDS = (
    "analytic-guide-only-residual-removed",
    "direct-or-residual-only-analytic-guide-removed",
    "association-destroyed-or-factorized-eventwise",
    "unconditional-base-sanity-reference",
)
_LITERATURE_IDS = (
    "ngdb-style-auxiliary-guide-plus-correction",
    "deft-style-generalized-h-frozen-base-correction",
    "task-compatible-same-base-smc-or-feynman-kac",
    "closest-variable-cardinality-point-or-edit-generator",
)
_CSDI_ID = "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1"
_EDITPP_ID = "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1"


LEGACY_PARTIAL_ROSTER_SNAPSHOT = _legacy_partial_roster_snapshot()
_ADAPTER_ROSTER_SNAPSHOT = _corrected_b06_roster_snapshot()
ADAPTER_ROSTER_SNAPSHOT = tuple(_ADAPTER_ROSTER_SNAPSHOT)
if tuple((row[0], row[1]) for row in _ADAPTER_ROSTER_SNAPSHOT) != tuple(
    (row[0], row[1]) for row in LEGACY_PARTIAL_ROSTER_SNAPSHOT
):
    raise RuntimeError("corrected B06 roster changed the accepted identity/domain order")
LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS = tuple(
    ordinal
    for ordinal, (legacy, corrected) in enumerate(
        zip(LEGACY_PARTIAL_ROSTER_SNAPSHOT, _ADAPTER_ROSTER_SNAPSHOT)
    )
    if legacy[2] != corrected[2]
)
if LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS != tuple(range(12, 20)):
    raise RuntimeError("legacy/corrected mismatch is not exactly eight literature rows")


def _adapter_class(adapter_id: str) -> str:
    if adapter_id in _PRIMARY_IDS:
        return "PRIMARY"
    if adapter_id in _CONTROL_IDS:
        return "CONTROL"
    if adapter_id in _LITERATURE_IDS:
        return "LITERATURE_FAMILY"
    if adapter_id == _CSDI_ID:
        return "EXTERNAL_CSDI"
    if adapter_id == _EDITPP_ID:
        return "EXTERNAL_EDITPP"
    raise RuntimeError("accepted adapter identity lacks a frozen class")


def _conformance_scope(adapter_id: str) -> str:
    adapter_class = _adapter_class(adapter_id)
    if adapter_class in ("PRIMARY", "CONTROL"):
        return "SYNTHETIC_EXACT_CONFIGURATION_INTERFACE_PASS_PRODUCTION_RUNTIME_OPEN"
    if adapter_class == "LITERATURE_FAMILY":
        return "SYNTHETIC_EXACT_CONFIGURATION_INTERFACE_PASS_CLEAN_ROOM_ALGORITHM_AND_RUNTIME_OPEN"
    return "SYNTHETIC_EXACT_CONFIGURATION_INTERFACE_PASS_AUTHOR_EXTENSIONS_AND_UPSTREAM_RUNTIME_OPEN"


def _implementation_binding(
    *,
    module_source_sha256: str,
    adapter_id: str,
    domain_id: str,
    config_sha256: str,
) -> str:
    source = _exact_sha256(
        module_source_sha256,
        name="module_source_sha256",
        nonzero=True,
    )
    return _sha256(
        "heterodiff-b12-row-specific-adapter-implementation-source-v1",
        {
            "adapter_id": adapter_id,
            "config_sha256": config_sha256,
            "domain_id": domain_id,
            "entrypoint": (
                "heterodiff.evaluation.b12_two_domain_adapter_stack:"
                "build_synthetic_conformance_manifest"
            ),
            "module_source_sha256": source,
        },
    )


@dataclass(frozen=True)
class AdapterConformanceRecord:
    """One source-bound synthetic-interface result in accepted roster order."""

    ordinal: int
    adapter_id: str
    domain_id: str
    adapter_class: str
    config_sha256: str
    module_source_sha256: str
    implementation_source_sha256: str
    input_sha256: str
    output_sha256: str
    conformance_result: str
    context_encoding_sha256: str
    event_count: int
    f105_coordinate_dimension: int
    receipt: _b12.AdapterReceipt
    record_sha256: str

    def semantic_payload(self) -> Dict[str, Any]:
        if type(self) is not AdapterConformanceRecord:
            raise TypeError("conformance record must have exact concrete type")
        ordinal = _exact_nonnegative_integer(self.ordinal, name="ordinal")
        if ordinal >= len(_ADAPTER_ROSTER_SNAPSHOT):
            raise B12AdapterStackError("adapter ordinal is outside the roster")
        expected = _ADAPTER_ROSTER_SNAPSHOT[ordinal]
        if (self.adapter_id, self.domain_id, self.config_sha256) != expected:
            raise B12AdapterStackError("adapter identity/domain/config differs from B12")
        adapter_class = _adapter_class(self.adapter_id)
        if self.adapter_class != adapter_class:
            raise B12AdapterStackError("adapter class differs from the frozen identity")
        if self.conformance_result != _conformance_scope(self.adapter_id):
            raise B12AdapterStackError("adapter conformance scope was widened")
        module_source_sha256 = _exact_sha256(
            self.module_source_sha256,
            name="module_source_sha256",
            nonzero=True,
        )
        implementation_source_sha256 = _exact_sha256(
            self.implementation_source_sha256,
            name="implementation_source_sha256",
            nonzero=True,
        )
        expected_implementation = _implementation_binding(
            module_source_sha256=module_source_sha256,
            adapter_id=self.adapter_id,
            domain_id=self.domain_id,
            config_sha256=self.config_sha256,
        )
        if implementation_source_sha256 != expected_implementation:
            raise B12AdapterStackError("row-specific implementation binding differs")
        input_sha256 = _exact_sha256(self.input_sha256, name="input_sha256")
        output_sha256 = _exact_sha256(self.output_sha256, name="output_sha256")
        context_sha256 = _exact_sha256(
            self.context_encoding_sha256,
            name="context_encoding_sha256",
        )
        event_count = _exact_nonnegative_integer(self.event_count, name="event_count")
        if type(self.f105_coordinate_dimension) is not int:
            raise TypeError("f105_coordinate_dimension must be an exact integer")
        f105_domain_id = B06_TO_F105_DOMAIN[self.domain_id]
        if self.f105_coordinate_dimension != _DOMAIN_DIMENSION_AND_CAP[f105_domain_id][0]:
            raise B12AdapterStackError("record coordinate dimension differs from F105")
        if type(self.receipt) is not _b12.AdapterReceipt:
            raise TypeError("receipt must have exact accepted AdapterReceipt type")
        self.receipt.validate()
        if (
            self.receipt.adapter_id,
            self.receipt.domain_id,
            self.receipt.config_sha256,
            self.receipt.implementation_source_sha256,
            self.receipt.input_sha256,
            self.receipt.output_sha256,
        ) != (
            self.adapter_id,
            self.domain_id,
            self.config_sha256,
            implementation_source_sha256,
            input_sha256,
            output_sha256,
        ):
            raise B12AdapterStackError("typed receipt differs from conformance record")
        payload = {
            "adapter_class": adapter_class,
            "adapter_id": self.adapter_id,
            "config_sha256": self.config_sha256,
            "conformance_result": self.conformance_result,
            "context_encoding_sha256": context_sha256,
            "domain_id": self.domain_id,
            "event_count": event_count,
            "f105_coordinate_dimension": self.f105_coordinate_dimension,
            "implementation_source_sha256": implementation_source_sha256,
            "input_sha256": input_sha256,
            "module_source_sha256": module_source_sha256,
            "ordinal": ordinal,
            "output_sha256": output_sha256,
            "predicate_receipt_sha256": self.receipt.predicate.receipt_sha256,
        }
        if self.record_sha256 != _sha256(
            "heterodiff-b12-adapter-conformance-record-v1", payload
        ):
            raise B12AdapterStackError("adapter conformance record digest mismatch")
        return payload


def _predicate_receipt(
    *,
    adapter_id: str,
    domain_id: str,
    config_sha256: str,
    implementation_source_sha256: str,
    input_sha256: str,
    output_sha256: str,
    conformance_result: str,
) -> _b12.AuthenticatedPredicateReceipt:
    subject = _sha256(
        "heterodiff-b12-adapter-subject-v1",
        {
            "adapter_id": adapter_id,
            "config_sha256": config_sha256,
            "domain_id": domain_id,
            "implementation_source_sha256": implementation_source_sha256,
            "input_sha256": input_sha256,
            "output_sha256": output_sha256,
        },
    )
    evidence = _sha256(
        "heterodiff-b12-local-synthetic-adapter-conformance-evidence-v1",
        {
            "adapter_id": adapter_id,
            "conformance_result": conformance_result,
            "domain_id": domain_id,
            "subject_sha256": subject,
        },
    )
    payload = {
        "authentication_evidence_sha256": evidence,
        "authentication_method_id": (
            "DETERMINISTIC_LOCAL_SYNTHETIC_INTERFACE_QUALIFICATION_NOT_INDEPENDENT_V1"
        ),
        "disposition": "ACCEPT",
        "predicate_id": f"ADAPTER_RECEIPT:{adapter_id}:{domain_id}",
        "reviewer_principal_id": "LOCAL_SYNTHETIC_INTERFACE_QUALIFIER_NOT_INDEPENDENT",
        "subject_sha256": subject,
    }
    return _b12.AuthenticatedPredicateReceipt(
        predicate_id=payload["predicate_id"],
        subject_sha256=subject,
        reviewer_principal_id=payload["reviewer_principal_id"],
        authentication_method_id=payload["authentication_method_id"],
        authentication_evidence_sha256=evidence,
        disposition="ACCEPT",
        receipt_sha256=_sha256(
            "heterodiff-b12-authenticated-predicate-v1", payload
        ),
    )


def _record_for_row(
    *,
    ordinal: int,
    row: Tuple[str, str, str],
    configuration: ExactConfiguration,
    context: ExactContextEncoding,
    module_source_sha256: str,
) -> AdapterConformanceRecord:
    adapter_id, domain_id, config_sha256 = row
    if context.b06_domain_id != domain_id:
        raise B12AdapterStackError("context and adapter domains differ")
    input_sha256 = _configuration_sha256(configuration)
    if input_sha256 != context.configuration_sha256:
        raise B12AdapterStackError("configuration and context input digests differ")
    implementation_source_sha256 = _implementation_binding(
        module_source_sha256=module_source_sha256,
        adapter_id=adapter_id,
        domain_id=domain_id,
        config_sha256=config_sha256,
    )
    conformance_result = _conformance_scope(adapter_id)
    output_sha256 = _sha256(
        "heterodiff-b12-synthetic-adapter-interface-output-v1",
        {
            "adapter_class": _adapter_class(adapter_id),
            "adapter_id": adapter_id,
            "config_sha256": config_sha256,
            "conformance_result": conformance_result,
            "context_encoding_sha256": context.encoding_sha256,
            "domain_id": domain_id,
            "event_count": context.event_count,
            "implementation_source_sha256": implementation_source_sha256,
            "input_sha256": input_sha256,
            "output_kind": "QUALIFICATION_INTERFACE_ARTIFACT_NOT_MODEL_SAMPLE",
        },
    )
    predicate = _predicate_receipt(
        adapter_id=adapter_id,
        domain_id=domain_id,
        config_sha256=config_sha256,
        implementation_source_sha256=implementation_source_sha256,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
        conformance_result=conformance_result,
    )
    receipt = _b12.AdapterReceipt(
        adapter_id=adapter_id,
        domain_id=domain_id,
        config_sha256=config_sha256,
        implementation_source_sha256=implementation_source_sha256,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
        predicate=predicate,
    )
    receipt.validate()
    semantic_payload = {
        "adapter_class": _adapter_class(adapter_id),
        "adapter_id": adapter_id,
        "config_sha256": config_sha256,
        "conformance_result": conformance_result,
        "context_encoding_sha256": context.encoding_sha256,
        "domain_id": domain_id,
        "event_count": context.event_count,
        "f105_coordinate_dimension": _DOMAIN_DIMENSION_AND_CAP[configuration.domain_id][0],
        "implementation_source_sha256": implementation_source_sha256,
        "input_sha256": input_sha256,
        "module_source_sha256": module_source_sha256,
        "ordinal": ordinal,
        "output_sha256": output_sha256,
        "predicate_receipt_sha256": predicate.receipt_sha256,
    }
    record = AdapterConformanceRecord(
        ordinal=ordinal,
        adapter_id=adapter_id,
        domain_id=domain_id,
        adapter_class=_adapter_class(adapter_id),
        config_sha256=config_sha256,
        module_source_sha256=module_source_sha256,
        implementation_source_sha256=implementation_source_sha256,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
        conformance_result=conformance_result,
        context_encoding_sha256=context.encoding_sha256,
        event_count=context.event_count,
        f105_coordinate_dimension=_DOMAIN_DIMENSION_AND_CAP[configuration.domain_id][0],
        receipt=receipt,
        record_sha256=_sha256(
            "heterodiff-b12-adapter-conformance-record-v1", semantic_payload
        ),
    )
    record.semantic_payload()
    return record


def build_synthetic_conformance_manifest(
    *,
    retail_configuration: ExactConfiguration,
    physionet_configuration: ExactConfiguration,
    module_source_sha256: str,
) -> Tuple[AdapterConformanceRecord, ...]:
    """Build all 22 source-bound qualification rows in accepted roster order."""

    source_sha256 = _exact_sha256(
        module_source_sha256,
        name="module_source_sha256",
        nonzero=True,
    )
    if type(retail_configuration) is not ExactConfiguration:
        raise TypeError("retail_configuration must have exact ExactConfiguration type")
    if retail_configuration.domain_id != RETAIL_DOMAIN_ID:
        raise B12AdapterStackError("retail_configuration belongs to another domain")
    if type(physionet_configuration) is not ExactConfiguration:
        raise TypeError("physionet_configuration must have exact ExactConfiguration type")
    if physionet_configuration.domain_id != PHYSIONET_DOMAIN_ID:
        raise B12AdapterStackError("physionet_configuration belongs to another domain")
    by_domain = {
        RETAIL_B06_DOMAIN_ID: retail_configuration,
        PHYSIONET_B06_DOMAIN_ID: physionet_configuration,
    }
    contexts = {
        domain_id: encode_exact_context(configuration)
        for domain_id, configuration in by_domain.items()
    }
    records = tuple(
        _record_for_row(
            ordinal=ordinal,
            row=row,
            configuration=by_domain[row[1]],
            context=contexts[row[1]],
            module_source_sha256=source_sha256,
        )
        for ordinal, row in enumerate(_ADAPTER_ROSTER_SNAPSHOT)
    )
    if tuple(
        (record.adapter_id, record.domain_id, record.config_sha256)
        for record in records
    ) != _ADAPTER_ROSTER_SNAPSHOT:
        raise RuntimeError("built manifest differs from the accepted B12 roster")
    if len({record.implementation_source_sha256 for record in records}) != 22:
        raise RuntimeError("row-specific implementation bindings are not unique")
    for record in records:
        record.semantic_payload()
    return records


def build_synthetic_adapter_receipts(
    *,
    retail_configuration: ExactConfiguration,
    physionet_configuration: ExactConfiguration,
    module_source_sha256: str,
) -> Tuple[_b12.AdapterReceipt, ...]:
    """Return the exact 22 qualification-only typed adapter receipts."""

    return tuple(
        record.receipt
        for record in build_synthetic_conformance_manifest(
            retail_configuration=retail_configuration,
            physionet_configuration=physionet_configuration,
            module_source_sha256=module_source_sha256,
        )
    )


@dataclass(frozen=True)
class AuthorExtensionObligation:
    """One exact, deliberately unimplemented upstream-extension boundary."""

    predicate_id: str
    adapter_id: str
    domain_id: str
    extension_id: str
    ordinal_within_adapter: int
    status: str = "OPEN_IMPLEMENTATION_AND_RUNTIME_EVIDENCE_ABSENT"
    upstream_execution_claimed: bool = False
    domain_scale_qualification_claimed: bool = False

    def validate(self) -> None:
        if type(self) is not AuthorExtensionObligation:
            raise TypeError("author-extension obligation must have exact concrete type")
        if self.adapter_id not in (_CSDI_ID, _EDITPP_ID):
            raise B12AdapterStackError("extension adapter identity is not frozen")
        expected_domain = (
            PHYSIONET_B06_DOMAIN_ID if self.adapter_id == _CSDI_ID else RETAIL_B06_DOMAIN_ID
        )
        if self.domain_id != expected_domain:
            raise B12AdapterStackError("extension domain differs from its adapter")
        if type(self.ordinal_within_adapter) is not int or not 1 <= self.ordinal_within_adapter <= 4:
            raise TypeError("extension ordinal must be an exact integer in 1..4")
        prefix = "CSDI" if self.adapter_id == _CSDI_ID else "EDITPP"
        if self.predicate_id != f"{prefix}_AUTHOR_EXTENSION_{self.ordinal_within_adapter}":
            raise B12AdapterStackError("extension predicate identity differs")
        if type(self.extension_id) is not str or not self.extension_id:
            raise TypeError("extension_id must be a nonempty exact string")
        if self.status != "OPEN_IMPLEMENTATION_AND_RUNTIME_EVIDENCE_ABSENT":
            raise B12AdapterStackError("extension obligation was falsely closed")
        if type(self.upstream_execution_claimed) is not bool or self.upstream_execution_claimed:
            raise B12AdapterStackError("upstream execution cannot be claimed here")
        if (
            type(self.domain_scale_qualification_claimed) is not bool
            or self.domain_scale_qualification_claimed
        ):
            raise B12AdapterStackError("domain-scale qualification cannot be claimed here")


_CSDI_EXTENSIONS = (
    "LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS",
    "VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER",
    "EXACT_PHYSIONET_F105_EVENT_ADAPTER",
    "FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE",
)
_EDITPP_EXTENSIONS = (
    "STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS",
    "SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL",
    "EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER",
    "ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE",
)

AUTHOR_EXTENSION_OBLIGATIONS = tuple(
    AuthorExtensionObligation(
        predicate_id=f"CSDI_AUTHOR_EXTENSION_{ordinal}",
        adapter_id=_CSDI_ID,
        domain_id=PHYSIONET_B06_DOMAIN_ID,
        extension_id=extension_id,
        ordinal_within_adapter=ordinal,
    )
    for ordinal, extension_id in enumerate(_CSDI_EXTENSIONS, start=1)
) + tuple(
    AuthorExtensionObligation(
        predicate_id=f"EDITPP_AUTHOR_EXTENSION_{ordinal}",
        adapter_id=_EDITPP_ID,
        domain_id=RETAIL_B06_DOMAIN_ID,
        extension_id=extension_id,
        ordinal_within_adapter=ordinal,
    )
    for ordinal, extension_id in enumerate(_EDITPP_EXTENSIONS, start=1)
)

for _obligation in AUTHOR_EXTENSION_OBLIGATIONS:
    _obligation.validate()


def qualification_fixture_configurations() -> Tuple[ExactConfiguration, ExactConfiguration]:
    """Return tiny deterministic Retail/PhysioNet fixtures for qualification only."""

    retail_zero = ExactEvent(RETAIL_DOMAIN_ID, (Fraction(0),) * 10)
    retail_distinct = ExactEvent(
        RETAIL_DOMAIN_ID,
        (Fraction(1, 3),) + (Fraction(0),) * 9,
    )
    physionet_zero = ExactEvent(PHYSIONET_DOMAIN_ID, (Fraction(0),) * 112)
    physionet_distinct = ExactEvent(
        PHYSIONET_DOMAIN_ID,
        (Fraction(1, 5),) + (Fraction(0),) * 111,
    )
    retail = ExactConfiguration(
        RETAIL_DOMAIN_ID,
        (retail_zero, retail_zero, retail_distinct),
    )
    physionet = ExactConfiguration(
        PHYSIONET_DOMAIN_ID,
        (physionet_zero, physionet_zero, physionet_distinct),
    )
    return retail, physionet


__all__ = [
    "ADAPTER_ROSTER_SNAPSHOT",
    "AUTHOR_EXTENSION_OBLIGATIONS",
    "AdapterConformanceRecord",
    "AuthorExtensionObligation",
    "B12AdapterStackError",
    "ExactContextEncoding",
    "LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS",
    "LEGACY_PARTIAL_ROSTER_SNAPSHOT",
    "PHYSIONET_B06_DOMAIN_ID",
    "PRIMARY_CONTEXT_DIMENSION",
    "RETAIL_B06_DOMAIN_ID",
    "SCHEMA_VERSION",
    "build_synthetic_adapter_receipts",
    "build_synthetic_conformance_manifest",
    "encode_exact_context",
    "qualification_fixture_configurations",
]
