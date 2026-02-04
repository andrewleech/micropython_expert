STM32F401CDU6 (smaller version of the processor used on the pyboard)
* Home - http://www.espruino.com/Pico

###Features###
* 84 MHz
* 384K Flash
* 96K RAM

###Building###
To build, follow the directions for the [[STM Discovery STM32F407|Board-STM32F407-Discovery]], but use a ```BOARD``` of ```ESPRUINO_PICO```.

Getting the Espruino Pico into DFU mode requires some contortions. On the bottom of the board there is a set of BOOT0/BTN pads. Shorting (with a solder blob, or by rubbing an HB pencil across the gap) connects the push button on the top of the board to BOOT0. Press the button, and plug into USB while continuing to press the button.

The board should boot up in DFU mode. Once flashed with Micropython firmware, I find using the pyb.bootloader() command from the REPL to be a more convenient way of entering DFU mode.


