"""Run against an installed wheel or source distribution, without serial hardware."""

import asyncio
import io
import tempfile
from importlib.metadata import metadata, version
from pathlib import Path

from ctui import CommandValidationError, MemoryHistory

from ctserial.commands import CtserialApp


async def main() -> None:
    """Verify artifact metadata, command registration, parsing, and CLI cleanup."""
    assert version("ctserial") == "0.6.0"
    assert version("ctui").split(".")[0] == "1"
    package = metadata("ctserial")
    assert package["License-Expression"] == "GPL-3.0-or-later"
    assert "LICENSE" in package.get_all("License-File", [])
    assert package["Requires-Python"].replace(" ", "") == ">=3.11,<4"
    requirements = package.get_all("Requires-Dist")
    assert any(item.startswith("serialx") for item in requirements)
    assert not any(item.startswith("pyserial") for item in requirements)
    with tempfile.TemporaryDirectory() as directory:
        app = CtserialApp(data_dir=Path(directory), history=MemoryHistory())
        stdout, stderr = io.StringIO(), io.StringIO()
        assert await app.run_cli(["--help"], stdout=stdout, stderr=stderr) == 0
        for name in ("send hex", "send utf8", "fuzz hex", "fuzz utf8"):
            result = await app.dispatch(f"help {name}")
            assert name in result.output, name
        try:
            await app.dispatch("send hex zz")
        except CommandValidationError:
            pass
        else:
            raise AssertionError("Invalid hexadecimal input was accepted")
        assert (
            await app.run_cli(["-c", "send utf8 hello"], stdout=stdout, stderr=stderr)
            == 2
        )
        assert "Connect to one first" in stderr.getvalue()
        assert app.session is None
    print("ctserial 0.6.0 installed-artifact smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
