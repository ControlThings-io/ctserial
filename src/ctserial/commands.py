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

import re
import shlex
from datetime import datetime

from ctui import Ctui
from ctui.dialogs import message_dialog
from pkg_resources import get_distribution
from serial import (
    EIGHTBITS,
    PARITY_EVEN,
    PARITY_MARK,
    PARITY_NONE,
    PARITY_ODD,
    PARITY_SPACE,
    STOPBITS_ONE,
    Serial,
)
from tabulate import tabulate

from ctserial import common

ctserial = Ctui()
ctserial.name = "ctserial"
ctserial.version = get_distribution("ctserial").version
ctserial.description = (
    "a security professional's swiss army knife for interacting with serial devices"
)
ctserial.prompt = "ctserial> "
ctserial.session = None
# ctserial.statusbar = f"Session:{ctserial.session.port}"
ctserial.output_format = "mixed"
ctserial.macros = {}


@ctserial.command
def do_connect(device: str = "/dev/null/", baudrate: int = 9600, parity=PARITY_NONE):
    """
    Connect to a serial device

    :PARAM: device: Serial device path or COM port
    :PARAM: baudrate: Defaults to 9600. Most standard rates from 75 to 4000000 supported.
    :PARAM: parity: Defaults to none. Can also be even, odd, mark, or space
    """
    assert (
        ctserial.session == None
    ), "Session already open.  Close first."  # ToDo assert session type
    valid_device = common.validate_serial_device(device)
    parities = {
        "none": PARITY_NONE,
        "even": PARITY_EVEN,
        "odd": PARITY_ODD,
        "mark": PARITY_MARK,
        "space": PARITY_SPACE,
    }
    assert (
        parity in parities.keys()
    ), "Parity must be none (default), even, odd, mark, or space"
    s = Serial(
        port=valid_device,
        baudrate=baudrate,
        parity=parities[parity],
        stopbits=STOPBITS_ONE,
        bytesize=EIGHTBITS,
    )
    assert s.isOpen(), f"Could not connect to {valid_device}"
    ctserial.session = s
    date, time = str(datetime.today()).split()
    return (
        ctserial.output_text
        + f"{date} {time} - ASCII session OPENED with {valid_device}\n"
    )


@ctserial.command
def do_close():
    """
    Close the open session
    """
    assert (
        ctserial.session
    ), "There is not an open session.  Connect to one first."  # ToDo assert session type
    ctserial.session.close()
    ctserial.session = None
    date, time = str(datetime.today()).split()
    return (
        ctserial.output_text
        + f"{date} {time} - Session with {ctserial.session.port} CLOSED\n"
    )


@ctserial.command
def do_send():
    """Various send functions..."""


@ctserial.command
def do_send_hex(data: str):
    """
    Send raw hex to serial device, ignoring spaces \\x and 0x.

    :PARAM: data: Raw hex to send.
    """
    assert (
        ctserial.session
    ), "There is not an open session.  Connect to one first."  # ToDo assert session type
    raw_hex = data.lower().replace("0x", "").replace("\\x", "").replace(" ", "")
    assert re.match("^[0123456789abcdef]+$", raw_hex), "Only hex characters allowed"
    assert len(raw_hex) % 2 != 0, "You must send an even number of hex characters"
    tx_bytes = bytes.fromhex(raw_hex)
    rx_bytes = common.send_instruction(ctserial.session, tx_bytes)
    output_text = ctserial.output_text
    output_text += common.format_output(tx_bytes, "--> ", ctserial.output_format) + "\n"
    output_text += common.format_output(rx_bytes, "<-- ", ctserial.output_format) + "\n"
    return output_text


@ctserial.command
def do_send_utf8(data: str):
    """
    Send UTF-8 string to serial device.

    :PARAM: data: UTF-8 string to send.
    """
    assert (
        ctserial.session
    ), "There is not an open session.  Connect to one first."  # ToDo assert session type
    utf8_str = "".join(shlex.split(data))  # remove spaces not in quotes and format
    tx_bytes = bytes(utf8_str, encoding="utf-8")
    rx_bytes = common.send_instruction(ctserial.session, tx_bytes)
    output_text = ctserial.output_text
    output_text += common.format_output(tx_bytes, "--> ", ctserial.output_format) + "\n"
    output_text += common.format_output(rx_bytes, "<-- ", ctserial.output_format) + "\n"
    return output_text


def main():
    ctserial.run()


if __name__ == "__main__":
    main()
