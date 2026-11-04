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

## D6 — Show fuzz transactions during execution (accepted)

The user requested each send and receive be visible before the next attempt.
Exchanges were already awaited sequentially, but ctui only displayed the returned
table after the whole command completed. Update the UI's rolling table and
invalidate it at each TX, RX, no-response, or error row; yield after each exchange
to allow rendering. Keep the final UI result from replacing the streamed table.
CLI batches print and flush each new row to their selected stdout, followed by a
single completion summary. Headless dispatch updates output_text and returns the
summary/table without printing. Both pattern types share this presentation path.

Temporary live-device checks returned the expected responses for standalone sends
and fuzzing, including through terminal input. Missing responses were not
reproduced, so this fix leaves the response deadlines and serial framing unchanged.

## D7 — One line per payload with UTF-8 text (accepted)

The user requested unwrapped payloads while retaining byte grouping and only
UTF-8 output. Each TX/RX row now contains all hex bytes grouped every four bytes,
with no inserted line breaks, and one UTF-8 text cell under a UTF-8 header.
Replace invalid UTF-8, Unicode controls, and line/paragraph separators with the
replacement character so binary payloads cannot split the decoded cell into
multiple lines. The UI continues to allow horizontal scrolling of long rows.
This applies to both send commands and both streaming fuzz commands.

## D8 — Device-reported names in connect suggestions (accepted)

The user chose native port paths with `Manufacturer | Product` details, using
device-reported descriptors rather than USB vendor/product database names or
numeric IDs. Use serialx's asynchronous enumeration and resolved native paths
so Linux suggestions show names such as `/dev/ttyACM0` rather than stable
symlinks. Trim descriptor padding, omit unavailable fields, and show
`Serial device` when neither name is available. Sort and deduplicate port paths.

Completion is advisory: callers can still enter custom paths or serialx URLs.
On enumeration failure, return no device candidates so manual connections remain
usable even when ctui invokes completion for dispatch-time prefix expansion.
