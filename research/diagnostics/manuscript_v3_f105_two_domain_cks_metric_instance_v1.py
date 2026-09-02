#!/usr/bin/env python3
"""Read-only validator for the exact two-domain F105 CKS instance."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Mapping, Tuple


SCHEMA = "heterodiff-manuscript-v3-f105-two-domain-cks-metric-instance-v1"
REPORTED_DATE = "2026-09-01"
STATE = "F105_TWO_DOMAIN_CKS_EXACT_INSTANCE_FROZEN_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "ADDITIVE_ALL_OR_NOTHING_18_PRE_FIELD_CLOSURE_WITH_F060_CORRECTION"

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py"
HUMAN_PATH = "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_f105_two_domain_cks_metric_instance_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_f105_two_domain_cks_metric_instance_v1.py"
)
PACKAGE_PATHS = (SOURCE_PATH, HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

EXPECTED_SOURCE_BYTES = 25342
EXPECTED_SOURCE_SHA256 = "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881"
EXPECTED_HUMAN_BYTES = 15242
EXPECTED_HUMAN_SHA256 = "5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef"
EXPECTED_TEST_BYTES = 17542
EXPECTED_TEST_SHA256 = "f86daa76c8e0492e614107c7f777a914da826356d71edf09d2a59ddcfbbc6a82"

AUTHORITY_MESSAGES = (
    (
        "Adopt CKS for F105 and build the exact two-domain metric instance.",
        66,
        "a185a475568c39c840cb4cf105321538d334ad0f81cfe3d7856edd6a3ae2abdc",
    ),
    (
        "Makes sense, go ahead and finish the tasks you mentioned above.",
        63,
        "9cc94897178bda0c7a8acc3d6a3a17e328640f2968ad3802f7fcfda5c4fa7898",
    ),
)

PREDECESSOR_SPECS = (
    ("GENERIC_CKS_THEOREM", "human", "PROJECT_CKS_COUNT_NORMALIZED_EVENT_THEOREM.md", 16151, "53445cb8617fb6573105ad8912616967dcad601dcf6b30b4a28d3bf9a3034c15"),
    ("GENERIC_CKS_THEOREM", "machine", "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json", 10073, "33dd22403ad7d71375c53c05028dd59567f127e233a8dc247a7a7ea730f13f6f"),
    ("GENERIC_CKS_THEOREM", "validator", "research/diagnostics/manuscript_v3_cks_count_normalized_event_theorem_v1.py", 25728, "722d5781f05646e3252609939768a8e021274288ca90d9142eee7c220bf30576"),
    ("GENERIC_CKS_THEOREM", "test", "tests/unit/test_manuscript_v3_cks_count_normalized_event_theorem_v1.py", 15192, "527e6349962e7180d19cfa6ebad9747a638b37a06225d3cc068fff7f1c15b61b"),
    ("GENERIC_CKS_REFERENCE", "human", "PROJECT_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION.md", 17236, "6ab0413f900c0126094e178637106bd6375e36f697b07b92b9351bdd4fad8dd6"),
    ("GENERIC_CKS_REFERENCE", "machine", "research/fixtures/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.json", 10720, "9842d49a2a14ecaaa1f968ffd427f1792b31aa6d3c67384fcf0de5702db95dbb"),
    ("GENERIC_CKS_REFERENCE", "validator", "research/diagnostics/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py", 38245, "a1b72a2fab24dad7077e6c22efe1d3babb5215c1eb016cc7bc098d35536fa9c3"),
    ("GENERIC_CKS_REFERENCE", "test", "tests/unit/test_manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py", 46846, "7867364a1f0f7898db88dbb4c12405c5c66ebef7c7deb40c15a398f8b3fa0c18"),
    ("PHYSIONET_ROUTE_DRAFT", "human", "PROJECT_PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT.md", 10756, "d41f107f92a8cda85ff1c2afab7e6f38e6fcc46223214d34e5a3cdbf6666be0b"),
    ("PHYSIONET_ROUTE_DRAFT", "machine", "research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json", 12418, "2934e6499fb3645e5c8bcd95185594d11e0873bce06a68102765a9168e9e5f9b"),
    ("PHYSIONET_LOCAL_CODE", "raw_parser", "src/heterodiff/data/physionet_2012_raw.py", 25231, "ff869134bfd696964c23bf7a2dbd0b2b428811b0fb3058cd7f3bd688dd48968c"),
    ("PHYSIONET_LOCAL_CODE", "adapter", "src/heterodiff/data/physionet_2012_adapter.py", 34377, "4429d826115bd520d2d3dacecb68fed3dc53d72c99acec9095068f44aa5582da"),
    ("RETAIL_ROUTE_DRAFT", "human", "PROJECT_RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS.md", 12733, "9367f1fd9f13f89ea734eff1020d3ea0f3e0d9993f5c490c6339b65f4beeb377"),
    ("RETAIL_ROUTE_DRAFT", "machine", "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json", 21912, "0e91275c1671e2725aea60c32d4cac2216c6bb71c2cda195b53b79d8fd295388"),
    ("F060_PREDECESSOR", "human", "PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md", 10183, "e6125a472bacd83382ccfeb24d2ca9802886da62b79eecbe407dff1b4b168dfc"),
    ("F060_PREDECESSOR", "machine", "research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json", 19860, "b7dc23fd0dfee04ffe4834ff1b186ca99dce23f784c4555a245aab0cfb47f068"),
    ("F060_PREDECESSOR", "validator", "research/diagnostics/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py", 46174, "b828463a8a78ebe96efda5588a5d288e11b890512e8a8f17913066ca7c965abf"),
    ("F060_PREDECESSOR", "test", "tests/unit/test_manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py", 31846, "74cda9146983d2276f615a510305d6f837ee398aa7703c80788149a5c46ec2c7"),
    ("LOCKED_ROUTE_SUCCESSOR", "human", "PROJECT_MANUSCRIPT_V3_LOCKED_ROUTE_SUCCESSOR.md", 7630, "da43f5802fe71f17d95b1515163f2cf373d12c072e2058595b0978d0efc64f2f"),
    ("LOCKED_ROUTE_SUCCESSOR", "machine", "research/fixtures/manuscript_v3_locked_route_successor_v1.json", 12809, "fbf8f470d5c019606b2a757708539f05e5897edd9ac782fd621d5969f88713e9"),
    ("LOCKED_ROUTE_SUCCESSOR", "validator", "research/diagnostics/manuscript_v3_locked_route_successor_v1.py", 37354, "7864cfc716736ddae26980662a4febe94850401c6282c69938f68f3be4c01a28"),
    ("LOCKED_ROUTE_SUCCESSOR", "test", "tests/unit/test_manuscript_v3_locked_route_successor_v1.py", 7637, "2423361968445a42b7b2f36d9fc6f77a56b89999e7f585aa6e264b8557b72f8d"),
)

PREDECESSOR_SEMANTIC_DIGESTS = {
    "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json": "613dd2a1be716f382215769babca2503bd9b0c6cd9ae48fa2972e5df353743a3",
    "research/fixtures/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.json": "ff4a651db864a6ac534b05ccec1952ebca6acd5a0c0c3caa299deab93c89d94a",
    "research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json": "342f9dccdc8bb8edbba3f08c8600017bb3d1187ffe1034b8ab37ce48d953d650",
    "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json": "2f5a8ec8871ece584099b20b10ee2cf6424ac9a724becc34c691b49d1e7fba87",
    "research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json": "b48f21698908f3fb3506866db30f2658c9e050caf32da88e7906b428f86e1c51",
    "research/fixtures/manuscript_v3_locked_route_successor_v1.json": "c61df8e95a48c6cdb3d9f92986a45b65e2342d06b4a51d1e264a40f9ba108051",
}

PHYSIONET_PARAMETERS = (
    "Albumin", "ALP", "ALT", "AST", "Bilirubin", "BUN", "Cholesterol",
    "Creatinine", "DiasABP", "FiO2", "GCS", "Glucose", "HCO3", "HCT",
    "HR", "K", "Lactate", "Mg", "MAP", "MechVent", "Na", "NIDiasABP",
    "NIMAP", "NISysABP", "PaCO2", "PaO2", "pH", "Platelets",
    "RespRate", "SaO2", "SysABP", "Temp", "TropI", "TropT", "Urine",
    "WBC", "Weight",
)
PHYSIONET_UNITS = (
    "g/dL", "IU/L", "IU/L", "IU/L", "mg/dL", "mg/dL", "mg/dL",
    "mg/dL", "mmHg", "fraction", "score", "mg/dL", "mmol/L", "percent",
    "bpm", "mEq/L", "mmol/L", "mmol/L", "mmHg", "binary", "mEq/L",
    "mmHg", "mmHg", "mmHg", "mmHg", "mmHg", "pH", "cells/nL", "bpm",
    "percent", "mmHg", "degC", "ug/L", "ug/L", "mL", "cells/nL", "kg",
)

FIELD_CLOSURE_SPECS = (
    ("F023", "/domains/0/generated_endpoint_semantics", "/domain_contracts/0/generated_endpoint_semantics"),
    ("F024", "/domains/0/context_semantics", "/domain_contracts/0/context_semantics"),
    ("F026", "/domains/0/event_type_and_mark_schema", "/domain_contracts/0/event_schema"),
    ("F027", "/domains/0/physical_time_semantics", "/domain_contracts/0/physical_time"),
    ("F028", "/domains/0/horizon", "/domain_contracts/0/horizon"),
    ("F029", "/domains/0/cap", "/domain_contracts/0/configuration_cap"),
    ("F030", "/domains/0/segmentation_rule", "/domain_contracts/0/segmentation_rule"),
    ("F031", "/domains/0/overflow_and_exclusion_rule", "/domain_contracts/0/terminal_no_go_rule"),
    ("F042", "/domains/1/generated_endpoint_semantics", "/domain_contracts/1/generated_endpoint_semantics"),
    ("F043", "/domains/1/context_semantics", "/domain_contracts/1/context_semantics"),
    ("F045", "/domains/1/event_type_and_mark_schema", "/domain_contracts/1/event_schema"),
    ("F046", "/domains/1/physical_time_semantics", "/domain_contracts/1/physical_time"),
    ("F047", "/domains/1/horizon", "/domain_contracts/1/horizon"),
    ("F048", "/domains/1/cap", "/domain_contracts/1/configuration_cap"),
    ("F049", "/domains/1/segmentation_rule", "/domain_contracts/1/segmentation_rule"),
    ("F050", "/domains/1/overflow_and_exclusion_rule", "/domain_contracts/1/terminal_no_go_rule"),
    ("F051", "/domains/1/cancellation_country_and_simultaneous_line_item_rule", "/domain_contracts/1/cancellation_country_and_simultaneity"),
    ("F105", "/metric_and_estimand_plan/primary_metric_id", "/metric_contract/primary_metric_id"),
)

MAX_FILE_BYTES = 1_000_000
_DIGEST_DOMAIN = b"heterodiff:f105-two-domain-cks-instance:v1\0"


class ValidationError(RuntimeError):
    """Raised when any exact package condition fails."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_parts(relative: str) -> Tuple[str, ...]:
    if type(relative) is not str:
        raise ValidationError("path must be a built-in string")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise ValidationError("unsafe package-relative path")
    if str(pure) != relative:
        raise ValidationError("path is not canonical POSIX relative form")
    return pure.parts


def _read_regular(
    root: Path,
    relative: str,
    *,
    expected_bytes: int | None = None,
    expected_sha256: str | None = None,
) -> Tuple[bytes, Dict[str, Any]]:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValidationError("package root is not a directory")
    parts = _relative_parts(relative)
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    try:
        directory_descriptor = os.open(root, directory_flags)
    except OSError as exc:
        raise ValidationError("cannot open package root") from exc
    try:
        for component in parts[:-1]:
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
            except OSError as exc:
                raise ValidationError(
                    f"cannot component-wise no-follow open {relative}"
                ) from exc
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(parts[-1], flags, dir_fd=directory_descriptor)
        except OSError as exc:
            raise ValidationError(f"cannot no-follow open {relative}") from exc
    finally:
        os.close(directory_descriptor)
    try:
        first = os.fstat(descriptor)
        if not stat.S_ISREG(first.st_mode):
            raise ValidationError(f"{relative} is not regular")
        if first.st_nlink != 1:
            raise ValidationError(f"{relative} is not single-link custody")
        if stat.S_IMODE(first.st_mode) != 0o644:
            raise ValidationError(f"{relative} mode is not 0644")
        limit = expected_bytes if expected_bytes is not None else MAX_FILE_BYTES
        if first.st_size > limit or first.st_size > MAX_FILE_BYTES:
            raise ValidationError(f"{relative} exceeds its byte bound")
        chunks = []
        remaining = first.st_size
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                raise ValidationError(f"short read for {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ValidationError(f"growth during read for {relative}")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    stable = (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns)
    stable_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    if stable != stable_after:
        raise ValidationError(f"unstable read for {relative}")
    data = b"".join(chunks)
    digest = _sha256(data)
    if expected_bytes is not None and len(data) != expected_bytes:
        raise ValidationError(f"byte count mismatch for {relative}")
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValidationError(f"raw hash mismatch for {relative}")
    if not data.endswith(b"\n"):
        raise ValidationError(f"{relative} lacks terminal LF")
    return data, {
        "bytes": len(data),
        "mode_octal": "0644",
        "nlink": 1,
        "path": relative,
        "raw_sha256": digest,
        "terminal_lf": True,
    }


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    if type(record) is not dict:
        raise ValidationError("machine record must be a built-in object")
    try:
        payload = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValidationError("machine record is not canonicalizable") from exc
    if len(payload) + 1 > MAX_FILE_BYTES:
        raise ValidationError("machine record exceeds its byte bound")
    return payload + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be a built-in object")
    payload = {key: value for key, value in record.items() if key != "record_sha256"}
    return _sha256(_DIGEST_DOMAIN + canonical_machine_bytes(payload)[:-1])


def _parse_canonical_machine(
    data: bytes, *, verify_f105_self_digest: bool = True
) -> Dict[str, Any]:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError("machine record is not ASCII") from exc
    if not text.endswith("\n") or "\n" in text[:-1] or "\r" in text:
        raise ValidationError("machine record must be one canonical LF-terminated line")
    try:
        record = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValidationError("invalid machine JSON") from exc
    if type(record) is not dict or canonical_machine_bytes(record) != data:
        raise ValidationError("machine bytes are not canonical JSON")
    digest = record.get("record_sha256")
    if type(digest) is not str:
        raise ValidationError("machine semantic digest is absent")
    if verify_f105_self_digest and digest != record_sha256(record):
        raise ValidationError("machine semantic digest mismatch")
    return record


def _parse_bound_predecessor_json(data: bytes) -> Dict[str, Any]:
    try:
        text = data.decode("utf-8")
        record = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValidationError("invalid bound predecessor JSON") from exc
    if type(record) is not dict:
        raise ValidationError("bound predecessor JSON is not an object")
    return record


def _validate_source(source_bytes: bytes) -> None:
    module_name = "_verified_f105_two_domain_cks_instance"
    module = ModuleType(module_name)
    module.__file__ = SOURCE_PATH
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        code = compile(source_bytes, SOURCE_PATH, "exec", dont_inherit=True)
        exec(code, module.__dict__)
    finally:
        if previous is None:
            del sys.modules[module_name]
        else:
            sys.modules[module_name] = previous

    def require(condition: bool, message: str) -> None:
        if condition is not True:
            raise ValidationError(message)

    require(module.PRIMARY_METRIC_ID == "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1", "metric ID drift")
    require(tuple(module.PHYSIONET_PARAMETERS) == PHYSIONET_PARAMETERS, "PhysioNet roster drift")
    require(tuple(module.PHYSIONET_UNITS[name] for name in PHYSIONET_PARAMETERS) == PHYSIONET_UNITS, "PhysioNet unit drift")
    require(module.PHYSIONET_SPEC.coordinate_dimension == 112, "PhysioNet dimension drift")
    require(module.RETAIL_SPEC.coordinate_dimension == 10, "Retail dimension drift")
    require(module.PHYSIONET_CONFIGURATION_CAP == 131072, "PhysioNet cap drift")
    require(module.RETAIL_CONFIGURATION_CAP == 1067371, "Retail cap drift")
    require(module.PHYSIONET_HORIZON_MINUTES == 2880, "PhysioNet horizon drift")
    require(module.RETAIL_HORIZON_SECONDS == 63849600, "Retail seconds drift")
    require(module.RETAIL_HORIZON_MICROSECONDS == 63849600000000, "Retail microseconds drift")
    for spec in module.DOMAIN_SPECS.values():
        require(
            (spec.event_tau2, spec.count_scale2, spec.event_scale2, spec.outer_sigma2)
            == (Fraction(1), Fraction(1), Fraction(1), Fraction(1)),
            "kernel parameter drift",
        )
    decimal_phys = module.physionet_event_from_decimal_token(elapsed_minutes=0, parameter="HR", value_text="0.1")
    binary_phys = module.physionet_event_from_binary64(elapsed_minutes=0, parameter="HR", value=0.1)
    require(decimal_phys.coordinates[75 + PHYSIONET_PARAMETERS.index("HR")] == Fraction(1, 11), "PhysioNet exact decimal drift")
    require(decimal_phys != binary_phys, "PhysioNet decimal collapsed through binary64")
    require(
        module.physionet_event_from_decimal_token(elapsed_minutes=0, parameter="HR", value_text="-1")
        != module.physionet_event_from_decimal_token(elapsed_minutes=0, parameter="HR", value_text="0"),
        "PhysioNet missing/present-zero collision",
    )
    require(module.retail_source_civil_microseconds((2009, 12, 1, 0, 0, 0, 0)) == 0, "Retail time origin drift")
    require(module.retail_source_civil_microseconds((2011, 12, 9, 23, 59, 59, 999999)) == 63849599999999, "Retail horizon drift")
    retail_args = dict(
        invoice_no="123456", stock_code="01234", description="Widget",
        quantity=2, invoice_calendar=(2009, 12, 1, 0, 0, 0, 0),
        country="United Kingdom",
    )
    decimal_retail = module.retail_event_from_decimal_token(unit_price_text="0.1", **retail_args)
    binary_retail = module.retail_event_from_binary64(unit_price=0.1, **retail_args)
    require(decimal_retail.coordinates[7] == Fraction(1, 11), "Retail exact decimal drift")
    require(decimal_retail != binary_retail, "Retail decimal collapsed through binary64")
    require(module.retail_customer_key_hex(customer_id="12345") == "3132333435", "Retail customer projection drift")
    try:
        module.retail_customer_key_hex(customer_id="00001")
    except module.CKSInstanceError:
        pass
    else:
        raise ValidationError("Retail canonical CustomerID admits a leading-zero alias")
    one = module.physionet_configuration((decimal_phys,))
    require(module.configuration_kernel(one, one) == module.ConfigurationKernelSymbol(Fraction(0), ()), "kernel identity drift")
    score = module.conditional_cks_score((one, one), one)
    require(score == module.FormalCKSScore(((module.ConfigurationKernelSymbol(Fraction(0), ()), Fraction(-1)),)), "score identity drift")


def _rational_one() -> Dict[str, int]:
    return {"denominator": 1, "numerator": 1}


def _domain_contracts() -> list[Dict[str, Any]]:
    return [
        {
            "slot_id": "R3-PHYS",
            "domain_id": "physionet-challenge-2012",
            "generated_endpoint_semantics": "COMPLETE_ADMITTED_OCCURRENCE_EXPANDED_TIME_SERIES_ROW_CONFIGURATION_PER_RECORDID_FIRST_48_HOURS",
            "context_semantics": {
                "custody_and_split_identity": "RecordID",
                "static_descriptor_names": ["RecordID", "Age", "Gender", "Height", "ICUType", "Weight"],
                "admission_weight_static_later_weight_rows_events": True,
                "context_excluded_from_generated_event_coordinates": True,
            },
            "event_schema": {
                "raw_fields": ["Time", "Parameter", "Value"],
                "parameter_roster": list(PHYSIONET_PARAMETERS),
                "units_by_parameter": {name: unit for name, unit in zip(PHYSIONET_PARAMETERS, PHYSIONET_UNITS)},
                "source_decimal_values_exact_rational": True,
                "source_decimal_token_max_ascii_bytes": 256,
                "generated_binary64_values_exact_as_integer_ratio": True,
                "missing_token": "-1",
                "present_values_nonnegative": True,
                "transform": "R112_ONEHOT37_PLUS_T_OVER_2880_PLUS_TYPE_SPECIFIC_PRESENT37_PLUS_TYPE_SPECIFIC_V_OVER_1_PLUS_V37",
                "missing_and_present_zero_distinct": True,
                "simultaneous_multiple_and_duplicate_rows_preserved": True,
            },
            "physical_time": "INTEGER_ELAPSED_MINUTES_SINCE_ICU_ADMISSION_CLOSED_0_TO_2880",
            "horizon": {"event_support": "CLOSED", "minutes": 2880},
            "configuration_cap": {"agent_selected_not_source_fact": True, "rows": 131072},
            "segmentation_rule": "ONE_CONFIGURATION_PER_RECORDID_ALL_TIME_SERIES_ROWS_ON_FROZEN_HORIZON_STATIC_DESCRIPTORS_EXCLUDED",
            "terminal_no_go_rule": "WHOLE_DOMAIN_NO_GO_ON_CAP_SCHEMA_TIME_VALUE_TYPE_COLLISION_OR_ANY_REQUIRED_ROW_OR_PATIENT_EXCLUSION_NO_TRUNCATION_RETRY_RESPLIT_TOPUP_OR_REASSIGNMENT",
        },
        {
            "slot_id": "R4-RETAIL",
            "domain_id": "online-retail-ii",
            "generated_endpoint_semantics": "COMPLETE_ADMITTED_OCCURRENCE_EXPANDED_TRANSACTION_LINE_ITEM_CONFIGURATION_PER_CUSTOMERID_ON_FROZEN_HORIZON",
            "context_semantics": {
                "customer_id": "CANONICAL_POSITIVE_DECIMAL_INTEGER_ONE_TO_FIVE_ASCII_DIGITS",
                "event_coordinate": False,
                "f060_customer_key_hex": "LOWERCASE_HEX_OF_EXACT_CUSTOMER_ID_ASCII_BYTES",
                "one_contiguous_row_ordinal_per_source_row": True,
            },
            "event_schema": {
                "raw_fields": ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"],
                "transform": "R10_J_INVOICE_CANCEL_J_STOCK_DESCRIPTION_MASK_J_TIME_OVER_H_SIGNED_QUANTITY_SIGNED_PRICE_COUNTRY_MASK_J",
                "invoice_grammar": "SIX_ASCII_DIGITS_OR_ASCII_C_CASE_INSENSITIVE_PLUS_SIX_DIGITS",
                "utf8_token_map": "INJECTIVE_LENGTH_PREFIXED_BASE256_C_OVER_C_PLUS_1",
                "description_optional_masked_max_utf8_bytes": 4096,
                "stock_required_max_utf8_bytes": 256,
                "country_optional_masked_max_utf8_bytes": 256,
                "present_source_strings_trimmed_casefolded_or_normalized": False,
                "quantity": "EXACT_SIGNED_INTEGER_Q_OVER_1_PLUS_ABS_Q",
                "source_unit_price": "EXACT_SIGNED_DECIMAL_RATIONAL_Q_OVER_1_PLUS_ABS_Q",
                "source_unit_price_token_max_ascii_bytes": 256,
                "generated_unit_price": "EXACT_BINARY64_AS_INTEGER_RATIO_Q_OVER_1_PLUS_ABS_Q",
            },
            "physical_time": {
                "carrier": "SOURCE_CIVIL_MICROSECONDS_SINCE_2009_12_01_00_00_00",
                "input": "EXACT_SEVEN_INTEGER_GREGORIAN_TUPLE",
                "timezone_utc_offset_dst_or_instant_claimed": False,
            },
            "horizon": {
                "start_inclusive": "2009-12-01T00:00:00.000000_SOURCE_CIVIL",
                "end_exclusive": "2011-12-10T00:00:00.000000_SOURCE_CIVIL",
                "days": 739,
                "seconds": 63849600,
                "microseconds": 63849600000000,
            },
            "configuration_cap": {"documented_whole_dataset_row_bound_conditional_on_future_snapshot": True, "rows": 1067371},
            "segmentation_rule": "ONE_CONFIGURATION_PER_CANONICAL_CUSTOMERID_ALL_ROWS_ON_FROZEN_HORIZON_PRESERVE_DUPLICATES_TIES_AND_MULTIPLICITY",
            "terminal_no_go_rule": "WHOLE_DOMAIN_NO_GO_ON_CAP_SCHEMA_REQUIRED_FIELD_TIME_TOKEN_OR_ANY_ROW_OR_CUSTOMER_EXCLUSION_NO_TRUNCATION_RETRY_RESPLIT_TOPUP_MIGRATION_OR_REASSIGNMENT",
            "cancellation_country_and_simultaneity": {
                "cancellation": "ONE_IFF_RAW_INVOICE_STARTS_ASCII_C_CASE_INSENSITIVE_AND_REMAINDER_SIX_DIGITS_RAW_INVOICE_RETAINED",
                "country": "EXACT_OPTIONAL_UTF8_TOKEN_WITH_MISSING_MASK_NO_ONE_COUNTRY_PER_CUSTOMER_RULE",
                "duplicates_multiple_invoice_rows_and_equal_times_preserved": True,
            },
        },
    ]


def _f060_correction() -> Dict[str, Any]:
    return {
        "field_id": "F060",
        "json_pointer": "/split_and_leakage_plan/retail_temporal_cutoff_and_window_rule",
        "status": "CLOSED_VALUE_SUPERSEDED_NO_COUNT_DELTA",
        "predecessor_rule_id": "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_F061_PARAMETERIZED_V1",
        "successor_rule_id": "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_SOURCE_CIVIL_F061_PARAMETERIZED_V2",
        "changed_semantics_only": ["rule_id", "timestamp_carrier", "normalized_timestamp_key", "timestamp_domain"],
        "normalized_row_exact_keys": ["row_ordinal", "customer_key_hex", "timestamp_source_civil_microseconds_since_2009_12_01"],
        "timestamp_domain": "INTEGER_HALF_OPEN_0_TO_63849600000000",
        "utc_timezone_offset_dst_or_instant_claimed": False,
        "customer_key_projection": "LOWERCASE_HEX_OF_EXACT_F043_CUSTOMER_ID_ASCII_BYTES",
        "row_ordinal": "CONTIGUOUS_ONE_PER_SOURCE_ROW_PRESERVE_TIES_DUPLICATES_AND_MULTIPLICITY",
        "unchanged_contract": {
            "candidate_pairs": "ALL_0_LE_G1_LT_G2_LE_M_MINUS_2",
            "customer_intervals": "CLOSED_MINIMUM_TO_MAXIMUM_OVER_ALL_CUSTOMER_ROWS",
            "selection": "FIRST_FEASIBLE_LEXICOGRAPHIC_T_G1_T_G1_PLUS_1_T_G2_T_G2_PLUS_1",
            "windows": ["TRAIN_T_LE_T_G1", "VALIDATION_T_G1_LT_T_LE_T_G2", "TEST_T_GT_T_G2"],
            "requires_exact_future_f061_positive_customer_counts": True,
            "complete_pairwise_disjoint_customers_and_rows": True,
            "strict_time_separation": True,
            "fallback_retry_exclusion_reassignment_migration_resplit_or_topup": False,
            "no_feasible_pair_code": "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR",
        },
        "f061_value": None,
        "actual_cutoff_split_or_feasibility_observed": False,
    }


def _expected_core() -> Dict[str, Any]:
    closures = [
        {
            "field_id": field_id,
            "json_pointer": json_pointer,
            "status": "CLOSED_BY_EXACT_TWO_DOMAIN_CKS_INSTANCE",
            "value_pointer": value_pointer,
        }
        for field_id, json_pointer, value_pointer in FIELD_CLOSURE_SPECS
    ]
    return {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "authority": {
            "normalized_visible_messages": [
                {"text": text, "utf8_bytes": size, "sha256": digest}
                for text, size, digest in AUTHORITY_MESSAGES
            ],
            "exact_instance_build_test_review_and_tracker_reconciliation_authorized": True,
            "dataset_download_opening_authentication_contact_access_request_entropy_training_science_result_claim_or_submission_authorized": False,
            "raw_transport_account_identity_timestamp_signature_or_external_attestation_bound": False,
        },
        "public_documentation_observations": {
            "raw_response_or_html_bytes_custodied": False,
            "network_request_count_transport_or_redirect_claimed": False,
            "dataset_file_opened_or_downloaded": False,
            "physionet": {
                "url": "https://physionet.org/content/challenge-2012/1.0.0/",
                "page_version": "1.0.0",
                "published_date_display": "2012-01-20",
                "record_count_display": 12000,
                "training_set_count_display": 4000,
                "held_test_set_counts_display": [4000, 4000],
                "first_hours": 48,
                "descriptor_names": ["RecordID", "Age", "Gender", "Height", "ICUType", "Weight"],
                "time_series_roster": list(PHYSIONET_PARAMETERS),
                "nonnegative_valid_values_and_minus_one_missing_displayed": True,
                "simultaneous_multiple_and_outlier_warning_displayed": True,
            },
            "retail": {
                "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
                "instance_count_display": 1067371,
                "date_range_display": ["2009-12-01", "2011-12-09"],
                "field_names": ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"],
                "missing_values_displayed": True,
                "license_label_displayed": "CC BY 4.0",
                "timezone_displayed": False,
            },
            "snapshot_license_access_governance_or_privacy_receipt_created": False,
        },
        "domain_contracts": _domain_contracts(),
        "metric_contract": {
            "primary_metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
            "shared_parameters": {
                "count_scale2": _rational_one(),
                "event_scale2": _rational_one(),
                "event_tau2": _rational_one(),
                "outer_sigma2": _rational_one(),
            },
            "embedding": "PHI_X_EQUALS_COUNT_N_AND_NORMALIZED_EVENT_GAUSSIAN_MEAN_EMPTY_EVENT_CHANNEL_ZERO",
            "event_kernel": "EXP_NEGATIVE_SQUARED_TRANSFORM_DISTANCE_OVER_2",
            "configuration_kernel": "EXP_NEGATIVE_COUNT_DIFFERENCE_SQUARED_PLUS_EVENT_MEAN_RKHS_DISTANCE_SQUARED_OVER_2",
            "event_transforms_borel_injective": True,
            "configuration_embedding_injective_on_admitted_finite_counting_measures": True,
            "domain_kernels_characteristic": True,
            "strictly_proper_conditional_kernel_score": True,
            "score": "ONE_OVER_R_R_MINUS_1_OFF_DIAGONAL_DRAW_KERNEL_SUM_MINUS_TWO_OVER_R_DRAW_TARGET_KERNEL_SUM",
            "loss_direction": "LOWER_IS_BETTER",
            "paired_orientation": "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE",
            "cross_domain_evaluation": "FORBIDDEN",
            "conditional_draws_per_case_selected": None,
            "supported_formal_score_R_min": 2,
            "supported_formal_score_R_max": 128,
            "exact_nested_exponential_symbolic_output": True,
            "binary64_exponential_or_numeric_score_comparison": False,
            "fitted_parameters": False,
        },
        "field_closures": closures,
        "field_corrections": [_f060_correction()],
        "count_transition": {
            "before": {"pre_execution_open": 140, "pre_execution_closed": 26, "post_execution_open": 3, "post_execution_closed": 3, "total_open": 143, "total_closed": 29},
            "after": {"pre_execution_open": 122, "pre_execution_closed": 44, "post_execution_open": 3, "post_execution_closed": 3, "total_open": 125, "total_closed": 47},
            "closed_by_package": {"field_ids": [field_id for field_id, _, _ in FIELD_CLOSURE_SPECS], "pre_execution": 18, "post_execution": 0, "total": 18},
            "corrected_without_count_delta": ["F060"],
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "source_contract": {
            "source_path": SOURCE_PATH,
            "verified_bytes_compiled_in_memory_by_validator": True,
            "pathname_import_after_verification": False,
            "io_network_randomness_fitting_training_exponential_evaluation_or_science": False,
            "occurrence_multiplicity_and_permutation_invariance": True,
            "whole_configuration_cap_refusal": True,
        },
        "nonclosure": {
            "open_blockers": [f"B{index:02d}" for index in range(1, 13)],
            "open_fields_explicit": ["F025", "F032-F041", "F044", "F052-F059", "F061", "F109-F112"],
            "exact_gate_a_cks_checkbox_open_pending_manuscript_display_production_integration_and_independent_acceptance": True,
            "physionet_or_retail_domain_admitted": False,
            "actual_snapshot_split_manifest_cutoff_or_observation_kernel_present": False,
            "formal_tests_closed": 0,
            "results_filled": 0,
            "runtime_training_scientific_execution_or_claim": False,
        },
        "publication_boundary": {
            "internal_project_control_only": True,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_methods_statistics_license_governance_and_claim_audit_required": True,
        },
    }


def build_expected_record(root: Path = ROOT) -> Dict[str, Any]:
    predecessor_bindings = []
    semantic_bindings = []
    for ordinal, (group, role, path, size, digest) in enumerate(PREDECESSOR_SPECS):
        data, binding = _read_regular(root, path, expected_bytes=size, expected_sha256=digest)
        binding.update({"group": group, "ordinal": ordinal, "role": role})
        predecessor_bindings.append(binding)
        if path in PREDECESSOR_SEMANTIC_DIGESTS:
            record = _parse_bound_predecessor_json(data)
            semantic = PREDECESSOR_SEMANTIC_DIGESTS[path]
            if record.get("record_sha256") != semantic:
                raise ValidationError(f"predecessor semantic digest mismatch for {path}")
            semantic_bindings.append({"path": path, "record_sha256": semantic})

    source_bytes, source_binding = _read_regular(
        root, SOURCE_PATH, expected_bytes=EXPECTED_SOURCE_BYTES, expected_sha256=EXPECTED_SOURCE_SHA256
    )
    _validate_source(source_bytes)
    _, human_binding = _read_regular(
        root, HUMAN_PATH, expected_bytes=EXPECTED_HUMAN_BYTES, expected_sha256=EXPECTED_HUMAN_SHA256
    )
    _, test_binding = _read_regular(
        root, TEST_PATH, expected_bytes=EXPECTED_TEST_BYTES, expected_sha256=EXPECTED_TEST_SHA256
    )
    _, validator_binding = _read_regular(root, VALIDATOR_PATH)
    package_bindings = []
    for ordinal, (role, binding) in enumerate(
        (("source", source_binding), ("human", human_binding), ("validator", validator_binding), ("test", test_binding))
    ):
        item = dict(binding)
        item.update({"group": "CURRENT_PACKAGE", "ordinal": ordinal, "role": role})
        package_bindings.append(item)

    record = _expected_core()
    record["predecessor_bindings"] = predecessor_bindings
    record["predecessor_semantic_bindings"] = semantic_bindings
    record["package_bindings_excluding_machine_self"] = package_bindings
    record["package_file_roster"] = list(PACKAGE_PATHS)
    record["machine_self_binding"] = {
        "path": MACHINE_PATH,
        "raw_self_hash_embedded": False,
        "semantic_self_digest_field": "record_sha256",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate_package(root: Path = ROOT) -> Dict[str, Any]:
    expected = build_expected_record(root)
    machine_bytes, _ = _read_regular(root, MACHINE_PATH)
    observed = _parse_canonical_machine(machine_bytes)
    if observed != expected:
        raise ValidationError("machine record differs from the fully reconstructed contract")
    return observed


def main(argv: list[str]) -> int:
    if argv == ["--expected-json"]:
        sys.stdout.write(canonical_machine_bytes(build_expected_record(ROOT)).decode("ascii"))
        return 0
    if argv:
        raise ValidationError("usage: validator.py [--expected-json]")
    record = validate_package(ROOT)
    sys.stdout.write(json.dumps({"record_sha256": record["record_sha256"], "state": record["state"]}, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ValidationError as exc:
        sys.stderr.write(f"VALIDATION_ERROR: {exc}\n")
        raise SystemExit(1)
