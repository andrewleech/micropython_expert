The [_thread](https://docs.micropython.org/en/latest/library/_thread.html) module provides the ability to create additional threads and is intended to implement the API defined by the [equivalent CPython module](https://docs.python.org/3/library/_thread.html). Threading is particularly desirable for microcontrollers with multiple cores in order to achieve greater performance. However, the feature is currently ''experimental'', poorly documented and differs between ports.

The higher-level [threading](https://docs.python.org/3/library/threading.html) module is not yet implemented but cant be built on top of the `_thread` primitives.

Note that an [asyncio](https://docs.micropython.org/en/latest/library/uasyncio.html) solution is often easier to implement, portable and more robust and should be preferred where concurrency (not necessarily parallelism) is required.

Threads are currently supported on ESP32, RP2040 (Pico), STM32, and Unix.

## Port-specific notes

### ESP32

The ESP32 port is built on the ESP IDF which uses FreeRTOS to manage threading. 

Threads are currently created on the same core as the MicroPython interpreter.

See [mpthreadport.c](https://github.com/micropython/micropython/blob/master/ports/esp32/mpthreadport.c#L139), specifically how `xTaskCreatePinnedToCore` is used rather than `xTaskCreate` which would allow FreeRTOS to choose the appropriate core to run on.

There are some complexities that prevent the second core to be used (additional information required!).

### RP2040 (Pico)

The RP2040 is a dual-core microcontroller. MicroPython supports running a single extra thread, which runs on the second core.

Note that this port does not use the GIL, otherwise the two cores would run in lock-step, providing no benefit from threading. This means that all program state must be carefully synchronised.

### STM32 (and Pyboard)

We provide additional firmware variants for the Pyboard that enables the `_thread` module. It allows multiple concurrent threads sharing the single core with pre-emptive context switching.

### Unix

### Resources

* [Threads in MicroPython](https://www.youtube.com/watch?v=aDXgX0rGVDY): Damien's talk that introduced the feature
* [Threading](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/THREADING.md): A doc which aims to explain the different forms of MicroPython concurrency.
