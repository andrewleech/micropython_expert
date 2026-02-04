Cortex M4 STM32F429ZI
* on STM site - http://www.st.com/web/catalog/tools/FM116/SC959/SS1532/LN1199/PF259090
* [datasheet](http://www.st.com/st-web-ui/static/active/en/resource/technical/document/data_brief/DM00094498.pdf)

### Features ###
* STM32F429ZI 168MHz (LQFP-144)
* 2MiB flash, 256KiB RAM
* 8MiB (64Mbit) SDRAM
* 3-axis gyro (L3GD20)
* 2.4 inch TFT display
* 2 LEDs
* one user button
* USB OTG

### Status ###

Not *officially* supported (no downloads provided, no customised documentation), but the `stmhal` variant supports the basic board well (button, LEDs, flash, USB micro-B port).

Unlike the STM32F4 Discovery board, this board is designed to be powered and flashed via the USB mini-B connector; to run on the USB micro-B connector alone you have to jumper a 5V pin to pin PB13.

MicroPython does not use the 8MiB SDRAM on the board (it won't appear in `micropython.mem_info()`).  Reports welcomed of whether it's enabled at all and of what tweaks are required to make MicroPython use it.

Similarly, bare MicroPython does not initialise any of the other peripherals and they're connected in ways that make them easy to isolate or ignore, so almost all the pins they use should be available as GPIOs.  There may well be drivers for them in other STM32 eval board variants.

The chip's 256KiB RAM is made up of 192KiB contiguous general-purpose SRAM and a separate 64KiB core-coupled memory (CCM). MicroPython reserves the 64KiB CCM for caching writes to its flash filesystem.  MicroPython uses 80KiB for the stack, 112KiB for the statics/heap.  That stack/heap split results in quite a generous stack which you're unlikely to use unless you use deeply nested calls or heavy recursion, but is easily tuned by modifying `_heap_end` in the [linker script](https://github.com/micropython/micropython/blob/761e4c7f/stmhal/boards/stm32f429.ld).

The chip's 2MiB flash is made up of various pages of different sizes, split across two non-contiguous 1MiB blocks, and only the first 64KiB of any page can be used.  By default that leaves 112KiB available before filesystem overheads, ~95KiB after overheads.  It's pretty simple to [increase this](https://forum.micropython.org/viewtopic.php?t=777#p4491) to 304KiB (before overheads) by enabling the [non-contiguous flash features](https://gist.github.com/zwlp/bcfda08018c0c80a948a99809fc7cc4e) in `storage.c`, rebuilding, reflashing, then carrying out a [factory reset](http://docs.micropython.org/en/v1.9/pyboard/pyboard/tutorial/reset.html) to enlarge the filesystem.  It should be possible to increase this by another 64KiB by using the first half of sector 5; haven't managed to get this working like it should just yet though.

On the USB mini-B, the STLinkV2 offers a virtual mass storage device (on STM32F429I-DISC1 boards) plus a virtual serial port that's connected (or on the older board, solder bridges can be adjusted to connect it) to the target's USART1.  On the USB micro-B, MicroPython adds a its own mass storage device and a second virtual serial port which is emulated and connected to the REPL.

### Building ###

    cd stmhal
    make BOARD=STM32F429DISC

Do not confuse `STM32F429DISC` with the similarly named `STM32F4DISC`.  Images for the F4DISC will not boot on the F429.

### Flashing ###

Several mechanisms are available for getting MicroPython onto the board initially.

#### stlink ####

The easiest mechanism is via the onboard STLinkV2.  On Linux, install [texane's stlink](https://github.com/texane/stlink/) and use:

    make BOARD=STM32F429DISC deploy-stlink

The stock Makefile's approach of flashing two images straddling the filesystem turned out rather unreliable for this particular user, frequently resulting in failed verification of the second image and/or leaving the STLink in a strange unresponsive state (at least, wedged in a way that st-flash couldn't un-wedge).  What seemed to improve matters was a combination of building/flashing a monolithic image (see below) and performing a full (external!) reset after flashing to avoid [watchdog-related hangs](/micropython/micropython/issues/2635).  It's possible that texane's stlink isn't holding the target in reset between image parts, or isn't really honouring its `--reset` flag.  Some folks believe OpenOCD to be preferable for STLink-based flashing, perhaps for this sort of reason.

#### Drag & drop ####

On the STM32F429I-DISC1 (newer) boards the STLinkV2 supports writing flat binaries via a virtual mass storage device, but the Makefile produces DFUs, ELFs and split binaries by default.  On Linux, once you've built an image, generate a flat binary using:

    arm-none-eabi-objcopy -O binary build-STM32F429DISC/firmware.elf build-STM32F429DISC/firmware.bin

then copy `firmware.bin` into the virtual drive.

A downside of flashing this way is that you'll overwrite MicroPython's flash filesystem every time you flash, so you'll probably want to freeze Python source into the MicroPython image if you flash this way.

This should probably be added as a deploy target to the port's Makefile.

#### Serial ####

Flashing over serial using the ROM serial bootloader is also possible using `stm32loader`.  On Linux, probably any variant will do, but [jsnyder's variant](https://github.com/jsnyder/stm32loader) is known to work, at least on the USART1 PA9/PA10 pins:

    # These values come from the stmhal Makefile.
    # Vector table (tiny, probably unvarying)
    FLASH_ADDR=0x08000000
    # Main body of uPy (bigger, and could embed frozen bytecode/source)
    TEXT_ADDR=0x08020000
 
    # Full erase.  Typically ~20s.
    stm32loader.py -b 460800 -p /dev/ttyACM0 -e

    # Vector table flash.  Typically ~5s.  Quite noisy!
    # I think I found I had to reset between invocations of stm32loader.
    # You can do that with the button, or via "st-flash reset" if you have texane's st-util
    stm32loader.py -b 460800 -p /dev/ttyACM0 -a $FLASH_ADDR -wv ./build-STM32F429DISC/firmware0.bin
 
    # Main body flash.  Typically ~70s.  Again, may need a reset first.
    stm32loader.py -b 460800 -p /dev/ttyACM0 -a $TEXT_ADDR  -wv ./build-STM32F429DISC/firmware1.bin

This should probably be added as a deploy target to the port's Makefile.

#### DFU ####

DFU is not easily available on this board because it's only available on one USB peripheral of the STM32 (the `OTG_FS` block), and that peripheral is not brought out to a connector, only to pins.  The `OTG_HS` block is the one brought out to the USB micro-B connector, but confusingly it's marked as "OTG_FS" in some Discovery schematics/labels because it's used in full-speed mode.

DFU flashing [has been performed](https://forum.micropython.org/viewtopic.php?t=777) using [butchered USB cables](https://forum.micropython.org/download/file.php?id=95&sid=8d5e16b1ed22b6ba278e3ae038969aa9) with PA11 = D-, PA12 = D+.  This user found it necessary to use a version of `dfu-util` from git commit [4f006799](https://sourceforge.net/p/dfu-util/dfu-util/ci/4f006799/) or later, which contains a workaround for an apparent ROM bug in [DfuSe region enumeration](https://sourceforge.net/p/dfu-util/tickets/22/).

### Bugs ###

If the REPL is duplicated on a UART, Ctrl-C may not work on that UART, per [issue 1568](https://github.com/micropython/micropython/issues/1568).

Relative imports like `from . import submodule` seem to cause crashes.  Not yet fully investigated/reported as an issue.