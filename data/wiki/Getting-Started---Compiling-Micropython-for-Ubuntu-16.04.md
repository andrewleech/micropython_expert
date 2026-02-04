This page is intended to supplement [Getting Started](https://github.com/micropython/micropython/wiki/Getting-Started). It covers potential issues a developer might get in compiling micropython from source on Ubuntu 16.xx or derivatives of Ubuntu 16.xx such as Linux Mint 18.xx

## Problems With ARM GCC Tool Chain
With Linux Mint 18 and Ubuntu 16 (and derivatives) there is a known problem while compiling the Micropython source. The ARM GCC tool chain is at a version which is not compatible with compiling for some version of the Micropython source code.
At the point of writing this was failing for the Pyboard 'D' STM hardware. The version on your machine has to be version 8.1 or higher. You can check the installed version using this command:

```bash
$ arm-none-eabi-gcc --version
arm-none-eabi-gcc (15:4.9.3+svn231177-1) 4.9.3 20150529 (prerelease)
Copyright (C) 2014 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

```
When compiling with the wrong version of ARM GCC you might see errors like this:

```bash

$ make BOARD=PYBD_SF2 FROZEN_MPY_DIR=modules
In file included from ../../lib/mbedtls/library/aes.c:31:0:
./mbedtls/mbedtls_config.h:83:20: fatal error: stdlib.h: No such file or directory
 #include <stdlib.h>
                    ^
compilation terminated.
In file included from ../../lib/mbedtls/library/aesni.c:30:0:
./mbedtls/mbedtls_config.h:83:20: fatal error: stdlib.h: No such file or directory
 #include <stdlib.h>
```

## Installing Newer Version Of Tool Chain
It is recommended that you leave your default system and update your machine to use the newer version of the ARM GCC tool-chain. For this example I downloaded the version from the [new ARM GCC tool-chain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads) onto my **_~/applications_** folder. After uncompressing the zip file you need to update your bashrc script and include this line to make the ARM GCC binaries link to your new folder. Hence from your home directory use the command line to edit your bashrc file like this:

```bash
$ nano .bashrc
```

Add this line to your path environment variable then save the file.

```bash
# Added by Joe Bogs 26/06/2019 to allow my gcc-arm tool chain to work for compiling builds for Pyboard 'D' See https://micropython.org
export PATH=/home/joeblogs/applications/gcc-arm/gcc-arm-none-eabi-8-2018-q4-major/bin/:$PATH
```

Then you can either run the source command from the current terminal or open a new terminal. To run source do:

```bash
$ source .bashrc
```

To check you are using the new ARM GCC binaries do:

```bash

$ arm-none-eabi-gcc --version
arm-none-eabi-gcc (GNU Tools for Arm Embedded Processors 8-2018-q4-major) 8.2.1 20181213 (release) [gcc-8-branch revision 267074]
Copyright (C) 2018 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

```

You will notice that the system is now using version 8.2.1. You can also further check by just using **which**
to find out what binary you are pointing to like this:

```bash

$ which arm-none-eabi-ar
/home/nherriot/applications/gcc-arm/gcc-arm-none-eabi-8-2018-q4-major/bin//arm-none-eabi-ar

```

You should now be able to compile your micropython source code as normal for the STM boards.







