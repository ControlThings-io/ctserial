# Copyright (C) 2018  Justin Searle
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details at <http://www.gnu.org/licenses/>.

import shlex
import re
import serial
import serial.tools.list_ports
import time

from ctui.application import Ctui
from ctui.dialogs import message_dialog
from tabulate import tabulate


class CtSerial(Ctui):
    """Commands that users may use at the application prompt."""
    name = 'ctmodbus'
    version = '0.5'
    description = 'a security professional\'s swiss army knife for interacting with Modbus devices'
    prompt = 'ctmodbus> '
    session = None
    unit_id = 1
    statusbar = 'Session:{}'.format(session)
    session = ''
    output_format = 'mixed'
    macro_hex = {}


    # def get_statusbar_text():
    #     sep = '  -  '
    #     session = get_app().session
    #     if type(session) == serial.Serial:
    #         device = 'connected:' + session.port
    #     else:
    #         device = 'connected:None'
    #     output_format = 'output:' + get_app().output_format
    #     return sep.join([device, output_format])


    def do_connect(self, args, output_text):
        """Generate a session with a single serial device to interact with it."""
        parts = args.split()
        devices = [x.device for x in serial.tools.list_ports.comports()]
        if len(parts) > 0:
            device = parts[0]
            if len(parts) > 1:
                baudrate = parts[1]
            else:
                baudrate = 9600
            if device in devices:
                self.session = serial.Serial(
                    port=device,
                    baudrate=baudrate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS)
                # initiate a serial session and return success message
                self.session.isOpen()
                output_text += 'Connect session opened with {}\n'.format(device)
                return output_text
        # return list of devices if command incomplete or incorrect
        message = 'Valid devices:\n' + ', \n'.join(devices) + '\n'
        message_dialog(title='Invalid Device', text=message)
        return False


    def do_close(self, args, output_text):
        """Close a session."""
        if type(self.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        else:
            device = self.session.port
            self.session.close()
            output_text += 'Session with {} closed.'.format(device) + '\n'
            self.session = ''
        return output_text


    def _send_instruction(self, session, tx_bytes):
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
            output = '\n\n{}'.format(e)
        time.sleep(0.1)
        return rx_raw


    def _format_output(self, raw_bytes, prefix=''):
        """ Return hex and utf-8 decodes aligned on two lines """
        if len(raw_bytes) == 0:
            return prefix + 'None'
        table = []
        if self.output_format == 'hex' or self.output_format == 'mixed':
            hex_out = [prefix] + list(bytes([x]).hex() for x in raw_bytes)
            table.append(hex_out)
        if self.output_format == 'ascii' or self.output_format == 'mixed':
            ascii_out = [' ' * len(prefix)] + list(raw_bytes.decode('ascii', 'replace'))
            table.append(ascii_out)
        if self.output_format == 'utf-8':
            # TODO: track \xefbfdb and replace with actual sent character
            utf8 = raw_bytes.decode('utf-8', 'replace')
            utf8_hex_out = [prefix] + list(x.encode('utf-8').hex() for x in utf8)
            utf8_str_out = [' ' * len(prefix)] + list(utf8)
            table = [utf8_hex_out, utf8_str_out]
        return tabulate(table, tablefmt="plain", stralign='right')


    def do_sendhex(self, args, output_text):
        """Send raw hex to serial device."""
        if type(self.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        data = args.lower().replace("0x", "")
        if re.match('^[0123456789abcdef\\\\x ]+$', data):
            raw_hex = re.sub('[\\\\x ]', '', data)
            if len(raw_hex) % 2 == 0:
                tx_bytes = bytes.fromhex(raw_hex)
                session = self.session
                rx_bytes = self._send_instruction(session, tx_bytes)
                output_text += self._format_output(tx_bytes, prefix='--> ') + '\n'
                output_text += self._format_output(rx_bytes, prefix='<-- ') + '\n'
                return output_text
        return False


    def do_send(self, args, output_text):
        """Send string to serial device."""
        if type(self.session) != serial.Serial:
            output_text += 'Connect to a device first\n'
            return output_text
        if len(args) > 0:
            # remove spaces not in quotes and format
            string = ''.join(shlex.split(args))
            tx_bytes = bytes(string, encoding='utf-8')
            session = self.session
            rx_bytes = self._send_instruction(session, tx_bytes)
            output_text += self._format_output(tx_bytes, prefix='--> ') + '\n'
            output_text += self._format_output(rx_bytes, prefix='<-- ') + '\n'
            return output_text
        return False


    def do_macro_set(self, args, output_text):
        v1 = args[: args.find(' ')]
        v2 = args[args.find(' '): ]
        self.macro_hex[v1] = v2
        output_text += "key " + v1 + " set to value " + v2 + "\n"
        return output_text


    def do_macro_send(self, args, output_text):
        macro = self.macro_hex[args]
        if macro:
            return self.do_sendhex(macro, output_text)
        output_text += 'Unknown macro\n'
        return output_text




def main():
    ctserial = CtSerial()
    ctserial.run()

if __name__ == '__main__':
    main()
