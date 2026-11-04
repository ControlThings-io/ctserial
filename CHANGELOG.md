# v0.6.0 (unreleased)

* Keep each sent/received payload on one line, preserving four-byte hex groups
  and displaying only the UTF-8 decode.
* Display fuzz sends, responses, and errors as each exchange happens in the UI
  and CLI, preserving progress if a later attempt fails.
* Correct package metadata to GPL-3.0-or-later, matching LICENSE and source headers,
  and include LICENSE in both distribution formats.
* Upgrade to ctui 1.0 and its typed, asynchronous UI/CLI application API.
* Require Python 3.11 or later; drop Python 3.8–3.10 support.
* Replace pyserial with serialx and use native asynchronous serial exchanges.
* Parse `send hex` with ctui's `HexBytes`.
* Parse `send utf8` once with ctui's string conversion, then encode as UTF-8.
* Add `fuzz hex` with `FuzzyHexPattern` and `fuzz utf8` with `FuzzyStringPattern`.
  Both expand lazily, validate limits before sending, and send sequentially.
* Add a `devices` command and support directly opening paths, symlinks, and
  serialx URLs without requiring an enumeration match.
* Serialize session operations, bound response collection and transaction output,
  and close connections on UI/CLI shutdown.
* Add regression, Linux pseudo-terminal, and installed-artifact smoke tests.
* Replace obsolete Poetry development instructions with uv documentation.

See [README.md](README.md#compatibility-changes-in-060) for compatibility changes
and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for publication steps.

# v0.4.0 (2021-04-23)

* Migration of build environment to Poetry
* Changes for ctui v0.7 compatibility
* Changed output of tool to tables
* Automatic ASCII or UTF-8 decodes based on content
* Enhanced serial device search and information

Note: Macros and ability to use spaces in hex strings temporarily removed but will be added back in the next release
