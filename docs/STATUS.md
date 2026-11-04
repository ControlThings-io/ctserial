# Current status

## ctserial 0.6.0 developer-tool refresh — 2026-11-04

Work is based on `9707e76` on `main`, aligned with the local `origin/main`
reference at inspection. The developer-tool refresh is uncommitted. No commit,
push, PR update, or workflow rerun occurred during this follow-up. The 0.6.0
release remains unreleased.

The implementation includes async serialx sessions, ctui 1.x commands, streaming
fuzz output, single-line UTF-8 rows, and device-name completion. See
[README.md](../README.md), [DECISIONS.md](DECISIONS.md), and
[RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for usage and release contracts.

## Current changes

- Refreshed only the requested developer tools in `uv.lock`: Black 26.5.1 to
  26.10.1 and Pylint 4.0.7 to 4.1.3, verified as the latest stable releases on
  PyPI on 2026-11-04.
- Pylint's required Astroid dependency advanced from 4.0.4 to 4.3.4. These are
  the only three changed lockfile package records. Runtime packages and
  application source are unchanged.
- The existing unconstrained dev declarations already permit these versions;
  `pyproject.toml` needs no change. The Python 3.11 development environment is
  synced to the updated lockfile.
- README now documents targeted developer-tool upgrades and reviewing/testing
  them while keeping development and CI on the same checked-in lockfile.

## Validation

Linux x86-64 with Python 3.11.17 and the updated lockfile:

- Black 26.10.1: `--check src tests` passed; no reformatting required.
- isort: `--check-only src tests` passed.
- Pylint 4.1.3 with Astroid 4.3.4: existing checks on commands/common passed,
  rated 10.00/10. No new Pylint CI gate or broader lint scope was introduced.
- All 41 unittest tests passed, including the real serialx Linux PTY test.
- `uv lock --check --offline`, `git diff --check`, and documentation file-link
  checks passed.
- No remote CI success or Windows/macOS run is claimed for this refresh.
  Async checks required execution outside the local notification-restricting
  sandbox.

## Next steps

1. After authorized submission, confirm remote CI passes with the tool refresh.
   Existing Black/Pylint Dependabot PRs may become redundant or need updating.
2. Before publishing 0.6.0, rebuild/smoke-test both distributions and complete
   [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md).

The timing-sensitive Windows test was fixed in `9707e76` using controlled time;
that issue was independent of Black's formatter. Prior release artifacts predate
some display/completion changes and are not evidence for the current source.
If missing serial responses recur, capture connection settings, commands, and
transaction rows; previous temporary physical-device checks returned expected
responses without establishing the cause of the reported symptom.
