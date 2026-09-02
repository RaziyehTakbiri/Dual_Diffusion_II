#!/usr/bin/env python3
"""Read-only custody validator for the Test-29/Test-30 macrostep precursor."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


SCHEMA = (
    "heterodiff-manuscript-v3-formal-test29-test30-single-macrostep-"
    "integration-qualification-v1"
)
REPORTED_DATE = "2026-08-31"
STATE = (
    "SYNTHETIC_SUPPLIED_INPUT_SINGLE_MACROSTEP_LEFT_JUMP_RIGHT_INTEGRATION_VALIDATED"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"

ROOT = Path(__file__).resolve().parents[2]
HUMAN_PATH = (
    "PROJECT_FORMAL_TEST29_TEST30_SINGLE_MACROSTEP_INTEGRATION_QUALIFICATION.md"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.py"
)
SOURCE_PATH = (
    "src/heterodiff/evaluation/" "formal_test29_test30_single_macrostep_integration.py"
)
SPEC_PATH = "manuscript_v3/executable_method_spec.md"

TEST29_SOURCE_PATH = (
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py"
)
TEST29_HUMAN_PATH = "PROJECT_FORMAL_TEST29_FINITE_ACYCLIC_ROUTE_QUALIFICATION.md"
TEST29_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json"
)
TEST29_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.py"
)
TEST29_TEST_PATH = "tests/unit/test_formal_test29_finite_acyclic_route_oracle.py"

TEST30_SOURCE_PATH = (
    "src/heterodiff/evaluation/" "formal_test30_synthetic_coupled_path_qualification.py"
)
TEST30_HUMAN_PATH = "PROJECT_FORMAL_TEST30_SYNTHETIC_COUPLED_PATH_QUALIFICATION.md"
TEST30_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json"
)
TEST30_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py"
)
TEST30_TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py"
)

EXPECTED_SOURCE_SHA256 = (
    "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7"
)
EXPECTED_SPEC_SHA256 = (
    "58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d"
)
PARENT_EXPECTED_SHA256 = {
    TEST29_SOURCE_PATH: (
        "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089"
    ),
    TEST29_HUMAN_PATH: (
        "4dfc775e04708d800ab7cbbb2241e0399e11f1f5edccac41da15ae186c067c05"
    ),
    TEST29_MACHINE_PATH: (
        "79fb7722a9007d18d0fe6f0c7f00026b37170930b87686e910d472b28e54b2b9"
    ),
    TEST29_VALIDATOR_PATH: (
        "b962f9b9fcc957e1a25590d341f4fc0b9889fd041757d9c623b36d4fca300905"
    ),
    TEST29_TEST_PATH: (
        "6f9fc2576958992c5688123228128f2f56cecc47b4e8bc2de3b238e510d1662d"
    ),
    TEST30_SOURCE_PATH: (
        "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0"
    ),
    TEST30_HUMAN_PATH: (
        "7a6978be9d7f453adebb2d7ea1464523b7b43df8027138d18c744a2add0140d4"
    ),
    TEST30_MACHINE_PATH: (
        "03b6ff21dedc065a3385f403f7631ee89023bd9572d5793405fa2d8492cb7cb5"
    ),
    TEST30_VALIDATOR_PATH: (
        "7319bc6de7ec32b65aed81af64d027f639b0b9c91fe3534b853fe42c8429758b"
    ),
    TEST30_TEST_PATH: (
        "7d0b18f0d1470e6cacc44918e078b6122b5822cb7080e544507c5c0e8b19efef"
    ),
}
PARENT_PATHS = tuple(PARENT_EXPECTED_SHA256)
PACKAGE_PATHS = (SOURCE_PATH, HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)
ALL_CUSTODY_PATHS = PACKAGE_PATHS + PARENT_PATHS + (SPEC_PATH,)

TEST29_RECORD_SHA256 = (
    "6c443bf95161371536b6f3f395a4a2328c70d0f83d4e254f54e699e31e07797d"
)
TEST30_RECORD_SHA256 = (
    "f70ccc081c029939b8b150a00c5ad776bd58a4081c37af5b1d2fccb4be698fbe"
)
AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
AUTHORITY_SHA256 = "44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a"
CONTROL_PREDICATE = STATE


class ValidationError(RuntimeError):
    """Raised when the immutable package or its exact receipt differs."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def record_sha256(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("machine schema must be exact ASCII text")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_payload_bytes(payload))


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


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
    parts = relative_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValidationError("unsafe relative path: " + relative_path)
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts:
        raise ValidationError("unsafe relative path: " + relative_path)
    result = root.joinpath(*pure.parts)
    if result == root or root not in result.parents:
        raise ValidationError("relative path escaped workspace")
    return result


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows = []
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


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
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
        chunks = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("file changed during stable read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during stable read")
    raw = b"".join(chunks)
    if len(raw) != after_fd.st_size:
        raise ValidationError("short stable read: " + relative_path)
    return raw


def _require_hard_pinned_sha256(
    raw: bytes, *, relative_path: str, expected_sha256: str
) -> bytes:
    if _sha256(raw) != expected_sha256:
        raise ValidationError(
            "hard-pinned SHA-256 differs before source execution: " + relative_path
        )
    return raw


def _stable_read_hard_pinned(
    root: Path, relative_path: str, expected_sha256: str
) -> bytes:
    return _require_hard_pinned_sha256(
        _stable_read(root, relative_path),
        relative_path=relative_path,
        expected_sha256=expected_sha256,
    )


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    expected_symbols: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    row = {
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
    return row


def _source_safety(source_raw: bytes) -> Dict[str, Any]:
    try:
        text = source_raw.decode("utf-8")
        tree = ast.parse(text, filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("composite source is not valid UTF-8 Python") from error
    allowed_roots = {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "types",
        "typing",
    }
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            root_name = name.split(".", 1)[0]
            if root_name not in allowed_roots:
                raise ValidationError(
                    "composite source imports forbidden module: " + name
                )
            imports.append(name)
    banned_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "input",
        "system",
        "popen",
        "remove",
        "unlink",
        "rename",
        "write",
        "write_text",
        "write_bytes",
    }
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = ""
        if name in banned_calls:
            raise ValidationError("composite source contains forbidden call: " + name)
        if name:
            calls.append(name)
    required_tokens = (
        CONTROL_PREDICATE,
        "FROZEN_LOW_WORD_COUNT = 16",
        "run_addressed_acyclic_fixture",
        "midpoint_representative",
        "_heun_half",
        "test28_initializer_admissible=False",
        "continuous_gaussian_destination_sampled=False",
        "formal_test29_closed=False",
        "tracker_files_edited=0",
        "NO_ARBITRARY_PARENT_MODULE_AUTHENTICATION",
        "recompute_single_macrostep_report_sha256",
        "validate_single_macrostep_result",
        "recompute_frozen_single_macrostep_qualification_report_sha256",
        "validate_frozen_single_macrostep_qualification",
        "_execute_single_macrostep_core",
        "_execute_frozen_single_macrostep_qualification_core",
        "_strict_compare_dataclass_fields",
    )
    for token in required_tokens:
        if token not in text:
            raise ValidationError("composite source lacks scope token: " + token)
    return {
        "ast_parsed": True,
        "allowed_import_roots": sorted(allowed_roots),
        "observed_import_count": len(imports),
        "observed_call_count": len(calls),
        "filesystem_write_call_present": False,
        "rng_or_entropy_import_present": False,
        "network_import_present": False,
        "subprocess_import_present": False,
        "project_import_present": False,
        "tracker_mutation_present": False,
    }


def _load_verified_module(
    source_raw: bytes,
    *,
    logical_path: str,
    expected_sha256: str,
    module_stem: str,
    inspect_composite_safety: bool,
) -> ModuleType:
    """Compile and execute only the supplied stable-read, hard-pinned bytes."""

    _require_hard_pinned_sha256(
        source_raw,
        relative_path=logical_path,
        expected_sha256=expected_sha256,
    )
    if inspect_composite_safety:
        _source_safety(source_raw)
    digest = _sha256(source_raw)
    module_name = "_" + module_stem + "_validation_" + digest[:16]
    module = ModuleType(module_name)
    module.__file__ = logical_path
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    code = compile(
        source_raw,
        logical_path,
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
    return module


def _verify_parent_machine(
    raw: bytes, *, schema: str, state: str, record_digest: str
) -> Dict[str, Any]:
    try:
        record = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("parent machine record is not ASCII JSON") from error
    if type(record) is not dict:
        raise ValidationError("parent machine root is not an object")
    expected = {
        "schema_version": schema,
        "state": state,
        "record_sha256": record_digest,
    }
    actual = {key: record.get(key) for key in expected}
    _strict_equal(actual, expected, "parent_machine_identity")
    return expected


def _qualification_receipt(
    composite: ModuleType, test29: ModuleType, test30: ModuleType
) -> Dict[str, Any]:
    result = composite.run_frozen_single_macrostep_qualification(test29, test30)
    if type(result) is not composite.FrozenSingleMacrostepQualification:
        raise ValidationError("composite returned another qualification type")
    if (
        composite.validate_frozen_single_macrostep_qualification(test29, test30, result)
        is not result
    ):
        raise ValidationError("composite qualification validator changed identity")
    if (
        composite.recompute_frozen_single_macrostep_qualification_report_sha256(result)
        != result.report_sha256
    ):
        raise ValidationError("composite qualification digest recomputation differs")
    expected = {
        "schema_version": "heterodiff-test29-test30-single-macrostep-integration-v1",
        "predicate": CONTROL_PREDICATE,
        "scope": (
            "DETERMINISTIC_TEST30_INITIAL_STATE;SUPPLIED_CP23_SHAPED_PHYSICAL_"
            "HALF_INCREMENTS;ONE_SUPPLIED_CP24_SHAPED_TEST29_WORD;ONE_FINITE_"
            "ACYCLIC_CENTRAL_EDIT;LEFT_HEUN_THEN_JUMP_THEN_RIGHT_HEUN;LOW_WORD_"
            "EXHAUSTION"
        ),
        "strict_nonclaims": (
            "NO_TEST28_INITIALIZER_OR_ADMISSION;NO_LIVE_CP23_OR_CP24_STREAM;"
            "NO_BROWNIAN_GAUSSIAN_OR_INDEPENDENCE_LAW;NO_CONTINUOUS_GAUSSIAN_"
            "DESTINATION;NO_WAITING_CLOCK_ACCEPTANCE_THINNING_OR_JUMP_SUBSTEP_"
            "LAW;NO_GENERAL_STRANG_PATH_OR_STEP_HALVING;NO_FORMAL_TEST_CLOSURE;"
            "NO_SCIENTIFIC_EXECUTION_OR_TRACKER_EFFECT;"
            "NO_ARBITRARY_PARENT_MODULE_AUTHENTICATION"
        ),
        "failure_policy": "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_PARTIAL_RESULT",
        "low_word_cases_checked": 16,
        "route_family_counts": [["birth", 8], ["death", 4], ["replacement", 4]],
        "final_cardinality_counts": [[1, 4], [2, 4], [3, 8]],
        "source_serial_counts": [[1, 4], [2, 4]],
        "normal_cell_counts": [[0, 6], [1, 6]],
        "distinct_input_sha256_count": 16,
        "distinct_report_sha256_count": 16,
        "case_input_sha256s": [
            "1bb4bd2d52c887816e29788402fba18b6b35dffb20ee35a7511f313e622e2827",
            "5fa34b217984020253e31bf378d1c64ee58fc0cf99975798eb5967994845bef5",
            "9593712e78babf05ce8f8b4f2faf4d255d890ce8c519023038e5af1b8e17ff14",
            "51c971f7a3ada33ed00b94545567ee3ddeca7ebed33f18e5068bc1c0911e7cc8",
            "689ed24af8b1741d49475661b75f437fd8d26f37be2b48670b0c57b80c1d7eb7",
            "2640e004a029091aa6c66ed5365e346522b79d511772b5c8979a8c31c50c935f",
            "65720a71500971810e1d3cc1b5e686b3261cee6a111c15595f359500c8be91b5",
            "19b9214a8a031c26c1cf3ddf0078e4a75cacbf36777a424f60e13904cecd9c75",
            "d0e43934b8d71a63a8f4508b69bebf75dbe4513fe10293fb2b08c262cdeab122",
            "4bbcf84d6e9be1b41551343dd49d8b0ccc969880014470658d65718afda9dcee",
            "a5ff880a762417e80c2126cea3fc6991e730dda165e9b96803f17aee1cb75a3d",
            "4c7d0c9fe1583b4cbd34d89e060aa4e2183949314eaed41df4c7a65bfe023e12",
            "5100945ba69d01ee968959c624c5597a2d5ffe9aca33c0a424dd66c6936e2211",
            "a30ce739f13325e1437c00853535360f5a87531db696cfec6b5c9bec9a521f7d",
            "3af59eeb1658768e09b4a30b43daece9ce60feb9233c144ffb88fdf890fa10e5",
            "844433af43454c7a611b62e787381daea68b4cf847e56201b3584b4f9df0f87d",
        ],
        "case_report_sha256s": [
            "fde29ca1d76163c1a07d22d7d11f5e63cc1ab2a88f1f2d891c60aa994746416a",
            "3b72f544c3e29d29367b9b7f65ba8f80c1972d54235b3ecc18caab23622108ef",
            "870861f8dd42b7ba16032c2ed37561acdefd9e7ccab0baf197ba7f73c6354b5b",
            "ad92a5d4c41e013e8f651cde8040f52c61477304e95d21f29267b8ef3f7025af",
            "acc209ea62f7e6b86b3538f8d5fac992be7ae8ee591b1b7173cee8f4a39df2f7",
            "f871041036fb81506e03e8a2e3aa92bd7258700e3da046b4c1f110a3ac7b607f",
            "fd52f6851a5e09a3207dcdead80f632e8cc11bf6a7acd3b7bb3641f3cdb01430",
            "de54628ea10efe3d536538174ecc5798aa117fb31b283a7c22df1b340611fbc4",
            "78b3b4d0c7ad8affc838c84fae0a2a0224723c6871b898683a8159c4bc28e117",
            "9729f24a62df32c01d54550ac85653640f9c0a3e701be3c2f88da47dc754fee6",
            "8263fc90115c0ddaaf16526740cef357219b090164efafd7e2d582b5f03c9962",
            "86774da459af02a585ea9ff5db60653cb78e77d050a64caef33a870b14601f68",
            "7d8577aee492d7d08e589f6dc0617075040f25c91522196587b2d190f87edd7a",
            "5d8f8935a1aad693a965f998d93c166ab440fd2b1260434b0b29a47b209a42f2",
            "b9dd27bca465fd203ba6e01adb0bdd9e96e36dd993e604c099ca13bc3493530b",
            "a2a3e6030b2416fc4595c426e96b6e97df7bd867bf8022a289428a119aa2aaae",
        ],
        "every_case_one_left_jump_right_macrostep": True,
        "every_case_address_unique": True,
        "every_case_lineage_matches_test29": True,
        "birth_death_replacement_all_covered": True,
        "no_effect_claim_scoped_to_validator_admitted_parents": True,
        "arbitrary_parent_modules_authenticated": False,
        "test28_initializer_admissible": False,
        "live_parent_stream_consumed": False,
        "continuous_gaussian_destination_sampled": False,
        "general_strang_path_integrated": False,
        "formal_tests_closed": 0,
        "fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "tracker_files_edited": 0,
        "passed": True,
        "report_sha256": (
            "ccf2639c539d312463209bd165cc288df1ba77518f1d31aa7e616df18b66455f"
        ),
    }
    pair_tuple_fields = {
        "route_family_counts",
        "final_cardinality_counts",
        "source_serial_counts",
        "normal_cell_counts",
    }
    actual = {
        key: [list(row) for row in getattr(result, key)]
        if key in pair_tuple_fields
        else list(getattr(result, key))
        if key in {"case_input_sha256s", "case_report_sha256s"}
        else getattr(result, key)
        for key in expected
    }
    _strict_equal(actual, expected, "qualification_receipt")
    return expected


def _case_receipt(
    composite: ModuleType, test29: ModuleType, test30: ModuleType
) -> Dict[str, Any]:
    supplied = composite.build_frozen_single_macrostep_input(test29, test30, 2)
    result = composite.run_supplied_single_macrostep(test29, test30, supplied)
    if type(result) is not composite.SingleMacrostepResult:
        raise ValidationError("composite returned another case-result type")
    if (
        composite.validate_single_macrostep_result(
            test29,
            test30,
            supplied,
            result,
        )
        is not result
    ):
        raise ValidationError("composite case validator changed identity")
    if (
        composite.recompute_single_macrostep_report_sha256(result)
        != result.report_sha256
    ):
        raise ValidationError("composite case digest recomputation differs")

    def snapshot(value: Tuple[Tuple[int, str, float], ...]):
        return [
            {"serial": serial, "kind": kind, "coordinate_hex": coordinate.hex()}
            for serial, kind, coordinate in value
        ]

    expected = {
        "schema_version": "heterodiff-test29-test30-single-macrostep-integration-v1",
        "predicate": CONTROL_PREDICATE,
        "scope": (
            "DETERMINISTIC_TEST30_INITIAL_STATE;SUPPLIED_CP23_SHAPED_PHYSICAL_"
            "HALF_INCREMENTS;ONE_SUPPLIED_CP24_SHAPED_TEST29_WORD;ONE_FINITE_"
            "ACYCLIC_CENTRAL_EDIT;LEFT_HEUN_THEN_JUMP_THEN_RIGHT_HEUN;LOW_WORD_"
            "EXHAUSTION"
        ),
        "strict_nonclaims": (
            "NO_TEST28_INITIALIZER_OR_ADMISSION;NO_LIVE_CP23_OR_CP24_STREAM;"
            "NO_BROWNIAN_GAUSSIAN_OR_INDEPENDENCE_LAW;NO_CONTINUOUS_GAUSSIAN_"
            "DESTINATION;NO_WAITING_CLOCK_ACCEPTANCE_THINNING_OR_JUMP_SUBSTEP_"
            "LAW;NO_GENERAL_STRANG_PATH_OR_STEP_HALVING;NO_FORMAL_TEST_CLOSURE;"
            "NO_SCIENTIFIC_EXECUTION_OR_TRACKER_EFFECT;"
            "NO_ARBITRARY_PARENT_MODULE_AUTHENTICATION"
        ),
        "failure_policy": "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_PARTIAL_RESULT",
        "raw64_word": 2,
        "run_id": 29030,
        "step_index": 0,
        "macrostep_width_hex": "0x1.0000000000000p-2",
        "input_sha256": (
            "9593712e78babf05ce8f8b4f2faf4d255d890ce8c519023038e5af1b8e17ff14"
        ),
        "report_sha256": (
            "870861f8dd42b7ba16032c2ed37561acdefd9e7ccab0baf197ba7f73c6354b5b"
        ),
        "route_id": "macro-replacement",
        "family": "replacement",
        "source_index": 0,
        "source_serial": 1,
        "created_serial": 3,
        "normal_cell_indices": [0],
        "state_before": [
            {"serial": 1, "kind": "A", "coordinate_hex": "0x1.8000000000000p-1"},
            {"serial": 2, "kind": "B", "coordinate_hex": "-0x1.999999999999ap-2"},
        ],
        "state_after_left": [
            {"serial": 1, "kind": "A", "coordinate_hex": "0x1.4a24dd2f1a9fcp-1"},
            {"serial": 2, "kind": "B", "coordinate_hex": "-0x1.8cbf7ced91688p-2"},
        ],
        "state_after_jump": [
            {"serial": 2, "kind": "B", "coordinate_hex": "-0x1.8cbf7ced91688p-2"},
            {"serial": 3, "kind": "B", "coordinate_hex": "-0x1.d956b87528a49p-1"},
        ],
        "state_after_right": [
            {"serial": 2, "kind": "B", "coordinate_hex": "-0x1.3788069d7342fp-2"},
            {"serial": 3, "kind": "B", "coordinate_hex": "-0x1.c8af0124cbbe0p-1"},
        ],
        "left_heun_application_count": 2,
        "central_jump_count": 1,
        "right_heun_application_count": 2,
        "address_count": 5,
        "address_identities_unique": True,
        "lineage_matches_test29": True,
        "destination_is_normal_cell_midpoint_only": True,
        "no_effect_claim_scoped_to_validator_admitted_parents": True,
        "arbitrary_parent_modules_authenticated": False,
        "test28_initializer_admissible": False,
        "live_cp23_stream_consumed": False,
        "live_cp24_stream_consumed": False,
        "continuous_gaussian_destination_sampled": False,
        "waiting_clock_or_acceptance_thinning_executed": False,
        "general_strang_path_integrated": False,
        "formal_test28_closed": False,
        "formal_test29_closed": False,
        "formal_test30_closed": False,
        "passed": True,
    }
    actual = {}
    for key in expected:
        if key == "raw64_word":
            actual[key] = supplied.central_word.raw64_word
        elif key == "macrostep_width_hex":
            actual[key] = result.macrostep_width.hex()
        elif key == "normal_cell_indices":
            actual[key] = list(result.normal_cell_indices)
        elif key.startswith("state_"):
            actual[key] = snapshot(getattr(result, key))
        else:
            actual[key] = getattr(result, key)
    _strict_equal(actual, expected, "case_receipt")
    return expected


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    base = ROOT if root is None else Path(root).resolve()
    human = _stable_read(base, HUMAN_PATH)
    validator = _stable_read(base, VALIDATOR_PATH)
    hostile_test = _stable_read(base, TEST_PATH)

    # Every immutable input pin is checked before any source payload executes.
    source = _stable_read_hard_pinned(base, SOURCE_PATH, EXPECTED_SOURCE_SHA256)
    spec = _stable_read_hard_pinned(base, SPEC_PATH, EXPECTED_SPEC_SHA256)
    parent_raw = {
        path: _stable_read_hard_pinned(base, path, digest)
        for path, digest in PARENT_EXPECTED_SHA256.items()
    }
    test29_machine_identity = _verify_parent_machine(
        parent_raw[TEST29_MACHINE_PATH],
        schema="heterodiff-manuscript-v3-formal-test29-finite-acyclic-route-v1",
        state="FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED",
        record_digest=TEST29_RECORD_SHA256,
    )
    test30_machine_identity = _verify_parent_machine(
        parent_raw[TEST30_MACHINE_PATH],
        schema=(
            "heterodiff-manuscript-v3-formal-test30-synthetic-coupled-path-"
            "qualification-v1"
        ),
        state="SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED",
        record_digest=TEST30_RECORD_SHA256,
    )
    safety = _source_safety(source)
    test29_module = _load_verified_module(
        parent_raw[TEST29_SOURCE_PATH],
        logical_path=TEST29_SOURCE_PATH,
        expected_sha256=PARENT_EXPECTED_SHA256[TEST29_SOURCE_PATH],
        module_stem="test29_parent",
        inspect_composite_safety=False,
    )
    test30_module = _load_verified_module(
        parent_raw[TEST30_SOURCE_PATH],
        logical_path=TEST30_SOURCE_PATH,
        expected_sha256=PARENT_EXPECTED_SHA256[TEST30_SOURCE_PATH],
        module_stem="test30_parent",
        inspect_composite_safety=False,
    )
    composite_module = _load_verified_module(
        source,
        logical_path=SOURCE_PATH,
        expected_sha256=EXPECTED_SOURCE_SHA256,
        module_stem="test29_test30_composite",
        inspect_composite_safety=True,
    )
    qualification = _qualification_receipt(
        composite_module, test29_module, test30_module
    )
    case = _case_receipt(composite_module, test29_module, test30_module)
    parent_roles = {
        TEST29_SOURCE_PATH: "TEST29_PURE_SOURCE",
        TEST29_HUMAN_PATH: "TEST29_HUMAN_CONTRACT",
        TEST29_MACHINE_PATH: "TEST29_MACHINE_RECORD",
        TEST29_VALIDATOR_PATH: "TEST29_READ_ONLY_VALIDATOR",
        TEST29_TEST_PATH: "TEST29_CONSOLIDATED_HOSTILE_TEST",
        TEST30_SOURCE_PATH: "TEST30_PURE_SOURCE",
        TEST30_HUMAN_PATH: "TEST30_HUMAN_CONTRACT",
        TEST30_MACHINE_PATH: "TEST30_MACHINE_RECORD",
        TEST30_VALIDATOR_PATH: "TEST30_READ_ONLY_VALIDATOR",
        TEST30_TEST_PATH: "TEST30_CONSOLIDATED_HOSTILE_TEST",
    }
    record = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": (
            "ADDITIVE_PURE_SYNTHETIC_TEST29_TEST30_SINGLE_MACROSTEP_"
            "INTEGRATION_PRECURSOR_NO_SCIENTIFIC_EFFECT"
        ),
        "scope_review": {
            "physical_file_count": 5,
            "pure_source_file_count": 1,
            "evidence_artifact_count": 4,
            "exact_package_roster": list(PACKAGE_PATHS),
            "consolidated_hostile_test": True,
            "unlisted_package_file_present": False,
            "parent_package_count": 2,
            "parent_file_count": 10,
            "method_spec_input_count": 1,
            "hard_pinned_before_execution_count": 12,
        },
        "authority_provenance": {
            "source": "CONVERSATION_VISIBLE_TEXT",
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_utf8_bytes": 207,
            "normalized_visible_text_sha256": AUTHORITY_SHA256,
            "normalization": (
                "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_UNBOUND"
            ),
            "raw_transport_bytes_bound": False,
            "conversation_envelope_bound": False,
            "account_identity_bound": False,
            "cryptographic_user_authentication_claimed": False,
            "continued_bounded_local_project_work_authorized": True,
            "external_contact_or_browsing_authorized": False,
            "data_access_or_download_authorized": False,
            "entropy_or_live_randomness_authorized": False,
            "runtime_approval_authorized": False,
            "scientific_execution_authorized": False,
            "training_authorized": False,
            "claim_promotion_or_submission_authorized": False,
            "tracker_edit_authorized": False,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_audit_required": True,
            "visible_authority_text_permitted_in_derivative": False,
            "conversation_provenance_permitted_in_derivative": False,
            "internal_paths_hashes_or_receipts_permitted_in_derivative": False,
            "account_identity_present": False,
            "absolute_local_paths_present": False,
            "credentials_tokens_cookies_or_secrets_present": False,
            "raw_data_or_test_data_content_present": False,
            "sanitized_method_content_and_unresolved_status_only": True,
        },
        "parent_packages": {
            "test29": {
                "machine_identity": test29_machine_identity,
                "raw_five_file_package_hard_pinned": True,
                "orchestration_reported_independent_audit_go": True,
                "audit_report_cryptographically_attested_by_this_package": False,
                "narrow_predicate": (
                    "FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED"
                ),
                "full_formal_test_after": "OPEN",
            },
            "test30": {
                "machine_identity": test30_machine_identity,
                "raw_five_file_package_hard_pinned": True,
                "orchestration_reported_independent_audit_go": True,
                "audit_report_cryptographically_attested_by_this_package": False,
                "narrow_predicate": (
                    "SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED"
                ),
                "full_formal_test_after": "PENDING",
            },
        },
        "integration_contract": {
            "initial_state_source": "DETERMINISTIC_TEST30_SYNTHETIC_FIXTURE",
            "initial_occurrence_serials": [1, 2],
            "initial_occurrence_kinds": ["A", "B"],
            "test28_initializer_admitted": False,
            "macrostep_width": 0.25,
            "left_heun_duration": 0.125,
            "right_heun_duration": 0.125,
            "left_address_domain_tag": 4,
            "central_address_domain_tag": 6,
            "right_address_domain_tag": 5,
            "brownian_input_semantics": (
                "SUPPLIED_PHYSICAL_HALF_STEP_INCREMENT_DELTA_W_NOT_STANDARDIZED_"
                "NORMAL_Z_NO_SOURCE_LAW"
            ),
            "central_word_count_per_case": 1,
            "central_edit_count_per_case": 1,
            "central_edit_families_covered": ["birth", "death", "replacement"],
            "continuous_coordinate_freeze_at_midpoint": True,
            "destination_semantics": (
                "FINITE_NORMAL_QUANTILE_CELL_MIDPOINT_REPRESENTATIVE_NOT_"
                "CONTINUOUS_GAUSSIAN_DRAW"
            ),
            "post_edit_roster_must_equal_test29_lineage": True,
            "pure_central_selection_precedes_right_roster_preflight": True,
            "heun_or_path_arithmetic_before_complete_increment_preflight": False,
            "result_or_source_owned_effect_before_complete_increment_preflight": False,
            "public_parent_boundary_check": (
                "EXACT_MODULE_TYPE_SCHEMA_AND_REQUIRED_SYMBOL_PRESENCE_ONLY"
            ),
            "arbitrary_parent_modules_authenticated": False,
            "no_effect_claim_scoped_to_validator_admitted_hard_pinned_parents": True,
            "case_and_qualification_digests_bind_all_material_fields": True,
            "public_report_recompute_and_validation_surface_present": True,
            "case_validation_requires_supplied_input_and_parent_apis": True,
            "case_validation_reconstructs_with_nonrecursive_core": True,
            "qualification_validation_reruns_sixteen_ordered_canonical_cases": True,
            "semantic_validation_strict_compares_every_field_and_digest": True,
            "digest_recomputation_alone_is_semantic_validation": False,
            "general_jump_substep_law_qualified": False,
            "general_strang_path_qualified": False,
        },
        "qualification_receipt": qualification,
        "case_receipt": case,
        "formal_test_states": {
            "formal_test28_before": "OPEN",
            "formal_test28_after": "OPEN",
            "formal_test29_before": "OPEN",
            "formal_test29_after": "OPEN",
            "formal_test30_before": "PENDING",
            "formal_test30_after": "PENDING",
            "formal_test_state_delta": 0,
        },
        "source_safety": safety,
        "source_execution_custody": {
            "composite_source_sha256": EXPECTED_SOURCE_SHA256,
            "method_spec_sha256": EXPECTED_SPEC_SHA256,
            "parent_expected_sha256": dict(PARENT_EXPECTED_SHA256),
            "hard_pinned_before_any_source_execution": True,
            "all_parent_five_file_pins_checked": True,
            "stable_read_verified_parent_payloads_executed_directly": True,
            "stable_read_verified_composite_payload_executed_directly": True,
            "source_path_reopened_for_execution": False,
            "cached_bytecode_loader_used": False,
            "importlib_path_loader_used": False,
        },
        "source_crosswalk": [
            {
                "ordinal": 0,
                "obligation": "LEFT_SUPPLIED_PHYSICAL_HEUN_HALF_STEP",
                "symbols": ["_validate_increment_roster", "_heun_half"],
                "scope": "EXACT_INITIAL_TEST30_LINEAGE_CP23_TAG4_VALUES",
            },
            {
                "ordinal": 1,
                "obligation": "ONE_FINITE_ACYCLIC_CENTRAL_EDIT",
                "symbols": [
                    "frozen_central_jump_fixture",
                    "run_addressed_acyclic_fixture",
                ],
                "scope": "ONE_CP24_SHAPED_SUPPLIED_WORD_NO_CLOCK_OR_THINNING",
            },
            {
                "ordinal": 2,
                "obligation": "BOUNDED_DESTINATION_AND_TEST29_LINEAGE_MAPPING",
                "symbols": ["_destination_occurrence", "midpoint_representative"],
                "scope": "FINITE_NORMAL_CELL_REPRESENTATIVE_NOT_GAUSSIAN_DRAW",
            },
            {
                "ordinal": 3,
                "obligation": "RIGHT_SUPPLIED_PHYSICAL_HEUN_HALF_STEP",
                "symbols": ["_validate_increment_roster", "_heun_half"],
                "scope": "EXACT_POST_EDIT_TEST29_LINEAGE_CP23_TAG5_VALUES",
            },
            {
                "ordinal": 4,
                "obligation": "LOW_WORD_EXHAUSTION_AND_NONCLOSURE_RECEIPT",
                "symbols": ["run_frozen_single_macrostep_qualification"],
                "scope": "SIXTEEN_LOW_WORD_CASES_COMPONENT_ONLY",
            },
            {
                "ordinal": 5,
                "obligation": "EXACT_RUN_BOUNDARY_REVALIDATION",
                "symbols": [
                    "run_supplied_single_macrostep",
                    "_validate_increment_roster",
                    "_validate_central_word",
                ],
                "scope": (
                    "EXACT_BUILTIN_FIELDS_CANONICAL_RECONSTRUCTION_"
                    "OBJECT_MUTATION_REJECTED"
                ),
            },
            {
                "ordinal": 6,
                "obligation": "COMPLETE_CASE_AND_QUALIFICATION_REPORT_BINDING",
                "symbols": [
                    "recompute_single_macrostep_report_sha256",
                    "validate_single_macrostep_result",
                    "recompute_frozen_single_macrostep_qualification_report_sha256",
                    "validate_frozen_single_macrostep_qualification",
                    "_execute_single_macrostep_core",
                    "_execute_frozen_single_macrostep_qualification_core",
                    "_strict_compare_dataclass_fields",
                ],
                "scope": (
                    "CONTEXT_RECONSTRUCTION_AND_STRICT_COMPARISON_OF_EVERY_"
                    "MATERIAL_IDENTITY_SCOPE_POLICY_STATE_COUNT_CASE_DIGEST_"
                    "FLAG_PROJECT_DELTA_PASS_AND_REPORT_DIGEST_FIELD"
                ),
            },
        ],
        "control_effects": {
            "eligible_new_project_control_after_independent_audit": CONTROL_PREDICATE,
            "eligible_value_after_independent_audit": True,
            "tracker_edited": False,
            "formal_tests_closed": 0,
            "existing_fields_closed": 0,
            "blockers_closed": 0,
            "result_slots_filled": 0,
            "scientific_results_produced": 0,
            "claims_promoted": 0,
            "formal_test28_state": "OPEN",
            "formal_test29_state": "OPEN",
            "formal_test30_state": "PENDING",
        },
        "strict_nonclaims": {
            "test28_initializer_admitted": False,
            "live_cp23_stream_consumed": False,
            "live_cp24_stream_consumed": False,
            "brownian_or_independence_law_certified": False,
            "continuous_gaussian_destination_sampled": False,
            "waiting_clock_acceptance_or_thinning_executed": False,
            "general_strang_path_integrated": False,
            "independent_scientific_recomputation_present": False,
            "formal_test28_closed": False,
            "formal_test29_closed": False,
            "formal_test30_closed": False,
            "tracker_edit_authorized": False,
            "arbitrary_parent_modules_authenticated": False,
            "no_effect_claim_applies_to_arbitrary_parent_modules": False,
        },
        "remaining_gaps": [
            "TEST28_LIVE_INITIALIZER_DISTRIBUTION_ADMISSION_AND_TAG3_COORDINATION",
            "LIVE_CP23_TAG4_TAG5_STREAM_AND_BROWNIAN_SOURCE_LAW",
            "LIVE_CP24_STREAM_AND_WORD_TO_CONTINUOUS_GAUSSIAN_DESTINATION_MAP",
            "WAITING_CLOCK_ACCEPTANCE_THINNING_REJECTION_AND_ZERO_OR_MULTIPLE_EDITS",
            "GENERAL_STRANG_CONFIGURATION_PATH_LEARNED_NATIVE_DRIFT_AND_STEP_HALVING",
            "PRODUCTION_ENDPOINT_EDIT_LAW_THRESHOLDS_AND_INDEPENDENT_RECOMPUTATION",
            "RUNNER_RUNTIME_CUSTODY_SEPARATE_SCIENTIFIC_AUTHORITY_AND_EVIDENCE",
        ],
        "input_bindings": [
            _binding(
                0,
                "EXECUTABLE_METHOD_SPEC_LEFT_JUMP_RIGHT_ORDER",
                SPEC_PATH,
                spec,
                expected_symbols=[
                    "noise stochastic Heun method",
                    "Freeze continuous coordinates and generative time",
                    "second stochastic-Heun",
                ],
            )
        ],
        "parent_bindings": [
            _binding(ordinal, parent_roles[path], path, parent_raw[path])
            for ordinal, path in enumerate(PARENT_PATHS)
        ],
        "package_bindings": [
            _binding(
                0,
                "PURE_SINGLE_MACROSTEP_SOURCE",
                SOURCE_PATH,
                source,
                expected_symbols=[
                    "run_supplied_single_macrostep",
                    "run_frozen_single_macrostep_qualification",
                    "recompute_single_macrostep_report_sha256",
                    "validate_single_macrostep_result",
                    "recompute_frozen_single_macrostep_qualification_report_sha256",
                    "validate_frozen_single_macrostep_qualification",
                ],
            ),
            _binding(1, "HUMAN_CONTRACT", HUMAN_PATH, human),
            _binding(2, "READ_ONLY_VALIDATOR", VALIDATOR_PATH, validator),
            _binding(3, "CONSOLIDATED_HOSTILE_TEST", TEST_PATH, hostile_test),
        ],
        "record_sha256": "0" * 64,
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _require_text_tokens(raw: bytes, tokens: Iterable[str], label: str) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " is not UTF-8") from error
    for token in tokens:
        if token not in text:
            raise ValidationError(label + " lacks token: " + token)


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    base = ROOT if root is None else Path(root).resolve()
    machine_raw = _stable_read(base, MACHINE_PATH)
    try:
        if not machine_raw.endswith(b"\n") or b"\r" in machine_raw:
            raise ValidationError("machine record line ending differs")
        record = json.loads(machine_raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not canonical ASCII JSON") from error
    if type(record) is not dict:
        raise ValidationError("machine record root must be an object")
    if canonical_machine_bytes(record) != machine_raw:
        raise ValidationError("machine record bytes are not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine self-digest differs")
    expected = expected_record(base)
    _strict_equal(record, expected, "record")

    human = _stable_read(base, HUMAN_PATH)
    source = _stable_read_hard_pinned(base, SOURCE_PATH, EXPECTED_SOURCE_SHA256)
    spec = _stable_read_hard_pinned(base, SPEC_PATH, EXPECTED_SPEC_SHA256)
    for path, digest in PARENT_EXPECTED_SHA256.items():
        _stable_read_hard_pinned(base, path, digest)
    _require_text_tokens(
        human,
        (
            AUTHORITY_TEXT,
            CONTROL_PREDICATE,
            "Formal Test 28 remains **OPEN**",
            "Formal Test 29 remains **OPEN**",
            "Formal Test 30 remains **PENDING**",
            "physical Brownian increments",
            "not a continuous Gaussian sample",
            "does not reopen a source path for execution",
            "publication-safe derivative",
        ),
        "human contract",
    )
    _require_text_tokens(
        source,
        (
            CONTROL_PREDICATE,
            "run_supplied_single_macrostep",
            "run_frozen_single_macrostep_qualification",
        ),
        "composite source",
    )
    _require_text_tokens(
        spec,
        (
            "noise stochastic Heun method",
            "Freeze continuous coordinates and generative time",
            "second stochastic-Heun",
        ),
        "executable method spec",
    )
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "eligible_after_independent_audit": True,
        "formal_test28": "OPEN",
        "formal_test29": "OPEN",
        "formal_test30": "PENDING",
        "formal_tests_closed": 0,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "scientific_effect": 0,
        "tracker_files_edited": 0,
        "validation": "PASS",
    }


def main() -> int:
    try:
        status = validate()
    except Exception as error:
        print("FORMAL_TEST29_TEST30_SINGLE_MACROSTEP_VALIDATION_FAIL: " + str(error))
        return 1
    print(
        "FORMAL_TEST29_TEST30_SINGLE_MACROSTEP_VALIDATION_PASS "
        + json.dumps(status, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
