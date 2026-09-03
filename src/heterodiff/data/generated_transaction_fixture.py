"""Generated transaction-style atomic-counting fixtures.

The fixtures in this module are deliberately synthetic.  They exercise a
transaction-shaped event representation without importing an official retail
dataset or making an empirical claim.  Each source contains exactly one
invoice.  The invoice is the sample identity and its customer is the natural
group identity.

The parser is byte bounded and fail closed.  It preserves one event occurrence
per data row, including exact duplicate rows, and keeps source line information
only in a private provenance object.  Semantic reconstruction is a canonical
row *multiset*: raw CSV ordering, quoting, and decimal spelling are not part of
that semantic claim.
"""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import io
import math
import re
from typing import Dict, Optional, Tuple

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    MultiplicityMode,
    ObservationPattern,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)

from .atomic_counting_grid import AtomicCountingGridTensor


R_ACG_1_ID = "R-ACG-1"
R_ACG_1_A_ID = "R-ACG-1-A"
R_ACG_1_B_ID = "R-ACG-1-B"
R_ACG_1_A_INVOICE_ID = "invoice-a"
R_ACG_1_B_INVOICE_ID = "invoice-b"
R_ACG_1_CUSTOMER_ID = "customer-shared"
R_ACG_1_SPLIT = "train"

TRANSACTION_SOURCE_FORMAT = "generated-transaction-utf8-lf-csv-v1"
TRANSACTION_SCHEMA_VERSION = "generated-transaction-counting-fixture-v1"
TRANSACTION_EVENT_ID_NAMESPACE = "generated-transaction-row"
TRANSACTION_HEADER = (
    "Invoice",
    "Customer",
    "TimeIndex",
    "Product",
    "Cancellation",
    "Quantity",
    "UnitPrice",
)
TRANSACTION_HEADER_TEXT = ",".join(TRANSACTION_HEADER)
TRANSACTION_PRODUCT_TOKENS = ("sku-a", "sku-b")
TRANSACTION_TIME_INDICES = (5, 7)


class CancellationState(str, Enum):
    """Explicit transaction state; it is never inferred from quantity."""

    ACTIVE = "active"
    CANCELLED = "cancelled"


TRANSACTION_CANCELLATION_STATES = tuple(
    sorted(state.value for state in CancellationState)
)
TRANSACTION_TYPE_VOCABULARY = tuple(
    sorted(
        (product, cancellation)
        for product in TRANSACTION_PRODUCT_TOKENS
        for cancellation in TRANSACTION_CANCELLATION_STATES
    )
)
TRANSACTION_TYPE_IDS = {
    pair: type_id for type_id, pair in enumerate(TRANSACTION_TYPE_VOCABULARY)
}


R_ACG_1_A_TEXT = (
    TRANSACTION_HEADER_TEXT
    + "\n"
    + "invoice-a,customer-shared,5,sku-a,active,2,3.50\n"
    + "invoice-a,customer-shared,5,sku-a,active,2,3.50\n"
    + "invoice-a,customer-shared,5,sku-b,cancelled,1,4.25\n"
)
R_ACG_1_B_TEXT = (
    TRANSACTION_HEADER_TEXT
    + "\n"
    + "invoice-b,customer-shared,7,sku-a,cancelled,-2,3.50\n"
    + "invoice-b,customer-shared,7,sku-b,active,-1,4.25\n"
)
R_ACG_1_A_BYTES = R_ACG_1_A_TEXT.encode("utf-8")
R_ACG_1_B_BYTES = R_ACG_1_B_TEXT.encode("utf-8")
R_ACG_1_A_SHA256 = (
    "9f11c4b120f42df3cf35bd485a405c56dbceba6177911143b452b17932a23584"
)
R_ACG_1_B_SHA256 = (
    "25dd1cb8c9979c3ea6db4563e171e53c691c00650566b24d8a62342bc023673d"
)


class GeneratedTransactionFixtureError(ValueError):
    """A generated transaction source violates the frozen semantic policy."""


class GeneratedTransactionResourceError(GeneratedTransactionFixtureError):
    """A source would exceed a predeclared resource ceiling."""


def _exact_positive_int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("{} must be an exact integer".format(name))
    if value <= 0:
        raise ValueError("{} must be positive".format(name))
    return value


@dataclass(frozen=True)
class TransactionFixtureResourceLimits:
    """Limits checked before parsing, allocation, or partial publication."""

    maximum_source_bytes: int
    maximum_data_rows: int
    maximum_semantic_occurrences: int
    maximum_atomic_time_positions: int
    maximum_declared_event_types: int
    maximum_occurrences_per_cell: int
    maximum_mark_scalar_dimensions_per_occurrence: int

    def __post_init__(self) -> None:
        for name in (
            "maximum_source_bytes",
            "maximum_data_rows",
            "maximum_semantic_occurrences",
            "maximum_atomic_time_positions",
            "maximum_declared_event_types",
            "maximum_occurrences_per_cell",
            "maximum_mark_scalar_dimensions_per_occurrence",
        ):
            object.__setattr__(
                self,
                name,
                _exact_positive_int(getattr(self, name), name=name),
            )
        if self.maximum_semantic_occurrences > self.maximum_data_rows:
            raise ValueError(
                "semantic-occurrence ceiling cannot exceed the data-row ceiling"
            )
        if self.maximum_occurrences_per_cell > self.maximum_semantic_occurrences:
            raise ValueError(
                "per-cell ceiling cannot exceed the semantic-occurrence ceiling"
            )

    def as_dict(self) -> Dict[str, int]:
        return {
            name: getattr(self, name)
            for name in (
                "maximum_source_bytes",
                "maximum_data_rows",
                "maximum_semantic_occurrences",
                "maximum_atomic_time_positions",
                "maximum_declared_event_types",
                "maximum_occurrences_per_cell",
                "maximum_mark_scalar_dimensions_per_occurrence",
            )
        }


R_ACG_1_RESOURCE_LIMITS = TransactionFixtureResourceLimits(
    maximum_source_bytes=512,
    maximum_data_rows=8,
    maximum_semantic_occurrences=8,
    maximum_atomic_time_positions=2,
    maximum_declared_event_types=4,
    maximum_occurrences_per_cell=2,
    maximum_mark_scalar_dimensions_per_occurrence=2,
)


def _snapshot_limits(value: object) -> TransactionFixtureResourceLimits:
    if type(value) is not TransactionFixtureResourceLimits:
        raise TypeError("limits must be an exact TransactionFixtureResourceLimits")
    return TransactionFixtureResourceLimits(
        maximum_source_bytes=value.maximum_source_bytes,
        maximum_data_rows=value.maximum_data_rows,
        maximum_semantic_occurrences=value.maximum_semantic_occurrences,
        maximum_atomic_time_positions=value.maximum_atomic_time_positions,
        maximum_declared_event_types=value.maximum_declared_event_types,
        maximum_occurrences_per_cell=value.maximum_occurrences_per_cell,
        maximum_mark_scalar_dimensions_per_occurrence=(
            value.maximum_mark_scalar_dimensions_per_occurrence
        ),
    )


_PRIVATE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_TIME_INDEX_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
_SPLITS = frozenset(("train", "validation", "test"))
_MAX_PRIVATE_ID_BYTES = 128


def _private_id(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact string".format(name))
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise GeneratedTransactionFixtureError(
            "{} must contain only ASCII".format(name)
        ) from exc
    if (
        not encoded
        or len(encoded) > _MAX_PRIVATE_ID_BYTES
        or _PRIVATE_ID_RE.fullmatch(value) is None
    ):
        raise GeneratedTransactionFixtureError(
            "{} is not a canonical generated identifier".format(name)
        )
    return value


def _fixture_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("fixture_id must be an exact string")
    if not value or value != value.strip() or any(
        character in value for character in ("\x00", "\r", "\n")
    ):
        raise GeneratedTransactionFixtureError(
            "fixture_id must be nonempty, trimmed, and single-line"
        )
    return value


def _source_split(value: object) -> str:
    if type(value) is not str or value not in _SPLITS:
        raise GeneratedTransactionFixtureError(
            "source_split must be exactly train, validation, or test"
        )
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GeneratedTransactionFixtureError(
            "{} must be a lowercase SHA-256 digest".format(name)
        )
    return value


def _raw_cell(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact string".format(name))
    if not value or value != value.strip() or any(
        character in value for character in ("\x00", "\r", "\n")
    ):
        raise GeneratedTransactionFixtureError(
            "{} must be nonempty, trimmed, and single-line".format(name)
        )
    return value


def _parse_time_index(text: str) -> int:
    _raw_cell(text, name="TimeIndex")
    if _TIME_INDEX_RE.fullmatch(text) is None:
        raise GeneratedTransactionFixtureError(
            "TimeIndex must be a canonical nonnegative decimal integer"
        )
    value = int(text)
    if value not in TRANSACTION_TIME_INDICES:
        raise GeneratedTransactionFixtureError(
            "TimeIndex is outside the frozen atomic time vocabulary"
        )
    return value


def _parse_decimal(text: str, *, name: str) -> Tuple[Decimal, float]:
    _raw_cell(text, name=name)
    try:
        decimal_value = Decimal(text)
    except InvalidOperation as exc:
        raise GeneratedTransactionFixtureError(
            "{} must be a decimal number".format(name)
        ) from exc
    if not decimal_value.is_finite():
        raise GeneratedTransactionFixtureError(
            "{} must be a finite decimal number".format(name)
        )
    try:
        float_value = float(decimal_value)
    except (OverflowError, ValueError) as exc:
        raise GeneratedTransactionFixtureError(
            "{} cannot be represented as binary64".format(name)
        ) from exc
    if not math.isfinite(float_value):
        raise GeneratedTransactionFixtureError(
            "{} cannot be represented as finite binary64".format(name)
        )
    if decimal_value != 0 and float_value == 0.0:
        raise GeneratedTransactionFixtureError(
            "{} underflows the binary64 event representation".format(name)
        )
    if float_value == 0.0:
        float_value = 0.0
    if Decimal.from_float(float_value) != decimal_value:
        raise GeneratedTransactionFixtureError(
            "{} is not exactly representable in the binary64 event state".format(
                name
            )
        )
    return decimal_value, float_value


def _canonical_decimal_text(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise TypeError("canonical decimal values must be finite Decimal instances")
    if value == 0:
        return "0"
    normalized = value.normalize()
    # All admitted nonzero values survive finite binary64 conversion, bounding
    # the fixed-point expansion to a small deterministic string.
    return format(normalized, "f")


@dataclass(frozen=True)
class TransactionSemanticRow:
    """Raw-format-independent meaning of one transaction line item."""

    invoice_id: str
    customer_id: str
    time_index: int
    product_token: str
    cancellation_state: CancellationState
    quantity: Decimal
    unit_price: Decimal

    def __post_init__(self) -> None:
        _private_id(self.invoice_id, name="invoice_id")
        _private_id(self.customer_id, name="customer_id")
        if type(self.time_index) is not int or self.time_index not in TRANSACTION_TIME_INDICES:
            raise GeneratedTransactionFixtureError(
                "semantic time_index is outside the frozen atomic vocabulary"
            )
        if type(self.product_token) is not str or self.product_token not in (
            TRANSACTION_PRODUCT_TOKENS
        ):
            raise GeneratedTransactionFixtureError(
                "semantic product_token is outside the frozen vocabulary"
            )
        if type(self.cancellation_state) is not CancellationState:
            raise TypeError("cancellation_state must be an exact CancellationState")
        if type(self.quantity) is not Decimal or not self.quantity.is_finite():
            raise TypeError("quantity must be a finite exact Decimal")
        if type(self.unit_price) is not Decimal or not self.unit_price.is_finite():
            raise TypeError("unit_price must be a finite exact Decimal")
        if self.unit_price <= 0:
            raise GeneratedTransactionFixtureError("unit_price must be strictly positive")

    @property
    def type_id(self) -> int:
        return TRANSACTION_TYPE_IDS[
            (self.product_token, self.cancellation_state.value)
        ]

    def ordered_fields(self) -> Tuple[Tuple[str, object], ...]:
        """Return the canonical seven-field semantic record."""

        return (
            ("Invoice", self.invoice_id),
            ("Customer", self.customer_id),
            ("TimeIndex", self.time_index),
            ("Product", self.product_token),
            ("Cancellation", self.cancellation_state.value),
            ("Quantity", _canonical_decimal_text(self.quantity)),
            ("UnitPrice", _canonical_decimal_text(self.unit_price)),
        )

    def sort_key(self) -> Tuple[object, ...]:
        return tuple(value for _, value in self.ordered_fields())


@dataclass(frozen=True)
class TransactionSourceRow:
    """One parsed row with private physical-line provenance."""

    line_number: int
    source_sha256: str
    raw_cells: Tuple[str, ...]
    semantic: TransactionSemanticRow
    quantity_binary64: float
    unit_price_binary64: float

    def __post_init__(self) -> None:
        if type(self.line_number) is not int or self.line_number < 2:
            raise GeneratedTransactionFixtureError(
                "line_number must be an exact integer at or after line two"
            )
        _sha256(self.source_sha256, name="source_sha256")
        if type(self.raw_cells) is not tuple or len(self.raw_cells) != len(
            TRANSACTION_HEADER
        ):
            raise TypeError("raw_cells must be an exact seven-cell tuple")
        for name, value in zip(TRANSACTION_HEADER, self.raw_cells):
            _raw_cell(value, name=name)
        if type(self.semantic) is not TransactionSemanticRow:
            raise TypeError("semantic must be an exact TransactionSemanticRow")
        raw_quantity, raw_quantity_float = _parse_decimal(
            self.raw_cells[5], name="Quantity"
        )
        raw_price, raw_price_float = _parse_decimal(
            self.raw_cells[6], name="UnitPrice"
        )
        try:
            raw_cancellation = CancellationState(self.raw_cells[4])
        except ValueError as exc:
            raise GeneratedTransactionFixtureError(
                "raw cancellation is outside the explicit frozen vocabulary"
            ) from exc
        if (
            self.raw_cells[0] != self.semantic.invoice_id
            or self.raw_cells[1] != self.semantic.customer_id
            or _parse_time_index(self.raw_cells[2]) != self.semantic.time_index
            or self.raw_cells[3] != self.semantic.product_token
            or raw_cancellation is not self.semantic.cancellation_state
            or raw_quantity != self.semantic.quantity
            or raw_price != self.semantic.unit_price
        ):
            raise GeneratedTransactionFixtureError(
                "raw cells disagree with their semantic transaction row"
            )
        for name, value in (
            ("quantity_binary64", self.quantity_binary64),
            ("unit_price_binary64", self.unit_price_binary64),
        ):
            if type(value) is not float or not math.isfinite(value):
                raise TypeError("{} must be a finite exact float".format(name))
        if self.unit_price_binary64 <= 0.0:
            raise GeneratedTransactionFixtureError(
                "unit_price binary64 value must be strictly positive"
            )
        if self.quantity_binary64 != float(self.semantic.quantity):
            raise GeneratedTransactionFixtureError(
                "quantity binary64 value disagrees with its Decimal source"
            )
        if self.unit_price_binary64 != float(self.semantic.unit_price):
            raise GeneratedTransactionFixtureError(
                "unit_price binary64 value disagrees with its Decimal source"
            )
        if (
            self.quantity_binary64 != raw_quantity_float
            or self.unit_price_binary64 != raw_price_float
        ):
            raise GeneratedTransactionFixtureError(
                "binary64 marks disagree with their exact raw decimal cells"
            )

    @property
    def event_id(self) -> Tuple[str, str, int]:
        return (
            TRANSACTION_EVENT_ID_NAMESPACE,
            self.source_sha256,
            self.line_number,
        )


@dataclass(frozen=True)
class TransactionFixturePrivateProvenance:
    """Private source rows and their canonical event alignment."""

    source_rows: Tuple[TransactionSourceRow, ...]
    event_rows: Tuple[TransactionSourceRow, ...]

    def __post_init__(self) -> None:
        if type(self.source_rows) is not tuple or not self.source_rows:
            raise TypeError("source_rows must be a nonempty exact tuple")
        if type(self.event_rows) is not tuple:
            raise TypeError("event_rows must be an exact tuple")
        if any(type(row) is not TransactionSourceRow for row in self.source_rows):
            raise TypeError("source_rows must contain exact TransactionSourceRow values")
        if any(type(row) is not TransactionSourceRow for row in self.event_rows):
            raise TypeError("event_rows must contain exact TransactionSourceRow values")
        if tuple(row.line_number for row in self.source_rows) != tuple(
            range(2, 2 + len(self.source_rows))
        ):
            raise GeneratedTransactionFixtureError(
                "source row provenance must cover consecutive physical data lines"
            )
        source_ids = tuple(row.event_id for row in self.source_rows)
        event_ids = tuple(row.event_id for row in self.event_rows)
        if len(set(source_ids)) != len(source_ids):
            raise GeneratedTransactionFixtureError("source row event IDs must be unique")
        if len(event_ids) != len(source_ids) or set(event_ids) != set(source_ids):
            raise GeneratedTransactionFixtureError(
                "event_rows must be a permutation of every source row"
            )
        source_by_id = {row.event_id: row for row in self.source_rows}
        if any(row != source_by_id[row.event_id] for row in self.event_rows):
            raise GeneratedTransactionFixtureError(
                "event_rows must contain the exact parsed source rows"
            )

    def semantic_row_multiset(
        self,
    ) -> Tuple[Tuple[Tuple[str, object], ...], ...]:
        """Return a canonical multiset, retaining repeated semantic rows."""

        ordered = sorted(
            (row.semantic for row in self.source_rows),
            key=TransactionSemanticRow.sort_key,
        )
        return tuple(row.ordered_fields() for row in ordered)


@dataclass(frozen=True)
class TransactionFixturePartitionDescription:
    """Adapter-independent description of one natural sample/group split."""

    fixture_id: str
    sample_id: str
    group_id: str
    split: str
    source_sha256: str

    def __post_init__(self) -> None:
        _fixture_id(self.fixture_id)
        _private_id(self.sample_id, name="sample_id")
        _private_id(self.group_id, name="group_id")
        _source_split(self.split)
        _sha256(self.source_sha256, name="source_sha256")


R_ACG_1_CORPUS_SPLIT_DESCRIPTION = (
    TransactionFixturePartitionDescription(
        R_ACG_1_A_ID,
        R_ACG_1_A_INVOICE_ID,
        R_ACG_1_CUSTOMER_ID,
        R_ACG_1_SPLIT,
        R_ACG_1_A_SHA256,
    ),
    TransactionFixturePartitionDescription(
        R_ACG_1_B_ID,
        R_ACG_1_B_INVOICE_ID,
        R_ACG_1_CUSTOMER_ID,
        R_ACG_1_SPLIT,
        R_ACG_1_B_SHA256,
    ),
)


def _transaction_schema(limits: TransactionFixtureResourceLimits) -> FeatureSchema:
    limits = _snapshot_limits(limits)
    if len(TRANSACTION_TIME_INDICES) > limits.maximum_atomic_time_positions:
        raise GeneratedTransactionResourceError(
            "frozen atomic time vocabulary exceeds its predeclared ceiling"
        )
    if len(TRANSACTION_TYPE_VOCABULARY) > limits.maximum_declared_event_types:
        raise GeneratedTransactionResourceError(
            "frozen product/cancellation vocabulary exceeds its ceiling"
        )
    if 2 > limits.maximum_mark_scalar_dimensions_per_occurrence:
        raise GeneratedTransactionResourceError(
            "transaction mark dimension exceeds its predeclared ceiling"
        )
    quantity = ContinuousField(
        "quantity",
        support=SupportKind.REAL,
        unit="item-count",
    )
    unit_price = ContinuousField(
        "unit_price",
        support=SupportKind.POSITIVE,
        unit="currency-unit/item",
    )
    return FeatureSchema(
        event_types=tuple(
            EventTypeSchema(
                type_id,
                "{}__{}".format(product, cancellation),
                (quantity, unit_price),
            )
            for type_id, (product, cancellation) in enumerate(
                TRANSACTION_TYPE_VOCABULARY
            )
        ),
        horizon=float(max(TRANSACTION_TIME_INDICES)),
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic(
            tuple(float(value) for value in TRANSACTION_TIME_INDICES),
            (1.0,) * len(TRANSACTION_TIME_INDICES),
        ),
        allow_simultaneous=True,
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
        version=TRANSACTION_SCHEMA_VERSION,
    )


def transaction_fixture_schema(
    limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS,
) -> FeatureSchema:
    """Return the exact generated transaction native schema."""

    return _transaction_schema(limits)


def _preflight_source(
    source_bytes: object,
    *,
    limits: TransactionFixtureResourceLimits,
    expected_sha256: Optional[str],
) -> Tuple[bytes, str]:
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    limits = _snapshot_limits(limits)
    if len(source_bytes) > limits.maximum_source_bytes:
        raise GeneratedTransactionResourceError(
            "source byte length {} exceeds predeclared ceiling {}".format(
                len(source_bytes), limits.maximum_source_bytes
            )
        )
    digest = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha256 is not None:
        expected = _sha256(expected_sha256, name="expected_sha256")
        if digest != expected:
            raise GeneratedTransactionFixtureError(
                "source SHA-256 mismatch: expected {}, got {}".format(
                    expected, digest
                )
            )
    return source_bytes, digest


def parse_transaction_fixture_source(
    source_bytes: bytes,
    *,
    limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS,
    expected_sha256: Optional[str] = None,
) -> Tuple[TransactionSourceRow, ...]:
    """Parse one bounded, single-invoice generated transaction source."""

    limits = _snapshot_limits(limits)
    source, source_sha256 = _preflight_source(
        source_bytes,
        limits=limits,
        expected_sha256=expected_sha256,
    )
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GeneratedTransactionFixtureError(
            "transaction source must be strict UTF-8"
        ) from exc
    if text.startswith("\ufeff"):
        raise GeneratedTransactionFixtureError("transaction source must not use a BOM")
    if "\r" in text:
        raise GeneratedTransactionFixtureError(
            "transaction source requires LF line endings"
        )
    if not text.endswith("\n"):
        raise GeneratedTransactionFixtureError(
            "transaction source requires a final LF"
        )
    first_lf = text.find("\n")
    if text[:first_lf] != TRANSACTION_HEADER_TEXT:
        raise GeneratedTransactionFixtureError(
            "transaction source header does not match the exact schema"
        )

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader)
        if tuple(header) != TRANSACTION_HEADER:
            raise GeneratedTransactionFixtureError(
                "transaction source header does not match the exact schema"
            )
        rows = []
        invoice_id = None
        customer_id = None
        for row_number, cells in enumerate(reader, start=1):
            if row_number > limits.maximum_data_rows:
                raise GeneratedTransactionResourceError(
                    "data-row count exceeds predeclared ceiling {}".format(
                        limits.maximum_data_rows
                    )
                )
            if len(cells) != len(TRANSACTION_HEADER):
                raise GeneratedTransactionFixtureError(
                    "transaction row must contain exactly seven CSV cells"
                )
            raw_cells = tuple(cells)
            for name, value in zip(TRANSACTION_HEADER, raw_cells):
                _raw_cell(value, name=name)
            invoice = _private_id(raw_cells[0], name="Invoice")
            customer = _private_id(raw_cells[1], name="Customer")
            if invoice_id is None:
                invoice_id = invoice
                customer_id = customer
            elif invoice != invoice_id or customer != customer_id:
                raise GeneratedTransactionFixtureError(
                    "one source must contain exactly one invoice/customer pair"
                )
            time_index = _parse_time_index(raw_cells[2])
            product = raw_cells[3]
            if product not in TRANSACTION_PRODUCT_TOKENS:
                raise GeneratedTransactionFixtureError(
                    "Product is outside the frozen vocabulary"
                )
            try:
                cancellation = CancellationState(raw_cells[4])
            except ValueError as exc:
                raise GeneratedTransactionFixtureError(
                    "Cancellation is outside the explicit frozen vocabulary"
                ) from exc
            quantity_decimal, quantity_float = _parse_decimal(
                raw_cells[5], name="Quantity"
            )
            price_decimal, price_float = _parse_decimal(
                raw_cells[6], name="UnitPrice"
            )
            if price_decimal <= 0 or price_float <= 0.0:
                raise GeneratedTransactionFixtureError(
                    "UnitPrice must be strictly positive"
                )
            semantic = TransactionSemanticRow(
                invoice_id=invoice,
                customer_id=customer,
                time_index=time_index,
                product_token=product,
                cancellation_state=cancellation,
                quantity=quantity_decimal,
                unit_price=price_decimal,
            )
            rows.append(
                TransactionSourceRow(
                    line_number=reader.line_num,
                    source_sha256=source_sha256,
                    raw_cells=raw_cells,
                    semantic=semantic,
                    quantity_binary64=quantity_float,
                    unit_price_binary64=price_float,
                )
            )
    except csv.Error as exc:
        raise GeneratedTransactionFixtureError("malformed transaction CSV") from exc

    if not rows:
        raise GeneratedTransactionFixtureError(
            "transaction source requires at least one data row"
        )
    if len(rows) > limits.maximum_semantic_occurrences:
        raise GeneratedTransactionResourceError(
            "semantic occurrence count exceeds its predeclared ceiling"
        )
    return tuple(rows)


@dataclass(frozen=True)
class TransactionFixtureResult:
    """One validated invoice configuration and its private row provenance."""

    fixture_id: str
    source_split: str
    source_sha256: str
    source_byte_length: int
    configuration: EventConfiguration
    private_provenance: TransactionFixturePrivateProvenance
    resource_limits: TransactionFixtureResourceLimits
    source_format: str = TRANSACTION_SOURCE_FORMAT

    def __post_init__(self) -> None:
        _fixture_id(self.fixture_id)
        _source_split(self.source_split)
        _sha256(self.source_sha256, name="source_sha256")
        if type(self.source_byte_length) is not int or self.source_byte_length <= 0:
            raise TypeError("source_byte_length must be a positive exact integer")
        if type(self.configuration) is not EventConfiguration:
            raise TypeError("configuration must be an exact EventConfiguration")
        if type(self.private_provenance) is not TransactionFixturePrivateProvenance:
            raise TypeError(
                "private_provenance must be exact TransactionFixturePrivateProvenance"
            )
        if type(self.resource_limits) is not TransactionFixtureResourceLimits:
            raise TypeError(
                "resource_limits must be exact TransactionFixtureResourceLimits"
            )
        object.__setattr__(
            self,
            "resource_limits",
            _snapshot_limits(self.resource_limits),
        )
        if self.source_format != TRANSACTION_SOURCE_FORMAT:
            raise GeneratedTransactionFixtureError(
                "source_format is not the frozen transaction format"
            )
        if self.source_byte_length > self.resource_limits.maximum_source_bytes:
            raise GeneratedTransactionResourceError("source byte ceiling was exceeded")

        configuration = self.configuration
        configuration.validate(require_complete=True)
        if configuration.schema != _transaction_schema(self.resource_limits):
            raise GeneratedTransactionFixtureError(
                "configuration schema is not the frozen transaction schema"
            )
        if configuration.observed is None or not (
            configuration.observed.cardinality_observed
        ):
            raise GeneratedTransactionFixtureError(
                "source cardinality must remain explicitly observed"
            )
        rows = self.private_provenance.source_rows
        if len(rows) != len(configuration.events):
            raise GeneratedTransactionFixtureError(
                "one configuration occurrence is required for every source row"
            )
        if any(row.source_sha256 != self.source_sha256 for row in rows):
            raise GeneratedTransactionFixtureError(
                "private row provenance disagrees with source_sha256"
            )
        if any(
            row.semantic.invoice_id != configuration.sample_id
            or row.semantic.customer_id != configuration.group_id
            for row in rows
        ):
            raise GeneratedTransactionFixtureError(
                "source invoice/customer identity disagrees with sample/group"
            )
        expected_observation = EventObservation(
            time_observed=True,
            type_observed=True,
            observed_marks=frozenset(("quantity", "unit_price")),
        )
        for event, observation, row in zip(
            configuration.events,
            configuration.observed.events,
            self.private_provenance.event_rows,
        ):
            if event.event_id != row.event_id:
                raise GeneratedTransactionFixtureError(
                    "private source row is not aligned with its event occurrence"
                )
            expected_marks = {
                "quantity": (row.quantity_binary64,),
                "unit_price": (row.unit_price_binary64,),
            }
            if (
                event.event_time != float(row.semantic.time_index)
                or event.event_type != row.semantic.type_id
                or dict(event.marks) != expected_marks
            ):
                raise GeneratedTransactionFixtureError(
                    "event occurrence disagrees with its semantic source row"
                )
            if observation != expected_observation:
                raise GeneratedTransactionFixtureError(
                    "transaction source-observation mask is not fully observed"
                )
        if len(configuration.events) > (
            self.resource_limits.maximum_semantic_occurrences
        ):
            raise GeneratedTransactionResourceError(
                "semantic occurrence ceiling was exceeded"
            )
        maximum = max(self.occupied_cell_counts.values(), default=0)
        if maximum > self.resource_limits.maximum_occurrences_per_cell:
            raise GeneratedTransactionResourceError(
                "per-cell occurrence ceiling was exceeded"
            )
        reserved = {
            R_ACG_1_A_ID: (
                R_ACG_1_A_SHA256,
                len(R_ACG_1_A_BYTES),
                R_ACG_1_A_INVOICE_ID,
                R_ACG_1_CUSTOMER_ID,
            ),
            R_ACG_1_B_ID: (
                R_ACG_1_B_SHA256,
                len(R_ACG_1_B_BYTES),
                R_ACG_1_B_INVOICE_ID,
                R_ACG_1_CUSTOMER_ID,
            ),
        }.get(self.fixture_id)
        if reserved is not None:
            expected_sha, expected_size, expected_sample, expected_group = reserved
            actual = (
                self.source_sha256,
                self.source_byte_length,
                self.configuration.sample_id,
                self.configuration.group_id,
                self.source_split,
                self.resource_limits,
            )
            expected = (
                expected_sha,
                expected_size,
                expected_sample,
                expected_group,
                R_ACG_1_SPLIT,
                R_ACG_1_RESOURCE_LIMITS,
            )
            if actual != expected:
                raise GeneratedTransactionFixtureError(
                    "reserved fixture identity requires its exact source, "
                    "partition, and resource policy"
                )

    @property
    def partition(self) -> TransactionFixturePartitionDescription:
        return TransactionFixturePartitionDescription(
            fixture_id=self.fixture_id,
            sample_id=self.configuration.sample_id,
            group_id=self.configuration.group_id,
            split=self.source_split,
            source_sha256=self.source_sha256,
        )

    @property
    def occupied_cell_counts(self) -> Dict[Tuple[float, int], int]:
        counts = Counter(
            (event.event_time, event.event_type)
            for event in self.configuration.events
        )
        return dict(sorted(counts.items()))

    def reconstruct_semantic_row_multiset(
        self,
    ) -> Tuple[Tuple[Tuple[str, object], ...], ...]:
        return self.private_provenance.semantic_row_multiset()

    def to_atomic_counting_grid(
        self, *, max_occurrences_per_cell: Optional[int] = None
    ) -> AtomicCountingGridTensor:
        required = max(self.occupied_cell_counts.values(), default=0)
        if max_occurrences_per_cell is None:
            capacity = required
        else:
            capacity = _exact_positive_int(
                max_occurrences_per_cell,
                name="max_occurrences_per_cell",
            )
        if capacity < required:
            raise GeneratedTransactionResourceError(
                "fixture requires {} occurrences in one cell; capacity {} would "
                "truncate it".format(required, capacity)
            )
        if capacity > self.resource_limits.maximum_occurrences_per_cell:
            raise GeneratedTransactionResourceError(
                "requested capacity exceeds the predeclared per-cell ceiling"
            )
        return AtomicCountingGridTensor.from_configuration(
            self.configuration,
            max_occurrences_per_cell=capacity,
        )


def build_transaction_counting_fixture(
    source_bytes: bytes,
    *,
    fixture_id: str,
    expected_sha256: Optional[str],
    source_split: str,
    expected_invoice_id: Optional[str] = None,
    expected_customer_id: Optional[str] = None,
    limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS,
) -> TransactionFixtureResult:
    """Build one invoice while preserving every line-item occurrence."""

    limits = _snapshot_limits(limits)
    source, source_sha256 = _preflight_source(
        source_bytes,
        limits=limits,
        expected_sha256=expected_sha256,
    )
    fixture = _fixture_id(fixture_id)
    split = _source_split(source_split)
    rows = parse_transaction_fixture_source(
        source,
        limits=limits,
        expected_sha256=source_sha256,
    )
    invoice_id = rows[0].semantic.invoice_id
    customer_id = rows[0].semantic.customer_id
    if expected_invoice_id is not None and invoice_id != _private_id(
        expected_invoice_id, name="expected_invoice_id"
    ):
        raise GeneratedTransactionFixtureError("source invoice identity mismatch")
    if expected_customer_id is not None and customer_id != _private_id(
        expected_customer_id, name="expected_customer_id"
    ):
        raise GeneratedTransactionFixtureError("source customer identity mismatch")

    cell_counts = Counter()
    events = []
    observations = []
    for row in rows:
        semantic = row.semantic
        event = Event(
            event_time=float(semantic.time_index),
            event_type=semantic.type_id,
            marks={
                "quantity": row.quantity_binary64,
                "unit_price": row.unit_price_binary64,
            },
            event_id=row.event_id,
        )
        events.append(event)
        observations.append(
            EventObservation(
                time_observed=True,
                type_observed=True,
                observed_marks=frozenset(("quantity", "unit_price")),
            )
        )
        cell = (event.event_time, event.event_type)
        cell_counts[cell] += 1
        if cell_counts[cell] > limits.maximum_occurrences_per_cell:
            raise GeneratedTransactionResourceError(
                "transaction cell multiplicity exceeds its predeclared ceiling"
            )

    configuration = EventConfiguration(
        schema=_transaction_schema(limits),
        events=tuple(events),
        observed=ObservationPattern(
            events=tuple(observations),
            cardinality_observed=True,
        ),
        sample_id=invoice_id,
        group_id=customer_id,
    )
    row_by_event_id = {row.event_id: row for row in rows}
    event_rows = tuple(
        row_by_event_id[event.event_id] for event in configuration.events
    )
    provenance = TransactionFixturePrivateProvenance(
        source_rows=rows,
        event_rows=event_rows,
    )
    return TransactionFixtureResult(
        fixture_id=fixture,
        source_split=split,
        source_sha256=source_sha256,
        source_byte_length=len(source),
        configuration=configuration,
        private_provenance=provenance,
        resource_limits=limits,
    )


def build_r_acg_1_a(
    *, limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS
) -> TransactionFixtureResult:
    """Build the first invoice in the exact R-ACG-1 corpus."""

    return build_transaction_counting_fixture(
        R_ACG_1_A_BYTES,
        fixture_id=R_ACG_1_A_ID,
        expected_sha256=R_ACG_1_A_SHA256,
        source_split=R_ACG_1_SPLIT,
        expected_invoice_id=R_ACG_1_A_INVOICE_ID,
        expected_customer_id=R_ACG_1_CUSTOMER_ID,
        limits=limits,
    )


def build_r_acg_1_b(
    *, limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS
) -> TransactionFixtureResult:
    """Build the second invoice in the exact R-ACG-1 corpus."""

    return build_transaction_counting_fixture(
        R_ACG_1_B_BYTES,
        fixture_id=R_ACG_1_B_ID,
        expected_sha256=R_ACG_1_B_SHA256,
        source_split=R_ACG_1_SPLIT,
        expected_invoice_id=R_ACG_1_B_INVOICE_ID,
        expected_customer_id=R_ACG_1_CUSTOMER_ID,
        limits=limits,
    )


def build_r_acg_1_corpus(
    *, limits: TransactionFixtureResourceLimits = R_ACG_1_RESOURCE_LIMITS
) -> Tuple[TransactionFixtureResult, TransactionFixtureResult]:
    """Build both invoice samples belonging to the shared customer group."""

    return (build_r_acg_1_a(limits=limits), build_r_acg_1_b(limits=limits))


if len(R_ACG_1_A_BYTES) != 214 or hashlib.sha256(
    R_ACG_1_A_BYTES
).hexdigest() != R_ACG_1_A_SHA256:
    raise RuntimeError("R-ACG-1-A embedded bytes do not match their frozen identity")
if len(R_ACG_1_B_BYTES) != 168 or hashlib.sha256(
    R_ACG_1_B_BYTES
).hexdigest() != R_ACG_1_B_SHA256:
    raise RuntimeError("R-ACG-1-B embedded bytes do not match their frozen identity")


__all__ = [
    "CancellationState",
    "GeneratedTransactionFixtureError",
    "GeneratedTransactionResourceError",
    "R_ACG_1_A_BYTES",
    "R_ACG_1_A_ID",
    "R_ACG_1_A_INVOICE_ID",
    "R_ACG_1_A_SHA256",
    "R_ACG_1_A_TEXT",
    "R_ACG_1_B_BYTES",
    "R_ACG_1_B_ID",
    "R_ACG_1_B_INVOICE_ID",
    "R_ACG_1_B_SHA256",
    "R_ACG_1_B_TEXT",
    "R_ACG_1_CORPUS_SPLIT_DESCRIPTION",
    "R_ACG_1_CUSTOMER_ID",
    "R_ACG_1_ID",
    "R_ACG_1_RESOURCE_LIMITS",
    "R_ACG_1_SPLIT",
    "TRANSACTION_CANCELLATION_STATES",
    "TRANSACTION_HEADER",
    "TRANSACTION_HEADER_TEXT",
    "TRANSACTION_PRODUCT_TOKENS",
    "TRANSACTION_SCHEMA_VERSION",
    "TRANSACTION_SOURCE_FORMAT",
    "TRANSACTION_TIME_INDICES",
    "TRANSACTION_TYPE_IDS",
    "TRANSACTION_TYPE_VOCABULARY",
    "TransactionFixturePartitionDescription",
    "TransactionFixturePrivateProvenance",
    "TransactionFixtureResourceLimits",
    "TransactionFixtureResult",
    "TransactionSemanticRow",
    "TransactionSourceRow",
    "build_r_acg_1_a",
    "build_r_acg_1_b",
    "build_r_acg_1_corpus",
    "build_transaction_counting_fixture",
    "parse_transaction_fixture_source",
    "transaction_fixture_schema",
]
