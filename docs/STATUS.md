# Current status

## ctserial 0.6.0 fuzz feedback — 2026-11-04

The release preparation is committed locally as `a129af3` on `main`; the branch
is one commit ahead of the local `origin/main` tracking reference. The streaming
follow-up described below is uncommitted. No submission or publication was
performed during this follow-up. The changelog remains marked `unreleased`.

The 0.6.0 baseline includes ctui 1.x, Python 3.11+, native async serialx sessions,
HexBytes/UTF-8 sends, both fuzzy-pattern commands, GPL metadata, release docs, and
CI. See [README.md](../README.md), [DECISIONS.md](DECISIONS.md), and the
[release checklist](../RELEASE_CHECKLIST.md) for contracts and release steps.

## Current changes

- Fuzz commands update the rolling UI table immediately for each TX, RX,
  no-response, and error row, yielding between complete exchanges for rendering.
- CLI fuzz output prints and flushes each new row to the selected stdout and
  prints one completion summary, without duplicating the complete table.
- Headless dispatch still returns the summary/table without printing. Both hex
  and UTF-8 fuzzing share the same presentation and serialized exchange path.
- Progress remains visible if a later attempt fails. Existing response deadlines,
  framing, and serial transmission behavior are unchanged.
- Added regressions for intermediate UI output for both pattern types, CLI
  streaming/flush/output routing, and preserving output after an I/O error.

## Validation

Local Linux x86-64 evidence for this follow-up:

- Python 3.11.17: 38 unittest tests passed, including the real serialx PTY test.
- Python 3.14.10: the same 38 tests passed, including the real serialx PTY test.
- Pylint on commands: 10.00/10. Black, isort, lockfile, documentation file links,
  and whitespace checks passed.
- Temporary live-device checks compared the user's two known requests with
  standalone sends and repeated fuzzing. All returned the expected responses.
- A temporary check through actual terminal input and the ctui layout also
  returned both expected responses and observed separate TX1, RX1, TX2, RX2 table
  updates. Missing responses were not reproduced, before or after this fix.
- No physical device paths or device-specific integration scripts were added to
  the repository; automated serial tests continue to use a Linux PTY.
- Follow-up wheel and sdist rebuilt; both passed isolated Python 3.11
  installed-artifact smoke tests, including GPL metadata checks. The GPL-corrected
  baseline also passed direct metadata/license inclusion checks.

Async worker/event-loop notification checks required execution outside the local
sandbox. This is local evidence, not proof of the remote platform matrix.

## Open items and next steps

1. If missing responses recur in the user's session, capture the exact connect
   settings, command invocation, and observed transaction rows; current live
   checks do not establish the cause of that symptom.
2. Run remote CI across the declared Python/platform matrix. Temporary live-device
   testing supplements the PTY tests but does not cover all adapter types.
3. Follow [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for authorized submission,
   changelog dating, tagging, and publication verification.

Generic timing-based collection can attribute late bytes to the next exchange.
Protocol framing and old ctui project import remain unimplemented, as documented
in [README.md](../README.md) and [DECISIONS.md](DECISIONS.md).
