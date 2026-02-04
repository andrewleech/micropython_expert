This describes the basics on building micropython binaries for different boards. In the examples below all builds were done on a Linux Mint 18.0 machine.

Prerequisites to this are setting up your build environment. You can [get started and setup your build environment on Linux Mint 18.0 here](https://github.com/micropython/micropython/wiki/Getting-Started---Compiling-Micropython-for-Ubuntu-16.04)

Assuming that you have a working environment and you can run **make** to make a build for Linux we can now explain the:
* directory structure
* making a build for an architecture
* flashing onto micropython hardware

## Directory Structure
Building micropython for different hardware happens in the **ports** directory. If you look in:
```bash
  ~/microPython/project/micropython/ports
```
This contains a list of hardware platforms that are supported. At the time of writing, 14 in total. This document describes how to build for stm32 - the platform used by the micropython organisation. Which is in the stm32 subdirectory:
```bash
  /ports/stm32
```

Within each platform directory there is build<name> directory e.g.

```bash
 /ports/stm32/build-PYBD_SF2
 /ports/stm32/build-PYBD_SF6
```
When a build is complete the firmware builds are placed in the relevant directory. Within a build directory there are two main build files that are used to flash onto a board. Which are named **firmware.hex** and **firmware.dfu**. The *dfu* file is the file that has to be flashed onto your microcontroller.

Within the stm32 directory there is a **modules** directory. This is used to compile your own modules into a firmware build. This is explained later.

## Making A Build For An Architecture
To make a build for a particular architecture you have to be in the specific hardware directory to run the make command. The **make** command can take many parameters, this document looks at building for a particular board and compiling into the firmware your own modules.

The format of the build command is **make** then **[option]** then **[target]**. For compiling against the new [pyboard D-series](https://store.micropython.org/category/pyboard%20D-series) the build targets are:
* PYBD_SF2
* PYBD_SF4
* PYBD_SF6

Hence you would comple for the [SF2](https://store.micropython.org/product/PYBD-SF2-W4F2) like:
```bash
   /> make BOARD=PYBD_SF2
```
And for the SF6 it would be:
```bash
   /> make BOARD=PYBD_SF6
```

### Compiling Your Own Python Code Into Firmware
To make a firmware build with a python file that you have created, simply place in the **/modules** directory the python file you wish to be available in your firmware build. Hence if you wanted to have a **hello_world.py** compiled into your firmware image do: 
- place the **hello_world.py** into your /ports/stm32/modules directory
- do your build with the command **FROZEN_MPY_DIR=modules

e.g.
```bash
   /> make BOARD=PYBD_SF2 FROZEN_MPY_DIR=modules
```

## Flashing Onto Micropython Hardware
[Flashing onto is described here](https://github.com/micropython/micropython/wiki/Pyboard-Firmware-Update)




