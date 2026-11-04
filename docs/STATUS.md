# Current status

## ctserial 0.6.0 preparation — 2026-11-04

Implementation is complete on `main`, based on `58abc18`. Changes are uncommitted;
no tag, push, PyPI upload, or GitHub release has been performed. The changelog
remains marked `unreleased` until publication is authorized and dated.

Completed:

- Version 0.6.0, Python 3.11+, ctui 1.x, and serialx 1.15.1+ with an updated uv lock.
- `CtuiApp` migration, native async serial sessions, serialized exchanges,
  lifecycle cleanup, device enumeration, and connection/project status.
- `send hex` with `HexBytes`; `send utf8` with ctui string conversion followed by
  UTF-8 encoding, as explicitly selected by the user.
- `fuzz hex` with `FuzzyHexPattern` and `fuzz utf8` with `FuzzyStringPattern`;
  shared lazy expansion, complete-count validation, and sequential sending.
- Bounded responses and rolling transaction display; legacy sniffer migrated to
  serialx with cleanup on interruption and partial-open failure.
- Regression tests, real serialx Linux PTY integration, artifact smoke tests,
  Python 3.11–3.14/Linux/macOS/Windows CI, and tests before tag-triggered publishing.
- README, changelog, [decisions](DECISIONS.md), and
  [release checklist](../RELEASE_CHECKLIST.md); license and development/release
  documents explicitly included in distributions.
- GPL-3.0-or-later package metadata, explicitly selected by the user to match
  LICENSE and source headers; artifact smoke tests check the declaration.

## Validation

Local Linux x86-64 evidence for this working tree:

- Python 3.11.17: 35 unittest tests passed, including the real serialx PTY test.
- Python 3.14.10: the same 35 tests passed, including the real serialx PTY test.
- Black and isort formatting checks passed. Pylint on commands/common: 10.00/10.
- `uv lock --check --offline` and `git diff --check` passed.
- Final wheel and sdist built; both passed isolated Python 3.11 installed-artifact
  smoke tests after the backend-timeout fix. Archives contain the expected metadata,
  README and LICENSE; sdist also includes tests, release/status docs, and uv.lock,
  with no bytecode files. Runtime/dependency metadata matches 0.6.0. Both archives
  were rebuilt after the GPL metadata correction and passed their smoke tests;
  direct inspection verified GPL-3.0-or-later and LICENSE inclusion in each.
- Local documentation file links checked; whitespace review passed.
- Console-script help worked with a temporary XDG data directory.

Async worker/event-loop notification checks required execution outside the local
sandbox; tests use temporary project directories and mocked ports or a PTY.
This is a local environment limitation, not remote CI evidence.

## Open items and next steps

1. Run remote CI across the declared Python/platform matrix and exercise physical
   serial adapters. Local PTY tests do not establish physical-adapter behavior.
2. Follow [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md): date the changelog,
   obtain submission authorization, commit/push, tag, and verify publication.

Generic timing-based response collection can attribute late bytes to the next
exchange. Protocol framing and old ctui project import are not implemented; see
[README.md](../README.md) and [DECISIONS.md](DECISIONS.md).
