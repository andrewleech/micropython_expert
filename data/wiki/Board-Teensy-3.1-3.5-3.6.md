Cortex M4 based
* [Teensy 3.1/3.2](http://www.pjrc.com/store/teensy31.html)
* [Teensy 3.5](http://www.pjrc.com/store/teensy35.html)
* [Teensy 3.6](http://www.pjrc.com/store/teensy36.html)

**Note:** Some of the following instructions require using [Dave Hylands' micropython repository](https://github.com/dhylands?utf8=%E2%9C%93&tab=repositories&q=micropython&type=&language=) as some functionality has not been merged in micropython (see: [#2513](https://github.com/micropython/micropython/pull/2513) [#2519](https://github.com/micropython/micropython/pull/2519) [#2520](https://github.com/micropython/micropython/pull/2520)).

## Features
### Teensy 3.1
* MK20DX256VLH7 72MHz
* 256K Flash, 64kB RAM
* 34 pins available for digitial  I/O
* 21 pins availale for analog 16-bit A/D
* 12 timers, 12 PWM
* 3xUART
* SPI, I2C, CAN

### Teensy 3.5
* [MK64FX512VMD12](http://www.nxp.com/files/microcontrollers/doc/ref_manual/K64P144M120SF5RM.pdf) 120 MHz
* 512K flash, 
* 57 pins available for digital I/O (5v tolerant)
* 24 pins available for analog 13-bit A/D
* 14 timers, 20 PWM
* 6xUART
* 3xSPI, 3xI2C, 1xCAN, 16xDMA
* RTC
* 2 DAC channels
* SD card

### Teensy 3.6
* [MK64FX512VMD12](http://www.nxp.com/files/32bit/doc/ref_manual/K66P144M180SF5RMV2.pdf) 180 MHz
* 1M flash, 256K RAM, 4K EEPROM
* 57 pins available for digital I/O (NOT 5v tolerant)
* 26 pins available for analog 13-bit A/D
* USB High Speed OTG port
* 14 timers, 22 PWM
* 6xUART
* 3xSPI, 4xI2C, 2xCAN, 32xDMA
* RTC
* 2 DAC channels
* SD card

### Building
To build, you can either use the ARM toolchain from [here](https://launchpad.net/gcc-arm-embedded) (add to your PATH), or you can use the ARM toolchain included with Arduino/Teensyduino (set ARDUINO environment variable to point to the root of your arduino/teensyduino tree).

```
git clone https://github.com/micropython/micropython
cd micropython/ports/teensy
make BOARD=TEENSY_3.1
```
BOARD can be one of TEENSY_3.1, TEENSY_3.5, or TEENSY_3.6. If no BOARD is specified, then TEENSY_3.1 will be assumed.

### Flashing

The firmware will be in build-TEENSY_3.1/micropython.hex (replace TEENSY_3.1 appropriately).

You can flash using [teensy_loader_cli](https://github.com/PaulStoffregen/teensy_loader_cli) or by using the flashing tools included with teensyduino but setting ARDUINO to point to the arduino/teensyduino tree.
```
make BOARD=TEENSY_3.6 deploy
```
### Running Scripts
Currently, scripts must be compiled into the firmware image. Place your .py files into the teensy/scripts directory and they'll be built into your firmware image.

The sample scripts directory includes a boot.py and main.py. The default main.py flashes the LED twice.

If you want to update a script, you'll need to rebuild and reflash the firmware.

### What's currently supported
- machine.info()
- machine.unique_id()
- machine.reset()
- machine.freq()
- machine.idle()
- machine.sleep()
- machine.deepsleep()
- machine.reset_cause()
- machine.disable_irq()
- machine.enable_irq()
- machine.mem8/16/32[]
- machine.Pin
- machine.Timer
- machine.UART
- machine.SD