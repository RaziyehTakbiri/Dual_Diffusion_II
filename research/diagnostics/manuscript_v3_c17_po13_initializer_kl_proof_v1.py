"""Read-only validator for the C17 PO13 initializer-KL proof package.

The validator qualifies a static local mathematical artifact.  It imports no
project science, draws no entropy, accesses no dataset, contacts no service,
and writes no project file.  Its finite two-state arithmetic is a
deterministic witness for signs and orientation; the proof is the bound human
artifact, not a floating-point calculation.
"""

from __future__ import annotations

import ast
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-c17-po13-initializer-kl-proof-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "C17_GATE_A_ROUTE_NARROWED_NO_GO_PO13_PROVED_C17_UNPROVED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "ADDITIVE_STATIC_MATHEMATICAL_PROOF_NO_SCIENTIFIC_EFFECT"
CONTROL_PREDICATE = (
    "C17_PO13_INITIALIZER_KL_DERIVATION_AND_ORIENTATION_PROVED"
)
GATE_CONTROL_PREDICATE = "GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO"
REPORTED_DATE = "2026-08-30"

HUMAN_PATH = "PROJECT_C17_PO13_INITIALIZER_KL_PROOF.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_c17_po13_initializer_kl_proof_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_c17_po13_initializer_kl_proof_v1.py"
)

PREDECESSOR_HUMAN_PATH = (
    "PROJECT_C17_FORK_B_ASSUMPTIONS_PROOF_CODE_CROSSWALK_DRAFT.md"
)
PREDECESSOR_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.json"
)
PREDECESSOR_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.py"
)
PREDECESSOR_TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.py"
)
THEOREM_TARGET_PATH = "manuscript_v3/c17_hybrid_path_error_theorem.md"
DIRECT_CONTRACT_PATH = "manuscript_v3/c17_fork_b_direct_certificate_contract.md"
CAP_CONTRACT_PATH = "manuscript_v3/c17_cap_defect_cancellation_contract.md"
FINITE_BRIDGE_SOURCE_PATH = "src/heterodiff/theory/finite_bridge_path_control.py"
PATH_KL_SOURCE_PATH = "src/heterodiff/theory/path_kl.py"

NORMALIZED_AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
AUTHORITY_TEXT_SHA256 = (
    "44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a"
)
ROUTE = "FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES"
ORIENTATION = "KL(P0_H || P0_HHAT)_TARGET_FIRST"


class ValidationError(ValueError):
    """Raised when exact types, semantics, canonical form, or custody fail."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _foreign_record_sha256(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("foreign schema is not exact ASCII text")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(
        (schema + "\0").encode("ascii") + _canonical_payload_bytes(payload)
    )


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(ordinal) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("relative path is not exact text")
    raw_parts = relative_path.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise ValidationError("unsafe relative path: " + relative_path)
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts:
        raise ValidationError("unsafe relative path: " + relative_path)
    path = root.joinpath(*pure.parts)
    if path == root or root not in path.parents:
        raise ValidationError("path escaped workspace")
    return path


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows: List[Tuple[Any, ...]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("ancestor custody invalid")
        rows.append(
            (
                str(current),
                status.st_dev,
                status.st_ino,
                stat.S_IFMT(status.st_mode),
                stat.S_IMODE(status.st_mode),
                status.st_uid,
                status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("ancestor escaped workspace")
        current = current.parent
    return tuple(reversed(rows))


def _leaf_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd)
        == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    expected_symbols: Optional[Sequence[str]] = None,
    foreign_self_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }
    if expected_symbols is not None:
        row["expected_symbols"] = list(expected_symbols)
    if foreign_self_digest is not None:
        row["record_sha256"] = foreign_self_digest
    return row


INPUT_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "PREDECESSOR_HUMAN", "path": PREDECESSOR_HUMAN_PATH, "bytes": 16520, "raw_sha256": "0bdf49f4a830f90cd074ba8728c2c36db72b961c2e767776ce511400395bbd66", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 1, "role": "PREDECESSOR_MACHINE", "path": PREDECESSOR_MACHINE_PATH, "bytes": 29073, "raw_sha256": "32ea89c4e15a80e0ae805b288ee6b95d2f5d474f8ba5dabf29eb53c04e8f286b", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "18b695a4e10f6c7668176cf85ec6f6c32e30de5ec359128d9faf56a06d5394ef"},
    {"ordinal": 2, "role": "PREDECESSOR_VALIDATOR", "path": PREDECESSOR_VALIDATOR_PATH, "bytes": 45842, "raw_sha256": "5b173183f7659014c7c2153f6f6e4305298ca56e1c301672f26ef34c5bf29852", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 3, "role": "PREDECESSOR_HOSTILE_TEST", "path": PREDECESSOR_TEST_PATH, "bytes": 26473, "raw_sha256": "74655baac781bd76c786ec020a1fc29b636998cf0986e78940ab25a740cd46dd", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 4, "role": "C17_THEOREM_TARGET", "path": THEOREM_TARGET_PATH, "bytes": 34923, "raw_sha256": "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 5, "role": "FORK_B_DIRECT_CERTIFICATE_CONTRACT", "path": DIRECT_CONTRACT_PATH, "bytes": 7109, "raw_sha256": "80c00dd62106e9fd4743fd6999c1e642f0ef31b063cf9ae3c84822b7a68deae4", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 6, "role": "CAP_DEFECT_CANCELLATION_CONTRACT", "path": CAP_CONTRACT_PATH, "bytes": 5931, "raw_sha256": "a0a57cdba08c588269c8706ab78bb68ac2360f29b97d20cd05cdcd3a8c93cb3f", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 7, "role": "FINITE_INITIAL_TILT_SOURCE", "path": FINITE_BRIDGE_SOURCE_PATH, "bytes": 45529, "raw_sha256": "1cdb2cf82016ad0979fff3ef7451fe6116904cca772b017e6e605b78b476c502", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["conditional_initial_law"]},
    {"ordinal": 8, "role": "FINITE_DIRECTED_INITIAL_KL_SOURCE", "path": PATH_KL_SOURCE_PATH, "bytes": 15389, "raw_sha256": "769992c89f151d90c04c66c50cad538bfa859396d8f6737aa6b5e05e39bb173a", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["_initial_kl", "ctmc_path_kl"]},
)


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "source": "CONVERSATION_VISIBLE_TEXT",
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 207,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_UNBOUND",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "continued_bounded_local_project_work_authorized": True,
    "tracker_edit_authorized_by_package": False,
    "external_contact_or_browsing_authorized": False,
    "data_access_or_download_authorized": False,
    "entropy_or_live_randomness_authorized": False,
    "runtime_approval_authorized": False,
    "scientific_execution_authorized": False,
    "training_authorized": False,
    "claim_promotion_or_submission_authorized": False,
    "user_selected_file_paths_or_schema": False,
    "agent_selected_bounded_implementation_details": True,
}


EXPECTED_THEOREM_SCOPE: Mapping[str, Any] = {
    "selected_route": ROUTE,
    "orientation": ORIENTATION,
    "measurable_space_general": True,
    "finite_state_required": False,
    "strictly_positive_measurable_h_and_hhat_required": True,
    "positive_finite_normalizers_required": True,
    "real_domain_instantiation_required_for_algebraic_derivation": False,
    "exact_error_definition": "E=LOG(HHAT/H)",
    "target_initial_law": "DP0=(H/Z_H)D_RHO",
    "plugin_initial_law": "DQ0=(HHAT/Z_HHAT)D_RHO",
    "density_ratio_identity": "DP0/DQ0=(Z_HHAT/Z_H)EXP(-E)",
    "log_mgf_identity": "E_P0[EXP(E)]=Z_HHAT/Z_H",
    "initializer_kl_identity": (
        "KL(P0||Q0)=LOG(Z_HHAT/Z_H)-E_P0[E]="
        "LOG(E_P0[EXP(E)])-E_P0[E]"
    ),
    "extended_value_semantics": (
        "E_POSITIVE_PART_INTEGRABLE_KL_FINITE_IFF_E_NEGATIVE_PART_INTEGRABLE"
    ),
    "zero_condition": "E_CONSTANT_P0_ALMOST_SURELY_EQUIVALENT_P0_EQUALS_Q0",
    "gauge_invariant": True,
    "reverse_orientation_formula": (
        "KL(Q0||P0)=LOG(E_Q0[EXP(-E)])+E_Q0[E]"
    ),
}


EXPECTED_PROPOSITIONS: List[Mapping[str, Any]] = [
    {
        "ordinal": 0,
        "proposition_id": "PO13.1A",
        "title": "INITIAL_DENSITY_RATIO",
        "status": "PROVED",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 1,
        "proposition_id": "PO13.1B",
        "title": "TARGET_FIRST_LOG_MGF_KL_IDENTITY_WITH_EXTENDED_VALUES",
        "status": "PROVED",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 2,
        "proposition_id": "PO13.1C",
        "title": "NONNEGATIVITY_ZERO_CASE_AND_GAUGE_INVARIANCE",
        "status": "PROVED",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 3,
        "proposition_id": "PO13.2",
        "title": "ACTUAL_ERROR_OSCILLATION_IMPLIES_HOEFFDING_U0_BOUND",
        "status": "PROVED_CONDITIONAL_NO_ACTUAL_RANGE_SUPPLIED",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 4,
        "proposition_id": "PO13.3",
        "title": "FORWARD_REVERSE_ORIENTATION_NONINTERCHANGEABILITY",
        "status": "PROVED_WITH_EXACT_TWO_STATE_WITNESS",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 5,
        "proposition_id": "PO13.4",
        "title": "DYNAMIC_ONLY_PATH_CONTROL_OBSTRUCTION",
        "status": "PROVED_WITH_ZERO_GENERATOR_CONSTANT_PATH_WITNESS",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 6,
        "proposition_id": "PO13.5",
        "title": "SMOOTH_TERMINAL_MATCHED_UNBOUNDED_INITIALIZER_OBSTRUCTION",
        "status": "PROVED_ANALYTIC_FAMILY_NO_FLOATING_EXECUTION",
        "uses_floating_arithmetic": False,
    },
    {
        "ordinal": 7,
        "proposition_id": "L16.1",
        "title": "SHARED_GUIDE_POINTWISE_CANCELLATION",
        "status": "PROVED_AUXILIARY_LEMMA_PO16_REMAINS_OPEN",
        "uses_floating_arithmetic": False,
    },
]


def _assumption_effects() -> List[Dict[str, Any]]:
    return [
        {
            "ordinal": index - 1,
            "assumption_id": "A" + str(index),
            "status": "OPEN",
            "general_assumption_verified": False,
            "physionet_verified": False,
            "retail_verified": False,
            "closed_by_this_package": False,
        }
        for index in range(1, 13)
    ]


def _proof_obligation_effects() -> List[Dict[str, Any]]:
    titles = (
        "QUOTIENT_STATE_MEASURABILITY_AND_BOUNDARY_TERMS",
        "BASE_MARTINGALE_PROBLEM_WELLPOSEDNESS_AND_NONEXPLOSION",
        "POSITIVE_FINITE_INFORMATION_COMMON_SUPPORT_AND_NORMALIZERS",
        "TERMINAL_AND_CLEAN_HOLD_COMPATIBILITY",
        "WITHIN_STRATUM_REGULARITY_AND_TARGET_INTEGRABILITY",
        "SHARED_DIFFUSION_RANGE_CONDITION_AND_GIRSANOV",
        "JUMP_SUPPORT_RADON_NIKODYM_FACTORS_AND_STRUCTURAL_ZEROS",
        "FINITE_TARGET_COMPENSATORS",
        "TRUE_UI_LIKELIHOOD_MARTINGALE_OR_JUSTIFIED_LOCALIZATION",
        "CONTROLLED_PATH_LAW_UNIQUENESS",
        "IDEAL_LAW_VERSUS_NUMERICAL_AND_OPERATIONAL_ERROR_SEPARATION",
        "CANDIDATE_BASE_CONDITIONING_SCOPE",
        "INITIALIZER_KL_DERIVATION_AND_ORIENTATION",
        "FIVE_TERM_PATH_LIKELIHOOD_DECOMPOSITION",
        "SIMULTANEOUS_TARGET_OCCUPATION_DIRECT_CERTIFICATES",
        "CAP_REFERENCE_AND_RESIDUAL_NO_DOUBLE_COUNTING",
        "FINITE_AND_MIXED_KNOWN_LAW_INSTANTIATION_AND_FALSIFICATION",
        "PROOF_CODE_AUDIT_AND_NONVACUITY_THRESHOLD",
    )
    rows: List[Dict[str, Any]] = []
    for index, title in enumerate(titles, 1):
        discharged = index == 13
        status = (
            "DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS"
            if discharged
            else "OPEN"
        )
        if index == 16:
            status = "OPEN_AUXILIARY_SHARED_GUIDE_CANCELLATION_LEMMA_ONLY"
        rows.append(
            {
                "ordinal": index - 1,
                "proof_obligation_id": "PO" + str(index).zfill(2),
                "title": title,
                "status": status,
                "mathematical_derivation_discharged": discharged,
                "conditional_on_declared_assumptions": discharged,
                "real_domain_discharged": False,
                "sufficient_for_c17": False,
                "closed_by_this_package": discharged,
            }
        )
    return rows


EXPECTED_FINITE_WITNESS: Mapping[str, Any] = {
    "witness_kind": "EXACT_RATIONAL_TWO_STATE_STATIC_PATH_ORIENTATION_WITNESS",
    "base_weights": ["1/2", "1/2"],
    "exact_tilt_h": ["2", "1"],
    "plugin_tilt_hhat": ["1", "3"],
    "normalizer_z_h": "3/2",
    "normalizer_z_hhat": "2",
    "normalizer_ratio_z_hhat_over_z_h": "4/3",
    "target_initial_p0": ["2/3", "1/3"],
    "plugin_initial_q0": ["1/4", "3/4"],
    "exp_error_hhat_over_h": ["1/2", "3"],
    "target_over_plugin_density_ratio": ["8/3", "4/9"],
    "forward_kl_symbolic_terms": ["(2/3)LOG(8/3)", "(1/3)LOG(4/9)"],
    "reverse_kl_symbolic_terms": ["(1/4)LOG(3/8)", "(3/4)LOG(9/4)"],
    "forward_and_reverse_positive": True,
    "forward_and_reverse_unequal": True,
    "zero_generator": [["0", "0"], ["0", "0"]],
    "all_dynamic_components_exactly_zero": True,
    "constant_path_pushforward_is_injective_on_support": True,
    "path_kl_equals_initializer_kl": True,
    "initializer_kl_strictly_positive": True,
    "floating_values_are_not_proof_or_scientific_results": True,
}


EXPECTED_RANGE_ROUTE: Mapping[str, Any] = {
    "theorem": "IF_M_LE_E_LE_M_CAP_P0_AS_THEN_K0_LE_(M_CAP-M)^2/8",
    "range_is_gauge_invariant": True,
    "must_bind_actual_error_rtheta_minus_rstar": True,
    "rtheta_architecture_range_alone_sufficient": False,
    "unknown_rstar_norm_accepted": False,
    "target_initial_measure_required": True,
    "actual_error_range_certificate_present": False,
    "nonvacuity_threshold_present": False,
    "U0": None,
    "K0_numeric_value": None,
    "PO15_discharged": False,
}


EXPECTED_SMOOTH_OBSTRUCTION: Mapping[str, Any] = {
    "theorem_id": "PO13.5",
    "state_space": "UNIT_INTERVAL_WITH_BOREL_SIGMA_FIELD",
    "base_initial_law": "UNIFORM_ON_[0,1]",
    "base_generator": "ZERO_GENERATOR",
    "base_drift": "ZERO",
    "base_covariance": "ZERO",
    "base_jump_families": "EMPTY",
    "family_parameter": "INTEGER_N_AT_LEAST_2",
    "terminal_likelihood": "G_N(X)=EXP(N*X)",
    "exact_information": "H_N,TIME(X)=EXP(N*X)",
    "common_guide": "HTILDE_N,TIME(X)=EXP(N*X)",
    "exact_residual": "RSTAR_N,TIME(X)=0",
    "schedule": (
        "SMOOTH_ALPHA_WITH_ALPHA(0)=0_AND_ALPHA=1_ON_DECLARED_CLEAN_HOLD"
    ),
    "plugin_information": "HHAT_N,TIME(X)=EXP(ALPHA(TIME)*N*X)",
    "plugin_residual": "RTHETA_N,TIME(X)=(ALPHA(TIME)-1)*N*X",
    "terminal_and_clean_hold_residuals_zero": True,
    "exact_initial_density": "P_N(X)=N*EXP(N*X)/(EXP(N)-1)",
    "plugin_initial_density": "Q_N(X)=1",
    "K0_exact": (
        "N*EXP(N)/(EXP(N)-1)-1-LOG((EXP(N)-1)/N)"
    ),
    "K0_strict_lower_bound": "K0_N>LOG(N)-1",
    "K0_unbounded_as_n_tends_to_infinity": True,
    "KC": "0",
    "K_PLUS": "0",
    "K_MINUS": "0",
    "K_REPLACEMENT": "0",
    "controlled_path_laws": "UNIQUE_CONSTANT_PATH_LAWS_FROM_NORMALIZED_INITIALS",
    "terminal_matching_plus_zero_dynamic_error_controls_full_path_KL": False,
    "separate_initializer_certificate_necessary": True,
    "dataset_checkpoint_solver_or_floating_execution_used": False,
}


def _survival_conditions() -> List[Dict[str, Any]]:
    rows = (
        (
            "S1_PATH_IDENTITY",
            "PO14_PROVED_WITH_A1_THROUGH_A12_INCLUDING_IDEAL_OPERATIONAL_SEPARATION_AND_CANDIDATE_BASE_SCOPE_AND_TARGET_FIRST_ORIENTATION",
        ),
        (
            "S2_INITIALIZER",
            "EXACT_TARGET_INITIAL_OR_EXACT_DOMINATION_ACTUAL_ERROR_AND_FINITE_NONVACUOUS_U0",
        ),
        (
            "S3_CONTINUOUS",
            "EXACT_TARGET_OCCUPATION_OR_EXACT_DOMINATION_ACTUAL_GRADIENT_AND_FINITE_UC",
        ),
        (
            "S4_BIRTH",
            "EXHAUSTIVE_AGGREGATE_BIRTH_SUPPORT_FACTORS_ACTUAL_EDGE_ERROR_AND_FINITE_U_PLUS",
        ),
        (
            "S5_DEATH",
            "EXHAUSTIVE_AGGREGATE_DEATH_SUPPORT_MULTIPLICITY_ACTUAL_EDGE_ERROR_AND_FINITE_U_MINUS",
        ),
        (
            "S6_REPLACEMENT",
            "EXHAUSTIVE_REPLACEMENT_FIBERS_RN_FACTORS_ACTUAL_EDGE_ERROR_AND_FINITE_U_REPLACEMENT",
        ),
        (
            "S7_SIMULTANEITY",
            "ONE_PRESPECIFIED_EVENT_COVERS_ALL_FIVE_BOUNDS_NUMERICAL_AND_PROPOSAL_ERROR",
        ),
        (
            "S8_NONVACUITY",
            "PREOUTCOME_THRESHOLD_AND_FAILURE_RULE_WITH_CERTIFIED_SUM_STRICTLY_BELOW_THRESHOLD",
        ),
        (
            "S9_FALSIFICATION_AND_AUDIT",
            "ALL_FIVE_FINITE_AND_MIXED_KNOWN_LAW_COMPONENTS_HOSTILES_AND_FRESH_PROOF_CODE_AUDIT",
        ),
    )
    return [
        {
            "ordinal": ordinal,
            "condition_id": condition_id,
            "requirement": requirement,
            "currently_satisfied": False,
            "required_to_reopen_real_domain_promotion": True,
        }
        for ordinal, (condition_id, requirement) in enumerate(rows)
    ]


EXPECTED_GATE_DECISION: Mapping[str, Any] = {
    "gate_item": "C17_ROUTE_DEMONSTRABLY_VIABLE_OR_ROUTE_NARROWED_BEFORE_OUTCOMES",
    "decision": "ROUTE_NARROWED_PREOUTCOME_NO_GO",
    "real_domain_C17_promotion_under_current_Fork_B_observability": "NO_GO",
    "C17_theorem_status": "UNPROVED",
    "surviving_scope": "CONDITIONAL_THEORY_AND_FINITE_MIXED_KNOWN_LAW_FALSIFICATION_ONLY",
    "real_domain_contribution_or_model_quality_guarantee_survives": False,
    "decision_is_universal_impossibility_claim": False,
    "decision_is_fail_closed_for_current_project_evidence": True,
    "all_reopening_conditions_conjunctive": True,
    "partial_satisfaction_reopens_route": False,
    "new_preoutcome_independently_audited_supersession_required": True,
    "eligible_control_predicate_after_independent_audit": GATE_CONTROL_PREDICATE,
    "eligible_timetable_wording": "ROUTE_NARROWED_PREOUTCOME_NO_GO",
    "forbidden_timetable_wording": ["C17_VIABLE", "C17_PROVED", "FORK_B_CERTIFIED"],
    "survival_conditions": _survival_conditions(),
}


EXPECTED_CROSSWALK: List[Mapping[str, Any]] = [
    {
        "ordinal": 0,
        "mathematical_object": "NORMALIZED_INITIAL_TILT",
        "path": FINITE_BRIDGE_SOURCE_PATH,
        "symbol": "conditional_initial_law",
        "strength": "FINITE_BINARY64_IMPLEMENTATION_WITNESS_NOT_GENERAL_PROOF",
        "sufficient_for_real_domain_U0": False,
    },
    {
        "ordinal": 1,
        "mathematical_object": "DIRECTED_INITIAL_RELATIVE_ENTROPY",
        "path": PATH_KL_SOURCE_PATH,
        "symbol": "_initial_kl",
        "strength": "PRIVATE_FINITE_BINARY64_HELPER_NOT_FORMAL_ARITHMETIC",
        "sufficient_for_real_domain_U0": False,
    },
    {
        "ordinal": 2,
        "mathematical_object": "FINITE_STATIC_PATH_KL",
        "path": PATH_KL_SOURCE_PATH,
        "symbol": "ctmc_path_kl",
        "strength": "FINITE_TIME_HOMOGENEOUS_DIAGNOSTIC_NOT_GENERAL_C17",
        "sufficient_for_real_domain_U0": False,
    },
    {
        "ordinal": 3,
        "mathematical_object": "GENERAL_INITIALIZER_KL_DERIVATION",
        "path": HUMAN_PATH,
        "symbol": "Theorem PO13.1",
        "strength": "GENERAL_MEASURE_THEOREM_CONDITIONAL_ON_DECLARED_OBJECTS",
        "sufficient_for_real_domain_U0": False,
    },
]


EXPECTED_EFFECTS: Mapping[str, Any] = {
    "control_predicate": CONTROL_PREDICATE,
    "control_predicate_value_after_validation_and_independent_audit": True,
    "gate_control_predicate": GATE_CONTROL_PREDICATE,
    "gate_control_predicate_value_after_validation_and_independent_audit": True,
    "C17_status": "UNPROVED",
    "Gate_A_C17_viability_or_narrowing_item": (
        "ELIGIBLE_TO_CHECK_AS_ROUTE_NARROWED_PREOUTCOME_NO_GO_AFTER_INDEPENDENT_AUDIT"
    ),
    "B01": "OPEN",
    "F001": None,
    "F002": None,
    "F003": None,
    "F004": None,
    "F005": None,
    "F006": None,
    "A1_through_A12_open_count": 12,
    "proof_obligation_count": 18,
    "proof_obligations_discharged_by_this_package": 1,
    "PO13_status": "DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS",
    "PO16_status": "OPEN_AUXILIARY_SHARED_GUIDE_CANCELLATION_LEMMA_ONLY",
    "finite_nonvacuous_U0_present": False,
    "simultaneous_five_component_event_present": False,
    "unresolved_field_count": 172,
    "effective_open_blocker_count": 12,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "scientific_results_produced": 0,
    "tracker_edited": False,
    "claim_promoted": False,
    "confirmatory_execution_authorized": False,
}


EXPECTED_NONCLAIMS: Mapping[str, Any] = {
    "proof_is_not_full_C17": True,
    "PO13_is_not_preregistration_field_F003": True,
    "A3_real_domain_objects_verified": False,
    "real_domain_K0_evaluated": False,
    "real_domain_U0_certified": False,
    "path_likelihood_decomposition_proved": False,
    "target_occupation_available": False,
    "five_simultaneous_certificates_present": False,
    "PO16_discharged": False,
    "general_cap_reference_stability_route_proved": False,
    "project_science_imported_or_executed_by_validator": False,
    "network_or_external_contact_performed": False,
    "dataset_or_outcome_accessed": False,
    "entropy_or_live_randomness_used": False,
    "runtime_or_scientific_execution_performed": False,
    "existing_project_file_modified": False,
    "gate_item_closure_would_mean_C17_viable": False,
    "gate_item_closure_would_mean_route_narrowed_only": True,
}


EXPECTED_TOP_LEVEL_KEYS: Set[str] = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "theorem_scope",
    "proposition_register",
    "assumption_effects",
    "proof_obligation_effects",
    "finite_exact_witness",
    "smooth_terminal_matched_obstruction",
    "conditional_U0_range_route",
    "gate_A_route_narrowing_decision",
    "proof_code_crosswalk",
    "field_blocker_gate_effects",
    "scope_and_nonclaims",
    "input_bindings",
    "package_bindings",
    "record_sha256",
}


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, role, path in (
        (0, "HUMAN_PO13_PROOF", HUMAN_PATH),
        (1, "READ_ONLY_VALIDATOR", VALIDATOR_PATH),
        (2, "HOSTILE_UNIT_TEST", TEST_PATH),
    ):
        rows.append(_binding(ordinal, role, path, _stable_read(root, path)))
    return rows


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    """Construct the exact acyclic machine record."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "reported_date": REPORTED_DATE,
        "authority_provenance": dict(EXPECTED_AUTHORITY),
        "theorem_scope": dict(EXPECTED_THEOREM_SCOPE),
        "proposition_register": [dict(row) for row in EXPECTED_PROPOSITIONS],
        "assumption_effects": _assumption_effects(),
        "proof_obligation_effects": _proof_obligation_effects(),
        "finite_exact_witness": dict(EXPECTED_FINITE_WITNESS),
        "smooth_terminal_matched_obstruction": dict(EXPECTED_SMOOTH_OBSTRUCTION),
        "conditional_U0_range_route": dict(EXPECTED_RANGE_ROUTE),
        "gate_A_route_narrowing_decision": {
            **dict(EXPECTED_GATE_DECISION),
            "survival_conditions": _survival_conditions(),
        },
        "proof_code_crosswalk": [dict(row) for row in EXPECTED_CROSSWALK],
        "field_blocker_gate_effects": dict(EXPECTED_EFFECTS),
        "scope_and_nonclaims": dict(EXPECTED_NONCLAIMS),
        "input_bindings": [dict(row) for row in INPUT_BINDINGS],
        "package_bindings": _package_bindings(workspace),
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _fraction(value: str) -> Fraction:
    if type(value) is not str or not value or value.strip() != value:
        raise ValidationError("fraction must be canonical nonempty text")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValidationError("invalid exact fraction") from error
    canonical = (
        str(result.numerator)
        if result.denominator == 1
        else str(result.numerator) + "/" + str(result.denominator)
    )
    if canonical != value:
        raise ValidationError("fraction text is not canonical")
    return result


def _normalize(base: Sequence[Fraction], tilt: Sequence[Fraction]) -> Tuple[Fraction, List[Fraction]]:
    if len(base) != len(tilt) or not base:
        raise ValidationError("finite witness roster mismatch")
    if any(value <= 0 for value in base) or sum(base) != 1:
        raise ValidationError("base weights are not a positive probability law")
    if any(value <= 0 for value in tilt):
        raise ValidationError("tilt is not strictly positive")
    normalizer = sum(weight * value for weight, value in zip(base, tilt))
    if normalizer <= 0:
        raise ValidationError("finite witness normalizer is invalid")
    law = [weight * value / normalizer for weight, value in zip(base, tilt)]
    if sum(law) != 1 or any(value <= 0 for value in law):
        raise ValidationError("normalized witness law is invalid")
    return normalizer, law


def _decimal_log_fraction(value: Fraction) -> Decimal:
    if value <= 0:
        raise ValidationError("log fraction must be positive")
    return Decimal(value.numerator).ln() - Decimal(value.denominator).ln()


def evaluate_exact_witness(
    witness: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Reconstruct exact rational identities and deterministic decimal signs."""

    row = EXPECTED_FINITE_WITNESS if witness is None else witness
    base = [_fraction(value) for value in row["base_weights"]]
    exact = [_fraction(value) for value in row["exact_tilt_h"]]
    plugin = [_fraction(value) for value in row["plugin_tilt_hhat"]]
    z_h, p0 = _normalize(base, exact)
    z_hhat, q0 = _normalize(base, plugin)
    exp_error = [candidate / target for target, candidate in zip(exact, plugin)]
    target_over_plugin = [target / candidate for target, candidate in zip(p0, q0)]
    ratio = z_hhat / z_h
    if any(
        density_ratio != ratio / error_ratio
        for density_ratio, error_ratio in zip(target_over_plugin, exp_error)
    ):
        raise ValidationError("density ratio identity failed")
    if sum(weight * error for weight, error in zip(p0, exp_error)) != ratio:
        raise ValidationError("log-mgf normalizer identity failed")

    expected_exact = {
        "normalizer_z_h": _fraction(row["normalizer_z_h"]),
        "normalizer_z_hhat": _fraction(row["normalizer_z_hhat"]),
        "normalizer_ratio_z_hhat_over_z_h": _fraction(
            row["normalizer_ratio_z_hhat_over_z_h"]
        ),
        "target_initial_p0": [_fraction(value) for value in row["target_initial_p0"]],
        "plugin_initial_q0": [_fraction(value) for value in row["plugin_initial_q0"]],
        "exp_error_hhat_over_h": [_fraction(value) for value in row["exp_error_hhat_over_h"]],
        "target_over_plugin_density_ratio": [_fraction(value) for value in row["target_over_plugin_density_ratio"]],
    }
    actual_exact = {
        "normalizer_z_h": z_h,
        "normalizer_z_hhat": z_hhat,
        "normalizer_ratio_z_hhat_over_z_h": ratio,
        "target_initial_p0": p0,
        "plugin_initial_q0": q0,
        "exp_error_hhat_over_h": exp_error,
        "target_over_plugin_density_ratio": target_over_plugin,
    }
    if actual_exact != expected_exact:
        raise ValidationError("stored exact witness values do not reconstruct")

    with localcontext() as context:
        context.prec = 80
        forward = sum(
            Decimal(weight.numerator) / Decimal(weight.denominator)
            * _decimal_log_fraction(density_ratio)
            for weight, density_ratio in zip(p0, target_over_plugin)
        )
        reverse = sum(
            Decimal(weight.numerator) / Decimal(weight.denominator)
            * _decimal_log_fraction(Fraction(1, 1) / density_ratio)
            for weight, density_ratio in zip(q0, target_over_plugin)
        )
        error_logs = [_decimal_log_fraction(value) for value in exp_error]
        error_expectation = sum(
            Decimal(weight.numerator) / Decimal(weight.denominator) * value
            for weight, value in zip(p0, error_logs)
        )
        log_mgf_formula = _decimal_log_fraction(ratio) - error_expectation
        range_length = max(error_logs) - min(error_logs)
        range_upper = range_length * range_length / Decimal(8)
        if not (forward > 0 and reverse > 0 and forward != reverse):
            raise ValidationError("orientation witness did not separate KL directions")
        if abs(forward - log_mgf_formula) > Decimal("1e-70"):
            raise ValidationError("decimal log-mgf witness check failed")
        if not forward < range_upper:
            raise ValidationError("stored witness did not satisfy range theorem")
        return {
            "exact_rational_identities": "PASS",
            "forward_positive": True,
            "reverse_positive": True,
            "orientations_unequal": True,
            "log_mgf_formula_agrees": True,
            "range_bound_strict_for_witness": True,
            "decimal_precision": context.prec,
            "floating_values_reported": False,
        }


def _ast_symbol_names(raw: bytes, path: str) -> Set[str]:
    try:
        text = raw.decode("utf-8")
        tree = ast.parse(text, filename=path)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("source AST parse failed: " + path) from error
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _validate_inputs(root: Path) -> None:
    raws: Dict[str, bytes] = {}
    for expected in INPUT_BINDINGS:
        raw = _stable_read(root, expected["path"])
        raws[expected["path"]] = raw
        observed = _binding(
            expected["ordinal"],
            expected["role"],
            expected["path"],
            raw,
            expected_symbols=expected.get("expected_symbols"),
            foreign_self_digest=expected.get("record_sha256"),
        )
        _strict_equal(observed, dict(expected), "input binding")
        if "expected_symbols" in expected:
            names = _ast_symbol_names(raw, expected["path"])
            missing = set(expected["expected_symbols"]) - names
            if missing:
                raise ValidationError("expected source symbol absent")

    predecessor_raw = raws[PREDECESSOR_MACHINE_PATH]
    try:
        predecessor = json.loads(predecessor_raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("predecessor machine is invalid JSON") from error
    if canonical_machine_bytes(predecessor) != predecessor_raw:
        raise ValidationError("predecessor machine is not canonical")
    if predecessor.get("record_sha256") != _foreign_record_sha256(predecessor):
        raise ValidationError("predecessor self digest mismatch")
    if predecessor.get("route_selection", {}).get("route") != ROUTE:
        raise ValidationError("predecessor route mismatch")
    obligations = predecessor.get("proof_obligation_register")
    if type(obligations) is not list or len(obligations) != 18:
        raise ValidationError("predecessor proof obligation roster mismatch")
    po13 = obligations[12]
    if po13 != {
        "closed_by_this_package": False,
        "code_evidence_sufficient": False,
        "discharged": False,
        "ordinal": 12,
        "proof_obligation_id": "PO13",
        "real_domain_discharged": False,
        "required_for_c17": True,
        "status": "OPEN",
        "title": "INITIALIZER_KL_DERIVATION_AND_ORIENTATION",
    }:
        raise ValidationError("predecessor PO13 state mismatch")
    if any(row.get("discharged") is not False for row in obligations):
        raise ValidationError("predecessor unexpectedly discharged an obligation")
    certificates = predecessor.get("direct_certificate_register")
    if type(certificates) is not list or [
        row.get("component_id") for row in certificates
    ] != ["K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"]:
        raise ValidationError("predecessor direct-certificate roster mismatch")
    for row in certificates:
        for key in (
            "bound_value",
            "certificate_path",
            "occupation_receipt",
            "dominating_measure_receipt",
            "radon_nikodym_factor_receipt",
            "simultaneous_event_receipt",
            "nonvacuity_threshold",
        ):
            if row.get(key) is not None:
                raise ValidationError("predecessor certificate is unexpectedly populated")
        for key in ("finite", "nonvacuous", "certificate_present"):
            if row.get(key) is not False:
                raise ValidationError("predecessor certificate state mismatch")
    route_state = predecessor.get("route_selection", {})
    for key in (
        "finite_nonvacuous_bounds_present",
        "target_occupation_available",
        "dominating_measure_and_exact_radon_nikodym_factors_available",
    ):
        if route_state.get(key) is not False:
            raise ValidationError("predecessor observability state mismatch")
    gaps = predecessor.get("unresolved_gap_register")
    required_gaps = {
        "EXACT_UNKNOWN_RESIDUAL_R_STAR_UNAVAILABLE",
        "ERROR_TO_R_STAR_DERIVATIVE_AND_EDGE_CERTIFICATES_ABSENT",
        "TARGET_OCCUPATION_OR_PROVED_DOMINATING_RN_FACTORS_ABSENT",
        "UI_HYBRID_CHANGE_OF_MEASURE_PROOF_ABSENT",
        "CONTROLLED_PATH_LAW_UNIQUENESS_PROOF_ABSENT",
        "SIMULTANEOUS_NONVACUOUS_DIRECT_CERTIFICATES_ABSENT",
        "REAL_DOMAIN_INSTANTIATION_AND_ADMISSION_ABSENT",
    }
    if type(gaps) is not list or not required_gaps.issubset(set(gaps)):
        raise ValidationError("predecessor unresolved-gap evidence mismatch")
    effects = predecessor.get("field_and_blocker_effects", {})
    if effects.get("B01") != {"status": "OPEN", "closed_by_this_package": False}:
        raise ValidationError("predecessor B01 state mismatch")
    for index in range(1, 7):
        row = effects.get("F" + str(index).zfill(3))
        if type(row) is not dict or row.get("status") != "OPEN" or row.get("value") is not None:
            raise ValidationError("predecessor C17 field state mismatch")

    theorem_text = raws[THEOREM_TARGET_PATH].decode("utf-8")
    required_theorem_tokens = (
        "\\boxed{\\mathrm{KL}(P^h\\,\\|\\,P^{\\widehat h})}",
        "\\mathcal K_0(e)",
        "\\log\\mathbb E_{\\rho_0^h}[e^{e_0(Y_0)}]",
        "Prove the initial density ratio and the displayed formula for",
    )
    if any(token not in theorem_text for token in required_theorem_tokens):
        raise ValidationError("theorem target token missing")


def _validate_human(root: Path) -> None:
    raw = _stable_read(root, HUMAN_PATH)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("human proof is not UTF-8") from error
    required = (
        "Theorem PO13.1 (initializer density ratio and oriented KL)",
        "Corollary PO13.2 (certified oscillation bound)",
        "Theorem PO13.5 (smooth terminal-matched unbounded obstruction)",
        "Gate-A route-narrowing decision",
        "PO13_DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS",
        "GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO=true",
        "REAL_DOMAIN_C17_PROMOTION_UNDER_CURRENT_FORK_B_OBSERVABILITY = NO_GO",
        "closes 0 of 172 preregistration fields",
    )
    if any(token not in text for token in required):
        raise ValidationError("human proof required token missing")
    forbidden = (
        "C17 is proved",
        "Gate A is complete",
        "U0 is certified for PhysioNet",
        "U0 is certified for Retail",
    )
    if any(token in text for token in forbidden):
        raise ValidationError("human proof contains forbidden promotion")


def _validate_package(root: Path, record: Mapping[str, Any]) -> None:
    observed = _package_bindings(root)
    _strict_equal(record["package_bindings"], observed, "package bindings")


def load_record(root: Optional[Path] = None) -> Tuple[Path, bytes, Dict[str, Any]]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    try:
        record = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not canonical ASCII JSON") from error
    if type(record) is not dict:
        raise ValidationError("machine record must be an object")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    return workspace, raw, record


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate the exact stopped proof package and return its narrow status."""

    workspace, _, record = load_record(root)
    if set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine top-level key roster mismatch")
    expected = expected_record(workspace)
    _strict_equal(record, expected, "machine record")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("machine self digest mismatch")
    _validate_inputs(workspace)
    _validate_human(workspace)
    _validate_package(workspace, record)
    witness = evaluate_exact_witness(record["finite_exact_witness"])
    discharged = [
        row
        for row in record["proof_obligation_effects"]
        if row["mathematical_derivation_discharged"]
    ]
    if [row["proof_obligation_id"] for row in discharged] != ["PO13"]:
        raise ValidationError("proof discharge roster is not exactly PO13")
    gate = record["gate_A_route_narrowing_decision"]
    if gate["decision"] != "ROUTE_NARROWED_PREOUTCOME_NO_GO":
        raise ValidationError("Gate-A route decision mismatch")
    if len(gate["survival_conditions"]) != 9 or any(
        row["currently_satisfied"] is not False
        for row in gate["survival_conditions"]
    ):
        raise ValidationError("Gate-A survival-condition state mismatch")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value_after_independent_audit": True,
        "gate_control_predicate": GATE_CONTROL_PREDICATE,
        "gate_control_predicate_value_after_independent_audit": True,
        "selected_route": ROUTE,
        "orientation": ORIENTATION,
        "proof_obligation_count": 18,
        "proof_obligations_discharged_by_package": 1,
        "discharged_obligation": "PO13",
        "PO16_open": True,
        "A1_through_A12_open_count": 12,
        "finite_nonvacuous_U0_present": False,
        "C17_status": "UNPROVED",
        "Gate_A_C17_item": "ROUTE_NARROWED_PREOUTCOME_NO_GO",
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "exact_witness": witness["exact_rational_identities"],
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
