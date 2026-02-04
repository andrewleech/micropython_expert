Cortex M4
* GHI Electronics FEZ Cerb40 II https://www.ghielectronics.com/catalog/product/450

###Features###
* STM32F405RGT6 ARM 32 bit CORTEX M4™ 168MHz
* 1024KB FLASH, 192kB SRAM
* 12 MHz crystal
* 32.768 kHz RTC Crystal
* MiniUSB connector
* on-board 3.3V regulator

This is basically about as bare bones as you can get for an STM32F405 board.

###Status###
Supported using BOARD=CERB40

To flash, connect the LOADER pin to 3.3V while resetting (or plugging in the USB). This will put the board into DFU mode.

Remaining instructions are as per pyboard.