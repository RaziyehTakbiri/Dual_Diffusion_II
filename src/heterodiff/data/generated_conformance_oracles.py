"""Hand-authored golden oracles for the generated conformance corpus.

This module is the trusted side of the generated Phase-C gate.  It does not
import a generated fixture builder, source parser, semantic builder, or the
adapter implementation under test.  Exact source objects, schemas, native
events, observation masks, and every private evidence leaf are frozen here as
literal commitments.  Runtime construction uses only the neutral event and
adapter-evidence contracts.

The fixtures remain generated conformance data only.  These oracles do not
establish model quality, official-dataset performance, or generalization.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    MultiplicityMode,
    ObservationPattern,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)

from .adapter_contract import feature_schema_digest, native_observation_digest
from .adapter_evidence import (
    CoverageDisposition,
    CoverageEntry,
    EvaluationLabelEntry,
    EvaluationLabels,
    ExpectedAdapterEvidence,
    OccurrenceProvenance,
    PrivateProvenance,
    SemanticReconstruction,
    SourceCoverageLedger,
    SourceFieldStatus,
    SourceInventory,
    SourceInventoryItem,
    SourceValueStatus,
    StaticContext,
    StaticContextEntry,
    native_occurrence_digests,
    source_inventory_digest,
)


H_FAMILY_ID = "H-CONT-1"
M_FAMILY_ID = "M-ACG-1"
P_FAMILY_ID = "P-ACG-1"
R_A_FAMILY_ID = "R-ACG-1-A"
R_B_FAMILY_ID = "R-ACG-1-B"

H_EXPECTED_SAMPLE_ID = "H-CONT-1"
H_EXPECTED_GROUP_ID = "generated-process-group-1"
M_EXPECTED_SAMPLE_ID = "M-ACG-1"
M_EXPECTED_GROUP_ID = "synthetic-maestro-group-1"
P_EXPECTED_SAMPLE_ID = "900001"
P_EXPECTED_GROUP_ID = "900001"
R_EXPECTED_GROUP_ID = "customer-shared"

END_OF_STREAM_EXCLUSION_REASON = "structural-terminator"
PARTITION_IDENTITY_EXCLUSION_REASON = "partition-identity"


class GeneratedConformanceOracleError(ValueError):
    """A source or family is outside the independently frozen oracle set."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _policy_digest(value: object) -> str:
    payload = _canonical_bytes(value)
    digest = hashlib.sha256()
    digest.update(b"heterodiff.generated-adapter-policy.v1\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


H_POLICY_SHA256 = _policy_digest(
    {
        "family": "continuous-simple-0-1-2",
        "fixture": H_FAMILY_ID,
        "labels": "frozen-process-parameters",
        "source_observation": "all-present-values",
    }
)
M_POLICY_SHA256 = _policy_digest(
    {
        "family": "atomic-counting-a",
        "fixture": M_FAMILY_ID,
        "note_pairing": "frozen-fifo",
        "projection": "midi-clock-onset",
        "raw_reconstruction": True,
    }
)
P_POLICY_SHA256 = _policy_digest(
    {
        "family": "atomic-counting-b",
        "fixture": P_FAMILY_ID,
        "missingness": "parameter-specific-minus-one",
        "row_policy": "one-dynamic-observation-row-one-occurrence",
        "static_context": "admission-descriptors",
    }
)
R_POLICY_SHA256 = _policy_digest(
    {
        "cancellation": "explicit-field",
        "family": "atomic-counting-c",
        "group": "customer",
        "sample": "invoice",
        "type_vocabulary": "frozen-product-by-cancellation",
    }
)

_FROZEN_POLICY_DIGESTS = (
    "e51c63f9e79c0db1ba01ccbfb8b1036537edf3577cb5cfe84315c164c637abe3",
    "2b49f41b0e62e4d387a2c668db1340b2e1233f92beba8bdc9bbe937de78f15e7",
    "82dc11a52bc22a80a596af3424c09457e4a92ee53a7c2288ab6db1a0c39e1187",
    "ca1c5a66165d704c671a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49",
)
if (H_POLICY_SHA256, M_POLICY_SHA256, P_POLICY_SHA256, R_POLICY_SHA256) != (
    _FROZEN_POLICY_DIGESTS
):
    raise RuntimeError("independent generated policy commitments changed")

_POLICY_BY_FAMILY = MappingProxyType(
    {
        H_FAMILY_ID: H_POLICY_SHA256,
        M_FAMILY_ID: M_POLICY_SHA256,
        P_FAMILY_ID: P_POLICY_SHA256,
        R_A_FAMILY_ID: R_POLICY_SHA256,
        R_B_FAMILY_ID: R_POLICY_SHA256,
    }
)

_SOURCE_IDENTITY_BY_FAMILY = MappingProxyType(
    {
        H_FAMILY_ID: (
            847,
            "ce4f6022bb73ab8e4025be0de65afadb111d30ea57f9e1d6b6575b685039f797",
        ),
        M_FAMILY_ID: (
            65,
            "5526627c28764a13534549c46353dc15f65fde3b00e7b91e1cc4a1cd1b38457d",
        ),
        P_FAMILY_ID: (
            207,
            "f75b1604bed422d4af8290bb5356ec4212f18c3020d772f7022611aa9c551ad4",
        ),
        R_A_FAMILY_ID: (
            214,
            "9f11c4b120f42df3cf35bd485a405c56dbceba6177911143b452b17932a23584",
        ),
        R_B_FAMILY_ID: (
            168,
            "25dd1cb8c9979c3ea6db4563e171e53c691c00650566b24d8a62342bc023673d",
        ),
    }
)


# The registry is intentionally a data literal rather than executable parser
# logic.  Every byte payload is strict base64 and every native float below is
# spelled with ``float.fromhex`` (or an exact integer conversion).
_GOLDEN_JSON = (
    "{\"H-CONT-1\":{\"coverage\":[{\"disposition\":\"event_occurrence\",\"exclusion_reason"
    "_code\":null,\"item_key\":\"event.0000\",\"secondary_tags\":[],\"target_key\":\"occurr"
    "ence.event.0000\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":"
    "null,\"item_key\":\"event.0001\",\"secondary_tags\":[],\"target_key\":\"occurrence.ev"
    "ent.0001\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"i"
    "tem_key\":\"event.0002\",\"secondary_tags\":[],\"target_key\":\"occurrence.event.000"
    "2\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key"
    "\":\"event.0003\",\"secondary_tags\":[],\"target_key\":\"occurrence.event.0003\"},{\"d"
    "isposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"even"
    "t.0004\",\"secondary_tags\":[],\"target_key\":\"occurrence.event.0004\"},{\"disposit"
    "ion\":\"evaluation_only_label\",\"exclusion_reason_code\":null,\"item_key\":\"metada"
    "ta\",\"secondary_tags\":[],\"target_key\":\"process-parameters\"}],\"evaluation_labe"
    "ls\":{\"entries\":[[\"process-parameters\",\"eyJiYXNlbGluZSI6WyIweDEuOTk5OTk5OTk5O"
    "Tk5YXAtMSIsIjB4MS42NjY2NjY2NjY2NjY2cC0xIiwiMHgxLjMzMzMzMzMzMzMzMzNwLTEiXSwiZ"
    "GVjYXkiOltbIjB4MS4wMDAwMDAwMDAwMDAwcCswIiwiMHgxLjAwMDAwMDAwMDAwMDBwKzAiLCIwe"
    "DEuMDAwMDAwMDAwMDAwMHArMCJdLFsiMHgxLjAwMDAwMDAwMDAwMDBwKzAiLCIweDEuMDAwMDAwM"
    "DAwMDAwMHArMCIsIjB4MS4wMDAwMDAwMDAwMDAwcCswIl0sWyIweDEuMDAwMDAwMDAwMDAwMHArM"
    "CIsIjB4MS4wMDAwMDAwMDAwMDAwcCswIiwiMHgxLjAwMDAwMDAwMDAwMDBwKzAiXV0sImV2ZW50X"
    "3R5cGVzIjpbeyJleGNpdGF0aW9uX3dlaWdodHMiOltdLCJmaWVsZHMiOltdLCJuYW1lIjoicHVsc"
    "2UiLCJ0eXBlX2lkIjowfSx7ImV4Y2l0YXRpb25fd2VpZ2h0cyI6WyIweDEuOTk5OTk5OTk5OTk5Y"
    "XAtMyJdLCJmaWVsZHMiOlt7ImRpc3RyaWJ1dGlvbiI6InVuaWZvcm0iLCJuYW1lIjoiYW1wbGl0d"
    "WRlIiwicGFyYW1ldGVycyI6W1sibG93IiwiLTB4MS4wMDAwMDAwMDAwMDAwcCswIl0sWyJoaWdoI"
    "iwiMHgxLjAwMDAwMDAwMDAwMDBwKzAiXV0sInN1cHBvcnQiOlsiLTB4MS4wMDAwMDAwMDAwMDAwc"
    "CswIiwiMHgxLjAwMDAwMDAwMDAwMDBwKzAiXX1dLCJuYW1lIjoic2lnbmFsIiwidHlwZV9pZCI6M"
    "X0seyJleGNpdGF0aW9uX3dlaWdodHMiOlsiMHgxLjk5OTk5OTk5OTk5OWFwLTQiLCItMHgxLjk5O"
    "Tk5OTk5OTk5OWFwLTQiXSwiZmllbGRzIjpbeyJkaXN0cmlidXRpb24iOiJ1bmlmb3JtIiwibmFtZ"
    "SI6ImNvbmZpZGVuY2UiLCJwYXJhbWV0ZXJzIjpbWyJsb3ciLCIweDAuMHArMCJdLFsiaGlnaCIsI"
    "jB4MS4wMDAwMDAwMDAwMDAwcCswIl1dLCJzdXBwb3J0IjpbIjB4MC4wcCswIiwiMHgxLjAwMDAwM"
    "DAwMDAwMDBwKzAiXX0seyJkaXN0cmlidXRpb24iOiJ1bmlmb3JtIiwibmFtZSI6Im9mZnNldCIsI"
    "nBhcmFtZXRlcnMiOltbImxvdyIsIi0weDEuMDAwMDAwMDAwMDAwMHArMSJdLFsiaGlnaCIsIjB4M"
    "S4wMDAwMDAwMDAwMDAwcCsxIl1dLCJzdXBwb3J0IjpbIi0weDEuMDAwMDAwMDAwMDAwMHArMSIsI"
    "jB4MS4wMDAwMDAwMDAwMDAwcCsxIl19XSwibmFtZSI6ImNvbnRleHQiLCJ0eXBlX2lkIjoyfV0sI"
    "mV4Y2l0YXRpb24iOltbIjB4MS45OTk5OTk5OTk5OTlhcC01IiwiMHgxLjQ3YWUxNDdhZTE0N2JwL"
    "TYiLCIweDEuNDdhZTE0N2FlMTQ3YnAtNyJdLFsiMHgxLjQ3YWUxNDdhZTE0N2JwLTYiLCIweDEuO"
    "Tk5OTk5OTk5OTk5YXAtNSIsIjB4MS40N2FlMTQ3YWUxNDdicC02Il0sWyIweDEuNDdhZTE0N2FlM"
    "TQ3YnAtNyIsIjB4MS40N2FlMTQ3YWUxNDdicC02IiwiMHgxLjk5OTk5OTk5OTk5OWFwLTUiXV0sI"
    "m1hcmtfbG9nX3N0cmVuZ3RoX2NsaXAiOiIweDEuODAwMDAwMDAwMDAwMHAtMSIsInBhcmFtZXRlc"
    "l9pZCI6ImhldGVyb2RpZmYuZ2VuZXJhdGVkLWhhd2tlcy1wYXJhbWV0ZXJzLnYxIn0=\"]],\"form"
    "at_id\":\"generated.process-parameters.v1\"},\"inventory\":{\"item_format_id\":\"gen"
    "erated.hawkes-item.v1\",\"items\":[[\"event.0000\",\"eyJldmVudF90eXBlIjoyLCJtYXJrc"
    "yI6WyIweDEuNGIxYWI2ZWY4NjRhOHAtNCIsIjB4MS5iN2JhYmZiNzQxYTEwcC0yIl0sInRpbWUiO"
    "iIweDEuY2YxODU1ZDcwZWJiY3ArMCIsInR5cGVfbmFtZSI6ImNvbnRleHQifQ==\"],[\"event.00"
    "01\",\"eyJldmVudF90eXBlIjowLCJtYXJrcyI6W10sInRpbWUiOiIweDEuMTY1MzYyM2IzYmU0YnA"
    "rMSIsInR5cGVfbmFtZSI6InB1bHNlIn0=\"],[\"event.0002\",\"eyJldmVudF90eXBlIjoyLCJtY"
    "XJrcyI6WyIweDEuZTg5YWVlZjAzZTAwMnAtMiIsIi0weDEuMWNhZmVmNjFhMzk1OHAtMiJdLCJ0a"
    "W1lIjoiMHgxLjNlNDI3ODdmZjIwNjhwKzEiLCJ0eXBlX25hbWUiOiJjb250ZXh0In0=\"],[\"even"
    "t.0003\",\"eyJldmVudF90eXBlIjoyLCJtYXJrcyI6WyIweDEuNmJlYTE3MjRiNzBmMHAtMyIsIjB"
    "4MS5iZGRiMzE2NzZjYzQ4cC0yIl0sInRpbWUiOiIweDEuZGMxMjI1ODRlMWM5Y3ArMSIsInR5cGV"
    "fbmFtZSI6ImNvbnRleHQifQ==\"],[\"event.0004\",\"eyJldmVudF90eXBlIjoxLCJtYXJrcyI6W"
    "yItMHgxLjc3NjcxYTYzYTM5OTRwLTEiXSwidGltZSI6IjB4MS4zYzc3NzVlNTg5MzVlcCsyIiwid"
    "HlwZV9uYW1lIjoic2lnbmFsIn0=\"],[\"metadata\",\"eyJjYW5kaWRhdGVfY291bnQiOjYsImhvc"
    "ml6b24iOiIweDEuNDAwMDAwMDAwMDAwMHArMiIsIm1heF9jYW5kaWRhdGVzIjoxMDAwLCJtYXhfZ"
    "XZlbnRzIjo2NCwicGFyYW1ldGVyX2lkIjoiaGV0ZXJvZGlmZi5nZW5lcmF0ZWQtaGF3a2VzLXBhc"
    "mFtZXRlcnMudjEiLCJyZWFsaXplZF9ldmVudF9jb3VudHMiOlsxLDEsM10sInNlZWQiOjQsInRlc"
    "m1pbmF0ZWRfYnkiOiJob3Jpem9uIn0=\"]]},\"native_observation_sha256\":\"3fda63942b4"
    "d78725fb24f5eb7973fba938fad4bc6dfff1a1e99b3e448dfb26d\",\"policy_sha256\":\"e51c"
    "63f9e79c0db1ba01ccbfb8b1036537edf3577cb5cfe84315c164c637abe3\",\"provenance\":["
    "{\"field_statuses\":[[\"confidence\",\"present\",null],[\"offset\",\"present\",null]],"
    "\"native_occurrence_sha256\":\"218ad874506da27d5dedb27feef902cbc84690ed79f0d645"
    "78073f00990e018c\",\"occurrence_index\":0,\"private_format_id\":\"generated.hawkes"
    "-provenance.v1\",\"private_payload_b64\":\"eyJldmVudCI6eyJldmVudF90eXBlIjoyLCJtY"
    "XJrcyI6WyIweDEuNGIxYWI2ZWY4NjRhOHAtNCIsIjB4MS5iN2JhYmZiNzQxYTEwcC0yIl0sInRpb"
    "WUiOiIweDEuY2YxODU1ZDcwZWJiY3ArMCIsInR5cGVfbmFtZSI6ImNvbnRleHQifSwic2VlZCI6N"
    "Cwic291cmNlX2luZGV4IjowfQ==\",\"provenance_key\":\"occurrence.event.0000\",\"sourc"
    "e_item_keys\":[\"event.0000\"]},{\"field_statuses\":[],\"native_occurrence_sha256\""
    ":\"e482553a8d58e26a42c53e0ef4161bc3e890e13e81bffe5ad3b17173118f9027\",\"occurre"
    "nce_index\":1,\"private_format_id\":\"generated.hawkes-provenance.v1\",\"private_p"
    "ayload_b64\":\"eyJldmVudCI6eyJldmVudF90eXBlIjowLCJtYXJrcyI6W10sInRpbWUiOiIweDE"
    "uMTY1MzYyM2IzYmU0YnArMSIsInR5cGVfbmFtZSI6InB1bHNlIn0sInNlZWQiOjQsInNvdXJjZV9"
    "pbmRleCI6MX0=\",\"provenance_key\":\"occurrence.event.0001\",\"source_item_keys\":["
    "\"event.0001\"]},{\"field_statuses\":[[\"confidence\",\"present\",null],[\"offset\",\"p"
    "resent\",null]],\"native_occurrence_sha256\":\"f042b380000d19c0a7aa00adcd4287497"
    "2c44af33009f95aa6eeff775a3001d9\",\"occurrence_index\":2,\"private_format_id\":\"g"
    "enerated.hawkes-provenance.v1\",\"private_payload_b64\":\"eyJldmVudCI6eyJldmVudF"
    "90eXBlIjoyLCJtYXJrcyI6WyIweDEuZTg5YWVlZjAzZTAwMnAtMiIsIi0weDEuMWNhZmVmNjFhMz"
    "k1OHAtMiJdLCJ0aW1lIjoiMHgxLjNlNDI3ODdmZjIwNjhwKzEiLCJ0eXBlX25hbWUiOiJjb250ZX"
    "h0In0sInNlZWQiOjQsInNvdXJjZV9pbmRleCI6Mn0=\",\"provenance_key\":\"occurrence.eve"
    "nt.0002\",\"source_item_keys\":[\"event.0002\"]},{\"field_statuses\":[[\"confidence\""
    ",\"present\",null],[\"offset\",\"present\",null]],\"native_occurrence_sha256\":\"ae2a"
    "2c3b82a1b360f046aac4b40e7a18354da363cc0406f5c5bb83bf1357d980\",\"occurrence_in"
    "dex\":3,\"private_format_id\":\"generated.hawkes-provenance.v1\",\"private_payload"
    "_b64\":\"eyJldmVudCI6eyJldmVudF90eXBlIjoyLCJtYXJrcyI6WyIweDEuNmJlYTE3MjRiNzBmM"
    "HAtMyIsIjB4MS5iZGRiMzE2NzZjYzQ4cC0yIl0sInRpbWUiOiIweDEuZGMxMjI1ODRlMWM5Y3ArM"
    "SIsInR5cGVfbmFtZSI6ImNvbnRleHQifSwic2VlZCI6NCwic291cmNlX2luZGV4IjozfQ==\",\"pr"
    "ovenance_key\":\"occurrence.event.0003\",\"source_item_keys\":[\"event.0003\"]},{\"f"
    "ield_statuses\":[[\"amplitude\",\"present\",null]],\"native_occurrence_sha256\":\"4b"
    "da47c6513438476c4c3232b3212064974bdded9f71b84c87248b22acff45f6\",\"occurrence_"
    "index\":4,\"private_format_id\":\"generated.hawkes-provenance.v1\",\"private_paylo"
    "ad_b64\":\"eyJldmVudCI6eyJldmVudF90eXBlIjoxLCJtYXJrcyI6WyItMHgxLjc3NjcxYTYzYTM"
    "5OTRwLTEiXSwidGltZSI6IjB4MS4zYzc3NzVlNTg5MzVlcCsyIiwidHlwZV9uYW1lIjoic2lnbmF"
    "sIn0sInNlZWQiOjQsInNvdXJjZV9pbmRleCI6NH0=\",\"provenance_key\":\"occurrence.even"
    "t.0004\",\"source_item_keys\":[\"event.0004\"]}],\"reconstruction\":{\"canonical_pay"
    "load_b64\":\"eyJldmVudHMiOlt7ImV2ZW50X3R5cGUiOjIsIm1hcmtzIjpbIjB4MS40YjFhYjZlZ"
    "jg2NGE4cC00IiwiMHgxLmI3YmFiZmI3NDFhMTBwLTIiXSwidGltZSI6IjB4MS5jZjE4NTVkNzBlY"
    "mJjcCswIiwidHlwZV9uYW1lIjoiY29udGV4dCJ9LHsiZXZlbnRfdHlwZSI6MCwibWFya3MiOltdL"
    "CJ0aW1lIjoiMHgxLjE2NTM2MjNiM2JlNGJwKzEiLCJ0eXBlX25hbWUiOiJwdWxzZSJ9LHsiZXZlb"
    "nRfdHlwZSI6MiwibWFya3MiOlsiMHgxLmU4OWFlZWYwM2UwMDJwLTIiLCItMHgxLjFjYWZlZjYxY"
    "TM5NThwLTIiXSwidGltZSI6IjB4MS4zZTQyNzg3ZmYyMDY4cCsxIiwidHlwZV9uYW1lIjoiY29ud"
    "GV4dCJ9LHsiZXZlbnRfdHlwZSI6MiwibWFya3MiOlsiMHgxLjZiZWExNzI0YjcwZjBwLTMiLCIwe"
    "DEuYmRkYjMxNjc2Y2M0OHAtMiJdLCJ0aW1lIjoiMHgxLmRjMTIyNTg0ZTFjOWNwKzEiLCJ0eXBlX"
    "25hbWUiOiJjb250ZXh0In0seyJldmVudF90eXBlIjoxLCJtYXJrcyI6WyItMHgxLjc3NjcxYTYzY"
    "TM5OTRwLTEiXSwidGltZSI6IjB4MS4zYzc3NzVlNTg5MzVlcCsyIiwidHlwZV9uYW1lIjoic2lnb"
    "mFsIn1dLCJmb3JtYXQiOiJoZXRlcm9kaWZmLmdlbmVyYXRlZC1oYXdrZXMtc2VtYW50aWMtcmVjb"
    "3JkLnYxIn0=\",\"record_count\":5,\"schema_sha256\":\"52b9726910af952ebf29a63a71092"
    "e10c4b12e26094d557aac6f32d27fce47af\",\"semantic_format_id\":\"generated.hawkes-"
    "semantic.v1\"},\"source_b64\":\"eyJldmVudHMiOlt7ImV2ZW50X3R5cGUiOjIsIm1hcmtzIjpb"
    "IjB4MS40YjFhYjZlZjg2NGE4cC00IiwiMHgxLmI3YmFiZmI3NDFhMTBwLTIiXSwidGltZSI6IjB4"
    "MS5jZjE4NTVkNzBlYmJjcCswIiwidHlwZV9uYW1lIjoiY29udGV4dCJ9LHsiZXZlbnRfdHlwZSI6"
    "MCwibWFya3MiOltdLCJ0aW1lIjoiMHgxLjE2NTM2MjNiM2JlNGJwKzEiLCJ0eXBlX25hbWUiOiJw"
    "dWxzZSJ9LHsiZXZlbnRfdHlwZSI6MiwibWFya3MiOlsiMHgxLmU4OWFlZWYwM2UwMDJwLTIiLCIt"
    "MHgxLjFjYWZlZjYxYTM5NThwLTIiXSwidGltZSI6IjB4MS4zZTQyNzg3ZmYyMDY4cCsxIiwidHlw"
    "ZV9uYW1lIjoiY29udGV4dCJ9LHsiZXZlbnRfdHlwZSI6MiwibWFya3MiOlsiMHgxLjZiZWExNzI0"
    "YjcwZjBwLTMiLCIweDEuYmRkYjMxNjc2Y2M0OHAtMiJdLCJ0aW1lIjoiMHgxLmRjMTIyNTg0ZTFj"
    "OWNwKzEiLCJ0eXBlX25hbWUiOiJjb250ZXh0In0seyJldmVudF90eXBlIjoxLCJtYXJrcyI6WyIt"
    "MHgxLjc3NjcxYTYzYTM5OTRwLTEiXSwidGltZSI6IjB4MS4zYzc3NzVlNTg5MzVlcCsyIiwidHlw"
    "ZV9uYW1lIjoic2lnbmFsIn1dLCJmb3JtYXQiOiJoZXRlcm9kaWZmLmdlbmVyYXRlZC1oYXdrZXMt"
    "c291cmNlLnYxIiwibWV0YWRhdGEiOnsiY2FuZGlkYXRlX2NvdW50Ijo2LCJob3Jpem9uIjoiMHgx"
    "LjQwMDAwMDAwMDAwMDBwKzIiLCJtYXhfY2FuZGlkYXRlcyI6MTAwMCwibWF4X2V2ZW50cyI6NjQs"
    "InBhcmFtZXRlcl9pZCI6ImhldGVyb2RpZmYuZ2VuZXJhdGVkLWhhd2tlcy1wYXJhbWV0ZXJzLnYx"
    "IiwicmVhbGl6ZWRfZXZlbnRfY291bnRzIjpbMSwxLDNdLCJzZWVkIjo0LCJ0ZXJtaW5hdGVkX2J5"
    "IjoiaG9yaXpvbiJ9fQ==\",\"source_sha256\":\"ce4f6022bb73ab8e4025be0de65afadb111d3"
    "0ea57f9e1d6b6575b685039f797\",\"source_size_bytes\":847,\"static_context\":{\"entr"
    "ies\":[],\"format_id\":\"generated.empty-static.v1\"}},\"M-ACG-1\":{\"coverage\":[{\"d"
    "isposition\":\"static_context\",\"exclusion_reason_code\":null,\"item_key\":\"track."
    "0000.event.0000\",\"secondary_tags\":[],\"target_key\":\"tempo-map\"},{\"disposition"
    "\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"track.0000.eve"
    "nt.0001\",\"secondary_tags\":[\"note-onset\"],\"target_key\":\"note.e66a8466a2b71948"
    "45e59c0a56bc74913a7fb21a9cbc796ced54179e00d48dbf\"},{\"disposition\":\"event_occ"
    "urrence\",\"exclusion_reason_code\":null,\"item_key\":\"track.0000.event.0002\",\"se"
    "condary_tags\":[\"note-onset\"],\"target_key\":\"note.340d8b6b22ad77171e5eec884c0e"
    "62eb4aec9875c728b5a8bb9ec2cb2c27ccd2\"},{\"disposition\":\"event_occurrence\",\"ex"
    "clusion_reason_code\":null,\"item_key\":\"track.0000.event.0003\",\"secondary_tags"
    "\":[\"note-onset\"],\"target_key\":\"note.0583c7b11456e4720edf5117d3ba7346cdffbda0"
    "0b28a229a4d47775d2c32fed\"},{\"disposition\":\"event_occurrence\",\"exclusion_reas"
    "on_code\":null,\"item_key\":\"track.0000.event.0004\",\"secondary_tags\":[\"note-clo"
    "sure\"],\"target_key\":\"note.e66a8466a2b7194845e59c0a56bc74913a7fb21a9cbc796ced"
    "54179e00d48dbf\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":n"
    "ull,\"item_key\":\"track.0000.event.0005\",\"secondary_tags\":[\"note-closure\"],\"ta"
    "rget_key\":\"note.340d8b6b22ad77171e5eec884c0e62eb4aec9875c728b5a8bb9ec2cb2c27"
    "ccd2\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_"
    "key\":\"track.0000.event.0006\",\"secondary_tags\":[\"note-closure\"],\"target_key\":"
    "\"note.0583c7b11456e4720edf5117d3ba7346cdffbda00b28a229a4d47775d2c32fed\"},{\"d"
    "isposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"trac"
    "k.0000.event.0007\",\"secondary_tags\":[\"note-onset\"],\"target_key\":\"note.778afd"
    "99b07f0ee056bb19e0513edad5e1fa997334a672fe7bbe88b4719d88f9\"},{\"disposition\":"
    "\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"track.0000.event"
    ".0008\",\"secondary_tags\":[\"note-closure\"],\"target_key\":\"note.778afd99b07f0ee0"
    "56bb19e0513edad5e1fa997334a672fe7bbe88b4719d88f9\"},{\"disposition\":\"excluded_"
    "with_reason\",\"exclusion_reason_code\":\"structural-terminator\",\"item_key\":\"tra"
    "ck.0000.event.0009\",\"secondary_tags\":[\"container-structure\"],\"target_key\":nu"
    "ll}],\"evaluation_labels\":{\"entries\":[],\"format_id\":\"generated.empty-labels.v"
    "1\"},\"inventory\":{\"item_format_id\":\"generated.midi-event.v1\",\"items\":[[\"track"
    ".0000.event.0000\",\"eyJhYnNvbHV0ZV90aWNrcyI6MCwiZGVsdGFfdGlja3MiOjAsImVuY29kZ"
    "WRfaGV4IjoiMDBmZjUxMDMwN2ExMjAiLCJldmVudF9pbmRleCI6MCwia2luZCI6Im1ldGEiLCJtZ"
    "XRhX25hbWUiOiJzZXRfdGVtcG8iLCJtZXRhX3R5cGUiOjgxLCJwYXlsb2FkX2hleCI6IjA3YTEyM"
    "CIsInRyYWNrX2J5dGVfb2Zmc2V0IjowLCJ0cmFja19pbmRleCI6MH0=\"],[\"track.0000.event"
    ".0001\",\"eyJhYnNvbHV0ZV90aWNrcyI6MCwiY2hhbm5lbCI6MCwiZGF0YV9oZXgiOiIzYzQwIiwi"
    "ZGVsdGFfdGlja3MiOjAsImVuY29kZWRfaGV4IjoiMDA5MDNjNDAiLCJldmVudF9pbmRleCI6MSwi"
    "a2luZCI6ImNoYW5uZWwiLCJtZXNzYWdlX3R5cGUiOiJub3RlX29uIiwic3RhdHVzIjoxNDQsInRy"
    "YWNrX2J5dGVfb2Zmc2V0Ijo3LCJ0cmFja19pbmRleCI6MCwidXNlZF9ydW5uaW5nX3N0YXR1cyI6"
    "ZmFsc2V9\"],[\"track.0000.event.0002\",\"eyJhYnNvbHV0ZV90aWNrcyI6MCwiY2hhbm5lbCI"
    "6MCwiZGF0YV9oZXgiOiIzYzQwIiwiZGVsdGFfdGlja3MiOjAsImVuY29kZWRfaGV4IjoiMDA5MDN"
    "jNDAiLCJldmVudF9pbmRleCI6Miwia2luZCI6ImNoYW5uZWwiLCJtZXNzYWdlX3R5cGUiOiJub3R"
    "lX29uIiwic3RhdHVzIjoxNDQsInRyYWNrX2J5dGVfb2Zmc2V0IjoxMSwidHJhY2tfaW5kZXgiOjA"
    "sInVzZWRfcnVubmluZ19zdGF0dXMiOmZhbHNlfQ==\"],[\"track.0000.event.0003\",\"eyJhYn"
    "NvbHV0ZV90aWNrcyI6MCwiY2hhbm5lbCI6MCwiZGF0YV9oZXgiOiI0MDYwIiwiZGVsdGFfdGlja3"
    "MiOjAsImVuY29kZWRfaGV4IjoiMDA5MDQwNjAiLCJldmVudF9pbmRleCI6Mywia2luZCI6ImNoYW"
    "5uZWwiLCJtZXNzYWdlX3R5cGUiOiJub3RlX29uIiwic3RhdHVzIjoxNDQsInRyYWNrX2J5dGVfb2"
    "Zmc2V0IjoxNSwidHJhY2tfaW5kZXgiOjAsInVzZWRfcnVubmluZ19zdGF0dXMiOmZhbHNlfQ==\"]"
    ",[\"track.0000.event.0004\",\"eyJhYnNvbHV0ZV90aWNrcyI6MTIwLCJjaGFubmVsIjowLCJkY"
    "XRhX2hleCI6IjNjMDAiLCJkZWx0YV90aWNrcyI6MTIwLCJlbmNvZGVkX2hleCI6Ijc4ODAzYzAwI"
    "iwiZXZlbnRfaW5kZXgiOjQsImtpbmQiOiJjaGFubmVsIiwibWVzc2FnZV90eXBlIjoibm90ZV9vZ"
    "mYiLCJzdGF0dXMiOjEyOCwidHJhY2tfYnl0ZV9vZmZzZXQiOjE5LCJ0cmFja19pbmRleCI6MCwid"
    "XNlZF9ydW5uaW5nX3N0YXR1cyI6ZmFsc2V9\"],[\"track.0000.event.0005\",\"eyJhYnNvbHV0"
    "ZV90aWNrcyI6MTIwLCJjaGFubmVsIjowLCJkYXRhX2hleCI6IjNjMDAiLCJkZWx0YV90aWNrcyI6"
    "MCwiZW5jb2RlZF9oZXgiOiIwMDgwM2MwMCIsImV2ZW50X2luZGV4Ijo1LCJraW5kIjoiY2hhbm5l"
    "bCIsIm1lc3NhZ2VfdHlwZSI6Im5vdGVfb2ZmIiwic3RhdHVzIjoxMjgsInRyYWNrX2J5dGVfb2Zm"
    "c2V0IjoyMywidHJhY2tfaW5kZXgiOjAsInVzZWRfcnVubmluZ19zdGF0dXMiOmZhbHNlfQ==\"],["
    "\"track.0000.event.0006\",\"eyJhYnNvbHV0ZV90aWNrcyI6MTIwLCJjaGFubmVsIjowLCJkYXR"
    "hX2hleCI6IjQwMDAiLCJkZWx0YV90aWNrcyI6MCwiZW5jb2RlZF9oZXgiOiIwMDgwNDAwMCIsImV"
    "2ZW50X2luZGV4Ijo2LCJraW5kIjoiY2hhbm5lbCIsIm1lc3NhZ2VfdHlwZSI6Im5vdGVfb2ZmIiw"
    "ic3RhdHVzIjoxMjgsInRyYWNrX2J5dGVfb2Zmc2V0IjoyNywidHJhY2tfaW5kZXgiOjAsInVzZWR"
    "fcnVubmluZ19zdGF0dXMiOmZhbHNlfQ==\"],[\"track.0000.event.0007\",\"eyJhYnNvbHV0ZV"
    "90aWNrcyI6MTgwLCJjaGFubmVsIjowLCJkYXRhX2hleCI6IjQzN2YiLCJkZWx0YV90aWNrcyI6Nj"
    "AsImVuY29kZWRfaGV4IjoiM2M5MDQzN2YiLCJldmVudF9pbmRleCI6Nywia2luZCI6ImNoYW5uZW"
    "wiLCJtZXNzYWdlX3R5cGUiOiJub3RlX29uIiwic3RhdHVzIjoxNDQsInRyYWNrX2J5dGVfb2Zmc2"
    "V0IjozMSwidHJhY2tfaW5kZXgiOjAsInVzZWRfcnVubmluZ19zdGF0dXMiOmZhbHNlfQ==\"],[\"t"
    "rack.0000.event.0008\",\"eyJhYnNvbHV0ZV90aWNrcyI6MjQwLCJjaGFubmVsIjowLCJkYXRhX"
    "2hleCI6IjQzMDAiLCJkZWx0YV90aWNrcyI6NjAsImVuY29kZWRfaGV4IjoiM2M4MDQzMDAiLCJld"
    "mVudF9pbmRleCI6OCwia2luZCI6ImNoYW5uZWwiLCJtZXNzYWdlX3R5cGUiOiJub3RlX29mZiIsI"
    "nN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29mZnNldCI6MzUsInRyYWNrX2luZGV4IjowLCJ1c2VkX"
    "3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0=\"],[\"track.0000.event.0009\",\"eyJhYnNvbHV0ZV90"
    "aWNrcyI6MjQwLCJkZWx0YV90aWNrcyI6MCwiZW5jb2RlZF9oZXgiOiIwMGZmMmYwMCIsImV2ZW50"
    "X2luZGV4Ijo5LCJraW5kIjoibWV0YSIsIm1ldGFfbmFtZSI6ImVuZF9vZl90cmFjayIsIm1ldGFf"
    "dHlwZSI6NDcsInBheWxvYWRfaGV4IjoiIiwidHJhY2tfYnl0ZV9vZmZzZXQiOjM5LCJ0cmFja19p"
    "bmRleCI6MH0=\"]]},\"native_observation_sha256\":\"ca3aea82612d7f15d193eb4c3d48aa"
    "d152c92175b080c9f60e7355afda7dd397\",\"policy_sha256\":\"2b49f41b0e62e4d387a2c66"
    "8db1340b2e1233f92beba8bdc9bbe937de78f15e7\",\"provenance\":[{\"field_statuses\":["
    "[\"midi_clock_onset_offset\",\"present\",null],[\"velocity_normalized\",\"present\","
    "null]],\"native_occurrence_sha256\":\"541cc752d8eb0c2f01a180671ebdaac476028bd42"
    "367b5b71c9c9f076d3592ef\",\"occurrence_index\":2,\"private_format_id\":\"generated"
    ".note-provenance.v1\",\"private_payload_b64\":\"eyJjbG9zdXJlX3Byb3ZlbmFuY2UiOnsi"
    "YWJzb2x1dGVfdGljayI6MTIwLCJkYXRhX2hleCI6IjQwMDAiLCJkZWx0YV90aWNrcyI6MCwiZW5j"
    "b2RlZF9ieXRlc19oZXgiOiIwMDgwNDAwMCIsImV2ZW50X2luZGV4Ijo2LCJtZXNzYWdlX3R5cGUi"
    "OiJub3RlX29mZiIsInN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29mZnNldCI6MjcsInRyYWNrX2lu"
    "ZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sImNsb3N1cmVfc3BlbGxpbmciOiJu"
    "b3RlX29mZiIsImdyaWRfaW5kZXgiOjAsImlkZW50aXR5Ijp7ImNoYW5uZWwiOjAsInBpdGNoIjo2"
    "NCwicG9ydCI6MH0sIm1pZGlfY2xvY2tfb25zZXRfb2Zmc2V0X2V4YWN0Ijp7ImRlbm9taW5hdG9y"
    "IjoxLCJudW1lcmF0b3IiOjB9LCJub3RlX2lkIjoiMDU4M2M3YjExNDU2ZTQ3MjBlZGY1MTE3ZDNi"
    "YTczNDZjZGZmYmRhMDBiMjhhMjI5YTRkNDc3NzVkMmMzMmZlZCIsIm9uc2V0X3Byb3ZlbmFuY2Ui"
    "OnsiYWJzb2x1dGVfdGljayI6MCwiZGF0YV9oZXgiOiI0MDYwIiwiZGVsdGFfdGlja3MiOjAsImVu"
    "Y29kZWRfYnl0ZXNfaGV4IjoiMDA5MDQwNjAiLCJldmVudF9pbmRleCI6MywibWVzc2FnZV90eXBl"
    "Ijoibm90ZV9vbiIsInN0YXR1cyI6MTQ0LCJ0cmFja19ieXRlX29mZnNldCI6MTUsInRyYWNrX2lu"
    "ZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sIm9uc2V0X3NwZWxsaW5nIjoibm90"
    "ZV9vbl9wb3NpdGl2ZV92ZWxvY2l0eSIsIm9uc2V0X3RpY2siOjAsIm9uc2V0X3RpbWVfbWljcm9z"
    "ZWNvbmRzIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9LCJvbnNldF92ZWxvY2l0eSI6"
    "OTYsInJlbGVhc2VfdGljayI6MTIwLCJyZWxlYXNlX3RpbWVfbWljcm9zZWNvbmRzIjp7ImRlbm9t"
    "aW5hdG9yIjoxLCJudW1lcmF0b3IiOjEyNTAwMH0sInJlbGVhc2VfdmVsb2NpdHkiOjAsInNvdXJj"
    "ZV9taWRpX3NoYTI1NiI6IjU1MjY2MjdjMjg3NjRhMTM1MzQ1NDljNDYzNTNkYzE1ZjY1ZmRlM2Iw"
    "MGU3YjkxZTFjYzRhMWNkMWIzODQ1N2QiLCJzb3VyY2Vfc3BsaXQiOiJ0cmFpbiIsInZlbG9jaXR5"
    "X25vcm1hbGl6ZWRfZXhhY3QiOnsiZGVub21pbmF0b3IiOjEyNywibnVtZXJhdG9yIjo5Nn19\",\"p"
    "rovenance_key\":\"note.0583c7b11456e4720edf5117d3ba7346cdffbda00b28a229a4d4777"
    "5d2c32fed\",\"source_item_keys\":[\"track.0000.event.0003\",\"track.0000.event.000"
    "6\"]},{\"field_statuses\":[[\"midi_clock_onset_offset\",\"present\",null],[\"velocit"
    "y_normalized\",\"present\",null]],\"native_occurrence_sha256\":\"184d3a04871068041"
    "7fa18b7850a6c88ae9741eca1f4c8a2b3d8d1685baef7d4\",\"occurrence_index\":0,\"priva"
    "te_format_id\":\"generated.note-provenance.v1\",\"private_payload_b64\":\"eyJjbG9z"
    "dXJlX3Byb3ZlbmFuY2UiOnsiYWJzb2x1dGVfdGljayI6MTIwLCJkYXRhX2hleCI6IjNjMDAiLCJk"
    "ZWx0YV90aWNrcyI6MCwiZW5jb2RlZF9ieXRlc19oZXgiOiIwMDgwM2MwMCIsImV2ZW50X2luZGV4"
    "Ijo1LCJtZXNzYWdlX3R5cGUiOiJub3RlX29mZiIsInN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29m"
    "ZnNldCI6MjMsInRyYWNrX2luZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sImNs"
    "b3N1cmVfc3BlbGxpbmciOiJub3RlX29mZiIsImdyaWRfaW5kZXgiOjAsImlkZW50aXR5Ijp7ImNo"
    "YW5uZWwiOjAsInBpdGNoIjo2MCwicG9ydCI6MH0sIm1pZGlfY2xvY2tfb25zZXRfb2Zmc2V0X2V4"
    "YWN0Ijp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9LCJub3RlX2lkIjoiMzQwZDhiNmIy"
    "MmFkNzcxNzFlNWVlYzg4NGMwZTYyZWI0YWVjOTg3NWM3MjhiNWE4YmI5ZWMyY2IyYzI3Y2NkMiIs"
    "Im9uc2V0X3Byb3ZlbmFuY2UiOnsiYWJzb2x1dGVfdGljayI6MCwiZGF0YV9oZXgiOiIzYzQwIiwi"
    "ZGVsdGFfdGlja3MiOjAsImVuY29kZWRfYnl0ZXNfaGV4IjoiMDA5MDNjNDAiLCJldmVudF9pbmRl"
    "eCI6MiwibWVzc2FnZV90eXBlIjoibm90ZV9vbiIsInN0YXR1cyI6MTQ0LCJ0cmFja19ieXRlX29m"
    "ZnNldCI6MTEsInRyYWNrX2luZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sIm9u"
    "c2V0X3NwZWxsaW5nIjoibm90ZV9vbl9wb3NpdGl2ZV92ZWxvY2l0eSIsIm9uc2V0X3RpY2siOjAs"
    "Im9uc2V0X3RpbWVfbWljcm9zZWNvbmRzIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9"
    "LCJvbnNldF92ZWxvY2l0eSI6NjQsInJlbGVhc2VfdGljayI6MTIwLCJyZWxlYXNlX3RpbWVfbWlj"
    "cm9zZWNvbmRzIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjEyNTAwMH0sInJlbGVhc2Vf"
    "dmVsb2NpdHkiOjAsInNvdXJjZV9taWRpX3NoYTI1NiI6IjU1MjY2MjdjMjg3NjRhMTM1MzQ1NDlj"
    "NDYzNTNkYzE1ZjY1ZmRlM2IwMGU3YjkxZTFjYzRhMWNkMWIzODQ1N2QiLCJzb3VyY2Vfc3BsaXQi"
    "OiJ0cmFpbiIsInZlbG9jaXR5X25vcm1hbGl6ZWRfZXhhY3QiOnsiZGVub21pbmF0b3IiOjEyNywi"
    "bnVtZXJhdG9yIjo2NH19\",\"provenance_key\":\"note.340d8b6b22ad77171e5eec884c0e62e"
    "b4aec9875c728b5a8bb9ec2cb2c27ccd2\",\"source_item_keys\":[\"track.0000.event.000"
    "2\",\"track.0000.event.0005\"]},{\"field_statuses\":[[\"midi_clock_onset_offset\",\""
    "present\",null],[\"velocity_normalized\",\"present\",null]],\"native_occurrence_sh"
    "a256\":\"9815b8331b21b5c031b759fc60b6d29adfe256bfe66ba99489f8ee78908e8e6c\",\"oc"
    "currence_index\":3,\"private_format_id\":\"generated.note-provenance.v1\",\"privat"
    "e_payload_b64\":\"eyJjbG9zdXJlX3Byb3ZlbmFuY2UiOnsiYWJzb2x1dGVfdGljayI6MjQwLCJk"
    "YXRhX2hleCI6IjQzMDAiLCJkZWx0YV90aWNrcyI6NjAsImVuY29kZWRfYnl0ZXNfaGV4IjoiM2M4"
    "MDQzMDAiLCJldmVudF9pbmRleCI6OCwibWVzc2FnZV90eXBlIjoibm90ZV9vZmYiLCJzdGF0dXMi"
    "OjEyOCwidHJhY2tfYnl0ZV9vZmZzZXQiOjM1LCJ0cmFja19pbmRleCI6MCwidXNlZF9ydW5uaW5n"
    "X3N0YXR1cyI6ZmFsc2V9LCJjbG9zdXJlX3NwZWxsaW5nIjoibm90ZV9vZmYiLCJncmlkX2luZGV4"
    "IjoxLCJpZGVudGl0eSI6eyJjaGFubmVsIjowLCJwaXRjaCI6NjcsInBvcnQiOjB9LCJtaWRpX2Ns"
    "b2NrX29uc2V0X29mZnNldF9leGFjdCI6eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjoxfSwi"
    "bm90ZV9pZCI6Ijc3OGFmZDk5YjA3ZjBlZTA1NmJiMTllMDUxM2VkYWQ1ZTFmYTk5NzMzNGE2NzJm"
    "ZTdiYmU4OGI0NzE5ZDg4ZjkiLCJvbnNldF9wcm92ZW5hbmNlIjp7ImFic29sdXRlX3RpY2siOjE4"
    "MCwiZGF0YV9oZXgiOiI0MzdmIiwiZGVsdGFfdGlja3MiOjYwLCJlbmNvZGVkX2J5dGVzX2hleCI6"
    "IjNjOTA0MzdmIiwiZXZlbnRfaW5kZXgiOjcsIm1lc3NhZ2VfdHlwZSI6Im5vdGVfb24iLCJzdGF0"
    "dXMiOjE0NCwidHJhY2tfYnl0ZV9vZmZzZXQiOjMxLCJ0cmFja19pbmRleCI6MCwidXNlZF9ydW5u"
    "aW5nX3N0YXR1cyI6ZmFsc2V9LCJvbnNldF9zcGVsbGluZyI6Im5vdGVfb25fcG9zaXRpdmVfdmVs"
    "b2NpdHkiLCJvbnNldF90aWNrIjoxODAsIm9uc2V0X3RpbWVfbWljcm9zZWNvbmRzIjp7ImRlbm9t"
    "aW5hdG9yIjoxLCJudW1lcmF0b3IiOjE4NzUwMH0sIm9uc2V0X3ZlbG9jaXR5IjoxMjcsInJlbGVh"
    "c2VfdGljayI6MjQwLCJyZWxlYXNlX3RpbWVfbWljcm9zZWNvbmRzIjp7ImRlbm9taW5hdG9yIjox"
    "LCJudW1lcmF0b3IiOjI1MDAwMH0sInJlbGVhc2VfdmVsb2NpdHkiOjAsInNvdXJjZV9taWRpX3No"
    "YTI1NiI6IjU1MjY2MjdjMjg3NjRhMTM1MzQ1NDljNDYzNTNkYzE1ZjY1ZmRlM2IwMGU3YjkxZTFj"
    "YzRhMWNkMWIzODQ1N2QiLCJzb3VyY2Vfc3BsaXQiOiJ0cmFpbiIsInZlbG9jaXR5X25vcm1hbGl6"
    "ZWRfZXhhY3QiOnsiZGVub21pbmF0b3IiOjEsIm51bWVyYXRvciI6MX19\",\"provenance_key\":\""
    "note.778afd99b07f0ee056bb19e0513edad5e1fa997334a672fe7bbe88b4719d88f9\",\"sour"
    "ce_item_keys\":[\"track.0000.event.0007\",\"track.0000.event.0008\"]},{\"field_sta"
    "tuses\":[[\"midi_clock_onset_offset\",\"present\",null],[\"velocity_normalized\",\"p"
    "resent\",null]],\"native_occurrence_sha256\":\"184d3a048710680417fa18b7850a6c88a"
    "e9741eca1f4c8a2b3d8d1685baef7d4\",\"occurrence_index\":1,\"private_format_id\":\"g"
    "enerated.note-provenance.v1\",\"private_payload_b64\":\"eyJjbG9zdXJlX3Byb3ZlbmFu"
    "Y2UiOnsiYWJzb2x1dGVfdGljayI6MTIwLCJkYXRhX2hleCI6IjNjMDAiLCJkZWx0YV90aWNrcyI6"
    "MTIwLCJlbmNvZGVkX2J5dGVzX2hleCI6Ijc4ODAzYzAwIiwiZXZlbnRfaW5kZXgiOjQsIm1lc3Nh"
    "Z2VfdHlwZSI6Im5vdGVfb2ZmIiwic3RhdHVzIjoxMjgsInRyYWNrX2J5dGVfb2Zmc2V0IjoxOSwi"
    "dHJhY2tfaW5kZXgiOjAsInVzZWRfcnVubmluZ19zdGF0dXMiOmZhbHNlfSwiY2xvc3VyZV9zcGVs"
    "bGluZyI6Im5vdGVfb2ZmIiwiZ3JpZF9pbmRleCI6MCwiaWRlbnRpdHkiOnsiY2hhbm5lbCI6MCwi"
    "cGl0Y2giOjYwLCJwb3J0IjowfSwibWlkaV9jbG9ja19vbnNldF9vZmZzZXRfZXhhY3QiOnsiZGVu"
    "b21pbmF0b3IiOjEsIm51bWVyYXRvciI6MH0sIm5vdGVfaWQiOiJlNjZhODQ2NmEyYjcxOTQ4NDVl"
    "NTljMGE1NmJjNzQ5MTNhN2ZiMjFhOWNiYzc5NmNlZDU0MTc5ZTAwZDQ4ZGJmIiwib25zZXRfcHJv"
    "dmVuYW5jZSI6eyJhYnNvbHV0ZV90aWNrIjowLCJkYXRhX2hleCI6IjNjNDAiLCJkZWx0YV90aWNr"
    "cyI6MCwiZW5jb2RlZF9ieXRlc19oZXgiOiIwMDkwM2M0MCIsImV2ZW50X2luZGV4IjoxLCJtZXNz"
    "YWdlX3R5cGUiOiJub3RlX29uIiwic3RhdHVzIjoxNDQsInRyYWNrX2J5dGVfb2Zmc2V0Ijo3LCJ0"
    "cmFja19pbmRleCI6MCwidXNlZF9ydW5uaW5nX3N0YXR1cyI6ZmFsc2V9LCJvbnNldF9zcGVsbGlu"
    "ZyI6Im5vdGVfb25fcG9zaXRpdmVfdmVsb2NpdHkiLCJvbnNldF90aWNrIjowLCJvbnNldF90aW1l"
    "X21pY3Jvc2Vjb25kcyI6eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjowfSwib25zZXRfdmVs"
    "b2NpdHkiOjY0LCJyZWxlYXNlX3RpY2siOjEyMCwicmVsZWFzZV90aW1lX21pY3Jvc2Vjb25kcyI6"
    "eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjoxMjUwMDB9LCJyZWxlYXNlX3ZlbG9jaXR5Ijow"
    "LCJzb3VyY2VfbWlkaV9zaGEyNTYiOiI1NTI2NjI3YzI4NzY0YTEzNTM0NTQ5YzQ2MzUzZGMxNWY2"
    "NWZkZTNiMDBlN2I5MWUxY2M0YTFjZDFiMzg0NTdkIiwic291cmNlX3NwbGl0IjoidHJhaW4iLCJ2"
    "ZWxvY2l0eV9ub3JtYWxpemVkX2V4YWN0Ijp7ImRlbm9taW5hdG9yIjoxMjcsIm51bWVyYXRvciI6"
    "NjR9fQ==\",\"provenance_key\":\"note.e66a8466a2b7194845e59c0a56bc74913a7fb21a9cb"
    "c796ced54179e00d48dbf\",\"source_item_keys\":[\"track.0000.event.0001\",\"track.00"
    "00.event.0004\"]}],\"reconstruction\":{\"canonical_payload_b64\":\"eyJjb250cm9sbGV"
    "ycyI6W10sImRpYWdub3N0aWNzIjp7Im1hbnVzY3JpcHRfcHJvamVjdGlvbl9hZG1pdHRlZCI6ZmF"
    "sc2UsIm5vdGVfcHJvZHVjaW5nX3N0cmVhbXMiOltbMCwwXV0sIm91dF9vZl84OF9rZXlfbm90ZV9"
    "jb3VudCI6MCwicGl0Y2hfbWF4aW11bSI6NjcsInBpdGNoX21pbmltdW0iOjYwLCJwcm9qZWN0aW9"
    "uX2NvbGxpc2lvbnMiOlt7ImdyaWRfaW5kZXgiOjAsIm5vdGVfaWRzIjpbIjM0MGQ4YjZiMjJhZDc"
    "3MTcxZTVlZWM4ODRjMGU2MmViNGFlYzk4NzVjNzI4YjVhOGJiOWVjMmNiMmMyN2NjZDIiLCJlNjZ"
    "hODQ2NmEyYjcxOTQ4NDVlNTljMGE1NmJjNzQ5MTNhN2ZiMjFhOWNiYzc5NmNlZDU0MTc5ZTAwZDQ"
    "4ZGJmIl0sInBpdGNoIjo2MH1dfSwiZm9ybWF0X3R5cGUiOjAsImdhdGUiOiJtYWVzdHJvLW1pZGk"
    "tY2xvY2stb25zZXQtc2VtYW50aWNzLXYxIiwiZ3JpZF9zcGFjaW5nX3RpY2tzIjoxMjAsIm1pZGl"
    "fcG9ydHMiOltdLCJub3RlcyI6W3siY2xvc3VyZV9wcm92ZW5hbmNlIjp7ImFic29sdXRlX3RpY2s"
    "iOjEyMCwiZGF0YV9oZXgiOiIzYzAwIiwiZGVsdGFfdGlja3MiOjEyMCwiZW5jb2RlZF9ieXRlc19"
    "oZXgiOiI3ODgwM2MwMCIsImV2ZW50X2luZGV4Ijo0LCJtZXNzYWdlX3R5cGUiOiJub3RlX29mZiI"
    "sInN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29mZnNldCI6MTksInRyYWNrX2luZGV4IjowLCJ1c2V"
    "kX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sImNsb3N1cmVfc3BlbGxpbmciOiJub3RlX29mZiIsImd"
    "yaWRfaW5kZXgiOjAsImlkZW50aXR5Ijp7ImNoYW5uZWwiOjAsInBpdGNoIjo2MCwicG9ydCI6MH0"
    "sIm1pZGlfY2xvY2tfb25zZXRfb2Zmc2V0X2V4YWN0Ijp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF"
    "0b3IiOjB9LCJub3RlX2lkIjoiZTY2YTg0NjZhMmI3MTk0ODQ1ZTU5YzBhNTZiYzc0OTEzYTdmYjI"
    "xYTljYmM3OTZjZWQ1NDE3OWUwMGQ0OGRiZiIsIm9uc2V0X3Byb3ZlbmFuY2UiOnsiYWJzb2x1dGV"
    "fdGljayI6MCwiZGF0YV9oZXgiOiIzYzQwIiwiZGVsdGFfdGlja3MiOjAsImVuY29kZWRfYnl0ZXN"
    "faGV4IjoiMDA5MDNjNDAiLCJldmVudF9pbmRleCI6MSwibWVzc2FnZV90eXBlIjoibm90ZV9vbiI"
    "sInN0YXR1cyI6MTQ0LCJ0cmFja19ieXRlX29mZnNldCI6NywidHJhY2tfaW5kZXgiOjAsInVzZWR"
    "fcnVubmluZ19zdGF0dXMiOmZhbHNlfSwib25zZXRfc3BlbGxpbmciOiJub3RlX29uX3Bvc2l0aXZ"
    "lX3ZlbG9jaXR5Iiwib25zZXRfdGljayI6MCwib25zZXRfdGltZV9taWNyb3NlY29uZHMiOnsiZGV"
    "ub21pbmF0b3IiOjEsIm51bWVyYXRvciI6MH0sIm9uc2V0X3ZlbG9jaXR5Ijo2NCwicmVsZWFzZV9"
    "0aWNrIjoxMjAsInJlbGVhc2VfdGltZV9taWNyb3NlY29uZHMiOnsiZGVub21pbmF0b3IiOjEsIm5"
    "1bWVyYXRvciI6MTI1MDAwfSwicmVsZWFzZV92ZWxvY2l0eSI6MCwic291cmNlX21pZGlfc2hhMjU"
    "2IjoiNTUyNjYyN2MyODc2NGExMzUzNDU0OWM0NjM1M2RjMTVmNjVmZGUzYjAwZTdiOTFlMWNjNGE"
    "xY2QxYjM4NDU3ZCIsInNvdXJjZV9zcGxpdCI6InRyYWluIiwidmVsb2NpdHlfbm9ybWFsaXplZF9"
    "leGFjdCI6eyJkZW5vbWluYXRvciI6MTI3LCJudW1lcmF0b3IiOjY0fX0seyJjbG9zdXJlX3Byb3Z"
    "lbmFuY2UiOnsiYWJzb2x1dGVfdGljayI6MTIwLCJkYXRhX2hleCI6IjNjMDAiLCJkZWx0YV90aWN"
    "rcyI6MCwiZW5jb2RlZF9ieXRlc19oZXgiOiIwMDgwM2MwMCIsImV2ZW50X2luZGV4Ijo1LCJtZXN"
    "zYWdlX3R5cGUiOiJub3RlX29mZiIsInN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29mZnNldCI6MjM"
    "sInRyYWNrX2luZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sImNsb3N1cmVfc3B"
    "lbGxpbmciOiJub3RlX29mZiIsImdyaWRfaW5kZXgiOjAsImlkZW50aXR5Ijp7ImNoYW5uZWwiOjA"
    "sInBpdGNoIjo2MCwicG9ydCI6MH0sIm1pZGlfY2xvY2tfb25zZXRfb2Zmc2V0X2V4YWN0Ijp7ImR"
    "lbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9LCJub3RlX2lkIjoiMzQwZDhiNmIyMmFkNzcxNzF"
    "lNWVlYzg4NGMwZTYyZWI0YWVjOTg3NWM3MjhiNWE4YmI5ZWMyY2IyYzI3Y2NkMiIsIm9uc2V0X3B"
    "yb3ZlbmFuY2UiOnsiYWJzb2x1dGVfdGljayI6MCwiZGF0YV9oZXgiOiIzYzQwIiwiZGVsdGFfdGl"
    "ja3MiOjAsImVuY29kZWRfYnl0ZXNfaGV4IjoiMDA5MDNjNDAiLCJldmVudF9pbmRleCI6MiwibWV"
    "zc2FnZV90eXBlIjoibm90ZV9vbiIsInN0YXR1cyI6MTQ0LCJ0cmFja19ieXRlX29mZnNldCI6MTE"
    "sInRyYWNrX2luZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sIm9uc2V0X3NwZWx"
    "saW5nIjoibm90ZV9vbl9wb3NpdGl2ZV92ZWxvY2l0eSIsIm9uc2V0X3RpY2siOjAsIm9uc2V0X3R"
    "pbWVfbWljcm9zZWNvbmRzIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9LCJvbnNldF9"
    "2ZWxvY2l0eSI6NjQsInJlbGVhc2VfdGljayI6MTIwLCJyZWxlYXNlX3RpbWVfbWljcm9zZWNvbmR"
    "zIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjEyNTAwMH0sInJlbGVhc2VfdmVsb2NpdHk"
    "iOjAsInNvdXJjZV9taWRpX3NoYTI1NiI6IjU1MjY2MjdjMjg3NjRhMTM1MzQ1NDljNDYzNTNkYzE"
    "1ZjY1ZmRlM2IwMGU3YjkxZTFjYzRhMWNkMWIzODQ1N2QiLCJzb3VyY2Vfc3BsaXQiOiJ0cmFpbiI"
    "sInZlbG9jaXR5X25vcm1hbGl6ZWRfZXhhY3QiOnsiZGVub21pbmF0b3IiOjEyNywibnVtZXJhdG9"
    "yIjo2NH19LHsiY2xvc3VyZV9wcm92ZW5hbmNlIjp7ImFic29sdXRlX3RpY2siOjEyMCwiZGF0YV9"
    "oZXgiOiI0MDAwIiwiZGVsdGFfdGlja3MiOjAsImVuY29kZWRfYnl0ZXNfaGV4IjoiMDA4MDQwMDA"
    "iLCJldmVudF9pbmRleCI6NiwibWVzc2FnZV90eXBlIjoibm90ZV9vZmYiLCJzdGF0dXMiOjEyOCw"
    "idHJhY2tfYnl0ZV9vZmZzZXQiOjI3LCJ0cmFja19pbmRleCI6MCwidXNlZF9ydW5uaW5nX3N0YXR"
    "1cyI6ZmFsc2V9LCJjbG9zdXJlX3NwZWxsaW5nIjoibm90ZV9vZmYiLCJncmlkX2luZGV4IjowLCJ"
    "pZGVudGl0eSI6eyJjaGFubmVsIjowLCJwaXRjaCI6NjQsInBvcnQiOjB9LCJtaWRpX2Nsb2NrX29"
    "uc2V0X29mZnNldF9leGFjdCI6eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjowfSwibm90ZV9"
    "pZCI6IjA1ODNjN2IxMTQ1NmU0NzIwZWRmNTExN2QzYmE3MzQ2Y2RmZmJkYTAwYjI4YTIyOWE0ZDQ"
    "3Nzc1ZDJjMzJmZWQiLCJvbnNldF9wcm92ZW5hbmNlIjp7ImFic29sdXRlX3RpY2siOjAsImRhdGF"
    "faGV4IjoiNDA2MCIsImRlbHRhX3RpY2tzIjowLCJlbmNvZGVkX2J5dGVzX2hleCI6IjAwOTA0MDY"
    "wIiwiZXZlbnRfaW5kZXgiOjMsIm1lc3NhZ2VfdHlwZSI6Im5vdGVfb24iLCJzdGF0dXMiOjE0NCw"
    "idHJhY2tfYnl0ZV9vZmZzZXQiOjE1LCJ0cmFja19pbmRleCI6MCwidXNlZF9ydW5uaW5nX3N0YXR"
    "1cyI6ZmFsc2V9LCJvbnNldF9zcGVsbGluZyI6Im5vdGVfb25fcG9zaXRpdmVfdmVsb2NpdHkiLCJ"
    "vbnNldF90aWNrIjowLCJvbnNldF90aW1lX21pY3Jvc2Vjb25kcyI6eyJkZW5vbWluYXRvciI6MSw"
    "ibnVtZXJhdG9yIjowfSwib25zZXRfdmVsb2NpdHkiOjk2LCJyZWxlYXNlX3RpY2siOjEyMCwicmV"
    "sZWFzZV90aW1lX21pY3Jvc2Vjb25kcyI6eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjoxMjU"
    "wMDB9LCJyZWxlYXNlX3ZlbG9jaXR5IjowLCJzb3VyY2VfbWlkaV9zaGEyNTYiOiI1NTI2NjI3YzI"
    "4NzY0YTEzNTM0NTQ5YzQ2MzUzZGMxNWY2NWZkZTNiMDBlN2I5MWUxY2M0YTFjZDFiMzg0NTdkIiw"
    "ic291cmNlX3NwbGl0IjoidHJhaW4iLCJ2ZWxvY2l0eV9ub3JtYWxpemVkX2V4YWN0Ijp7ImRlbm9"
    "taW5hdG9yIjoxMjcsIm51bWVyYXRvciI6OTZ9fSx7ImNsb3N1cmVfcHJvdmVuYW5jZSI6eyJhYnN"
    "vbHV0ZV90aWNrIjoyNDAsImRhdGFfaGV4IjoiNDMwMCIsImRlbHRhX3RpY2tzIjo2MCwiZW5jb2R"
    "lZF9ieXRlc19oZXgiOiIzYzgwNDMwMCIsImV2ZW50X2luZGV4Ijo4LCJtZXNzYWdlX3R5cGUiOiJ"
    "ub3RlX29mZiIsInN0YXR1cyI6MTI4LCJ0cmFja19ieXRlX29mZnNldCI6MzUsInRyYWNrX2luZGV"
    "4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sImNsb3N1cmVfc3BlbGxpbmciOiJub3R"
    "lX29mZiIsImdyaWRfaW5kZXgiOjEsImlkZW50aXR5Ijp7ImNoYW5uZWwiOjAsInBpdGNoIjo2Nyw"
    "icG9ydCI6MH0sIm1pZGlfY2xvY2tfb25zZXRfb2Zmc2V0X2V4YWN0Ijp7ImRlbm9taW5hdG9yIjo"
    "xLCJudW1lcmF0b3IiOjF9LCJub3RlX2lkIjoiNzc4YWZkOTliMDdmMGVlMDU2YmIxOWUwNTEzZWR"
    "hZDVlMWZhOTk3MzM0YTY3MmZlN2JiZTg4YjQ3MTlkODhmOSIsIm9uc2V0X3Byb3ZlbmFuY2UiOns"
    "iYWJzb2x1dGVfdGljayI6MTgwLCJkYXRhX2hleCI6IjQzN2YiLCJkZWx0YV90aWNrcyI6NjAsImV"
    "uY29kZWRfYnl0ZXNfaGV4IjoiM2M5MDQzN2YiLCJldmVudF9pbmRleCI6NywibWVzc2FnZV90eXB"
    "lIjoibm90ZV9vbiIsInN0YXR1cyI6MTQ0LCJ0cmFja19ieXRlX29mZnNldCI6MzEsInRyYWNrX2l"
    "uZGV4IjowLCJ1c2VkX3J1bm5pbmdfc3RhdHVzIjpmYWxzZX0sIm9uc2V0X3NwZWxsaW5nIjoibm9"
    "0ZV9vbl9wb3NpdGl2ZV92ZWxvY2l0eSIsIm9uc2V0X3RpY2siOjE4MCwib25zZXRfdGltZV9taWN"
    "yb3NlY29uZHMiOnsiZGVub21pbmF0b3IiOjEsIm51bWVyYXRvciI6MTg3NTAwfSwib25zZXRfdmV"
    "sb2NpdHkiOjEyNywicmVsZWFzZV90aWNrIjoyNDAsInJlbGVhc2VfdGltZV9taWNyb3NlY29uZHM"
    "iOnsiZGVub21pbmF0b3IiOjEsIm51bWVyYXRvciI6MjUwMDAwfSwicmVsZWFzZV92ZWxvY2l0eSI"
    "6MCwic291cmNlX21pZGlfc2hhMjU2IjoiNTUyNjYyN2MyODc2NGExMzUzNDU0OWM0NjM1M2RjMTV"
    "mNjVmZGUzYjAwZTdiOTFlMWNjNGExY2QxYjM4NDU3ZCIsInNvdXJjZV9zcGxpdCI6InRyYWluIiw"
    "idmVsb2NpdHlfbm9ybWFsaXplZF9leGFjdCI6eyJkZW5vbWluYXRvciI6MSwibnVtZXJhdG9yIjo"
    "xfX1dLCJzY2hlbWFfdmVyc2lvbiI6MSwic291cmNlX21pZGlfc2hhMjU2IjoiNTUyNjYyN2MyODc"
    "2NGExMzUzNDU0OWM0NjM1M2RjMTVmNjVmZGUzYjAwZTdiOTFlMWNjNGExY2QxYjM4NDU3ZCIsInN"
    "vdXJjZV9zcGxpdCI6InRyYWluIiwidGVtcG9fbWFwIjp7InBvaW50cyI6W3siZWxhcHNlZF9taWN"
    "yb3NlY29uZHMiOnsiZGVub21pbmF0b3IiOjEsIm51bWVyYXRvciI6MH0sImlzX2ltcGxpY2l0X2R"
    "lZmF1bHQiOmZhbHNlLCJtaWNyb3NlY29uZHNfcGVyX3F1YXJ0ZXJfbm90ZSI6NTAwMDAwLCJzb3V"
    "yY2VfZXZlbnRzIjpbeyJhYnNvbHV0ZV90aWNrIjowLCJkZWx0YV90aWNrcyI6MCwiZW5jb2RlZF9"
    "ieXRlc19oZXgiOiIwMGZmNTEwMzA3YTEyMCIsImV2ZW50X2luZGV4IjowLCJtZXRhX25hbWUiOiJ"
    "zZXRfdGVtcG8iLCJtZXRhX3R5cGUiOjgxLCJwYXlsb2FkX2hleCI6IjA3YTEyMCIsInRyYWNrX2J"
    "5dGVfb2Zmc2V0IjowLCJ0cmFja19pbmRleCI6MH1dLCJ0aWNrIjowfV0sInRpY2tzX3Blcl9xdWF"
    "ydGVyX25vdGUiOjQ4MH0sInRpY2tzX3Blcl9xdWFydGVyX25vdGUiOjQ4MCwidGltZV9zaWduYXR"
    "1cmVzIjpbXX0=\",\"record_count\":4,\"schema_sha256\":\"faca57d5a88ae9c1f11fbc9e38c"
    "162f4b4b36e1a265029c3e4c420bf2894e2ce\",\"semantic_format_id\":\"generated.note-"
    "semantics.v1\"},\"source_b64\":\"TVRoZAAAAAYAAAABAeBNVHJrAAAAKwD/UQMHoSAAkDxAAJA"
    "8QACQQGB4gDwAAIA8AACAQAA8kEN/PIBDAAD/LwA=\",\"source_sha256\":\"5526627c28764a13"
    "534549c46353dc15f65fde3b00e7b91e1cc4a1cd1b38457d\",\"source_size_bytes\":65,\"st"
    "atic_context\":{\"entries\":[[\"tempo-map\",\"eyJwb2ludHMiOlt7ImVsYXBzZWRfbWljcm9z"
    "ZWNvbmRzIjp7ImRlbm9taW5hdG9yIjoxLCJudW1lcmF0b3IiOjB9LCJpc19pbXBsaWNpdF9kZWZh"
    "dWx0IjpmYWxzZSwibWljcm9zZWNvbmRzX3Blcl9xdWFydGVyX25vdGUiOjUwMDAwMCwic291cmNl"
    "X2V2ZW50cyI6W3siYWJzb2x1dGVfdGljayI6MCwiZGVsdGFfdGlja3MiOjAsImVuY29kZWRfYnl0"
    "ZXNfaGV4IjoiMDBmZjUxMDMwN2ExMjAiLCJldmVudF9pbmRleCI6MCwibWV0YV9uYW1lIjoic2V0"
    "X3RlbXBvIiwibWV0YV90eXBlIjo4MSwicGF5bG9hZF9oZXgiOiIwN2ExMjAiLCJ0cmFja19ieXRl"
    "X29mZnNldCI6MCwidHJhY2tfaW5kZXgiOjB9XSwidGljayI6MH1dLCJ0aWNrc19wZXJfcXVhcnRl"
    "cl9ub3RlIjo0ODB9\"]],\"format_id\":\"generated.tempo-map.v1\"}},\"P-ACG-1\":{\"cover"
    "age\":[{\"disposition\":\"excluded_with_reason\",\"exclusion_reason_code\":\"partiti"
    "on-identity\",\"item_key\":\"row.0002\",\"secondary_tags\":[\"private-identity\"],\"ta"
    "rget_key\":null},{\"disposition\":\"static_context\",\"exclusion_reason_code\":null"
    ",\"item_key\":\"row.0003\",\"secondary_tags\":[],\"target_key\":\"context.age\"},{\"dis"
    "position\":\"static_context\",\"exclusion_reason_code\":null,\"item_key\":\"row.0004"
    "\",\"secondary_tags\":[],\"target_key\":\"context.gender\"},{\"disposition\":\"static_"
    "context\",\"exclusion_reason_code\":null,\"item_key\":\"row.0005\",\"secondary_tags\""
    ":[],\"target_key\":\"context.height\"},{\"disposition\":\"static_context\",\"exclusio"
    "n_reason_code\":null,\"item_key\":\"row.0006\",\"secondary_tags\":[],\"target_key\":\""
    "context.icutype\"},{\"disposition\":\"static_context\",\"exclusion_reason_code\":nu"
    "ll,\"item_key\":\"row.0007\",\"secondary_tags\":[],\"target_key\":\"context.weight\"},"
    "{\"disposition\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"r"
    "ow.0008\",\"secondary_tags\":[],\"target_key\":\"occurrence.row.0008\"},{\"dispositi"
    "on\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"row.0009\",\"s"
    "econdary_tags\":[],\"target_key\":\"occurrence.row.0009\"},{\"disposition\":\"event_"
    "occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"row.0010\",\"secondary_ta"
    "gs\":[],\"target_key\":\"occurrence.row.0010\"},{\"disposition\":\"event_occurrence\""
    ",\"exclusion_reason_code\":null,\"item_key\":\"row.0011\",\"secondary_tags\":[],\"tar"
    "get_key\":\"occurrence.row.0011\"},{\"disposition\":\"event_occurrence\",\"exclusion"
    "_reason_code\":null,\"item_key\":\"row.0012\",\"secondary_tags\":[],\"target_key\":\"o"
    "ccurrence.row.0012\"},{\"disposition\":\"event_occurrence\",\"exclusion_reason_cod"
    "e\":null,\"item_key\":\"row.0013\",\"secondary_tags\":[],\"target_key\":\"occurrence.r"
    "ow.0013\"}],\"evaluation_labels\":{\"entries\":[],\"format_id\":\"generated.empty-la"
    "bels.v1\"},\"inventory\":{\"item_format_id\":\"generated.clinical-row.v1\",\"items\":"
    "[[\"row.0002\",\"eyJjZWxscyI6WyIwMDowMCIsIlJlY29yZElEIiwiOTAwMDAxIl0sImVsYXBzZW"
    "RfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjJ9\"],[\"row.0003\",\"eyJjZWxscyI6WyIwMDowMC"
    "IsIkFnZSIsIjU0Il0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjN9\"],[\"row.0"
    "004\",\"eyJjZWxscyI6WyIwMDowMCIsIkdlbmRlciIsIjAiXSwiZWxhcHNlZF9taW51dGVzIjowLC"
    "JsaW5lX251bWJlciI6NH0=\"],[\"row.0005\",\"eyJjZWxscyI6WyIwMDowMCIsIkhlaWdodCIsIi"
    "0xIl0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjV9\"],[\"row.0006\",\"eyJjZW"
    "xscyI6WyIwMDowMCIsIklDVVR5cGUiLCI0Il0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW"
    "1iZXIiOjZ9\"],[\"row.0007\",\"eyJjZWxscyI6WyIwMDowMCIsIldlaWdodCIsIi0xIl0sImVsYX"
    "BzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjd9\"],[\"row.0008\",\"eyJjZWxscyI6WyIwMD"
    "owNSIsIkhSIiwiODAiXSwiZWxhcHNlZF9taW51dGVzIjo1LCJsaW5lX251bWJlciI6OH0=\"],[\"r"
    "ow.0009\",\"eyJjZWxscyI6WyIwMDowNSIsIkhSIiwiODAuMCJdLCJlbGFwc2VkX21pbnV0ZXMiOj"
    "UsImxpbmVfbnVtYmVyIjo5fQ==\"],[\"row.0010\",\"eyJjZWxscyI6WyIwMDowNSIsIlRlbXAiLC"
    "IzNy4wIl0sImVsYXBzZWRfbWludXRlcyI6NSwibGluZV9udW1iZXIiOjEwfQ==\"],[\"row.0011\""
    ",\"eyJjZWxscyI6WyIwMDowNiIsIlVyaW5lIiwiMTIwIl0sImVsYXBzZWRfbWludXRlcyI6NiwibG"
    "luZV9udW1iZXIiOjExfQ==\"],[\"row.0012\",\"eyJjZWxscyI6WyIwMDowNyIsIldlaWdodCIsIj"
    "gxLjUiXSwiZWxhcHNlZF9taW51dGVzIjo3LCJsaW5lX251bWJlciI6MTJ9\"],[\"row.0013\",\"ey"
    "JjZWxscyI6WyIwMDowOCIsIkhSIiwiLTEiXSwiZWxhcHNlZF9taW51dGVzIjo4LCJsaW5lX251bW"
    "JlciI6MTN9\"]]},\"native_observation_sha256\":\"ab6673020b0fe7fdd66f5eafa5b7b822"
    "864213d7c027ce095ba6a5121f1a85fb\",\"policy_sha256\":\"82dc11a52bc22a80a596af34"
    "24c09457e4a92ee53a7c2288ab6db1a0c39e1187\",\"provenance\":[{\"field_statuses\":[[\""
    "value\",\"present\",null]],\"native_occurrence_sha256\":\"98438a4ecb496f4795b592dc"
    "123f30ef4614d3a3d1ac525ebc6c648428ed6d09\",\"occurrence_index\":0,\"private_form"
    "at_id\":\"generated.row-provenance.v1\",\"private_payload_b64\":\"eyJldmVudF9pZCI6"
    "WyJwaHlzaW9uZXQtMjAxMi1yb3ciLCI5MDAwMDEiLDhdLCJyYXdfY2VsbHMiOlsiMDA6MDUiLCJI"
    "UiIsIjgwIl0sInNvdXJjZV9saW5lIjo4LCJ2YWx1ZV9taXNzaW5nIjpmYWxzZX0=\",\"provenanc"
    "e_key\":\"occurrence.row.0008\",\"source_item_keys\":[\"row.0008\"]},{\"field_status"
    "es\":[[\"value\",\"present\",null]],\"native_occurrence_sha256\":\"98438a4ecb496f479"
    "5b592dc123f30ef4614d3a3d1ac525ebc6c648428ed6d09\",\"occurrence_index\":1,\"priva"
    "te_format_id\":\"generated.row-provenance.v1\",\"private_payload_b64\":\"eyJldmVud"
    "F9pZCI6WyJwaHlzaW9uZXQtMjAxMi1yb3ciLCI5MDAwMDEiLDldLCJyYXdfY2VsbHMiOlsiMDA6M"
    "DUiLCJIUiIsIjgwLjAiXSwic291cmNlX2xpbmUiOjksInZhbHVlX21pc3NpbmciOmZhbHNlfQ==\""
    ",\"provenance_key\":\"occurrence.row.0009\",\"source_item_keys\":[\"row.0009\"]},{\"f"
    "ield_statuses\":[[\"value\",\"present\",null]],\"native_occurrence_sha256\":\"a58493"
    "fa5f4a76475eb8804781a3e40278111e02c793a95663d705690306d5e2\",\"occurrence_inde"
    "x\":2,\"private_format_id\":\"generated.row-provenance.v1\",\"private_payload_b64\""
    ":\"eyJldmVudF9pZCI6WyJwaHlzaW9uZXQtMjAxMi1yb3ciLCI5MDAwMDEiLDEwXSwicmF3X2NlbG"
    "xzIjpbIjAwOjA1IiwiVGVtcCIsIjM3LjAiXSwic291cmNlX2xpbmUiOjEwLCJ2YWx1ZV9taXNzaW"
    "5nIjpmYWxzZX0=\",\"provenance_key\":\"occurrence.row.0010\",\"source_item_keys\":[\""
    "row.0010\"]},{\"field_statuses\":[[\"value\",\"present\",null]],\"native_occurrence_"
    "sha256\":\"d93a740bc999b36a8f47755c8def5930a82e5cd23231f2f00d567cef9277b8dd\",\""
    "occurrence_index\":3,\"private_format_id\":\"generated.row-provenance.v1\",\"priva"
    "te_payload_b64\":\"eyJldmVudF9pZCI6WyJwaHlzaW9uZXQtMjAxMi1yb3ciLCI5MDAwMDEiLDE"
    "xXSwicmF3X2NlbGxzIjpbIjAwOjA2IiwiVXJpbmUiLCIxMjAiXSwic291cmNlX2xpbmUiOjExLCJ"
    "2YWx1ZV9taXNzaW5nIjpmYWxzZX0=\",\"provenance_key\":\"occurrence.row.0011\",\"sourc"
    "e_item_keys\":[\"row.0011\"]},{\"field_statuses\":[[\"value\",\"present\",null]],\"nat"
    "ive_occurrence_sha256\":\"954139cc49224d4c66a128f42ed8b9140d5db90b18a46df7851a"
    "f12f1521d840\",\"occurrence_index\":4,\"private_format_id\":\"generated.row-proven"
    "ance.v1\",\"private_payload_b64\":\"eyJldmVudF9pZCI6WyJwaHlzaW9uZXQtMjAxMi1yb3ci"
    "LCI5MDAwMDEiLDEyXSwicmF3X2NlbGxzIjpbIjAwOjA3IiwiV2VpZ2h0IiwiODEuNSJdLCJzb3Vy"
    "Y2VfbGluZSI6MTIsInZhbHVlX21pc3NpbmciOmZhbHNlfQ==\",\"provenance_key\":\"occurren"
    "ce.row.0012\",\"source_item_keys\":[\"row.0012\"]},{\"field_statuses\":[[\"value\",\"s"
    "ource_missing\",null]],\"native_occurrence_sha256\":\"33552800d44a6a924e7921df08"
    "3e24d54267a14116d1f2bbc9c79e5bee51d8fa\",\"occurrence_index\":5,\"private_format"
    "_id\":\"generated.row-provenance.v1\",\"private_payload_b64\":\"eyJldmVudF9pZCI6Wy"
    "JwaHlzaW9uZXQtMjAxMi1yb3ciLCI5MDAwMDEiLDEzXSwicmF3X2NlbGxzIjpbIjAwOjA4IiwiSF"
    "IiLCItMSJdLCJzb3VyY2VfbGluZSI6MTMsInZhbHVlX21pc3NpbmciOnRydWV9\",\"provenance_"
    "key\":\"occurrence.row.0013\",\"source_item_keys\":[\"row.0013\"]}],\"reconstruction"
    "\":{\"canonical_payload_b64\":\"eyJmb3JtYXQiOiJnZW5lcmF0ZWQtY2xpbmljYWwtcm93LXNl"
    "bWFudGljcy12MSIsInJvd3MiOlt7ImNlbGxzIjpbIjAwOjAwIiwiUmVjb3JkSUQiLCI5MDAwMDEi"
    "XSwiZWxhcHNlZF9taW51dGVzIjowLCJsaW5lX251bWJlciI6Mn0seyJjZWxscyI6WyIwMDowMCIs"
    "IkFnZSIsIjU0Il0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjN9LHsiY2VsbHMi"
    "OlsiMDA6MDAiLCJHZW5kZXIiLCIwIl0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIi"
    "OjR9LHsiY2VsbHMiOlsiMDA6MDAiLCJIZWlnaHQiLCItMSJdLCJlbGFwc2VkX21pbnV0ZXMiOjAs"
    "ImxpbmVfbnVtYmVyIjo1fSx7ImNlbGxzIjpbIjAwOjAwIiwiSUNVVHlwZSIsIjQiXSwiZWxhcHNl"
    "ZF9taW51dGVzIjowLCJsaW5lX251bWJlciI6Nn0seyJjZWxscyI6WyIwMDowMCIsIldlaWdodCIs"
    "Ii0xIl0sImVsYXBzZWRfbWludXRlcyI6MCwibGluZV9udW1iZXIiOjd9LHsiY2VsbHMiOlsiMDA6"
    "MDUiLCJIUiIsIjgwIl0sImVsYXBzZWRfbWludXRlcyI6NSwibGluZV9udW1iZXIiOjh9LHsiY2Vs"
    "bHMiOlsiMDA6MDUiLCJIUiIsIjgwLjAiXSwiZWxhcHNlZF9taW51dGVzIjo1LCJsaW5lX251bWJl"
    "ciI6OX0seyJjZWxscyI6WyIwMDowNSIsIlRlbXAiLCIzNy4wIl0sImVsYXBzZWRfbWludXRlcyI6"
    "NSwibGluZV9udW1iZXIiOjEwfSx7ImNlbGxzIjpbIjAwOjA2IiwiVXJpbmUiLCIxMjAiXSwiZWxh"
    "cHNlZF9taW51dGVzIjo2LCJsaW5lX251bWJlciI6MTF9LHsiY2VsbHMiOlsiMDA6MDciLCJXZWln"
    "aHQiLCI4MS41Il0sImVsYXBzZWRfbWludXRlcyI6NywibGluZV9udW1iZXIiOjEyfSx7ImNlbGxz"
    "IjpbIjAwOjA4IiwiSFIiLCItMSJdLCJlbGFwc2VkX21pbnV0ZXMiOjgsImxpbmVfbnVtYmVyIjox"
    "M31dfQ==\",\"record_count\":12,\"schema_sha256\":\"3def77ea09b2fef1f9a1e42416a8f73"
    "e81925e439ded9372e59948558a7aac25\",\"semantic_format_id\":\"generated.clinical-"
    "row-semantics.v1\"},\"source_b64\":\"VGltZSxQYXJhbWV0ZXIsVmFsdWUKMDA6MDAsUmVjb3J"
    "kSUQsOTAwMDAxCjAwOjAwLEFnZSw1NAowMDowMCxHZW5kZXIsMAowMDowMCxIZWlnaHQsLTEKMDA"
    "6MDAsSUNVVHlwZSw0CjAwOjAwLFdlaWdodCwtMQowMDowNSxIUiw4MAowMDowNSxIUiw4MC4wCjA"
    "wOjA1LFRlbXAsMzcuMAowMDowNixVcmluZSwxMjAKMDA6MDcsV2VpZ2h0LDgxLjUKMDA6MDgsSFI"
    "sLTEK\",\"source_sha256\":\"f75b1604bed422d4af8290bb5356ec4212f18c3020d772f70226"
    "11aa9c551ad4\",\"source_size_bytes\":207,\"static_context\":{\"entries\":[[\"context"
    ".age\",\"eyJpc19taXNzaW5nIjpmYWxzZSwicGFyYW1ldGVyIjoiQWdlIiwicmF3X2NlbGxzIjpbI"
    "jAwOjAwIiwiQWdlIiwiNTQiXSwidmFsdWUiOiIweDEuYjAwMDAwMDAwMDAwMHArNSJ9\"],[\"cont"
    "ext.gender\",\"eyJpc19taXNzaW5nIjpmYWxzZSwicGFyYW1ldGVyIjoiR2VuZGVyIiwicmF3X2N"
    "lbGxzIjpbIjAwOjAwIiwiR2VuZGVyIiwiMCJdLCJ2YWx1ZSI6IjB4MC4wcCswIn0=\"],[\"contex"
    "t.height\",\"eyJpc19taXNzaW5nIjp0cnVlLCJwYXJhbWV0ZXIiOiJIZWlnaHQiLCJyYXdfY2Vsb"
    "HMiOlsiMDA6MDAiLCJIZWlnaHQiLCItMSJdLCJ2YWx1ZSI6bnVsbH0=\"],[\"context.icutype\""
    ",\"eyJpc19taXNzaW5nIjpmYWxzZSwicGFyYW1ldGVyIjoiSUNVVHlwZSIsInJhd19jZWxscyI6Wy"
    "IwMDowMCIsIklDVVR5cGUiLCI0Il0sInZhbHVlIjoiMHgxLjAwMDAwMDAwMDAwMDBwKzIifQ==\"]"
    ",[\"context.weight\",\"eyJpc19taXNzaW5nIjp0cnVlLCJwYXJhbWV0ZXIiOiJXZWlnaHQiLCJy"
    "YXdfY2VsbHMiOlsiMDA6MDAiLCJXZWlnaHQiLCItMSJdLCJ2YWx1ZSI6bnVsbH0=\"]],\"format_"
    "id\":\"generated.admission-context.v1\"}},\"R-ACG-1-A\":{\"coverage\":[{\"dispositio"
    "n\":\"event_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"line.0002\",\"s"
    "econdary_tags\":[],\"target_key\":\"occurrence.line.0002\"},{\"disposition\":\"event"
    "_occurrence\",\"exclusion_reason_code\":null,\"item_key\":\"line.0003\",\"secondary_"
    "tags\":[],\"target_key\":\"occurrence.line.0003\"},{\"disposition\":\"event_occurren"
    "ce\",\"exclusion_reason_code\":null,\"item_key\":\"line.0004\",\"secondary_tags\":[],"
    "\"target_key\":\"occurrence.line.0004\"}],\"evaluation_labels\":{\"entries\":[],\"for"
    "mat_id\":\"generated.empty-labels.v1\"},\"inventory\":{\"item_format_id\":\"generate"
    "d.transaction-row.v1\",\"items\":[[\"line.0002\",\"eyJsaW5lX251bWJlciI6MiwicmF3X2N"
    "lbGxzIjpbImludm9pY2UtYSIsImN1c3RvbWVyLXNoYXJlZCIsIjUiLCJza3UtYSIsImFjdGl2ZSI"
    "sIjIiLCIzLjUwIl0sInNlbWFudGljX2ZpZWxkcyI6W1siSW52b2ljZSIsImludm9pY2UtYSJdLFs"
    "iQ3VzdG9tZXIiLCJjdXN0b21lci1zaGFyZWQiXSxbIlRpbWVJbmRleCIsNV0sWyJQcm9kdWN0Iiw"
    "ic2t1LWEiXSxbIkNhbmNlbGxhdGlvbiIsImFjdGl2ZSJdLFsiUXVhbnRpdHkiLCIyIl0sWyJVbml"
    "0UHJpY2UiLCIzLjUiXV19\"],[\"line.0003\",\"eyJsaW5lX251bWJlciI6MywicmF3X2NlbGxzIj"
    "pbImludm9pY2UtYSIsImN1c3RvbWVyLXNoYXJlZCIsIjUiLCJza3UtYSIsImFjdGl2ZSIsIjIiLC"
    "IzLjUwIl0sInNlbWFudGljX2ZpZWxkcyI6W1siSW52b2ljZSIsImludm9pY2UtYSJdLFsiQ3VzdG"
    "9tZXIiLCJjdXN0b21lci1zaGFyZWQiXSxbIlRpbWVJbmRleCIsNV0sWyJQcm9kdWN0Iiwic2t1LW"
    "EiXSxbIkNhbmNlbGxhdGlvbiIsImFjdGl2ZSJdLFsiUXVhbnRpdHkiLCIyIl0sWyJVbml0UHJpY2"
    "UiLCIzLjUiXV19\"],[\"line.0004\",\"eyJsaW5lX251bWJlciI6NCwicmF3X2NlbGxzIjpbImlud"
    "m9pY2UtYSIsImN1c3RvbWVyLXNoYXJlZCIsIjUiLCJza3UtYiIsImNhbmNlbGxlZCIsIjEiLCI0L"
    "jI1Il0sInNlbWFudGljX2ZpZWxkcyI6W1siSW52b2ljZSIsImludm9pY2UtYSJdLFsiQ3VzdG9tZ"
    "XIiLCJjdXN0b21lci1zaGFyZWQiXSxbIlRpbWVJbmRleCIsNV0sWyJQcm9kdWN0Iiwic2t1LWIiX"
    "SxbIkNhbmNlbGxhdGlvbiIsImNhbmNlbGxlZCJdLFsiUXVhbnRpdHkiLCIxIl0sWyJVbml0UHJpY"
    "2UiLCI0LjI1Il1dfQ==\"]]},\"native_observation_sha256\":\"bf820f6e3a83a741107b9f8"
    "252cac0ebc2061af76497656e8ae1838f382b5aae\",\"policy_sha256\":\"ca1c5a66165d704c"
    "671a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49\",\"provenance\":[{\"field_stat"
    "uses\":[[\"quantity\",\"present\",null],[\"unit_price\",\"present\",null]],\"native_oc"
    "currence_sha256\":\"b466ce869c9b0a3ae31f1ea5f7cf5f9fe32104fbde7667234e087dce9a"
    "8e240f\",\"occurrence_index\":0,\"private_format_id\":\"generated.transaction-prov"
    "enance.v1\",\"private_payload_b64\":\"eyJsaW5lX251bWJlciI6MiwicmF3X2NlbGxzIjpbIm"
    "ludm9pY2UtYSIsImN1c3RvbWVyLXNoYXJlZCIsIjUiLCJza3UtYSIsImFjdGl2ZSIsIjIiLCIzLj"
    "UwIl0sInNlbWFudGljX2ZpZWxkcyI6W1siSW52b2ljZSIsImludm9pY2UtYSJdLFsiQ3VzdG9tZX"
    "IiLCJjdXN0b21lci1zaGFyZWQiXSxbIlRpbWVJbmRleCIsNV0sWyJQcm9kdWN0Iiwic2t1LWEiXS"
    "xbIkNhbmNlbGxhdGlvbiIsImFjdGl2ZSJdLFsiUXVhbnRpdHkiLCIyIl0sWyJVbml0UHJpY2UiLC"
    "IzLjUiXV19\",\"provenance_key\":\"occurrence.line.0002\",\"source_item_keys\":[\"lin"
    "e.0002\"]},{\"field_statuses\":[[\"quantity\",\"present\",null],[\"unit_price\",\"pres"
    "ent\",null]],\"native_occurrence_sha256\":\"b466ce869c9b0a3ae31f1ea5f7cf5f9fe321"
    "04fbde7667234e087dce9a8e240f\",\"occurrence_index\":1,\"private_format_id\":\"gene"
    "rated.transaction-provenance.v1\",\"private_payload_b64\":\"eyJsaW5lX251bWJlciI6"
    "MywicmF3X2NlbGxzIjpbImludm9pY2UtYSIsImN1c3RvbWVyLXNoYXJlZCIsIjUiLCJza3UtYSIs"
    "ImFjdGl2ZSIsIjIiLCIzLjUwIl0sInNlbWFudGljX2ZpZWxkcyI6W1siSW52b2ljZSIsImludm9p"
    "Y2UtYSJdLFsiQ3VzdG9tZXIiLCJjdXN0b21lci1zaGFyZWQiXSxbIlRpbWVJbmRleCIsNV0sWyJQ"
    "cm9kdWN0Iiwic2t1LWEiXSxbIkNhbmNlbGxhdGlvbiIsImFjdGl2ZSJdLFsiUXVhbnRpdHkiLCIy"
    "Il0sWyJVbml0UHJpY2UiLCIzLjUiXV19\",\"provenance_key\":\"occurrence.line.0003\",\"s"
    "ource_item_keys\":[\"line.0003\"]},{\"field_statuses\":[[\"quantity\",\"present\",nul"
    "l],[\"unit_price\",\"present\",null]],\"native_occurrence_sha256\":\"d5367b8f629b89"
    "cc61753d2578b4526ce5ea0f8c90b1945170c90be4ff16e3a9\",\"occurrence_index\":2,\"pr"
    "ivate_format_id\":\"generated.transaction-provenance.v1\",\"private_payload_b64\""
    ":\"eyJsaW5lX251bWJlciI6NCwicmF3X2NlbGxzIjpbImludm9pY2UtYSIsImN1c3RvbWVyLXNoYX"
    "JlZCIsIjUiLCJza3UtYiIsImNhbmNlbGxlZCIsIjEiLCI0LjI1Il0sInNlbWFudGljX2ZpZWxkcy"
    "I6W1siSW52b2ljZSIsImludm9pY2UtYSJdLFsiQ3VzdG9tZXIiLCJjdXN0b21lci1zaGFyZWQiXS"
    "xbIlRpbWVJbmRleCIsNV0sWyJQcm9kdWN0Iiwic2t1LWIiXSxbIkNhbmNlbGxhdGlvbiIsImNhbm"
    "NlbGxlZCJdLFsiUXVhbnRpdHkiLCIxIl0sWyJVbml0UHJpY2UiLCI0LjI1Il1dfQ==\",\"provena"
    "nce_key\":\"occurrence.line.0004\",\"source_item_keys\":[\"line.0004\"]}],\"reconstr"
    "uction\":{\"canonical_payload_b64\":\"eyJmb3JtYXQiOiJnZW5lcmF0ZWQtdHJhbnNhY3Rpb2"
    "4tcm93LW11bHRpc2V0LXYxIiwicm93cyI6W1tbIkludm9pY2UiLCJpbnZvaWNlLWEiXSxbIkN1c3"
    "RvbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDVdLFsiUHJvZHVjdCIsInNrdS"
    "1hIl0sWyJDYW5jZWxsYXRpb24iLCJhY3RpdmUiXSxbIlF1YW50aXR5IiwiMiJdLFsiVW5pdFByaW"
    "NlIiwiMy41Il1dLFtbIkludm9pY2UiLCJpbnZvaWNlLWEiXSxbIkN1c3RvbWVyIiwiY3VzdG9tZX"
    "Itc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDVdLFsiUHJvZHVjdCIsInNrdS1hIl0sWyJDYW5jZWxsYX"
    "Rpb24iLCJhY3RpdmUiXSxbIlF1YW50aXR5IiwiMiJdLFsiVW5pdFByaWNlIiwiMy41Il1dLFtbIk"
    "ludm9pY2UiLCJpbnZvaWNlLWEiXSxbIkN1c3RvbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW"
    "1lSW5kZXgiLDVdLFsiUHJvZHVjdCIsInNrdS1iIl0sWyJDYW5jZWxsYXRpb24iLCJjYW5jZWxsZW"
    "QiXSxbIlF1YW50aXR5IiwiMSJdLFsiVW5pdFByaWNlIiwiNC4yNSJdXV19\",\"record_count\":3"
    ",\"schema_sha256\":\"a98b39c8699788c77456bc2da98263f144e9f53addaf929dce96a2e92d"
    "5fff33\",\"semantic_format_id\":\"generated.transaction-multiset.v1\"},\"source_b6"
    "4\":\"SW52b2ljZSxDdXN0b21lcixUaW1lSW5kZXgsUHJvZHVjdCxDYW5jZWxsYXRpb24sUXVhbnRp"
    "dHksVW5pdFByaWNlCmludm9pY2UtYSxjdXN0b21lci1zaGFyZWQsNSxza3UtYSxhY3RpdmUsMiwz"
    "LjUwCmludm9pY2UtYSxjdXN0b21lci1zaGFyZWQsNSxza3UtYSxhY3RpdmUsMiwzLjUwCmludm9p"
    "Y2UtYSxjdXN0b21lci1zaGFyZWQsNSxza3UtYixjYW5jZWxsZWQsMSw0LjI1Cg==\",\"source_sh"
    "a256\":\"9f11c4b120f42df3cf35bd485a405c56dbceba6177911143b452b17932a23584\",\"so"
    "urce_size_bytes\":214,\"static_context\":{\"entries\":[],\"format_id\":\"generated.e"
    "mpty-static.v1\"}},\"R-ACG-1-B\":{\"coverage\":[{\"disposition\":\"event_occurrence\""
    ",\"exclusion_reason_code\":null,\"item_key\":\"line.0002\",\"secondary_tags\":[],\"ta"
    "rget_key\":\"occurrence.line.0002\"},{\"disposition\":\"event_occurrence\",\"exclusi"
    "on_reason_code\":null,\"item_key\":\"line.0003\",\"secondary_tags\":[],\"target_key\""
    ":\"occurrence.line.0003\"}],\"evaluation_labels\":{\"entries\":[],\"format_id\":\"gen"
    "erated.empty-labels.v1\"},\"inventory\":{\"item_format_id\":\"generated.transactio"
    "n-row.v1\",\"items\":[[\"line.0002\",\"eyJsaW5lX251bWJlciI6MiwicmF3X2NlbGxzIjpbIml"
    "udm9pY2UtYiIsImN1c3RvbWVyLXNoYXJlZCIsIjciLCJza3UtYSIsImNhbmNlbGxlZCIsIi0yIiw"
    "iMy41MCJdLCJzZW1hbnRpY19maWVsZHMiOltbIkludm9pY2UiLCJpbnZvaWNlLWIiXSxbIkN1c3R"
    "vbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDddLFsiUHJvZHVjdCIsInNrdS1"
    "hIl0sWyJDYW5jZWxsYXRpb24iLCJjYW5jZWxsZWQiXSxbIlF1YW50aXR5IiwiLTIiXSxbIlVuaXR"
    "QcmljZSIsIjMuNSJdXX0=\"],[\"line.0003\",\"eyJsaW5lX251bWJlciI6MywicmF3X2NlbGxzIj"
    "pbImludm9pY2UtYiIsImN1c3RvbWVyLXNoYXJlZCIsIjciLCJza3UtYiIsImFjdGl2ZSIsIi0xIi"
    "wiNC4yNSJdLCJzZW1hbnRpY19maWVsZHMiOltbIkludm9pY2UiLCJpbnZvaWNlLWIiXSxbIkN1c3"
    "RvbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDddLFsiUHJvZHVjdCIsInNrdS"
    "1iIl0sWyJDYW5jZWxsYXRpb24iLCJhY3RpdmUiXSxbIlF1YW50aXR5IiwiLTEiXSxbIlVuaXRQcm"
    "ljZSIsIjQuMjUiXV19\"]]},\"native_observation_sha256\":\"485a625b6ecd326012ef5b2c"
    "f362f097ddf188e6b784989704695be2f3d201e2\",\"policy_sha256\":\"ca1c5a66165d704c6"
    "71a7206c428f0cbefb9f201c2364f9dc7a812abd11b7d49\",\"provenance\":[{\"field_statu"
    "ses\":[[\"quantity\",\"present\",null],[\"unit_price\",\"present\",null]],\"native_occ"
    "urrence_sha256\":\"29a080cc05ace949c7155dff586512342813938cfe3d214241295326ae9"
    "62553\",\"occurrence_index\":0,\"private_format_id\":\"generated.transaction-prove"
    "nance.v1\",\"private_payload_b64\":\"eyJsaW5lX251bWJlciI6MiwicmF3X2NlbGxzIjpbIml"
    "udm9pY2UtYiIsImN1c3RvbWVyLXNoYXJlZCIsIjciLCJza3UtYSIsImNhbmNlbGxlZCIsIi0yIiw"
    "iMy41MCJdLCJzZW1hbnRpY19maWVsZHMiOltbIkludm9pY2UiLCJpbnZvaWNlLWIiXSxbIkN1c3R"
    "vbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDddLFsiUHJvZHVjdCIsInNrdS1"
    "hIl0sWyJDYW5jZWxsYXRpb24iLCJjYW5jZWxsZWQiXSxbIlF1YW50aXR5IiwiLTIiXSxbIlVuaXR"
    "QcmljZSIsIjMuNSJdXX0=\",\"provenance_key\":\"occurrence.line.0002\",\"source_item_"
    "keys\":[\"line.0002\"]},{\"field_statuses\":[[\"quantity\",\"present\",null],[\"unit_p"
    "rice\",\"present\",null]],\"native_occurrence_sha256\":\"e098cca703ed8d19f58547723"
    "0f0e52e7c83fce045409a47d94a32970e12287c\",\"occurrence_index\":1,\"private_forma"
    "t_id\":\"generated.transaction-provenance.v1\",\"private_payload_b64\":\"eyJsaW5lX"
    "251bWJlciI6MywicmF3X2NlbGxzIjpbImludm9pY2UtYiIsImN1c3RvbWVyLXNoYXJlZCIsIjciL"
    "CJza3UtYiIsImFjdGl2ZSIsIi0xIiwiNC4yNSJdLCJzZW1hbnRpY19maWVsZHMiOltbIkludm9pY"
    "2UiLCJpbnZvaWNlLWIiXSxbIkN1c3RvbWVyIiwiY3VzdG9tZXItc2hhcmVkIl0sWyJUaW1lSW5kZ"
    "XgiLDddLFsiUHJvZHVjdCIsInNrdS1iIl0sWyJDYW5jZWxsYXRpb24iLCJhY3RpdmUiXSxbIlF1Y"
    "W50aXR5IiwiLTEiXSxbIlVuaXRQcmljZSIsIjQuMjUiXV19\",\"provenance_key\":\"occurrenc"
    "e.line.0003\",\"source_item_keys\":[\"line.0003\"]}],\"reconstruction\":{\"canonical"
    "_payload_b64\":\"eyJmb3JtYXQiOiJnZW5lcmF0ZWQtdHJhbnNhY3Rpb24tcm93LW11bHRpc2V0L"
    "XYxIiwicm93cyI6W1tbIkludm9pY2UiLCJpbnZvaWNlLWIiXSxbIkN1c3RvbWVyIiwiY3VzdG9tZ"
    "XItc2hhcmVkIl0sWyJUaW1lSW5kZXgiLDddLFsiUHJvZHVjdCIsInNrdS1hIl0sWyJDYW5jZWxsY"
    "XRpb24iLCJjYW5jZWxsZWQiXSxbIlF1YW50aXR5IiwiLTIiXSxbIlVuaXRQcmljZSIsIjMuNSJdX"
    "SxbWyJJbnZvaWNlIiwiaW52b2ljZS1iIl0sWyJDdXN0b21lciIsImN1c3RvbWVyLXNoYXJlZCJdL"
    "FsiVGltZUluZGV4Iiw3XSxbIlByb2R1Y3QiLCJza3UtYiJdLFsiQ2FuY2VsbGF0aW9uIiwiYWN0a"
    "XZlIl0sWyJRdWFudGl0eSIsIi0xIl0sWyJVbml0UHJpY2UiLCI0LjI1Il1dXX0=\",\"record_cou"
    "nt\":2,\"schema_sha256\":\"a98b39c8699788c77456bc2da98263f144e9f53addaf929dce96a"
    "2e92d5fff33\",\"semantic_format_id\":\"generated.transaction-multiset.v1\"},\"sour"
    "ce_b64\":\"SW52b2ljZSxDdXN0b21lcixUaW1lSW5kZXgsUHJvZHVjdCxDYW5jZWxsYXRpb24sUXV"
    "hbnRpdHksVW5pdFByaWNlCmludm9pY2UtYixjdXN0b21lci1zaGFyZWQsNyxza3UtYSxjYW5jZWx"
    "sZWQsLTIsMy41MAppbnZvaWNlLWIsY3VzdG9tZXItc2hhcmVkLDcsc2t1LWIsYWN0aXZlLC0xLDQ"
    "uMjUK\",\"source_sha256\":\"25dd1cb8c9979c3ea6db4563e171e53c691c00650566b24d8a62"
    "342bc023673d\",\"source_size_bytes\":168,\"static_context\":{\"entries\":[],\"format"
    "_id\":\"generated.empty-static.v1\"}}}"
)


def _decode_base64(value: object, *, name: str) -> bytes:
    if type(value) is not str:
        raise RuntimeError("{} must be exact base64 text".format(name))
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise RuntimeError("{} is not canonical base64".format(name)) from exc
    if base64.b64encode(decoded) != encoded:
        raise RuntimeError("{} is not canonical base64".format(name))
    return decoded


def _load_golden_registry() -> Dict[str, object]:
    try:
        registry = json.loads(_GOLDEN_JSON)
    except (TypeError, ValueError) as exc:  # pragma: no cover - frozen invariant
        raise RuntimeError("generated golden registry is not valid JSON") from exc
    if type(registry) is not dict or set(registry) != set(_POLICY_BY_FAMILY):
        raise RuntimeError("generated golden registry family set changed")
    return registry


def _golden_record(family_id: str) -> Dict[str, object]:
    record = _load_golden_registry().get(family_id)
    if type(record) is not dict:
        raise GeneratedConformanceOracleError(
            "unknown generated family identity"
        )
    return record


def _frozen_source(family_id: str) -> bytes:
    record = _golden_record(family_id)
    source = _decode_base64(
        record.get("source_b64"), name="{} source".format(family_id)
    )
    expected_size = record.get("source_size_bytes")
    expected_sha256 = record.get("source_sha256")
    frozen_size, frozen_sha256 = _SOURCE_IDENTITY_BY_FAMILY[family_id]
    if (
        type(expected_size) is not int
        or isinstance(expected_size, bool)
        or expected_size != frozen_size
        or len(source) != expected_size
        or type(expected_sha256) is not str
        or expected_sha256 != frozen_sha256
        or hashlib.sha256(source).hexdigest() != expected_sha256
    ):
        raise RuntimeError("{} frozen source commitment changed".format(family_id))
    if record.get("policy_sha256") != _POLICY_BY_FAMILY[family_id]:
        raise RuntimeError("{} frozen policy binding changed".format(family_id))
    return source


H_CONT_1_BYTES = _frozen_source(H_FAMILY_ID)
M_ACG_1_BYTES = _frozen_source(M_FAMILY_ID)
P_ACG_1_BYTES = _frozen_source(P_FAMILY_ID)
R_ACG_1_A_BYTES = _frozen_source(R_A_FAMILY_ID)
R_ACG_1_B_BYTES = _frozen_source(R_B_FAMILY_ID)

_SOURCE_BY_FAMILY = MappingProxyType(
    {
        H_FAMILY_ID: H_CONT_1_BYTES,
        M_FAMILY_ID: M_ACG_1_BYTES,
        P_FAMILY_ID: P_ACG_1_BYTES,
        R_A_FAMILY_ID: R_ACG_1_A_BYTES,
        R_B_FAMILY_ID: R_ACG_1_B_BYTES,
    }
)


def _require_exact_source(
    actual: bytes, expected: bytes, family_id: str
) -> None:
    if type(actual) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if actual != expected:
        raise GeneratedConformanceOracleError(
            "{} source bytes differ from the frozen oracle".format(family_id)
        )


def _observed(*field_names: str) -> EventObservation:
    return EventObservation(observed_marks=frozenset(field_names))


def _h_configuration() -> EventConfiguration:
    schema = FeatureSchema(
        event_types=(
            EventTypeSchema(0, "pulse"),
            EventTypeSchema(
                1,
                "signal",
                (
                    ContinuousField(
                        "amplitude",
                        support=SupportKind.BOUNDED,
                        lower=-1.0,
                        upper=1.0,
                    ),
                ),
            ),
            EventTypeSchema(
                2,
                "context",
                (
                    ContinuousField(
                        "confidence",
                        support=SupportKind.BOUNDED,
                        lower=0.0,
                        upper=1.0,
                    ),
                    ContinuousField(
                        "offset",
                        support=SupportKind.BOUNDED,
                        lower=-2.0,
                        upper=2.0,
                    ),
                ),
            ),
        ),
        horizon=5.0,
        time_measure=TimeMeasureKind.CONTINUOUS,
        time_reference=TimeReference.continuous(1.0),
        allow_simultaneous=False,
        version="typed-hawkes-v1",
        multiplicity_mode=MultiplicityMode.SIMPLE,
    )
    events = (
        Event(
            float.fromhex("0x1.cf1855d70ebbcp+0"),
            2,
            {
                "confidence": float.fromhex("0x1.4b1ab6ef864a8p-4"),
                "offset": float.fromhex("0x1.b7babfb741a10p-2"),
            },
            "synthetic-0",
        ),
        Event(
            float.fromhex("0x1.1653623b3be4bp+1"),
            0,
            {},
            "synthetic-1",
        ),
        Event(
            float.fromhex("0x1.3e42787ff2068p+1"),
            2,
            {
                "confidence": float.fromhex("0x1.e89aeef03e002p-2"),
                "offset": float.fromhex("-0x1.1cafef61a3958p-2"),
            },
            "synthetic-2",
        ),
        Event(
            float.fromhex("0x1.dc122584e1c9cp+1"),
            2,
            {
                "confidence": float.fromhex("0x1.6bea1724b70f0p-3"),
                "offset": float.fromhex("0x1.bddb31676cc48p-2"),
            },
            "synthetic-3",
        ),
        Event(
            float.fromhex("0x1.3c7775e58935ep+2"),
            1,
            {"amplitude": float.fromhex("-0x1.77671a63a3994p-1")},
            "synthetic-4",
        ),
    )
    observed = ObservationPattern(
        (
            _observed("confidence", "offset"),
            _observed(),
            _observed("confidence", "offset"),
            _observed("confidence", "offset"),
            _observed("amplitude"),
        ),
        cardinality_observed=True,
    )
    return EventConfiguration(
        schema,
        events,
        observed,
        sample_id=H_EXPECTED_SAMPLE_ID,
        group_id=H_EXPECTED_GROUP_ID,
    )


def _m_configuration() -> EventConfiguration:
    mark_fields = (
        ContinuousField(
            "velocity_normalized",
            support=SupportKind.POSITIVE,
            unit="midi-velocity/127",
        ),
        ContinuousField(
            "midi_clock_onset_offset",
            support=SupportKind.REAL,
            unit="midi-clock-grid-width",
        ),
    )
    schema = FeatureSchema(
        event_types=tuple(
            EventTypeSchema(pitch, "midi_pitch_{}".format(pitch), mark_fields)
            for pitch in range(21, 109)
        ),
        horizon=1.0,
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic((0.0, 1.0), (1.0, 1.0)),
        allow_simultaneous=True,
        version="maestro-midi-clock-counting-fixture-v1",
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
    )
    events = (
        Event(
            0.0,
            60,
            {
                "midi_clock_onset_offset": 0.0,
                "velocity_normalized": float.fromhex("0x1.0204081020408p-1"),
            },
            "e66a8466a2b7194845e59c0a56bc74913a7fb21a9cbc796ced54179e00d48dbf",
        ),
        Event(
            0.0,
            60,
            {
                "midi_clock_onset_offset": 0.0,
                "velocity_normalized": float.fromhex("0x1.0204081020408p-1"),
            },
            "340d8b6b22ad77171e5eec884c0e62eb4aec9875c728b5a8bb9ec2cb2c27ccd2",
        ),
        Event(
            0.0,
            64,
            {
                "midi_clock_onset_offset": 0.0,
                "velocity_normalized": float.fromhex("0x1.83060c183060cp-1"),
            },
            "0583c7b11456e4720edf5117d3ba7346cdffbda00b28a229a4d47775d2c32fed",
        ),
        Event(
            1.0,
            67,
            {
                "midi_clock_onset_offset": 1.0,
                "velocity_normalized": 1.0,
            },
            "778afd99b07f0ee056bb19e0513edad5e1fa997334a672fe7bbe88b4719d88f9",
        ),
    )
    event_observation = _observed(
        "midi_clock_onset_offset", "velocity_normalized"
    )
    return EventConfiguration(
        schema,
        events,
        ObservationPattern((event_observation,) * 4, cardinality_observed=True),
        sample_id=M_EXPECTED_SAMPLE_ID,
        group_id=M_EXPECTED_GROUP_ID,
    )


_P_ATOMS = tuple(float(index) for index in range(2881))
_P_ATOM_WEIGHTS = (1.0,) * len(_P_ATOMS)


def _p_configuration() -> EventConfiguration:
    schema = FeatureSchema(
        event_types=(
            EventTypeSchema(
                0,
                "HR",
                (
                    ContinuousField(
                        "value",
                        support=SupportKind.POSITIVE,
                        unit="beats/minute",
                    ),
                ),
            ),
            EventTypeSchema(
                1,
                "Temp",
                (
                    ContinuousField(
                        "value", support=SupportKind.REAL, unit="degC"
                    ),
                ),
            ),
            EventTypeSchema(
                2,
                "Urine",
                (
                    ContinuousField(
                        "value", support=SupportKind.POSITIVE, unit="mL"
                    ),
                ),
            ),
            EventTypeSchema(
                3,
                "Weight",
                (
                    ContinuousField(
                        "value", support=SupportKind.POSITIVE, unit="kg"
                    ),
                ),
            ),
        ),
        horizon=2880.0,
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic(_P_ATOMS, _P_ATOM_WEIGHTS),
        allow_simultaneous=True,
        version="physionet-2012-counting-fixture-v1",
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
    )
    events = (
        Event(5.0, 0, {"value": 80.0}, ("physionet-2012-row", "900001", 8)),
        Event(5.0, 0, {"value": 80.0}, ("physionet-2012-row", "900001", 9)),
        Event(5.0, 1, {"value": 37.0}, ("physionet-2012-row", "900001", 10)),
        Event(6.0, 2, {"value": 120.0}, ("physionet-2012-row", "900001", 11)),
        Event(7.0, 3, {"value": 81.5}, ("physionet-2012-row", "900001", 12)),
        Event(8.0, 0, {}, ("physionet-2012-row", "900001", 13)),
    )
    return EventConfiguration(
        schema,
        events,
        ObservationPattern(
            (_observed("value"),) * 5 + (_observed(),),
            cardinality_observed=True,
        ),
        sample_id=P_EXPECTED_SAMPLE_ID,
        group_id=P_EXPECTED_GROUP_ID,
    )


def _r_schema() -> FeatureSchema:
    fields = (
        ContinuousField(
            "quantity", support=SupportKind.REAL, unit="item-count"
        ),
        ContinuousField(
            "unit_price",
            support=SupportKind.POSITIVE,
            unit="currency-unit/item",
        ),
    )
    return FeatureSchema(
        event_types=(
            EventTypeSchema(0, "sku-a__active", fields),
            EventTypeSchema(1, "sku-a__cancelled", fields),
            EventTypeSchema(2, "sku-b__active", fields),
            EventTypeSchema(3, "sku-b__cancelled", fields),
        ),
        horizon=7.0,
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic((5.0, 7.0), (1.0, 1.0)),
        allow_simultaneous=True,
        version="generated-transaction-counting-fixture-v1",
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
    )


def _r_configuration(family_id: str) -> EventConfiguration:
    if family_id == R_A_FAMILY_ID:
        source_sha256 = (
            "9f11c4b120f42df3cf35bd485a405c56dbceba6177911143b452b17932a23584"
        )
        sample_id = "invoice-a"
        events = (
            Event(
                5.0,
                0,
                {"quantity": 2.0, "unit_price": 3.5},
                ("generated-transaction-row", source_sha256, 2),
            ),
            Event(
                5.0,
                0,
                {"quantity": 2.0, "unit_price": 3.5},
                ("generated-transaction-row", source_sha256, 3),
            ),
            Event(
                5.0,
                3,
                {"quantity": 1.0, "unit_price": 4.25},
                ("generated-transaction-row", source_sha256, 4),
            ),
        )
    elif family_id == R_B_FAMILY_ID:
        source_sha256 = (
            "25dd1cb8c9979c3ea6db4563e171e53c691c00650566b24d8a62342bc023673d"
        )
        sample_id = "invoice-b"
        events = (
            Event(
                7.0,
                1,
                {"quantity": -2.0, "unit_price": 3.5},
                ("generated-transaction-row", source_sha256, 2),
            ),
            Event(
                7.0,
                2,
                {"quantity": -1.0, "unit_price": 4.25},
                ("generated-transaction-row", source_sha256, 3),
            ),
        )
    else:
        raise GeneratedConformanceOracleError(
            "unknown generated transaction family identity"
        )
    event_observation = _observed("quantity", "unit_price")
    return EventConfiguration(
        _r_schema(),
        events,
        ObservationPattern(
            (event_observation,) * len(events), cardinality_observed=True
        ),
        sample_id=sample_id,
        group_id=R_EXPECTED_GROUP_ID,
    )


def build_generated_expected_configuration(
    family_id: str,
) -> EventConfiguration:
    """Build a fresh literal native configuration for one frozen family."""

    if type(family_id) is not str:
        raise TypeError("family_id must be exact text")
    if family_id == H_FAMILY_ID:
        return _h_configuration()
    if family_id == M_FAMILY_ID:
        return _m_configuration()
    if family_id == P_FAMILY_ID:
        return _p_configuration()
    if family_id in (R_A_FAMILY_ID, R_B_FAMILY_ID):
        return _r_configuration(family_id)
    raise GeneratedConformanceOracleError("unknown generated family identity")


def _string(record: Mapping[str, object], key: str, *, context: str) -> str:
    value = record.get(key)
    if type(value) is not str:
        raise RuntimeError("{} {} must be exact text".format(context, key))
    return value


def _integer(record: Mapping[str, object], key: str, *, context: str) -> int:
    value = record.get(key)
    if type(value) is not int or isinstance(value, bool):
        raise RuntimeError("{} {} must be an exact integer".format(context, key))
    return value


def _mapping(value: object, *, context: str) -> Dict[str, object]:
    if type(value) is not dict:
        raise RuntimeError("{} must be an exact mapping".format(context))
    return value


def _list(value: object, *, context: str) -> list:
    if type(value) is not list:
        raise RuntimeError("{} must be an exact list".format(context))
    return value


def _keyed_payloads(value: object, *, context: str) -> Tuple[Tuple[str, bytes], ...]:
    result = []
    for index, raw_pair in enumerate(_list(value, context=context)):
        pair = _list(raw_pair, context="{}[{}]".format(context, index))
        if len(pair) != 2 or type(pair[0]) is not str:
            raise RuntimeError("{}[{}] is not a keyed payload".format(context, index))
        result.append(
            (
                pair[0],
                _decode_base64(
                    pair[1], name="{}[{}] payload".format(context, index)
                ),
            )
        )
    return tuple(result)


def _build_expected(
    family_id: str, source_bytes: bytes
) -> ExpectedAdapterEvidence:
    record = _golden_record(family_id)
    expected_source = _SOURCE_BY_FAMILY[family_id]
    _require_exact_source(source_bytes, expected_source, family_id)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    policy_sha256 = _POLICY_BY_FAMILY[family_id]

    configuration = build_generated_expected_configuration(family_id)
    native_sha256 = native_observation_digest(configuration)
    if native_sha256 != _string(
        record, "native_observation_sha256", context=family_id
    ):
        raise RuntimeError("{} literal native state changed".format(family_id))

    inventory_record = _mapping(
        record.get("inventory"), context="{} inventory".format(family_id)
    )
    inventory = SourceInventory(
        source_sha256=source_sha256,
        source_size_bytes=len(source_bytes),
        policy_sha256=policy_sha256,
        item_format_id=_string(
            inventory_record, "item_format_id", context="inventory"
        ),
        items=tuple(
            SourceInventoryItem(key, payload)
            for key, payload in _keyed_payloads(
                inventory_record.get("items"), context="inventory items"
            )
        ),
    )

    coverage_entries = []
    for index, raw_entry in enumerate(
        _list(record.get("coverage"), context="coverage")
    ):
        entry = _mapping(raw_entry, context="coverage[{}]".format(index))
        item_key = entry.get("item_key")
        disposition = entry.get("disposition")
        target_key = entry.get("target_key")
        exclusion_reason_code = entry.get("exclusion_reason_code")
        secondary_tags = entry.get("secondary_tags")
        if (
            type(item_key) is not str
            or type(disposition) is not str
            or (target_key is not None and type(target_key) is not str)
            or (
                exclusion_reason_code is not None
                and type(exclusion_reason_code) is not str
            )
            or type(secondary_tags) is not list
            or any(type(tag) is not str for tag in secondary_tags)
        ):
            raise RuntimeError("coverage[{}] has invalid literal types".format(index))
        coverage_entries.append(
            CoverageEntry(
                item_key=item_key,
                disposition=CoverageDisposition(disposition),
                target_key=target_key,
                exclusion_reason_code=exclusion_reason_code,
                secondary_tags=tuple(secondary_tags),
            )
        )
    coverage = SourceCoverageLedger(
        source_sha256=source_sha256,
        source_size_bytes=len(source_bytes),
        policy_sha256=policy_sha256,
        source_inventory_sha256=source_inventory_digest(inventory),
        entries=tuple(coverage_entries),
    )

    static_record = _mapping(
        record.get("static_context"), context="static context"
    )
    static_context = StaticContext(
        source_sha256=source_sha256,
        policy_sha256=policy_sha256,
        format_id=_string(static_record, "format_id", context="static context"),
        entries=tuple(
            StaticContextEntry(key, payload)
            for key, payload in _keyed_payloads(
                static_record.get("entries"), context="static entries"
            )
        ),
    )

    labels_record = _mapping(
        record.get("evaluation_labels"), context="evaluation labels"
    )
    evaluation_labels = EvaluationLabels(
        source_sha256=source_sha256,
        policy_sha256=policy_sha256,
        format_id=_string(
            labels_record, "format_id", context="evaluation labels"
        ),
        entries=tuple(
            EvaluationLabelEntry(key, payload)
            for key, payload in _keyed_payloads(
                labels_record.get("entries"), context="evaluation label entries"
            )
        ),
    )

    occurrence_digests = native_occurrence_digests(configuration)
    provenance_entries = []
    for index, raw_entry in enumerate(
        _list(record.get("provenance"), context="provenance")
    ):
        entry = _mapping(raw_entry, context="provenance[{}]".format(index))
        occurrence_index = _integer(
            entry, "occurrence_index", context="provenance[{}]".format(index)
        )
        if not 0 <= occurrence_index < len(occurrence_digests):
            raise RuntimeError("provenance occurrence index is out of range")
        occurrence_sha256 = occurrence_digests[occurrence_index]
        if occurrence_sha256 != _string(
            entry,
            "native_occurrence_sha256",
            context="provenance[{}]".format(index),
        ):
            raise RuntimeError("{} literal occurrence state changed".format(family_id))
        source_item_keys = _list(
            entry.get("source_item_keys"),
            context="provenance[{}] source keys".format(index),
        )
        if any(type(key) is not str for key in source_item_keys):
            raise RuntimeError("provenance source keys must be exact text")
        field_statuses = []
        for field_index, raw_status in enumerate(
            _list(
                entry.get("field_statuses"),
                context="provenance[{}] field statuses".format(index),
            )
        ):
            status = _list(
                raw_status,
                context="provenance[{}] field status[{}]".format(
                    index, field_index
                ),
            )
            if (
                len(status) != 3
                or type(status[0]) is not str
                or type(status[1]) is not str
                or (status[2] is not None and type(status[2]) is not str)
            ):
                raise RuntimeError("provenance field status literal is invalid")
            field_statuses.append(
                SourceFieldStatus(
                    status[0], SourceValueStatus(status[1]), status[2]
                )
            )
        provenance_entries.append(
            OccurrenceProvenance(
                provenance_key=_string(
                    entry,
                    "provenance_key",
                    context="provenance[{}]".format(index),
                ),
                native_occurrence_sha256=occurrence_sha256,
                source_item_keys=tuple(source_item_keys),
                field_statuses=tuple(field_statuses),
                private_format_id=_string(
                    entry,
                    "private_format_id",
                    context="provenance[{}]".format(index),
                ),
                private_payload_bytes=_decode_base64(
                    entry.get("private_payload_b64"),
                    name="provenance[{}] payload".format(index),
                ),
            )
        )
    provenance = PrivateProvenance(
        source_sha256=source_sha256,
        native_observation_sha256=native_sha256,
        policy_sha256=policy_sha256,
        entries=tuple(provenance_entries),
    )

    reconstruction_record = _mapping(
        record.get("reconstruction"), context="reconstruction"
    )
    schema_sha256 = feature_schema_digest(configuration.schema)
    if schema_sha256 != _string(
        reconstruction_record, "schema_sha256", context="reconstruction"
    ):
        raise RuntimeError("{} literal schema changed".format(family_id))
    reconstruction = SemanticReconstruction(
        source_sha256=source_sha256,
        schema_sha256=schema_sha256,
        policy_sha256=policy_sha256,
        semantic_format_id=_string(
            reconstruction_record,
            "semantic_format_id",
            context="reconstruction",
        ),
        record_count=_integer(
            reconstruction_record, "record_count", context="reconstruction"
        ),
        canonical_payload_bytes=_decode_base64(
            reconstruction_record.get("canonical_payload_b64"),
            name="reconstruction payload",
        ),
    )
    return ExpectedAdapterEvidence(
        native_observation_sha256=native_sha256,
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted_state=None,
        reconstruction=reconstruction,
    )


def build_h_expected_evidence(
    source_bytes: bytes = H_CONT_1_BYTES,
) -> ExpectedAdapterEvidence:
    return _build_expected(H_FAMILY_ID, source_bytes)


def build_m_expected_evidence(
    source_bytes: bytes = M_ACG_1_BYTES,
) -> ExpectedAdapterEvidence:
    return _build_expected(M_FAMILY_ID, source_bytes)


def build_p_expected_evidence(
    source_bytes: bytes = P_ACG_1_BYTES,
) -> ExpectedAdapterEvidence:
    return _build_expected(P_FAMILY_ID, source_bytes)


def build_r_expected_evidence(source_bytes: bytes) -> ExpectedAdapterEvidence:
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if source_bytes == R_ACG_1_A_BYTES:
        return _build_expected(R_A_FAMILY_ID, source_bytes)
    if source_bytes == R_ACG_1_B_BYTES:
        return _build_expected(R_B_FAMILY_ID, source_bytes)
    raise GeneratedConformanceOracleError(
        "R source bytes are outside the frozen oracle set"
    )


def build_r_a_expected_evidence(
    source_bytes: bytes = R_ACG_1_A_BYTES,
) -> ExpectedAdapterEvidence:
    return _build_expected(R_A_FAMILY_ID, source_bytes)


def build_r_b_expected_evidence(
    source_bytes: bytes = R_ACG_1_B_BYTES,
) -> ExpectedAdapterEvidence:
    return _build_expected(R_B_FAMILY_ID, source_bytes)


def build_generated_expected_evidence(
    family_id: str, source_bytes: bytes
) -> ExpectedAdapterEvidence:
    """Dispatch by an independently frozen generated-family identifier."""

    if type(family_id) is not str:
        raise TypeError("family_id must be exact text")
    if family_id not in _SOURCE_BY_FAMILY:
        raise GeneratedConformanceOracleError("unknown generated family identity")
    return _build_expected(family_id, source_bytes)


def build_all_generated_expected_evidence() -> Tuple[ExpectedAdapterEvidence, ...]:
    return (
        build_h_expected_evidence(),
        build_m_expected_evidence(),
        build_p_expected_evidence(),
        build_r_a_expected_evidence(),
        build_r_b_expected_evidence(),
    )


__all__ = [
    "END_OF_STREAM_EXCLUSION_REASON",
    "GeneratedConformanceOracleError",
    "H_FAMILY_ID",
    "H_POLICY_SHA256",
    "M_FAMILY_ID",
    "M_POLICY_SHA256",
    "PARTITION_IDENTITY_EXCLUSION_REASON",
    "P_FAMILY_ID",
    "P_POLICY_SHA256",
    "R_A_FAMILY_ID",
    "R_B_FAMILY_ID",
    "R_POLICY_SHA256",
    "build_all_generated_expected_evidence",
    "build_generated_expected_configuration",
    "build_generated_expected_evidence",
    "build_h_expected_evidence",
    "build_m_expected_evidence",
    "build_p_expected_evidence",
    "build_r_a_expected_evidence",
    "build_r_b_expected_evidence",
    "build_r_expected_evidence",
]
