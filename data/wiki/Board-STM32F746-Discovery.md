Cortex M7 STM32F746G 
* [STM32F7 Discovery Home Page](http://www.st.com/stm32f7-discovery)
* [STM32F746xx Datasheet](http://www.st.com/st-web-ui/static/active/en/resource/technical/document/data_brief/DM00037955.pdf)
* [STM32F74xxx Reference Manual](http://www.st.com/web/en/resource/technical/document/reference_manual/DM00124865.pdf)
* [Board User Manual](http://www.st.com/st-web-ui/static/active/en/resource/technical/document/user_manual/DM00190424.pdf)

### Features
* STM32F746NGH6U 216MHz (216pin TFBGA)
* 1024KB flash ROM, 320KB RAM
* USB OTG FS/HS, camera interface, Ethernet, LCD-TFT
* SAI Audio DAC stereo with audio jack input and output
* Stereo MEMS digital microphones
* sdcard connector
* 1 user LED
* 1 user switch
* Reset switch
* Arduino Uno V3 connectors
* Integrated ST-LINK/V2-1

### Status
* I think that this board now has as much support as the pyboard.
* Things which are not working (or haven't been tested):
  * SDRAM (16 Mbytes - 8 Mbytes accessible)
  * QSPI Flash memory (16 MBytes)
  * LCD
  * touch interface
  * camera interface
  * audio stuff
  * ethernet
* Use BOARD=STM32F7DISC to build micropython

### Powering the Board
It is recommended that you power the board using the 5V connector or via a powered USB hub which is capable of delivering an amp or two. In my current setup the board is drawing about 850 mA with the backlight off.
I've been using this hub: http://www.adafruit.com/products/961 I've also run the board without a hub (and the PC was limiting the current to 500 mA), which means that something was suffering for not having as much current.

### Entering DFU mode
The board doesn't provide a convenient way to enter DFU mode. There are several techniques that can be used to enter DFU mode.
DFU mode is available on the USB FS connector (CN13)
* You can short the pads where R42 would be installed (it isn't installed by default) and press the reset button. You should now be able see the board when using ```dfu-util -l```
* I chose to install a switch between the MCU side of R42 and 3.3v (see picture below).
* You can install the initial micropython image using the STLINK interface, and then use pyb.bootloader() to enter DFU mode from the REPL. See the [[Building st-flash|Building-st-flash]] page for some instructions on how to build st-flash.

Here is a link to a photo of [my modified STM32F7 Disocvery Board](https://www.dropbox.com/s/bbypmt8tennczh7/STM32F7-Discovery.jpg?dl=0)
The white wire connects to R42. CN13 has a USB cable plugged into it. The FTDI board is plugged into D0 (RX) and D1 (TX).
The red wire connects to 3.3v on R39.

### REPL
UART1 from the STM32F7 is connected to the stlink MCU, and until USB-serial is working, the software is configured to have a REPL on UART1. The stlink MCU acts as a USB serial dongle.

I use the following file (which I call 49-stm32.rules):
```
# 0483:5740 - STM32F4/F7 Dsicovery in USB Serial Mode
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", ENV{ID_MM_DEVICE_IGNORE}="1"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", ENV{MTP_NO_PROBE}="1"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE:="0666"
KERNEL=="ttyACM*", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE:="0666"

# 0483:df11 - STM32F4/F7 Discovery in DFU mode
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", MODE:="0666"
```
and install it using:
```
sudo cp 49-stm32.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
sudo udevadm trigger
```
That covers off DFU mode and the USB-serial link from CN14 (labelled USB ST-LINK, mini B connector). CN13 (labelled USB_FS, micro B connector) goes directly to the F7.