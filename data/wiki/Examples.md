# Examples

This page provides some examples to get you started on using micropython and the pyboard.

## SDdatalogger

[SDdatalogger in the repository](https://github.com/micropython/micropython/tree/master/examples/SDdatalogger)

The board has a SD-card slot, 4 LEDs, one user programmable switch, a reset switch and a built-in accelerometer with a range of +/-1.5g.
In this example we wan't to log the data from the accelerometer to a file on the SD-card.

Now ,the first problem with that is, that when the pyboard is connected to the computer, the computer mounts the filesystem. At the same time, the microcontroller is using the filesystem which results in broken files. So what we have to do is to tell the pyboard to NOT act as mass storage device, so the filesystem isn't mounted.
To do that, we change boot.py. boot.py is the first script that is run after boot.

```python
# boot.py -- runs on boot-up

import pyb

pyb.usb_mode('CDC+HID')
```

`import pyb` imports the pyb module, that let's you access the functions and methods for controlling the pyboard. `pyb.usb_mode()` let's you set as what kind of device the pyboard should act if connected to USB. `'CDC+HID'` means 'Human Interface Device' - in this mode the board is recognized as if it were a mouse or keyboard. In this example, this only means that it is NOT recognized as mass storage device, so the file system doesn't get mounted.
The problem is, now we can't access the filesystem anymore, so you'd have to remove the SD-card and put it into a SD-card reader to get back your data or to change the scripts again. Now, if we set `pyb.usb_mode()` back to `'CDC+MSC'`, the pyboard would act as SD-card reader. So, we use the switch to change between these modes. After reset, you have a short time window. If the switch is pressed and hold, the board acts as mass storage, if not it acts as Human Interface Device.

```python
# boot.py -- runs on boot-up

import pyb

pyb.LED(3).on()                 # indicate we are waiting for switch press
pyb.delay(2000)                 # wait for user to maybe press the switch
switch_value = pyb.Switch()()   # sample the switch at end of delay
pyb.LED(3).off()                # indicate that we finished waiting for the switch

pyb.LED(4).on()                 # indicate that we are selecting the mode

if switch_value:
    pyb.usb_mode('CDC+MSC')
else:
    pyb.usb_mode('CDC+HID')

pyb.LED(4).off()                # indicate that we finished selecting the mode
```

So, now when the switch was pressed, we can access the data, if not, the filesystem is left untouched by the computer and only used by the microcontroller. But until now, the board only switches its states, but doesn't do anything else. Using `pyb.main()`, we can tell the microcontroller which script to execute after 'boot.py'. If we chose HID-mode, we wan't to log data, so we call a script called 'datalogger.py'. If the cardreader-mode was selected, we call 'cardreader.py'.
So we add these calls to the if-clauses:

```python
if switch_value:
    pyb.usb_mode('CDC+MSC')
    pyb.main('cardreader.py')           # if switch was pressed - cardreader-mode
else:
    pyb.usb_mode('CDC+HID')
    pyb.main('datalogger.py')           # if switch wasn't pressed - datalogger-mode
```

'cardreader.py' can be empty, it doesn't have to do anything. We just want't to use the filesystem.
'datalogger.py' contains the actual script for logging the data. We `import pyb` again and create objects of the stuff we want to use.

```python
import pyb

# creating objects
accel = pyb.Accel()        # accelerometer object
blue = pyb.LED(4)          # LED object
switch = pyb.Switch()      # switch object
```

Now we need to get the data and write it to a file.

```python
log = open('1:/log.csv', 'w')               # open file on SD (SD: '1:/', flash: '0/)
t = pyb.millis()                            # get time
x, y, z = accel.filtered_xyz()              # get acceleration data
log.write('{},{},{},{}\n'.format(t,x,y,z))  # write data to file
log.close()                                 # close file
```

This would measure only one time, but we want to have a continuous measurement, so we put it in loop that runs forever.

```python
while True:     # runs forever

    log = open('1:/log.csv', 'w')               # open file on SD (SD: '1:/', flash: '0/)
    t = pyb.millis()                            # get time
    x, y, z = accel.filtered_xyz()              # get acceleration data
    log.write('{},{},{},{}\n'.format(t,x,y,z))  # write data to file
    log.close()                                 # close file
```

Still not there. This way, the file would be opened and closed every time the loop runs. Also, the file would be overwritten every time. And if we disconnect the power with the file still being open, it will get corrupted. So let's use the user switch to start and end a loop. If the switch is pressed, the file is opened and data is written to it. When it get's pressed again, the file is closed.

```python
while True:

    # start if switch is pressed
    if switch():
        log = open('1:/log.csv', 'w')       # open file on SD (SD: '1:/', flash: '0/)

        # until switch is pressed again
        while not switch():
            t = pyb.millis()                            # get time
            x, y, z = accel.filtered_xyz()              # get acceleration data
            log.write('{},{},{},{}\n'.format(t,x,y,z))  # write data to file

        # end after switch is pressed again
        log.close()                         # close file
```

If you try that, you will run into another problem. If you press the switch, the write loop will start immediately. This loop also checks if the switch is pressed, so unlike you get your fingers off the switch _really_ quickly, it will detect the switch as pressed. To avoid that, we add a `pyb.delay(200)`. That will pause the board for 200 milliseconds (0.2 seconds), which gives you enough time to get your hands of the switch. We need to call that every time between `switch()` is called. We also add the blue LED now. It is on as long as the file is open.

```python
    # start if switch is pressed
    if switch():
        pyb.delay(200)                      # delay avoids detection of multiple presses
        blue.on()                           # blue LED indicates file open
        log = open('1:/log.csv', 'w')       # open file on SD (SD: '1:/', flash: '0/)

        # until switch is pressed again
        while not switch():
            t = pyb.millis()                            # get time
            x, y, z = accel.filtered_xyz()              # get acceleration data
            log.write('{},{},{},{}\n'.format(t,x,y,z))  # write data to file

        # end after switch is pressed again
        log.close()                         # close file
        **blue.off()**                          # blue LED indicates file closed
        **pyb.delay(200)**                      # delay avoids detection of multiple presses
```

Now, as long as the switch wasn't pressed, the board doesn't have to do anything. To save power, there is the `pyb.wfi()` function. It makes the board wait for an interrupt (i.e. a button press). As long it is waiting, it is in power saving mode. We add that as first item in the outer while loop so our script finally looks like this:

```python
# datalogger.py
# Logs the data from the acceleromter to a file on the SD-card

import pyb

# creating objects
accel = pyb.Accel()
blue = pyb.LED(4)
switch = pyb.Switch()

# loop
while True:

    # wait for interrupt
    # this reduces power consumption while waiting for switch press
    pyb.wfi()

    # start if switch is pressed
    if switch():
        pyb.delay(200)                      # delay avoids detection of multiple presses
        blue.on()                           # blue LED indicates file open
        log = open('1:/log.csv', 'w')       # open file on SD (SD: '1:/', flash: '0/)

        # until switch is pressed again
        while not switch():
            t = pyb.millis()                            # get time
            x, y, z = accel.filtered_xyz()              # get acceleration data
            log.write('{},{},{},{}\n'.format(t,x,y,z))  # write data to file

        # end after switch is pressed again
        log.close()                         # close file
        blue.off()                          # blue LED indicates file closed
        pyb.delay(200)                      # delay avoids detection of multiple presses
```

So, now you have a datalogger, that can also act as cardreader. Connect a battery and throw the board up in the air. If you see (almost) zero acceleration during the time the board flew through the air, there was no error, you just discovered micro gravity during free fall.