"""Hostile contract tests for the CP63 runner/recomputation rehearsal."""

from __future__ import annotations

import ast
import copy
from dataclasses import fields
import hashlib
import inspect
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_independent_recomputation as oracle,
)
from heterodiff.evaluation import (
    mixed_initializer_test28_runner_recomputation_rehearsal as runner,
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_runner_recomputation_rehearsal.py"
)
_INDEPENDENT_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_recomputation.py"
)
_RUNNER_SOURCE_SHA256 = (
    "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
)
_INDEPENDENT_SOURCE_SHA256 = (
    "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
)
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_SHA256 = "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
_CP62_SEMANTIC_SHA256 = (
    "f3bd0b80c52a9d79a3b6a8e06aa2923c6303e891bf526c1869c5552e1413f3ff"
)
_REHEARSAL_SEED_HEX = "12a5228200019dae"
_REHEARSAL_CASE_IDS = tuple(
    f"rehearsal-row-{row_ordinal:02d}" for row_ordinal in range(1, 17)
)
_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_EXPECTED_SEMANTIC_CASE_RECEIPTS = (
    (
        1,
        9359,
        "3808f6f069d2bbb29761432f1f5134735f5d6ffb1c41811066b226b1fe6e6d08",
        "e2908539d363544e65c0874e9f3375140f30dca45c4e1511b29ee76625a235a6",
        1205,
        "8446c082f0aeeb45e7a34baba8f1b9619c66770f85fefbd3e8938834c34b53e4",
        "b4333eb7b4dc59453a1b2e8f8b7eef8c6565875cce351f7f17cd0eebf383c2bb",
        "60690f0e7287410ad7a93313b8de466638f341f5913ae15c23095803f3d19497",
    ),
    (
        2,
        22206,
        "90a209203dd59c6efc1cc9d9eb62c2627f329e0c9bf3ca8ad756e058de503e08",
        "d58be6273e00accb30872b39485bcf6542002740a6c7b278a2a355fa7821028f",
        1205,
        "852f533294a568dd4e580601162829b55666254a21bc022daa19fbbf4f9937dd",
        "59374850a5c1d8d0b0842105e42fea159613952f103a253ebc965e40f0ada67e",
        "4d5d7a98518083a9b5186c6cbb4972c621fa40366359099ec539bc04b667e023",
    ),
    (
        3,
        78551,
        "b17c3a5452d30a64f2af0c93a4f6c8661c3c9b9076c5b20a80a908e452b03db6",
        "187c7f9d7dde0e4a6b3a4ad1fbc48b091e29a419c25842dcefd1344ad3bef9cd",
        1208,
        "becc723b94ee0352e738663dc233a4829b9b1bc3bd7c7e397577ac53f6852b00",
        "72874b7e59e73d989e3f7f3c9a1d0e9bfc31614be41ac81518f9006a213f8bf2",
        "0e1297f06cf5c1d04f78e87102bbddd24504c28e590b5aec0194a3bae78d3bd1",
    ),
    (
        4,
        302752,
        "0f9771bfc95777afce5543fab42e486da3848fe03d5a7b4bead374eff5e0e9f4",
        "80b300c7a36fe01925c059c1385f39cdc9b2ee99b5e408b5353368f53901a033",
        1208,
        "50812833467df5ea0d03ab8e5a472ec89f321f77144ca58f9367781862090ff0",
        "0b0a8a3c608c7b658c740dde25f7cc3ec5ce113a11f937a00b31a75930ad9338",
        "2b06e465773a6e56fd730d1530880877413f0c49825bf38066f35fa6e500f00f",
    ),
    (
        5,
        18263,
        "e133ab69d1e0549c88aa3110083070ec759622391a38fee1f58daa3cd13cceeb",
        "a80a6bd5b2c9525a9b2d3e4287345fb76655a405bd00edddb99ea462d136114a",
        1201,
        "7e9c0998995ff385dbda033708df50a12aa3a2fa388d6a47e248ad238512a267",
        "67c2e1a9c6a1f8190e896b076ca6e0eab4b5e27b4784caceb7d1577129a49f01",
        "eccb83cbfa5107b9c3446a7f3dc052f33c95aca2e3f13a7d315747924935fa02",
    ),
    (
        6,
        57906,
        "7827e8cdcccf8e3e522f04e56480efd7fd2520bd1adaeb3663fc5449c8baf7d4",
        "639d50857cf0e900968f05416c6d381eccd7fef90c1ba1904d9edf427492c97b",
        1203,
        "af4e16e7c5d6dc8b90273a0605c100933a42b00c54fa595825e477542a405cf1",
        "fabe7b141674956dbb9bec5d8ebe59593707b259a067b8486adfed18a6dae5e9",
        "f16cfcb5f672e5b147509c8961f00fd27f3e56636bc36ac653ccbd7bc1318331",
    ),
    (
        7,
        215280,
        "aebf50cde28517219a834f5e662779dc0917d859c597308b17e51075a7b291d5",
        "2912cfda341c1927d6a00c7d2bf8d41473402b2c1220dcd6059276c95dbede7d",
        1205,
        "24f1ad3afe74c764f98628f7aef7f21bdb5a3c9ed520cf3bbf6daa4675455bc3",
        "54e5c03bd24470580e44503ca87e1596d0c4f6c879de662dadae082c6c549d06",
        "0d3b9226489ef5631a69fa4f7858b4b87d2da3b9377cfff59ffbc95d5b388292",
    ),
    (
        8,
        849489,
        "8da94ad317b232e97a7174c91c54cbc2f097b80659ec93da7703e3a4b13a0cc8",
        "bf523db87b5db37cd56e6beb0eedf53c2ff659dc013643039c88680cea7ae43e",
        1205,
        "34795d706fbfa0988370a431e418ebc6768a3b5760e607db2c8f2b613eb5ac94",
        "54c2a39a52e23aac472f93d7cda7d74a0375c1e5e942ac959493d7d965ddbb0b",
        "17851af3e514b62092c39c35900548a21c208f54c464b29bd7b857e4e0345966",
    ),
    (
        9,
        11386,
        "9c8c43dbf355f76ce6740a985cdd3fae3a84071694746e2475306536719298b0",
        "237d8dfec43d732df7c6744db0fa4abd82ca88eafd50f5d863ba3eca5042d0f6",
        954,
        "1d35d0beba9b42cdf45053159e15a1163cc4659ace0e7ef5e9e76306bf39da58",
        "5bd5f1a069d00213cb980cec2896deb4923e33faca068a706356ce766320b724",
        "b9c7e5be80f55c0440e493a3564633c7b44a8f54d922340abae133ae336c7381",
    ),
    (
        10,
        27720,
        "4d17f3dfec01ca0afa567233b7db4633f29a954c784ef897e95f456b246a28f4",
        "c8fb68ef07456f155d162dd274380d15d9985c8038573cf82fc023ac872b47aa",
        2767,
        "f7b8aac0014e23ad6e732c83dc3ff58c036e146bc59062b3d502e8c837ffe501",
        "2cbb633ffb7d52fc0f60ff520e6c0a405a574adf7e6bf5d802c47b549f97abe8",
        "0a9b11be43b483a2a3be66b24b13424ccbafaaaae08383f32f160d4cbbf7b0a5",
    ),
    (
        11,
        92454,
        "2ca4410e67644d9f3c4d508d0dcd3079d411fb2784b48b17f6e545b3f884b6a2",
        "8de78570baa1f97ae8dd32b714f1ab4c5da9ec73bd9a2b7ee8fa376cdb0460fe",
        2769,
        "4eb8ba9a76ad3b5510a2eebd3113e0e392115144d8fb41cd50de5d9c16e7ccc6",
        "fbc4d55e1a10a97605ada2ad919bba761c9736447f6eacbf54c6d5d1f0836f11",
        "1f5fd42cf35f4cf46e3347b26f120decd0d1f52ab3f26405b61890ab888209bc",
    ),
    (
        12,
        353054,
        "ee18f23ae44969cbb9a7ab92e2c9afc8491ca92a84e42f671b0de835858e1b87",
        "6f125f1865b1d57f1bf69794613035efc5284dafe52f3dd1603ddd619b616361",
        2769,
        "2649a6ffc5e3dbf1b6280dc3037b89a58ec7e5d1d12dc4a659cf9aac6e284d1c",
        "0fe51cb8a98f285b901b365367c8c58deb45c41391d3f31fa7e5f30931eb8df1",
        "24ef364df1dd9a82981fd2dd85bfc8dca995d6a4a1052a8e58df0a065cdd9d21",
    ),
    (
        13,
        19942,
        "eb3cd5161cfb50fc81422e94b71e86578bc90013271fe09e8b9f5291170826c1",
        "b354211d1c288f647563f35b3061788cf4a3442005b24dc5b93fccfa71a2f974",
        3225,
        "635ab91d243d778f5db4592b1b66292b05a90cf4c3429c8cb30c57c7d9efb9d4",
        "b640c59513d11a9e35ed4a2e34fb140555c58b799c327a714cbca391f19e6647",
        "97c14fd3ecda26744dd1f23748231ffb12b73e9ab6636d92a34c19c0b433aa88",
    ),
    (
        14,
        61413,
        "9d82fc205675125bb6f686b2760590f18560533f3c3247020f90a35a66ebf4b0",
        "dd3574135237ac50b379af320f18f154341a92342eca1b69ca5a5b57db0cc2ff",
        3152,
        "655a3c12c60a22db4c858782a16da0fe64031d77eb76ff86c032db323c50c174",
        "b8aada6d6820208210bc8281e8c5f6ed57134a90fe10498c8a659866efd32bcf",
        "ca90046e94148e89729f8abbfda8980ef7b839d616900a705f52b01effc25985",
    ),
    (
        15,
        229867,
        "78accd09a4ad2b65dbcb6e8a1bc70c286dee5766333ee43f7572c440568afe3b",
        "66439be79f81fed3ed23bd6911f197d795960646dd75b78cede4ed464dee629c",
        2766,
        "35f11c6f0c73d359b059480f42495d52afe5dd01dd3553179d44ac11c0b26d5c",
        "1405a70bc6f11f1c761794cb0d07f160b6cbfbb57215a77a463b9367002f31da",
        "af2f4407c4764ade505a29da426a812e757f673936ce98d9941053bf57d269ab",
    ),
    (
        16,
        904912,
        "1745ed8bc51d5ec923a1881e03e3373b896c4cdad9ea0bc24e8c6b8247f6a44a",
        "41012d6a70fd73f55127ec45a1adb52e572686b4553eb8389e3dbbf3c7ad6738",
        3140,
        "0245b44560ee5c4cf3234917aa8449ccef14ab54340ed2c312e52dec581b6aad",
        "1c0e239447e79cbd841c7d644e973365859e806e21b9fd624a0cec57de7f7088",
        "3308a1652b36b0a764f8986a962e132e9bb5b0522a0e43023afbffd12d60a9ac",
    ),
)
_EXPECTED_RECOMPUTATION_RECEIPT = (
    12939,
    "4c281147b68adc5a83ddd88bab73c42cef619498a13a7f234acb4cd886a40ee7",
    "870b89d2252dd5e62fc0c10982d5d2f194402b2a941c4c7bd8a0b6214a2832dc",
    "895b3afbe514158fdfbc3c3d2ae67175cdab2a5834cbf25b00297e69aa179406",
)
_EXPECTED_SEMANTIC_PIN_RECEIPT_SHA256 = (
    "d7dfdae440b3b26b289279ccdda6e665fe43fee965c0836fe1d6dac91ce8d5e7"
)


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_record_digest(record: dict) -> str:
    body = copy.deepcopy(record)
    body["raw_sha256"] = "0" * 64
    return hashlib.sha256(
        b"cp63-test28-raw-record-v1\0" + _plain_json_bytes(body)
    ).hexdigest()


def _rehearsal_request_instance_sha256(record: dict) -> str:
    identity = {
        name: record[name]
        for name in (
            "schema",
            "rehearsal_id",
            "seed_ordinal",
            "row_ordinal",
            "logical_request_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "plan_seed_hex",
            "seed_free_request_sha256",
            "runtime_lock_sha256",
        )
    }
    return hashlib.sha256(
        b"cp63-test28-rehearsal-request-instance-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()


def _redigest_raw_after_child_edit(record: dict) -> bytes:
    child_payload = {
        key: record[key]
        for key in record
        if key not in {"supervisor_custody", "raw_sha256"}
    }
    child_bytes = _plain_json_bytes(child_payload)
    child_frame = len(child_bytes).to_bytes(8, "big") + child_bytes
    record["supervisor_custody"]["frame_bytes"] = len(child_frame)
    record["supervisor_custody"]["child_frame_sha256"] = hashlib.sha256(
        child_frame
    ).hexdigest()
    record["raw_sha256"] = _raw_record_digest(record)
    return _plain_json_bytes(record)


def _redigest_owned_json_leaf(
    value: dict,
    *,
    digest_field: str,
    domain: bytes,
) -> None:
    value.pop(digest_field)
    value[digest_field] = hashlib.sha256(
        domain + b"\0" + _plain_json_bytes(value)
    ).hexdigest()


def _assert_runner_and_independent_reject_stable(trace: dict) -> None:
    payload = _plain_json_bytes(trace)
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_stable_trace_canonical_json_bytes(trace)
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(payload)


def _synthetic_seed_capsule_bytes(**changes: object) -> bytes:
    values = {
        "schema": runner.CP63_TEST28_SCHEMA_VERSION,
        "purpose": "future-production-external-iid-uniform-uint64-with-replacement",
        "cp61_stable_design_sha256": (
            "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
        ),
        "seed_count": 2_048,
        "seed_ordinals": list(range(1, 2_049)),
        "seed_encoding": "uint64-16-lowercase-hex-big-endian",
        "ordered_seed_values": [f"{ordinal - 1:016x}" for ordinal in range(1, 2_049)],
        "source_method_id": "development-synthetic-no-source-law",
        "source_receipt_sha256": hashlib.sha256(b"synthetic-source").hexdigest(),
        "acquisition_session_sha256": hashlib.sha256(
            b"synthetic-acquisition"
        ).hexdigest(),
        "body_sha256": "0" * 64,
    }
    values.update(changes)
    values["body_sha256"] = "0" * 64
    values["body_sha256"] = hashlib.sha256(
        b"cp63-test28-seed-capsule-v1\0" + _plain_json_bytes(values)
    ).hexdigest()
    return _plain_json_bytes(values)


@pytest.fixture(scope="module")
def rehearsal_frames() -> dict[str, tuple[tuple[bytes, dict], ...]]:
    """Spend the exact 16 x 2 development launch allowance once."""

    source_custody = {
        _SOURCE: _RUNNER_SOURCE_SHA256,
        _INDEPENDENT_SOURCE: _INDEPENDENT_SOURCE_SHA256,
    }
    for path, expected in source_custody.items():
        assert _file_sha256(path) == expected
    frames = {}
    try:
        for case_id in _REHEARSAL_CASE_IDS:
            repetitions = []
            for _ in range(2):
                payload = runner.cp63_run_rehearsal_case(case_id)
                repetitions.append(
                    (payload, runner.cp63_validate_raw_record_bytes(payload))
                )
            frames[case_id] = tuple(repetitions)
    finally:
        for path, expected in source_custody.items():
            assert _file_sha256(path) == expected
    return frames


def test_cp63_public_surface_and_signatures_are_exact() -> None:
    classes = {
        "CP63SeedCapsuleContractV1",
        "CP63SeedCapsuleObservationV1",
        "CP63ScheduleContractV1",
        "CP63BoundRequestV1",
        "CP63LifecycleContractV1",
        "CP63RawRecordSchemaV1",
        "CP63RunnerResourceContractV1",
        "CP63RehearsalCaseV1",
        "CP63RunnerRecomputationRehearsalBundleV1",
    }
    functions = {
        "cp63_runner_recomputation_rehearsal_bundle": (),
        "cp63_validate_seed_capsule_bytes": ("payload",),
        "cp63_seed_capsule_canonical_json_bytes": ("record",),
        "cp63_schedule_contract": (),
        "cp63_bound_request": ("seed_capsule", "logical_request_ordinal"),
        "cp63_validate_raw_record_bytes": ("payload",),
        "cp63_project_stable_trace": ("raw_record",),
        "cp63_stable_trace_canonical_json_bytes": ("trace",),
        "cp63_stable_trace_sha256": ("trace",),
        "cp63_run_rehearsal_case": ("case_id",),
    }
    expected = (
        classes
        | set(functions)
        | {
            "CP63RunnerRehearsalError",
            "CP63_TEST28_SCHEMA_VERSION",
            "CP63_TEST28_SCOPE",
        }
    )
    assert expected == set(runner.__all__)
    for name in expected:
        assert hasattr(runner, name), name
    for name, parameters in functions.items():
        assert tuple(inspect.signature(getattr(runner, name)).parameters) == parameters


def test_cp63_record_field_sets_are_exactly_frozen() -> None:
    expected = {
        "CP63SeedCapsuleContractV1": (
            "schema_version",
            "purpose",
            "cp61_stable_design_sha256",
            "seed_count",
            "seed_ordinals",
            "seed_encoding",
            "exact_json_keys",
            "maximum_capsule_bytes",
            "duplicate_values_retained",
            "order_is_semantic",
            "no_retry_drop_replacement_or_topup",
            "source_method_required",
            "source_receipt_required",
            "acquisition_session_required",
            "body_digest_required",
            "parser_can_verify_iid_uniform",
            "production_values_present",
            "record_sha256",
        ),
        "CP63SeedCapsuleObservationV1": (
            "schema",
            "purpose",
            "cp61_stable_design_sha256",
            "seed_count",
            "seed_ordinals",
            "seed_encoding",
            "ordered_seed_values",
            "source_method_id",
            "source_receipt_sha256",
            "acquisition_session_sha256",
            "body_sha256",
            "canonical_byte_count",
            "syntactically_valid",
            "source_custody_digest_bound",
            "iid_uniform_with_replacement_verified",
            "production_execution_authorized",
            "record_sha256",
        ),
        "CP63ScheduleContractV1": (
            "schema_version",
            "seed_count",
            "row_count",
            "row_ordinals",
            "total_request_count",
            "logical_request_ordinal_min",
            "logical_request_ordinal_max",
            "logical_request_order",
            "plan_seed_assignment",
            "fixture_strategy_budget_or_shard_hashing_before_plan_seed_assignment",
            "duplicate_seed_values_distinguished_by_ordinal",
            "schedule_digest_formula",
            "shard_mapping_bound",
            "production_schedule_instantiated",
            "record_sha256",
        ),
        "CP63BoundRequestV1": (
            "schema_version",
            "seed_capsule_body_sha256",
            "seed_ordinal",
            "row_ordinal",
            "logical_request_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "plan_seed_hex",
            "seed_free_request_sha256",
            "runtime_lock_sha256",
            "request_instance_sha256",
            "definition_only",
            "production_execution_authorized",
            "record_sha256",
        ),
        "CP63LifecycleContractV1": (
            "schema_version",
            "lifecycle_id",
            "allowed_states",
            "initial_state",
            "terminal_states",
            "no_retry_drop_replacement_or_topup",
            "infrastructure_failure_invalidates_entire_attempt",
            "timeout_is_semantic_nonreturn",
            "attempt_spent_after_durable_stochastic_output",
            "confirmatory_states_enterable",
            "filesystem_mutation_permitted",
            "production_lifecycle_instantiated",
            "record_sha256",
        ),
        "CP63RawRecordSchemaV1": (
            "schema_version",
            "purpose",
            "exact_outer_keys",
            "child_frame_encoding",
            "public_raw_record_encoding",
            "uint64_encoding",
            "float64_encoding",
            "fraction_encoding",
            "bytes_encoding",
            "four_closed_outcome_arms",
            "preexecution_refusal_codes",
            "execution_failure_codes",
            "complete_kernel_trace_required_for_validated_returns",
            "volatile_supervisor_custody_retained",
            "recompute_owned_semantic_leaf_hashes",
            "future_production_shape_predeclared",
            "infrastructure_failure_has_raw_record",
            "raw_trace_retained_separately",
            "production_schema_frozen",
            "production_records_observed",
            "raw_frame_max_bytes",
            "record_sha256",
        ),
        "CP63RunnerResourceContractV1": (
            "schema_version",
            "seed_capsule_max_bytes",
            "request_frame_max_bytes",
            "raw_frame_max_bytes",
            "stable_trace_max_bytes",
            "stderr_max_bytes",
            "deadline_seconds",
            "termination_grace_seconds",
            "reap_ceiling_seconds",
            "rehearsal_concurrency",
            "rehearsal_launch_limit",
            "external_seed_count",
            "row_count",
            "total_request_count",
            "rejection_proposal_slot_count",
            "sir_proposal_slot_count",
            "total_proposal_slot_count",
            "sir_resampling_draw_count",
            "maximum_event_occurrence_count",
            "maximum_coordinate_count",
            "maximum_future_raw_aggregate_bytes",
            "maximum_future_stable_aggregate_bytes",
            "capacity_receipt_present",
            "production_resources_allocated",
            "record_sha256",
        ),
        "CP63RehearsalCaseV1": (
            "schema_version",
            "case_id",
            "row_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "seed_hex",
            "seed_derivation",
            "seed_is_external_source_draw",
            "seed_is_future_capsule_member",
            "requested_repetitions",
            "maximum_child_launches",
            "production_observation",
            "record_sha256",
        ),
        "CP63RunnerRecomputationRehearsalBundleV1": (
            "schema_version",
            "scope",
            "cp62_source_sha256",
            "cp62_bundle_sha256",
            "cp62_semantic_sha256",
            "seed_capsule_contract",
            "schedule_contract",
            "lifecycle_contract",
            "raw_record_schema",
            "resource_contract",
            "rehearsal_cases",
            "seed_capsule_parser_exposed",
            "seed_capsule_syntax_only",
            "production_seed_ingest_for_execution",
            "arbitrary_seed_execution",
            "campaign_loop_exposed",
            "durable_attempt_writer",
            "shard_mapping_bound",
            "capacity_receipt_present",
            "rehearsal_all_rows_executed",
            "closed_refusal_failure_classification_implemented",
            "full_32768_recomputation_exposed",
            "estimates_computed",
            "intervals_computed",
            "decision_made",
            "production_schema_frozen",
            "production_runner_bound",
            "runner_and_recomputation_blocker_closed",
            "formal_test_28_closed",
            "record_sha256",
        ),
    }
    for name, field_names in expected.items():
        assert tuple(item.name for item in fields(getattr(runner, name))) == field_names


def test_cp63_source_is_stdlib_only_at_import_and_has_no_production_api() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    forbidden_import_roots = {"numpy", "scipy", "torch"}
    imported_roots = set()
    public_function_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                public_function_names.add(node.name)
    assert not forbidden_import_roots & imported_roots
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".", 1)[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots = {node.module.split(".", 1)[0]}
        else:
            continue
        assert roots <= set(sys.stdlib_module_names) | {"__future__"}
    assert (
        not {
            "run_request",
            "run_campaign",
            "execute_request",
            "execute_campaign",
            "write_attempt",
            "authorize_execution",
        }
        & public_function_names
    )


def test_cp63_zero_argument_bundle_builder_cannot_import_or_execute_cp62(
    monkeypatch,
) -> None:
    def bomb() -> None:
        raise AssertionError("definition-only builder crossed the execution boundary")

    monkeypatch.setattr(runner, "_cp62_module", bomb)
    first = runner.cp63_runner_recomputation_rehearsal_bundle()
    second = runner.cp63_runner_recomputation_rehearsal_bundle()
    assert first.record_sha256 == second.record_sha256


def test_cp63_bundle_binds_cp62_and_keeps_every_production_claim_false() -> None:
    bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    assert bundle.cp62_source_sha256 == _CP62_SOURCE_SHA256
    assert bundle.cp62_bundle_sha256 == _CP62_BUNDLE_SHA256
    assert bundle.cp62_semantic_sha256 == _CP62_SEMANTIC_SHA256
    assert bundle.seed_capsule_parser_exposed is True
    assert bundle.seed_capsule_syntax_only is True
    assert bundle.production_seed_ingest_for_execution is False
    assert bundle.arbitrary_seed_execution is False
    assert bundle.campaign_loop_exposed is False
    assert bundle.durable_attempt_writer is False
    assert bundle.shard_mapping_bound is False
    assert bundle.capacity_receipt_present is False
    assert bundle.rehearsal_all_rows_executed is False
    assert bundle.closed_refusal_failure_classification_implemented is False
    assert bundle.production_schema_frozen is False
    assert bundle.production_runner_bound is False
    assert bundle.full_32768_recomputation_exposed is False
    assert bundle.estimates_computed is False
    assert bundle.intervals_computed is False
    assert bundle.decision_made is False
    assert bundle.runner_and_recomputation_blocker_closed is False
    assert bundle.formal_test_28_closed is False


def test_cp63_records_are_sealed_nonpickleable_and_digest_checked() -> None:
    bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    records = (
        bundle,
        bundle.seed_capsule_contract,
        bundle.schedule_contract,
        bundle.lifecycle_contract,
        bundle.raw_record_schema,
        bundle.resource_contract,
        bundle.rehearsal_cases[0],
    )
    for record in records:
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises(TypeError):
            type("HostileSubclass", (type(record),), {})
        with pytest.raises(TypeError):
            record.__reduce_ex__(5)

    observed = runner.cp63_validate_seed_capsule_bytes(_synthetic_seed_capsule_bytes())
    object.__setattr__(observed, "source_method_id", "redigested-lookalike")
    with pytest.raises(ValueError):
        runner.cp63_seed_capsule_canonical_json_bytes(observed)


def test_cp63_contracts_freeze_lifecycle_schema_and_resource_nonclaims() -> None:
    bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    seed = bundle.seed_capsule_contract
    assert seed.seed_count == 2_048
    assert seed.seed_ordinals == tuple(range(1, 2_049))
    assert seed.maximum_capsule_bytes == 131_072
    assert seed.duplicate_values_retained is True
    assert seed.order_is_semantic is True
    assert seed.no_retry_drop_replacement_or_topup is True
    assert seed.source_method_required is True
    assert seed.source_receipt_required is True
    assert seed.acquisition_session_required is True
    assert seed.body_digest_required is True
    assert seed.parser_can_verify_iid_uniform is False
    assert seed.production_values_present is False

    lifecycle = bundle.lifecycle_contract
    assert lifecycle.allowed_states == (
        "DEFINED",
        "REHEARSAL_STARTED",
        "REHEARSAL_PASS",
        "REHEARSAL_FAIL",
        "REHEARSAL_INVALID_INFRA",
    )
    assert lifecycle.initial_state == "DEFINED"
    assert lifecycle.terminal_states == (
        "REHEARSAL_PASS",
        "REHEARSAL_FAIL",
        "REHEARSAL_INVALID_INFRA",
    )
    assert lifecycle.confirmatory_states_enterable is False
    assert lifecycle.filesystem_mutation_permitted is False
    assert lifecycle.no_retry_drop_replacement_or_topup is True
    assert lifecycle.infrastructure_failure_invalidates_entire_attempt is True
    assert lifecycle.timeout_is_semantic_nonreturn is False
    assert lifecycle.attempt_spent_after_durable_stochastic_output is True
    assert lifecycle.production_lifecycle_instantiated is False

    raw = bundle.raw_record_schema
    assert raw.purpose == "development-runner-rehearsal-only"
    assert raw.exact_outer_keys == (
        "schema",
        "purpose",
        "rehearsal_id",
        "repetition",
        "seed_ordinal",
        "row_ordinal",
        "logical_request_ordinal",
        "row_key",
        "fixture_id",
        "strategy",
        "budget",
        "plan_seed_hex",
        "seed_free_request_sha256",
        "request_instance_sha256",
        "runtime_lock_sha256",
        "phase",
        "closed_status",
        "failure_code",
        "kernel_trace",
        "supervisor_custody",
        "raw_sha256",
    )
    assert raw.four_closed_outcome_arms == (
        "returned-before-deadline",
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
        "timeout-at-deadline",
    )
    assert len(raw.preexecution_refusal_codes) == 5
    assert len(raw.execution_failure_codes) == 7
    assert raw.complete_kernel_trace_required_for_validated_returns is True
    assert raw.volatile_supervisor_custody_retained is True
    assert raw.recompute_owned_semantic_leaf_hashes is True
    assert raw.infrastructure_failure_has_raw_record is False
    assert raw.raw_trace_retained_separately is True
    assert raw.future_production_shape_predeclared is True
    assert raw.production_schema_frozen is False
    assert raw.production_records_observed is False

    resource = bundle.resource_contract
    expected_values = {
        "seed_capsule_max_bytes": 131_072,
        "request_frame_max_bytes": 65_536,
        "raw_frame_max_bytes": 16_777_216,
        "stable_trace_max_bytes": 8_388_608,
        "stderr_max_bytes": 1_048_576,
        "deadline_seconds": 300,
        "termination_grace_seconds": 2,
        "reap_ceiling_seconds": 5,
        "rehearsal_concurrency": 1,
        "rehearsal_launch_limit": 32,
        "external_seed_count": 2_048,
        "row_count": 16,
        "total_request_count": 32_768,
        "rejection_proposal_slot_count": 348_160,
        "sir_proposal_slot_count": 2_785_280,
        "total_proposal_slot_count": 3_133_440,
        "sir_resampling_draw_count": 16_384,
        "maximum_event_occurrence_count": 4_700_160,
        "maximum_coordinate_count": 7_833_600,
        "maximum_future_raw_aggregate_bytes": 549_755_813_888,
        "maximum_future_stable_aggregate_bytes": 274_877_906_944,
    }
    for name, value in expected_values.items():
        assert getattr(resource, name) == value
    assert resource.capacity_receipt_present is False
    assert resource.production_resources_allocated is False


def test_cp63_seed_capsule_parser_observes_syntax_but_never_source_iid() -> None:
    payload = _synthetic_seed_capsule_bytes()
    observed = runner.cp63_validate_seed_capsule_bytes(payload)
    assert observed.seed_count == 2_048
    assert observed.seed_ordinals == tuple(range(1, 2_049))
    assert len(observed.ordered_seed_values) == 2_048
    assert observed.syntactically_valid is True
    assert observed.source_custody_digest_bound is True
    assert observed.iid_uniform_with_replacement_verified is False
    assert observed.production_execution_authorized is False
    assert observed.canonical_byte_count == len(payload)
    assert runner.cp63_seed_capsule_canonical_json_bytes(observed) == payload


@pytest.mark.parametrize(
    "payload",
    (
        None,
        "not-bytes",
        b"",
        b"{}\n",
        b"\xef\xbb\xbf{}",
        b'{"schema":"one","schema":"two"}',
        b"x" * 131_073,
    ),
)
def test_cp63_seed_capsule_parser_rejects_noncanonical_or_oversized_input(
    payload,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_validate_seed_capsule_bytes(payload)


@pytest.mark.parametrize(
    "change",
    (
        {"schema": "wrong"},
        {"purpose": "development"},
        {"seed_count": 2_047},
        {"seed_ordinals": list(range(2_048))},
        {"seed_encoding": "decimal"},
        {"ordered_seed_values": ["0" * 16] * 2_047},
        {"ordered_seed_values": ["0" * 15 + "G"] * 2_048},
        {"source_method_id": ""},
        {"source_receipt_sha256": "0" * 63},
        {"acquisition_session_sha256": "z" * 64},
    ),
)
def test_cp63_seed_capsule_parser_rejects_field_tamper(change) -> None:
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_validate_seed_capsule_bytes(_synthetic_seed_capsule_bytes(**change))


def test_cp63_seed_capsule_parser_rejects_wrong_body_digest() -> None:
    value = json.loads(_synthetic_seed_capsule_bytes().decode("ascii"))
    value["body_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        runner.cp63_validate_seed_capsule_bytes(_plain_json_bytes(value))


def test_cp63_duplicate_seed_values_are_retained_at_distinct_ordinals() -> None:
    values = [f"{ordinal:016x}" for ordinal in range(2_048)]
    values[1] = values[0]
    observed = runner.cp63_validate_seed_capsule_bytes(
        _synthetic_seed_capsule_bytes(ordered_seed_values=values)
    )
    assert observed.ordered_seed_values[0] == observed.ordered_seed_values[1]
    first = runner.cp63_bound_request(observed, 1)
    seventeenth = runner.cp63_bound_request(observed, 17)
    assert first.plan_seed_hex == seventeenth.plan_seed_hex
    assert first.seed_ordinal == 1
    assert seventeenth.seed_ordinal == 2
    assert first.request_instance_sha256 != seventeenth.request_instance_sha256


@pytest.mark.parametrize("logical_ordinal", (False, 0, 32_769, 1.0, "1", None))
def test_cp63_bound_request_rejects_noninteger_or_out_of_range_ordinal(
    logical_ordinal,
) -> None:
    observed = runner.cp63_validate_seed_capsule_bytes(_synthetic_seed_capsule_bytes())
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_bound_request(observed, logical_ordinal)


@pytest.mark.parametrize(
    "logical_ordinal,seed_ordinal,row_ordinal,plan_seed_hex",
    (
        (1, 1, 1, "0000000000000000"),
        (16, 1, 16, "0000000000000000"),
        (17, 2, 1, "0000000000000001"),
        (32_768, 2_048, 16, "00000000000007ff"),
    ),
)
def test_cp63_bound_request_uses_exact_seed_major_unmodified_plan_seed(
    logical_ordinal,
    seed_ordinal,
    row_ordinal,
    plan_seed_hex,
) -> None:
    observed = runner.cp63_validate_seed_capsule_bytes(_synthetic_seed_capsule_bytes())
    request = runner.cp63_bound_request(observed, logical_ordinal)
    assert request.logical_request_ordinal == logical_ordinal
    assert request.seed_ordinal == seed_ordinal
    assert request.row_ordinal == row_ordinal
    assert request.plan_seed_hex == plan_seed_hex
    assert request.definition_only is True
    assert request.production_execution_authorized is False
    identity = {
        name: getattr(request, name)
        for name in (
            "schema_version",
            "seed_capsule_body_sha256",
            "seed_ordinal",
            "row_ordinal",
            "logical_request_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "plan_seed_hex",
            "seed_free_request_sha256",
            "runtime_lock_sha256",
        )
    }
    expected = hashlib.sha256(
        b"cp63-test28-bound-request-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()
    assert request.request_instance_sha256 == expected


def test_cp63_schedule_is_exact_seed_major_and_shard_neutral() -> None:
    schedule = runner.cp63_schedule_contract()
    assert schedule.seed_count == 2_048
    assert schedule.row_count == 16
    assert schedule.total_request_count == 32_768
    assert schedule.row_ordinals == tuple(range(1, 17))
    assert schedule.logical_request_order == "(seed_ordinal-1)*16+row_ordinal"
    assert schedule.logical_request_ordinal_min == 1
    assert schedule.logical_request_ordinal_max == 32_768
    assert schedule.plan_seed_assignment == "external-seed-value-unchanged"
    assert (
        schedule.fixture_strategy_budget_or_shard_hashing_before_plan_seed_assignment
        is False
    )
    assert schedule.shard_mapping_bound is False
    assert schedule.production_schedule_instantiated is False


def test_cp63_rehearsal_inventory_is_all_rows_twice_and_not_external() -> None:
    bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    assert tuple(case.case_id for case in bundle.rehearsal_cases) == _REHEARSAL_CASE_IDS
    assert tuple(case.row_ordinal for case in bundle.rehearsal_cases) == tuple(
        range(1, 17)
    )
    expected_shapes = tuple(
        (fixture_id, strategy, budget)
        for fixture_id in ("T28-M1-Q", "T28-M2-Q")
        for strategy, budgets in (
            ("bounded-rejection", (1, 4, 16, 64)),
            ("fixed-budget-sir", (8, 32, 128, 512)),
        )
        for budget in budgets
    )
    assert (
        tuple(
            (case.fixture_id, case.strategy, case.budget)
            for case in bundle.rehearsal_cases
        )
        == expected_shapes
    )
    assert len({case.record_sha256 for case in bundle.rehearsal_cases}) == 16
    for case in bundle.rehearsal_cases:
        assert case.schema_version == runner.CP63_TEST28_SCHEMA_VERSION
        assert case.row_key == (
            f"row-{case.row_ordinal:02d}/{case.fixture_id}/{case.strategy}/"
            f"budget-{case.budget}"
        )
        assert case.seed_hex == _REHEARSAL_SEED_HEX
        assert case.seed_derivation == (
            "first-eight-bytes-big-endian-of-sha256(cp63-test28-all-row-"
            "rehearsal-seed-v1\\0)"
        )
        assert case.seed_is_external_source_draw is False
        assert case.seed_is_future_capsule_member is False
        assert case.requested_repetitions == 2
        assert case.maximum_child_launches == 2
        assert case.production_observation is False


@pytest.mark.parametrize(
    "case_id",
    (None, False, 1, "", "rehearsal-row-00", "rehearsal-row-17", "production"),
)
def test_cp63_runner_rejects_every_nonfrozen_case_identifier(case_id) -> None:
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_run_rehearsal_case(case_id)


def _install_fake_rehearsal_boundary(monkeypatch, supervise) -> None:
    case = runner.cp63_runner_recomputation_rehearsal_bundle().rehearsal_cases[0]
    row = SimpleNamespace(seed_free_request_sha256="a" * 64)
    monkeypatch.setattr(runner, "_case_and_row", lambda _case_id: (case, row))
    monkeypatch.setattr(runner, "_supervise_rehearsal_case", supervise)
    monkeypatch.setattr(runner, "_REHEARSAL_LAUNCH_COUNT", 0)
    monkeypatch.setattr(
        runner,
        "_REHEARSAL_CASE_LAUNCH_COUNTS",
        {case_id: 0 for case_id in _REHEARSAL_CASE_IDS},
    )
    monkeypatch.setattr(runner, "_REHEARSAL_RUNNING", False)


def test_cp63_launch_gate_assigns_exact_repetitions_and_refuses_a_third(
    monkeypatch,
) -> None:
    observed = []

    def supervise(case, row, repetition, launch_ordinal):
        del case, row
        observed.append((repetition, launch_ordinal))
        return b"synthetic"

    _install_fake_rehearsal_boundary(monkeypatch, supervise)
    assert runner.cp63_run_rehearsal_case("rehearsal-row-01") == b"synthetic"
    assert runner.cp63_run_rehearsal_case("rehearsal-row-01") == b"synthetic"
    assert observed == [(1, 1), (2, 2)]
    with pytest.raises(runner.CP63RunnerRehearsalError) as captured:
        runner.cp63_run_rehearsal_case("rehearsal-row-01")
    assert captured.value.code == "REHEARSAL_CASE_LAUNCH_LIMIT_REACHED"
    assert observed == [(1, 1), (2, 2)]


def test_cp63_failed_launch_is_spent_and_gate_reopens_without_retry(
    monkeypatch,
) -> None:
    observed = []

    def supervise(case, row, repetition, launch_ordinal):
        del case, row
        observed.append((repetition, launch_ordinal))
        raise runner.CP63RunnerRehearsalError("SYNTHETIC_INFRA", "synthetic")

    _install_fake_rehearsal_boundary(monkeypatch, supervise)
    for expected_repetition in (1, 2):
        with pytest.raises(runner.CP63RunnerRehearsalError) as captured:
            runner.cp63_run_rehearsal_case("rehearsal-row-01")
        assert captured.value.code == "SYNTHETIC_INFRA"
        assert runner._REHEARSAL_RUNNING is False
        assert observed[-1] == (expected_repetition, expected_repetition)
    with pytest.raises(runner.CP63RunnerRehearsalError) as captured:
        runner.cp63_run_rehearsal_case("rehearsal-row-01")
    assert captured.value.code == "REHEARSAL_CASE_LAUNCH_LIMIT_REACHED"
    assert len(observed) == 2


@pytest.mark.parametrize(
    "running,total,per_case,code",
    (
        (True, 0, 0, "REHEARSAL_CONCURRENCY_REFUSED"),
        (False, 32, 0, "REHEARSAL_LAUNCH_LIMIT_REACHED"),
        (False, 1, 2, "REHEARSAL_CASE_LAUNCH_LIMIT_REACHED"),
    ),
)
def test_cp63_launch_gate_refusals_never_cross_the_spawn_boundary(
    monkeypatch,
    running,
    total,
    per_case,
    code,
) -> None:
    def bomb(*_args):
        raise AssertionError("refused launch crossed the supervisor boundary")

    _install_fake_rehearsal_boundary(monkeypatch, bomb)
    runner._REHEARSAL_RUNNING = running
    runner._REHEARSAL_LAUNCH_COUNT = total
    runner._REHEARSAL_CASE_LAUNCH_COUNTS["rehearsal-row-01"] = per_case
    with pytest.raises(runner.CP63RunnerRehearsalError) as captured:
        runner.cp63_run_rehearsal_case("rehearsal-row-01")
    assert captured.value.code == code


def test_cp63_launch_gate_is_thread_safe_while_one_supervisor_is_active(
    monkeypatch,
) -> None:
    started = threading.Event()
    release = threading.Event()
    worker_result = []

    def supervise(*_args):
        started.set()
        assert release.wait(timeout=5)
        return b"synthetic"

    _install_fake_rehearsal_boundary(monkeypatch, supervise)

    def worker() -> None:
        worker_result.append(runner.cp63_run_rehearsal_case("rehearsal-row-01"))

    thread = threading.Thread(target=worker)
    thread.start()
    assert started.wait(timeout=5)
    try:
        with pytest.raises(runner.CP63RunnerRehearsalError) as captured:
            runner.cp63_run_rehearsal_case("rehearsal-row-01")
        assert captured.value.code == "REHEARSAL_CONCURRENCY_REFUSED"
    finally:
        release.set()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert worker_result == [b"synthetic"]


def test_cp63_exact_16_by_2_rehearsal_has_stable_pair_parity(
    rehearsal_frames,
) -> None:
    assert set(rehearsal_frames) == set(_REHEARSAL_CASE_IDS)
    raw_keys = set(
        runner.cp63_runner_recomputation_rehearsal_bundle().raw_record_schema.exact_outer_keys
    )
    stable_keys = raw_keys - {"repetition", "supervisor_custody", "raw_sha256"}
    pair_hashes = []
    for row_ordinal, case_id in enumerate(_REHEARSAL_CASE_IDS, 1):
        repetitions = rehearsal_frames[case_id]
        assert len(repetitions) == 2
        raw_records = []
        for repetition, (payload, raw) in enumerate(repetitions, 1):
            assert payload == _plain_json_bytes(raw)
            assert set(raw) == raw_keys
            assert raw["repetition"] == repetition
            assert raw["row_ordinal"] == row_ordinal
            assert raw["logical_request_ordinal"] == row_ordinal
            assert raw["seed_ordinal"] == 1
            assert raw["plan_seed_hex"] == _REHEARSAL_SEED_HEX
            assert raw["runtime_lock_sha256"] == _RUNTIME_LOCK_SHA256
            assert raw["request_instance_sha256"] == (
                _rehearsal_request_instance_sha256(raw)
            )
            assert raw["raw_sha256"] == _raw_record_digest(raw)
            assert raw["phase"] == "returned-before-deadline"
            assert raw["failure_code"] is None
            assert set(raw["kernel_trace"]) == {"semantic", "volatile_custody"}
            supervisor = raw["supervisor_custody"]
            child_payload = {
                key: raw[key]
                for key in raw_keys
                if key not in {"supervisor_custody", "raw_sha256"}
            }
            child_bytes = _plain_json_bytes(child_payload)
            child_frame = len(child_bytes).to_bytes(8, "big") + child_bytes
            assert supervisor["frame_bytes"] == len(child_frame)
            assert (
                supervisor["child_frame_sha256"]
                == hashlib.sha256(child_frame).hexdigest()
            )
            assert supervisor["stderr_bytes"] == 0
            assert supervisor["stderr_hex"] == ""
            assert supervisor["stderr_sha256"] == hashlib.sha256(b"").hexdigest()
            assert supervisor["exit_code"] == 0
            assert supervisor["term_signal"] is None
            assert supervisor["completion_strictly_before_deadline"] is True
            assert supervisor["exact_one_frame"] is True
            assert supervisor["termination_attempted"] is False
            assert supervisor["termination_signal_delivered"] is False
            assert supervisor["kill_attempted"] is False
            assert supervisor["reaped"] is True
            raw_records.append(raw)
        stable = [runner.cp63_project_stable_trace(raw) for raw in raw_records]
        assert raw_records[0]["raw_sha256"] != raw_records[1]["raw_sha256"]
        assert stable[0] == stable[1], case_id
        assert set(stable[0]) == stable_keys
        assert stable[0]["kernel_trace"] == raw_records[0]["kernel_trace"]["semantic"]
        stable_bytes = runner.cp63_stable_trace_canonical_json_bytes(stable[0])
        assert stable_bytes == _plain_json_bytes(stable[0])
        stable_sha256 = hashlib.sha256(
            b"cp63-test28-stable-trace-v1\0" + stable_bytes
        ).hexdigest()
        assert runner.cp63_stable_trace_sha256(stable[0]) == stable_sha256
        assert runner.cp63_stable_trace_sha256(stable[1]) == stable_sha256
        pair_hashes.append(stable_sha256)
    assert len(set(pair_hashes)) == 16


def test_cp63_real_stable_traces_recompute_to_one_identical_receipt_per_repetition(
    rehearsal_frames,
) -> None:
    stable_payloads_by_repetition = []
    traces = []
    for repetition in range(2):
        payloads = []
        repetition_traces = []
        for case_id in _REHEARSAL_CASE_IDS:
            raw = rehearsal_frames[case_id][repetition][1]
            stable = runner.cp63_project_stable_trace(raw)
            payload = runner.cp63_stable_trace_canonical_json_bytes(stable)
            assert (
                oracle.cp63_independently_validate_stable_trace_bytes(payload) == stable
            )
            payloads.append(payload)
            repetition_traces.append(stable)
        stable_payloads_by_repetition.append(tuple(payloads))
        traces.append(tuple(repetition_traces))

    receipts = tuple(
        oracle.cp63_recompute_rehearsal(payloads)
        for payloads in stable_payloads_by_repetition
    )
    assert oracle.cp63_recomputation_canonical_json_bytes(
        receipts[0]
    ) == oracle.cp63_recomputation_canonical_json_bytes(receipts[1])
    assert oracle.cp63_recomputation_sha256(
        receipts[0]
    ) == oracle.cp63_recomputation_sha256(receipts[1])
    receipt = receipts[0]
    assert receipt.request_count == 16
    assert receipt.row_ordinals == tuple(range(1, 17))
    assert receipt.logical_request_ordinals == tuple(range(1, 17))
    assert len(receipt.stable_trace_sha256s) == 16
    assert len(receipt.compact_observation_sha256s) == 16
    assert len(receipt.observable_contributions) == 72
    assert sum(receipt.observable_contributions) == 16
    assert len(receipt.first_attempt_contributions) == 170
    selected_rejection_count = sum(
        trace["closed_status"] == "returned-rejection-selected-before-deadline"
        for trace in traces[0]
    )
    assert sum(receipt.first_attempt_contributions) == selected_rejection_count
    assert len(receipt.selected_feature_present) == 312
    assert len(receipt.selected_feature_values) == 312
    expected_selected_feature_count = sum(
        (6 if trace["fixture_id"] == "T28-M1-Q" else 33)
        for trace in traces[0]
        if trace["closed_status"]
        in {
            "returned-rejection-selected-before-deadline",
            "returned-sir-selected-before-deadline",
        }
    )
    assert sum(receipt.selected_feature_present) == expected_selected_feature_count
    assert all(
        present == (value is not None)
        for present, value in zip(
            receipt.selected_feature_present,
            receipt.selected_feature_values,
            strict=True,
        )
    )
    assert receipt.missing_count == 0
    assert receipt.duplicate_count == 0
    assert receipt.invalid_count == 0
    assert receipt.independent_parser is True
    assert receipt.runner_source_imported is False
    assert receipt.intervals_computed is False
    assert receipt.decision_made is False

    reordered = list(stable_payloads_by_repetition[0])
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_recompute_rehearsal(tuple(reordered))
    duplicated = list(stable_payloads_by_repetition[0])
    duplicated[1] = duplicated[0]
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_recompute_rehearsal(tuple(duplicated))

    case_receipts = []
    runner_bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    for index, case_id in enumerate(_REHEARSAL_CASE_IDS):
        stable_payload = stable_payloads_by_repetition[0][index]
        assert stable_payload == stable_payloads_by_repetition[1][index]
        compact_records = tuple(
            oracle.cp63_compact_observation(
                stable_payloads_by_repetition[repetition][index]
            )
            for repetition in range(2)
        )
        compact_payloads = tuple(
            oracle.cp63_recomputation_canonical_json_bytes(record)
            for record in compact_records
        )
        assert compact_payloads[0] == compact_payloads[1]
        assert compact_records[0].record_sha256 == compact_records[1].record_sha256
        assert oracle.cp63_recomputation_sha256(
            compact_records[0]
        ) == oracle.cp63_recomputation_sha256(compact_records[1])
        raw_repetitions = []
        for repetition, (raw_payload, raw) in enumerate(rehearsal_frames[case_id], 1):
            raw_repetitions.append(
                {
                    "repetition": repetition,
                    "public_raw_byte_count": len(raw_payload),
                    "public_raw_plain_sha256": hashlib.sha256(raw_payload).hexdigest(),
                    "raw_record_sha256": raw["raw_sha256"],
                    "child_frame_byte_count": raw["supervisor_custody"]["frame_bytes"],
                    "child_frame_sha256": raw["supervisor_custody"][
                        "child_frame_sha256"
                    ],
                }
            )
        case_receipts.append(
            {
                "case_id": case_id,
                "row_ordinal": index + 1,
                "case_record_sha256": runner_bundle.rehearsal_cases[
                    index
                ].record_sha256,
                "closed_status": traces[0][index]["closed_status"],
                "raw_repetitions": raw_repetitions,
                "stable_trace_byte_count": len(stable_payload),
                "stable_trace_plain_sha256": hashlib.sha256(stable_payload).hexdigest(),
                "stable_trace_sha256": runner.cp63_stable_trace_sha256(
                    traces[0][index]
                ),
                "compact_canonical_byte_count": len(compact_payloads[0]),
                "compact_canonical_plain_sha256": hashlib.sha256(
                    compact_payloads[0]
                ).hexdigest(),
                "compact_record_sha256": compact_records[0].record_sha256,
                "compact_public_sha256": oracle.cp63_recomputation_sha256(
                    compact_records[0]
                ),
            }
        )

    semantic_case_receipts = [
        {
            key: item[key]
            for key in (
                "case_id",
                "row_ordinal",
                "stable_trace_byte_count",
                "stable_trace_plain_sha256",
                "stable_trace_sha256",
                "compact_canonical_byte_count",
                "compact_canonical_plain_sha256",
                "compact_record_sha256",
                "compact_public_sha256",
            )
        }
        for item in case_receipts
    ]
    assert (
        tuple(
            (
                item["row_ordinal"],
                item["stable_trace_byte_count"],
                item["stable_trace_plain_sha256"],
                item["stable_trace_sha256"],
                item["compact_canonical_byte_count"],
                item["compact_canonical_plain_sha256"],
                item["compact_record_sha256"],
                item["compact_public_sha256"],
            )
            for item in semantic_case_receipts
        )
        == _EXPECTED_SEMANTIC_CASE_RECEIPTS
    )

    receipt_payloads = tuple(
        oracle.cp63_recomputation_canonical_json_bytes(item) for item in receipts
    )
    assert receipt_payloads[0] == receipt_payloads[1]
    recomputation_receipt = {
        "canonical_byte_count": len(receipt_payloads[0]),
        "canonical_plain_sha256": hashlib.sha256(receipt_payloads[0]).hexdigest(),
        "record_sha256": receipts[0].record_sha256,
        "public_sha256": oracle.cp63_recomputation_sha256(receipts[0]),
    }
    assert (
        recomputation_receipt["canonical_byte_count"],
        recomputation_receipt["canonical_plain_sha256"],
        recomputation_receipt["record_sha256"],
        recomputation_receipt["public_sha256"],
    ) == _EXPECTED_RECOMPUTATION_RECEIPT
    semantic_pin_receipt = {
        "schema": "cp63-test28-semantic-pin-receipt-v1",
        "runner_source_sha256": _RUNNER_SOURCE_SHA256,
        "independent_source_sha256": _INDEPENDENT_SOURCE_SHA256,
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
        "rehearsal_id": "cp63-all-row-rehearsal-v1",
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "launch_count": 16,
        "case_receipts": semantic_case_receipts,
        "recomputation_receipt": recomputation_receipt,
        "receipt_sha256": "0" * 64,
    }
    semantic_pin_receipt["receipt_sha256"] = hashlib.sha256(
        b"cp63-test28-semantic-pin-receipt-v1\0"
        + _plain_json_bytes(semantic_pin_receipt)
    ).hexdigest()
    assert (
        semantic_pin_receipt["receipt_sha256"] == _EXPECTED_SEMANTIC_PIN_RECEIPT_SHA256
    )
    independent_bundle = oracle.cp63_independent_recomputation_bundle()
    independent_bundle_payload = oracle.cp63_recomputation_canonical_json_bytes(
        independent_bundle
    )
    acceptance_receipt = {
        "schema": "cp63-test28-16x2-acceptance-receipt-v1",
        "runner_source_sha256": _RUNNER_SOURCE_SHA256,
        "independent_source_sha256": _INDEPENDENT_SOURCE_SHA256,
        "runner_bundle_record_sha256": runner_bundle.record_sha256,
        "cp62_source_sha256": _CP62_SOURCE_SHA256,
        "cp62_bundle_sha256": _CP62_BUNDLE_SHA256,
        "cp62_semantic_sha256": _CP62_SEMANTIC_SHA256,
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
        "rehearsal_id": "cp63-all-row-rehearsal-v1",
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "launch_count": 32,
        "row_count": 16,
        "repetitions_per_row": 2,
        "case_receipts": case_receipts,
        "repetition_blind_554_receipt": {
            "canonical_byte_count": len(receipt_payloads[0]),
            "canonical_plain_sha256": hashlib.sha256(receipt_payloads[0]).hexdigest(),
            "record_sha256": receipts[0].record_sha256,
            "public_sha256": oracle.cp63_recomputation_sha256(receipts[0]),
            "repetitions_equal": True,
            "estimand_count": 554,
            "observable_estimand_count": 72,
            "rejection_first_attempt_estimand_count": 170,
            "selected_feature_estimand_count": 312,
        },
        "independent_554_inventory": {
            "canonical_byte_count": len(independent_bundle_payload),
            "canonical_plain_sha256": hashlib.sha256(
                independent_bundle_payload
            ).hexdigest(),
            "record_sha256": independent_bundle.record_sha256,
            "public_sha256": oracle.cp63_recomputation_sha256(independent_bundle),
        },
        "receipt_sha256": "0" * 64,
    }
    acceptance_receipt["receipt_sha256"] = hashlib.sha256(
        b"cp63-test28-16x2-acceptance-receipt-v1\0"
        + _plain_json_bytes(acceptance_receipt)
    ).hexdigest()
    print(
        "CP63_IMMUTABLE_ACCEPTANCE_RECEIPT="
        + _plain_json_bytes(acceptance_receipt).decode("ascii")
    )


def test_cp63_real_raw_record_rejects_digest_frame_and_repetition_tamper(
    rehearsal_frames,
) -> None:
    original = rehearsal_frames["rehearsal-row-01"][0][1]

    wrong_raw_digest = copy.deepcopy(original)
    wrong_raw_digest["raw_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        runner.cp63_validate_raw_record_bytes(_plain_json_bytes(wrong_raw_digest))

    wrong_frame_digest = copy.deepcopy(original)
    wrong_frame_digest["supervisor_custody"]["child_frame_sha256"] = "0" * 64
    wrong_frame_digest["raw_sha256"] = _raw_record_digest(wrong_frame_digest)
    with pytest.raises(ValueError):
        runner.cp63_validate_raw_record_bytes(_plain_json_bytes(wrong_frame_digest))

    wrong_repetition = copy.deepcopy(original)
    wrong_repetition["repetition"] = 3
    with pytest.raises(ValueError):
        runner.cp63_validate_raw_record_bytes(
            _redigest_raw_after_child_edit(wrong_repetition)
        )


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("schema", "wrong-schema"),
        ("purpose", "production"),
        ("rehearsal_id", "wrong-rehearsal"),
        ("seed_ordinal", 2),
        ("logical_request_ordinal", 2),
        ("row_key", "wrong-row"),
        ("fixture_id", "T28-M2-Q"),
        ("strategy", "fixed-budget-sir"),
        ("budget", 4),
        ("plan_seed_hex", "0" * 16),
        ("seed_free_request_sha256", "0" * 64),
        ("request_instance_sha256", "0" * 64),
        ("runtime_lock_sha256", "0" * 64),
        ("phase", "timeout-at-deadline"),
        ("closed_status", "timeout-censored-at-deadline"),
        ("failure_code", "plan_validation_refusal"),
    ),
)
def test_cp63_real_stable_trace_redigested_outer_tamper_is_rejected(
    rehearsal_frames,
    field,
    replacement,
) -> None:
    trace = runner.cp63_project_stable_trace(rehearsal_frames["rehearsal-row-01"][0][1])
    trace[field] = replacement
    payload = _plain_json_bytes(trace)
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_stable_trace_canonical_json_bytes(trace)
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(payload)


@pytest.mark.parametrize("tamper", ("wrong-digest", "wrong-field", "stale-body"))
def test_cp63_real_selected_configuration_owned_digest_is_independently_checked(
    rehearsal_frames,
    tamper,
) -> None:
    selected = None
    for case_id in _REHEARSAL_CASE_IDS:
        candidate = runner.cp63_project_stable_trace(rehearsal_frames[case_id][0][1])
        configuration = candidate["kernel_trace"].get("selected_configuration")
        has_coordinate = configuration is not None and any(
            event["coordinates_float64_be"] for event in configuration["events"]
        )
        if configuration is not None and (tamper != "stale-body" or has_coordinate):
            selected = candidate
            break
    assert selected is not None
    trace = copy.deepcopy(selected)
    configuration = trace["kernel_trace"]["selected_configuration"]
    if tamper == "wrong-digest":
        configuration["cp62_configuration_sha256"] = "0" * 64
    elif tamper == "wrong-field":
        digest = configuration.pop("cp62_configuration_sha256")
        configuration["cp63_configuration_sha256"] = digest
    else:
        events = configuration["events"]
        coordinates = next(
            event["coordinates_float64_be"]
            for event in events
            if event["coordinates_float64_be"]
        )
        coordinates[0]["$float64_be"] = (
            "3ff0000000000000"
            if coordinates[0]["$float64_be"] != "3ff0000000000000"
            else "0000000000000000"
        )
    semantic = trace["kernel_trace"]
    semantic.pop("cp62_semantic_trace_sha256")
    semantic["cp62_semantic_trace_sha256"] = hashlib.sha256(
        b"cp62-test28-semantic-kernel-trace-v1\0" + _plain_json_bytes(semantic)
    ).hexdigest()
    payload = _plain_json_bytes(trace)
    with pytest.raises((TypeError, ValueError)):
        runner.cp63_stable_trace_canonical_json_bytes(trace)
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(payload)


@pytest.mark.parametrize(
    "tamper",
    (
        "runtime-observation",
        "derived-stream-seed",
        "resource-preflight",
        "quota-proof",
        "sir-normalized-weights",
        "sir-warning",
    ),
)
def test_cp63_real_independent_parser_replays_full_returned_semantics(
    rehearsal_frames,
    tamper,
) -> None:
    case_id = (
        "rehearsal-row-05"
        if tamper in {"sir-normalized-weights", "sir-warning"}
        else "rehearsal-row-01"
    )
    trace = copy.deepcopy(
        runner.cp63_project_stable_trace(rehearsal_frames[case_id][0][1])
    )
    semantic = trace["kernel_trace"]
    if tamper == "runtime-observation":
        semantic["runtime_observation"]["python_version"] = "0.0.0"
    elif tamper == "derived-stream-seed":
        semantic["proposal_seed_hex"] = (
            "0000000000000000"
            if semantic["proposal_seed_hex"] != "0000000000000000"
            else "0000000000000001"
        )
    elif tamper == "resource-preflight":
        semantic["resource_preflight"]["worst_case_occurrences"] += 1
    elif tamper == "quota-proof":
        attempt = semantic["attempts"][0]
        quota = attempt["quota"]
        quota["exact_exponential_bernoulli_certified"] = not quota[
            "exact_exponential_bernoulli_certified"
        ]
        _redigest_owned_json_leaf(
            quota,
            digest_field="cp62_quota_sha256",
            domain=b"cp62-test28-quota-certificate-v1",
        )
        _redigest_owned_json_leaf(
            attempt,
            digest_field="cp62_attempt_sha256",
            domain=b"cp62-test28-rejection-attempt-v1",
        )
    elif tamper == "sir-normalized-weights":
        particles = semantic["particles"]
        left, right = next(
            (left, right)
            for left in range(len(particles))
            for right in range(left + 1, len(particles))
            if particles[left]["normalized_weight_float64_be"]
            != particles[right]["normalized_weight_float64_be"]
        )
        (
            particles[left]["normalized_weight_float64_be"],
            particles[right]["normalized_weight_float64_be"],
        ) = (
            particles[right]["normalized_weight_float64_be"],
            particles[left]["normalized_weight_float64_be"],
        )
        (
            semantic["normalized_weights_float64_be"][left],
            semantic["normalized_weights_float64_be"][right],
        ) = (
            semantic["normalized_weights_float64_be"][right],
            semantic["normalized_weights_float64_be"][left],
        )
        for index in (left, right):
            _redigest_owned_json_leaf(
                particles[index],
                digest_field="cp62_particle_sha256",
                domain=b"cp62-test28-sir-particle-v1",
            )
    else:
        semantic["ess_warning"] = not semantic["ess_warning"]
    _redigest_owned_json_leaf(
        semantic,
        digest_field="cp62_semantic_trace_sha256",
        domain=b"cp62-test28-semantic-kernel-trace-v1",
    )
    _assert_runner_and_independent_reject_stable(trace)
