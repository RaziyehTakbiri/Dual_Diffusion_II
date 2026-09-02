"""Pure, supplied-input qualification for a narrow Formal-Test-30 precursor.

This module constructs a coupled family of synthetic mixed OU/edit paths from
explicit values carrying the checkpoint-23 tag-4/tag-5 address layout.  Only
the finest frozen grid is addressed: the CP23 address has no level limb, so
independent use of the same run at several levels would collide.  Every
coarser half-step increment is instead derived as the exact sum of the two
corresponding finer half-step increments for each lineage that survives the
whole interval.

The fixture has deterministic boundary edits (birth, replacement, death) and
additive-noise OU coordinates.  It checks persistent lineage, strong path
differences on common checkpoints, exact edit-family counts, and convergence
of the numerical endpoint Gaussian law to the analytic OU law.  Supplied
increment values are data, not random draws.  Consequently this module does
not certify a Gaussian/source law, consume a live Philox stream, implement the
general frozen-jump subproblem, integrate the complete sampler, perform an
independent recomputation, or close Formal Test 30.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from numbers import Real
from typing import Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "heterodiff-formal-test30-synthetic-coupled-path-v1"
QUALIFICATION_SCOPE = (
    "SUPPLIED_FINEST_CP23_TAG4_TAG5_VALUES;DERIVED_COARSE_SUMS;"
    "FROZEN_SYNTHETIC_BOUNDARY_EDITS;ADDITIVE_OU_HEUN;"
    "PATH_EDIT_ENDPOINT_LAW_QUALIFICATION_ONLY"
)
STRICT_NONCLAIMS = (
    "NO_LIVE_PHILOX_OR_EXTERNAL_ENTROPY;NO_GAUSSIAN_OR_INDEPENDENCE_LAW;"
    "NO_GENERAL_FROZEN_JUMP_OR_STRANG_INTEGRATION;NO_WHOLE_METHOD;"
    "NO_SCIENTIFIC_EXECUTION_OR_INDEPENDENT_RECOMPUTATION;"
    "FORMAL_TEST30_REMAINS_PENDING"
)
INPUT_SEMANTICS = (
    "PHYSICAL_HALF_STEP_INCREMENT_DELTA_W_NOT_STANDARDIZED_NORMAL_Z;"
    "COARSE_DELTA_W_EQUALS_EXACT_DYADIC_REAL_SUM_OF_BINARY64_LEAF_VALUES;"
    "DERIVED_SUM_ROUNDED_ONCE_ONLY_WHEN_SIMULATED"
)
PATH_NORM = (
    "MAX_ABSOLUTE_CONTINUOUS_COORDINATE_DIFFERENCE_AT_FROZEN_SHARED_"
    "PRE_AND_POST_EDIT_CHECKPOINTS_NOT_CONTINUUM_SUP_NORM"
)
ENDPOINT_METRIC = (
    "MAX_COMPONENT_ONE_DIMENSIONAL_GAUSSIAN_W2_UNDER_IDEAL_IID_GAUSSIAN_"
    "MOMENT_PREMISE_AGAINST_SYNTHETIC_ANALYTIC_OU_ORACLE_NOT_PRODUCTION_"
    "ENDPOINT_LAW"
)
ENDPOINT_LAW_PREMISE = (
    "HYPOTHETICAL_INDEPENDENT_CENTERED_GAUSSIAN_HALF_INCREMENTS_WITH_"
    "VARIANCE_EQUAL_TO_HALF_STEP;NOT_ASSERTED_OF_SUPPLIED_VALUES"
)
FAILURE_POLICY = "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_TOLERANCE_SUBSTITUTION"

DOMAIN_BROWNIAN_LEFT = "brownian_left"
DOMAIN_BROWNIAN_RIGHT = "brownian_right"
TAG_BROWNIAN_LEFT = 4
TAG_BROWNIAN_RIGHT = 5
_DOMAIN_BY_TAG = {
    TAG_BROWNIAN_LEFT: DOMAIN_BROWNIAN_LEFT,
    TAG_BROWNIAN_RIGHT: DOMAIN_BROWNIAN_RIGHT,
}
_MAX_UINT64 = (1 << 64) - 1


class SyntheticCoupledPathError(ValueError):
    """Raised when supplied coupling or frozen lineage custody is invalid."""


def _exact_uint64(value: object, *, name: str, positive: bool = False) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact built-in integer" % name)
    checked = value
    minimum = 1 if positive else 0
    if checked < minimum or checked > _MAX_UINT64:
        raise ValueError("%s lies outside its uint64 range" % name)
    return checked


def _finite_real(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean value" % name)
    checked = float(value)
    if not math.isfinite(checked):
        raise ValueError("%s must be finite" % name)
    return checked


def _positive_real(value: object, *, name: str) -> float:
    checked = _finite_real(value, name=name)
    if checked <= 0.0:
        raise ValueError("%s must be greater than zero" % name)
    return checked


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class CP23BrownianAddress:
    """The exact public CP23 key/counter shape used by a supplied value."""

    domain: str
    domain_tag: int
    run_id: int
    step_index: int
    occurrence_serial: int
    proposal_index: int
    philox_key: Tuple[int, int]
    philox_counter: Tuple[int, int, int, int]

    def __post_init__(self) -> None:
        if type(self.domain) is not str:
            raise TypeError("address.domain must be exact text")
        tag = _exact_uint64(self.domain_tag, name="address.domain_tag")
        if tag not in _DOMAIN_BY_TAG or self.domain != _DOMAIN_BY_TAG[tag]:
            raise SyntheticCoupledPathError(
                "address is not an exact tag-4/tag-5 domain"
            )
        run_id = _exact_uint64(self.run_id, name="address.run_id")
        step = _exact_uint64(self.step_index, name="address.step_index")
        serial = _exact_uint64(
            self.occurrence_serial,
            name="address.occurrence_serial",
            positive=True,
        )
        proposal = _exact_uint64(self.proposal_index, name="address.proposal_index")
        if proposal != 0:
            raise SyntheticCoupledPathError(
                "CP23 Brownian addresses require proposal index zero"
            )
        if type(self.philox_key) is not tuple or type(self.philox_counter) is not tuple:
            raise TypeError("address key and counter must be exact tuples")
        if len(self.philox_key) != 2 or any(
            type(word) is not int for word in self.philox_key
        ):
            raise TypeError("address key words must be exact built-in integers")
        if len(self.philox_counter) != 4 or any(
            type(word) is not int for word in self.philox_counter
        ):
            raise TypeError("address counter words must be exact built-in integers")
        expected_key = (run_id, tag)
        expected_counter = (0, step, serial, 0)
        if self.philox_key != expected_key:
            raise SyntheticCoupledPathError("address key differs from CP23")
        if self.philox_counter != expected_counter:
            raise SyntheticCoupledPathError("address counter differs from CP23")
        object.__setattr__(self, "domain_tag", tag)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "step_index", step)
        object.__setattr__(self, "occurrence_serial", serial)
        object.__setattr__(self, "proposal_index", proposal)
        object.__setattr__(self, "philox_key", expected_key)
        object.__setattr__(self, "philox_counter", expected_counter)

    @property
    def identity(self) -> Tuple[int, int, int, int]:
        return (
            self.domain_tag,
            self.step_index,
            self.occurrence_serial,
            self.proposal_index,
        )


@dataclass(frozen=True)
class AddressedBrownianIncrement:
    """One caller-supplied finite increment attached to a CP23-shaped address."""

    address: CP23BrownianAddress
    increment: float

    def __post_init__(self) -> None:
        if type(self.address) is not CP23BrownianAddress:
            raise TypeError("increment.address must be an exact CP23BrownianAddress")
        object.__setattr__(
            self, "increment", _finite_real(self.increment, name="increment")
        )


@dataclass(frozen=True)
class SyntheticOccurrence:
    serial: int
    kind: str
    coordinate: float

    def __post_init__(self) -> None:
        serial = _exact_uint64(self.serial, name="occurrence.serial", positive=True)
        if type(self.kind) is not str:
            raise TypeError("occurrence.kind must be exact text")
        if self.kind not in ("A", "B"):
            raise ValueError("occurrence.kind must be A or B")
        coordinate = _finite_real(self.coordinate, name="occurrence.coordinate")
        object.__setattr__(self, "serial", serial)
        object.__setattr__(self, "coordinate", coordinate)


@dataclass(frozen=True)
class FrozenLineageEdit:
    """One deterministic edit at a coarsest-grid boundary."""

    coarsest_boundary: int
    kind: str
    source_serial: Optional[int]
    created: Optional[SyntheticOccurrence]

    def __post_init__(self) -> None:
        boundary = _exact_uint64(
            self.coarsest_boundary, name="edit.coarsest_boundary", positive=True
        )
        if type(self.kind) is not str:
            raise TypeError("edit.kind must be exact text")
        if self.kind not in ("birth", "death", "replacement"):
            raise ValueError("edit.kind is unknown")
        source = self.source_serial
        if source is not None:
            source = _exact_uint64(source, name="edit.source_serial", positive=True)
        if self.created is not None and type(self.created) is not SyntheticOccurrence:
            raise TypeError("edit.created must be an exact SyntheticOccurrence")
        if self.kind == "birth" and (source is not None or self.created is None):
            raise ValueError("birth requires only a created occurrence")
        if self.kind == "death" and (source is None or self.created is not None):
            raise ValueError("death requires only a source serial")
        if self.kind == "replacement" and (source is None or self.created is None):
            raise ValueError("replacement requires source and created occurrence")
        object.__setattr__(self, "coarsest_boundary", boundary)
        object.__setattr__(self, "source_serial", source)


@dataclass(frozen=True)
class FrozenSyntheticDesign:
    """Frozen levels, edit schedule, OU parameters, and pass tolerances."""

    run_id: int
    levels: Tuple[int, ...]
    horizon: float
    mean_reversion: float
    diffusion: float
    long_run_mean_a: float
    long_run_mean_b: float
    initial_occurrences: Tuple[SyntheticOccurrence, ...]
    edits: Tuple[FrozenLineageEdit, ...]
    path_tolerance: float
    endpoint_w2_tolerance: float
    require_strict_path_contraction: bool

    def __post_init__(self) -> None:
        run_id = _exact_uint64(self.run_id, name="design.run_id")
        if type(self.levels) is not tuple or len(self.levels) < 3:
            raise TypeError(
                "design.levels must be an exact tuple with at least 3 levels"
            )
        checked_levels = tuple(
            _exact_uint64(level, name="design.levels[%d]" % index, positive=True)
            for index, level in enumerate(self.levels)
        )
        if checked_levels != tuple(sorted(set(checked_levels))):
            raise ValueError("design.levels must be strictly increasing")
        if checked_levels != tuple(range(checked_levels[0], checked_levels[-1] + 1)):
            raise ValueError("design.levels must be consecutive dyadic exponents")
        if checked_levels[-1] > 16:
            raise ValueError("synthetic finest level exceeds its local resource bound")
        horizon = _positive_real(self.horizon, name="design.horizon")
        theta = _positive_real(self.mean_reversion, name="design.mean_reversion")
        diffusion = _positive_real(self.diffusion, name="design.diffusion")
        mean_a = _finite_real(self.long_run_mean_a, name="design.long_run_mean_a")
        mean_b = _finite_real(self.long_run_mean_b, name="design.long_run_mean_b")
        path_tolerance = _positive_real(
            self.path_tolerance, name="design.path_tolerance"
        )
        endpoint_tolerance = _positive_real(
            self.endpoint_w2_tolerance, name="design.endpoint_w2_tolerance"
        )
        if type(self.require_strict_path_contraction) is not bool:
            raise TypeError("design.require_strict_path_contraction must be bool")
        if type(self.initial_occurrences) is not tuple or not self.initial_occurrences:
            raise TypeError("design.initial_occurrences must be a nonempty tuple")
        if any(
            type(item) is not SyntheticOccurrence for item in self.initial_occurrences
        ):
            raise TypeError("initial occurrences have the wrong exact type")
        initial_serials = tuple(item.serial for item in self.initial_occurrences)
        if initial_serials != tuple(range(1, len(initial_serials) + 1)):
            raise ValueError("initial lineage serials must be contiguous from one")
        if type(self.edits) is not tuple or not self.edits:
            raise TypeError("design.edits must be a nonempty exact tuple")
        if any(type(item) is not FrozenLineageEdit for item in self.edits):
            raise TypeError("design edits have the wrong exact type")
        coarsest_steps = 1 << checked_levels[0]
        boundaries = tuple(item.coarsest_boundary for item in self.edits)
        if boundaries != tuple(sorted(set(boundaries))):
            raise ValueError("edit boundaries must be unique and increasing")
        if boundaries[-1] >= coarsest_steps:
            raise ValueError("edits must occur strictly inside the horizon")
        _replay_lineage(self.initial_occurrences, self.edits)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "levels", checked_levels)
        object.__setattr__(self, "horizon", horizon)
        object.__setattr__(self, "mean_reversion", theta)
        object.__setattr__(self, "diffusion", diffusion)
        object.__setattr__(self, "long_run_mean_a", mean_a)
        object.__setattr__(self, "long_run_mean_b", mean_b)
        object.__setattr__(self, "path_tolerance", path_tolerance)
        object.__setattr__(self, "endpoint_w2_tolerance", endpoint_tolerance)

    @property
    def coarsest_level(self) -> int:
        return self.levels[0]

    @property
    def finest_level(self) -> int:
        return self.levels[-1]


@dataclass(frozen=True)
class LineageReplay:
    final_occurrences: Tuple[SyntheticOccurrence, ...]
    retired_serials: Tuple[int, ...]
    next_serial: int
    edit_counts: Tuple[Tuple[str, int], ...]


def _replay_lineage(
    initial: Tuple[SyntheticOccurrence, ...], edits: Tuple[FrozenLineageEdit, ...]
) -> LineageReplay:
    live: Dict[int, SyntheticOccurrence] = {item.serial: item for item in initial}
    retired = []
    next_serial = len(initial) + 1
    counts = {"birth": 0, "death": 0, "replacement": 0}
    for edit in edits:
        if edit.source_serial is not None and edit.source_serial not in live:
            raise SyntheticCoupledPathError("edit source lineage is not live")
        if edit.created is not None:
            if edit.created.serial != next_serial:
                raise SyntheticCoupledPathError(
                    "created lineage is not the next fresh monotone serial"
                )
            if edit.created.serial in live or edit.created.serial in retired:
                raise SyntheticCoupledPathError("created lineage serial was reused")
        if edit.kind == "birth":
            live[edit.created.serial] = edit.created  # type: ignore[union-attr]
            next_serial += 1
        elif edit.kind == "death":
            retired.append(edit.source_serial)
            del live[edit.source_serial]  # type: ignore[index]
        else:
            retired.append(edit.source_serial)
            del live[edit.source_serial]  # type: ignore[index]
            live[edit.created.serial] = edit.created  # type: ignore[union-attr]
            next_serial += 1
        counts[edit.kind] += 1
    return LineageReplay(
        final_occurrences=tuple(live[key] for key in sorted(live)),
        retired_serials=tuple(retired),
        next_serial=next_serial,
        edit_counts=tuple(
            (key, counts[key]) for key in ("birth", "death", "replacement")
        ),
    )


def frozen_synthetic_design() -> FrozenSyntheticDesign:
    """Return the exact version-one design; changing it requires a new schema."""

    return FrozenSyntheticDesign(
        run_id=23030,
        levels=(2, 3, 4, 5),
        horizon=1.0,
        mean_reversion=0.7,
        diffusion=0.8,
        long_run_mean_a=0.35,
        long_run_mean_b=-0.25,
        initial_occurrences=(
            SyntheticOccurrence(1, "A", 0.75),
            SyntheticOccurrence(2, "B", -0.4),
        ),
        edits=(
            FrozenLineageEdit(1, "birth", None, SyntheticOccurrence(3, "A", 0.2)),
            FrozenLineageEdit(2, "replacement", 1, SyntheticOccurrence(4, "B", -0.1)),
            FrozenLineageEdit(3, "death", 2, None),
        ),
        path_tolerance=0.025,
        endpoint_w2_tolerance=0.006,
        require_strict_path_contraction=True,
    )


def _design_payload(design: FrozenSyntheticDesign) -> Mapping[str, object]:
    return {
        "run_id": design.run_id,
        "levels": list(design.levels),
        "horizon_hex": design.horizon.hex(),
        "mean_reversion_hex": design.mean_reversion.hex(),
        "diffusion_hex": design.diffusion.hex(),
        "long_run_mean_a_hex": design.long_run_mean_a.hex(),
        "long_run_mean_b_hex": design.long_run_mean_b.hex(),
        "initial_occurrences": [
            {
                "serial": item.serial,
                "kind": item.kind,
                "coordinate_hex": item.coordinate.hex(),
            }
            for item in design.initial_occurrences
        ],
        "edits": [
            {
                "coarsest_boundary": edit.coarsest_boundary,
                "kind": edit.kind,
                "source_serial": edit.source_serial,
                "created": None
                if edit.created is None
                else {
                    "serial": edit.created.serial,
                    "kind": edit.created.kind,
                    "coordinate_hex": edit.created.coordinate.hex(),
                },
            }
            for edit in design.edits
        ],
        "path_tolerance_hex": design.path_tolerance.hex(),
        "endpoint_w2_tolerance_hex": design.endpoint_w2_tolerance.hex(),
        "require_strict_path_contraction": design.require_strict_path_contraction,
        "input_semantics": INPUT_SEMANTICS,
        "path_norm": PATH_NORM,
        "endpoint_metric": ENDPOINT_METRIC,
        "endpoint_law_premise": ENDPOINT_LAW_PREMISE,
        "failure_policy": FAILURE_POLICY,
    }


def _require_exact_frozen_design_v1(
    design: FrozenSyntheticDesign,
) -> FrozenSyntheticDesign:
    if type(design) is not FrozenSyntheticDesign:
        raise TypeError("design must be an exact FrozenSyntheticDesign")
    expected = frozen_synthetic_design()
    if design != expected:
        raise SyntheticCoupledPathError(
            "the named v1 qualification requires the exact frozen design"
        )
    return design


def _edits_by_level_boundary(
    design: FrozenSyntheticDesign, level: int
) -> Mapping[int, FrozenLineageEdit]:
    scale = 1 << (level - design.coarsest_level)
    return {edit.coarsest_boundary * scale: edit for edit in design.edits}


def _live_roster_by_step(
    design: FrozenSyntheticDesign, level: int
) -> Tuple[Tuple[int, ...], ...]:
    live = {item.serial: item for item in design.initial_occurrences}
    edits = _edits_by_level_boundary(design, level)
    rosters = []
    for step in range(1 << level):
        if step in edits:
            _apply_edit(live, edits[step])
        rosters.append(tuple(sorted(live)))
    return tuple(rosters)


def _apply_edit(live: Dict[int, SyntheticOccurrence], edit: FrozenLineageEdit) -> None:
    if edit.source_serial is not None and edit.source_serial not in live:
        raise SyntheticCoupledPathError("runtime edit source lineage is not live")
    if edit.kind == "birth":
        live[edit.created.serial] = edit.created  # type: ignore[union-attr]
    elif edit.kind == "death":
        del live[edit.source_serial]  # type: ignore[index]
    else:
        del live[edit.source_serial]  # type: ignore[index]
        live[edit.created.serial] = edit.created  # type: ignore[union-attr]


_FIXED_Z_NUMERATORS = (-15, -9, -5, -3, -1, 1, 3, 5, 9, 15, 7, -7, 11, -11, 13, -13)


def build_frozen_explicit_inputs(
    design: Optional[FrozenSyntheticDesign] = None,
) -> Tuple[AddressedBrownianIncrement, ...]:
    """Build the frozen, non-random finest-grid payload used by local tests.

    This convenience fixture is deterministic data construction, not a source
    sampler.  :func:`qualify_synthetic_coupled_path` accepts an independently
    supplied tuple with the same exact roster.
    """

    checked = frozen_synthetic_design() if design is None else design
    checked = _require_exact_frozen_design_v1(checked)
    level = checked.finest_level
    rosters = _live_roster_by_step(checked, level)
    # At level five a half-step has duration 1/64.  Dividing the fixed integer
    # table by 64 therefore gives a transparent, exactly dyadic test payload.
    scale = float(1 << (level + 1))
    result = []
    for step, serials in enumerate(rosters):
        for serial in serials:
            for tag in (TAG_BROWNIAN_LEFT, TAG_BROWNIAN_RIGHT):
                table_index = (37 * step + 19 * serial + 11 * tag) % len(
                    _FIXED_Z_NUMERATORS
                )
                value = _FIXED_Z_NUMERATORS[table_index] / scale
                result.append(
                    AddressedBrownianIncrement(
                        address=CP23BrownianAddress(
                            domain=_DOMAIN_BY_TAG[tag],
                            domain_tag=tag,
                            run_id=checked.run_id,
                            step_index=step,
                            occurrence_serial=serial,
                            proposal_index=0,
                            philox_key=(checked.run_id, tag),
                            philox_counter=(0, step, serial, 0),
                        ),
                        increment=value,
                    )
                )
    return tuple(result)


IncrementKey = Tuple[int, int, int]
IncrementValue = Fraction


def _validate_finest_inputs(
    design: FrozenSyntheticDesign,
    supplied: Tuple[AddressedBrownianIncrement, ...],
) -> Dict[IncrementKey, Fraction]:
    if type(supplied) is not tuple:
        raise TypeError("supplied increments must be an exact tuple")
    rosters = _live_roster_by_step(design, design.finest_level)
    expected = tuple(
        (step, serial, tag)
        for step, serials in enumerate(rosters)
        for serial in serials
        for tag in (TAG_BROWNIAN_LEFT, TAG_BROWNIAN_RIGHT)
    )
    observed = []
    values: Dict[IncrementKey, Fraction] = {}
    address_identities = set()
    for index, item in enumerate(supplied):
        if type(item) is not AddressedBrownianIncrement:
            raise TypeError("supplied increment %d has the wrong exact type" % index)
        address = item.address
        if address.run_id != design.run_id:
            raise SyntheticCoupledPathError("supplied increment belongs to another run")
        key = (address.step_index, address.occurrence_serial, address.domain_tag)
        if address.identity in address_identities:
            raise SyntheticCoupledPathError("a CP23 Brownian address was reused")
        address_identities.add(address.identity)
        if key in values:
            raise SyntheticCoupledPathError("a semantic fine increment was duplicated")
        observed.append(key)
        values[key] = Fraction.from_float(item.increment)
    if tuple(observed) != expected:
        raise SyntheticCoupledPathError(
            "supplied fine increments do not equal the frozen canonical roster"
        )
    return values


def _derive_all_levels(
    design: FrozenSyntheticDesign,
    finest: Mapping[IncrementKey, Fraction],
) -> Tuple[Tuple[int, Dict[IncrementKey, Fraction]], ...]:
    blocks = [(design.finest_level, dict(finest))]
    current = dict(finest)
    for fine_level in range(design.finest_level, design.coarsest_level, -1):
        coarse_level = fine_level - 1
        rosters = _live_roster_by_step(design, coarse_level)
        coarse: Dict[IncrementKey, Fraction] = {}
        for step, serials in enumerate(rosters):
            for serial in serials:
                left = (
                    current[(2 * step, serial, TAG_BROWNIAN_LEFT)]
                    + current[(2 * step, serial, TAG_BROWNIAN_RIGHT)]
                )
                right = (
                    current[(2 * step + 1, serial, TAG_BROWNIAN_LEFT)]
                    + current[(2 * step + 1, serial, TAG_BROWNIAN_RIGHT)]
                )
                coarse[(step, serial, TAG_BROWNIAN_LEFT)] = left
                coarse[(step, serial, TAG_BROWNIAN_RIGHT)] = right
                # Fraction.from_float gives the exact dyadic represented by
                # every supplied binary64 leaf.  Thus these equalities are
                # mathematical dyadic identities, not tolerance comparisons.
                if left - current[(2 * step, serial, TAG_BROWNIAN_LEFT)] != (
                    current[(2 * step, serial, TAG_BROWNIAN_RIGHT)]
                ):
                    raise ArithmeticError("left coarse dyadic sum was not exact")
                if right - current[(2 * step + 1, serial, TAG_BROWNIAN_LEFT)] != (
                    current[(2 * step + 1, serial, TAG_BROWNIAN_RIGHT)]
                ):
                    raise ArithmeticError("right coarse dyadic sum was not exact")
        blocks.append((coarse_level, coarse))
        current = coarse
    return tuple(reversed(blocks))


def _kind_mean(design: FrozenSyntheticDesign, kind: str) -> float:
    return design.long_run_mean_a if kind == "A" else design.long_run_mean_b


def _heun_half(
    coordinate: float,
    *,
    duration: float,
    increment: float,
    theta: float,
    diffusion: float,
    long_run_mean: float,
) -> float:
    drift = -theta * (coordinate - long_run_mean)
    predictor = coordinate + duration * drift + diffusion * increment
    predictor_drift = -theta * (predictor - long_run_mean)
    result = (
        coordinate + 0.5 * duration * (drift + predictor_drift) + diffusion * increment
    )
    if not math.isfinite(result):
        raise ArithmeticError("synthetic Heun coordinate became non-finite")
    return result


@dataclass(frozen=True)
class LevelQualification:
    level: int
    step_count: int
    checkpoint_states: Tuple[Tuple[Tuple[int, float], ...], ...]
    final_lineage: Tuple[Tuple[int, str], ...]
    retired_serials: Tuple[int, ...]
    edit_counts: Tuple[Tuple[str, int], ...]
    endpoint_w2_max: float
    endpoint_mean_error_max: float
    endpoint_standard_deviation_error_max: float


def _simulate_level(
    design: FrozenSyntheticDesign,
    level: int,
    increments: Mapping[IncrementKey, Fraction],
) -> LevelQualification:
    live: Dict[int, SyntheticOccurrence] = {
        item.serial: item for item in design.initial_occurrences
    }
    retired = []
    counts = {"birth": 0, "death": 0, "replacement": 0}
    edits = _edits_by_level_boundary(design, level)
    dt = design.horizon / float(1 << level)
    half = 0.5 * dt
    checkpoint_scale = 1 << (level - design.coarsest_level)
    checkpoints = [tuple((serial, live[serial].coordinate) for serial in sorted(live))]
    for step in range(1 << level):
        updated: Dict[int, SyntheticOccurrence] = {}
        for serial in sorted(live):
            occurrence = live[serial]
            coordinate = occurrence.coordinate
            coordinate = _heun_half(
                coordinate,
                duration=half,
                increment=float(increments[(step, serial, TAG_BROWNIAN_LEFT)]),
                theta=design.mean_reversion,
                diffusion=design.diffusion,
                long_run_mean=_kind_mean(design, occurrence.kind),
            )
            coordinate = _heun_half(
                coordinate,
                duration=half,
                increment=float(increments[(step, serial, TAG_BROWNIAN_RIGHT)]),
                theta=design.mean_reversion,
                diffusion=design.diffusion,
                long_run_mean=_kind_mean(design, occurrence.kind),
            )
            updated[serial] = SyntheticOccurrence(serial, occurrence.kind, coordinate)
        live = updated
        boundary = step + 1
        if boundary % checkpoint_scale == 0:
            checkpoints.append(
                tuple((serial, live[serial].coordinate) for serial in sorted(live))
            )
        if boundary in edits:
            edit = edits[boundary]
            if edit.source_serial is not None:
                retired.append(edit.source_serial)
            _apply_edit(live, edit)
            counts[edit.kind] += 1
            if boundary % checkpoint_scale == 0:
                # Both pre-edit and post-edit states are retained.  This keeps
                # retired paths in the metric up to their exact retirement.
                checkpoints.append(
                    tuple((serial, live[serial].coordinate) for serial in sorted(live))
                )

    moment_live: Dict[int, Tuple[str, float, float]] = {
        item.serial: (item.kind, item.coordinate, 0.0)
        for item in design.initial_occurrences
    }
    for step in range(1 << level):
        for _half_tag in (TAG_BROWNIAN_LEFT, TAG_BROWNIAN_RIGHT):
            next_moments = {}
            coefficient = (
                1.0
                - design.mean_reversion * half
                + 0.5 * (design.mean_reversion * half) ** 2
            )
            noise_coefficient = design.diffusion * (
                1.0 - 0.5 * design.mean_reversion * half
            )
            for serial, (kind, mean, variance) in moment_live.items():
                target = _kind_mean(design, kind)
                next_mean = target + coefficient * (mean - target)
                next_variance = (
                    coefficient * coefficient * variance
                    + noise_coefficient * noise_coefficient * half
                )
                next_moments[serial] = (kind, next_mean, next_variance)
            moment_live = next_moments
        boundary = step + 1
        if boundary in edits:
            edit = edits[boundary]
            if edit.kind in ("death", "replacement"):
                del moment_live[edit.source_serial]  # type: ignore[index]
            if edit.kind in ("birth", "replacement"):
                created = edit.created
                moment_live[created.serial] = (  # type: ignore[union-attr]
                    created.kind,  # type: ignore[union-attr]
                    created.coordinate,  # type: ignore[union-attr]
                    0.0,
                )

    final_oracle = _endpoint_oracle(design)
    w2_values = []
    mean_errors = []
    sd_errors = []
    for serial in sorted(moment_live):
        _kind, mean, variance = moment_live[serial]
        exact_mean, exact_variance = final_oracle[serial]
        mean_error = abs(mean - exact_mean)
        sd_error = abs(math.sqrt(variance) - math.sqrt(exact_variance))
        mean_errors.append(mean_error)
        sd_errors.append(sd_error)
        w2_values.append(math.sqrt(mean_error * mean_error + sd_error * sd_error))
    return LevelQualification(
        level=level,
        step_count=1 << level,
        checkpoint_states=tuple(checkpoints),
        final_lineage=tuple((serial, live[serial].kind) for serial in sorted(live)),
        retired_serials=tuple(retired),
        edit_counts=tuple(
            (key, counts[key]) for key in ("birth", "death", "replacement")
        ),
        endpoint_w2_max=max(w2_values),
        endpoint_mean_error_max=max(mean_errors),
        endpoint_standard_deviation_error_max=max(sd_errors),
    )


def _endpoint_oracle(
    design: FrozenSyntheticDesign,
) -> Mapping[int, Tuple[float, float]]:
    live: Dict[int, Tuple[SyntheticOccurrence, float]] = {
        item.serial: (item, 0.0) for item in design.initial_occurrences
    }
    coarsest_steps = float(1 << design.coarsest_level)
    for edit in design.edits:
        time = design.horizon * edit.coarsest_boundary / coarsest_steps
        if edit.kind in ("death", "replacement"):
            del live[edit.source_serial]  # type: ignore[index]
        if edit.kind in ("birth", "replacement"):
            live[edit.created.serial] = (edit.created, time)  # type: ignore[union-attr]
    result = {}
    for serial, (occurrence, start_time) in live.items():
        duration = design.horizon - start_time
        decay = math.exp(-design.mean_reversion * duration)
        target = _kind_mean(design, occurrence.kind)
        mean = target + (occurrence.coordinate - target) * decay
        variance = (
            design.diffusion
            * design.diffusion
            * (1.0 - decay * decay)
            / (2.0 * design.mean_reversion)
        )
        result[serial] = (mean, variance)
    return result


def _checkpoint_gap(coarse: LevelQualification, fine: LevelQualification) -> float:
    if len(coarse.checkpoint_states) != len(fine.checkpoint_states):
        raise ArithmeticError("common-checkpoint counts differ")
    maximum = 0.0
    for coarse_state, fine_state in zip(
        coarse.checkpoint_states, fine.checkpoint_states
    ):
        if tuple(serial for serial, _ in coarse_state) != tuple(
            serial for serial, _ in fine_state
        ):
            raise ArithmeticError("persistent lineage differs at a common checkpoint")
        for (_serial, coarse_value), (_, fine_value) in zip(coarse_state, fine_state):
            maximum = max(maximum, abs(coarse_value - fine_value))
    return maximum


@dataclass(frozen=True)
class SyntheticCoupledPathQualification:
    schema_version: str
    scope: str
    strict_nonclaims: str
    input_semantics: str
    path_norm: str
    endpoint_metric: str
    endpoint_law_premise: str
    failure_policy: str
    design_sha256: str
    input_sha256: str
    levels: Tuple[int, ...]
    explicit_input_count: int
    tag4_input_count: int
    tag5_input_count: int
    derived_coarse_increment_count: int
    coarse_sum_comparisons: int
    coarse_equal_sum_fine: bool
    persistent_lineage_across_levels: bool
    retired_lineage_ledger_across_levels: bool
    edit_family_counts_match_oracle: bool
    path_pair_gaps: Tuple[float, ...]
    endpoint_w2_by_level: Tuple[float, ...]
    path_contraction_passed: bool
    finest_path_tolerance_passed: bool
    endpoint_contraction_passed: bool
    finest_endpoint_tolerance_passed: bool
    frozen_levels_and_tolerances_used: bool
    live_cp23_stream_consumed: bool
    gaussian_source_law_certified: bool
    general_split_step_integrated: bool
    independent_recomputation_present: bool
    formal_test30_closed: bool
    passed: bool
    report_sha256: str


def qualify_synthetic_coupled_path(
    design: FrozenSyntheticDesign,
    supplied: Tuple[AddressedBrownianIncrement, ...],
) -> SyntheticCoupledPathQualification:
    """Validate and run the frozen, supplied-input synthetic qualification."""

    design = _require_exact_frozen_design_v1(design)
    finest = _validate_finest_inputs(design, supplied)
    design_sha256 = _canonical_digest(_design_payload(design))
    input_payload = [
        {
            "domain": item.address.domain,
            "domain_tag": item.address.domain_tag,
            "run_id": item.address.run_id,
            "step_index": item.address.step_index,
            "occurrence_serial": item.address.occurrence_serial,
            "proposal_index": item.address.proposal_index,
            "philox_key": list(item.address.philox_key),
            "philox_counter": list(item.address.philox_counter),
            "increment_hex": item.increment.hex(),
        }
        for item in supplied
    ]
    input_sha256 = _canonical_digest(input_payload)
    level_blocks = _derive_all_levels(design, finest)
    levels = tuple(level for level, _block in level_blocks)
    if levels != design.levels:
        raise ArithmeticError("derived level roster differs from frozen levels")
    results = tuple(
        _simulate_level(design, level, block) for level, block in level_blocks
    )
    path_gaps = tuple(
        _checkpoint_gap(coarse, fine) for coarse, fine in zip(results[:-1], results[1:])
    )
    endpoint_w2 = tuple(result.endpoint_w2_max for result in results)
    replay = _replay_lineage(design.initial_occurrences, design.edits)
    expected_lineage = tuple(
        (item.serial, item.kind) for item in replay.final_occurrences
    )
    persistent = all(result.final_lineage == expected_lineage for result in results)
    retired_ledger = all(
        result.retired_serials == replay.retired_serials for result in results
    )
    edit_match = all(result.edit_counts == replay.edit_counts for result in results)
    path_contraction = all(
        path_gaps[index + 1] < path_gaps[index] for index in range(len(path_gaps) - 1)
    )
    if not design.require_strict_path_contraction:
        path_contraction = all(
            path_gaps[index + 1] <= path_gaps[index]
            for index in range(len(path_gaps) - 1)
        )
    endpoint_contraction = all(
        endpoint_w2[index + 1] < endpoint_w2[index]
        for index in range(len(endpoint_w2) - 1)
    )
    derived_count = sum(len(block) for _level, block in level_blocks[:-1])
    comparisons = derived_count
    positive_flags = {
        "coarse_equal_sum_fine": True,
        "persistent_lineage_across_levels": persistent,
        "retired_lineage_ledger_across_levels": retired_ledger,
        "edit_family_counts_match_oracle": edit_match,
        "path_contraction_passed": path_contraction,
        "finest_path_tolerance_passed": path_gaps[-1] <= design.path_tolerance,
        "endpoint_contraction_passed": endpoint_contraction,
        "finest_endpoint_tolerance_passed": endpoint_w2[-1]
        <= design.endpoint_w2_tolerance,
        "frozen_levels_and_tolerances_used": True,
    }
    negative_flags = {
        "live_cp23_stream_consumed": False,
        "gaussian_source_law_certified": False,
        "general_split_step_integrated": False,
        "independent_recomputation_present": False,
        "formal_test30_closed": False,
    }
    passed = all(positive_flags.values())
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": QUALIFICATION_SCOPE,
        "input_semantics": INPUT_SEMANTICS,
        "path_norm": PATH_NORM,
        "endpoint_metric": ENDPOINT_METRIC,
        "endpoint_law_premise": ENDPOINT_LAW_PREMISE,
        "failure_policy": FAILURE_POLICY,
        "design_sha256": design_sha256,
        "input_sha256": input_sha256,
        "levels": list(levels),
        "explicit_input_count": len(supplied),
        "tag4_input_count": sum(
            item.address.domain_tag == TAG_BROWNIAN_LEFT for item in supplied
        ),
        "tag5_input_count": sum(
            item.address.domain_tag == TAG_BROWNIAN_RIGHT for item in supplied
        ),
        "derived_coarse_increment_count": derived_count,
        "coarse_sum_comparisons": comparisons,
        "path_pair_gaps": list(path_gaps),
        "endpoint_w2_by_level": list(endpoint_w2),
        "positive_flags": positive_flags,
        "negative_flags": negative_flags,
        "strict_nonclaims": STRICT_NONCLAIMS,
        "passed": passed,
    }
    report_sha256 = _canonical_digest(payload)
    return SyntheticCoupledPathQualification(
        schema_version=SCHEMA_VERSION,
        scope=QUALIFICATION_SCOPE,
        strict_nonclaims=STRICT_NONCLAIMS,
        input_semantics=INPUT_SEMANTICS,
        path_norm=PATH_NORM,
        endpoint_metric=ENDPOINT_METRIC,
        endpoint_law_premise=ENDPOINT_LAW_PREMISE,
        failure_policy=FAILURE_POLICY,
        design_sha256=design_sha256,
        input_sha256=input_sha256,
        levels=levels,
        explicit_input_count=len(supplied),
        tag4_input_count=sum(
            item.address.domain_tag == TAG_BROWNIAN_LEFT for item in supplied
        ),
        tag5_input_count=sum(
            item.address.domain_tag == TAG_BROWNIAN_RIGHT for item in supplied
        ),
        derived_coarse_increment_count=derived_count,
        coarse_sum_comparisons=comparisons,
        coarse_equal_sum_fine=True,
        persistent_lineage_across_levels=persistent,
        retired_lineage_ledger_across_levels=retired_ledger,
        edit_family_counts_match_oracle=edit_match,
        path_pair_gaps=path_gaps,
        endpoint_w2_by_level=endpoint_w2,
        path_contraction_passed=path_contraction,
        finest_path_tolerance_passed=positive_flags["finest_path_tolerance_passed"],
        endpoint_contraction_passed=endpoint_contraction,
        finest_endpoint_tolerance_passed=positive_flags[
            "finest_endpoint_tolerance_passed"
        ],
        frozen_levels_and_tolerances_used=True,
        live_cp23_stream_consumed=negative_flags["live_cp23_stream_consumed"],
        gaussian_source_law_certified=negative_flags["gaussian_source_law_certified"],
        general_split_step_integrated=negative_flags["general_split_step_integrated"],
        independent_recomputation_present=negative_flags[
            "independent_recomputation_present"
        ],
        formal_test30_closed=negative_flags["formal_test30_closed"],
        passed=passed,
        report_sha256=report_sha256,
    )


def run_frozen_synthetic_qualification() -> SyntheticCoupledPathQualification:
    """Run the exact local fixture without RNG, data access, or side effects."""

    design = frozen_synthetic_design()
    return qualify_synthetic_coupled_path(design, build_frozen_explicit_inputs(design))


__all__ = [
    "SCHEMA_VERSION",
    "QUALIFICATION_SCOPE",
    "STRICT_NONCLAIMS",
    "INPUT_SEMANTICS",
    "PATH_NORM",
    "ENDPOINT_METRIC",
    "ENDPOINT_LAW_PREMISE",
    "FAILURE_POLICY",
    "DOMAIN_BROWNIAN_LEFT",
    "DOMAIN_BROWNIAN_RIGHT",
    "TAG_BROWNIAN_LEFT",
    "TAG_BROWNIAN_RIGHT",
    "SyntheticCoupledPathError",
    "CP23BrownianAddress",
    "AddressedBrownianIncrement",
    "SyntheticOccurrence",
    "FrozenLineageEdit",
    "FrozenSyntheticDesign",
    "LevelQualification",
    "SyntheticCoupledPathQualification",
    "frozen_synthetic_design",
    "build_frozen_explicit_inputs",
    "qualify_synthetic_coupled_path",
    "run_frozen_synthetic_qualification",
]
