"""Hostile contract tests for the definition-only CP65 schema catalog."""

from __future__ import annotations

import inspect
import hashlib
import json
from dataclasses import fields
from pathlib import Path

import heterodiff.evaluation.mixed_initializer_test28_production_schema_preimage_validator as cp65
import pytest


_ZERO_SHA256 = "0" * 64
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_TEST_RSA_N = int(
    "d6bd979dc04df9b8b2f0a44d8fedc5acc83bfac1eee9205f68064fd00348d425"
    "99f591c66350f64862ed47ef162c5047e6b099cb60bbea5b6476764b466d47d3"
    "b79b9d247fc71b1e344a72b35394973b2e0567cd405fad7837e7d3b1426b27c9"
    "76a59de3dd87490bad87cd38668cf755b77c450ae83fbb9380e5aab28096e60b0"
    "aa7aaf51d9bacf9f5ef8ccadd9639254510ca26b2b348d2599cbf3ec2e86254e4"
    "8d781fc3db4298f912c9ed72633ede902622118946d9ec9614e0930bea5b90b84"
    "45d321cc86fbca79b7ebe86020069b56503df6b890798082189f428eb77b2b347"
    "3fc434a9e46e3842a64f263b431e9a5940c165feef82eb59360db3de42e6e59d"
    "b0ee7d567cfe96076e230c72b3858931a50bd7c5c86918fa1837f8d45fa47969"
    "a40bd5fd3850c3a26079930eeec5be77ca8b0c3e988b63a2de056ab25fb95db31"
    "43ccb243c611319ef8ea44e690b9a38b542e16832db0c9f06d1ba4fb1ca06b740"
    "8fc19b6a6cdd26b02552c9a15cf146be2ab653ddacca63065db812c081",
    16,
)
_TEST_RSA_D = int(
    "d61279340d026ee13e9980e1c58ade9629a3098f0d919ff11c6db66102f53670"
    "29b4525778a8bc6c5b1a7aac90e92a3b1371984fd42661322ccb9f8fd92c95ff"
    "2cb9d8050bd0bc6af6ec04be5aa2f5c44c539d30536d4e2c5b67237541663b6"
    "aae79da15cfc0cf03f24140476a8c3b015b8269fdbe9bd26df0808413a0f74d6"
    "b527ae585a7b78ad040e946ecf1cb913a6348a28dc375d131c99de65535ce9e40"
    "4cfbeef593b56005c9bf7e47d4d1b55a004fd384b1da4ce37a96636e93e154d6"
    "f3d8dfcb395d90501e201adbaab9c629b540ddc274da22163079a32d56dd69364"
    "6f01c40b1e5abb67ea2be353ea484697780b9fa8f41257c61aea8a87ac6c605e"
    "ff40238b9988829507b995f0fa196f8a28a3c62e8024757d6f1ba695b443efc4"
    "bdb3cf322ca878ab726b59a5106399cc9f94c3f978db205ee2f4af409f43d150"
    "ee0769c74351ed574566f12375bc9126e8fbf83ce4a71252237c8786d032a4d76"
    "e09c4014a868c535ba9885ffa0baccfb4d89ddd50793562d5d840a86f20365",
    16,
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _test_rsa_pss_signature(message: bytes, family_id: str) -> bytes:
    """Create a deterministic test-only PSS vector; production exposes no signer."""

    message_hash = hashlib.sha256(message).digest()
    salt = hashlib.sha256(("cp65-test-salt:" + family_id).encode("ascii")).digest()
    digest = hashlib.sha256(b"\0" * 8 + message_hash + salt).digest()
    data_block = b"\0" * 318 + b"\x01" + salt
    mask = bytearray()
    counter = 0
    while len(mask) < len(data_block):
        mask.extend(hashlib.sha256(digest + counter.to_bytes(4, "big")).digest())
        counter += 1
    encoded = bytearray(
        left ^ right for left, right in zip(data_block, mask[: len(data_block)])
    )
    encoded[0] &= 0x7F
    encoded.extend(digest)
    encoded.append(0xBC)
    signature = pow(int.from_bytes(encoded, "big"), _TEST_RSA_D, _TEST_RSA_N)
    return signature.to_bytes(384, "big")


def _json_pointer(document: object, pointer: str) -> object:
    """Resolve one exact RFC-6901 pointer for immutable-fixture checks."""

    current = document
    for encoded in pointer.split("/")[1:]:
        key = encoded.replace("~1", "/").replace("~0", "~")
        if type(current) is list:
            current = current[int(key)]
        else:
            assert type(current) is dict
            current = current[key]
    return current


def _receipt_payload(artifact_id: str, document: dict) -> bytes:
    """Finish one synthetic receipt using the independently stated body formula."""

    declaration = next(
        row for row in cp65._ARTIFACT_DECLARATIONS if row[0] == artifact_id
    )
    domain = declaration[6].encode("ascii") + b"\0"
    body = dict(document)
    body["body_sha256"] = _ZERO_SHA256
    document = dict(body)
    document["body_sha256"] = hashlib.sha256(domain + _canonical_json(body)).hexdigest()
    return _canonical_json(document)


def _inventory_entry(ordinal: int, path: str, payload: bytes) -> dict:
    row = {
        "ordinal": ordinal,
        "path": path,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "entry_sha256": _ZERO_SHA256,
    }
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-preterminal-durable-artifact-inventory-entry-v1\0"
        + _canonical_json(row)
    ).hexdigest()
    return row


def _preterminal_inventory_payload(
    entries: list[dict],
    *,
    transition_entry_count: int = 1,
    transition_head_sha256: str = "a" * 64,
) -> bytes:
    ordered = hashlib.sha256(
        b"cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1\0"
        + b"".join(bytes.fromhex(row["entry_sha256"]) for row in entries)
    ).hexdigest()
    return _receipt_payload(
        "preterminal-durable-artifact-inventory",
        {
            "schema": "cp65-test28-preterminal-durable-artifact-inventory-v1",
            "purpose": "preterminal-durable-artifact-inventory",
            "attempt_id": "attempt-development-only",
            "terminal_arm": "PREAUTHORIZATION",
            "auxiliary_transition_journal_prefix_entry_count": transition_entry_count,
            "auxiliary_transition_journal_prefix_head_sha256": transition_head_sha256,
            "entry_count": len(entries),
            "entries": entries,
            "ordered_entries_sha256": ordered,
            "created_at_utc": "2026-01-01T00:00:00.000001Z",
            "body_sha256": _ZERO_SHA256,
        },
    )


def _terminal_state_payload(
    inventory_payload: bytes,
    *,
    transition_entry_count: int = 2,
    transition_head_sha256: str = "d" * 64,
) -> bytes:
    return _receipt_payload(
        "terminal-state",
        {
            "schema": "cp65-test28-terminal-state-v1",
            "purpose": "attempt-terminal-state-publication",
            "attempt_id": "attempt-development-only",
            "terminal_arm": "PREAUTHORIZATION",
            "previous_lifecycle_state": "FROZEN",
            "terminal_state": "INCOMPLETE",
            "freeze_receipt_sha256": "b" * 64,
            "preauthorization_outcome_sha256": "c" * 64,
            "launch_authorization_sha256": _ZERO_SHA256,
            "postauthorization_outcome_sha256": _ZERO_SHA256,
            "started_receipt_sha256": _ZERO_SHA256,
            "durable_artifact_inventory_sha256": hashlib.sha256(
                inventory_payload
            ).hexdigest(),
            "auxiliary_transition_journal_after_inventory_entry_count": (
                transition_entry_count
            ),
            "auxiliary_transition_journal_after_inventory_head_sha256": (
                transition_head_sha256
            ),
            "reason_code": "attempt-incomplete",
            "terminalized_at_utc": "2026-01-01T00:00:00.000002Z",
            "body_sha256": _ZERO_SHA256,
        },
    )


def _sha256_manifest_payload(
    inventory_entries: list[dict],
    inventory_payload: bytes,
    terminal_payload: bytes,
    *,
    transition_entry_count: int = 3,
    transition_head_sha256: str = "e" * 64,
) -> bytes:
    entries = [
        {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
        for row in inventory_entries
    ]
    entries.extend(
        (
            {
                "path": "preterminal_durable_artifact_inventory.json",
                "bytes": len(inventory_payload),
                "sha256": hashlib.sha256(inventory_payload).hexdigest(),
            },
            {
                "path": "terminal_state.json",
                "bytes": len(terminal_payload),
                "sha256": hashlib.sha256(terminal_payload).hexdigest(),
            },
        )
    )
    entries.sort(key=lambda row: row["path"])
    ordered = hashlib.sha256(
        b"cp65-test28-sha256-manifest-ordered-entries-v1\0" + _canonical_json(entries)
    ).hexdigest()
    return _receipt_payload(
        "sha256-manifest",
        {
            "schema": "cp65-test28-sha256-manifest-v1",
            "purpose": "terminal-corpus-sha256-manifest",
            "attempt_id": "attempt-development-only",
            "terminal_state_sha256": hashlib.sha256(terminal_payload).hexdigest(),
            "auxiliary_transition_journal_after_terminal_entry_count": (
                transition_entry_count
            ),
            "auxiliary_transition_journal_after_terminal_head_sha256": (
                transition_head_sha256
            ),
            "entry_count": len(entries),
            "entries": entries,
            "ordered_entries_sha256": ordered,
            "created_at_utc": "2026-01-01T00:00:00.000003Z",
            "body_sha256": _ZERO_SHA256,
        },
    )


def _refinish_inventory_document(document: dict) -> bytes:
    for row in document["entries"]:
        row["entry_sha256"] = _ZERO_SHA256
        row["entry_sha256"] = hashlib.sha256(
            b"cp65-test28-preterminal-durable-artifact-inventory-entry-v1\0"
            + _canonical_json(row)
        ).hexdigest()
    document["entry_count"] = len(document["entries"])
    document["ordered_entries_sha256"] = hashlib.sha256(
        b"cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1\0"
        + b"".join(bytes.fromhex(row["entry_sha256"]) for row in document["entries"])
    ).hexdigest()
    return _receipt_payload("preterminal-durable-artifact-inventory", document)


def _refinish_sha256_manifest_document(document: dict) -> bytes:
    document["entry_count"] = len(document["entries"])
    document["ordered_entries_sha256"] = hashlib.sha256(
        b"cp65-test28-sha256-manifest-ordered-entries-v1\0"
        + _canonical_json(document["entries"])
    ).hexdigest()
    return _receipt_payload("sha256-manifest", document)


def _terminal_publication_fixture() -> tuple[
    tuple[tuple[str, str, bytes], ...], bytes, bytes, bytes
]:
    earlier = (
        (
            "dependency-lock",
            "frozen_inputs/dependency_lock.txt",
            (
                _PROJECT_ROOT / "requirements/m1-reference-macos-arm64-py311.lock"
            ).read_bytes(),
        ),
        (
            "frozen-protocol",
            "frozen_inputs/protocol.md",
            (
                _PROJECT_ROOT
                / "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
            ).read_bytes(),
        ),
    )
    entries = [
        _inventory_entry(ordinal, relative_path, payload)
        for ordinal, (_artifact_id, relative_path, payload) in enumerate(earlier, 1)
    ]
    inventory = _preterminal_inventory_payload(entries)
    terminal = _terminal_state_payload(inventory)
    manifest = _sha256_manifest_payload(entries, inventory, terminal)
    return earlier, inventory, terminal, manifest


def _reviewer_key_set_payload() -> tuple[bytes, tuple[dict, ...]]:
    rows = []
    modulus_hex = _TEST_RSA_N.to_bytes(384, "big").hex()
    for ordinal, role in enumerate(cp65._REQUIRED_REVIEWER_ROLES, 1):
        row = {
            "reviewer_role": role,
            "reviewer_identity_sha256": hashlib.sha256(
                ("cp65-test-reviewer:" + role).encode("ascii")
            ).hexdigest(),
            "signature_scheme_id": "rsa-pss-sha256-3072-e65537-salt32-v1",
            "authority_id": "cp65-test-reviewer-%d" % ordinal,
            "public_key_identity_sha256": _ZERO_SHA256,
            "modulus_hex": modulus_hex,
            "public_exponent": 65_537,
            "valid_from_utc": "2025-01-01T00:00:00.000000Z",
            "valid_until_utc": "2030-01-01T00:00:00.000000Z",
            "row_sha256": _ZERO_SHA256,
        }
        identity = {
            "reviewer_role": row["reviewer_role"],
            "reviewer_identity_sha256": row["reviewer_identity_sha256"],
            "signature_scheme_id": row["signature_scheme_id"],
            "authority_id": row["authority_id"],
            "modulus_hex": row["modulus_hex"],
            "public_exponent": row["public_exponent"],
        }
        row["public_key_identity_sha256"] = hashlib.sha256(
            b"cp65-test28-independent-reviewer-public-key-identity-v1\0"
            + _canonical_json(identity)
        ).hexdigest()
        row["row_sha256"] = hashlib.sha256(
            b"cp65-test28-independent-reviewer-public-key-row-v1\0"
            + _canonical_json(row)
        ).hexdigest()
        rows.append(row)
    payload = _receipt_payload(
        "independent-reviewer-public-key-set",
        {
            "schema": "cp65-test28-independent-reviewer-public-key-set-v1",
            "purpose": "independent-reviewer-public-key-set-custody",
            "protocol_sha256": (
                "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8"
            ),
            "machine_manifest_sha256": (
                "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
            ),
            "required_reviewer_roles": list(cp65._REQUIRED_REVIEWER_ROLES),
            "key_count": 4,
            "ordered_keys": rows,
            "ordered_public_key_identity_sha256s": [
                row["public_key_identity_sha256"] for row in rows
            ],
            "body_sha256": _ZERO_SHA256,
        },
    )
    return payload, tuple(rows)


def _launch_authorization_pair(
    *,
    corrupt_signature: bool = False,
    preflight_summary_raw_sha256: str = "c" * 64,
    independent_signoff_raw_sha256: str = "f" * 64,
) -> tuple[bytes, bytes]:
    scheme = "rsa-pss-sha256-3072-e65537-salt32-v1"
    key = {
        "schema": "cp65-test28-launch-authority-public-key-v1",
        "purpose": "launch-authority-public-key-custody",
        "authority_scheme_id": scheme,
        "authority_id": "cp65-test-launch-authority",
        "modulus_hex": _TEST_RSA_N.to_bytes(384, "big").hex(),
        "public_exponent": 65_537,
        "valid_from_utc": "2025-01-01T00:00:00.000000Z",
        "valid_until_utc": "2030-01-01T00:00:00.000000Z",
        "body_sha256": _ZERO_SHA256,
    }
    key_payload = _receipt_payload("launch-authority-public-key", key)
    identity = hashlib.sha256(
        b"cp65-test28-launch-authority-public-key-identity-v1\0"
        + _canonical_json(
            {
                "authority_scheme_id": scheme,
                "authority_id": key["authority_id"],
                "modulus_hex": key["modulus_hex"],
                "public_exponent": 65_537,
            }
        )
    ).hexdigest()
    receipt = {
        "schema": "cp65-test28-launch-authorization-receipt-v2",
        "purpose": "explicit-production-launch-authorization",
        "attempt_id": "attempt-development-only",
        "attempt_state": "FROZEN",
        "protocol_sha256": "1" * 64,
        "machine_manifest_sha256": "2" * 64,
        "source_manifest_sha256": "3" * 64,
        "dependency_lock_sha256": "4" * 64,
        "seed_source_receipt_sha256": "5" * 64,
        "seed_capsule_body_sha256": "6" * 64,
        "schedule_sha256": "7" * 64,
        "production_runtime_receipt_sha256": "8" * 64,
        "capacity_receipt_sha256": "9" * 64,
        "durability_receipt_sha256": "a" * 64,
        "production_shard_map_receipt_sha256": "b" * 64,
        "preflight_gate_summary_sha256": preflight_summary_raw_sha256,
        "power_threshold_receipt_sha256": "d" * 64,
        "freeze_receipt_sha256": "e" * 64,
        "independent_signoff_sha256": independent_signoff_raw_sha256,
        "authorized_attempt_number": 1,
        "authorization_issued_at_utc": "2026-01-01T00:00:00.000000Z",
        "authorization_expires_at_utc": "2026-01-01T01:00:00.000000Z",
        "authority_scheme_id": scheme,
        "authority_identity_sha256": identity,
        "authority_signature_hex": "",
        "authority_signature_sha256": _ZERO_SHA256,
        "body_sha256": _ZERO_SHA256,
    }
    signature = _test_rsa_pss_signature(
        b"cp65-test28-launch-authorization-signature-preimage-v1\0"
        + _canonical_json(receipt),
        "launch-authorization",
    )
    if corrupt_signature:
        signature = bytes((signature[0] ^ 1,)) + signature[1:]
    receipt["authority_signature_hex"] = signature.hex()
    receipt["authority_signature_sha256"] = hashlib.sha256(signature).hexdigest()
    return _receipt_payload("launch-authorization", receipt), key_payload


def _seed_source_attestation_pair(
    *, corrupt_signature: bool = False
) -> tuple[bytes, bytes]:
    scheme = "rsa-pss-sha256-3072-e65537-salt32-v1"
    key = {
        "schema": "cp65-test28-seed-source-authority-public-key-v1",
        "purpose": "seed-source-authority-public-key-custody",
        "source_authority_scheme_id": scheme,
        "source_authority_id": "cp65-test-seed-source-authority",
        "modulus_hex": _TEST_RSA_N.to_bytes(384, "big").hex(),
        "public_exponent": 65_537,
        "valid_from_utc": "2025-01-01T00:00:00.000000Z",
        "valid_until_utc": "2030-01-01T00:00:00.000000Z",
        "body_sha256": _ZERO_SHA256,
    }
    key_payload = _receipt_payload("seed-source-authority-public-key", key)
    identity = hashlib.sha256(
        b"cp65-test28-seed-source-authority-public-key-identity-v1\0"
        + _canonical_json(
            {
                "source_authority_scheme_id": scheme,
                "source_authority_id": key["source_authority_id"],
                "modulus_hex": key["modulus_hex"],
                "public_exponent": 65_537,
            }
        )
    ).hexdigest()
    receipt = {
        "schema": "cp65-test28-seed-source-authority-attestation-v1",
        "purpose": "external-seed-source-authority-attestation",
        "attempt_id": "attempt-development-only",
        "freeze_receipt_sha256": "1" * 64,
        "acquisition_start_receipt_sha256": "2" * 64,
        "acquisition_journal_sha256": "3" * 64,
        "acquisition_journal_head_sha256": "4" * 64,
        "acquisition_journal_entry_count": 2_048,
        "ordered_seed_values_commitment_sha256": "5" * 64,
        "seed_source_custody_artifact_sha256": "6" * 64,
        "source_method_id": "cp65-test-external-source",
        "source_authority_scheme_id": scheme,
        "source_authority_identity_sha256": identity,
        "attested_at_utc": "2026-01-01T00:00:00.000000Z",
        "attestation_expires_at_utc": "2026-01-01T01:00:00.000000Z",
        "source_authority_signature_hex": "",
        "source_authority_signature_sha256": _ZERO_SHA256,
        "body_sha256": _ZERO_SHA256,
    }
    signature = _test_rsa_pss_signature(
        b"cp65-test28-seed-source-authority-attestation-signature-preimage-v1\0"
        + _canonical_json(receipt),
        "seed-source-attestation",
    )
    if corrupt_signature:
        signature = signature[:-1] + bytes((signature[-1] ^ 1,))
    receipt["source_authority_signature_hex"] = signature.hex()
    receipt["source_authority_signature_sha256"] = hashlib.sha256(signature).hexdigest()
    return _receipt_payload("seed-source-authority-attestation", receipt), key_payload


def _power_review_signoff_pair(
    *, corrupt_signature: bool = False
) -> tuple[bytes, bytes]:
    key_set_payload, key_rows = _reviewer_key_set_payload()
    key = next(
        row
        for row in key_rows
        if row["reviewer_role"] == "statistical-power-and-decision-reviewer"
    )
    row_digests = [
        hashlib.sha256(("slot:%d" % ordinal).encode()).hexdigest()
        for ordinal in range(1, 33)
    ]
    receipt = {
        "schema": "cp65-test28-power-review-signoff-v1",
        "purpose": "signed-power-review-custody",
        "attempt_id": "attempt-development-only",
        "protocol_sha256": "1" * 64,
        "machine_manifest_sha256": "2" * 64,
        "power_review_sha256": "3" * 64,
        "selected_count_justification_sha256": "4" * 64,
        "primary_slot_count": 32,
        "ordered_slot_threshold_row_sha256s": row_digests,
        "ordered_slot_thresholds_sha256": "5" * 64,
        "reviewer_role": key["reviewer_role"],
        "reviewer_identity_sha256": key["reviewer_identity_sha256"],
        "reviewer_public_key_identity_sha256": key["public_key_identity_sha256"],
        "decision": "APPROVE",
        "signed_at_utc": "2026-01-01T00:00:00.000000Z",
        "signature_scheme_id": key["signature_scheme_id"],
        "reviewer_signature_sha256": _ZERO_SHA256,
        "reviewer_signature_hex": "",
        "body_sha256": _ZERO_SHA256,
    }
    signature = _test_rsa_pss_signature(
        b"cp65-test28-power-review-signoff-signature-preimage-v1\0"
        + _canonical_json(receipt),
        "power-review-signoff",
    )
    if corrupt_signature:
        signature = bytes((signature[0] ^ 1,)) + signature[1:]
    receipt["reviewer_signature_hex"] = signature.hex()
    receipt["reviewer_signature_sha256"] = hashlib.sha256(signature).hexdigest()
    return _receipt_payload("power-review-signoff", receipt), key_set_payload


def _preflight_summary_payload() -> bytes:
    requirements = cp65._build_gate_requirements()[:15]
    return _receipt_payload(
        "preflight-gate-summary",
        {
            "schema": "cp65-test28-preflight-gate-summary-v2",
            "purpose": "preauthorization-gates-1-through-15-summary",
            "attempt_id": "attempt-development-only",
            "freeze_receipt_sha256": "1" * 64,
            "covered_gate_ids": [row.gate_id for row in requirements],
            "covered_gate_states": ["PASS"] * 15,
            "covered_evidence_node_ids": [row.evidence_node_id for row in requirements],
            "ordered_evidence_receipt_sha256s": [
                hashlib.sha256(
                    ("cp65-test-evidence:" + row.evidence_artifact_id).encode("ascii")
                ).hexdigest()
                for row in requirements
            ],
            "external_digest_preimage_registry_sha256": "2" * 64,
            "body_sha256": _ZERO_SHA256,
        },
    )


def _independent_signoff_set_payload(
    summary_payload: bytes,
    key_set_payload: bytes,
    key_rows: tuple[dict, ...],
    *,
    duplicate_role: bool = False,
    empty_reviewed: bool = False,
    false_derived_booleans: bool = False,
    corrupt_signature: bool = False,
) -> bytes:
    summary_raw = hashlib.sha256(summary_payload).hexdigest()
    signoffs = []
    for ordinal, original_key in enumerate(key_rows, 1):
        key = key_rows[0] if duplicate_role and ordinal == 2 else original_key
        row = {
            "reviewer_role": key["reviewer_role"],
            "reviewer_identity_sha256": key["reviewer_identity_sha256"],
            "reviewer_public_key_identity_sha256": key["public_key_identity_sha256"],
            "reviewed_artifact_sha256s": [] if empty_reviewed else [summary_raw],
            "decision": "APPROVE",
            "signed_at_utc": "2026-01-01T00:00:00.000004Z",
            "signature_scheme_id": "rsa-pss-sha256-3072-e65537-salt32-v1",
            "reviewer_signature_sha256": _ZERO_SHA256,
            "reviewer_signature_hex": "",
            "signoff_sha256": _ZERO_SHA256,
        }
        message = (
            b"cp65-test28-independent-signoff-row-signature-preimage-v1\0"
            + _canonical_json(row)
        )
        signature = _test_rsa_pss_signature(message, "independent-signoff-%d" % ordinal)
        if corrupt_signature and ordinal == 1:
            signature = bytes((signature[0] ^ 1,)) + signature[1:]
        row["reviewer_signature_hex"] = signature.hex()
        row["reviewer_signature_sha256"] = hashlib.sha256(signature).hexdigest()
        row["signoff_sha256"] = hashlib.sha256(
            b"cp65-test28-independent-signoff-row-v1\0" + _canonical_json(row)
        ).hexdigest()
        signoffs.append(row)
    all_true = not false_derived_booleans
    return _receipt_payload(
        "independent-signoff-set",
        {
            "schema": "cp65-test28-independent-signoff-set-v1",
            "purpose": "independent-preauthorization-signoff-set",
            "attempt_id": "attempt-development-only",
            "freeze_receipt_sha256": "1" * 64,
            "preflight_gate_summary_sha256": summary_raw,
            "reviewer_public_key_set_sha256": hashlib.sha256(
                key_set_payload
            ).hexdigest(),
            "required_reviewer_roles": list(cp65._REQUIRED_REVIEWER_ROLES),
            "ordered_signoffs": signoffs,
            "signoff_count": 4,
            "all_required_roles_present": all_true,
            "all_decisions_approve": all_true,
            "all_signatures_mathematically_valid_under_declared_keys": all_true,
            "body_sha256": _ZERO_SHA256,
        },
    )


def _external_digest_registry_payload(
    *,
    preimage_ascii: str = "capacity-observation-session-001",
    digest_kind: str = "plain-sha256",
    domain_separator: str = "",
    target_artifact_raw_sha256: str = "a" * 64,
) -> bytes:
    decoded = preimage_ascii.encode("ascii")
    digest_input = (
        decoded
        if digest_kind == "plain-sha256"
        else domain_separator.encode("ascii") + decoded
    )
    entry = {
        "ordinal": 1,
        "classification_id": (
            "sha256-pointer:capacity-receipt:/measurement_session_sha256"
        ),
        "target_artifact_id": "capacity-receipt",
        "target_relative_path": "capacity_receipt.json",
        "target_json_pointer": "/measurement_session_sha256",
        "target_instance_selector_json_ascii": _canonical_json(
            {
                "artifact_instance_ordinal": 1,
                "shard_ordinal": 0,
                "wildcard_indices": [],
            }
        ).decode("ascii"),
        "target_artifact_raw_sha256": target_artifact_raw_sha256,
        "digest_kind": digest_kind,
        "domain_separator": domain_separator,
        "preimage_encoding": "ascii",
        "preimage_bytes": len(decoded),
        "preimage_ascii": preimage_ascii,
        "digest_sha256": hashlib.sha256(digest_input).hexdigest(),
        "entry_sha256": _ZERO_SHA256,
    }
    entry["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-external-digest-preimage-registry-entry-v1\0"
        + _canonical_json(entry)
    ).hexdigest()
    ordered = hashlib.sha256(
        b"cp65-test28-external-digest-preimage-registry-ordered-entries-v1\0"
        + bytes.fromhex(entry["entry_sha256"])
    ).hexdigest()
    return _receipt_payload(
        "external-digest-preimage-registry",
        {
            "schema": "cp65-test28-external-digest-preimage-registry-v1",
            "purpose": (
                "post-gate15-pre-summary-bounded-external-digest-preimage-custody"
            ),
            "attempt_id": "attempt-development-only",
            "protocol_sha256": (
                "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8"
            ),
            "machine_manifest_sha256": (
                "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
            ),
            "schema_semantic_sha256": (
                cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256
            ),
            "entry_count": 1,
            "entries": [entry],
            "ordered_entry_sha256s": [entry["entry_sha256"]],
            "ordered_entries_sha256": ordered,
            "finalized_at_utc": "2026-01-01T00:00:00.000001Z",
            "body_sha256": _ZERO_SHA256,
        },
    )


def _capacity_receipt_payload(measurement_session_sha256: str) -> bytes:
    fixed_hashes = {
        "schedule_sha256": "1" * 64,
        "capacity_schema_sha256": "2" * 64,
        "storage_root_identity_sha256": "3" * 64,
        "filesystem_identity_sha256": "4" * 64,
        "measurement_session_sha256": measurement_session_sha256,
        "auxiliary_metadata_reservation_artifact_sha256": "5" * 64,
        "auxiliary_artifact_size_proof_sha256": "6" * 64,
        "reservation_manifest_sha256": "7" * 64,
    }
    document = {
        "schema": "cp65-test28-capacity-receipt-v2",
        "purpose": "production-capacity-and-exclusive-reservation-observation",
        "attempt_id": "attempt-development-only",
        "destination_reservation_required_bytes": 1_099_511_627_776,
        "auxiliary_metadata_reservation_required_bytes": 34_359_738_368,
        "combined_available_and_quota_required_before_reservation_bytes": (
            1_133_871_366_144
        ),
        "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes": (
            34_359_738_368
        ),
        **fixed_hashes,
        "measured_at_utc": "2026-01-01T00:00:00.000000Z",
        "measurement_method_id": "cp65-test-capacity-measurement",
        "quota_method_id": "cp65-test-quota-measurement",
        "reservation_method_id": "cp65-test-destination-reservation",
        "auxiliary_metadata_reservation_method_id": "cp65-test-aux-reservation",
        "allocation_unit_bytes": 4_096,
        "available_bytes_before_reservation": 1_133_871_366_144,
        "quota_headroom_bytes_before_reservation": 1_133_871_366_144,
        "physically_allocated_reservation_bytes": 1_099_511_627_776,
        "physically_allocated_auxiliary_metadata_bytes": 34_359_738_368,
        "auxiliary_metadata_reserved_quota_bytes": 34_359_738_368,
        "usable_reserved_bytes_after_allocation": 1_099_511_627_776,
        "available_bytes_after_reservation": 34_359_738_368,
        "quota_headroom_bytes_after_reservation": 34_359_738_368,
        "available_inodes_after_reservation": 1_024,
        "non_sparse_allocation_verified": True,
        "reservation_same_filesystem_verified": True,
        "reservation_exclusive_verified": True,
        "reservation_durable_verified": True,
        "auxiliary_metadata_reservation_exclusive_verified": True,
        "auxiliary_metadata_non_sparse_allocation_verified": True,
        "auxiliary_metadata_reserved_quota_verified": True,
        "auxiliary_metadata_reservation_durable_verified": True,
        "auxiliary_metadata_reservation_same_storage_root_verified": True,
        "destination_and_auxiliary_reservation_no_double_count_verified": True,
        "shard_count": 32,
        "atomic_rename_supported": True,
        "file_fsync_supported": True,
        "directory_fsync_supported": True,
        "maximum_auxiliary_artifact_logical_bytes": 21_845_344_321,
        "maximum_auxiliary_reserved_bytes": 23_286_841_344,
        "allocation_and_directory_charge_policy_slot_bytes": 1_073_741_824,
        "observed_allocation_and_directory_charge_bytes": 1_073_741_824,
        "allocation_and_directory_charge_within_policy": True,
        "body_sha256": _ZERO_SHA256,
    }
    return _receipt_payload("capacity-receipt", document)


def _source_materialization(entries: tuple[tuple[str, bytes], ...]) -> bytes:
    framed = bytearray(b"CP65SRC1")
    framed.extend(len(entries).to_bytes(4, "big"))
    for path, content in entries:
        encoded_path = path.encode("ascii")
        framed.extend(len(encoded_path).to_bytes(4, "big"))
        framed.extend(encoded_path)
        framed.extend(len(content).to_bytes(8, "big"))
        framed.extend(hashlib.sha256(content).digest())
        framed.extend(content)
    framed.extend(
        hashlib.sha256(
            b"cp65-test28-frozen-source-fixture-materialization-v1\0" + bytes(framed)
        ).digest()
    )
    return bytes(framed)


def _auxiliary_slot_rows() -> list[dict]:
    declarations = {row[0]: row for row in cp65._ARTIFACT_DECLARATIONS}
    bounds = {row.artifact_id: row for row in cp65._build_auxiliary_bounds()}
    slots = []
    for artifact_id, declaration in declarations.items():
        if artifact_id in cp65._DESTINATION_IDS or artifact_id == (
            "rejected-launch-authorization-candidate"
        ):
            continue
        if declaration[2] == "per-shard":
            for shard_ordinal in range(1, 33):
                path = declaration[1].replace(
                    "{shard_id}", "shard-%04d" % shard_ordinal
                )
                slots.append((path, artifact_id))
        else:
            slots.append((declaration[1], artifact_id))
    assert len(slots) == 183
    rows = []
    for ordinal, (path, artifact_id) in enumerate(sorted(slots), 1):
        bound = bounds[artifact_id]
        is_committed = artifact_id == "committed-marker"
        is_transition_journal = (
            artifact_id == "auxiliary-reservation-transition-journal"
        )
        is_prepared_authorization = artifact_id == "launch-authorization"
        row = {
            "ordinal": ordinal,
            "artifact_id": artifact_id,
            "final_relative_path": path,
            "alternate_final_relative_path": (
                "rejected_launch_authorization_candidate.json"
                if is_prepared_authorization
                else ""
            ),
            "reservation_state": (
                "future-o-excl-covered-by-hold"
                if is_committed
                else (
                    "preallocated-live-journal-in-place"
                    if is_transition_journal
                    else "preallocated-partial-in-place"
                )
            ),
            "partial_relative_path": (
                ""
                if is_committed
                else path
                if is_transition_journal
                else path + ".partial"
            ),
            "primary_publication_arm_id": (
                "DIRECT_O_EXCL_AFTER_HOLD_RELEASE"
                if is_committed
                else (
                    "IN_PLACE_TRANSITION_JOURNAL"
                    if is_transition_journal
                    else "AUTHORIZATION"
                    if is_prepared_authorization
                    else "UNCONDITIONAL"
                )
            ),
            "alternate_publication_arm_id": (
                "PREAUTHORIZATION_TERMINAL" if is_prepared_authorization else ""
            ),
            "device_identity_sha256": _ZERO_SHA256 if is_committed else "d" * 64,
            "inode": 0 if is_committed else ordinal,
            "extent_map_sha256": (
                _ZERO_SHA256
                if is_committed
                else hashlib.sha256(("extent:" + path).encode("ascii")).hexdigest()
            ),
            "maximum_logical_bytes": bound.maximum_logical_bytes_per_instance,
            "reserved_bytes": bound.maximum_reserved_bytes_per_instance,
            "non_sparse_verified": not is_committed,
            "exclusive_verified": not is_committed,
            "file_fsync_completed_at_utc": (
                "" if is_committed else "2026-01-01T00:00:00.000001Z"
            ),
            "directory_fsync_completed_at_utc": (
                "" if is_committed else "2026-01-01T00:00:00.000002Z"
            ),
            "entry_sha256": _ZERO_SHA256,
        }
        zeroed = dict(row)
        row["entry_sha256"] = hashlib.sha256(
            b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0"
            + _canonical_json(zeroed)
        ).hexdigest()
        rows.append(row)
    return rows


def _auxiliary_reservation_document() -> dict:
    rows = _auxiliary_slot_rows()
    slot_bytes = sum(row["reserved_bytes"] for row in rows)
    allocated_future_bytes = sum(
        row["reserved_bytes"]
        for row in rows
        if row["reservation_state"]
        in ("preallocated-partial-in-place", "preallocated-live-journal-in-place")
    )
    charge_bytes = 1_073_741_824
    hold_bytes = 34_359_738_368 - allocated_future_bytes - charge_bytes
    document = {
        "schema": "cp65-test28-auxiliary-metadata-reservation-v3",
        "purpose": "exclusive-dynamic-auxiliary-reservation",
        "attempt_id": "attempt-development-only",
        "freeze_receipt_sha256": "1" * 64,
        "schedule_sha256": "2" * 64,
        "capacity_schema_sha256": "3" * 64,
        "measurement_session_sha256": "4" * 64,
        "exclusive_root_charge_measurement_sha256": _ZERO_SHA256,
        "storage_root_identity_sha256": "5" * 64,
        "filesystem_identity_sha256": "6" * 64,
        "reservation_method_id": "o-excl-in-place-plus-dynamic-hold-and-quota",
        "allocation_unit_bytes": 4_096,
        "artifact_entry_count": 183,
        "artifact_entries": rows,
        "artifact_slot_reserved_bytes": slot_bytes,
        "allocated_existing_final_bytes": 0,
        "allocated_future_partial_bytes": allocated_future_bytes,
        "unique_nonhold_artifact_allocated_bytes": allocated_future_bytes,
        "exclusive_root_charge_baseline_bytes": 8_589_934_592,
        "exclusive_root_charge_current_bytes": (
            8_589_934_592 + allocated_future_bytes + hold_bytes + charge_bytes
        ),
        "disjoint_allocation_and_directory_charge_bytes": charge_bytes,
        "hold_relative_path": ".cp65_auxiliary_reservation_hold.partial",
        "hold_device_identity_sha256": "d" * 64,
        "hold_inode": 10_000,
        "hold_extent_map_sha256": hashlib.sha256(b"extent:hold").hexdigest(),
        "hold_allocated_bytes": hold_bytes,
        "allocation_and_directory_charge_policy_slot_bytes": charge_bytes,
        "exclusive_reserved_headroom_bytes": 11_072_897_024,
        "physical_reservation_sum_bytes": 34_359_738_368,
        "enforced_quota_bytes": 34_359_738_368,
        "exclusive_verified": True,
        "non_sparse_verified": True,
        "durable_verified": True,
        "same_root_verified": True,
        "created_at_utc": "2026-01-01T00:00:00.000003Z",
        "body_sha256": _ZERO_SHA256,
    }
    _refinish_exclusive_root_charge_measurement(document)
    return document


def _make_auxiliary_slot_existing(
    document: dict, artifact_id: str, allocated_bytes: int
) -> dict:
    """Move one initially preallocated row into the exact initial-final arm."""

    row = next(
        item
        for item in document["artifact_entries"]
        if item["artifact_id"] == artifact_id
    )
    assert row["reservation_state"] == "preallocated-partial-in-place"
    assert 0 < allocated_bytes <= row["reserved_bytes"]
    original_reserved = row["reserved_bytes"]
    row["reservation_state"] = "existing-final-in-place"
    row["partial_relative_path"] = ""
    row["reserved_bytes"] = allocated_bytes
    zeroed = dict(row)
    zeroed["entry_sha256"] = _ZERO_SHA256
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0"
        + _canonical_json(zeroed)
    ).hexdigest()
    document["allocated_future_partial_bytes"] -= original_reserved
    document["allocated_existing_final_bytes"] += allocated_bytes
    document["unique_nonhold_artifact_allocated_bytes"] = (
        document["allocated_existing_final_bytes"]
        + document["allocated_future_partial_bytes"]
    )
    document["hold_allocated_bytes"] += original_reserved - allocated_bytes
    document["exclusive_root_charge_current_bytes"] = (
        document["exclusive_root_charge_baseline_bytes"]
        + document["unique_nonhold_artifact_allocated_bytes"]
        + document["hold_allocated_bytes"]
        + document["disjoint_allocation_and_directory_charge_bytes"]
    )
    _refinish_exclusive_root_charge_measurement(document)
    return row


def _refinish_exclusive_root_charge_measurement(document: dict) -> None:
    preimage = {
        "schema": "cp65-test28-exclusive-root-charge-measurement-v1",
        "attempt_id": document["attempt_id"],
        "measurement_session_sha256": document["measurement_session_sha256"],
        "storage_root_identity_sha256": document["storage_root_identity_sha256"],
        "filesystem_identity_sha256": document["filesystem_identity_sha256"],
        "exclusive_root_charge_baseline_bytes": document[
            "exclusive_root_charge_baseline_bytes"
        ],
        "exclusive_root_charge_current_bytes": document[
            "exclusive_root_charge_current_bytes"
        ],
        "unique_nonhold_artifact_allocated_bytes": document[
            "unique_nonhold_artifact_allocated_bytes"
        ],
        "hold_allocated_bytes": document["hold_allocated_bytes"],
        "disjoint_allocation_and_directory_charge_bytes": document[
            "disjoint_allocation_and_directory_charge_bytes"
        ],
    }
    document["exclusive_root_charge_measurement_sha256"] = hashlib.sha256(
        b"cp65-test28-exclusive-root-charge-measurement-v1\0"
        + _canonical_json(preimage)
    ).hexdigest()


def _auxiliary_transition_journal(
    auxiliary_receipt_payload: bytes,
    schema_semantic_sha256: str,
    transitions: tuple[tuple[int, int, int, int, int, int, str, str], ...] = (),
) -> tuple[bytes, str]:
    """Build the frozen 64-KiB chained transition journal."""

    receipt_raw = hashlib.sha256(auxiliary_receipt_payload).digest()
    semantic = bytes.fromhex(schema_semantic_sha256)
    head = hashlib.sha256(
        b"cp65-test28-auxiliary-reservation-transition-head-v1\0"
        + receipt_raw
        + semantic
    ).digest()
    output = bytearray(65_536)
    output[0:8] = b"CP65AUX1"
    output[8:16] = (1).to_bytes(8, "big")
    output[16:48] = receipt_raw
    output[48:80] = semantic
    output[80:112] = head
    output[112:120] = (255).to_bytes(8, "big")
    output[120:128] = (256).to_bytes(8, "big")
    for ordinal, transition in enumerate(transitions, 1):
        (
            artifact_slot_ordinal,
            transition_code,
            allocated_before,
            allocated_after,
            hold_before,
            hold_after,
            target_path_sha256,
            target_raw_sha256,
        ) = transition
        slot = bytearray(256)
        slot[0:8] = ordinal.to_bytes(8, "big")
        slot[8:16] = artifact_slot_ordinal.to_bytes(8, "big")
        slot[16:24] = transition_code.to_bytes(8, "big")
        slot[24:32] = allocated_before.to_bytes(8, "big")
        slot[32:40] = allocated_after.to_bytes(8, "big")
        slot[40:48] = hold_before.to_bytes(8, "big")
        slot[48:56] = hold_after.to_bytes(8, "big")
        slot[56:88] = bytes.fromhex(target_path_sha256)
        slot[88:120] = bytes.fromhex(target_raw_sha256)
        slot[120:152] = head
        head = hashlib.sha256(
            b"cp65-test28-auxiliary-reservation-transition-entry-v1\0"
            + receipt_raw
            + bytes(slot[:152])
        ).digest()
        slot[152:184] = head
        output[ordinal * 256 : (ordinal + 1) * 256] = slot
    return bytes(output), head.hex()


def _validate_auxiliary_transition_pair(
    document: dict,
    transitions: tuple[tuple[int, int, int, int, int, int, str, str], ...],
    *,
    extra_items: tuple[tuple[str, str, bytes], ...] = (),
) -> cp65.CP65SuppliedValidationV1:
    auxiliary_payload = _receipt_payload("auxiliary-metadata-reservation", document)
    journal, _head = _auxiliary_transition_journal(
        auxiliary_payload,
        cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
        transitions,
    )
    return cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "auxiliary-metadata-reservation",
                "auxiliary_metadata_reservation.json",
                auxiliary_payload,
            ),
            (
                "auxiliary-reservation-transition-journal",
                "auxiliary_reservation_transition_journal.bin",
                journal,
            ),
        )
        + extra_items
    )


def _seed_sequence_commitment(seed_values: tuple[str, ...]) -> str:
    return hashlib.sha256(
        b"cp64-test28-ordered-seed-sequence-v1\0"
        + _canonical_json(
            {
                "seed_count": len(seed_values),
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "ordered_seed_values": list(seed_values),
            }
        )
    ).hexdigest()


def _acquisition_start_payload() -> bytes:
    return _receipt_payload(
        "external-seed-acquisition-start-receipt",
        {
            "schema": "cp64-test28-external-seed-acquisition-start-receipt-v1",
            "purpose": "durable-start-before-external-source-contact",
            "attempt_id": "attempt-development-only",
            "freeze_receipt_sha256": "1" * 64,
            "source_method_id": "external-iid-uniform-uint64-with-replacement",
            "acquisition_journal_relative_path": "seed_acquisition_journal.bin",
            "acquisition_journal_device_identity_sha256": "2" * 64,
            "acquisition_journal_inode": 7,
            "acquisition_journal_preallocated_bytes": 163_840,
            "acquisition_journal_allocation_method_id": "o-excl-zero-fill-fsync",
            "acquisition_journal_extent_map_sha256": "3" * 64,
            "acquisition_journal_file_fsync_completed_at_utc": (
                "2026-01-01T00:00:00.000001Z"
            ),
            "acquisition_journal_directory_fsync_completed_at_utc": (
                "2026-01-01T00:00:00.000002Z"
            ),
            "acquisition_journal_inode_recheck_sha256": "4" * 64,
            "acquisition_session_id": "external-session-development-only",
            "started_at_utc": "2026-01-01T00:00:00.000003Z",
            "body_sha256": _ZERO_SHA256,
        },
    )


def _journal_with_values(
    start_body_sha256: str, values: tuple[int, ...]
) -> tuple[bytes, str]:
    start_digest = bytes.fromhex(start_body_sha256)
    previous = hashlib.sha256(
        b"cp64-external-seed-acquisition-journal-head-v1\0" + start_digest
    ).digest()
    framed = bytearray()
    for ordinal, value in enumerate(values, 1):
        ordinal_bytes = ordinal.to_bytes(8, "big")
        value_bytes = value.to_bytes(8, "big")
        entry_digest = hashlib.sha256(
            b"cp64-external-seed-acquisition-journal-entry-v1\0"
            + start_digest
            + ordinal_bytes
            + value_bytes
            + previous
        ).digest()
        framed.extend(ordinal_bytes + value_bytes + previous + entry_digest)
        previous = entry_digest
    framed.extend(b"\0" * (163_840 - len(framed)))
    return bytes(framed), previous.hex()


def _partial_acquisition_payload(
    start_body_sha256: str,
    journal: bytes,
    head_sha256: str,
    values: tuple[int, ...],
) -> bytes:
    encoded_values = tuple("%016x" % value for value in values)
    return _receipt_payload(
        "partial-seed-acquisition-terminal-receipt",
        {
            "schema": "cp64-test28-partial-acquisition-terminal-receipt-v1",
            "purpose": "terminal-custody-of-recovered-prefix",
            "attempt_id": "attempt-development-only",
            "freeze_receipt_sha256": "1" * 64,
            "acquisition_start_receipt_sha256": start_body_sha256,
            "source_method_id": "external-iid-uniform-uint64-with-replacement",
            "expected_seed_count": 2_048,
            "acquired_seed_count": len(values),
            "acquisition_journal_sha256": hashlib.sha256(journal).hexdigest(),
            "acquisition_journal_head_sha256": head_sha256,
            "acquisition_journal_entry_count": len(values),
            "acquisition_journal_raw_bytes": 163_840,
            "seed_encoding": "uint64-16-lowercase-hex-big-endian",
            "ordered_partial_seed_values": list(encoded_values),
            "ordered_partial_seed_values_commitment_sha256": (
                _seed_sequence_commitment(encoded_values)
            ),
            "terminal_state": "INCOMPLETE",
            "topup_redraw_reselection_permitted": False,
            "body_sha256": _ZERO_SHA256,
        },
    )


def _completed_source_receipt_payload(
    start_body_sha256: str,
    journal: bytes,
    head_sha256: str,
    values: tuple[int, ...],
) -> bytes:
    encoded_values = tuple("%016x" % value for value in values)
    return _receipt_payload(
        "external-seed-source-receipt",
        {
            "schema": "cp65-test28-external-seed-source-receipt-v2",
            "purpose": "completed-external-seed-source-custody",
            "attempt_id": "attempt-development-only",
            "freeze_receipt_sha256": "1" * 64,
            "cp61_stable_design_sha256": (
                "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
            ),
            "seed_count": 2_048,
            "seed_encoding": "uint64-16-lowercase-hex-big-endian",
            "source_method_id": "external-iid-uniform-uint64-with-replacement",
            "acquisition_start_receipt_sha256": start_body_sha256,
            "acquisition_session_sha256": start_body_sha256,
            "acquisition_journal_sha256": hashlib.sha256(journal).hexdigest(),
            "acquisition_journal_head_sha256": head_sha256,
            "acquisition_journal_entry_count": 2_048,
            "ordered_seed_values_commitment_sha256": (
                _seed_sequence_commitment(encoded_values)
            ),
            "custody_artifact_sha256": "5" * 64,
            "source_authority_attestation_sha256": "6" * 64,
            "body_sha256": _ZERO_SHA256,
        },
    )


_EXPECTED_FIELDS = {
    cp65.CP65PredecessorCustodyV1: (
        "schema_version",
        "cp64_schema_version",
        "cp64_source_relative_path",
        "cp64_source_sha256",
        "cp64_source_bytes",
        "cp64_source_lines",
        "cp64_test_relative_path",
        "cp64_test_sha256",
        "cp64_test_bytes",
        "cp64_test_lines",
        "v15_protocol_relative_path",
        "v15_protocol_sha256",
        "v15_protocol_bytes",
        "v15_protocol_lines",
        "v15_manifest_relative_path",
        "v15_manifest_sha256",
        "v15_manifest_bytes",
        "v15_manifest_lines",
        "cp64_bundle_record_sha256",
        "cp64_bundle_public_sha256",
        "cp64_bundle_canonical_json_sha256",
        "cp64_bundle_canonical_json_bytes",
        "cp64_no_execution_gate_contract_record_sha256",
        "cp64_false_schema_definition_flags",
        "cp64_gate_count",
        "cp64_evidence_present_count",
        "cp64_ledger_total_count",
        "cp64_ledger_satisfied_count",
        "cp64_ledger_missing_count",
        "v15_protocol_state",
        "v15_lifecycle_current_state",
        "v15_complete_production_roster_frozen",
        "formal_test_28_status",
        "formal_test_28_closed",
        "cp65_source_hashes_external_binding_required",
        "predecessor_only",
        "record_sha256",
    ),
    cp65.CP65FieldRuleV1: (
        "schema_version",
        "rule_id",
        "artifact_id",
        "json_pointer",
        "value_kind",
        "required",
        "integer_interval",
        "length_interval",
        "boolean_domain",
        "string_domain",
        "string_pattern_id",
        "array_item_rule_ids",
        "exact_object_keys",
        "cross_constraint_ids",
        "record_sha256",
    ),
    cp65.CP65ArtifactSchemaV1: (
        "schema_version",
        "artifact_id",
        "path_template",
        "path_scope",
        "presence_rule_id",
        "encoding",
        "media_kind",
        "exact_keys",
        "field_rule_ids",
        "record_rule_id",
        "minimum_instances",
        "maximum_instances",
        "minimum_bytes_per_instance",
        "maximum_bytes_per_instance",
        "final_newline_rule",
        "digest_preimage_contract_id",
        "dag_node_ids",
        "auxiliary_reservation_class",
        "cp64_contract_preserved",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65TransientPathContractV1: (
        "schema_version",
        "transient_ordinal",
        "transient_path_id",
        "owner_artifact_id",
        "final_relative_path",
        "alternate_final_relative_path",
        "transient_relative_path",
        "primary_publication_arm_id",
        "alternate_publication_arm_id",
        "path_scope",
        "shard_ordinal",
        "transient_kind",
        "aliases_final_inode_when_published",
        "prepared_authorization_alias",
        "retained_at_committed",
        "sha256_manifest_included",
        "collision_free",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65DigestPreimageContractV1: (
        "schema_version",
        "contract_id",
        "artifact_id",
        "digest_field_pointer",
        "algorithm_id",
        "domain_separator",
        "canonical_profile_id",
        "zeroed_field_pointers",
        "ordered_component_ids",
        "output_encoding",
        "output_bytes",
        "verifier_implemented",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65Sha256PointerContractV1: (
        "schema_version",
        "classification_id",
        "target_artifact_id",
        "target_json_pointer",
        "semantic_class",
        "digest_kind",
        "source_artifact_id",
        "source_json_pointer",
        "source_contract_id",
        "source_availability_cut_id",
        "instance_selector_id",
        "cardinality_rule_id",
        "preimage_encoding",
        "domain_separator",
        "zero_policy_id",
        "conditional_binding_rule_id",
        "externally_retained_preimage_required",
        "preimage_registry_entry_required",
        "validator_implemented",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65PredicateContractV1: (
        "schema_version",
        "predicate_id",
        "applies_to_artifact_ids",
        "input_json_pointers",
        "operation_id",
        "operand_json_ascii",
        "child_predicate_ids",
        "evaluation_order",
        "failure_code",
        "validator_implemented",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65GateRequirementV1: (
        "schema_version",
        "gate_ordinal",
        "gate_id",
        "evidence_node_id",
        "evidence_artifact_id",
        "required_artifact_ids",
        "predicate_id",
        "predicate_clause_ids",
        "preflight_summary_covered",
        "requires_external_provenance",
        "requires_independent_authority",
        "evidence_present",
        "gate_state",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65AuxiliaryArtifactBoundV1: (
        "schema_version",
        "bound_id",
        "artifact_id",
        "physical_slot_group_id",
        "mutually_exclusive_artifact_ids",
        "maximum_instance_count",
        "maximum_logical_bytes_per_instance",
        "maximum_reserved_bytes_per_instance",
        "maximum_total_reserved_bytes",
        "simultaneous_presence_rule_id",
        "reservation_partition_id",
        "destination_reservation_excluded",
        "record_sha256",
    ),
    cp65.CP65AuxiliarySizeProofV1: (
        "schema_version",
        "proof_id",
        "cp64_capacity_schema_record_sha256",
        "auxiliary_reservation_floor_bytes",
        "artifact_bound_ids",
        "covered_complete_roster_artifact_ids",
        "destination_artifact_ids",
        "maximum_auxiliary_artifact_logical_bytes",
        "maximum_auxiliary_artifact_slot_reserved_bytes",
        "allocation_and_directory_charge_policy_slot_bytes",
        "maximum_auxiliary_policy_required_bytes",
        "exclusive_reserved_policy_headroom_bytes",
        "maximum_dynamic_hold_bytes",
        "arithmetic_formula",
        "every_auxiliary_artifact_covered_exactly_once",
        "simultaneous_branch_upper_bound_conservative",
        "integer_arithmetic_verified",
        "fits_exclusive_auxiliary_reservation",
        "definition_only",
        "production_reservation_observed",
        "record_sha256",
    ),
    cp65.CP65AuthorizationSignatureContractV1: (
        "schema_version",
        "scheme_id",
        "public_key_artifact_id",
        "authorization_artifact_id",
        "hash_algorithm_id",
        "mgf_algorithm_id",
        "modulus_bytes",
        "modulus_bit_length",
        "public_exponent",
        "signature_bytes",
        "signature_hex_characters",
        "salt_bytes",
        "em_bits",
        "em_bytes",
        "trailer_field",
        "unused_high_bits",
        "signing_preimage_domain",
        "signing_preimage_zeroed_field_pointers",
        "signature_digest_formula",
        "public_key_identity_formula",
        "strict_pss_verification_steps",
        "signer_implemented",
        "key_generation_implemented",
        "public_key_present",
        "trust_root_bound",
        "signature_instance_present",
        "verifier_implemented",
        "authority_verified",
        "launch_authorized",
        "definition_only",
        "record_sha256",
    ),
    cp65.CP65SuppliedValidationV1: (
        "schema_version",
        "validation_scope",
        "caller_supplied_bytes_only",
        "input_artifact_ids",
        "input_relative_paths",
        "input_sha256s",
        "input_byte_lengths",
        "validated_artifact_ids",
        "validated_relative_paths",
        "validated_body_sha256s",
        "syntax_valid",
        "intrinsic_digest_preimages_valid",
        "all_required_digest_preimage_sources_supplied",
        "validated_digest_preimage_count",
        "unresolved_digest_preimage_count",
        "digest_preimages_valid",
        "all_required_cross_binding_targets_supplied",
        "validated_cross_binding_count",
        "unresolved_cross_binding_count",
        "cross_bindings_valid",
        "signature_verification_applicable",
        "signature_mathematically_valid_under_supplied_key",
        "parser_input_resource_limits_satisfied",
        "external_production_receipts_observed",
        "external_provenance_verified",
        "filesystem_observed",
        "source_authority_verified",
        "authorization_trust_root_bound",
        "authority_verified",
        "production_evidence_accepted",
        "gate_transition_permitted",
        "launch_authorized",
        "execution_permitted",
        "definition_only",
        "record_sha256",
    ),
}


def test_cp65_authoritative_surface_is_exactly_definition_only() -> None:
    assert cp65.CP65_TEST28_SCHEMA_VERSION == (
        "cp65-test28-production-schema-preimage-validator-v1"
    )
    assert "no-execution" in cp65.CP65_TEST28_SCOPE
    assert "no-authorization" in cp65.CP65_TEST28_SCOPE
    assert (
        tuple(
            inspect.signature(
                cp65.cp65_production_schema_preimage_validator_bundle
            ).parameters
        )
        == ()
    )
    assert tuple(
        inspect.signature(cp65.cp65_validate_supplied_artifact_bytes).parameters
    ) == ("artifact_id", "relative_path", "payload")


def test_cp65_authoritative_public_surface_has_no_execution_entrypoint() -> None:
    allowed_verifiers = {"cp65_verify_launch_authorization_signature"}
    forbidden = (
        "sign",
        "keygen",
        "issuer",
        "run",
        "execute",
        "materialize",
        "transition",
    )
    public_names = set(cp65.__all__)
    assert "cp65_verify_launch_authorization_signature" in public_names
    assert "cp65_verify_independent_signoff_signature" not in public_names
    assert "cp65_verify_seed_source_authority_attestation_signature" not in public_names
    for name in public_names:
        if name in allowed_verifiers:
            continue
        if not inspect.isfunction(getattr(cp65, name)):
            continue
        lowered = name.lower()
        assert not any(token in lowered for token in forbidden)


def test_cp65_records_use_manual_slots_for_python39() -> None:
    for name in cp65.__all__:
        value = getattr(cp65, name)
        if inspect.isclass(value) and name.startswith("CP65"):
            assert "__slots__" in value.__dict__
            assert "__dict__" not in value.__dict__


@pytest.mark.parametrize("record_type, expected", tuple(_EXPECTED_FIELDS.items()))
def test_cp65_record_field_order_is_exact(record_type: type, expected: tuple) -> None:
    assert tuple(field.name for field in fields(record_type)) == expected


def test_cp65_bounded_parser_accepts_one_exact_canonical_object() -> None:
    assert cp65._parse_canonical_json_object(b'{"a":1}', 1024) == {"a": 1}


def test_cp65_frozen_predecessor_inputs_accept_only_exact_immutable_live_bytes() -> None:
    protocol = (
        _PROJECT_ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
    ).read_bytes()
    machine_manifest = (
        _PROJECT_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    ).read_bytes()
    dependency_lock = (
        _PROJECT_ROOT / "requirements/m1-reference-macos-arm64-py311.lock"
    ).read_bytes()
    protocol_sha256 = hashlib.sha256(protocol).hexdigest()
    manifest_sha256 = hashlib.sha256(machine_manifest).hexdigest()
    lock_sha256 = hashlib.sha256(dependency_lock).hexdigest()
    assert (len(protocol), protocol.count(b"\n"), protocol_sha256) == (
        125_063,
        2_265,
        "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8",
    )
    assert (len(machine_manifest), machine_manifest.count(b"\n"), manifest_sha256) == (
        2_038_189,
        39_046,
        "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376",
    )
    parsed_machine_manifest = json.loads(machine_manifest)
    assert (
        _json_pointer(
            parsed_machine_manifest,
            "/diagnostic_contracts/runtime_conditional_finite_precision_arithmetic/"
            "source_law_boundary/product_uniform_comparison_support",
        )
        == 2**128
    )
    assert (len(dependency_lock), lock_sha256) == (
        736,
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
    )
    exact = (
        ("frozen-protocol", "frozen_inputs/protocol.md", protocol),
        (
            "frozen-protocol-sha256",
            "frozen_inputs/protocol.sha256",
            protocol_sha256.encode("ascii") + b"\n",
        ),
        (
            "frozen-machine-manifest",
            "frozen_inputs/machine_manifest.json",
            machine_manifest,
        ),
        ("dependency-lock", "frozen_inputs/dependency_lock.txt", dependency_lock),
    )
    for artifact_id, relative_path, payload in exact:
        result = cp65.cp65_validate_supplied_artifact_bytes(
            artifact_id, relative_path, payload
        )
        assert result.syntax_valid and result.intrinsic_digest_preimages_valid

    forged_manifest = json.loads(machine_manifest)
    forged_manifest["cp65_test_only_forged_leaf"] = "f" * 64
    mutations = (
        ("frozen-protocol", "frozen_inputs/protocol.md", protocol[:-1] + b"x"),
        (
            "frozen-protocol-sha256",
            "frozen_inputs/protocol.sha256",
            _ZERO_SHA256.encode("ascii") + b"\n",
        ),
        (
            "frozen-machine-manifest",
            "frozen_inputs/machine_manifest.json",
            _canonical_json(forged_manifest),
        ),
        (
            "dependency-lock",
            "frozen_inputs/dependency_lock.txt",
            dependency_lock[:-1] + bytes((dependency_lock[-1] ^ 1,)),
        ),
    )
    for artifact_id, relative_path, payload in mutations:
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                artifact_id, relative_path, payload
            )


def test_cp65_pinned_predecessor_manifest_has_a_separate_exact_resource_profile() -> None:
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_NODES == 37_036
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_DECODED_STRING_CHARACTERS == 1_280_910
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_OBJECT_MEMBERS == 111
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_DEPTH == 11
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_ABSOLUTE == 2**128
    assert cp65._PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_DIGITS == 39
    payload = (
        _PROJECT_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    ).read_bytes()
    parsed = cp65._parse_pinned_predecessor_manifest(payload)
    assert cp65._validate_pinned_predecessor_manifest_resources(parsed) == (
        37_036,
        1_280_910,
        11,
        111,
        2**128,
        39,
    )

    at_node_cap = {"a": [False] * 37_034}
    assert cp65._validate_pinned_predecessor_manifest_resources(at_node_cap)[0] == (
        37_036
    )
    with pytest.raises(ValueError):
        cp65._validate_pinned_predecessor_manifest_resources({"a": [False] * 37_035})

    at_character_cap = {"a": "x" * 640_000, "b": "y" * 640_908}
    assert (
        cp65._validate_pinned_predecessor_manifest_resources(at_character_cap)[1]
        == 1_280_910
    )
    at_character_cap["b"] += "z"
    with pytest.raises(ValueError):
        cp65._validate_pinned_predecessor_manifest_resources(at_character_cap)

    assert (
        cp65._validate_pinned_predecessor_manifest_resources(
            {"k%03d" % index: False for index in range(111)}
        )[3]
        == 111
    )
    with pytest.raises(ValueError):
        cp65._validate_pinned_predecessor_manifest_resources(
            {"k%03d" % index: False for index in range(112)}
        )

    at_depth: object = False
    for _level in range(10):
        at_depth = [at_depth]
    assert cp65._validate_pinned_predecessor_manifest_resources(at_depth)[2] == 11
    too_deep = [at_depth]
    with pytest.raises(ValueError):
        cp65._validate_pinned_predecessor_manifest_resources(too_deep)
    assert cp65._validate_pinned_predecessor_manifest_resources({"n": 2**128})[
        4:
    ] == (2**128, 39)
    for forbidden in (2**128 + 1, -(2**128) - 1):
        with pytest.raises(ValueError):
            cp65._validate_pinned_predecessor_manifest_resources({"n": forbidden})


def test_cp65_freeze_crosslinks_have_exact_nonvacuous_counts_and_reject_mismatch() -> None:
    protocol = (
        _PROJECT_ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
    ).read_bytes()
    machine_manifest = (
        _PROJECT_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    ).read_bytes()
    dependency_lock = (
        _PROJECT_ROOT / "requirements/m1-reference-macos-arm64-py311.lock"
    ).read_bytes()
    protocol_sha256 = hashlib.sha256(protocol).hexdigest()
    source_manifest_payload = b'{"source":"manifest"}'
    freeze_document = {
        "attempt_id": "attempt-development-only",
        "protocol_sha256": protocol_sha256,
        "machine_manifest_sha256": hashlib.sha256(machine_manifest).hexdigest(),
        "bound_files_sha256": hashlib.sha256(source_manifest_payload).hexdigest(),
        "frozen_source_fixture_materialization_sha256": "3" * 64,
        "dependency_lock_sha256": hashlib.sha256(dependency_lock).hexdigest(),
        "power_threshold_receipt_sha256": "4" * 64,
        "launch_authority_public_key_sha256": "5" * 64,
        "independent_reviewer_public_key_set_sha256": "6" * 64,
        "seed_source_authority_public_key_sha256": "7" * 64,
        "production_receipt_schema_bundle_sha256": "8" * 64,
    }
    freeze_row = (
        "freeze_receipt.json",
        b"freeze-receipt",
        "1" * 64,
        freeze_document,
    )
    supplied = {"freeze-receipt": (freeze_row,)}
    assert cp65._validate_supplied_cross_bindings(supplied) == (0, 10)

    ordered_sources = (
        (
            "frozen-protocol",
            (
                "frozen_inputs/protocol.md",
                protocol,
                hashlib.sha256(protocol).hexdigest(),
                protocol,
            ),
            (1, 9),
        ),
        (
            "frozen-protocol-sha256",
            (
                "frozen_inputs/protocol.sha256",
                protocol_sha256.encode("ascii") + b"\n",
                hashlib.sha256(protocol_sha256.encode("ascii") + b"\n").hexdigest(),
                protocol_sha256,
            ),
            (2, 9),
        ),
        (
            "frozen-machine-manifest",
            (
                "frozen_inputs/machine_manifest.json",
                machine_manifest,
                hashlib.sha256(machine_manifest).hexdigest(),
                json.loads(machine_manifest),
            ),
            (3, 8),
        ),
        (
            "source-manifest",
            (
                "frozen_inputs/bound_files.json",
                source_manifest_payload,
                "2" * 64,
                {},
            ),
            (4, 7),
        ),
        (
            "dependency-lock",
            (
                "frozen_inputs/dependency_lock.txt",
                dependency_lock,
                hashlib.sha256(dependency_lock).hexdigest(),
                dependency_lock,
            ),
            (5, 6),
        ),
    )
    for artifact_id, row, expected_counts in ordered_sources:
        supplied[artifact_id] = (row,)
        assert cp65._validate_supplied_cross_bindings(supplied) == expected_counts

    for field in (
        "protocol_sha256",
        "machine_manifest_sha256",
        "bound_files_sha256",
        "dependency_lock_sha256",
    ):
        original = freeze_document[field]
        freeze_document[field] = "f" * 64
        with pytest.raises(ValueError, match="cross-artifact digest binding"):
            cp65._validate_supplied_cross_bindings(supplied)
        freeze_document[field] = original


@pytest.mark.parametrize(
    "payload",
    (
        b'{"a":1,"a":2}',
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":null}',
        b'{"a":"\\u00e9"}',
        b'{ "a":1}',
        b'{"b":1,"a":2}',
        b'{"a":1}\n',
        b'\xef\xbb\xbf{"a":1}',
        b'{"a":18446744073709551616}',
        (b'{"' + b"a" * 129 + b'":1}'),
        (b'{"a":' + b"[" * 17 + b"0" + b"]" * 17 + b"}"),
    ),
)
def test_cp65_bounded_parser_rejects_noncanonical_or_unbounded_json(
    payload: bytes,
) -> None:
    with pytest.raises(ValueError):
        cp65._parse_canonical_json_object(payload, 67_108_864)


def test_cp65_parser_member_cap_is_exactly_128() -> None:
    accepted = json.dumps(
        {"k%03d" % ordinal: ordinal for ordinal in range(128)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    rejected = json.dumps(
        {"k%03d" % ordinal: ordinal for ordinal in range(129)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    assert len(cp65._parse_canonical_json_object(accepted, 67_108_864)) == 128
    with pytest.raises(ValueError):
        cp65._parse_canonical_json_object(rejected, 67_108_864)


def test_cp65_supplied_set_resource_caps_are_exact_and_parser_scoped() -> None:
    assert cp65._MAX_SUPPLIED_ARTIFACT_SET_ITEMS == 312
    assert cp65._MAX_SUPPLIED_ARTIFACT_SET_BYTES == 536_870_912
    assert cp65._MAX_SUPPLIED_ARTIFACT_SET_NODES == 1_048_576
    assert cp65._MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS == 268_435_456


def test_cp65_json_resource_counter_uses_exact_node_cap_and_counts_object_keys() -> None:
    at_limit = [[False] * 31 for _ in range(32_768)]
    at_limit[-1].pop()
    assert cp65._validate_json_resources(at_limit) == (1_048_576, 0)
    del at_limit
    over_limit = [[False] * 31 for _ in range(32_768)]
    with pytest.raises(ValueError):
        cp65._validate_json_resources(over_limit)
    assert cp65._validate_json_resources({"abc": "de", "f": "ghi"}) == (
        3,
        9,
    )


@pytest.mark.parametrize(
    "target_name",
    ("loads", "dumps"),
)
def test_cp65_parser_normalizes_memory_error_from_parse_and_canonicalization(
    monkeypatch: pytest.MonkeyPatch, target_name: str
) -> None:
    def exhaust_memory(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("synthetic CP65 resource exhaustion")

    caught = None
    with monkeypatch.context() as guarded:
        guarded.setattr(cp65.json, target_name, exhaust_memory)
        try:
            cp65._parse_canonical_json_object(b'{"a":1}', 1024)
        except BaseException as exc:  # assertion runs after the stdlib hook is restored
            caught = exc
    assert type(caught) is ValueError


@pytest.mark.parametrize(
    "target_name",
    ("_validate_artifact_payload", "_validate_supplied_cross_bindings"),
)
def test_cp65_public_validation_normalizes_memory_error_across_the_pipeline(
    monkeypatch: pytest.MonkeyPatch, target_name: str
) -> None:
    payload = _acquisition_start_payload()

    def exhaust_memory(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("synthetic CP65 resource exhaustion")

    caught = None
    with monkeypatch.context() as guarded:
        guarded.setattr(cp65, target_name, exhaust_memory)
        try:
            cp65.cp65_validate_supplied_artifact_bytes(
                "external-seed-acquisition-start-receipt",
                "seed_acquisition_start_receipt.json",
                payload,
            )
        except BaseException as exc:
            caught = exc
    assert type(caught) is ValueError


_CP65_GLOBAL_ADDITIONS = (
    "frozen_inputs/launch_authority_public_key.json",
    "dependency_lock_match_receipt.json",
    "seed_source_custody_artifact.json",
    "seed_capsule_sequence_crosscheck_receipt.json",
    "production_schedule.json",
    "production_runner_supervisor_qualification_receipt.json",
    "closed_refusal_failure_classifier_qualification_receipt.json",
    "independent_554_estimate_interval_decision_path_qualification_receipt.json",
    "independent_full_32768_recomputation_qualification_receipt.json",
    "frozen_inputs/independent_reviewer_public_keys.json",
    "frozen_inputs/seed_source_authority_public_key.json",
    "seed_source_authority_attestation.json",
    "frozen_inputs/source_fixture_materialization.bin",
    "frozen_inputs/production_schema_preimage_validator_bundle.json",
    "power_review_signoff.json",
    "preterminal_durable_artifact_inventory.json",
    "external_digest_preimage_registry.json",
    "auxiliary_reservation_transition_journal.bin",
)


@pytest.fixture(scope="module")
def authoritative_bundle() -> cp65.CP65ProductionSchemaPreimageValidatorBundleV1:
    return cp65.cp65_production_schema_preimage_validator_bundle()


def test_cp65_roster_counts_paths_and_partitions_are_exact() -> None:
    assert len(cp65._GLOBAL_PATHS) == 54
    assert cp65._GLOBAL_PATHS[-len(_CP65_GLOBAL_ADDITIONS) :] == _CP65_GLOBAL_ADDITIONS
    assert len(cp65._PER_SHARD_PATHS) == 8
    assert len(cp65._CONDITIONAL_PATHS) == 2
    assert len(cp65._ARTIFACT_DECLARATIONS) == 64
    assert len({row[0] for row in cp65._ARTIFACT_DECLARATIONS}) == 64
    assert len({row[1] for row in cp65._ARTIFACT_DECLARATIONS}) == 64
    assert len(cp65._RECEIPT_ENVELOPE_IDS) == 41
    assert len(cp65._REFERENCED_OUTPUT_IDS) == 15
    assert len(cp65._FROZEN_OR_BINARY_CUSTODY_IDS) == 8
    partitions = (
        set(cp65._RECEIPT_ENVELOPE_IDS),
        set(cp65._REFERENCED_OUTPUT_IDS),
        set(cp65._FROZEN_OR_BINARY_CUSTODY_IDS),
    )
    assert not (partitions[0] & partitions[1])
    assert not (partitions[0] & partitions[2])
    assert not (partitions[1] & partitions[2])
    assert set.union(*partitions) == {row[0] for row in cp65._ARTIFACT_DECLARATIONS}
    expanded = set(cp65._GLOBAL_PATHS) | set(cp65._CONDITIONAL_PATHS)
    for shard_ordinal in range(1, 33):
        shard_id = "shard-%04d" % shard_ordinal
        expanded.update(
            path.replace("{shard_id}", shard_id) for path in cp65._PER_SHARD_PATHS
        )
    assert len(expanded) == 312
    assert all(
        not path.startswith("/") and ".." not in path.split("/") for path in expanded
    )


def test_cp65_transient_namespace_has_one_prepared_authorization_alias(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rows = authoritative_bundle.transient_path_contracts
    assert len(rows) == 310
    assert tuple(row.transient_ordinal for row in rows) == tuple(range(1, 311))
    assert tuple(row.transient_relative_path for row in rows) == tuple(
        sorted(row.transient_relative_path for row in rows)
    )
    assert len({row.transient_path_id for row in rows}) == 310
    assert len({row.transient_relative_path for row in rows}) == 310
    assert all(
        row.collision_free
        and row.definition_only
        and not row.retained_at_committed
        and not row.sha256_manifest_included
        for row in rows
    )
    assert (
        sum(row.transient_kind == "destination-reserved-partial" for row in rows) == 128
    )
    assert (
        sum(row.transient_kind == "auxiliary-partial-candidate" for row in rows) == 181
    )
    assert (
        sum(row.transient_kind == "dynamic-auxiliary-reservation-hold" for row in rows)
        == 1
    )

    prepared = next(row for row in rows if row.prepared_authorization_alias)
    assert prepared.owner_artifact_id == "launch-authorization"
    assert prepared.final_relative_path == "launch_authorization.json"
    assert prepared.alternate_final_relative_path == (
        "rejected_launch_authorization_candidate.json"
    )
    assert prepared.transient_relative_path == "launch_authorization.json.partial"
    assert prepared.primary_publication_arm_id == "AUTHORIZATION"
    assert prepared.alternate_publication_arm_id == "PREAUTHORIZATION_TERMINAL"
    assert not any(
        row.transient_relative_path
        == "rejected_launch_authorization_candidate.json.partial"
        for row in rows
    )

    hold = next(
        row
        for row in rows
        if row.transient_kind == "dynamic-auxiliary-reservation-hold"
    )
    assert hold.owner_artifact_id == "__auxiliary_dynamic_hold__"
    assert hold.final_relative_path == hold.alternate_final_relative_path == ""
    assert hold.primary_publication_arm_id == hold.alternate_publication_arm_id == ""
    assert not hold.aliases_final_inode_when_published

    final_paths = set(cp65._GLOBAL_PATHS) | set(cp65._CONDITIONAL_PATHS)
    for shard_ordinal in range(1, 33):
        final_paths.update(
            template.replace("{shard_id}", "shard-%04d" % shard_ordinal)
            for template in cp65._PER_SHARD_PATHS
        )
    assert final_paths.isdisjoint(row.transient_relative_path for row in rows)
    assert len(final_paths | {row.transient_relative_path for row in rows}) == 622


def test_cp65_external_digest_preimage_registry_schema_is_exact_and_bounded() -> None:
    assert cp65._EXTERNAL_DIGEST_PREIMAGE_REGISTRY_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "protocol_sha256",
        "machine_manifest_sha256",
        "schema_semantic_sha256",
        "entry_count",
        "entries",
        "ordered_entry_sha256s",
        "ordered_entries_sha256",
        "finalized_at_utc",
        "body_sha256",
    )
    assert cp65._EXTERNAL_DIGEST_PREIMAGE_REGISTRY_ENTRY_KEYS == (
        "ordinal",
        "classification_id",
        "target_artifact_id",
        "target_relative_path",
        "target_json_pointer",
        "target_instance_selector_json_ascii",
        "target_artifact_raw_sha256",
        "digest_kind",
        "domain_separator",
        "preimage_encoding",
        "preimage_bytes",
        "preimage_ascii",
        "digest_sha256",
        "entry_sha256",
    )
    schema = cp65.cp65_artifact_schema("external-digest-preimage-registry")
    assert schema.maximum_bytes_per_instance == 67_108_864
    assert schema.minimum_instances == 0


def test_cp65_external_digest_registry_validates_retained_preimages_but_never_evidence() -> None:
    payload = _external_digest_registry_payload()
    result = cp65.cp65_validate_supplied_artifact_bytes(
        "external-digest-preimage-registry",
        "external_digest_preimage_registry.json",
        payload,
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert result.validated_digest_preimage_count >= 1
    assert result.unresolved_digest_preimage_count > 0
    assert not result.digest_preimages_valid
    assert not result.external_production_receipts_observed
    assert not result.production_evidence_accepted

    def refinish(document: dict) -> bytes:
        entry = document["entries"][0]
        entry["entry_sha256"] = _ZERO_SHA256
        entry["entry_sha256"] = hashlib.sha256(
            b"cp65-test28-external-digest-preimage-registry-entry-v1\0"
            + _canonical_json(entry)
        ).hexdigest()
        document["ordered_entry_sha256s"] = [entry["entry_sha256"]]
        document["ordered_entries_sha256"] = hashlib.sha256(
            b"cp65-test28-external-digest-preimage-registry-ordered-entries-v1\0"
            + bytes.fromhex(entry["entry_sha256"])
        ).hexdigest()
        document["body_sha256"] = _ZERO_SHA256
        return _receipt_payload("external-digest-preimage-registry", document)

    for mutation in ("preimage", "self-target", "postgate-target", "selector"):
        document = json.loads(payload)
        entry = document["entries"][0]
        if mutation == "preimage":
            entry["preimage_ascii"] += "-changed"
            entry["preimage_bytes"] = len(entry["preimage_ascii"].encode("ascii"))
        elif mutation == "self-target":
            entry[
                "classification_id"
            ] = "sha256-pointer:external-digest-preimage-registry:/protocol_sha256"
            entry["target_artifact_id"] = "external-digest-preimage-registry"
            entry["target_relative_path"] = "external_digest_preimage_registry.json"
            entry["target_json_pointer"] = "/protocol_sha256"
        elif mutation == "postgate-target":
            entry[
                "classification_id"
            ] = "sha256-pointer:terminal-state:/freeze_receipt_sha256"
            entry["target_artifact_id"] = "terminal-state"
            entry["target_relative_path"] = "terminal_state.json"
            entry["target_json_pointer"] = "/freeze_receipt_sha256"
        elif mutation == "selector":
            entry["target_instance_selector_json_ascii"] = _canonical_json(
                {
                    "artifact_instance_ordinal": 2,
                    "shard_ordinal": 0,
                    "wildcard_indices": [],
                }
            ).decode("ascii")
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                "external-digest-preimage-registry",
                "external_digest_preimage_registry.json",
                refinish(document),
            )
    schema = cp65.cp65_artifact_schema("external-digest-preimage-registry")
    assert schema.maximum_instances == 1
    assert schema.presence_rule_id == "presence:external-digest-preimage-registry"
    presence = next(
        row
        for row in cp65.cp65_production_schema_preimage_validator_bundle().predicate_contracts
        if row.predicate_id == schema.presence_rule_id
    )
    assert presence.operation_id == "relative-path-template-match"
    assert presence.input_json_pointers == ("$relative_path",)
    assert json.loads(presence.operand_json_ascii) == {
        "path_template": "external_digest_preimage_registry.json"
    }
    bound = next(
        row
        for row in cp65._build_auxiliary_bounds()
        if row.artifact_id == "external-digest-preimage-registry"
    )
    assert bound.maximum_logical_bytes_per_instance == 67_108_864
    assert bound.maximum_reserved_bytes_per_instance == 67_108_864


def test_cp65_registry_entry_resolves_exact_target_raw_pointer_and_selector() -> None:
    preimage_ascii = "capacity-observation-session-001"
    expected_digest = hashlib.sha256(preimage_ascii.encode("ascii")).hexdigest()
    capacity = _capacity_receipt_payload(expected_digest)
    registry = _external_digest_registry_payload(
        preimage_ascii=preimage_ascii,
        target_artifact_raw_sha256=hashlib.sha256(capacity).hexdigest(),
    )
    unresolved = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "external-digest-preimage-registry",
                "external_digest_preimage_registry.json",
                registry,
            ),
        )
    )
    capacity_only = cp65.cp65_validate_supplied_artifact_set(
        (("capacity-receipt", "capacity_receipt.json", capacity),)
    )
    resolved = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "external-digest-preimage-registry",
                "external_digest_preimage_registry.json",
                registry,
            ),
            ("capacity-receipt", "capacity_receipt.json", capacity),
        )
    )
    assert unresolved.intrinsic_digest_preimages_valid
    assert resolved.validated_digest_preimage_count > (
        unresolved.validated_digest_preimage_count
        + capacity_only.validated_digest_preimage_count
    )
    assert resolved.unresolved_digest_preimage_count < (
        unresolved.unresolved_digest_preimage_count
        + capacity_only.unresolved_digest_preimage_count
    )
    assert not resolved.digest_preimages_valid
    assert not resolved.production_evidence_accepted

    wrong_target = _external_digest_registry_payload(
        preimage_ascii=preimage_ascii,
        target_artifact_raw_sha256="f" * 64,
    )
    with pytest.raises(ValueError, match="registry target raw"):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "external-digest-preimage-registry",
                    "external_digest_preimage_registry.json",
                    wrong_target,
                ),
                ("capacity-receipt", "capacity_receipt.json", capacity),
            )
        )

    wrong_pointer_capacity = _capacity_receipt_payload("e" * 64)
    pointer_bound_registry = _external_digest_registry_payload(
        preimage_ascii=preimage_ascii,
        target_artifact_raw_sha256=hashlib.sha256(wrong_pointer_capacity).hexdigest(),
    )
    with pytest.raises(ValueError, match="registry target pointer"):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "external-digest-preimage-registry",
                    "external_digest_preimage_registry.json",
                    pointer_bound_registry,
                ),
                (
                    "capacity-receipt",
                    "capacity_receipt.json",
                    wrong_pointer_capacity,
                ),
            )
        )


def test_cp65_digest_result_counts_every_expanded_pointer_instance() -> None:
    summary = _preflight_summary_payload()
    result = cp65.cp65_validate_supplied_artifact_bytes(
        "preflight-gate-summary",
        "preflight_gate_summary.json",
        summary,
    )
    # The body digest is intrinsic.  The two singleton raw-artifact links and
    # all fifteen evidence-receipt raw digests require supplied source bytes.
    assert result.validated_digest_preimage_count == 1
    assert result.unresolved_digest_preimage_count == 17
    assert result.unresolved_cross_binding_count == 2
    assert not result.all_required_digest_preimage_sources_supplied
    assert not result.digest_preimages_valid
    assert not result.cross_bindings_valid
    assert not result.production_evidence_accepted


def test_cp65_intrinsic_digest_count_formulas_are_artifact_specific() -> None:
    schedule_validated, _schedule_unresolved = cp65._intrinsic_digest_instance_counts(
        "production-schedule",
        {"requests": [None] * 32_768},
    )
    assert schedule_validated == 98_307

    power_validated, _power_unresolved = cp65._intrinsic_digest_instance_counts(
        "power-threshold-receipt",
        {"ordered_slot_thresholds": [None] * 32},
    )
    assert power_validated == 35

    capacity = _capacity_receipt_payload("9" * 64)
    capacity_result = cp65.cp65_validate_supplied_artifact_bytes(
        "capacity-receipt",
        "capacity_receipt.json",
        capacity,
    )
    assert capacity_result.validated_digest_preimage_count == 1
    assert capacity_result.unresolved_digest_preimage_count == 8
    assert not capacity_result.all_required_digest_preimage_sources_supplied
    assert not capacity_result.digest_preimages_valid


def test_cp65_seed_capsule_and_schedule_nested_schemas_are_exact() -> None:
    assert cp65._SEED_CAPSULE_KEYS == (
        "schema",
        "purpose",
        "cp61_stable_design_sha256",
        "seed_count",
        "seed_ordinals",
        "seed_encoding",
        "ordered_seed_values",
        "source_method_id",
        "source_receipt_sha256",
        "acquisition_session_sha256",
        "body_sha256",
    )
    assert cp65._SCHEDULE_REQUEST_KEYS == (
        "schema_version",
        "seed_capsule_body_sha256",
        "seed_ordinal",
        "row_ordinal",
        "logical_request_ordinal",
        "row_key",
        "fixture_id",
        "strategy",
        "budget",
        "plan_seed_hex",
        "seed_free_request_sha256",
        "runtime_lock_sha256",
        "request_instance_sha256",
        "request_row_sha256",
    )
    assert cp65._TERMINAL_COUNT_KEYS == (
        "returned_rejection_selected_before_deadline",
        "returned_rejection_exhausted_before_deadline",
        "returned_sir_selected_before_deadline",
        "preexecution_refusal_before_deadline",
        "execution_failure_before_deadline",
        "timeout_censored_at_deadline",
    )


def test_cp65_power_threshold_rows_freeze_design_grammar_not_observed_counts(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    assert cp65._THRESHOLD_ROW_KEYS == (
        "slot_ordinal",
        "gate_id",
        "estimand_id",
        "threshold_encoding",
        "threshold_value",
        "design_minimum_selected_count",
        "justification_ascii",
        "justification_sha256",
        "row_sha256",
    )
    assert cp65._POWER_PRIMARY_SLOT_IDS == tuple(
        "cp65-power-primary-slot-%02d" % ordinal for ordinal in range(1, 33)
    )
    assert len(cp65._CP61_ESTIMAND_IDS) == 554
    assert len(set(cp65._CP61_ESTIMAND_IDS)) == 554
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    assert rules[
        ("power-threshold-receipt", "/ordered_slot_thresholds")
    ].length_interval == (32, 32)
    assert (
        rules[
            ("power-threshold-receipt", "/ordered_slot_thresholds/*/gate_id")
        ].string_domain
        == cp65._POWER_PRIMARY_SLOT_IDS
    )
    assert (
        rules[
            ("power-threshold-receipt", "/ordered_slot_thresholds/*/estimand_id")
        ].string_domain
        == cp65._CP61_ESTIMAND_IDS
    )
    encoding = rules[
        ("power-threshold-receipt", "/ordered_slot_thresholds/*/threshold_encoding")
    ]
    assert encoding.string_domain == (
        "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1",
    )
    assert (
        rules[
            ("power-threshold-receipt", "/ordered_slot_thresholds/*/threshold_value")
        ].string_pattern_id
        == "canonical-rational-threshold-v1"
    )
    assert rules[
        (
            "power-threshold-receipt",
            "/ordered_slot_thresholds/*/design_minimum_selected_count",
        )
    ].integer_interval == (1_040, 1_040)
    assert "selected_count" not in cp65._THRESHOLD_ROW_KEYS


def test_cp65_authority_and_signoff_keysets_are_acyclic_and_exact() -> None:
    assert cp65._SEED_AUTHORITY_ATTESTATION_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "acquisition_start_receipt_sha256",
        "acquisition_journal_sha256",
        "acquisition_journal_head_sha256",
        "acquisition_journal_entry_count",
        "ordered_seed_values_commitment_sha256",
        "seed_source_custody_artifact_sha256",
        "source_method_id",
        "source_authority_scheme_id",
        "source_authority_identity_sha256",
        "attested_at_utc",
        "attestation_expires_at_utc",
        "source_authority_signature_hex",
        "source_authority_signature_sha256",
        "body_sha256",
    )
    assert "seed_source_receipt_sha256" not in cp65._SEED_AUTHORITY_ATTESTATION_KEYS
    assert cp65._EXTERNAL_SEED_SOURCE_KEYS[-2:] == (
        "source_authority_attestation_sha256",
        "body_sha256",
    )
    assert cp65._SIGNOFF_ROW_KEYS == (
        "reviewer_role",
        "reviewer_identity_sha256",
        "reviewer_public_key_identity_sha256",
        "reviewed_artifact_sha256s",
        "decision",
        "signed_at_utc",
        "signature_scheme_id",
        "reviewer_signature_sha256",
        "reviewer_signature_hex",
        "signoff_sha256",
    )
    assert cp65._REQUIRED_REVIEWER_ROLES == (
        "protocol-and-provenance-reviewer",
        "runtime-and-durability-reviewer",
        "statistical-power-and-decision-reviewer",
        "independent-recomputation-reviewer",
    )


def test_cp65_capacity_and_terminal_inventory_dag_is_acyclic() -> None:
    assert "capacity_receipt_sha256" not in cp65._RESERVATION_MANIFEST_KEYS
    assert cp65._RESERVATION_MANIFEST_KEYS[3:9] == (
        "freeze_receipt_sha256",
        "schedule_sha256",
        "capacity_schema_sha256",
        "measurement_session_sha256",
        "storage_root_identity_sha256",
        "filesystem_identity_sha256",
    )
    assert cp65._PRETERMINAL_INVENTORY_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_arm",
        "auxiliary_transition_journal_prefix_entry_count",
        "auxiliary_transition_journal_prefix_head_sha256",
        "entry_count",
        "entries",
        "ordered_entries_sha256",
        "created_at_utc",
        "body_sha256",
    )
    assert cp65._PRETERMINAL_INVENTORY_ENTRY_KEYS == (
        "ordinal",
        "path",
        "bytes",
        "sha256",
        "entry_sha256",
    )


_EXPECTED_GATE_REQUIRED_ARTIFACTS = (
    (
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
        "dependency-lock",
        "power-review-signoff",
        "power-threshold-receipt",
        "launch-authority-public-key",
        "independent-reviewer-public-key-set",
        "seed-source-authority-public-key",
        "freeze-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
    ),
    ("freeze-receipt", "dependency-lock", "dependency-lock-match-receipt"),
    (
        "freeze-receipt",
        "source-manifest",
        "dependency-lock",
        "dependency-lock-match-receipt",
        "production-runtime-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "production-runtime-receipt",
        "production-schedule",
    ),
    (
        "freeze-receipt",
        "production-schema-preimage-validator-bundle",
        "production-schedule",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "capacity-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "capacity-receipt",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "durability-receipt",
    ),
    (
        "freeze-receipt",
        "seed-capsule-body",
        "production-schedule",
        "capacity-receipt",
        "durability-receipt",
        "reservation-manifest",
        "production-shard-map-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runtime-receipt",
        "production-runner-supervisor-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runner-supervisor-qualification-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-full-32768-recomputation-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-554-estimate-interval-decision-path-qualification-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "independent-reviewer-public-key-set",
        "power-review-signoff",
        "power-threshold-receipt",
    ),
    (
        "freeze-receipt",
        "preflight-gate-summary",
        "external-digest-preimage-registry",
        "independent-reviewer-public-key-set",
        "independent-signoff-set",
    ),
)


def test_cp65_gate_requirements_bind_full_upstream_custody() -> None:
    assert cp65._GATE_REQUIRED_ARTIFACT_IDS[:16] == _EXPECTED_GATE_REQUIRED_ARTIFACTS
    requirements = cp65._build_gate_requirements()
    assert tuple(row.gate_ordinal for row in requirements) == tuple(range(1, 18))
    assert all(row.requires_external_provenance for row in requirements)
    assert tuple(
        row.gate_ordinal for row in requirements if row.requires_independent_authority
    ) == (5, 15, 16, 17)
    assert all(
        not row.evidence_present and row.gate_state == "MISSING" for row in requirements
    )
    gate17 = requirements[-1].required_artifact_ids
    assert "preauthorization-outcome" in gate17
    assert "launch-authority-public-key" in gate17
    assert "launch-authorization" in gate17
    assert "postauthorization-outcome" not in gate17


def test_cp65_preflight_summary_binds_exact_raw_evidence_vector_and_signoffs_cover_it(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    requirements = authoritative_bundle.gate_requirements[:15]
    evidence_ids = tuple(row.evidence_artifact_id for row in requirements)
    evidence_raw = {
        artifact_id: ("cp65-evidence:" + artifact_id).encode("ascii")
        for artifact_id in evidence_ids
    }
    summary = {
        "schema": "cp65-test28-preflight-gate-summary-v2",
        "purpose": "preauthorization-gates-1-through-15-summary",
        "attempt_id": "attempt-development-only",
        "freeze_receipt_sha256": "1" * 64,
        "covered_gate_ids": [row.gate_id for row in requirements],
        "covered_gate_states": ["PASS"] * 15,
        "covered_evidence_node_ids": [row.evidence_node_id for row in requirements],
        "ordered_evidence_receipt_sha256s": [
            hashlib.sha256(evidence_raw[artifact_id]).hexdigest()
            for artifact_id in evidence_ids
        ],
        "external_digest_preimage_registry_sha256": "2" * 64,
        "body_sha256": "3" * 64,
    }
    assert cp65._validate_preflight_gate_summary_evidence(summary, evidence_raw) == 15

    for mutation in ("state", "digest", "order", "missing", "extra"):
        forged = json.loads(json.dumps(summary))
        forged_evidence = dict(evidence_raw)
        if mutation == "state":
            forged["covered_gate_states"][0] = "MISSING"
        elif mutation == "digest":
            forged["ordered_evidence_receipt_sha256s"][0] = "f" * 64
        elif mutation == "order":
            forged["covered_gate_ids"][0:2] = reversed(forged["covered_gate_ids"][0:2])
        elif mutation == "missing":
            del forged_evidence[evidence_ids[-1]]
        elif mutation == "extra":
            forged_evidence["not-a-gate-evidence-artifact"] = b"extra"
        with pytest.raises(ValueError):
            cp65._validate_preflight_gate_summary_evidence(forged, forged_evidence)

    reviewed_rules = tuple(
        row
        for row in authoritative_bundle.field_rules
        if row.artifact_id == "independent-signoff-set"
        and row.json_pointer.endswith("/reviewed_artifact_sha256s")
    )
    assert len(reviewed_rules) == 1
    assert reviewed_rules[0].length_interval == (1, 1)
    assert (
        "independent-signoff-reviewed-summary-raw-binding"
        in reviewed_rules[0].cross_constraint_ids
    )


def test_cp65_supplied_signoff_set_derives_four_role_pss_aggregation() -> None:
    summary_payload = _preflight_summary_payload()
    key_set_payload, key_rows = _reviewer_key_set_payload()
    signoff_payload = _independent_signoff_set_payload(
        summary_payload, key_set_payload, key_rows
    )
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "preflight-gate-summary",
                "preflight_gate_summary.json",
                summary_payload,
            ),
            (
                "independent-reviewer-public-key-set",
                "frozen_inputs/independent_reviewer_public_keys.json",
                key_set_payload,
            ),
            (
                "independent-signoff-set",
                "independent_signoff.json",
                signoff_payload,
            ),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert result.signature_verification_applicable
    assert result.signature_mathematically_valid_under_supplied_key
    assert result.validated_cross_binding_count >= 14
    assert result.unresolved_cross_binding_count > 0
    assert not result.external_provenance_verified
    assert not result.authority_verified
    assert not result.production_evidence_accepted
    assert not result.gate_transition_permitted


@pytest.mark.parametrize(
    "mutation",
    (
        "duplicate-role",
        "empty-reviewed-array",
        "false-derived-booleans",
        "arbitrary-signature",
    ),
)
def test_cp65_supplied_signoff_set_rejects_self_declared_or_uncovered_approval(
    mutation: str,
) -> None:
    summary_payload = _preflight_summary_payload()
    key_set_payload, key_rows = _reviewer_key_set_payload()
    signoff_payload = _independent_signoff_set_payload(
        summary_payload,
        key_set_payload,
        key_rows,
        duplicate_role=mutation == "duplicate-role",
        empty_reviewed=mutation == "empty-reviewed-array",
        false_derived_booleans=mutation == "false-derived-booleans",
        corrupt_signature=mutation == "arbitrary-signature",
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "preflight-gate-summary",
                    "preflight_gate_summary.json",
                    summary_payload,
                ),
                (
                    "independent-reviewer-public-key-set",
                    "frozen_inputs/independent_reviewer_public_keys.json",
                    key_set_payload,
                ),
                (
                    "independent-signoff-set",
                    "independent_signoff.json",
                    signoff_payload,
                ),
            )
        )


def test_cp65_auxiliary_arithmetic_separates_logical_slots_and_overhead() -> None:
    bounds = cp65._build_auxiliary_bounds()
    proof = cp65._build_auxiliary_size_proof(bounds)
    by_artifact = {row.artifact_id: row for row in bounds}
    assert len(by_artifact) == len(bounds)
    for row in bounds:
        assert row.artifact_id in row.mutually_exclusive_artifact_ids
        assert tuple(
            by_artifact[artifact_id].mutually_exclusive_artifact_ids
            for artifact_id in row.mutually_exclusive_artifact_ids
        ) == (row.mutually_exclusive_artifact_ids,) * len(
            row.mutually_exclusive_artifact_ids
        )
        assert all(
            by_artifact[artifact_id].physical_slot_group_id
            == row.physical_slot_group_id
            for artifact_id in row.mutually_exclusive_artifact_ids
        )
    launch_group = by_artifact["launch-authorization"]
    rejected_group = by_artifact["rejected-launch-authorization-candidate"]
    assert launch_group.physical_slot_group_id == (
        "auxiliary-slot:launch-authorization-candidate"
    )
    assert rejected_group.physical_slot_group_id == launch_group.physical_slot_group_id
    assert launch_group.mutually_exclusive_artifact_ids == (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    )
    groups = {}
    for row in bounds:
        if not row.destination_reservation_excluded or row.artifact_id.startswith("__"):
            continue
        groups.setdefault(row.physical_slot_group_id, []).append(row)
    derived_logical = sum(
        max(
            row.maximum_instance_count * row.maximum_logical_bytes_per_instance
            for row in rows
        )
        for rows in groups.values()
    )
    derived_reserved = sum(
        max(row.maximum_total_reserved_bytes for row in rows)
        for rows in groups.values()
    )
    assert derived_logical == proof.maximum_auxiliary_artifact_logical_bytes
    assert derived_reserved == proof.maximum_auxiliary_artifact_slot_reserved_bytes
    assert proof.maximum_auxiliary_artifact_logical_bytes == 21_845_344_321
    assert proof.maximum_auxiliary_artifact_slot_reserved_bytes == 22_213_099_520
    assert proof.allocation_and_directory_charge_policy_slot_bytes == 1_073_741_824
    assert proof.maximum_auxiliary_policy_required_bytes == 23_286_841_344
    assert proof.exclusive_reserved_policy_headroom_bytes == 11_072_897_024
    assert proof.maximum_dynamic_hold_bytes == 34_359_738_368
    assert (
        proof.maximum_auxiliary_policy_required_bytes
        + proof.exclusive_reserved_policy_headroom_bytes
        == 34_359_738_368
    )


def test_cp65_bundle_claim_boundary_is_narrow_and_fail_closed(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    true_definition_flags = (
        "sha256_pointer_contracts_cover_every_sha256_field_rule",
        "registry_required_targets_all_durable_by_gate15",
        "later_artifacts_have_no_registry_dependency",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "requirement_schemas_frozen",
        "complete_final_path_template_roster_frozen",
    )
    assert all(getattr(bundle, name) is True for name in true_definition_flags)
    assert bundle.auxiliary_reserved_partial_or_existing_final_slot_count == 183
    assert bundle.ordinary_auxiliary_partial_candidate_path_count == 181
    assert bundle.expanded_transient_path_count == 310
    assert bundle.expanded_final_and_transient_path_count == 622
    false_scope_flags = (
        "complete_production_roster_frozen",
        "complete_production_digest_instance_validation_interface_frozen",
        "artifact_occurrence_and_branch_schema_frozen",
        "production_receipt_schema_frozen",
        "production_execution_and_output_schema_frozen",
        "production_schema_frozen",
        "source_receipt_binds_capsule_body",
        "capacity_receipt_binds_shard_map",
        "external_production_receipts_observed",
        "external_seed_values_present",
        "source_authority_verified",
        "production_runtime_observed",
        "capacity_observed",
        "durability_observed",
        "candidate_shard_policy_selected",
        "production_shard_map_instantiated",
        "runner_supervisor_qualified",
        "closed_classifier_qualified",
        "power_thresholds_frozen",
        "freeze_receipt_present",
        "independent_signoffs_present",
        "launch_authorization_present",
        "started",
        "production_requests_materialized",
        "production_campaign_exposed",
        "production_execution_authorized",
        "production_execution_observed",
        "estimates_computed",
        "intervals_computed",
        "decision_made",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_closed",
    )
    assert all(getattr(bundle, name) is False for name in false_scope_flags)
    assert bundle.schema_completeness_claim_scope == (
        "supplied-receipt-envelope-instance-canonical-fields-digests-and-pure-"
        "gate-predicates-only;excludes-lifecycle-occurrence-branch-presence-"
        "provenance-trust-evidence-and-execution-output-semantics"
    )
    assert bundle.evidence_present_count == 0
    assert bundle.formal_test_28_status == "OPEN"
    assert (
        bundle.ledger_total_count,
        bundle.ledger_satisfied_count,
        bundle.ledger_missing_count,
    ) == (
        20,
        16,
        4,
    )


def test_cp65_catalog_references_resolve_and_have_no_orphans(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    artifact_ids = {record.artifact_id for record in bundle.artifact_schemas}
    rule_ids = {record.rule_id for record in bundle.field_rules}
    predicate_ids = {record.predicate_id for record in bundle.predicate_contracts}
    digest_ids = {record.contract_id for record in bundle.digest_preimage_contracts}
    assert len(artifact_ids) == len(bundle.artifact_schemas) == 64
    assert len(rule_ids) == len(bundle.field_rules)
    assert len(predicate_ids) == len(bundle.predicate_contracts)
    assert len(digest_ids) == len(bundle.digest_preimage_contracts)
    assert not any(
        contract_id.startswith("classified-binding:") for contract_id in digest_ids
    )

    referenced_rules = set()
    referenced_predicates = set()
    referenced_digests = set()
    referenced_artifacts = set()
    for schema in bundle.artifact_schemas:
        referenced_rules.update(schema.field_rule_ids)
        referenced_predicates.update((schema.presence_rule_id, schema.record_rule_id))
        referenced_digests.add(schema.digest_preimage_contract_id)
    for rule in bundle.field_rules:
        referenced_artifacts.add(rule.artifact_id)
        referenced_rules.update(rule.array_item_rule_ids)
        referenced_predicates.update(rule.cross_constraint_ids)
        assert rule.value_kind in {"array", "boolean", "integer", "object", "string"}
        if rule.value_kind == "boolean":
            assert rule.boolean_domain in ((False,), (True,), (False, True))
        elif rule.value_kind == "integer":
            assert len(rule.integer_interval) == 2
            assert rule.integer_interval[0] <= rule.integer_interval[1]
        elif rule.value_kind == "string":
            assert rule.string_domain or rule.string_pattern_id
        elif rule.value_kind == "array":
            assert len(rule.length_interval) == 2
            assert rule.array_item_rule_ids
        elif rule.value_kind == "object":
            assert rule.exact_object_keys
    for predicate in bundle.predicate_contracts:
        referenced_artifacts.update(predicate.applies_to_artifact_ids)
        referenced_predicates.update(predicate.child_predicate_ids)
        assert predicate.validator_implemented
        assert predicate.failure_code
    for gate in bundle.gate_requirements:
        referenced_artifacts.add(gate.evidence_artifact_id)
        referenced_artifacts.update(gate.required_artifact_ids)
        referenced_predicates.add(gate.predicate_id)
        referenced_predicates.update(gate.predicate_clause_ids)
    for bound in bundle.auxiliary_artifact_bounds:
        if not bound.artifact_id.startswith("__"):
            referenced_artifacts.add(bound.artifact_id)
        referenced_predicates.add(bound.simultaneous_presence_rule_id)
    referenced_digests.update(bundle.digest_dag_edge_source_contract_ids)
    referenced_digests.update(bundle.artifact_preimage_edge_source_contract_ids)
    referenced_digests.update(
        row.source_contract_id
        for row in bundle.sha256_pointer_contracts
        if row.source_contract_id
    )

    assert referenced_rules == rule_ids
    assert referenced_predicates == predicate_ids
    assert referenced_artifacts == artifact_ids
    # The COMMITTED raw digest is the public terminal output and therefore has
    # no downstream dependency edge.
    assert digest_ids - referenced_digests == {"committed-marker:raw-sha256"}


def test_cp65_candidate_completeness_flags_are_recomputed_and_mutation_sensitive(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    operation_ids = {
        "all-equal",
        "contiguous-cover",
        "cross-constraint-satisfied",
        "digest-sequence-equal",
        "discriminated-union",
        "exact-equal",
        "field-rule-satisfied",
        "integer-formula-equal",
        "integer-sum-equal",
        "length-equal",
        "logical-and",
        "logical-not",
        "logical-or",
        "member-of",
        "not-equal",
        "ordered-equal",
        "relative-path-template-match",
        "rsa-pss-verify",
        "sha256-body-equal",
        "sha256-raw-equal",
        "strictly-increasing",
        "utc-interval-contained",
    }

    def audit(
        *,
        artifact_schemas: tuple[object, ...] | None = None,
        field_rules: tuple[object, ...] | None = None,
        transient_paths: tuple[object, ...] | None = None,
        digest_contracts: tuple[object, ...] | None = None,
        pointer_contracts: tuple[object, ...] | None = None,
        predicates: tuple[object, ...] | None = None,
        gates: tuple[object, ...] | None = None,
        bounds: tuple[object, ...] | None = None,
        graph_edges: tuple[tuple[str, str], ...] | None = None,
    ) -> dict[str, bool]:
        schemas = (
            bundle.artifact_schemas if artifact_schemas is None else artifact_schemas
        )
        rules = bundle.field_rules if field_rules is None else field_rules
        transients = (
            bundle.transient_path_contracts
            if transient_paths is None
            else transient_paths
        )
        digests = (
            bundle.digest_preimage_contracts
            if digest_contracts is None
            else digest_contracts
        )
        pointers = (
            bundle.sha256_pointer_contracts
            if pointer_contracts is None
            else pointer_contracts
        )
        predicate_rows = (
            bundle.predicate_contracts if predicates is None else predicates
        )
        gate_rows = bundle.gate_requirements if gates is None else gates
        bound_rows = bundle.auxiliary_artifact_bounds if bounds is None else bounds
        edges = (
            bundle.artifact_preimage_dependency_edges
            if graph_edges is None
            else graph_edges
        )

        def unique(rows: tuple[object, ...], attribute: str) -> bool:
            values = tuple(getattr(row, attribute) for row in rows)
            return len(values) == len(set(values))

        artifact_ids = {row.artifact_id for row in schemas}
        rule_ids = {row.rule_id for row in rules}
        predicate_ids = {row.predicate_id for row in predicate_rows}
        digest_ids = {row.contract_id for row in digests}
        pointer_ids = {row.classification_id for row in pointers}
        bound_ids = {row.bound_id for row in bound_rows}
        identities_unique = all(
            (
                unique(schemas, "artifact_id"),
                unique(rules, "rule_id"),
                unique(predicate_rows, "predicate_id"),
                unique(digests, "contract_id"),
                unique(pointers, "classification_id"),
                unique(bound_rows, "bound_id"),
            )
        )

        rule_pairs = {(row.artifact_id, row.json_pointer) for row in rules}
        top_level_keysets_complete = (
            identities_unique
            and set(bundle.receipt_envelope_artifact_ids) <= artifact_ids
        )
        for schema in schemas:
            if schema.media_kind == "receipt-envelope-canonical-json":
                top_level_keysets_complete &= bool(schema.exact_keys)
                top_level_keysets_complete &= all(
                    (schema.artifact_id, "/" + key) in rule_pairs
                    for key in schema.exact_keys
                )
            top_level_keysets_complete &= set(schema.field_rule_ids) <= rule_ids

        field_semantics_complete = identities_unique
        for row in rules:
            field_semantics_complete &= row.artifact_id in artifact_ids
            field_semantics_complete &= row.required is True
            field_semantics_complete &= set(row.array_item_rule_ids) <= rule_ids
            field_semantics_complete &= set(row.cross_constraint_ids) <= predicate_ids
            if row.value_kind == "boolean":
                field_semantics_complete &= bool(row.boolean_domain)
            elif row.value_kind == "integer":
                field_semantics_complete &= (
                    len(row.integer_interval) == 2
                    and row.integer_interval[0] <= row.integer_interval[1]
                )
            elif row.value_kind == "string":
                field_semantics_complete &= bool(
                    row.string_domain or row.string_pattern_id
                )
            elif row.value_kind == "array":
                field_semantics_complete &= (
                    len(row.length_interval) == 2
                    and row.length_interval[0] <= row.length_interval[1]
                    and bool(row.array_item_rule_ids)
                )
            elif row.value_kind == "object":
                field_semantics_complete &= bool(row.exact_object_keys)
            else:
                field_semantics_complete = False

        referenced_rules: set[str] = set()
        referenced_predicates: set[str] = set()
        referenced_digests: set[str] = set()
        referenced_artifacts: set[str] = set()
        for schema in schemas:
            referenced_rules.update(schema.field_rule_ids)
            referenced_predicates.update(
                (schema.presence_rule_id, schema.record_rule_id)
            )
            referenced_digests.add(schema.digest_preimage_contract_id)
        for row in rules:
            referenced_artifacts.add(row.artifact_id)
            referenced_rules.update(row.array_item_rule_ids)
            referenced_predicates.update(row.cross_constraint_ids)
        for row in predicate_rows:
            referenced_artifacts.update(row.applies_to_artifact_ids)
            referenced_predicates.update(row.child_predicate_ids)
        for row in gate_rows:
            referenced_artifacts.add(row.evidence_artifact_id)
            referenced_artifacts.update(row.required_artifact_ids)
            referenced_predicates.add(row.predicate_id)
            referenced_predicates.update(row.predicate_clause_ids)
        for row in bound_rows:
            if not row.artifact_id.startswith("__"):
                referenced_artifacts.add(row.artifact_id)
            referenced_predicates.add(row.simultaneous_presence_rule_id)
        referenced_digests.update(bundle.digest_dag_edge_source_contract_ids)
        referenced_digests.update(bundle.artifact_preimage_edge_source_contract_ids)
        referenced_digests.update(
            row.source_contract_id for row in pointers if row.source_contract_id
        )
        references_resolve = (
            referenced_rules <= rule_ids
            and referenced_predicates <= predicate_ids
            and referenced_digests <= digest_ids
            and referenced_artifacts <= artifact_ids
        )
        no_orphans = (
            references_resolve
            and referenced_rules == rule_ids
            and referenced_predicates == predicate_ids
            and referenced_artifacts == artifact_ids
            and digest_ids - referenced_digests == {"committed-marker:raw-sha256"}
        )
        executable = (
            references_resolve
            and field_semantics_complete
            and all(
                row.validator_implemented and row.operation_id in operation_ids
                for row in predicate_rows
            )
        )

        def is_sha_rule(row: object) -> bool:
            parts = row.json_pointer.split("/")
            leaf = parts[-1]
            parent = parts[-2] if leaf == "*" and len(parts) > 1 else ""
            return (
                row.value_kind == "string"
                and row.length_interval == (64, 64)
                and row.string_pattern_id == "lowercase-sha256-hex"
                and (leaf.endswith("sha256") or parent.endswith("sha256s"))
            )

        sha_rule_pairs = {
            (row.artifact_id, row.json_pointer) for row in rules if is_sha_rule(row)
        }
        pointer_pairs = {
            (row.target_artifact_id, row.target_json_pointer) for row in pointers
        }
        pointer_cover = (
            identities_unique
            and len(pointer_ids) == len(pointers)
            and len(pointer_pairs) == len(pointers)
            and pointer_pairs == sha_rule_pairs
            and all("fallback" not in row.classification_id for row in pointers)
        )

        gate15_artifacts = {
            artifact_id
            for row in gate_rows
            if 1 <= row.gate_ordinal <= 15
            for artifact_id in (row.evidence_artifact_id,) + row.required_artifact_ids
        }
        registry_rows = tuple(
            row for row in pointers if row.preimage_registry_entry_required
        )
        registry_temporal = bool(registry_rows) and all(
            row.externally_retained_preimage_required
            and row.target_artifact_id in gate15_artifacts
            and row.source_availability_cut_id
            == "durable-by-gate15-before-registry-finalization"
            for row in registry_rows
        )
        no_late_registry = all(
            not row.preimage_registry_entry_required
            for row in pointers
            if row.target_artifact_id not in gate15_artifacts
        )

        nodes = bundle.artifact_preimage_dependency_node_ids
        order = bundle.artifact_preimage_topological_order
        positions = {node: ordinal for ordinal, node in enumerate(order)}
        graph_complete = (
            len(nodes) == len(set(nodes))
            and len(edges) == len(set(edges))
            and len(order) == len(nodes)
            and set(order) == set(nodes)
            and all(
                source in positions
                and target in positions
                and positions[source] < positions[target]
                for source, target in edges
            )
            and len(bundle.artifact_preimage_edge_target_pointers) == len(edges)
            and len(bundle.artifact_preimage_edge_source_contract_ids) == len(edges)
            and len(bundle.artifact_preimage_edge_digest_kinds) == len(edges)
            and set(bundle.artifact_preimage_edge_source_contract_ids) <= digest_ids
            and {row.source_contract_id for row in pointers}
            <= set(bundle.artifact_preimage_edge_source_contract_ids)
        )

        expanded_paths: list[str] = []
        scopes = {"global": 0, "per-shard": 0, "conditional-global": 0}
        for schema in schemas:
            if schema.path_scope not in scopes:
                continue
            scopes[schema.path_scope] += 1
            if schema.path_scope == "per-shard":
                expanded_paths.extend(
                    schema.path_template.replace(
                        "{shard_id}", "shard-%04d" % shard_ordinal
                    )
                    for shard_ordinal in range(1, 33)
                )
            else:
                expanded_paths.append(schema.path_template)
        transient_ids = tuple(row.transient_path_id for row in transients)
        roster_complete = (
            identities_unique
            and len(expanded_paths) == len(set(expanded_paths)) == 312
            and scopes == {"global": 54, "per-shard": 8, "conditional-global": 2}
            and len(transient_ids) == len(set(transient_ids)) == 310
            and all(row.collision_free for row in transients)
            and set(bundle.receipt_envelope_artifact_ids)
            | set(bundle.referenced_execution_output_artifact_ids)
            | set(bundle.frozen_or_binary_custody_artifact_ids)
            == artifact_ids
            and not (
                set(bundle.receipt_envelope_artifact_ids)
                & set(bundle.referenced_execution_output_artifact_ids)
            )
            and not (
                set(bundle.receipt_envelope_artifact_ids)
                & set(bundle.frozen_or_binary_custody_artifact_ids)
            )
            and not (
                set(bundle.referenced_execution_output_artifact_ids)
                & set(bundle.frozen_or_binary_custody_artifact_ids)
            )
        )

        proof = bundle.auxiliary_size_proof
        groups: dict[str, list[object]] = {}
        for row in bound_rows:
            if row.destination_reservation_excluded and not row.artifact_id.startswith(
                "__"
            ):
                groups.setdefault(row.physical_slot_group_id, []).append(row)
        derived_logical = sum(
            max(
                row.maximum_instance_count * row.maximum_logical_bytes_per_instance
                for row in rows
            )
            for rows in groups.values()
        )
        derived_reserved = sum(
            max(row.maximum_total_reserved_bytes for row in rows)
            for rows in groups.values()
        )
        aux_complete = (
            identities_unique
            and set(proof.artifact_bound_ids) == bound_ids
            and len(proof.artifact_bound_ids) == len(bound_rows)
            and set(proof.covered_complete_roster_artifact_ids) == artifact_ids
            and all(
                set(row.mutually_exclusive_artifact_ids) <= artifact_ids
                for row in bound_rows
                if not row.artifact_id.startswith("__")
            )
            and derived_logical == proof.maximum_auxiliary_artifact_logical_bytes
            and derived_reserved == proof.maximum_auxiliary_artifact_slot_reserved_bytes
            and derived_reserved
            + proof.allocation_and_directory_charge_policy_slot_bytes
            == proof.maximum_auxiliary_policy_required_bytes
            and proof.maximum_auxiliary_policy_required_bytes
            + proof.exclusive_reserved_policy_headroom_bytes
            == proof.auxiliary_reservation_floor_bytes
        )

        gate_complete = (
            len(gate_rows) == 17
            and tuple(row.gate_ordinal for row in gate_rows) == tuple(range(1, 18))
            and len({row.gate_id for row in gate_rows}) == 17
            and all(
                row.evidence_artifact_id in artifact_ids
                and set(row.required_artifact_ids) <= artifact_ids
                and row.predicate_id in predicate_ids
                and set(row.predicate_clause_ids) <= predicate_ids
                and not row.evidence_present
                and row.gate_state == "MISSING"
                for row in gate_rows
            )
            and all(row.preflight_summary_covered for row in gate_rows[:15])
            and all(not row.preflight_summary_covered for row in gate_rows[15:])
        )
        signature = bundle.authorization_signature_contract
        signature_complete = (
            signature.scheme_id == "rsa-pss-sha256-3072-e65537-salt32-v1"
            and signature.hash_algorithm_id == "sha256"
            and signature.mgf_algorithm_id == "mgf1-sha256"
            and (
                signature.modulus_bytes,
                signature.modulus_bit_length,
                signature.public_exponent,
                signature.signature_bytes,
                signature.signature_hex_characters,
                signature.salt_bytes,
                signature.em_bits,
                signature.em_bytes,
            )
            == (384, 3072, 65_537, 384, 768, 32, 3071, 384)
            and signature.verifier_implemented
            and not signature.signer_implemented
            and not signature.key_generation_implemented
            and not signature.public_key_present
            and not signature.trust_root_bound
            and not signature.signature_instance_present
            and not signature.authority_verified
            and not signature.launch_authorized
        )
        terminal_complete = all(
            artifact_id in artifact_ids
            for artifact_id in (
                "preauthorization-outcome",
                "postauthorization-outcome",
                "preterminal-durable-artifact-inventory",
                "terminal-state",
                "sha256-manifest",
                "committed-marker",
            )
        ) and {
            row.string_domain
            for row in rules
            if row.artifact_id == "preterminal-durable-artifact-inventory"
            and row.json_pointer == "/terminal_arm"
        } == {
            ("PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED")
        }

        digest_complete = (
            pointer_cover
            and references_resolve
            and graph_complete
            and registry_temporal
            and no_late_registry
            and all(row.verifier_implemented for row in digests)
        )
        return {
            "sha256_pointer_contracts_cover_every_sha256_field_rule": pointer_cover,
            "registry_required_targets_all_durable_by_gate15": registry_temporal,
            "later_artifacts_have_no_registry_dependency": no_late_registry,
            "all_schema_references_resolve_exactly_once": references_resolve
            and identities_unique,
            "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids": no_orphans
            and identities_unique,
            "all_referenced_rules_have_executable_validator_semantics": executable,
            "artifact_preimage_dag_complete": graph_complete,
            "all_required_production_receipt_keysets_predeclared": top_level_keysets_complete,
            "complete_receipt_type_range_size_and_domain_schemas_frozen": field_semantics_complete
            and top_level_keysets_complete,
            "complete_auxiliary_artifact_size_schema_frozen": aux_complete,
            "bounded_auxiliary_artifact_size_proof_present": aux_complete,
            "generic_prestart_terminal_record_schema_frozen": terminal_complete,
            "all_required_production_receipt_digest_preimages_frozen": digest_complete,
            "authorization_signature_preimage_and_verifier_frozen": signature_complete,
            "requirement_schemas_frozen": gate_complete and executable,
            "complete_final_path_template_roster_frozen": roster_complete,
        }

    baseline = audit()

    def altered(record: object, **changes: object) -> object:
        result = object.__new__(type(record))
        for field in fields(record):
            object.__setattr__(
                result,
                field.name,
                changes.get(field.name, getattr(record, field.name)),
            )
        return result

    frozen_schema_rule_index = next(
        index
        for index, row in enumerate(bundle.field_rules)
        if row.artifact_id == "freeze-receipt" and row.json_pointer == "/schema"
    )
    malformed_field_rules = list(bundle.field_rules)
    malformed_field_rules[frozen_schema_rule_index] = altered(
        malformed_field_rules[frozen_schema_rule_index],
        string_domain=(),
        string_pattern_id="",
    )
    mutation_cases = (
        (
            {"field_rules": tuple(malformed_field_rules)},
            {
                "all_referenced_rules_have_executable_validator_semantics",
                "complete_receipt_type_range_size_and_domain_schemas_frozen",
            },
        ),
        (
            {"field_rules": bundle.field_rules + (bundle.field_rules[0],)},
            {
                "all_schema_references_resolve_exactly_once",
                "complete_receipt_type_range_size_and_domain_schemas_frozen",
            },
        ),
        (
            {
                "artifact_schemas": tuple(
                    row
                    for row in bundle.artifact_schemas
                    if row.artifact_id != "freeze-receipt"
                )
            },
            {
                "all_required_production_receipt_keysets_predeclared",
                "complete_final_path_template_roster_frozen",
            },
        ),
        (
            {
                "pointer_contracts": bundle.sha256_pointer_contracts
                + (bundle.sha256_pointer_contracts[0],)
            },
            {
                "sha256_pointer_contracts_cover_every_sha256_field_rule",
                "all_required_production_receipt_digest_preimages_frozen",
            },
        ),
        (
            {"digest_contracts": bundle.digest_preimage_contracts[1:]},
            {
                "all_schema_references_resolve_exactly_once",
                "all_required_production_receipt_digest_preimages_frozen",
            },
        ),
        (
            {"predicates": bundle.predicate_contracts[:-1]},
            {
                "all_referenced_rules_have_executable_validator_semantics",
                "requirement_schemas_frozen",
            },
        ),
        (
            {"gates": bundle.gate_requirements + (bundle.gate_requirements[-1],)},
            {"requirement_schemas_frozen"},
        ),
        (
            {
                "bounds": bundle.auxiliary_artifact_bounds
                + (bundle.auxiliary_artifact_bounds[0],)
            },
            {
                "complete_auxiliary_artifact_size_schema_frozen",
                "bounded_auxiliary_artifact_size_proof_present",
            },
        ),
        (
            {
                "graph_edges": bundle.artifact_preimage_dependency_edges
                + (
                    (
                        bundle.artifact_preimage_dependency_edges[0][1],
                        bundle.artifact_preimage_dependency_edges[0][0],
                    ),
                )
            },
            {"artifact_preimage_dag_complete"},
        ),
    )
    for mutation_ordinal, (overrides, affected_flags) in enumerate(
        mutation_cases, start=1
    ):
        mutated = audit(**overrides)
        assert all(not mutated[name] for name in affected_flags), (
            mutation_ordinal,
            {name: mutated[name] for name in affected_flags},
        )

    assert {name for name, complete in baseline.items() if not complete} == set()
    assert (
        tuple(
            sorted(
                name
                for name, independently_complete in baseline.items()
                if getattr(bundle, name) is not independently_complete
            )
        )
        == ()
    )


def test_cp65_predicate_operation_set_is_closed_and_executable(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    operations = {
        record.operation_id for record in authoritative_bundle.predicate_contracts
    }
    assert operations == {
        "all-equal",
        "contiguous-cover",
        "cross-constraint-satisfied",
        "digest-sequence-equal",
        "discriminated-union",
        "exact-equal",
        "field-rule-satisfied",
        "integer-formula-equal",
        "integer-sum-equal",
        "length-equal",
        "logical-and",
        "logical-not",
        "logical-or",
        "member-of",
        "not-equal",
        "ordered-equal",
        "relative-path-template-match",
        "rsa-pss-verify",
        "sha256-body-equal",
        "sha256-raw-equal",
        "strictly-increasing",
        "utc-interval-contained",
    }


def test_cp65_every_issued_predicate_has_one_positive_and_targeted_negative_vector(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    vectors = cp65._predicate_contract_test_vectors()
    by_id = {row.predicate_id: row for row in authoritative_bundle.predicate_contracts}
    assert len(vectors) == len(by_id)
    assert {row[0] for row in vectors} == set(by_id)
    assert len({row[0] for row in vectors}) == len(vectors)
    for (
        predicate_id,
        positive_values,
        positive_children,
        negative_values,
        negative_children,
    ) in vectors:
        assert type(predicate_id) is str
        assert type(positive_values) is tuple
        assert type(positive_children) is tuple
        assert type(negative_values) is tuple
        assert type(negative_children) is tuple
        assert (
            cp65._evaluate_predicate_contract(
                predicate_id, positive_values, positive_children
            )
            is True
        )
        assert (
            cp65._evaluate_predicate_contract(
                predicate_id, negative_values, negative_children
            )
            is False
        )
    with pytest.raises(ValueError):
        cp65._evaluate_predicate_contract("unknown-predicate", (), ())


def test_cp65_each_predicate_operation_passes_independently_hardcoded_witnesses() -> None:
    digest = "1" * 64
    raw = b"independent-raw-witness"
    body = {"body_sha256": _ZERO_SHA256}
    body_domain = "independent-body-domain-v1"
    body_digest = hashlib.sha256(
        body_domain.encode("ascii") + b"\0" + _canonical_json(body)
    ).hexdigest()
    rsa_message = b"independent-predicate-rsa-witness"
    rsa_signature = _test_rsa_pss_signature(rsa_message, "predicate-operation")
    rsa_modulus = _TEST_RSA_N.to_bytes(384, "big")
    corrupted_signature = rsa_signature[:-1] + bytes((rsa_signature[-1] ^ 1,))
    vectors = {
        "all-equal": (("x", "x"), ("x", "y"), {}),
        "contiguous-cover": (
            ([1, 3], [2, 4], [1, 5], [4, 8]),
            ([1, 3], [2, 4], [1, 6], [4, 8]),
            {"seed_cover": [1, 4], "logical_cover": [1, 8]},
        ),
        "cross-constraint-satisfied": (
            ([[digest], [digest], [digest], [digest]], digest),
            ([[digest], [digest], [digest], []], digest),
            {"constraint_id": "independent-signoff-reviewed-summary-raw-binding"},
        ),
        "digest-sequence-equal": (([digest], [digest]), ([digest], ["2" * 64]), {}),
        "discriminated-union": (
            ("AUTHORIZATION", digest, ""),
            ("AUTHORIZATION", _ZERO_SHA256, ""),
            {
                "arms": [
                    "AUTHORIZATION",
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ]
            },
        ),
        "exact-equal": ((True,), (False,), {"expected": True}),
        "field-rule-satisfied": (
            ("attempt-1",),
            ("",),
            {"rule_id": "source-manifest:/attempt_id"},
        ),
        "integer-formula-equal": (
            (2, 2, 163_840),
            (2, 1, 163_840),
            {
                "formula": (
                    "entry-count=acquired-count;raw-file-bytes=163840;"
                    "valid-prefix-bytes=80*entry-count"
                )
            },
        ),
        "integer-sum-equal": (({"PASS": 2}, 2), ({"PASS": 2}, 3), {}),
        "length-equal": (([1], [2], 1), ([1], [2], 2), {}),
        "logical-and": ((True, True), (True, False), {}),
        "logical-not": (
            (True, False),
            (True, True),
            {"forbidden": "both-present"},
        ),
        "logical-or": (
            ("AUTHORIZATION", ""),
            ("AUTHORIZATION", "INCOMPLETE"),
            {
                "arms": [
                    "AUTHORIZATION",
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ]
            },
        ),
        "member-of": (("A",), ("C",), {"members": ["A", "B"]}),
        "not-equal": (
            ("AUTHORIZATION", digest),
            ("AUTHORIZATION", _ZERO_SHA256),
            {
                "value": _ZERO_SHA256,
                "when": {"/outcome_arm": "AUTHORIZATION"},
            },
        ),
        "ordered-equal": (([1, 2],), ([2, 1],), {"expected": [1, 2]}),
        "relative-path-template-match": (
            ("shards/shard-0001/index.json",),
            ("shards/{shard_id}/index.json",),
            {"path_template": "shards/{shard_id}/index.json"},
        ),
        "rsa-pss-verify": (
            (rsa_message, rsa_modulus, rsa_signature),
            (rsa_message, rsa_modulus, corrupted_signature),
            {"scheme": "rsa-pss-sha256-3072-e65537-salt32-v1"},
        ),
        "sha256-body-equal": (
            (body_digest, body),
            (_ZERO_SHA256, body),
            {"domain": body_domain},
        ),
        "sha256-raw-equal": (
            (hashlib.sha256(raw).hexdigest(), raw),
            (_ZERO_SHA256, raw),
            {},
        ),
        "strictly-increasing": (([1, 2, 3],), ([1, 3, 2],), {"first": 1, "step": 1}),
        "utc-interval-contained": (
            (
                "2025-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:00.000000Z",
                "2027-01-01T00:00:00.000000Z",
                "2028-01-01T00:00:00.000000Z",
            ),
            (
                "2025-01-01T00:00:00.000000Z",
                "2027-01-01T00:00:00.000000Z",
                "2027-01-01T00:00:00.000000Z",
                "2028-01-01T00:00:00.000000Z",
            ),
            {"inequality": "valid-from<=issued<expires<=valid-until"},
        ),
    }
    assert set(vectors) == cp65._PREDICATE_OPERATION_IDS
    for operation_id, (positive, negative, operand) in vectors.items():
        evaluator = cp65._PREDICATE_EVALUATORS[operation_id]
        assert evaluator(tuple(positive), operand) is True, operation_id
        assert evaluator(tuple(negative), operand) is False, operation_id


def test_cp65_predicate_graph_resolves_wildcards_synthetic_inputs_and_children() -> None:
    raw = b'{"raw":"artifact"}'
    documents = {
        "freeze-receipt": {
            "relative_path": "freeze_receipt.json",
            "raw_bytes": b"freeze-receipt",
            "document": {"bound_files_sha256": hashlib.sha256(raw).hexdigest()},
        },
        "source-manifest": {
            "relative_path": "frozen_inputs/bound_files.json",
            "raw_bytes": raw,
            "document": {"entries": [{"ordinal": 1}, {"ordinal": 2}]},
        },
        "launch-authorization": {
            "relative_path": "launch_authorization.json",
            "raw_bytes": b"launch",
            "document": {},
        },
        "preauthorization-outcome": {
            "relative_path": "preauthorization_outcome.json",
            "raw_bytes": b"preauthorization",
            "document": {
                "outcome_arm": "AUTHORIZATION",
                "terminal_state": "",
            },
        },
    }
    synthetic = {}
    assert cp65._evaluate_predicate_graph(
        "cross:source-manifest-entry-ordinals-strictly-increase",
        documents,
        synthetic,
    )
    assert cp65._evaluate_predicate_graph(
        "cross:freeze-binds-source-manifest-raw-bytes", documents, synthetic
    )
    assert cp65._evaluate_predicate_graph(
        "cross:published-and-rejected-authorization-not-copresent",
        documents,
        {},
    )
    both = dict(documents)
    both["rejected-launch-authorization-candidate"] = {
        "relative_path": "rejected_launch_authorization_candidate.json",
        "raw_bytes": b"rejected",
        "document": {},
    }
    assert not cp65._evaluate_predicate_graph(
        "cross:published-and-rejected-authorization-not-copresent", both, {}
    )
    broken = {artifact_id: dict(row) for artifact_id, row in documents.items()}
    broken["source-manifest"]["document"] = {
        "entries": [{"ordinal": 1}, {"ordinal": 1}]
    }
    assert not cp65._evaluate_predicate_graph(
        "cross:source-manifest-entry-ordinals-strictly-increase",
        broken,
        synthetic,
    )
    with pytest.raises(ValueError):
        cp65._evaluate_predicate_graph("unknown-predicate", documents, synthetic)
    with pytest.raises(ValueError, match="cycle"):
        cp65._evaluate_predicate_graph(
            "record:frozen-protocol",
            documents,
            {},
            _active_predicate_ids=("record:frozen-protocol",),
        )


def test_cp65_full_preimage_graph_is_exactly_topological_and_typed(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    nodes = bundle.artifact_preimage_dependency_node_ids
    edges = bundle.artifact_preimage_dependency_edges
    order = bundle.artifact_preimage_topological_order
    assert len(nodes) == len(set(nodes)) == bundle.artifact_preimage_node_count
    assert len(edges) == len(set(edges)) == bundle.artifact_preimage_edge_count
    assert set(order) == set(nodes) and len(order) == len(nodes)
    positions = {node: index for index, node in enumerate(order)}
    assert all(source in positions and target in positions for source, target in edges)
    assert all(positions[source] < positions[target] for source, target in edges)
    assert len(bundle.artifact_preimage_edge_target_pointers) == len(edges)
    assert len(bundle.artifact_preimage_edge_source_contract_ids) == len(edges)
    assert len(bundle.artifact_preimage_edge_digest_kinds) == len(edges)
    digest_ids = {record.contract_id for record in bundle.digest_preimage_contracts}
    assert set(bundle.artifact_preimage_edge_source_contract_ids) <= digest_ids
    assert set(bundle.artifact_preimage_edge_digest_kinds) <= {
        "body-domain-sha256",
        "byte-identity",
        "digest-value-equality",
        "domain-separated-canonical-json-sha256",
        "key-identity-domain-sha256",
        "ordered-domain-sha256",
        "plain-raw-bytes-sha256",
        "plain-raw-file-sha256",
        "record-row-domain-sha256",
        "selected-stored-sha256-cross-binding",
        "signature-preimage-sha256",
    }
    assert bundle.artifact_preimage_dag_acyclic
    assert bundle.artifact_preimage_dag_complete
    assert bundle.artifact_body_domain_separators_unique


def test_cp65_nonintrinsic_sha_pointers_have_exact_two_edge_equality_states(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    nodes = set(bundle.artifact_preimage_dependency_node_ids)
    edges = bundle.artifact_preimage_dependency_edges
    pointers = bundle.artifact_preimage_edge_target_pointers
    contracts = bundle.artifact_preimage_edge_source_contract_ids
    kinds = bundle.artifact_preimage_edge_digest_kinds
    metadata = tuple(zip(edges, pointers, contracts, kinds))
    for row in bundle.sha256_pointer_contracts:
        binding = "binding:" + row.classification_id
        if cp65._sha256_pointer_is_intrinsic_owned(row):
            assert binding not in nodes
            continue
        assert binding in nodes
        incoming = tuple(item for item in metadata if item[0][1] == binding)
        outgoing = tuple(item for item in metadata if item[0][0] == binding)
        assert len(incoming) == len(outgoing) == 1
        assert incoming[0][1] == "$selected-source-digest"
        assert incoming[0][2] == row.source_contract_id
        assert incoming[0][3] == row.digest_kind
        if row.target_artifact_id == "rejected-launch-authorization-candidate":
            assert outgoing[0][0][1] == (
                "state:rejected-launch-authorization-candidate:validated-envelope"
            )
        else:
            assert outgoing[0][0][1].endswith(":body-sha256")
        assert outgoing[0][1] == row.target_json_pointer
        assert outgoing[0][2] == row.source_contract_id
        assert outgoing[0][3] == "digest-value-equality"


def test_cp65_full_graph_versions_mutable_aux_journal_custody_without_a_cycle(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    edges = set(authoritative_bundle.artifact_preimage_dependency_edges)
    chain = (
        "digest:auxiliary-metadata-reservation:raw-sha256",
        "state:auxiliary-transition-journal:head0",
        "state:auxiliary-transition-journal:preinventory-prefix",
        "digest:preterminal-durable-artifact-inventory:body-sha256",
        "digest:preterminal-durable-artifact-inventory:raw-sha256",
        "state:auxiliary-transition-journal:after-inventory",
        "digest:terminal-state:body-sha256",
        "digest:terminal-state:raw-sha256",
        "state:auxiliary-transition-journal:after-terminal",
        "digest:sha256-manifest:body-sha256",
        "digest:sha256-manifest:raw-sha256",
        "state:auxiliary-transition-journal:final",
        "digest:committed-marker:body-sha256",
        "digest:committed-marker:raw-sha256",
    )
    assert set(chain) <= set(authoritative_bundle.artifact_preimage_dependency_node_ids)
    assert set(zip(chain, chain[1:])) <= edges
    assert (
        "digest:auxiliary-reservation-transition-journal:raw-sha256",
        "digest:committed-marker:body-sha256",
    ) in edges
    assert (
        "digest:auxiliary-reservation-transition-journal:raw-sha256",
        "digest:preterminal-durable-artifact-inventory:body-sha256",
    ) not in edges
    assert (
        "digest:auxiliary-reservation-transition-journal:raw-sha256",
        "digest:sha256-manifest:body-sha256",
    ) not in edges
    pointer_rows = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in authoritative_bundle.sha256_pointer_contracts
    }
    expected_states = {
        (
            "preterminal-durable-artifact-inventory",
            "/auxiliary_transition_journal_prefix_head_sha256",
        ): (
            "auxiliary-reservation-transition-journal:preinventory-prefix",
            "shards-finalized-before-preterminal-inventory",
        ),
        (
            "terminal-state",
            "/auxiliary_transition_journal_after_inventory_head_sha256",
        ): (
            "auxiliary-reservation-transition-journal:after-inventory",
            "preterminal-inventory-before-terminal",
        ),
        (
            "sha256-manifest",
            "/auxiliary_transition_journal_after_terminal_head_sha256",
        ): (
            "auxiliary-reservation-transition-journal:after-terminal",
            "terminal-before-manifest",
        ),
        (
            "committed-marker",
            "/auxiliary_reservation_transition_journal_final_head_sha256",
        ): (
            "auxiliary-reservation-transition-journal:final-head",
            "final-journal-sealed-before-committed",
        ),
        ("committed-marker", "/auxiliary_reservation_transition_journal_sha256",): (
            "auxiliary-reservation-transition-journal:raw-sha256",
            "final-journal-sealed-before-committed",
        ),
    }
    for pointer, (contract_id, cut_id) in expected_states.items():
        row = pointer_rows[pointer]
        assert row.source_contract_id == contract_id
        assert row.source_availability_cut_id == cut_id
        assert not row.preimage_registry_entry_required


def test_cp65_coarse_graph_is_explicitly_not_the_full_preimage_graph(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    assert (bundle.digest_dag_node_count, bundle.digest_dag_edge_count) == (20, 44)
    assert bundle.digest_dag_is_gate_evidence_only
    assert bundle.artifact_preimage_node_count > bundle.digest_dag_node_count
    assert bundle.artifact_preimage_edge_count > bundle.digest_dag_edge_count
    assert len(bundle.digest_dag_edges) == len(bundle.digest_dag_edge_target_pointers)
    assert len(bundle.digest_dag_edges) == len(
        bundle.digest_dag_edge_source_contract_ids
    )
    assert len(bundle.digest_dag_edges) == len(bundle.digest_dag_edge_digest_kinds)


def test_cp65_preauthorization_candidate_publication_graph_is_one_way_and_acyclic(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    schemas = {row.artifact_id: row for row in authoritative_bundle.artifact_schemas}
    assert (
        schemas["rejected-launch-authorization-candidate"].digest_preimage_contract_id
        == "launch-authorization:body-sha256"
    )
    assert not any(
        row.contract_id == "rejected-launch-authorization-candidate:body-sha256"
        for row in authoritative_bundle.digest_preimage_contracts
    )
    nodes = set(authoritative_bundle.artifact_preimage_dependency_node_ids)
    edges = set(authoritative_bundle.artifact_preimage_dependency_edges)
    prepared = "state:launch-authorization-candidate:prepared-raw"
    preauth_body = "digest:preauthorization-outcome:body-sha256"
    preauth_raw = "digest:preauthorization-outcome:raw-sha256"
    auth_winner = "state:preauthorization-outcome:authorization-winner"
    terminal_winner = "state:preauthorization-outcome:terminal-winner"
    launch_raw = "digest:launch-authorization:raw-sha256"
    rejected_raw = "digest:rejected-launch-authorization-candidate:raw-sha256"
    assert {
        prepared,
        preauth_body,
        preauth_raw,
        auth_winner,
        terminal_winner,
        launch_raw,
        rejected_raw,
    } <= nodes
    assert {
        (prepared, preauth_body),
        (preauth_body, preauth_raw),
        (preauth_raw, auth_winner),
        (preauth_raw, terminal_winner),
        (prepared, launch_raw),
        (auth_winner, launch_raw),
        (prepared, rejected_raw),
        (terminal_winner, rejected_raw),
    } <= edges
    assert (launch_raw, preauth_body) not in edges
    assert (rejected_raw, launch_raw) not in edges
    assert (launch_raw, rejected_raw) not in edges
    assert not any(
        "launch-authorization:body-sha256" in source
        and "rejected-launch-authorization-candidate:body-sha256" in target
        or "rejected-launch-authorization-candidate:body-sha256" in source
        and "launch-authorization:body-sha256" in target
        for source, target in edges
    )
    pointer = next(
        row
        for row in authoritative_bundle.sha256_pointer_contracts
        if row.target_artifact_id == "preauthorization-outcome"
        and row.target_json_pointer == "/prepared_launch_authorization_sha256"
    )
    assert pointer.source_contract_id == (
        "launch-authorization-candidate:prepared-raw-sha256"
    )
    assert pointer.source_availability_cut_id == (
        "authorization-candidate-prepared-before-preauth-cas"
    )


def test_cp65_every_field_pointer_has_an_exact_executable_rule(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    rules = {(row.artifact_id, row.json_pointer): row for row in bundle.field_rules}
    assert len(rules) == len(bundle.field_rules)

    for schema in bundle.artifact_schemas:
        for key in schema.exact_keys:
            assert (schema.artifact_id, "/" + key) in rules
        for rule_id in schema.field_rule_ids:
            assert rule_id in {row.rule_id for row in bundle.field_rules}

    for row in bundle.field_rules:
        assert row.required is True
        assert row.rule_id == "%s:%s" % (row.artifact_id, row.json_pointer)
        if row.value_kind == "boolean":
            assert row.boolean_domain in ((False,), (True,), (False, True))
        elif row.value_kind == "integer":
            assert len(row.integer_interval) == 2
            assert type(row.integer_interval[0]) is int
            assert type(row.integer_interval[1]) is int
            assert row.integer_interval[0] <= row.integer_interval[1]
        elif row.value_kind == "string":
            assert len(row.length_interval) == 2
            assert row.string_domain or row.string_pattern_id
        elif row.value_kind == "array":
            assert len(row.length_interval) == 2
            assert row.array_item_rule_ids
        elif row.value_kind == "object":
            assert row.exact_object_keys
        else:  # pragma: no cover - makes a newly invented kind fail loudly.
            pytest.fail("unfrozen field value kind: %s" % row.value_kind)

    sha_rules = []
    for row in bundle.field_rules:
        parts = row.json_pointer.split("/")
        leaf = parts[-1]
        parent = parts[-2] if len(parts) > 1 else ""
        if (
            leaf == "sha256"
            or leaf.endswith("_sha256")
            or (leaf == "*" and parent.endswith("_sha256s"))
        ):
            sha_rules.append(row)
    assert sha_rules
    assert all(
        row.value_kind == "string"
        and row.string_pattern_id == "lowercase-sha256-hex"
        and row.length_interval == (64, 64)
        for row in sha_rules
    )
    assert rules[
        (
            "started-receipt",
            "/production_runner_rng_or_child_started_before_receipt",
        )
    ].boolean_domain == (False,)


def test_cp65_closed_count_field_rules_have_exact_protocol_intervals(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    exact_intervals = {
        ("independent-signoff-set", "/signoff_count"): (4, 4),
        ("independent-reviewer-public-key-set", "/key_count"): (4, 4),
        ("power-review-signoff", "/primary_slot_count"): (32, 32),
        ("capacity-receipt", "/shard_count"): (32, 32),
        ("reservation-manifest", "/entry_count"): (128, 128),
        ("production-shard-map-receipt", "/shard_count"): (32, 32),
        (
            "production-shard-map-receipt",
            "/shards/*/logical_request_count",
        ): (1_024, 1_024),
        ("shard-index", "/request_count"): (1_024, 1_024),
        ("shard-receipt", "/request_count"): (1_024, 1_024),
        ("external-seed-source-receipt", "/seed_count"): (2_048, 2_048),
        (
            "external-seed-source-receipt",
            "/acquisition_journal_entry_count",
        ): (2_048, 2_048),
        (
            "seed-source-authority-attestation",
            "/acquisition_journal_entry_count",
        ): (2_048, 2_048),
        ("seed-capsule-sequence-crosscheck-receipt", "/seed_count"): (
            2_048,
            2_048,
        ),
        (
            "preterminal-durable-artifact-inventory",
            "/auxiliary_transition_journal_prefix_entry_count",
        ): (0, 251),
        (
            "terminal-state",
            "/auxiliary_transition_journal_after_inventory_entry_count",
        ): (1, 252),
        (
            "sha256-manifest",
            "/auxiliary_transition_journal_after_terminal_entry_count",
        ): (2, 253),
        (
            "committed-marker",
            "/auxiliary_reservation_transition_journal_final_entry_count",
        ): (4, 255),
        ("preterminal-durable-artifact-inventory", "/entry_count"): (1, 312),
        ("sha256-manifest", "/entry_count"): (1, 312),
        ("external-digest-preimage-registry", "/entry_count"): (0, 4_096),
    }
    rules_by_id = {row.rule_id: row for row in authoritative_bundle.field_rules}
    for identity, expected in exact_intervals.items():
        rule = rules[identity]
        assert rule.value_kind == "integer"
        assert rule.integer_interval == expected
        for accepted in set(expected):
            assert cp65._field_rule_value_satisfied(rule, accepted, rules_by_id, ())
        if expected[0] > 0:
            assert not cp65._field_rule_value_satisfied(
                rule, expected[0] - 1, rules_by_id, ()
            )
        assert not cp65._field_rule_value_satisfied(
            rule, expected[1] + 1, rules_by_id, ()
        )

    exact_array_intervals = {
        ("independent-signoff-set", "/required_reviewer_roles"): (4, 4),
        ("independent-signoff-set", "/ordered_signoffs"): (4, 4),
        ("independent-reviewer-public-key-set", "/required_reviewer_roles"): (
            4,
            4,
        ),
        ("independent-reviewer-public-key-set", "/ordered_keys"): (4, 4),
        (
            "independent-reviewer-public-key-set",
            "/ordered_public_key_identity_sha256s",
        ): (4, 4),
        ("power-review-signoff", "/ordered_slot_threshold_row_sha256s"): (
            32,
            32,
        ),
        ("reservation-manifest", "/entries"): (128, 128),
        ("production-shard-map-receipt", "/shards"): (32, 32),
        (
            "production-shard-map-receipt",
            "/shards/*/per_file_reservation_manifest_entry_sha256s",
        ): (4, 4),
        ("shard-index", "/ordered_request_entries"): (1_024, 1_024),
        ("preterminal-durable-artifact-inventory", "/entries"): (1, 312),
        ("sha256-manifest", "/entries"): (1, 312),
        ("external-digest-preimage-registry", "/entries"): (0, 4_096),
        (
            "external-digest-preimage-registry",
            "/ordered_entry_sha256s",
        ): (0, 4_096),
    }
    for identity, expected in exact_array_intervals.items():
        rule = rules[identity]
        assert rule.value_kind == "array"
        assert rule.length_interval == expected


def test_cp65_common_identifiers_and_purposes_are_not_generic_strings(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    receipt_ids = set(authoritative_bundle.receipt_envelope_artifact_ids)
    for artifact_id in receipt_ids:
        schema_rule = rules.get((artifact_id, "/schema"))
        purpose_rule = rules.get((artifact_id, "/purpose"))
        if schema_rule is not None:
            assert len(schema_rule.string_domain) == 1
        if purpose_rule is not None:
            assert len(purpose_rule.string_domain) == 1
        attempt_rule = rules.get((artifact_id, "/attempt_id"))
        if attempt_rule is not None:
            assert attempt_rule.string_pattern_id == "attempt-id-v1"

    for row in authoritative_bundle.field_rules:
        leaf = row.json_pointer.rsplit("/", 1)[-1]
        if leaf.endswith("_method_id") or leaf.endswith("_session_id"):
            assert row.string_pattern_id == "opaque-method-session-authority-id-v1"
        if leaf.endswith("_authority_id"):
            assert row.string_pattern_id == "opaque-method-session-authority-id-v1"
    assert rules[
        (
            "partial-seed-acquisition-terminal-receipt",
            "/topup_redraw_reselection_permitted",
        )
    ].boolean_domain == (False,)


def test_cp65_protocol_enums_and_frozen_schedule_domains_are_closed(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    singleton_domains = {
        (
            "rejected-launch-authorization-candidate",
            "/authority_scheme_id",
        ): ("rsa-pss-sha256-3072-e65537-salt32-v1",),
        ("seed-source-custody-artifact", "/custody_media_type"): (
            "application/octet-stream",
        ),
        ("seed-source-custody-artifact", "/custody_encoding"): ("identity",),
        (
            "seed-capsule-sequence-crosscheck-receipt",
            "/seed_encoding",
        ): ("uint64-16-lowercase-hex-big-endian",),
        ("production-runtime-receipt", "/runtime_profile_id"): (
            "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration",
        ),
        ("production-schedule", "/requests/*/schema_version"): (
            cp65._CP63_SCHEMA_VERSION,
        ),
    }
    for identity, expected in singleton_domains.items():
        assert rules[identity].string_domain == expected
    assert rules[
        ("preterminal-durable-artifact-inventory", "/terminal_arm")
    ].string_domain == (
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
    )
    assert rules[("production-schedule", "/requests/*/row_key")].string_domain == tuple(
        row[1] for row in cp65._ROW_INVENTORY
    )
    assert rules[
        ("production-schedule", "/requests/*/fixture_id")
    ].string_domain == tuple(dict.fromkeys(row[2] for row in cp65._ROW_INVENTORY))
    assert rules[
        ("production-schedule", "/requests/*/strategy")
    ].string_domain == tuple(dict.fromkeys(row[3] for row in cp65._ROW_INVENTORY))
    assert (
        rules[
            (
                "closed-refusal-failure-classifier-qualification-receipt",
                "/closed_refusal_codes/*",
            )
        ].string_domain
        == cp65._CLOSED_REFUSAL_CODES
    )
    assert (
        rules[
            (
                "closed-refusal-failure-classifier-qualification-receipt",
                "/closed_failure_codes/*",
            )
        ].string_domain
        == cp65._CLOSED_FAILURE_CODES
    )
    for artifact_id, pointer in (
        ("launch-authority-public-key", "/authority_id"),
        (
            "independent-reviewer-public-key-set",
            "/ordered_keys/*/authority_id",
        ),
        ("seed-source-authority-public-key", "/source_authority_id"),
    ):
        assert rules[(artifact_id, pointer)].string_pattern_id == (
            "opaque-method-session-authority-id-v1"
        )


def test_cp65_lifecycle_sentinels_and_discriminated_unions_are_exact(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    pre_arm = rules[("preauthorization-outcome", "/outcome_arm")]
    post_arm = rules[("postauthorization-outcome", "/outcome_arm")]
    pre_state = rules[("preauthorization-outcome", "/terminal_state")]
    post_state = rules[("postauthorization-outcome", "/terminal_state")]
    assert pre_arm.string_domain == (
        "AUTHORIZATION",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert post_arm.string_domain == (
        "STARTED",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert pre_state.string_domain == (
        "",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert post_state.string_domain == pre_state.string_domain
    assert pre_state.length_interval == post_state.length_interval == (0, 16)

    unions = {
        artifact_id: [
            predicate
            for predicate in authoritative_bundle.predicate_contracts
            if predicate.operation_id == "discriminated-union"
            and artifact_id in predicate.applies_to_artifact_ids
        ]
        for artifact_id in (
            "preauthorization-outcome",
            "postauthorization-outcome",
            "terminal-state",
        )
    }
    assert all(len(rows) == 1 for rows in unions.values())
    assert all(row.validator_implemented for rows in unions.values() for row in rows)
    assert all(
        row.cross_constraint_ids
        for row in (
            pre_arm,
            post_arm,
            pre_state,
            post_state,
            rules[("terminal-state", "/terminal_arm")],
            rules[("terminal-state", "/terminal_state")],
        )
    )


def test_cp65_predicate_graph_has_no_empty_or_unreachable_semantics(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    predicates = {row.predicate_id: row for row in bundle.predicate_contracts}
    assert len(predicates) == len(bundle.predicate_contracts)
    field_predicate_ids = {"field:" + row.rule_id for row in bundle.field_rules}
    assert field_predicate_ids <= set(predicates)

    for row in bundle.predicate_contracts:
        assert row.validator_implemented is True
        assert row.failure_code
        assert set(row.child_predicate_ids) <= set(predicates)
        if row.operation_id in {"logical-and", "logical-or"}:
            assert row.child_predicate_ids
        elif row.operation_id == "logical-not":
            assert len(row.child_predicate_ids) == 1
        else:
            assert row.input_json_pointers or row.operation_id == "rsa-pss-verify"

    for schema in bundle.artifact_schemas:
        record = predicates[schema.record_rule_id]
        expected = {"field:" + rule_id for rule_id in schema.field_rule_ids}
        for rule_id in schema.field_rule_ids:
            field_rule = next(
                row for row in bundle.field_rules if row.rule_id == rule_id
            )
            expected.update(field_rule.cross_constraint_ids)
        assert expected <= set(record.child_predicate_ids)

    for gate in bundle.gate_requirements:
        gate_predicate = predicates[gate.predicate_id]
        expected_clauses = tuple(
            "record:" + artifact_id for artifact_id in gate.required_artifact_ids
        ) + ("gate-pass:" + gate.gate_id,)
        assert gate.predicate_clause_ids == expected_clauses
        assert gate_predicate.child_predicate_ids == expected_clauses

    roots = {schema.record_rule_id for schema in bundle.artifact_schemas} | {
        gate.predicate_id for gate in bundle.gate_requirements
    }
    reachable = set()
    pending = list(roots)
    while pending:
        predicate_id = pending.pop()
        if predicate_id in reachable:
            continue
        reachable.add(predicate_id)
        pending.extend(predicates[predicate_id].child_predicate_ids)
    assert reachable == set(predicates)


def test_cp65_every_sha_pointer_is_owned_or_has_one_typed_dependency_source(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    contracts = {row.contract_id: row for row in bundle.digest_preimage_contracts}
    owned = {
        (row.artifact_id, row.digest_field_pointer)
        for row in bundle.digest_preimage_contracts
        if row.digest_field_pointer.startswith("/")
    }
    incoming = {}
    for (_source, target), pointer, source_contract_id, digest_kind in zip(
        bundle.artifact_preimage_dependency_edges,
        bundle.artifact_preimage_edge_target_pointers,
        bundle.artifact_preimage_edge_source_contract_ids,
        bundle.artifact_preimage_edge_digest_kinds,
    ):
        if not target.startswith("digest:"):
            continue
        target_contract = contracts[target[len("digest:") :]]
        if not pointer.startswith("/"):
            continue
        incoming.setdefault((target_contract.artifact_id, pointer), []).append(
            (source_contract_id, digest_kind)
        )

    sha_pointers = set()
    for row in bundle.field_rules:
        parts = row.json_pointer.split("/")
        leaf = parts[-1]
        parent = parts[-2] if len(parts) > 1 else ""
        if (
            leaf == "sha256"
            or leaf.endswith("_sha256")
            or (leaf == "*" and parent.endswith("_sha256s"))
        ):
            sha_pointers.add((row.artifact_id, row.json_pointer))
    rejected_alias_pointers = {
        pointer
        for pointer in sha_pointers
        if pointer[0] == "rejected-launch-authorization-candidate"
    }
    assert sha_pointers <= owned | set(incoming) | rejected_alias_pointers
    assert all(
        source_id in contracts
        and digest_kind
        in {
            "body-domain-sha256",
            "byte-identity",
            "digest-value-equality",
            "domain-separated-canonical-json-sha256",
            "key-identity-domain-sha256",
            "ordered-domain-sha256",
            "plain-raw-bytes-sha256",
            "plain-raw-file-sha256",
            "record-row-domain-sha256",
            "selected-stored-sha256-cross-binding",
            "signature-preimage-sha256",
        }
        for bindings in incoming.values()
        for source_id, digest_kind in bindings
    )

    classifications = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in bundle.sha256_pointer_contracts
    }
    exact_identity_sources = {
        (
            "launch-authorization",
            "/authority_identity_sha256",
        ): "launch-authority-public-key:identity",
        (
            "seed-source-authority-attestation",
            "/source_authority_identity_sha256",
        ): "seed-source-authority-public-key:identity",
        (
            "power-review-signoff",
            "/reviewer_public_key_identity_sha256",
        ): "independent-reviewer-public-key-set:key-identity",
        (
            "independent-signoff-set",
            "/ordered_signoffs/*/reviewer_public_key_identity_sha256",
        ): "independent-reviewer-public-key-set:key-identity",
    }
    for pointer, source_id in exact_identity_sources.items():
        assert classifications[pointer].source_contract_id == source_id
        assert classifications[pointer].digest_kind == ("key-identity-domain-sha256")

    identity_contract = (
        "independent-reviewer-public-key-set:selected-reviewer-identity-sha256"
    )
    for pointer in (
        ("power-review-signoff", "/reviewer_identity_sha256"),
        (
            "independent-signoff-set",
            "/ordered_signoffs/*/reviewer_identity_sha256",
        ),
    ):
        row = classifications[pointer]
        assert row.source_artifact_id == "independent-reviewer-public-key-set"
        assert row.source_contract_id == identity_contract
        assert not row.preimage_registry_entry_required


def test_cp65_sha_pointer_catalog_is_exhaustive_bounded_and_temporally_possible(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    bundle = authoritative_bundle
    sha_rules = tuple(
        row for row in bundle.field_rules if cp65._is_sha256_field_rule(row)
    )
    classifications = bundle.sha256_pointer_contracts
    assert (
        bundle.sha256_pointer_contract_count == len(classifications) == len(sha_rules)
    )
    keys = {
        (row.target_artifact_id, row.target_json_pointer, row.instance_selector_id)
        for row in classifications
    }
    assert len(keys) == len(classifications)
    assert {(row.artifact_id, row.json_pointer) for row in sha_rules} == {
        (row.target_artifact_id, row.target_json_pointer) for row in classifications
    }
    assert all(row.definition_only for row in classifications)
    assert all("fallback" not in row.classification_id for row in classifications)
    assert {
        row.semantic_class for row in classifications
    } <= cp65._SHA256_POINTER_SEMANTIC_CLASSES

    expanded = {
        row.classification_id: cp65._sha256_pointer_expanded_cardinality(row)
        for row in classifications
    }
    assert all(type(value) is int and value >= 1 for value in expanded.values())
    registry_rows = tuple(
        row for row in classifications if row.preimage_registry_entry_required
    )
    assert registry_rows
    registry_cardinality = {
        row.classification_id: cp65._sha256_pointer_registry_entry_cardinality(row)
        for row in classifications
    }
    assert sum(registry_cardinality.values()) <= 4_096
    assert all(
        row.semantic_class
        in {"externally-retained-preimage", "conditional-zero-or-cross"}
        and row.externally_retained_preimage_required
        and row.target_artifact_id in cp65._REGISTRY_CUT_DURABLE_ARTIFACT_IDS
        for row in registry_rows
    )
    assert all(
        not row.preimage_registry_entry_required
        for row in classifications
        if row.target_artifact_id not in cp65._REGISTRY_CUT_DURABLE_ARTIFACT_IDS
    )
    assert all(
        not row.preimage_registry_entry_required
        for row in classifications
        if expanded[row.classification_id] > 4_096
    )
    assert bundle.sha256_pointer_contracts_cover_every_sha256_field_rule
    assert bundle.registry_required_targets_all_durable_by_gate15
    assert bundle.later_artifacts_have_no_registry_dependency
    unimplemented = tuple(
        row for row in classifications if not row.validator_implemented
    )
    assert unimplemented
    assert all(
        row.source_artifact_id in cp65._REFERENCED_OUTPUT_IDS
        or row.target_artifact_id
        in {
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
            "shard-index",
            "shard-receipt",
        }
        for row in unimplemented
    )
    assert not bundle.complete_production_digest_instance_validation_interface_frozen


def test_cp65_sha_pointer_availability_cuts_are_closed_and_registry_is_preflight_only(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    cuts = {
        "intrinsic-same-record",
        "frozen-before-acquisition-start",
        "durable-by-gate15-before-registry-finalization",
        "registry-finalized-before-summary",
        "summary-finalized-before-signoff",
        "signoff-finalized-before-authorization",
        "authorization-candidate-prepared-before-preauth-cas",
        "preauth-outcome-before-postauth",
        "postauth-outcome-before-started-or-terminal",
        "started-before-launch-and-terminal",
        "shards-finalized-before-preterminal-inventory",
        "preterminal-inventory-before-terminal",
        "terminal-before-manifest",
        "manifest-before-final-journal-seal",
        "final-journal-sealed-before-committed",
    }
    rows = authoritative_bundle.sha256_pointer_contracts
    assert {row.source_availability_cut_id for row in rows} <= cuts
    assert all(
        row.source_availability_cut_id
        == "durable-by-gate15-before-registry-finalization"
        for row in rows
        if row.preimage_registry_entry_required
    )
    assert all(
        row.source_availability_cut_id == "intrinsic-same-record"
        for row in rows
        if row.semantic_class in {"self-body", "signature", "key-identity"}
        and row.source_artifact_id == row.target_artifact_id
    )


def test_cp65_high_cardinality_schedule_and_shard_digests_never_use_registry(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rows = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in authoritative_bundle.sha256_pointer_contracts
    }
    schedule_contracts = {
        "/requests/*/seed_capsule_body_sha256": "seed-capsule-body:body-sha256",
        "/requests/*/seed_free_request_sha256": (
            "production-schedule:cp62-seed-free-request-sha256"
        ),
        "/requests/*/runtime_lock_sha256": (
            "v15-machine-manifest:cp62-runtime-lock-record-sha256"
        ),
        "/requests/*/request_instance_sha256": (
            "production-schedule:request-instance-sha256"
        ),
        "/requests/*/request_row_sha256": "production-schedule:requests-row-digest",
        "/ordered_request_record_sha256s/*": (
            "production-schedule:requests-row-digest"
        ),
        "/ordered_requests_sha256": ("production-schedule:ordered-request-records"),
    }
    for pointer, contract_id in schedule_contracts.items():
        row = rows[("production-schedule", pointer)]
        assert row.source_contract_id == contract_id
        assert not row.preimage_registry_entry_required
    shard_contracts = {
        "/shard_record_sha256": "production-shard-map-receipt:shards-row-digest",
        "/ordered_request_entries/*/request_sha256": (
            "shard-index:request-payload-segment-sha256"
        ),
        "/ordered_request_entries/*/raw_sha256": (
            "shard-index:raw-payload-segment-sha256"
        ),
        "/ordered_request_entries/*/stable_sha256": (
            "shard-index:stable-payload-segment-sha256"
        ),
        "/ordered_request_entries/*/stderr_sha256": (
            "shard-index:stderr-payload-segment-sha256"
        ),
        "/ordered_request_entries/*/rng_initial_sha256": (
            "shard-index:rng-initial-state-row-sha256"
        ),
        "/ordered_request_entries/*/rng_final_sha256": (
            "shard-index:rng-final-state-row-sha256"
        ),
        "/raw_file_sha256": "shard-raw-records:raw-sha256",
        "/stable_file_sha256": "shard-stable-traces:raw-sha256",
        "/stderr_file_sha256": "shard-stderr-records:raw-sha256",
        "/rng_initial_file_sha256": "shard-rng-initial-states:raw-sha256",
        "/rng_final_file_sha256": "shard-rng-final-states:raw-sha256",
    }
    for pointer, contract_id in shard_contracts.items():
        row = rows[("shard-index", pointer)]
        assert row.source_contract_id == contract_id
        assert not row.preimage_registry_entry_required
    assert all(
        not row.preimage_registry_entry_required
        for row in authoritative_bundle.sha256_pointer_contracts
        if row.target_artifact_id == "external-digest-preimage-registry"
    )


def test_cp65_exact_17_output_backed_digest_routes_are_definition_only_not_instance_validators(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    output_backed = {
        ("shard-index", "/ordered_request_entries/*/request_sha256"),
        ("shard-index", "/ordered_request_entries/*/raw_sha256"),
        ("shard-index", "/ordered_request_entries/*/stable_sha256"),
        ("shard-index", "/ordered_request_entries/*/stderr_sha256"),
        ("shard-index", "/ordered_request_entries/*/rng_initial_sha256"),
        ("shard-index", "/ordered_request_entries/*/rng_final_sha256"),
        ("shard-index", "/raw_file_sha256"),
        ("shard-index", "/stable_file_sha256"),
        ("shard-index", "/stderr_file_sha256"),
        ("shard-index", "/rng_initial_file_sha256"),
        ("shard-index", "/rng_final_file_sha256"),
        ("shard-receipt", "/requests_file_sha256"),
        ("shard-receipt", "/raw_file_sha256"),
        ("shard-receipt", "/stable_file_sha256"),
        ("shard-receipt", "/stderr_file_sha256"),
        ("shard-receipt", "/rng_initial_file_sha256"),
        ("shard-receipt", "/rng_final_file_sha256"),
    }
    assert len(output_backed) == 17
    rows = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in authoritative_bundle.sha256_pointer_contracts
    }
    assert all(not rows[pointer].validator_implemented for pointer in output_backed)
    assert all(
        not rows[pointer].preimage_registry_entry_required
        and rows[pointer].source_artifact_id in cp65._REFERENCED_OUTPUT_IDS
        for pointer in output_backed
    )
    assert (
        not authoritative_bundle.complete_production_digest_instance_validation_interface_frozen
    )


def test_cp65_schema_design_and_predecessor_digest_pins_have_exact_nested_sources(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rows = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in authoritative_bundle.sha256_pointer_contracts
    }
    contracts = {
        row.contract_id: row for row in authoritative_bundle.digest_preimage_contracts
    }
    capacity = "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256"
    cp61 = "v15-machine-manifest:cp61-stable-design-semantic-sha256"
    candidate = "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256"
    durability = "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256"
    schedule = "v15-machine-manifest:cp63-schedule-contract-record-sha256"
    supervisor = "v15-machine-manifest:cp62-supervisor-contract-record-sha256"
    raw_schema = "v15-machine-manifest:cp63-raw-record-schema-record-sha256"
    projection = "v15-machine-manifest:cp62-projection-contract-record-sha256"
    runtime_lock = "v15-machine-manifest:cp62-runtime-lock-record-sha256"
    selected_sources = {
        capacity: (
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/capacity_receipt_schema/record_sha256",
            "968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe",
        ),
        cp61: (
            "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/"
            "stable_design_semantic_sha256",
            "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb",
        ),
        candidate: (
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/candidate_shard_policy/record_sha256",
            "8623c092772eaa0e40066d7e423967095e86491c01d869aa824c81fa9ee4b4ea",
        ),
        durability: (
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/durability_receipt_schema/record_sha256",
            "aced3702d8f1cbb240de9c41c6f97581a5ce019045e3300cc485bcb6328e76c2",
        ),
        schedule: (
            "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/"
            "runner_bundle/canonical_record/fields/schedule_contract/fields/"
            "record_sha256",
            "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607",
        ),
        supervisor: (
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "supervisor_contract/record_sha256",
            "6dfb5b8bbb7cecabed1c84349bc32ac130dd2fb698ba400e0ce74d3ef58434fb",
        ),
        raw_schema: (
            "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/"
            "runner_bundle/canonical_record/fields/raw_record_schema/fields/"
            "record_sha256",
            "29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb",
        ),
        projection: (
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "stable_trace_projection/record_sha256",
            "1d42337a0191822fb7d7fa81883bab08101dbf68cd88e1b835553bc96fb32733",
        ),
        runtime_lock: (
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "runtime_source_abi_lock/record_sha256",
            "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460",
        ),
    }
    assert len(selected_sources) == 9
    expected = {
        ("capacity-receipt", "/capacity_schema_sha256"): capacity,
        ("auxiliary-metadata-reservation", "/capacity_schema_sha256"): capacity,
        ("reservation-manifest", "/capacity_schema_sha256"): capacity,
        ("external-seed-source-receipt", "/cp61_stable_design_sha256"): cp61,
        ("seed-capsule-body", "/cp61_stable_design_sha256"): cp61,
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/estimand_contract_sha256",
        ): cp61,
        (
            "production-shard-map-receipt",
            "/candidate_shard_policy_sha256",
        ): candidate,
        ("durability-receipt", "/layout_contract_sha256"): durability,
        ("production-schedule", "/schedule_contract_sha256"): schedule,
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/production_schedule_contract_sha256",
        ): schedule,
        (
            "production-runner-supervisor-qualification-receipt",
            "/supervisor_contract_sha256",
        ): supervisor,
        (
            "closed-refusal-failure-classifier-qualification-receipt",
            "/supervisor_contract_sha256",
        ): supervisor,
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/raw_record_schema_sha256",
        ): raw_schema,
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/stable_projection_schema_sha256",
        ): projection,
        (
            "capacity-receipt",
            "/auxiliary_artifact_size_proof_sha256",
        ): "production-schema-preimage-validator-bundle:auxiliary-size-proof-record-sha256",
        ("production-schedule", "/requests/*/runtime_lock_sha256"): runtime_lock,
    }
    assert len(expected) == 16
    for pointer, contract_id in expected.items():
        row = rows[pointer]
        assert row.source_contract_id == contract_id
        assert not row.preimage_registry_entry_required
        assert contract_id in contracts
        if contract_id.startswith("v15-machine-manifest:"):
            assert row.source_artifact_id == "frozen-machine-manifest"
            source_pointer, _expected_digest = selected_sources[contract_id]
            assert row.semantic_class == "selected-stored-digest"
            assert row.digest_kind == "selected-stored-sha256-cross-binding"
            assert row.source_json_pointer == source_pointer
            assert row.source_availability_cut_id == ("frozen-before-acquisition-start")
            contract = contracts[contract_id]
            assert contract.artifact_id == "frozen-machine-manifest"
            assert contract.digest_field_pointer == source_pointer
            assert contract.algorithm_id == "sha256"
            assert contract.domain_separator == ""
            assert contract.canonical_profile_id == (
                "selected-stored-lowercase-sha256-reference-v1"
            )
            assert contract.zeroed_field_pointers == ()
            assert contract.ordered_component_ids == ()
            assert contract.verifier_implemented

    manifest_payload = (
        _PROJECT_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    ).read_bytes()
    assert len(manifest_payload) == 2_038_189
    assert manifest_payload.count(b"\n") == 39_046
    assert hashlib.sha256(manifest_payload).hexdigest() == (
        "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
    )
    manifest = json.loads(manifest_payload)
    for source_pointer, expected_digest in selected_sources.values():
        assert _json_pointer(manifest, source_pointer) == expected_digest

    dependency_lock_raw_sha256 = (
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
    )
    runtime_lock_record_sha256 = selected_sources[runtime_lock][1]
    assert runtime_lock_record_sha256 != dependency_lock_raw_sha256
    schedule_document = {
        "schedule_contract_sha256": selected_sources[schedule][1],
        "requests": [{"runtime_lock_sha256": runtime_lock_record_sha256}],
    }
    supplied = {
        "production-schedule": (
            ("production_schedule.json", b"schedule", "1" * 64, schedule_document),
        ),
        "frozen-machine-manifest": (
            (
                "frozen_inputs/machine_manifest.json",
                manifest_payload,
                "2" * 64,
                manifest,
            ),
        ),
    }
    validated, unresolved = cp65._validate_supplied_cross_bindings(supplied)
    assert validated == 2
    assert unresolved == 0
    schedule_document["requests"][0]["runtime_lock_sha256"] = dependency_lock_raw_sha256
    with pytest.raises(ValueError, match="selected predecessor stored digest"):
        cp65._validate_supplied_cross_bindings(supplied)


def test_cp65_independent_qualification_source_is_a_disjoint_role_submanifest(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    role_rule = next(
        row
        for row in authoritative_bundle.field_rules
        if row.artifact_id == "source-manifest"
        and row.json_pointer == "/entries/*/role"
    )
    assert "production-runner-source" in role_rule.string_domain
    assert "independent-recomputation-source" in role_rule.string_domain
    contract_id = "source-manifest:independent-recomputation-submanifest"
    contracts = {
        row.contract_id: row for row in authoritative_bundle.digest_preimage_contracts
    }
    contract = contracts[contract_id]
    assert contract.domain_separator == (
        "cp65-test28-independent-recomputation-source-submanifest-v1\0"
    )
    assert contract.canonical_profile_id == (
        "role-filtered-ordered-source-manifest-submanifest-v1"
    )
    assert contract.verifier_implemented
    pointer_rows = {
        (row.target_artifact_id, row.target_json_pointer): row
        for row in authoritative_bundle.sha256_pointer_contracts
    }
    for pointer in (
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/independent_recomputation_source_manifest_sha256",
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/independent_source_manifest_sha256",
        ),
    ):
        row = pointer_rows[pointer]
        assert row.semantic_class == "nested-domain-digest"
        assert row.digest_kind == "domain-separated-canonical-json-sha256"
        assert row.source_artifact_id == "source-manifest"
        assert row.source_contract_id == contract_id
        assert not row.preimage_registry_entry_required
    predicates = {
        row.predicate_id: row for row in authoritative_bundle.predicate_contracts
    }
    assert "source-manifest-role-partitions-disjoint" in predicates
    assert predicates["source-manifest-role-partitions-disjoint"].validator_implemented

    entries = [
        {
            "ordinal": 1,
            "role": "independent-recomputation-source",
            "relative_path": "independent/recompute.py",
            "bytes": 12,
            "lines": 1,
            "sha256": "1" * 64,
        },
        {
            "ordinal": 2,
            "role": "production-runner-source",
            "relative_path": "runner/main.py",
            "bytes": 18,
            "lines": 2,
            "sha256": "2" * 64,
        },
    ]
    document = {
        "schema": "cp65-test28-source-manifest-v1",
        "purpose": "frozen-source-fixture-materialization-custody",
        "attempt_id": "attempt-development-only",
        "protocol_sha256": "3" * 64,
        "machine_manifest_sha256": "4" * 64,
        "entry_count": 2,
        "total_bytes": 30,
        "entries": entries,
        "ordered_entries_sha256": "5" * 64,
        "body_sha256": "6" * 64,
    }
    expected = hashlib.sha256(
        b"cp65-test28-independent-recomputation-source-submanifest-v1\0"
        + _canonical_json({"entry_count": 1, "entries": [entries[0]]})
    ).hexdigest()
    assert (
        cp65._independent_recomputation_source_submanifest_sha256(document) == expected
    )
    changed = json.loads(_canonical_json(document))
    changed["entries"][0]["lines"] = 2
    assert (
        cp65._independent_recomputation_source_submanifest_sha256(changed) != expected
    )
    for mutation in ("missing-role", "duplicate-path", "out-of-order"):
        forged = json.loads(_canonical_json(document))
        if mutation == "missing-role":
            forged["entries"][0]["role"] = "production-runner-source"
        elif mutation == "duplicate-path":
            forged["entries"][1]["relative_path"] = forged["entries"][0][
                "relative_path"
            ]
        elif mutation == "out-of-order":
            forged["entries"] = list(reversed(forged["entries"]))
        with pytest.raises(ValueError):
            cp65._independent_recomputation_source_submanifest_sha256(forged)


def test_cp65_sha_pointer_zero_policies_are_exact_and_arm_conditioned(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    conditional = {
        (row.target_artifact_id, row.target_json_pointer): (
            row.zero_policy_id,
            row.conditional_binding_rule_id,
        )
        for row in authoritative_bundle.sha256_pointer_contracts
        if row.semantic_class == "conditional-zero-or-cross"
    }
    assert conditional == {
        ("preauthorization-outcome", "/prepared_launch_authorization_sha256",): (
            "authorization-arm-nonzero-final-launch-raw;terminal-arm-zero-iff-"
            "no-prepared-candidate-else-nonzero-rejected-candidate-raw",
            "preauthorization-prepared-candidate-branch-binding",
        ),
        ("terminal-state", "/launch_authorization_sha256"): (
            "zero-iff-preauthorization-terminal-otherwise-exact-raw-cross",
            "terminal-launch-authorization-arm-binding",
        ),
        ("terminal-state", "/postauthorization_outcome_sha256"): (
            "zero-unless-postauthorization-arm-exact-raw-cross",
            "terminal-postauthorization-outcome-arm-binding",
        ),
        ("terminal-state", "/started_receipt_sha256"): (
            "zero-unless-started-arm-exact-raw-cross",
            "terminal-started-receipt-arm-binding",
        ),
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/device_identity_sha256",
        ): (
            "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
            "auxiliary-device-identity-committed-marker-zero-arm-binding",
        ),
        ("auxiliary-metadata-reservation", "/artifact_entries/*/extent_map_sha256",): (
            "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
            "auxiliary-extent-map-committed-marker-zero-arm-binding",
        ),
    }
    for row in authoritative_bundle.sha256_pointer_contracts:
        if (row.target_artifact_id, row.target_json_pointer) in conditional:
            if row.target_artifact_id == "auxiliary-metadata-reservation":
                assert row.externally_retained_preimage_required
                assert row.preimage_registry_entry_required
                assert cp65._sha256_pointer_expanded_cardinality(row) == 183
                assert cp65._sha256_pointer_registry_entry_cardinality(row) == 182
            else:
                assert not row.externally_retained_preimage_required
                assert not row.preimage_registry_entry_required
                assert cp65._sha256_pointer_registry_entry_cardinality(row) == 0
            continue
        assert row.zero_policy_id == "nonzero-required"
        assert row.conditional_binding_rule_id == (
            "unconditional-classified-digest-binding"
        )

    registry_rows = tuple(
        row
        for row in authoritative_bundle.sha256_pointer_contracts
        if row.target_artifact_id == "external-digest-preimage-registry"
    )
    assert registry_rows
    assert all(not row.preimage_registry_entry_required for row in registry_rows)


@pytest.mark.parametrize(
    "target_key,replacement",
    (
        ("device_identity_sha256", "a" * 64),
        ("extent_map_sha256", "b" * 64),
    ),
)
def test_cp65_aux_committed_slot_rejects_nonzero_conditional_identity(
    target_key: str, replacement: str
) -> None:
    document = _auxiliary_reservation_document()
    row = next(
        item
        for item in document["artifact_entries"]
        if item["artifact_id"] == "committed-marker"
    )
    row[target_key] = replacement
    row["entry_sha256"] = _ZERO_SHA256
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0" + _canonical_json(row)
    ).hexdigest()
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "auxiliary-metadata-reservation",
            "auxiliary_metadata_reservation.json",
            _receipt_payload("auxiliary-metadata-reservation", document),
        )


@pytest.mark.parametrize(
    "target_key",
    ("device_identity_sha256", "extent_map_sha256"),
)
def test_cp65_aux_preallocated_slot_rejects_zero_conditional_identity(
    target_key: str,
) -> None:
    document = _auxiliary_reservation_document()
    row = next(
        item
        for item in document["artifact_entries"]
        if item["reservation_state"] == "preallocated-partial-in-place"
    )
    row[target_key] = _ZERO_SHA256
    row["entry_sha256"] = _ZERO_SHA256
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0" + _canonical_json(row)
    ).hexdigest()
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "auxiliary-metadata-reservation",
            "auxiliary_metadata_reservation.json",
            _receipt_payload("auxiliary-metadata-reservation", document),
        )


def test_cp65_all_four_signature_families_have_exact_preimages_and_raw_digests(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    contracts = {
        row.contract_id: row for row in authoritative_bundle.digest_preimage_contracts
    }
    families = (
        (
            "launch-authorization:unsigned-preimage",
            "launch-authorization:raw-signature",
        ),
        (
            "seed-source-authority-attestation:unsigned-preimage",
            "seed-source-authority-attestation:raw-signature",
        ),
        (
            "independent-signoff-set:row-unsigned-preimage",
            "independent-signoff-set:row-raw-signature",
        ),
        (
            "power-review-signoff:unsigned-preimage",
            "power-review-signoff:raw-signature",
        ),
    )
    for unsigned_id, signature_id in families:
        unsigned = contracts[unsigned_id]
        signature = contracts[signature_id]
        assert unsigned.domain_separator.endswith("signature-preimage-v1\0")
        assert unsigned.zeroed_field_pointers[-1].endswith("body_sha256") or (
            unsigned.zeroed_field_pointers[-1].endswith("signoff_sha256")
        )
        assert signature.domain_separator == ""
        assert signature.output_bytes == 32
        assert unsigned.verifier_implemented and signature.verifier_implemented
        family_id = unsigned_id.split(":", 1)[0]
        document = {"family_id": family_id}
        for pointer in unsigned.zeroed_field_pointers:
            leaf = pointer.rsplit("/", 1)[-1]
            document[leaf] = "a" * 64
        zeroed = dict(document)
        for pointer in unsigned.zeroed_field_pointers:
            leaf = pointer.rsplit("/", 1)[-1]
            zeroed[leaf] = "" if leaf.endswith("signature_hex") else _ZERO_SHA256
        message = unsigned.domain_separator.encode("ascii") + _canonical_json(zeroed)
        raw_signature = _test_rsa_pss_signature(message, family_id)
        modulus = _TEST_RSA_N.to_bytes(384, "big")
        assert cp65._verify_rsa_pss_sha256_3072(message, modulus, raw_signature)
        assert hashlib.sha256(raw_signature).hexdigest() != _ZERO_SHA256
        forged = bytearray(raw_signature)
        forged[-1] ^= 1
        assert not cp65._verify_rsa_pss_sha256_3072(message, modulus, bytes(forged))
        assert not cp65._verify_rsa_pss_sha256_3072(
            message + b"x", modulus, raw_signature
        )

    message = b"cp65-test-rsa-profile-negative-vector"
    signature = _test_rsa_pss_signature(message, "profile-negative")
    modulus = _TEST_RSA_N.to_bytes(384, "big")
    assert not cp65._verify_rsa_pss_sha256_3072(message, modulus[:-1], signature)
    assert not cp65._verify_rsa_pss_sha256_3072(
        message, (_TEST_RSA_N - 1).to_bytes(384, "big"), signature
    )
    assert not cp65._verify_rsa_pss_sha256_3072(
        message, modulus, _TEST_RSA_N.to_bytes(384, "big")
    )


@pytest.mark.parametrize(
    "artifact_id,relative_path,key_artifact_id,key_relative_path,builder",
    (
        (
            "launch-authorization",
            "launch_authorization.json",
            "launch-authority-public-key",
            "frozen_inputs/launch_authority_public_key.json",
            _launch_authorization_pair,
        ),
        (
            "seed-source-authority-attestation",
            "seed_source_authority_attestation.json",
            "seed-source-authority-public-key",
            "frozen_inputs/seed_source_authority_public_key.json",
            _seed_source_attestation_pair,
        ),
        (
            "power-review-signoff",
            "power_review_signoff.json",
            "independent-reviewer-public-key-set",
            "frozen_inputs/independent_reviewer_public_keys.json",
            _power_review_signoff_pair,
        ),
    ),
)
def test_cp65_supplied_set_aggregates_every_nonset_signature_family(
    artifact_id: str,
    relative_path: str,
    key_artifact_id: str,
    key_relative_path: str,
    builder: object,
) -> None:
    assert callable(builder)
    signed_payload, key_payload = builder()
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (artifact_id, relative_path, signed_payload),
            (key_artifact_id, key_relative_path, key_payload),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert result.signature_verification_applicable
    assert result.signature_mathematically_valid_under_supplied_key
    assert result.unresolved_cross_binding_count > 0
    assert not result.external_provenance_verified
    assert not result.authority_verified
    assert not result.gate_transition_permitted
    assert not result.launch_authorized

    corrupted_payload, corrupted_key_payload = builder(corrupt_signature=True)
    corrupted = cp65.cp65_validate_supplied_artifact_set(
        (
            (artifact_id, relative_path, corrupted_payload),
            (key_artifact_id, key_relative_path, corrupted_key_payload),
        )
    )
    assert corrupted.syntax_valid
    assert corrupted.signature_verification_applicable
    assert not corrupted.signature_mathematically_valid_under_supplied_key
    assert not corrupted.authority_verified
    assert not corrupted.gate_transition_permitted


def test_cp65_launch_signature_convenience_wrapper_matches_set_aggregation() -> None:
    authorization, key = _launch_authorization_pair()
    direct = cp65.cp65_verify_launch_authorization_signature(authorization, key)
    supplied_set = cp65.cp65_validate_supplied_artifact_set(
        (
            ("launch-authorization", "launch_authorization.json", authorization),
            (
                "launch-authority-public-key",
                "frozen_inputs/launch_authority_public_key.json",
                key,
            ),
        )
    )
    for result in (direct, supplied_set):
        assert result.signature_verification_applicable
        assert result.signature_mathematically_valid_under_supplied_key
        assert not result.authorization_trust_root_bound
        assert not result.authority_verified
        assert not result.launch_authorized


def test_cp65_signature_result_is_applicable_if_signed_bytes_are_supplied() -> None:
    summary = _preflight_summary_payload()
    reviewer_keys, reviewer_rows = _reviewer_key_set_payload()
    signoff = _independent_signoff_set_payload(summary, reviewer_keys, reviewer_rows)
    launch, launch_key = _launch_authorization_pair(
        preflight_summary_raw_sha256=hashlib.sha256(summary).hexdigest(),
        independent_signoff_raw_sha256=hashlib.sha256(signoff).hexdigest(),
    )
    source, source_key = _seed_source_attestation_pair()
    power, power_keys = _power_review_signoff_pair()
    assert power_keys == reviewer_keys
    signed_without_keys = (
        ("launch-authorization", "launch_authorization.json", launch),
        (
            "seed-source-authority-attestation",
            "seed_source_authority_attestation.json",
            source,
        ),
        ("power-review-signoff", "power_review_signoff.json", power),
        ("independent-signoff-set", "independent_signoff.json", signoff),
    )
    for item in signed_without_keys:
        result = cp65.cp65_validate_supplied_artifact_set((item,))
        assert result.syntax_valid
        assert result.signature_verification_applicable
        assert not result.signature_mathematically_valid_under_supplied_key
        assert result.unresolved_cross_binding_count > 0
        assert not result.authority_verified
        assert not result.gate_transition_permitted

    all_valid_items = (
        signed_without_keys[0],
        (
            "launch-authority-public-key",
            "frozen_inputs/launch_authority_public_key.json",
            launch_key,
        ),
        signed_without_keys[1],
        (
            "seed-source-authority-public-key",
            "frozen_inputs/seed_source_authority_public_key.json",
            source_key,
        ),
        signed_without_keys[2],
        (
            "independent-reviewer-public-key-set",
            "frozen_inputs/independent_reviewer_public_keys.json",
            reviewer_keys,
        ),
        (
            "preflight-gate-summary",
            "preflight_gate_summary.json",
            summary,
        ),
        signed_without_keys[3],
    )
    all_valid = cp65.cp65_validate_supplied_artifact_set(all_valid_items)
    assert all_valid.signature_verification_applicable
    assert all_valid.signature_mathematically_valid_under_supplied_key

    corrupt_source, _same_key = _seed_source_attestation_pair(corrupt_signature=True)
    one_invalid = list(all_valid_items)
    one_invalid[2] = (
        "seed-source-authority-attestation",
        "seed_source_authority_attestation.json",
        corrupt_source,
    )
    aggregate = cp65.cp65_validate_supplied_artifact_set(tuple(one_invalid))
    assert aggregate.signature_verification_applicable
    assert not aggregate.signature_mathematically_valid_under_supplied_key
    assert not aggregate.authority_verified
    assert not aggregate.gate_transition_permitted


def test_cp65_retained_bundle_roundtrips_under_the_128_member_parser_cap(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    payload = cp65.cp65_canonical_json_bytes(authoritative_bundle)
    parsed = cp65._parse_canonical_json_object(payload, 67_108_864)
    assert 65 <= len(parsed) <= 128
    observation = cp65.cp65_validate_supplied_artifact_bytes(
        "production-schema-preimage-validator-bundle",
        "frozen_inputs/production_schema_preimage_validator_bundle.json",
        payload,
    )
    assert observation.syntax_valid
    assert observation.intrinsic_digest_preimages_valid
    assert not observation.digest_preimages_valid
    assert observation.unresolved_digest_preimage_count > 0
    assert observation.definition_only
    assert not observation.external_production_receipts_observed
    assert not observation.launch_authorized
    assert not observation.execution_permitted


def test_cp65_source_archive_roundtrip_is_cross_checked_against_manifest() -> None:
    entries = (
        ("src/example.py", b"x = 1\n"),
        ("tests/empty.bin", b""),
        ("tests/fixture.json", b"{}\n"),
        ("tests/no_final_lf.txt", b"first\nsecond"),
    )
    archive = _source_materialization(entries)
    manifest_rows = [
        {
            "ordinal": ordinal,
            "role": (
                "production-runner-source"
                if path.startswith("src/")
                else "independent-recomputation-source"
            ),
            "relative_path": path,
            "bytes": len(content),
            "lines": (
                0
                if not content
                else content.count(b"\n") + int(not content.endswith(b"\n"))
            ),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for ordinal, (path, content) in enumerate(entries, 1)
    ]
    manifest = {
        "schema": "cp65-test28-source-manifest-v1",
        "purpose": "frozen-source-fixture-materialization-custody",
        "attempt_id": "attempt-development-only",
        "protocol_sha256": "1" * 64,
        "machine_manifest_sha256": "2" * 64,
        "entry_count": len(manifest_rows),
        "total_bytes": sum(row["bytes"] for row in manifest_rows),
        "entries": manifest_rows,
        "ordered_entries_sha256": hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + _canonical_json(manifest_rows)
        ).hexdigest(),
        "body_sha256": _ZERO_SHA256,
    }
    manifest_payload = _receipt_payload("source-manifest", manifest)
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "frozen-source-fixture-materialization",
                "frozen_inputs/source_fixture_materialization.bin",
                archive,
            ),
            ("source-manifest", "frozen_inputs/bound_files.json", manifest_payload),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid

    forged_ordered = dict(manifest)
    forged_ordered["ordered_entries_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "source-manifest",
            "frozen_inputs/bound_files.json",
            _receipt_payload("source-manifest", forged_ordered),
        )

    forged = dict(manifest)
    forged_rows = [dict(row) for row in manifest_rows]
    forged_rows[0]["bytes"] += 1
    forged["entries"] = forged_rows
    forged["total_bytes"] += 1
    forged["ordered_entries_sha256"] = hashlib.sha256(
        b"cp65-test28-source-manifest-ordered-entries-v1\0"
        + _canonical_json(forged_rows)
    ).hexdigest()
    forged_payload = _receipt_payload("source-manifest", forged)
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "frozen-source-fixture-materialization",
                    "frozen_inputs/source_fixture_materialization.bin",
                    archive,
                ),
                ("source-manifest", "frozen_inputs/bound_files.json", forged_payload),
            )
        )

    for row_index, changed_lines in ((0, 2), (1, 1), (2, 2), (3, 1)):
        forged = dict(manifest)
        forged_rows = [dict(row) for row in manifest_rows]
        forged_rows[row_index]["lines"] = changed_lines
        forged["entries"] = forged_rows
        forged["ordered_entries_sha256"] = hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + _canonical_json(forged_rows)
        ).hexdigest()
        forged_payload = _receipt_payload("source-manifest", forged)
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_set(
                (
                    (
                        "frozen-source-fixture-materialization",
                        "frozen_inputs/source_fixture_materialization.bin",
                        archive,
                    ),
                    (
                        "source-manifest",
                        "frozen_inputs/bound_files.json",
                        forged_payload,
                    ),
                )
            )


def test_cp65_source_manifest_entry_cardinality_is_exactly_one_through_4096(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    assert rules[("source-manifest", "/entry_count")].integer_interval == (1, 4_096)
    assert rules[("source-manifest", "/entries")].length_interval == (1, 4_096)

    def payload(entry_count: int) -> bytes:
        empty_sha256 = hashlib.sha256(b"").hexdigest()
        entries = [
            {
                "ordinal": ordinal,
                "role": (
                    "production-runner-source"
                    if ordinal == 1
                    else "independent-recomputation-source"
                ),
                "relative_path": "src/file-%04d.py" % ordinal,
                "bytes": 0,
                "lines": 0,
                "sha256": empty_sha256,
            }
            for ordinal in range(1, entry_count + 1)
        ]
        return _receipt_payload(
            "source-manifest",
            {
                "schema": "cp65-test28-source-manifest-v1",
                "purpose": "frozen-source-fixture-materialization-custody",
                "attempt_id": "attempt-development-only",
                "protocol_sha256": "1" * 64,
                "machine_manifest_sha256": "2" * 64,
                "entry_count": entry_count,
                "total_bytes": 0,
                "entries": entries,
                "ordered_entries_sha256": hashlib.sha256(
                    b"cp65-test28-source-manifest-ordered-entries-v1\0"
                    + _canonical_json(entries)
                ).hexdigest(),
                "body_sha256": _ZERO_SHA256,
            },
        )

    maximum = cp65.cp65_validate_supplied_artifact_bytes(
        "source-manifest", "frozen_inputs/bound_files.json", payload(4_096)
    )
    assert maximum.syntax_valid and maximum.intrinsic_digest_preimages_valid
    for forbidden_count in (0, 4_097):
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                "source-manifest",
                "frozen_inputs/bound_files.json",
                payload(forbidden_count),
            )


def test_cp65_path_aware_set_rejects_duplicates_aliases_and_wrong_shard_width() -> None:
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                ("frozen-protocol", "frozen_inputs/protocol.md", b"a"),
                ("dependency-lock", "frozen_inputs/protocol.md", b"b"),
            )
        )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "shard-requests", "shards/shard-01/requests.jsonl", b"{}\n"
        )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "shard-requests", "shards/{shard_id}/requests.jsonl", b"{}\n"
        )
    launch_candidate = b'{"not":"a-final-launch-receipt"}'
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "launch-authorization",
            "launch_authorization.json.partial",
            launch_candidate,
        )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "rejected-launch-authorization-candidate",
            "rejected_launch_authorization_candidate.json.partial",
            launch_candidate,
        )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            tuple(
                ("frozen-protocol", "frozen_inputs/protocol-%03d.md" % index, b"x")
                for index in range(313)
            )
        )


def test_cp65_auxiliary_transition_journal_is_fixed_bounded_and_receipt_bound(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    schema = cp65.cp65_artifact_schema("auxiliary-reservation-transition-journal")
    assert schema.path_template == "auxiliary_reservation_transition_journal.bin"
    assert schema.minimum_bytes_per_instance == 65_536
    assert schema.maximum_bytes_per_instance == 65_536
    assert schema.media_kind == "binary-transition-journal"

    auxiliary_payload = _receipt_payload(
        "auxiliary-metadata-reservation", _auxiliary_reservation_document()
    )
    journal, head = _auxiliary_transition_journal(
        auxiliary_payload, authoritative_bundle.schema_semantic_sha256
    )
    assert len(journal) == 65_536
    assert journal[:8] == b"CP65AUX1"
    assert int.from_bytes(journal[112:120], "big") == 255
    assert int.from_bytes(journal[120:128], "big") == 256
    assert head == journal[80:112].hex()
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "auxiliary-metadata-reservation",
                "auxiliary_metadata_reservation.json",
                auxiliary_payload,
            ),
            (
                "auxiliary-reservation-transition-journal",
                "auxiliary_reservation_transition_journal.bin",
                journal,
            ),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid


@pytest.mark.parametrize(
    "mutation_offset",
    (0, 8, 80, 112, 120, 128, 256, 512),
)
def test_cp65_auxiliary_transition_journal_rejects_header_and_torn_suffix_mutations(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
    mutation_offset: int,
) -> None:
    auxiliary_payload = _receipt_payload(
        "auxiliary-metadata-reservation", _auxiliary_reservation_document()
    )
    journal, _head = _auxiliary_transition_journal(
        auxiliary_payload, authoritative_bundle.schema_semantic_sha256
    )
    forged = bytearray(journal)
    forged[mutation_offset] ^= 1
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "auxiliary-metadata-reservation",
                    "auxiliary_metadata_reservation.json",
                    auxiliary_payload,
                ),
                (
                    "auxiliary-reservation-transition-journal",
                    "auxiliary_reservation_transition_journal.bin",
                    bytes(forged),
                ),
            )
        )


def _final_auxiliary_transition_sequence() -> tuple[
    tuple[int, int, int, int, int, int, str, str], ...
]:
    rows = _auxiliary_slot_rows()
    slots = {row["artifact_id"]: row for row in rows}
    excluded = {
        "preterminal-durable-artifact-inventory",
        "terminal-state",
        "sha256-manifest",
        "committed-marker",
        "auxiliary-reservation-transition-journal",
    }
    ordinary = next(row for row in rows if row["artifact_id"] not in excluded)
    allocated = 23_219_732_480
    hold = 11_140_005_888

    def target(row: dict, code: int) -> tuple[int, int, int, int, int, int, str, str]:
        nonlocal allocated, hold
        before, hold_before = allocated, hold
        after = before - 4_096
        hold_after = hold_before + 4_096
        allocated, hold = after, hold_after
        return (
            row["ordinal"],
            code,
            before,
            after,
            hold_before,
            hold_after,
            hashlib.sha256(row["final_relative_path"].encode("ascii")).hexdigest(),
            hashlib.sha256(
                ("raw:" + row["final_relative_path"]).encode("ascii")
            ).hexdigest(),
        )

    transitions = [target(ordinary, 1)]
    transitions.append(target(slots["preterminal-durable-artifact-inventory"], 3))
    transitions.append(target(slots["terminal-state"], 4))
    transitions.append(target(slots["sha256-manifest"], 5))
    transitions.append(
        (0, 6, allocated, allocated, hold, hold, _ZERO_SHA256, _ZERO_SHA256)
    )
    return tuple(transitions)


def _complete_auxiliary_terminal_publication_items() -> tuple[
    tuple[tuple[str, str, bytes], ...], dict[str, bytes]
]:
    dependency_lock = (
        _PROJECT_ROOT / "requirements/m1-reference-macos-arm64-py311.lock"
    ).read_bytes()
    document = _auxiliary_reservation_document()
    dependency_allocated = ((len(dependency_lock) + 4_095) // 4_096) * 4_096
    dependency_row = _make_auxiliary_slot_existing(
        document, "dependency-lock", dependency_allocated
    )
    draft_auxiliary = _receipt_payload("auxiliary-metadata-reservation", document)
    auxiliary_allocated = ((len(draft_auxiliary) + 4_095) // 4_096) * 4_096
    _make_auxiliary_slot_existing(
        document, "auxiliary-metadata-reservation", auxiliary_allocated
    )
    auxiliary = _receipt_payload("auxiliary-metadata-reservation", document)
    assert ((len(auxiliary) + 4_095) // 4_096) * 4_096 == auxiliary_allocated
    rows = {row["artifact_id"]: row for row in document["artifact_entries"]}
    allocated = (
        document["unique_nonhold_artifact_allocated_bytes"]
        + document["disjoint_allocation_and_directory_charge_bytes"]
    )
    hold = document["hold_allocated_bytes"]

    def target(
        row: dict, code: int, payload: bytes
    ) -> tuple[int, int, int, int, int, int, str, str]:
        nonlocal allocated, hold
        before = allocated
        hold_before = hold
        if code == 2:
            after = before
            hold_after = hold_before
        else:
            actual = ((len(payload) + 4_095) // 4_096) * 4_096
            released = row["reserved_bytes"] - actual
            assert released >= 0
            after = before - released
            hold_after = hold_before + released
        allocated, hold = after, hold_after
        return (
            row["ordinal"],
            code,
            before,
            after,
            hold_before,
            hold_after,
            hashlib.sha256(row["final_relative_path"].encode("ascii")).hexdigest(),
            hashlib.sha256(payload).hexdigest(),
        )

    transitions = [target(dependency_row, 2, dependency_lock)]
    _journal, preinventory_head = _auxiliary_transition_journal(
        auxiliary,
        cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
        tuple(transitions),
    )
    inventory_entries = [
        _inventory_entry(1, "auxiliary_metadata_reservation.json", auxiliary),
        _inventory_entry(2, "frozen_inputs/dependency_lock.txt", dependency_lock),
    ]
    inventory = _preterminal_inventory_payload(
        inventory_entries,
        transition_entry_count=len(transitions),
        transition_head_sha256=preinventory_head,
    )
    transitions.append(
        target(rows["preterminal-durable-artifact-inventory"], 3, inventory)
    )
    _journal, after_inventory_head = _auxiliary_transition_journal(
        auxiliary,
        cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
        tuple(transitions),
    )
    terminal = _terminal_state_payload(
        inventory,
        transition_entry_count=len(transitions),
        transition_head_sha256=after_inventory_head,
    )
    transitions.append(target(rows["terminal-state"], 4, terminal))
    _journal, after_terminal_head = _auxiliary_transition_journal(
        auxiliary,
        cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
        tuple(transitions),
    )
    manifest = _sha256_manifest_payload(
        inventory_entries,
        inventory,
        terminal,
        transition_entry_count=len(transitions),
        transition_head_sha256=after_terminal_head,
    )
    transitions.append(target(rows["sha256-manifest"], 5, manifest))
    transitions.append(
        (0, 6, allocated, allocated, hold, hold, _ZERO_SHA256, _ZERO_SHA256)
    )
    journal, final_head = _auxiliary_transition_journal(
        auxiliary,
        cp65.cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
        tuple(transitions),
    )
    committed = _receipt_payload(
        "committed-marker",
        {
            "schema": "cp65-test28-committed-marker-v3",
            "purpose": "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
            "attempt_id": "attempt-development-only",
            "terminal_state_sha256": hashlib.sha256(terminal).hexdigest(),
            "sha256_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "auxiliary_metadata_reservation_sha256": hashlib.sha256(
                auxiliary
            ).hexdigest(),
            "auxiliary_reservation_transition_journal_sha256": hashlib.sha256(
                journal
            ).hexdigest(),
            "auxiliary_reservation_transition_journal_final_head_sha256": (final_head),
            "auxiliary_reservation_transition_journal_final_entry_count": len(
                transitions
            ),
            "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc": (
                "2026-01-01T00:00:00.000004Z"
            ),
            "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc": (
                "2026-01-01T00:00:00.000005Z"
            ),
            "hold_relative_path": document["hold_relative_path"],
            "hold_device_identity_sha256": document["hold_device_identity_sha256"],
            "hold_inode": document["hold_inode"],
            "hold_extent_map_sha256": document["hold_extent_map_sha256"],
            "hold_removed_at_utc": "2026-01-01T00:00:00.000006Z",
            "hold_removal_directory_fsync_completed_at_utc": (
                "2026-01-01T00:00:00.000007Z"
            ),
            "hold_absence_verified": True,
            "committed_at_utc": "2026-01-01T00:00:00.000008Z",
            "body_sha256": _ZERO_SHA256,
        },
    )
    payloads = {
        "auxiliary-metadata-reservation": auxiliary,
        "auxiliary-reservation-transition-journal": journal,
        "dependency-lock": dependency_lock,
        "preterminal-durable-artifact-inventory": inventory,
        "terminal-state": terminal,
        "sha256-manifest": manifest,
        "committed-marker": committed,
    }
    paths = {
        artifact_id: next(
            row[1] for row in cp65._ARTIFACT_DECLARATIONS if row[0] == artifact_id
        )
        for artifact_id in payloads
    }
    items = tuple(
        (artifact_id, paths[artifact_id], payload)
        for artifact_id, payload in payloads.items()
    )
    return items, payloads


def test_cp65_full_auxiliary_journal_terminal_commit_chain_is_derived() -> None:
    items, payloads = _complete_auxiliary_terminal_publication_items()
    result = cp65.cp65_validate_supplied_artifact_set(items)
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert result.validated_cross_binding_count >= 20
    assert result.unresolved_cross_binding_count > 0
    assert not result.cross_bindings_valid
    assert not result.production_evidence_accepted

    targets = (
        (
            "preterminal-durable-artifact-inventory",
            "auxiliary_transition_journal_prefix_head_sha256",
        ),
        (
            "terminal-state",
            "auxiliary_transition_journal_after_inventory_head_sha256",
        ),
        (
            "sha256-manifest",
            "auxiliary_transition_journal_after_terminal_head_sha256",
        ),
        (
            "committed-marker",
            "auxiliary_reservation_transition_journal_final_head_sha256",
        ),
        (
            "committed-marker",
            "auxiliary_reservation_transition_journal_final_entry_count",
        ),
        (
            "committed-marker",
            "auxiliary_reservation_transition_journal_sha256",
        ),
    )
    for artifact_id, field in targets:
        document = json.loads(payloads[artifact_id])
        document[field] = (
            document[field] + 1 if type(document[field]) is int else "f" * 64
        )
        forged_payload = _receipt_payload(artifact_id, document)
        forged_items = tuple(
            (row[0], row[1], forged_payload if row[0] == artifact_id else row[2])
            for row in items
        )
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_set(forged_items)


def test_cp65_auxiliary_transition_journal_final_code_sequence_and_conservation(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    auxiliary_payload = _receipt_payload(
        "auxiliary-metadata-reservation", _auxiliary_reservation_document()
    )
    transitions = _final_auxiliary_transition_sequence()
    journal, head = _auxiliary_transition_journal(
        auxiliary_payload,
        authoritative_bundle.schema_semantic_sha256,
        transitions,
    )
    count, observed_head, parsed = cp65._auxiliary_transition_journal_prefix(
        journal,
        expected_auxiliary_reservation_raw_sha256=hashlib.sha256(
            auxiliary_payload
        ).hexdigest(),
        expected_schema_semantic_sha256=authoritative_bundle.schema_semantic_sha256,
    )
    assert count == len(transitions) == 5
    assert observed_head == head
    assert tuple(row[2] for row in parsed[-4:]) == (3, 4, 5, 6)
    assert all(row[3] + row[5] == row[4] + row[6] == 34_359_738_368 for row in parsed)

    for mutation in (
        "broken-conservation",
        "broken-continuity",
        "checkpoint-order",
        "zero-ordinary-target",
        "nonzero-seal-target",
        "entry-after-seal",
    ):
        forged = [list(row) for row in transitions]
        if mutation == "broken-conservation":
            forged[0][3] += 1
        elif mutation == "broken-continuity":
            forged[1][2] += 1
        elif mutation == "checkpoint-order":
            forged[1][1], forged[2][1] = forged[2][1], forged[1][1]
        elif mutation == "zero-ordinary-target":
            forged[0][6] = _ZERO_SHA256
        elif mutation == "nonzero-seal-target":
            forged[-1][6] = "f" * 64
        elif mutation == "entry-after-seal":
            forged.append(list(forged[0]))
            forged[-1][0] = forged[0][0]
            forged[-1][1] = 2
            forged[-1][2:6] = forged[-2][2:6]
        else:  # pragma: no cover
            raise AssertionError(mutation)
        payload, _ = _auxiliary_transition_journal(
            auxiliary_payload,
            authoritative_bundle.schema_semantic_sha256,
            tuple(tuple(row) for row in forged),
        )
        with pytest.raises(ValueError):
            cp65._auxiliary_transition_journal_prefix(payload)


def test_cp65_auxiliary_transition_code2_accepts_initial_and_transitioned_finals() -> None:
    protocol = (
        _PROJECT_ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
    ).read_bytes()
    protocol_item = (
        "frozen-protocol",
        "frozen_inputs/protocol.md",
        protocol,
    )
    protocol_raw_sha256 = hashlib.sha256(protocol).hexdigest()
    protocol_allocated_bytes = ((len(protocol) + 4_095) // 4_096) * 4_096

    initial_document = _auxiliary_reservation_document()
    initial_row = _make_auxiliary_slot_existing(
        initial_document, "frozen-protocol", protocol_allocated_bytes
    )
    initial_allocated = (
        initial_document["unique_nonhold_artifact_allocated_bytes"]
        + initial_document["disjoint_allocation_and_directory_charge_bytes"]
    )
    initial_hold = initial_document["hold_allocated_bytes"]
    initial_recheck = (
        initial_row["ordinal"],
        2,
        initial_allocated,
        initial_allocated,
        initial_hold,
        initial_hold,
        hashlib.sha256(initial_row["final_relative_path"].encode("ascii")).hexdigest(),
        protocol_raw_sha256,
    )
    for transitions in ((initial_recheck,), (initial_recheck, initial_recheck)):
        result = _validate_auxiliary_transition_pair(
            initial_document, transitions, extra_items=(protocol_item,)
        )
        assert result.syntax_valid and result.intrinsic_digest_preimages_valid

    transitioned_document = _auxiliary_reservation_document()
    transitioned_row = next(
        row
        for row in transitioned_document["artifact_entries"]
        if row["artifact_id"] == "frozen-protocol"
    )
    allocated_before = (
        transitioned_document["unique_nonhold_artifact_allocated_bytes"]
        + transitioned_document["disjoint_allocation_and_directory_charge_bytes"]
    )
    hold_before = transitioned_document["hold_allocated_bytes"]
    released_slack = transitioned_row["reserved_bytes"] - protocol_allocated_bytes
    allocated_after = allocated_before - released_slack
    hold_after = hold_before + released_slack
    target_path_sha256 = hashlib.sha256(
        transitioned_row["final_relative_path"].encode("ascii")
    ).hexdigest()
    code1 = (
        transitioned_row["ordinal"],
        1,
        allocated_before,
        allocated_after,
        hold_before,
        hold_after,
        target_path_sha256,
        protocol_raw_sha256,
    )
    code2 = (
        transitioned_row["ordinal"],
        2,
        allocated_after,
        allocated_after,
        hold_after,
        hold_after,
        target_path_sha256,
        protocol_raw_sha256,
    )
    result = _validate_auxiliary_transition_pair(
        transitioned_document,
        (code1, code2, code2),
        extra_items=(protocol_item,),
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid


@pytest.mark.parametrize(
    "mutation",
    (
        "untouched-preallocated",
        "live-journal",
        "future-o-excl",
        "code1-on-initial-final",
        "code2-changes-accounting",
        "wrong-final-path",
        "wrong-final-bytes",
    ),
)
def test_cp65_auxiliary_transition_code2_rejects_ineligible_or_false_rechecks(
    mutation: str,
) -> None:
    protocol = (
        _PROJECT_ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
    ).read_bytes()
    protocol_item = (
        "frozen-protocol",
        "frozen_inputs/protocol.md",
        protocol,
    )
    protocol_raw_sha256 = hashlib.sha256(protocol).hexdigest()
    protocol_allocated_bytes = ((len(protocol) + 4_095) // 4_096) * 4_096
    document = _auxiliary_reservation_document()
    if mutation in (
        "code1-on-initial-final",
        "code2-changes-accounting",
        "wrong-final-path",
        "wrong-final-bytes",
    ):
        row = _make_auxiliary_slot_existing(
            document, "frozen-protocol", protocol_allocated_bytes
        )
    elif mutation == "live-journal":
        row = next(
            item
            for item in document["artifact_entries"]
            if item["artifact_id"] == "auxiliary-reservation-transition-journal"
        )
    elif mutation == "future-o-excl":
        row = next(
            item
            for item in document["artifact_entries"]
            if item["artifact_id"] == "committed-marker"
        )
    else:
        row = next(
            item
            for item in document["artifact_entries"]
            if item["artifact_id"] == "frozen-protocol"
        )
    allocated = (
        document["unique_nonhold_artifact_allocated_bytes"]
        + document["disjoint_allocation_and_directory_charge_bytes"]
    )
    hold = document["hold_allocated_bytes"]
    code = 1 if mutation == "code1-on-initial-final" else 2
    allocated_after = allocated
    hold_after = hold
    if mutation == "code2-changes-accounting":
        allocated_after -= 4_096
        hold_after += 4_096
    target_path_sha256 = hashlib.sha256(
        row["final_relative_path"].encode("ascii")
    ).hexdigest()
    target_raw_sha256 = protocol_raw_sha256
    if mutation == "wrong-final-path":
        target_path_sha256 = "e" * 64
    elif mutation in ("wrong-final-bytes", "live-journal", "future-o-excl"):
        target_raw_sha256 = "f" * 64
    transition = (
        row["ordinal"],
        code,
        allocated,
        allocated_after,
        hold,
        hold_after,
        target_path_sha256,
        target_raw_sha256,
    )
    with pytest.raises(ValueError):
        _validate_auxiliary_transition_pair(
            document, (transition,), extra_items=(protocol_item,)
        )


def test_cp65_auxiliary_v3_derives_183_physical_slots_and_dynamic_complement() -> None:
    document = _auxiliary_reservation_document()
    rows = document["artifact_entries"]
    assert len(rows) == 183
    assert [row["ordinal"] for row in rows] == list(range(1, 184))
    assert [row["final_relative_path"] for row in rows] == sorted(
        row["final_relative_path"] for row in rows
    )
    assert len({row["final_relative_path"] for row in rows}) == 183
    assert len({(row["device_identity_sha256"], row["inode"]) for row in rows}) == 183
    assert len({row["extent_map_sha256"] for row in rows}) == 183
    assert document["artifact_slot_reserved_bytes"] == 22_213_099_520
    authorization = next(
        row for row in rows if row["artifact_id"] == "launch-authorization"
    )
    assert authorization["partial_relative_path"] == "launch_authorization.json.partial"
    assert authorization["alternate_final_relative_path"] == (
        "rejected_launch_authorization_candidate.json"
    )
    assert authorization["primary_publication_arm_id"] == "AUTHORIZATION"
    assert authorization["alternate_publication_arm_id"] == (
        "PREAUTHORIZATION_TERMINAL"
    )
    assert not any(
        row["artifact_id"] == "rejected-launch-authorization-candidate" for row in rows
    )
    committed = next(row for row in rows if row["artifact_id"] == "committed-marker")
    assert committed["reservation_state"] == "future-o-excl-covered-by-hold"
    assert committed["partial_relative_path"] == ""
    assert committed["device_identity_sha256"] == _ZERO_SHA256
    assert committed["inode"] == 0
    assert committed["extent_map_sha256"] == _ZERO_SHA256
    assert committed["primary_publication_arm_id"] == (
        "DIRECT_O_EXCL_AFTER_HOLD_RELEASE"
    )
    assert not committed["non_sparse_verified"]
    assert not committed["exclusive_verified"]
    transition_journal = next(
        row
        for row in rows
        if row["artifact_id"] == "auxiliary-reservation-transition-journal"
    )
    assert transition_journal["reservation_state"] == (
        "preallocated-live-journal-in-place"
    )
    assert transition_journal["partial_relative_path"] == (
        "auxiliary_reservation_transition_journal.bin"
    )
    assert transition_journal["reserved_bytes"] == 65_536
    assert transition_journal["primary_publication_arm_id"] == (
        "IN_PLACE_TRANSITION_JOURNAL"
    )
    assert document["hold_allocated_bytes"] == 11_140_005_888
    assert (
        document["unique_nonhold_artifact_allocated_bytes"]
        + document["disjoint_allocation_and_directory_charge_bytes"]
        + document["hold_allocated_bytes"]
        == document["physical_reservation_sum_bytes"]
        == 34_359_738_368
    )
    assert document["unique_nonhold_artifact_allocated_bytes"] == (
        document["allocated_existing_final_bytes"]
        + document["allocated_future_partial_bytes"]
    )
    assert (
        document["exclusive_root_charge_current_bytes"]
        - document["exclusive_root_charge_baseline_bytes"]
        == document["physical_reservation_sum_bytes"]
    )
    payload = _receipt_payload("auxiliary-metadata-reservation", document)
    observation = cp65.cp65_validate_supplied_artifact_bytes(
        "auxiliary-metadata-reservation",
        "auxiliary_metadata_reservation.json",
        payload,
    )
    assert observation.syntax_valid and observation.intrinsic_digest_preimages_valid
    assert not observation.digest_preimages_valid
    assert not observation.filesystem_observed
    assert not observation.production_evidence_accepted


def test_cp65_auxiliary_root_charge_is_disjoint_measured_and_registry_bound(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    assert "observed_allocation_and_directory_charge_bytes" not in (
        cp65._AUXILIARY_RESERVATION_KEYS
    )
    assert cp65._AUXILIARY_RESERVATION_KEYS[6:10] == (
        "measurement_session_sha256",
        "exclusive_root_charge_measurement_sha256",
        "storage_root_identity_sha256",
        "filesystem_identity_sha256",
    )
    allocated = cp65._AUXILIARY_RESERVATION_KEYS.index("allocated_future_partial_bytes")
    assert cp65._AUXILIARY_RESERVATION_KEYS[allocated + 1 : allocated + 5] == (
        "unique_nonhold_artifact_allocated_bytes",
        "exclusive_root_charge_baseline_bytes",
        "exclusive_root_charge_current_bytes",
        "disjoint_allocation_and_directory_charge_bytes",
    )
    contracts = {
        row.contract_id: row for row in authoritative_bundle.digest_preimage_contracts
    }
    contract_id = (
        "auxiliary-metadata-reservation:exclusive-root-charge-measurement-sha256"
    )
    assert contracts[contract_id].domain_separator == (
        "cp65-test28-exclusive-root-charge-measurement-v1\0"
    )
    pointer = next(
        row
        for row in authoritative_bundle.sha256_pointer_contracts
        if row.target_artifact_id == "auxiliary-metadata-reservation"
        and row.target_json_pointer == "/exclusive_root_charge_measurement_sha256"
    )
    assert pointer.source_contract_id == contract_id
    assert pointer.preimage_registry_entry_required
    assert cp65._sha256_pointer_registry_entry_cardinality(pointer) == 1
    predicates = {
        row.predicate_id: row for row in authoritative_bundle.predicate_contracts
    }
    predicate = predicates["auxiliary-exclusive-root-charge-disjoint-conservation"]
    assert predicate.validator_implemented

    for mutation in (
        "current-charge",
        "unique-double-credit",
        "disjoint-over-policy",
        "zero-hold",
        "measurement-digest",
    ):
        document = _auxiliary_reservation_document()
        if mutation == "current-charge":
            document["exclusive_root_charge_current_bytes"] += 1
        elif mutation == "unique-double-credit":
            document["unique_nonhold_artifact_allocated_bytes"] += 1
            document["exclusive_root_charge_current_bytes"] += 1
        elif mutation == "disjoint-over-policy":
            document["disjoint_allocation_and_directory_charge_bytes"] += 1
            document["exclusive_root_charge_current_bytes"] += 1
        elif mutation == "zero-hold":
            document["hold_allocated_bytes"] = 0
            document["exclusive_root_charge_current_bytes"] = (
                document["exclusive_root_charge_baseline_bytes"]
                + document["unique_nonhold_artifact_allocated_bytes"]
                + document["disjoint_allocation_and_directory_charge_bytes"]
            )
        elif mutation == "measurement-digest":
            document["exclusive_root_charge_measurement_sha256"] = "f" * 64
        else:  # pragma: no cover
            raise AssertionError(mutation)
        if mutation != "measurement-digest":
            _refinish_exclusive_root_charge_measurement(document)
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                "auxiliary-metadata-reservation",
                "auxiliary_metadata_reservation.json",
                _receipt_payload("auxiliary-metadata-reservation", document),
            )


def test_cp65_auxiliary_v3_existing_final_arm_increases_hold_by_exact_slack() -> None:
    document = _auxiliary_reservation_document()
    row = next(
        item
        for item in document["artifact_entries"]
        if item["reservation_state"] == "preallocated-partial-in-place"
    )
    original_reserved = row["reserved_bytes"]
    row["reservation_state"] = "existing-final-in-place"
    row["partial_relative_path"] = ""
    row["reserved_bytes"] = 4_096
    document["allocated_future_partial_bytes"] -= original_reserved
    document["allocated_existing_final_bytes"] += 4_096
    document["unique_nonhold_artifact_allocated_bytes"] = (
        document["allocated_existing_final_bytes"]
        + document["allocated_future_partial_bytes"]
    )
    document["hold_allocated_bytes"] += original_reserved - 4_096
    document["exclusive_root_charge_current_bytes"] = (
        document["exclusive_root_charge_baseline_bytes"]
        + document["unique_nonhold_artifact_allocated_bytes"]
        + document["hold_allocated_bytes"]
        + document["disjoint_allocation_and_directory_charge_bytes"]
    )
    _refinish_exclusive_root_charge_measurement(document)
    zeroed = dict(row)
    zeroed["entry_sha256"] = _ZERO_SHA256
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0"
        + _canonical_json(zeroed)
    ).hexdigest()
    payload = _receipt_payload("auxiliary-metadata-reservation", document)
    result = cp65.cp65_validate_supplied_artifact_bytes(
        "auxiliary-metadata-reservation",
        "auxiliary_metadata_reservation.json",
        payload,
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong-artifact",
        "wrong-cap",
        "duplicate-inode",
        "duplicate-extent",
        "wrong-partial-path",
        "false-row-observation",
        "wrong-live-journal-arm",
        "fabricated-static-total",
        "fabricated-dynamic-total",
        "insufficient-hold",
        "insufficient-quota",
        "false-receipt-observation",
    ),
)
def test_cp65_auxiliary_v3_rejects_fabricated_rows_and_totals(mutation: str) -> None:
    document = _auxiliary_reservation_document()
    rows = document["artifact_entries"]
    if mutation == "wrong-artifact":
        rows[0]["artifact_id"] = "shard-index"
    elif mutation == "wrong-cap":
        rows[0]["reserved_bytes"] += 1
    elif mutation == "duplicate-inode":
        rows[1]["inode"] = rows[0]["inode"]
    elif mutation == "duplicate-extent":
        rows[1]["extent_map_sha256"] = rows[0]["extent_map_sha256"]
    elif mutation == "wrong-partial-path":
        rows[0]["partial_relative_path"] = rows[1]["partial_relative_path"]
    elif mutation == "false-row-observation":
        next(
            row
            for row in rows
            if row["reservation_state"] == "preallocated-partial-in-place"
        )["non_sparse_verified"] = False
    elif mutation == "wrong-live-journal-arm":
        next(
            row
            for row in rows
            if row["artifact_id"] == "auxiliary-reservation-transition-journal"
        )["reservation_state"] = "preallocated-partial-in-place"
    elif mutation == "fabricated-static-total":
        document["artifact_slot_reserved_bytes"] += 1
    elif mutation == "fabricated-dynamic-total":
        document["physical_reservation_sum_bytes"] += 1
    elif mutation == "insufficient-hold":
        document["hold_allocated_bytes"] -= 1
        document["physical_reservation_sum_bytes"] -= 1
    elif mutation == "insufficient-quota":
        document["enforced_quota_bytes"] -= 1
    elif mutation == "false-receipt-observation":
        document["same_root_verified"] = False
    else:  # pragma: no cover
        raise AssertionError(mutation)

    for row in rows:
        zeroed = dict(row)
        zeroed["entry_sha256"] = _ZERO_SHA256
        row["entry_sha256"] = hashlib.sha256(
            b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0"
            + _canonical_json(zeroed)
        ).hexdigest()
    payload = _receipt_payload("auxiliary-metadata-reservation", document)
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "auxiliary-metadata-reservation",
            "auxiliary_metadata_reservation.json",
            payload,
        )


def test_cp65_auxiliary_hold_release_is_bound_by_final_committed_marker_schema() -> None:
    assert cp65._COMMITTED_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_state_sha256",
        "sha256_manifest_sha256",
        "auxiliary_metadata_reservation_sha256",
        "auxiliary_reservation_transition_journal_sha256",
        "auxiliary_reservation_transition_journal_final_head_sha256",
        "auxiliary_reservation_transition_journal_final_entry_count",
        "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc",
        "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc",
        "hold_relative_path",
        "hold_device_identity_sha256",
        "hold_inode",
        "hold_extent_map_sha256",
        "hold_removed_at_utc",
        "hold_removal_directory_fsync_completed_at_utc",
        "hold_absence_verified",
        "committed_at_utc",
        "body_sha256",
    )
    declaration = next(
        row for row in cp65._ARTIFACT_DECLARATIONS if row[0] == "committed-marker"
    )
    assert declaration[6] == "cp65-test28-committed-marker-v3"
    predicates = {
        row.predicate_id: row
        for row in cp65.cp65_production_schema_preimage_validator_bundle().predicate_contracts
    }
    record = predicates["record:committed-marker"]
    operands = " ".join(
        predicates[child].operand_json_ascii for child in record.child_predicate_ids
    )
    assert "hold_absence_verified" in operands
    assert "hold_removed_at_utc" in operands
    assert "hold_removal_directory_fsync_completed_at_utc" in operands
    assert "committed_at_utc" in operands


def test_cp65_transition_journal_prefix_checkpoints_are_acyclic_and_ordered() -> None:
    assert cp65._PRETERMINAL_INVENTORY_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_arm",
        "auxiliary_transition_journal_prefix_entry_count",
        "auxiliary_transition_journal_prefix_head_sha256",
        "entry_count",
        "entries",
        "ordered_entries_sha256",
        "created_at_utc",
        "body_sha256",
    )
    assert cp65._TERMINAL_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_arm",
        "previous_lifecycle_state",
        "terminal_state",
        "freeze_receipt_sha256",
        "preauthorization_outcome_sha256",
        "launch_authorization_sha256",
        "postauthorization_outcome_sha256",
        "started_receipt_sha256",
        "durable_artifact_inventory_sha256",
        "auxiliary_transition_journal_after_inventory_entry_count",
        "auxiliary_transition_journal_after_inventory_head_sha256",
        "reason_code",
        "terminalized_at_utc",
        "body_sha256",
    )
    assert cp65._SHA_MANIFEST_KEYS == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_state_sha256",
        "auxiliary_transition_journal_after_terminal_entry_count",
        "auxiliary_transition_journal_after_terminal_head_sha256",
        "entry_count",
        "entries",
        "ordered_entries_sha256",
        "created_at_utc",
        "body_sha256",
    )


def test_cp65_terminal_publication_intrinsic_digests_and_set_counts_are_derived() -> None:
    earlier, inventory, terminal, manifest = _terminal_publication_fixture()
    inventory_result = cp65.cp65_validate_supplied_artifact_bytes(
        "preterminal-durable-artifact-inventory",
        "preterminal_durable_artifact_inventory.json",
        inventory,
    )
    assert inventory_result.syntax_valid
    assert inventory_result.intrinsic_digest_preimages_valid
    assert inventory_result.validated_digest_preimage_count == 4
    assert inventory_result.unresolved_digest_preimage_count == 3

    terminal_result = cp65.cp65_validate_supplied_artifact_bytes(
        "terminal-state", "terminal_state.json", terminal
    )
    assert terminal_result.syntax_valid
    assert terminal_result.intrinsic_digest_preimages_valid
    assert terminal_result.validated_digest_preimage_count == 1
    assert terminal_result.unresolved_digest_preimage_count == 4

    manifest_result = cp65.cp65_validate_supplied_artifact_bytes(
        "sha256-manifest", "sha256_manifest.json", manifest
    )
    assert manifest_result.syntax_valid
    assert manifest_result.intrinsic_digest_preimages_valid
    assert manifest_result.validated_digest_preimage_count == 2
    assert manifest_result.unresolved_digest_preimage_count == 6

    result = cp65.cp65_validate_supplied_artifact_set(
        earlier
        + (
            (
                "preterminal-durable-artifact-inventory",
                "preterminal_durable_artifact_inventory.json",
                inventory,
            ),
            ("terminal-state", "terminal_state.json", terminal),
            ("sha256-manifest", "sha256_manifest.json", manifest),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert result.validated_cross_binding_count == 8
    assert result.unresolved_cross_binding_count == 5
    assert not result.all_required_cross_binding_targets_supplied
    assert not result.cross_bindings_valid
    assert not result.production_evidence_accepted


@pytest.mark.parametrize(
    "terminal_arm,conditional_sources,expected_count",
    (
        ("PREAUTHORIZATION", (), 3),
        (
            "POSTAUTHORIZATION_PRESTART",
            ("launch-authorization", "postauthorization-outcome"),
            5,
        ),
        (
            "STARTED",
            (
                "launch-authorization",
                "postauthorization-outcome",
                "started-receipt",
            ),
            6,
        ),
    ),
)
def test_cp65_terminal_arm_crosslinks_are_nonvacuous_and_raw_bound(
    terminal_arm: str,
    conditional_sources: tuple[str, ...],
    expected_count: int,
) -> None:
    always_sources = (
        "freeze-receipt",
        "preauthorization-outcome",
        "preterminal-durable-artifact-inventory",
    )
    payloads = {
        artifact_id: ("cp65-terminal-source:" + artifact_id).encode("ascii")
        for artifact_id in always_sources + conditional_sources
    }
    pointer_by_source = {
        "freeze-receipt": "freeze_receipt_sha256",
        "preauthorization-outcome": "preauthorization_outcome_sha256",
        "preterminal-durable-artifact-inventory": ("durable_artifact_inventory_sha256"),
        "launch-authorization": "launch_authorization_sha256",
        "postauthorization-outcome": "postauthorization_outcome_sha256",
        "started-receipt": "started_receipt_sha256",
    }
    terminal = {
        "terminal_arm": terminal_arm,
        "freeze_receipt_sha256": hashlib.sha256(payloads["freeze-receipt"]).hexdigest(),
        "preauthorization_outcome_sha256": hashlib.sha256(
            payloads["preauthorization-outcome"]
        ).hexdigest(),
        "durable_artifact_inventory_sha256": hashlib.sha256(
            payloads["preterminal-durable-artifact-inventory"]
        ).hexdigest(),
        "launch_authorization_sha256": _ZERO_SHA256,
        "postauthorization_outcome_sha256": _ZERO_SHA256,
        "started_receipt_sha256": _ZERO_SHA256,
    }
    for source_id in conditional_sources:
        terminal[pointer_by_source[source_id]] = hashlib.sha256(
            payloads[source_id]
        ).hexdigest()
    target_only = {
        "terminal-state": (("terminal_state.json", b"terminal", "1" * 64, terminal),)
    }
    assert cp65._validate_supplied_cross_bindings(target_only) == (
        0,
        expected_count,
    )

    supplied = dict(target_only)
    for source_id, payload in payloads.items():
        supplied[source_id] = (
            (
                source_id + ".json",
                payload,
                hashlib.sha256(payload).hexdigest(),
                payload,
            ),
        )
    assert cp65._validate_supplied_cross_bindings(supplied) == (
        expected_count,
        0,
    )
    for source_id in always_sources + conditional_sources:
        pointer = pointer_by_source[source_id]
        original = terminal[pointer]
        terminal[pointer] = "f" * 64
        with pytest.raises(ValueError, match="cross-artifact digest binding"):
            cp65._validate_supplied_cross_bindings(supplied)
        terminal[pointer] = original


def test_cp65_inventory_and_manifest_entry_cardinality_never_exceeds_final_roster(
    authoritative_bundle: cp65.CP65ProductionSchemaPreimageValidatorBundleV1,
) -> None:
    rules = {
        (row.artifact_id, row.json_pointer): row
        for row in authoritative_bundle.field_rules
    }
    for artifact_id in (
        "preterminal-durable-artifact-inventory",
        "sha256-manifest",
    ):
        assert rules[(artifact_id, "/entry_count")].integer_interval[1] == 312
        assert rules[(artifact_id, "/entries")].length_interval[1] == 312

    inventory_entries = [
        _inventory_entry(
            ordinal,
            "cardinality/inventory-%03d.json" % ordinal,
            ("inventory:%d" % ordinal).encode("ascii"),
        )
        for ordinal in range(1, 314)
    ]
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "preterminal-durable-artifact-inventory",
            "preterminal_durable_artifact_inventory.json",
            _preterminal_inventory_payload(inventory_entries),
        )

    manifest_entries = [
        {
            "path": "cardinality/manifest-%03d.json" % ordinal,
            "bytes": ordinal,
            "sha256": hashlib.sha256(
                ("manifest:%d" % ordinal).encode("ascii")
            ).hexdigest(),
        }
        for ordinal in range(1, 314)
    ]
    manifest_payload = _receipt_payload(
        "sha256-manifest",
        {
            "schema": "cp65-test28-sha256-manifest-v1",
            "purpose": "terminal-corpus-sha256-manifest",
            "attempt_id": "attempt-development-only",
            "terminal_state_sha256": "1" * 64,
            "auxiliary_transition_journal_after_terminal_entry_count": 1,
            "auxiliary_transition_journal_after_terminal_head_sha256": "2" * 64,
            "entry_count": len(manifest_entries),
            "entries": manifest_entries,
            "ordered_entries_sha256": hashlib.sha256(
                b"cp65-test28-sha256-manifest-ordered-entries-v1\0"
                + _canonical_json(manifest_entries)
            ).hexdigest(),
            "created_at_utc": "2026-01-01T00:00:00.000001Z",
            "body_sha256": _ZERO_SHA256,
        },
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "sha256-manifest", "sha256_manifest.json", manifest_payload
        )


@pytest.mark.parametrize(
    "mutation",
    ("empty-count", "count", "order", "duplicate", "path", "row", "ordered"),
)
def test_cp65_preterminal_inventory_rejects_internal_forgery(mutation: str) -> None:
    _earlier, inventory, _terminal, _manifest = _terminal_publication_fixture()
    document = json.loads(inventory)
    if mutation == "empty-count":
        document["entries"] = []
        document["entry_count"] = 999
        document["ordered_entries_sha256"] = "f" * 64
    elif mutation == "count":
        document["entry_count"] = 999
    elif mutation == "order":
        document["entries"] = list(reversed(document["entries"]))
    elif mutation == "duplicate":
        document["entries"][1]["path"] = document["entries"][0]["path"]
        inventory = _refinish_inventory_document(document)
        document = None
    elif mutation == "path":
        document["entries"][0]["path"] = "../escape"
        inventory = _refinish_inventory_document(document)
        document = None
    elif mutation == "row":
        document["entries"][0]["entry_sha256"] = "f" * 64
    elif mutation == "ordered":
        document["ordered_entries_sha256"] = "f" * 64
    else:  # pragma: no cover
        raise AssertionError(mutation)
    if document is not None:
        inventory = _receipt_payload("preterminal-durable-artifact-inventory", document)
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "preterminal-durable-artifact-inventory",
            "preterminal_durable_artifact_inventory.json",
            inventory,
        )


@pytest.mark.parametrize("mutation", ("count", "order", "duplicate", "path", "ordered"))
def test_cp65_sha256_manifest_rejects_internal_forgery(mutation: str) -> None:
    _earlier, _inventory, _terminal, manifest = _terminal_publication_fixture()
    document = json.loads(manifest)
    if mutation == "count":
        document["entry_count"] = 999
    elif mutation == "order":
        document["entries"] = list(reversed(document["entries"]))
    elif mutation == "duplicate":
        document["entries"][1]["path"] = document["entries"][0]["path"]
    elif mutation == "path":
        document["entries"][0]["path"] = "../escape"
    elif mutation == "ordered":
        document["ordered_entries_sha256"] = "f" * 64
    else:  # pragma: no cover
        raise AssertionError(mutation)
    forged = _receipt_payload("sha256-manifest", document)
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_bytes(
            "sha256-manifest", "sha256_manifest.json", forged
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "inventory-member-sha",
        "inventory-forbidden-terminal",
        "manifest-omit-inventory",
        "manifest-omit-terminal",
        "manifest-terminal-sha",
        "manifest-extra-committed",
    ),
)
def test_cp65_terminal_publication_set_rejects_membership_and_closure_forgery(
    mutation: str,
) -> None:
    earlier, inventory, terminal, manifest = _terminal_publication_fixture()
    if mutation in ("inventory-member-sha", "inventory-forbidden-terminal"):
        inventory_document = json.loads(inventory)
        if mutation == "inventory-member-sha":
            inventory_document["entries"][0]["sha256"] = "f" * 64
        else:
            inventory_document["entries"].append(
                {
                    "ordinal": 3,
                    "path": "terminal_state.json",
                    "bytes": 1,
                    "sha256": hashlib.sha256(b"x").hexdigest(),
                    "entry_sha256": _ZERO_SHA256,
                }
            )
        inventory = _refinish_inventory_document(inventory_document)
        terminal = _terminal_state_payload(inventory)
        manifest = _sha256_manifest_payload(
            inventory_document["entries"], inventory, terminal
        )
    else:
        manifest_document = json.loads(manifest)
        if mutation == "manifest-omit-inventory":
            manifest_document["entries"] = [
                row
                for row in manifest_document["entries"]
                if row["path"] != "preterminal_durable_artifact_inventory.json"
            ]
        elif mutation == "manifest-omit-terminal":
            manifest_document["entries"] = [
                row
                for row in manifest_document["entries"]
                if row["path"] != "terminal_state.json"
            ]
        elif mutation == "manifest-terminal-sha":
            next(
                row
                for row in manifest_document["entries"]
                if row["path"] == "terminal_state.json"
            )["sha256"] = ("f" * 64)
        elif mutation == "manifest-extra-committed":
            manifest_document["entries"].append(
                {
                    "path": "COMMITTED.json",
                    "bytes": 1,
                    "sha256": hashlib.sha256(b"x").hexdigest(),
                }
            )
            manifest_document["entries"].sort(key=lambda row: row["path"])
        else:  # pragma: no cover
            raise AssertionError(mutation)
        manifest = _refinish_sha256_manifest_document(manifest_document)
    supplied = earlier + (
        (
            "preterminal-durable-artifact-inventory",
            "preterminal_durable_artifact_inventory.json",
            inventory,
        ),
        ("terminal-state", "terminal_state.json", terminal),
        ("sha256-manifest", "sha256_manifest.json", manifest),
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(supplied)


@pytest.mark.parametrize("mutation", ("arm-disagreement", "omitted-eligible-artifact"))
def test_cp65_terminal_inventory_matches_branch_and_all_supplied_preinventory_paths(
    mutation: str,
) -> None:
    earlier, inventory, terminal, manifest = _terminal_publication_fixture()
    inventory_document = json.loads(inventory)
    if mutation == "arm-disagreement":
        inventory_document["terminal_arm"] = "STARTED"
    elif mutation == "omitted-eligible-artifact":
        inventory_document["entries"] = inventory_document["entries"][:1]
    else:  # pragma: no cover
        raise AssertionError(mutation)
    inventory = _refinish_inventory_document(inventory_document)
    terminal = _terminal_state_payload(inventory)
    manifest = _sha256_manifest_payload(
        inventory_document["entries"], inventory, terminal
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            earlier
            + (
                (
                    "preterminal-durable-artifact-inventory",
                    "preterminal_durable_artifact_inventory.json",
                    inventory,
                ),
                ("terminal-state", "terminal_state.json", terminal),
                ("sha256-manifest", "sha256_manifest.json", manifest),
            )
        )


def test_cp65_committed_marker_is_complete_canonical_publication_not_path_presence() -> None:
    document = {
        "schema": "cp65-test28-committed-marker-v3",
        "purpose": "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
        "attempt_id": "attempt-development-only",
        "terminal_state_sha256": "1" * 64,
        "sha256_manifest_sha256": "2" * 64,
        "auxiliary_metadata_reservation_sha256": "3" * 64,
        "auxiliary_reservation_transition_journal_sha256": "4" * 64,
        "auxiliary_reservation_transition_journal_final_head_sha256": "5" * 64,
        "auxiliary_reservation_transition_journal_final_entry_count": 4,
        "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc": (
            "2026-01-01T00:00:00.000001Z"
        ),
        "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc": (
            "2026-01-01T00:00:00.000002Z"
        ),
        "hold_relative_path": ".cp65_auxiliary_reservation_hold.partial",
        "hold_device_identity_sha256": "6" * 64,
        "hold_inode": 10_000,
        "hold_extent_map_sha256": "7" * 64,
        "hold_removed_at_utc": "2026-01-01T00:00:00.000003Z",
        "hold_removal_directory_fsync_completed_at_utc": (
            "2026-01-01T00:00:00.000004Z"
        ),
        "hold_absence_verified": True,
        "committed_at_utc": "2026-01-01T00:00:00.000005Z",
        "body_sha256": _ZERO_SHA256,
    }
    payload = _receipt_payload("committed-marker", document)
    result = cp65.cp65_validate_supplied_artifact_bytes(
        "committed-marker", "COMMITTED.json", payload
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid
    for malformed in (payload[:-1], payload + b"\n", b"{}"):
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                "committed-marker", "COMMITTED.json", malformed
            )
    for key, value in (
        ("hold_absence_verified", False),
        ("hold_relative_path", "different.partial"),
        ("committed_at_utc", "2026-01-01T00:00:00.000002Z"),
    ):
        forged = dict(document)
        forged[key] = value
        forged_payload = _receipt_payload("committed-marker", forged)
        with pytest.raises(ValueError):
            cp65.cp65_validate_supplied_artifact_bytes(
                "committed-marker", "COMMITTED.json", forged_payload
            )


def test_cp65_journal_recovers_exact_cp64_chain_and_zero_suffix() -> None:
    start_payload = _acquisition_start_payload()
    start_body = json.loads(start_payload)["body_sha256"]
    values = (0, 1, 2**64 - 1)
    journal, head = _journal_with_values(start_body, values)
    partial_payload = _partial_acquisition_payload(start_body, journal, head, values)
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "external-seed-acquisition-start-receipt",
                "seed_acquisition_start_receipt.json",
                start_payload,
            ),
            (
                "external-seed-acquisition-journal",
                "seed_acquisition_journal.bin",
                journal,
            ),
            (
                "partial-seed-acquisition-terminal-receipt",
                "seed_partial_acquisition_terminal_receipt.json",
                partial_payload,
            ),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid
    assert not result.production_evidence_accepted
    assert not result.execution_permitted


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong-ordinal",
        "wrong-previous-head",
        "wrong-entry-digest",
        "claimed-value-differs",
        "claimed-head-differs",
        "claimed-count-differs",
        "claimed-raw-digest-differs",
    ),
)
def test_cp65_journal_rejects_forged_claimed_prefix(mutation: str) -> None:
    start_payload = _acquisition_start_payload()
    start_body = json.loads(start_payload)["body_sha256"]
    values = (7, 11)
    journal, head = _journal_with_values(start_body, values)
    claimed_values = values
    claimed_head = head
    claimed_journal = journal
    if mutation == "wrong-ordinal":
        changed = bytearray(journal)
        changed[7] = 2
        claimed_journal = bytes(changed)
    elif mutation == "wrong-previous-head":
        changed = bytearray(journal)
        changed[16] ^= 1
        claimed_journal = bytes(changed)
    elif mutation == "wrong-entry-digest":
        changed = bytearray(journal)
        changed[48] ^= 1
        claimed_journal = bytes(changed)
    elif mutation == "claimed-value-differs":
        claimed_values = (8, 11)
    elif mutation == "claimed-head-differs":
        claimed_head = "f" * 64
    elif mutation == "claimed-count-differs":
        claimed_values = (7,)
    elif mutation == "claimed-raw-digest-differs":
        pass
    else:  # pragma: no cover
        raise AssertionError(mutation)
    partial_payload = _partial_acquisition_payload(
        start_body, claimed_journal, claimed_head, claimed_values
    )
    if mutation == "claimed-raw-digest-differs":
        document = json.loads(partial_payload)
        document["acquisition_journal_sha256"] = "f" * 64
        partial_payload = _receipt_payload(
            "partial-seed-acquisition-terminal-receipt", document
        )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "external-seed-acquisition-start-receipt",
                    "seed_acquisition_start_receipt.json",
                    start_payload,
                ),
                (
                    "external-seed-acquisition-journal",
                    "seed_acquisition_journal.bin",
                    claimed_journal,
                ),
                (
                    "partial-seed-acquisition-terminal-receipt",
                    "seed_partial_acquisition_terminal_receipt.json",
                    partial_payload,
                ),
            )
        )


def test_cp65_journal_torn_suffix_is_retained_but_never_value_evidence() -> None:
    start_payload = _acquisition_start_payload()
    start_body = json.loads(start_payload)["body_sha256"]
    journal, head = _journal_with_values(start_body, (19,))
    torn = bytearray(journal)
    torn[80] = 1
    torn_journal = bytes(torn)
    partial_payload = _partial_acquisition_payload(
        start_body, torn_journal, head, (19,)
    )
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "external-seed-acquisition-start-receipt",
                "seed_acquisition_start_receipt.json",
                start_payload,
            ),
            (
                "external-seed-acquisition-journal",
                "seed_acquisition_journal.bin",
                torn_journal,
            ),
            (
                "partial-seed-acquisition-terminal-receipt",
                "seed_partial_acquisition_terminal_receipt.json",
                partial_payload,
            ),
        )
    )
    assert result.syntax_valid

    forged_two = _partial_acquisition_payload(
        start_body, torn_journal, "e" * 64, (19, 23)
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "external-seed-acquisition-start-receipt",
                    "seed_acquisition_start_receipt.json",
                    start_payload,
                ),
                (
                    "external-seed-acquisition-journal",
                    "seed_acquisition_journal.bin",
                    torn_journal,
                ),
                (
                    "partial-seed-acquisition-terminal-receipt",
                    "seed_partial_acquisition_terminal_receipt.json",
                    forged_two,
                ),
            )
        )


def test_cp65_partial_syntax_validation_never_reports_vacuous_cross_closure() -> None:
    start_payload = _acquisition_start_payload()
    result = cp65.cp65_validate_supplied_artifact_bytes(
        "external-seed-acquisition-start-receipt",
        "seed_acquisition_start_receipt.json",
        start_payload,
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.all_required_digest_preimage_sources_supplied
    assert result.unresolved_digest_preimage_count > 0
    assert not result.digest_preimages_valid
    assert not result.all_required_cross_binding_targets_supplied
    assert result.validated_cross_binding_count >= 0
    assert result.unresolved_cross_binding_count > 0
    assert not result.cross_bindings_valid
    assert not result.external_provenance_verified
    assert not result.gate_transition_permitted
    assert not result.launch_authorized
    assert not result.execution_permitted


def test_cp65_completed_source_receipt_requires_all_2048_exact_journal_entries() -> None:
    start_payload = _acquisition_start_payload()
    start_body = json.loads(start_payload)["body_sha256"]
    values = tuple(range(2_048))
    journal, head = _journal_with_values(start_body, values)
    completed_payload = _completed_source_receipt_payload(
        start_body, journal, head, values
    )
    result = cp65.cp65_validate_supplied_artifact_set(
        (
            (
                "external-seed-acquisition-start-receipt",
                "seed_acquisition_start_receipt.json",
                start_payload,
            ),
            (
                "external-seed-acquisition-journal",
                "seed_acquisition_journal.bin",
                journal,
            ),
            (
                "external-seed-source-receipt",
                "seed_source_receipt.json",
                completed_payload,
            ),
        )
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.digest_preimages_valid

    truncated_chain, truncated_head = _journal_with_values(start_body, values[:-1])
    forged_completed = _completed_source_receipt_payload(
        start_body, truncated_chain, truncated_head, values
    )
    with pytest.raises(ValueError):
        cp65.cp65_validate_supplied_artifact_set(
            (
                (
                    "external-seed-acquisition-start-receipt",
                    "seed_acquisition_start_receipt.json",
                    start_payload,
                ),
                (
                    "external-seed-acquisition-journal",
                    "seed_acquisition_journal.bin",
                    truncated_chain,
                ),
                (
                    "external-seed-source-receipt",
                    "seed_source_receipt.json",
                    forged_completed,
                ),
            )
        )
