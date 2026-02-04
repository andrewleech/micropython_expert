# Differences to CPython

*NOTE: This page provides high-level overview of differences between MicroPython and CPython. Some specific points may be out of date. Specific list differences are now maintained as a part of MicroPython documentation at http://docs.micropython.org/en/latest/unix/genrst/index.html*

MicroPython does not support the entire python standard library. If a module is missing it will be due to the in-applicability of that module for use in an embedded controller. High memory consumption (e.g. sqlite3) or a lack of a certain required hardware feature (e.g. multiprocessing) are reasons that some modules can not be implemented for some microcontrollers. The full list of standard python libraries can be found here: [Python 3.4 standard lib](https://docs.python.org/3.4/library/index.html)

There are several differences between CPython3 (considered to be a reference implementation of the Python3 language) and MicroPython. These differences are classified into 3 categories, each category having a different status regarding the possibility that items belonging to it will change. 

## Differences By Design
MicroPython is intended for constrained environments, in particular, microcontrollers, which have orders of magnitude less performance and memory than "desktop" systems on which CPython3 runs. This means that MicroPython must be designed with this constrained environment in mind, leaving out features which simply won't fit, or won't scale, with target systems. "By design" differences are unlikely to change.

1. MicroPython does not ship with an extensive standard library of modules. It's not possible and does not make sense, to provide the complete CPython3 library. Many modules are not usable or useful in the context of embedded systems, and there is not enough memory to deploy the entire library on small devices. So MicroPython takes the minimalist approach - only core datatypes (plus modules specific to particular hardware) are included with the interpreter, and all the rest is left as 3rd-party dependencies for particular user applications. The [micropython-lib](https://github.com/micropython/micropython-lib) project provides a non-monolithic standard library for MicroPython ([forum](http://forum.micropython.org/viewtopic.php?f=5&t=70))
1. Unlike CPython3, which uses reference-counting, MicroPython uses garbage collection as the primary means of memory management.
1. MicroPython does not implement complete CPython object data model, but only a subset of it. Advanced usages of multiple inheritance, ``__new__`` method may not work. Method resolution order is different (#525). Metaclasses are not supported (at least yet).
1. MicroPython design is not based around descriptor objects. So far, we were able to implement all native Python features (like properties) without explicit descriptors. Descriptors are considered "overdynamic" feature, and conflicts with the aim of being fast and efficient. However, basic support for descriptors in user-defined classes is now implemented. 
1. By virtue of being "micro", MicroPython implements only subset of functionality and parameters of particular functions and classes. Each specific issue may be treated as "implementation difference" and resolved, but there unlikely will ever be 100% coverage of CPython features.
1. By virtue of being "micro", MicroPython supports only minimal subset of introspection and reflection features (such as object names, docstrings, etc.). Each specific feature may be treated as "implementation difference" and resolved, but there unlikely will ever be 100% coverage of CPython features.
1. print() function does not check for recursive data structures in the same way CPython does. There's however checks for stack usage, so printing recursive data structure won't lead to crash due to stack overflow. Note that it's possible to implement more CPython-like handling of recursive data structures on the Python application level. Do this by writing a function which keeps the history of each object visited, and override the builtin print() with your custom function. Such an implementation may of course use a lot of memory, which is why it's not implemented at the MicroPython level.
1. MicroPython optimizes local variable handling and does not record or provide any introspection info for them, e.g. locals() doesn't have entries for locals.
1. MicroPython uses different floating representations on different platforms which can lead to [substantially reduced numerical precision](https://github.com/micropython/micropython/wiki/Floating-Point-Support).

## Implementation Differences
Some features don't cater for constrained systems, and at the same time are not easy to implement efficiently, or at all. Such features are known as "implementation differences" and some of them are potentially the subject for future development (after corresponding discussion and consideration). Note that many of them would affect the size and performance of any given MicroPython implementation, so sometimes not implementing a specific feature is identified by MicroPython's target usage.

1. Unicode support is work in progress. It is based on internal representation using UTF-8. Strings containing Unicode escapes in the \xNN, \uNNNN, and \U000NNNNN forms are fully supported; \N{...} is not supported. [#695](//github.com/micropython/micropython/issues/695).
1. Object finalization (``__del__()`` method) is supported for builtin types, but not yet user classes. This is tracked by [#245](//github.com/micropython/micropython/issues/245).
1. Subclassing of builtin types is partially implemented, but there may be various differences and compatibility issues with CPython. [#401](//github.com/micropython/micropython/issues/401)
1. Buffered I/O streams (io.TextIOWrapper and superclasses) are not supported.
1. `async def` keyword is implemented with the following simplifications: there's no separate "coroutine" object type, `async def` just defines a generator function without requirement for "yield" or "yield from" to appear in function body. Usage of "yield" or "yield from" in `async def` function is not detected or banned.
1. `async with` should be equivalent to [PEP492 description](https://www.python.org/dev/peps/pep-0492/#asynchronous-context-managers-and-async-with).
1. `async for` should be equivalent to [PEP492 description](https://www.python.org/dev/peps/pep-0492/#asynchronous-iterators-and-async-for).
1. There's no support for "Future-like objects" with `__await__` method. `await` can be used only on coroutines and generators (not "Future-like objects"). It's also just a syntactic sugar for "yield from" and thus accepts iterables and iterators, which are not allowed in CPython.
1. Instance `__dict__` support is optional (disabled in many ports) and read-only, so `foo.__dict__['bar'] = 23` or `foo.__dict__.update({'bar': 23})` does not work. [#1757](//github.com/micropython/micropython/issues/1757) [#2139](//github.com/micropython/micropython/issues/2139)

## Known Issues
Known issues are essentially bugs, misfeatures, and omissions considered such, and scheduled to be fixed. So, ideally any entry here should be accompanied by bug ticket reference. But note that these known issues will have different priorities, especially within wider development process. So if you are actually affected by some issue, please add details of your case to the ticket (or open it if does not yet exist) to help planning. Submitting patches is even more productive. (Please note that the list of not implemented modules/classes include only those which are considered very important to implement; per the above, MicroPython does not provide full standard library in general.)

1. <strike>Some functions don't perform argument checking well enough, which potentially may lead to crash if wrong argument types are passed.</strike>
1. Some functions use ``assert()`` for argument checking, which will lead to crash if wrong argument types are passed/erroneous conditions are faced. This should be replaced with Python exception raising.
1. <strike>It's not possible to override builtin functions in a general way. So far - no "builtins" module is implemented, so any overrides work within a current module only. [#959](//github.com/micropython/micropython/issues/959)<strike>
1. Persistent bytecode support (analog of .pyc) is in beta.
1. <strike>print() function doesn't use the Python stream infrastructure, it uses the underlying C printf() function directly. This means if you override sys.stdout, then print() won't be affected. </strike>[#209](//github.com/micropython/micropython/issues/209)
1. Currently, it's not possible to override sys.stdin, sys.stdout, sys.stderr (for efficiency, they are stored in read-only memory).
1. <strike>Some more advanced usages of package/module importing is not yet fully implemented. [#298](//github.com/micropython/micropython/issues/298)</strike>
1. <strike>Exception handling with generators is not fully implemented.</strike> (Some small details may need to be done yet.) [#243](//github.com/micropython/micropython/issues/243)
1. str.format() may miss few advanced/obscure features (but otherwise almost completely implemented). [#407](//github.com/micropython/micropython/issues/407), [#574](//github.com/micropython/micropython/issues/574)
1. <strike>% string formatting operator may miss more advanced features</strike> [#403](//github.com/micropython/micropython/issues/403), [#574](//github.com/micropython/micropython/issues/574)
1. ``struct`` module implementation (named ``ustruct``) should have all basic functionality<strike>, but misses some syntactic sugar (like repetition specifiers in type strings)</strike>. It's named differently to allow implement full ``struct`` functionality on Python level.
1. Instead of ``re`` module, minimified "ure" module is provided is subset of functionality. micropython-lib also offers more complete implementation based on PCRE engine, for "unix" port [#13](//github.com/micropython/micropython/issues/13)
1. Only beginning of ``io`` module and class hierarchy exists so far.
1. ``collections.deque`` class is not implemented.
1. <strike>``memoryview`` object not implemented.</strike>
1. Container slice assignment/deletion is only partially implemented. [#509](https://github.com/micropython/micropython/issues/509)
1. 3-argument slicing is only partially implemented.
1. <strike>Keyword and keyword-only arguments need more work</strike> [#466](https://github.com/micropython/micropython/issues/466), [#524](//github.com/micropython/micropython/issues/524).
1. Only basic support for ``__new__`` method is available [#606](//github.com/micropython/micropython/issues/606), [#622](//github.com/micropython/micropython/issues/622).
1. <strike>Bitwise operations on long ints are only partially implemented (x & 0xffffffff idiom for casting signed 32-bit value to unsigned works).</strike> [#1810](https://github.com/micropython/micropython/pull/1810)