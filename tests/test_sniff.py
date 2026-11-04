"""Keep the legacy synchronous sniffer importable after removing pyserial."""

import unittest
from unittest.mock import Mock, patch

from ctserial import sniff


class SniffTests(unittest.TestCase):
    """Validate serialx construction and cleanup without real ports."""

    def test_interrupt_closes_port(self):
        session = Mock()
        session.read.side_effect = KeyboardInterrupt
        with (
            patch("sys.argv", ["sniff", "-t", "/dev/test@115200"]),
            patch(
                "ctserial.sniff.serialx.serial_for_url", return_value=session
            ) as factory,
        ):
            with self.assertRaises(SystemExit) as result:
                sniff.main()
        self.assertEqual(result.exception.code, 1)
        factory.assert_called_once_with("/dev/test", baudrate=115200, timeout=0)
        session.close.assert_called_once()

    def test_partial_open_failure_closes_earlier_ports(self):
        session = Mock()
        with (
            patch("sys.argv", ["sniff", "-t", "/dev/one", "-t", "/dev/two"]),
            patch(
                "ctserial.sniff.serialx.serial_for_url",
                side_effect=[session, OSError("missing port")],
            ),
        ):
            with self.assertRaisesRegex(OSError, "missing port"):
                sniff.main()
        session.close.assert_called_once()
