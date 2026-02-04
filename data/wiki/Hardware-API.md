This is the current proposal for a new hardware API.  It is a work in progress.
Discussion: https://github.com/micropython/micropython/issues/1430

# Design goals and priciples

The main aim is to provide Python modules/functions/classes that **abstract the hardware in a Pythonic way**.

The API should be Pythonic, obvious and relatively minimal.  There should be a close mapping from functions to hardware and there should be as little magic as possible.  The API should be as consistent across peripherals (Pin, UART, I2C, ADC, etc) as possible.  There should usually be only one way to do something.  A method name should do exactly what it says and no more (i.e. it shouldn't be heavily overloaded).

The existing `pyb` module already provides such abstraction but it is not as clean or consistent or general as it could be.  The new hardware API will co-exist alongside the `pyb` module (only for stmhal port, e.g. PyBoard) so that existing scripts still run.  The pyb module will eventually be deprecated, but only after all functionality finds another home (which may be some time).

# Terminology

* Port - when used in this document, refers to some kind of hardware port.
* Software - MicroPython as a project, and particular implementation ported to a particular CPU/MCU/SoC. A separate word used to disambiguate word "port" (which otherwise may refer to a hardware or software port)
* MUST, SHOULD, MAY - Have meanings based on https://www.ietf.org/rfc/rfc2119.txt
* CAN - Gives an example how feature with undefined behavior may act on a particular software implementation. Essentially, it's a note for implementers, from API side, the behavior stays undefined.

# Use cases

Create a UART with various pin configurations:
```python
uart = UART(0) # reference (existing) UART(0) entity, without (re-)initialising it
uart = UART(0, 9600) # create and initialise UART(0) using default pins, no flow control
uart = UART(1, 9600, 8, pins=('GP1', 'GP2')) # specified pins, no hardware flow control
uart = UART(1, 9600, 8, pins=('GP1', 'GP2', 'GP7', 'GP6')) # RTS/CTS flow control
uart = UART(1, 9600, 8, pins=('GP1', None)) # Tx only
uart = UART(1, 9600, 8, pins=(None, 'GP2')) # Rx only
uart = UART(1, 9600, 8, pins=('GP1')) # raise 
uart = UART(1, 9600, 8, pins=('GP1', 'GP2', 'GP7')) # raise
uart = UART(1, 9600, 8, pins=('GP1', 'GP2', 'GP7', None)) # OK, RTS only
```

Create a UART and enable pull-up on the pins:
```python
# create and initialize UART1 with TX and RX on GP1 and GP2 respectively.
UART(1, 9600, pins=('GP1', 'GP2')) 
# enable the pull-ups on both UART1 pins
Pin('GP1', mode=Pin.ALT, pull=Pin.PULL_UP)
Pin('GP2', mode=Pin.ALT, pull=Pin.PULL_UP)
```

These use-cases need to be written:

- Basic I/O on a pin
- PWM on a pin
- ADC on a pin
- Using a Timer to do a one-shot callback
- Using a Timer to do a repeated callback

# General conventions of the API

You make objects corresponding to physical entities in the MCU (eg Pin, UART, Timer).  Some entities like UART can be connected to Pin's.

Conventions are:

- Selection of a peripheral/entity is done by an id. Whenever possible, a port should allow an ID to be an integer, but in various cases this will not be possible. Besides this recommendation, a format of an id is arbitrary (common cases: integer, strings, tuple of string/integers). There can be "virtual" peripherals, e.g. bitbanging I2C port, software timer, etc. These are recommended to have negative ids, with -1 being a default choice. If there're multiple types of the same virtual peripheral (e.g. OS software timers with different properties), further negative values can be given, and symbolic constants are recommended to be provided for them. (But another implementation strategy for this case is to define separate classes for such cases, instead of overloading default Timer class - e.g. OSSlowTimer, OSFastTimer. This is informal comment.)

- All periphs provide a constructor, `.init()` and `.deinit()` methods. The `Pin` and the `IRQ` classes are the exception here, `Pin` doesn't provide `.deinit()` because a single pin cannot be completely de-initalized, and also because of the dynamic nature of pins which can be used as GPIO and also by other peripherals.

- Peripherals should provide default values for all the initialization arguments, this way when calling `.init()` with no params, or the constructor with only the peripheral id (or no id at all, then the default one is used), it will be initialized with the default configuration.

- If a peripheral is in the non-initialized state, any operation on it except for `.init()` SHOULD raise `OSError` with `EBUSY` code.

- When connecting a periph to some pins, ~~one uses the `pins=` keyword in the constructor/init function.  This is a tuple/list of pins, where each pin can be an integer, string or `Pin` instance.~~ keyword arguments with names of the pins should be used, e.g. `tx=`, `miso=`, etc.

In the method specs below, *NOHEAP* means the function cannot allocate on the heap.  For some ports this may be difficult if the function needs to return an integer value that does not fit in a small integer.  Don't know what to do about this.

## OSError exceptions regarding peripherals

- In case that the peripheral is not available (invalid id) ??
- Operations on non-initialized peripherals ??

# New machine module

The classes to control the peripherals of the board will reside in a new module called `machine`, therefore, by doing:

```python
import machine
dir(machine)
```

one can easily see what's supported on the board.

## Physical memory access

Provided by `mem8` (NOHEAP), `mem16` (NOHEAP), `mem32` (HEAP) virtual arrays. Mind that only `mem8` and `mem16` guarantee no heap access. For systems with virtual memory, these functions access hardware-defined physical address space (which includes memory-mapped I/O devices, etc.), not virtual memory map of a current process. 

## IRQs

An interrupt request (IRQ) is an asynchronous and pre-emptive action triggered by a peripheral.  Peripherals that support interrupts provide the `irq` method which returns an irq object.  This can be used to execute a function when an IRQ is triggered, or wake up the device, or both.

```python
peripheral.irq(*, trigger, priority=1, handler=None, wake=None)
```

- All arguments are keyworkd only, to be able to adapt to the different nature of each peripheral.
- `trigger` is what causes the interrupt, for instance a `Pin` object accepts `Pin.IRQ_RISING`, `Pin.IRQ_FALLING`, etc. Trigger sources can also be ORed together, like `Pin.IRQ_RISING | Pin.IRQ_FALLING`.
- `priority` it's just a number from 1 to N (should each port define it's own N?). The higher the number, the more priority it gets.
- `handler` is the function that gets called when the interrupt is fired.
- `wake` specifies if the irq can wake the device from any of the sleep modes, e.g. `machine.SLEEP` or `machine.DEEPSLEEP`, and they can also be ORed together.

The `irq` is always enabled when created. Calling the irq method with no arguments simply returns the existing object (or creates it for the first time) without re-configuring it, just as with any other constructor.

The created `irq` object supports the following methods:

- `irq.init()` re-init. The interrupt will be automatically enabled.
- `irq.enable()` enable the interrupt.
- `irq.disable()` disable the interrupt.
- `irq()` manually call the irq handler.
- `irq.flags()` get the triggers that caused the current irq. Only returns useful values when called inside the irq handler. The flags are cleared automatically when leaving the handler, therefore, this method always returns 0 when called outside.

Signature of an irq handler: `def my_handler(peripheral)`

Example:

```python
def pin_handler(pin):
    print('Interrupt from pin {}'.format(pin.id()))
    flags = pin.irq().flags()
    if flags & Pin.IRQ_RISING:
        # handle rising edge
    else:
        # handle falling edge
    # disable the interrupt
    pin.irq().deinit()
```
 
## The Pin class

### Constructor

Creates and initilizes a pin.

`pin = Pin(id, mode, pull=None, *, value, drive, slew, alt, ...)`
- `id`: mandatory and positional. `id` can be an arbitrary object (among possible value types are: int (an internal Pin ID), str (a Pin name), tuple (pair of [port, pin]))
- `mode`: is mandatory and positional (can be kw). Specifies pin mode:
  - `Pin.IN` - Pin configured for input; there's additional requirement that, if viewed as output, pin was in high-impedance state. This requirement is almost universally satisfied by any MCU.
  - `Pin.OUT` - Pin configured for (normal) output.
  - `Pin.OPEN_DRAIN` RECOMMENDED - Pin configured for open-drain output, with special requirements for input handling. Open-drain output works in following way: if output value is set to 0, pin is low level; if output value is 1, pin is in high impedance state. Some MCUs don't support open-drain outputs directly, but it's almost always possible to emulate it (by outputting low level, in case of 0 value, or setting pin as input in case of 1 value). It is recommended that software implemented such emulation (see below for additional requirements for input handling).
  - `Pin.ALT` OPTIONAL - Pin is configured to perform alternative function, which is MCU-specific. For pin configured in such way, any other Pin methods (except .init()) are not applicable (calling them will lead to undefined, or hardware-specific, result)
  - `Pin.ALT_OPEN_DRAIN` OPTIONAL - Same as `Pin.ALT`, but pin is set as open-drain.
- `pull` is optional and positional (also can be named). May take `Pin.PULL_UP`, `Pin.PULL_DOWN` or `None`
- The rest of args are kwonly.
- `value` is required for a software to implement; it is valid only for `Pin.OUT` and `Pin.OPEN_DRAIN` modes and specifies initial output pin value if given.
- The rest are optional for software to implement, and a software can define them and also define others.
- `alt` specifies an alternate function, it is optional and the values it takes vary per MCU. It exists to allow advanced pin operations for software that support it. This argument is valid only for `Pin.ALT` and `Pin.ALT_OPEN_DRAIN` modes. It may be used when a pin supports more than one alternate function. If only one pin alternate function is support for particular MCU, it is not required.

### Pins with alternate function(s)

As specified above, Pin class allows to set alternate function for particular pin, but does not specify any further operations on such pin (such pins are usually not used as GPIO, but driven by other hardware blocks in MCU). The only operation supported on such pin is re-initializing, by calling constructor or .init() method. If a pin with alternate function set is re-initialized with `Pin.IN`, `Pin.OUT`, or `Pin.OPEN_DRAIN`, the alternate function will be removed from such pin (it will be used as GPIO).

### Methods

TOD: Do we really need 2+ ways to set the value?

- `pin.init(...)` - (Re)initinialize a pin, accepts the same parameters as constructor, except `id`.
- `pin.value()` NOHEAP - Get pin value (returns 1 or 0). Behavior depends on the mode of a pin:
  - `Pin.IN` - Returns the actual input value currently present on a pin.
  - `Pin.OUT` - Undefined. MAY return value stored in the output buffer of a pin.
  - `Pin.OPEN_DRAIN` - If pin is in "0" state, undefined. MAY return value stored in the output buffer of a pin (i.e. 0). Or MAY return actual input value on a pin. Otherwise, if pin is in "1", MUST return actual input value on a pin. (Note that if open-drain pin is in 0 state, entire bus to which pin is connected, expected to be in 0 state, so there's little point to read actual input value; the only reason for another value in this case would be voltage conflict on a bus, which is usually a hardware malfunction and in some cases may lead to physical damage of a pin).
- `pin.value(x)` NOHEAP - Set output value of a pin (value can be any valid expression, which is cast to True/False valur for 1/0 output value respectively). Exact behavior depends on the pin mode:
  - `Pin.IN` - Value is stored in the output buffer for a pin. Pin state doesn't change (it keeps being in high-impedance state, as required for IN mode). The stored value will become active on a pin as soon as it is changed to OUT or OPEN_DRAIN mode.
  - `Pin.OUT` - Pin is set to the `x` value immediately.
  - `Pin.OPEN_DRAIN` - If value is "0", ping is set to low state. Otherwise, it is set to high-impedance state.
- `pin.out_value()` NOHEAP, optional - Return value stored in the output buffer of a pin, regardless of its mode.
- `pin()` NOHEAP - Fast method to get the value of the pin. Fully equivalent to `Pin.value()`.
- `pin(x)` NOHEAP - Fast method to set the value of the pin. Fully equivalent to `Pin.value(x)`.
- `pin.toggle()` NOHEAP, optional - Toggle output value of a pin.

**Getters and setters**
- `pin.id()` NOHEAP; get only. - Return ID of a pin. This MAY return `id` as specified in the constructor. Or it MAY return "normalized" software-specific pin ID.
- `pin.mode([mode])` NOHEAP
- `pin.pull([pull])` NOHEAP
- `pin.drive([drive])` NOHEAP
- `pin.slew([slew])` NOHEAP

### Constants
- **for mode:** `Pin.IN`, `Pin.OUT`, `Pin.OPEN_DRAIN`, `Pin.ALT`, `Pin.ALT_OPEN_DRAIN`
- **for pull:** `Pin.PULL_UP`, `Pin.PULL_DOWN`, (no pull is `None`). _optional:_ `Pin.PULL_UP_STRONG`, `Pin.PULL_DOWN_WEAK`, ...
- **for drive:** `Pin.LOW_POWER`, `Pin.MED_POWER`, `Pin.HIGH_POWER`
- **for slew:** `Pin.FAST_RISE`, `Pin.SLOW_RISE`
- **IRQ triggers:** `pin.IRQ_RISING`, `pin.IRQ_FALLING`, `pin.IRQ_HIGH_LEVEL`, `pin.IRQ_LOW_LEVEL`

## The UART class

`uart = UART(id, baudrate=9600, bits=8, parity=None, stop=1, *, pins, ...)`

- `pins` is a 4 or 2 item list indicating the TX, RX, RTS and CTS pins (in that order). Any of the pins can be `None` if one wants the UART to operate with limited functionality. If the `RTS` pin is given the the `RX` pin must be given as well. The same applies to `CTS`. When no pins are given, then the default set of `TX` and `RX` pins is taken, and hardware flow control will be disabled. If `pins=None`, no pin assignment will be made.


Methods:

- `uart.init(...)`
- `uart.any()` return the number of characters available for reading.
- `uart.read([nbytes])`
- `uart.readinto(buf[, nbytes])` NOHEAP
- `uart.readall()`
- `uart.readline([max_size])`
- `uart.write(buf)` NOHEAP
- `uart.sendbreak()` NOHEAP

## The I2C class - I2C Master end-point

Changes from pyb: re-cast for master-only support (slave moved to I2CSlave class), so "mode" arg removed, changed method names.

`i2c = I2C(id, *, baudrate, addr, pins)`

`pins` is a tuple/list of SDA,SCL pins in that order (TODO: or should it be SCL, SDA to be consistent with the clock first for SPI?).

This class implements only master mode operations:

- `i2c.scan()` search for devices present on the bus.

Master mode transfers:

- `i2c.readfrom(addr, nbytes, *, stop=True)`
- `i2c.readfrom_into(addr, buf, *, stop=True)` NOHEAP; stop is if we want to send a stop bit at the end
- `i2c.writeto(addr, buf, *, stop=True)` NOHEAP; stop is if we want to send a stop bit at the end

Master mode mem transfers:

- `i2c.readfrom_mem(addr, memaddr, nbytes, *, addrsize=8)`
- `i2c.readfrom_mem_into(addr, memaddr, buf, *, addrsize=8)` NOHEAP
- `i2c.writeto_mem(addr, memaddr, buf, *, addrsize=8)` NOHEAP

For master transfers we don't use read/write names because the type signature here is different to standard read/write (here we need to specify the address of the target slave).  Other option would be to provide `i2c.set_addr(addr)` to set the slave address and then we can simply use standard read/readinto/write methods.  But that introduces state into the I2C master (being the slave address) and really turns it into an endpoint, which is a higher level concept than simply providing basic methods to read/write on the I2C bus.  An endpoint wrapper can very easily be written in Python.

## The I2CSlave class - I2C Slave end-point

`i2csl = I2CSlave(id, *, baudrate, addr, pins)`

See I2C class for arguments (id's refer to the same underlying hardware blocks as master I2C class).

Slave mode:

TODO: Details TBD. The general idea is that slave end-point can be configured in such a way that it can be accessed by master I2C.readfrom_mem(), etc. methods. Actual ability to do that depends largely on underlying hardware, and would require low-latency interrupts and DMA support.

- `i2c.read(nbytes)`
- `i2c.readinto(buf)` NOHEAP
- `i2c.write(buf)` NOHEAP

## The SPI class - SPI master end-point
Changes from pyb: re-cast for master-only support (slave moved to SPISlave class), so "mode" arg removed, changed method names.

`spi = SPI(id, *, baudrate, polarity=1, phase=0, bits=8, firstbit=SPI.MSB, pins)`

`pins` is a tuple/list of SCK,MOSI,MISO pins in that order.  Optionally the list can also have NSS at the end.

Methods:

- `spi.write(buf)` NOHEAP
- `spi.read(nbytes, *, write=0x00)` write is the byte to output on MOSI for each byte read in
- `spi.readinto(buf, *, write=0x00)` NOHEAP
- `spi.write_readinto(write_buf, read_buf)` NOHEAP; write_buf and read_buf can be the same

## The SPISlave class - SPI slave end-point

TODO: Details TBD. As SPI usually offer (much) higher transfer speeds, implementing slave support would require even more performant resources that I2C slave. One of the usecases may be high-speed communication between 2 or more systems, akin to "remote DMA" (i.e. slave will be initialized with a single bytearary buffer, which master can read at any time).

## The I2S class

**Note that I2S has not yet officially supported by any existing
  MicroPython port; support for stmhal (pyboard) is currently under
  development by @blmorris.
  The proposed API for I2S is based on the new model for SPI, with
  certain modifications based on the I2S development discussions on
  GitHub, and will provide guidance as the I2S code is prepared for
  merging. **
  

`i2s = I2S(id, mode, dataformat=I2S_DATAFORMAT_16B_EXTENDED,
standard=I2S_STANDARD_PHILIPS, polarity=0,
audiofreq=I2S_AUDIOFREQ_48K, clksrc=I2S_CLOCK_PLL, mclkout=0,
pins)`

`pins` is a tuple/list of BCK,WS,TX,RX pins in that order.  BCK, WS,
and at least one of either TX or RX are required. If Both TX and RX
are provided, the I2S port is initialized in duplex mode, otherwise it
initilizes as simplex in the direction specified by the provided pin.

### Methods

All write and read methods for I2S will utilize DMA and be
non-blocking when IRQ's are enabled.

Buffer oriented:

- `i2s.write(buf)` NOHEAP
- `i2s.read(buf)` ??
- `i2s.write_readinto(write_buf, read_buf)`
- `i2s.write_callback(func)`
- `i2s.read_callback(func)`

Stream oriented:

- `i2s.stream_out(stream)`
- `i2s.stream_in(stream)`
- `i2s.pause()`
- `i2s.resume()`
- `i2s.stop()`

### Constants
- **for mode:** `I2S.MASTER`, `I2S.SLAVE`
- **for standard:** `I2S.PHILIPS`, `I2S.MSB`, `I2S.LSB`,
`I2S.PCM_SHORT`, `I2S.PCM_LONG`
- **for clksrc:** `I2S.PLL`, `I2S.EXTERNAL`
- **for dataformat:** default is 0 for 16bit extended; otherwise valid
values are 16, 24, or 32 for these respective sample widths
- **for audiofreq:** default is 48000 for 48kHz sample rate; otherwise
44100, 88200, and 96000 are valid (TODO: provide a complete list of
valid sample rates...)
- **for mclkout:** Enable Master Clock output; 0 or 1, True or False

## The ADC class

Need to decide on standard for return value (eg always 12-bits maximum value?). See discussion in https://github.com/micropython/micropython/pull/1130 for suggestion to always use 14- or 30-bit value (maximum MicroPython unsigned value which fits into 16- or 32-bit machine word).

Constructor:

`adc = ADC(id, *, bits, ...)`

Methods:

- `adc.init(...)` re-init
- `apin = adc.channel(id, *, pin=...)` make an analog pin from a channel and optionally specify a pin. If only the pin is given, the right channel for that pin will be selected.
- `apin.value()` NOHEAP? depends what the return value is, probably should be integer.
- `apin()` fast method to read the value of the pin.
- `apin.readtimed(buf, timer)`


## The RTC (Real Time Clock) class

Constructor:

`rtc = RTC(id=0, datetime=(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None))` create an RTC object instance and set the current time.

Methods:

- `rtc.init()` re-init
- `rtc.now()` returns a `datetime` tuple with the current time and date.
- `rtc.alarm(alarm_id, time=time_ms or datetime_tuple, *, repeat=False)` sets the RTC alarm. If the alarm has already expired the returned value will be 0. An alarm can be set both via passing an integer with the number of milliseconds or a `datetime` tuple with a future time. If the `datetime` tuple contains a past time, the alarm will expire immediately triggering any enabled IRQ. The same applies when passing a 0 or negative `time_ms` value.
- `rtc.alarm_left(alarm_id)` get the number of milliseconds left before the alarm expires. Returns 0 if the alarm is already expired.
- `rtc.alarm_cancel(alarm_id)` cancel a running alarm.
- `rtc.calibration([cal_value])` get or set the RTC calibration value. Platform dependent.
- `rtc.irq(*, trigger, handler, priority, wake)` calls the handler function once the alarm expires. See the IRQ section for details.

Constants:

- `RTC.ALARM0`

## The WDT class

Constructor:

`wdt = WDT(id, [timeout])` instantiate and optionally enable the WDT with the specified timeout.

Methods:

- `wdt.init(...)` re-init (on some platforms re-initializing the WDT might not be allowed, for security reasons).
- `wdt.feed()` feed the watchdog.
- `wdt.deinit()` disable the WDT (again, might not be possible on some platforms, raise `OSError` in that case).

**Note:**
_danicampora_: Just as WLAN below, I think it should be possible to retrieve the existing WDT instance when calling the constructor with no params besides the id.

## The Timer class

The `Timer` class provide access to the hardware timers of the SoC. It allows to generate periodic events, count events, and create PWM signals.

Constructor:

`timer = Timer(id, mode=Timer.PERIODIC, *, freq, period_ns, counter_config=(prescaler, period_counts))`

* mode: mandatory values: Timer.PERIODIC, Timer.ONE_SHOT, other: hardware-specific, subject to further standardization.

Since timers are used for various applications, many of which require high accuracy, having 3 ways of setting the timer frequency (freq itself, period in us or ns, and period in timer counts together with the prescaler) it's important. Having period in time units also helps readability and ease of use.

**Suggestion:** On some devices, all channels of a timer must have the same frequency, but the mode can be changed. On some other devices is the other way around. Proposal: The basic API ties both things to the Timer object, but we could also accept the following:

`timer = Timer(id, mode=(Timer.PERIODIC, Timer.PWM) *, ....)`

Which setups the timer and configures channel 0 in periodic mode and channel 1 in PWM mode. The same could be done for the frequency:

`timer = Timer(id, mode=Timer.PERIODIC *, frequency=(1000, 100))`

And of course, both mode and frequency could accept a tuple. The availability of this would be hardware dependent and needs to be documented properly. Requirement is that all ports support at least the first method that fixes all channels to have the same mode and frequency. 

Timer methods:

- `timer.init()` re-init.
- `timer.deinit()` disables the Timer and all it's channels.
- `timer.counter()` gets or sets the value of the timer counter.
- `timer.time()` gets or sets the current timer time (in ns or us, TBD). Only makes sense in PERIODIC or ONESHOT.
- `timer.period()` gets or sets the timer period in ns or us.
- `timer.counter_config()` gets or sets the `(prescaler, period_counts)` tuple.
- `timer.frequency()` gets or sets the timer frequency/frequencies.
- `timer.channel(id)` returns a TimerChannel object.

TimerChannel methods:

- `timerchannel.irq()` create a irq object associated with the channel.
- `timerchannel.pulse_width()` in PWM mode, change the pulse width in timer count units.
- `timerchannel.pulse_width_percent()` change the pulse width in percentage (0-100). Accepts floating point numbers if the port supports it.
- `timerchannel.capture()`
- `timerchannel.compare()`

## The WLAN class

The WLAN class belongs to the network module.

Constructor:

`wlan = WLAN(id, mode=WLAN.STA, *, ssid='wlan', auth=None, channel=1, iface=None)`

**Note:**
Since WLAN might be a system feature of the platform (this is the case of the WiPy and the ESP8266), 
calling the constructor without params (besides the id) will return the existing WLAN object.

Methods:

- `wlan.init()` re-init.
- `wlan.deinit()` disable the NIC. NOHEAP.
- `wlan.mode([mode])` set or get the mode. NOHEAP
- `wlan.ssid([ssid])` set or get our own SSID name
- `wlan.auth([(sec, key)])` set or get the authentication tuple.
- `wlan.channel([channel])` set or get the channel. NOHEAP
- `wlan.scan()` perform a network scan and return a named tuple of the form:
  `(ssid, bssid, sec, channel, rssi)`
- `wlan.mac([mac])` get or set the MAC address. The MAC address is a `bytes` object of length 6.
- `wlan.connect(ssid, auth=None, *, bssid, timeout=None)` Connect to the network specified by the SSID using the given authentication. Optionally specify the BSSID and a timeout.
- `wlan.disconnect()` Closes the current connection. NOHEAP
- `wlan.isconnected()` returns `True` if connected and IP address has been assigned. NOHEAP
- `wlan.ifconfig(id=0, config=[(ip, netmask, gateway, dns) or 'dhcp'])` get or set the IP configuration. The `id` is the interface id, and defaults to zero. In the case of `AP+STA` mode, the NIC effectively has 2 interfaces that can be configured independently using `id=0` for the STA and `id=1` for the AP. Alternatively, a port can choose to use string names for the `id`, e.g. `id='STA'` and `id='AP'`.

Constants:

- `WLAN.STA` Station mode
- `WLAN.AP` Access point mode
- `WLAN.STA_AP` Station mode + Access point mode. (prefer to use separate `WLAN.STA` & `WLAN.AP`)
- `WLAN.P2P` Peer to peer (also called WiFi-direct or Ad-Hoc mode)
- `WLAN.WEP` WEP security
- `WLAN.WPA` WPA security
- `WLAN.WPA2` WPA2 security
- `WLAN.WPA_ENT` WPA Enterprise security

# machine module functions

- `machine.reset()` perform a hard reset (same as pressing the reset switch on the board)
- `machine.enable_irq()` enable the interrupts
- `machine.disable_irq()` disable the interrupts
- `machine.freq([freq, ...])` NOHEAP; get or set CPU and/or bus frequencies
- `machine.idle([... options])` NOHEAP; idle the CPU, may require external event to leave idle mode
- `machine.sleep([... options])` NOHEAP; enter sleep mode that retains RAM and continues execution when woken
- `machine.deepsleep([... options])` NOHEAP; enter sleep mode that may not retain RAM and may reset when woken
- `machine.reset_cause()` get the reset cause
- `machine.wake_reason()` get the wake reason (from `SLEEP` or `DEEPSLEEP` modes). `None` will be returned if no sleep-wake cycle has occurred

### Constants

To specify from which sleep mode a callback can wake the machine:
- `machine.IDLE`
- `machine.SLEEP`
- `machine.DEEPSLEEP`

Reset causes:
- `machine.PWR_ON_RESET`
- `machine.HARD_RESET`
- `machine.SOFT_RESET`
- `machine.WDT_RESET`
- `machine.DEEPSLEEP_RESET`

Wake reason:
- `machine.NETWORK_WAKE`
- `machine.PIN_WAKE`
- `machine.RTC_WAKE`

# time module additions

The time module has uPy specific functions:
- `time.sleep_ms(ms)` NOHEAP - Delay for given number of milliseconds, should be positive or 0
- `time.sleep_us(us)` NOHEAP - Delay for given number of microseconds, should be positive or 0
- `time.ticks_ms()` NOHEAP  - Return increasing millisecond counter with arbitrary reference point, and wrapping after some (unspecified) value. The value should be treated as opaque, suitable for use only with ticks_diff().
- `time.ticks_us()` NOHEAP - As above, but microsecond counter.
- `time.ticks_cpu()` NOHEAP - As above, but highest resolution available (usually CPU clocks).
- `time.ticks_diff(old, new)` NOHEAP - Measure period between consecutive calls to ticks_ms(), ticks_us(), or ticks_cpu(). Value returned by these functions may wrap around at any time, so directly subtracting them is not supported. ticks_diff() should be used instead. "old" value should actually precede "new" value in time, or result is undefined. This function should not be used to measure arbitrarily long periods of time (because ticks_*() functions wrap around and usually would have short period). The expected usage pattern is implementing event polling with timeout:
```
# Wait for GPIO pin to be asserted, but at most 500us
start = time.ticks_us()
while pin.value() == 0:
    if time.ticks_diff(start, time.ticks_us()) > 500:
        raise TimeoutError
```
- `time.source(rtc_or_timer_obj)` attach a RTC to use as the time reference for `time.time()` and `time.localtime()`.

# os module additions

The os module has uPy specific functions:
- `os.mount(block_dev, mount_point, *, readonly)`
- `os.umount(mount_point)`
- `os.mkfs(device or path, *, options...)`
- `os.dupterm([stream_obj])` get or set duplication of controlling terminal, so that REPL can be redirected to UART or other (note: could allow to duplicate to multiple stream objs but that's arguably overkill and could anyway be done in Python by making a stream multiplexer)

# micropython module

- `micropython.main(path)` set the location of the main script.