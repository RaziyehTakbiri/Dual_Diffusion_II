# Independent hostile review: B08 native AWS Databricks runtime successor v1

## Review disposition

**`GO_NATIVE_DBR_N0_CONSTRUCTION_READINESS_ZERO_DELTA`.** The stabilized
package is accepted only as the bounded, offline Stage-N0 construction
contract for the prospective native-Databricks-Runtime route.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project delta: **zero**
- B08 and Wave 2 remain `OPEN`.
- F151 and F152 remain `OPEN` and null.
- F153 retains its previously accepted policy value; this package does not
  claim effective whole-runtime F153 satisfaction.
- Formal Tests 28 and 29 remain `OPEN`; Formal Test 30 remains `PENDING`.

This disposition is not authority for network access, dependency resolution,
Databricks or AWS operations, data access, calibration, training, inference,
scientific execution, field or blocker closure, or a timetable transition.

## Final bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1.md` | 17,648 | `d02ce3e1d8bc5d6fb10b98cca0d5fab4771ad0079acd0aa0e59ce1b9684a3601` |
| `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile.template.json` | 4,314 | `2e05801bf65ede62b2c318ba82a6d4f35aa9191b64a4ac24608fda05df071a91` |
| `src/heterodiff/experiments/b08_databricks_native_runtime_profile.py` | 22,082 | `a9258e63a4dc45822ce4d67b2535c5d22dcb9dad14323c00fbc01cfc366a9004` |
| `research/diagnostics/b08_databricks_native_runtime_capture_v1.py` | 44,785 | `bb0895bc1e1947ad9b6b5f831e408e6a5835fbccec8917ac25efc83ef2f1e168` |
| `tests/unit/test_b08_databricks_native_runtime_profile.py` | 7,444 | `c11016c49f9d6ebaa793457a27ff77c717a0b6d37fc8b70582c6094a40f9101c` |
| `tests/unit/test_b08_databricks_native_runtime_capture_v1.py` | 22,103 | `7332b4ea7e118ba4515ab3a96ceecca16be6d07b49ed5efe9498c5c34950b3d9` |

The canonical template independently reproduced its domain-separated semantic
digest as
`e2bd94423e9049a612ec865087e25c71c8711dccc0cda500979b387875cc79e5`.
The checked-in template is byte-canonical and exactly equals
`build_draft_profile()`.

## Commands and results

The final bytes were exercised with the following checks.

```text
/Users/mahtab/opt/anaconda3/bin/python -m pytest -q \
  tests/unit/test_b08_databricks_native_runtime_profile.py \
  tests/unit/test_b08_databricks_native_runtime_capture_v1.py
```

Result: **44 passed**.

The same focused suite was then run from `/private/tmp` with absolute test and
source paths and an absolute `PYTHONPATH`. Result: **44 passed**.

```text
/Users/mahtab/opt/anaconda3/bin/python -m pytest -q \
  tests/unit/test_b08_databricks_aws_job_lifecycle.py \
  tests/unit/test_b08_databricks_aws_qualification.py \
  tests/unit/test_b08_databricks_aws_qualification_capture_v1.py \
  tests/unit/test_b08_databricks_container_package.py \
  tests/unit/test_b08_databricks_runtime_profile.py \
  tests/unit/test_b08_wave2_capacity_preflight.py \
  tests/unit/test_manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py \
  tests/unit/test_manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py
```

Result: **293 passed**.

`python -m pyflakes` over the two native sources and two focused tests and
`git diff --check` over all six reviewed files both exited zero with no output.
The only pytest diagnostics were cache-write warnings caused by the repository's
read-only cache location; they did not affect collection or execution.

## Independent hostile reproduction

The pre-stabilization attacks were recreated independently against the final
bytes rather than inferred from the focused tests.

1. A self-redigested combined forgery with false F152 completeness and artifact
   closure, a substituted requirement roster, fabricated runtime/ABI/package/
   module bodies, and a valid outer digest failed closed. Dedicated hostile
   cases also rejected each F152 false claim before current-state acceptance.
2. A self-redigested requirement-count/hash-count substitution failed with
   `RECEIPT_F152_LOCK_BINDING_MISMATCH`; the receipt roster must equal the exact
   parser result from the currently bound lock bytes.
3. Uppercase or otherwise malformed source revision and manifest literals
   failed before receipt admission with `SOURCE_REVISION_INVALID` or
   `SOURCE_MANIFEST_SHA256_INVALID`.
4. Re-digested runtime, ABI, distribution-metadata, module-origin, payload-
   closure, module-ownership, and F153-effectiveness substitutions all failed
   either their exact nested schema/semantic validator or the recomputed
   current-state equality check.
5. A resolved parent-directory symlink into a forbidden output root failed.
   Pre-existing output symlinks were not followed or clobbered.
6. Symlinked, hardlinked, non-owner, and non-`0600` receipt candidates fail
   custody admission. Descriptor identity, regular-file status, owner, mode,
   single-link count, bounded size, and before/after stability are checked.
7. An independent write probe observed fsync calls for both the receipt file
   and its parent directory. The created file was mode `0600`, owner-matched,
   and single-linked. No-follow and no-clobber flags are used on the target.

The original combined probe's final outcomes included:

```text
combined_redigested_forgery=REJECTED
invalid_source_literals=SOURCE_REVISION_INVALID
lock_observation_substitution=RECEIPT_F152_LOCK_BINDING_MISMATCH
world_writable_receipt=RECEIPT_MODE_NOT_PRIVATE_0600
hardlinked_receipt=RECEIPT_HARDLINK_FORBIDDEN
symlink_receipt=RECEIPT_SYMLINK_FORBIDDEN
output_symlink_no_clobber=OUTPUT_NO_CLOBBER; target unchanged
resolved_forbidden_alias=REJECTED
```

No previously reported semantic or custody bypass remained reproducible.

## Scientific and operational boundary audit

The selected route has no custom-container, container-registry, private-ECR,
or image-pull-instance-profile dependency. Historical Docker/ECR artifacts and
no-go records remain unchanged; their route-specific obligations are
superseded/not applicable, not completed.

The profile and capture helper are explicit about the evidence they do not
establish:

- the named F152 lock file is absent, so the draft remains
  `DRAFT_UNRESOLVED_F152_LOCK`;
- complete transitive dependency closure and artifact/payload closure are
  `false` and unresolved;
- installed-distribution entries are metadata observations, not payload
  closure;
- module paths and hashes are origin observations, not proof of distribution
  ownership or shadow exclusion;
- the ten policy/provider/runtime target paths not observable by this helper
  remain in the exact unresolved roster;
- PyTorch deterministic-algorithm state, warning mode, intra/inter-operation
  thread settings, cuDNN state, CUDA/MPS operational disablement, effective
  F153 satisfaction, and every-process/worker equivalence are explicitly
  unobserved or `false`; and
- source identity and runtime observations remain externally unauthenticated
  and unattested.

An observation-bound profile remains in
`OBSERVED_REVIEW_PENDING_NO_AUTHORITY`, retains fifteen unresolved paths, and
keeps `eligible_for_scientific_execution=false`. Its remaining paths comprise
the two F152 closure predicates, three effective-runtime/F153/worker predicates,
and ten target paths.

Static inspection and the import-deny test found no Databricks API, Spark,
network, subprocess, entropy, NumPy, SciPy, Torch, dataset, model, calibration,
training, inference, or outcome execution path. The helper reads only the exact
profile and lock plus local runtime/package metadata and module-origin bytes,
then writes one private no-clobber candidate receipt.

## Documentation, link, and tracker audit

All six local links in the governance successor resolve, as do all four native-
package links added to the timetable and evidence ledger. The independently
recounted authoritative state remains:

- marked tasks: 62 checked / 101 open / 163 total;
- PRE fields: 23 open / 143 closed;
- POST fields: 1 open / 5 closed;
- all fields: 24 open / 148 closed;
- blockers: 7 open / 5 closed;
- B08: `OPEN`;
- F151/F152: `OPEN`;
- F153: `CLOSED` only as the previously accepted prospective policy; and
- Formal Tests 28/29/30: `OPEN` / `OPEN` / `PENDING`.

The review did not edit either tracker. Capacity, physical storage reservation,
availability, exact hardware, F104 calibration, resource ceilings, tuning/final
allocations, total compute ceiling, B08, and Wave 2 all remain open.

## Final findings and closure decision

| Priority | Open | Final result |
|---|---:|---|
| P0 | 0 | No critical correctness, safety, or authority-boundary defect found. |
| P1 | 0 | The prior re-digested semantic-forgery and receipt-custody bypasses are remediated and independently rejected. |
| P2 | 0 | Nested schema/equality, unresolved-claim labeling, link, and unrelated-working-directory checks pass. |

The package may be retained as an independently reviewed N0 construction-
readiness control only. The next eligible work remains the separately governed
N1 administrator inputs and exact F152 native-lock construction/review. No
later stage may use this review as runtime qualification, capacity proof,
calibration evidence, scientific authority, or B08 closure.
