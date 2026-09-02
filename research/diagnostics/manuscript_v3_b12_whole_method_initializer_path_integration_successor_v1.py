#!/usr/bin/env python3
"""Authoritative isolated validator for the initializer-to-path successor.

This validator is intentionally standard-library-only.  It captures a frozen
conservative local source closure with descriptor-relative no-follow reads,
copies only those exact bytes to a private capsule, and runs the candidate in
a fresh ``-I -S -B`` interpreter.  The ordinary candidate API explicitly
remains a non-authoritative development surface.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


SCHEMA_VERSION = (
    "heterodiff-b12-whole-method-initializer-path-successor-record-v1"
)
STATE = "WHOLE_METHOD_BETA_INITIALIZER_PATH_SUCCESSOR_PENDING_INDEPENDENT_REVIEW"
PASS_TOKEN = (
    "PASS_B12_WHOLE_METHOD_INITIALIZER_PATH_SUCCESSOR_PENDING_INDEPENDENT_REVIEW"
)
MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_b12_whole_method_initializer_path_integration_successor_v1.json"
)
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_b12_whole_method_initializer_path_integration_successor_v1.py"
)
HUMAN_REL = "PROJECT_B12_WHOLE_METHOD_INITIALIZER_PATH_INTEGRATION_SUCCESSOR.md"
PRIMARY_REL = (
    "src/heterodiff/evaluation/"
    "b12_whole_method_initializer_path_integration_successor.py"
)
INDEPENDENT_REL = (
    "src/heterodiff/evaluation/"
    "b12_whole_method_initializer_path_integration_recomputation.py"
)
TEST_REL = "tests/unit/test_b12_whole_method_initializer_path_integration_successor.py"
PREDECESSOR_MACHINE_REL = (
    "research/fixtures/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)
PRIMARY_MODULE = (
    "heterodiff.evaluation."
    "b12_whole_method_initializer_path_integration_successor"
)
PROPOSED_TASK = (
    "Produce whole-method beta: initializer, continuous path, jump/edit law, "
    "and sampler integrated."
)
FEATURE_COMPLETE_TASK = "End-to-end method is feature-complete."
EXPECTED_CORE_SHA256 = (
    "73887c5411e8822942c9c37ddbdfb1a485f96ef1a2fce4c4ff56f503b4b9bc8e"
)
EXPECTED_RECEIPT_SHA256 = (
    "7f3af61499f4c618daa38d72e38570c4759c5e146eeeef61bb182b9b4f20e102"
)
EXPECTED_CUSTODY_SHA256 = (
    "037d50b89289979c8b40bc843f14fd47fc0365792c0b12c4315b4132c6e428ca"
)
EXPECTED_SELECTED_CONFIGURATION_SHA256 = (
    "c9450132be2800eddc7e8e36547c49e8b7839e1e282e32f0736b453267b92b06"
)
EXPECTED_STABLE_INITIALIZER_SHA256 = (
    "5bca3f822a6a526fb0775cc7bf422347df7e65227141b4f2c76a462d3d597f85"
)
EXPECTED_TRANSFORM_SHA256 = (
    "72a27a8f315e4a1fa95933fde4fe8711d08bcd1d00766dea80bf50275ebcb5b4"
)
EXPECTED_INITIAL_STATE_SHA256 = (
    "2338839b5c7df9c0845063a4053e6ab40d16132f232713ef515d5599d728f05f"
)
EXPECTED_PATH_INPUT_SHA256 = (
    "63aa54613cad1b89973bbceb83cab2479f2cacbcd92e8c2b925f1ff34912f9a4"
)
EXPECTED_PATH_REPORT_SHA256 = (
    "15b46792946d98a9893ba3b7fe31ff83c483500c45751564c8bfbbe9fb247b81"
)
EXPECTED_SUPPLIED_INPUT_SHA256 = (
    "f7e213442d073f88df73d2b33c21e43add4269a8a45b07714bfbd60b4b4ff971"
)
EXPECTED_PREDECESSOR_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)
EXPECTED_PREDECESSOR_RECORD_SHA256 = (
    "451ef6059fea8cb2f98128c388056bcd82739645a97dfdd56021055744cb04af"
)
TRANSFORM_POLICY_ID = (
    "TEST28-TYPE-PARITY-FIRST-COORDINATE-ZERO-DIM-ZERO-TO-PATH-STATE-V1"
)
MAX_FILE_BYTES = 5_000_000
MAX_CHILD_OUTPUT_BYTES = 1_048_576
CHILD_TIMEOUT_SECONDS = 45


# role, path, exact bytes, raw SHA-256.  The test binding is patched only after
# its focused hostile suite is stable.
EXPECTED_AUTHORED_BINDINGS = (
    (
        "human_candidate",
        HUMAN_REL,
        10167,
        "47e8aefc19513d92937799323907be80b5f77fdc33d44a759a3e56171d86e1b3",
    ),
    (
        "primary_source",
        PRIMARY_REL,
        54992,
        "cca5df6d65a4861d019b709cea6abc9ae14fb91a445a1ed4f6738f1ac3b62f84",
    ),
    (
        "independent_recomputation_source",
        INDEPENDENT_REL,
        32508,
        "5c01fb8a195402cf012a815b92bcec13b86845bc088f8b1152d28aa6153a5f5f",
    ),
    (
        "focused_hostile_tests",
        TEST_REL,
        34686,
        "ccbb166dd26bfa90c5ec5c0ad0181bee1fbd0f52ec3c6198c955dc32c6a580f6",
    ),
)


# Conservative recursive all-branch local closure.  Several cold files are
# copied but deliberately not imported by the minimal-package bootstrap.
SEMANTIC_MANIFEST = (
    ("src/heterodiff/__init__.py", 1387, "26fdc70b2d9f92ad41f740e1963ab409986f391aac2c85c5649379b26164a53e"),
    ("src/heterodiff/artifacts/__init__.py", 668, "9514ee0c1d91f05326ca8cd29695e1fce19a761a8f517d8284ecb0d7ffefd9ef"),
    ("src/heterodiff/artifacts/manifest.py", 25462, "fb4d6b47fff568cd73ff46fb41aff85a5bae0608553595008499a1fe6cf1a012"),
    ("src/heterodiff/evaluation/__init__.py", 1085, "1957eb6081e80a72b26e0ad25cb2cdced7a6e03807a3055ee364c161989f30e1"),
    (INDEPENDENT_REL, 32508, "5c01fb8a195402cf012a815b92bcec13b86845bc088f8b1152d28aa6153a5f5f"),
    (PRIMARY_REL, 54992, "cca5df6d65a4861d019b709cea6abc9ae14fb91a445a1ed4f6738f1ac3b62f84"),
    ("src/heterodiff/evaluation/exact_rational_quadratic_initial_tilt.py", 73232, "87e197085ecee91ddbd78e1dfde3d0eb84797740946f76f1ee26f837d4149313"),
    ("src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py", 61434, "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7"),
    ("src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py", 59285, "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176"),
    ("src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py", 42349, "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0"),
    ("src/heterodiff/evaluation/metric_floor.py", 19602, "85c6a0cd5302dbd3cbc33596be92be7349e88e430bb7e267ba39671be984e4d6"),
    ("src/heterodiff/evaluation/mixed_initializer_test28_atomic_q_oracle.py", 62038, "fdc622fe1fe8faf0d39c90140267e538cdd065aad608ff2c740776a5825692ac"),
    ("src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py", 173666, "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"),
    ("src/heterodiff/events/__init__.py", 1222, "3e4e213835262634f5f795e60dafda08fc3d599a5741088f567215d5406640b9"),
    ("src/heterodiff/events/configuration.py", 16009, "66fdc15a1253be8490ff3a18ca9355344388a7820cf7f74c293372669585c0c4"),
    ("src/heterodiff/events/observations.py", 14142, "bf1377f543f0adbd5d690c61ebff4eff08db73aa47ef7fd4bc516eeb026e0698"),
    ("src/heterodiff/events/schema.py", 18274, "bebe1ac4c106ea58f05ef01568dfceb6ccd6580443baf6e43a8da8ea45cfe3e6"),
    ("src/heterodiff/events/transforms.py", 16464, "0bcd1e09de33c635b347fd7bb38646e32a32227cbd4fe70766a27b41156b16d0"),
    ("src/heterodiff/models/__init__.py", 408, "461f713772ce4b9b0d60a71af7df493708f3f4b335dcd59251aba4c6ad1e3e27"),
    ("src/heterodiff/models/configuration_energy_torch.py", 178324, "355e81ffba2eb2a7cf314f685ac9ea89fc7af6c61e4908a935b6032245879815"),
    ("src/heterodiff/models/configuration_initial_tilt_composer_torch.py", 77031, "b3436037b7e3a0eff00cc06564b18a77026f9024948432259b505a3f4a6b1adc"),
    ("src/heterodiff/models/configuration_residual_torch.py", 60679, "3afc4534f09f2cf41e3a737322c44112620fb9055aa51378c3c326c9c4a2293b"),
    ("src/heterodiff/models/configuration_totalized_jump_residual_torch.py", 66752, "285d320f2a462954db54bd70cafff9266b4e31baf45e1d1276fdf3497b17cfff"),
    ("src/heterodiff/models/reference_config.py", 13685, "9ac1c2d0422467390ce95eccb075f4a55bcdd98b0544577058072c987c17c318"),
    ("src/heterodiff/processes/__init__.py", 573, "7545c78dd49c4544c887442bac6797fc4a34fd8be5664acdf4b88d6f3bc257bf"),
    ("src/heterodiff/processes/arbitrary_rational_uint64_exp_quota.py", 27956, "3985d23337f854e43a6ee766d4d9a0afeed0a60fd9e37855c064c88e7477dde1"),
    ("src/heterodiff/processes/certified_initial_score_provider_v1.py", 88896, "8aecb4ed75d4f88b7d6b0355f2d2c5ddad685d761fe4fbe63359bda672973234"),
    ("src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py", 52186, "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089"),
    ("src/heterodiff/processes/plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py", 109798, "a8164e10239bab6d43a8d8f068cf035d9a4c8b0b29ee233bf5b0af8d75a0684c"),
    ("src/heterodiff/processes/plugin_bridge_sampler.py", 49550, "f6d7357f193651416b68cca9f3365855f520c5a7c2eb876114fc9e286627abc2"),
    ("src/heterodiff/processes/reference/__init__.py", 750, "2a50aebebb6e7c10b5930b84bc5ee8de5db8c50a1fcd12f7b3909765efbea438"),
    ("src/heterodiff/processes/reference/continuous.py", 9650, "d950014e8f2f0442f08e6d74d73876ee873e6f9c3503dfbe923cdaa9eff2b705"),
    ("src/heterodiff/processes/reference/discrete.py", 14225, "524c1411bbd7359fdbb51eed9ccaf928a40387498293a59ca9a267fb5ec16996"),
    ("src/heterodiff/processes/reversible_hybrid_reference.py", 65650, "4cb33ee7e3297b8d405d090fe03420ff45ba6e7cdbac4a85d6d5580027ed370e"),
    ("src/heterodiff/theory/__init__.py", 6156, "7396b7366268fd5c7a4642671440719a2d65b88c178116f16875d9e1f05431a6"),
    ("src/heterodiff/theory/association_observation.py", 151385, "948a0dfcd55b6301cddcc00746cb67a0b5b18b3c8e70433b2f44351e889fe906"),
    ("src/heterodiff/theory/association_operational_guide.py", 48320, "9540a3bce5e865a2f3d35192f55ba72a9574243d959f404e5c500f27c3919d7f"),
    ("src/heterodiff/theory/association_preconditioner.py", 197693, "29e8a37fa1b74a37fc84d5208793e00e9b19674d6988bcfad46ac50613b1148c"),
    ("src/heterodiff/theory/association_totalized_jump_guide.py", 63257, "6b519b59994e763900c3d17fee6d44e8ec793e09db5ecffaffd1e47374fc7dd4"),
    ("src/heterodiff/theory/conditional_bridge.py", 8938, "6cbb6c80a9bf4cc5a32a921a431b651617d6fa79cc7bad6a97ed61eac0b1db7a"),
    ("src/heterodiff/theory/configuration_reference.py", 35567, "725ddc4011e2c6cf15f1810be6fabc404c50bd53333e34ad22bedcdf4d6497da"),
    ("src/heterodiff/theory/exact_reversal.py", 5692, "7f33ba16b953f1186b059ed8fb754ee69579ea3755bdb57577408d6e92b70a80"),
    ("src/heterodiff/theory/finite_atomic_association_bridge.py", 22215, "1c9f8b2c3e53f97870f07d636505e04147f3dfe3f048b03c15f4fd8c2942133c"),
    ("src/heterodiff/theory/finite_atomic_counting.py", 37720, "e9fc4f10a49c36ac2e1d48dca2e9e04586cf81eb7c3f0d6d6a708a43a669bda8"),
    ("src/heterodiff/theory/finite_atomic_overflow_observation.py", 20270, "6aed0aff991daff6fd20e67733bc87e5379d971d4256009d54c2fb76a3cc477e"),
    ("src/heterodiff/theory/finite_atomic_reference_guide.py", 28598, "56cd3cae88f395b082c59c674a45104de45c3311981f86563a114db7fa97a0b7"),
    ("src/heterodiff/theory/finite_bridge_path_control.py", 45529, "1cdb2cf82016ad0979fff3ef7451fe6116904cca772b017e6e605b78b476c502"),
    ("src/heterodiff/theory/finite_bridge_population.py", 25808, "6ebbce521f876436b5229c28f725f7256c013f7a22d81f722b923632e124261e"),
    ("src/heterodiff/theory/finite_state.py", 17818, "50462bba10a441325c06affe72660b53960a7793faa7722b94cd4fa6af434468"),
    ("src/heterodiff/theory/gaussian_particle_bridge.py", 35177, "41e63b43fdb7afa3a2d321ba64a0efb6cba5fe9598a43932a0f5e7daae4a42b0"),
    ("src/heterodiff/theory/immigration_death.py", 23289, "66fff8cfe944abe3df02842490e86b06d16145e3a164684d8106832c35e1204c"),
    ("src/heterodiff/theory/path_kl.py", 15389, "769992c89f151d90c04c66c50cad538bfa859396d8f6737aa6b5e05e39bb173a"),
    ("src/heterodiff/theory/regional_configuration_bridge.py", 46562, "47793fa9e65eea0f45faf491311e67aa206b025f6926cc3766d4055b8d752862"),
    ("src/heterodiff/theory/reverse_energy_objective.py", 76278, "67c5e745e2c6c0efa77aec537a381cf9504fa19508db31692de94fc36ea8cc9d"),
    ("src/heterodiff/theory/singular_schema.py", 25869, "f2bdaee061a2b00eea32896204cab014796e674a7a44be8a1c5ad57459fe94c5"),
    ("src/heterodiff/theory/unordered_association.py", 7866, "8ba24367974abc2289b8245691e80f2fdd4107de5e165324838c9b224d0bdbc4"),
    (PREDECESSOR_MACHINE_REL, 9789, "a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b"),
)

EXPECTED_LOADED_LOCAL_SOURCE_PATHS = (
    "src/heterodiff/artifacts/manifest.py",
    PRIMARY_REL,
    "src/heterodiff/evaluation/exact_rational_quadratic_initial_tilt.py",
    "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
    "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
    "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
    "src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py",
    "src/heterodiff/processes/arbitrary_rational_uint64_exp_quota.py",
    "src/heterodiff/processes/certified_initial_score_provider_v1.py",
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
    "src/heterodiff/processes/plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py",
    "src/heterodiff/theory/configuration_reference.py",
    "src/heterodiff/theory/exact_reversal.py",
    "src/heterodiff/theory/finite_atomic_counting.py",
    "src/heterodiff/theory/finite_state.py",
    "src/heterodiff/theory/path_kl.py",
)


REAL_RESIDUAL_IDS = (
    "B02_REAL_DATA_ACQUISITION", "B03_REAL_DATA_SPLIT_AND_ESCROW",
    "B08_RUNTIME_COMPUTE_ENVELOPE", "B09_REAL_LICENSE_PRIVACY_APPROVALS",
    "F172_PROSPECTIVE_FREEZE_AFTER_TEST_SEAL", "ALL_PREEXECUTION_ARTIFACTS_ACCEPTED",
    "PRIMARY_64_DIMENSION_CONTEXT_ENCODER", "PRIMARY_DOMAIN_SCALE_RUNTIME",
    "PRIMARY_ADAPTER_RETAIL", "PRIMARY_ADAPTER_PHYSIONET", "CONTROL_ADAPTER_RETAIL",
    "CONTROL_ADAPTER_PHYSIONET", "LITERATURE_FAMILY_ADAPTER_RETAIL",
    "LITERATURE_FAMILY_ADAPTER_PHYSIONET", "CSDI_AUTHOR_EXTENSION_1",
    "CSDI_AUTHOR_EXTENSION_2", "CSDI_AUTHOR_EXTENSION_3", "CSDI_AUTHOR_EXTENSION_4",
    "EDITPP_AUTHOR_EXTENSION_1", "EDITPP_AUTHOR_EXTENSION_2",
    "EDITPP_AUTHOR_EXTENSION_3", "EDITPP_AUTHOR_EXTENSION_4",
    "PRODUCTION_SCHEMA_EXTERNAL_ACCEPTANCE", "RUNNER_AND_RECOMPUTATION",
    "UNCONDITIONAL_OPERATIONAL_PREDICTIONS", "PRODUCTION_RUNTIME_AND_DURABILITY",
    "TEST28_PRODUCTION_GATE_01", "TEST28_PRODUCTION_GATE_02",
    "TEST28_PRODUCTION_GATE_03", "TEST28_PRODUCTION_GATE_04",
    "TEST28_PRODUCTION_GATE_05", "TEST28_PRODUCTION_GATE_06",
    "TEST28_PRODUCTION_GATE_07", "TEST28_PRODUCTION_GATE_08",
    "TEST28_PRODUCTION_GATE_09", "TEST28_PRODUCTION_GATE_10",
    "TEST28_PRODUCTION_GATE_11", "TEST28_PRODUCTION_GATE_12",
    "TEST28_PRODUCTION_GATE_13", "TEST28_PRODUCTION_GATE_14",
    "TEST28_PRODUCTION_GATE_15", "TEST28_PRODUCTION_GATE_16",
    "TEST28_PRODUCTION_GATE_17", "TEST29_PRODUCTION_ROUTE_RECEIPT",
    "TEST29_WHOLE_METHOD_RESIDUAL", "TEST30_PRODUCTION_COUPLED_PATH_RECEIPT",
    "TEST30_WHOLE_METHOD_RESIDUAL", "REAL_IMMUTABLE_EXECUTION_LEDGER",
    "INDEPENDENT_REAL_RECOMPUTATION_RECEIPT",
    "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED",
)


class ValidationError(RuntimeError):
    """Fail-closed package qualification error."""


@dataclass(frozen=True)
class CapturedFile:
    path: str
    raw: bytes
    leaf_identity: Tuple[int, ...]
    parent_identities: Tuple[Tuple[int, ...], ...]


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _domain_sha256(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _identity(metadata: os.stat_result) -> Tuple[int, ...]:
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_nlink,
        metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns,
    )


def _canonical_relative(value: str) -> PurePosixPath:
    if type(value) is not str or not value or not value.isascii() or "\\" in value:
        raise ValidationError("path must be exact nonempty ASCII POSIX text")
    relative = PurePosixPath(value)
    if (
        relative.as_posix() != value
        or relative.is_absolute()
        or any(part in ("", ".", "..") for part in relative.parts)
    ):
        raise ValidationError("path is noncanonical or escapes the root")
    return relative


@contextmanager
def _opened_stable_root(root: Path):
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(root, flags)
    except OSError as error:
        raise ValidationError("cannot safely open root: %s" % error) from error
    try:
        identity = _identity(os.fstat(descriptor))
        if not stat.S_ISDIR(identity[2]):
            raise ValidationError("root is not a directory")
        yield descriptor, identity
        if _identity(os.fstat(descriptor)) != identity:
            raise ValidationError("root changed during validation")
    finally:
        os.close(descriptor)


def _capture_regular(
    root_fd: int,
    root_identity: Tuple[int, ...],
    relative_path: str,
) -> CapturedFile:
    relative = _canonical_relative(relative_path)
    if _identity(os.fstat(root_fd)) != root_identity:
        raise ValidationError("root changed before read")
    opened = []
    parents = []
    current = root_fd
    try:
        for part in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(part, flags, dir_fd=current)
            except OSError as error:
                raise ValidationError("unsafe parent for %s: %s" % (relative_path, error)) from error
            opened.append(descriptor)
            metadata = os.fstat(descriptor)
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValidationError("non-directory parent for " + relative_path)
            parents.append(_identity(metadata))
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            leaf = os.open(relative.name, flags, dir_fd=current)
        except OSError as error:
            raise ValidationError("unsafe leaf for %s: %s" % (relative_path, error)) from error
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or not 1 <= before.st_size <= MAX_FILE_BYTES
        ):
            raise ValidationError("file custody differs: " + relative_path)
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        if len(raw) != before.st_size or _identity(os.fstat(leaf)) != _identity(before):
            raise ValidationError("file changed or short-read: " + relative_path)
        for descriptor, expected in zip(opened[:-1], parents):
            if _identity(os.fstat(descriptor)) != expected:
                raise ValidationError("parent changed: " + relative_path)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValidationError("root changed after read")
        return CapturedFile(relative_path, raw, _identity(before), tuple(parents))
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _verify_expected(captured: CapturedFile, expected_size: int, expected_sha256: str) -> None:
    if (
        len(captured.raw) != expected_size
        or hashlib.sha256(captured.raw).hexdigest() != expected_sha256
        or not captured.raw.endswith(b"\n")
    ):
        raise ValidationError("fixed binding differs: " + captured.path)


def _binding(role: str, captured: CapturedFile) -> Dict[str, Any]:
    return {
        "bytes": len(captured.raw),
        "mode_octal": "0644",
        "nlink": 1,
        "path": captured.path,
        "raw_sha256": hashlib.sha256(captured.raw).hexdigest(),
        "role": role,
        "terminal_lf": captured.raw.endswith(b"\n"),
    }


def _capture_workspace(
    root_fd: int,
    root_identity: Tuple[int, ...],
    *,
    include_machine: bool,
) -> Dict[str, CapturedFile]:
    captures: Dict[str, CapturedFile] = {}
    expected = {
        path: (size, digest)
        for _, path, size, digest in EXPECTED_AUTHORED_BINDINGS
    }
    expected.update({path: (size, digest) for path, size, digest in SEMANTIC_MANIFEST})
    for path, (size, digest) in expected.items():
        capture = _capture_regular(root_fd, root_identity, path)
        _verify_expected(capture, size, digest)
        captures[path] = capture
    validator = _capture_regular(root_fd, root_identity, VALIDATOR_REL)
    if not validator.raw.endswith(b"\n"):
        raise ValidationError("validator terminal LF differs")
    captures[VALIDATOR_REL] = validator
    if include_machine:
        captures[MACHINE_REL] = _capture_regular(root_fd, root_identity, MACHINE_REL)
    return captures


def _revalidate_captures(
    root_fd: int,
    root_identity: Tuple[int, ...],
    captures: Mapping[str, CapturedFile],
) -> None:
    for path, expected in captures.items():
        actual = _capture_regular(root_fd, root_identity, path)
        if actual != expected:
            raise ValidationError("workspace or capsule identity changed: " + path)


def _strict_json(value: object, name: str) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _strict_json(item, "%s[%d]" % (name, index))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError(name + " has a non-text key")
            _strict_json(item, name + "." + key)
        return
    raise ValidationError(name + " has a non-exact JSON type")


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValidationError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _load_canonical_json(raw: bytes, name: str) -> Dict[str, Any]:
    if not raw.endswith(b"\n") or raw[:-1].endswith(b"\n"):
        raise ValidationError(name + " framing differs")
    try:
        value = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(name + " JSON differs") from error
    if type(value) is not dict:
        raise ValidationError(name + " root differs")
    _strict_json(value, name)
    if _canonical(value) + b"\n" != raw:
        raise ValidationError(name + " is noncanonical")
    return value


def _manifest_payload() -> list[Dict[str, Any]]:
    return [
        {"bytes": size, "path": path, "raw_sha256": digest}
        for path, size, digest in SEMANTIC_MANIFEST
    ]


def _write_all(descriptor: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        count = os.write(descriptor, raw[offset:])
        if count <= 0:
            raise ValidationError("capsule write made no progress")
        offset += count


def _materialize_private_capsule(
    captures: Mapping[str, CapturedFile],
) -> Tuple[Path, Path]:
    parent = Path(tempfile.mkdtemp(prefix="b12-beta-isolated-")).resolve(strict=True)
    os.chmod(parent, 0o700)
    capsule = parent / "capsule"
    capsule.mkdir(mode=0o700)
    try:
        for path, _, _ in SEMANTIC_MANIFEST:
            relative = _canonical_relative(path)
            destination = capsule.joinpath(*relative.parts)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(destination, flags, 0o600)
            try:
                _write_all(descriptor, captures[path].raw)
                os.fchmod(descriptor, 0o644)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        work = parent / "work"
        work.mkdir(mode=0o700)
        if capsule.resolve(strict=True) != capsule or work.resolve(strict=True) != work:
            raise ValidationError("private capsule path differs")
        return parent, capsule
    except Exception:
        shutil.rmtree(parent)
        raise


CHILD_BOOTSTRAP = r'''import hashlib,json,os,sys
from pathlib import Path,PurePosixPath
from types import ModuleType

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")

def pairs(items):
    value={}
    for key,item in items:
        if type(key) is not str or key in value:
            raise RuntimeError("duplicate manifest key")
        value[key]=item
    return value

if len(sys.argv)!=4:
    raise RuntimeError("child argument roster differs")
root=Path(sys.argv[1])
site_path=Path(sys.argv[2])
if not root.is_absolute() or root.resolve(strict=True)!=root:
    raise RuntimeError("capsule root differs")
manifest_raw=sys.argv[3].encode("ascii")
manifest=json.loads(sys.argv[3],object_pairs_hook=pairs)
if type(manifest) is not list or canonical(manifest)!=manifest_raw:
    raise RuntimeError("manifest framing differs")
allowed=set()
for row in manifest:
    if type(row) is not dict or tuple(sorted(row))!=("bytes","path","raw_sha256"):
        raise RuntimeError("manifest row differs")
    relative=PurePosixPath(row["path"])
    if relative.is_absolute() or relative.as_posix()!=row["path"] or any(p in ("",".","..") for p in relative.parts):
        raise RuntimeError("manifest path differs")
    target=root.joinpath(*relative.parts)
    raw=target.read_bytes()
    status=target.stat()
    if (not target.is_file() or status.st_nlink!=1 or (status.st_mode & 0o777)!=0o644 or len(raw)!=row["bytes"] or hashlib.sha256(raw).hexdigest()!=row["raw_sha256"]):
        raise RuntimeError("capsule member differs: "+row["path"])
    allowed.add(row["path"])

if tuple(sys.version_info[:3])!=(3,11,5) or sys.implementation.name!="cpython" or sys.implementation.cache_tag!="cpython-311":
    raise RuntimeError("child interpreter differs")
if not site_path.is_absolute() or site_path.resolve(strict=True)!=site_path:
    raise RuntimeError("site path differs")
sys.path.insert(0,str(root/"src"))
sys.path.append(str(site_path))

def package(name,relative):
    module=ModuleType(name)
    module.__package__=name
    module.__path__=[str(root/"src"/relative)]
    sys.modules[name]=module
    return module

top=package("heterodiff","heterodiff")
for child in ("artifacts","evaluation","processes","theory"):
    value=package("heterodiff."+child,"heterodiff/"+child)
    setattr(top,child,value)

def audit(event,args):
    if event in ("os.system","subprocess.Popen") or event.startswith("socket."):
        raise RuntimeError("forbidden child effect: "+event)
sys.addaudithook(audit)

import importlib
primary=importlib.import_module("heterodiff.evaluation.b12_whole_method_initializer_path_integration_successor")
receipt=primary.run_whole_method_beta_successor(str(root))
primary.validate_beta_successor_receipt(receipt)
receipt_payload=dict(receipt.payload())
receipt_payload["receipt_sha256"]=receipt.receipt_sha256
core=primary._core(str(root))
core_bytes=primary._canonical(core)+b"\n"
core_sha=hashlib.sha256(core_bytes).hexdigest()
if core_sha!=receipt.core_output_sha256:
    raise RuntimeError("child core replay differs")
cp62=sys.modules.get("heterodiff.evaluation.mixed_initializer_test28_execution_capsule")
if (cp62 is None or cp62._CALIBRATION_LAUNCH_COUNT!=0 or cp62._CALIBRATION_RUNNING is not False or any(cp62._CALIBRATION_CASE_LAUNCH_COUNTS.values())):
    raise RuntimeError("CP62 cold calibration branch became reachable")

loaded=[]
source_root=(root/"src").resolve(strict=True)
for name,module in tuple(sys.modules.items()):
    if not name.startswith("heterodiff."):
        continue
    path=getattr(module,"__file__",None)
    if path is None:
        continue
    resolved=Path(path).resolve(strict=True)
    try:
        relative=resolved.relative_to(root).as_posix()
    except ValueError as error:
        raise RuntimeError("local module escaped capsule: "+name) from error
    if relative not in allowed:
        raise RuntimeError("unmanifested local module: "+relative)
    loaded.append(relative)

import numpy,scipy
envelope={
    "core":core,
    "core_output_sha256":core_sha,
    "execution_boundary":{
        "cp62_cold_calibration_entrypoints_executed":False,
        "package_initializer_files_executed":False,
        "package_namespace_policy":"MINIMAL_NAMESPACE_NO_INIT_EXECUTION",
    },
    "loaded_local_source_paths":sorted(set(loaded)),
    "receipt":receipt_payload,
    "runtime":{
        "cpython_cache_tag":sys.implementation.cache_tag,
        "numpy_version":numpy.__version__,
        "python_version":"%d.%d.%d"%tuple(sys.version_info[:3]),
        "scipy_version":scipy.__version__,
    },
}
sys.stdout.buffer.write(canonical(envelope)+b"\n")
'''


def _runtime_boundary() -> Tuple[Path, int, Tuple[int, ...]]:
    if (
        tuple(sys.version_info[:3]) != (3, 11, 5)
        or sys.implementation.name != "cpython"
        or sys.implementation.cache_tag != "cpython-311"
    ):
        raise ValidationError("validator interpreter differs")
    executable = Path(sys.executable)
    if not executable.is_absolute() or not executable.exists():
        raise ValidationError("validator executable differs")
    prefix = Path(sys.prefix)
    if not prefix.is_absolute() or prefix.name != ".venv-m1":
        raise ValidationError("validator must run from the pinned .venv-m1")
    site_path = prefix / "lib/python3.11/site-packages"
    if site_path.resolve(strict=True) != site_path:
        raise ValidationError("site-packages path differs")
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(site_path, flags)
    identity = _identity(os.fstat(descriptor))
    return site_path, descriptor, identity


def _run_isolated_child(capsule: Path) -> Dict[str, Any]:
    manifest_json = _canonical(_manifest_payload()).decode("ascii")
    site_path, site_fd, site_identity = _runtime_boundary()
    environment = {
        "BLIS_NUM_THREADS": "1", "LANG": "C", "LC_ALL": "C",
        "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
        "PYTHONUTF8": "1", "TZ": "UTC", "VECLIB_MAXIMUM_THREADS": "1",
    }
    try:
        completed = subprocess.run(
            [
                sys.executable, "-I", "-S", "-B", "-c", CHILD_BOOTSTRAP,
                str(capsule), str(site_path), manifest_json,
            ],
            cwd=str(capsule.parent / "work"),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=CHILD_TIMEOUT_SECONDS,
        )
        if _identity(os.fstat(site_fd)) != site_identity:
            raise ValidationError("site-packages root changed during child")
    except subprocess.TimeoutExpired as error:
        raise ValidationError("isolated child timed out") from error
    finally:
        os.close(site_fd)
    if completed.returncode != 0:
        detail = completed.stderr[:2048].decode("utf-8", errors="replace")
        raise ValidationError("isolated child failed: " + detail)
    if completed.stderr:
        raise ValidationError("isolated child emitted stderr")
    if not 1 <= len(completed.stdout) <= MAX_CHILD_OUTPUT_BYTES:
        raise ValidationError("isolated child output bound differs")
    return _load_canonical_json(completed.stdout, "child envelope")


def _validate_envelope(envelope: Mapping[str, Any]) -> None:
    if type(envelope) is not dict or tuple(sorted(envelope)) != (
        "core", "core_output_sha256", "execution_boundary", "loaded_local_source_paths", "receipt", "runtime"
    ):
        raise ValidationError("child envelope roster differs")
    if envelope["core_output_sha256"] != EXPECTED_CORE_SHA256:
        raise ValidationError("core digest differs")
    if envelope["runtime"] != {
        "cpython_cache_tag": "cpython-311",
        "numpy_version": "2.4.6",
        "python_version": "3.11.5",
        "scipy_version": "1.17.1",
    }:
        raise ValidationError("child runtime identity differs")
    if envelope["execution_boundary"] != {
        "cp62_cold_calibration_entrypoints_executed": False,
        "package_initializer_files_executed": False,
        "package_namespace_policy": "MINIMAL_NAMESPACE_NO_INIT_EXECUTION",
    }:
        raise ValidationError("isolated execution boundary differs")
    manifest_paths = {path for path, _, _ in SEMANTIC_MANIFEST}
    loaded = envelope["loaded_local_source_paths"]
    if (
        type(loaded) is not list
        or loaded != list(EXPECTED_LOADED_LOCAL_SOURCE_PATHS)
        or any(path not in manifest_paths for path in loaded)
    ):
        raise ValidationError("loaded local source roster differs")
    core = envelope["core"]
    receipt = envelope["receipt"]
    if type(core) is not dict or type(receipt) is not dict:
        raise ValidationError("child semantics type differs")
    if hashlib.sha256(_canonical(core) + b"\n").hexdigest() != EXPECTED_CORE_SHA256:
        raise ValidationError("core bytes differ")
    if receipt.get("receipt_sha256") != EXPECTED_RECEIPT_SHA256:
        raise ValidationError("receipt digest differs")
    exact_receipt = {
        "authoritative_qualification_requires_isolated_validator": True,
        "core_output_sha256": EXPECTED_CORE_SHA256,
        "custody_chain_sha256": EXPECTED_CUSTODY_SHA256,
        "derived_initial_state_sha256": EXPECTED_INITIAL_STATE_SHA256,
        "direct_public_api_custody_authenticated": False,
        "independent_implementation_sha256": "5c01fb8a195402cf012a815b92bcec13b86845bc088f8b1152d28aa6153a5f5f",
        "independent_output_sha256": EXPECTED_CORE_SHA256,
        "initializer_to_path_integrated": True,
        "integrated_path_input_sha256": EXPECTED_PATH_INPUT_SHA256,
        "integrated_path_report_sha256": EXPECTED_PATH_REPORT_SHA256,
        "open_residual_slot_count": 50,
        "predecessor_receipt_sha256": EXPECTED_PREDECESSOR_RECEIPT_SHA256,
        "proposed_timetable_task": PROPOSED_TASK,
        "receipt_sha256": EXPECTED_RECEIPT_SHA256,
        "schema_version": "heterodiff-b12-whole-method-initializer-path-receipt-v1",
        "selected_configuration_sha256": EXPECTED_SELECTED_CONFIGURATION_SHA256,
        "stable_initializer_execution_sha256": EXPECTED_STABLE_INITIALIZER_SHA256,
        "state": "OFFLINE_NONCONFIRMATORY_WHOLE_METHOD_BETA_INTEGRATED",
        "supplied_input_sha256": EXPECTED_SUPPLIED_INPUT_SHA256,
        "test28_initializer_admissible": True,
        "transform_policy_id": TRANSFORM_POLICY_ID,
        "transform_sha256": EXPECTED_TRANSFORM_SHA256,
    }
    if receipt != exact_receipt:
        raise ValidationError("exact receipt differs")
    effects = {
        "blocker_delta": 0, "data_accessed": False, "field_delta": 0,
        "formal_test_delta": 0, "network_used": False, "result_delta": 0,
        "science_executed": False, "tracker_or_ledger_edited": False,
        "training_executed": False, "upstream_runtimes_executed": False,
    }
    if core.get("effects") != effects:
        raise ValidationError("effect boundary differs")
    if core.get("formal_test_states") != {"28": "OPEN", "29": "OPEN", "30": "PENDING"}:
        raise ValidationError("Formal-Test boundary differs")
    if core.get("open_residual_predicate_ids") != list(REAL_RESIDUAL_IDS):
        raise ValidationError("exact-50 residual roster differs")
    if core.get("proposed_timetable_task_closures") != [PROPOSED_TASK]:
        raise ValidationError("proposed checkbox roster differs")
    if core.get("qualification_boundary") != {
        "authoritative_isolated_hash_first_validator_required": True,
        "direct_public_api_custody_authenticated": False,
    }:
        raise ValidationError("qualification boundary differs")
    expected_nonclaims = {
        "arbitrary_length_general_path": False, "b12_closed": False,
        "confirmatory_evidence": False, "direct_public_api_custody_authenticated": False,
        "gate_b0_feature_complete": False, "production_receipt": False,
        "real_residual_receipts_present": 0, "upstream_external_runtime": False,
    }
    if core.get("nonclaims") != expected_nonclaims:
        raise ValidationError("nonclaim boundary differs")
    state = core.get("initializer_path_state")
    path = core.get("integrated_path")
    custody = core.get("custody_chain")
    if not all(type(value) is dict for value in (state, path, custody)):
        raise ValidationError("integration object type differs")
    if (
        state["selected_configuration_sha256"] != EXPECTED_SELECTED_CONFIGURATION_SHA256
        or state["initial_state_sha256"] != EXPECTED_INITIAL_STATE_SHA256
        or state["transform_sha256"] != EXPECTED_TRANSFORM_SHA256
        or state["occurrences"] != []
        or state["empty_configuration_initial_state"] is not True
        or path["initial_state_sha256"] != state["initial_state_sha256"]
        or path["selected_configuration_sha256"] != state["selected_configuration_sha256"]
        or path["transform_sha256"] != state["transform_sha256"]
        or path["path_input_sha256"] != EXPECTED_PATH_INPUT_SHA256
        or path["path_report_sha256"] != EXPECTED_PATH_REPORT_SHA256
        or path["initializer_to_path_integrated"] is not True
        or path["test28_initializer_admissible"] is not True
        or path["formal_test28_production_law_admissible"] is not False
        or path["arbitrary_length_general_strang_path_integrated"] is not False
        or [step["central_edit"]["route_id"] for step in path["steps"]]
        != ["beta-zero-birth", "two-step-death"]
        or [step["central_edit"]["family"] for step in path["steps"]]
        != ["birth", "death"]
    ):
        raise ValidationError("initializer-to-path semantics differ")
    if (
        custody["custody_chain_sha256"] != EXPECTED_CUSTODY_SHA256
        or custody["initializer_result_sha256"] != EXPECTED_STABLE_INITIALIZER_SHA256
        or custody["supplied_input_sha256"] != EXPECTED_SUPPLIED_INPUT_SHA256
        or custody["integrated_path_report_sha256"] != EXPECTED_PATH_REPORT_SHA256
        or core["predecessor"]["machine_record_sha256"]
        != EXPECTED_PREDECESSOR_RECORD_SHA256
    ):
        raise ValidationError("custody or predecessor binding differs")


def _capsule_manifest_sha256() -> str:
    return _domain_sha256(
        "heterodiff-b12-whole-method-beta-isolated-capsule-manifest-v1",
        _manifest_payload(),
    )


def _expected_machine(
    captures: Mapping[str, CapturedFile], envelope: Mapping[str, Any]
) -> Dict[str, Any]:
    _validate_envelope(envelope)
    authored = [
        _binding(role, captures[path])
        for role, path, _, _ in EXPECTED_AUTHORED_BINDINGS
    ]
    authored.append(_binding("authoritative_validator", captures[VALIDATOR_REL]))
    manifest_bindings = [
        _binding("semantic_source" if path.endswith(".py") else "sealed_resource", captures[path])
        for path, _, _ in SEMANTIC_MANIFEST
    ]
    receipt = envelope["receipt"]
    core = envelope["core"]
    route_binding = {
        "author_applied_timetable_checkbox_delta": 0,
        "authoritative_qualification_requires_isolated_validator": True,
        "custody_chain_sha256": receipt["custody_chain_sha256"],
        "derived_initial_state_sha256": receipt["derived_initial_state_sha256"],
        "direct_public_api_custody_authenticated": False,
        "gate_b0_feature_complete_eligible": False,
        "independent_output_sha256": receipt["independent_output_sha256"],
        "initializer_to_path_integrated": True,
        "integrated_path_input_sha256": receipt["integrated_path_input_sha256"],
        "integrated_path_report_sha256": receipt["integrated_path_report_sha256"],
        "isolated_capsule_manifest_sha256": _capsule_manifest_sha256(),
        "isolated_hash_first_validator_pass": True,
        "open_residual_slot_count": 50,
        "predecessor_machine_record_sha256": EXPECTED_PREDECESSOR_RECORD_SHA256,
        "predecessor_receipt_sha256": EXPECTED_PREDECESSOR_RECEIPT_SHA256,
        "proposed_timetable_task_closures": [PROPOSED_TASK],
        "selected_configuration_sha256": receipt["selected_configuration_sha256"],
        "stable_initializer_execution_sha256": receipt["stable_initializer_execution_sha256"],
        "supplied_input_sha256": receipt["supplied_input_sha256"],
        "test28_initializer_admissible": True,
        "transform_policy_id": receipt["transform_policy_id"],
        "transform_sha256": receipt["transform_sha256"],
    }
    unsigned = {
        "bindings": authored,
        "effects": core["effects"],
        "isolated_capsule": {
            "cp62_cold_calibration_entrypoints_executed": False,
            "execution_flags": ["-I", "-S", "-B"],
            "loaded_local_source_paths": envelope["loaded_local_source_paths"],
            "manifest_file_count": len(SEMANTIC_MANIFEST),
            "manifest_sha256": _capsule_manifest_sha256(),
            "numpy_scipy_files_capsule_manifested": False,
            "ordinary_clean_route_core_output_sha256": EXPECTED_CORE_SHA256,
            "ordinary_clean_route_receipt_sha256": EXPECTED_RECEIPT_SHA256,
            "package_initializer_files_executed": False,
            "package_namespace_policy": "MINIMAL_NAMESPACE_NO_INIT_EXECUTION",
            "private_capsule_mode_octal": "0700",
            "runtime": envelope["runtime"],
            "runtime_site_path_external_to_capsule": True,
            "upstream_csdi_editpp_runtimes_executed": False,
        },
        "route_binding": route_binding,
        "schema_version": SCHEMA_VERSION,
        "semantic_manifest": manifest_bindings,
        "semantics": {
            "core": core,
            "core_output_sha256": envelope["core_output_sha256"],
            "receipt": receipt,
            "supplied_input_constants": {
                "checkpoint_step": 256,
                "initializer_row_ordinal": 5,
                "initializer_seed_hex": "12a5228200019dae",
                "path_words": [2, 27],
                "schema_version": "heterodiff-b12-whole-method-nonconfirmatory-input-v1",
                "supplied_input_sha256": EXPECTED_SUPPLIED_INPUT_SHA256,
            },
        },
        "state": STATE,
    }
    machine = dict(unsigned)
    machine["record_sha256"] = _domain_sha256(SCHEMA_VERSION, unsigned)
    return machine


def _execute_capsule(
    captures: Mapping[str, CapturedFile]
) -> Dict[str, Any]:
    parent, capsule = _materialize_private_capsule(captures)
    try:
        with _opened_stable_root(capsule) as (capsule_fd, capsule_identity):
            capsule_captures: Dict[str, CapturedFile] = {}
            for path, size, digest in SEMANTIC_MANIFEST:
                value = _capture_regular(capsule_fd, capsule_identity, path)
                _verify_expected(value, size, digest)
                capsule_captures[path] = value
            envelope = _run_isolated_child(capsule)
            _revalidate_captures(capsule_fd, capsule_identity, capsule_captures)
            return envelope
    finally:
        shutil.rmtree(parent)


def validate(root: Path) -> Dict[str, Any]:
    if not root.is_absolute() or root.resolve(strict=True) != root:
        raise ValidationError("project root must be canonical absolute physical path")
    with _opened_stable_root(root) as (root_fd, root_identity):
        captures = _capture_workspace(root_fd, root_identity, include_machine=True)
        machine = _load_canonical_json(captures[MACHINE_REL].raw, "machine record")
        envelope = _execute_capsule(captures)
        expected = _expected_machine(captures, envelope)
        if machine != expected:
            raise ValidationError("machine record differs from isolated reconstruction")
        _revalidate_captures(root_fd, root_identity, captures)
        return {
            "core_output_sha256": envelope["core_output_sha256"],
            "record_sha256": machine["record_sha256"],
            "receipt_sha256": envelope["receipt"]["receipt_sha256"],
        }


def _emit_expected(root: Path) -> Dict[str, Any]:
    if not root.is_absolute() or root.resolve(strict=True) != root:
        raise ValidationError("project root must be canonical absolute physical path")
    with _opened_stable_root(root) as (root_fd, root_identity):
        captures = _capture_workspace(root_fd, root_identity, include_machine=False)
        envelope = _execute_capsule(captures)
        expected = _expected_machine(captures, envelope)
        _revalidate_captures(root_fd, root_identity, captures)
        return expected


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--emit-expected", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = _parse_args()
    root = (
        arguments.root.absolute()
        if arguments.root is not None
        else Path(__file__).resolve().parents[2]
    )
    try:
        if arguments.emit_expected:
            print(_canonical(_emit_expected(root)).decode("ascii"))
            return 0
        result = validate(root)
    except Exception as error:
        print("FAIL — %s" % error, file=sys.stderr)
        return 1
    print(
        "%s — record %s; receipt %s; core %s"
        % (
            PASS_TOKEN,
            result["record_sha256"],
            result["receipt_sha256"],
            result["core_output_sha256"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
