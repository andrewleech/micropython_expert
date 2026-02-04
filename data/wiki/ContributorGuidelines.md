# Code of Conduct

Please read the [MicroPython Code of Conduct](https://github.com/micropython/micropython/blob/master/CODEOFCONDUCT.md) before contributing to the MicroPython project.

# Getting started

We welcome all types of contributions, across a wide variety of different domains.

* The core Python virtual machine and runtime
* The standard library and MicroPython-specific built-ins
* The ["MicroPython Library"](https://github.com/micropython/micropython-lib)
* Ports to different architectures and microcontrollers
* Board definitions
* Documentation
* Developer tools and workflow
* Community management

There's information about [getting started with MicroPython development](https://docs.micropython.org/en/latest/develop/gettingstarted.html) in the official documentation. For more assistance, the [discussion forums](https://github.com/micropython/micropython/discussions) and the [Discord server](https://micropython.org/discord) are a great way to ask questions and connect with other MicroPython developers.

It's often a good idea before starting a piece of work to get some feedback from the community or the project maintainers, to ensure that your effort will not be wasted. Raising an issue with `"RFC: "` as the start of the title is a good way to do this.

MicroPython itself is written in C, but most of the support tooling and build infrastructure, as well as drivers and libraries are written in Python. In general, if it's possible to implement something in either C or Python, we prefer Python. It is possible to extend MicroPython in C++, but no C++ code is used in the main repository.

When working on MicroPython, especially the core VM, runtime, or standard library, it is much more productive to use the Unix or Windows ports, as you can run it locally without having to deploy it to a device. The Unix port works on Linux (including embedded Linux distributions), macOS, and *BSD, and Windows Subsystem for Linux. The Windows port provides both a Visual Studio project and a Cygwin-based makefile build.

# What to contribute

## Bug fixes
When submitting a fix, please include a detailed description of how the bug occurs, ideally with reproduction steps, and what boards/ports/devices it effects.

Bug fixes can sometimes have unintended and complicated interactions with other features and an the "obvious" fix might not always be the "correct" fix. It might take a bit of backwards-and-forwards discussion to resolve this.

## New features
As much as we'd like to, in the spirit of keeping things "micro", not all features can be added to MicroPython. It's important to find the right subset of functionality that makes sense for the embedded world.

MicroPython supports devices with as little as 128kiB of flash and 16kiB of RAM. Even the Unix port can be used to run MicroPython on truly minimal Linux systems with just 4MiB or even 2MiB of flash. To give you an idea of how highly we value code size, the MicroPython team will spent hours of effort just to save 100's (or even 10's) of bytes. This unfortunately means that the code can be more complicated, but it is a worthwhile trade-off.

In many cases, features can be enabled conditionally for a given target (i.e. boards with lots of flash or RAM, or the Unix/Windows ports). See the various `MICROPY_` macro definitions in the codebase. The continuous integration will check any new changes to ensure that our "minimal" ports do not increase in size.

### Discuss first

If you're thinking of contributing a significant new feature and not sure if it's suitable, consider starting a [Discussion](https://github.com/micropython/micropython/discussions) or opening an [Issue](https://github.com/micropython/micropython/issues) with a feature request first. Explain any work you plan to do, and why you think it would be good for MicroPython to include and support this feature.

You should also search the open [Issues](https://github.com/micropython/micropython/issues), [Pull Requests](https://github.com/micropython/micropython/pulls), and [Discussions](https://github.com/micropython/micropython/discussions) first to see if anyone else has a similar idea.

### Adding Python library features

Some guidelines if adding a new Python library feature (like a new function or a new module):

* For features that also exist in [CPython](https://docs.python.org/3.5/library/), the MicroPython functionality should be a compatible subset of the CPython functionality. For example, if a module with the same name exists in CPython then MicroPython should not add an API or a name which isn't already in CPython. This is a relatively new goal, so many MicroPython modules have functions that don't exist in CPython. These are considered legacy, documented as MicroPython additions, and the goal is to not add more if possible.
* If the functionality can be implemented in a pure Python module, contribute it to [micropython-lib](https://github.com/micropython/micropython-lib/) as a package that can be installed on demand.
* Otherwise, consider if it's more suitable to add the feature to a [port-specific library](https://docs.micropython.org/en/latest/library/index.html#port-specific-libraries), the [machine](https://docs.micropython.org/en/latest/library/machine.html) module, or (in some very specific cases) the [micropython](https://docs.micropython.org/en/latest/library/micropython.html) module.

### Adding Python syntax features

If you want to change the Python language features supported by MicroPython, then it's a good idea to discuss this with the maintainers first.

### Adding hardware features

New hardware driver support or functionality is always welcome:

* If implementing an existing [machine](https://docs.micropython.org/en/latest/library/machine.html) API for a new port (for example, adding `machine.I2S` to a port which has I2S hardware but no MicroPython driver yet), then the API must match the existing `machine` API whenever possible. Additions that substantially change an existing `machine` API for a single port only, or have non-trivial "special case" notes, may be better suited as port-specific APIs (see below).
* Contributing a new [machine](https://docs.micropython.org/en/latest/library/machine.html) API that adds brand new functionality (for example, adding a `machine.TenGbpsEthernet` class for 10Gbps Ethernet controllers) must be very carefully implemented and designed. These APIs must be generic to work on multiple ports, while still being efficient and small in code size. If you're planning to contribute such a driver, please discuss with the maintainers and the community first. You could start with a [Discussion](https://github.com/micropython/micropython/discussions) or make a Pull Request that only adds the docs for your proposed API.
* If a new driver has port- or hardware-specific features that aren't suitable for a [machine](https://docs.micropython.org/en/latest/library/machine.html) API then consider adding them to a [port-specific library](https://docs.micropython.org/en/latest/library/index.html#port-specific-libraries). (Except `pyb`, this is legacy and new code should go into `stm` instead). This allows more freedom to expose the hardware's exact capabilities.

## Ports
We welcome ports to new architectures and microcontroller families. However, not all ports can be accepted into the main repository as each port is a significant maintenance overhead for the core team. It is straightforward to maintain a third-party "out-of-tree" port using MicroPython as a submodule.

## Board definitions
Each port contains a set of board definitions. Each one of these boards will be compiled automatically and published on the [downloads page](https://micropython.org/download/). Board definitions will typically also require a thumbnail image to be added to the [MicroPython media repository](https://github.com/micropython/micropython-media) via a PR.

# Sending pull requests

Before sending a PR, please ensure that your code and commits meet the [code conventions](https://github.com/micropython/micropython/blob/master/CODECONVENTIONS.md). We have automated tools to assist with finding and fixing code style issues, see the code conventions documentation for more information. In addition, ensure that your code matches the style of the surrounding code and the project in general. If you have questions about this or are looking for guidance on a particular style question please either mention this in the PR or reach out on the forums or Discord.

The MicroPython project adheres to a strict linear git history, with no merge commits. All PRs must rebase cleanly. Please prefer to break up your work into small commits. It's always easier to squash them later than to split them.

When you submit a pull request, please make sure that it's understood why you are proposing this change: what problem it addresses, how it improves MicroPython, and what the potential downsides are (e.g. code size). Detailed commit messages are an easy way to achieve this, and additionally the PR description and comments can be used to provide a more informal summary and justification.

All code must be your own work or suitably licensed. Please see the information about signing off your commits in the [code conventions](https://github.com/micropython/micropython/blob/master/CODECONVENTIONS.md#git-commit-conventions).

## Continuous Integration

All PRs will trigger GitHub Actions to run the continuous integration (CI). This checks that all ports compile in a variety of configurations, and runs the full test suite against the Unix and Windows port, as well as emulated hardware. If you are unsure why a test is failing, please indicate that in the PR comments.

## Updating PRs

When updating a PR, either due to review feedback or to fix CI issues, you should update your branch locally and then force push it to your GitHub branch that the PR was created from. When updating your branch, this typically involves either editing the commits directly via rebase, or adding new commits then "fix"-ing them into the existing commits during a rebase. Please fetch the upstream and rebase your branch on `master` before pushing.
