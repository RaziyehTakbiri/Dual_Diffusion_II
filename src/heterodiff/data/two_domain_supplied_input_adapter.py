"""Supplied input -> exact F105 configurations and split-ready group lineage.

No file, network, workbook, training, or approval operation is performed here.
PhysioNet input is already-decoded record text; its hash binds that UTF-8 text,
not an original archive. Retail input is already-decoded eight-field rows:
Quantity is an integer, InvoiceDate a seven-integer source-civil tuple, and
UnitPrice an exact decimal string. No spreadsheet-to-token conversion is
invented. These adapters do not certify source completeness or admit data.

Configurations are canonical multisets. Occurrences retain source order and
carry their event explicitly; do not zip them with sorted configuration.events.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import StringIO
from typing import Dict, Optional, Tuple

from heterodiff.data.physionet_2012_raw import (
    PhysioNet2012Record,
    parse_physionet_2012_record,
)
from heterodiff.data.physionet_2012_admission_preflight import PatientRecord
from heterodiff.data import two_domain_f061_preservation_first_successor as f061
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks


RETAIL_FIELDS = (
    'InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate',
    'UnitPrice', 'CustomerID', 'Country',
)


class SuppliedInputError(ValueError):
    """The complete supplied input cannot be adapted without loss or coercion."""


@dataclass(frozen=True)
class EventOccurrence:
    """A preserved observation; PhysioNet row numbers are physical CSV lines.

    Retail uses source_record_ordinal=0 and zero-based source_row_number.
    """

    source_record_ordinal: int
    source_row_number: int
    event: cks.ExactEvent


@dataclass(frozen=True)
class GroupConfiguration:
    group_id: str
    configuration: cks.ExactConfiguration
    occurrences: Tuple[EventOccurrence, ...]
    context: Tuple[Tuple[str, str], ...]


@dataclass(frozen=True)
class F061CountAssessment:
    group_count: int
    hamilton_counts: Tuple[int, int, int]
    compatible: bool
    reason: str

    def to_dict(self) -> Dict[str, object]:
        return {
            'group_count': self.group_count,
            'hamilton_counts': dict(zip(f061.SPLIT_NAMES, self.hamilton_counts)),
            'compatible_with_frozen_exact_128_128_rule': self.compatible,
            'reason': self.reason,
            'groups_dropped_or_added': 0,
            'split_constructed': False,
            'admission_granted': False,
        }


def assess_f061_group_count(group_count: int) -> F061CountAssessment:
    """Check the existing count rule only; never subset, top up, or resplit."""

    counts = f061.hamilton_counts(group_count)
    try:
        f061.exact_count_compatibility_predicate(group_count, counts)
    except f061.F061SuccessorError as error:
        if error.reason_code != f061.TERMINAL_NO_GO_CODE:
            raise
        return F061CountAssessment(group_count, counts, False, error.reason_code)
    return F061CountAssessment(
        group_count, counts, True,
        'COUNT_COMPATIBLE_ONLY_EXTERNAL_REVIEW_AND_ADMISSION_STILL_REQUIRED',
    )


@dataclass(frozen=True)
class PhysioNetAdaptation:
    groups: Tuple[GroupConfiguration, ...]
    raw_records: Tuple[PhysioNet2012Record, ...]
    supplied_text_utf8_sha256: Tuple[str, ...]
    patient_projection: Tuple[PatientRecord, ...]

    def summary(self) -> Dict[str, object]:
        return _summary('physionet-challenge-2012', self.groups,
                        sum(len(record.rows) for record in self.raw_records))


@dataclass(frozen=True)
class RetailDecodedRow:
    row_ordinal: int
    invoice_no: str
    stock_code: str
    description: Optional[str]
    quantity: int
    invoice_calendar: Tuple[int, ...]
    unit_price_text: str
    customer_id: str
    country: Optional[str]


@dataclass(frozen=True)
class RetailAdaptation:
    groups: Tuple[GroupConfiguration, ...]
    source_rows: Tuple[RetailDecodedRow, ...]

    def split_rows(self) -> list:
        """Fresh exact input carrier for the existing F060 temporal splitter.

        This is input preparation, not a split or source/approval receipt.
        The production path must still use the accepted guarded F061 entrypoint.
        """

        return [
            {
                'row_ordinal': row.row_ordinal,
                'customer_key_hex': cks.retail_customer_key_hex(
                    customer_id=row.customer_id),
                'timestamp_source_civil_microseconds_since_2009_12_01': (
                    cks.retail_source_civil_microseconds(row.invoice_calendar)
                ),
            }
            for row in self.source_rows
        ]

    def summary(self) -> Dict[str, object]:
        return _summary('online-retail-ii', self.groups, len(self.source_rows))


def _summary(domain_id: str, groups: tuple, source_rows: int) -> Dict[str, object]:
    return {
        'domain_id': domain_id,
        'decision': 'SUPPLIED_INPUT_ADAPTED_NOT_ADMITTED',
        'natural_group_count': len(groups),
        'source_row_count': source_rows,
        'event_occurrence_count': sum(len(group.occurrences) for group in groups),
        'f061_count_assessment': assess_f061_group_count(len(groups)).to_dict(),
        'snapshot_completeness_verified': False,
        'governance_approval_verified': False,
        'support_or_near_duplicate_audit_verified': False,
        'training_or_scientific_evaluation_executed': False,
    }


def adapt_physionet_record_texts(record_texts: tuple) -> PhysioNetAdaptation:
    """Adapt every observation while retaining all static rows and raw tokens.

    Record ordinals follow the supplied tuple. Duplicate patient identifiers
    fail the entire call; records are never merged, discarded, or reassigned.
    """

    if type(record_texts) is not tuple or not record_texts:
        raise SuppliedInputError('PHYSIONET_REQUIRES_NONEMPTY_EXACT_TEXT_TUPLE')
    groups, records, digests, projection = [], [], [], []
    patient_ids = set()
    for ordinal, text in enumerate(record_texts):
        if type(text) is not str:
            raise SuppliedInputError('PHYSIONET_RECORD_TEXT_MUST_BE_EXACT_STRING')
        try:
            record = parse_physionet_2012_record(StringIO(text, newline=''))
            patient = PatientRecord(ordinal, record.record_id)
            if patient.patient_id in patient_ids:
                raise SuppliedInputError('DUPLICATE_PHYSIONET_PATIENT_ID')
            patient_ids.add(patient.patient_id)
            cks.validate_configuration_count(
                cks.PHYSIONET_DOMAIN_ID, len(record.observation_rows))
            occurrences = tuple(
                EventOccurrence(
                    ordinal, row.line_number,
                    cks.physionet_event_from_decimal_token(
                        elapsed_minutes=row.elapsed_minutes,
                        parameter=row.parameter, value_text=row.value_text),
                )
                for row in record.observation_rows
            )
            configuration = cks.physionet_configuration(
                tuple(item.event for item in occurrences))
            text_digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        except (TypeError, ValueError, UnicodeError) as error:
            raise SuppliedInputError(
                f'PHYSIONET_RECORD_{ordinal}_INVALID:{error}') from error
        groups.append(GroupConfiguration(
            patient.patient_id, configuration, occurrences,
            tuple((row.parameter, row.value_text)
                  for row in record.admission_descriptor_rows),
        ))
        records.append(record)
        digests.append(text_digest)
        projection.append(patient)
    return PhysioNetAdaptation(tuple(groups), tuple(records), tuple(digests),
                              tuple(projection))


def adapt_retail_decoded_rows(rows: tuple) -> RetailAdaptation:
    """Adapt exact decoded eight-field rows, preserving source row ordinals.

    Unknown/missing fields, implicit numeric/time conversions, and any malformed
    required value fail the entire call. No rows are filtered or deduplicated.
    """

    if type(rows) is not tuple or not rows:
        raise SuppliedInputError('RETAIL_REQUIRES_NONEMPTY_EXACT_ROW_TUPLE')
    grouped = {}
    source_rows = []
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or set(row) != set(RETAIL_FIELDS):
            raise SuppliedInputError(f'RETAIL_ROW_{ordinal}_EXACT_FIELDS_REQUIRED')
        try:
            customer_id = cks.validate_retail_customer_context(
                customer_id=row['CustomerID'])
            event = cks.retail_event_from_decimal_token(
                invoice_no=row['InvoiceNo'], stock_code=row['StockCode'],
                description=row['Description'], quantity=row['Quantity'],
                invoice_calendar=row['InvoiceDate'],
                unit_price_text=row['UnitPrice'], country=row['Country'],
            )
            occurrences = grouped.setdefault(customer_id, [])
            cks.validate_configuration_count(
                cks.RETAIL_DOMAIN_ID, len(occurrences) + 1)
        except (TypeError, ValueError) as error:
            raise SuppliedInputError(f'RETAIL_ROW_{ordinal}_INVALID:{error}') from error
        occurrences.append(EventOccurrence(0, ordinal, event))
        source_rows.append(RetailDecodedRow(
            ordinal, row['InvoiceNo'], row['StockCode'], row['Description'],
            row['Quantity'], row['InvoiceDate'], row['UnitPrice'], customer_id,
            row['Country'],
        ))
    groups = tuple(
        GroupConfiguration(
            customer_id,
            cks.retail_configuration(tuple(item.event for item in occurrences)),
            tuple(occurrences), (('CustomerID', customer_id),),
        )
        for customer_id, occurrences in sorted(grouped.items())
    )
    return RetailAdaptation(groups, tuple(source_rows))


__all__ = [
    'SuppliedInputError', 'EventOccurrence', 'GroupConfiguration',
    'F061CountAssessment', 'PhysioNetAdaptation', 'RetailDecodedRow',
    'RetailAdaptation', 'assess_f061_group_count',
    'adapt_physionet_record_texts', 'adapt_retail_decoded_rows',
]
