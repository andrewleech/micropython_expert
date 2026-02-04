Cortex M4 STM32F407ZGT6 
* [Olimex Shop](https://www.olimex.com/Products/ARM/ST/STM32-E407/open-source-hardware)
* [Manual](https://www.olimex.com/Products/ARM/ST/STM32-E407/resources/STM32-E407.pdf)
* [OpenOCD configuration](https://www.olimex.com/Products/ARM/ST/STM32-E407/resources/stm32f4x.cfg)

###Features###
* STM32F407ZGT6 168MHz
* 1024KB flash ROM, 192KB RAM
* 3 x 12-bit 2.4 MSPS A/D
* 2 x 12-bit D/A converters
* USB OTG FS and USB OTG HS
* Ethernet 100Mbit
* 14 timers
* 3 x SPI
* 3 x I2C
* 2 CANs
* 114 GPIOsC
* Camera interface
* JTAG connector with ARM 2x10 pin layout for programming/debugging
* UEXT connector
* SD-card
* Power and user LED
* Reset and user button
* 4 full 20-pin Ports with the external memory bus for add-on modules Arduino platform with unsoldered headers
* Dimensions: 101.6 x 86mm (4 x 3.4")

###Status###
* Initial support has been implemented  
 * Working: GPIO, DAC, Timer, CAN, LED, Switch, REPL  
 * Not tested: SD-Card  
 * Not working: Ethernet  
* To build use one of the following methods:
   1. ```make BOARD=OLIMEX_E407```
   2. ```export BOARD=OLIMEX_E407``` in your environment and then just use make.
