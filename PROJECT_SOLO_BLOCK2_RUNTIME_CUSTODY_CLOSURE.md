# Solo Block 2 runtime and operational-custody closure v1

**Package state:** `FINAL_EXECUTOR_QUALIFIED_OPERATIONAL_RECEIPTS_NULL_FETCH_HOLD`  
**Reported date:** `2026-08-31`  
**HTTP requests performed:** `0/2`  
**Resolver calls performed:** `0/2`  
**Durable row intents created:** `0/2`  
**Administrative contacts or data actions:** `0`  
**Scientific effect:** zero

## 1. What this successor closes

This additive package supplies the final production runtime/client/custody
surface required by the accepted Solo Block 2 public-documentation
reconnaissance amendment v2.  It does not modify any byte of that six-file
predecessor.  It closes only the local code and protocol design for:

- exact loaded-runtime and environment capture;
- a pre-existing, identity-bound operational custody root;
- canonical, exclusive, durable package/preflight/GO/authority/intent/outcome
  receipts;
- the exact two registered HTTPS root-page request paths;
- one bounded system-resolver call inside a spent row attempt;
- one chosen global address, one socket, one connect, one TLS session, one
  plaintext HTTP/1.1 request, no application retry and no address fallback;
- bounded streaming raw and derived custody; and
- forward-only row-0 then row-1 sequencing.

It is the final executable surface, not a generic URL client and not another
simulator.  Its closed command surface has four local receipt registrars, one
offline preflight and one row attempt.  Registrar arguments are limited to the
bound root, exact reviewer principal or authority text, exact timestamps and,
where applicable, row ordinal 0 or 1.  The preflight and attempt accept only
the already-bound root and fixed row ordinal.  There is no caller-supplied
transport, resolver, socket, clock, environment, filesystem, URL, transcript,
client, callback or dependency seam.

The package does **not** create the post-freeze operational receipts needed to
make either row eligible.  Package lock, offline-preflight authority, runtime
preflight, independent row GO, fresh row authority, row directory, intent,
network observations, errors and outcomes all remain strict null.  No request
can be made from the stopped package state.

## 2. Current authority boundary

The normalized visible authority text is exactly:

> Alright, go through it then. I am overseeing you to the end.

It is 60 UTF-8 bytes and has SHA-256
`2e8560c4586f620abe2f276793c09a49e0008aaed86ba2b4a112a01565ae50fb`.
Only trailing transport framing or an HTML-space transport entity is outside
the normalized text.  Account identity, raw transport bytes, timestamps,
conversation-envelope metadata and cryptographic user authentication are not
bound.

In the immediate agreed schedule, this text authorizes construction, local
review and qualification of this final closure package and preparation of one
empty, mode-0700, repo-local custody root.  It does not bind the final stopped
machine raw digest, package aggregate, runtime-preflight digest, independent
GO, row request digest in an operational receipt, or exact affirmative row
authority template.  It therefore does **not** authorize package-lock
materialization, offline-preflight receipt materialization, DNS, an HTTPS
request, TLS transport entropy, a contact, authentication, form, cookie,
credential, download, archive, API, data access, escrow action, scientific
entropy, training, science, result, claim, submission or tracker edit.

TLS necessarily consumes transport cryptographic entropy.  A future exact row
authority must affirmatively authorize that transport entropy while continuing
to set scientific entropy to false.  This package never treats the current
text as that later authority.

## 3. Immutable predecessor and additive files

The complete accepted v2 predecessor remains an immutable six-file input:

- `PROJECT_SOLO_BLOCK2_PUBLIC_DOCUMENTATION_RECONNAISSANCE_AMENDMENT.md`;
- `research/fixtures/manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.json`;
- `research/diagnostics/manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py`;
- `tests/unit/test_manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py`;
- `src/heterodiff/artifacts/solo_block2_public_documentation_reconnaissance_executor_v2.py`; and
- `tests/unit/test_solo_block2_public_documentation_reconnaissance_executor_v2.py`.

This closure adds exactly six files:

- this human contract;
- `research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v1.json`;
- `research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v1.py`;
- `tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v1.py`;
- `src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py`; and
- `tests/unit/test_solo_block2_runtime_custody_executor_v1.py`.

The machine record binds the other five additive raw files.  The machine raw
digest remains external to avoid a self-cycle.  After a later independent
review event, the exact package-lock registrar recomputes the canonical
aggregate of the stopped machine raw digest, machine semantic digest and five
bound raw-file receipts.  It accepts the reviewer principal and event time as
direct bounded command arguments and creates `package-lock.json` with
`O_EXCL`, mode 0600 and file/directory fsync.  There are no proposal or staging
receipt files.  Until that final receipt exists, offline preflight fails
closed.

The six exact command shapes are:

- `register-package-lock ROOT REVIEWER CREATED_UNIX_NS`;
- `register-preflight-authority ROOT CREATED_UNIX_NS EXACT_TEXT`;
- `preflight ROOT`;
- `register-independent-go ROOT ROW REVIEWER CREATED_UNIX_NS`;
- `register-row-authority ROOT ROW CREATED_UNIX_NS EXPIRES_UNIX_NS EXACT_TEXT`;
- `attempt ROOT ROW`.

Every command requires the real `python3.12` launcher, isolated flags, empty
environment projection and exact direct-script argument vector.  The
registrars do not infer that command invocation proves an external person's
identity; the supplied principal/text must correspond to the separately
observed reviewer or user event.  Each registrar receipt explicitly says that
its principal identity and caller-supplied nanosecond time are not externally authenticated, signed or trusted-clock attested.
Receipt chronology is an
internally checked assertion, not independent identity or time evidence.

## 4. Exact custody root and pre-intent poison rule

The one operational root is:

`/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/research/custody/solo_block2_public_documentation_runtime_v1`

At package construction it is an empty directory with device `16777234`,
inode `66899471`, owner UID `501`, GID `20`, mode `0700`, and link count `2`.
The machine record binds those values.  The executor walks every custody,
package, interpreter, CA, resolver and loaded-module path component from an
opened `/` descriptor with `O_DIRECTORY|O_NOFOLLOW`, then uses only
directory-descriptor-relative names inside the custody root.  Slash, empty,
`.`, `..`, NUL and symlink components are forbidden.

The row basenames are fixed.  The executor creates a row directory mode 0700
and all raw sinks with `openat`, `O_EXCL|O_NOFOLLOW`, mode 0600.  Directory
link-count reporting varies across admitted host filesystems, so link counts
are bounded by the exact live entry roster while device, inode, owner, group,
mode and every regular-file link count remain exact.  It writes and
fsyncs the exact plaintext request receipt, fsyncs every initially empty raw
sink and the row directory, then creates and fsyncs the canonical intent last.
It reopens the intent and every gate before entering the resolver.  The parent
root link count may remain the same or increase by exactly one when `mkdirat`
creates the row directory; all other identity attributes must remain equal.

Directory creation plus multiple exclusive sidecar creations are not atomic.
If a crash leaves a row directory or any sidecar without a durable intent, the
exact row basename is permanently
`TERMINAL_ABANDONED_PREINTENT_RESERVATION_NO_REQUEST_NO_RETRY`.  It is never
deleted, repaired, renamed, replaced, reused or treated as an eligible retry.
For row 0 this state also permanently preempts row 1.

Once `intent.json` is durable, the attempt is spent even if the resolver never
starts, the resolver child is killed, the connect or TLS handshake fails, the
request is only partially passed to TLS, custody becomes incomplete, the
process crashes or outcome creation fails.  There is no retry, resume,
replacement, alternate address, alternate URL, mirror or fallback.

## 5. Stopped runtime preflight

The required launch prefix is exact:

`/usr/bin/env -i /Users/mahtab/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B <exact-source-path>`

The executor rejects any other interpreter path or digest, Python build,
OpenSSL build, environment, original argument vector, Python flags,
`sys.path`, inherited descriptor roster or source bytes.  The exact flag
receipt requires non-optimized CPython 3.12 defaults plus `-I -S -B`, UTF-8
mode 1, safe-path mode, an empty `sys._xoptions` object and an empty warning
option roster; extra switches such as `-O`, `-W`, `-X`, `-u` or reordered
launcher arguments therefore fail closed.  Standard streams are first normalized to the verified
`/dev/null` character device, and the complete `/dev/fd` roster is checked so
descriptors above 1023 cannot escape the gate.  The accepted predecessor
parser is read and hashed through one no-follow descriptor, compiled from
those same raw bytes and never loaded through a path or bytecode loader.
The already executing Python image and executor source do not have equivalent
one-open OS attestation: their digests are post-load path receipts.  Concurrent
same-UID replacement between OS/Python load and that later check is an explicit
nonclaim and must be excluded by the local execution environment; this package
does not represent it as technically prevented.
Offline preflight content-addresses:

- the interpreter, `/usr/bin/env`, Python build and every imported file-backed
  module, including any existing bytecode-cache file that the startup loader
  could have read;
- all enumerated dyld images and all five arm64e shared-cache components;
- the built-in CPython SSL/socket/hash/native surface and OpenSSL version;
- the explicit root-owned `/private/etc/ssl/cert.pem` bytes and stat identity;
- `/private/var/run/resolv.conf`, `/private/etc/hosts`, and the bounded raw
  `/usr/sbin/scutil --dns` SystemConfiguration snapshot;
- kernel, OS, architecture, uid, gid, groups, cwd, locale, timezone, exact
  environment name/value digests, forced umask 0077, `sys.path`, Python flags,
  stdio identities and the custody-root identity.

The current host snapshot returns status 1 with exact stdout
`No DNS configuration available` and empty stderr.  The executor treats that
as HOLD and refuses to materialize a runtime preflight.
It never guesses that `/etc/resolv.conf` is authoritative on macOS.  A later
preflight can proceed only when the stopped SystemConfiguration snapshot is
nonempty and admitted, and a later attempt recomputes the entire manifest and
requires exact equality immediately before row reservation.

Even a successful snapshot does not bind mDNSResponder daemon/cache state,
DNS wire bytes, packet count, TTLs or server determinism.  Those are explicit
nonclaims in the manifest and future authority.  A changed snapshot or any
other loaded-runtime drift produces HOLD before intent.

## 6. Exact row attempt and resolver truth boundary

The operation roster remains exactly the predecessor's two HTTPS GET rows:

1. `https://physionet.org/content/challenge-2012/1.0.0/`;
2. `https://archive.ics.uci.edu/dataset/502/online+retail+ii`.

There is no DNS preflight, HEAD, third URL, general URL input, link follow,
redirect target, browser, API, child page, search, form, authentication,
cookie, credential, `Range`, `Referer`, script, subresource, mirror or
alternate-host route.

After all gates and durable intent, the executor forks one bounded child for
one high-level `socket.getaddrinfo` call for the exact row host, service 443,
`AF_UNSPEC`, `SOCK_STREAM`, TCP and `AI_ADDRCONFIG`.  The child closes every
inherited descriptor except its capped result-pipe writer.  The parent applies
a 12-second absolute monotonic resolver deadline inside the 45-second total
attempt deadline, caps the result bytes, kills with SIGKILL and reaps on
expiry, and rejects any unsupported or malformed tuple.  Only global IPv4 or
IPv6 addresses are admitted.  Returned order, including duplicates, is
preserved.  It selects the first admitted address and creates exactly one
socket and one connect; it never tries another address.

This bounds executor waiting and high-level application calls.  It does not
claim that killing the child stops the system resolver daemon, that the OS
made one DNS packet, or that TCP/TLS made no lower-layer retransmission.  Zero
retry means zero application-level resolver, address, connect, TLS and HTTP
retry/fallback.  TCP retransmission, TLS record behavior and OS scheduling are
outside custody and are expressly bound as nonclaims.

The executor creates a new client-only TLS context after intent, verifies the
hostname and SNI, permits only TLS 1.2 through 1.3, disables tickets/session
reuse, loads no client certificate and requires ALPN exactly `http/1.1`.  It
rehashes the CA bytes/stat before and after loading and retains the selected
cipher, TLS version, leaf DER digest and bounded verified-chain public-byte
digests.  Exact request bytes mean plaintext HTTP/1.1 bytes passed to TLS, not
unobservable encrypted wire bytes.

## 7. Streaming and terminal custody

The preopened sinks are `request.raw`, `response-head.raw`,
`transfer-body.raw`, `decoded-entity.raw`, `tls-metadata.raw`, `stderr.raw`
and `overflow-witness.raw`.  No client path reopening, truncation, rename-over
or replacement exists.  Response head and raw transfer body are written as
received.  A separately capped one-byte overflow witness distinguishes an
exact accepted ceiling from an attempted cap-plus-one stream.  Each open sink
is rehashed through its same read/write descriptor before intent, again before
the resolver and again before outcome, so same-inode byte changes, appends,
link changes and path replacement fail closed.  Derived entity bytes are
written only after the byte-pinned predecessor parser finishes.  Every sink,
receipt and exact row and root directory roster is fsynced and reverified
before the exclusive outcome is created.

The byte-pinned accepted v2 parser requires exact HTTP/1.1 grammar, CRLF framing, one status, no
obs-fold, unambiguous singleton/framing headers, no `Transfer-Encoding` plus
`Content-Length`, and either exact Content-Length, strict extension-free and
trailer-free chunked framing, or complete connection-close framing.  It rejects
1xx, 3xx, `Location`, `Set-Cookie`, authentication headers, `Refresh`, every
`Content-Disposition`, nonidentity content encoding, nontext media, invalid
UTF-8, BOM/control bytes, data-like magic, challenge/login/robot/error markers,
ambiguity, truncation and every cap violation.  Oversized retained test input
is still classified by that parser, so earlier protocol evidence and then
scope evidence outrank the body-cap content result.  All 36 frozen diagnostic
fields are retained.  Protocol evidence outranks scope evidence, which
outranks a later transport error.  A general body cap-plus-one is
transport/content no-go; when an already-complete Content-Length or chunked
frame is followed by the overflow witness, the extra byte instead proves a
protocol violation.

The terminal states remain forward-only.  A complete accepted response is only
`TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY`; it is not official source,
version, archive, license or governance verification.  Any other result is a
no-go terminal state.  Missing outcome after intent is spent incomplete.

Row 1 cannot obtain GO, authority or intent until the executor reopens row 0's
canonical intent/outcome, exact directory roster and every raw sidecar; checks
their device/inode/owner/mode/link-count/size/digest; re-runs strict response
qualification with all 36 diagnostics; validates the resolver, selected
endpoint, TLS policy, leaf certificate and verified-chain receipts; and proves
the exact terminal accepted state in the same package/runtime context.  An
outcome digest alone is insufficient.
The exact custody-requalified row-0 parent transcript and fully recomputed
parent outcome are then passed into row-1 qualification; no synthetic prior is available.
Row 1 revalidates the same context after durable intent and after
its spent attempt, and its observation binds the previous qualification
outcome digest.

The package validator treats the machine's empty root and null slots as the
freeze-time snapshot.  After later authorization, it admits only the exact
forward prefix of package-lock, preflight, row-0 and row-1 receipt/directory
names with the required owner, device, mode and link identities.  It neither
mistakes legitimate later receipts for package drift nor treats their presence
as proof that an operational row succeeded.

## 8. Current non-effects and next gates

No original Solo Block 2 operational box is closed by this package.  The
following all remain open: populated precontact instance, independent instance
admission, administrative-contact authority, administrative requests,
complete approval receipts, admitted data-access instance and fresh data-
access authority.  All approval, escrow, power, version, license, governance,
contact, data and scientific blockers remain open.  Result slots remain empty;
F172 remains null.  No timetable or evidence-ledger byte is edited here.

The next legal sequence is:

1. stop and independently audit the six package files;
2. separately authorize and create the exact independent package lock;
3. obtain exact offline-preflight authority and run preflight only when the
   resolver snapshot is admissible;
4. obtain an independent row-0 GO that binds the stopped package and preflight;
5. obtain fresh, expiring, exact-equality row-0 authority that binds all final
   digests and explicitly permits TLS transport entropy; and only then
6. allow creation of the row-0 directory, sidecars and intent followed by its
   one spent attempt.

Row 1 requires a separately fresh post-row-0 GO and authority.  None of these
later steps is implied by this package or the current user text.
