"""Exercise the real serialx POSIX backend over a Linux pseudo-terminal."""

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path

from ctui import MemoryHistory

from ctserial.commands import CtserialApp


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux pseudo-terminal test")
class SerialBackendTests(unittest.IsolatedAsyncioTestCase):
    """Verify connect, bytes on the wire, response collection, and port cleanup."""

    async def test_send_and_fuzz_over_real_serial_transport(self):
        import pty

        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        os.set_blocking(master, False)
        received = bytearray()
        loop = asyncio.get_running_loop()

        def respond():
            try:
                data = os.read(master, 4096)
            except BlockingIOError:
                return
            if data:
                received.extend(data)
                os.write(master, b"OK")

        loop.add_reader(master, respond)
        self.addCleanup(loop.remove_reader, master)
        with tempfile.TemporaryDirectory() as directory:
            app = CtserialApp(data_dir=Path(directory), history=MemoryHistory())
            try:
                async with asyncio.timeout(5):
                    await app.dispatch(f"connect {os.ttyname(slave)} 115200")
                    await app.dispatch("send hex deadc0de")
                    await app.dispatch('send utf8 "Hi 国"')
                    await app.dispatch("fuzz hex '0[0-2]'")
                    result = await app.dispatch("fuzz utf8 '国[0-1]'")
                    self.assertIn("Sent 2 payloads", result.output)
                    self.assertIn("OK", result.output)
                    self.assertEqual(
                        received,
                        bytes.fromhex("deadc0de")
                        + "Hi 国".encode()
                        + b"\x00\x01\x02"
                        + "国0国1".encode(),
                    )
                    session = app.session
                    await app.dispatch("close")
                    self.assertFalse(session.is_open)
                    self.assertIsNone(app.session)
            finally:
                await app.on_stop()
