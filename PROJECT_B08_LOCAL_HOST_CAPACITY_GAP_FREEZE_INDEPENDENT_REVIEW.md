# B08 local-host capacity-gap freeze independent review

**Review decision:** `ACCEPT_EXACT_THREE_FIELD_PARTIAL_B08_FREEZE`  
**Review kind:** internal independent pre-execution policy, custody, and hostile technical review  
**P0/P1/P2:** `0/0/0`  
**B08 status after acceptance:** `OPEN`  
**Institutional, operational, capacity, or execution approval:** no  
**Reviewer identity externally authenticated:** no

## 1. Decision

I independently reopened and reviewed the exact five-file candidate, the live
F150--F162 field roster, the accepted execution preregistration, and all twenty
byte-bound predecessors. I accept only the proposed closures of F153, F158,
and F161. The other ten B08 fields remain open and null, B08 remains open, and
the package creates no runtime, capacity, reservation, science, authority, or
tracker state.

The permissible field delta is exactly:

| Field | Pointer | Accepted value |
|---|---|---|
| `F153` | `/compute_and_fairness_plan/deterministic_settings` | `B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1` |
| `F158` | `/compute_and_fairness_plan/pilot_compute_allocation` | `B08_ZERO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_B07_V1` |
| `F161` | `/compute_and_fairness_plan/failure_reserve` | `B08_ZERO_FAILURE_RESERVE_NO_RERUN_NO_REPLACEMENT_V1` |

There is no permissible blocker, Gate-A item, Formal Test, result,
operational-task, or timetable-checkbox closure. The marked-task count is
unchanged. Only a later authorized tracker/evidence integration may register
the exact three-field delta described in Section 7.

## 2. Exact reviewed bytes

| Artifact | Bytes | Mode / links | Raw SHA-256 |
|---|---:|---:|---|
| `PROJECT_B08_LOCAL_HOST_CAPACITY_GAP_FREEZE.md` | 15,948 | `0644 / 1` | `66b0f9796eb2da7038a4aca7cbadfc449fc1af1eae542601007f7a589c6436e0` |
| `src/heterodiff/experiments/b08_local_host_capacity_gap.py` | 24,128 | `0644 / 1` | `347f2de3008af8df679faad1b275179e6a6b788977d744919f880c58383af499` |
| `research/fixtures/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.json` | 20,982 | `0644 / 1` | `f141e12624f10a13aab61fc034914e3fea5d75bb5f4f49cc4dd723c4fe48eda6` |
| `research/diagnostics/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py` | 36,431 | `0644 / 1` | `74f3b3e82f40eb2ce16ab66181d6a1758f55a499eb4ad1ddc947c7aca0d27881` |
| `tests/unit/test_manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py` | 19,522 | `0644 / 1` | `660a70eb5a15c57d8b4ed835c9d670d954b399b450fc50f6abbdc7353ad74da5` |

The non-machine package aggregate is
`53dbbfb86a90397db06f4502d08701e55580f8319b30841fb32cf4e6ff5552bc`.
The canonical machine semantic digest is
`fa6e67b277ec7dca7ee1222d4bfdf7fe71c20be2841b4c32e69d2d114030bbf0`,
and its supported-projection digest is
`fa9aa9824029a1aa5053de8dd545b6965f56a9d28e3e63920c2f7b7b1778197e`.
The machine record intentionally uses a noncyclic semantic self-binding; this
review supplies the independent raw-byte binding for the exact machine file.

## 3. Contract reconstruction and field audit

The active evidence ledger maps F150--F162 to the thirteen members of
`compute_and_fairness_plan` and shows all thirteen open before this candidate.
The accepted preregistration requires hardware, environment/container,
deterministic settings, ceilings, pilot/tuning/final allocations, failure
reserve, matched compute, complete attempt accounting, and no post-result
top-up. B06 leaves B08 open on exactly four compound requirements:

1. production hardware and runtime identity;
2. F104 calibration weights;
3. scalar plus all eight hard-axis ceiling values; and
4. a capacity reservation/resource receipt.

The candidate truthfully leaves all four requirements unsatisfied. It also
leaves F150--F152, F154--F157, F159--F160, and F162 open and null. Formal Test
28's development capacity schemas do not supply any of those missing facts or
close Formal Test 28.

F153 is an exact prospective policy, not a runtime-success assertion. It
requires CPU-only execution, disables CUDA and MPS as an admissible route,
fixes the listed startup, locale, hash, bytecode, user-site, safe-path, UTF-8,
thread-pool, and torch determinism controls, and terminates pre-execution on an
unsupported or nondeterministic operation. It correctly leaves precision to
F141 and seeds to B07. Its explicit B12 operation-level receipt requirement
prevents the policy from being mistaken for demonstrated production
determinism.

F158 is exactly zero because accepted F131 selects a distribution-free design
with no empirical pilot, while every accepted B06 `PILOT` resource-event cell
is zero. The local synthetic diagnostics are not domain, learner, metric, or
empirical-pilot runs and cannot be transferred or relabeled.

F161 is exactly zero because accepted F148 is
`NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`, no failed row is replaced or retried,
every failed or aborted scheduled attempt is charged to its original
prospective allocation, and post-result top-up is forbidden. This is zero
*extra* reserve; it does not erase failure accounting or imply that a future
scheduled attempt consumes no resources.

## 4. Host observations and nonpromotion boundary

I corroborated the public host facts available at review time: MacBook Pro
`MacBookPro18,1`, Apple M1 Pro arm64, 10 CPU cores split 8 performance / 2
efficiency, 16 GPU cores, 16 GB memory, macOS 26.3.1 build 25D2128, and Darwin
25.3.0. I independently recomputed the current lockfile SHA-256 as
`ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d`
and the project `pyproject.toml` SHA-256 as
`78d8cddc752e6d2d41c6e050132ea71e65fb374a02a6fb00c2cf12ec3ff89fa0`.
The recorded storage arithmetic is exact: 39,564,700 blocks times 1,024 is
40,514,252,800 bytes, while reserved bytes remain zero.

The capture time, private-device preimage, prior installed-distribution state,
and prior PyTorch process state are not externally attested. The package says
so and makes none of them a field-closure premise. The two self-digested
synthetic receipts remain small local observations only: they are not F104
weight calibration, capacity, a deterministic-production receipt, a selected
runtime, or a future-availability guarantee. This boundary is material to the
acceptance.

## 5. Validator, custody, and hostile review

The validator reads the canonical machine record with duplicate-key,
non-finite, non-ASCII, noncanonical, size, mode, hard-link, symlink, and
terminal-line-feed controls before interpreting its projection. It validates
the exact record schema, semantic self-digest, frozen projection, four current
non-machine bindings, and all twenty accepted predecessor bindings. It never
imports or executes the candidate policy source. Instead it pins the source
bytes first and then checks the parsed static effect surface.

The policy module is pure standard-library code. Builders return fresh nested
objects, exact JSON-native-type checks reject Boolean/integer aliases and
container subclasses, receipt validators recompute their noncyclic digests,
and every semantic projection is compared with the frozen exact value. The
validator uses absolute-root, no-follow, stable descriptor reads and rejects
non-regular files, linked files, wrong modes, changing metadata, symlinked
ancestors, and a symlinked project root.

Fresh review-only disposable mutations confirmed refusal of a symlinked path
ancestor, a hard-linked machine record, a hard-linked validator, a coherently
resigned Boolean-for-integer alias in the projection, and a symlinked project
root. The canonical standalone validator passed from an unrelated working
directory under CPython 3.9, 3.11, and 3.14.

## 6. Verification results

- Candidate focused and hostile suite: `66/66` passed.
- Candidate plus the six relevant accepted predecessor suites: `586/586`
  passed (`520` predecessor tests plus the `66` candidate tests).
- CPython 3.9 focused replay: `66/66` passed.
- CPython 3.9, 3.11, and 3.14 standalone unrelated-CWD validation: all passed
  with `PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN`.
- Fresh independent hostile mutations: `5/5` refused as required.

No candidate, predecessor, tracker, evidence-ledger, source under `sources/`,
runtime identity manifest, capacity record, or science artifact was edited by
this review.

## 7. Exact permissible registration delta

If and only if a later authorized integration reopens the exact hashes in
Section 2 and this review, it may register only this delta:

> Close F153, F158, and F161 with the exact values bound above. PRE moves from
> 33 open / 133 closed to 30 open / 136 closed; POST remains 1 open / 5 closed;
> total fields move from 34 open / 138 closed to 31 open / 141 closed. Method,
> runtime, and compute moves from 20 open / 45 closed to 17 open / 48 closed.
> F150--F152, F154--F157, F159--F160, and F162 remain open and null. B08 and
> B12 remain open; blockers remain 7 open / 5 closed; Gate A remains 5/8;
> Formal Test 28 remains OPEN, Formal Test 29 remains OPEN, Formal Test 30
> remains PENDING; all result slots remain unchanged. No timetable checkbox,
> operational task, hardware/runtime selection, capacity reservation, F104
> weight, scalar or hard-axis ceiling, data access, entropy, training,
> inference, science, claim, release, submission, or execution authority is
> created.

That bounded paragraph is prospective integration authority only. This review
does not itself edit the timetable or evidence ledger.
