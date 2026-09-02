# Solo Block 2 runtime and operational-custody closure v2

**Package state:** `FINAL_V2_EXECUTOR_QUALIFIED_OPERATIONAL_RECEIPTS_NULL_FETCH_HOLD`  
**Reported date:** `2026-08-31`  
**HTTP requests performed by this package:** `0/2`  
**Resolver calls performed by this package:** `0/2`  
**Durable v2 row intents created:** `0/2`  
**Scientific, tracker, contact, or data effect:** zero

## 1. Additive successor and present HOLD

This is an offline, additive successor to the stopped Solo Block 2 runtime and
operational-custody closure v1. It does not edit, replace, delete, reinterpret,
or resume any v1 file or custody object. It binds a new executor, a new hostile
test, and a new empty custody root. Construction and qualification perform no
DNS query, resolver call, socket creation, TLS action, HTTP request, durable
intent creation, receipt registration, tracker edit, data access, or science.

The v2 executor remains in `FETCH_HOLD` after this package is frozen. The
package lock, preflight authority, runtime preflight, per-row independent GO,
fresh row authority, row directories, intents, observations, errors, and
outcomes are all absent. No operational command is authorized by this
construction package.

The v2 package consists of exactly six files:

- this contract;
- `research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v2.json`;
- `research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v2.py`;
- `tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v2.py`;
- `src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v2.py`; and
- `tests/unit/test_solo_block2_runtime_custody_executor_v2.py`.

The machine record self-digests its semantic content and binds the other five
files by exact path, bytes, SHA-256, mode, link count, and modification time.
It also binds the complete six-file v1 closure as an immutable predecessor.

## 2. V1 false HOLD and attempt-budget finding

One exact v1 row-0 command exited with status 1 after approximately 9.37
seconds. Standard output and error were intentionally normalized to
`/dev/null`. The v1 custody root contains its five prerequisite receipts and
does not contain `row0-physionet-root-v1`, a sidecar, or `intent.json`.
The v1 source contains no row-directory deletion path. Under the package's
declared same-UID noninterference assumption, the observed exact roster
therefore establishes that row reservation never succeeded, no durable intent
existed, and the contractual one-attempt budget was not spent. This is not an
OS-audited claim that an external same-UID process could not have removed a
directory; that concurrent-substitution/deletion exclusion remains a nonclaim.

No v1 application resolver, socket, TLS, HTTP, or request-emission site was
reachable. The only relevant pre-reservation external observation was the
local `/usr/sbin/scutil --dns` SystemConfiguration query inside runtime
manifest construction; it was not the admitted `socket.getaddrinfo` call and
did not emit the registered HTTP request. V1 remains preserved as evidence and
is never retried by this package.

The failure was a false runtime HOLD caused by a non-round-trip-safe manifest
leaf. `platform.mac_ver()` returns a tuple containing a nested release tuple.
V1 converted only the outer tuple to a list. After canonical JSON storage and
reload, the nested tuple became a list. Direct Python equality between the
admitted record and a newly rebuilt record therefore failed even when their
semantic JSON trees were the same. This defect occurred before row reservation.

## 3. V2 round-trip-safe full-manifest gate

V2 retains full exact runtime admission; it does not weaken the manifest into
an unbound stable/volatile subset. The repaired `mac_version` leaf is produced
directly in the canonical JSON data model and is exactly:

`[version_string, [release_component_0, release_component_1, release_component_2], machine_string]`

with exact builtin strings and lists. The executor canonicalizes the admitted
and current full manifests and requires both:

1. exact canonical-byte equality; and
2. exact self-digest equality.

Qualification includes a tuple-to-JSON round-trip regression and a direct
helper-level regression of the exact pre-reservation comparison gate. It does
not invoke the production attempt or `mkdirat`. The regression proves that a
semantically identical reconstructed manifest does not fail merely because
JSON changed the historical nested tuple to a list. Any real field drift—including SystemConfiguration output, resolver files, loaded
modules, dyld receipts, CA bytes, environment, flags, cwd, stdio, or root
identity—still produces HOLD before reservation.

The v2 production process continues to normalize standard streams, enforce the
exact isolated interpreter/argv/environment/flag surface, validate the complete
descriptor roster, reopen every package and authority gate, and require an
empty exact row basename before `mkdirat`. Resolver/socket code remains
unreachable until the row directory, all exclusive sidecars, exact request
receipt, directory fsync, and durable canonical intent have succeeded.

## 4. Preserved response precedence and row sequencing requirements

V2 preserves and binds two required properties of the accepted design without
broadening scope.

First, it never classifies an oversized response before the accepted v2 parser
has completed protocol/framing precedence. Supplied retained bytes are passed
to the accepted parser first. Thus malformed framing or duplicate
`Content-Length` remains `PROTOCOL_VIOLATION` even when the body is oversized;
a completely framed response with `Location` remains `SCOPE_VIOLATION`; only
then may an otherwise valid oversized entity become a transport/content
failure. Regression tests cover both cross-precedence combinations.

Second, row 1 never uses a synthetic row-0 transcript or reconstructed default
context. It reopens and requalifies the actual row-0 intent, outcome, raw
sidecars, diagnostic receipts, forward relations, and accepted parent-parser
context from custody. The exact actual row-0 transcript-model and
outcome-model digests are passed to retained-response qualification. Tests use
two distinct valid row-0 contexts and prove row 1 binds the selected actual
custody context and rejects substitution.

## 5. New operational root

The sole v2 operational root is:

`/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/research/custody/solo_block2_public_documentation_runtime_v2`

At package construction it is empty with device `16777234`, inode `66956470`,
UID `501`, GID `20`, mode `0700`, and link count `2`. The machine record binds
that exact identity. The v1 root and all five v1 receipts remain outside the
v2 root. They are immutable by this contract and v2 never writes them; their
filesystem permissions are not represented as a technical read-only enforcement.

V2 keeps the exact registered operations and requests:

1. `https://physionet.org/content/challenge-2012/1.0.0/` — 282 request bytes,
   SHA-256 `ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449`;
2. `https://archive.ics.uci.edu/dataset/502/online+retail+ii` — 287 request
   bytes, SHA-256
   `94271e586cfbec1d25c03754b1c4f47aadbd8e9459cffad6c050e0a80cf16b1b`.

There is no general URL, redirect, retry, address fallback, authentication,
cookie, form, child page, search, API, archive, download, data, contact, or
scientific route.

## 6. Future authority and forward-only custody

The six production command shapes remain registrar/package specific and are
not exercised by qualification:

- `register-package-lock ROOT REVIEWER CREATED_UNIX_NS`;
- `register-preflight-authority ROOT CREATED_UNIX_NS EXACT_TEXT`;
- `preflight ROOT`;
- `register-independent-go ROOT ROW REVIEWER CREATED_UNIX_NS`;
- `register-row-authority ROOT ROW CREATED_UNIX_NS EXPIRES_UNIX_NS EXACT_TEXT`;
- `attempt ROOT ROW`.

A later operator must independently review the stopped six-file v2 package,
materialize a package lock, separately authorize and materialize the offline
preflight, and then obtain a fresh exact row-specific GO and authority. TLS
transport entropy must be explicit while scientific entropy stays forbidden.

Once a v2 row directory is created, any partial reservation is terminal and is
not removed or retried. Once `intent.json` is durable, the attempt is spent
regardless of resolver, connect, TLS, send, receive, custody, or outcome
failure. Row 1 remains preempted until actual row-0 custody requalifies as the
bounded unverified root-page observation required by the executor. None of
those future events is represented as completed by this package.

## 7. Qualification boundary

All package qualification is offline and cache-disabled. Tests may use only
temporary test-owned directories, inert bytes, fake local receipts, monkeypatch
objects, and source/AST inspection. They must not write either operational
root, register a receipt, invoke a production command, call the resolver,
create a socket, use loopback, or perform a browser/network action.

Passing this closure proves only that the stopped v2 bytes and offline protocol
design satisfy their declared invariants. It does not verify an official fact,
select a source, close a research field, edit a tracker, spend an attempt, or
make either request eligible.
