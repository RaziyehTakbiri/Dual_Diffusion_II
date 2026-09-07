"""Tiny supplied synthetic inputs only; no actual dataset or approvals."""

from dataclasses import FrozenInstanceError
from fractions import Fraction
import hashlib

import pytest

from heterodiff.data import two_domain_supplied_input_adapter as adapter
from heterodiff.data import physionet_2012_admission_preflight as phys
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks


def record(patient='101', observations='00:10,HR,80\n'):
    return (
        'Time,Parameter,Value\n'
        f'00:00,RecordID,{patient}\n'
        '00:00,Age,42\n00:00,Gender,1\n00:00,Height,-1\n'
        '00:00,ICUType,2\n00:00,Weight,70\n' + observations
    )


def retail_row(**changes):
    value = {
        'InvoiceNo': '123456', 'StockCode': 'sku  ', 'Description': None,
        'Quantity': 2, 'InvoiceDate': (2009, 12, 1, 1, 0, 0, 0),
        'UnitPrice': '0.10', 'CustomerID': '101', 'Country': 'UK',
    }
    value.update(changes)
    return value


def test_physionet_preserves_static_context_multiplicity_and_lineage():
    text = record(observations=(
        '00:10,HR,80\n00:10,HR,80\n00:10,HR,-1\n'
        '00:10,HR,0\n00:20,Weight,71\n'
    ))
    result = adapter.adapt_physionet_record_texts((text,))
    group = result.groups[0]
    assert len(group.configuration.events) == len(group.occurrences) == 5
    assert group.occurrences[0].event == group.occurrences[1].event
    assert group.occurrences[2].event != group.occurrences[3].event
    assert tuple(item.source_row_number for item in group.occurrences) == (8, 9, 10, 11, 12)
    assert all(item.source_record_ordinal == 0 for item in group.occurrences)
    assert ('Weight', '70') in group.context
    assert result.raw_records[0].audit.total_rows == 11
    assert result.raw_records[0].audit.exact_duplicate_row_excess == 1
    assert result.supplied_text_utf8_sha256 == (hashlib.sha256(text.encode()).hexdigest(),)
    assert result.patient_projection == (phys.PatientRecord(0, '101'),)
    assert group.configuration.events == tuple(sorted(item.event for item in group.occurrences))


def test_physionet_exact_decimal_and_canonical_multiset_keep_source_order_separate():
    result = adapter.adapt_physionet_record_texts((record(observations=(
        '00:01,Weight,0.10\n00:02,HR,0.10000000000000001\n'
    )),))
    occurrences = result.groups[0].occurrences
    assert occurrences[0].event.coordinates[-1] == Fraction(1, 11)
    assert occurrences[1].event == cks.physionet_event_from_decimal_token(
        elapsed_minutes=2, parameter='HR', value_text='0.10000000000000001')


def test_physionet_preserves_empty_event_configuration_and_all_records():
    result = adapter.adapt_physionet_record_texts((record('102', ''), record('101')))
    assert tuple(group.group_id for group in result.groups) == ('102', '101')
    assert result.groups[0].configuration.events == ()
    assert result.patient_projection == (phys.PatientRecord(0, '102'), phys.PatientRecord(1, '101'))
    assert result.summary()['source_row_count'] == 13
    assert result.summary()['decision'] == 'SUPPLIED_INPUT_ADAPTED_NOT_ADMITTED'


@pytest.mark.parametrize('texts', [(), [], ('x',), (1,), (record('01'),),
                                 (record(), record()),
                                 (record(observations='00:10,Unknown,2\n'),),
                                 (record(observations='48:01,HR,2\n'),),
                                 (record(observations='00:10,HR,-2\n'),)])
def test_physionet_rejects_inexact_missing_duplicate_or_invalid_input(texts):
    with pytest.raises(adapter.SuppliedInputError):
        adapter.adapt_physionet_record_texts(texts)


def test_physionet_cap_is_checked_before_event_materialization(monkeypatch):
    calls = []
    def fail_cap(domain, count):
        calls.append((domain, count))
        raise cks.CKSInstanceError('cap')
    monkeypatch.setattr(cks, 'validate_configuration_count', fail_cap)
    with pytest.raises(adapter.SuppliedInputError):
        adapter.adapt_physionet_record_texts((record(),))
    assert calls == [(cks.PHYSIONET_DOMAIN_ID, 1)]


def test_retail_preserves_duplicates_masks_signed_values_and_customer_groups():
    rows = (
        retail_row(), retail_row(),
        retail_row(InvoiceNo='c123456', Quantity=-2, UnitPrice='-0.10', Country=None),
        retail_row(CustomerID='102', Description='', Country=''),
    )
    result = adapter.adapt_retail_decoded_rows(rows)
    assert tuple(group.group_id for group in result.groups) == ('101', '102')
    first = result.groups[0]
    assert len(first.configuration.events) == 3
    assert first.occurrences[0].event == first.occurrences[1].event
    assert first.occurrences[2].event.coordinates[1] == 1
    assert first.occurrences[2].event.coordinates[6:8] == (Fraction(-2, 3), Fraction(-1, 11))
    assert result.groups[1].occurrences[0].event.coordinates[3] == 1
    assert first.occurrences[0].event.coordinates[3] == 0
    assert result.source_rows[0].stock_code == 'sku  '
    assert result.source_rows[0].unit_price_text == '0.10'
    assert [row['row_ordinal'] for row in result.split_rows()] == [0, 1, 2, 3]
    assert result.split_rows()[0] == {
        'row_ordinal': 0, 'customer_key_hex': '313031',
        'timestamp_source_civil_microseconds_since_2009_12_01': 3_600_000_000,
    }
    assert sum(len(group.occurrences) for group in result.groups) == len(rows)


def test_retail_source_input_mutations_do_not_change_adapted_output():
    row = retail_row()
    result = adapter.adapt_retail_decoded_rows((row,))
    row['Quantity'] = 99
    assert result.source_rows[0].quantity == 2
    projection = result.split_rows()
    projection[0]['customer_key_hex'] = '00'
    assert result.split_rows()[0]['customer_key_hex'] == '313031'
    with pytest.raises(FrozenInstanceError):
        result.source_rows[0].quantity = 10


@pytest.mark.parametrize('changes', [
    {'CustomerID': None}, {'CustomerID': '001'}, {'CustomerID': 101},
    {'InvoiceNo': '123'}, {'StockCode': ''}, {'Quantity': True},
    {'Quantity': 2.0}, {'InvoiceDate': '2009-12-01'},
    {'InvoiceDate': (2011, 12, 10, 0, 0, 0, 0)},
    {'UnitPrice': 0.1}, {'UnitPrice': 'NaN'}, {'extra': 1},
])
def test_retail_required_data_never_silently_coerced_filtered_or_clipped(changes):
    with pytest.raises(adapter.SuppliedInputError):
        adapter.adapt_retail_decoded_rows((retail_row(), retail_row(**changes)))


@pytest.mark.parametrize('rows', [(), [], ({},), (retail_row, )])
def test_retail_requires_exact_complete_rows(rows):
    with pytest.raises(adapter.SuppliedInputError):
        adapter.adapt_retail_decoded_rows(rows)


@pytest.mark.parametrize('count', [1, 6, 851, 856, 12000])
def test_frozen_count_incompatibility_is_explicit_and_never_subsets(count):
    result = adapter.assess_f061_group_count(count).to_dict()
    assert result['compatible_with_frozen_exact_128_128_rule'] is False
    assert sum(result['hamilton_counts'].values()) == count
    assert result['groups_dropped_or_added'] == 0
    assert result['admission_granted'] is False
    assert result['split_constructed'] is False


@pytest.mark.parametrize('count', [852, 853, 854, 855])
def test_count_compatibility_is_not_forged_admission_or_split(count):
    result = adapter.assess_f061_group_count(count).to_dict()
    assert result['compatible_with_frozen_exact_128_128_rule'] is True
    assert result['hamilton_counts'] == {'TRAIN': count - 256, 'VALIDATION': 128, 'TEST': 128}
    assert result['admission_granted'] is False


@pytest.mark.parametrize('count', [True, 0, -1, 1.5, '852'])
def test_inexact_count_is_rejected(count):
    with pytest.raises(ValueError):
        adapter.assess_f061_group_count(count)


def test_adapter_summary_discloses_nonadmission_without_ids_or_payloads():
    summary = adapter.adapt_retail_decoded_rows((retail_row(),)).summary()
    assert summary['decision'] == 'SUPPLIED_INPUT_ADAPTED_NOT_ADMITTED'
    assert summary['event_occurrence_count'] == 1
    assert summary['snapshot_completeness_verified'] is False
    assert summary['governance_approval_verified'] is False
    assert summary['support_or_near_duplicate_audit_verified'] is False
    assert summary['training_or_scientific_evaluation_executed'] is False
    assert '101' not in repr(summary)


def test_source_only_notebook_works_without_site_packages_or_installed_project():
    import json
    from pathlib import Path
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]
    notebook = root / 'databricks/notebooks/two_domain_adapter_smoke.py'
    completed = subprocess.run(
        [sys.executable, '-I', '-S', '-B', str(notebook)],
        cwd=str(root), capture_output=True, text=True, timeout=60, check=True,
    )
    report = json.loads(completed.stdout)
    assert report['decision'] == 'PASS_TWO_DOMAIN_SUPPLIED_INPUT_ADAPTER_SYNTHETIC_SMOKE'
    assert report['scope'] == 'SOURCE_ONLY_ADAPTER_SMOKE_NOT_INSTALLED_WHEEL'
    assert report['site_packages_disabled'] is True
    assert report['numerical_libraries_imported'] is False
    assert report['legacy_data_initializer_exports_executed'] is False
    assert report['approval_or_admission_granted'] is False
    assert report['physionet']['event_occurrence_count'] == 3
    assert report['retail']['event_occurrence_count'] == 2
