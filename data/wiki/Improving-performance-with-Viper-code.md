The Viper code emitter uses special Viper native data types to get faster performance. The largest advantage is for integer arithmetic, bit manipulations and integer array operations. 


Read the official documentation here: https://docs.micropython.org/en/latest/reference/speed_python.html

# An example
```py
# Original Python function
def add_to_array( a, n ):
    sum_array = 0
    for i in range(len(a)):
        a[i] += n
        sum_array += a[i]
    return sum_array

# This decorator allows taking advantage of the Viper data types:
@micropython.viper
# The function declaration uses type hints (type annotations
# to cast parameters 
# and return value to/from viper data types.
# pa is a pointer to memory (very fast)
# Since pa does not carry information about the array length,
# a third argument with the length is needed
def viper_add_to_array( pa:ptr32, n:int, length:int)->int:
    sum_array = 0
    i = 0
    while i < length: # while is a bit faster than for...range
        # Same instructions now use fast integer arithmetic
        pa[i] += n  # Pointers are used like arrays
        sum_array += pa[i]
        i += 1
    return sum_array
my_array = array.array("l", (i for i in range(10000)))
add_to_array( my_array, 10 )
viper_add_to_array( my_array, 10, len(my_array) )

```
This Viper function is about 16 times faster on a ESP32-S3 with PSRAM wih an array of 10000. 

In this example, the original add_to_array() function with @micropython.native decorator is about 1.6 times faster than the original function.

Some have reported much higher performance gains! 

# The Viper decorator

The @micropython.viper decorator is applied to functions, including nested functions and methods. It also can be applied to an entire class and to interrupt service routines (ISR).

Viper code is compiled and runs very fast, especially when using the Viper data types. However line by line error reporting and interrupt from the console via control-C do not work while in Viper code (no problem, just reset the microcontroller when stuck in a loop).

The @micropython.viper directive is a compile-time directive and activates the Viper code emitter. The Viper emits machine code and additonally does static (compile-time) analysis of the code to determine integer variables and emits special (very fast) machine code to handle integer operations. It also activates the very fast pointer data types.

All things nice that MicroPython does, will continue to work. What is affected is mostly how integer variables and access to arrays work. 

The Viper extensions are Python language extensions and not fully compliant with Python, so differences are to be expected.

# @micropython.viper vs. @micropython.native decorator

The @micropython.native decorator is another means to speed up code, but does not require special data types or constructs. It covers most of the MicroPython language functionality without change, except a very few restrictions. 

When not using the Viper data types, performance of Viper and native is similar. In fact, the Viper code emitter is an extension of the native code emitter. However since most code has at least some integer variables, Viper code may be faster than native code, sometimes even without change.

Advantages of the @micropython.native decorator: no change to the code is needed.

Advantage of the @micropython.viper decorator: the result can be faster, especially if integer and array operations are involved. But it is necessary to change the code.


# The Viper data types: int, uint, bool, ptr32, ptr16 and ptr8

These data types are very fast. They are not implemented as an MicroPython object but as a raw variable. They can be only used within a Viper decorated function.

Most of the difficulties using the Viper code emitter are related to the use of these data types and their peculiarities. So here goes a lot of detail about these data types.

Viper variables are "raw" variables and are not stored as MicroPython objects. In contrast the string, tuple, list and integer variables we all know are always stored as MicroPython objects. 

The Viper code emitter detects Viper variables at compile time, and generates very fast code for the operations. For example
```x = 0``` or ```x = int(myfunction())``` will make `x` Viper `int` variable. Now, `x = x + 1` will be compiled around 2 or 3 machine code instructions!

Compile time means: when the .py file is analyzed by the MicroPython interpreter, or when mpy-cross is run.

Please note that once assigned, the type of a Viper variable cannot be changed (unlike regular Python), which is quite reasonable since there is no underlying object:

```py
    x = 1
    x = "hello" # This changes the Viper int variable x to a string object, not allowed
    # The previous line raises a compile time error:
    # ViperTypeError: local 'x' has type 'int' but source is 'object'
    # The reverse order is also not allowed.
```

Be aware: The Viper code emitter analyzes of the code at compile time, determining the type of the variables. This is very unusual when coming from a Python background, where typing is dynamic and at runtime. On the other hand, most problems with Viper variables are detected at compile time, before the program even runs, which is very nice!


In case you are familiar with C: The Viper data types are similar to some C language data types:

|Viper data type | similar C data  type | size |
|----------------|----------------------|------|
|`int`   |`long int` | 32 bit signed integer|
|`uint`  | `unsigned long int`| 32 bit unsigned integer |
|`bool` | `long int`| 32 bit signed integer, where 0 is False and not zero is True. This is unlike C bool where 0 is false and 1 is true |
|`ptr32` | `*long int` |  memory pointer to a 32 bit signed integer |
|`ptr16` |`*unsigned short int` |memory pointer to a 16 bit unsigned integer |
|`ptr8`  | `*unsigned char`|memory pointer to an 8 bit unsigned integer |

## What to remember about Viper data types

* The Viper data types only exist in a viper function
* The Viper data types are detected at compile time (statically, before the program starts to run)
* They are not MicroPython objects but raw variables
* The associated functions `int()`, `uint()`, `bool()` `ptr8()`, `ptr16()` and `ptr32()` are type casts (similar to C language)
* The MicroPython `int` object we all know is different from the Viper `int` inside a Viper function. If needed, the MicroPython `int` can still be accessed as `builtins.int` (`import builtins` first). Same with `bool`. 
* Operations are very fast

## The Viper int data type

The Viper ```int```data type in Viper code is a special data type for fast signed integer operations. A Viper `int` can hold values from -2\*\*31 to 2\*\*31-1, i.e. this is a 32 bit signed integer.

A Viper `int` is different to the ```int``` we know in MicroPython, which is still available in Viper decorated functions as  ```builtins.int```.  Hence this document will make a difference between a "Viper ```int```" opposed to a ```builtins.int```.

It is advisable to be aware at all times that `Viper int` and `builtins.int` are different data types.

### Viper integer constants
Viper integer constants are in the range -2\*\*29 to 2\*\*29-1. When you assign a viper constant to a variable, it automatically is a Viper `int`.

Be aware: integer constants don't have the full range of values a Viper int value can hold, they are signed 30 bit integers. 

Integer expressions are evaluated compile time and reduced to a constant.

### Create Viper int by assigning a value
As it is usual in Python, a Viper variable is of type Viper `int when  you assign Viper ```int```value, either as a constant, integer expression or with the int() function. for example:
```py
    x = 0
    y = int(some_function_returning_an_integer())
    z = 1 + y 
    # now x, y and z are Viper int variables
    p = 2**3+1
```
If the variable is created by assigning an expression, the Viper code emitter will evaluate the expression at compile time.

Be aware: Integer constant expressions outside of what is called the "small integer" range of MicroPython are not Viper `int` but `builtins.int`.  On most architectures a MicroPython small integer falls is -2\*\*29 and 2\*\*29-1. 

For example:
```py
@micropython.viper
def myfunction();
    x = 0xffffffff # this is not a Viper int
    y = 1<<30 # this is not a Viper int
    z = 2**31-1  # this is not a Viper int
```
In all these cases a `builtins.int` variable will be created. See [here](##-making-sure-a-viper-int-is-a-viper-int) for a way prevent the problems described here.

### Create Viper int with a type hint on the function parameter
A second way to get a Viper `int` is with a type hint (type annotation) of a function parameter:
```py
@micropython.viper
def myfunction(x:int):
```
With the type hint, `x` is converted on the fly to the Viper `int` data type using the Viper int() function (see "```int()``` casting" below).


## Making sure a Viper int is a Viper int

There is a possible source of problems: when you initialize a Viper `int` with a integer expression that falls outside of the Viper int range (which is not the 32 bit range!), a `builtins.int` will be created instead, no warning. The same happens if you try initialize a Viper int with a variable of type `builtins.int`. These errors can go unnoticed.

Solution: Except for very short Viper functions, you could initialize all Viper `int` variables at the beginning setting them to zero (just as you might do in C language):
```py
@micropython.viper
def myfunction(x:int)->int:
    # declare all my integer variables
    x = 0
    limit = 0
    step = 0
```
This defines the type of the variable clearly as Viper `int`. Any attempt to change the type later will give a nice compile-time message `ViperTypeError: local 'x' has type 'int' but source is 'object'`, for example:
```py
    x = 0
    y = 0
    ...some code ...
    x = 2**30 #  2**30 yields a builtins.int
    ... some more code ...
    y = "hello"  # oh, some confusion here, can't change Viper int to string
```

Another way to make sure Viper variables are always of the intended type, is to use the type cast:
```py
    x = int(some expression)
```
But this is a perhaps a little bit less readable.

### Differences of Viper int and builtins.int data types

Viper ```int``` variables allow values from -2\*\*31 to 2\*\*31-1, whereas ```builtins.int``` variables have no practical range limit. For a `builtins.int`, if the value grows a lot, more memory will be allocated as needed.

As a result, arithmetic operations on Viper variables behave like operations in the C language 32 bit signed integer operations, for example:
* Arithmetic operations wrap around if exceeding the range, for example `131072*32768=0`, since the result overflows 32 bits (just like C)
* Shift left (```x<<1```): the bits shifted beyond the 32 most significant bit get lost. 
* No overflow exception

Arithmetic and logic operations for Viper ```int``` are very fast, since there is no need to check for data types, conversion rules and other conditions at runtime, and the necessary code can be generated at compile time.

Integer expressions that include Viper `int` are of type Viper `int`, example:
```py
@micropython.viper
def viper_expression():
    x = 1
    print(x<<31)
    # the value printed is -2147483648
```
Although `x<<31` is not being assigned to a Viper int, the expression is truncated to the size of a Viper `int` *before* passing it to the called function (print). This is a behavior a bit different from integer constant expressions, where the expression is evaluated, and *then* tested if the result fits into a Viper `int` or `builtins.int`.


There are no automatic conversion rules if a Viper ```int``` is used together with other data types. For example, this code will raise a compile time error: "ViperTypeError: can't do binary op between 'object' and 'int'":
```py
@micropython.viper
def myfunction(my_argument):
    x:int = 2
    x = my_argument + 1 # <- ViperTypeError: local 'x' has type 'int' but source is 'object'

    my_float_variable = 1.0
    my_float_variable = my_float_variable + x # <-- ViperTypeError: can't do binary op between 'object' and 'int'
myfunction(1)
```
The 'object' in the error message refers to `my_argument` and `my_float_variable`. The 'int' in the error message refers to the `1` Viper int constant.

To avoid that error message, the Viper ```int```variable x must be converted explicitly to float, and my_argument cast to a Viper `int`.
```py
@micropython.viper
def myfunction(my_argument):
    x:int = 2
    x = int(my_argument) + 1 # <- ViperTypeError: local 'x' has type 'int' but source is 'object'

    my_float_variable = 1.0
    my_float_variable = my_float_variable + float(x) # <-- ViperTypeError: can't do binary op between 'object' and 'int'
myfunction(1)
```

A Viper ```int``` is not an object, and thus does not support methods such as ```from_bytes()```or ```to_bytes()```. 

The \*\* operator (exponentiation, `__pow__`) is not implemented for Viper ```int```.

Be aware: In versions MicroPython 1.22 and prior, unary minus is not implemented, instead of `x=-a` use `x=0-a`. In version 1.23 the unary minus is being implemented, but not completely yet, so until further confirmation it's best to avoid unary minus, and use subtraction from zero instead.

Be aware: Do not use shift left or right with a negative value, i.e. `x<<(-1)` or `x>>(-1)` should not be used because the result is undefined. This mirrors the C language definition for shifting. Unlike regular MicroPython, there is no check (no exception raised) for negative shift amounts.

Be aware: If you are using a ESP32 or ESP32-S3 (or any XTENSAWIN processor, in MicroPython parlance), do not shift left by more than 31 bits. The result should be zero, but isn't. The RP2040 is not affected. Not tested yet for other processors. The workaround is to check if the shift amount is larger than 31 before shifting.


### int() casting

Within Viper decorated functions, the int() function will cast an expression to a Viper `int`. Examples:
```py
   x = int(len(some_array)) # Many MicroPython functions return builtins.int
   x = int(2**30) # \*\* is not implemented for Viper int and returns a builtins.int
   x = int(1) # Here int() is not necessary
   x = int(1+2) # Here int() is not necessary, 1+2 is a Viper int expression
   x = int(my_int_function())+1 # Use int() for any external function that returns a integer
 ```
```int("123")``` is rejected, the argument has to be a Viper `uint` or a `builtins.int`.

The int() function will return the 4 least significant bytes of the integer, similar to a C language expression: ```x && 0xffffffff```. If it is unclear that the input value is in the viper ```int``` range, the value has to be tested before casting. But in many practical applications, you can know beforehand the acceptable value ranges, and no additional overhead is incurred.

In other words, beware: `int()` just truncates values outside of the Viper int range chopping off the excessive bytes, no exception raised.

int() casting is very fast in Viper code. 

## The Viper uint data type

This data type is in most aspects similar to Viper `int` but the range is 0 to 2\*\*32-1, i.e. it's an unsigned 32 bit integer. Typical uses could be:

* As return type hint when return values could fall between the maximum `int` value and 2\*\*32-1
* For unsigned int arithmetic, in the range 0 to 2\*\*32-1
* For pointer arithmetic, see `ptr` data types below


The uint() cast function will return the last 4 bytes of `builtins.int` as a unsigned 32 bit int.

Viper `uint` does not support `//` (integer division) nor `%` (module) operators

Casting from `uint` to `int` and back just changes the type. There is no change in the data itself, the `int()` and `uint()` functions are a no-op for this case.
Example:
```py
@micropython.viper
def test_uint_int_assignments():
    x = int(-1)
    y = uint(x)
    print(f"{x=} uint(x)={y=:08x}, expected 0xffffffff")
    z = int(y)
    print(f"{y=} int(y)={y=:08x}, expected 0xffffffff")
```

## The viper bool data type

A bool Viper variable can be True or False. Boolean expressions are evaluated using the viper bool data type. This makes logic computations fast. 

You create a bool Viper variable by assigning `True`, `False` or the result of a logical expression of constants and Viper bool variables that yields `True` or `False`, for example:
```py
@micropython.viper
def function_with_bools():
    a = True
    y = 1
    z = 2
    b = y < z
    c = bool(y)
    # Now a, b and c are Viper bool variables
    # and a, b, and c are True
```


You can convert a `int` or `uint` to bool using the `bool()` cast function. A zero value is interpreted as False, any value different from zero is interpreted as True.

Similar to `builtins.int` for the Viper `int` data type, `builtins.bool` can be used to have the MicroPython boolean data type available.

As a note of minor interest, the bool Viper variable is stored as a 32 bit integer:
```py
@micropython.viper
def cast_bools():
    x = int(12345)
    b = bool(x)
    y = int(b)
    # Now y holds the same value as x
```
The explanation of this behavior is that similar to `int()` and `uint()`, `bool()` is a cast operator. If used on a Viper variable, only the type is changed, no conversion takes place (this is unlike the C (bool) cast, where the integer is converted to 0 or 1).

## The Viper ptr32, ptr16 and ptr8 data types
These data types are pointers to memory, similar to a C language `long *p;` or `unsigned char *p`. This is rather unusual for Python, where no pointers exist and memory access is well hidden within objects that protect that access.

If x is for example a ptr32, x[0] is the four bytes at the address the pointer is pointing to, x[1] the next four bytes, etc. 

You can assign to x[n], modifying the memory contents. There is no bounds checking, so a runaway index can destroy unintended memory locations. This could  block the microcontroller. Don't panic: this is recoverable with a hard reset. In very bad cases, it might be required to flash the MicroPython image again, but there is nothing to worry: it´s not feasible to brick the microcontroller with a runaway pointer.

### Declaration of pointer variables with type hints on function argument
```py
@micropython.viper
def myfunction( x:ptr32, b:bool )->int:
    print(x[0], x[1], x[2] ) # will print 1, 2, 3
    return x[1]
myfunction( array.array("l", (1,2,3,4)))

```

## Declaration of pointer variables with ptr32(), ptr16() and ptr8()
```py
@micropython.viper
def myfunction( )->int:
    int32_array = array.array("l", (1,2,3,4))
    x = ptr32( int32_array )
    print(x[0], x[1], x[2] ) # this will print 1, 2, 3
    ba = bytearray(10)
    y = ptr8(ba)
    y[0] = 1 # This will change ba[0]
    return x[1]
```

You can also cast a integer to a pointer:
```py
@micropython.viper
def myfunction()->int:
    GPIO_OUT = ptr32(0x60000300) # GPIO base register
    GPIO_OUT[2] = 0x10 # clear pin 4
```

The argument to `ptr32()`, `ptr16()` or `ptr8()` can be a Viper int, a uint or a bultins.int, no difference. Only the part needed for an address will be extracted.

You will have to search the microcontroller data sheet for the correct locations and meaning of each bit of the device registers. However, this type of manipulation can be very fast. Be aware: on a ESP32, MicroPython runs on top of FreeRTOS, which steals some CPU cycles every now and then, and can cause small but unwanted delays in Viper code.

The `uctypes` module has an `addressof()` function. The result can also be converted to a pointer:
```py
import uctypes
@micropython.viper
def fun():
    ba = bytearray(10)
    pba = ptr8( uctypes.addressof(ba) )
```
This also can be used to point at uctypes structures.


### Viper pointers and arrays

* ptr32 allows to manipulate elements of array.array of type "l" (signed 32 bit integer)
* ptr16 allows to manipulate elements of array.array of type "H" (unsigned 16 bit integer)
* ptr8 allows to manipulate elements of a bytearray or array.array of type "B" (unsigned 8 bit integer)

Be aware: A `bytes` object could be cast to a ptr8, but bytes objects are meant to be readonly, not to be modified.


### Values of indexed pointers
 
If x is a ptr32, ptr16 or ptr8, x[n] will return a Viper 32 bit signed integer.

The type of the object pointed to by the ptr variable is irrelevant. You could, for example, retrieve two elements of a "h" array with a single ptr32 x[n] assignment.

If x is a ptr16, x[n] will always be between 0 and 2\*\*16-1.

If x is a ptr8, x[n] will always be between 0 and 255.

### Assigning to a indexed pointer

* If x is a ptr8, `x[n] = v` will extract the least significant byte of the Viper integer `v`and modify the byte at x[n]

* If x is a ptr16, `x[n] = v` will extract the least two significant bytes of the Viper integer `v`and modify the two byte at x[n]

* If x is a ptr32, `x[n] = v` will modify the four bytes at `x[n]` with the Viper integer v.

In all cases you will need to convert to a Viper `int` first.

### Relationship with mem8, mem16 and mem32 functions

These functions are similar to ptr8, ptr16 and ptr32, but the Viper pointers are significantly faster.


### Viper pointer casting and pointer arithmetic

Viper pointers can be cast to a ```uint``` and back to `ptr32`, enabling to do pointer arithmetic. For example:
```py
@micropython.viper
def fun():
    a = array("i", (11,22,33,44))
    len_of_array:int = 4
    x:ptr32 = ptr32(a)
    pointer_to_second_half_of_a:ptr32 = ptr32(uint(x) + (int(len(a))//2)*4 )
```

Note that since the array element length is 4 bytes, you have to multiply by 4 yourself. The ptr32, ptr16 and ptr8 addresses are byte addresses. 

Be aware: Some architectures may reject ptr32 access of pointers that are not multiple of four. Accessing odd bytes will most probably crash the program, no way to trap that as an exception.

# Viper function parameters and return values

From the point of view of the caller, Viper functions behave just like any other MicroPython functions. The workings of the Viper variables is hidden from the caller. The Viper data types are not visible outside the Viper function.

The static analysis that MicroPython does, is Viper function by Viper function. No type hint information, nor the fact that they are Viper functions is carried over from the analysis of one function to another.

The call overhead for a Viper function is substantially lower than call overhead for a undecorated function. For example, for a function with 5 parameters, the call processing time with Viper may be 2 times faster than a undecorated function, including the time to convert to and from the Viper data types. 

## Viper function parameters

For integer parameters, use the `int` or `uint` type hint to get automatic conversion to a Viper int. The conversion is done internally by MicroPython using the `int()` or `uint()` cast operator respectively:
```py
@micropython.viper
def my_function( x:int, z:uint ):
    # now x and z are Viper data type variables
    ....
```

Similarly, a boolean parameter is cast automatically to a Viper bool:
```py
@micropython.viper
def my_function( b:bool ):
    # b is a Viper bool variable
    ....
```

For arrays and bytearrays, use the ptr32, ptr16 and ptr8 type hints in the function parameters to get fast access to the arrays. The cast from an array to a pointer is done automatically while processing the call, i.e. a ptr8(), ptr16() or ptr32() cast is applied automatically to the argument.
```py
@micropython.viper
def my_function( p:ptr32 ):
    ....
a = array.array("l", (0 for x in range(100)))
my_function( a )
```


Viper functions do not accept keyword arguments nor optional arguments.

Some older versions of the MicroPython docs state that there is a maximum of 4 arguments for a Viper function. That is not a restriction anymore (apparently since MicroPython 1.14 or so).

## Passing a Viper variable to a called function
In a Viper decorated function, you can certainly call another function. The called function can be `@micropython.viper` decorated, `@micropython.native` decorated or plain (undecorated), a bound or unbound method and you can use a generator (however: no await of an async function inside a Viper function).

If you pass a Viper variable as argument to a function, it gets converted to a `builtins.int` on the fly:
* A Viper `int` is treated as signed.
* A  `ptr32`, `ptr16`, `ptr8` and `uint` always leave a positive result, no sign, but they are converted also to a `builtins.int` since there are no pointers nor unsigned ints outside Viper functions.

```py
@micropython.viper
def viperfun():
    x = int(1) # x now is a Viper int
    some_function(x) # some_function will get 1
    y = uint(0xffffffff) 
    some_function(y) # some_function will get 0xffffffff == 4294967295
    z = int(-1)
    some_function(z) # some_function will get a -1
    ba = bytearray(10)
    pba = ptr8(ba)
    some_function(pba) # #  # some_function will get a number like 1008145600, which is the address of ba, no sign
```

The rationale here is that the Viper data types don't make sense outside the Viper function, so they are converted to standard MicroPython `builtins.int` when passed as parameters.  The pointers don't carry information about the type, so they can't be cast back to an array. If you wish to use a returned pointer, you have to cast it back to a pointer explicitly in a Viper function or use functions like machine.mem8(), machine.mem16() or machine.mem32().

A nice effect of this is that you can pass a pointer down to a Viper function:
```py
@micropython.viper
def fun1():
    ba = bytearray(10)
    pba = ptr8(ba)
    # Call another Viper function, pass a pointer
    fun2(pba)
@micropython.viper
def fun2( mypointer:ptr8 ):
    # mypointer is now pointing to the bytearray ba
    x = mypointer[0] 
```

A side effect of this behavior is that `type(viper_variable)` always returns class `builtins.int`, because the Viper variable is converted to a `builtins.int` during the call process.

Talking about detecting type: inside a Viper function, `isinstance(viper_variable,int)` will give a compile-time error `NotImplementedError: conversion to object`, since `int` is a Viper data type, not a MicroPython class. However, `isinstance(viper_variable, builtins.int)` will return `True` since the `viper_variable` will be converted to a MicroPython `builtins.int` automatically during the call process. This also applies to `bool`.


## Viper function return values
If the function returns a Viper variable, a return type hint must be supplied, for example:

```py
@micropython.viper
def function_returns_integer(param1:int)->int:
    return 1
@micropython.viper
def function_returns_bool(x:int)->bool:
    return True
```
The conversion of the return value back to `builtins.bool` is done automatically. 

You can return a pointer in a Viper function, but you must add the return type hint as ->ptr8, ->ptr16 or ->ptr32. The pointer returned is converted to a `builtins.int` and it's value will be the memory address of the array. The addresses are always byte addresses. The function that uses that returned integer must cast it to a pointer of the correct type to make things work, for example:
```py
@micropython.viper
def function_returning_pointer()->ptr8:
    ba = bytearray(10)
    pointer_to_ba = ptr8(ba)
    pointer_to_ba[0] = 123
    # Return a pointer to a bytearray
    return pointer_to_ba

@micropython.viper
def function_using_returned_pointer( ):
    mypointer = ptr8(function_returning_pointer())
    # mypointer is now pointing to the bytearray ba
    x = int(mypointer[0])
    print(f"x has the value 123: {x=}") 
```

Returned pointers can also be used with `machine.mem8` for `ptr8`, `machine.mem16` for `ptr16` and `machine.mem32` for `ptr32` addresses. The `machine.mem` objects are certainly slower than Viper pointer operations.

If the value returned by the function is any other object (i.e. if the value returned is not a Viper data type), you do not need to specify a type hint. If you wish, you can use `->object` as return type hint, for example:
```py
@micropython.viper
# MicroPython object returned, no return type hint required
def function_returns_something(x):
    if x > 10:
        return (1,2,3)
    if x > 0:
        return True
    if x < -10:
        return None
    return x
@micropython.viper
# ->object can be optionally used as return type hint
# for any MicroPython object (except Viper data types)
def function_returns_object(x)->object:
    return (1,2,3)
```


# Other topics

## Range vs. while

`range()` does work under Viper, so you could write: ```for x in range(10)```. It is a bit faster to use a while loop, with viper ints for j, limit and step. 
```py
    limit:int = 100
    step:int = 2
    j:int = start
    while j < limit:
           ...loop body....
        j += step
```

You can also use pointer arithmetic to get rid of a counter to control the while loop, and that's even faster! Using pointer arithmetic also enables to use `p[0]` instead of `p[i]`, again an improvement. This timing was done on a 80Mhz Cortex-M3 in the W600:
```py
from array import array
from time import ticks_us, ticks_diff

a = array('i', (2*i+1 for i in range(10000)))

@micropython.viper
def vip_add1(p: ptr32, l: int) -> int:
    r:int = 0
    for k in range(l):            # range() works, but is not fastest
        r += p[k]                 # accessing with p[i]
    return r

@micropython.viper
def vip_add2(p: ptr32, l: uint) -> int:
    r:int = 0
    k:uint = uint(0)
    while k < l:                  # a while loop is faster 
        r += p[k]                 # accessing with p[i]
        k += 1
    return r

@micropython.viper
def vip_add3(p: ptr32, l: uint) -> int:
    r:int = 0
    pstop: uint = uint(p) + 4*l
    while uint(p) < pstop:        # directly looping the pointer to the array and indexing
        r += p[0]                 # with p[0] is faster than accessing with p[i]
        p = ptr32(uint(p) + 4)    # casts necessary because the types are fixed in viper
    return r


t0 = ticks_us()
sum1 = vip_add1(a, len(a))           # --> 100000000
t1 = ticks_us()
sum2 = vip_add2(a, len(a))           # --> 100000000
t2 = ticks_us()
sum3 = vip_add3(a, len(a))           # --> 100000000
t3 = ticks_us()

print('vip_add1:', sum1, 'time:', ticks_diff(t1, t0)/10000, 'µs per it.') # --> 0.7064 µs
print('vip_and2:', sum2, 'time:', ticks_diff(t2, t1)/10000, 'µs per it.') # --> 0.5767 µs
print('vip_and3:', sum3, 'time:', ticks_diff(t3, t2)/10000, 'µs per it.') # --> 0.3635 µs
```


## Global variables
If you need to do integer arithmetic with a global variable, this works:
```py
import builtins
x = 1
g = None
@micropython.viper
def global_test():
    global x, g
    viper_int:int = 333
    g = viper_int
    x = x + builtins.int(10)
print(x) # x now is 11 and g is now 333

```
You can assign a Viper integer to a global variable, it gets converted to a `builtins.int`.

The global variable `x` is of type `builtins.int` and you cannot mix Viper `int` with `builtins.int`. In the example, `10` is a Viper `int` constant and has to be converted to a `builtins.int` before operating.

For Viper bool variables, similar rules apply.

## Example of nonlocal and closure with Viper functions

If you access nonlocal integer variables that belong to a non-Viper function, make sure the expression you assign to that is a `builtin.int`. Assigning a Viper int to a nonlocal variable does nothing.

Here is a working example of a closure:
```py
import builtins
def foo():
    x = 0
    @micropython.viper
    def inner() -> int:
        nonlocal x
        x = builtins.int( int(x)+1 )
        return int(x)
    return inner
bar = foo()
bar()
bar()
bar()
```
Since x is a non-Viper integer, we have to use non-Viper arithmetic in the inner function to make this work.

In the previous example, if `foo()` is decorated with `@micropython.viper`, we get a compile time message complaining about x (ViperTypeError: local 'x' used before type known). Since x is not an object but a raw Viper variable, it cannot be referred to as a `nonlocal`. 

You can't make a Viper variable nonlocal (compile-time error `ViperTypeError: local 'x' used before type known`)

Beware: You can't change the type of a nonlocal variable inside a viper function to an integer. Example:
```py
def nonlocal_fails():
    y = None
    @micropython.viper
    def internal_viper():
        nonlocal y
        viperx:int = 111
        y = viperx # <--- this assignment will not work!
        return y
    return internal_viper()
print(nonlocal_fails(), "expected result 111")
```
The actual result is 55, but depends on the value assigned (111). The device may freeze or give any error, so don't do this.

## Viper in classes
A specific method (including `__init__`, `@staticmethod` and `@classmethod`) can have the @micropython.viper decorator.

The complete class can be decorated:
```py
@micropython.viper
class MyClass:
    def __init__( self ):
        self.a = 10
        # __init__ will be a Viper decorated function, by inclusion
```
Instance variables such as ```self.a``` can only be MicroPython objects and can never be of a Viper data type (remember that a Viper `int` is not an object). 

You can assign a Viper `int ` to a instance variable like self.x. The Viper int gets converted to a `builtins.int` automatically, Operations such `self.x = self.x + viper_integer` requiere to convert the Viper integer to a `builtins.int`: `self.x = self.x + builtins.int(viper_integer)`


## Slices
Viper integers cannot be used in slices. This is a restriction. The following code will not work:
```py
    x = bytearray((1,2,3,4,5))
    print("function slice", x[0:2])
```
This is a workaround: `x[builtins.int(0):builtins.int(2)]`

## async and generators

Viper decorated functions cannot have the async attribute (it crashes) nor be generators (`NotImplementedError: native yield` compile time error`)

Workaround: async functions and generators can call Viper functions.

However, a Viper function can call a generator.

## Type hints in the body of a Viper function

Type hints in the body of the of a Viper function are not required, but add nicely to readability. So although not mandatory, it's perhaps more readable to declare the variables with type hints:
```py
@micropython.viper
def myfunction():
    # declare all my integer variables
    x:int = 0
    limit:int = 0
    step:int = 0
```

You can't use `builtins.int` as type hint, and there is no `type` statement in MicroPython. So `builtins.int` will be always written without type hint.

## Test if a variable is of type Viper int
In compile time:
```py
    # Test if x is a Viper int variable
    x = "hello"
```
If x is a Viper variable, the assignment will fail at compile time.

In runtime, to distinguish between a Viper int and a `builtins.int`:
```py
    x = 1
    if x << 31 < 0:
       print("x is a Viper int")
```
The expression in the if statement will be true if x is a signed Viper `int`, as opposed to a `builtins.int`. A `builtins.int` will remain positive, no matter how many times you shift the value.

## Source code of the Viper code emitter
The Viper code emitter is in the MicroPython code repository in `py/emitnative.c`, embedded in the native code emitter.


# Some error messages

## ViperTypeError: can't do binary op between 'int' and 'object'

This is a compile time error

In this context, 'int' means a Viper `int` and 'object' any other MicroPython object including a `builtins.int`. The most common cause is trying to do an arithmetic or logic operation of a Viper `int` and a `builtins.int`.

Another example for this error message is to combine a Viper int with a float: if `x` is a Viper `int`, then `f = 1.0 + x` will raise this error. Use `f = 1.0 + float(x)` instead. Similarly with


## ViperTypeError: local 'x' has type 'int' but source is 'object'

This compile time error happens when `x` is of type Viper `int` but an object is later assigned to x, for example:
```py
   x = 0
   x = "hello"
```
It's likely that the 'object'  is `builtins.int`. You have to cast that with int() to a Viper `int`.


`
## TypeError: can't convert str to int
A cause of this can be doing, for example, `int("1234")`. The Viper `int()` is a casting operator and does not convert. A workaround could be `int(builtins.int("1234"))`


# Some interesting links
The official documentation: https://docs.micropython.org/en/v1.9.3/pyboard/reference/speed_python.html

Damien George's talk on MicroPython performance: https://www.youtube.com/watch?v=hHec4qL00x0

Interesting discussion about Viper, parameters and optimization. Also see Damien George's comment on Viper data types and casting: https://forum.micropython.org/viewtopic.php?f=2&t=1382

How to use the Viper decorator. Several examples of Viper and GPIO registers. https://forum.micropython.org/viewtopic.php?f=6&t=6994

Closure and some interesting low level stuff: https://github.com/micropython/micropython/issues/8086

Slices and Viper: https://github.com/micropython/micropython/issues/6523

32 bit integer operations: https://github.com/orgs/micropython/discussions/11259

Another example manipulating manipulating GPIO: https://forum.micropython.org/viewtopic.php?f=18&t=8266

A TFT display driver using Viper code, look at TFT_io.py: https://github.com/robert-hh/SSD1963-TFT-Library-for-PyBoard-and-RP2040

Use of Viper decorator: https://github.com/orgs/micropython/discussions/11157

Step by step with a real problem: https://luvsheth.com/p/making-micropython-computations-run

The MicroPython tests for Viper have some examples, see all cases prefixed by "viper_": https://github.com/micropython/micropython/tree/master/tests/micropython

The issue that gave origin to this wiki page, with interesting discussions. This also is the source for some examples here: [#14297](https://github.com/orgs/micropython/discussions/14297)

Search https://forum.micropython.org and https://github.com/orgs/micropython/discussions for Viper. There are many insights and examples.

Some Viper code examples here: https://github.com/bixb922/viper-examples, including a integer FFT (Fast Fourier Transform) and autocorrelation. Many examples to test or demonstrate how viper works.



