# Copyright (C) 2021  Justin Searle
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details at <http://www.gnu.org/licenses/>.

"""Typed UI/CLI commands and the lifecycle of one asynchronous serial session.

The connection lock covers connect, close, and complete send/fuzz operations so
concurrent UI commands cannot mix responses or close a port during an exchange.
Transaction output is an in-memory rolling window; ctui owns project history.
"""

import asyncio
import sys
from collections import deque
from importlib.metadata import version
from typing import TextIO

import serialx
from ctui import (
    Argument,
    CommandError,
    CommandResult,
    CtuiApp,
    FuzzyHexPattern,
    FuzzyStringPattern,
    HexBytes,
    command,
)
from tabulate import tabulate

from ctserial import common

PARITIES = {parity.name.lower(): parity for parity in serialx.Parity}


class CtserialApp(CtuiApp):
    """Interact with one serial device through ctui's shared UI/CLI dispatcher.

    session is owned by this instance and closed by on_stop in UI and CLI modes.
    Only the most recent 1,000 transaction rows are retained for display.
    """

    name = "ctserial"
    version = version("ctserial")
    description = "A security professional's tool for interacting with serial devices"
    prompt = "ctserial> "
    app_id = "io.controlthings.ctserial"

    def __init__(self, **kwargs):
        """Initialize runtime state; forward service configuration to CtuiApp."""
        super().__init__(**kwargs)
        self.session: serialx.AsyncSerial | None = None
        self.device: str | None = None
        self.transactions: deque[list[str]] = deque(maxlen=1000)
        self._connection_lock = asyncio.Lock()
        self._cli_stdout: TextIO | None = None
        self.statusbar = self.connection_status

    async def run_cli(
        self, arguments, *, stdout=None, stderr=None, program=None
    ) -> int:
        """Run a CLI batch, streaming fuzz rows to its selected output stream.

        Keep ctui's parsing, lifecycle, and exit statuses. Bind the stream only
        for this invocation so headless dispatch never prints implicitly.
        """
        self._cli_stdout = stdout if stdout is not None else sys.stdout
        try:
            return await super().run_cli(
                arguments, stdout=stdout, stderr=stderr, program=program
            )
        finally:
            self._cli_stdout = None

    def connection_status(self) -> str:
        """Return the active ctui project and serial device for the status bar."""
        project = self.backend.current if self.backend is not None else None
        project_name = project.name if project is not None else "default"
        connection = self.device if self.session is not None else "disconnected"
        return f"PROJECT: {project_name} | Connection: {connection}"

    @command
    async def devices(self) -> str:
        """List available serial devices, manufacturers, and products."""
        try:
            return await common.list_serial_devices()
        except (OSError, serialx.SerialException) as error:
            raise CommandError(f"Could not list serial devices: {error}") from error

    @command(
        arguments={
            "device": Argument(
                help="Serial device path, COM port, or serialx URL",
                completer=common.serial_device_suggestions,
            ),
            "baudrate": Argument(
                help="Baud rate (default: 9600)", validator=lambda value: value > 0
            ),
            "parity": Argument(help="Parity (default: none)", choices=PARITIES),
        }
    )
    async def connect(
        self, device: str, baudrate: int = 9600, parity: str = "none"
    ) -> str:
        """Open a serial device with eight data bits and one stop bit.

        Open the supplied path directly, including symlinks and virtual ports
        that device enumeration may omit. An existing connection must be closed
        first. Failed opens leave the application disconnected.
        """
        async with self._connection_lock:
            if self.session is not None:
                raise CommandError("Session already open. Close it first.")
            session = serialx.async_serial_for_url(
                device,
                baudrate=baudrate,
                parity=PARITIES[parity],
                stopbits=serialx.StopBits.ONE,
                byte_size=8,
            )
            try:
                await session.open()
            except (OSError, ValueError, serialx.SerialException) as error:
                raise CommandError(f"Could not connect to {device}: {error}") from error
            self.session, self.device = session, device
            return f"Session OPENED with {device}"

    async def _close_session(self) -> None:
        """Close while holding the connection lock; clear state even on failure."""
        try:
            if self.session is not None:
                await self.session.close()
        finally:
            self.session = None
            self.device = None

    @command
    async def close(self) -> str:
        """Close the open serial session after any active send or fuzz command."""
        async with self._connection_lock:
            self._require_session()
            device = self.device
            try:
                await self._close_session()
            except (OSError, serialx.SerialException) as error:
                raise CommandError(f"Could not close {device}: {error}") from error
            return f"Session with {device} CLOSED"

    async def on_stop(self) -> None:
        """Release the serial connection on normal exit or CLI command failure."""
        async with self._connection_lock:
            await self._close_session()

    def _require_session(self) -> serialx.AsyncSerial:
        """Return the session or raise a user-facing error before sending."""
        if self.session is None:
            raise CommandError("There is not an open session. Connect to one first.")
        return self.session

    def _record(self, direction: str, data: bytes) -> None:
        """Append one unwrapped row with grouped hex and a safe UTF-8 decode."""
        self.transactions.append(
            [
                direction,
                common.bytes2hexstr(data, group=8, sep=" "),
                common.bytes_decode(data),
            ]
        )

    def _transaction_table(self) -> str:
        """Render the retained transaction rows with their column labels."""
        return tabulate(
            self.transactions, headers=["DIR", "RAW HEX", "UTF-8"], tablefmt="plain"
        )

    def _show_fuzz_progress(self, *, summary: str | None = None) -> None:
        """Present the current fuzz transaction before the next exchange starts.

        Replace the rolling UI table and request a redraw, or print/flush just
        the latest row to the CLI's selected stream. A summary updates only the
        UI; CLI completion is returned through ctui. Headless dispatch updates
        output_text without printing or requiring terminal resources.
        """
        table = self._transaction_table()
        self.output_text = f"{summary}\n{table}" if summary else table
        if self._cli_stdout is not None:
            if summary is None:
                print(
                    tabulate([self.transactions[-1]], tablefmt="plain"),
                    file=self._cli_stdout,
                    flush=True,
                )
        elif hasattr(self, "layout"):
            self.layout.set_output(self.output_text)
            self.app.invalidate()

    async def _exchange(self, data: bytes, *, show_progress: bool = False) -> None:
        """Record a send and its response while the caller holds the lock.

        No response is a visible transaction result, allowing fuzzing to continue.
        I/O/size failures stop the command; cancellation propagates unchanged.
        The sent row remains visible even if receiving fails.
        With show_progress, present the TX row before waiting and the RX/error
        row immediately afterwards, including when the command fails midway.
        """
        session = self._require_session()
        self._record("-->", data)
        if show_progress:
            self._show_fuzz_progress()
        try:
            response = await common.send_instruction(session, data)
        except (OSError, ValueError, serialx.SerialException) as error:
            self.transactions.append(["!", "", str(error)])
            if show_progress:
                self._show_fuzz_progress()
            raise CommandError(f"Serial exchange failed: {error}") from error
        if response:
            self._record("<--", response)
        else:
            self.transactions.append(["<--", "", "No response received"])
        if show_progress:
            self._show_fuzz_progress()

    @command(arguments={"data": Argument(help="Hexadecimal bytes; quote separators")})
    async def send_hex(self, data: HexBytes) -> str:
        """Send bytes parsed by ctui's HexBytes and show the transaction table."""
        async with self._connection_lock:
            await self._exchange(data)
            return self._transaction_table()

    @command(
        arguments={
            "data": Argument(
                help="Text to encode as UTF-8; quote spaces and backslashes"
            )
        }
    )
    async def send_utf8(self, data: str) -> str:
        """Encode ctui's parsed string as UTF-8 and show the transaction table.

        Shell-like quoting is handled once by ctui. Preserve the resulting text,
        including spaces and literal backslashes; do not interpret byte escapes.
        """
        async with self._connection_lock:
            await self._exchange(data.encode("utf-8"))
            return self._transaction_table()

    @command(
        arguments={
            "pattern": Argument(help="Finite hex pattern, e.g. 'de[0-3]?'"),
            "limit": Argument(
                help="Maximum complete expansion (default: 256; maximum: 65536)",
                flags=("--limit",),
                validator=lambda value: 1 <= value <= 65_536,
            ),
        }
    )
    async def fuzz_hex(
        self, pattern: FuzzyHexPattern, limit: int = 256
    ) -> str | CommandResult:
        """Send every expansion in order, waiting for each response before sending.

        Reject patterns exceeding --limit before any bytes are sent. The whole
        sequence holds the connection lock. I/O failure or cancellation stops the
        sequence without retrying; a missing response continues to the next value.
        Show every send and response as it happens.
        """
        return await self._fuzz(pattern, limit)

    @command(
        arguments={
            "pattern": Argument(help="Finite string pattern, e.g. 'user[0-3]'"),
            "limit": Argument(
                help="Maximum complete expansion (default: 256; maximum: 65536)",
                flags=("--limit",),
                validator=lambda value: 1 <= value <= 65_536,
            ),
        }
    )
    async def fuzz_utf8(
        self, pattern: FuzzyStringPattern, limit: int = 256
    ) -> str | CommandResult:
        """Expand a finite string pattern and send each result encoded as UTF-8.

        Apply the same limits, sequential exchanges, and failure behavior as
        fuzz hex. Quote patterns containing spaces or backslashes.
        """
        return await self._fuzz(pattern, limit)

    async def _fuzz(
        self, pattern: FuzzyHexPattern | FuzzyStringPattern, limit: int
    ) -> str | CommandResult:
        """Validate the complete expansion before sending bytes or UTF-8 strings.

        Hold the connection lock for the full sequence. Keep generation lazy and
        the display window bounded even when an explicitly raised limit is used.
        """
        try:
            payloads = pattern.expand(limit=limit)
        except ValueError as error:
            raise CommandError(str(error)) from error
        async with self._connection_lock:
            self._require_session()
            for payload in payloads:
                data = payload.encode("utf-8") if isinstance(payload, str) else payload
                await self._exchange(data, show_progress=True)
                # Let the UI render the response before starting another exchange.
                await asyncio.sleep(0)
            summary = f"Sent {pattern.count:,} payloads."
            self._show_fuzz_progress(summary=summary)
            if self._cli_stdout is not None:
                return summary
            if hasattr(self, "layout"):
                return CommandResult.success()
            return self.output_text


def main() -> None:
    """Run the interactive UI or ctui's automatic CLI with lifecycle cleanup."""
    CtserialApp().run()


if __name__ == "__main__":
    main()
