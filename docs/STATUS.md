# Current status

## ctserial 0.6.0 connect suggestions — 2026-11-04

The release and prior display work are committed through `493e2f5` on `main`,
three commits ahead of the local `origin/main` reference. Device completion is
uncommitted. No submission or publication occurred during this follow-up; the
changelog remains `unreleased`.

The baseline includes ctui 1.x, Python 3.11+, native async serialx sessions,
HexBytes/UTF-8 sends, both fuzzy-pattern commands, live fuzz output, single-line
UTF-8 transaction rows, GPL metadata, and release CI. See [README.md](../README.md),
[DECISIONS.md](DECISIONS.md), and [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md).

## Current changes

- `connect` suggests asynchronously enumerated native serial paths, with
  device-reported `Manufacturer | Product` details as explicitly chosen by the
  user. Trim descriptor padding and omit missing fields; no USB database labels
  or numeric IDs are displayed.
- Resolve stable symlinks to native port names for suggestions; sort/deduplicate
  paths. Use `Serial device` when manufacturer and product are both unavailable.
- Keep manual paths and serialx URLs usable, including on enumeration failure.
- Added completion/filtering and enumeration-failure regressions; connection
  tests mock enumeration rather than consulting the host's devices.
- Updated README, changelog, and decision D8.

## Validation

- Python 3.11.17 on Linux x86-64: all 41 tests passed, including the real serialx
  PTY test, mocked device completion/filtering, and manual-connect fallback.
- Black and isort passed; Pylint on commands/common: 10.00/10. Lockfile and
  whitespace and documentation file-link checks passed.
- A temporary check using the actual ctui layout/completer and live device
  enumeration produced the user's chosen path/details format exactly. No serial
  port was opened and no serial data was sent during this completion check.
- Historical evidence: `493e2f5` passed 39 Python 3.11 tests; `1c11eb5` passed
  38 tests on Python 3.11 and 3.14 plus wheel/sdist smoke tests. Prior temporary
  physical-device checks verified expected send/fuzz responses; missing responses
  were not reproduced. No physical device is required by repository tests.
- Existing artifacts predate the display/completion changes. No current artifact
  rebuild, Python 3.14 rerun, or remote CI success is claimed for this follow-up.

Async worker/event-loop notification checks require execution outside the local
sandbox. Local results do not establish remote platform-matrix success.

## Open items and next steps

1. Before release, run remote CI and rebuild/smoke-test both distributions.
   Follow [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for authorized submission,
   changelog dating, tagging, and publication verification.
2. If missing responses recur, capture connection settings, the exact command,
   and transaction rows. Current live-device checks do not establish that cause.

Generic timing-based collection can attribute late bytes to the next exchange.
Protocol framing and old ctui project import remain unimplemented; see
[README.md](../README.md) and [DECISIONS.md](DECISIONS.md).
