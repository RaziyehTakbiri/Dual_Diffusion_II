"""Strict, authority-free contracts for the V3 live-host rehearsal.

These contracts carry no marker, writer, runtime-admission, or scientific
authority.  They describe one read-only environment-profile observation and
its PASS/FAIL result.  Parsing a record never makes it admissible.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Tuple


REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v3-live-host-"
    "environment-rehearsal-freeze-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-qualification-v1"
)
REQUEST_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-request-v1"
)
CHILD_OBSERVATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-child-observation-v1"
)
RESULT_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-result-v1"
)
PROTECTED_SNAPSHOT_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-protected-snapshot-v1"
)

REQUEST_DOMAIN = (REQUEST_SCHEMA + "\0").encode("ascii")
CHILD_OBSERVATION_DOMAIN = (CHILD_OBSERVATION_SCHEMA + "\0").encode("ascii")
RESULT_DOMAIN = (RESULT_SCHEMA + "\0").encode("ascii")

PROFILE_ID = "M1_REFERENCE_MACOS_ARM64_PY311_V3_ENVIRONMENT_REHEARSAL"
PYTHON_FLAGS = ("-P", "-B", "-S", "-X", "utf8")
PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
PYTHON_REALPATH = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
PLANNED_RESULT_RELATIVE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_result_v1.json"
)
FUTURE_V3_MARKER_RELATIVE_PATH = (
    "artifacts/a1_r1_activation_preparation_v3.attempt.json"
)
FUTURE_V3_PREPARATION_ROOT_RELATIVE_PATH = "artifacts/a1_r1_activation_preparation_v3"
V2_TERMINAL_REGISTRATION_RECORD_SHA256 = (
    "da57dda788f5de2b2a34ed30bdaf7f692db98696a00e420aa0484d44127b6ed0"
)
EXPECTED_SYS_PATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python311.zip",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload",
)

REQUESTED_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPYCACHEPREFIX": "/dev/null",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}
REQUESTED_ENVIRONMENT_SHA256 = hashlib.sha256(
    b"heterodiff-a1-r1-activation-preparation-v3-requested-environment-v1\0"
    + json.dumps(
        REQUESTED_ENVIRONMENT,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
).hexdigest()
DARWIN_INJECTED_ENVIRONMENT_KEY = "__CF_USER_TEXT_ENCODING"
FORBIDDEN_ENVIRONMENT_KEYS = (
    "HOME",
    "PATH",
    "PYTHONHOME",
    "PYTHONPATH",
    "SSH_AUTH_SOCK",
    "USER",
)
FORBIDDEN_ENVIRONMENT_PREFIXES = (
    "AWS_",
    "DYLD_",
    "GITHUB_",
    "GOOGLE_",
    "OPENAI_",
    "SSH_",
)

HASH_PROBE_STRINGS = (
    "heterodiff-a1",
    "dual-manifold",
    "runtime-attestor",
    "frozen-prerequisite-v2",
)
HASH_PROBE_VALUES = (
    2985988193407401162,
    4011400747771974541,
    -4843661051715643476,
    2311044021579714838,
)
HASH_PROBE_PREIMAGE = (
    b"[2985988193407401162,4011400747771974541,-4843661051715643476,"
    b"2311044021579714838]"
)
HASH_PROBE_SHA256 = "f7b1ba1308d7559c69fc44640d0fcd07dbeae53b9024da5d862463db71e230af"

OBSERVATION_OUTCOMES = ("PASS", "FAIL")
RESULT_OUTCOMES = ("PASS", "FAIL")
FAILURE_CODES = (
    "NONE",
    "ARGV",
    "CWD",
    "DARWIN_ENVIRONMENT",
    "EFFECTIVE_ENVIRONMENT",
    "IDENTITY",
    "INTERPRETER",
    "PLATFORM",
    "PYTHON_FLAGS",
    "HASH_PROBE",
    "SYS_PATH",
    "SITE_MODULE",
    "SUPERVISOR_BOUNDARY",
    "ENTROPY_CONTACT",
    "NETWORK_CONTACT",
    "WORKSPACE_WRITE",
    "TEMPORARY_WRITE",
    "RAW_ENVIRONMENT_EMISSION",
    "RAW_IDENTITY_EMISSION",
    "SCIENTIFIC_IMPORT_OR_EXECUTION",
    "REHEARSAL_REPLAY",
    "RESULT_RACE",
    "RUNTIME_APPROVAL_CONTAMINATION",
    "MARKER_AUTHORIZATION_CONTAMINATION",
    "CHILD_PROCESS",
    "CHILD_STDERR",
    "CHILD_STDOUT",
    "CHILD_TIMEOUT",
    "PROTECTED_CUSTODY",
    "INTERNAL_FAILURE",
)


class ContractError(ValueError):
    """Raised when a V3 rehearsal record is not exact and canonical."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise ContractError("value is not canonical ASCII JSON") from error


def sha256(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise ContractError("SHA-256 input must be exact bytes")
    return hashlib.sha256(payload).hexdigest()


def require_sha256(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractError(name + " must be one lowercase SHA-256")
    return value


def _require_exact_keys(
    record: Any, names: Tuple[str, ...], label: str
) -> Dict[str, Any]:
    if type(record) is not dict or tuple(sorted(record)) != tuple(sorted(names)):
        raise ContractError(label + " fields changed")
    return dict(record)


def _require_bool(record: Mapping[str, Any], name: str) -> None:
    if type(record[name]) is not bool:
        raise ContractError(name + " must be an exact Boolean")


def _require_int(record: Mapping[str, Any], name: str, minimum: int = 0) -> None:
    if type(record[name]) is not int or record[name] < minimum:
        raise ContractError(name + " must be an exact bounded integer")


REQUEST_FIELDS = (
    "schema",
    "registration_raw_sha256",
    "registration_record_sha256",
    "human_sha256",
    "contracts_sha256",
    "authority_sha256",
    "runtime_sha256",
    "test_sha256",
    "v2_terminal_registration_record_sha256",
    "environment_policy_sha256",
    "workspace_anchor_identity_sha256",
    "profile_id",
    "rehearsal_ordinal",
    "python_relative_path",
    "python_realpath",
    "python_flags",
    "requested_environment_sha256",
    "hash_probe_sha256",
    "child_observation_schema",
    "result_schema",
    "planned_result_relative_path",
    "future_v3_marker_relative_path",
    "future_v3_preparation_root_relative_path",
    "workspace_write_requested",
    "entropy_requested",
    "network_contact_requested",
    "scientific_execution_requested",
    "request_sha256",
)

CHILD_OBSERVATION_FIELDS = (
    "schema",
    "request_sha256",
    "profile_id",
    "outcome",
    "failure_code",
    "direct_file_main",
    "spec_is_none",
    "python_argv_exact",
    "native_argv_exact",
    "cwd_exact",
    "requested_environment_key_count",
    "effective_environment_key_count",
    "requested_environment_exact_after_normalization",
    "darwin_injected_key_present",
    "darwin_injected_value_matches_uid",
    "darwin_injected_removed_before_observation",
    "uid_euid_equal",
    "gid_egid_equal",
    "nonprivileged_identity",
    "supplemental_root_group_absent",
    "process_taint_absent",
    "implementation_code",
    "version_code",
    "platform_code",
    "venv_executable_exact",
    "interpreter_realpath_exact",
    "python_flags_exact",
    "hash_randomization_disabled",
    "hash_probe_sha256",
    "hash_probe_matches_prefrozen_reference",
    "sys_path_exact",
    "system_only_sys_path",
    "pythonpath_absent",
    "pythonhome_absent",
    "dyld_key_count",
    "credential_key_count",
    "site_imported",
    "entropy_contacted",
    "network_contacted",
    "scientific_imports_performed",
    "workspace_write_performed",
    "temporary_write_performed",
    "raw_environment_emitted",
    "raw_identity_emitted",
    "observation_sha256",
)

RESULT_FIELDS = (
    "schema",
    "request_raw_sha256",
    "request_sha256",
    "child_observation_raw_sha256",
    "child_observation_sha256",
    "child_observation",
    "outcome",
    "failure_code",
    "child_exit_code",
    "child_transport_failure_code",
    "child_stdout_byte_count",
    "child_stderr_byte_count",
    "preflight_snapshot_sha256",
    "postflight_snapshot_sha256",
    "protected_snapshot_schema",
    "protected_path_roster_sha256",
    "workspace_anchor_identity_sha256",
    "supervisor_direct_file_main",
    "supervisor_spec_is_none",
    "supervisor_python_argv_exact",
    "supervisor_native_argv_exact",
    "supervisor_environment_exact_after_normalization",
    "supervisor_python_flags_exact",
    "supervisor_cwd_exact",
    "supervisor_profile_exact",
    "parent_environment_observation_passed",
    "child_environment_observation_passed",
    "parent_child_environment_semantics_match",
    "protected_custody_unchanged",
    "v2_terminal_custody_revalidated_intact_before",
    "v2_terminal_custody_revalidated_intact_after",
    "v3_marker_absent_before",
    "v3_marker_absent_after",
    "v3_preparation_root_absent_before",
    "v3_preparation_root_absent_after",
    "planned_result_absent_before",
    "planned_result_absent_after",
    "application_workspace_write_performed",
    "application_temporary_write_performed",
    "entropy_contacted",
    "network_contacted",
    "scientific_execution_performed",
    "runtime_approval_created",
    "marker_creation_authorized",
    "child_launch_count",
    "retry_count",
    "child_exit_observed",
    "mechanical_one_shot_enforced",
    "prepublication_replay_resistance",
    "result_sha256",
)


def _finish(record: Mapping[str, Any], terminal: str, domain: bytes) -> Dict[str, Any]:
    value = dict(record)
    if terminal not in value or value[terminal] is not None:
        raise ContractError(terminal + " must begin null")
    value[terminal] = sha256(domain + canonical_json(value))
    return value


def _validate_terminal(
    value: Dict[str, Any], terminal: str, domain: bytes, label: str
) -> None:
    claimed = require_sha256(value[terminal], terminal)
    body = dict(value)
    body[terminal] = None
    if claimed != sha256(domain + canonical_json(body)):
        raise ContractError(label + " self digest changed")


def validate_request(record: Any) -> Dict[str, Any]:
    value = _require_exact_keys(record, REQUEST_FIELDS, "request")
    if value["schema"] != REQUEST_SCHEMA:
        raise ContractError("request schema changed")
    for name in REQUEST_FIELDS:
        if name.endswith("_sha256"):
            require_sha256(value[name], name)
    _require_int(value, "rehearsal_ordinal")
    if value["rehearsal_ordinal"] != 0:
        raise ContractError("rehearsal ordinal changed")
    if (
        value["profile_id"] != PROFILE_ID
        or value["python_relative_path"] != PYTHON_RELATIVE_PATH
        or value["python_realpath"] != PYTHON_REALPATH
        or value["python_flags"] != list(PYTHON_FLAGS)
        or value["child_observation_schema"] != CHILD_OBSERVATION_SCHEMA
        or value["result_schema"] != RESULT_SCHEMA
        or value["planned_result_relative_path"] != PLANNED_RESULT_RELATIVE_PATH
        or value["future_v3_marker_relative_path"] != FUTURE_V3_MARKER_RELATIVE_PATH
        or value["future_v3_preparation_root_relative_path"]
        != FUTURE_V3_PREPARATION_ROOT_RELATIVE_PATH
        or value["v2_terminal_registration_record_sha256"]
        != V2_TERMINAL_REGISTRATION_RECORD_SHA256
        or value["requested_environment_sha256"] != REQUESTED_ENVIRONMENT_SHA256
        or value["environment_policy_sha256"] != environment_policy()["policy_sha256"]
        or value["hash_probe_sha256"] != HASH_PROBE_SHA256
    ):
        raise ContractError("request fixed profile changed")
    for name in (
        "workspace_write_requested",
        "entropy_requested",
        "network_contact_requested",
        "scientific_execution_requested",
    ):
        _require_bool(value, name)
        if value[name] is not False:
            raise ContractError(name + " must remain false")
    _validate_terminal(value, "request_sha256", REQUEST_DOMAIN, "request")
    return value


def finish_request(record: Mapping[str, Any]) -> Dict[str, Any]:
    return validate_request(_finish(record, "request_sha256", REQUEST_DOMAIN))


def _child_failure_code(value: Mapping[str, Any]) -> str:
    leading = (
        (
            "ARGV",
            (
                "direct_file_main",
                "spec_is_none",
                "python_argv_exact",
                "native_argv_exact",
            ),
        ),
        ("CWD", ("cwd_exact",)),
        (
            "DARWIN_ENVIRONMENT",
            (
                "darwin_injected_key_present",
                "darwin_injected_value_matches_uid",
                "darwin_injected_removed_before_observation",
            ),
        ),
        (
            "EFFECTIVE_ENVIRONMENT",
            (
                "requested_environment_exact_after_normalization",
                "pythonpath_absent",
                "pythonhome_absent",
            ),
        ),
        (
            "IDENTITY",
            (
                "uid_euid_equal",
                "gid_egid_equal",
                "nonprivileged_identity",
                "supplemental_root_group_absent",
                "process_taint_absent",
            ),
        ),
        ("INTERPRETER", ("venv_executable_exact", "interpreter_realpath_exact")),
    )
    for code, names in leading:
        if any(value[name] is not True for name in names):
            return code
    if (
        value["implementation_code"] != "CPYTHON"
        or value["version_code"] != "CPYTHON_3_11_5"
        or value["platform_code"] != "DARWIN_ARM64"
    ):
        return "PLATFORM"
    if any(
        value[name] is not True
        for name in ("python_flags_exact", "hash_randomization_disabled")
    ):
        return "PYTHON_FLAGS"
    if (
        value["hash_probe_sha256"] != HASH_PROBE_SHA256
        or value["hash_probe_matches_prefrozen_reference"] is not True
    ):
        return "HASH_PROBE"
    if any(
        value[name] is not True for name in ("sys_path_exact", "system_only_sys_path")
    ):
        return "SYS_PATH"
    if value["effective_environment_key_count"] != len(REQUESTED_ENVIRONMENT) + 1:
        return "EFFECTIVE_ENVIRONMENT"
    effect_priority = (
        ("SITE_MODULE", "site_imported"),
        ("RAW_ENVIRONMENT_EMISSION", "raw_environment_emitted"),
        ("RAW_IDENTITY_EMISSION", "raw_identity_emitted"),
        ("ENTROPY_CONTACT", "entropy_contacted"),
        ("NETWORK_CONTACT", "network_contacted"),
        ("SCIENTIFIC_IMPORT_OR_EXECUTION", "scientific_imports_performed"),
        ("WORKSPACE_WRITE", "workspace_write_performed"),
        ("TEMPORARY_WRITE", "temporary_write_performed"),
    )
    for code, name in effect_priority:
        if value[name] is True:
            return code
    return "NONE"


def validate_child_observation(record: Any) -> Dict[str, Any]:
    value = _require_exact_keys(record, CHILD_OBSERVATION_FIELDS, "child observation")
    if value["schema"] != CHILD_OBSERVATION_SCHEMA:
        raise ContractError("child observation schema changed")
    require_sha256(value["request_sha256"], "request_sha256")
    require_sha256(value["hash_probe_sha256"], "hash_probe_sha256")
    if value["hash_probe_sha256"] != HASH_PROBE_SHA256:
        raise ContractError("child hash reference digest changed")
    if value["profile_id"] != PROFILE_ID:
        raise ContractError("child profile changed")
    if value["outcome"] not in OBSERVATION_OUTCOMES:
        raise ContractError("child outcome changed")
    if value["failure_code"] not in FAILURE_CODES:
        raise ContractError("child failure code changed")
    if value["implementation_code"] not in {"CPYTHON", "OTHER", "NOT_OBSERVED"}:
        raise ContractError("child implementation code changed")
    if value["version_code"] not in {"CPYTHON_3_11_5", "OTHER", "NOT_OBSERVED"}:
        raise ContractError("child version code changed")
    if value["platform_code"] not in {"DARWIN_ARM64", "OTHER", "NOT_OBSERVED"}:
        raise ContractError("child platform code changed")
    for name in CHILD_OBSERVATION_FIELDS:
        if name in {
            "schema",
            "request_sha256",
            "profile_id",
            "outcome",
            "failure_code",
            "implementation_code",
            "version_code",
            "platform_code",
            "hash_probe_sha256",
            "requested_environment_key_count",
            "effective_environment_key_count",
            "dyld_key_count",
            "credential_key_count",
            "observation_sha256",
        }:
            continue
        _require_bool(value, name)
    for name in (
        "requested_environment_key_count",
        "effective_environment_key_count",
        "dyld_key_count",
        "credential_key_count",
    ):
        _require_int(value, name)
    if value["requested_environment_key_count"] != len(REQUESTED_ENVIRONMENT):
        raise ContractError("requested environment policy count changed")
    if (
        value["effective_environment_key_count"] > 128
        or value["dyld_key_count"] > value["effective_environment_key_count"]
        or value["credential_key_count"] > value["effective_environment_key_count"]
    ):
        raise ContractError("child environment counts are inconsistent")
    success = value["outcome"] == "PASS"
    if success:
        if value["requested_environment_key_count"] != len(REQUESTED_ENVIRONMENT):
            raise ContractError("passing requested environment count changed")
        if value["effective_environment_key_count"] != len(REQUESTED_ENVIRONMENT) + 1:
            raise ContractError("passing effective environment count changed")
        required_true = (
            "direct_file_main",
            "spec_is_none",
            "python_argv_exact",
            "native_argv_exact",
            "cwd_exact",
            "requested_environment_exact_after_normalization",
            "darwin_injected_key_present",
            "darwin_injected_value_matches_uid",
            "darwin_injected_removed_before_observation",
            "uid_euid_equal",
            "gid_egid_equal",
            "nonprivileged_identity",
            "supplemental_root_group_absent",
            "process_taint_absent",
            "venv_executable_exact",
            "interpreter_realpath_exact",
            "python_flags_exact",
            "hash_randomization_disabled",
            "hash_probe_matches_prefrozen_reference",
            "sys_path_exact",
            "system_only_sys_path",
            "pythonpath_absent",
            "pythonhome_absent",
        )
        if any(value[name] is not True for name in required_true):
            raise ContractError("passing child observation has a false gate")
        if (
            value["implementation_code"] != "CPYTHON"
            or value["version_code"] != "CPYTHON_3_11_5"
            or value["platform_code"] != "DARWIN_ARM64"
            or value["hash_probe_sha256"] != HASH_PROBE_SHA256
            or value["dyld_key_count"] != 0
            or value["credential_key_count"] != 0
        ):
            raise ContractError("passing child profile changed")
        if any(
            value[name] is not False
            for name in (
                "site_imported",
                "entropy_contacted",
                "network_contacted",
                "scientific_imports_performed",
                "workspace_write_performed",
                "temporary_write_performed",
                "raw_environment_emitted",
                "raw_identity_emitted",
            )
        ):
            raise ContractError("passing child has a forbidden effect")
    expected_failure = _child_failure_code(value)
    if value["failure_code"] != expected_failure or success != (
        expected_failure == "NONE"
    ):
        raise ContractError("child failure priority changed")
    _validate_terminal(
        value,
        "observation_sha256",
        CHILD_OBSERVATION_DOMAIN,
        "child observation",
    )
    return value


def finish_child_observation(record: Mapping[str, Any]) -> Dict[str, Any]:
    return validate_child_observation(
        _finish(record, "observation_sha256", CHILD_OBSERVATION_DOMAIN)
    )


def _result_failure_code(value: Mapping[str, Any]) -> str:
    supervisor_gates = (
        "supervisor_direct_file_main",
        "supervisor_spec_is_none",
        "supervisor_python_argv_exact",
        "supervisor_native_argv_exact",
        "supervisor_environment_exact_after_normalization",
        "supervisor_python_flags_exact",
        "supervisor_cwd_exact",
        "supervisor_profile_exact",
        "parent_environment_observation_passed",
    )
    if any(value[name] is not True for name in supervisor_gates):
        return "SUPERVISOR_BOUNDARY"
    if (
        value["v2_terminal_custody_revalidated_intact_before"] is not True
        or value["v3_marker_absent_before"] is not True
        or value["v3_preparation_root_absent_before"] is not True
        or value["planned_result_absent_before"] is not True
        or value["preflight_snapshot_sha256"] is None
    ):
        return "PROTECTED_CUSTODY"
    if value["child_transport_failure_code"] != "NONE":
        return value["child_transport_failure_code"]
    child = value["child_observation"]
    if child is None:
        return "CHILD_STDOUT"
    if child["outcome"] == "FAIL":
        return child["failure_code"]
    if (
        value["child_environment_observation_passed"] is not True
        or value["parent_child_environment_semantics_match"] is not True
    ):
        return "EFFECTIVE_ENVIRONMENT"
    if (
        value["protected_custody_unchanged"] is not True
        or value["v2_terminal_custody_revalidated_intact_after"] is not True
        or value["v3_marker_absent_after"] is not True
        or value["v3_preparation_root_absent_after"] is not True
        or value["planned_result_absent_after"] is not True
        or value["postflight_snapshot_sha256"] is None
        or value["preflight_snapshot_sha256"] != value["postflight_snapshot_sha256"]
    ):
        return "PROTECTED_CUSTODY"
    effects = (
        ("RUNTIME_APPROVAL_CONTAMINATION", "runtime_approval_created"),
        ("MARKER_AUTHORIZATION_CONTAMINATION", "marker_creation_authorized"),
        ("ENTROPY_CONTACT", "entropy_contacted"),
        ("NETWORK_CONTACT", "network_contacted"),
        ("SCIENTIFIC_IMPORT_OR_EXECUTION", "scientific_execution_performed"),
        ("WORKSPACE_WRITE", "application_workspace_write_performed"),
        ("TEMPORARY_WRITE", "application_temporary_write_performed"),
    )
    for code, name in effects:
        if value[name] is True:
            return code
    return "NONE"


def validate_result(record: Any) -> Dict[str, Any]:
    value = _require_exact_keys(record, RESULT_FIELDS, "result")
    if value["schema"] != RESULT_SCHEMA:
        raise ContractError("result schema changed")
    success = value["outcome"] == "PASS"
    for name in RESULT_FIELDS:
        if name.endswith("_sha256"):
            if name.startswith("child_observation_") and value[name] is None:
                continue
            if (
                name in {"preflight_snapshot_sha256", "postflight_snapshot_sha256"}
                and value[name] is None
                and not success
            ):
                continue
            require_sha256(value[name], name)
    if value["outcome"] not in RESULT_OUTCOMES:
        raise ContractError("result outcome changed")
    if value["failure_code"] not in FAILURE_CODES:
        raise ContractError("result failure code changed")
    if value["child_transport_failure_code"] not in {
        "NONE",
        "CHILD_PROCESS",
        "CHILD_STDERR",
        "CHILD_STDOUT",
        "CHILD_TIMEOUT",
    }:
        raise ContractError("result child transport failure changed")
    if (
        value["child_exit_code"] is not None
        and type(value["child_exit_code"]) is not int
    ):
        raise ContractError("child_exit_code must be null or an exact signed integer")
    for name in (
        "child_stdout_byte_count",
        "child_stderr_byte_count",
        "child_launch_count",
        "retry_count",
    ):
        _require_int(value, name)
    if value["child_launch_count"] not in {0, 1} or value["retry_count"] != 0:
        raise ContractError("result launch or retry count changed")
    if value["protected_snapshot_schema"] != PROTECTED_SNAPSHOT_SCHEMA:
        raise ContractError("protected snapshot schema changed")
    require_sha256(
        value["protected_path_roster_sha256"], "protected_path_roster_sha256"
    )
    for name in RESULT_FIELDS:
        if name.endswith("_performed") or name in {
            "protected_custody_unchanged",
            "parent_environment_observation_passed",
            "child_environment_observation_passed",
            "parent_child_environment_semantics_match",
            "supervisor_direct_file_main",
            "supervisor_spec_is_none",
            "supervisor_python_argv_exact",
            "supervisor_native_argv_exact",
            "supervisor_environment_exact_after_normalization",
            "supervisor_python_flags_exact",
            "supervisor_cwd_exact",
            "supervisor_profile_exact",
            "v2_terminal_custody_revalidated_intact_before",
            "v2_terminal_custody_revalidated_intact_after",
            "v3_marker_absent_before",
            "v3_marker_absent_after",
            "v3_preparation_root_absent_before",
            "v3_preparation_root_absent_after",
            "planned_result_absent_before",
            "planned_result_absent_after",
            "entropy_contacted",
            "network_contacted",
            "runtime_approval_created",
            "marker_creation_authorized",
            "child_exit_observed",
            "mechanical_one_shot_enforced",
            "prepublication_replay_resistance",
        }:
            _require_bool(value, name)
    if (
        value["mechanical_one_shot_enforced"] is not False
        or value["prepublication_replay_resistance"] is not False
    ):
        raise ContractError("procedural one-shot disclosure changed")
    if value["child_launch_count"] == 0:
        if (
            value["child_exit_observed"] is not False
            or value["child_exit_code"] is not None
            or value["child_observation"] is not None
        ):
            raise ContractError("unlaunched child has observed custody")
    elif value["child_exit_observed"] is True and value["child_exit_code"] is None:
        raise ContractError("observed child exit lacks its code")
    if (
        value["child_stdout_byte_count"] > 64 * 1024
        or value["child_stderr_byte_count"] > 4 * 1024
    ):
        raise ContractError("child transport size bound changed")
    transport = value["child_transport_failure_code"]
    if value["child_observation"] is not None and transport != "NONE":
        raise ContractError("typed child observation has a transport failure")
    if transport == "NONE" and (
        value["child_launch_count"] != 1
        or value["child_exit_observed"] is not True
        or value["child_exit_code"] != 0
        or value["child_stderr_byte_count"] != 0
    ):
        raise ContractError("successful child transport custody changed")
    if transport == "CHILD_STDERR" and value["child_stderr_byte_count"] == 0:
        raise ContractError("stderr failure has no stderr bytes")
    if transport == "CHILD_PROCESS" and not (
        value["child_launch_count"] == 0
        or value["child_exit_observed"] is False
        or value["child_exit_code"] != 0
    ):
        raise ContractError("child process failure has no process failure")
    if transport == "CHILD_STDOUT" and (
        value["child_launch_count"] != 1
        or value["child_exit_observed"] is not True
        or value["child_exit_code"] is None
        or value["child_stderr_byte_count"] != 0
    ):
        raise ContractError("child stdout failure transport changed")
    if success and (
        value["child_observation_raw_sha256"] is None
        or value["child_observation_sha256"] is None
        or value["child_observation"] is None
        or value["child_exit_code"] != 0
        or value["child_stderr_byte_count"] != 0
    ):
        raise ContractError("passing result lacks exact child custody")
    if value["child_observation"] is not None:
        checked_child = validate_child_observation(value["child_observation"])
        child_payload = canonical_json(checked_child) + b"\n"
        if (
            value["child_observation_raw_sha256"] != sha256(child_payload)
            or value["child_observation_sha256"] != checked_child["observation_sha256"]
            or checked_child["request_sha256"] != value["request_sha256"]
        ):
            raise ContractError("result child observation custody changed")
        if value["child_stdout_byte_count"] != len(child_payload):
            raise ContractError("result child stdout size changed")
    elif (
        value["child_observation_raw_sha256"] is not None
        or value["child_observation_sha256"] is not None
    ):
        raise ContractError("null child observation has nonnull custody")
    required_true = (
        "protected_custody_unchanged",
        "parent_environment_observation_passed",
        "child_environment_observation_passed",
        "parent_child_environment_semantics_match",
        "supervisor_direct_file_main",
        "supervisor_spec_is_none",
        "supervisor_python_argv_exact",
        "supervisor_native_argv_exact",
        "supervisor_environment_exact_after_normalization",
        "supervisor_python_flags_exact",
        "supervisor_cwd_exact",
        "supervisor_profile_exact",
        "v2_terminal_custody_revalidated_intact_before",
        "v2_terminal_custody_revalidated_intact_after",
        "v3_marker_absent_before",
        "v3_marker_absent_after",
        "v3_preparation_root_absent_before",
        "v3_preparation_root_absent_after",
        "planned_result_absent_before",
        "planned_result_absent_after",
    )
    required_false = (
        "application_workspace_write_performed",
        "application_temporary_write_performed",
        "entropy_contacted",
        "network_contacted",
        "scientific_execution_performed",
        "runtime_approval_created",
        "marker_creation_authorized",
    )
    if success and (
        any(value[name] is not True for name in required_true)
        or value["preflight_snapshot_sha256"] != value["postflight_snapshot_sha256"]
        or value["child_observation"]["outcome"] != "PASS"
        or any(value[name] is not False for name in required_false)
    ):
        raise ContractError("passing result custody gate changed")
    expected_failure = _result_failure_code(value)
    if value["failure_code"] != expected_failure or success != (
        expected_failure == "NONE"
    ):
        raise ContractError("result failure priority changed")
    _validate_terminal(value, "result_sha256", RESULT_DOMAIN, "result")
    return value


def finish_result(record: Mapping[str, Any]) -> Dict[str, Any]:
    return validate_result(_finish(record, "result_sha256", RESULT_DOMAIN))


def parse_canonical(payload: bytes, kind: str) -> Dict[str, Any]:
    if type(payload) is not bytes or not payload.endswith(b"\n"):
        raise ContractError("record must be exact bytes ending in one LF")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("record is not canonical ASCII JSON") from error
    if canonical_json(value) + b"\n" != payload:
        raise ContractError("record is not canonical ASCII JSON plus LF")
    validators = {
        "REQUEST": validate_request,
        "CHILD_OBSERVATION": validate_child_observation,
        "RESULT": validate_result,
    }
    if kind not in validators:
        raise ContractError("unknown V3 rehearsal contract")
    return validators[kind](value)


def environment_policy() -> Dict[str, Any]:
    body = {
        "schema": (
            "heterodiff-a1-r1-activation-preparation-v3-live-host-"
            "environment-policy-v1"
        ),
        "profile_id": PROFILE_ID,
        "requested_environment": dict(REQUESTED_ENVIRONMENT),
        "requested_environment_key_count": len(REQUESTED_ENVIRONMENT),
        "darwin_injected_environment_key": DARWIN_INJECTED_ENVIRONMENT_KEY,
        "darwin_value_derivation": "0x%X:0x0:0x0 % os.getuid()",
        "darwin_value_emission_permitted": False,
        "raw_uid_or_gid_emission_permitted": False,
        "python_flags": list(PYTHON_FLAGS),
        "isolated_or_ignore_environment_flag_permitted": False,
        "pythonhashseed_honored": True,
        "expected_hash_probe_sha256": HASH_PROBE_SHA256,
        "forbidden_environment_keys": list(FORBIDDEN_ENVIRONMENT_KEYS),
        "forbidden_environment_prefixes": list(FORBIDDEN_ENVIRONMENT_PREFIXES),
        "site_import_permitted": False,
        "network_contact_permitted": False,
        "scientific_import_permitted": False,
        "application_write_permitted": False,
    }
    return {
        **body,
        "policy_sha256": sha256(
            b"heterodiff-a1-r1-activation-preparation-v3-environment-policy-v1\0"
            + canonical_json(body)
        ),
    }


__all__ = [
    "CHILD_OBSERVATION_DOMAIN",
    "CHILD_OBSERVATION_FIELDS",
    "CHILD_OBSERVATION_SCHEMA",
    "ContractError",
    "DARWIN_INJECTED_ENVIRONMENT_KEY",
    "EXPECTED_SYS_PATH",
    "FAILURE_CODES",
    "FORBIDDEN_ENVIRONMENT_KEYS",
    "FORBIDDEN_ENVIRONMENT_PREFIXES",
    "HASH_PROBE_PREIMAGE",
    "HASH_PROBE_SHA256",
    "HASH_PROBE_STRINGS",
    "HASH_PROBE_VALUES",
    "PROFILE_ID",
    "PLANNED_RESULT_RELATIVE_PATH",
    "PROTECTED_SNAPSHOT_SCHEMA",
    "PYTHON_FLAGS",
    "PYTHON_REALPATH",
    "PYTHON_RELATIVE_PATH",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_SCHEMA",
    "REQUESTED_ENVIRONMENT",
    "REQUESTED_ENVIRONMENT_SHA256",
    "REQUEST_DOMAIN",
    "REQUEST_FIELDS",
    "REQUEST_SCHEMA",
    "RESULT_DOMAIN",
    "RESULT_FIELDS",
    "RESULT_SCHEMA",
    "FUTURE_V3_MARKER_RELATIVE_PATH",
    "FUTURE_V3_PREPARATION_ROOT_RELATIVE_PATH",
    "V2_TERMINAL_REGISTRATION_RECORD_SHA256",
    "canonical_json",
    "environment_policy",
    "finish_child_observation",
    "finish_request",
    "finish_result",
    "parse_canonical",
    "require_sha256",
    "sha256",
    "validate_child_observation",
    "validate_request",
    "validate_result",
]
