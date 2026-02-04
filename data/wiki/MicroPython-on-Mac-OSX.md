# Introduction
Micro Python supports OSX as well as it does Linux: once the necessary software dependencies are installed on an OSX system, development and usage is essentially the same on both platforms, so no special 'tricks' are required to work with Micro Python on OSX.  (If any discrepancies are found, they should be reported as an [issue on the MicroPython repo](https://github.com/micropython/micropython/issues).) 

Specifically, this means that both the unix and stmhal (pyboard) ports of Micro Python can be compiled on Mac OSX directly from the master branch without any alteration. This article aims to describe which software packages are required to build Micro Python and how to install them on your OSX system. I use [Macports](http://www.macports.org) so this article will focus on that; it is also possible to Homebrew to install the required software dependencies.

This article is targeted towards Micro Python developers using OSX, it will address OSX specific issues rather than general development questions.

# Compiling the unix port on OSX

Recent modifications to the build scripts have made the build process for the unix port on OSX the same as it is that on Linux, despite the fact that Micro Python is built using gcc on Linux and clang on OSX.
In order to compile on OSX you will need the following software packages installed:
* A relatively recent version of Xcode to provide the clang compiler (MicroPython has been confirmed to compile under clang versions 3.1 and 4.2)
* [Macports](http://www.macports.org) for the next commands
* libffi (minimum version 3.1-4 from Macports) `sudo port install libffi`
* pkgconfig `sudo port install pkgconfig`
* Python >= 3.3 `sudo port install python34`
* Setup python34 as python3 `sudo port select python3 python34'
* git - to keep local source tree up to date `sudo port install git`
* If you like using git completion or `$(__git_ps1)` for your prompt, then add the following line to your ~/.bashrc file: `. /opt/local/share/git/contrib/completion/git-prompt.sh`

## Build Process
Same as on Linux 
- go to `micropython/mpy-cross`and run `make -C mpy-cross``
- go to `micropython/ports/unix` and 
   - run `make axtls`,
   - run `make` (or `make -B` or `make clean; make` if rebuilding.

If installing libffi with homebrew, you might have to specify its location to pkgconfig
```
export PKG_CONFIG_PATH=/usr/local/Cellar/libffi/3.2.1/lib/pkgconfig/
```

## Running tests
Go to `micropython/tests` and run the test script `./run-tests`
The test script will look for the executable in `../unix/micropython` and will compare the output of the micropython executable to the locally installed version of Python3
* If your Python3 executable is named `python3.x` then it may be necessary to create a link named `python3` to this executable
* All tests should pass on OSX, however it may be necessary to set the encoding in the terminal to 'UTF-8' if the unicode tests are failing

# Compiling the stmhal port for the pyboard

Required software:
* mac version of gcc-arm-none-eabi, version >= 4.8
* dfu-util >= 0.7 to load firmware to pyboard
* Python3 >= 3.3
* pyserial package for Python3

TODO: building stmhal

TODO: Using test scripts to run tests on pyboard
```
cd micropython/tests
./run-tests --pyboard --device /dev/tty.usbmodem*
```

Using pyboard.py to run python scripts residing on the mac:
```
python3 tools/pyboard.py --device /dev/tty.usbmodem* FILE
```

### Using `screen` to access REPL
Type `screen /dev/tty.usbmodem*` with `*` replaced by your specific device number; use `ls /dev/tty.usbmodem*` to find the name of your device.
To exit from 'screen' type 'Ctl-a, k'; and then answer 'y' to exit

Development workflow on mac is the same as for Linux; see [DevelWorkflow](DevelWorkflow) for recommended workflow practices and usage of git.

TODO: Issues that may be encountered using previous versions of pyboard firmware (USB mass storage issue) that can be fixed with firmware upgrade

# Patching pyserial 2.7

It turns out that there are some bugs in the OSX portion of pyserial 2.7. To confirm if your pyserial has been fixed or not, plug in your pyboard, and the run the following python script using python3 (just to be clear, this script will be run on your Mac, not on the pyboard)
```python
from serial.tools import list_ports
for port in list_ports.comports():
    print(port)
```
If you get output like this:
```
['/dev/cu.Bluetooth-Incoming-Port', 'n/a', 'n/a']
['/dev/cu.Bluetooth-Modem', 'n/a', 'n/a']
['/dev/cu.usbmodem622', 'Pyboard Virtual Comm Port in FS Mode', 'USB VID:PID=f055:9800 SNR=000000000011']
```
Then your version of pyserial is working and you don't need to do anything further.

If, however, you get no output (no serial ports listed) when running python3 and get output similar to the above when running python2 then you have the buggy version.

I found this issue http://sourceforge.net/p/pyserial/patches/38/ with an attached patch which addresses the issue.

I installed python34 using ports (as in the first part of this wiki page) and my python 3.4 version of pyserial was found here: `/opt/local/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/serial`

I executed the following commands to install the patched version:
```
cd /opt/local/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/serial/tools
sudo cp list_ports_osx.py list_ports_osx_original.py
sudo curl -O http://sourceforge.net/p/pyserial/patches/_discuss/thread/603bd426/55a8/attachment/list_ports_osx.py
```
Now I was able to execute the list_ports.comports() example posted above under python3 and it produced the correct output.