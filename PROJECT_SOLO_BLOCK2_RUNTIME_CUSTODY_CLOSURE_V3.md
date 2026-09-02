# Solo Block 2 offline resolver and row-link repair closure v3

**Package state:** `FINAL_V3_ENUM_AND_ROW1_LINK_REPAIR_QUALIFIED_NO_OPERATIONAL_ROOT_NO_FETCH_HOLD`  
**Reported date:** `2026-08-31`  
**V3 operational root:** absent  
**V3 resolver, socket, TLS, HTTP, receipt, intent, tracker, or scientific effect:** zero

## 1. Additive candidate only

This six-file package is an offline, additive repair candidate. It does not
edit, replace, retry, resume, delete, or reinterpret the locked v1 or v2
packages or either operational custody root. It creates no v3 operational
root, package lock, preflight, GO, row authority, row directory, intent,
response observation, or outcome. Every production command in the candidate
fails closed because the machine record deliberately binds
`operational_custody_root` to null.

The package consists of exactly:

- this contract;
- `research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v3.json`;
- `research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v3.py`;
- `tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v3.py`;
- `src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v3.py`; and
- `tests/unit/test_solo_block2_runtime_custody_executor_v3.py`.

Qualification is cache-disabled, loopback-free, and offline. Tests may use
only inert values and temporary test-owned paths. They may not create an
operational root or receipt, invoke the production attempt, call a resolver,
create a socket, open a browser, or contact any site.

## 2. Preserved v2 terminal incident

V2 row 0 remains a spent production attempt. Its durable intent consumed the
single attempt even though the request send site was never entered. The exact
operation remains `SB2-PUBLIC-ROOT-PHYSIONET-000`, URL
`https://physionet.org/content/challenge-2012/1.0.0/`, request length 282, and
request SHA-256
`ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449`.

The bound v2 package aggregate is
`48091940a7ceb844c892fb06fd263e479b8c86a1f46c4f0c88d00d72a87439cb`.
The row receipts are:

- intent raw/semantic:
  `a02263b26109ef29f7212a8ea72c987e9e4f7732a88f6ff6b305b99d89177b92` /
  `e3735ad4c4ab07e79ab0dbc3ef8e8f3c26f5ee86489a7233b854854dea5d1610`;
- error raw/semantic:
  `705ddcdb3f0be55ad434620c574a21ea3e02aff6c892ca88f1743d5da6ec3964` /
  `aaeca81dd0bd9305c624249cfdc057387fd465fee5b889b16b81ce752285ef55`;
- outcome raw/semantic:
  `ae72c77609c10c21aaf3e64a8ab77bf4da3adb03c42e55f3bfdfa17f00a98458` /
  `b463ba6475fe82dae08aa98ca2a7d3710915b077f97de2748edf84445aca4924`.

The terminal state is
`TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY`, retry is false, and the
qualified observation is null. Counters are resolver child fork 1,
high-level resolver 1, socket 1, connect 1, TLS wrap 1, and sendall 0.
Request emission is `NOT_ATTEMPTED`. TLS completed far enough to obtain and
validate ALPN/session/certificate inputs, but TLS metadata was not retained
because resolver-receipt validation failed before its write. No official fact,
approval, tracker update, data access, or scientific effect follows from v2.
V2 row 1 remains preempted.

## 3. Resolver receipt defect and repair

The v2 resolver child serialized `getaddrinfo` results through canonical JSON,
which produced builtin integers in the parent. The parent then reconstructed
the retained row and replaced the parsed socket-type value with
`socket.SOCK_STREAM`. On this runtime that constant is a `SocketKind` IntEnum,
not exact builtin `int`. The strict receipt validator correctly rejected the
row after TLS and before request transmission.

V3 normalizes each system resolver tuple at the child JSON boundary with
explicit `int(...)` conversion. The parent accepts only exact builtin integer
leaves, validates family/type/protocol/port/address relations, and retains the
already parsed values. Frozen builtin-integer constants are used only for
comparisons and syscall arguments. Resolver receipt validation now occurs
immediately after resolver return and before socket construction, connection,
TLS, metadata custody, or send.

Hostile regressions cover real `AddressFamily` and `SocketKind` values, IPv4
and IPv6, canonical JSON round trips, Boolean/float/IntEnum/custom-int
substitution, unsupported family, datagram/UDP values, private addresses,
wrong ports, duplicate/order preservation, and pre-socket validation order.

## 4. Row-0-to-row-1 raw-link defect and repair

The exclusive canonical writer returns the SHA-256 of the complete canonical
receipt bytes. V2 stored that raw digest in an outcome's
`intent_record_sha256` field. Its row-1 gate later compared the field with the
intent's semantic self-digest instead of the raw receipt digest. A successful
v2 row 0 would therefore have been rejected by row 1 even when custody was
otherwise exact.

V3 preserves the established raw forward-link meaning and verifies the field
against the SHA-256 of the exact reopened intent bytes. A regression constructs
one canonical receipt whose raw and semantic digests differ, accepts only the
raw link, and rejects the semantic digest substitution.

## 5. Exact requests remain unchanged and ineligible

The closed two-operation roster and the accepted v2 parser remain byte-pinned.
V3 does not change either registered URL, method, path, Host field, header,
request byte, request digest, attempt limit, redirect limit, retry limit, or
row dependency. The request user-agent therefore deliberately remains part of
the exact pre-existing request bytes rather than being rewritten to say v3.

Both operations are ineligible in this construction package. There is no
general URL, redirect, retry, fallback, authentication, cookie, search, API,
archive, download, child-page, contact, data, tracker, or scientific route.

## 6. Supersession boundary

Changing code, schema, version, operation ID, or custody path cannot reset the
spent v2 attempt. Before an operational successor root may be created or any
same-URL request may be attempted, the user must explicitly acknowledge the
spent v2 intent/outcome and supersede the v2 no-retry boundary for exactly one
additional globally budgeted attempt. That authority must bind the final
reviewed activation-package aggregate, exact root device/inode/path, the exact
282-byte request, the v2 incident hashes, and a unique one-use budget ID.

The successor limits remain attempt 1, retry 0, redirect 0, address fallback
0, application fallback 0, resolver high-level calls 1, socket 1, connect 1,
TLS wrap 1, and plaintext sendall 1. Its first exclusive row reservation is
terminal if partial, and its durable intent consumes the new budget regardless
of later failure. There is no automatic further version/root or loop-until-
success permission. The one new global budget is row-0-only; row 1 cannot
consume a second attempt under that supersession and remains separately
preempted unless a later, independently authorized design says otherwise.

Even after explicit supersession, a separate activation package must be
frozen and independently reviewed, followed by a fresh package lock, offline
preflight authority and receipt, row-specific independent GO, and fresh
expiring exact row authority. No v2 receipt is reusable.

## 7. Qualification meaning

Passing this package proves only that the two identified code defects have an
offline additive repair whose source, tests, exact predecessor evidence, and
non-effect claims are internally consistent. It does not authorize or perform
a request, verify an official source/version/license fact, approve a source,
populate a research field, edit a tracker, or conduct science.
