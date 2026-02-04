## Download

You can download the latest firmware from http://micropython.org/download/.

## Preparation

First, disconnect everything from your pyboard. Then connect the DFU pin with the 3.3V pin (they're right next to each other) to put the board into DFU (*Device Firmware Update*) mode. Now connect the pyboard to your computer via USB.
![DFU pin quick reference](https://raw.githubusercontent.com/nadrimajstor/micropython-wiki/master/images/pybv10b-DFU_quick_ref.png)

## Flashing

### dfu-util

First, install dfu-util via your package manager.

You can list all DFU-capable devices using the `-l` argument:

```
$ sudo dfu-util -l
dfu-util 0.5

(C) 2005-2008 by Weston Schmidt, Harald Welte and OpenMoko Inc.
(C) 2010-2011 Tormod Volden (DfuSe support)
This program is Free Software and has ABSOLUTELY NO WARRANTY

dfu-util does currently only support DFU version 1.0

Found DFU: [0483:df11] devnum=0, cfg=1, intf=0, alt=0, name="@Internal Flash  /0x08000000/04*016Kg,01*064Kg,07*128Kg"
Found DFU: [0483:df11] devnum=0, cfg=1, intf=0, alt=1, name="@Option Bytes  /0x1FFFC000/01*016 e"
Found DFU: [0483:df11] devnum=0, cfg=1, intf=0, alt=2, name="@OTP Memory /0x1FFF7800/01*512 e,01*016 e"
Found DFU: [0483:df11] devnum=0, cfg=1, intf=0, alt=3, name="@Device Feature/0xFFFF0000/01*004 e"
```

If desired, backup the original firmware (this doesn't work with dfu-util 0.5, but does with 0.7 or newer).
Previous releases of micropython are available from: http://micropython.org/download/ so performing a backup shouldn't be necessary.

```
$ sudo dfu-util --alt 0 --upload pyboard-original.dat -s:524288
(...)
Starting upload: [#######] finished!
```

Then write the downloaded firmware to the pyboard:

```
$ sudo dfu-util --alt 0 -D pybv10-2014-05-19-v1.0.1-24-g5cdff5f.dfu 
(...)
done parsing DfuSe file
```

> **NOTE:**
>
> If you have other DFU capable devices connected to you machine (*for example an Apple Magic Mouse*), and you receive the following message:
>
```
More than one DFU capable USB device found, you might try '--list' and then disconnect all but one device
```
>
> you may want to disconnet all other devices, or specify which device's firmware you want to edit by passing either `--device` or the shorter `-d` flag to `dfu-util`. Example:
>
```
$ sudo dfu-util --alt 0 -D pybv10-2014-05-19-v1.0.1-24-g5cdff5f.dfu -d 0483
```

After the the program finished, disconnect the pyboard from USB and remove the jumper between the DFU and the 3.3v ports.

If you need to restore the original firmware, use the following command:
```
$ sudo dfu-util --alt 0 -D pyboard-original.dat -d 0483:df11 -s 0x8000000
```
This will restore everything, including the internal flash filesystem.

### pydfu

There is an alternative DFU programmer that is written in pure Python.  It can be found here:
https://github.com/micropython/micropython/blob/master/tools/pydfu.py .  It requires the PyUSB package.

To use pydfu:
```
$ python pydfu.py -u <firmware.dfu>
```
This will copy the given firmware file to the pyboard.  pydfu is much faster than dfu-util.

Dependencies
* libusb (MacPorts: port install libusb or HomeBrew: brew install libusb)
* PyUSB  (pip install pyusb)

### On Windows - Using dfu-util

Install WinUSB using the [Zadig](http://zadig.akeo.ie/) utility, by selecting Options->List All Devices, select _STM32 BOOTLOADER_ and click Install Driver.

Download [dfu-util](http://dfu-util.sourceforge.net/) for Windows (version 0.9 at the time of writing) and unzip.

Execute:
```
dfu-util -l
```
You should see something like:
```
dfu-util 0.9

Copyright 2005-2009 Weston Schmidt, Harald Welte and OpenMoko Inc.
Copyright 2010-2016 Tormod Volden and Stefan Schmidt
This program is Free Software and has ABSOLUTELY NO WARRANTY
Please report bugs to http://sourceforge.net/p/dfu-util/tickets/

Found DFU: [0483:df11] ver=2200, devnum=3, cfg=1, intf=0, path="2-1.3", alt=3, name="@Device Feature/0xFFFF0000/01*004 e", serial="357637573036"
Found DFU: [0483:df11] ver=2200, devnum=3, cfg=1, intf=0, path="2-1.3", alt=2, name="@OTP Memory /0x1FFF7800/01*512 e,01*016 e", serial="357637573036"
Found DFU: [0483:df11] ver=2200, devnum=3, cfg=1, intf=0, path="2-1.3", alt=1, name="@Option Bytes  /0x1FFFC000/01*016 e", serial="357637573036"
Found DFU: [0483:df11] ver=2200, devnum=3, cfg=1, intf=0, path="2-1.3", alt=0, name="@Internal Flash  /0x08000000/04*016Kg,01*064Kg,07*128Kg", serial="357637573036"
```
To install the firmware execute:
```
dfu-util --alt 0 -D pybv10-2014-05-19-v1.0.1-24-g5cdff5f.dfu
```
Which should show progress bars for the firmware download to the pyboard and complete with:
```
done parsing DfuSe file
```
After the the program has finished, disconnect the pyboard from USB and remove the jumper between the DFU and the 3.3v ports.

### On Windows - Using STM DfuSe

See this PDF document: [Micro-Python-Windows-setup.pdf](http://micropython.org/resources/Micro-Python-Windows-setup.pdf)

### Firmware version

Once you have flashed the new firmware you may want to check it correspond to the version expected. At the REPL prompt, type

```
>>> import os
>>> os.uname()
```