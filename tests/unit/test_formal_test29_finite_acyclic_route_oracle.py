"""Hostile mathematical tests for the finite-acyclic Test-29 precursor."""

import ast
import copy
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import py_compile
import sys

import pytest
from scipy.integrate import quad

from heterodiff.processes import formal_test29_finite_acyclic_route_oracle as oracle


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src"
    / "heterodiff"
    / "processes"
    / "formal_test29_finite_acyclic_route_oracle.py"
)
VALIDATOR_PATH = (
    ROOT
    / "research"
    / "diagnostics"
    / "manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.py"
)
MACHINE_PATH = (
    ROOT
    / "research"
    / "fixtures"
    / "manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json"
)


def _load_validator():
    name = "_formal_test29_finite_acyclic_validator_for_tests"
    specification = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


validator = _load_validator()

CP19_TO_CP24_SOURCE_HASHES = {
    "src/heterodiff/processes/plugin_bridge_operational_thinning.py": (
        "3773a113247da86015a4d8bbcb33f10d004ad66093f05d168decf46b35aea0fd"
    ),
    "src/heterodiff/processes/plugin_bridge_operational_thinning_loop.py": (
        "312c5da26b695718ece0e0305a36fd050d206ae5b74bd5e934808d93e2353bf3"
    ),
    "src/heterodiff/processes/plugin_bridge_continuous_route_evidence.py": (
        "a597f076f5cca1834515121e831f732a4ed1fbd2c23c5802672c2edd639e1a38"
    ),
    "src/heterodiff/processes/"
    "plugin_bridge_operational_thinning_loop_route_evidence.py": (
        "90b2829b7df486ba780276fa684669ddab2f68c949e4d70f7046fec2234f969d"
    ),
    "src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py": (
        "e728ef0149a3c3275a3b7c1efba8f038279db86cc05e06c56a09545374197557"
    ),
    "src/heterodiff/processes/plugin_bridge_counter_keyed_operational_epoch_loop.py": (
        "21fdf6931d50dd35022cf6d39e8d529a3da0e20e4875c55cca2188e0fa572320"
    ),
}


def _gaussian_2d():
    return oracle.GaussianDestination(
        (Fraction(0), Fraction(1, 2)),
        (Fraction(1), Fraction(4)),
    )


def _gaussian_1d():
    return oracle.GaussianDestination((Fraction(-1, 2),), (Fraction(9, 4),))


def _fixture(*, normal_bits=1):
    layout = oracle.WordLayout(
        route_bits=2,
        source_bits=2,
        normal_bits=normal_bits,
        maximum_normal_dimension=2,
    )
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
    birth_r1 = oracle.StateSpec(
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
    replacement_r1 = oracle.StateSpec(
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
        (root, birth_r1, replacement_r1) + terminals,
        "root-r2",
        layout,
    )


def _normal_density(value):
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def test_schema_policy_scope_and_truthful_nonclosure_flags():
    qualification = oracle.qualify_finite_acyclic_fixture(_fixture())
    assert qualification.schema_version == (
        "formal-test29-finite-acyclic-route-oracle-v1"
    )
    assert "strict-rank-decrease" in qualification.policy
    assert "not-continuous-gaussian-from-bounded-words" in qualification.scope
    assert qualification.active_state_count == 3
    assert qualification.terminal_state_count == 3
    assert qualification.maximum_jump_bound == 2
    assert qualification.exact_tilted_total_rates_recovered is True
    assert qualification.exact_edit_family_probabilities_recovered is True
    assert qualification.exact_categorical_route_law_recovered is True
    assert qualification.exact_integer_source_law_recovered is True
    assert qualification.exact_ideal_gaussian_disintegration_recovered is True
    assert qualification.exact_bounded_normal_cell_pushforward_recovered is True
    assert qualification.cp24_compatible_address_consumption_defined is True
    assert qualification.finite_run_persistent_fresh_lineage_defined is True
    assert qualification.unconditional_bounded_fixture_completion_proved is True
    assert qualification.exact_continuous_gaussian_from_bounded_words is False
    assert qualification.production_cp24_execution_integrated is False
    assert qualification.general_cyclic_liveness_proved is False
    assert qualification.formal_test29_closed is False


def test_exact_tilted_total_route_family_and_source_disintegration():
    law = oracle.ideal_one_step_law(_fixture(), "root-r2")
    assert law.total_tilted_rate == Fraction(4)
    assert law.route_masses == (
        ("root-birth", Fraction(1, 2)),
        ("root-replacement", Fraction(1, 4)),
        ("root-death", Fraction(1, 4)),
    )
    assert law.family_masses == (
        (oracle.FAMILY_BIRTH, Fraction(1, 2)),
        (oracle.FAMILY_DEATH, Fraction(1, 4)),
        (oracle.FAMILY_REPLACEMENT, Fraction(1, 4)),
    )
    assert tuple(
        (atom.route_id, atom.source_index, atom.mass) for atom in law.atoms
    ) == (
        ("root-birth", None, Fraction(1, 2)),
        ("root-replacement", 0, Fraction(1, 8)),
        ("root-replacement", 1, Fraction(1, 8)),
        ("root-death", 0, Fraction(1, 8)),
        ("root-death", 1, Fraction(1, 8)),
    )
    assert sum((atom.mass for atom in law.atoms), Fraction()) == 1


def test_exact_gaussian_moments_and_independent_quadrature():
    gaussian = _gaussian_2d()
    assert tuple(gaussian.raw_moment(0, order) for order in range(5)) == (
        Fraction(1),
        Fraction(0),
        Fraction(1),
        Fraction(0),
        Fraction(3),
    )
    assert tuple(gaussian.raw_moment(1, order) for order in range(5)) == (
        Fraction(1),
        Fraction(1, 2),
        Fraction(17, 4),
        Fraction(49, 8),
        Fraction(865, 16),
    )
    mean = float(gaussian.mean[1])
    scale = math.sqrt(float(gaussian.variance[1]))
    for order in range(5):
        numerical, error = quad(
            lambda x, power=order: (mean + scale * x) ** power * _normal_density(x),
            -math.inf,
            math.inf,
            epsabs=1.0e-12,
            epsrel=1.0e-12,
            limit=200,
        )
        assert error < 1.0e-8
        assert numerical == pytest.approx(
            float(gaussian.raw_moment(1, order)), abs=2e-10
        )


def test_normal_cells_have_exact_declared_mass_and_quadrature_mass():
    for bits in range(1, 7):
        cells = tuple(
            oracle.NormalQuantileCell(index, bits) for index in range(1 << bits)
        )
        assert sum((cell.probability for cell in cells), Fraction()) == 1
        assert cells[0].lower_probability == 0
        assert cells[-1].upper_probability == 1
        for cell in cells:
            lower, upper = cell.standard_normal_bounds()
            numerical, error = quad(
                _normal_density,
                lower,
                upper,
                epsabs=2.0e-13,
                epsrel=2.0e-13,
                limit=200,
            )
            assert error < 1.0e-9
            assert numerical == pytest.approx(float(cell.probability), abs=2e-13)
            assert cell.cdf_mass_residual() < 2e-16
            assert math.isfinite(cell.midpoint_representative())


def test_analytic_and_enumerated_uint64_pushforwards_are_identical():
    fixture = _fixture(normal_bits=2)
    for state in fixture.states:
        if state.rank == 0:
            continue
        analytic = oracle.operational_pushforward_law(fixture, state.state_id)
        enumerated = oracle.enumerate_low_word_pushforward(fixture, state.state_id)
        assert enumerated == analytic
        assert analytic.raw64_words_consumed_per_jump == 1
        assert sum((mass for _, mass in analytic.route_masses), Fraction()) == 1


def test_normal_cell_pushforward_matches_gaussian_quantile_partition():
    fixture = _fixture(normal_bits=2)
    law = oracle.operational_pushforward_law(fixture, "root-r2")
    values = dict(law.normal_cell_joint_masses)
    for coordinate in (0, 1):
        for cell in range(4):
            assert values[("root-birth", coordinate, cell)] == Fraction(1, 8)
    for cell in range(4):
        assert values[("root-replacement", 0, cell)] == Fraction(1, 16)
    assert not any(key[1] == 1 for key in values if key[0] == "root-replacement")
    assert not any(key[0] == "root-death" for key in values)


def test_high_uint64_bits_do_not_change_the_exact_low_residue_map():
    fixture = _fixture(normal_bits=2)
    used = fixture.layout.used_bits
    assert used == 8
    for low in range(1 << used):
        baseline = oracle.select_one_step(fixture, "root-r2", low)
        high = low | (((1 << (64 - used)) - 1) << used)
        shifted = oracle.select_one_step(fixture, "root-r2", high)
        assert shifted.route_id == baseline.route_id
        assert shifted.source_index == baseline.source_index
        assert shifted.normal_cells == baseline.normal_cells
        assert shifted.decoded_word.low_word == low


def test_route_bucket_and_source_bucket_boundaries_are_exact():
    fixture = _fixture()
    selected = [oracle.select_one_step(fixture, "root-r2", code) for code in range(4)]
    assert [item.route_id for item in selected] == [
        "root-birth",
        "root-birth",
        "root-replacement",
        "root-death",
    ]
    replacement_source_zero = oracle.select_one_step(fixture, "root-r2", 2)
    replacement_source_one = oracle.select_one_step(
        fixture, "root-r2", 2 | (2 << fixture.layout.route_bits)
    )
    assert replacement_source_zero.source_index == 0
    assert replacement_source_one.source_index == 1
    child_sources = [
        oracle.select_one_step(
            fixture,
            "birth-r1",
            source_code << fixture.layout.route_bits,
        ).source_index
        for source_code in range(4)
    ]
    assert child_sources == [0, 0, 1, 2]


def test_cp24_compatible_addresses_are_direct_injective_and_consumed():
    fixture = _fixture()
    result = oracle.run_acyclic_fixture(
        fixture,
        (0, 2 << fixture.layout.route_bits),
        run_id=17,
        step_index=3,
    )
    assert tuple(transition.address.key for transition in result.transitions) == (
        (17, 6),
        (17, 6),
    )
    assert tuple(transition.address.counter for transition in result.transitions) == (
        (0, 3, 0, 0),
        (0, 3, 0, 1),
    )
    addresses = {
        (
            oracle.CP24CompatibleAddress(run_id, step, proposal).key,
            oracle.CP24CompatibleAddress(run_id, step, proposal).counter,
        )
        for run_id, step, proposal in itertools.product(range(3), range(3), range(3))
    }
    assert len(addresses) == 27


def test_explicit_addressed_word_roster_is_consumed_and_recomputed_exactly():
    fixture = _fixture()
    words = (0, 2 << fixture.layout.route_bits)
    addressed = oracle.bind_supplied_words_to_addresses(
        fixture, words, run_id=17, step_index=3
    )
    assert tuple(item.address.counter for item in addressed) == (
        (0, 3, 0, 0),
        (0, 3, 0, 1),
    )
    result = oracle.run_addressed_acyclic_fixture(
        fixture, addressed, run_id=17, step_index=3
    )
    assert (
        tuple(
            transition.selection.decoded_word.raw64_word
            for transition in result.transitions
        )
        == words
    )
    assert tuple(transition.address for transition in result.transitions) == tuple(
        item.address for item in addressed
    )
    assert (
        oracle.validate_addressed_acyclic_run_result(fixture, addressed, result)
        is result
    )


def test_addressed_word_roster_refuses_missing_reordered_alien_and_duplicate_entries():
    fixture = _fixture()
    addressed = oracle.bind_supplied_words_to_addresses(
        fixture, (0, 0), run_id=4, step_index=5
    )
    with pytest.raises(ValueError, match="exactly the initial rank"):
        oracle.run_addressed_acyclic_fixture(
            fixture, addressed[:1], run_id=4, step_index=5
        )
    with pytest.raises(oracle.FormalTest29FiniteAcyclicError, match="roster position"):
        oracle.run_addressed_acyclic_fixture(
            fixture, tuple(reversed(addressed)), run_id=4, step_index=5
        )
    with pytest.raises(oracle.FormalTest29FiniteAcyclicError, match="roster position"):
        oracle.run_addressed_acyclic_fixture(
            fixture, (addressed[0], addressed[0]), run_id=4, step_index=5
        )
    alien = replace(addressed[1], address=oracle.CP24CompatibleAddress(4, 6, 1))
    with pytest.raises(oracle.FormalTest29FiniteAcyclicError, match="roster position"):
        oracle.run_addressed_acyclic_fixture(
            fixture, (addressed[0], alien), run_id=4, step_index=5
        )
    with pytest.raises(TypeError, match="exact addressed records"):
        oracle.run_addressed_acyclic_fixture(
            fixture, (addressed[0], object()), run_id=4, step_index=5
        )


def test_addressed_word_constructor_is_exact_type_and_uint64_guarded():
    address = oracle.CP24CompatibleAddress(0, 0, 0)
    assert oracle.CP24CompatibleAddress(0, 0, 63).counter == (0, 0, 0, 63)
    with pytest.raises(ValueError, match="completed_proposals"):
        oracle.CP24CompatibleAddress(0, 0, 64)
    with pytest.raises(TypeError, match="exact CP24CompatibleAddress"):
        oracle.AddressedUint64Word((0, 6, 0), 0)
    with pytest.raises(ValueError, match="raw64_word"):
        oracle.AddressedUint64Word(address, 1 << 64)
    with pytest.raises(TypeError, match="tuple"):
        oracle.bind_supplied_words_to_addresses(
            _fixture(), [0, 0], run_id=0, step_index=0
        )


def test_birth_then_death_lineage_is_fresh_monotone_and_never_resurrected():
    fixture = _fixture()
    child_death_source_one = 2 << fixture.layout.route_bits
    result = oracle.run_acyclic_fixture(
        fixture,
        (0, child_death_source_one),
        run_id=5,
        step_index=7,
    )
    first, second = result.transitions
    assert first.selection.family == oracle.FAMILY_BIRTH
    assert first.lineage_before.active_serials == (1, 2)
    assert first.created_serial == 3
    assert first.lineage_after.active_serials == (1, 2, 3)
    assert second.selection.family == oracle.FAMILY_DEATH
    assert second.source_serial == 2
    assert second.created_serial is None
    assert result.terminal_lineage.active_serials == (1, 3)
    assert result.terminal_lineage.retired_serials == (2,)
    assert result.terminal_lineage.next_serial == 4


def test_replacement_chain_retires_and_replaces_with_fresh_serials():
    fixture = _fixture()
    root_replacement_source_one = 2 | (2 << fixture.layout.route_bits)
    child_replacement_source_zero = 0
    result = oracle.run_acyclic_fixture(
        fixture,
        (root_replacement_source_one, child_replacement_source_zero),
        run_id=9,
        step_index=11,
    )
    first, second = result.transitions
    assert first.source_serial == 2
    assert first.created_serial == 3
    assert first.lineage_after.active_serials == (1, 3)
    assert first.lineage_after.retired_serials == (2,)
    assert second.source_serial == 1
    assert second.created_serial == 4
    assert result.terminal_lineage.active_serials == (3, 4)
    assert result.terminal_lineage.retired_serials == (1, 2)
    assert result.terminal_lineage.next_serial == 5


def test_every_low_word_tape_completes_within_the_initial_rank():
    fixture = _fixture(normal_bits=1)
    low_words = range(fixture.layout.low_word_count)
    terminal_states = set()
    consumed_counts = set()
    for first_word, second_word in itertools.product(low_words, repeat=2):
        result = oracle.run_acyclic_fixture(
            fixture,
            (first_word, second_word),
            run_id=0,
            step_index=0,
        )
        assert result.terminal is True
        assert result.consumed_word_count <= result.maximum_jump_bound == 2
        assert result.unused_word_count == 2 - result.consumed_word_count
        assert len(
            {transition.address.counter for transition in result.transitions}
        ) == len(result.transitions)
        assert all(
            transition.rank_after < transition.rank_before
            for transition in result.transitions
        )
        terminal_states.add(result.terminal_state_id)
        consumed_counts.add(result.consumed_word_count)
    assert terminal_states == {
        "birth-terminal",
        "replacement-terminal",
        "death-terminal",
    }
    assert consumed_counts == {1, 2}


def test_result_recomputation_accepts_exact_and_rejects_redigested_forgery():
    fixture = _fixture()
    words = (0, 0)
    result = oracle.run_acyclic_fixture(fixture, words, run_id=3, step_index=4)
    assert oracle.validate_acyclic_run_result(fixture, words, result) is result
    forged = replace(result, unused_word_count=result.unused_word_count + 1)
    with pytest.raises(oracle.FormalTest29FiniteAcyclicError, match="reconstruction"):
        oracle.validate_acyclic_run_result(fixture, words, forged)
    with pytest.raises(oracle.FormalTest29FiniteAcyclicError, match="reconstruction"):
        oracle.validate_acyclic_run_result(fixture, (1, 0), result)


def test_bounded_word_gaussian_obstruction_is_explicit_and_exact():
    zero = oracle.bounded_word_continuous_gaussian_obstruction(0)
    two = oracle.bounded_word_continuous_gaussian_obstruction(2)
    assert zero["finite_support_upper_bound"] == 1
    assert two["finite_support_upper_bound"] == 1 << 128
    assert two["gaussian_is_non_atomic"] is True
    assert two["exact_continuous_gaussian_possible"] is False
    assert "finite support" in two["reason"]


@pytest.mark.parametrize("value", [True, 1.0, Fraction(1), "1", None])
def test_integer_boundaries_reject_non_exact_integer_types(value):
    with pytest.raises((TypeError, ValueError)):
        oracle.decode_uint64_word(_fixture().layout, value)
    with pytest.raises((TypeError, ValueError)):
        oracle.CP24CompatibleAddress(value, 0, 0)
    with pytest.raises((TypeError, ValueError)):
        oracle.bounded_word_continuous_gaussian_obstruction(value)


@pytest.mark.parametrize("word", [-1, 1 << 64])
def test_uint64_word_boundaries_are_fail_closed(word):
    with pytest.raises(ValueError, match="raw64_word"):
        oracle.decode_uint64_word(_fixture().layout, word)


def test_run_preflights_the_complete_word_tape_before_consumption():
    fixture = _fixture()
    with pytest.raises(TypeError, match="tuple"):
        oracle.run_acyclic_fixture(fixture, [0, 0], run_id=0, step_index=0)
    with pytest.raises(ValueError, match="exactly the initial rank"):
        oracle.run_acyclic_fixture(fixture, (0,), run_id=0, step_index=0)
    with pytest.raises(ValueError, match="exactly the initial rank"):
        oracle.run_acyclic_fixture(fixture, (0, 0, 0), run_id=0, step_index=0)
    with pytest.raises(TypeError, match=r"raw64_words\[1\]"):
        oracle.run_acyclic_fixture(fixture, (0, True), run_id=0, step_index=0)


def test_gaussian_destination_rejects_wrong_shapes_types_and_variances():
    with pytest.raises(TypeError, match="tuple"):
        oracle.GaussianDestination([Fraction(0)], (Fraction(1),))
    with pytest.raises(ValueError, match="dimensions differ"):
        oracle.GaussianDestination((Fraction(0),), (Fraction(1), Fraction(1)))
    with pytest.raises(TypeError, match=r"mean\[0\]"):
        oracle.GaussianDestination((0,), (Fraction(1),))
    with pytest.raises(ValueError, match=r"variance\[0\].*positive"):
        oracle.GaussianDestination((Fraction(0),), (Fraction(0),))
    with pytest.raises(ValueError, match="Gaussian dimension"):
        oracle.GaussianDestination((), ())
    gaussian = _gaussian_1d()
    with pytest.raises((TypeError, ValueError)):
        gaussian.raw_moment(True, 1)
    with pytest.raises(ValueError, match="order"):
        gaussian.raw_moment(0, 5)


def test_normal_cell_and_word_layout_resource_guards_are_fail_closed():
    with pytest.raises(ValueError, match="index"):
        oracle.NormalQuantileCell(2, 1)
    with pytest.raises(TypeError, match="bits"):
        oracle.NormalQuantileCell(0, True)
    with pytest.raises(ValueError, match="exceeds one uint64"):
        oracle.WordLayout(16, 16, 16, 3)
    with pytest.raises(TypeError, match="route_bits"):
        oracle.WordLayout(True, 1, 1, 1)


def test_route_contract_rejects_wrong_family_fibers_and_source_laws():
    gaussian = _gaussian_1d()
    with pytest.raises(ValueError, match="family"):
        oracle.RouteSpec("bad", "move", "next", Fraction(1), Fraction(1), (), gaussian)
    with pytest.raises(ValueError, match="birth routes"):
        oracle.RouteSpec(
            "bad",
            oracle.FAMILY_BIRTH,
            "next",
            Fraction(1),
            Fraction(1),
            (Fraction(1),),
            gaussian,
        )
    with pytest.raises(ValueError, match="death routes"):
        oracle.RouteSpec(
            "bad",
            oracle.FAMILY_DEATH,
            "next",
            Fraction(1),
            Fraction(1),
            (Fraction(1),),
            gaussian,
        )
    with pytest.raises(TypeError, match="Gaussian"):
        oracle.RouteSpec(
            "bad",
            oracle.FAMILY_REPLACEMENT,
            "next",
            Fraction(1),
            Fraction(1),
            (Fraction(1),),
            None,
        )
    with pytest.raises(ValueError, match="sum to one"):
        oracle.RouteSpec(
            "bad",
            oracle.FAMILY_DEATH,
            "next",
            Fraction(1),
            Fraction(1),
            (Fraction(1, 2),),
            None,
        )
    with pytest.raises(TypeError, match="base_rate"):
        oracle.RouteSpec(
            "bad", oracle.FAMILY_BIRTH, "next", 1, Fraction(1), (), gaussian
        )


def test_state_and_fixture_graph_hostilities_are_rejected():
    fixture = _fixture()
    root = fixture.state("root-r2")
    with pytest.raises(ValueError, match="rank-zero"):
        oracle.StateSpec("bad-terminal", 0, 2, root.routes[:1])
    with pytest.raises(ValueError, match="positive-rank"):
        oracle.StateSpec("bad-active", 1, 0, ())
    with pytest.raises(ValueError, match="unique"):
        oracle.FixtureSpec(
            "duplicate",
            (root, root),
            root.state_id,
            fixture.layout,
        )
    with pytest.raises(ValueError, match="initial_state_id"):
        oracle.FixtureSpec("missing-initial", fixture.states, "missing", fixture.layout)
    cyclic_route = replace(root.routes[0], next_state_id=root.state_id)
    cyclic_root = replace(root, routes=(cyclic_route,) + root.routes[1:])
    with pytest.raises(ValueError, match="strictly decrease"):
        oracle.FixtureSpec(
            "cycle",
            (cyclic_root,) + fixture.states[1:],
            cyclic_root.state_id,
            fixture.layout,
        )
    wrong_destination = replace(fixture.state("birth-terminal"), lineage_cardinality=1)
    states = tuple(
        wrong_destination if state.state_id == "birth-terminal" else state
        for state in fixture.states
    )
    with pytest.raises(ValueError, match="lineage cardinalities"):
        oracle.FixtureSpec("wrong-lineage", states, "root-r2", fixture.layout)


def test_fixture_rejects_nondyadic_routes_sources_and_oversized_gaussian():
    fixture = _fixture()
    root = fixture.state("root-r2")
    nondyadic_routes = (
        replace(root.routes[0], base_rate=Fraction(1), tilt=Fraction(1)),
        replace(root.routes[1], base_rate=Fraction(1), tilt=Fraction(1)),
        replace(root.routes[2], base_rate=Fraction(1), tilt=Fraction(1)),
    )
    with pytest.raises(ValueError, match="not representable"):
        oracle.FixtureSpec(
            "nondyadic-routes",
            (replace(root, routes=nondyadic_routes),) + fixture.states[1:],
            "root-r2",
            fixture.layout,
        )
    bad_source_route = replace(
        root.routes[1], source_masses=(Fraction(1, 3), Fraction(2, 3))
    )
    with pytest.raises(ValueError, match="not representable"):
        oracle.FixtureSpec(
            "nondyadic-source",
            (replace(root, routes=(root.routes[0], bad_source_route, root.routes[2])),)
            + fixture.states[1:],
            "root-r2",
            fixture.layout,
        )
    narrow_layout = oracle.WordLayout(2, 2, 1, 1)
    with pytest.raises(ValueError, match="dimension exceeds"):
        oracle.FixtureSpec(
            "dimension-overflow", fixture.states, "root-r2", narrow_layout
        )


def test_terminal_states_refuse_one_step_law_selection_and_pushforward():
    fixture = _fixture()
    with pytest.raises(ValueError, match="terminal state"):
        oracle.ideal_one_step_law(fixture, "death-terminal")
    with pytest.raises(ValueError, match="terminal state"):
        oracle.select_one_step(fixture, "death-terminal", 0)
    with pytest.raises(ValueError, match="terminal state"):
        oracle.operational_pushforward_law(fixture, "death-terminal")
    with pytest.raises(ValueError, match="terminal state"):
        oracle.enumerate_low_word_pushforward(fixture, "death-terminal")


def test_enumeration_guard_refuses_large_layout_without_affecting_closed_form():
    fixture = _fixture(normal_bits=7)
    assert fixture.layout.used_bits == 18
    closed = oracle.operational_pushforward_law(fixture, "root-r2")
    assert closed.total_low_words == 1 << 18
    with pytest.raises(ValueError, match="enumeration guard"):
        oracle.enumerate_low_word_pushforward(fixture, "root-r2")


def test_parent_sources_remain_exactly_bound_and_additive():
    for relative_path, expected_hash in CP19_TO_CP24_SOURCE_HASHES.items():
        path = ROOT / relative_path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
    source_text = SOURCE.read_text(encoding="utf-8")
    for relative_path in CP19_TO_CP24_SOURCE_HASHES:
        assert relative_path.rsplit("/", 1)[-1][:-3] not in source_text


def test_source_has_no_entropy_data_network_model_or_effectful_import_path():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "fractions",
        "math",
        "statistics",
        "typing",
    }
    forbidden = {
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
        "heterodiff",
    }
    assert imported_roots.isdisjoint(forbidden)


def test_public_surface_is_explicit_and_contains_no_generic_sampler_claim():
    expected = {
        "GaussianDestination",
        "NormalQuantileCell",
        "WordLayout",
        "RouteSpec",
        "StateSpec",
        "FixtureSpec",
        "ideal_one_step_law",
        "select_one_step",
        "operational_pushforward_law",
        "enumerate_low_word_pushforward",
        "bind_supplied_words_to_addresses",
        "run_acyclic_fixture",
        "run_addressed_acyclic_fixture",
        "validate_acyclic_run_result",
        "validate_addressed_acyclic_run_result",
        "qualify_finite_acyclic_fixture",
        "bounded_word_continuous_gaussian_obstruction",
    }
    assert expected <= set(oracle.__all__)
    assert not any(
        name in oracle.__all__ for name in ("sample", "sampler", "run_philox")
    )


def test_exact_fraction_component_guard_accepts_boundary_and_rejects_overflow():
    cap = oracle.MAX_EXACT_FRACTION_COMPONENT_BITS
    boundary = Fraction(1 << (cap - 1), 1)
    route = oracle.RouteSpec(
        "guard-boundary",
        oracle.FAMILY_BIRTH,
        "terminal",
        boundary,
        Fraction(1),
        (),
        _gaussian_1d(),
    )
    assert route.tilted_rate == boundary
    over = Fraction(1 << cap, 1)
    with pytest.raises(ValueError, match="exact-component guard"):
        oracle.RouteSpec(
            "guard-over",
            oracle.FAMILY_BIRTH,
            "terminal",
            over,
            Fraction(1),
            (),
            _gaussian_1d(),
        )
    over_denominator = Fraction(1, 1 << cap)
    with pytest.raises(ValueError, match="exact-component guard"):
        oracle.GaussianDestination((over_denominator,), (Fraction(1),))


def test_derived_fraction_products_normalizations_and_moments_are_guarded():
    cap = oracle.MAX_EXACT_FRACTION_COMPONENT_BITS
    factor = Fraction(1 << (cap // 2), 1)
    with pytest.raises(ValueError, match="route_tilted_rate.*exact-component guard"):
        oracle.RouteSpec(
            "derived-product-over",
            oracle.FAMILY_BIRTH,
            "terminal",
            factor,
            factor,
            (),
            _gaussian_1d(),
        )
    gaussian = oracle.GaussianDestination((factor,), (Fraction(1),))
    with pytest.raises(ValueError, match="exact-component guard"):
        gaussian.raw_moment(0, 2)
    safe = Fraction(1 << (cap // 2 - 2), 1)
    safe_route = oracle.RouteSpec(
        "derived-safe",
        oracle.FAMILY_BIRTH,
        "terminal",
        safe,
        safe,
        (),
        _gaussian_1d(),
    )
    assert (
        safe_route.tilted_rate.numerator.bit_length()
        <= oracle.MAX_EXACT_FRACTION_COMPONENT_BITS
    )


def test_machine_record_is_canonical_self_digested_and_reconstructed_exactly():
    observed = validator.validate(MACHINE_PATH)
    expected = validator.expected_record()
    assert observed == expected
    assert observed["record_sha256"] == validator._self_digest(observed)
    assert MACHINE_PATH.read_bytes() == validator._canonical_json(observed) + b"\n"


def test_machine_record_binds_authority_zero_delta_and_explicit_nonclosures():
    record = validator.validate(MACHINE_PATH)
    assert record["visible_authority"]["exact_text"] == validator.VISIBLE_AUTHORITY
    assert (
        record["visible_authority"][
            "authorizes_data_contact_entropy_science_or_submission"
        ]
        is False
    )
    assert record["named_predicate"] == (
        "FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED"
    )
    assert record["closure_delta"] == {
        "component_predicates_closed": 1,
        "component_predicate_ids": [record["named_predicate"]],
        "formal_tests_closed": 0,
        "fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "scientific_claims_promoted": 0,
        "tracker_files_edited": 0,
        "formal_test29_state": "OPEN",
        "blocker_b12_state": "OPEN_UNCHANGED",
    }
    truth = record["semantic_receipt"]["qualification_truth_table"]
    assert truth["exact_continuous_gaussian_from_bounded_words"] is False
    assert truth["production_cp24_execution_integrated"] is False
    assert truth["general_cyclic_liveness_proved"] is False
    assert truth["formal_test29_closed"] is False
    assert record["publication_boundary"]["internal_evidence_only"] is True
    assert (
        record["publication_boundary"][
            "anonymous_or_public_submission_inclusion_permitted"
        ]
        is False
    )


def test_machine_semantic_receipt_is_exact_exhaustive_and_resource_bounded():
    receipt = validator.validate(MACHINE_PATH)["semantic_receipt"]
    assert receipt["layout"] == {
        "route_bits": 2,
        "source_bits": 2,
        "normal_bits": 1,
        "maximum_normal_dimension": 2,
        "used_bits": 6,
        "low_word_count": 64,
        "raw64_words_per_jump": 1,
        "cp24_completed_proposals_minimum": 0,
        "cp24_completed_proposals_maximum_exclusive": 64,
    }
    assert receipt["exact_fraction_component_bit_cap"] == 4096
    assert receipt["law_premises"] == {
        "route_and_source_source_law": "ABSTRACT_UNIFORM_UINT64",
        "route_and_source_source_law_operationally_proved": False,
        "ideal_gaussian_fiber": "INDEPENDENT_STANDARD_NORMAL",
        "ideal_gaussian_fiber_operationally_sampled": False,
        "bounded_word_output_kind": "NORMAL_QUANTILE_CELL_INDEX_ONLY",
        "bounded_word_output_is_continuous_coordinate": False,
    }
    assert receipt["root_total_tilted_rate"] == "4/1"
    assert receipt["exhaustive_completion"] == {
        "word_tapes_checked": 4096,
        "expected_word_tapes": 4096,
        "terminal_counts": {
            "birth-terminal": 2048,
            "death-terminal": 1024,
            "replacement-terminal": 1024,
        },
        "consumed_word_counts": {"1": 1024, "2": 3072},
        "all_runs_terminal": True,
        "all_runs_within_initial_rank": True,
        "every_consumed_address_trace_unique": True,
        "complete_address_roster_preflighted_before_interpretation": True,
    }
    assert (
        receipt["gaussian_moments"][
            "maximum_numeric_cdf_mass_residual_below_3e_minus_16"
        ]
        is True
    )
    assert (
        receipt["bounded_word_obstruction"]["exact_continuous_gaussian_possible"]
        is False
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("state",), "FORMAL_TEST29_CLOSED"),
        (("closure_delta", "formal_tests_closed"), 1),
        (("closure_delta", "fields_closed"), 1),
        (("closure_delta", "blockers_closed"), 1),
        (("closure_delta", "result_slots_filled"), 1),
        (("closure_delta", "formal_test29_state"), "CLOSED"),
        (
            (
                "semantic_receipt",
                "qualification_truth_table",
                "exact_continuous_gaussian_from_bounded_words",
            ),
            True,
        ),
        (
            (
                "semantic_receipt",
                "qualification_truth_table",
                "production_cp24_execution_integrated",
            ),
            True,
        ),
        (
            (
                "semantic_receipt",
                "qualification_truth_table",
                "general_cyclic_liveness_proved",
            ),
            True,
        ),
        (
            (
                "semantic_receipt",
                "qualification_truth_table",
                "formal_test29_closed",
            ),
            True,
        ),
        (("publication_boundary", "internal_evidence_only"), False),
        (("operation_receipt", "scientific_execution_performed"), True),
    ],
)
def test_redigested_machine_semantic_promotions_are_rejected(tmp_path, path, value):
    record = copy.deepcopy(validator.validate(MACHINE_PATH))
    cursor = record
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    record["record_sha256"] = validator._self_digest(record)
    forged = tmp_path / "forged.json"
    forged.write_bytes(validator._canonical_json(record) + b"\n")
    os.chmod(forged, 0o644)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError,
        match="reconstructed expected record",
    ):
        validator.validate(forged)


def test_machine_wrong_self_digest_noncanonical_and_duplicate_keys_are_rejected(
    tmp_path,
):
    record = copy.deepcopy(validator.validate(MACHINE_PATH))
    wrong_digest = tmp_path / "wrong-digest.json"
    record["record_sha256"] = "0" * 64
    wrong_digest.write_bytes(validator._canonical_json(record) + b"\n")
    os.chmod(wrong_digest, 0o644)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError, match="self-digest"
    ):
        validator.validate(wrong_digest)

    record = copy.deepcopy(validator.validate(MACHINE_PATH))
    pretty = tmp_path / "pretty.json"
    pretty.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.chmod(pretty, 0o644)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError, match="not canonical"
    ):
        validator.validate(pretty)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"state":"a","state":"b"}\n', encoding="utf-8")
    os.chmod(duplicate, 0o644)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError, match="duplicate key"
    ):
        validator.validate(duplicate)


def test_validator_refuses_machine_symlink_hardlink_and_wrong_mode(tmp_path):
    symlink = tmp_path / "machine-symlink.json"
    symlink.symlink_to(MACHINE_PATH)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError, match="symlink"
    ):
        validator.validate(symlink)

    hardlink = tmp_path / "machine-hardlink.json"
    os.link(MACHINE_PATH, hardlink)
    try:
        with pytest.raises(
            validator.FormalTest29QualificationValidationError, match="hard-linked"
        ):
            validator.validate(hardlink)
    finally:
        hardlink.unlink()

    wrong_mode = tmp_path / "wrong-mode.json"
    wrong_mode.write_bytes(MACHINE_PATH.read_bytes())
    os.chmod(wrong_mode, 0o600)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError, match="0644"
    ):
        validator.validate(wrong_mode)


def test_validator_refuses_predecessor_drift_even_with_regular_custody(tmp_path):
    role, relative_path, expected_hash = validator.PARENT_BINDINGS[0]
    original = ROOT / relative_path
    drifted = tmp_path / original.name
    drifted.write_bytes(original.read_bytes() + b"# drift\n")
    os.chmod(drifted, 0o644)
    with pytest.raises(
        validator.FormalTest29QualificationValidationError,
        match="predecessor SHA-256 differs",
    ):
        validator._binding(drifted, role=role, expected_sha256=expected_hash)


def test_validator_rejects_pure_source_drift_before_import_execution(tmp_path):
    marker = tmp_path / "must-not-exist"
    payload = (
        "from pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('executed')\n"
    ).encode("utf-8")
    with pytest.raises(
        validator.FormalTest29QualificationValidationError,
        match="differs before import",
    ):
        validator._load_bound_oracle(payload)
    assert not marker.exists()


def test_validator_executes_verified_payload_without_reopening_source_path(
    tmp_path, monkeypatch
):
    marker = tmp_path / "unbound-path-bytes-executed"
    swapped_path = tmp_path / "swapped_source.py"
    swapped_path.write_text(
        "from pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('unbound execution')\n",
        encoding="utf-8",
    )
    os.chmod(swapped_path, 0o644)
    py_compile.compile(str(swapped_path), doraise=True)
    verified_payload = SOURCE.read_bytes()
    monkeypatch.setattr(validator, "SOURCE_PATH", swapped_path)
    loaded = validator._load_bound_oracle(verified_payload)
    assert loaded.FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION == (
        "formal-test29-finite-acyclic-route-oracle-v1"
    )
    assert not marker.exists()


def test_validator_source_is_read_only_and_has_no_external_effect_calls():
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_call_attributes = {
        "write_bytes",
        "write_text",
        "unlink",
        "rename",
        "replace",
        "mkdir",
        "makedirs",
        "remove",
        "rmdir",
        "system",
        "popen",
        "run",
        "Popen",
        "urlopen",
        "request",
    }
    observed = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert observed.isdisjoint(forbidden_call_attributes)
    import_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_roots.add(node.module.split(".")[0])
    assert "requests" not in import_roots
    assert "urllib" not in import_roots


def test_five_file_package_and_all_predecessors_are_regular_0644_single_link():
    paths = [
        ROOT / "PROJECT_FORMAL_TEST29_FINITE_ACYCLIC_ROUTE_QUALIFICATION.md",
        SOURCE,
        VALIDATOR_PATH,
        MACHINE_PATH,
        Path(__file__),
    ] + [ROOT / path for _, path, _ in validator.PARENT_BINDINGS]
    for path in paths:
        metadata = path.lstat()
        assert path.is_file() and not path.is_symlink()
        assert metadata.st_mode & 0o777 == 0o644
        assert metadata.st_nlink == 1
