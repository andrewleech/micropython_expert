# Overview

The STM32F4 chip on the Pyboard can be programmed and debugged using C or C++. The underlying MicroPython firmware is compiled this way. But given the relative size and simplicity of the Pyboard, it makes for an interesting alternative to the [STM32F4DISCOVERY](https://www.st.com/en/evaluation-tools/stm32f4discovery.html). The Pyboard has a smaller footprint (64-pin vs. 100-pin package) as well significantly less peripheral chips on the board.

The Pyboard does, however, lack an onboard, pre-wired ST-Link/v2 programmer that a board like the STM32F4DISCOVERY has. This makes it a bit more inconvenient to target using C/C++, but this page explains how to overcome this.

# Prerequisites

- [pyboard v1.1](https://store.micropython.org/product/PYBv1.1)
- [ST-Link/v2](https://www.st.com/en/development-tools/st-link-v2.html) (the -ISOL version is not needed)
  - ![st-link/v2](https://www.st.com/bin/ecommerce/api/image.PF251168.en.feature-description-include-personalized-no-cpn-large.jpg)
- 5 Male to Female Jumper Wires

# Software Setup

Before any hardware is set up, let's first set up a new C project from which to develop. Download [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html) and when creating a new project, select STM32F405RG from the product selector.

You can now configure IO pins, interrupts, etc. Selecting Generate Code will generate an entire C project based on the configured IDE settings.

One such configuration that has been tested in using [CLion](https://www.jetbrains.com/clion/) and its [OpenOCD plugin](https://github.com/elmot/clion-embedded-arm/blob/master/USAGE.md).

# Hardware Setup

Connect the Pyboard USB connector to a USB power adapter (not your development host).

Connect the ST-Link/v2 USB cable to your development host.

From the [micropython README](https://github.com/micropython/micropython#the-stm32-version):

> connect the 3V3 pin to the P1/DFU pin with a wire (on PYBv1.1 they are next to each other on the bottom left of the board, second row from the bottom).

This is needed because the programming pins on the Pyboard are shared with LEDs, so if the MicroPython firmware is running, it conflicts with the ST-Link/v2 programming.

In the following diagram, P1/DFU is labelled BOOT0.

![pvbv11-pinout](https://micropython.org/resources/pybv11-pinout.jpg)

Next, connect the following pins from the ST-Link/v2 to the Pyboard. Refer to the [ST-Link/v2 User Manual](https://www.st.com/resource/en/user_manual/dm00026748.pdf). Pin 1 on the ST-Link/v2 is the lower left corner of the connecter if you hold the ST-Link/v2 such that the labels are correctly oriented.

```
ST-Link/V2        | pyboard v1.1
----------------- | -------------
PIN1  (VAPP)      -> 3V3
PIN7  (TMS_SWDIO) -> PA13 (P5)
PIN9  (TCK_SWCLK) -> PA14 (P4)
PIN13 (TDO_SWO)   -> PB3  (X17-1) (Optional debug serial)
PIN15 (NRST)      -> RST
PIN20 (GND)       -> GND
```

# Programming

You can now program/debug using any software that supports the ST-Link/v2. One such program is [OpenOCD](http://openocd.org/).

```bash
$ openocd -f board/stm32f4discovery.cfg -c "program app.elf" -c reset -c shutdown
```

Debugging has been tested to work under CLion using the OpenOCD plugin and `gcc-arm-embedded` toolchain.

# References

- [Programming the STM32F4DISCOVERY using External ST-Link/v2](https://electronics.stackexchange.com/a/410840/194001)
- [Symbolic Debugging for STM32](https://github.com/micropython/micropython/wiki/)
