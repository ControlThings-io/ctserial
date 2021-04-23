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

import operator
import time
import unicodedata
from textwrap import wrap

from ctui.dialogs import message_dialog
from serial.tools.list_ports import comports
from tabulate import tabulate


def validate_serial_device(device):
    """
    Verify requested serial device is connected to the system

    :PARAM: device: A device file path or comm port
    """
    devices = [x.device for x in comports()]
    assert device in devices, "{} is not in: \n{} ".format(
        device, list_serial_devices()
    )
    return device


def list_serial_devices():
    headers = ["DEVICE", "MANUFACTURER", "PRODUCT ID"]
    rows = []
    for dev in comports():
        columns = []
        columns.append(dev.device)
        columns.append(dev.manufacturer)
        columns.append(dev.product)
        rows.append(columns)
    table = sorted(rows, key=operator.itemgetter(0))
    return tabulate(table, headers=headers, tablefmt="fancy_grid")


def send_instruction(session, tx_bytes):
    """Send data to serial device"""
    # clear out any leftover data
    try:
        rx_raw = bytes()
        if session.inWaiting() > 0:
            session.flushInput()
        session.write(tx_bytes)
        time.sleep(0.1)
        while session.inWaiting() > 0:
            rx_raw += session.read()
    except BaseException as e:
        message_dialog("ERROR", "\n\n{}".format(e))
    time.sleep(0.1)
    return rx_raw


def format_output(raw_bytes, prefix="", output_format="utf-8"):
    """ Return hex and utf-8 decodes aligned on two lines """
    if len(raw_bytes) == 0:
        return prefix + "None"
    table = []
    if output_format == "hex" or output_format == "mixed":
        hex_out = [prefix] + list(bytes([x]).hex() for x in raw_bytes)
        table.append(hex_out)
    if output_format == "ascii" or output_format == "mixed":
        ascii_out = [" " * len(prefix)] + list(raw_bytes.decode("ascii", "replace"))
        table.append(ascii_out)
    if output_format == "utf-8":
        # TODO: track \xefbfdb and replace with actual sent character
        utf8 = raw_bytes.decode("utf-8", "replace")
        utf8_hex_out = [prefix] + list(x.encode("utf-8").hex() for x in utf8)
        utf8_str_out = [" " * len(prefix)] + list(utf8)
        table = [utf8_hex_out, utf8_str_out]
    return tabulate(table, tablefmt="plain", stralign="right")


# def bytes2hexstr(raw_bytes, count=0, sep=" ", length=len(raw_bytes)):
#     hexstr = raw_bytes.hex()
#     lines = []
#     for i in range(0, len(hexstr), length):
#         line = hexstr[i : i + length]
#         lines.append(sep.join(line[i : i + count] for i in range(0, len(line), count)))
#         if i + length < len(hexstr):
#             lines.append("\n")
#     return "".join(lines)


def bytes2hexstr(raw_bytes, group=0, sep=" ", line=0):
    hexstr = raw_bytes.hex()
    if group:
        hexstr = sep.join(hexstr[i : i + group] for i in range(0, len(hexstr), group))
    if line:
        hexstr = "\n".join(wrap(hexstr, line))
    return hexstr


def replace_control_characters(string):
    safe_string = []
    for char in string:
        if unicodedata.category(char)[0] != "C":
            safe_string.append(char)
        else:
            safe_string.append("\ufffd")
    return "".join(safe_string)


def bytes2ascii(raw_bytes):
    ascii = raw_bytes.decode("ascii", "replace")
    safe_ascii = replace_control_characters(ascii)
    return safe_ascii


def bytes2utf8(raw_bytes):
    utf8 = raw_bytes.decode("utf-8", "replace")
    safe_utf8 = replace_control_characters(utf8)
    return safe_utf8


def bytes_decode(raw_bytes):
    ascii = bytes2ascii(raw_bytes)
    utf8 = bytes2utf8(raw_bytes)
    if ascii == utf8:
        return f"ASCII: {ascii}"
    else:
        return f"ASCII: {ascii}\nUTF-8: {utf8}"
