### Overview
There are 10 Timers on the STM32F405 chip being used by the mircropython KS project. Not all Timers have pins allocated to them on this 64 pin package. (The 407 based chipsets have the same allocation of timers.)
Timers in this chipset come with various capabilities:
* TIM1 and TIM8 are advanced 16 bit timers and can count up and down. They can be used to drive steppers or 3 phase motors. They have special trigger and brake input pins to support this. They are the only timers with pinouts defined for complementary outputs. I.e. they can drive three channels of two pins up and down in perfect synchronisation. They are capable of driving 4 channels for output.
* TIM2 and TIM5 are 32 bit Timers. TIM2 can be triggered by an external signal. Both TIM2 and 5 have 4 channels.
* TIM3 and TIM4 are 16 bit timers. Both have 4 channels but TIM3 has more pins allocated.
* TIM9 and TIM12 are 2 channel timers. Only TIM9 has pins.
* TIM10 and TIM11 have a single output channel each.
* The remaining Timers 6,7,13,14 do not have any pin connections on the 64 pin package.
All timers can be used to generate timebases. Most can do PWM generation. A digram below shows how timers can be cascaded to make longer or triggered timings. Most triggers can also generate Interrupts.

The following timers can sample an input signal and determine its period. `1,2,3,4,5,8,9,10,11`

These Timers can be used to correctly determine speed and direction from externally supplied quadrature signals. `1,2,3,4,5,8,9`

* [[STM32F405 pinouts]]
* [[STM32F405 Timer Triggering]]
* [[clock source and Timebase calculations| Timebase-calculation-and-Clock-sources]]
* [[Single shot timer setup|Timer-one-shot]]
* [[Capture mode|Timer-capture-mode]]
* [[Implementation|Timer-Implementation]]

### Timer Summary:
Advanced - TIM1,8
* 16bit, 4 channels (2x complementary)
* can generate up to three complementary outputs with insertion of dead time
  * ideal for motor control.
  * seen as three phase PWM generators multiplexed on 6 channels
* max speed 168 MHz, max interface speed 84 MHz
* independent DMA request generation
* as 16bit PWM generators they have full 100% modulation capability
* TIM1 can be slaved to TIM5,2,3,4
* TIM8 can be slaved to TIM1,2,4,5

GP 16bit - TIM3,4
* 4 channels (not complementary)
* timing, delay, one pulse, input capture, encoder input
* up, down count with DMA control, Master/slave
* can generate PWM output
* 16 bit prescaler
* max speed 84 MHz, max interface speed 42 MHz
* TIM3 can be slaved to TIM1,2,5,4
* TIM4 can be slaved to TIM1,2,3,8

GP 32bit - TIM2,5
* 4 channels (not complementary)
* timing, delay, one pulse, input capture, encoder input
* up, down count with DMA control, Master/slave
* can generate PWM output
* 16 bit prescaler
* max speed 84 MHz, max interface speed 42 MHz
* TIM2 can be slaved to TIM1,8,3,4
* TIM5 can be slaved to TIM2,3,4,8

Basic - TIM6,7
* 0 channels - no direct external pin control.
* must be Masters
* up count only with DMA control
* 16 bit prescaler
* used for timebase timers or triggering the DAC
* max speed 84 MHz, max interface speed 42 MHz

1 channel - TIM10,11,13,14
* general purpose timers
* up count only, no DMA control
* can generate PWM output
* 16 bit prescaler
* must be Masters
* TIM13,14 - max speed 84 MHz, max interface speed 42 MHz
* TIM10,11 - max speed 168 MHz, max interface speed 84 MHz

2 channel - TIM9,12
* 2 independent channels
* general purpose timers, Master/slave
* up count only, no DMA control
* can generate PWM output
* 16 bit prescaler
* TIM12 - max speed 84 MHz, max interface speed 42 MHz
* TIM9 - max speed 168 MHz, max interface speed 84 MHz
* TIM12 can be slaved to TIM4,5,13,14
* TIM9 can be slaved to TIM2,3,10,11
Independent watchdog
* 12 bit downcounter and 8 bit prescaler
* driven from independent 32kHz rc clock
* operates in stop or standby mode and can reset the device
* can be used as free running app  timeout counter

Window watchdog
* free running 7bit downcounter
* clocked from main clock
* can reset the device or generate interrupt

SysTick timer
* 24 bit downcounter from main clock
* autoreload capability
* maskable interrupt on = 0