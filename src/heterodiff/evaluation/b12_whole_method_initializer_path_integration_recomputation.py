"""Separate recomputation for the initializer-to-path beta successor.

This module deliberately does not import the successor's primary source.  It
re-executes the accepted predecessor, initializer, typed transform, and bounded
numerical path, then emits the same canonical core document independently.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import stat
import struct
from typing import Mapping, Tuple

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_tilt
from heterodiff.evaluation import formal_test29_test30_single_macrostep_integration as single
from heterodiff.evaluation import formal_test29_test30_two_macrostep_path_qualification as two
from heterodiff.evaluation import formal_test30_synthetic_coupled_path_qualification as test30
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as cp62
from heterodiff.processes import certified_initial_score_provider_v1 as score_facade
from heterodiff.processes import plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as initializer
from heterodiff.processes import formal_test29_finite_acyclic_route_oracle as test29
from heterodiff.theory.configuration_reference import TransformedEvent


SCHEMA_VERSION = "heterodiff-b12-whole-method-initializer-path-successor-v1"
CORE_SCHEMA = "heterodiff-b12-whole-method-initializer-path-core-v1"
STATE = "OFFLINE_NONCONFIRMATORY_WHOLE_METHOD_BETA_INTEGRATED"
TRANSFORM_POLICY_ID = (
    "TEST28-TYPE-PARITY-FIRST-COORDINATE-ZERO-DIM-ZERO-TO-PATH-STATE-V1"
)
PATH_POLICY_ID = "BOUNDED-TWO-MACROSTEP-HEUN-EDIT-PATH-V1"
PROPOSED_TASK = (
    "Produce whole-method beta: initializer, continuous path, jump/edit law, "
    "and sampler integrated."
)
FROZEN_WORDS = (2, 27)
MACROSTEP_WIDTH = 0.25
RUN_ID = 29_032
MAX_TRANSFORM_EVENTS = 10_000
PREDECESSOR_MACHINE_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)
PREDECESSOR_MACHINE_SHA256 = (
    "a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b"
)
PREDECESSOR_RECORD_SHA256 = (
    "451ef6059fea8cb2f98128c388056bcd82739645a97dfdd56021055744cb04af"
)
PREDECESSOR_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)
FROZEN_INPUT_SCHEMA = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
FROZEN_INPUT_DOMAIN = "heterodiff-b12-whole-method-nonconfirmatory-input-v1"
FROZEN_INITIALIZER_ROW_ORDINAL = 5
FROZEN_INITIALIZER_SEED = int("12a5228200019dae", 16)
FROZEN_CHECKPOINT_STEP = 256
FROZEN_SUPPLIED_INPUT_SHA256 = (
    "f7e213442d073f88df73d2b33c21e43add4269a8a45b07714bfbd60b4b4ff971"
)
REAL_RESIDUAL_IDS = (
    "B02_REAL_DATA_ACQUISITION",
    "B03_REAL_DATA_SPLIT_AND_ESCROW",
    "B08_RUNTIME_COMPUTE_ENVELOPE",
    "B09_REAL_LICENSE_PRIVACY_APPROVALS",
    "F172_PROSPECTIVE_FREEZE_AFTER_TEST_SEAL",
    "ALL_PREEXECUTION_ARTIFACTS_ACCEPTED",
    "PRIMARY_64_DIMENSION_CONTEXT_ENCODER",
    "PRIMARY_DOMAIN_SCALE_RUNTIME",
    "PRIMARY_ADAPTER_RETAIL",
    "PRIMARY_ADAPTER_PHYSIONET",
    "CONTROL_ADAPTER_RETAIL",
    "CONTROL_ADAPTER_PHYSIONET",
    "LITERATURE_FAMILY_ADAPTER_RETAIL",
    "LITERATURE_FAMILY_ADAPTER_PHYSIONET",
    "CSDI_AUTHOR_EXTENSION_1",
    "CSDI_AUTHOR_EXTENSION_2",
    "CSDI_AUTHOR_EXTENSION_3",
    "CSDI_AUTHOR_EXTENSION_4",
    "EDITPP_AUTHOR_EXTENSION_1",
    "EDITPP_AUTHOR_EXTENSION_2",
    "EDITPP_AUTHOR_EXTENSION_3",
    "EDITPP_AUTHOR_EXTENSION_4",
    "PRODUCTION_SCHEMA_EXTERNAL_ACCEPTANCE",
    "RUNNER_AND_RECOMPUTATION",
    "UNCONDITIONAL_OPERATIONAL_PREDICTIONS",
    "PRODUCTION_RUNTIME_AND_DURABILITY",
    "TEST28_PRODUCTION_GATE_01",
    "TEST28_PRODUCTION_GATE_02",
    "TEST28_PRODUCTION_GATE_03",
    "TEST28_PRODUCTION_GATE_04",
    "TEST28_PRODUCTION_GATE_05",
    "TEST28_PRODUCTION_GATE_06",
    "TEST28_PRODUCTION_GATE_07",
    "TEST28_PRODUCTION_GATE_08",
    "TEST28_PRODUCTION_GATE_09",
    "TEST28_PRODUCTION_GATE_10",
    "TEST28_PRODUCTION_GATE_11",
    "TEST28_PRODUCTION_GATE_12",
    "TEST28_PRODUCTION_GATE_13",
    "TEST28_PRODUCTION_GATE_14",
    "TEST28_PRODUCTION_GATE_15",
    "TEST28_PRODUCTION_GATE_16",
    "TEST28_PRODUCTION_GATE_17",
    "TEST29_PRODUCTION_ROUTE_RECEIPT",
    "TEST29_WHOLE_METHOD_RESIDUAL",
    "TEST30_PRODUCTION_COUPLED_PATH_RECEIPT",
    "TEST30_WHOLE_METHOD_RESIDUAL",
    "REAL_IMMUTABLE_EXECUTION_LEDGER",
    "INDEPENDENT_REAL_RECOMPUTATION_RECEIPT",
    "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED",
)
if len(REAL_RESIDUAL_IDS) != 50 or len(set(REAL_RESIDUAL_IDS)) != 50:
    raise RuntimeError("frozen open residual roster differs")


class IndependentBetaRecomputationError(ValueError):
    """Fail-closed independent recomputation error."""


@dataclass(frozen=True)
class _FrozenSuppliedInput:
    schema_version: str
    initializer_row_ordinal: int
    initializer_seed: int
    path_first_word: int
    path_second_word: int
    checkpoint_step: int
    input_sha256: str


def _frozen_supplied_input():
    payload = {
        "checkpoint_step": FROZEN_CHECKPOINT_STEP,
        "initializer_row_ordinal": FROZEN_INITIALIZER_ROW_ORDINAL,
        "initializer_seed": FROZEN_INITIALIZER_SEED,
        "path_first_word": FROZEN_WORDS[0],
        "path_second_word": FROZEN_WORDS[1],
        "schema_version": FROZEN_INPUT_SCHEMA,
    }
    value = _FrozenSuppliedInput(
        **payload,
        input_sha256=_domain_sha256(FROZEN_INPUT_DOMAIN, payload),
    )
    if value.input_sha256 != FROZEN_SUPPLIED_INPUT_SHA256:
        raise IndependentBetaRecomputationError("frozen supplied input differs")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    return _sha256(domain.encode("ascii") + b"\0" + _canonical(value))


def _json_pairs(pairs):
    if type(pairs) is not list:
        raise IndependentBetaRecomputationError("JSON pairs differ")
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise IndependentBetaRecomputationError("duplicate JSON key")
        result[key] = value
    return result


def _identity(metadata: os.stat_result) -> tuple:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _capture_predecessor_machine(project_root: str) -> bytes:
    parts = tuple(PREDECESSOR_MACHINE_RELATIVE_PATH.split("/"))
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(project_root, root_flags)
    opened = []
    try:
        root_before = os.fstat(root_fd)
        current = root_fd
        parents = []
        for part in parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            parents.append((descriptor, _identity(os.fstat(descriptor))))
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf = os.open(parts[-1], flags, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or before.st_size != 9789
        ):
            raise IndependentBetaRecomputationError("predecessor custody differs")
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        if (
            len(raw) != before.st_size
            or _sha256(raw) != PREDECESSOR_MACHINE_SHA256
            or _identity(before) != _identity(os.fstat(leaf))
            or _identity(root_before) != _identity(os.fstat(root_fd))
            or any(identity != _identity(os.fstat(fd)) for fd, identity in parents)
        ):
            raise IndependentBetaRecomputationError("predecessor changed or differs")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _predecessor_binding(project_root: str) -> Mapping[str, object]:
    raw = _capture_predecessor_machine(project_root)
    if not raw.endswith(b"\n"):
        raise IndependentBetaRecomputationError("predecessor machine differs")
    try:
        machine = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_json_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IndependentBetaRecomputationError("predecessor JSON differs") from error
    if type(machine) is not dict or _canonical(machine) + b"\n" != raw:
        raise IndependentBetaRecomputationError("predecessor canonical form differs")
    supplied = machine.get("record_sha256")
    unsigned = dict(machine)
    unsigned.pop("record_sha256", None)
    if supplied != PREDECESSOR_RECORD_SHA256 or supplied != _domain_sha256(
        "heterodiff-b12-whole-method-nonconfirmatory-runner-candidate-v1", unsigned
    ):
        raise IndependentBetaRecomputationError("predecessor self-record differs")
    receipt = machine["semantics"]["receipt"]
    route = machine["route_binding"]
    if (
        receipt["receipt_sha256"] != PREDECESSOR_RECEIPT_SHA256
        or route["stable_receipt_sha256"] != PREDECESSOR_RECEIPT_SHA256
        or route["supplied_input_sha256"] != FROZEN_SUPPLIED_INPUT_SHA256
        or route["open_residual_slot_count"] != 50
        or route["confirmatory_evidence"] is not False
    ):
        raise IndependentBetaRecomputationError("predecessor boundary differs")
    return {
        "core_output_sha256": receipt["core_output_sha256"],
        "machine_raw_sha256": PREDECESSOR_MACHINE_SHA256,
        "machine_record_sha256": PREDECESSOR_RECORD_SHA256,
        "receipt_schema": receipt["schema_version"],
        "receipt_sha256": PREDECESSOR_RECEIPT_SHA256,
        "route_binding": dict(route),
    }


def _configuration_sha256(configuration: object) -> str:
    if type(configuration) is not tuple or len(configuration) > MAX_TRANSFORM_EVENTS:
        raise IndependentBetaRecomputationError("configuration type or size differs")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-certified-initial-score-state-v1\0")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    for ordinal, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise IndependentBetaRecomputationError("configuration event type differs")
        digest.update(ordinal.to_bytes(8, "big", signed=False))
        digest.update(event.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(event.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _event_sha256(event: TransformedEvent, ordinal: int) -> str:
    return _domain_sha256(
        "heterodiff-b12-beta-selected-event-v1",
        {
            "coordinate_hex": [coordinate.hex() for coordinate in event.coordinates],
            "event_type": event.event_type,
            "ordinal": ordinal,
        },
    )


def _occurrence(
    serial: int,
    kind: str,
    coordinate: float,
    role: str,
    source_event_ordinal,
    source_event_sha256,
) -> Mapping[str, object]:
    if (
        type(serial) is not int
        or serial < 1
        or kind not in ("A", "B")
        or type(coordinate) is not float
        or not math.isfinite(coordinate)
    ):
        raise IndependentBetaRecomputationError("occurrence structure differs")
    return {
        "coordinate_hex": coordinate.hex(),
        "kind": kind,
        "role": role,
        "serial": serial,
        "source_event_ordinal": source_event_ordinal,
        "source_event_sha256": source_event_sha256,
    }


def _state_sha256(occurrences: Tuple[Mapping[str, object], ...]) -> str:
    if type(occurrences) is not tuple:
        raise IndependentBetaRecomputationError("state roster differs")
    return _domain_sha256(
        "heterodiff-b12-beta-integrated-path-state-v1", list(occurrences)
    )


def _execute_initializer():
    supplied = _frozen_supplied_input()
    bundle = cp62.cp62_execution_capsule_bundle()
    row = bundle.request_bindings[supplied.initializer_row_ordinal - 1]
    if (
        row.fixture_id != "T28-M1-Q"
        or row.strategy != "fixed-budget-sir"
        or row.budget != 8
        or bundle.formal_test_28_status != "OPEN"
        or bundle.formal_test_28_closed
    ):
        raise IndependentBetaRecomputationError("initializer predecessor differs")
    source = exact_tilt.build_t28_m1_q_exact_score_provider()
    provider = score_facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    plan = initializer.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=supplied.initializer_seed,
        budget=row.budget,
        ess_warning_fraction=0.25,
    )
    owner = initializer.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    owner.validate_result(result)
    if type(result) is not initializer.MixedSupportInitialTiltSIRResultV2:
        raise IndependentBetaRecomputationError("initializer result arm differs")
    digest = _configuration_sha256(result.selected_configuration)
    if digest != result.selected_configuration_sha256:
        raise IndependentBetaRecomputationError("selected configuration digest differs")
    return supplied, result


def _stable_initializer_sha256(result, supplied) -> str:
    row = cp62.cp62_execution_capsule_bundle().request_bindings[
        supplied.initializer_row_ordinal - 1
    ]
    payload = {
        "particles": [
            {
                "configuration_sha256": particle.scored.configuration_sha256,
                "exact_log_weight": [
                    str(particle.scored.exact_log_weight.numerator),
                    str(particle.scored.exact_log_weight.denominator),
                ],
                "normalized_weight_hex": particle.normalized_weight.hex(),
                "ordinal": ordinal,
            }
            for ordinal, particle in enumerate(result.particles)
        ],
        "budget": row.budget,
        "effective_sample_size_hex": result.effective_sample_size.hex(),
        "ess_warning": result.ess_warning,
        "initializer_row_ordinal": row.row_ordinal,
        "initializer_seed": supplied.initializer_seed,
        "maximum_normalized_weight_hex": result.maximum_normalized_weight.hex(),
        "proposal_stream_final_state_sha256": result.proposal_stream_final_state_sha256,
        "proposal_stream_initial_state_sha256": result.proposal_stream_initial_state_sha256,
        "resampling_stream_final_state_sha256": result.resampling_stream_final_state_sha256,
        "resampling_stream_initial_state_sha256": result.resampling_stream_initial_state_sha256,
        "resampling_uniform_53": result.resampling_uniform_53,
        "resampling_word": result.resampling_word,
        "request_binding_sha256": row.record_sha256,
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "selected_index": result.selected_index,
        "status": result.status,
        "strategy": row.strategy,
    }
    return _domain_sha256(
        "heterodiff-b12-beta-stable-initializer-execution-v1", payload
    )


def _transform(configuration: tuple, selected_sha256: str):
    if _configuration_sha256(configuration) != selected_sha256:
        raise IndependentBetaRecomputationError("transform input digest differs")
    occurrences = []
    for ordinal, event in enumerate(configuration):
        if event.event_type == 0 and event.coordinates != ():
            raise IndependentBetaRecomputationError("type-0 dimension differs")
        if event.event_type == 1 and len(event.coordinates) != 1:
            raise IndependentBetaRecomputationError("type-1 dimension differs")
        if event.event_type not in (0, 1):
            raise IndependentBetaRecomputationError("event type leaves frozen law")
        coordinate = float(0.0 if event.event_type == 0 else event.coordinates[0])
        occurrences.append(
            _occurrence(
                ordinal + 1,
                "A" if event.event_type % 2 == 0 else "B",
                coordinate,
                "SELECTED_EVENT",
                ordinal,
                _event_sha256(event, ordinal),
            )
        )
    empty = not occurrences
    exact = tuple(occurrences)
    initial_sha = _state_sha256(exact)
    payload = {
        "empty_configuration_initial_state": empty,
        "initial_state_sha256": initial_sha,
        "occurrences": list(exact),
        "schema_version": SCHEMA_VERSION,
        "selected_configuration_sha256": selected_sha256,
        "source_event_count": len(configuration),
        "transform_policy_id": TRANSFORM_POLICY_ID,
    }
    transform_sha = _domain_sha256(
        "heterodiff-b12-beta-initializer-path-transform-v1", payload
    )
    return dict(payload, transform_sha256=transform_sha), exact


def _increment(serial: int, word: int, step_index: int, right: bool) -> float:
    low_word = word & 31
    numerator = (
        ((7 * serial + 3 * low_word + 5 * step_index) % 13) - 6
        if right
        else ((5 * serial + 2 * low_word + 3 * step_index) % 11) - 5
    )
    return float(numerator) / 64.0


def _evolved_coordinate(coordinate: float, increment: float, kind: str) -> float:
    design = test30.frozen_synthetic_design()
    target = design.long_run_mean_a if kind == "A" else design.long_run_mean_b
    value = test30._heun_half(
        coordinate,
        duration=0.5 * MACROSTEP_WIDTH,
        increment=increment,
        theta=design.mean_reversion,
        diffusion=design.diffusion,
        long_run_mean=target,
    )
    if not math.isfinite(value):
        raise IndependentBetaRecomputationError("Heun result differs")
    return value


def _evolve(state, increments: Mapping[int, float]):
    if tuple(sorted(increments)) != tuple(item["serial"] for item in state):
        raise IndependentBetaRecomputationError("increment roster differs")
    return tuple(
        dict(
            item,
            coordinate_hex=_evolved_coordinate(
                float.fromhex(item["coordinate_hex"]),
                increments[item["serial"]],
                item["kind"],
            ).hex(),
        )
        for item in state
    )


def _zero_fixture():
    gaussian = test29.GaussianDestination((Fraction(1, 4),), (Fraction(1, 4),))
    root = test29.StateSpec(
        "beta-zero-root",
        1,
        0,
        (
            test29.RouteSpec(
                "beta-zero-birth",
                test29.FAMILY_BIRTH,
                "beta-zero-terminal",
                Fraction(1),
                Fraction(1),
                (),
                gaussian,
            ),
        ),
    )
    terminal = test29.StateSpec("beta-zero-terminal", 0, 1, ())
    return test29.FixtureSpec(
        "b12-beta-zero-cardinality-birth-v1",
        (root, terminal),
        root.state_id,
        test29.WordLayout(0, 0, 1, 1),
    )


def _fixture(cardinality: int):
    if not 0 <= cardinality <= 3:
        raise IndependentBetaRecomputationError("fixture cardinality differs")
    return _zero_fixture() if cardinality == 0 else two.dynamic_central_jump_fixture(test29, cardinality)


def _increment_rows(items):
    return [
        {
            "domain": item.address.domain,
            "domain_tag": item.address.domain_tag,
            "increment_hex": item.increment.hex(),
            "occurrence_serial": item.address.occurrence_serial,
            "philox_counter": list(item.address.philox_counter),
            "philox_key": list(item.address.philox_key),
            "proposal_index": item.address.proposal_index,
            "run_id": item.address.run_id,
            "step_index": item.address.step_index,
        }
        for item in items
    ]


def _created(fixture, selection, serial: int):
    route = next(row for row in fixture.initial_state.routes if row.route_id == selection.route_id)
    if route.gaussian_destination is None or len(selection.normal_cells) != 1:
        raise IndependentBetaRecomputationError("destination route differs")
    cell = selection.normal_cells[0]
    coordinate = float(route.gaussian_destination.mean[0]) + math.sqrt(
        float(route.gaussian_destination.variance[0])
    ) * cell.midpoint_representative()
    return _occurrence(
        serial,
        "A" if selection.family == test29.FAMILY_BIRTH else "B",
        coordinate,
        "PATH_BIRTH",
        None,
        None,
    )


def _path(transform: Mapping[str, object], initial_state):
    path_input = {
        "initial_state_sha256": transform["initial_state_sha256"],
        "path_policy_id": PATH_POLICY_ID,
        "selected_configuration_sha256": transform["selected_configuration_sha256"],
        "transform_sha256": transform["transform_sha256"],
        "words": list(FROZEN_WORDS),
    }
    path_input_sha = _domain_sha256(
        "heterodiff-b12-beta-integrated-path-input-v1", path_input
    )
    current = tuple(initial_state)
    lineage = test29.LineageState(
        tuple(item["serial"] for item in current),
        (),
        1 if not current else max(item["serial"] for item in current) + 1,
    )
    steps = []
    for step_index, word in enumerate(FROZEN_WORDS):
        before_sha = _state_sha256(current)
        fixture = _fixture(len(lineage.active_serials))
        central_word = test29.AddressedUint64Word(
            test29.CP24CompatibleAddress(RUN_ID, step_index, 0), word
        )
        central_word = single._validate_central_word(
            test29, central_word, run_id=RUN_ID, step_index=step_index
        )
        oracle = test29.run_addressed_acyclic_fixture(
            fixture, (central_word,), run_id=RUN_ID, step_index=step_index
        )
        test29.validate_addressed_acyclic_run_result(
            fixture, (central_word,), oracle
        )
        selection = test29.select_one_step(fixture, fixture.initial_state_id, word)
        if oracle.transitions[0].selection != selection:
            raise IndependentBetaRecomputationError("route selection differs")
        lineage_after, source_serial, created_serial = test29._advance_lineage(
            lineage, selection
        )
        left_records = tuple(
            single._addressed_increment(
                test30,
                run_id=RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30.TAG_BROWNIAN_LEFT,
                increment=_increment(serial, word, step_index, False),
            )
            for serial in lineage.active_serials
        )
        left_values = single._validate_increment_roster(
            test30,
            left_records,
            expected_serials=lineage.active_serials,
            run_id=RUN_ID,
            step_index=step_index,
            tag=test30.TAG_BROWNIAN_LEFT,
            label="beta left",
        )
        left = _evolve(current, left_values)
        left_sha = _state_sha256(left)
        live = {item["serial"]: dict(item) for item in left}
        if source_serial is not None:
            if source_serial not in live:
                raise IndependentBetaRecomputationError("source is not live")
            del live[source_serial]
        created = None
        if created_serial is not None:
            created = _created(fixture, selection, created_serial)
            if created["serial"] in live:
                raise IndependentBetaRecomputationError("fresh serial collided")
            live[created["serial"]] = dict(created)
        if tuple(sorted(live)) != lineage_after.active_serials:
            raise IndependentBetaRecomputationError("lineage and coordinates differ")
        jumped = tuple(live[serial] for serial in sorted(live))
        jump_sha = _state_sha256(jumped)
        right_records = tuple(
            single._addressed_increment(
                test30,
                run_id=RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30.TAG_BROWNIAN_RIGHT,
                increment=_increment(serial, word, step_index, True),
            )
            for serial in lineage_after.active_serials
        )
        right_values = single._validate_increment_roster(
            test30,
            right_records,
            expected_serials=lineage_after.active_serials,
            run_id=RUN_ID,
            step_index=step_index,
            tag=test30.TAG_BROWNIAN_RIGHT,
            label="beta right",
        )
        right = _evolve(jumped, right_values)
        right_sha = _state_sha256(right)
        edit = {
            "created_occurrence": created,
            "family": selection.family,
            "normal_cell_indices": [cell.index for cell in selection.normal_cells],
            "raw64_word": word,
            "route_id": selection.route_id,
            "source_index": selection.source_index,
            "source_serial": source_serial,
        }
        edit["edit_sha256"] = _domain_sha256(
            "heterodiff-b12-beta-central-edit-v1", edit
        )
        steps.append(
            {
                "active_serials_after": list(lineage_after.active_serials),
                "active_serials_before": list(lineage.active_serials),
                "addressed_central_word": {
                    "counter": list(central_word.address.counter),
                    "key": list(central_word.address.key),
                    "raw64_word": central_word.raw64_word,
                },
                "after_jump_sha256": jump_sha,
                "after_left_sha256": left_sha,
                "after_right_sha256": right_sha,
                "before_sha256": before_sha,
                "central_edit": edit,
                "left_addressed_increments": _increment_rows(left_records),
                "left_state": list(left),
                "retired_serials_after": list(lineage_after.retired_serials),
                "retired_serials_before": list(lineage.retired_serials),
                "right_addressed_increments": _increment_rows(right_records),
                "right_state": list(right),
                "step_index": step_index,
            }
        )
        current = right
        lineage = lineage_after
    if steps[0]["before_sha256"] != transform["initial_state_sha256"]:
        raise IndependentBetaRecomputationError("path did not start from transform")
    if steps[1]["before_sha256"] != steps[0]["after_right_sha256"]:
        raise IndependentBetaRecomputationError("path continuity differs")
    report = {
        "arbitrary_length_general_strang_path_integrated": False,
        "bounded_two_macrostep_path_integrated": True,
        "cp23_addressed_increments_validated": True,
        "cp24_addressed_words_validated": True,
        "final_state": list(current),
        "final_state_sha256": _state_sha256(current),
        "formal_test_28_closed": False,
        "formal_test_29_closed": False,
        "formal_test_30_closed": False,
        "formal_test28_production_law_admissible": False,
        "initializer_to_path_integrated": True,
        "initial_state_sha256": transform["initial_state_sha256"],
        "path_input_sha256": path_input_sha,
        "path_policy_id": PATH_POLICY_ID,
        "selected_configuration_sha256": transform["selected_configuration_sha256"],
        "steps": steps,
        "test29_route_and_lineage_semantics_integrated": True,
        "test30_heun_primitive_integrated": True,
        "transform_sha256": transform["transform_sha256"],
        "test28_initializer_admissible": True,
        "upstream_runtime_executed": False,
    }
    report["path_report_sha256"] = _domain_sha256(
        "heterodiff-b12-beta-integrated-path-report-v1", report
    )
    return report


def _core(project_root: str) -> Mapping[str, object]:
    root = Path(project_root)
    if type(project_root) is not str or str(root) != project_root or root.resolve(strict=True) != root:
        raise IndependentBetaRecomputationError("project root differs")
    supplied, result = _execute_initializer()
    stable_initializer_sha = _stable_initializer_sha256(result, supplied)
    predecessor_binding = _predecessor_binding(project_root)
    transform, initial_state = _transform(
        result.selected_configuration, result.selected_configuration_sha256
    )
    path = _path(transform, initial_state)
    custody_payload = {
        "derived_initial_state_sha256": transform["initial_state_sha256"],
        "initializer_result_sha256": stable_initializer_sha,
        "integrated_path_input_sha256": path["path_input_sha256"],
        "integrated_path_report_sha256": path["path_report_sha256"],
        "predecessor_receipt_sha256": predecessor_binding["receipt_sha256"],
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "supplied_input_sha256": supplied.input_sha256,
        "transform_policy_id": TRANSFORM_POLICY_ID,
        "transform_sha256": transform["transform_sha256"],
    }
    custody_sha = _domain_sha256(
        "heterodiff-b12-beta-end-to-end-custody-v1", custody_payload
    )
    return {
        "custody_chain": dict(custody_payload, custody_chain_sha256=custody_sha),
        "effects": {
            "blocker_delta": 0,
            "data_accessed": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "result_delta": 0,
            "science_executed": False,
            "tracker_or_ledger_edited": False,
            "training_executed": False,
            "upstream_runtimes_executed": False,
        },
        "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
        "initializer": {
            "stable_execution_sha256": stable_initializer_sha,
            "selected_configuration_sha256": result.selected_configuration_sha256,
            "selected_event_count": len(result.selected_configuration),
            "selected_index": result.selected_index,
            "strategy": "fixed-budget-sir",
        },
        "initializer_path_state": transform,
        "integrated_path": path,
        "nonclaims": {
            "arbitrary_length_general_path": False,
            "b12_closed": False,
            "confirmatory_evidence": False,
            "gate_b0_feature_complete": False,
            "production_receipt": False,
            "real_residual_receipts_present": 0,
            "upstream_external_runtime": False,
            "direct_public_api_custody_authenticated": False,
        },
        "qualification_boundary": {
            "authoritative_isolated_hash_first_validator_required": True,
            "direct_public_api_custody_authenticated": False,
        },
        "open_residual_predicate_ids": list(REAL_RESIDUAL_IDS),
        "predecessor": predecessor_binding,
        "proposed_timetable_task_closures": [PROPOSED_TASK],
        "schema_version": CORE_SCHEMA,
        "state": STATE,
    }


def independently_recompute_beta_successor(project_root: str) -> bytes:
    """Return independently reconstructed canonical successor core bytes."""

    return _canonical(_core(project_root)) + b"\n"


__all__ = [
    "IndependentBetaRecomputationError",
    "independently_recompute_beta_successor",
]
