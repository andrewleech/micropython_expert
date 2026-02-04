Status "not officially supported but should be fully functional" as of 2018-08.  Pre-built DFU binaries are [available](https://micropython.org/download#other) for this board.

# Pages elsewhere

 * [mBed page](https://os.mbed.com/platforms/ST-Nucleo-F767ZI/)
 * [ST's page for this Nucleo](https://www.st.com/content/st_com/en/products/evaluation-tools/product-evaluation-tools/mcu-eval-tools/stm32-mcu-eval-tools/stm32-mcu-nucleo/nucleo-f767zi.html)
 * [ST's page for this MCU](https://www.st.com/en/microcontrollers/stm32f767zi.html)

# Features

 * STM32F767ZI (LQFP-144) at up to 216 MHz
 * 2MiB flash, 512KiB RAM
 * three user LEDs
 * one user button
 * USB OTG
 * Ethernet port (probably not yet supported by uPy)

# Caveats

The default build for the board only exposes the Arduino compatibility pins plus the "Zio" ones up to D25 (i.e. the rest are not in `pyb.Pin.cpu` nor `machine.Pin.cpu`).  Tuple-based access is documented but doesn't seem to exist.  So you'll need to edit `pins.csv`, [add the rest](https://gist.github.com/zwbrbr/f9202e3cc9288b459b8b116b83125c06) and rebuild to get access to them.

# Flashing

Probably requires newer OpenOCD than 0.9.0, which complained "Cannot identify target as a STM32 family" despite getting a device ID.

To steer the target into DFU mode, temporarily pull `BOOT0` high (connect CN11 pin 7 to CN11 pin 16; see the mBed page for pretty diagrams) while plugging the STLink USB into the host.  As soon as it's plugged in you can remove the connection.  Then use the usual DFU flashing described in the README.