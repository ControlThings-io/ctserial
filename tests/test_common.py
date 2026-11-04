"""Verify asynchronous response boundaries, failures, and byte presentation."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import serialx

from ctserial import common


class ExchangeTests(unittest.IsolatedAsyncioTestCase):
    """A controllable async stream avoids requiring physical serial hardware."""

    async def asyncSetUp(self):
        self.session = AsyncMock(spec=serialx.AsyncSerial)

    async def test_collects_chunks_until_idle(self):
        async def read(_size):
            if chunks:
                return chunks.pop(0)
            await asyncio.sleep(10)

        chunks = [b"one", b"two"]
        self.session.read.side_effect = read
        result = await common.send_instruction(self.session, b"ping", idle_timeout=0.01)
        self.assertEqual(result, b"onetwo")
        self.session.write.assert_awaited_once_with(b"ping")

    async def test_no_response_times_out_without_blocking_loop(self):
        ticked = asyncio.Event()

        async def read(_size):
            ticked.set()
            await asyncio.sleep(10)

        self.session.read.side_effect = read
        result = await common.send_instruction(self.session, b"ping", timeout=0.01)
        self.assertEqual(result, b"")
        self.assertTrue(ticked.is_set())

    async def test_continuous_response_has_overall_deadline(self):
        async def read(_size):
            await asyncio.sleep(0.002)
            return b"x"

        self.session.read.side_effect = read
        async with asyncio.timeout(1):
            result = await common.send_instruction(self.session, b"ping", timeout=0.02)
        self.assertTrue(result)

    async def test_response_size_is_bounded(self):
        self.session.read.return_value = b"12345"
        with self.assertRaisesRegex(ValueError, "exceeds 4 bytes"):
            await common.send_instruction(self.session, b"ping", max_response=4)

    async def test_eof_is_connection_error(self):
        self.session.read.return_value = b""
        with self.assertRaises(ConnectionError):
            await common.send_instruction(self.session, b"ping")

    async def test_io_failure_propagates(self):
        self.session.write.side_effect = OSError("disconnected")
        with self.assertRaisesRegex(OSError, "disconnected"):
            await common.send_instruction(self.session, b"ping")
        self.session.read.assert_not_awaited()

    async def test_write_timeout_is_an_error(self):
        async def write(_data):
            await asyncio.sleep(10)

        self.session.write.side_effect = write
        with self.assertRaises(TimeoutError):
            await common.send_instruction(self.session, b"ping", timeout=0.01)
        self.session.read.assert_not_awaited()

    async def test_backend_read_timeout_is_not_silenced(self):
        self.session.read.side_effect = TimeoutError("backend timed out")
        with self.assertRaisesRegex(TimeoutError, "backend timed out"):
            await common.send_instruction(self.session, b"ping")

    async def test_cancellation_propagates(self):
        self.session.read.side_effect = asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):
            await common.send_instruction(self.session, b"ping")

    async def test_device_table_uses_serialx_attributes(self):
        ports = [
            SimpleNamespace(device="COM2", manufacturer=None, product=None),
            SimpleNamespace(device="COM1", manufacturer="Maker", product="Adapter"),
        ]
        with patch("ctserial.common.async_list_serial_ports", return_value=ports):
            result = await common.list_serial_devices()
        self.assertLess(result.index("COM1"), result.index("COM2"))
        self.assertIn("Adapter", result)


class PresentationTests(unittest.TestCase):
    """Keep binary output readable even for control bytes and invalid Unicode."""

    def test_control_bytes_are_replaced(self):
        output = common.bytes_decode(b"\x00\x1bHello\xff")
        self.assertNotIn("\x1b", output)
        self.assertIn("Hello", output)

    def test_utf8_decode_and_hex_grouping(self):
        self.assertIn("UTF-8: 国", common.bytes_decode("国".encode()))
        self.assertEqual(common.bytes2hexstr(b"\xde\xad\xc0\xde", group=4), "dead c0de")
