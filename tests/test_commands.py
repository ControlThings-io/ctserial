"""Regression tests through ctui's real typed dispatcher and CLI lifecycle."""

import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import serialx
from ctui import CommandError, CommandValidationError, MemoryHistory

from ctserial.commands import CtserialApp


class CommandTests(unittest.IsolatedAsyncioTestCase):
    """Exercise conversion, connection ownership, and serialized exchanges."""

    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = CtserialApp(
            data_dir=Path(self.directory.name), history=MemoryHistory()
        )
        self.session = AsyncMock(spec=serialx.AsyncSerial)
        self.app.session, self.app.device = self.session, "/dev/test"
        self.exchange = patch(
            "ctserial.commands.common.send_instruction", new_callable=AsyncMock
        )
        self.send = self.exchange.start()
        self.send.return_value = b"OK"
        self.addCleanup(self.exchange.stop)
        self.addAsyncCleanup(self.app.on_stop)

    async def test_hex_representations_use_ctui_conversion(self):
        for data in (
            "deadc0de",
            "'de ad c0 de'",
            "'de:ad:c0:de'",
            r"'\xde\xad\xc0\xde'",
        ):
            with self.subTest(data=data):
                result = await self.app.dispatch(f"send hex {data}")
                self.assertIn("deadc0de", result.output)
                self.send.assert_awaited_with(self.session, bytes.fromhex("deadc0de"))

    async def test_invalid_hex_never_sends(self):
        for data in ("abc", "zz", "'de-ad:c0'", "'de ad' extra"):
            with self.subTest(data=data):
                with self.assertRaises(CommandValidationError):
                    await self.app.dispatch(f"send hex {data}")
        self.send.assert_not_awaited()

    async def test_utf8_preserves_spaces_unicode_quotes_and_backslashes(self):
        cases = {
            'send utf8 "Dead Code 国"': "Dead Code 国".encode(),
            'send utf8 "O\'Reilly"': b"O'Reilly",
            r"send utf8 '\n'": b"\\n",
        }
        for command, payload in cases.items():
            with self.subTest(command=command):
                await self.app.dispatch(command)
                self.send.assert_awaited_with(self.session, payload)

    async def test_fuzz_hex_expands_in_order(self):
        result = await self.app.dispatch("fuzz hex 'de[0-1][a-b]'")
        self.assertIn("Sent 4 payloads", result.output)
        self.assertEqual(
            [call.args[1] for call in self.send.await_args_list],
            [bytes.fromhex(value) for value in ("de0a", "de0b", "de1a", "de1b")],
        )

    async def test_fuzz_utf8_encodes_generated_strings(self):
        result = await self.app.dispatch("fuzz utf8 '国{admin,user}[0-1]'")
        self.assertIn("Sent 4 payloads", result.output)
        self.assertEqual(
            [call.args[1] for call in self.send.await_args_list],
            [text.encode() for text in ("国admin0", "国admin1", "国user0", "国user1")],
        )

    async def test_fuzz_limit_rejects_entire_pattern_before_sending(self):
        for command in ("fuzz hex '???0'", "fuzz utf8 '[a-z]{2}'"):
            with self.subTest(command=command):
                with self.assertRaisesRegex(CommandError, "expansion limit"):
                    await self.app.dispatch(command)
        self.send.assert_not_awaited()

    async def test_explicit_fuzz_limit(self):
        await self.app.dispatch("fuzz hex '0[0-3]' --limit 4")
        self.assertEqual(self.send.await_count, 4)
        self.send.reset_mock()
        with self.assertRaises(CommandError):
            await self.app.dispatch("fuzz utf8 '[a-d]' --limit 3")
        self.send.assert_not_awaited()

    async def test_invalid_fuzz_limits_and_patterns(self):
        for command in (
            "fuzz hex '0?' --limit 0",
            "fuzz utf8 '?' --limit 65537",
            "fuzz hex '?'",
            "fuzz utf8 '[z-a]'",
        ):
            with self.subTest(command=command):
                with self.assertRaises(CommandValidationError):
                    await self.app.dispatch(command)
        self.send.assert_not_awaited()

    async def test_no_session_is_user_facing(self):
        self.app.session = None
        for command in (
            "send hex 00",
            "send utf8 test",
            "fuzz hex '0?'",
            "fuzz utf8 '[a-b]'",
            "close",
        ):
            with self.subTest(command=command):
                with self.assertRaisesRegex(CommandError, "Connect to one first"):
                    await self.app.dispatch(command)
        self.send.assert_not_awaited()

    async def test_no_response_is_visible_and_fuzz_continues(self):
        self.send.return_value = b""
        result = await self.app.dispatch("fuzz hex '0[0-1]'")
        self.assertEqual(self.send.await_count, 2)
        self.assertIn("No response received", result.output)

    async def test_io_error_stops_fuzz_and_retains_transaction(self):
        self.send.side_effect = OSError("device disconnected")
        with self.assertRaisesRegex(CommandError, "device disconnected"):
            await self.app.dispatch("fuzz hex '0?'")
        self.assertEqual(self.send.await_count, 1)
        self.assertEqual(self.app.transactions[0][0], "-->")
        self.assertIn("device disconnected", self.app.transactions[-1][-1])

    async def test_cancellation_stops_fuzz_and_releases_lock(self):
        entered = asyncio.Event()

        async def wait(*_args):
            entered.set()
            await asyncio.Event().wait()

        self.send.side_effect = wait
        task = asyncio.create_task(self.app.dispatch("fuzz utf8 '[a-z]'"))
        await asyncio.wait_for(entered.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await self.app.dispatch("close")
        self.session.close.assert_awaited_once()
        self.assertEqual(self.send.await_count, 1)

    async def test_fuzz_and_close_cannot_interleave(self):
        entered, release = asyncio.Event(), asyncio.Event()

        async def wait(*_args):
            entered.set()
            await release.wait()
            return b"OK"

        self.send.side_effect = wait
        fuzz = asyncio.create_task(self.app.dispatch("fuzz hex '0[0-1]'"))
        await asyncio.wait_for(entered.wait(), timeout=2)
        close = asyncio.create_task(self.app.dispatch("close"))
        await asyncio.sleep(0)
        self.session.close.assert_not_awaited()
        release.set()
        await asyncio.gather(fuzz, close)
        self.assertEqual(self.send.await_count, 2)
        self.session.close.assert_awaited_once()
        self.assertIsNone(self.app.session)

    async def test_connect_uses_native_async_api_without_enumeration(self):
        self.app.session = None
        with patch(
            "ctserial.commands.serialx.async_serial_for_url", return_value=self.session
        ) as factory:
            result = await self.app.dispatch("connect /dev/custom-link 115200 even")
        factory.assert_called_once_with(
            "/dev/custom-link",
            baudrate=115200,
            parity=serialx.Parity.EVEN,
            stopbits=serialx.StopBits.ONE,
            byte_size=8,
        )
        self.session.open.assert_awaited_once()
        self.assertIn("OPENED", result.output)
        self.assertIn("/dev/custom-link", self.app.connection_status())
        with self.assertRaisesRegex(CommandError, "already open"):
            await self.app.dispatch("connect /dev/other")

    async def test_failed_open_leaves_disconnected(self):
        self.app.session = None
        self.session.open.side_effect = FileNotFoundError("missing port")
        with patch(
            "ctserial.commands.serialx.async_serial_for_url", return_value=self.session
        ):
            with self.assertRaisesRegex(CommandError, "missing port"):
                await self.app.dispatch("connect /dev/missing")
        self.assertIsNone(self.app.session)

    async def test_invalid_connection_arguments(self):
        for command in (
            "connect",
            "connect /dev/test 0",
            "connect /dev/test 9600 invalid",
        ):
            with self.subTest(command=command):
                with self.assertRaises(CommandValidationError):
                    await self.app.dispatch(command)

    async def test_cli_failure_closes_connection(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        status = await self.app.run_cli(
            ["-c", "send hex 00", "-c", "send hex zz"], stdout=stdout, stderr=stderr
        )
        self.assertEqual(status, 2)
        self.session.close.assert_awaited_once()
        self.assertIsNone(self.app.session)
        self.assertIn("Error:", stderr.getvalue())

    async def test_cli_batch_and_exit_close_connection(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        status = await self.app.run_cli(
            ["-c", "send utf8 hi", "-c", "exit confirm", "-c", "send utf8 ignored"],
            stdout=stdout,
            stderr=stderr,
        )
        self.assertEqual(status, 0, stderr.getvalue())
        self.assertEqual(self.send.await_count, 1)
        self.session.close.assert_awaited_once()

    async def test_device_listing_errors_are_user_facing(self):
        with patch(
            "ctserial.commands.common.list_serial_devices",
            side_effect=OSError("unavailable"),
        ):
            with self.assertRaisesRegex(CommandError, "unavailable"):
                await self.app.dispatch("devices")

    async def test_transaction_window_is_bounded(self):
        for _ in range(1100):
            self.app._record("-->", b"test")
        self.assertEqual(len(self.app.transactions), 1000)
