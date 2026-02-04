NUCLEO-F401RE
* [Home](http://www.st.com/web/catalog/tools/FM116/SC959/SS1532/LN1847/PF260000?icmp=nucleo-ipf_pron_pr-nucleo_feb2014&sc=nucleoF401RE-pr)
* [Datasheet](http://www.st.com/st-web-ui/static/active/en/resource/technical/document/data_brief/DM00105918.pdf)
* [User Manual](http://www.st.com/resource/en/user_manual/dm00105823.pdf)

### Features ###
* STM32F401RE ARM 32 bit CORTEX M4™ 84MHz (64pin)
* 512KB FLASH, 96kB SRAM
* 1x ADC 12 bit
* 3 TIMERS - up to 72Mhz
* 2 I2C, 2 UART, 2 SPI
* 1 user LED
* 1 user switch
* Reset switch
* Arduino pin headers
* Additional Morpho headers
* mbed enabled

### Status ###
* Supported

### How to build ###
`cd ports/stm32`
`make BOARD=NUCLEO_F401RE`

### How to deploy ###
`make BOARD=NUCLEO_F401RE deploy-stlink`

NOTE: This command will also build micropython if not built before

### Important notes on HW revisions of the board ###
Some NUCLEO_F401RE boards come in different hardware revisions, which is located on a sticker at the backside of the board. The revision C-01 has a different configuration for the high speed external clock (HSE). This could be fixed by reconfiguring some solder bridges as mentioned in the user manual, section 6.7.1.
To ensure an "out of the box" working experience, Micropython is configured to use the HSI oscillator as the PLL source on these board. However on later revisions (C-02, C-03 at time of writing) the PLL source can be switched to use the HSE by modifying the defines in `mpconfigboard.h` (see comments in file).

The other issue is, that revision C-01 also has no 32kHz oscillator.