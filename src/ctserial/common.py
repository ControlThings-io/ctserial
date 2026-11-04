"""
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
"""

import asyncio
import math
import unicodedata
from textwrap import wrap

from ctui import CompletionContext, CompletionItem
from serialx import AsyncSerial, SerialException, async_list_serial_ports
from tabulate import tabulate


async def serial_device_suggestions(
    _context: CompletionContext,
) -> list[CompletionItem]:
    """Suggest current native port paths with device-reported name details.

    Enumerate asynchronously without opening ports. Prefer resolved native
    paths, such as /dev/ttyACM0, over serialx's stable symlinks. Trim
    descriptor padding and omit missing fields; no USB database names or IDs
    are used. Deduplicate paths and sort suggestions by path.

    Return no suggestions on enumeration failure so manually entered paths and
    URLs remain usable, including during ctui's dispatch-time prefix expansion.
    """
    try:
        devices = await async_list_serial_ports()
    except (OSError, SerialException):
        return []
    suggestions = {}
    for device in devices:
        path = device.resolved_device or device.device
        details = " | ".join(
            replace_control_characters(value.strip())
            for value in (device.manufacturer, device.product)
            if value and value.strip()
        )
        suggestions.setdefault(path, CompletionItem(path, details or "Serial device"))
    return [suggestions[path] for path in sorted(suggestions)]


async def list_serial_devices() -> str:
    """Return a device table using serialx's asynchronous port enumeration."""
    devices = await async_list_serial_ports()
    rows = sorted(
        (dev.device, dev.manufacturer or "", dev.product or "") for dev in devices
    )
    return tabulate(
        rows, headers=["DEVICE", "MANUFACTURER", "PRODUCT"], tablefmt="fancy_grid"
    )


async def send_instruction(
    session: AsyncSerial,
    tx_bytes: bytes,
    *,
    timeout: float = 1.0,
    idle_timeout: float = 0.1,
    max_response: int = 65_536,
) -> bytes:
    """Write bytes and collect a response without blocking the event loop.

    Wait at most timeout seconds for writing and reading together. After the
    first chunk, idle_timeout seconds of silence ends the response. Return b""
    when no response arrives, or the accumulated bytes at the overall deadline.
    These timing boundaries cannot identify protocol frames; late bytes remain
    buffered for the next read. Never discard pending input implicitly.

    Read at most max_response bytes; raise ValueError if the response exceeds
    that cap. EOF raises ConnectionError. I/O failures and cancellation propagate.
    Callers must serialize exchanges on each connection.
    """
    if not all(math.isfinite(value) and value > 0 for value in (timeout, idle_timeout)):
        raise ValueError("Response timeouts must be finite and positive")
    if max_response < 1:
        raise ValueError("Response byte limit must be positive")
    response = bytearray()
    deadline = asyncio.get_running_loop().time() + timeout
    # A write timeout is an error: the caller cannot know how much was sent.
    async with asyncio.timeout(timeout):
        await session.write(tx_bytes)
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            return bytes(response)
        wait = min(remaining, idle_timeout) if response else remaining
        read_timeout = asyncio.timeout(wait)
        try:
            async with read_timeout:
                chunk = await session.read(min(4096, max_response + 1 - len(response)))
        except TimeoutError:
            if read_timeout.expired():
                return bytes(response)
            raise
        if not chunk:
            raise ConnectionError(
                "Serial connection closed while waiting for a response"
            )
        response.extend(chunk)
        if len(response) > max_response:
            raise ValueError(f"Response exceeds {max_response:,} bytes")


def bytes2hexstr(
    raw_bytes: bytes, group: int = 0, sep: str = " ", line: int = 0
) -> str:
    """Return lowercase hex, optionally grouping digits and wrapping text.

    group counts hexadecimal characters, not bytes. Zero disables grouping or
    line wrapping; line uses textwrap's whitespace-aware wrapping semantics.
    """
    hexstr = raw_bytes.hex()
    if group:
        hexstr = sep.join(hexstr[i : i + group] for i in range(0, len(hexstr), group))
    if line:
        hexstr = "\n".join(wrap(hexstr, line))
    return hexstr


def replace_control_characters(string: str) -> str:
    """Replace Unicode controls and line/paragraph separators to keep one row."""
    safe_string = []
    for char in string:
        category = unicodedata.category(char)
        if category[0] != "C" and category not in ("Zl", "Zp"):
            safe_string.append(char)
        else:
            safe_string.append("\ufffd")
    return "".join(safe_string)


def bytes2ascii(raw_bytes: bytes) -> str:
    """Decode ASCII with replacement and remove terminal control characters."""
    return replace_control_characters(raw_bytes.decode("ascii", "replace"))


def bytes2utf8(raw_bytes: bytes) -> str:
    """Decode UTF-8 with replacement and remove terminal control characters."""
    return replace_control_characters(raw_bytes.decode("utf-8", "replace"))


def bytes_decode(raw_bytes: bytes) -> str:
    """Return only safe UTF-8 text, replacing invalid bytes and control characters.

    Column headers supply the encoding label; decoded data has no prefix or
    additional ASCII representation. Embedded CR/LF bytes cannot split a row.
    """
    return bytes2utf8(raw_bytes)
