There are many ways to, and degrees of securing any computer system, and most of the options to improve security also have some sort of a downside. Either in speed, complexity to build, distribute or use the software, or in increased requirements to the hardware platform your solution needs to run on.

## Threat assessment and modeling
In order to be able to make a good or appropriate selection from the menu of security controls that you could apply, you will need to define what you want, or need, to secure against. After you know in enough detail the risks to secure against, only then you can start to apply the security controls to reduce that risk to a level that you or your users find acceptable.
Compare this to real life: you probably want you bank's vault to have a better lock than your toolshed doors.

While it is possible to do this on intuition, it can be difficult as often you need to think alternately as an attacker and as a defender.

According to the [Threat Model Manifesto](https://www.threatmodelingmanifesto.org/), the threat modeling process should answer the following four questions:

* What are we working on?
* What can go wrong?
* What are we going to do about it?
* Did we do a good enough job?

You do not need to start from scratch - there is a significant amount of documents and tools and videos that can help you do this.
But the best way to learn about threat modelling is by start doing it

## Responses 
After risks have been identified, then responses to these risks need to be identified. Generally these are categorized as : 
* Mitigate. Take action to reduce the likelihood that the threat will materialize.
* Eliminate: Simply remove the feature or component that is causing the threat.
* Transfer. Shift responsibility to another entity such as the customer.
* Accept. Do not mitigate, eliminate, or transfer the risk because none of the above options are acceptable given business requirements or constraints.

### Further reading
 - [Threat Model Manifesto](https://www.threatmodelingmanifesto.org/)
 - [Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
 - [Awesome Threat Modeling](https://github.com/hysnsec/awesome-threat-modelling?tab=readme-ov-file#awesome-threat-modeling-)
 - [Security for IoT](https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-iot/security/)

# Security controls that can be applied to MicroPython 
## Frozen code


> Category: Reduces (not eliminate) the likelihood of someone tampering with your code 

MicroPython has a feature that allows Python code to be “frozen” into the firmware, as an alternative to loading code from the filesystem.

This has the following benefits:

 - the code is pre-compiled to bytecode, avoiding the need for the Python source to be compiled at load-time.
- the bytecode can be executed directly from ROM (i.e. flash memory) rather than being copied into RAM. Similarly any constant objects (strings, tuples, etc) are loaded from ROM also. This can lead to significantly more memory being available for your application.
 - on devices that do not have a filesystem, this is the only way to load Python code.

See : [MicroPython Manifest files](https://docs.micropython.org/en/latest/reference/manifest.html)
Note that while frozen code is compiled to bytecode or even native code, this does not mean that your code cannot be read. While it may be more difficult to read, that will not stop a motivated person from reading and reverse enginering your code.

## Securing the REPL access with a password.
See : https://github.com/shariltumin/password-protected-REPL-micropython 

## Disabling the WebREPL
> Category: Eliminate any access via WebREPL
  * `#define MICROPY_PY_WEBREPL 0`

## Disabling the Python compiler
> Category: Eliminates to option for a user to run code that has not been pre-compiled. 
> Note: may also need to prevent a user to transfer css-compiled `.mpy` files to the MCU
  * `#define MICROPY_ENABLE_COMPILER 0`


## Disable serial REPL access
If you want sys.stdin/sys.stdout and no REPL, then the other option is to use a normal build config and structure your [main.py](http://main.py/) so it absolutely can't drop to the REPL.

Something like this in `main.py`:
```py
import machine, app
try:
    app.main()
finally:
   machine.reset()
```


Another config that should work everywhere is `#define MICROPY_ENABLE_COMPILER 0` which will completely remove the ability for the board to compile python into bytecode; this indirectly disables repl as the repl requires the compiler to execute any entered code.

The configuration for handling whether repl is connected to usb / uart is implemented with the stdin / stdout functions in `https://github.com/micropython/micropython/blob/master/ports/esp32/mphalport.c`

A quick scan of that file (from latest master) looks like #define MICROPY_HW_ENABLE_UART_REPL (0) should work on the current version to disconnect stdio / repl from the uart.

For more details : [Discussion](https://github.com/orgs/micropython/discussions/16353#discussioncomment-11452937) 

## Secure physical access
Note: Securing pysical access with small devices likel MCUs is very hard. and an adigium in security is that "Physical access is the end of all security" 

## Port/vendor specific solutions
 * Encryption/Signing

## Minimise attack surface
  * Shut down peripherals and network as much as possible


