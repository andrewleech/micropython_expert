Micropython largely adopts the limitations of the platform it is running on for
any computations using floating point math. This can lead to surprising results
if it catches you unawares. Some platforms use double precision floating point
and thus operate the way normal Python does on larger platforms. Others may use
single precision floating point hardware or may entirely emulate floating point
arithmetic in software.

In any case, precision and speed can vary greatly from platform to platform.

As a quick test, you can determine whether your platform is using 32 or 64 bit
floating by evaluating `1.0 + 1e-8 - 1.0`. Running MicroPython on a Raspberry
Pico, for instance, you get this result
```
>>> 1.0 + 1e-8 - 1.0
0.0
```
On the other hand, on a version using 64-bit floating point numbers, you get this
```
>>> 1.0 + 1e-8 - 1.0
9.99999993922529e-09
```

## Impact of 32-bit Floating Point
For many applications, particularly those that run on a microcontroller, single-precision 
(32-bit) floating is entirely acceptable, at least partly because many microcontroller 
applications don't need floating point at all. Also, if you need to do reasonably fast
number crunching you may be able to do with [fixed point arithmetic](https://vanhunteradams.com//FixedPoint/FixedPoint.html) where you use normal
integer math, but interpret the numbers as if they were a constant factor larger than
the actual values.

It can also help to recast your algorithms to make better use of the available precision.
This [discussion hits](https://github.com/orgs/micropython/discussions/13075) on many of 
the key aspects about how to avoid problems, the key issue is to avoid subtracting 
large numbers that are nearly the same. Conversely, avoid adding small numbers to big
ones.

## Changing the representation
If you absolutely need 64-bit floating point numbers, it is possible to [recompile  micropython to use the 64-bit numbers](https://forums.raspberrypi.com/viewtopic.php?t=319525). 

