# A1 R1 activation-preparation V3 live-host rehearsal terminal-failure registration v1

## Outcome

The one authorized canonical V3 live-host environment rehearsal attempt is spent and terminal. The registered state is `R1_A1_ACTIVATION_PREPARATION_V3_REHEARSAL_ATTEMPT_SPENT_TERMINAL_EXIT_70_EMPTY_TOOL_OUTPUT_FIELD_NO_TYPED_RESULT_NO_RETRY_NO_MARKER_NOT_EXECUTABLE`; global state remains `DRAFT_NOT_EXECUTABLE`. The state names only the empty orchestrator tool-output field; it does not claim that operating-system stdout and stderr were separately observed empty.

The canonical parent authority action was invoked exactly once and returned exit code 70 without a typed result. The tool's single `output` field was the empty string and its reported original token count was zero. The tool did not expose separately labeled stdout and stderr observations. Its raw command receipt is not bound as a registered workspace artifact. The reported duration is conservatively registered only as less than 0.01 seconds because an exact wall-time lexeme is not bound here.

This is an additive postmortem with a read-only validator. It does not retry the rehearsal, invoke the V3 authority or child, run a profile probe, create a result, marker, nonce, or preparation root, or alter any frozen V3 or V2 byte. The V3 result, marker, and root remain absent and are required to remain absent and nonreusable. That rule is a registered procedural prohibition, not a claim that future physical absence is mechanically guaranteed. The hostile suite creates, changes, links, removes, and fake-caches only synthetic files inside isolated pytest temporary fixtures to exercise custody rejection; those test writes are noncanonical, nonoperational, and never evidence.

## Frozen V3 predecessor

The six-file rehearsal freeze remains exact:

| Role | Bytes | SHA-256 |
|---|---:|---|
| human freeze | 11,329 | `e4afa4a9c3db43ee7036c0f69ccd12d806a4e41ca7c263e21a4c00c5bba2ce5b` |
| machine freeze | 14,326 | `09b2892d84a446f6057461d562eca9c076491a7a48fe25756b834d9b39f375d1` |
| contracts | 35,283 | `8ea49970e6419ef6851f511f31c88daab4a785cfd4c674700de2449533edb191` |
| read-only supervisor | 55,103 | `24dba07ac156104eec0d06cc95a64fe9470715bdda5f4b57107efe884faad5ec` |
| environment child | 19,530 | `1c4f729d65d585b4c38ae977f0001f97d0e8cbfa23ad566d1e9d999b370eeac6` |
| hostile test | 30,285 | `18305d55f1ef15b9c754223b10ae02f67d56bed44104b967181fdb525e5793f2` |

The frozen V3 machine self-digest is `7b082199634154c23baa341a19c957ea3191298a1d9f3366e00ea57c376a206a`. Its visible-conversation authorization covered this static freeze, one audited read-only rehearsal, and mandatory additive result publication; it excluded any retry, marker, root, nonce, capsule, runtime approval, rank, training, production, or scientific execution.

The registered canonical command is the frozen 16-key `/usr/bin/env -i` profile followed by `.venv-m1/bin/python -P -B -S -X utf8`, the exact supervisor path, and `--rehearse-live-host`. This postmortem binds the frozen command vector and its domain-separated digest. It does not reconstruct a raw command receipt or claim a new invocation.

## Collapsed failure diagnosis

The exact failure stage is unknown. The failed gate, supervisor gate vector, exception class, child-launch count, child exit, and downstream reachability are all unknown. In particular, exit code 70 belongs to the canonical parent action and is not a child exit code.

The frozen parent catches every exception escaping `rehearse_live_host()` and returns 70. Within that function, `_require_live_supervisor_boundary` is the first possible source step, followed by static admission, registration admission, entry-state checks, preflight custody, request construction, child launch or transport, postflight custody, and result construction. With no typed result or bound raw receipt, none of those stages can be selected. The short reported duration is merely consistent with an early failure; it neither localizes the failure nor proves its cause. No Darwin-environment, native-argument, or other deterministic cause is claimed.

No durable V3 operational attempt marker or result was created. Mechanical one-shot enforcement is false, and the absent V3 filesystem is indistinguishable from a true pre-run state to the frozen status implementation. Terminality therefore comes from this additive registration of the orchestrator-reported canonical invocation and the original no-retry authorization, not from a V3 filesystem marker.

## Post-failure exploratory context

Before the no-more-probes boundary was fixed, five separate stdlib-only `python -c` parent-profile processes were run as exploratory implementation context. The process count was initially reported as three, corrected to four, and finally transcript-audited as five. The broad Boolean vector was initially described as 15 fields and corrected to 16. This correction chain is preserved rather than silently normalized.

The implementation transcript reports process exit code zero for each of the five contextual processes. It also reports zero registered authority, runtime-child, or project-module invocations; zero explicit application entropy or network API calls; zero explicit application workspace-output writes; and Boolean-only output containing no raw UID-like value, Darwin-injected value, or absolute path. Operating-system-level entropy, network, and filesystem effects were not independently observed. The commands, process receipts, and raw outputs are not bound as registered workspace artifacts, and neither these reported safety facts, the five-zero vector, nor the probe content is independently verified from durable raw receipts.

The five processes were not direct-file invocations and added no canonical rehearsal attempt or retry. They were not covered by the frozen rehearsal route. No separate exact user authorization is bound or claimed for them. Every row is quarantined: cross-process transfer is forbidden and no row is bound to the canonical failure process. They cannot narrow its stage, gate, child count, or cause.

The closed ordinal roster is:

0. `BROAD_PARENT_PROFILE_BOOLEAN_VECTOR`: all 16 reported Booleans were true, in this exact order: `cpython_3_11_5`, `cwd_matches_expected`, `darwin_arm64`, `darwin_key_present`, `darwin_value_matches_uid`, `effective_environment_count_17`, `gid_egid_equal`, `hash_probe_matches`, `nonroot`, `normalized_environment_exact16`, `process_taint_absent`, `python_flags_exact`, `site_absent`, `supplemental_root_group_absent`, `sys_path_exact`, `uid_euid_equal`.
1. `NATIVE_ARGC_C_MODE_COMBINED_PREFIX_RELATIVE_ARGV0`: the reported C-mode argument count, C-mode token, and payload-presence checks were true; the combined native-prefix and relative-interpreter classifications were false.
2. `NATIVE_FLAGS_ABSOLUTE_SYMLINK_AND_REALPATH_ARGV0`: the reported native flags matched, while both absolute-symlink and realpath interpreter classifications were false.
3. `NATIVE_ARGV0_ALLOWLISTED_EXECUTABLE_AND_BASENAME_CLASSIFICATION`: all eight reported executable, realpath, relative, and basename allowlist classifications were false.
4. `NATIVE_ARGV0_ABSOLUTE_LENGTH_AND_ENV_SHAPE_CLASSIFICATION`: the reported argv0 was absolute; it was not empty, `-c`, `/usr/bin/env`, or an env basename, and its length was not under 64.

The unexpected long absolute argv0 is only a portability hypothesis for a future design. The canonical native-argv gate remains unknown. No further contextual probe is permitted in this milestone.

## Frozen-status defect

Because the V3 result, marker, and root are absent, the frozen status code still projects its pre-run state: `R1_A1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_IMPLEMENTATION_FROZEN_AWAITING_SINGLE_READ_ONLY_REHEARSAL_NO_MARKER_NOT_EXECUTABLE`. This projection is reconstructed from frozen source plus current lstat absences; no separate post-failure status receipt is bound as a registered workspace artifact.

The frozen status cannot represent a consumed attempt that exits without a typed result. Its PRE_RUN projection is therefore a representational defect, not authorization to run again. The attempt count is one, the retry count is zero, and retry remains forbidden.

## Terminal custody and preserved state

The read-only validator reopens every frozen V3 file, the V3 machine self-digest, the exact four-file V2 terminal registration, and the independently validated V2 terminal state:

| V2 terminal-registration role | Bytes | SHA-256 |
|---|---:|---|
| human | 11,507 | `c29302fadc4a5c6a81a963442c85a681c92791ad664482267e80ef6d75f546ed` |
| machine | 17,232 | `bc73165ba905db1f26c5c81e2aebaf644e5e8009bd00daa477469479674d3085` |
| validator | 62,047 | `ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671` |
| hostile test | 19,591 | `7f28086bfeaab835241296961bfc91461789cadce6780ef38009569fd2189d5f` |

The V2 terminal-registration self-digest is `da57dda788f5de2b2a34ed30bdaf7f692db98696a00e420aa0484d44127b6ed0`. Its 2,171-byte attempt marker has raw digest `e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4`. The reopened V2 preparation tree remains exactly 65 regular files and 20 directories, with owner-only `0600` files, file link count one, `0700` directories, and no symlinks. Its capsule remains closed-world at 53 files and 14 directories, with every row reopened twice and inventory digest `c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360`.

The V2 preparation prefix remains at three events with head `4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5`; its capture-A claim remains spent without an A binding, B claim, candidate, approval, or execution authority. No raw runtime envelope or typed terminal ledger event exists, and V2 retry remains forbidden.

The V3 result, marker, and root are lstat-absent. At the stable registration checkpoint, the no-bytecode-cache hygiene gate covers the frozen V3 files and this additive validator and test. The durable loader does not reinterpret later non-evidence cache creation as a new operational attempt.

The frozen V3 state projection remains 172 unresolved nulls, 12 open blockers, and a 550-row D1 quarantine with roster digest `1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14`. Those values are reopened from the frozen registration; this postmortem does not recompute the underlying rosters. D1 and all scientific execution remain inadmissible.

## Next gate and nonclaims

Any future live attempt requires a wholly disjoint V4 package, exact audit, and fresh user authorization. This postmortem deliberately does not freeze exact V4 operational paths or make their future absence a condition of V3 terminal custody; those paths belong to a transition-aware V4 freeze. V4 must bind all four files and the self-digest of this terminal registration, carry V3 attempt count one and retry count zero, and reopen the spent V3 namespace and custody before any V4 authority route. V4 is a new, disjoint-version attempt and can never be represented as a V3 retry.

A V4 design must also disclose the five post-outcome probes as prior knowledge. Before any live supervisor evaluation or child action, it must atomically publish and fsync a fresh, disjoint attempt identity and nonce through an O_EXCL/no-clobber sole-writer ledger or equivalent. If its nonce uses entropy, the durable reservation must precede the sole entropy draw; a partial reservation or post-draw failure is terminally spent. It must preserve a privacy-safe typed supervisor-failure receipt for every prechild failure and durably establish a typed prechild-admission receipt before any child launch. Every typed terminal outcome must be persisted locally without clobber independently of stdout or tool transport, and replay or retry must fail closed. Its outer transport must preserve either typed outcome. V4 is not authorized by this terminal registration.

This registration invokes no V3 operational writer, authority, runtime child, explicit application entropy or network API, rank, training, production, or scientific computation. It creates exactly the four additive registration files and none of the exact V3 operational paths; it defines or claims no exact V4 operational path. It grants no runtime approval, activation, submission, or execution authority.

## Publication and trust boundary

The six-file V3 freeze, this four-file terminal registration, V2 custody, workspace anchor identities, conversation or tool logs, and any future result are internal and publication-excluded. No raw UID, group identity, Darwin-injected value, absolute user path, raw environment, command receipt, or probe output is reproduced here. A publication-safe derivative requires a fresh anonymity audit.

The validator provides procedural honest-host checks. It is not a security sandbox and cannot resist an actor able to mutate registered files, process memory, module globals, native process state, or the Python runtime itself.
