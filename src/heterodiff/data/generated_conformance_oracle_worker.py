"""Standalone fixture-replay worker for the five generated cases.

This file is an executable source artifact, not an importable package API.  It
uses only a small Python-standard-library surface and deliberately imports no
Heterodiff module.  The worker separately implements the frozen V1 binary
frame, reconstructs identity-bearing native configurations from hand-frozen
semantic literals, and constructs the compact expected-evidence commitment
from hand-frozen leaf commitments.

Standard input must contain exactly one bounded V1 request frame.  Success
writes exactly one V1 response frame to standard output.  Rejection messages
never reflect request values; when standard error is writable, rejection
attempts emit one fixed line and exit nonzero.
"""

import base64
import binascii
import hashlib
import json
import sys


_REQUEST_DOMAIN = b"heterodiff.adapter.oracle-worker-request.v1"
_RESPONSE_DOMAIN = b"heterodiff.adapter.oracle-worker-response.v1"
_REQUEST_NAMES = (
    b"execution_input_set_sha256",
    b"case_ordinal",
    b"oracle_id",
    b"oracle_source_byte_count",
    b"oracle_source_sha256",
    b"source_bytes",
    b"descriptor_payload_bytes",
    b"partition_payload_bytes",
    b"split_manifest_payload_bytes",
)
_RESPONSE_NAMES = (
    b"request_frame_sha256",
    b"case_ordinal",
    b"oracle_id",
    b"oracle_source_byte_count",
    b"oracle_source_sha256",
    b"expected_configuration_payload_bytes",
    b"expected_evidence_payload_bytes",
    b"expected_native_observation_sha256",
)
_ORACLE_ID = b"generated-conformance-fixture-replay-worker-v1"
_MAX_FRAME = 32 * 1024 * 1024
_MAX_STRUCTURED = 16 * 1024 * 1024
_MAX_CASE_SOURCE = 64 * 1024
_MAX_ORACLE_SOURCE = 1024 * 1024
_MAX_JSON_DEPTH = 32
_MAX_JSON_NODES = 200000
_MAX_JSON_STRING_BYTES = 512 * 1024
_MAX_SAFE_INTEGER = (1 << 53) - 1
_HEX = b"0123456789abcdef"
_REJECTION = b"ORACLE_WORKER_REJECTED\n"

_SPLIT = (
    b'{"entries":[{"group_id":"900001","sample_id":"900001","split":"train"},'
    b'{"group_id":"customer-shared","sample_id":"invoice-a","split":"train"},'
    b'{"group_id":"customer-shared","sample_id":"invoice-b","split":"train"},'
    b'{"group_id":"generated-process-group-1","sample_id":"H-CONT-1",'
    b'"split":"train"},{"group_id":"synthetic-maestro-group-1",'
    b'"sample_id":"M-ACG-1","split":"train"}],"unicode_profile":"ucd-3.2.0"}'
)

_H_DESCRIPTOR = (
    b'{"capabilities":{"evaluation_labels":true,"fitted_state":false,'
    b'"multiplicity_mode":"simple","private_provenance":true,'
    b'"raw_byte_reconstruction":false,"semantic_reconstruction":true,'
    b'"static_context":false,"supported_representation_ids":[],'
    b'"time_measure":"continuous"},"identity":{"adapter_id":'
    b'"generated.native.family-a","adapter_version":"1","contract_version":'
    b'"heterodiff-native-event-adapter-v1","policy_sha256":'
    b'"e51c63f9e79c0db1ba01ccbfb8b1036537edf3577cb5cfe84315c164c637abe3"},'
    b'"unicode_profile":"ucd-3.2.0"}'
)
_M_DESCRIPTOR = (
    b'{"capabilities":{"evaluation_labels":false,"fitted_state":false,'
    b'"multiplicity_mode":"finite_counting","private_provenance":true,'
    b'"raw_byte_reconstruction":true,"semantic_reconstruction":true,'
    b'"static_context":true,"supported_representation_ids":'
    b'["heterodiff.atomic-counting-grid.v1"],"time_measure":"atomic_grid"},'
    b'"identity":{"adapter_id":"generated.native.family-b","adapter_version":"1",'
    b'"contract_version":"heterodiff-native-event-adapter-v1","policy_sha256":'
    b'"2b49f41b0e62e4d387a2c668db1340b2e1233f92beba8bdc9bbe937de78f15e7"},'
    b'"unicode_profile":"ucd-3.2.0"}'
)
_P_DESCRIPTOR = (
    b'{"capabilities":{"evaluation_labels":false,"fitted_state":false,'
    b'"multiplicity_mode":"finite_counting","private_provenance":true,'
    b'"raw_byte_reconstruction":false,"semantic_reconstruction":true,'
    b'"static_context":true,"supported_representation_ids":'
    b'["heterodiff.atomic-counting-grid.v1"],"time_measure":"atomic_grid"},'
    b'"identity":{"adapter_id":"generated.native.family-c","adapter_version":"1",'
    b'"contract_version":"heterodiff-native-event-adapter-v1","policy_sha256":'
    b'"82dc11a52bc22a80a596af3424c09457e4a92ee53a7c2288ab6db1a0c39e1187"},'
    b'"unicode_profile":"ucd-3.2.0"}'
)
_R_DESCRIPTOR = (
    b'{"capabilities":{"evaluation_labels":false,"fitted_state":false,'
    b'"multiplicity_mode":"finite_counting","private_provenance":true,'
    b'"raw_byte_reconstruction":false,"semantic_reconstruction":true,'
    b'"static_context":false,"supported_representation_ids":'
    b'["heterodiff.atomic-counting-grid.v1"],"time_measure":"atomic_grid"},'
    b'"identity":{"adapter_id":"generated.native.family-d","adapter_version":"1",'
    b'"contract_version":"heterodiff-native-event-adapter-v1","policy_sha256":'
    b'"ca1c5a66165d704c671a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49"},'
    b'"unicode_profile":"ucd-3.2.0"}'
)


def _strict_b64(value):
    try:
        encoded = value.encode("ascii", "strict")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeError, binascii.Error):
        raise ValueError()
    if base64.b64encode(decoded) != encoded:
        raise ValueError()
    return decoded


def _case(
    family,
    ordinal,
    source_b64,
    descriptor,
    partition,
    policy,
    inventory,
    coverage,
    labels,
    labels_format,
    provenance,
    reconstruction,
    static,
    static_format,
    native,
    configuration,
    evidence,
):
    source = _strict_b64(source_b64)
    return {
        "family": family,
        "ordinal": ordinal,
        "source": source,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "descriptor": descriptor,
        "partition": partition,
        "policy": policy,
        "inventory": inventory,
        "coverage": coverage,
        "labels": labels,
        "labels_format": labels_format,
        "provenance": provenance,
        "reconstruction": reconstruction,
        "static": static,
        "static_format": static_format,
        "native": native,
        "configuration": configuration,
        "evidence": evidence,
    }


_NO_FIT = "37c01173be50a6d2908242368d20b4c5edb2e02deff27f835c5caf46a0dc8129"
_EMPTY_LABELS = "853da5250ed5f090ae94d5654735b8c9f7c59bc5157e472a26517d73132dbf1c"
_EMPTY_STATIC = "172bf762a97f19b9e26221cafda60ffc6e771ee432961a987447369283f607e0"

_CASES = (
    _case(
        "R-ACG-1-B",
        0,
        "SW52b2ljZSxDdXN0b21lcixUaW1lSW5kZXgsUHJvZHVjdCxDYW5jZWxsYXRpb24s"
        "UXVhbnRpdHksVW5pdFByaWNlCmludm9pY2UtYixjdXN0b21lci1zaGFyZWQsNyxz"
        "a3UtYSxjYW5jZWxsZWQsLTIsMy41MAppbnZvaWNlLWIsY3VzdG9tZXItc2hhcmVk"
        "LDcsc2t1LWIsYWN0aXZlLC0xLDQuMjUK",
        _R_DESCRIPTOR,
        b'{"group_id":"customer-shared","sample_id":"invoice-b","split":"train",'
        b'"unicode_profile":"ucd-3.2.0"}',
        "ca1c5a66165d704c671a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49",
        "471db6ead44404981a920ffadd5e9ab3875db1cf01b7e0c233c3259c76573fa6",
        "2481969ffd6b279d2e2a7cb409207fc4409886742ac1a1890b7f04185d4cf5b8",
        _EMPTY_LABELS,
        "generated.empty-labels.v1",
        "2f2c5714825bcbaa57f2dd9ff1aff39cd350d9b035f8bf848b5e809c847dcc97",
        "0c6e50288f975b2d7ff14b16993e5bae6b0ac0e45598cdccc3fec1a245391763",
        _EMPTY_STATIC,
        "generated.empty-static.v1",
        "485a625b6ecd326012ef5b2cf362f097ddf188e6b784989704695be2f3d201e2",
        "f3906f7a4b1a73c63ca3dcbca27373519472ba135903c96ac7a154231f9cb7fd",
        "d22b2d94e7a161457d63ab7ce0d36a86a7e6abacaf087c5e2e0ca4f9fee04fa5",
    ),
    _case(
        "H-CONT-1",
        1,
        "eyJldmVudHMiOlt7ImV2ZW50X3R5cGUiOjIsIm1hcmtzIjpbIjB4MS40YjFhYjZl"
        "Zjg2NGE4cC00IiwiMHgxLmI3YmFiZmI3NDFhMTBwLTIiXSwidGltZSI6IjB4MS5j"
        "ZjE4NTVkNzBlYmJjcCswIiwidHlwZV9uYW1lIjoiY29udGV4dCJ9LHsiZXZlbnRf"
        "dHlwZSI6MCwibWFya3MiOltdLCJ0aW1lIjoiMHgxLjE2NTM2MjNiM2JlNGJwKzEi"
        "LCJ0eXBlX25hbWUiOiJwdWxzZSJ9LHsiZXZlbnRfdHlwZSI6MiwibWFya3MiOlsi"
        "MHgxLmU4OWFlZWYwM2UwMDJwLTIiLCItMHgxLjFjYWZlZjYxYTM5NThwLTIiXSwi"
        "dGltZSI6IjB4MS4zZTQyNzg3ZmYyMDY4cCsxIiwidHlwZV9uYW1lIjoiY29udGV4"
        "dCJ9LHsiZXZlbnRfdHlwZSI6MiwibWFya3MiOlsiMHgxLjZiZWExNzI0YjcwZjBw"
        "LTMiLCIweDEuYmRkYjMxNjc2Y2M0OHAtMiJdLCJ0aW1lIjoiMHgxLmRjMTIyNTg0"
        "ZTFjOWNwKzEiLCJ0eXBlX25hbWUiOiJjb250ZXh0In0seyJldmVudF90eXBlIjox"
        "LCJtYXJrcyI6WyItMHgxLjc3NjcxYTYzYTM5OTRwLTEiXSwidGltZSI6IjB4MS4z"
        "Yzc3NzVlNTg5MzVlcCsyIiwidHlwZV9uYW1lIjoic2lnbmFsIn1dLCJmb3JtYXQi"
        "OiJoZXRlcm9kaWZmLmdlbmVyYXRlZC1oYXdrZXMtc291cmNlLnYxIiwibWV0YWRh"
        "dGEiOnsiY2FuZGlkYXRlX2NvdW50Ijo2LCJob3Jpem9uIjoiMHgxLjQwMDAwMDAw"
        "MDAwMDBwKzIiLCJtYXhfY2FuZGlkYXRlcyI6MTAwMCwibWF4X2V2ZW50cyI6NjQs"
        "InBhcmFtZXRlcl9pZCI6ImhldGVyb2RpZmYuZ2VuZXJhdGVkLWhhd2tlcy1wYXJh"
        "bWV0ZXJzLnYxIiwicmVhbGl6ZWRfZXZlbnRfY291bnRzIjpbMSwxLDNdLCJzZWVk"
        "Ijo0LCJ0ZXJtaW5hdGVkX2J5IjoiaG9yaXpvbiJ9fQ==",
        _H_DESCRIPTOR,
        b'{"group_id":"generated-process-group-1","sample_id":"H-CONT-1",'
        b'"split":"train","unicode_profile":"ucd-3.2.0"}',
        "e51c63f9e79c0db1ba01ccbfb8b1036537edf3577cb5cfe84315c164c637abe3",
        "90d907edf89fb4345bab5c954673a77d6628d2cb95990f522156b2dc60c01242",
        "27373ec24698df373c4d02f661c670142e21f1e1922a1a6cfe3ec9f012380e9b",
        "7369424f817661b040e240f49e0f1efd2c6b3cbbcb0afcb6d163ad2163290984",
        "generated.process-parameters.v1",
        "66cc53330acff2e1199d30ec8741b38ab5f14e9d0e88ecfacb5f01b2d376b6f4",
        "6c0db46998233a24150d8402975446c9b34a766048d758658f216bd1b68f0aa9",
        _EMPTY_STATIC,
        "generated.empty-static.v1",
        "3fda63942b4d78725fb24f5eb7973fba938fad4bc6dfff1a1e99b3e448dfb26d",
        "26fc5da984740a391b390cb26036ad2d771de43f7e72013a6e9c7710e6d4eacb",
        "dc9a7f24bafdf49e7093b040c118d741394b48e32f6c76ec45f0a0b7166bad47",
    ),
    _case(
        "R-ACG-1-A",
        2,
        "SW52b2ljZSxDdXN0b21lcixUaW1lSW5kZXgsUHJvZHVjdCxDYW5jZWxsYXRpb24s"
        "UXVhbnRpdHksVW5pdFByaWNlCmludm9pY2UtYSxjdXN0b21lci1zaGFyZWQsNSxz"
        "a3UtYSxhY3RpdmUsMiwzLjUwCmludm9pY2UtYSxjdXN0b21lci1zaGFyZWQsNSxz"
        "a3UtYSxhY3RpdmUsMiwzLjUwCmludm9pY2UtYSxjdXN0b21lci1zaGFyZWQsNSxz"
        "a3UtYixjYW5jZWxsZWQsMSw0LjI1Cg==",
        _R_DESCRIPTOR,
        b'{"group_id":"customer-shared","sample_id":"invoice-a","split":"train",'
        b'"unicode_profile":"ucd-3.2.0"}',
        "ca1c5a66165d704c671a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49",
        "6d3cdcd19a1f8c1c000d35e7f02553a3dff8398781423a88a0edab451e21147c",
        "5612cc7b071d8fe6ef4673f5ec24b46fee1272d1e61d9c3839f54e3203271d96",
        _EMPTY_LABELS,
        "generated.empty-labels.v1",
        "a17a824aa895896dd89e06e564cbd4bf3ee6d4b7c3d0b802630e9ede05f2f785",
        "b7826f0950b358db7d3432542e3d1cab4592f7a2fc4ca2ce5f02426432d5f683",
        _EMPTY_STATIC,
        "generated.empty-static.v1",
        "bf820f6e3a83a741107b9f8252cac0ebc2061af76497656e8ae1838f382b5aae",
        "1b2a5bb5f30fa9f9b4871d6383bb95649526a429ee41f5db3e947904dee3b1af",
        "429277b18161fd81773623140cd0eb8a3b927a4cefdbd01654936c55e5b8357a",
    ),
    _case(
        "P-ACG-1",
        3,
        "VGltZSxQYXJhbWV0ZXIsVmFsdWUKMDA6MDAsUmVjb3JkSUQsOTAwMDAxCjAwOjAw"
        "LEFnZSw1NAowMDowMCxHZW5kZXIsMAowMDowMCxIZWlnaHQsLTEKMDA6MDAsSUNV"
        "VHlwZSw0CjAwOjAwLFdlaWdodCwtMQowMDowNSxIUiw4MAowMDowNSxIUiw4MC4w"
        "CjAwOjA1LFRlbXAsMzcuMAowMDowNixVcmluZSwxMjAKMDA6MDcsV2VpZ2h0LDgx"
        "LjUKMDA6MDgsSFIsLTEK",
        _P_DESCRIPTOR,
        b'{"group_id":"900001","sample_id":"900001","split":"train",'
        b'"unicode_profile":"ucd-3.2.0"}',
        "82dc11a52bc22a80a596af3424c09457e4a92ee53a7c2288ab6db1a0c39e1187",
        "f8dd01915e5687ddebd059d6c7b91044b28b59553a2b7e2ccf833f435c12d765",
        "228c4475724bb46a9409f36ab9f296ccd04762346aa0737523d756b254925687",
        _EMPTY_LABELS,
        "generated.empty-labels.v1",
        "a96fa631d3ca3f1cd191e93d3aad230290e27e2bde8d5fca92c5862eedeaac5c",
        "72a913bfb737d46f06f710c3baeefab37d377fce8e9169c124390c750ffc5117",
        "dbfa51eac3c706096d90f5716af0f086d207d318c47f8e3771a23c2380aae2de",
        "generated.admission-context.v1",
        "ab6673020b0fe7fdd66f5eafa5b7b822864213d7c027ce095ba6a5121f1a85fb",
        "342171e92a04ed0e9c4b88b879a47e1c0e8e1dd8d8fe1eaab024ecc862cd3379",
        "6b7acda51f1b0f5a4e5208abbb96177757c834287c80b07f722aca708c9f35d9",
    ),
    _case(
        "M-ACG-1",
        4,
        "TVRoZAAAAAYAAAABAeBNVHJrAAAAKwD/UQMHoSAAkDxAAJA8QACQQGB4gDwAAIA8"
        "AACAQAA8kEN/PIBDAAD/LwA=",
        _M_DESCRIPTOR,
        b'{"group_id":"synthetic-maestro-group-1","sample_id":"M-ACG-1",'
        b'"split":"train","unicode_profile":"ucd-3.2.0"}',
        "2b49f41b0e62e4d387a2c668db1340b2e1233f92beba8bdc9bbe937de78f15e7",
        "e1026de6dd6bd6f5ecdb08213e0d100213102ff7af6d303b6b110d5216693839",
        "833812cafcf79d4109fdcfaf64b11235f0466ca669b1a2f722e0839ce6feebd3",
        _EMPTY_LABELS,
        "generated.empty-labels.v1",
        "fb681879d0c33470110874144de33bdab903c243d94b2d38a8f993f18628357a",
        "ebec083d41933de376dbedc825cbb6c9e379244746b2e5c017219915a485b7a2",
        "27deb48e11872820987da79f2fcca9488f1d13cc9e7fedbc9855603aec347165",
        "generated.tempo-map.v1",
        "ca3aea82612d7f15d193eb4c3d48aad152c92175b080c9f60e7355afda7dd397",
        "24ea3833eefe0bb025efaa1ca32211e6cb7c49ce5f7023da22ac4b9edee4cd0e",
        "df0858161c5b807b02e91f02a7f571a9d21e58a67b11654d1b461b2fb815479d",
    ),
)
_CASE_BY_SOURCE_SHA256 = dict(
    (item["source_sha256"], item) for item in _CASES
)


def _canonical(value):
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _domain_digest(domain, payload):
    encoded = _canonical(payload)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)
    return digest.hexdigest()


def _hx(value):
    numeric_value = float(value)
    if numeric_value == 0.0:
        numeric_value = 0.0
    return numeric_value.hex().lower()


def _field(name, support, unit=None, lower=None, upper=None):
    return {
        "dimension": 1,
        "lower": lower,
        "name": name,
        "support": support,
        "unit": unit,
        "upper": upper,
    }


def _event_type(type_id, name, fields=()):
    return {"fields": list(fields), "name": name, "type_id": type_id}


def _time_reference(kind, atoms=(), continuous_weight=0.0):
    atoms = tuple(atoms)
    return {
        "atom_weights": [_hx(1.0) for _item in atoms],
        "atoms": [_hx(item) for item in atoms],
        "continuous_weight": _hx(continuous_weight),
        "kind": kind,
    }


def _schema(
    event_types,
    horizon,
    time_measure,
    time_reference,
    allow_simultaneous,
    version,
    multiplicity_mode,
):
    return {
        "allow_simultaneous": allow_simultaneous,
        "event_types": list(event_types),
        "horizon": _hx(horizon),
        "multiplicity_mode": multiplicity_mode,
        "time_measure": time_measure,
        "time_reference": time_reference,
        "version": version,
    }


def _event(time_hex, event_type, marks, event_id, observed_marks):
    return {
        "time": time_hex,
        "type": event_type,
        "marks": dict((name, tuple(values)) for name, values in marks.items()),
        "id": event_id,
        "observed": tuple(observed_marks),
    }


def _event_id_key(value):
    if value is None:
        return (0,)
    if type(value) is str:
        return (1, value)
    return (
        2,
        tuple(
            (0, item) if type(item) is int else (1, item)
            for item in value
        ),
    )


def _event_id_tree(value):
    if value is None:
        return {"kind": "none"}
    if type(value) is str:
        return {"kind": "text", "value": value}
    return {
        "components": [
            (
                {"kind": "integer", "value": item}
                if type(item) is int
                else {"kind": "text", "value": item}
            )
            for item in value
        ],
        "kind": "tuple",
    }


def _event_key(value):
    model_key = (
        float.fromhex(value["time"]),
        value["type"],
        tuple(
            (name, tuple(float.fromhex(item) for item in value["marks"][name]))
            for name in sorted(value["marks"])
        ),
    )
    observation_key = (True, True, tuple(sorted(value["observed"])))
    return model_key, observation_key, _event_id_key(value["id"])


def _occurrence(value, include_id):
    event = {
        "event_time": value["time"],
        "event_type": value["type"],
        "marks": dict(
            (name, list(value["marks"][name]))
            for name in sorted(value["marks"])
        ),
    }
    if include_id:
        event["event_id"] = _event_id_tree(value["id"])
    return {
        "event": event,
        "observation": {
            "observed_marks": sorted(value["observed"]),
            "time_observed": True,
            "type_observed": True,
        },
    }


def _h_semantics():
    schema = _schema(
        (
            _event_type(0, "pulse"),
            _event_type(
                1,
                "signal",
                (
                    _field(
                        "amplitude",
                        "bounded",
                        lower="-0x1.0000000000000p+0",
                        upper="0x1.0000000000000p+0",
                    ),
                ),
            ),
            _event_type(
                2,
                "context",
                (
                    _field(
                        "confidence",
                        "bounded",
                        lower="0x0.0p+0",
                        upper="0x1.0000000000000p+0",
                    ),
                    _field(
                        "offset",
                        "bounded",
                        lower="-0x1.0000000000000p+1",
                        upper="0x1.0000000000000p+1",
                    ),
                ),
            ),
        ),
        5.0,
        "continuous",
        _time_reference("continuous", continuous_weight=1.0),
        False,
        "typed-hawkes-v1",
        "simple",
    )
    events = (
        _event(
            "0x1.cf1855d70ebbcp+0",
            2,
            {
                "confidence": ("0x1.4b1ab6ef864a8p-4",),
                "offset": ("0x1.b7babfb741a10p-2",),
            },
            "synthetic-0",
            ("confidence", "offset"),
        ),
        _event("0x1.1653623b3be4bp+1", 0, {}, "synthetic-1", ()),
        _event(
            "0x1.3e42787ff2068p+1",
            2,
            {
                "confidence": ("0x1.e89aeef03e002p-2",),
                "offset": ("-0x1.1cafef61a3958p-2",),
            },
            "synthetic-2",
            ("confidence", "offset"),
        ),
        _event(
            "0x1.dc122584e1c9cp+1",
            2,
            {
                "confidence": ("0x1.6bea1724b70f0p-3",),
                "offset": ("0x1.bddb31676cc48p-2",),
            },
            "synthetic-3",
            ("confidence", "offset"),
        ),
        _event(
            "0x1.3c7775e58935ep+2",
            1,
            {"amplitude": ("-0x1.77671a63a3994p-1",)},
            "synthetic-4",
            ("amplitude",),
        ),
    )
    return schema, events, "H-CONT-1", "generated-process-group-1"


def _m_semantics():
    fields = (
        _field(
            "midi_clock_onset_offset",
            "real",
            unit="midi-clock-grid-width",
        ),
        _field(
            "velocity_normalized",
            "positive",
            unit="midi-velocity/127",
        ),
    )
    schema = _schema(
        tuple(
            _event_type(pitch, "midi_pitch_{}".format(pitch), fields)
            for pitch in range(21, 109)
        ),
        1.0,
        "atomic_grid",
        _time_reference("atomic_grid", (0.0, 1.0)),
        True,
        "maestro-midi-clock-counting-fixture-v1",
        "finite_counting",
    )
    observed = ("midi_clock_onset_offset", "velocity_normalized")
    events = (
        _event(
            "0x0.0p+0",
            60,
            {
                "midi_clock_onset_offset": ("0x0.0p+0",),
                "velocity_normalized": ("0x1.0204081020408p-1",),
            },
            "e66a8466a2b7194845e59c0a56bc74913a7fb21a9cbc796ced54179e00d48dbf",
            observed,
        ),
        _event(
            "0x0.0p+0",
            60,
            {
                "midi_clock_onset_offset": ("0x0.0p+0",),
                "velocity_normalized": ("0x1.0204081020408p-1",),
            },
            "340d8b6b22ad77171e5eec884c0e62eb4aec9875c728b5a8bb9ec2cb2c27ccd2",
            observed,
        ),
        _event(
            "0x0.0p+0",
            64,
            {
                "midi_clock_onset_offset": ("0x0.0p+0",),
                "velocity_normalized": ("0x1.83060c183060cp-1",),
            },
            "0583c7b11456e4720edf5117d3ba7346cdffbda00b28a229a4d47775d2c32fed",
            observed,
        ),
        _event(
            "0x1.0000000000000p+0",
            67,
            {
                "midi_clock_onset_offset": ("0x1.0000000000000p+0",),
                "velocity_normalized": ("0x1.0000000000000p+0",),
            },
            "778afd99b07f0ee056bb19e0513edad5e1fa997334a672fe7bbe88b4719d88f9",
            observed,
        ),
    )
    return schema, events, "M-ACG-1", "synthetic-maestro-group-1"


def _p_semantics():
    schema = _schema(
        (
            _event_type(
                0,
                "HR",
                (_field("value", "positive", unit="beats/minute"),),
            ),
            _event_type(
                1,
                "Temp",
                (_field("value", "real", unit="degC"),),
            ),
            _event_type(
                2,
                "Urine",
                (_field("value", "positive", unit="mL"),),
            ),
            _event_type(
                3,
                "Weight",
                (_field("value", "positive", unit="kg"),),
            ),
        ),
        2880.0,
        "atomic_grid",
        _time_reference("atomic_grid", range(2881)),
        True,
        "physionet-2012-counting-fixture-v1",
        "finite_counting",
    )
    prefix = ("physionet-2012-row", "900001")
    events = (
        _event(
            _hx(5.0),
            0,
            {"value": (_hx(80.0),)},
            prefix + (8,),
            ("value",),
        ),
        _event(
            _hx(5.0),
            0,
            {"value": (_hx(80.0),)},
            prefix + (9,),
            ("value",),
        ),
        _event(
            _hx(5.0),
            1,
            {"value": (_hx(37.0),)},
            prefix + (10,),
            ("value",),
        ),
        _event(
            _hx(6.0),
            2,
            {"value": (_hx(120.0),)},
            prefix + (11,),
            ("value",),
        ),
        _event(
            _hx(7.0),
            3,
            {"value": (_hx(81.5),)},
            prefix + (12,),
            ("value",),
        ),
        _event(_hx(8.0), 0, {}, prefix + (13,), ()),
    )
    return schema, events, "900001", "900001"


def _r_semantics(family):
    fields = (
        _field("quantity", "real", unit="item-count"),
        _field("unit_price", "positive", unit="currency-unit/item"),
    )
    schema = _schema(
        (
            _event_type(0, "sku-a__active", fields),
            _event_type(1, "sku-a__cancelled", fields),
            _event_type(2, "sku-b__active", fields),
            _event_type(3, "sku-b__cancelled", fields),
        ),
        7.0,
        "atomic_grid",
        _time_reference("atomic_grid", (5.0, 7.0)),
        True,
        "generated-transaction-counting-fixture-v1",
        "finite_counting",
    )
    observed = ("quantity", "unit_price")
    if family == "R-ACG-1-A":
        source = (
            "9f11c4b120f42df3cf35bd485a405c56dbceba6177911143b452b17932a23584"
        )
        events = (
            _event(
                _hx(5.0),
                0,
                {"quantity": (_hx(2.0),), "unit_price": (_hx(3.5),)},
                ("generated-transaction-row", source, 2),
                observed,
            ),
            _event(
                _hx(5.0),
                0,
                {"quantity": (_hx(2.0),), "unit_price": (_hx(3.5),)},
                ("generated-transaction-row", source, 3),
                observed,
            ),
            _event(
                _hx(5.0),
                3,
                {"quantity": (_hx(1.0),), "unit_price": (_hx(4.25),)},
                ("generated-transaction-row", source, 4),
                observed,
            ),
        )
        sample = "invoice-a"
    else:
        source = (
            "25dd1cb8c9979c3ea6db4563e171e53c691c00650566b24d8a62342bc023673d"
        )
        events = (
            _event(
                _hx(7.0),
                1,
                {"quantity": (_hx(-2.0),), "unit_price": (_hx(3.5),)},
                ("generated-transaction-row", source, 2),
                observed,
            ),
            _event(
                _hx(7.0),
                2,
                {"quantity": (_hx(-1.0),), "unit_price": (_hx(4.25),)},
                ("generated-transaction-row", source, 3),
                observed,
            ),
        )
        sample = "invoice-b"
    return schema, events, sample, "customer-shared"


def _semantics(family):
    if family == "H-CONT-1":
        return _h_semantics()
    if family == "M-ACG-1":
        return _m_semantics()
    if family == "P-ACG-1":
        return _p_semantics()
    return _r_semantics(family)


def _configuration_payload(case):
    schema, raw_events, sample, group = _semantics(case["family"])
    events = tuple(sorted(raw_events, key=_event_key))
    tree = {
        "group_id": group,
        "observation_pattern": {"cardinality_observed": True},
        "occurrences": [_occurrence(item, True) for item in events],
        "sample_id": sample,
        "schema": schema,
    }
    payload = _canonical(tree)
    actual = _domain_digest(
        "heterodiff.adapter.private-native-configuration.v1",
        tree,
    )
    if actual != case["configuration"]:
        raise ValueError()
    detached = {
        "occurrences": [_occurrence(item, False) for item in events],
        "observation_pattern": {"cardinality_observed": True},
        "schema": schema,
    }
    native = _domain_digest(
        "heterodiff.adapter.native-observation.v1",
        detached,
    )
    if native != case["native"]:
        raise ValueError()
    return payload, native


def _evidence_payload(case, native):
    source_sha256 = case["source_sha256"]
    policy = case["policy"]
    tree = {
        "coverage": {
            "coverage_ledger_sha256": case["coverage"],
            "policy_sha256": policy,
            "source_inventory_sha256": case["inventory"],
            "source_sha256": source_sha256,
            "source_size_bytes": len(case["source"]),
        },
        "evaluation_labels": {
            "evaluation_labels_sha256": case["labels"],
            "format_id": case["labels_format"],
            "policy_sha256": policy,
            "source_sha256": source_sha256,
        },
        "fitted_state_sha256": _NO_FIT,
        "native_observation_sha256": native,
        "private_provenance": {
            "native_observation_sha256": native,
            "policy_sha256": policy,
            "private_provenance_sha256": case["provenance"],
            "source_sha256": source_sha256,
        },
        "semantic_reconstruction_sha256": case["reconstruction"],
        "source_inventory_sha256": case["inventory"],
        "static_context": {
            "format_id": case["static_format"],
            "policy_sha256": policy,
            "source_sha256": source_sha256,
            "static_context_sha256": case["static"],
        },
    }
    if _domain_digest(
        "heterodiff.adapter.expected-evidence.v1",
        tree,
    ) != case["evidence"]:
        raise ValueError()
    return _canonical(tree)


def _read_u64(frame, offset):
    end = offset + 8
    if end > len(frame):
        raise ValueError()
    return int.from_bytes(frame[offset:end], "big"), end


def _parse_frame(frame):
    if not frame or len(frame) > _MAX_FRAME:
        raise ValueError()
    end = len(_REQUEST_DOMAIN)
    if len(frame) < end + 1 or frame[:end] != _REQUEST_DOMAIN:
        raise ValueError()
    if frame[end] != 0:
        raise ValueError()
    count, offset = _read_u64(frame, end + 1)
    if count != len(_REQUEST_NAMES):
        raise ValueError()
    values = []
    for expected in _REQUEST_NAMES:
        size, offset = _read_u64(frame, offset)
        if size > len(frame) - offset:
            raise ValueError()
        name_end = offset + size
        if frame[offset:name_end] != expected:
            raise ValueError()
        offset = name_end
        size, offset = _read_u64(frame, offset)
        if size > len(frame) - offset:
            raise ValueError()
        value_end = offset + size
        values.append(frame[offset:value_end])
        offset = value_end
    if offset != len(frame):
        raise ValueError()
    return tuple(values)


def _digest(value):
    if len(value) != 64 or any(item not in _HEX for item in value):
        raise ValueError()
    return value


def _u64(value):
    if len(value) != 8:
        raise ValueError()
    return int.from_bytes(value, "big")


def _validate_json_tree(value):
    count = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        count += 1
        if count > _MAX_JSON_NODES or depth > _MAX_JSON_DEPTH:
            raise ValueError()
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current) > _MAX_SAFE_INTEGER:
                raise ValueError()
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                raise ValueError()
            if len(encoded) > _MAX_JSON_STRING_BYTES:
                raise ValueError()
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    raise ValueError()
                try:
                    encoded = key.encode("ascii", "strict")
                except UnicodeError:
                    raise ValueError()
                if len(encoded) > _MAX_JSON_STRING_BYTES:
                    raise ValueError()
                stack.append((item, depth + 1))
            continue
        raise ValueError()


def _lexical_json_preflight(value):
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if byte >= 0x80:
            raise ValueError()
        if in_string:
            if not escaped and byte == 0x22:
                in_string = False
                continue
            string_bytes += 1
            if string_bytes > _MAX_JSON_STRING_BYTES:
                raise ValueError()
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > _MAX_JSON_DEPTH:
                raise ValueError()
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                raise ValueError()
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > _MAX_JSON_NODES * 2:
            raise ValueError()
    if in_string or depth != 0:
        raise ValueError()


def _strict_json(value):
    if not value or len(value) > _MAX_STRUCTURED:
        raise ValueError()
    _lexical_json_preflight(value)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        raise ValueError()

    def pairs_hook(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError()
            result[key] = item
        return result

    def integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise ValueError()
        result = int(token, 10)
        if abs(result) > _MAX_SAFE_INTEGER:
            raise ValueError()
        return result

    def number(_token):
        raise ValueError()

    try:
        tree = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_int=integer,
            parse_float=number,
            parse_constant=number,
        )
    except ValueError:
        raise ValueError()
    except (TypeError, RecursionError):
        raise ValueError()
    _validate_json_tree(tree)
    try:
        encoded = _canonical(tree)
    except (TypeError, ValueError, UnicodeError):
        raise ValueError()
    if encoded != value:
        raise ValueError()
    return value


def _select_case(values):
    _digest(values[0])
    ordinal = _u64(values[1])
    if ordinal > 4095 or values[2] != _ORACLE_ID:
        raise ValueError()
    oracle_size = _u64(values[3])
    if oracle_size == 0 or oracle_size > _MAX_ORACLE_SOURCE:
        raise ValueError()
    _digest(values[4])
    source = values[5]
    if not source or len(source) > _MAX_CASE_SOURCE:
        raise ValueError()
    _strict_json(values[6])
    _strict_json(values[7])
    _strict_json(values[8])
    source_sha256 = hashlib.sha256(source).hexdigest()
    case = _CASE_BY_SOURCE_SHA256.get(source_sha256)
    if (
        case is None
        or source != case["source"]
        or ordinal != case["ordinal"]
        or values[6] != case["descriptor"]
        or values[7] != case["partition"]
        or values[8] != _SPLIT
    ):
        raise ValueError()
    return case


def _build_frame(names, values):
    result = [_RESPONSE_DOMAIN, b"\x00", len(names).to_bytes(8, "big")]
    for name, value in zip(names, values):
        result.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(value).to_bytes(8, "big"),
                value,
            )
        )
    frame = b"".join(result)
    if len(frame) > _MAX_FRAME:
        raise ValueError()
    return frame


def _process(frame):
    values = _parse_frame(frame)
    case = _select_case(values)
    configuration, native = _configuration_payload(case)
    evidence = _evidence_payload(case, native)
    response_values = (
        hashlib.sha256(frame).hexdigest().encode("ascii"),
        values[1],
        values[2],
        values[3],
        values[4],
        configuration,
        evidence,
        native.encode("ascii"),
    )
    return _build_frame(_RESPONSE_NAMES, response_values)


def _reject(status, close_stdout):
    if close_stdout:
        try:
            sys.stdout.buffer.close()
        except BaseException:
            pass
    try:
        sys.stderr.buffer.write(_REJECTION)
        sys.stderr.buffer.flush()
    except BaseException:
        pass
    return status


def _main():
    try:
        frame = sys.stdin.buffer.read(33554433)
        response = _process(frame)
    except BaseException:
        return _reject(64, False)
    try:
        written = sys.stdout.buffer.write(response)
        sys.stdout.buffer.flush()
    except BaseException:
        return _reject(74, True)
    if written != len(response):
        return _reject(74, True)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
