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
ctserial> sendhex deadc0de        (sends actual hex, so 4 bytes)
ctserial> sendhex de ad c0de      (sends same hex as before, ignoring any non-hex character)
ctserial> send Dead Code 国        (sends full utf-8 string without spaces)
ctserial> send "Dead Code 国"      (Use quotes if you need spaces)
ctserial> exit
```

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

