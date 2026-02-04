STM32F405RGT6 (same processor as used on the pyboard)
* Home - https://www.ghielectronics.com/catalog/product/450

###Features###
* 168 MHz
* 1 Mb Flash
* 192K RAM

###Building###
To build, follow the directions for the [[STM Discovery STM32F407|Board-STM32F407-Discovery]], but use a ```BOARD``` of ```CERB40```.

To enter DFU mode, connect the LODR pin to 3.3v and plug into USB (or reset the processor by momentarily connecting the REST pin to ground)

The board should boot up in DFU mode. Once flashed with Micropython firmware, I find using the pyb.bootloader() command from the REPL to be a more convenient way of entering DFU mode.


