##  Introduction.

Software bugs, unforseen sequences of events and hardware events such us power glitches, transients from motors, ESD (electrostatic discharge) can cause an MCU to crash and stop running properly. Common failures are corruption of RAM and registers including the program counter. The program may jump to a different place and continue to run, but using corrupt parameters or it may get into and endless loop of doing nothing, or worse enabling or disabling an output it shouldn't. Watchdog timers and service routines (or Computer Operating Properly - COP in Freescale talk) can save the day by detecting these failures and resetting the MCU or system.

The purpose of this page is to (1) examine best practice in watchdog systems, (2) examine the hardware capabilities of target MCU's for Micro Python and (3) propose a solution for two independent watchdog systems - firstly a build in watchdog service in Micro Python and secondly the framework for users to add a more robust system in their Python code.

##  1. Best practice.
* If there is a fuse map of flash configuration to enable the watchdog use it. Don't rely on software to enable the WDT.
* Use an external watchdog timer with and independent timer.
* If you have to use in internal watchdog timer it should run from a different oscillator to the main program, eg an RC oscillator or the 32 kHz oscillator.
* Timer ISR's often continue to run after a crash. If the watchdog is serviced in an ISR it must check for correct operation of all tasks or functions before servicing the watchdog.
* Do not scatter watchdog tickles throughout the program. Use a single watchdog task (WDSR) that runs periodically (from timer or in the main loop) and services the watchdog after checking all tasks or functions.
* If the system has a memory management or memory protection unit use it to protect the WDT registers from all access except from the WDSR.
* For non multitasking systems create a single variable that is reset at the start of the main loop and modified by each function in the loop. The last function in the loop is the WDSR and it verifies the value. The value will only be correct if all functions have run. If correct tickle the watchdog and reset the variable.
* For multitasking systems create an array of integer counters, one for each task. Each task increments it counter as it runs. Periodically the WDSR checks that the count values are reasonable, tickles the WDT and resets the counters.
* Do not rely on a WDT that calls an NMI. Always force a hard reset of the MCU and peripherals.
* If the WDT is only serviced in the main loop it may not detect failure of timers or ISR's, The WDSR should check that ISR's are running before tickling the WDT.
* The WDSR should not trust the WDT. Its oscillator may have stopped or it may have been disabled by a crash. When the WDSR detects a failure (by analysing code behaviour) it should disable interrupts spin in a delay loop for a period longer than the WDT timeout then do a software reset. This gives the WDT a chance to do a proper hardware reset, but if that fails a software reset will occur.
* Non-periodic functions need special handling. For example a command interpreter may only be called after a command is received by the UART ISR. The ISR can set a flag to inform the WDSR that a function should be running.
* Vendor supplied libraries may take a long time to initialise. If so start the WDT with a long timeout and change it after initialisation is complete.
* If functions run less frequently than the WDT timeout period the WDSR can run under a timer ISR and tickle the watchdog frequently, whilst checking the system health only after multiple intervals.. There is some risk that the counter could be corrupted.




## 2. Hardware capabilities.
* STM32F405 (pyboard). Independent Watchdog Timer (IWDT) with its own RC oscillator. Separate Window Watchdog Timer (WWDT) using system clock.

## 3a.  Built in Watchdog.
* Use the IWDT in Micro Python. This will recover from most hardware events and some software events.
* The IWDT will detect an oscillator (crystal failure). See if the STM32 can test the crystal oscillator after reset and run with the high speed RC oscillator if the crystal is dead.

## 3b. User Watchdog.
* Use the WWDT for user programs. Provide hooks in Micro Python for user Python code to manage this Watchdog.

## 4. Glossary
* WDT Watchdog timer. Hardware in the MCU or an external IC.
* WDSR.  Watchdog Service Routine. Software that services the watchdog to prevent it resetting the MCU.
* ISR.  Interrupt Service Routine.

## 5. References.

* Great Watchdog Timers For Embedded Systems. Jack Ganssle. Version 1.3, updated September, 2011. http://www.ganssle.com/watchdogs.htm
* Watching the Watchdog. Jack Ganssle. http://www.embedded.com/print/4024522
* A Designer's Guide to Watchdog Timers. Jack Ganssle. Contributed By Convergence Promotions LLC . http://www.digikey.com/en-US/articles/techzone/2012/may/a-designers-guide-to-watchdog-timers
* Watchdog Timer Techniques. John Santic. http://johnsantic.com/comp/wdt.html
* Creating Robust Watchdog Timers. Bob Japenga. http://www.microtoolsinc.com/RobustGuidelines7.pdf
* Watchdog Timers. Niall Murphy. http://www.barrgroup.com/Embedded-Systems/How-To/Advanced-Watchdog-Timer-Tips

