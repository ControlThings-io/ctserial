# Current status

## ctserial 0.6.0 transaction display — 2026-11-04

Release preparation (`a129af3`) and streaming fuzz output (`1c11eb5`) are committed
locally on `main`, two commits ahead of the local `origin/main` reference. The
single-line UTF-8 display changes below are uncommitted. No submission or
publication was performed during this follow-up; the changelog is `unreleased`.

The baseline includes ctui 1.x, Python 3.11+, native async serialx sessions,
HexBytes/UTF-8 sends, both fuzzy-pattern commands, live fuzz output, GPL metadata,
and release CI. See [README.md](../README.md), [DECISIONS.md](DECISIONS.md), and
[RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for usage and release contracts.

## Current changes

- Each TX/RX payload occupies one row, preserving four-byte hexadecimal groups
  without inserting line breaks.
- A single UTF-8 column replaces the combined ASCII/UTF-8 decode. Invalid bytes,
  controls, and Unicode line/paragraph separators become replacement characters.
- Both send commands and both streaming fuzz commands share this display path.
- Updated presentation regressions, README, changelog, and decision D7.

## Validation

- Current follow-up: Python 3.11.17 on Linux x86-64 passed all 39 tests, including
  long-payload row/grouping checks, UTF-8/control-byte presentation, live fuzz
  output, and the real serialx PTY test.
- Black and isort checks passed. Pylint on commands/common: 10.00/10.
  Documentation file links and `git diff --check` passed.
- Historical evidence for `1c11eb5`: 38 tests passed on Python 3.11 and 3.14;
  wheel/sdist smoke tests passed. Temporary live-device checks returned the user's
  expected responses for sends and fuzzing, including actual terminal input.
  Missing responses were not reproduced. Repository tests use no physical device.
- Those artifacts predate this display change; no new artifact validation or
  Python 3.14 run is claimed for the current follow-up.

Async worker/event-loop notification checks require execution outside the local
sandbox. Local results do not establish remote platform-matrix success.

## Open items and next steps

1. Before release, run remote CI and rebuild/smoke-test both distribution formats.
   Follow [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for authorized submission,
   changelog dating, tagging, and publication verification.
2. If missing responses recur, capture connection settings, the exact command,
   and transaction rows. Current live-device checks do not establish that cause.

Generic timing-based collection can attribute late bytes to the next exchange.
Protocol framing and old ctui project import remain unimplemented, as documented
in [README.md](../README.md) and [DECISIONS.md](DECISIONS.md).
