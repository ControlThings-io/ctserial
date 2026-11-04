# ControlThings Serial

A flexible serial interface tool for penetration testers, with an interactive
terminal UI and a command-line interface powered by ctui.

## Installation

ctserial 0.6.0 requires **Python 3.11 or later**. Install with pip:

```bash
python -m pip install ctserial
```

Or use an isolated environment with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ctserial
# Try it without installing:
uvx ctserial
```

Serial communication uses [serialx](https://puddly.github.io/serialx/), which
supports Linux, macOS, and Windows. Your account needs access to the serial port.

## Interactive usage

Start `ctserial`, then enter commands in its terminal UI:

```text
ctserial> devices
ctserial> connect /dev/ttyUSB0 115200 none
ctserial> send hex deadc0de
ctserial> send hex "de ad c0 de"
ctserial> send utf8 "Dead Code 国"
ctserial> fuzz hex "de[0-3]?"
ctserial> fuzz utf8 "user[0-3]"
ctserial> close
ctserial> exit
```

`connect DEVICE [BAUDRATE] [PARITY]` defaults to 9600 baud and no parity, using
8 data bits and 1 stop bit. Parity can be `none`, `even`, `odd`, `mark`, or `space`.
Use a device path, symlink, Windows COM port, or a serialx URL. Paths are opened
directly, including virtual ports omitted from `devices`.

`send hex` uses ctui's `HexBytes` conversion. It accepts contiguous hexadecimal,
byte separators, `0x` prefixes, and `\xNN` notation. Quote values containing spaces
or backslashes, for example `send hex '\xde\xad'`.

`send utf8` accepts one string argument and encodes it as UTF-8. Quote text
containing spaces. Quoting is parsed once by ctui; literal backslashes remain
literal, so `send utf8 '\n'` sends a backslash and `n`. Use `send hex 0a` for a
newline byte. ctui 1.0.0 does not provide a `StringBytes` type.

### Fuzzing

`fuzz hex PATTERN` uses ctui's `FuzzyHexPattern`. `?` matches any hexadecimal
nibble, `[0-3]` selects a range, and `{n}` repeats the preceding atom. For example,
`fuzz hex "de[0-3]?"` sends 64 two-byte payloads in expansion order.

`fuzz utf8 PATTERN` uses ctui's `FuzzyStringPattern` and encodes each generated
string as UTF-8. It supports character classes, literal alternatives such as
`{admin,user}`, fixed repetition, Unicode literals, and ASCII wildcard classes
such as `\d`. For example:

```text
ctserial> fuzz utf8 "国{admin,user}[0-1]"
ctserial> fuzz utf8 'user\d' --limit 10
ctserial> fuzz hex "??" --limit 256
```

Both commands expand lazily and send one payload at a time, waiting for each
response. The UI updates after every send and receive; CLI output flushes each
transaction row immediately. The default maximum is 256 payloads. Set `--limit N`
to change it, up to 65,536. A pattern larger than the limit is rejected before
sending anything; it is never silently truncated. A missing response is displayed
as `No response received` and fuzzing continues; an I/O error stops the sequence. A running fuzz command holds the connection
until it finishes or is cancelled, so other sends and `close` wait their turn.

### Responses and projects

Each exchange has a one-second write/response deadline. After the first response
bytes, 100 ms of silence ends collection. A response larger than 65,536 bytes
raises an error. These timing boundaries do not identify protocol frames; late
bytes remain buffered and may appear in the next exchange. Adjust the application
for protocols requiring explicit framing or different timings.

The UI displays the most recent 1,000 transaction rows with hexadecimal, ASCII,
and UTF-8 decodes. Transaction rows are kept in memory. ctui's project commands
manage persistent command history in the platform's user-data directory. The
status bar shows the active project and connection. Serial ports close on exit,
including CLI command failures.

### Command-line usage

Use repeatable `--command` (or `-c`) arguments to keep one session across commands:

```bash
ctserial -c 'connect /dev/ttyUSB0 115200' \
  -c 'send hex deadc0de' \
  -c 'fuzz utf8 "user[0-3]"' \
  -c close
ctserial --help
ctserial help fuzz hex
```

Use `--file commands.txt` for a UTF-8 command file with one command per line.
Blank lines and lines starting with `#` are ignored. Execution stops at the first
error. The connection closes automatically when the batch ends.

## Compatibility changes in 0.6.0

- Python 3.8–3.10 are no longer supported because ctui 1.0 requires Python 3.11+.
- The application uses ctui's `CtuiApp`/`@command` API and serialx's native async
  API. pyserial is no longer a dependency.
- Use `send utf8 "text with spaces"`; bare `send TEXT` and joining multiple
  unquoted words are unsupported. UTF-8 input is parsed only once.
- Hexadecimal syntax follows ctui's validation rather than stripping arbitrary
  prefixes and separators.
- ctui 1.0 project storage differs from ctui 0.8; old project data is not imported
  automatically. Transaction output remains in memory.

## Development

```bash
git clone https://github.com/ControlThings-io/ctserial.git
cd ctserial
uv sync --locked --python 3.11
uv run python -m unittest discover -s tests -v
uv run black --check src tests
uv run isort --check-only src tests
uv lock --check
```

The Linux integration test uses a pseudo-terminal with the real serialx backend;
no physical serial device is required. It is skipped on other platforms.
See [current status](docs/STATUS.md), [decisions](docs/DECISIONS.md), and the
[release checklist](RELEASE_CHECKLIST.md) for validation gaps and release steps.

## Author

Justin Searle <justin@controlthings.io>
