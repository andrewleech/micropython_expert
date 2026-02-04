_This entire page is wildly out of date as Servo now implemented._

This page is about a mechanism for controlling Hobby Servos. There are two main kinds of Hobby Servo. Analog and Digital. Both are controlled identically. Digital servos can be updated more frequently.

For the complete list of servos and their specs you can't go past http://www.servodatabase.com/
Each servo is listed with its update rate (pulse cycle) and pulse width.

####Analog servos:
* Cheap.
* Generally have +/-90 degree rotations about a centered rest position
  * but can also be continuous rotation or other ranges (e.g. +/- 180 degree).
* Use a PWM mechanism (but not standard PWM) to control their desired position with a central frequency approximately 1500 usecs (666 Hz).
* Need to get updates at from 20-65 times per second (Hz).

####Digital servos:
* have a higher refresh frequency - upto 400Hz and therefore:
  * hold position better, 
  * have better torque, speed, and accuracy
  * therefore use more power.
  * This higher rate is handled internally and so the digital servo keeps updating its position even when it receives external updates infrequently.
  * but if signals are received at a higher rate the servo can update more responsively.
* more expensive than analog.
* some also have other communication options. E.g. serial ports.
  * This Servo class is for traditional PWM control only and does not address these.

####PWM
So we need a PWM signal to control them. This is not the 'normal' use of PWM where the position is set by duty cycle (perhaps by integrating voltage over time as used for dimming Leds). This method is based on individual pulse widths, not a chain of pulses. This method is used because a R/C vehicle may lose its signal from time to time and the servos must stay in position in the absence of any pulse train.

So the pulse widths are: notionally 1ms (1000us) = full CCW rotation, 1.5ms (1500us) = detent, center, rest position, and 2ms (2000us) is maximum CW rotation. This 'standard' is not always used (detent may be at 1.8ms and maximum at 2.6ms). So we need these values to be adjustable.

The pulses are typically sent at 20Hz with rates as high as 65Hz. This is a repetition with a period of 50-15ms.

PWM signals can be generated in hardware or software.
The exact update frquency is (as mentioned) not critical but the pulse width is.We need to define the rest position accurately enough that the servo can sit in its rest position without jittering.

####Useful aspects to control:
* How many servos to control
  * more servos means less time spent on each one (in a loop) and a lower update rate.
  * resulting in 'soft' servo positioning where the servo will move if it is under load (which sometimes doesn't matter).
* PWM frequency range - from 1ms (1kHz) to 1.5ms (666kHz), to a max of 3ms (333kHz).
* PWM frequency accuracy especially around 1.5ms
  * 8 bit PWM would give us 255 steps. This can make it difficult to get the stationary center position. 
  * 12 bits gives us 4096 steps
  * Actual clock freq and accuracy is a function of many aspects of clocks in a chipset.
  *  Accuracy around 1.5ms is what's important.
* Update rate of 20-65 Hz

####Calculations:
If we update every 20ms and we have a maximum pulse width of 3ms - we can cycle through 6 servo pins with that signal. As we change update rates we get less servo pins we can service before the cycle is up.
Table period vs number of servos with a single PWM generator
```
Period  Freq    Max pulse width
                  3ms     2ms 
20Hz   (50ms)     16      25   servos
30Hz   (33ms)     11      16   servos
40Hz   (25ms)      8      12   servos
50Hz   (20ms)      6      10   servos  * standard update rate
60Hz   (17ms)      5       8   servos
70Hz   (14ms)      3       7   servos
```
So if we add more parallel timers we can service more servos.
This suggests the following mechanism:

**Using hardware timers:**

Where S = number of servos and R = rate of update in Hz.

1. Allocate a number of Timers based on the update rate and number of servos.
  * This can be minimised by querying the servos maximum pulse widths and calculating the maximum servos possible for that update rate and number of servos. Or conservatively, using the table above.
  * I.e. if need 50Hz and 12 servos then need 2 timers.
  * When you run out of Timers then update rate drops.

2. Have a software interrupt routine per Timer which interrupts R times a second and:
  * steps to the next servo in the list of servos for that Timer
  * reads the pin and pulse_width required for that servo from the python class.
  * sets the PWM freq to that pulse width
  * outputs the pulse on correct pin using anoeyhr s/w interrupt or hardware timer.
  * sleeps

The top level python structure sets the servo instances up and adds them to a servo pool. Which manages how many servos are in a Timer queue and setting up and activating the timer interrupt routines.

**Using Software timer:**

Need different interrupt routines for setting and resetting the pulses. No reason why it can't be as efficient as the hardware version.


####Hardware considerations:
The pyboard has 23 pins that can output hardware PWM. It has 12x 16bit timers and 2x 32bit timers. Only 4 pins are configured with servo headers on the main board but this is obviously for convenience only.

The Teensy3.1 has 12 pins that can output PWM but (I think) only 3 Timers. So a software interrupt routine would be an excellent library for the Teensy. The Teensy 3.1 has PWM 12bit resolution. Some data here: https://www.pjrc.com/teensy/td_pulse.html

####Implementation
The actual implementation on the pyboard is set to only adjust the 4 lines dedicated to Servo control.
The code wouuld need to be updated or replaced to drive more pins as servos.
The Servo is driven by hardware using TIM5 which neatly is designed to control exactly the four pins allocated to Servos on the Pyboard.

