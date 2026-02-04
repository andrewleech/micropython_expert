Note: These are tips for developers who are developing MicroPython itself, not working with MicroPython as a tool.

Link-time optimisation (LTO) is a compiler feature which can significantly reduce code size by finding optimisations across multiple compilation units.

## Diagnosing LTO Issues

Sometimes an issue may appear with LTO=1 that goes away with LTO=0. There are generally two possible reasons for this:

* Unexposed errors in the source files, that only appear with the more aggressive cross-compilation-unit optimization done by LTO. (For example, a symbol is declared with different types in different source files.)
* Toolchain or binutils assembler/linker bugs. Hopefully not these!

Some tips to dig into LTO errors:

### `-save-temps`

LTO generates a number of enormous intermediate assembly files, which is often the "source file" shown for an LTO-specific error, i.e.

```
LINK build-NUCLEO_F091RC/firmware.elf
/tmp/cccK8t2U.s: Assembler messages:
/tmp/cccK8t2U.s: Error: unaligned opcodes detected in executable segment
make[1]: *** [/tmp/ccu7PpiF.mk:5: /tmp/ccCeWcJW.ltrans1.ltrans.o] Error 1
```

However these files are all temporary (in /tmp) and already deleted when GCC exits. Add `LDFLAGS += -save-temps` to the Makefile in order to place these files in the build directory and keep them. With this option, the files will now have names like `build-NUCLEO_F091RC/firmware.elf.ltrans1.ltrans.s` and `build-NUCLEO_F091RC/firmware.elf.ltrans1.ltrans.o`.

If an assembler error is showing, you can probably recreate it by passing the temporary file directly into as - i.e. `arm-none-eabi-as build-NUCLEO_F091RC/firmware.elf.ltrans1.ltrans.s`. This lets you tweak the generated assembler code and narrow down a root cause.

### Maximum Partitions

Depending on how the call graph is partitioned by the [LTO whole program analyzer](https://gcc.gnu.org/onlinedocs/gccint/LTO-Overview.html), a single `ltrans` assembly file might be 200,000+ lines long. Not the best to debug...

Add `LDFLAGS += -save-temps -flto-partition=max` to the Makefile. Now, GCC will create one ltrans partition per compilation unit (i.e. per source file). This is very inefficient for LTO, but very good for debugging LTO issues - provided the issue still occurs in this configuration. Each file will now have a name like `firmware.elf.ltrans1932.ltrans.s` and should contain the output from only one compilation unit.
