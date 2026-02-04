An ARM Cortex M3 CPU with a little 'FPGA' on-board.
* http://freesoc.myshopify.com/products/freesoc-development-kit

###Features###
* 32-bit Arm Cortex M3
* 67MHz Operation, 256KB Flash Memory, and 64KB SRAM
  * A graphically configurable external memory interface allows you to expand the storage of your device with up to 1GB of external memory, directly mapped in the 4GB address space of the Cortex M3.
* Hardware multiply and divide operations
* Analog
  * Dual 12-bit, 700ksps SAR ADCs 
  * Delta Sigma ADC 8-20 bits, 180 sps (16bit 48Ks) (8bit 384Ks)
  * Quad 8-bit 5.5Msps IDACs or 1Msps on each DAC
  * 4 Quad comparators
  * 4 Quad Rail-to-Rail OpAmps, 3MHz GBW and 10mA drive
  * CapSense on all GPIOs
  * Quad Multifunction Analog Blocks.
    * E.g. programmable gain amplifier, transimpedance amplifier, or sample and hold.
  * Advanced I/O Routing Network. Route any analog peripheral to any GPIO pin.
    * E.g. Use freeSoC as a 32 channel analog multiplexer, or 16-channel differential mux.
  * 24 PLD based Universal Digital Blocks (UDBs). These are the heart of freeSoC's digital flexibility.
    * Can be configured graphically with built in components like PWM, SPI, I2C, LIN, CAN, SPDIF, I2S, Quadrature Decoders, Counters, CRC, and standard digital logic gates.
  * Or roll your own using Verilog
  * Full Speed USB
  * 4 16bit counter/Timer blocks
  * 4 dedicated PWM blocks
  * RTC
  * 8 special I/O pins for high-current drive applications

###Status###
No work has yet been done on porting to this chip