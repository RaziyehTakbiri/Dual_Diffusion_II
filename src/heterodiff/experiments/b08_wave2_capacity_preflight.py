"""Pure validation for the Wave-2 local-capacity no-go preflight.

The module validates exact arithmetic and evidence boundaries.  It performs no
capture, reservation, benchmark, subprocess, network, data, or science action.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from typing import Dict, Iterable, List


SCHEMA_VERSION = "heterodiff-manuscript-v3-b08-wave2-capacity-preflight-v1"
STATE = "B08_WAVE2_LOCAL_CAPACITY_PREFLIGHT_TERMINAL_NO_GO"
CONTROL_PREDICATE = "B08_LOCAL_HOST_CAPACITY_INSUFFICIENT_NO_PROMOTION_V1"

RESIDUAL_FIELD_IDS = (
    "F150", "F151", "F152", "F154", "F155",
    "F156", "F157", "F159", "F160", "F162",
)
REQUIREMENT_IDS = (
    "HARDWARE_AND_RUNTIME_IDENTITY",
    "CALIBRATION_WEIGHTS",
    "SCALAR_AND_HARD_AXIS_CEILING_VALUES",
    "CAPACITY_RESERVATION_RECEIPT",
)

AVAILABLE_BLOCKS_1024 = 38_359_440
AVAILABLE_BYTES = 39_280_066_560
DESTINATION_RESERVATION_BYTES = 1_099_511_627_776
AUXILIARY_RESERVATION_BYTES = 34_359_738_368
COMBINED_RESERVATION_BYTES = 1_133_871_366_144
SHORTFALL_BYTES = 1_094_591_299_584
MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION = 4_096
AVAILABILITY_FRACTION = Fraction(799_155, 23_068_672)

_HEX = frozenset("0123456789abcdef")


def canonical_json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("value is not finite canonical JSON") from error
    return encoded.encode("ascii")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _exact_keys(value: object, expected: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise ValueError(name + " must be an exact object")
    expected_set = frozenset(expected)
    if frozenset(value) != expected_set or any(type(key) is not str for key in value):
        raise ValueError(name + " has a non-exact schema")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(name + " must be an exact boolean")
    return value


def _exact_int(value: object, *, name: str, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError(name + " must be an exact nonnegative integer")
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(name + " must be a lowercase SHA-256 digest")
    return value


def predecessor_bindings() -> List[Dict[str, object]]:
    return [
        {
            "bytes": 20_982,
            "path": "research/fixtures/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.json",
            "raw_sha256": "f141e12624f10a13aab61fc034914e3fea5d75bb5f4f49cc4dd723c4fe48eda6",
            "role": "ACCEPTED_B08_PARTIAL_FREEZE_MACHINE",
        },
        {
            "bytes": 7_087_027,
            "path": "research/fixtures/cp50_test28_mixed_initializer_v26.json",
            "raw_sha256": "7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68",
            "role": "CURRENT_TEST28_CAPACITY_CONTRACT",
        },
        {
            "bytes": 11_076,
            "path": "PROJECT_B12_WHOLE_METHOD_INITIALIZER_PATH_INTEGRATION_SUCCESSOR_INDEPENDENT_REVIEW.md",
            "raw_sha256": "e24f2e97a67048323170b44d6e537ab07c3a7a6692cf682bc3053c1165732765",
            "role": "ACCEPTED_NONCONFIRMATORY_WHOLE_METHOD_BETA_REVIEW",
        },
    ]


def fresh_data_free_receipt() -> Dict[str, object]:
    body: Dict[str, object] = {
        "capture_not_externally_attested": True,
        "data_or_entropy_used": False,
        "f104_calibration_weight_claimed": False,
        "matrix_product": {
            "device": "cpu",
            "input_formula": (
                "A[i,j]=binary32((512*i+j)%257);"
                "B[i,j]=binary32((512*j+i)%263);C=A@B"
            ),
            "output_sha256s": [
                "c76266f28c6450c7287b439af602d1b5b72ea14f4feab8de04b4ad0c860e1773"
            ] * 3,
            "repeat_count": 3,
            "wall_time_ns": [4_144_125, 1_058_334, 946_333],
        },
        "production_capacity_or_ceiling_claimed": False,
        "reported_date": "2026-09-02",
        "sha256_stream": {
            "input_formula": "1048576 zero bytes concatenated 64 times",
            "output_sha256s": [
                "3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351"
            ] * 5,
            "repeat_count": 5,
            "wall_time_ns": [
                41_411_917, 35_264_500, 69_533_916, 39_519_542, 41_525_500
            ],
        },
        "synthetic_non_scientific": True,
    }
    body["receipt_sha256"] = sha256_json(body)
    return body


def residual_gaps() -> List[Dict[str, object]]:
    reasons = {
        "F150": "NO_SELECTED_RESERVED_PRODUCTION_HARDWARE",
        "F151": "NO_COMPLETE_OBSERVED_B12_PRODUCTION_RUNTIME_MANIFEST",
        "F152": "CURRENT_LOCK_EXPLICITLY_DISCLAIMS_PRODUCTION_ROLE",
        "F154": "NO_QUALIFIED_COMPLETE_RUN_UNIT_WALL_TIME_CEILING",
        "F155": "CPU_ONLY_PRODUCTION_ROUTE_NOT_SELECTED_AND_QUALIFIED",
        "F156": "NO_COMPLETE_RUN_PEAK_MEMORY_OR_PERSISTENT_BYTE_CEILINGS",
        "F157": "NO_COMPLETE_B12_RUN_UNIT_TO_MODEL_EVALUATION_MAPPING",
        "F159": "NO_INSTANTIATED_TUNING_WEIGHTS_HARD_AXES_OR_CAPACITY",
        "F160": "NO_INSTANTIATED_FINAL_WEIGHTS_HARD_AXES_OR_CAPACITY",
        "F162": "NO_TOTAL_SCALAR_EIGHT_AXIS_CEILING_OR_RESERVATION_RECEIPT",
    }
    return [
        {
            "field_id": field_id,
            "reason_code": reasons[field_id],
            "status": "OPEN_NULL_NO_VALUE_PROPOSED",
        }
        for field_id in RESIDUAL_FIELD_IDS
    ]


def supported_projection() -> Dict[str, object]:
    return {
        "b08_gate": {
            "B08_close_permitted": False,
            "requirements": [
                {"requirement_id": requirement_id, "satisfied": False}
                for requirement_id in REQUIREMENT_IDS
            ],
            "terminal_disposition": "B08_REMAINS_OPEN_EXTERNAL_CAPACITY_REQUIRED",
        },
        "capacity_arithmetic": {
            "auxiliary_reservation_bytes": AUXILIARY_RESERVATION_BYTES,
            "availability_fraction_denominator": AVAILABILITY_FRACTION.denominator,
            "availability_fraction_numerator": AVAILABILITY_FRACTION.numerator,
            "available_1024_byte_blocks": AVAILABLE_BLOCKS_1024,
            "available_bytes": AVAILABLE_BYTES,
            "capacity_pass": False,
            "combined_reservation_bytes": COMBINED_RESERVATION_BYTES,
            "destination_reservation_bytes": DESTINATION_RESERVATION_BYTES,
            "minimum_available_inodes_after_reservation": MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION,
            "reserved_bytes": 0,
            "shortfall_bytes": SHORTFALL_BYTES,
            "snapshot_is_reservation_receipt": False,
        },
        "existing_b08_partial_freeze_revalidation": {
            "focused_tests_passed": 66,
            "focused_tests_total": 66,
            "validator_disposition": "PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN",
        },
        "fresh_data_free_receipt": fresh_data_free_receipt(),
        "project_effects": {
            "B08_closed": False,
            "capacity_or_reservation_created": False,
            "field_ids_closed_now": [],
            "formal_tests_closed_now": [],
            "production_hardware_or_runtime_selected": False,
            "tracker_or_evidence_ledger_edited": False,
        },
        "residual_gaps": residual_gaps(),
    }


def build_machine_record() -> Dict[str, object]:
    projection = supported_projection()
    return {
        "control_predicate": CONTROL_PREDICATE,
        "predecessor_bindings": predecessor_bindings(),
        "record_sha256": sha256_json(projection),
        "reported_date": "2026-09-02",
        "schema_version": SCHEMA_VERSION,
        "state": STATE,
        "supported_projection": projection,
    }


def validate_machine_record(record: object) -> Dict[str, object]:
    value = _exact_keys(
        record,
        (
            "control_predicate", "predecessor_bindings", "record_sha256",
            "reported_date", "schema_version", "state", "supported_projection",
        ),
        name="record",
    )
    if value != build_machine_record():
        raise ValueError("record differs from exact Wave-2 preflight")
    projection = value["supported_projection"]
    _sha256(value["record_sha256"], name="record.record_sha256")
    if value["record_sha256"] != sha256_json(projection):
        raise ValueError("record digest differs")
    arithmetic = projection["capacity_arithmetic"]
    for key in (
        "available_1024_byte_blocks", "available_bytes",
        "destination_reservation_bytes", "auxiliary_reservation_bytes",
        "combined_reservation_bytes", "shortfall_bytes",
    ):
        _exact_int(arithmetic[key], name="capacity_arithmetic." + key, positive=True)
    if arithmetic["available_1024_byte_blocks"] * 1024 != arithmetic["available_bytes"]:
        raise ValueError("available-byte arithmetic differs")
    if (
        arithmetic["destination_reservation_bytes"]
        + arithmetic["auxiliary_reservation_bytes"]
        != arithmetic["combined_reservation_bytes"]
    ):
        raise ValueError("combined reservation arithmetic differs")
    if (
        arithmetic["combined_reservation_bytes"] - arithmetic["available_bytes"]
        != arithmetic["shortfall_bytes"]
    ):
        raise ValueError("shortfall arithmetic differs")
    if not arithmetic["available_bytes"] < arithmetic["combined_reservation_bytes"]:
        raise ValueError("capacity no-go predicate differs")
    _exact_bool(arithmetic["capacity_pass"], name="capacity_pass")
    if arithmetic["capacity_pass"]:
        raise ValueError("capacity cannot pass")
    if [row["field_id"] for row in projection["residual_gaps"]] != list(RESIDUAL_FIELD_IDS):
        raise ValueError("residual field roster differs")
    if projection["project_effects"]["field_ids_closed_now"] != []:
        raise ValueError("field closure is forbidden")
    if projection["b08_gate"]["B08_close_permitted"]:
        raise ValueError("B08 closure is forbidden")
    return deepcopy(value)
