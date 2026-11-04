# Current status

## ctserial 0.6.0 CI timing fix — 2026-11-04

Work is based on `aa9e90a` on `main`, aligned with the local `origin/main`
reference at inspection. The test-only fix below is uncommitted. No commit,
push, PR update, or workflow rerun was performed. The release is still unreleased.

The 0.6.0 implementation includes async serialx sessions, ctui 1.x commands,
streaming fuzz output, single-line UTF-8 rows, and device-name completion. See
[README.md](../README.md), [DECISIONS.md](DECISIONS.md), and
[RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for behavior and release steps.

## Current fix and evidence

The remaining failure on the Black Dependabot PR is an asyncio deadline test,
not the formatter. It assumed a 2 ms sleep would deliver a response before a
20 ms deadline. Replace real sleeps in that test with a controlled loop clock
advanced on each synchronous read. Assert all expected chunks are collected
and fail if reading continues beyond the overall deadline. Runtime serial timing
and dependency declarations/lockfile are unchanged; no lockfile bump is needed
for this failure.

Observed remote results on 2026-11-04:

- [Black PR #1 run](https://github.com/ControlThings-io/ctserial/actions/runs/41866049624)
  at `e9fdd016`: style passed; Windows Python 3.11 and 3.12 failed only
  `test_continuous_response_has_overall_deadline` with an empty response.
- [Main run](https://github.com/ControlThings-io/ctserial/actions/runs/41865704019)
  at `aa9e90a`: the same test failed on Windows Python 3.11 with Black 26.5.1.
- [Pylint PR #2 run](https://github.com/ControlThings-io/ctserial/actions/runs/41866068037)
  succeeded. No Pylint change is part of this fix.

Internet research corroborates this class of timing issue. Python's
[3.11/3.12 platform documentation](https://docs.python.org/3.12/library/asyncio-platforms.html#windows)
describes typical Windows monotonic-clock resolution around 15.6 ms. CPython
[issue #110088](https://github.com/python/cpython/issues/110088) records
Windows GitHub Actions timing assertions failing under CI scheduling, and its
[asyncio test utilities](https://github.com/python/cpython/blob/main/Lib/test/test_asyncio/utils.py)
allow clock-resolution tolerance. These support the timing diagnosis; they do
not establish a Black defect. No matching Black issue was found in the searches.

## Local validation

- A temporary delayed-scheduling simulation reproduced the old empty-response
  assertion failure; the same simulation passes with the revised test.
- Python 3.11.17 and Python 3.14.10 on Linux x86-64: all 41 tests passed, including
  the real serialx PTY test.
- Black 26.10.1, the Dependabot version, passed `--check src tests` in an isolated
  environment. The changed file also passed locked Black 26.5.1 and isort.
- `uv lock --check --offline`, `git diff --check`, and documentation file-link
  checks passed.
- No fixed Windows run or remote matrix success is claimed yet. Local async
  checks require execution outside this environment's notification-restricting
  sandbox. Existing release artifacts predate this test-only change.

## Next steps

1. After authorized submission, confirm the Windows jobs pass and update/rebase
   the Black Dependabot PR onto the fix. Its existing run predates this change.
2. Complete remaining release checks and artifact validation using
   [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md).

If missing serial responses recur, capture connection settings, commands, and
transaction rows. Previous temporary physical-device checks returned expected
responses, but did not establish the cause of the reported symptom. Generic
response framing and old ctui project import remain as documented in the README.
