# Decisions

## D1 — ctui 1.x and Python 3.11 (accepted)

For 0.6.0, use the supported top-level ctui API: a `CtuiApp` subclass, typed
`@command` methods, and lifecycle hooks shared by UI and CLI. Require
`ctui>=1.0.0,<2` and Python 3.11+, matching ctui's minimum. Preserve the existing
`send hex` and `send utf8` command names. Use ctui's SQLite project backend for
command history; no migration of ctui 0.8 project data is implemented.

## D2 — Byte and pattern conversion (accepted)

Use ctui's `HexBytes`, `FuzzyHexPattern`, and `FuzzyStringPattern` for command
conversion. Published ctui 1.0.0 has no `StringBytes`; the user explicitly chose
ctui `str` conversion followed by UTF-8 encoding for `send utf8`. Parse quoting
only once. Both fuzz commands share bounded lazy expansion and exchange logic;
UTF-8 pattern results are encoded individually. Sampling is not exposed in 0.6.0.

## D3 — Native asynchronous serialx sessions (accepted implementation choice)

Use `serialx>=1.15.1,<2` and its native `AsyncSerial` API, with a lock around
connect, close, sends, and whole fuzz sequences. This prevents concurrent UI
commands from consuming each other's responses. Open requested ports directly
rather than requiring enumeration membership, which excludes symlinks and PTYs.
The legacy standalone sniff module uses serialx's synchronous API.

## D4 — Bounded exchanges and output (accepted implementation choice)

Without protocol framing, collect a response within a one-second overall deadline
and stop after 100 ms of silence following the first bytes. Do not silently
flush pending input. Late replies may be consumed by a subsequent exchange;
protocol-specific framing remains future work. Reject responses above 65,536
bytes and retain only the latest 1,000 display rows. Display rows remain in
memory rather than becoming a new traffic-persistence feature.

Fuzzing defaults to a maximum complete expansion of 256 payloads, with an explicit
`--limit` up to 65,536. Reject oversized patterns before writing. Continue on no
response, stop on I/O failure, and propagate cancellation without retrying. These
bounds keep defaults finite while allowing explicit larger runs.

## D5 — GPL-3.0-or-later metadata (accepted)

The inherited `pyproject.toml` declared `LGPL-3.0-or-later`, while `LICENSE` is
GPL v3 and source headers state GPL v3 or later. The user explicitly selected
`GPL-3.0-or-later` for 0.6.0 to match those existing files. Correct the package
declaration and include the existing LICENSE via explicit `license-files`.
Installed-artifact smoke tests verify the declaration and license-file metadata.
