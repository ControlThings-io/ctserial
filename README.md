# Control Things Serial

ctserial goal is to become the security professional's Swiss army knife for interacting with raw serial devices

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
ctserial> sendhex \xde \xad c0de  (sends same hex as before, ignoring spaces and \x)
ctserial> send Dead Code 国        (sends full utf-8 string without spaces)
ctserial> send "Dead Code 国"      (Use quotes if you need spaces)
ctserial> exit
```

# Platform Independence

Python 3.6+ and all dependencies are available for all major operating systems.  It is primarily developed on MacOS and Linux, but should work in Windows as well.

# Author

* Justin Searle <justin@controlthings.io>

