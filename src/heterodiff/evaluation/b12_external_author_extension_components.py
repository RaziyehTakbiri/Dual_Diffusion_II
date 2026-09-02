"""Pure offline components for the eight B12 external author extensions.

The accepted B06 registry names four CSDI/PhysioNet author extensions and
four EditPP/Retail author extensions.  This module implements their exact
local transformation and interface surfaces over already-materialized F105
``ExactConfiguration`` values.  It deliberately does not import, execute, or
emulate either upstream package and does not train or sample a model.

The implemented boundary is:

* occurrence-complete, serial-bound channels that retain tied duplicates;
* a variable-cardinality CSDI multiset decoder;
* exact R112 PhysioNet and R10 Retail F105 structural adapters;
* transformed Retail structured-mark heads;
* immutable arbitrary-subset association masks; and
* exactly 64 pending draw slots bound to the accepted F139--F147 contract.

All public builders require exact concrete types and fail closed.  There is no
filesystem, network, subprocess, entropy, data-loader, optimizer, training,
checkpoint, model-inference, or production-receipt surface in this module.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Dict, Mapping, Tuple

from heterodiff.evaluation import b12_two_domain_adapter_stack as _stack
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    PHYSIONET_DOMAIN_ID,
    RETAIL_DOMAIN_ID,
    ExactConfiguration,
    ExactEvent,
    physionet_event_from_decimal_token,
    retail_event_from_decimal_token,
)
from heterodiff.experiments import two_domain_baseline_registry as _b06
from heterodiff.experiments import two_domain_training_checkpoint_plan as _training


SCHEMA_VERSION = "heterodiff-b12-external-author-extension-components-v1"
STATE = (
    "OFFLINE_AUTHOR_EXTENSION_COMPONENTS_IMPLEMENTED_PENDING_INDEPENDENT_"
    "REVIEW_RUNTIME_OPEN"
)
COMPONENT_STATUS = "IMPLEMENTED_OFFLINE_PURE_COMPONENT_PENDING_INDEPENDENT_REVIEW"
DRAW_SLOT_STATUS = "AWAITING_EXTERNAL_MODEL_OUTPUT_NO_OUTPUT_MINTED"
DRAW_COUNT = 64
PRIMARY_CONTEXT_DIMENSION = 64
ZERO_SHA256 = "0" * 64

CSDI_ADAPTER_ID = "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1"
EDITPP_ADAPTER_ID = "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1"
CSDI_B06_DOMAIN_ID = "physionet-challenge-2012"
EDITPP_B06_DOMAIN_ID = "online-retail-ii"
CSDI_B06_CONFIG_SHA256 = (
    "72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046"
)
EDITPP_B06_CONFIG_SHA256 = (
    "64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee"
)
CSDI_TRAINING_CONFIG_SHA256 = (
    "e2c04e136c6799cbd4cc6dda82a6025881b912e70e8e51515f0eafd7af48b85b"
)
EDITPP_TRAINING_CONFIG_SHA256 = (
    "21144dceee490dcb77d7b2aa49ed639daaca0fc13ff750b55e27ba9ffa3e7b5a"
)
TRAINING_PLAN_SEMANTICS_SHA256 = (
    "dd1c74d655f4cfeb4a895c11eb09a9e3ef41c328ce432ad782bce204e59585db"
)
F144_SEMANTICS_SHA256 = (
    "040db767c5bae9879ca5f006095dace2c43d4a2640af19839994465cff2011d2"
)

# Capture the accepted context class and function once.  Rebinding a public
# predecessor-module alias after this module is imported cannot redirect a
# builder or make its validator accept a different context implementation.
_EXACT_CONTEXT_TYPE = _stack.ExactContextEncoding
_ENCODE_EXACT_CONTEXT = _stack.encode_exact_context

_HEX = frozenset("0123456789abcdef")
_EXPECTED_EXTENSIONS: Mapping[str, Tuple[str, ...]] = {
    CSDI_ADAPTER_ID: (
        "LOSSLESS_OCCURRENCE_CHANNEL_FOR_SIMULTANEOUS_DUPLICATE_ROWS",
        "VARIABLE_CARDINALITY_EVENT_MULTISET_DECODER",
        "EXACT_PHYSIONET_F105_EVENT_ADAPTER",
        "FROZEN_PARTIAL_OBSERVATION_MASK_AND_64_DRAW_INTERFACE",
    ),
    EDITPP_ADAPTER_ID: (
        "STRUCTURED_INVOICE_STOCK_DESCRIPTION_QUANTITY_PRICE_COUNTRY_MARK_HEADS",
        "SIMULTANEOUS_AND_DUPLICATE_OCCURRENCE_SERIAL_CHANNEL",
        "EXACT_SOURCE_CIVIL_RETAIL_F105_EVENT_ADAPTER",
        "ARBITRARY_UNORDERED_SUBSET_ASSOCIATION_MASK_AND_64_DRAW_INTERFACE",
    ),
}
_ENTRYPOINTS: Mapping[Tuple[str, int], str] = {
    (CSDI_ADAPTER_ID, 1): "build_csdi_author_adapter",
    (CSDI_ADAPTER_ID, 2): "decode_csdi_event_multiset",
    (CSDI_ADAPTER_ID, 3): "build_csdi_author_adapter",
    (CSDI_ADAPTER_ID, 4): "build_csdi_conditioning_interface",
    (EDITPP_ADAPTER_ID, 1): "build_editpp_author_adapter",
    (EDITPP_ADAPTER_ID, 2): "build_editpp_author_adapter",
    (EDITPP_ADAPTER_ID, 3): "build_editpp_author_adapter",
    (EDITPP_ADAPTER_ID, 4): "build_editpp_conditioning_interface",
}


class ExternalAuthorExtensionError(ValueError):
    """Raised before an inexact value can cross this component boundary."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _digest(domain: str, value: Any) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be a nonempty exact string")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _exact_sha256(value: object, *, name: str, nonzero: bool = False) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ExternalAuthorExtensionError(f"{name} must be lowercase SHA-256")
    if nonzero and value == ZERO_SHA256:
        raise ExternalAuthorExtensionError(f"{name} must be nonzero")
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a nonnegative exact integer")
    return value


def _fraction_payload(value: object, *, name: str) -> Tuple[str, str]:
    if type(value) is not Fraction:
        raise TypeError(f"{name} must be an exact Fraction")
    return (str(value.numerator), str(value.denominator))


def _event_payload(event: ExactEvent, *, expected_domain: str) -> Dict[str, Any]:
    if type(event) is not ExactEvent:
        raise TypeError("event must have exact ExactEvent type")
    if event.domain_id != expected_domain:
        raise ExternalAuthorExtensionError("event crosses the frozen domain boundary")
    expected_dimension = 112 if expected_domain == PHYSIONET_DOMAIN_ID else 10
    if type(event.coordinates) is not tuple or len(event.coordinates) != expected_dimension:
        raise ExternalAuthorExtensionError("event coordinate dimension differs from F105")
    coordinates = tuple(
        _fraction_payload(value, name="event coordinate") for value in event.coordinates
    )
    if expected_domain == PHYSIONET_DOMAIN_ID:
        _validate_physionet_coordinates(event.coordinates)
    elif expected_domain == RETAIL_DOMAIN_ID:
        _validate_retail_coordinates(event.coordinates)
    else:
        raise ExternalAuthorExtensionError("event domain is not one of the frozen domains")
    return {
        "coordinates": coordinates,
        "f105_coordinate_dimension": expected_dimension,
        "f105_domain_id": expected_domain,
    }


def _validate_physionet_coordinates(coordinates: Tuple[Fraction, ...]) -> None:
    one_hot = coordinates[:37]
    if sum(one_hot, Fraction(0)) != 1 or any(value not in (0, 1) for value in one_hot):
        raise ExternalAuthorExtensionError("PhysioNet type block is not exact one-hot-37")
    active = one_hot.index(Fraction(1))
    time = coordinates[37]
    if not Fraction(0) <= time <= Fraction(1):
        raise ExternalAuthorExtensionError("PhysioNet elapsed-time coordinate is outside [0,1]")
    masks = coordinates[38:75]
    values = coordinates[75:112]
    for index, mask in enumerate(masks):
        if mask not in (0, 1) or (index != active and mask != 0):
            raise ExternalAuthorExtensionError("PhysioNet presence block differs from F105")
    for index, value in enumerate(values):
        if index != active and value != 0:
            raise ExternalAuthorExtensionError("PhysioNet value block differs from F105")
    active_mask = masks[active]
    active_value = values[active]
    if active_mask == 0 and active_value != 0:
        raise ExternalAuthorExtensionError("missing PhysioNet mark has nonzero value")
    if active_mask == 1 and not Fraction(0) <= active_value < Fraction(1):
        raise ExternalAuthorExtensionError("present PhysioNet mark is outside F105 range")


def _validate_retail_coordinates(coordinates: Tuple[Fraction, ...]) -> None:
    invoice, cancellation, stock = coordinates[:3]
    description_present, description = coordinates[3:5]
    source_civil, quantity, price = coordinates[5:8]
    country_present, country = coordinates[8:10]
    if not Fraction(0) < invoice < Fraction(1):
        raise ExternalAuthorExtensionError("Retail invoice coordinate is outside F105")
    if cancellation not in (0, 1):
        raise ExternalAuthorExtensionError("Retail cancellation coordinate is not binary")
    if not Fraction(0) < stock < Fraction(1):
        raise ExternalAuthorExtensionError("Retail stock coordinate is outside F105")
    for label, present, value in (
        ("description", description_present, description),
        ("country", country_present, country),
    ):
        if present not in (0, 1):
            raise ExternalAuthorExtensionError(f"Retail {label} presence is not binary")
        if not Fraction(0) <= value < Fraction(1):
            raise ExternalAuthorExtensionError(f"Retail {label} coordinate is outside F105")
        if present == 0 and value != 0:
            raise ExternalAuthorExtensionError(f"missing Retail {label} is nonzero")
    if not Fraction(0) <= source_civil < Fraction(1):
        raise ExternalAuthorExtensionError("Retail source-civil time is outside F105")
    if not Fraction(-1) < quantity < Fraction(1):
        raise ExternalAuthorExtensionError("Retail quantity coordinate is outside F105")
    if not Fraction(-1) < price < Fraction(1):
        raise ExternalAuthorExtensionError("Retail price coordinate is outside F105")


def _configuration_payload(
    configuration: ExactConfiguration, *, expected_domain: str
) -> Dict[str, Any]:
    if type(configuration) is not ExactConfiguration:
        raise TypeError("configuration must have exact ExactConfiguration type")
    if configuration.domain_id != expected_domain:
        raise ExternalAuthorExtensionError("configuration crosses the frozen domain")
    if type(configuration.events) is not tuple:
        raise TypeError("configuration events must be an exact tuple")
    if tuple(sorted(configuration.events)) != configuration.events:
        raise ExternalAuthorExtensionError("configuration order is not F105 canonical")
    cap = 131072 if expected_domain == PHYSIONET_DOMAIN_ID else 1067371
    if len(configuration.events) > cap:
        raise ExternalAuthorExtensionError("configuration exceeds the frozen F105 cap")
    events = tuple(
        _event_payload(event, expected_domain=expected_domain)
        for event in configuration.events
    )
    return {
        "event_count": len(events),
        "events": events,
        "f105_coordinate_dimension": 112 if expected_domain == PHYSIONET_DOMAIN_ID else 10,
        "f105_domain_id": expected_domain,
    }


def _configuration_sha256(
    configuration: ExactConfiguration, *, expected_domain: str
) -> str:
    return _digest(
        "heterodiff-b12-external-author-extension-exact-configuration-v1",
        _configuration_payload(configuration, expected_domain=expected_domain),
    )


def _expected_identity(adapter_id: str) -> Tuple[str, str, str, str]:
    if adapter_id == CSDI_ADAPTER_ID:
        return (
            CSDI_B06_DOMAIN_ID,
            PHYSIONET_DOMAIN_ID,
            CSDI_B06_CONFIG_SHA256,
            CSDI_TRAINING_CONFIG_SHA256,
        )
    if adapter_id == EDITPP_ADAPTER_ID:
        return (
            EDITPP_B06_DOMAIN_ID,
            RETAIL_DOMAIN_ID,
            EDITPP_B06_CONFIG_SHA256,
            EDITPP_TRAINING_CONFIG_SHA256,
        )
    raise ExternalAuthorExtensionError("adapter identity is not frozen")


def _assert_predecessor_contracts() -> None:
    registry = _b06.validate_registry(deepcopy(_b06.FROZEN_REGISTRY))
    external_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in registry["external_baselines"]
    }
    if set(external_rows) != {
        (CSDI_ADAPTER_ID, CSDI_B06_DOMAIN_ID),
        (EDITPP_ADAPTER_ID, EDITPP_B06_DOMAIN_ID),
    }:
        raise RuntimeError("B06 external identity/domain roster differs")
    for adapter_id in (CSDI_ADAPTER_ID, EDITPP_ADAPTER_ID):
        b06_domain, _, config_sha256, training_sha256 = _expected_identity(adapter_id)
        row = external_rows[(adapter_id, b06_domain)]
        if row["config_sha256"] != config_sha256:
            raise RuntimeError("B06 external configuration digest differs")
        statement = row["native_capability_and_extension_statement"]
        if tuple(statement["author_extensions"]) != _EXPECTED_EXTENSIONS[adapter_id]:
            raise RuntimeError("B06 external author-extension roster differs")
        if statement["runtime_qualification_owned_by_B12"] is not True:
            raise RuntimeError("B06 external runtime ownership differs")
        if statement["all_extension_compute_charged"] is not True:
            raise RuntimeError("B06 extension compute charging differs")
        training_rows = {
            (value["method_id"], value["domain_id"]): value
            for value in _training.executable_configuration_rows()
        }
        if training_rows[(adapter_id, b06_domain)][
            "executable_configuration_sha256"
        ] != training_sha256:
            raise RuntimeError("F139--F147 executable configuration digest differs")
    if _training.plan_semantics_sha256() != TRAINING_PLAN_SEMANTICS_SHA256:
        raise RuntimeError("F139--F147 plan semantics differ")
    if _training.f144_semantics_sha256() != F144_SEMANTICS_SHA256:
        raise RuntimeError("F144 checkpoint-selection semantics differ")
    if _stack.PRIMARY_CONTEXT_DIMENSION != PRIMARY_CONTEXT_DIMENSION:
        raise RuntimeError("accepted B12 context dimension differs")
    obligation_pairs = tuple(
        (value.adapter_id, value.extension_id) for value in _stack.AUTHOR_EXTENSION_OBLIGATIONS
    )
    expected_pairs = tuple(
        (adapter_id, extension_id)
        for adapter_id in (CSDI_ADAPTER_ID, EDITPP_ADAPTER_ID)
        for extension_id in _EXPECTED_EXTENSIONS[adapter_id]
    )
    if obligation_pairs != expected_pairs:
        raise RuntimeError("accepted B12 author-extension obligation roster differs")


_assert_predecessor_contracts()


@dataclass(frozen=True)
class OccurrenceChannelRow:
    """One canonical serial plus an exact event, retaining every occurrence."""

    serial: int
    event: ExactEvent
    event_sha256: str
    occurrence_sha256: str

    def semantic_payload(self, *, expected_domain: str) -> Dict[str, Any]:
        if type(self) is not OccurrenceChannelRow:
            raise TypeError("occurrence row must have exact concrete type")
        serial = _exact_nonnegative_integer(self.serial, name="occurrence serial")
        event_payload = _event_payload(self.event, expected_domain=expected_domain)
        event_sha256 = _exact_sha256(self.event_sha256, name="event_sha256")
        expected_event_sha256 = _digest(
            "heterodiff-b12-external-author-extension-event-v1", event_payload
        )
        if event_sha256 != expected_event_sha256:
            raise ExternalAuthorExtensionError("event digest differs")
        occurrence_payload = {
            "event_sha256": event_sha256,
            "f105_domain_id": expected_domain,
            "serial": serial,
        }
        occurrence_sha256 = _exact_sha256(
            self.occurrence_sha256, name="occurrence_sha256"
        )
        if occurrence_sha256 != _digest(
            "heterodiff-b12-external-author-extension-occurrence-v1",
            occurrence_payload,
        ):
            raise ExternalAuthorExtensionError("occurrence digest differs")
        return {
            "event": event_payload,
            "event_sha256": event_sha256,
            "occurrence_sha256": occurrence_sha256,
            "serial": serial,
        }


def _build_occurrence_channel(
    configuration: ExactConfiguration, *, expected_domain: str
) -> Tuple[OccurrenceChannelRow, ...]:
    payload = _configuration_payload(configuration, expected_domain=expected_domain)
    rows = []
    for serial, (event, event_payload) in enumerate(
        zip(configuration.events, payload["events"])
    ):
        event_sha256 = _digest(
            "heterodiff-b12-external-author-extension-event-v1", event_payload
        )
        occurrence_payload = {
            "event_sha256": event_sha256,
            "f105_domain_id": expected_domain,
            "serial": serial,
        }
        row = OccurrenceChannelRow(
            serial=serial,
            event=event,
            event_sha256=event_sha256,
            occurrence_sha256=_digest(
                "heterodiff-b12-external-author-extension-occurrence-v1",
                occurrence_payload,
            ),
        )
        row.semantic_payload(expected_domain=expected_domain)
        rows.append(row)
    return tuple(rows)


def _decode_occurrence_channel(
    rows: Tuple[OccurrenceChannelRow, ...], *, expected_domain: str
) -> ExactConfiguration:
    if type(rows) is not tuple:
        raise TypeError("occurrence channel must be an exact tuple")
    if any(type(row) is not OccurrenceChannelRow for row in rows):
        raise TypeError("occurrence channel contains an inexact row")
    if tuple(row.serial for row in rows) != tuple(range(len(rows))):
        raise ExternalAuthorExtensionError("occurrence serials are not contiguous and complete")
    for row in rows:
        row.semantic_payload(expected_domain=expected_domain)
    configuration = ExactConfiguration(expected_domain, tuple(row.event for row in rows))
    if configuration.events != tuple(row.event for row in rows):
        raise ExternalAuthorExtensionError("occurrence channel is not in canonical F105 order")
    _configuration_payload(configuration, expected_domain=expected_domain)
    return configuration


def decode_csdi_event_multiset(
    rows: Tuple[OccurrenceChannelRow, ...],
) -> ExactConfiguration:
    """Decode every CSDI-channel occurrence into one variable-cardinality multiset."""

    return _decode_occurrence_channel(rows, expected_domain=PHYSIONET_DOMAIN_ID)


@dataclass(frozen=True)
class RetailStructuredMarkHeads:
    """Named exact heads over the ten transformed F105 Retail coordinates."""

    occurrence_serial: int
    invoice_token: Fraction
    cancellation: Fraction
    stock_token: Fraction
    description_present: Fraction
    description_token: Fraction
    source_civil_time: Fraction
    quantity: Fraction
    unit_price: Fraction
    country_present: Fraction
    country_token: Fraction
    event_sha256: str
    heads_sha256: str

    def semantic_payload(self) -> Dict[str, Any]:
        if type(self) is not RetailStructuredMarkHeads:
            raise TypeError("Retail mark heads must have exact concrete type")
        serial = _exact_nonnegative_integer(
            self.occurrence_serial, name="occurrence_serial"
        )
        coordinates = (
            self.invoice_token,
            self.cancellation,
            self.stock_token,
            self.description_present,
            self.description_token,
            self.source_civil_time,
            self.quantity,
            self.unit_price,
            self.country_present,
            self.country_token,
        )
        for index, value in enumerate(coordinates):
            _fraction_payload(value, name=f"Retail head {index}")
        _validate_retail_coordinates(coordinates)
        event_sha256 = _exact_sha256(self.event_sha256, name="event_sha256")
        payload = {
            "coordinate_order": (
                "invoice_token",
                "cancellation",
                "stock_token",
                "description_present",
                "description_token",
                "source_civil_time",
                "quantity",
                "unit_price",
                "country_present",
                "country_token",
            ),
            "coordinates": tuple(
                _fraction_payload(value, name="Retail structured head")
                for value in coordinates
            ),
            "event_sha256": event_sha256,
            "f105_coordinate_dimension": 10,
            "occurrence_serial": serial,
            "semantics": "EXACT_TRANSFORMED_F105_HEADS_NOT_INVERTED_RAW_SOURCE_TOKENS",
        }
        if self.heads_sha256 != _digest(
            "heterodiff-b12-editpp-retail-structured-mark-heads-v1", payload
        ):
            raise ExternalAuthorExtensionError("Retail structured-head digest differs")
        return payload


def _retail_heads(row: OccurrenceChannelRow) -> RetailStructuredMarkHeads:
    row.semantic_payload(expected_domain=RETAIL_DOMAIN_ID)
    values = row.event.coordinates
    payload = {
        "coordinate_order": (
            "invoice_token",
            "cancellation",
            "stock_token",
            "description_present",
            "description_token",
            "source_civil_time",
            "quantity",
            "unit_price",
            "country_present",
            "country_token",
        ),
        "coordinates": tuple(
            _fraction_payload(value, name="Retail structured head") for value in values
        ),
        "event_sha256": row.event_sha256,
        "f105_coordinate_dimension": 10,
        "occurrence_serial": row.serial,
        "semantics": "EXACT_TRANSFORMED_F105_HEADS_NOT_INVERTED_RAW_SOURCE_TOKENS",
    }
    result = RetailStructuredMarkHeads(
        occurrence_serial=row.serial,
        invoice_token=values[0],
        cancellation=values[1],
        stock_token=values[2],
        description_present=values[3],
        description_token=values[4],
        source_civil_time=values[5],
        quantity=values[6],
        unit_price=values[7],
        country_present=values[8],
        country_token=values[9],
        event_sha256=row.event_sha256,
        heads_sha256=_digest(
            "heterodiff-b12-editpp-retail-structured-mark-heads-v1", payload
        ),
    )
    result.semantic_payload()
    return result


@dataclass(frozen=True)
class ExternalAuthorAdapter:
    """One exact offline author adapter for one accepted external B06 row."""

    adapter_id: str
    b06_domain_id: str
    f105_domain_id: str
    b06_config_sha256: str
    training_executable_config_sha256: str
    module_source_sha256: str
    configuration: ExactConfiguration
    context: _stack.ExactContextEncoding
    occurrences: Tuple[OccurrenceChannelRow, ...]
    retail_mark_heads: Tuple[RetailStructuredMarkHeads, ...]
    adapter_sha256: str

    def semantic_payload(self) -> Dict[str, Any]:
        if type(self) is not ExternalAuthorAdapter:
            raise TypeError("external author adapter must have exact concrete type")
        expected_b06, expected_f105, expected_config, expected_training = _expected_identity(
            self.adapter_id
        )
        if self.b06_domain_id != expected_b06 or self.f105_domain_id != expected_f105:
            raise ExternalAuthorExtensionError("adapter domain binding differs")
        if self.b06_config_sha256 != expected_config:
            raise ExternalAuthorExtensionError("adapter B06 configuration differs")
        if self.training_executable_config_sha256 != expected_training:
            raise ExternalAuthorExtensionError("adapter training contract differs")
        source_sha256 = _exact_sha256(
            self.module_source_sha256, name="module_source_sha256", nonzero=True
        )
        configuration_payload = _configuration_payload(
            self.configuration, expected_domain=expected_f105
        )
        if type(self.context) is not _EXACT_CONTEXT_TYPE:
            raise TypeError("context must have exact accepted context type")
        context_payload = self.context.semantic_payload()
        expected_context = _ENCODE_EXACT_CONTEXT(self.configuration)
        if self.context != expected_context:
            raise ExternalAuthorExtensionError("64D context differs from accepted encoder")
        if len(self.context.coordinates) != PRIMARY_CONTEXT_DIMENSION:
            raise ExternalAuthorExtensionError("context dimension differs from exact 64")
        if type(self.occurrences) is not tuple:
            raise TypeError("occurrences must be an exact tuple")
        decoded = _decode_occurrence_channel(
            self.occurrences, expected_domain=expected_f105
        )
        if decoded != self.configuration:
            raise ExternalAuthorExtensionError("occurrence decoder changed the configuration")
        occurrence_payloads = tuple(
            row.semantic_payload(expected_domain=expected_f105)
            for row in self.occurrences
        )
        if len(occurrence_payloads) != len(self.configuration.events):
            raise ExternalAuthorExtensionError("occurrence channel was truncated or expanded")
        if type(self.retail_mark_heads) is not tuple:
            raise TypeError("retail_mark_heads must be an exact tuple")
        if self.adapter_id == CSDI_ADAPTER_ID:
            if self.retail_mark_heads:
                raise ExternalAuthorExtensionError("CSDI adapter cannot carry Retail heads")
            heads_payloads: Tuple[Dict[str, Any], ...] = ()
        else:
            if len(self.retail_mark_heads) != len(self.occurrences):
                raise ExternalAuthorExtensionError("Retail structured heads are incomplete")
            heads_payloads = tuple(head.semantic_payload() for head in self.retail_mark_heads)
            if tuple(head.occurrence_serial for head in self.retail_mark_heads) != tuple(
                range(len(self.occurrences))
            ):
                raise ExternalAuthorExtensionError("Retail head serials differ")
            if tuple(head.event_sha256 for head in self.retail_mark_heads) != tuple(
                row.event_sha256 for row in self.occurrences
            ):
                raise ExternalAuthorExtensionError("Retail heads cross occurrence associations")
            for head, row in zip(self.retail_mark_heads, self.occurrences):
                head_coordinates = (
                    head.invoice_token,
                    head.cancellation,
                    head.stock_token,
                    head.description_present,
                    head.description_token,
                    head.source_civil_time,
                    head.quantity,
                    head.unit_price,
                    head.country_present,
                    head.country_token,
                )
                if head_coordinates != row.event.coordinates:
                    raise ExternalAuthorExtensionError(
                        "Retail structured heads differ from their bound occurrence event"
                    )
        payload = {
            "adapter_id": self.adapter_id,
            "b06_config_sha256": self.b06_config_sha256,
            "b06_domain_id": self.b06_domain_id,
            "component_scope": "AUTHOR_EXTENSION_OFFLINE_TRANSFORMATION_INTERFACE_ONLY",
            "configuration": configuration_payload,
            "context": context_payload,
            "event_count": len(occurrence_payloads),
            "f105_domain_id": self.f105_domain_id,
            "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
            "f144_semantics_sha256": F144_SEMANTICS_SHA256,
            "module_source_sha256": source_sha256,
            "occurrences": occurrence_payloads,
            "retail_mark_heads": heads_payloads,
            "training_executable_config_sha256": self.training_executable_config_sha256,
            "upstream_native_functionality_claimed": False,
            "upstream_package_executed": False,
        }
        if self.adapter_sha256 != _digest(
            "heterodiff-b12-external-author-adapter-v1", payload
        ):
            raise ExternalAuthorExtensionError("external author adapter digest differs")
        return payload


def _build_author_adapter(
    *,
    adapter_id: str,
    configuration: ExactConfiguration,
    module_source_sha256: str,
) -> ExternalAuthorAdapter:
    b06_domain, f105_domain, config_sha256, training_sha256 = _expected_identity(adapter_id)
    source_sha256 = _exact_sha256(
        module_source_sha256, name="module_source_sha256", nonzero=True
    )
    configuration_payload = _configuration_payload(
        configuration, expected_domain=f105_domain
    )
    context = _ENCODE_EXACT_CONTEXT(configuration)
    occurrences = _build_occurrence_channel(
        configuration, expected_domain=f105_domain
    )
    heads = (
        tuple(_retail_heads(row) for row in occurrences)
        if adapter_id == EDITPP_ADAPTER_ID
        else ()
    )
    payload = {
        "adapter_id": adapter_id,
        "b06_config_sha256": config_sha256,
        "b06_domain_id": b06_domain,
        "component_scope": "AUTHOR_EXTENSION_OFFLINE_TRANSFORMATION_INTERFACE_ONLY",
        "configuration": configuration_payload,
        "context": context.semantic_payload(),
        "event_count": len(occurrences),
        "f105_domain_id": f105_domain,
        "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
        "f144_semantics_sha256": F144_SEMANTICS_SHA256,
        "module_source_sha256": source_sha256,
        "occurrences": tuple(
            row.semantic_payload(expected_domain=f105_domain) for row in occurrences
        ),
        "retail_mark_heads": tuple(head.semantic_payload() for head in heads),
        "training_executable_config_sha256": training_sha256,
        "upstream_native_functionality_claimed": False,
        "upstream_package_executed": False,
    }
    result = ExternalAuthorAdapter(
        adapter_id=adapter_id,
        b06_domain_id=b06_domain,
        f105_domain_id=f105_domain,
        b06_config_sha256=config_sha256,
        training_executable_config_sha256=training_sha256,
        module_source_sha256=source_sha256,
        configuration=configuration,
        context=context,
        occurrences=occurrences,
        retail_mark_heads=heads,
        adapter_sha256=_digest("heterodiff-b12-external-author-adapter-v1", payload),
    )
    result.semantic_payload()
    return result


def build_csdi_author_adapter(
    *, configuration: ExactConfiguration, module_source_sha256: str
) -> ExternalAuthorAdapter:
    return _build_author_adapter(
        adapter_id=CSDI_ADAPTER_ID,
        configuration=configuration,
        module_source_sha256=module_source_sha256,
    )


def build_editpp_author_adapter(
    *, configuration: ExactConfiguration, module_source_sha256: str
) -> ExternalAuthorAdapter:
    return _build_author_adapter(
        adapter_id=EDITPP_ADAPTER_ID,
        configuration=configuration,
        module_source_sha256=module_source_sha256,
    )


@dataclass(frozen=True)
class PendingDrawSlot:
    """One deterministic slot; it contains no fabricated model output."""

    draw_ordinal: int
    slot_sha256: str
    status: str = DRAW_SLOT_STATUS
    generated_configuration_sha256: None = None

    def semantic_payload(
        self, *, adapter_id: str, interface_subject_sha256: str
    ) -> Dict[str, Any]:
        if type(self) is not PendingDrawSlot:
            raise TypeError("draw slot must have exact concrete type")
        ordinal = _exact_nonnegative_integer(self.draw_ordinal, name="draw_ordinal")
        if ordinal >= DRAW_COUNT:
            raise ExternalAuthorExtensionError("draw ordinal is outside exact 0..63")
        if self.status != DRAW_SLOT_STATUS or self.generated_configuration_sha256 is not None:
            raise ExternalAuthorExtensionError("pending draw slot falsely contains output")
        subject = _exact_sha256(
            interface_subject_sha256, name="interface_subject_sha256"
        )
        payload = {
            "adapter_id": adapter_id,
            "draw_ordinal": ordinal,
            "generated_configuration_sha256": None,
            "interface_subject_sha256": subject,
            "status": DRAW_SLOT_STATUS,
        }
        if self.slot_sha256 != _digest(
            "heterodiff-b12-external-author-extension-draw-slot-v1", payload
        ):
            raise ExternalAuthorExtensionError("draw-slot digest differs")
        return payload


@dataclass(frozen=True)
class FrozenConditioningInterface:
    """Occurrence-associated immutable subset mask plus exactly 64 draw slots."""

    adapter_id: str
    b06_config_sha256: str
    training_executable_config_sha256: str
    adapter_sha256: str
    context_encoding_sha256: str
    event_count: int
    observation_mask: Tuple[bool, ...]
    observed_occurrence_sha256s: Tuple[str, ...]
    mask_sha256: str
    interface_subject_sha256: str
    draw_slots: Tuple[PendingDrawSlot, ...]
    interface_sha256: str

    def semantic_payload(self, *, adapter: ExternalAuthorAdapter) -> Dict[str, Any]:
        if type(self) is not FrozenConditioningInterface:
            raise TypeError("conditioning interface must have exact concrete type")
        if type(adapter) is not ExternalAuthorAdapter:
            raise TypeError("adapter must have exact ExternalAuthorAdapter type")
        adapter.semantic_payload()
        if self.adapter_id != adapter.adapter_id:
            raise ExternalAuthorExtensionError("conditioning adapter identity differs")
        if self.b06_config_sha256 != adapter.b06_config_sha256:
            raise ExternalAuthorExtensionError("conditioning B06 config differs")
        if self.training_executable_config_sha256 != adapter.training_executable_config_sha256:
            raise ExternalAuthorExtensionError("conditioning training contract differs")
        if self.adapter_sha256 != adapter.adapter_sha256:
            raise ExternalAuthorExtensionError("conditioning adapter digest differs")
        if self.context_encoding_sha256 != adapter.context.encoding_sha256:
            raise ExternalAuthorExtensionError("conditioning 64D context differs")
        event_count = _exact_nonnegative_integer(self.event_count, name="event_count")
        if event_count != len(adapter.occurrences):
            raise ExternalAuthorExtensionError("conditioning event count differs")
        if type(self.observation_mask) is not tuple or len(self.observation_mask) != event_count:
            raise ExternalAuthorExtensionError("observation mask is not occurrence-complete")
        if any(type(value) is not bool for value in self.observation_mask):
            raise TypeError("observation mask values must be exact booleans")
        if type(self.observed_occurrence_sha256s) is not tuple:
            raise TypeError("observed occurrence roster must be an exact tuple")
        expected_observed = tuple(
            row.occurrence_sha256
            for row, observed in zip(adapter.occurrences, self.observation_mask)
            if observed
        )
        observed = tuple(
            _exact_sha256(value, name="observed occurrence digest")
            for value in self.observed_occurrence_sha256s
        )
        if observed != expected_observed:
            raise ExternalAuthorExtensionError("observation associations differ")
        mask_payload = {
            "adapter_sha256": adapter.adapter_sha256,
            "event_count": event_count,
            "observation_mask": self.observation_mask,
            "observed_occurrence_sha256s": observed,
        }
        if self.mask_sha256 != _digest(
            "heterodiff-b12-external-author-extension-observation-mask-v1",
            mask_payload,
        ):
            raise ExternalAuthorExtensionError("observation-mask digest differs")
        subject_payload = {
            "adapter_id": adapter.adapter_id,
            "adapter_sha256": adapter.adapter_sha256,
            "b06_config_sha256": adapter.b06_config_sha256,
            "context_dimension": PRIMARY_CONTEXT_DIMENSION,
            "context_encoding_sha256": adapter.context.encoding_sha256,
            "draw_count": DRAW_COUNT,
            "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
            "mask_sha256": self.mask_sha256,
            "training_executable_config_sha256": adapter.training_executable_config_sha256,
        }
        subject = _exact_sha256(
            self.interface_subject_sha256, name="interface_subject_sha256"
        )
        if subject != _digest(
            "heterodiff-b12-external-author-extension-interface-subject-v1",
            subject_payload,
        ):
            raise ExternalAuthorExtensionError("conditioning subject digest differs")
        if type(self.draw_slots) is not tuple or len(self.draw_slots) != DRAW_COUNT:
            raise ExternalAuthorExtensionError("draw-slot roster is not exact 64")
        if tuple(slot.draw_ordinal for slot in self.draw_slots) != tuple(range(DRAW_COUNT)):
            raise ExternalAuthorExtensionError("draw-slot ordinals are not exact 0..63")
        draw_payloads = tuple(
            slot.semantic_payload(
                adapter_id=adapter.adapter_id,
                interface_subject_sha256=subject,
            )
            for slot in self.draw_slots
        )
        payload = {
            "adapter_id": adapter.adapter_id,
            "adapter_sha256": adapter.adapter_sha256,
            "b06_config_sha256": adapter.b06_config_sha256,
            "context_dimension": PRIMARY_CONTEXT_DIMENSION,
            "context_encoding_sha256": adapter.context.encoding_sha256,
            "draw_count": DRAW_COUNT,
            "draw_slots": draw_payloads,
            "event_count": event_count,
            "interface_subject_sha256": subject,
            "mask_sha256": self.mask_sha256,
            "observation_mask": self.observation_mask,
            "observed_occurrence_sha256s": observed,
            "runtime_output_claimed": False,
            "training_executable_config_sha256": adapter.training_executable_config_sha256,
        }
        if self.interface_sha256 != _digest(
            "heterodiff-b12-external-author-extension-conditioning-interface-v1",
            payload,
        ):
            raise ExternalAuthorExtensionError("conditioning-interface digest differs")
        return payload


def _build_conditioning_interface(
    *, adapter: ExternalAuthorAdapter, observed_occurrence_serials: Tuple[int, ...]
) -> FrozenConditioningInterface:
    if type(adapter) is not ExternalAuthorAdapter:
        raise TypeError("adapter must have exact ExternalAuthorAdapter type")
    adapter.semantic_payload()
    if type(observed_occurrence_serials) is not tuple:
        raise TypeError("observed occurrence serials must be an exact tuple")
    if any(type(value) is not int for value in observed_occurrence_serials):
        raise TypeError("observed occurrence serials must be exact integers")
    if tuple(sorted(set(observed_occurrence_serials))) != observed_occurrence_serials:
        raise ExternalAuthorExtensionError(
            "observed occurrence serials must be strictly increasing and unique"
        )
    if any(value < 0 or value >= len(adapter.occurrences) for value in observed_occurrence_serials):
        raise ExternalAuthorExtensionError("observed occurrence serial is outside the roster")
    selected = frozenset(observed_occurrence_serials)
    mask = tuple(serial in selected for serial in range(len(adapter.occurrences)))
    observed = tuple(
        row.occurrence_sha256
        for row, is_observed in zip(adapter.occurrences, mask)
        if is_observed
    )
    mask_payload = {
        "adapter_sha256": adapter.adapter_sha256,
        "event_count": len(adapter.occurrences),
        "observation_mask": mask,
        "observed_occurrence_sha256s": observed,
    }
    mask_sha256 = _digest(
        "heterodiff-b12-external-author-extension-observation-mask-v1", mask_payload
    )
    subject_payload = {
        "adapter_id": adapter.adapter_id,
        "adapter_sha256": adapter.adapter_sha256,
        "b06_config_sha256": adapter.b06_config_sha256,
        "context_dimension": PRIMARY_CONTEXT_DIMENSION,
        "context_encoding_sha256": adapter.context.encoding_sha256,
        "draw_count": DRAW_COUNT,
        "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
        "mask_sha256": mask_sha256,
        "training_executable_config_sha256": adapter.training_executable_config_sha256,
    }
    subject_sha256 = _digest(
        "heterodiff-b12-external-author-extension-interface-subject-v1",
        subject_payload,
    )
    slots = []
    for ordinal in range(DRAW_COUNT):
        slot_payload = {
            "adapter_id": adapter.adapter_id,
            "draw_ordinal": ordinal,
            "generated_configuration_sha256": None,
            "interface_subject_sha256": subject_sha256,
            "status": DRAW_SLOT_STATUS,
        }
        slots.append(
            PendingDrawSlot(
                draw_ordinal=ordinal,
                slot_sha256=_digest(
                    "heterodiff-b12-external-author-extension-draw-slot-v1",
                    slot_payload,
                ),
            )
        )
    draw_slots = tuple(slots)
    payload = {
        "adapter_id": adapter.adapter_id,
        "adapter_sha256": adapter.adapter_sha256,
        "b06_config_sha256": adapter.b06_config_sha256,
        "context_dimension": PRIMARY_CONTEXT_DIMENSION,
        "context_encoding_sha256": adapter.context.encoding_sha256,
        "draw_count": DRAW_COUNT,
        "draw_slots": tuple(
            slot.semantic_payload(
                adapter_id=adapter.adapter_id,
                interface_subject_sha256=subject_sha256,
            )
            for slot in draw_slots
        ),
        "event_count": len(adapter.occurrences),
        "interface_subject_sha256": subject_sha256,
        "mask_sha256": mask_sha256,
        "observation_mask": mask,
        "observed_occurrence_sha256s": observed,
        "runtime_output_claimed": False,
        "training_executable_config_sha256": adapter.training_executable_config_sha256,
    }
    result = FrozenConditioningInterface(
        adapter_id=adapter.adapter_id,
        b06_config_sha256=adapter.b06_config_sha256,
        training_executable_config_sha256=adapter.training_executable_config_sha256,
        adapter_sha256=adapter.adapter_sha256,
        context_encoding_sha256=adapter.context.encoding_sha256,
        event_count=len(adapter.occurrences),
        observation_mask=mask,
        observed_occurrence_sha256s=observed,
        mask_sha256=mask_sha256,
        interface_subject_sha256=subject_sha256,
        draw_slots=draw_slots,
        interface_sha256=_digest(
            "heterodiff-b12-external-author-extension-conditioning-interface-v1",
            payload,
        ),
    )
    result.semantic_payload(adapter=adapter)
    return result


def build_csdi_conditioning_interface(
    *, adapter: ExternalAuthorAdapter, observed_occurrence_serials: Tuple[int, ...]
) -> FrozenConditioningInterface:
    if type(adapter) is not ExternalAuthorAdapter or adapter.adapter_id != CSDI_ADAPTER_ID:
        raise ExternalAuthorExtensionError("CSDI conditioning requires the exact CSDI adapter")
    return _build_conditioning_interface(
        adapter=adapter,
        observed_occurrence_serials=observed_occurrence_serials,
    )


def build_editpp_conditioning_interface(
    *, adapter: ExternalAuthorAdapter, observed_occurrence_serials: Tuple[int, ...]
) -> FrozenConditioningInterface:
    if type(adapter) is not ExternalAuthorAdapter or adapter.adapter_id != EDITPP_ADAPTER_ID:
        raise ExternalAuthorExtensionError("EditPP conditioning requires the exact EditPP adapter")
    return _build_conditioning_interface(
        adapter=adapter,
        observed_occurrence_serials=observed_occurrence_serials,
    )


@dataclass(frozen=True)
class AuthorExtensionImplementationRecord:
    """One source-bound claim limited to offline component implementation."""

    predicate_id: str
    adapter_id: str
    b06_domain_id: str
    b06_config_sha256: str
    training_executable_config_sha256: str
    ordinal_within_adapter: int
    extension_id: str
    entrypoint: str
    module_source_sha256: str
    status: str
    claim_scope: str
    upstream_native_functionality_claimed: bool
    upstream_execution_claimed: bool
    domain_scale_runtime_qualified: bool
    production_receipt_claimed: bool
    record_sha256: str

    def semantic_payload(self) -> Dict[str, Any]:
        if type(self) is not AuthorExtensionImplementationRecord:
            raise TypeError("implementation record must have exact concrete type")
        b06_domain, _, config_sha256, training_sha256 = _expected_identity(self.adapter_id)
        ordinal = _exact_nonnegative_integer(
            self.ordinal_within_adapter, name="ordinal_within_adapter"
        )
        if ordinal not in range(1, 5):
            raise ExternalAuthorExtensionError("extension ordinal is outside 1..4")
        prefix = "CSDI" if self.adapter_id == CSDI_ADAPTER_ID else "EDITPP"
        if self.predicate_id != f"{prefix}_AUTHOR_EXTENSION_{ordinal}":
            raise ExternalAuthorExtensionError("extension predicate identity differs")
        if self.extension_id != _EXPECTED_EXTENSIONS[self.adapter_id][ordinal - 1]:
            raise ExternalAuthorExtensionError("extension identity differs")
        if self.entrypoint != _ENTRYPOINTS[(self.adapter_id, ordinal)]:
            raise ExternalAuthorExtensionError("extension entrypoint differs")
        if self.b06_domain_id != b06_domain or self.b06_config_sha256 != config_sha256:
            raise ExternalAuthorExtensionError("extension B06 binding differs")
        if self.training_executable_config_sha256 != training_sha256:
            raise ExternalAuthorExtensionError("extension training binding differs")
        source = _exact_sha256(
            self.module_source_sha256, name="module_source_sha256", nonzero=True
        )
        if self.status != COMPONENT_STATUS:
            raise ExternalAuthorExtensionError("component status differs")
        if self.claim_scope != "COMPONENT_IMPLEMENTATION_ONLY":
            raise ExternalAuthorExtensionError("component claim scope was widened")
        booleans = (
            self.upstream_native_functionality_claimed,
            self.upstream_execution_claimed,
            self.domain_scale_runtime_qualified,
            self.production_receipt_claimed,
        )
        if any(type(value) is not bool or value for value in booleans):
            raise ExternalAuthorExtensionError("component record contains a forbidden claim")
        payload = {
            "adapter_id": self.adapter_id,
            "b06_config_sha256": self.b06_config_sha256,
            "b06_domain_id": self.b06_domain_id,
            "claim_scope": self.claim_scope,
            "domain_scale_runtime_qualified": False,
            "entrypoint": (
                "heterodiff.evaluation.b12_external_author_extension_components:"
                + self.entrypoint
            ),
            "extension_id": self.extension_id,
            "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
            "f144_semantics_sha256": F144_SEMANTICS_SHA256,
            "module_source_sha256": source,
            "ordinal_within_adapter": ordinal,
            "predicate_id": self.predicate_id,
            "production_receipt_claimed": False,
            "status": self.status,
            "training_executable_config_sha256": self.training_executable_config_sha256,
            "upstream_execution_claimed": False,
            "upstream_native_functionality_claimed": False,
        }
        if self.record_sha256 != _digest(
            "heterodiff-b12-author-extension-implementation-record-v1", payload
        ):
            raise ExternalAuthorExtensionError("implementation record digest differs")
        return payload


def build_author_extension_implementation_manifest(
    *, module_source_sha256: str
) -> Tuple[AuthorExtensionImplementationRecord, ...]:
    source = _exact_sha256(
        module_source_sha256, name="module_source_sha256", nonzero=True
    )
    records = []
    for adapter_id in (CSDI_ADAPTER_ID, EDITPP_ADAPTER_ID):
        b06_domain, _, config_sha256, training_sha256 = _expected_identity(adapter_id)
        prefix = "CSDI" if adapter_id == CSDI_ADAPTER_ID else "EDITPP"
        for ordinal, extension_id in enumerate(_EXPECTED_EXTENSIONS[adapter_id], start=1):
            payload = {
                "adapter_id": adapter_id,
                "b06_config_sha256": config_sha256,
                "b06_domain_id": b06_domain,
                "claim_scope": "COMPONENT_IMPLEMENTATION_ONLY",
                "domain_scale_runtime_qualified": False,
                "entrypoint": (
                    "heterodiff.evaluation.b12_external_author_extension_components:"
                    + _ENTRYPOINTS[(adapter_id, ordinal)]
                ),
                "extension_id": extension_id,
                "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
                "f144_semantics_sha256": F144_SEMANTICS_SHA256,
                "module_source_sha256": source,
                "ordinal_within_adapter": ordinal,
                "predicate_id": f"{prefix}_AUTHOR_EXTENSION_{ordinal}",
                "production_receipt_claimed": False,
                "status": COMPONENT_STATUS,
                "training_executable_config_sha256": training_sha256,
                "upstream_execution_claimed": False,
                "upstream_native_functionality_claimed": False,
            }
            record = AuthorExtensionImplementationRecord(
                predicate_id=f"{prefix}_AUTHOR_EXTENSION_{ordinal}",
                adapter_id=adapter_id,
                b06_domain_id=b06_domain,
                b06_config_sha256=config_sha256,
                training_executable_config_sha256=training_sha256,
                ordinal_within_adapter=ordinal,
                extension_id=extension_id,
                entrypoint=_ENTRYPOINTS[(adapter_id, ordinal)],
                module_source_sha256=source,
                status=COMPONENT_STATUS,
                claim_scope="COMPONENT_IMPLEMENTATION_ONLY",
                upstream_native_functionality_claimed=False,
                upstream_execution_claimed=False,
                domain_scale_runtime_qualified=False,
                production_receipt_claimed=False,
                record_sha256=_digest(
                    "heterodiff-b12-author-extension-implementation-record-v1",
                    payload,
                ),
            )
            record.semantic_payload()
            records.append(record)
    result = tuple(records)
    if len(result) != 8 or len({record.record_sha256 for record in result}) != 8:
        raise RuntimeError("author-extension implementation manifest is not exact eight")
    return result


def qualification_fixture_configurations() -> Tuple[ExactConfiguration, ExactConfiguration]:
    """Return small valid duplicate-bearing fixtures; no external data are read."""

    physio_duplicate = physionet_event_from_decimal_token(
        elapsed_minutes=0,
        parameter="HR",
        value_text="-1",
    )
    physio_distinct = physionet_event_from_decimal_token(
        elapsed_minutes=60,
        parameter="Albumin",
        value_text="2.5",
    )
    physionet = ExactConfiguration(
        PHYSIONET_DOMAIN_ID,
        (physio_duplicate, physio_duplicate, physio_distinct),
    )
    retail_duplicate = retail_event_from_decimal_token(
        invoice_no="123456",
        stock_code="SKU-1",
        description="",
        quantity=2,
        invoice_calendar=(2010, 1, 2, 3, 4, 5, 6),
        unit_price_text="1.25",
        country=None,
    )
    retail_distinct = retail_event_from_decimal_token(
        invoice_no="C654321",
        stock_code="SKU-2",
        description=None,
        quantity=-1,
        invoice_calendar=(2011, 2, 3, 4, 5, 6, 7),
        unit_price_text="0",
        country="GB",
    )
    retail = ExactConfiguration(
        RETAIL_DOMAIN_ID,
        (retail_duplicate, retail_duplicate, retail_distinct),
    )
    return retail, physionet


def candidate_semantics(*, module_source_sha256: str) -> Dict[str, Any]:
    """Return the compact deterministic semantics used by the machine record."""

    source = _exact_sha256(
        module_source_sha256, name="module_source_sha256", nonzero=True
    )
    retail_configuration, physionet_configuration = qualification_fixture_configurations()
    csdi = build_csdi_author_adapter(
        configuration=physionet_configuration,
        module_source_sha256=source,
    )
    editpp = build_editpp_author_adapter(
        configuration=retail_configuration,
        module_source_sha256=source,
    )
    if decode_csdi_event_multiset(csdi.occurrences) != physionet_configuration:
        raise RuntimeError("qualification CSDI decoder does not round-trip")
    csdi_interface = build_csdi_conditioning_interface(
        adapter=csdi,
        observed_occurrence_serials=(0, 2),
    )
    editpp_interface = build_editpp_conditioning_interface(
        adapter=editpp,
        observed_occurrence_serials=(1,),
    )
    records = build_author_extension_implementation_manifest(
        module_source_sha256=source
    )
    return {
        "adapter_records": (
            {
                "adapter_id": csdi.adapter_id,
                "adapter_sha256": csdi.adapter_sha256,
                "b06_config_sha256": csdi.b06_config_sha256,
                "context_encoding_sha256": csdi.context.encoding_sha256,
                "event_count": len(csdi.occurrences),
                "f105_coordinate_dimension": 112,
                "interface_sha256": csdi_interface.interface_sha256,
                "training_executable_config_sha256": csdi.training_executable_config_sha256,
            },
            {
                "adapter_id": editpp.adapter_id,
                "adapter_sha256": editpp.adapter_sha256,
                "b06_config_sha256": editpp.b06_config_sha256,
                "context_encoding_sha256": editpp.context.encoding_sha256,
                "event_count": len(editpp.occurrences),
                "f105_coordinate_dimension": 10,
                "interface_sha256": editpp_interface.interface_sha256,
                "training_executable_config_sha256": editpp.training_executable_config_sha256,
            },
        ),
        "component_implementation_predicate_ids": tuple(
            record.predicate_id for record in records
        ),
        "draw_count_per_interface": DRAW_COUNT,
        "effects": {
            "blocker_delta": 0,
            "field_delta": 0,
            "formal_test_delta": 0,
            "result_delta": 0,
            "science_delta": 0,
            "timetable_task_delta": 0,
            "tracker_edited": False,
        },
        "f139_f144_f147_plan_semantics_sha256": TRAINING_PLAN_SEMANTICS_SHA256,
        "f144_semantics_sha256": F144_SEMANTICS_SHA256,
        "implementation_record_sha256s": tuple(
            record.record_sha256 for record in records
        ),
        "nonclaims": {
            "b12_closed": False,
            "data_accessed": False,
            "domain_scale_runtime_qualified": False,
            "entropy_used": False,
            "formal_test_executed_or_closed": False,
            "independent_review_completed": False,
            "network_used": False,
            "production_receipt_claimed": False,
            "scientific_training_or_inference_performed": False,
            "upstream_native_functionality_claimed": False,
            "upstream_packages_executed": False,
        },
        "primary_context_dimension": PRIMARY_CONTEXT_DIMENSION,
        "schema": SCHEMA_VERSION,
        "state": STATE,
    }


__all__ = [
    "AuthorExtensionImplementationRecord",
    "COMPONENT_STATUS",
    "CSDI_ADAPTER_ID",
    "DRAW_COUNT",
    "EDITPP_ADAPTER_ID",
    "ExternalAuthorAdapter",
    "ExternalAuthorExtensionError",
    "FrozenConditioningInterface",
    "OccurrenceChannelRow",
    "PendingDrawSlot",
    "PRIMARY_CONTEXT_DIMENSION",
    "RetailStructuredMarkHeads",
    "SCHEMA_VERSION",
    "STATE",
    "build_author_extension_implementation_manifest",
    "build_csdi_author_adapter",
    "build_csdi_conditioning_interface",
    "build_editpp_author_adapter",
    "build_editpp_conditioning_interface",
    "candidate_semantics",
    "decode_csdi_event_multiset",
    "qualification_fixture_configurations",
]
