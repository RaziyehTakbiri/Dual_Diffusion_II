"""Read-only validator for the C17 Fork-B assumptions/crosswalk draft.

The module validates an additive static administrative package.  It does not
import project science, execute a diagnostic, contact a source, inspect data,
draw entropy, or write a project file.  Immutable route-selection inputs are
reopened during ordinary validation.  Mutable theorem documents and source
files are represented as a historical snapshot and are reopened only by the
explicit ``audit_historical_snapshot_at_freeze`` function; their later
legitimate evolution does not invalidate this package.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-c17-fork-b-assumptions-"
    "proof-code-crosswalk-draft-v1"
)
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "C17_FORK_B_ASSUMPTIONS_AND_PROOF_CODE_CROSSWALK_DRAFT_VALIDATED_UNPROVED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "ADDITIVE_STATIC_C17_PROOF_PROGRAM_DRAFT_NO_SCIENTIFIC_EFFECT"
CONTROL_PREDICATE = "C17_FORK_B_ASSUMPTIONS_AND_PROOF_CODE_CROSSWALK_DRAFT_VALIDATED"
REPORTED_DATE = "2026-08-30"

HUMAN_PATH = "PROJECT_C17_FORK_B_ASSUMPTIONS_PROOF_CODE_CROSSWALK_DRAFT.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.py"
)

PREREG_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
STATIC_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
STATIC_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
STATIC_VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
STATIC_TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)

NORMALIZED_AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. "
    "Mark all the completed tasks as the end."
)
AUTHORITY_TEXT_SHA256 = (
    "465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38"
)

ROUTE = "FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES"
ORIENTATION = "KL(P_H || P_HHAT)_TARGET_FIRST"
COMMON_SUPPORT_POLICY = (
    "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
    "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
)


class ValidationError(ValueError):
    """Raised when custody, canonical form, exact types, or semantics fail."""


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


def _foreign_self_digest(record: Mapping[str, Any]) -> str:
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
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or any(
        part in ("", ".", "..") for part in pure.parts
    ):
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


def _strict_absent(root: Path, relative_path: str) -> None:
    path = _safe_relative_path(root, relative_path)
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValidationError("historically absent path is present: " + relative_path)


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    self_digest: Optional[str] = None,
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
    if self_digest is not None:
        row["record_sha256"] = self_digest
    return row


LIVE_IMMUTABLE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "EXECUTION_PREREGISTRATION_MACHINE", "path": PREREG_MACHINE_PATH, "bytes": 39771, "raw_sha256": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 1, "role": "PREEXECUTION_CLOSURE_MACHINE", "path": CLOSURE_MACHINE_PATH, "bytes": 24571, "raw_sha256": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"},
    {"ordinal": 2, "role": "STATIC_SELECTION_HUMAN", "path": STATIC_HUMAN_PATH, "bytes": 23012, "raw_sha256": "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 3, "role": "STATIC_SELECTION_MACHINE", "path": STATIC_MACHINE_PATH, "bytes": 33638, "raw_sha256": "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "1f02200d524749d6708695072dfbc8b785a6f03d5be908b3563f121d7fcd5b53"},
    {"ordinal": 4, "role": "STATIC_SELECTION_VALIDATOR", "path": STATIC_VALIDATOR_PATH, "bytes": 56344, "raw_sha256": "8843cef229c24cbd25cd00e55697755c8fc7a1247f20044dfe110e182e558ec0", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 5, "role": "STATIC_SELECTION_HOSTILE_TEST", "path": STATIC_TEST_PATH, "bytes": 48158, "raw_sha256": "801fc7c87f57eb72da6cdfa7b2be93c6edd66b974fefe47dabbe5b91eaa0f005", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
)


HISTORICAL_DOCUMENT_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "C17_THEOREM_TARGET", "path": "manuscript_v3/c17_hybrid_path_error_theorem.md", "bytes": 34923, "raw_sha256": "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 1, "role": "FORK_B_DIRECT_CERTIFICATE_CONTRACT", "path": "manuscript_v3/c17_fork_b_direct_certificate_contract.md", "bytes": 7109, "raw_sha256": "80c00dd62106e9fd4743fd6999c1e642f0ef31b063cf9ae3c84822b7a68deae4", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 2, "role": "CAP_DEFECT_CANCELLATION_CONTRACT", "path": "manuscript_v3/c17_cap_defect_cancellation_contract.md", "bytes": 5931, "raw_sha256": "a0a57cdba08c588269c8706ab78bb68ac2360f29b97d20cd05cdcd3a8c93cb3f", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 3, "role": "FINITE_A1_ASSOCIATION_CONTRACT", "path": "manuscript_v3/c17_finite_a1_association_component_contract.md", "bytes": 8189, "raw_sha256": "063a9acabd79a3c329aa721aded5c4ec8804749aaccde3d8e2096c41d5ce78c8", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 4, "role": "EXECUTABLE_METHOD_SPEC_HISTORICAL_SNAPSHOT", "path": "manuscript_v3/executable_method_spec.md", "bytes": 442123, "raw_sha256": "58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 5, "role": "NOVELTY_AUDIT_HISTORICAL_SNAPSHOT", "path": "manuscript_v3/novelty_audit_matrix.md", "bytes": 27171, "raw_sha256": "ec11ddf036873958e218d092be2803c939881bf2b5d9a8adb6de71bdb92e33a1", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
)


HISTORICAL_SOURCE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "CAPPED_REFERENCE_STATE", "path": "src/heterodiff/theory/configuration_reference.py", "bytes": 35567, "raw_sha256": "725ddc4011e2c6cf15f1810be6fabc404c50bd53333e34ad22bedcdf4d6497da", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["CappedPoissonConfigurationReference"]},
    {"ordinal": 1, "role": "BASE_REFERENCE_CHARACTERISTICS", "path": "src/heterodiff/processes/reversible_hybrid_reference.py", "bytes": 65650, "raw_sha256": "4cb33ee7e3297b8d405d090fe03420ff45ba6e7cdbac4a85d6d5580027ed370e", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["ReversibleHybridReference"]},
    {"ordinal": 2, "role": "ASSOCIATION_OBSERVATION", "path": "src/heterodiff/theory/association_observation.py", "bytes": 151385, "raw_sha256": "948a0dfcd55b6301cddcc00746cb67a0b5b18b3c8e70433b2f44351e889fe906", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["evaluate_association_observation", "association_log_density_coordinate_gradients"]},
    {"ordinal": 3, "role": "ANALYTIC_ASSOCIATION_GUIDE", "path": "src/heterodiff/theory/association_preconditioner.py", "bytes": 197693, "raw_sha256": "29e8a37fa1b74a37fc84d5208793e00e9b19674d6988bcfad46ac50613b1148c", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["AnalyticAssociationPreconditioner", "evaluate", "coordinate_gradients", "edit_log_ratio", "cap_boundary_defect", "estimate_cap_boundary_from_proposal"]},
    {"ordinal": 4, "role": "CONFIGURATION_RESIDUAL_INTERFACE", "path": "src/heterodiff/models/configuration_residual_torch.py", "bytes": 60679, "raw_sha256": "3afc4534f09f2cf41e3a737322c44112620fb9055aa51378c3c326c9c4a2293b", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["configuration_residual", "configuration_residual_state_pair_difference", "configuration_residual_coordinate_gradients"]},
    {"ordinal": 5, "role": "FINITE_POPULATION_RISK", "path": "src/heterodiff/theory/finite_bridge_population.py", "bytes": 25808, "raw_sha256": "6ebbce521f876436b5229c28f725f7256c013f7a22d81f722b923632e124261e", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["equal_prior_logistic_risk_per_time", "population_equal_prior_logistic_risk"]},
    {"ordinal": 6, "role": "FINITE_INITIAL_AND_PATH_KL", "path": "src/heterodiff/theory/finite_bridge_path_control.py", "bytes": 45529, "raw_sha256": "1cdb2cf82016ad0979fff3ef7451fe6116904cca772b017e6e605b78b476c502", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["conditional_initial_law", "tilted_path_kl"]},
    {"ordinal": 7, "role": "FINITE_CTMC_PATH_KL", "path": "src/heterodiff/theory/path_kl.py", "bytes": 15389, "raw_sha256": "769992c89f151d90c04c66c50cad538bfa859396d8f6737aa6b5e05e39bb173a", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["ctmc_path_kl"]},
    {"ordinal": 8, "role": "FINITE_ASSOCIATION_BRIDGE", "path": "src/heterodiff/theory/finite_atomic_association_bridge.py", "bytes": 22215, "raw_sha256": "1c9f8b2c3e53f97870f07d636505e04147f3dfe3f048b03c15f4fd8c2942133c", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["FiniteAtomicAssociationBridgeOracle"]},
    {"ordinal": 9, "role": "MIXED_KNOWN_LAW_ORACLE", "path": "src/heterodiff/evaluation/mixed_ctmc_ou_known_law_oracle.py", "bytes": 35409, "raw_sha256": "b07c406f837e51d02a5608377330f4eed256801305712efc8082741e38822198", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["build_mixed_ctmc_ou_known_law_oracle"]},
    {"ordinal": 10, "role": "FINITE_FORK_B_DIAGNOSTIC", "path": "src/heterodiff/evaluation/finite_association_fork_b_diagnostic.py", "bytes": 57731, "raw_sha256": "a7279bd83a0e7cc65c132a9f5f73c18fd7bd15a896ceb86788aa4194650ac94d", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["evaluate_finite_association_fork_b_diagnostic"]},
    {"ordinal": 11, "role": "MIXED_PATH_KL_DIAGNOSTIC", "path": "src/heterodiff/evaluation/mixed_ctmc_ou_path_kl_diagnostic.py", "bytes": 31393, "raw_sha256": "448f50ebde693aa6f7141fcbd91541b781fba4efde92eaf8e0674d8537ca7d7f", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["build_mixed_ctmc_ou_path_kl_diagnostic"]},
    {"ordinal": 12, "role": "CAP_DEFECT_CANCELLATION_DIAGNOSTIC", "path": "src/heterodiff/evaluation/mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py", "bytes": 28528, "raw_sha256": "50b9748a50982f10f289cba94c8ace9adab6ea003e57da091958fda8844f6ef9", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic"]},
    {"ordinal": 13, "role": "TOTALIZED_OPERATIONAL_COMPOSER", "path": "src/heterodiff/models/configuration_totalized_jump_potential_composer_torch.py", "bytes": 106034, "raw_sha256": "bbb31fc7e48c2d18a8ae7b196f20639ec56d0e8089a210222b437c6a8bb78076", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["TotalizedConfigurationJumpPotentialComposer"]},
    {"ordinal": 14, "role": "REFERENCE_CANDIDATE_PREFLIGHT", "path": "src/heterodiff/processes/plugin_bridge_sampler.py", "bytes": 49550, "raw_sha256": "f6d7357f193651416b68cca9f3365855f520c5a7c2eb876114fc9e286627abc2", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "expected_symbols": ["ProcessValidReferenceJumpComposer"]},
)


HISTORICAL_ABSENCE_OBSERVATIONS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "path": "src/heterodiff/theory/mixed_hybrid_oracle.py", "historically_absent": True, "permanent_absence_gate": False},
    {"ordinal": 1, "path": "src/heterodiff/theory/mixed_hybrid_conditional_oracle.py", "historically_absent": True, "permanent_absence_gate": False},
    {"ordinal": 2, "path": "src/heterodiff/theory/mixed_hybrid_conditional_sampler.py", "historically_absent": True, "permanent_absence_gate": False},
    {"ordinal": 3, "path": "src/heterodiff/models/configuration_potential_composer_torch.py", "historically_absent": True, "permanent_absence_gate": False},
)


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "source": "CONVERSATION_VISIBLE_TEXT",
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 92,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_UNBOUND",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "local_additive_block2_block3_draft_work_authorized": True,
    "later_one_way_tracker_marking_after_independent_audit_authorized": True,
    "tracker_modified_by_this_package": False,
    "user_selected_file_paths_or_schema": False,
    "agent_selected_bounded_implementation_details": True,
    "external_contact_or_browsing_authorized": False,
    "data_access_or_download_authorized": False,
    "runtime_approval_authorized": False,
    "scientific_execution_authorized": False,
    "training_authorized": False,
    "claim_promotion_or_submission_authorized": False,
}


EXPECTED_ROUTE_SELECTION: Mapping[str, Any] = {
    "route": ROUTE,
    "orientation": ORIENTATION,
    "component_order": ["K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"],
    "simultaneous_upper_bound_order": ["U0", "UC", "U_PLUS", "U_MINUS", "U_REPLACEMENT"],
    "common_support_policy": COMMON_SUPPORT_POLICY,
    "viability": "CONDITIONALLY_VIABLE_PROOF_PROGRAM_NOT_CURRENTLY_DISCHARGED_OR_NONVACUOUS",
    "logical_implication_only": "PROVED_C17_IDENTITY_AND_VALID_SIMULTANEOUS_COMPONENT_BOUNDS_IMPLIES_SUM_BOUND",
    "c17_status": "UNPROVED",
    "a1_through_a12_proved": False,
    "finite_nonvacuous_bounds_present": False,
    "target_occupation_available": False,
    "dominating_measure_and_exact_radon_nikodym_factors_available": False,
    "physionet_domain_admitted": False,
    "retail_domain_admitted": False,
    "nce_used_as_path_certificate": False,
    "cap_or_reference_defect_added_as_sixth_kl_term": False,
    "manuscript_claim_promoted": False,
    "scientific_effect": 0,
}


def _assumption_rows() -> List[Dict[str, Any]]:
    definitions = (
        ("A1", "STATE_AND_MEASURABLE_STRUCTURE", "OPEN_PARTIAL_CODE_SURFACE", ["CS01", "CS02"], ["PO01"]),
        ("A2", "WELL_POSED_CANDIDATE_BASE", "OPEN_PARTIAL_CODE_SURFACE", ["CS02"], ["PO02"]),
        ("A3", "POSITIVE_FINITE_INFORMATION_FUNCTIONS", "OPEN_POLICY_SELECTED_DOMAIN_UNVERIFIED", ["CS03", "CS04"], ["PO03"]),
        ("A4", "TERMINAL_AND_CLEAN_HOLD_COMPATIBILITY", "OPEN_SPECIFICATION_ONLY", ["CS03", "CS04"], ["PO04"]),
        ("A5", "WITHIN_STRATUM_DIFFERENTIABILITY_AND_INTEGRABILITY", "OPEN_PARTIAL_CODE_SURFACE", ["CS03", "CS04", "CS05"], ["PO05"]),
        ("A6", "SHARED_DIFFUSION_AND_DEGENERATE_RANGE", "OPEN_SPECIFICATION_ONLY", ["CS02", "CS10"], ["PO06"]),
        ("A7", "COMMON_JUMP_SUPPORT_AND_EXACT_RN_FACTORS", "OPEN_PARTIAL_CODE_SURFACE", ["CS02", "CS04", "CS15"], ["PO07"]),
        ("A8", "FINITE_TARGET_COMPENSATORS", "OPEN_FINITE_FIXTURES_ONLY", ["CS07", "CS08", "CS10"], ["PO08"]),
        ("A9", "TRUE_UI_CHANGE_OF_MEASURE_MARTINGALE", "OPEN_NO_UI_PROOF", ["CS07", "CS08"], ["PO09"]),
        ("A10", "CONTROLLED_PATH_LAW_UNIQUENESS", "OPEN_NO_UNIQUENESS_PROOF", ["CS02"], ["PO10"]),
        ("A11", "EXACT_LAW_NOT_NUMERICAL_OR_OPERATIONAL_PATH", "OPEN_INTERFACE_SEPARATION_ONLY", ["CS07", "CS08", "CS14", "CS15"], ["PO11"]),
        ("A12", "CONDITIONING_AND_CANDIDATE_BASE_SCOPE", "OPEN_SCOPE_DECLARED_BROADER_EQUALITY_UNPROVED", ["CS02", "CS06"], ["PO12"]),
    )
    rows: List[Dict[str, Any]] = []
    for ordinal, (identifier, title, disposition, symbols, obligations) in enumerate(definitions):
        rows.append({
            "ordinal": ordinal,
            "assumption_id": identifier,
            "title": title,
            "required_for_current_c17_target": True,
            "current_disposition": disposition,
            "evidence_strength": "PARTIAL_OR_SPECIFICATION_ONLY_NOT_PROOF",
            "code_symbol_ids": symbols,
            "proof_obligation_ids": obligations,
            "verified_for_general_c17": False,
            "verified_for_physionet": False,
            "verified_for_retail": False,
            "closed_by_this_package": False,
        })
    return rows


def _proof_obligation_rows() -> List[Dict[str, Any]]:
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
    for ordinal, title in enumerate(titles):
        rows.append({
            "ordinal": ordinal,
            "proof_obligation_id": "PO" + str(ordinal + 1).zfill(2),
            "title": title,
            "status": "OPEN",
            "required_for_c17": True,
            "discharged": False,
            "real_domain_discharged": False,
            "code_evidence_sufficient": False,
            "closed_by_this_package": False,
        })
    return rows


def _component_certificate_rows() -> List[Dict[str, Any]]:
    definitions = (
        ("K0", "U0", "TARGET_INITIAL_LAW"),
        ("KC", "UC", "TARGET_OCCUPATION_OR_PROVED_DOMINATION"),
        ("K_PLUS", "U_PLUS", "TARGET_BIRTH_COMPENSATOR_OR_PROVED_DOMINATION"),
        ("K_MINUS", "U_MINUS", "TARGET_DEATH_COMPENSATOR_OR_PROVED_DOMINATION"),
        ("K_REPLACEMENT", "U_REPLACEMENT", "TARGET_REPLACEMENT_COMPENSATOR_OR_PROVED_DOMINATION"),
    )
    rows: List[Dict[str, Any]] = []
    for ordinal, (component, upper_bound, measure) in enumerate(definitions):
        rows.append({
            "ordinal": ordinal,
            "component_id": component,
            "upper_bound_id": upper_bound,
            "required_measure": measure,
            "bound_value": None,
            "certificate_path": None,
            "occupation_receipt": None,
            "dominating_measure_receipt": None,
            "radon_nikodym_factor_receipt": None,
            "simultaneous_event_receipt": None,
            "nonvacuity_threshold": None,
            "finite": False,
            "nonvacuous": False,
            "certificate_present": False,
            "closed_by_this_package": False,
        })
    return rows


EXPECTED_CROSSWALK: List[Mapping[str, Any]] = [
    {"symbol_id": "CS01", "mathematical_object": "CAPPED_REFERENCE_STATE", "source_ordinal": 0, "strength": "PARTIAL_CODE_SURFACE", "sufficient_for_c17": False},
    {"symbol_id": "CS02", "mathematical_object": "BASE_REFERENCE_CHARACTERISTICS", "source_ordinal": 1, "strength": "PARTIAL_CODE_SURFACE", "sufficient_for_c17": False},
    {"symbol_id": "CS03", "mathematical_object": "TERMINAL_ASSOCIATION_LAW", "source_ordinal": 2, "strength": "PARTIAL_CODE_SURFACE", "sufficient_for_c17": False},
    {"symbol_id": "CS04", "mathematical_object": "ANALYTIC_GUIDE_AND_CAP_DIAGNOSTIC", "source_ordinal": 3, "strength": "PARTIAL_CODE_SURFACE", "sufficient_for_c17": False},
    {"symbol_id": "CS05", "mathematical_object": "LEARNED_RESIDUAL_INTERFACE", "source_ordinal": 4, "strength": "INTERFACE_ONLY_NO_CERTIFIED_ERROR_TO_R_STAR", "sufficient_for_c17": False},
    {"symbol_id": "CS06", "mathematical_object": "FINITE_JOINT_PRODUCT_RISK", "source_ordinal": 5, "strength": "FINITE_ORACLE_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS07", "mathematical_object": "FINITE_INITIAL_AND_PATH_KL", "source_ordinal": 6, "strength": "FINITE_JUMP_ONLY_ORACLE", "sufficient_for_c17": False},
    {"symbol_id": "CS08", "mathematical_object": "FINITE_CTMC_PATH_KL", "source_ordinal": 7, "strength": "FINITE_NUMERICAL_DIAGNOSTIC", "sufficient_for_c17": False},
    {"symbol_id": "CS09", "mathematical_object": "FINITE_ASSOCIATION_BRIDGE", "source_ordinal": 8, "strength": "A1_SCALE_ORACLE_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS10", "mathematical_object": "MIXED_KNOWN_LAW_FIXTURE", "source_ordinal": 9, "strength": "FINITE_FACTORIZED_DIAGNOSTIC_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS11", "mathematical_object": "FINITE_FORK_B_COMPONENT_DIAGNOSTIC", "source_ordinal": 10, "strength": "PARTIAL_DIAGNOSTIC_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS12", "mathematical_object": "MIXED_PATH_KL_DIAGNOSTIC", "source_ordinal": 11, "strength": "FINITE_FACTORIZED_NUMERICAL_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS13", "mathematical_object": "CAP_DEFECT_CANCELLATION_DIAGNOSTIC", "source_ordinal": 12, "strength": "ALGEBRAIC_DIAGNOSTIC_ONLY", "sufficient_for_c17": False},
    {"symbol_id": "CS14", "mathematical_object": "TOTALIZED_OPERATIONAL_COMPOSER", "source_ordinal": 13, "strength": "OPERATIONAL_SURROGATE_NOT_ANALYTIC_H", "sufficient_for_c17": False},
    {"symbol_id": "CS15", "mathematical_object": "REFERENCE_CANDIDATE_PREFLIGHT", "source_ordinal": 14, "strength": "PREFLIGHT_ONLY_NOT_COMPLETE_SAMPLER", "sufficient_for_c17": False},
]


EXPECTED_UNRESOLVED_GAPS: List[str] = [
    "GENERAL_SAME_CONTEXT_JOINT_PRODUCT_TRAINER_AND_NUISANCE_BRANCH_ABSENT",
    "EXACT_UNKNOWN_RESIDUAL_R_STAR_UNAVAILABLE",
    "ERROR_TO_R_STAR_DERIVATIVE_AND_EDGE_CERTIFICATES_ABSENT",
    "TARGET_OCCUPATION_OR_PROVED_DOMINATING_RN_FACTORS_ABSENT",
    "UI_HYBRID_CHANGE_OF_MEASURE_PROOF_ABSENT",
    "CONTROLLED_PATH_LAW_UNIQUENESS_PROOF_ABSENT",
    "GENERAL_IDEAL_MIXED_LEARNED_PATH_LAW_ABSENT",
    "CAP_REFERENCE_STABILITY_ROUTE_ABSENT",
    "SIMULTANEOUS_NONVACUOUS_DIRECT_CERTIFICATES_ABSENT",
    "REAL_DOMAIN_INSTANTIATION_AND_ADMISSION_ABSENT",
    "METHOD_SPEC_LIVE_SOURCE_CROSSWALK_CONFLICT_UNRESOLVED",
]


EXPECTED_FIELD_EFFECTS: Mapping[str, Any] = {
    "B01": {"status": "OPEN", "closed_by_this_package": False},
    "F001": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F002": {"status": "OPEN", "value": None, "draft_inventory_present": True, "closed_by_this_package": False},
    "F003": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F004": {"status": "OPEN", "value": None, "draft_crosswalk_present": True, "closed_by_this_package": False},
    "F005": {"status": "OPEN", "value": None, "fork_b_does_not_select_coercivity_statement": True, "closed_by_this_package": False},
    "F006": {"status": "OPEN", "value": None, "closed_by_this_package": False},
}


EXPECTED_SCOPE: Mapping[str, Any] = {
    "control_predicate": CONTROL_PREDICATE,
    "control_predicate_value_after_validation": True,
    "control_predicate_is_project_control_not_prereg_field_or_theorem": True,
    "static_draft_and_read_only_qualification_only": True,
    "historical_source_snapshot_is_not_permanent_absence_gate": True,
    "historical_snapshot_standard_validation_reopened": False,
    "explicit_historical_freeze_audit_available": True,
    "project_science_imported_or_executed": False,
    "network_or_external_contact_performed_by_package": False,
    "dataset_or_outcome_accessed": False,
    "runtime_or_scientific_execution_performed": False,
    "tracker_edited": False,
    "existing_files_modified": False,
    "unresolved_field_count": 172,
    "effective_open_blocker_count": 12,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "scientific_results_produced": 0,
    "c17_claim_promoted": False,
    "c19_closed": False,
    "common_support_domain_admission_promoted": False,
    "confirmatory_execution_authorized": False,
}


EXPECTED_TOP_LEVEL_KEYS: Set[str] = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "route_selection",
    "assumption_inventory",
    "proof_obligation_register",
    "direct_certificate_register",
    "proof_code_crosswalk",
    "unresolved_gap_register",
    "field_and_blocker_effects",
    "historical_snapshot_inputs",
    "scope_and_nonclaims",
    "live_immutable_input_bindings",
    "package_bindings",
    "record_sha256",
}


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, role, path in (
        (0, "HUMAN_C17_DRAFT", HUMAN_PATH),
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
        "route_selection": dict(EXPECTED_ROUTE_SELECTION),
        "assumption_inventory": _assumption_rows(),
        "proof_obligation_register": _proof_obligation_rows(),
        "direct_certificate_register": _component_certificate_rows(),
        "proof_code_crosswalk": [dict(row) for row in EXPECTED_CROSSWALK],
        "unresolved_gap_register": list(EXPECTED_UNRESOLVED_GAPS),
        "field_and_blocker_effects": dict(EXPECTED_FIELD_EFFECTS),
        "historical_snapshot_inputs": {
            "documents": [dict(row) for row in HISTORICAL_DOCUMENT_BINDINGS],
            "sources": [dict(row) for row in HISTORICAL_SOURCE_BINDINGS],
            "absent_paths_at_snapshot": [
                dict(row) for row in HISTORICAL_ABSENCE_OBSERVATIONS
            ],
            "snapshot_date": REPORTED_DATE,
            "standard_validation_reopens_snapshot": False,
            "future_materialization_or_refactor_permitted": True,
            "new_one_way_audit_required_after_change": True,
        },
        "scope_and_nonclaims": dict(EXPECTED_SCOPE),
        "live_immutable_input_bindings": [
            dict(row) for row in LIVE_IMMUTABLE_BINDINGS
        ],
        "package_bindings": _package_bindings(workspace),
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _validate_live_inputs(root: Path) -> None:
    raws: Dict[str, bytes] = {}
    for expected in LIVE_IMMUTABLE_BINDINGS:
        raw = _stable_read(root, expected["path"])
        raws[expected["path"]] = raw
        observed = _binding(
            expected["ordinal"],
            expected["role"],
            expected["path"],
            raw,
            self_digest=expected.get("record_sha256"),
        )
        _strict_equal(observed, dict(expected), "immutable input binding")

    prereg = json.loads(raws[PREREG_MACHINE_PATH].decode("ascii"))
    if type(prereg) is not dict or prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration execution authority changed")
    theory = prereg.get("theory_and_known_law_plan")
    if type(theory) is not dict:
        raise ValidationError("preregistration theory plan missing")
    for field in (
        "c17_final_theorem_statement",
        "c17_assumption_inventory",
        "c17_proof_artifact_path",
        "c17_code_definition_crosswalk_path",
        "excess_logistic_risk_to_hybrid_dirichlet_control_statement",
        "coercivity_or_identifiability_assumptions",
    ):
        if field not in theory or theory[field] is not None:
            raise ValidationError("C17 preregistration field is not open: " + field)

    closure = json.loads(raws[CLOSURE_MACHINE_PATH].decode("ascii"))
    if type(closure) is not dict:
        raise ValidationError("closure record type invalid")
    if _foreign_self_digest(closure) != closure.get("record_sha256"):
        raise ValidationError("closure self digest invalid")
    nulls = closure.get("null_projection")
    blockers = closure.get("blocker_projection")
    if (
        type(nulls) is not dict
        or nulls.get("effective_total_unresolved_null_count") != 172
        or type(blockers) is not dict
        or blockers.get("effective_unresolved_blocker_count") != 12
        or blockers.get("blockers_closed_by_closure") != 0
    ):
        raise ValidationError("closure count projection changed")

    static = json.loads(raws[STATIC_MACHINE_PATH].decode("ascii"))
    if type(static) is not dict:
        raise ValidationError("static selection record type invalid")
    if _foreign_self_digest(static) != static.get("record_sha256"):
        raise ValidationError("static selection self digest invalid")
    c17 = static.get("c17_selection")
    support = static.get("common_support_selection")
    if type(c17) is not dict or type(support) is not dict:
        raise ValidationError("static selection blocks missing")
    if (
        c17.get("route") != ROUTE
        or c17.get("orientation") != ORIENTATION
        or c17.get("component_order")
        != ["K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"]
        or c17.get("simultaneous_upper_bound_order")
        != ["U0", "UC", "U_PLUS", "U_MINUS", "U_REPLACEMENT"]
        or c17.get("c17_proved") is not False
        or c17.get("a1_through_a12_proved") is not False
        or c17.get("finite_nonvacuous_bounds_present") is not False
        or support.get("policy") != COMMON_SUPPORT_POLICY
        or support.get("domain_admission_promoted") is not False
    ):
        raise ValidationError("frozen C17 or common-support selection changed")


def _validate_semantics(record: Mapping[str, Any]) -> None:
    route = record["route_selection"]
    if (
        route["c17_status"] != "UNPROVED"
        or route["finite_nonvacuous_bounds_present"] is not False
        or route["target_occupation_available"] is not False
        or route["manuscript_claim_promoted"] is not False
        or type(route["scientific_effect"]) is not int
        or route["scientific_effect"] != 0
    ):
        raise ValidationError("C17 route overclaim")

    assumptions = record["assumption_inventory"]
    if len(assumptions) != 12:
        raise ValidationError("assumption inventory length mismatch")
    for ordinal, row in enumerate(assumptions):
        if (
            row["ordinal"] != ordinal
            or type(row["ordinal"]) is not int
            or row["assumption_id"] != "A" + str(ordinal + 1)
            or row["required_for_current_c17_target"] is not True
            or row["verified_for_general_c17"] is not False
            or row["verified_for_physionet"] is not False
            or row["verified_for_retail"] is not False
            or row["closed_by_this_package"] is not False
        ):
            raise ValidationError("assumption row overclaim or ordering error")

    obligations = record["proof_obligation_register"]
    if len(obligations) != 18:
        raise ValidationError("proof-obligation length mismatch")
    for ordinal, row in enumerate(obligations):
        if (
            row["ordinal"] != ordinal
            or type(row["ordinal"]) is not int
            or row["proof_obligation_id"] != "PO" + str(ordinal + 1).zfill(2)
            or row["status"] != "OPEN"
            or row["discharged"] is not False
            or row["real_domain_discharged"] is not False
            or row["code_evidence_sufficient"] is not False
            or row["closed_by_this_package"] is not False
        ):
            raise ValidationError("proof obligation overclaim or ordering error")

    certificates = record["direct_certificate_register"]
    if len(certificates) != 5:
        raise ValidationError("certificate component length mismatch")
    for ordinal, row in enumerate(certificates):
        if row["ordinal"] != ordinal or type(row["ordinal"]) is not int:
            raise ValidationError("certificate ordinal mismatch")
        for field in (
            "bound_value",
            "certificate_path",
            "occupation_receipt",
            "dominating_measure_receipt",
            "radon_nikodym_factor_receipt",
            "simultaneous_event_receipt",
            "nonvacuity_threshold",
        ):
            if row[field] is not None:
                raise ValidationError("certificate typed-null promoted: " + field)
        if (
            row["finite"] is not False
            or row["nonvacuous"] is not False
            or row["certificate_present"] is not False
            or row["closed_by_this_package"] is not False
        ):
            raise ValidationError("certificate overclaim")

    if len(record["proof_code_crosswalk"]) != 15 or any(
        row["sufficient_for_c17"] is not False
        for row in record["proof_code_crosswalk"]
    ):
        raise ValidationError("code crosswalk overclaim")
    if set(record["field_and_blocker_effects"]) != {
        "B01", "F001", "F002", "F003", "F004", "F005", "F006"
    }:
        raise ValidationError("field effect roster mismatch")
    for identifier, row in record["field_and_blocker_effects"].items():
        if row["status"] != "OPEN" or row["closed_by_this_package"] is not False:
            raise ValidationError("field or blocker promoted: " + identifier)
        if identifier.startswith("F") and row["value"] is not None:
            raise ValidationError("preregistration field populated: " + identifier)
    scope = record["scope_and_nonclaims"]
    if (
        scope["unresolved_field_count"] != 172
        or scope["effective_open_blocker_count"] != 12
        or scope["unresolved_fields_closed"] != 0
        or scope["blockers_closed"] != 0
        or scope["tracker_edited"] is not False
        or scope["c17_claim_promoted"] is not False
        or scope["confirmatory_execution_authorized"] is not False
    ):
        raise ValidationError("scope or nonclosure boundary changed")


def audit_historical_snapshot_at_freeze(
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Reproduce the historical doc/source/absence observation explicitly."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    for expected in HISTORICAL_DOCUMENT_BINDINGS:
        raw = _stable_read(workspace, expected["path"])
        observed = _binding(
            expected["ordinal"], expected["role"], expected["path"], raw
        )
        _strict_equal(observed, dict(expected), "historical document binding")
    symbol_count = 0
    for expected in HISTORICAL_SOURCE_BINDINGS:
        raw = _stable_read(workspace, expected["path"])
        observed = _binding(
            expected["ordinal"], expected["role"], expected["path"], raw
        )
        observed["expected_symbols"] = list(expected["expected_symbols"])
        _strict_equal(observed, dict(expected), "historical source binding")
        try:
            tree = ast.parse(raw.decode("utf-8"), filename=expected["path"])
        except (SyntaxError, UnicodeDecodeError) as error:
            raise ValidationError("historical source AST invalid") from error
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for symbol in expected["expected_symbols"]:
            if symbol not in names:
                raise ValidationError(
                    "historical expected symbol absent: " + expected["path"]
                    + ":" + symbol
                )
            symbol_count += 1
    for row in HISTORICAL_ABSENCE_OBSERVATIONS:
        _strict_absent(workspace, row["path"])
        if row["historically_absent"] is not True or row["permanent_absence_gate"] is not False:
            raise ValidationError("historical absence semantics invalid")
    return {
        "snapshot_date": REPORTED_DATE,
        "document_count": len(HISTORICAL_DOCUMENT_BINDINGS),
        "source_count": len(HISTORICAL_SOURCE_BINDINGS),
        "expected_symbol_count": symbol_count,
        "historically_absent_path_count": len(HISTORICAL_ABSENCE_OBSERVATIONS),
        "method_spec_live_source_crosswalk_conflict": "UNRESOLVED",
        "standard_validation_permanent_absence_gate": False,
        "audit": "PASS",
    }


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact immutable custody, machine canonicality, and nonclaims."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    try:
        record = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not canonical ASCII JSON") from error
    if type(record) is not dict or set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine record schema mismatch")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self digest type invalid")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self digest invalid")
    _strict_equal(record, expected_record(workspace), "C17 draft record")
    _validate_live_inputs(workspace)
    _validate_semantics(record)
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "route": ROUTE,
        "viability": record["route_selection"]["viability"],
        "c17_status": "UNPROVED",
        "assumption_count": 12,
        "assumptions_proved": 0,
        "proof_obligation_count": 18,
        "proof_obligations_discharged": 0,
        "certificate_component_count": 5,
        "finite_nonvacuous_certificate_count": 0,
        "B01_open": True,
        "F001_through_F006_open_count": 6,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "historical_snapshot_reopened_by_standard_validation": False,
        "validation": "PASS",
    }


__all__ = [
    "COMMON_SUPPORT_POLICY",
    "CONTROL_PREDICATE",
    "HISTORICAL_ABSENCE_OBSERVATIONS",
    "HISTORICAL_DOCUMENT_BINDINGS",
    "HISTORICAL_SOURCE_BINDINGS",
    "LIVE_IMMUTABLE_BINDINGS",
    "MACHINE_PATH",
    "NORMALIZED_AUTHORITY_TEXT",
    "ORIENTATION",
    "ROUTE",
    "SCHEMA",
    "STATE",
    "ValidationError",
    "audit_historical_snapshot_at_freeze",
    "canonical_machine_bytes",
    "expected_record",
    "record_sha256",
    "validate",
]

