**Welcome to the MicroPython Wiki!**

![micropython-logo](https://avatars1.githubusercontent.com/u/6298560?s=140 '"micro" the project mascot')

This is the wiki for the [MicroPython](https://micropython.org/) project, which puts an implementation of Python 3.x on a microcontroller or embedded system.

This wiki complements the [official documentation](https://docs.micropython.org/) and aims to provide a place for community-edited documentation, tips, tricks, and guides. Anyone with a GitHub account can contribute.

This wiki replaces the former [Gollum Wiki](https://wiki.micropython.org/gollum/Home) on micropython.org and the content from there is being migrated over. In the meantime, you can access it [here](https://wiki.micropython.org/gollum/Home).

# MicroPython: a beginner's guide

The following hints result from problems that have frequently arisen in
[Discussions](https://github.com/micropython/micropython/discussions) and in the former Forum. The notes are intended for those new to
microcontroller programming.

# 1. Learn the basics of Python

It's worth getting familiar with the language before using it in a
microcontroller context. This is best done on a PC with an online course or an
introductory textbook. With a basic grasp of the language it's a good idea to
study its [use on microcontrollers](http://docs.micropython.org/en/latest/reference/constrained.html)
(official doc).

# 2. Choose your hardware with care

Perhaps you want to measure temperature and display it on a screen. Beginners
often rush out and buy hardware, then start trying to figure out how to use it.
The problem is that hardware devices usually need a device driver. This is a
program providing an application program interface (API) for the device. Writing
device drivers is not a beginner task; numerous drivers for MicroPython have
been written and published. You are advised to seek devices for which a driver
already exists.

Platforms to run MicroPython also have different characteristics. If you have
special requirements such a battery powered operation or high speed I/O, search
discussions and if necessary request help before spending money. Different 
platforms also [differ in how they support numerical computations](https://github.com/micropython/micropython/wiki/Floating-Point-Support).


# 3. Concurrency

Most firmware applications need to do several things at once. You might want to
detect a button press while taking regular temperature readings and updating a
display.

You've read the adverts which promise these powerful features:
 * Timers
 * Interrupts
 * Threading
 * Multi-core (on some boards)

All of these promise concurrency, but using them requires care and some reading.

These features are powerful but require some expertise to deploy effectively in
an application; they carry risks of introducing subtle bugs. They are rarely
the best way to achieve concurrency. In most cases the best approach is known
as cooperative multi-tasking and the Python implementation is a library called
`asyncio`.

Either way you probably have some reading to do. Learn `asyncio` or learn how
to write reliable code using the magic features.
 * [Asyncio official docs](http://docs.micropython.org/en/latest/library/asyncio.html).
 * [Asyncio unofficial tutorial](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md).
 * [Interrupts official guide](http://docs.micropython.org/en/latest/reference/isr_rules.html) - also applies to timer callbacks.

Writing code for threading and multi-core is particularly challenging. There is no
official guide. [This unofficial doc](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/THREADING.md)
provides some guidance but does assume some MicroPython knowledge.

# 4. Requesting help

Please post a request in [Discussions](https://github.com/micropython/micropython/discussions). Choose a topic appropriate to your query
and write a title which summarises your problem. Please indicate when the issue
has been resolved. Also avoid spamming multiple root messages about the same
issue as it makes it hard to provide a coherent response or for helpers to know
if the issue is resolved. Your request will be seen, and if someone has an idea
how to fix it they will respond.

# 5. Bug reports

Please raise issues against MicroPython only if you are convinced that you have
found a bug in MicroPython. Examples of bugs are when the same code sample
produces a different outcome in MicroPython compared to CPython. Study the
[list of differences](https://github.com/micropython/micropython/wiki/Differences)
between MicroPython and CPython to be sure this isn't a known isse.

If you're unsure whether something is a bug please ask in discussions before
raising an issue: the maintainers are busy and you will probably get a quicker
response.

To report a bug provide a minimal code sample that reproduces the bug with
details of how it should be run - hardware, firmware build, any necessary
wiring. Choose the issue title with care, identfying the hardware platform at
the start of the line. For example (fictitious bug)  
```
rp2: RTC runs backwards on 32nd of month.
```
This will ensure that the report is seen by the appropriate maintainer.
