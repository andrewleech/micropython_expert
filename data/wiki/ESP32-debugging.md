# Debugging the ESP32 port

An overview of how to debug and/or report issues in the MicroPython ESP32 port.

## Help, my MicroPython crashed

If your board crashed with a "Guru Meditation Error" you've encountered a fatal
error. MicroPython will print a collection of data that might be relevant to
determining the cause, and then reset the board.

These errors may indicate a bug in MicroPython. But it might also be caused by
a bug in your code, especially if you're building and/or customizing your own
version of MicroPython. The instructions below may help to determine the what
is going wrong.

If you believe the crash is due to a bug in MicroPython, please consider
reporting it. To do first determine if you can reproduce the issue and write
down the steps for doing so. Then copy all output leading up to the error until
and including the 'Rebooting...' message and file a bug report
[here](https://github.com/micropython/micropython/issues/new).

## Debugging issues yourself

### Prerequisites

In order to debug issues on the ESP32 port, you need two things:

- A working ESP-IDF build environment.
  - To set up the ESP-IDF, follow the instructions in [the ESP32 port README
    section](https://github.com/micropython/micropython/blob/master/ports/esp32/README.md#setting-up-esp-idf-and-the-build-environment)
    for setting up the build environment.
- The ELF file for the exact build of MicroPython that you're using.
  - If you're building MicroPython yourself, the ELF file will be located in the
    build directory (`ports/esp32/build-BOARDNAME`) alongside the flashable
    binary itself.
  - If you downloaded MicroPython from the official website, you can find the
    corresponding ELF file available as a separate download link next to the
    flashable binary link itself.

There are a number of different variants of the ESP32 supported, and they
require slightly different toolchains which support their specific chip
architectures. In all the examples below replace `$TOOLCHAIN` with the
appropriate toolchain for the chip variant you are using:

```sh
# ESP32
TOOLCHAIN=xtensa-esp32-elf

# ESP32-S2
TOOLCHAIN=xtensa-esp32s2-elf

# ESP32-S3
TOOLCHAIN=xtensa-esp32s3-elf

# ESP32-C2, ESP32-C3, ESP32-C6, ESP32-H2
TOOLCHAIN=riscv32-esp-elf
```

### Interpreting a backtrace

When MicroPython on the ESP32 crashes, it will print out a backtrace as a list
of pointers, as can be seen in this example crash:

```
MicroPython v1.22.2 on 2024-02-22; Generic ESP32 module with ESP32
Type "help()" for more information.
>>> from network import PPP
>>> from io import BytesIO
>>> ppp = PPP(BytesIO(0))
>>> ppp.active(True)
True
>>> ppp.connect()
Guru Meditation Error: Core  1 panic'ed (LoadProhibited). Exception was unhandled.

Core  1 register dump:
PC      : 0x400db62b  PS      : 0x00060c30  A0      : 0x800db9c7  A1      : 0x3ffbb830
A2      : 0x3ffd0220  A3      : 0x00000040  A4      : 0x00000001  A5      : 0xb33fffff
A6      : 0x00000000  A7      : 0x00060823  A8      : 0x800db62b  A9      : 0x3ffbb810
A10     : 0x00000000  A11     : 0x3ffbd634  A12     : 0x3ffdeba4  A13     : 0x3ffdf1a4
A14     : 0x3ffdebcc  A15     : 0x00000001  SAR     : 0x00000020  EXCCAUSE: 0x0000001c
EXCVADDR: 0x00000008  LBEG    : 0x4000c2e0  LEND    : 0x4000c2f6  LCOUNT  : 0x00000000


Backtrace: 0x400db628:0x3ffbb830 0x400db9c4:0x3ffbb850 0x400e819e:0x3ffbb870 0x40113d22:0x3ffbb890 0x401f7bdd:0x3ffbb8b0 0x400fd081:0x3ffbb8e0 0x4016fca8:0x3ffbb910 0x4016fe25:0x3ffbb930 0x401fa741:0x3ffbb960 0x40178d97:0x3ffbb980 0x40178df1:0x3ffbb9b0 0x40176f72:0x3ffbb9d0 0x4016f795:0x3ffbb9f0 0x4016fb97:0x3ffbba10 0x4016f5e5:0x3ffbba30 0x4016fa80:0x3ffbba50 0x401611a0:0x3ffbba70


ELF file SHA256: 51aa7525e37c5ea9

Rebooting...
```

Note the SHA256 hash of the ELF file is printed, which you can use to check that
you have the correct ELF file:

```sh
sha256sum ESP32_GENERIC-20240222-v1.22.2.elf
```

This will print the SHA256 hash of the ELF file:

```
51aa7525e37c5ea9e35a4aa7d994ccd3897917063110d0885347c0eb8faf473b  ESP32_GENERIC-20240222-v1.22.2.elf
```

Having determine the correct ELF file, we can now convert the backtrace from the
list of pointers into a more human-readable form use `addr2line`:

```sh
$TOOLCHAIN-addr2line -pfiaC -e path/to/micropython.elf [backtrace]
```

For the example crash given above this would become:

```sh
xtensa-esp32-elf-addr2line -pfiaC -e ESP32_GENERIC-20240222-v1.22.2.elf 0x400db628:0x3ffbb830 0x400db9c4:0x3ffbb850 0x400e819e:0x3ffbb870 0x40113d22:0x3ffbb890 0x401f7bdd:0x3ffbb8b0 0x400fd081:0x3ffbb8e0 0x4016fca8:0x3ffbb910 0x4016fe25:0x3ffbb930 0x401fa741:0x3ffbb960 0x40178d97:0x3ffbb980 0x40178df1:0x3ffbb9b0 0x40176f72:0x3ffbb9d0 0x4016f795:0x3ffbb9f0 0x4016fb97:0x3ffbba10 0x4016f5e5:0x3ffbba30 0x4016fa80:0x3ffbba50 0x401611a0:0x3ffbba70
```

And it will give the following output:

```
0x400db628: gc_realloc at /home/micropython/micropython-autobuild/py/gc.c:1036
0x400db9c4: m_realloc at /home/micropython/micropython-autobuild/py/malloc.c:141
0x400e819e: vstr_ensure_extra at /home/micropython/micropython-autobuild/py/vstr.c:115
 (inlined by) vstr_add_len at /home/micropython/micropython-autobuild/py/vstr.c:126
0x40113d22: stringio_write at /home/micropython/micropython-autobuild/py/objstringio.c:98
0x401f7bdd: mp_stream_rw at /home/micropython/micropython-autobuild/py/stream.c:60
0x400fd081: ppp_output_callback at /home/micropython/micropython-autobuild/ports/esp32/network_ppp.c:104
0x4016fca8: pppos_output_last at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/pppos.c:878
0x4016fe25: pppos_write at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/pppos.c:241
0x401fa741: ppp_write at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/ppp.c:996
0x40178d97: fsm_sconfreq at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/fsm.c:757
0x40178df1: fsm_lowerup at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/fsm.c:102
 (inlined by) fsm_lowerup at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/fsm.c:91
0x40176f72: lcp_lowerup at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/lcp.c:475
0x4016f795: ppp_start at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/ppp.c:750
0x4016fb97: pppos_connect at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/pppos.c:340
0x4016f5e5: ppp_do_connect at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/ppp.c:464
 (inlined by) ppp_connect at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/ppp.c:285
0x4016fa80: pppapi_do_ppp_connect at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/netif/ppp/pppapi.c:277
0x401611a0: tcpip_thread_handle_msg at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/api/tcpip.c:166
 (inlined by) tcpip_thread at /home/micropython/esp-idf-v5.0/components/lwip/lwip/src/api/tcpip.c:148
```

### Interactive debugging via JTAG

To interactively debug MicroPython itself on the ESP32 you need a JTAG debugger
attached to the chip. The easiest way to set do this is by making use of the
built-in USB JTAG support available on the S3/C3/C6/H2 variants, or using a
board that includes JTAG support. For more information on setting up and using
JTAG please reference [the ESP-IDF documentation on JTAG
debugging](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/jtag-debugging/index.html).

For example to debug a board using the built-in USB JTAG of an ESP32-S3:

```sh
openocd -f board/esp32s3-builtin.cfg &
$TOOLCHAIN-gdb -x gdbinit path/to/micropython.elf
```

This is using the following `gdbinit` file:

```gdb
set pagination off
target remote :3333
set remote hardware-watchpoint-limit 2
monitor reset halt
maintenance flush register-cache
thbreak app_main
continue
```
