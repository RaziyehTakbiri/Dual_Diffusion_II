# Finite-A1 development checkpoint freeze

**Lane:** `A1-DEV-GUIDED-1729-N32768-V1`  
**State:** `FROZEN_EXECUTION_AUTHORIZED`  
**Checkpoint execution authorized now:** yes, for this development lane only  
**Confirmatory execution authorized:** no  
**Scientific-result or claim effect:** none

## 1. Purpose and boundary

This freeze selects exactly one learned residual checkpoint from the already
preregistered finite-A1 training protocol. Its only purpose is to exercise the
learned-checkpoint and association-path evaluation interfaces with a genuine
optimizer-produced model. It is a development artifact, not an execution of
`R1-A1`, `R2-HYBRID`, `R3-PHYS`, or `R4-RETAIL`.

The lane cannot qualify a known-law gate, promote C17 or any other manuscript
claim, enter a production aggregate or candidate decision, authorize access to
real-domain test data, or change the manuscript-v3 confirmatory state. The
publication preregistration retains all `174` existing `null` fields and all
`12` unresolved blockers.

This document now hash-binds the audited development-only runner, its hostile
test, the final source manifest, and the training configuration. It authorizes
exactly the frozen development attempt. No optimizer permit exists until the
bound runner completes its fresh preflight, copies and seals the source
capsule, confirms both reserved production roots are absent, and durably issues
the single-use permit inside that capsule record.

## 2. Frozen coordinate

The sole coordinate is:

| Field | Frozen value |
|---|---:|
| method | `guided` |
| paired seed | `1729` |
| accepted-example budget | `32768` |
| optimizer updates | `3000` |
| batch size | `128` |

The method is the association-aware guide plus one shared scalar residual. The
seed is the first value in the preregistered seed registry. The maximum frozen
sample budget is selected before any learner outcome because it produces the
most useful development checkpoint without increasing the frozen 3,000-update
optimizer schedule.

There is exactly one attempt. A failure, nonfinite result, certificate refusal,
runtime mismatch, timeout, interruption after custody begins, or malformed
receipt does not activate another seed, budget, method, restart, or checkpoint.

The development process has a `3600`-second wall timeout, a maximum recorded
peak resident-set size of `8,589,934,592` bytes (8 GiB), and a maximum complete
capsule/output size of `2,147,483,648` bytes (2 GiB). These are operational
development ceilings, not scientific acceptance thresholds or compute-fairness
evidence. Exceeding any ceiling yields `REFUSED` or `FAILURE` and no checkpoint
claim; it does not permit a retry or a smaller substitute coordinate.

## 3. Frozen finite subject

The lane uses the finite-A1 production fixture identified by
`0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc`.
The locally rebuilt Python-3.9 compatibility token is not admissible.

The subject has horizon `T=1`, cap `3`, `20` capped three-type count states,
and `21` observations: all count observations through cardinality three plus
overflow. The reporting grid is `t_j=j/32`, `j=0,...,32`. Birth rates are
`(0.38, 0.30, 0.24)`, per-occurrence death rates are
`(0.28, 0.34, 0.25)`, and the row-source/column-destination replacement matrix
is

```text
[[0,    0.16, 0.07],
 [0.11, 0,    0.15],
 [0.09, 0.13, 0   ]]
```

The initial capped-factorial parameter is `(0.65, 0.50, 0.40)`. Detection is
`(0.72, 0.63, 0.68)`, observation clutter is `(0.10, 0.08, 0.12)`, the
observation reference is uniform on 21 outcomes, and whole-observation
contamination is `0.08`. The exact confusion matrix and all split, association,
overflow, feature, and target/reference conventions are inherited without
alteration from the hash-bound A1 specification.

## 4. Frozen learner and optimizer

The correction network is `21 -> 32 -> 32 -> 1` with SiLU activations and
`1,793` binary64 trainable parameters. It uses the preregistered bounded map
`2048*tanh(u/2048)` and the guided composition rule. All 21 observations share
one checkpoint.

Training uses deterministic CPU AdamW with:

- initial learning rate `1e-3` and final learning rate `1e-5`;
- the exact preregistered cosine schedule over 3,000 updates;
- betas `(0.9, 0.999)`, epsilon `1e-8`, and weight decay `1e-6`;
- batch size `128` and gradient-norm clipping at `1`; and
- the final update as the sole checkpoint.

There is no validation selection, early stopping, tuning trial, warm start,
checkpoint tie, or experiment-level optional stopping. Data, model, and batch
streams retain the three-child `SeedSequence(1729).spawn(3)` custody, NumPy
`PCG64` sampling, generator-driven Xavier initialization, zero biases, and the
preregistered nested sample construction.

## 5. Frozen runtime contract

The required target is macOS 14 or later on untranslated arm64 CPython 3.11.5,
with NumPy 2.4.6, SciPy 1.17.1, CPU-only PyTorch 2.12.1, and threadpoolctl
3.6.0. Accelerators are hidden, deterministic PyTorch algorithms are enabled,
and every discovered numerical pool plus PyTorch intra-op and inter-op
execution uses one thread. `PYTHONHASHSEED=0`.

The environment lock is
`requirements/m1-reference-macos-arm64-py311.lock`, SHA-256
`ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d`.
The A1 scientific specification is
`research/62_a1_association_guided_residual_falsification_spec.md`, SHA-256
`475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c`.

The target `.venv-m1` environment is installed and has been checked as
native arm64 CPython 3.11.5 with NumPy 2.4.6, SciPy 1.17.1, CPU-only PyTorch
2.12.1, threadpoolctl 3.6.0, and one discovered native pool using one thread.
That installation check is not the fresh development-runtime observation. The
authorized runner must recapture and bind that observation before it can issue
the dynamic optimizer permit. Source imports are fixed to `PYTHONPATH=src`,
and every capsule Python process uses safe-path mode (`-P` and
`PYTHONSAFEPATH=1`). The capsule also disables bytecode writes
(`PYTHONDONTWRITEBYTECODE=1`) so post-run evidence can be inventoried byte for
byte.

The formal production runtime-identity approval is still absent. This
development lane neither requires nor supplies that production approval, and
its runtime observation cannot be reused as formal production authority. No
local compatibility calculation may be relabeled as the target-runtime
checkpoint.

## 6. Capsule and acceptance contract

The expected development capsule root is
`artifacts/manuscript_v3_a1_development_checkpoint_v1`. It must be absent
before execution and must not be redirected to either
`artifacts/a1_campaign_v4` or
`artifacts/a1_finite_association_production_order_v1`.

A checkpoint exists only if a later receipt binds all of the following:

1. the exact production fixture token and five prerequisite content digests;
2. the final source manifest and training-configuration digests;
3. the attested target-runtime observation;
4. the single coordinate and its preflight, data, schedule, initial-parameter,
   launch, worker-session, and exactly-once run identities;
5. exactly 3,000 optimizer updates and the complete rolling transcript;
6. an immutable final-update snapshot whose continuous correction certificate
   passes with certified maximum absolute correction at most `20`;
7. reopened checkpoint bytes and matching parameter, classifier, certificate,
   checkpoint, and completion-receipt digests; and
8. a durable `SUCCESS` state followed by a parent-confirmed zero child exit.

Until those conditions hold, every execution and result field in the machine
freeze remains pending. A later development checkpoint and diagnostic must
remain ineligible for production campaign admission, R1/R2 qualification,
confirmatory inference, or claim promotion.

## 7. Frozen implementation binding

The implementation is frozen to:

- runner `src/heterodiff/experiments/finite_association_development_checkpoint_runner.py`,
  SHA-256 `bd493e39c097ee6f0befc78cec57a7d17c76c8ed6fbc0167c77fce3bd56084d9`;
- hostile test `tests/unit/test_finite_association_development_checkpoint_runner.py`,
  SHA-256 `535abf37475213218465214ba49932454bfb19c5e5ea33f26aff06ad92022e89`;
- training-source manifest
  `474fefc6dc06fb8d513e3848308e9e68a5ab86b13f2e5ba4442e362d19239379`;
  and
- training configuration
  `db230ee90fa963941132c48f87be760662eaf0f229d13fdd7483cb6ef4ca74cf`.

The exact launch is
`PYTHONPATH=src .venv-m1/bin/python -P -m heterodiff.experiments.finite_association_development_checkpoint_runner --execute-development-checkpoint`.
The matching `--status` operation reopens the capsule, source manifest,
runtime preflight, permit, attempt, complete artifact inventory, inner SUCCESS
ledger, and checkpoint bytes before reporting success. It also reopens the
retained exact authorized machine-freeze bytes and bound hostile-test bytes,
rather than relying on their digests alone. These bindings authorize no
production-order transition and no confirmatory or manuscript claim.

The optimizer child is held behind a fail-closed pipe gate. It cannot enter
the learner module until the parent has durably recorded the PID-linked permit
consumption. Constructor interruption closes the gate and forces an EOF exit;
an interruption after process return but before that record kills and reaps
the child. Those terminal-only paths cannot yield a checkpoint or a retry,
although they may lack a completed PID-linked consumption record.
