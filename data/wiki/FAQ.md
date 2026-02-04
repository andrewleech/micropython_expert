## What are the differences between MicroPython and standard Python (CPython)?

Please see the [MicroPython differences from CPython](http://docs.micropython.org/en/latest/unix/genrst/index.html).  There is extra information in the [[Differences]] wiki page. 

## How big is MicroPython? How much memory does it take?

TL;DR: 128K ROM/8K RAM is the recommended minimum configuration for doing something "real". You can easily go below (or above) that, see below.

You can see sizes of various configurations (as well as how they change over time) at the [Code Dashboard](http://micropython.org/resources/code-dashboard/). Generally, we keep minimal configuration of MicroPython under 80K of ARM Thumb2 code (which includes compiler and interactive prompt, much less size can be achieved disabling those). That means a Cortex-M microcontroller with 128KB of flash can host a minimal version together with some hardware drivers. More full-fledged configurations take more space, for example "stmhal" (advanced microcontroller support) and "unix" (desktop-capable) ports are around 280KB.

Regarding RAM usage, MicroPython can *start up* with 2KB of heap. Adding stack and required static memory, a 4KB microcontroller could start a MicroPython, but hardly could go further than interpreting simple expressions. Thus, 8KB is minimal amount to run simple scripts. As Python is interpreted high-level language, the more memory you have, the more capable applications you can run. The reference MicroPython board, PyBoard, has 128KB of RAM.


## How fast is MicroPython?

We try to make MicroPython have about same, or better, average performance as CPython, while offering considerably smaller memory footprint (both code ("ROM") and heap ("RAM") sizes). Optimizing for size is known to be opposite of optimizing for speed, so in some cases MicroPython may be slower (an example is diversified access to large dictionaries). However, on some operations (like integer arithmetics), MicroPython can be around 10 times faster than CPython 3.3 (note that CPython itself is being optimized, so newer versions may be faster than older).

Additionally, on select architectures (which include the most popular ones like x86, x86_64, ARMv7), MicroPython offers an ahead-of-time compiler for large subset of Python language, which may increase performance 2 times on average. Beyond that, MicroPython offers "viper" native compiler for a smaller subset of Python language, which offers near-C speed for arithmetic/memory operations. As a final touch, MicroPython offers inline assembler support (currently only for ARMv7 (Thumb2)), for really performance-critical code.

Summing up, MicroPython offers wide selection of performance options and optimizations, allowing you to get the performance you need - all available even on a microcontroller!

* Some informal performance samples: **[[Performance]]**
* Continuous Integration performance testing: [Code Dashboard](http://micropython.org/resources/code-dashboard/) (look for "pystones" curve).

## How many platforms are supported by MicroPython?

All standard OS's are supported (Mac, Windows, Linux), as well as [[many embedded platforms|Boards Summary]] (the list is far from being exhaustive). MicroPython is written in ANSI C (with optional optimizations for selected platforms) and can be easily ported to new OS/hardware.

## What's the difference between `pyb` and `machine`?

Short answer: Use `machine`...unless there's a specific feature you require in `pyb` not present in `machine`.

The `pyb` module was developed first when there was only an STM32 port (for the PyBoard). As such, there were aspects of the API that were modeled after the STM32 HAL; it turns out that made it difficult to retain the same API when other ports were introduced.

The `machine` module was designed to be general enough to support all ports and, for the most part, supersedes `pyb`. Code written for `machine` is intended to work with little or no change across all ports.

`pyb` still exists a) for backwards compatibility and b) because there are some features that don't have equivalents in `machine` (mostly specific to STM32). There are also a couple of features for the STM32 port that haven't yet been migrated to machine (like PWM where it's still necessary to use `pyb`). 

