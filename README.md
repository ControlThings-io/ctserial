# Control Things Serial

A highly flexible serial interface tool made for penetration testers.

# Installation:

As long as you have git and Python 3.6 or later installed, all you should need to do is:

```
pip3 install ctserial
```

# Usage:

First, start the tool from a terminal.  Then connect to your serial device and interact with it.  For example:

```
ctserial> connect /dev/your-serial-device
ctserial> send hex deadc0de        (sends actual hex, so 4 bytes)
ctserial> send Dead Code 国        (sends full utf-8 string without spaces)
ctserial> send "Dead Code 国"      (Use quotes if you need spaces)
ctserial> exit
```

NOTE: The v0.4.0 temporarily removed non-hex character cleaning from `send hex` hexstring, so you can not currently use spaces in the hex string.  This will be restored in the near future, but I had to push out v0.4.0 a bit fast to replace a broken v0.3.2 which got out of sync with the ctui library it depended on.

# Platform Independence

Python 3.6+ and all dependencies are available for all major operating systems.  It is primarily developed on MacOS and Linux, but should work in Windows as well.

# Development

If you are interested in modifying `ctserial`:

1. Install Python's Poetry package at https://python-poetry.org/.
2. Clone the `ctserial` github repository.
3. Open a termainal to the cloned repository.
4. Run `poetry install` to create a new virtual environment and install an editable instance of `ctserial` with its dependencies.


# Author

* Justin Searle <justin@controlthings.io>

