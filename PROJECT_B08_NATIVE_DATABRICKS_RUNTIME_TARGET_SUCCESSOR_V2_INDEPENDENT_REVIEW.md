# Independent hostile review: B08 native Databricks Runtime target successor V2

## Review disposition

**`PASS_NATIVE_DBR_V2_TARGET_SUCCESSOR_ZERO_DELTA`.** The additive V2
successor is accepted only as a prospective, data-free correction of the
native-Databricks-Runtime target from Ubuntu `24.04.3 LTS` to Ubuntu
`24.04.4 LTS`.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project, field, blocker, result, and timetable delta: **zero**
- B08 and Wave 2 remain `OPEN`.
- F151 and F152 remain `OPEN` and null.
- F153 retains only its previously accepted prospective-policy status.

This review grants no Databricks, AWS, network, dependency-resolution,
package-installation, runtime-capture, data, calibration, training, inference,
scientific-execution, field-closure, blocker-closure, B08-closure, or tracker
authority.

## Exact V2 identity accepted

| Identity | Exact value |
|---|---|
| Profile path | `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile-v2.template.json` |
| Schema | `heterodiff-b08-databricks-native-runtime-profile-v2` |
| Profile ID | `b08-databricks-aws-native-dbr17.3-ubuntu24.04.4-linux-x86_64-cpu-py312-v2` |
| Record-digest domain | `heterodiff/b08/databricks-native-runtime-profile/v2\0` |
| Target operating-system release | `24.04.4 LTS` |
| Canonical template file SHA-256 | `4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6` |
| Domain-separated semantic SHA-256 | `d5994e8158737b2d1cbd369b347698e131256639b93e5a33ac1ba7ee49c098c3` |

The template is exact canonical ASCII JSON followed by one terminal LF. An
independent implementation removed `record_sha256`, canonicalized the remaining
record with sorted keys and compact separators, prepended the exact V2 domain
bytes including the terminal NUL, and reproduced the semantic digest above.

## Final V2 bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_SUCCESSOR_V2.md` | 4,771 | `eb5e4d2d6a83baf194d379bd4d40ad3aba441f73401250f1970261d92d09c35d` |
| `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile-v2.template.json` | 4,331 | `4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6` |
| `src/heterodiff/experiments/b08_databricks_native_runtime_profile_v2.py` | 14,694 | `10a7ccd40ec7a9c8df22699fc5399521a3c91d2ee8c23f41306a71184c7556bd` |
| `tests/unit/test_b08_databricks_native_runtime_profile_v2.py` | 9,096 | `40237298f7e9b6f89b484afa9445528ada1c793a713d083230a0a5fe3f782b9a` |

## V1 byte preservation and exact projection

All six files accepted by the V1 independent review remain byte-exact:

| V1 file | SHA-256 |
|---|---|
| `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1.md` | `d02ce3e1d8bc5d6fb10b98cca0d5fab4771ad0079acd0aa0e59ce1b9684a3601` |
| `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile.template.json` | `2e05801bf65ede62b2c318ba82a6d4f35aa9191b64a4ac24608fda05df071a91` |
| `src/heterodiff/experiments/b08_databricks_native_runtime_profile.py` | `a9258e63a4dc45822ce4d67b2535c5d22dcb9dad14323c00fbc01cfc366a9004` |
| `research/diagnostics/b08_databricks_native_runtime_capture_v1.py` | `bb0895bc1e1947ad9b6b5f831e408e6a5835fbccec8917ac25efc83ef2f1e168` |
| `tests/unit/test_b08_databricks_native_runtime_profile.py` | `c11016c49f9d6ebaa793457a27ff77c717a0b6d37fc8b70582c6094a40f9101c` |
| `tests/unit/test_b08_databricks_native_runtime_capture_v1.py` | `7332b4ea7e118ba4515ab3a96ceecca16be6d07b49ed5efe9498c5c34950b3d9` |

An independent flattened-record comparison found exactly four differing
machine-record leaves between the canonical V1 and V2 drafts:

1. `/schema_version` changes from the V1 identity to the V2 identity;
2. `/profile_id` changes to the V2 profile ID;
3. `/target/operating_system_release` changes from `24.04.3 LTS` to
   `24.04.4 LTS`; and
4. `/record_sha256` changes as the necessary consequence of the new identity,
   operating-system value, and `/v2` digest domain.

The profile path is not a machine-record field. The versioned path and the
digest domain are exact V2 module constants. Projecting V2 back to the V1
schema, profile identity, operating-system release, and digest domain produces
the exact V1 draft. The same exact projection holds for the bounded
`OBSERVED_REVIEW_PENDING` state.

Every other value is inherited exactly, including the F152 path and expected
distribution roster, all fifteen F153 environment values, unresolved paths,
runtime bindings, lifecycle behavior, and all-false safety boundary.

## Focused and hostile verification

The final V2 focused suite passed from the repository root:

```text
28 passed in 0.10s
```

The same exact suite passed from an unrelated `/private/tmp` working directory
with absolute source and test paths:

```text
28 passed in 0.10s
```

The V1 profile and capture regressions plus the V2 focused suite passed
together:

```text
72 passed in 0.26s
```

An additional independent 28-case self-redigested hostile matrix attempted to
change platform identity, operating-system identity, native-route restrictions,
F152 completeness, artifact and installed-payload closure, module ownership,
F153 effectiveness, process/worker equivalence, external authentication or
attestation, scientific eligibility, and every operational or scientific
authority flag. All 28 cases failed closed; none was accepted.

Dedicated focused cases also reject V1/V2 cross-acceptance, wrong schema or
profile identity, old or malformed operating-system releases, GPU or ML-runtime
substitution, unknown keys, noncanonical types, invalid digests, and
self-redigested closure or authority claims. The V2 module is standard-library
only apart from importing the pure reviewed V1 profile module. Static import and
call-surface inspection found no file, environment, network, subprocess, Spark,
Databricks, entropy, data, model, calibration, training, inference, or outcome
operation. `pyflakes` and `git diff --check` completed with no findings.

## Zero-delta scientific and operational boundary

The canonical V2 draft retains all of the following exact states:

- F152 SHA-256 is null and its lock remains absent;
- complete transitive-lock and artifact closure are false;
- installed-payload closure and module-distribution ownership are false;
- F153 effective-runtime satisfaction and every-process/worker equivalence are
  false;
- eligibility for scientific execution is false;
- eligibility for data-free independent review is false in the unresolved
  canonical draft; and
- every safety-boundary value is false.

Ubuntu `24.04.4 LTS` remains a prospective target value derived from the
operator-provided bounded discovery output. It is not an externally
authenticated runtime receipt, F151 evidence, F152 closure, capacity or storage
evidence, or scientific-execution readiness.

No V2 identity was inserted into the README, completion timetable, or evidence
ledger by this construction or review. No completed task, field, blocker,
Formal Test, B08 state, or Wave-2 state changes.

## Narrow next eligible action

The only newly eligible action is the **additive offline construction and
independent review** of one separately versioned Databricks source notebook for
a V2-bound isolated overlay/F152-lock candidate. That notebook must bind all of
the following before it can itself be reviewed:

- the exact V2 profile path, schema, profile ID, digest domain, canonical file
  SHA-256, and semantic SHA-256 accepted above;
- the discovered DBR 17.3 / CPython 3.12 / x86-64 native package mismatch;
- isolation from the mutable DBR base environment;
- exact package/artifact hashes and a fail-closed candidate-lock output; and
- explicit absence of study/test data, calibration, training, inference,
  result inspection, and tracker authority.

This review does **not** authorize executing that notebook, resolving or
installing dependencies, contacting a package index, publishing a lock,
capturing a runtime, launching a replacement attempt, or performing any
scientific operation. Those require a separately reviewed package and the
applicable explicit authority.

## Final finding

No critical, major, or minor correctness, projection, canonicalization,
fail-closed, or authority-boundary defect remains in the reviewed V2 package.
It may be retained as the exact zero-delta Ubuntu-24.04.4 target successor and
as an input to the narrowly bounded notebook-construction step above only.
