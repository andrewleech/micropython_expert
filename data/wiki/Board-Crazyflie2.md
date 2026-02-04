STM32F405 main application MCU (Cortex-M4, 168MHz, 192kb SRAM, 1Mb flash)

nRF51822 radio and power management MCU (Cortex-M0, 32Mhz, 16kb SRAM, 128kb flash)

* Home: http://www.bitcraze.se/getting-started-with-the-crazyflie-2-0/
* Wiki: http://wiki.bitcraze.se/projects:crazyflie2:index
* Forum: http://forum.bitcraze.se/
* Spec: http://wiki.bitcraze.se/projects:crazyflie2:hardware:specification
* Schematics: http://wiki.bitcraze.se/projects:crazyflie2:hardware:schematics

### Features ###
 * Dual MCU (main MCU and comms processor)
 * On board radio with custom comms protocol or Bluetooth LE
 * On Board LiPo charger
 * 3 axis gyro (MPU-9250)
 * 3 axis accelerometer (MPU-9250)
 * 3 axis magnetometer (MPU-9250)
 * High precision pressure sensor (LPS25H)
 * 8KB EEPROM
 * 5 user accessible LEDs
 * 4 User controllable motors (PWM)
 * Expansion board support with auto detection (LED ring, Near Field Charging, Breakout board)

### Status ###
 * LEDs can be turned on/off
 * I2C bus 1 working (EEPROM)
 * I2C bus 3 working (IMU/MPU)
 * PWM control of motors

### TODO ###
 * Wrapper/lib for IMU/MPU
 * Wrapper/lib for Pressure sensor
 * Wrapper/lib for motor control
 * One wire bit banging support for expansion board detection and initialisation

### Building/Flashing ###
To place the crazyflie2 into DFU mode:

 * Remove all power (battery and usb)
 * Hold down button
 * Insert power
 * Blue light will go solid blue
 * Blue light will start blinking
 * Blue light will start blinking rapidly
 * Once the Blue light starts blinking rapidly release the button and plug into your computer, it will show up in DFU mode and the instructions below can be used to flash it

---
    git clone -b crazyflie2 https://github.com/exec-all/micropython/
    BOARD=CRAZYFLIE2 make
    dfu-util -a 0 -D build-CRAZYFLIE2/firmware.dfu