# B08 native Databricks Runtime target successor V2

## State and disposition

**State:** `DRAFT_DATA_FREE_V2_TARGET_SUCCESSOR_ZERO_DELTA`  
**Profile schema:** `heterodiff-b08-databricks-native-runtime-profile-v2`  
**Profile ID:** `b08-databricks-aws-native-dbr17.3-ubuntu24.04.4-linux-x86_64-cpu-py312-v2`

This additive package corrects the prospective native-DBR operating-system
target from Ubuntu `24.04.3 LTS` to Ubuntu `24.04.4 LTS`. The latter is the
release reported by the user's bounded cluster discovery. That report is an
operator input, not an externally authenticated F151 runtime receipt.

The package is a draft construction candidate only. It is not independently
accepted and grants no Databricks, AWS, network, dependency-resolution, data,
calibration, training, inference, scientific-execution, closure, or tracker
authority.

## Preservation and exact successor delta

Every reviewed V1 file remains unchanged. V2 cryptographically identifies the
following exact predecessor:

- V1 profile source SHA-256:
  `a9258e63a4dc45822ce4d67b2535c5d22dcb9dad14323c00fbc01cfc366a9004`;
- V1 canonical template file SHA-256:
  `2e05801bf65ede62b2c318ba82a6d4f35aa9191b64a4ac24608fda05df071a91`;
- V1 template semantic record SHA-256:
  `e2bd94423e9049a612ec865087e25c71c8711dccc0cda500979b387875cc79e5`;
  and
- V1 independent-review SHA-256:
  `09deb7b2144e948c3b5b6a6010ec78904dfe3dd71da0889a8cfd4d8c59e3e81f`.

Relative to the V1 semantic record, V2 changes exactly:

1. schema identity from V1 to V2;
2. profile identity to the V2 ID above;
3. record-digest domain from `/v1` to `/v2`;
4. canonical template path to the versioned V2 path; and
5. `/target/operating_system_release` from `24.04.3 LTS` to
   `24.04.4 LTS`.

The profile filename itself is not a machine-record field. Every other record
value projects exactly onto the reviewed V1 record. V2 retains the same DBR
17.3 LTS, AWS classic dedicated single-node, Standard engine, non-ML,
Photon-disabled, x86_64, CPython-3.12, CPU-only target family.

## Exact V2 artifacts

- pure profile wrapper:
  `src/heterodiff/experiments/b08_databricks_native_runtime_profile_v2.py`;
- canonical unresolved template:
  `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile-v2.template.json`;
- focused tests:
  `tests/unit/test_b08_databricks_native_runtime_profile_v2.py`; and
- this zero-delta successor record.

The V2 template semantic record SHA-256 is
`d5994e8158737b2d1cbd369b347698e131256639b93e5a33ac1ba7ee49c098c3`.
Its canonical file SHA-256 is
`4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6`.

## Inherited unresolved evidence and safety boundary

The F152 path and expected top-level distributions are unchanged:

- `heterodiff==0.1.0`;
- `numpy==2.4.6`;
- `scipy==1.17.1`;
- `threadpoolctl==3.6.0`; and
- `torch==2.12.1+cpu`.

The lock remains absent and unresolved. Complete transitive-lock closure and
artifact/payload closure remain false. All 15 F153 requested environment values
remain exact, including an exactly present empty `CUDA_VISIBLE_DEVICES`, but
effective whole-runtime satisfaction and every-process/worker equivalence
remain false and unresolved.

The declared Ubuntu `24.04.4 LTS` target is still prospective. The unresolved
roster continues to include `/target/operating_system_release`; only a later
coherent external capture and independent review may establish its operational
identity. Installed-payload closure, module-distribution ownership, PyTorch
deterministic runtime state, source/runtime attestation, capacity, storage
reservation, calibration, and every scientific fact remain absent.

Every safety-boundary value remains false, including network/contact, study or
test data, calibration, training/inference, scientific execution, field or
blocker closure, B08 closure, and tracker/timetable editing.

## Zero-delta consequence

This construction creates no timetable, field, blocker, Formal-Test, result,
runtime, data, capacity, science, or claim transition. B08 and Wave 2 remain
open. F151 and F152 remain open and null. F153 retains only its previously
accepted prospective-policy status; this V2 package does not establish its
effective runtime satisfaction.

The existing README, completion timetable, evidence ledger, V1 package, and V1
independent review are deliberately not edited by this construction.

## Next eligible action

An independent reviewer must verify the final V2 bytes, predecessor hashes,
canonical/semantic digests, exact V1 projection, hostile fail-closed behavior,
and zero-delta boundary. Only after that review may a separately versioned
Databricks discovery notebook bind the V2 template file and semantic hashes.
Notebook review does not itself authorize an operational attempt.
