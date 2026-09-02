"""Read-only custody validator for the finite-acyclic Test-29 precursor.

The validator binds the visible overnight authority, the human qualification
record, the pure implementation, the hostile test suite, and the exact frozen
CP19--CP24 source ancestry.  It recomputes the finite route/cell/lineage oracle
without entropy or external effects and validates a canonical self-digested
machine record.

It closes only ``FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED``.
Formal Test 29, B12, every project field, and every scientific result remain
unchanged and open in their prior states.
"""

from __future__ import annotations

from fractions import Fraction
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Dict, Mapping, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
oracle = None


SCHEMA_VERSION = "heterodiff-manuscript-v3-formal-test29-finite-acyclic-route-v1"
STATE = "FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED"
PREDICATE = STATE
REPORTED_DATE = "2026-08-30"
VISIBLE_AUTHORITY = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)

HUMAN_PATH = ROOT / "PROJECT_FORMAL_TEST29_FINITE_ACYCLIC_ROUTE_QUALIFICATION.md"
SOURCE_PATH = (
    ROOT
    / "src"
    / "heterodiff"
    / "processes"
    / "formal_test29_finite_acyclic_route_oracle.py"
)
TEST_PATH = (
    ROOT / "tests" / "unit" / "test_formal_test29_finite_acyclic_route_oracle.py"
)
VALIDATOR_PATH = Path(__file__).resolve()
MACHINE_PATH = (
    ROOT
    / "research"
    / "fixtures"
    / "manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json"
)

EXPECTED_FOCUSED_TESTS = 59
EXPECTED_PARENT_REGRESSION_COLLECTED = 129
EXPECTED_PARENT_REGRESSION_PASSED = 126
EXPECTED_PARENT_REGRESSION_FAILED = 3
EXPECTED_PARENT_REGRESSION_FAILED_NODE_IDS = (
    "tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py"
    "::test_optional_torch_import_boundary_is_explicit",
    "tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py"
    "::test_optional_torch_import_boundary_is_explicit",
    "tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py"
    "::test_optional_torch_import_boundary_is_explicit",
)
EXPECTED_PARENT_REGRESSION_COMMAND_ARGV = (
    ".venv-m1/bin/python",
    "-P",
    "-B",
    "-m",
    "pytest",
    "-p",
    "no:cacheprovider",
    "-W",
    "error",
    "-q",
    "tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py",
    "tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py",
    "tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py",
)
EXPECTED_ISOLATED_REGRESSION_COMMAND_ARGV = (
    ".venv-m1/bin/python",
    "-P",
    "-B",
    "-m",
    "pytest",
    "-p",
    "no:cacheprovider",
    "-W",
    "error",
    "-q",
) + EXPECTED_PARENT_REGRESSION_FAILED_NODE_IDS
EXPECTED_SOURCE_SHA256 = (
    "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089"
)

PARENT_BINDINGS = (
    (
        "CP19_SOURCE",
        "src/heterodiff/processes/plugin_bridge_operational_thinning.py",
        "3773a113247da86015a4d8bbcb33f10d004ad66093f05d168decf46b35aea0fd",
    ),
    (
        "CP20_SOURCE",
        "src/heterodiff/processes/plugin_bridge_operational_thinning_loop.py",
        "312c5da26b695718ece0e0305a36fd050d206ae5b74bd5e934808d93e2353bf3",
    ),
    (
        "CP21_SOURCE",
        "src/heterodiff/processes/plugin_bridge_continuous_route_evidence.py",
        "a597f076f5cca1834515121e831f732a4ed1fbd2c23c5802672c2edd639e1a38",
    ),
    (
        "CP22_SOURCE",
        "src/heterodiff/processes/"
        "plugin_bridge_operational_thinning_loop_route_evidence.py",
        "90b2829b7df486ba780276fa684669ddab2f68c949e4d70f7046fec2234f969d",
    ),
    (
        "CP23_SOURCE",
        "src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py",
        "e728ef0149a3c3275a3b7c1efba8f038279db86cc05e06c56a09545374197557",
    ),
    (
        "CP24_SOURCE",
        "src/heterodiff/processes/"
        "plugin_bridge_counter_keyed_operational_epoch_loop.py",
        "21fdf6931d50dd35022cf6d39e8d529a3da0e20e4875c55cca2188e0fa572320",
    ),
)

PARENT_TEST_BINDINGS = (
    (
        "CP22_REGRESSION_TEST",
        "tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py",
        "afdf2eb12d6db0cc0bb024a34f73ed22bfa1819e254ebecaf348111a9bfb8fbf",
    ),
    (
        "CP23_REGRESSION_TEST",
        "tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py",
        "747ee46ab8132ddb086e7719035fa0dfac870cd4f65bf7159c1aa13699b3ad53",
    ),
    (
        "CP24_REGRESSION_TEST",
        "tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py",
        "17987cb9e7c03b9df7e33e85be7e7b3196c254b1b006579b6fc9f40146024789",
    ),
)

ALLOWED_SOURCE_IMPORTS = {
    "__future__",
    "dataclasses",
    "fractions",
    "math",
    "statistics",
    "typing",
}
FORBIDDEN_SOURCE_IMPORTS = {
    "heterodiff",
    "numpy",
    "torch",
    "random",
    "secrets",
    "os",
    "pathlib",
    "socket",
    "subprocess",
    "time",
    "requests",
    "urllib",
}


class FormalTest29QualificationValidationError(ValueError):
    """Raised when a custody or semantic invariant differs."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _self_digest(record: Mapping[str, object]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(_canonical_json(payload))


def _duplicate_rejecting_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FormalTest29QualificationValidationError(
                "machine record contains a duplicate key"
            )
        result[key] = value
    return result


def _stable_read(
    path: Path, *, require_text: bool = True
) -> Tuple[bytes, os.stat_result]:
    path = Path(path)
    before = os.lstat(path)
    if stat.S_ISLNK(before.st_mode):
        raise FormalTest29QualificationValidationError("symlink input is forbidden")
    if not stat.S_ISREG(before.st_mode):
        raise FormalTest29QualificationValidationError("input must be a regular file")
    if stat.S_IMODE(before.st_mode) != 0o644:
        raise FormalTest29QualificationValidationError(
            "input mode must be exactly 0644"
        )
    if before.st_nlink != 1:
        raise FormalTest29QualificationValidationError("hard-linked input is forbidden")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = os.lstat(path)
    if stat.S_ISLNK(final.st_mode) or not stat.S_ISREG(final.st_mode):
        raise FormalTest29QualificationValidationError(
            "input path identity changed during read"
        )
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_opened = (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
        opened.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    identity_final = (
        final.st_dev,
        final.st_ino,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    )
    if (
        identity_before != identity_opened
        or identity_opened != identity_after
        or identity_after != identity_final
    ):
        raise FormalTest29QualificationValidationError("input changed during read")
    payload = b"".join(chunks)
    if len(payload) != before.st_size:
        raise FormalTest29QualificationValidationError("input byte count changed")
    if require_text:
        if not payload.endswith(b"\n"):
            raise FormalTest29QualificationValidationError(
                "text input must have a terminal LF"
            )
        if b"\r" in payload:
            raise FormalTest29QualificationValidationError(
                "text input must use LF line endings"
            )
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise FormalTest29QualificationValidationError(
                "text input must be UTF-8"
            ) from error
    return payload, after


def _binding(
    path: Path, *, role: str, expected_sha256: Optional[str] = None
) -> Mapping[str, object]:
    payload, metadata = _stable_read(path)
    digest = _sha256(payload)
    if expected_sha256 is not None and digest != expected_sha256:
        raise FormalTest29QualificationValidationError(
            "%s predecessor SHA-256 differs" % role
        )
    try:
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as error:
        raise FormalTest29QualificationValidationError(
            "bound input must remain inside the project root"
        ) from error
    return {
        "role": role,
        "path": relative,
        "raw_sha256": digest,
        "bytes": len(payload),
        "mode_octal": "0644",
        "nlink": metadata.st_nlink,
        "terminal_lf": payload.endswith(b"\n"),
    }


def _gaussian_2d() -> oracle.GaussianDestination:
    return oracle.GaussianDestination(
        (Fraction(0), Fraction(1, 2)),
        (Fraction(1), Fraction(4)),
    )


def _gaussian_1d() -> oracle.GaussianDestination:
    return oracle.GaussianDestination((Fraction(-1, 2),), (Fraction(9, 4),))


def _fixture() -> oracle.FixtureSpec:
    layout = oracle.WordLayout(2, 2, 1, 2)
    root = oracle.StateSpec(
        "root-r2",
        2,
        2,
        (
            oracle.RouteSpec(
                "root-birth",
                oracle.FAMILY_BIRTH,
                "birth-r1",
                Fraction(1),
                Fraction(2),
                (),
                _gaussian_2d(),
            ),
            oracle.RouteSpec(
                "root-replacement",
                oracle.FAMILY_REPLACEMENT,
                "replacement-r1",
                Fraction(4),
                Fraction(1, 4),
                (Fraction(1, 2), Fraction(1, 2)),
                _gaussian_1d(),
            ),
            oracle.RouteSpec(
                "root-death",
                oracle.FAMILY_DEATH,
                "death-terminal",
                Fraction(1, 2),
                Fraction(2),
                (Fraction(1, 2), Fraction(1, 2)),
                None,
            ),
        ),
    )
    birth = oracle.StateSpec(
        "birth-r1",
        1,
        3,
        (
            oracle.RouteSpec(
                "birth-child-death",
                oracle.FAMILY_DEATH,
                "birth-terminal",
                Fraction(3, 2),
                Fraction(2, 3),
                (Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)),
                None,
            ),
        ),
    )
    replacement = oracle.StateSpec(
        "replacement-r1",
        1,
        2,
        (
            oracle.RouteSpec(
                "replacement-child-replacement",
                oracle.FAMILY_REPLACEMENT,
                "replacement-terminal",
                Fraction(5),
                Fraction(1, 5),
                (Fraction(1, 2), Fraction(1, 2)),
                _gaussian_2d(),
            ),
        ),
    )
    terminals = (
        oracle.StateSpec("birth-terminal", 0, 2, ()),
        oracle.StateSpec("replacement-terminal", 0, 2, ()),
        oracle.StateSpec("death-terminal", 0, 1, ()),
    )
    return oracle.FixtureSpec(
        "test29-hostile-acyclic-fixture",
        (root, birth, replacement) + terminals,
        "root-r2",
        layout,
    )


def _fraction_text(value: Fraction) -> str:
    if type(value) is not Fraction:
        raise TypeError("value must be an exact Fraction")
    return "%d/%d" % (value.numerator, value.denominator)


def _source_import_receipt(source_payload: bytes) -> Mapping[str, object]:
    tree = ast.parse(source_payload.decode("utf-8"), filename=SOURCE_PATH.name)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    if not roots <= ALLOWED_SOURCE_IMPORTS:
        raise FormalTest29QualificationValidationError(
            "pure source import allowlist differs"
        )
    if roots.intersection(FORBIDDEN_SOURCE_IMPORTS):
        raise FormalTest29QualificationValidationError(
            "pure source imports an effectful dependency"
        )
    return {
        "observed_import_roots": sorted(roots),
        "allowed_import_roots": sorted(ALLOWED_SOURCE_IMPORTS),
        "forbidden_import_roots_absent": True,
        "entropy_import_absent": True,
        "network_import_absent": True,
        "data_import_absent": True,
        "model_import_absent": True,
        "parent_execution_import_absent": True,
    }


def _load_bound_oracle(source_payload: bytes):
    """Execute exactly the already-stable-read, hash-admitted source bytes."""

    digest = _sha256(source_payload)
    if digest != EXPECTED_SOURCE_SHA256:
        raise FormalTest29QualificationValidationError(
            "pure implementation SHA-256 differs before import"
        )
    _source_import_receipt(source_payload)
    module_name = "_bound_formal_test29_finite_acyclic_route_oracle_" + digest[:16]
    module = ModuleType(module_name)
    module.__file__ = str(SOURCE_PATH)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    code = compile(
        source_payload,
        str(SOURCE_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=0,
    )
    prior = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    finally:
        if prior is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior
    if Path(module.__file__).resolve() != SOURCE_PATH.resolve():
        raise FormalTest29QualificationValidationError(
            "pure implementation changed its declared source origin"
        )
    return module


def _semantic_receipt() -> Mapping[str, object]:
    fixture = _fixture()
    qualification = oracle.qualify_finite_acyclic_fixture(fixture)
    active_states = tuple(state for state in fixture.states if state.rank > 0)
    for state in active_states:
        if oracle.operational_pushforward_law(
            fixture, state.state_id
        ) != oracle.enumerate_low_word_pushforward(fixture, state.state_id):
            raise FormalTest29QualificationValidationError(
                "closed-form and enumerated pushforwards differ"
            )
    terminal_counts: Dict[str, int] = {}
    consumed_counts: Dict[int, int] = {}
    unique_address_traces = True
    tape_count = 0
    for first in range(fixture.layout.low_word_count):
        for second in range(fixture.layout.low_word_count):
            addressed = oracle.bind_supplied_words_to_addresses(
                fixture, (first, second), run_id=0, step_index=0
            )
            result = oracle.run_addressed_acyclic_fixture(
                fixture, addressed, run_id=0, step_index=0
            )
            oracle.validate_addressed_acyclic_run_result(fixture, addressed, result)
            tape_count += 1
            terminal_counts[result.terminal_state_id] = (
                terminal_counts.get(result.terminal_state_id, 0) + 1
            )
            consumed_counts[result.consumed_word_count] = (
                consumed_counts.get(result.consumed_word_count, 0) + 1
            )
            identities = tuple(
                (transition.address.key, transition.address.counter)
                for transition in result.transitions
            )
            unique_address_traces = unique_address_traces and len(
                set(identities)
            ) == len(identities)
    root_law = oracle.ideal_one_step_law(fixture, "root-r2")
    maximum_cell_residual = max(
        oracle.NormalQuantileCell(index, bits).cdf_mass_residual()
        for bits in range(1, 7)
        for index in range(1 << bits)
    )
    obstruction = oracle.bounded_word_continuous_gaussian_obstruction(2)
    return {
        "fixture_id": fixture.fixture_id,
        "law_premises": {
            "route_and_source_source_law": "ABSTRACT_UNIFORM_UINT64",
            "route_and_source_source_law_operationally_proved": False,
            "ideal_gaussian_fiber": "INDEPENDENT_STANDARD_NORMAL",
            "ideal_gaussian_fiber_operationally_sampled": False,
            "bounded_word_output_kind": "NORMAL_QUANTILE_CELL_INDEX_ONLY",
            "bounded_word_output_is_continuous_coordinate": False,
        },
        "state_count": len(fixture.states),
        "active_state_count": len(active_states),
        "terminal_state_count": len(fixture.states) - len(active_states),
        "exact_fraction_component_bit_cap": (oracle.MAX_EXACT_FRACTION_COMPONENT_BITS),
        "layout": {
            "route_bits": fixture.layout.route_bits,
            "source_bits": fixture.layout.source_bits,
            "normal_bits": fixture.layout.normal_bits,
            "maximum_normal_dimension": fixture.layout.maximum_normal_dimension,
            "used_bits": fixture.layout.used_bits,
            "low_word_count": fixture.layout.low_word_count,
            "raw64_words_per_jump": 1,
            "cp24_completed_proposals_minimum": 0,
            "cp24_completed_proposals_maximum_exclusive": (
                oracle.CP24_OPERATIONAL_EPOCH_MAX_PROPOSALS
            ),
        },
        "root_total_tilted_rate": _fraction_text(root_law.total_tilted_rate),
        "root_route_masses": [
            {"route_id": route_id, "mass": _fraction_text(mass)}
            for route_id, mass in root_law.route_masses
        ],
        "root_family_masses": [
            {"family": family, "mass": _fraction_text(mass)}
            for family, mass in root_law.family_masses
        ],
        "gaussian_moments": {
            "standard_coordinate_orders_0_through_4": [
                _fraction_text(_gaussian_2d().raw_moment(0, order))
                for order in range(5)
            ],
            "shifted_coordinate_orders_0_through_4": [
                _fraction_text(_gaussian_2d().raw_moment(1, order))
                for order in range(5)
            ],
            "quantile_cell_levels_checked": [1, 2, 3, 4, 5, 6],
            "maximum_numeric_cdf_mass_residual": format(maximum_cell_residual, ".17g"),
            "maximum_numeric_cdf_mass_residual_below_3e_minus_16": (
                maximum_cell_residual < 3.0e-16
            ),
        },
        "exhaustive_completion": {
            "word_tapes_checked": tape_count,
            "expected_word_tapes": fixture.layout.low_word_count**2,
            "terminal_counts": dict(sorted(terminal_counts.items())),
            "consumed_word_counts": {
                str(key): value for key, value in sorted(consumed_counts.items())
            },
            "all_runs_terminal": sum(terminal_counts.values()) == tape_count,
            "all_runs_within_initial_rank": all(
                key <= fixture.initial_state.rank for key in consumed_counts
            ),
            "every_consumed_address_trace_unique": unique_address_traces,
            "complete_address_roster_preflighted_before_interpretation": True,
        },
        "qualification_truth_table": {
            "exact_tilted_total_rates_recovered": (
                qualification.exact_tilted_total_rates_recovered
            ),
            "exact_edit_family_probabilities_recovered": (
                qualification.exact_edit_family_probabilities_recovered
            ),
            "exact_categorical_route_law_recovered": (
                qualification.exact_categorical_route_law_recovered
            ),
            "exact_integer_source_law_recovered": (
                qualification.exact_integer_source_law_recovered
            ),
            "exact_ideal_gaussian_disintegration_recovered": (
                qualification.exact_ideal_gaussian_disintegration_recovered
            ),
            "exact_bounded_normal_cell_pushforward_recovered": (
                qualification.exact_bounded_normal_cell_pushforward_recovered
            ),
            "cp24_compatible_address_consumption_defined": (
                qualification.cp24_compatible_address_consumption_defined
            ),
            "finite_run_persistent_fresh_lineage_defined": (
                qualification.finite_run_persistent_fresh_lineage_defined
            ),
            "unconditional_bounded_fixture_completion_proved": (
                qualification.unconditional_bounded_fixture_completion_proved
            ),
            "exact_continuous_gaussian_from_bounded_words": (
                qualification.exact_continuous_gaussian_from_bounded_words
            ),
            "production_cp24_execution_integrated": (
                qualification.production_cp24_execution_integrated
            ),
            "general_cyclic_liveness_proved": (
                qualification.general_cyclic_liveness_proved
            ),
            "formal_test29_closed": qualification.formal_test29_closed,
        },
        "bounded_word_obstruction": obstruction,
    }


def expected_record() -> Mapping[str, object]:
    global oracle
    human_payload, _ = _stable_read(HUMAN_PATH)
    source_payload, _ = _stable_read(SOURCE_PATH)
    test_payload, _ = _stable_read(TEST_PATH)
    validator_payload, _ = _stable_read(VALIDATOR_PATH)
    human_text = human_payload.decode("utf-8")
    required_human_fragments = (
        VISIBLE_AUTHORITY,
        PREDICATE,
        "**Formal Test 29:** **OPEN**",
        "Blocker `B12`",
        "No project tracker is edited",
        "internal_evidence_only=true",
        "sanitized, publication-safe derivative",
    )
    if any(fragment not in human_text for fragment in required_human_fragments):
        raise FormalTest29QualificationValidationError(
            "human qualification record omits a required boundary"
        )
    source_static_receipt = _source_import_receipt(source_payload)
    oracle = _load_bound_oracle(source_payload)
    package_bindings = [
        _binding(HUMAN_PATH, role="HUMAN_QUALIFICATION"),
        _binding(SOURCE_PATH, role="PURE_IMPLEMENTATION"),
        _binding(VALIDATOR_PATH, role="READ_ONLY_VALIDATOR"),
        _binding(TEST_PATH, role="HOSTILE_TEST"),
    ]
    for binding, payload in zip(
        package_bindings,
        (human_payload, source_payload, validator_payload, test_payload),
    ):
        if binding["raw_sha256"] != _sha256(payload):
            raise FormalTest29QualificationValidationError(
                "package input changed between stable reads"
            )
    predecessor_bindings = [
        _binding(ROOT / path, role=role, expected_sha256=expected)
        for role, path, expected in PARENT_BINDINGS
    ]
    regression_test_bindings = [
        _binding(ROOT / path, role=role, expected_sha256=expected)
        for role, path, expected in PARENT_TEST_BINDINGS
    ]
    record = {
        "schema_version": SCHEMA_VERSION,
        "state": STATE,
        "reported_date": REPORTED_DATE,
        "visible_authority": {
            "exact_text": VISIBLE_AUTHORITY,
            "sha256": _sha256(VISIBLE_AUTHORITY.encode("utf-8")),
            "scope": "SAFE_LOCAL_OVERNIGHT_PROJECT_WORK_ONLY",
            "authorizes_data_contact_entropy_science_or_submission": False,
        },
        "package_kind": "ADDITIVE_PURE_FORMAL_TEST29_COMPONENT_QUALIFICATION",
        "named_predicate": PREDICATE,
        "scope_review": {
            "review_kind": "EXPLICIT_ADDITIVE_FIVE_FILE_COMPONENT_SCOPE",
            "physical_file_count": 5,
            "human_machine_validator_source_and_hostile_test_present": True,
            "single_named_component_predicate": True,
            "shared_visible_authority_boundary": True,
            "machine_record_self_digested": True,
            "predecessor_sources_exactly_bound": 6,
            "predecessor_regression_tests_exactly_bound": 3,
            "independent_audit_required_before_tracker_consumption": True,
            "formal_test_or_blocker_closure_in_scope": False,
        },
        "closure_delta": {
            "component_predicates_closed": 1,
            "component_predicate_ids": [PREDICATE],
            "formal_tests_closed": 0,
            "fields_closed": 0,
            "blockers_closed": 0,
            "result_slots_filled": 0,
            "scientific_claims_promoted": 0,
            "tracker_files_edited": 0,
            "formal_test29_state": "OPEN",
            "blocker_b12_state": "OPEN_UNCHANGED",
        },
        "semantic_receipt": _semantic_receipt(),
        "source_static_receipt": source_static_receipt,
        "package_bindings": package_bindings,
        "predecessor_bindings": predecessor_bindings,
        "regression_test_bindings": regression_test_bindings,
        "test_evidence": {
            "focused_workspace": {
                "passed": EXPECTED_FOCUSED_TESTS,
                "failed": 0,
                "skipped": 0,
                "warnings": 0,
                "cache_provider_disabled": True,
                "bytecode_disabled": True,
            },
            "focused_unrelated_working_directory": {
                "working_directory": "/private/tmp",
                "passed": EXPECTED_FOCUSED_TESTS,
                "failed": 0,
                "skipped": 0,
                "warnings": 0,
                "cache_provider_disabled": True,
                "bytecode_disabled": True,
            },
            "cp22_cp23_cp24_regression": {
                "command_provenance": "PACKAGE_OWNER_EXECUTED_LOCALLY_BEFORE_FREEZE",
                "working_directory": str(ROOT),
                "command_argv": list(EXPECTED_PARENT_REGRESSION_COMMAND_ARGV),
                "environment": {
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": "UNSET",
                },
                "collected": EXPECTED_PARENT_REGRESSION_COLLECTED,
                "passed": EXPECTED_PARENT_REGRESSION_PASSED,
                "failed": EXPECTED_PARENT_REGRESSION_FAILED,
                "skipped": 0,
                "warnings": 0,
                "cache_provider_disabled": True,
                "bytecode_disabled": True,
                "warnings_as_errors": True,
                "full_regression_claimed_pass": False,
                "failure_class": (
                    "SUBPROCESS_PROJECT_SRC_IMPORT_PATH_ABSENT_UNDER_PARENT_TEST_HARNESS"
                ),
                "failure_node_ids": list(EXPECTED_PARENT_REGRESSION_FAILED_NODE_IDS),
                "first_child_error": "ModuleNotFoundError: No module named 'heterodiff'",
                "all_non_import_boundary_parent_tests_passed": True,
                "isolated_import_boundary_rerun_with_explicit_project_src_pythonpath": {
                    "command_provenance": (
                        "PACKAGE_OWNER_EXECUTED_LOCALLY_BEFORE_FREEZE"
                    ),
                    "working_directory": str(ROOT),
                    "command_argv": list(EXPECTED_ISOLATED_REGRESSION_COMMAND_ARGV),
                    "environment": {
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONPATH": str(ROOT / "src"),
                    },
                    "passed": 3,
                    "failed": 0,
                    "skipped": 0,
                    "warnings": 0,
                    "cache_provider_disabled": True,
                    "bytecode_disabled": True,
                    "warnings_as_errors": True,
                },
            },
            "static_pyflakes_findings": 0,
            "black_check_clean": True,
            "focused_pyc_files_present": False,
            "independent_audit_state": "PENDING",
        },
        "remaining_gaps": [
            "EXACT_CONTINUOUS_GAUSSIAN_COORDINATE_FROM_OPERATIONAL_WORD_SOURCE",
            "PROVED_LIVE_PHILOX_OR_PHYSICAL_ENTROPY_SOURCE_LAW",
            "PRODUCTION_CP24_OWNER_INTEGRATION",
            "EXACT_WAITING_CLOCK_AND_ACCEPTANCE_THINNING_FOR_ADDITIVE_ROUTE",
            "PRODUCTION_ACTIVE_TOTAL_RATE_IDENTITY",
            "GENERAL_CYCLIC_OR_RECURRENT_LIVENESS",
            "PRODUCTION_INDEPENDENT_RECOMPUTATION_AND_TERMINAL_TEST29_RECEIPT",
            "BROWNIAN_PATH_WHOLE_METHOD_AND_SCIENTIFIC_EXECUTION",
        ],
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_submission_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_review_required": True,
            "raw_visible_authority_text_in_derivative_permitted": False,
            "internal_paths_or_hashes_in_derivative_permitted": False,
            "conversation_or_custody_provenance_in_derivative_permitted": False,
            "sanitized_mathematics_scope_and_unresolved_status_only": True,
            "scientific_result_or_model_quality_claim_permitted": False,
        },
        "operation_receipt": {
            "network_accessed": False,
            "external_contact_performed": False,
            "data_accessed": False,
            "entropy_acquired": False,
            "production_cp24_campaign_executed": False,
            "deterministic_cp22_cp24_regression_executed": True,
            "scientific_execution_performed": False,
            "training_performed": False,
            "submission_performed": False,
            "project_files_written_outside_additive_package": False,
            "temporary_hostile_test_files_created": True,
        },
    }
    record["record_sha256"] = _self_digest(record)
    return record


def validate(machine_path: Path = MACHINE_PATH) -> Mapping[str, object]:
    payload, _ = _stable_read(Path(machine_path))
    try:
        observed = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_duplicate_rejecting_object
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FormalTest29QualificationValidationError(
            "machine record is not valid canonical JSON"
        ) from error
    if type(observed) is not dict:
        raise FormalTest29QualificationValidationError(
            "machine record root must be an object"
        )
    if observed.get("record_sha256") != _self_digest(observed):
        raise FormalTest29QualificationValidationError(
            "machine record self-digest differs"
        )
    canonical = _canonical_json(observed) + b"\n"
    if payload != canonical:
        raise FormalTest29QualificationValidationError(
            "machine record is not canonical JSON with one terminal LF"
        )
    expected = expected_record()
    if observed != expected:
        raise FormalTest29QualificationValidationError(
            "machine record differs from the reconstructed expected record"
        )
    return observed


def main() -> int:
    record = validate()
    print(
        json.dumps(
            {
                "state": record["state"],
                "record_sha256": record["record_sha256"],
                "formal_test29_state": record["closure_delta"]["formal_test29_state"],
                "independent_audit_state": record["test_evidence"][
                    "independent_audit_state"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
