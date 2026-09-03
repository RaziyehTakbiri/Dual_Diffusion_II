"""Fixed supervisor-side source profile for the output-blind child runtime.

The implementation closure selects adapter code, but it does not select the
runtime trusted to call that adapter.  The supervisor matches the runtime and
its complete protected-project dependency set against this local profile
before spawning a child.  External interpreter and dependency identities
remain outside this source profile and are not attested.
"""

from __future__ import annotations

import hashlib
import json
from typing import NamedTuple, Tuple


OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_ARTIFACT_TYPE = (
    "heterodiff.adapter.output-blind-child-runtime-capture-profile.v1"
)
OUTPUT_BLIND_TRUSTED_RUNTIME_CALL_ABI_ID = (
    "case-input-bytes-and-adapter-two-required-positional-v1"
)
OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME = (
    "heterodiff.data.adapter_output_blind_child_runtime"
)
OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME = (
    "run_output_blind_adapter_case"
)


class TrustedRuntimeSourceModuleV1(NamedTuple):
    """One exact protected-project module in the fixed runtime profile."""

    module_name: str
    is_package: bool
    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str


OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES: Tuple[
    TrustedRuntimeSourceModuleV1, ...
] = (
    TrustedRuntimeSourceModuleV1(
        "heterodiff",
        True,
        "support-source",
        0,
        "module:heterodiff",
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data",
        True,
        "support-source",
        0,
        "module:heterodiff.data",
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data.adapter_child_bundle_codec",
        False,
        "contract-source",
        40704,
        "module:heterodiff.data.adapter_child_bundle_codec",
        "43174618cfae3669cacb78b80747089a"
        "b6d2be065cf272505e3e2c79378f1d74",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data.adapter_contract",
        False,
        "contract-source",
        49022,
        "module:heterodiff.data.adapter_contract",
        "2fda1b033ffb473c77f7057c8191598d"
        "0880d0498d685dc0bcc220b2f737e82c",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data.adapter_evidence",
        False,
        "contract-source",
        111819,
        "module:heterodiff.data.adapter_evidence",
        "862e27ebd6de360633282db192b57caf4"
        "9eee0e0f1b023516593719c3102d29b",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data.adapter_output_blind_case_input",
        False,
        "contract-source",
        19457,
        "module:heterodiff.data.adapter_output_blind_case_input",
        "9b6a39d161c0a5a1d18f091bdce1bf6"
        "c2a9247eded73faf179241895c48548b4",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.data.adapter_output_blind_child_runtime",
        False,
        "contract-source",
        9316,
        "module:heterodiff.data.adapter_output_blind_child_runtime",
        "70930b9e60e0fe8a4f33d32f4ea1a15"
        "1f16b9aeb56fa71198276026d61ca86f2",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.events",
        True,
        "contract-source",
        1222,
        "module:heterodiff.events",
        "3e4e213835262634f5f795e60dafda08"
        "fc3d599a5741088f567215d5406640b9",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.events.configuration",
        False,
        "contract-source",
        16009,
        "module:heterodiff.events.configuration",
        "66fdc15a1253be8490ff3a18ca935534"
        "4388a7820cf7f74c293372669585c0c4",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.events.observations",
        False,
        "contract-source",
        14142,
        "module:heterodiff.events.observations",
        "bf1377f543f0adbd5d690c61ebff4eff"
        "08db73aa47ef7fd4bc516eeb026e0698",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.events.schema",
        False,
        "contract-source",
        18274,
        "module:heterodiff.events.schema",
        "bebe1ac4c106ea58f05ef01568dfceb6c"
        "cd6580443baf6e43a8da8ea45cfe3e6",
    ),
    TrustedRuntimeSourceModuleV1(
        "heterodiff.events.transforms",
        False,
        "contract-source",
        16464,
        "module:heterodiff.events.transforms",
        "0bcd1e09de33c635b347fd7bb38646e3"
        "2a32227cbd4fe70766a27b41156b16d0",
    ),
)


def output_blind_runtime_capture_profile_bytes(
    modules: Tuple[TrustedRuntimeSourceModuleV1, ...],
) -> bytes:
    """Build the canonical fixed-schema profile for exact joined modules."""

    if (
        type(modules) is not tuple
        or not modules
        or any(type(item) is not TrustedRuntimeSourceModuleV1 for item in modules)
    ):
        raise TypeError("runtime capture profile modules must be exact")
    names = tuple(item.module_name for item in modules)
    if names != tuple(sorted(set(names))):
        raise ValueError("runtime capture profile module names differ")
    for item in modules:
        if (
            type(item.module_name) is not str
            or not item.module_name
            or type(item.is_package) is not bool
            or item.role_id
            not in ("adapter-source", "contract-source", "support-source")
            or type(item.source_byte_count) is not int
            or item.source_byte_count < 0
            or type(item.source_object_id) is not str
            or item.source_object_id != "module:" + item.module_name
            or type(item.source_sha256) is not str
            or len(item.source_sha256) != 64
            or any(
                char not in "0123456789abcdef"
                for char in item.source_sha256
            )
        ):
            raise ValueError("runtime capture profile module differs")
    tree = {
        "artifact_type": OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_ARTIFACT_TYPE,
        "format_version": "1",
        "protected_namespace_roots": ["heterodiff"],
        "runtime_call_abi_id": OUTPUT_BLIND_TRUSTED_RUNTIME_CALL_ABI_ID,
        "runtime_entry_point": {
            "callable_name": OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME,
            "module_name": OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME,
        },
        "modules": [
            {
                "is_package": item.is_package,
                "module_name": item.module_name,
                "role_id": item.role_id,
                "source_byte_count": item.source_byte_count,
                "source_object_id": item.source_object_id,
                "source_sha256": item.source_sha256,
            }
            for item in modules
        ],
    }
    return json.dumps(
        tree,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii", "strict")


def output_blind_runtime_capture_profile_sha256(
    modules: Tuple[TrustedRuntimeSourceModuleV1, ...],
) -> str:
    raw = output_blind_runtime_capture_profile_bytes(modules)
    return hashlib.sha256(
        OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_ARTIFACT_TYPE.encode(
            "ascii", "strict"
        )
        + b"\x00"
        + len(raw).to_bytes(8, "big")
        + raw
    ).hexdigest()


OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_BYTES = (
    output_blind_runtime_capture_profile_bytes(
        OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
    )
)
OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256 = (
    output_blind_runtime_capture_profile_sha256(
        OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
    )
)


__all__ = [
    "OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_CALL_ABI_ID",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_ARTIFACT_TYPE",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_BYTES",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256",
    "OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES",
    "TrustedRuntimeSourceModuleV1",
    "output_blind_runtime_capture_profile_bytes",
    "output_blind_runtime_capture_profile_sha256",
]
