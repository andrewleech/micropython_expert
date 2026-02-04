This page gives a quick overview of how to build and install stlink (which includes st-flash).

These instructions were done under Ubuntu 14.04 LTS.

###Install Pre-requisites###
You'll need some build tools. It's possible that there are some prerequisites missing here.
```
sudo apt-get install libusb-dev
sudo apt-get install autoconf
sudo apt-get install build-essential
```

###Build stlink###
```
git clone https://github.com/texane/stlink
cd stlink
./autogen.sh
./configure
make
sudo make install
```

###Install udev rules###
```
sudo cp 49*.rules /etc/udev/rules.d
udevadm control --reload-rules
udevadm trigger
```

###Flashing MicroPython using st-flash###
I normally create a GNUmakefile (in the stmhal directory) which looks something like the following:
```
$(info Executing GNUmakefile)

BOARD = STM32F7DISC
$(info BOARD = $(BOARD))

include Makefile

.PHONY: stlink
stlink: $(BUILD)/firmware.elf
	$(ECHO) "Writing flash"
	$(Q)$(OBJCOPY) -O binary -j .isr_vector $^ $(BUILD)/firmware0.bin
	$(Q)st-flash write $(BUILD)/firmware0.bin 0x08000000
	$(Q)$(OBJCOPY) -O binary -j .text -j .data $^ $(BUILD)/firmware1.bin
	$(Q)st-flash --reset write $(BUILD)/firmware1.bin 0x08020000
```
and then you can use ```make stlink``` to flash the micropython image using st-flash