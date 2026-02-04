STMF405RG (same as micropython original Pyboard)
* Home - http://netduino.com/netduinoplus2/specs.htm
* Wiki - http://forums.netduino.com/index.php?showtopic=6554

###Features###
* same as pyboard but:
  * more GPIO pins broken out
  * Ethernet port
  * Arduino formfactor

###Status###
Initial port completed.
* pyb.Led(1) controls the Blue LED
* pyb.Led(2) controls the White LED
* pyb.switch() returns True if the pushbutton is pushed
* 5V and 3.3v is enabled on the expansion header

To build, follow the directions for the [[STM Discovery STM32F407|Board-STM32F407-Discovery]], but use a ```BOARD``` of ```NETDUINO_PLUS_2```.

###Programming from Linux (via DFU)###
This is the same as is done for the [[STM Discovery STM32F407|Board-STM32F407-Discovery]]

The push button on the board is connected to BOOT0. You'll need to wire up an external pushbutton to control the RESET line.