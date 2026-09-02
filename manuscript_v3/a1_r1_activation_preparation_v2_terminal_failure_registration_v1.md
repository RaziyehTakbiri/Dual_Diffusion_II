# A1 R1 activation-preparation v2 terminal-failure registration v1

## Outcome

The authorized A1 R1 activation-preparation v2 attempt is spent and terminal. The exact state is
`A1_R1_ACTIVATION_PREPARATION_V2_ATTEMPT_SPENT_TERMINAL_RUNTIME_CAPTURE_A_CHILD_FAILED_NO_BINDING_NO_RETRY`.
The source capsule was materialized and admitted for preparation custody only, then the first runtime-inspection child failed closed after its durable A-launch claim and before any A binding. The v2 attempt must not be retried, repaired, resumed, deleted, replaced, or reinterpreted as an execution authorization.

This is an additive, read-only forensic registration. It does not change any frozen v2 file, marker, ledger record, capsule byte, source byte, runtime file, or historical artifact. The machine sidecar and independent validator bind and reopen the exact terminal custody described here.

## Frozen predecessor

The postmortem binds all six frozen v2 files without modification:

| Role | Bytes | SHA-256 |
|---|---:|---|
| human freeze | 10,686 | `b6893f6870e913633d186812690d4fc1b836dfe740f28588f3266cca4b5f8d28` |
| machine freeze | 46,331 | `b80fd02cb15dc7b5b051678af940c05dbc043992bbe1daee35ddc00dfe51f305` |
| contracts module | 19,039 | `ee18bf3a1b6daf09717bae3960c1c1649b64da03985ee5ea4cc5d44c1267414d` |
| authority module | 143,460 | `2bd8f1dd450f2ddf9fd16b1c20dc865ff2bb219ca7f675262508356cbd7fa28e` |
| runtime-inspection oracle | 45,459 | `59c3f08bd88b376d4a1bbadcd095c024e94c69ab0fe75029a069255998d11097` |
| hostile test | 47,279 | `176ef2e220bf37f3cd493ef91f436266030c6d28b5d72c09bc7d116ac4da11c8` |

The frozen machine record self-digest is `7ef6ec8e5c61f254277730a9879e89e6ef8be43d917eb9adc0bcc747b1e74f0e`; its static qualification snapshot is `d2931175f4ccd7ed7dbaf6d656ab0fa6e39b37809500ed7ab9f39a0977237964`.

## Authorization custody

The marker binds the pre-registered full authorization context: “I authorize the irreversible A1 R1 activation-preparation v2 sequence: its one-shot marker, deterministic source-capsule materialization, and exactly two privacy-safe runtime inspections; this does not authorize runtime approval, rank, training, production, scientific execution, claim promotion, or activation.” Its domain-separated digest is `d1a7808a81a67b5969f949c59c337d40f48b2b5a47e92d445c40a7f2f4718cda`.

The user then assented exactly: “Yes, authorize the V2 preparation attempt.” The sidecar binds that visible text after NFC normalization and removal only of trailing ASCII space, tab, carriage return, and line feed. No raw user-message envelope is bound as a registered workspace artifact; its provenance is the conversation-visible text registered here. The authorization did not include runtime approval, rank, training, production, scientific execution, claim promotion, submission, or activation.

## Exact terminal custody

Every record below is canonical ASCII JSON with a trailing line feed, mode `0600`, link count one, a regular nonsymlink inode, an exact raw digest, and a valid schema-specific self-digest.

| Role | Raw SHA-256 | Record SHA-256 |
|---|---|---|
| attempt marker | `e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4` | `e9cc86c08ab20b44fee62c0bd8476d08130b059c826eb820c4924be3d2e16f45` |
| ledger genesis | `1ea198cbedfcebb557f7ad872d4e1a49003d39aa007c8a4bdb1b752df0c53779` | `6b7267d63ad7842a89dca1b5d99340933a7df3300fd727076bc142c6767afc69` |
| event-0 nonce claim | `64fca0f0cb7b22d674ac581d47decb58c37d78a8e5c7a9106b495c923d23862d` | `5cff31b87b27dbb83f8aa474fc36d613b3a57e22b36d07919e6caddc56a518ff` |
| event 0, capsule opened | `3910afb3a96e1da2510bf32a45fd5929a3307fff145e0ffbb847718afcca6301` | `9409499d860d4b6b2d909b3480be19053ed5af97f4bcbf9bf6f8f9815bcfb2bd` |
| source-capsule manifest | `29bd8aba8cfaf85ed5c542293f703f4e0ac08ff51596c5edca208e02e934084f` | `77576eaf4c6c741c7ac2c9de467c2a6b33ca52c7b021144f41e146622d856702` |
| event-1 nonce claim | `7b0e164c1963c816a850673c78b33b93596fc395edd0a5d4939bbe3b3cc11f7d` | `768c1f8661e1c889e6e55704d0056fb14f07b16ef6f756471f58af51f3f6a230` |
| event 1, capsule admitted | `f31b4805efcd74af94d87e38a9217ce1d6c8301bba808e5a5604c27127bbfb4c` | `2cd92a085303f6f41d53aa849f9a9c38299a049d6910eabbbbeaa47bd2d1d60f` |
| source-capsule admission | `e7d88bd02ffa2f29b4f70368f0de27c3cf8ede73512b8cfd36dc76d30eec06cf` | `3f4c41adeb59b74461218fc23155584618d4c24c8db10a9a87d8d334bf6e5834` |
| event-2 nonce claim | `a611905e2fd6e591790607bcb0e52bc5d61c6e1c7b7f6feaa0a1cedec80c9d51` | `6d106204929efef19a9ee1e76d2c76feb9acbb6a672055cfaad204f91789ed50` |
| event 2, double capture opened | `2e138e029fb19e06db466adb32c8d31deca2783b8a576c848ed42f62019d0e0f` | `4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5` |
| runtime double-capture request | `a4b5850d1bded22be30e7d93eed3396a8b2478fd6ae6dd7fc3e1538349016d4b` | `a6453702e03a9f01c6b3544a387491bd41f904af3eb2161821d36753de608b87` |
| runtime capture-A launch claim | `d9f7a0d343604ab5171bbc592b21f0eb4b0a97ea5b3fa2103c6b854493ba16af` | `6140a49e94c472fcd75d6ccfb55d4de0030190b39d57b2e59ebcd9c49fc7eda4` |

The independently validated ledger prefix contains events 0, 1, and 2 and ends at head `4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5`. The admitted capsule remains a closed 53-file, 14-directory, owner-only tree with inventory digest `c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360`. The whole current preparation tree is exactly 65 files and 20 directories. Capsule admission is preparation custody only and is not execution admission.

The capture-A claim is terminally spent under `LAUNCH_SPENT_NO_RECAPTURE`. There is no A binding, B launch claim, B binding, runtime candidate, raw capture envelope, review, approval, final runtime manifest, scientific campaign nonce, or typed terminal ledger event. Event-3 and event-4 nonce claims and event records are absent. The runtime-candidate directory is empty. Terminality is therefore derived from the spent A claim without its binding and is registered here rather than represented by a v2 event-3 record.

## Failure diagnosis

The canonical runtime-candidate action exited with code 1 after approximately 1.99 seconds. The parent reported `_execute_runtime_at_root` → `_run_runtime_child` → `PreparationAuthorityError("runtime capture child failed closed")`. It did not report timeout or size overflow. The v2 parent intentionally neither persisted nor surfaced the child’s stderr, so this postmortem does not claim a verbatim child traceback.

A read-only, non-oracle profile probe using the same replacement environment, interpreter, and isolation flags deterministically reproduced the first failing condition. The frozen policy requested exactly `LANG=C`, `LC_ALL=C`, and `PYTHONHASHSEED=0`; on this pinned Darwin framework-Python profile, the equivalent probe’s effective interpreter environment also contained the macOS-injected `__CF_USER_TEXT_ENCODING` entry. Frozen control flow makes the exact environment comparison the deterministic inferred failure: the runtime’s first capture check requires dictionary equality and therefore raises `runtime child environment is not exact` before capsule, installed-file, or distribution scanning.

All other pre-capture profile checks matched: isolated flags, the virtual-environment executable, framework interpreter realpath, isolated standard-library path, CPython 3.11, Darwin, and arm64. Because downstream checks were not reached, this registration does not claim that no additional downstream defect exists.

Within the workspace registration, the exact effective value of the injected entry appears only in the machine sidecar, read-only validator, and hostile test. Internal conversation or tool logs may also retain it. Every workspace carrier and internal log is publication-excluded. The value is UID-like and publication-unsafe. This prose and any future public derivative use the token `<DARWIN_USER_TEXT_ENCODING>` instead. A future disjoint v3 design must derive the expected Darwin value from `os.getuid()`—not `os.geteuid()`—and must distinguish the requested launch environment from the effective interpreter environment.

## Status and frozen-test defects

The v2 public status reports `PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID` and correctly preserves the spent, closed, retry-forbidden, and execution-unauthorized booleans. The reason label is a generic exception fallback, not a precise finding that the independently reopened prefix or capsule custody is invalid. That fallback also reports `preparation_event_count=0`, collapsing the valid three-event prefix. The v2 status is therefore lossy and is not a complete forensic receipt.

The frozen hostile test is also not durably transition-aware despite the human freeze’s claim. Two exact tests fail after the legitimate marker transition:

- `test_owned_paths_are_exactly_additive_and_no_operational_output_exists`, defined at line 314, first fails at line 316 because it unconditionally requires the canonical marker to be absent.
- `test_status_is_zero_write_transition_aware_and_initially_awaiting_authorization`, defined at line 401, first fails at line 415 because it unconditionally requires the initial awaiting-authorization status object.

The orchestrator-reported targeted post-transition result is two selected, zero passed, two failed, exit code 1. No raw pytest receipt was bound as a registered workspace artifact. The validator independently reopens both failure conditions from the exact frozen test and current terminal state. The frozen test bytes remain immutable; this registration records the defect rather than editing history.

## Nonclaims and next gate

This postmortem invoked no v2 writer, entropy call, runtime oracle, runtime child, network contact, retry, repair, deletion, or replacement. It created no capture binding or candidate and performed no runtime approval, rank, training, production, scientific execution, result selection, claim promotion, or submission action. The frozen v2 static snapshot is reopened and still projects 172 unresolved nulls and 12 open blockers. It projects a 550-row D1 quarantine with roster digest `1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14`; D1 remains execution-inadmissible. This postmortem does not freshly recompute the underlying blocker, null, or D1 rosters. Global state remains `DRAFT_NOT_EXECUTABLE`.

Any future preparation attempt requires a wholly disjoint v3 namespace and fresh explicit authorization. Before an irreversible v3 marker, that milestone must run an audited, read-only, non-oracle launch-profile preflight; freeze requested-versus-effective Darwin environment semantics; preserve the v2 terminal tree byte-for-byte; and use canonical tests that branch over every permitted live state instead of asserting only pre-marker absence. Nothing in this registration authorizes v3, runtime approval, rank, training, production, or science.

## Publication and trust boundary

This registration, its sidecar, and all raw v2 custody are internal preregistration evidence. They are excluded from anonymous submission and public release. A publication-safe derivative must omit or tokenize UID-like environment data and pass a fresh anonymity audit. The validator supplies procedural honest-host custody checks; it is not a sandbox and does not resist an actor who can mutate same-process memory, module globals, native process state, or registered files.
