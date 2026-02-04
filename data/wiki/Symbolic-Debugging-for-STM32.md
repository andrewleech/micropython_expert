# How to on symbolic debugging  

> So also: [Programming/Debugging using ST-Link/v2](https://github.com/micropython/micropython/wiki/Programming-Debugging-the-pyboard-using-ST-Link-v2)

Symbolic debugging needs a wired link to the "SWD" pins on the PYBV10. On the pyboard these are shared with the Red and Green leds so they need to be not used when debugging.

The steps for symbolic debugging 

* a) wire an ST-Link to the PYBV10. ST-links come with all the low cost ST  NUCLEO & Discovery line of boards. The NUCLEO boards are setup to easly  

* b) build an image with symbolics and no code optomization (S0)and use an interface that drives the ST-Link (eg openStem32.org's AC6 Eclipse)

## hardware wires from ST-LINK to pyboard
Nucleo-F401RE CN4----PYBV10  

1-open  

2-JTCK/SWCLK ------- X20-2 (red)     PA13-RED-P5/Led-Red  

3 GND  ------------------- GND   (blue) 

4 JTMS/SWDIO-------- X21-2  (White)  PA14-GRN-P4/LED-Green  

5 NRST ------------------ X13    (red)  

6-open  

I used a 0.1" SIL connector that I had lying around and wire-wrap to link the Nucleo-F401RE CN4 connector to wires soldered to the pyboard. (The Nucleo-F401RE was a "could be interesting purchase" I made 1yr ago) 
The Nucleo-F401RE CN4 is a 0.1 Single In Line (SIL) male connector, so I can use the female connector to plugin to CN4. Not ideal but works.  

The Nucleo-F401RE board also has two "ST-LINK" jumpers that need to be removed to make the signals available to CN4.  
 

**Note:** I anchored the wires by weaving them through adjacent holes, when soldering to the pyboard so that the stress of moving the boards didn't wiggle the wire. The wire is at its most vulnerable point where it is soldered to the board.

![pyBoard wired to a ST-LINK on a Nucleo-F401RE](http://forum.micropython.org/download/file.php?id=159)


## symbolic debugging 
Symbolic debugging is useful for checking out the interface to hardware - single stepping through each line of code, and looking at the registers/variables. Symbolic debugging often relies on a toolchain that can be difficult to get right - so often its more pain to setup and debug the debugger than it is to use other methods. 
Retrofitting symbolic debugging to a large project often doesn't work - so it may not work for the main python code but can be very useful for some integration testing. Your mileage may vary.

STM has developed and made widely available low cost ST-Link. (This is fantastic as its reasonably simply hardware but complex software to access the internals of the processor - other manufacturers let 3rd party's supply commercial debugging hardware)

STM is also supporting an freely downloadable symbolic debugger tool chain at OpenSTM32.org. 
If you've used another symbolic debugger with the pyboard please list it here.

STM's documents:  

ST TN0072 -Software toolchains and STM32 features 

### OpenSTM32.org
This is an Eclipse Lunar based toolchain for both Linux and Windows. 

I've used it to take a STM32cubeMX example and customize it for the pyboard. As of writing (2015Nov) it doesn't accept the stmhal/build-PYBV10/firmware.ELF.  

Download/install the " [System Workbench for STM32](http://www.openstm32.org/System+Workbench+for+STM32)" - 

### ST-Link Upload
The ST-Link can  be used to upload to the board, see [Building ST-Flash](https://github.com/micropython/micropython/wiki/Building-st-flash).

There is also an STM "STM32 ST-Link Utility" (Windows?)that can be used to verify the ST-Link works and to program to memory 


